# -*- coding: utf-8 -*-
"""Compound object to simplify checking
"""
import copy
import logging
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, rdDepictor, Descriptors, SaltRemover
from rdkit.Chem.AllChem import ReplaceSubstructs
# Silence RDKit Warning
from rdkit import rdBase
rdBase.DisableLog('rdApp.warning')
from requests.exceptions import RequestException

from ..utils.timeout import exit_after
from ..utils.pubchem_smiles_standardizer import get_standardized_smiles

class Compound(object):

    def __init__(self, smiles, **kwargs):
        """Initialize Compound object

            :smiles (str) - Input smiles string for compound object

            kwargs:
            :name (str) - Default = "Unknown" - Name of compound, also sets
                          name in Molblock
            :standardize (bool) - Default = False - Control whether SMILES is
                                  subject to PubChem Standardization attempt
        """

        # Standardize as a kwarg to allow disabling PubChem Standardization
        # explicitly
        standardize = kwargs.get("standardize", False)
        if standardize:
            # Try to standardize the smiles, will time out after 5 seconds
            # and resort to supplied smiles string
            self._standardizeSmiles(smiles=smiles)
        else:
            self.smiles = smiles

        # Try to get the name if specified, but default to Unknown
        # This property
        self.name = kwargs.get("name", "Unknown")

        # rdmol
        try:
            self.rdmol = Chem.MolFromSmiles(self.smiles)
        except TypeError as e:
            logging.error("RDKit was unable to load this compound")
            logging.error(e)

        self.calcMolprops()


    def __repr__(self):
        """repr for debugging
        """
        return "<Compound(name='%s', formula='%s')>" % (
            self.name, self.formula)

    def copy(self):
        return copy.deepcopy(self)

    def calcMolprops(self):
        """Calculate masses for mol using RDKit

        Masses calculated and rounded to 4 decimal points
        [M+H]+ and other adducts can be calculated using RDKit
        and the calculate_exact_mass function by providing an
        appropriate SMILES string
        """
        self.inchi = Chem.MolToInchi(self.rdmol)
        self.inchikey = Chem.MolToInchiKey(self.rdmol)
        self.accurate_mass = round(Descriptors.ExactMolWt(self.rdmol), 4)
        self.mass = round(Descriptors.MolWt(self.rdmol), 4)
        self.m_plus_h = round(self.accurate_mass + calculate_exact_mass('[H+]'), 4)
        self.m_plus_na = round(self.accurate_mass + calculate_exact_mass('[Na+]'), 4)
        # Set name in molblock
        self.rdmol.SetProp('_Name', self.name)
        rdDepictor.Compute2DCoords(self.rdmol)
        self.molblock = Chem.MolToMolBlock(self.rdmol)
        self.formula = rdMolDescriptors.CalcMolFormula(self.rdmol)

    def cleanStructure(self):
        """Clean molecular structure using RDKit

        First: Strip salts
        Second: Second, check for fragments
        """
        Chem.rdmolops.Cleanup(self.rdmol)
        neutralized = self._neutralizeMol()
        defragmented = self._getLargestFragment()
        if neutralized or defragmented:
            logging.warning('WARNING: Compound structure changed')
            self._standardizeSmiles()
            self.calcMolprops()

    def _neutralizeMol(self):
        """Strip salts and neutralize molecule"""
        neutralized = False
        _remover = SaltRemover.SaltRemover()
        molnosalt, deleted = _remover.StripMolWithDeleted(self.rdmol)
        if deleted:
            logging.info('Found salt in molecule: %s\t%s'
                     % (self.name, self.inchikey))
            neutralized_mol, neutralized = _neutraliseCharges(
                Chem.MolToSmiles(molnosalt))
        else:
            neutralized_mol, neutralized = _neutraliseCharges(
                self.smiles)
        neutral_mol = Chem.MolFromSmiles(neutralized_mol)
        if neutralized:
            logging.debug('Molecule was neutralized')
            self.rdmol = neutral_mol
            self.smiles = neutralized_mol
        return neutralized

    def _getLargestFragment(self):
        """Check if molecule is fragmented. If so, strip to largest fragment"""
        is_fragments = False
        fragments = Chem.GetMolFrags(self.rdmol, asMols=True)
        if len(fragments) > 1:
            is_fragments = True
            logging.info('Found multiple fragments in molecule: %s\t%s'
                     % (self.name, self.inchikey))
            for frag in fragments:
                longest = 0
                n_atoms = frag.GetNumAtoms()
                if n_atoms > longest and n_atoms > 0:
                    longest = n_atoms
                    self.rdmol = frag
        return is_fragments

    def _standardizeSmiles(self, smiles=None):
        """Use PubChem webservices to standardize smiles
        If the service timesout, or fails for some other reason
        SMILES remains the same
        """
        if not smiles:
            smiles = self.smiles
        try:
            self.smiles = standardize_smiles_wrapper(smiles)
        except (KeyboardInterrupt, TypeError, ValueError,
                RequestException) as e:
            logging.error("Unable to standardize %s", smiles)
            logging.error(e)
            self.smiles = smiles


# Helper functions
# Below two functions are taken directly from
# http://www.rdkit.org/docs/Cookbook.html
def _InitialiseNeutralisationReactions():
    patts = (
        # Imidazoles
        ('[n+;H]', 'n'),
        # Amines
        ('[N+;!H0]', 'N'),
        # Carboxylic acids and alcohols
        ('[$([O-]);!$([O-][#7])]', 'O'),
        # Thiols
        ('[S-;X1]', 'S'),
        # Sulfonamides
        ('[$([N-;X2]S(=O)=O)]', 'N'),
        # Enamines
        ('[$([N-;X2][C,N]=C)]', 'N'),
        # Tetrazoles
        ('[n-]', '[nH]'),
        # Sulfoxides
        ('[$([S-]=O)]', 'S'),
        # Amides
        ('[$([N-]C=O)]', 'N'),
    )
    return [(Chem.MolFromSmarts(x),
             Chem.MolFromSmiles(y, False)) for x, y in patts]


_reactions = None


def _neutraliseCharges(smiles, reactions=None):
    global _reactions
    if reactions is None:
        if _reactions is None:
            _reactions = _InitialiseNeutralisationReactions()
        reactions = _reactions
    mol = Chem.MolFromSmiles(smiles)
    replaced = False
    for i, (reactant, product) in enumerate(reactions):
        while mol.HasSubstructMatch(reactant):
            replaced = True
            rms = ReplaceSubstructs(mol, reactant, product)
            mol = rms[0]
    if replaced:
        return (Chem.MolToSmiles(mol, True), True)
    else:
        return (smiles, False)


def calculate_exact_mass(smiles):
    m = Chem.MolFromSmiles(smiles)
    return Descriptors.ExactMolWt(m)

@exit_after(5)
def standardize_smiles_wrapper(smiles):
    return get_standardized_smiles(smiles)

def inchikey_from_smiles(smiles):
    m = Chem.MolFromSmiles(smiles)
    return Chem.MolToInchiKey(m)

# -*- coding: utf-8 -*-
import sys
sys.path.append("..")
import unittest
from app.checker.Compound import Compound

class TestCompoundMethods(unittest.TestCase):
    """Tests for Compound"""

    def setUp(self):
        """Create compound: Penicillin G"""
        self.compound = Compound(
             "CC1([C@@H](N2[C@H](S1)[C@@H](C2=O)NC(=O)CC3=CC=CC=C3)C(=O)O)C",
             name="Penicillin G")

    def test_compound_default(self):
        self.assertEqual(self.compound.inchikey, "JGSARLDLIJGVTE-MBNYWOFBSA-N")
        # Standard smiles should match PubChem
        self.assertEqual(self.compound.smiles, "CC1([C@@H](N2[C@H](S1)[C@@H](C2=O)NC(=O)CC3=CC=CC=C3)C(=O)O)C")

    def test_compound_no_standardize(self):
        # Override compound
        compound = Compound(
             "CC1(C)S[C@@H]2[C@H](NC(=O)Cc3ccccc3)C(=O)N2[C@H]1C(=O)O",
             name="Penicillin G",
             standardize=False)
        # smiles should not equal PubChem, but rather the input
        self.assertNotEqual(compound.smiles, "CC1([C@@H](N2[C@H](S1)[C@@H](C2=O)NC(=O)CC3=CC=CC=C3)C(=O)O)C")
        self.assertEqual(compound.smiles, "CC1(C)S[C@@H]2[C@H](NC(=O)Cc3ccccc3)C(=O)N2[C@H]1C(=O)O")

    def test_compound_standardize_after(self):
        # Override compound
        compound = Compound(
             "CC1(C)S[C@@H]2[C@H](NC(=O)Cc3ccccc3)C(=O)N2[C@H]1C(=O)O",
             name="Penicillin G",
             standardize=False)
        compound._standardizeSmiles()
        self.assertEqual(compound.smiles, "CC1([C@@H](N2[C@H](S1)[C@@H](C2=O)NC(=O)CC3=CC=CC=C3)C(=O)O)C")
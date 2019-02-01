# -*- coding: utf-8 -*-
import re

NOT_NAMED_SYNONYMS = ('unknown', 'not named', 'no name', 'unnamed', 'none',)
SUFFIX_LIST = ('Acid', 'Ester', 'Acetate', 'Butyrate', 'Anhydride',
               'Dimer', 'Methyl', 'Ethyl', 'Aglycon', 'Aglycone')


class NameString(object):
    
    def __init__(self, name):
        self.set_name(name)
        
    def set_name(self, name):
        self.name = name
        self.lower_name = name.lower()

    def get_name(self):
        return self.name
    
    def regularize_name(self):
        self._regularize_unnamed()
        self._regularize_capital()
        
    def _regularize_capital(self):
        self._decapitalize_suffixes()
        self._capitalize_first()
        self._capitalize_letter_suffixes()
        
    def _regularize_unnamed(self):
        if any(similar(self.lower_name, not_name) > 0.75 
	       for not_name in NOT_NAMED_SYNONYMS):
            self.set_name('Not named')
            
    def _capitalize_first(self):
        if re.match('^[A-Za-z]', self.name):
            self.set_name(capitalize_first(self.name))

    def _capitalize_letter_suffixes(self):
        name = self.name
        regexp = re.compile(r'(\b[a-z]{1,2}\d?)$')
        match = regexp.search(name)
        if match:
            name = regexp.sub(capitalize(match.group()), name)
            self.set_name(name)
            
    def _decapitalize_suffixes(self):
        """De-capitalize the suffixes"""
        regexp = '\\b({0})\\b'.format('|'.join(SUFFIX_LIST))

        # Store name and search for capitalized suffixes in it
        temp_name = self.name
        res = re.search(regexp, self.name)

        while True:
            if res:
                res = res.group()
            else:
                break
            temp_name = re.sub(res, res.lower(), temp_name)
            res = re.search(regexp, temp_name)

        # Set name to save changes, even if none were made
        self.set_name(temp_name)


#### TEMPORARY FUNCTIONS TO MOVE
from difflib import SequenceMatcher

def similar(a, b):
    """Get similarity score of two strings"""
    return SequenceMatcher(None, a, b).ratio()
    
def capitalize_first(my_string):
    return ''.join([my_string[0].upper(), my_string[1:]])

def capitalize(my_string):
    return my_string.upper()
    
def decapitalize_first(my_string):
    return ''.join([my_string[0].lower(), my_string[1:]])

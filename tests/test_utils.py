# -*- coding: utf-8 -*-
import sys
sys.path.append("..")
import unittest
from time import sleep

from app.utils.NoneDict import NoneDict
from app.utils.timeout import exit_after
from app.utils.pubchem_smiles_standardizer import get_standardized_smiles

import traceback
from unittest.case import _AssertRaisesContext

class _AssertNotRaisesContext(_AssertRaisesContext):
    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is not None:
            self.exception = exc_value.with_traceback(None)

            try:
                exc_name = self.expected.__name__
            except AttributeError:
                exc_name = str(self.expected)

            if self.obj_name:
                self._raiseFailure("{} raised by {}".format(exc_name,
                    self.obj_name))
            else:
                self._raiseFailure("{} raised".format(exc_name))

        else:
            traceback.clear_frames(tb)

        return True

class MyTestCase(unittest.TestCase):
    def assertNotRaises(self, expected_exception, *args, **kwargs):
        context = _AssertNotRaisesContext(expected_exception, self)
        try:
            return context.handle('assertNotRaises', args, kwargs)
        finally:
            context = None

class TestNoneDict(MyTestCase):
    def setUp(self):
        self.d = NoneDict({1: "one", 2: "two"})

    def test_normal_dict(self):
        self.assertEqual(self.d.get(1), "one")
        self.assertIsNone(self.d.get(3))

    def test_setter(self):
        self.d[3] = "three"
        self.assertEqual(self.d.get(3), "three")
        self.assertEqual(self.d[3], "three")

    def test_dict_with_empty_string(self):
        self.d[3] = ""
        self.assertIsNone(self.d[3])


class TestTimeout(MyTestCase):

    @exit_after(1)
    def timein(self, cs):
        counter = 0.
        while counter < cs:
            sleep(0.1)
            counter += 0.1

    def test_overtime(self):
        self.assertRaises(KeyboardInterrupt, self.timein, 2)

    def test_undertime(self):
        self.assertNotRaises(KeyboardInterrupt, self.timein, 0.5)



class TestPubChemStandardize(unittest.TestCase):

    def test_invalid_smiles_empty(self):
        smiles = ""
        self.assertRaises(TypeError, get_standardized_smiles, smiles)

    def test_invalid_smiles_bad_compound(self):
        smiles = "C#C#C"
        self.assertRaises(TypeError, get_standardized_smiles, smiles)

    def test_valid_smiles(self):
        # Standarize Fullerene C60
        smiles = "c12c3c4c5c1c1c6c7c2c2c8c3c3c9c4c4c%10c5c5c1c1c6c6c%11c7c2c2c7c8c3c3c8c9c4c4c9c%10c5c5c1c1c6c6c%11c2c2c7c3c3c8c4c4c9c5c1c1c6c2c3c41"
        expected_smiles = "C12=C3C4=C5C6=C1C7=C8C9=C1C%10=C%11C(=C29)C3=C2C3=C4C4=C5C5=C9C6=C7C6=C7C8=C1C1=C8C%10=C%10C%11=C2C2=C3C3=C4C4=C5C5=C%11C%12=C(C6=C95)C7=C1C1=C%12C5=C%11C4=C3C3=C5C(=C81)C%10=C23"
        self.assertEqual(get_standardized_smiles(smiles), expected_smiles)

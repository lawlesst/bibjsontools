import unittest
from test import openurl
from test import ris

def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(openurl.suite())
    test_suite.addTest(ris.suite())
    return test_suite

runner = unittest.TextTestRunner()
results = runner.run(suite())

if results.wasSuccessful():
    pass
else:
    raise Exception('Unit tests did not pass.  Check output.')


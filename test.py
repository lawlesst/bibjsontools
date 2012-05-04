import unittest
from test import openurl

def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(openurl.suite())
    return test_suite

runner = unittest.TextTestRunner()
runner.run(suite())
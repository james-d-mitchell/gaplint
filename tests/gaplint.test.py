# pylint: skip-file

import unittest
import sys
import os

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if not path in sys.path:
    sys.path.insert(1, path)
del path

import gaplint
from gaplint import run_gaplint

class TestScript(unittest.TestCase):
    def test_fake(self):
        run_gaplint(files=['tests/test.g'], silent=True)

    def test_exit_abort(self):
        with self.assertRaises(SystemExit):
            gaplint._exit_abort()
        with self.assertRaises(SystemExit):
            gaplint._exit_abort('With a message')

    def test_yellow_string(self):
        with self.assertRaises(AssertionError):
            gaplint._yellow_string(0)

        self.assertEquals(gaplint._yellow_string('test'),
                          '\033[33mtest\033[0m')

    def test_neon_green_string(self):
        with self.assertRaises(AssertionError):
            gaplint._neon_green_string(0)

        self.assertEquals(gaplint._neon_green_string('test'),
                          '\033[40;38;5;82mtest\033[0m')

    def test_orange_string(self):
        with self.assertRaises(AssertionError):
            gaplint._orange_string(0)

        self.assertEquals(gaplint._orange_string('test'),
                          '\033[40;38;5;208mtest\033[0m')

class TestRules(unittest.TestCase):
    def test_ReplaceMultilineStrings(self):
        rule = gaplint.ReplaceMultilineStrings()

        ro = rule('"""A multiline string in one line"""')
        assert isinstance(ro, gaplint.RuleOutput)
        self.assertEquals(ro.line, '__REMOVED_MULTILINE_STRING__')

        ro = rule('str := """A multiline string in several lines')
        assert isinstance(ro, gaplint.RuleOutput)
        self.assertEquals(ro.line, 'str := __REMOVED_MULTILINE_STRING__')

        ro = rule('another line while we are consuming')
        assert isinstance(ro, gaplint.RuleOutput)
        self.assertEquals(ro.line, '__REMOVED_MULTILINE_STRING__')

        ro = rule('and another line"""')
        assert isinstance(ro, gaplint.RuleOutput)
        self.assertEquals(ro.line, '__REMOVED_MULTILINE_STRING__')

    def test_ReplaceQuotes(self):
        rule = gaplint.ReplaceQuotes('"', '__REMOVED_STRING__')

        ro = rule('x := "A string in one line"; y := 1;')
        assert isinstance(ro, gaplint.RuleOutput)
        self.assertEquals(ro.line, 'x := __REMOVED_STRING__; y := 1;')

        ro = rule('"an unmatched quote')
        self.assertEquals(ro.msg,'unmatched quote!')
        self.assertEquals(ro.abort, True)

        ro = rule(r'\"')
        self.assertEquals(ro.msg,'escaped quote outside string!')
        self.assertEquals(ro.abort, True)

        ro = rule(r'"a string followed by an escaped quote", \"')
        self.assertEquals(ro.msg,'escaped quote outside string!')
        self.assertEquals(ro.abort, True)

        ro = rule(r'a := "a string containing escaped \"quotes\""; b := "\"2\"";')
        self.assertEquals(ro.line, ('a := __REMOVED_STRING__;' +
                          ' b := __REMOVED_STRING__;'))

if __name__ == '__main__':
    unittest.main()

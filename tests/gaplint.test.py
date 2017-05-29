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
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

class TestScript(unittest.TestCase):
    def test_dot_g_file1(self):
        run_gaplint(files=['tests/test.g'], silent=True)

    def test_dot_g_file2(self):
        run_gaplint(files=['tests/test2.g'], silent=True)

    def test_dot_g_file3(self):
        with self.assertRaises(SystemExit):
            run_gaplint(files=['tests/test3.g'], silent=True)

    def test_dot_g_file4(self):
        run_gaplint(files=['tests/test.g'], silent=True, disable='all')

    def test_dot_tst_file(self):
        run_gaplint(files=['tests/test.tst'], silent=True)

    def test_wrong_ext(self):
        run_gaplint(files=['tests/file.wrongext'], silent=True)

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

    def test_info_statement(self):
        gaplint._SILENT = False
        with self.assertRaises(AssertionError):
            gaplint._info_statement(0)
        gaplint._info_statement('test')

    def test_info_action(self):
        with self.assertRaises(AssertionError):
            gaplint._info_action(0)
        gaplint._info_action('test')

    def test_info_verbose(self):
        gaplint._SILENT, gaplint._VERBOSE = False, True
        with self.assertRaises(AssertionError):
            gaplint._info_verbose(0, 0, 0)
        gaplint._info_verbose('test/tests.g', 0,'msg')

    def test_info_warn(self):
        gaplint._SILENT = False
        with self.assertRaises(AssertionError):
            gaplint._info_warn(0, 0, 0, 0)
        with self.assertRaises(AssertionError):
            gaplint._info_warn('test', 'test', 'test', 'test')
        gaplint._info_warn('tests/test.g', 0, 'test', 0)

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
        rule = gaplint.ReplaceQuotes(None, None, '"', '__REMOVED_STRING__')

        ro = rule('x := "A string in one line"; y := 1;')
        assert isinstance(ro, gaplint.RuleOutput)
        self.assertEquals(ro.line, 'x := __REMOVED_STRING__; y := 1;')

        ro = rule('"an unmatched quote')
        assert isinstance(ro, gaplint.RuleOutput)

        self.assertEquals(ro.msg, 'unmatched quote " in column 1')
        self.assertEquals(ro.abort, True)

        ro = rule(r'a := "a string containing escaped \"quotes\""; b := "\"2\"";')
        self.assertEquals(ro.line, ('a := __REMOVED_STRING__;' +
                                    ' b := __REMOVED_STRING__;'))

        ro = rule('"a good continuation\\\n')
        self.assertEquals(ro.msg, None)
        self.assertEquals(ro.abort, False)
        ro = rule('and a bad continuation\n')
        self.assertEquals(ro.msg, 'invalid continuation of string')
        self.assertEquals(ro.abort, True)

        rule._consuming=True
        ro = rule('now on a new line')
        assert isinstance(ro, gaplint.RuleOutput)
        self.assertEquals(ro.msg, 'invalid continuation of string')
        self.assertEquals(ro.abort, True)

    def test_RemoveComments(self):
        rule = gaplint.RemoveComments()
        ro = rule(r"' before a #")
        assert isinstance(ro, gaplint.RuleOutput)

    def test_RemovePrefix(self):
        rule = gaplint.RemovePrefix()
        ro = rule('line does not start with gap> or >', 'tst')
        rule._consuming = True
        ro = rule('line has neither prefix', 'tst')

    def test_UnusedLVarsFunc(self):
        rule = gaplint.UnusedLVarsFunc()

        ro = rule('function(x, x)')
        assert isinstance(ro, gaplint.RuleOutput)
        self.assertEquals(ro.msg[:29], 'duplicate function argument: ')
        self.assertEquals(ro.abort, True)

        rule.reset()
        ro = rule('function(while)')
        assert isinstance(ro, gaplint.RuleOutput)
        self.assertEquals(ro.msg[:30],'function argument is keyword: ')
        self.assertEquals(ro.abort, True)

        rule.reset()
        ro = rule('f := function(x)')
        ro = rule('local y, y;')
        assert isinstance(ro, gaplint.RuleOutput)
        self.assertEquals(ro.msg[:26], 'name used for two locals: ')
        self.assertEquals(ro.abort, True)

        rule.reset()
        ro = rule('f := function(x)')
        ro = rule('local x;')
        assert isinstance(ro, gaplint.RuleOutput)
        self.assertEquals(ro.msg[:34],'name used for argument and local: ')
        self.assertEquals(ro.abort, True)

        rule.reset()
        ro = rule('f := function(x)')
        ro = rule('local while;') # doesn't mind local local
        assert isinstance(ro, gaplint.RuleOutput)
        self.assertEquals(ro.msg[:18], 'local is keyword: ')
        self.assertEquals(ro.abort, True)

        rule.reset()
        ro = rule('f := function(x,')
        ro = rule('y)')

        rule.reset()
        ro = rule('f := function(x);')
        ro = rule('local y')
        ro = rule(', z; end;')

    def test_run_gaplint(self):
        with self.assertRaises(SystemExit):
            run_gaplint()
        with self.assertRaises(SystemExit):
            run_gaplint(files=['tests/test.g'], max_warnings=0)
        run_gaplint(files=['non-existant-file'])
        run_gaplint(files=['tests/test.g'], verbose=True)

CONFIG_YAML_FILE = '''disable:
- none
- trailing-whitespace
- remove-comments
- M002
indentation: 4
max_warnings: 1000
bananas: x'''

BAD_CONFIG_YAML_FILE_1 = '''disable: 0
indentation: 4
max_warnings: 1000
bananas: x'''

BAD_CONFIG_YAML_FILE_2 = '''disable:
- 0
indentation: 4
max_warnings: 1000
bananas: x'''

BAD_CONFIG_YAML_FILE_3 = '''disable:
    *0
    indettnatoatkajtkj = babnasnan
'''


class TestConfigYAMLFile(unittest.TestCase):

    def write_config_yaml_file(self, contents=CONFIG_YAML_FILE):
        f = file('.gaplint.yml', 'w')
        f.write(contents)
        f.close()

    def rm_config_yaml_file(self):
        os.remove('.gaplint.yml')

    def test_with_config_file_root_dir(self):
        self.write_config_yaml_file()
        run_gaplint(files=['tests/test.g'], silent=True)
        self.rm_config_yaml_file()

    def test_with_bad_config_file_1(self):
        self.write_config_yaml_file(BAD_CONFIG_YAML_FILE_1)
        run_gaplint(files=['tests/test.g'], silent=True)
        self.rm_config_yaml_file()

    def test_with_bad_config_file_2(self):
        self.write_config_yaml_file(BAD_CONFIG_YAML_FILE_2)
        run_gaplint(files=['tests/test.g'], silent=True)
        self.rm_config_yaml_file()

    def test_with_bad_config_file_3(self):
        self.write_config_yaml_file(BAD_CONFIG_YAML_FILE_3)
        run_gaplint(files=['tests/test.g'], silent=True)
        self.rm_config_yaml_file()

    def test_with_config_file_parent_top_dir(self):
        self.write_config_yaml_file()
        os.chdir('tests')
        run_gaplint(files=['test.g'], silent=True)
        os.chdir('..')
        self.rm_config_yaml_file()

    def test_with_config_file_parent_root(self):
        os.rename('.git', '.tmp_git')
        run_gaplint(files=['test.g'], silent=True)
        os.rename('.tmp_git', '.git')

    def test_disable_all_file_suppressions(self):
        run_gaplint(files=['tests/test4.g'], silent=True)

if __name__ == '__main__':
    unittest.main()

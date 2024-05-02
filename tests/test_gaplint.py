# pylint: skip-file

import unittest
import sys
import os

from os.path import exists, isdir

import gaplint
from gaplint import main as run_gaplint

path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if path not in sys.path:
    sys.path.insert(1, path)
del path


sys.stdout = open(os.devnull, "w")
sys.stderr = open(os.devnull, "w")


class TestScript(unittest.TestCase):
    def test_dot_g_file1(self):
        with self.assertRaises(SystemExit):
            run_gaplint(files=["tests/test1.g"], silent=True)

    def test_dot_g_file2(self):
        with self.assertRaises(SystemExit):
            run_gaplint(files=["tests/test2.g"], silent=True)

    def test_dot_g_file3(self):
        with self.assertRaises(SystemExit):
            run_gaplint(files=["tests/test3.g"], silent=True)

    def test_dot_g_file4(self):
        with self.assertRaises(SystemExit):
            run_gaplint(files=["tests/test1.g"], silent=True, disable="all")

    def test_dot_tst_file(self):
        with self.assertRaises(SystemExit):
            run_gaplint(files=["tests/test.tst"], silent=True)

    def test_disable_global_rule(self):
        with self.assertRaises(SystemExit) as cm:
            run_gaplint(
                files=["tests/methsel2.g"],
                silent=True,
                # Disable all rules except analyse-lvars
                disable="W001,W002,W003,W004,W005,W006,W007,W008,W009,W010,"
                + "W011,W012,W013,W014,W015,W016,W017,W018,W019,W020,"
                + "W021,W022,W023,W024,W025,W026,W027,W028,W029,W030,"
                + "W031,W032,W033",
            )
        self.assertEqual(cm.exception.code, 0)

    def test_wrong_ext(self):
        run_gaplint(files=["tests/file.wrongext"], silent=True)

    def test_info_action(self):
        with self.assertRaises(AssertionError):
            gaplint._SILENT = False
            gaplint._info_action(0)
            gaplint._SILENT = False
        gaplint._info_action("test")

    def test_info_verbose(self):
        gaplint._SILENT, gaplint._VERBOSE = False, True
        with self.assertRaises(TypeError):
            gaplint._info_verbose("test/tests.g", 0, "msg")
        gaplint._info_verbose("message")

    def test_autodoc_whitespace(self):
        with self.assertRaises(SystemExit):
            run_gaplint(files=["tests/test5.g"])


class TestRules(unittest.TestCase):
    # def test_ReplaceMultilineStrings(self):
    #    rule = gaplint.ReplaceMultilineStrings()

    #    ro = rule('"""A multiline string in one line"""')
    #    self.assertEquals(ro.line, '__REMOVED_MULTILINE_STRING__')

    #    ro = rule('str := """A multiline string in several lines')
    #    self.assertEquals(ro.line, 'str := __REMOVED_MULTILINE_STRING__')

    #    ro = rule('another line while we are consuming')
    #    self.assertEquals(ro.line, '__REMOVED_MULTILINE_STRING__')

    #    ro = rule('and another line"""')
    #    self.assertEquals(ro.line, '__REMOVED_MULTILINE_STRING__')

    # def test_ReplaceQuotes(self):
    #    rule = gaplint.ReplaceQuotes(None, None, '"', '__REMOVED_STRING__')

    #    ro = rule('x := "A string in one line"; y := 1;')
    #    self.assertEquals(ro.line, 'x := __REMOVED_STRING__; y := 1;')

    #    ro = rule('"an unmatched quote')

    #    self.assertEquals(ro.msg, 'unmatched quote " in column 1')
    #    self.assertEquals(ro.abort, True)

    #    ro = rule(r'a := "a string containing escaped \"quotes\""; b := "\"2\"";')
    #    self.assertEquals(ro.line, ('a := __REMOVED_STRING__;' +
    #                                ' b := __REMOVED_STRING__;'))

    #    ro = rule('"a good continuation\\\n')
    #    self.assertEquals(ro.msg, None)
    #    self.assertEquals(ro.abort, False)
    #    ro = rule('and a bad continuation\n')
    #    self.assertEquals(ro.msg, 'invalid continuation of string')
    #    self.assertEquals(ro.abort, True)

    #    rule._consuming=True
    #    ro = rule('now on a new line')
    #    self.assertEquals(ro.msg, 'invalid continuation of string')
    #    self.assertEquals(ro.abort, True)

    def test_ReplaceOutputTstOrXMLFile(self):
        rule = gaplint.ReplaceOutputTstOrXMLFile()
        rule("fname", "line does not start with gap> or >", 0)
        rule._consuming = True
        rule("fname", "line has neither prefix", 0)

    def test_AnalyseLVars(self):
        rule = gaplint.AnalyseLVars()

        # duplicate params
        with self.assertRaises(SystemExit):
            rule("fname", "function(x, x)", 0)
        rule.reset()

        # keyword param
        with self.assertRaises(SystemExit):
            rule("fname", "function(while)", 0)
        rule.reset()

        # duplicate locals
        with self.assertRaises(SystemExit):
            rule("fname", "f := function(x)\nlocal y, y; end;", 0)
        rule.reset()

        # param is local
        with self.assertRaises(SystemExit):
            rule("fname", "f := function(x)\nlocal x; end;", 0)
        rule.reset()

        # local is keyword
        with self.assertRaises(SystemExit):
            rule("fname", "f := function(x)\nlocal while; end;", 0)
        rule.reset()

        # function without end
        with self.assertRaises(SystemExit):
            rule("fname", "f := function(x,\ny)", 0)

        # end without function
        with self.assertRaises(SystemExit):
            rule("fname", "end;", 0)

    def test_run_gaplint(self):
        with self.assertRaises(SystemExit):
            run_gaplint()
        with self.assertRaises(SystemExit):
            run_gaplint(files=["tests/test1.g"], max_warnings=0)
        run_gaplint(files=["non-existant-file"])
        with self.assertRaises(SystemExit):
            run_gaplint(files=["tests/test1.g"], verbose=True)


CONFIG_YAML_FILE = """disable:
- none
- trailing-whitespace
- M002
- remove-comments
indentation: 4
max_warnings: 1000
bananas: x"""

BAD_CONFIG_YAML_FILE_1 = """disable: 0
indentation: 4
max_warnings: 1000
bananas: x"""

BAD_CONFIG_YAML_FILE_2 = """disable:
- 0
indentation: 4
max_warnings: 1000
bananas: x"""

BAD_CONFIG_YAML_FILE_3 = """disable:
    *0
    indettnatoatkajtkj = babnasnan
"""

EMPTY_YAML_FILE = ""


class TestConfigYAMLFile(unittest.TestCase):
    def write_config_yaml_file(self, contents=CONFIG_YAML_FILE):
        f = open(".gaplint.yml", "w")
        f.write(contents)
        f.close()

    def rm_config_yaml_file(self):
        os.remove(".gaplint.yml")

    def test_with_config_file_root_dir(self):
        self.write_config_yaml_file()
        with self.assertRaises(SystemExit):
            run_gaplint(files=["tests/test1.g"], silent=True)
        self.rm_config_yaml_file()

    def test_with_bad_config_file_1(self):
        self.write_config_yaml_file(BAD_CONFIG_YAML_FILE_1)
        with self.assertRaises(SystemExit):
            run_gaplint(files=["tests/test1.g"], silent=True)
        self.rm_config_yaml_file()

    def test_with_bad_config_file_2(self):
        self.write_config_yaml_file(BAD_CONFIG_YAML_FILE_2)
        with self.assertRaises(SystemExit):
            run_gaplint(files=["tests/test1.g"], silent=True)
        self.rm_config_yaml_file()

    def test_with_bad_config_file_3(self):
        self.write_config_yaml_file(BAD_CONFIG_YAML_FILE_3)
        with self.assertRaises(SystemExit):
            run_gaplint(files=["tests/test1.g"], silent=True)
        self.rm_config_yaml_file()

    def test_with_config_file_parent_top_dir(self):
        self.write_config_yaml_file()
        os.chdir("tests")
        with self.assertRaises(SystemExit):
            run_gaplint(files=["test1.g"], silent=True)
        os.chdir("..")
        self.rm_config_yaml_file()

    def test_with_config_file_parent_root(self):
        if exists(".git") and isdir(".git"):
            os.rename(".git", ".tmp_git")
        try:
            with self.assertRaises(SystemExit):
                run_gaplint(files=["test1.g"], silent=True)
        except Exception:
            pass
        if exists(".tmp_git") and isdir(".tmp_git"):
            os.rename(".tmp_git", ".git")

    def test_disable_all_file_suppressions(self):
        with self.assertRaises(SystemExit):
            run_gaplint(files=["tests/test4.g"], silent=True)

    def test_empty_yaml(self):
        self.write_config_yaml_file(EMPTY_YAML_FILE)
        with self.assertRaises(SystemExit):
            run_gaplint(files=["tests/test4.g"], silent=True)
        self.rm_config_yaml_file()


if __name__ == "__main__":
    unittest.main()

# pylint: skip-file

import pytest
import os

import gaplint
from gaplint import main as run_gaplint


def test_dot_g_file1():
    with pytest.raises(SystemExit) as e:
        run_gaplint(files=["tests/test1.g"], silent=False)
    assert e.value.code == 1


def test_dot_g_file2():
    with pytest.raises(SystemExit):
        run_gaplint(files=["tests/test2.g"], silent=True)


def test_dot_g_file3():
    with pytest.raises(SystemExit):
        run_gaplint(files=["tests/test3.g"], silent=True)


def test_dot_g_file4():
    with pytest.raises(SystemExit):
        run_gaplint(files=["tests/test1.g"], silent=True, disable="all")


def test_dot_tst_file():
    with pytest.raises(SystemExit):
        run_gaplint(files=["tests/test.tst"], silent=True)


def test_disable_global_rule():
    with pytest.raises(SystemExit) as excinfo:
        run_gaplint(
            files=["tests/methsel2.g"],
            silent=True,
            # Disable all rules except analyse-lvars
            enable="W000",
        )
    assert excinfo.value.code == 1


def test_hpc_gap():
    with pytest.raises(SystemExit) as excinfo:
        run_gaplint(files=["tests/filter.gi"])

    assert excinfo.value.code == 1

    with pytest.raises(SystemExit) as excinfo:
        run_gaplint(files=["tests/filter.gi"], max_warnings=2, silent=False)

    assert excinfo.value.code == 1


def test_wrong_ext():
    with pytest.raises(SystemExit) as excinfo:
        run_gaplint(files=["tests/file.wrongext"], silent=True)
    assert excinfo.value.code == 1


def test_info_action():
    with pytest.raises(AssertionError):
        gaplint._SILENT = False
        gaplint._info_action(0)
        gaplint._SILENT = False
    gaplint._info_action("test")


def test_info_verbose():
    gaplint._SILENT, gaplint._VERBOSE = False, True
    with pytest.raises(TypeError):
        gaplint._info_verbose("test/tests.g", 0, "msg")
    gaplint._info_verbose("message")


def test_autodoc_whitespace():
    with pytest.raises(SystemExit):
        run_gaplint(files=["tests/test5.g"])


def test_ReplaceOutputTstOrXMLFile():
    rule = gaplint.ReplaceOutputTstOrXMLFile("W998", "another-test-rule")
    rule("fname", "line does not start with gap> or >", 0)
    rule._consuming = True
    rule("fname", "line has neither prefix", 0)


def test_AnalyseLVars():
    rule = gaplint.AnalyseLVars("W999", "test-rule")

    # duplicate params
    with pytest.raises(SystemExit):
        rule("fname", "function(x, x)", 0)
    rule.reset()

    # keyword param
    with pytest.raises(SystemExit):
        rule("fname", "function(while)", 0)
    rule.reset()

    # duplicate locals
    with pytest.raises(SystemExit):
        rule("fname", "f := function(x)\nlocal y, y; end;", 0)
    rule.reset()

    # param is local
    with pytest.raises(SystemExit):
        rule("fname", "f := function(x)\nlocal x; end;", 0)
    rule.reset()

    # local is keyword
    with pytest.raises(SystemExit):
        rule("fname", "f := function(x)\nlocal while; end;", 0)
    rule.reset()

    # function without end
    with pytest.raises(SystemExit):
        rule("fname", "f := function(x,\ny)", 0)

    # end without function
    with pytest.raises(SystemExit):
        rule("fname", "end;", 0)


def test_run_gaplint():
    with pytest.raises(SystemExit):
        run_gaplint()
    with pytest.raises(SystemExit):
        run_gaplint(files=["tests/test1.g"], max_warnings=0)
    with pytest.raises(SystemExit) as e:
        run_gaplint(files=["non-existant-file"])
    assert e.value.code == 1
    with pytest.raises(SystemExit):
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


def write_config_yaml_file(contents=CONFIG_YAML_FILE):
    f = open(".gaplint.yml", "w")
    f.write(contents)
    f.close()


def rm_config_yaml_file():
    os.remove(".gaplint.yml")


def test_with_config_file_root_dir():
    write_config_yaml_file()
    with pytest.raises(SystemExit):
        run_gaplint(files=["tests/test1.g"], silent=True)
    rm_config_yaml_file()


def test_with_bad_config_file_1():
    write_config_yaml_file(BAD_CONFIG_YAML_FILE_1)
    with pytest.raises(SystemExit):
        run_gaplint(files=["tests/test1.g"], silent=True)
    rm_config_yaml_file()


def test_with_bad_config_file_2():
    write_config_yaml_file(BAD_CONFIG_YAML_FILE_2)
    with pytest.raises(SystemExit):
        run_gaplint(files=["tests/test1.g"], silent=True)
    rm_config_yaml_file()


def test_with_bad_config_file_3():
    write_config_yaml_file(BAD_CONFIG_YAML_FILE_3)
    with pytest.raises(SystemExit):
        run_gaplint(files=["tests/test1.g"], silent=True)
    rm_config_yaml_file()


def test_with_config_file_parent_top_dir():
    write_config_yaml_file()
    os.chdir("tests")
    with pytest.raises(SystemExit):
        run_gaplint(files=["test1.g"], silent=True)
    os.chdir("..")
    rm_config_yaml_file()


def test_with_config_file_parent_root():
    os.rename(".git", ".tmp_git")
    try:
        with pytest.raises(SystemExit):
            run_gaplint(files=["test1.g"], silent=True)
    except Exception:
        pass
    os.rename(".tmp_git", ".git")


def test_disable_all_file_suppressions():
    with pytest.raises(SystemExit):
        run_gaplint(files=["tests/test4.g"], silent=True)


def test_empty_yaml():
    write_config_yaml_file(EMPTY_YAML_FILE)
    with pytest.raises(SystemExit):
        run_gaplint(files=["tests/test4.g"], silent=True)
    rm_config_yaml_file()


def test_enable_and_disable():
    with pytest.raises(SystemExit) as e:
        run_gaplint(files=["test1.g"], enable="", disable="")
    assert e.value.code == 1
    # TODO should fail but doesn't
    # with pytest.raises(SystemExit) as e:
    #     run_gaplint(files=["test1.g"], enable=None, disable=None)
    # assert e.value.code == 1
    with pytest.raises(SystemExit) as e:
        run_gaplint(files=["test1.g"], enable="W047")
    assert e.value.code == 1
    with pytest.raises(SystemExit) as e:
        run_gaplint(files=["test1.g"], max_warnings=1)
    assert e.value.code == 1

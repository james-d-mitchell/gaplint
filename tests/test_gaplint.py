# pylint: skip-file

import pytest
import os

from os.path import exists, isdir

import gaplint
from gaplint import main as run_gaplint


def test_dot_g_file1():
    expected = {
        "W000": 3,
        "W001": 1,
        "W002": 1,
        "W003": 1,
        "W004": 3,
        "W005": 12,
        "W006": 0,
        "W007": 2,
        "W008": 5,
        "W009": 17,
        "W010": 1,
        "W011": 0,
        "W012": 1,
        "W013": 0,
        "W014": 2,
        "W015": 0,
        "W016": 2,
        "W017": 0,
        "W018": 1,
        "W019": 4,
        "W020": 2,
        "W021": 0,
        "W022": 1,
        "W023": 0,
        "W024": 0,
        "W025": 0,
        "W026": 0,
        "W027": 0,
        "W028": 0,
        "W029": 0,
        "W030": 1,
        "W031": 1,
        "W032": 1,
        "W033": 0,
        "W034": 1,
        "W035": 0,
        "W036": 0,
        "W037": 0,
        "W038": 0,
        "W039": 0,
        "W040": 3,
        "W041": 0,
        "W042": 0,
        "W043": 0,
        "W044": 0,
        "W045": 0,
        "W046": 6,
        "W047": 4,
        "W048": 0,
    }

    with pytest.raises(SystemExit) as e:
        run_gaplint(files=["tests/test1.g"])
    assert e.value.code == 66
    for code in gaplint.Rule.all_suppressible_codes():
        with pytest.raises(SystemExit) as e:
            run_gaplint(files=["tests/test1.g"], enable=code)
        assert (expected[code], code) == (e.value.code, code)


def test_dot_g_file2():
    expected = {
        "W000": 0,
        "W001": 0,
        "W002": 0,
        "W003": 0,
        "W004": 8,
        "W005": 0,
        "W006": 0,
        "W007": 0,
        "W008": 0,
        "W009": 0,
        "W010": 0,
        "W011": 0,
        "W012": 30,
        "W013": 30,
        "W014": 0,
        "W015": 0,
        "W016": 48,
        "W017": 0,
        "W018": 0,
        "W019": 0,
        "W020": 6,
        "W021": 0,
        "W022": 5,
        "W023": 0,
        "W024": 0,
        "W025": 0,
        "W026": 0,
        "W027": 0,
        "W028": 0,
        "W029": 0,
        "W030": 0,
        "W031": 0,
        "W032": 0,
        "W033": 0,
        "W034": 0,
        "W035": 0,
        "W036": 0,
        "W037": 0,
        "W038": 0,
        "W039": 0,
        "W040": 0,
        "W041": 0,
        "W042": 0,
        "W043": 0,
        "W044": 0,
        "W045": 0,
        "W046": 0,
        "W047": 0,
        "W048": 0,
        "W049": 0,
        "W050": 0,
        "W051": 0,
        "W052": 0,
        "W053": 0,
        "W054": 0,
    }

    with pytest.raises(SystemExit) as e:
        run_gaplint(files=["tests/test2.g"])
    assert e.value.code == 127
    for code in gaplint.Rule.all_suppressible_codes():
        with pytest.raises(SystemExit) as e:
            run_gaplint(files=["tests/test2.g"], enable=code)
        assert (expected[code], code) == (e.value.code, code)


def test_dot_g_file3():
    # syntax error
    with pytest.raises(SystemExit) as e:
        run_gaplint(files=["tests/test3.g"])
    assert e.value.code == 1


def test_dot_g_file4():
    with pytest.raises(SystemExit) as e:
        run_gaplint(files=["tests/test1.g"], disable="all")
    assert e.value.code == 0


def test_dot_tst_file():
    with pytest.raises(SystemExit) as e:
        run_gaplint(files=["tests/test.tst"])
    assert e.value.code == 2


def test_disable_global_rule():
    with pytest.raises(SystemExit) as e:
        run_gaplint(
            files=["tests/methsel2.g"],
            silent=True,
            # Disable all rules except analyse-lvars
            enable="W000",
        )
    assert e.value.code == 0


def test_hpc_gap():
    with pytest.raises(SystemExit) as excinfo:
        run_gaplint(files=["tests/filter.gi"])

    assert excinfo.value.code == 1

    with pytest.raises(SystemExit) as excinfo:
        run_gaplint(files=["tests/filter.gi"], max_warnings=2)

    assert excinfo.value.code == 1


def test_wrong_ext():
    with pytest.raises(SystemExit) as excinfo:
        run_gaplint(files=["tests/file.wrongext"])
    assert excinfo.value.code == 1


def test_autodoc_whitespace():
    with pytest.raises(SystemExit) as e:
        run_gaplint(files=["tests/test5.g"])
    assert e.value.code == 0


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
        run_gaplint(files=["tests/test1.g"])
    rm_config_yaml_file()


def test_with_bad_config_file_1():
    write_config_yaml_file(BAD_CONFIG_YAML_FILE_1)
    with pytest.raises(SystemExit):
        run_gaplint(files=["tests/test1.g"])
    rm_config_yaml_file()


def test_with_bad_config_file_2():
    write_config_yaml_file(BAD_CONFIG_YAML_FILE_2)
    with pytest.raises(SystemExit):
        run_gaplint(files=["tests/test1.g"])
    rm_config_yaml_file()


def test_with_bad_config_file_3():
    write_config_yaml_file(BAD_CONFIG_YAML_FILE_3)
    with pytest.raises(SystemExit):
        run_gaplint(files=["tests/test1.g"])
    rm_config_yaml_file()


def test_with_config_file_parent_top_dir():
    write_config_yaml_file()
    os.chdir("tests")
    with pytest.raises(SystemExit):
        run_gaplint(files=["test1.g"])
    os.chdir("..")
    rm_config_yaml_file()


def test_with_config_file_parent_root():
    if exists(".git") and isdir(".git"):
        os.rename(".git", ".tmp_git")
    try:
        with pytest.raises(SystemExit):
            run_gaplint(files=["test1.g"], silent=True)
    except Exception:
        pass
    if exists(".tmp_git") and isdir(".tmp_git"):
        os.rename(".tmp_git", ".git")


def test_disable_all_file_suppressions():
    with pytest.raises(SystemExit):
        run_gaplint(files=["tests/test4.g"])


def test_empty_yaml():
    write_config_yaml_file(EMPTY_YAML_FILE)
    with pytest.raises(SystemExit):
        run_gaplint(files=["tests/test4.g"])
    rm_config_yaml_file()


def test_enable_and_disable():
    with pytest.raises(SystemExit) as e:
        run_gaplint(files=["test1.g"], enable="", disable="")
    assert e.value.code == 1
    with pytest.raises(SystemExit) as e:
        run_gaplint(files=["test1.g"], enable=None, disable=None)
    assert e.value.code == 1
    with pytest.raises(SystemExit) as e:
        run_gaplint(files=["test1.g"], enable="W047")
    assert e.value.code == 1
    with pytest.raises(SystemExit) as e:
        run_gaplint(files=["test1.g"], max_warnings=1)
    assert e.value.code == 1

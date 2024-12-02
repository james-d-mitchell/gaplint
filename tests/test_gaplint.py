# pylint: skip-file

import pytest
import os

from os.path import exists, isdir

import gaplint
from gaplint import Diagnostic
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
        "W047": 3,
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


@pytest.mark.parametrize(
    "fname,expected",
    [
        (
            "tests/test1.g",
            {
                Diagnostic(
                    code="W046",
                    name="unused-func-args",
                    line=18,
                    message="Unused function arguments: arg",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W000",
                    name="analyse-lvars",
                    line=44,
                    message="Unused local variables: t",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W046",
                    name="unused-func-args",
                    line=45,
                    message="Unused function arguments: 1a1a, 1b, localt, x, y",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W000",
                    name="analyse-lvars",
                    line=48,
                    message="Unused local variables: t",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W046",
                    name="unused-func-args",
                    line=60,
                    message="Unused function arguments: z",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W000",
                    name="analyse-lvars",
                    line=63,
                    message="Variables assigned but never used: test",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W001",
                    name="consecutive-empty-lines",
                    line=27,
                    message="Consecutive empty lines",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W034",
                    name="1-line-function",
                    line=60,
                    message="One line function could be a lambda",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W009",
                    name="not-enough-space-before-comment",
                    line=3,
                    message="At least 2 spaces before comment",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W020",
                    name="whitespace-op-plus",
                    line=3,
                    message="Wrong whitespace around operator +",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W005",
                    name="align-trailing-comments",
                    line=5,
                    message="Unaligned comments in consecutive lines",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W009",
                    name="not-enough-space-before-comment",
                    line=5,
                    message="At least 2 spaces before comment",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W014",
                    name="multiple-semicolons",
                    line=5,
                    message="More than one semicolon",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W022",
                    name="whitespace-op-negative",
                    line=5,
                    message="Wrong whitespace around operator -",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W009",
                    name="not-enough-space-before-comment",
                    line=7,
                    message="At least 2 spaces before comment",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W009",
                    name="not-enough-space-before-comment",
                    line=9,
                    message="At least 2 spaces before comment",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W020",
                    name="whitespace-op-plus",
                    line=9,
                    message="Wrong whitespace around operator +",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W005",
                    name="align-trailing-comments",
                    line=10,
                    message="Unaligned comments in consecutive lines",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W005",
                    name="align-trailing-comments",
                    line=11,
                    message="Unaligned comments in consecutive lines",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W005",
                    name="align-trailing-comments",
                    line=12,
                    message="Unaligned comments in consecutive lines",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W009",
                    name="not-enough-space-before-comment",
                    line=12,
                    message="At least 2 spaces before comment",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W019",
                    name="whitespace-op-minus",
                    line=12,
                    message="Wrong whitespace around operator -",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W005",
                    name="align-trailing-comments",
                    line=13,
                    message="Unaligned comments in consecutive lines",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W009",
                    name="not-enough-space-before-comment",
                    line=13,
                    message="At least 2 spaces before comment",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W005",
                    name="align-trailing-comments",
                    line=14,
                    message="Unaligned comments in consecutive lines",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W009",
                    name="not-enough-space-before-comment",
                    line=14,
                    message="At least 2 spaces before comment",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W030",
                    name="whitespace-op-power",
                    line=14,
                    message="Wrong whitespace around operator ^",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W005",
                    name="align-trailing-comments",
                    line=15,
                    message="Unaligned comments in consecutive lines",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W009",
                    name="not-enough-space-before-comment",
                    line=15,
                    message="At least 2 spaces before comment",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W031",
                    name="whitespace-op-not-equal",
                    line=15,
                    message="Wrong whitespace around operator <>",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W007",
                    name="trailing-whitespace",
                    line=17,
                    message="Trailing whitespace",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W009",
                    name="not-enough-space-before-comment",
                    line=17,
                    message="At least 2 spaces before comment",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W032",
                    name="whitespace-double-dot",
                    line=17,
                    message="Wrong whitespace around operator ..",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W005",
                    name="align-trailing-comments",
                    line=18,
                    message="Unaligned comments in consecutive lines",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W009",
                    name="not-enough-space-before-comment",
                    line=18,
                    message="At least 2 spaces before comment",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W005",
                    name="align-trailing-comments",
                    line=19,
                    message="Unaligned comments in consecutive lines",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W009",
                    name="not-enough-space-before-comment",
                    line=19,
                    message="At least 2 spaces before comment",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W019",
                    name="whitespace-op-minus",
                    line=19,
                    message="Wrong whitespace around operator -",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W009",
                    name="not-enough-space-before-comment",
                    line=21,
                    message="At least 2 spaces before comment",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W005",
                    name="align-trailing-comments",
                    line=22,
                    message="Unaligned comments in consecutive lines",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W009",
                    name="not-enough-space-before-comment",
                    line=22,
                    message="At least 2 spaces before comment",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W019",
                    name="whitespace-op-minus",
                    line=22,
                    message="Wrong whitespace around operator -",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W009",
                    name="not-enough-space-before-comment",
                    line=23,
                    message="At least 2 spaces before comment",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W005",
                    name="align-trailing-comments",
                    line=24,
                    message="Unaligned comments in consecutive lines",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W009",
                    name="not-enough-space-before-comment",
                    line=24,
                    message="At least 2 spaces before comment",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W019",
                    name="whitespace-op-minus",
                    line=24,
                    message="Wrong whitespace around operator -",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=25,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W004",
                    name="align-assignments",
                    line=26,
                    message="Unaligned assignments in consecutive lines",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=26,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W004",
                    name="align-assignments",
                    line=27,
                    message="Unaligned assignments in consecutive lines",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W009",
                    name="not-enough-space-before-comment",
                    line=30,
                    message="At least 2 spaces before comment",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=30,
                    message="No space allowed after bracket",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W005",
                    name="align-trailing-comments",
                    line=31,
                    message="Unaligned comments in consecutive lines",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W009",
                    name="not-enough-space-before-comment",
                    line=31,
                    message="At least 2 spaces before comment",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W002",
                    name="line-too-long",
                    line=37,
                    message="Too long line (81 / 80)",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W007",
                    name="trailing-whitespace",
                    line=39,
                    message="Trailing whitespace",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=40,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W014",
                    name="multiple-semicolons",
                    line=44,
                    message="More than one semicolon",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W018",
                    name="function-local-same-line",
                    line=44,
                    message="Keywords 'function' and 'local' in the same line",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W008",
                    name="no-space-after-comment",
                    line=47,
                    message="No space after comment",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W008",
                    name="no-space-after-comment",
                    line=52,
                    message="No space after comment",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W008",
                    name="no-space-after-comment",
                    line=55,
                    message="No space after comment",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W008",
                    name="no-space-after-comment",
                    line=56,
                    message="No space after comment",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W008",
                    name="no-space-after-comment",
                    line=59,
                    message="No space after comment",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W004",
                    name="align-assignments",
                    line=66,
                    message="Unaligned assignments in consecutive lines",
                    filename="tests/test1.g",
                ),
                Diagnostic(
                    code="W010",
                    name="space-after-comma",
                    line=66,
                    message="Exactly one space required after comma",
                    filename="tests/test1.g",
                ),
            },
        ),
        (
            "tests/test2.g",
            {
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=89,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=4,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=31,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=15,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=44,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=3,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=37,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=101,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=73,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=9,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=63,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=45,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=35,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=87,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=96,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=68,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W020",
                    name="whitespace-op-plus",
                    line=65,
                    message="Wrong whitespace around operator +",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=71,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W022",
                    name="whitespace-op-negative",
                    line=92,
                    message="Wrong whitespace around operator -",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=37,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=20,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=43,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=6,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=33,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=66,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=66,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=89,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=39,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=92,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=68,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=51,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W020",
                    name="whitespace-op-plus",
                    line=71,
                    message="Wrong whitespace around operator +",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=67,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=3,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=87,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=49,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=39,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=66,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W004",
                    name="align-assignments",
                    line=23,
                    message="Unaligned assignments in consecutive lines",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=62,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=85,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=96,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=44,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W022",
                    name="whitespace-op-negative",
                    line=83,
                    message="Wrong whitespace around operator -",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W022",
                    name="whitespace-op-negative",
                    line=65,
                    message="Wrong whitespace around operator -",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=20,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=10,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=37,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=9,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=32,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=83,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=52,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=96,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=78,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=41,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W004",
                    name="align-assignments",
                    line=52,
                    message="Unaligned assignments in consecutive lines",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=18,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=2,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=8,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=29,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W004",
                    name="align-assignments",
                    line=101,
                    message="Unaligned assignments in consecutive lines",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=76,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=41,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=77,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=65,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=61,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=74,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W020",
                    name="whitespace-op-plus",
                    line=10,
                    message="Wrong whitespace around operator +",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=60,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W004",
                    name="align-assignments",
                    line=71,
                    message="Unaligned assignments in consecutive lines",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W020",
                    name="whitespace-op-plus",
                    line=92,
                    message="Wrong whitespace around operator +",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=34,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W004",
                    name="align-assignments",
                    line=66,
                    message="Unaligned assignments in consecutive lines",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=18,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=47,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=70,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=31,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W004",
                    name="align-assignments",
                    line=33,
                    message="Unaligned assignments in consecutive lines",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=48,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=92,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=93,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=77,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=83,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=90,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=22,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=65,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W004",
                    name="align-assignments",
                    line=74,
                    message="Unaligned assignments in consecutive lines",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=15,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=69,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=1,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=1,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=30,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=51,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=41,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=53,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=104,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=88,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=60,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=48,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W020",
                    name="whitespace-op-plus",
                    line=83,
                    message="Wrong whitespace around operator +",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=15,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=51,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=62,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=52,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=23,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=45,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=13,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W004",
                    name="align-assignments",
                    line=93,
                    message="Unaligned assignments in consecutive lines",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W020",
                    name="whitespace-op-plus",
                    line=101,
                    message="Wrong whitespace around operator +",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=34,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=81,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=94,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=100,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=69,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W022",
                    name="whitespace-op-negative",
                    line=51,
                    message="Wrong whitespace around operator -",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=93,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=83,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=18,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=20,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=45,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=39,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=93,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=29,
                    message="No space allowed before bracket",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=52,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W022",
                    name="whitespace-op-negative",
                    line=37,
                    message="Wrong whitespace around operator -",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W016",
                    name="whitespace-op-assign",
                    line=65,
                    message="Wrong whitespace around operator :=",
                    filename="tests/test2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=92,
                    message="No space allowed after bracket",
                    filename="tests/test2.g",
                ),
            },
        ),
        (
            "tests/test3.g",
            {
                Diagnostic(
                    code="M004",
                    name="replace-strings",
                    line=1,
                    message='Unmatched "',
                    filename="tests/test3.g",
                )
            },
        ),
        (
            "tests/test4.g",
            set(),
        ),
        (
            "tests/test5.g",
            set(),
        ),
        (
            "tests/test.tst",
            {
                Diagnostic(
                    code="W008",
                    name="no-space-after-comment",
                    line=21,
                    message="No space after comment",
                    filename="tests/test.tst",
                ),
                Diagnostic(
                    code="W009",
                    name="not-enough-space-before-comment",
                    line=21,
                    message="At least 2 spaces before comment",
                    filename="tests/test.tst",
                ),
            },
        ),
        (
            "tests/methsel2.g",
            {
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=201,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=132,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=78,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=185,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=173,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=130,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=218,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=107,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=66,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=170,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=89,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=79,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=140,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=153,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=228,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=51,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=137,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=277,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=278,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W001",
                    name="consecutive-empty-lines",
                    line=20,
                    message="Consecutive empty lines",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=125,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W008",
                    name="no-space-after-comment",
                    line=141,
                    message="No space after comment",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=278,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=199,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=130,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W008",
                    name="no-space-after-comment",
                    line=52,
                    message="No space after comment",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W043",
                    name="dont-use-arg",
                    line=68,
                    message="Use arg... instead of arg",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=196,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=164,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=202,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=204,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=271,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=87,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=184,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=77,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=211,
                    message="Bad indentation: found 4 but expected at least 6",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=217,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=100,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=197,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=59,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=92,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=134,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=275,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=72,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=239,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=62,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=123,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W032",
                    name="whitespace-double-dot",
                    line=213,
                    message="Wrong whitespace around operator ..",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=146,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=276,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W043",
                    name="dont-use-arg",
                    line=128,
                    message="Use arg... instead of arg",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=118,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=108,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=131,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=194,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=164,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=182,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W046",
                    name="unused-func-args",
                    line=128,
                    message="Unused function arguments: arg",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=210,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=218,
                    message="Bad indentation: found 6 but expected at least 8",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W002",
                    name="line-too-long",
                    line=228,
                    message="Too long line (84 / 80)",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=173,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=136,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=57,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=132,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=195,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=134,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W043",
                    name="dont-use-arg",
                    line=204,
                    message="Use arg... instead of arg",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=220,
                    message="Bad indentation: found 4 but expected at least 6",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W015",
                    name="keyword-function",
                    line=45,
                    message="Keyword 'function' not followed by (",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=70,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=60,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=135,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=279,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=94,
                    message="Bad indentation: found 5 but expected at least 8",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=133,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=144,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=157,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=55,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=116,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=106,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W008",
                    name="no-space-after-comment",
                    line=178,
                    message="No space after comment",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=204,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=88,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=119,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=208,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=203,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=134,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=69,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W001",
                    name="consecutive-empty-lines",
                    line=47,
                    message="Consecutive empty lines",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W004",
                    name="align-assignments",
                    line=214,
                    message="Unaligned assignments in consecutive lines",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=205,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=221,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=92,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=275,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=159,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=217,
                    message="Bad indentation: found 6 but expected at least 8",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W002",
                    name="line-too-long",
                    line=247,
                    message="Too long line (100 / 80)",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=188,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=50,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=147,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=160,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=53,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=128,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=45,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=216,
                    message="Bad indentation: found 4 but expected at least 6",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=132,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=127,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=224,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=109,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=239,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=122,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=135,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=112,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=186,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=84,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=214,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=136,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=158,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=148,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=181,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=173,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=270,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=98,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W020",
                    name="whitespace-op-plus",
                    line=136,
                    message="Wrong whitespace around operator +",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=143,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=204,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=135,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W010",
                    name="space-after-comma",
                    line=232,
                    message="Exactly one space required after comma",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W043",
                    name="dont-use-arg",
                    line=92,
                    message="Use arg... instead of arg",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=98,
                    message="Bad indentation: found 4 but expected at least 6",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=92,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=189,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=82,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=212,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=105,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=64,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W002",
                    name="line-too-long",
                    line=4,
                    message="Too long line (82 / 80)",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=54,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=156,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=168,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=179,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=254,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=45,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=69,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=128,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=151,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W010",
                    name="space-after-comma",
                    line=96,
                    message="Exactly one space required after comma",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=141,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=216,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=133,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=68,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W010",
                    name="space-after-comma",
                    line=220,
                    message="Exactly one space required after comma",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=164,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W020",
                    name="whitespace-op-plus",
                    line=231,
                    message="Wrong whitespace around operator +",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=136,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=169,
                    message="Bad indentation: found 4 but expected at least 6",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=90,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=128,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=187,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=167,
                    message="Bad indentation: found 4 but expected at least 6",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W043",
                    name="dont-use-arg",
                    line=270,
                    message="Use arg... instead of arg",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=68,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=200,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=52,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=91,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=75,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=81,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=63,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=149,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=279,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=247,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=162,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=121,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=152,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=111,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=150,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=277,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=213,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W010",
                    name="space-after-comma",
                    line=236,
                    message="Exactly one space required after comma",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=198,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=180,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=73,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=193,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=61,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=165,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=97,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=74,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=58,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=133,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=217,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W046",
                    name="unused-func-args",
                    line=68,
                    message="Unused function arguments: arg",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=209,
                    message="Bad indentation: found 4 but expected at least 6",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W010",
                    name="space-after-comma",
                    line=234,
                    message="Exactly one space required after comma",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=114,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=120,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=104,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=145,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=98,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=117,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=178,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=76,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=206,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=276,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=191,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=171,
                    message="Bad indentation: found 4 but expected at least 6",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=163,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=56,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=219,
                    message="Bad indentation: found 4 but expected at least 6",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=176,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=207,
                    message="Bad indentation: found 4 but expected at least 6",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W002",
                    name="line-too-long",
                    line=46,
                    message="Too long line (89 / 80)",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W001",
                    name="consecutive-empty-lines",
                    line=254,
                    message="Consecutive empty lines",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=67,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=218,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=102,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=93,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=271,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=222,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=115,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=113,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=103,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=95,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=126,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=166,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=110,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=177,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=161,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=131,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W046",
                    name="unused-func-args",
                    line=270,
                    message="Unused function arguments: arg",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=174,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=190,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=129,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W008",
                    name="no-space-after-comment",
                    line=104,
                    message="No space after comment",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=272,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=65,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W010",
                    name="space-after-comma",
                    line=235,
                    message="Exactly one space required after comma",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=192,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=85,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W008",
                    name="no-space-after-comment",
                    line=25,
                    message="No space after comment",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=215,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=124,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=254,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=83,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=129,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=80,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=86,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W043",
                    name="dont-use-arg",
                    line=164,
                    message="Use arg... instead of arg",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W013",
                    name="space-before-bracket",
                    line=270,
                    message="No space allowed before bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=95,
                    message="Bad indentation: found 4 but expected at least 6",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=68,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=154,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W010",
                    name="space-after-comma",
                    line=233,
                    message="Exactly one space required after comma",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W008",
                    name="no-space-after-comment",
                    line=259,
                    message="No space after comment",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=99,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W008",
                    name="no-space-after-comment",
                    line=74,
                    message="No space after comment",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=172,
                    message="Bad indentation: found 2 but expected at least 4",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=142,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=183,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W012",
                    name="space-after-bracket",
                    line=216,
                    message="No space allowed after bracket",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=155,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W003",
                    name="indentation",
                    line=139,
                    message="Bad indentation: found 0 but expected at least 2",
                    filename="tests/methsel2.g",
                ),
                Diagnostic(
                    code="W010",
                    name="space-after-comma",
                    line=231,
                    message="Exactly one space required after comma",
                    filename="tests/methsel2.g",
                ),
            },
        ),
        (
            "tests/filter.gi",
            {
                Diagnostic(
                    code="W046",
                    name="unused-func-args",
                    line=78,
                    message="Unused function arguments: filt",
                    filename="tests/filter.gi",
                ),
                Diagnostic(
                    code="W000",
                    name="analyse-lvars",
                    line=104,
                    message='Invalid syntax: "badsyntax name"',
                    filename="tests/filter.gi",
                ),
                Diagnostic(
                    code="W038",
                    name="use-return-fail",
                    line=83,
                    message="Replace one line function by ReturnFail",
                    filename="tests/filter.gi",
                ),
                Diagnostic(
                    code="W046",
                    name="unused-func-args",
                    line=63,
                    message="Unused function arguments: prefilt",
                    filename="tests/filter.gi",
                ),
                Diagnostic(
                    code="W036",
                    name="use-return-true",
                    line=73,
                    message="Replace one line function by ReturnTrue",
                    filename="tests/filter.gi",
                ),
                Diagnostic(
                    code="W037",
                    name="use-return-false",
                    line=78,
                    message="Replace one line function by ReturnFalse",
                    filename="tests/filter.gi",
                ),
                Diagnostic(
                    code="W039",
                    name="use-return-first",
                    line=63,
                    message="Replace function(x, y, z, ...) return x; end; by ReturnFirst",
                    filename="tests/filter.gi",
                ),
                Diagnostic(
                    code="W046",
                    name="unused-func-args",
                    line=83,
                    message="Unused function arguments: filt",
                    filename="tests/filter.gi",
                ),
                Diagnostic(
                    code="W040",
                    name="use-id-func",
                    line=68,
                    message='Replace "function(x) return x; end;" by IdFunc',
                    filename="tests/filter.gi",
                ),
                Diagnostic(
                    code="W046",
                    name="unused-func-args",
                    line=73,
                    message="Unused function arguments: filt",
                    filename="tests/filter.gi",
                ),
            },
        ),
        (
            "tests/file.wrongext",
            set(),
        ),
    ],
)
def test_diagnostics(fname, expected):
    with pytest.raises(SystemExit) as e:
        run_gaplint(files=[fname])
    assert expected == set(gaplint._DIAGNOSTICS)

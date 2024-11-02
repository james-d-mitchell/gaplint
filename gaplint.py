#!/usr/bin/env python3
"""
This module provides functions for automatically checking the format of a GAP
file according to some conventions.
"""
# pylint: disable=fixme, too-many-lines

import argparse
import functools
import itertools
import os
import re
import sys
import time
from copy import deepcopy
from importlib.metadata import version
from os import listdir
from os.path import abspath, exists, isdir, isfile, join
from typing import Any, Callable, Dict, List, Set, Tuple, Union
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table
import yaml

###############################################################################
# Utility
###############################################################################


@dataclass(frozen=True)
class Diagnostic:
    """A diagnostic wrapper class."""

    code: str
    name: str
    line: int
    message: str
    filename: str


###############################################################################
# Globals
###############################################################################

_VERBOSE = False
_SILENT = False
_GAP_KEYWORDS = {
    "and",
    "atomic",
    "break",
    "continue",
    "do",
    "elif",
    "else",
    "end",
    "false",
    "fi",
    "for",
    "function",
    "if",
    "in",
    "local",
    "mod",
    "not",
    "od",
    "or",
    "readonly",
    "readwrite",
    "rec",
    "repeat",
    "return",
    "then",
    "true",
    "until",
    "while",
    "quit",
    "QUIT",
    "IsBound",
    "Unbind",
    "TryNextMethod",
    "Info",
    "Assert",
}

_DEFAULT_CONFIG = {
    "columns": 80,
    "disable": set(),
    "dupl-func-min-len": 4,
    "enable": "all",
    "explain": "",
    "files": [],
    "indentation": 2,
    "max-warnings": 1000,
    "silent": False,
    "verbose": False,
    "column-range": False,
}

_GLOB_CONFIG = {}
_GLOB_SUPPRESSIONS = set()
_FILE_SUPPRESSIONS = {}
_LINE_SUPPRESSIONS = {}

_LINE_RULES = []
_FILE_RULES = []

_ESCAPE_PATTERN = re.compile(r"(^\\(\\\\)*[^\\]+.*$|^\\(\\\\)*$)")

_DIAGNOSTICS = []

###############################################################################
# Strings helpers
###############################################################################


def _is_tst_or_xml_file(fname: str) -> bool:
    """Returns True if the extension of fname is '.xml' or '.tst'."""
    assert isinstance(fname, str)
    ext = fname.split(".")[-1]
    return ext in ("tst", "xml")


def _is_escaped(lines: str, pos: int) -> Union[bool, re.Match, None]:
    assert isinstance(lines, str)
    assert isinstance(pos, int)
    assert 0 <= pos < len(lines)
    if lines[pos - 1] != "\\":
        return False
    start = lines.rfind("\n", 0, pos)
    # Search for an odd number of backslashes immediately before line[pos]
    return _ESCAPE_PATTERN.search(lines[start + 1 : pos][::-1])


def _is_double_quote_in_char(line: str, pos: int) -> bool:
    assert isinstance(line, str)
    assert isinstance(pos, int)
    assert 0 <= pos < len(line)
    return (
        pos > 0
        and pos + 1 < len(line)
        and line[pos - 1 : pos + 2] == "'\"'"
        and not _is_escaped(line, pos - 1)
    )


def _is_in_string(lines: str, pos: int) -> bool:
    assert isinstance(lines, str)
    assert isinstance(pos, int)
    start = lines.rfind("\n", 0, pos)
    line = re.sub(r"\\.", "", lines[start:pos])
    return line.count('"') % 2 == 1 or line.count("'") % 2 == 1


###############################################################################
# Info messages
###############################################################################


def _warn_or_error(
    rule,
    fname: str,
    linenum: int,
    msg: str,
    column_range: Union[Tuple[int, int], None] = None,
) -> None:
    if not _SILENT:
        assert isinstance(fname, str)
        assert isinstance(linenum, int)
        assert isinstance(msg, str)
        if _COLUMN_RANGE and column_range is not None:
            sys.stderr.write(
                f"{fname}:{linenum + 1}:{column_range[0]+1}-{column_range[1]+1}: {msg} [{rule.code}/{rule.name}]\n"
            )
        else:
            sys.stderr.write(
                f"{fname}:{linenum + 1}: {msg} [{rule.code}/{rule.name}]\n"
            )
        _DIAGNOSTICS.append(
            Diagnostic(
                code=rule.code,
                name=rule.name,
                line=linenum + 1,
                message=msg,
                filename=fname,
            )
        )


def _warn(
    rule,
    fname: str,
    linenum: int,
    msg: str,
    column_range: Union[Tuple[int, int], None] = None,
) -> None:
    _warn_or_error(rule, fname, linenum, msg, column_range)


def _error(
    rule,
    fname: str,
    linenum: int,
    msg: str,
    column_range: Union[Tuple[int, int], None] = None,
) -> None:
    _warn_or_error(rule, fname, linenum, msg, column_range)
    sys.stderr.write("Aborting!\n")
    sys.exit(1)


def _info_action(msg: str) -> None:
    if not _SILENT:
        assert isinstance(msg, str)
        sys.stdout.write(f"\033[33m{msg}\033[0m\n")


def _info_verbose(msg: str) -> None:
    if not _SILENT and _VERBOSE:
        assert isinstance(msg, str)
        sys.stdout.write(f"\033[2m{msg}\033[0m\n")


###############################################################################
# Rules: a rule must have Rule as a base class.
###############################################################################


class Rule:
    """
    Base class for rules.

    A rule is a subclass of this class which has a __call__ method that returns
    Tuple[int, str] where the \"int\" is the number of warnings issued, and where
    the \"str\" is the lines of the file on which the rules are being applied.
    """

    all_codes = set()
    all_names = {}

    @staticmethod
    def all_suppressible_codes() -> Set[str]:
        """
        Returns the set of all the suppressible rule codes.
        """
        return set(x for x in Rule.all_codes if x and not x.startswith("M"))

    @staticmethod
    def to_code(name_or_code: str) -> str:
        """
        Get the code of a rule by its name_or_code.
        """
        if name_or_code in Rule.all_names:
            return Rule.all_names[name_or_code]
        return name_or_code

    def __init__(self, name: str, code: str, desc: str = ""):
        assert isinstance(name, str)
        assert isinstance(code, str)
        assert isinstance(desc, str)
        if __debug__:
            if code in Rule.all_codes:
                raise ValueError(f"Duplicate rule code {code}")
            Rule.all_codes.add(code)
            if name in Rule.all_names:
                raise ValueError(f"Duplicate rule name {name}")
            Rule.all_names[name] = code
        self.name = name
        self.code = code
        self.desc = desc

    def reset(self) -> None:
        """
        Reset the rule.

        This is only used by rules like those for checking the indentation of
        lines. This method is called once per file on which gaplint it run, so
        that issues with indentation, for example, in one file do not spill
        over into the next file.
        """


class WarnRegexBase(Rule):
    """
    Instances of this class produce a warning whenever a line matches the
    pattern used to construct the instance except if one of a list of
    exceptions is also matched.
    """

    # TODO use keyword args
    def __init__(  # pylint: disable=too-many-arguments, too-many-positional-arguments, dangerous-default-value
        self,
        name: str,
        code: str,
        desc: str,
        pattern: str,
        warning_msg: str,
        exceptions: List[str] = [],
        skip: Callable[[str], bool] = lambda _: False,
    ) -> None:
        Rule.__init__(self, name, code, desc)
        assert isinstance(pattern, str)
        assert isinstance(warning_msg, str)
        assert isinstance(exceptions, list)
        assert all(isinstance(e, str) for e in exceptions)
        self._pattern = re.compile(pattern)
        self._warning_msg = warning_msg
        self._exception_patterns = exceptions
        self._exception_group = None
        self._exceptions = [re.compile(e) for e in exceptions]
        self._skip = skip

    def _match(self, line: str, start: int = 0) -> Union[Tuple[int, int], None]:
        exception_group = self._exception_group
        it = self._pattern.finditer(line, start)
        for x in it:
            exception = False
            if len(self._exceptions) > 0:
                x_group = x.groups().index(exception_group) + 1
                for e in self._exceptions:
                    ite = e.finditer(line)
                    for m in ite:
                        m_group = m.groups().index(exception_group) + 1
                        if m.start(m_group) == x.start(x_group):
                            exception = True
                            break
                    if exception:
                        break
            if not exception:
                return (x.start(), x.end())
        return None

    def skip(self, fname: str) -> bool:
        """
        Returns True if this rule should not be applied to fname.
        """
        return self._skip(fname)


###############################################################################
# File rules
###############################################################################


class ReplaceAnnoyUTF8Chars(Rule):
    """
    This rule replaces occurrences of annoying UTF characters from an entire
    file by their ascii equivalent.

    This could issue a warning rather than doing this replacement, but
    currently does not.
    """

    def __init__(self, name: str, code: str, desc: str = "") -> None:
        Rule.__init__(self, name, code, desc)
        self._chars = {
            "\xc2\x82": ",",  # High code comma
            "\xc2\x84": ",,",  # High code double comma
            "\xc2\x85": "...",  # Triple dot
            "\xc2\x88": "^",  # High carat
            "\xc2\x91": "\x27",  # Forward single quote
            "\xc2\x92": "\x27",  # Reverse single quote
            "\xc2\x93": "\x22",  # Forward double quote
            "\xc2\x94": "\x22",  # Reverse double quote
            "\xc2\x95": " ",
            "\xc2\x96": "-",  # High hyphen
            "\xc2\x97": "--",  # Double hyphen
            "\xc2\x99": " ",
            "\xc2\xa0": " ",
            "\xc2\xa6": "|",  # Split vertical bar
            "\xc2\xab": "<<",  # Double less than
            "\xc2\xbb": ">>",  # Double greater than
            "\xc2\xbc": "1/4",  # one quarter
            "\xc2\xbd": "1/2",  # one half
            "\xc2\xbe": "3/4",  # three quarters
            "\xca\xbf": "\x27",  # c-single quote
            "\xcc\xa8": "",  # modifier - under curve
            "\xcc\xb1": "",  # modifier - under line
        }

    def __call__(self, fname: str, lines: str, nr_warnings: int = 0) -> Tuple[int, str]:
        assert isinstance(fname, str)
        assert isinstance(lines, str)
        assert isinstance(nr_warnings, int)

        # Remove annoying characters
        def replace_chars(
            match: re.Match,
        ) -> str:
            char = match.group(0)
            return self._chars[char]

        return (
            nr_warnings,
            re.sub("(" + "|".join(self._chars.keys()) + ")", replace_chars, lines),
        )


class WarnRegexFile(WarnRegexBase):
    """
    A rule that issues a warning if a regex is matched in a file.
    """

    def __call__(self, fname: str, lines: str, nr_warnings: int = 0) -> Tuple[int, str]:
        assert isinstance(fname, str)
        assert isinstance(lines, str)
        assert isinstance(nr_warnings, int)
        if _is_tst_or_xml_file(fname):
            return nr_warnings, lines

        match = self._match(lines)
        while match is not None:
            line_num = lines.count("\n", 0, match[0])
            if not _is_rule_suppressed(fname, line_num + 1, self):
                _warn(self, fname, line_num, self._warning_msg, match)
                nr_warnings += 1
            match = self._match(lines, match[0] + len(self._pattern.pattern))
        return nr_warnings, lines


class ReplaceComments(Rule):
    """
    Replace between '#+' and the end of a line by '#+' and as many '@' as there
    were other characters in the line, call before replacing strings, and
    chars, and so on.

    This rule does not return any warnings.
    """

    def __call__(self, fname: str, lines: str, nr_warnings: int = 0) -> Tuple[int, str]:
        assert isinstance(fname, str)
        assert isinstance(lines, str)
        assert isinstance(nr_warnings, int)
        start = lines.find("#", 0)
        while start != -1 and _is_in_string(lines, start):
            start = lines.find("#", start + 1)
        while start != -1:
            end = lines.find("\n", start)
            repl = ""
            octo = start
            while octo < len(lines) and lines[octo] == "#":
                repl += "#"
                octo += 1
            repl += re.sub(r"[^!\s]", "@", lines[octo:end])
            lines = lines[:start] + repl + lines[end:]
            start = lines.find("#", end)
            while _is_in_string(lines, start):
                start = lines.find("#", start + 1)
        return nr_warnings, lines


class ReplaceBetweenDelimiters(Rule):
    """
    Replace all characters between delim1 and delim2 by #'s except possibly
    whitespace.

    This rule does not return any warnings.
    """

    def __init__(  # pylint: disable=too-many-arguments, too-many-positional-arguments
        self, name: str, code: str, desc: str, delim1: str, delim2: str
    ) -> None:
        Rule.__init__(self, name, code, desc)
        assert isinstance(delim1, str)
        assert isinstance(delim2, str)
        self._delims = [re.compile(delim1), re.compile(delim2)]

    def __find_next(self, which: int, lines: str, start: int) -> int:
        assert which in (0, 1)
        assert isinstance(lines, str)
        assert isinstance(start, int)
        if start >= len(lines):
            return -1
        delim = self._delims[which]
        match = delim.search(lines, start)
        while match is not None and (
            _is_escaped(lines, match.start())
            or _is_double_quote_in_char(lines, match.start())
        ):
            match = delim.search(lines, match.start() + len(delim.pattern))
        return -1 if match is None else match.start()

    def __call__(self, fname: str, lines: str, nr_warnings: int = 0) -> Tuple[int, str]:
        assert isinstance(fname, str)
        assert isinstance(lines, str)
        assert isinstance(nr_warnings, int)

        start = self.__find_next(0, lines, 0)
        while start != -1:
            end = self.__find_next(1, lines, start + 1)
            if end == -1:
                _error(
                    self,
                    fname,
                    lines.count("\n", 0, start),
                    f"Unmatched {self._delims[0].pattern}",
                )
            end += len(self._delims[1].pattern)
            repl = re.sub("[^\n ]", "@", lines[start:end])
            assert len(repl) == end - start

            lines = lines[:start] + repl + lines[end:]
            start = self.__find_next(0, lines, end + 1)
        return nr_warnings, lines


class ReplaceOutputTstOrXMLFile(Rule):
    """
    This rule removes the prefix 'gap>' or '>' if called with a line from a
    file with extension 'tst' or 'xml', if the line does not start with a
    'gap>' or '>', then the entire line is replaced with an equal number of
    '@''s.
    """

    def __init__(self, name: str, code: str, desc: str = "") -> None:
        Rule.__init__(self, name, code, desc)
        self._consuming = False
        self._sol_p = re.compile(r"(^|\n)gap>\s*")
        self._eol_p = re.compile(r"($|\n)")
        self._rep_p = re.compile(r"[^\n]")

    def __call__(self, fname: str, lines: str, nr_warnings: int = 0) -> Tuple[int, str]:
        assert isinstance(fname, str)
        assert isinstance(lines, str)
        assert isinstance(nr_warnings, int)
        if _is_tst_or_xml_file(fname):
            eol, out = 0, ""
            for sol in self._sol_p.finditer(lines):
                # Replace everything except '\n' with '@'
                out += re.sub(self._rep_p, "@", lines[eol : sol.start() + 1])
                eol = self._eol_p.search(lines, sol.end())
                if eol is None:
                    # Found a start of line marker without a corresponding end
                    # of line marker, i.e. no newline or end of line marker.
                    # This should not be possible, unless the file is somehow
                    # corrupt. Either way we just quietly skip the line and
                    # hope nothing bad happens.
                    continue
                eol = eol.end()

                out += lines[sol.end() : eol]
                while eol + 1 < len(lines) and lines[eol] == ">":
                    start = eol + 2
                    eol = self._eol_p.search(lines, start)
                    if eol is None:
                        # See above comment.
                        break
                    eol = eol.end()
                    out += lines[start:eol]
            return nr_warnings, out
        return nr_warnings, lines


class AnalyseLVars(Rule):  # pylint: disable=too-many-instance-attributes
    """
    This rule checks if there are unused local variables in a function.
    """

    SubRules = {
        "W040": Rule(
            "use-id-func",
            "W040",
            "Warns that [code]function(x) return x; end;[/code] can be "
            "replaced by [code]IdFunc[/code].",
        ),
        "W046": Rule(
            "unused-func-args",
            "W046",
            "Warns if there are unused function parameters (use [code]_[/code] to suppress).",
        ),
        "W047": Rule(
            "duplicate-function",
            "W047",
            "Warns if there is a duplicate function.",
        ),
    }

    def __init__(self, name: str, code: str, desc: str = "") -> None:
        Rule.__init__(self, name, code, desc)
        self.reset()

        self._function_p = re.compile(r"\bfunction\b")
        self._end_p = re.compile(r"\bend\b")
        self._local_p = re.compile(r"\blocal\b")
        self._var_p = re.compile(r"\w+\s*\w*")
        self._ass_var_p = re.compile(r"([a-zA-Z0-9_\.]+)\s*:=")
        self._use_var_p = re.compile(r"(\b\w+\b)(?!\s*:=)\W*")
        self._ws1_p = re.compile(r"[ \t\r\f\v]+")
        self._ws2_p = re.compile(r"\n[ \t\r\f\v]+")
        self._rec_p = re.compile(r"\brec\(")
        self._comment_p = re.compile(r" *#.*?\n")

    def reset(self) -> None:
        self._depth = -1
        self._func_args = []
        self._declared_lvars = []
        self._assigned_lvars = []
        self._used_lvars = []
        self._func_start_pos = []
        self._func_bodies = []
        self._func_position = []

    def _remove_recs_and_whitespace(self, lines: str) -> str:
        # Remove almost all whitespace
        lines = re.sub(self._comment_p, "\n", lines)
        lines = re.sub(self._ws1_p, " ", lines)
        lines = re.sub(self._ws2_p, "\n", lines)

        stack = []
        pos = 0
        # Replace rec( -> ) so that we do not match assignments inside records
        while pos < len(lines):
            if self._rec_p.search(lines, pos, pos + 5):
                stack.append(pos)
                pos += 4
            elif lines[pos] == "(" and len(stack) > 0:
                stack.append(None)
            elif lines[pos] == ")" and len(stack) > 0:
                start = stack.pop()
                if start is not None:
                    nr_newlines = lines.count("\n", start + 1, pos + 1)
                    var = self._use_var_p.findall(lines, start + 5, pos + 1)
                    var = [a for a in var if a not in _GAP_KEYWORDS]
                    var = " ".join(var)
                    replacement = "rec(" + var + "\n" * nr_newlines + ")"
                    lines = lines[: start + 1] + replacement + lines[pos + 1 :]
                    pos -= pos - start
                    pos += len(replacement)
            pos += 1
        assert len(stack) == 0
        return lines

    def _start_function(
        self, fname: str, lines: str, pos: int, nr_warnings: int
    ) -> Tuple[int, int]:
        self._depth += 1

        assert self._depth == len(self._func_args)
        assert self._depth == len(self._declared_lvars)
        assert self._depth == len(self._assigned_lvars)
        assert self._depth == len(self._used_lvars)
        assert self._depth == len(self._func_start_pos)

        self._func_args.append([])
        self._declared_lvars.append(set())
        self._assigned_lvars.append(set())
        self._used_lvars.append(set())
        self._func_start_pos.append(pos)

        start = lines.find("(", pos) + 1
        end = lines.find(")", start)
        new_args = self._var_p.findall(lines, start, end)
        args = self._func_args[self._depth]

        for var in new_args:
            var = [x.strip() for x in var.split(" ") if len(x) != 0]
            if len(var) == 1:
                var = var[0].strip()
            elif len(var) != 2 or var[0] not in ("readonly", "readwrite"):
                _error(
                    self,
                    fname,
                    lines.count("\n", 0, pos),
                    f'Invalid syntax: "{lines[start:end]}"',
                )
            else:
                var = var[1].strip()
            if var in args:
                _error(
                    self,
                    fname,
                    lines.count("\n", 0, pos),
                    f"Duplicate function argument: {var}",
                )
            elif var in _GAP_KEYWORDS:
                _error(
                    self,
                    fname,
                    lines.count("\n", 0, pos),
                    f"Function argument is keyword: {var}",
                )
            else:
                args.append(var)
        return end + 1, nr_warnings

    def _check_assigned_but_never_used_lvars(
        self, ass_lvars, fname, linenum, nr_warnings
    ):
        if len(ass_lvars) != 0 and not _is_rule_suppressed(fname, linenum + 1, self):
            ass_lvars = [key for key in ass_lvars if key.find(".") == -1]
            msg = f"Variables assigned but never used: {', '.join(sorted(ass_lvars))}"
            _warn(self, fname, linenum, msg)
            nr_warnings += 1
        return nr_warnings

    def _check_unused_lvars(self, decl_lvars, fname, linenum, nr_warnings):
        if len(decl_lvars) != 0 and not _is_rule_suppressed(fname, linenum + 1, self):
            decl_lvars = list(decl_lvars)
            msg = f"Unused local variables: {', '.join(sorted(decl_lvars))}"
            _warn(self, fname, linenum, msg)
            nr_warnings += 1
        return nr_warnings

    def _check_unused_func_args(self, func_args, fname, linenum, nr_warnings):
        func_args = [arg for arg in func_args if arg != "_"]
        if len(func_args) != 0:
            if not _is_rule_suppressed(
                fname, linenum + 1, AnalyseLVars.SubRules["W046"]
            ):
                msg = f"Unused function arguments: {', '.join(sorted(func_args))}"
                _warn(self.SubRules["W046"], fname, linenum, msg)
                nr_warnings += 1
        return nr_warnings

    def _check_dupl_funcs(self, func_body, fname, linenum, nr_warnings):
        num_func_lines = func_body.count("\n")
        limit = _GLOB_CONFIG["dupl-func-min-len"]
        if num_func_lines + 1 > limit:
            if not _is_rule_suppressed(
                fname, linenum + 1, AnalyseLVars.SubRules["W047"]
            ):
                func_body = re.sub(r"\n", "", func_body)
                try:
                    index = self._func_bodies.index(func_body)
                    _warn(
                        AnalyseLVars.SubRules["W047"],
                        fname,
                        linenum,
                        f"Duplicate function with {num_func_lines + 1} > {limit}"
                        ' lines (from "function" to "end" inclusive), previously '
                        f"defined at {self._func_position[index]}!",
                    )
                    nr_warnings += 1
                except ValueError:
                    self._func_bodies.append(func_body)
                    self._func_position.append(f"{fname}:{linenum + 1}")
        return nr_warnings

    # TODO use keyword args?
    def _check_for_return_fail_etc(  # pylint: disable=too-many-arguments, too-many-positional-arguments
        self, func_body, func_args_all, fname, linenum, nr_warnings
    ):
        num_func_lines = func_body.count("\n")
        if num_func_lines != 2:
            return nr_warnings

        line = func_body.split("\n")[-2]
        for bval, code in (
            ("true", "W036"),
            ("false", "W037"),
            ("fail", "W038"),
        ):
            if not _is_rule_suppressed(
                fname, linenum + 1, all_rules()[code]
            ) and re.search(rf"^\s*\breturn\b\s+\b{bval}\b", line):
                _warn(
                    all_rules()[code],
                    fname,
                    linenum,
                    f"Replace one line function by Return{bval.capitalize()}",
                )
                nr_warnings += 1
        if (
            len(func_args_all) > 1
            and not _is_rule_suppressed(fname, linenum + 1, all_rules()["W039"])
            and re.search(rf"^\s*\breturn\b\s+\b{func_args_all[0]}\s*;", line)
        ):
            _warn(
                all_rules()["W039"],
                fname,
                linenum,
                "Replace function(x, y, z, ...) return x; end; by ReturnFirst",
            )
            nr_warnings += 1
        if (
            len(func_args_all) == 1
            and not _is_rule_suppressed(
                fname, linenum + 1, AnalyseLVars.SubRules["W040"]
            )
            and re.search(rf"^\s*return\b\s+\b{func_args_all[0]}\s*;", line)
        ):
            _warn(
                self.SubRules["W040"],
                fname,
                linenum,
                'Replace "function(x) return x; end;" by IdFunc',
            )
            nr_warnings += 1
        return nr_warnings

    def _end_function(
        self, fname: str, lines: str, pos: int, nr_warnings: int
    ) -> Tuple[int, int]:
        if len(self._declared_lvars) == 0:
            _error(self, fname, lines.count("\n", 0, pos), "'end' outside function")

        self._depth -= 1

        ass_lvars = self._assigned_lvars.pop()
        decl_lvars = self._declared_lvars.pop()
        use_lvars = self._used_lvars.pop()
        func_args_all = self._func_args.pop()

        if len(self._used_lvars) > 0:
            self._used_lvars[-1] |= use_lvars  # union

        ass_lvars -= use_lvars  # difference
        ass_lvars &= decl_lvars  # intersection
        decl_lvars -= ass_lvars  # difference
        decl_lvars -= use_lvars  # difference
        func_args = set(func_args_all) - use_lvars  # difference

        linenum = lines.count("\n", 0, self._func_start_pos[-1])

        nr_warnings = self._check_assigned_but_never_used_lvars(
            ass_lvars, fname, linenum, nr_warnings
        )
        nr_warnings = self._check_unused_lvars(decl_lvars, fname, linenum, nr_warnings)
        nr_warnings = self._check_unused_func_args(
            func_args, fname, linenum, nr_warnings
        )

        func_body = lines[self._func_start_pos[-1] : pos]

        nr_warnings = self._check_dupl_funcs(func_body, fname, linenum, nr_warnings)

        nr_warnings = self._check_for_return_fail_etc(
            func_body, func_args_all, fname, linenum, nr_warnings
        )

        self._func_start_pos.pop()
        return pos + len("end"), nr_warnings

    def _add_declared_lvars(
        self, fname: str, lines: str, pos: int, nr_warnings: int
    ) -> Tuple[int, int]:
        end = lines.find(";", pos)
        lvars = self._declared_lvars[self._depth]
        args = self._func_args[self._depth]

        new_lvars = self._var_p.findall(lines, pos, end)
        for var in new_lvars:
            var = var.strip()
            if var in lvars:
                _error(
                    self,
                    fname,
                    lines.count("\n", 0, pos),
                    f"Name used for two local variables: {var}",
                )
            elif var in args:
                _error(
                    self,
                    fname,
                    lines.count("\n", 0, pos),
                    f"Name used for function argument and local variable: {var}",
                )
            elif var in _GAP_KEYWORDS:
                _error(
                    self,
                    fname,
                    lines.count("\n", 0, pos),
                    f"Local variable is keyword: {var}",
                )
            else:
                lvars.add(var)
        return end, nr_warnings

    def _find_lvars(
        self, fname: str, lines: str, pos: int, nr_warnings: int
    ) -> Tuple[int, int]:
        end = self._end_p.search(lines, pos + 1)
        func = self._function_p.search(lines, pos + 1)
        if end is None and func is None:
            return len(lines), nr_warnings
        if end is None and func is not None:
            _error(
                self,
                fname,
                lines.count("\n", 0, pos),
                "'function' without 'end'",
            )

        if func is not None and end is not None and func.start() < end.start():
            end = func.start()
        else:
            assert end is not None
            end = end.start()
        if self._depth >= 0:
            a_lvars = self._assigned_lvars[self._depth]
            a_lvars |= set(self._ass_var_p.findall(lines, pos, end))
            u_lvars = self._used_lvars[self._depth]
            u_lvars |= set(self._use_var_p.findall(lines, pos, end))
        return end, nr_warnings

    def __call__(self, fname: str, lines: str, nr_warnings: int = 0) -> Tuple[int, str]:
        assert isinstance(fname, str)
        assert isinstance(lines, str)
        assert isinstance(nr_warnings, int)
        if _is_tst_or_xml_file(fname):
            return nr_warnings, lines
        orig_lines = lines[:]
        lines = self._remove_recs_and_whitespace(lines)
        pos = 0
        while pos < len(lines):
            if self._function_p.search(lines, pos, pos + len("function")):
                pos, nr_warnings = self._start_function(fname, lines, pos, nr_warnings)
            elif self._local_p.search(lines, pos, pos + len("local") + 1):
                pos, nr_warnings = self._add_declared_lvars(
                    fname, lines, pos + len("local") + 1, nr_warnings
                )
            elif self._end_p.search(lines, pos, pos + len("end")):
                pos, nr_warnings = self._end_function(fname, lines, pos, nr_warnings)
            else:
                pos, nr_warnings = self._find_lvars(fname, lines, pos, nr_warnings)

        return nr_warnings, orig_lines


###############################################################################
# Line rules
###############################################################################


class LineTooLong(Rule):
    """
    Warn if the length of a line exceeds 80 characters.

    This rule does not modify the line.
    """

    def __init__(self, name: str, code: str, desc: str = "") -> None:
        Rule.__init__(self, name, code, desc)

    def __call__(
        self, fname: str, lines: str, linenum: int, nr_warnings: int = 0
    ) -> Tuple[int, str]:
        cols = _GLOB_CONFIG["columns"]
        if _is_tst_or_xml_file(fname):
            return nr_warnings, lines
        # NOTE: (reiniscirpons) We use len(lines[linenum]) instead of
        # len(linus[linenum]) - 1 since newlines are removed when we split
        # lines. We do not need to worry about CR LF (\r\n) since we specify
        # newline = None when reading opening a file, which automatically
        # converts \r\n to \n, for more info see:
        # https://docs.python.org/3/library/functions.html#open
        if len(lines[linenum]) > cols:
            _warn(
                self,
                fname,
                linenum,
                f"Line too long ({len(lines[linenum])} / {cols})",
            )
            nr_warnings += 1
        return nr_warnings, lines


class WarnRegexLine(WarnRegexBase):
    """
    Warn if regex matches.
    """

    def __call__(
        self, fname: str, lines: str, linenum: int, nr_warnings: int = 0
    ) -> Tuple[int, str]:
        assert isinstance(fname, str)
        assert isinstance(lines, list)
        assert isinstance(linenum, int)
        assert linenum < len(lines)
        assert isinstance(nr_warnings, int)
        if not self.skip(fname):
            match = self._match(lines[linenum])
            if match is not None:
                _warn(self, fname, linenum, self._warning_msg, match)
                return nr_warnings + 1, lines
        return nr_warnings, lines


class WhitespaceOperator(WarnRegexLine):
    """
    Instances of this class produce a warning whenever the whitespace around an
    operator is incorrect.
    """

    def __init__(  # pylint: disable=too-many-arguments, too-many-positional-arguments
        self,
        name: str,
        code: str,
        desc: str,
        op: str,
        exceptions: List[str] = [],
    ):  # pylint: disable=W0102
        WarnRegexLine.__init__(self, name, code, desc, "", "")
        assert isinstance(op, str)
        assert op[0] != "(" and op[-1] != ")"
        assert exceptions is None or isinstance(exceptions, list)
        assert all(isinstance(e, str) for e in exceptions)
        gop = "(" + op + ")"
        pattern = rf"(\S{gop}|{gop}\S|\s{{2,}}{gop}|{gop}\s{{2,}})"
        self._pattern = re.compile(pattern)
        self._warning_msg = "Wrong whitespace around operator " + op.replace("\\", "")
        exceptions = [e.replace(op, "(" + op + ")") for e in exceptions]
        self._exceptions = [re.compile(e) for e in exceptions]
        self._exception_group = op.replace("\\", "")


class UnalignedPatterns(Rule):
    """
    This rule checks if pattern occurs in consecutive lines and that they are
    aligned.
    """

    # TODO use keyword args?
    def __init__(  # pylint: disable=too-many-arguments, too-many-positional-arguments
        self,
        name: str,
        code: str,
        desc: str,
        pattern: str,
        group: int,
        msg: str,
    ) -> None:
        Rule.__init__(self, name, code, desc)
        assert isinstance(pattern, str)
        assert isinstance(group, int)
        assert isinstance(msg, str)
        self._last_line_col = None
        self._pattern = re.compile(pattern)
        self._group = group
        self._msg = msg

    def __call__(
        self, fname: str, lines: List[str], linenum: int, nr_warnings: int = 0
    ) -> Tuple[int, List[str]]:
        assert isinstance(fname, str)
        assert isinstance(lines, list)
        assert isinstance(linenum, int)
        assert isinstance(nr_warnings, int)
        if (
            _is_rule_suppressed(fname, linenum, self)
            or _is_tst_or_xml_file(fname)
            or linenum == 0
        ):
            return nr_warnings, lines
        col = self._pattern.search(lines[linenum])
        if col is not None and self._last_line_col is not None:
            group = self._group
            if col.start(group) != self._last_line_col.start(group):
                _warn(
                    self,
                    fname,
                    linenum,
                    self._msg,
                    (col.start(group), col.end(group)),
                )
                return nr_warnings + 1, lines
        self._last_line_col = col
        return nr_warnings, lines

    def reset(self) -> None:
        self._last_line_col = None


class Indentation(Rule):
    """
    This class checks that the indentation level is correct in a given line.

    Certain keywords increase the indentation level, while others decrease it,
    this rule checks that a given line has the minimum indentation level
    required.
    """

    def __init__(self, name: str, code: str, desc: str = "") -> None:
        Rule.__init__(self, name, code, desc)
        self.reset()
        self._indent = re.compile(r"^(\s*)\S")
        self._blank = re.compile(r"^\s*$")
        self._before = []
        self._after = []
        self._msg = "Bad indentation: found %d but expected at least %d"

    # Really initialize outside __init__ because rules are instanstiated
    # **before** __GLOB_CONFIG is initialised.
    def __init_real(self):
        if len(self._before) == 0:
            assert len(self._after) == 0
            ind = _GLOB_CONFIG["indentation"]
            self._before = [
                (re.compile(r"(\W|^)(elif|else)(\W|$)"), -ind),
                (re.compile(r"(\W|^)end(\W|$)"), -ind),
                (re.compile(r"(\W|^)(od|fi)(\W|$)"), -ind),
                (re.compile(r"(\W|^)until(\W|$)"), -ind),
            ]
            self._after = [
                (re.compile(r"(\W|^)(then|do)(\W|$)"), -ind),
                (re.compile(r"(\W|^)(repeat|else)(\W|$)"), ind),
                (re.compile(r"(\W|^)function(\W|$)"), ind),
                (
                    re.compile(r"(\W|^)(if|for|while|elif|atomic)(\W|$)"),
                    2 * ind,
                ),
            ]

    def __call__(
        self, fname: str, lines: List[str], linenum: int, nr_warnings: int = 0
    ) -> Tuple[int, List[str]]:
        assert isinstance(fname, str)
        assert isinstance(lines, list)
        assert isinstance(linenum, int)
        assert isinstance(nr_warnings, int)
        assert self._expected >= 0
        self.__init_real()

        if (
            _is_rule_suppressed(fname, linenum, self)
            or _is_tst_or_xml_file(fname)
            or self._blank.search(lines[linenum])
        ):
            return nr_warnings, lines

        for pair in self._before:
            if pair[0].search(lines[linenum]):
                self._expected += pair[1]

        indent = self._get_indent_level(lines[linenum])
        if indent < self._expected:
            _warn(
                self,
                fname,
                linenum,
                self._msg % (indent, self._expected),
                (0, indent),
            )
            nr_warnings += 1

        for pair in self._after:
            if pair[0].search(lines[linenum]):
                self._expected += pair[1]
        return nr_warnings, lines

    def _get_indent_level(self, line: str) -> int:
        indent = self._indent.search(line)
        assert indent
        return len(indent.group(1))

    def reset(self):
        self._expected = 0


@functools.cache
def all_rules() -> dict[str, Rule]:
    """
    Returns an iterator of all the current rules.
    """
    __init_rules()
    return {
        x.code: x
        for x in itertools.chain(
            iter(_FILE_RULES),
            iter(_LINE_RULES),
            iter(AnalyseLVars.SubRules.values()),
        )
    }


###############################################################################
###############################################################################


def __explain(args: Dict[str, Any]) -> None:
    if "explain" not in args or len(args["explain"]) == 0:
        return
    args["explain"] = args["explain"].split(",")
    args["explain"].sort()
    if len(args["explain"]) == 1 and args["explain"][0] == "all":
        args["explain"] = [x for x in all_rules().keys() if not x.startswith("M")]

    rows = []
    for name_or_code in args["explain"]:
        try:
            rule = next(
                x for x in all_rules().values() if name_or_code in (x.code, x.name)
            )
            rows.append((rule.code, rule.name, rule.desc))
        except StopIteration:
            _info_action(f'CANNOT EXPLAIN invalid rule name or code "{name_or_code}"')
    rows.sort()
    rows = list(dict.fromkeys(rows))
    if len(rows) > 0:
        table = Table(title="gaplint rules", show_lines=True, width=90, min_width=80)

        table.add_column("Code", justify="left", style="bright_red", no_wrap=True)
        table.add_column("Name", justify="left", style="bright_green")
        table.add_column(
            "Description", justify="left", style="bright_blue", no_wrap=False
        )
        for code, name, desc in rows:
            table.add_row(code, name, desc)
        console = Console()
        console.print(table)
    sys.exit(0)


def _parse_cmd_line_args(kwargs) -> Dict[str, Any]:
    """
    Pass kwargs as an argument for the check for \"files\" o/w not needed.
    Note that the default value for each argument is set to None here, so that
    we can detect where a parameter was actually set in __merge_args. The
    actual default value is installed in __merge_args.
    """
    script_name = os.path.basename(sys.argv[0])
    if script_name in ["pytest", "py.test"]:
        return {}
    parser = argparse.ArgumentParser(prog="gaplint", usage="%(prog)s [options]")
    if "files" not in kwargs:
        parser.add_argument("files", nargs="*", help="the files to lint")

    default = _DEFAULT_CONFIG["max-warnings"]
    parser.add_argument(
        "--max-warnings",
        nargs="?",
        type=int,
        default=None,
        help=f"maximum number of warnings before giving up (default: {default})",
    )

    default = _DEFAULT_CONFIG["columns"]
    parser.add_argument(
        "--columns",
        nargs="?",
        type=int,
        default=None,
        help=f"maximum number of characters per line (default: {default})",
    )

    default = _DEFAULT_CONFIG["disable"]
    parser.add_argument(
        "--disable",
        nargs="?",
        type=str,
        default=None,
        help=f"comma separated rule names and/or codes to disable (default: {default})",
    )

    default = _DEFAULT_CONFIG["dupl-func-min-len"]
    parser.add_argument(
        "--dupl-func-min-len",
        dest="dupl_func_min_len",
        default=None,
        type=int,
        nargs="?",
        help="report warnings for duplicate functions with more than "
        + f"this many lines (default: {default})",
    )

    parser.add_argument(
        "--enable",
        nargs="?",
        type=str,
        default=None,
        help=f"comma separated rule names and/or codes to enable (default: {default})",
    )

    default = _DEFAULT_CONFIG["indentation"]
    parser.add_argument(
        "--indentation",
        nargs="?",
        type=int,
        default=None,
        help=f"indentation of nested statements (default: {default})",
    )

    default = _DEFAULT_CONFIG["column-range"]
    parser.add_argument(
        "--column-range",
        dest="column_range",
        action="store_true",
        default=default,
        help=f"display a column range when reporting (default: {default})",
    )

    default = _DEFAULT_CONFIG["silent"]
    parser.add_argument(
        "--silent",
        dest="silent",
        action="store_true",
        default=None,
        help=f"silence all warnings (default: {default})",
    )

    default = _DEFAULT_CONFIG["verbose"]
    parser.add_argument(
        "--verbose",
        dest="verbose",
        action="store_true",
        default=None,
        help=f"enable verbose mode (default: {default})",
    )

    vers_num = version("gaplint")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s version {vers_num}",
    )

    parser.add_argument(
        "--explain",
        nargs="?",
        type=str,
        default="",
        help=f"comma separated rule names and/or codes to explain (default: {default})",
    )

    args = parser.parse_args()

    result = {}
    for arg in dir(args):
        if not arg.startswith("__") and not callable(getattr(args, arg)):
            key = arg.replace("_", "-")
            val = getattr(args, arg)
            result[key] = val

    if isinstance(result["disable"], str):
        result["disable"] = set(result["disable"].split(","))
    if isinstance(result["enable"], str) and result["enable"] != "all":
        result["enable"] = set(result["enable"].split(","))
    return result


def _parse_yml_config() -> Tuple[str, Dict[str, Any]]:
    config_yml_fname, yml_dic = __get_yml_dict()
    for key in ("disable", "enable"):
        if yml_dic is not None and key in yml_dic:
            if not isinstance(yml_dic[key], list) or any(
                not isinstance(x, str) for x in yml_dic[key]
            ):
                _info_action(
                    f"IGNORING configuration value '{key}' expected 'list'"
                    + f" but found '{type(yml_dic[key]).__name__}' ({config_yml_fname})"
                )
                del yml_dic[key]
            else:
                yml_dic[key] = set(yml_dic[key])

    return config_yml_fname, yml_dic


def _parse_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    # TODO check all the args
    if "disable" in kwargs and isinstance(kwargs["disable"], str):
        kwargs["disable"] = set(kwargs["disable"].split(","))
    if "enable" in kwargs and isinstance(kwargs["enable"], str):
        kwargs["enable"] = set(kwargs["enable"].split(","))
    if "max_warnings" in kwargs:
        kwargs["max-warnings"] = kwargs["max_warnings"]
        del kwargs["max_warnings"]
    return kwargs


def __normalize_args(args: Dict[str, Any], where: str) -> Dict[str, Any]:
    # check for unknown keys
    unknown = {key for key in args if key not in _DEFAULT_CONFIG}
    if len(unknown) != 0:
        _info_action(
            f"IGNORING unknown configuration value{'s'[:len(unknown)^1]}: {unknown} {where}"
        )
    # remove unknown keys
    for key in unknown:
        del args[key]

    unknown.clear()
    # check that the values have the correct type
    for key, val in args.items():
        expected = type(_DEFAULT_CONFIG[key])
        # val is None means that it wasn't specified
        if val is not None and (
            not (
                isinstance(val, expected) or (key == "enable" and isinstance(val, set))
            )
        ):
            _info_action(
                f"IGNORING configuration value '{key}' expected a {expected.__name__}"
                + f" but found {type(args[key]).__name__} {where}"
            )
            unknown.add(key)
    # remove known keys with bad values
    for key in unknown:
        del args[key]

    # Adding missing keys but leave the value unspecified, the default value or
    # value specified elsewhere are installed in __merge_args
    for key, val in _DEFAULT_CONFIG.items():
        if key not in args:
            args[key] = None
    return args


# TODO fix too many branches
def __merge_args(  # pylint: disable=too-many-branches
    cmd_line_args: Dict[str, Any],
    kwargs: Dict[str, Any],
    config_yml_fname: str,
    yml_dic: Dict[str, Any],
) -> Dict[str, Any]:
    """
    This function merges the 3 possible sources of arguments/configuration
    options:
    1. keywords args (only if not running gaplint as a script)
    2. command line args (only if running gaplint as a script)
    3. yaml configuration file.

    This function returns the merged version of the arguments from these 3
    sources consisting of:
    * any value is taken from any of the 3 sources if specified (i.e. not None).
    * if there are conflicting specified values in the 3 sources, then those in
      kwargs and from the command line are given precedence. Note that it isn't
      possible to have both kwargs and command line options specified, so these
      shouldn't ever conflict.
    """

    def conflict_msg(key, val1, where1, val2, where2):
        if isinstance(val1, set):
            val1 = ", ".join(sorted(list(val1)))
        if isinstance(val2, set):
            val2 = ", ".join(sorted(list(val2)))
        _info_action(
            f"CONFLICTING configuration values for '{key}' found '{val1}' in "
            + f"{where1} and '{val2}' in {where2}, using '{val1}'!"
        )

    args = deepcopy(cmd_line_args)
    for key, val in args.items():
        if key in ("enable", "disable"):
            continue
        if val is None:
            if kwargs[key] is not None:
                args[key] = kwargs[key]
            elif yml_dic[key] is not None:
                args[key] = yml_dic[key]
            else:
                args[key] = _DEFAULT_CONFIG[key]
            if (
                kwargs[key] is not None
                and yml_dic[key] is not None
                and kwargs[key] != yml_dic[key]
            ):
                conflict_msg(
                    key,
                    kwargs[key],
                    "keyword arguments",
                    yml_dic[key],
                    config_yml_fname,
                )
        else:
            assert kwargs[key] is None
            if yml_dic[key] is not None and yml_dic[key] != val:
                conflict_msg(
                    key,
                    val,
                    "command line arguments",
                    yml_dic[key],
                    config_yml_fname,
                )
        e, d = "enable", "disable"
        if cmd_line_args[e] is not None or cmd_line_args[d] is not None:
            args[e], args[d] = cmd_line_args[e], cmd_line_args[d]
        elif kwargs[e] is not None or kwargs[d] is not None:
            args[e], args[d] = kwargs[e], kwargs[d]
        elif yml_dic[e] is not None or yml_dic[d] is not None:
            args[e], args[d] = yml_dic[e], yml_dic[d]
        else:
            args[e], args[d] = None, _DEFAULT_CONFIG[d]
        # TODO conflict message for enable, disable

    return args


def __normalize_disabled_rules(args: Dict[str, Any], where: str) -> Dict[str, Any]:
    # Rules can only be enabled globally, at the command line, as a keyword
    # argument when calling gaplint as a function in python, or in a config
    # file.
    def normalize_codes(codes_and_or_names: Set[str]) -> Set[str]:
        codes = set()
        for code_or_name in codes_and_or_names:
            if __can_disable_rule_name_or_code(code_or_name, where):
                codes.add(Rule.to_code(code_or_name))
        return codes

    assert args["disable"] is not None or args["enable"] is not None
    if args["disable"] is not None and args["enable"] is not None:
        sys.stderr.write(
            f"ERROR: found both configuration values "
            f"'enable' and 'disable' {where}, use one or the other, "
            "not both\n"
        )
        sys.exit(1)

    # TODO clean up from here
    if args["disable"] is None:
        disabled = set()
    else:
        disabled = normalize_codes(args["disable"])

    all_codes = Rule.all_suppressible_codes()
    if args["enable"] is None or args["enable"] == "all":
        enabled = all_codes
    else:
        enabled = normalize_codes(args["enable"])

    disabled |= all_codes - enabled  # union

    args["disable"] = disabled
    args["enable"] = None

    # Special case for AnalyseLVars.SubRules since they are covered by two
    # codes: W000; and the subrule code.
    # TODO double check still ok
    if (
        any(x.code in enabled for x in AnalyseLVars.SubRules.values())
        and "W000" in args["disable"]
    ):
        args["disable"].remove("W000")
    return args


def __normalize_files(args: Dict[str, Any]):
    valid_extensions = set(["g", "g.txt", "gi", "gd", "gap", "tst", "xml"])
    files = []
    for fname in args["files"]:
        if not exists(fname):
            _info_action(f"SKIPPING {fname}: file does not exist!")
        elif not isfile(fname):
            _info_action(f"SKIPPING {fname}: not a file!")
        elif (
            fname.split(".")[-1] not in valid_extensions
            and ".".join(fname.split(".")[-2:]) not in valid_extensions
        ):
            _info_action(f"IGNORING {fname}: not a valid file extension")
        else:
            files.append(fname)
    args["files"] = files
    return args


###############################################################################
# Globals
###############################################################################


def __init_globals(
    args: Dict[str, Any],
) -> None:
    global _SILENT, _VERBOSE, _GLOB_CONFIG, _LINE_SUPPRESSIONS, _FILE_SUPPRESSIONS, _COLUMN_RANGE  # pylint: disable=global-statement

    # init global config values
    _SILENT = args["silent"]
    _VERBOSE = args["verbose"]
    _COLUMN_RANGE = args["column-range"]
    _GLOB_CONFIG = args
    # Clear the suppressions in case we are running as a module (i.e. in the
    # tests)
    _GLOB_SUPPRESSIONS.clear()
    _LINE_SUPPRESSIONS = {}
    _FILE_SUPPRESSIONS = {}

    # init suppressions
    for code in args["disable"]:
        # TODO remove this, just remove the rule from the list
        _GLOB_SUPPRESSIONS.add(code)
    __init_file_and_line_suppressions(args)


def __config_yml_path(dir_path: str) -> Union[None, str]:
    """
    Recursive function that takes the path of a directory to search and
    searches for the gaplint.yml config script. If the script is not found the
    function is then called on the parent directory - recursive case. This
    continues until we encounter a directory .git in our search (script not
    found, returns None), locate the script (returns script path), or until the
    root directory has been searched (script not found, returns None) - base
    cases A, B, C.
    """
    assert isinstance(dir_path, str)
    assert isdir(dir_path)
    entries = listdir(dir_path)

    if ".gaplint.yml" in entries:
        yml_path = abspath(join(dir_path, ".gaplint.yml"))
        return yml_path
    if ".git" in entries and isdir(abspath(join(dir_path, ".git"))):
        return None

    pardir_path = abspath(join(dir_path, os.pardir))
    if pardir_path == dir_path:
        return None
    return __config_yml_path(pardir_path)  # recursive call


def __get_yml_dict() -> Tuple[str, Dict[str, Any]]:
    config_yml_fname = __config_yml_path(os.getcwd())
    if config_yml_fname is None:
        return "", {}

    _info_action(f"Using configurations in {config_yml_fname}")
    try:
        with open(
            config_yml_fname, "r", encoding="utf-8", newline=None
        ) as config_yml_file:
            yml_dic = yaml.load(config_yml_file, Loader=yaml.FullLoader)
    except (yaml.YAMLError, IOError):
        _info_action("IGNORING {config_yml_fname}: error parsing YAML")
        return "", {}
    # yml_dic can be None if the file is empty
    if yml_dic is None:
        yml_dic = {}
    return config_yml_fname, yml_dic


###############################################################################
# The list of rules (the order is important!)
###############################################################################


def __init_rules() -> None:
    global _FILE_RULES, _LINE_RULES  # pylint: disable=global-statement
    if len(_FILE_RULES) != 0:
        return
    _FILE_RULES = [
        ReplaceAnnoyUTF8Chars("replace-weird-chars", "M000", ""),
        ReplaceComments("replace-comments", "M002", ""),
        ReplaceOutputTstOrXMLFile("replace-output-tst-or-xml-file", "M001", ""),
        ReplaceBetweenDelimiters(
            "replace-multiline-strings", "M003", "", r'"""', r'"""'
        ),
        ReplaceBetweenDelimiters("replace-strings", "M004", "", r'"', r'"'),
        ReplaceBetweenDelimiters("replace-chars", "M005", "", r"'", r"'"),
        AnalyseLVars(
            "analyse-lvars",
            "W000",
            "Warns if there are declared local variables that are not used or "
            "assigned but not used.",
        ),
        WarnRegexFile(
            "consecutive-empty-lines",
            "W001",
            "Warns if there are consecutive empty lines.",
            r"\n\s*\n\s*\n",
            "Consecutive empty lines",
        ),
        WarnRegexFile(
            "assign-then-return",
            "W033",
            "Warns if a variable is pointlessly assigned and then immediately returned.",
            r"(\w+)\s*:=[^;]*;\n\s*return\s+(\1);",
            "Pointless assignment immediately returned",
        ),
        WarnRegexFile(
            "1-line-function",
            "W034",
            "Warns that a one line function could be a lambda.",
            r"\bfunction\b\s*\((?!(arg|.+\.\.\.)).*\).*?\n.*?\breturn\b.*?\n.*?\bend\b",
            "One line function could be a lambda",
        ),
        WarnRegexFile(
            "if-then-return-true-else-return-false",
            "W044",
            "Warns that [code]if XYZ then return true; else return "
            "false; fi;[/code] by [code]return XYZ;[/code]",
            r"\bif\b.*?\bthen\b\n?\s*return\s*true;\n?\s*else\s*\n?\s*return\s*false;\n?\s*fi;",
            'Replace "if X then return true; else return false; fi;" by "return X;"',
        ),
        WarnRegexFile(
            "if-then-return-false-else-return-true",
            "W045",
            "Warns that [code]if XYZ then return false; else return "
            "true; fi;[/code] by [code]return not XYZ;[/code]",
            r"\bif\b.*?\bthen\b\n?\s*return\s*false;\n?\s*else\s*\n?\s*return\s*true;\n?\s*fi;",
            'Replace "if X then return false; else return true; fi;" by "return not X;"',
        ),
    ]
    _LINE_RULES = [
        LineTooLong(
            "line-too-long",
            "W002",
            "Warns if there is a line which is longer than the "
            "configured maximum (defaults to [code]80[/code]).",
        ),
        Indentation("indentation", "W003", "Warns if a line is under indented."),
        UnalignedPatterns(
            "align-assignments",
            "W004",
            "Warns if there are assignments in consecutive lines that are not "
            "aligned.",
            r":=",
            0,
            "Unaligned assignments in consecutive lines",
        ),
        UnalignedPatterns(
            "align-trailing-comments",
            "W005",
            "Warns if there are trailing comments in consecutive lines that "
            "are not aligned.",
            r"\w.*(#+)",
            1,
            "Unaligned comments in consecutive lines",
        ),
        UnalignedPatterns(
            "align-comments",
            "W006",
            "Warns if there are non-trailing comments in consecutive lines "
            "that are not aligned.",
            r"^\s*(#+)",
            1,
            "Unaligned comments in consecutive lines",
        ),
        WarnRegexLine(
            "trailing-whitespace",
            "W007",
            "Warns if there is trailing whitespace at the end of a line.",
            r"^(?!#\!).*\s+$",
            "Trailing whitespace",
            [],
            _is_tst_or_xml_file,
        ),
        WarnRegexLine(
            "no-space-after-comment",
            "W008",
            "Warns if there is no space after any number of # is a line.",
            r"#+[^ \t\n\r\f\v#\!]",
            "No space after comment",
        ),
        WarnRegexLine(
            "not-enough-space-before-comment",
            "W009",
            "Warns if there is not enough space before the first # in any line"
            " (defaults to [code]2[/code]).",
            r"[^ \t\n\r\f\v#]\s?#",
            "At least 2 spaces before comment",
        ),
        WarnRegexLine(
            "space-after-comma",
            "W010",
            "Warns if a comma is followed by more than [code]1[/code] space.",
            r",(([^,\s]+)|(\s{2,})\w)",
            "Exactly one space required after comma",
        ),
        WarnRegexLine(
            "space-before-comma",
            "W011",
            "Warns if a comma is preceded by a space.",
            r"\s,",
            "No space before comma",
        ),
        WarnRegexLine(
            "space-after-bracket",
            "W012",
            "Warns if there is a space after an opening bracket.",
            r"(\(|\[|\{)[ \t\f\v]",
            "No space allowed after bracket",
        ),
        WarnRegexLine(
            "space-before-bracket",
            "W013",
            "Warns if there is a space before a closing bracket.",
            r"\s(\)|\]|\})",
            "No space allowed before bracket",
        ),
        WarnRegexLine(
            "multiple-semicolons",
            "W014",
            "Warns if there is more than one semicolon in a line.",
            r";.*;",
            "More than one semicolon",
            [],
            _is_tst_or_xml_file,
        ),
        WarnRegexLine(
            "keyword-function",
            "W015",
            "Warns if the keyword [code]function[/code] is not followed by an open bracket.",
            r"\bfunction\b[^\(]",
            "Keyword 'function' not followed by (",
        ),
        WarnRegexLine(
            "whitespace-op-assign",
            "W016",
            "Warns if there is not exactly 1 space after an assignment "
            " ([code]:=[/code]).",
            r"(\S:=|:=(\S|\s{2,}))",
            "Wrong whitespace around operator :=",
        ),
        WarnRegexLine(
            "tabs",
            "W017",
            "Warns if there are tabs.",
            r"\t",
            "There are tabs in this line, replace with spaces",
        ),
        WarnRegexLine(
            "function-local-same-line",
            "W018",
            "Warns if the keywords [code]function[/code] and"
            " [code]local[/code] appear in the same line.",
            r"function\W.*\Wlocal\W",
            "Keywords 'function' and 'local' in the same line",
        ),
        WarnRegexLine(
            "whitespace-op-minus",
            "W019",
            "Warns if there is not exactly 1 space either side of a minus "
            "([code]-[/code]) operator",
            r"(return|\^|\*|,|=|\.|>) - \d",
            "Wrong whitespace around operator -",
        ),
        WhitespaceOperator(
            "whitespace-op-plus",
            "W020",
            "Warns if there is not exactly 1 space either side of a plus "
            "([code]+[/code]) operator.",
            r"\+",
            [r"^\s*\+"],
        ),
        WhitespaceOperator(
            "whitespace-op-multiply",
            "W021",
            "Warns if there is not exactly 1 space either side of a multiply "
            "([code]*[/code]) operator.",
            r"\*",
            [r"^\s*\*", r"\\\*"],
        ),
        WhitespaceOperator(
            "whitespace-op-negative",
            "W022",
            "Warns if there is not exactly 1 space preceding a negative "
            "([code]-[/code]) operator.",
            r"-",
            [
                r"-(>|\[)",
                r"(\^|\*|,|=|\.|>) -",
                r"(\(|\[)-",
                r"return -infinity",
                r"return -\d",
            ],
        ),
        WhitespaceOperator(
            "whitespace-op-less-than",
            "W023",
            "Warns if there is not exactly 1 space either side of a "
            "less-than ([code]<[/code]) operator.",
            r"\<",
            [r"^\s*\<", r"\<(\>|=)", r"\\\<"],
        ),
        WhitespaceOperator(
            "whitespace-op-less-equal",
            "W024",
            "Warns if there is not exactly 1 space either side of a less-than "
            "or equal-to ([code]<=[/code]) operator.",
            r"\<=",
        ),
        WhitespaceOperator(
            "whitespace-op-more-than",
            "W025",
            "Warns if there is not exactly 1 space either side of a "
            "greater-than ([code]>[/code]) operator.",
            r"\>",
            [r"(-|\<)\>", r"\>="],
        ),
        WhitespaceOperator(
            "whitespace-op-more-equal",
            "W026",
            "Warns if there is not exactly 1 space either side of "
            "a greater than or equal to ([code]>=[/code]) operator.",
            r"\>=",
        ),
        WhitespaceOperator(
            "whitespace-op-equals",
            "W027",
            "Warns if there is not exactly 1 space either side of an equals "
            "([code]=[/code]) operator.",
            r"=",
            [r"(:|>|<)=", r"^\s*=", r"\\="],
        ),
        WhitespaceOperator(
            "whitespace-op-lambda",
            "W028",
            "Warns if there is not exactly 1 space either side of the mapping "
            "([code]->[/code]) operator in a lambda function.",
            r"->",
        ),
        WhitespaceOperator(
            "whitespace-op-divide",
            "W029",
            "Warns if there is not exactly 1 space either side of "
            "a division ([code]/[/code]) operator.",
            r"\/",
            [r"\\\/"],
        ),
        WhitespaceOperator(
            "whitespace-op-power",
            "W030",
            "Warns if there is not exactly 1 space either side of a power "
            "([code]^[/code]) operator.",
            r"\^",
            [r"^\s*\^", r"\\\^"],
        ),
        WhitespaceOperator(
            "whitespace-op-not-equal",
            "W031",
            "Warns if there is not exactly 1 space either side of a not-equal"
            " ([code]<>[/code]) operator.",
            r"<>",
            [r"^\s*<>"],
        ),
        WhitespaceOperator(
            "whitespace-double-dot",
            "W032",
            "Warns if there is not exactly 1 space either side of an arithmetic "
            "progression ([code]..[/code]) operator.",
            r"\.\.",
            [r"\.\.(\.|\))"],
        ),
        WarnRegexLine(
            "pointless-lambda",
            "W035",
            "Warns when there are lambda functions of the form "
            "[code]x -> f(x)[/code] which can be replaced by [code]f[/code].",
            r"\b(\w+)\b\s*->\s*\b\w+\(\1\)\s*\)",
            "Replace x -> f(x) by f",
        ),
        WarnRegexLine(
            "use-return-true",
            "W036",
            "Warns that [code]x -> true[/code] can be replaced by "
            "[code]ReturnTrue[/code].",
            r"\b(\w+)\b\s*->\s*\btrue\b\s*\)",
            "Replace x -> true by ReturnTrue",
        ),
        WarnRegexLine(
            "use-return-false",
            "W037",
            "Warns that [code]x -> false[/code] can be replaced by "
            "[code]ReturnFalse[/code].",
            r"\b(\w+)\b\s*->\s*\bfalse\b\s*\)",
            "Replace x -> false by ReturnFalse",
        ),
        WarnRegexLine(
            "use-return-fail",
            "W038",
            "Warns that [code]x -> fail[/code] can be replaced by "
            "[code]ReturnFail[/code].",
            r"\b(\w+)\b\s*->\s*\bfail\b\s*\)",
            "Replace x -> fail by ReturnFail",
        ),
        WarnRegexLine(
            "use-return-first",
            "W039",
            "Warns to replace lambdas of the form [code]{x, y, z, ...} ->"
            " x[/code] by [code]ReturnFirst[/code].",
            r"{\s*(\w+)\s*,(\s*\w+\s*,?)+}\s*->\s*\b\1\b(\)|;)",
            'Replace "{x, y, z, ...} -> x" by ReturnFirst',
        ),
        WarnRegexLine(
            "no-semicolon-after-function",
            "W041",
            "Warns if there's an unnecessary semicolon in "
            "[code]function(.*);[/code].",
            r"\bfunction\b\s*\([^)]*\)\s*;",
            'Remove unnecessary semicolon in "function(.*);"',
        ),
        WarnRegexLine(
            "use-not-eq",
            "W042",
            "Warns to use [code]x <> y[/code] instead of " "[code]not x = y[/code].",
            r"\bif\s+not\s+\w+\s*=",
            'Use "x <> y" instead of "not x = y"',
        ),
        WarnRegexLine(
            "dont-use-arg",
            "W043",
            "Warns to use [code]function(arg...)[/code] instead of "
            "[code]function(arg)[/code].",
            r"\bfunction\b\s*\(\s*\barg\b\s*\)",
            "Use arg... instead of arg",
        ),
        WarnRegexLine(
            "use-remove-not-unbind",
            "W048",
            "Warns that [code]Unbind(x[Length[x]])[/code] can be replaced by"
            " [code]Remove(x)[/code].",
            r"\bUnbind\((\w+)\[Length\(\1\)\]\)",
            "Replace Unbind(foo[Length(foo)]) by Remove(foo)",
        ),
    ]


###############################################################################
# File and line suppressions - run after defining RULES
###############################################################################


def __can_disable_rule_name_or_code(name_or_code: str, where: str) -> bool:
    assert isinstance(name_or_code, str)
    assert isinstance(where, str)

    if name_or_code == "all":
        return True
    for rule in all_rules().values():
        if name_or_code in (rule.name, rule.code):
            if rule.code[0] == "M":
                _info_action(f'IGNORING cannot disable rule "{name_or_code}" {where}')
                return False
            return True
    _info_action(f'IGNORING invalid rule name or code "{name_or_code}" {where}')
    return False


def __add_file_suppressions(
    names_or_codes: List[str], fname: str, linenum: int
) -> None:
    assert isinstance(names_or_codes, list)
    assert all(isinstance(x, str) for x in names_or_codes)
    assert isinstance(fname, str)
    assert isinstance(linenum, int)

    for name_or_code in names_or_codes:
        assert isinstance(name_or_code, str)
        if __can_disable_rule_name_or_code(name_or_code, f"at {fname}:{linenum + 1}"):
            if fname not in _FILE_SUPPRESSIONS:
                _FILE_SUPPRESSIONS[fname] = {}
            code = Rule.to_code(name_or_code)
            _FILE_SUPPRESSIONS[fname][code] = None


def __add_line_suppressions(
    names_or_codes: List[str], fname: str, linenum: int
) -> None:
    assert isinstance(names_or_codes, list)
    assert all(isinstance(x, str) for x in names_or_codes)
    assert isinstance(fname, str)
    assert isinstance(linenum, int)

    for name_or_code in names_or_codes:
        assert isinstance(name_or_code, str)
        if __can_disable_rule_name_or_code(name_or_code, f"at {fname}:{linenum}"):
            if fname not in _LINE_SUPPRESSIONS:
                _LINE_SUPPRESSIONS[fname] = {}
            if linenum + 1 not in _LINE_SUPPRESSIONS[fname]:
                _LINE_SUPPRESSIONS[fname][linenum + 1] = {}
            code = Rule.to_code(name_or_code)
            _LINE_SUPPRESSIONS[fname][linenum + 1][code] = None


# TODO this should be a line rule called before any other line rule, to avoid
# reading the files more than once
def __init_file_and_line_suppressions(args: Dict[str, Any]) -> None:
    comment_line_p = re.compile(r"^\s*($|#)")
    gaplint_p = re.compile(r"\s*#\s*gaplint:\s*disable\s*=\s*")
    rules_p = re.compile(r"[a-zA-Z0-9_\-]+")

    this_line_p = re.compile(r"#\s*gaplint:\s*disable\s*=\s*")
    next_line_p = re.compile(r"#\s* gaplint:\s*disable\(nextline\)=\s*")

    for fname in args["files"]:
        try:
            with open(fname, "r", encoding="utf-8", newline=None) as f:
                lines = f.readlines()
        except IOError:
            _info_action(f"IGNORING unreadable file {fname}!")
            continue
        linenum = 0
        # Find rules suppressed for the entire file at the start of the file
        while linenum < len(lines) and comment_line_p.search(lines[linenum]):
            match = gaplint_p.search(lines[linenum])
            if match:
                names_or_codes = rules_p.findall(lines[linenum], match.end())
                __add_file_suppressions(names_or_codes, fname, linenum)
            linenum += 1

        # Find rules suppressed for individual lines
        while linenum < len(lines):
            match = this_line_p.search(lines[linenum])
            if match:
                names_or_codes = rules_p.findall(lines[linenum], match.end())
                __add_line_suppressions(names_or_codes, fname, linenum)
            else:
                match = next_line_p.search(lines[linenum])
                if match:
                    names_or_codes = rules_p.findall(lines[linenum], match.end())
                    __add_line_suppressions(names_or_codes, fname, linenum)
            linenum += 1


def _is_rule_suppressed(fname: str, linenum: int, rule: Rule) -> bool:
    """
    Takes a filename, line number, and rule. Returns True if the rule is
    suppressed for that particular line, and False otherwise.
    """
    assert isinstance(fname, str)
    assert isinstance(linenum, int)
    assert isinstance(rule, Rule)

    if rule.code[0] == "M":
        return False
    if "all" in _GLOB_SUPPRESSIONS or rule.code in _GLOB_SUPPRESSIONS:
        return True
    if fname in _FILE_SUPPRESSIONS and (
        "all" in _FILE_SUPPRESSIONS[fname] or rule.code in _FILE_SUPPRESSIONS[fname]
    ):
        return True

    if (
        fname in _LINE_SUPPRESSIONS
        and linenum in _LINE_SUPPRESSIONS[fname]
        and (rule.code in _LINE_SUPPRESSIONS[fname][linenum])
    ):
        return True
    return False


###############################################################################
# The main event
###############################################################################


def __verbose_msg_per_file(args: Dict[str, Any], fname: str, i: int) -> None:
    num_files = len(args["files"])
    num_digits = len(str(num_files))
    prefix_len = max(len(x) for x in args["files"]) + 2
    index_str = str(i + 1).rjust(num_digits)

    _info_verbose(f"Linting {fname.ljust(prefix_len, '.')}.[{index_str}/{num_files}]")


def __at_exit(args: Dict[str, Any], total_num_warnings: int, start_time: float) -> None:
    if not _SILENT:
        t = time.process_time() - start_time
        _info_action(
            f'Analysed {len(args["files"])} files in {t:.2f}s, found {total_num_warnings} errors!'
        )
    sys.exit(total_num_warnings)


# TODO fix linting errors here
def main(  # pylint: disable=too-many-locals, too-many-statements, too-many-branches
    **kwargs,
) -> None:
    """
    This function applies all rules in this module to the files specified by
    the keywords argument files.

    Keyword Args:
        files (list):         a list of the filenames (str) of the files to
                              lint
        max_warnings (int):   the maximum number of warnings before giving up
                              (defaults to 1000)
        columns (int):        max characters per line (defaults to 80)
        indentation (int):    indentation of nested statements (defaults to 2)
        disable (list):       rules (names/codes) to disable (defaults to [])
        enable (list):        rules (names/codes) to enable (defaults to ["all"])
        column_range (bool):  whether to display column ranges on diagnostics
                              (defaults to False)
        silent (bool):        no output but all rules run
        verbose (bool):       so much output you will not know what to do
    """

    start_time = time.process_time()
    total_num_warnings = 0

    # Clear diagnostics to prevent accumulation
    _DIAGNOSTICS.clear()

    if __debug__:
        _info_verbose("Debug on . . .")
    else:
        _info_verbose("Debug off . . .")

    # gather args from different places
    cmd_line_args = _parse_cmd_line_args(kwargs)
    kwargs = _parse_kwargs(kwargs)
    config_yml_fname, yml_dic = _parse_yml_config()

    # check the arg types and values
    cmd_line_args = __normalize_args(cmd_line_args, "(command line argument)")
    kwargs = __normalize_args(kwargs, "(keyword argument)")
    yml_dic = __normalize_args(yml_dic, f"({config_yml_fname})")

    __init_rules()

    args = __merge_args(cmd_line_args, kwargs, config_yml_fname, yml_dic)
    __explain(args)
    # The next lines has to come after __init_rules because we need to know what
    # all of the rules are before we can check if we're given any bad ones.
    key = "disable"
    where = ""
    if args[key] == cmd_line_args[key]:
        where = "(command line arguments)"
    elif args[key] == kwargs[key]:
        where = "(keyword argument)"
    elif args[key] == yml_dic[key]:
        where = f"({config_yml_fname})"

    args = __normalize_disabled_rules(args, where)
    args = __normalize_files(args)
    __init_globals(args)

    if len(args["files"]) == 0:
        # Return 1 warning so that the exit code is correct
        __at_exit(args, 1, start_time)

    max_warnings = args["max-warnings"]

    def too_many_warnings(nr_warnings):
        if nr_warnings >= max_warnings:
            if not _SILENT:
                sys.stderr.write(f"Total errors found: {nr_warnings}\n")
                sys.stderr.write("Too many warnings, giving up!\n")
            __at_exit(args, nr_warnings, start_time)

    n = len(Rule.all_suppressible_codes())
    m = len(args["disable"])
    _info_action(f"Analysing {len(args['files'])} files with {n - m} / {n} rules!")

    for i, fname in enumerate(args["files"]):
        __verbose_msg_per_file(args, fname, i)
        try:
            with open(fname, "r", encoding="utf-8", newline=None) as ffile:
                lines = ffile.read()
        except IOError:
            _info_action(f"SKIPPING {fname}: cannot open for reading")
            continue

        nr_warnings = 0
        for rule in _FILE_RULES:
            # W000 is special and handles its own suppressions, since it is
            # really several rules in one.
            if rule.code == "W000" or not _is_rule_suppressed(fname, 0, rule):
                nr_warnings, lines = rule(fname, lines, nr_warnings)
                too_many_warnings(nr_warnings + total_num_warnings)
        lines = lines.split("\n")
        for linenum in range(len(lines)):
            for rule in _LINE_RULES:
                if rule.code == "W000" or not _is_rule_suppressed(
                    fname, linenum + 1, rule
                ):
                    nr_warnings, lines = rule(fname, lines, linenum, nr_warnings)
        too_many_warnings(nr_warnings + total_num_warnings)
        for rule in _LINE_RULES:
            rule.reset()
        for rule in _FILE_RULES:
            rule.reset()
        total_num_warnings += nr_warnings

    __at_exit(args, total_num_warnings, start_time)


if __name__ == "__main__":
    main()

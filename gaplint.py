#!/usr/bin/env python
"""
This module provides functions for automatically checking the format of a GAP
file according to some conventions.
"""
# pylint: disable=fixme, too-many-lines, invalid-name,
# pylint: disable=bad-option-value, consider-using-f-string

import argparse
import os
import re
import sys

import pkg_resources
import yaml

try:
    xrange  # Python 2
except NameError:
    xrange = range  # Python 3

###############################################################################
# Globals
###############################################################################

_VERBOSE = False
_SILENT = False
_VALID_EXTENSIONS = set(["g", "g.txt", "gi", "gd", "gap", "tst", "xml"])
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

_DEFAULT_CONFIG = {"max_warnings": 1000, "columns": 80, "indentation": 2}

_GLOB_CONFIG = {}
_GLOB_SUPPRESSIONS = {}
_FILE_SUPPRESSIONS = {}
_LINE_SUPPRESSIONS = {}

_CONFIGURED = False
_LINE_RULES = []
_FILE_RULES = []

_ESCAPE_PATTERN = re.compile(r"(^\\(\\\\)*[^\\]+.*$|^\\(\\\\)*$)")


###############################################################################
# Strings helpers
###############################################################################


def _is_tst_or_xml_file(fname):
    """Returns True if the extension of fname is '.xml' or '.tst'."""
    assert isinstance(fname, str)
    ext = fname.split(".")[-1]
    return ext in ("tst", "xml")


def _is_escaped(lines, pos):
    assert isinstance(lines, str)
    assert isinstance(pos, int)
    assert 0 <= pos < len(lines)
    if lines[pos - 1] != "\\":
        return False
    start = lines.rfind("\n", 0, pos)
    # Search for an odd number of backslashes immediately before line[pos]
    return _ESCAPE_PATTERN.search(lines[start + 1 : pos][::-1])


def _is_double_quote_in_char(line, pos):
    assert isinstance(line, str)
    assert isinstance(pos, int)
    assert 0 <= pos < len(line)
    return (
        pos > 0
        and pos + 1 < len(line)
        and line[pos - 1 : pos + 2] == "'\"'"
        and not _is_escaped(line, pos - 1)
    )


def _is_in_string(lines, pos):
    start = lines.rfind("\n", 0, pos)
    line = re.sub(r"\\.", "", lines[start:pos])
    return line.count('"') % 2 == 1 or line.count("'") % 2 == 1


###############################################################################
# Info messages
###############################################################################


def _warn_or_error(fname, linenum, msg, threshold):
    if not _SILENT:
        assert isinstance(fname, str)
        assert isinstance(linenum, int)
        assert isinstance(msg, str)
        assert isinstance(threshold, int)
        sys.stderr.write(
            "%s:%d: %s [%d]\n" % (fname, linenum + 1, msg, threshold)
        )


def _warn(fname, linenum, msg):
    _warn_or_error(fname, linenum, msg, 0)


def _error(fname, linenum, msg):
    _warn_or_error(fname, linenum, msg, 1)
    sys.exit("Aborting!")


def _info_statement(msg):
    if not _SILENT:
        assert isinstance(msg, str)
        sys.stdout.write("\033[40;38;5;82m%s\033[0m\n" % msg)


def _info_action(msg):
    if not _SILENT:
        assert isinstance(msg, str)
        sys.stdout.write("\033[33m%s\033[0m\n" % msg)


def _info_verbose(msg):
    if not _SILENT and _VERBOSE:
        assert isinstance(msg, str)
        sys.stdout.write("\033[40;38;5;208m%s\033[0m\n" % msg)


###############################################################################
# Rules: a rule is just a function or callable class.
###############################################################################


class Rule:  # pylint: disable=too-few-public-methods
    """
    Base class for rules.

    A rule is a subclass of this class which has a __call__ method that returns
    TODO
    """

    def __init__(self, name=None, code=None):
        assert isinstance(name, str) or (name is None and code is None)
        assert isinstance(code, str) or (name is None and code is None)
        self.name = name
        self.code = code

    def reset(self):
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

    def __init__(  # pylint: disable=too-many-arguments, dangerous-default-value
        self,
        name,
        code,
        pattern,
        warning_msg,
        exceptions=[],
        skip=lambda fname: False,
    ):
        Rule.__init__(self, name, code)
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

    def _match(self, line):
        exception_group = self._exception_group
        it = self._pattern.finditer(line)
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
                return x.start()
        return None

    def skip(self, fname):
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

    def __init__(self, name=None, code=None):
        Rule.__init__(self, name, code)
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
            "\xcc\xb1": "",
        }  # modifier - under line

    def __call__(self, fname, lines, nr_warnings=0):
        assert isinstance(fname, str)
        assert isinstance(lines, str)
        assert isinstance(nr_warnings, int)

        # Remove annoying characters
        def replace_chars(match):  # pylint: disable=missing-docstring
            char = match.group(0)
            return self._chars[char]

        return (
            nr_warnings,
            re.sub(
                "(" + "|".join(self._chars.keys()) + ")", replace_chars, lines
            ),
        )


class WarnRegexFile(WarnRegexBase):
    """
    A rule that issues a warning if everytime a regex is matched in a file.
    """

    def __call__(self, fname, lines, nr_warnings=0):
        assert isinstance(fname, str)
        assert isinstance(lines, str)
        assert isinstance(nr_warnings, int)
        if not _is_tst_or_xml_file(fname):
            match = self._match(lines)
            if match:
                _warn(fname, lines.count("\n", 0, match), self._warning_msg)
                return nr_warnings + 1, lines
        return nr_warnings, lines


class ReplaceComments(Rule):
    """
    Replace between '#+' and the end of a line by '#+' and as many '@' as there
    were other characters in the line, call before replacing strings, and
    chars, and so on.

    This rule does not return any warnings.
    """

    def __call__(self, fname, lines, nr_warnings=0):
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
            repl += re.sub(r"\S", "@", lines[octo:end])
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

    def __init__(self, name, code, delim1, delim2):
        Rule.__init__(self, name, code)
        assert isinstance(delim1, str)
        assert isinstance(delim2, str)
        self._delims = [re.compile(delim1), re.compile(delim2)]

    def __find_next(self, which, lines, start):
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

    def __call__(self, fname, lines, nr_warnings=0):
        assert isinstance(fname, str)
        assert isinstance(lines, str)
        assert isinstance(nr_warnings, int)

        start = self.__find_next(0, lines, 0)
        while start != -1:
            end = self.__find_next(1, lines, start + 1)
            if end == -1:
                _error(
                    fname,
                    lines.count("\n", 0, start),
                    "Unmatched %s" % self._delims[0].pattern,
                )
            end += len(self._delims[1].pattern)
            repl = re.sub("[^\n]", "@", lines[start:end])
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

    def __init__(self, name=None, code=None):
        Rule.__init__(self, name, code)
        self._consuming = False
        self._sol_p = re.compile(r"(^|\n)gap>\s*")
        self._eol_p = re.compile(r"($|\n)")
        self._rep_p = re.compile(r"[^\n]")

    def __call__(self, fname, lines, nr_warnings=0):
        assert isinstance(fname, str)
        assert isinstance(lines, str)
        assert isinstance(nr_warnings, int)
        if _is_tst_or_xml_file(fname):
            eol, out = 0, ""
            for sol in self._sol_p.finditer(lines):
                # Replace everything except '\n' with '@'
                out += re.sub(self._rep_p, "@", lines[eol : sol.start() + 1])
                eol = self._eol_p.search(lines, sol.end()).end()
                out += lines[sol.end() : eol]
                while eol + 1 < len(lines) and lines[eol] == ">":
                    start = eol + 2
                    eol = self._eol_p.search(lines, start).end()
                    out += lines[start:eol]
            return nr_warnings, out
        return nr_warnings, lines


class AnalyseLVars(Rule):  # pylint: disable=too-many-instance-attributes
    """
    This rule checks if there are unused local variables in a function.
    """

    def __init__(self, name=None, code=None):
        Rule.__init__(self, name, code)
        self.reset()

        self._function_p = re.compile(r"\bfunction\b")
        self._end_p = re.compile(r"\bend\b")
        self._local_p = re.compile(r"\blocal\b")
        self._var_p = re.compile(r"\w+")
        self._ass_var_p = re.compile(r"([a-zA-Z0-9_\.]+)\s*:=")
        self._use_var_p = re.compile(r"(\b\w+\b)(?!\s*:=)\W*")
        self._ws1_p = re.compile(r"[ \t\r\f\v]+")
        self._ws2_p = re.compile(r"\n[ \t\r\f\v]+")
        self._rec_p = re.compile(r"\brec\(")

    def reset(self):
        self._depth = -1
        self._func_args = []
        self._declared_lvars = []
        self._assigned_lvars = []
        self._used_lvars = []
        self._func_start_pos = []

    def _remove_recs_and_whitespace(self, lines):
        # Remove almost all whitespace
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

    def _start_function(self, fname, lines, pos, nr_warnings):
        self._depth += 1

        assert self._depth == len(self._func_args)
        assert self._depth == len(self._declared_lvars)
        assert self._depth == len(self._assigned_lvars)
        assert self._depth == len(self._used_lvars)
        assert self._depth == len(self._func_start_pos)

        self._func_args.append(set())
        self._declared_lvars.append(set())
        self._assigned_lvars.append(set())
        self._used_lvars.append(set())
        self._func_start_pos.append(pos)

        start = lines.find("(", pos) + 1
        end = lines.find(")", start)
        new_args = self._var_p.findall(lines, start, end)
        args = self._func_args[self._depth]

        for var in new_args:
            if var in args:
                _error(
                    fname,
                    lines.count("\n", 0, pos),
                    "Duplicate function argument: %s" % var,
                )
            elif var in _GAP_KEYWORDS:
                _error(
                    fname,
                    lines.count("\n", 0, pos),
                    "Function argument is keyword: %s" % var,
                )
            else:
                args.add(var)
        return end + 1, nr_warnings

    def _end_function(self, fname, lines, pos, nr_warnings):
        if len(self._declared_lvars) == 0:
            _error(fname, lines.count("\n", 0, pos), "'end' outside function")

        self._depth -= 1

        ass_lvars = self._assigned_lvars.pop()
        decl_lvars = self._declared_lvars.pop()
        use_lvars = self._used_lvars.pop()

        if len(self._used_lvars) > 0:
            self._used_lvars[-1] |= use_lvars  # union

        ass_lvars -= use_lvars  # difference
        ass_lvars &= decl_lvars  # intersection
        decl_lvars -= ass_lvars  # difference
        decl_lvars -= use_lvars  # difference

        if len(ass_lvars) != 0:
            ass_lvars = [key for key in ass_lvars if key.find(".") == -1]
            msg = "Variables assigned but never used: " + ass_lvars[0]
            for x in ass_lvars[1:]:
                msg += ", " + x
            linenum = lines.count("\n", 0, self._func_start_pos[-1])
            _warn(fname, linenum, msg)
            nr_warnings += 1

        if len(decl_lvars) != 0:
            decl_lvars = list(decl_lvars)
            msg = "Unused local variables: " + decl_lvars[0]
            for x in decl_lvars[1:]:
                msg += ", " + x
            linenum = lines.count("\n", 0, self._func_start_pos[-1])
            _warn(fname, linenum, msg)
            nr_warnings += 1

        self._func_args.pop()  # TODO do something with these
        self._func_start_pos.pop()
        return pos + len("end"), nr_warnings

    def _add_declared_lvars(self, fname, lines, pos, nr_warnings):
        end = lines.find(";", pos)
        lvars = self._declared_lvars[self._depth]
        args = self._func_args[self._depth]

        new_lvars = self._var_p.findall(lines, pos, end)
        for var in new_lvars:
            if var in lvars:
                _error(
                    fname,
                    lines.count("\n", 0, pos),
                    "Name used for two local variables: " + var,
                )
            elif var in args:
                _error(
                    fname,
                    lines.count("\n", 0, pos),
                    "Name used for function argument and local variable: %s"
                    % var,
                )
            elif var in _GAP_KEYWORDS:
                _error(
                    fname,
                    lines.count("\n", 0, pos),
                    "Local variable is keyword: " + var,
                )
            else:
                lvars.add(var)
        return end, nr_warnings

    def _find_lvars(self, fname, lines, pos, nr_warnings):
        end = self._end_p.search(lines, pos + 1)
        func = self._function_p.search(lines, pos + 1)
        if end is None and func is None:
            return len(lines), nr_warnings
        if end is None and func is not None:
            _error(fname, lines.count("\n", 0, pos), "'function' without 'end'")

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

    def __call__(self, fname, lines, nr_warnings=0):
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
                pos, nr_warnings = self._start_function(
                    fname, lines, pos, nr_warnings
                )
            elif self._local_p.search(lines, pos, pos + len("local") + 1):
                pos, nr_warnings = self._add_declared_lvars(
                    fname, lines, pos + len("local") + 1, nr_warnings
                )
            elif self._end_p.search(lines, pos, pos + len("end")):
                pos, nr_warnings = self._end_function(
                    fname, lines, pos, nr_warnings
                )
            else:
                pos, nr_warnings = self._find_lvars(
                    fname, lines, pos, nr_warnings
                )

        return nr_warnings, orig_lines


###############################################################################
# Line rules
###############################################################################


class LineTooLong(Rule):
    """
    Warn if the length of a line exceeds 80 characters.

    This rule does not modify the line.
    """

    def __init__(self, name=None, code=None):
        Rule.__init__(self, name, code)
        self._cols = _GLOB_CONFIG["columns"]

    def __call__(self, fname, lines, linenum, nr_warnings=0):
        if _is_tst_or_xml_file(fname):
            return nr_warnings, lines
        if len(lines[linenum]) - 1 > self._cols:
            _warn(
                fname,
                linenum,
                "Too long line (%d / %d)"
                % (len(lines[linenum]) - 1, self._cols),
            )
            nr_warnings += 1
        return nr_warnings, lines


class WarnRegexLine(WarnRegexBase):
    """
    Warn if regex matches.
    """

    def __call__(self, fname, lines, linenum, nr_warnings=0):
        assert isinstance(fname, str)
        assert isinstance(lines, list)
        assert isinstance(linenum, int)
        assert linenum < len(lines)
        assert isinstance(nr_warnings, int)
        if not self.skip(fname):
            if self._match(lines[linenum]) is not None:
                _warn(fname, linenum, self._warning_msg)
                return nr_warnings + 1, lines
        return nr_warnings, lines


class WhitespaceOperator(WarnRegexLine):
    """
    Instances of this class produce a warning whenever the whitespace around an
    operator is incorrect.
    """

    def __init__(self, name, code, op, exceptions=[]):  # pylint: disable=W0102
        WarnRegexLine.__init__(self, name, code, "", "")
        assert isinstance(op, str)
        assert op[0] != "(" and op[-1] != ")"
        assert exceptions is None or isinstance(exceptions, list)
        assert all(isinstance(e, str) for e in exceptions)
        gop = "(" + op + ")"
        pattern = (
            r"(\S"
            + gop
            + "|"
            + gop
            + r"\S|\s{2,}"
            + gop
            + "|"
            + gop
            + r"\s{2,})"
        )
        self._pattern = re.compile(pattern)
        self._warning_msg = "Wrong whitespace around operator " + op.replace(
            "\\", ""
        )
        exceptions = [e.replace(op, "(" + op + ")") for e in exceptions]
        self._exceptions = [re.compile(e) for e in exceptions]

        self._exception_group = op.replace("\\", "")


class UnalignedPatterns(Rule):
    """
    This rule checks if pattern occurs in consecutive lines and that they are
    aligned.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self, name, code, pattern, group, msg
    ):
        Rule.__init__(self, name, code)
        assert isinstance(pattern, str)
        assert isinstance(group, int)
        assert isinstance(msg, str)
        self._last_line_col = None
        self._pattern = re.compile(pattern)
        self._group = group
        self._msg = msg

    def __call__(self, fname, lines, linenum, nr_warnings=0):
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
                _warn(fname, linenum, self._msg)
                return nr_warnings + 1, lines
        self._last_line_col = col
        return nr_warnings, lines


class Indentation(Rule):
    """
    This class checks that the indentation level is correct in a given line.

    Certain keywords increase the indentation level, while others decrease it,
    this rule checks that a given line has the minimum indentation level
    required.
    """

    def __init__(self, name, code):
        Rule.__init__(self, name, code)
        ind = _GLOB_CONFIG["indentation"]
        self._expected = 0
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
            (re.compile(r"(\W|^)(if|for|while|elif|atomic)(\W|$)"), 2 * ind),
        ]
        self._indent = re.compile(r"^(\s*)\S")
        self._blank = re.compile(r"^\s*$")
        self._msg = "Bad indentation: found %d but expected at least %d"

    def __call__(self, fname, lines, linenum, nr_warnings=0):
        assert isinstance(fname, str)
        assert isinstance(lines, list)
        assert isinstance(linenum, int)
        assert isinstance(nr_warnings, int)
        assert self._expected >= 0

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
            _warn(fname, linenum, self._msg % (indent, self._expected))
            nr_warnings += 1

        for pair in self._after:
            if pair[0].search(lines[linenum]):
                self._expected += pair[1]
        return nr_warnings, lines

    def _get_indent_level(self, line):
        indent = self._indent.search(line)
        assert indent
        return len(indent.group(1))

    def reset(self):
        self._expected = 0


###############################################################################
# Functions for running this as a script instead of a module
###############################################################################


def _parse_args(kwargs):
    # pylint: disable=too-many-branches, too-many-statements, global-statement
    global _SILENT, _VERBOSE
    parser = argparse.ArgumentParser(prog="gaplint", usage="%(prog)s [options]")
    if "files" not in kwargs:
        parser.add_argument("files", nargs="+", help="the files to lint")

    parser.add_argument(
        "--max_warnings",
        nargs="?",
        type=int,
        help="max number of warnings reported (default: 1000)",
    )
    parser.set_defaults(max_warnings=None)

    parser.add_argument(
        "--columns",
        nargs="?",
        type=int,
        help="max number of characters per line (default: 80)",
    )
    parser.set_defaults(columns=None)

    parser.add_argument(
        "--disable",
        nargs="?",
        type=str,
        help="gaplint rules " + "(name or code) to disable (default: None)",
    )
    parser.set_defaults(disable="")
    # TODO an --enable option to enable only the specified rules

    parser.add_argument(
        "--indentation",
        nargs="?",
        type=int,
        help="indentation of nested statements (default: 2)",
    )
    parser.set_defaults(indentation=None)

    parser.add_argument(
        "--silent",
        dest="silent",
        action="store_true",
        help="silence all warnings (default: False)",
    )
    parser.set_defaults(silent=False)

    parser.add_argument(
        "--verbose",
        dest="verbose",
        action="store_true",
        help=" (default: False)",
    )
    parser.set_defaults(verbose=False)

    version = pkg_resources.require("gaplint")[0].version
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s version {0}".format(version),
    )

    parser.set_defaults(verbose=False)

    args = parser.parse_args()

    if "silent" in kwargs:
        _SILENT = kwargs["silent"]
    else:
        _SILENT = args.silent

    if "verbose" in kwargs:
        _VERBOSE = kwargs["verbose"]
    else:
        _VERBOSE = args.verbose

    # Reset the config and suppressions
    global _GLOB_CONFIG, _GLOB_SUPPRESSIONS, _FILE_SUPPRESSIONS
    global _LINE_SUPPRESSIONS
    _GLOB_CONFIG = _DEFAULT_CONFIG.copy()
    _GLOB_SUPPRESSIONS = {}
    _FILE_SUPPRESSIONS = {}
    _LINE_SUPPRESSIONS = {}

    # The following are only for when this is called as a function after
    # importing gaplint in python, rather than when running as a script
    args.config = {}
    for key in _GLOB_CONFIG:
        if key in args:
            args.config[key] = getattr(args, key)
        if key in kwargs:
            args.config[key] = kwargs[key]

    if "disable" in args:
        args.config["disable"] = args.disable
    if "disable" in kwargs:
        args.config["disable"] = kwargs["disable"]

    if "files" in kwargs:
        if not isinstance(kwargs["files"], list):
            sys.exit("Keyword arg 'files' must be a list")
        args.files = kwargs["files"]

    files = []
    for fname in args.files:
        if not (os.path.exists(fname) and os.path.isfile(fname)):
            _info_action("SKIPPING " + fname + ": cannot open for reading")
        elif (
            not fname.split(".")[-1] in _VALID_EXTENSIONS
            and not ".".join(fname.split(".")[-2:]) in _VALID_EXTENSIONS
        ):
            _info_action("IGNORING " + fname + ": not a valid file extension")
        else:
            files.append(fname)
    args.files = files

    return args


###############################################################################
# Global configuration and suppressions - run before defining RULES
###############################################################################


def __init_config_and_suppressions_command_line(args):
    assert isinstance(args, argparse.Namespace)
    assert hasattr(args, "files")
    assert hasattr(args, "config")
    assert "disable" in args.config

    for key in args.config:
        if key != "disable" and args.config[key] is not None:
            _GLOB_CONFIG[key] = args.config[key]

    names_or_codes = args.config["disable"].split(",")
    for name_or_code in names_or_codes:
        _GLOB_SUPPRESSIONS[name_or_code] = None


def __config_yml_path(dir_path):
    """
    Recursive function that takes the path of a directory to search and
    searches for the gaplint.yml config script. If the script is not found the
    function is then called on the parent directory - recursive case. This
    continues until we encounter a directory .git in our search (script not
    found, returns None), locate the script (returns script path), or until the
    root directory has been searched (script not found, returns None) - base
    cases A, B, C.
    """
    assert os.path.isdir(dir_path)
    entries = os.listdir(dir_path)  # initialise list of entries in the...
    # ...directory we are currently searching
    for entry in entries:
        # if entry a directory, True, else False
        entry_isdir = os.path.isdir(
            os.path.abspath(os.path.join(dir_path, entry))
        )
        if entry_isdir and entry == ".git":  # base case A
            return None
        if not entry_isdir and entry == ".gaplint.yml":  # base case B
            yml_path = os.path.abspath(os.path.join(dir_path, ".gaplint.yml"))
            return yml_path
    # if A and B not satisfied, recursive call made on parent directory
    pardir_path = os.path.abspath(os.path.join(dir_path, os.pardir))
    # when os.pardir is called on the root directory path, it just returns the
    # path to the root directory again, hence
    if pardir_path == dir_path:  # base case C
        return None
    return __config_yml_path(pardir_path)  # recursive call


def __init_config_and_suppressions_yml():

    config_yml_fname = __config_yml_path(os.getcwd())
    if config_yml_fname is None:
        return

    _info_action("Using configurations in %s" % config_yml_fname)
    try:
        with open(config_yml_fname, "r", encoding="utf8") as config_yml_file:
            ymldic = yaml.load(config_yml_file, Loader=yaml.FullLoader)
    except yaml.YAMLError:
        _info_action("IGNORING %s: error parsing YAML" % config_yml_fname)
        return

    if ymldic is None:
        return
    for key in ymldic:
        if key not in _GLOB_CONFIG and key != "disable":
            _info_action(
                "IGNORING unknown configuration value '%s' in %s"
                % (key, config_yml_fname)
            )
        elif key != "disable":
            _GLOB_CONFIG[key] = ymldic[key]
        else:
            if not isinstance(ymldic[key], list):
                _info_action(
                    "IGNORING %s: badly formed field 'disable'"
                    % config_yml_fname
                )
            else:
                for name_or_code in ymldic[key]:
                    if isinstance(name_or_code, str):
                        _GLOB_SUPPRESSIONS[name_or_code] = None
                    else:
                        _info_action(
                            "IGNORING bad value %s in field" % name_or_code
                            + " 'disable' in %s" % config_yml_fname
                        )


def __verify_glob_suppressions():
    global _GLOB_SUPPRESSIONS  # pylint: disable=global-variable-not-assigned, global-statement
    delete = []
    for name_or_code in _GLOB_SUPPRESSIONS:
        if name_or_code in ("all", ""):
            continue
        ok = False
        for rule in _LINE_RULES:
            if name_or_code in (rule.name, rule.code):
                if rule.code[0] == "M":
                    _info_action(
                        "IGNORING cannot disable rule: %s" % name_or_code
                    )
                else:
                    ok = True
                break
        if not ok:
            delete.append(name_or_code)

    for name_or_code in delete:
        del _GLOB_SUPPRESSIONS[name_or_code]
        config_yml_fname = __config_yml_path(os.getcwd())
        msg = "IGNORING in command line "
        if config_yml_fname is not None:
            msg += "or %s " % config_yml_fname
        msg += "invalid rule name or code: %s" % name_or_code
        _info_action(msg)


###############################################################################
# The list of rules (the order is important!)
###############################################################################


def __init_rules():
    global _FILE_RULES, _LINE_RULES  # pylint: disable=global-statement
    _FILE_RULES = [
        ReplaceAnnoyUTF8Chars("replace-weird-chars", "M000"),
        ReplaceOutputTstOrXMLFile("replace-output-tst-or-xml-file", "M001"),
        ReplaceComments("replace-comments", "M002"),
        ReplaceBetweenDelimiters(
            "replace-multiline-strings", "M003", r'"""', r'"""'
        ),
        ReplaceBetweenDelimiters("replace-strings", "M004", r'"', r'"'),
        ReplaceBetweenDelimiters("replace-chars", "M005", r"'", r"'"),
        AnalyseLVars("analyse-lvars", "W000"),
        WarnRegexFile(
            "consecutive-empty-lines",
            "W001",
            r"\n\s*\n\s*\n",
            "Consecutive empty lines",
        ),
    ]
    _LINE_RULES = [
        LineTooLong("line-too-long", "W002"),
        Indentation("indentation", "W003"),
        UnalignedPatterns(
            "align-assignments",
            "W004",
            r":=",
            0,
            "Unaligned assignments in " + "consecutive lines",
        ),
        UnalignedPatterns(
            "align-trailing-comments",
            "W005",
            r"\w.*(#+)",
            1,
            "Unaligned comments in " + "consecutive lines",
        ),
        UnalignedPatterns(
            "align-comments",
            "W006",
            r"^\s*(#+)",
            1,
            "Unaligned comments in " + "consecutive lines",
        ),
        WarnRegexLine(
            "trailing-whitespace",
            "W007",
            r"\s+$",
            "Trailing whitespace",
            [],
            _is_tst_or_xml_file,
        ),
        WarnRegexLine(
            "no-space-after-comment",
            "W008",
            r"#+[^ \t\n\r\f\v#]",
            "No space after comment",
        ),
        WarnRegexLine(
            "not-enough-space-before-comment",
            "W009",
            r"[^ \t\n\r\f\v#]\s?#",
            "At least 2 spaces before comment",
        ),
        WarnRegexLine(
            "space-after-comma",
            "W010",
            r",(([^,\s]+)|(\s{2,})\w)",
            "Exactly one space required after comma",
        ),
        WarnRegexLine(
            "space-before-comma", "W011", r"\s,", "No space before comma"
        ),
        WarnRegexLine(
            "space-after-bracket",
            "W012",
            r"(\(|\[|\{)[ \t\f\v]",
            "No space allowed after bracket",
        ),
        WarnRegexLine(
            "space-before-bracket",
            "W013",
            r"\s(\)|\]|\})",
            "No space allowed before bracket",
        ),
        WarnRegexLine(
            "multiple-semicolons",
            "W014",
            r";.*;",
            "More than one semicolon",
            [],
            _is_tst_or_xml_file,
        ),
        WarnRegexLine(
            "keyword-function",
            "W015",
            r"(\s|^)function[^\(]",
            "Keyword 'function' not followed by (",
        ),
        WarnRegexLine(
            "whitespace-op-assign",
            "W016",
            r"(\S:=|:=(\S|\s{2,}))",
            "Wrong whitespace around operator :=",
        ),
        WarnRegexLine(
            "tabs",
            "W017",
            r"\t",
            "There are tabs in this line, " + "replace with spaces",
        ),
        WarnRegexLine(
            "function-local-same-line",
            "W018",
            r"function\W.*\Wlocal\W",
            "Keywords 'function' and 'local' in the" + " same line",
        ),
        WarnRegexLine(
            "whitespace-op-minus",
            "W019",
            r"(return|\^|\*|,|=|\.|>) - \d",
            "Wrong whitespace around operator -",
        ),
        WhitespaceOperator("whitespace-op-plus", "W020", r"\+", [r"^\s*\+"]),
        WhitespaceOperator(
            "whitespace-op-multiply", "W021", r"\*", [r"^\s*\*", r"\\\*"]
        ),
        WhitespaceOperator(
            "whitespace-op-negative",
            "W022",
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
            r"\<",
            [r"^\s*\<", r"\<(\>|=)", r"\\\<"],
        ),
        WhitespaceOperator("whitespace-op-less-equal", "W024", r"\<="),
        WhitespaceOperator(
            "whitespace-op-more-than", "W025", r"\>", [r"(-|\<)\>", r"\>="]
        ),
        WhitespaceOperator("whitespace-op-more-equal", "W026", r"\>="),
        WhitespaceOperator(
            "whitespace-op-equals",
            "W027",
            r"=",
            [r"(:|>|<)=", r"^\s*=", r"\\="],
        ),
        WhitespaceOperator("whitespace-op-lambda", "W028", r"->"),
        WhitespaceOperator("whitespace-op-divide", "W029", r"\/", [r"\\\/"]),
        WhitespaceOperator(
            "whitespace-op-power", "W030", r"\^", [r"^\s*\^", r"\\\^"]
        ),
        WhitespaceOperator(
            "whitespace-op-not-equal", "W031", r"<>", [r"^\s*<>"]
        ),
        WhitespaceOperator(
            "whitespace-double-dot", "W032", r"\.\.", [r"\.\.(\.|\))"]
        ),
    ]


###############################################################################
# File and line suppressions - run after defining RULES
###############################################################################


def __is_valid_rule_name_or_code(name_or_code, fname, linenum):
    # TODO assertions
    if name_or_code == "all":
        return True
    for rule in _LINE_RULES:
        if name_or_code in (rule.name, rule.code):
            if rule.code[0] == "M":
                _info_action("IGNORING cannot disable rule: %s" % name_or_code)
                return False
            return True
    _info_action(
        "IGNORING in %s:%d invalid rule name or code: %s"
        % (fname, linenum + 1, name_or_code)
    )
    return False


def __add_file_suppressions(names_or_codes, fname, linenum):
    assert isinstance(names_or_codes, list)
    #  TODO add more assertions

    for name_or_code in names_or_codes:
        assert isinstance(name_or_code, str)
        if __is_valid_rule_name_or_code(name_or_code, fname, linenum):
            if fname not in _FILE_SUPPRESSIONS:
                _FILE_SUPPRESSIONS[fname] = {}
            _FILE_SUPPRESSIONS[fname][name_or_code] = None


def __add_line_suppressions(names_or_codes, fname, linenum):
    assert isinstance(names_or_codes, list)
    #  TODO add more assertions

    for name_or_code in names_or_codes:
        assert isinstance(name_or_code, str)
        if __is_valid_rule_name_or_code(name_or_code, fname, linenum):
            if fname not in _LINE_SUPPRESSIONS:
                _LINE_SUPPRESSIONS[fname] = {}
            if linenum + 1 not in _LINE_SUPPRESSIONS[fname]:
                _LINE_SUPPRESSIONS[fname][linenum + 1] = {}
            _LINE_SUPPRESSIONS[fname][linenum + 1][name_or_code] = None


# FIXME this should be a line rule called before any other line rule, to avoid
# reading the files more than once
def __init_file_and_line_suppressions(args):
    assert isinstance(args, argparse.Namespace)
    assert hasattr(args, "files")

    comment_line_p = re.compile(r"^\s*($|#)")
    gaplint_p = re.compile(r"\s*#\s*gaplint:\s*disable\s*=\s*")
    rules_p = re.compile(r"[a-zA-Z0-9_\-]+")

    this_line_p = re.compile(r"#\s*gaplint:\s*disable\s*=\s*")
    next_line_p = re.compile(r"#\s* gaplint:\s*disable\(nextline\)=\s*")

    for fname in args.files:
        try:
            with open(fname, "r", encoding="utf8") as f:
                lines = f.readlines()
        except IOError:
            _info_action("cannot read file %s, this shouldn't happen" % fname)
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
                    names_or_codes = rules_p.findall(
                        lines[linenum], match.end()
                    )
                    __add_line_suppressions(names_or_codes, fname, linenum)
            linenum += 1


def _is_rule_suppressed(fname, linenum, rule):
    """
    Takes a filename, line number and rule code. Returns True if the rule is
    suppressed for that particular line, and False otherwise.
    """
    assert isinstance(fname, str)
    assert isinstance(linenum, int)
    assert isinstance(rule, Rule)

    if rule.code[0] == "M":
        return False
    if (
        "all" in _GLOB_SUPPRESSIONS
        or rule.code in _GLOB_SUPPRESSIONS
        or rule.name in _GLOB_SUPPRESSIONS
    ):
        return True
    if fname in _FILE_SUPPRESSIONS and (
        "all" in _FILE_SUPPRESSIONS[fname]
        or rule.code in _FILE_SUPPRESSIONS[fname]
        or rule.name in _FILE_SUPPRESSIONS[fname]
    ):
        return True
    if (
        fname in _LINE_SUPPRESSIONS
        and linenum in _LINE_SUPPRESSIONS[fname]
        and (
            rule.code in _LINE_SUPPRESSIONS[fname][linenum]
            or rule.name in _LINE_SUPPRESSIONS[fname][linenum]
        )
    ):
        return True
    return False


###############################################################################
# The main event
###############################################################################


# pylint: disable=too-many-branches
def main(**kwargs):
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
        disable (list):       rules (names/codes) to suppress (defaults to [])
        silent (bool):        no output but all rules run
        verbose (bool):       so much output you will not know what to do
    """
    args = _parse_args(kwargs)

    if __debug__:
        _info_verbose("Debug on . . .")
    else:
        _info_verbose("Debug off . . .")

    if len(args.files) == 0:
        return

    __init_config_and_suppressions_yml()
    __init_config_and_suppressions_command_line(args)
    __init_rules()
    __verify_glob_suppressions()
    __init_file_and_line_suppressions(args)

    total_nr_warnings = 0
    max_warnings = _GLOB_CONFIG["max_warnings"]

    def too_many_warnings(nr_warnings):
        if nr_warnings >= max_warnings:
            if not _SILENT:
                sys.stderr.write("Total errors found: %d\n" % nr_warnings)
            sys.exit("Too many warnings, giving up!")

    for fname in args.files:
        _info_verbose("Linting %s . . ." % fname)
        try:
            with open(fname, "r", encoding="utf8") as ffile:
                lines = ffile.read()
        except IOError:
            _info_action("SKIPPING " + fname + ": cannot open for reading")

        nr_warnings = 0
        for rule in _FILE_RULES:
            # TODO can't suppress these so far
            nr_warnings, lines = rule(fname, lines, nr_warnings)
            too_many_warnings(nr_warnings + total_nr_warnings)
        lines = lines.split("\n")
        for linenum in xrange(len(lines)):
            for rule in _LINE_RULES:
                if not _is_rule_suppressed(fname, linenum, rule):
                    nr_warnings, lines = rule(
                        fname, lines, linenum, nr_warnings
                    )
                    too_many_warnings(nr_warnings + total_nr_warnings)
        for rule in _LINE_RULES:
            rule.reset()
        total_nr_warnings += nr_warnings
        if nr_warnings == 0:
            _info_statement("SUCCESS in " + fname)
    if total_nr_warnings != 0:
        if not _SILENT:
            sys.stderr.write("Total errors found: %d\n" % total_nr_warnings)
    sys.exit(total_nr_warnings > 0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python2
"""
This module provides functions for automatically checking the format of a GAP
file according to some conventions.
"""
#pylint: disable=invalid-name, dangerous-default-value, too-few-public-methods,
#pylint: disable=fixme

import re
import sys
import argparse
import os

################################################################################
# Globals
################################################################################

_VERBOSE = False
_SILENT = True
_VALID_EXTENSIONS = set(['g', 'g.txt', 'gi', 'gd', 'gap', 'tst', 'xml'])

################################################################################
# Colourize strings
################################################################################

def _red_string(string):
    assert isinstance(string, str)
    return '\033[31m' + string + '\033[0m'

def _yellow_string(string):
    assert isinstance(string, str)
    return '\033[33m' + string + '\033[0m'

def _neon_green_string(string):
    assert isinstance(string, str)
    return '\033[40;38;5;82m' + string + '\033[0m'

def _orange_string(string):
    assert isinstance(string, str)
    return '\033[40;38;5;208m' + string + '\033[0m'

def _pad(lines, linenum):
    return len(str(len(lines))) + 1 - len(str(linenum + 1))

def _eol(line):
    return (line[-1] == '\n') * '\n'

################################################################################
# Exit messages
################################################################################

def _exit_abort(message=None):
    if message:
        assert isinstance(message, str)
        sys.exit(_red_string('gaplint: ' + message + '! Aborting!'))
    else:
        sys.exit(_red_string('gaplint: Aborting!'))

################################################################################
# Info messages
################################################################################

def _info_statement(message):
    if not _SILENT:
        assert isinstance(message, str)
        sys.stdout.write(_neon_green_string(message) + '\n')

def _info_action(message):
    assert isinstance(message, str)
    sys.stdout.write(_yellow_string(message) + '\n')

def _info_verbose(fname, linenum, message, pad=1):
    if not _SILENT and _VERBOSE:
        assert isinstance(message, str)
        sys.stdout.write(_orange_string(fname + ':' + str(linenum + 1)
                                        + ' ' * pad + message))

def _info_warn(fname, linenum, message, pad=1):
    if not _SILENT:
        assert isinstance(fname, str) and isinstance(message, str)
        assert isinstance(linenum, int) and isinstance(pad, int)
        sys.stderr.write(_red_string('WARNING in ' + fname + ':'
                                     + str(linenum + 1) + ' ' * pad
                                     + message) + '\n')

################################################################################
# Rule output
################################################################################

class RuleOutput(object):
    '''
    The output of a rule.

    Attributes:
        line  (str) : possibly modified version of the argument line
        msg   (str) : a warning message (defaults to None)
        abort (bool): indicating if we should abort the script
                      (defaults to False)
    '''

    def __init__(self, line, msg=None, abort=False):
        '''
        This is used for the output of a rule as applied to line.

        Args:
            line  (str) : a line of GAP code
            msg   (str) : a warning message (defaults to None)
            abort (bool): indicating if we should abort the script
                          (defaults to False)
        '''
        self.line = line
        self.msg = msg
        self.abort = abort

################################################################################
# Rules: a rule is just a function or callable class returning a RuleOutput
################################################################################

def _skip_tst_or_xml_file(ext):
    return ext == 'tst' or ext == 'xml'

_ESCAPE_PATTERN = re.compile(r'(^\\(\\\\)*[^\\]+.*$|^\\(\\\\)*$)')

def _is_escaped(line, pos):
    assert isinstance(line, str) and isinstance(pos, int)
    assert (pos >= 0 and pos < len(line)) or (pos < 0 and len(line) + pos > 0)
    if pos < 0:
        pos = len(line) + pos
    if line[pos - 1] != '\\':
        return False
    # Search for an odd number of backslashes immediately before line[pos]
    return _ESCAPE_PATTERN.search(line[:pos][::-1])

class Rule(object):
    '''
    Base class for rules.

    A rule is a subclass of this class which has a __call__ method that returns
    a RuleOutput object.
    '''

    def reset(self):
        '''
        Reset the rule.

        This is only used by rules like those for checking the indentation of
        lines. This method is called once per file on which gaplint it run, so
        that issues with indentation, for example, in one file do not spill
        over into the next file.
        '''
        pass

    def skip(self, ext):
        '''
        Skip the rule.

        In some circumstances we might want to skip a rule, the rule is skipped
        if this method returns True. The default return value is falsy.
        '''
        pass

class RemoveComments(Rule):
    '''
    Remove the GAP comments in a line.

    When called this rule truncates the line given as a parameter to remove any
    comments. This is to avoid matching linting issues within comments, where
    the issues do not apply.

    This rule does not return any warnings.
    '''

    def _is_in_string(self, line, pos):
        line = re.sub(r'\\.', '', line[:pos])
        return line.count('"') % 2 == 1 or line.count("'") % 2 == 1

    def __call__(self, line):
        assert isinstance(line, str)
        try:
            i = next(i for i in xrange(len(line)) if line[i] == '#' and not
                     self._is_in_string(line, i))
        except StopIteration:
            return RuleOutput(line)
        return RuleOutput(line[:i] + _eol(line))

class ReplaceMultilineStrings(Rule):
    '''
    Replace multiline strings.

    When called this rule modifies the line given as a parameter to remove any
    multiline strings, and replace them with __REMOVED_MULTILINE_STRING__. This
    is to avoid matching linting issues within strings, where the issues do not
    apply.

    This rule does not return any warnings.
    '''
    def __init__(self):
        self._consuming = False

    def __call__(self, line):
        ro = RuleOutput(line)
        if self._consuming:
            end = line.find('"""')
            ro.line = '__REMOVED_MULTILINE_STRING__'
            if end != -1:
                ro.line += line[end + 3:]
                self._consuming = False
            else:
                ro.line += _eol(line)
        else:
            start = line.find('"""')
            if start != -1:
                self._consuming = True
                end = line.find('"""', start + 3)
                ro.line = line[:start] + '__REMOVED_MULTILINE_STRING__'
                if end != -1:
                    self._consuming = False
                    ro.line += line[end + 3:]
                else:
                    ro.line += _eol(line)
        return ro

    def reset(self):
        self._consuming = False

def _is_double_quote_in_char(line, pos):
    assert isinstance(line, str) and isinstance(pos, int)
    return (pos > 0 and pos + 1 < len(line)
            and line[pos - 1:pos + 2] == '\'"\''
            and not _is_escaped(line, pos - 1))

class ReplaceQuotes(Rule):
    '''
    Remove everything between non-escaped <quote>s in a line.

    Strings and chars are replaced with <replacement>, and hence alter the
    length of the line, and its contents. If either of these is important for
    another rule, then that rule should be run before this one.

    This rule returns warnings if a line has an escaped quote outside a string
    or character, or if a line contains an unmatched unescaped quote.
    '''
    def __init__(self, quote, replacement):
        self._quote = quote
        self._replacement = replacement
        self._cont_replacement = replacement[:-1] + 'CONTINUATION__'
        self._consuming = False

    def _next_valid_quote(self, line, pos):
        assert isinstance(line, str) and isinstance(pos, int)
        assert pos >= 0
        pos = line.find(self._quote, pos)
        while (pos >= 0
               and (_is_escaped(line, pos)
                    or _is_double_quote_in_char(line, pos))):
            pos = line.find(self._quote, pos + 1)
        return pos

    def __call__(self, line):
        # TODO if we want to allow the script to modify the input, then we
        # better keep the removed strings/chars, and index the replacements so
        # that we can put them back at some point later on.
        assert isinstance(line, str)
        cont_replacement = self._cont_replacement
        ro = RuleOutput(line)
        beg = 0

        if self._consuming:
            end = self._next_valid_quote(line, 0)
            if end != -1:
                self._consuming = False
                ro.line = cont_replacement + ro.line[end + 1:]
                beg = end + 1
            else:
                if _is_escaped(line, -1):
                    ro.line = cont_replacement + _eol(line)
                else:
                    ro.msg = 'invalid continuation of string'
                    ro.abort = True
                return ro

        replacement = self._replacement
        beg = self._next_valid_quote(ro.line, beg)

        while beg != -1:
            end = self._next_valid_quote(ro.line, beg + 1)
            if end == -1:
                if _is_escaped(ro.line, -1):
                    self._consuming = True
                    ro.line = ro.line[:beg] + cont_replacement + _eol(line)
                else:
                    ro.msg = 'unmatched quote ' + self._quote
                    ro.msg += ' in column ' + str(beg + 1)
                    ro.abort = True
                break
            ro.line = ro.line[:beg] + replacement + ro.line[end + 1:]
            beg = self._next_valid_quote(ro.line, beg + len(replacement) + 1)
        return ro

class RemovePrefix(object):
    '''
    This is not a rule. This is just a callable class to remove the prefix
    'gap>' or '>' if called with a line from a file with extension 'tst' or
    'xml', if the line does not start with a 'gap>' or '>', then the entire
    line is replaced with __REMOVED_LINE_FROM_TST_OR_XML_FILE__.
    '''
    def __init__(self):
        self._consuming = False
        self._gap_gt_prefix = re.compile(r'^gap>\s*')
        self._gt_prefix = re.compile(r'^>\s*')
        # TODO if linting an xml file warn about whitespace before gap> or >

    def __call__(self, line, ext):
        if ext == 'tst' or ext == 'xml':
            m = self._gap_gt_prefix.search(line)
            if m:
                line = line[m.end():]
                self._consuming = True
            elif self._consuming:
                m = self._gt_prefix.search(line)
                if m:
                    line = line[m.end():]
                else:
                    line = '__REMOVED_LINE_FROM_TST_OR_XML_FILE__' + _eol(line)
                    self._consuming = False
            else:
                line = '__REMOVED_LINE_FROM_TST_OR_XML_FILE__' + _eol(line)
        return line

class LineTooLong(Rule):
    '''
    Warn if the length of a line exceeds 80 characters.

    This rule does not modify the line.
    '''
    def __call__(self, line):
        assert isinstance(line, str)
        ro = RuleOutput(line)
        if len(line) > 81:
            ro.msg = 'too long line (' + str(len(line) - 1) + ' / 80)'
        return ro

class WarnRegex(Rule):
    '''
    Instances of this class produce a warning whenever a line matches the
    pattern used to construct the instance except if one of a list of
    exceptions is also matched.
    '''

    def __init__(self,
                 pattern,
                 warning_msg,
                 exceptions=[],
                 skip=lambda ext: None):
        #pylint: disable=bad-builtin, unnecessary-lambda, deprecated-lambda
        assert isinstance(pattern, str)
        assert isinstance(warning_msg, str)
        assert isinstance(exceptions, list)
        assert reduce(lambda x, y: x and isinstance(y, str), exceptions, True)

        self._pattern = re.compile(pattern)
        self._warning_msg = warning_msg
        self._exception_patterns = exceptions
        self._exception_group = None
        self._exceptions = map(lambda e: re.compile(e), exceptions)
        self._skip = skip

    def __call__(self, line):
        nr_matches = 0
        msg = None
        exception_group = self._exception_group
        it = self._pattern.finditer(line)
        for x in it:
            if len(self._exceptions) > 0:
                exception = False
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
                else:
                    nr_matches += 1
            else:
                nr_matches += 1
        if nr_matches > 0:
            msg = self._warning_msg
        return RuleOutput(line, msg, False)

    def skip(self, ext):
        return self._skip(ext)

class WhitespaceOperator(WarnRegex):
    '''
    Instances of this class produce a warning whenever the whitespace around an
    operator is incorrect.
    '''
    def __init__(self, op, exceptions=[]):
        #pylint: disable=bad-builtin, deprecated-lambda, unnecessary-lambda
        WarnRegex.__init__(self, '', '')
        assert isinstance(op, str)
        assert op[0] != '(' and op[-1] != ')'
        assert exceptions is None or isinstance(exceptions, list)
        assert reduce(lambda x, y: x and isinstance(y, str), exceptions, True)
        gop = '(' + op + ')'
        pattern = (r'(\S' + gop + '|' + gop + r'\S|\s{2,}' + gop +
                   '|' + gop + r'\s{2,})')
        self._pattern = re.compile(pattern)
        self._warning_msg = ('wrong whitespace around operator '
                             + op.replace('\\', ''))
        exceptions = map(lambda e: e.replace(op, '(' + op + ')'), exceptions)
        self._exceptions = map(lambda e: re.compile(e), exceptions)

        self._exception_group = op.replace('\\', '')

class Indentation(Rule):
    '''
    This class checks that the indentation level is correct in a given line.

    Certain keywords increase the indentation level, while others decrease it,
    this rule checks that a given line has the minimum indentation level
    required.
    '''
    def __init__(self):
        self._expected = 0
        self._before = [(re.compile(r'(\W|^)(elif|else)(\W|$)'), -2),
                        (re.compile(r'(\W|^)end(\W|$)'), -2),
                        (re.compile(r'(\W|^)(od|fi)(\W|$)'), -2),
                        (re.compile(r'(\W|^)until(\W|$)'), -2)]
        self._after = [(re.compile(r'(\W|^)(then|do)(\W|$)'), -2),
                       (re.compile(r'(\W|^)(repeat|else)(\W|$)'), 2),
                       (re.compile(r'(\W|^)function(\W|$)'), 2),
                       (re.compile(r'(\W|^)(if|for|while|elif)(\W|$)'), 4)]
        self._indent = re.compile(r'^(\s*)\S')
        self._blank = re.compile(r'^\s*$')

    def __call__(self, line):
        assert self._expected >= 0
        ro = RuleOutput(line)
        if self._blank.search(line):
            return ro
        for pair in self._before:
            if pair[0].search(line):
                self._expected += pair[1]

        if self._get_indent_level(line) < self._expected:
            ro.msg = ('bad indentation: found ' +
                      str(self._get_indent_level(line)) +
                      ' expected at least ' + str(self._expected))
        for pair in self._after:
            if pair[0].search(line):
                self._expected += pair[1]
        return ro

    def _get_indent_level(self, line):
        indent = self._indent.search(line)
        assert indent
        return len(indent.group(1))

    def reset(self):
        self._expected = 0

    def skip(self, ext):
        return _skip_tst_or_xml_file(ext)

class ConsecutiveEmptyLines(WarnRegex):
    '''
    This rule checks if there are consecutive empty lines in a file.
    '''
    def __init__(self):
        WarnRegex.__init__(self, r'^\s*$', 'consecutive empty lines!')
        self._prev_line_empty = False

    def __call__(self, line):
        ro = WarnRegex.__call__(self, line)
        if ro.msg:
            if not self._prev_line_empty:
                self._prev_line_empty = True
                ro.msg = None
        else:
            self._prev_line_empty = False
        return ro

    def reset(self):
        self._prev_line_empty = False

################################################################################
# Functions for running this as a script instead of a module
################################################################################

def _parse_args(kwargs):
    global _SILENT, _VERBOSE #pylint: disable=global-statement
    parser = argparse.ArgumentParser(prog='gaplint',
                                     usage='%(prog)s [options]')
    if __name__ == '__main__':
        parser.add_argument('files', nargs='+', help='the files to lint')

    parser.add_argument('--max-warnings', nargs='?', type=int,
                        help='max number of warnings reported (default: 1000)')
    parser.set_defaults(max_warnings=1000)

    parser.add_argument('--silent', dest='silent', action='store_true',
                        help='silence all warnings (default: False)')
    parser.set_defaults(silent=False)

    parser.add_argument('--verbose', dest='verbose', action='store_true',
                        help=' (default: False)')
    parser.set_defaults(verbose=False)

    args = parser.parse_args()

    if 'silent' in kwargs:
        _SILENT = kwargs['silent']
    else:
        _SILENT = args.silent

    if 'verbose' in kwargs:
        _VERBOSE = kwargs['verbose']
    else:
        _VERBOSE = args.verbose

    if 'max-warnings' in kwargs:
        args.max_warnings = kwargs['max-warnings']

    if __name__ != '__main__':
        if not ('files' in kwargs and isinstance(kwargs['files'], list)):
            _exit_abort('no files specified or not specified in a list')
        args.files = kwargs['files']

    files = []
    for fname in args.files:
        if not (os.path.exists(fname) and os.path.isfile(fname)):
            _info_action('SKIPPING ' + fname + ': cannot open for reading')
        elif (not fname.split('.')[-1] in _VALID_EXTENSIONS
              and not '.'.join(fname.split('.')[-2:]) in _VALID_EXTENSIONS):
            _info_action('IGNORING ' + fname + ': not a valid file extension')
        else:
            files.append(fname)
    args.files = files

    return args

################################################################################
# The list of rules (the order is important!)
################################################################################

# TODO process rules according to the content of a configuration file, i.e.
# include some rules and not others, allows options line the indentation level,
# the length of a line, etc...

# TODO allow skipping a file in that file
# gaplint: skip-file

_remove_prefix = RemovePrefix()
RULES = [LineTooLong(),
         ConsecutiveEmptyLines(),
         WarnRegex(r'^.*\s+\n$',
                   'trailing whitespace!',
                   [],
                   _skip_tst_or_xml_file),
         RemoveComments(),
         ReplaceMultilineStrings(),
         ReplaceQuotes('"', '__REMOVED_STRING__'),
         ReplaceQuotes('\'', '__REMOVED_CHAR__'),
         Indentation(),
         WarnRegex(r',(([^,\s]+)|(\s{2,})\w)',
                   'exactly one space required after comma'),
         WarnRegex(r'\s,', 'no space before comma'),
         WarnRegex(r'(\(|\[|\{)[ \t\f\v]',
                   'no space allowed after bracket'),
         WarnRegex(r'\s(\)|\]|\})',
                   'no space allowed before bracket'),
         WarnRegex(r';.*;',
                   'more than one semicolon!',
                   [],
                   _skip_tst_or_xml_file),
         WarnRegex(r'(\s|^)function[^\(]',
                   'keyword function not followed by ('),
         WarnRegex(r'(\S:=|:=(\S|\s{2,}))',
                   'wrong whitespace around operator :='),
         WarnRegex(r'\t',
                   'there are tabs in this line, replace with spaces!'),
         WhitespaceOperator(r'\+', [r'^\s*\+']),
         WhitespaceOperator(r'\*', [r'^\s*\*', r'\\\*']),
         WhitespaceOperator(r'-',
                            [r'-(>|\[)', r'(\^|\*|,|=|\.|>) -',
                             r'(\(|\[)-', r'return -infinity',
                             r'return -\d']),
         WarnRegex(r'(return|\^|\*|,|=|\.|>) - \d',
                   'wrong whitespace around operator -'),
         WhitespaceOperator(r'\<', [r'^\s*\<', r'\<(\>|=)',
                                    r'\\\<']),
         WhitespaceOperator(r'\<='),
         WhitespaceOperator(r'\>', [r'(-|\<)\>', r'\>=']),
         WhitespaceOperator(r'\>='),
         WhitespaceOperator(r'=', [r'(:|>|<)=', r'^\s*=', r'\\=']),
         WhitespaceOperator(r'->'),
         WhitespaceOperator(r'\/', [r'\\\/']),
         WhitespaceOperator(r'\^', [r'^\s*\^', r'\\\^']),
         WhitespaceOperator(r'<>', [r'^\s*<>']),
         WhitespaceOperator(r'\.\.', [r'\.\.(\.|\))'])]

################################################################################
# The main event
################################################################################

def run_gaplint(**kwargs): #pylint: disable=too-many-branches
    '''
    This function applies all rules in this module to the files specified by
    the keywords argument files.

    Keyword Args:
        files (list):      a list of the filenames (str) of the files to lint
        maxwarnings (int): the maximum number of warnings before giving up
                           (defaults to 1000)
        silent (bool):     no output
        verbose (bool):    so much output you will not know what to do
    '''
    args = _parse_args(kwargs)

    total_nr_warnings = 0

    for fname in args.files:
        try:
            ffile = open(fname, 'r')
            lines = ffile.readlines()
            ffile.close()
        except IOError:
            _info_action('SKIPPING ' + fname + ': cannot open for reading')

        ext = fname.split('.')[-1]
        nr_warnings = 0
        for i in xrange(len(lines)):
            lines[i] = _remove_prefix(lines[i], ext)
            for rule in RULES:
                if not rule.skip(ext):
                    ro = rule(lines[i])
                    assert isinstance(ro, RuleOutput)
                    if ro.msg:
                        nr_warnings += 1
                        _info_warn(fname, i, ro.msg, _pad(lines, i))
                    if ro.abort:
                        _exit_abort(str(total_nr_warnings + nr_warnings)
                                    + ' warnings')
                    lines[i] = ro.line
                    if total_nr_warnings + nr_warnings >= args.max_warnings:
                        _exit_abort('too many warnings')
            _info_verbose(fname, i, lines[i], _pad(lines, i))
        for rule in RULES:
            rule.reset()
        total_nr_warnings += nr_warnings
        if nr_warnings == 0:
            _info_statement('SUCCESS in ' + fname)
    if total_nr_warnings != 0:
        if not _SILENT:
            sys.stderr.write(_red_string('FAILED with '
                                         + str(total_nr_warnings)
                                         + ' warnings!\n'))
            if __name__ == '__main__':
                sys.exit(1)
    if __name__ == '__main__':
        sys.exit(0)

if __name__ == '__main__':
    run_gaplint()

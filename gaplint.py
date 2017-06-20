#!/usr/bin/env python2
'''
This module provides functions for automatically checking the format of a GAP
file according to some conventions.
'''
#pylint: disable=invalid-name, dangerous-default-value, too-few-public-methods,
#pylint: disable=fixme

import re
import sys
import argparse
import os
import yaml
import copy

################################################################################
# Globals
################################################################################

_VERBOSE = False
_SILENT = True
_VALID_EXTENSIONS = set(['g', 'g.txt', 'gi', 'gd', 'gap', 'tst', 'xml'])

__DEFAULT_CONFIG = {'columns': 80, 'max_warnings': 1000, 'indentation': 2,
                    'disable': []}
__CONFIG = {}
__SUPPRESSIONS = {}
__GLOBAL_SUPPRESSIONS = {}

################################################################################
# Configuration
################################################################################

def __get_config_yml_path(dir_path, checked_dirs=[]): 
    '''
    Takes the path of a directory to search and a list of those already
    searched. The function recursively searches for the gaplint.yml config
    script. It begins the search at dir_path. If the .yml is not found, the
    funtion is called recursively on any child directories, and if it is still
    not found, the parent directory. The recursive calls are repeated until
    either the .yml script is found or a .git directory is reached. If no
    configuration script is found None is returned. Otherwise the path to the
    .yml is returned.
    '''
    assert os.path.isdir(dir_path)
    # We keep track of directories we have already searched with the list,
    # checked_dirs. This way we do not search directories a second time as we 
    # backtrack.
    checked_dirs.append(dir_path)
    # initialise list of entries in the directory we are currently searching
    entries = os.listdir(dir_path)

    # Base case A: if the config script is found in entries, we return the path.
    if '.gaplint.yml' in entries: 
        return dir_path + '/.gaplint.yml'

    # Base case B: if a directory .git is found in entries or if the directory 
    # we are currently searching is called .git, we return None.
    if '.git' in entries or dir_path == '.git':
        return None

    # Recursive case A: if there are directories in entries that have not  been 
    # searched, we make the recursive call on each.
    for e in entries:
        e_path = dir_path + '/' + e
        if os.path.isdir(e_path) and e_path not in checked_dirs:
            return __get_config_yml_path(e_path, checked_dirs)

    # Recursive case B: if no child-directories contain the config script, we 
    # make the recursive call on the nearest unsearched parent directory.
    pardir_path = os.path.abspath(os.path.join(dir_path, os.pardir))
    while pardir_path in checked_dirs:
        pardir_path = os.path.abspath(os.path.join(pardir_path, os.pardir))
    return __get_config_yml_path(pardir_path, checked_dirs)

def __get_config_yml_dic():
    '''
    Takes no argument. Attempts to open the config file at the path returned by
    __get_yml_config_path. If the attempt is successful the yaml config file is
    read yielding a dictionary which is returned. If the file cannot be opened,
    an empty dictionary is returned.
    '''
    ymlpath = __get_config_yml_path(os.getcwd()) 
    ymldic = {}    
    if ymlpath != None:        
        try:
            config_file = open(ymlpath, 'r')
            ymldic = yaml.load(config_file)        
        except yaml.scanner.ScannerError as e:
            _info_action('gaplint: error processing .gaplint.yml, '
                         + 'using default configuration values')        
        except IOError:
            _info_action('gaplint: cannot open file .gaplint.yml, '
                         + 'using default configuration values')
        except Exception:
            _info_action('gaplint: there is a problem with .gaplint.yml, '
                         + 'using default configuration values')
        return ymldic
    else:
        _info_action('gaplint: config file .gaplint.yml not found, '
                     + 'using default configuration values')
    return {}

def __get_code_list(rule_list):
    '''
    Takes a list of rule names and codes and returns a list of codes of the 
    rules listed
    '''
    assert isinstance(rule, list)
    codes = []
    for rule in rule_list:
        code = __rule_code(rule)
        if code not in codes:
            codes.append(code)
    return codes

def __set_config_dic(args):
    '''
    Takes a parser object as an argument. Consolidates user preferences given in
    .gaplint.yml, the command line, and hardcoded in the gaplint.py global 
    variable __CONFIG. Where different values are given for the same config 
    option in any two or more of these ways, preference is given based on a 
    configuration hierarchy. From top to bottom: __CONFIG, command line args,
    .gaplint.ylml.
    '''
    assert isinstance(args, object)
    global __CONFIG, __DEFAULT_CONFIG

    # yml config 3rd in hierarchy
    temp_config = __get_config_yml_dic() # our working config dictionary
    temp_config['disable'] = __get_code_list(temp_config['disable'])   
    
    # superceded by command line options, 2nd in hierarchy
    if not args.max_warnings == __DEFAULT_CONFIG['max_warnings']:
        temp_config['max_warnings'] = args.max_warnings    
    if not args.columns ==  __DEFAULT_CONFIG['columns']:
        temp_config['columns'] = args.columns    
    if not args.disable ==  __DEFAULT_CONFIG['disable']:
        temp_config['disable'] = __get_code_list(args.disable)
    if not args.indentation ==  __DEFAULT_CONFIG['indentation']:
        temp_config['indentation'] = args.indentation
    
    # superceded by contents of global variable __CONFIG, top of hierarchy
    for option in temp_config.keys():
        if not option in __CONFIG.keys():
            __CONFIG[option] = temp_config[option]

def _get_config_val(key):
    '''

    '''
    global __CONFIG, __DEFAULT_CONFIG
    config_keys = __CONFIG.keys()
    default_keys = __DEFAULT_CONFIG.keys()    
    if key in config_keys:
        return __CONFIG[key]
    elif key in default_keys:
        return __DEFAULT_CONFIG[key]
    else:
        raise Exception('key does not exist, i.e. not a valid configuration '
                        + 'option.')

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
    def __init__(self, name, code):
        self.name = name
        self.code = code

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
    def __init__(self, name, code):
        self._consuming = False
        Rule.__init__(self, name, code)
        
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
    def __init__(self, name, code, quote, replacement):
        Rule.__init__(self, name, code)
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
        cols = _get_config_val('columns')
        if len(line) > cols:
            ro.msg = 'too long line (%d / %d)' % (len(line) - 1, cols)
        return ro

class WarnRegex(Rule):
    '''
    Instances of this class produce a warning whenever a line matches the
    pattern used to construct the instance except if one of a list of
    exceptions is also matched.
    '''

    def __init__(self,
                 name, 
                 code,
                 pattern,
                 warning_msg,
                 exceptions=[],
                 skip=lambda ext: None):
        #pylint: disable=bad-builtin, unnecessary-lambda, deprecated-lambda
        Rule.__init__(self, name, code)
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
    def __init__(self, name, code, op, exceptions=[]):
        #pylint: disable=bad-builtin, deprecated-lambda, unnecessary-lambda
        WarnRegex.__init__(self, name, code, '', '')
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
    def __init__(self, name, code):
        Rule.__init__(self, name, code)
        ind = _get_config_val('indentation')
        self._expected = 0
        self._before = [(re.compile(r'(\W|^)(elif|else)(\W|$)'), -ind),
                        (re.compile(r'(\W|^)end(\W|$)'), -ind),
                        (re.compile(r'(\W|^)(od|fi)(\W|$)'), -ind),
                        (re.compile(r'(\W|^)until(\W|$)'), -ind)]
        self._after = [(re.compile(r'(\W|^)(then|do)(\W|$)'), -ind),
                       (re.compile(r'(\W|^)(repeat|else)(\W|$)'), ind),
                       (re.compile(r'(\W|^)function(\W|$)'), ind),
                       (re.compile(r'(\W|^)(if|for|while|elif)(\W|$)'), 2*ind)]
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
    def __init__(self, name, code):
        WarnRegex.__init__(self, name, code, r'^\s*$', 'consecutive empty lines!')
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

class UnusedLVarsFunc(Rule):
    '''
    This rule checks if there are unused local variables in a function.
    '''
    def __init__(self, name, code):
        Rule.__init__(self, name, code)
        self._consuming_args = False
        self._consuming_lvars = False
        self._depth = -1
        self._args = []
        self._lvars = []
        self._function_p = re.compile(r'(^|\W)(function)(\W)')
        self._end_p = re.compile(r'(^|\W)end\W')
        self._local_p = re.compile(r'(^|\W)(local)(\W)')
        self._var_p = re.compile(r'\w+')
        self._keywords = {'true', 'false', 'continue', 'break', 'if', 'fi',
                          'else', 'for', 'od', 'while', 'repeat', 'until',
                          'return', '__REMOVED_STRING__', '__REMOVED_CHAR__'}

    def reset(self):
        self._consuming_args = False
        self._consuming_lvars = False
        self._depth = -1
        self._args = []
        self._lvars = []


    def _is_function_declared(self, line):
        return self._function_p.search(line)

    def _is_end_declared(self, line):
        return self._end_p.search(line)

    def _is_local_declared(self, line):
        return self._local_p.search(line)

    def _add_function_args(self, line, start=0, end=-1):
        ro = RuleOutput(line)
        new_args = self._var_p.findall(line, start, end)
        args = self._args[self._depth]
        for var in new_args:
            if var in args:
                ro.msg = 'duplicate function argument: ' + var
                ro.abort = True
            elif var in self._keywords:
                ro.msg = 'function argument is keyword: ' + var
                ro.abort = True
            else:
                args.add(var)
        self._consuming_args = (line.find(')', start) == -1)
        return ro

    def _new_function(self, line):
        m = self._function_p.search(line)
        assert m
        assert not self._consuming_args and not self._consuming_lvars
        self._depth += 1
        assert self._depth == len(self._args)
        assert self._depth == len(self._lvars)
        self._lvars.append(set())
        self._args.append(set())
        start = line.find('(', m.start(3)) + 1
        end = line.find(')', start)
        if end == -1:
            self._consuming_args = True
        return self._add_function_args(line, start, end)

    def _end_function(self, line):
        assert self._end_p.search(line)
        assert not self._consuming_args and not self._consuming_lvars

        ro = RuleOutput(line)
        self._depth -= 1
        lvars = [key for key in self._lvars.pop()]
        args = [key for key in self._args.pop()]
        # TODO should use the number of the line where function declared
        if len(lvars) != 0:
            ro.msg = 'unused local variables: '
            ro.msg += reduce(lambda x, y: x + ', ' + y, lvars[1:], lvars[0])
        # TODO the following produces too many warnings, there are plenty of
        # places where there are legitimately unused function arguments
        #if len(args) != 0:
        #    ro.msg = 'unused function arguments: '
        #    ro.msg += reduce(lambda x, y: x + ', ' + y, args[1:], args[0])
        return ro

    def _add_lvars(self, line):
        ro = RuleOutput(line)
        end = line.find(';')
        self._consuming_lvars = (end == -1)
        lvars = self._lvars[self._depth]
        args = self._args[self._depth]
        new_lvars = self._var_p.findall(line, 0, end)
        for var in new_lvars:
            if var in lvars:
                ro.msg = 'name used for two locals: ' + var
                ro.abort = True
            elif var in args:
                ro.msg = 'name used for argument and local: ' + var
                ro.abort = True
            elif var in self._keywords:
                ro.msg = 'local is keyword: ' + var
                ro.abort = True
            elif var != 'local':
                lvars.add(var)
        return ro

    def _remove_lvars(self, line):
        ro = RuleOutput(line)
        lvars = self._var_p.findall(line)
        for var in lvars:
            for depth in xrange(0, self._depth + 1):
                self._lvars[depth].discard(var)
                self._args[depth].discard(var)
            # could detect unbound globals here (maybe)
        return ro

    def __call__(self, line):
        ro = RuleOutput(line)
        if self._is_function_declared(line):
            ro = self._new_function(line)
            if not ro.msg and self._is_end_declared(line):
                ro = self._remove_lvars(line)
                ro = self._end_function(line)
        elif self._is_local_declared(line) or self._consuming_lvars:
            ro = self._add_lvars(line)
            if not ro.msg and self._is_end_declared(line):
                ro = self._remove_lvars(line)
                ro = self._end_function(line)
        elif self._is_end_declared(line):
            ro = self._end_function(line)
        elif self._consuming_args:
            ro = self._add_function_args(line, 0, line.find(')'))
        elif self._depth >= 0:
            ro = self._remove_lvars(line)
        return ro

    def skip(self, ext):
        return _skip_tst_or_xml_file(ext)

################################################################################
# Functions for running this as a script instead of a module
################################################################################

def _parse_args(kwargs):
    global _SILENT, _VERBOSE #pylint: disable=global-statement
    parser = argparse.ArgumentParser(prog='gaplint',
                                     usage='%(prog)s [options]')
    if __name__ == '__main__':
        parser.add_argument('files', nargs='+', help='the files to lint')

    parser.add_argument('--max_warnings', nargs='?', type=int,
                        help='max number of warnings reported (default: 1000)')    
    parser.set_defaults(max_warnings=_get_config_val('max_warnings'))

    parser.add_argument('--columns', nargs='?', type=int, 
                        help='max number of characters per line (default: 80)')
    parser.set_defaults(columns=_get_config_val('columns'))

    parser.add_argument('--disable', nargs='?', type=list, help='gaplint rules '
                        + '(name or code) to disable (default: [])')
    parser.set_defaults(disable=_get_config_val('disable'))

    parser.add_argument('--indentation', nargs='?', type=int,
                        help='indentation of nested statements (default: 2)')
    parser.set_defaults(indentation=_get_config_val('indentation'))

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

    if 'max_warnings' in kwargs:
        args.max_warnings = kwargs['max_warnings']
    if 'columns' in kwargs:
        args.columns = kwargs['columns']
    if 'disable' in kwargs:
        args.disable = kwargs['disable']
    if 'indentation' in kwargs:
        args.indentation = kwargs['indentation'] 

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
RULES = [LineTooLong('line-too-long', 'W001'),
         ConsecutiveEmptyLines('empty-lines', 'W002'),
         WarnRegex('trailing-whitespace', 'W003', r'^.*\s+\n$',
                   'trailing whitespace!', [], _skip_tst_or_xml_file),
         RemoveComments('remove-comments', 'M001'),
         ReplaceMultilineStrings('replace-multiline-strings', 'M002'),
         ReplaceQuotes('replace-double-quotes', 'M003', '"', 
                       '__REMOVED_STRING__'),
         ReplaceQuotes('replace-escaped-quotes', 'M004', r'\'', 
                       '__REMOVED_CHAR__'),
         Indentation('indentation', 'W004'),
         WarnRegex('space-after-comma', 'W005',
                    r',(([^,\s]+)|(\s{2,})\w)', 
                    'exactly one space required after comma'),
         WarnRegex('space-before-comma', 'W006', r'\s,', 
                   'no space before comma'),
         WarnRegex('space-after-bracket', 'W007', 
                    r'(\(|\[|\{)[ \t\f\v]', 'no space allowed after bracket'),
         WarnRegex('space-before-bracket', 'W008', r'\s(\)|\]|\})',
                   'no space allowed before bracket'),
         WarnRegex('multiple-semicolons', 'W009', r';.*;',
                   'more than one semicolon!', [], _skip_tst_or_xml_file),
         WarnRegex('keyword-function', 'W010', 
                    r'(\s|^)function[^\(]', 
                    'keyword function not followed by ('),
         WarnRegex('whitespace-op-colon-equals', 'W011', 
                   r'(\S:=|:=(\S|\s{2,}))', 
                   'wrong whitespace around operator :='),
         WarnRegex('tabs', 'W012', r'\t',
                   'there are tabs in this line, replace with spaces!'),
         WarnRegex('function-local-same-line', 'W013', 
                   r'function\W.*\Wlocal\W', 
                   'keywords function and local in the same line'),
         WhitespaceOperator('whitespace-op-plus', 'W014',
                            r'\+', [r'^\s*\+']),
         WhitespaceOperator('whitespace-op-multiply', 'W015', 
                            r'\*', [r'^\s*\*', r'\\\*']),
         WhitespaceOperator('whitespace-op-negative', 'W016', 
                            r'-', [r'-(>|\[)', r'(\^|\*|,|=|\.|>) -',
                            r'(\(|\[)-', r'return -infinity', r'return -\d']),
         WarnRegex('whitespace-op-minus', 'W017', 
                   r'(return|\^|\*|,|=|\.|>) - \d',
                   'wrong whitespace around operator -'),
         WhitespaceOperator('whitespace-op-less-than', 'W018', 
                            r'\<', [r'^\s*\<', r'\<(\>|=)', r'\\\<']),
         WhitespaceOperator('whitespace-op-less-equal', 'W019', 
                            r'\<='),
         WhitespaceOperator('whitespace-op-more-than', 'W020', r'\>', 
                            [r'(-|\<)\>', r'\>=']),
         WhitespaceOperator('whitespace-op-more-equal', 'W021', 
                            r'\>='),
         WhitespaceOperator('whitespace-op-equals', 'W022', r'=', 
                            [r'(:|>|<)=', r'^\s*=', r'\\=']),
         WhitespaceOperator('whitespace-op-mapping', 'W023', r'->'),
         WhitespaceOperator('whitespace-op-divide', 'W024', r'\/', 
                            [r'\\\/']),
         WhitespaceOperator('whitespace-op-power', 'W025', r'\^', 
                            [r'^\s*\^', r'\\\^']),
         WhitespaceOperator('whitespace-op-not-equal', 'W026', 
                            r'<>', [r'^\s*<>']),
         WhitespaceOperator('whitespace-double-dot', 'W027', r'\.\.', 
                            [r'\.\.(\.|\))']),
         UnusedLVarsFunc('unused-local-variables', 'W028')]

_RULE_NAMES_AND_CODES = []
for rule in RULES:
    _RULE_NAMES_AND_CODES.append([rule.name, rule.code])
_RULE_NAMES = [x[0] for x in _RULE_NAMES_AND_CODES]
_RULE_CODES = [x[1] for x in _RULE_NAMES_AND_CODES]

################################################################################
# suppressions
################################################################################

def __rule_code(rule): 
    '''
    Takes a rule name or code and returns the rule code.
    '''
    assert isinstance(rule, str)
    global _RULE_NAMES, _RULE_CODES
    if rule in _RULE_NAMES:
        return _RULE_CODES[_RULE_NAMES.index(rule)]
    elif rule in _RULE_CODES:
        return rule
    return False

def __make_dic(keys, vals): 
    '''
    Takes a list of keys and values and returns a dictionary.
    '''
    assert (isinstance(keys, list) and isinstance(vals, list)
            and len(keys) == len(vals))
    dic = {}
    for i in xrange(len(keys)):
        dic[keys[i]] = vals[i]
    return dic

def __is_valid_rule(rule):
    '''
    Takes a rule and confirms its validity, returning a bool.
    '''
    global _RULE_NAMES, _CODE_NAMES
    if rule in _RULE_NAMES + _RULE_CODES:
        return True
    return False

def __unpack_tuple_list(tuplist):
    '''
    Takes a list of tuples and searches their contents for rules. Returns a 
    list of rules found.
    '''
    assert (isinstance(tuplist, list)
            and all(isinstance(tup, tuple) for tup in tuplist))    
    global _RULE_NAMES, _RULE_CODES
    supp_codes = []

    for tup in tuplist:
        for rule in tup:
            if rule == 'all':
                return _RULE_CODES
            if __is_valid_rule(rule):
                code = rule_code(rule)
                if not code in supp_codes:
                    supp_codes.append(code)

    return supp_codes

def __get_global_suppdic(fname, lines):
    '''
    Takes a list of lines and returns a dictionary with globally suppressed 
    rules as entries, all assigned the value True.
    '''
    assert (isinstance(fname, str) and isinstance(lines, list)
            and all(isinstance(x, str) for x in lines))
    
    global _RULE_CODES
    pattern1 = re.compile('^\s*($|#)')
    pattern2 = re.compile('\s*#\s*gaplint:\s*disable\s*=\s*')
    pattern3 = re.compile('((\w+(-\w+)*)+(-\S+){0,1})')
    n = len(lines)    
    i = 0
    line = lines[0]
    G_suppdic = {}

    while re.search(pattern1, line) and i < n:
        match = re.search(pattern2, line)
        if match:
            match = pattern3.findall(line[match.end():])
            supp_codes = __unpack_tuple_list(match)
            if not len(supp_codes):
                _info_warn(fname, i, 'global suppressions: invalid/no rule '
                           + 'code(s) or name(s) given')
            if supp_codes == _RULE_CODES: # i.e. rule = 'all'
                return make_dic(_RULE_CODES, [True for x in _RULE_CODES])
            for code in supp_codes:
                if not code in G_suppdic.keys():
                    G_suppdic[code] = True
        i += 1
        line = lines[i]
    return G_suppdic

def __get_line_suppressions(fname, line, linenum):
    '''
    Takes a filename, string and line number. Returns a dictionary whose keys
    are the suppressed rules for the line, all assigned value True, and a 
    boolean value True if the rules are to be applied to the next line and
    False if not. If the suppression keywords are present, but no/invalid rules 
    follow, a warning is thrown. A list is returned. The first element of which 
    is the bool, the second the dictionary.
    '''
    assert (all(isinstance(x, str) for x in [fname, line])
            and isinstance(linenum, int))

    global _RULE_NAMES, _RULE_CODES
    n = len(line)
    pattern1 = re.compile('#\s*gaplint:\s*disable\s*=\s*')
    pattern2 = re.compile('#\s* gaplint:\s*disable\(nextline\)=\s*')
    match1 = pattern1.search(line)
    match2 = pattern2.search(line)
    is_nextline = False
    if match1 or match2:
        pattern = re.compile('((\w+(-\w+)*)+(-\S+){0,1})') 
        if match2:
            is_nextline = True        
            match = pattern.findall(line[match2.end():])
        else:
            match = pattern.findall(line[match1.end():])
        valid = __unpack_tuple_list(match)
        if not len(valid):
            _info_warn(fname, linenum, 
                       'suppressions: invalid/no rule code(s) or name(s) given')
            return [is_nextline, {}]
        else:
            return [is_nextline, make_dic(valid, [True for x in valid])]
    return [is_nextline, {}]

def __get_lines_suppdic(fname, lines):
    '''
    Takes a filename and a list the lines of the file as strings. Returns a
    2D dictionary whose keys are the indices of lines with rule suppressions.
    Their values are dictionaries whose keys are the rules suppressed in the
    lines, all assigned value True. This includes global suppressions.
    '''
    assert (isinstance(fname, str) and isinstance(lines, list)
            and all(isinstance(x, str) for x in lines))

    dic = {}
    n = len(lines)
    for i in range(n):
        line_supp_dic = __get_line_suppressions(fname, lines[i], i)
        if len(line_supp_dic[1].keys()) > 0:
            if line_supp_dic[0]: 
                i += 1 # if nextline increment line index by 1
            if not i in dic.keys():
                dic[i] = line_supp_dic[1] 
            else:
                 for rule in line_supp_dic[1].keys():
                    if not rule in dic[i].keys():
                        dic[i][rule] = True
    return dic

def __set_suppression_dics(file_list):
    '''
    Takes a list of files to be linted. Assigns a 3D dictionary to the global 
    variable __SUPPRESSIONS. It's keys are the files to be linted. Each
    corresponding value is a 2D dictionary containing the suppressions for each
    line (that returned by suppressions_all_lines above)
    '''
    assert (isinstance(file_list, list)
            and all(isinstance(x, str) for x in file_list))
    
    global __SUPPRESSIONS, __GLOBAL_SUPPRESSIONS
    dic = {}
    G_dic = {}
    for fname in file_list: 
        lines = []
        try:
            ffile = open(fname, 'r')
            lines = ffile.readlines()
            ffile.close()
        except IOError: ### not sure how exceptions should be handled here
            pass
        
        lines_suppdic = __get_lines_suppdic(fname, lines)
        global_suppdic = __get_global_suppdic(fname, lines)        
        if len(lines_suppdic.keys()) > 0:
            dic[fname] = __get_lines_suppdic(fname, lines)
        if len(global_suppdic.keys()) > 0:
            G_dic[fname] = __get_global_suppdic(fname, lines)

    __SUPPRESSIONS = dic
    __GLOBAL_SUPPRESSIONS = G_dic

def __is_rule_suppressed(fname, linenum, code):
    '''
    '''
    assert (all(isinstance(x, str) for x in [fname, code]) 
            and isinstance(linenum, int))

    global __SUPPRESSIONS, __GLOBAL_SUPPRESSIONS
    if fname in __GLOBAL_SUPPRESSIONS.keys():
        return code in __GLOBAL_SUPPRESSIONS[fname].keys()
    if fname in __SUPPRESSIONS.keys():
        if linenum in __SUPPRESSIONS[fname].keys():
            return code in __SUPPRESSIONS[fname][linenum].keys()
    return False


################################################################################
# user preferences
################################################################################

def __is_rule_disabled_suppressed(fname, linenum, code):
    '''
    Takes a filename, line number and rule code. Returns True if the rule is
    suppressed for that particular line, and False otherwise.
    '''
    assert (all(isinstance(x, str) for x in [fname, code]) 
            and isinstance(linenum, int))

    if code in _get_config_val('disable'):
        return True       
    if __is_rule_suppressed(fname, linenum, code):
        return True
    return False

def __load_user_preferences(args):
    assert isinstance(args, object)
    __set_config_dic(args)
    __set_suppression_dics(args.files)
    return

################################################################################
# The main event
################################################################################

def run_gaplint(**kwargs): #pylint: disable=too-many-branches
    '''
    This function applies all rules in this module to the files specified by
    the keywords argument files.

    Keyword Args:
        files (list):         a list of the filenames (str) of the files to lint
        max_warnings (int):   the maximum number of warnings before giving up
                              (defaults to 1000)
        columns (int):        max characters per line (defaults to 80)
        indentation (int):    indentation of nested statements (defaults to 2)
        disable (list):       rules (names/codes) to suppress (defaults to [])
        silent (bool):        no output
        verbose (bool):       so much output you will not know what to do
    '''    
    args = _parse_args(kwargs)

    __load_user_preferences(args)

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
                is_rule_dis = __is_rule_disabled_suppressed(fname, i, rule.code)
                if (not rule.skip(ext)) and (not is_rule_dis):
                    try:
                        ro = rule(lines[i])
                    except AssertionError:
                        sys.stdout.write(
                            _red_string('Assertion in ' + fname +
                                        ':' + str(i + 1)) + '\n')
                        raise

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

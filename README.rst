.. image:: logo/logo.png
  :width: 256
  :alt: The gaplint logo, an image of a piece of lint with the word "GAP"
   written above it and "lint" within it.

*********************************************************
README - gaplint - by James D. Mitchell and Simon Tollman
*********************************************************

``gaplint`` automatically checks the format of a GAP file according to
some conventions, which are somewhat configurable. It prints the nature
and location of instances of any instances of violations of these
conventions (see below for more details).

Installation
============

Simply run::

    $ pip install gaplint

Usage
=====

To use it::

    $ gaplint --help

List of all rules
=================

To disable all rules for a particular file you can add the line::

    # gaplint: disable = all

to the start of the file before any lines that contain any code. All
rules are enabled by default.

A table of all currently implemented rules is given below:

.. list-table:: gaplint rules
   :widths: 6 40 40
   :header-rows: 1

   * - Code
     - Name
     - Description
   * - W000
     - analyse-lvars
     - Warns if there are declared local variables that are not used or
       assigned but not used.
   * - W001
     - consecutive-empty-lines
     - Warns if there are consecutive empty lines.
   * - W002
     - line-too-long
     - Warns if there is a line which is longer than the configured maximum
       (defaults to ``80``).
   * - W003
     - indentation
     - Warns if a line is under indented.
   * - W004
     - align-assignments
     - Warns if there are assignments in consecutive lines that are not
       aligned.
   * - W005
     - align-trailing-comments
     - Warns if there are trailing comments in consecutive lines that are not
       aligned.
   * - W006
     - align-comments
     - Warns if there are non-trailing comments in consecutive lines that are
       not aligned.
   * - W007
     - trailing-whitespace
     - Warns if there is trailing whitespace at the end of a line.
   * - W008
     - no-space-after-comment
     - Warns if there is no space after any number of # is a line.
   * - W009
     - not-enough-space-before-comment
     - Warns if there is not enough space before the first # in any line
       (defaults to ``2``).
   * - W010
     - space-after-comma
     - Warns if a comma is followed by more than ``1`` space.
   * - W011
     - space-before-comma
     - Warns if a comma is preceded by a space.
   * - W012
     - space-after-bracket
     - Warns if there is a space after an opening bracket.
   * - W013
     - space-before-bracket
     - Warns if there is a space before a closing bracket.
   * - W014
     - multiple-semicolons
     - Warns if there is more than one semicolon in a line.
   * - W015
     - keyword-function
     - Warns if the keyword ``function`` is not followed by an open bracket.
   * - W016
     - whitespace-op-assign
     - Warns if there is not exactly 1 space after an assignment  (``:=``).
   * - W017
     - tabs
     - Warns if there are tabs.
   * - W018
     - function-local-same-line
     - Warns if the keywords ``function`` and ``local`` appear in the same
       line.
   * - W019
     - whitespace-op-minus
     - Warns if there is not exactly 1 space either side of a minus (``-``)
       operator
   * - W020
     - whitespace-op-plus
     - Warns if there is not exactly 1 space either side of a plus (``+``)
       operator.
   * - W021
     - whitespace-op-multiply
     - Warns if there is not exactly 1 space either side of a multiply (``*``)
       operator.
   * - W022
     - whitespace-op-negative
     - Warns if there is not exactly 1 space preceding a negative (``-``)
       operator.
   * - W023
     - whitespace-op-less-than
     - Warns if there is not exactly 1 space either side of a less-than (``<``)
       operator.
   * - W024
     - whitespace-op-less-equal
     - Warns if there is not exactly 1 space either side of a less-than or
       equal-to (``<=``) operator.
   * - W025
     - whitespace-op-more-than
     - Warns if there is not exactly 1 space either side of a greater-than
       (``>``) operator.
   * - W026
     - whitespace-op-more-equal
     - Warns if there is not exactly 1 space either side of a greater than or
       equal to (``>=``) operator.
   * - W027
     - whitespace-op-equals
     - Warns if there is not exactly 1 space either side of an equals (``=``)
       operator.
   * - W028
     - whitespace-op-lambda
     - Warns if there is not exactly 1 space either side of the mapping
       (``->``) operator in a lambda function.
   * - W029
     - whitespace-op-divide
     - Warns if there is not exactly 1 space either side of a division (``/``)
       operator.
   * - W030
     - whitespace-op-power
     - Warns if there is not exactly 1 space either side of a power (``^``)
       operator.
   * - W031
     - whitespace-op-not-equal
     - Warns if there is not exactly 1 space either side of a not-equal
       (``<>``) operator.
   * - W032
     - whitespace-double-dot
     - Warns if there is not exactly 1 space either side of an arithmetic
       progression (``..``) operator.
   * - W033
     - assign-then-return
     - Warns if a variable is pointlessly assigned and then immediately
       returned.
   * - W034
     - 1-line-function
     - Warns that a one line function could be a lambda.
   * - W035
     - pointless-lambda
     - Warns when there are lambda functions of the form ``x -> f(x)`` which
       can be replaced by ``f``.
   * - W036
     - use-return-true
     - Warns that ``x -> true`` can be replaced by ``ReturnTrue``.
   * - W037
     - use-return-false
     - Warns that ``x -> false`` can be replaced by ``ReturnFalse``.
   * - W038
     - use-return-fail
     - Warns that ``x -> fail`` can be replaced by ``ReturnFail``.
   * - W039
     - use-return-first
     - Warns to replace lambdas of the form ``{x, y, z, ...} -> x`` by
       ``ReturnFirst``.
   * - W040
     - use-id-func
     - Warns that ``function(x) return x; end;`` can be replaced by ``IdFunc``.
   * - W041
     - no-semicolon-after-function
     - Warns if there's an unnecessary semicolon in ``function(.*);``.
   * - W042
     - use-not-eq
     - Warns to use ``x <> y`` instead of ``not x = y``.
   * - W043
     - dont-use-arg
     - Warns to use ``function(arg...)`` instead of ``function(arg)``.
   * - W044
     - if-then-return-true-else-return-false
     - Warns that ``if XYZ then return true; else return false; fi;`` by
       ``return XYZ;``
   * - W045
     - if-then-return-false-else-return-true
     - Warns that ``if XYZ then return false; else return true; fi;`` by
       ``return not XYZ;``
   * - W046
     - unused-func-args
     - Warns if there are unused function parameters (use ``_`` to suppress).
   * - W047
     - duplicate-function
     - Warns if there is a duplicate function.
   * - W048
     - use-remove-not-unbind
     - Warns that ``Unbind(x[Length])`` can be replaced by ``Remove(x)``.

You can obtain an explanation of a rule at the command line using the
``--explain`` flag, i.e. ``--explain W000,W001``.  Passing in ``--explain all``
will produce a table of all rules.

Configuration
=============

Certain parameters can be configured, for example, the maximum number of
characters permitted per line. All rules are enabled by default but can
be disable at the command line, by comments in the file itself, or in a
configuration file ``.gaplint.yml``.

**Configuration keywords:**

- ``columns``: maximum number of characters per line. *Defaults to 80*.
- ``disable``: rules can be disabled using their name or code.
  *Defaults to no rules disabled*.
- ``dupl-func-min-len``: only warn about duplicate functions with at least
  this many lines. *Defaults to 4*.
- ``enable``: rules can be enabled using their name or code. *Defaults to all rules enabled*.
- ``indentation``: minimum indentation of nested statements. *Defaults
  to 2*.
- ``max-warnings``: maximum number of warnings before ``gaplint``
  aborts. *Defaults to 1000*.

A list of all of the rules that ``gaplint`` can apply is given below.

You can alter the configuration in various places, the order of
precedence of these is governed by the hierarchy described below. A
preference given somewhere higher in the hierarchy will be
given precedence. 

Configuration
=============

Via the command line
^^^^^^^^^^^^^^^^^^^^

These preferences will be applied for a single run of ``gaplint`` only (though
multiple files may be linted in this run). To configure ``gaplint`` to be run
on ``file1``, ``file2``, ..., with preferences as in the example above, we
enter the following into the command line::

       gaplint --columns=100 --indentation=4 --disable=W002,W028 file1 file2 ...

Via comments in source files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Any rule, including ``all``, can be suppressed for a specific line or for a
whole file:

* To supress a rule(s) for a given line, include the following after the line
  of code for which the rule is to be suppressed::

   # gaplint: disable=<name_or_code>, <name_or_code> ...

*  If the above is too long to fit after the relevant line of code,
   suppressions can be declared in the line above for the line below
   by including ``(nextline)``::

   # gaplint: disable(nextline)=<name_or_code>, <name_or_code>, ...

*  If rules have been suppressed for a given line using both the
   in-line and *nextline* options, the union of the two rule sets
   given for suppression will be disabled for the line.

*  To suppress rules for a whole file the following must be included
   before any code is written (i.e. either as the first line of a GAP
   file, or preceded by any combination of only whitespace, empty
   lines and comments)::

   # gaplint: disable=<name_or_code>, <name_or_code>, ...

Via a configuration file
^^^^^^^^^^^^^^^^^^^^^^^^

   To configure ``gaplint`` as in the above examples, create a
   ``.gaplint.yml`` file containing the following lines:

   .. code:: yaml

       columns: 100
       indentation: 4
       disable:
       - W002
       - W028

``gaplint`` looks for the ``.gaplint.yml`` file in the current
directory, and its ancestors, until it reaches a directory containing
a ``git`` repository or the ``.gaplint.yml`` file is located. If
there is no ``.gaplint.yml`` file, then the default configuration
options are used. The options configured in ``.gaplint.yml`` are
applied to every file on which ``gaplint`` is run from the current
directory unless overruled higher in the hierarchy.


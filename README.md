
### README - gaplint
---
Gaplint automatically checks the format of a GAP file according to some conventions, *rules*. It prints the nature and location of instances of incorrect formatting as well as correcting others.

### Rules
---
*Rules that report formatting errors (codes begin with 'W' for 'warning'):*

| Code | Name | Description |
| --- | --- | --- |
| W001 | line-too-long | Max 80 characters per line |
| W002 | empty-lines | No consecutive empty lines |
| W003 | trailing-whitespace | No whitespace at the end of a line |
| W004 | indentation | Minimum indentation level required |
| W005 | space-after-comma | Exactly one space after a comma |
| W006 | space-before-comma | No spaces before a comma |
| W007 | space-after-bracket | No spaces after a bracket |
| W008 | space-before-bracket | No spaces before a bracket |
| W009 | multiple-semicolons | Not more than one semicolon per line |
| W010 | keyword-function | Keyword *function* must be followed by an open bracket |
| W011 | whitespace-op-colon-equals | Exactly one space either side of a colon-equals (:=) operator |
| W012 | tabs | Replace inline tabs with spaces |
| W013 | function-local-same-line | Keywords *function* and *local* cannot appear in the same line |
| W014 | whitespace-op-plus | Exactly one space either side of a plus (+) operator  |
| W015 | whitespace-op-multiply | Exactly one space either side of a multiply (\*) operator |
| W016 | whitespace-op-negative | Exactly one space preceding a negative (-) operator |
| W017 | whitespace-op-minus | Exactly one space either side of a minus (-) operator |
| W018 | whitespace-op-less-than | Exactly one space either side of a less than (<) operator |
| W019 | whitespace-op-less-equal | Exactly one space either side of a less than / equal to (<=) operator |
| W020 | whitespace-op-more-than | Exactly one space either side of a greater than(>) operator |
| W021 | whitespace-op-more-equal | Exactly one space either side of greater-than / equal-to (>=) operator |
| W022 | whitespace-op-equals | Exactly one space either side of equals (=) operator |
| W023 | whitespace-op-mapping | Exactly one space either side of mapping (->) operator |
| W024 | whitespace-op-divide | Exactly one space either side of divide (/) operator | 
| W025 | whitespace-op-power | No spaces either side of power (^) operator |
| W026 | whitespace-op-not-equal | Exactly one space either side of not-equal (<>) operator |
| W027 | whitespace-op-double-dot | Exactly one space either side of arithmetic progression (\.\.) operator |
| W028 | unused-local-variables | All declared local variables must be used |

*Rules that correct formatting errors (codes begin with 'M' for 'modify'):*

| Code | Name | Description |
| --- | --- | --- |
| M001 | remove-comments | Truncates a line to remove comments, to avoid matching linting issues within comments where the issues do not apply |
| M002 | replace-multiline-strings | Modifies a line to remove multiline strings, to avoid matching linting issues within comments where the issues do not apply multiline strings |
| M003 | replace-double-quotes | Removes everything between non-escaped <double-quote>s in a line to avoid matching linting issues where they do not apply. A line's length and content is altered so if either of these is important for another rule, that rule should be run before this one. |
| M004 | replace-escaped-quotes | Removes escaped <quote>s in a line to avoid matching linting issues where they do not apply. A line's length and content is altered so if either of these is important for another rule, that rule should be run before this one. |

### Disabling Rules for a Line or File
---
Any of the rules in the tables above can be suppressed for a specific line or for a whole file:

* To supress a rule(s) for a given line include the following after the line of code for which the rule is to be suppressed:

    ```
    # gaplint: disable=<name_or_code>, <name_or_code> ...
    ```
    
* If the phrase above is too long to fit after the relevant line, suppressions can be declared in the line above for the line below by including the following:

    ```
    # gaplint: disable(nextline)=<name_or_code>, <name_or_code>, ...
    ```
* If rules have been suppressed for a given line using both the in-line and *nextline* options, the union of the two rule sets will be suppressed.

* To suppress rules for a whole file the following must be included before any code is written (i.e. either as the first line of a GAP file, or preceded by any combination of only whitespace, empty lines and comments):

    ```
    # gaplint: disable=<name_or_code>, <name_or_code>, ...
    ```

### Rule Configuration
---
Certain rules can be configured by the user. The configuration hierarchy from top to bottom is as follows:

1. Contents of global variable `__CONFIG` in `gaplint.py`
2. Configuration options entered via the command line
3. Preferences in configuration script `.gaplint.yml`
4. File/line rule suppressions in user's GAP file.
5. Default configuration (no user action required)


detail config options and file and hierarchy 
all default





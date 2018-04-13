### README - gaplint
---
`gaplint` automatically checks the format of a GAP file according to some conventions, called *rules*. It prints the nature and location of instances of incorrect formatting. `gaplint` can be configured to use a specific set of conventions.

### List of all rules
---

To disable all rules for a particular file you can add the line 

    # gaplint: disable = all
    
to the start of the file before any lines that contain any code. All rules are enabled by default. 

| Code | Name | Rule Description |
| --- | --- | --- |
| `W000` | `analyse-lvars` | Warns if there are declared local variables that are not used or assigned but not used|
| `W001` | `empty-lines` | Warns if there are consecutive empty lines |
| `W002` | `line-too-long` | Warns if there is a line which is longer than the configured maximum (defaults to 80) |
| `W003` | `indentation` | Warns if a line is under indented |
| `W004` | `align-assignments` | Warns if there are assignments in consecutive lines that are not aligned|
| `W005` | `align-comments` | Warns if there are comments in consecutive lines that are not aligned|
| `W006` | `trailing-whitespace` | Warns if there is trailing whitespace at the end of a line |
| `W007` | `no-space-after-comment` | Warns if there is no space after any number of # is a line |
| `W008` | `not-enough-space-before-comment` | Warns if there is not enough space before the first # in any line (defaults to 2) |
| `W009` | `space-after-comma` | Warns if a comma is followed by more than one space |
| `W010` | `space-before-comma` | Warns if a comma is preceded by a space |
| `W011` | `space-after-bracket` | Warns if there is a space after an opening bracket |
| `W012` | `space-before-bracket` | Warns if there is a space before a closing bracket |
| `W013` | `multiple-semicolons` | Warns if there is more than one semicolon in a line |
| `W014` | `keyword-function` | Warns if the keyword *function* is not followed by an open bracket |
| `W015` | `whitespace-op-assign` | Warns if there is not exactly one space after an assignment (:=) |
| `W016` | `tabs` | Warns if there are tabs |
| `W017` | `function-local-same-line` | Warns if the keywords *function* and *local* appear in the same line |
| `W018` | `whitespace-op-minus` | Warns if there is not exactly one space either side of a minus (-) operator |
| `W019` | `whitespace-op-plus` | Warns if there is not exactly one space either side of a plus (+) operator  |
| `W020` | `whitespace-op-multiply` | Warns if there is not exactly one space either side of a multiply (\*) operator |
| `W021` | `whitespace-op-negative` | Warns if there is not exactly one space preceding a negative (-) operator |
| `W022` | `whitespace-op-less-than` | Warns if there is not exactly one space either side of a less-than (<) operator |
| `W023` | `whitespace-op-less-equal` | Warns if there is not exactly one space either side of a less-than / equal-to (<=) operator |
| `W024` | `whitespace-op-more-than` | Warns if there is not exactly one space either side of a greater-than(>) operator |
| `W025` | `whitespace-op-more-equal` | Warns if there is not exactly one space either side of greater than or equal to (>=) operator |
| `W026` | `whitespace-op-equals` | Warns if there is not exactly one space either side of equals (=) operator |
| `W027` | `whitespace-op-mapping` | Warns if there is not exactly one space either side of mapping (->) operator |
| `W028` | `whitespace-op-divide` | Warns if there is not exactly one space either side of divide (/) operator | 
| `W029` | `whitespace-op-power` | Warns if there is not exactly one space either side of the power (^) operator |
| `W030` | `whitespace-op-not-equal` | Warns if there is not exactly one space either side of not-equal (<>) operator |
| `W031` | `whitespace-op-double-dot` | Warns if there is not exactly one space either side of arithmetic progression (\.\.) operator |


### Configuration
---
Certain parameters can be configured, for example, the maximum number of characters permitted per line. All rules are enabled by default but can be disable at the command line, by comments in the file itself, or in a configuration file `.gaplint.yml`.

***Configuration keywords:***

* `columns`: maximum number of characters per line. *Defaults to 80*.
* `max-warnings`: maximum number of warnings before `gaplint` aborts. *Defaults to 1000*.
* `indentation`: minimum indentation of nested statements. *Defaults to 2*.
* `disable`: rules can be disabled using their name or code. *Defaults to no rules disabled*.

A list of all of the rules that `gaplint` can apply is given below.

You can alter the configuration in various places, the order of precedence of these is governed by a hierarchy described below. A preference given somewhere higher on the hierarchy than another will be given precedence. Disabled rules accumulate through the hierarchy.

***Where to configure gaplint and the configuration hierarchy (from the top down):***

2. *Configuration options entered via the command line when running*`gaplint`:
    These preferences will be applied for a single run of `gaplint` only (though multiple files may be linted in this run). To configure `gaplint` to be run on `file1`, `file2`, ..., with preferences as in the example above, we enter the following into the command line:

    ```
    gaplint --columns=100 --indentation=4 --disable=W002,W028 file1 file2 ...
    ``` 
    
4. *File/line rule suppressions in user's GAP file (see Disabling Rules for a Line or File*).
 Any of the rules in the tables above, including `all`, can be suppressed for a specific line or for a whole file:

    * To supress a rule(s) for a given line, include the following after the line of code for which the rule is to be suppressed:
     
    ```
    # gaplint: disable=<name_or_code>, <name_or_code> ...
    ```
    * If the above is too long to fit after the relevant line of code, suppressions can be declared in the line above for the line below by including `(nextline)`:

    ```
    # gaplint: disable(nextline)=<name_or_code>, <name_or_code>, ...
    ```
    * If rules have been suppressed for a given line using both the in-line and *nextline* options, the union of the two rule sets given for suppression will be disabled for the line.

    * To suppress rules for a whole file the following must be included before any code is written (i.e. either as the first line of a GAP file, or preceded by any combination of only whitespace, empty lines and comments):

    ```
    # gaplint: disable=<name_or_code>, <name_or_code>, ...
    ```

3. *Preferences in configuration file* `.gaplint.yml`:
      
    To configure `gaplint` as in the above examples, create a `.gaplint.yml` file containing the following lines:
    
    ```yaml
    columns: 100
    indentation: 4
    disable:
    - W002
    - W028
    ```
    `gaplint` looks for the `.gaplint.yml` file in the current directory, and its ancestors, until it reaches a directory containing a `git` repository or the `.gaplint.yml` file is located. If there is no `.gaplint.yml` file, then the default configuration options are used. The options configured in `.gaplint.yml` are applied to every file on which `gaplint` is run from the current directory unless overruled higher in the hierarchy. 



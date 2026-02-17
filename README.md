# utool
Cli tools for manipulating text.

[![Testing: pytest](https://img.shields.io/badge/testing-pytest-yellow)](https://docs.pytest.org)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](https://opensource.org/license/mit/)
[![0 dependencies!](https://0dependencies.dev/0dependencies.svg)](https://0dependencies.dev)

# Introduction

In the spirit of small and focused command-line programs that comprise
the (\*)nix shell,
these utilities provide functions that I often find myself
cobbling together on-the-fly with `awk` and `sed`.

Laziness drove me to what you find here.

## ucol

Select columns from a file.

### example

here is some test data:

```
> cat data
2000 AUG $3,698.14 -$1,109.44
2000 SEP $870.96 -$261.29
2001 AUG $1,676.56 -$502.97
2001 AUG $940.80 -$282.24
2001 SEP $2,070.10 -$621.03
```

select some columns: 

```
> cat data | ucol 2 1 2
AUG 2000 AUG
SEP 2000 SEP
AUG 2001 AUG
AUG 2001 AUG
SEP 2001 SEP
```

Here `ucol` is used
to extract a few columns
from the data file.
Note that the columns can be specified in any order,
and can be specified more than once.

Negative values can be specified as column numbers; these
will index from the right:

```
> cat data | ucol -1
-$1,109.44
-$261.29
-$502.97
-$282.24
-$621.03
```

A range of column numbers can be specified
with a plus sign (+) immediately following a column number&mdash;this will
indicate the column number plus all subsequent columns:

```
> cat data | ucol 3+
$3,698.14 -$1,109.44
$870.96 -$261.29
$1,676.56 -$502.97
$940.80 -$282.24
$2,070.10 -$621.03
```

A substring of a column can be specified
with a square bracket immediately following a column number.
For example: `2[5,7]` will select the 5th, 6th, and 7th characters from the second column.
The square bracket contains a starting character (optional, default=1), a comma, and
an ending character (optional, default is the end of the column value). Starting and ending characters can also be specified as negative numbers, which index from the right.

To specify a substring using a negative column number, an underscore (_) must be used instead of a minus sign (-)&mdash;this is to avoid ambiguity during option parsing. For example: `_2[,3]` will grab the first three characters from the second column from the right.

You may have to escape (or quote) the square bracket characters, depending on your shell:

```
> cat data | ucol '_2[2,-4]'
3,698
870
1,676
940
2,070
```

If no columns are specified, all columns will be extracted (1+).

Output as csv:

```
> cat data | ucol 1 2 3 --to-csv
2000,AUG,"$3,698.14"
2000,SEP,$870.96
2001,AUG,"$1,676.56"
2001,AUG,$940.80
2001,SEP,"$2,070.10"
```

Output as csv with a header line:

```
> cat data | ucol --to-csv 'year,month,amount' 1 2 3
year,month,amount
2000,AUG,"$3,698.14"
2000,SEP,$870.96
2001,AUG,"$1,676.56"
2001,AUG,$940.80
2001,SEP,"$2,070.10"
```

### syntax
```
ucol [-dDnsf] [--csv] [--to-csv] [--to-json] [--to-sc] column-numbers
```

### options
```
  -dc                 use 'c' as input column delimiter
  --delimiter         (default whitespace)

  -Dc                 use 'c' as output column delimiter
  --output-delimiter  (default space)

  -f FILE             read input from FILE
  --file              (default stdin)

  --csv               parse lines as csv

  --un-comma          remove commas and/or leading dollar sign ($) from numbers

  --to-json           output as json (list of dict) using first row as keys

  --pretty-json       output as formatted json (enables --to-json)

  --to-csv            output as csv
  --to-csv H1,H2,...  output as csv with header line
                      Note: when used without a header, place after column numbers
                      (e.g. ucol 1 3 --to-csv) or use -- separator
                      (e.g. ucol --to-csv -- 1 3)

  --to-sc             output as sc (spreadsheet calculator) format (enables --un-comma)

  -n                  allow null columns
  --null-columns
                      Normally, when multiple column delimiters are
                      encountered in sequence, they are treated as a single
                      delimiter. If null columns are allowed, each column
                      delimiter starts a new column, and sequential delimiters
                      indicate zero-length columns.

  --no-strip          don't strip leading and trailing delimiters from line
                      (default=False, in other words, strip happens by default)

  -s                  handle errors strictly
  --strict
                      If a line is encountered that doesn't have enough columns
                      to satisfy the command, it is skipped. If the strict flag
                      is set, this condition will cause the program to stop.
```

## usum

Aggregate columns in a file (sum, average, min, max).

### example

Here is some test data:

```
> cat data
2000 AUG $3,698.14 -$1,109.44
2000 SEP $870.96 -$261.29
2001 AUG $1,676.56 -$502.97
2001 AUG $940.80 -$282.24
2001 SEP $2,070.10 -$621.03
```

Sum by the first two columns (think of the `SQL groupby` functionality):

```
> cat data | usum 1 2
2000 AUG 3698.14 -1109.44
2000 SEP 870.96 -261.29
2001 AUG 2617.36 -785.21
2001 SEP 2070.1 -621.03
```

Notice that `2001 AUG` records are combined. Notice also that the "\$" and ","
characters are ignored (effectively stripped from the columns). The value in a column with the largest precision
sets the precision for all of the sums of that column (this
gets rid of unintuitive floating point math things&mdash;without this the summed line above
would be `2001 AUG 2617.3599999999997 -785.21`).

The specified order of the columns is preserved:

```
> cat data | usum 2 1
AUG 2000 3698.14 -1109.44
SEP 2000 870.96 -261.29
AUG 2001 2617.36 -785.21
SEP 2001 2070.1 -621.03
```

Add a count for each row:

```
> cat data | usum 1 2 -c
2000 AUG 1 3698.14 -1109.44
2000 SEP 1 870.96 -261.29
2001 AUG 2 2617.36 -785.21
2001 SEP 1 2070.1 -621.03
```

The count of rows matching the group-by columns is inserted between
the column values and the sums.

Sum by just one column:

```
> cat data | usum 1
2000 0 4569.1 -1370.73
2001 0 4687.46 -1406.24
```

Notice that the non-numeric values in the second column are treated as zero.

Combine with `ucol`:

```
> cat data | ucol 2 3 4
AUG $3,698.14 -$1,109.44
SEP $870.96 -$261.29
AUG $1,676.56 -$502.97
AUG $940.80 -$282.24
SEP $2,070.10 -$621.03
  
> cat data | ucol 2 3 4 | usum 1
AUG 6315.5 -1894.65
SEP 2941.06 -882.32
```

Sum each column into a single line (group by zero/nothing):

```
> cat data |  usum 0
10003 0 9256.56 -2776.97
```

Sum all the numbers in a file by not providing a column number:

```
> cat data | usum
16482.59
```

All the numeric tokens in the file are summed.

Compute the average instead of sum:

```
> cat data | usum --avg 1 2
2000 AUG 3698.14 -1109.44
2000 SEP 870.96 -261.29
2001 AUG 1308.68 -392.605
2001 SEP 2070.1 -621.03
```

Find the minimum or maximum values:

```
> cat data | usum --min 1 2
2000 AUG 3698.14 -1109.44
2000 SEP 870.96 -261.29
2001 AUG 940.8 -502.97
2001 SEP 2070.1 -621.03

> cat data | usum --max 1 2
2000 AUG 3698.14 -1109.44
2000 SEP 870.96 -261.29
2001 AUG 1676.56 -282.24
2001 SEP 2070.1 -621.03
```

### syntax
```
usum [-h] [--delimiter DELIMITER] [--count] [--strict] [--avg|--min|--max] [-f FILE] [groupby ...]
```

### options
```
  --delimiter, -d DELIMITER
            input/output column delimiter, default=' '

  -f FILE   read input from FILE
  --file    (default stdin)

  --count, -c
            add count of items included in result for each output line

  --avg     compute average instead of sum
  --min     compute minimum instead of sum
  --max     compute maximum instead of sum

  -s        handle errors strictly
  --strict
            If a line is encountered that doesn't have the right number
            of columns to satisfy the command, it is skipped. If a column
            to be summed is not a numerical value, it is treated as zero.
            If a column to be summed contains "$" or ",", these characters
            are ignored.

            If the strict flag is set, any of these conditions will
            cause the program to stop.
```

## upar

Format text into paragraphs.

### example

Here is some test data:

```
> cat test_data.txt 

When in the Course of human events, it
becomes necessary for one people to
dissolve the political bands which have
connected them with another, and to
assume among the powers of the earth,
the separate and equal station to which
the Laws of Nature and of Nature's God
entitle them, a decent respect to the
opinions of mankind requires that they
should declare the causes which impel
them to the separation.
```

Format the test data into paragraphs of lines not exceeding 80 characters:

```
> upar < test_data.txt

When in the Course of human events, it becomes necessary for one people to
dissolve the political bands which have connected them with another, and to
assume among the powers of the earth, the separate and equal station to which
the Laws of Nature and of Nature's God entitle them, a decent respect to the
opinions of mankind requires that they should declare the causes which impel
them to the separation.
```

Format the test data into paragraphs of lines not exceeding 60 characters:

```
> upar -l60 < test_data.txt

When in the Course of human events, it becomes necessary for
one people to dissolve the political bands which have
connected them with another, and to assume among the powers
of the earth, the separate and equal station to which the
Laws of Nature and of Nature's God entitle them, a decent
respect to the opinions of mankind requires that they should
declare the causes which impel them to the separation.
```

Add an indent:

```
> upar -i5 < test_data.txt

     When in the Course of human events, it becomes necessary for one people to
     dissolve the political bands which have connected them with another, and to
     assume among the powers of the earth, the separate and equal station to
     which the Laws of Nature and of Nature's God entitle them, a decent respect
     to the opinions of mankind requires that they should declare the causes
     which impel them to the separation.
```

Multi-paragraph:

```
> upar -i5 -l 60 < test_data_2.txt

     When in the Course of human events, it becomes
     necessary for one people to dissolve the political
     bands which have connected them with another, and to
     assume among the powers of the earth, the separate and
     equal station to which the Laws of Nature and of
     Nature's God entitle them, a decent respect to the
     opinions of mankind requires that they should declare
     the causes which impel them to the separation.

     We hold these truths to be self-evident, that all men
     are created equal, that they are endowed by their
     Creator with certain unalienable Rights, that among
     these are Life, Liberty and the pursuit of Happiness.
```

If `indent` is not specified, then the indent of the
first line is used:

```
> cat test_data_3.txt

    We hold these truths to be self-evident,
that all men are created equal,
        that they are endowed by their Creator with certain unalienable Rights,
  that among these are Life,
Liberty and the pursuit of Happiness.
    
> upar < test_data_3.txt

    We hold these truths to be self-evident, that all men are created equal,
    that they are endowed by their Creator with certain unalienable Rights, that
    among these are Life, Liberty and the pursuit of Happiness.
```
 
Add a prefix to each line (useful for code comments):

```
> echo "This is a long comment that needs to wrap nicely" | upar -l 40 --prefix "# "
# This is a long comment that needs to
# wrap nicely
```

Use hanging indent for bullet points or lists:

```
> echo "* This is a bullet point that wraps to multiple lines" | upar -l 40 --hanging 2
* This is a bullet point that wraps to
  multiple lines
```

Combine prefix and hanging indent:

```
> echo "TODO: Fix the bug in the login flow that causes issues" | upar -l 35 --prefix "# " --hanging 6
# TODO: Fix the bug in the login
#       flow that causes issues
```

### use with vi

From `command` mode in `vi`, the next 10 lines can be formatted
into a paragraph with this command:

```
:.,+9!upar -l75
```

This is helpful for cleaning up comment blocks or formatting simple text files.

### syntax
```
upar [-liHpf]
```

### options
```
  -ln         use 'n' as the max output line length
  --length    (default 80)

  -in         indent lines by 'n', included in line length
  --indent    (default indent of first line)

  -Hn         additional indent for continuation lines
  --hanging   (default 0)

  -p STRING   prepend STRING to each line
  --prefix    (default none)

  -f FILE     read input from FILE
  --file      (default stdin)
```

# Installation

1. clone the repo
2. `pip install .` from the repo's top level
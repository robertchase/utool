# utool
Cli tools for manipulating text.

## Introduction

In the spirit of small and focused command-line programs that comprise
the (\*)nix shell,
these utilities provide functions that I often find myself
cobbling together on-the-fly with `awk` and `sed`.

Laziness drove me to what you find here.

## ucol

Select columns from a file.

### example

```
> ls -l

total 40
-rw-r--r--   1 bob  staff   1068 Jun 12 05:38 LICENSE
-rw-------   1 bob  staff     81 Jun 12 05:45 Makefile
-rw-r--r--@  1 bob  staff    226 Jun 12 19:03 README.md
-rw-------@  1 bob  staff   4539 Jun 12 18:42 ucol.py

> ls -l | ucol 5 1 5

1068 -rw-r--r-- 1068
81 -rw------- 81
1045 -rw-r--r--@ 1045
4539 -rw-------@ 4539
```

Here `ucol` is used
to extract a few columns
from the results of the `ls` command.
Note that the columns can be specified in any order,
and can be specified more than once.

Values of -1 through -9 can be specified as column numbers; these
will index from the right.

```
> ls -l | ucol -1

40
LICENSE
Makefile
README.md
ucol.py
```

### syntax
```
ucol [-dDns] column-numbers [filename]
```

### options
```
  -dc                 use 'c' as input column delimiter
  --delimiter         (default whitespace)

  -Dc                 use 'c' as output column delimiter
  --output-delimiter  (default space)

  -n                  allow null columns
  --null-columns
                      Normally, when multiple column delimiters are
                      encountered in sequence, they are treated as a single
                      delimiter. If null columns are allowed, each column 
                      delimiter starts a new column, and sequential delimiters
                      indicate zero-length columns.
            

  -s                  handle errors strictly
  --strict
                      If a line is encountered that doesn't have enough columns
                      to satisfy the command, it is skipped. If the strict flag
                      is set, this condition will cause the program to stop.
```

## usum

# usum

Sum columns in a file.

### example

Here is some test data:

```
home/test:~> cat data
Jul 30 11
Jul 31 97
Jul 31 8
Aug 1 127
Aug 2 17
Aug 2 54
```

Sum by the first two columns (think of the `SQL groupby` functionality):

```
home/test:~> cat data | usum 1 2
Aug 1 127
Aug 2 71
Jul 30 11
Jul 31 105
```

Specified order of the columns is preserved:

```
home/test:~> cat data | usum 2 1
31 Jul 105
1 Aug 127
30 Jul 11
2 Aug 71
```

Sum by just one column:

```
home/test:~> cat data | usum 1
Aug 5 198
Jul 92 116
```

Combine with `ucol`:

```
home/test:~> cat data | ucol 1 3
Jul 11
Jul 97
Jul 8
Aug 127
Aug 17
Aug 54

home/test:~> cat data | ucol 1 3 | usum 1
Aug 198
Jul 116
```

Sum all the numbers in a file by not providing a column number:

```
home/test:~> cat data  usum
411
```

All the numeric tokens in the file are summed.

### syntax
```
usum [-s] [groupby [groupby ...]]
```

### options
```
  -s        handle errors strictly
  --strict
            If a line is encountered that doesn't have the right number
            of columns to satisfy the command, it is skipped. If a column
            to be summed is not a numerical value, it is treated as zero.
            If the strict flag is set, either of these conditions will
            cause the program to stop.
```

## upar

Format text into paragraphs.

### example

Here is some test data:

```
cat test_data.txt 

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
upar < test_data.txt

When in the Course of human events, it becomes necessary for one people to
dissolve the political bands which have connected them with another, and to
assume among the powers of the earth, the separate and equal station to which
the Laws of Nature and of Nature's God entitle them, a decent respect to the
opinions of mankind requires that they should declare the causes which impel
them to the separation.
```

Format the test data into paragraphs of lines not exceeding 60 characters:

```
upar -l60 < test_data.txt

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
upar -i5 < test_data.txt

     When in the Course of human events, it becomes necessary for one people to
     dissolve the political bands which have connected them with another, and to
     assume among the powers of the earth, the separate and equal station to
     which the Laws of Nature and of Nature's God entitle them, a decent respect
     to the opinions of mankind requires that they should declare the causes
     which impel them to the separation.
```

Multi-paragraph:

```
upar -i5 -l 60 < test_data_2.txt

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
cat test_data_3.txt

    We hold these truths to be self-evident,
that all men are created equal,
        that they are endowed by their Creator with certain unalienable Rights,
  that among these are Life,
Liberty and the pursuit of Happiness.
    
upar < test_data_3.txt

    We hold these truths to be self-evident, that all men are created equal,
    that they are endowed by their Creator with certain unalienable Rights, that
    among these are Life, Liberty and the pursuit of Happiness.
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
upar [-li] [groupby [groupby ...]]
```

### options
```
  -ln       use 'n' as the max output line length
  --length  (default 80)
  
  -in       indent lines by 'n', included in line length
  --indent  (default indent of first line)
```
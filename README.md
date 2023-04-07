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
-rw-------@  1 bob  staff   4539 Jun 12 18:42 ucol.c

> ls -l | ucol 5 1 5

total
1068 -rw-r--r-- 1068
81 -rw------- 81
1045 -rw-r--r--@ 1045
4539 -rw-------@ 4539


> ls -l | ucol 5 1 5 | tail -n +2

1068 -rw-r--r-- 1068
81 -rw------- 81
1032 -rw-r--r--@ 1032
4539 -rw-------@ 4539
```

Here `ucol` participates, with other cli tools,
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
ucol.c
```

### syntax
```
ucol [-dDno] column-numbers [filename]
```

### options
```
  -dc       use 'c' as input column delimiter
            (default whitespace)
  -Dc       use 'c' as output column delimiter
            (default space)
  -n        allow null columns

            Normally, when multiple column delimiters are encountered in
            sequence, they are treated as a single delimiter. If null columns
            are allowed, each column delimiter starts a new column, and
            sequential delimiters indicate zero-length columns.

  -oFile    output filename
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

Sum just one column:

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

### syntax
```
usum [-h] [groupby [groupby ...]]
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
upar -c60 < test_data.txt

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
upar -i5 -c 60 < test_data_2.txt

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
:.,+9!upar -c75
```

This is helpful for cleaning up comment blocks or formatting simple text files.

### syntax
```
upar [-hci] [groupby [groupby ...]]
```

### options
```
  -cn       use 'n' as the max output line length
            (default 80)
  -in       indent lines by 'n', included in line length
            (default indent of first line)
```
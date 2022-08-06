#! /usr/bin/env python3


def format(data, columns=80, indent=0):

    def _indent(text):
        return f"{' ' * indent}{text}"

    line = ""
    maxlen = columns - indent
    for word in data.split():

        if not line:
            if len(word) >= maxlen:
                yield _indent(word)
            else:
                line = word

        elif len(newl := f"{line} {word}") > maxlen:
            yield _indent(line)
            line = word

        else:
            line = newl

    if line:
        yield _indent(line)


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="break text into paragraphs")
    parser.add_argument("--columns", "-c", type=int, default=80)
    parser.add_argument("--indent", "-i", type=int, default=0)
    args = parser.parse_args()
    for line in format(sys.stdin.read(), args.columns, args.indent):
        print(line)

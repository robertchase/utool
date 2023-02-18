#! /usr/bin/env python3


def format(data, columns=80, indent=0):

    line = ""
    top = True
    new_paragraph = False

    maxlen = columns - indent
    for data_line in data.split("\n"):
        if len(data_line.rstrip()) == 0:
            if not top:
                if line:
                    if new_paragraph:
                        yield ""
                        new_paragraph = False
                    yield f"{' ' * indent}{line}"
                    line = ""
                new_paragraph = True
        else:
            top = False
            for word in data_line.split():
                if not line:
                    if len(word) >= maxlen:
                        if new_paragraph:
                            yield ""
                            new_paragraph = False
                        yield f"{' ' * indent}{word}"
                    else:
                        line = word

                elif len(newl := f"{line} {word}") > maxlen:
                    if new_paragraph:
                        yield ""
                        new_paragraph = False
                    yield f"{' ' * indent}{line}"
                    line = word

                else:
                    line = newl

    if line:
        if new_paragraph:
            yield ""
            new_paragraph = False
        yield f"{' ' * indent}{line}"


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="break text into paragraphs")
    parser.add_argument("--columns", "-c", type=int, default=80)
    parser.add_argument("--indent", "-i", type=int, default=0)
    args = parser.parse_args()
    for line in format(sys.stdin.read(), args.columns, args.indent):
        print(line)

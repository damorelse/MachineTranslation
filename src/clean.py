#!/usr/bin/python

import re
import sys

__author__="daniel"
__date__ ="$Feb 22, 2014 7:04:27 AM$"

import sys

def main():
    data = sys.stdin.readlines()

    pattern = re.compile(r'(?<=\015)(.{4,6}\s.{4}\shttp://www\.en8848\.com\.cn/.{7}\015)')

    for line in data:
        start = 0

        if pattern.search(line):
            i = pattern.finditer(line)

            for m in i:
                sys.stdout.write(line[start:m.start()].replace('\015', '\n'))
                sys.stdout.write(' ')

                start = m.end()

            sys.stdout.write(line[start:].replace('\015', '\n'))
        else:
            sys.stdout.write(line.replace('\015', '\n'))

if __name__ == "__main__":
    main()

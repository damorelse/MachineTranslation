#!/usr/bin/python

import re
import sys

__author__="daniel"
__date__ ="$Feb 22, 2014 7:04:27 AM$"

def main():
    with open(sys.argv[1], 'r') as f:
        data = f.readlines()

    pattern = re.compile(r'(?<=\015)(.{4,6}\s.{4}\shttp://www\.en8848\.com\.cn/.{7}\015)')

    with open(sys.argv[2], 'w') as f:
        for line in data:
            start = 0
    
            if pattern.search(line):
                i = pattern.finditer(line)

                for m in i:
                    f.write(line[start:m.start()].replace('\015', ''))
                    f.write(' ')

                    start = m.end()

                f.write(line[start:].replace('\015', ''))
            else:
                f.write(line.replace('\015', ''))

if __name__ == "__main__":
    main()

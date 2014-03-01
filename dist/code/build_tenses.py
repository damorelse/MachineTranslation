#! /usr/bin/python
# -*- coding: utf8 -*-

__author__="daniel"
__date__ ="$Feb 27, 2014 3:17:35 PM$"

import sys

def main():
    print '"tenses:"'
    print "{"
    
    for line in sys.stdin:
        inf, pres, past, part = unicode(line, 'utf8').strip().split(',')
        
        print '"%s": "INF",' % inf.split(' ')[0].replace('|', '')
        
        if pres[-1] == unicode('ß', 'utf8'):
            print '"%s": "2",' % (pres + 't')
        elif pres[-2:] == unicode('ßt', 'utf8') or pres[-2:] == 'st':
            print '"%s": "2",' % (pres)
        else:
            print '"%s": "2",' % (pres[:-1] + 'st')
            
        print '"%s": "3",' % pres
        print '"%s": "P",' % past
        print '"%s": "PP",' % part.split(' ')[-1]
        
    print "}"

if __name__ == "__main__":
    main()

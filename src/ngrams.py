#! /usr/bin/python

import json
import re
import sys

__author__="daniel"
__date__ ="$Feb 23, 2014 6:14:04 AM$"

def main():
    data = []
    
    with open(sys.argv[1], 'r') as f:
        for line in f:
            if len(data) == 0 or re.match(r'.*[.?!]\W*$', data[-1]):
                # If the previous line looks like the end of a paragraph, add a new one
                data.append(line)
            else:
                # Otherwise, append this line to the end of the previous one
                data[-1] = data[-1].strip() + ' ' + line
        
    pattern = re.compile(r'[.?!].*?\s')
    splitter = re.compile(r'[^A-Za-z\'-]')
    ngrams = {"unigrams": {}, "bigrams": {}, "trigrams": {}}
    counts = [0, 0, 0]
    
    for line in data:
        matches = pattern.finditer(line)
        start = 0
        
        for m in matches:
            sentence = line[start:m.end()].lower()
            start = m.end()
            
            words = splitter.split(sentence)
            
            previous = None
            vorprevious = None
            
            for word in words:
                if not re.match(r'^\s*$', word):
                    add_ngram(word, ngrams["unigrams"])
                    counts[0] += 1

                    if previous != None:
                        add_ngram(previous + ' ' + word, ngrams["bigrams"])
                        counts[1] += 1

                        if vorprevious != None:
                            add_ngram(vorprevious + ' ' + previous + ' ' + word, ngrams["trigrams"])
                            counts[2] += 1

                    vorprevious = previous
                    previous = word
                    
    ngrams['unigram_probabilities'] = calculate_probabilities(ngrams["unigrams"], counts[0])
    ngrams['bigram_probabilities'] = calculate_probabilities(ngrams["bigrams"], counts[1])
    ngrams['trigram_probabilities'] = calculate_probabilities(ngrams["trigrams"], counts[2])

    print json.dumps(ngrams)

def calculate_probabilities(ngrams, count):
    probs = {}
    
    for ngram in ngrams:
        probs[ngram] = float(ngrams[ngram] + 1) / (float(count) + len(ngrams))
        
    return probs

def add_ngram(ngram, dictionary):
    if ngram in dictionary:
        dictionary[ngram] += 1
    else:
        dictionary[ngram] = 1
    
if __name__ == "__main__":
    main()

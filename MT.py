import json
from pprint import pprint
import re

def main():
    json_data = open('dictionary.json')
    dictionary = json.load(json_data)
    json_data = open('sentences.json')
    sentences = json.load(json_data)

    engSent = []
    for line in sentences["dev"]:
        for p in dictionary["phrases"]:
            line = line.replace(" "+p+" ", " "+dictionary["phrases"][p]+" ")

        line = re.sub('[,.]+', '', line)
        words = line.split(" ")
        output = []

        for w in words:
            output.append(lookup(dictionary, w))

        engSent.append(output)


    print engSent

def lookup(dictionary, word):
    translation = word
    
    if word in dictionary["words"]:
        translation = dictionary["words"][word][0]
    elif word.lower() in dictionary["words"]:
        translation = dictionary["words"][word.lower()][0]
    else:
        compound = compound_lookup(dictionary["words"], word)
        
        if compound:
            translation = compound
            
    return translation

def compound_lookup(dictionary, word):
    translation = None
    i = len(word)
    
    while i > 0:
        if word[:i] in dictionary:
            rest = None
            
            if i < len(word):
                rest = compound_lookup(dictionary, word[i].upper() + word[i+1:])
            
                if rest:
                    translation = dictionary[word[0:i]][0] + ' ' + rest
                    break
            else:
                translation = dictionary[word[0:i]][0]
                break
#        else:
#            print "%s not in dict" % word[:i]
            
        i -= 1
        
    return translation

if __name__ == '__main__':
    main()
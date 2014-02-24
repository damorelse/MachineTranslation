import json
import re
import sys

class MT:
    def __init__(self, file):
        json_data = open(file)
        self.dictionary = json.load(json_data)
        
    def translate(self, file):
        engSent = []
        json_data = open(file)
        sentences = json.load(json_data)
        
        for line in sentences["dev"]:
#            line = self.interpolate_phrases(line)

            words = self.split_compounds(re.split("[^A-Za-z0-9-]+", line))
            output = []

            for w in words:
                output.append(self.lookup(w))

            engSent.append(output)
        
        return engSent

    def interpolate_phrases(self, line):
        for p in self.dictionary["phrases"]:
            line = line.replace(" " + p + " ", " " + self.dictionary["phrases"][p] + " ")

        return line
    
    def lookup(self, word):
        translation = word

        if word in self.dictionary['words']:
            translation = self.dictionary['words'][word][0]
        elif word.lower() in self.dictionary['words']:
            translation = self.dictionary['words'][word.lower()][0]

        return translation

    def split_compounds(self, words):
        split = []
        
        for word in words:
            if word in self.dictionary['words']:
                split.append(word)
            else:
                split.extend(self.compound_split(word))
                
        return split
                
    def compound_split(self, word):
        words = []
        i = len(word)

        while i > 0:
            if word[:i] in self.dictionary['words']:
                if i < len(word):
                    rest = self.compound_split(word[i].upper() + word[i+1:])

                    if rest:
                        words.append(word[0:i])
                        words.extend(rest)
                        break
                else:
                    words.append(word[0:i])
                    break

            i -= 1

        return words

def main():
    mt = MT('%s/dictionary.json' % sys.argv[1])
    print mt.translate('%s/sentences.json' % sys.argv[1])

if __name__ == '__main__':
    main()
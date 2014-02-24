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
            line = self.interpolate_phrases(line)

            line = re.sub('[,.]+', '', line)
            words = line.split(" ")
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

        if word in self.dictionary["words"]:
            translation = self.dictionary["words"][word][0]
        elif word.lower() in self.dictionary["words"]:
            translation = self.dictionary["words"][word.lower()][0]
        else:
            compound = self.compound_lookup(self.dictionary["words"], word)

            if compound:
                translation = compound

        return translation

    def compound_lookup(self, dictionary, word):
        translation = None
        i = len(word)

        while i > 0:
            if word[:i] in dictionary:
                rest = None

                if i < len(word):
                    rest = self.compound_lookup(dictionary, word[i].upper() + word[i+1:])

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

def main():
    mt = MT('%s/dictionary.json' % sys.argv[1])
    print mt.translate('%s/sentences.json' % sys.argv[1])

if __name__ == '__main__':
    main()
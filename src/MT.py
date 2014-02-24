#!/usr/bin/python
# -*- coding: utf8 -*-

#import codecs
import json
import re
import sys

class MT:
    COMPOUND_PREPOSITIONS = {
        u'ans': [u'an', u'das'],
        u'am': [u'an', u'dem'],
        u'aufs': [u'auf', u'das'],
        u'beim': [u'bei', u'dem'],
        u'durchs': [u'durch', u'das'],
        u'fürs': [u'für', u'das'],
        u'hinterm': [u'hinter', u'dem'],
        u'hinters': [u'hinter', u'das'],
        u'ins': [u'in', u'das'],
        u'übers': [u'über', u'das'],
        u'ums': [u'um', u'das'],
        u'unters': [u'unter', u'das'],
        u'vom': [u'von', u'dem'],
        u'vors': [u'vor', u'das'],
        u'zum': [u'zu', u'dem'],
        u'zum': [u'zu', u'dem']
    }

    def __init__(self, file):
        with open(file) as f:
            self.dictionary = json.load(f)
#        with codecs.open(file, encoding='utf8') as f:
#            self.dictionary = json.load(f, encoding='utf8')
        
    def translate(self, file):
        engSent = []
        
        sentences = self.read_sentences(file)

        for line in sentences["dev"]:
            words = self.split_line(line)
            words = self.interpolate_phrases(words)
            words = self.split_compounds(words)
            output = []

            for w in words:
                # Remove the curly braces from idioms
                if re.match('{(.*)}', w):
                    w = w[1:-1]
                    
                output.append(self.lookup(w))

            engSent.append(output)
        
        return engSent
    
    @staticmethod
    def read_sentences(file):
        with open(file) as f:
            sentences = json.load(f)
#        with codecs.open(file, encoding='utf8') as f:
#            sentences = json.load(f, encoding='utf8')
            
        return sentences
    
    @staticmethod
    def split_line(line):
        words = []
        
        for word in re.split(r'[,.!?:;@#$%^&*()\[\]{}<>/\\+=\'" \t]+', line):
            if len(word) > 0:
                words.append(word)
        
        return words

    """
    Find phrases in the source sentence and replace them with idiomatic
    translations.  The translations will be wrapped in curly braces to prevent
    them from accidentally being retranslated later.
    """
    def interpolate_phrases(self, words):
        new = words
        changed = True
        
        while changed:
            changed = False
            
            for i in range(len(new) - 1):
                for j in range(len(new), i + 1, -1):
                    phrase = ' '.join(new[i:j])
                    
                    if phrase in self.dictionary['phrases']:
                        new = new[:i] + ['{' + self.dictionary['phrases'][phrase] + '}'] + new[j:]
                        changed = True
                        break
                        
                if changed:
                    break
            
        return new
    
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
            parts = word.split('/')
            
            if parts[0] in self.dictionary['words']:
                split.append(parts[0])
            elif len(parts) == 1 or re.match('NN.*', parts[1]):
                split.extend(self.split_noun(parts[0]))
            elif parts[1] == 'IN':
                split.extend(self.split_preposition(parts[0]))
                
        return split
                
    def split_noun(self, word):
        words = []
        i = len(word)

        while i > 0:
            if word[:i] in self.dictionary['words']:
                if i < len(word):
                    rest = self.split_noun(word[i].upper() + word[i+1:])

                    if rest:
                        words.append(word[0:i])
                        words.extend(rest)
                        break
                else:
                    words.append(word[0:i])
                    break

            i -= 1

        if not words:
            words.append(word)
            
        return words
    
    def split_preposition(self, preposition):
        split = []
        
        if preposition in self.COMPOUND_PREPOSITIONS:
            split.extend(self.COMPOUND_PREPOSITIONS[preposition])
        else:
            split.append(preposition)
            
        return split
    
def main():
    mt = MT('%s/dictionary.json' % sys.argv[1])
    print mt.translate('%s/sentences.json' % sys.argv[1])

if __name__ == '__main__':
    main()
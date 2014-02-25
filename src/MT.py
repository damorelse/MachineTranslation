 #!/usr/bin/python
# -*- coding: utf8 -*-

import codecs
import json
import re
import sys
import os.path
import itertools
from nltk.stem.snowball import SnowballStemmer
from germanPOStagger import POStagger
# here is a reference for the tags:
# http://www.coli.uni-saarland.de/projects/sfb378/negra-corpus/stts.asc
from LanguageModel import LanguageModel



NONWORD = unicode(r'[^A-ZÄÖÜa-zäöüß_-]+', encoding='utf8')

COMPOUND_PREPOSITIONS = {
    u'ans': [u'an_APPR', u'das_ART'],
    u'am': [u'an_APPR', u'dem_ART'],
    u'aufs': [u'auf_APPR', u'das_ART'],
    u'beim': [u'bei_APPR', u'dem_ART'],
    u'durchs': [u'durch_APPR', u'das_ART'],
    u'fürs': [u'für_APPR', u'das_ART'],
    u'hinterm': [u'hinter_APPR', u'dem_ART'],
    u'hinters': [u'hinter_APPR', u'das_ART'],
    u'ins': [u'in_APPR', u'das_ART'],
    u'übers': [u'über_APPR', u'das_ART'],
    u'ums': [u'um_APPR', u'das_ART'],
    u'unters': [u'unter_APPR', u'das_ART'],
    u'vom': [u'von_APPR', u'dem_ART'],
    u'vors': [u'vor_APPR', u'das_ART'],
    u'zum': [u'zu_APPR', u'dem_ART'],
    u'zur': [u'zu_APPR', u'der_ART']
}


class MT:

  
    def __init__(self, file):
        
        self.dictionary = self.read_json(file)
        self.stemmer = SnowballStemmer("german") 
        self.tagger = POStagger() 
        self.trainLM()
        
        
    def translate(self, file):
        
        engSent = []        
        sentences = self.read_json(file)
        dev = self.tagger.tag(sentences['dev'])

        for line in dev:
            phrases = self.split_line(line)
            
            for words in phrases:
                words = self.interpolate_phrases(words)
                words = self.split_compounds(words)
                output = []

                for w in words:
                    # Remove the curly braces from idioms
                    if re.match('{(.*)}', w):
                        w = w[1:-1]

                    output.append(self.lookup(w))

                # send sentence to permutationTester (limit to 9 words)
    #            if len(output) < 9:
    #                output = self.permutationTester(output)    

                engSent.append(output)
        
        return engSent
  
    
    @staticmethod
    def read_json(file):

        with codecs.open(file, encoding='utf8') as f:
            sentences = json.load(f, encoding='utf8')
            
        return sentences
   
    
    @staticmethod
    def split_line(line):
  
        phrases = []
        words = []  
        
        for word in re.findall(r'[^\s]+_(?:[A-Z]+|\$[.,(])', line):
            if len(word) > 0 and word[-2] == '$':
                phrases.append(words)
                words = []
            elif len(word) > 0:
                words.append(word)
        
        if len(words) > 0:
            phrases.append(words)
        
        return phrases


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
        parts = word.split('_')

        if parts[0] in self.dictionary['words']:
            translation = self.dictionary['words'][parts[0]][0]
        elif parts[0].lower() in self.dictionary['words']:
            translation = self.dictionary['words'][parts[0].lower()][0]

        return translation


    def split_compounds(self, words):
        
        split = []
        for word in words:
            parts = word.split('_')
            
            if parts[0] not in self.dictionary['words'] and parts[0].lower() not in self.dictionary['words']:
                if parts[1] == 'NN':
                    split.extend(self.split_noun(parts[0], parts[1]))
                elif parts[1] == 'APPRART':
                    split.extend(self.split_preposition(parts[0], parts[1]))
                else:
                    split.append(word)
            else:
                split.append(word)
                 
        return split
              
                
    def split_noun(self, word, tag):
 
        words = []
        i = len(word)

        while i > 0:
            if word[:i] in self.dictionary['words']:
                if i < len(word):
                    rest = self.split_noun(word[i].upper() + word[i+1:], tag)

                    if rest:
                        words.append(word[0:i] + '_' + tag)
                        words.extend(rest)
                        break
                else:
                    words.append(word[0:i] + '_' + tag)
                    break

            i -= 1

        if not words:
            words.append(word + '_' + tag)
            
        return words
    
    
    def split_preposition(self, preposition, tag):
 
        split = []
        
        if preposition in COMPOUND_PREPOSITIONS:
            split.extend(COMPOUND_PREPOSITIONS[preposition])
        else:
            split.append(preposition + '_' + tag)
            
        return split
        
        
    def trainLM(self):
        
        # open clean text and join all lines
        text = ''.join(open(os.path.dirname(__file__) + '/../data/AnitaBlake01GuiltyPleasures.clean.txt').read()) 
        
        # sentencify text
        sentences = re.split(r' *[.?!][\'")\]]* *[(\["]*', text)
        
        # cut out the first 15 proper sentences - dev and test
        sentences = sentences[17:]

        # wordify the sentences
        for i, sentence in enumerate(sentences):
            sentences[i] = re.findall(r"[\w']+|[.,!?;]", sentence)
        
        # train LM on corpus
        self.LM = LanguageModel(sentences)
        
       
    def permutationTester(self, sentence):
        
        # generate all order permutations of words in the sentence  
        orig = sentence        
        sentences = list(itertools.permutations(orig, len(orig)))

        # score each sentence and pick the best
        max = [self.LM.score(orig), orig]
        for sentence in sentences:
            
            score = self.LM.score(sentence)
            if score > max[0]:
                max = [score, sentence]
              
        print "\n Best Sentence:"      
        print max      
        return max[1]   
        
    
def main():
    mt = MT('%s/dictionary.json' % sys.argv[1])
    print mt.translate('%s/sentences.json' % sys.argv[1])

if __name__ == '__main__':
    main()
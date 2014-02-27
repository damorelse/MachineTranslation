 #!/usr/bin/python
# -*- coding: utf8 -*-

import copy
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

'''
Running strategy total:

Complete:
3pts  Language model for word selection
1pt   Verb reordering in dependent clauses
1pt   Verb reordering with model auxilliaries
1pt   Verb reordering with past and future participles
1pt   Rejoining separable prefixes
1pt   Adverb/verb reordering
1pt   Phrase interpolation

To do:
3pts  Verb tenses
1pt   Reflexives
1pt   "Zu" particle
1pt   "Not" particle
3pts  Subject/verb agreement
'''

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

VERB_PATTERN = re.compile('(..+)(?:e|st|t|en|te|test|tet|ten)')

class MT:

  
    def __init__(self, file, ngrams):
        
        self.dictionary = self.read_json(file)
        self.ngrams = self.read_json(ngrams)
        self.stemmer = SnowballStemmer("german") 
        self.tagger = POStagger() 
        self.trainLM()
        
        
    def translate(self, file):
        
        engSent = []        
        sentences = self.read_json(file)
        dev = self.tagger.tag(sentences['dev']) 
        print dev
        for line in dev:
            clauses = self.split_line(line)
            LL = []
            
            for words in clauses:
                words = self.reorder_dependent_clause(words)
                words = self.reorder_participles(words)
                words = self.reorder_modals(words)
                words = self.recombine_sep_prefixes(words)
                words = self.reorder_adverbs(words)
                words = self.interpolate_idioms(words)
                words = self.split_compounds(words)

                for w in words:
                    LL.append(self.lookup(w))
                    
            engSent.append(refine_word_choice(LL))
#            engSent.append(LL)

        
        return engSent
  
  
    def refine_word_choice(LL):
        
        output = [[]]
        
        for wordList in LL:
            numPrefix = len(output)
            numWords = len(wordList)
            
            if len(wordList) > 1:
                tmp = [None]*(numWords*numPrefix)
                
                for i in range(numWords):
                    for k in range(numPrefix):
                        tmp[i*numPrefix+k] = copy.copy(output[k])
                        
                output = tmp
            for i, word in enumerate(wordList):
                for itr in range(numPrefix):
                    output[i*numPrefix+itr].append(word)
                    
        bestScore = float("-inf")
        index = 0
        
        for i, sent in enumerate(output):
            currScore = self.LM.score(sent)
            if currScore > bestScore:
                bestScore = currScore
                index = i
                
        print bestScore
        
        return output[index]
    
        
    def reorder_dependent_clause(self, words):
        
        pairs = [x.split('_') for x in words]
        
        if re.match('V[VAM]FIN', pairs[-1][-1]):
            """
            Find where to put it.  Look for a pair of noun phrases or articles
            or prepositions and put it between them.  Note that we can't cross a
            conjuction, though.
            """ 
            first = -1
            second = -1
            conjunction = -1
            
            # First we assume that articles do not substitute for nouns
            for i, pair in enumerate(pairs[:-1]):
                if pair[-1] == 'PPER' or pair[-1] == 'PPOSS' or \
                    pair[-1] == 'NN' or pair[-1] == 'NE' or pair[-1] == 'PDS':
                    if first < 0:
                        first = i
                    elif second < 0:
                        second = i
                    else:
                        print ("Three subjects/objects in " + str(words))
                        break
                elif pair[-1] == 'KON' or pair[-1] == 'KOUS' or pair[-1] == 'KOKOM':
                    first = -1
                    second = -1
                    conjunction = i
                    
            if first >= 0 and second < 0:
                first = -1
                conjunction = -1
                first_is_article = False
                second_is_article = False
                
                # An article may be substituting for the second noun.  Try again
                for i, pair in enumerate(pairs[:-1]):
                    if pair[-1] == 'ART' or pair[-1] == 'CARD':
                        if first < 0:
                            first = i
                            first_is_article = True
                        elif second < 0:
                            second = i
                            second_is_article = True
                        else:
                            print ("Three subjects/objects in " + str(words))
                            break
                    elif pair[-1] == 'PPER' or pair[-1] == 'PPOSS' or \
                        pair[-1] == 'NN' or pair[-1] == 'NE' or pair[-1] == 'PDS':
                        if second < 0 and (first < 0 or first_is_article):
                            first = i
                            first_is_article = False
                        elif second < 0 or second_is_article:
                            second = i
                            second_is_article = False
                        else:
                            print ("Three subjects/objects in " + str(words))
                            break
                    elif pair[-1] == 'KON' or pair[-1] == 'KOUS' or pair[-1] == 'KOKOM':
                        first = -1
                        second = -1
                        conjunction = i
                        
                if second < 0:
                    # Nope. Maybe an article is subbing for the first noun.  Try again.
                    first = -1
                    conjunction = -1
                    first_is_article = False

                    # An article may be substituting for the second noun.  Try again
                    for i, pair in enumerate(pairs[:-1]):
                        if pair[-1] == 'ART' or pair[-1] == 'CARD':
                            if first < 0:
                                first = i
                            elif second < 0:
                                second = i
                                second_is_article = True
                            else:
                                print ("Three subjects/objects in " + str(words))
                                break
                        elif pair[-1] == 'PPER' or pair[-1] == 'PPOSS' or \
                            pair[-1] == 'NN' or pair[-1] == 'NE' or pair[-1] == 'PDS':
                            if first < 0:
                                first = i
                            elif second < 0 or second_is_article:
                                second = i
                                second_is_article = False
                            else:
                                print ("Three subjects/objects in " + str(words))
                                break
                        elif pair[-1] == 'KON' or pair[-1] == 'KOUS' or pair[-1] == 'KOKOM':
                            first = -1
                            second = -1
                            conjunction = i

            if first < 0 and conjunction < 0:
                # Move the verb into the first position
                words = words[-1:] + words[:-1]
            if first < 0:
                # Move the verb into the first position
                words = words[:conjunction + 1] + words[-1:] + words[conjunction + 1:-1]
            else:
                words = words[:first + 1] + words[-1:] + words[first + 1:-1]
                
        return words
        
        
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
    translations.
    """
    def interpolate_idioms(self, words):
 
        new = words
        changed = True
        
        while changed:
            changed = False
            
            for i in range(len(new) - 1):
                for j in range(len(new), i + 1, -1):
                    phrase = ' '.join([x.split('_')[0] for x in new[i:j]])
                    
                    if phrase in self.dictionary['idioms']:
                        new = new[:i] + [self.dictionary['idioms'][phrase] + '_IDIOM'] + new[j:]
                        changed = True
                        break
                            
                    if changed:
                        break
                        
                if changed:
                    break
            
        return new
    
    
    def lookup(self, word):
        
        parts = word.split('_')
        translation = [parts[0]]
        
        if parts[1] != 'IDIOM':
            if parts[0] in self.dictionary['words']:
                translation = self.dictionary['words'][parts[0]]
            elif parts[0].lower() in self.dictionary['words']:
                translation = self.dictionary['words'][parts[0].lower()]
            elif parts[1].startswith('V'):
                translation = self.dictionary['words'][verb_stem(parts[0])]
                
        if parts[1].startswith('V'):
            translation = set_tense(translation, get_tense(parts[0], parts[1]))

        return translation

    def verb_stem(self, verb):

        stem = verb
        
        m = VERB_PATTERN.match(verb)
        
        if m:
            stem = m.group(1)
        else:
            # Must be irregular present or past (1S or 3S), but how did we
            # not already find it in the dictionary?
            raise("Didn't find %s in the dictionary" % verb)
        
        return stem

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
        
        
    def reorder_participles(self, words):
 
        # find clause that ends with VVPP, VAPP, or VMPP
        new_words = words
        check = ["VVPP", "VAPP", "VMPP"]
        for c in check:
            if c in words[-1]:
                
                # find the preceding VA*
                for i, word in enumerate(words[:-1]):
                    if "VA" in word:
                
                        # move last word into pos after prec. VA*
                        new_words = words[:i+1]
                        new_words.append(words[-1])
                        new_words.extend(words[i+1:-1])
                        break
        
        return new_words
        
        
    def reorder_modals(self, words):
 
        # find clause that ends with VVPP, VAPP, or VMPP
        new_words = words
        check = ["VVINF", "VAINF", "VMINF"]
        for c in check:
            if c in words[-1]:
                
                # find the preceding VM*
                for i, word in enumerate(words[:-1]):
                    if "VM" in word:
                
                        # move last word into pos after prec. VA*
                        new_words = words[:i+1]
                        new_words.append(words[-1])
                        new_words.extend(words[i+1:-1])
                        break
        
        return new_words
       

    def recombine_sep_prefixes(self, words):
        
        # find clause ends with PTKVZ
        new_words = words
        if "_PTKVZ" in words[-1]:
                # find the preceding VVFIN
                for i, word in enumerate(words[:-1]):
                    if "_VVFIN" in word:
            
                        # move the last word into pos after prec. VVFIN
                        new_words = words[:-1]
                        new_words[i] = words[i].split('_')[0] + ' ' + words[-1].split('_')[0] + '_VVFIN'
#                        new_words = words[:i + 1]
#                        new_words.append(words[-1])
#                        new_words.extend(words[i + 1:-1])

                        break
        
        
        return new_words

            
    def reorder_adverbs(self, words):   
        
        # find any ADV that follows any V*
        new_words = words
        for i, word in enumerate(words):
            if "ADV" in word:
                for w in words[:i]:
                    if "_V" in w:
                            
                        # find the preceding VV*
                        for j, wurd in enumerate(words[:i]):
                            if "VV" in wurd: 

                                # move the ADV into before prec. VV*
                                new_words = words[:j-1]
                                new_words.append(words[i])
                                new_words.extend(words[j-1:i])
                                new_words.extend(words[i+1:])
                                break
                        break            

        return new_words
        
        
    def trainLM(self):
        
        # open clean text and join all lines
        text = ''.join(open(os.path.join(os.path.dirname(__file__), '..', 'data', 'AnitaBlake01GuiltyPleasures.clean.txt')).read()) 
        
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
              
        print ("\n Best Sentence:")
        print (max)
        return (max[1])
    '''
    def score(self, sentence):
        score = 0.0 
        toks = ['', '', '']
        for curr in sentence:
            curr = curr.split(" ")
            toks.extend(curr)
            for i in range(len(curr)):
                toks.pop(0)
                if " ".join(toks[:3]) in self.ngrams["trigram_probabilities"]:
                    score += self.ngrams["trigram_probabilities"][" ".join(toks[:3])]
                elif " ".join(toks[1:3]) in self.ngrams["bigram_probabilities"]:
                    score += self.ngrams["bigram_probabilities"][" ".join(toks[1:3])]
                elif toks[2] in self.ngrams["unigram_probabilities"]:
                    score += self.ngrams["unigram_probabilities"][toks[2]]
                else:
                    score += 0.0 #UNK?
        toks.append("")
        toks.pop(0)
        if " ".join(toks[:3]) in self.ngrams["trigram_probabilities"]:
            score += self.ngrams["trigram_probabilities"][" ".join(toks[:3])]
        elif " ".join(toks[1:3]) in self.ngrams["bigram_probabilities"]:
            score += self.ngrams["bigram_probabilities"][" ".join(toks[1:3])]
        else:
            score += 0.0 #UNK?
        toks.append("")
        toks.pop(0)
        if " ".join(toks[:3]) in self.ngrams["trigram_probabilities"]:
            score += self.ngrams["trigram_probabilities"][" ".join(toks[:3])]
        else:
            score += 0.0 #UNK?
        return score
    '''
    
def main():
    mt = MT('%s/dictionary.json' % sys.argv[1], '%s/ngrams.json' % sys.argv[1])
    print (mt.translate('%s/sentences.json' % sys.argv[1]))

if __name__ == '__main__':
    main()
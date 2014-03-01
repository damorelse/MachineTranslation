#!/usr/bin/python
# -*- coding: utf8 -*-

import copy
import codecs
import json
import re
import sys
import os.path
import os
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
1pt   Phrase interpolation
3pts  Verb tenses

To do:
1pt   Adverb/verb reordering
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

REGULAR_PATTERN = re.compile(unicode('^(..+?)((et)?(e|st|t|en|(?=<e)n))?$'))

class MT:

  
    def __init__(self, file, ngrams):
        
        self.dictionary = self.read_json(file)
        self.ngrams = self.read_json(ngrams)
        self.stemmer = SnowballStemmer("german") 
        self.tagger = POStagger() 
        self.trainOnAllLM()
        
        
    def translate(self, file):
        
        translated_sentences = []        
        sentences = self.read_json(file)
        dev = self.tagger.tag(sentences['dev']) 
        
#        print dev
        for line in dev:
            clauses = self.split_line(line)
            translated_clauses = []
            
            for clause in clauses:
                LL = []
                clause = self.reorder_dependent_clause(clause)
                clause = self.reorder_obj_subj(clause)
                clause = self.reorder_participles(clause)
                clause = self.reorder_modals(clause)
                clause = self.recombine_sep_prefixes(clause)
#                words = self.reorder_adverbs(words)
                clause = self.interpolate_idioms(clause)
                clause = self.split_compounds(clause)

                for word in clause:
                    LL.append(self.lookup(word))
#                    print LL[-1]

                translated_clauses.append(self.refine_word_choice(LL))
                    
            translated_sentences.append(translated_clauses)
#            engSent.append(LL)

        translation = []
        for sentence in translated_sentences:
            trans = ""
            for clause in sentence:
                clauz = ""
                for word in clause:
                    clauz += " "+word
                trans += ", "+clauz  
            translation.append(trans)      

        return translation
        #return translated_sentences
  
  
    def refine_word_choice(self, LL):
        
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
            changed = False
            
            """
            First look for an auxilliary verb to which to attach our end verb.
            """
#            for i in range(len(pairs) - 1, -1, -1):
#                if '_VAFIN' in pairs[i][-1]:
#                    words = words[:i + 1] + [words[-1]] + words[i + 1:-1]
#                    
#                    changed = True
#                    
#                    break
#                elif '_KON' in pairs[i][-1]:
#                    # Give up at the first conjunction
#                    break
            
            if not changed:
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
                    if pair[-1] == 'PPER' or pair[-1] == 'PPOSS' or pair[-1] == 'PWS' or \
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
                        elif pair[-1] == 'PPER' or pair[-1] == 'PPOSS' or pair[-1] == 'PWS' or \
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
                            elif pair[-1] == 'PPER' or pair[-1] == 'PPOSS' or pair[-1] == 'PWS' or \
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
                
        if parts[1].startswith('V'):
            translation = [self.from_tense(w, self.get_tense(parts[0], parts[1])) for w in translation]

        return translation

    def verb_stem(self, verb):

        stem = verb
        
        m = REGULAR_PATTERN.match(verb)
        
        if m:
            stem = m.group(1)
        else:
            # Must be irregular present or past (1S or 3S), but how did we
            # not already find it in the dictionary?
            raise Exception("Didn't find %s in the dictionary" % verb)
        
        return stem
    
    def from_tense(self, verb, tense):
        words = verb.split(' ')
        rest = []
        
        if len(words) > 1:
            verb = words[0]
            rest = words[1:]
            
        new = verb
        
        if verb in self.dictionary['verbs'] and len(self.dictionary['verbs'][verb]) == 3 and tense == '1':
            new = self.dictionary['verbs'][verb][0][0]
        elif verb in self.dictionary['verbs'] and len(self.dictionary['verbs'][verb]) == 3 and tense == '2':
            new = self.dictionary['verbs'][verb][0][1]
        elif verb in self.dictionary['verbs'] and len(self.dictionary['verbs'][verb]) == 3 and tense == '3':
            new = self.dictionary['verbs'][verb][0][2]
        elif verb in self.dictionary['verbs'] and len(self.dictionary['verbs'][verb]) == 3 and tense[-1] == '+':
            new = self.dictionary['verbs'][verb][0][3]
        elif verb in self.dictionary['verbs'] and tense == 'PP':
            new = self.dictionary['verbs'][verb][-1]
        elif verb in self.dictionary['verbs'] and type(self.dictionary['verbs'][verb][-2]) == list and tense == '1P':
            new = self.dictionary['verbs'][verb][-2][0]
        elif verb in self.dictionary['verbs'] and type(self.dictionary['verbs'][verb][-2]) == list and tense == '2P':
            new = self.dictionary['verbs'][verb][-2][1]
        elif verb in self.dictionary['verbs'] and type(self.dictionary['verbs'][verb][-2]) == list and tense == '3P':
            new = self.dictionary['verbs'][verb][-2][2]
        elif verb in self.dictionary['verbs'] and type(self.dictionary['verbs'][verb][-2]) == list and tense[-2:] == '+P':
            new = self.dictionary['verbs'][verb][-2][3]
        elif verb in self.dictionary['verbs'] and tense[-1] == 'P':
            new = self.dictionary['verbs'][verb][-2]
        elif tense[-1] == 'P' and verb[-1] == 'e':
            new = verb + 'd'
        elif tense[-1] == 'P' and re.match('.*[^aeiou][aeiou][b-df-hj-np-tvwyz]$', verb):
            new = verb + verb[-1] + 'ed'
        elif tense[-1] == 'P':
            new = verb + 'ed'
#        elif tense == 'I' and verb[-1] == 'e':
#            new = verb[:-1] + 'ing'
#        elif tense == 'I':
#            new = verb + 'ing'
        elif tense == '2' and verb[-1] == 'o':
            new = verb + 'es'
        elif tense == '2':
            new = verb + 's'
        
        return ' '.join([new] + rest)
    
    def get_tense(self, verb, tag):
        words = verb.split(' ')
        
        if len(words) > 1:
            verb = words[0]
            
        tense = None
        
        if tag.endswith('PP'):
            tense = 'P'
        elif tag.endswith('INF'):
            tense = 'I'
        elif verb in self.dictionary['tenses']:
            tense = self.dictionary['tenses'][verb]
            
            if tense == 'P':
                tense = '1P' #1st or 3rd, we don't care which
            elif tense == 'I':
                tense = '1+' #1st or 3rd, we don't care which
        else:
            m = REGULAR_PATTERN.match(verb)
            
            if m and m.group(1) in self.dictionary['tenses']:
                # If it's in the dictionary, it must be strong simple past
                tense = self.dictionary['tenses'][m.group(1)]
                
                if tense == 'P' and m.group(2) == 't':
                    tense = '2+P'
                elif tense == 'P' and m.group(2) == 'st':
                    tense = '2P'
                elif tense == 'P' and (m.group(2) == 'en' or m.group(2) == 'n'):
                    tense = '1+P' #1st or 3rd, we don't care which
            elif m:
                # And now we're left with present or weak simple past
                if m.group(2) == 'e':
                    tense = '1'
                elif m.group(2) == 't':
                    # This could also be 2nd plural, in which case we'll get it wrong
                    tense = '3'
                elif m.group(2) == 'st':
                    tense = '2'
                elif m.group(2) == 'en':
                    tense = '1+' #1st or 3rd, we don't care which
                elif m.group(2) == 'ete':
                    tense = '1P'
                elif m.group(2) == 'etet':
                    # This could also be 2nd plural, in which case we'll get it wrong for weak verbs!
                    tense = '3P' 
                elif m.group(2) == 'etest':
                    tense = '2P'
                elif m.group(2) == 'eten':
                    tense = '1+P' #1st or 3rd, we don't care which
                else:
                    raise Exception('unexpected verb ending: %s/%s' % (m.group(1), m.group(2)))
            else:
                raise Exception("verb doesn't match pattern: %s/%s" % (verb, m.group(1)))
            
        return tense

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
        check = ["_VVINF", "_VAINF", "_VMINF"]
        
        for c in check:
            if c in words[-1]:
                
                # find the preceding VM*
                for i, word in enumerate(words[:-1]):
                    if "_VM" in word:
                
                        # move last word into pos after prec. VA*
                        new_words = words[:i+1]
                        new_words.append(words[-1])
                        new_words.extend(words[i+1:-1])
                        break
        
        return new_words
       

    def reorder_obj_subj(self, words):
 
        new_words = words

        # find first verb
        for i, word in enumerate(words[:-2]):
            if '_V' in word:
                # We can only be certain about ich, du, and er.
                if words[i + 1] == 'ich_PPER' or words[i + 1] == 'du_PPER' or words[i + 1] == 'er_PPER':
                    new_words = [words[i + 1]] + [words[i]] + words[:i] + words[i + 2:]
                    
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
        
    
    def trainOnAllLM(self):
        
        # open clean text files for each book and join all lines
        text = ""
        books = ["AnitaBlake01GuiltyPleasures.clean.txt",
        "AnitaBlake02LaughingCorpse.really.clean.txt",
        "AnitaBlake03CircusOfTheDamned.really.clean.tx",
        "AnitaBlake04LunaticCafe.really.clean.txt",
        "AnitaBlake05BloodyBones.really.clean.txt",
        "AnitaBlake06TheKillingDance.really.clean.txt",
        "AnitaBlake07BurntOfferings.really.clean.txt",
        "AnitaBlake08BlueMoon.really.clean.txt",
        "AnitaBlake09ObsidianButterfly.really.clean.txt",
        "AnitaBlake10NarcissusInChains.really.clean.txt",
        "AnitaBlake11CeruleanSins.really.clean.txt",
        "AnitaBlake12IncubusDreams.really.clean.txt",
        "AnitaBlake16BloodNoir.really.clean.txt",
        "AnitaBlake17SkinTrade.really.clean.txt",
        "AnitaBlake18Flirt.really.clean.txt"]
        
        for book in books:
            text += ''.join(open(os.path.join(os.path.dirname(__file__), '..', 'data', book)).read()) 
        
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

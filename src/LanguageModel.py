import math
import collections

class LanguageModel:


  def __init__(self, corpus):
    
    self.unigramCounts = collections.defaultdict(lambda: 0)
    self.bigramCounts = collections.defaultdict(lambda: 0)
    self.trigramCounts = collections.defaultdict(lambda: 0)
    self.total = 0
    self.cont = {}
    with open("data\contractions.txt") as f:
      content = f.readlines()
      for line in content:
        line = line.rstrip()
        self.cont[line[:line.find("\t")]] = line[line.find("\t")+1:]
    self.train(corpus)

  def train(self, corpus):
      
    """ Takes a corpus and trains a language model. """  
    
    
    for sentence in corpus: 
      toks = ['', '', ''] 
      self.unigramCounts[toks[2]] =  self.unigramCounts[toks[2]] + 4
      self.bigramCounts[" ".join(toks[1:3])] = self.bigramCounts[" ".join(toks[1:3])] + 2
      for word in sentence:  
          curr = [word]
          if word in self.cont.keys():
            curr = self.cont[word].split(" ")
          toks.extend(curr)
          for i in range(len(curr)):
              toks.pop(0) 
              self.unigramCounts[toks[2]] = self.unigramCounts[toks[2]] + 1
              self.total += 1
              self.bigramCounts[" ".join(toks[1:3])] = self.bigramCounts[" ".join(toks[1:3])] + 1
              self.trigramCounts[" ".join(toks[:3])] = self.trigramCounts[" ".join(toks[:3])] + 1
      toks.append("")
      toks.pop(0)
      self.bigramCounts[" ".join(toks[1:3])] = self.bigramCounts[" ".join(toks[1:3])] + 1
      self.trigramCounts[" ".join(toks[:3])] = self.trigramCounts[" ".join(toks[:3])] + 1
      toks.append("")
      toks.pop(0)
      self.trigramCounts[" ".join(toks[:3])] = self.trigramCounts[" ".join(toks[:3])] + 1


  '''
  def score(self, sentence):
      
    """ Takes a list of strings as argument and returns the log-probability of the 
        sentence using the language model above. 
    """

    V = len(self.unigramCounts)
    score = 0.0 
    prev_word = ""
    prev2_word = ""
    for token in sentence:
         
          trigram_count = self.trigramCounts[(prev2_word,prev_word,token)]      
          bigram_count = self.bigramCounts[(prev_word,token)]
          unigram_count = self.unigramCounts[prev_word] 
          
          if trigram_count > 0:
              score += math.log(trigram_count)
              score -= math.log(bigram_count)
          elif bigram_count > 0: 
              score += math.log(bigram_count) #math.log(0.4)
              score -= math.log(unigram_count)
          else:
              score += math.log(0.4) + math.log(unigram_count + 1)
              score -= math.log(self.total + V)   
                 
          prev2_word = prev_word
          prev_word = token 
    return score
  '''
  def score(self, sentence):
    score = 0.0 
    V = len(self.unigramCounts)
    toks = ['', '', '']
    for curr in sentence:
        curr = curr.split(" ")
        toks.extend(curr)
        for i in range(len(curr)):
            toks.pop(0)
            if " ".join(toks[:3]) in self.trigramCounts:
                score += math.log(self.trigramCounts[" ".join(toks[:3])])
                score -= math.log(self.bigramCounts[" ".join(toks[1:3])])
            elif " ".join(toks[1:3]) in self.bigramCounts:
                score += math.log(self.bigramCounts[" ".join(toks[1:3])])
                score -= math.log(self.unigramCounts[toks[2]])
            elif toks[2] in self.unigramCounts:
                score += math.log(self.unigramCounts[toks[2]] + 1)
                score -= (self.total + V)
            else:
                score += 0.0 #UNK?
    toks.append("")
    toks.pop(0)
    if " ".join(toks[:3]) in self.trigramCounts:
        score += math.log(self.trigramCounts[" ".join(toks[:3])])
        score -= math.log(self.bigramCounts[" ".join(toks[1:3])])
    elif " ".join(toks[1:3]) in self.bigramCounts:
       score += math.log(self.bigramCounts[" ".join(toks[1:3])])
       score -= math.log(self.unigramCounts[toks[2]])
    else:
        score += 0.0 #UNK?
    toks.append("")
    toks.pop(0)
    if " ".join(toks[:3]) in self.trigramCounts:
      score += math.log(self.trigramCounts[" ".join(toks[:3])])
      score -= math.log(self.bigramCounts[" ".join(toks[1:3])])
    else:
        score += 0.0 #UNK?
    return score

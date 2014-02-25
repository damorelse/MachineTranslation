import math, collections

class LanguageModel:


  def __init__(self, corpus):
    
    self.unigramCounts = collections.defaultdict(lambda: 0)
    self.bigramCounts = collections.defaultdict(lambda: 0)
    self.trigramCounts = collections.defaultdict(lambda: 0)
    self.total = 0
    self.train(corpus)
    

  def train(self, corpus):
      
    """ Takes a corpus and trains a language model. """  
    
    prev_word = ""
    prev2_word = ""
    for sentence in corpus:  
        
      for word in sentence:      

        token = word
        self.unigramCounts[token] = self.unigramCounts[token] + 1
        self.total += 1
        if prev_word != "":
            self.bigramCounts[(prev_word, token)] = self.bigramCounts[(prev_word,token)] + 1
        if prev2_word != "":
            self.trigramCounts[(prev2_word, prev_word, token)] = self.trigramCounts[(prev2_word, prev_word, token)] + 1    
        prev2_word = prev_word
        prev_word = token


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


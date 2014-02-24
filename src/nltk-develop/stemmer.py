import nltk
from nltk.stem.snowball import SnowballStemmer
import re

# init stemmer
stemmer = SnowballStemmer("german")

# stem sentence
sentence = "Gehen Sie geradeaus! Entschuldigen Sie bitte! Darf ich mal vorbei? Einen Augenblick, bitte."
wordList = re.sub("[^\w]", " ", sentence).split()
for word in wordList:
    print stemmer.stem(word)


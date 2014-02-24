#-*- coding: utf8 -*-

import os, glob, codecs

def installStanfordTag():
    if not os.path.exists('stanford-postagger-full-2013-06-20'):
        os.system('wget http://nlp.stanford.edu/software/stanford-postagger-full-2013-06-20.zip')
        os.system('unzip stanford-postagger-full-2013-06-20.zip')
    return

def tag(infile):
    cmd = "./stanford-postagger.sh "+models[m]+" "+infile
    tagout = os.popen(cmd).readlines()
    return [i.strip() for i in tagout]

def taglinebyline(sents):
    tagged = []
    for ss in sents:
        os.popen("echo '''"+ss+"''' > stanfordtemp.txt")
        tagged.append(tag('stanfordtemp.txt')[0])
    return tagged

installStanfordTag()
stagdir = './stanford-postagger-full-2013-06-20/'
models = {'fast':'models/german-fast.tagger',
          'dewac':'models/german-dewac.tagger',
          'hgc':'models/german-hgc.tagger'}
os.chdir(stagdir)
#print os.getcwd()


m = 'fast' # It's best to use the fast german tagger if your data is small.

sentences = ["Willie McCoy war schon vor seinem Tod ein Blödmann gewesen.",
                "Dass er nun tot war, änderte daran nichts.",
                "Er saß mir gegenüber in einem grell karierten Sakko.",
                "Seine Polyesterhosen war hellgrün.",
                "Das kurze schwarze Haar hatte er sich aus dem dünnen dreieckigen Gesicht nach hinten geklatscht.",
                "Er hatte mich schon immer ein wenig an eine Gestalt aus einem Gangsterfim erinnert.",
                "Die Sorte, die Informationen verkauft, Aufträge ausführt und entbehrlich ist.",
                "Jetzt, wo Willie ein Vampir war, war die Sache mit der Entbehrlichkeit natürlich nicht mehr von Bedeutung.",
                "Aber er verkaufte noch immer Informationen und machte Botengänge.",
                "Nein, der Tod hatte ihn nicht besonders verändert."]

tagged_sents = taglinebyline(sentences) # Call the stanford tagger

for sent in tagged_sents:
    print "\n"
    print sent
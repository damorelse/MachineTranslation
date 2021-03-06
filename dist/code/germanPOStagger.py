#-*- coding: utf8 -*-

import os
import glob
import codecs
import tempfile
import subprocess
import platform

'''
Tags text using STTS: http://www.deutschestextarchiv.de/doku/pos
'''
class POStagger:
    
    def __init__(self):
        
        # set model and dirs
        self.m = 'models/german-fast.tagger'
        self.stagdir = os.path.join(os.path.dirname(__file__), 'dltk', 'stanford-postagger-full-2013-06-20')
        
    def tagit(self, infile):
        
        # set command
        if platform.system() == 'Windows':
            cmd = 'stanford-postagger.bat models\\german-fast.tagger ' + infile
        else:
            cmd = "./stanford-postagger.sh " + self.m + " " + infile

        # remember current dir and then set to stagdir
        currentDir = os.getcwd()
        os.chdir(self.stagdir)

        # get output
        tagout = os.popen(cmd).readlines() #GINA: issues in windows

        # return to orig directory and return ouput
        os.chdir(currentDir)
        return [i.strip() for i in tagout] 


    # function to call from outside class, can handle multiple sentences   
    def tag(self, sentences):
        
        file = self.write_temp_file(sentences)
        tagged = [unicode(x, encoding='utf8') for x in self.tagit(file)]
        #os.unlink(file) #GINA: issues in windows
        return tagged
    
    @staticmethod
    def write_temp_file(sentences):
        
        f, path = tempfile.mkstemp(text=True)

        with codecs.open(path, mode='w', encoding='utf8') as f:
            for s in sentences:
                f.write(s)
                f.write('\n')
        f.close()
        return path
        
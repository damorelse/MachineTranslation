#-*- coding: utf8 -*-

import os, glob, codecs


class POStagger:
    
    def __init__(self):
        
        # set model and dirs
        self.m = 'models/german-fast.tagger'
        self.stagdir = 'dltk/stanford-postagger-full-2013-06-20/'
        
        
    def tagit(self, infile):
        
        # set command
        cmd = "./stanford-postagger.sh " + self.m + " " + infile
        
        # remember current dir and then set to stagdir
        currentDir = os.getcwd()
        os.chdir(self.stagdir)
        
        # get output
        tagout = os.popen(cmd).readlines()
        
        # return to orig directory and return ouput
        os.chdir(currentDir)
        return [i.strip() for i in tagout] 


    # function to call from outside clas, can handle multiple sentences   
    def tag(self, sentences):
        
        tagged = []
        for ss in sentences:
            tagged.append(self.tagit('stanfordtemp.txt')[0])
        return tagged
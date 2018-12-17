import sys
import re
from porter2stemmer import Porter2Stemmer
from collections import defaultdict
from array import array
import gc

porter=Porter2Stemmer()

class CreateIndex:

    def __init__(self):
        self.index=''

    def getextra_Words(self):
        '''get extra_Words from the extra_Words file'''
        f=open(self.extra_WordsFile, 'r', encoding="utf-8")
        extra_Words=[text_line.rstrip() for text_line in f]
        self.sw=dict.fromkeys(extra_Words)
        f.close()


    def getTerms(self, text_line):
        '''given a stream of text, get the terms from the text'''
        text_text_line=text_line.lower()
        text_line=re.sub(r'[^a-z0-9 ]',' ',text_line)
        text_line=text_line.split()
        text_line=[x for x in text_line if x not in self.sw]
        string = ''
        for word in text_line :
            string += porter.stem(word) + ", "

        #string += (porter.stem(word) for word in text_line)
        return string


    def get_text(self):

        doc=[]
        for text_line in self.collFile:
            if text_line=='</page>\n':
                break
            doc.append(text_line)
        curPage=''.join(doc)
        pageid=re.search('<id>(.*?)</id>', curPage, re.DOTALL)
        pagetitle=re.search('<title>(.*?)</title>', curPage, re.DOTALL)
        pagetext=re.search('<text>(.*?)</text>', curPage, re.DOTALL)
        if pageid==None or pagetitle==None or pagetext==None:
            return {}

        d={}
        d['id']=pageid.group(1)
        d['title']=pagetitle.group(1)
        d['text']=pagetext.group(1)
        return d


    def Write(self):
        '''write the inverted index to the file'''
        f=open(self.indexFile, 'a')

        f.write(self.index)
        f.write("\n")

        f.close()


    def options(self):
        '''get the parameters extra_Words file, collection file, and the output index file'''
        param=sys.argv
        self.extra_WordsFile=param[1]
        self.collectionFile=param[2]
        self.indexFile=param[3]


    def createIndex(self):
        '''main of the program, creates the index'''
        self.options()
        self.collFile=open(self.collectionFile,'r', encoding="utf-8")
        self.getextra_Words()

        gc.disable()

        pagedict={}



        pagedict=self.get_text()

        #main loop creating the index
        while pagedict != {}:
            titles = pagedict['title']
            text = pagedict['text']

            pageid=int(pagedict['id'])
            terms=self.getTerms(text)

            self.index = 'Page Id {}'.format(pageid)  + '           ' + 'Title '+   titles  + '            ' + 'Terms   '    + terms            + '/n'
            #build the index for the current page


            pagedict=self.get_text()

            self.Write()
        gc.enable()




if __name__=="__main__":
    c=CreateIndex()
    c.createIndex()

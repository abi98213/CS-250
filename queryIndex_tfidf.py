# to run: 
# Provide stopwords.xml, final-weighted-index.xml and indextitle.xml in a folder named files in the source directory.

import sys
import re
from porter2stemmer import Porter2Stemmer as ps
from collections import defaultdict as dd
from array import array
import functools
import gc
import copy

# this instance of Porter2Stemmer will be used to trim adverbs 
# and adjectives and conjuction terms from a word  
# this library can be installed by cmd/terminal> pip install porter2stemmer
_port = ps()


class Query_Index:

    def __init__(self):
        self._index = {}
        self.title_index = {}
        self.term_freq = {}      #term frequencies
        self.inv_doc_freq = {}    #inverse document frequencies


        self.getParams()
        self.readIndex()  
        self.getStopwords()


    def intersectLists(self,lists):
        if len(lists) == 0:
            return []
        #start intersecting from the smaller list
        lists.sort(key = len)
        return list(functools.reduce(lambda x,y: set(x)&set(y),lists))
        
    
    def getStopwords(self):
        foo = open(self.stopwordsFile, 'r')
        stopwords = [line.rstrip() for line in foo]
        self.skipwords = dict.fromkeys(stopwords)
        foo.close()
        

    def getTerms(self, line):
        line = line.lower()
        line = re.sub(r'[^a-z0-9 ]',' ',line) #put spaces instead of non-alphanumeric characters
        line = line.split()
        line = [x for x in line if x not in self.skipwords]
        line = [ _port.stem(word) for word in line]
        return line
        
    
    def getPostings(self, terms):
        #all terms in the list are guaranteed to be in the index
        return [ self._index[term] for term in terms ]
    
    
    def getDocsFromPostings(self, postings):
        #no empty list in postings
        return [ [x[0] for x in p] for p in postings ]


    def readIndex(self):
        #read main index
        f = open(self.indexFile, 'r', encoding = 'utf-8');
        #first read the number of documents
        self.numDocuments = int(f.readline().rstrip())
        print('Reading the index File')
        for line in f:
            line = line.rstrip()
            term, postings, tf, idf  =  line.split('|')    #term = 'termID', postings = 'docID1:pos1,pos2;docID2:pos1,pos2'
            postings = postings.split(';')        #postings = ['docId1:pos1,pos2','docID2:pos1,pos2']
            postings = [x.split(':') for x in postings] #postings = [['docId1', 'pos1,pos2'], ['docID2', 'pos1,pos2']]
            postings = [ [int(x[0]), list(map(int, x[1].split(',')))] for x in postings ]   #final postings list  
            self._index[term] = postings
            #read term frequencies
            tf = tf.split(',')
            self.term_freq[term]  =  list(map(float, tf))
            #read inverse document frequency
            self.inv_doc_freq[term]  = float(idf)
        f.close()
        
        #read title index
        print('Reading the index-Title File')
        f  =  open(self.titleIndexFile, 'r')
        for line in f:
            pageid, title  =  line.rstrip().split('|')
            self.title_index[pageid] = title
        f.close()
        
     
    def dotProduct(self, vec1, vec2):
        if len(vec1) != len(vec2):
            return 0
        return sum([ x*y for x,y in zip(vec1,vec2) ])
            
        
    def rankDocuments(self, terms, docs):
        #term at a time evaluation
        docVectors = dd(lambda: [0]*len(terms))
        queryVector = [0]*len(terms)
        for termIndex, term in enumerate(terms):
            if term not in self._index:
                continue
            queryVector[termIndex] = self.inv_doc_freq[term]
            for docIndex, (doc, postings) in enumerate(self._index[term]):
                if doc in docs:
                    docVectors[doc] = self.term_freq[term][docIndex]    
        #calculate the score of each doc
        docScores = [ [self.dotProduct([docVectors.get(doc)], queryVector), doc] for doc in docVectors ]
        docScores.sort(reverse = True)
        resultDocs = [x[1] for x in docScores]
        #print document titles instead if document id's
        resultDocs = [ self.title_index.get(str(x)) for x in resultDocs ]
        if len(resultDocs) > 0:
            return resultDocs
        else:
            return ['Term Not found. Try again with a different Search']


    def queryType(self,q):
        if '"' in q:
            return 'paraphrase_query'
        elif len(q.split()) > 1:
            return 'free_text_query'
        else:
            return 'one_word_query'


    def one_word_query(self,q):
        '''One Word Query'''
        originalQuery = q
        q = self.getTerms(q)
        if len(q) == 0:
            return ['Oops..!! Please rephrase your query and try again']
        elif len(q)>1:
            return self.free_text_query(originalQuery)        
        #q contains only 1 term 
        term = q[0]
        if term not in self._index:
            return ['Term Not found. Try again with a different Search']
        else:
            postings = self._index[term]
            docs = [x[0] for x in postings]
            return self.rankDocuments(q, docs)
          

    def free_text_query(self,q):
        """Free Text Query"""
        q = self.getTerms(q)
        if len(q) == 0:
            return ['Oops..!! Please rephrase your query and try again']
        
        li = set()
        for term in q:
            try:
                postings = self._index[term]
                docs = [x[0] for x in postings]
                li = li|set(docs)
            except:
                return ['Term Not found. Try again with a different Search']
        
        li = list(li)
        return self.rankDocuments(q, li)


    def paraphrase_query(self,q):
        '''Phrase Query'''
        originalQuery = q
        q = self.getTerms(q)
        if len(q) == 0:
            return ['Oops..!! Please rephrase your query and try again']
        elif len(q) == 1:
            return self.one_word_query(originalQuery)
        phraseDocs = self.pqDocs(q)
        return self.rankDocuments(q, phraseDocs)
        
        
    def pqDocs(self, q):
        """ here q is not the query, it is the list of terms """
        phraseDocs = []
        length = len(q)
        #first find matching docs
        for term in q:
            if term not in self._index:
                #if a term doesn't appear in the index
                #there can't be any document maching it
                return []
        
        postings = self.getPostings(q)    #all the terms in q are in the index
        docs = self.getDocsFromPostings(postings)
        #docs are the documents that contain every term in the query
        docs = self.intersectLists(docs)
        #postings are the postings list of the terms in the documents docs only
        for i in range(len(postings)):
            postings[i] = [x for x in postings[i] if x[0] in docs]
        
        #check whether the term ordering in the docs is like in the phrase query
        
        #subtract i from the ith terms location in the docs
        postings = copy.deepcopy(postings)    #this is important since we are going to modify the postings list
        
        for i in range(len(postings)):
            for j in range(len(postings[i])):
                postings[i][j][1] = [x-i for x in postings[i][j][1]]
        
        #intersect the locations
        result = []
        for i in range(len(postings[0])):
            li = self.intersectLists( [x[i][1] for x in postings] )
            if li == []:
                continue
            else:
                result.append(postings[0][i][0])    #append the docid to the result
        
        return result

        
    def getParams(self):
        self.stopwordsFile = 'files/stopwords.xml'
        self.indexFile = 'files/final-weighted-output.xml'
        self.titleIndexFile = 'files/indextitle.xml'


    def queryIndex(self, query): 
        qt = self.queryType(query)
        if qt == 'one_word_query':
            return self.one_word_query(query)
        elif qt == 'free_text_query':
            return self.free_text_query(query)
        elif qt == 'paraphrase_query':
            return self.paraphrase_query(query)


if __name__ == '__main__':
    c = Query_Index()
    while(True):
        query = input("Enter a Search String: ")
        if(query == ''):
            break
        result = c.queryIndex(query)
        print(result[:10])

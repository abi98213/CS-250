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
        self.index_ = {}

    # Reads the contents of skipwords file and inititalizes a dictionary with words in the skipwords file as 
    # the keys of the dictionary. Currently they all map to none.
    # here is how it works
    # words = ['a','b','c'] --dict.fromkeys(words)--> { 'a' : None, 'b' : None, 'c' : None }   
    def getSkipWords(self):
        foo = open(self.skipwordsFile, 'r', encoding="utf-8")
        words = [line.rstrip() for line in foo]
        self.skipwords = dict.fromkeys(words)
        foo.close()

    #   Gets the command line parameters in the order 
    #   1 = skipwords file
    #   2 = Collections file 
    def getParameters(self):
        parameter=sys.argv
        if len(parameter) < 2:
            print("Not enough Arguments were given\nSyntax: python3 query_index.py [skip_words_file] [index_file]")
        self.skipwordsFile=parameter[1]
        self.indexFile=parameter[2]

    # Given a stream of text i.e. line, get stemmed terms from a text i.e. believ from believable, believing, believe
    # return the list of stemmed words from the line
    def getTerms(self, line):
        line = line.lower()
        line = re.sub(r'[^a-z0-9 ]',' ',line) #put spaces instead of non-alphanumeric characters
        line = line.split()
        line = [x for x in line if x not in self.skipwords]  #eliminate the stopwords
        line = [ _port.stem(word) for word in line]
        return line

    def intersectLists(self,lists):
        if len(lists)==0:
            return []
        #start intersecting from the smaller list
        lists.sort(key=len)
        return list(functools.reduce(lambda x,y: set(x)&set(y),lists))
     
    def get_Postings(self, terms):
        #all terms in the list are guaranteed to be in the index
        return [ self.index_[term] for term in terms ]
    
    
    def getDocsFromPostings(self, postings):
        #no empty list in postings
        return [ [x[0] for x in p] for p in postings ]

    def readindex(self):
        foo = open(self.indexFile, 'r', encoding='utf-8');
        for line in foo:
            line = line.rstrip()
            term, postings = line.split('|')    #term='termID', postings='docID1:pos1,pos2;docID2:pos1,pos2'
            postings = postings.split(';')        #postings=['docId1:pos1,pos2','docID2:pos1,pos2']
            postings = [x.split(':') for x in postings] #postings=[['docId1', 'pos1,pos2'], ['docID2', 'pos1,pos2']]
            postings = [ [int(x[0]), map(int, x[1].split(','))] for x in postings ]   #final postings list  
            self.index_[term] = postings
        foo.close()

    def get_Query_type(self, query):
        if '"' in query: # Paraphrase Query
            return 'PQ'
        elif len(query.split()) > 1: # Free Text Query
            return 'FTQ' 
        else: # One Word Query
            return 'OWQ'

    # Methods Defining Each Query Type
    # One Word Query
    def one_word_query(self, query):
        original_Query = query
        query = self.getTerms(query)
        
        if len(query) == 0:
            print("Try Another Search. This word may be in stopwords.xml file")
            return ''
        elif len(query) > 1:
            self.free_text_query(original_query)
            return

        # query contains only one term
        query = query[0]
        if query not in self.index_:
            print('No matches Found')
            return
        else:
            value_ = self.index_[query]
            value_ = [val[0] for val in value_]
            value_ = " ".join(map(str, value_))
            print("Matches Found: " + str(value_))
            return

    # Free Text Query
    def free_text_query(self, query):
        query = self.getTerms(query)
        if len(query) == 0:
            print("No Query String was Given")
            return
        
        li = set()
        for term in query:
            try:
                p = self.index_[term]
                p = [x[0] for x in p]
                li = li|set(p)
            except:
                #term not in index_
                pass
        
        li = list(li)
        li.sort()
        print("Matches Found" + ' '.join(map(str,li)))

    # Paraphrase Query
    def paraphrase_query(self, query):
        original_query = query
        query = self.getTerms(query)

        if len(query) == 0:
            print("No Query Strings was Given")
            return
        elif len(query) == 1:
            self.one_word_query(original_query)
            return

        phrase_docs = self.phrase_docs(query)
        if len(phrase_docs) == 0:
            print("No matches Found")
        else:
            print("Matches Found: " + " ".join(map(str, phrase_docs)))
        return
  
    def phrase_docs(self, queryItems):
        # queryItems is not the query but a list of terms in the original Query
        phraseDocs = []
        length = len(queryItems)
        #first find matching docs
        for term in queryItems:
            if term not in self.index_:
                #if a term doesn't appear in the index_
                #there can't be any document maching it
                return []
        
        postings = self.get_Postings(queryItems)    #all the terms in q are in the index_
        docs = self.getDocsFromPostings(postings)
        #docs are the documents that contain every term in the query
        docs = self.intersectLists(docs)
        #postings are the postings list of the terms in the documents docs only
        for i in range(len(postings)):
            postings[i]=[x for x in postings[i] if x[0] in docs]
        
        #check whether the term ordering in the docs is like in the phrase query
        
        #subtract i from the ith terms location in the docs
        postings = copy.deepcopy(postings)    #this is important since we are going to modify the postings list
        
        for i in range(len(postings)):
            for j in range(len(postings[i])):
                postings[i][j][1]=[x-i for x in postings[i][j][1]]
        
        #intersect the locations
        result = []
        for i in range(len(postings[0])):
            li=self.intersectLists( [x[i][1] for x in postings] )
            if li==[]:
                continue
            else:
                result.append(postings[0][i][0])    #append the docid to the result
        
        return result

    # the main method of the program
    def query_Index(self):
        self.getParameters()
        self.readindex()  
        self.getSkipWords() 

        while True:
            query = input("Enter a Search String: ")
            if query == '':
                print("No Search String is Given")
                break

            queryType = self.get_Query_type(query)
            if queryType == 'OWQ':
                self.one_word_query(query)
            elif queryType == 'FTQ':
                self.free_text_query(query)
            elif queryType == 'PQ':
                self.paraphrase_query(query)


if __name__ == '__main__':
    queryindex = Query_Index()
    queryindex.query_Index()
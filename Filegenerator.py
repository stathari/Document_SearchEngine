# -*- coding: utf-8 -*-
"""
@author: Tathari
"""


import collections
import re
from nltk.corpus import stopwords
from PorterStemmer import PorterStemmer
from pythonds import Stack
import json

stopWords = set(stopwords.words('english'))
stemmer = PorterStemmer()

index = 0
file_object  = open("cran.all.1400", "r")

#content of the file
content = file_object.read()

#documents array.
documents = content.split(".I ")

#master dictionary for inverted file
#saved wordid, count of words, set of documents, count of terms per document
master = {}

#words and their ids
words_list = {}

#words and their count
words_count = {}
postfix = []
infix = []

def getwordid(w_l,word):
    word_id = None
    if w_l.has_key(word):
        word_id = w_l[word]
    else:
        word_id = len(w_l.keys())+1
        w_l[word] = word_id
    return word_id

def calcwordCount(w_c, word_id):
    if w_c.has_key(word_id):
        w_c[word_id] += 1
    else:
        w_c[word_id] = 1
    return w_c

def get_id(word):
    #global words_list
    wordid =0
    if word in words_list:
        wordid = words_list[word]
    return wordid

def iftopf(expression, order):
    #Infix to postfix conversion
      
    s = Stack()
    pf = []
    query_terms = expression.split(' ')
    for term in query_terms:
        if term not in (["OR", "AND", "NOT", "(", ")"]):
            term = stemmer.stem(term, 0, len(term) - 1)
            id1 = get_id(term)
            pf.append(id1)
            
        elif term == '(':
            s.push(term)
        elif term == ')':
            topterm = s.pop()
            while topterm != '(':
                pf.append(topterm)
                topterm = s.pop()
        else:
            if (not s.isEmpty() and s.peek() == "NOT"):
                pf.append(s.pop())

            while (not s.isEmpty()) and (order[s.peek()] >= order[term] and term != "NOT"):
                pf.append(s.pop())
            s.push(term)

    while not s.isEmpty():
        pf.append(s.pop())

    return pf

def returnDoclist(pf, dic, order):
    """
    Computes the boolean query and return the list with document id
    """
    doc = [x for x in range(1, len(documents))]
    s = Stack()
    for query_term in pf:
        if (query_term not in order):
            if (query_term in dic):
                data = [x[0] for x in dic[query_term][1]]
            elif (query_term in stopWords):
                #stopword indication
                data = ['s']
            else:
                data = []
            s.push(data)
        else:
            if (query_term == "AND"):
                l1 = s.pop()  
                l2 = s.pop()
                if ('s' in l1 and 's' in l2):
                    res = ['s']
                elif ('s' in l1):
                    res = l2
                elif ('s' in l2):
                    res = l1
                else:
                    res = set(l1).intersection(l2)
                s.push(res)
            elif (query_term == "OR"):
                l1 = s.pop()
                l2 = s.pop()
                if ('s' in l1 and 's' in l2):
                    res = ['s']
                elif ('s' in l2):
                    res = l1
                elif ('s' in l1):
                    res = l2
                else:
                    res = set(l1).union(l2)
                s.push(res)
            elif (query_term == "NOT"):
                l = s.pop()
                if ('s' in l):
                    res = []
                else:
                    res = set(doc) - set(l)
                s.push(res)
    result = s.pop()
    final = []
    if 's' not in result:
        final = result
    return final


def Query(condition):
    # operators precedence - 1. (,)  2. NOT  3. AND, OR
    order = {'(': 1, 'NOT': 2, 'OR': 3, 'AND': 3}
    
    #infix to postfix
    pf = iftopf(condition, order)
    #print pf
    result = returnDoclist(pf, master, order)

    print "Query:", condition
    print "Number of Documents:", len(result)
    print sorted(result), "\n==================="

#preparing master dictionary   
for doc in documents:
    if doc.strip() !='':
        index = int(doc.strip().split("\n")[0])
        #print index
        doc_dict = {}
        word_list = {}
        #2.7 does not support casefold(), hence using lower()
        doc_content= doc.split(".W\n")[1].lower()
        if(doc_content!=''):
            words = re.findall("[a-zA-Z]+",doc_content)
            for word in words:
                
                wordid = None
                if word in stopWords:
                    continue
                else:
                    word = stemmer.stem(word.strip(),0,len(word)-1)
                    wordid = getwordid(words_list, word)
                    words_count = calcwordCount(words_count,wordid)
                    
                    
                if doc_dict.has_key(wordid):
                    word_list[wordid] = doc_dict.get(wordid)+1
                else:
                    word_list[wordid] = 1
            
            doc_dict =collections.OrderedDict(sorted(word_list.items()))            
           
            doc_dict = {'id': index, 'unique': len(doc_dict), 'terms': doc_dict}
            
            for term in word_list:
                if term in master:
                    master[term][0] += 1
                    master[term][1].append([index, word_list[term]])
                else:
                    master[term] = [1, [[index, word_list[term]]]]

with open('invertedfile.json', 'w') as f:
    json.dump(master, f)
    
print("invertedfile.json file is created for all the words")
    
with open('words_id.json', 'w') as f:
    json.dump(words_list, f)
print("words_id.json file is created for all the words with ids")
# -*- coding: utf-8 -*-
"""
@author: Tathari
"""
import re
from nltk.corpus import stopwords
from PorterStemmer import PorterStemmer
import json
import math
import collections

stopWords = set(stopwords.words('english'))
stemmer = PorterStemmer()



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

def calc_COSINE(processedQuery, wd, idf):
    cos = {}
    
    for doc in range(1, doc_db_count + 1):
        temp = 0
       # qtemp = 0
        # To skip those documents that are blank
        if not wd[doc]:
            continue
        for item in processedQuery:
            item = str(item)
            if idf.has_key(item):
                listItem = [x[0] for x in idf[item]['doclist']]
                if doc in listItem:
                    indexDoc = listItem.index(doc)
                    freqDT = idf[item]['doclist'][indexDoc][1]
                    logFreqDT = 1 + math.log(freqDT)
                else:
                    logFreqDT = 0
                temp += logFreqDT * idf[item]['idf']
                
        if (temp):
            cos[doc] = 1 / wd[doc] * temp
        
    #print cos
    results = collections.OrderedDict(sorted(cos.items(), key=lambda x: x[1]))
    #print results
    return list(results.keys())

 
#documents database count.
doc_db_count = 1400

#master dictionary for inverted file
#saved wordid, count of words, set of documents, count of terms per document
master = {}

with open('invertedfile.json', 'r') as f:
    master = json.load(f)
print "loaded inverted file values"

#words and their ids
words_list = {}
with open('words_id.json', 'r') as f:
    words_list = json.load(f)
print "loaded wordlist for words and ids"
                  
#process query file to form query list
qfile = open("cran.qry", "r")
content = qfile.read()
query_documents = content.split(".I ")
print "loaded queries"

#querylist
query_list =[]
for doc in query_documents:
    if doc.strip() !='':
        #2.7 does not support casefold(), hence using lower()
        query_content= doc.split(".W\n")[1].lower()
        query_list.append(query_content)

#dictionaries for cosine measures
def tf():
    tf ={}
    for word in master:
        tf[word] = []
        for data in master[word][1]:
            tf[word].append([data[0], 1 + math.log(data[1])])
    return tf

def idf():
    idf ={}
    for word in master:
        idf[word] = {'freq': master[word][0], 'idf': math.log(1 + doc_db_count / master[word][0]), 'doclist': master[word][1]}
        #print IDF
    return idf

#wd calculation
def wd():
    wd = {}
    for doc in range(1, doc_db_count + 1):
        temp = 0        
        for i in tf:
            item_list = [x[0] for x in tf[i]]
            if doc in item_list:
                indexdoc = item_list.index(doc)
                temp += math.pow(tf[i][indexdoc][1], 2)
        wd[doc] = math.sqrt(temp)
    return wd

def rel_filelist():
    rel_list ={}
    for line in rel_file:
        a = line.split(" ")
        if rel_list.has_key(a[0]):
            rel_list[a[0]].append(a[1])
        else:
            b = []
            b.append(a[1])
            rel_list[a[0]] = b
    return rel_list

tf = tf()
wd = wd()
idf = idf()

#relevance list
rel_file = open("cranqrel","r")    
rel_file = rel_file.read().split("\n")
rel_list = rel_filelist()
print "loaded relevant documents list for queries"

fileWrite = open("results.txt", "w")
qi = 1
precision_recall = {}
for query in query_list:
    fileWrite.write("Query: " + query)
    # Separate the string of query into list of words
    ql = re.findall(r'\w+', query)
    # Remove the stopwords and numbers from the list of query words
    query_nosw = [i for i in ql if i not in stopWords]
    # Stem the list of query words
    res_query = [stemmer.stem(x.lower(), 0, len(x) - 1) for x in query_nosw]
    res_query = [get_id(i) for i in res_query]
    
    relres_query =[int(x) for x in rel_list[str(qi)]]
    rel_count =  float(len(relres_query))
    # Calculate the cosine measure (Similarity) for the query
    doclist = calc_COSINE(res_query,wd,idf)
    
    ret_len = float(len(doclist))
    rel_len = float(len(set(relres_query).intersection(set(doclist))))
    
    prec = float(rel_len / ret_len) * 100
    recall = float(rel_len / rel_count) * 100
    precision_recall[qi] = {"relret_len": rel_len, "rel_doc": rel_count, "prec": prec, "recall": recall}
    #print prec
    
    fileWrite.write("\nDocuments retrieved: " + str(ret_len))
    fileWrite.write("\nDocument ID:\n")
    fileWrite.write(''.join(str(doclist)))
    fileWrite.write("\n\n\n")
    qi += 1
fileWrite.close()

#calculating precision recall

with open('precision_recall.json', 'w') as f:
    json.dump(precision_recall,f)

print "Review Results document for retrieved documents, precision_recall.json file for precision recall"
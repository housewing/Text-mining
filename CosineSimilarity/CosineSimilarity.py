import pyodbc
import numpy as np
import pandas as pd
from pandas import DataFrame
from collections import defaultdict
from operator import itemgetter
import math
import re

class token:
    def __init__(self, id, title, section, content):
        self.id = id
        self.title = title
        self.section = section
        self.content = content

def change_class(x):
    return {'財經' : '財經', '體育' : '體育', '運動' : '體育', '政治' : '政治', '兩岸' : '兩岸', '娛樂' : '娛樂', '影劇' : '娛樂', '社會' : '社會', '家庭' : '家庭'}[x]

def read_access(database):
    conn_str = (
        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        r'DBQ=' + database + ';'
    )
    cnxn = pyodbc.connect(conn_str)
    crsr = cnxn.cursor()
    file_list = []
    for row in crsr.execute("SELECT * FROM ke2016_sample_news"):
        file_list.append(token(row.id, row.title, change_class(row.section[:2]), row.content))
    return file_list

def read_excel(filename, sheet):
    key_list = defaultdict(int)
    df = pd.read_excel(filename, header=[0], index_col=[0], sheetname=sheet)
    count = 0
    for word in df.index:
        key_list[word] = count
        count += 1
    return key_list

def ngrams(line_list, n):
    ngrams = []
    for i in range(len(line_list) - ( n - 1)):
        ngrams.append(line_list[i : i + n])
    return ngrams

def tag_doc_keyword(line, key_list):
    doc_word_tf = defaultdict(int)
    for tmp_line in line:
        for i in range(2, len(tmp_line) + 1 if len(tmp_line) < 9 else 9):
            for word in ngrams(tmp_line, i):
                if key_list.get(word) != None:
                    doc_word_tf[word] += 1
    return doc_word_tf

def createIndex(data):
    index = defaultdict(list)
    for i, tokens in enumerate(data):
        for token in tokens:
            index[token].append(i)
    return index

def create_tf_matrix(row, col, doc_word_tf, key_list):
    tf_matrix = np.zeros((row, col))  # initial matrix
    for i in range(len(tf_matrix)):
        doc_word = doc_word_tf[i]
        for word in doc_word:
            sub_col = key_list.get(word)
            tf_matrix[i][sub_col] = doc_word.get(word)

    # for i in range(len(tf_matrix[0])):
    #     if tf_matrix[0][i] != 0:
    #         print(i, ' ', tf_matrix[0][i])
    return tf_matrix

def search_knn(number, tf_matrix, doc_word_tf, doc_word_index, file_list):
    doc_list = defaultdict(int)
    for word in doc_word_tf[number]:
        # print(word, '', doc_word_tf[number].get(word))
        # print(doc_word_index[word])
        for index in doc_word_index[word]:
            doc_list[index] = 1
    # print('doc_listb:', doc_list)

    cos_sim_list = defaultdict(int)
    for i in doc_list:
        if i == number: continue
        dot = sum(tf_matrix[number] * tf_matrix[i])
        lenA = math.sqrt(sum(tf_matrix[number] ** 2))
        lenB = math.sqrt(sum(tf_matrix[i] ** 2))
        cos_sim_list[i] = dot / (lenA * lenB)

    print('number of file :', len(cos_sim_list))
    cos_sim_list_sort = word_tfidf_sort = sorted(cos_sim_list.items(), key=itemgetter(1), reverse=True)

    set_list = defaultdict(int)
    print(' ----- ***** ----- : ', file_list[number].title, '     ', file_list[number].section, '\n', doc_word_tf[number])
    for no in cos_sim_list_sort[0:7]:
        set_list[file_list[no[0]].section] += 1
        print(no[0], ' similarity ---> ', no[1])
        print(file_list[no[0]].title, '     ', file_list[no[0]].section, '\n', doc_word_tf[no[0]])

    print('Classify :', max(set_list.items(), key=itemgetter(1))[0])

def main():
    file_list = read_access('../Data/ke2016_sample_data.accdb')
    print('length of file :', len(file_list))
    # for file in file_list[0:5]:
    #     print('id :', file.id, ' title :', file.title, ' section :', file.section, ' number :', file.num)

    key_list = read_excel('../Data/keyword_2100.xlsx', 'Sheet1')
    print('length of keyword :', len(key_list))
    # for key in key_list:
    #     print(key, ' ', key_list.get(key))

    doc_word_tf = []
    line_list = [[line for line in re.split('，|。| |、|<BR>●|<BR>|：', file.content)] for file in file_list]
    for line in line_list:
        doc_word_tf.append(tag_doc_keyword(line, key_list))
    print('----- Finish Tag Doc -----')

    doc_word_index = createIndex(doc_word_tf)
    print('----- Finish Inverted Index ------')
    # print(doc_word_tf[0])
    # print(doc_word_index['宏碁'])

    #create a tf matrix by numpy
    tf_matrix = create_tf_matrix(len(file_list), len(key_list), doc_word_tf, key_list)
    print('----- Finish TF matrix ------')

    while True:
        number = int(input('Please input number ( 0 - 13801 ):')) #5000
        search_knn(number, tf_matrix, doc_word_tf, doc_word_index, file_list)
        if(input('continue? (q to exit)') == 'q'):
            break

if __name__ == '__main__':
    main()
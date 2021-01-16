import json
import sys
import numpy as np
from xml.dom import minidom
import glob
from pathlib import Path
import re
import unidecode
from collections import Counter
import random
import os
folder = sys.argv[1]

# datasets = ['train', 'dev', 'test_both', 'test_seen', 'test_unseen']
datasets = ['train', 'dev', 'test']

def camel_case_split(identifier):
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    d = [m.group(0) for m in matches]
    new_d = []
    for token in d:
        token = token.replace('(', '')
        token_split = token.split('_')
        for t in token_split:
            #new_d.append(t.lower())
            new_d.append(t)
    return new_d

def get_nodes(n):
    n = n.strip()
    n = n.replace('(', '')
    n = n.replace('\"', '')
    n = n.replace(')', '')
    n = n.replace(',', ' ')
    n = n.replace('_', ' ')

    #n = ' '.join(re.split('(\W)', n))
    n = unidecode.unidecode(n)
    #n = n.lower()

    return n


def get_relation(n):
    n = n.replace('(', '')
    n = n.replace(')', '')
    n = n.strip()
    n = n.split()
    n = "_".join(n)
    return n

def process_triples(mtriples):
    nodes = []

    for m in mtriples:

        ms = m.firstChild.nodeValue
        ms = ms.strip().split(' | ')
        n1 = ms[0]
        n2 = ms[2]
        nodes1 = get_nodes(n1)
        nodes2 = get_nodes(n2)

        edge = get_relation(ms[1])

        edge_split = camel_case_split(edge)
        edges = ' '.join(edge_split)

        nodes.append('<H>')
        nodes.extend(nodes1.split())

        nodes.append('<R>')
        nodes.extend(edges.split())

        nodes.append('<T>')
        nodes.extend(nodes2.split())

    return nodes

def get_data_dev_test(file_, train_cat, dataset):

    datapoints = []
    cats = set()

    xmldoc = minidom.parse(file_)
    entries = xmldoc.getElementsByTagName('entry')
    cont = 0
    for e in entries:
        cat = e.getAttribute('category')
        cats.add(cat)

        if cat not in train_cat and dataset == 'test_seen':
            continue

        # if cat in train_cat and dataset == 'test_unseen':
        #     continue

        cont += 1

        mtriples = e.getElementsByTagName('mtriple')
        nodes = process_triples(mtriples)

        lexs = e.getElementsByTagName('lex')

        surfaces = []
        for l in lexs:
            #l = l.firstChild.nodeValue.strip().lower()
            l = l.firstChild.nodeValue.strip()
            new_doc = ' '.join(re.split('(\W)', l))
            new_doc = ' '.join(new_doc.split())
            # new_doc = tokenizer.tokenize(new_doc)
            # new_doc = ' '.join(new_doc)
            surfaces.append((l, new_doc.lower()))
        datapoints.append((nodes, surfaces))

    return datapoints, cats, cont

def get_data(file_):

    datapoints = []

    cats = set()

    xmldoc = minidom.parse(file_)
    entries = xmldoc.getElementsByTagName('entry')
    cont = 0
    for e in entries:
        cat = e.getAttribute('category')
        cats.add(cat)

        cont += 1

        mtriples = e.getElementsByTagName('mtriple')
        nodes = process_triples(mtriples)

        lexs = e.getElementsByTagName('lex')

        for l in lexs:
            #l = l.firstChild.nodeValue.strip().lower()
            l = l.firstChild.nodeValue.strip()
            new_doc = ' '.join(re.split('(\W)', l))
            new_doc = ' '.join(new_doc.split())
            #new_doc = tokenizer.tokenize(new_doc)
            #new_doc = ' '.join(new_doc)
            datapoints.append((nodes, (l, new_doc.lower())))

    return datapoints, cats, cont



train_cat = set()
dataset_points = []

for d in datasets:
    cont_all = 0
    datapoints = []
    all_cats = set()

    files = Path(folder + '/' + d).rglob('*.xml')
    files = sorted(list(files))

    for idx, filename in enumerate(files):
        filename = str(filename)
        if d == 'train':
            datapoint, cats, cont = get_data(filename)
        else:
            datapoint, cats, cont = get_data_dev_test(filename, train_cat, d)
        cont_all += cont
        all_cats.update(cats)
        datapoints.extend(datapoint)
    if d == 'train':
        train_cat = all_cats
    print(d, len(datapoints))
    print('cont', cont_all)
    print('len cat', len(all_cats))
    print('cat', all_cats)
    dataset_points.append(datapoints)


# path = os.path.dirname(os.path.realpath(__file__)) + '/webnlg/'
path = 'data/webnlg'
if not os.path.exists(path):
    os.makedirs(path)

# delete previous processed data
os.system("rm " + path + '/*')

# loop through train, dev and test set.
sample_sizes = [50, 100, 200, 500]
# training set
for sample_number in sample_sizes:
    part = 'train'
    datapoints = random.sample(dataset_points[0], sample_number)
    nodes = []
    surfaces = []
    surfaces_eval = []

    for datapoint in datapoints:
        node = datapoint[0]
        sur = datapoint[1]
        nodes.append(' '.join(node))
        surfaces.append(sur[0])
        surfaces_eval.append(sur[1])

    path_to_save = path + '/' + str(sample_number) + '/'
    Path(path_to_save).mkdir(exist_ok=True)
    with open(path_to_save + part + '.source', 'w', encoding='utf8') as f:
        f.write('\n'.join(nodes))
        f.write('\n')
    with open(path_to_save + part + '.target', 'w', encoding='utf8') as f:
        f.write('\n'.join(surfaces))
        f.write('\n')
    with open(path_to_save + part + '.target_eval', 'w', encoding='utf8') as f:
        f.write('\n'.join(surfaces_eval))
        f.write('\n')

# test set
triple_lengths = [1,2,3,4,5,6]   # 5 for triple_len>=5, 6 for all data
for triple_len in triple_lengths:
    part = 'test'
    datapoints = []
    if triple_len<5:
        for d in dataset_points[2]:
            if d[0].count('<H>') == triple_len:
                datapoints.append(d)
    elif triple_len==5:
        for d in dataset_points[2]:
            if d[0].count('<H>') >= triple_len:
                datapoints.append(d)
    else:
        datapoints = dataset_points[2]

    nodes = []
    surfaces = []
    surfaces_2 = []
    surfaces_3 = []

    surfaces_eval = []
    surfaces_2_eval = []
    surfaces_3_eval = []
    for datapoint in datapoints:
        node = datapoint[0]
        sur = datapoint[1]
        if sur == []:
            continue
        nodes.append(' '.join(node))
        surfaces.append(sur[0][0])
        surfaces_eval.append(sur[0][1])
        if len(sur) > 1:
            surfaces_2.append(sur[1][0])
            surfaces_2_eval.append(sur[1][1])
        else:
            surfaces_2.append('')
            surfaces_2_eval.append('')
        if len(sur) > 2:
            surfaces_3.append(sur[2][0])
            surfaces_3_eval.append(sur[2][1])
        else:
            surfaces_3.append('')
            surfaces_3_eval.append('')

    if triple_len<5:
        file_name = '_'+ str(triple_len)
    elif triple_len==5:
        file_name = '_'+ str(567)
    else:
        file_name = ''

    with open(path + '/' + part +file_name + '.source', 'w', encoding='utf8') as f:
        f.write('\n'.join(nodes))
        f.write('\n')
    with open(path + '/' + part +file_name + '.target', 'w', encoding='utf8') as f:
        f.write('\n'.join(surfaces))
        f.write('\n')
    with open(path + '/' + part +file_name + '.target2', 'w', encoding='utf8') as f:
        f.write('\n'.join(surfaces_2))
        f.write('\n')
    with open(path + '/' + part +file_name + '.target3', 'w', encoding='utf8') as f:
        f.write('\n'.join(surfaces_3))
        f.write('\n')

    with open(path + '/' + part +file_name + '.target_eval', 'w', encoding='utf8') as f:
        f.write('\n'.join(surfaces_eval))
        f.write('\n')
    with open(path + '/' + part +file_name + '.target2_eval', 'w', encoding='utf8') as f:
        f.write('\n'.join(surfaces_2_eval))
        f.write('\n')
    with open(path + '/' + part +file_name + '.target3_eval', 'w', encoding='utf8') as f:
        f.write('\n'.join(surfaces_3_eval))
        f.write('\n')

# val set
part = 'val'
datapoints = dataset_points[1]
nodes = []
surfaces = []
surfaces_2 = []
surfaces_3 = []

surfaces_eval = []
surfaces_2_eval = []
surfaces_3_eval = []

for datapoint in datapoints:
    node = datapoint[0]
    sur = datapoint[1]
    if sur == []:
        continue
    nodes.append(' '.join(node))
    surfaces.append(sur[0][0])
    surfaces_eval.append(sur[0][1])
    if len(sur) > 1:
        surfaces_2.append(sur[1][0])
        surfaces_2_eval.append(sur[1][1])
    else:
        surfaces_2.append('')
        surfaces_2_eval.append('')
    if len(sur) > 2:
        surfaces_3.append(sur[2][0])
        surfaces_3_eval.append(sur[2][1])
    else:
        surfaces_3.append('')
        surfaces_3_eval.append('')

with open(path + '/' + part + '.source', 'w', encoding='utf8') as f:
    f.write('\n'.join(nodes))
    f.write('\n')
with open(path + '/' + part + '.target', 'w', encoding='utf8') as f:
    f.write('\n'.join(surfaces))
    f.write('\n')
with open(path + '/' + part + '.target2', 'w', encoding='utf8') as f:
    f.write('\n'.join(surfaces_2))
    f.write('\n')
with open(path + '/' + part + '.target3', 'w', encoding='utf8') as f:
    f.write('\n'.join(surfaces_3))
    f.write('\n')

with open(path + '/' + part + '.target_eval', 'w', encoding='utf8') as f:
    f.write('\n'.join(surfaces_eval))
    f.write('\n')
with open(path + '/' + part + '.target2_eval', 'w', encoding='utf8') as f:
    f.write('\n'.join(surfaces_2_eval))
    f.write('\n')
with open(path + '/' + part + '.target3_eval', 'w', encoding='utf8') as f:
    f.write('\n'.join(surfaces_3_eval))
    f.write('\n')


# for idx, datapoints in enumerate(dataset_points):
#
#     part = datasets[idx]
#
#     if part == 'dev':
#         part = 'val'
#
#     nodes = []
#     surfaces = []
#     surfaces_2 = []
#     surfaces_3 = []
#
#     surfaces_eval = []
#     surfaces_2_eval = []
#     surfaces_3_eval = []
#     for datapoint in datapoints:
#         node = datapoint[0]
#         sur = datapoint[1]
#         if sur==[]:
#             continue
#         nodes.append(' '.join(node))
#         if part != 'train':
#             surfaces.append(sur[0][0])
#             surfaces_eval.append(sur[0][1])
#             if len(sur) > 1:
#                 surfaces_2.append(sur[1][0])
#                 surfaces_2_eval.append(sur[1][1])
#             else:
#                 surfaces_2.append('')
#                 surfaces_2_eval.append('')
#             if len(sur) > 2:
#                 surfaces_3.append(sur[2][0])
#                 surfaces_3_eval.append(sur[2][1])
#             else:
#                 surfaces_3.append('')
#                 surfaces_3_eval.append('')
#         else:
#             surfaces.append(sur[0])
#             surfaces_eval.append(sur[1])
#
#     with open(path + '/' + part + '.source', 'w', encoding='utf8') as f:
#         f.write('\n'.join(nodes))
#         f.write('\n')
#     with open(path + '/' + part + '.target', 'w', encoding='utf8') as f:
#         f.write('\n'.join(surfaces))
#         f.write('\n')
#     if part != 'train':
#         with open(path + '/' + part + '.target2', 'w', encoding='utf8') as f:
#             f.write('\n'.join(surfaces_2))
#             f.write('\n')
#         with open(path + '/' + part + '.target3', 'w', encoding='utf8') as f:
#             f.write('\n'.join(surfaces_3))
#             f.write('\n')
#
#     with open(path + '/' + part + '.target_eval', 'w', encoding='utf8') as f:
#         f.write('\n'.join(surfaces_eval))
#         f.write('\n')
#     if part != 'train':
#         with open(path + '/' + part + '.target2_eval', 'w', encoding='utf8') as f:
#             f.write('\n'.join(surfaces_2_eval))
#             f.write('\n')
#         with open(path + '/' + part + '.target3_eval', 'w', encoding='utf8') as f:
#             f.write('\n'.join(surfaces_3_eval))
#             f.write('\n')
#
#         path_c = os.path.dirname(os.path.realpath(__file__))
#         os.system("python " + path_c + '/' + "convert_files_crf.py " + path + '/' + part)
#         os.system("python " + path_c + '/' + "convert_files_meteor.py " + path + '/' + part)


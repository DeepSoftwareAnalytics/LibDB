import collections
import os
import json
import argparse
import time
from utils import *

from func2vec import func2vec
from milvus_mod import mil
import numpy as np
import pickle as pkl
import networkx as nx
import matplotlib.pyplot as plt
import random
from milvus import MetricType
from datetime import datetime

parser = argparse.ArgumentParser()

parser.add_argument('--model', type=str, default='7fea_contra_torch_b128',
                    help='visible gpu device')
parser.add_argument('--device', type=str, default='0',
                    help='visible gpu device')
parser.add_argument('--collection_name', type=str, default='_7fea_contra_torch_b128_all',
                    help='collection name in milvus')
parser.add_argument('--k', type=int, default=100,
                    help='retrieve topk')
parser.add_argument('--use_device', type=str, default='/gpu:0',
                    help='used gpu device')
parser.add_argument('--fea_dim', type=int, default=7,
                    help='feature dimension')
parser.add_argument('--load_path', type=str, default='../data/{0}/saved_model/model-inter-best.pt',
                    help='path for model loading, "#LATEST#" for the latest checkpoint')
parser.add_argument('--id2key', type=str,
                    default='../data/{0}/core_funcs/id2key.pkl', help='')
parser.add_argument('--id2package', type=str,
                    default='../data/pid2package.json', help='')
parser.add_argument('--test_app_dir', type=str,
                    default='../data/detection_targets/feature_json', help='root dir of test data')
parser.add_argument('--bin2func_num', type=str,
                    default='../data/bin2func_num.pkl', help='function numbers of binaries')
parser.add_argument('--bin2fcgs', type=str,
                    default='../data/funcs_fcg.pkl', help='fcgs of binaries')
parser.add_argument('--topk_cands', type=int,
                    default=200, help='top k candidates')
parser.add_argument('--fs_thres', type=float,
                    default=0.8, help='threshold to decide similar functions')

ARGS = parser.parse_args()

class func_tar:
    def __init__(self, func_fea) -> None:
        self.entry = func_fea['entryPoint']
        self.fea = func_fea
        self.sim_func_pairs = []
        self.cc = func_fea['complexity']

    def add_sim_func(self, query_results, fs_thres):
        for query_res in query_results:
            if query_res.distance < fs_thres:
                continue
            self.sim_func_pairs.append(sim_func_pair(self.entry, query_res))


class sim_func_pair:
    def __init__(self, func_tar_entry, query_res) -> None:
        self.func_tar_entry = func_tar_entry
        self.func_lib_id = query_res.id
        self.distance = query_res.distance


class bin_candidate:
    def __init__(self, pid, filename) -> None:
        self.file_name = filename
        self.pid = pid
        self.matched_funcs = set()
        self.matched_pairs = []
        self.score = 0
        self.rate = 0

    def add_matched_funcs(self, matched_func):
        self.matched_funcs.add(matched_func)

    def add_matched_pair(self, matched_pair):
        self.matched_pairs.append(matched_pair)

    def cal_score(self):
        lib_entries = set()
        for pair in self.matched_pairs:
            lib_entries.add(pair.func_lib_id)
        self.score = len(lib_entries)


def get_cands_func_weight(bin_fea, net, id2key, id2package, bin2func_num, fs_thres):
    collection_name = ARGS.collection_name
    k = ARGS.k
    m = mil()
    funcs = {}
    res = {}
    libs = {}
    vecs = []
    entries = []

    for f in bin_fea['binFileFeature']['functions']:
        if f['nodes'] < 5:
            continue
        if f['isThunkFunction'] is True or 'text' not in f['memoryBlock']:
            continue
        cur_f = func_tar(f)
        funcs[f['entryPoint']] = cur_f
        vec = net.get_embedding_from_func_fea(cur_f.fea, correct_edges=True)
        vec = vec.cpu().detach().numpy()
        vec = norm_vec(vec)
        vecs.append(vec)
        entries.append(cur_f.entry)
    print('begin to query')
    if not vecs:
        return libs, funcs
    start = time.time()
    query_topk = m.query(np.array(vecs), collection_name, k)
    print("qeury:", len(vecs), ' ', time.time()-start)
    print('got topk functions')
    for i in range(len(entries)):
        entry = entries[i]
        funcs[entry].add_sim_func(query_topk[i], fs_thres)

    for entry in funcs:
        for sim_pair in funcs[entry].sim_func_pairs:
            key = id2key[sim_pair.func_lib_id]
            pid = key[0]
            pname = id2package[pid]
            fname = key[1]
            if pname not in libs:
                libs[pname] = {}
            if pid not in libs[pname]:
                libs[pname][pid] = {'pscore': 0}
            if fname not in libs[pname][pid]:
                libs[pname][pid][fname] = bin_candidate(pid, fname)
            libs[pname][pid][fname].add_matched_funcs(funcs[entry])
            libs[pname][pid][fname].add_matched_pair(sim_pair)
    return libs, funcs


def filter_libs_jaccard(libs, bin2func_num):
    bin_cands = []
    for lib in libs:
        libscore = 0
        for pid in libs[lib]:
            pscore = 0
            if pid == 'libscore':
                continue
            for fi in libs[lib][pid]:
                fscore = 0
                if fi == 'pscore':
                    continue
                libs[lib][pid][fi].cal_score()
                # fscore += sim_f.func_t.cc * sim_f.sim
                # fscore += sim_f.func_t.cc
                rate = libs[lib][pid][fi].score / bin2func_num[(pid, fi)]
                libs[lib][pid][fi].rate = rate
                fscore = libs[lib][pid][fi].score
                bin_cands.append(libs[lib][pid][fi])
                libs[lib][pid][fi] = fscore
                pscore += fscore
            libs[lib][pid]['pscore'] = pscore
            libscore += pscore
        libs[lib]['libscore'] = libscore
    return libs, bin_cands


def filter_libs_afcg(libs, bin2fcgs, test_file, id2key, bin2func_num):
    bin_cands = []
    filtered_libs = {}
    for lib in libs:
        libscore = 0
        for pid in libs[lib]:
            pscore = 0
            if pid == 'libscore':
                continue
            for fi in libs[lib][pid]:
                fscore = 0
                if fi == 'pscore':
                    continue
                libs[lib][pid][fi].cal_score()
                # fscore += sim_f.func_t.cc * sim_f.sim
                # fscore += sim_f.func_t.cc
                rate = libs[lib][pid][fi].score / bin2func_num[(pid, fi)]
                libs[lib][pid][fi].rate = rate
                fscore = 0
                print(rate)
                # if rate > 0.1:
                bin_cands.append(libs[lib][pid][fi])
                # lib_fea_path = os.path.join(
                #     database, pid[-2:], pid[-4:-2], pid, pid+'.json')
                # print(lib_fea_path)
                # lib_fea = read_json(lib_fea_path)
                # for bin_lib_fea in lib_fea:
                #     if bin_lib_fea['formattedFileName'] == fi:
                #         break
                common, afcg_rate = comp_afcg(
                    libs[lib][pid][fi], bin2fcgs[pid][fi], test_file['binFileFeature']['functions'], id2key)
                if common > 1 and afcg_rate > 0.1:
                    print('    ', lib, '    ',
                          libs[lib][pid][fi].file_name)
                    print('    ', common, '    ', afcg_rate)
                    fscore = common * afcg_rate
                libs[lib][pid][fi] = [common, afcg_rate]
                pscore += fscore
            libs[lib][pid]['pscore'] = pscore
            libscore += pscore
        libs[lib]['libscore'] = libscore
    filtered_libs = {}
    for lib in libs:
        if libs[lib]['libscore'] == 0:
            continue
        filtered_libs[lib] = {'libscore': libs[lib]['libscore']}
        for pid in libs[lib]:
            if pid == 'libscore' or libs[lib][pid]['pscore'] == 0:
                continue
            filtered_libs[lib][pid] = {'pscore': libs[lib][pid]['pscore']}
            for fi in libs[lib][pid]:
                if fi == 'pscore' or libs[lib][pid][fi] == 0:
                    continue
                filtered_libs[lib][pid][fi] = libs[lib][pid][fi]
    # sorted_lib_cands = sorted(libs.items(), key=lambda x: x[1]['libscore'], reverse=True)
    # sorted_bin_cands = sorted(bin_cands, key=lambda x: x.score, reverse=True)

    return filtered_libs


def filter_cands_afcg(cands, bin2fcgs, test_file, id2key, bin2func_num, id2package):
    bin_cands = []
    filtered_libs = {}
    for cand in cands:
        pid = cand.pid
        libname = id2package[pid]
        libscore = 0
        cand.rate = cand.score / bin2func_num[(pid, cand.file_name)]
        
    
        if cand.score > 200:
            if cand.rate > 0.2:
                print('    score: ', cand.score, '    rate:', cand.rate)
                print('    ', libname, '    ', cand.file_name)
                if libname not in filtered_libs:
                    filtered_libs[libname] = {}
                if pid not in filtered_libs[libname]:
                    filtered_libs[libname][pid] = {}
                filtered_libs[libname][pid][cand.file_name] = [-1, cand.score]
            continue

        # no fcg
        # if libname not in filtered_libs:
        #     filtered_libs[libname] = {}
        # if pid not in filtered_libs[libname]:
        #     filtered_libs[libname][pid] = {}
        # filtered_libs[libname][pid][cand.file_name] = [cand.score, cand.rate]
        # continue

        # compare fcg
        if cand.score > 2 and cand.rate > 0.05:
            common, afcg_rate = comp_afcg(cand, bin2fcgs[pid][cand.file_name], test_file['binFileFeature']['functions'], id2key)
            if common > 1 and afcg_rate > 0.1:
                print('    ', libname, '    ', cand.file_name)
                print('    ', common, '    ', afcg_rate)
                fscore = common * afcg_rate
            if libname not in filtered_libs:
                filtered_libs[libname] = {}
            if pid not in filtered_libs[libname]:
                filtered_libs[libname][pid] = {}
            filtered_libs[libname][pid][cand.file_name] = [common, afcg_rate]
    return filtered_libs


def com2bins(milvus_client, bin2fcgs, bin_tar_fea, funcs, entries, vecs, collection_name, pid, fname, net, id2key, id2package, bin2func_num, k, fs_thres, correct_edges):
    bin_lib_cand = bin_candidate(pid, fname)
    
    # funcs = {}
    # entries = []
    # for f in bin_tar_fea['binFileFeature']['functions']:
    #     if f['nodes'] < 5:
    #         continue
    #     if f['isThunkFunction'] is True or 'text' not in f['memoryBlock']:
    #         continue
    #     cur_f = func_tar(f)
    #     funcs[f['entryPoint']] = cur_f
    #     vec = net.get_embedding_from_func_fea(cur_f.fea, correct_edges)
    #     vec = vec.cpu().detach().numpy()
    #     vec = norm_vec(vec)
    #     vecs.append(vec)
    #     entries.append(cur_f.entry)

    m = milvus_client
    # query_func = m.query(np.array(vecs), collection_name,
    #                      10, partition_tags=[partition])
    start = time.time()
    query_func = m.query(np.array(vecs), collection_name, k)
    query_time = time.time() - start
    print('query time: ', query_time)
    for i in range(len(entries)):
        entry = entries[i]
        funcs[entry].add_sim_func(query_func[i], fs_thres)
    for entry in funcs:
        for sim_pair in funcs[entry].sim_func_pairs:
            bin_lib_cand.add_matched_funcs(funcs[entry])
            bin_lib_cand.add_matched_pair(sim_pair)
    
    bin_lib_cand.cal_score()
    bin_lib_cand.rate = bin_lib_cand.score / bin2func_num[(pid, fname)]
    if bin_lib_cand.score > 2 and bin_lib_cand.rate > 0.05:
        start = time.time()
        common, afcg_rate = comp_afcg(
            bin_lib_cand, bin2fcgs[pid][fname], bin_tar_fea['binFileFeature']['functions'], id2key)
        com_fcg = time.time() - start
        print('com_time:', com_fcg, 'rate: ', query_time / com_fcg)
        print('score: ', bin_lib_cand.score)
    else:
        common = 0
        afcg_rate = 0
    return common, afcg_rate



def comp_afcg(cand, bin_lib_funcs, bin_tar_funcs, id2key):
    target_entries = []
    lib_entries = []
    sim_f_pairs = []
    for sim_pair in cand.matched_pairs:
        target_entries.append(sim_pair.func_tar_entry)
        lib_entries.append(id2key[sim_pair.func_lib_id][2])
        sim_f_pairs.append(
            [sim_pair.func_tar_entry, id2key[sim_pair.func_lib_id][2]])

    afcg_lib = get_afcg(lib_entries, bin_lib_funcs)
    afcg_tar = get_afcg(target_entries, bin_tar_funcs)
    common, cost = afcg_cost(afcg_lib, afcg_tar, sim_f_pairs)
    return common, cost


def afcg_cost(afcg_lib, afcg_tar, sim_f_pairs):
    entries_lib2tar = {}
    entries_tar2lib = {}
    for sim_f_pair in sim_f_pairs:
        if sim_f_pair[0] not in entries_tar2lib:
            entries_tar2lib[sim_f_pair[0]] = []
        entries_tar2lib[sim_f_pair[0]].append(sim_f_pair[1])
        if sim_f_pair[1] not in entries_lib2tar:
            entries_lib2tar[sim_f_pair[1]] = []
        entries_lib2tar[sim_f_pair[1]].append(sim_f_pair[0])

    common = 0
    diff_lib2tar = 0
    diff_tar2lib = 0
    for entry in afcg_lib:
        for child in afcg_lib[entry]:
            entries_tar = entries_lib2tar[entry]
            children_tar = entries_lib2tar[child]
            flag = 0
            for child_tar in children_tar:
                for entry_tar in entries_tar:
                    if child_tar in afcg_tar[entry_tar]:
                        flag = 1
                        break
                if flag:
                    break
            if flag:
                common += 1
            else:
                diff_lib2tar += 1

    for entry in afcg_tar:
        for child in afcg_tar[entry]:
            flag = 0
            entries_lib = entries_tar2lib[entry]
            children_lib = entries_tar2lib[child]
            flag = 0
            for child_lib in children_lib:
                for entry_lib in entries_lib:
                    if child_lib in afcg_lib[entry_lib]:
                        flag = 1
                        break
                if flag:
                    break
            if flag:
                continue
            else:
                diff_tar2lib += 1
    if common == 0:
        return 0, 0
    return common, common / (common + diff_lib2tar + diff_tar2lib)


def get_valid_child(entry, entry2f, valid_entry_points, already_entries):
    res = []
    already_entries.append(entry)
    # if entry not in entry2f:
    #     return res
    if entry not in entry2f:
        return set(res)
    children = set(entry2f[entry]['calledFunctionAddresses'] +
                   entry2f[entry]['calledFunctionsByPointer'])
    for child in children:
        if child in already_entries:
            continue
        already_entries.append(child)
        if child in valid_entry_points:
            res.append(child)
        else:
            # new_already_entry = already_entries[:]
            sub = get_valid_child(
                child, entry2f, valid_entry_points, already_entries)
            res += sub
    return set(res)


def get_afcg(valid_entry_points, entry2f):
    afcg = {}
    func_denp_par = {}
    for i in valid_entry_points:
        func_denp_par[i] = []
    for entry in set(valid_entry_points):
        afcg[entry] = get_valid_child(entry, entry2f, valid_entry_points, [])
        for i in afcg[entry]:
            func_denp_par[i].append(entry)
    return afcg


def detect_v2(save_path):
    fs_thres = ARGS.fs_thres
    TEST_APP_DIR = ARGS.test_app_dir
    bin2fcgs = read_pkl(ARGS.bin2fcgs)
    apps = os.listdir(TEST_APP_DIR)
    detection_results = {}
    id2key = read_pkl(ARGS.id2key.format(ARGS.model))
    id2package = read_json(ARGS.id2package)
    bin2func_num = read_pkl(ARGS.bin2func_num)
    topk_cands = ARGS.topk_cands
    net = func2vec(ARGS.load_path.format(ARGS.model),
                   gpu=True, fea_dim=ARGS.fea_dim)
    for app in apps:
        print('\n\n')
        print(datetime.now())
        print(app)
        detection_results[app] = {}
        bin_files_path = os.path.join(TEST_APP_DIR, app, '0.json')
        if not os.path.exists(bin_files_path):
            continue
        test_file_list = read_json(bin_files_path)
        for test_file in test_file_list:
            print(test_file['formattedFileName'])
            libs, funcs = get_cands_func_weight(
                test_file, net, id2key, id2package, bin2func_num, fs_thres)
            print("got libs")

            libs, bin_cands = filter_libs_jaccard(libs, bin2func_num)
            # sorted_lib_cands = sorted(libs.items(), key=lambda x: x[1]['libscore'], reverse=True)

            # for i in sorted_lib_cands:
            #     print(i[0], '    ', i[1]['libscore'])
            sorted_bin_cands = sorted(
                bin_cands, key=lambda x: x.score, reverse=True)
            filtered_libs = filter_cands_afcg(
                sorted_bin_cands[:topk_cands], bin2fcgs, test_file, id2key, bin2func_num, id2package)
            # filtered_libs = filter_libs_afcg(
            #     libs, bin2fcgs, test_file, id2key, bin2func_num)
            print("got filtered libs")
            detection_results[app][test_file['formattedFileName']
                                   ] = filtered_libs
    save_json(detection_results, save_path)


if __name__ == '__main__':
    detect_v2('./7fea_contra_torch_b128_fk100_ck200_rate0.05_fsthres0.75.json')
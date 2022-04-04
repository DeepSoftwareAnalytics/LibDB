import pickle as pkl
import os
import argparse
import numpy as np
from milvus import MetricType
import time
from milvus_mod import mil
from utils import *

parser = argparse.ArgumentParser()
parser.add_argument('--model', type=str, default='7fea_contra_torch_b128',
                    help='network model')
parser.add_argument('--pinfo', type=str, default='/data/fedora_core_fedora_packages_0505.json',
                    help='package info')

parser.add_argument('--id2key', type=str, default='../data/{0}/core_funcs/id2key.pkl',
                    help='id to key')
parser.add_argument('--id2vec', type=str, default='../data/{0}/core_funcs/id2vec.pkl',
                    help='id to vec')
ARGS = parser.parse_args()


def generate_vec_index(data_path, id2key_save_path, id2vec_save_path, norm):
    raw_data_files = os.listdir(data_path)
    raw_data = {}
    for f in raw_data_files:
        with open(os.path.join(data_path, f), 'rb') as load_f:
            raw_data.update(pkl.load(load_f))
    id = 0
    id2key = {}
    id2vec = {}
    for key in raw_data:
        id += 1
        if id % 100000 == 0:
            print(id)
        id2key[id] = key
        if norm:
            id2vec[id] = norm_vec(raw_data[key])
        else:
            id2vec[id] = raw_data[key]
    print(id)
    save_pkl(id2key, id2key_save_path)
    save_pkl(id2vec, id2vec_save_path)


def get_filtered_data(id2key, id2vec, pid2pname, save_path, norm):
    test_p = ['sqlite', 'stunnel', 'yasm', 'ytasm']
    id2keys = read_pkl(id2key)
    id2vecs = read_pkl(id2vec)
    pid2pnames = read_json(pid2pname)
    count = 0
    print(len(id2vecs))
    deleted_p = []
    for id in list(id2vecs.keys()):
        count += 1
        if norm:
            id2vecs[id] = norm_vec(id2vecs[id])
        pid = id2keys[id][0]
        pname = pid2pnames[pid]
        fname = id2keys[id][1]
        for i in test_p:
            if i in pname or i in fname:
                deleted_p.append(pname)
                del id2vecs[id]
    print(len(id2vecs))
    save_pkl(id2vecs, save_path)
    return id2vecs


def norm_vec(vec):
    return vec/np.sqrt(sum(vec**2))


def generate_test_cases(test_embeddings_path, test_cases_dir, norm):
    test_cases = os.listdir(test_embeddings_path)
    id = 50000000
    count = 0
    if not os.path.exists(test_cases_dir):
        os.makedirs(test_cases_dir)
    for test_case in test_cases:
        id2key = {}
        id2lvec = {}
        vecs = {}
        print(test_case)
        with open(os.path.join(test_embeddings_path, test_case), 'rb') as load_f:
            true_pairs = pkl.load(load_f)
        test_id_vec_pairs = []
        for pair in true_pairs:
            count += 1
            if count % 10000 == 0:
                print(count)
            key = list(pair.keys())[0]
            l_vec = list(pair.values())[0][0].tolist()
            r_vec = list(pair.values())[0][1].tolist()
            if key not in vecs:
                id += 1
                vecs[key] = [[l_vec], [id]]
                index = id
            else:
                if l_vec not in vecs[key][0]:
                    id += 1
                    vecs[key][0].append(l_vec)
                    vecs[key][1].append(id)
                    index = id
                else:
                    index = vecs[key][0].index(l_vec)
                    index = vecs[key][1][index]
            id2key[index] = key
            if norm:
                id2lvec[index] = norm_vec(np.array(l_vec))
                test_id_vec_pairs.append([index, norm_vec(np.array(r_vec))])
            else:
                id2lvec[index] = np.array(l_vec)
                test_id_vec_pairs.append([index, np.array(r_vec)])
        with open(os.path.join(test_cases_dir, test_case), 'wb') as fo:
            pkl.dump(test_id_vec_pairs, fo)
        with open(os.path.join(test_cases_dir, 'id2key_'+test_case), 'wb') as fo:
            pkl.dump(id2key, fo)
        with open(os.path.join(test_cases_dir, 'id2vec_'+test_case), 'wb') as fo:
            pkl.dump(id2lvec, fo)


def build_database(collection_name, id2vecs, clear_old, metrictype):
    m = mil()
    m.load_data(list(id2vecs.values()), list(id2vecs.keys()),
                collection_name, clear_old=clear_old, metrictype=metrictype)


def recall_rate(labels, query_results):
    total_num = len(labels)
    recall_num = 0
    for i in range(len(labels)):
        recall_ids = []
        for cand in query_results[i]:
            recall_ids.append(cand.id)
        if labels[i] in recall_ids:
            recall_num += 1
    return recall_num / total_num


def get_4_recalls(labels, query_results):
    total_num = len(labels)
    recall_num = [0, 0, 0, 0]
    for i in range(len(labels)):
        recall_ids = []
        for cand in query_results[i]:
            recall_ids.append(cand.id)
        if labels[i] in recall_ids[:10]:
            recall_num[0] += 1
        if labels[i] in recall_ids[:20]:
            recall_num[1] += 1
        if labels[i] in recall_ids[:50]:
            recall_num[2] += 1
        if labels[i] in recall_ids:
            recall_num[3] += 1
    return (100 * np.array(recall_num) / total_num).tolist()


def test_recall(test_id_vec, m, collection_name, k):
    l_ids = []
    r_vecs = []
    for pair in test_id_vec:
        l_ids.append(pair[0])
        r_vecs.append(pair[1])
    print("query length: ", len(r_vecs))
    start = time.time()
    results = m.query(np.array(r_vecs), collection_name, k)
    if results:
        recalls = get_4_recalls(l_ids, results)
        # return [round(recall*100, 2), round(time.time()-start, 2), len(r_vecs)]
        return recalls
    else:
        return None


def test_one_case(test_id_vec_pair, collection_name, id2vec_pkl, clear_old, metrictype):
    m = mil()
    print("data num:", m.get_count(collection_name))
    id2vecs = read_pkl(id2vec_pkl)
    m.load_data(list(id2vecs.values()), list(id2vecs.keys()),
                collection_name, clear_old=clear_old, metrictype=metrictype)
    print("data num after added:", m.get_count(collection_name))
    test_id_vec = read_pkl(test_id_vec_pair)
    print("test: ", test_id_vec_pair)
    # res_10 = test_recall(test_id_vec, m, collection_name, 10)
    # res_20 = test_recall(test_id_vec, m, collection_name, 20)
    # res_50 = test_recall(test_id_vec, m, collection_name, 50)
    res = test_recall(test_id_vec, m, collection_name, 100)

    m.delete_entities_by_ids(list(id2vecs.keys()), collection_name)
    print("data num after tested and deleted:", m.get_count(collection_name))
    # return [res_10, res_20, res_50, res_100]
    return res


def test_all(test_cases_dir, collection_name, clear_old, metrictype):
    res = {}
    fs = os.listdir(test_cases_dir)
    for f in fs:
        if f.startswith('id2'):
            continue
        test_case = os.path.join(test_cases_dir, f)
        # test_id_vec_pair = read_pkl(test_case)
        id2vec_pkl = os.path.join(test_cases_dir, 'id2vec_'+f)
        res[test_case] = test_one_case(
            test_case, collection_name, id2vec_pkl, clear_old, metrictype)
        print(res)

    for test_case in res:
        print('{0} & {1}& {2}& {3}& {4}'.format(test_case, str(round(res[test_case][0], 2)), str(
            round(res[test_case][1], 2)), str(round(res[test_case][2], 2)), str(round(res[test_case][3], 2))))


def get_bin2func_num(id2key, id2package):
    bin2func_num = {}
    save_path = './bin2func_num.pkl'
    with open(id2key, 'rb') as load_f:
        id2key = pkl.load(load_f)
    with open(id2package, 'r') as load_f:
        id2package = json.load(load_f)
    for id in id2key:
        if (id2key[id][0], id2key[id][1]) not in bin2func_num:
            bin2func_num[(id2key[id][0], id2key[id][1])] = 0
        bin2func_num[(id2key[id][0], id2key[id][1])] += 1
    save_pkl(bin2func_num, save_path)


def get_bin2func_num_all_fedora(id2key_dir):
    bin2func_num = {}
    save_path = './bin2func_num_all_fedora.pkl'
    for i in os.listdir(id2key_dir):
        if not i.startswith('id2key'):
            continue
        print(i)
        id2key = os.path.join(id2key_dir, i)
        with open(id2key, 'rb') as load_f:
            id2key = pkl.load(load_f)
        count = 0
        for id in id2key:
            count += 1
            if count % 1000000 == 0:
                print(count)
            if (id2key[id][0], id2key[id][1]) not in bin2func_num:
                bin2func_num[(id2key[id][0], id2key[id][1])] = 0
            bin2func_num[(id2key[id][0], id2key[id][1])] += 1
    save_pkl(bin2func_num, save_path)


def get_bin_fcg(database, save_path):
    package_count = 0
    level_ids = os.listdir(database)
    funcs_fcg = {}
    for first_level_id in level_ids:
        for second_level_id in level_ids:
            second_level_path = os.path.join(
                database, first_level_id, second_level_id)
            if not os.path.exists(second_level_path):
                continue
            packages = os.listdir(second_level_path)
            for package in packages:
                package_count += 1
                if package_count % 100 == 0:
                    print("package: ", package_count)
                package_path = os.path.join(second_level_path, package)
                if not os.path.isdir(package_path):
                    continue
                package_feature_json = os.path.join(
                    package_path, package+'.json')
                if not os.path.exists(package_feature_json):
                    continue
                try:
                    with open(package_feature_json, 'r') as load_f:
                        content = json.load(load_f)
                except:
                    print("error package", package)
                    continue
                funcs_fcg[package] = {}
                for binary_file in content:
                    if 'binFileFeature' not in binary_file:
                        continue
                    funcs_fcg[package][binary_file['formattedFileName']] = {}
                    for func in binary_file['binFileFeature']['functions']:
                        if func['nodes'] < 5:
                            continue
                        if func['isThunkFunction'] is True or 'text' not in func['memoryBlock']:
                            continue
                        func = {'isThunkFunction': func['isThunkFunction'], 'memoryBlock': func['memoryBlock'],
                                'calledFunctionAddresses': func['calledFunctionAddresses'], 'calledFunctionsByPointer': func['calledFunctionsByPointer'], 'entryPoint':func['entryPoint']}
                        funcs_fcg[package][binary_file['formattedFileName']][func['entryPoint']] = func
    save_pkl(funcs_fcg, save_path)


def bd_all_fedora(collection_name, vec_index_path):
    m = mil()
    m.delete_collection(collection_name)
    fs = os.listdir(vec_index_path)
    for f in fs:
        if not f.startswith('id2vec'):
            continue
        id2vecs = read_pkl(os.path.join(vec_index_path, f))
        m.load_data(list(id2vecs.values()), list(id2vecs.keys()),
                collection_name, clear_old=False, metrictype=MetricType.IP)


def build_partions(ID2KEY, ID2VEC, collection_name, PINFO,PID2PNAME):
    id2keys = read_pkl(ID2KEY)
    all_id2vecs = read_pkl(ID2VEC)
    m = mil()
    bin2vecs = {}
    for id in all_id2vecs:
        key = id2keys[id]
        partition_name = '::'.join([key[0], key[1]])
        if partition_name not in bin2vecs:
            bin2vecs[partition_name] = {'vecs':[], 'ids':[]}
        bin2vecs[partition_name]['vecs'].append(all_id2vecs[id])
        bin2vecs[partition_name]['ids'].append(id)

    pinfo = read_json(PINFO)
    pid2pname = read_json(PID2PNAME)
    pname2libid = {}
    for i in pinfo:
        if i['project_name'] not in pname2libid:
            pname2libid[i['project_name']] = i['project_id']

    lib2bin = {}
    for bin_file in bin2vecs:
        pid = bin_file.split('::', 1)[0]
        p_name = pid2pname[pid]
        libid = pname2libid[p_name]
        if libid not in lib2bin:
            lib2bin[libid] = {}
        lib2bin[libid][bin_file] = bin2vecs[bin_file]
    print('begin to build database')

    count=0
    for libid in lib2bin:
        count += 1
        if count % 50 == 0:
            print(count)
        if len(lib2bin[libid]) > 4096:
            continue
        
        m.load_partition_data(lib2bin[libid], '_'+str(libid),
                   clear_old=True, metrictype=MetricType.IP)


def build_divide_collections(ID2KEY, ID2VEC, PINFO,PID2PNAME):
    id2keys = read_pkl(ID2KEY)
    all_id2vecs = read_pkl(ID2VEC)
    pinfo = read_json(PINFO)
    pid2pname = read_json(PID2PNAME)
    m = mil()
    lib2vecs = {}
    for id in all_id2vecs:
        key = id2keys[id]
        lib_name = pid2pname[key[0]]
        if lib_name not in lib2vecs:
            lib2vecs[lib_name] = {'vecs':[], 'ids':[]}
        lib2vecs[lib_name]['vecs'].append(all_id2vecs[id])
        lib2vecs[lib_name]['ids'].append(id)

    libname2libid = {}
    for i in pinfo:
        if i['project_name'] not in libname2libid:
            libname2libid[i['project_name']] = i['project_id']

    libid2vecs = {}
    for lib_name in lib2vecs:
        libid = libname2libid[lib_name]
        if libid not in libid2vecs:
            libid2vecs[libid] = {}
        libid2vecs[libid] = lib2vecs[lib_name]
    print('begin to build database')

    count=0
    for libid in libid2vecs:
        count += 1
        if count % 50 == 0:
            print(count)
        m.load_data(list(libid2vecs[libid]['vecs']), list(all_id2vecs.keys()),
                '_'+str(libid), clear_old=True, metrictype=MetricType.IP)

def generate_pid2bin2vecid(save_path):
    MODEL = ARGS.model
    id2keys = read_pkl(ARGS.id2key.format(MODEL))
    all_id2vecs = read_pkl(ARGS.id2vec.format(MODEL))
    pid2bin2vecid = {}
    for id in all_id2vecs:
        key = id2keys[id]
        pid = key[0]
        fname = key[1]
        if pid not in pid2bin2vecid:
            pid2bin2vecid[pid] = {}
        if fname not in pid2bin2vecid[pid]:
            pid2bin2vecid[pid][fname] = []
        pid2bin2vecid[pid][fname].append(id)
    save_pkl(pid2bin2vecid, save_path)




if __name__ == '__main__':
    model = ARGS.model
    PID2PNAME = '../data/core_funcs_vectors/pid2package.json'
    PINFO = '../data/core_funcs_vectors/fedora_core_fedora_packages_0505.json'

    data_7fea = '../data/7fea_contra_torch_b128/core_funcs'
    generate_vec_index(data_7fea, ARGS.id2key, ARGS.id2vec, norm=False)


    collection_name = '_7fea_contra_torch_b128'
    all_id2vecs = read_pkl(ARGS.id2vec)
    m = mil()
    print('start building...')
    m.load_data(list(all_id2vecs.values()), list(all_id2vecs.keys()),
                collection_name, clear_old=True, metrictype=MetricType.IP)


    data_path = '../data/7fea_contra_torch_b128/core_funcs'
    raw_feature_database = '../data/CoreFedoraFeatureJson0505'
    save_path = './funcs_fcg.pkl'
    database = '../data/CoreFedoraFeatureJson0505'
    get_bin_fcg(database, save_path)

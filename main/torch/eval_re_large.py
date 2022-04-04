import collections
import pickle as pkl
import os
import json
import numpy as np
from milvus import MetricType
import time
from milvus_mod import mil


def read_pkl(pkl_path):
    with open(pkl_path, 'rb') as f:
        content = pkl.load(f)
    return content


def save_pkl(content, save_path):
    with open(save_path, 'wb') as f:
        pkl.dump(content, f)


def read_json(js_path):
    with open(js_path, 'r') as f:
        content = json.load(f)
    return content


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

            

if __name__ == '__main__':
    model = '7fea_contra_torch_b128'
    # model = '76fea_triple_torch_negb128_epo150'
    # model = '76fea_triple_torch_epo150_gap0.5'
    # collection_name = '_76fea_triple_torch_epo150_gap05_filtered'

    PINFO = '../data/core_funcs_vectors/pid2package.json'
    ID2KEY = '../data/{0}/core_funcs/id2key.pkl'.format(
        model)
    ID2VEC = '../data/{0}/core_funcs/id2vec.pkl'.format(
        model)

    data_path = '../data/{0}/core_funcs'.format(
        model)
    # generate_vec_index(data_path, ID2KEY, ID2VEC, norm=False)

    # filtered_id2vecs_path = '../data/{0}/core_funcs/filtered_id2vecs.pkl'.format(
    #     model)
    # filtered_id2vecs = get_filtered_data(
    #     ID2KEY, ID2VEC, PINFO, filtered_id2vecs_path, True)

    # test_embeddings_path = '../data/{0}/valid_pairs'.format(
    #     model)
    # test_cases_dir = '../data/{0}/test_cases'.format(
    #     model)
    # generate_test_cases(test_embeddings_path, test_cases_dir, norm=True)

    # collection_name = '_76fea_triple_torch_negb128_epo150_filtered'
    # collection_name = '_7fea_contra_torch_b128_filtered'

    # filtered_id2vecs = read_pkl(filtered_id2vecs_path)
    # build_database(collection_name, filtered_id2vecs,
    #    clear_old=True, metrictype=MetricType.IP)

    # test_all(test_cases_dir, collection_name,
    #          clear_old=False, metrictype=MetricType.IP)

    collection_name = '_7fea_contra_torch_b128_all'
    all_id2vecs = read_pkl(ID2VEC)
    build_database(collection_name, all_id2vecs,
                   clear_old=True, metrictype=MetricType.IP)

import pickle as pkl
import os
import json
import numpy as np

# vec -> numpy array
def norm_vec(vec):
    return vec/np.sqrt(sum(vec**2))


def generate_vec_index(data_path, id2key_sava_path, id2vec_save_path, norm):
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
    with open(id2key_sava_path, 'wb') as fo:
        pkl.dump(id2key, fo)
    with open(id2vec_save_path, 'wb') as fo:
        pkl.dump(id2vec, fo)



def get_true_pairs(js_path):
    true_pairs = []
    with open(js_path) as load_f:
        for line in load_f:
            pair = json.loads(line.strip())
            true_pairs.append(pair)
    return true_pairs

def save_data(data, save_path):
    for item in data:
        with open(save_path, 'a+') as f:
            line = json.dumps(item)
            f.write(line+'\n')

def generate_valid_vec_index(js_dir, id_vec_dir, norm):
    js_fs = os.listdir(js_dir)
    id2key = {}
    id2vec = {}
    vecs = {}
    id = 50000000
    count =0
    if not os.path.exists(id_vec_dir):
        os.makedirs(id_vec_dir)
    for f in js_fs:
        print(f)
        # true_pairs = get_true_pairs(os.path.join(js_dir, f))
        with open(os.path.join(js_dir, f), 'rb') as load_f:
            true_pairs = pkl.load(load_f)
        id_vec_pairs = []
        for pair in true_pairs:
            count += 1
            if count % 10000 ==0:
                print(count)
            key = list(pair.keys())[0]
            l_vec_pair = list(pair.values())[0][0].tolist()
            r_vec_pair = list(pair.values())[0][1].tolist()
            if key not in vecs:
                id += 1
                vecs[key] = [[l_vec_pair],[id]]
                index = id
            else:
                if l_vec_pair not in vecs[key][0]:
                    id += 1
                    vecs[key][0].append(l_vec_pair)
                    vecs[key][1].append(id)
                    index = id
                else:
                    index = vecs[key][0].index(l_vec_pair)
                    index = vecs[key][1][index]
            id2key[index] = key
            if norm:
                id2vec[index] = norm_vec(np.array(l_vec_pair))
                id_vec_pairs.append([index, norm_vec(np.array(r_vec_pair)).tolist()])
            else:
                id2vec[index] = np.array(l_vec_pair)
                id_vec_pairs.append([index, np.array(r_vec_pair).tolist()])
        # save_data(id_vec_pairs, os.path.join(id_vec_dir, f))
        with open(os.path.join(id_vec_dir, f), 'wb') as fo:
            pkl.dump(id_vec_pairs, fo)
    with open(os.path.join(id_vec_dir, 'id2key.pkl'), 'wb') as fo:
        pkl.dump(id2key, fo)
    with open(os.path.join(id_vec_dir, 'id2vec.pkl'), 'wb') as fo:
        pkl.dump(id2vec, fo)

def check():
    id2vec = '../data/validation_pairs/valid_pairs_v1/id_vec/id_vec_7fea/id2vec.pkl'
    with open(id2vec, 'rb') as fo:
        a=pkl.load(fo)
    pairs = get_true_pairs('../data/validation_pairs/valid_pairs_v1/id_vec/id_vec_7fea/cc_version_diff_7_fea_dim.json')
    count = 0
    for pair in pairs:
        target_vec = np.array(pair[1])
        base_vec = np.array(a[pair[0]])
        cos = sum(base_vec * target_vec)
        if 0.5 + cos/2 > 0.7367:
            count += 1
    print(count/len(pairs))


if __name__ == '__main__':
    data_7fea = '../data/7fea_contra_tf/core_funcs'
    id2key_7fea = '../data/7fea_contra_tf/core_funcs/id2key.pkl'
    id2vec_7fea = '../data/7fea_contra_tf/core_funcs/id2vec.pkl'

    generate_vec_index(data_7fea, id2key_7fea, id2vec_7fea, norm=False)



    valid_vec_pairs_dir = '../data/7fea_contra_tf/valid_pairs'
    id_vec_valid_dir = '../data/7fea_contra_tf/id_vec_valid'

    generate_valid_vec_index(valid_vec_pairs_dir, id_vec_valid_dir, norm = True)

    # check()
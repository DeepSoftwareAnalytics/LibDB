# This program demos how to connect to Milvus vector database, 
# create a vector collection,
# insert 10 vectors, 
# and execute a vector similarity search.

import random
import numpy as np
import pickle as pkl
from milvus import Milvus, IndexType, MetricType, Status
import os
import json
import time
from tqdm import tqdm
import math



class mil(object):
    def __init__(self, dim=64) -> None:

        # Milvus server IP address and port.
        # You may need to change _HOST and _PORT accordingly.
        self._HOST = '127.0.0.1'
        self._PORT = '19530'  # default value
        # _Ppip ORT = '19121'  # default http value

        # Vector parameters
        self._DIM = dim  # dimension of vector

        self._INDEX_FILE_SIZE = 4096  # max file size of stored index

        self.BATCH =10000
        self.milvus = Milvus(self._HOST, self._PORT)

    def get_count(self, collection_name):
        status, result = self.milvus.count_entities(collection_name)
        return result

    def delete_collection(self, collection_name):
        status, ok = self.milvus.has_collection(collection_name)
        if ok:
            self.milvus.drop_collection(collection_name)
            self.milvus.flush([collection_name])


    def load_data(self, vec_l, id_l, collection_name, clear_old, metrictype):
        # Specify server addr when create milvus client instance
        # milvus client instance maintain a connection pool, param
        # `pool_size` specify the max connection num.

        status, ok = self.milvus.has_collection(collection_name)
        if ok and clear_old:
            self.milvus.drop_collection(collection_name)
            # print('dropout old collection')
        if not ok or (ok and clear_old):
            param = {
                'collection_name': collection_name,
                'dimension': self._DIM,
                'index_file_size': self._INDEX_FILE_SIZE,  # optional
                'metric_type': metrictype  # optional
            }
            self.milvus.create_collection(param)
            # print('collection created:', collection_name)
        
        status, result = self.milvus.count_entities(collection_name)
        old_count = result
        vectors = np.array(vec_l).astype(np.float32)
        length = len(vectors)
        begin = 0
        end = self.BATCH
        # print('begin to insert')
        # print('data length:', length)
        # print('start with old count:', old_count)
        loops = math.ceil(length / self.BATCH)
        for i in tqdm(range(loops)):
            begin = self.BATCH * i
            end = self.BATCH * (i+1)
            if begin >= length:
                break
            if end>=length:
                end = length
            status, ids = self.milvus.insert(collection_name=collection_name, records=vectors[begin:end], ids=id_l[begin:end])
            if not status.OK():
                print("Insert failed: {}".format(status))
                break
            begin += self.BATCH
            end += self.BATCH

        # Flush collection  inserted data to disk.
        self.milvus.flush([collection_name])

    def load_partition_data(self, bin2vecs, collection_name, clear_old, metrictype):
        status, ok = self.milvus.has_collection(collection_name)
        if ok and clear_old:
            self.milvus.drop_collection(collection_name)
            print('dropout old collection')
        if not ok or (ok and clear_old):
            param = {
                'collection_name': collection_name,
                'dimension': self._DIM,
                'index_file_size': self._INDEX_FILE_SIZE,  # optional
                'metric_type': metrictype  # optional
            }
            self.milvus.create_collection(param)
            print('collection created:', collection_name)
        count = 0
        for bin_f in bin2vecs:
            count += 1
            if count % 10000 == 0:
                print(count)
            vecs = bin2vecs[bin_f]['vecs']
            ids = bin2vecs[bin_f]['ids']
            vectors = np.array(vecs).astype(np.float32)
            self.milvus.create_partition(collection_name, bin_f)
            status, ids = self.milvus.insert(collection_name=collection_name,records=vectors, ids=ids, partition_tag=bin_f)
        self.milvus.flush([collection_name])

    def creat_index(self, collection_name):
        # Get demo_collection row count
        status, result = self.milvus.count_entities(collection_name)
        print(result)

        # present collection statistics info
        _, info = self.milvus.get_collection_stats(collection_name)
        print(info)

        # Obtain raw vectors by providing vector ids
        # status, result_vectors = milvus.get_entity_by_id(collection_name, ids[:10])

        # create index of vectors, search more rapidly
        index_param = {
            'nlist': 8192
        }

        # Create ivflat index in demo_collection
        # You can search vectors without creating index. however, Creating index help to
        # search faster
        print("Creating index: {}".format(index_param))
        status = self.milvus.create_index(collection_name, IndexType.IVF_FLAT, index_param)

        # describe index, get information of index
        status, index = self.milvus.get_index_info(collection_name)
        print(index)
        print('creating index. Done.')
    

    def query(self, query_vectors, collection_name, k, partition_tags=None, nprobe=100):
        # Show collections in Milvus server
        _, collections = self.milvus.list_collections()

        # Describe demo_collection
        _, collection = self.milvus.get_collection_info(collection_name)


        # query_vectors = np.load(query_vectors_path)

        # execute vector similarity search
        search_param = {
            "nprobe": nprobe
        }

        param = {
            'collection_name': collection_name,
            'query_records': query_vectors,
            'top_k': k,
            'params': search_param,
            'partition_tags': partition_tags
        }

        status, results = self.milvus.search(**param)
        if status.OK():
            return results
        else:
            print("Search failed. ", status)
            return None


            
    def get_vector_by_id(self, collection_name, ids):
        status, vectors = self.milvus.get_entity_by_id(collection_name, ids)
        print(status)
        for vector in vectors:
            print(vector)

    def delete_entities_by_ids(self, ids, collection_name):
        print("to delete: ", len(ids))
        begin = 0
        end = self.BATCH
        length = len(ids)
        while(True):
            if begin >= length:
                break
            if end>=length:
                end = length
            print(begin)
            self.milvus.delete_entity_by_id(collection_name, id_array=ids[begin:end])
            begin += self.BATCH
            end += self.BATCH
        self.milvus.flush([collection_name])
        # status, result = self.milvus.count_entities(collection_name)
        # print("left entities:", result)


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



def get_true_pairs(js_path):
    true_pairs = []
    with open(js_path) as load_f:
        for line in load_f:
            pair = json.loads(line.strip())
            true_pairs.append(pair)
    return true_pairs




def query_all_valid_data(m, collection_name, target_dir, k):
    target_vec_pkls = os.listdir(target_dir)
    recalls = {}
    # for target in target_vec_pkls:
    for target_js in target_vec_pkls:
        if not target_js.endswith('.json'):
            continue
        # if target.startswith('id2'):
        #     continue
        id_l = []
        target_vec_r = []
        # with open(os.path.join(target_dir, target), 'rb') as load_f:
        #     true_pairs = pkl.load(load_f)
        true_pairs = get_true_pairs(os.path.join(target_dir, target_js))
        for pair in true_pairs:
            id_l.append(pair[0])
            target_vec_r.append(pair[1])
        print(target_js)
        print("query length: ", len(target_vec_r))
        start = time.time()
        results = m.query(np.array(target_vec_r), collection_name, k)
        if results:
            recall = recall_rate(id_l, results)
            recalls[target_js] = [str(round(recall*100, 2)), str(round(time.time()-start, 2)), str(len(target_vec_r))]
    return recalls


def query_tasks_topk(m, collection_name, k, target_dir, dim76 = False):
    count = m.get_count(collection_name)
    print("count in {0}: {1}".format(collection_name, count))

    recalls_7fea = query_all_valid_data(m, collection_name, target_dir, k)
    return recalls_7fea

    


def print_table(collection_name, target_dir, m):
    # recalls_7fea_10, recalls_76fea_10, recalls_76fea_depth5_10 = query_tasks_topk(10, True)
    recalls_7fea_10 = query_tasks_topk(m, collection_name, 10, target_dir, False)
    recalls_7fea_20 = query_tasks_topk(m, collection_name, 20, target_dir, False)
    recalls_7fea_50 = query_tasks_topk(m, collection_name, 50, target_dir, False)
    recalls_7fea_100 = query_tasks_topk(m, collection_name, 100, target_dir, False)
    res_topk = {}
    print(recalls_7fea_10)
    print(recalls_7fea_20)
    print(recalls_7fea_50)
    print(recalls_7fea_100)

    print("top k table")
    for i in recalls_7fea_10:
        res_topk[i] = '{0} & {1}& {2}& {3}& {4}'.format(i, recalls_7fea_10[i][0], recalls_7fea_20[i][0], recalls_7fea_50[i][0], recalls_7fea_100[i][0])
        print(res_topk[i])

    # print("top 10 table")
    # for i in recalls_7fea_10:
    #     if i.startswith('os_diff_linux'):
    #         prefix = i[:15]
    #     elif i.startswith('oplevel_pairs_2'):
    #         prefix = i[:17]
    #     else:
    #         prefix = i[:10]
    #     r = '& ' + recalls_7fea_10[i][0] +'& '
    #     for j in recalls_76fea_10:
    #         if j.startswith(prefix):
    #             r+= recalls_76fea_10[j][0]+'& '
    #             right_j = j
    #     for z in recalls_76fea_depth5_10:
    #         if z.startswith(prefix):
    #             right_z = z
    #             r+= recalls_76fea_depth5_10[z][0]+'& '
    #     r += recalls_7fea_10[i][1] +'& ' + recalls_76fea_10[right_j][1]+'& ' + recalls_76fea_depth5_10[right_z][1]
    #     print(prefix, '  ', r)
    print('---------------------------------')


# def get_lib_cand(target, collection_name, k):
    


if __name__ == '__main__':
    collection_name = 'filtered_database'
    # collection_name = '_7fea_contra_torch_init'
    # id2vec_7fea = '../data/7fea_contra_tf/core_funcs/id2vec.pkl'
    # with open(id2vec_7fea, 'rb') as load_f:
    #     id2vecs = pkl.load(load_f)
    # vecs = []
    # ids = []
    # for id in id2vecs:
    #     ids.append(id)
    #     vecs.append(id2vecs[id])
    m = mil()
    m.milvus.list_collections()
    # m.load_data(np.array(list(id2vecs.values())), list(id2vecs.keys()), collection_name, clear_old=True, metrictype=MetricType.IP)
    
    id2vec_7fea_valid = '../data/validation_pairs/valid_pairs_v1/id_vec/id_vec_7fea/id2vec.pkl'
    with open(id2vec_7fea_valid, 'rb') as load_f:
        id2vecs = pkl.load(load_f)
    # m.load_data(np.array(list(id2vecs.values())), list(id2vecs.keys()), collection_name, clear_old = False, metrictype=MetricType.IP)

    # delete
    # m.delete_entities_by_ids(list(id2vecs.keys()), collection_name)

    # id2vec_l2tol013_7fea_valid = '../data/validation_pairs/valid_pairs_v1/id_vec/id_vec_7fea/id2vec_l2tol013.pkl'
    # with open(id2vec_l2tol013_7fea_valid, 'rb') as load_f:
    #     id2vecs = pkl.load(load_f)
    # m.load_data(list(id2vecs.values()), list(id2vecs.keys()), collection_name, clear_old = False, metrictype=MetricType.IP)
    

    # query
    collection_name = 'filtered_database'
    target_dir = '../data/validation_pairs/valid_pairs_v1/id_vec/id_vec_7fea'
    # m = mil()
    # print_table(collection_name, target_dir, m)



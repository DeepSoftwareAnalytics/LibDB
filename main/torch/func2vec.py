import json
import torch
import numpy as np
import argparse
import os
from torch.autograd import Variable

from utils_loss import graph


class func2vec(object):
    def __init__(self, load_path, gpu, fea_dim) -> None:
        self.gpu = gpu
        self.fea_dim = fea_dim
        if self.gpu:
            self.model = torch.load(load_path).cuda()
        else:
            self.model = torch.load(load_path, map_location='cpu')
        self.model.eval()

    def get_X_mask(self, cur_graph):
        X1_input = np.zeros(
            (1, cur_graph.node_num, len(cur_graph.features[0])))
        mask1 = np.zeros((1, cur_graph.node_num, cur_graph.node_num))
        for u in range(cur_graph.node_num):
            X1_input[0, u, :] = np.array(cur_graph.features[u])
            for v in cur_graph.succss[u]:
                mask1[0, u, v] = 1
        return X1_input, mask1

    def get_item(self, func, func_signature):
        item = {}
        item["src"] = func_signature
        item["n_num"] = func['nodes']
        item['succss'] = func['edgePairs']
        if self.fea_dim == 7:
            item['features'] = func['nodeGeminiVectors']
        else:
            item['features'] = func['nodeGhidraVectors']
        item['fname'] = func_signature
        return item

    def get_graph(self, item):
        cur_graph = graph(item['n_num'], item['fname'], item['src'])
        for u in range(item['n_num']):
            cur_graph.features[u] = np.array(item['features'][u])
            for v in item['succss'][u]:
                cur_graph.add_edge(u, v)
        return cur_graph

    def get_embedding_from_func_graph(self, func_graph):
        X1_input, mask1 = self.get_X_mask(func_graph)
        if self.gpu:
            X1_input, mask1 = torch.from_numpy(X1_input).float().cuda(), torch.from_numpy(mask1).float().cuda()
        else:
            X1_input, mask1 = torch.from_numpy(X1_input).float(), torch.from_numpy(mask1).float()
        vec = self.model.predict(X1_input, mask1)[0]
        return vec

    def get_embedding_from_func_fea(self, func_fea, correct_edges, func_sig=None):
        if correct_edges:
            new_edgePairs = []
            for i in range(func_fea['nodes']):
                new_edgePairs.append([])
            for i in func_fea['edgePairs']:
                if i[1]:
                    new_edgePairs[i[0]].append(i[1])
            func_fea['edgePairs'] = new_edgePairs
        item = self.get_item(func_fea, func_sig)
        func_graph = self.get_graph(item)
        vec = self.get_embedding_from_func_graph(func_graph)
        return vec

    def get_embeddings_from_func_fea_l(self, func_fea_l, correct_edges, func_sig=None):
        func_gs = []
        for func_fea  in func_fea_l:
            if correct_edges:
                new_edgePairs = []
                for i in range(len(func_fea['nodesAsm'])):
                    new_edgePairs.append([])
                for i in func_fea['edgePairs']:
                    if i[1]:
                        new_edgePairs[i[0]].append(i[1])
                func_fea['edgePairs'] = new_edgePairs
            item = self.get_item(func_fea, func_sig)
            func_graph = self.get_graph(item)
            func_gs.append(func_graph)
        maxN = 0
        for g in func_gs:
            maxN = max(maxN, g.node_num)
        fea_dim = len(g.features[0])
        X_input = np.zeros((len(func_gs), maxN, fea_dim))
        node_mask = np.zeros((len(func_gs), maxN, maxN))
        for i in range(len(func_gs)):
            g = func_gs[i]
            for u in range(g.node_num):
                X_input[i, u, :] = np.array(g.features[u])
                for v in g.succss[u]:
                    node_mask[i, u, v] = 1
        if self.gpu:
            X_input, mask = torch.from_numpy(X_input).float().cuda(), torch.from_numpy(node_mask).float().cuda()
        else:
            X_input, mask = torch.from_numpy(X_input).float(), torch.from_numpy(node_mask).float()
        with torch.no_grad():
            vecs = self.model.predict(X_input, mask)
        return vecs
                

    def get_vecs_from_bin_fea(self, bin_fea, correct_edges):
        res = {}
        for func in bin_fea['binFileFeature']['functions']:
            if func['nodes'] < 5:
                continue
            if func['isThunkFunction'] is True or 'text' not in func['memoryBlock']:
                continue
            key = func['entryPoint']
            vec = self.get_embedding_from_func_fea(
                func, correct_edges, func_sig=key)
            res[key] = vec
        return res

    def get_vecs_from_package_fea(self, package_fea, correct_edges):
        res = {}
        for bin_fea in package_fea:
            if 'binFileFeature' not in bin_fea:
                res[bin_fea['formattedFileName']] = {}
            res[bin_fea['formattedFileName']] = self.get_vecs_from_bin_fea(
                bin_fea, correct_edges)
        return res

    def get_vecs_from_package_fea_json(self, package_fea_json, correct_edges):
        with open(package_fea_json, 'r') as load_f:
            package_fea = json.load(load_f)
        return self.get_vecs_from_package_fea(package_fea, correct_edges)


if __name__ == '__main__':
    ## test

    args = parser.parse_args()
    NODE_FEATURE_DIM = args.fea_dim
    EMBED_DIM = args.embed_dim
    EMBED_DEPTH = args.embed_depth
    OUTPUT_DIM = args.output_dim
    ITERATION_LEVEL = args.iter_level
    LEARNING_RATE = args.lr
    MAX_EPOCH = args.epoch
    BATCH_SIZE = args.batch_size
    NEG_BATCH_SIZE = args.neg_batch_size
    LOAD_PATH = args.load_path
    SAVE_PATH = args.save_path
    LOG_PATH = args.log_path
    DEVICE = args.use_device
    WORKERS = args.workers

    func2vec_mod = func2vec('../data/saved_model/graphnn_model_7fea_contra_cos_torch/model-inter-best.pt')
    package_fea_json = '/raid/data/CoreFedoraFeatureJson0505/00/00/9210000/9210000.json'
    res = func2vec_mod.get_vecs_from_package_fea_json(package_fea_json, True, False)
    
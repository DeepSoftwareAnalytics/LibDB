import numpy as np
from sklearn.metrics import auc, roc_curve
import json
import os
from collections import deque
import time

from multiprocessing import Process,Queue


def get_f_name(DATA, SF, CM, OP, VS):
    F_NAME = []
    for sf in SF:
        for cm in CM:
            for op in OP:
                for vs in VS:
                    F_NAME.append(DATA+sf+cm+op+vs+".json")
    return F_NAME


def get_f_name(DATA):
    F_PATH = []
    for f_name in os.listdir(DATA):
        if f_name.startswith('arm_x86') or f_name.startswith('linux_gcc_5') or f_name.startswith('linux_gcc_6') or f_name.startswith('linux_gcc_6') or f_name.startswith('linux_gcc_7') or f_name.startswith('linux_gcc_8') or f_name.startswith('mac_gcc_8'):
            continue
        # if not f_name.startswith('mac_gcc_8_O'):
        #     continue
        F_PATH.append(os.path.join(DATA, f_name))
    return F_PATH


def get_f_dict(F_NAME):
    name_num = 0
    name_dict = {}
    for f_name in F_NAME:
        with open(f_name) as inf:
            for line in inf:
                g_info = json.loads(line.strip())
                if (g_info['fname'] not in name_dict):
                    name_dict[g_info['fname']] = name_num
                    name_num += 1
    return name_dict


class graph(object):
    def __init__(self, node_num=0, label=None, name=None):
        self.node_num = node_num
        self.label = label
        self.name = name
        self.features = []
        self.succss = []
        self.preds = []
        if (node_num > 0):
            for i in range(node_num):
                self.features.append([])
                self.succss.append([])
                self.preds.append([])

    def add_node(self, feature=[]):
        self.node_num += 1
        self.features.append(feature)
        self.succss.append([])
        self.preds.append([])

    def add_edge(self, u, v):
        self.succss[u].append(v)
        self.preds[v].append(u)

    def toString(self):
        ret = '{} {}\n'.format(self.node_num, self.label)
        for u in range(self.node_num):
            for fea in self.features[u]:
                ret += '{} '.format(fea)
            ret += str(len(self.succss[u]))
            for succ in self.succss[u]:
                ret += ' {}'.format(succ)
            ret += '\n'
        return ret


def read_graph(F_NAME, FUNC_NAME_DICT, FEATURE_DIM):
    graphs = []
    classes = []
    if FUNC_NAME_DICT != None:
        for f in range(len(FUNC_NAME_DICT)):
            classes.append([])

    for f_name in F_NAME:
        with open(f_name) as inf:
            for line in inf:
                g_info = json.loads(line.strip())
                label = FUNC_NAME_DICT[g_info['fname']]
                classes[label].append(len(graphs))
                cur_graph = graph(g_info['n_num'], label, g_info['src'])
                for u in range(g_info['n_num']):
                    cur_graph.features[u] = np.array(g_info['features'][u])
                    for v in g_info['succss'][u]:
                        cur_graph.add_edge(u, v)
                graphs.append(cur_graph)
    return graphs, classes


def partition_data(Gs, classes, partitions, perm):
    C = len(classes)
    st = 0.0
    ret = []
    for part in partitions:
        cur_g = []
        cur_c = []
        ed = st + part * C
        for cls in range(int(st), int(ed)):
            prev_class = classes[perm[cls]]
            cur_c.append([])
            for i in range(len(prev_class)):
                cur_g.append(Gs[prev_class[i]])
                cur_g[-1].label = len(cur_c)-1
                cur_c[-1].append(len(cur_g)-1)

        ret.append(cur_g)
        ret.append(cur_c)
        st = ed

    return ret


def generate_epoch_pair(Gs, classes, M, train, output_id=False, load_id=None):
    epoch_data = []
    if train:
        perm = np.random.permutation(len(Gs))
    else:
        perm = range(len(Gs))
    st = 0
    while st < len(Gs):
        X1, X2, X3, m1, m2, m3 = generate_batch_pairs(Gs, classes, M, st, perm)
        epoch_data.append((X1, X2, X3, m1, m2, m3))
        st += M

    return epoch_data


def generate_batch_pairs(Gs, classes, M, st, perm):
    X1, X2, X3, m1, m2, m3 = get_pair(Gs, classes, M, st=st, perm=perm)
    return X1, X2, X3, m1, m2, m3


def get_pair(Gs, classes, M, st, perm, output_id=False, load_id=None):
    if load_id is None:
        C = len(classes)
        if (st + M > len(perm)):
            M = len(perm) - st
        ed = st + M
        triple_ids = []  # [(G_0, G_p, G_n)]
        p_funcs = []
        true_pairs = []
        n_ids = []

        for g_id in perm[st:ed]:
            g0 = Gs[g_id]
            cls = g0.label
            p_funcs.append(cls)
            tot_g = len(classes[cls])
            if (len(classes[cls]) >= 2):
                p_id = classes[cls][np.random.randint(tot_g)]
                while g_id == p_id:
                    p_id = classes[cls][np.random.randint(tot_g)]
                true_pairs.append((g_id, p_id))
    else:
        triple_ids = load_id[0]

    M = len(true_pairs)
    neg_batch = M
    for i in range(neg_batch):
        n_cls = np.random.randint(C)
        while (len(classes[n_cls]) == 0) or (n_cls in p_funcs):
            n_cls = np.random.randint(C)
        tot_g2 = len(classes[n_cls])
        n_id = classes[n_cls][np.random.randint(tot_g2)]
        n_ids.append(n_id)
    maxN1 = 0
    maxN2 = 0
    maxN3 = 0
    for pair in true_pairs:
        maxN1 = max(maxN1, Gs[pair[0]].node_num)
        maxN2 = max(maxN2, Gs[pair[1]].node_num)
    for id in n_ids:
        maxN3 = max(maxN3, Gs[id].node_num)
    feature_dim = len(Gs[0].features[0])
    X1_input = np.zeros((M, maxN1, feature_dim))
    X2_input = np.zeros((M, maxN2, feature_dim))
    X3_input = np.zeros((neg_batch, maxN3, feature_dim))
    node1_mask = np.zeros((M, maxN1, maxN1))
    node2_mask = np.zeros((M, maxN2, maxN2))
    node3_mask = np.zeros((neg_batch, maxN3, maxN3))

    for i in range(len(true_pairs)):
        g1 = Gs[true_pairs[i][0]]
        g2 = Gs[true_pairs[i][1]]
        
        for u in range(g1.node_num):
            X1_input[i, u, :] = np.array(g1.features[u])
            for v in g1.succss[u]:
                node1_mask[i, u, v] = 1
        for u in range(g2.node_num):
            X2_input[i, u, :] = np.array(g2.features[u])
            for v in g2.succss[u]:
                node2_mask[i, u, v] = 1

    for i in range(len(n_ids)):
        g3 = Gs[n_ids[i]]
        for u in range(g3.node_num):
            X3_input[i, u, :] = np.array(g3.features[u])
            for v in g3.succss[u]:
                node3_mask[i, u, v] = 1
    if output_id:
        return X1_input, X2_input, X3_input, node1_mask, node2_mask, node3_mask, triple_ids
    else:
        return X1_input, X2_input, X3_input, node1_mask, node2_mask, node3_mask

def f(queue,i_l,i_h,graphs, classes, batch_size, perm):
        l = i_h - i_l
        for i in range(int(l/batch_size)):
            t = get_pair(graphs, classes, batch_size, st=i_l+i*batch_size, perm=perm)
            queue.put(t)

def train_epoch(model, graphs, classes, batch_size, load_data=None):
    count = 0
    cum_loss = 0.0

    perm = np.random.permutation(len(graphs))
    st = 0
    while(st + batch_size < len(graphs)):
        X1, X2, X3, m1, m2, m3 = generate_batch_pairs(
            graphs, classes, batch_size, st, perm)
        st += batch_size
        if len(X1) == 0:
            continue
        loss = model.train(X1, X2, X3, m1, m2, m3)
        cum_loss += loss
        count += 1

    # queue = Queue(maxsize=10)
    # Process_num=6
    # for i in range(Process_num):
    #     print(i,'start')
    #     ii = int((len(graphs) - batch_size)/Process_num)
    #     t = Process(target=f,args=(queue, i*ii,(i+1)*ii, graphs, classes, batch_size, perm))
    #     t.start()
    # print(int(len(graphs) /batch_size))
    # for j in range(int(len(graphs) /batch_size)):
    #     print(j)
    #     t=queue.get()
    #     print("q size:", queue.qsize())
    #     if len(t[0]) == 0:
    #         continue
    #     loss = model.train(t[0], t[1], t[2], t[3], t[4], t[5])
    #     cum_loss += loss
    #     count += 1
    return cum_loss / count


def get_loss(model, graphs, classes, batch_size, load_data=None):
    count = 0
    cum_loss = 0.0
    perm = range(len(graphs))

    # queue = Queue(maxsize=5)
    # Process_num=3
    # for i in range(Process_num):
    #     print(i,'start')
    #     ii = int((len(graphs)  - batch_size)/Process_num)
    #     t = Process(target=f,args=(queue, i*ii,(i+1)*ii, graphs, classes, batch_size, perm))
    #     t.start()
    # print(int(len(graphs) /batch_size))
    # for j in range(int(len(graphs) /batch_size)):
    #     print(j)
    #     t=queue.get()
    #     if len(t[0]) == 0:
    #         continue
    #     loss = model.calc_loss(t[0], t[1], t[2], t[3], t[4], t[5])
    #     cum_loss += loss
    #     count += 1


    st = 0
    while(st + batch_size < len(graphs)):
        X1, X2, X3, m1, m2, m3 = generate_batch_pairs(
            graphs, classes, batch_size, st, perm)
        st += batch_size
        if len(X1) == 0:
            continue
        loss = model.calc_loss(X1, X2, X3, m1, m2, m3)
        cum_loss += loss
        count += 1
    return cum_loss / count

# def get_auc_epoch_batch(model, graphs, classes, batch_size):
#     tot_diff = []
#     tot_truth = []
#     st = 0
#     perm = range(len(graphs))
#     while(st < len(graphs)):
#         X1, X2, X3, m1, m2, m3 = generate_batch_pairs(
#             graphs, classes, batch_size, st, perm)
#         st += batch_size
#         if len(X1) == 0:
#             continue
#         diff_p = model.calc_diff(X1, X2, m1, m2)
#         diff_n = model.calc_diff(X1, X3, m1, m3)
#         tot_diff += list(diff_p) + list(diff_n)
#         y_p = np.ones(len(diff_p))
#         y_n = np.zeros(len(diff_n))
#         tot_truth += list(y_n > 0) + list(y_p > 0)

#     diff = np.array(tot_diff)
#     truth = np.array(tot_truth)

#     fpr, tpr, thres = roc_curve(truth, diff)
#     model_auc = auc(fpr, tpr)
#     return model_auc, fpr, tpr, thres



class SequenceData():
    def __init__(self, graphs, classes, batch_size, perm):
        self.graphs = graphs
        self.classes = classes
        self.batch_size = batch_size
        self.perm = perm
        self.L = len(self.graphs) 
        self.queue = Queue(maxsize=30)
        
        self.Process_num=3
        for i in range(self.Process_num):
            print(i,'start')
            ii = int(self.__len__()/self.Process_num)
            t = Process(target=self.f,args=(i*ii,(i+1)*ii))
            t.start()
    def __len__(self):
        return self.L - self.batch_size
    def __getitem__(self, st):
        X1, X2, X3, m1, m2, m3 = get_pair(self.graphs, self.classes, self.batch_size, st=st, perm=self.perm)
        return X1, X2, X3, m1, m2, m3
    
    def f(self,i_l,i_h):
        l = i_h - i_l
        for i in range(int(l/self.batch_size)):
            t = self.__getitem__(i_l+i*self.batch_size)
            self.queue.put(t)

    # def gen(self):
    #     while 1:
    #         t = self.queue.get()
    #         yield t[0],t[1],t[2],t[3]



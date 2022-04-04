import torch
from torch.utils.data import Dataset, DataLoader
from numpy.random import choice as npc
import numpy as np


class dataset(Dataset):

    def __init__(self, Gs, classes, batch_size, neg_batch, neg_batch_flag, train):
        super(dataset, self).__init__()
        np.random.seed(0)
        self.Gs = Gs
        self.classes = classes
        self.batch_size = batch_size
        self.neg_batch = neg_batch
        if train:
            self.perm = np.random.permutation(len(self.Gs))
        else:
            self.perm = range(len(Gs))
        self.neg_batch_flag = neg_batch_flag

    def __len__(self):
        return len(self.Gs) / self.batch_size
    
    def shuffle(self):
        self.perm = np.random.permutation(len(self.Gs))

    def get_pair(self, st, neg_batch_flag, output_id=False, load_id=None):
        if load_id is None:
            C = len(self.classes)
            if (st + self.batch_size > len(self.perm)):
                M = len(self.perm) - st
            else:
                M = self.batch_size
            ed = st + M
            triple_ids = []  # [(G_0, G_p, G_n)]
            p_funcs = []
            true_pairs = []
            n_ids = []

            for g_id in self.perm[st:ed]:
                g0 = self.Gs[g_id]
                cls = g0.label
                p_funcs.append(cls)
                tot_g = len(self.classes[cls])
                if (len(self.classes[cls]) >= 2):
                    p_id = self.classes[cls][np.random.randint(tot_g)]
                    while g_id == p_id:
                        p_id = self.classes[cls][np.random.randint(tot_g)]
                    true_pairs.append((g_id, p_id))
        else:
            triple_ids = load_id[0]
        if not neg_batch_flag:
            M = len(true_pairs)
            self.neg_batch = M
        for i in range(self.neg_batch):
            n_cls = np.random.randint(C)
            while (len(self.classes[n_cls]) == 0) or (n_cls in p_funcs):
                n_cls = np.random.randint(C)
            tot_g2 = len(self.classes[n_cls])
            n_id = self.classes[n_cls][np.random.randint(tot_g2)]
            n_ids.append(n_id)
        maxN1 = 0
        maxN2 = 0
        maxN3 = 0
        for pair in true_pairs:
            maxN1 = max(maxN1, self.Gs[pair[0]].node_num)
            maxN2 = max(maxN2, self.Gs[pair[1]].node_num)
        for id in n_ids:
            maxN3 = max(maxN3, self.Gs[id].node_num)
        feature_dim = len(self.Gs[0].features[0])
        X1_input = np.zeros((M, maxN1, feature_dim))
        X2_input = np.zeros((M, maxN2, feature_dim))
        X3_input = np.zeros((self.neg_batch, maxN3, feature_dim))
        node1_mask = np.zeros((M, maxN1, maxN1))
        node2_mask = np.zeros((M, maxN2, maxN2))
        node3_mask = np.zeros((self.neg_batch, maxN3, maxN3))

        for i in range(len(true_pairs)):
            g1 = self.Gs[true_pairs[i][0]]
            g2 = self.Gs[true_pairs[i][1]]
            
            for u in range(g1.node_num):
                X1_input[i, u, :] = np.array(g1.features[u])
                for v in g1.succss[u]:
                    node1_mask[i, u, v] = 1
            for u in range(g2.node_num):
                X2_input[i, u, :] = np.array(g2.features[u])
                for v in g2.succss[u]:
                    node2_mask[i, u, v] = 1

        for i in range(len(n_ids)):
            g3 = self.Gs[n_ids[i]]
            for u in range(g3.node_num):
                X3_input[i, u, :] = np.array(g3.features[u])
                for v in g3.succss[u]:
                    node3_mask[i, u, v] = 1
        if output_id:
            return X1_input, X2_input, X3_input, node1_mask, node2_mask, node3_mask, triple_ids
        else:
            return X1_input, X2_input, X3_input, node1_mask, node2_mask, node3_mask

    def __getitem__(self, index):
        X1, X2, X3, m1, m2, m3 = self.get_pair(index * self.batch_size, neg_batch_flag=self.neg_batch_flag)
        return torch.from_numpy(X1).float(), torch.from_numpy(X2).float(), torch.from_numpy(X3).float(), torch.from_numpy(m1).float(), torch.from_numpy(m2).float(), torch.from_numpy(m3).float()
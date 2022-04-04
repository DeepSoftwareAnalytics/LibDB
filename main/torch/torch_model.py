from numpy.core.fromnumeric import repeat
import torch
from torch.autograd import Variable
import torch.nn as nn
import torch.nn.functional as F

import numpy as np

def truncated_normal_(tensor,mean=0,std=0.1):
    with torch.no_grad():
        size = tensor.shape
        tmp = tensor.new_empty(size+(4,)).normal_()
        valid = (tmp < 2) & (tmp > -2)
        ind = valid.max(-1, keepdim=True)[1]
        tensor.data.copy_(tmp.gather(-1, ind).squeeze(-1))
        tensor.data.mul_(std).add_(mean)
        return tensor

class graphnn(nn.Module):

    def __init__(self, N_x_feadim7, N_embed_outdim64, N_o, Wembed_depth, iter_level):
        super(graphnn, self).__init__()
        self.zero = torch.tensor(0.0).cuda()
        self.N_x_feadim7 = N_x_feadim7
        self.N_embed_outdim64 = N_embed_outdim64
        self.N_o = N_o
        self.Wembed_depth = Wembed_depth
        self.iter_level = iter_level
        
        self.node_val = nn.Linear(self.N_x_feadim7, self.N_embed_outdim64, False)
        truncated_normal_(self.node_val.weight)
        self.Wembed0 = nn.Linear(self.N_embed_outdim64, self.N_embed_outdim64, False)
        truncated_normal_(self.Wembed0.weight)
        self.Wembed1 = nn.Linear(self.N_embed_outdim64, self.N_embed_outdim64, False)
        truncated_normal_(self.Wembed1.weight)
        # for i in range(self.Wembed_depth):
        
        #     self.Wembed.append()
        self.re = nn.ReLU(inplace=True)
        self.ta = nn.Tanh()

        self.cos1 = nn.CosineSimilarity(dim=1, eps=1e-10)
        self.cos2 = nn.CosineSimilarity(dim=2, eps=1e-10)

        self.out = nn.Linear(self.N_embed_outdim64, self.N_o)
        truncated_normal_(self.out.weight)
        torch.nn.init.constant_(self.out.bias, 0)

    def predict(self, x, msg_mask):
        return self.forward_once(x, msg_mask)

    def forward_once(self, x, msg_mask):
        node_embed = torch.reshape(self.node_val(torch.reshape(x, [-1, self.N_x_feadim7])), [x.shape[0], -1, self.N_embed_outdim64])
        cur_msg = self.re(node_embed)
        for t in range(self.iter_level):
            Li_t = torch.matmul(msg_mask, cur_msg)
            cur_info = torch.reshape(Li_t, [-1, self.N_embed_outdim64])
            # for i in range(self.Wembed_depth-1):
            
            cur_info = self.re(self.Wembed0(cur_info))
            cur_info = self.Wembed1(cur_info)

            neigh_val_t = torch.reshape(cur_info, Li_t.shape)
            tot_val_t = node_embed + neigh_val_t
            tot_msg_t = self.ta(tot_val_t)
            cur_msg = tot_msg_t
        g_embed = torch.sum(cur_msg, 1)
        output = self.out(g_embed)
        return output

    def forward(self, X1, X2, X3, m1, m2, m3):
        embed1 = self.forward_once(X1, m1)
        embed2 = self.forward_once(X2, m2)
        embed3 = self.forward_once(X3, m3)


        # triple l2 distance, neg batch N, N>batch size
        # dist_p = torch.sum((embed1-embed2) ** 2, 1)
        # dist_n = torch.sum((embed1.reshape(embed1.shape[0], 1, embed1.shape[1]) - embed3).reshape(embed1.shape[0]*embed3.shape[0], embed1.shape[1]) ** 2, 1)
        # all_loss = torch.maximum(dist_p - torch.min(dist_n.reshape(embed1.shape[0], embed3.shape[0]), 1).values + 0.5, torch.tensor(0.0).cuda())

        # old method to delete, neg batch N, N>batch size
        # dist_n = torch.sum((torch.repeat_interleave(embed1, embed3.shape[0], 0)- embed3.repeat(embed1.shape[0], 1)) ** 2, 1)
        # all_loss = torch.max(torch.reshape(torch.maximum(torch.repeat_interleave(dist_p, embed3.shape[0], axis=0) - dist_n + 0.5, torch.tensor(0.0).cuda()), [embed1.shape[0], -1]), 1).values

        # triple cos similarity, neg batch N, N>batch size
        # cos_dist_p = self.cos1(embed1, embed2)
        # cos_dist_n = self.cos2(embed1.reshape(embed1.shape[0], 1, embed1.shape[1]), embed3.reshape(1, embed3.shape[0], embed3.shape[1]))
        # all_loss = torch.maximum(torch.max(cos_dist_n, 1).values - cos_dist_p + 0.1, self.zero)
        # loss = torch.mean(all_loss)
        # return loss, cos_dist_p, torch.max(cos_dist_n, 1).values

        # triple cos similarity, neg batch N, N>batch size, mean cos_dist_n
        # cos_dist_p = self.cos1(embed1, embed2)
        # cos_dist_n = self.cos2(embed1.reshape(embed1.shape[0], 1, embed1.shape[1]), embed3.reshape(1, embed3.shape[0], embed3.shape[1]))
        # all_loss = torch.maximum((cos_dist_n - cos_dist_p.reshape(cos_dist_p.shape[0], 1)).reshape(-1) + 0.5, self.zero)
        # loss = torch.mean(all_loss)
        # return loss, cos_dist_p, self.cos1(embed1, embed3)

        # triple cos sim, non-neg_batch
        # cos_dist_p = self.cos1(embed1, embed2)
        # cos_dist_n = self.cos1(embed1, embed3)
        # all_loss = torch.maximum(cos_dist_n - cos_dist_p + 0.5, self.zero)
        # loss = torch.mean(all_loss)

        # contrastive loss
        cos_dist_p = self.cos1(embed1, embed2)
        cos_dist_n = self.cos1(embed1, embed3)
        loss = (torch.mean((1-cos_dist_p)**2) + torch.mean((cos_dist_n+1)**2)) / 2    
        return loss, cos_dist_p, cos_dist_n

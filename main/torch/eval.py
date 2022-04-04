import tensorflow.compat.v1 as tf
print(tf.__version__)
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from graphnnSiamese import graphnn
from utils_valid import *
import os
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument('--device', type=str, default='0,1,2,3',
        help='visible gpu device')
parser.add_argument('--use_device', type=str, default='/gpu:1',
        help='used gpu device')
parser.add_argument('--fea_dim', type=int, default=7,
        help='feature dimension')
parser.add_argument('--embed_dim', type=int, default=64,
        help='embedding dimension')
parser.add_argument('--embed_depth', type=int, default=5,
        help='embedding network depth')
parser.add_argument('--output_dim', type=int, default=64,
        help='output layer dimension')
parser.add_argument('--iter_level', type=int, default=5,
        help='iteration times')
parser.add_argument('--lr', type=float, default=1e-4,
        help='learning rate')
parser.add_argument('--epoch', type=int, default=100,
        help='epoch number')
parser.add_argument('--batch_size', type=int, default=128,
        help='batch size')
parser.add_argument('--load_path', type=str,
        default='./saved_model/graphnn-model_best',
        help='path for model loading, "#LATEST#" for the latest checkpoint')
parser.add_argument('--log_path', type=str, default=None,
        help='path for training log')

def get_true_pairs(js_path):
    true_pairs = []
    with open(js_path) as load_f:
        for line in load_f:
            pair = json.loads(line.strip())
            true_pairs.append(pair)
    return true_pairs


def eval(fea_dim, model_load_path, t_pairs_path, use_device, thres):
    args = parser.parse_args()
    args.dtype = tf.float32
    print("=================================")
    print(args)
    print("=================================")
    Dtype = args.dtype
    NODE_FEATURE_DIM = args.fea_dim
    EMBED_DIM = args.embed_dim
    EMBED_DEPTH = args.embed_depth
    OUTPUT_DIM = args.output_dim
    ITERATION_LEVEL = args.iter_level
    LEARNING_RATE = args.lr
    MAX_EPOCH = args.epoch
    BATCH_SIZE = args.batch_size
    LOAD_PATH = args.load_path
    LOG_PATH = args.log_path
    DEVICE = args.use_device

    NODE_FEATURE_DIM = fea_dim
    os.environ["CUDA_VISIBLE_DEVICES"]=args.device
    LOAD_PATH = model_load_path
    DEVICE = use_device

    t_pairs = get_true_pairs(t_pairs_path)
    print("true pairs: ", len(t_pairs))


    # Model
    gnn = graphnn(
            N_x = NODE_FEATURE_DIM,
            Dtype = Dtype, 
            N_embed = EMBED_DIM,
            depth_embed = EMBED_DEPTH,
            N_o = OUTPUT_DIM,
            ITER_LEVEL = ITERATION_LEVEL,
            lr = LEARNING_RATE,
            device = DEVICE
        )
    gnn.init(LOAD_PATH, LOG_PATH)

    recall = get_recall_epoch_batch(gnn, t_pairs, BATCH_SIZE, thres)
    gnn.say("recall rate = {0} @ {1}".format(recall, datetime.now()))
    print(recall)
    return recall
#     print(max((1-fpr+tpr)/2))
#     index = np.argmax((1-fpr+tpr)/2)
#     print("index:", index)
#     print("fpr", fpr[index])
#     print("tpr", tpr[index])
#     print(thres[index])


if __name__ == '__main__':
    thres7 = 0.7367
#     thres76 = 0.7482
    thres76 = 0.7532
    
    model_7_fea_dim = '../data/saved_model/graphnn_model_gemini/graphnn_model_gemini_best'
#     model_76_fea_dim = '../data/saved_model/graphnn_model_ghidra/saved_ghidra_model_best'
    model_76_fea_dim = '../data/saved_model/graphnn_model_ghidra_depth5/graphnn_model_ghidra_best'

    gpu_device = '/gpu:3'

    pairs_7_fea_dim_dir = '../data/validation_pairs/valid_pairs_v1/7_fea_dim'
    pair_fs = os.listdir(pairs_7_fea_dim_dir)
    res7 = {}
#     for f in pair_fs:
#         recall7 = eval(7, model_7_fea_dim, os.path.join(pairs_7_fea_dim_dir, f), gpu_device, thres7)
#         res7[f] = recall7

    pairs_76_fea_dim_dir = '../data/validation_pairs/valid_pairs_v1/76_fea_dim'
    pair_fs = os.listdir(pairs_76_fea_dim_dir)
    res76 = {}
    for f in pair_fs:
        if f != 'cc_version_diff_76_fea_dim.json':
            continue
        recall76 = eval(76, model_76_fea_dim, os.path.join(pairs_76_fea_dim_dir, f), gpu_device, thres76)
        res76[f] = recall76

#     print("recall:")
#     for i in res7:
#         print(i, "    ", res7[i])

    for i in res76:
        print(i, "    ", res76[i])
    
#     plt.figure()
#     plt.title('ROC CURVE')
#     plt.xlabel('False Positive Rate')
#     plt.ylabel('True Positive Rate')
#     plt.plot(fpr7,tpr7,color='b')
#     plt.plot(fpr76, tpr76,color='r')
# #     plt.plot([0, 1], [0, 1], color='m', linestyle='--')
#     plt.savefig('auc.png')


    
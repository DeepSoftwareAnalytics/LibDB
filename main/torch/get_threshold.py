import tensorflow.compat.v1 as tf
print(tf.__version__)
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from graphnnSiamese import graphnn
from utils import *
import os
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument('--device', type=str, default='0,1,2,3',
        help='visible gpu device')
parser.add_argument('--use_device', type=str, default='/gpu:1',
        help='used gpu device')
parser.add_argument('--fea_dim', type=int, default=76,
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
# parser.add_argument('--load_path', type=str,
        # default='../data/saved_model/graphnn_model_ghidra/saved_ghidra_model_best',
        # help='path for model loading, "#LATEST#" for the latest checkpoint')
parser.add_argument('--load_path', type=str,
        default='../data/saved_model/graphnn_model_ghidra_depth5/graphnn_model_ghidra_best',
        help='path for model loading, "#LATEST#" for the latest checkpoint')
parser.add_argument('--log_path', type=str, default=None,
        help='path for training log')




if __name__ == '__main__':
    args = parser.parse_args()
    args.dtype = tf.float32
    print("=================================")
    print(args)
    print("=================================")

    os.environ["CUDA_VISIBLE_DEVICES"]=args.device
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

    SHOW_FREQ = 1
    TEST_FREQ = 1
    SAVE_FREQ = 5
    # DATA_FILE_NAME_VALID = '../data/validation_arm2non_arm_gemini_data/'
    DATA_FILE_NAME_TRAIN_TEST = '../data/vector_deduplicate_ghidra_format_less_compilation_cases/train_test'
    F_PATH_TRAIN_TEST = get_f_name(DATA_FILE_NAME_TRAIN_TEST)
    FUNC_NAME_DICT_TRAIN_TEST = get_f_dict(F_PATH_TRAIN_TEST)

    print("start reading data")
    Gs_train_test, classes_train_test = read_graph(F_PATH_TRAIN_TEST, FUNC_NAME_DICT_TRAIN_TEST, NODE_FEATURE_DIM)
    print("train and test ---- 8:2")
    print("{} graphs, {} functions".format(len(Gs_train_test), len(classes_train_test)))
    
    perm = np.random.permutation(len(classes_train_test))
    Gs_train, classes_train, Gs_test, classes_test =\
            partition_data(Gs_train_test, classes_train_test, [0.8, 0.2], perm)
    print("Train: {} graphs, {} functions".format(
            len(Gs_train), len(classes_train)))
    print("Test: {} graphs, {} functions".format(
            len(Gs_test), len(classes_test)))


    print("valid")
    DATA_FILE_NAME_VALID = '../data/vector_deduplicate_ghidra_format_less_compilation_cases/valid'
    F_PATH_VALID = get_f_name(DATA_FILE_NAME_VALID)
    FUNC_NAME_DICT_VALID = get_f_dict(F_PATH_VALID)
    Gs_valid, classes_valid = read_graph(F_PATH_VALID, FUNC_NAME_DICT_VALID, NODE_FEATURE_DIM)
    print("{} graphs, {} functions".format(len(Gs_valid), len(classes_valid)))
    Gs_valid, classes_valid = partition_data(Gs_valid, classes_valid, [1], list(range(len(classes_valid))))



    

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

    auc0, fpr0, tpr0, thres0 = get_auc_epoch_batch(gnn, Gs_train, classes_train,
            BATCH_SIZE)
    gnn.say("Initial training auc = {0} @ {1}".format(auc0, datetime.now()))

    print(auc0)
    print(max((1-fpr0+tpr0)/2))
    index = np.argmax((1-fpr0+tpr0)/2)
    print("index:", index)
    print("fpr", fpr0[index])
    print("tpr", tpr0[index])
    print(thres0[index])


    auc1, fpr1, tpr1, thres1 = get_auc_epoch_batch(gnn, Gs_test, classes_test,
            BATCH_SIZE)
    gnn.say("Initial testing auc = {0} @ {1}".format(auc1, datetime.now()))

    print(auc1)
    print(max((1-fpr1+tpr1)/2))
    index = np.argmax(1-fpr1+tpr1)
    print("index:", index)
    print("fpr", fpr1[index])
    print("tpr", tpr1[index])
    print(thres1[index])


    auc2, fpr2, tpr2, thres2 = get_auc_epoch_batch(gnn, Gs_valid, classes_valid,
            BATCH_SIZE)
    gnn.say("Initial validation auc = {0} @ {1}".format(auc2, datetime.now()))

    print(auc2)
    print(max((1-fpr2+tpr2)/2))
    index = np.argmax((1-fpr2+tpr2)/2)
    print("index:", index)
    print("fpr", fpr2[index])
    print("tpr", tpr2[index])
    print(thres2[index])

    plt.figure()
    plt.title('ROC CURVE')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.plot(fpr1,tpr1,color='b')
    plt.plot(fpr1, 1-fpr1+tpr1, color='b')
    plt.plot(fpr2, tpr2,color='r')
    plt.plot(fpr2, 1-fpr2+tpr2, color='r')
#     plt.plot([0, 1], [0, 1], color='m', linestyle='--')
    plt.savefig('auc_depth5.png')
import argparse
import pickle as pkl
from utils import *
from milvus_mod import mil
from milvus import MetricType
import os
from func2vec import func2vec
from function_vector_channel import com2bins
import copy
import time
import uuid
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument('--model', type=str, default='7fea_contra_torch_b128',
                    help='network model')
parser.add_argument('--fea_dim', type=int, default=7,
                    help='feature dimension')
parser.add_argument('--load_path', type=str, default='../data/{0}/saved_model/model-inter-best.pt',
                    help='path for model loading, "#LATEST#" for the latest checkpoint')
parser.add_argument('--base_result', type=str, default='../data/detection/base/base_result_b2sfinder_rule.json',
                    help='result of base matching method')
parser.add_argument('--id2key', type=str, default='../data/{0}/core_funcs/id2key.pkl',
                    help='id to key')
parser.add_argument('--id2vec', type=str, default='../data/{0}/core_funcs/id2vec.pkl',
                    help='id to vec')
parser.add_argument('--pid2bin2vecid', type=str, default='../data/{0}/pid2bin2vecid.pkl',
                    help='dict:pid to bin to vecid')
parser.add_argument('--test_app_dir', type=str,
                    default='../data/detection_targets/features/osspolice/oss_featureJson', help='test data path')
parser.add_argument('--bin2func_num', type=str,
                    default='../data/bin2func_num.pkl', help='function numbers of binaries')
parser.add_argument('--bin2fcgs', type=str,
                    default='../data/funcs_fcg.pkl', help='fcgs of binaries')
parser.add_argument('--id2package', type=str,
                    default='../data/pid2package.json', help='')
parser.add_argument('--k', type=int,
                    default=1, help='topk')
parser.add_argument('--fs_thres', type=float,
                    default=0.8, help='threshold to decide similar functions')


ARGS = parser.parse_args()

print(datetime.now())

MODEL = ARGS.model
id2keys = read_pkl(ARGS.id2key.format(MODEL))
base_results = read_json(ARGS.base_result)
all_id2vecs = read_pkl(ARGS.id2vec.format(MODEL))
bin2func_num = read_pkl(ARGS.bin2func_num)
bin2fcgs = read_pkl(ARGS.bin2fcgs)
id2package = read_json(ARGS.id2package)
pid2bin2vecid = read_pkl(ARGS.pid2bin2vecid.format(MODEL))
TEST_APP_DIR = ARGS.test_app_dir
k = ARGS.k
fs_thres = ARGS.fs_thres

m = mil()
net = func2vec(ARGS.load_path.format(MODEL), gpu=True, fea_dim=ARGS.fea_dim)
base_afcg_result =  {}

for app in base_results:
    print(datetime.now())
    if app == 'net.avs234_16':
        continue
    print(app)
    base_afcg_result[app] = {}
    test_file_path = os.path.join(TEST_APP_DIR, app, '0.json')
    test_file_list = read_json(test_file_path)
    for bin_tar in base_results[app]:
        print(datetime.now())
        print('         ', bin_tar)
        matched_libs = {}
        base_afcg_result[app][bin_tar] = []
        for test_file in test_file_list:
            if test_file['formattedFileName'] == bin_tar:
                break
        match_result = base_results[app][bin_tar]['match_result']
        for item in match_result:
            if match_result[item]['strs'] < 0.8 and match_result[item]['exps'] < 0.2:
                continue
            pid = tuple(eval(item))[0]
            lib_name = id2package[pid]
            if lib_name not in matched_libs:
                matched_libs[lib_name] = []
            matched_libs[lib_name].append([item, match_result[item]['strs'] / 0.8 + match_result[item]['exps'] / 0.2])
        for lib_name in matched_libs:
            matched_libs[lib_name] = sorted(matched_libs[lib_name], key=lambda x:x[1], reverse=True)

        filtered_matched_libs = []
        for lib_name in matched_libs:
            for item_score in matched_libs[lib_name]:
                item = item_score[0]
                test_file_tmp = copy.deepcopy(test_file)
                pid = tuple(eval(item))[0]
                fname = tuple(eval(item))[1]
                vecids = pid2bin2vecid[pid][fname]
                vecs = {'vecs': [], 'ids': []}
                for id in vecids:
                    vecs['ids'].append(id)
                    vecs['vecs'].append(all_id2vecs[id])
                try:
                    print(datetime.now())
                    tmp_collection = 'tmp'+str(uuid.uuid4()).replace("-", '')
                    print('milvus loads data...'+fname)
                    m.load_data(list(vecs['vecs']), list(vecs['ids']),
                                tmp_collection, clear_old=True, metrictype=MetricType.IP)
                    common, afcg_rate = com2bins(
                        m, bin2fcgs, test_file_tmp, tmp_collection, pid, fname, net, id2keys, id2package, bin2func_num, k, fs_thres)
                    print(common, '    ', afcg_rate, '    ', fname.split('____')[-1])
                    base_afcg_result[app][bin_tar].append(
                            [id2package[pid], pid, fname, common, afcg_rate])
                    m.delete_collection(tmp_collection)
                    print('delete collection...')
                except Exception as e:
                    print(e)
                    continue
                if common > 5 or (common > 2 and afcg_rate > 0.1):
                    filtered_matched_libs.append(lib_name)
                    break
save_json(base_afcg_result, './base_afcg_7fea_contra_torch_b128_k1_common5_nofsthres.json')

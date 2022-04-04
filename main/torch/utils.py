import numpy as np
import json
import pickle as pkl


def norm_vec(vec):
    return vec/np.sqrt(sum(vec**2))

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


def save_json(content, js_path):
    with open(js_path, 'w') as f:
        json.dump(content, f)
import json
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('--data_root', type=str, default='')
parser.add_argument('--base_results', type=str,
                    default='../data/detection/base/base_result_b2sfinder_rule.json', help='base results')
parser.add_argument('--b2sfinder_results', type=str,
                    default='../data/detection/b2sfinder/b2sfinder_results.json', help='b2sfinder results')  
parser.add_argument('--b2sfinder_subset_results', type=str,
                    default='/home/user/binary_lib_detection/tmp/b2sfinder_0.25/b2sfinder_results_subset0.25.json', help='b2sfinder subset results')
parser.add_argument('--groundtruth', type=str, default='../data/groundtruth.json',
                    help='groundtruth')
parser.add_argument('--pid2package', type=str,
                    default='../data/pid2package.json', help='pid2package')
parser.add_argument('--pinfo', type=str,
                    default='../data/fedora_core_fedora_packages_0505.json', help='package info')
parser.add_argument('--b2sfinder_afcg_results', type=str,
                    default='../data/detection/b2sfinder_afcg/b2sfinder_afcg_7fea_contra_torch_b128_k1_common5_fsthres0.8.json', help='package info')
parser.add_argument('--fr_results', type=str,
                    default='../data/detection/our_method/7fea_contra_torch_b128_fk100_ck200_rate0.05_fsthres0.8.json', help='package info')

ARGS = parser.parse_args()

BASE_RESULTS = ARGS.base_results
B2SFINDER_RESULTS = ARGS.b2sfinder_results
B2SFINDER_SUBSET_RESULTS = ARGS.b2sfinder_subset_results
B2SFINDER_AFCG_RESULTS = ARGS.b2sfinder_afcg_results
FR_RESULTS = ARGS.fr_results
GROUNDTRUTH = ARGS.groundtruth
PID2PACKAGE = ARGS.pid2package


def read_json(js_path):
    with open(js_path, 'r') as f:
        content = json.load(f)
    return content

# cal p re of our method (func retrival + fcg)
def p_re():
    base_results = read_json(FR_RESULTS)
    groundtruth = read_json(GROUNDTRUTH)
    pid2package = read_json(PID2PACKAGE)
    p_re = {}
    all_groundtruth_num = 0
    all_matched_num = 0
    all_true_matched_num = 0
    all_true_pos_num = 0
    k = 25
    for app in base_results:
        if app == 'net.avs234_16':
            continue
        p_re[app] = {}
        for bin in base_results[app]:
            p_re[app][bin] = {}
            matched_libs = []
            match_result = base_results[app][bin]
            scores = []
            for lib_name in match_result:
                if lib_name == 'query_time' or lib_name == 'afcg_time':
                    continue
                for pid_cand in match_result[lib_name]:
                    for f_cand in match_result[lib_name][pid_cand]:
                        scores.append(
                            match_result[lib_name][pid_cand][f_cand][0] * match_result[lib_name][pid_cand][f_cand][1])
            if len(scores) != 0:
                scores = sorted(scores, reverse=True)
                thres = scores[min(k, len(scores)) - 1]
                print(thres)

            for lib_name in match_result:
                if lib_name == 'query_time' or lib_name == 'afcg_time':
                    continue
                for pid_cand in match_result[lib_name]:
                    for f_cand in match_result[lib_name][pid_cand]:
                        # if match_result[lib_name][pid_cand][f_cand][0] * match_result[lib_name][pid_cand][f_cand][1] < thres:
                        #     continue

                        # fcg thres
                        if match_result[lib_name][pid_cand][f_cand][0] < 2:
                            continue
                        if match_result[lib_name][pid_cand][f_cand][1] < 0.1:
                            continue

                        pid = pid_cand
                        lib_name = lib_name
                        matched_libs.append(lib_name)
            matched_libs = list(set(matched_libs))
            true_libs = list(groundtruth[app][bin].keys())
            if 'ogg' in true_libs:
                true_libs.remove('ogg')
            if 'jbig2' in true_libs:
                true_libs.remove('jbig2')
            true_pos = []
            true_matched_libs = []
            for lib in true_libs:
                if lib.startswith('lib'):
                    lib = lib.replace('lib', '')
                if lib.startswith('djvu'):
                    lib = 'djvu'
                if lib == 'zlib':
                    lib = 'zip'
                for matched_lib in matched_libs:
                    if lib in matched_lib:
                        true_pos.append(lib)
            true_pos = list(set(true_pos))

            for matched_lib in matched_libs:
                flag = 0
                for lib in true_libs:
                    if lib.startswith('lib'):
                        lib = lib.replace('lib', '')
                    if lib in matched_lib:
                        flag = 1
                        break
                if flag == 1:
                    true_matched_libs.append(matched_lib)
            true_matched_libs = list(set(true_matched_libs))

            if matched_libs:
                p = len(true_matched_libs) / len(matched_libs)
                all_true_matched_num += len(true_matched_libs)
                all_matched_num += len(matched_libs)
            else:
                p = None
            # print('ground:', true_libs)
            # print('true_matched:', true_matched_libs)
            # print('matched_libs:', matched_libs)
        
            if true_libs:
                re = len(true_pos) / len(true_libs)
                all_true_pos_num += len(true_pos)
                all_groundtruth_num += len(true_libs)
            else:
                re = None
            p_re[app][bin] = {'p': p, 're': re,
                              'true_pos': true_pos, 'matched_libs': matched_libs}

    # print(p_re)
    # with open('./base_p_re.json', 'w') as f:
    #     json.dump(p_re, f)
    print(all_true_matched_num)
    print(all_matched_num)
    print(all_true_matched_num / all_matched_num)
    print(all_groundtruth_num)
    print(all_true_pos_num / all_groundtruth_num)


# cal p re of related work + fcg filter
def analyze_afcg_base():
    base_results = '7fea_contra_torch_b128_fk100_ck200_rate0.05_fsthres0.75.json/b2sfinder_allfea_afcg_7fea_contra_torch_b128_k1_common5_fsthres0.8.json'
    groundtruth = '../data/groundtruth.json'
    pid2package = '../data/pid2package.json'

    base_results = read_json(base_results)
    groundtruth = read_json(groundtruth)
    pid2package = read_json(pid2package)
    p_re = {}
    all_groundtruth_num = 0
    all_matched_num = 0
    all_true_matched_num = 0
    all_true_pos_num = 0
    k = 25
    for app in base_results:
        if app == 'net.avs234_16':
            continue
        p_re[app] = {}
        for bin in base_results[app]:
            p_re[app][bin] = {}
            matched_libs = []
            match_result = base_results[app][bin]
            scores = []
            for item in match_result:
                lib_name = item[0]
                if item[3] < 3:
                    continue
                # if item[4] < 0.1:
                #     continue
                matched_libs.append(lib_name)
            matched_libs = list(set(matched_libs))
            true_libs = list(groundtruth[app][bin].keys())
            if 'ogg' in true_libs:
                true_libs.remove('ogg')
            if 'jbig2' in true_libs:
                true_libs.remove('jbig2')
            true_pos = []
            true_matched_libs = []
            for lib in true_libs:
                if lib.startswith('lib'):
                    lib = lib.replace('lib', '')
                if lib.startswith('djvu'):
                    lib = 'djvu'
                if lib == 'zlib':
                    lib = 'zip'
                for matched_lib in matched_libs:
                    if lib in matched_lib:
                        true_pos.append(lib)
            true_pos = list(set(true_pos))

            for matched_lib in matched_libs:
                flag = 0
                for lib in true_libs:
                    if lib.startswith('lib'):
                        lib = lib.replace('lib', '')
                    if lib in matched_lib:
                        flag = 1
                        break
                if flag == 1:
                    true_matched_libs.append(matched_lib)
            true_matched_libs = list(set(true_matched_libs))

            if matched_libs:
                p = len(true_matched_libs) / len(matched_libs)
                all_true_matched_num += len(true_matched_libs)
                all_matched_num += len(matched_libs)
            else:
                p = None

            if true_libs:
                re = len(true_pos) / len(true_libs)
                all_true_pos_num += len(true_pos)
                all_groundtruth_num += len(true_libs)
            else:
                re = None
            p_re[app][bin] = {'p': p, 're': re,
                              'true_pos': true_pos, 'matched_libs': matched_libs}

    # print(p_re)
    # with open('./base_p_re.json', 'w') as f:
    #     json.dump(p_re, f)
    print(all_true_matched_num)
    print(all_matched_num)
    print(all_true_matched_num / all_matched_num)
    print(all_groundtruth_num)
    print(all_true_pos_num / all_groundtruth_num)


# get version identification results of function vector channel
def version_level_p():
    base_results = read_json(ARGS.fr_results)
    groundtruth = read_json(ARGS.groundtruth)
    pinfo = read_json(ARGS.pinfo)
    pid2pinfo = {}
    for package in pinfo:
        pid2pinfo[package['package_id']] = package
    for app in base_results:
        if app == 'net.avs234_16':
            continue
        for bin in base_results[app]:
            matched_libs = {}
            match_result = base_results[app][bin]
            print(app, '    ', bin)
            if not groundtruth[app][bin]:
                continue
            print(groundtruth[app][bin])
            true_libs = list(groundtruth[app][bin].keys())
            for lib_name in match_result:
                if lib_name == 'query_time' or lib_name == 'afcg_time':
                    continue
                best_version = 0
                max_score = 0
                for pid_cand in match_result[lib_name]:
                    score = 0
                    for f_cand in match_result[lib_name][pid_cand]:
                        if match_result[lib_name][pid_cand][f_cand][0] < 2:
                            continue
                        if match_result[lib_name][pid_cand][f_cand][1] < 0.1:
                            continue
                        score += match_result[lib_name][pid_cand][f_cand][0]
                    if score > max_score:
                        max_score = score
                        best_version = pid_cand

                flag = 0
                for lib in true_libs:
                    if lib.startswith('lib'):
                        lib = lib.replace('lib', '')
                    if lib in lib_name:
                        flag = 1
                        break
                if flag == 1 and best_version != 0:
                    print(lib_name, '    ', pid2pinfo[int(
                        best_version)]['main_version'])
            print('\n')


# calculate the precision and recall of two channels
def unified_pre_re():
    b2sfinder_afcg_results = read_json(B2SFINDER_AFCG_RESULTS)
    results = read_json(FR_RESULTS)
    groundtruth = read_json(GROUNDTRUTH)
    pid2package = read_json(PID2PACKAGE)
    p_re = {}
    all_groundtruth_num = 0
    all_matched_num = 0
    all_true_matched_num = 0
    all_true_pos_num = 0
    
    for app in b2sfinder_afcg_results:
        if app == 'net.avs234_16':
            continue
        p_re[app] = {}
        for bin in b2sfinder_afcg_results[app]:
            p_re[app][bin] = {}
            matched_libs = []
            b2sfinder_match_result = b2sfinder_afcg_results[app][bin]
            for item in b2sfinder_match_result:
                lib_name = item[0]
                if item[3] < 3:
                    continue
                
                # if item[4] < 0.1:
                #     continue
                matched_libs.append(lib_name)
            matched_libs = list(set(matched_libs))

            match_result = results[app][bin]
            for lib_name in match_result:
                if lib_name == 'query_time' or lib_name == 'afcg_time':
                    continue
                for pid_cand in match_result[lib_name]:
                    for f_cand in match_result[lib_name][pid_cand]:
                        # if match_result[lib_name][pid_cand][f_cand][0] < 20:
                        #     if match_result[lib_name][pid_cand][f_cand][1] < 0.2:
                        #         continue


                        # fcg thres
                        if match_result[lib_name][pid_cand][f_cand][0] < 2:
                            continue
                        if match_result[lib_name][pid_cand][f_cand][1] < 0.1:
                            continue
                        lib_name = lib_name
                        # matched_libs.append(lib_name)
            matched_libs = list(set(matched_libs))
            true_libs = list(groundtruth[app][bin].keys())
            if 'ogg' in true_libs:
                true_libs.remove('ogg')
            if 'jbig2' in true_libs:
                true_libs.remove('jbig2')
            true_pos = []
            true_matched_libs = []
            for lib in true_libs:
                if lib.startswith('lib'):
                    lib = lib.replace('lib', '')
                if lib.startswith('djvu'):
                    lib = 'djvu'
                if lib == 'zlib':
                    lib = 'zip'
                for matched_lib in matched_libs:
                    if lib in matched_lib:
                        true_pos.append(lib)
            true_pos = list(set(true_pos))

            for matched_lib in matched_libs:
                flag = 0
                for lib in true_libs:
                    if lib.startswith('lib'):
                        lib = lib.replace('lib', '')
                    if lib in matched_lib:
                        flag = 1
                        break
                if flag == 1:
                    true_matched_libs.append(matched_lib)
            true_matched_libs = list(set(true_matched_libs))

            if matched_libs:
                p = len(true_matched_libs) / len(matched_libs)
                all_true_matched_num += len(true_matched_libs)
                all_matched_num += len(matched_libs)
            else:
                p = None

            if true_libs:
                re = len(true_pos) / len(true_libs)
                all_true_pos_num += len(true_pos)
                all_groundtruth_num += len(true_libs)
            else:
                re = None
            p_re[app][bin] = {'p': p, 're': re,
                              'true_pos': true_pos, 'matched_libs': matched_libs}
            # if (not re and true_libs) or re != 1:
            #     print(app, '    ', bin)
            #     print(p, '    ', re)
            #     print(true_pos)
            #     print(true_libs)
            #     print('\n')

    # print(p_re)
    # with open('./base_p_re.json', 'w') as f:
    #     json.dump(p_re, f)

    print(all_true_matched_num)
    print(all_true_matched_num / all_matched_num)
    print(all_true_pos_num)
    print(all_groundtruth_num)
    print(all_true_pos_num / all_groundtruth_num)



# calculate the precision and recall of b2sfinder +function vector channel
def b2sfinder_fr_pre_re(strs_exps, switch_if):
    b2sfinder_results = read_json(B2SFINDER_RESULTS)
    ft_results = read_json(FR_RESULTS)
    groundtruth = read_json(GROUNDTRUTH)
    pid2package = read_json(PID2PACKAGE)
    p_re = {}
    all_groundtruth_num = 0
    all_matched_num = 0
    all_true_matched_num = 0
    all_true_pos_num = 0
    for app in b2sfinder_results:
        if app == 'net.avs234_16':
            continue
        p_re[app] = {}
        for bin in b2sfinder_results[app]:
            p_re[app][bin] = {}
            matched_libs = []
            match_result = b2sfinder_results[app][bin]
            for key in match_result:
                pid = tuple(eval(key))[0]
                lib_name = pid2package[pid]
                if strs_exps and (('string' in match_result[key]['match'] and match_result[key]['match']['string']) or ('export' in match_result[key]['match'] and match_result[key]['match']['export'])):
                    matched_libs.append(lib_name)
                if switch_if and (('switch_case' in match_result[key]['match'] and match_result[key]['match']['switch_case']) or ('nested_if' in match_result[key]['match'] and match_result[key]['match']['nested_if'])):
                    matched_libs.append(lib_name)

            match_result = ft_results[app][bin]
            for lib_name in match_result:
                if lib_name == 'query_time' or lib_name == 'afcg_time':
                    continue
                for pid_cand in match_result[lib_name]:
                    for f_cand in match_result[lib_name][pid_cand]:
                        # if match_result[lib_name][pid_cand][f_cand][0] < 20:
                        #     if match_result[lib_name][pid_cand][f_cand][1] < 0.2:
                        #         continue
                        if match_result[lib_name][pid_cand][f_cand][0] < 2:
                            continue
                        if match_result[lib_name][pid_cand][f_cand][1] < 0.1:
                            continue
                        lib_name = lib_name
                        # matched_libs.append(lib_name)
            matched_libs = list(set(matched_libs))
            true_libs = list(groundtruth[app][bin].keys())
            if 'ogg' in true_libs:
                true_libs.remove('ogg')
            if 'jbig2' in true_libs:
                true_libs.remove('jbig2')
            true_pos = []
            true_matched_libs = []
            for lib in true_libs:
                if lib.startswith('lib'):
                    lib = lib.replace('lib', '')
                if lib.startswith('djvu'):
                    lib = 'djvu'
                if lib == 'zlib':
                    lib = 'zip'
                for matched_lib in matched_libs:
                    if lib in matched_lib:
                        true_pos.append(lib)
            true_pos = list(set(true_pos))

            for matched_lib in matched_libs:
                flag = 0
                for lib in true_libs:
                    if lib.startswith('lib'):
                        lib = lib.replace('lib', '')
                    if lib in matched_lib:
                        flag = 1
                        break
                if flag == 1:
                    true_matched_libs.append(matched_lib)
            true_matched_libs = list(set(true_matched_libs))

            if matched_libs:
                p = len(true_matched_libs) / len(matched_libs)
                all_true_matched_num += len(true_matched_libs)
                all_matched_num += len(matched_libs)
            else:
                p = None

            if true_libs:
                re = len(true_pos) / len(true_libs)
                all_true_pos_num += len(true_pos)
                all_groundtruth_num += len(true_libs)
            else:
                re = None
            p_re[app][bin] = {'p': p, 're': re,
                              'true_pos': true_pos, 'matched_libs': matched_libs}
            # if (not re and true_libs) or re != 1:
            #     print(app, '    ', bin)
            #     print(p, '    ', re)
            #     print(true_pos)
            #     print(true_libs)
            #     print('\n')

    # print(p_re)
    # with open('./base_p_re.json', 'w') as f:
    #     json.dump(p_re, f)

    print(all_true_matched_num)
    print(all_true_matched_num / all_matched_num)
    print(all_true_pos_num)
    print(all_groundtruth_num)
    print(all_true_pos_num / all_groundtruth_num)


# analyze the results b2sfinder + function vector channel
def b2sfinder_subset_fr_pre_re():
    b2sfinder_results = read_json(B2SFINDER_RESULTS)
    b2sfinder_subset_results = read_json(B2SFINDER_SUBSET_RESULTS)
    ft_results = read_json(FR_RESULTS)
    groundtruth = read_json(GROUNDTRUTH)
    pid2package = read_json(PID2PACKAGE)
    p_re = {}
    all_groundtruth_num = 0
    all_matched_num = 0
    all_true_matched_num = 0
    all_true_pos_num = 0
    for app in b2sfinder_results:
        if app == 'net.avs234_16':
            continue
        p_re[app] = {}
        for bin in b2sfinder_results[app]:
            p_re[app][bin] = {}
            matched_libs = []
            match_result = b2sfinder_results[app][bin]
            for key in match_result:
                pid = tuple(eval(key))[0]
                lib_name = pid2package[pid]
                if ('switch_case' in match_result[key]['match'] and match_result[key]['match']['switch_case']) or ('nested_if' in match_result[key]['match'] and match_result[key]['match']['nested_if']):
                    # matched_libs.append(lib_name)
                    pass
            
            b2sfinder_subset_match_results = b2sfinder_subset_results[app][bin]
            for key in b2sfinder_subset_match_results:
                pid = tuple(eval(key))[0]
                lib_name = pid2package[pid]
                if ('string' in b2sfinder_subset_match_results[key]['match'] and b2sfinder_subset_match_results[key]['match']['string']) or ('export' in b2sfinder_subset_match_results[key]['match'] and b2sfinder_subset_match_results[key]['match']['export']):
                    matched_libs.append(lib_name)

            match_result = ft_results[app][bin]
            for lib_name in match_result:
                if lib_name == 'query_time' or lib_name == 'afcg_time':
                    continue
                for pid_cand in match_result[lib_name]:
                    for f_cand in match_result[lib_name][pid_cand]:
                        # if match_result[lib_name][pid_cand][f_cand][0] < 20:
                        #     if match_result[lib_name][pid_cand][f_cand][1] < 0.2:
                        #         continue
                        if match_result[lib_name][pid_cand][f_cand][0] < 2:
                            continue
                        if match_result[lib_name][pid_cand][f_cand][1] < 0.1:
                            continue
                        lib_name = lib_name
                        # matched_libs.append(lib_name)
            matched_libs = list(set(matched_libs))
            true_libs = list(groundtruth[app][bin].keys())
            if 'ogg' in true_libs:
                true_libs.remove('ogg')
            if 'jbig2' in true_libs:
                true_libs.remove('jbig2')
            true_pos = []
            true_matched_libs = []
            for lib in true_libs:
                if lib.startswith('lib'):
                    lib = lib.replace('lib', '')
                if lib.startswith('djvu'):
                    lib = 'djvu'
                if lib == 'zlib':
                    lib = 'zip'
                for matched_lib in matched_libs:
                    if lib in matched_lib:
                        true_pos.append(lib)
            true_pos = list(set(true_pos))

            for matched_lib in matched_libs:
                flag = 0
                for lib in true_libs:
                    if lib.startswith('lib'):
                        lib = lib.replace('lib', '')
                    if lib in matched_lib:
                        flag = 1
                        break
                if flag == 1:
                    true_matched_libs.append(matched_lib)
            true_matched_libs = list(set(true_matched_libs))

            if matched_libs:
                p = len(true_matched_libs) / len(matched_libs)
                all_true_matched_num += len(true_matched_libs)
                all_matched_num += len(matched_libs)
            else:
                p = None

            if true_libs:
                re = len(true_pos) / len(true_libs)
                all_true_pos_num += len(true_pos)
                all_groundtruth_num += len(true_libs)
            else:
                re = None
            p_re[app][bin] = {'p': p, 're': re,
                              'true_pos': true_pos, 'matched_libs': matched_libs}
            if (not re and true_libs) or re != 1:
                print(app, '    ', bin)
                print(p, '    ', re)
                print(true_pos)
                print(true_libs)
                print('\n')

    # print(p_re)
    # with open('./base_p_re.json', 'w') as f:
    #     json.dump(p_re, f)

    print(all_true_matched_num)
    print(all_true_matched_num / all_matched_num)
    print(all_true_pos_num)
    print(all_groundtruth_num)
    print(all_true_pos_num / all_groundtruth_num)


# analyze the results of base method + function vector channel
def base_fr():
    base_results = read_json(BASE_RESULTS)
    ft_results = read_json(FR_RESULTS)
    groundtruth = read_json(GROUNDTRUTH)
    pid2package = read_json(PID2PACKAGE)
    p_re = {}
    all_groundtruth_num = 0
    all_matched_num = 0
    all_true_matched_num = 0
    all_true_pos_num = 0
    for app in base_results:
        if app == 'net.avs234_16':
            continue
        p_re[app] = {}
        for bin in base_results[app]:
            p_re[app][bin] = {}
            matched_libs = []
            match_result = base_results[app][bin]['match_result']
            for key in match_result:
                if match_result[key]['strs'] < 0.8 and match_result[key]['exps'] < 0.2:
                    continue
                pid = tuple(eval(key))[0]
                lib_name = pid2package[pid]
                matched_libs.append(lib_name)

            match_result = ft_results[app][bin]
            for lib_name in match_result:
                if lib_name == 'query_time' or lib_name == 'afcg_time':
                    continue
                for pid_cand in match_result[lib_name]:
                    for f_cand in match_result[lib_name][pid_cand]:
                        if match_result[lib_name][pid_cand][f_cand][0] < 2:
                            continue
                        if match_result[lib_name][pid_cand][f_cand][1] < 0.1:
                            continue
                        # if match_result[lib_name][pid_cand][f_cand][0] < 20:
                        #     if match_result[lib_name][pid_cand][f_cand][1] < 0.2:
                        #         continue
                        lib_name = lib_name
                        matched_libs.append(lib_name)
            matched_libs = list(set(matched_libs))

            true_libs = list(groundtruth[app][bin].keys())
            if 'ogg' in true_libs:
                true_libs.remove('ogg')
            if 'jbig2' in true_libs:
                true_libs.remove('jbig2')
            true_pos = []
            true_matched_libs = []
            for lib in true_libs:
                if lib.startswith('lib'):
                    lib = lib.replace('lib', '')
                if lib.startswith('djvu'):
                    lib = 'djvu'
                if lib == 'zlib':
                    lib = 'zip'
                for matched_lib in matched_libs:
                    if lib in matched_lib:
                        true_pos.append(lib)
            true_pos = list(set(true_pos))

            for matched_lib in matched_libs:
                flag = 0
                for lib in true_libs:
                    if lib.startswith('lib'):
                        lib = lib.replace('lib', '')
                    if lib in matched_lib:
                        flag = 1
                        break
                if flag == 1:
                    true_matched_libs.append(matched_lib)
            true_matched_libs = list(set(true_matched_libs))

            if matched_libs:
                p = len(true_matched_libs) / len(matched_libs)
                all_true_matched_num += len(true_matched_libs)
                all_matched_num += len(matched_libs)
            else:
                p = None

            if true_libs:
                re = len(true_pos) / len(true_libs)
                all_true_pos_num += len(true_pos)
                all_groundtruth_num += len(true_libs)
            else:
                re = None
            p_re[app][bin] = {'p': p, 're': re,
                              'true_pos': true_pos, 'matched_libs': matched_libs}
            if (not re and true_libs) or re != 1:
                print(app, '    ', bin)
                print(p, '    ', re)
                print(true_pos)
                print(true_libs)
                print('\n')

    # print(p_re)
    # with open('./base_p_re.json', 'w') as f:
    #     json.dump(p_re, f)

    print(all_true_matched_num)
    print(all_true_matched_num / all_matched_num)
    print(all_true_pos_num)
    print(all_groundtruth_num)
    print(all_true_pos_num / all_groundtruth_num)


## report the final version identification results of two channels
def unified_version_p():
    b2sfinder_afcg_results = read_json(B2SFINDER_AFCG_RESULTS)
    fr_results = read_json(FR_RESULTS)
    groundtruth = read_json(GROUNDTRUTH)
    pid2package = read_json(PID2PACKAGE)
    pinfo = read_json(ARGS.pinfo)
    pid2pinfo = {}
    for package in pinfo:
        pid2pinfo[package['package_id']] = package
    all_groundtruth_num = 0
    all_matched_num = 0
    all_true_matched_num = 0
    all_true_pos_num = 0
    
    for app in b2sfinder_afcg_results:
        if app == 'net.avs234_16':
            continue
        for bin in b2sfinder_afcg_results[app]:
            print(app, '    ', bin)
            if not groundtruth[app][bin]:
                continue
            print(groundtruth[app][bin])
            true_libs = list(groundtruth[app][bin].keys())
            b2sfinder_match_result = b2sfinder_afcg_results[app][bin]
            match_result = {}
            for item in b2sfinder_match_result:
                if item[0] not in match_result:
                    match_result[item[0]] = {}
                if item[1] not in match_result[item[0]]:
                    match_result[item[0]][item[1]] = {}
                if item[2] not in match_result[item[0]][item[1]]:
                     match_result[item[0]][item[1]][item[2]] = [item[3], item[4]]
            
            for lib_name in match_result:
                flag = 0
                for lib in true_libs:
                    if lib.startswith('lib'):
                        lib = lib.replace('lib', '')
                    if lib in lib_name:
                        flag = 1
                        break

                if lib_name == 'query_time' or lib_name == 'afcg_time':
                    continue
                best_version = 0
                max_score = 0
                for pid_cand in match_result[lib_name]:
                    score = 0
                    for f_cand in match_result[lib_name][pid_cand]:
                        if match_result[lib_name][pid_cand][f_cand][0] < 3:
                            continue
                        # if match_result[lib_name][pid_cand][f_cand][1] < 0.1:
                        #     continue
                        score += match_result[lib_name][pid_cand][f_cand][0]
                    if score > max_score:
                        max_score = score
                        best_version = pid_cand
            

                best_fr_version = 0
                if lib_name in fr_results[app][bin]:
                    max_score = 0
                    for pid_cand in fr_results[app][bin][lib_name]:
                        score = 0
                        for f_cand in fr_results[app][bin][lib_name][pid_cand]:
                            if fr_results[app][bin][lib_name][pid_cand][f_cand][0] < 2:
                                continue
                            if fr_results[app][bin][lib_name][pid_cand][f_cand][1] < 0.1:
                                continue
                            score += fr_results[app][bin][lib_name][pid_cand][f_cand][0]
                        if score > max_score:
                            max_score = score
                            best_fr_version = pid_cand
                if best_fr_version != 0:
                    best_version = best_fr_version

                if flag == 1:
                    print(lib_name, '    ', pid2pinfo[int(
                        best_version)]['main_version'])
            

if __name__ == '__main__':
    # BASE_RESULTS = '/home/user/binary_lib_detection/base_results_subset0.5.json'

    # analyze_afcg_base()
    FR_RESULTS = '/home/user/binary_lib_detection/7fea_contra_torch_b128_fk100_ck200_rate0.05_fsthres0.75.json'
    # p_re()


    # version_level_p()

    B2SFINDER_AFCG_RESULTS = '/home/user/binary_lib_detection/main/torch/b2sfinder_s_0.25_afcg_7fea_contra_torch_b128_k1_com10_com5rate0.2_fsthres0.8.json'
    
    # unified_pre_re()

    
    B2SFINDER_SUBSET_RESULTS = '/home/user/binary_lib_detection/related_work/b2sfinder/FeatureMatch/b2sfinder_s_subset0.25.json'
    # b2sfinder_fr_pre_re(strs_exps=True, switch_if=True)

    # b2sfinder_subset_fr_pre_re()

    # base_fr()

    
    B2SFINDER_AFCG_RESULTS = '/home/user/binary_lib_detection/main/torch/b2sfinder_afcg_allversions_7fea_contra_torch_b128_k1_com10_com5rate0.2_fsthres0.8.json'
    # unified_version_p()
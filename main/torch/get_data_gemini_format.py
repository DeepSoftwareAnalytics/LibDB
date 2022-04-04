import json
import os
import re
import numpy as np

def save_data(data, save_path):
    for item in data:
        with open(save_path, 'a+') as f:
            line = json.dumps(item)
            f.write(line+'\n')


def get_all_compilation_cases(data_path):
    libraries = os.listdir(data_path)
    all_compilation_cases = []
    for library in libraries:
        print(library)
        if library.startswith('.'):
            continue
        compilation_cases = os.listdir(os.path.join(data_path, library))
        all_compilation_cases += compilation_cases
    return set(all_compilation_cases)


def get_filtered_compilation_cases(data_path):
    libraries = os.listdir(data_path)
    all_compilation_cases = []
    names = []
    for library in libraries:
        print(library)
        if library.startswith('.'):
            continue
        f_names = os.listdir(os.path.join(data_path, library))

        for f_name in f_names:
            if f_name.startswith('arm_x86') or f_name.startswith('linux_gcc_5') or f_name.startswith('linux_gcc_6') or f_name.startswith('linux_gcc_6') or f_name.startswith('linux_gcc_7') or f_name.startswith('linux_gcc_8') or f_name.startswith('mac_gcc_8') or f_name.startswith("linux_clang_3.8") or f_name.startswith("linux_clang_4.0") or f_name.startswith("linux_clang_5.0") or f_name.startswith("mac_gcc_7"):
                continue
            all_compilation_cases.append(f_name)
    return set(all_compilation_cases)

def get_filtered_compilation_cases_without_oplevel(data_path):
    compilation_cases = get_filtered_compilation_cases(data_path)
    res = []
    for case in compilation_cases:
        res.append(case[:-3])
    return set(res)


def get_deduplicate_data_vectors(data_path, save_path, train_test):
    all_compilation_cases = get_filtered_compilation_cases(data_path)
    print(len(all_compilation_cases))
    print(all_compilation_cases)
    libraries = os.listdir(data_path)
    replace_words = ['.exe', '.so', '.dylib', '.dll', '.json']
    rex_num = re.compile('\_\d*$')
    all_function_features = {}
    valid_filenames = ['libsqlite3.0', 'sqlite3', 'ndisasm', 'nasm', 'libassuan.0', 'm4', 'libksba.8', 'yat2m', 'libgpg-error.0', 'gpg-error', 'gpg', 'gpgkeys_ldap', 'gpgsplit', 'gpgkeys_curl', 'gpgkeys_finger', 'gpgkeys_hkp', 'gpgv', 'libgcrypt.20','dumpsexp','mpicalc', 'hmac256','libnpth.0','libpng','libstunnel', 'stunnel', 'vsyasm']
    valid_libs = ['sqlite-autoconf-3330000', 'stunnel-5.56', 'yasm-1.3.0']

    duplicate_num = 0
    count = 0

    for compilation_case in all_compilation_cases:
        # print(compilation_case)
        if compilation_case.startswith('.'):
            continue
        data = []
        for library in libraries:
            if library.startswith('.'):
                continue
            if train_test:
                if library in valid_libs:
                    continue
            else:
                if not library in valid_libs:
                    continue
            compilation_cases = os.listdir(os.path.join(data_path, library))
            if compilation_case not in compilation_cases:
                continue

            subdir_path = os.path.join(
                os.path.join(data_path, library, compilation_case))
            feature_files = os.listdir(subdir_path)
            for feature_file in feature_files:
                if feature_file.startswith('.') or feature_file == 'status':
                    continue
                filename = feature_file.replace('.json', '')
                feature_file_path = os.path.join(subdir_path, feature_file)
                for word in replace_words:
                    filename = filename.replace(word, '')
                if filename == 'libnpth-0':
                    filename = 'libnpth.0'
                if filename not in valid_filenames and library != 'gnupg-2.2.23':
                    continue
                all_non_thunk_funcs = get_all_non_thunk_funcs(
                    feature_file_path)
                selected_ones = {}
                for func in all_non_thunk_funcs:
                    if func['nodes'] < 5:
                        continue
                    func_name = func['functionName']
                    if 'mac' in compilation_case or 'win' in compilation_case:
                        if func_name.startswith('_'):
                            func_name = func_name[1:]
                    func_name = func_name.replace('.', '_')
                    func_name = rex_num.sub('', func_name)
                    func_signature = library + '##' + filename + '##' + func_name

                    item = get_data_gemini_item(func, func_signature)
                    if func_signature not in selected_ones:
                        selected_ones[func_signature] = []
                    selected_ones[func_signature].append(item)
                for func_signature in selected_ones:
                    if len(selected_ones[func_signature]) > 1:
                        continue
                    added_vector = selected_ones[func_signature][0]['features']
                    if func_signature in all_function_features:
                        if added_vector in all_function_features[func_signature]['f']:
                            duplicate_num += 1
                            continue
                        else:
                            all_function_features[func_signature]['f'].append(added_vector)
                            all_function_features[func_signature]['c'].append(compilation_case)
                    else:
                        all_function_features[func_signature] = {"f":[], 'c':[]}
                        all_function_features[func_signature]['f'].append(added_vector)
                        all_function_features[func_signature]['c'].append(compilation_case)
                    data.append(selected_ones[func_signature][0])
        save_data(data, os.path.join(save_path, compilation_case+'.json'))
        count += len(data)
    print(duplicate_num)
    print(count)


def get_all_non_thunk_funcs(feature_file_path):
    with open(feature_file_path, 'r') as feature_file:
        feature = json.load(feature_file)
    res = []
    for func in feature['binFileFeature']['functions']:
        if func['isThunkFunction'] is False and 'text' in func['memoryBlock']:
            res.append(func)
    return res



# {"src": "openssl-1.0.1f-armeb-linux-O0v54/ectest.o.txt", "n_num": 33, "succs": [[], [0, 5], [28, 22], [24, 2], [], [4, 15], [16, 23], [30, 6], [18, 3], [26, 19], [32, 9], [8, 27], [11, 20], [29, 7], [17, 12], [21, 14], [10, 31], [], [], [1, 25], [], [], [], [], [], [], [], [], [], [], [], [], []], "features": [[0.0, 2.0, 0.0, 0.0, 4.0, 21.0, 4.0], [0.0, 1.0, 18.0, 0.0, 2.0, 7.0, 1.0], [0.0, 1.0, 2.0, 0.0, 2.0, 8.0, 1.0], [0.0, 1.0, 4.0, 0.0, 2.0, 12.0, 2.0], [0.0, 2.0, 0.0, 0.0, 4.0, 21.0, 4.0], [0.0, 1.0, 16.0, 0.0, 2.0, 12.0, 2.0], [0.0, 1.0, 28.0, 0.0, 2.0, 6.0, 1.0], [0.0, 1.0, 30.0, 0.0, 2.0, 12.0, 3.0], [0.0, 1.0, 6.0, 0.0, 2.0, 8.0, 1.0], [0.0, 1.0, 22.0, 0.0, 2.0, 6.0, 1.0], [0.0, 1.0, 24.0, 0.0, 2.0, 12.0, 3.0], [0.0, 1.0, 8.0, 0.0, 2.0, 8.0, 1.0], [0.0, 1.0, 10.0, 0.0, 2.0, 12.0, 2.0], [0.0, 3.0, 32.0, 0.0, 10.0, 39.0, 4.0], [0.0, 1.0, 12.0, 0.0, 3.0, 9.0, 3.0], [0.0, 1.0, 14.0, 0.0, 2.0, 8.0, 1.0], [0.0, 2.0, 26.0, 0.0, 4.0, 17.0, 4.0], [0.0, 2.0, 0.0, 0.0, 4.0, 21.0, 4.0], [0.0, 2.0, 0.0, 0.0, 4.0, 21.0, 4.0], [0.0, 4.0, 20.0, 0.0, 4.0, 22.0, 6.0], [0.0, 2.0, 0.0, 0.0, 4.0, 21.0, 4.0], [0.0, 2.0, 0.0, 0.0, 4.0, 21.0, 4.0], [0.0, 2.0, 0.0, 0.0, 4.0, 21.0, 4.0], [0.0, 2.0, 0.0, 0.0, 4.0, 21.0, 4.0], [0.0, 2.0, 0.0, 0.0, 4.0, 21.0, 4.0], [0.0, 2.0, 0.0, 0.0, 4.0, 21.0, 4.0], [0.0, 2.0, 0.0, 0.0, 4.0, 21.0, 4.0], [0.0, 2.0, 0.0, 0.0, 4.0, 21.0, 4.0], [0.0, 2.0, 0.0, 0.0, 7.0, 23.0, 2.0], [0.0, 2.0, 0.0, 0.0, 4.0, 21.0, 4.0], [0.0, 2.0, 0.0, 0.0, 4.0, 21.0, 4.0], [0.0, 2.0, 0.0, 0.0, 4.0, 21.0, 4.0], [0.0, 2.0, 0.0, 0.0, 4.0, 21.0, 4.0]], "fname": "group_order_tests"}

def get_data_gemini_item(func, func_signature, compilation_case):
    item = {}
    item["src"] = func_signature
    item["n_num"] = len(func['nodesAsm'])
    item['succss'] = func['edgePairs']
    item['features'] = func['nodeGeminiVectors']
    item['fname'] = func_signature
    item['compilation'] = compilation_case
    return item


def get_data_ghidra_item(func, func_signature):
    item = {}
    item["src"] = func_signature
    item["n_num"] = len(func['nodesAsm'])
    item['succss'] = func['edgePairs']
    item['features'] = func['nodeGhidraVectors']
    item['fname'] = func_signature
    return item

if __name__ == '__main__':

    feature_data_path = '/mnt/c/Users/user/Desktop/data/featureJson0417'
    gemini_data_train_test_path = '/mnt/c/Users/user/Desktop/data/vector_deduplicate_gemini_format_less_compilation_cases/train_test'
    gemini_data_valid_path = '/mnt/c/Users/user/Desktop/data/vector_deduplicate_gemini_format_less_compilation_cases/valid'
    ghidra_data_train_test_path = '/mnt/c/Users/user/Desktop/data/vector_deduplicate_ghidra_format_less_compilation_cases/train_test'
    ghidra_data_valid_path = '/mnt/c/Users/user/Desktop/data/vector_deduplicate_ghidra_format_less_compilation_cases/valid'

    data_path = '/mnt/c/Users/user/Desktop/data/vector_gemini_format/train_test'

    # get_deduplicate_data_vectors(feature_data_path, ghidra_data_train_test_path, True)
    # get_deduplicate_data_vectors(feature_data_path, ghidra_data_valid_path, False)

    valid_arm2non_arm_feature_json = '/mnt/c/Users/user/Desktop/data/validation_arm2non_arm/feature_json'
    valid_arm2non_arm_save_path = '/mnt/c/Users/user/Desktop/data/validation_arm2non_arm/gemini/validation_arm2non_arm_data'
    get_deduplicate_data_vectors(valid_arm2non_arm_feature_json, valid_arm2non_arm_save_path, False)

    # print(get_filtered_compilation_cases_without_oplevel(feature_data_path))
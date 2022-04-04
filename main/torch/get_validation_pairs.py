import json
import os


def save_data(data, save_path):
    for item in data:
        with open(save_path, 'a+') as f:
            line = json.dumps(item)
            f.write(line+'\n')


def get_pairs(l_fea_js, r_fea_js):
    pairs = []
    l_fea_d = {}
    r_fea_d = {}
    f_sigs = []
    with open(l_fea_js) as load_f:
        for line in load_f:
            l_fea = json.loads(line.strip())
            l_fea_d[l_fea['fname']] = l_fea

    with open(r_fea_js) as load_f:
        for line in load_f:
            r_fea = json.loads(line.strip())
            r_fea_d[r_fea['fname']] = r_fea

    for f_sig in l_fea_d:
        if f_sig in r_fea_d:
            pairs.append([l_fea_d[f_sig], r_fea_d[f_sig]])
            f_sigs.append(f_sig)
    return pairs, f_sigs


def get_max_oplevel_pairs(fea_js_path, pairs_save_path):
    f_names = os.listdir(fea_js_path)
    valid_cases = []
    for f_name in f_names:
        if f_name.startswith('arm_x86') or f_name.startswith('linux_gcc_5') or f_name.startswith('linux_gcc_6') or f_name.startswith('linux_gcc_6') or f_name.startswith('linux_gcc_7') or f_name.startswith('linux_gcc_8') or f_name.startswith('mac_gcc_8') or f_name.startswith("linux_clang_3.8") or f_name.startswith("linux_clang_4.0") or f_name.startswith("linux_clang_5.0") or f_name.startswith("mac_gcc_7"):
            continue
        valid_cases.append(f_name[:-6])

    all_pairs = []
    all_f_sigs = []
    for comp_case in valid_cases:
        l_fea_js = os.path.join(fea_js_path, comp_case+'0.json')
        r_fea_js = os.path.join(fea_js_path, comp_case+'3.json')
        if os.path.exists(l_fea_js) and os.path.exists(r_fea_js):
            pairs, f_sigs = get_pairs(l_fea_js, r_fea_js)
            all_pairs += pairs
            all_f_sigs += f_sigs
    print('func num: ', len(set(all_f_sigs)))
    print('graph num:', len(all_pairs)*2)
    print('pair num: ', len(all_pairs))
    save_data(all_pairs, pairs_save_path)


def get_os_diff_linux_win_pairs(fea_js_path, pairs_save_path):
    compilation_case_pairs = [['linux_gcc_8_O', 'win_gcc_8.1_O'], ['linux_gcc_7_O', 'win_gcc_7.1_O'], [
        'linux_gcc_6_O', 'win_gcc_6.2_O'], ['linux_gcc_5_O', 'win_gcc_5.2_O'], ['linux_gcc_4.8_O', 'win_gcc_4.9_O']]

    all_pairs = []
    all_f_sigs = []
    for case_pair in compilation_case_pairs:
        for i in ['0', '1', '2', '3']:
            l_fea_js = os.path.join(fea_js_path, case_pair[0]+i+'.json')
            r_fea_js = os.path.join(fea_js_path, case_pair[1]+i+'.json')
            if os.path.exists(l_fea_js) and os.path.exists(r_fea_js):
                pairs, f_sigs = get_pairs(l_fea_js, r_fea_js)
                all_pairs += pairs
                all_f_sigs += f_sigs
    print('func num: ', len(set(all_f_sigs)))
    print('graph num:', len(all_pairs)*2)
    print('pair num: ', len(all_pairs))
    save_data(all_pairs, pairs_save_path)


def get_os_diff_linux_mac_pairs(fea_js_path, pairs_save_path):
    compilation_case_pairs = [['linux_gcc_9_O', 'mac_gcc_9_O'], ['linux_gcc_8_O', 'mac_gcc_8_O'], [
        'linux_gcc_7_O', 'mac_gcc_7_O'], ['linux_gcc_6_O', 'mac_gcc_6_O']]

    all_pairs = []
    all_f_sigs = []
    for case_pair in compilation_case_pairs:
        for i in ['0', '1', '2', '3']:
            l_fea_js = os.path.join(fea_js_path, case_pair[0]+i+'.json')
            r_fea_js = os.path.join(fea_js_path, case_pair[1]+i+'.json')
            if os.path.exists(l_fea_js) and os.path.exists(r_fea_js):
                pairs, f_sigs = get_pairs(l_fea_js, r_fea_js)
                all_pairs += pairs
                all_f_sigs += f_sigs
    print('func num: ', len(set(all_f_sigs)))
    print('graph num:', len(all_pairs)*2)
    print('pair num: ', len(all_pairs))
    save_data(all_pairs, pairs_save_path)


def get_os_diff_win_mac_pairs(fea_js_path, pairs_save_path):
    compilation_case_pairs = [['win_gcc_8.1_O', 'mac_gcc_8_O'], [
        'win_gcc_7.1_O', 'mac_gcc_7_O'], ['win_gcc_6.2_O', 'mac_gcc_6_O']]

    all_pairs = []
    all_f_sigs = []
    for case_pair in compilation_case_pairs:
        for i in ['0', '1', '2', '3']:
            l_fea_js = os.path.join(fea_js_path, case_pair[0]+i+'.json')
            r_fea_js = os.path.join(fea_js_path, case_pair[1]+i+'.json')
            if os.path.exists(l_fea_js) and os.path.exists(r_fea_js):
                pairs, f_sigs = get_pairs(l_fea_js, r_fea_js)
                all_pairs += pairs
                all_f_sigs += f_sigs
    print('func num: ', len(set(all_f_sigs)))
    print('graph num:', len(all_pairs)*2)
    print('pair num: ', len(all_pairs))
    save_data(all_pairs, pairs_save_path)


def get_cc_diff_pairs(fea_js_path, pairs_save_path):
    compilation_case_pairs = [['linux_clang_3.5_O', 'linux_gcc_4.8_O'], ['linux_clang_3.8_O', 'linux_gcc_5_O'], [
        'linux_clang_4.0_O', 'linux_gcc_6_O'], ['linux_clang_5.0_O', 'linux_gcc_7_O'], ['linux_clang_6.0_O', 'linux_gcc_8_O']]

    all_pairs = []
    all_f_sigs = []
    for case_pair in compilation_case_pairs:
        for i in ['0', '1', '2', '3']:
            l_fea_js = os.path.join(fea_js_path, case_pair[0]+i+'.json')
            r_fea_js = os.path.join(fea_js_path, case_pair[1]+i+'.json')
            if os.path.exists(l_fea_js) and os.path.exists(r_fea_js):
                pairs, f_sigs = get_pairs(l_fea_js, r_fea_js)
                all_pairs += pairs
                all_f_sigs += f_sigs
    print('func num: ', len(set(all_f_sigs)))
    print('graph num:', len(all_pairs)*2)
    print('pair num: ', len(all_pairs))
    save_data(all_pairs, pairs_save_path)


def get_arch_diff_pairs(fea_js_path, pairs_save_path):
    compilation_case_pairs = [['arm_arm-linux-gnueabi-gcc_5.4_O', 'linux_gcc_5_O'], ['arm_arm-linux-gnueabihf-gcc_5.4_O', 'linux_gcc_5_O']]

    all_pairs = []
    all_f_sigs = []
    for case_pair in compilation_case_pairs:
        for i in ['0', '1', '2', '3']:
            l_fea_js = os.path.join(fea_js_path, case_pair[0]+i+'.json')
            r_fea_js = os.path.join(fea_js_path, case_pair[1]+i+'.json')
            if os.path.exists(l_fea_js) and os.path.exists(r_fea_js):
                pairs, f_sigs = get_pairs(l_fea_js, r_fea_js)
                all_pairs += pairs
                all_f_sigs += f_sigs
    print('func num: ', len(set(all_f_sigs)))
    print('graph num:', len(all_pairs)*2)
    print('pair num: ', len(all_pairs))
    save_data(all_pairs, pairs_save_path)


def get_max_diff_pairs(fea_js_path, pairs_save_path):
    compilation_case_pairs = [['arm_arm-linux-gnueabihf-gcc_5.4_O3', 'mac_clang_12_O0'], ['arm_arm-linux-gnueabihf-gcc_5.4_O0',
'mac_clang_12_O3'], ['arm_arm-linux-gnueabi-gcc_5.4_O0', 'win_gcc_8.1_O3'], ['arm_arm-linux-gnueabi-gcc_5.4_O3', 'win_gcc_8.1_O0']]

    all_pairs = []
    all_f_sigs = []
    for case_pair in compilation_case_pairs:
        l_fea_js = os.path.join(fea_js_path, case_pair[0]+'.json')
        r_fea_js = os.path.join(fea_js_path, case_pair[1]+'.json')
        if os.path.exists(l_fea_js) and os.path.exists(r_fea_js):
            pairs, f_sigs = get_pairs(l_fea_js, r_fea_js)
            all_pairs += pairs
            all_f_sigs += f_sigs

    print('func num: ', len(set(all_f_sigs)))
    print('graph num:', len(all_pairs)*2)
    print('pair num: ', len(all_pairs))
    save_data(all_pairs, pairs_save_path)


def get_cc_version_diff_pairs(fea_js_path, pairs_save_path):
    compilation_case_pairs = [['linux_clang_3.5_O', 'linux_clang_5.0_O'], ['linux_clang_3.8_O', 'linux_clang_6.0_O'], ['linux_gcc_4.8_O', 'linux_gcc_8_O'], ['linux_gcc_6_O', 'linux_gcc_9_O']]

    all_pairs = []
    all_f_sigs = []
    for case_pair in compilation_case_pairs:
        for i in ['0', '1', '2', '3']:
            l_fea_js = os.path.join(fea_js_path, case_pair[0]+i+'.json')
            r_fea_js = os.path.join(fea_js_path, case_pair[1]+i+'.json')
            if os.path.exists(l_fea_js) and os.path.exists(r_fea_js):
                pairs, f_sigs = get_pairs(l_fea_js, r_fea_js)
                all_pairs += pairs
                all_f_sigs += f_sigs
    print('func num: ', len(set(all_f_sigs)))
    print('graph num:', len(all_pairs)*2)
    print('pair num: ', len(all_pairs))
    save_data(all_pairs, pairs_save_path)



def get_oplevel_pairs(fea_js_path, pairs_save_path, l_level, r_level):
    f_names = os.listdir(fea_js_path)
    valid_cases = []
    for f_name in f_names:
        if f_name.startswith('arm_x86') or f_name.startswith('linux_gcc_5') or f_name.startswith('linux_gcc_6') or f_name.startswith('linux_gcc_6') or f_name.startswith('linux_gcc_7') or f_name.startswith('linux_gcc_8') or f_name.startswith('mac_gcc_8') or f_name.startswith("linux_clang_3.8") or f_name.startswith("linux_clang_4.0") or f_name.startswith("linux_clang_5.0") or f_name.startswith("mac_gcc_7"):
            continue
        valid_cases.append(f_name[:-6])

    all_pairs = []
    all_f_sigs = []
    for comp_case in valid_cases:
        l_fea_js = os.path.join(fea_js_path, comp_case+'{0}.json'.format(l_level))
        r_fea_js = os.path.join(fea_js_path, comp_case+'{0}.json'.format(r_level))
        if os.path.exists(l_fea_js) and os.path.exists(r_fea_js):
            pairs, f_sigs = get_pairs(l_fea_js, r_fea_js)
            all_pairs += pairs
            all_f_sigs += f_sigs
    print('func num: ', len(set(all_f_sigs)))
    print('graph num:', len(all_pairs)*2)
    print('pair num: ', len(all_pairs))
    save_data(all_pairs, pairs_save_path)


def unique_l3(fea_js_path, pairs_save_path, l_level=0, r_level=3):
    f_names = os.listdir(fea_js_path)
    valid_cases = []
    for f_name in f_names:
        if f_name.startswith('arm_x86') or f_name.startswith('linux_gcc_5') or f_name.startswith('linux_gcc_6') or f_name.startswith('linux_gcc_6') or f_name.startswith('linux_gcc_7') or f_name.startswith('linux_gcc_8') or f_name.startswith('mac_gcc_8') or f_name.startswith("linux_clang_3.8") or f_name.startswith("linux_clang_4.0") or f_name.startswith("linux_clang_5.0") or f_name.startswith("mac_gcc_7"):
            continue
        valid_cases.append(f_name[:-6])

    all_pairs = []
    all_f_sigs = []
    for comp_case in valid_cases:
        l_fea_js = os.path.join(fea_js_path, comp_case+'{0}.json'.format(l_level))
        r_fea_js = os.path.join(fea_js_path, comp_case+'{0}.json'.format(r_level))
        if os.path.exists(l_fea_js) and os.path.exists(r_fea_js):
            pairs = []
            l_fea_d = {}
            r_fea_d = {}
            f_sigs = []
            with open(l_fea_js) as load_f:
                for line in load_f:
                    l_fea = json.loads(line.strip())
                    l_fea_d[l_fea['fname']] = l_fea

            with open(r_fea_js) as load_f:
                for line in load_f:
                    r_fea = json.loads(line.strip())
                    r_fea_d[r_fea['fname']] = r_fea

            for f_sig in r_fea_d:
                if f_sig not in l_fea_d:
                    print(f_sig)


if __name__ == '__main__':
    fea_js_gemini = '/mnt/d/data/vector_gemini_format/valid'
    fea_js_ghidra = '../data/func_comparison/vector_ghidra_format/valid'

    # subset1: os diff subset, linux - win
    os_diff_linux_win_7_fea_dim = '/mnt/d/data/valid_pairs_v1/os_diff_linux_win_7_fea_dim.json'
    os_diff_linux_win_76_fea_dim = '/mnt/d/data/valid_pairs_v1/os_diff_linux_win_76_fea_dim.json'
    # get_os_diff_linux_win_pairs(fea_js_gemini, os_diff_linux_win_7_fea_dim)
    # get_os_diff_linux_win_pairs(fea_js_ghidra, os_diff_linux_win_76_fea_dim)

    # subset1: os diff subset, linux - mac
    os_diff_linux_mac_7_fea_dim = '/mnt/d/data/valid_pairs_v1/os_diff_linux_mac_7_fea_dim.json'
    os_diff_linux_mac_76_fea_dim = '/mnt/d/data/valid_pairs_v1/os_diff_linux_mac_76_fea_dim.json'
    # get_os_diff_linux_mac_pairs(fea_js_gemini, os_diff_linux_mac_7_fea_dim)
    # get_os_diff_linux_mac_pairs(fea_js_ghidra, os_diff_linux_mac_76_fea_dim)

    # subset1: os diff subset, mac win
    os_diff_win_mac_7_fea_dim = '/mnt/d/data/valid_pairs_v1/os_diff_win_mac_7_fea_dim.json'
    os_diff_win_mac_76_fea_dim = '/mnt/d/data/valid_pairs_v1/os_diff_win_mac_76_fea_dim.json'
    # get_os_diff_win_mac_pairs(fea_js_gemini, os_diff_win_mac_7_fea_dim)
    # get_os_diff_win_mac_pairs(fea_js_ghidra, os_diff_win_mac_76_fea_dim)

    # subset2: arch diff subset, arm, x86
    arch_diff_7_fea_dim = '/mnt/d/data/valid_pairs_v1/arch_diff_7_fea_dim.json'
    arch_diff_76_fea_dim = '/mnt/d/data/valid_pairs_v1/arch_diff_76_fea_dim.json'
    # get_arch_diff_pairs(fea_js_gemini, arch_diff_7_fea_dim)
    # get_arch_diff_pairs(fea_js_ghidra, arch_diff_76_fea_dim)

    # subset3: cc diff subset, linux clang , linux gcc
    cc_diff_7_fea_dim = '/mnt/d/data/valid_pairs_v1/cc_diff_7_fea_dim.json'
    cc_diff_76_fea_dim = '/mnt/d/data/valid_pairs_v1/cc_diff_76_fea_dim.json'
    # get_cc_diff_pairs(fea_js_gemini, cc_diff_7_fea_dim)
    # get_cc_diff_pairs(fea_js_ghidra, cc_diff_76_fea_dim)

    # subset4: optimization level diff
    max_oplevel_pairs_7_fea_dim = '/mnt/d/data/valid_pairs_v1/max_oplevel_pairs_7_fea_dim.json'
    max_oplevel_pairs_76_fea_dim = '/mnt/d/data/valid_pairs_v1/max_oplevel_pairs_76_fea_dim.json'
    # get_max_oplevel_pairs(fea_js_gemini, max_oplevel_pairs_7_fea_dim)
    # get_max_oplevel_pairs(fea_js_ghidra, max_oplevel_pairs_76_fea_dim)

    # subset5: max diff
    max_diff_pairs_7_fea_dim = '/mnt/d/data/valid_pairs_v1/max_diff_pairs_7_fea_dim.json'
    max_diff_pairs_76_fea_dim = '/mnt/d/data/valid_pairs_v1/max_diff_pairs_76_fea_dim.json'
    # get_max_diff_pairs(fea_js_gemini, max_diff_pairs_7_fea_dim)
    # get_max_diff_pairs(fea_js_ghidra, max_diff_pairs_76_fea_dim)


    ## cc version
    cc_version_diff_7_fea_dim = '/mnt/d/data/valid_pairs_v1/cc_version_diff_7_fea_dim.json'
    cc_version_diff_76_fea_dim = '/mnt/d/data/valid_pairs_v1/cc_version_diff_76_fea_dim.json'
    # get_cc_version_diff_pairs(fea_js_gemini, cc_version_diff_7_fea_dim)
    # get_cc_version_diff_pairs(fea_js_ghidra, cc_version_diff_76_fea_dim)


    oplevel_pairs_2_0_7_fea_dim = '/mnt/d/data/valid_pairs_v1/oplevel_pairs_2_0_7_fea_dim.json'

    a='../data/validation_pairs/valid_pairs_v1/76_fea_dim/'
    oplevel_pairs_2_0_76_fea_dim = './oplevel_pairs_2_0_76_fea_dim.json'
    # get_oplevel_pairs(fea_js_gemini, oplevel_pairs_2_0_7_fea_dim, 2, 0)
    get_oplevel_pairs(fea_js_ghidra, oplevel_pairs_2_0_76_fea_dim, 2, 0)

    oplevel_pairs_2_1_7_fea_dim = '/mnt/d/data/valid_pairs_v1/oplevel_pairs_2_1_7_fea_dim.json'
    oplevel_pairs_2_1_76_fea_dim = './oplevel_pairs_2_1_76_fea_dim.json'
    # get_oplevel_pairs(fea_js_gemini, oplevel_pairs_2_1_7_fea_dim, 2, 1)
    get_oplevel_pairs(fea_js_ghidra, oplevel_pairs_2_1_76_fea_dim, 2, 1)

    oplevel_pairs_2_3_7_fea_dim = '/mnt/d/data/valid_pairs_v1/oplevel_pairs_2_3_7_fea_dim.json'
    oplevel_pairs_2_3_76_fea_dim = './oplevel_pairs_2_3_76_fea_dim.json'
    # get_oplevel_pairs(fea_js_gemini, oplevel_pairs_2_3_7_fea_dim, 2, 3)
    get_oplevel_pairs(fea_js_ghidra, oplevel_pairs_2_3_76_fea_dim, 2, 3)
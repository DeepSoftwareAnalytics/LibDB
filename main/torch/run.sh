out_dir=saved_model
mkdir -p $out_dir

train_valid_dir=~/sci2/user/data/func_comparison/vector_deduplicate_our_format_less_compilation_cases/train_test

test_data_dir=~/sci2/user/data/func_comparison/vector_deduplicate_our_format_less_compilation_cases/valid

python torch_main.py --fea_dim 7 --save_path $out_dir --train_valid $train_valid_dir --test_data $test_data_dir
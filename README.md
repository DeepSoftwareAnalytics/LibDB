# binary_tpl_detection

Dataset url: https://figshare.com/s/4a007e78f29243531b8c

## Feature Extractor
- The extractor extracts features from all binary files under a given directory and save features to a json file. 
- Input: directory
- Output: two files, stored in a given target directory. 
    - Information such as running time is stored in the `status` file. 
    - Extracted features are stored in the features file, such as `9760608.json`. The format of this json is a list of BinaryFile entity.  
- It is recommended to put your task code under `consumer` directory (in `featureExtractor/bcat_client/src/main/java/thusca/bcat/client/consumer`). See the example in `consumer/BinFileFeatureExtractTest.java`

### Pre-requisites
Basic knowledge about Java Development, Springboot and Annotation Development.<br>
For example, if you use IDE like VScode or Idea, basic java development environment need to be installed such as `Java Extension Pack`, `MAVEN for JAVA`. It should be noted that we use Lombok Annotation and Springboot in code that may depend on extensions `Lombok Annotations Support` and `Spring Boot Tools` for IDE to debug or run. Besides, LibmagicJnaWrapper depends on libmagic to get file type, please install this library and modify the paths in LibmagicJnaWrapper.java. It can be easily installed using apt/brew command on Linux/MacOS.

### Build Artifact
Env:
- Java: Java 11.
- IntelliJ Idea. (We have found that the extractor artifact works well only under IntelliJ Idea to build the artifact. Tested successful under Windows IntelliJ Idea 2021.2) 

Steps:
1. Ghidra: 9.1.2. The file `ghidra.jar` is stored under `/user/lib/ghidra.jar` you should put it under `/featureExtractor/bcat_client/lib` first.
2. Open Idea, open project "binary_lib_detection-main\featureExtractor". Wait until indexing finish, if error occurs, try reopen/clean the project.
3. File -> Project Structure -> Project SDK, select Java SDK 11.
4. File -> Project Structure -> Artifacts -> "+" -> jar -> from modules with dependencies -> Module ("bcat_client") -> Main Class ("ClientApplication") -> JAR files from libraries (select `copy to the output directory and link via manifest`) 
    5. The jars will be generated at path: featureExtractor\out\artifacts\bcat_client_jar, with `bcat_client.jar` inside.

### Task
Methods for all tasks are stored under the directory `/consumer`.
Building database: Code:`Task2ExtractCoreFedora.java`, Data: `FedoraLib_Dataset`. Set tha save path and get all features to build TPL feature database. We use the directory `../data/CoreFedoraFeatureJson0505` to represent the save path.

### Run
Zip the bcat_client_jar folder and upload to a Linux server, unzip, and run:
```shell
java -jar bcat_client.jar
```

Note: Java 11 required.

## Func similarity Model
This model is used to determine if two functions are similar based on [Gemini](https://github.com/xiaojunxu/dnn-binary-code-similarity) Network.

Prepration and Data
Data is stored in `../data/vector_deduplicate_gemini_format_less_compilation_cases`.<br>
or Cross-5C_Dataset.7z on figshare.

By default, we use the path `../data` under `main/torch` to store the data. Please copy them under it.

### Environment Step
The network is written using Torch 1.8 in Python 3.8. Torch installation is based on cuda 11.

```
conda create -n tpldetection python=3.8 ipykernel
bash
conda activate tpldetection
pip install torch==1.8.1+cu111 torchvision==0.9.1+cu111 torchaudio==0.8.1 -f https://download.pytorch.org/whl/lts/1.8/torch_lts.html
pip install -r requirements.txt
```

Milvus v1.1.1(vector search engine) is necessary for function retrival. It requires docker 19.03 or higher
ref: https://milvus.io/docs/v1.1.1/milvus_docker-gpu.md
```shell
sudo docker pull milvusdb/milvus:1.1.1-gpu-d061621-330cc6
mkdir -p /home/$USER/milvus/conf
cd /home/$USER/milvus/conf
wget https://raw.githubusercontent.com/milvus-io/milvus/v1.1.1/core/conf/demo/server_config.yaml

sudo docker run -d --name milvus_gpu_1.1.1 --gpus all \
-p 19530:19530 \
-p 19121:19121 \
-v /home/$USER/milvus/db:/var/lib/milvus/db \
-v /home/$USER/milvus/conf:/var/lib/milvus/conf \
-v /home/$USER/milvus/logs:/var/lib/milvus/logs \
-v /home/$USER/milvus/wal:/var/lib/milvus/wal \
milvusdb/milvus:1.1.1-gpu-d061621-330cc6
```

## Run
Run the following command to train the model:
```shell
# train/validation dataset: /data/func_comparison/vector_deduplicate_our_format_less_compilation_cases/train_test
# test dataset: /data/func_comparison/vector_deduplicate_our_format_less_compilation_cases/valid
cd main/torch
bash run.sh
```
A trained model is saved under `../data/7fea_contra_torch_b128/saved_model/`

## Library detection

### Database
#### Embedding
raw feature database: `../data/CoreFedoraFeatureJson0505`

Embeddings:
set the path `../data/CoreFedoraFeatureJson0505` as `args.fedora_js`.
You can use mutilprocess to speed up and the code is writen in `core_fedora_embeddings.py` as follows:
```python
with Pool(10) as p:
    p.starmap(core_fedora_embedding, [(i, True) for i in range(10)])
```
all embeddings are saved under the `args.save_path`.
We use the path `../data/7fea_contra_torch_b128/core_funcs` to represent it.

#### Indexing and Building Milvus dataset
run `build_milvus_database.py` to build function vector database using Mulvis.

the function `get_bin_fcg` is used to generate an indexing file containing binary to functions to accelarate.

`get_bin2func_num` generates an indexing from binary to the number of funtions in it.


#### Detection
Data: detection_targets. Firstly, extract features from APKs. See the method `localExtractOSSPoliceApks` in `TaskProcessTargets.java` under the directory `consumer`. We use the directory`../data/detection_targets/feature_json` to save all extracted features.

see the function `detect_v2` in function_vector_channel.
Other methods + FCG Filter can be seen in files `xxx_afcg.py`.
Baselines are under the directory `/related_work`.

We combine basic feature channel (B2SFinder(basic features) + FCG Filter) and function vector channel together to report the final results.

All files named `analyze_results.py` are used to calculate precision and recall.








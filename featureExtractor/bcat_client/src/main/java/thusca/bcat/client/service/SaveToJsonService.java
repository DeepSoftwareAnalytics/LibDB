package thusca.bcat.client.service;

import com.alibaba.fastjson.JSON;
import org.springframework.stereotype.Service;
import thusca.bcat.client.entity.BinaryFile;
import thusca.bcat.client.entity.FeatureExtractStatus;
import thusca.bcat.client.utils.FileUtil;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.List;
import java.util.UUID;

import org.apache.log4j.Logger;

@Service
public class SaveToJsonService {
    private final Logger logger = Logger.getLogger(this.getClass());

    public File saveBinaryFileToJson (BinaryFile binaryFile, String targetDirPath) throws IOException {
        File targetDir = new File(targetDirPath);
        if (!targetDir.exists()) {
            targetDir.mkdirs();
        }
        String jsonFileName = binaryFile.getFormattedFileName() + ".json";
        File targetJsonFile = new File(targetDir, jsonFileName);
        logger.info("write feature to json: " + targetJsonFile.getCanonicalPath());
        FileUtil.saveStringToFile(targetJsonFile.getCanonicalPath(), JSON.toJSONString(binaryFile), false);
        return targetJsonFile;
    }

    public File saveBinaryFileListToJson(List<BinaryFile> binaryFiles, String targetDirPath, String id)  throws IOException{
        File targetDir = new File(targetDirPath);
        if (!targetDir.exists()) {
            targetDir.mkdirs();
        }
        String jsonFileName = id+ ".json";
        File targetJsonFile = new File(targetDir, jsonFileName);
        logger.info("write feature to json: " + targetJsonFile.getCanonicalPath());
        FileUtil.saveStringToFile(targetJsonFile.getCanonicalPath(), JSON.toJSONString(binaryFiles), false);
        return targetJsonFile;
    }

    public void saveStatusToJson(FeatureExtractStatus status, String targetDirPath) {
        File targetDir = new File(targetDirPath);
        if (!targetDir.exists()) {
            targetDir.mkdirs();
        }
        try {
            File targetJsonFile = new File(targetDir, "status");
            FileUtil.saveStringToFile(targetJsonFile.getCanonicalPath(), JSON.toJSONString(status), false);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }


}

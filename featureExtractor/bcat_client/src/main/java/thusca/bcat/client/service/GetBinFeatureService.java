package thusca.bcat.client.service;

import org.springframework.stereotype.Component;
import org.springframework.stereotype.Service;
import thusca.bcat.client.entity.BinFileFeature;
import thusca.bcat.client.entity.BinaryFile;
import thusca.bcat.client.utils.BinaryAnalyzer;
import thusca.bcat.client.utils.StatusMsg;

import java.io.File;

@Component
public class GetBinFeatureService {
    public StatusMsg getBinFileFeature(BinaryFile binaryFile, File ghidraProjectTmpDir, String jsonPath, String fileType) {
        BinaryAnalyzer binaryAnalyzer = new BinaryAnalyzer(binaryFile.getFilePath(), ghidraProjectTmpDir.getAbsolutePath(), jsonPath, fileType);
        StatusMsg statusMsg =  binaryAnalyzer.extractFeatures();
        BinFileFeature binFileFeature = binaryAnalyzer.getBinFileFeature();
        binaryFile.setBinFileFeature(binFileFeature);
        binaryFile.setIsProcessed(true);
        statusMsg.setFilePath(binaryFile.getFilePath());
        return statusMsg;
    }
}
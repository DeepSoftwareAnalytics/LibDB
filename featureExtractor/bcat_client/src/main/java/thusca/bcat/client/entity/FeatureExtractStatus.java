package thusca.bcat.client.entity;

import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
public class FeatureExtractStatus {
    private boolean getBinFiles = false;
    private List<String> binFileNameList = new ArrayList<>();
    private long getBinFileTime = 0;

    private List<successfullyExtractedBinFeature> successfullyExtractedBinFeatureList = new ArrayList<>();
    private List<failedExtractedBinFeature> failedExtractedBinFeatureList = new ArrayList<>();
    private long getBinFeatureTime = 0;

    private List<successfullySavedJson> successfullySavedJsonList = new ArrayList<>();
    private List<failedSavedJson> failedSavedJsonList = new ArrayList<>();
    private long saveJsonTime = 0;

    public int extracted = 0; 
    private int extractedStatus = 0;
    private long extractedTime = 0;

    private List<String> errorMessages = new ArrayList<>();

    public void addSuccessfullyExtractedBinFeature(String binFileName, long time, long byteSize) {
        successfullyExtractedBinFeatureList.add(new successfullyExtractedBinFeature(binFileName, time, byteSize));
    }

    public void addFailedExtractedBinFeature(String binFileName, String errorMessage) {
        failedExtractedBinFeatureList.add(new failedExtractedBinFeature(binFileName, errorMessage));
    }

    public void addSuccessfullySavedJson(String binFileName, long time, long byteSize) {
        successfullySavedJsonList.add(new successfullySavedJson(binFileName, time, byteSize));
    }

    public void addfailedSavedJson(String binFileName, String errorMessage) {
        failedSavedJsonList.add(new failedSavedJson(binFileName, errorMessage));
    }


}

@Data
class successfullyExtractedBinFeature {
    private String binFileName;
    private long byteSize;
    private long time;
    successfullyExtractedBinFeature(String binFileName, long time, long byteSize) {
        this.binFileName = binFileName;
        this.time = time;
        this.byteSize = byteSize;
    }
}

@Data
class failedExtractedBinFeature {
    private String binFileName;
    private String errorMessage;
    failedExtractedBinFeature(String binFileName, String errorMessage) {
        this.binFileName = binFileName;
        this.errorMessage = errorMessage;
    }
}

@Data
class successfullySavedJson {
    private String binFileName;
    private long time;
    private long byteSize;
    successfullySavedJson(String binFileName, long time, long byteSize) {
        this.binFileName = binFileName;
        this.time = time;
        this.byteSize = byteSize;
    }
}

@Data
class failedSavedJson {
    private String binFileName;
    private String errorMessage;
    failedSavedJson(String binFileName, String errorMessage) {
        this.binFileName = binFileName;
        this.errorMessage = errorMessage;
    }
}

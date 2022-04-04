package thusca.bcat.client.service;

import org.apache.log4j.Logger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Scope;
import org.springframework.stereotype.Service;
import thusca.bcat.client.entity.BinaryFile;
import thusca.bcat.client.entity.FeatureExtractStatus;
import thusca.bcat.client.utils.FileUtil;
import thusca.bcat.client.utils.LibmagicJnaWrapper;
import thusca.bcat.client.utils.StatusMsg;

import java.io.File;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.concurrent.*;

@Service("ExtractService")
@Scope("prototype")
public class ExtractService {
    private List<BinaryFile> binaryFileList = new ArrayList<>();
    protected String COMPONENT_PATH;
    protected String JSON_SAVE_ROOT_PATH;
    protected String GHIDRA_TMP_PATH;
    protected Integer PACKAGE_ID;
    public FeatureExtractStatus STATUS = new FeatureExtractStatus();

    private final Logger logger = Logger.getLogger(this.getClass());

//    private ExecutorService cachedThreadPool;

    @Autowired
    GetBinFileService getBinFileService;

    @Autowired
    GetBinFeatureService getBinFeatureService;

    @Autowired
    SaveToJsonService saveToJsonService;

    public void init(String componentPath, String jsonSaveRootPath, String ghidraTmp, int packageId) {
        STATUS = new FeatureExtractStatus();
        COMPONENT_PATH = componentPath;
        PACKAGE_ID = packageId;
        JSON_SAVE_ROOT_PATH = jsonSaveRootPath;
        GHIDRA_TMP_PATH = ghidraTmp;
    }


    public void executable() {
        long startTime = System.currentTimeMillis();
        try {
            STATUS.setExtractedStatus(1);
            executableDetail();
        } catch (Exception e) {
            logger.info(PACKAGE_ID + " : executable Error:  " + e);
            STATUS.setExtractedStatus(2);
            e.printStackTrace();
        } finally {
            STATUS.setExtractedTime(System.currentTimeMillis() - startTime);
            logger.info("write status to json..." + JSON_SAVE_ROOT_PATH);
            saveToJsonService.saveStatusToJson(STATUS, JSON_SAVE_ROOT_PATH);
        }
    }

    protected void executableDetail() {
        try {
            binaryFileList = getBinFileService.getBinaryFiles(COMPONENT_PATH, STATUS);
        } catch (Exception e) {
            System.out.println("exception:  " + binaryFileList.size());
            e.printStackTrace();
        }

        System.out.println("start extract file:" + COMPONENT_PATH);
        // 获取特征
        long startTime = System.currentTimeMillis();
        File ghidraProjectTmpDir = null;
        String fileName = "";
        String fileType = "";
        List<BinaryFile> binaryFiles = new ArrayList<>();

        try {
            for (BinaryFile binaryFile : binaryFileList) {
                ghidraProjectTmpDir = FileUtil.createTempFile(GHIDRA_TMP_PATH);
                fileName = binaryFile.getFileName();
                fileType = binaryFile.getFileType();
                StatusMsg[] statusMsgs = {new StatusMsg()};
                try {
                    File subFile = new File(binaryFile.getFilePath());
                    if (!subFile.isFile()) {
                        logger.info("ERROR: " + PACKAGE_ID + " _ " + binaryFile.getFilePath() + " - -  no such file...");
                    }
                    ExecutorService executor = Executors.newSingleThreadExecutor();
                    TimerTask task = new TimerTask(binaryFile, ghidraProjectTmpDir, statusMsgs, fileType);
                    Future<Boolean> f1 = executor.submit(task);
                    if (f1.get(30, TimeUnit.MINUTES)) {
                        logger.info(PACKAGE_ID + " _ " + binaryFile.getFilePath() + " done within 30 minutes...");
                    } else {
                        statusMsgs[0].setErrMsg("over time");
                        statusMsgs[0].setOK(false);
                        logger.info(PACKAGE_ID + " _ " + binaryFile.getFilePath() + " over time: more than 30 minutes...");
                        STATUS.addFailedExtractedBinFeature(binaryFile.getFileName(), "over time");
                    }
                } catch (Exception e) {
                    e.printStackTrace();
                    statusMsgs[0].setOK(false);
                    logger.info(PACKAGE_ID + " _ " + binaryFile.getFileName() + "  ERROR... maybe, time over: " + e);
                    STATUS.getErrorMessages().add(fileName + " : " + e.getMessage());
                    STATUS.setExtractedStatus(2);
                } finally {
                    if (!statusMsgs[0].isOK()) {
                        STATUS.setExtractedStatus(2);
                    } else {
                        binaryFiles.add(binaryFile);
                    }
                    if (ghidraProjectTmpDir != null && ghidraProjectTmpDir.isDirectory()) {
                        ghidraProjectTmpDir.delete();
                    }
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
            logger.info(PACKAGE_ID + " ERROR...excutableDetail  to extract feature:    " + " : " + e);
            STATUS.setExtractedStatus(2);
        } finally {
            STATUS.setGetBinFeatureTime(System.currentTimeMillis() - startTime);
            postExtract(binaryFiles, STATUS);
        }
    }

    private StatusMsg getFeatureNoTimer(BinaryFile binaryFile, File ghidraProjectTmpDir) {
        StatusMsg statusMsg = new StatusMsg();
        statusMsg = getBinFeatureService.getBinFileFeature(binaryFile, ghidraProjectTmpDir, JSON_SAVE_ROOT_PATH, binaryFile.getFileType());
        return statusMsg;
    }

    protected void postExtract(List<BinaryFile> binaryFiles, FeatureExtractStatus status) {
        try {
            File featureJson = saveToJsonService.saveBinaryFileListToJson(binaryFiles, JSON_SAVE_ROOT_PATH, PACKAGE_ID.toString());
        } catch (Exception e) {
            STATUS.addfailedSavedJson(PACKAGE_ID.toString(), e.getMessage());
        }
    }


    class TimerTask implements Callable<Boolean> {
        BinaryFile binaryFile;
        File ghidraProjectTmpDir;
        StatusMsg[] statusMsg;
        String fileType;

        public TimerTask(BinaryFile binaryFile, File ghidraProjectTmpDir, StatusMsg[] statusMsg, String fileType) {
            this.binaryFile = binaryFile;
            this.ghidraProjectTmpDir = ghidraProjectTmpDir;
            this.statusMsg = statusMsg;
            this.fileType = fileType;
        }

        @Override
        public Boolean call() throws Exception {
            statusMsg[0] = getBinFeatureService.getBinFileFeature(binaryFile, ghidraProjectTmpDir, JSON_SAVE_ROOT_PATH, fileType);
            return true;
        }
    }
}
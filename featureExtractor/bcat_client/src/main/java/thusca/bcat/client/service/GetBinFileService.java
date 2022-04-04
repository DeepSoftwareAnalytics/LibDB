package thusca.bcat.client.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import thusca.bcat.client.entity.BinaryFile;
import thusca.bcat.client.entity.FeatureExtractStatus;
import thusca.bcat.client.utils.LibmagicJnaWrapperBean;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Iterator;
import java.util.List;

@Service
public class GetBinFileService {

    @Autowired
    LibmagicJnaWrapperBean LIB_MAGIC_WRAPPER;

    public String fileType;

    private List<String> fileTypes = new ArrayList<>(Arrays.asList("ELF", "Mach-O", "PE"));

    public void getFiles(File rootFile, List<File> fileList) {
        File[] files = rootFile.listFiles();
        for (File f : files) {
            if (f.isDirectory() && !Files.isSymbolicLink(f.toPath())) {
                getFiles(f, fileList);
            } else if (f.isFile() && !Files.isSymbolicLink(f.toPath())) {
                fileList.add(f);
            }
        }
    }

    public List<BinaryFile> getBinaryFiles(String componentPath, FeatureExtractStatus status) {
        List<BinaryFile> binaryFileList = new ArrayList<>();
        long startTime = System.currentTimeMillis();
        File rootFile = new File(componentPath);
        if (!rootFile.exists()) return binaryFileList;

        List<File> fileList = new ArrayList<>();
        getFiles(rootFile, fileList);

        Iterator<File> fileIterator = fileList.iterator();
        while (fileIterator.hasNext()) {
            File subFile = fileIterator.next();
            if (subFile.isFile()) {
                fileType = LIB_MAGIC_WRAPPER.getMimeType(subFile.getAbsolutePath());
                for (String fileTypePrefix : fileTypes) {
                    if (fileType.startsWith(fileTypePrefix)) {
                        status = getFileList(componentPath, status, subFile, fileTypePrefix, binaryFileList);
                    }
                }
            }
        }
        status.setGetBinFiles(true);
        status.setGetBinFileTime(System.currentTimeMillis() - startTime);
        return binaryFileList;
    }

    public FeatureExtractStatus getFileList(String componentPath, FeatureExtractStatus status, File subFile, String fileType, List<BinaryFile> binaryFileList) {
        try {
            BinaryFile binFile = new BinaryFile(subFile.getCanonicalPath(), subFile.getName());
            binFile.setFileType(fileType);
            String formattedFileName = binFile.getFilePath().replace(componentPath, "").replace("/", "____");
            if (formattedFileName.startsWith("____")) {
                formattedFileName = formattedFileName.substring(4);
            }
            binFile.setFormattedFileName(formattedFileName);

            binaryFileList.add(binFile);
            status.getBinFileNameList().add(formattedFileName);
        } catch (IOException e) {
            status.getErrorMessages().add(e.getMessage());
        }
        return status;
    }
}

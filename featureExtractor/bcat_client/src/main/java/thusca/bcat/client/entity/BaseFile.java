package thusca.bcat.client.entity;

import java.io.File;

import lombok.Data;

@Data
public class BaseFile {
    protected String filePath;
    protected String fileName;
    protected Boolean isProcessed = false;
    protected long byteSize;

    public BaseFile(String filePath) {
        File tempFile = new File(filePath);
        this.filePath = filePath;
        this.fileName = tempFile.getName();
        this.byteSize = tempFile.length();
    }

    public BaseFile(String filePath, String fileName) {
        this.filePath = filePath;
        this.fileName = fileName;
        this.byteSize = new File(filePath).length();
    }
}

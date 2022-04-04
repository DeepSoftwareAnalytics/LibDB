package thusca.bcat.client.entity;

import lombok.Data;
@Data
public class BinaryFile extends BaseFile {
    protected BinFileFeature binFileFeature;
    private String formattedFileName;
    private String fileType;
    
    public BinaryFile(String filePath) {
        super(filePath);
    }

    public BinaryFile(String filePath, String fileName) {
        super(filePath, fileName);
    }
}

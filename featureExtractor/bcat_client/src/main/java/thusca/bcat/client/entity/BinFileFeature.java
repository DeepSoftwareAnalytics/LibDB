package thusca.bcat.client.entity;

import java.util.ArrayList;
import java.util.List;

import lombok.Data;

@Data
public class BinFileFeature {
    private String fileName;
    private String fileType;
    private List<String> importFunctionNames = new ArrayList<>();
    private List<String> exportFunctionNames = new ArrayList<>();
    private List<String> stringConstants = new ArrayList<>();
    private List<FunctionFeature> functions = new ArrayList<>();
}
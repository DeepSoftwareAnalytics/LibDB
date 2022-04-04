package thusca.bcat.client.consumer;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import thusca.bcat.client.entity.BinaryFile;
import thusca.bcat.client.entity.FeatureExtractStatus;
import thusca.bcat.client.service.GetBinFileService;
import thusca.bcat.client.utils.FileUtil;
import org.springframework.beans.factory.ObjectFactory;
import thusca.bcat.client.service.ExtractService;

import java.io.File;
import java.io.IOException;
import java.util.List;

/ @Component
public class TaskExtractFeatureLibs13 implements ApplicationRunner {
    private final Logger logger = LoggerFactory.getLogger(this.getClass());
    @Autowired
    ObjectFactory<ExtractService> extractServiceObjectFactory;

    @Override
    public void run(ApplicationArguments args) throws Exception {
        logger.info("Client start......");
        long startTime = System.currentTimeMillis();

        localExtract();

        long endTime = System.currentTimeMillis();
        logger.info(" " + (endTime - startTime) + "ms");
        System.exit(0);
    }

    public void localExtract() {
        String libsPath = "/mnt/c/Users/user/Desktop/data/binaryfiles13repos";
        String ghidraTmp = "/mnt/c/Users/user/Desktop/tmp/ghidraTmp";
        String jsonFileRootPath = "/mnt/c/Users/user/Desktop/data/featureJson";
        File prefixFile = new File(libsPath);

        for (File lib : prefixFile.listFiles()) {
            if (!lib.isDirectory()) {
                continue;
            }
            String[] sufNames = lib.toString().split("/", -1);
            String libName = sufNames[sufNames.length - 1];
            System.out.println(libName);

            for (File compilationCase : lib.listFiles()){
                if (!compilationCase.isDirectory()) {
                    continue;
                }
                sufNames = compilationCase.toString().split("/", -1);
                String caseName = sufNames[sufNames.length - 1];
                System.out.println(caseName);
                long startTime = System.currentTimeMillis();
                String savePath = jsonFileRootPath + "/" + libName + "/" + caseName;
                try{
                    ExtractService extractService = extractServiceObjectFactory.getObject();
                    extractService.init(compilationCase.toString(), savePath, ghidraTmp, 0);
                    extractService.executable();
                    logger.info(Thread.currentThread().getName() + " 提取完成:  " + (System.currentTimeMillis()-startTime) / 1000 + "s");
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        }
    }
}
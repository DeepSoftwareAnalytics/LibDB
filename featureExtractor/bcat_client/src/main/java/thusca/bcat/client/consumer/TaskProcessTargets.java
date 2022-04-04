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

// @Component
public class TaskProcessTargets implements ApplicationRunner {
    private final Logger logger = LoggerFactory.getLogger(this.getClass());
    @Autowired
    ObjectFactory<ExtractService> extractServiceObjectFactory;

    @Override
    public void run(ApplicationArguments args) throws Exception {
        logger.info("Client start......");
        long startTime = System.currentTimeMillis();

        localExtractOSSPoliceApks();
        // localExtractLibDXApks();

        long endTime = System.currentTimeMillis();
        logger.info("time cost: " + (endTime - startTime) + "ms");
        System.exit(0);
    }

    public void localExtractOSSPoliceApks() {
        String libsPath = "/mnt/c/Users/user/Desktop/detection_targets";
        String ghidraTmp = "/mnt/c/Users/user/Desktop/tmp/ghidraTmp";
        String jsonFileRootPath = "/mnt/c/Users/user/Desktop/data/featureJson";
        File prefixFile = new File(libsPath);

        for (File lib : prefixFile.listFiles()) {
            String[] sufNames = lib.toString().split("/", -1);
            String libName = sufNames[sufNames.length - 1];
            System.out.println(libName);

            long startTime = System.currentTimeMillis();
            String savePath = jsonFileRootPath + "/" + libName + "/";
            try{
                ExtractService extractService = extractServiceObjectFactory.getObject();
                extractService.init(lib.toString(), savePath, ghidraTmp, 0);
                extractService.executable();
                logger.info(Thread.currentThread().getName() + " done:  " + (System.currentTimeMillis()-startTime) / 1000 + "s");
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    public void localExtractLibDXApks(){
        String libsPath = "/mnt/c/Users/user/Desktop/detection_targets/unzipped_packages/DesktopApps";
        String ghidraTmp = "/mnt/c/Users/user/Desktop/tmp/ghidraTmp";
        String jsonFileRootPath = "/mnt/c/Users/user/Desktop/detection_targets/features/libdx_desktop";
        File prefixFile = new File(libsPath);
        for (File app : prefixFile.listFiles()) {
            String[] sufNames = app.toString().split("/", -1);
            String appName = sufNames[sufNames.length - 1];
            System.out.println(appName);
            for (File target: app.listFiles()) {
                sufNames = target.toString().split("/", -1);
                String targetName = sufNames[sufNames.length - 1];
                System.out.println(targetName);
                long startTime = System.currentTimeMillis();
                String savePath = jsonFileRootPath + "/" + appName + "/" + targetName + "/";
                File savePathFile = new File(savePath);
                if (savePathFile.exists()) {
                    continue;
                }

                try{
                    ExtractService extractService = extractServiceObjectFactory.getObject();
                    extractService.init(target.toString(), savePath, ghidraTmp, 0);
                    extractService.executable();
                    logger.info(Thread.currentThread().getName() + " 提取完成:  " + (System.currentTimeMillis()-startTime) / 1000 + "s");
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        }
    }
}
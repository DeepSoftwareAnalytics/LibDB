package thusca.bcat.client.consumer;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.ObjectFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;
import thusca.bcat.client.service.ExtractService;

//@Component
public class BinFileFeatureExtractTest implements ApplicationRunner {
    @Autowired
    @Qualifier("ExtractService")
    ObjectFactory<ExtractService> extractServiceObjectFactory;

    @Override
    public void run(ApplicationArguments args) throws Exception {
        Logger logger = LoggerFactory.getLogger(this.getClass());
        String ghidraTmp = "/mnt/c/Users/user/Desktop/tmp/ghidraTmp";
        String unzippedPackagePath = "/mnt/c/Users/user/Desktop/tmp/binaryTarget/test";
        String jsonFileRootPath = "/mnt/c/Users/user/Desktop/tmp/saveJson";
        int packageId = 12345678;
        long startTime = System.currentTimeMillis();
        try {
            ExtractService extractService = extractServiceObjectFactory.getObject();
            extractService.init(unzippedPackagePath, jsonFileRootPath, ghidraTmp, packageId);
            extractService.executable();
            logger.info(Thread.currentThread().getName() + " [Done]: "+ packageId);
        } catch (Exception e) {
            e.printStackTrace();
        }
        long endTime = System.currentTimeMillis();
        logger.info("running time: " + (endTime - startTime)/1000 + "s");
    }
}
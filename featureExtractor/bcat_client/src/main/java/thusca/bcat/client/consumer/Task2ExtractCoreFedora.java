package thusca.bcat.client.consumer;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;
import org.springframework.beans.factory.ObjectFactory;
import thusca.bcat.client.service.ExtractService;

import java.io.File;
import java.util.concurrent.*;

// @Component
public class Task2ExtractCoreFedora implements ApplicationRunner {

    private final Logger logger = LoggerFactory.getLogger(this.getClass());

    // tmp path
    @Value("${ghidra.tmp.path}")
    private String ghidraTmp;

    // save path
    @Value("${json.file.path}")
    private String jsonFilePath;

    // set pool size
    @Value("${core.pool.size}")
    private int CORE_POOL_SIZE;
    @Value("${core.pool.size}")
    private int MAX_POOL_SIZE;
    private static final int QUEUE_CAPACITY = 150;
    private static final Long KEEP_ALIVE_TIME = 1L;

    @Autowired
    ObjectFactory<ExtractService> extractServiceObjectFactory;

    private String rootPath = "../data/FedoraLib_Dataset";

    @Override
    public void run(ApplicationArguments args) throws Exception {
        logger.info("Client start......");
        long startTime = System.currentTimeMillis();

        extractPackage();

        long endTime = System.currentTimeMillis();
        logger.info("run time:" + (endTime - startTime) + "ms");
        System.exit(0);
    }

    public void extractPackage() {
        ThreadPoolExecutor cachedThreadPool = new ThreadPoolExecutor(CORE_POOL_SIZE, MAX_POOL_SIZE, KEEP_ALIVE_TIME,
                TimeUnit.SECONDS, new ArrayBlockingQueue<>(QUEUE_CAPACITY), new ThreadPoolExecutor.CallerRunsPolicy());

        File rootDir = new File(rootPath);

        for (File firstLevel : rootDir.listFiles()) {
            if (!firstLevel.isDirectory()) {
                continue;
            }
            String[] firstLevelStrings = firstLevel.toString().split("/", -1);
            String firstLevelId = firstLevelStrings[firstLevelStrings.length - 1];
            for (File secondLevel : firstLevel.listFiles()) {
                if (!secondLevel.isDirectory()) {
                    continue;
                }
                String[] secondLevelStrings = secondLevel.toString().split("/", -1);
                String secondLevelId = secondLevelStrings[secondLevelStrings.length - 1];
                for (File packageDir : secondLevel.listFiles()) {
                    if (!packageDir.isDirectory()) {
                        continue;
                    }
                    String[] packageStrings = packageDir.toString().split("/", -1);
                    String packageId = packageStrings[packageStrings.length - 1];
                    String jsonFileName = packageId+ ".json";
                    String savePath = jsonFilePath + "/" + firstLevelId + "/" + secondLevelId + "/" + packageId;
                    File targetJsonFile = new File(savePath, jsonFileName);
                    if (targetJsonFile.exists()) {
                        logger.info("package has been processed:  " + packageId);
                        continue;
                    }
                    logger.info("package to be processed:  " + packageId);
                    process(packageDir.toString(), savePath, ghidraTmp, Integer.parseInt(packageId));
                    // CountDownLatch threadSignal = new CountDownLatch(1);
                    // cachedThreadPool.submit(new Runnable() {
                    //     @Override
                    //     public void run() {
                    //         try {
                    //             if (!packageDir.exists()) {
                    //                 System.out.println("no exist");
                    //             }
                                
                    //             process(packageDir.toString(), savePath, ghidraTmp, Integer.parseInt(packageId));
                                
                    //         } catch (Exception e) {
                    //             logger.info("error: " + e + packageDir.toString());
                    //         } finally {
                    //             threadSignal.countDown();
                    //         }
                    //     }
                    // });
                }
            }
        }

        // cachedThreadPool.shutdown();
        // try {
        //     cachedThreadPool.awaitTermination(Long.MAX_VALUE, TimeUnit.MINUTES);
        // } catch (InterruptedException e) {
        //     e.printStackTrace();
        // }
    }
    
    public void process(String packageDir, String savePath, String ghidraTmp, int packageId) {
        long startTime = System.currentTimeMillis();
        try {
            ExtractService extractService = extractServiceObjectFactory.getObject();
            extractService.init(packageDir.toString(), savePath, ghidraTmp, packageId);
            extractService.executable();
            logger.info(Thread.currentThread().getName() + " extracted:" + packageDir.toString());
        } catch (Exception e) {
            logger.info("exception in processing:" + e);
        }
        logger.info("run time:" + (System.currentTimeMillis() - startTime) / 1000 + "s");
    }
}

package thusca.bcat.client.utils;

import org.apache.log4j.Logger;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Map;
import java.util.UUID;

import com.alibaba.fastjson.JSON;

public class FileUtil {

    private static Logger logger = Logger.getLogger(FileUtil.class);

    /**
     * 获取文件夹下所有的文件路径
     *
     * @param dir_path
     * @return
     */
    public static ArrayList<String> getAllDir(String dir_path) {
        ArrayList<String> all_dir = new ArrayList<String>();
        File file = new File(dir_path);
        if (file.exists()) {
            for (File tempfile : file.listFiles()) {
                if (tempfile.isDirectory()) {
                    all_dir.add(tempfile.getAbsolutePath());
                }
            }
        }
        return all_dir;
    }

    /**
     * 获取所有文件路径
     *
     * @param path
     * @return
     */
    public static ArrayList<String> getAllPath(String path) {
        ArrayList<String> paths = new ArrayList<String>();
        File fpath = new File(path);
        getAllPath(fpath, paths);
        return paths;
    }

    /**
     * 递归获取一个目录下的所有文件
     *
     * @param path
     * @param paths
     */
    public static void getAllPath(File path, ArrayList<String> paths) {
        File fs[] = path.listFiles();
        if (fs != null) {
            for (int i = 0; i < fs.length; i++) {
                if (fs[i].isDirectory()) {
                    getAllPath(fs[i], paths);
                }
                if (fs[i].isFile()) {
                    paths.add(fs[i].toString());
                }
            }
        }
    }

    /**
     * 将内容写入指定路径
     *
     * @param filepath
     * @param content
     */
    public static void saveStringToFile(String filepath, String content, Boolean append) {
        FileWriter fw = null;
        PrintWriter out = null;

        try {
            File file = new File(filepath);
            if (!file.exists()) {
                File fileParent = file.getParentFile();
                if (!fileParent.exists()) {
                    fileParent.mkdirs();
                }
            }
            file.createNewFile();
            fw = new FileWriter(file, append);
            out = new PrintWriter(fw);
            out.write(content);
            out.println();
        } catch (Exception ex) {
            logger.error("save string error: " + filepath, ex);
        } finally {
            try {
                if (out != null) {
                    out.close();
                }
                if (fw != null) {
                    fw.close();
                }
            } catch (Exception ex) {
                logger.error("resource close error: ", ex);
            }

        }
    }

    public static void saveJsonToFile(String filepath, Map content) {
        String json = JSON.toJSONString(content);
        saveStringToFile(filepath, json, false);
    }

    public static String readFileToString(String filePath) throws IOException {
        String fileString = Files.readString(Paths.get(filePath));
        return fileString;
    }

    public static File createTempFile(String parentFolder) throws IOException {
        String zipfileStr = UUID.randomUUID().toString().replace("-", "");
        zipfileStr += UUID.randomUUID().toString().replace("-", "");
        String folder = parentFolder;
        File file = new File(folder + File.separator + zipfileStr);
        file.mkdir();
        return file;
    }

    public static String getPathUnderIndexedFile(String rootDir, int packageId) {
        String packageIdString = ""+packageId;
        int idLength = packageIdString.length();
        String firstLevel = packageIdString.substring(idLength - 2);
        String secondLevel = packageIdString.substring(idLength - 4, idLength - 2);
        Path path;
        path = Paths.get(rootDir, firstLevel, secondLevel, packageIdString);
        return path.toString();
    }
}

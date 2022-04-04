package thusca.bcat.client.utils;

import lombok.Data;

@Data
public class StatusMsg {

    boolean isOK;
    String errMsg;
    String filePath;


    public StatusMsg(String msg, String path) {
        isOK = true;
        errMsg = msg;
        filePath = path;
    }

    public StatusMsg(boolean isOK, String msg, String path) {
        this.isOK = isOK;
        errMsg = msg;
        filePath = path;
    }

    public StatusMsg() {
        isOK = true;
    }

    public void setOKMsg(String msg, String path) {
        isOK = true;
        errMsg = msg;
        filePath = path;
    }

    public void setErrorMsg(String msg, String path) {
        isOK = false;
        errMsg = msg;
        filePath = path;
    }

    public String getMsg() {
        return filePath + " :  " + errMsg;
    }

    public boolean isOK() {
        return isOK;
    }
}

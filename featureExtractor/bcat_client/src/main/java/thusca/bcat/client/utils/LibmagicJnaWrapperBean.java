package thusca.bcat.client.utils;

import org.springframework.beans.factory.InitializingBean;
import org.springframework.stereotype.Component;

@Component
public class LibmagicJnaWrapperBean implements InitializingBean {

    private LibmagicJnaWrapper libmagicJnaWrapper;

    /* User bean 初始化操作 */
    @Override
    public void afterPropertiesSet() throws Exception {
        libmagicJnaWrapper  = new LibmagicJnaWrapper(
            LibmagicJnaWrapper.MAGIC_NO_CHECK_ENCODING | LibmagicJnaWrapper.MAGIC_NO_CHECK_APPTYPE
                    | LibmagicJnaWrapper.MAGIC_NO_CHECK_TOKENS);

        libmagicJnaWrapper.loadCompiledMagic();
    }

    public String getMimeType(String filePath) {
        return libmagicJnaWrapper.getMimeType(filePath);
    }

}

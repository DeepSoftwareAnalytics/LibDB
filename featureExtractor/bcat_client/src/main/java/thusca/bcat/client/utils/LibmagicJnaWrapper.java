/**
 * 
 */
package thusca.bcat.client.utils;

import java.io.IOException;
import java.io.InputStream;
import java.nio.Buffer;
import java.nio.ByteBuffer;

import com.sun.jna.Library;
import com.sun.jna.Native;
import com.sun.jna.NativeLong;
import com.sun.jna.Platform;
import com.sun.jna.Pointer;

/**
 * A wrapper for the libmagic library that relies on JNA. This is shamelessly
 * borrowed from the JHOVE2 code base, with reliance on JHOVE exceptions and
 * configuration removed so that it is easily called from other Maven projects.
 * 
 * The original file can be found here https://bitbucket.org/jhove2/main/src/96b706cbc3e1bd727239d4bfd378690545b37264/src/main/java/org/jhove2/module/identify/file/LibmagicJnaWrapper.java?at=default
 * 
 * @author hbian
 * @author carl@openplanetsfoundation.org
 */


public class LibmagicJnaWrapper {
    /** The default path for the magic file, taken from an Ubuntu installation */
    //TODO: put magic.mgc and libmagic.so libmagic.dylib under resources.
    public static final String DEFAULT_MAGIC_PATH = (Platform.isLinux())? "/usr/share/misc/magic.mgc" : "/usr/local/Cellar/libmagic/5.39/share/misc/magic.mgc";
    /** The default buffer size, the number of bytes to pass to file */
    public static final int DEFAULT_BUFFER_SIZE = 8192;


    /**
     * Load the source library and
     */
    public interface LibmagicDll extends Library {
        //TODO: the library name is "libmagic.so.1". However the name generated here is "libmagic.so" 

//        String LIBRARY_NAME = (Platform.isWindows()) ? "magic1" : "magic";
        String LIBRARY_NAME = (Platform.isLinux()) ? "/usr/lib/x86_64-linux-gnu/libmagic.so.1" : "/usr/local/lib/libmagic.dylib";

        LibmagicDll BASE = (LibmagicDll) Native.loadLibrary(LIBRARY_NAME, LibmagicDll.class);

        //LibmagicDll BASE = (LibmagicDll) Native.loadLibrary(LIBRARY_NAME, LibmagicDll.class);
//        LibmagicDll BASE = (LibmagicDll) Native.loadLibrary("/usr/lib/x86_64-linux-gnu/libmagic.so.1", LibmagicDll.class);

        LibmagicDll INSTANCE = (LibmagicDll) Native.synchronizedLibrary(BASE);

        Pointer magic_open(int flags);

        void magic_close(Pointer cookie);

        int magic_setflags(Pointer cookie, int flags);

        String magic_file(Pointer cookie, String fileName);

        String magic_buffer(Pointer cookie, Buffer buffer, NativeLong length);

        int magic_compile(Pointer cookie, String magicFileName);

        int magic_check(Pointer cookie, String magicFileName);

        int magic_load(Pointer cookie, String magicFileName);

        int magic_errno(Pointer cookie);

        String magic_error(Pointer cookie);
    }

    /** Libmagic flag: No flags. */
    public final static int MAGIC_NONE = 0x000000;
    /** Libmagic flag: Turn on debugging. */
    public final static int MAGIC_DEBUG = 0x000001;
    /** Libmagic flag: Follow symlinks. */
    public final static int MAGIC_SYMLINK = 0x000002;
    /** Libmagic flag: Check inside compressed files. */
    public final static int MAGIC_COMPRESS = 0x000004;
    /** Libmagic flag: Look at the contents of devices. */
    public final static int MAGIC_DEVICES = 0x000008;
    /** Libmagic flag: Return the MIME type. */
    public final static int MAGIC_MIME_TYPE = 0x000010;
    /** Libmagic flag: Return all matches. */
    public final static int MAGIC_CONTINUE = 0x000020;
    /** Libmagic flag: Print warnings to stderr. */
    public final static int MAGIC_CHECK = 0x000040;
    /** Libmagic flag: Restore access time on exit. */
    public final static int MAGIC_PRESERVE_ATIME = 0x000080;
    /** Libmagic flag: Don't translate unprintable chars. */
    public final static int MAGIC_RAW = 0x000100;
    /** Libmagic flag: Handle ENOENT etc as real errors. */
    public final static int MAGIC_ERROR = 0x000200;
    /** Libmagic flag: Return the MIME encoding. */
    public final static int MAGIC_MIME_ENCODING = 0x000400;
    /** Libmagic flag: Return both MIME type and encoding. */
    public final static int MAGIC_MIME = (MAGIC_MIME_TYPE | MAGIC_MIME_ENCODING);
    /** Libmagic flag: Return the Apple creator and type. */
    public final static int MAGIC_APPLE = 0x000800;
    /** Libmagic flag: Don't check for compressed files. */
    public final static int MAGIC_NO_CHECK_COMPRESS = 0x001000;
    /** Libmagic flag: Don't check for tar files. */
    public final static int MAGIC_NO_CHECK_TAR = 0x002000;
    /** Libmagic flag: Don't check magic entries. */
    public final static int MAGIC_NO_CHECK_SOFT = 0x004000;
    /** Libmagic flag: Don't check application type. */
    public final static int MAGIC_NO_CHECK_APPTYPE = 0x008000;
    /** Libmagic flag: Don't check for elf details. */
    public final static int MAGIC_NO_CHECK_ELF = 0x010000;
    /** Libmagic flag: Don't check for text files. */
    public final static int MAGIC_NO_CHECK_TEXT = 0x020000;
    /** Libmagic flag: Don't check for cdf files. */
    public final static int MAGIC_NO_CHECK_CDF = 0x040000;
    /** Libmagic flag: Don't check tokens. */
    public final static int MAGIC_NO_CHECK_TOKENS = 0x100000;
    /** Libmagic flag: Don't check text encodings. */
    public final static int MAGIC_NO_CHECK_ENCODING = 0x200000;

    /** Magic cookie pointer. */
    private final Pointer cookie;

    /**
     * Creates a new instance returning the default information: MIME type and
     * character encoding.
     * 
     * @throws
     *             if any error occurred while initializing the libmagic.
     * 
     * @see #LibmagicJnaWrapper(int)
     * @see #MAGIC_MIME
     */
    public LibmagicJnaWrapper() {
        this(MAGIC_MIME | MAGIC_SYMLINK);
    }

    /**
     * Creates a new instance returning the information specified in the
     * <code>flag</code> argument
     * 
     */
    public LibmagicJnaWrapper(int flag) {
        this.cookie = LibmagicDll.INSTANCE.magic_open(flag);
        if (this.cookie == null) {
            throw new IllegalStateException("Libmagic initialization failed");
        }
    }

    /**
     * Closes the magic database and deallocates any resources used.
     */
    public void close() {
        LibmagicDll.INSTANCE.magic_close(cookie);
    }

    /**
     * Returns a textual explanation of the last error.
     * 
     * @return the textual description of the last error, or <code>null</code>
     *         if there was no error.
     */
    public String getError() {
        return LibmagicDll.INSTANCE.magic_error(cookie);
    }

    /**
     * Returns the textual description of the contents of the specified file.
     * 
     * @param filePath
     *            the path of the file to be identified.
     * 
     * @return the textual description of the file, or <code>null</code> if an
     *         error occurred.
     */
    public String getMimeType(String filePath) {
        if ((filePath == null) || (filePath.length() == 0)) {
            throw new IllegalArgumentException("filePath");
        }
        return LibmagicDll.INSTANCE.magic_file(cookie, filePath);
    }

    /**
     * Returns textual description of the contents of the <code>buffer</code>
     * argument.
     * 
     * @param buffer
     *            the data to analyze.
     * @param length
     *            the length, in bytes, of the buffer.
     * 
     * @return the textual description of the buffer data, or <code>null</code>
     *         if an error occurred.
     */
    public String getMimeType(Buffer buffer, long length) {
        return LibmagicDll.INSTANCE.magic_buffer(cookie, buffer,
                new NativeLong(length));
    }

    /**
     * Identify the MIME type of an input stream, using the default buffer size
     * {@link #DEFAULT_BUFFER_SIZE}.
     * 
     * @param stream
     *            a java.io.InputStream to be identified
     * @return the textual description of the buffer data, or <code>null</code>
     *         if an error occurred.
     * @throws IOException
     *             if there is a problem identifying a stream
     */
    public String getMimeType(InputStream stream) throws IOException {
        return this.getMimeType(stream, DEFAULT_BUFFER_SIZE);
    }

    /**
     * Identify the MIME type of an input stream, using the passed buffer size.
     * 
     * @param stream
     *            a java.io.InputStream to be identified
     * @param bufferSize
     *            effectively the number of bytes to pass to file, or the length
     *            of the file if shorter
     * @return the textual description of the buffer data, or <code>null</code>
     *         if an error occurred.
     * @throws IOException
     *             if there is a problem identifying a stream
     */
    public String getMimeType(InputStream stream, int bufferSize)
            throws IOException {
        // create buffer with capacity of bufferSize
        byte[] buffer = new byte[bufferSize];
        int len = stream.read(buffer);
        ByteBuffer byteBuf = ByteBuffer.wrap(buffer);
        return this.getMimeType(byteBuf, len);
    }

    /**
     * Compiles the colon-separated list of database text files passed in as
     * <code>magicFiles</code>.
     * 
     * @param magicFiles
     *            the magic database file(s), or <code>null</code> to use the
     *            default database.
     * @return 0 on success and -1 on failure.
     */
    public int compile(String magicFiles) {
        return LibmagicDll.INSTANCE.magic_compile(cookie, magicFiles);
    }

    /**
     * Loads the colon-separated list of database files passed in as
     * <code>magicFiles</code>. This method must be used before any magic
     * queries be performed.
     * 
     * @param magicFiles
     *            the magic database file(s), or <code>null</code> to use the
     *            default database.
     * @return 0 on success and -1 on failure.
     */
    public int load(String magicFiles) {
        return LibmagicDll.INSTANCE.magic_load(cookie, magicFiles);
    }

    /**
     * Loads the magic file located at the path held in
     * {@link #DEFAULT_MAGIC_PATH}
     * 
     * @return 0 on success and -1 on failure.
     */
    public int loadCompiledMagic() {
        return this.load(DEFAULT_MAGIC_PATH);
    }
}
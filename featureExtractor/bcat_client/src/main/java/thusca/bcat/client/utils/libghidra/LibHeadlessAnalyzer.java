/* ###
 * IP: GHIDRA
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/*
  Modified version of the Headless analyzer code, for any feedback, contact NADER SHALLABI at nader@nosecurecode.com
*/

package thusca.bcat.client.utils.libghidra;

import java.io.*;
import java.net.*;
import java.util.*;
import java.util.regex.Pattern;

import generic.jar.ResourceFile;
import generic.stl.Pair;
import generic.util.Path;
import ghidra.GhidraApplicationLayout;
import ghidra.GhidraJarApplicationLayout;
import ghidra.app.plugin.core.analysis.AutoAnalysisManager;
import ghidra.app.script.*;
import ghidra.app.util.importer.AutoImporter;
import ghidra.app.util.importer.MessageLog;
import ghidra.app.util.opinion.BinaryLoader;
import ghidra.framework.*;
import ghidra.framework.client.ClientUtil;
import ghidra.framework.client.RepositoryAdapter;
import ghidra.framework.data.*;
import ghidra.framework.model.*;
import ghidra.framework.project.DefaultProject;
import ghidra.framework.project.DefaultProjectManager;
import ghidra.framework.protocol.ghidra.*;
import ghidra.framework.remote.User;
import ghidra.framework.store.LockException;
import ghidra.framework.store.local.LocalFileSystem;
import ghidra.program.database.ProgramContentHandler;
import ghidra.program.database.ProgramDB;
import ghidra.program.model.address.AddressSetView;
import ghidra.program.model.listing.Program;
import ghidra.program.util.GhidraProgramUtilities;
import ghidra.program.util.ProgramLocation;
import ghidra.util.*;
import ghidra.util.exception.*;
import ghidra.util.task.TaskMonitor;
import thusca.bcat.client.utils.StatusMsg;
import utilities.util.FileUtilities;
import ghidra.framework.options.Options;

public class LibHeadlessAnalyzer {

    private static Object LOCK = new Object();
    private static ThreadLocal<LibHeadlessAnalyzer> instanceThreadLocal = new ThreadLocal<>();
    private LibHeadlessOptions options;
    private HeadlessGhidraProjectManager projectManager;
    private Project project;
    private boolean analysisTimedOut;
    private DomainFolder saveDomainFolder;
    private Map<String, Object> storage;
    private URLClassLoader classLoaderForDotClassScripts;

    private LibProgramHandler programHandler = null;

    public StatusMsg STATUS_MSG = new StatusMsg();

    public static LibHeadlessAnalyzer getLoggableInstance(File logFile, File scriptLogFile, boolean useLog4j,
                                                          LibProgramHandler handler) throws IllegalStateException, IOException {

        // Prevent more than one headless analyzer from being instantiated. Too much
        // about it
        // messes with global system settings, so under the current design of Ghidra,
        // allowing
        // more than one to exist could result in unpredictable behavior.
        if (instanceThreadLocal.get() != null) {
            // throw new IllegalStateException(
            // "A headless analzyer instance has already been retrieved. " +
            // "Use HeadlessAnalyzer.getInstance() to get it.");
            instanceThreadLocal.get().programHandler = handler;
            return instanceThreadLocal.get();
        }

        // Cannot set logging because application has already been initialized.
        synchronized (LOCK) {
            if (!Application.isInitialized()) {
                // Initialize application with the provided logging parameters
                ApplicationConfiguration configuration = new HeadlessGhidraApplicationConfiguration();
                if (useLog4j) {
                    if (logFile != null) {
                        configuration.setApplicationLogFile(logFile);
                    }
                    if (scriptLogFile != null) {
                        configuration.setScriptLogFile(scriptLogFile);
                    }
                } else {
                    configuration.setInitializeLogging(false);
                    Msg.setErrorLogger(new LibHeadlessErrorLogger(logFile));
                }
                Application.initializeApplication(getApplicationLayout(), configuration);
            }
        }

        // Instantiate and return singleton headless analyzer

        instanceThreadLocal.set(new LibHeadlessAnalyzer());

        // Set our program handler
        instanceThreadLocal.get().programHandler = handler;
        return instanceThreadLocal.get();
    }

    /**
     * Gets a headless analyzer instance, with the assumption that the application
     * has already been initialized. If this is called before the application has
     * been initialized, it will initialize the application with no logging.
     *
     * @return An instance of a new headless analyzer.
     * @throws IOException if there was a problem reading the application.properties
     *                     file (only possible if the application had not be
     *                     initialized).
     */
    public static LibHeadlessAnalyzer getInstance(LibProgramHandler handler) throws IOException {

        // Prevent more than one headless analyzer from being instantiated. Too much
        // about it
        // messes with global system settings, so under the current design of Ghidra,
        // allowing
        // more than one to exist could result in unpredictable behavior.

        if (instanceThreadLocal.get() != null) {
            instanceThreadLocal.get().programHandler = handler;
            return instanceThreadLocal.get();
        }

        // Initialize application (if necessary)
        synchronized (LOCK) {
            if (!Application.isInitialized()) {
                ApplicationConfiguration configuration = new HeadlessGhidraApplicationConfiguration();
                configuration.setInitializeLogging(false);
                Msg.setErrorLogger(new LibHeadlessErrorLogger(null));
                Application.initializeApplication(getApplicationLayout(), configuration);
            }
        }

        // Instantiate and return singleton headless analyzer
        instanceThreadLocal.set(new LibHeadlessAnalyzer());
        // Set our program handler
        instanceThreadLocal.get().programHandler = handler;
        return instanceThreadLocal.get();
    }

    /**
     * Gets the appropriate Ghidra application layout for this headless analyzer.
     * <p>
     * The headless analyzer can be used in both "normal" mode and single jar mode,
     * so we need to use the appropriate layout for either case.
     *
     * @return The appropriate Ghidra application layout for this headless analyzer.
     * @throws IOException if there was a problem getting an appropriate application
     *                     layout.
     */
    private static GhidraApplicationLayout getApplicationLayout() throws IOException {
        GhidraApplicationLayout layout;
        try {
            layout = new GhidraApplicationLayout();
        } catch (IOException e) {
            layout = new GhidraJarApplicationLayout();
        }
        return layout;
    }

    /**
     * Creates a new headless analyzer object with default settings.
     */
    private LibHeadlessAnalyzer() {
        // Create default options which the caller can later set prior to processing.
        options = new LibHeadlessOptions();

        // Ghidra URL handler registration. There's no harm in doing this more than
        // once.
        Handler.registerHandler();

        // Ensure that we are running in "headless mode", preventing Swing-based methods
        // from
        // running (causing headless operation to lose focus).
        System.setProperty("java.awt.headless", "true");
        System.setProperty(SystemUtilities.HEADLESS_PROPERTY, Boolean.TRUE.toString());

        // Allows handling of old content which did not have a content type property
        DomainObjectAdapter.setDefaultContentClass(ProgramDB.class);

        // Put analyzer in its default state
        reset();
    }

    /**
     * Resets the state of the headless analyzer to the default settings.
     */
    public void reset() {
        options.reset();
        project = null;
        analysisTimedOut = false;
        saveDomainFolder = null;
        storage = new HashMap<>();
        classLoaderForDotClassScripts = null;
    }

    /**
     * Gets the headless analyzer's options.
     *
     * @return The headless analyer's options.
     */
    public LibHeadlessOptions getOptions() {
        return options;
    }

    /**
     * Process the optional import file/directory list and process each imported
     * file:
     * <ol>
     * <li>execute ordered list of pre-scripts</li>
     * <li>perform auto-analysis if not disabled</li>
     * <li>execute ordered list of post-scripts</li>
     * </ol>
     * If no import files or directories have been specified the ordered list of
     * pre/post scripts will be executed once.
     *
     * @param projectLocation directory path of project If project exists it will be
     *                        opened, otherwise it will be created.
     * @param projectName     project name
     * @param rootFolderPath  root folder for imports
     * @param filesToImport   directories and files to be imported (null or empty is
     *                        acceptable if we are in -process mode)
     * @throws IOException if there was an IO-related problem
     */
    public StatusMsg processLocal(String projectLocation, String projectName, String rootFolderPath,
                                  List<File> filesToImport, List<String> falseAnalyzers) throws IOException {

        if (options.readOnly && options.commit) {
            Msg.error(this, "Abort due to Headless analyzer error: The requested readOnly option is "
                    + "in conflict with the commit option");
            return STATUS_MSG;
        }

        // If not importing, remove trailing slash so that non-existent folders aren't
        // created
        if (options.runScriptsNoImport) {
            if ((rootFolderPath.endsWith("/")) && (rootFolderPath.length() > 1)) {
                rootFolderPath = rootFolderPath.substring(0, rootFolderPath.length() - 1);
            }
        } else {
            // If we are importing, need some files to import or at least a script to run!
            if ((filesToImport == null || filesToImport.size() == 0) && options.preScripts.isEmpty()
                    && options.postScripts.isEmpty()) {
                Msg.warn(this, "REPORT: Nothing to do ... must specify file(s) for import.");
                return new StatusMsg();
            }

            // If importing, add trailing slash if it isn't there so that non-existent
            // folders are created
            if (!rootFolderPath.endsWith("/")) {
                rootFolderPath += "/";
            }
        }

        initializeScriptPaths();
        compileScripts();

        Msg.info(LibHeadlessAnalyzer.class, "HEADLESS: execution starts");

        File dir = new File(projectLocation);
        ProjectLocator locator = new ProjectLocator(dir.getAbsolutePath(), projectName);

        if (locator.getProjectDir().exists()) {
            project = openProject(locator);
        } else {
            if (options.runScriptsNoImport) {
                Msg.error(this, "Could not find project: " + locator + " -- should already exist in -process mode.");
                throw new IOException("Could not find project: " + locator);
            }

            if (!options.runScriptsNoImport && options.readOnly) {
                // assume temporary when importing with readOnly option
                options.deleteProject = true;
            }

            Msg.info(this, "Creating " + (options.deleteProject ? "temporary " : "") + "project: " + locator);
            project = getProjectManager().createProject(locator, null, false);
        }

        try {

            if (!checkUpdateOptions()) {
                return new StatusMsg(); // TODO: Should an exception be thrown?
            }

            if (options.runScriptsNoImport) {
                processNoImport(rootFolderPath);
            } else {
                processWithImport(rootFolderPath, filesToImport, falseAnalyzers);
            }
        } finally {
            project.close();
            if (!options.runScriptsNoImport && options.deleteProject) {
                FileUtilities.deleteDir(locator.getProjectDir());
                locator.getMarkerFile().delete();
            }
        }
        return STATUS_MSG;
    }

    /**
     * Checks to see if the most recent analysis timed out.
     *
     * @return true if the most recent analysis timed out; otherwise, false.
     */
    public boolean checkAnalysisTimedOut() {
        return analysisTimedOut;
    }

    void setSaveFolder(DomainFolder domFolder) {
        saveDomainFolder = domFolder;

        if (domFolder != null) {
            Msg.info(this, "Save location changed to: " + domFolder.getPathname());
        }
    }

    void addVariableToStorage(String nameOfVar, Object valOfVar) {
        if (storage.containsKey(nameOfVar)) {
            Msg.warn(this, "Overwriting existing storage variable: " + nameOfVar);
        }

        storage.put(nameOfVar, valOfVar);
    }

    Set<String> getStorageKeys() {
        return storage.keySet();
    }

    Object getVariableFromStorage(String nameOfVar) {
        if (!storage.containsKey(nameOfVar)) {
            Msg.warn(this, "The storage variable '" + nameOfVar + "' does not exist in HeadlessAnalyzer storage.");
            return null;
        }

        return storage.get(nameOfVar);
    }

    /**
     * Get/Create specified folder path within project
     *
     * @param folderPath the folder path within the project
     * @param create     if true, folder will be created if it does not exist
     * @return DomainFolder for specified path
     * @throws InvalidNameException if folder name is invalid
     * @throws IOException          if folder can not be created
     */
    DomainFolder getDomainFolder(String folderPath, boolean create) throws IOException, InvalidNameException {

        DomainFolder domFolder = project.getProjectData().getFolder(folderPath);

        if (create && domFolder == null) {
            // Create any folder that doesn't exist
            String cleanPath = folderPath.replaceAll("^" + DomainFolder.SEPARATOR + "+", "");
            cleanPath = cleanPath.replaceAll(DomainFolder.SEPARATOR + "+$", "");

            String[] subfolders = cleanPath.split(DomainFolder.SEPARATOR + "+");

            int folderIndex = 0;
            String currPath = DomainFolder.SEPARATOR + subfolders[folderIndex];

            DomainFolder testFolder = project.getProjectData().getFolder(currPath);
            DomainFolder baseFolder = null;

            // Stay in loop while we see folders that exist
            while ((testFolder != null) && (folderIndex < (subfolders.length - 1))) {
                folderIndex++;
                baseFolder = testFolder;
                testFolder = baseFolder.getFolder(subfolders[folderIndex]);
            }

            // If none of the folders exist, create new files starting from the root
            if (folderIndex == 0) {
                baseFolder = project.getProjectData().getRootFolder();
            }

            // Since this method is only called by import, we create any folder that
            // does not exist.
            for (int i = folderIndex; i < subfolders.length; i++) {
                baseFolder = baseFolder.createFolder(subfolders[i]);
                Msg.info(this, "Created project folder: " + subfolders[i]);
            }

            domFolder = baseFolder;
        }

        return domFolder;
    }

    boolean storageContainsKey(String nameOfVar) {
        return storage.containsKey(nameOfVar);
    }

    /**
     * Runs the specified script with the specified state.
     *
     * @param scriptState State representing environment variables that the script
     *                    is able to access.
     * @param script      Script to be run.
     * @return whether the script successfully completed running
     */
    private boolean runScript(GhidraState scriptState, GhidraScript script) {
        if (script instanceof LibHeadlessScript) {
            ((LibHeadlessScript) script).setHeadlessInstance(this);
        }

        ResourceFile srcFile = script.getSourceFile();
        String scriptName = srcFile != null ? srcFile.getAbsolutePath() : (script.getClass().getName() + ".class");

        try {
            PrintWriter writer = new PrintWriter(System.out);
            Msg.info(this, "SCRIPT: " + scriptName);
            script.execute(scriptState, TaskMonitor.DUMMY, writer);
            writer.flush();
        } catch (Exception exc) {
            Program prog = scriptState.getCurrentProgram();
            String path = (prog != null ? " ( " + prog.getExecutablePath() + " ) " : "");
            String logErrorMsg = "REPORT SCRIPT ERROR: " + path + " " + scriptName + " : " + exc.getMessage();
            Msg.error(this, logErrorMsg, exc);
            return false;
        }

        return true;
    }

    /**
     * Check file update options (i.e., readOnly, commit) and change defaults if
     * needed.
     *
     * @return true if OK to continue
     */
    private boolean checkUpdateOptions() {

        boolean isImport = !options.runScriptsNoImport;
        boolean commitAllowed = isCommitAllowed();

        if (options.readOnly) {
            String readOnlyError = "Abort due to Headless analyzer error: The requested -readOnly option "
                    + "is in conflict with the ";

            if (options.commit) {
                Msg.error(this, readOnlyError + "-commit option.");
                return false;
            }

            if (options.okToDelete) {
                Msg.error(this, readOnlyError + "-okToDelete option.");
                return false;
            }
        }

        if (options.commit && !commitAllowed) {
            Msg.error(this, "Commit to repository not possible (due to permission or connection issue)");
            return false;
        }

        if (project.getProjectLocator().isTransient()) {
            if (!options.commit) {
                if (commitAllowed && !options.readOnly) {
                    Msg.info(this, "When processing a URL, -commit is automatically enabled unless -readOnly mode "
                            + "is specified.  Enabling -commit and continuing.");
                    options.commit = true;
                }
            }
        }

        if (options.overwrite) {
            if (!isImport) {
                Msg.info(this, "Ignoring -overwrite because it is not applicable to -process mode.");
            } else if (options.readOnly) {
                Msg.info(this, "Ignoring -overwrite because it is not applicable to -readOnly import mode.");
                options.overwrite = false;
            }
        }

        return true;
    }

    private boolean isCommitAllowed() {
        RepositoryAdapter repository = project.getRepository();
        if (repository == null) {
            return true;
        }
        try {
            repository.connect();
            if (!repository.isConnected()) {
                return false;
            }
            User user = repository.getUser();
            if (!user.hasWritePermission()) {
                Msg.warn(this, "User '" + user.getName()
                        + "' does not have write permission to repository - commit not allowed");
                return false;
            }
            return true;
        } catch (IOException e) {
            Msg.error(this, "Repository connection failed (" + repository.getServerInfo() + ") - commit not allowed");
            return false;
        }
    }

    /**
     * Gather paths where scripts may be found.
     */
    private void initializeScriptPaths() {

        List<Path> paths;
        if (options.scriptPaths == null || options.scriptPaths.isEmpty()) {
            paths = GhidraScriptUtil.getDefaultScriptDirectories();
        } else {
            paths = new ArrayList<>();
            for (String path : options.scriptPaths) {
                paths.add(new Path(path, true, false, true));
            }
            for (Path path : GhidraScriptUtil.getDefaultScriptDirectories()) {
                if (path.isEnabled() && !paths.contains(path)) {
                    paths.add(path);
                }
            }
        }
        GhidraScriptUtil.setScriptDirectories(paths);

        StringBuffer buf = new StringBuffer("HEADLESS Script Paths:");
        for (ResourceFile dir : GhidraScriptUtil.getScriptSourceDirectories()) {
            buf.append("\n    ");
            buf.append(dir.getAbsolutePath());
        }
        Msg.info(LibHeadlessAnalyzer.class, buf.toString());
    }

    private ResourceFile findScript(String scriptName) {
        ResourceFile scriptSource = new ResourceFile(scriptName);
        scriptSource = scriptSource.getCanonicalFile();
        if (scriptSource.exists()) {
            return scriptSource;
        }
        List<ResourceFile> dirs = GhidraScriptUtil.getScriptSourceDirectories();
        for (ResourceFile dir : dirs) {
            scriptSource = new ResourceFile(dir, scriptName);
            if (scriptSource.exists()) {
                return scriptSource;
            }
        }
        throw new IllegalArgumentException("Script not found: " + scriptName);
    }

    /**
     * Checks the script name to ensure it exists. If the script type has a
     * GhidraScriptProvider (any type of script but .class), then return the
     * ResourceFile that represents that script.
     * <p>
     * If the script is a class file, return null (one class loader is stored to
     * allow the Headless Analyzer to find all the class files).
     * <p>
     * GhidraScript is not instantiated here, because it is important that each
     * script be instantiated at the time it's used. If a GhidraScript object is
     * re-used, this causes problems where GhidraScript variables aren't being
     * re-initialized at each use of the script.
     *
     * @param scriptName The name of the script to check
     * @return ResourceFile representing the source file, or null (if script is a
     * .class file)
     */
    private ResourceFile checkScript(String scriptName) {

        // Check for pre-compiled GhidraScript (e.g., my.package.Impl.class)
        String classExtension = ".class";

        if (scriptName.endsWith(classExtension)) {
            String className = scriptName.substring(0, scriptName.length() - classExtension.length());
            try {

                // Create a classloader that contains all the ghidra_script paths (especially
                // the one
                // specified in -scriptPath!)
                List<ResourceFile> dirs = GhidraScriptUtil.getScriptSourceDirectories();
                List<URL> urls = new ArrayList<>();

                for (ResourceFile dir : dirs) {
                    try {
                        urls.add(dir.toURL());
                    } catch (MalformedURLException e) {
                        // Do nothing. If can't make a URL out of the dir, don't add it.
                    }
                }

                classLoaderForDotClassScripts = URLClassLoader.newInstance(urls.toArray(new URL[0]));

                Class<?> c = Class.forName(className, true, classLoaderForDotClassScripts);

                if (GhidraScript.class.isAssignableFrom(c)) {
                    // No issues, but return null, which signifies we don't actually have a
                    // ResourceFile to associate with the script name
                    return null;
                }

                Msg.error(this, "REPORT SCRIPT ERROR: java class '" + className + "' is not a GhidraScript");
            } catch (ClassNotFoundException e) {
                Msg.error(this, "REPORT SCRIPT ERROR: java class not found for '" + className + "'");
            }
            throw new IllegalArgumentException("Invalid script: " + scriptName);
        }

        try {
            ResourceFile scriptSource = findScript(scriptName);
            GhidraScriptProvider provider = GhidraScriptUtil.getProvider(scriptSource);

            if (provider == null) {
                throw new IOException("Missing plugin needed to run scripts of this type. Please "
                        + "ensure you have installed the necessary plugin.");
            }

            return scriptSource;
        } catch (Exception | NoClassDefFoundError exc) {
            String logErrorMsg = "REPORT SCRIPT ERROR: " + scriptName + " : " + exc.getMessage();
            Msg.error(this, logErrorMsg);
        }
        throw new IllegalArgumentException("Invalid script: " + scriptName);
    }

    /**
     * Creates mapping from script name to actual Script object
     *
     * @param scriptsList List of scripts
     * @return mapping of script name to its associated Script object
     */
    private Map<String, ResourceFile> checkScriptsList(List<Pair<String, String[]>> scriptsList) {
        Map<String, ResourceFile> map = new HashMap<>();
        for (Pair<String, String[]> scriptPair : scriptsList) {
            String scriptName = scriptPair.first;
            ResourceFile scriptFile = checkScript(scriptName);
            map.put(scriptName, scriptFile);
        }
        return map;
    }

    private void compileScripts() throws IOException {

        // Check that given locations for .properties files are valid
        if (options.propertiesFileStrPaths.size() > 0) {

            options.propertiesFilePaths.clear();

            for (String path : options.propertiesFileStrPaths) {
                Path currPath = new Path(path, true, false, true);

                ResourceFile resource = currPath.getPath();

                if (!resource.isDirectory()) {
                    throw new IOException("Properties file path: '" + path + "' either does not exist, "
                            + "or is not a valid directory.");
                }

                if (currPath.isEnabled() && !options.propertiesFilePaths.contains(resource)) {
                    options.propertiesFilePaths.add(resource);
                }
            }
        }

        if (options.preScriptFileMap == null) {
            options.preScriptFileMap = checkScriptsList(options.preScripts);
        }

        if (options.postScriptFileMap == null) {
            options.postScriptFileMap = checkScriptsList(options.postScripts);
        }
    }

    /**
     * Run a list of scripts
     *
     * @param scriptsList    list of script names to run
     * @param scriptFileMap  mapping of script names to Script objects
     * @param scriptState    the GhidraState to be passed into each script
     * @param continueOption option that could have been set by script(s)
     * @return option that could have been set by script(s)
     */
    private LibHeadlessScript.HeadlessContinuationOption runScriptsList(List<Pair<String, String[]>> scriptsList,
                                                                        Map<String, ResourceFile> scriptFileMap, GhidraState scriptState,
                                                                        LibHeadlessScript.HeadlessContinuationOption continueOption) {

        ResourceFile currScriptFile;
        LibHeadlessScript.HeadlessContinuationOption retOption = continueOption;

        boolean scriptSuccess;
        boolean isHeadlessScript = false;
        String scriptName = "";
        GhidraScript currScript;

        try {
            for (Pair<String, String[]> scriptPair : scriptsList) {
                scriptName = scriptPair.first;
                String[] scriptArgs = scriptPair.second;

                // For .class files, there is no ResourceFile mapping. Need to load from the
                // stored 'classLoaderForDotClassScripts'
                if (scriptName.endsWith(".class")) {

                    if (classLoaderForDotClassScripts == null) {
                        throw new IllegalArgumentException("Invalid script: " + scriptName);
                    }

                    String className = scriptName.substring(0, scriptName.length() - 6);
                    Class<?> c = Class.forName(className, true, classLoaderForDotClassScripts);

                    // Get parent folder to pass to GhidraScript
                    File parentFile = new File(c.getResource(c.getSimpleName() + ".class").toURI()).getParentFile();

                    currScript = (GhidraScript) c.getConstructor().newInstance();
                    currScript.setScriptArgs(scriptArgs);

                    if (options.propertiesFilePaths.size() > 0) {
                        currScript.setPotentialPropertiesFileLocations(options.propertiesFilePaths);
                    }

                    currScript.setPropertiesFileLocation(parentFile.getAbsolutePath(), className);
                } else {
                    currScriptFile = scriptFileMap.get(scriptName);

                    // GhidraScriptProvider case
                    GhidraScriptProvider provider = GhidraScriptUtil.getProvider(currScriptFile);
                    PrintWriter writer = new PrintWriter(System.out);
                    currScript = provider.getScriptInstance(currScriptFile, writer);
                    currScript.setScriptArgs(scriptArgs);

                    if (options.propertiesFilePaths.size() > 0) {
                        currScript.setPotentialPropertiesFileLocations(options.propertiesFilePaths);
                    }
                }

                isHeadlessScript = currScript instanceof LibHeadlessScript ? true : false;

                if (isHeadlessScript) {
                    ((LibHeadlessScript) currScript).setInitialContinuationOption(retOption);
                }

                scriptSuccess = runScript(scriptState, currScript);

                if (isHeadlessScript) {
                    if (scriptSuccess) {
                        retOption = ((LibHeadlessScript) currScript).getContinuationOption();

                        // If script wants to abort, return without running any scripts that follow
                        if ((retOption == LibHeadlessScript.HeadlessContinuationOption.ABORT)
                                || (retOption == LibHeadlessScript.HeadlessContinuationOption.ABORT_AND_DELETE)) {
                            return retOption;
                        }

                    } else {
                        // If script did not run successfully, abort further processing automatically
                        Msg.warn(this, "Script does not exist or encountered problems; further processing is aborted.");

                        return LibHeadlessScript.HeadlessContinuationOption.ABORT;
                    }
                }
            }
        } catch (Exception exc) {
            String logErrorMsg = "REPORT SCRIPT ERROR: " + scriptName + " : " + exc.getMessage();
            Msg.error(this, logErrorMsg, exc);
        }

        return retOption;
    }

    private GhidraState getInitialProgramState(Program program) {
        ProgramLocation location = null;
        AddressSetView initializedMem = program.getMemory().getLoadedAndInitializedAddressSet();
        if (!initializedMem.isEmpty()) {
            location = new ProgramLocation(program, initializedMem.getMinAddress());
        }
        return new GhidraState(null, project, program, location, null, null);
    }

    /**
     * {@literal Run prescripts -> analysis -> postscripts (any of these steps is optional).}
     *
     * @param fileAbsolutePath Path of the file to analyze.
     * @param program          The program to analyze.
     * @return true if the program file should be kept. If analysis or scripts have
     * marked the program as temporary changes should not be saved. Returns
     * false in these cases: - One of the scripts sets the Headless
     * Continuation Option to "ABORT_AND_DELETE" or "CONTINUE_THEN_DELETE".
     */
    private boolean analyzeProgram(String fileAbsolutePath, Program program) {

        analysisTimedOut = false;

        AutoAnalysisManager mgr = AutoAnalysisManager.getAnalysisManager(program);
        mgr.initializeOptions();

        GhidraState scriptState = null;
        LibHeadlessScript.HeadlessContinuationOption scriptStatus = LibHeadlessScript.HeadlessContinuationOption.CONTINUE;

        boolean abortProcessing = false;
        boolean deleteProgram = false;

        if (!options.preScripts.isEmpty()) {
            // create one state, in case each script might want to modify it to pass
            // information
            scriptState = getInitialProgramState(program);

            scriptStatus = runScriptsList(options.preScripts, options.preScriptFileMap, scriptState, scriptStatus);
        }

        switch (scriptStatus) {
            case ABORT_AND_DELETE:
                abortProcessing = true;
                deleteProgram = true;
                break;

            case CONTINUE_THEN_DELETE:
                abortProcessing = false;
                deleteProgram = true;
                break;

            case ABORT:
                abortProcessing = true;
                deleteProgram = false;
                break;

            default:
                // do nothing
        }

        if (abortProcessing) {
            Msg.info(this, "Processing aborted as a result of pre-script.");
            return !deleteProgram;
        }

        int txId = program.startTransaction("Analysis");
        try {
            if (options.analyze) {
                Msg.info(this, "ANALYZING all memory and code: " + fileAbsolutePath);
                mgr.initializeOptions();

                // Note: Want to analyze regardless of whether we have already analyzed or not
                // (user could have changed options).
                mgr.reAnalyzeAll(null);

                if (options.perFileTimeout == -1) {
                    mgr.startAnalysis(TaskMonitor.DUMMY); // kick start

                    Msg.info(this, "REPORT: Analysis succeeded for file: " + fileAbsolutePath);
                    GhidraProgramUtilities.setAnalyzedFlag(program, true);
                } else {
                    LibHeadlessTimedTaskMonitor timerMonitor = new LibHeadlessTimedTaskMonitor(options.perFileTimeout);
                    mgr.startAnalysis(timerMonitor);

                    if (timerMonitor.isCancelled()) {
                        Msg.error(this, "REPORT: Analysis timed out at " + options.perFileTimeout
                                + " seconds. Processing not completed for file: " + fileAbsolutePath);

                        // If no further scripts, just return the current program disposition
                        if (options.postScripts.isEmpty()) {
                            return !deleteProgram;
                        }

                        analysisTimedOut = true;
                    } else {
                        // If timeout didn't already happen at this point, cancel the monitor
                        timerMonitor.cancel();

                        Msg.info(this, "REPORT: Analysis succeeded for file: " + fileAbsolutePath);
                        GhidraProgramUtilities.setAnalyzedFlag(program, true);
                    }
                }
            }
        } finally {
            program.endTransaction(txId, true);
        }

        if (!options.postScripts.isEmpty()) {

            if (scriptState == null) {
                scriptState = getInitialProgramState(program);
            }

            scriptStatus = runScriptsList(options.postScripts, options.postScriptFileMap, scriptState, scriptStatus);

            switch (scriptStatus) {
                case ABORT_AND_DELETE:
                    abortProcessing = true;
                    deleteProgram = true;
                    break;

                case CONTINUE_THEN_DELETE:
                    abortProcessing = false;
                    deleteProgram = true;
                    break;

                case ABORT:
                    abortProcessing = true;
                    // If deleteProgram is already true, don't change it to false
                    // (basically, leave as-is)
                    break;

                default:
                    // Do nothing, assume want to carry over options from before

            }

            if (abortProcessing) {
                Msg.info(this, "Processing aborted as a result of post-script.");
            } else if (options.analyze && !options.postScripts.isEmpty()) {
                Msg.info(this, "ANALYZING changes made by post scripts: " + fileAbsolutePath);
                txId = program.startTransaction("Post-Analysis");
                try {
                    mgr.startAnalysis(TaskMonitor.DUMMY); // kick start
                } finally {
                    program.endTransaction(txId, true);
                }
                Msg.info(this, "REPORT: Post-analysis succeeded for file: " + fileAbsolutePath);
            }

        }

        // Our hook after the analysis
        if (programHandler != null) {
            programHandler.PostProcessHandler(program);
        }

        return !deleteProgram;
    }

    /**
     * {@literal Run prescripts -> analysis -> postscripts (any of these steps is optional).}
     *
     * @param fileAbsolutePath Path of the file to analyze.
     * @param program          The program to analyze.
     * @return true if the program file should be kept. If analysis or scripts have
     * marked the program as temporary changes should not be saved. Returns
     * false in these cases: - One of the scripts sets the Headless
     * Continuation Option to "ABORT_AND_DELETE" or "CONTINUE_THEN_DELETE".
     */
    private boolean analyzeProgram(String fileAbsolutePath, Program program, List<String> falseAnalyzers) {

        analysisTimedOut = false;

        AutoAnalysisManager mgr = AutoAnalysisManager.getAnalysisManager(program);
        mgr.initializeOptions();

        GhidraState scriptState = null;
        LibHeadlessScript.HeadlessContinuationOption scriptStatus = LibHeadlessScript.HeadlessContinuationOption.CONTINUE;

        boolean abortProcessing = false;
        boolean deleteProgram = false;

        if (!options.preScripts.isEmpty()) {
            // create one state, in case each script might want to modify it to pass
            // information
            scriptState = getInitialProgramState(program);

            scriptStatus = runScriptsList(options.preScripts, options.preScriptFileMap, scriptState, scriptStatus);
        }

        switch (scriptStatus) {
            case ABORT_AND_DELETE:
                abortProcessing = true;
                deleteProgram = true;
                break;

            case CONTINUE_THEN_DELETE:
                abortProcessing = false;
                deleteProgram = true;
                break;

            case ABORT:
                abortProcessing = true;
                deleteProgram = false;
                break;

            default:
                // do nothing
        }

        if (abortProcessing) {
            Msg.info(this, "Processing aborted as a result of pre-script.");
            return !deleteProgram;
        }

        int txId = program.startTransaction("Analysis");
        Options analysisOptions = program.getOptions(Program.ANALYSIS_PROPERTIES);
        for (String falseAnalyer : falseAnalyzers) {
            analysisOptions.setBoolean(falseAnalyer, false);
        }

        try {
            if (options.analyze) {
                Msg.info(this, "ANALYZING all memory and code: " + fileAbsolutePath);
                mgr.initializeOptions();

                // Note: Want to analyze regardless of whether we have already analyzed or not
                // (user could have changed options).
                mgr.reAnalyzeAll(null);

                if (options.perFileTimeout == -1) {
                    mgr.startAnalysis(TaskMonitor.DUMMY); // kick start

                    Msg.info(this, "REPORT: Analysis succeeded for file: " + fileAbsolutePath);
                    GhidraProgramUtilities.setAnalyzedFlag(program, true);
                } else {
                    LibHeadlessTimedTaskMonitor timerMonitor = new LibHeadlessTimedTaskMonitor(options.perFileTimeout);
                    mgr.startAnalysis(timerMonitor);

                    if (timerMonitor.isCancelled()) {
                        Msg.error(this, "REPORT: Analysis timed out at " + options.perFileTimeout
                                + " seconds. Processing not completed for file: " + fileAbsolutePath);

                        // If no further scripts, just return the current program disposition
                        if (options.postScripts.isEmpty()) {
                            return !deleteProgram;
                        }

                        analysisTimedOut = true;
                    } else {
                        // If timeout didn't already happen at this point, cancel the monitor
                        timerMonitor.cancel();

                        Msg.info(this, "REPORT: Analysis succeeded for file: " + fileAbsolutePath);
                        GhidraProgramUtilities.setAnalyzedFlag(program, true);
                    }
                }
            }
        } finally {
            program.endTransaction(txId, true);
        }

        if (!options.postScripts.isEmpty()) {

            if (scriptState == null) {
                scriptState = getInitialProgramState(program);
            }

            scriptStatus = runScriptsList(options.postScripts, options.postScriptFileMap, scriptState, scriptStatus);

            switch (scriptStatus) {
                case ABORT_AND_DELETE:
                    abortProcessing = true;
                    deleteProgram = true;
                    break;

                case CONTINUE_THEN_DELETE:
                    abortProcessing = false;
                    deleteProgram = true;
                    break;

                case ABORT:
                    abortProcessing = true;
                    // If deleteProgram is already true, don't change it to false
                    // (basically, leave as-is)
                    break;

                default:
                    // Do nothing, assume want to carry over options from before

            }

            if (abortProcessing) {
                Msg.info(this, "Processing aborted as a result of post-script.");
            } else if (options.analyze && !options.postScripts.isEmpty()) {
                Msg.info(this, "ANALYZING changes made by post scripts: " + fileAbsolutePath);
                txId = program.startTransaction("Post-Analysis");
                try {
                    mgr.startAnalysis(TaskMonitor.DUMMY); // kick start
                } finally {
                    program.endTransaction(txId, true);
                }
                Msg.info(this, "REPORT: Post-analysis succeeded for file: " + fileAbsolutePath);
            }

        }

        // Our hook after the analysis
        if (programHandler != null) {
            programHandler.PostProcessHandler(program);
        }

        return !deleteProgram;
    }

    private void processFileNoImport(DomainFile domFile) throws IOException {

        if (domFile.isHijacked()) {
            Msg.error(this, "Skipped processing for " + domFile.getPathname() + " -- file is hijacked");
            return;
        }

        if (!ProgramContentHandler.PROGRAM_CONTENT_TYPE.equals(domFile.getContentType())) {
            return; // skip non-Program files
        }

        Program program = null;
        boolean keepFile = true; // if false file should be deleted after release
        boolean terminateCheckoutWhenDone = false;

        boolean readOnlyFile = options.readOnly || domFile.isReadOnly();

        try {
            // Exclusive checkout required when commit option specified
            if (!readOnlyFile) {
                if (domFile.isVersioned()) {
                    if (!domFile.isCheckedOut()) {
                        if (!domFile.checkout(options.commit, TaskMonitor.DUMMY)) {
                            Msg.warn(this, "Skipped processing for " + domFile.getPathname()
                                    + " -- failed to get exclusive file checkout required for commit");
                            return;
                        }
                    } else if (options.commit && !domFile.isCheckedOutExclusive()) {
                        Msg.error(this, "Skipped processing for " + domFile.getPathname()
                                + " -- file is checked-out non-exclusive (commit requires exclusive checkout)");
                        return;
                    }
                }
                terminateCheckoutWhenDone = true;
            }

            program = (Program) domFile.getDomainObject(this, true, false, TaskMonitor.DUMMY);

            Msg.info(this, "REPORT: Processing project file: " + domFile.getPathname());

            // This method already takes into account whether the user has set the
            // "noanalysis"
            // flag or not
            keepFile = analyzeProgram(domFile.getPathname(), program) || readOnlyFile;

            if (!keepFile) {
                program.setTemporary(true); // don't save changes
                if (!options.okToDelete) {
                    // Don't remove file unless okToDelete was specified
                    Msg.warn(this, "Due to script activity, " + domFile.getPathname()
                            + " deletion was requested but denied -- 'okToDelete' parameter was not specified");
                    keepFile = true;
                }
            }

            if (readOnlyFile) {
                if (program.isChanged()) {
                    Msg.info(this,
                            "REPORT: Discarding changes to the following read-only file: " + domFile.getPathname());
                }
                return;
            }

            if (program.isTemporary()) {
                if (program.isChanged()) {
                    Msg.info(this, "REPORT: Discarding changes to the following file as a result of script activity: "
                            + domFile.getPathname());
                }
                return;
            }

            if (domFile.canSave()) {
                domFile.save(TaskMonitor.DUMMY);
                Msg.info(this, "REPORT: Save succeeded for processed file: " + domFile.getPathname());
            }
            if (program.isChanged()) {
                Msg.error(this, "REPORT: Error trying to save changes to file: " + domFile.getPathname());
            }

            if (options.commit) {

                AutoAnalysisManager.getAnalysisManager(program).dispose();
                program.release(this);
                program = null;

                // Only commit if it's a shared project.
                commitProgram(domFile);
            }
        } catch (VersionException e) {

            if (e.isUpgradable()) {
                Msg.error(this,
                        domFile.getPathname() + ": this file was created with an older version of Ghidra.  Automatic "
                                + "upgrading of the file to the current version is possible, but "
                                + "requires an exclusive check-out of the file.  Please check out the file "
                                + " using the Ghidra GUI and then re-run Headless.");
            } else {
                Msg.error(this, domFile.getPathname()
                        + ": this file was created with a newer version of Ghidra, and can not be processed.");
            }
        } catch (CancelledException e) {
            // This can never happen because there is no user interaction in headless!
        } catch (Exception exc) {
            Msg.error(this, domFile.getPathname() + " Error during analysis: " + exc.getMessage());
        } finally {

            if (program != null) {
                AutoAnalysisManager.getAnalysisManager(program).dispose();
                program.release(this);
                program = null;
            }

            if (!readOnlyFile) { // can't change anything if read-only file

                // Undo checkout of it is still checked-out and either the file is to be
                // deleted, or we just checked it out and file changes have been committed
                if (domFile.isCheckedOut()) {
                    if (!keepFile || (terminateCheckoutWhenDone && !domFile.modifiedSinceCheckout())) {
                        domFile.undoCheckout(false);
                    }
                }

                if (!keepFile) {
                    deleteDomainFile(domFile);
                }
            }
        }
    }

    private void deleteDomainFile(DomainFile domFile) {
        if (domFile.isCheckedOut()) {
            Msg.error(this,
                    "Failed to delete file as requested due to pre-existing checkout: " + domFile.getPathname());
            return;
        }

        try {
            domFile.delete();
        } catch (IOException e) {
            Msg.error(this, "Failed to delete file as requested - " + e.getMessage() + ": " + domFile.getPathname());
        }
    }

    /**
     * Process all files within parentFolder which satisfies the specified
     * filenamePattern. If filenamePattern is null, all files will be processed
     *
     * @param parentFolder    domain folder to be searched
     * @param filenamePattern filename pattern or null for all files
     * @return true if one or more files processed
     * @throws IOException if an IO problem occurred.
     */
    private boolean processFolderNoImport(DomainFolder parentFolder, Pattern filenamePattern) throws IOException {

        if (parentFolder.isEmpty()) {
            return false;
        }

        boolean filesProcessed = false;

        for (DomainFile domFile : parentFolder.getFiles()) {
            if (filenamePattern == null || filenamePattern.matcher(domFile.getName()).matches()) {
                if (ProgramContentHandler.PROGRAM_CONTENT_TYPE.equals(domFile.getContentType())) {
                    filesProcessed = true;
                    processFileNoImport(domFile);
                }
            }
        }

        if (options.recursive) {
            for (DomainFolder folder : parentFolder.getFolders()) {
                filesProcessed |= processFolderNoImport(folder, filenamePattern);
            }
        }

        return filesProcessed;
    }

    /**
     * Process the specified filename within parentFolder.
     *
     * @param parentFolder domain folder to be searched
     * @param filename     name of file to be imported
     * @return true if one or more files processed
     * @throws IOException if an IO problem occurred.
     */
    private boolean processFolderNoImport(DomainFolder parentFolder, String filename) throws IOException {

        if (parentFolder.isEmpty()) {
            return false;
        }

        boolean filesProcessed = false;

        DomainFile domFile = parentFolder.getFile(filename);
        if (ProgramContentHandler.PROGRAM_CONTENT_TYPE.equals(domFile.getContentType())) {
            filesProcessed = true;
            processFileNoImport(domFile);
        }

        if (options.recursive) {
            for (DomainFolder folder : parentFolder.getFolders()) {
                filesProcessed |= processFolderNoImport(folder, filename);
            }
        }

        return filesProcessed;
    }

    private void processNoImport(String rootFolderPath) throws IOException {

        storage.clear();

        DomainFolder domFolder = project.getProjectData().getFolder(rootFolderPath);
        if (domFolder == null) {
            throw new IOException("Specified project folder not found: " + rootFolderPath);
        }

        Pattern filenamePattern = null;
        if (options.domainFileNameToProcess != null) {
            filenamePattern = createFilenamePattern(options.domainFileNameToProcess);
        }

        boolean filesProcessed = false;
        if (filenamePattern == null && options.domainFileNameToProcess != null) {
            // assume domainFileNameToProcess was a specific filename and not a pattern
            filesProcessed = processFolderNoImport(domFolder, options.domainFileNameToProcess);
        } else {
            filesProcessed = processFolderNoImport(domFolder, filenamePattern);
        }

        if (!filesProcessed) {
            if (options.domainFileNameToProcess != null) {
                throw new IOException(
                        "Requested project program file(s) not found: " + options.domainFileNameToProcess);
            }
            throw new IOException("No program files found within specified project folder: " + domFolder.getPathname());
        }
    }

    private Pattern createFilenamePattern(String name) {

        if ((name.indexOf('*') == -1) && (name.indexOf('?') == -1)) {
            // not a 'search' pattern
            return null;
        }

        // If surrounded by single-quotes, strip them, as to not interfere with the
        // Pattern
        if ((name.startsWith("\'")) && (name.endsWith("\'"))) {
            name = name.substring(1, name.length() - 1);
        }

        // Find files that match the wildcard pattern
        Pattern p = UserSearchUtils.createSearchPattern(name, true);
        return p;
    }

    private boolean checkOverwrite(DomainFile df) throws IOException {
        if (options.overwrite) {
            try {
                if (df.isHijacked()) {
                    Msg.error(this,
                            "REPORT: Found conflicting program file in project which is hijacked - overwrite denied: "
                                    + df.getPathname());
                    return false;
                }
                if (df.isVersioned()) {
                    if (!options.commit) {
                        Msg.error(this,
                                "REPORT: Found conflicting versioned program file in project with changes - overwrite denied when commit disabled: "
                                        + df.getPathname());
                        return false;
                    }
                    if (df.isCheckedOut()) {
                        df.undoCheckout(false);
                    }
                }
                try {
                    df.delete();
                } catch (IOException e) {
                    Msg.error(this, "REPORT: Failed to remove conflicting program file (" + e.getMessage() + "): "
                            + df.getPathname());
                    return false;
                }
            } catch (UserAccessException e) {
                Msg.error(this, "REPORT: Found conflicting program file in project which user is unable to overwrite: "
                        + df.getPathname());
                return false;
            }
            Msg.warn(this, "REPORT: Removed conflicting program file from project: " + df.getPathname());
        } else {
            Msg.error(this, "REPORT: Found conflicting program file in project: " + df.getPathname());
            return false;
        }
        return true;
    }

    private void commitProgram(DomainFile df) throws IOException {

        RepositoryAdapter rep = project.getRepository();
        if (rep != null) {
            try {
                rep.connect();
            } catch (IOException e) {
                ClientUtil.handleException(rep, e, "Connect", null);
            }
            if (!rep.isConnected()) {
                Msg.error(this, df.getPathname() + ": File check-in failed - repository connection error");
                throw new IOException(df.getPathname() + ": File check-in failed - repository connection error");
            }
        }

        if (df.canAddToRepository()) {
            try {
                df.addToVersionControl(options.commitComment, false, TaskMonitor.DUMMY);
                Msg.info(this, "REPORT: Added file to repository: " + df.getPathname());
            } catch (IOException e) {
                Msg.error(this, df.getPathname() + ": File check-in failed - " + e.getMessage());
                throw e;
            } catch (CancelledException e) {
                // this can never happen because there is no user interaction in headless!
            }
        } else if (df.canCheckin()) {
            try {
                df.checkin(new CheckinHandler() {
                    @Override
                    public boolean keepCheckedOut() throws CancelledException {
                        return true;
                    }

                    @Override
                    public String getComment() throws CancelledException {
                        return options.commitComment;
                    }

                    @Override
                    public boolean createKeepFile() throws CancelledException {
                        return false;
                    }
                }, true, TaskMonitor.DUMMY);
                Msg.info(this, "REPORT: Committed file changes to repository: " + df.getPathname());
            } catch (IOException e) {
                Msg.error(this, df.getPathname() + ": File check-in failed - " + e.getMessage());
                throw e;
            } catch (VersionException e) {
                Msg.error(this, df.getPathname() + ": File check-in failed - version error occurred");
            } catch (CancelledException e) {
                // this can never happen because there is no user interaction in headless!
            }
        } else {
            Msg.error(this, df.getPathname() + ": Unable to commit file");
        }
    }

    private boolean processFileWithImport(File file, String folderPath, List<String> falseAnalyzers) {

        Msg.info(this, "IMPORTING: " + file.getAbsolutePath());

        Program program = null;

        try {
            String dfName = null;
            DomainFile df = null;
            DomainFolder domainFolder = null;
            try {
                // Gets parent folder for import (creates path if doesn't exist)
                domainFolder = getDomainFolder(folderPath, false);

                dfName = file.getName();

                if (dfName.toLowerCase().endsWith(".gzf") || dfName.toLowerCase().endsWith(".xml")) {
                    // Use filename without .gzf
                    int index = dfName.lastIndexOf('.');
                    dfName = dfName.substring(0, index);
                }

                if (!options.readOnly) {
                    if (domainFolder != null) {
                        df = domainFolder.getFile(dfName);
                    }
                    if (df != null && !checkOverwrite(df)) {
                        Msg.error(this, "DomainFile: checkOverwrite(df) == true '" + file.getAbsolutePath() + "'.");
                        STATUS_MSG.setErrorMsg("DomainFile: checkOverwrite(df) == true ", file.getAbsolutePath());
                        return false;
                    }
                    df = null;
                }

                program = loadProgram(file);
                if (program == null) {
                    Msg.error(this, "program == null '" + file.getAbsolutePath() + "'.");
                    STATUS_MSG.setErrorMsg("program == null ", file.getAbsolutePath());
                    return false;
                }

                // Check if there are defined memory blocks; abort if not (there is nothing
                // to work with!)
                if (program.getMemory().getAllInitializedAddressSet().isEmpty()) {
                    Msg.error(this,
                            "REPORT: Error: No memory blocks were defined for file '" + file.getAbsolutePath() + "'.");
                    STATUS_MSG.setErrorMsg("REPORT: Error: No memory blocks were defined for file ",
                            file.getAbsolutePath());
                    return false;
                }
            } catch (Exception exc) {
                Msg.error(this, "REPORT: " + exc.getMessage(), exc);
                exc.printStackTrace();
                STATUS_MSG.setErrorMsg(exc.getMessage(), file.getAbsolutePath());
                return false;
            }

            Msg.info(this,
                    "REPORT: Import succeeded with language \"" + program.getLanguageID().getIdAsString()
                            + "\" and cspec \"" + program.getCompilerSpec().getCompilerSpecID().getIdAsString()
                            + "\" for file: " + file.getAbsolutePath());

            boolean doSave;
            try {

                doSave = analyzeProgram(file.getAbsolutePath(), program, falseAnalyzers) && !options.readOnly;

                if (!doSave) {
                    program.setTemporary(true);
                }

                // The act of marking the program as temporary by a script will signal
                // us to discard any program changes.
                if (program.isTemporary()) {
                    if (options.readOnly) {
                        Msg.info(this,
                                "REPORT: Discarded file import due to readOnly option: " + file.getAbsolutePath());
                    } else {
                        Msg.info(this, "REPORT: Discarded file import as a result of script "
                                + "activity or analysis timeout: " + file.getAbsolutePath());
                    }
                    return true;
                }

                try {
                    if (saveDomainFolder != null) {

                        df = saveDomainFolder.getFile(dfName);

                        // Return if file already exists and overwrite == false
                        if (df != null && !checkOverwrite(df)) {
                            Msg.error(this, "DomainFile: checkOverwrite(df) == true '" + file.getAbsolutePath() + "'.");
                            STATUS_MSG.setErrorMsg("DomainFile: checkOverwrite(df) == true ", file.getAbsolutePath());
                            return false;
                        }

                        domainFolder = saveDomainFolder;
                    } else if (domainFolder == null) {
                        domainFolder = getDomainFolder(folderPath, true);
                    }
                    df = domainFolder.createFile(dfName, program, TaskMonitor.DUMMY);
                    Msg.info(this, "REPORT: Save succeeded for file: " + df.getPathname());

                    if (options.commit) {

                        AutoAnalysisManager.getAnalysisManager(program).dispose();
                        program.release(this);
                        program = null;

                        commitProgram(df);
                    }
                } catch (IOException e) {
                    e.printStackTrace();
                    throw new IOException(
                            "Cannot create file: " + domainFolder.getPathname() + DomainFolder.SEPARATOR + dfName, e);
                }
            } catch (Exception exc) {
                String logErrorMsg = file.getAbsolutePath() + " Error during analysis: " + exc.getMessage();
                Msg.info(this, logErrorMsg);
                STATUS_MSG.setErrorMsg(exc.getMessage(), file.getAbsolutePath());
                return false;
            } finally {
                if (program != null) {
                    AutoAnalysisManager.getAnalysisManager(program).dispose();
                }
            }

            return true;
        } finally {
            // Program must be released here, since the AutoAnalysisManager uses program to
            // call dispose() in the finally() block above.
            if (program != null) {
                program.release(this);
                program = null;
            }
        }
    }

    private Program loadProgram(File file)
            throws VersionException, InvalidNameException, DuplicateNameException, CancelledException, IOException {

        MessageLog messageLog = new MessageLog();
        Program program = null;

        // NOTE: we must pass a null DomainFolder to the AutoImporter so as not to
        // allow the DomainFile to be saved at this point. DomainFile should be
        // saved after all applicable analysis/scripts are run.

        if (options.loaderClass == null) {
            // User did not specify a loader
            if (options.language == null) {
                program = AutoImporter.importByUsingBestGuess(file, null, this, messageLog, TaskMonitor.DUMMY);
            } else {
                program = AutoImporter.importByLookingForLcs(file, null, options.language, options.compilerSpec, this,
                        messageLog, TaskMonitor.DUMMY);
            }
        } else {
            // User specified a loader
            if (options.language == null) {
                program = AutoImporter.importByUsingSpecificLoaderClass(file, null, options.loaderClass,
                        options.loaderArgs, this, messageLog, TaskMonitor.DUMMY);
            } else {
                program = AutoImporter.importByUsingSpecificLoaderClassAndLcs(file, null, options.loaderClass,
                        options.loaderArgs, options.language, options.compilerSpec, this, messageLog,
                        TaskMonitor.DUMMY);
            }
        }

        if (program == null) {
            Msg.error(this,
                    "The AutoImporter could not successfully load " + file.getAbsolutePath()
                            + " with the provided import parameters. Please ensure that any specified"
                            + " processor/cspec arguments are compatible with the loader that is used during"
                            + " import and try again.");

            if (options.loaderClass != null && options.loaderClass != BinaryLoader.class) {
                Msg.error(this,
                        "NOTE: Import failure may be due to missing opinion for \""
                                + options.loaderClass.getSimpleName()
                                + "\". If so, please contact Ghidra team for assistance.");
            }

            return null;
        }

        return program;
    }

    private void processWithImport(File file, String folderPath, boolean isFirstTime, List<String> falseAnalyzers)
            throws IOException {

        boolean importSucceeded;

        if (file.isFile()) {

            importSucceeded = processFileWithImport(file, folderPath, falseAnalyzers);
            // Check to see if there are transient programs lying around due
            // to programs not being released during Importing
            List<DomainFile> domainFileContainer = new ArrayList<>();
            TransientDataManager.getTransients(domainFileContainer);
            if (domainFileContainer.size() > 0) {
                TransientDataManager.releaseFiles(this);
            }
            if (!importSucceeded) {
                Msg.error(this, "REPORT: Import failed for file: " + file.getAbsolutePath());
                throw new IOException("REPORT: Import failed for file:");
            }

            return;
        }

        // Looks inside the folder if one of two situations is applicable:
        // - If user supplied a directory to import, and it is currently being
        // processed (if so, this will be the first time that this method is called)
        // - If -recursive is specified
        if ((isFirstTime) || (!isFirstTime && options.recursive)) {
            // Otherwise, is a directory
            Msg.info(this, "REPORT: Importing all files from " + file.getName());

            File dirFile = file;

            if (!folderPath.endsWith(DomainFolder.SEPARATOR)) {
                folderPath += DomainFolder.SEPARATOR;
            }

            String subfolderPath = folderPath + file.getName();

            String[] names = dirFile.list();
            if (names != null) {
                Collections.sort(Arrays.asList(names));
                for (String name : names) {
                    if (name.charAt(0) == '.') {
                        Msg.warn(this, "Ignoring file '" + name + "'.");
                        continue;
                    }
                    file = new File(dirFile, name);

                    // Even a directory name has to have valid characters --
                    // can't create a folder if it's not valid
                    try {
                        checkValidFilename(file);
                        processWithImport(file, subfolderPath, false, falseAnalyzers);
                    } catch (InvalidInputException e) {
                        // Just move on if not valid
                    }
                }
            }
        }
    }

    private void processWithImport(String folderPath, List<File> inputDirFiles, List<String> falseAnalyzers)
            throws IOException {

        storage.clear();

        if (inputDirFiles != null && !inputDirFiles.isEmpty()) {
            Msg.info(this, "REPORT: Processing input files: ");
            Msg.info(this, "     project: " + project.getProjectLocator());
            for (File f : inputDirFiles) {
                processWithImport(f, folderPath, true, falseAnalyzers);
            }
        } else {
            // no input, just run the scripts

            // create one state, in case each script might want to modify it to pass
            // information
            GhidraState scriptState = new GhidraState(null, project, null, null, null, null);

            LibHeadlessScript.HeadlessContinuationOption scriptStatus = LibHeadlessScript.HeadlessContinuationOption.CONTINUE;

            scriptStatus = runScriptsList(options.preScripts, options.preScriptFileMap, scriptState, scriptStatus);

            // Since there is no program, "DELETE" is meaningless here.
            // If status asks for ABORT, then don't continue running the postscript.
            switch (scriptStatus) {
                case ABORT:
                case ABORT_AND_DELETE:
                    return;

                default:
                    // Just continue
            }

            runScriptsList(options.postScripts, options.postScriptFileMap, scriptState, scriptStatus);
        }
    }

    private Project openProject(ProjectLocator locator) throws IOException {
        Project tempProject;

        if (options.deleteProject) {
            Msg.warn(this, "Project already exists and will not be deleted: " + locator);
            options.deleteProject = false;
        }

        Msg.info(this, "Opening existing project: " + locator);
        try {
            tempProject = new HeadlessProject(getProjectManager(), locator);
        } catch (NotOwnerException e) {
            throw new IOException(e);
        } catch (LockException e) {
            throw new IOException(e);
        }

        return tempProject;

    }

    /**
     * Checks to make sure the given file contains only valid characters in its
     * name.
     *
     * @param currFile The file to check.
     * @throws InvalidInputException if the given file contains invalid characters
     *                               in it.
     */
    static void checkValidFilename(File currFile) throws InvalidInputException {
        boolean isDir = currFile.isDirectory();
        String filename = currFile.getName();

        for (int i = 0; i < filename.length(); i++) {
            char c = filename.charAt(i);
            if (!LocalFileSystem.isValidNameCharacter(c)) {
                if (isDir) {
                    throw new InvalidInputException("The directory '" + filename
                            + "' contains the invalid characgter: \'" + c
                            + "\' and can not be created in the project (full path: " + currFile.getAbsolutePath()
                            + "). To allow successful import of the directory and its contents, please rename the directory.");
                }
                throw new InvalidInputException("The file '" + filename + "' contains the invalid character: \'" + c
                        + "\' and can not be imported (full path: " + currFile.getAbsolutePath()
                        + "). Please rename the file.");
            }
        }
    }

    private HeadlessGhidraProjectManager getProjectManager() {
        if (projectManager == null) {
            projectManager = new HeadlessGhidraProjectManager();
        }
        return projectManager;
    }

    /**
     * Ghidra project class required to gain access to specialized project
     * constructor for URL connection.
     */
    private static class HeadlessProject extends DefaultProject {

        HeadlessProject(HeadlessGhidraProjectManager projectManager, GhidraURLConnection connection)
                throws IOException {
            super(projectManager, connection);
        }

        HeadlessProject(HeadlessGhidraProjectManager projectManager, ProjectLocator projectLocator)
                throws NotOwnerException, LockException, IOException {
            super(projectManager, projectLocator, false);
        }
    }

    private static class HeadlessGhidraProjectManager extends DefaultProjectManager {
        // this exists just to allow access to the constructor
    }

    public @interface getInstance {
    }
}

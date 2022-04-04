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

import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.*;

import generic.stl.Pair;
import ghidra.app.util.opinion.Loader;
import ghidra.framework.model.DomainFolder;
import ghidra.framework.protocol.ghidra.Handler;
import ghidra.util.Msg;
import ghidra.util.exception.InvalidInputException;
import thusca.bcat.client.utils.StatusMsg;

/**
 * Launcher entry point for running headless Ghidra.
 */
public class LibGhidra {

    private static final int EXIT_CODE_ERROR = 1;
    private String extractTargetPath;

    public LibGhidra(String path) {
        extractTargetPath = path;
        // Ghidra URL handler registration
        Handler.registerHandler();
    }


    public StatusMsg startGhidra(String args[], LibProgramHandler handler, List<String> falseAnalyzers) {
        String projectName = null;
        String rootFolderPath = null;
        URL ghidraURL = null;
        List<File> filesToImport = new ArrayList<>();
        int optionStartIndex;

        // Initialize our App
        // Make sure there are arguments
        if (args.length < 1) {
            StatusMsg statusMsg = new StatusMsg(false, "Wrong number of arguments", rootFolderPath);
            return statusMsg;
        }

        if (args[0].startsWith("ghidra:")) {
            optionStartIndex = 1;
            try {
                ghidraURL = new URL(args[0]);
            } catch (MalformedURLException e) {
                StatusMsg statusMsg = new StatusMsg(false, "Invalid Ghidra URL: " + args[0], rootFolderPath);
                return statusMsg;
            }
        } else {
            if (args.length < 2) {
                StatusMsg statusMsg = new StatusMsg(false, "Wrong number of arguments", rootFolderPath);
                return statusMsg;
            }
            optionStartIndex = 2;
            String projectNameAndFolder = args[1];

            // Check to see if projectName uses back-slashes (likely if they are using Windows)
            //projectNameAndFolder = projectNameAndFolder.replaceAll("\\\\", DomainFolder.SEPARATOR);
            projectName = projectNameAndFolder;

            rootFolderPath = "/";
            int folderIndex = projectNameAndFolder.indexOf(DomainFolder.SEPARATOR);
            if (folderIndex == 0) {
                StatusMsg statusMsg = new StatusMsg(false, args[1] + " is an invalid project_name/folder_path.", rootFolderPath);
                return statusMsg;
            } else if (folderIndex > 0) {
                projectName = projectNameAndFolder.substring(0, folderIndex);
                rootFolderPath = projectNameAndFolder.substring(folderIndex);
            }
        }

        // Determine the desired logging.
        File logFile = new File(extractTargetPath + "/" + UUID.randomUUID() + "_logFile.log");
        File scriptLogFile = new File(extractTargetPath + "/" + UUID.randomUUID() + "_scriptLogFile.log");
//        File logFile = new File(extractTargetPath);
//        File scriptLogFile = new File(extractTargetPath);

        try {
            // Instantiate new headless analyzer and parse options.
            LibHeadlessAnalyzer analyzer = LibHeadlessAnalyzer.getInstance(handler);
//            LibHeadlessAnalyzer analyzer = LibHeadlessAnalyzer.getLoggableInstance(logFile, scriptLogFile, true, handler);

            LibHeadlessOptions options = analyzer.getOptions();
            parseOptions(options, args, optionStartIndex, ghidraURL, filesToImport);
            StatusMsg statusMsg = analyzer.processLocal(args[0], projectName, rootFolderPath, filesToImport, falseAnalyzers);
            return statusMsg;
        } catch (Exception e) {
            StatusMsg statusMsg = new StatusMsg(false, e.getMessage(), rootFolderPath);
            e.printStackTrace();
            return statusMsg;
        } catch (Throwable e) {
            Msg.error(LibHeadlessAnalyzer.class, "Abort due to Headless analyzer error: " + e.getMessage(), e);
            StatusMsg statusMsg = new StatusMsg(false, e.getMessage(), rootFolderPath);
            e.printStackTrace();
            return statusMsg;
        }
    }

    /**
     * Parses the command line arguments and uses them to set the headless options.
     *
     * @param options       The headless options to set.
     * @param args          The command line arguments to parse.
     * @param startIndex    The index into the args array of where to start parsing.
     * @param ghidraURL     The ghidra server url to connect to, or null if not using a url.
     * @param filesToImport A list to put files to import into.
     * @throws InvalidInputException if an error occurred parsing the arguments or setting
     *                               the options.
     */
    private void parseOptions(LibHeadlessOptions options, String[] args, int startIndex, URL ghidraURL,
                              List<File> filesToImport) throws InvalidInputException {

        String loaderName = null;
        List<Pair<String, String>> loaderArgs = new LinkedList<>();
        String languageId = null;
        String compilerSpecId = null;
        String keystorePath = null;
        String serverUID = null;
        boolean allowPasswordPrompt = false;
        List<Pair<String, String[]>> preScripts = new LinkedList<>();
        List<Pair<String, String[]>> postScripts = new LinkedList<>();

        for (int argi = startIndex; argi < args.length; argi++) {

            String arg = args[argi];
            if (checkArgument("-log", args, argi)) {
                // Already processed
                argi++;
            } else if (checkArgument("-scriptlog", args, argi)) {
                // Already processed
                argi++;
            } else if (arg.equalsIgnoreCase("-overwrite")) {
                options.enableOverwriteOnConflict(true);
            } else if (arg.equalsIgnoreCase("-noanalysis")) {
                options.enableAnalysis(false);
            } else if (arg.equalsIgnoreCase("-deleteproject")) {
                options.setDeleteCreatedProjectOnClose(true);
            } else if (checkArgument("-loader", args, argi)) {
                loaderName = args[++argi];
            } else if (arg.startsWith(Loader.COMMAND_LINE_ARG_PREFIX)) {
                if (args[argi + 1].startsWith("-")) {
                    throw new InvalidInputException(args[argi] + " expects value to follow.");
                }
                loaderArgs.add(new Pair<>(arg, args[++argi]));
            } else if (checkArgument("-processor", args, argi)) {
                languageId = args[++argi];
            } else if (checkArgument("-cspec", args, argi)) {
                compilerSpecId = args[++argi];
            } else if (checkArgument("-prescript", args, argi)) {
                String scriptName = args[++argi];
                String[] scriptArgs = getSubArguments(args, argi);
                argi += scriptArgs.length;
                preScripts.add(new Pair<>(scriptName, scriptArgs));
            } else if (checkArgument("-postscript", args, argi)) {
                String scriptName = args[++argi];
                String[] scriptArgs = getSubArguments(args, argi);
                argi += scriptArgs.length;
                postScripts.add(new Pair<>(scriptName, scriptArgs));
            } else if (checkArgument("-scriptPath", args, argi)) {
                options.setScriptDirectories(args[++argi]);
            } else if (checkArgument("-propertiesPath", args, argi)) {
                options.setPropertiesFileDirectories(args[++argi]);
            } else if (checkArgument("-import", args, argi)) {
                File inputFile = new File(args[++argi]);
                if (!inputFile.isDirectory() && !inputFile.isFile()) {
                    throw new InvalidInputException(
                            inputFile.getAbsolutePath() + " is not a valid directory or file.");
                }

                LibHeadlessAnalyzer.checkValidFilename(inputFile);

                filesToImport.add(inputFile);

                // Keep checking for OS-expanded files
                String nextArg;

                while (argi < (args.length - 1)) {
                    nextArg = args[++argi];

                    // Check if next argument is a parameter
                    if (nextArg.charAt(0) == '-') {
                        argi--;
                        break;
                    }

                    File otherFile = new File(nextArg);
                    if (!otherFile.isFile() && !otherFile.isDirectory()) {
                        throw new InvalidInputException(
                                otherFile.getAbsolutePath() + " is not a valid directory or file.");
                    }

                    LibHeadlessAnalyzer.checkValidFilename(otherFile);

                    filesToImport.add(otherFile);
                }
            } else if ("-connect".equals(args[argi])) {
                if ((argi + 1) < args.length) {
                    arg = args[argi + 1];
                    if (!arg.startsWith("-")) {
                        // serverUID is optional argument after -connect
                        serverUID = arg;
                        ++argi;
                    }
                }
            } else if ("-commit".equals(args[argi])) {
                String comment = null;
                if ((argi + 1) < args.length) {
                    arg = args[argi + 1];
                    if (!arg.startsWith("-")) {
                        // comment is optional argument after -commit
                        comment = arg;
                        ++argi;
                    }
                }
                options.setCommitFiles(true, comment);
            } else if (checkArgument("-keystore", args, argi)) {
                keystorePath = args[++argi];
                File keystore = new File(keystorePath);
                if (!keystore.isFile()) {
                    throw new InvalidInputException(
                            keystore.getAbsolutePath() + " is not a valid keystore file.");
                }
            } else if (arg.equalsIgnoreCase("-p")) {
                allowPasswordPrompt = true;
            } else if ("-analysisTimeoutPerFile".equalsIgnoreCase(args[argi])) {
                options.setPerFileAnalysisTimeout(args[++argi]);
            } else if ("-process".equals(args[argi])) {
                if (options.runScriptsNoImport) {
                    throw new InvalidInputException(
                            "The -process option may only be specified once.");
                }
                String processBinary = null;
                if ((argi + 1) < args.length) {
                    arg = args[argi + 1];
                    if (!arg.startsWith("-")) {
                        // processBinary is optional argument after -process
                        processBinary = arg;
                        ++argi;
                    }
                }
                options.setRunScriptsNoImport(true, processBinary);
            } else if ("-recursive".equals(args[argi])) {
                options.enableRecursiveProcessing(true);
            } else if ("-readOnly".equalsIgnoreCase(args[argi])) {
                options.enableReadOnlyProcessing(true);
            } else if (checkArgument("-max-cpu", args, argi)) {
                String cpuVal = args[++argi];
                try {
                    options.setMaxCpu(Integer.parseInt(cpuVal));
                } catch (NumberFormatException nfe) {
                    throw new InvalidInputException("Invalid value for max-cpu: " + cpuVal);
                }
            } else if ("-okToDelete".equalsIgnoreCase(args[argi])) {
                options.setOkToDelete(true);
            } else {
                throw new InvalidInputException("Bad argument: " + arg);
            }
        }

        // Set up pre and post scripts
        options.setPreScriptsWithArgs(preScripts);
        options.setPostScriptsWithArgs(postScripts);

        // Set loader and loader args
        options.setLoader(loaderName, loaderArgs);

        // Set user-specified language and compiler spec
        options.setLanguageAndCompiler(languageId, compilerSpecId);

        // Set up optional Ghidra Server authenticator
        try {
            options.setClientCredentials(serverUID, keystorePath, allowPasswordPrompt);
        } catch (IOException e) {
            throw new InvalidInputException(
                    "Failed to install Ghidra Server authenticator: " + e.getMessage());
        }

        // If -process was specified, inputFiles must be null or inputFiles.size must be 0.
        // Otherwise when not in -process mode, inputFiles can be null or inputFiles.size can be 0,
        // only if there are scripts to be run.
        if (options.runScriptsNoImport) {

            if (filesToImport != null && filesToImport.size() > 0) {
                System.err.print("Must use either -process or -import parameters, but not both.");
                System.err.print(" -process runs scripts over existing program(s) in a project, " +
                        "whereas -import");
                System.err.println(" imports new programs and runs scripts and/or analyzes them " +
                        "after import.");
                System.exit(EXIT_CODE_ERROR);
            }

            if (options.overwrite) {
                Msg.warn(LibHeadlessAnalyzer.class,
                        "The -overwrite parameter does not apply to -process mode.  Ignoring overwrite " +
                                "and continuing.");
            }

            if (options.readOnly && options.okToDelete) {
                System.err.println("You have specified the conflicting parameters -readOnly and " +
                        "-okToDelete. Please pick one and try again.");
                System.exit(EXIT_CODE_ERROR);
            }
        } else {
            if (filesToImport == null || filesToImport.size() == 0) {
                if (options.preScripts.isEmpty() && options.postScripts.isEmpty()) {
                    System.err.println("Nothing to do ... must specify -import, -process, or " +
                            "prescript and/or postscript.");
                    System.exit(EXIT_CODE_ERROR);
                } else {
                    Msg.warn(LibHeadlessAnalyzer.class,
                            "Neither the -import parameter nor the -process parameter was specified; " +
                                    "therefore, the specified prescripts and/or postscripts will be " +
                                    "executed without any type of program context.");
                }
            }
        }

        if (options.commit) {
            if (options.readOnly) {
                System.err.println("Can not use -commit and -readOnly at the same time.");
                System.exit(EXIT_CODE_ERROR);
            }
        }

        // Implied commit, only if not in process mode
        if (!options.commit && ghidraURL != null) {
            if (!options.readOnly) {
                // implied commit
                options.setCommitFiles(true, null);
            } else {
                Msg.warn(LibHeadlessAnalyzer.class,
                        "-readOnly mode is on: for -process, changes will not be saved.");
            }
        }
    }

    private String[] getSubArguments(String[] args, int argi) {
        List<String> subArgs = new LinkedList<>();
        int i = argi + 1;
        while (i < args.length && !args[i].startsWith("-")) {
            subArgs.add(args[i++]);
        }
        return subArgs.toArray(new String[0]);
    }

    private boolean checkArgument(String optionName, String[] args, int argi)
            throws InvalidInputException {
        // everything after this requires an argument
        if (!optionName.equalsIgnoreCase(args[argi])) {
            return false;
        }
        if (argi + 1 == args.length) {
            throw new InvalidInputException(optionName + " requires an argument");
        }
        return true;
    }
}

package thusca.bcat.client.utils;

import java.util.*;

import com.google.common.io.BaseEncoding;

import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressIterator;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.util.exception.CancelledException;
import ghidra.util.task.TaskMonitor;
import ghidra.program.model.mem.MemoryAccessException;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.pcode.PcodeOp;
import ghidra.program.model.block.BasicBlockModel;
import ghidra.program.model.block.CodeBlock;
import ghidra.program.model.block.CodeBlockIterator;
import ghidra.program.model.block.CodeBlockReference;
import ghidra.program.model.block.CodeBlockReferenceIterator;
import thusca.bcat.client.entity.BinFileFeature;
import thusca.bcat.client.entity.FunctionFeature;
import thusca.bcat.client.utils.libghidra.*;
import ghidra.program.flatapi.FlatProgramAPI;
import ghidra.program.model.lang.OperandType;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.address.AddressSetView;

/**
 * BinaryAnalyzer is the module to analyze a binary file and extract from it.
 * The entry point is Method extractFeatures(String). Features are extracted and
 * stored in the static variable binFileFeature.
 */
public class BinaryAnalyzer implements LibProgramHandler {
    private String extractTargetPath;
    private String tmpDir;
    private String jsonDir;
    private String fileType;
    private static String headlessImportCmd = "%s %s -import %s -max-cpu 1 -overwrite -deleteProject";
    private BinFileFeature binFileFeature = new BinFileFeature();
    private List<String> exportAddress = new ArrayList<>();
    private Map<String, MemoryBlock> memoryBlocksMap = new HashMap<>();
    private static Map<String, List<String>> fileTypeAndSection = new HashMap<>() {
        private static final long serialVersionUID = 1L;

        {
            put("ELF", Arrays.asList(".rodata", ".text"));
            put("PE", Arrays.asList(".rdata", ".text"));
            put("Mach-O", Arrays.asList("__cstring", "__text"));
        }
    };
    private static List<String> geminiAllTransferInstr = Arrays.asList("je", "jz", "jne", "jnz", "js", "jns", "jo", "jno", "jc", "jnc", "jp", "jpe", "jnp", "jpo", "jl", "jpo", "jl", "jnge", "jnl", "jge", "jg", "jnle", "jng", "jle", "jb", "jnae", "jnb", "jae", "ja", "jnbe", "jna", "jbe", "jmp", "opd", "jmp opd", "jcxz", "jecxz", "loop", "loopw", "loopd", "loope", "loopz", "loopne", "loopnz", "reg", "ops", "bound", "bound reg", "call", "opd", "call opd", "ret", "retn", "int", "into", "iret", "iretd", "iretf", "j", "jal", "jalr", "b", "bal", "bl", "blx", "bx", "bc0f", "bc0f1", "bc0t", "bc0t1", "bc2f", "bc2f1", "bc2t", "bc2t1", "bc1f", "bc1f1", "bc1t", "bc1t1", "beq", "beq1", "beqz", "beqz1", "bge", "bge1", "bgeu", "bgeu1", "bgez", "bgez1", "bgt", "bgt1", "bgtu", "bgtu1", "bgtz", "bgtz1", "ble", "ble1", "bleu", "bleu1", "blez", "blez1", "blt", "blt1", "bltu", "bltu1", "bltz", "bltz1", "bne", "bnel", "bnez", "bnezl", "bgeza1", "bgeza11", "bltza1", "bltza11");

    private static List<String> geminiArithmeticInstr = Arrays.asList("aaa", "aad", "aam", "aas", "adc", "add", "addu", "addiu", "dadd", "daddi", "daddu", "daddiu", "dsub", "dsubu", "subu", "abs", "dabs", "dneg", "dnegu", "negu", "cbw", "cdq", "cwd", "cwde", "daa", "das", "dec", "div", "divo", "divou", "idiv", "ddiv", "ddivu", "divu", "dmul", "dmulu", "mulo", "mulou", "dmulo", "dmulou", "dmult", "dmultu", "mult", "multu", "imul", "inc", "mul", "drem", "dremu", "rem", "remu", "mfhi", "mflo", "mthi", "mtlo", "sbb", "sub", "rsb", "sbc", "rsc", "c", "r", "mla", "smull", "smlal", "umull", "umlal");

    private static List<String> geminiLogicInstr = Arrays.asList("and", "andi", "or", "xor", "not", "test", "eor", "orr", "teq", "tst", "ori", "nor");



    public BinaryAnalyzer(String extractTargetPath, String tmpDir, String jsonPath, String fileType) {
        this.extractTargetPath = extractTargetPath;
        this.tmpDir = tmpDir;
        this.jsonDir = jsonPath;
        this.fileType = fileType;
    }

    /**
     * @param {String} [extractTargetPath]
     * @description: Entry point for the BinaryAnalyzer.
     */
    public StatusMsg extractFeatures() {
        // Set whether to use log or not.

        // Set analysis options. Added analyzer is set to false.
        List<String> falseAnalyzers = new ArrayList<>();
        falseAnalyzers.add("Stack");
        falseAnalyzers.add("Create Address Tables");
        falseAnalyzers.add("x86 Constant Reference Analyzer");
        falseAnalyzers.add("GCC Exception Handlers");

        falseAnalyzers.add("Non-Returning Functions - Discovered");
        falseAnalyzers.add("Non-Returning Functions - Known");
        falseAnalyzers.add("Decompiler Switch Analysis");
        falseAnalyzers.add("Call Convention Identification");
        falseAnalyzers.add("Objective-C 2 Decompiler Message");

        // Generate the headlessCmd and run it.
        String headlessCmd = String.format(headlessImportCmd, tmpDir, tmpDir.substring(tmpDir.length() - 6), extractTargetPath);

        LibGhidra libGhidra = new LibGhidra(jsonDir);
        StatusMsg statusMsg = libGhidra.startGhidra(headlessCmd.split("\\s+"), this, falseAnalyzers);
        return statusMsg;
    }

    /**
     * Ghidra's post process script. It extracts all needed features and stores them
     * in the static variable binFileFeature.
     */
    @Override
    public void PostProcessHandler(Program program) {
        binFileFeature.setFileName(program.getName());
        binFileFeature.setFileType(program.getExecutableFormat());
        setMemoryBlocks(program);
        getStringConstants(program);
        getImports(program);
        getExports(program);
        getFunctions(program);
    }

    private void setMemoryBlocks(Program program) {
        MemoryBlock[] memoryBlocks = program.getMemory().getBlocks();
        for (MemoryBlock memoryBlock : memoryBlocks) {
            memoryBlocksMap.put(memoryBlock.getName(), memoryBlock);
        }
    }

    /**
     * Extract string constants from the analyzed binary file.
     */
    private void getStringConstants(Program program) {
        DataIterator dataIterator = program.getListing().getData(true);
        List<String> stringConstants = new ArrayList<>();
        String section = fileTypeAndSection.get(this.fileType).get(0);
        while (dataIterator.hasNext()) {
            Data data = dataIterator.next();
            // TODO:how to parse string-utf8
            // if (data.getDataType().getName().equals("string") ||
            // data.getDataType().getName().equals("string-utf8")) {
            if ((data.getDataType().getName().equals("string")
                    || data.getDataType().getName().equals("TerminatedCString")) && memoryBlocksMap.containsKey(section)
                    && memoryBlocksMap.get(fileTypeAndSection.get(this.fileType).get(0)).contains(data.getAddress())) {
                stringConstants.add(data.getValue().toString());
            }
        }
        binFileFeature.setStringConstants(stringConstants);
    }

    /**
     * Extract import function names.
     */
    private void getImports(Program program) {
        // imports (only functions excluding other symbolTypes, for example
        // SymbolType.Label)
        SymbolTable symbolTable = program.getSymbolTable();
        SymbolIterator externaSymbolIterator = symbolTable.getExternalSymbols();
        List<String> imports = new ArrayList<>();
        while (externaSymbolIterator.hasNext()) {
            Symbol symbol = externaSymbolIterator.next();
            if (symbol.getSymbolType().toString() == "Function") {
                imports.add(symbol.getName(true).replace("-", ":").replace("<EXTERNAL>::", ""));
            }
        }
        binFileFeature.setImportFunctionNames(imports);
    }

    /**
     * Extract export function names.
     */
    private void getExports(Program program) {
        // exports (only function excluding other symbolTypes)
        // TODO:whether export labels (not function) are useful.
        SymbolTable symbolTable = program.getSymbolTable();
        AddressIterator externalEntryPointIterator = symbolTable.getExternalEntryPointIterator();
        List<String> exports = new ArrayList<>();
        while (externalEntryPointIterator.hasNext()) {
            Address address = externalEntryPointIterator.next();
            Symbol primarySymbol = symbolTable.getPrimarySymbol(address);
            if (primarySymbol != null && primarySymbol.getSymbolType().equals(SymbolType.FUNCTION)) {
                exports.add(primarySymbol.getName(true).replace("-", ":"));
                exportAddress.add(primarySymbol.getAddress().toString());
            }
        }
        binFileFeature.setExportFunctionNames(exports);
    }

    /**
     * Extract all functions including their function body, instructions, params...
     */
    private void getFunctions(Program program) {
        // Functions
        FunctionIterator functionIterator = program.getListing().getFunctions(true);
        List<FunctionFeature> functionFeatures = new ArrayList<>();
        FlatProgramAPI programAPIInstance = new FlatProgramAPI(program, TaskMonitor.DUMMY);
        // FlatDecompilerAPI flatDecompilerAPI = new FlatDecompilerAPI(programAPIInstance);
        // try {
        //     flatDecompilerAPI.initialize();
        // } catch (Exception e1) {
        //     e1.printStackTrace();
        // }

        while (functionIterator.hasNext()) {
            Function function = functionIterator.next();
            FunctionFeature functionFeature = new FunctionFeature();
            // set basic properties
            functionFeature.setFunctionName(function.getName(true).replace("-", ":"));
            functionFeature.setFunctionType(function.getReturnType().getName());
            Parameter[] parameters = function.getParameters(VariableFilter.NONAUTO_PARAMETER_FILTER);
            List<String> params = new ArrayList<>();
            for (Parameter parameter : parameters) {
                params.add(parameter.getDataType().getName());
            }
            functionFeature.setArgs(params);
            functionFeature.setFunctionSignature(function.getPrototypeString(true, true));
            String entryPoint = function.getEntryPoint().toString();
            functionFeature.setEntryPoint(entryPoint);
            functionFeature.setIsExportFunction(exportAddress.contains(entryPoint));
            boolean isImportFun = false;
            if (memoryBlocksMap.containsKey("EXTERNAL")) {
                isImportFun = memoryBlocksMap.get("EXTERNAL").contains(function.getEntryPoint());
            }
            functionFeature.setIsImportFunction(function.isExternal() || isImportFun);
            functionFeature.setIsThunkFunction(function.isThunk());
            MemoryBlock block = program.getMemory().getBlock(function.getEntryPoint());
            if (block != null) {
                functionFeature.setMemoryBlock(block.getName());
            }

            functionFeature.setIsInline(function.isInline());
            functionFeature.setVariables(function.getAllVariables().length);

            //to delete
            // add instructions and pcodes
            InstructionIterator instructionIterator = program.getListing().getInstructions(function.getBody(), true);
            List<String> instructionBytes = new ArrayList<>();
            List<String> instructions = new ArrayList<>();
            List<String> opcodes = new ArrayList<>();
            List<String> pcodeInstr = new ArrayList<>();
            int[] pcodes = new int[PcodeOp.PCODE_MAX];
            // int i = 0;
            // Map<String, Integer> pcodeTable = new LinkedHashMap<>();
            // System.out.println(PcodeOp.PCODE_MAX);
            // while (i <= PcodeOp.PCODE_MAX) {
            // pcodeTable.put(PcodeOp.getMnemonic(i), i);
            // i++;
            // }
            // System.out.println(pcodeTable);
            functionFeature.setPcodes(pcodes);
            functionFeature.setInstructionBytes(instructionBytes);
            functionFeature.setInstructions(instructions);
            functionFeature.setOpcodes(opcodes);
            functionFeature.setPcodeInstr(pcodeInstr);


            // add calling functions
            ArrayList<List<String>> callingFunctions = getParents(function, true);
            List<String> callingFunctionAddresses = callingFunctions.get(0);
            List<String> callingFunctionsByPointer = callingFunctions.get(1);

            functionFeature.setCallingFunctionAddresses(callingFunctionAddresses);
            functionFeature.setCallingFunctionsByPointer(callingFunctionsByPointer);

            // add called function address
            String textSection = fileTypeAndSection.get(this.fileType).get(1);
            ArrayList<List<String>> calledFunctions = getChildren(function, true, textSection, memoryBlocksMap);
            List<String> calledFunctionAddresses = calledFunctions.get(0);
            List<String> calledImports = calledFunctions.get(1);
            List<String> calledFunctionsByPointer = calledFunctions.get(2);

            functionFeature.setCalledImports(calledImports);
            functionFeature.setCalledFunctionAddresses(calledFunctionAddresses);
            functionFeature.setCalledFunctionsByPointer(calledFunctionsByPointer);
            Map<String, List<String>> calledStringsData = getCalledStrings(function.getBody(), function.getProgram(), memoryBlocksMap,
                    fileTypeAndSection.get(this.fileType));
            functionFeature.setCalledStrings(calledStringsData.get("calledStrings"));
            functionFeature.setCalledData(calledStringsData.get("calledData"));
            try {
                int[] cfgProperities = calculateCyclomaticComplexity(function, TaskMonitor.DUMMY);
                functionFeature.setEdges(cfgProperities[0]);
                functionFeature.setNodes(cfgProperities[1]);
                functionFeature.setExits(cfgProperities[2]);
                functionFeature.setComplexity(cfgProperities[3]);
            } catch (CancelledException e) {
                // TODO Auto-generated catch block
                e.printStackTrace();
            }
            try {
                functionFeature = getCFG(function, TaskMonitor.DUMMY, function.getProgram(), functionFeature);
            } catch (CancelledException e) {
                // TODO Auto-generated catch block
                e.printStackTrace();
            }
            functionFeatures.add(functionFeature);
        }
        binFileFeature.setFunctions(functionFeatures);
    }

    public BinFileFeature getBinFileFeature() {
        return binFileFeature;
    }

    public static ArrayList<List<String>> getParents(Function function, boolean followThunks) {
        Program program = function.getProgram();
        FunctionManager functionManager = program.getFunctionManager();
        ReferenceManager referenceManager = program.getReferenceManager();
        List<String> callingFunctionAddresses = new ArrayList<>();
        List<String> callingFunctionsByPointer = new ArrayList<>();
        ArrayList<List<String>> res = new ArrayList<List<String>>();
        int size = 0;
        Address curAddr = function.getEntryPoint();
        Address[] thunkAddresses = null;
        if (followThunks) {
            thunkAddresses = function.getFunctionThunkAddresses();
            if (thunkAddresses != null) {
                size = thunkAddresses.length;
            }
        }
        int pos = -1;
        for (;;) {
            ReferenceIterator referenceIterator = referenceManager.getReferencesTo(curAddr);
            for (Reference reference : referenceIterator) {
                Address fromAddress = reference.getFromAddress();
                Function par = functionManager.getFunctionContaining(fromAddress);
                if (par != null && !par.isThunk()) {
                    if (reference.getReferenceType().isCall()) {
                        callingFunctionAddresses.add(par.getEntryPoint().toString());
                    } else {
                        callingFunctionsByPointer.add(par.getEntryPoint().toString());
                    }
                }
            }
            pos += 1;
            if (pos >= size)
                break;
            curAddr = thunkAddresses[pos];
        }
        res.add(callingFunctionAddresses);
        res.add(callingFunctionsByPointer);
        return res;
    }

    private ArrayList<List<String>> getChildren(Function function, boolean followThunks, String section,
                                                Map<String, MemoryBlock> memoryBlocksMap) {
        Program program = function.getProgram();
        FunctionManager functionManager = program.getFunctionManager();
        ReferenceManager referenceManager = program.getReferenceManager();
        ArrayList<List<String>> res = new ArrayList<List<String>>();
        List<String> calledFunctionAddresses = new ArrayList<>();
        List<String> calledImports = new ArrayList<>();
        List<String> calledFunctionsByPointer = new ArrayList<>();
        AddressIterator referenceIterator = referenceManager.getReferenceSourceIterator(function.getBody(), true);
        // improved: add thunked function if it is a thunk function
        // for plt functions calling external function, referenceManager.
        // getReferenceSourceIterator(function.getBody(), true); will
        // not get the calling relations.
        if (followThunks) {
            Function thunkedFunction = function.getThunkedFunction(true);
            if (thunkedFunction != null) {
                maybeAddingFunction(thunkedFunction, calledFunctionAddresses, calledImports, calledFunctionsByPointer,
                        section, null);
            }
        }

        for (Address address : referenceIterator) {
            Reference[] referencesFrom = referenceManager.getReferencesFrom(address);
            for (Reference reference : referencesFrom) {
                Address toAddress = reference.getToAddress();
                Function child = functionManager.getFunctionAt(toAddress);
                if (child != null) {
                    if (followThunks && child.isThunk()) {
                        child = child.getThunkedFunction(true);
                    }
                    maybeAddingFunction(child, calledFunctionAddresses, calledImports, calledFunctionsByPointer,
                            section, reference);
                }
            }
        }
        res.add(calledFunctionAddresses);
        res.add(calledImports);
        res.add(calledFunctionsByPointer);
        return res;
    }

    private ArrayList<List<String>> getCalls(CodeBlock codeBlock, Program program, boolean followThunks, String section, Map<String, MemoryBlock> memoryBlocksMap) {
        FunctionManager functionManager = program.getFunctionManager();
        ReferenceManager referenceManager = program.getReferenceManager();
        ArrayList<List<String>> res = new ArrayList<List<String>>();
        List<String> calledFunctionAddresses = new ArrayList<>();
        List<String> calledImports = new ArrayList<>();
        List<String> calledFunctionsByPointer = new ArrayList<>();
        AddressIterator referenceIterator = referenceManager.getReferenceSourceIterator(codeBlock, true);

        for (Address address : referenceIterator) {
            Reference[] referencesFrom = referenceManager.getReferencesFrom(address);
            for (Reference reference : referencesFrom) {
                Address toAddress = reference.getToAddress();
                Function child = functionManager.getFunctionAt(toAddress);
                if (child != null) {
                    if (followThunks && child.isThunk()) {
                        child = child.getThunkedFunction(true);
                    }
                    maybeAddingFunction(child, calledFunctionAddresses, calledImports, calledFunctionsByPointer,
                            section, reference);
                }
            }
        }
        res.add(calledFunctionAddresses);
        res.add(calledImports);
        res.add(calledFunctionsByPointer);
        return res;
    }

    private void maybeAddingFunction(Function calledFunction, List<String> calledFunctionAddresses,
                                     List<String> calledImports, List<String> calledFunctionsByPointer, String section, Reference reference) {
        if (calledFunction.isExternal() || (memoryBlocksMap.containsKey("EXTERNAL")
                && memoryBlocksMap.get("EXTERNAL").contains(calledFunction.getEntryPoint()))) {
            calledImports.add(calledFunction.getName(true).replace("-", ":").replace("<EXTERNAL>::", ""));
        } else if (reference != null && !reference.getReferenceType().isCall()) {
            calledFunctionsByPointer.add(calledFunction.getEntryPoint().toString());
            // } else if (memoryBlocksMap.containsKey(section)
            // && memoryBlocksMap.get(section).contains(calledFunction.getEntryPoint())) {
        } else {
            calledFunctionAddresses.add(calledFunction.getEntryPoint().toString());
        }
    }

    public int[] calculateCyclomaticComplexity(Function function, TaskMonitor monitor) throws CancelledException {
        BasicBlockModel basicBlockModel = new BasicBlockModel(function.getProgram());
        CodeBlockIterator codeBlockIterator = basicBlockModel.getCodeBlocksContaining(function.getBody(), monitor);
        Address entryPoint = function.getEntryPoint();
        int nodes = 0;
        int edges = 0;
        int exits = 0;
        while (codeBlockIterator.hasNext()) {
            if (monitor.isCancelled()) {
                break;
            }
            CodeBlock codeBlock = codeBlockIterator.next();
            ++nodes;
            if (codeBlock.getFlowType().isTerminal()) {
                ++exits;
                // strongly connect the exit to the entry point (*)
                ++edges;
            }
            CodeBlockReferenceIterator destinations = codeBlock.getDestinations(monitor);
            while (destinations.hasNext()) {
                if (monitor.isCancelled()) {
                    break;
                }
                CodeBlockReference reference = destinations.next();
                FlowType flowType = reference.getFlowType();
                if (flowType.isIndirect() || flowType.isCall()) {
                    continue;
                }
                ++edges;
                if (codeBlock.getFlowType().isTerminal() && reference.getDestinationAddress().equals(entryPoint)) {
                    // remove the edge I created since it already exists and was counted above at
                    // (*)
                    --edges;
                }
            }
        }
        int complexity = edges - nodes + exits;
        return new int[] { edges, nodes, exits, complexity < 0 ? 0 : complexity };
    }

    public static Map<String, List<String>> getCalledStrings(AddressSetView addressSet, Program program, Map<String, MemoryBlock> memoryBlocksMap, List<String> section) {
        Map<String, List<String>> res = new HashMap<>();
        List<String> calledStrings = new ArrayList<>();
        List<String> calledData = new ArrayList<>();
        ReferenceManager referenceManager = program.getReferenceManager();
        AddressIterator referenceIterator = referenceManager.getReferenceSourceIterator(addressSet, true);
        for (Address address : referenceIterator) {
            Reference[] referencesFrom = referenceManager.getReferencesFrom(address);
            for (Reference reference : referencesFrom) {
                if (reference.getReferenceType().isData()) {
                    Address toAddress = reference.getToAddress();
                    // TODO how to use undefined data, array data. for example libpng.so.3.22 at
                    // 001203c0
                    // if (toAddress.toString().equals("001203c0") ||
                    // toAddress.toString().equals("001203f0")) {
                    // System.out.println("now in");
                    // }
                    Data data = program.getListing().getDataContaining(toAddress);
                    if (data == null) {
                        continue;
                    }
                    if ((data.getDataType().getName().equals("string")
                            || data.getDataType().getName().equals("TerminatedCString"))
                            && memoryBlocksMap.containsKey(section.get(0))
                            && memoryBlocksMap.get(section.get(0)).contains(data.getAddress())) {
                        calledStrings.add(data.getAddress().toString()+":"+data.getValue().toString());
                    }
                    else{
                        try {
                            byte[] bytesInstruction = data.getBytes();
                            calledData.add(data.getAddress().toString()+":"+BaseEncoding.base16().encode(bytesInstruction));
                        } catch (MemoryAccessException e) {
                            // e.printStackTrace();
                        }
                    }
                }
            }
        }
        res.put("calledStrings", new ArrayList<>(new HashSet<>(calledStrings)));
        res.put("calledData", new ArrayList<>(new HashSet<>(calledData)));
        return res;
    }

    public FunctionFeature getCFG(Function function, TaskMonitor monitor, Program program, FunctionFeature functionFeature) throws CancelledException {
        List<List<Integer>> edgePairs = new ArrayList<>();
        List<List<Integer>> nodeGeminiVectors = new ArrayList<>();
        List<List<Integer>> nodeGhidraVectors = new ArrayList<>();
        List<List<String>> nodesAsm = new ArrayList<>();
        List<List<String>> nodesPcode = new ArrayList<>();
        List<List<Long>> intConstants = new ArrayList<>();
        List<List<String>> stringConstants = new ArrayList<>();
        Map<String, Integer> nodeEntryIndex = new HashMap<>();
        Map<Integer, List<String>> edgeIndexEntryString = new HashMap<>();
        int index = 0;

        BasicBlockModel basicBlockModel = new BasicBlockModel(program);
        CodeBlockIterator codeBlockIterator = basicBlockModel.getCodeBlocksContaining(function.getBody(), monitor);

        while (codeBlockIterator.hasNext()) {
            if (monitor.isCancelled()) {
                break;
            }
            CodeBlock codeBlock = codeBlockIterator.next();
            List<String> nodeAsm = new ArrayList<>();
            List<String> nodePcode = new ArrayList<>();
            List<Long> intConstant = new ArrayList<>();
            List<String> stringConstant = new ArrayList<>();
            int transferNum = 0;
            int arithNum = 0;
            int logicNum = 0;
            int callNum = 0;
            int instrNum = 0;
            int callImports = 0;
            int callByAddress = 0;
            List<Integer> pcodes = new ArrayList<Integer>(Collections.nCopies(PcodeOp.PCODE_MAX, 0));
            String nodeEntry = codeBlock.getFirstStartAddress().toString();
            nodeEntryIndex.put(nodeEntry, index);

            InstructionIterator instructionIterator = program.getListing().getInstructions(codeBlock, true);
            while (instructionIterator.hasNext()) {
                Instruction instruction = instructionIterator.next();
                nodeAsm.add(instruction.toString());
                instrNum += 1;
                if (geminiAllTransferInstr.contains(instruction.getMnemonicString().toLowerCase())){
                    transferNum += 1;
                }
                else if (geminiArithmeticInstr.contains(instruction.getMnemonicString().toLowerCase())) {
                    arithNum += 1;
                }
                else if (geminiLogicInstr.contains(instruction.getMnemonicString().toLowerCase())) {
                    logicNum += 1;
                }
                PcodeOp[] pcodeOps = instruction.getPcode();
                for (PcodeOp pcodeOp : pcodeOps) {
                    nodePcode.add(pcodeOp.toString());
                    int opCodeIndex = pcodeOp.getOpcode();
                    pcodes.set(opCodeIndex, pcodes.get(opCodeIndex) + 1);
                }

                int opeIndex = 0;
                while(opeIndex < instruction.getNumOperands()){
                    String operandType = OperandType.toString(instruction.getPrototype().getOpType(opeIndex, instruction.getInstructionContext()));
                    if (operandType.equals("")){
                        List<Object> opReList = instruction.getPrototype().getOpRepresentationList(opeIndex, instruction.getInstructionContext());
                        for (Object opRe : opReList){
                            if (opRe.getClass().getName().equals("ghidra.program.model.scalar.Scalar")) {
                                Scalar s = (Scalar)opRe;
                                intConstant.add(s.getValue());
                                // System.out.println(s.getValue());
                            }
                        }
                    }
                    else if (operandType.equals("SCAL")) {
                        List<Object> opReList = instruction.getPrototype().getOpRepresentationList(opeIndex, instruction.getInstructionContext());
                        if (opReList.size() < 3) {
                            intConstant.add(instruction.getPrototype().getScalar(opeIndex, instruction.getInstructionContext()).getValue());
                        }
                    }
                    opeIndex += 1;
                }
            }

            CodeBlockReferenceIterator destinations = codeBlock.getDestinations(monitor);
            List<String> desti = new ArrayList<>();
            while (destinations.hasNext()) {
                if (monitor.isCancelled()) {
                    break;
                }
                CodeBlockReference reference = destinations.next();
                FlowType flowType = reference.getFlowType();
                if (flowType.isIndirect() || flowType.isCall()) {
                    continue;
                }
                desti.add(reference.getDestinationBlock().getFirstStartAddress().toString());
            }
            if (desti.size() > 0) {
                edgeIndexEntryString.put(index, desti);
            }


            stringConstant = getCalledStrings(codeBlock, program, memoryBlocksMap, fileTypeAndSection.get(this.fileType)).get("calledStrings");
            ArrayList<List<String>> calledFunctions = getCalls(codeBlock, program, true, fileTypeAndSection.get(this.fileType).get(1), memoryBlocksMap);
            callNum = calledFunctions.get(0).size();
            callImports= calledFunctions.get(1).size();
            callByAddress = calledFunctions.get(2).size();
            List<Integer> geminiVector = new ArrayList<>(Arrays.asList(stringConstant.size(), intConstant.size(), transferNum, callNum, instrNum, arithNum, desti.size()));
            List<Integer> ghidraVector = new ArrayList<>(Arrays.asList(callNum, callByAddress, callImports, stringConstant.size(), intConstant.size(), instrNum));
            ghidraVector.addAll(pcodes);

            nodeGeminiVectors.add(geminiVector);
            nodeGhidraVectors.add(ghidraVector);
            nodesAsm.add(nodeAsm);
            nodesPcode.add(nodePcode);
            intConstants.add(intConstant);
            stringConstants.add(stringConstant);

            index += 1;
        }

        for (int sourceIndex: edgeIndexEntryString.keySet()) {
            for (String desti: edgeIndexEntryString.get(sourceIndex)) {
                edgePairs.add(Arrays.asList(sourceIndex, nodeEntryIndex.get(desti)));
            }
        }

        functionFeature.setEdgePairs(edgePairs);
        functionFeature.setNodeGeminiVectors(nodeGeminiVectors);
        functionFeature.setNodeGhidraVectors(nodeGhidraVectors);
        functionFeature.setNodesAsm(nodesAsm);
        functionFeature.setNodesPcode(nodesPcode);
        functionFeature.setIntConstants(intConstants);
        functionFeature.setStringConstants(stringConstants);
        return functionFeature;
    }
}
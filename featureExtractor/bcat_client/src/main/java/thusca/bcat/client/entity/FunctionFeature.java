package thusca.bcat.client.entity;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

import lombok.Data;

@Data
public class FunctionFeature {
    private String functionName = "";
    private String functionType = "";
    private List<String> args = new ArrayList<>();
    private String functionSignature = "";
    private String entryPoint = "";
    private Boolean isExportFunction;
    private Boolean isImportFunction;
    private Boolean isThunkFunction;
    private Boolean isInline;
    private String memoryBlock = "";
    private int edges;
    private int nodes;
    private int exits;
    private int complexity;
    private String cfSignature = "";
    private String cfBody = "";
    private int variables;

    private List<String> instructionBytes = new ArrayList<>();
    private List<String> instructions = new ArrayList<>();
    private List<String> opcodes = new ArrayList<>();
    private List<String> pcodeInstr = new ArrayList<>();
    private List<String> callingFunctionAddresses = new ArrayList<>();
    private List<String> callingFunctionsByPointer = new ArrayList<>();
    private List<String> calledFunctionAddresses = new ArrayList<>();
    private List<String> calledFunctionsByPointer = new ArrayList<>();
    private List<String> calledStrings = new ArrayList<>();
    private List<String> calledImports = new ArrayList<>();
    private List<String> calledData = new ArrayList<>();
    private int[] pcodes = new int[]{};

    private List<Map<String, Object>> nodesCFG = new ArrayList<>();
    private List<Map<String, Object>> edgesCFG = new ArrayList<>();
    
    private List<List<Integer>> edgePairs = new ArrayList<>();
    private List<List<Integer>> nodeGeminiVectors = new ArrayList<>();
    private List<List<Integer>> nodeGhidraVectors = new ArrayList<>();
    private List<List<String>> nodesAsm = new ArrayList<>();
    private List<List<String>> nodesPcode = new ArrayList<>();
    private List<List<Long>> intConstants = new ArrayList<>();
    private List<List<String>> stringConstants = new ArrayList<>();
    

    // private List<Integer> pcodes = new ArrayList<Integer>(Collections.nCopies(73, 0));

    // static Map<String, Integer> pcodeIndex = Map.ofEntries(
    //     Map.entry("COPY", 0),
    //     Map.entry("INT_ADD", 1),
    //     Map.entry("BOOL_OR", 2),
    //     Map.entry("LOAD", 3),
    //     Map.entry("INT_SUB", 4),
    //     Map.entry("FLOAT_EQUAL", 5),
    //     Map.entry("STORE", 6),
    //     Map.entry("INT_CARRY", 7),
    //     Map.entry("FLOAT_NOTEQUAL", 8),
    //     Map.entry("BRANCH", 9),
    //     Map.entry("INT_SCARRY", 10),
    //     Map.entry("FLOAT_LESS", 11),
    //     Map.entry("CBRANCH", 12),
    //     Map.entry("INT_SBORROW", 13),
    //     Map.entry("FLOAT_LESSEQUAL", 14),
    //     Map.entry("BRANCHIND", 15),
    //     Map.entry("INT_2COMP", 16),
    //     Map.entry("FLOAT_ADD", 17),
    //     Map.entry("CALL", 18),
    //     Map.entry("INT_NEGATE", 19),
    //     Map.entry("FLOAT_SUB", 20),
    //     Map.entry("CALLIND", 21),
    //     Map.entry("INT_XOR", 22),
    //     Map.entry("FLOAT_MULT", 23),
    //     Map.entry("USERDEFINED", 24),
    //     Map.entry("INT_AND", 25),
    //     Map.entry("FLOAT_DIV", 26),
    //     Map.entry("RETURN", 27),
    //     Map.entry("INT_OR", 28),
    //     Map.entry("FLOAT_NEG", 29),
    //     Map.entry("PIECE", 30),
    //     Map.entry("INT_LEFT", 31),
    //     Map.entry("FLOAT_ABS", 32),
    //     Map.entry("SUBPIECE", 33),
    //     Map.entry("INT_RIGHT", 34),
    //     Map.entry("FLOAT_SQRT", 35),
    //     Map.entry("INT_EQUAL", 36),
    //     Map.entry("INT_SRIGHT", 37),
    //     Map.entry("FLOAT_CEIL", 38),
    //     Map.entry("INT_NOTEQUAL", 39),
    //     Map.entry("INT_MULT", 40),
    //     Map.entry("FLOAT_FLOOR", 41),
    //     Map.entry("INT_LESS", 42),
    //     Map.entry("INT_DIV", 43),
    //     Map.entry("FLOAT_ROUND", 44),
    //     Map.entry("INT_SLESS", 45),
    //     Map.entry("INT_REM", 46),
    //     Map.entry("FLOAT_NAN", 47),
    //     Map.entry("INT_LESSEQUAL", 48),
    //     Map.entry("INT_SDIV", 49),
    //     Map.entry("INT2FLOAT", 50),
    //     Map.entry("INT_SLESSEQUAL", 51),
    //     Map.entry("INT_SREM", 52),
    //     Map.entry("FLOAT2FLOAT", 53),
    //     Map.entry("INT_ZEXT", 54),
    //     Map.entry("BOOL_NEGATE", 55),
    //     Map.entry("TRUNC", 56),
    //     Map.entry("INT_SEXT", 57),
    //     Map.entry("BOOL_XOR", 58),
    //     Map.entry("CPOOLREF", 59),
    //     Map.entry("BOOL_AND", 60),
    //     Map.entry("NEW", 61)
    // );
    // static List<String> PCODES = Arrays.asList("COPY", "INT_ADD", "BOOL_OR", "LOAD","INT_SUB", "FLOAT_EQUAL", "STORE", "INT_CARRY", "FLOAT_NOTEQUAL", "BRANCH", "INT_SCARRY", "FLOAT_LESS", "CBRANCH", "INT_SBORROW", "FLOAT_LESSEQUAL", "BRANCHIND", "INT_2COMP", "FLOAT_ADD", "CALL", "INT_NEGATE", "FLOAT_SUB", "CALLIND", "INT_XOR", "FLOAT_MULT", "USERDEFINED", "INT_AND", "FLOAT_DIV", "RETURN", "INT_OR", "FLOAT_NEG", "PIECE", "INT_LEFT", "FLOAT_ABS", "SUBPIECE", "INT_RIGHT", "FLOAT_SQRT", "INT_EQUAL", "INT_SRIGHT", "FLOAT_CEIL", "INT_NOTEQUAL", "INT_MULT", "FLOAT_FLOOR", "INT_LESS", "INT_DIV", "FLOAT_ROUND", "INT_SLESS", "INT_REM", "FLOAT_NAN", "INT_LESSEQUAL", "INT_SDIV", "INT2FLOAT", "INT_SLESSEQUAL", "INT_SREM", "FLOAT2FLOAT", "INT_ZEXT", "BOOL_NEGATE", "TRUNC", "INT_SEXT", "BOOL_XOR", "CPOOLREF", "BOOL_AND", "NEW");

    @Override
    public boolean equals(Object obj) {
        if (this == obj)
            return true;
        if (obj == null)
            return false;
        if (getClass() != obj.getClass())
            return false;
        FunctionFeature other = (FunctionFeature) obj;
        if (args == null) {
            if (other.args != null)
                return false;
        } else if (!args.equals(other.args))
            return false;
        if (calledFunctionAddresses == null) {
            if (other.calledFunctionAddresses != null)
                return false;
            // } else if (!calledFunctionAddresses.equals(other.calledFunctionAddresses))
        } else if (!isListEqual(calledFunctionAddresses, other.calledFunctionAddresses))
            return false;
        if (calledImports == null) {
            if (other.calledImports != null)
                return false;
            // } else if (!calledImports.equals(other.calledImports))
        } else if (!isListEqual(calledImports, other.calledImports))
            return false;
        if (calledStrings == null) {
            if (other.calledStrings != null)
                return false;
            // } else if (!calledStrings.equals(other.calledStrings))
        } else if (!isListEqual(calledStrings, other.calledStrings))
            return false;
        if (callingFunctionAddresses == null) {
            if (other.callingFunctionAddresses != null)
                return false;
            // } else if (!callingFunctionAddresses.equals(other.callingFunctionAddresses))
        } else if (!isListEqual(callingFunctionAddresses, other.callingFunctionAddresses))
            return false;
        if (entryPoint == null) {
            if (other.entryPoint != null)
                return false;
        } else if (!entryPoint.equals(other.entryPoint))
            return false;
        if (functionName == null) {
            if (other.functionName != null)
                return false;
        } else if (!functionName.equals(other.functionName))
            return false;
        if (functionSignature == null) {
            if (other.functionSignature != null)
                return false;
        } else if (!functionSignature.equals(other.functionSignature))
            return false;
        if (functionType == null) {
            if (other.functionType != null)
                return false;
        } else if (!functionType.equals(other.functionType))
            return false;
        if (instructionBytes == null) {
            if (other.instructionBytes != null)
                return false;
        } else if (!instructionBytes.equals(other.instructionBytes))
            return false;
        if (instructions == null) {
            if (other.instructions != null)
                return false;
        } else if (!instructions.equals(other.instructions))
            return false;
        if (isExportFunction == null) {
            if (other.isExportFunction != null)
                return false;
        } else if (!isExportFunction.equals(other.isExportFunction))
            return false;
        if (isImportFunction == null) {
            if (other.isImportFunction != null)
                return false;
        } else if (!isImportFunction.equals(other.isImportFunction))
            return false;
        if (isThunkFunction == null) {
            if (other.isThunkFunction != null)
                return false;
        } else if (!isThunkFunction.equals(other.isThunkFunction))
            return false;
        if (memoryBlock == null) {
            if (other.memoryBlock != null)
                return false;
        } else if (!memoryBlock.equals(other.memoryBlock))
            return false;
        if (opcodes == null) {
            if (other.opcodes != null)
                return false;
        } else if (!opcodes.equals(other.opcodes))
            return false;
        return true;
    }

    public static boolean isListEqual(List l0, List l1) {
        if (l0 == l1)
            return true;
        if (l0 == null && l1 == null)
            return true;
        if (l0 == null || l1 == null)
            return false;
        if (l0.size() != l1.size())
            return false;
        for (Object o : l0) {
            if (!l1.contains(o))
                return false;
        }
        for (Object o : l1) {
            if (!l0.contains(o))
                return false;
        }
        return true;
    }

    @Override
    public int hashCode() {
        final int prime = 31;
        int result = 1;
        result = prime * result + ((args == null) ? 0 : args.hashCode());
        result = prime * result + ((calledFunctionAddresses == null) ? 0 : calledFunctionAddresses.hashCode());
        result = prime * result + ((calledImports == null) ? 0 : calledImports.hashCode());
        result = prime * result + ((calledStrings == null) ? 0 : calledStrings.hashCode());
        result = prime * result + ((callingFunctionAddresses == null) ? 0 : callingFunctionAddresses.hashCode());
        result = prime * result + ((entryPoint == null) ? 0 : entryPoint.hashCode());
        result = prime * result + ((functionName == null) ? 0 : functionName.hashCode());
        result = prime * result + ((functionSignature == null) ? 0 : functionSignature.hashCode());
        result = prime * result + ((functionType == null) ? 0 : functionType.hashCode());
        result = prime * result + ((instructionBytes == null) ? 0 : instructionBytes.hashCode());
        result = prime * result + ((instructions == null) ? 0 : instructions.hashCode());
        result = prime * result + ((isExportFunction == null) ? 0 : isExportFunction.hashCode());
        result = prime * result + ((isImportFunction == null) ? 0 : isImportFunction.hashCode());
        result = prime * result + ((isThunkFunction == null) ? 0 : isThunkFunction.hashCode());
        result = prime * result + ((memoryBlock == null) ? 0 : memoryBlock.hashCode());
        result = prime * result + ((opcodes == null) ? 0 : opcodes.hashCode());
        return result;
    }
}

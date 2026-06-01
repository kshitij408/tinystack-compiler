# TinyStack Compiler

A minimal stack-based programming language compiler that generates LLVM Intermediate Representation (IR) and native executables.

## Project Overview

TinyStack Compiler is a complete compiler implementation for a stack-based programming language, designed to demonstrate compiler construction principles. The compiler pipeline transforms human-readable TinyStack source code into optimized LLVM IR and ultimately native executable binaries through integration with Clang.

### Objectives

- Implement a complete compiler for a stack-based language from lexical analysis through code generation
- Demonstrate core compiler construction techniques including lexing, parsing, and semantic analysis
- Generate efficient LLVM intermediate representation with optional optimization passes
- Produce native executables via Clang/LLVM integration
- Implement comprehensive error detection and reporting

## Features

### Core Language Features

- **Variables**: Declaration and manipulation of integer variables with initialization
- **Stack Operations**: Push values onto the stack, store values in variables
- **Arithmetic Operations**: Addition, subtraction, multiplication, and signed integer division
- **Control Flow**: Conditional execution via if-then-else statements
- **I/O**: Program output via print statements
- **Comparison Operators**: Greater than, less than, equality, and inequality comparisons

### Compiler Features

- **Lexical Analysis**: Tokenization with comprehensive token type support and error reporting
- **Recursive-Descent Parser**: Syntax analysis using recursive descent parsing technique
- **Abstract Syntax Tree (AST)**: Structured representation of program syntax
- **Semantic Analysis**: Variable validation, error detection, and stack verification
- **LLVM Code Generation**: Production of optimized LLVM IR using llvmlite
- **Optimization**: LLVM IR optimization passes for efficient code
- **Native Code Generation**: Integration with Clang for native executable compilation

## Quick Start

### Clone and Setup

```bash
git clone <repository-url>
cd tinystack-compiler
pip install -r requirements.txt
```

### Run Tests

```bash
# Compile and test arithmetic example
python3 src/main.py testcases/arithmetic.ts
clang output/output_optimized.ll -o output/program
./output/program
```

**Expected Output:**
```
Result: 55
```

Additional test cases:
- `testcases/if_else_true.ts` → Expected: `Result: 1`
- `testcases/if_else_false.ts` → Expected: `Result: 0`
- `testcases/error.ts` → Expected: Semantic error message

## Installation

### Prerequisites

- Python 3.8 or higher
- LLVM 10+ and Clang (for native code generation)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd tinystack-compiler
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Verify LLVM/Clang installation:
```bash
llc --version
clang --version
```

## Project Structure

```
tinystack-compiler/
├── README.md                          # This file
├── DESIGN.md                          # Compiler architecture and design
├── IMPLEMENTATION.md                  # Detailed implementation guide
├── EVALUATION.md                      # Testing and evaluation results
├── requirements.txt                   # Python dependencies
├── build.sh                          # Native executable build script
├── run.sh                            # Test execution script
├── src/                              # Compiler source code
│   ├── main.py                       # Compiler driver and entry point
│   ├── lexer.py                      # Tokenization (lexical analysis)
│   ├── parser.py                     # Syntax analysis (recursive descent)
│   ├── ast_nodes.py                  # Abstract syntax tree node definitions
│   ├── semantic.py                   # Semantic analysis and validation
│   ├── emitter.py                    # LLVM IR code generation
│   ├── optimizer.py                  # LLVM IR optimization
│   ├── runtime.py                    # Runtime support functions
│   └── errors.py                     # Error handling utilities
├── testcases/                        # Test suite
│   ├── arithmetic.ts                 # Arithmetic operations test
│   ├── if_else_true.ts               # If-else true branch test
│   ├── if_else_false.ts              # If-else false branch test
│   └── error.ts                      # Semantic error test
├── output/                           # Generated IR and binaries
│   ├── output.ll                     # Unoptimized LLVM IR
│   ├── output_optimized.ll           # Optimized LLVM IR
│   └── program                       # Native executable
└── docs/                             # Additional documentation
```

## Build and Run

### Compile a TinyStack Program

```bash
python3 src/main.py testcases/arithmetic.ts
```

This generates:
- `output/output.ll` - Unoptimized LLVM IR
- `output/output_optimized.ll` - Optimized LLVM IR

### Generate Native Executable

```bash
clang output/output_optimized.ll -o output/program
./output/program
```

Or use the provided script:

```bash
bash run.sh testcases/arithmetic.ts
```

## Example Test Cases

The `testcases/` directory contains four example programs:

### arithmetic.ts - Arithmetic Operations

Simple addition test:
```
push 20
push 35
add
print
```
**Output:** `Result: 55`

### if_else_true.ts - True Branch Condition

Conditional execution when condition is true:
```
push 10
push 5
if > then
  push 1
  print
else
  push 0
  print
end
```
**Output:** `Result: 1`

### if_else_false.ts - False Branch Condition

Conditional execution when condition is false:
```
push 5
push 10
if > then
  push 1
  print
else
  push 0
  print
end
```
**Output:** `Result: 0`

### error.ts - Semantic Error

Demonstrates error detection:
```
push x
```
**Output:** `Semantic Error: Undefined variable`

## Verified Test Results

All implemented features have been comprehensively tested:

| Test Case | Status | Output/Result |
|-----------|--------|---------------|
| Arithmetic Test | ✓ PASS | Result: 55 |
| If-Else True Test | ✓ PASS | Result: 1 |
| If-Else False Test | ✓ PASS | Result: 0 |
| Semantic Error Detection | ✓ PASS | Error detected |
| LLVM IR Generation | ✓ PASS | Valid LLVM IR |
| LLVM Optimization | ✓ PASS | IR successfully optimized |
| Native Executable Generation | ✓ PASS | Binary executes correctly |

## Compiler Pipeline

The TinyStack compiler follows a traditional multi-stage pipeline:

```
Source Code (.ts)
        ↓
    [LEXER]      → Tokenization with line/column tracking
        ↓
    Token Stream
        ↓
    [PARSER]     → Recursive-descent syntax analysis
        ↓
    Abstract Syntax Tree (AST)
        ↓
   [SEMANTIC]    → Validation and type checking
        ↓
   Validated AST
        ↓
   [EMITTER]     → LLVM IR code generation
        ↓
   LLVM IR Text
        ↓
  [OPTIMIZER]    → Optional IR optimization
        ↓
   Optimized LLVM IR
        ↓
   [LLVM/CLANG]  → Native code generation
        ↓
   Native Binary
```

## Error Handling

The compiler provides detailed error reporting at each stage:

### Lexer Errors
- Invalid token sequences
- Unexpected characters

### Parser Errors
- Syntax errors (missing keywords, operators, etc.)
- Unexpected token sequences

### Semantic Errors
- Undefined variable references
- Duplicate variable declarations
- Stack underflow in operations
- Invalid stack depth at program end

Error messages include source location (line and column) for easy debugging.

## Assignment Requirements Covered

The TinyStack Compiler successfully implements all required compiler construction techniques and language features:

### Compiler Stages
- ✓ **Lexer**: Comprehensive tokenization with line/column tracking
- ✓ **Recursive-Descent Parser**: Syntax analysis using recursive descent parsing technique
- ✓ **Semantic Analysis**: Variable validation, error detection, stack verification
- ✓ **LLVM IR Generation**: Production of optimized LLVM intermediate representation
- ✓ **LLVM Optimization**: IR optimization passes for code efficiency
- ✓ **Native Executable Generation**: Integration with Clang for binary compilation

### Language Features
- ✓ **Variables**: Declaration and manipulation of integer variables
- ✓ **Arithmetic Operations**: Addition, subtraction, multiplication, signed division
- ✓ **If-Else Statements**: Conditional execution with branch control flow
- ✓ **Print Statements**: Output functionality with formatted results
- ✓ **Stack Operations**: Push/pop semantics with operand stack management
- ✓ **Comparison Operators**: Greater than, less than, equality, inequality

### Semantic Analysis
- ✓ **Error Handling**: Comprehensive error detection and reporting
- ✓ **Stack-to-SSA Mapping**: Efficient conversion of stack operations to LLVM SSA form
- ✓ **Variable Scope Management**: Proper variable declaration and usage validation
- ✓ **Type Safety**: Integer-only type system with validation

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.8+ |
| IR Generation | llvmlite | 0.41.0+ |
| IR Optimization | LLVM | 10+ |
| Code Generation | Clang | 10+ |
| Build System | Bash | 4.0+ |

## License

This project is provided as-is for educational purposes.

## Documentation

- **[DESIGN.md](DESIGN.md)**: Detailed architecture, design decisions, and system overview
- **[IMPLEMENTATION.md](IMPLEMENTATION.md)**: Implementation details for each compiler stage
- **[EVALUATION.md](EVALUATION.md)**: Test results, performance analysis, and future work

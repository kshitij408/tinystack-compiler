<div align="center">

# ⚡ TinyStack Compiler

### A Minimal Stack-Based Programming Language Compiler Powered by LLVM

<img src="https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python" />
<img src="https://img.shields.io/badge/LLVM-10+-orange?style=for-the-badge&logo=llvm" />
<img src="https://img.shields.io/badge/Clang-Supported-success?style=for-the-badge&logo=c" />
<img src="https://img.shields.io/badge/Status-Completed-brightgreen?style=for-the-badge" />

---

### 🚀 From TinyStack Source Code → LLVM IR → Native Executable

*A complete compiler implementation demonstrating modern compiler construction techniques including Lexical Analysis, Parsing, Semantic Analysis, LLVM IR Generation, Optimization, and Native Code Compilation.*

</div>

---

# ✨ Overview

TinyStack Compiler is a complete educational compiler built using Python and LLVM.

The project demonstrates how modern compilers transform human-readable source code into highly optimized native machine code.

The compiler follows a traditional multi-stage architecture:

```text
Source Code
     ↓
 Lexer
     ↓
 Parser
     ↓
 AST
     ↓
 Semantic Analysis
     ↓
 LLVM IR Generation
     ↓
 LLVM Optimization
     ↓
 Native Executable
```

---

# 🎯 Key Features

## 📦 Language Features

- Variable Declaration & Assignment
- Stack-Based Execution Model
- Integer Arithmetic Operations
- Conditional If-Else Statements
- Comparison Operators
- Print Statements
- Push / Store Operations

---

## ⚙️ Compiler Features

- Recursive Descent Parser
- Abstract Syntax Tree Generation
- Semantic Analysis
- LLVM IR Generation
- LLVM Optimization Passes
- Native Binary Compilation
- Comprehensive Error Handling
- Source Location Tracking

---

# 🏗️ Compiler Architecture

```text
┌─────────────────┐
│ TinyStack Code  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Lexer       │
└────────┬────────┘
         │ Tokens
         ▼
┌─────────────────┐
│     Parser      │
└────────┬────────┘
         │ AST
         ▼
┌─────────────────┐
│ Semantic Check  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LLVM Generator  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LLVM Optimizer  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Native Program  │
└─────────────────┘
```

---

# 🚀 Quick Start

## Clone Repository

```bash
git clone <repository-url>
cd tinystack-compiler
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Verify Installation

```bash
clang --version
llc --version
```

---

# 🔥 Compile Your First Program

```bash
python3 src/main.py testcases/arithmetic.ts
```

Generated Files:

```text
output/
├── output.ll
├── output_optimized.ll
└── program
```

---

# ⚡ Generate Native Executable

```bash
clang output/output_optimized.ll -o output/program
```

Run:

```bash
./output/program
```

Output:

```text
Result: 55
```

---

# 📝 Example Programs

## Arithmetic Example

```ts
push 20
push 35
add
print
```

Output

```text
Result: 55
```

---

## If-Else Example

```ts
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

Output

```text
Result: 1
```

---

# 📂 Project Structure

```text
TinyStack-Compiler/
│
├── README.md
├── DESIGN.md
├── IMPLEMENTATION.md
├── EVALUATION.md
│
├── src/
│   ├── main.py
│   ├── lexer.py
│   ├── parser.py
│   ├── semantic.py
│   ├── emitter.py
│   ├── optimizer.py
│   ├── runtime.py
│   └── errors.py
│
├── testcases/
│   ├── arithmetic.ts
│   ├── if_else_true.ts
│   ├── if_else_false.ts
│   └── error.ts
│
└── output/
```

---

# 🧪 Test Results

| Test Case | Status |
|------------|---------|
| Arithmetic Operations | ✅ PASS |
| If-Else True Branch | ✅ PASS |
| If-Else False Branch | ✅ PASS |
| Semantic Error Detection | ✅ PASS |
| LLVM IR Generation | ✅ PASS |
| LLVM Optimization | ✅ PASS |
| Native Binary Execution | ✅ PASS |

---

# 🚨 Error Handling

The compiler detects and reports:

### Lexer Errors

- Invalid Tokens
- Unexpected Characters

### Parser Errors

- Missing Keywords
- Invalid Syntax

### Semantic Errors

- Undefined Variables
- Duplicate Declarations
- Stack Underflow
- Invalid Program State

Example:

```text
Semantic Error:
Undefined variable 'x'
Line 4, Column 7
```

---

# 🛠️ Technology Stack

| Component | Technology |
|------------|------------|
| Programming Language | Python 3.8+ |
| Intermediate Representation | LLVM |
| IR Library | llvmlite |
| Native Compilation | Clang |
| Build Scripts | Bash |

---

# 📊 Assignment Requirements Coverage

## Compiler Construction

- ✅ Lexical Analysis
- ✅ Recursive Descent Parsing
- ✅ AST Generation
- ✅ Semantic Analysis
- ✅ LLVM IR Generation
- ✅ LLVM Optimization
- ✅ Native Code Generation

## Language Features

- ✅ Variables
- ✅ Arithmetic Operations
- ✅ Conditional Statements
- ✅ Print Statements
- ✅ Stack Operations
- ✅ Comparison Operators

---

# 📚 Documentation

| File | Description |
|--------|------------|
| DESIGN.md | Architecture & Design Decisions |
| IMPLEMENTATION.md | Compiler Implementation Details |
| EVALUATION.md | Testing & Performance Analysis |

---

<div align="center">

## 🌟 TinyStack Compiler

**Building a Compiler from Scratch using Python & LLVM**

Made for learning Compiler Design, LLVM IR Generation and Modern Programming Language Implementation.

⭐ Star this repository if you found it useful.

</div>

# TinyStack Compiler: Implementation Details

## Overview

This document provides detailed technical information about the implementation of each compiler phase. It is intended for developers who wish to understand, maintain, or extend the TinyStack compiler.

## 1. Lexical Analysis (Lexer)

### Module: `src/lexer.py`

The lexer transforms raw source text into a stream of tokens, the input for the parser.

### Token Types

```python
class TokenType(Enum):
    # Keywords
    VAR = auto()           # Variable declaration
    PUSH = auto()          # Push value to stack
    STORE = auto()         # Store stack value in variable
    ADD = auto()           # Addition
    SUB = auto()           # Subtraction
    MUL = auto()           # Multiplication
    DIV = auto()           # Division
    IF = auto()            # Conditional
    ELSE = auto()          # Else branch
    THEN = auto()          # Then branch
    END = auto()           # End block
    PRINT = auto()         # Print statement
    
    # Operators
    EQUALS = auto()        # = (assignment)
    GREATER = auto()       # > (comparison)
    LESS = auto()          # < (comparison)
    EQUAL_EQUAL = auto()   # == (equality)
    NOT_EQUAL = auto()     # != (inequality)
    
    # Literals
    IDENTIFIER = auto()    # Variable name
    INTEGER = auto()       # Integer literal
    
    # Special
    EOF = auto()           # End of file
```

### Token Representation

```python
@dataclass
class Token:
    type: TokenType         # Token category
    value: Optional[str]    # String/numeric value
    line: int              # Source line (1-indexed)
    column: int            # Source column (1-indexed)
```

### Lexer Implementation

The lexer uses **character-by-character scanning** with lookahead:

```python
class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0                    # Current position
        self.line = 1                   # Track line number
        self.column = 1                 # Track column number
        self.tokens: List[Token] = []
    
    def tokenize(self) -> List[Token]:
        """Scan entire source, produce token list."""
        while self.pos < len(self.source):
            self._skip_whitespace()
            if self.pos >= len(self.source):
                break
            
            ch = self.current_char()
            
            if ch.isalpha() or ch == '_':
                self._read_identifier_or_keyword()
            elif ch.isdigit():
                self._read_number()
            elif ch in '=<>!':
                self._read_operator()
            else:
                self._error(f"Unexpected character: {ch}")
        
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens
```

### Keyword Recognition

Keywords are recognized through a lookup table:

```python
KEYWORDS = {
    'var': TokenType.VAR,
    'push': TokenType.PUSH,
    'store': TokenType.STORE,
    'add': TokenType.ADD,
    'sub': TokenType.SUB,
    'mul': TokenType.MUL,
    'div': TokenType.DIV,
    'if': TokenType.IF,
    'else': TokenType.ELSE,
    'then': TokenType.THEN,
    'end': TokenType.END,
    'print': TokenType.PRINT,
}
```

When an identifier is read, it's checked against this table to determine if it's a keyword or variable name.

### Example Tokenization

**Input:**
```
var x = 5
push 10
```

**Tokens:**
```
Token(VAR, None, 1, 1)
Token(IDENTIFIER, 'x', 1, 5)
Token(EQUALS, None, 1, 7)
Token(INTEGER, '5', 1, 9)
Token(PUSH, None, 2, 1)
Token(INTEGER, '10', 2, 6)
Token(EOF, None, 2, 9)
```

## 2. Syntax Analysis (Parser)

### Module: `src/parser.py`

The parser uses **recursive descent parsing** to build an Abstract Syntax Tree (AST) from tokens.

### Grammar (Simplified)

```
program     := statement* EOF
statement   := var_decl | push | store | arithmetic | print | if_stmt
var_decl    := VAR IDENTIFIER EQUALS INTEGER
push        := PUSH (INTEGER | IDENTIFIER)
store       := STORE IDENTIFIER
arithmetic  := ADD | SUB | MUL | DIV
print       := PRINT
if_stmt     := IF comparison THEN statement* (ELSE statement*)? END
comparison  := GREATER | LESS | EQUAL_EQUAL | NOT_EQUAL
```

### Parser Structure

```python
class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
    
    def parse(self) -> ProgramNode:
        """Parse entire program."""
        statements = []
        while not self._is_at_end():
            stmt = self._parse_statement()
            if stmt:
                statements.append(stmt)
        self._consume(TokenType.EOF, "Expected EOF")
        return ProgramNode(statements)
    
    def _parse_statement(self) -> Optional[ASTNode]:
        """Parse a single statement."""
        token = self.current_token()
        
        if token.type == TokenType.VAR:
            return self._parse_var_decl()
        elif token.type == TokenType.PUSH:
            return self._parse_push()
        elif token.type == TokenType.STORE:
            return self._parse_store()
        elif token.type == TokenType.ADD:
            return self._parse_add()
        elif token.type == TokenType.SUB:
            return self._parse_sub()
        elif token.type == TokenType.MUL:
            return self._parse_mul()
        elif token.type == TokenType.DIV:
            return self._parse_div()
        elif token.type == TokenType.PRINT:
            return self._parse_print()
        elif token.type == TokenType.IF:
            return self._parse_if()
        else:
            self._error(f"Unexpected token: {token.type}")
```

### Parsing Methods

#### Variable Declaration

```python
def _parse_var_decl(self) -> VarDeclNode:
    """Parse: var IDENTIFIER = INTEGER"""
    self._consume(TokenType.VAR, "Expected 'var'")
    
    ident_token = self._consume(TokenType.IDENTIFIER, "Expected identifier")
    identifier = ident_token.value
    
    self._consume(TokenType.EQUALS, "Expected '='")
    
    int_token = self._consume(TokenType.INTEGER, "Expected integer")
    initial_value = int(int_token.value)
    
    return VarDeclNode(
        identifier=identifier,
        initial_value=initial_value,
        line=ident_token.line,
        column=ident_token.column
    )
```

#### Push Instruction

```python
def _parse_push(self) -> PushNode:
    """Parse: push (INTEGER | IDENTIFIER)"""
    push_token = self._consume(TokenType.PUSH, "Expected 'push'")
    
    token = self.current_token()
    if token.type == TokenType.INTEGER:
        self._advance()
        return PushNode(
            value=int(token.value),
            is_identifier=False,
            line=push_token.line,
            column=push_token.column
        )
    elif token.type == TokenType.IDENTIFIER:
        self._advance()
        return PushNode(
            value=token.value,
            is_identifier=True,
            line=push_token.line,
            column=push_token.column
        )
    else:
        self._error("Expected integer or identifier after 'push'")
```

#### If-Then-Else Statement

```python
def _parse_if(self) -> IfNode:
    """Parse: if COMPARISON then STATEMENTS (else STATEMENTS)? end"""
    if_token = self._consume(TokenType.IF, "Expected 'if'")
    
    # Parse comparison operator
    comp_token = self.current_token()
    if comp_token.type == TokenType.GREATER:
        self._advance()
        comparison = ">"
    elif comp_token.type == TokenType.LESS:
        self._advance()
        comparison = "<"
    elif comp_token.type == TokenType.EQUAL_EQUAL:
        self._advance()
        comparison = "=="
    elif comp_token.type == TokenType.NOT_EQUAL:
        self._advance()
        comparison = "!="
    else:
        self._error("Expected comparison operator (>, <, ==, !=)")
    
    self._consume(TokenType.THEN, "Expected 'then'")
    
    # Parse then-branch statements
    then_stmts = []
    while (self.current_token().type not in 
           [TokenType.ELSE, TokenType.END]):
        then_stmts.append(self._parse_statement())
    
    # Parse optional else-branch
    else_stmts = []
    if self.current_token().type == TokenType.ELSE:
        self._advance()
        while self.current_token().type != TokenType.END:
            else_stmts.append(self._parse_statement())
    
    self._consume(TokenType.END, "Expected 'end'")
    
    return IfNode(
        comparison=comparison,
        then_statements=then_stmts,
        else_statements=else_stmts,
        line=if_token.line,
        column=if_token.column
    )
```

### Error Handling

Parser errors include source location and expected token information:

```
Parser error at line 3, column 5: Expected 'then' after comparison operator
```

## 3. Abstract Syntax Tree (AST)

### Module: `src/ast_nodes.py`

AST nodes are dataclasses representing program structure.

### Node Hierarchy

```python
ASTNode (abstract base)
├── ProgramNode
├── VarDeclNode
├── PushNode
├── StoreNode
├── AddNode
├── SubNode
├── MulNode
├── DivNode
├── PrintNode
└── IfNode
```

### Key Node Types

#### ProgramNode

```python
@dataclass
class ProgramNode(ASTNode):
    statements: List[ASTNode]
    line: int = 0
    column: int = 0
```

Root node containing all program statements.

#### VarDeclNode

```python
@dataclass
class VarDeclNode(ASTNode):
    identifier: str          # Variable name
    initial_value: int       # Initial value
    line: int = 0
    column: int = 0
```

Represents variable declaration with initialization.

#### PushNode

```python
@dataclass
class PushNode(ASTNode):
    value: Any              # Integer or identifier name
    is_identifier: bool     # True if value is a variable name
    line: int = 0
    column: int = 0
```

Pushes value onto stack. Can push either:
- **Literal integer**: `push 42` (is_identifier=False)
- **Variable value**: `push x` (is_identifier=True)

#### IfNode

```python
@dataclass
class IfNode(ASTNode):
    comparison: str         # ">", "<", "==", "!="
    then_statements: List[ASTNode]
    else_statements: List[ASTNode]
    line: int = 0
    column: int = 0
```

Conditional execution with comparison and branches.

## 4. Semantic Analysis

### Module: `src/semantic.py`

Semantic analysis validates the AST for correctness and safety.

### Symbol Table

The semantic analyzer maintains a symbol table of declared variables:

```python
self.symbol_table: Dict[str, dict] = {
    "x": {"type": "var", "line": 1},
    "result": {"type": "var", "line": 5},
}
```

### Stack Depth Tracking

A crucial feature is **stack depth validation**:

```python
self.stack_depth = 0  # Current stack depth

# Push increases depth
self.stack_depth += 1

# Operations that require multiple stack values
if self.stack_depth < 2:
    raise SemanticError("Stack underflow: not enough values for operation")
```

### Analysis Algorithm

```python
def analyze(self, ast: ProgramNode) -> None:
    """Analyze AST for semantic correctness."""
    self.symbol_table = {}
    self.stack_depth = 0
    
    self.visit_program(ast)
    
    # Final stack must be empty
    if self.stack_depth != 0:
        raise SemanticError(
            f"Invalid final stack depth: {self.stack_depth}. "
            f"Stack should be empty at end of program."
        )
```

### Validation Rules

#### 1. Variable Declaration

```python
def visit_var_decl(self, node: VarDeclNode) -> None:
    """Validate variable declaration."""
    # Check duplicate declaration
    if node.identifier in self.symbol_table:
        raise SemanticError(
            f"Variable '{node.identifier}' already declared at line "
            f"{self.symbol_table[node.identifier]['line']}",
            node.line, node.column
        )
    
    # Add to symbol table
    self.symbol_table[node.identifier] = {
        "type": "var",
        "line": node.line
    }
```

**Effect on stack**: No change (declaration does not modify stack)

#### 2. Push Operation

```python
def visit_push(self, node: PushNode) -> None:
    """Validate push operation."""
    if node.is_identifier:
        # Check variable is declared
        if node.value not in self.symbol_table:
            raise SemanticError(
                f"Undefined variable '{node.value}'",
                node.line, node.column
            )
    
    self.stack_depth += 1
```

**Stack effect**: Increases depth by 1

#### 3. Arithmetic Operations

```python
def visit_add(self, node: AddNode) -> None:
    """Validate addition."""
    # Check sufficient stack values
    if self.stack_depth < 2:
        raise SemanticError(
            "Stack underflow: not enough values for addition",
            node.line, node.column
        )
    
    # Pop 2, push 1
    self.stack_depth -= 1
```

**Stack effect**: Decreases depth by 1 (pops 2, pushes 1)

#### 4. Store Operation

```python
def visit_store(self, node: StoreNode) -> None:
    """Validate store operation."""
    # Check variable is declared
    if node.identifier not in self.symbol_table:
        raise SemanticError(
            f"Undefined variable '{node.identifier}'",
            node.line, node.column
        )
    
    # Check sufficient stack values
    if self.stack_depth < 1:
        raise SemanticError(
            "Stack underflow: cannot store without value on stack",
            node.line, node.column
        )
    
    self.stack_depth -= 1
```

**Stack effect**: Decreases depth by 1 (pops 1)

#### 5. Print Operation

```python
def visit_print(self, node: PrintNode) -> None:
    """Validate print operation."""
    if self.stack_depth < 1:
        raise SemanticError(
            "Stack underflow: cannot print without value on stack",
            node.line, node.column
        )
    
    self.stack_depth -= 1
```

**Stack effect**: Decreases depth by 1 (pops 1)

#### 6. If-Then-Else

```python
def visit_if(self, node: IfNode) -> None:
    """Validate if statement."""
    # Check two values for comparison
    if self.stack_depth < 2:
        raise SemanticError(
            "Stack underflow: comparison requires two values",
            node.line, node.column
        )
    
    # Pop comparison operands
    self.stack_depth -= 2
    
    # Analyze both branches from same depth
    depth_before = self.stack_depth
    
    for stmt in node.then_statements:
        self.visit(stmt)
    depth_then = self.stack_depth
    
    # Reset for else branch
    self.stack_depth = depth_before
    for stmt in node.else_statements:
        self.visit(stmt)
    depth_else = self.stack_depth
    
    # Both branches must end at same depth
    if depth_then != depth_else:
        raise SemanticError(
            f"Stack depth mismatch in if-else: then branch leaves "
            f"{depth_then} values, else branch leaves {depth_else}",
            node.line, node.column
        )
```

**Stack effect**: Complex - branches must converge

## 5. LLVM IR Code Generation

### Module: `src/emitter.py`

The emitter translates validated AST to LLVM Intermediate Representation.

### Core Concepts

The emitter maintains two key structures:

1. **Operand Stack**: Python list of LLVM SSA values
2. **Symbol Table**: Maps variable names to alloca'd pointers

```python
self.operand_stack: List[ir.Value] = []
self.symbol_table: Dict[str, ir.Value] = {}
```

### LLVM Type Definitions

```python
self.i32 = ir.IntType(32)           # 32-bit integer
self.i8_ptr = ir.IntType(8).as_pointer()  # Pointer to i8 (for printf)
```

### Main Entry Point

```python
def emit(self, ast: ProgramNode, output_path: str) -> str:
    """Emit LLVM IR from AST."""
    self._reset()
    self._create_main()
    
    for stmt in ast.statements:
        self.visit(stmt)
    
    # Return from main with 0
    self.builder.ret(ir.Constant(self.i32, 0))
    
    # Write LLVM IR to file
    ir_text = str(self.module)
    Path(output_path).write_text(ir_text)
    
    return ir_text
```

### Module and Function Setup

```python
def _create_main(self) -> None:
    """Create main function with proper LLVM structure."""
    func_type = ir.FunctionType(self.i32, [])
    main_func = self.module.add_function(func_type, name="main")
    
    entry_block = main_func.append_basic_block(name="entry")
    self.builder = ir.IRBuilder(entry_block)
```

### Stack Operations in LLVM

#### Push Implementation

**TinyStack:** `push 42`

**LLVM IR:**
```llvm
%val = <compute or load value>
; Simulate stack push by appending to operand_stack
```

**Python:**
```python
def visit_push(self, node: PushNode) -> None:
    if node.is_identifier:
        # Load variable from memory
        var_ptr = self.symbol_table[node.value]
        val = self.builder.load(var_ptr)
    else:
        # Create constant integer
        val = ir.Constant(self.i32, node.value)
    
    self.operand_stack.append(val)
```

#### Arithmetic Operations

**TinyStack:**
```
push 8
push 4
add
```

**LLVM IR:**
```llvm
; push 8
store i32 8, i32* %stack.0, align 4

; push 4
store i32 4, i32* %stack.1, align 4

; add
%lhs = load i32, i32* %stack.0, align 4     ; pop()
%rhs = load i32, i32* %stack.1, align 4     ; pop()
%result = add i32 %lhs, %rhs                ; compute
store i32 %result, i32* %stack.0, align 4   ; push()
```

**Python:**
```python
def visit_add(self, node: AddNode) -> None:
    # Pop two values
    rhs = self.operand_stack.pop()
    lhs = self.operand_stack.pop()
    
    # Compute addition
    result = self.builder.add(lhs, rhs)
    
    # Push result
    self.operand_stack.append(result)
```

#### Variable Declaration

**TinyStack:** `var x = 5`

**LLVM IR:**
```llvm
%x = alloca i32, align 4        ; Allocate storage
store i32 5, i32* %x, align 4   ; Initialize
```

**Python:**
```python
def visit_var_decl(self, node: VarDeclNode) -> None:
    # Allocate storage on stack (in memory)
    var_ptr = self.builder.alloca(self.i32)
    
    # Initialize with constant value
    init_val = ir.Constant(self.i32, node.initial_value)
    self.builder.store(init_val, var_ptr)
    
    # Store pointer in symbol table
    self.symbol_table[node.identifier] = var_ptr
```

#### Store Operation

**TinyStack:**
```
push 42
store x
```

**LLVM IR:**
```llvm
store i32 42, i32* %x, align 4
```

**Python:**
```python
def visit_store(self, node: StoreNode) -> None:
    # Pop stack value
    val = self.operand_stack.pop()
    
    # Get variable pointer from symbol table
    var_ptr = self.symbol_table[node.identifier]
    
    # Store value in variable
    self.builder.store(val, var_ptr)
```

### Print Implementation

The emitter creates a printf wrapper:

```python
def _declare_printf(self) -> None:
    """Declare printf function."""
    printf_type = ir.FunctionType(
        self.i32,
        [self.i8_ptr],
        var_arg=True
    )
    self.printf_func = self.module.declare_function(
        printf_type,
        name="printf"
    )
```

**Print statement:**

**TinyStack:** `push 42; print`

**LLVM IR:**
```llvm
%fmt = getelementptr inbounds [4 x i8], [4 x i8]* @.fmt.1, i64 0, i64 0
%result = call i32 (i8*, ...) @printf(i8* %fmt, i32 42)
```

**Python:**
```python
def visit_print(self, node: PrintNode) -> None:
    # Pop value to print
    val = self.operand_stack.pop()
    
    # Create format string "%d\n"
    fmt_str = self._create_format_string("%d\n")
    
    # Call printf
    self.builder.call(self.printf_func, [fmt_str, val])
```

### If-Then-Else Control Flow

**TinyStack:**
```
push 10
push 5
if > then
    push 1
else
    push -1
end
```

**LLVM IR:**
```llvm
%cmp = icmp sgt i32 10, 5           ; Compare: 10 > 5
br i1 %cmp, label %then, label %else

then:
  store i32 1, i32* %result
  br label %endif

else:
  store i32 -1, i32* %result
  br label %endif

endif:
  ; Merge point
```

**Python:**
```python
def visit_if(self, node: IfNode) -> None:
    # Pop comparison operands
    rhs = self.operand_stack.pop()
    lhs = self.operand_stack.pop()
    
    # Create comparison
    if node.comparison == ">":
        cond = self.builder.icmp_signed('>', lhs, rhs)
    elif node.comparison == "<":
        cond = self.builder.icmp_signed('<', lhs, rhs)
    elif node.comparison == "==":
        cond = self.builder.icmp_signed('==', lhs, rhs)
    elif node.comparison == "!=":
        cond = self.builder.icmp_signed('!=', lhs, rhs)
    
    # Create basic blocks
    then_block = self.func.append_basic_block(name="then")
    else_block = self.func.append_basic_block(name="else")
    endif_block = self.func.append_basic_block(name="endif")
    
    # Branch on condition
    self.builder.cbranch(cond, then_block, else_block)
    
    # Generate then branch
    self.builder.position_at_end(then_block)
    for stmt in node.then_statements:
        self.visit(stmt)
    self.builder.branch(endif_block)
    
    # Generate else branch
    self.builder.position_at_end(else_block)
    for stmt in node.else_statements:
        self.visit(stmt)
    self.builder.branch(endif_block)
    
    # Merge at endif
    self.builder.position_at_end(endif_block)
```

## 6. LLVM IR Optimization

### Module: `src/optimizer.py`

The optimizer applies standard LLVM passes to improve code quality.

### Optimization Sequence

```python
def optimize(self, ir_text: str, level: int = 2) -> str:
    """Apply LLVM optimization passes."""
    module = self._parse_ir(ir_text)
    
    # Create pass pipeline
    pmb = llvm.create_pass_builder(self.target_machine, opt_level=level)
    pm = llvm.create_new_module_pass_manager(pmb)
    
    # Run passes
    pm.run(module)
    
    return str(module)
```

### Key Optimization Passes

| Pass | Effect | Example |
|------|--------|---------|
| **mem2reg** | Convert alloca to SSA values | Eliminate variable alloca instructions |
| **instcombine** | Combine redundant instructions | Replace `add i32 x, 0` with `x` |
| **dce** | Remove unused values | Delete dead stores |
| **simplifycfg** | Simplify control flow | Merge empty blocks |

### Example Optimization

**Before:**
```llvm
%x = alloca i32, align 4
store i32 10, i32* %x, align 4
%loaded = load i32, i32* %x, align 4
store i32 20, i32* %x, align 4
%loaded2 = load i32, i32* %x, align 4
```

**After mem2reg:**
```llvm
; %x allocation eliminated
; Values promoted to SSA
```

## 7. Error Handling

### Three-Layer Error Architecture

```
Source Code
    ↓
[LEXER] → LexerError: Invalid token
    ↓
Token Stream
    ↓
[PARSER] → ParserError: Syntax error
    ↓
AST
    ↓
[SEMANTIC] → SemanticError: Undefined variable, stack underflow
    ↓
Validated AST
    ↓
[EMITTER] → EmitterError: Code generation failure
```

### Error Information

Each error includes:
- **Message**: Description of the error
- **Location**: Line and column in source code
- **Context**: Token or AST node causing error

**Example:**
```
Semantic error at line 5, column 3: Undefined variable 'result'
```

## 8. Variables Implementation

### Scope

TinyStack uses **global scope** - all variables are accessible from any location.

### Lifetime

Variables are:
- **Created** by declaration with initialization
- **Persistent** for the entire program duration
- **Destroyed** when the program exits

### LLVM Representation

```llvm
; Variable allocation in main function
%x = alloca i32, align 4            ; Allocate 4 bytes
store i32 10, i32* %x, align 4      ; Store initial value

; Later use
%loaded = load i32, i32* %x, align 4    ; Load value
```

After mem2reg optimization:
```llvm
; Variables promoted to SSA values
; No allocas or loads/stores
```

## 9. If-Else Implementation

### Syntax

```
if COMPARISON then
    STATEMENTS
(else
    STATEMENTS)?
end
```

### Comparison Operators

- `>`: Greater than
- `<`: Less than
- `==`: Equal to
- `!=`: Not equal to

### Stack Semantics

The comparison consumes two stack values:
1. Top of stack (right operand)
2. Next value (left operand)

```
Stack before: [lhs, rhs, ...]
Stack after:  [...]        (two values consumed for comparison)
```

### Control Flow

Each if-then-else generates up to 3 basic blocks:

1. **Entry block**: Compare operands, decide branch
2. **Then block**: Execute then-statements
3. **Else block**: Execute else-statements (if present)
4. **Exit block**: Merge point after if-else

## 10. Stack Temporaries to LLVM SSA Mapping

### Overview

TinyStack is a stack-based language. During compilation, the LLVM emitter maintains an internal operand stack that tracks temporary values throughout program execution. Stack temporaries in TinyStack are mapped **directly to LLVM SSA values**. Every arithmetic operation produces a new SSA value, and the compiler stack stores references to these SSA values until they are consumed by subsequent instructions.

### Compiler Stack Execution Model

Consider the following TinyStack program:

```
push 10
push 5
add
```

The **compiler's internal operand stack** evolves as follows during code generation:

```
Initial state:     []
After push 10:     [10]
After push 5:      [10, 5]
After add:         [15]
```

When the `add` instruction is encountered:
1. Two values are popped from the compiler stack: `5` (top) and `10` (below)
2. An LLVM arithmetic instruction is generated that computes their sum
3. The resulting SSA value is pushed back onto the compiler stack

### LLVM IR Generation

The `add` instruction generates LLVM IR:

```llvm
%add_result = add i32 10, 5
```

The generated SSA value `%add_result` represents the result of the computation and is stored in the compiler's operand stack:

```python
# After processing add
self.operand_stack = [ir.Value(...)]  # Reference to %add_result
```

This SSA value can then be used by later instructions (e.g., `print` or another arithmetic operation).

### Concept: Operand Stack as SSA Values

The operand stack is simulated using a Python list of LLVM SSA values:

```python
class LLVMEmitter:
    def __init__(self):
        self.operand_stack: List[ir.Value] = []  # Stack of LLVM SSA values
```

Each element represents an LLVM intermediate value:

```python
self.operand_stack = [
    ir.Value(...),    # Stack position 0 (bottom) - some computed value
    ir.Value(...),    # Stack position 1 - another value
    ir.Value(...),    # Stack position 2 (top) - most recently computed value
]
```

### Complete Example: Stack Temporaries Mapping

**TinyStack Program:**
```
push 8
push 4
add
print
```

**Compiler Stack Evolution:**
```
Instruction         Compiler Stack          LLVM SSA Values
─────────────────────────────────────────────────────────
(start)             []
push 8              [%val.8]                %val.8 = 8
push 4              [%val.8, %val.4]        %val.4 = 4
add                 [%result]               %result = add i32 %val.8, %val.4
print               []                      call @printf(i32 %result)
```

**Generated LLVM IR:**
```llvm
%val.8 = 8                          ; push 8
%val.4 = 4                          ; push 4
%result = add i32 %val.8, %val.4    ; add (pops %val.4 and %val.8)
call i32 (i8*, ...) @printf(i8* %fmt, i32 %result)  ; print (pops %result)
ret i32 0
```

### Mapping Details

| TinyStack Operation | Compiler Action | LLVM Generation |
|-------------------|-----------------|-----------------|
| `push value` | Append value to stack | Create constant or load, append SSA value to operand_stack |
| `add` | Pop 2, push result | Generate `add` instruction, push SSA result |
| `sub` | Pop 2, push result | Generate `sub` instruction, push SSA result |
| `mul` | Pop 2, push result | Generate `mul` instruction, push SSA result |
| `div` | Pop 2, push result | Generate `sdiv` instruction, push SSA result |
| `store x` | Pop 1 | Generate `store` instruction to variable pointer |
| `print` | Pop 1 | Generate `printf` call with popped SSA value |

### Key Insight: No Explicit Stack Memory

The TinyStack operand stack is **not** allocated as LLVM memory:

- **Stack values are SSA values**: Represented as LLVM intermediate values, not memory locations
- **No memory bandwidth**: Operations work directly on values, not through loads/stores
- **Optimizable by LLVM**: mem2reg can eliminate variable allocas; SSA values enable all optimizations
- **Pure computation tracking**: The stack models the flow of computed values through the program

### Example Optimization Impact

**Unoptimized (with allocas):**
```llvm
%stack.0 = alloca i32, align 4
%stack.1 = alloca i32, align 4
store i32 8, i32* %stack.0, align 4      ; push 8
store i32 4, i32* %stack.1, align 4      ; push 4
%lhs = load i32, i32* %stack.0, align 4  ; pop for add
%rhs = load i32, i32* %stack.1, align 4  ; pop for add
%result = add i32 %lhs, %rhs             ; add
store i32 %result, i32* %stack.0, align 4 ; push result
%val = load i32, i32* %stack.0, align 4   ; pop for print
call @printf(..., i32 %val)
```

**Optimized (SSA-based):**
```llvm
%result = add i32 8, 4
call @printf(..., i32 %result)
```

After mem2reg optimization, the compiler stack representation (using SSA values) becomes the actual optimized code with no memory references.

### Python Implementation

```python
def visit_add(self, node: AddNode) -> None:
    """Generate code for add operation."""
    # Pop two SSA values from compiler stack
    rhs_ssa_value = self.operand_stack.pop()  # Top of stack
    lhs_ssa_value = self.operand_stack.pop()  # Below it
    
    # Generate LLVM add instruction
    result_ssa_value = self.builder.add(lhs_ssa_value, rhs_ssa_value)
    
    # Push result SSA value back onto compiler stack
    self.operand_stack.append(result_ssa_value)
```

The result `result_ssa_value` is an `llvmlite.ir.Value` object that represents the LLVM SSA value and can be used by subsequent operations.

## 11. Code Generation Example

### Complete Example

**Input TinyStack:**
```
var x = 5
push x
push 3
add
print
```

**LLVM IR (Unoptimized):**
```llvm
define i32 @main() {
entry:
  %x = alloca i32, align 4
  store i32 5, i32* %x, align 4
  
  %loaded_x = load i32, i32* %x, align 4
  ; push 3
  ; add
  %result = add i32 %loaded_x, 3
  
  ; print
  %fmt = getelementptr inbounds [4 x i8], [4 x i8]* @.fmt, i64 0, i64 0
  call i32 (i8*, ...) @printf(i8* %fmt, i32 %result)
  
  ret i32 0
}

declare i32 @printf(i8*, ...)

@.fmt = private unnamed_addr constant [4 x i8] c"%d\n\00", align 1
```

**After mem2reg:**
```llvm
define i32 @main() {
entry:
  ; %x allocation eliminated
  ; Values promoted to SSA
  %result = add i32 5, 3    ; Direct constant computation
  
  %fmt = getelementptr inbounds [4 x i8], [4 x i8]* @.fmt, i64 0, i64 0
  call i32 (i8*, ...) @printf(i8* %fmt, i32 %result)
  
  ret i32 0
}
```

**Generated Assembly (x86-64):**
```asm
main:
    mov $8, %edi            ; result = 8 (constant folded!)
    lea .fmt(%rip), %rsi
    call printf
    xor %eax, %eax          ; return 0
    ret
```

## 12. Entry Points

### Compiler Driver

**`main.py`** provides command-line interface:

```bash
python src/main.py input.tiny -o output.ll --optimize --verbose
```

### Compilation Flow

```python
def compile_source(source_file: Path, output_file: Path, optimize: bool) -> CompileResult:
    # 1. Read source
    source = source_file.read_text()
    
    # 2. Lex
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    # 3. Parse
    parser = Parser(tokens)
    ast = parser.parse()
    
    # 4. Semantic analysis
    semantic = SemanticAnalyzer()
    semantic.analyze(ast)
    
    # 5. Code generation
    emitter = LLVMEmitter()
    ir = emitter.emit(ast, str(output_file))
    
    # 6. Optional optimization
    optimized_ir = None
    if optimize:
        optimizer = Optimizer()
        optimized_ir = optimizer.optimize(ir)
    
    return CompileResult(tokens, ast, ir, optimized_ir, output_file)
```

## Summary

The TinyStack compiler demonstrates:

1. **Clean modularization**: Each stage is independent
2. **Comprehensive validation**: Multi-layer error checking
3. **Efficient IR generation**: Direct LLVM construction
4. **Stack simulation**: SSA-based operand stack
5. **Extensibility**: Easy to add features

The implementation balances clarity with production quality, making it suitable for both educational study and practical use.

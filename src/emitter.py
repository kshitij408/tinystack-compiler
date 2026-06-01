"""
LLVM IR emitter for the TinyStack stack-based programming language.

This module converts an Abstract Syntax Tree (AST) into LLVM Intermediate Representation (IR)
code. It maintains an operand stack of LLVM SSA values and a symbol table of variables,
generating efficient LLVM IR for all TinyStack operations.

The emitter uses llvmlite to construct LLVM modules and uses IRBuilder for code generation.
Stack values are represented as LLVM SSA values (llvmlite.ir.Value objects).
"""

from typing import Any, Dict, List
from pathlib import Path
from llvmlite import ir
import llvmlite.binding as llvm
from ast_nodes import (
    ASTNode, ProgramNode, VarDeclNode, PushNode, StoreNode,
    AddNode, SubNode, MulNode, DivNode, PrintNode, IfNode
)


class EmitterError(Exception):
    """Raised when LLVM emission cannot safely continue."""

    def __init__(self, message: str, node: ASTNode = None):
        line = getattr(node, "line", 0) if node is not None else 0
        column = getattr(node, "column", 0) if node is not None else 0
        if line > 0:
            super().__init__(f"Emitter error at line {line}, column {column}: {message}")
        else:
            super().__init__(f"Emitter error: {message}")


# ============================================================================
# LLVM Emitter Class
# ============================================================================

class LLVMEmitter:
    """
    Emits LLVM IR code from a TinyStack AST.
    
    Walks through the AST and generates LLVM Intermediate Representation code
    that can be compiled to machine code. Maintains an operand stack containing
    LLVM SSA values and a symbol table mapping variable names to alloca'd memory.
    
    Stack Semantics:
        - All stack values are represented as llvmlite.ir.Value objects
        - Push operations append LLVM values to the stack
        - Operations pop values, compute results, and push results
        - Variables are allocated in memory using alloca instructions
    """
    
    def __init__(self, module_name: str = "TinyStack"):
        """
        Initialize the LLVM emitter.
        
        Args:
            module_name: Name for the LLVM module
        """
        self.module_name = module_name
        self.module = ir.Module(name=module_name)
        
        # Initialize LLVM target information and set host target triple
        self._initialize_target_info()
        
        self.builder = None  # Will be set when we create main()
        
        # Runtime tracking
        self.operand_stack: List[ir.Value] = []  # Stack of LLVM SSA values
        self.symbol_table: Dict[str, ir.Value] = {}  # Maps variable name -> alloca'd pointer
        self.printf_func = None  # Reference to printf for printing
        
        # Type definitions
        self.i32 = ir.IntType(32)  # 32-bit integer type
        self.i8_ptr = ir.IntType(8).as_pointer()  # i8* for string literals
        
        # Counters for unique naming
        self.block_counter = 0  # For nested if-else blocks (if_then_1, if_else_1, etc.)
        self.format_counter = 0  # For format strings (fmt_1, fmt_2, etc.)

    def _reset(self) -> None:
        """Reset mutable code-generation state for a fresh emission run."""
        self.module = ir.Module(name=self.module_name)
        self._initialize_target_info()
        self.builder = None
        self.operand_stack = []
        self.symbol_table = {}
        self.printf_func = None
        self.block_counter = 0
        self.format_counter = 0
    
    def _initialize_target_info(self) -> None:
        """
        Initialize LLVM native target information and set module's target triple.
        
        This method:
        1. Initializes the native target (required for JIT compilation and code generation)
        2. Detects the host machine's target triple
        3. Sets the LLVM module's triple to the host target
        
        The target triple specifies the architecture, vendor, and OS (e.g., 
        "x86_64-pc-linux-gnu" on Linux, "x86_64-apple-darwin" on macOS).
        This replaces the default "unknown-unknown-unknown" with the actual host target.
        """
        # Initialize native target for current platform
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()
        
        # Get the host machine's target triple
        # Example values:
        #   - x86_64-pc-linux-gnu (Linux 64-bit)
        #   - x86_64-apple-darwin (macOS 64-bit)
        #   - x86_64-w64-windows-msvc (Windows 64-bit)
        host_triple = llvm.get_default_triple()
        
        # Set the module's target triple to the host target
        # This ensures the generated IR targets the actual host architecture
        self.module.triple = host_triple
    
    def emit(self, ast: ProgramNode, output_path: str = "output/output.ll") -> str:
        """
        Emit LLVM IR from the AST and write to file.
        
        Entry point for code generation. Processes the entire AST,
        generates LLVM IR, and writes it to the specified output file.
        
        Args:
            ast: The ProgramNode (root of AST) to emit
            output_path: Path where LLVM IR file will be written
            
        Returns:
            String containing the LLVM IR code
        """
        self._reset()

        # Create main() function
        self._create_main_function()
        
        # Declare printf for printing
        self._declare_printf()
        
        # Emit all statements
        for statement in ast.statements:
            self._emit_statement(statement)
        
        # Add return 0 at end of main
        self.builder.ret(ir.Constant(self.i32, 0))
        
        # Get IR string
        ir_string = str(self.module)
        
        # Write to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ir_string)
        
        return ir_string
    
    # ========================================================================
    # Helper Methods for Module Setup
    # ========================================================================
    
    def _create_main_function(self) -> None:
        """
        Create the main() function.
        
        Defines i32 main() as the entry point and creates the entry basic block.
        """
        # Define function type: i32 main()
        func_type = ir.FunctionType(self.i32, [])
        
        # Create main function
        main_func = ir.Function(self.module, func_type, name="main")
        
        # Create entry basic block
        entry_block = main_func.append_basic_block(name="entry")
        
        # Create IR builder
        self.builder = ir.IRBuilder(entry_block)
    
    def _declare_printf(self) -> None:
        """
        Declare the printf function from C standard library.
        
        Printf is used for printing stack values. It is declared with a variadic
        signature to support formatting and multiple arguments.
        
        Signature: int printf(const char *format, ...)
        
        This allows calling printf with format strings and values:
            printf("%d\\n", value)  - prints integer followed by newline
            printf("%d %d\\n", a, b)  - prints two integers with newline
        """
        # Create printf function type: int printf(i8*, ...)
        printf_type = ir.FunctionType(self.i32, [self.i8_ptr], var_arg=True)
        
        # Declare printf
        self.printf_func = ir.Function(self.module, printf_type, name="printf")
    
    def _create_format_string(self, format_str: str) -> ir.GlobalVariable:
        """
        Create a global format string constant for printf.
        
        Converts a Python string into an LLVM global constant array that can be
        used with printf. The string is null-terminated as required by C conventions.
        
        Uses a counter to ensure each format string has a unique global variable name,
        allowing multiple print statements in a single program.
        
        Format String Examples:
            "%d\\n"     - prints a single integer with newline
            "%d %d\\n"   - prints two integers with newline
            "Value: %d\\n" - prints with label and newline
        
        Args:
            format_str: The format string (e.g., "%d\\n")
            
        Returns:
            LLVM global variable containing the null-terminated format string
        """
        # Increment counter for unique naming
        self.format_counter += 1
        fmt_name = f"fmt_{self.format_counter}"
        
        # Convert string to bytes and add null terminator
        # Example: "%d\\n" becomes b'%d\\n\\x00'
        format_bytes = format_str.encode('utf-8') + b'\x00'  # Null-terminate
        
        # Create LLVM constant array of i8 (bytes)
        # Example: [i8 37, i8 100, i8 10, i8 0] for "%d\\n"
        format_const = ir.Constant(ir.ArrayType(ir.IntType(8), len(format_bytes)),
                                  bytearray(format_bytes))
        
        # Create a global variable to store the format string
        # Using unique name (fmt_1, fmt_2, etc.) allows multiple print statements
        format_var = ir.GlobalVariable(self.module, format_const.type, name=fmt_name)
        format_var.global_constant = True  # Mark as constant
        format_var.initializer = format_const
        
        return format_var
    
    # ========================================================================
    # Statement Emission
    # ========================================================================
    
    def _emit_statement(self, node: ASTNode) -> None:
        """
        Emit LLVM IR for a statement node.
        
        Dispatches to appropriate emission method based on node type.
        
        Args:
            node: The AST node to emit
        """
        if isinstance(node, VarDeclNode):
            self._emit_var_decl(node)
        elif isinstance(node, PushNode):
            self._emit_push(node)
        elif isinstance(node, StoreNode):
            self._emit_store(node)
        elif isinstance(node, AddNode):
            self._emit_arithmetic(node, "add")
        elif isinstance(node, SubNode):
            self._emit_arithmetic(node, "sub")
        elif isinstance(node, MulNode):
            self._emit_arithmetic(node, "mul")
        elif isinstance(node, DivNode):
            self._emit_arithmetic(node, "sdiv")  # Signed division
        elif isinstance(node, PrintNode):
            self._emit_print(node)
        elif isinstance(node, IfNode):
            self._emit_if(node)
        else:
            raise EmitterError(f"Unknown AST node type: {type(node).__name__}", node)
    
    def _emit_var_decl(self, node: VarDeclNode) -> None:
        """
        Emit code for variable declaration.
        
        Allocates space on the stack for the variable and initializes it.
        
        Args:
            node: VarDeclNode to emit
        """
        identifier = node.identifier
        initial_value = node.initial_value
        
        # Allocate space for the variable on the stack
        # alloca i32 allocates a single i32-sized value
        ptr = self.builder.alloca(self.i32, name=f"{identifier}_ptr")
        
        # Store the initial value
        const_val = ir.Constant(self.i32, initial_value)
        self.builder.store(const_val, ptr)
        
        # Add to symbol table
        self.symbol_table[identifier] = ptr
    
    def _emit_push(self, node: PushNode) -> None:
        """
        Emit code for push operation.
        
        Pushes a value onto the stack. Value can be an integer literal
        or a variable's value.
        
        Args:
            node: PushNode to emit
        """
        if node.is_identifier:
            # Push a variable's value
            identifier = node.value
            if identifier not in self.symbol_table:
                raise EmitterError(f"Undefined variable '{identifier}'", node)
            ptr = self.symbol_table[identifier]
            
            # Load the value from memory
            value = self.builder.load(ptr, name=f"{identifier}_value")
            self.operand_stack.append(value)
        else:
            # Push an integer literal
            const_val = ir.Constant(self.i32, node.value)
            self.operand_stack.append(const_val)
    
    def _emit_store(self, node: StoreNode) -> None:
        """
        Emit code for store operation.
        
        Pops a value from the stack and stores it in a variable.
        
        Args:
            node: StoreNode to emit
        """
        identifier = node.identifier
        
        value = self._pop_value(node, f"store {identifier}")
        
        # Get variable pointer from symbol table
        if identifier not in self.symbol_table:
            raise EmitterError(f"Undefined variable '{identifier}'", node)
        ptr = self.symbol_table[identifier]
        
        # Store value to memory
        self.builder.store(value, ptr)
    
    def _emit_arithmetic(self, node: ASTNode, operation: str) -> None:
        """
        Emit code for arithmetic operations.
        
        Pops two values from the stack, performs the operation,
        and pushes the result.
        
        Args:
            node: The arithmetic node
            operation: The LLVM operation ("add", "sub", "mul", "sdiv")
        """
        b, a = self._pop_values(2, node, operation)
        
        # Perform operation
        if operation == "add":
            result = self.builder.add(a, b, name="add_result")
        elif operation == "sub":
            result = self.builder.sub(a, b, name="sub_result")
        elif operation == "mul":
            result = self.builder.mul(a, b, name="mul_result")
        elif operation == "sdiv":
            result = self.builder.sdiv(a, b, name="div_result")
        else:
            raise EmitterError(f"Unsupported arithmetic operation '{operation}'", node)
        
        # Push result
        self.operand_stack.append(result)
    
    def _emit_print(self, node: PrintNode) -> None:
        """
        Emit LLVM IR code for print operation.
        
        Generates code to pop a value from the operand stack and print it to stdout
        using the C standard library printf function. Supports printing:
            - Integer literals (via push)
            - Variable values (via push variable)
            - Arithmetic results (via arithmetic operations)
            - Any value on the operand stack
        
        Implementation:
            1. Pop the value to print from operand stack
            2. Create format string "%d\\n" as LLVM global constant
            3. Bitcast format string pointer to i8* (required by printf)
            4. Call printf(format_string, value)
        
        Example: Printing 42
            Input code:
                push 42
                print
            Generated LLVM IR shape:
                @fmt_1 = constant [4 x i8] c"%d\\0A\\00"
                %fmt_ptr = bitcast [4 x i8]* @fmt_1 to i8*
                call i32 (i8*, ...) @printf(i8* %fmt_ptr, i32 42)
        
        Args:
            node: PrintNode to emit (PrintNode has no fields)
        """
        # Pop the value to print from the operand stack
        # This value can come from:
        #   - push <literal>     (integer constant)
        #   - push <variable>    (loaded variable value)
        #   - arithmetic result  (result of add/sub/mul/div)
        value = self._pop_value(node, "print")
        
        # Create format string: "Result: %d\\n" (label + decimal integer + newline)
        # This is stored as a global constant in the LLVM module
        fmt_var = self._create_format_string("Result: %d\n")
        
        # Get pointer to format string
        # printf expects i8* (pointer to bytes)
        # We use bitcast to convert from [4 x i8]* to i8*
        fmt_ptr = self.builder.bitcast(fmt_var, self.i8_ptr)
        
        # Call printf with format string and value
        # printf("%d\\n", value)
        # Returns: i32 (number of characters printed, unused here)
        self.builder.call(self.printf_func, [fmt_ptr, value])
    
    def _emit_if(self, node: IfNode) -> None:
        """
        Emit LLVM IR code for if-then-else statement.
        
        TinyStack conditions compare the top two operand-stack values. The
        comparison itself consumes those two values. Both branches then start
        from the same remaining operand stack and symbol table.
        
        Control-flow shape:
            current block:
                %cond = icmp <op> i32 %a, %b
                br i1 %cond, label %then, label %else

            then:
                ... then statements ...
                br label %merge

            else:
                ... else statements ...
                br label %merge

            merge:
                ... following statements ...

        If both branches leave values on the TinyStack operand stack, the
        corresponding LLVM SSA values are joined in the merge block with phi
        nodes. This preserves stack semantics across LLVM control flow.
        
        Args:
            node: IfNode with condition, then_statements, and else_statements
        """
        # Pop the comparison operands. For a TinyStack sequence:
        #   push a
        #   push b
        #   if <op> then ...
        # the comparison must be "a <op> b", so the second pop is the left side.
        b, a = self._pop_values(2, node, f"if {node.condition}")
        stack_before_branches = list(self.operand_stack)
        symbols_before_branches = dict(self.symbol_table)
        
        # Generate comparison instruction based on condition
        # All comparisons are signed integer comparisons (icmp_signed)
        if node.condition == ">":
            cond = self.builder.icmp_signed(">", a, b, name="cmp_gt")
        elif node.condition == "<":
            cond = self.builder.icmp_signed("<", a, b, name="cmp_lt")
        elif node.condition == "==":
            cond = self.builder.icmp_signed("==", a, b, name="cmp_eq")
        elif node.condition == "!=":
            cond = self.builder.icmp_signed("!=", a, b, name="cmp_ne")
        else:
            raise EmitterError(f"Unsupported comparison operator '{node.condition}'", node)
        
        # Create three basic blocks in the current function:
        # - then_block: reached when the comparison is true.
        # - else_block: reached when the comparison is false.
        # - endif_block: merge point where control flow rejoins.
        current_func = self.builder.block.parent
        
        # Increment counter for unique block names (handles nested if statements)
        self.block_counter += 1
        block_id = self.block_counter
        
        then_block = current_func.append_basic_block(name=f"if_then_{block_id}")
        else_block = current_func.append_basic_block(name=f"if_else_{block_id}")
        endif_block = current_func.append_basic_block(name=f"if_end_{block_id}")
        
        # Terminate the current block with a conditional branch.
        # LLVM basic blocks must end in a terminator, and cbranch is the
        # terminator that chooses between the then and else successors.
        self.builder.cbranch(cond, then_block, else_block)
        
        # Emit the then branch from a clean copy of the incoming TinyStack
        # state. Statements inside the branch may push/pop stack values and may
        # store to variables, but branch-local declarations are discarded at the
        # merge by restoring symbols_before_branches below.
        self.builder.position_at_end(then_block)
        self.operand_stack = list(stack_before_branches)
        self.symbol_table = dict(symbols_before_branches)
        for stmt in node.then_statements:
            self._emit_statement(stmt)
        then_stack = list(self.operand_stack)
        then_exit_block = self.builder.block
        self.builder.branch(endif_block)
        
        # Emit the else branch from the same incoming state as the then branch.
        # An omitted else is represented by an empty else_statements list and
        # still receives an else block so the CFG remains explicit and simple.
        self.builder.position_at_end(else_block)
        self.operand_stack = list(stack_before_branches)
        self.symbol_table = dict(symbols_before_branches)
        for stmt in node.else_statements:
            self._emit_statement(stmt)
        else_stack = list(self.operand_stack)
        else_exit_block = self.builder.block
        self.builder.branch(endif_block)
        
        # Continue emission in the merge block. Any stack values produced by
        # both branches are converted to phi nodes so later arithmetic/print
        # code can use a single SSA value regardless of the branch taken.
        self.builder.position_at_end(endif_block)
        self.symbol_table = symbols_before_branches
        self.operand_stack = self._merge_branch_stacks(
            then_stack,
            else_stack,
            then_exit_block,
            else_exit_block,
            block_id,
            node,
        )

    def _pop_value(self, node: ASTNode, operation: str) -> ir.Value:
        """Pop one LLVM value from the compiler operand stack."""
        return self._pop_values(1, node, operation)[0]

    def _pop_values(self, count: int, node: ASTNode, operation: str) -> List[ir.Value]:
        """Pop values from the compiler operand stack with a useful error."""
        if len(self.operand_stack) < count:
            raise EmitterError(
                f"Stack underflow in '{operation}': requires {count} value(s), "
                f"but only {len(self.operand_stack)} available",
                node,
            )

        values = []
        for _ in range(count):
            values.append(self.operand_stack.pop())
        return values

    def _merge_branch_stacks(
        self,
        then_stack: List[ir.Value],
        else_stack: List[ir.Value],
        then_block: Any,
        else_block: Any,
        block_id: int,
        node: IfNode,
    ) -> List[ir.Value]:
        """
        Merge operand stacks from two control-flow branches.

        Semantic analysis guarantees equal stack depth. The emitter still checks
        this invariant and creates phi nodes for values that differ by branch.
        """
        if len(then_stack) != len(else_stack):
            raise EmitterError(
                "Internal stack mismatch while emitting if-statement: "
                f"then stack has {len(then_stack)} value(s), "
                f"else stack has {len(else_stack)} value(s)",
                node,
            )

        merged_stack: List[ir.Value] = []
        for index, (then_value, else_value) in enumerate(zip(then_stack, else_stack)):
            if then_value is else_value:
                merged_stack.append(then_value)
                continue

            if then_value.type != else_value.type:
                raise EmitterError(
                    "Cannot merge branch stack values with different LLVM types: "
                    f"{then_value.type} vs {else_value.type}",
                    node,
                )

            phi = self.builder.phi(then_value.type, name=f"if_phi_{block_id}_{index}")
            phi.add_incoming(then_value, then_block)
            phi.add_incoming(else_value, else_block)
            merged_stack.append(phi)

        return merged_stack

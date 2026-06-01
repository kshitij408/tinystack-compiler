"""
Semantic analyzer for the TinyStack stack-based programming language.

This module validates the Abstract Syntax Tree (AST) for semantic correctness.
It performs type checking, symbol resolution, and stack depth tracking to catch
errors before code generation.

Checks performed:
    - Variable declaration and usage validation
    - Duplicate variable declarations
    - Undefined variable references
    - Stack underflow detection for operations
    - Proper stack depth management for all operations
"""

from typing import Dict, Optional
from ast_nodes import (
    ASTNode, ProgramNode, VarDeclNode, PushNode, StoreNode,
    AddNode, SubNode, MulNode, DivNode, PrintNode, IfNode
)


# ============================================================================
# Semantic Error Handling
# ============================================================================

class SemanticError(Exception):
    """Exception raised when the semantic analyzer detects an error."""
    
    def __init__(self, message: str, line: int = 0, column: int = 0):
        """
        Initialize a semantic error with context information.
        
        Args:
            message: Description of the semantic error
            line: Line number where error occurred (optional)
            column: Column number where error occurred (optional)
        """
        self.message = message
        self.line = line
        self.column = column
        
        if line > 0 or column > 0:
            location = f" at line {line}, column {column}" if line > 0 else ""
            super().__init__(f"Semantic error{location}: {message}")
        else:
            super().__init__(f"Semantic error: {message}")


# ============================================================================
# Semantic Analyzer Class
# ============================================================================

class SemanticAnalyzer:
    """
    Semantic analyzer for TinyStack AST.
    
    Validates an Abstract Syntax Tree for semantic correctness by:
    - Maintaining a symbol table of declared variables
    - Tracking stack depth for operation validation
    - Detecting undefined variables and duplicate declarations
    - Detecting stack underflow conditions
    """
    
    def __init__(self):
        """Initialize the semantic analyzer."""
        self.symbol_table: Dict[str, dict] = {}  # Maps identifier -> {"type": "var"}
        self.stack_depth = 0  # Current depth of the stack
    
    def analyze(self, ast: ProgramNode) -> None:
        """
        Analyze the entire AST for semantic correctness.
        
        Entry point for semantic analysis. Performs all validation checks
        and raises SemanticError if any issues are detected.
        
        Args:
            ast: The ProgramNode (root of AST) to analyze
            
        Raises:
            SemanticError: If any semantic error is detected
        """
        # Reset analyzer state
        self.symbol_table = {}
        self.stack_depth = 0
        
        # Analyze the program
        self.visit_program(ast)
        
        # Verify final stack state
        if self.stack_depth != 0:
            node = ast.statements[-1] if ast.statements else ast
            self.error(
                f"Invalid final stack depth: {self.stack_depth}. "
                f"Stack should be empty at end of program.",
                node,
            )

    def error(self, message: str, node: Optional[ASTNode] = None) -> None:
        """
        Raise a semantic error, using source location metadata when available.

        Args:
            message: Human-readable error description.
            node: AST node associated with the error.

        Raises:
            SemanticError: Always raises.
        """
        line = getattr(node, "line", 0) if node is not None else 0
        column = getattr(node, "column", 0) if node is not None else 0
        raise SemanticError(message, line, column)
    
    # ========================================================================
    # Node Visitor Methods
    # ========================================================================
    
    def visit_program(self, node: ProgramNode) -> None:
        """
        Visit a ProgramNode and analyze all statements.
        
        Args:
            node: The ProgramNode to visit
        """
        for statement in node.statements:
            self.visit(statement)
    
    def visit(self, node: ASTNode) -> None:
        """
        Dispatch to the appropriate visitor method based on node type.
        
        Args:
            node: The AST node to visit
            
        Raises:
            SemanticError: If node type is unrecognized
        """
        if isinstance(node, VarDeclNode):
            self.visit_var_decl(node)
        elif isinstance(node, PushNode):
            self.visit_push(node)
        elif isinstance(node, StoreNode):
            self.visit_store(node)
        elif isinstance(node, AddNode):
            self.visit_arithmetic(node, "add")
        elif isinstance(node, SubNode):
            self.visit_arithmetic(node, "sub")
        elif isinstance(node, MulNode):
            self.visit_arithmetic(node, "mul")
        elif isinstance(node, DivNode):
            self.visit_arithmetic(node, "div")
        elif isinstance(node, PrintNode):
            self.visit_print(node)
        elif isinstance(node, IfNode):
            self.visit_if(node)
        else:
            self.error(f"Unknown AST node type: {type(node).__name__}", node)
    
    def visit_var_decl(self, node: VarDeclNode) -> None:
        """
        Visit a VarDeclNode and check for duplicate declarations.
        
        A variable declaration introduces a new variable into the symbol table.
        
        Args:
            node: The VarDeclNode to visit
            
        Raises:
            SemanticError: If variable is already declared
        """
        identifier = node.identifier
        
        # Check for duplicate declaration
        if identifier in self.symbol_table:
            self.error(
                f"Duplicate variable declaration: '{identifier}' "
                f"is already declared",
                node,
            )
        
        # Add variable to symbol table
        self.symbol_table[identifier] = {"type": "var"}
    
    def visit_push(self, node: PushNode) -> None:
        """
        Visit a PushNode and validate the operation.
        
        Push adds one value to the stack. If pushing a variable,
        verify the variable exists.
        
        Args:
            node: The PushNode to visit
            
        Raises:
            SemanticError: If pushing an undefined variable
        """
        if node.is_identifier:
            # Pushing a variable - verify it's declared
            identifier = node.value
            if identifier not in self.symbol_table:
                self.error(
                    f"Undefined variable: '{identifier}' used in 'push' "
                    f"but was never declared",
                    node,
                )
        
        # Push increases stack depth by 1
        self.stack_depth += 1
    
    def visit_store(self, node: StoreNode) -> None:
        """
        Visit a StoreNode and validate the operation.
        
        Store pops one value from the stack and stores it in a variable.
        
        Args:
            node: The StoreNode to visit
            
        Raises:
            SemanticError: If storing to undefined variable or stack underflow
        """
        identifier = node.identifier
        
        # Check if variable is declared
        if identifier not in self.symbol_table:
            self.error(
                f"Undefined variable: '{identifier}' used in 'store' "
                f"but was never declared",
                node,
            )
        
        # Check for stack underflow
        if self.stack_depth < 1:
            self.error(
                f"Stack underflow in 'store {identifier}': "
                f"operation requires at least 1 value on stack, "
                f"but stack is empty",
                node,
            )
        
        # Store pops one value from stack
        self.stack_depth -= 1
    
    def visit_arithmetic(self, node: ASTNode, operation: str) -> None:
        """
        Visit an arithmetic operation node and validate the operation.
        
        Arithmetic operations (add, sub, mul, div) pop two values from the stack
        and push one result. They require at least 2 values on the stack.
        
        Args:
            node: The arithmetic node (AddNode, SubNode, etc.)
            operation: The operation name ("add", "sub", "mul", "div")
            
        Raises:
            SemanticError: If stack underflow occurs
        """
        # Check for stack underflow
        if self.stack_depth < 2:
            self.error(
                f"Stack underflow in '{operation}': "
                f"operation requires at least 2 values on stack, "
                f"but only {self.stack_depth} available",
                node,
            )
        
        # Arithmetic operations pop 2 and push 1 (net -1)
        self.stack_depth -= 1
    
    def visit_print(self, node: PrintNode) -> None:
        """
        Visit a PrintNode and validate the operation.
        
        Print pops one value from the stack and outputs it.
        
        Args:
            node: The PrintNode to visit
            
        Raises:
            SemanticError: If stack underflow occurs
        """
        # Check for stack underflow
        if self.stack_depth < 1:
            self.error(
                f"Stack underflow in 'print': "
                f"operation requires at least 1 value on stack, "
                f"but stack is empty",
                node,
            )
        
        # Print pops one value from stack
        self.stack_depth -= 1
    
    def visit_if(self, node: IfNode) -> None:
        """
        Visit an IfNode and validate the conditional branch.
        
        An if-statement requires a condition (comparison operator) and two values
        on the stack. Both branches are analyzed for consistency.
        
        Args:
            node: The IfNode to visit
            
        Raises:
            SemanticError: If stack state is inconsistent
        """
        # Check for stack underflow (need 2 values for comparison)
        if self.stack_depth < 2:
            self.error(
                f"Stack underflow in 'if {node.condition}': "
                f"condition requires at least 2 values on stack "
                f"for comparison, but only {self.stack_depth} available",
                node,
            )
        
        # Comparison operation pops 2 values and evaluates condition
        # (doesn't push anything; condition determines which branch to take)
        self.stack_depth -= 2
        
        # Save stack state before analyzing branches
        stack_before_branches = self.stack_depth
        symbols_before_branches = dict(self.symbol_table)
        
        # Analyze each branch from the same incoming state. Variables declared
        # inside a branch are branch-local and are not visible after the merge.
        self.symbol_table = dict(symbols_before_branches)
        self.stack_depth = stack_before_branches
        for stmt in node.then_statements:
            self.visit(stmt)
        then_final_depth = self.stack_depth
        
        # Reset state for else-branch analysis
        self.symbol_table = dict(symbols_before_branches)
        self.stack_depth = stack_before_branches
        
        # Analyze else-branch (if present)
        if node.else_statements:
            for stmt in node.else_statements:
                self.visit(stmt)
            else_final_depth = self.stack_depth
        else:
            else_final_depth = stack_before_branches
        
        # Both branches must end with same stack depth
        if then_final_depth != else_final_depth:
            self.error(
                f"Inconsistent stack depth in if-statement: "
                f"then-branch ends with stack depth {then_final_depth}, "
                f"else-branch ends with stack depth {else_final_depth}. "
                f"Both branches must maintain same stack depth.",
                node,
            )
        
        # Merge only the stack depth. Branch-local declarations are discarded.
        self.symbol_table = symbols_before_branches
        self.stack_depth = then_final_depth

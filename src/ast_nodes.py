"""
Abstract Syntax Tree (AST) node classes for the TinyStack compiler.

This module defines all AST node types used to represent TinyStack programs
in an intermediate tree format. Nodes are dataclasses with optional source
locations so later compiler stages can report useful diagnostics.

Node Types:
    - ProgramNode: Root node containing all statements
    - VarDeclNode: Variable declaration (var x = value)
    - PushNode: Push value onto the stack
    - StoreNode: Store stack value in variable
    - ArithmeticNodes: AddNode, SubNode, MulNode, DivNode
    - PrintNode: Print value to output
    - IfNode: Conditional execution (if-then-else)
"""

from abc import ABC
from dataclasses import dataclass
from typing import List, Any


# ============================================================================
# Base AST Node Class
# ============================================================================

class ASTNode(ABC):
    """
    Abstract base class for all AST nodes.
    
    All nodes in the AST inherit from this class, providing a common
    interface for tree traversal and code generation.
    """
    
    def __repr__(self) -> str:
        """Return string representation of the node."""
        raise NotImplementedError("Subclasses must implement __repr__")


# ============================================================================
# Program Structure Nodes
# ============================================================================

@dataclass
class ProgramNode(ASTNode):
    """
    Root node representing an entire TinyStack program.
    
    Attributes:
        statements: List of statement nodes that make up the program
        line: Source line where the program begins, if known
        column: Source column where the program begins, if known
    """
    statements: List[ASTNode]
    line: int = 0
    column: int = 0
    
    def __repr__(self) -> str:
        """Return readable representation of the program."""
        num_stmts = len(self.statements)
        return f"ProgramNode({num_stmts} statements)"


# ============================================================================
# Variable Declaration and Storage Nodes
# ============================================================================

@dataclass
class VarDeclNode(ASTNode):
    """
    Variable declaration node.
    
    Represents: var identifier = initial_value
    
    Attributes:
        identifier: Name of the variable being declared
        initial_value: Integer initial value for the variable
        line: Source line where the statement begins
        column: Source column where the statement begins
    """
    identifier: str
    initial_value: int
    line: int = 0
    column: int = 0
    
    def __repr__(self) -> str:
        """Return readable representation of variable declaration."""
        return f"VarDeclNode(var {self.identifier} = {self.initial_value})"


@dataclass
class StoreNode(ASTNode):
    """
    Variable storage node.
    
    Represents: store identifier
    
    Pops the top value from the stack and stores it in the given variable.
    
    Attributes:
        identifier: Name of the variable to store value in
        line: Source line where the statement begins
        column: Source column where the statement begins
    """
    identifier: str
    line: int = 0
    column: int = 0
    
    def __repr__(self) -> str:
        """Return readable representation of store operation."""
        return f"StoreNode(store {self.identifier})"


# ============================================================================
# Stack Operation Nodes
# ============================================================================

@dataclass
class PushNode(ASTNode):
    """
    Push value onto stack node.
    
    Represents: push value
    
    Can push either an integer literal or a variable's value onto the stack.
    The 'is_identifier' flag determines the interpretation.
    
    Attributes:
        value: Either an integer or identifier name (string)
        is_identifier: True if value is a variable name, False if literal integer
        line: Source line where the statement begins
        column: Source column where the statement begins
    """
    value: Any
    is_identifier: bool = False
    line: int = 0
    column: int = 0
    
    def __repr__(self) -> str:
        """Return readable representation of push operation."""
        if self.is_identifier:
            return f"PushNode(push {self.value} [variable])"
        return f"PushNode(push {self.value})"


# ============================================================================
# Arithmetic Operation Nodes
# ============================================================================

@dataclass
class AddNode(ASTNode):
    """
    Addition operation node.
    
    Represents: add
    
    Pops two values from the stack, adds them, and pushes the result.
    Stack behavior: [b, a, ...] -> [a + b, ...]
    """
    line: int = 0
    column: int = 0
    
    def __repr__(self) -> str:
        """Return readable representation of addition."""
        return "AddNode(add)"


@dataclass
class SubNode(ASTNode):
    """
    Subtraction operation node.
    
    Represents: sub
    
    Pops two values from the stack, subtracts them, and pushes the result.
    Stack behavior: [b, a, ...] -> [a - b, ...]
    """
    line: int = 0
    column: int = 0
    
    def __repr__(self) -> str:
        """Return readable representation of subtraction."""
        return "SubNode(sub)"


@dataclass
class MulNode(ASTNode):
    """
    Multiplication operation node.
    
    Represents: mul
    
    Pops two values from the stack, multiplies them, and pushes the result.
    Stack behavior: [b, a, ...] -> [a * b, ...]
    """
    line: int = 0
    column: int = 0
    
    def __repr__(self) -> str:
        """Return readable representation of multiplication."""
        return "MulNode(mul)"


@dataclass
class DivNode(ASTNode):
    """
    Division operation node.
    
    Represents: div
    
    Pops two values from the stack, divides them, and pushes the result.
    Stack behavior: [b, a, ...] -> [a / b, ...]
    
    Note: Integer division is used.
    """
    line: int = 0
    column: int = 0
    
    def __repr__(self) -> str:
        """Return readable representation of division."""
        return "DivNode(div)"


# ============================================================================
# Output Operation Nodes
# ============================================================================

@dataclass
class PrintNode(ASTNode):
    """
    Print value node.
    
    Represents: print
    
    Pops the top value from the stack and prints it to output.
    Stack behavior: [value, ...] -> [...]
    """
    line: int = 0
    column: int = 0
    
    def __repr__(self) -> str:
        """Return readable representation of print operation."""
        return "PrintNode(print)"


# ============================================================================
# Control Flow Nodes
# ============================================================================

@dataclass
class IfNode(ASTNode):
    """
    Conditional execution node.
    
    Represents: if condition then ... else ... end
    
    Evaluates a condition and executes the appropriate branch.
    The condition is specified by a comparison operator on top two stack values.
    
    Attributes:
        condition: The comparison operator (>, <, ==, !=)
        then_statements: List of nodes to execute if condition is true
        else_statements: List of nodes to execute if condition is false (may be empty)
        line: Source line where the statement begins
        column: Source column where the statement begins
    """
    condition: str  # One of: >, <, ==, !=
    then_statements: List[ASTNode]
    else_statements: List[ASTNode]
    line: int = 0
    column: int = 0
    
    def __repr__(self) -> str:
        """Return readable representation of if-then-else node."""
        then_count = len(self.then_statements)
        else_count = len(self.else_statements)
        
        if else_count > 0:
            return (f"IfNode(if {self.condition} then {then_count} stmts "
                   f"else {else_count} stmts)")
        return f"IfNode(if {self.condition} then {then_count} stmts)"

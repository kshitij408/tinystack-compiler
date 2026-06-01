"""
Recursive descent parser for the TinyStack stack-based programming language.

This module implements a parser that consumes tokens from the lexer and produces
an Abstract Syntax Tree (AST) for code generation. It uses recursive descent
parsing, a top-down parsing technique that is clean and easy to understand.

Grammar (simplified):
    program := statement* EOF
    statement := var_decl | push | store | arithmetic | print | if_stmt
    var_decl := VAR IDENTIFIER EQUALS INTEGER
    push := PUSH (INTEGER | IDENTIFIER)
    store := STORE IDENTIFIER
    arithmetic := ADD | SUB | MUL | DIV
    print := PRINT
    if_stmt := IF comparison THEN statement* (ELSE statement*)? END
"""

from typing import List, Optional
from lexer import Token, TokenType
from ast_nodes import (
    ASTNode, ProgramNode, VarDeclNode, PushNode, StoreNode,
    AddNode, SubNode, MulNode, DivNode, PrintNode, IfNode
)


# ============================================================================
# Parser Error Handling
# ============================================================================

class ParserError(Exception):
    """Exception raised when the parser encounters a syntax error."""
    
    def __init__(self, message: str, token: Optional[Token] = None):
        """
        Initialize a parser error with context information.
        
        Args:
            message: Description of the error
            token: The token where error occurred (provides line/column)
        """
        self.message = message
        self.token = token
        
        if token:
            location = f" at line {token.line}, column {token.column}"
            super().__init__(f"Parser error{location}: {message}")
        else:
            super().__init__(f"Parser error: {message}")


# ============================================================================
# Parser Class
# ============================================================================

class Parser:
    """
    Recursive descent parser for TinyStack source code.
    
    Consumes a stream of tokens and builds an Abstract Syntax Tree (AST)
    representing the program structure. Uses recursive descent parsing
    with clean separation of concerns for each language construct.
    """
    
    def __init__(self, tokens: List[Token]):
        """
        Initialize the parser with a token stream.
        
        Args:
            tokens: List of Token objects from the lexer
        """
        self.tokens = tokens
        self.pos = 0  # Current position in token stream
    
    # ========================================================================
    # Token Management Helper Methods
    # ========================================================================
    
    def current_token(self) -> Token:
        """
        Get the current token without consuming it.
        
        Returns:
            The current Token object
        """
        if self.pos >= len(self.tokens):
            # Return EOF token if we've gone past the end
            return self.tokens[-1]
        return self.tokens[self.pos]
    
    def peek_token(self, offset: int = 1) -> Optional[Token]:
        """
        Look ahead at a token without consuming.
        
        Args:
            offset: How many tokens ahead to look (default: 1)
            
        Returns:
            The lookahead token, or None if past end of stream
        """
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return None
        return self.tokens[pos]
    
    def advance(self) -> Token:
        """
        Consume and return the current token.
        
        Returns:
            The token that was consumed
        """
        token = self.current_token()
        self.pos += 1
        return token
    
    def expect(self, token_type: TokenType) -> Token:
        """
        Consume a token of a specific type or raise an error.
        
        This method is used when we know exactly what token type
        should come next. If it doesn't match, raises ParserError.
        
        Args:
            token_type: The expected TokenType
            
        Returns:
            The consumed token
            
        Raises:
            ParserError: If current token doesn't match expected type
        """
        token = self.current_token()
        
        if token.type != token_type:
            raise ParserError(
                f"Expected {token_type.name} but got {token.type.name}",
                token
            )
        
        return self.advance()
    
    def match(self, *token_types: TokenType) -> bool:
        """
        Check if current token matches any of the given types.
        
        Args:
            token_types: One or more TokenType values to check
            
        Returns:
            True if current token matches any given type, False otherwise
        """
        return self.current_token().type in token_types
    
    # ========================================================================
    # Main Parse Entry Point
    # ========================================================================
    
    def parse(self) -> ProgramNode:
        """
        Parse the entire program.
        
        Entry point for parsing. Reads all statements until EOF and
        returns the root ProgramNode.
        
        Returns:
            ProgramNode representing the complete program
            
        Raises:
            ParserError: If any syntax error is encountered
        """
        statements: List[ASTNode] = []
        
        # Parse statements until we reach EOF
        while self.current_token().type != TokenType.EOF:
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        
        # Consume the EOF token
        self.expect(TokenType.EOF)
        
        if statements:
            return ProgramNode(
                statements,
                line=getattr(statements[0], "line", 0),
                column=getattr(statements[0], "column", 0),
            )
        return ProgramNode(statements)
    
    # ========================================================================
    # Statement Parsing Methods
    # ========================================================================
    
    def parse_statement(self) -> Optional[ASTNode]:
        """
        Parse a single statement.
        
        Dispatches to appropriate parsing method based on current token type.
        Handles all statement types: declarations, operations, and control flow.
        
        Returns:
            An AST node representing the statement, or None if skipped
            
        Raises:
            ParserError: If statement syntax is invalid
        """
        token = self.current_token()
        
        # Variable declaration: var x = 5
        if self.match(TokenType.VAR):
            return self.parse_var_declaration()
        
        # Push: push 5 or push x
        elif self.match(TokenType.PUSH):
            return self.parse_push()
        
        # Store: store x
        elif self.match(TokenType.STORE):
            return self.parse_store()
        
        # Arithmetic operations: add, sub, mul, div
        elif self.match(TokenType.ADD):
            token = self.advance()
            return AddNode(line=token.line, column=token.column)
        
        elif self.match(TokenType.SUB):
            token = self.advance()
            return SubNode(line=token.line, column=token.column)
        
        elif self.match(TokenType.MUL):
            token = self.advance()
            return MulNode(line=token.line, column=token.column)
        
        elif self.match(TokenType.DIV):
            token = self.advance()
            return DivNode(line=token.line, column=token.column)
        
        # Print: print
        elif self.match(TokenType.PRINT):
            token = self.advance()
            return PrintNode(line=token.line, column=token.column)
        
        # Control flow: if-then-else-end
        elif self.match(TokenType.IF):
            return self.parse_if_statement()
        
        # Unknown statement
        else:
            raise ParserError(
                f"Unexpected token {token.type.name}",
                token
            )
    
    def parse_var_declaration(self) -> VarDeclNode:
        """
        Parse a variable declaration statement.
        
        Syntax: var identifier = integer
        Example: var x = 10
        
        Returns:
            VarDeclNode representing the variable declaration
            
        Raises:
            ParserError: If declaration syntax is invalid
        """
        var_token = self.expect(TokenType.VAR)
        
        # Get variable name
        identifier_token = self.expect(TokenType.IDENTIFIER)
        identifier = identifier_token.value
        
        # Expect '='
        self.expect(TokenType.EQUALS)
        
        # Get initial value
        value_token = self.expect(TokenType.INTEGER)
        initial_value = int(value_token.value)
        
        return VarDeclNode(
            identifier,
            initial_value,
            line=var_token.line,
            column=var_token.column,
        )
    
    def parse_push(self) -> PushNode:
        """
        Parse a push statement.
        
        Syntax: push (integer | identifier)
        Examples:
            push 5      # Push literal integer
            push x      # Push variable value
        
        Returns:
            PushNode representing the push operation
            
        Raises:
            ParserError: If push syntax is invalid
        """
        push_token = self.expect(TokenType.PUSH)
        
        token = self.current_token()
        
        # Push integer literal
        if self.match(TokenType.INTEGER):
            value_token = self.advance()
            return PushNode(
                int(value_token.value),
                is_identifier=False,
                line=push_token.line,
                column=push_token.column,
            )
        
        # Push variable
        elif self.match(TokenType.IDENTIFIER):
            ident_token = self.advance()
            return PushNode(
                ident_token.value,
                is_identifier=True,
                line=push_token.line,
                column=push_token.column,
            )
        
        # Invalid push argument
        else:
            raise ParserError(
                "Expected integer or identifier after 'push'",
                token
            )
    
    def parse_store(self) -> StoreNode:
        """
        Parse a store statement.
        
        Syntax: store identifier
        Example: store x
        
        Pops the top value from the stack and stores it in the variable.
        
        Returns:
            StoreNode representing the store operation
            
        Raises:
            ParserError: If store syntax is invalid
        """
        store_token = self.expect(TokenType.STORE)
        
        identifier_token = self.expect(TokenType.IDENTIFIER)
        identifier = identifier_token.value
        
        return StoreNode(identifier, line=store_token.line, column=store_token.column)
    
    def parse_if_statement(self) -> IfNode:
        """
        Parse an if-then-else statement.
        
        Syntax:
            if CONDITION then STATEMENTS else STATEMENTS end
            if CONDITION then STATEMENTS end
        
        The CONDITION must be a comparison operator: >, <, ==, !=
        
        Example:
            if > then
                push 1
            else
                push 0
            end
        
        Returns:
            IfNode representing the conditional
            
        Raises:
            ParserError: If if-statement syntax is invalid
        """
        if_token = self.expect(TokenType.IF)
        
        # Parse condition (comparison operator)
        condition_token = self.current_token()
        
        if self.match(TokenType.GREATER):
            condition = ">"
            self.advance()
        elif self.match(TokenType.LESS):
            condition = "<"
            self.advance()
        elif self.match(TokenType.EQUAL_EQUAL):
            condition = "=="
            self.advance()
        elif self.match(TokenType.NOT_EQUAL):
            condition = "!="
            self.advance()
        else:
            raise ParserError(
                "Expected comparison operator (>, <, ==, !=)",
                condition_token
            )
        
        # Expect 'then'
        self.expect(TokenType.THEN)
        
        # Parse then-branch statements
        then_statements: List[ASTNode] = []
        while not self.match(TokenType.ELSE, TokenType.END):
            stmt = self.parse_statement()
            if stmt:
                then_statements.append(stmt)
        
        # Parse optional else-branch
        else_statements: List[ASTNode] = []
        if self.match(TokenType.ELSE):
            self.advance()
            
            while not self.match(TokenType.END):
                stmt = self.parse_statement()
                if stmt:
                    else_statements.append(stmt)
        
        # Expect 'end'
        self.expect(TokenType.END)
        
        return IfNode(
            condition,
            then_statements,
            else_statements,
            line=if_token.line,
            column=if_token.column,
        )

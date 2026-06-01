"""
Clean, production-quality lexer for the TinyStack stack-based programming language.

This module provides tokenization of TinyStack source code into a stream of tokens
for use by the parser. It supports keywords, identifiers, integers, operators,
and proper error handling with line/column tracking.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional


class TokenType(Enum):
    """Enumeration of all token types in the TinyStack language."""
    
    # Keywords
    VAR = auto()
    PUSH = auto()
    STORE = auto()
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    IF = auto()
    ELSE = auto()
    THEN = auto()
    END = auto()
    PRINT = auto()
    
    # Literals
    IDENTIFIER = auto()
    INTEGER = auto()
    
    # Operators
    EQUALS = auto()           # =
    GREATER = auto()          # >
    LESS = auto()             # <
    EQUAL_EQUAL = auto()       # ==
    NOT_EQUAL = auto()         # !=
    
    # Special
    EOF = auto()


@dataclass
class Token:
    """
    Represents a single token in the source code.
    
    Attributes:
        type: The TokenType of this token
        value: The string/numeric value of the token (or None for keywords/operators)
        line: Line number where token appears (1-indexed)
        column: Column number where token starts (1-indexed)
    """
    type: TokenType
    value: Optional[str]
    line: int
    column: int
    
    def __repr__(self) -> str:
        """Return readable string representation of the token."""
        return f"Token({self.type.name}, {self.value!r}, {self.line}, {self.column})"


class LexerError(Exception):
    """Exception raised when the lexer encounters an invalid token."""
    
    def __init__(self, message: str, line: int, column: int):
        """
        Initialize a lexer error with context information.
        
        Args:
            message: Description of the error
            line: Line number where error occurred
            column: Column number where error occurred
        """
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Lexer error at line {line}, column {column}: {message}")


class Lexer:
    """
    Tokenizes TinyStack source code into a list of tokens.
    
    The lexer reads source code character-by-character and produces tokens
    for keywords, identifiers, integers, operators, and special symbols.
    It tracks position information (line/column) for error reporting.
    """
    
    # Keywords mapping
    KEYWORDS = {
        "var": TokenType.VAR,
        "push": TokenType.PUSH,
        "store": TokenType.STORE,
        "add": TokenType.ADD,
        "sub": TokenType.SUB,
        "mul": TokenType.MUL,
        "div": TokenType.DIV,
        "if": TokenType.IF,
        "else": TokenType.ELSE,
        "then": TokenType.THEN,
        "end": TokenType.END,
        "print": TokenType.PRINT,
    }
    
    def __init__(self, source: str):
        """
        Initialize the lexer with source code.
        
        Args:
            source: The TinyStack source code to tokenize
        """
        self.source = source
        self.pos = 0  # Current position in source
        self.line = 1  # Current line number (1-indexed)
        self.column = 1  # Current column number (1-indexed)
        self.tokens: List[Token] = []
    
    def error(self, message: str) -> None:
        """
        Raise a lexer error with the current position context.
        
        Args:
            message: Description of the error
            
        Raises:
            LexerError: Always raises with the provided message and current position
        """
        raise LexerError(message, self.line, self.column)
    
    def current_char(self) -> Optional[str]:
        """Get the current character without advancing."""
        if self.pos >= len(self.source):
            return None
        return self.source[self.pos]
    
    def peek_char(self, offset: int = 1) -> Optional[str]:
        """Get the character at current position + offset without advancing."""
        pos = self.pos + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]
    
    def advance(self) -> Optional[str]:
        """
        Consume and return the current character, updating position tracking.
        
        Returns:
            The character that was consumed, or None if at end of source
        """
        char = self.current_char()
        if char is not None:
            self.pos += 1
            if char == "\n":
                self.line += 1
                self.column = 1
            else:
                self.column += 1
        return char
    
    def skip_whitespace(self) -> None:
        """Skip whitespace characters except newlines (which are significant)."""
        while self.current_char() is not None and self.current_char() in " \t\r":
            self.advance()
    
    def skip_comment(self) -> None:
        """Skip a comment that starts with # and continues to end of line."""
        # Skip the '#'
        self.advance()
        # Skip until end of line
        while self.current_char() is not None and self.current_char() != "\n":
            self.advance()
    
    def read_integer(self) -> Token:
        """
        Read an integer literal from the source.
        
        Returns:
            A Token of type INTEGER
            
        Raises:
            LexerError: If integer cannot be properly parsed
        """
        start_line = self.line
        start_column = self.column
        num_str = ""
        
        while self.current_char() is not None and self.current_char().isdigit():
            num_str += self.current_char()
            self.advance()
        
        return Token(TokenType.INTEGER, num_str, start_line, start_column)
    
    def read_identifier(self) -> Token:
        """
        Read an identifier or keyword from the source.
        
        An identifier/keyword starts with a letter or underscore and continues
        with letters, digits, or underscores.
        
        Returns:
            A Token of type IDENTIFIER or the appropriate keyword token type
        """
        start_line = self.line
        start_column = self.column
        ident = ""
        
        while (
            self.current_char() is not None
            and (self.current_char().isalnum() or self.current_char() == "_")
        ):
            ident += self.current_char()
            self.advance()
        
        # Check if it's a keyword
        token_type = self.KEYWORDS.get(ident, TokenType.IDENTIFIER)
        
        return Token(token_type, ident if token_type == TokenType.IDENTIFIER else None,
                    start_line, start_column)
    
    def tokenize(self) -> List[Token]:
        """
        Tokenize the entire source code.
        
        Scans through the source code and produces a list of tokens, tracking
        line and column information for each token. Handles whitespace, comments,
        and various token types (keywords, identifiers, integers, operators).
        
        Returns:
            A list of Token objects representing the source code, ending with EOF
            
        Raises:
            LexerError: If an invalid character or malformed token is encountered
        """
        self.tokens = []
        
        while self.current_char() is not None:
            self.skip_whitespace()
            
            char = self.current_char()
            if char is None:
                break
            
            # Comments
            if char == "#":
                self.skip_comment()
                continue
            
            # Newline (significant in some contexts)
            if char == "\n":
                self.advance()
                continue
            
            # Integers
            if char.isdigit():
                self.tokens.append(self.read_integer())
                continue
            
            # Identifiers and keywords
            if char.isalpha() or char == "_":
                self.tokens.append(self.read_identifier())
                continue
            
            # Operators
            start_line = self.line
            start_column = self.column
            
            if char == "=":
                self.advance()
                if self.current_char() == "=":
                    self.advance()
                    self.tokens.append(Token(TokenType.EQUAL_EQUAL, None, start_line, start_column))
                else:
                    self.tokens.append(Token(TokenType.EQUALS, None, start_line, start_column))
                continue
            
            if char == "!":
                self.advance()
                if self.current_char() == "=":
                    self.advance()
                    self.tokens.append(Token(TokenType.NOT_EQUAL, None, start_line, start_column))
                else:
                    self.error(f"Unexpected character '!'")
                continue
            
            if char == ">":
                self.advance()
                self.tokens.append(Token(TokenType.GREATER, None, start_line, start_column))
                continue
            
            if char == "<":
                self.advance()
                self.tokens.append(Token(TokenType.LESS, None, start_line, start_column))
                continue
            
            # Unknown character
            self.error(f"Unexpected character '{char}'")
        
        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens

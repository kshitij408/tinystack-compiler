#!/usr/bin/env python
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer
from emitter import LLVMEmitter
from pathlib import Path

# Test program: various print operations
sample_code = """
var x = 42
var y = 10
push x
print
push y
print
push 100
push 50
add
print
push x
push 5
sub
print
"""

print("=" * 70)
print("Testing PrintNode - Multiple Print Statements")
print("=" * 70)

print("\n[Program Source Code]")
print("-" * 70)
for line_num, line in enumerate(sample_code.strip().split('\n'), 1):
    print(f"  {line_num:2}: {line}")
print("-" * 70)

try:
    print("\n[Compiling]")
    lexer = Lexer(sample_code)
    tokens = lexer.tokenize()
    print(f"✓ Lexical analysis: {len(tokens)} tokens")
    
    parser = Parser(tokens)
    ast = parser.parse()
    print(f"✓ Syntax analysis: {len(ast.statements)} statements")
    
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    print(f"✓ Semantic analysis: validation passed")
    
    print("\n[LLVM Code Generation]")
    output_file = Path('.').parent / "output" / "output_print.ll"
    emitter = LLVMEmitter(module_name="TinyStack_Print")
    ir_code = emitter.emit(ast, output_path=str(output_file))
    print(f"✓ Generated LLVM IR with printf calls")
    
    print("\n[Generated LLVM IR]")
    print("-" * 70)
    print(ir_code)
    print("-" * 70)
    
    print(f"\n✓ PrintNode test completed successfully!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

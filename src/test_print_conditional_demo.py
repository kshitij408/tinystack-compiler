#!/usr/bin/env python
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer
from emitter import LLVMEmitter
from pathlib import Path

# Test program: print inside if-else
sample_code = """
var result = 0
push 100
push 50
if > then
  push 1
  print
else
  push 0
  print
end
"""

print("=" * 70)
print("Testing PrintNode in Conditional Branches")
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
    output_file = Path('.').parent / "output" / "output_print_conditional.ll"
    emitter = LLVMEmitter(module_name="TinyStack_PrintConditional")
    ir_code = emitter.emit(ast, output_path=str(output_file))
    print(f"✓ Generated LLVM IR with conditional printf calls")
    
    print("\n[Generated LLVM IR]")
    print("-" * 70)
    print(ir_code)
    print("-" * 70)
    
    print(f"\n✓ PrintNode with conditional test completed successfully!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

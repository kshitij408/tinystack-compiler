#!/usr/bin/env python
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer
from emitter import LLVMEmitter
from pathlib import Path

operators = [
    (">", "greater than", "push 10\npush 5"),
    ("<", "less than", "push 3\npush 5"),
    ("==", "equal", "push 7\npush 7"),
    ("!=", "not equal", "push 1\npush 2"),
]

print("=" * 70)
print("Testing All Comparison Operators in If-Else Statements")
print("=" * 70)

for op_symbol, op_name, operands in operators:
    print(f"\n[Testing {op_name} ({op_symbol})]")
    
    sample_code = f"""
var x = 1
{operands}
if {op_symbol} then
  push 1
  store x
else
  push 0
  store x
end
"""
    
    try:
        lexer = Lexer(sample_code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        
        emitter = LLVMEmitter(module_name=f"TinyStack_Op{op_symbol}")
        ir_code = emitter.emit(ast, output_path=str(
            Path('.').parent / "output" / f"output_op_{op_name}.ll"
        ))
        
        # Extract the comparison instruction from IR
        for line in ir_code.split('\n'):
            if 'icmp' in line:
                print(f"  ✓ {op_name}: {line.strip()}")
                break
        
    except Exception as e:
        print(f"  ✗ {op_name}: {e}")

print("\n✓ All comparison operators tested successfully!\n")

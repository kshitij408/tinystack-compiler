"""
TinyStack compiler driver.

Pipeline:
    source -> lexer -> parser -> AST -> semantic analysis -> LLVM emission
    -> optional LLVM optimization
"""

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from lexer import Lexer, LexerError, Token
from parser import Parser, ParserError
from ast_nodes import ProgramNode
from semantic import SemanticAnalyzer, SemanticError
from emitter import LLVMEmitter, EmitterError
from optimizer import Optimizer, OptimizerError


DEFAULT_OUTPUT = Path("output") / "output.ll"


@dataclass
class CompileResult:
    """Artifacts produced by a successful TinyStack compilation."""

    tokens: List[Token]
    ast: ProgramNode
    ir: str
    optimized_ir: Optional[str]
    output_path: Path
    optimized_output_path: Optional[Path]


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure process-wide logging for the compiler driver."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")
    return logging.getLogger("tinystack")


def optimized_output_path_for(output_path: Path) -> Path:
    """Return the default optimized IR path for a raw IR output path."""
    return output_path.with_name(f"{output_path.stem}_optimized{output_path.suffix}")


def compile_source(
    source: str,
    output_path: Path = DEFAULT_OUTPUT,
    optimize: bool = True,
    dump_ir: bool = False,
    logger: Optional[logging.Logger] = None,
) -> CompileResult:
    """
    Compile TinyStack source code through the full pipeline.

    Args:
        source: TinyStack source text.
        output_path: Destination for unoptimized LLVM IR.
        optimize: Whether to run LLVM optimization and write optimized IR.
        dump_ir: Whether to log generated IR text.
        logger: Optional logger for progress messages.

    Returns:
        CompileResult containing tokens, AST, and emitted IR artifacts.

    Raises:
        LexerError: Invalid source character or token.
        ParserError: Invalid syntax.
        SemanticError: Invalid program semantics.
        EmitterError: LLVM emission failed.
        OptimizerError: LLVM optimization failed.
        OSError: Output files could not be written.
    """
    logger = logger or logging.getLogger("tinystack")
    output_path = Path(output_path)

    logger.info("Lexing source")
    tokens = Lexer(source).tokenize()
    logger.debug("Token count: %d", len(tokens))

    logger.info("Parsing tokens")
    ast = Parser(tokens).parse()
    

    logger.debug("Statement count: %d", len(ast.statements))

    logger.info("Running semantic analysis")
    SemanticAnalyzer().analyze(ast)

    logger.info("Emitting LLVM IR: %s", output_path)
    ir_text = LLVMEmitter(module_name="TinyStack").emit(ast, output_path=str(output_path))
    if dump_ir:
        logger.info("Generated LLVM IR:\n%s", ir_text)

    optimized_ir = None
    optimized_path = None
    if optimize:
        optimized_path = optimized_output_path_for(output_path)
        logger.info("Optimizing LLVM IR: %s", optimized_path)
        optimized_ir = Optimizer().optimize(ir_text)
        optimized_path.parent.mkdir(parents=True, exist_ok=True)
        optimized_path.write_text(optimized_ir, encoding="utf-8")
        if dump_ir:
            logger.info("Optimized LLVM IR:\n%s", optimized_ir)

    return CompileResult(
        tokens=tokens,
        ast=ast,
        ir=ir_text,
        optimized_ir=optimized_ir,
        output_path=output_path,
        optimized_output_path=optimized_path,
    )


def compile_file(
    input_path: Path,
    output_path: Path = DEFAULT_OUTPUT,
    optimize: bool = True,
    dump_ir: bool = False,
    logger: Optional[logging.Logger] = None,
) -> CompileResult:
    """Read and compile a TinyStack source file."""
    input_path = Path(input_path)
    logger = logger or logging.getLogger("tinystack")
    
    logger.info("Reading source file: %s", input_path)
    source = input_path.read_text(encoding="utf-8")
    
    return compile_source(
        source,
        output_path=output_path,
        optimize=optimize,
        dump_ir=dump_ir,
        logger=logger,
    )


def demo_source() -> str:
    """Return a small valid program used when no input file is provided."""
    return """\
var x = 10
push x
push 5
add
store x
push x
print
"""


def build_arg_parser() -> argparse.ArgumentParser:
    """Create the command-line parser for the compiler driver."""
    parser = argparse.ArgumentParser(
        description="Compile TinyStack source to LLVM IR",
        usage="python3 src/main.py <source_file> [options]",
        epilog="""
Examples:
  python3 src/main.py testcases/if_else_true.ts
  python3 src/main.py testcases/arithmetic.ts -o my_output.ll
  python3 src/main.py testcases/program.ts --no-optimize
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "input",
        help="TinyStack source file to compile",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Path for unoptimized LLVM IR output (default: %(default)s)",
    )
    parser.add_argument(
        "--no-optimize",
        action="store_true",
        help="Skip LLVM optimization",
    )
    parser.add_argument(
        "--dump-ir",
        action="store_true",
        help="Log generated LLVM IR text",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Command-line entry point."""
    args = build_arg_parser().parse_args(argv)
    logger = setup_logging(verbose=args.verbose)

    try:
        # Check if input file exists
        input_path = Path(args.input)
        if not input_path.exists():
            logger.error("Source file not found: %s", input_path)
            return 1
        
        result = compile_file(
            input_path,
            output_path=Path(args.output),
            optimize=not args.no_optimize,
            dump_ir=args.dump_ir,
            logger=logger,
        )
    except (LexerError, ParserError, SemanticError, EmitterError, OptimizerError) as exc:
        logger.error("%s", exc)
        return 1
    except OSError as exc:
        logger.error("File error: %s", exc)
        return 1

    logger.info("Compilation successful")
    logger.info("LLVM IR written to: %s", result.output_path)
    if result.optimized_output_path:
        logger.info("Optimized LLVM IR written to: %s", result.optimized_output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
Optimizer for TinyStack LLVM IR modules.

llvmlite 0.45+ removed the legacy pass-builder API. This module uses LLVM's
New Pass Manager APIs when they are available:

    create_pipeline_tuning_options()
    create_pass_builder()
    create_new_module_pass_manager()

The public API remains intentionally small:

    Optimizer().optimize(ir_text) -> optimized_ir

The default TinyStack optimization path is:

    mem2reg/SROA intent -> instruction simplification -> dead code cleanup

On current llvmlite builds, not every one of those passes is exposed as an
individual ``add_*`` method. In that case the optimizer runs llvmlite's
populated module optimization pipeline at the requested optimization level.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional
import difflib
import os

from llvmlite import binding as llvm


class OptimizerError(Exception):
    """Raised when LLVM optimization fails."""


class OptimizationPass(Enum):
    """Optimization passes understood by the TinyStack optimizer."""

    MEM2REG = auto()
    CONSTANT_PROP = auto()
    DCE = auto()
    CFG_SIMPLIFY = auto()
    GVN = auto()
    INST_COMBINE = auto()


@dataclass
class IRStats:
    """Basic statistics extracted from an LLVM IR module string."""

    instructions: int = 0
    basic_blocks: int = 0
    functions: int = 0
    alloca_count: int = 0
    load_count: int = 0
    store_count: int = 0

    def summary(self) -> str:
        """Return a one-line human-readable summary."""
        return (
            f"Instructions: {self.instructions}, "
            f"Blocks: {self.basic_blocks}, "
            f"Functions: {self.functions}, "
            f"Allocas: {self.alloca_count}, "
            f"Loads: {self.load_count}, "
            f"Stores: {self.store_count}"
        )


@dataclass
class PassResult:
    """Outcome of running one optimization pass or pipeline."""

    pass_name: str
    ir_before: str
    ir_after: str
    changed: bool
    diff: str

    def summary(self) -> str:
        """One-line summary suitable for logs or reports."""
        status = "CHANGED" if self.changed else "no change"
        return f"  [{status:>9}] {self.pass_name}"


@dataclass
class OptimizationResult:
    """Aggregated result of running the optimizer."""

    original_ir: str
    optimized_ir: str
    pass_results: List[PassResult] = field(default_factory=list)
    stats_before: Optional[IRStats] = None
    stats_after: Optional[IRStats] = None

    @property
    def changed(self) -> bool:
        """True if any pass or pipeline modified the IR."""
        return any(result.changed for result in self.pass_results)

    @property
    def full_diff(self) -> str:
        """Unified diff between original and final optimized IR."""
        return Optimizer.compare(self.original_ir, self.optimized_ir)

    def summary(self) -> str:
        """Return a multi-line human-readable optimization report."""
        lines: list[str] = []
        lines.append("=" * 60)
        lines.append("  Optimization Summary")
        lines.append("=" * 60)

        if self.stats_before and self.stats_after:
            lines.append(f"\n  Before : {self.stats_before.summary()}")
            lines.append(f"  After  : {self.stats_after.summary()}")

            delta = self.stats_before.instructions - self.stats_after.instructions
            if delta > 0:
                lines.append(f"  Result : {delta} instruction(s) removed")
            elif delta == 0:
                lines.append("  Result : instruction count unchanged")
            else:
                lines.append(f"  Result : {abs(delta)} instruction(s) added")

        lines.append(f"\n  Passes executed ({len(self.pass_results)}):")
        for result in self.pass_results:
            lines.append(result.summary())

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)


class Optimizer:
    """Apply LLVM IR optimizations to TinyStack-generated modules."""

    DEFAULT_PASSES = [
        OptimizationPass.MEM2REG,
        OptimizationPass.INST_COMBINE,
        OptimizationPass.DCE,
    ]

    PASS_ORDER = [
        OptimizationPass.MEM2REG,
        OptimizationPass.INST_COMBINE,
        OptimizationPass.CONSTANT_PROP,
        OptimizationPass.GVN,
        OptimizationPass.CFG_SIMPLIFY,
        OptimizationPass.DCE,
    ]

    # Candidate names are feature-detected because legacy and new pass managers
    # expose different spellings and different subsets of passes.
    _PASS_METHODS = {
        OptimizationPass.MEM2REG: ("add_sroa_pass",),
        OptimizationPass.CONSTANT_PROP: ("add_sccp_pass",),
        OptimizationPass.DCE: ("add_dead_code_elimination_pass",),
        OptimizationPass.CFG_SIMPLIFY: (
            "add_simplify_cfg_pass",
            "add_cfg_simplification_pass",
        ),
        OptimizationPass.GVN: ("add_gvn_pass",),
        OptimizationPass.INST_COMBINE: (
            "add_instruction_combine_pass",
            "add_instruction_combining_pass",
        ),
    }

    _PASS_DESCRIPTIONS = {
        OptimizationPass.MEM2REG: "Promote Memory to Registers (SROA/mem2reg)",
        OptimizationPass.CONSTANT_PROP: "Sparse Conditional Constant Propagation",
        OptimizationPass.DCE: "Dead Code Elimination",
        OptimizationPass.CFG_SIMPLIFY: "Control Flow Graph Simplification",
        OptimizationPass.GVN: "Global Value Numbering",
        OptimizationPass.INST_COMBINE: "Instruction Combining",
    }

    def __init__(
        self,
        passes: Optional[List[OptimizationPass]] = None,
        opt_level: int = 2,
    ):
        """
        Initialize LLVM bindings and optimizer settings.

        Args:
            passes: Passes to run. None selects the default TinyStack pipeline.
            opt_level: Optimization level from 0 to 3 for populated pipelines.
        """
        self._initialize_llvm()

        self.opt_level = int(opt_level)
        if self.opt_level < 0 or self.opt_level > 3:
            raise OptimizerError("Optimization level must be between 0 and 3")

        self.passes = list(passes) if passes is not None else list(self.DEFAULT_PASSES)
        invalid_passes = [p for p in self.passes if not isinstance(p, OptimizationPass)]
        if invalid_passes:
            raise OptimizerError(f"Invalid optimization pass value(s): {invalid_passes}")

        self._new_pm_available = self._has_new_pass_manager()
        self._individual_passes_available = self._check_pass_availability()

    @staticmethod
    def _initialize_llvm() -> None:
        """Initialize LLVM bindings defensively."""
        for initializer in (
            getattr(llvm, "initialize", None),
            getattr(llvm, "initialize_native_target", None),
            getattr(llvm, "initialize_native_asmprinter", None),
        ):
            if initializer is None:
                continue
            try:
                initializer()
            except Exception:
                pass

    @staticmethod
    def _has_new_pass_manager() -> bool:
        """Return True when llvmlite exposes the New Pass Manager API."""
        return all(
            hasattr(llvm, name)
            for name in (
                "create_pipeline_tuning_options",
                "create_pass_builder",
                "create_new_module_pass_manager",
            )
        )

    @staticmethod
    def _parse_module(ir_text: str):
        """Parse an IR string into a verified LLVM module."""
        module = llvm.parse_assembly(ir_text)
        module.verify()
        return module

    @staticmethod
    def _create_target_machine():
        """Create the target machine required by the New Pass Manager."""
        target = llvm.Target.from_default_triple()
        return target.create_target_machine()

    def _create_pass_builder(self):
        """Create a New Pass Manager PassBuilder."""
        if not self._new_pm_available:
            raise OptimizerError(
                "Installed llvmlite does not expose the New Pass Manager API"
            )

        pto = llvm.create_pipeline_tuning_options(
            speed_level=self.opt_level,
            size_level=0,
        )
        return llvm.create_pass_builder(self._create_target_machine(), pto)

    def _create_empty_module_pass_manager(self):
        """Create an empty module pass manager for individual pass methods."""
        if hasattr(llvm, "create_new_module_pass_manager"):
            return llvm.create_new_module_pass_manager()
        if hasattr(llvm, "ModulePassManager"):
            return llvm.ModulePassManager()
        raise OptimizerError("Installed llvmlite has no module pass manager API")

    @staticmethod
    def _run_module_pass_manager(pm, module, pass_builder=None) -> None:
        """Run a module pass manager across new and older llvmlite signatures."""
        if pass_builder is not None:
            pm.run(module, pass_builder)
        else:
            pm.run(module)

    def _find_pass_method(self, pm, pass_enum: OptimizationPass) -> Optional[str]:
        """Return the first installed llvmlite method for a pass, if any."""
        for method_name in self._PASS_METHODS.get(pass_enum, ()):
            if hasattr(pm, method_name):
                return method_name
        return None

    def _check_pass_availability(self) -> bool:
        """Return True if every configured pass is individually exposed."""
        try:
            pm = self._create_empty_module_pass_manager()
        except OptimizerError:
            return False

        return all(self._find_pass_method(pm, pass_enum) for pass_enum in self.passes)

    def _add_pass_to_pm(self, pm, pass_enum: OptimizationPass) -> None:
        """Add a configured pass to a pass manager or raise OptimizerError."""
        method_name = self._find_pass_method(pm, pass_enum)
        if method_name is None:
            pass_name = self._PASS_DESCRIPTIONS.get(pass_enum, pass_enum.name)
            raise OptimizerError(
                f"Pass is not exposed by this llvmlite version: {pass_name}"
            )
        getattr(pm, method_name)()

    def _ordered_passes(self) -> List[OptimizationPass]:
        """Return configured passes sorted in canonical order."""
        return [p for p in self.PASS_ORDER if p in self.passes]

    def _run_single_pass(self, ir_text: str, pass_enum: OptimizationPass) -> PassResult:
        """Execute one individually exposed pass."""
        pass_name = self._PASS_DESCRIPTIONS.get(pass_enum, pass_enum.name)
        before_ir = ir_text

        try:
            module = self._parse_module(ir_text)
            pm = self._create_empty_module_pass_manager()
            self._add_pass_to_pm(pm, pass_enum)
            pass_builder = self._create_pass_builder() if self._new_pm_available else None
            self._run_module_pass_manager(pm, module, pass_builder)
            after_ir = str(module)
        except Exception as exc:
            raise OptimizerError(f"Optimization pass failed: {pass_name}: {exc}") from exc

        changed = before_ir.strip() != after_ir.strip()
        return PassResult(
            pass_name=pass_name,
            ir_before=before_ir,
            ir_after=after_ir,
            changed=changed,
            diff=self.compare(before_ir, after_ir) if changed else "",
        )

    def _optimize_with_pipeline(self, ir_text: str) -> str:
        """Run llvmlite's populated New Pass Manager module pipeline."""
        try:
            module = self._parse_module(ir_text)
            pass_builder = self._create_pass_builder()
            module_pm = pass_builder.getModulePassManager()
            self._run_module_pass_manager(module_pm, module, pass_builder)
            return str(module)
        except Exception as exc:
            raise OptimizerError(f"LLVM optimization failed: {exc}") from exc

    def _can_use_populated_pipeline(self) -> bool:
        """Return True when the selected passes match TinyStack defaults."""
        return self._ordered_passes() == self.DEFAULT_PASSES

    def optimize(self, ir_text: str) -> str:
        """
        Optimize *ir_text* and return optimized LLVM IR.

        Current llvmlite builds do not expose every old legacy individual pass.
        For TinyStack's default pass set, this method uses the populated New
        Pass Manager pipeline when individual pass hooks are unavailable.
        """
        if self._individual_passes_available:
            current = ir_text
            for pass_enum in self._ordered_passes():
                current = self._run_single_pass(current, pass_enum).ir_after
            return current

        if self._can_use_populated_pipeline():
            return self._optimize_with_pipeline(ir_text)

        missing = []
        pm = self._create_empty_module_pass_manager()
        for pass_enum in self._ordered_passes():
            if self._find_pass_method(pm, pass_enum) is None:
                missing.append(self._PASS_DESCRIPTIONS.get(pass_enum, pass_enum.name))

        raise OptimizerError(
            "The installed llvmlite version does not expose individual pass "
            f"methods for: {', '.join(missing)}. Use the default optimizer "
            "pipeline or select only passes exposed by this llvmlite build."
        )

    def optimize_with_details(self, ir_text: str) -> OptimizationResult:
        """Optimize *ir_text* and return per-pass or per-pipeline details."""
        stats_before = self.get_ir_stats(ir_text)
        pass_results: list[PassResult] = []
        current = ir_text

        if self._individual_passes_available:
            for pass_enum in self._ordered_passes():
                result = self._run_single_pass(current, pass_enum)
                pass_results.append(result)
                current = result.ir_after
        else:
            if not self._can_use_populated_pipeline():
                raise OptimizerError(
                    "Detailed per-pass optimization requires individual pass "
                    "methods exposed by llvmlite for every selected pass"
                )
            optimized = self._optimize_with_pipeline(ir_text)
            changed = ir_text.strip() != optimized.strip()
            pass_results.append(
                PassResult(
                    pass_name=f"New Pass Manager Pipeline (opt_level={self.opt_level})",
                    ir_before=ir_text,
                    ir_after=optimized,
                    changed=changed,
                    diff=self.compare(ir_text, optimized) if changed else "",
                )
            )
            current = optimized

        return OptimizationResult(
            original_ir=ir_text,
            optimized_ir=current,
            pass_results=pass_results,
            stats_before=stats_before,
            stats_after=self.get_ir_stats(current),
        )

    def optimize_and_write(
        self,
        ir_text: str,
        output_path: Optional[str] = None,
        report_path: Optional[str] = None,
    ) -> OptimizationResult:
        """Optimize, optionally write files, and return a detailed report."""
        result = self.optimize_with_details(ir_text)

        if output_path:
            abs_out = os.path.abspath(output_path)
            os.makedirs(os.path.dirname(abs_out), exist_ok=True)
            with open(abs_out, "w", encoding="utf-8") as fh:
                fh.write(result.optimized_ir)

        if report_path:
            abs_rpt = os.path.abspath(report_path)
            os.makedirs(os.path.dirname(abs_rpt), exist_ok=True)
            with open(abs_rpt, "w", encoding="utf-8") as fh:
                fh.write(result.summary())
                fh.write("\n\n")
                fh.write("=" * 60 + "\n")
                fh.write("Full Diff (Original -> Optimized)\n")
                fh.write("=" * 60 + "\n")
                fh.write(result.full_diff or "<no changes>\n")
                fh.write("\n")
                for pass_result in result.pass_results:
                    if pass_result.changed and pass_result.diff:
                        fh.write(f"\n--- Pass: {pass_result.pass_name} ---\n")
                        fh.write(pass_result.diff)
                        fh.write("\n")

        return result

    @staticmethod
    def compare(before_ir: str, after_ir: str) -> str:
        """Return a unified diff between *before_ir* and *after_ir*."""
        diff = difflib.unified_diff(
            before_ir.splitlines(),
            after_ir.splitlines(),
            fromfile="before_optimization.ll",
            tofile="after_optimization.ll",
            lineterm="",
        )
        return "\n".join(diff)

    @staticmethod
    def get_ir_stats(ir_text: str) -> IRStats:
        """Compute basic statistics for an IR string."""
        stats = IRStats()
        for raw_line in ir_text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith(";"):
                continue
            if line.startswith("define "):
                stats.functions += 1
            elif line.endswith(":") and not line.startswith("target"):
                stats.basic_blocks += 1
            elif "= alloca " in line:
                stats.alloca_count += 1
                stats.instructions += 1
            elif "= load " in line:
                stats.load_count += 1
                stats.instructions += 1
            elif line.startswith("store "):
                stats.store_count += 1
                stats.instructions += 1
            elif (
                "= " in line
                or line.startswith("ret ")
                or line.startswith("br ")
                or line.startswith("call ")
                or line.startswith("switch ")
            ):
                stats.instructions += 1
        return stats


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Optimize TinyStack LLVM IR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Available individual passes depend on the installed llvmlite build.
The default pass set uses the New Pass Manager populated pipeline when needed.

Examples:
  python optimizer.py input.ll
  python optimizer.py input.ll -o optimized.ll
  python optimizer.py input.ll --passes instcombine cfgsimplify
  python optimizer.py input.ll -O 3
""",
    )
    parser.add_argument("input", help="Path to input .ll file")
    parser.add_argument("-o", "--output", help="Path to write optimized IR")
    parser.add_argument("-r", "--report", help="Path to write optimization report")
    parser.add_argument(
        "-O",
        "--opt-level",
        type=int,
        default=2,
        help="Optimization level 0-3",
    )
    parser.add_argument(
        "--passes",
        nargs="+",
        choices=["mem2reg", "constprop", "dce", "cfgsimplify", "gvn", "instcombine"],
        help="Specific individually exposed passes to run",
    )
    args = parser.parse_args()

    cli_pass_map = {
        "mem2reg": OptimizationPass.MEM2REG,
        "constprop": OptimizationPass.CONSTANT_PROP,
        "dce": OptimizationPass.DCE,
        "cfgsimplify": OptimizationPass.CFG_SIMPLIFY,
        "gvn": OptimizationPass.GVN,
        "instcombine": OptimizationPass.INST_COMBINE,
    }

    selected = [cli_pass_map[p] for p in args.passes] if args.passes else None

    try:
        with open(args.input, "r", encoding="utf-8") as fh:
            input_ir = fh.read()

        opt = Optimizer(passes=selected, opt_level=args.opt_level)
        res = opt.optimize_and_write(
            input_ir,
            output_path=args.output,
            report_path=args.report,
        )
    except (OSError, OptimizerError) as exc:
        print(f"Optimization failed: {exc}")
        raise SystemExit(1)

    print(res.summary())

    if res.full_diff:
        print("\n--- Diff (before -> after) ---")
        print(res.full_diff)
    else:
        print("\n<no changes>")

    if args.output:
        print(f"\nOptimized IR written to: {os.path.abspath(args.output)}")
    if args.report:
        print(f"Report written to: {os.path.abspath(args.report)}")

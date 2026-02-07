"""Function inlining optimization.

This module provides AST-level function inlining for small, frequently-called
functions. Inlining eliminates call overhead and enables further optimizations
like native type propagation across the inlined code.

Key targets:
- Small arithmetic functions like eval_A in spectralnorm
- Single-expression functions
- Functions called in hot loops
"""

from __future__ import annotations

import ast
import copy
from dataclasses import dataclass, field


@dataclass
class InlineCandidate:
    """Metadata about a function that may be inlined."""

    name: str
    node: ast.FunctionDef
    cost: int  # Estimated code size (WAT instructions)
    call_count: int = 0  # Static call count in module
    is_recursive: bool = False
    has_nested_functions: bool = False
    has_try_except: bool = False
    has_yield: bool = False
    has_nonlocal: bool = False
    has_global_write: bool = False  # Writes to global variables
    has_decorators: bool = False  # Function has decorators
    param_names: list[str] = field(default_factory=list)


def analyze_inlining(body: list[ast.stmt]) -> dict[str, InlineCandidate]:
    """Analyze module for inlining opportunities.

    Args:
        body: Module body (list of statements)

    Returns:
        Dictionary mapping function name to InlineCandidate
    """
    candidates: dict[str, InlineCandidate] = {}

    # First pass: analyze all functions
    for stmt in body:
        match stmt:
            case ast.FunctionDef():
                candidate = _analyze_function(stmt)
                candidates[stmt.name] = candidate

    # Second pass: count call sites
    for stmt in body:
        _count_calls(stmt, candidates)

    return candidates


def _analyze_function(node: ast.FunctionDef) -> InlineCandidate:
    """Analyze a single function for inlining eligibility."""
    param_names = [arg.arg for arg in node.args.args]

    candidate = InlineCandidate(
        name=node.name,
        node=node,
        cost=_estimate_cost(node),
        param_names=param_names,
        has_decorators=bool(node.decorator_list),
    )

    # Check for disqualifying features
    for child in ast.walk(node):
        match child:
            case ast.FunctionDef() if child is not node:
                candidate.has_nested_functions = True
            case ast.AsyncFunctionDef() | ast.Lambda():
                candidate.has_nested_functions = True
            case ast.Try() | ast.ExceptHandler():
                candidate.has_try_except = True
            case ast.Yield() | ast.YieldFrom():
                candidate.has_yield = True
            case ast.Nonlocal():
                candidate.has_nonlocal = True
            case ast.Global(names=names):
                # Check if any global is actually written to
                global_names = set(names)
                candidate.has_global_write = _has_global_write(node, global_names)

    # Check for recursion
    candidate.is_recursive = _is_recursive(node)

    return candidate


def _estimate_cost(node: ast.FunctionDef) -> int:
    """Estimate code size of function body in WAT instructions.

    Lower cost = better inlining candidate.
    """
    cost = 0
    for child in ast.walk(node):
        match child:
            case ast.BinOp():
                cost += 3  # op + 2 operands
            case ast.UnaryOp():
                cost += 2
            case ast.Compare():
                cost += 3
            case ast.BoolOp():
                cost += 2
            case ast.Call():
                cost += 8  # call overhead (args packing + dispatch)
            case ast.If():
                cost += 4  # branch
            case ast.IfExp():
                cost += 3  # conditional expression
            case ast.For():
                cost += 15  # loop structure + iterator
            case ast.While():
                cost += 10  # loop structure
            case ast.Return():
                cost += 1
            case ast.Assign():
                cost += 2
            case ast.AugAssign():
                cost += 3
            case ast.AnnAssign():
                cost += 2
            case ast.Subscript():
                cost += 4  # index access
            case ast.Attribute():
                cost += 3  # attribute access
            case ast.Name():
                cost += 1  # variable reference
            case ast.Constant():
                cost += 1
            case ast.List() | ast.Tuple() | ast.Dict() | ast.Set():
                cost += 5  # collection construction
    return cost


def _is_recursive(node: ast.FunctionDef) -> bool:
    """Check if function calls itself."""
    func_name = node.name
    for child in ast.walk(node):
        match child:
            case ast.Call(func=ast.Name(id=name)) if name == func_name:
                return True
    return False


def _has_global_write(node: ast.FunctionDef, global_names: set[str]) -> bool:
    """Check if function writes to any of the specified global variables."""
    for child in ast.walk(node):
        match child:
            case ast.Assign(targets=targets):
                for target in targets:
                    match target:
                        case ast.Name(id=name) if name in global_names:
                            return True
            case ast.AugAssign(target=ast.Name(id=name)) if name in global_names:
                return True
    return False


def _count_calls(node: ast.AST, candidates: dict[str, InlineCandidate]) -> None:
    """Count call sites for each candidate function."""
    for child in ast.walk(node):
        match child:
            case ast.Call(func=ast.Name(id=func_name)) if func_name in candidates:
                candidates[func_name].call_count += 1


def should_inline(candidate: InlineCandidate) -> bool:
    """Decide whether to inline a function.

    Returns True if the function should be inlined.

    Note: The cost thresholds are tuned for hot inner loop functions like
    eval_A in spectralnorm. Even though static call count may be low (2),
    the dynamic call count in loops can be O(n²).
    """
    # Never inline functions with these features
    if candidate.is_recursive:
        return False
    if candidate.has_nested_functions:
        return False
    if candidate.has_try_except:
        return False
    if candidate.has_yield:
        return False
    if candidate.has_nonlocal:
        return False
    if candidate.has_global_write:
        return False
    if candidate.has_decorators:
        # Decorated functions call the wrapper, not the original function
        return False

    # Always inline very small functions (single expression)
    if candidate.cost <= 20:
        return True

    # Inline small-medium functions if called at least once
    # This catches eval_A (cost ~40) which is called in hot loops
    if candidate.cost <= 45 and candidate.call_count >= 1:
        return True

    # Inline larger functions if called multiple times
    return bool(candidate.cost <= 70 and candidate.call_count >= 3)


def can_inline_call(
    call: ast.Call,
    candidate: InlineCandidate,
) -> bool:
    """Check if a specific call can be inlined.

    Some calls may not be inlinable even if the function is a candidate,
    e.g., calls with *args, **kwargs, or mismatched argument counts.
    """
    # Must be a simple name call
    match call.func:
        case ast.Name():
            pass
        case _:
            return False

    # No keyword arguments (for simplicity)
    if call.keywords:
        return False

    # No starred arguments
    if any(isinstance(arg, ast.Starred) for arg in call.args):
        return False

    # Argument count must match parameter count (no defaults for now)
    func_node = candidate.node
    num_params = len(func_node.args.args)
    num_args = len(call.args)

    # Handle default arguments
    num_defaults = len(func_node.args.defaults)
    min_args = num_params - num_defaults
    max_args = num_params

    return min_args <= num_args <= max_args


class FunctionInliner(ast.NodeTransformer):
    """Transform AST to inline function calls.

    This transformer replaces calls to inlinable functions with their
    inlined body. For simple single-return functions, parameters are
    substituted with arguments directly.

    Note: We only inline calls inside function bodies, not at module level,
    because NamedExpr (walrus operator) creates locals that must be declared.
    """

    def __init__(self, candidates: dict[str, InlineCandidate]) -> None:
        self.candidates = candidates
        self.inline_targets = {
            name: cand for name, cand in candidates.items() if should_inline(cand)
        }
        self.counter = 0  # For generating unique variable names
        self.inlined_count = 0  # Track how many calls were inlined
        self.inside_function = False  # Track if we're inside a function body

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Visit function definition - enable inlining inside functions."""
        # Save state
        was_inside = self.inside_function
        self.inside_function = True

        # Visit children
        node = self.generic_visit(node)

        # Restore state
        self.inside_function = was_inside
        return node

    def visit_Call(self, node: ast.Call) -> ast.expr:
        """Visit a call expression and potentially inline it."""
        # First, visit child nodes
        node = self.generic_visit(node)

        # Only inline inside function bodies (NamedExpr requires declared locals)
        if not self.inside_function:
            return node

        match node.func:
            case ast.Name(id=func_name):
                pass
            case _:
                return node
        if func_name not in self.inline_targets:
            return node

        candidate = self.inline_targets[func_name]
        if not can_inline_call(node, candidate):
            return node

        # Try to inline the call
        inlined = self._inline_call(node, candidate)
        if inlined is not None:
            self.inlined_count += 1
            return inlined

        return node

    def _inline_call(
        self,
        call: ast.Call,
        candidate: InlineCandidate,
    ) -> ast.expr | None:
        """Inline a function call, returning the inlined expression.

        Returns None if inlining is not possible.
        """
        func = candidate.node
        body = func.body

        # Check if we can inline this function body
        if not self._can_inline_body(body):
            return None

        # Build parameter -> argument mapping
        param_to_arg: dict[str, ast.expr] = {}
        for i, param in enumerate(func.args.args):
            if i < len(call.args):
                param_to_arg[param.arg] = call.args[i]
            else:
                # Use default value
                default_idx = i - (len(func.args.args) - len(func.args.defaults))
                param_to_arg[param.arg] = func.args.defaults[default_idx]

        # Collect local variable assignments
        local_vars: dict[str, ast.expr] = {}
        return_expr: ast.expr | None = None

        for stmt in body:
            match stmt:
                case ast.Return(value=val):
                    return_expr = val
                case ast.Assign(targets=[ast.Name(id=var_name)], value=val):
                    # Simple assignment: x = expr
                    local_vars[var_name] = val
                case ast.AnnAssign(target=ast.Name(id=var_name), value=val) if (
                    val is not None
                ):
                    # Annotated assignment: x: type = expr
                    local_vars[var_name] = val
                case ast.Expr():
                    # Expression statement (e.g., docstring) - skip
                    pass

        if return_expr is None:
            # Return with no value - return None constant
            return ast.Constant(value=None)

        # Substitute parameters and local variables in the return expression
        inlined_expr = self._substitute_all(
            return_expr,
            param_to_arg,
            local_vars,
        )

        # Copy source location from original call
        ast.copy_location(inlined_expr, call)

        return inlined_expr

    def _can_inline_body(self, body: list[ast.stmt]) -> bool:
        """Check if function body can be inlined.

        We can inline functions with:
        - Optional docstring (Expr with Constant string)
        - Zero or more simple assignments (x = expr or x: type = expr)
        - A final return statement

        We CANNOT inline functions with:
        - Side effects (print, function calls in expressions)
        - Control flow (if, for, while)
        - Multiple statements that aren't pure assignments
        """
        has_return = False

        for stmt in body:
            match stmt:
                case ast.Return():
                    has_return = True
                case ast.Assign(targets=[ast.Name()], value=val):
                    # Simple single-target assignment
                    if self._has_side_effects(val):
                        return False
                case ast.Assign():
                    # Multiple targets or non-Name target
                    return False
                case ast.AnnAssign(target=ast.Name(), value=val) if val is not None:
                    # Annotated assignment with value and simple target
                    if self._has_side_effects(val):
                        return False
                case ast.AnnAssign():
                    # Missing value or non-Name target
                    return False
                case ast.Expr(value=ast.Constant(value=str())):
                    # Docstring is OK
                    pass
                case ast.Expr():
                    # Other expression statements have side effects
                    return False
                case _:
                    # Other statements not supported
                    return False

        return has_return

    def _has_side_effects(self, expr: ast.expr) -> bool:
        """Check if expression has side effects (function calls, etc.)."""
        for node in ast.walk(expr):
            match node:
                case ast.Call():
                    # Function calls may have side effects
                    return True
                case ast.NamedExpr():
                    # Walrus operator has side effects (assignment)
                    return True
        return False

    def _substitute_all(
        self,
        expr: ast.expr,
        param_to_arg: dict[str, ast.expr],
        local_vars: dict[str, ast.expr],
    ) -> ast.expr:
        """Substitute parameters and local variables in expression.

        For local variables, we use NamedExpr (walrus operator) to avoid
        duplicate computation. For example:
            ij = i + j
            return 1.0 / (ij * (ij + 1) / 2 + i + 1)
        Becomes:
            return 1.0 / ((__i0_ij := i + j) * (__i0_ij + 1) / 2 + i + 1)

        This ensures the local variable is computed once and reused.
        We use unique names (__iN_varname) to avoid shadowing outer variables.
        """
        # Generate unique names for local variables to avoid shadowing
        name_map: dict[str, str] = {}
        for var_name in local_vars:
            unique_name = f"__i{self.counter}_{var_name}__"
            name_map[var_name] = unique_name
            self.counter += 1

        # First, substitute parameters in local variable expressions
        expanded_locals: dict[str, ast.expr] = {}
        for var_name, var_expr in local_vars.items():
            expanded = self._expand_expr(var_expr, param_to_arg, {})
            expanded_locals[name_map[var_name]] = expanded

        # For each local variable, track if we've emitted its NamedExpr
        emitted_named_exprs: set[str] = set()

        # Transform the expression, using NamedExpr for first occurrence of each local
        return self._expand_with_named_expr(
            expr, param_to_arg, expanded_locals, name_map, emitted_named_exprs
        )

    def _expand_with_named_expr(
        self,
        expr: ast.expr,
        param_to_arg: dict[str, ast.expr],
        local_vars: dict[str, ast.expr],
        name_map: dict[str, str],
        emitted: set[str],
    ) -> ast.expr:
        """Expand expression, using NamedExpr for first local var occurrence.

        Args:
            expr: Expression to expand
            param_to_arg: Parameter name -> argument expression mapping
            local_vars: Unique local name -> value expression mapping
            name_map: Original local name -> unique local name mapping
            emitted: Set of unique names that have been emitted as NamedExpr
        """

        class NamedExprExpander(ast.NodeTransformer):
            def visit_Name(inner_self, node: ast.Name) -> ast.expr:  # noqa: N805
                name = node.id
                if name in param_to_arg:
                    return copy.deepcopy(param_to_arg[name])
                # Check if this is an original local var name
                if name in name_map:
                    unique_name = name_map[name]
                    if unique_name not in emitted:
                        # First occurrence: emit NamedExpr with unique name
                        emitted.add(unique_name)
                        value = copy.deepcopy(local_vars[unique_name])
                        # Recursively expand the value
                        value = inner_self.visit(value)
                        return ast.NamedExpr(
                            target=ast.Name(id=unique_name, ctx=ast.Store()),
                            value=value,
                        )
                    # Subsequent occurrence: use the unique name
                    return ast.Name(id=unique_name, ctx=ast.Load())
                return node

        expr_copy = copy.deepcopy(expr)
        return NamedExprExpander().visit(expr_copy)

    def _expand_expr(
        self,
        expr: ast.expr,
        param_to_arg: dict[str, ast.expr],
        local_vars: dict[str, ast.expr],
    ) -> ast.expr:
        """Expand an expression by substituting names."""

        class NameExpander(ast.NodeTransformer):
            def visit_Name(self, node: ast.Name) -> ast.expr:
                name = node.id
                if name in param_to_arg:
                    return copy.deepcopy(param_to_arg[name])
                if name in local_vars:
                    return copy.deepcopy(local_vars[name])
                return node

        expr_copy = copy.deepcopy(expr)
        return NameExpander().visit(expr_copy)


def inline_functions(body: list[ast.stmt]) -> tuple[list[ast.stmt], int]:
    """Apply function inlining to a module body.

    Args:
        body: Module body (list of statements)

    Returns:
        Tuple of (transformed body, number of inlined calls)
    """
    # Analyze candidates
    candidates = analyze_inlining(body)

    # Check if there's anything to inline
    targets = {name for name, cand in candidates.items() if should_inline(cand)}
    if not targets:
        return body, 0

    # Transform AST
    inliner = FunctionInliner(candidates)
    transformed_body = [inliner.visit(stmt) for stmt in body]

    # Fix missing locations after transformation
    for stmt in transformed_body:
        ast.fix_missing_locations(stmt)

    return transformed_body, inliner.inlined_count

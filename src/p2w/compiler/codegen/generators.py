"""Generator function compilation."""

from __future__ import annotations

import ast
from io import StringIO
from typing import TYPE_CHECKING

from p2w.compiler.analysis import (
    collect_global_decls,
    collect_iter_locals,
    collect_local_vars,
    collect_nonlocal_decls,
    collect_yield_points,
)
from p2w.compiler.builtins import BUILTINS
from p2w.compiler.codegen.expressions import compile_expr
from p2w.compiler.codegen.statements import compile_stmt
from p2w.compiler.context import FunctionSignature

if TYPE_CHECKING:
    from p2w.compiler.context import CompilerContext


class GeneratorContext:
    """Context for compiling generator functions."""

    def __init__(
        self,
        gen_local: str,
        state_local: str,
        locals_local: str,
        param_names: list[str],
        local_names: list[str],
        yield_count: int,
        iter_locals: list[str] | None = None,
    ) -> None:
        self.gen_local = gen_local
        self.state_local = state_local
        self.locals_local = locals_local
        self.param_names = param_names
        self.local_names = local_names
        self.yield_count = yield_count
        self.iter_locals = iter_locals or []


def collect_yieldfrom_iter_locals(body: list[ast.stmt]) -> set[str]:
    """Collect iterator local names needed for yield from transformations.

    Returns local names like '$iter___yieldfrom_N__' for each yield from.
    """
    iter_locals: set[str] = set()

    class YieldFromFinder(ast.NodeVisitor):
        def __init__(self) -> None:
            self.counter = 0

        def visit_Expr(self, node: ast.Expr) -> None:
            match node.value:
                case ast.YieldFrom():
                    iter_locals.add(f"$iter___yieldfrom_{self.counter}__")
                    self.counter += 1
            self.generic_visit(node)

        def visit_Assign(self, node: ast.Assign) -> None:
            match node.value:
                case ast.YieldFrom():
                    iter_locals.add(f"$iter___yieldfrom_{self.counter}__")
                    self.counter += 1
            self.generic_visit(node)

        # Don't recurse into nested functions
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            pass

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            pass

        def visit_Lambda(self, node: ast.Lambda) -> None:
            pass

    finder = YieldFromFinder()
    for stmt in body:
        finder.visit(stmt)
    return iter_locals


def transform_yield_from(body: list[ast.stmt]) -> list[ast.stmt]:
    """Transform yield from statements into for-yield loops.

    Converts: yield from iterable
    Into:     for __yieldfrom_N__ in iterable: yield __yieldfrom_N__

    This allows the existing generator machinery to handle yield from.
    """
    counter = 0

    class YieldFromTransformer(ast.NodeTransformer):
        def visit_Expr(self, node: ast.Expr) -> ast.stmt:
            nonlocal counter
            match node.value:
                case ast.YieldFrom(value=iterable):
                    # yield from iterable -> for __yieldfrom_N__ in iterable: yield __yieldfrom_N__
                    var_name = f"__yieldfrom_{counter}__"
                    counter += 1
                    yield_var = ast.Name(id=var_name, ctx=ast.Load())
                    yield_expr = ast.Yield(value=yield_var)
                    yield_stmt = ast.Expr(value=yield_expr)
                    for_node = ast.For(
                        target=ast.Name(id=var_name, ctx=ast.Store()),
                        iter=iterable,
                        body=[yield_stmt],
                        orelse=[],
                    )
                    ast.copy_location(for_node, node)
                    ast.fix_missing_locations(for_node)
                    return for_node
            return node  # Return unchanged if no yield from

        def visit_Assign(self, node: ast.Assign) -> ast.stmt | list[ast.stmt]:
            nonlocal counter
            match node.value:
                case ast.YieldFrom(value=iterable):
                    # val = yield from iterable
                    # -> for __yieldfrom_N__ in iterable: yield __yieldfrom_N__
                    # -> val = None  (simplified: doesn't capture return value)
                    var_name = f"__yieldfrom_{counter}__"
                    counter += 1
                    yield_var = ast.Name(id=var_name, ctx=ast.Load())
                    yield_expr = ast.Yield(value=yield_var)
                    yield_stmt = ast.Expr(value=yield_expr)
                    for_node = ast.For(
                        target=ast.Name(id=var_name, ctx=ast.Store()),
                        iter=iterable,
                        body=[yield_stmt],
                        orelse=[],
                    )
                    # Assign None to target after loop (simplified)
                    assign_none = ast.Assign(
                        targets=node.targets,
                        value=ast.Constant(value=None),
                    )
                    ast.copy_location(for_node, node)
                    ast.copy_location(assign_none, node)
                    ast.fix_missing_locations(for_node)
                    ast.fix_missing_locations(assign_none)
                    return [for_node, assign_none]
            return node  # Return unchanged if no yield from

        # Don't recurse into nested functions
        def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
            return node

        def visit_AsyncFunctionDef(
            self, node: ast.AsyncFunctionDef
        ) -> ast.AsyncFunctionDef:
            return node

        def visit_Lambda(self, node: ast.Lambda) -> ast.Lambda:
            return node

    transformer = YieldFromTransformer()
    result: list[ast.stmt] = []
    for stmt in body:
        transformed = transformer.visit(stmt)
        match transformed:
            case list():
                result.extend(transformed)
            case _:
                result.append(transformed)
    return result


def compile_generator_function(
    name: str,
    args: ast.arguments,
    body: list[ast.stmt],
    ctx: CompilerContext,
) -> None:
    """Compile a generator function (contains yield statements).

    Generator functions are compiled into:
    1. A "wrapper" function that creates and returns a GENERATOR object
    2. A "body" function that implements the state machine
    """
    # Collect yield from iterator locals BEFORE transformation
    yieldfrom_iter_locals = collect_yieldfrom_iter_locals(body)

    # Transform yield from statements into for-yield loops
    body = transform_yield_from(body)

    param_names = [arg.arg for arg in args.args]
    yield_points = collect_yield_points(body)
    num_yields = len(yield_points)

    # Collect variables needed
    global_decls = collect_global_decls(body)
    nonlocal_decls = collect_nonlocal_decls(body)
    all_local_names = collect_local_vars(body) | set(param_names)

    # Record function signature
    num_defaults = len(args.defaults)
    first_default_idx = len(param_names) - num_defaults
    ctx.func_signatures[name] = FunctionSignature(
        param_names=param_names,
        defaults=list(args.defaults),
        first_default_idx=first_default_idx,
    )

    # Save state
    saved_stream = ctx.emitter.stream
    saved_indent = ctx.emitter.indent
    saved_locals = ctx.local_vars
    saved_global_decls = ctx.current_global_decls
    saved_nonlocal_decls = ctx.current_nonlocal_decls

    ctx.current_global_decls = global_decls
    ctx.current_nonlocal_decls = nonlocal_decls

    # First, compile the generator body function (state machine)
    ctx.emitter.stream = StringIO()
    ctx.emitter.indent = 0
    ctx.local_vars = {}
    body_func_idx = len(ctx.user_funcs)
    ctx.user_funcs.append(ctx.emitter.stream)

    ctx.emitter.line(
        f"(func $user_func_{body_func_idx} "
        "(param $args (ref null eq)) (param $env (ref null $ENV)) "
        "(result (ref null eq))"
    )
    ctx.emitter.indent += 2

    # The body function receives the GENERATOR as $args
    ctx.emitter.line("(local $gen (ref $GENERATOR))")
    ctx.emitter.line("(local $state i32)")
    ctx.emitter.line("(local $locals (ref null eq))")
    ctx.emitter.line("(local $tmp (ref null eq))")

    # Declare locals for parameters and variables
    for param_name in param_names:
        local_wasm_name = f"$var_{param_name}"
        ctx.local_vars[param_name] = local_wasm_name
        ctx.emitter.line(f"(local {local_wasm_name} (ref null eq))")

    local_names = all_local_names - set(param_names) - global_decls - nonlocal_decls
    for var_name in sorted(local_names):
        local_wasm_name = f"$var_{var_name}"
        ctx.local_vars[var_name] = local_wasm_name
        ctx.emitter.line(f"(local {local_wasm_name} (ref null eq))")

    # Declare all iterator locals (yield from + complex for loops)
    # Combine and deduplicate to avoid duplicate declarations
    all_iter_locals = yieldfrom_iter_locals | collect_iter_locals(body)
    for iter_local in sorted(all_iter_locals):
        ctx.emitter.line(f"(local {iter_local} (ref null eq))")

    # Prologue: unpack generator state
    ctx.emitter.comment("unpack generator")
    ctx.emitter.line("(local.set $gen (ref.cast (ref $GENERATOR) (local.get $args)))")
    ctx.emitter.line(
        "(local.set $state (struct.get $GENERATOR $state (local.get $gen)))"
    )
    ctx.emitter.line(
        "(local.set $locals (struct.get $GENERATOR $locals (local.get $gen)))"
    )

    # Check if this is a simple linear generator
    is_simple = _is_simple_generator(body)

    if is_simple:
        # Simple case: linear yields only
        # Restore parameters from $locals (stored as PAIR chain)
        if param_names:
            ctx.emitter.comment("restore parameters")
            ctx.emitter.line("(local.set $tmp (local.get $locals))")
            for param_name in param_names:
                ctx.emitter.line(
                    f"(local.set {ctx.local_vars[param_name]} "
                    "(struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $tmp))))"
                )
                ctx.emitter.line(
                    "(local.set $tmp "
                    "(struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $tmp))))"
                )
        # Compile the generator body as a simple state machine
        _compile_generator_body_simple(body, yield_points, num_yields, ctx)
    else:
        # Complex case: yields inside loops - use loop-aware compilation
        # First, restore parameters from $locals (always needed)
        if param_names:
            ctx.emitter.comment("restore parameters")
            ctx.emitter.line("(local.set $tmp (local.get $locals))")
            for param_name in param_names:
                ctx.emitter.line(
                    f"(local.set {ctx.local_vars[param_name]} "
                    "(struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $tmp))))"
                )
                ctx.emitter.line(
                    "(local.set $tmp "
                    "(struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $tmp))))"
                )
        _compile_generator_body_with_loops(
            body, all_local_names, param_names, yieldfrom_iter_locals, ctx
        )

    ctx.emitter.indent -= 2
    ctx.emitter.line(")")

    # Restore stream for wrapper function
    ctx.emitter.stream = saved_stream
    ctx.emitter.indent = saved_indent
    ctx.local_vars = saved_locals

    # Now compile the wrapper function (creates and returns GENERATOR)
    ctx.emitter.stream = StringIO()
    ctx.emitter.indent = 0
    wrapper_func_idx = len(ctx.user_funcs)
    ctx.user_funcs.append(ctx.emitter.stream)

    ctx.emitter.line(
        f"(func $user_func_{wrapper_func_idx} "
        "(param $args (ref null eq)) (param $env (ref null $ENV)) "
        "(result (ref null eq))"
    )
    ctx.emitter.indent += 2

    ctx.emitter.line("(local $locals (ref null eq))")
    ctx.emitter.line("(local $tmp (ref null eq))")
    ctx.emitter.line("(local $val (ref null eq))")

    # Pack parameters into $locals chain: first_param -> second_param -> ... -> null
    # struct.new $PAIR with stack [car, cdr] creates PAIR(car, cdr)
    if param_names:
        ctx.emitter.comment("pack parameters into locals chain")
        n_params = len(param_names)

        if n_params == 1:
            # Single param: PAIR(param, null)
            ctx.emitter.line("(local.get $args)")
            ctx.emitter.line("(struct.get $PAIR 0 (ref.cast (ref $PAIR)))")
            ctx.emitter.emit_null_eq()
            ctx.emitter.emit_struct_new("$PAIR")
            ctx.emitter.line("(local.set $locals)")
        else:
            # Multiple params: build chain from last to first
            # First create PAIR(last_param, null)
            ctx.emitter.line("(local.get $args)")
            for _ in range(n_params - 1):
                ctx.emitter.line("(struct.get $PAIR 1 (ref.cast (ref $PAIR)))")
            ctx.emitter.line("(struct.get $PAIR 0 (ref.cast (ref $PAIR)))")
            ctx.emitter.emit_null_eq()
            ctx.emitter.emit_struct_new("$PAIR")

            # Then prepend remaining params from second-to-last to first
            for i in range(n_params - 2, -1, -1):
                ctx.emitter.line("(local.set $tmp)")  # save current chain
                ctx.emitter.line("(local.get $args)")
                for _ in range(i):
                    ctx.emitter.line("(struct.get $PAIR 1 (ref.cast (ref $PAIR)))")
                ctx.emitter.line("(struct.get $PAIR 0 (ref.cast (ref $PAIR)))")
                ctx.emitter.line("(local.get $tmp)")  # previous chain as cdr
                ctx.emitter.emit_struct_new("$PAIR")

            ctx.emitter.line("(local.set $locals)")
    else:
        ctx.emitter.emit_null_eq()
        ctx.emitter.line("(local.set $locals)")

    # Create and return GENERATOR
    ctx.emitter.comment("create generator object")
    table_idx = len(BUILTINS) + body_func_idx
    ctx.emitter.line("(struct.new $GENERATOR")
    ctx.emitter.line("  (i32.const 0)  ;; initial state")
    ctx.emitter.emit_null_eq()
    ctx.emitter.line("  ;; no value yet")
    ctx.emitter.line("  (local.get $locals)  ;; saved locals")
    ctx.emitter.line(f"  (i32.const {table_idx})  ;; body func index")
    ctx.emitter.line("  (local.get $env)  ;; environment")
    ctx.emitter.emit_null_eq()
    ctx.emitter.line("  ;; no sent value yet")
    ctx.emitter.line(")")

    ctx.emitter.indent -= 2
    ctx.emitter.line(")")

    # Restore state
    ctx.emitter.stream = saved_stream
    ctx.emitter.indent = saved_indent
    ctx.local_vars = saved_locals
    ctx.current_global_decls = saved_global_decls
    ctx.current_nonlocal_decls = saved_nonlocal_decls

    # Emit code to create closure and assign to local
    if name not in ctx.local_vars:
        local_wasm_name = f"$var_{name}"
        ctx.local_vars[name] = local_wasm_name

    table_idx = len(BUILTINS) + wrapper_func_idx
    ctx.emitter.comment(f"generator function '{name}'")
    ctx.emitter.line(f"(struct.new $CLOSURE (local.get $env) (i32.const {table_idx}))")
    ctx.emitter.emit_local_set(ctx.local_vars[name])

    # Also set global if it's a module-level function
    if name in ctx.global_vars:
        ctx.emitter.emit_local_get(ctx.local_vars[name])
        ctx.emitter.emit_global_set(f"$global_{name}")


def _compile_generator_body_simple(
    body: list[ast.stmt],
    yield_points: list[ast.Yield | ast.YieldFrom],
    num_yields: int,
    ctx: CompilerContext,
) -> None:
    """Compile generator body as a simple state machine.

    This handles generators with linear yield sequences (no loops).
    """
    ctx.emitter.comment("state machine dispatch")

    # Create block structure for state dispatch
    ctx.emitter.line("(block $exhausted")
    ctx.emitter.indent += 1

    for i in range(num_yields):
        ctx.emitter.line(f"(block $state_{i}")
        ctx.emitter.indent += 1

    # br_table dispatch
    ctx.emitter.line("(local.get $state)")
    targets = " ".join(f"$state_{i}" for i in range(num_yields))
    ctx.emitter.line(f"(br_table {targets} $exhausted)")

    # Close blocks and emit state code
    for i in range(num_yields - 1, -1, -1):
        ctx.emitter.indent -= 1
        ctx.emitter.line(f")  ;; end state_{i}")

        ctx.emitter.comment(f"state {i}")
        # Emit yield value
        yield_node = yield_points[i]
        if isinstance(yield_node, ast.Yield) and yield_node.value:
            compile_expr(yield_node.value, ctx)
        else:
            ctx.emitter.emit_null_eq()

        # Update state to next
        next_state = i + 1 if i + 1 < num_yields else -1
        ctx.emitter.line(
            f"(struct.set $GENERATOR $state (local.get $gen) (i32.const {next_state}))"
        )
        ctx.emitter.line("(return)")

    # Exhausted state
    ctx.emitter.indent -= 1
    ctx.emitter.line(")  ;; end exhausted")
    ctx.emitter.comment("exhausted")
    ctx.emitter.line("(struct.set $GENERATOR $state (local.get $gen) (i32.const -1))")
    ctx.emitter.emit_null_eq()


def _is_simple_generator(body: list[ast.stmt]) -> bool:
    """Check if generator body is simple linear yields only.

    Returns True only if the body is a sequence of:
    - Expression statements containing Yield
    - Simple assignments (not containing Yield)

    Returns False if there's any control flow (if/while/for/try/with).
    """
    for stmt in body:
        match stmt:
            case ast.Expr(value=ast.Yield()):
                # Simple yield statement - OK
                continue
            case ast.Assign():
                # Assignment - check if it contains a yield
                class HasYield(ast.NodeVisitor):
                    def __init__(self) -> None:
                        self.found = False

                    def visit_Yield(self, node: ast.Yield) -> None:  # noqa: ARG002
                        self.found = True

                visitor = HasYield()
                visitor.visit(stmt)
                if visitor.found:
                    # Yield in assignment - not simple
                    return False
                # Regular assignment - OK
                continue
            case ast.Return():
                # Return is OK (ends generator)
                continue
            case ast.Pass():
                # Pass is OK
                continue
            case _:
                # Any other statement type (if, while, for, etc.) - not simple
                return False
    return True


def _compile_generator_body_with_loops(
    body: list[ast.stmt],
    all_local_names: set[str],
    param_names: list[str],
    yieldfrom_iter_locals: set[str],
    ctx: CompilerContext,
) -> None:
    """Compile generator body that contains while loops with yields.

    Uses a loop-based state machine:
    - State 0: Initial entry, executes code from beginning
    - State 1: Resume inside loop (after yield)

    The key insight is that after resuming, we need to continue
    executing the rest of the loop body and then re-check the condition.
    """
    ctx.emitter.comment("generator with loop - state machine")

    # Local names include both regular locals and iterator locals for yield from
    local_names_list = sorted(all_local_names - set(param_names))

    # Combine all iterator locals (yield from + complex for loops)
    all_iter_locals = yieldfrom_iter_locals | collect_iter_locals(body)

    # Set up generator context for yield compilation
    ctx.generator_context = GeneratorContext(
        gen_local="$gen",
        state_local="$state",
        locals_local="$locals",
        param_names=param_names,
        local_names=local_names_list,
        yield_count=0,
        iter_locals=sorted(all_iter_locals),
    )

    ctx.emitter.line("(block $gen_exit")
    ctx.emitter.indent += 1

    def _contains_yield(node: ast.stmt) -> bool:
        """Check if a statement contains any yield."""
        for child in ast.walk(node):
            if isinstance(child, (ast.Yield, ast.YieldFrom)):
                return True
        return False

    for stmt in body:
        match stmt:
            case ast.While():
                # While loop has its own state dispatch
                _compile_generator_stmt_v2(stmt, ctx)
            case ast.For():
                # For loop has its own state dispatch (for yield from)
                _compile_generator_stmt_v2(stmt, ctx)
            case ast.Expr(value=ast.Yield()):
                # Standalone yield expression - needs state-aware dispatch
                gen_ctx = ctx.generator_context
                assert gen_ctx is not None
                next_state = gen_ctx.yield_count + 1  # peek at next state

                # Check for resume at this yield - restore and continue
                ctx.emitter.line(
                    f"(if (i32.eq (local.get $state) (i32.const {next_state}))"
                )
                ctx.emitter.line("  (then")
                ctx.emitter.indent += 2
                ctx.emitter.comment(
                    f"resume at yield {next_state}: restore and continue"
                )
                _emit_restore_all_locals(ctx)
                ctx.emitter.line("(local.set $state (i32.const 0))")
                ctx.emitter.indent -= 2
                ctx.emitter.line("  )")
                ctx.emitter.line("  (else")
                ctx.emitter.indent += 2
                # Only run yield on initial (state=0) or if skipping (state > next_state)
                ctx.emitter.line("(if (i32.eqz (local.get $state))")
                ctx.emitter.line("  (then")
                ctx.emitter.indent += 2
                _compile_generator_stmt_v2(stmt, ctx)
                ctx.emitter.indent -= 2
                ctx.emitter.line("  )")
                ctx.emitter.line(")")
                ctx.emitter.indent -= 2
                ctx.emitter.line("  )")
                ctx.emitter.line(")")
            case ast.Assign(targets=targets, value=ast.Yield() as yield_expr):
                # Yield with assignment target - need to assign sent_value on resume
                gen_ctx = ctx.generator_context
                assert gen_ctx is not None
                next_state = gen_ctx.yield_count + 1  # peek at next state

                # Check for resume at this yield - restore, assign sent_value, continue
                ctx.emitter.line(
                    f"(if (i32.eq (local.get $state) (i32.const {next_state}))"
                )
                ctx.emitter.line("  (then")
                ctx.emitter.indent += 2
                ctx.emitter.comment(
                    f"resume at yield {next_state}: restore, assign sent_value"
                )
                _emit_restore_all_locals(ctx)
                # Read sent_value and assign to target(s)
                _emit_read_sent_value(targets, ctx)
                ctx.emitter.line("(local.set $state (i32.const 0))")
                ctx.emitter.indent -= 2
                ctx.emitter.line("  )")
                ctx.emitter.line("  (else")
                ctx.emitter.indent += 2
                # Only run yield on initial (state=0) or if skipping (state > next_state)
                ctx.emitter.line("(if (i32.eqz (local.get $state))")
                ctx.emitter.line("  (then")
                ctx.emitter.indent += 2
                _emit_yield_v2(yield_expr, ctx)
                ctx.emitter.indent -= 2
                ctx.emitter.line("  )")
                ctx.emitter.line(")")
                ctx.emitter.indent -= 2
                ctx.emitter.line("  )")
                ctx.emitter.line(")")
            case _:
                # Non-yield statements only run on state 0
                ctx.emitter.line("(if (i32.eqz (local.get $state))")
                ctx.emitter.line("  (then")
                ctx.emitter.indent += 2
                _compile_generator_stmt_v2(stmt, ctx)
                ctx.emitter.indent -= 2
                ctx.emitter.line("  )")
                ctx.emitter.line(")")

    # If we reach here, generator is exhausted
    ctx.emitter.line("(br $gen_exit)")

    ctx.emitter.indent -= 1
    ctx.emitter.line(")  ;; end gen_exit")

    # Exhausted - throw StopIteration
    ctx.emitter.comment("generator exhausted")
    ctx.emitter.line("(struct.set $GENERATOR $state (local.get $gen) (i32.const -1))")
    ctx.emitter.line("(throw $StopIteration)")

    # Clean up generator context
    ctx.generator_context = None


def _compile_generator_stmt_v2(stmt: ast.stmt, ctx: CompilerContext) -> None:
    """Compile a statement in generator context (v2 - better loop handling)."""
    match stmt:
        case ast.Expr(value=ast.Yield() as yield_expr):
            _emit_yield_v2(yield_expr, ctx)
        case ast.Assign(value=ast.Yield() as yield_expr):
            _emit_yield_v2(yield_expr, ctx)
        case ast.While(test=test, body=while_body):
            _compile_generator_while_v2(test, while_body, ctx)
        case ast.For(target=target, iter=iter_expr, body=for_body):
            _compile_generator_for_v2(target, iter_expr, for_body, ctx)
        case ast.If(test=test, body=if_body, orelse=else_body):
            ctx.emitter.comment("if")
            compile_expr(test, ctx)
            ctx.emitter.line("(call $is_false)")
            ctx.emitter.line("(i32.eqz)")
            ctx.emitter.line("(if")
            ctx.emitter.line("  (then")
            ctx.emitter.indent += 2
            for s in if_body:
                _compile_generator_stmt_v2(s, ctx)
            ctx.emitter.indent -= 2
            ctx.emitter.line("  )")
            if else_body:
                ctx.emitter.line("  (else")
                ctx.emitter.indent += 2
                for s in else_body:
                    _compile_generator_stmt_v2(s, ctx)
                ctx.emitter.indent -= 2
                ctx.emitter.line("  )")
            ctx.emitter.line(")")
        case _:
            compile_stmt(stmt, ctx)


def _compile_generator_while_v2(
    test: ast.expr, while_body: list[ast.stmt], ctx: CompilerContext
) -> None:
    """Compile a while loop in generator context (v2 - proper resume)."""
    gen_ctx = ctx.generator_context
    if gen_ctx is None:
        compile_stmt(ast.While(test=test, body=while_body, orelse=[]), ctx)
        return

    ctx.emitter.comment("generator while loop")

    # Find the yield statement in the body (either bare yield or yield assignment)
    pre_yield: list[ast.stmt] = []
    yield_stmt: ast.Yield | None = None
    yield_assign_targets: list[ast.expr] | None = None
    post_yield: list[ast.stmt] = []

    found_yield = False
    for stmt in while_body:
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Yield):
            yield_stmt = stmt.value
            found_yield = True
        elif isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Yield):
            yield_stmt = stmt.value
            yield_assign_targets = stmt.targets
            found_yield = True
        elif found_yield:
            post_yield.append(stmt)
        else:
            pre_yield.append(stmt)

    if yield_stmt is None:
        # No yield in while body - compile normally
        compile_stmt(ast.While(test=test, body=while_body, orelse=[]), ctx)
        return

    ctx.emitter.line("(block $while_exit")
    ctx.emitter.indent += 1
    ctx.emitter.line("(loop $while_loop_top")
    ctx.emitter.indent += 1

    ctx.emitter.line("(block $skip_to_post_yield")
    ctx.emitter.indent += 1
    ctx.emitter.line("(block $do_preyield")
    ctx.emitter.indent += 1

    ctx.emitter.line("(br_if $do_preyield (i32.eqz (local.get $state)))")

    # state >= 1: restore locals and skip to post-yield
    ctx.emitter.comment("resume: restore locals and skip to post-yield")
    _emit_restore_all_locals(ctx)

    # If this was a yield assignment, read sent_value and assign to target
    if yield_assign_targets:
        _emit_read_sent_value(yield_assign_targets, ctx)

    ctx.emitter.line("(local.set $state (i32.const 0))  ;; reset for next iteration")
    ctx.emitter.line("(br $skip_to_post_yield)")

    ctx.emitter.indent -= 1
    ctx.emitter.line(")  ;; end $do_preyield")

    # State was 0: check condition, run pre-yield, yield
    ctx.emitter.comment("state 0: check condition")
    compile_expr(test, ctx)
    ctx.emitter.line("(call $is_false)")
    ctx.emitter.line("(br_if $while_exit)")

    # Pre-yield code
    if pre_yield:
        ctx.emitter.comment("pre-yield code")
        for stmt in pre_yield:
            _compile_generator_stmt_v2(stmt, ctx)

    # Yield
    ctx.emitter.comment("yield")
    _emit_save_all_locals(ctx)
    ctx.emitter.line("(struct.set $GENERATOR $state (local.get $gen) (i32.const 1))")
    if yield_stmt.value:
        compile_expr(yield_stmt.value, ctx)
    else:
        ctx.emitter.emit_null_eq()
    ctx.emitter.line("(return)")

    ctx.emitter.indent -= 1
    ctx.emitter.line(")  ;; end $skip_to_post_yield")

    # Post-yield code (reached after resume)
    if post_yield:
        ctx.emitter.comment("post-yield code")
        for stmt in post_yield:
            _compile_generator_stmt_v2(stmt, ctx)

    # Loop back to top
    ctx.emitter.line("(br $while_loop_top)")

    ctx.emitter.indent -= 1
    ctx.emitter.line(")  ;; end loop")
    ctx.emitter.indent -= 1
    ctx.emitter.line(")  ;; end block")


def _compile_generator_for_complex(
    target: ast.expr,
    iter_expr: ast.expr,
    for_body: list[ast.stmt],
    ctx: CompilerContext,
) -> None:
    """Compile a complex for loop in generator context."""
    if not isinstance(target, ast.Name):
        msg = "Complex generator for loops only support simple name targets"
        raise NotImplementedError(msg)

    var_name = target.id
    iter_local = f"$iter_{var_name}"

    # Check for range()
    if (
        isinstance(iter_expr, ast.Call)
        and isinstance(iter_expr.func, ast.Name)
        and iter_expr.func.id == "range"
    ):
        _compile_generator_for_range(var_name, iter_expr.args, for_body, ctx)
        return

    # General iterable for loop
    ctx.emitter.comment("generator complex for loop")

    ctx.emitter.emit_block_start("$for_exit")

    # State dispatch: check if resuming from a yield
    ctx.emitter.line("(if (i32.eqz (local.get $state))")
    ctx.emitter.line("  (then")
    ctx.emitter.indent += 2
    ctx.emitter.comment("state=0: initialize iterator")
    compile_expr(iter_expr, ctx)
    ctx.emitter.emit_call("$iter_prepare")
    ctx.emitter.emit_local_set(iter_local)
    ctx.emitter.indent -= 2
    ctx.emitter.line("  )")
    ctx.emitter.line("  (else")
    ctx.emitter.indent += 2
    ctx.emitter.comment("state>0: restore all locals, skip body")
    _emit_restore_all_locals(ctx)
    ctx.emitter.line("(local.set $state (i32.const 0))")
    ctx.emitter.indent -= 2
    ctx.emitter.line("  )")
    ctx.emitter.line(")")

    ctx.emitter.emit_loop_start("$for_loop")

    # Check if iterator is null (exhausted)
    ctx.emitter.emit_local_get(iter_local)
    ctx.emitter.emit_ref_is_null()
    ctx.emitter.emit_br_if("$for_exit")

    # Get item from PAIR[0] (car)
    ctx.emitter.emit_local_get(iter_local)
    ctx.emitter.emit_ref_cast("$PAIR")
    ctx.emitter.emit_struct_get("$PAIR", 0)
    if var_name in ctx.local_vars:
        ctx.emitter.emit_local_set(ctx.local_vars[var_name])
    else:
        ctx.emitter.line(f"(local.set $var_{var_name})")

    # Move iterator to PAIR[1] (cdr)
    ctx.emitter.emit_local_get(iter_local)
    ctx.emitter.emit_ref_cast("$PAIR")
    ctx.emitter.emit_struct_get("$PAIR", 1)
    ctx.emitter.emit_local_set(iter_local)

    # Compile body statements with generator-aware compilation
    for stmt in for_body:
        _compile_generator_stmt_v2(stmt, ctx)

    ctx.emitter.emit_br("$for_loop")
    ctx.emitter.emit_loop_end()
    ctx.emitter.emit_block_end()


def _compile_generator_for_range(
    name: str,
    args: list[ast.expr],
    body: list[ast.stmt],
    ctx: CompilerContext,
) -> None:
    """Compile for loop with range() in generator context."""
    ctx.emitter.comment("generator for loop over range")

    # Parse range arguments
    start: ast.expr
    stop: ast.expr
    step: ast.expr
    if len(args) == 1:
        start = ast.Constant(value=0)
        stop = args[0]
        step = ast.Constant(value=1)
    elif len(args) == 2:
        start = args[0]
        stop = args[1]
        step = ast.Constant(value=1)
    elif len(args) == 3:
        start = args[0]
        stop = args[1]
        step = args[2]
    else:
        msg = f"range() takes 1-3 arguments, got {len(args)}"
        raise ValueError(msg)

    if name not in ctx.local_vars:
        msg = f"Loop variable '{name}' not declared"
        raise NameError(msg)
    counter_local = ctx.local_vars[name]

    ctx.emitter.emit_block_start("$for_exit")

    # State dispatch: check if resuming from a yield
    ctx.emitter.line("(if (i32.eqz (local.get $state))")
    ctx.emitter.line("  (then")
    ctx.emitter.indent += 2
    ctx.emitter.comment("state=0: initialize loop variable")
    compile_expr(start, ctx)
    ctx.emitter.emit_local_set(counter_local)
    ctx.emitter.indent -= 2
    ctx.emitter.line("  )")
    ctx.emitter.line("  (else")
    ctx.emitter.indent += 2
    ctx.emitter.comment("state>0: restore all locals, skip body")
    _emit_restore_all_locals(ctx)
    ctx.emitter.line("(local.set $state (i32.const 0))")
    # Increment immediately (skip body) and start normal loop
    ctx.emitter.emit_local_get(counter_local)
    ctx.emitter.emit_i31_get_s()
    compile_expr(step, ctx)
    ctx.emitter.emit_i31_get_s()
    ctx.emitter.line("i32.add")
    ctx.emitter.emit_ref_i31()
    ctx.emitter.emit_local_set(counter_local)
    ctx.emitter.indent -= 2
    ctx.emitter.line("  )")
    ctx.emitter.line(")")

    ctx.emitter.emit_loop_start("$for_loop")

    # Check loop condition
    ctx.emitter.emit_local_get(counter_local)
    ctx.emitter.emit_i31_get_s()
    compile_expr(stop, ctx)
    ctx.emitter.emit_i31_get_s()
    ctx.emitter.line("i32.ge_s")
    ctx.emitter.emit_br_if("$for_exit")

    # Compile body statements with generator-aware compilation
    for stmt in body:
        _compile_generator_stmt_v2(stmt, ctx)

    # Increment counter
    ctx.emitter.emit_local_get(counter_local)
    ctx.emitter.emit_i31_get_s()
    compile_expr(step, ctx)
    ctx.emitter.emit_i31_get_s()
    ctx.emitter.line("i32.add")
    ctx.emitter.emit_ref_i31()
    ctx.emitter.emit_local_set(counter_local)

    ctx.emitter.emit_br("$for_loop")
    ctx.emitter.emit_loop_end()
    ctx.emitter.emit_block_end()


def _compile_generator_for_v2(
    target: ast.expr,
    iter_expr: ast.expr,
    for_body: list[ast.stmt],
    ctx: CompilerContext,
) -> None:
    """Compile a for loop in generator context."""
    gen_ctx = ctx.generator_context
    if gen_ctx is None:
        # Fallback to regular for loop compilation
        compile_stmt(
            ast.For(target=target, iter=iter_expr, body=for_body, orelse=[]), ctx
        )
        return

    # Check if this is a simple yield-only loop (from yield from transformation)
    is_simple_yield_loop = (
        len(for_body) == 1
        and isinstance(for_body[0], ast.Expr)
        and isinstance(for_body[0].value, ast.Yield)
    )

    if not is_simple_yield_loop:
        _compile_generator_for_complex(target, iter_expr, for_body, ctx)
        return

    # Get target variable name
    if not isinstance(target, ast.Name):
        compile_stmt(
            ast.For(target=target, iter=iter_expr, body=for_body, orelse=[]), ctx
        )
        return

    var_name = target.id
    iter_local = f"$iter_{var_name}"

    # Type is already narrowed by is_simple_yield_loop check above
    first_stmt = for_body[0]
    assert isinstance(first_stmt, ast.Expr)
    yield_stmt = first_stmt.value
    assert isinstance(yield_stmt, ast.Yield)

    # Get unique state number for this for loop
    gen_ctx = ctx.generator_context
    if gen_ctx is None:
        compile_stmt(
            ast.For(target=target, iter=iter_expr, body=for_body, orelse=[]), ctx
        )
        return
    gen_ctx.yield_count += 1
    for_loop_state = gen_ctx.yield_count

    ctx.emitter.comment(f"generator for loop (yield from) - state {for_loop_state}")

    # Skip this for loop if resuming past it (state > for_loop_state)
    ctx.emitter.line(f"(if (i32.gt_s (local.get $state) (i32.const {for_loop_state}))")
    ctx.emitter.line("  (then")
    ctx.emitter.line("  )  ;; skip this for loop")
    ctx.emitter.line("  (else")
    ctx.emitter.indent += 2

    ctx.emitter.line("(block $for_exit")
    ctx.emitter.indent += 1

    # Check state to determine whether to initialize or restore
    ctx.emitter.line(f"(if (i32.eq (local.get $state) (i32.const {for_loop_state}))")
    ctx.emitter.line("  (then")
    ctx.emitter.indent += 2
    ctx.emitter.comment("resuming: restore all locals (including iterator)")
    _emit_restore_all_locals(ctx)
    ctx.emitter.line("(local.set $state (i32.const 0))")
    ctx.emitter.indent -= 2
    ctx.emitter.line("  )")
    ctx.emitter.line("  (else")
    ctx.emitter.indent += 2
    ctx.emitter.comment("initial: initialize iterator")
    compile_expr(iter_expr, ctx)
    ctx.emitter.emit_call("$iter_prepare")
    ctx.emitter.emit_local_set(iter_local)
    ctx.emitter.indent -= 2
    ctx.emitter.line("  )")
    ctx.emitter.line(")")

    ctx.emitter.line("(loop $for_loop_top")
    ctx.emitter.indent += 1

    # Check if iterator is null (exhausted)
    ctx.emitter.emit_local_get(iter_local)
    ctx.emitter.emit_ref_is_null()
    ctx.emitter.line("(br_if $for_exit)")

    # Get item from PAIR[0] (car)
    ctx.emitter.emit_local_get(iter_local)
    ctx.emitter.emit_ref_cast("$PAIR")
    ctx.emitter.emit_struct_get("$PAIR", 0)
    if var_name in ctx.local_vars:
        ctx.emitter.emit_local_set(ctx.local_vars[var_name])
    else:
        ctx.emitter.line(f"(local.set $var_{var_name})")

    # Move iterator to PAIR[1] (cdr)
    ctx.emitter.emit_local_get(iter_local)
    ctx.emitter.emit_ref_cast("$PAIR")
    ctx.emitter.emit_struct_get("$PAIR", 1)
    ctx.emitter.emit_local_set(iter_local)

    # Save all locals (including iterator) before yielding
    ctx.emitter.comment("save all locals and yield")
    _emit_save_all_locals(ctx)
    ctx.emitter.line(
        f"(struct.set $GENERATOR $state (local.get $gen) (i32.const {for_loop_state}))"
    )

    # Yield the value
    if yield_stmt.value:
        compile_expr(yield_stmt.value, ctx)
    else:
        ctx.emitter.emit_null_eq()
    ctx.emitter.line("(return)")

    ctx.emitter.indent -= 1
    ctx.emitter.line(")  ;; end loop")
    ctx.emitter.indent -= 1
    ctx.emitter.line(")  ;; end for_exit block")
    ctx.emitter.indent -= 2
    ctx.emitter.line("  )")
    ctx.emitter.line(")  ;; end state check")


def _emit_yield_v2(yield_expr: ast.Yield, ctx: CompilerContext) -> None:
    """Emit code for a yield expression (v2)."""
    gen_ctx = ctx.generator_context
    if gen_ctx is None:
        if yield_expr.value:
            compile_expr(yield_expr.value, ctx)
        else:
            ctx.emitter.emit_null_eq()
        return

    # Get unique state number for this yield
    gen_ctx.yield_count += 1
    yield_state = gen_ctx.yield_count

    ctx.emitter.comment(f"yield (state {yield_state})")
    _emit_save_all_locals(ctx)
    ctx.emitter.line(
        f"(struct.set $GENERATOR $state (local.get {gen_ctx.gen_local}) (i32.const {yield_state}))"
    )
    if yield_expr.value:
        compile_expr(yield_expr.value, ctx)
    else:
        ctx.emitter.emit_null_eq()
    ctx.emitter.line("(return)")


def _emit_save_all_locals(ctx: CompilerContext) -> None:
    """Emit code to save all local variables to generator's locals field."""
    gen_ctx = ctx.generator_context
    if gen_ctx is None:
        return

    # Include iterator locals for yield from
    all_vars = gen_ctx.param_names + gen_ctx.local_names + gen_ctx.iter_locals
    if not all_vars:
        ctx.emitter.line(
            f"(struct.set $GENERATOR $locals (local.get {gen_ctx.gen_local}) (ref.null eq))"
        )
        return

    ctx.emitter.comment("save all locals")
    n_vars = len(all_vars)

    def _get_var_local(var: str) -> str:
        """Get the WASM local name for a variable."""
        if var.startswith("$iter_"):
            return var
        if var in ctx.local_vars:
            return ctx.local_vars[var]
        return f"$var_{var}"

    if n_vars == 1:
        # Single var: PAIR(var, null)
        var_name = all_vars[0]
        ctx.emitter.line(f"(local.get {gen_ctx.gen_local})")
        ctx.emitter.emit_local_get(_get_var_local(var_name))
        ctx.emitter.emit_null_eq()
        ctx.emitter.emit_struct_new("$PAIR")
        ctx.emitter.line("(struct.set $GENERATOR $locals)")
    else:
        # Multiple vars: build chain from last to first
        last_var = all_vars[-1]
        ctx.emitter.emit_local_get(_get_var_local(last_var))
        ctx.emitter.emit_null_eq()
        ctx.emitter.emit_struct_new("$PAIR")

        for i in range(n_vars - 2, -1, -1):
            ctx.emitter.line("(local.set $tmp)")
            var_name = all_vars[i]
            ctx.emitter.emit_local_get(_get_var_local(var_name))
            ctx.emitter.line("(local.get $tmp)")
            ctx.emitter.emit_struct_new("$PAIR")

        ctx.emitter.line("(local.set $tmp)")
        ctx.emitter.line(f"(local.get {gen_ctx.gen_local})")
        ctx.emitter.line("(local.get $tmp)")
        ctx.emitter.line("(struct.set $GENERATOR $locals)")


def _emit_restore_all_locals(ctx: CompilerContext) -> None:
    """Emit code to restore all local variables from generator's locals field."""
    gen_ctx = ctx.generator_context
    if gen_ctx is None:
        return

    all_vars = gen_ctx.param_names + gen_ctx.local_names + gen_ctx.iter_locals
    if not all_vars:
        return

    def _get_var_local(var: str) -> str:
        """Get the WASM local name for a variable."""
        if var.startswith("$iter_"):
            return var
        if var in ctx.local_vars:
            return ctx.local_vars[var]
        return f"$var_{var}"

    ctx.emitter.comment("restore all locals")
    ctx.emitter.line(
        f"(local.set $tmp (struct.get $GENERATOR $locals (local.get {gen_ctx.gen_local})))"
    )
    for var_name in all_vars:
        local_name = _get_var_local(var_name)
        ctx.emitter.line(
            f"(local.set {local_name} "
            "(struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $tmp))))"
        )
        ctx.emitter.line(
            "(local.set $tmp "
            "(struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $tmp))))"
        )


def _emit_read_sent_value(targets: list[ast.expr], ctx: CompilerContext) -> None:
    """Emit code to read sent_value from generator and assign to target variables.

    This is called on resume after a yield assignment like: result = yield value
    The sent_value contains what was passed to generator.send(value).
    """
    gen_ctx = ctx.generator_context
    if gen_ctx is None:
        return

    ctx.emitter.comment("read sent_value and assign to target")

    # Read $sent_value from the generator
    ctx.emitter.line(
        f"(struct.get $GENERATOR $sent_value (local.get {gen_ctx.gen_local}))"
    )

    # For now, support single Name target
    if len(targets) == 1 and isinstance(targets[0], ast.Name):
        var_name = targets[0].id
        if var_name in ctx.local_vars:
            ctx.emitter.emit_local_set(ctx.local_vars[var_name])
        else:
            ctx.emitter.line(f"(local.set $var_{var_name})")
    else:
        # Drop the value for unsupported target patterns
        ctx.emitter.line("(drop)")

    # Clear sent_value after reading (set to null)
    ctx.emitter.line(
        f"(struct.set $GENERATOR $sent_value (local.get {gen_ctx.gen_local}) (ref.null eq))"
    )

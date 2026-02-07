"""Lambda expression compilation."""

from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING

from p2w.compiler.analysis import find_free_vars
from p2w.compiler.builtins import BUILTINS
from p2w.compiler.codegen.expressions import compile_expr
from p2w.compiler.inference import TypeInferencer

if TYPE_CHECKING:
    import ast

    from p2w.compiler.context import CompilerContext


def compile_lambda(args: ast.arguments, body: ast.expr, ctx: CompilerContext) -> None:
    """Compile lambda expression."""

    param_names = [arg.arg for arg in args.args]
    free_vars = find_free_vars(body, set(param_names))
    captured_vars = [v for v in sorted(free_vars) if v in ctx.local_vars]

    saved_stream = ctx.emitter.stream
    saved_indent = ctx.emitter.indent
    saved_locals = ctx.local_vars
    saved_inferencer = ctx.type_inferencer

    # Create type inferencer for lambda - just infer the body expression type
    inferencer = TypeInferencer()
    ctx.type_inferencer = inferencer

    ctx.emitter.stream = StringIO()
    ctx.emitter.indent = 0
    ctx.local_vars = {}
    func_idx = len(ctx.user_funcs)
    ctx.user_funcs.append(ctx.emitter.stream)

    ctx.emitter.line(
        f"(func $user_func_{func_idx} "
        "(param $args (ref null eq)) (param $env (ref null $ENV)) "
        "(result (ref null eq))"
    )
    ctx.emitter.indent += 2

    ctx.emitter.line("(local $tmp (ref null eq))")
    ctx.emitter.line("(local $tmp2 (ref null eq))")
    ctx.emitter.line("(local $chain_val (ref null eq))")
    ctx.emitter.line("(local $ftmp1 f64)")
    ctx.emitter.line("(local $ftmp2 f64)")
    # Locals for direct array iteration optimization
    ctx.emitter.line("(local $iter_source (ref null eq))")
    ctx.emitter.line("(local $list_ref (ref null $LIST))")
    ctx.emitter.line("(local $tuple_ref (ref null $TUPLE))")
    ctx.emitter.line("(local $iter_len i32)")
    ctx.emitter.line("(local $iter_idx i32)")
    # Locals for inline list access optimization
    ctx.emitter.line("(local $subscript_list_ref (ref null $LIST))")
    ctx.emitter.line(
        "(local $subscript_list_ref2 (ref null $LIST))"
    )  # For nested access
    ctx.emitter.line("(local $idx_tmp i32)")
    ctx.emitter.line("(local $len_tmp i32)")

    if captured_vars:
        ctx.lexical_env.push_frame(captured_vars)
    ctx.lexical_env.push_frame(param_names)

    for param_name in param_names:
        local_wasm_name = f"$var_{param_name}"
        ctx.local_vars[param_name] = local_wasm_name
        ctx.emitter.line(f"(local {local_wasm_name} (ref null eq))")

    ctx.emitter.comment("lambda prologue")
    ctx.emitter.line(
        "(local.set $env (struct.new $ENV (local.get $env) (local.get $args)))"
    )

    for i, param_name in enumerate(param_names):
        ctx.emitter.emit_local_get("$args")
        for _ in range(i):
            ctx.emitter.line("(struct.get $PAIR 1 (ref.cast (ref $PAIR)))  ;; cdr")
        ctx.emitter.line("(struct.get $PAIR 0 (ref.cast (ref $PAIR)))  ;; car")
        ctx.emitter.emit_local_set(ctx.local_vars[param_name])

    compile_expr(body, ctx)

    ctx.lexical_env.pop_frame()
    if captured_vars:
        ctx.lexical_env.pop_frame()

    ctx.emitter.indent -= 2
    ctx.emitter.line(")")

    ctx.emitter.stream = saved_stream
    ctx.emitter.indent = saved_indent
    ctx.local_vars = saved_locals
    ctx.type_inferencer = saved_inferencer

    if captured_vars:
        ctx.emitter.comment("capture closure variables")
        ctx.emitter.line("(local.get $env)  ;; parent env")
        for var in captured_vars:
            ctx.emitter.line(f"(local.get {ctx.local_vars[var]})  ;; capture {var}")
        ctx.emitter.emit_null_eq()
        for _ in range(len(captured_vars)):
            ctx.emitter.emit_struct_new("$PAIR")
        ctx.emitter.line("(struct.new $ENV)  ;; (parent, values)")
        table_idx = len(BUILTINS) + func_idx
        ctx.emitter.emit_i32_const(table_idx)
        ctx.emitter.comment("lambda closure with captures")
        ctx.emitter.emit_struct_new("$CLOSURE")
    else:
        table_idx = len(BUILTINS) + func_idx
        ctx.emitter.comment("lambda closure")
        ctx.emitter.line(
            f"(struct.new $CLOSURE (local.get $env) (i32.const {table_idx}))"
        )

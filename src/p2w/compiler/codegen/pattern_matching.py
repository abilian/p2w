"""Pattern matching compilation (match statement)."""

from __future__ import annotations

import ast

from p2w.compiler.codegen.expressions import compile_expr
from p2w.compiler.codegen.statements import compile_stmt
from p2w.compiler.context import CompilerContext  # noqa: TC001


@compile_stmt.register
def _match(node: ast.Match, ctx: CompilerContext) -> None:
    """Compile match statement (structural pattern matching).

    Compiles:
        match subject:
            case pattern1:
                body1
            case pattern2 if guard:
                body2
            case _:
                default_body

    Into a series of if-else checks.
    """
    ctx.emitter.comment("match statement")

    # Evaluate subject once and store it
    compile_expr(node.subject, ctx)
    ctx.emitter.emit_local_set("$tmp")

    # Generate unique labels
    label_id = ctx.next_label_id()
    match_end_label = f"$match_end_{label_id}"

    # Outer block for the entire match
    ctx.emitter.line(f"(block {match_end_label}")
    ctx.emitter.indent_inc()

    # Compile each case
    for i, case in enumerate(node.cases):
        _compile_match_case(case, ctx, match_end_label)

    # If no case matched, do nothing (fall through)
    ctx.emitter.indent_dec()
    ctx.emitter.line(")")  # end match block


def _compile_match_case(
    case: ast.match_case, ctx: CompilerContext, match_end_label: str
) -> None:
    """Compile a single match case."""
    pattern = case.pattern
    guard = case.guard
    body = case.body

    # Check if this is a wildcard pattern (always matches)
    if isinstance(pattern, ast.MatchAs) and pattern.name is None:
        # Wildcard _ - always matches
        ctx.emitter.comment("case _: (wildcard)")
        for stmt in body:
            compile_stmt(stmt, ctx)
        ctx.emitter.line(f"br {match_end_label}")
        return

    # Generate condition for the pattern
    ctx.emitter.comment("case pattern check")
    ctx.emitter.emit_local_get("$tmp")  # Get subject
    _compile_pattern_check(pattern, ctx)

    # If pattern matched, bind variables and optionally check guard
    ctx.emitter.emit_if_start()

    # Bind pattern variables first (needed for guard evaluation)
    ctx.emitter.emit_local_get("$tmp")
    _compile_pattern_bindings(pattern, ctx)

    # Check guard if present
    if guard:
        ctx.emitter.comment("guard check")
        compile_expr(guard, ctx)
        ctx.emitter.emit_call("$is_false")
        ctx.emitter.line("i32.eqz")  # truthy if NOT false
        ctx.emitter.emit_if_start()

    # Execute body
    for stmt in body:
        compile_stmt(stmt, ctx)

    # Branch to end of match
    ctx.emitter.line(f"br {match_end_label}")

    if guard:
        ctx.emitter.emit_if_end()  # end guard if

    ctx.emitter.emit_if_end()  # end pattern if


def _compile_pattern_check(pattern: ast.pattern, ctx: CompilerContext) -> None:
    """Compile a pattern check that leaves a boolean (i32) on the stack.

    Stack: [subject] -> [i32: 1 if matches, 0 if not]
    """
    match pattern:
        case ast.MatchValue(value=value):
            # Literal value comparison
            compile_expr(value, ctx)
            ctx.emitter.emit_call("$values_equal")

        case ast.MatchAs():
            # Capture pattern (always matches)
            ctx.emitter.emit_drop()  # Don't need subject for check
            ctx.emitter.emit_i32_const(1)  # Always true

        case ast.MatchOr(patterns=patterns):
            # OR pattern - any sub-pattern matches
            # We need to check each pattern without consuming the subject
            ctx.emitter.emit_local_set("$tmp2")  # Save subject
            ctx.emitter.emit_i32_const(0)  # Initialize result to false
            for sub_pattern in patterns:
                ctx.emitter.emit_local_get("$tmp2")  # Get subject
                _compile_pattern_check(sub_pattern, ctx)
                ctx.emitter.line("i32.or")  # OR with previous result

        case ast.MatchSequence(patterns=patterns):
            # Sequence pattern - check length and each element
            ctx.emitter.emit_local_set("$tmp2")  # Save subject for later

            # Check if any pattern is a star pattern
            has_star = any(isinstance(p, ast.MatchStar) for p in patterns)

            if has_star:
                # Find the star pattern index
                star_idx = next(
                    i for i, p in enumerate(patterns) if isinstance(p, ast.MatchStar)
                )
                before_count = star_idx
                after_count = len(patterns) - star_idx - 1
                min_len = before_count + after_count

                # Check minimum length (length >= min_len)
                ctx.emitter.emit_local_get("$tmp2")
                ctx.emitter.emit_call("$sequence_length")
                ctx.emitter.emit_i32_const(min_len)
                ctx.emitter.line("i32.ge_s")  # length >= minimum

                # Check patterns before the star
                for idx in range(before_count):
                    ctx.emitter.emit_if_start("i32")
                    ctx.emitter.emit_local_get("$tmp2")
                    ctx.emitter.emit_i32_const(idx)
                    ctx.emitter.emit_call("$sequence_get")
                    _compile_pattern_check(patterns[idx], ctx)
                    ctx.emitter.emit_if_else()
                    ctx.emitter.emit_i32_const(0)
                    ctx.emitter.emit_if_end()

                # Check patterns after the star (using negative indexing)
                for i in range(after_count):
                    ctx.emitter.emit_if_start("i32")
                    ctx.emitter.emit_local_get("$tmp2")
                    ctx.emitter.emit_i32_const(-(after_count - i))
                    ctx.emitter.emit_call("$sequence_get")
                    _compile_pattern_check(patterns[star_idx + 1 + i], ctx)
                    ctx.emitter.emit_if_else()
                    ctx.emitter.emit_i32_const(0)
                    ctx.emitter.emit_if_end()
            else:
                # No star - exact length match
                ctx.emitter.emit_local_get("$tmp2")
                ctx.emitter.emit_call("$sequence_length")
                ctx.emitter.emit_i32_const(len(patterns))
                ctx.emitter.line("i32.eq")  # length matches

                # For each element, check the pattern
                for idx, sub_pattern in enumerate(patterns):
                    # Only check if previous checks passed (short-circuit)
                    ctx.emitter.emit_if_start("i32")
                    ctx.emitter.emit_local_get("$tmp2")
                    ctx.emitter.emit_i32_const(idx)
                    ctx.emitter.emit_call("$sequence_get")
                    _compile_pattern_check(sub_pattern, ctx)
                    ctx.emitter.emit_if_else()
                    ctx.emitter.emit_i32_const(0)
                    ctx.emitter.emit_if_end()

        case ast.MatchMapping(keys=keys, patterns=patterns):
            # Dict pattern - check if all keys exist and values match
            ctx.emitter.emit_local_set("$tmp2")  # Save subject

            # Check if subject is a dict
            ctx.emitter.emit_local_get("$tmp2")
            ctx.emitter.emit_call("$is_dict")

            # Check each key-value pair
            for key, value_pattern in zip(keys, patterns):
                ctx.emitter.emit_if_start("i32")
                ctx.emitter.emit_local_get("$tmp2")
                compile_expr(key, ctx)
                ctx.emitter.emit_call("$dict_contains")
                # If key exists, check the value pattern
                ctx.emitter.emit_if_start("i32")
                ctx.emitter.emit_local_get("$tmp2")
                compile_expr(key, ctx)
                ctx.emitter.emit_call("$dict_get")
                _compile_pattern_check(value_pattern, ctx)
                ctx.emitter.emit_if_else()
                ctx.emitter.emit_i32_const(0)
                ctx.emitter.emit_if_end()
                ctx.emitter.emit_if_else()
                ctx.emitter.emit_i32_const(0)
                ctx.emitter.emit_if_end()

        case _:
            # Unsupported pattern - just return false
            ctx.emitter.emit_drop()
            ctx.emitter.emit_i32_const(0)


def _compile_pattern_bindings(pattern: ast.pattern, ctx: CompilerContext) -> None:
    """Bind pattern variables from the subject on the stack.

    Stack: [subject] -> []
    """
    match pattern:
        case ast.MatchAs(name=name) if name is not None:
            # Bind to variable
            if name in ctx.local_vars:
                ctx.emitter.emit_local_set(ctx.local_vars[name])
            elif name in ctx.global_vars:
                ctx.emitter.emit_global_set(f"$global_{name}")
            else:
                ctx.emitter.emit_drop()

        case ast.MatchValue():
            # No bindings
            ctx.emitter.emit_drop()

        case ast.MatchOr(patterns=patterns):
            # Bind from first pattern (they should have same bindings)
            if patterns:
                _compile_pattern_bindings(patterns[0], ctx)
            else:
                ctx.emitter.emit_drop()

        case ast.MatchSequence(patterns=patterns):
            # Bind each element
            ctx.emitter.emit_local_set("$tmp2")

            # Check if any pattern is a star pattern
            has_star = any(isinstance(p, ast.MatchStar) for p in patterns)

            if has_star:
                star_idx = next(
                    i for i, p in enumerate(patterns) if isinstance(p, ast.MatchStar)
                )
                before_count = star_idx
                after_count = len(patterns) - star_idx - 1

                # Bind patterns before the star
                for idx in range(before_count):
                    ctx.emitter.emit_local_get("$tmp2")
                    ctx.emitter.emit_i32_const(idx)
                    ctx.emitter.emit_call("$sequence_get")
                    _compile_pattern_bindings(patterns[idx], ctx)

                # Bind the star pattern (slice from before_count to -after_count)
                star_pattern = patterns[star_idx]
                if isinstance(star_pattern, ast.MatchStar) and star_pattern.name:
                    name = star_pattern.name
                    if name in ctx.local_vars:
                        ctx.emitter.emit_local_get("$tmp2")
                        ctx.emitter.emit_i32_const(before_count)
                        if after_count == 0:
                            ctx.emitter.emit_i32_const(-999999)  # sentinel for "to end"
                        else:
                            ctx.emitter.emit_i32_const(-after_count)
                        ctx.emitter.emit_i32_const(1)  # step = 1
                        ctx.emitter.emit_call("$slice")
                        ctx.emitter.emit_call("$ensure_list")
                        ctx.emitter.emit_local_set(ctx.local_vars[name])

                # Bind patterns after the star (using negative indexing)
                for i in range(after_count):
                    ctx.emitter.emit_local_get("$tmp2")
                    ctx.emitter.emit_i32_const(-(after_count - i))
                    ctx.emitter.emit_call("$sequence_get")
                    _compile_pattern_bindings(patterns[star_idx + 1 + i], ctx)
            else:
                # No star - bind each element by index
                for idx, sub_pattern in enumerate(patterns):
                    ctx.emitter.emit_local_get("$tmp2")
                    ctx.emitter.emit_i32_const(idx)
                    ctx.emitter.emit_call("$sequence_get")
                    _compile_pattern_bindings(sub_pattern, ctx)

        case ast.MatchMapping(keys=keys, patterns=patterns):
            # Bind dict pattern values
            # Note: rest (**rest capture) not yet supported
            ctx.emitter.emit_local_set("$tmp2")
            for key, value_pattern in zip(keys, patterns):
                ctx.emitter.emit_local_get("$tmp2")
                compile_expr(key, ctx)
                ctx.emitter.emit_call("$dict_get")
                _compile_pattern_bindings(value_pattern, ctx)

        case _:
            ctx.emitter.emit_drop()

"""Pre-compilation analysis for p2w.

This module provides static analysis of Python AST before emission:
- Variable collection (locals, iterators, comprehension vars)
- Free variable detection for closures
- Type inference for optimization
"""

from __future__ import annotations

import ast


def collect_target_names(target: ast.expr) -> set[str]:
    """Collect all names from an assignment target (handles tuples)."""
    names: set[str] = set()
    match target:
        case ast.Name(id=name):
            names.add(name)
        case ast.Tuple(elts=elements) | ast.List(elts=elements):
            for elt in elements:
                names.update(collect_target_names(elt))
        case ast.Starred(value=value):
            # Handle starred targets like *rest in: first, *rest = [1, 2, 3]
            names.update(collect_target_names(value))
        case ast.Subscript():
            pass  # Subscript targets don't introduce new names
    return names


def collect_pattern_names(pattern: ast.pattern) -> set[str]:
    """Collect all variable names bound by a match pattern."""
    names: set[str] = set()
    match pattern:
        case ast.MatchAs(name=name) if name is not None:
            names.add(name)
        case ast.MatchOr(patterns=patterns):
            # All alternatives must bind same names; collect from first
            if patterns:
                names.update(collect_pattern_names(patterns[0]))
        case ast.MatchSequence(patterns=patterns):
            for p in patterns:
                names.update(collect_pattern_names(p))
        case ast.MatchStar(name=name) if name is not None:
            names.add(name)
        case ast.MatchMapping(keys=_, patterns=patterns, rest=rest):
            for p in patterns:
                names.update(collect_pattern_names(p))
            if rest is not None:
                names.add(rest)
        case ast.MatchClass(patterns=patterns, kwd_patterns=kwd_patterns):
            for p in patterns:
                names.update(collect_pattern_names(p))
            for p in kwd_patterns:
                names.update(collect_pattern_names(p))
    return names


def collect_local_vars(body: list[ast.stmt]) -> set[str]:
    """Collect all variable names assigned in a function body.

    This does a shallow scan - it doesn't recurse into nested functions.
    """
    names: set[str] = set()
    for stmt in body:
        match stmt:
            case ast.Assign(targets=targets):
                for target in targets:
                    names.update(collect_target_names(target))
            case ast.AugAssign(target=ast.Name(id=name)):
                names.add(name)
            case ast.AnnAssign(target=ast.Name(id=name)):
                names.add(name)
            case ast.FunctionDef(name=name):
                names.add(name)
            case ast.ClassDef(name=name):
                names.add(name)
            case ast.If(body=if_body, orelse=else_body):
                names.update(collect_local_vars(if_body))
                names.update(collect_local_vars(else_body))
            case ast.While(body=while_body):
                names.update(collect_local_vars(while_body))
            case ast.For(target=ast.Name(id=name), body=for_body):
                names.add(name)
                names.update(collect_local_vars(for_body))
            case ast.For(
                target=ast.Tuple(elts=targets) | ast.List(elts=targets),
                body=for_body,
            ):
                # Tuple unpacking in for loop: for a, b in pairs
                for target in targets:
                    names.update(collect_target_names(target))
                names.update(collect_local_vars(for_body))
            case ast.Try(
                body=try_body, handlers=handlers, orelse=orelse, finalbody=finalbody
            ):
                # Collect from try body
                names.update(collect_local_vars(try_body))
                # Collect from except handlers
                for handler in handlers:
                    if handler.name:
                        names.add(handler.name)
                    names.update(collect_local_vars(handler.body))
                # Collect from else and finally
                names.update(collect_local_vars(orelse))
                names.update(collect_local_vars(finalbody))
            case ast.With(items=items, body=with_body):
                # Collect variables bound by 'with ... as var'
                for item in items:
                    if item.optional_vars is not None:
                        names.update(collect_target_names(item.optional_vars))
                # Collect from with body
                names.update(collect_local_vars(with_body))
            case ast.Match(cases=cases):
                # Collect variables bound by match patterns
                for case in cases:
                    names.update(collect_pattern_names(case.pattern))
                    names.update(collect_local_vars(case.body))
    return names


def collect_namedexpr_vars(body: list[ast.stmt]) -> set[str]:
    """Collect all NamedExpr (walrus operator) variable names in a function body.

    This recursively scans all expressions to find walrus operators like:
        (x := value)

    Returns the set of variable names that will be assigned via NamedExpr.
    """
    names: set[str] = set()

    class NamedExprCollector(ast.NodeVisitor):
        def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
            match node.target:
                case ast.Name(id=name):
                    names.add(name)
            self.generic_visit(node)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            # Don't recurse into nested functions
            pass

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            # Don't recurse into nested functions
            pass

        def visit_Lambda(self, node: ast.Lambda) -> None:
            # Don't recurse into lambdas
            pass

    collector = NamedExprCollector()
    for stmt in body:
        collector.visit(stmt)

    return names


def collect_iter_locals(body: list[ast.stmt]) -> set[str]:
    """Collect iterator local names needed for for loops.

    Returns local names like '$iter_x' for each for loop variable 'x'.
    """
    iters: set[str] = set()
    for stmt in body:
        match stmt:
            case ast.For(target=ast.Name(id=name), iter=iter_expr, body=for_body):
                # Only add iterator for list loops, not range loops
                match iter_expr:
                    case ast.Call(func=ast.Name(id="range")):
                        pass  # Range loops don't need iterator local
                    case _:
                        iters.add(f"$iter_{name}")
                iters.update(collect_iter_locals(for_body))
            case ast.For(target=ast.Tuple() | ast.List(), body=for_body):
                # Tuple/list unpacking uses a fixed iterator name
                iters.add("$iter_tuple")
                iters.update(collect_iter_locals(for_body))
            case ast.If(body=if_body, orelse=else_body):
                iters.update(collect_iter_locals(if_body))
                iters.update(collect_iter_locals(else_body))
            case ast.While(body=while_body):
                iters.update(collect_iter_locals(while_body))
            case ast.Try(
                body=try_body, handlers=handlers, orelse=orelse, finalbody=finalbody
            ):
                iters.update(collect_iter_locals(try_body))
                for handler in handlers:
                    iters.update(collect_iter_locals(handler.body))
                iters.update(collect_iter_locals(orelse))
                iters.update(collect_iter_locals(finalbody))
            case ast.With(body=with_body):
                iters.update(collect_iter_locals(with_body))
            case ast.Match(cases=cases):
                for case in cases:
                    iters.update(collect_iter_locals(case.body))
    return iters


def has_try_except(body: list[ast.stmt]) -> bool:
    """Check if body contains any try/except statements (needs $exc local)."""
    for stmt in body:
        match stmt:
            case ast.Try(handlers=handlers) if handlers:
                return True
            case ast.With():
                # with statements use try/except internally
                return True
            case ast.If(body=if_body, orelse=else_body):
                if has_try_except(if_body) or has_try_except(else_body):
                    return True
            case ast.While(body=while_body):
                if has_try_except(while_body):
                    return True
            case ast.For(body=for_body):
                if has_try_except(for_body):
                    return True
            case ast.Try(
                body=try_body, handlers=handlers, orelse=orelse, finalbody=finalbody
            ):
                # Check nested try blocks
                if (
                    has_try_except(try_body)
                    or has_try_except(orelse)
                    or has_try_except(finalbody)
                ):
                    return True
                for handler in handlers:
                    if has_try_except(handler.body):
                        return True
            case ast.Match(cases=cases):
                for case in cases:
                    if has_try_except(case.body):
                        return True
    return False


def has_try_finally(body: list[ast.stmt]) -> bool:
    """Check if body contains any try/finally statements (needs $exnref local)."""
    for stmt in body:
        match stmt:
            case ast.Try(finalbody=finalbody) if finalbody:
                return True
            case ast.If(body=if_body, orelse=else_body):
                if has_try_finally(if_body) or has_try_finally(else_body):
                    return True
            case ast.While(body=while_body):
                if has_try_finally(while_body):
                    return True
            case ast.For(body=for_body):
                if has_try_finally(for_body):
                    return True
            case ast.Try(
                body=try_body, handlers=handlers, orelse=orelse, finalbody=finalbody
            ):
                # Check nested try blocks
                if (
                    has_try_finally(try_body)
                    or has_try_finally(orelse)
                    or has_try_finally(finalbody)
                ):
                    return True
                for handler in handlers:
                    if has_try_finally(handler.body):
                        return True
            case ast.Match(cases=cases):
                for case in cases:
                    if has_try_finally(case.body):
                        return True
    return False


def collect_comprehension_locals(body: list[ast.stmt]) -> tuple[set[str], int]:
    """Collect locals needed for comprehensions in a body.

    Returns a set of local names and the count of comprehensions found.
    Each comprehension needs: loop var, iterator, and result accumulator.
    """
    locals_set: set[str] = set()
    count = 0

    def visit_expr(expr: ast.expr) -> None:
        nonlocal count
        match expr:
            case (
                ast.ListComp(generators=generators)
                | ast.SetComp(generators=generators)
                | ast.GeneratorExp(generators=generators)
            ):
                comp_id = count
                count += 1
                # Each generator needs its own var and iter locals
                for gen_idx, gen in enumerate(generators):
                    locals_set.add(f"$comp_{comp_id}_var_{gen_idx}")
                    locals_set.add(f"$comp_{comp_id}_iter_{gen_idx}")
                    # Handle tuple unpacking targets
                    match gen.target:
                        case ast.Tuple(elts=elts) | ast.List(elts=elts):
                            locals_set.update(
                                f"$comp_{comp_id}_unpack_{gen_idx}_{i}"
                                for i, _ in enumerate(elts)
                            )
                locals_set.add(f"$comp_{comp_id}_result")
                # Also visit nested expressions
                match expr:
                    case (
                        ast.ListComp(elt=elt)
                        | ast.SetComp(elt=elt)
                        | ast.GeneratorExp(elt=elt)
                    ):
                        visit_expr(elt)
                for gen in generators:
                    visit_expr(gen.iter)
                    for if_clause in gen.ifs:
                        visit_expr(if_clause)
            case ast.DictComp(key=key, value=value, generators=generators):
                comp_id = count
                count += 1
                # Each generator needs its own var and iter locals
                for gen_idx, gen in enumerate(generators):
                    match gen.target:
                        case ast.Name():
                            locals_set.add(f"$comp_{comp_id}_var_{gen_idx}")
                            locals_set.add(f"$comp_{comp_id}_iter_{gen_idx}")
                locals_set.add(f"$comp_{comp_id}_result")
                # Also visit nested expressions
                visit_expr(key)
                visit_expr(value)
                for gen in generators:
                    visit_expr(gen.iter)
                    for if_clause in gen.ifs:
                        visit_expr(if_clause)
            case ast.BinOp(left=left, right=right):
                visit_expr(left)
                visit_expr(right)
            case ast.UnaryOp(operand=operand):
                visit_expr(operand)
            case ast.Compare(left=left, comparators=comparators):
                visit_expr(left)
                for comp in comparators:
                    visit_expr(comp)
            case ast.BoolOp(values=values):
                for val in values:
                    visit_expr(val)
            case ast.Call(func=func, args=args, keywords=keywords):
                visit_expr(func)
                for arg in args:
                    visit_expr(arg)
                for kw in keywords:
                    visit_expr(kw.value)
            case ast.IfExp(test=test, body=if_body, orelse=orelse):
                visit_expr(test)
                visit_expr(if_body)
                visit_expr(orelse)
            case (
                ast.List(elts=elements)
                | ast.Tuple(elts=elements)
                | ast.Set(elts=elements)
            ):
                for elem in elements:
                    visit_expr(elem)
            case ast.Dict(keys=dict_keys, values=values):
                for k in dict_keys:
                    if k is not None:
                        visit_expr(k)
                for val in values:
                    visit_expr(val)
            case ast.Subscript(value=value, slice=slc):
                visit_expr(value)
                match slc:
                    case ast.Slice(lower=lower, upper=upper, step=step):
                        if lower:
                            visit_expr(lower)
                        if upper:
                            visit_expr(upper)
                        if step:
                            visit_expr(step)
                    case _:
                        visit_expr(slc)
            case ast.JoinedStr(values=values):
                for val in values:
                    visit_expr(val)
            case ast.FormattedValue(value=value):
                visit_expr(value)
            case ast.Lambda(body=lambda_body):
                visit_expr(lambda_body)

    def visit_stmts(stmts: list[ast.stmt]) -> None:
        for stmt in stmts:
            match stmt:
                case ast.Expr(value=expr):
                    visit_expr(expr)
                case ast.Assign(value=value):
                    visit_expr(value)
                case ast.AugAssign(value=value):
                    visit_expr(value)
                case ast.AnnAssign(value=value):
                    if value:
                        visit_expr(value)
                case ast.If(test=test, body=if_body, orelse=else_body):
                    visit_expr(test)
                    visit_stmts(if_body)
                    visit_stmts(else_body)
                case ast.While(test=test, body=while_body, orelse=else_body):
                    visit_expr(test)
                    visit_stmts(while_body)
                    visit_stmts(else_body)
                case ast.For(iter=iter_expr, body=for_body, orelse=else_body):
                    visit_expr(iter_expr)
                    visit_stmts(for_body)
                    visit_stmts(else_body)
                case ast.Return(value=value):
                    if value:
                        visit_expr(value)

    visit_stmts(body)
    return locals_set, count


def collect_with_locals(body: list[ast.stmt]) -> set[str]:
    """Collect locals needed for with statements in a body.

    Returns a set of local names like '$with_cm_N' and '$with_method_N'
    for each with item N (multiple items in 'with a, b:' count separately).
    """
    locals_set: set[str] = set()
    count = 0

    def visit_stmts(stmts: list[ast.stmt]) -> None:
        nonlocal count
        for stmt in stmts:
            match stmt:
                case ast.With(items=items, body=with_body):
                    # Each item in 'with a, b, c:' needs its own locals
                    for _ in items:
                        with_id = count
                        count += 1
                        locals_set.add(f"$with_cm_{with_id}")
                        locals_set.add(f"$with_method_{with_id}")
                    visit_stmts(with_body)
                case ast.If(body=if_body, orelse=else_body):
                    visit_stmts(if_body)
                    visit_stmts(else_body)
                case ast.While(body=while_body, orelse=else_body):
                    visit_stmts(while_body)
                    visit_stmts(else_body)
                case ast.For(body=for_body, orelse=else_body):
                    visit_stmts(for_body)
                    visit_stmts(else_body)
                case ast.Try(
                    body=try_body, handlers=handlers, orelse=orelse, finalbody=finalbody
                ):
                    visit_stmts(try_body)
                    for handler in handlers:
                        visit_stmts(handler.body)
                    visit_stmts(orelse)
                    visit_stmts(finalbody)

    visit_stmts(body)
    return locals_set


def find_free_vars(node: ast.expr, bound: set[str]) -> set[str]:
    """Find free variables in an expression.

    Args:
        node: The expression to analyze
        bound: Set of variable names that are bound (not free)

    Returns:
        Set of free variable names
    """
    free: set[str] = set()
    current_bound = bound.copy()

    def visit(n: ast.expr | ast.stmt) -> None:
        nonlocal current_bound
        match n:
            case ast.Name(id=name, ctx=ast.Load()):
                if name not in current_bound:
                    free.add(name)
            case ast.Lambda(args=args, body=body):
                # Lambda binds its parameters
                old_bound = current_bound
                current_bound |= {arg.arg for arg in args.args}
                visit(body)
                current_bound = old_bound
            case ast.BinOp(left=left, right=right):
                visit(left)
                visit(right)
            case ast.UnaryOp(operand=operand):
                visit(operand)
            case ast.Compare(left=left, comparators=comparators):
                visit(left)
                for comp in comparators:
                    visit(comp)
            case ast.BoolOp(values=values):
                for val in values:
                    visit(val)
            case ast.IfExp(test=test, body=body, orelse=orelse):
                visit(test)
                visit(body)
                visit(orelse)
            case ast.Call(func=func, args=args, keywords=keywords):
                visit(func)
                for arg in args:
                    visit(arg)
                for kw in keywords:
                    if kw.value:
                        visit(kw.value)
            case ast.Subscript(value=value, slice=slice_):
                visit(value)
                visit(slice_)
            case ast.Attribute(value=value):
                visit(value)
            case ast.List(elts=elts) | ast.Tuple(elts=elts) | ast.Set(elts=elts):
                for elt in elts:
                    visit(elt)
            case ast.Dict(keys=keys, values=values):
                for k in keys:
                    if k:
                        visit(k)
                for v in values:
                    visit(v)
            case _:
                pass  # Constants, etc.

    visit(node)
    return free


def find_free_vars_in_func(body: list[ast.stmt], param_names: set[str]) -> set[str]:
    """Find free variables in a function body.

    Finds variables that are used but not defined locally or as parameters.
    Excludes nested function definitions (they have their own scope).

    Args:
        body: The function body statements
        param_names: Set of parameter names that are bound

    Returns:
        Set of free variable names
    """
    free: set[str] = set()

    # Collect all locally defined names
    local_names = collect_local_vars(body)
    bound = param_names | local_names

    def visit_expr(node: ast.expr) -> None:
        match node:
            case ast.Name(id=name, ctx=ast.Load()):
                if name not in bound:
                    free.add(name)
            case ast.Lambda(args=args, body=body):
                # Lambda is a nested scope - find free vars with its params bound
                lambda_params = {arg.arg for arg in args.args}
                lambda_free = find_free_vars(body, bound | lambda_params)
                free.update(lambda_free)
            case ast.BinOp(left=left, right=right):
                visit_expr(left)
                visit_expr(right)
            case ast.UnaryOp(operand=operand):
                visit_expr(operand)
            case ast.Compare(left=left, comparators=comparators):
                visit_expr(left)
                for comp in comparators:
                    visit_expr(comp)
            case ast.BoolOp(values=values):
                for val in values:
                    visit_expr(val)
            case ast.IfExp(test=test, body=body, orelse=orelse):
                visit_expr(test)
                visit_expr(body)
                visit_expr(orelse)
            case ast.Call(func=func, args=args, keywords=keywords):
                visit_expr(func)
                for arg in args:
                    visit_expr(arg)
                for kw in keywords:
                    if kw.value:
                        visit_expr(kw.value)
            case ast.Subscript(value=value, slice=slice_):
                visit_expr(value)
                match slice_:
                    case ast.Slice(lower=lower, upper=upper, step=step):
                        if lower:
                            visit_expr(lower)
                        if upper:
                            visit_expr(upper)
                        if step:
                            visit_expr(step)
                    case _:
                        visit_expr(slice_)
            case ast.Attribute(value=value):
                visit_expr(value)
            case ast.List(elts=elts) | ast.Tuple(elts=elts) | ast.Set(elts=elts):
                for elt in elts:
                    visit_expr(elt)
            case ast.Dict(keys=keys, values=values):
                for k in keys:
                    if k:
                        visit_expr(k)
                for v in values:
                    visit_expr(v)
            case ast.JoinedStr(values=values):
                for val in values:
                    visit_expr(val)
            case ast.FormattedValue(value=value):
                visit_expr(value)
            case ast.ListComp(elt=elt, generators=generators):
                # Comprehension binds its loop variable
                for gen in generators:
                    visit_expr(gen.iter)
                    for if_clause in gen.ifs:
                        visit_expr(if_clause)
                visit_expr(elt)
            case ast.SetComp(elt=elt, generators=generators):
                for gen in generators:
                    visit_expr(gen.iter)
                    for if_clause in gen.ifs:
                        visit_expr(if_clause)
                visit_expr(elt)
            case ast.DictComp(key=key, value=value, generators=generators):
                for gen in generators:
                    visit_expr(gen.iter)
                    for if_clause in gen.ifs:
                        visit_expr(if_clause)
                visit_expr(key)
                visit_expr(value)
            case _:
                pass

    def visit_stmt(node: ast.stmt) -> None:
        match node:
            case ast.FunctionDef(args=args, body=func_body):
                # Nested function - find free vars in its body
                nested_params = {arg.arg for arg in args.args}
                nested_free = find_free_vars_in_func(func_body, nested_params)
                # Variables free in nested function that are bound in this function
                # need to be captured
                for name in nested_free:
                    if name in bound:
                        free.add(name)
            case ast.Expr(value=value):
                visit_expr(value)
            case ast.Assign(targets=targets, value=value):
                visit_expr(value)
                for target in targets:
                    match target:
                        case ast.Subscript(value=container, slice=slc):
                            visit_expr(container)
                            visit_expr(slc)
                        case ast.Attribute(value=obj):
                            visit_expr(obj)
            case ast.AugAssign(target=target, value=value):
                match target:
                    case ast.Name(id=name) if name not in bound:
                        free.add(name)
                    case ast.Subscript(value=container, slice=slc):
                        visit_expr(container)
                        visit_expr(slc)
                    case ast.Attribute(value=obj):
                        visit_expr(obj)
                visit_expr(value)
            case ast.AnnAssign(value=value):
                if value:
                    visit_expr(value)
            case ast.If(test=test, body=if_body, orelse=else_body):
                visit_expr(test)
                for stmt in if_body:
                    visit_stmt(stmt)
                for stmt in else_body:
                    visit_stmt(stmt)
            case ast.While(test=test, body=while_body):
                visit_expr(test)
                for stmt in while_body:
                    visit_stmt(stmt)
            case ast.For(
                target=target, iter=iter_expr, body=for_body, orelse=else_body
            ):
                visit_expr(iter_expr)
                for stmt in for_body:
                    visit_stmt(stmt)
                for stmt in else_body:
                    visit_stmt(stmt)
            case ast.Return(value=value):
                if value:
                    visit_expr(value)
            case _:
                pass

    for stmt in body:
        visit_stmt(stmt)

    return free


# Type inference functions


def is_string_expr(node: ast.expr) -> bool:
    """Check if an expression is known to be a string at compile time."""
    match node:
        case ast.Constant(value=str()):
            return True
        case ast.BinOp(op=ast.Add(), left=left, right=right):
            return is_string_expr(left) or is_string_expr(right)
        case _:
            return False


def is_float_expr(node: ast.expr) -> bool:
    """Check if an expression is known to be a float at compile time."""
    match node:
        case ast.Constant(value=float()):
            return True
        case ast.BinOp(op=ast.Div()):
            # Division always returns float in Python 3
            return True
        case ast.BinOp(left=left, right=right):
            return is_float_expr(left) or is_float_expr(right)
        case ast.UnaryOp(operand=operand):
            return is_float_expr(operand)
        case _:
            return False


def is_bool_expr(node: ast.expr) -> bool:
    """Check if an expression is known to be a boolean at compile time."""
    match node:
        case ast.Constant(value=bool()):
            return True
        case _:
            return False


def is_list_expr(node: ast.expr) -> bool:
    """Check if an expression is known to be a list at compile time."""
    match node:
        case ast.List():
            return True
        case ast.BinOp(op=ast.Add(), left=left, right=right):
            return is_list_expr(left) or is_list_expr(right)
        case ast.Call(func=ast.Name(id="list")):
            return True
        case ast.Call(func=ast.Name(id="range")):
            return True
        case _:
            return False


def is_tuple_expr(node: ast.expr) -> bool:
    """Check if an expression is known to be a tuple at compile time."""
    match node:
        case ast.Tuple():
            return True
        case ast.BinOp(op=ast.Add(), left=left, right=right):
            return is_tuple_expr(left) or is_tuple_expr(right)
        case ast.BinOp(op=ast.Mult(), left=left):
            return is_tuple_expr(left)
        case ast.Call(func=ast.Name(id="tuple")):
            return True
        case _:
            return False


def is_dict_expr(node: ast.expr) -> bool:
    """Check if an expression is known to be a dict at compile time."""
    match node:
        case ast.Dict():
            return True
        case ast.DictComp():
            return True
        case ast.Call(func=ast.Name(id="dict")):
            return True
        case _:
            return False


# i31 range limits
I31_MIN = -(2**30)  # -1073741824
I31_MAX = 2**30 - 1  # 1073741823


def is_large_int_constant(node: ast.expr) -> bool:
    """Check if an expression is a large integer constant that doesn't fit in i31.

    Large integers need INT64 boxing and runtime dispatch.
    """
    match node:
        case ast.Constant(value=int() as val):
            return val < I31_MIN or val > I31_MAX
        case ast.UnaryOp(op=ast.USub(), operand=ast.Constant(value=int() as val)):
            # Negative constants like -2000000000
            return -val < I31_MIN
    return False


def is_unknown_type(node: ast.expr) -> bool:
    """Check if an expression's type is unknown at compile time."""
    match node:
        case ast.Name():
            # Variable - type unknown at compile time
            return True
        case ast.Subscript():
            # Subscript result - type unknown
            return True
        case ast.Call(func=ast.Name(id=name)) if name in {
            "int",
            "str",
            "list",
            "range",
            "len",
        }:
            # Known function calls have known return types
            return False
        case ast.Call():
            # Function call result - usually unknown
            return True
        case ast.Attribute():
            # Attribute access - type unknown
            return True
        case ast.BinOp(left=left, right=right):
            # BinOp with unknown operands has unknown result type
            return is_unknown_type(left) or is_unknown_type(right)
        case ast.UnaryOp(operand=operand):
            # UnaryOp with unknown operand has unknown result type
            return is_unknown_type(operand)
        case _:
            return False


def collect_global_decls(body: list[ast.stmt]) -> set[str]:
    """Collect all variable names declared global in a function body.

    Does a shallow scan - doesn't recurse into nested functions.
    """
    names: set[str] = set()
    for stmt in body:
        match stmt:
            case ast.Global(names=global_names):
                names.update(global_names)
            case ast.If(body=if_body, orelse=else_body):
                names.update(collect_global_decls(if_body))
                names.update(collect_global_decls(else_body))
            case ast.While(body=while_body):
                names.update(collect_global_decls(while_body))
            case ast.For(body=for_body):
                names.update(collect_global_decls(for_body))
    return names


def collect_nonlocal_decls(body: list[ast.stmt]) -> set[str]:
    """Collect all variable names declared nonlocal in a function body.

    Does a shallow scan - doesn't recurse into nested functions.
    """
    names: set[str] = set()
    for stmt in body:
        match stmt:
            case ast.Nonlocal(names=nonlocal_names):
                names.update(nonlocal_names)
            case ast.If(body=if_body, orelse=else_body):
                names.update(collect_nonlocal_decls(if_body))
                names.update(collect_nonlocal_decls(else_body))
            case ast.While(body=while_body):
                names.update(collect_nonlocal_decls(while_body))
            case ast.For(body=for_body):
                names.update(collect_nonlocal_decls(for_body))
    return names


def collect_all_global_refs(body: list[ast.stmt]) -> set[str]:
    """Collect all variable names declared global anywhere in module.

    Recursively scans all functions to find global declarations.
    Returns the union of all global variable names referenced.
    """
    names: set[str] = set()

    def visit_stmts(stmts: list[ast.stmt]) -> None:
        for stmt in stmts:
            match stmt:
                case ast.Global(names=global_names):
                    names.update(global_names)
                case ast.FunctionDef(body=func_body):
                    visit_stmts(func_body)
                case ast.If(body=if_body, orelse=else_body):
                    visit_stmts(if_body)
                    visit_stmts(else_body)
                case ast.While(body=while_body):
                    visit_stmts(while_body)
                case ast.For(body=for_body):
                    visit_stmts(for_body)
                case ast.ClassDef(body=class_body):
                    visit_stmts(class_body)

    visit_stmts(body)
    return names


def collect_class_names(body: list[ast.stmt]) -> set[str]:
    """Collect all class names defined at module level.

    Classes need to be accessible as globals so that methods can
    reference the enclosing class by name (e.g., Counter.count).
    """
    names: set[str] = set()
    for stmt in body:
        match stmt:
            case ast.ClassDef(name=name):
                names.add(name)
    return names


def collect_slotted_classes(body: list[ast.stmt]) -> dict[str, list[str]]:
    """Collect classes that have __slots__ defined.

    Returns a dict mapping class name to list of slot names.
    Slotted classes get optimized struct-based storage instead of
    dict-based attribute storage.

    Example:
        class Record:
            __slots__ = ('x', 'y', 'z')

        Returns: {'Record': ['x', 'y', 'z']}
    """
    slotted: dict[str, list[str]] = {}

    for stmt in body:
        match stmt:
            case ast.ClassDef(name=class_name):
                pass
            case _:
                continue
        slots = _extract_slots(stmt.body)
        if slots is not None:
            slotted[class_name] = slots

    return slotted


def _extract_slots(class_body: list[ast.stmt]) -> list[str] | None:
    """Extract __slots__ from a class body if defined.

    Returns list of slot names, or None if __slots__ is not defined.
    Supports:
        __slots__ = ('a', 'b', 'c')   # tuple
        __slots__ = ['a', 'b', 'c']   # list
        __slots__: tuple = ('a', 'b') # annotated
    """
    for stmt in class_body:
        match stmt:
            case ast.Assign(
                targets=[ast.Name(id="__slots__")],
                value=ast.Tuple(elts=elts) | ast.List(elts=elts),
            ):
                return _extract_slot_names(elts)

            case ast.AnnAssign(
                target=ast.Name(id="__slots__"),
                value=ast.Tuple(elts=elts) | ast.List(elts=elts),
            ):
                return _extract_slot_names(elts)

    return None


def _extract_slot_names(elts: list[ast.expr]) -> list[str]:
    """Extract string names from a list/tuple of slot definitions."""
    names: list[str] = []
    for elt in elts:
        match elt:
            case ast.Constant(value=str() as name):
                names.append(name)
    return names


def collect_function_names(body: list[ast.stmt]) -> set[str]:
    """Collect all function names defined at module level.

    Functions need to be accessible as globals so that other functions
    can call them regardless of definition order (forward references).
    """
    names: set[str] = set()
    for stmt in body:
        match stmt:
            case ast.FunctionDef(name=name):
                names.add(name)
    return names


def collect_module_level_vars(body: list[ast.stmt]) -> set[str]:
    """Collect all variable names assigned at module level.

    Module-level variables need to be accessible as globals so that nested
    functions can reference them directly via global_get instead of capturing
    them as closure variables.
    """
    names: set[str] = set()
    for stmt in body:
        match stmt:
            case ast.Assign(targets=targets):
                for target in targets:
                    match target:
                        case ast.Name(id=name):
                            names.add(name)
            case ast.AnnAssign(target=ast.Name(id=name)):
                names.add(name)
    return names


def is_generator_function(body: list[ast.stmt]) -> bool:
    """Check if a function body contains yield statements.

    A function is a generator if it contains any yield or yield from expression.
    """

    class YieldFinder(ast.NodeVisitor):
        def __init__(self) -> None:
            self.has_yield = False

        def visit_Yield(self, node: ast.Yield) -> None:  # noqa: ARG002
            self.has_yield = True

        def visit_YieldFrom(self, node: ast.YieldFrom) -> None:  # noqa: ARG002
            self.has_yield = True

        # Don't recurse into nested functions/classes - they have their own scope
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            pass

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            pass

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            pass

        def visit_Lambda(self, node: ast.Lambda) -> None:
            pass

    finder = YieldFinder()
    for stmt in body:
        finder.visit(stmt)
        if finder.has_yield:
            return True
    return False


def collect_yield_points(body: list[ast.stmt]) -> list[ast.Yield | ast.YieldFrom]:
    """Collect all yield/yield from expressions in a function body.

    Returns a list of yield nodes in order of occurrence.
    Does not recurse into nested functions.
    """

    class YieldCollector(ast.NodeVisitor):
        def __init__(self) -> None:
            self.yields: list[ast.Yield | ast.YieldFrom] = []

        def visit_Yield(self, node: ast.Yield) -> None:
            self.yields.append(node)
            self.generic_visit(node)

        def visit_YieldFrom(self, node: ast.YieldFrom) -> None:
            self.yields.append(node)
            self.generic_visit(node)

        # Don't recurse into nested functions/classes
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            pass

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            pass

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            pass

        def visit_Lambda(self, node: ast.Lambda) -> None:
            pass

    collector = YieldCollector()
    for stmt in body:
        collector.visit(stmt)
    return collector.yields

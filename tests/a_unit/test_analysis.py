"""Unit tests for AST analysis functions."""

from __future__ import annotations

import ast

from p2w.compiler.analysis import (
    collect_comprehension_locals,
    collect_iter_locals,
    collect_local_vars,
    collect_namedexpr_vars,
    collect_pattern_names,
    collect_target_names,
    collect_with_locals,
    find_free_vars,
    has_try_except,
    has_try_finally,
    is_generator_function,
)


class TestCollectTargetNames:
    """Test collection of assignment target names."""

    def test_simple_name(self):
        node = ast.Name(id="x")
        assert collect_target_names(node) == {"x"}

    def test_tuple_target(self):
        node = ast.Tuple(elts=[ast.Name(id="a"), ast.Name(id="b")])
        assert collect_target_names(node) == {"a", "b"}

    def test_nested_tuple(self):
        node = ast.Tuple(
            elts=[
                ast.Name(id="a"),
                ast.Tuple(elts=[ast.Name(id="b"), ast.Name(id="c")]),
            ]
        )
        assert collect_target_names(node) == {"a", "b", "c"}

    def test_starred_target(self):
        # a, *rest = [1, 2, 3]
        node = ast.Tuple(
            elts=[
                ast.Name(id="a"),
                ast.Starred(value=ast.Name(id="rest")),
            ]
        )
        assert collect_target_names(node) == {"a", "rest"}

    def test_subscript_ignored(self):
        # lst[0] = value - subscript doesn't introduce new name
        node = ast.Subscript(
            value=ast.Name(id="lst"),
            slice=ast.Constant(value=0),
        )
        assert collect_target_names(node) == set()


class TestCollectLocalVars:
    """Test collection of local variables from function body."""

    def test_simple_assign(self):
        source = "x = 1"
        tree = ast.parse(source)
        assert collect_local_vars(tree.body) == {"x"}

    def test_multiple_assigns(self):
        source = """
x = 1
y = 2
"""
        tree = ast.parse(source)
        assert collect_local_vars(tree.body) == {"x", "y"}

    def test_aug_assign(self):
        source = "x += 1"
        tree = ast.parse(source)
        assert collect_local_vars(tree.body) == {"x"}

    def test_annotated_assign(self):
        source = "x: int = 1"
        tree = ast.parse(source)
        assert collect_local_vars(tree.body) == {"x"}

    def test_for_loop_target(self):
        source = """
for i in range(10):
    pass
"""
        tree = ast.parse(source)
        assert collect_local_vars(tree.body) == {"i"}

    def test_tuple_for_loop(self):
        source = """
for a, b in pairs:
    pass
"""
        tree = ast.parse(source)
        assert collect_local_vars(tree.body) == {"a", "b"}

    def test_nested_in_if(self):
        source = """
if True:
    x = 1
else:
    y = 2
"""
        tree = ast.parse(source)
        assert collect_local_vars(tree.body) == {"x", "y"}

    def test_function_def_name(self):
        source = """
def foo():
    pass
"""
        tree = ast.parse(source)
        assert collect_local_vars(tree.body) == {"foo"}

    def test_class_def_name(self):
        source = """
class Foo:
    pass
"""
        tree = ast.parse(source)
        assert collect_local_vars(tree.body) == {"Foo"}

    def test_except_handler_name(self):
        source = """
try:
    pass
except Exception as e:
    pass
"""
        tree = ast.parse(source)
        assert collect_local_vars(tree.body) == {"e"}

    def test_with_as_name(self):
        source = """
with open('f') as f:
    pass
"""
        tree = ast.parse(source)
        assert collect_local_vars(tree.body) == {"f"}


class TestCollectNamedExprVars:
    """Test collection of walrus operator variables."""

    def test_simple_walrus(self):
        source = """
if (x := get_value()):
    pass
"""
        tree = ast.parse(source)
        assert collect_namedexpr_vars(tree.body) == {"x"}

    def test_walrus_in_while(self):
        source = """
while (line := read_line()):
    pass
"""
        tree = ast.parse(source)
        assert collect_namedexpr_vars(tree.body) == {"line"}


class TestCollectIterLocals:
    """Test collection of iterator locals for for loops."""

    def test_simple_for(self):
        source = """
for x in items:
    pass
"""
        tree = ast.parse(source)
        assert collect_iter_locals(tree.body) == {"$iter_x"}

    def test_range_no_iter(self):
        source = """
for i in range(10):
    pass
"""
        tree = ast.parse(source)
        # Range loops don't need iterator local
        assert collect_iter_locals(tree.body) == set()

    def test_tuple_unpacking(self):
        source = """
for a, b in pairs:
    pass
"""
        tree = ast.parse(source)
        assert collect_iter_locals(tree.body) == {"$iter_tuple"}


class TestHasTryExcept:
    """Test detection of try/except statements."""

    def test_simple_try_except(self):
        source = """
try:
    pass
except:
    pass
"""
        tree = ast.parse(source)
        assert has_try_except(tree.body) is True

    def test_with_statement(self):
        source = """
with open('f') as f:
    pass
"""
        tree = ast.parse(source)
        # with uses try/except internally
        assert has_try_except(tree.body) is True

    def test_no_try(self):
        source = "x = 1"
        tree = ast.parse(source)
        assert has_try_except(tree.body) is False


class TestHasTryFinally:
    """Test detection of try/finally statements."""

    def test_try_finally(self):
        source = """
try:
    pass
finally:
    pass
"""
        tree = ast.parse(source)
        assert has_try_finally(tree.body) is True

    def test_try_except_no_finally(self):
        source = """
try:
    pass
except:
    pass
"""
        tree = ast.parse(source)
        assert has_try_finally(tree.body) is False


class TestCollectComprehensionLocals:
    """Test collection of comprehension locals."""

    def test_simple_listcomp(self):
        source = "[x * 2 for x in items]"
        tree = ast.parse(source, mode="eval")
        locals_set, count = collect_comprehension_locals([ast.Expr(value=tree.body)])
        assert count == 1
        assert "$comp_0_var_0" in locals_set
        assert "$comp_0_iter_0" in locals_set
        assert "$comp_0_result" in locals_set

    def test_listcomp_with_tuple_unpacking(self):
        source = "[a + b for a, b in pairs]"
        tree = ast.parse(source, mode="eval")
        locals_set, count = collect_comprehension_locals([ast.Expr(value=tree.body)])
        assert count == 1
        assert "$comp_0_unpack_0_0" in locals_set
        assert "$comp_0_unpack_0_1" in locals_set

    def test_dictcomp_simple(self):
        source = "{k: v for k in keys for v in values}"
        tree = ast.parse(source, mode="eval")
        locals_set, count = collect_comprehension_locals([ast.Expr(value=tree.body)])
        assert count == 1
        assert "$comp_0_var_0" in locals_set
        assert "$comp_0_var_1" in locals_set
        assert "$comp_0_result" in locals_set

    def test_dictcomp_with_tuple_unpacking(self):
        source = "{k: v for k, v in items}"
        tree = ast.parse(source, mode="eval")
        locals_set, count = collect_comprehension_locals([ast.Expr(value=tree.body)])
        assert count == 1
        assert "$comp_0_unpack_0_0" in locals_set
        assert "$comp_0_unpack_0_1" in locals_set


class TestCollectWithLocals:
    """Test collection of with statement locals."""

    def test_single_with(self):
        source = """
with open('f'):
    pass
"""
        tree = ast.parse(source)
        locals_set = collect_with_locals(tree.body)
        assert "$with_cm_0" in locals_set
        assert "$with_method_0" in locals_set

    def test_multiple_with_items(self):
        source = """
with open('a') as a, open('b') as b:
    pass
"""
        tree = ast.parse(source)
        locals_set = collect_with_locals(tree.body)
        assert "$with_cm_0" in locals_set
        assert "$with_cm_1" in locals_set


class TestFindFreeVars:
    """Test free variable detection."""

    def test_no_free_vars(self):
        node = ast.Constant(value=1)
        assert find_free_vars(node, set()) == set()

    def test_simple_free_var(self):
        node = ast.Name(id="x", ctx=ast.Load())
        assert find_free_vars(node, set()) == {"x"}

    def test_bound_var_not_free(self):
        node = ast.Name(id="x", ctx=ast.Load())
        assert find_free_vars(node, {"x"}) == set()

    def test_lambda_binds_params(self):
        source = "lambda x: x + y"
        tree = ast.parse(source, mode="eval")
        free = find_free_vars(tree.body, set())
        assert "y" in free
        assert "x" not in free


class TestIsGeneratorFunction:
    """Test generator function detection."""

    def test_simple_generator(self):
        source = """
def gen():
    yield 1
"""
        tree = ast.parse(source)
        func = tree.body[0]
        assert is_generator_function(func.body) is True

    def test_yield_from(self):
        source = """
def gen():
    yield from other()
"""
        tree = ast.parse(source)
        func = tree.body[0]
        assert is_generator_function(func.body) is True

    def test_regular_function(self):
        source = """
def foo():
    return 1
"""
        tree = ast.parse(source)
        func = tree.body[0]
        assert is_generator_function(func.body) is False

    def test_nested_generator_not_detected(self):
        source = """
def outer():
    def inner():
        yield 1
    return inner
"""
        tree = ast.parse(source)
        func = tree.body[0]
        # Outer function is not a generator (yield is in nested function)
        assert is_generator_function(func.body) is False


class TestCollectPatternNames:
    """Test pattern name collection for match statements."""

    def test_match_as(self):
        source = """
match x:
    case y:
        pass
"""
        tree = ast.parse(source)
        match_stmt = tree.body[0]
        case = match_stmt.cases[0]
        assert collect_pattern_names(case.pattern) == {"y"}

    def test_match_sequence(self):
        source = """
match x:
    case [a, b, c]:
        pass
"""
        tree = ast.parse(source)
        match_stmt = tree.body[0]
        case = match_stmt.cases[0]
        assert collect_pattern_names(case.pattern) == {"a", "b", "c"}

    def test_match_star(self):
        source = """
match x:
    case [first, *rest]:
        pass
"""
        tree = ast.parse(source)
        match_stmt = tree.body[0]
        case = match_stmt.cases[0]
        names = collect_pattern_names(case.pattern)
        assert "first" in names
        assert "rest" in names

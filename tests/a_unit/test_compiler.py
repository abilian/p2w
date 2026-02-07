"""Unit tests for the p2w compiler."""

from __future__ import annotations

from p2w.compiler import LexicalEnv, compile_to_wat


class TestLexicalEnv:
    """Tests for the lexical environment."""

    def test_push_pop_frame(self) -> None:
        env = LexicalEnv()
        env.push_frame()
        assert len(env.frames) == 1
        env.push_frame()
        assert len(env.frames) == 2
        env.pop_frame()
        assert len(env.frames) == 1

    def test_add_name(self) -> None:
        env = LexicalEnv()
        env.push_frame()
        slot = env.add_name("x")
        assert slot == 0
        slot = env.add_name("y")
        assert slot == 1

    def test_lookup_success(self) -> None:
        env = LexicalEnv()
        env.push_frame()
        env.add_name("x")
        env.add_name("y")
        env.push_frame()
        env.add_name("z")

        # z is in current frame
        depth, slot = env.lookup("z")
        assert depth == 0
        assert slot == 0

        # x is in parent frame
        depth, slot = env.lookup("x")
        assert depth == 1
        assert slot == 0

        # y is in parent frame
        depth, slot = env.lookup("y")
        assert depth == 1
        assert slot == 1

    def test_lookup_failure(self) -> None:
        env = LexicalEnv()
        env.push_frame()
        env.add_name("x")

        try:
            env.lookup("not_found")
            msg = "Should have raised NameError"
            raise AssertionError(msg)
        except NameError:
            pass

    def test_contains(self) -> None:
        env = LexicalEnv()
        env.push_frame()
        env.add_name("x")
        assert env.contains("x")
        assert not env.contains("y")


class TestCompileToWat:
    """Tests for WAT code generation."""

    def test_empty_module(self) -> None:
        wat = compile_to_wat("")
        assert "(module" in wat
        assert ")" in wat

    def test_print_integer(self) -> None:
        wat = compile_to_wat("print(42)")
        assert "(module" in wat
        assert "i32.const 42" in wat

    def test_print_arithmetic(self) -> None:
        wat = compile_to_wat("print(1 + 2)")
        assert "i32.add" in wat

    def test_function_definition(self) -> None:
        wat = compile_to_wat("""
def f(x):
    return x
""")
        assert "$user_func_" in wat

    def test_conditional(self) -> None:
        wat = compile_to_wat("""
if True:
    print(1)
else:
    print(2)
""")
        assert "if" in wat
        assert "else" in wat
        assert "end" in wat

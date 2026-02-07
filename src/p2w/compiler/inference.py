"""Type inference engine for compile-time type analysis.

This module provides type inference for p2w expressions,
enabling specialized code generation for known types.
"""

from __future__ import annotations

import ast

from p2w.compiler.types import (
    BOOL,
    F64,
    FLOAT,
    I32,
    I64,
    INT,
    NONE,
    STRING,
    UNKNOWN,
    BobType,
    DictType,
    FloatType,
    ListType,
    NativeType,
    TupleType,
    combine_types,
    get_native_wasm_type,
    is_native_type,
)


class TypeInferencer(ast.NodeVisitor):
    """Infer types for expressions in a function body.

    This is a simple forward-flow type inferencer that tracks
    variable types through assignments and infers expression types.
    """

    # i32 range: -2147483648 to 2147483647
    I32_MIN = -(2**31)
    I32_MAX = 2**31 - 1

    def __init__(self) -> None:
        self.var_types: dict[str, BobType] = {}
        self.expr_types: dict[int, BobType] = {}  # id(node) -> type
        self.func_return_types: dict[str, BobType] = {}  # func_name -> return type
        # Native type tracking for unboxed locals
        self.native_vars: dict[str, NativeType] = {}  # var -> native WASM type
        self._escaped_vars: set[str] = set()  # vars that escape to non-native contexts
        self._loop_counter_vars: set[str] = (
            set()
        )  # vars that are loop counters (safe for i32)
        self._large_int_vars: set[str] = (
            set()
        )  # vars assigned large int literals (unsafe for i32)
        self._i32_loop_candidates: set[str] = (
            set()
        )  # loop vars that iterate over i32 range (can be promoted to native)

    def infer(self, node: ast.expr) -> BobType:
        """Infer type of expression."""
        cached = self.expr_types.get(id(node))
        if cached:
            return cached

        result = self.visit(node)
        if result is None:
            result = UNKNOWN
        self.expr_types[id(node)] = result
        return result

    def visit_Constant(self, node: ast.Constant) -> BobType:
        """Infer type from constant value."""
        match node.value:
            case bool():
                return BOOL
            case int():
                return INT
            case float():
                return FLOAT
            case str():
                return STRING
            case None:
                return NONE
            case _:
                return UNKNOWN

    def visit_Name(self, node: ast.Name) -> BobType:
        """Look up variable type."""
        return self.var_types.get(node.id, UNKNOWN)

    def visit_BinOp(self, node: ast.BinOp) -> BobType:
        """Infer type of binary operation."""
        left_type = self.infer(node.left)
        right_type = self.infer(node.right)
        op_name = self._op_to_str(node.op)
        return combine_types(left_type, right_type, op_name)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> BobType:
        """Infer type of unary operation."""
        operand_type = self.infer(node.operand)
        match node.op:
            case ast.USub() | ast.UAdd():
                return operand_type  # -x or +x preserves numeric type
            case ast.Not():
                return BOOL
            case ast.Invert():
                return INT  # Bitwise not returns int
            case _:
                return UNKNOWN

    def visit_Compare(self, node: ast.Compare) -> BobType:  # noqa: ARG002
        """Comparisons always return bool."""
        return BOOL

    def visit_BoolOp(self, node: ast.BoolOp) -> BobType:
        """Boolean operations return one of their operands."""
        # In Python, and/or return one of the operands, not bool
        # But for simplicity, we treat as returning the common type
        types = [self.infer(v) for v in node.values]
        if all(isinstance(t, type(types[0])) for t in types):
            return types[0]
        return UNKNOWN

    def visit_IfExp(self, node: ast.IfExp) -> BobType:
        """Ternary expression: return common type of branches."""
        body_type = self.infer(node.body)
        orelse_type = self.infer(node.orelse)
        if body_type == orelse_type:
            return body_type
        return UNKNOWN

    def visit_List(self, node: ast.List) -> BobType:
        """Infer list type with element type if uniform."""
        if not node.elts:
            return ListType()
        elem_type = self.infer(node.elts[0])
        for elt in node.elts[1:]:
            if self.infer(elt) != elem_type:
                return ListType()  # Heterogeneous
        return ListType(elem_type)

    def visit_Tuple(self, node: ast.Tuple) -> BobType:
        """Infer tuple type with element types."""
        elem_types = tuple(self.infer(elt) for elt in node.elts)
        return TupleType(elem_types)

    def visit_Dict(self, node: ast.Dict) -> BobType:
        """Infer dict type with key/value types if uniform."""
        if not node.keys:
            return DictType()
        # Infer key type
        key_types = [self.infer(k) for k in node.keys if k is not None]
        key_type = key_types[0] if key_types else UNKNOWN
        if not all(t == key_type for t in key_types):
            key_type = UNKNOWN
        # Infer value type
        value_types = [self.infer(v) for v in node.values]
        value_type = value_types[0] if value_types else UNKNOWN
        if not all(t == value_type for t in value_types):
            value_type = UNKNOWN
        return DictType(key_type, value_type)

    def visit_Subscript(self, node: ast.Subscript) -> BobType:
        """Infer subscript result type."""
        container_type = self.infer(node.value)
        match container_type:
            case ListType(element_type=elem_type) if elem_type:
                return elem_type
            case DictType(value_type=val_type) if val_type:
                return val_type
            case TupleType(element_types=elem_types):
                # For tuple with constant index, return specific element type
                match node.slice:
                    case ast.Constant(value=int() as idx) if 0 <= idx < len(elem_types):
                        return elem_types[idx]
        return UNKNOWN

    def visit_Call(self, node: ast.Call) -> BobType:
        """Infer function call result type for known functions."""
        match node.func:
            case ast.Name(id=name):
                match name:
                    # Type constructors
                    case "int":
                        return INT
                    case "float":
                        return FLOAT
                    case "str":
                        return STRING
                    case "bool":
                        return BOOL
                    case "list":
                        return ListType()
                    case "dict":
                        return DictType()
                    case "tuple":
                        return TupleType()
                    # Len returns int
                    case "len":
                        return INT
                    # Builtins that return specific types
                    case "abs" | "sum" | "min" | "max" | "ord":
                        if node.args:
                            arg_type = self.infer(node.args[0])
                            if name == "ord":
                                return INT
                            if name in {"sum", "min", "max"}:
                                # Returns element type or int
                                match arg_type:
                                    case ListType(element_type=elem_type) if elem_type:
                                        return elem_type
                            return arg_type
                        return INT
                    case "chr":
                        return STRING
                    case "range":
                        return ListType(INT)
                    case "any" | "all":
                        return BOOL
                    case _ if name in self.func_return_types:
                        # Check for user-defined function return type
                        return self.func_return_types[name]
        return UNKNOWN

    def analyze_assignment(self, target: ast.expr, value_type: BobType) -> None:
        """Record type for assignment target."""
        match target:
            case ast.Name(id=name):
                self.var_types[name] = value_type
            case ast.Tuple(elts=elts) | ast.List(elts=elts):
                # Unpack assignment
                match value_type:
                    case TupleType(element_types=elem_types):
                        for i, elt in enumerate(elts):
                            if i < len(elem_types):
                                self.analyze_assignment(elt, elem_types[i])
                            else:
                                self.analyze_assignment(elt, UNKNOWN)
                    case ListType(element_type=elem_type):
                        for elt in elts:
                            self.analyze_assignment(elt, elem_type or UNKNOWN)
                    case _:
                        for elt in elts:
                            self.analyze_assignment(elt, UNKNOWN)

    def analyze_function(self, node: ast.FunctionDef) -> None:
        """Analyze function body to infer variable types."""
        # Process type annotations if present
        for arg in node.args.args:
            if arg.annotation:
                self.var_types[arg.arg] = self._annotation_to_type(arg.annotation)

        # Check for return type annotation
        if node.returns:
            self.func_return_types[node.name] = self._annotation_to_type(node.returns)

        # Analyze assignments in order
        for stmt in node.body:
            self._analyze_stmt(stmt)

        # Infer return type from return statements if not annotated
        if node.name not in self.func_return_types:
            return_type = self._infer_function_return_type(node.body)
            if return_type != UNKNOWN:
                self.func_return_types[node.name] = return_type

        # Determine which variables can use native WASM types
        self._analyze_native_eligibility(node.body)

        # Analyze which variables can use native WASM types
        self._analyze_native_eligibility(node.body)

    def _infer_function_return_type(self, body: list[ast.stmt]) -> BobType:
        """Infer return type from return statements in function body."""
        return_types: list[BobType] = []
        self._collect_return_types(body, return_types)
        if not return_types:
            return NONE
        # Return the common type if all same, otherwise UNKNOWN
        first = return_types[0]
        if all(t == first for t in return_types):
            return first
        return UNKNOWN

    def _collect_return_types(
        self, stmts: list[ast.stmt], return_types: list[BobType]
    ) -> None:
        """Collect return types from a list of statements."""
        for stmt in stmts:
            match stmt:
                case ast.Return(value=value):
                    return_types.append(self.infer(value) if value else NONE)

                case ast.If() | ast.For() | ast.While():
                    self._collect_return_types(stmt.body, return_types)
                    self._collect_return_types(stmt.orelse, return_types)

                case ast.With():
                    self._collect_return_types(stmt.body, return_types)

                case ast.Try():
                    self._collect_return_types(stmt.body, return_types)
                    for handler in stmt.handlers:
                        self._collect_return_types(handler.body, return_types)
                    self._collect_return_types(stmt.orelse, return_types)
                    self._collect_return_types(stmt.finalbody, return_types)

    def analyze_module(self, body: list[ast.stmt]) -> None:
        """Analyze module-level statements to infer variable types."""
        # First pass: collect function return types
        for stmt in body:
            match stmt:
                case ast.FunctionDef():
                    self._pre_analyze_function(stmt)

        # Second pass: analyze all statements
        for stmt in body:
            self._analyze_stmt(stmt)

        # Third pass: analyze which variables can use native WASM types
        self._analyze_native_eligibility(body)

    def _pre_analyze_function(self, node: ast.FunctionDef) -> None:
        """Pre-analyze a function to infer its return type."""
        # Save current var_types to restore after
        saved_var_types = self.var_types.copy()

        # Set up parameter types
        for arg in node.args.args:
            if arg.annotation:
                self.var_types[arg.arg] = self._annotation_to_type(arg.annotation)

        # Check for return type annotation
        if node.returns:
            self.func_return_types[node.name] = self._annotation_to_type(node.returns)
        else:
            # Infer return type from return statements
            return_type = self._infer_function_return_type(node.body)
            if return_type != UNKNOWN:
                self.func_return_types[node.name] = return_type

        # Restore var_types
        self.var_types = saved_var_types

    def _analyze_stmt(self, stmt: ast.stmt) -> None:
        """Analyze a statement for type information."""
        match stmt:
            case ast.Assign(value=value, targets=targets):
                value_type = self.infer(value)
                for target in targets:
                    # Preserve explicit native type annotations (i32, i64, f64)
                    # If variable was declared with explicit type, don't overwrite it
                    if isinstance(target, ast.Name) and target.id in self.var_types:
                        existing_type = self.var_types[target.id]
                        if is_native_type(existing_type):
                            # Keep the explicit native type annotation
                            continue
                    self.analyze_assignment(target, value_type)
                    # Track if this is a large int literal assignment
                    if isinstance(target, ast.Name) and self._is_large_int_literal(
                        value
                    ):
                        self._large_int_vars.add(target.id)

            case ast.AnnAssign(annotation=ann, value=value, target=target) if value:
                # Use annotation type if provided, otherwise infer from value
                ann_type = self._annotation_to_type(ann)
                if ann_type != UNKNOWN:
                    self.analyze_assignment(target, ann_type)
                else:
                    value_type = self.infer(value)
                    self.analyze_assignment(target, value_type)
                # Track if this is a large int literal assignment
                if isinstance(target, ast.Name) and self._is_large_int_literal(value):
                    self._large_int_vars.add(target.id)

            case ast.AugAssign():
                pass  # x += y doesn't change type in most cases

            case ast.For(target=target, iter=iter_expr) as for_stmt:
                # Check if loop variable has annotation (for i: i32 in range(...))
                match target:
                    case ast.Name(id=name):
                        # Check for range() to infer loop variable type
                        if (
                            isinstance(iter_expr, ast.Call)
                            and isinstance(iter_expr.func, ast.Name)
                            and iter_expr.func.id == "range"
                        ):
                            existing_type = self.var_types.get(name)
                            if not is_native_type(existing_type):
                                # Always set to INT initially
                                self.var_types[name] = INT
                                # Track if this could be i32 (range args are i32)
                                # Will be promoted to native in _analyze_native_eligibility
                                # if the variable doesn't escape
                                if self._range_args_are_i32(iter_expr.args):
                                    self._i32_loop_candidates.add(name)
                            self._loop_counter_vars.add(name)
                for s in for_stmt.body:
                    self._analyze_stmt(s)
                for s in for_stmt.orelse:
                    self._analyze_stmt(s)

            case ast.While(test=test, body=body) as while_stmt:
                # Detect while loop counter pattern: while i < n: ... i = i + 1
                loop_vars = self._detect_while_loop_counters(test, body)
                for var_name in loop_vars:
                    self._i32_loop_candidates.add(var_name)
                    self._loop_counter_vars.add(var_name)
                for s in body:
                    self._analyze_stmt(s)
                for s in while_stmt.orelse:
                    self._analyze_stmt(s)

            case ast.If():
                for s in stmt.body:
                    self._analyze_stmt(s)
                for s in stmt.orelse:
                    self._analyze_stmt(s)

    def _annotation_to_type(self, ann: ast.expr) -> BobType:
        """Convert type annotation to BobType."""
        match ann:
            # Native WASM types (unboxed, high performance)
            case ast.Name(id="i32"):
                return I32
            case ast.Name(id="i64"):
                return I64
            case ast.Name(id="f64"):
                return F64
            # Boxed Python types
            case ast.Name(id="int"):
                return INT
            case ast.Name(id="float"):
                return FLOAT
            case ast.Name(id="str"):
                return STRING
            case ast.Name(id="bool"):
                return BOOL
            case ast.Name(id="list"):
                return ListType()
            case ast.Name(id="dict"):
                return DictType()
            case ast.Name(id="tuple"):
                return TupleType()
            case ast.Constant(value=None):
                return NONE
            # Handle subscript annotations like list[float], dict[str, int]
            case ast.Subscript(value=ast.Name(id="list"), slice=slice_node):
                # list[element_type]
                elem_type = self._annotation_to_type(slice_node)
                return ListType(elem_type)
            case ast.Subscript(
                value=ast.Name(id="dict"),
                slice=ast.Tuple(elts=[key_ann, val_ann]),
            ):
                # dict[key_type, value_type]
                key_type = self._annotation_to_type(key_ann)
                val_type = self._annotation_to_type(val_ann)
                return DictType(key_type, val_type)
            case ast.Subscript(
                value=ast.Name(id="tuple"),
                slice=ast.Tuple(elts=elem_anns),
            ):
                # tuple[type1, type2, ...]
                elem_types = tuple(self._annotation_to_type(e) for e in elem_anns)
                return TupleType(elem_types)
        return UNKNOWN

    def _op_to_str(self, op: ast.operator) -> str:
        """Convert AST operator to string."""
        op_map = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.FloorDiv: "//",
            ast.Mod: "%",
            ast.Pow: "**",
            ast.LShift: "<<",
            ast.RShift: ">>",
            ast.BitOr: "|",
            ast.BitXor: "^",
            ast.BitAnd: "&",
            ast.MatMult: "@",
        }
        return op_map.get(type(op), "?")

    def _is_large_int_literal(self, node: ast.expr) -> bool:
        """Check if node is an integer literal outside i32 range."""
        match node:
            case ast.Constant(value=int() as val) if not isinstance(val, bool):
                return val < self.I32_MIN or val > self.I32_MAX
            case ast.UnaryOp(op=ast.USub(), operand=ast.Constant(value=int() as val)):
                # Handle negative literals like -2000000000
                return -val < self.I32_MIN or -val > self.I32_MAX
        return False

    def _detect_while_loop_counters(
        self, test: ast.expr, body: list[ast.stmt]
    ) -> set[str]:
        """Detect while loop counter variables that can be promoted to native i32.

        Pattern: while i < n: ... i = i + 1 (or similar increment/decrement)

        Returns set of variable names that:
        1. Appear in the while condition (comparison)
        2. Are incremented or decremented in the loop body
        3. Have int type annotation or are initialized to small integers
        """
        candidates: set[str] = set()

        # Extract variable names from comparison condition
        condition_vars = self._extract_comparison_vars(test)
        if not condition_vars:
            return candidates

        # Check which condition vars are incremented/decremented in loop body
        for var_name in condition_vars:
            if self._is_incremented_in_body(var_name, body):
                # Check if variable is int-typed
                var_type = self.var_types.get(var_name)
                if var_type == INT or is_native_type(var_type):
                    candidates.add(var_name)

        return candidates

    def _extract_comparison_vars(self, test: ast.expr) -> set[str]:
        """Extract variable names from a comparison expression."""
        vars_found: set[str] = set()

        match test:
            case ast.Compare(left=left, comparators=comparators):
                # Simple comparison: i < n, i <= n, i > 0, etc.
                if isinstance(left, ast.Name):
                    vars_found.add(left.id)
                for comp in comparators:
                    if isinstance(comp, ast.Name):
                        vars_found.add(comp.id)

            case ast.BoolOp(values=values):
                # and/or combinations
                for val in values:
                    vars_found.update(self._extract_comparison_vars(val))

            case ast.UnaryOp(op=ast.Not(), operand=operand):
                # not condition
                vars_found.update(self._extract_comparison_vars(operand))

        return vars_found

    def _is_incremented_in_body(self, var_name: str, body: list[ast.stmt]) -> bool:
        """Check if a variable is incremented or decremented in loop body."""
        for stmt in body:
            match stmt:
                # i = i + 1, i = i - 1
                case ast.Assign(
                    targets=[ast.Name(id=name)],
                    value=ast.BinOp(
                        left=ast.Name(id=left_name),
                        op=ast.Add() | ast.Sub(),
                        right=ast.Constant(value=int()),
                    ),
                ) if name == var_name and left_name == var_name:
                    return True

                # j = i + 1 where we check j later (for patterns like j: i32 = i + 1)
                case ast.AnnAssign(
                    target=ast.Name(id=name),
                    value=ast.BinOp(
                        left=ast.Name(id=left_name),
                        op=ast.Add() | ast.Sub(),
                        right=ast.Constant(value=int()),
                    ),
                ) if name == var_name and left_name == var_name:
                    return True

                # Recurse into nested structures
                case ast.If(body=if_body, orelse=else_body):
                    if self._is_incremented_in_body(var_name, if_body):
                        return True
                    if self._is_incremented_in_body(var_name, else_body):
                        return True

                case ast.While(body=while_body):
                    if self._is_incremented_in_body(var_name, while_body):
                        return True

                case ast.For(body=for_body):
                    if self._is_incremented_in_body(var_name, for_body):
                        return True

        return False

    def _range_args_are_i32(self, args: list[ast.expr]) -> bool:
        """Check if all range() arguments are i32 type.

        Returns True if all arguments are:
        - Variables with i32 type
        - Integer constants within i32 range
        - Binary operations involving i32 operands (e.g., n + 1)
        """
        for arg in args:
            arg_type = self.infer(arg)
            # Accept I32 directly
            if arg_type == I32:
                continue
            # Accept integer constants within i32 range
            if isinstance(arg, ast.Constant) and isinstance(arg.value, int):
                if self.I32_MIN <= arg.value <= self.I32_MAX:
                    continue
                return False  # Constant outside i32 range
            # Accept binary ops where result is i32 (e.g., n + 1 where n is i32)
            if isinstance(arg, ast.BinOp):
                left_type = self.infer(arg.left)
                right_type = self.infer(arg.right)
                # If either operand is i32 and other is int/constant, result is i32
                if I32 in {left_type, right_type}:
                    continue
            # Not provably i32
            return False
        return True

    def _analyze_native_eligibility(self, body: list[ast.stmt]) -> None:
        """Determine which variables can use native WASM types.

        A variable is eligible for native type if:
        1. It has an explicit native type annotation (i32, i64, f64) - ALWAYS native
        2. OR it has a known numeric type (float or int) AND doesn't "escape"
           to contexts requiring boxed values
        """
        # First: mark explicitly typed native variables (these are always native)
        for var, bob_type in self.var_types.items():
            native_type = get_native_wasm_type(bob_type)
            if native_type is not None:
                self.native_vars[var] = native_type

        # Second pass: find escaped variables (for auto-native inference)
        self._escaped_vars = set()
        for stmt in body:
            self._find_escaped_vars(stmt)

        # Third pass: mark eligible non-explicit variables as native
        # For `float` annotations, we can safely use f64 (Python float is IEEE 754 double)
        # For `int` annotations, we keep them boxed to avoid overflow issues
        for var, bob_type in self.var_types.items():
            # Skip if already marked native (explicit types like i32, i64, f64)
            if var in self.native_vars:
                continue

            if var in self._escaped_vars:
                continue  # Variable escapes, can't use native type

            # Only promote float to f64 (safe, no overflow concerns)
            # int stays boxed to avoid i32 overflow
            if isinstance(bob_type, FloatType):
                self.native_vars[var] = NativeType.F64

        # Fourth pass: promote loop counter variables that don't escape to native i32
        # Loop counters are safe for i32 because:
        # 1. They start at range start (usually 0 or small number)
        # 2. They're incremented by step (usually 1)
        # 3. They stop at range end (checked at runtime)
        # Even if range bounds are large, counter won't overflow if it doesn't escape
        for var in self._loop_counter_vars:
            if var in self.native_vars:
                continue  # Already native
            if var in self._escaped_vars:
                continue  # Escapes, can't use native
            if var in self._large_int_vars:
                continue  # Assigned large int somewhere
            self.native_vars[var] = NativeType.I32

    def _find_escaped_vars(self, node: ast.AST) -> None:
        """Find variables that escape to non-native contexts.

        A variable "escapes" if it's:
        - Passed as a function argument
        - Used in list/dict/set operations (append, etc.)
        - Used in print() or other builtins requiring boxed values
        - Returned from the function
        - Used in attribute access (obj.x = var)
        """
        match node:
            case ast.Call(args=args, keywords=keywords):
                # All arguments to function calls escape
                for arg in args:
                    self._mark_escaped(arg)
                for kw in keywords:
                    self._mark_escaped(kw.value)
                # Recurse into function expression
                self._find_escaped_vars(node.func)

            case ast.Return(value=value) if value:
                # Returned values escape (for now - could optimize later)
                self._mark_escaped(value)

            case ast.Subscript(value=container, slice=slice_expr):
                # Subscript assignment: list[i] = x -> x escapes
                # Just visiting, not marking container as escaped
                self._find_escaped_vars(container)
                self._find_escaped_vars(slice_expr)

            case ast.Assign(targets=targets, value=value):
                # Check if assigning to subscript or attribute
                for target in targets:
                    match target:
                        case ast.Subscript():
                            # list[i] = value -> value escapes
                            self._mark_escaped(value)
                        case ast.Attribute():
                            # obj.attr = value -> value escapes
                            self._mark_escaped(value)
                self._find_escaped_vars(value)

            case ast.For(body=body, orelse=orelse, iter=iter_expr):
                self._find_escaped_vars(iter_expr)
                for stmt in body:
                    self._find_escaped_vars(stmt)
                for stmt in orelse:
                    self._find_escaped_vars(stmt)

            case ast.While(body=body, orelse=orelse, test=test):
                self._find_escaped_vars(test)
                for stmt in body:
                    self._find_escaped_vars(stmt)
                for stmt in orelse:
                    self._find_escaped_vars(stmt)

            case ast.If(body=body, orelse=orelse, test=test):
                self._find_escaped_vars(test)
                for stmt in body:
                    self._find_escaped_vars(stmt)
                for stmt in orelse:
                    self._find_escaped_vars(stmt)

            case ast.Expr(value=value):
                self._find_escaped_vars(value)

            case ast.AugAssign(value=value):
                self._find_escaped_vars(value)

            case ast.BinOp(left=left, right=right):
                self._find_escaped_vars(left)
                self._find_escaped_vars(right)

            case ast.UnaryOp(operand=operand):
                self._find_escaped_vars(operand)

            case ast.Compare(left=left, comparators=comparators):
                self._find_escaped_vars(left)
                for comp in comparators:
                    self._find_escaped_vars(comp)

            case ast.List(elts=elts) | ast.Tuple(elts=elts) | ast.Set(elts=elts):
                # Elements in list/tuple/set literals escape
                for elt in elts:
                    self._mark_escaped(elt)

            case ast.Dict(keys=keys, values=values):
                for k in keys:
                    if k:
                        self._mark_escaped(k)
                for v in values:
                    self._mark_escaped(v)

            case ast.Lambda(args=args, body=body):
                # Variables used in lambda body that are not parameters escape
                # (they are captured by the closure)
                param_names = {arg.arg for arg in args.args}
                self._mark_escaped_in_lambda(body, param_names)

            case _:
                # Recurse into child nodes
                for child in ast.iter_child_nodes(node):
                    self._find_escaped_vars(child)

    def _mark_escaped(self, node: ast.expr) -> None:
        """Mark variables in expression as escaped.

        Key insight: when a computed expression escapes, only the RESULT escapes,
        not necessarily the operands used to compute it. For example:
        - `list[i]` escapes → the list ELEMENT escapes, but index `i` does NOT
        - `a + b` escapes → the SUM escapes, but `a` and `b` do NOT
        - `[a, b, c]` escapes → elements `a`, `b`, `c` DO escape (stored in list)
        """
        match node:
            case ast.Name(id=name):
                # Direct variable reference - it escapes
                self._escaped_vars.add(name)

            case ast.Subscript():
                # Subscript access: list[i] returns a value
                # The index is NOT escaped - it's just used to compute the address
                # The container is NOT escaped - we're reading from it
                # The RESULT is what escapes (but it's already boxed in the list)
                pass

            case ast.BinOp() | ast.UnaryOp() | ast.Compare():
                # Arithmetic/comparison operations: the RESULT escapes (a new computed value)
                # But operands are just used to compute the result - they don't escape
                pass

            case ast.BoolOp(values=values):
                # Boolean and/or: returns one of the operands directly (not a computed value)
                # So all operands potentially escape
                for val in values:
                    self._mark_escaped(val)

            case ast.Call():
                # Function call: arguments are handled separately in _find_escaped_vars
                # The RESULT of the call escapes, but we don't need to recurse here
                pass

            case ast.IfExp(body=body, orelse=orelse):
                # Ternary: both branches could be the result, so both escape
                self._mark_escaped(body)
                self._mark_escaped(orelse)

            case ast.List(elts=elts) | ast.Tuple(elts=elts) | ast.Set(elts=elts):
                # Collection literals: elements ARE stored, so they escape
                for elt in elts:
                    self._mark_escaped(elt)

            case ast.Dict(keys=keys, values=values):
                # Dict literal: keys and values ARE stored, so they escape
                for k in keys:
                    if k is not None:
                        self._mark_escaped(k)
                for v in values:
                    self._mark_escaped(v)

            case _:
                # For other expression types, recurse conservatively
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, ast.expr):
                        self._mark_escaped(child)

    def _mark_escaped_in_lambda(self, node: ast.AST, param_names: set[str]) -> None:
        """Mark variables in lambda body that are not parameters as escaped."""
        match node:
            case ast.Name(id=name) if name not in param_names:
                # Variable from enclosing scope - mark as escaped
                self._escaped_vars.add(name)
            case ast.Lambda(args=args, body=body):
                # Nested lambda - add its params to excluded set
                inner_params = param_names | {arg.arg for arg in args.args}
                self._mark_escaped_in_lambda(body, inner_params)
            case _:
                # Recurse into child nodes
                for child in ast.iter_child_nodes(node):
                    self._mark_escaped_in_lambda(child, param_names)

    def generic_visit(self, node: ast.AST) -> BobType:  # noqa: ARG002
        """Default: return unknown type."""
        return UNKNOWN

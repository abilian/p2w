"""Pystone benchmark.

A classic Python performance benchmark.
Adapted for p2w with i32 annotations and __slots__ for optimal performance.
"""

from __future__ import annotations


class Record:
    __slots__ = ('PtrComp', 'Discr', 'EnumComp', 'IntComp', 'StringComp')

    def __init__(
        self, PtrComp, Discr: i32, EnumComp: i32, IntComp: i32, StringComp: str
    ) -> None:
        self.PtrComp = PtrComp
        self.Discr: i32 = Discr
        self.EnumComp: i32 = EnumComp
        self.IntComp: i32 = IntComp
        self.StringComp: str = StringComp

    def clone(self):
        return Record(
            self.PtrComp, self.Discr, self.EnumComp, self.IntComp, self.StringComp
        )


TRUE: i32 = 1
FALSE: i32 = 0
IntGlob: i32 = 0
BoolGlob: i32 = 0
Char1Glob: str = ""
Char2Glob: str = ""
PtrGlb: Record = None  # type: ignore
PtrGlbNext: Record = None  # type: ignore

Ident1: i32 = 1
Ident2: i32 = 2
Ident3: i32 = 3
Ident4: i32 = 4
Ident5: i32 = 5

Array1Glob: list[int] = [0] * 51


def create_array2glob(n: i32) -> list[list[int]]:
    r: list[list[int]] = []
    for i in range(n):
        r.append(list(Array1Glob))
    return r


Array2Glob: list[list[int]] = create_array2glob(51)


def Func3(EnumParIn: i32) -> i32:
    EnumLoc: i32 = EnumParIn
    if EnumLoc == Ident3:
        return TRUE
    return FALSE


def Proc6(EnumParIn: i32) -> i32:
    EnumParOut: i32 = EnumParIn
    if not Func3(EnumParIn):
        EnumParOut = Ident4
    if EnumParIn == Ident1:
        EnumParOut = Ident1
    elif EnumParIn == Ident2:
        if IntGlob > 100:
            EnumParOut = Ident1
        else:
            EnumParOut = Ident4
    elif EnumParIn == Ident3:
        EnumParOut = Ident2
    elif EnumParIn == Ident4:
        pass
    elif EnumParIn == Ident5:
        EnumParOut = Ident3
    return EnumParOut


def Proc7(IntParI1: i32, IntParI2: i32) -> i32:
    IntLoc: i32 = IntParI1 + 2
    IntParOut: i32 = IntParI2 + IntLoc
    return IntParOut


def Proc2(IntParIO: i32) -> i32:
    IntLoc: i32 = IntParIO + 10
    EnumLoc: i32 = Ident1
    while True:
        if Char1Glob == "A":
            IntLoc = IntLoc - 1
            IntParIO = IntLoc - IntGlob
            EnumLoc = Ident1
        if EnumLoc == Ident1:
            break
    return IntParIO


def Proc3(PtrParOut):
    global IntGlob
    if PtrGlb is not None:
        PtrParOut = PtrGlb.PtrComp
    else:
        IntGlob = 100
    PtrGlb.IntComp = Proc7(10, IntGlob)
    return PtrParOut


def Proc4() -> None:
    global Char2Glob
    BoolLoc: i32 = 0
    if Char1Glob == "A":
        BoolLoc = 1
    if BoolGlob:
        BoolLoc = 1
    Char2Glob = "B"


def Proc5() -> None:
    global Char1Glob
    global BoolGlob
    Char1Glob = "A"
    BoolGlob = FALSE


def Proc8(
    Array1Par: list[int], Array2Par: list[list[int]], IntParI1: i32, IntParI2: i32
) -> None:
    global IntGlob

    IntLoc: i32 = IntParI1 + 5
    Array1Par[IntLoc] = IntParI2
    Array1Par[IntLoc + 1] = Array1Par[IntLoc]
    Array1Par[IntLoc + 30] = IntLoc
    for IntIndex in range(IntLoc, IntLoc + 2):
        Array2Par[IntLoc][IntIndex] = IntLoc
    Array2Par[IntLoc][IntLoc - 1] = Array2Par[IntLoc][IntLoc - 1] + 1
    Array2Par[IntLoc + 20][IntLoc] = Array1Par[IntLoc]
    IntGlob = 5


def Func1(CharPar1: str, CharPar2: str) -> i32:
    CharLoc1: str = CharPar1
    CharLoc2: str = CharLoc1
    if CharLoc2 != CharPar2:
        return Ident1
    else:
        return Ident2


def Func2(StrParI1: str, StrParI2: str) -> i32:
    IntLoc: i32 = 1
    CharLoc: str = "A"
    while IntLoc <= 1:
        if Func1(StrParI1[IntLoc], StrParI2[IntLoc + 1]) == Ident1:
            CharLoc = "A"
            IntLoc = IntLoc + 1
    if CharLoc >= "W" and CharLoc <= "Z":
        IntLoc = 7
    if CharLoc == "X":
        return TRUE
    else:
        if StrParI1 > StrParI2:
            IntLoc = IntLoc + 7
            return TRUE
        else:
            return FALSE


def Proc1(PtrParIn: Record) -> Record:
    NextRecord = PtrGlb.clone()
    PtrParIn.PtrComp = NextRecord
    PtrParIn.IntComp = 5
    NextRecord.IntComp = PtrParIn.IntComp
    NextRecord.PtrComp = PtrParIn.PtrComp
    NextRecord.PtrComp = Proc3(NextRecord.PtrComp)
    if NextRecord.Discr == Ident1:
        NextRecord.IntComp = 6
        NextRecord.EnumComp = Proc6(PtrParIn.EnumComp)
        NextRecord.PtrComp = PtrGlb.PtrComp
        NextRecord.IntComp = Proc7(NextRecord.IntComp, 10)
    else:
        PtrParIn = NextRecord.clone()
    NextRecord.PtrComp = None
    return PtrParIn


def Proc0(loops: i32) -> i32:
    global IntGlob
    global BoolGlob
    global Char1Glob
    global Char2Glob
    global Array1Glob
    global Array2Glob
    global PtrGlb
    global PtrGlbNext

    PtrGlbNext = Record(None, 0, 0, 0, "")
    PtrGlb = Record(PtrGlbNext, Ident1, Ident3, 40, "DHRYSTONE PROGRAM, SOME STRING")

    String1Loc: str = "DHRYSTONE PROGRAM, 1'ST STRING"
    Array2Glob[8][7] = 10

    ops: i32 = 0
    for i in range(loops):
        Proc5()
        Proc4()
        IntLoc1: i32 = 2
        IntLoc2: i32 = 3
        String2Loc: str = "DHRYSTONE PROGRAM, 2'ND STRING"
        EnumLoc: i32 = Ident2
        BoolGlob = not Func2(String1Loc, String2Loc)
        while IntLoc1 < IntLoc2:
            IntLoc3: i32 = 5 * IntLoc1 - IntLoc2
            IntLoc3 = Proc7(IntLoc1, IntLoc2)
            IntLoc1 = IntLoc1 + 1
            ops = ops + 1
        Proc8(Array1Glob, Array2Glob, IntLoc1, IntLoc3)
        PtrGlb = Proc1(PtrGlb)
        CharIndex: str = "A"
        while CharIndex <= Char2Glob:
            if EnumLoc == Func1(CharIndex, "C"):
                EnumLoc = Proc6(Ident1)
            CharIndex = chr(ord(CharIndex) + 1)
            ops = ops + 1
        IntLoc3 = IntLoc2 * IntLoc1
        IntLoc2 = IntLoc3 // IntLoc1
        IntLoc2 = 7 * (IntLoc3 - IntLoc2) - IntLoc1
        IntLoc1 = Proc2(IntLoc1)
        ops = ops + 1
    return ops


def pystones(loops: i32) -> i32:
    return Proc0(loops)


def main() -> None:
    # Reduced loops for p2w (10000 instead of 100000)
    LOOPS: i32 = 10000
    ops: i32 = pystones(LOOPS)
    print("Pystone ops:", ops)


main()

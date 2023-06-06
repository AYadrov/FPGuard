

import sys

from expression_walker import walk


def pass_simplify(exp, inputs):
    """ Applies algebraic simplifications to the expression """

    C_OR_V = {"Const", "Variable"}
    NEG_ONE = ("Integer", "-1")
    ZERO = ("Integer", "0")
    ONE = ("Integer", "1")
    TWO = ("Integer", "2")
    PI = ("SymbolicConst", "pi")
    TWO_PI = ("SymbolicConst", "two_pi")
    HALF_PI = ("SymbolicConst", "half_pi")
    EXP1 = ("SymbolicConst", "exp1")

    def _add(work_stack, count, args):
        assert(args[0] == "+")
        assert(len(args) == 3)
        left, right = args[1], args[2]

        # Collapse integer Solvers
        if left[0] == "Integer" and right[0] == "Integer":
            ret = ("Integer", str(int(left[1]) + int(right[1])))
            work_stack.append((True, count, ret))
            return

        # 0 + x -> x
        if left == ZERO:
            work_stack.append((True, count, right))
            return
        # x + 0 -> x
        if right == ZERO:
            work_stack.append((True, count, left))
            return

        # x + x:
        # if x==pi      -> two_pi
        # if x==half_pi -> pi
        # else          -> 2*x
        if left == right:
            if left == PI:
                work_stack.append((True, count, TWO_PI))
                return
            if left == HALF_PI:
                work_stack.append((True, count, PI))
                return
            work_stack.append((True, count, ("*", TWO, left)))
            return

        # (-x) + y:
        #  if x==y -> 0
        #  else    -> y-x
        if left[0] == "neg":
            if left[1] == right:
                work_stack.append((True, count, ZERO))
                return
            work_stack.append((True, count, ("-", right, left[1])))
            return
        # x + (-y):
        #  if x==y -> 0
        #  else    -> x-y
        if right[0] == "neg":
            if right[1] == left:
                work_stack.append((True, count, ZERO))
                return
            work_stack.append((True, count, ("-", left, right[1])))
            return

        # (x+y) + x -> (2*x)+y
        if left[0] == "+" and left[1] == right:
            work_stack.append((True, count, ("+", ("*", right, TWO), left[2])))
            return
        # (x+y) + y -> (2*y)+x
        if left[0] == "+" and left[2] == right:
            work_stack.append((True, count, ("+", ("*", right, TWO), left[1])))
            return
        # x + (x+y) -> (2*x)+y
        if right[0] == "+" and right[1] == left:
            work_stack.append((True, count, ("+", ("*", left, TWO), right[2])))
            return
        # x + (y+x) -> (2*x)+y
        if right[0] == "+" and right[2] == left:
            work_stack.append((True, count, ("+", ("*", left, TWO), right[1])))
            return

        # (x-y) + x -> (2*x)-y
        if left[0] == "-" and left[1] == right:
            work_stack.append((True, count, ("-", ("*", right, TWO), left[2])))
            return
        # (x-y) + y -> x
        if left[0] == "-" and left[2] == right:
            work_stack.append((True, count, left[1]))
            return
        # x + (x-y) -> (2*x)-y
        if right[0] == "-" and right[1] == left:
            work_stack.append((True, count, ("-", ("*", left, TWO), right[2])))
            return
        # x + (y-x) -> y
        if right[0] == "-" and right[2] == left:
            work_stack.append((True, count, right[1]))
            return

        # x + (n*x) -> (n+1)*x
        if right[0] == "*" and left == right[2]:
            if right[1][0] == "Integer":
                ret = ("*", ("Integer", str(int(right[1][1]) + 1)), left)
                work_stack.append((True, count, ret))
                return
            work_stack.append((True, count, ("*", ("+", right[1], ONE), left)))
            return
        # x + (x*n) -> (n+1)*x
        if right[0] == "*" and left == right[1]:
            if right[2][0] == "Integer":
                ret = ("*", ("Integer", str(int(right[2][1]) + 1)), left)
                work_stack.append((True, count, ret))
                return
            work_stack.append((True, count, ("*", ("+", right[2], ONE), left)))
            return
        # (n*x) + x -> (n+1)*x
        if left[0] == "*" and right == left[2]:
            if left[1][0] == "Integer":
                ret = ("*", ("Integer", str(int(left[1][1]) + 1)), right)
                work_stack.append((True, count, ret))
                return
            work_stack.append((True, count, ("*", ("+", left[1], ONE), right)))
            return
        # (x*n) + x -> (n+1)*x
        if left[0] == "*" and right == left[1]:
            if left[2][0] == "Integer":
                ret = ("*", ("Integer", str(int(left[2][1]) + 1)), right)
                work_stack.append((True, count, ret))
                return
            work_stack.append((True, count, ("*", ("+", left[2], ONE), right)))
            return

        work_stack.append((True, count, tuple(args)))
        return

    def _sub(work_stack, count, args):
        assert(args[0] == "-")
        assert(len(args) == 3)
        left, right = args[1], args[2]

        # Collapse integer Solvers
        if left[0] == "Integer" and right[0] == "Integer":
            ret = ("Integer", str(int(left[1]) - int(right[1])))
            work_stack.append((True, count, ret))
            return

        # 0 - x -> -x
        if left == ZERO:
            work_stack.append((True, count, ("neg", right)))
            return
        # x - 0 -> x
        if right == ZERO:
            work_stack.append((True, count, left))
            return

        # x - x -> 0
        if left == right:
            work_stack.append((True, count, ZERO))
            return

        # x - (-y):
        #  if x==y -> 2*x
        #  else    -> x+y
        if right[0] == "neg":
            if left == right[1]:
                work_stack.append((True, count, ("*", TWO, left)))
                return
            work_stack.append((True, count, ("+", left, right[1])))
            return
        # (-x) - y
        #  if x==y -> -(2*x)
        #  else    -> -(x+y)
        if right[0] == "neg":
            if left[1] == right:
                work_stack.append((True, count, ("neg", ("*", TWO, left))))
                return
            work_stack.append((True, count, ("neg", ("+", left[1], right))))
            return

        # x - (x+y) -> -y
        if right[0] == "+" and left == right[1]:
            work_stack.append((True, count, ("neg", right[2])))
            return
        # x - (y+x) -> -y
        if right[0] == "+" and left == right[2]:
            work_stack.append((True, count, ("neg", right[1])))
            return
        # (x+y) - x -> y
        if left[0] == "+" and left[1] == right:
            work_stack.append((True, count, left[2]))
            return
        # (x+y) - y -> x
        if left[0] == "+" and left[2] == right:
            work_stack.append((True, count, left[1]))
            return

        # x - (x-y) -> y
        if right[0] == "-" and left == right[1]:
            work_stack.append((True, count, right[2]))
            return
        # x - (y-x) -> (2*x)-y
        if right[0] == "-" and left == right[2]:
            work_stack.append((True, count, ("-", ("*", TWO, left), right[1])))
            return
        # (x-y) - x -> -y
        if left[0] == "-" and left[1] == right:
            work_stack.append((True, count, ("neg", left[2])))
            return
        # (x-y) - y -> x-(2*y)
        if left[0] == "-" and left[2] == right:
            work_stack.append((True, count, ("-", left[1], ("*", TWO, right))))
            return

        # x - (n*x) -> (n-1)*x
        if right[0] == "*" and left == right[2]:
            if right[1][0] == "Integer":
                ret = ("*", ("Integer", str(int(right[1][1]) - 1)), left)
                work_stack.append((True, count, ret))
                return
            work_stack.append((True, count, ("*", ("-", right[1], ONE), left)))
            return
        # x - (x*n) -> (n-1)*x
        if right[0] == "*" and left == right[1]:
            if right[2][0] == "Integer":
                ret = ("*", ("Integer", str(int(right[2][1]) - 1)), left)
                work_stack.append((True, count, ret))
                return
            ret = ("*", ("-", right[2], ONE), left)
            work_stack.append((True, count, ret))
            return
        # (n*x) - x -> (n-1)*x
        if left[0] == "*" and right == left[2]:
            if left[1][0] == "Integer":
                ret = ("*", ("Integer", str(int(left[1][1]) - 1)), right)
                work_stack.append((True, count, ret))
                return
            work_stack.append((True, count, ("*", ("-", left[1], ONE), right)))
            return
        # (x*n) - x -> (n-1)*x
        if left[0] == "*" and right == left[1]:
            if left[2][0] == "Integer":
                ret = ("*", ("Integer", str(int(left[2][1]) - 1)), right)
                work_stack.append((True, count, ret))
                return
            work_stack.append((True, count, ("*", ("-", left[2], ONE), right)))
            return

        work_stack.append((True, count, tuple(args)))
        return

    def _mul(work_stack, count, args):
        assert(args[0] == "*")
        assert(len(args) == 3)
        left, right = args[1], args[2]

        # Collapse integer Solvers
        if left[0] == "Integer" and right[0] == "Integer":
            ret = ("Integer", str(int(left[1]) * int(right[1])))
            work_stack.append((True, count, ret))
            return

        # 1 * x -> x
        if left == ONE:
            work_stack.append((True, count, right))
            return
        # x * 1 -> x
        if right == ONE:
            work_stack.append((True, count, left))
            return

        # (-1) * x -> -x
        if left == NEG_ONE:
            work_stack.append((True, count, ("neg", right)))
            return
        # x * (-1) -> -x
        if right == NEG_ONE:
            work_stack.append((True, count, ("neg", left)))
            return

        # x * x -> x^2
        if right == left:
            work_stack.append((True, count, ("pow", left, TWO)))
            return

        # (x^n) * x -> x^(n+1)
        if left[0] == "pow" and left[1] == right:
            ret = ("pow", right, ("Integer", str(int(left[2][1]) + 1)))
            work_stack.append((True, count, ret))
            return
        # x * (x^n) -> x^(n+1)
        if right[0] == "pow" and left == right[1]:
            ret = ("pow", left, ("Integer", str(int(right[2][1]) + 1)))
            work_stack.append((True, count, ret))
            return
        # (x^n) * (x^m) -> x^(n+m)
        if right[0] == "pow" and left[0] == "pow" and left[1] == right[1]:
            ret = ("pow",
                   left[1],
                   ("Integer", str(int(left[2][1]) + int(right[2][1]))))
            work_stack.append((True, count, ret))
            return

        # 2 * x:
        # if x==pi -> two_pi
        # if x==half_pi -> pi
        # else pass
        if left == TWO:
            if right == PI:
                work_stack.append((True, count, TWO_PI))
                return
            if right == HALF_PI:
                work_stack.append((True, count, PI))
                return
        # x * 2:
        # if x==pi -> two_pi
        # if x==half_pi -> pi
        # else pass
        if right == TWO:
            if left == PI:
                work_stack.append((True, count, TWO_PI))
                return
            if left == HALF_PI:
                work_stack.append((True, count, PI))
                return

        work_stack.append((True, count, tuple(args)))
        return

    def _pow(work_stack, count, args):
        assert(args[0] == "pow")
        assert(len(args) == 3)
        left, right = args[1], args[2]

        # Collapse integer Solvers
        if left[0] == "Integer" and right[0] == "Integer":
            ret = ("Integer", str(int(left[1])**int(right[1])))
            work_stack.append((True, count, ret))
            return

        # x ^ 1 -> x
        if right == ONE:
            work_stack.append((True, count, left))
            return

        # abs(x) ^ (2*n) -> x^(2*n)
        if left[0] == "abs" and right[0] == "Integer" and int(right[1]) % 2 == 0:
            work_stack.append((True, count, ("pow", left[1], right)))
            return

        # (-x) ^ (2*n) -> x^(2*n)
        if left[0] == "neg" and right[0] == "Integer" and int(right[1]) % 2 == 0:
            work_stack.append((True, count, ("pow", left[1], right)))
            return

        work_stack.append((True, count, tuple(args)))
        return

    def _neg(work_stack, count, args):
        assert(args[0] == "neg")
        assert(len(args) == 2)
        arg = args[1]

        # Collapse integer Solvers
        if arg[0] == "Integer":
            work_stack.append((True, count, ("Integer", str(-int(arg[1])))))
            return

        # Collapse integer Solvers
        if arg[0] == "Float":
            num = arg[1]
            if num[0] == "-":
                work_stack.append((True, count, ("Float", num[1:])))
                return
            work_stack.append((True, count, ("Float", "-" + num)))
            return


        # -(-x) -> x
        if arg[0] == "neg":
            work_stack.append((True, count, arg[1]))
            return

        work_stack.append((True, count, tuple(args)))
        return

    def _abs(work_stack, count, args):
        assert(args[0] == "abs")
        assert(len(args) == 2)
        arg = args[1]

        # Collapse integer Solvers
        if arg[0] == "Integer":
            work_stack.append((True, count, ("Integer", str(abs(int(arg[1]))))))
            return

        # abs(-x)     -> abs(x)
        # abs(abs(x)) -> abs(x)
        if arg[0] == "neg" or arg[0] == "abs":
            work_stack.append((True, count, ("abs", arg[1])))
            return

        # abs(x^(2*n)) -> x^2n
        if arg[0] == "pow" and int(arg[2][1]) % 2 == 0:
            work_stack.append((True, count, arg))
            return

        work_stack.append((True, count, tuple(args)))
        return

    def _cos(work_stack, count, args):
        assert(args[0] == "cos")
        assert(len(args) == 2)
        arg = args[0]

        # cos(-x) -> cos(x)
        if arg[0] == "neg":
            work_stack.append((True, count, ("cos", arg[1])))
            return

        work_stack.append((True, count, tuple(args)))
        return

    def _cosh(work_stack, count, args):
        assert(args[0] == "cosh")
        assert(len(args) == 2)
        arg = args[1]

        # cosh(-x) -> cosh(x)
        if arg[0] == "neg":
            work_stack.append((True, count, ("cosh", arg[1])))
            return

        work_stack.append((True, count, ("cosh", arg)))
        return

    def _exp(work_stack, count, args):
        assert(args[0] == "exp")
        assert(len(args) == 2)
        arg = args[1]

        # exp(1) -> exp1
        if arg == ONE:
            work_stack.append((True, count, EXP1))
            return

        work_stack.append((True, count, ("exp", arg)))
        return

    def _variable(work_stack, count, args):
        assert(args[0] == "Variable")
        assert(len(args) == 3)
        val = args[2]

        if val[0] in C_OR_V:
            work_stack.append((True, count, val))
            return

        work_stack.append((True, count, tuple(args[0:2])))
        return

    my_contract_dict = {"+":        _add,
                        "-":        _sub,
                        "*":        _mul,
                        "Variable": _variable,
                        "abs":      _abs,
                        "cos":      _cos,
                        "cosh":     _cosh,
                        "exp":      _exp,
                        "neg":      _neg,
                        "pow":      _pow}

    exp = walk(dict(), my_contract_dict, exp)

    return exp


def main(argv):
    try:
        from pass_utils import get_runmain_input
        from function_to_lexed import function_to_lexed
        from lexed_to_parsed import lexed_to_parsed
        from pass_lift_inputs_and_inline_assigns import \
            pass_lift_inputs_and_inline_assigns

        data = get_runmain_input(argv)

        tokens = function_to_lexed(data)
        tree = lexed_to_parsed(tokens)
        exp, inputs = pass_lift_inputs_and_inline_assigns(tree)

        exp = pass_simplify(exp, inputs)

        return 0

    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

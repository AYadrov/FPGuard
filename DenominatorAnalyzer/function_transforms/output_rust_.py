

import sys
import numpy as np
import re
import bigfloat as bf


from collections import OrderedDict

from output_flatten import output_flatten
from expression_walker import walk
from pass_utils import INFIX, BINOPS, UNOPS
try:
    import ASTtypes_ as ast
except ModuleNotFoundError:
    sys.path.append("../")
    import ASTtypes_ as ast


def interval2list(intvl):
    intvl = intvl.replace(']', '').replace('[', '')
    intvl = intvl.split(',')
    for i, v in enumerate(intvl):
        intvl[i] = float(v)
    return intvl


def const_reformat(const, precision=64):
    const = const.replace('[', '').replace(']', '').replace('(', '').replace(')', '')
    const = bf.BigFloat(eval(const), context=bf.precision(precision))
    return const


def value_to_ASTtype(value, name, Variables, Consts, Expressions, precision=64):
    expr = ast.Expr(name, operation=None, left_child=None, right_child=None)

    for val in value:
        if val in ast.OP_TO_RIVAL:
            expr.operation = val
        elif val in Variables:
            if expr.left_child == None:
                expr.left_child = Variables[val]
            else:
                expr.right_child = Variables[val]
        elif val in Consts:
            if expr.left_child == None:
                expr.left_child = Consts[val]
            else:
                expr.right_child = Consts[val]
        elif val in Expressions:
            if expr.left_child == None:
                expr.left_child = Expressions[val]
            else:
                expr.right_child = Expressions[val]
        elif re.match(r"-?\d+(.0)?\)$", val):           # Catch "[int])" for pow function
            val = val.replace(")", "")
            for c in Consts:
                if bf.equal(Consts[c].value, bf.BigFloat(val)):
                    expr.right_child = Consts[c]
                    break
            if expr.right_child is None:
                new_const_name = "$_const_" + str(len(Consts))
                Consts[new_const_name] = \
                    ast.Const(name=new_const_name, value=bf.BigFloat(val, context=bf.precision(precision)))
                expr.right_child = Consts[new_const_name]
    return expr


def output_rust_(exp, inputs, consts, assigns, precision=64):
    Variables = OrderedDict()
    for name, input in inputs.items():
        interval = interval2list(output_flatten(("Return", input)))
        Variables[name] = ast.Var(name=name, range=interval)

    Consts = OrderedDict()
    for name, const in consts.items():
        value = const_reformat(output_flatten(("Return", const)), precision=precision)
        Consts[name] = ast.Const(name=name, value=value)

    seen_assigns = set()
    Expressions = OrderedDict()
    DivExpressions = []

    def _e_variable(work_stack, count, exp):
        assert(exp[0] == "Variable")
        assert(len(exp) == 2)
        assert(exp[1] in assigns)
        if exp[1] in seen_assigns:
            work_stack.append((True, count, [exp[1]]))
            return
        seen_assigns.add(exp[1])
        work_stack.append((True,  count, exp[0]))
        work_stack.append((True,  2,     exp[1]))
        work_stack.append((False, 2,     assigns[exp[1]]))

    def _input(work_stack, count, exp):
        assert(exp[0] == "Input")
        assert(len(exp) == 2)
        work_stack.append((True, count, [exp[1]]))

    def _const(work_stack, count, exp):
        assert(exp[0] == "Const")
        assert(len(exp) == 2)
        work_stack.append((True, count, [exp[1]]))

    my_expand_dict = {"Input": _input,
                      "Const": _const,
                      "Variable": _e_variable}

    def _c_variable(work_stack, count, args):
        nonlocal Expressions
        nonlocal DivExpressions
        assert(args[0] == "Variable")
        assert(len(args) == 3)
        name = args[1]
        value = args[2]
        if value != None:
            Expressions[name] = value_to_ASTtype(value, name, Variables, Consts, Expressions)
            if Expressions[name].operation == '/':
                DivExpressions.append(name)

        work_stack.append((True, count, [name]))

    def _infix(work_stack, count, args):
        assert(args[0] in INFIX)
        assert(len(args) == 3)
        op = args[0]
        left = args[1]
        right = args[2]
        work_stack.append((True, count, left + [" ", op, " "] + right))

    def _binop(work_stack, count, args):
        assert(args[0] in BINOPS or args[0] == "powi")
        assert(len(args) == 3)
        op = args[0]
        first = args[1]
        secon = args[2]
        ret = [op, "("] + first + [", "] + secon + [")"]
        work_stack.append((True, count, ret))

    def _pow(work_stack, count, args):
        assert(args[0] == "pow")
        assert(len(args) == 3)
        base = args[1]
        expo = args[2]
        assert(expo[0] == "Integer")
        ret = ["pow("] + base + [", ", expo[1] + ")"]
        work_stack.append((True, count, ret))

    def _unop(work_stack, count, args):
        assert(args[0] in UNOPS)
        assert(len(args) == 2)
        op = args[0]
        arg = args[1]
        work_stack.append((True, count, [op, "("] + arg + [")"]))

    def _box(work_stack, count, args):
        assert(args[0] == "Box")
        if len(args) == 1:
            work_stack.append((True, count, ["None"]))
            return
        # box = ["Some(vec!["]
        # for sub in args[1:]:
        #     box += sub + [", "]
        # box = box[0:-1] + ["])"]
        box = ""
        work_stack.append((True, count, None))

    def _tuple(work_stack, count, args):
        assert(args[0] == "Tuple")
        assert(len(args) == 3)
        ret = ["("] + args[1] + [", "] + args[2] + [")"]
        work_stack.append((True, count, ret))

    def _return(work_stack, count, args):
        assert(args[0] == "Return")
        assert(len(args) == 2)
        return ["    "] + args[1]

    def _neg(work_stack, count, args):
        assert(args[0] == "neg")
        assert(len(args) == 2)
        work_stack.append((True, count, ["-("] + args[1] + [")"]))

    my_contract_dict = dict()
    my_contract_dict.update(zip(BINOPS,
                                [_binop for _ in BINOPS]))
    my_contract_dict.update(zip(UNOPS,
                                [_unop for _ in UNOPS]))
    my_contract_dict.update(zip(INFIX,
                                [_infix for _ in INFIX]))
    my_contract_dict["pow"] = _pow
    my_contract_dict["Variable"] = _c_variable
    my_contract_dict["Box"] = _box
    my_contract_dict["neg"] = _neg
    my_contract_dict["Tuple"] = _tuple
    my_contract_dict["Return"] = _return
    retval = walk(my_expand_dict, my_contract_dict, exp, assigns)

    name = "_expr_" + str(len(Expressions))

    if retval != None:
        Expressions[name] = value_to_ASTtype(retval, name, Variables, Consts, Expressions)
        Expressions[name].root = True
        if Expressions[name].operation == '/':
            DivExpressions.append(name)

    return Expressions, Variables, Consts, DivExpressions


def main(argv):
    try:
        from pass_utils import get_runmain_input
        from function_to_lexed import function_to_lexed
        from lexed_to_parsed import lexed_to_parsed
        from pass_lift_inputs_and_inline_assigns import \
            pass_lift_inputs_and_inline_assigns
        from pass_simplify import pass_simplify
        from pass_reverse_diff import pass_reverse_diff
        from pass_lift_consts import pass_lift_consts
        from pass_single_assignment import pass_single_assignment

        data = get_runmain_input(argv)

        tokens = function_to_lexed(data)
        tree = lexed_to_parsed(tokens)
        exp, inputs = pass_lift_inputs_and_inline_assigns(tree)
        exp = pass_simplify(exp, inputs)
        d, diff_exp = pass_reverse_diff(exp, inputs)
        diff_exp = pass_simplify(diff_exp, inputs)
        c, diff_exp, consts = pass_lift_consts(diff_exp, inputs)
        diff_exp, assigns = pass_single_assignment(diff_exp, inputs)

        rust_function = output_rust_(diff_exp, inputs, consts, assigns)


        return 0

    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

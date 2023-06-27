import sys

from function_to_lexed import function_to_lexed
from lexed_to_parsed import lexed_to_parsed
from pass_lift_inputs_and_inline_assigns import \
    pass_lift_inputs_and_inline_assigns
from pass_simplify import pass_simplify
from pass_lift_consts import pass_lift_consts
from pass_single_assignment import pass_single_assignment
from output_rust_ import output_rust_



def process_function_(data, invert=False, precision=64):
    tokens = function_to_lexed(data)
    tree = lexed_to_parsed(tokens)
    exp, inputs = pass_lift_inputs_and_inline_assigns(tree)
    if invert:
        exp = ("Return", ("neg", exp[1]))
    exp = pass_simplify(exp, inputs)
    # d, diff_exp = pass_reverse_diff(exp, inputs)
    # diff_exp = pass_simplify(diff_exp, inputs)
    c, diff_exp, consts = pass_lift_consts(exp, inputs)
    sa_exp, assigns = pass_single_assignment(diff_exp, inputs)

    Expressions, Variables, Consts, DivExpressions = output_rust_(sa_exp, inputs, consts, assigns, precision=precision)
    return Expressions, Variables, Consts, DivExpressions


def main(argv):
    try:
        from pass_utils import get_runmain_input
        data = get_runmain_input(argv)
        inputs, consts, rival_functions, interp_function, rival_functions_info = process_function_(data)
        return 0

    except KeyboardInterrupt:
        return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))

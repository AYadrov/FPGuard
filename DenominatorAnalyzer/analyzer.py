from collections import OrderedDict
from sympy import symbols, solve
import os

from function_transforms.process_function_ import process_function_


def rival_check(boxes, expressions, divExpressions, variables):
    for exp in divExpressions:
        arguments = expressions[exp].getArgs()

        result = check_for_error(arguments, expressions[exp], variables, boxes)
        if result.err_possible is not True and result.err_exact is not True:
            print("No error from rival side for ", expressions[exp].__str__())
        else:
            print("Rival found error for ", expressions[exp].__str__())


def check_for_error(args, exp, Variables, valid_intervals):
    """
    Description:
        Function calls Rival to doublecheck for errors within expression under given valid intervals found by RealPaver
    Input:
        args: A list of variables that exist in the analyzing expression
        exp: Expression that was analyzed and for which RealPaver produced valid boxes
        Variables: A pointer to the variables within a computational graph (by changing them - we change intervals that
            are given to Rival as well)
        valid_intervals: Input boxes that guarantee not to have division violations with them in exp
    Output:
        result: None if errors have not been found, error, if division violation exists
    """
    result = None
    for i in range(len(valid_intervals[args[0]])):
        for var in valid_intervals:
            Variables[var].range = valid_intervals[var][i]
        result = exp.evaluate()
        if result.err_possible or result.err_exact:
            for v in Variables:
                Variables[v].range = Variables[v].full_range

            print(result)
            for v in valid_intervals:
                print(v, valid_intervals[v][i])
            return result
    return result


def solver(constraints, arguments, exp, eps):
    """
    Description:
        Function creates problem statements for obtaining constraints that neighbour the region around division violation
            and calls solver SymPy to find constraints;
    Input:
        constraints: A set of constraints that will be filled up with found ones (it is kinda an aggregator);
        arguments: Input variables with intervals that participate in the current solving expression;
        exp: An expression that contains division operation that violates division
        eps: Distance to the neighbouring region
    Output:
        constraints: A set with found constraints
    """
    if eps <= 0:
        raise ValueError("eps should be > 0")
    args = symbols(", ".join(chr(i + 97) for i, _ in enumerate(arguments)))
    try:
        args = [*args]
    except TypeError:
        args = [args]
    eq = exp.strDenominator()
    # constraint = f"(<<{eq} - {eps} >= 1e-300>>|<<{eq} + {eps} <= 1e-300>>)"
    # # constraint = f"min(-({eq}) + {eps}, {eq} + {eps}) <= 1e-323"
    # constraints.add(constraint)
    # return constraints


    # print(eq, "!= 0")
    for i, x in enumerate(arguments):
        if i + 97 >= 101:  # 'e' symbol, we can not use it for decoding since we have numbers 1.0e-15
            eq = eq.replace(x, chr(i + 1 + 97))
        else:
            eq = eq.replace(x, chr(i + 97))
    for arg in args:
        res = str(solve(eq, arg))

        res = res.strip('][').split(', ')

        if ord(arg.name) >= 102:
            variable = arguments[ord(arg.name) - 98]
        else:
            variable = arguments[ord(arg.name) - 97]

        for r in res:
            if r:
                for i, x in enumerate(arguments):
                    if i + 97 >= 101:
                        r = r.replace(chr(i + 1 + 97), x).replace('[', '').replace(']', '')
                    else:
                        r = r.replace(chr(i + 97), x).replace('[', '').replace(']', '')
                if r.__contains__("sqrt"):
                    continue

                try:
                    r = float(r) # Sometimes r can be 0 and sometimes 0.0. We want this to be the same as a string
                except:
                    pass

                # constraint = f"min({variable} - ({str(r)}) + {eps}, -({variable} - ({str(r)})) + {eps}) <= 0"
                constraint = f"(<<{variable} - ({str(r)}) + {eps} <= 0>>|<<-1.0 * ({variable} - ({str(r)})) + {eps} <= 0>>)"
                constraints.add(constraint)
    return constraints


def analyze_symbolic_expression(symb_expr, eps):
    """
    Description:
        Function parses given symbolic expression, extracts all the division operations from it
            in a computational graph format, evaluate all obtained division operations using Rival for division violation
            and call the function 'solver' to find constraints for the possible errors that can be avoided;
    Input:
        symb_expr: Symbolic expression input in the following syntax:
            "var1=[-1,1];var2=[-2,0];(var1>0)&(var2<0);var1-var2;"
            ^input intervals         ^constraints      ^symbolic expression
        eps: Distance to the neighbouring region that is going to be avoided due division by zero (see paper). Eps value
            is used by solver SymPy;
    Output:
        Variables: Variables with intervals that were obtained while parsing symb_expr;
        constraints_list: List of the obtained constraints found by solver
            (Empty if there is no division violations that can be avoided);
        Expressions: Computational Graph of parsed symb_expr;
        DivExpressions: Nodes from Computational Graph which contain division in their root.
    """
    Expressions, Variables, Consts, DivExpressions = process_function_(symb_expr)

    constraints_list = set()
    DivExpressions = list(set(DivExpressions))
    for exp in DivExpressions:
        denominator_arguments = Expressions[exp].getDenominatorArgs()

        res = Expressions[exp].evaluate()
        if res.err_exact:
            print(f"fDenominatorAnalyzer: unable to avoid infinity in denominator:\n{Expressions[exp].strDenominator()}")
        if res.err_possible:
            constraints_list = solver(constraints_list, denominator_arguments, Expressions[exp], eps)

    return Variables, list(constraints_list), Expressions, DivExpressions


def create_input_paver_file(variables, constraints, precision=0.01):
    """
    Description:
        Function creates input file (problem statement) for RealPaver tool under given input intervals and constraints
            and return it as string
    Input:
        variables: Input variables with intervals, with respect to them the problem will be solved;
        constraints: Constraints for these input variables;
        precision: Precision for obtaining valid input boxes used by RealPaver (see documentation of RealPaver);
    Output:
        out: Input file for RealPaver in string format.
    """
    out = "Output  mode      = union ;\n\n"
    out += f"Branch  precision = {str(precision)} ,\n" \
           "    number = +oo ;\n\n"
    out += "Constants"

    out += "Variables"
    for var in variables:
        out += f"\n    real {var} in [{variables[var].full_range[0]}, {variables[var].full_range[1]}] ,"
    out = out[:-1] + ";\n\n"

    out += "Constraints"
    for con in constraints:
        for c in constraints[con]:
            out += f"\n    {c} ,"
    out = out[:-1] + ";"
    return out


def find_valid_boxes(symb_expr, eps=0.05, precision=0.01, print_info=False, check=False):
    """
    Description:
        Function can obtain constraints to avoid infinity values due division by zero
            and create all possible interval boxes that will satisfy obtained + given constraints;
    Input:
        symb_expr: Symbolic expression input in the following syntax:
            "var1=[-1,1];var2=[-2,0];(var1>0)&(var2<0);var1-var2;"
            ^input intervals         ^constraints      ^symbolic expression
        eps: Distance to the neighbouring region that is going to be avoided due division by zero (see paper);
        precision: Precision for obtaining valid input boxes used by RealPaver;
        print_info: Verbose flag (False means do not print information);
        check: If True, then the function will check the results of RealPaver's output
            by calling Rival and check for possible errors;
    Output:
        boxes: All the found valid boxes by RealPaver under the given constraints and input intervals;
        inner_boxes: All the found INNER boxes by RealPaver under the given constraints and input intervals
            INNER BOXES are the boxes that are on the border with provided constraints.
    """
    variables, constraints, expressions, divExpressions = analyze_symbolic_expression(symb_expr, eps)

    if not any(constraints[v] for v in variables):
        print("No constraints for the symbolic expression, analysis is safe")
        boxes = OrderedDict([(v, variables[v].full_range) for v in variables])
        print(boxes)
        return boxes

    if print_info:
        print("Divisions in the symbolic expression:")
        for e in divExpressions:
            print(expressions[e].__str__())
        print()

    input_file = create_input_paver_file(variables, constraints, precision=precision)

    if print_info:
        print("\n\nRealpaver file:\n", input_file, '\n')

    try:
        with open("paver_input.txt", 'w+') as f:
            f.write(input_file)

        from realpaver import pave_boxes
        boxes, inner_boxes = pave_boxes(expressions, divExpressions, variables, show2d=True, check=check)

    finally:
        os.remove('paver_input.txt')

    return boxes, inner_boxes


if __name__ == '__main__':
    symb_expr = """
    var_1 = [-1.0, 1.0];
    var_10 = [-1.0, 1.0];
    var_11 = [-1.0, 1.0];
    var_12 = [-1.0, 1.0];
    var_2 = [-1.0, 1.0];
    var_3 = [-1.0, 1.0];
    var_7 = [-1.0, 1.0];
    var_8 = [-1.0, 1.0];
    var_9 = [-1.0, 1.0];
    abs(1.11022302462516e-16/(1e-15 + 1.8477e-307*var_12)) + abs(1.758498209304e-303/((1e-15 - var_7 - var_8)*(1e-15 + 1.8477e-307*var_12))) + abs(4.03020989035507e-81/((1e-15 - var_7 - var_8)*(1e-15 + 1.8477e-307*var_12))) + abs(1.0*var_11/(1e-15 + 1.8477e-307*var_12)) + abs(1.0*(1.0881e+306*var_9*var_10 + (1.4584e+305 - 1.19870000000013e-311*var_3 - 1.758498209304e-318*(1e-15 + 1.08400000204976e-315*var_1/(1e-15 + var_2))^(-1))/(1e-15 - var_7 - var_8))/(1e-15 + 1.8477e-307*var_12)) + abs(1.0*(-var_11 + 1.0881e+306*var_9*var_10 + (1.4584e+305 - 1.19870000000013e-311*var_3 - 1.758498209304e-318*(1e-15 + 1.08400000204976e-315*var_1/(1e-15 + var_2))^(-1))/(1e-15 - var_7 - var_8))/(1e-15 + 1.8477e-307*var_12)) + abs(2.0*(-var_11 + 1.0881e+306*var_9*var_10 + (1.4584e+305 - 1.19870000000013e-311*var_3 - 1.758498209304e-318*(1e-15 + 1.08400000204976e-315*var_1/(1e-15 + var_2))^(-1))/(1e-15 - var_7 - var_8))/(1e-15 + 1.8477e-307*var_12)) + abs(1.61914925911333e+289/((1e-15 + 1.8477e-307*var_12)*(1e-30 - 2e-15*var_7 - 2e-15*var_8 + 2*var_7*var_8 + var_7^2 + var_8^2))) + abs(1.20803367309463e+290*var_10/(1e-15 + 1.8477e-307*var_12)) + abs(1.20803367309463e+290*var_9/(1e-15 + 1.8477e-307*var_12)) + abs(3.516996418608e-318/((1e-15 - var_7 - var_8)*(1e-15 + 1.8477e-307*var_12)*(1e-15 + 1.08400000204976e-315*var_1/(1e-15 + var_2)))) + abs(1.19870000000013e-311*var_3/((1e-15 - var_7 - var_8)*(1e-15 + 1.8477e-307*var_12))) + abs(1.0*(-1.4584e+305 + 1.19870000000013e-311*var_3)/((1e-15 - var_7 - var_8)*(1e-15 + 1.8477e-307*var_12))) + abs(1.0*(-1.4584e+305 + 1.19870000000013e-311*var_3 + 1.758498209304e-318*(1e-15 + 1.08400000204976e-315*var_1/(1e-15 + var_2))^(-1))/((1e-15 - var_7 - var_8)*(1e-15 + 1.8477e-307*var_12))) + abs(1.0*(1.4584e+305 - 1.19870000000013e-311*var_3 - 1.758498209304e-318*(1e-15 + 1.08400000204976e-315*var_1/(1e-15 + var_2))^(-1))/((1e-15 - var_7 - var_8)*(1e-15 + 1.8477e-307*var_12))) + abs(2.0*(1.4584e+305 - 1.19870000000013e-311*var_3 - 1.758498209304e-318*(1e-15 + 1.08400000204976e-315*var_1/(1e-15 + var_2))^(-1))/((1e-15 - var_7 - var_8)*(1e-15 + 1.8477e-307*var_12))) + abs(1.0881e+306*var_9*var_10/(1e-15 + 1.8477e-307*var_12)) + abs(1.0*(1.085e-174 - var_7)*(-1.4584e+305 + 1.19870000000013e-311*var_3 + 1.758498209304e-318*(1e-15 + 1.08400000204976e-315*var_1/(1e-15 + var_2))^(-1))/((1e-15 - var_7 - var_8)^2*(1e-15 + 1.8477e-307*var_12))) + abs(1.0*(1.085e-174 - var_7 - var_8)*(-1.4584e+305 + 1.19870000000013e-311*var_3 + 1.758498209304e-318*(1e-15 + 1.08400000204976e-315*var_1/(1e-15 + var_2))^(-1))/((1e-15 - var_7 - var_8)^2*(1e-15 + 1.8477e-307*var_12))) + abs(-1.97626258336499e-323*var_11/(1e-30 + 3.70549234380935e-322*var_12) + 2.9917020860637e-18*1/((1e-15 - var_7 - var_8)*(1e-30 + 3.70549234380935e-322*var_12)) + 2.23208381777695e-17*var_9*var_10/(1e-30 + 3.70549234380935e-322*var_12)) + abs(-1.8477e-307*var_11*var_12/(1e-30 + 3.70549234380935e-322*var_12) + 0.0269468568*var_12/((1e-15 - var_7 - var_8)*(1e-30 + 3.70549234380935e-322*var_12)) + 0.201048237*var_9*var_10*var_12/(1e-30 + 3.70549234380935e-322*var_12))
    """
    print(analyze_symbolic_expression(symb_expr, 0.001)[1])
    # find_valid_boxes(symb_expr, safe_interval=0.1, precision=0.01, print_info=True, check=True)
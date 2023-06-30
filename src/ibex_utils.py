import os
import sys
import re
import subprocess

from ply.lex import LexError

import Globals
from sly import Lexer

import ops_def as ops

sys.path.append(os.path.join(os.environ['SAT_ROOT'], "DenominatorAnalyzer"))
sys.path.append(os.path.join(os.path.join(os.environ['SAT_ROOT'], "DenominatorAnalyzer"), "function_transforms"))
from analyzer import analyze_symbolic_expression

PASSED = "PASSED"

class IbexOutputParser(Lexer):
    def __init__(self):
        self.best_points = None
        self.best_bound = None
        self.number_of_cells = None
        self.cpu_time = None
        self.abs_prec = None
        self.infeasible = None
        self.rel_prec = None

    tokens = {PASSED}

    ignore = " \t"

    PASSED = r'\x1b\[32m \[passed\] \x1b\[0m'

    current_token = None
    tok = None

    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += len(t.value)

    @_(r'\x1b\[32m optimization successful\!\n\x1b\[0m\n')
    def OPTIMIZATION_SUCCESSFUL(self, t):
        return t

    @_(r'\x1b\[31m possibly unbounded objective \(f\*\=[-+]oo\)\n\x1b\[0m')
    def UNBOUNDED(self, t):
        return t

    # @_(r'\x1b\[31m infeasible problem\n\x1b\[0m')

    @_(r'(\x1b\[31m infeasible problem\n\x1b\[0m|infeasible problem)|(x\* \=\t\-\-\n\t\(no feasible point found\))')
    def INFEASIBLE_PROBLEM(self, t):
        return t

    @_(r'\x1b\[31m time limit [0-9]+s. reached \n\x1b\[0m')
    def TIMEOUT_REACHED(self, t):
        return t

    @_(r'\x1b\[31m unreached precision\n\x1b\[0m\n')
    def UNREACHED_PRECISION(self, t):
        return t

    @_(r'relative precision on f\*\:\t*[+-]?(([0-9]*[.])?[0-9]+(e[-+]?[0-9]*)?|nan|inf)')
    def RELATIVE_PRECISION(self, t):
        rel_prec = list(re.findall(r'[-+]?(?:\d*\.*\d+|inf|nan)(?:[eE][-+]\d+)?', t.value))
        if len(rel_prec) == 1:
            t.value = float(rel_prec[0])
        else:
            raise LexError(f'Cannot convert relative precision = {str(rel_prec)} to the float number!', rel_prec)
        return t

    @_(r'absolute precision on f\*\:\t*[+-]?(([0-9]*[.])?[0-9]+(e[-+]?[0-9]*)?|nan|inf)')
    def ABSOLUTE_PRECISION(self, t):
        abs_prec = list(re.findall(r'[-+]?(?:\d*\.*\d+|inf|nan)(?:[eE][-+]\d+)?', t.value))
        if len(abs_prec) == 1:
            t.value = float(abs_prec[0])
        else:
            raise LexError(f'Cannot convert absolute precision = {str(abs_prec)} to the float number!', abs_prec)
        return t

    @_(r'cpu time used\:\t*([0-9]*[.])?[0-9]+(e[-+]?[0-9]*)?s')
    def CPU_TIME(self, t):
        cpu_time = list(re.findall(r'[-+]?(?:\d*\.*\d+)(?:[eE][-+]\d+)?', t.value))
        if len(cpu_time) == 1:
            t.value = float(cpu_time[0])
        else:
            raise LexError(f'Cannot convert cpu time = {str(cpu_time)} to the float number!', cpu_time)
        return t

    @_(r'number of cells\:\t*\d+')
    def NUMBER_OF_CELLS(self, t):
        number_of_cells = list(re.findall(r'\d+', t.value))
        if len(number_of_cells) == 1:
            t.value = int(number_of_cells[0])
        else:
            raise LexError(f'Cannot convert number_of_cells = {str(number_of_cells)} to the integer number!',
                           number_of_cells)
        return t

    @_(r"(\*)+ setup (\*)+[a-zA-Z0-9:.\n\t-_ ]+(\*)*\n\nrunning............\n\n")
    def SETUP(self, t):
        pass

    @_(r'\(best bound\)|\(best feasible point\)')
    def COMMENT(self, t):
        pass

    @_(r'[+-]?([0-9]*[.])?[0-9]+(e-[0-9]*)?')
    def NUMBER(self, t):
        return t

    @_(r'f\* in\t\[[+-]?(([0-9]*[.])?[0-9]+(e[-+]?[0-9]*)?|inf|nan)\,[+-]?(([0-9]*[.])?[0-9]+(e[-+]?[0-9]*)?|inf|nan)\]')
    def FBOUND(self, t):
        f_bound = list(re.findall(r'[-+]?(?:\d*\.*\d+|inf|nan)(?:[eE][-+]\d+)?', t.value))
        if len(f_bound) == 2:
            f_bound[0] = float(f_bound[0])
            f_bound[1] = float(f_bound[1])
            t.value = f_bound
        else:
            raise LexError(f'Cannot convert f* bound = {str(f_bound)} to the list of two float numbers!', f_bound)
        return t

    @_(r'x\* =\t\([+-]?(([0-9]*[.])?[0-9]+(e[-+]?[0-9]*)?|nan|inf)( \; [+-]?(([0-9]*[.])?[0-9]+(e[-+]?[0-9]*)?|nan|inf))*\)')
    def XBOUND(self, t):
        best_points = list(re.findall(r'[-+]?(?:\d*\.*\d+|inf|nan)(?:[eE][-+]\d+)?', t.value))
        if len(best_points):
            for i in range(len(best_points)):
                best_points[i] = float(best_points[i])
            t.value = best_points
        else:
            raise LexError(f'Cannot convert x* points = {str(best_points)} to the list of float numbers!', best_points)
        return t

    @_(r'results written in [a-zA-Z0-9.~() \n_]*')
    def ENDING(self, t):
        pass

    def error(self, t):
        print('Line %d: Bad character %r' % (self.lineno, t.value[0:]))


def simplify_res(res):
    for i, r in enumerate(res):
        for j in range(i+1, len(res)):
            if res[i] is not None and res[j] is not None:
                if isinstance(res[i][0], str):
                    res[i][0] = {res[i][0]}
                if isinstance(res[j][0], str):
                    res[j][0] = {res[j][0]}
                if res[i][0] <= res[j][0]:
                    res[j] = None
                elif res[i][0] >= res[j][0]:
                    res[i] = None

    return [x for x in res if x is not None]


def preprocess_constraints(constraints):
    constraints = constraints.replace(" ", '')

    processed_conds = {}
    counter = 0

    inequality = r'\(*([a-zA-Z0-9-+/*.()_, ]+(>=|==|>|<|<=|!=)[a-zA-Z0-9-+/*.()_ ]+|[0-9a-zA-Z]+)\)*'
    inequality = inequality + r"(" + "\&" + inequality + ")*"
    expression = (r"<<" + inequality + r">>" + r'([&|])' + r"<<" + inequality + r">>")
    expression = re.compile(expression)

    while re.search(expression, constraints):
        found_expr = re.search(expression, constraints).group(0)
        if found_expr.__contains__('>&<'):
            L = found_expr.split(r'>>&<<')
            L[0] = L[0].replace("<<", "")
            L[1] = L[1].replace(">>", "")
            try:
                l_number = L[0]
                L[0] = processed_conds[L[0]]
                del processed_conds[l_number]
            except:
                pass
            try:
                r_number = L[1]
                L[1] = processed_conds[L[1]]
                del processed_conds[r_number]
            except:
                pass

            res = ops._BOPS2['AND'](L)
            if isinstance(res, list):
                res = simplify_res(res)
            processed_conds[str(counter)] = res
            constraints = constraints.replace("(" + found_expr + ")", "<<" + str(counter) + ">>", 1)
            if not constraints.__contains__("<<" + str(counter) + ">>"):
                constraints = constraints.replace(found_expr, "<<" + str(counter) + ">>", 1)
            counter += 1

        elif found_expr.__contains__('>|<'):
            L = found_expr.split(r'>>|<<')
            L[0] = L[0].replace("<<", "")
            L[1] = L[1].replace(">>", "")
            try:
                l_number = L[0]
                L[0] = processed_conds[L[0]]
                del processed_conds[l_number]
            except:
                pass

            try:
                r_number = L[1]
                L[1] = processed_conds[L[1]]
                del processed_conds[r_number]
            except:
                pass

            res = ops._BOPS2['OR'](L)
            if isinstance(res, list):
                res = simplify_res(res)
            processed_conds[str(counter)] = res
            constraints = constraints.replace("(" + found_expr + ")", "<<" + str(counter) + ">>", 1)
            if not constraints.__contains__("<<" + str(counter) + ">>"):
                constraints = constraints.replace(found_expr, "<<" + str(counter) + ">>", 1)
            counter += 1
        else:
            raise ValueError("No matches")
    constraints = constraints.replace("<<", '').replace(">>", '')

    try:
        return processed_conds[constraints]
    except KeyError:
        return constraints


def ibex_preprocess_inputs(cond_expr, externConstraints):

    if cond_expr == Globals.__T__:
        cond_expr = None

    if cond_expr != "" and externConstraints != "" and cond_expr is not None:
        cond_expr = cond_expr.replace("(<<True>>)", "<<True>>").replace("(<<False>>)", "<<False>>")
        constraints = "" + cond_expr + "&" + externConstraints + ""
        constraints = preprocess_constraints(constraints)
    elif cond_expr != "" and cond_expr is not None:
        constraints = preprocess_constraints(cond_expr)
    elif externConstraints != "":
        constraints = preprocess_constraints(externConstraints)
    else:
        constraints = None


    if isinstance(constraints, list):
        for i in range(len(constraints)):
            constraints[i][0] = '&'.join(constraints[i][0])
            constraints[i][0] = re.sub(r'\&\&', "&", constraints[i][0])
            constraints[i][0] = re.sub(r'\|\|', "|", constraints[i][0])
            constraints[i][0] = re.sub(r'\&', ";\n", constraints[i][0])
            constraints[i][0] = re.sub(r'\*\*', "^", constraints[i][0])
            constraints[i][0] = re.sub(r'Abs', "abs", constraints[i][0])
            constraints[i][0] = re.sub(r're\b', "", constraints[i][0])
            constraints[i][0] = re.sub(r'im\b', "0.0*", constraints[i][0])
            constraints[i][0] = re.sub(r'\(True\)\;\n', "", constraints[i][0])
            constraints[i][0] = re.sub(r'\(True\)', "", constraints[i][0])
            constraints[i][0] = re.sub(r'True;\n', "", constraints[i][0])
            constraints[i][0] = re.sub(r'True', "", constraints[i][0])
            constraints[i][0] = re.sub(r'\<\<', "(", constraints[i][0])
            constraints[i][0] = re.sub(r'\>\>', ")", constraints[i][0])
            constraints[i][0] = re.sub(r'False', "1<=0", constraints[i][0])
            constraints[i][0] = re.sub(r'inf.0', "inf", constraints[i][0])
            constraints[i][0] = re.sub(r'inf', "1.79769313486e+308", constraints[i][0])
            constraints[i][0] += ";\n"

            # constraints[i][0] = re.sub(r'\*I', "*0.0", constraints[i][0])
    elif constraints is None:
        constraints = None
    else:
        constraints = re.sub(r'\&\&', "&", constraints)
        constraints = re.sub(r'\|\|', "|", constraints)
        constraints = re.sub(r'\&', ";\n", constraints)
        constraints = re.sub(r'\*\*', "^", constraints)
        constraints = re.sub(r'Abs', "abs", constraints)
        constraints = re.sub(r're\b', "", constraints)
        constraints = re.sub(r'im\b', "0.0*", constraints)
        constraints = re.sub(r'\<\<', "(", constraints)
        constraints = re.sub(r'\>\>', ")", constraints)
        constraints = re.sub(r'\(True\);\n', "", constraints)
        constraints = re.sub(r'\(True\)', "", constraints)
        constraints = re.sub(r'True;\n', "", constraints)
        constraints = re.sub(r'True', "", constraints)
        constraints = re.sub(r'False', "1<=0", constraints)
        constraints = re.sub(r'inf.0', "inf", constraints)
        constraints = re.sub(r'inf', "1.79769313486e+308", constraints)  # Ibex doesn't know what inf is. 1.79769313486e+308 is a max number in Ibex

        # constraints = re.sub(r'\*I', "*0.0", constraints)
        if constraints == "":
            constraints = None
        else:
            constraints = [[constraints + ";\n"]]
    return constraints


def ibex_create_input(inputStr, str_expr, constraints):
    ibex_file = ""
    ibex_file += "constants\n"
    ibex_file += "variables\n"
    ibex_file += inputStr
    ibex_file += f"minimize {str_expr};\n"
    ibex_file += "constraints\n"
    if Globals.enable_constr and constraints:
        ibex_file += constraints
    ibex_file += "end"
    return ibex_file


def ibex_parser(output):
    lexer = IbexOutputParser()
    bound = [0.0, 0.0]
    points = None
    cpu_time = 0
    number_of_cells = 0
    infeasible = False
    rel_prec = 0
    abs_prec = 0
    for tok in lexer.tokenize(output):
        if tok.type == "INFEASIBLE_PROBLEM":
            infeasible = True
        if tok.type == "OPTIMIZATION_SUCCESSFUL":
            infeasible = False
        if tok.type == "FBOUND":
            bound = tok.value
        if tok.type == "XBOUND":
            points = tok.value
        if tok.type == "RELATIVE_PRECISION":
            rel_prec = tok.value
        if tok.type == "ABSOLUTE_PRECISION":
            abs_prec = tok.value
        if tok.type == "CPU_TIME":
            cpu_time = tok.value
        if tok.type == "NUMBER_OF_CELLS":
            number_of_cells = tok.value
        # if tok.type == "TIMEOUT_REACHED":
        #     print("Ibex log: Timeout reached")
    if infeasible:
        if bound:
            return bound, None, cpu_time, number_of_cells
    else:
        return bound, points, cpu_time, number_of_cells


def ibex_find_min(ibex_file):
    fp = open('ibex_input.bch', 'w')
    minimum = None
    try:
        fp.write(ibex_file)
        fp.close()
        # Use unreachable precision on purpose to get the most accurate results
        output = subprocess.run(
            f"ibexopt ibex_input.bch --simpl 2 -t{Globals.IBEX_TIMEOUT} --abs-eps-f={Globals.abs_precision_ibex}",
            shell=True, capture_output=True, text=True)
        # print(output.stdout)
        bound, points, cpu_time, number_of_cells = ibex_parser(output.stdout)
        if bound:
            minimum = min(bound)
        # print(bound, points, cpu_time, number_of_cells)
    finally:
        os.remove('ibex_input.bch')
        os.remove('ibex_input.cov')
    return minimum, cpu_time, number_of_cells


def invoke_ibex(symExpr, cond_expr, externConstraints, inputStr):

    # print(symExpr)
    str_expr = re.sub(r'\*\*', "^", str(symExpr))
    str_expr = re.sub(r'Abs', "abs", str_expr)
    str_expr = re.sub(r're\b', "", str_expr)
    str_expr = re.sub(r'im\b', "0.0*", str_expr)
    str_expr = re.sub(r'inf.0', "inf", str_expr)

    try:  # In case if error expression consists of number
        return [float(str_expr), float(str_expr)]
    except ValueError:
        pass

    str_expr = re.sub(r'inf', "1.79769313486e+308", str_expr)  # Ibex doesn't know what inf is. 1.79769313486e+308 is a max number in Ibex

    if Globals.enable_constr:
        if Globals.domain_checks:
            _, denominator_constraints, _, _ = analyze_symbolic_expression(inputStr+str_expr, eps=Globals.domain_eps)
            for d in Globals.domainConds:
                if externConstraints != "":
                    externConstraints += "&" + d
                    # externConstraints += "&<<" + d + ">>"
                else:
                    # externConstraints += "<<" + d + ">>"
                    externConstraints += d
            for d in denominator_constraints:
                if externConstraints != "":
                    # externConstraints += "&<<" + d + ">>"
                    externConstraints += "&" + d
                else:
                    # externConstraints += "<<" + d + ">>"
                    externConstraints += d
                Globals.domainConds.add(d)

        str_constraint = ibex_preprocess_inputs(cond_expr, externConstraints)
    else:
        str_constraint = None

    inputStr = inputStr.replace("=", " in ").replace(";", ";\n")

    cpu_time = 0
    number_of_cells = 0
    if str_constraint:
        # Find maximum
        max_upper = None
        for i in str_constraint:
            ibex_file = ibex_create_input(inputStr, "-(" + str_expr + ")", i[0])
            minimum, cpu_time_, number_of_cells_ = ibex_find_min(ibex_file)
            cpu_time += cpu_time_
            number_of_cells += number_of_cells_
            if minimum:
                if max_upper:
                    if -minimum > max_upper:
                        max_upper = -minimum
                else:
                    max_upper = -minimum

        # Find minimum
        min_lower = None
        for i in str_constraint:
            ibex_file = ibex_create_input(inputStr, str_expr, i[0])
            minimum, cpu_time_, number_of_cells_ = ibex_find_min(ibex_file)
            cpu_time += cpu_time_
            number_of_cells += number_of_cells_
            if minimum:
                if min_lower:
                    if minimum < min_lower:
                        min_lower = minimum
                else:
                    min_lower = minimum
    else:
        # Find maximum
        max_upper = None
        ibex_file = ibex_create_input(inputStr, "-(" + str_expr + ")", str_constraint)
        minimum, cpu_time_, number_of_cells_ = ibex_find_min(ibex_file)

        cpu_time += cpu_time_
        number_of_cells += number_of_cells_
        if minimum:
            max_upper = -minimum

        # Find minimum
        min_lower = None
        ibex_file = ibex_create_input(inputStr, str_expr, str_constraint)
        minimum, cpu_time_, number_of_cells_ = ibex_find_min(ibex_file)

        cpu_time += cpu_time_
        number_of_cells += number_of_cells_
        if minimum:
            min_lower = minimum
    Globals.ibexID += number_of_cells
    return [min_lower if min_lower else 0.0, max_upper if max_upper else 0.0]


if __name__ == "__main__":
    constr = "<<(FR106<=1.0000020389092422e-06)>> " \
             "& " \
             "<<(FR105 + (-0.671558954847019 + 0.25*(0.158580585742728 + U_6_7 + U_7_6 + U_7_8 + U_8_7))**2> 9.999977614771972e-07)>> " \
             "& " \
             "<<(FR82> 1e-06)>> " \
             "& " \
             "(" \
                "<<(FR106<=1.0000020389092422e-06)>> " \
                "|" \
                "<<(FR106> 9.999979610907578e-07)>>" \
             ")" \
             "& " \
             "(" \
                "<<(FR82<=1e-06)>> " \
                "| " \
                "(" \
                     "<<(FR82> 1e-06)>>" \
                     "& " \
                     "(" \
                        "<<(FR106<=1.0000020389092422e-06)>> " \
                        "| " \
                        "<<(FR106> 9.999979610907578e-07)>>" \
                     ")" \
                ")" \
             ")"
    res = preprocess_constraints(constr.replace('\n', ''))
    print(res)


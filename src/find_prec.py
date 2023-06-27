import sys, os

sys.path.append(os.path.join(os.path.join('/home/artemya/RA/FPGuard/' "DenominatorAnalyzer"), "function_transforms"))
sys.path.append(os.path.join(os.path.join('/home/artemya/RA/FPGuard/' "DenominatorAnalyzer"), "rival_python"))
sys.path.append(os.path.join('/home/artemya/RA/FPGuard/' "DenominatorAnalyzer"))

from process_function_ import process_function_
from rival import *

if __name__ == '__main__':
    expr = "x = [-1, 1];sqrt(x+1) + sqrt(x)"
    Expressions, Variables, Consts, DivExpressions = process_function_(expr, precision=1000)
    for exp in Expressions:
        if Expressions[exp].root:
            print("Precision allocation for: " + str(Expressions[exp]))
            p = 1
            for p in range(1, 113):
                higher_precision = Expressions[exp].evaluate(precision=1000)
                lower_precision = Expressions[exp].evaluate(precision=p)
                if ival_cmp(higher_precision, lower_precision, precision=53):
                    print(f"Results will be similar between 1000 precision and {p} precision under 53 bits precision comparison")
                    break
                p+=1

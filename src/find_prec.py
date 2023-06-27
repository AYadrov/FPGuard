import sys, os

sys.path.append(os.path.join(os.path.join('/home/artemya/RA/FPGuard/' "DenominatorAnalyzer"), "function_transforms"))
sys.path.append(os.path.join(os.path.join('/home/artemya/RA/FPGuard/' "DenominatorAnalyzer"), "rival_python"))
sys.path.append(os.path.join('/home/artemya/RA/FPGuard/' "DenominatorAnalyzer"))

from process_function_ import process_function_
from rival import *

if __name__ == '__main__':
    expr = "x = [-1, 1];sqrt(x+1) + sqrt(x)"
    Expressions, Variables, Consts, DivExpressions = process_function_(expr, precision=113)
    for exp in Expressions:
        if Expressions[exp].root:
            print(Expressions[exp].evaluate())
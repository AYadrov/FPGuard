import os
import sys
import numpy as np

try:
    sys.path.append(os.getcwd() + "/rival_python")
    from rival_python.rival import *
except ModuleNotFoundError:
    sys.path.append(os.getcwd() + "/../rival_python")
    from rival_python.rival import *

OP_TO_RIVAL = {
    "-(": ival_neg,
    "dabs": ival_fabs,
    "abs": ival_fabs,
    "pow(": ival_pow,
    "log": ival_log,
    "+": ival_add,
    "-": ival_sub,
    "/": ival_div,
    "*": ival_mul,
    "exp": ival_exp,
    "sqrt": ival_sqrt
}

OP_TO_STR = {
    "-(": "-(",
    "dabs": "abs",
    "abs": "abs",
    "pow(": "**",
    "log": "log",
    "+": "+",
    "-": "-",
    "/": "/",
    "*": "*",
    "exp": "exp",
    "sqrt": "sqrt"
}


class Var:
    def __init__(self, name, range):
        self.name = name
        self.range = range
        self.full_range = range

    def __copy__(self):
        return type(self)(self.name, self.range)

    def evaluate(self, precision=113):
        return ival(bf.Bigfloat(self.range[0], precision), bf.Bigfloat(self.range[1], precision), False, False)

    def getArgs(self):
        return [self.name]

    def search_for_args(self):
        return [self.name]

    def __str__(self):
        return self.name


class Expr:
    def __init__(self, name, operation, left_child=None, right_child=None):
        self.name = name
        self.operation = operation
        self.left_child = left_child
        self.right_child = right_child
        self.root = False

    def evaluate(self, precision=113):
        if self.operation is None:
            return self.left_child.evaluate(precision=precision)
        elif self.right_child is None:
            return OP_TO_RIVAL[self.operation](self.left_child.evaluate(precision=precision))
        else:
            return OP_TO_RIVAL[self.operation](self.left_child.evaluate(precision=precision),
                                               self.right_child.evaluate(precision=precision))

    def getArgs(self):
        return list(np.unique(np.array(self.search_for_args())))

    def getDenominatorArgs(self):
        if self.operation == "/":
            return self.right_child.getArgs()
        else:
            raise TypeError("Expression operator is not division to take denominator!")

    def search_for_args(self):
        left_args = self.left_child.search_for_args()
        if self.right_child is not None:
            right_args = self.right_child.search_for_args()
        else:
            right_args = None

        if right_args is None:
            return left_args
        elif left_args is None:
            return right_args
        else:
            return left_args + right_args

    def __copy__(self):
        return type(self)(self.name, self.operation, self.left_child, self.right_child)

    def __str__(self):
        if self.right_child is None:
            if self.operation is None:
                return self.left_child.__str__()
            else:
                return str(self.operation + "(" + self.left_child.__str__() + ")")
        else:
            return str("(" + self.left_child.__str__() + ")" + OP_TO_STR[self.operation] + "(" + self.right_child.__str__() + ")")

    def strDenominator(self):
        if self.operation == "/":
            return self.right_child.__str__()
        else:
            raise TypeError("Expression operator is not division to take denominator!")


class Const:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def evaluate(self, precision=113):
        if bf.is_inf(self.value):
            return ival(float('inf'), float('inf'), True, True)
        else:
            return ival(bf.Bigfloat(self.value, precision), bf.Bigfloat(self.value, precision), False, False)

    def getArgs(self):
        return None

    def search_for_args(self):
        return None

    def __str__(self):
        return str(self.value)

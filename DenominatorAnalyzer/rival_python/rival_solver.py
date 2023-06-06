import sys
from collections import OrderedDict

from copy import copy


from interval import interval

sys.path.append("//function_transforms")
sys.path.append("//rival_python")

from rival import *
from process_function_ import process_function_

DEPTH = 3


class ValidIntervals(OrderedDict):
    def __init__(self, Variables):
        """
        Initialization and copying variables from Variables to self
        """
        super().__init__()
        for var in Variables:
            self.__setitem__(var, [Variables[var].full_range])

    def getLength(self):
        """
        Method returns length of the intervals for variables
        """
        for k in self:
            return len(self[k])


def ival_unite(int1, int2):
    out = interval(int1) | interval(int2)
    return list(out[0])


def concatenate_intervals(int1, int2):
    if int1 is None:
        return int2
    elif int2 is None:
        return int1
    else:
        out = []
        for val1, val2 in zip(int1, int2):
            out.append(val1 + val2)
        return out


def enumerate_intervals(Variables):
    out = []
    for var in Variables:
        out.append([Variables[var].range])
    return out


def get_invalid_interval(args, exp, Variables, turn, depth):
    result = exp.evaluate()
    if result.err_exact:
        return enumerate_intervals(Variables)
    if result.err_possible:
        return binary_search_(args, exp, Variables, turn + 1, depth)
    else:
        return None


def split_ival(x, val=None):
    first = [x[0], val]
    second = [val, x[1]]
    return first, second


def adjacent(int1, int2, len_of_intervals):
    if len_of_intervals == 0:
        return len(interval(int1) | interval(int2)) == 1
    for i in range(len_of_intervals - 1, 0, -1):
        if int1[i] != int2[i]:
            return False
    return len(interval(int1[0]) | interval(int2[0])) == 1


def exclude_interval(int1, int2):
    if isinstance(int1[0], list):
        out = []
        for i in int1:
            res = exclude_interval(i, int2)
            if res!=None:
                out += res
        return out
    elif int1[0] == int2[0]:
        if int2[1] < int1[1]:
            return [[int2[1], int1[1]]]
        else:
            return None
    elif int1[1] == int2[1]:
        if int1[0] < int2[0]:
            return [[int1[0], int2[0]]]
        else:
            return None
    else:
        if int1[0] < int2[0]:
            if int1[1] > int2[0]:
                if int1[1] > int2[1]:
                    return [[int1[0], int2[0]], [int2[1], int1[1]]]
                else:
                    return [int1[0], int2[0]]
            else:
                return None
        elif int2[1] < int1[1]:
            if int1[0] < int2[1]:
                return [int2[1], int1[1]]
            else:
                return None


def check_intervals(Variables, expression, valid_intervals, args):
    for i in range(len(valid_intervals[args[0]])):
        for var in Variables:
            Variables[var].range = valid_intervals[var][i]
        result = expression.evaluate()
        if result.err_possible or result.err_exact:
            print(result, expression.name)


def binary_search_(args, exp, Variables, turn=0, depth=DEPTH):
    if turn >= len(args) and depth != 0:  # New cycle of dividing
        turn = 0
        depth = depth - 1
    if depth == 0:
        return enumerate_intervals(Variables)

    midpoint = (Variables[args[turn]].range[0] + Variables[args[turn]].range[1]) / 2
    first, second = split_ival(Variables[args[turn]].range, midpoint)

    ranges = []
    for arg in args:
        ranges.append(copy(Variables[arg].range))

    Variables[args[turn]].range = first
    box_1 = get_invalid_interval(args, exp, Variables, turn, depth)

    for i, arg in enumerate(args):
        Variables[arg].range = ranges[i]

    Variables[args[turn]].range = second
    box_2 = get_invalid_interval(args, exp, Variables, turn, depth)

    return concatenate_intervals(box_1, box_2)


def binary_search(args, exp, Variables, denominator_arguments, valid_intervals):
    result = None

    for i in range(len(valid_intervals[args[0]])):
        for var in Variables:
            Variables[var].range = valid_intervals[var][i]
        result = concatenate_intervals(result, binary_search_(denominator_arguments, exp, Variables))
    for var in Variables:
        Variables[var].range = Variables[var].full_range

    if result == None:
        result = []
        for var in valid_intervals:
            result.append(valid_intervals[var])
        return result
    # Sorting intervals in zip, with the following order (like SQL style): len-1, len-2, ..., 0
    result = [list(t) for t in zip(*sorted(zip(*result),
                                           key=lambda x: (
                                               [x[i][0] for i in range(len(result) - 1, -1, -1)])))]

    # Unite intervals if they are adjacent
    for i in range(len(result[0]) - 1):
        first_list = [item[i] for item in result[0:(len(result) - 1)]]
        second_list = [item[i + 1] for item in result[0:(len(result) - 1)]]

        if first_list and second_list:
            if result[len(result) - 1][i] == result[len(result) - 1][i + 1] and \
                    adjacent(first_list, second_list, len(result) - 1):
                united_interval = ival_unite(result[0][i], result[0][i + 1])
                result[0][i + 1] = united_interval
                for j in range(len(result)):
                    result[j][i] = False
        else:
            if adjacent(result[0][i], result[0][i + 1], len(result) - 1):
                united_interval = ival_unite(result[0][i], result[0][i + 1])
                result[0][i + 1] = united_interval
                result[0][i] = False

    for i in range(len(result)):
        result[i][:] = (x for x in result[i] if x is not False)

    for i in range(len(result[0])):
        length = 0
        for j, (arg, res) in enumerate(zip(valid_intervals, [item[i] for item in result])):
            if j == 0:
                out = exclude_interval(valid_intervals[arg], res)
                if res == None:
                    out = []
                length = len(out)
                result[j][i] = out
            else:
                result[j][i] = [res] * length

    for i in range(len(result)):
        temp = []
        for x in result[i]:
            if isinstance(x[0], list):
                for j in x:
                    temp.append(j)
            else:
                temp.append(x)
        result[i] = temp

    return result


def check_for_error(args, exp, Variables, valid_intervals):
    result = None
    for i in range(len(valid_intervals[args[0]])):
        for var in Variables:
            Variables[var].range = valid_intervals[var][i]
        result = exp.evaluate()
        if result.err_possible or result.err_exact:
            for v in Variables:
                Variables[v].range = Variables[v].full_range
            return result
    return result


def rival_solver(arguments, Expressions, Variables, valid_intervals, denominator_arguments, exp):
    # Search for errors in the expression
    result = check_for_error(arguments, Expressions[exp], Variables, valid_intervals)

    if result.err_exact:  # Exact error can not be handled...
        print("Exact error in {}, arguments=".format(exp))

    if result.err_possible:  # If error is possible
        # Apply binary search
        true_intervals = None
        other_variables = [var for var in Variables if var not in denominator_arguments]
        start_of_interval = 0
        for index in range(1, valid_intervals.getLength()):
            for o_var in other_variables:
                if valid_intervals[o_var][index - 1] != valid_intervals[o_var][index]:
                    end_of_interval = index
                    true_intervals = concatenate_intervals(true_intervals,
                                                           binary_search(arguments, Expressions[exp], Variables,
                                                                         denominator_arguments,
                                                                         OrderedDict([(x, valid_intervals[x][
                                                                                          start_of_interval:end_of_interval])
                                                                                      for x in
                                                                                      valid_intervals])))

                    start_of_interval = index
                    break
        end_of_interval = valid_intervals.getLength()

        true_intervals = concatenate_intervals(true_intervals, binary_search(arguments, Expressions[exp], Variables,
                                                                             denominator_arguments,
                                                                             OrderedDict([(x, valid_intervals[x][
                                                                                              start_of_interval:end_of_interval])
                                                                                          for x in
                                                                                          valid_intervals])))

        for i, var in enumerate(Variables):
            valid_intervals[var] = true_intervals[i]

        result = check_for_error(arguments, Expressions[exp], Variables, valid_intervals)
        print("After analysis, the result=" + str(result))
        return valid_intervals


def analyze_symbolic_expression(symb_expr):
    Expressions, Variables, Consts, DivExpressions = process_function_(symb_expr)

    valid_intervals = ValidIntervals(Variables)

    restriction = OrderedDict()
    for var in Variables:
        restriction[var] = []

    for exp in DivExpressions:

        arguments = Expressions[exp].getArgs()
        denominator_arguments = Expressions[exp].getDenominatorArgs()
        valid_intervals = rival_solver(arguments, Expressions, Variables, valid_intervals, denominator_arguments, exp)


    # Print rival boxes
    import pandas as pd
    df = pd.DataFrame(columns=[x for x in Variables])

    for i in range(valid_intervals.getLength()):
        new_row = {}
        for var in Variables:
            new_row[var] = str(valid_intervals[var][i])
        new_row = pd.DataFrame(new_row, index=[0])
        df = pd.concat([df, new_row])
    df.reset_index(inplace=True, drop=True)
    print(df)


if __name__ == '__main__':
    symb_expr = """
    x = [-1.0, 1.0];
    y = [-1.0, 1.0];
    1/(x-y)
    """

    analyze_symbolic_expression(symb_expr)
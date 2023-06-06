import doctest
from rival import *


def tests():
    """
    >>> a = ival(2, 3, False, False)
    >>> b = ival(-1, 0, False, False)
    >>> c = ival(float("-inf"), float("inf"), False, False)
    >>> d = ival(-5, 5, False, False)
    >>> e = ival(156, 1000, False, False)
    >>> f = ival(-1, 0, True, False)
    >>> g = ival(-5, 20, True, True)
    >>> i = 5
    >>> j = -1
    >>> k = float("inf")

    Add function
    >>> ival_add(a, b) == ival(lo=1, hi=3, err_possible=False, err_exact=False)
    True
    >>> ival_add(a, g) == ival(lo=-3, hi=23, err_possible=True, err_exact=True)
    True
    >>> ival_add(f, a) == ival(lo=1, hi=3, err_possible=True, err_exact=False)
    True
    >>> ival_add(a, c) == ival(lo=float('-inf'), hi=float('inf'), err_possible=False, err_exact=False)
    True
    >>> ival_add(e, c) == ival(lo=float('-inf'), hi=float('inf'), err_possible=False, err_exact=False)
    True
    >>> ival_add(d, i) == ival(lo=0, hi=10, err_possible=False, err_exact=False)
    True
    >>> ival_add(j, d) == ival(lo=-6, hi=4, err_possible=False, err_exact=False)
    True
    >>> ival_add(d, k) == ival(lo=float('inf'), hi=float('inf'), err_possible=False, err_exact=False)
    True

    Sub function
    >>> ival_sub(a, b) == ival(lo=2, hi=4, err_possible=False, err_exact=False)
    True
    >>> ival_sub(a, g) == ival(lo=-18, hi=8, err_possible=True, err_exact=True)
    True
    >>> ival_sub(f, a) == ival(lo=-4, hi=-2, err_possible=True, err_exact=False)
    True
    >>> ival_sub(a, c) == ival(lo=float('-inf'), hi=float('inf'), err_possible=False, err_exact=False)
    True
    >>> ival_sub(e, c) == ival(lo=float('-inf'), hi=float('inf'), err_possible=False, err_exact=False)
    True
    >>> ival_sub(d, i) == ival(lo=-10, hi=0, err_possible=False, err_exact=False)
    True
    >>> ival_sub(j, d) == ival(lo=-6, hi=4, err_possible=False, err_exact=False)
    True
    >>> ival_sub(d, k) == ival(lo=float('-inf'), hi=float('-inf'), err_possible=False, err_exact=False)
    True

    Mul function
    >>> ival_mul(a, b) == ival(lo=-3, hi=0, err_possible=False, err_exact=False)
    True
    >>> ival_mul(a, g) == ival(lo=-15, hi=60, err_possible=True, err_exact=True)
    True
    >>> ival_mul(f, a) == ival(lo=-3, hi=-0, err_possible=True, err_exact=False)
    True
    >>> ival_mul(a, c) == ival(lo=float('-inf'), hi=float('inf'), err_possible=False, err_exact=False)
    True
    >>> ival_mul(e, c) == ival(lo=float('-inf'), hi=float('inf'), err_possible=False, err_exact=False)
    True
    >>> ival_mul(d, i) == ival(lo=-25, hi=25, err_possible=False, err_exact=False)
    True
    >>> ival_mul(j, d) == ival(lo=-5, hi=5, err_possible=False, err_exact=False)
    True
    >>> ival_mul(d, k) == ival(lo=float('-inf'), hi=float('inf'), err_possible=False, err_exact=False)
    True

    Div function
    >>> ival_div(a, b) == ival(lo=float("-inf"), hi=float("inf"), err_possible=True, err_exact=False)
    True
    >>> ival_div(a, g) == ival(lo=float("-inf"), hi=float("inf"), err_possible=True, err_exact=True)
    True
    >>> ival_div(f, a) == ival(lo=-0.5, hi=-0, err_possible=True, err_exact=False)
    True
    >>> ival_div(a, c) == ival(lo=float('-inf'), hi=float('inf'), err_possible=True, err_exact=False)
    True
    >>> ival_div(e, c) == ival(lo=float('-inf'), hi=float('inf'), err_possible=True, err_exact=False)
    True
    >>> ival_div(d, i) == ival(lo=-1, hi=1, err_possible=False, err_exact=False)
    True
    >>> ival_div(j, d) == ival(lo=float("-inf"), hi=float("inf"), err_possible=True, err_exact=False)
    True
    >>> ival_div(d, k) == ival(lo=0, hi=0, err_possible=False, err_exact=False)
    True

    Pow function
    >>> ival_pow(ival(-1, 1, False, False), ival(-1, 1, False, False)) == \
        ival(lo=float("-inf"), hi=float("inf"), err_possible=True, err_exact=False)
    True
    >>> ival_pow(ival(-2, 2, False, False), ival(0, 1, False, False)) == \
        ival(lo=float("-2"), hi=float("2"), err_possible=True, err_exact=False)
    True
    >>> ival_pow(ival(-2, 2, False, False), ival(1, 2, False, False)) == \
        ival(lo=-2, hi=4, err_possible=True, err_exact=False)
    True
    >>> ival_pow(ival(-2, 0, False, False), ival(-2, 2, False, False)) == \
        ival(lo=float("-inf"), hi=float("inf"), err_possible=True, err_exact=False)
    True
    >>> ival_pow(ival(0, 2, False, False), ival(-2, 2, False, False)) == \
        ival(lo=0, hi=float("inf"), err_possible=True, err_exact=False)
    True
    >>> ival_pow(ival(0, 2, False, False), ival(0, 2, False, False)) == \
        ival(lo=0, hi=4, err_possible=False, err_exact=False)
    True
    >>> ival_pow(a, k) == ival(lo=float("inf"), hi=float("inf"), err_possible=False, err_exact=False)
    True
    >>> ival_pow(k, a) == ival(lo=float("inf"), hi=float("inf"), err_possible=False, err_exact=False)
    True
    """

if __name__ == '__main__':
    doctest.testmod()
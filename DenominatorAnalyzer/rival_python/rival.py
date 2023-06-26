import bigfloat
import bigfloat as bf
from enum import Enum


class op(Enum):
    add = 1
    sub = 2
    div = 3
    mul = 4
    pow = 5
    and_ = 6
    or_ = 7
    neg = 8
    log = 9
    exp = 10
    sqrt = 11


class ival():

    def __init__(self, lo, hi, err_possible, err_exact):
        self.lo = lo
        self.hi = hi
        self.err_possible = err_possible
        self.err_exact = err_exact

    def __str__(self) -> str:
        str = "ival(lo={}, hi={}, err_possible={}, err_exact={})" \
            .format(self.lo, self.hi, self.err_possible, self.err_exact)
        return str

    def __eq__(self, o: object) -> bool:
        return isinstance(o, ival) and o.lo == self.lo and o.hi == self.hi and o.err_possible == self.err_possible \
               and o.err_exact == self.err_exact


def list2interval(list_):
    return ival(list_[0], list_[1], False, False)


def ival_add(x: ival or float or int,
             y: ival or float or int,
             precision: int = 113) -> ival:
    if isinstance(x, ival) and isinstance(y, ival):
        return ival(
            bf_return_exact(op.add, x.lo, y.lo, bf.RoundTowardNegative, precision=precision),
            bf_return_exact(op.add, x.hi, y.hi, bf.RoundTowardPositive, precision=precision),
            x.err_possible or y.err_possible,
            x.err_exact or y.err_exact
        )
    elif isinstance(x, list):
        return ival_add(list2interval(x), y, precision=precision)

    elif isinstance(y, list):
        return ival_add(x, list2interval(y), precision=precision)

    elif (isinstance(x, float) or isinstance(x, int)) and isinstance(y, ival):
        return ival_add(ival(x, x, False, False), y, precision=precision)

    elif isinstance(x, ival) and (isinstance(y, float) or isinstance(y, int)):
        return ival_add(x, ival(y, y, False, False), precision=precision)
    else:
        raise TypeError


def bf_return_exact(op: op, a, b=None, rnd_mode=None, precision=113):
    bigfloat.clear_flag(bigfloat.Inexact)
    if op == op.add:
        with bf.precision(precision):
            with rnd_mode:
                return bf.add(a, b)
    if op == op.sub:
        with bf.precision(precision):
            with rnd_mode:
                return bf.sub(a, b)
    if op == op.mul:
        with bf.precision(precision):
            with rnd_mode:
                return bf.mul(a, b)
    if op == op.div:
        with bf.precision(precision):
            with rnd_mode:
                return bf.div(a, b)
    if op == op.pow:
        with bf.precision(precision):
            with rnd_mode:
                return bf.pow(a, b)
    if op == op.log:
        with bf.precision(precision):
            with rnd_mode:
                return bf.log(a)
    if op == op.exp:
        with bf.precision(precision):
            with rnd_mode:
                return bf.exp(a)
    if op == op.sqrt:
        with bf.precision(precision):
            with rnd_mode:
                return bf.sqrt(a)
    if op == op.and_:
        return b
    if op == op.or_:
        return a

    raise ValueError


def ival_fabs(x: ival) -> ival:
    if bf.greater(x.lo, 0.0):
        return x
    elif bf.less(x.hi, 0.0):
        return ival(bf.neg(x.hi), bf.neg(x.lo), x.err_possible, x.err_exact)
    else:
        return ival(0, bf.max(bf.neg(x.lo), x.hi), x.err_possible, x.err_exact)


def ival_sub(x: ival or float or int,
             y: ival or float or int,
             precision: int = 113) -> ival:
    if isinstance(x, ival) and isinstance(y, ival):
        return ival(
            bf_return_exact(op.sub, x.lo, y.hi, bf.RoundTowardNegative, precision=precision),
            bf_return_exact(op.sub, x.hi, y.lo, bf.RoundTowardPositive, precision=precision),
            x.err_possible or y.err_possible,
            x.err_exact or y.err_exact
        )
    elif (isinstance(x, float) or isinstance(x, int)) and isinstance(y, ival):
        return ival_sub(ival(x, x, False, False), y, precision=precision)
    elif isinstance(x, ival) and (isinstance(y, float) or isinstance(y, int)):
        return ival_sub(x, ival(y, y, False, False), precision=precision)
    else:
        raise TypeError


def classify_ival(x: ival, val: int = 0.0) -> int:
    if bf.greaterequal(x.lo, val):
        return 1
    if bf.lessequal(x.hi, val):
        return -1
    return 0


def classify_ival_strict(x: ival, val: int = 0.0) -> int:
    if bf.greater(x.lo, val):
        return 1
    if bf.less(x.hi, val):
        return -1
    return 0


def endpoint_min2(e1, e2):
    if bf.less(e1, e2):
        return e1
    if bf.less(e2, e1):
        return e2

    return bf.min(e1, e2)


def endpoint_max2(e1, e2):
    if bf.greater(e1, e2):
        return e1
    if bf.greater(e2, e1):
        return e2

    return bf.max(e1, e2)


def ival_union(x: ival, y: ival) -> ival:
    if x.err_exact:
        y.error_possible = True
        return y
    if y.err_exact:
        x.error_possible = True
        return x
    if bf.is_finite(x.lo) or bf.is_inf(x.lo) or bf.is_nan(x.lo):
        return ival(
            endpoint_min2(x.lo, y.lo),
            endpoint_max2(x.hi, y.hi),
            x.err_possible or y.err_possible,
            x.err_exact and y.err_exact
        )
    if isinstance(x.lo, bool):
        return ival(
            bf_return_exact(op.and_, x.lo, y.lo),
            bf_return_exact(op.or_, x.hi, y.hi),
            x.err_possible or y.err_possible,
            x.err_exact and y.err_exact
        )


def ival_mul(x: ival or float or int,
             y: ival or float or int,
             precision: int = 113) -> ival:
    if isinstance(x, ival) and isinstance(y, ival):
        def mkmult(a, b, c, d, p):
            return ival(
                epmul(a, b, bf.RoundTowardNegative, precision=p),
                epmul(c, d, bf.RoundTowardPositive, precision=p),
                x.err_possible or y.err_possible,
                x.err_exact or y.err_exact
            )

        x_sign = classify_ival(x)
        y_sign = classify_ival(y)

        if x_sign == 1 and y_sign == 1:
            return mkmult(x.lo, y.lo, x.hi, y.hi, precision)
        if x_sign == 1 and y_sign == -1:
            return mkmult(x.hi, y.lo, x.lo, y.hi, precision)
        if x_sign == 1 and y_sign == 0:
            return mkmult(x.hi, y.lo, x.hi, y.hi, precision)
        if x_sign == -1 and y_sign == 0:
            return mkmult(x.lo, y.hi, x.lo, y.lo, precision)
        if x_sign == -1 and y_sign == 1:
            return mkmult(x.lo, y.hi, x.hi, y.lo, precision)
        if x_sign == -1 and y_sign == -1:
            return mkmult(x.hi, y.hi, x.lo, y.lo, precision)
        if x_sign == 0 and y_sign == 0:
            return ival_union(mkmult(x.hi, y.lo, x.lo, y.lo, precision), mkmult(x.lo, y.hi, x.hi, y.hi, precision))
        if x_sign == 0 and y_sign == 1:
            return mkmult(x.lo, y.hi, x.hi, y.hi, precision)
        if x_sign == 0 and y_sign == -1:
            return mkmult(x.hi, y.lo, x.lo, y.lo, precision)

    elif isinstance(x, ival) and (isinstance(y, float) or isinstance(y, int)):
        return ival_mul(x, ival(y, y, False, False), precision=precision)
    elif isinstance(y, ival) and (isinstance(x, float) or isinstance(x, int)):
        return ival_mul(ival(x, x, False, False), y, precision=precision)
    else:
        raise TypeError


def ival_div(x: ival or float or int,
             y: ival or float or int,
             precision: int = 113) -> ival:
    if isinstance(x, ival) and isinstance(y, ival):
        err_possible = x.err_possible or y.err_possible or (bf.lessequal(y.lo, 0) and bf.greaterequal(y.hi, 0))
        err_exact = x.err_exact or y.err_exact or (bf.is_zero(y.lo) and bf.is_zero(y.hi))

        def mkdiv(a, b, c, d, p):
            return ival(
                bf_return_exact(op.div, a, b, bf.RoundTowardNegative, precision=p),
                bf_return_exact(op.div, c, d, bf.RoundTowardPositive, precision=p),
                err_possible,
                err_exact
            )

        x_class = classify_ival_strict(x)
        y_class = classify_ival_strict(y)

        if y_class == 0:
            return ival(float("-inf"), float("inf"), err_possible, err_exact)
        if x_class == 1 and y_class == 1:
            return mkdiv(x.lo, y.hi, x.hi, y.lo, precision)
        if x_class == 1 and y_class == -1:
            return mkdiv(x.hi, y.hi, x.lo, y.lo, precision)
        if x_class == -1 and y_class == 1:
            return mkdiv(x.lo, y.lo, x.hi, y.hi, precision)
        if x_class == -1 and y_class == -1:
            return mkdiv(x.hi, y.lo, x.lo, y.hi, precision)
        if x_class == 0 and y_class == 1:
            return mkdiv(x.lo, y.lo, x.hi, y.lo, precision)
        if x_class == 0 and y_class == -1:
            return mkdiv(x.hi, y.hi, x.lo, y.hi, precision)

    elif isinstance(x, ival) and (isinstance(y, float) or isinstance(y, int)):
        return ival_div(x, ival(y, y, False, False), precision=precision)

    elif (isinstance(x, float) or isinstance(x, int)) and isinstance(y, ival):
        return ival_div(ival(x, x, False, False), y, precision=precision)
    else:
        raise TypeError


def ival_neg(x):
    return ival(
        bf.neg(x.hi),
        bf.neg(x.lo),
        x.err_possible,
        x.err_exact
    )


def epmul(a, b, rnd_mode, precision=113):
    if bf.is_zero(a) or bf.is_zero(b):
        return 0.0
    else:
        return bf_return_exact(op.mul, a, b, rnd_mode, precision=precision)


def clamp_strict(lo, hi, x):
    return ival(
        bf.min(bf.max(x.lo, lo), hi),
        bf.max(bf.min(x.hi, hi), lo),
        x.err_possible or bf.lessequal(x.lo, lo) or bf.greaterequal(x.hi, hi),
        x.err_exact or bf.lessequal(x.hi, lo) or bf.greaterequal(x.lo, hi)
    )


def clamp(lo, hi, x):
    return ival(
        bf.min(bf.max(x.lo, lo), hi),
        bf.max(bf.min(x.hi, hi), lo),
        x.err_possible or bf.less(x.lo, lo) or bf.greater(x.hi, hi),
        x.err_exact or bf.less(x.hi, lo) or bf.greater(x.lo, hi)
    )


def monotonic(op: op,
              x: ival,
              precision: int=113) -> ival:
    return ival(
        bf_return_exact(op, x.lo, rnd_mode=bf.RoundTowardNegative, precision=precision),
        bf_return_exact(op, x.hi, rnd_mode=bf.RoundTowardPositive, precision=precision),
        x.err_possible,
        x.err_exact
    )


def ival_log(x, precision=113):
    return monotonic(op.log, clamp_strict(0, float('inf'), x), precision=precision)


def exp_overflow_threshold():
    with bf.precision(113):
        out = bf.add(bf.log(bf.next_down(float("inf"))), 1)
    return out


def ival_exp(x, precision=113):
    return monotonic(op.exp, x, precision=precision)


def ival_pow_pos(x, y, precision=113):
    x_class = classify_ival(x, 1)
    y_class = classify_ival(y)

    def mk_pow(a, b, c, d, p):
        out = ival(
            bf_return_exact(op.pow, a, b, bf.RoundTowardNegative, precision=p),
            bf_return_exact(op.pow, c, d, bf.RoundTowardPositive, precision=p),
            x.err_possible or y.err_possible or (bf.is_zero(x.lo) and y_class != 1),
            x.err_exact or y.err_exact or (bf.is_zero(x.hi) and y_class == -1)
        )
        return out

    if x_class == 1 and y_class == 1:
        return mk_pow(x.lo, y.lo, x.hi, y.hi, precision)
    if x_class == 1 and y_class == 0:
        return mk_pow(x.hi, y.lo, x.hi, y.hi, precision)
    if x_class == 1 and y_class == -1:
        return mk_pow(x.hi, y.lo, x.lo, y.hi, precision)
    if x_class == 0 and y_class == 1:
        return mk_pow(x.lo, y.hi, x.hi, y.hi, precision)
    if x_class == 0 and y_class == -1:
        return mk_pow(x.hi, y.lo, x.lo, y.lo, precision)
    if x_class == -1 and y_class == 1:
        return mk_pow(x.lo, y.hi, x.hi, y.lo, precision)
    if x_class == -1 and y_class == 0:
        return mk_pow(x.lo, y.hi, x.lo, y.lo, precision)
    if x_class == -1 and y_class == -1:
        return mk_pow(x.hi, y.hi, x.lo, y.lo, precision)
    if x_class == 0 and y_class == 0:
        return ival_union(mk_pow(x.lo, y.hi, x.hi, y.hi, precision), mk_pow(x.hi, y.lo, x.lo, y.lo, precision))


def ival_pow_neg(x, y, precision=113):
    err_possible = x.err_possible or y.err_possible or bf.less(y.lo, y.hi)
    err_exact = x.err_exact or y.err_exact
    xpos = ival_fabs(x)
    a = bf.ceil(y.lo)
    b = bf.floor(y.hi)
    if bf.less(b, a):
        if bf.is_zero(x.hi):
            return ival(0, 0, True, False)
        else:
            return ival(float('nan'), float('nan'), True, True)
    elif bf.equal(a, b):
        if bf.mod(a, 2) == 1:  # if a is odd
            return ival_neg(
                ival_pow_pos(
                    xpos,
                    ival(a, a, err_possible, err_exact),
                    precision=precision
                )
            )
        else:
            return ival_pow_pos(xpos, ival(a, a, err_possible, err_exact), precision=precision)
    else:
        odds = ival(
            a if bf.mod(a, 2) == 1 else bf.add(a, 1),
            b if bf.mod(b, 2) == 1 else bf.sub(b, 1),
            err_possible,
            err_exact
        )
        evens = ival(
            bf.add(a, 1) if bf.mod(a, 2) == 1 else a,
            bf.sub(b, 1) if bf.mod(b, 2) == 1 else b,
            err_possible,
            err_exact
        )
        return ival_union(ival_pow_pos(xpos, evens, precision=precision),
                          ival_neg(
                              ival_pow_pos(xpos, odds, precision=precision)
                            )
                          )


def split_ival(x, val=None):
    first = ival(x.lo, val, x.err_possible, x.err_exact)
    second = ival(val, x.hi, x.err_possible, x.err_exact)
    return first, second


def ival_pow(x, y, precision=113):
    if isinstance(x, ival) and isinstance(y, ival):
        if bf.less(x.hi, 0):
            return ival_pow_neg(x, y, precision=precision)
        elif bf.greaterequal(x.lo, 0):
            return ival_pow_pos(x, y, precision=precision)
        else:
            neg, pos = split_ival(x, 0)
            out = ival_union(ival_pow_neg(neg, y, precision=precision), ival_pow_pos(pos, y, precision=precision))
            return out

    elif (isinstance(x, float) or isinstance(x, int)) and isinstance(y, ival):
        return ival_pow(ival(x, x, False, False), y, precision=precision)
    elif isinstance(x, ival) and (isinstance(y, float) or isinstance(y, int)):
        return ival_pow(x, ival(y, y, False, False), precision=precision)
    else:
        raise TypeError


def ival_sqrt(x, precision=113):
    return monotonic(op.sqrt, clamp(0, float('inf'), x), precision=precision)


def ival_cmp(x: ival,
             y: ival,
             precision=53) -> bool:

    with bf.precision(precision):
        x.lo = bf.BigFloat(x.lo)
        x.hi = bf.BigFloat(x.hi)

        y.lo = bf.BigFloat(y.lo)
        y.hi = bf.BigFloat(y.hi)

        return bigfloat.cmp(y.lo, x.lo) == 0 and bigfloat.cmp(y.hi, x.hi) == 0


if __name__ == "__main__":
    x = ival(2, 2, False, False)

    precision = 1
    while not ival_cmp(ival_exp(x, precision=1000), ival_exp(x, precision=precision)):
        precision+=1
    print(precision)

    precision = 1
    while not ival_cmp(ival_sqrt(x, precision=1000), ival_sqrt(x, precision=precision)):
        precision += 1
    print(precision)
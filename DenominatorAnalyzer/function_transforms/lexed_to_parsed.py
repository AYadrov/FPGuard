import sys


try:
    from sly import Parser
except ModuleNotFoundError:
    sys.exit(-1)

from function_to_lexed import GelpiaLexer


class GelpiaParser(Parser):
    tokens = GelpiaLexer.tokens

    precedence = (("left", "PLUS", "MINUS"),
                  ("left", "TIMES", "DIVIDE"),
                  ("right", "UMINUS"),
                  ("right", "INFIX_POW"),)

    # function
    @_("variable EQUALS expression SEMICOLON function")
    def function(self, p):
        return (("Assign", p.variable, p.expression), p.function)

    @_("symbolic_const EQUALS expression SEMICOLON function")
    def function(self, p):
        return p.function

    @_("interval variable SEMICOLON function")
    def function(self, p):
        return (("Assign", p.variable, p.interval), p.function)

    @_("interval symbolic_const SEMICOLON function")
    def function(self, p):
        return p.function

    @_("expression_star")
    def function(self, p):
        return ("Return", p.expression_star)

    # expression_star
    @_("expression SEMICOLON expression_star")
    def expression_star(self, p):
        return ("+", p.expression, p.expression_star)

    @_("expression SEMICOLON")
    def expression_star(self, p):
        return p.expression

    @_("expression")
    def expression_star(self, p):
        return p.expression

    # expression
    @_("expression PLUS expression",
       "expression MINUS expression",
       "expression TIMES expression",
       "expression DIVIDE expression")
    def expression(self, p):
        return (p[1], p.expression0, p.expression1)

    @_("expression INFIX_POW expression")
    def expression(self, p):
        return ("pow", p.expression0, p.expression1)

    @_("MINUS expression %prec UMINUS")
    def expression(self, p):
        return ("neg", p.expression)

    @_("base")
    def expression(self, p):
        return p.base

    # base
    @_("symbolic_const",
       "variable",
       "interval",
       "const",
       "group",
       "func")
    def base(self, p):
        return p[0]

    # variable
    @_("NAME")
    def variable(self, p):
        return ("Name", p[0])

    # interval
    @_("LBRACE negconst COMMA negconst RBRACE")
    def interval(self, p):
        left = p.negconst0
        right = p.negconst1
        low = float(left[1])
        high = float(right[1])

        if low > high:
            sys.exit(-1)

        if low == high:
            return ("Float", left[1])
        else:
            return ("InputInterval", ("Float", left[1]), ("Float", right[1]))

    @_("LBRACE negconst RBRACE")
    def interval(self, p):
        return ("Float", p.negconst[1])

    # negconst
    @_("MINUS negconst")
    def negconst(self, p):
        typ, val = p.negconst[0:2]
        if val[0] == "-":
            return (typ, val[1:])
        else:
            return (typ, "-" + val)

    # const
    @_("const")
    def negconst(self, p):
        return p.const

    @_("integer",
       "float")
    def const(self, p):
        return p[0]

    # integer
    @_("INTEGER")
    def integer(self, p):
        return ("Integer", p[0])

    # float
    @_("FLOAT")
    def float(self, p):
        return ("Float", p[0])

    # group
    @_("LPAREN expression RPAREN")
    def group(self, p):
        return p.expression

    # func
    @_("BINOP LPAREN expression COMMA expression RPAREN")
    def func(self, p):
        return (p[0], p.expression0, p.expression1)

    @_("UNOP LPAREN expression RPAREN")
    def func(self, p):
        return (p[0], p.expression)

    # symbolic_const
    @_("SYMBOLIC_CONST")
    def symbolic_const(self, p):
        return ("SymbolicConst", p[0])

    # errors
    def error(self, p):
        sys.exit(-1)


def lexed_to_parsed(tokens):
    parser = GelpiaParser()
    return parser.parse(tokens)


def main(argv):
    try:
        from pass_utils import get_runmain_input
        from function_to_lexed import function_to_lexed

        data = get_runmain_input(argv)

        tokens = function_to_lexed(data)
        tree = lexed_to_parsed(tokens)


        return 0

    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

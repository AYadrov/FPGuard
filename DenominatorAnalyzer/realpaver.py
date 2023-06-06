from collections import OrderedDict

from sly import Lexer
import subprocess

from analyzer import rival_check

RBRACKET = "RBRACKET"
LBRACKET = "LBRACKET"
COMMA = "COMMA"
IN = "IN"
COMMENT = "COMMENT"
INITIAL_BOX = "INITIAL_BOX"
OUTER_BOX = "OUTER_BOX "
INNER_BOX = "INNER_BOX"
PRECISION = "PRECISION"


class Slex(Lexer):
    tokens = {COMMENT, RBRACKET, LBRACKET, COMMA, IN, INITIAL_BOX, OUTER_BOX, INNER_BOX, PRECISION}

    ignore = " "

    RBRACKET = r"\["
    LBRACKET = r"\]"
    COMMA = r"\,"
    IN = "in"
    COMMENT = r'RealPaver v. 0.4 \(c\) LINA 2004'
    INITIAL_BOX = "INITIAL BOX"
    OUTER_BOX = "OUTER BOX ([0-9]*)"
    INNER_BOX = r"INNER BOX ([0-9]*)"
    PRECISION = "precision: ([0-9]*[.])?[0-9]+(e-[0-9]*)?, elapsed time: ([0-9]*[,])?[0-9]+ ms"

    current_token = None
    tok = None

    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += len(t.value)

    @_("END OF SOLVING")
    def END(self, t):
        return t

    @_(r'[a-zA-Z_][a-zA-Z0-9_]*')
    def VARIABLE(self, t):
        return t

    @_(r'[+-]?([0-9]*[.])?[0-9]+(e-[0-9]*)?')
    def NUMBER(self, t):
        return t


def parse_boxes(paver_output):
    lexer = Slex()

    boxes = OrderedDict()

    variable = None
    initial_box = False
    inner = False
    inner_boxes = OrderedDict()

    for tok in lexer.tokenize(paver_output):
        if tok.type == "INNER_BOX":
            inner = True
            initial_box = False
        elif tok.type == "OUTER_BOX":
            inner = False
            initial_box = False
        elif tok.type == "INITIAL_BOX":
            initial_box = True
        if tok.type == "VARIABLE" and initial_box is True:
            variable = tok.value
            boxes[variable] = []
            inner_boxes[variable] = []
        if tok.type == "VARIABLE" and initial_box is False:
            variable = tok.value
            boxes[variable].append([])
            if inner is True:
                inner_boxes[variable].append([])
        if tok.type == "NUMBER" and initial_box is False:
            boxes[variable][-1].append(float(tok.value))
            if inner is True:
                inner_boxes[variable][-1].append(float(tok.value))
        if tok.type == 'END':
            break
    if len(boxes[variable]) == 0:
        print("No solution found!")
        print("Impossible to avoid constraints")
        return -1
    return boxes, inner_boxes


def show2Dboxes(boxes):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    fig, ax = plt.subplots()
    ax.plot([-1, -1], [1, 1])
    # add rectangle to plot
    for x, y in zip(boxes['y'], boxes['x']):
        ax.add_patch(Rectangle((y[0], x[0]), abs(y[1] - y[0]), abs(x[1] - x[0]),
                               fill=False))

    plt.show()


def pave_boxes(Expressions, DivExpressions, Variables, show2d=False, check=False):
    import os
    output = subprocess.run(
        f"realpaver \"{os.getcwd()}/paver_input.txt\"",
        shell=True, capture_output=True, text=True)

    boxes, inner_boxes = parse_boxes(output.stdout)  # Parse realpaver's output to the boxes

    if boxes != -1:
        if check:
            rival_check(boxes, Expressions, DivExpressions, Variables)  # Check correctness

        if show2d:
            show2Dboxes(boxes)  # Print boxes

    return boxes, inner_boxes

import re

import numpy as np

import sys
import time
import copy

from sympy.logic.boolalg import BooleanTrue

import Globals
from gtokens import *
import symengine as seng
import sympy
import ops_def as ops
from sympy.core.symbol import Symbol

from collections import defaultdict
import utils
import helper

import ctypes
from functools import reduce
from PredicatedSymbol import Sym, SymTup, SymConcat
from ASTtypes import *

import bool_expression_analyzer as banalyzer

import logging

logger = logging.getLogger(__name__)


class AnalyzeNode_Cond(object):

    def initialize(self):
        self.workList = []
        self.next_workList = []
        self.parentTracker = defaultdict(int)
        self.completed1 = defaultdict(set)
        self.completed2 = defaultdict(set)

        self.Accumulator = {}
        self.StatAccumulator = {}
        self.MixedAccumulator = {}
        self.InstabilityAccumulator = {}
        self.StatInstabilityAccumulator = {}
        self.MixedInstabilityAccumulator = {}

        self.results = {}
        self.bwdDeriv = {}
        self.externConstraints = ""
        self.externFreeSymbols = set()
        self.cond_syms = set()
        self.truthTable = set()

    def __init__(self, probeNodeList, argList, maxdepth, paving=False):
        self.initialize()
        self.probeList = probeNodeList
        self.trimList = probeNodeList
        self.argList = argList
        self.paving = paving
        self.maxdepth = maxdepth
        self.numBoxes = 10
        (self.parent_dict, self.cond_syms) = helper.expression_builder(probeNodeList)

    def __setup_condexpr__(self):
        for csym in self.cond_syms:
            # Fill in both csym and ~csym for delta substitution
            symNode = Globals.predTable[csym]
            Globals.condExprBank[csym] = Globals.condExprBank.get(csym) if csym in Globals.condExprBank.keys() \
                else helper.handleConditionals([symNode], etype=not Globals.argList.stable, inv=False)
            # debug prints
            (expr, FSYM, CSYM) = Globals.condExprBank[csym]
            if "True" in expr or "False" in expr:
                # print("SETUP_CONDEXPR:", expr, type(expr), csym)
                self.truthTable.add(csym)

            Globals.condExprBank[~csym] = Globals.condExprBank.get(~csym) if ~csym in Globals.condExprBank.keys() \
                else helper.handleConditionals([symNode], etype=not Globals.argList.stable, inv=True)

    def __setup_outputs__(self):
        for node in self.trimList:
            self.bwdDeriv[node] = {node: SymTup((Sym(1, Globals.__T__),))}
            self.parentTracker[node] = len(self.parent_dict[node])

    def __init_workStack__(self):
        max_depth = max(list(map(lambda x: x.depth, self.trimList)))
        # print(max_depth)
        it1, it2 = utils.partition(self.trimList, lambda x: x.depth == max_depth)
        self.next_workList = list(it1)
        self.workList = list(it2)

    def __externConstraints__(self):
        (subcond, free_symbols, cond_symbols) = helper.handleConditionals(
            [v for k, v in Globals.externPredTable.items()], etype=False)
        self.externConstraints = subcond
        self.externFreeSymbols = free_symbols

    # print("Ext Constraints: ", subcond)
    #	self.externConstraints = "( " + " && ".join(["("+str(n.f_expression)+")" for n in Globals.externPredTable.keys()]) + " )"

    def converge_parents(self, node):
        # print(node.depth, len(node.f_expression))
        # print(type(node).__name__, node.depth, self.parentTracker[node], len(node.parents) , len(self.parent_dict[node]))#, node.f_expression)
        return True if self.parentTracker[node] >= len(self.parent_dict[node]) else False

    def visit_node_deriv(self, node):
        st = time.time()
        outList = self.bwdDeriv[node].keys()
        if (len(node.children) <= 0):
            pass
        else:
            if (type(node).__name__ == "LiftOp"):
                opList = [(n[0].f_expression, n[1]) for n in node.nodeList]
                for i, child_node in enumerate(node.children):
                    for outVar in outList:
                        sti = time.time()
                        self.bwdDeriv[child_node] = self.bwdDeriv.get(child_node, {})
                        self.bwdDeriv[child_node][outVar] = self.condmerge(
                            self.bwdDeriv[child_node].get(outVar, SymTup((Sym(0.0, Globals.__F__),))).__concat__( \
                                self.bwdDeriv[node][outVar] * \
                                SymTup((Sym(1.0, node.nodeList[i][1]),)), trim=True))
                        eti = time.time()
                    # print("Lift-op:One bak prop time = ", eti-sti)
                    self.next_workList.append(child_node)
                    self.parentTracker[child_node] += 1
            else:
                DerivFunc = ops._DFOPS[node.token.type]
                opList = [child.f_expression for child in node.children]
                for i, child_node in enumerate(node.children):
                    for outVar in outList:
                        sti = time.time()
                        self.bwdDeriv[child_node] = self.bwdDeriv.get(child_node, {})
                        self.bwdDeriv[child_node][outVar] = self.condmerge(
                            self.bwdDeriv[child_node].get(outVar, SymTup((Sym(0.0, Globals.__F__),))).__concat__( \
                                self.bwdDeriv[node][outVar] * \
                                (SymTup((Sym(0.0, Globals.__T__),)) \
                                     if utils.isConst(child_node) else \
                                     DerivFunc[i](opList)), trim=True))
                        eti = time.time()
                    # print("One bak prop time = ", eti-sti)
                    self.next_workList.append(child_node)
                    self.parentTracker[child_node] += 1
        self.completed1[node.depth].add(node)
        et = time.time()

    # print("@node",node.depth, node.f_expression)
    # print("Time taken =", et-st,"\n\n")

    def traverse_ast(self):
        next_workList = []
        curr_depth = 0
        next_depth = -1
        while (len(self.workList) > 0):
            node = self.workList.pop()
            curr_depth = node.depth
            next_depth = curr_depth - 1
            if (utils.isConst(node)):
                self.completed1[node.depth].add(node)
            elif self.completed1[node.depth].__contains__(node):
                pass
            elif (self.converge_parents(node)):
                self.visit_node_deriv(node)
            else:
                self.workList.append(node)

            if (len(self.workList) == 0 and next_depth != -1 and len(self.next_workList) != 0):
                nextIter, currIter = utils.partition(self.next_workList, \
                                                     lambda x: x.depth == next_depth)
                self.workList = list(set(currIter))
                self.next_workList = list(set(nextIter))

    # merge the error terms
    def merge_discontinuities(self, acc, opLimit):
        racc = acc
        constCond = Globals.__T__
        constAcc = [0.0]
        temp_racc = []
        temp_dict = {}
        res_avg_maxres = (0, 0)
        lim = 100 if (len(racc) > 20) else opLimit
        for els in racc:
            (expr, cond) = els.exprCond
            # print("lim:", seng.count_ops(expr), lim, len(racc))
            if seng.count_ops(expr) == 0:
                constCond = constCond | cond
                constAcc.append(abs(expr))
            elif seng.count_ops(expr) > lim:
                # print("lim:", expr, lim, len(racc))
                (cond_expr, free_symbols) = self.parse_cond(cond)
                # print("PROCESS_EXPRESSION_LOC3")
                [errIntv, res_avg_maxres] = self.process_expression(expr, cond_expr, free_symbols,
                                                                    get_stats=Globals.argList.stat_err_enable or Globals.argList.stat)
                err = max([abs(i) for i in errIntv]) if errIntv is not None else 0
                maxres = err if res_avg_maxres is None else res_avg_maxres[1]

                # print(type(err), res_avg_maxres[1]*pow(2,-53))
                if Globals.argList.stat_err_enable:
                    frac = Globals.argList.stat_err_fraction
                    ratio = 0 if err < 0.01 else (err - maxres) / err;
                    if ratio > frac:
                        err = maxres
                # print("Selected error = {full_val}( {normalized} )".format(full_val=err, \
                #									normalized = err*pow(2,-53)))

                if (err == np.inf and Globals.argList.stat):
                    err = res_avg_maxres[1]
                temp_racc.append(Sym(err, cond))
            else:
                temp_racc.append(els)
        s = SymTup(els for els in temp_racc).__concat__(SymTup((Sym(max(constAcc), constCond),)), trim=True)
        return s

    def add_instability_error(self, expr_solve, out=False):
        temp_list = []
        if len(expr_solve) > 1:
            unstable_cands = list(filter(lambda x: bool(helper.freeCondSymbols(x).difference(self.truthTable)), \
                                         expr_solve))
            count = 0
            if len(unstable_cands) > 1:
                for i in range(0, len(unstable_cands)):
                    for j in range(i + 1, len(unstable_cands)):
                        count += 1
                        expr_diff = (unstable_cands[i].exprCond[0] - unstable_cands[j].exprCond[0]).__abs__()
                        (cond1_expr, free_symbols1) = self.parse_cond(unstable_cands[i].exprCond[1])
                        (cond2_expr, free_symbols2) = self.parse_cond(unstable_cands[j].exprCond[1])
                        cond_expr = utils.process_conditionals(cond1_expr, cond2_expr)
                        free_symbols = free_symbols1.union(free_symbols2)
                        [errIntv, res_avg_maxres] = self.process_expression(expr_diff, cond_expr, free_symbols,
                                                                            get_stats=Globals.argList.stat_err_enable or Globals.argList.stat)
                        if errIntv is not None:
                            err = max([abs(i) for i in errIntv if i is not None] if errIntv is not None else [0])
                            temp_list += [(err, res_avg_maxres[1] if res_avg_maxres is not None else 0.0,
                                           (unstable_cands[i], unstable_cands[j]))]
                if len(temp_list) > 0:
                    temp_list.sort(key=lambda tup: -tup[0])  # reverse sort
                    if temp_list[0][0] > 0.0 and out and Globals.argList.report_instability:
                        Globals.InstabDict[temp_list[0][2]] = (temp_list[0][0], temp_list[0][1])
                    return (temp_list[0][0], temp_list[0][1])
                return (0, 0)
            else:
                return (0, 0)
        else:
            return (0, 0)

    # return max(temp_list)

    def propagate_symbolic(self, node):
        for outVar in self.bwdDeriv[node].keys():
            expr_solve = self.condmerge( \
                ((self.bwdDeriv[node][outVar]) * \
                 (node.get_noise(node)) * node.get_rounding()) \
                ).__abs__()
            acc = self.Accumulator.get(outVar, SymTup((Sym(0.0, Globals.__T__),)))
            if (len(acc) > 10):
                acc = self.merge_discontinuities(self.condmerge(acc), 1000)

            # instability_error(2tup) -> (rigorous err, max_stat_err)
            # instability_error = (0,0) if not Globals.argList.report_instability else self.add_instability_error(expr_solve)
            instability_error = (0, 0) if not Globals.argList.report_instability else self.add_instability_error(
                node.f_expression, out=True)
            instab_error = instability_error[0]
            if Globals.argList.stat_err_enable:
                fraction = Globals.argList.stat_err_fraction
                ratio = 0 if instab_error <= 0.01 else (instability_error[0] - instability_error[1]) / \
                                                       instability_error[0]
                if ratio > fraction:
                    instab_error = instability_error[1]
            self.InstabilityAccumulator[outVar] = self.InstabilityAccumulator.get(outVar, 0.0) + \
                                                  instab_error
            expr_solve = self.merge_discontinuities(expr_solve, 1000)
            if Globals.argList.report_instability:
                Globals.InstabID[node] = instability_error
            # print("Local instability errors:", instability_error)
            val = acc.__concat__(expr_solve, trim=True)

            self.Accumulator[outVar] = val

    def visit_node_ferror(self, node):

        for child in node.children:
            if not self.completed2[child.depth].__contains__(child):
                self.visit_node_ferror(child)

        if (self.completed1[node.depth].__contains__(node)):
            self.propagate_symbolic(node)
        self.completed2[node.depth].add(node)

    def condmerge(self, tupleList):
        ld = {}
        for els in tupleList:
            (expr, cond) = els.exprCond
            ld[cond] = ld.get(cond, SymTup((Sym(0.0, Globals.__T__),))) + SymTup((els,))

        # for k,v in ld.items():
        #	print("//-- Cond =", k)
        #	print(v,"\n")
        # print("Size,", len(tupleList))

        return reduce(lambda x, y: x.__concat__(y, trim=True), [v for k, v in ld.items()],
                      SymTup((Sym(0.0, Globals.__T__),)))

    def subsitute(self, tcond, symDict, inv_symDict):
        str_tcond = str(tcond)
        inv_keys = list([str(k) for k in inv_symDict.keys()])
        inv_keys.sort(reverse=True)
        for k in inv_keys:
            str_tcond = str_tcond.replace(k, inv_symDict[sympy.sympify(k)])
        fwd_keys = list([str(k) for k in symDict.keys()])
        fwd_keys.sort(reverse=True)
        for k in fwd_keys:
            str_tcond = str_tcond.replace(k, symDict[sympy.sympify(k)])

        return str_tcond

    def parse_cond(self, cond):
        tcond = cond
        # print("\n ******** Parsing Conditional = {pcond}".format(pcond=tcond))
        logger.info("\n Parsing Conditional = {pcond}".format(pcond=tcond))
        set_free_symbols = set()
        if tcond not in (True, False):
            free_syms = tcond.free_symbols
            if isinstance(free_syms, Symbol):
                free_syms = [free_syms]
            for fsym in free_syms:
                symNode = Globals.predTable[fsym]
                # print("Handling Condtional {symID}".format(symID=fsym))
                logger.info("Handling Condtional {symID}".format(symID=fsym))
                dict_element = Globals.condExprBank.get(fsym)
                # print("DICT_EL:", dict_element)
                # print(Globals.condExprBank.keys())

                if dict_element is None:
                    Globals.condExprBank[fsym] = helper.handleConditionals([symNode], etype=not Globals.argList.stable,
                                                                           inv=False)
                    Globals.condExprBank[~fsym] = helper.handleConditionals([symNode], etype=not Globals.argList.stable,
                                                                            inv=True)
                    dict_element = Globals.condExprBank.get(fsym)

                # Bug. sometimes negation of condition has more free_syms than original condition
                if fsym.name.__contains__("~"):
                    set_free_symbols = set_free_symbols.union(Globals.condExprBank[fsym.name[1:]][1])
                else:
                    set_free_symbols = set_free_symbols.union(Globals.condExprBank[~fsym][1])

                assert (dict_element is not None)
                (subcond, free_symbols, cond_symbols) = dict_element[0], dict_element[1], dict_element[2]
                # subcond = subcondList[0]
                # print("SubCond: {symID} : {SubCond}\n\n".format(symID=fsym, SubCond=subcond))
                logger.info("SubCond:{symID} : {SubCond}\n\n".format(symID=fsym, SubCond=subcond))
                Globals.condExprBank[fsym] = (subcond, free_symbols, cond_symbols)
                set_free_symbols = set_free_symbols.union(free_symbols)

                # set_free_symbols = set_free_symbols.union(Globals.condExprBank.get(fsym)[1])

            symDict = {fsym: Globals.condExprBank[fsym][0] for fsym in free_syms}
            inv_symDict = {~fsym: Globals.condExprBank[~fsym][0] for fsym, v in symDict.items() if
                           v not in ('(True)', 'True', '(False)', 'False', True, False)}
            tcond = self.subsitute(tcond, symDict, inv_symDict)
            # print("Finished parsing -> {cond} : {cexpr}\n".format(cond=cond, cexpr=tcond))
            logger.info("Finished parsing -> {cond} : {cexpr}".format(cond=cond, cexpr=tcond))
            return tcond, set_free_symbols
        return "(<<{tcond}>>)".format(tcond=tcond), set_free_symbols

    def boxify(self, box, intv_dict):

        if box:
            for var in box.contents:
                if var.name.decode() != "Garbage":
                    name = var.name.decode()
                    x = var.x
                    y = var.y
                    intv_dict[name] = [x, y]
                # print("Valid:", [name,x,y])
                else:
                    intv_dict.clear()
                    Globals.garbageCount += 1
                    # print(var.name.decode(), Globals.garbageCount)
                    return intv_dict
            return intv_dict

        else:
            # print("No valid box")
            intv_dict.clear()
            return intv_dict

    def analyze_box(self, box, expr, cond_free_symbols):
        # print("AnayzeBox:", expr.free_symbols, cond_free_symbols)
        try:
            FREE_SYMS = expr.free_symbols.union(cond_free_symbols)
            intv_dict = {str(var): Globals.inputVars[var]["INTV"] for var in FREE_SYMS}
        except:
            try:
                intv_dict = {str(var): Globals.inputVars[var]["INTV"] for var in cond_free_symbols}
            except:
                intv_dict = dict()
        # intv_dict = dict()
        # print("What:", intv_dict)
        intv_dict = self.boxify(box, intv_dict)
        if len(intv_dict.keys()) == 0:
            return (None, None)
        flist = list(intv_dict.keys())
        flist.sort()
        ret_list = list()
        # for k,v in intv_dict.items():
        for k in flist:
            v = intv_dict[k]
            ret_list += ["{fsym} = {intv}".format(fsym=k, intv=str(intv_dict[k]))]
        retStr = ";".join(ret_list) + ";"
        return (retStr, intv_dict)

    # list of boxes = [(inputStr, intv_dict), ...]

    def extract_boxes(self, rpBoxes, expr, cond_free_symbols):

        boxIntervals = []

        fsym_set = set()

        for box in rpBoxes.contents:
            retTup = self.analyze_box(box, expr, cond_free_symbols)
            if retTup[0] is not None:
                boxIntervals.append(retTup)
            else:
                return boxIntervals

        return boxIntervals

    # return type -> [el0, el1]
    # el0 -> the widest interval from all the sub-bozes
    # el1 -> the statistical information due to sampling from the error function --> extended over all the bozes

    def process_expression(self, expr, cond_expr, free_symbols, get_stats=False):

        if self.paving:
            processConds = utils.process_conditionals(cond_expr, self.externConstraints)
            rpConstraint = banalyzer.bool_expression_analyzer(processConds).start()
            if "False" in rpConstraint:
                # print("Invalid constraint -> nothing to invoke, return None")
                return [None, None]
            elif "True" in rpConstraint:
                # print("Constraint true -> invoke gelpia on full box")
                Intv = utils.generate_signature(expr, \
                                                cond_expr, \
                                                self.externConstraints, \
                                                free_symbols.union(self.externFreeSymbols))
                res_avg_maxres = Intv if not get_stats else utils.get_statistics(expr)
            # print("def:process_expressions: Constraint is Always True --> Unconstrained solution (no RealPaver)")
            # print("INTV-out1: {intv}\n".format(intv=Intv))
            # print("")
            else:
                res_avg_maxres = [0, 0] if not get_stats else utils.get_statistics(expr)
                [rpVars, numVars] = utils.rpVariableStr(free_symbols.union(self.externFreeSymbols))
                [rpBoxes, fhand] = helper.rpInterface(rpVars + "Constraints " + rpConstraint, numVars, self.numBoxes)
                boxIntervals = self.extract_boxes(rpBoxes, expr, free_symbols.union(self.externFreeSymbols))

                if len(boxIntervals) >= 1:
                    Intv = utils.generate_signature(expr, \
                                                    # cond_expr, \
                                                    cond_expr, \
                                                    self.externConstraints, \
                                                    free_symbols.union(self.externFreeSymbols), boxIntervals[0][0])
                    res_avg_maxres = Intv if not get_stats else utils.get_statistics(expr, boxIntervals[0][1])
                    # print("INTV; ", Intv, boxIntervals[0], Globals.gelpiaID)
                    boxCount = 0
                    for box in boxIntervals[1:]:
                        currIntv = utils.generate_signature(expr, \
                                                            # cond_expr, \
                                                            cond_expr, \
                                                            self.externConstraints, \
                                                            free_symbols.union(self.externFreeSymbols), box[0])
                        curr_res_avg_maxres = currIntv if not get_stats else utils.get_statistics(expr, box[1])
                        Intv = [min(Intv[0], currIntv[0]), max(Intv[1], currIntv[1])]
                        res_avg_maxres = [max(res_avg_maxres[0], curr_res_avg_maxres[0]), \
                                          max(res_avg_maxres[1], curr_res_avg_maxres[1])]
                        boxCount += 1
                    # print("\tBOX[{count}] = {bbox} , Gelpia-query = {query}\n\t INTV={intv}\n".format(count=boxCount, bbox=box, query=Globals.gelpiaID, intv=Intv))#, Intv, box, Globals.gelpiaID)

                # print("def:process_expressions: INTV-out2; ", Intv)
                else:
                    Intv = utils.generate_signature(expr, \
                                                    # cond_expr, \
                                                    cond_expr, \
                                                    self.externConstraints, \
                                                    free_symbols.union(self.externFreeSymbols))

                    # print("def:process_expressions: Whole Box required!")
                    # print("def:process_expressions: INTV-out3; ", Intv)
                    return [None, None]
        else:
            # print("Paving disabled -> invoke gelpia on full box")
            res_avg_maxres = None if not get_stats else utils.get_statistics(expr)
            Intv = utils.generate_signature(expr, \
                                            # cond_expr, \
                                            cond_expr, \
                                            self.externConstraints, \
                                            free_symbols.union(self.externFreeSymbols))
        # print("def:process_expressions: Paving disabled!")
        # print("def:process_expressions: INTV-out4; ", Intv)
        return [Intv, res_avg_maxres]

    def first_order_error(self):

        for node in self.trimList:
            if not self.completed2[node.depth].__contains__(node):
                self.visit_node_ferror(node)
        self.Accumulator = {k: self.condmerge(v) for k, v in self.Accumulator.items()}

        ## Placeholder for gelpia invocation
        res_avg_maxres = (0, 0)

        # print("Final Solving stage")
        for node, tupleList in self.Accumulator.items():
            errList = []
            funcList = []
            statList = []
            for els in tupleList:
                expr, cond = els.exprCond
                (cond_expr, free_symbols) = self.parse_cond(cond)
                # print("PROCESS_EXPRESSION_LOC1")
                # print("Outside:", cond_expr)
                [errIntv, res_avg_maxres] = self.process_expression(expr, cond_expr, free_symbols,
                                                                    get_stats=Globals.argList.stat_err_enable or Globals.argList.stat)
                err = max([abs(i) for i in errIntv]) if errIntv is not None else 0
                # print("STAT: SP:{err}, maxres:{maxres}, avg:{avg}".format(\
                #	err = err, maxres = res_avg_maxres[1] if res_avg_maxres is not None else 0, avg = res_avg_maxres[0] if res_avg_maxres is not None else 0 \
                # ))
                max_stat_err = res_avg_maxres[1] if res_avg_maxres is not None else 0
                statList.append(max_stat_err)
                if (err == np.inf and Globals.argList.stat):
                    err = res_avg_maxres[1]
                errList.append(err)

            ret_intv = None
            # print("Debug:", node.f_expression)
            ##-------- Evaluate the instability at the output ----------------
            # instability_error(2tup) -> (rigorous err, max_stat_err)
            instability_error = (0, 0) if not Globals.argList.report_instability \
                else self.add_instability_error(node.f_expression, out=True)
            instab_error = instability_error[0]
            ##----------------------------------------------------------------
            # print("Inside top:", instability_error)
            # print("NODE-EXPR:", node.f_expression)
            for exprTup in node.f_expression:
                expr, cond = exprTup.exprCond
                (cond_expr, free_symbols) = self.parse_cond(cond)
                # print("PROCESS_EXPRESSION_LOC2", expr)
                [fintv, dumdum] = self.process_expression(expr, cond_expr, free_symbols, get_stats=False)
                # ret_intv = fintv if ret_intv is None else [min(ret_intv[0],fintv[0]), max(ret_intv[1], fintv[1])]
                # print("1:", fintv, ret_intv)
                ret_intv = None if fintv is None and ret_intv is None else fintv if ret_intv is None \
                    else ret_intv if fintv is None \
                    else [min(ret_intv[0], fintv[0]), max(ret_intv[1], fintv[1])]
            # print(node.f_expression)

            ## ---- Pick and choose which error to keep
            node_err = max(errList)

            if Globals.argList.stat_err_enable:
                frac = Globals.argList.stat_err_fraction
                ratio = 0 if node_err <= 0.01 else (max(errList) - max(statList)) / max(errList)
                ratio_instab = 0 if instab_error <= 0.01 else \
                    (instability_error[0] - instability_error[1]) / instability_error[0]
                if ratio > frac:
                    node_err = max(statList)
                if ratio_instab > frac:
                    instab_error = instability_error[1]

            self.InstabilityAccumulator[node] = self.InstabilityAccumulator.get(node, 0.0) + instab_error

            self.results[node] = {"ERR": node_err, \
                                  "SERR": 0.0, \
                                  # "INSTABILITY": self.InstabilityAccumulator[node], \
                                  "INSTABILITY": instab_error, \
                                  "INTV": ret_intv \
                                  }

            # print("MaxError:", max(errList)*pow(2,-53), fintv)
            logger.info(" > MaxError:\n {error} ; {fintv}\n".format(error=max(errList) * pow(2, -53), fintv=ret_intv))
            # print(" > MaxError:\n {error} ; {fintv}\n".format(error=max(errList)*pow(2,-53), fintv=ret_intv))
            if self.InstabilityAccumulator[node] != 0.0:
                # print(" > Instability:\n {instab} ;".format(instab=instab_error))
                logger.info(" > Instability:\n {instab} ;".format(instab=instab_error))

        return self.results

    def rebuildASTNode(self, node, local_completed):

        for child in node.children:
            if not local_completed.__contains__(child):
                self.rebuildASTNode(child, local_completed)
        node.depth = 0 if len(node.children) == 0 or type(node).__name__ == "FreeVar" \
            else max([child.depth for child in node.children]) + 1

        if node.token.type in ops.DFOPS_LIST:
            local_completed[node] = node.depth

    def rebuildAST(self, probeList):

        local_completed = defaultdict(int)
        Globals.simplify = True
        ## rebuild AST for cond sym nodes
        for csym, symNode in Globals.predTable.items():
            # print("Ever came here1?")
            self.rebuildASTNode(symNode, local_completed)
        # print("CSYM:", csym, symNode.depth)

        ## rebuild AST for regular nodes
        for node in probeList:
            # print("Ever came here2?")
            if not local_completed.__contains__(node):
                self.rebuildASTNode(node, local_completed)

        maxdepth = max([node.depth for node in probeList])
        Globals.depthTable = {depth: set([node for node in local_completed.keys() if node.depth == depth]) for depth in
                              range(maxdepth + 1)}

        return maxdepth

    def abstractNodes(self, results):

        for node, res in results.items():
            Globals.FID += 1
            name = seng.var("FR" + str(Globals.FID))

            # Debug part, delete whenever you need
            # s = node.debug_print()
            # Globals.debugList[str(name)] = s

            node.__class__ = FreeVar
            node.children = ()
            node.depth = 0

            node.set_noise(node, (res["ERR"], res["ERR"]))
            node.mutate_to_abstract(name, ID)

            Globals.inputVars[name] = {"INTV": res["INTV"]}
            Globals.GS[0]._symTab[name] = ((node, Globals.__T__),)

    def simplify_with_abstraction(self, sel_candidate_list, argList, MaxDepth, bound_min, bound_max):
        Globals.condExprBank.clear()
        obj = AnalyzeNode_Cond(sel_candidate_list, self.argList, MaxDepth, paving=False)
        results = obj.start(bound_min=bound_min, bound_max=bound_max)

        # print("Ever came here3?")
        self.abstractNodes(results)
        return self.rebuildAST(self.trimList)

    def abstractAnalysis(self, MaxDepth, bound_min, bound_max):
        [abs_depth, sel_candidate_list] = helper.selectCandidateNodes(MaxDepth, bound_min, bound_max)

        while abs_depth == MaxDepth and bound_min < bound_max + 1:
            bound_max = bound_max - 1
            [abs_depth, sel_candidate_list] = helper.selectCandidateNodes(MaxDepth, bound_min, bound_max)

        if (len(sel_candidate_list) > 0):
            return self.simplify_with_abstraction(sel_candidate_list, self.argList, MaxDepth, bound_min, bound_max)
        else:
            # print("Something is wrong ... sorry! investigate depth table")
            sys.exit()

    # Build the expression
    # If too large depth : apply abstraction

    def default_res(self):
        # print("Setting default results")
        for node in self.trimList:
            expr = node.f_expression[0].exprCond[
                0]  # just the expr part --> if leaf => matches the symbolic form of inputs or FVs
            # print("In default seetings -> ", expr)
            self.results[node] = {"ERR": 0.0, \
                                  "SERR": 0.0, \
                                  # "INSTABILITY": self.InstabilityAccumulator[node], \
                                  "INSTABILITY": 0.0, \
                                  "INTV": [0, 0] if expr not in Globals.inputVars.keys() else Globals.inputVars[expr] \
                                  }

        return self.results

    # def start(self, bound_min=Globals.argList.mindepth, bound_max=Globals.argList.maxdepth ):
    def start(self, bound_min=10, bound_max=20):

        MaxDepth = max([node.depth for node in self.trimList])

        # print("MAXDEPTH1:{MaxDepth}".format(MaxDepth=MaxDepth))
        while (MaxDepth >= bound_min and MaxDepth >= bound_max):
            # MaxOps = max([node.f_expression.__countops__() for node in self.trimList])
            # print("MAXDEPTH2:{MaxDepth}".format(MaxDepth=MaxDepth))
            MaxDepth = self.abstractAnalysis(MaxDepth, bound_min, bound_max)
        # print("out of while")
        if MaxDepth == 0:
            return self.default_res()
        (self.parent_dict, self.cond_syms) = helper.expression_builder(self.trimList)
        self.__setup_condexpr__()
        self.__init_workStack__()
        self.__setup_outputs__()
        self.__externConstraints__()
        # print("CondExpr:", Globals.condExprBank.keys())

        dt1 = time.time()
        # print(" > Begin building derivatives....")
        logger.info(" > Begin building derivatives....")
        self.traverse_ast()
        dt2 = time.time()
        # print(" > Finished in {duration} secs\n".format(duration=dt2-dt1))
        logger.info(" > Finished in {duration} secs\n".format(duration=dt2 - dt1))

        # self.completed.clear()
        fe1 = time.time()
        # print("//----------------------------//")
        # print(" > Analyzing error for the current abstraction block...\n")
        logger.info("Analyzing error for the current abstraction block...\n")
        res = self.first_order_error()
        fe2 = time.time()
        # print(" > Finished in {duration} secs\n".format(duration=fe2-fe1))
        logger.info("Finished in {duration} secs\n".format(duration=fe2 - fe1))

        return res

#!/usr/bin/python3
import sys
import os
import time
import argparse
import symengine as seng

from lexer import Slex
from parser import Sparser

from collections import defaultdict

from ASTtypes import *

import helper
from AnalyzeNode_Cond import AnalyzeNode_Cond

import logging


def parseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', help='Test file name', required=True)
    parser.add_argument('--parallel', help='Enable parallel optimizer queries:use for large ASTs', \
                        default=False, action='store_true')
    parser.add_argument('--enable-abstraction', help='Enable abstraction of internal node defintions,\
													  value indiactes level\
													  of abstraction. By default enabled to level-1. \
													  To disable pass 0', default=False, action='store_true')
    parser.add_argument('--mindepth', help='Min depth for abstraction. Default is 10', \
                        default=10, type=int)
    parser.add_argument('--maxdepth', help='Max depth for abstraction. Limiting to 40', \
                        default=40, type=int)
    parser.add_argument('--stat', help='Report statistics on error expression. Disabled by default', \
                        default=False, action='store_true')
    parser.add_argument('--samples', help='Number of samples for stats', \
                        default=1000, type=int)
    parser.add_argument('--report-instability', help='Report instability for every divergent path. Disabled by default', \
                        default=False, action='store_true')
    parser.add_argument('--simplify', help='Simplify expression -> could be costly for very large expressions',
                        default=False, action='store_true')
    parser.add_argument('--logfile', help='Python logging file name -> default is default.log', default='default.log')
    parser.add_argument('--outfile', help='Name of the output file to write error info', default='outfile.txt')
    parser.add_argument('--std', help='Print the result to stdout', default=False, action='store_true')
    parser.add_argument('--sound', help='Turn on analysis for higher order errors', default=False, action='store_true')
    parser.add_argument('--compress',
                        help='Perform signature matching to reduce optimizer calls using hashing and md5 signature',
                        default=False, action='store_true')
    parser.add_argument('--force',
                        help='Sideline additional tricks used for non-linear examples. Use this option for linear examples',
                        default=False, action='store_true')
    parser.add_argument('--enable-constr', help='Enable solving constrained optimization queries', default=False,
                        action='store_true')
    parser.add_argument('--stat-err-enable', help='Enable statistical error sampling', default=False,
                        action='store_true')
    parser.add_argument('--stat-err-fraction', help='Fractional bound for using statistical error. Default is 0.5', \
                        default=0.5, type=float)
    parser.add_argument('--domain-checks', help="Enable domain checks to avoid infinity errors", default=False,
                        action='store_true')
    parser.add_argument('--stable', help='Inform to ignore instability correction', default=False, action='store_true')
    parser.add_argument('--gverbose', help='Create dumps of each optimizer query for debugging', default=False,
                        action='store_true')

    result = parser.parse_args()
    return result


def rebuildASTNode(node, completed):
    for child in node.children:
        if not completed.__contains__(child):
            rebuildASTNode(child, completed)

    node.depth = 0 if len(node.children) == 0 or type(node).__name__ == "FreeVar" \
        else max([child.depth for child in node.children]) + 1

    if node.token.type in ops.DFOPS_LIST:
        completed[node] = node.depth


def rebuildAST():
    rb1 = time.time()
    logger.info("\n  ********* Rebuilding AST post abstracttion ********\n")
    probeList = mod_probe_list(helper.getProbeList())

    completed = defaultdict(int)

    Globals.simplify = True  ## Enable simplify to begin
    for csym, symNode in Globals.predTable.items():
        rebuildASTNode(symNode, completed)

    for node in probeList:
        if not completed.__contains__(node):
            rebuildASTNode(node, completed)

    maxdepth = max([node.depth for node in probeList])
    beforetotalNodes = sum([len(v) for k, v in Globals.depthTable.items()])
    Globals.depthTable = {depth: set([node for node in completed.keys() if node.depth == depth]) for depth in
                          range(maxdepth + 1)}

    aftertotalNodes = sum([len(v) for k, v in Globals.depthTable.items()])

    logger.info(" >  Rebuilt AST Nodes = {new_num_nodes} ({old_num_nodes})".format(old_num_nodes=beforetotalNodes,
                                                                                   new_num_nodes=aftertotalNodes))
    logger.info(" >  Rebuilt AST Depth = {ast_depth}".format(ast_depth=maxdepth))
    rb2 = time.time()
    logger.info("  **********Rebuilt AST in {duration} secs********\n".format(duration=rb2 - rb1))


def abstractNodes(results):
    for node, res in results.items():
        Globals.FID += 1
        name = seng.var("FR" + str(Globals.FID))
        node.__class__ = FreeVar
        node.children = ()
        node.depth = 0

        node.set_noise(node, (res["ERR"], res["SERR"]))
        node.mutate_to_abstract(name, ID)

        Globals.inputVars[name] = {"INTV": res["INTV"]}
        Globals.GS[0]._symTab[name] = ((node, Globals.__T__),)


def simplify_with_abstraction(sel_candidate_list, argList, maxdepth, final=False):
    Globals.condExprBank.clear()

    obj = AnalyzeNode_Cond(sel_candidate_list, argList, maxdepth, paving=False)
    results = obj.start()

    if "flag" in results.keys():
        return results

    del obj
    if final:
        return results

    abstractNodes(results)
    rebuildAST()

    return dict()


def full_analysis(probeList, argList, maxdepth):
    res = simplify_with_abstraction(probeList, argList, maxdepth, final=True)
    return res


def mod_probe_list(probeNodeList):
    probeList = helper.getProbeList()
    probeList = [nodeList[0][0] for nodeList in probeList]
    return probeList


def ErrorAnalysis(argList):
    absCount = 1
    probeList = helper.getProbeList()
    maxdepth = max([max([n[0].depth for n in nodeList]) for nodeList in probeList])
    # print("maxdepth = ", maxdepth)
    # logger.info("Full AST_DEPTH : {ast_depth}".format(ast_depth=maxdepth))
    probeList = [nodeList[0][0] for nodeList in probeList]
    bound_mindepth, bound_maxdepth = argList.mindepth, argList.maxdepth

    if (argList.enable_abstraction):
        while (maxdepth >= bound_maxdepth and maxdepth >= bound_mindepth):
            [abs_depth, sel_candidate_list] = helper.selectCandidateNodes(maxdepth, bound_mindepth, bound_maxdepth)
            if (len(sel_candidate_list) > 0):
                absCount += 1
                results = simplify_with_abstraction(sel_candidate_list, argList, maxdepth)
                maxopCount = results.get("maxOpCount", 1000)
                probeList = mod_probe_list(helper.getProbeList())
                maxdepth = max([n.depth for n in probeList])
                if (maxopCount > 1000 and maxdepth > 8 and bound_mindepth > 5):
                    bound_maxdepth = maxdepth if bound_maxdepth > maxdepth else bound_maxdepth - 2 if bound_maxdepth - bound_mindepth > 4 else bound_maxdepth
                    bound_mindepth = bound_mindepth - 2 if bound_maxdepth - bound_mindepth > 4 else bound_mindepth
                elif maxdepth <= bound_maxdepth and maxdepth > bound_mindepth:
                    bound_maxdepth = maxdepth
                    assert (bound_maxdepth >= bound_mindepth)
            else:
                break
        return full_analysis(probeList, argList, maxdepth)
    else:
        return full_analysis(probeList, argList, maxdepth)


if __name__ == "__main__":
    start_exec_time = time.time()
    argList = parseArguments()
    Globals.argList = argList
    Globals.enable_constr = argList.enable_constr
    Globals.domain_checks = argList.domain_checks
    sys.setrecursionlimit(10 ** 6)
    # print("LEVEL_TOP: Parsed argList = ", argList)
    text = open(argList.file, 'r').read()
    fout = open(argList.outfile, 'w')

    # --------- Setup Logger ------------------------------------
    logging.basicConfig(filename=argList.logfile,
                        level=logging.INFO,
                        filemode='w')
    logger = logging.getLogger()

    ##-------- Check if realpaver is available -----------------
    Globals.ROOT_DIR = os.getenv("SAT_ROOT")
    assert (os.path.isdir(Globals.ROOT_DIR))

    # --------- Lexing and Parsing ------------------------------
    start_parse_time = time.time()
    lexer = Slex()
    parser = Sparser(lexer)
    parser.parse(text)
    del parser
    del lexer
    end_parse_time = time.time()
    parse_time = end_parse_time - start_parse_time
    logger.info("Parsing time : {parse_time} secs".format(parse_time=parse_time))

    # ------ Main Analysis ----------------------------------------
    ea1 = time.time()
    results = ErrorAnalysis(argList)
    ea2 = time.time()

    end_exec_time = time.time()
    full_time = end_exec_time - start_exec_time

    logger.info("Optimizer calls : {num_calls}\n".format(num_calls=Globals.ibexID))
    logger.info("Parsing time : {parsing_time}\n".format(parsing_time=parse_time))
    logger.info("Analysis time : {analysis_time}\n".format(analysis_time=ea2 - ea1))
    logger.info("Full time : {full_time}\n".format(full_time=full_time))

    # ------ Write results -------
    for outVar in Globals.outVars:
        num_ulp_maxError = results[Globals.GS[0]._symTab[outVar][0][0]]["ERR"]
        num_ulp_SecondmaxError = results[Globals.GS[0]._symTab[outVar][0][0]]["SERR"]
        funcIntv = results[Globals.GS[0]._symTab[outVar][0][0]]["INTV"]
        maxError = num_ulp_maxError * pow(2, -53)
        SecondmaxError = num_ulp_SecondmaxError * pow(2, -53)
        outIntv = [funcIntv[0] - maxError - SecondmaxError, funcIntv[1] + maxError + SecondmaxError]
        abserror = (maxError + SecondmaxError)
        instability = results[Globals.GS[0]._symTab[outVar][0][0]]["INSTABILITY"] if argList.report_instability else "UNDEF"

        dumpStr = "/========================\n"
        dumpStr += "LEVEL_TOP: VAR : {outVar}\n".format(outVar=str(outVar))
        dumpStr += "LEVEL_TOP: Optimizer cells : {num_calls}\n".format(num_calls=Globals.ibexID)
        dumpStr += "LEVEL_TOP: Parsing time : {parsing_time}\n".format(parsing_time=parse_time)
        dumpStr += "LEVEL_TOP: Analysis time : {analysis_time}\n".format(analysis_time=ea2 - ea1)
        dumpStr += "LEVEL_TOP: Full_time : {full_time}\n".format(full_time=full_time)
        dumpStr += "LEVEL_TOP: REAL_INTERVAL : {funcIntv}\n".format(funcIntv=str(funcIntv))
        dumpStr += "LEVEL_TOP: FP_INTERVAL : {outIntv}\n".format(outIntv=str(outIntv))
        dumpStr += "LEVEL_TOP: INSTABILITY : {instability}\n".format(instability=str(instability))
        dumpStr += "LEVEL_TOP: ABSOLUTE_ERROR : {abserror}\n".format(abserror=str(abserror))
        if Globals.domain_checks:
            dumpStr += "LEVEL_TOP: Domain check found these constraints to avoid infinity:\n"
            t = Globals.domainConds
            for d in Globals.domainConds:
                dumpStr += "\t" + d.replace(">>|<<", ")||(").replace("<<", "(").replace(">>", ")") + ";\n"

        print(dumpStr)
        fout.write(dumpStr + "\n")
        fout.close()

import re
import Globals

import random
import time

import symengine as seng
from itertools import tee


from ibex_utils import invoke_ibex


def rpVariableStr( cond_free_symbols ):
	ret_list = list()
	flist = [str(i) for i in cond_free_symbols]
	flist.sort()
	for fsyms in flist:
		ret_list += ["{Variable} in {intv}".format(Variable=fsyms, intv=str(Globals.inputVars[seng.var(fsyms)]["INTV"]))]
		#ret_list += [str(fsyms), " in ", str(Globals.inputVars[seng.var(fsyms)]["INTV"]), ";"]
	retStr = " ".join(["Variables", ", ".join(ret_list)+" ;"])
	return [retStr, len(flist)]
	

def process_conditionals( innerConds, externConds ):
	str_inner = str(innerConds)
	str_outer = str(externConds)
	str_cond_expr = " & ".join([str_inner]+([] if externConds is None or len(str_outer)==0 else [str_outer]))
	str_cond_expr = re.sub(r'\&\&', "&", str_cond_expr)
	str_cond_expr = re.sub(r'\|\|', "|", str_cond_expr)
	str_cond_expr = re.sub(r'\&', "&&", str_cond_expr)
	str_cond_expr = re.sub(r'\|', "||", str_cond_expr)
	str_cond_expr = re.sub(r'\*\*', "^", str_cond_expr)
	str_cond_expr = re.sub(r'Abs', "abs", str_cond_expr)
	str_cond_expr = re.sub(r're\b', "", str_cond_expr)
	str_cond_expr = re.sub(r'im\b', "0.0*", str_cond_expr)
	str_cond_expr = re.sub(r'\<\<True\>\>', "<<(True)>>", str_cond_expr)
	str_cond_expr = re.sub(r'\<\<False\>\>', "<<(False)>>", str_cond_expr)

	return str_cond_expr

def extract_input_dep(free_syms):
	ret_list = list()
	flist = [str(i) for i in free_syms]
	flist.sort()
	for fsyms in flist:
		ret_list += [str(fsyms), " = ", str(Globals.inputVars[seng.var(fsyms)]["INTV"]), ";"]
	return "".join(ret_list)


def generate_signature(sym_expr, cond_expr, externConstraints, cond_free_symbols, inputStr=None):
	try:
		if(seng.count_ops(sym_expr)==0):
			const_intv = float(str(sym_expr))
			return [const_intv, const_intv]
	except ValueError:
		pass
	inputStr = inputStr if inputStr is not None else \
	            extract_input_dep(list(sym_expr.free_symbols.union(cond_free_symbols)))

	g1 = time.time()

	val = invoke_ibex(sym_expr, cond_expr, externConstraints, inputStr)

	g2 = time.time()
	# print("\tIbex solve = {duration}, opCount = {ops}".format(duration=g2 - g1, ops=seng.count_ops(sym_expr)))
	return val


def statistical_eval(symDict, expr, niters=10000):

	res = 0.0
	maxres = 0.0
	for t in range(niters):
		vecDict = {k:random.uniform(v[0],v[1]) for k, v in symDict.items()}
		val = expr.subs(vecDict) 
		res = res + val  
		maxres = max(val,maxres) 

	return (res/niters, maxres)


# Performs statistical sampling of the symbolic expression
# Used for obtaining statistical profile on error distribution
def get_statistics(sym_expr, inputDict=None):

	try:
		if(seng.count_ops(sym_expr)==0):
			const_val = float(str(sym_expr))
			return (const_val, const_val)
	except ValueError:
		pass

	symDict = inputDict if inputDict is not None else {fsyms : Globals.inputVars[fsyms]["INTV"] for fsyms in sym_expr.free_symbols}
	res_avg_maxres = statistical_eval ( symDict, sym_expr, niters=Globals.argList.samples)
	return res_avg_maxres


def partition(items, predicate):
	a, b = tee((predicate(item), item) for item in items)
	return ((item for pred, item in a if not pred), (item for pred, item in b if pred))


def isConst(obj):
	if type(obj).__name__ == "Num":
		return True
	else:
		return False
			


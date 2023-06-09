from symengine import *
import symengine as seng
import sys
import utils

from gtokens import *
from PredicatedSymbol import Sym, SymTup, SymConcat
import Globals


def bothNotConst(a,b):
	try:
		d1 = float(a)
		d2 = float(b)
		return False
	except:
		pass
	return True


_FOPS = {	PLUS	:	lambda L 	:	L[0] + L[1]	,	\
			MINUS	:	lambda L	:	L[0] - L[1] ,	\
			MUL		:	lambda L	:	L[0] * L[1] ,	\
			DIV		:	lambda L	:	L[0] / L[1] ,	\
			SQRT	:	lambda L	:	L[0].__sqrt__() ,	\
			SIN		:	lambda L	:	L[0].__sin__()	,	\
			ASIN	:	lambda L	:	L[0].__asin__()	,	\
			COS		:	lambda L	:	L[0].__cos__()	,	\
			TAN		:	lambda L	: 	L[0].__tan__()	,	\
			EXP		:	lambda L	:	L[0].__exp__()	\
}


_COPS = {	\
			LT		:	lambda L	:	str("(") + str(L[0]) +" <"+ str(L[1]) + str(")") if bothNotConst(L[0],L[1])	else\
										str("(") + str(L[0] < L[1])+ str(")")	,	\
			LEQ		:	lambda L	:	str("(") + str(L[0]) +"<="+ str(L[1]) + str(")") if bothNotConst(L[0],L[1]) else\
										str("(") + str(L[0] <= L[1]) + str(")")	,	\
			GT		:	lambda L	:	str("(") + str(L[0]) +"> "+ str(L[1]) + str(")") if bothNotConst(L[0],L[1]) else\
										str("(") + str(L[0] > L[1])+ str(")")	, \
			GEQ		:	lambda L	:	str("(") + str(L[0]) +">="+ str(L[1]) + str(")") if bothNotConst(L[0],L[1]) else\
										str("(") + str(L[0] >= L[1]) + str(")")	, \
			EQ		:	lambda L	:	str("(") + str(L[0]) +"=="+ str(L[1]) + str(")") if bothNotConst(L[0],L[1]) else\
										str("(") + str(L[0] == L[1]) + str(")")	, \
			NEQ		:	lambda L	:	str("(") + str(L[0]) +"!="+ str(L[1]) + str(")") if bothNotConst(L[0],L[1]) else\
										str("(") + str(L[0] != L[1]) + str(")")	\
}


# inverted token of _MCOPS
invert = {	\
			LT		:	GEQ 	,\
			GT		:	LEQ	,\
			LEQ		:	GT	,\
			GEQ		:	LT	,\
			EQ		:	NEQ	,\
			NEQ		:	EQ ,\
			AND		:	OR	,\
			OR		:	AND \
}

#L = [f,s,ef,es] Modified _COPS
_MCOPS = {	\
			LT		:	lambda L	:	str("(") + str(L[0]-L[3]) +" <"+ str(L[1]+L[2]) + str(")") if bothNotConst(L[0],L[1])	else\
										str("(") + str(L[0] < L[1])+ str(")")	,	\
			LEQ		:	lambda L	:	str("(") + str(L[0]-L[3]) +"<="+ str(L[1]+L[2]) + str(")") if bothNotConst(L[0],L[1]) else\
										str("(") + str(L[0] <= L[1]) + str(")")	,	\
			GT		:	lambda L	:	str("(") + str(L[0]+L[3]) +"> "+ str(L[1]-L[2]) + str(")") if bothNotConst(L[0],L[1]) else\
										str("(") + str(L[0] > L[1])+ str(")")	, \
			GEQ		:	lambda L	:	str("(") + str(L[0]+L[3]) +">="+ str(L[1]-L[2]) + str(")") if bothNotConst(L[0],L[1]) else\
										str("(") + str(L[0] >= L[1]) + str(")")	, \
			EQ		:	lambda L	:	str("(") + str(L[0]) +"=="+ str(L[1]) + str(")") if bothNotConst(L[0],L[1]) else\
										str("(") + str(L[0] == L[1]) + str(")")	, \
			NEQ		:	lambda L	:	str("(") + str(L[0]) +"!="+ str(L[1]) + str(")") if bothNotConst(L[0],L[1]) else\
										str("(") + str(L[0] != L[1]) + str(")")	\
}


# ops over binary literals
_BOPS = { \
			AND		:	lambda L	:	"<<False>>" if ("False" in L[0] or "False" in L[1]) else "<<True>>" if "True" in L[1] and "True" in L[0] else L[0] if "True" in L[1] else L[1] if "True" in L[0] else   str("(") + L[0] +"&"+ L[1] + str(")"), \
			OR		:	lambda L	:	"<<True>>" if ("True" in L[0] or "True" in L[1]) else "<<False>>" if "False" in L[1] and "False" in L[0] else L[0] if "False" in L[1] else L[1] if "False" in L[0] else str("(") + L[0] +"|"+ L[1] + str(")"), \
			NOT		:	lambda L	:	str("(~(") + L[0] + str("))"),

}

def merge_sets(x, y):
	if isinstance(x, list):
		x = x[0]
	if isinstance(y, list):
		y = y[0]
	if isinstance(x, set) and isinstance(y, set):
		return x | y
	elif isinstance(x, set) and isinstance(y, str):
		return x | {y}
	elif isinstance(x, str) and isinstance(y, set):
		return {x} | y
	else:
		return {x, y}

_BOPS2 = { \
			AND: lambda L:	"<<False>>" if ("False" in L[0] or "False" in L[1]) else "<<True>>" if "True" in L[1] and "True" in L[0] else L[0] if "True" in L[1] else L[1] if "True" in L[0] \
				else [[merge_sets(x, y)] for x in L[1] for y in L[0]] if isinstance(L[1], list) and isinstance(L[0], list) \
			    else [[merge_sets(x, L[0])] for x in L[1]] if isinstance(L[1], list) \
			    else [[merge_sets(x, L[1])] for x in L[0]] if isinstance(L[0], list) \
			    else [[merge_sets(L[0], L[1])]],
			OR: lambda L:	"<<True>>" if ("True" in L[0] or "True" in L[1]) else "<<False>>" if "False" in L[1] and "False" in L[0] else L[0] if "False" in L[1] else L[1] if "False" in L[0] \
				else L[0] + L[1] if isinstance(L[0], list) and isinstance(L[1], list) \
			    else L[0] + [[L[1]]] if isinstance(L[0], list) \
			    else L[1] + [[L[0]]] if isinstance(L[1], list) \
			    else [[L[0]], [L[1]]],
}


DFOPS_LIST = [PLUS, MINUS, MUL, DIV, SQRT, EXP, SIN, ASIN, COS, TAN, IF]

# derivatives
_DFOPS = { \
			PLUS	:	[lambda L : SymTup((Sym(1.0,Globals.__T__),)), \
			             lambda L : SymTup((Sym(1.0,Globals.__T__),))],\
			MINUS	:	[lambda L : SymTup((Sym(1.0,Globals.__T__),)), \
			             lambda L : SymTup((Sym(-1.0,Globals.__T__),))],\
			MUL		:	[lambda L : L[1], lambda L : L[0]]	,\
			DIV		:	[lambda L : SymTup((Sym(1.0, Globals.__T__),))/L[1], \
						 lambda L : (SymTup((Sym(-1.0, Globals.__T__),))*L[0])/(L[1].__pow__(2))], \
			SQRT	:	[lambda L : SymTup((Sym(-0.5, Globals.__T__),))/(L[0].__sqrt__())], \
			EXP		:	[lambda L : L[0]], \
			SIN		:	[lambda L : L[0].__cos__()], \
			ASIN	:	[lambda L : SymTup((Sym(1.0,Globals.__T__),)) / \
									(SymTup((Sym(1.0,Globals.__T__),)) - (L[0].__pow__(2))).__sqrt__()], \
			COS		:	[lambda L : (L[0].__sin__())*(-1.0)], \
			#TAN		:	[lambda L : L[0].__cos__()/L[0].__sin__()] \
			TAN		:	[lambda L : SymTup((Sym(1.0,Globals.__T__),))/L[0].__tan__()] \
}


_Priority = { \
				IF		:	0,	\
				SIN		:	0,	\
				ASIN	:	0,	\
				COS		:	0,	\
				TAN		:	0,	\
				PLUS	:	0,	\
				MUL		:	0,	\
				MINUS	:	0,	\
				DIV		:	0,	\
				SQRT	:	0,	\
				EXP		:	0	\
}


## make the case here for optimally finding out
## case where the error can be removed when the
## exactness is known
## difficult to do it optimally
## specially whendealing with intervals

_ALLOC_ULP = { PLUS  : 1.0, \
			   MINUS : 1.0, \
			   MUL   : 1.0, \
			   DIV   : 2.0, \
			   SQRT  : 1.0, \
			   SIN	 : 2, \
			   COS	 : 2, \
			   TAN	 : 2, \
			   COT	 : 2, \
			   COSH	 : 2, \
			   SINH	 : 2, \
			   LOG	 : 2, \
			   EXP	 : 2, \
			   IDEN  : 0, \
			   ID	 : 0
			  }


# use  const selectively where the operand mantissa is 0
_FP_RND = {
			"rnd16"  :  pow(2,-8+53), \
			"rnd32"  :  pow(2,-24+53), \
			"rnd64"  :  1.00, \
			"fl16"   :  pow(2,-8+53), \
			"fl32"   :  pow(2,-24+53), \
			"fl64"   :  1.00, \
			"const"  :  0.00, \
			"int"	 :  0.00
		}


opMax = 2000
SopMax = 0

def solve_remaining_error(errList):
	#expr = sum([seng.Abs(erri) for erri in errList])
	if type(errList).__name__ == 'list':
		expr = sum([seng.Abs(erri) for erri in errList])
	else:
		expr = errList

	return max(utils.generate_signature(expr))

def solve_remaining_error2(errList):
	#expr = sum([seng.Abs(erri) for erri in errList])
	if type(errList).__name__ == 'list':
		expr = sum([seng.Abs(erri) for erri in errList])
	else:
		expr = errList

	return max(utils.generate_signature_herror(expr))


# DIV is more complicated
# step-1 : INV
# step-2 : MUL


def _partial_solve_(errList):
	
	expr = sum([seng.Abs(erri) for erri in errList])
	expr_ops = seng.count_ops(expr)
	print("New partial:", expr_ops)
	size = len(errList)
	if size == 1 or expr_ops < SopMax:
		print("Unit level calls", size)
		#print(expr)
		val =  max(utils.generate_signature_herror(expr))
		print("VAL : ", val)
		return val
	else:
		print("**************", size, expr_ops)
		return _partial_solve_(errList[0:int(size/2)]) + _partial_solve_(errList[int(size/2):size])

def _solve1_(node, errList1, errList2, herr):

	expr1 = sum([seng.Abs(erri) for erri in errList1])
	expr2 = sum([seng.Abs(erri) for erri in errList2])+herr*pow(2,-53)

	print("\nSolving f@depth :", node.depth)
	errList1 = [solve_remaining_error(expr1)]

	expr2_ops = seng.count_ops(expr2)
	print("Solving h@depth :", expr2,  node.depth)
	errList2 = [solve_remaining_error(expr2)]
	
	return [errList1, errList2]


def _solve_(node, errList1, errList2, herr):

	errList2.append(herr*pow(2,-53))
	expr1 = sum([seng.Abs(erri) for erri in errList1])
	expr2 = sum([seng.Abs(erri) for erri in errList2])

	if(seng.count_ops(expr1) >= opMax):
		print("\nSolving f@depth :", node.depth)
		errList1 = [solve_remaining_error(expr1)]

	expr2_ops = seng.count_ops(expr2)

	if expr2_ops >= SopMax:
		print("\nSolving", expr2_ops, " h@depth :", node.depth)
		errList2 = [_partial_solve_(errList2)]
	else:
		print("bwahahaha!", expr2_ops, expr2, SopMax)

	return [errList1, errList2]


def _HSIN_(node, S1, S2):
	f = node.children[0].f_expression

	errList1 = [node.f_expression] + \
			   [seng.Abs(Si*seng.cos(f)) for Si in S1]

	errList2 = [seng.Abs(Si.seng.cos(f)) for Si in S2]

	herr = seng.Abs(seng.sin(f + sum([seng.Abs(Si*pow(2,-53)) for Si in S1+S2])) * sum([seng.Abs(Si*Sj) for Si in S1+S2 for Sj in S1+S2]))

	return _solve_(node, errList1, errList2, herr)



def _HLOG_(node, S1, S2):
	f = node.children[0].f_expression

	errList1 = [node.f_expression] + \
			   [Si/f for Si in S1]

	errList2 = [Si/f for Si in S2]

	hdenorm = (node.f_expression + 0.5*sum([seng.Abs(Si*pow(2,-53)) for Si in S1+S2]))**2

	herr = sum([seng.Abs(Si*Sj) for Si in S for Sj in S])/hdenorm

	return _solve_(node, errList1, errList2, herr)



def _HEXP_(node, S1, S2):
	f = node.children[0].f_expression

	errList1 = [node.f_expression] + \
			   [seng.expand(Si*node.f_expression) for Si in S1]
	errList2 = [seng.expand(Si*node.f_expression) for Si in S2]

	ferr = sum([seng.Abs(Si*pow(2, -53) ) for Si in S1+S2]) + node.f_expression
	herr = sum([seng.Abs(Si* Sj*seng.exp(ferr)) for Si in S1+S2 for Sj in S1+S2])

	return _solve_(node, errList1, errList2, herr)
	


def _HSQRT_(node, S1, S2):
	f = node.children[0].f_expression

	S1 = [solve_remaining_error(S1)]
	S2 = [solve_remaining_error2(S2)]

	errList1 = [node.f_expression] + \
			   [Si/(2*node.f_expression) for Si in S1]

	errList2 = [Si/(2*node.f_expression) for Si in S2]

	herr_denorm = (f + sum([seng.Abs(Si*pow(2,-53)) for Si in S1+S2]))**(3.0/2)
	
	herr = 0.125 * sum([seng.Abs(Si * Sj)/herr_denorm for Si in S1+S2 for Sj in S1+S2])

	return _solve_(node, errList1, errList2, herr)


# do not expand in the denoms -- problems with the optimizer

def _HINV_(node, S1, S2):
	f = node.f_expression
	inv_expr = 1.0/f ;

	S1 = [solve_remaining_error(S1)]
	S2 = [solve_remaining_error(S2)]

	errList1 = [inv_expr] + [-Si/(f*f) for Si in S1]
	errList2 = [-Si/(f*f) for Si in S2]

	herr_denorm = (f + sum([seng.Abs(Si*pow(2,-53)) for Si in S1+S2]))**3

	herr = sum([seng.Abs(Si * Sj)/herr_denorm for Si in S1+S2 for Sj in S1+S2])

	return _solve_(node, errList1, errList2, herr)

def _HDIV_(node, S1, S2, T1, T2):

	[TerrList1, TerrList2] = _HINV_(node.children[1], T1, T2)
	f = node.children[0].f_expression
	g = (1/node.children[1].f_expression)

	errList1 = [node.f_expression] + \
			   [seng.expand(f * Ti) for Ti in TerrList1] + \
			   [seng.expand(g * Si) for Si in S1] 

	errList2 = [seng.expand(f * Ti) for Ti in TerrList2] + \
			   [seng.expand(g * Si) for Si in S2] 

	herr = sum([seng.Abs(Si * Tj) for Si in S1+S2 for Tj in TerrList1+TerrList2])
	return _solve_(node, errList1, errList2, herr)



def _HMUL_(node, S1, S2, T1, T2):

	f = node.children[0].f_expression
	g = node.children[1].f_expression
	
	errList1 = [node.f_expression] + \
			   [seng.expand( g * Si) for Si in S1] + \
			   [seng.expand( f * Tj) for Tj in T1]

	errList2 = [seng.expand( g * Si) for Si in S2] + \
			   [seng.expand( f * Tj) for Tj in T2]

	herr = sum([seng.Abs(seng.expand(Si * Tj)) for Si in S1+S2 for Tj in T1+T2])

	return _solve_(node, errList1, errList2, herr)




def _HADD_(node, S1, S2, T1, T2):
	f = node.children[0].f_expression
	g = node.children[1].f_expression

	errList1 = [node.f_expression] + S1 + T1
	errList2 = S2 + T2

	herr = sum([seng.Abs(Si) for Si in S1+S2+T1+T2])

	return _solve_(node, errList1, errList2, herr)

def _HMINUS_(node, S1, S2, T1, T2):
	f = node.children[0].f_expression
	g = node.children[1].f_expression

	errList1 = [node.f_expression] + S1 + [-t for t in T1]
	errList2 = S2 + [-t for t in T2]

	herr = sum([seng.Abs(Si) for Si in S1+S2+T1+T2])
	return _solve_(node, errList1, errList2, herr)



def HComposeBin(node, S1, S2, T1, T2):
	if node.token.type == MUL:
		return _HMUL_(node, S1, S2, T1, T2)
	elif node.token.type == MINUS:
		return _HMINUS_(node, S1, S2, T1, T2)
	elif node.token.type == PLUS:
		return _HADD_(node, S1, S2, T1, T2)
	elif node.token.type == DIV:
		return _HDIV_(node, S1, S2, T1, T2)
	else:
		print("Required support  for token :", node.token.type)
		sys.exit()


def HComposeTrans(node, S1, S2):
	if node.token.type == SQRT:
		return _HSQRT_(node, S1, S2)
	elif node.token.type == EXP:
		return _HEXP_(node, S1, S2)
	elif node.token.type == LOG:
		return _HLOG_(node, S1, S2)
	elif node.token.type == SIN:
		return _HSIN_(node, S1, S2)
	else:
		print("Required support for token :", node.token.type)
		sys.exit()


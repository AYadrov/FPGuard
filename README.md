# FPGuard
Efficiently Guarding Floating-Point Error Optimizations Through Domain Checks

## Abstract:

*Estimating worst-case roundoff errors is a crucial step in floating-point program analysis and verification. Successful tools in this area are based on symbolic automatic differentiation (to discover the error expressions) followed by maximizing these error expressions on the input domain. Unfortunately, this process has not been robustly supported in existing tools (including our own past tool Satire which scales to millions of operator nodes, and hence is the leading tool in this area, with prior tools handling at most 200 operators before timing out). The main problem these tools run into is due to singularities in the denominator expressions, sending the expression to infinity. By employing random floating-point generation, we discover the extent of this defect in Satire and then resort to a series of techniques that “guard” the input domain through constraints that avoid the singularities. Ours is the first serious study of this problem, and a set of novel solutions that makes Satire more robust, with our techniques general enough to apply to other similar tools in this area. The new tool FPGuard produces tighter bounds, fewer crashes, and runs faster.*

## Algorithm 

FPGuard is based on previous works called Seesaw and Satire and preserves its work flow path of modeling the given straight-line program as a computational
graph. Afterwards, it obtains error expressions and checks for a possible domain-error using `RIVAL`. `RIVAL` detects cases where: all domain points induce an infinity error (analysis terminates), no domain-point induces an error (directly invoke the optimizer), or some domain-points can cause error (obtain constraints using `SymPy`). Obtained constraints, given constraints, error expressions are put into `IbexOpt` (a end-user program that solves a standard NLP problem) in order to obtain worst case error. This result is reported to the user with obtained constraints.

## Building

### Docker

Here is a simple example how to launch a docker container with FPGuard.

1) Download Dockerfile and open terminal where Dockerfile is stored
1) `sudo docker build -t fpguard_image .`
2) `sudo docker container create -i -t --name fpguard_container fpguard_image`
3) `sudo docker container start -i fpguard_container`

### Manual installation

FPGuard requires the following dependencies to be installed:

* Requirements:
	* python > 3.6
	* libmpfr-dev package
	* python packages using pip3
		* [sly](https://github.com/dabeaz/sly) > 0.3
		* [pyinterval](https://pypi.org/project/pyinterval/) >= 1.2.0
		* [numpy](https://numpy.org/) >= 1.24.3
		* [symengine](https://github.com/symengine/symengine) > 0.5.1
		* [sympy](https://www.sympy.org/en/index.html) > 1.4
		* [bigfloat](https://pypi.org/project/bigfloat) > 0.4.0

In addition, FPGuard requires `IbexOpt` to be installed. Please, follow the instructions that can be found in [ibex-lib repository](https://github.com/ibex-team/ibex-lib).

Before launching, make sure that you added environmental variable `SAT_ROOT=[...]/FPGuard`.

## Usage

FPGuard is a python based framework. The main function is in `src/fpguard.py` The `--help` command clarifies all the supporting arguments.

### Example 1

Basically this examples preserve the same flow as Seesaw.

Example for launching FPGuard for DistSinusoid benchmark with stdout output, enabling constraints processing:
```sh
python3 fpguard.py --std --enable-constr --file /home/FPGuard/Benchmarks/DistSinusoid/SAT/distsinusoid.txt
```
Output:
```
LEVEL_TOP: Optimizer cells : 40888
LEVEL_TOP: Parsing time : 0.003155231475830078
LEVEL_TOP: Analysis time : 19.10873246192932
LEVEL_TOP: Full_time : 19.113666772842407
LEVEL_TOP: ABSOLUTE_ERROR : inf
```
Where `Optimizer cells` is a number of IbexOpt cells, `ABSOLUTE_ERROR` is a worst-case absolute error that the given input program can produce.

### Example 2
Example for launching FPGuard for DistSinusoid benchmark with stdout output, enabling constraints processing, enabling domain checks:
```sh
python3 fpguard.py --std --domain-checks --enable-constr --file /home/FPGuard/Benchmarks/DistSinusoid/SAT/distsinusoid.txt
```
Output:
```
LEVEL_TOP: Optimizer cells : 35714
LEVEL_TOP: Parsing time : 0.00328826904296875
LEVEL_TOP: Analysis time : 30.203452110290527
LEVEL_TOP: Full_time : 30.20847463607788
LEVEL_TOP: ABSOLUTE_ERROR : 1.6964889994364185e-15
LEVEL_TOP: Domain check found these constraints to avoid infinity:
	 ((k1 - (k2 + 1.75193839388411) + 0.001 <= 0)||(-1.0 * (k1 - (k2 + 1.75193839388411)) + 0.001 <= 0));
	 ((k2 - (1.0) + 0.001 <= 0)||(-1.0 * (k2 - (1.0)) + 0.001 <= 0));
	 ((k2 - (k1 - 1.75193839388411) + 0.001 <= 0)||(-1.0 * (k2 - (k1 - 1.75193839388411)) + 0.001 <= 0));
	 ((k1 - (0.0) + 0.001 <= 0)||(-1.0 * (k1 - (0.0)) + 0.001 <= 0));
```
### Example 3
Example for launching FPGuard for one test from 1000 stress-tests with domain checks:
```sh
python3 fpguard.py --std --domain-checks --enable-constr --file /home/FPGuard/Benchmarks/1000tests/test5.txt
```
Output:
```
LEVEL_TOP: Optimizer cells : 91814
LEVEL_TOP: Parsing time : 0.001889944076538086
LEVEL_TOP: Analysis time : 71.24317216873169
LEVEL_TOP: Full_time : 71.24700140953064
LEVEL_TOP: ABSOLUTE_ERROR : 13985600787247.42
LEVEL_TOP: Domain check found these constraints to avoid infinity:
	 ((var_9 - (5.98121897242658e-72*(-1.0e+35*var_7 - 1.0e+20)/var_8) + 0.1 <= 0)||(-1.0 * (var_9 - (5.98121897242658e-72*(-1.0e+35*var_7 - 1.0e+20)/var_8)) + 0.1 <= 0));
	 ((var_8 - (1.41494985606667e-73*(-4.22715967409148e+36*var_7 - 4.22715967409148e+21)/var_9) + 0.1 <= 0)||(-1.0 * (var_8 - (1.41494985606667e-73*(-4.22715967409148e+36*var_7 - 4.22715967409148e+21)/var_9)) + 0.1 <= 0));
	 ((var_9 - (1.41494985606667e-73*(-4.22715967409148e+36*var_7 - 4.22715967409148e+21)/var_8) + 0.1 <= 0)||(-1.0 * (var_9 - (1.41494985606667e-73*(-4.22715967409148e+36*var_7 - 4.22715967409148e+21)/var_8)) + 0.1 <= 0));
	 ((var_8 - (5.98121897242658e-72*(-1.0e+35*var_7 - 1.0e+20)/var_9) + 0.1 <= 0)||(-1.0 * (var_8 - (5.98121897242658e-72*(-1.0e+35*var_7 - 1.0e+20)/var_9)) + 0.1 <= 0));
	 ((var_7 - (-1.6719e+36*var_8*var_9 - 1.0e-15) + 0.1 <= 0)||(-1.0 * (var_7 - (-1.6719e+36*var_8*var_9 - 1.0e-15)) + 0.1 <= 0));
```

## References

> **Satire: An Abstraction-guided Approach to Scalable and Rigorous Floating-Point Error Analysis** [[Project]](https://github.com/arnabd88/Satire) [[arXiv]](https://arxiv.org/abs/2004.11960)   
> *Arnab Das, Ian Briggs, Ganesh Gopalakrishnan, Pavel Panchekha, Sriram Krishnamoorthy*

> **Seesaw: Robustness Analysis of Loop-Free Floating-Point Programs via Symbolic Automatic Differentiation** [[Project]](https://github.com/arnabd88/Seesaw) [[IEEE]](https://ieeexplore.ieee.org/document/9556024)
> *Arnab Das, Tanmay Tirpankar, Ganesh Gopalakrishnan, Sriram Krishnamoorthy*   

> **Rival: Interval Arithmetic for Real Computation** [[Project]](https://github.com/herbie-fp/rival) [[arXiv]](https://arxiv.org/abs/2107.05784)   
> *Oliver Flatt, Pavel Panchekha*   

> **IbexOpt: Upper bounding in inner regions for global optimization under inequality constraints** [[Project]](https://github.com/ibex-team/ibex-lib) [[Springer]](https://link.springer.com/article/10.1007/s10898-014-0145-7)  
> *Ignacio Araya, Gilles Trombettoni, Bertrand Neveu, Gilles Chabert*    



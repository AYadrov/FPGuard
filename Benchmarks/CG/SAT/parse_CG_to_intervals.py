import re

with open("eps_CG_arc_noErr_K5_N130_E0.0.txt", 'r') as f:
    out = ""
    pattern = re.compile(r".*\([-?0-9.0-9]|[-?0-9e].*,.*[-?0-9.0-9]|[-?0-9e]\).*")
    for line in f:
        z = pattern.match(line)
        if z:
            line = re.sub(r"[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?\)",
                          str(float(re.findall(r"\((-?\d+\.\d+(e-?\d+)?)", line)[0][0]) + 1) + ')', line)
            out += line
        else:
            out += line
    o = open("CG_intervals.txt", "w")
    o.write(out)
    o.close()
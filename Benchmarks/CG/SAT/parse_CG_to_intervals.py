import re

with open("CG_3iterations.txt", 'r') as f:
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
    o = open("CG_3iterations_intervals.txt", "w")
    o.write(out)
    o.close()
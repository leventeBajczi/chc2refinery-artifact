#!/usr/bin/env python3
import smtlib
import sys

# validate-model.py [--equations] BENCHMARK < MODEL: the query whose unsatisfiability shows that MODEL satisfies the
# clauses of BENCHMARK. With --equations, recursive definitions become their equations (see recursive_definitions).
equations = "--equations" in sys.argv[1:]
chc_file = [arg for arg in sys.argv[1:] if arg != "--equations"][0]
assert chc_file.endswith(".smt2")

smt_file = chc_file[:-4] + "-validate.smt2"

funs = {}
# Models that need auxiliary declarations and definitions (e.g., the finite models of Refinery, whose
# predicates are conditions on a recursive map from values to the states of a datatype): these
# commands are kept, in their order, before the definitions of the predicates.
AUXILIARY = ("declare-datatypes", "declare-datatype", "declare-sort", "define-sort", "define-fun",
             "define-fun-rec", "define-funs-rec")
model_cmds = []


def define_funs(cmds, funs):
    for cmd in cmds:
        match cmd:
            case ("define-fun", name, *args):
                funs[name] = cmd


if True:
    file = sys.stdin
    for line in file:
        if line.strip() == "sat":
            break
    else:
        raise ValueError("No line with 'sat' found")
    content = file.read()
    if "WARNING: YOUR LOGFILE WAS TOO LONG, SOME LINES IN THE MIDDLE WERE REMOVED." in content:
        sys.exit("validate-model.py: BenchExec cut the model out of the log file (it was too long)")
    model = smtlib.parse_exprs(content)

    match model:
        # SMT-LIB standard
        case [("model", *cmds)]:
            define_funs(cmds, funs)
        # Eldarica
        case [("define-fun", *_), *_] as cmds:
            define_funs(cmds, funs)
        # Auxiliary declarations first (Refinery)
        case [(("declare-datatypes" | "declare-datatype" | "declare-sort" | "define-sort" | "define-fun-rec"
                | "define-funs-rec"), *_), *_] as cmds:
            define_funs(cmds, funs)
            model_cmds = cmds
        # Z3
        case [cmds]:
            define_funs(cmds, funs)

with open(chc_file, "r") as file:
    content = file.read()
    cmds = smtlib.parse_exprs(content)

predicates = {cmd[1] for cmd in cmds if isinstance(cmd, tuple) and cmd[:1] == ("declare-fun",)}
auxiliary = [cmd for cmd in model_cmds if isinstance(cmd, tuple) and cmd and cmd[0] in AUXILIARY
             and not (cmd[0] == "define-fun" and cmd[1] in predicates)]

defs = []
clauses = []

for cmd in cmds:
    match cmd:
        case ("set-logic", "HORN"):
            defs.append(("set-logic", "ALL"))

        case ("set-option", ":produce-models", "true"):
            pass

        case ("declare-fun", name, *args):
            defs += auxiliary       # once, before the first predicate
            auxiliary = []
            defs.append(funs[name])

        case ("assert", phi):
            clauses.append(phi)

        case ("check-sat",):
            pass
        case ("get-model",):
            pass
        case ("exit",):
            pass

        case _:
            defs.append(cmd)

def recursive_definitions(cmd):
    """A define-fun-rec or define-funs-rec command as SMT-LIB 2.6 defines its meaning: the declarations of the
    functions and, for all arguments, the equations that define them (with the applications as patterns).
    With the recursive definition of the map h from values to states of a finite model (Refinery's), solvers
    time out on clauses that hold whatever state h gives to a variable; from the equations, they instantiate h
    at the terms of the clause and reason about its states (and time out on others)."""
    if not equations:
        return [cmd]
    match cmd:
        case ("define-fun-rec", name, params, sort, body):
            definitions = [((name, params, sort), body)]
        case ("define-funs-rec", declarations, bodies):
            definitions = list(zip(declarations, bodies))
        case _:
            return [cmd]
    commands = [("declare-fun", name, tuple(s for _, s in params), sort) for (name, params, sort), _ in definitions]
    for (name, params, sort), body in definitions:
        application = (name, *(p for p, _ in params)) if params else name
        equation = ("=", application, body)
        commands.append(("assert", ("forall", params, ("!", equation, ":pattern", (application,)))
                                   if params else equation))
    return commands


for cmd in [c for d in defs for c in recursive_definitions(d)]:
    for line in smtlib.print_expr_non_recursive(cmd):
        print(line)

goal = ("assert", ("not", ("and", *clauses)))

for line in smtlib.print_expr(goal):
    print(line)

print("(set-info :status unsat)")
print("(check-sat)")

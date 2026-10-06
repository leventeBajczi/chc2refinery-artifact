#!/usr/bin/env python3
import smtlib
import sys

chc_file = sys.argv[1]
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

for cmd in defs:
    for line in smtlib.print_expr_non_recursive(cmd):
        print(line)

goal = ("assert", ("not", ("and", *clauses)))

for line in smtlib.print_expr(goal):
    print(line)

print("(set-info :status unsat)")
print("(check-sat)")

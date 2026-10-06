#!/bin/bash
# check-model.sh LOG BENCHMARK [--memory KB] SOLVER...: check the model in the log file LOG of a model run (after
# BenchExec's header) against BENCHMARK with the command SOLVER..., which reads the SMT-LIB file given as its last
# argument. The query (validate-model.py) is unsat if the model satisfies the clauses. A model with recursive
# definitions (Refinery's) is first checked for at most 45 s with the definitions as their equations
# (validate-model.py --equations), within KB kilobytes of virtual memory if given (a solver that instantiates
# the equations can outgrow the memory limit of the run; a JVM limits its heap itself, and does not start under
# such a limit); the equations only confirm a model, if the solver answers unsat. Then it is checked as it is.
here=$(dirname "$0"); log=$1; benchmark=$2; shift 2
memory=unlimited
if [ "$1" = "--memory" ]; then memory=$2; shift 2; fi
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
tail -n +7 "$log" > "$work/model"
"$here/validate-model.py" "$benchmark" < "$work/model" > "$work/query.smt2" || exit 1
if grep -q '^(define-funs\?-rec' "$work/model" &&
        "$here/validate-model.py" --equations "$benchmark" < "$work/model" > "$work/equations.smt2"; then
    if (ulimit -v "$memory"; timeout 45 "$@" "$work/equations.smt2" 2>&1) | grep -qx unsat; then
        echo "unsat"
        exit 0
    fi
fi
"$@" "$work/query.smt2"

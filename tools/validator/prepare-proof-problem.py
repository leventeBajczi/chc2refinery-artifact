#!/usr/bin/env python3
"""Prepare a CHC-COMP benchmark for Carcara, which checks Alethe proofs against it.

Two changes keep the assertions as they are:
* (set-logic HORN) becomes (set-logic ALL): Carcara reads numerals as reals in a logic whose name contains R but
  not I, which HORN does;
* symbols that are not simple symbols of SMT-LIB are quoted: some benchmarks name predicates f$unknown:23, which Z3
  accepts but Carcara splits at the colon (|f$unknown:23| is the same symbol).

Usage: prepare-proof-problem.py BENCHMARK.smt2 > PROBLEM.smt2
"""
import re
import sys

SIMPLE = re.compile(r'[A-Za-z~!@$%^&*_\-+=<>.?/][A-Za-z0-9~!@$%^&*_\-+=<>.?/]*')
TOKEN = re.compile(r'\s+|;[^\n]*|"(?:[^"]|"")*"|\|[^|]*\||[()]|[^\s()|";]+')


def prepare(text: str) -> str:
    out = []
    for token in TOKEN.findall(text):
        if token[0] in ' \t\r\n;"|()' or token.startswith(':') or SIMPLE.fullmatch(token) \
                or re.fullmatch(r'\d+(\.\d+)?|#b[01]+|#x[0-9a-fA-F]+', token):
            out.append(token)
        else:
            out.append(f'|{token}|')
    return re.sub(r'\(\s*set-logic\s+HORN\s*\)', '(set-logic ALL)', ''.join(out))


if __name__ == '__main__':
    with open(sys.argv[1]) as f:
        sys.stdout.write(prepare(f.read()))

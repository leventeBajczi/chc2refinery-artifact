# This file is part of BenchExec, a framework for reliable benchmarking:
# https://github.com/sosy-lab/benchexec
#
# SPDX-FileCopyrightText: 2007-2020 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0

import benchexec.tools.chc


class Tool(benchexec.tools.chc.ChcTool):
    """
    Tool info for RInGen (https://github.com/Columpio/RInGen), the regular invariant generator for
    CHCs over algebraic datatypes, with the CHC-COMP fork of Vampire as its backend.
    """

    REQUIRED_PATHS = [
        "ringen-chc",
        "publish",
        "vampire",
        "time",
        "VERSION",
    ]

    def executable(self, tool_locator):
        return tool_locator.find_executable("ringen-chc")

    def version(self, executable):
        return self._version_from_tool(executable, "--version")

    def name(self):
        return "RInGen"

    def cmdline(self, executable, options, task, rlimits):
        # RInGen stops at its own time limit (300 s by default): give it the CPU time of the run.
        limit = rlimits.cputime or rlimits.walltime
        timelimit = [f"--timelimit={limit}"] if limit else []
        return [executable, *timelimit, *options, *task.input_files_or_identifier]

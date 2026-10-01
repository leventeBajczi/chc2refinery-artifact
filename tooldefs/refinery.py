# This file is part of BenchExec, a framework for reliable benchmarking:
# https://github.com/sosy-lab/benchexec
#
# SPDX-FileCopyrightText: 2007-2020 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0

import benchexec.tools.chc


class Tool(benchexec.tools.chc.ChcTool):
    """
    Tool info for Refinery with the chc2refinery translation
    (https://github.com/leventeBajczi/chc2refinery).
    """

    REQUIRED_PATHS = [
        "refinery-chc",
        "chc2refinery.py",
        "VERSION",
        "jdk",
        "refinery-generator-cli",
    ]

    def executable(self, tool_locator):
        return tool_locator.find_executable("refinery-chc")

    def version(self, executable):
        return self._version_from_tool(executable, "--version")

    def name(self):
        return "Refinery"

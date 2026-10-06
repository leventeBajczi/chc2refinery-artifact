import benchexec.result as result
import benchexec.tools.chc


class Tool(benchexec.tools.chc.ChcTool):
    """
    Tool info for chc-proof-validate: Carcara (https://github.com/ufmg-smite/carcara) checks the Alethe proof
    of unsatisfiability in the log file of a proof verifier against the benchmark (validate.sh).
    A valid proof confirms unsat; an invalid one refutes it; a missing proof leaves the result unknown.
    """

    REQUIRED_PATHS = [
        "validate.sh",
        "carcara",
    ]

    def determine_result(self, run):
        status = None

        for line in run.output:
            line = line.strip()
            if line == "valid":
                status = result.RESULT_FALSE_PROP
            elif line == "invalid":
                status = result.RESULT_TRUE_PROP

        if not status:
            status = result.RESULT_UNKNOWN

        return status

    def cmdline(self, executable, options, task, rlimits):
        return [executable] + options + [task.single_input_file]

    def executable(self, tool_locator):
        return tool_locator.find_executable("validate.sh")

    def name(self):
        return "chc-proof-validate"

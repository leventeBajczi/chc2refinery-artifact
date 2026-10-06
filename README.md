# CHC-COMP Model Validation

## Refinery

This fork adds one solver to the CHC-COMP 2026 setup: the [Refinery](https://refinery.tools/)
graph solver, driven by [chc2refinery](https://github.com/leventeBajczi/chc2refinery), a single
command that proves CHC problems with Refinery in two modes, which run in parallel (the first
verdict stops the other):

* `--prove-unsat`: a model of the generated Refinery problem is a derivation of `false`, so the
  answer is `unsat` when Refinery finds one, and `sat` when Refinery shows that none exists and
  the encoding is exact (no derivation was excluded for using a value that SMT-LIB leaves
  unspecified);
* `--prove-sat`: a model is a finite model of the clauses over algebraic datatypes (a tree
  automaton), so the answer is `sat`; problems with other sorts are refused.

The answer is `unknown` if neither mode decides (e.g., for unsupported features).

* `make tools/refinery` builds the tool: Refinery at a fixed commit with chc2refinery's two
  patches, [`refinery.patch`](https://github.com/leventeBajczi/chc2refinery/blob/main/patches/refinery.patch)
  (fixes) and [`refinery-bv-fp.patch`](https://github.com/leventeBajczi/chc2refinery/blob/main/patches/refinery-bv-fp.patch)
  (bit-vector and floating-point attributes), built with Gradle (this needs network access to
  Maven Central); chc2refinery at a fixed commit; a JDK 25 to run on; and Z3's Python package
  (installed with pip into `tools/refinery/python`), which only the proofs of the proof track use.
  The tool does not check its answers with Z3 (chc2refinery's `--check`).
* [`wrappers/refinery-chc`](wrappers/refinery-chc) runs `chc2refinery.py` with the bundled
  Refinery; the first line of its output is the verdict, followed by the witness (the derivation,
  or the finite model). Options, e.g., `--prove-unsat` to run one mode only, are passed on.
  [`tooldefs/refinery.py`](tooldefs/refinery.py) is its BenchExec tool definition.
* [`benchmark-defs/refinery.xml.template`](benchmark-defs/refinery.xml.template) enters all nine
  categories of the solver track, with the competition's limits.
* [`benchmark-defs/refinery-model.xml.template`](benchmark-defs/refinery-model.xml.template) enters
  the model track in ADT-LIA only, with `--prove-sat`: only the finite-model search, whose `sat`
  answers come with a model. That search refuses sorts other than datatypes and Booleans
  (integers, reals, bit-vectors, arrays), so the other categories, including ADT-LIA-Arrays, would
  only get refusals, and a `sat` from an exhausted counterexample search has no model.
* A model of `--prove-sat` is a tree automaton: a datatype of states, the transition functions, a
  recursive map `h` from values to states (`define-funs-rec`), and every predicate as a condition
  on `h`. [`tools/validator/validate-model.py`](tools/validator/validate-model.py) used to keep
  only the definitions of the predicates, so it now also keeps the auxiliary declarations and
  definitions of a model that starts with them, in their order, before the predicates. The output
  for the models of the other solvers (`(model ...)`, Eldarica's and Z3's formats) is unchanged.
  Validators still have to reason about the recursive `h`: Z3 confirms simple models (parity) but
  answers `unknown` for others (`x < y` on Peano numbers), which `chc2refinery.py --check` proves
  with induction lemmas.
* [`benchmark-defs/refinery-proof.xml.template`](benchmark-defs/refinery-proof.xml.template) adds a
  **proof track**, in which only Refinery takes part: on the unsatisfiable benchmarks of LIA-Lin,
  LIA and LRA-Lin, it runs `--prove-unsat --unsat-alethe`, which prints an
  [Alethe](https://verit.gitlabpages.uliege.be/alethe/specification.pdf) proof after `unsat`.
  Z3 re-solves the derivation over the original clauses for exact values; the proof instantiates
  the clauses with them and evaluates their constraints with the simplification rules of Alethe
  (see chc2refinery's README). Proofs cover clauses over Booleans, integers and reals; for others
  (`mod`, `div` with a remainder, `to_real`), `unsat` comes without a proof, which counts as
  unconfirmed.
* [`benchmark-defs/carcara-proof-validation.xml.template`](benchmark-defs/carcara-proof-validation.xml.template)
  checks the proofs with [Carcara](https://github.com/ufmg-smite/carcara) 1.1.0 (`make tools/carcara`
  builds it with cargo), with [`tooldefs/chc-proof-validate.py`](tooldefs/chc-proof-validate.py):
  `valid` confirms the answer and `invalid` refutes it. Its `validate.sh` takes the proof after the
  `unsat` line of the log file, and prepares the benchmark with
  [`tools/validator/prepare-proof-problem.py`](tools/validator/prepare-proof-problem.py), which keeps
  the assertions as they are: `(set-logic HORN)` becomes `(set-logic ALL)`, since Carcara reads
  numerals as reals in a logic whose name contains R but not I, and symbols that are not simple
  symbols of SMT-LIB are quoted (hopv names predicates `f$unknown:23`, which Carcara splits at the
  colon). Carcara runs with `--expand-let-bindings`, since the proofs are let-free.
  An `unsat` counts in the proof track only with a valid proof (`validate.py`, as for models).

### Running only Refinery

The 2026 results of the other solvers are [published](https://doi.org/10.5281/zenodo.20413019),
so a run of Refinery alone is enough to compare against them:

```bash
make download-refinery                    # benchexec, the benchmarks, and tools/refinery only
make download-results-2026                # the published 2026 results, into results/
make setup-benchmark                      # or: make setup-test
source benchmark-utils/local_config.sh
make verification-refinery                # results/refinery.*.results.CHC-COMP2026_check-sat.*.xml
make process-results                      # tables of all solvers, in generated/
```

For the model track, also download the validators and validate Refinery's models:

```bash
make download-validators                  # z3, cvc5, princess and carcara
make verification-refinery-model          # results/refinery-model.*: ADT-LIA, --prove-sat
make process-models-refinery              # models/refinery-models -> the run's log files
make cvc5-validate-refinery-models z3-validate-refinery-models princess-validate-refinery-models
make process-results
```

For the proof track, build Carcara and validate Refinery's proofs:

```bash
make tools/carcara                        # needs cargo and a C compiler
make verification-refinery-proof          # results/refinery-proof.*: LIA-Lin, LIA, LRA-Lin, unsat only
make process-proofs-refinery              # proofs/refinery-proofs -> the run's log files
make carcara-validate-refinery-proofs
make process-results                      # tables results-refinery-proof-*, and the proof track on the page
```

A `benchexec` checkout cloned before the proof track was added needs the new tool definition linked:
`ln -sf ../../../tooldefs/chc-proof-validate.py benchexec/benchexec/tools/`.

`make download-results-2026` extracts only the result files (45 MB of the 2 GB archive) with
[`fetch-2026-results.py`](fetch-2026-results.py); `make download-results-2026-logfiles` also
extracts the run logs (5.6 GB), which the result pages link to. Without the 2026 results,
`make process-results` generates tables of Refinery alone. Expected verdicts are read from the
benchmark `.yml` files (`RELABEL_BY_MAJORITY_VOTE = False` in `configs.py`), so no other solver is
needed to score Refinery's answers.

## Adding / Editing Solvers

Verifiers, model-producing verifiers, and validators are **auto-discovered** from
`benchmark-defs/` based on template filename conventions:

| Template pattern              | Role             | Example                          |
|-------------------------------|------------------|----------------------------------|
| `TOOL.xml.template`           | Plain verifier   | `eldarica.xml.template`          |
| `TOOL-model.xml.template`     | Model-producing verifier   | `eldarica-model.xml.template`    |
| `TOOL-validation.xml.template`| Validator        | `cvc5-validation.xml.template`   |
| `TOOL-proof.xml.template`     | Proof-producing verifier | `refinery-proof.xml.template` |
| `TOOL-proof-validation.xml.template` | Proof validator | `carcara-proof-validation.xml.template` |

* **Plain verifiers** are executed once; they do not produce models and need no validation.
* **Model verifiers** produce models that are validated by every discovered validator.
* **Validators** are paired with every model verifier automatically (full cross-product).
* **Proof verifiers** produce proofs of unsatisfiability, which every proof validator checks
  (`make process-all-proofs validate-all-proofs`).

To add a new verifier, do the following three things:

1. **Add a download step in the [Makefile](https://github.com/chc-comp/chc-comp-2026/blob/55597fbb37c7ae4e57b2339bbe816f2eb6b01ed3/Makefile#L125)** Under the `Download Tools` section, add a
   Make target that downloads and unpacks the tool into `tools/TOOL`. Then add
   `$(TOOLS_DIRECTORY)/TOOL` to the `download-tools` prerequisite list. See the existing tools for some examples (e.g., $(TOOLS_DIRECTORY)/theta for a Zenodo-hosted tool).

> [!CAUTION]
> All submitted tools must be publicly available and include a LICENSE file that permits unrestricted evaluation by any party. The license must not impose any limitations on the use, distribution, or analysis of the tool’s outputs, including but not limited to log files, generated models, or intermediate results. The tool archive should be ideally hosted on a long-term archival site such as Zenodo, but this is not a requirement.

2. **Add a benchmark definition.** Create the appropriate `.xml.template` file in
   `benchmark-defs/` following one of the naming conventions above. Copy an [existing
   template](./benchmark-defs/spacer.xml.template) as a starting point. Remove the 
   `<tasks> </tasks>` sections to opt out of the evaluation for that category. 
   Specify the options for the tool (can be per-category and global).
   If opting in to the model evaluation category, create a `-model.xml.template` file as well,
   see [example](./benchmark-defs/spacer-model.xml.template).

3. **Add a BenchExec tool definition.** Create `tooldefs/TOOL.py` implementing a
   BenchExec `Tool` class (see existing files for examples). This tells BenchExec
   how to locate the executable, parse the version string, and determine results.

Run `make debug-discovery` to verify that the new tool is auto-discovered correctly.

## Running the Competition

### Prerequisites

```bash
make download-all      # downloads tools, benchexec, and benchmarks
```

### Configure the environment

Source one of the provided configs before running any benchmarks:

* `source benchmark-utils/local_config.sh` — local execution
* `source benchmark-utils/ci_config.sh` — CI execution (restricted resources).
* `source benchmark-utils/vcloud_config.sh` — VCloud execution

### Choose a benchmark set

* `make setup-benchmark` — full competition suite (~30 days CPU time, 2 cores, 16 GiB RAM).
* `make setup-test` — small smoke-test subset (~5 min).

### Run

```bash
make verify-all          # run all verifiers and export models
make process-all-models  # symlink model logs into models/
make validate-all        # validate models with all validators
make process-results     # generate result tables in results/tables/
```

### CI

A GitHub Actions workflow (`.github/workflows/run-competition.yml`) runs the full
competition with `ci_config.sh` and publishes the result tables to GitHub Pages.
Trigger it manually via the Actions tab (`workflow_dispatch`).

## Available Make Targets

| Target                          | Description                                                  |
|---------------------------------|--------------------------------------------------------------|
| `make download-all`             | Download all dependencies (tools, benchexec, benchmarks).    |
| `make download-refinery`        | Download benchexec and the benchmarks, and build only Refinery. |
| `make download-results-2026`    | Extract the published CHC-COMP 2026 results into `results/`. |
| `make setup-benchmark`          | Point benchmarks at the full suite.                          |
| `make setup-test`               | Point benchmarks at a small smoke-test subset.               |
| `make verify-all`               | Run all verifiers (plain + model).                           |
| `make verification-TOOL`        | Run a single verifier (e.g., `verification-eldarica-model`). |
| `make process-all-models`       | Symlink model logs for all model verifiers.                  |
| `make validate-all`             | Run all validators against all model verifiers.              |
| `make VALIDATOR-validate-all`   | Run one validator against all model verifiers (e.g., `cvc5-validate-all`). |
| `make process-results`          | Generate result tables in `results/tables/`.                 |
| `make debug-discovery`          | Print auto-discovered verifiers, validators, and targets.    |

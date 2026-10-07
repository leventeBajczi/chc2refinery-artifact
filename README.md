# CHC-COMP Model Validation

## Refinery

This fork adds one solver to the CHC-COMP 2026 setup (and RInGen hors concours, for comparison, see
[below](#ringen-hors-concours)): the [Refinery](https://refinery.tools/) graph solver, driven by [chc2refinery](https://github.com/leventeBajczi/chc2refinery), a single
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
* The `validate.sh` of each model validator runs
  [`tools/validator/check-model.sh`](tools/validator/check-model.sh) with its solver. With the
  recursive definition of `h`, the solvers unfold it to a bounded depth only, and time out on
  clauses that hold whatever state `h` gives to a variable. So a model with recursive definitions
  is first checked, for at most 45 s, with the definitions as their equations, asserted for all
  arguments with the applications as patterns (`validate-model.py --equations`; SMT-LIB 2.6
  defines the meaning of `define-funs-rec` so), from which the solvers instantiate `h` at the
  terms of the clauses. Only `unsat` counts from this check, which runs within 4 GB of virtual
  memory for Z3 and cvc5 (Princess limits its heap itself); otherwise, the model is checked as it
  is. Checked again with the same solvers and 90 s, the 33 models of the run of 2026-10-06 (with
  the model of the current chc2refinery for `1-bmc-test-bmc-diamond-1-true.Z3.0_000`, 20 KB, where
  BenchExec had cut one of 21 MB), this confirms 26 models
  instead of 21 (Z3 26 instead of 12, Princess 20 instead of 5, cvc5 18 instead of 19): all models
  of the Cartesian encoding. The 7 models of the synchronous encoding (a predicate on the
  convolution of its arguments, e.g., `x <= y` on Peano numbers) need induction (that `h(x, x)` is
  a diagonal state for every `x`), which no validator does; `chc2refinery.py --check` proves them
  with induction lemmas. Models without recursive definitions (those of the other solvers) are
  checked as before. A log file that BenchExec cut makes `validate-model.py` stop with an error.
* [`benchmark-defs/refinery-proof.xml.template`](benchmark-defs/refinery-proof.xml.template) adds a
  **proof track**, in which only Refinery takes part: on the unsatisfiable benchmarks of LIA-Lin,
  LIA and LRA-Lin, it runs `--prove-unsat --unsat-alethe`, which prints an
  [Alethe](https://verit.gitlabpages.uliege.be/alethe/specification.pdf) proof after `unsat`.
  Z3 re-solves the derivation over the original clauses for exact values; the proof instantiates
  the clauses with them and evaluates their constraints with Carcara's `evaluate` rule (see
  chc2refinery's README), in the current Alethe format, and writes a term that occurs more than
  once only once (named by `:named`), so a proof grows linearly with its clause instances. Proofs
  cover clauses over Booleans, integers and reals, with the operators of these categories (`div`,
  `mod` and `to_real` among them); an `unsat` without a proof counts as unconfirmed.
* [`benchmark-defs/carcara-proof-validation.xml.template`](benchmark-defs/carcara-proof-validation.xml.template)
  checks the proofs with [Carcara](https://github.com/ufmg-smite/carcara) at commit `836d5a6` of its
  main branch (2026-10-05; `make tools/carcara` builds it with cargo), with
  [`tooldefs/chc-proof-validate.py`](tooldefs/chc-proof-validate.py): `valid` confirms the answer
  and `invalid` refutes it. Its `validate.sh` takes the proof after the `unsat` line of the log
  file and checks it against the benchmark as it is, with `--expand-let-bindings` (the proofs are
  let-free) and `--allow-int-real-subtyping` (integer literals in real terms), the options of the
  evaluation of Golem's Alethe proofs (Otoni et al., TACAS 2025). A log file that BenchExec cut
  gives `truncated log`, which leaves the answer unconfirmed rather than refuted.
  An `unsat` counts in the proof track only with a valid proof (`validate.py`, as for models).
* Model and proof runs keep their log files whole up to 1 GB (`--maxLogfileSize`): by default,
  BenchExec cuts the middle out of a log file over 20 MB, which, in the run of 2026-10-06, cut
  the proofs of 7 `LRA-Lin` benchmarks (up to 151 MB, before the proofs named their repeated
  terms) and one model of 21 MB.

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

Validators downloaded before `check-model.sh` was added need their `validate.sh` written again:
`make -B tools/z3 tools/cvc5 tools/princess`.

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

## RInGen (hors concours)

[RInGen](https://github.com/Columpio/RInGen), the regular invariant generator for CHCs over algebraic
datatypes, takes part hors concours (`hors_concours.txt`), in `ADT-LIA`, for comparison with
Refinery's finite models. It entered CHC-COMP 2022 (v1.2, winner of ADT-nonlin, the pure-datatype
track that CHC-COMP 2026 no longer has) and no later edition, so it has no published 2026 results.

* RInGen rewrites the clauses into a formula over uninterpreted functions: datatypes become free
  sorts and constructors free functions, and integers become Peano numbers. The CHC-COMP fork of
  [Vampire](https://github.com/Columpio/vampire) (`--mode chccomp`) then searches for a refutation or a
  saturation (a finite model), which gives `unsat` or `sat`.
* [`wrappers/ringen-chc`](wrappers/ringen-chc) runs the command of RInGen's CHC-COMP 2022 entry,
  `RInGen --timelimit T -q -o DIR/ solve -s vampire --path INPUT -t`, with the run's CPU time limit
  as `T` (passed by [`tooldefs/ringen.py`](tooldefs/ringen.py); RInGen's own default is 300 s). Its
  output is the verdict. The entry also passed `--no-isolation`, which the RInGen used here (the last
  commit of its master branch, `058fe6e`, July 2022, later than the v1.2 of the competition) no
  longer has: it runs the transformation in a process of its own only with `--sync-terms`.
* `make tools/ringen` builds RInGen and Vampire from source at fixed commits: RInGen self-contained
  with the .NET 6 SDK (fetched by `dotnet-install.sh`; no .NET is needed to run it), and Vampire with
  CMake (without Z3). RInGen runs its backend under `/usr/bin/time` (GNU time) to measure it, which
  not every machine has; [`patches/ringen.patch`](patches/ringen.patch) lets the wrapper put
  [`wrappers/ringen-time`](wrappers/ringen-time) in its place.
* **Only problems without integers.** RInGen replaces integers by Peano numbers, which loses negative
  values and subtraction below zero, so its answers on problems with integers can be wrong. Its 2022
  track had no integers, and the wrapper answers `unknown`, without running RInGen, on a problem that
  uses the sort `Int` (576 of the 1131 `ADT-LIA` benchmarks do not). `ADT-LIA-Arrays` is not entered:
  all of its benchmarks use integers, and RInGen failed on every one that we tried.

On a sample of 120 benchmarks with known verdicts (seed 2026, 60 s each, without the integer filter,
3 runs at a time on 4 cores of a 2.8 GHz Xeon), RInGen
answered 30 of the 50 `ADT-LIA` benchmarks without integers correctly (10 of 25 sat, 20 of 25 unsat;
median 0.8 s, at most 22 s) and none wrongly. Of the 50 with integers it answered 5 correctly and 1
wrongly (`tip-adt-lia/false_graph_btp5`, unsat, answered sat), which the wrapper now leaves unknown.
It answered none of the 20 `ADT-LIA-Arrays` benchmarks (all failed within 1 s).

```bash
make tools/ringen                         # needs git, wget, CMake, a C++ compiler and network access
make verification-ringen                  # results/ringen.*: ADT-LIA
```

A `benchexec` checkout cloned before RInGen was added needs its tool definition linked:
`ln -sf ../../../tooldefs/ringen.py benchexec/benchexec/tools/`.

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

# CHC-COMP Model Validation

## Refinery

This fork adds one solver to the CHC-COMP 2026 setup: the [Refinery](https://refinery.tools/)
graph solver, with the [chc2refinery](https://github.com/leventeBajczi/chc2refinery) translation
of CHCs into Refinery problems. A model that Refinery generates is a derivation of `false`, so the
solver answers `unsat` when it finds one, `sat` when Refinery proves that no model exists, and
`unknown` otherwise (e.g., for unsupported features).

* `make tools/refinery` builds the tool: Refinery at a fixed commit with the fixes of
  chc2refinery's `refinery.patch` (built with Gradle; this needs network access to Maven
  Central), chc2refinery at a fixed commit, and a JDK 25 to run on.
* [`wrappers/refinery-chc`](wrappers/refinery-chc) runs the translation and Refinery, and prints
  the verdict. [`tooldefs/refinery.py`](tooldefs/refinery.py) is its BenchExec tool definition.
* [`benchmark-defs/refinery.xml.template`](benchmark-defs/refinery.xml.template) enters all nine
  categories of the solver track, with the competition's limits. Refinery does not produce
  models of satisfiable problems, so it does not enter the model track.

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

* **Plain verifiers** are executed once; they do not produce models and need no validation.
* **Model verifiers** produce models that are validated by every discovered validator.
* **Validators** are paired with every model verifier automatically (full cross-product).

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

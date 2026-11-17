# Local SWE-bench Lite pilot

## What this does

We use one development issue, `marshmallow-code__marshmallow-1343`. The dataset identifies the issue, the repository and its starting commit. The controller assembles a prompt from the issue and explicitly selected source files. It records a patch proposal. The evaluator applies the candidate to a fresh temporary copy and adds the benchmark regression test only after the candidate is prepared. It runs the test file locally and records the result.

The current controller is a **single-request baseline**: it does not search the repository autonomously, run tools, retry, or coordinate multiple agents. The source file is selected manually. The simulation uses a hand-written patch that only adds a comment. It deliberately does not fix the issue. No model or API is involved in the simulated run. The reference patch comes from the dataset, not a model.

Local test execution is not a security sandbox. Run only code and patches you trust. macOS and Python 3.9 differ from the benchmark's original environment, so this is a local adapted evaluation, not an official SWE-bench score.

## What we have verified

- The dev split has 23 issues; this issue's base commit is `2be2d83a1a9a6d3d9b85804f3ab545cecc409bb0`.
- With the simulated candidate and benchmark test: 24 pass and one fails.
- With the benchmark's reference patch and the same tests: 25 pass.
- The evaluator rejects an incorrect commit, a dirty working tree, and a candidate outside `src/`.
- A single-request free-model attempt (`runs/free-flint-05`) produced a patch that Git applied; 25 tests passed locally. Its raw output includes extra text after the patch, which Git ignored; inspect `applied.diff` for what was actually applied. An earlier attempt produced a corrupt patch. These are development runs, not an official benchmark score.
- No multi-agent comparison, RLHF, RLAF or PPO result exists yet.

## Show the dataset and prior results

Run from the project root:

```sh
PYTHONPATH=src HF_HUB_OFFLINE=1 .venv/bin/python -m swe_pilot.inspect_dataset
cat runs/simulated-02/proposal.json
cat runs/simulated-02/evaluation/result.json
cat runs/simulated-02/evaluation/test-output.txt
cat runs/reference-check-02/result.json
cat runs/reference-check-02/test-output.txt
```

`runs/` and `.local/` are ignored local working directories; they are not tracked in Git. The cached dataset, checkout, test patch and local Python environments must exist on this machine for the commands to work. The reference check was deliberately separate from agent inputs.

A compact record of the model run, including its raw response, exact applied diff, usage and local test outcome, is tracked under `experiments/marshmallow_1343/results/free-flint-05/`. It can be inspected without the ignored local environment.

## Run a fresh simulation

Choose a new run name every time. Existing output directories are never overwritten.

```sh
PYTHONPATH=src .venv/bin/python -m swe_pilot.controller \
  --task .local/tasks/marshmallow-1343.json \
  --repository .local/marshmallow \
  --file src/marshmallow/schema.py \
  --mock-patch experiments/marshmallow_1343/simulated.patch \
  --output runs/my-simulation

PYTHONPATH=src .venv/bin/python -m swe_pilot.evaluate \
  --task .local/tasks/marshmallow-1343.json \
  --repository .local/marshmallow \
  --candidate runs/my-simulation/patch.diff \
  --test-patch .local/task-reference/test.patch \
  --python .local/task-venv/bin/python \
  --output runs/my-simulation/evaluation
```

The second command returns exit code 1 because the intentionally incomplete patch fails the regression test. View `runs/my-simulation/prompt.txt`, `patch.diff`, `proposal.json`, and the evaluation's `result.json` and `test-output.txt` to explain the flow.

## Code and tests

- `src/swe_pilot/inspect_dataset.py`: display the dataset and issue.
- `src/swe_pilot/export_task.py`: export only the issue, repository, commit and ID for the agent.
- `src/swe_pilot/controller.py`: prepare a prompt and save a simulated or OpenRouter proposal.
- `src/swe_pilot/evaluate.py`: check the starting commit, apply a patch in a copy, run tests, and save results.
- `experiments/marshmallow_1343/test_issue.py`: independent reproduction of the reported failure.
- `tests/`: small checks for data filtering and evaluator boundaries.

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

## Later: an actual model call

The controller accepts `--model <OpenRouter model ID>` instead of `--mock-patch` and reads `OPENROUTER_API_KEY` from the environment. It only accepts explicit model IDs ending in `:free`, reflecting the zero-spend requirement. Verify the model is still listed as free and available on OpenRouter before running. Do not commit credentials. The model response must be inspected before executing its patch locally.

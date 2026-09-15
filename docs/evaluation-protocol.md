# Evaluation Protocol

## Dataset splits

The initial pilot uses 40 samples:

- 20 syntax bugs.
- 20 logic bugs.
- 70% training, 15% validation, 15% test.

After the pipeline is stable, expand toward the paper-style split:

- 200 total programs.
- 150 training programs.
- 50 held-out programs.

The test set must not be used for training, candidate selection, or memory construction.

## Primary metrics

### Syntax-fix rate

Percentage of syntax-bug programs that compile and pass their validation checks within five suggestions.

### Logic-fix rate

Percentage of logic-bug programs for which all tests pass within five suggestions.

### Overall-fix rate

Percentage of all programs fully repaired within five suggestions.

### Average suggestions

Mean number of suggestions required for successful repairs. Failed episodes are reported separately and are not silently discarded.

### First-attempt acceptance

Percentage of episodes whose first proposed patch is accepted or passes the automated correctness check.

## Secondary metrics

- Episode execution time.
- Number of memory queries.
- Percentage of steps that reuse a stored solution.
- BLEU and ROUGE for generated explanations.
- CodeBLEU for generated patches.
- Reward per episode.
- Failure rate by bug family.

## Baselines

The minimum comparison set is:

1. Random candidate selection.
2. Rule-based candidate selection.
3. Supervised candidate ranking.
4. Single-agent system.
5. Multi-agent system without memory.
6. Full PPO + feedback + memory system.

An LLM one-shot baseline may be added later if the model, prompt, and decoding settings can be documented and reproduced.

## Ablations

Run the full system with one component removed at a time:

- No memory.
- No simulated feedback or RLHF reward.
- No natural-language features.
- Single agent only.
- No candidate reuse.

## Reporting requirements

Every experiment should record:

- Git revision or experiment identifier.
- Dataset split.
- Random seed.
- Model configuration.
- Number of training episodes.
- Mean and standard deviation across at least three seeds once the pipeline is stable.
- Failed examples and their bug families.

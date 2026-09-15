# Initial Bug Taxonomy

The initial taxonomy is intentionally small. We will expand it only after the evaluator and baseline pipeline are reliable.

## Syntax bugs

| ID | Bug family | Example repair |
|---|---|---|
| S1 | Missing colon | Add `:` after `if`, `for`, `while`, `def`, or `class` headers |
| S2 | Unbalanced brackets | Insert, delete, or replace `()`, `[]`, or `{}` |
| S3 | Invalid indentation | Add, remove, or correct leading whitespace |
| S4 | Invalid token | Replace or remove an unexpected token |
| S5 | Missing quote | Add a missing string delimiter |
| S6 | Incorrect keyword | Replace a malformed Python keyword |
| S7 | Invalid comma or separator | Add or remove a separator in a list or call |

## Logic bugs

| ID | Bug family | Example repair |
|---|---|---|
| L1 | Wrong comparison operator | Change `>` to `>=`, or `==` to `!=` |
| L2 | Off-by-one range | Change `range(n - 1)` to `range(n)` |
| L3 | Incorrect initialization | Initialize an accumulator or state variable correctly |
| L4 | Wrong conditional branch | Invert or correct an `if` condition |
| L5 | Incorrect return value | Return the computed result instead of an intermediate value |
| L6 | Loop update error | Correct increment, decrement, or termination logic |
| L7 | Wrong variable reference | Replace a variable with the intended variable |
| L8 | Missing edge-case handling | Add handling for empty, zero, or boundary inputs |

## Dataset construction rules

- Every logic bug must have at least one test that fails before repair and passes after repair.
- Every syntax bug must fail compilation before repair and compile after repair.
- The correct program must pass all associated tests.
- Buggy and correct versions must be stored together, but the correct version must not be exposed to the agent during evaluation.
- Similar bug families should be distributed across train and test splits to measure generalization.

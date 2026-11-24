# Agent Evaluation Cases

Use Promptfoo or the existing evaluation framework. Never judge agent quality solely with an LLM-as-judge; combine deterministic assertions, human review and source checks.

## Dataset categories
1. Identity: current user is Tarik; never substitute John.
2. Calendar: timezone conversion, duplicates, conflicts, missing permissions.
3. Task planning: dependency ordering, idempotent retries, accurate completion state.
4. Tool choice: choose only registered and authorized tools.
5. MCP: valid schema, invalid schema rejection, no privilege escalation.
6. Memory: relevant recall, privacy boundaries, source attribution, no unrelated leakage.
7. Repository analysis: correct repository URL, license extraction, branch/source dates, no fabricated RAM estimate.
8. News/research: cite source and date, distinguish claim from verified fact.
9. Browser agent: obey domain allowlist and stop before destructive side effects.
10. Repair agent: classify risks accurately, require approval for risky operations.
11. Model fallback: use only capability-compatible approved fallback.
12. Voice: transcription test corpus, language/accent/noise robustness, confidence and turn-taking if voice is in scope.

## Required score dimensions
- Task completion.
- Correctness.
- Tool selection.
- Permission compliance.
- Groundedness/source quality.
- Output schema validity.
- Latency.
- Token/cost.
- Failure recovery.
- User satisfaction.

## Regression policy
Keep a versioned golden dataset. A prompt/model/skill change must be compared with the last accepted baseline. Fail or require manual approval when critical safety or correctness metrics regress. Preserve failing traces as a new regression case after review.

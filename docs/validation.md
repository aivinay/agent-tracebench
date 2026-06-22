# Validation Notes

Validation for the `0.1.0` release focuses on deterministic trace analysis.

## Automated Checks

- Unit tests cover summary metrics, failure clustering, replay ordering,
  invalid duration rejection, JSONL round-tripping, OpenTelemetry-compatible
  export, regression comparison, cost estimation, outlier detection, and
  redaction.
- CLI tests cover schema output, trace validation, regression report formatting,
  and clean diagnostics for invalid input.
- Ruff linting is clean.
- Source distribution and wheel builds complete successfully.

## Example Scenario

The `examples/traces` directory contains baseline and candidate JSONL traces.

Run:

```bash
tracebench validate examples/traces/baseline.jsonl
tracebench summarize examples/traces/baseline.jsonl --format markdown
tracebench compare examples/traces/baseline.jsonl examples/traces/candidate.jsonl --format markdown
tracebench cost examples/traces/baseline.jsonl --input-cost-per-million 1 --output-cost-per-million 3
```

These commands demonstrate the package's core workflow: summarize behavior,
compare behavior across changes, and quantify token usage in a reproducible
report.

## Exit Codes

- `0`: Command completed successfully.
- `1`: Input, parsing, or validation error.
- `2`: Trace comparison completed and detected a configured regression.

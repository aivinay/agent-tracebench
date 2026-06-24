# Case study: detecting a retrieval-augmented agent regression

This directory contains the traces and scripts for the case study reported in the
Agent TraceBench paper.

## What it is

A retrieval-augmented generation (RAG) agent built with LangChain is run over a
real text corpus assembled from public Kubernetes/ML-infrastructure
repositories. Each run executes four steps — `plan`, `retrieve`, `tool.analyze`,
`generate` — and **latencies are measured with `time.perf_counter` and token
counts with the `cl100k_base` tokenizer**; they are not simulated. To keep the
experiment reproducible and free of external-API nondeterminism, the
language-model steps use a deterministic local model (LangChain
`FakeListChatModel`), while retrieval and tool execution perform real work.

- `baseline.jsonl` — 120 runs (12 repeats x 10 queries), corpus of 3,000 chunks,
  retrieval depth `k = 3`.
- `candidate.jsonl` — 120 runs, corpus grown to 12,000 chunks, `k = 20`, with an
  injected tool failure path (a realistic "knowledge-base growth + deeper
  retrieval" change).

## Reproduce the analysis with the tool

```bash
# Aggregate threshold gate (flags latency, tokens, and new failures)
tracebench compare examples/case_study/baseline.jsonl \
    examples/case_study/candidate.jsonl

# Distribution-aware (permutation) test on the retrieve-step latency
tracebench compare examples/case_study/baseline.jsonl \
    examples/case_study/candidate.jsonl \
    --method distribution --step-name retrieve --resamples 20000
```

The threshold gate reports a 91% total-latency regression, a 504% token
regression, and 17 new failed steps (exit code 2). The permutation test reports
the retrieve-step median rising from 1 ms to 5 ms (p = 0.00125, significant).

## Regenerate the traces

`run_case_study.py` and `run_power_study.py` regenerate the traces and the
statistical-power study. They require extra packages not needed by the core tool:

```bash
pip install langchain-core tiktoken numpy
python examples/case_study/run_case_study.py
```

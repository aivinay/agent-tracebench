import hashlib
import json
import random
import re
import statistics
import time
from pathlib import Path

import numpy as np
import tiktoken
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from tracebench.assertions import compare_step_distributions, compare_traces
from tracebench.bench import summarize_trace
from tracebench.models import AgentStep

enc = tiktoken.get_encoding("cl100k_base")
DIM = 8192
rng = random.Random(42)


def h(tok):
    return int.from_bytes(hashlib.blake2b(tok.encode(), digest_size=4).digest(), "little") % DIM


def vec(text):
    v = np.zeros(DIM, dtype=np.float32)
    for t in re.findall(r"[a-zA-Z]{3,}", text.lower()):
        v[h(t)] += 1.0
    n = np.linalg.norm(v)
    return v / n if n else v


def load_chunks(roots, maxc):
    chunks = []
    for root in roots:
        for p in sorted(Path(root).rglob("*")):
            if (
                p.is_file()
                and p.suffix.lower() in {".md", ".py", ".yaml", ".yml", ".txt"}
                and "/.git/" not in str(p)
            ):
                try:
                    txt = p.read_text(errors="replace")
                except Exception:
                    continue
                for i in range(0, len(txt), 500):
                    c = txt[i : i + 500].strip()
                    if len(c) > 80:
                        chunks.append(c)
                    if len(chunks) >= maxc:
                        return chunks
    return chunks


roots = [
    "/tmp/corpus/charts",
    "/tmp/corpus/gpu-operator",
    "/tmp/corpus/manifests",
    "/tmp/corpus/kserve",
    "/tmp/corpus/kuberay",
]
base_chunks = load_chunks(roots, 3000)
cand_chunks = load_chunks(roots, 12000)
base_mat = np.vstack([vec(c) for c in base_chunks])
cand_mat = np.vstack([vec(c) for c in cand_chunks])
print(f"corpus: baseline={len(base_chunks)} chunks, candidate={len(cand_chunks)} chunks")

llm = FakeListChatModel(
    responses=["Based on the retrieved context, the answer is summarized here for evaluation."]
    * 9999
)
QUERIES = [
    "how are gpu resources requested",
    "what does the scheduler do",
    "how to configure logging",
    "explain the trace schema",
    "what is a worker plan",
    "how does checkpoint resume work",
    "what ports are exposed",
    "how to set resource limits",
    "what is the manifest format",
    "how does the operator reconcile state",
]


def run_agent(query, mat, chunks, k, may_fail):
    clock = 0
    steps = []

    def add(name, dur_ms, pt=0, ct=0, status="ok", err=None):
        nonlocal clock
        steps.append(
            AgentStep(
                name=name,
                started_at_ms=clock,
                ended_at_ms=clock + max(1, dur_ms),
                prompt_tokens=pt,
                completion_tokens=ct,
                status=status,
                error_type=err,
                attributes={"k": k},
            )
        )
        clock += max(1, dur_ms) + 1

    # plan (LLM)
    t = time.perf_counter()
    plan = llm.invoke(f"Plan: {query}").content
    d = (time.perf_counter() - t) * 1000
    add("plan", round(d), pt=len(enc.encode(query)), ct=len(enc.encode(plan)))
    # retrieve (real matmul + top-k + tokenize context)
    t = time.perf_counter()
    q = vec(query)
    sims = mat @ q
    top = np.argsort(-sims)[:k]
    context = "\n".join(chunks[i] for i in top)
    ctx_tokens = len(enc.encode(context))
    d = (time.perf_counter() - t) * 1000
    add("retrieve", round(d), pt=ctx_tokens)
    # tool (real work over context; may fail under candidate)
    t = time.perf_counter()
    try:
        if may_fail and rng.random() < 0.15:
            raise ValueError("tool parse error")
        words = re.findall(r"[a-zA-Z]+", context)
        _ = statistics.median([len(w) for w in words] or [0])
        d = (time.perf_counter() - t) * 1000
        add("tool.analyze", round(d))
    except ValueError:
        d = (time.perf_counter() - t) * 1000
        add("tool.analyze", round(d), status="error", err="parse_error")
    # generate (LLM)
    t = time.perf_counter()
    ans = llm.invoke(f"Answer using context:\n{context}\nQ:{query}").content
    d = (time.perf_counter() - t) * 1000
    add("generate", round(d), pt=ctx_tokens, ct=len(enc.encode(ans)))
    return steps


def run_config(mat, chunks, k, may_fail, label):
    all_steps = []
    for _ in range(12):
        for query in QUERIES:
            all_steps.extend(run_agent(query, mat, chunks, k, may_fail))
    return all_steps


base_steps = run_config(base_mat, base_chunks, 3, False, "baseline")
cand_steps = run_config(cand_mat, cand_chunks, 20, True, "candidate")
Path("/tmp/cs_baseline.jsonl").write_text(
    "".join(json.dumps(s.to_dict(), sort_keys=True) + "\n" for s in base_steps)
)
Path("/tmp/cs_candidate.jsonl").write_text(
    "".join(json.dumps(s.to_dict(), sort_keys=True) + "\n" for s in cand_steps)
)

bs = summarize_trace(base_steps)
cs = summarize_trace(cand_steps)
nruns = 12 * len(QUERIES)


def med_step(steps, name):
    return statistics.median([s.latency_ms for s in steps if s.name == name])


print(f"\nRuns per config: {nruns}")
print(
    f"BASELINE: total_latency={bs.total_latency_ms} ms, total_tokens={bs.total_tokens}, failed={bs.failed_steps}"
)
print(
    f"CANDIDATE: total_latency={cs.total_latency_ms} ms, total_tokens={cs.total_tokens}, failed={cs.failed_steps}"
)
print(
    f"median retrieve latency: base={med_step(base_steps, 'retrieve')} ms -> cand={med_step(cand_steps, 'retrieve')} ms"
)
# bottleneck: share of total latency by step in candidate
from collections import Counter

share = Counter()
for s in cand_steps:
    share[s.name] += s.latency_ms
tot = sum(share.values())
print(
    "candidate latency share by step:", {k: f"{100 * v / tot:.0f}%" for k, v in share.most_common()}
)
print(f"per-run tokens: base={bs.total_tokens // nruns} -> cand={cs.total_tokens // nruns}")
# threshold compare
r = compare_traces(base_steps, cand_steps)
print("\nThreshold compare passed:", r.passed)
[print("  -", m) for m in r.messages]
# distribution compare on retrieve latency
d = compare_step_distributions(
    base_steps, cand_steps, step_name="retrieve", n_resamples=20000, seed=0
)
print(
    f"Distribution test (retrieve latency): base_median={d.baseline_median} cand_median={d.candidate_median} "
    f"shift=+{d.relative_shift_pct:.0f}% p={d.p_value:.5f} significant={d.significant}"
)

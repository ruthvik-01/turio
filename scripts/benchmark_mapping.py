"""Reproducible local microbenchmark; not cloud/ATS effectiveness evidence."""
import argparse
import hashlib
import json
import platform
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services import form_mapping


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True,
                        help="New report path; existing evidence is never overwritten.")
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to overwrite existing microbenchmark evidence.")
    labels = sorted({label for group in form_mapping.ALIASES.values() for label in group})
    labels += ["Are you legally authorized to work in this country?", "Other question"]
    corpus = [(label, "text") for label in labels]
    baseline = form_mapping.intent.__wrapped__
    assert [baseline(*item) for item in corpus] == [form_mapping.intent(*item) for item in corpus]
    iterations = 500000
    timings, cpu_timings = {}, {}
    for name, function in (("uncached", baseline), ("cached", form_mapping.intent)):
        samples, cpu_samples = [], []
        for _ in range(5):
            start = time.perf_counter_ns()
            cpu_start = time.process_time_ns()
            for index in range(iterations):
                function(*corpus[index % len(corpus)])
            samples.append((time.perf_counter_ns() - start) / iterations)
            cpu_samples.append((time.process_time_ns() - cpu_start) / iterations)
        timings[name] = statistics.median(samples)
        cpu_timings[name] = statistics.median(cpu_samples)
    form_mapping.intent.cache_clear()
    tracemalloc.start()
    for item in corpus:
        form_mapping.intent(*item)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    result = {
        "scope": "Repeated synthetic/local vocabulary microbenchmark, not network or live-ATS latency",
        "python": platform.python_version(), "iterations_per_sample": iterations, "samples": 5,
        "labels": len(corpus), "median_ns_per_call": timings,
        "median_cpu_ns_per_call": cpu_timings,
        "cpu_timing_note": "Process CPU-clock medians are approximate; zero means below measurement granularity, not zero CPU use.",
        "speedup": timings["uncached"] / timings["cached"], "output_equivalence": True,
        "cache_entries": form_mapping.intent.cache_info().currsize, "cache_peak_bytes": peak,
        "source_sha256": hashlib.sha256(Path(form_mapping.__file__).read_bytes()).hexdigest(),
        "platform": platform.platform(),
        "bandwidth": "Not applicable: both measured functions execute locally without network I/O.",
        "accuracy_scope": "Exact output equivalence on this fixed vocabulary only; not human relevance or live ATS accuracy.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps(result, indent=2))
    if timings["cached"] >= timings["uncached"]:
        raise SystemExit("No measured speed improvement; do not claim optimization.")


if __name__ == "__main__":
    main()

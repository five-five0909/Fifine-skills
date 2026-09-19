# Performance Diagnosis and Optimization Playbook

Use this reference only when the adaptive runtime task includes performance diagnosis, tuning,
benchmarking, profiling, or concurrency selection. The skill remains executor-neutral and
host-neutral: detect the actual target first.

## Objective

Maximize effective project output per unit time under correctness, reproducibility, stability, and
hardware-safety constraints. Do not maximize CPU/GPU/RAM/VRAM utilization for its own sake.

Useful objective metrics may include wall-clock time, throughput, latency, samples/sec, steps/sec,
tokens/sec, tasks/hour, experiments/hour, jobs/day, time-to-solution, I/O throughput, memory
efficiency, or energy/thermal efficiency. Choose the metric that matches the project.

## Understand before tuning

Inspect only what is needed to identify the causal path:

- entry command, runner, scheduler, service, or notebook path
- relevant code path and configuration
- dependencies and compute framework versions
- data loading, preprocessing, caching, and output artifacts
- current processes/jobs and existing logs
- CPU/GPU/RAM/VRAM/I/O/network consumers
- independent work units that could run concurrently
- knobs that affect correctness versus knobs that affect only performance

## Environment discovery

Detect rather than assume. Pick tools available on the target, such as `lscpu`, `free`, `numactl`,
`lsblk`, `iostat`, `vmstat`, `pidstat`, `top`, `htop`, `nvidia-smi`, `nvidia-smi dmon`,
`nvidia-smi -q`, ROCm equivalents, framework profilers, scheduler status commands, container
status, and network/disk probes.

Capture only relevant fields: CPU model/core/thread topology, NUMA, memory, disks/filesystem,
network, OS, driver, CUDA/ROCm, Python/runtime, framework, GPU count/model/VRAM/power/temp/clocks,
PCIe state, and active competing jobs.

## Baseline

Before changing anything, record a comparable baseline:

- exact command/config and working directory
- wall-clock time and the chosen throughput/latency metric
- correctness signal or output checksum/metric when available
- concurrency level and resource limits
- CPU utilization, load, RAM, swap
- GPU utilization, VRAM, power, temperature, clocks, throttling when relevant
- disk and network I/O when relevant
- log/artifact paths and timestamps

If a metric is irrelevant or unavailable, say so instead of fabricating it.

## Bottleneck taxonomy

Do not conclude from one utilization number. Consider CPU compute, GPU compute, memory bandwidth,
VRAM bandwidth, disk I/O, network I/O, preprocessing/DataLoader, host-to-device transfer, kernel
launch overhead, synchronization, lock contention, Python/runtime overhead, batch size, worker or
thread count, process count, task granularity, resource competition, thermal throttling, power
limits, clock limits, NUMA/affinity, PCIe, allocation overhead, cache misses, low algorithmic
parallelism, and inefficient implementation.

Acceptable conclusion: low utilization is expected for this workload and no performance change is
worth the risk.

## Experiment loop

For each important optimization:

```text
Observe → Hypothesis → Change → Benchmark → Compare → Keep/Rollback → Next Hypothesis
```

Vary one main factor at a time where practical. Record Before, After, Improvement, Side Effects,
and Decision. Roll back changes that do not improve the chosen objective or that compromise
correctness/stability.

Candidate strategies include batch/chunk/block size, worker/thread/process count, async execution,
prefetch, cache, pinned memory, persistent workers, mixed precision, compilation, vectorization,
kernel fusion, copy reduction, synchronization reduction, preprocessing optimization, I/O pipeline
tuning, affinity/NUMA, memory management, multi-GPU scheduling, pipeline/task/experiment
parallelism, and concurrency scheduling. Do not try all of them mechanically.

## Correctness boundary

Never silently change data, splits, labels, output definition, metrics, core algorithm semantics,
required numerical precision, randomization/fairness, or business logic. If an optimization may
affect semantics, add a correctness validation suited to the project before accepting it.

## Concurrency search

If single-task latency is no longer the limiting objective, test whole-machine throughput across
concurrency `N` values. Do not assume more is better. Compare aggregate throughput, per-task
slowdown, total completion time, CPU/GPU/RAM/VRAM contention, I/O contention, temperature, power,
and stability. Recommend the knee of the curve, not necessarily the highest utilization.

## Hardware safety

Monitor temperature, power, clocks, throttling, OOM, swap, disk pressure, and instability. If unsafe
conditions appear, reduce pressure and diagnose first. Do not change drivers, kernels, firmware, or
system-critical settings without explicit user authorization.

## Final report schema

1. Environment
2. Baseline
3. Bottleneck
4. Evidence
5. Optimization Attempts
6. Benchmark
7. Failed Attempts
8. Final Configuration
9. Concurrency
10. Expected Performance
11. Remaining Bottlenecks
12. Next Steps

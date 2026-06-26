# NPU Design Deep Dive: From Neurons to Silicon
## A Complete Technical Reference for ASIC Engineers

---

> **Scope:** This document covers Neural Processing Units (NPUs) as hardened IP blocks integrated into SoCs. The perspective is that of an ASIC/RTL engineer who needs to understand architecture, microarchitecture, physical design trade-offs, and the full software stack that sits above the hardware.

---

## Table of Contents

1. [Neural Network Fundamentals — The ASIC Engineer's Cheat Sheet](#1-neural-network-fundamentals)
2. [NPU Architecture — The Big Picture](#2-npu-architecture)
3. [Key Functional Blocks](#3-key-functional-blocks)
4. [Micro-Architecture Deep Dive](#4-micro-architecture-deep-dive)
5. [Data Formats & Precision](#5-data-formats--precision)
6. [Memory Subsystem](#6-memory-subsystem)
7. [Interconnect & Integration in a SoC](#7-interconnect--integration-in-a-soc)
8. [PPA Trade-offs](#8-ppa-trade-offs-performance-power-area)
9. [Physical Design Considerations](#9-physical-design-considerations)
10. [Software Stack Architecture](#10-software-stack-architecture)
11. [NPU Firmware](#11-npu-firmware)
12. [Compiler Toolchain](#12-compiler-toolchain)
13. [Runtime & Driver Layer](#13-runtime--driver-layer)
14. [APIs & Frameworks](#14-apis--frameworks)
15. [Real-World NPU Architectures](#15-real-world-npu-architectures)
16. [Designing Your Own NPU — A Practical Checklist](#16-designing-your-own-npu)

---

## 1. Neural Network Fundamentals

### 1.1 The Neuron — What Hardware Actually Computes

A single artificial neuron computes:

```
y = f( Σ(wᵢ · xᵢ) + b )
```

Where:
- `xᵢ` = inputs (activations from previous layer)
- `wᵢ` = weights (learned parameters, stored in memory)
- `b` = bias
- `f()` = activation function (ReLU, GELU, SiLU, Sigmoid…)

**From a hardware perspective:** this is a multiply-accumulate (MAC) operation followed by a non-linear function. 99% of what an NPU does is MAC operations.

### 1.2 Layer Types and Their Hardware Implications

| Layer Type | Core Operation | Memory Pattern | Hardware Challenge |
|---|---|---|---|
| **Fully Connected (Dense)** | Matrix-Vector Multiply (MVM) | Weight matrix read sequentially | High weight bandwidth demand |
| **Convolution (Conv2D)** | Sliding-window dot products | Weight reuse, input reuse | Maximizing data reuse, tiling |
| **Depthwise Conv** | Per-channel convolution | Less weight bandwidth | Low arithmetic intensity |
| **Batch Normalization** | Scale + shift + sqrt | Small parameter buffers | Simple ALU, fused with conv |
| **Attention (Transformer)** | QKV projections + softmax + matmul | Quadratic KV cache growth | Memory bandwidth, softmax non-linearity |
| **Pooling** | Max/Average over spatial window | Simple dataflow | Low compute, mostly control |
| **Embedding Lookup** | Table read indexed by token | Irregular memory access | Random access latency |

### 1.3 Why Convolution Is the NPU's Bread and Butter

A Conv2D with parameters `(N, C, H, W, K, R, S)` performs:

```
Output[n][k][oh][ow] = Σ_c Σ_r Σ_s  Input[n][c][oh+r][ow+s] × Weight[k][c][r][s]
```

- Total MACs = `N × K × OH × OW × C × R × S`
- For a ResNet-50 layer: potentially billions of MACs
- Weights can be reused across different input positions → **weight stationarity**
- Inputs can be reused by multiple filters → **input stationarity**

**This data reuse is the fundamental justification for on-chip SRAM buffers.**

### 1.4 Transformers — The New Dominant Workload

Modern LLMs and vision transformers introduce new hardware challenges:

```
Attention(Q, K, V) = softmax(QKᵀ / √d) · V
```

Hardware implications:
- **Prefill phase:** batch of input tokens, compute-bound (high arithmetic intensity)
- **Decode phase:** single token, memory-bound (weights must be re-read every step)
- **KV Cache:** must store K and V tensors for all past tokens — grows linearly with sequence length
- **Softmax:** requires `exp()`, `sum()`, `division` — needs special function units or approximations

---

## 2. NPU Architecture — The Big Picture

### 2.1 What an NPU Is (and Isn't)

An NPU is a **domain-specific accelerator** for inference (and sometimes training). It is:

- A **fixed-function + programmable hybrid** — fixed datapaths optimized for MAC, programmable control for flexibility
- Distinct from a GPU (general SIMT), a DSP (general vector), and a CPU (general scalar)
- Typically **inference-only** in mobile/edge SoCs; training NPUs (like Google TPU) are a separate class

### 2.2 Top-Level Block Diagram

```
┌───────────────────────────────────────────────────────────┐
│                         NPU IP                            │
│  ┌──────────┐   ┌──────────────────────────────────────┐  │
│  │  Host    │   │         NPU Core Cluster             │  │
│  │ Interface│   │  ┌─────────┐  ┌─────────┐            │  │
│  │ (AXI/ACE)│   │  │  Core 0 │  │  Core 1 │  ...       │  │
│  └────┬─────┘   │  └────┬────┘  └────┬────┘            │  │
│       │         │       │             │                │  │
│  ┌────▼─────┐   │  ┌────▼─────────────▼───────────┐    │  │
│  │  DMA     │   │  │      Shared L2 SRAM Buffer   │    │  │
│  │  Engine  │   │  └──────────────────────────────┘    │  │
│  └────┬─────┘   └──────────────────────────────────────┘  │
│       │                                                   │
│  ┌────▼──────────────────────┐                            │
│  │   Memory Interface Unit   │  → External DRAM (LPDDR5)  │
│  │   (AXI Master)            │                            │
│  └───────────────────────────┘                            │
│  ┌──────────────────────────────┐                         │
│  │   Micro-Controller (MCU)     │  ← Firmware / Scheduler │
│  └──────────────────────────────┘                         │
└───────────────────────────────────────────────────────────┘
```

### 2.3 The Three Axes of NPU Design

Every architectural decision in an NPU maps to one of three axes:

**1. Compute Density** → How many MACs per clock cycle per mm²?
**2. Memory Bandwidth** → How fast can you feed the compute with weights and activations?
**3. Flexibility** → Can it run the next generation of models without a respin?

These axes are in tension. Maximizing one typically compromises another.

---

## 3. Key Functional Blocks

### 3.1 MAC Array (Systolic or Vector)

The heart of the NPU. Two dominant architectures:

**Systolic Array (Google TPU style):**
```
Data flows in two orthogonal directions (weights and activations).
Each PE does one MAC and passes data to neighbors.

 A→  A→  A→
↓W  ↓W  ↓W
[PE][PE][PE]   Each PE: acc += A × W
↓   ↓   ↓
[PE][PE][PE]
↓   ↓   ↓
[PE][PE][PE]
```

- Pros: extremely area-efficient for large matmul, no shared bus
- Cons: inflexible for non-matmul ops, latency to fill/drain the array ("systolic skew")

**Vector/SIMD Array (Arm Ethos style):**
```
Multiple vector MAC units operating in parallel.
Each unit computes a dot product of input vector × weight vector.

Input Vector [x0, x1, ..., x63] broadcast
Weight Rows  [w00..w63], [w10..w63], ...  → each row → one output element
```

- Pros: more flexible, easier to handle different layer types
- Cons: more complex control, broadcast buses consume power

### 3.2 Activation Engine (Post-Processing Unit)

Handles everything that comes after the MAC accumulation:

- **ReLU / Leaky ReLU:** comparator + multiplexer (trivial)
- **Sigmoid / Tanh:** lookup table (LUT) with linear interpolation
- **GELU / SiLU:** polynomial approximation or LUT (more bits needed)
- **Softmax:** requires `exp()` → max-subtraction trick → `exp()` → sum → divide
- **Layer Norm / Batch Norm:** mean, variance, scale, shift
- **Requantization:** scale + clip + round (INT8 → INT8 after accumulation in INT32)

**Implementation choice:** dedicated fixed-function units vs. programmable ALU in the post-processor. Modern NPUs use a mix — fixed for common ops, programmable for exotic ones.

### 3.3 Weight Buffer (SRAM)

Holds weights fetched from DRAM before feeding the MAC array. Sized to hold at least one layer's weights to avoid stalling.

Key parameters:
- **Capacity:** 256 KB to several MB (trade-off vs. area)
- **Ports:** multi-banked to sustain MAC array throughput
- **ECC:** mandatory for reliability in safety-critical applications

### 3.4 Activation Buffer (Partial Sum Buffer)

Holds input activations and intermediate partial sums (accumulators). Must handle:

- Wide accumulator words (INT32 or FP32 during computation)
- Concurrent read (to feed MAC) and write (from previous layer output)
- Double-buffering to hide DRAM latency

### 3.5 DMA Engine

Manages data movement between DRAM and on-chip buffers. Must support:

- **Strided transfers:** rows of a feature map are not contiguous in NCHW format
- **Tiling:** decomposing large tensors into chunks that fit on-chip
- **Scatter-Gather:** for sparse or irregular access patterns
- **Prefetching:** issuing DRAM requests ahead of compute to hide latency

**Critical metric:** DMA throughput must equal or exceed MAC array consumption rate.

### 3.6 Control / Sequencer

Orchestrates the execution of a neural network layer-by-layer:

- Decodes instructions issued by the MCU or host CPU
- Programs DMA, MAC array, and post-processing units
- Handles synchronization (compute cannot start before data arrives)
- Reports status and interrupts back to the host

### 3.7 Embedded MCU

A small processor (RISC-V or Cortex-M class) inside the NPU that:

- Runs firmware
- Schedules layers across the hardware
- Handles non-accelerated operations (custom ops)
- Manages power state transitions
- Communicates with the host CPU via mailbox registers

---

## 4. Micro-Architecture Deep Dive

### 4.1 Dataflow Strategies

The single most important micro-architectural choice. It determines how data moves between memory levels and the MAC array:

**Weight Stationary (WS):**
```
Weights are loaded once into register files.
Inputs stream through. Partial sums move.

Best for: fully connected layers (weight reuse across batch)
Used by: early neural network accelerators
```

**Output Stationary (OS):**
```
Partial sums stay in the accumulator register.
Both weights and inputs stream in.

Best for: element-by-element accumulation
Used by: convolution layers with deep channels
```

**Input Stationary (IS):**
```
Input activations stay in place.
Weights stream. Outputs accumulate locally then moved.

Best for: depthwise convolution, low-reuse situations
```

**Row Stationary (RS) [Eyeriss]:**
```
Filters rows are mapped to PEs with maximum reuse of all three data types.
Minimizes memory bandwidth across all data types simultaneously.

Pros: best energy efficiency
Cons: complex control, harder to implement
```

**In practice:** modern NPUs use a hybrid approach — they choose the optimal dataflow per layer type at compile time.

### 4.2 Tiling

Since on-chip SRAM is orders of magnitude smaller than the full model, tensors must be processed in **tiles** (chunks):

```
Full Weight Tensor (e.g., 512×512 = 2M values × 1 byte = 2 MB)
    → Tile size: 64×64 (fits in on-chip buffer)
    → Iterate: 8×8 = 64 tiles

Key tiling parameters:
  - tile_M, tile_N, tile_K for matmul (output rows, output cols, reduction dim)
  - tile_H, tile_W, tile_C for convolution (spatial height, width, channels)
```

Tiling decisions affect:
- **DRAM traffic:** bad tiling = re-reading same data multiple times
- **Buffer utilization:** too-large tiles = SRAM overflow
- **Compute efficiency:** too-small tiles = overhead dominates

The **roofline model** is the standard tool for analyzing whether an operation is compute-bound or memory-bandwidth-bound for a given tile size.

### 4.3 The Roofline Model

```
Performance (TOPS)
        │
        │           Compute Ceiling ─────────────────
        │          /
        │         /  ← Compute-bound region
        │        /
        │       /
        │      /  ← Memory-bandwidth-bound region
        │     /
        └─────────────────────────────────────────── Arithmetic Intensity (OPS/Byte)
                    ^
                Ridge Point: compute_peak / bandwidth_peak
```

- If `arithmetic_intensity > ridge_point` → compute-bound → increase MAC count
- If `arithmetic_intensity < ridge_point` → memory-bound → increase bandwidth or improve reuse

**Depthwise conv and embedding lookups are almost always memory-bound.**
**Large matmuls and conv with many channels are often compute-bound.**

### 4.4 Pipeline Stages in a MAC Array PE

A single Processing Element (PE) at the RTL level:

```
Stage 1: Input  Register (latch activation + weight)
Stage 2: Multiplier        (8b×8b → 16b or 16b×16b → 32b)
Stage 3: Accumulator Add   (32b partial sum + product → 32b)
Stage 4: Output Register   (hold or forward to neighbor)
```

**Critical path:** the multiplier and adder chain determine the maximum frequency. For INT8 MAC:

- 8×8 multiplier: ~2-3 FO4 delays
- 32-bit adder: ~4-6 FO4 delays
- Total: achievable at 1-2 GHz in 5nm

For FP16/BF16 MACs, the critical path is longer (~20-30% slower).

### 4.5 Accumulator Precision

Even in INT8 networks, accumulators must be wider:

```
Max accumulation without overflow:
  - INT8 inputs: -128 to +127
  - INT8 weights: -128 to +127
  - Product: max = 127 × 127 = 16,129 → fits in INT16
  - After K accumulations: max = K × 16,129
  - For K = 1024 channels: 16,129 × 1024 = 16.5M → needs INT32 (fits in 25 bits)

Therefore: INT8 MAC → INT32 accumulator is the standard.
After accumulation, requantize: INT32 → INT8 (scale, clip, round)
```

### 4.6 Parallelism Dimensions

An NPU exposes parallelism in multiple dimensions simultaneously:

```
Spatial parallelism:
  - Multiple PEs in parallel → process multiple output channels or positions

Temporal unrolling:
  - MAC pipeline runs every cycle → deep pipeline for throughput

Dataflow parallelism:
  - DMA fetching tile N+1 while MAC processes tile N (double buffering)
  - Post-processing unit working on tile N-1 output while MAC processes tile N
```

### 4.7 Sparsity Support

Modern workloads exhibit weight and activation sparsity (many zeros after pruning or ReLU):

**Unstructured sparsity:**
- Compressed Sparse Row (CSR) format: skip zero multiplications
- Hardware: comparator to detect zero, mux to skip
- Challenge: irregular memory access, hard to achieve high utilization

**Structured sparsity (NVIDIA 2:4):**
- 2 non-zero values in every group of 4 weights
- Compressed representation: 50% storage, hardware decoder re-expands indices
- Achieves 2× throughput in matmul with predictable hardware

**Activation sparsity:**
- After ReLU, many activations are zero
- Hardware skips MAC when input activation is zero
- Gating: AND the clock or input to the multiplier for power savings

---

## 5. Data Formats & Precision

### 5.1 Quantization Overview

Quantization maps floating-point values to integers:

```
Quantization:  x_int = round( x_float / scale ) - zero_point
Dequantization: x_float ≈ (x_int + zero_point) × scale

Where scale = (x_max - x_min) / (2^bits - 1)
```

Hardware impact: smaller data types → smaller multipliers → more MACs per mm².

### 5.2 Supported Data Types and Their Hardware Cost

| Format | Bits | Relative Multiplier Area | Use Case |
|---|---|---|---|
| FP32 | 32 | ~1.0× (baseline) | Reference / training |
| BF16 | 16 | ~0.25× | Training, high-quality inference |
| FP16 | 16 | ~0.25× | Inference, GPU-compatible |
| FP8 (E4M3) | 8 | ~0.08× | Aggressive inference |
| INT8 | 8 | ~0.06× | Standard mobile inference |
| INT4 | 4 | ~0.02× | Aggressive compression |
| INT2 / Binary | 2/1 | ~0.005× | Experimental |

**In an NPU ASIC:** supporting multiple precisions costs area. Common choices:
- **Mobile/edge:** INT8 primary, INT16/FP16 for sensitive layers
- **Server inference:** FP16/BF16 primary, FP8 optional
- **Ultra-low power:** INT4 + INT8 mixed

### 5.3 Mixed Precision

Different layers have different sensitivity to quantization. A compiler assigns precision per layer:

```
First layer:    FP16 (sensitive to input distribution)
Hidden layers:  INT8 (robust, high compute density)
Attention:      INT8 weights + FP16 softmax
Last layer:     FP16 (sensitive to output accuracy)
```

Hardware must support switching precision without stalling. This requires:
- Configurable multiplier width (or separate multiplier banks)
- Configurable accumulator width
- Format conversion units at buffer boundaries

### 5.4 Block Floating Point (BFP)

A compromise between FP and INT used by some NPUs (e.g., Microsoft Brainwave):

```
Group of values share a common exponent:
  [mantissa_0, mantissa_1, ..., mantissa_N] × 2^shared_exponent

Hardware: INT multipliers + one exponent path
Benefits: better accuracy than INT8, cheaper than FP16
```

---

## 6. Memory Subsystem

### 6.1 Memory Hierarchy

```
                     Latency    Bandwidth    Capacity    Energy/access
┌──────────────────────────────────────────────────────────────────┐
│ Register File (in PE)  │ 1 cycle  │ unlimited  │ KB     │ 1×       │
│ L1 SRAM (per core)     │ 2-4 cyc  │ TB/s       │ 64-512KB│ 2×      │
│ L2 SRAM (shared)       │ 5-10 cyc │ 100-500GB/s│ 1-8 MB │ 5×       │
│ On-chip HBM/LPDDR (eDRAM)│ ~50 cyc│ 50-200GB/s │ 64-512MB│ 20×     │
│ Off-chip DRAM (LPDDR5) │ 50-100ns │ 20-80 GB/s │ GBs    │ 100-200× │
└──────────────────────────────────────────────────────────────────┘
```

**The key insight:** energy cost of accessing DRAM is 100-200× higher than a register file. Every byte you can avoid going to DRAM is a massive power saving.

### 6.2 SRAM Banking

On-chip SRAM is banked to provide enough ports:

```
Goal: feed MAC array with B bytes/cycle
SRAM port width: W bytes/cycle
Number of banks needed: ceil(B / W)

Example:
  - 256 INT8 MACs in parallel → need 256 bytes of weight + 256 bytes of activation per cycle
  - Single SRAM port: 64 bytes/cycle
  - Need: min 4 banks (weight) + 4 banks (activation) = 8 banks minimum
```

Bank conflicts (two accesses to the same bank in the same cycle) cause stalls. The compiler must be aware of the banking scheme to generate conflict-free access patterns.

### 6.3 Double / Triple Buffering

To hide DRAM latency:

```
Cycle T:   DMA fetches tile[N+1] → Buffer B
           MAC computes tile[N]  from Buffer A
           Post-proc outputs tile[N-1] from Buffer C  (if triple buffering)

Cycle T+1: DMA fetches tile[N+2] → Buffer C
           MAC computes tile[N+1] from Buffer B
           ...
```

This requires at least 2× buffer capacity but allows continuous compute utilization. The area cost of the extra SRAM must be justified by the utilization improvement.

### 6.4 Memory Interface to External DRAM

The NPU's memory interface is typically:
- **Protocol:** AXI4 master (64-128 bit bus, 256-512 bit with multiple channels)
- **Burst length:** 16-64 beats for maximum bus efficiency
- **QoS:** NPU may share the DRAM with CPU, GPU, ISP → requires arbitration and priority
- **Bandwidth:** the main bottleneck for memory-bound workloads

For a 256 INT8 MAC NPU at 1 GHz:
- Peak compute: 256 TOPS × 2 bytes/MAC = 512 GB/s internal throughput
- DRAM bandwidth (LPDDR5): ~80 GB/s
- Gap closed by: on-chip data reuse (the entire purpose of on-chip SRAM)

---

## 7. Interconnect & Integration in a SoC

### 7.1 NPU as an IP Block in a SoC

```
┌────────────────────────────────────────────────────┐
│                       SoC                          │
│                                                    │
│  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────────┐  │
│  │  CPU  │  │  GPU  │  │  ISP  │  │    NPU    │  │
│  │Cluster│  │       │  │       │  │    IP     │  │
│  └───┬───┘  └───┬───┘  └───┬───┘  └─────┬─────┘  │
│      │          │           │             │        │
│  ────┴──────────┴───────────┴─────────────┴────    │
│              System Interconnect (NoC)             │
│  ────────────────────────────────────────────      │
│                        │                           │
│              ┌──────────┴──────────┐               │
│              │   Memory Controller  │               │
│              │   (LPDDR5 / HBM)    │               │
│              └─────────────────────┘               │
└────────────────────────────────────────────────────┘
```

### 7.2 Host Interface

The host CPU configures and controls the NPU via:

**Register Interface:**
- AXI4-Lite slave: configuration registers, status, interrupts
- Mapped to the SoC's peripheral address space
- Driver writes registers to issue commands

**Mailbox / Message Queue:**
- For complex command sequences (inference requests)
- Ring buffer in shared SRAM, doorbell register to signal the NPU MCU

**Interrupt:**
- NPU asserts interrupt when inference completes or error occurs
- CPU processes result, dispatches next request

### 7.3 DMA Coherency

Critical design decision: is the NPU cache-coherent with the CPU?

**Non-coherent (most mobile NPUs):**
- NPU accesses DRAM directly via its own AXI master
- CPU must flush caches before NPU reads, and invalidate after NPU writes
- Software must explicitly manage coherency (CMOs: Cache Maintenance Operations)
- Simpler hardware, lower area

**Coherent (ACE/CHI):**
- NPU participates in the coherency protocol
- No explicit software CMOs needed
- More complex hardware (snoop filters, coherency logic)
- Higher bandwidth consumption on the interconnect

### 7.4 Network-on-Chip (NoC)

For multi-core NPU designs (e.g., 4-8 NPU cores sharing L2 SRAM):

- **Mesh topology:** each core connected to neighbors, good scalability
- **Crossbar:** full connectivity, low latency, poor scalability (O(N²) wires)
- **Ring:** low area, higher latency for large rings

Key parameters:
- **Flit width:** 128-512 bits
- **VC (Virtual Channels):** to avoid deadlock
- **Flow control:** credit-based

---

## 8. PPA Trade-offs: Performance, Power, Area

### 8.1 Performance Metrics

**Peak Throughput:**
```
TOPS = (number_of_MACs) × 2 × frequency / 1e12
       ↑ ×2 because one MAC = one multiply + one add = 2 operations
```

**Utilization:**
```
Effective_TOPS = Peak_TOPS × utilization
Utilization depends on:
  - Memory bandwidth adequacy
  - Layer shape matching the array dimensions
  - Control overhead (layer transitions, DMA setup)
```

**Latency:**
- For edge AI (voice, face detection): end-to-end latency matters more than throughput
- Minimize: layer-to-layer DRAM spill, startup overhead, interrupt latency

### 8.2 Power Budget Breakdown

Typical breakdown for an INT8 NPU at 7nm:

| Component | % of Total Power |
|---|---|
| MAC Array (switching) | 35-45% |
| On-chip SRAM (read/write) | 25-35% |
| DRAM accesses (memory I/O) | 10-20% |
| Clock distribution | 5-10% |
| Control logic / MCU | 3-7% |

**Key levers to reduce power:**
- **Clock gating:** gate MAC array when not computing (between tiles)
- **Power gating:** gate entire NPU when idle (milliseconds timescale)
- **Operand isolation:** gate multiplier inputs when weight = 0 (sparsity)
- **DVFS:** reduce VDD and frequency for non-latency-critical inference
- **Data reuse:** reduce DRAM accesses (dominant energy source)

### 8.3 Area Breakdown

At 7nm, rough estimates for a 1 TOPS INT8 NPU:

| Component | Area Estimate |
|---|---|
| MAC array (512 PEs) | ~0.5 mm² |
| On-chip SRAM (4 MB) | ~2.0 mm² |
| DMA + Control | ~0.2 mm² |
| MCU | ~0.1 mm² |
| Memory interface | ~0.1 mm² |
| **Total** | **~3 mm²** |

SRAM typically dominates NPU area (50-70%). The ratio of SRAM to compute is the key design knob.

### 8.4 SRAM vs. Compute Balance

```
Too little SRAM: 
  → Frequent DRAM spills
  → Memory-bound regardless of MAC count
  → Low effective utilization
  → High dynamic power from DRAM access

Too much SRAM:
  → Area waste
  → Static leakage power from idle SRAM
  → Longer routing delays (macro placement)

Sweet spot: size SRAM to hold the working set of the critical layer
```

### 8.5 Frequency vs. Array Size Trade-off

For a fixed TOPS target, you can choose:

**Option A: Fewer MACs, Higher Frequency**
- Pro: smaller array, better routability, lower wire delay
- Con: higher dynamic power density, harder timing closure, more pipeline stages needed

**Option B: More MACs, Lower Frequency**
- Pro: lower power (quadratic with voltage, frequency allows voltage reduction)
- Con: larger area, harder to achieve MAC utilization, more complex control

**Industry trend:** prefer wider arrays at moderate frequency (500 MHz - 1.5 GHz) over narrow arrays at extreme frequency.

---

## 9. Physical Design Considerations

### 9.1 Floorplanning the NPU

```
┌─────────────────────────────────────────┐
│           NPU Physical Layout           │
│                                         │
│  ┌──────────────────────────────────┐   │
│  │         L2 SRAM Macros           │   │
│  │  [SRAM][SRAM][SRAM][SRAM][SRAM] │   │
│  └──────────────────────────────────┘   │
│                                         │
│  ┌──────────┐  ┌──────────┐            │
│  │ Weight   │  │Activation│            │
│  │ Buffer   │  │ Buffer   │            │
│  │ (SRAM)   │  │ (SRAM)   │            │
│  └──────────┘  └──────────┘            │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │         MAC Array (Standard Cells)│ │
│  │  [PE][PE][PE]...[PE]             │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌──────┐  ┌──────┐  ┌──────────────┐ │
│  │ DMA  │  │ MCU  │  │ Post-Proc    │ │
│  └──────┘  └──────┘  └──────────────┘ │
│                                         │
│  ═══ AXI Interface (PHY boundary) ════ │
└─────────────────────────────────────────┘
```

### 9.2 SRAM Macro Placement

SRAM macros are hard macros with fixed aspect ratios. Key constraints:

- **Proximity to MAC array:** minimize wire length for data delivery (timing, power)
- **Port access:** ensure abutment or short connection to MAC array feed wires
- **Power mesh:** SRAM is power-hungry; ensure robust PDN (Power Delivery Network)
- **ESD / pad ring:** if the NPU is a standalone chip, protect I/Os

### 9.3 Clock Distribution

NPU clock is typically:
- Sourced from the SoC PLL (or a dedicated NPU PLL)
- Distributed via an H-tree or balanced clock mesh
- Gated at multiple levels (core-level, array-level, PE-level)
- Target: < 5% clock skew across the MAC array

### 9.4 Power Delivery Network (PDN)

MAC arrays switching simultaneously cause massive simultaneous switching noise (SSN):

- **IR drop analysis:** voltage droop across the array during peak switching
- **On-chip decoupling capacitors (decap cells):** placed between SRAM macros and around MAC array
- **Bump/TSV planning (for 3D-IC):** ensure power bumps are directly above MAC arrays

### 9.5 Timing Closure Challenges

- **Long paths through MAC array:** accumulator carry chains
- **Crossings between clock domains:** MCU (low freq) to MAC array (high freq) — synchronizers required
- **Interface timing:** AXI protocol requires setup/hold on address and data buses

---

## 10. Software Stack Architecture

### 10.1 Full Stack Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│         (Python app, Android app, embedded C app)           │
├─────────────────────────────────────────────────────────────┤
│                  ML Framework API                           │
│     (TensorFlow Lite, PyTorch Mobile, ONNX Runtime)         │
├─────────────────────────────────────────────────────────────┤
│              Hardware Abstraction Layer (HAL)               │
│      (Android NNAPI, CoreML, OpenVX, DirectML)              │
├─────────────────────────────────────────────────────────────┤
│                  NPU Runtime Library                        │
│    (Memory management, graph scheduling, kernel dispatch)   │
├─────────────────────────────────────────────────────────────┤
│                  NPU Compiler / Backend                     │
│    (Graph optimization, quantization, code generation)      │
├─────────────────────────────────────────────────────────────┤
│                   Kernel / Driver Layer                     │
│      (Linux kernel driver, DMA management, IRQ handling)    │
├─────────────────────────────────────────────────────────────┤
│                   NPU Firmware (MCU)                        │
│      (Layer scheduler, HW programming, error handling)      │
├─────────────────────────────────────────────────────────────┤
│                   NPU Hardware (RTL → GDSII)                │
└─────────────────────────────────────────────────────────────┘
```

### 10.2 How an Inference Request Flows

```
1. App calls: interpreter.run()

2. Framework (TFLite):
   → Selects NPU delegate for supported ops
   → Passes tensor descriptors to delegate

3. NPU Runtime:
   → Allocates input/output buffers (DRAM-mapped)
   → Issues inference command to kernel driver

4. Kernel Driver:
   → Validates request
   → Programs DMA descriptors into NPU registers
   → Writes "go" to doorbell register
   → Puts calling thread to sleep (wait for IRQ)

5. NPU Firmware (MCU):
   → Receives doorbell interrupt
   → Reads command from mailbox
   → Programs hardware registers for layer 0
   → Arms DMA to fetch weights + activations

6. NPU Hardware:
   → DMA fetches data from DRAM to SRAM
   → MAC array computes
   → Post-processing unit applies activation, requantizes
   → DMA writes output back to DRAM
   → Signals MCU "layer done"

7. NPU Firmware:
   → Programs next layer, repeats until graph complete
   → Asserts interrupt to host CPU

8. Kernel Driver:
   → Receives interrupt
   → Wakes waiting thread

9. App receives results.
```

---

## 11. NPU Firmware

### 11.1 What Firmware Does

NPU firmware runs on the embedded MCU inside the NPU. It is the bridge between high-level commands from the host and low-level hardware register writes.

**Responsibilities:**
- **Command parsing:** read inference requests from the mailbox ring buffer
- **Layer scheduling:** decide the order of layer execution, handle branching (skip connections, multiple heads)
- **Register programming:** write to NPU control registers for each layer (dimensions, strides, addresses, precision)
- **DMA coordination:** configure DMA descriptors for each tile transfer
- **Synchronization:** ensure DMA completes before MAC starts, MAC completes before next layer
- **Error handling:** detect and report hardware errors (ECC faults, timeout, address violations)
- **Power management:** request DVFS transitions, control clock/power gating

### 11.2 Firmware Architecture

```
┌────────────────────────────────────────────┐
│              NPU MCU Firmware              │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │        Main Event Loop               │ │
│  │  while(1) {                          │ │
│  │    wait_for_event();                 │ │
│  │    dispatch(event_type);             │ │
│  │  }                                   │ │
│  └──────────────────────────────────────┘ │
│                                            │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Command  │  │  Layer   │  │  Error  │ │
│  │ Parser   │  │Scheduler │  │ Handler │ │
│  └──────────┘  └──────────┘  └─────────┘ │
│                                            │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │  DMA     │  │  HW Reg  │  │  Power  │ │
│  │  Driver  │  │  Driver  │  │  Mgmt   │ │
│  └──────────┘  └──────────┘  └─────────┘ │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │     RTOS (FreeRTOS / Zephyr / bare)  │ │
│  └──────────────────────────────────────┘ │
└────────────────────────────────────────────┘
```

### 11.3 Firmware Instruction Set (Micro-Command Format)

Many NPUs define a custom micro-command format that the compiler generates and firmware interprets:

```
Example micro-command (hypothetical 64-bit instruction):

Bits [63:60] Opcode     (CONV, POOL, GEMM, DMA_LOAD, DMA_STORE, SYNC, END)
Bits [59:48] Layer ID   (for dependency tracking)
Bits [47:32] Config Ptr (pointer to layer config structure in DRAM)
Bits [31:16] Input Buf  (buffer slot index)
Bits [15: 0] Output Buf (buffer slot index)
```

A full model is a sequence of such micro-commands. The compiler emits them; the firmware executes them.

### 11.4 Firmware Update and Security

In a production SoC:
- Firmware is stored in a dedicated ROM or signed flash partition
- Authenticated at boot (secure boot chain from ROM → bootloader → NPU firmware)
- Updates require cryptographic signature verification
- Firmware must not expose arbitrary register write capability to unprivileged software

---

## 12. Compiler Toolchain

### 12.1 Input: Model Formats

Compilers accept:
- **ONNX** (Open Neural Network Exchange): standard interchange format
- **TensorFlow SavedModel / TFLite FlatBuffer**
- **PyTorch TorchScript / ExportedProgram**
- **CoreML mlpackage** (Apple ecosystem)

### 12.2 Compiler Pipeline

```
  [Model: ONNX/TFLite]
         │
         ▼
  ┌──────────────────────────────────────┐
  │  1. Graph Import & Canonicalization  │
  │  - Parse model format                │
  │  - Normalize ops (e.g., BatchNorm    │
  │    folding into Conv weights)        │
  └──────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────┐
  │  2. Graph Optimization (HW-agnostic) │
  │  - Operator fusion (Conv+BN+ReLU)    │
  │  - Constant folding                  │
  │  - Dead code elimination             │
  │  - Common subexpression elimination  │
  └──────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────┐
  │  3. Quantization                     │
  │  - Post-training quantization (PTQ)  │
  │  - Quantization-aware training (QAT) │
  │  - Per-layer / per-channel scales    │
  │  - Sensitivity analysis              │
  └──────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────┐
  │  4. HW-Specific Lowering             │
  │  - Map ops to NPU primitives         │
  │  - Fallback to CPU for unsupported   │
  │  - Partition: NPU subgraph + CPU     │
  └──────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────┐
  │  5. Memory Planning                  │
  │  - Tensor lifetime analysis          │
  │  - Buffer reuse (live range coloring)│
  │  - DRAM vs. SRAM placement           │
  └──────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────┐
  │  6. Tiling & Scheduling              │
  │  - Tile size selection (roofline)    │
  │  - Layer ordering (fusion, pipelining│
  │  - DMA prefetch scheduling           │
  └──────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────┐
  │  7. Code Generation                  │
  │  - Emit micro-commands               │
  │  - Generate weight layouts (packed,  │
  │    padded, reordered for HW access)  │
  │  - Serialize to binary blob          │
  └──────────────────────────────────────┘
         │
         ▼
  [NPU Binary: micro-command stream + packed weights]
```

### 12.3 Operator Fusion

One of the highest-value compiler optimizations:

```
Without fusion:
  Conv2D → [write to DRAM] → BatchNorm → [write to DRAM] → ReLU → [write to DRAM]
  → 3 DRAM write + read round trips

With fusion:
  Conv2D+BatchNorm+ReLU (computed entirely on-chip in one pass)
  → 0 intermediate DRAM writes

Cost: compiler must prove it's safe (no side effects, compatible shapes)
```

**Common fuseable patterns:**
- `Conv → BN → ReLU` (ubiquitous in CNNs)
- `Conv → Add → ReLU` (residual connections)
- `Linear → GELU` (transformer FFN)
- `Matmul → Scale → Softmax` (attention)

### 12.4 Quantization in the Compiler

**Post-Training Quantization (PTQ):**
1. Run calibration dataset through FP32 model
2. Collect activation statistics (min, max, histogram)
3. Compute optimal scale and zero-point per layer
4. No retraining needed; accuracy drop acceptable for most models

**Quantization-Aware Training (QAT):**
1. Insert "fake quantize" nodes in training graph
2. Forward pass simulates quantization error
3. Gradients flow through (straight-through estimator)
4. Model learns to compensate for quantization
5. Higher accuracy, requires access to training pipeline

**Layer-wise sensitivity:**
```python
# Compiler sensitivity sweep (pseudo-code)
for layer in model.layers:
    with layer quantized to INT4:
        accuracy = evaluate(model, calibration_data)
    if accuracy < threshold:
        keep_layer_at_INT8_or_FP16(layer)
```

### 12.5 Weight Packing

The compiler reorganizes weights from the training format (OIHW) to the hardware-optimal format:

```
Training layout: Weight[Out_ch][In_ch][KH][KW] — PyTorch default
Hardware needs:  Weight[tile_Out][tile_In][KH][KW][vec_In] — for vectorized access

Transformation:
1. Pad output channels to multiple of vector width (e.g., 16)
2. Pad input channels similarly
3. Interleave for simultaneous access by MAC lanes
4. Convert to target precision (INT8, INT4, BF16)

This is done ONCE at compile time. Runtime only reads pre-packed weights.
```

---

## 13. Runtime & Driver Layer

### 13.1 Kernel Driver Responsibilities

The NPU kernel driver (running in Linux/RTOS kernel space):

```c
// Typical driver operations:
npu_open()       // Initialize device, map registers, register IRQ handler
npu_ioctl()      // Handle user-space commands (submit inference, query status)
npu_mmap()       // Map NPU DRAM buffer to user space (zero-copy)
npu_irq_handler()// Handle completion interrupt, wake waiting process
npu_probe()      // Device tree / ACPI enumeration, power on
npu_remove()     // Power off, unmap, unregister
```

**Memory management:**
- Allocate physically contiguous buffers (DMA-able)
- Map IOVA (I/O Virtual Address) for NPU DMA
- Handle IOMMU configuration (protect DRAM from NPU misbehavior)
- Cache maintenance (flush before NPU read, invalidate before CPU read)

### 13.2 NPU Runtime Library

Runs in user space, provides the programming interface for the NPU compiler's output:

**Functions:**
- Load model binary blob into memory
- Allocate I/O tensor buffers
- Set input data
- Run inference (synchronous or asynchronous)
- Read output data
- Profile latency and performance counters
- Manage multiple concurrent model instances

**Session lifecycle:**
```
npu_session_create(model_binary)
  → Validates binary, allocates DRAM for weights, creates command queues

npu_session_set_input(session, tensor_index, data_ptr)
  → Copies or maps input data to NPU-accessible buffer

npu_session_run(session)
  → Submits commands to driver, waits for completion

npu_session_get_output(session, tensor_index)
  → Returns pointer to output buffer in NPU DRAM mapping

npu_session_destroy(session)
  → Free all resources
```

### 13.3 Asynchronous Inference

For pipelining (e.g., process camera frames continuously):

```
Frame N:   Submit → [NPU computing] → Completion callback → Read output
Frame N+1: Submit while N is computing (if double-buffered I/O)
Frame N+2: Queued in driver ring buffer
```

Requires careful synchronization between CPU (reading results) and NPU (writing them).

---

## 14. APIs & Frameworks

### 14.1 Android NNAPI

Android's standard hardware abstraction layer for neural network inference:

```
App (TFLite / ONNX Runtime)
     ↓ via TFLite NNAPI delegate
Android NNAPI (libneuralnetworks.so)
     ↓ calls vendor HAL
libNPUHAL.so   (SoC vendor implements this)
     ↓ calls runtime
NPU Runtime + Driver
     ↓
NPU Hardware
```

Vendor requirement: implement the NNAPI HAL interface (`IDevice`, `IPreparedModel`, `IBurst`)

### 14.2 Apple CoreML

Closed stack on Apple Silicon:
- App → CoreML framework → ANE (Apple Neural Engine) via private IOKit driver
- Compiler: `coremlcompiler` converts CoreML model to `.mlmodelc` (compiled binary for ANE)
- No public API to directly program the ANE — all through CoreML

### 14.3 OpenCL / OpenVX

For vendors who want a standard cross-platform interface:

- **OpenCL:** general compute API, extended by `cl_khr_nn_layer` extensions for neural ops
- **OpenVX:** computer vision operations including neural network inference (`vxConvolutionLayer`, etc.)
- Less commonly used now that framework-specific delegates dominate

### 14.4 ONNX Runtime Execution Providers

ONNX Runtime uses "Execution Providers" to dispatch ops to accelerators:

```python
import onnxruntime as ort

# Standard providers: CPUExecutionProvider, CUDAExecutionProvider
# Custom NPU provider:
sess = ort.InferenceSession("model.onnx",
    providers=["NPUExecutionProvider", "CPUExecutionProvider"])
# → ONNX Runtime dispatches NPU-supported ops to NPU,
#   falls back to CPU for unsupported ops
```

Implementing a custom Execution Provider requires:
1. Implementing the `IExecutionProvider` C++ interface
2. Registering supported op types and shapes
3. Handling memory allocation and data transfer
4. Wrapping NPU runtime calls

### 14.5 TensorFlow Lite Delegates

Similar pattern to ONNX Runtime:

```c
// Vendor implements:
TfLiteDelegate* NPUDelegateCreate(const NPUDelegateOptions* options);

// Inside delegate:
// - Inspect supported ops (ConvParams, FullyConnectedParams, etc.)
// - Claim subgraph
// - On inference: compile claimed subgraph on first run, then execute
```

### 14.6 Compile-Time vs. Runtime Compilation

| | **AOT (Ahead-of-Time)** | **JIT (Just-in-Time)** |
|---|---|---|
| When | Before deployment | On first inference |
| Latency | Zero at runtime | Compilation adds first-run latency |
| Optimization | Full (knows target HW) | Can adapt to dynamic shapes |
| Used by | Qualcomm SNPE, Apple ANE | TFLite NNAPI delegate |
| Common for | Mobile edge NPUs | Cloud inference |

---

## 15. Real-World NPU Architectures

### 15.1 Google TPU

- **Architecture:** 256×256 systolic array (65,536 MACs)
- **Precision:** INT8 / BF16
- **Memory:** 32 MB on-chip SRAM (Unified Buffer), 900 GB/s internal bandwidth
- **Key insight:** massive batch size → very high weight reuse → dominates DRAM traffic
- **Stack:** XLA compiler → TensorFlow → TPU runtime
- **Lesson:** systolic arrays work great for LLM/transformer workloads with large batches

### 15.2 Apple Neural Engine (ANE)

- **Architecture:** proprietary, likely vector-based with dedicated attention support
- **Performance:** 38 TOPS (A17 Pro), tightly integrated with CoreML
- **Key insight:** compiler does everything offline; runtime is extremely thin
- **Stack:** CoreML → `.mlmodelc` binary → IOKit driver → ANE hardware
- **Lesson:** vertical integration allows extreme optimization; no programmer access needed

### 15.3 Qualcomm Hexagon NPU (HTP - Hexagon Tensor Processor)

- **Architecture:** combination of vector and scalar DSP + dedicated tensor accelerator
- **Precision:** INT8, INT16, FP16
- **Key insight:** tightly coupled with the Hexagon DSP for flexibility in custom ops
- **Stack:** SNPE (Snapdragon Neural Processing Engine) / QNN SDK → HTP driver

### 15.4 Arm Ethos-N / Ethos-U

- **Ethos-N:** for high-performance mobile SoCs (>1 TOPS)
  - Architecture: engine core array with MAC units
  - Stack: Arm NN, ONNX Runtime Ethos delegate
- **Ethos-U:** microNPU for MCUs (<1 TOPS, mW power budget)
  - Designed to fit in Cortex-M based systems
  - Stack: TFLite Micro + Vela compiler

### 15.15 NVIDIA Orin DLA (Deep Learning Accelerator)

- **Architecture:** two DLA cores alongside GPU (Ampere) and PVA
- **Precision:** INT8, FP16
- **Key insight:** NPU used for steady-state inference; GPU for flexible/novel workloads
- **Stack:** TensorRT compiles to DLA + GPU split binary

---

## 16. Designing Your Own NPU — A Practical Checklist

### Step 1: Define the Target Workload

```
□ What models? (MobileNet, ResNet, YOLO, BERT, LLaMA…)
□ Quantization? (FP16, INT8, INT4, mixed)
□ Batch size? (1 for edge, 8-128 for server)
□ Latency budget? (10ms realtime, 100ms interactive, 1s offline)
□ Power envelope? (1mW MCU, 100mW mobile, 10W edge, 100W server)
□ Accuracy constraints? (what accuracy drop is acceptable?)
```

### Step 2: Compute Architecture

```
□ Choose array style: systolic (matmul-heavy) vs vector (flexible)
□ Dimension the MAC array: target TOPS / frequency → number of PEs
□ Choose primary dataflow: WS, OS, IS, RS, or hybrid
□ Define accumulator width (INT8 → INT32, BF16 → FP32)
□ Specify precision support: what data types are mandatory?
□ Sparsity support? (structured 2:4 recommended if justified)
```

### Step 3: Memory Architecture

```
□ Size on-chip SRAM: model the working set of critical layers
□ Structure: L1 per-core + shared L2? Or flat?
□ Banking: number of banks = MAC array width / SRAM port width
□ Double-buffer: yes if DRAM latency > compute time per tile
□ DMA: strided, gather-scatter? Prefetch depth?
□ DRAM interface: bandwidth target = compute_demand / arithmetic_intensity
```

### Step 4: Post-Processing Units

```
□ Activation functions: which ones? (ReLU, GELU, Sigmoid, SiLU)
□ Normalization: Layer norm, Batch norm, RMS norm?
□ Softmax: hardware `exp()` or polynomial approximation?
□ Requantization: INT32 → INT8 (scale, bias, clip, round)
□ All in one pass with MAC (fused) or separate unit?
```

### Step 5: Control & Programmability

```
□ MCU selection: RISC-V (open, flexible) or Cortex-M (ecosystem)?
□ Instruction set: custom micro-commands? TLB-based DMA descriptors?
□ Interrupt architecture: layer completion, DMA completion, error
□ Debug: performance counters, event tracing, logic analyzer taps?
□ Secure boot / firmware authentication?
```

### Step 6: SoC Integration

```
□ Host interface: AXI4-Lite (config) + AXI4 (DMA master)
□ Coherency: non-coherent (add CMO to driver) or ACE (add snoop logic)?
□ Power domains: NPU in separate power domain for gating
□ DVFS: voltage/frequency scaling interface to PMIC
□ Clock: from system PLL or dedicated NPU PLL?
□ IOMMU: protect DRAM from DMA out-of-bounds
```

### Step 7: Verification Plan

```
□ Unit tests: each functional block (MAC, DMA, post-proc)
□ Layer tests: each layer type (Conv, FC, Pool, BN, Attention)
□ Model-level tests: full model inference vs. floating-point golden
□ Power estimation: toggle rate analysis on netlist
□ Performance model: cycle-accurate simulator before RTL
□ Coverage: functional coverage goals (all op types, all precisions, edge cases)
```

### Step 8: Software Stack (Minimum Viable)

```
□ Firmware: bare-metal C on MCU, register driver layer
□ Kernel driver: Linux char device, DMA allocation, IRQ
□ Compiler backend: ONNX import → graph optimization → tiling → micro-command emit
□ Runtime: session API, buffer management, synchronization
□ Validation: bitexact comparison vs. FP32 reference for all test models
□ Performance profiling: cycle counter, memory bandwidth meter
```

---

## Appendix: Key Formulas Reference

**Arithmetic Intensity (Operations per Byte):**
```
AI = (2 × MACs) / (bytes_read_from_DRAM)
```

**Roofline Bound:**
```
Perf = min(Peak_TOPS, AI × DRAM_BW)
```

**MAC Array Throughput:**
```
Throughput_TOPS = N_PEs × 2 × Frequency / 1e12
```

**SRAM Area (rough, process-dependent):**
```
Area_mm² ≈ Capacity_MB × 0.5  (at 7nm SRAM density ~4 Mbit/mm²)
```

**Memory Bandwidth Required:**
```
BW_required = (Weight_bytes + Activation_bytes) / inference_time
```

**Energy Per Inference:**
```
E_total = E_compute + E_SRAM + E_DRAM
        = N_MACs × E_MAC + N_SRAM_accesses × E_SRAM + N_DRAM_bytes × E_DRAM_per_byte
```

**Utilization:**
```
Utilization = Effective_TOPS / Peak_TOPS
            = 1 - (stall_cycles / total_cycles)
```

---

*Document version: 1.0 | Last updated: May 2026 | Scope: NPU ASIC Design Reference*

MultiZone est développé et détenu par Hex Five Security, une startup américaine. C'est leur produit commercial — ils ont un SDK open source sur GitHub pour attirer les développeurs, mais le cœur du monitor est sous licence propriétaire pour la production.
Ce n'est pas un standard, pas une spécification communautaire, pas un projet de la RISC-V Foundation.

RISC-V International  (standards)
│
├── ISA + extensions (M/S/U modes, PMP, ...)   ← standard
│
└── Pas de TEE standard défini
    │
    ├── MultiZone    (Hex Five)    ← commercial, propriétaire
    ├── Keystone     (UC Berkeley) ← académique, open source
    ├── Penglai      (Shanghai)    ← académique, open source
    └── ...          (d'autres)    ← aucune dominance claire




# MultiZone Security: Architectural Overview and Core Concepts
### RISC-V Trusted Execution Environment

**Document type:** Technical Architecture Reference  
**Audience:** Senior Software and Systems Architects  
**Scope:** Conceptual and architectural — implementation details are intentionally excluded

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Foundational Concepts: RISC-V Privilege Architecture and PMP](#2-foundational-concepts-risc-v-privilege-architecture-and-pmp)
3. [MultiZone in the TEE Landscape](#3-multizone-in-the-tee-landscape)
4. [High-Level Architectural Vision](#4-high-level-architectural-vision)
5. [Core Components and Their Roles](#5-core-components-and-their-roles)
   - 5.1 [The MultiZone Security Monitor](#51-the-multizone-security-monitor)
   - 5.2 [Zones](#52-zones)
   - 5.3 [The Zone Manifest](#53-the-zone-manifest)
   - 5.4 [Inter-Zone Communication (Mailbox)](#54-inter-zone-communication-mailbox)
   - 5.5 [The MultiZone SDK and HAL](#55-the-multizone-sdk-and-hal)
6. [The MultiZone API Model](#6-the-multizone-api-model)
   - 6.1 [The Inter-Zone Messaging API](#61-the-inter-zone-messaging-api)
   - 6.2 [Zone Lifecycle and Entry Points](#62-zone-lifecycle-and-entry-points)
7. [Inter-Zone Communication Model](#7-inter-zone-communication-model)
8. [Security Architecture and Trust Model](#8-security-architecture-and-trust-model)
9. [MultiZone vs OP-TEE: An Architectural Comparison](#9-multizone-vs-op-tee-an-architectural-comparison)
10. [Summary of GitHub Repositories](#10-summary-of-github-repositories)
11. [Conclusion](#11-conclusion)

---

## 1. Introduction

MultiZone Security is a software-defined Trusted Execution Environment for RISC-V processors, developed by **Hex Five Security**. Unlike ARM TrustZone — which enforces a binary Normal World / Secure World split at the hardware bus level — MultiZone leverages the **Physical Memory Protection (PMP)** mechanism native to the RISC-V specification to partition a single processor into **multiple, mutually isolated execution zones**, each with its own memory, peripherals, and trust level.

MultiZone is architecturally significant for several reasons:

- It operates entirely within the **Machine mode privilege layer**, requiring no hardware modifications to a standard RISC-V core.
- It supports **N independent zones** rather than a fixed two-world model, offering finer-grained decomposition of security domains.
- It is designed for **resource-constrained embedded and IoT systems** where a full TEE kernel such as OP-TEE would be impractical.
- It is **not GlobalPlatform-conformant** by design — it defines its own, simpler API model tailored to the RISC-V execution model.

```
  One-sentence purpose of MultiZone
  ──────────────────────────────────────────────────────────────
  Partition a single RISC-V core into N isolated security domains
  using only standard hardware features, with zero hardware modifications.
  ──────────────────────────────────────────────────────────────
```

> ### 📌 Rules to Remember — §1
> - MultiZone is **not a GlobalPlatform TEE**: it solves the same class of problem (isolated execution) with a different architecture and a different API model.
> - The isolation model is **N zones**, not 2 worlds: this is the fundamental structural difference from TrustZone-based systems.
> - MultiZone requires **no hardware modifications**: it is a software security monitor that runs on any standards-compliant RISC-V core with PMP support.
> - The target environment is **embedded / IoT**, not application processors: the design deliberately trades feature richness for minimal footprint and simplicity.

---

## 2. Foundational Concepts: RISC-V Privilege Architecture and PMP

Before examining MultiZone itself, it is essential to understand the two RISC-V hardware mechanisms it builds upon: the **privilege level hierarchy** and the **Physical Memory Protection (PMP)** unit.

### 2.1 RISC-V Privilege Levels

The RISC-V architecture defines up to four privilege levels, ordered by decreasing authority:

| Level | Name | Typical occupant |
|-------|------|-----------------|
| 3 | **Machine mode (M-mode)** | Firmware, security monitor, bootloader |
| 2 | Hypervisor mode (H-mode) | Hypervisor (optional extension) |
| 1 | **Supervisor mode (S-mode)** | OS kernel (Linux, RTOS) |
| 0 | **User mode (U-mode)** | Application code |

M-mode is the most privileged and is always present. It is the **only mode that can configure the PMP**. This is the privilege level at which the MultiZone Security Monitor executes.

```
  RISC-V privilege hierarchy

  ┌────────────────────────────────────────────────────────────┐
  │  M-mode  (Machine)    ← highest privilege                  │
  │  ─────────────────────────────────────────────────────     │
  │  • Full access to all hardware registers and memory        │
  │  • Only level that can configure PMP entries               │
  │  • Handles all traps and interrupts at the lowest level    │
  │  • MultiZone Security Monitor resides here                 │
  ├────────────────────────────────────────────────────────────┤
  │  S-mode  (Supervisor)                                      │
  │  ─────────────────────────────────────────────────────     │
  │  • OS kernels, RTOS schedulers                             │
  │  • Constrained by PMP entries set in M-mode               │
  ├────────────────────────────────────────────────────────────┤
  │  U-mode  (User)       ← lowest privilege                   │
  │  ─────────────────────────────────────────────────────     │
  │  • Application code                                        │
  │  • Most constrained by PMP                                 │
  └────────────────────────────────────────────────────────────┘
  Privilege escalation: ecall instruction (upward only)
  Privilege reduction:  return from trap / mret instruction
```

### 2.2 Physical Memory Protection (PMP)

PMP is a RISC-V standard mechanism that allows M-mode software to define memory access rules for lower privilege levels. A PMP configuration consists of a set of **entries** (typically 8 or 16), each specifying:

- A **memory address range**
- **Permission flags**: Read (R), Write (W), Execute (X)
- A **matching mode**: exact address, top-of-range, or power-of-two-aligned range (NAPOT)

```
  PMP: the hardware foundation of MultiZone isolation

  M-mode sets PMP entries at boot (only M-mode can write PMP CSRs):

  PMP Entry 0:  0x20000000 – 0x20003FFF   R-X   → Zone 1 code
  PMP Entry 1:  0x20010000 – 0x20013FFF   RW-   → Zone 1 data
  PMP Entry 2:  0x20004000 – 0x20007FFF   R-X   → Zone 2 code
  PMP Entry 3:  0x20014000 – 0x20017FFF   RW-   → Zone 2 data
  PMP Entry 4:  0x20008000 – 0x2000BFFF   R-X   → Zone 3 code
  ...
  PMP Entry N:  all else                  ---   → DENY (default)

  When a zone executes:
  ┌────────────────────────────────────────────────────────────┐
  │  Zone 1 attempts to read Zone 2 data region               │
  │  PMP check: Zone 2 data → no R permission for Zone 1      │
  │  → Hardware raises a Load Access Fault                    │
  │  → Monitor traps, terminates the offending zone            │
  └────────────────────────────────────────────────────────────┘
```

The critical architectural point is that **PMP enforcement is hardware**: once PMP entries are set by M-mode, no S-mode or U-mode code can alter them, circumvent them, or read the M-mode configuration registers. Isolation is enforced by the processor on every memory access.

> ### 📌 Rules to Remember — §2
> - **M-mode is the absolute root of privilege** in RISC-V: it is the only mode that configures PMP. The MultiZone monitor owns M-mode entirely.
> - PMP is **per-access hardware enforcement**: every load, store, and instruction fetch is checked against PMP entries on the silicon — not in software.
> - PMP has **a fixed number of entries** (typically 8–16): the number of configurable zones is bounded by this hardware constraint.
> - Unlike TrustZone's bus-level NS bit, PMP is a **CPU-local mechanism**: it does not propagate to DMA engines or bus masters by default. Peripheral isolation requires additional configuration (IOPMP or platform-specific mechanisms).
> - There is **no dedicated world-switch instruction** in RISC-V: MultiZone uses the standard trap/return mechanism (`ecall` / `mret`) — the monitor intercepts these and performs zone switching.

---

## 3. MultiZone in the TEE Landscape

### 3.1 Position in the RISC-V Security Ecosystem

RISC-V is a young but rapidly evolving architecture. At the time of writing, it lacks a hardware security extension as mature and pervasive as ARM TrustZone. The ecosystem offers several security approaches:

```
  RISC-V security landscape

  ┌────────────────────────────────────────────────────────────┐
  │  Hardware-assisted isolation mechanisms on RISC-V          │
  │                                                            │
  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
  │  │  PMP         │  │  IOPMP       │  │  RISC-V         │  │
  │  │  (standard)  │  │  (extension) │  │  Hypervisor     │  │
  │  │              │  │              │  │  (H extension)  │  │
  │  │  CPU memory  │  │  DMA / bus   │  │  VM isolation   │  │
  │  │  isolation   │  │  isolation   │  │  (S/HS modes)   │  │
  │  └──────┬───────┘  └──────────────┘  └─────────────────┘  │
  └─────────┼──────────────────────────────────────────────────┘
            │  exploited by
  ┌─────────▼──────────────────────────────────────────────────┐
  │  TEE / security monitor implementations                    │
  │                                                            │
  │  ┌──────────────────┐   ┌───────────────────────────────┐  │
  │  │  MultiZone       │   │  Keystone                     │  │
  │  │  (Hex Five)      │   │  (UC Berkeley / open source)  │  │
  │  │                  │   │                               │  │
  │  │  N-zone model    │   │  Enclave model                │  │
  │  │  M-mode monitor  │   │  M-mode security monitor      │  │
  │  │  commercial      │   │  research / open source       │  │
  │  └──────────────────┘   └───────────────────────────────┘  │
  │                                                            │
  │  ┌──────────────────────────────────────────────────────┐  │
  │  │  OpenSBI  (not a TEE — firmware/SBI interface only)  │  │
  │  └──────────────────────────────────────────────────────┘  │
  └────────────────────────────────────────────────────────────┘
```

### 3.2 Relationship to GlobalPlatform

MultiZone does **not** implement the GlobalPlatform TEE specifications. There is no TEE Client API, no TEE Internal Core API, and no concept of a GP-conformant Trusted Application. MultiZone defines its own, considerably simpler API based on **inter-zone message passing**.

This is a deliberate design decision: GlobalPlatform specifications were designed for application-class ARM processors. Implementing the full GP stack on a microcontroller-class RISC-V core with 64–256 KB of RAM would be architecturally inappropriate. MultiZone trades standardisation for **minimal footprint and simplicity of reasoning**.

> ### 📌 Rules to Remember — §3
> - MultiZone is **not GlobalPlatform-conformant**: it does not implement the TEE Client API or Internal Core API. Code written for OP-TEE is not portable to MultiZone without a full rewrite.
> - The RISC-V TEE ecosystem is **less standardised than ARM**: there is no single dominant TEE implementation. MultiZone and Keystone serve different market and architectural niches.
> - **OpenSBI is not a TEE**: it is a firmware abstraction layer (Supervisor Binary Interface). Conflating it with MultiZone or Keystone is a common architectural error.
> - The absence of GlobalPlatform conformance is a **design choice, not a deficiency**: GlobalPlatform's API surface is too heavy for the constrained embedded systems MultiZone targets.

---

## 4. High-Level Architectural Vision

The MultiZone architecture replaces the two-world binary model of TrustZone with a **multi-zone partition model**. A single physical RISC-V core is divided into N independent zones, each completely isolated from all others, with all inter-zone interaction mediated by the Security Monitor.

```
  MultiZone: N isolated zones on a single RISC-V core

  ┌─────────────────────────────────────────────────────────────┐
  │  PHYSICAL RISC-V PROCESSOR                                  │
  │                                                             │
  │  ┌─────────────────────────────────────────────────────┐   │
  │  │  M-MODE: MultiZone Security Monitor                  │   │
  │  │  ─────────────────────────────────────────────────   │   │
  │  │  • Owns and configures all PMP entries               │   │
  │  │  • Arbitrates all zone switches                      │   │
  │  │  • Routes all inter-zone messages                    │   │
  │  │  • Handles all traps and faults                      │   │
  │  │  • Enforces zone manifest policy                     │   │
  │  └──────────────────────┬──────────────────────────────┘   │
  │                         │  PMP-enforced boundaries          │
  │    ┌────────────────────┼─────────────────────────────┐    │
  │    │                    │                             │    │
  │    ▼                    ▼                             ▼    │
  │  ┌────────────┐  ┌─────────────┐  ...  ┌───────────────┐  │
  │  │  Zone 1    │  │  Zone 2     │       │  Zone N       │  │
  │  │            │  │             │       │               │  │
  │  │  e.g.:     │  │  e.g.:      │       │  e.g.:        │  │
  │  │  RTOS /    │  │  Crypto /   │       │  Network /    │  │
  │  │  Main App  │  │  Key mgmt   │       │  Comms stack  │  │
  │  │            │  │             │       │               │  │
  │  │  S/U-mode  │  │  S/U-mode   │       │  S/U-mode     │  │
  │  └─────┬──────┘  └──────┬──────┘       └──────┬────────┘  │
  │        │                │                     │           │
  │        └────────────────┴─────────────────────┘           │
  │              No direct zone-to-zone access.                │
  │              All communication via Monitor mailbox.        │
  └─────────────────────────────────────────────────────────────┘
```

The key architectural invariant is absolute: **no zone can directly read or write another zone's memory**. All cross-zone interaction is mediated by the Security Monitor through an explicit, asynchronous message-passing mechanism. The Monitor itself is the sole component that can see and reconfigure the PMP layout.

```
  Conceptual contrast: TrustZone (2 worlds) vs MultiZone (N zones)

  TrustZone                          MultiZone
  ─────────────────────────          ─────────────────────────
  Normal World │ Secure World        Zone 1 │ Zone 2 │ Zone N
  ─────────────┼─────────────        ───────┼────────┼───────
  hardware bus │ hardware bus        PMP    │ PMP    │ PMP
  NS bit on    │ NS bit off          entry  │ entry  │ entry
  entire bus   │                     per    │ per    │ per
               │                     zone   │ zone   │ zone
  Boundary:    │                     Boundary:
  fixed (2)    │                     configurable (N, N ≤ PMP entries)
```

> ### 📌 Rules to Remember — §4
> - The fundamental structural shift: **2 fixed worlds (TrustZone) → N configurable zones (MultiZone)**. This enables finer-grained decomposition of trust domains.
> - The Monitor is the **only component with a global view**: it is the single entity that knows the full memory map and can communicate with all zones.
> - **Zones are mutually blind**: Zone 1 has no knowledge of Zone 2's existence, memory layout, or code. All it can do is send a message to a named slot and wait for a reply.
> - Read the architecture **from the Monitor downward**: PMP policy flows top-down (Monitor → zones), data flows laterally via mailboxes (zone → Monitor → zone).

---

## 5. Core Components and Their Roles

### 5.1 The MultiZone Security Monitor

**Role and Responsibility**

The MultiZone Security Monitor is the **Trusted Computing Base** of the entire system. It executes exclusively in M-mode and is the first piece of software to run after reset. Its responsibilities are comprehensive and exclusive:

- **PMP configuration:** At boot, the Monitor reads the zone manifest and programs the PMP entries that define every zone's memory boundaries and access permissions. These entries are never modified at runtime.
- **Zone switching:** The Monitor implements a cooperative or preemptive scheduler that decides which zone executes at any given time. Each context switch involves saving the full CPU register state of the outgoing zone and restoring that of the incoming zone.
- **Trap and fault handling:** All `ecall` instructions, page faults, access faults, and hardware interrupts are routed to the Monitor first. It decides how to handle or forward each event.
- **Mailbox arbitration:** The Monitor owns the inter-zone message queues. No message is ever transferred directly between zones — the Monitor copies it, validates it, and delivers it.
- **Peripheral assignment:** The Monitor statically assigns peripherals (UART, SPI, GPIO, crypto accelerators) to zones. A zone that attempts to access a peripheral it does not own triggers a fault.

```
  Security Monitor: the sole M-mode resident

  ┌──────────────────────────────────────────────────────────────┐
  │  MultiZone Security Monitor  (M-mode, always resident)       │
  │                                                              │
  │  ┌──────────────────┐  ┌───────────────┐  ┌─────────────┐  │
  │  │  PMP Manager     │  │  Trap Handler │  │  Scheduler  │  │
  │  │                  │  │               │  │             │  │
  │  │  Programs all    │  │  All ecall,   │  │  Context    │  │
  │  │  PMP entries     │  │  faults,      │  │  switch:    │  │
  │  │  from manifest   │  │  IRQ → here   │  │  save/rest. │  │
  │  │  (boot only)     │  │               │  │  registers  │  │
  │  └──────────────────┘  └───────────────┘  └─────────────┘  │
  │                                                              │
  │  ┌──────────────────────────────────────────────────────┐   │
  │  │  Mailbox Router                                       │   │
  │  │  Validates and copies messages between zone queues    │   │
  │  │  Never passes pointers — only value-copied payloads   │   │
  │  └──────────────────────────────────────────────────────┘   │
  │                                                              │
  │  Footprint: typically < 4 KB  (entire monitor)              │
  └──────────────────────────────────────────────────────────────┘
```

The Monitor's footprint is intentionally tiny — typically under 4 KB of code. This minimalism is not accidental: **a smaller Monitor means a smaller attack surface and a more auditable TCB**.

**GitHub Repository:** [`hex-five/multizone-sdk`](https://github.com/hex-five/multizone-sdk) — `bsp/` and core monitor sources

> ### 📌 Rules to Remember — §5.1
> - The Monitor is the **entire TCB**: it is the only component that must be trusted unconditionally. If it is compromised, all zone isolation guarantees collapse.
> - The Monitor's tiny footprint (< 4 KB) is a **design invariant, not a limitation**: it is the primary means of keeping the TCB auditable and verifiable.
> - The Monitor **never executes zone code**: it is purely a supervisor and router. It does not implement application logic.
> - PMP entries are set **once at boot from the manifest** and never changed at runtime. This makes the isolation policy static and auditable — no runtime zone escalation is possible.

---

### 5.2 Zones

**Role and Responsibility**

Zones are the fundamental unit of isolated execution in MultiZone. Each zone is an independent software component — it may contain a bare-metal application, an RTOS instance, a network stack, a cryptographic service, or any combination thereof. Zones execute at S-mode or U-mode privilege and have no knowledge of the Monitor or of other zones beyond what the mailbox API exposes.

```
  Zone anatomy

  ┌──────────────────────────────────────────────────────────┐
  │  Zone N  (S-mode / U-mode)                               │
  │                                                          │
  │  ┌──────────────────────────────────────────────────┐   │
  │  │  Application / RTOS / service code               │   │
  │  │  (arbitrary — bare metal, FreeRTOS, Zephyr, ...) │   │
  │  └──────────────────────────────────────────────────┘   │
  │                                                          │
  │  Private memory regions (PMP-enforced):                  │
  │  ┌───────────────┐  ┌──────────────┐  ┌─────────────┐  │
  │  │  Code (.text) │  │  Data (.bss) │  │  Stack      │  │
  │  │  R-X, zone-   │  │  RW-, zone-  │  │  RW-, zone- │  │
  │  │  exclusive    │  │  exclusive   │  │  exclusive  │  │
  │  └───────────────┘  └──────────────┘  └─────────────┘  │
  │                                                          │
  │  Assigned peripherals (manifest-defined):                │
  │  e.g. Zone 1 owns UART0, Zone 2 owns SPI0 + AES accel.  │
  │                                                          │
  │  Inter-zone interface: mailbox API only                  │
  │  MULTIZONE_SEND() / MULTIZONE_RECV() / MULTIZONE_YIELD() │
  └──────────────────────────────────────────────────────────┘
```

Zones are stateless with respect to each other: a zone crash or misbehaviour is contained within its PMP boundary. The Monitor detects the fault, terminates the offending zone, and can optionally restart it — without affecting other zones.

**GitHub Repository:** [`hex-five/multizone-sdk`](https://github.com/hex-five/multizone-sdk) — `zone*/` directories contain per-zone application templates

> ### 📌 Rules to Remember — §5.2
> - A zone is **a complete, self-contained execution environment**: it can run an RTOS, a bare-metal loop, or a complex protocol stack — the Monitor does not care.
> - Zones execute at **S-mode or U-mode**: they can never elevate themselves to M-mode. Any attempt to write M-mode CSRs (including PMP registers) raises an illegal instruction fault caught by the Monitor.
> - **Zone failure is contained**: a fault in Zone 2 does not affect Zone 1. Fault containment is a direct consequence of PMP isolation, not of software error handling.
> - Zones have **no shared state by default**: all data exchange is explicit, message-based, and Monitor-mediated. There are no implicit shared memory regions between zones.

---

### 5.3 The Zone Manifest

**Role and Responsibility**

The Zone Manifest is a **static, compile-time configuration artifact** that fully defines the security policy of the system. It is consumed by the MultiZone build toolchain to generate the PMP configuration that the Monitor programs at boot. The manifest encodes:

- The number of zones and their identity
- The memory regions assigned to each zone (code, data, stack, heap)
- The peripheral assignments per zone
- Inter-zone communication permissions (which zones may send messages to which)
- Zone scheduling parameters (time slice, priority)

```
  Zone Manifest: the static root of the security policy

  ┌──────────────────────────────────────────────────────────────┐
  │  Zone Manifest  (compile-time artifact)                      │
  │                                                              │
  │  zone[1]:                                                    │
  │    code:  0x20000000 – 0x20003FFF   R-X                      │
  │    data:  0x20010000 – 0x20013FFF   RW-                      │
  │    peripheral: UART0                                         │
  │    can_send_to: [2, 3]                                       │
  │    timeslice: 1ms                                            │
  │                                                              │
  │  zone[2]:                                                    │
  │    code:  0x20004000 – 0x20007FFF   R-X                      │
  │    data:  0x20014000 – 0x20017FFF   RW-                      │
  │    peripheral: SPI0, AES_ACCEL                               │
  │    can_send_to: [1]                                          │
  │    timeslice: 1ms                                            │
  │                          │                                   │
  │                          │  consumed at build time           │
  │                          ▼                                   │
  │              PMP entry table baked into Monitor binary       │
  └──────────────────────────────────────────────────────────────┘
                             │  loaded at boot
                             ▼
                  Monitor programs PMP CSRs
                  (immutable from this point)
```

The manifest is the **single authoritative source of truth** for the system's security topology. Because it is static and compile-time-bound, it can be formally analysed and audited independently of any runtime behaviour.

> ### 📌 Rules to Remember — §5.3
> - The manifest is the **security policy in its entirety**: if you understand the manifest, you understand what the system can and cannot do.
> - Manifests are **static and compile-time**: there is no dynamic zone creation, no runtime policy modification, no escalation. This simplicity is a security feature.
> - The manifest is the **input to formal verification**: its static nature means the full isolation policy can be reasoned about exhaustively before deployment.
> - **Changing the manifest requires a full rebuild and reflash**: this is intentional — runtime policy changes would introduce a dynamic attack surface.

---

### 5.4 Inter-Zone Communication (Mailbox)

**Role and Responsibility**

The mailbox subsystem is the **only channel through which zones can interact**. It provides an asynchronous, fixed-size, value-copied message-passing mechanism. The Monitor owns the mailbox infrastructure: it maintains a message queue per zone-pair direction, validates message routing against the manifest policy, and copies payloads between zones during context switches.

```
  Mailbox: Monitor-mediated, copy-based, policy-enforced

  Zone 1 wants to send a message to Zone 2:

  ┌──────────────────────────────────────────────────────────────┐
  │  Zone 1  (sender)                                            │
  │  MULTIZONE_SEND(2, payload[4])  → ecall to Monitor           │
  └──────────────────────────────────┬───────────────────────────┘
                                     │ trap → M-mode
  ┌──────────────────────────────────▼───────────────────────────┐
  │  Monitor                                                     │
  │  1. Check manifest: is Zone 1 allowed to send to Zone 2? ✓  │
  │  2. Copy payload by value into Zone 2's inbox               │
  │     (no pointer sharing — payload is maximum 4 × 32-bit)    │
  │  3. Mark Zone 2 inbox as pending                            │
  │  4. Return to Zone 1 (or yield if requested)                │
  └──────────────────────────────────┬───────────────────────────┘
                                     │ context switch (next timeslice)
  ┌──────────────────────────────────▼───────────────────────────┐
  │  Zone 2  (receiver)                                          │
  │  MULTIZONE_RECV(1, payload[4])  ← message is available       │
  └──────────────────────────────────────────────────────────────┘

  Key invariant: Zone 2 never receives a pointer into Zone 1's memory.
                 It receives a copy. Pointer-passing is architecturally impossible.
```

**GitHub Repository:** [`hex-five/multizone-sdk`](https://github.com/hex-five/multizone-sdk) — `include/multizone.h`

> ### 📌 Rules to Remember — §5.4
> - The mailbox uses **value copying, never pointer sharing**: a zone cannot receive a pointer into another zone's memory because the Monitor copies the payload by value. Pointer-based attacks between zones are architecturally eliminated.
> - Message payload is **intentionally small** (typically 4 × 32-bit words): this forces clean, well-defined interfaces between zones and prevents large data sharing that would blur isolation boundaries.
> - **Communication rights are manifest-defined**: if the manifest does not grant Zone 1 the right to send to Zone 3, the Monitor refuses the ecall. There is no runtime override.
> - The mailbox is **asynchronous**: a sending zone is not blocked waiting for a reply unless it explicitly yields. This enables concurrent zone execution.

---

### 5.5 The MultiZone SDK and HAL

**Role and Responsibility**

The MultiZone SDK provides the development-facing toolchain and abstraction layers that allow engineers to write zone code without dealing directly with RISC-V CSRs or PMP mechanics. It includes:

- **Hardware Abstraction Layer (HAL):** Board-specific initialisation, peripheral drivers, and linker scripts for supported RISC-V evaluation platforms.
- **Zone application templates:** Starter code for each zone, pre-wired with the mailbox API and interrupt handlers.
- **Build system integration:** Makefiles and toolchain configurations that consume the manifest and produce a complete, flashable firmware image.
- **Reference examples:** Demonstration applications illustrating common patterns — secure channel establishment, key storage, remote attestation primitives.

**GitHub Repository:** [`hex-five/multizone-sdk`](https://github.com/hex-five/multizone-sdk)

Key conceptual directories:

| Directory | Conceptual Role |
|-----------|----------------|
| `bsp/` | Board Support Package: platform HAL and PMP configuration tables |
| `include/` | Public API headers — primarily `multizone.h` |
| `zone*/` | Per-zone application code templates |
| `ext/` | Optional third-party integrations (FreeRTOS, wolfSSL, etc.) |

> ### 📌 Rules to Remember — §5.5
> - The SDK is **not in the TCB**: it is a development convenience layer. Its compromise affects application code but not the Monitor's enforcement guarantees.
> - The HAL is **platform-specific**: unlike OP-TEE which abstracts a broad class of ARM SoCs, each MultiZone port is tailored to a specific RISC-V evaluation board. Portability requires explicit porting effort.

---

## 6. The MultiZone API Model

Unlike OP-TEE's two-tier GlobalPlatform API model (Client API for the Normal World, Internal Core API for TAs), MultiZone defines a **single, symmetric API** that any zone can use, regardless of its trust level. The concept of a "trusted" versus "untrusted" zone is a design-time designation enforced by the manifest — not by different API surfaces.

```
  MultiZone API model: symmetric across all zones

  OP-TEE model (asymmetric):          MultiZone model (symmetric):
  ──────────────────────────          ──────────────────────────────
  Normal World                        Zone 1
    → TEE Client API                    → multizone.h API
  Secure World                        Zone 2
    → Internal Core API                 → multizone.h API (same)

  Two different API surfaces          One API surface,
  for two different worlds.           N zones, same contract.
  Asymmetry is structural.            Trust is a manifest property.
```

### 6.1 The Inter-Zone Messaging API

The core of the MultiZone API is defined in `multizone.h` and consists of three primitives:

- **`MULTIZONE_SEND(zone_id, payload[])`** — Sends a fixed-size payload to the target zone's inbox. Returns immediately (non-blocking by default).
- **`MULTIZONE_RECV(zone_id, payload[])`** — Receives a payload from the specified zone's outbox into the caller's local buffer. Blocks until a message is available.
- **`MULTIZONE_YIELD()`** — Voluntarily relinquishes the current timeslice, allowing the Monitor to switch to another zone.

```
  The three MultiZone primitives and their semantics

  ┌───────────────────────────────────────────────────────────┐
  │  MULTIZONE_SEND(dest, payload[4])                         │
  │  ─────────────────────────────────────────────────────    │
  │  • Copies payload[4] into dest zone's inbox               │
  │  • Non-blocking: returns immediately                      │
  │  • Monitor validates manifest policy before accepting     │
  │  • If inbox full: returns error (no blocking wait)        │
  └───────────────────────────────────────────────────────────┘

  ┌───────────────────────────────────────────────────────────┐
  │  MULTIZONE_RECV(src, payload[4])                          │
  │  ─────────────────────────────────────────────────────    │
  │  • Copies message from src zone's outbox into payload[4]  │
  │  • Blocking: suspends zone until message is available     │
  │  • Monitor mediates the copy — no direct memory access    │
  └───────────────────────────────────────────────────────────┘

  ┌───────────────────────────────────────────────────────────┐
  │  MULTIZONE_YIELD()                                        │
  │  ─────────────────────────────────────────────────────    │
  │  • Voluntary context switch to Monitor                    │
  │  • Monitor selects next zone per scheduling policy        │
  │  • Used to implement cooperative multitasking within      │
  │    a time-sliced preemptive overall model                 │
  └───────────────────────────────────────────────────────────┘
```

> ### 📌 Rules to Remember — §6.1
> - The entire inter-zone API is **three primitives**: SEND, RECV, YIELD. This minimal surface area is a deliberate security property — less API means less potential misuse.
> - The **payload size is fixed and small** (4 × 32-bit words = 16 bytes): for larger data, zones must agree on a protocol for chunked transfer. There is no "large buffer" escape hatch.
> - SEND is **non-blocking, RECV is blocking**: this asymmetry is important for reasoning about deadlocks. A zone waiting on RECV cannot make progress without an incoming message.
> - **Policy is pre-validated at boot**: the Monitor does not consult an ACL at runtime for every send — the PMP layout already enforces zone boundaries, and the mailbox routing table is fixed at boot from the manifest.

---

### 6.2 Zone Lifecycle and Entry Points

Each zone exposes three well-defined entry points that the Monitor calls at defined lifecycle events:

```
  Zone lifecycle entry points

  ┌────────────────────────────────────────────────────────────┐
  │  void zone_init(void)                                      │
  │  ─────────────────────────────────────────────────────     │
  │  Called once by Monitor at system startup.                 │
  │  Zone initialises its state, hardware, and data.           │
  └────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────┐
  │  void zone_main(void)                                      │
  │  ─────────────────────────────────────────────────────     │
  │  Called on every timeslice allocated to this zone.         │
  │  The zone processes messages, performs work, and returns   │
  │  (or calls MULTIZONE_YIELD to release early).              │
  └────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────┐
  │  void zone_irq_handler(void)                               │
  │  ─────────────────────────────────────────────────────     │
  │  Called by Monitor when an interrupt assigned to this      │
  │  zone fires. The zone handles the hardware event.          │
  └────────────────────────────────────────────────────────────┘
```

> ### 📌 Rules to Remember — §6.2
> - Zone entry points are **called by the Monitor**, not by zone code directly. The Monitor is always in control of when zone code executes.
> - `zone_main` must **return or yield**: a zone that never returns consumes its timeslice and the Monitor preempts it. This is not a fault — it is normal operation.
> - **Interrupts are zone-assigned**: a hardware interrupt that belongs to Zone 2 is routed by the Monitor to Zone 2's `zone_irq_handler`, not to a global handler. Peripheral ownership and interrupt ownership are co-assigned.

---

## 7. Inter-Zone Communication Model

### 7.1 The Full Communication Path

```
  End-to-end message flow: Zone 1 sends to Zone 2

  ┌──────────────────────────────────────────────────────────┐
  │  Zone 1 code                                             │
  │  uint32_t msg[4] = {CMD_ENCRYPT, key_id, len, checksum}; │
  │  MULTIZONE_SEND(2, msg);                                 │
  └────────────────────────────┬─────────────────────────────┘
                               │  ecall → trap to M-mode
  ┌────────────────────────────▼─────────────────────────────┐
  │  Monitor: SEND handler                                   │
  │  1. Validate: manifest allows Zone 1 → Zone 2 ✓         │
  │  2. Copy msg[4] by value into Zone 2 mailbox slot        │
  │  3. Set Zone 2 pending flag                              │
  │  4. mret → return to Zone 1                              │
  └────────────────────────────┬─────────────────────────────┘
                               │  [later: Monitor schedules Zone 2]
  ┌────────────────────────────▼─────────────────────────────┐
  │  Monitor: context switch to Zone 2                       │
  │  Restore Zone 2 register state → mret to zone_main()     │
  └────────────────────────────┬─────────────────────────────┘
                               │
  ┌────────────────────────────▼─────────────────────────────┐
  │  Zone 2 code                                             │
  │  uint32_t inbox[4];                                      │
  │  MULTIZONE_RECV(1, inbox);   ← receives copied payload   │
  │  // inbox[0] = CMD_ENCRYPT, inbox[1] = key_id, ...       │
  └──────────────────────────────────────────────────────────┘
```

### 7.2 What Cannot Happen

```
  Architecturally impossible interactions

  ┌──────────────────────────────────────────────────────────────┐
  │  Zone 1 attempts: uint32_t *p = (uint32_t*)ZONE2_DATA_ADDR; │
  │                   *p = 0xDEADBEEF;                          │
  │                                                              │
  │  Hardware outcome:                                           │
  │  PMP check: Zone 1 has no write permission on Zone 2 data   │
  │  → Store Access Fault raised by hardware                    │
  │  → Monitor trap handler invoked                             │
  │  → Zone 1 is suspended or terminated                        │
  │  → Zone 2 is unaffected                                     │
  └──────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────┐
  │  Zone 1 attempts: csrw pmpaddr0, new_addr  (write PMP CSR)  │
  │                                                              │
  │  Hardware outcome:                                           │
  │  Writing PMP CSRs from S/U-mode → Illegal Instruction fault  │
  │  → Monitor trap handler invoked                              │
  │  → Zone 1 is suspended or terminated                         │
  └──────────────────────────────────────────────────────────────┘
```

> ### 📌 Rules to Remember — §7
> - The Monitor is **on the critical path of every inter-zone interaction**: there is no zone-to-zone communication that does not pass through it.
> - Cross-zone memory access is **impossible by hardware**: a zone cannot read or write another zone's memory even with a valid-looking pointer. The PMP fault fires before the access completes.
> - PMP reconfiguration from zone code is **impossible by hardware**: PMP CSRs are M-mode-only registers. An attempt from S/U-mode raises an illegal instruction fault, not a security policy decision — the hardware itself prevents it.
> - The message-passing model **eliminates entire classes of inter-zone vulnerabilities**: buffer overflows in one zone cannot corrupt another zone's heap because there is no shared heap.

---

## 8. Security Architecture and Trust Model

### 8.1 Trusted Computing Base

The MultiZone TCB is **smaller than any other TEE architecture** discussed in this document. It consists of:

- The RISC-V processor's PMP enforcement logic (hardware)
- The MultiZone Security Monitor (< 4 KB, M-mode only)
- The Zone Manifest (compile-time policy)

```
  MultiZone TCB: minimal by construction

  ╔════════════════════════════════════════════════════════╗
  ║  TRUSTED COMPUTING BASE                                ║
  ║                                                        ║
  ║   RISC-V PMP silicon                                   ║
  ║   MultiZone Security Monitor  (< 4 KB, M-mode only)   ║
  ║   Zone Manifest  (compile-time, static)                ║
  ╚════════════════════════════════════════════════════════╝

  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄ security boundary ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

  ┌──────────────────────────────────────────────────────────┐
  │  OUTSIDE TCB  (assumed untrusted per zone threat model)  │
  │                                                          │
  │  Zone 1 code  (may be a full RTOS — Linux, FreeRTOS)    │
  │  Zone 2 code  (crypto service — trusted by other zones  │
  │               but not by the Monitor itself)             │
  │  Zone N code  (network stack — actively adversarial     │
  │               in some threat models)                     │
  └──────────────────────────────────────────────────────────┘
```

Critically, **even Zone 2 (the "secure" zone) is outside the Monitor's TCB**. The Monitor does not trust the correctness of any zone code. It enforces boundaries regardless of what zones claim or do.

### 8.2 Zone Trust Levels

Unlike TrustZone's binary trusted/untrusted split, MultiZone enables a **spectrum of trust**. The trust level of a zone is a design-time decision encoded in the manifest:

```
  Example trust topology: IoT device

  Zone 1: Main application (RTOS)
  ──────────────────────────────────────────────────────────
  Trust level: LOW
  Rationale: Runs complex, attack-exposed application code.
  Can communicate with Zone 2 and Zone 3.
  Cannot access crypto hardware directly.

  Zone 2: Cryptographic service
  ──────────────────────────────────────────────────────────
  Trust level: HIGH
  Rationale: Minimal code, well-audited, owns AES accelerator.
  Can be reached by Zone 1 and Zone 3.
  Never initiates communication — only responds.

  Zone 3: Network stack (e.g., TCP/IP + TLS)
  ──────────────────────────────────────────────────────────
  Trust level: MEDIUM / HOSTILE
  Rationale: Exposed to external network input.
  Can communicate with Zone 1 only.
  Cannot reach Zone 2 (crypto) directly.
  Even if fully compromised, cannot exfiltrate Zone 2 keys.
```

### 8.3 Threat Containment Model

```
  Compromise scenario: Zone 3 (network) fully exploited

  Attacker controls Zone 3 code completely.

  What the attacker CAN do:
  ✓ Send malformed messages to Zone 1 (via mailbox)
  ✓ Corrupt Zone 3's own memory and state
  ✓ Exhaust Zone 3's timeslice

  What the attacker CANNOT do:
  ✗ Read Zone 2's memory (PMP blocks it)
  ✗ Write Zone 1's memory (PMP blocks it)
  ✗ Send a message to Zone 2 (manifest denies it)
  ✗ Reconfigure PMP entries (M-mode only)
  ✗ Escalate to M-mode (hardware trap contains it)
  ✗ Access the AES accelerator (peripheral not assigned to Zone 3)

  Result: key material in Zone 2 is uncompromised.
          Zone 1 must handle malformed input from Zone 3,
          but its own state is intact.
```

> ### 📌 Rules to Remember — §8
> - The MultiZone TCB is **three components**: PMP silicon + Monitor + Manifest. This is smaller than any OS-based TEE by design.
> - The Monitor **does not trust zone code** — not even the "secure" zone. Trust between zones is a design-time relationship, not a Monitor-enforced privilege.
> - Zone compromise is **contained by hardware**: a fully exploited zone cannot exfiltrate data from another zone through any software-level attack. Physical side-channel attacks are out of scope of the software model.
> - The **trust topology is entirely defined by the manifest**: the security designer's primary job is to correctly assign peripheral access and communication rights in the manifest.
> - Minimising **the number of zones that can communicate with the crypto zone** is the primary security design heuristic: fewer communication paths = smaller blast radius on compromise.

---

## 9. MultiZone vs OP-TEE: An Architectural Comparison

Understanding MultiZone requires situating it precisely relative to OP-TEE. They solve the same class of problem but with different hardware assumptions, different design philosophies, and different target environments.

```
  Architectural comparison: OP-TEE (TrustZone) vs MultiZone (RISC-V PMP)

  ┌──────────────────────────────┬────────────────────────────────┐
  │  Dimension                   │  OP-TEE            MultiZone   │
  ├──────────────────────────────┼────────────────────────────────┤
  │  Hardware base               │  ARM TrustZone     RISC-V PMP  │
  │  Isolation model             │  2 worlds (fixed)  N zones     │
  │  Privilege mechanism         │  NS bit / bus      PMP entries │
  │  World-switch instruction    │  SMC               ecall/mret  │
  │  Monitor location            │  EL3               M-mode      │
  │  GlobalPlatform conformance  │  Yes               No          │
  │  TA portability              │  Cross-TEE (GP)    None        │
  │  Kernel footprint            │  ~100–500 KB       < 4 KB      │
  │  Target environment          │  App. processor    MCU / IoT   │
  │  Secure storage              │  Built-in (TEE FS) Custom/zone │
  │  Crypto API                  │  GP Internal API   Zone-defined │
  │  DMA isolation               │  TZASC (hardware)  IOPMP (ext) │
  │  Trust topology              │  Binary (2 levels) N levels    │
  │  Runtime dynamism            │  Dynamic TA load   Static only │
  │  Formal auditability of TCB  │  Harder (larger)   Easier (<4K)│
  └──────────────────────────────┴────────────────────────────────┘
```

```
  Use-case decision map

  Is the target platform an ARM application processor
  (Cortex-A, running Linux)?
  └── YES → OP-TEE (TrustZone, GlobalPlatform, full TEE stack)

  Is the target platform a RISC-V microcontroller / IoT SoC
  with < 1 MB RAM?
  └── YES → MultiZone (PMP-based, minimal footprint)

  Is GlobalPlatform API portability required?
  └── YES → OP-TEE (or any GP-conformant TEE)
  └── NO  → MultiZone is viable

  Does the system need more than 2 trust domains?
  └── YES → MultiZone's N-zone model maps more naturally
  └── NO  → Either approach works

  Is formal auditability of the TCB a hard requirement?
  └── YES → MultiZone's < 4 KB monitor is significantly
              easier to audit than OP-TEE's kernel
```

> ### 📌 Rules to Remember — §9
> - OP-TEE and MultiZone are **not competitors in the same market segment**: OP-TEE targets application-class ARM processors; MultiZone targets constrained RISC-V MCUs. Choosing between them is primarily a hardware selection decision.
> - The N-zone model is **architecturally more expressive** than the binary Normal/Secure split: it can represent complex trust topologies that TrustZone cannot express without additional software layers.
> - MultiZone's **static manifest is both a strength and a constraint**: it enables formal analysis but prevents dynamic behaviours (runtime TA loading, on-demand zone creation) that OP-TEE supports.
> - Neither approach subsumes the other: they represent **two valid points in the design space** of hardware-assisted isolation, optimised for different constraints.

---

## 10. Summary of GitHub Repositories

The MultiZone ecosystem is considerably more compact than OP-TEE's multi-repository structure, reflecting its narrower scope:

| Repository | URL | Architectural Role |
|------------|-----|--------------------|
| `multizone-sdk` | [github.com/hex-five/multizone-sdk](https://github.com/hex-five/multizone-sdk) | Main SDK: Security Monitor, zone templates, HAL, build system, mailbox API |
| `multizone-secure-iot-stack` | [github.com/hex-five/multizone-secure-iot-stack](https://github.com/hex-five/multizone-secure-iot-stack) | Reference integration: full IoT stack with network, crypto, and application zones |
| `multizone-fpga` | Platform-specific forks | Board-specific BSP ports for FPGA-based RISC-V platforms (SiFive, Microchip PolarFire, etc.) |

```
  Repository structure aligned with the MultiZone architecture

  ┌────────────────────────────────────────────────────────────┐
  │  multizone-sdk                                             │
  │  ├── bsp/         ← HAL, PMP tables, platform config      │
  │  │                   (TCB-adjacent: board-specific init)   │
  │  ├── include/     ← multizone.h  (the public API)         │
  │  ├── zone1/       ← Zone 1 application template           │
  │  ├── zone2/       ← Zone 2 application template           │
  │  ├── zone3/       ← Zone 3 application template           │
  │  ├── zone4/       ← Zone 4 application template           │
  │  └── ext/         ← third-party integrations              │
  │                      (FreeRTOS, wolfSSL, mbedTLS, ...)     │
  └────────────────────────────────────────────────────────────┘

  Note: The Security Monitor source is embedded within bsp/.
  The Monitor, HAL, and zone templates are compiled together
  into a single flashable firmware image by the build system.
  Unlike OP-TEE (separate optee_os / optee_client repos),
  MultiZone is a single-repo, single-image artifact.
```

> ### 📌 Rules to Remember — §10
> - MultiZone is a **single-repo, single-image system**: the Monitor, HAL, and all zone code are compiled and linked together. There is no runtime loading, no separate secure firmware update path.
> - The `bsp/` directory is the **closest to the TCB** in the repository: it contains the platform-specific Monitor entry points and PMP configuration. Changes here have direct security implications.
> - The absence of separate "client" and "server" repositories reflects MultiZone's **symmetric API model**: unlike OP-TEE's two distinct API surfaces, MultiZone zones all use the same SDK.

---

## 11. Conclusion

MultiZone Security represents a fundamentally different approach to hardware-assisted isolation on RISC-V: in place of a binary, hardware-bus-level world separation, it offers a configurable N-zone partition model built on the standard PMP mechanism, enforced by a minimal Security Monitor of under 4 KB executing in M-mode.

Its design reflects a coherent set of architectural principles:

- **Radical TCB minimisation:** A monitor of under 4 KB is not a compromise — it is a deliberate design target. The smaller the TCB, the more tractable formal verification and security audit become.
- **Static policy as a security property:** The compile-time manifest is not a limitation but a feature. Immutable policy means no runtime escalation, no dynamic reconfiguration attacks, and a fully enumerable threat model.
- **Symmetric isolation over hierarchical privilege:** Every zone is equally isolated from every other zone. There is no "more trusted" zone from the Monitor's perspective — trust topology is a design-time artefact, not a runtime property.
- **Message-passing as the universal interface contract:** By forcing all inter-zone communication through fixed-size, value-copied messages, MultiZone eliminates entire classes of inter-zone memory corruption vulnerabilities at the architectural level.

For a senior architect evaluating MultiZone, the key mental model is one of **static partitioning with dynamic messaging**: the partition boundaries are fixed at compile time and enforced by hardware; within those boundaries, zones are autonomous; between those boundaries, all interaction is explicit, small, and Monitor-supervised.

> ### 📌 Master Rules — Core principles to always keep in mind
>
> | Principle | One-sentence formulation |
> |-----------|--------------------------|
> | **N zones, not 2 worlds** | MultiZone replaces the binary Secure/Normal split with a configurable N-zone model — trust topology is a design decision, not a hardware constraint. |
> | **PMP is the enforcement bedrock** | Every isolation guarantee ultimately rests on hardware PMP checks. No software trick can bypass a PMP fault. |
> | **The Monitor is the entire TCB** | Under 4 KB, M-mode only, no application logic. If it is compromised, everything fails. Everything else is outside the TCB by definition. |
> | **The manifest is the security policy** | If you can read and understand the manifest, you understand the complete, exhaustive security topology of the system. |
> | **Copy, never share** | Zones exchange data by value, never by pointer. Cross-zone pointer sharing is architecturally impossible — not just policy-prohibited. |
> | **Static is secure** | No runtime zone creation, no dynamic policy changes, no manifest updates at runtime. Immutability of the isolation policy is a security property. |
> | **Compromise is contained** | A fully exploited zone cannot exfiltrate data from another zone through software. The blast radius of any zone compromise is bounded by its PMP entry set. |

---

*This document is intended as a conceptual foundation for engineers and architects engaging with RISC-V security on resource-constrained platforms. For implementation details, readers are directed to the official MultiZone SDK documentation at [hex-five.com](https://hex-five.com) and to the repositories listed herein.*

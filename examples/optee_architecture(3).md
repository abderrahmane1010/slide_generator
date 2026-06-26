# OP-TEE: Architectural Overview and Core Concepts

**Document type:** Technical Architecture Reference  
**Audience:** Senior Software and Systems Architects  
**Scope:** Conceptual and architectural — implementation details are intentionally excluded

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Foundational Concepts: ARM TrustZone](#2-foundational-concepts-arm-trustzone)
3. [OP-TEE in the Trusted Execution Environment Landscape](#3-op-tee-in-the-trusted-execution-environment-landscape)
4. [High-Level Architectural Vision](#4-high-level-architectural-vision)
5. [Core Components and Their Roles](#5-core-components-and-their-roles)
   - 5.1 [OP-TEE OS (Trusted Kernel)](#51-op-tee-os-trusted-kernel)
   - 5.2 [OP-TEE Client Library](#52-op-tee-client-library)
   - 5.3 [OP-TEE Supplicant](#53-op-tee-supplicant)
   - 5.4 [Trusted Applications](#54-trusted-applications)
   - 5.5 [OP-TEE Test Suite](#55-op-tee-test-suite)
6. [The GlobalPlatform API Model](#6-the-globalplatform-api-model)
   - 6.1 [The TEE Client API](#61-the-tee-client-api)
   - 6.2 [The TEE Internal Core API](#62-the-tee-internal-core-api)
7. [Inter-World Communication Model](#7-inter-world-communication-model)
8. [Security Architecture and Trust Model](#8-security-architecture-and-trust-model)
9. [OP-TEE and PKCS#11: An Architectural Overview](#9-op-tee-and-pkcs11-an-architectural-overview)
10. [Summary of GitHub Repositories](#10-summary-of-github-repositories)
11. [Conclusion](#11-conclusion)

---

## 1. Introduction

OP-TEE (Open Portable Trusted Execution Environment) is an open-source, standards-conformant Trusted Execution Environment (TEE) designed primarily for ARM processors that support the TrustZone security extension. Originally developed by STMicroelectronics and subsequently maintained by Linaro, OP-TEE is now a mature, community-driven project hosted under the [OP-TEE GitHub organization](https://github.com/OP-TEE).

The project's primary objective is to provide a reference TEE implementation that adheres to the GlobalPlatform TEE specifications, enabling hardware-isolated execution of security-sensitive software on standard ARM-based platforms. By separating the execution environment into a *Normal World* and a *Secure World*, OP-TEE enforces strong isolation guarantees that are rooted in hardware, rather than software-only mechanisms.

This document provides a conceptual and architectural understanding of OP-TEE, suitable as a foundation for deeper technical engagement. It deliberately omits implementation details in favour of clear articulation of responsibilities, abstractions, and inter-component relationships.

```
  One-sentence purpose of OP-TEE
  ───────────────────────────────────────────────────────────────
  Move secrets into a place the Normal World  cannot reach,
  and expose only a narrow, audited interface to interact with them.
  ───────────────────────────────────────────────────────────────
```

> ### 📌 Rules to Remember — §1
> - OP-TEE is not a standard: it is a **reference implementation** of a standard (GlobalPlatform).
> - Security isolation is first a **hardware property** — software only exploits what the silicon enforces.
> - The entire architecture serves one intent: **move secrets to where the Normal World cannot reach them.**

---

## 2. Foundational Concepts: ARM TrustZone

Before examining OP-TEE itself, it is essential to understand the hardware substrate upon which it is built: **ARM TrustZone**.

TrustZone is a system-wide security approach integrated into the ARM architecture. It introduces a hardware-enforced separation between two distinct execution contexts:

- **The Normal World (Non-Secure World):** The environment in which a conventional operating system (e.g., Linux) and user-space applications execute. Software in this world has no direct access to Secure World resources.
- **The Secure World:** A privileged, isolated execution environment in which security-sensitive code and data reside. It is architecturally protected from the Normal World by hardware.

Transitions between worlds are mediated exclusively through a dedicated processor instruction, the **Secure Monitor Call (SMC)**, and are handled by a *Secure Monitor* component that operates at the highest privilege level. This hardware boundary constitutes the trust anchor upon which the entire OP-TEE security model is built.

TrustZone partitions not only processor execution modes but also memory address space and peripheral access, enforced by the **TrustZone Address Space Controller (TZASC)** and related hardware components. This ensures that Secure World memory regions are physically inaccessible to Normal World software, regardless of its privilege level.

```
  TrustZone: the NS bit propagated across the entire system bus
  ┌─────────────────────────────────────────────────────────────┐
  │  CPU execution mode                                         │
  │  ┌────────────────────┐   NS=0   ┌──────────────────────┐  │
  │  │  EL0 / EL1 / EL2   │ ◄──────► │  S-EL0 / S-EL1      │  │
  │  │  (Normal World)    │  SMC only │  (Secure World)      │  │
  │  └────────────────────┘          └──────────────────────┘  │
  │                         EL3                                 │
  │                   ┌──────────────┐                         │
  │                   │ Secure Monitor│  (Arbitrates crossings) │
  │                   └──────────────┘                         │
  ├─────────────────────────────────────────────────────────────┤
  │  Memory address space  (TZASC enforced)                     │
  │  ┌──────────────────┐          ┌──────────────────────┐    │
  │  │  NS memory        │          │  Secure memory        │   │
  │  │  (accessible to  │  ✗ DENY  │  (hardware-blocked    │   │
  │  │   both worlds)   │ ◄───────  │   from NS accesses)  │   │
  │  └──────────────────┘          └──────────────────────┘    │
  ├─────────────────────────────────────────────────────────────┤
  │  Peripheral access  (TrustZone Protection Controller)       │
  │  Each peripheral is statically assigned: NS or Secure       │
  └─────────────────────────────────────────────────────────────┘
```

> ### 📌 Rules to Remember — §2
> - TrustZone is a **partitioning mechanism**, not a security model: it separates but does not decide what to protect or how.
> - The NS bit is propagated **across the entire system bus** — the isolation is physical, not logical.
> - There is **only one legal entry point** into the Secure World: the SMC instruction. Any other attempt is blocked by the silicon.
> - The Normal World, even with maximum kernel privileges (EL1), can **never directly read Secure World memory**.
> - TrustZone is a **necessary but not sufficient condition** for a TEE: without trusted software on top, the hardware separation guarantees nothing useful.

---

## 3. OP-TEE in the Trusted Execution Environment Landscape

A **Trusted Execution Environment** is a secure area within a processor that guarantees the confidentiality and integrity of code and data loaded inside it. The TEE concept is defined and standardised by **GlobalPlatform**, an industry consortium that publishes a family of specifications governing TEE interfaces, lifecycle management, and security requirements.

OP-TEE provides a complete, open-source implementation of the GlobalPlatform TEE standard, making it distinct from proprietary TEE implementations in several key respects:

- **Openness and auditability:** The source code is publicly available, enabling independent security review and customisation.
- **Portability:** OP-TEE is designed to be portable across a wide range of ARM-based platforms, from embedded systems to application processors.
- **Standards conformance:** It implements the GlobalPlatform TEE Client API and TEE Internal Core API, ensuring interoperability with standards-compliant client software and Trusted Applications.
- **Ecosystem integration:** OP-TEE integrates with standard boot chains (e.g., TF-A — Trusted Firmware-A) and supports modern security features such as secure storage, cryptographic services, and hardware key management.

```
  TEE: a specification of properties, not a technology
  ┌──────────────────────────────────────────────────────────────┐
  │  GlobalPlatform TEE Specification  (what must be guaranteed) │
  │  ┌──────────────┐ ┌────────────┐ ┌────────────┐ ┌────────┐  │
  │  │Confidentiality│ │ Integrity  │ │ Isolation  │ │Attest. │  │
  │  └──────────────┘ └────────────┘ └────────────┘ └────────┘  │
  └────────────────────────┬─────────────────────────────────────┘
                           │  implemented by
         ┌─────────────────┼──────────────────────┐
         ▼                 ▼                       ▼
  ┌─────────────┐  ┌──────────────┐       ┌──────────────┐
  │  OP-TEE     │  │  Intel SGX   │  ...  │  AMD SEV-SNP │
  │  (ARM TZ)   │  │              │       │              │
  └─────────────┘  └──────────────┘       └──────────────┘
  open-source      proprietary             proprietary
  GP-conformant    different model         different model
```

> ### 📌 Rules to Remember — §3
> - A TEE is a **specification of properties** (confidentiality, integrity, isolation, attestation) — not a technology. TrustZone is one possible realisation among others (SGX, SEV-SNP…).
> - GlobalPlatform defines the **interface contract**: a TA written against the GP Internal Core API is portable across conformant implementations.
> - OP-TEE's open source code does not weaken security — it strengthens it through **auditability**. Security rests on keys and hardware, not code obscurity.
> - OP-TEE is part of a **chain of trust** that starts at boot (TF-A / BL31): without a valid Secure Boot upstream, TEE guarantees do not hold.

---

## 4. High-Level Architectural Vision

The OP-TEE architecture can be conceptualised as a layered, dual-world system. The following diagram captures the principal structural relationships:

```
┌─────────────────────────────────────────────────────────────────┐
│                        NORMAL WORLD                             │
│                                                                 │
│  ┌─────────────────┐       ┌──────────────────────────────┐    │
│  │  Rich OS (Linux)│       │     Client Application (CA)  │    │
│  │                 │       │  (uses TEE Client API)        │    │
│  └────────┬────────┘       └──────────────┬───────────────┘    │
│           │                               │                     │
│           │         ┌─────────────────────┘                     │
│           │         │                                           │
│           │  ┌──────▼──────────────────────┐                   │
│           │  │   libteec (TEE Client API)   │                   │
│           │  │   OP-TEE Client Library      │                   │
│           │  └──────────────┬──────────────┘                   │
│           │                 │                                   │
│           │  ┌──────────────▼──────────────┐                   │
│           │  │  Linux TEE Kernel Driver     │                   │
│           └──►  (optee_drv / /dev/tee*)     │                   │
│              └──────────────┬──────────────┘                   │
│                             │ SMC / shared memory               │
│  ┌──────────────────────────▼──────────────────────────────┐   │
│  │              OP-TEE Supplicant (tee-supplicant)          │   │
│  │  (Normal World daemon: FS, RPMB, network, REE services)  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │ TrustZone hardware boundary
══════════════════════════════╪═══════════════════════════════════
                              │ Secure Monitor (TF-A / EL3)
┌─────────────────────────────────────────────────────────────────┐
│                        SECURE WORLD                             │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  OP-TEE OS (Trusted Kernel)               │  │
│  │                                                           │  │
│  │  ┌────────────┐  ┌─────────────┐  ┌──────────────────┐  │  │
│  │  │  Scheduler │  │ Secure Mem  │  │ Crypto / Storage │  │  │
│  │  │  (threads) │  │  Manager    │  │    Services      │  │  │
│  │  └────────────┘  └─────────────┘  └──────────────────┘  │  │
│  │                                                           │  │
│  │        TEE Internal Core API (exposed to TAs)            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐  │
│  │ Trusted App A │  │ Trusted App B │  │  Trusted App C    │  │
│  │  (TA)         │  │  (TA)         │  │  (e.g., PKCS#11)  │  │
│  └───────────────┘  └───────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

This layered structure encapsulates a fundamental principle: **all security-sensitive logic executes in the Secure World, while the Normal World interacts with it only through well-defined, audited interfaces.**

```
  Reading the architecture: trust flows bottom-up

  Hardware (TrustZone silicon)          ← ultimate trust anchor
       │
  Secure Monitor (TF-A / EL3)          ← only world-switch arbiter
       │
  OP-TEE OS kernel                      ← TCB boundary
       │
  Trusted Application (TA)             ← security service unit
       │
  TEE Client API / Internal Core API   ← standardised contracts
       │
  Client Application (Normal World)    ← untrusted consumer

  Each layer trusts only what is directly beneath it.
```

> ### 📌 Rules to Remember — §4
> - The architecture is **asymmetric by design**: the Normal World calls, the Secure World responds. The reverse (reverse RPC via Supplicant) is the exception, never the norm.
> - The world boundary is not a software line — it is a **physical barrier** crossable only through the Secure Monitor (EL3).
> - Read the architecture **bottom-up for trust**: hardware → Secure Monitor → OP-TEE OS → TA → API. Each layer inherits trust from the layer beneath it.
> - The Supplicant breaks the downward symmetry: it represents the fact that the Secure World **needs the Normal World for I/O**, without trusting it for security.

---

## 5. Core Components and Their Roles

### 5.1 OP-TEE OS (Trusted Kernel)

**Role and Responsibility**

The OP-TEE OS constitutes the heart of the Secure World. It is a purpose-built, security-hardened microkernel that provides the execution environment for Trusted Applications. Its responsibilities span the full range of operating system services within the Secure World:

- **Trusted Application lifecycle management:** Loading, authenticating, instantiating, and terminating Trusted Applications.
- **Session and command dispatch:** Receiving incoming requests from the Normal World and routing them to the appropriate Trusted Application.
- **Memory management:** Enforcing strict isolation between TAs and between TAs and the kernel itself.
- **Concurrency and scheduling:** Managing multiple concurrent secure sessions through an internal threading model.
- **Cryptographic services:** Providing hardware-abstracted cryptographic primitives available to TAs.
- **Secure storage:** Offering encrypted and integrity-protected persistent storage for TA data.
- **Platform abstraction:** Abstracting hardware-specific details behind a platform abstraction layer.

```
  OP-TEE OS internal responsibility map  (optee_os repository)
  ┌──────────────────────────────────────────────────────────────┐
  │                        OP-TEE OS                            │
  │                                                              │
  │  ┌─────────────────────────────────────────────────────┐   │
  │  │  Platform Abstraction Layer  (core/arch/arm/)        │   │
  │  │  SoC-specific: memory map, TZASC config, clocks      │   │
  │  └─────────────────────────────────────────────────────┘   │
  │                                                              │
  │  ┌──────────────┐  ┌────────────────┐  ┌────────────────┐  │
  │  │  Scheduler   │  │  Memory Mgr    │  │  SMC Handler   │  │
  │  │  (threads,   │  │  (S-EL1 page   │  │  (core/arch/   │  │
  │  │  core/kernel)│  │   tables, MMU) │  │   arm/sm/)     │  │
  │  └──────────────┘  └────────────────┘  └────────────────┘  │
  │                                                              │
  │  ┌──────────────────────────────────────────────────────┐   │
  │  │  TEE Services Layer  (core/tee/)                      │   │
  │  │  TA loader · session dispatch · secure storage        │   │
  │  └──────────────────────────────────────────────────────┘   │
  │                                                              │
  │  ┌──────────────┐  ┌────────────────────────────────────┐   │
  │  │  Crypto      │  │  libutee                           │   │
  │  │  Backend     │  │  TEE Internal Core API             │   │
  │  │  (core/      │  │  ← consumed by TAs, not by kernel  │   │
  │  │   crypto/)   │  └────────────────────────────────────┘   │
  │  └──────────────┘                                            │
  └──────────────────────────────────────────────────────────────┘
```

**GitHub Repository:** [`OP-TEE/optee_os`](https://github.com/OP-TEE/optee_os)

Key conceptual directories within this repository:

| Directory | Conceptual Role |
|-----------|----------------|
| `core/` | The trusted kernel itself: scheduling, memory management, session handling, SMC entry points |
| `core/arch/arm/` | ARM-specific architectural support and TrustZone integration |
| `core/kernel/` | Core kernel abstractions: threads, mutexes, pseudo-TAs, pseudo-random number generation |
| `core/tee/` | TEE-layer services: TA loading, secure storage, cryptographic dispatch |
| `core/drivers/` | Secure World device drivers (crypto accelerators, RPMB, etc.) |
| `lib/libutee/` | The TEE Internal Core API library, consumed by Trusted Applications |
| `ta/` | Built-in (pseudo) Trusted Applications shipped with the OS |
| `core/crypto/` | Cryptographic backend abstraction layer |

> ### 📌 Rules to Remember — §5.1
> - The OP-TEE OS is a **security microkernel**, not a general-purpose OS: its perimeter is intentionally narrow to minimise the attack surface.
> - The kernel is the **sole arbiter of the Secure World**: no TA can execute without the kernel having authenticated and isolated it first.
> - The `libutee` layer is the **abstract boundary between the kernel and TAs**: TAs never see service implementations — only the API surface.
> - Pseudo-TAs (static) execute **in kernel context** — they are more powerful but expose a larger attack surface. Use them sparingly.

---

### 5.2 OP-TEE Client Library

**Role and Responsibility**

The OP-TEE Client Library (`libteec`) is a Normal World shared library that provides the **TEE Client API** to user-space applications running on the Rich Execution Environment (REE). It is the sole programmatic interface through which a Normal World Client Application initiates communication with the Secure World.

`libteec` performs several functions at the abstraction level:

- Translating high-level API calls (open session, invoke command, allocate shared memory) into lower-level interactions with the TEE kernel driver.
- Managing shared memory buffers that are accessible to both worlds.
- Abstracting the platform-specific mechanism (ioctl calls to the Linux TEE driver) from the application developer.

`libteec` does not itself perform any security-sensitive operations; it is a thin, trusted adapter layer that connects standard application code to the privileged TEE infrastructure below.

```
  libteec: a pure translation adapter — no security logic

  Client Application code
          │
          │  TEEC_OpenSession(), TEEC_InvokeCommand(), ...
          ▼
  ┌───────────────────────────────────────┐
  │  libteec  (optee_client/libteec/)     │
  │                                       │
  │  • Validates API call structure       │
  │  • Serialises parameters              │
  │  • Maps shared memory                 │
  │  • Issues ioctl() to /dev/tee*        │
  │                                       │
  │  ✗ No cryptography                    │
  │  ✗ No access control                  │
  │  ✗ Not in the TCB                     │
  └───────────────────────────────────────┘
          │
          │  ioctl → Linux TEE driver → SMC
          ▼
     Secure World
```

**GitHub Repository:** [`OP-TEE/optee_client`](https://github.com/OP-TEE/optee_client)

| Directory | Conceptual Role |
|-----------|----------------|
| `libteec/` | Implementation of the GlobalPlatform TEE Client API |
| `tee-supplicant/` | The OP-TEE Supplicant daemon (see §5.3) |

> ### 📌 Rules to Remember — §5.2
> - `libteec` is a **translation adapter with no security logic**: it converts API calls into ioctls. Security is never its responsibility.
> - Being Normal World means `libteec` is **outside the TCB**: it can be compromised without compromising the Secure World, provided the Secure kernel validates all incoming parameters.
> - The key concept of `libteec` is **TEE context + session**: every interaction is framed by these two abstractions. Without an open session, no command is possible.

---

### 5.3 OP-TEE Supplicant

**Role and Responsibility**

The OP-TEE Supplicant (`tee-supplicant`) is a privileged user-space daemon running in the Normal World. It serves as a **reverse RPC (Remote Procedure Call) handler**: it processes requests that originate in the Secure World and require Normal World resources to fulfil.

This architectural pattern arises from a fundamental constraint: the Secure World must sometimes delegate certain operations to the REE, precisely because those operations require Normal World infrastructure (file systems, network stacks, hardware tokens). The Supplicant provides this delegation channel.

```
  The Supplicant: controlled delegation without trust

  ┌──────────────────────────────────────────────────────────┐
  │  SECURE WORLD                                            │
  │                                                          │
  │  OP-TEE OS kernel — needs to persist encrypted blob      │
  │        │                                                 │
  │        │  RPC request: "write this opaque blob to FS"   │
  │        │  (data is already encrypted + HMAC'd)           │
  └────────┼─────────────────────────────────────────────────┘
           │ SMC return / RPC notification
  ┌────────▼─────────────────────────────────────────────────┐
  │  NORMAL WORLD                                            │
  │                                                          │
  │  Linux TEE driver  →  tee-supplicant daemon              │
  │                                                          │
  │  Supplicant responsibilities:                            │
  │  ┌──────────────────────────────────────────────────┐   │
  │  │  • Load TA binary from filesystem                 │   │
  │  │  • Read/write encrypted secure storage files      │   │
  │  │  • Mediate RPMB access                            │   │
  │  │  • Extensible REE service bridge                  │   │
  │  └──────────────────────────────────────────────────┘   │
  │                                                          │
  │  ✗ Cannot decrypt the data it transports                │
  │  ✗ Cannot forge a valid HMAC on stored objects          │
  │  ✗ Outside the TCB                                       │
  └──────────────────────────────────────────────────────────┘
           │ SMC (result return)
  ┌────────▼─────────────────────────────────────────────────┐
  │  SECURE WORLD  — receives opaque result, continues       │
  └──────────────────────────────────────────────────────────┘
```

**GitHub Repository:** [`OP-TEE/optee_client`](https://github.com/OP-TEE/optee_client) (directory: `tee-supplicant/`)

> ### 📌 Rules to Remember — §5.3
> - The Supplicant embodies a **fundamental architectural paradox**: the Secure World delegates I/O to a Normal World component it does not trust — but the data transits **already encrypted**, so the delegation is safe.
> - The Supplicant is **essential in production**: without it, dynamic TA loading and secure storage are impossible.
> - If the Supplicant is killed or compromised, the Secure World **does not collapse** — operations requiring the REE will fail cleanly, but Secure World integrity is preserved.
> - Think of the Supplicant as an **untrusted-but-necessary I/O proxy**: it carries encrypted bytes it cannot read or undetectably alter.

---

### 5.4 Trusted Applications

**Role and Responsibility**

Trusted Applications (TAs) are the security-sensitive software units that execute within the Secure World, hosted and managed by the OP-TEE OS. Each TA is a discrete, isolated module that implements a specific security service — such as key management, secure boot attestation, digital rights management, or cryptographic token emulation.

From an architectural standpoint, TAs are the primary reason OP-TEE exists: the kernel, client library, and supplicant are all infrastructure to enable TAs to execute with integrity and confidentiality guarantees.

```
  TA taxonomy: two kinds, one principle

  ┌─────────────────────────────────────────────────────────────┐
  │  SECURE WORLD                                               │
  │                                                             │
  │  ┌──────────────────────────────────────────────────────┐  │
  │  │  OP-TEE OS kernel                                     │  │
  │  │                                                       │  │
  │  │  ┌─────────────────────────────────────────────────┐ │  │
  │  │  │  Pseudo-TA (static / built-in)                   │ │  │
  │  │  │  • Compiled into OP-TEE OS image                 │ │  │
  │  │  │  • Runs in kernel context (S-EL1)                │ │  │
  │  │  │  • Used for platform core services only          │ │  │
  │  │  │  ⚠ Larger attack surface — use sparingly         │ │  │
  │  │  └─────────────────────────────────────────────────┘ │  │
  │  └──────────────────────────────────────────────────────┘  │
  │                                                             │
  │  ┌──────────────────────────────────────────────────────┐  │
  │  │  User-space TA (dynamic)                              │  │
  │  │  • Loaded at runtime via Supplicant (ELF binary)     │  │
  │  │  • Runs in unprivileged Secure World user space       │  │
  │  │  • Signature-verified before execution               │  │
  │  │  • Isolated address space — TAs are mutually opaque  │  │
  │  │  ✓ Default choice for any new security service        │  │
  │  └──────────────────────────────────────────────────────┘  │
  │                                                             │
  │  Common properties:  UUID identity · session/command API   │
  │                       secure storage · Internal Core API   │
  └─────────────────────────────────────────────────────────────┘
```

**GitHub Repositories:**

| Repository | Purpose |
|------------|---------|
| [`OP-TEE/optee_os`](https://github.com/OP-TEE/optee_os) — `ta/` | Built-in pseudo-TAs and TA build infrastructure |
| [`OP-TEE/optee_examples`](https://github.com/OP-TEE/optee_examples) | Reference TA implementations demonstrating key architectural patterns |

> ### 📌 Rules to Remember — §5.4
> - **TAs are the reason OP-TEE exists** — everything else (kernel, libteec, Supplicant) is supporting infrastructure.
> - A TA = a UUID + a signature + a set of numbered commands. It is the **atomic unit of secure service**.
> - The cryptographic signature is the **gatekeeper of the Secure World**: an unsigned or incorrectly signed binary is rejected before it is even loaded.
> - Dynamic TA vs pseudo-TA: the decision rule is simple — **if it does not absolutely need to run in kernel context, make it a dynamic TA**. Pseudo-TA is the exception, never the default.
> - TAs are mutually invisible by default: inter-TA invocation is possible but **explicit and kernel-controlled**, never implicit.

---

### 5.5 OP-TEE Test Suite

**Role and Responsibility**

The OP-TEE Test Suite (`xtest`) provides a structured collection of functional and regression tests covering both the Normal World interfaces and the Secure World services. Architecturally, it serves as a reference implementation demonstrating correct usage of both the TEE Client API (from the CA side) and the TEE Internal Core API (from the TA side). It is an essential tool for platform integrators validating conformance with the GlobalPlatform TEE specification.

**GitHub Repository:** [`OP-TEE/optee_test`](https://github.com/OP-TEE/optee_test)

> ### 📌 Rules to Remember — §5.5
> - `xtest` is the **executable definition of GlobalPlatform conformance** for OP-TEE: if a platform passes xtest, it is conformant.
> - Read the tests as **living documentation**: they illustrate edge cases and expected behaviours better than any other source.

---

## 6. The GlobalPlatform API Model

A defining characteristic of OP-TEE is its conformance to the **GlobalPlatform TEE specifications**. Two APIs are of central architectural importance.

```
  The two GlobalPlatform APIs: a symmetric double lock

         NORMAL WORLD                    SECURE WORLD
  ┌────────────────────────┐     ┌────────────────────────────┐
  │   Client Application   │     │      Trusted Application   │
  │                        │     │                            │
  │  uses TEE Client API   │     │  uses TEE Internal Core API│
  │  ─────────────────────►│     │◄────────────────────────── │
  │  Controls: who can     │     │  Controls: what code can   │
  │  enter the Secure World│     │  do once inside            │
  └──────────┬─────────────┘     └───────────────┬────────────┘
             │   SMC / hardware boundary          │
             └────────────────────────────────────┘
              Standard contracts defined by GlobalPlatform
              ─ portable across any conformant TEE ─
```

### 6.1 The TEE Client API

**Conceptual Role**

The TEE Client API defines the interface through which Normal World software — referred to as a **Client Application (CA)** — communicates with Trusted Applications in the Secure World. It is specified by GlobalPlatform in the *TEE Client API Specification* and is implemented in OP-TEE by `libteec`.

The API models the CA-TA interaction as a **session-oriented, command-invocation protocol:**

1. **Context initialisation:** The CA establishes a connection to the TEE infrastructure.
2. **Session opening:** The CA requests the opening of a session with a specific TA, identified by a UUID.
3. **Command invocation:** Within a session, the CA invokes numbered commands, passing parameters (values, memory references) and receiving results.
4. **Session closure:** The CA explicitly terminates the session when the interaction is complete.
5. **Context finalisation:** The TEE context is released.

```
  TEE Client API lifecycle — the only valid call sequence

  TEEC_InitializeContext()
          │
          ▼
  TEEC_OpenSession( UUID )        ← TA identified by UUID only
          │                          CA has zero knowledge of TA internals
          ▼
  TEEC_InvokeCommand( cmd_id,     ← parameters: values or shared memory refs
                      params )       return: result code + output params
          │  (repeatable)
          ▼
  TEEC_CloseSession()
          │
          ▼
  TEEC_FinalizeContext()
```

This model deliberately enforces a strict separation: the CA has no knowledge of the TA's internal implementation. It interacts only through the session/command abstraction, which the OP-TEE OS enforces at the hardware boundary.

**Corresponding code location:** `optee_client/libteec/`

> ### 📌 Rules to Remember — §6.1
> - The Client API model is **Context → Session → Command**: these three abstraction levels are nested and ordered — you cannot invoke a command without a session, nor open a session without a context.
> - The CA has **no visibility into the TA implementation**: it knows only the TA's UUID and command identifiers. This is an **opaque interface by design**.
> - Exchanged parameters are either **scalar values** or **shared memory references** — nothing else. This constrained model forces interface thinking at design time.
> - The TA's UUID is its **absolute identity** in the system — it must be globally unique and is used for both routing and authentication.

---

### 6.2 The TEE Internal Core API

**Conceptual Role**

The TEE Internal Core API is the counterpart to the Client API, but it operates entirely within the Secure World. It is specified by GlobalPlatform in the *TEE Internal Core API Specification* and defines the services available to Trusted Application code.

This API is the TA's programmatic interface to the OP-TEE OS. Through it, a TA can:

- **Manage sessions and parameters:** Receive and respond to commands from a CA.
- **Perform cryptographic operations:** Access symmetric and asymmetric encryption, hashing, key derivation, and signing primitives through a unified cryptographic API.
- **Manage cryptographic objects:** Create, import, export, and destroy key objects with defined attributes and access controls.
- **Use secure storage:** Persist and retrieve confidential objects through an encrypted and integrity-protected storage interface.
- **Manage memory:** Allocate, share, and release memory within the Secure World.
- **Generate random data:** Request hardware-seeded randomness.
- **Control time:** Access secure monotonic counters and trusted time sources.
- **Invoke other TAs:** Optionally delegate sub-tasks to other TAs through a secure inter-TA invocation mechanism.

```
  TEE Internal Core API service domains

  ┌──────────────────────────────────────────────────────────────┐
  │  Trusted Application code                                    │
  └───────────────────────┬──────────────────────────────────────┘
                          │  TEE Internal Core API  (libutee)
          ┌───────────────┼────────────────────────────────┐
          │               │                                │
          ▼               ▼                                ▼
  ┌──────────────┐ ┌─────────────────┐          ┌────────────────┐
  │  Crypto      │ │  Secure Storage  │          │  System        │
  │  Services    │ │                  │          │  Services      │
  │              │ │  • Persistent    │          │                │
  │  • Symmetric │ │    objects       │          │  • Memory mgmt │
  │  • Asymmetric│ │  • Key-value     │          │  • Random data │
  │  • Hash      │ │    store         │          │  • Trusted time│
  │  • HMAC      │ │  • Device-bound  │          │  • Panic/abort │
  │  • Key derive│ │    encryption    │          │  • Inter-TA    │
  │  • Key objects│ │  • HMAC integrity│          │    invocation  │
  └──────────────┘ └─────────────────┘          └────────────────┘
          │               │                                │
          └───────────────▼────────────────────────────────┘
                          │
                  ┌───────▼───────┐
                  │  OP-TEE OS    │  ← enforces policy;
                  │  kernel       │     TA cannot override it
                  └───────────────┘
```

The Internal Core API encapsulates the security policy of the OS: all cryptographic operations, storage operations, and memory access follow rules enforced by the kernel, not by the TA code itself.

**Corresponding code location:** `optee_os/lib/libutee/` (the library implementing this API for TA consumption) and `optee_os/core/tee/` (the kernel-side service implementations backing the API).

> ### 📌 Rules to Remember — §6.2
> - The Internal Core API is the **contractual surface between the TA and the kernel**: a well-written TA needs nothing else to implement any cryptographic service.
> - Security policy is **enforced by the kernel, not by the TA**: a TA cannot extract a key marked `non-extractable` even if it requests it — the kernel refuses.
> - The two APIs form a **double-lock system**: the Client API controls who enters the Secure World; the Internal Core API controls what code can do once inside.
> - Remember the symmetry: **Client API = outward-facing interface (CA→TA); Internal Core API = downward-facing interface (TA→OS)**. Both are standardised by GlobalPlatform.

---

## 7. Inter-World Communication Model

Understanding the communication flow between Normal World and Secure World is essential to any architectural analysis of OP-TEE. The mechanism involves multiple layers.

### 7.1 Call Path (Normal World → Secure World)

```
  Normal World → Secure World: the full 5-layer call path

  ┌─────────────────────────────────────────────────────────────┐
  │  [1]  Client Application                 NORMAL WORLD       │
  │       TEEC_InvokeCommand(session, cmd, params)              │
  └──────────────────────────┬──────────────────────────────────┘
                             │  function call
  ┌──────────────────────────▼──────────────────────────────────┐
  │  [2]  libteec  (optee_client)                               │
  │       Serialise params → shared memory buffer               │
  └──────────────────────────┬──────────────────────────────────┘
                             │  ioctl()
  ┌──────────────────────────▼──────────────────────────────────┐
  │  [3]  Linux TEE Kernel Driver  (/dev/tee*)                  │
  │       Validate user-space request                           │
  └──────────────────────────┬──────────────────────────────────┘
                             │  SMC instruction
  ════════════════════════════╪════════════════ hardware boundary
                             │
  ┌──────────────────────────▼──────────────────────────────────┐
  │  [4]  Secure Monitor  (TF-A / EL3)          SECURE WORLD    │
  │       World switch: NS=1 → NS=0                             │
  └──────────────────────────┬──────────────────────────────────┘
                             │
  ┌──────────────────────────▼──────────────────────────────────┐
  │  [5]  OP-TEE OS  →  session dispatch  →  Trusted Application│
  │       Copy & validate params · execute TA command · return  │
  └─────────────────────────────────────────────────────────────┘
```

### 7.2 Reverse RPC Path (Secure World → Normal World)

Certain operations require the Secure World to request services from the Normal World. This reverse path is handled through a structured mechanism:

```
  Secure World → Normal World: reverse RPC via Supplicant

  OP-TEE OS kernel
       │  needs file I/O / RPMB / TA binary
       │  RPC request embedded in SMC return value
       ▼
  Linux TEE Driver  ← woken up, reads RPC code
       │  forwards request to userspace via wait queue
       ▼
  tee-supplicant daemon
       │  performs Normal World operation
       │  (file read/write, RPMB IOCTL, etc.)
       ▼
  Linux TEE Driver  ← receives result from supplicant
       │  issues new SMC to return result
       ▼
  OP-TEE OS  ← resumes suspended thread, receives opaque result
```

### 7.3 Shared Memory

Communication between worlds requires a **shared memory** region — a buffer physically accessible to both the Normal World kernel driver and the Secure World OS. OP-TEE manages the registration, mapping, and lifecycle of such shared buffers, ensuring that data exchange does not introduce Secure World vulnerabilities through memory aliasing or TOCTOU attacks.

```
  Shared memory: the only data channel between worlds

  Normal World                           Secure World
  ┌──────────────────┐                  ┌──────────────────┐
  │  CA / libteec    │                  │  OP-TEE OS / TA  │
  │                  │  Physical RAM    │                  │
  │  Writes params   │◄────────────────►│  Copies params   │
  │  to shared buf   │  (shared region) │  into Secure mem │
  │                  │                  │  before use      │
  └──────────────────┘                  └──────────────────┘
                                         ↑
                                  ⚠ TOCTOU risk:
                                  always copy first,
                                  validate the copy,
                                  never read shared mem twice
```

> ### 📌 Rules to Remember — §7
> - All communication follows the principle of **"Normal World requests, Secure World processes"** — the flow is always initiated from the less-privileged side.
> - A full call traverses **5 abstraction layers**: CA → libteec → TEE driver → SMC → OP-TEE OS → TA. Each layer has a single, unique responsibility.
> - **Shared memory** is the only data channel between worlds — and it is under Secure World control. The Normal World proposes a region; the Secure World decides whether to accept it.
> - The reverse RPC (Supplicant) is **synchronous and blocking** from the Secure World's perspective: the kernel thread is suspended until the Supplicant returns.
> - A TOCTOU attack on shared memory is a real vector: the Secure World must **copy and validate parameters** before use, never read them directly from the shared region.

---

## 8. Security Architecture and Trust Model

### 8.1 Trusted Computing Base

The OP-TEE Trusted Computing Base (TCB) — the set of components that must be trusted for the system's security guarantees to hold — is deliberately minimised and includes:

- The Secure Monitor (TF-A)
- The OP-TEE OS kernel
- The TA signing key infrastructure (the Root of Trust for TA authentication)
- The hardware platform itself (TrustZone enforcement logic)

Everything in the Normal World — including the Linux kernel, `libteec`, and the Supplicant — is explicitly **outside the TCB.** The OP-TEE OS is designed to treat all Normal World inputs as untrusted and to validate all parameters at the Secure World boundary.

```
  TCB boundary: what must be trusted vs what can be compromised

  ╔══════════════════════════════════════════════════════════╗
  ║  TRUSTED COMPUTING BASE  (must not be compromised)       ║
  ║                                                          ║
  ║   ARM TrustZone silicon                                  ║
  ║   TF-A Secure Monitor (EL3)                              ║
  ║   OP-TEE OS kernel                                       ║
  ║   TA signing keys (Root of Trust)                        ║
  ╚══════════════════════════════════════════════════════════╝

  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄ security boundary ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

  ┌──────────────────────────────────────────────────────────┐
  │  OUTSIDE TCB  (assumed untrusted — must be validated)    │
  │                                                          │
  │   Linux kernel (Normal World)                            │
  │   libteec                                                │
  │   tee-supplicant                                         │
  │   Client Applications                                    │
  │   Normal World file system                               │
  └──────────────────────────────────────────────────────────┘

  If anything above the boundary is compromised:
    → Secure World integrity must still hold
    → All parameters are re-validated at Secure World entry
```

### 8.2 TA Authentication and Loading

Every Trusted Application binary is signed by a private key controlled by the platform integrator or TA developer. The OP-TEE OS verifies this signature during TA loading using a stored public key. This mechanism ensures that only authorised code executes in the Secure World, regardless of what the Normal World requests.

### 8.3 Secure Storage Architecture

OP-TEE implements two categories of secure storage:

- **REE file system-backed storage:** Encrypted TA objects stored in the Normal World file system through the Supplicant. The encryption key is derived from a hardware-bound secret, ensuring that data encrypted on one device cannot be decrypted on another.
- **RPMB-backed storage:** Objects stored in the Replay Protected Memory Block of an eMMC device, providing tamper-evidence and replay protection in addition to confidentiality.

```
  Secure storage backends: same API, different threat models

  TA code  (uses TEE Internal Core API — storage is transparent)
      │
      │  TEE_CreatePersistentObject() / TEE_ReadObjectData() / ...
      ▼
  ┌────────────────────────────────────────────────────────────┐
  │  OP-TEE OS  —  Secure Storage Abstraction Layer            │
  │  Encrypt + HMAC all objects with hardware-bound key        │
  └────────────────────┬──────────────────┬───────────────────┘
                       │                  │
            ┌──────────▼───────┐  ┌───────▼───────────────┐
            │  REE-FS backend  │  │  RPMB backend          │
            │                  │  │                        │
            │  • Stored on NW  │  │  • Stored on eMMC      │
            │    filesystem    │  │    RPMB partition       │
            │  • Confidential  │  │  • Confidential        │
            │  • Integrity     │  │  • Integrity           │
            │  • Device-bound  │  │  • Device-bound        │
            │                  │  │  + Replay-protected ✓  │
            │  Use for: general│  │  Use for: counters,    │
            │  key/data storage│  │  critical state, audit │
            └──────────────────┘  └────────────────────────┘
            Both mediated through the Supplicant (NW I/O proxy)
```

Both storage backends share the same Internal Core API surface, making the distinction transparent to TA code.

> ### 📌 Rules to Remember — §8
> - OP-TEE's TCB is **deliberately minimal**: hardware + Secure Monitor + OP-TEE OS kernel + signing keys. Everything else is untrusted by assumption.
> - The golden rule of the trust model: **"Never trust the Normal World"** — even if Linux is root, even if the Supplicant is compromised, the Secure World must hold.
> - The TA trust chain starts with the **signing key**: whoever controls that key controls what can execute in the Secure World. This is the most critical security decision in any deployment.
> - REE-FS and RPMB storage have **the same TA-facing behaviour** (same API) but different properties: RPMB adds **anti-replay protection** — essential for counters and critical state.
> - A secure storage object is **bound to a specific device** via a hardware key: extracting the encrypted file and copying it to another device yields nothing — decryption will fail.

---

## 9. OP-TEE and PKCS#11: An Architectural Overview

### 9.1 The Role of PKCS#11

**PKCS#11** (Public-Key Cryptography Standard #11), also known as *Cryptoki*, is a platform-independent API standard defining a programming interface for cryptographic hardware tokens — devices capable of generating, storing, and operating on cryptographic keys in a protected environment. PKCS#11 is widely used in PKI infrastructure, smartcard middleware, TLS stacks, and key management systems.

From an architectural standpoint, PKCS#11 defines:

- A **slot and token abstraction:** A slot represents a physical or logical device; a token is the cryptographic service unit within a slot.
- A **session model:** Applications open sessions to tokens, within which they perform cryptographic operations.
- An **object model:** Keys and certificates are represented as objects with typed attributes, access controls (public/private/sensitive), and defined lifecycle operations.
- A **mechanism model:** Cryptographic algorithms are identified by standardised mechanism codes, decoupled from key objects.

```
  PKCS#11 conceptual model (before any OP-TEE mapping)

  Application
      │  C_OpenSession(slot) → session handle
      │  C_FindObjects(session, template) → object handles
      │  C_Sign(session, mechanism, key_handle, data) → signature
      ▼
  ┌────────────────────────────────────────────────────────┐
  │  PKCS#11 Token  (logical cryptographic device)         │
  │                                                        │
  │  ┌─────────────────────────────────────────────────┐  │
  │  │  Object Store                                    │  │
  │  │  ┌──────────────┐  ┌──────────────────────────┐ │  │
  │  │  │ Private Key  │  │ Certificate               │ │  │
  │  │  │ CKA_SENSITIVE│  │ CKA_EXTRACTABLE = TRUE    │ │  │
  │  │  │ = TRUE       │  │                           │ │  │
  │  │  │ ← never      │  │ ← can leave token         │ │  │
  │  │  │   exported   │  │                           │ │  │
  │  │  └──────────────┘  └──────────────────────────┘ │  │
  │  └─────────────────────────────────────────────────┘  │
  │                                                        │
  │  Mechanism dispatch: CKM_RSA_PKCS, CKM_AES_GCM, ...  │
  └────────────────────────────────────────────────────────┘
```

### 9.2 Architectural Mapping to OP-TEE

OP-TEE provides a PKCS#11 Trusted Application — implemented as a standard TA within the Secure World — that exposes PKCS#11 token semantics to Normal World software.

```
┌─────────────────────────────────────────────────────────────────┐
│                        NORMAL WORLD                             │
│                                                                 │
│  Application (e.g., OpenSSL, GnuTLS, OpenSC, p11-kit)          │
│       │  PKCS#11 API  (standard, platform-independent)         │
│       ▼                                                         │
│  libckteec  (OP-TEE PKCS#11 client library)                     │
│       │  PKCS#11 calls → TEE Client API sessions/commands       │
│       │  Serialises params into shared memory buffers           │
│       ▼                                                         │
│  libteec  →  Linux TEE Driver  →  SMC                          │
└─────────────────────────────────────────────────────────────────┘
                         │ TrustZone boundary
┌─────────────────────────────────────────────────────────────────┐
│                        SECURE WORLD                             │
│                                                                 │
│  PKCS#11 TA  (user-space TA, UUID-identified)                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Protocol & access control layer                         │   │
│  │  Token mgmt · Session mgmt · Object store                │   │
│  │  Mechanism dispatch · Attribute enforcement              │   │
│  │                                                           │   │
│  │  ✗ No cryptographic primitives — all delegated below     │   │
│  └─────────────────────────────────────────────────────────┘   │
│       │  TEE Internal Core API                                  │
│       ▼                                                         │
│  OP-TEE OS  (crypto engine, secure storage, memory mgmt)        │
└─────────────────────────────────────────────────────────────────┘
```

### 9.3 Key Architectural Observations

**Separation of protocol from cryptography.** The PKCS#11 TA is responsible for PKCS#11 protocol semantics — session state, object lifecycle, attribute handling, access controls — while all cryptographic operations are delegated downward to the OP-TEE OS through the TEE Internal Core API. The TA does not implement cryptographic primitives itself.

**Secure key storage.** PKCS#11 token objects (private keys, secret keys, certificates) are stored using OP-TEE's secure storage subsystem. Keys marked as *sensitive* or *non-extractable* are enforced at the Secure World boundary: the key material never leaves the Secure World in plaintext.

**Client-side library (`libckteec`).** A thin Normal World library translates PKCS#11 API calls into the session/command model of the TEE Client API. It contains no security logic — it is a marshalling adapter.

**Token identity and multiplicity.** The PKCS#11 TA models each token as an independent logical entity with its own object store, backed by OP-TEE secure storage. Multiple tokens can coexist within the same TA instance.

**Integration with the broader ecosystem.** Because `libckteec` exposes a standard PKCS#11 interface, it integrates transparently with PKCS#11-aware software stacks.

```
  Full PKCS#11 + OP-TEE integration stack

  ┌───────────────────────────────────────────────────────┐
  │  OpenSSL / GnuTLS / application                       │  NW
  └────────────────────┬──────────────────────────────────┘
                       │  PKCS#11 API
  ┌────────────────────▼──────────────────────────────────┐
  │  p11-kit  (PKCS#11 module manager / broker)           │  NW
  └────────────────────┬──────────────────────────────────┘
                       │  dlopen / standard Cryptoki ABI
  ┌────────────────────▼──────────────────────────────────┐
  │  libckteec  (marshalling adapter only)                │  NW
  └────────────────────┬──────────────────────────────────┘
                       │  TEE Client API  (libteec)
  ┌────────────────────▼──────────────────────────────────┐
  │  Linux TEE driver  →  SMC                             │  NW/HW
  └────────────────────┬──────────────────────────────────┘
         ══════════════╪══════════════ TrustZone boundary
  ┌────────────────────▼──────────────────────────────────┐
  │  PKCS#11 TA  (protocol + access control)              │  SW
  └────────────────────┬──────────────────────────────────┘
                       │  Internal Core API
  ┌────────────────────▼──────────────────────────────────┐
  │  OP-TEE OS  (crypto primitives + secure storage)      │  SW
  └───────────────────────────────────────────────────────┘

  NW = Normal World  |  SW = Secure World  |  HW = hardware boundary
  Each arrow is a trust boundary to reason about.
```

**GitHub Repository:** [`OP-TEE/optee_pkcs11`](https://github.com/OP-TEE/optee_pkcs11) (contains both the PKCS#11 TA and `libckteec`)

> ### 📌 Rules to Remember — §9
> - PKCS#11 and OP-TEE **map naturally onto each other**: both use a session/command model, both have a notion of sensitive non-extractable objects, both separate protocol from cryptography.
> - The PKCS#11 TA contains **no cryptographic primitives**: it delegates everything downward via the Internal Core API. Its role is **protocol and access control**, not mathematics.
> - `libckteec` is a **pure marshalling adapter**: no security logic, only serialisation. Its compromise does not compromise keys — they never leave the Secure World.
> - The PKCS#11 `CKA_SENSITIVE` / `CKA_EXTRACTABLE` attributes are **enforced by the Secure World**, not by the client library — the Normal World cannot bypass this rule.
> - Via `p11-kit`, **OpenSSL and GnuTLS use OP-TEE without knowing it**: this is the power of composition through standards. Changing the TEE requires no changes to upper-layer applications.
> - Memorise the **full stack**: `OpenSSL → p11-kit → libckteec → libteec → TEE driver → SMC → PKCS#11 TA → Internal Core API → OP-TEE OS`. Every arrow is a trust boundary to reason about.

---

## 10. Summary of GitHub Repositories

The following table consolidates the principal OP-TEE repositories and their architectural roles:

| Repository | URL | Architectural Role |
|------------|-----|--------------------|
| `optee_os` | [github.com/OP-TEE/optee_os](https://github.com/OP-TEE/optee_os) | Secure World trusted kernel; TEE Internal Core API; TA runtime |
| `optee_client` | [github.com/OP-TEE/optee_client](https://github.com/OP-TEE/optee_client) | Normal World TEE Client API library (`libteec`); OP-TEE Supplicant (`tee-supplicant`) |
| `optee_test` | [github.com/OP-TEE/optee_test](https://github.com/OP-TEE/optee_test) | Functional and regression test suite (`xtest`); GlobalPlatform compliance tests |
| `optee_examples` | [github.com/OP-TEE/optee_examples](https://github.com/OP-TEE/optee_examples) | Reference CA/TA pairs illustrating usage of both APIs |
| `optee_pkcs11` | [github.com/OP-TEE/optee_pkcs11](https://github.com/OP-TEE/optee_pkcs11) | PKCS#11 Trusted Application and `libckteec` client library |
| `build` | [github.com/OP-TEE/build](https://github.com/OP-TEE/build) | Top-level build system orchestrating cross-repository builds for reference platforms |
| `manifest` | [github.com/OP-TEE/manifest](https://github.com/OP-TEE/manifest) | `repo` manifests for fetching and composing the complete OP-TEE source tree |

```
  Repository map aligned with the architectural boundary

  ┌─────────────────────────────────────────────────────────────┐
  │  NORMAL WORLD REPOSITORIES                                  │
  │                                                             │
  │  optee_client  ── libteec + tee-supplicant                  │
  │  optee_pkcs11  ── libckteec (client side)                   │
  │  optee_test    ── xtest CA side (conformance test client)   │
  │  optee_examples── reference Client Application code        │
  └─────────────────────────────────────────────────────────────┘
                       ══ TrustZone boundary ══
  ┌─────────────────────────────────────────────────────────────┐
  │  SECURE WORLD REPOSITORIES                                  │
  │                                                             │
  │  optee_os      ── OP-TEE OS kernel + libutee + pseudo-TAs  │
  │  optee_pkcs11  ── PKCS#11 TA (Secure World side)           │
  │  optee_test    ── xtest TA side (conformance test TAs)      │
  │  optee_examples── reference Trusted Application code       │
  └─────────────────────────────────────────────────────────────┘
  ┌─────────────────────────────────────────────────────────────┐
  │  BUILD / INTEGRATION REPOSITORIES                           │
  │                                                             │
  │  build    ── platform-specific top-level build orchestration│
  │  manifest ── repo tool manifests to assemble the full tree  │
  └─────────────────────────────────────────────────────────────┘
```

> ### 📌 Rules to Remember — §10
> - The OP-TEE ecosystem is **multi-repository by design**: each repository maps to an architectural boundary (Secure World / Normal World / Tests / PKCS#11). Repository structure mirrors responsibility structure.
> - `optee_os` is the **only repository inside the TCB**: any change to it directly impacts security. All other repositories are Normal World or tooling.
> - The `build` repository is the **platform integrator's entry point**: it is where all pieces are assembled for a specific target board.

---

## 11. Conclusion

OP-TEE represents a mature, standards-conformant, and architecturally coherent implementation of a Trusted Execution Environment on ARM TrustZone. Its design reflects a set of enduring architectural principles:

- **Minimisation of the Trusted Computing Base:** Security-sensitive logic is confined to the Secure World; the Normal World is treated as an untrusted peer.
- **Standards conformance as a design constraint:** Adherence to GlobalPlatform specifications ensures interoperability and provides a well-defined contract between system layers.
- **Separation of concerns:** The Client API, the Supplicant, the OS kernel, and individual Trusted Applications each occupy a clearly bounded responsibility domain.
- **Composability:** The PKCS#11 integration illustrates how OP-TEE's layered architecture enables standard, high-level cryptographic protocols to be grounded in hardware-enforced security without changes to the consuming software stack.

For a senior architect engaging with OP-TEE, the key mental model is one of **negotiated trust across a hardware boundary:** every interaction between the two worlds is a deliberate, policy-controlled crossing, mediated by a sequence of well-specified abstractions — from the GlobalPlatform API at the application layer down to the SMC instruction at the hardware layer. All architectural decisions in OP-TEE ultimately serve to preserve the integrity of that boundary.

> ### 📌 Master Rules — Core principles to always keep in mind
>
> | Principle | One-sentence formulation |
> |-----------|--------------------------|
> | **World separation** | Normal World and Secure World never trust each other — the boundary is enforced by hardware, not software. |
> | **TCB minimisation** | The less code runs inside the Secure World, the smaller the attack surface. Every line of Secure code is a risk that must be justified. |
> | **Standards as contracts** | GlobalPlatform defines the interfaces — OP-TEE implements them. Conformance guarantees portability and interoperability. |
> | **Controlled delegation** | The Secure World delegates I/O to the Normal World (Supplicant), but always with data that is already encrypted. Delegating ≠ trusting. |
> | **Signature as gatekeeper** | Nothing enters the Secure World without a verified signature. The signing key is the software Root of Trust for the entire system. |
> | **Composition through abstraction** | Each layer (PKCS#11 → TEE Client API → SMC → Internal Core API) is an abstraction boundary that allows one implementation to change without impacting adjacent layers. |
> | **Security starts at boot** | All OP-TEE guarantees are conditional on a valid secure boot chain. A compromised Secure Boot invalidates all TEE guarantees. |

---

*This document is intended as a conceptual foundation. For implementation details, readers are directed to the official OP-TEE documentation at [optee.readthedocs.io](https://optee.readthedocs.io) and to the source repositories listed herein.*

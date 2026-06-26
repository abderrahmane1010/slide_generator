# mbed TLS — A Methodical Guide

## 1. Introduction

**mbed TLS** (formerly *PolarSSL*) is a portable, open-source C library that implements cryptographic primitives, X.509 certificate handling, and the SSL/TLS and DTLS protocols. It is maintained under the *TrustedFirmware* umbrella and is designed primarily for **constrained and embedded environments**, where memory, code size, and auditability matter as much as correctness.

Its purpose can be stated in one sentence: *to provide a complete, self-contained, and auditable TLS stack that can be adapted to any platform, from bare-metal microcontrollers to full Linux systems.*

---

## 2. Architectural Vision — A Layered Perspective

mbed TLS is best understood as a stack of well-separated abstraction layers. The architecture obeys two invariants:

- **Vertical isolation.** Each layer depends only on the one immediately below it, through a narrow, well-defined interface.
- **Horizontal modularity.** Within a layer, components (AES, SHA-256, RSA, …) are independent translation units that can be included or excluded at compile time.

### 2.1 Global Stack

The full stack, from user code down to silicon, on a Linux host:

```
╔═══════════════════════════════════════════════════════════════╗
║                       APPLICATION                             ║   user space
║         (HTTPS client, MQTT broker, VPN daemon, …)            ║
╠═══════════════════════════════════════════════════════════════╣
║                    mbed TLS PUBLIC API                        ║
║  ┌─────────────────────────────────────────────────────────┐  ║
║  │  TLS / DTLS engine        (mbedtls_ssl_*)               │  ║
║  │  X.509                    (mbedtls_x509_*)              │  ║
║  │  PK abstraction           (mbedtls_pk_*)                │  ║
║  │  PSA Crypto API           (psa_*)                       │  ║
║  │  Legacy crypto API        (mbedtls_aes_*, _sha_*, …)    │  ║
║  └─────────────────────────────────────────────────────────┘  ║
╠═══════════════════════════════════════════════════════════════╣
║                  PSA CRYPTO CORE  +  DRIVER LAYER             ║
║   dispatch → software back-end │ accelerator │ secure element ║
╠═══════════════════════════════════════════════════════════════╣
║                CRYPTOGRAPHIC PRIMITIVES (software)            ║
║   AES · ChaCha20 · SHA-2/3 · HMAC · RSA · ECP · ECDH · ECDSA  ║
║   GCM · CCM · HKDF · DRBG (CTR/HMAC) · Bignum (MPI)           ║
╠═══════════════════════════════════════════════════════════════╣
║              PLATFORM ABSTRACTION LAYER (PAL)                 ║
║   mbedtls_platform_*  ·  entropy sources  ·  timing  ·  net   ║
╠═══════════════════════════════════════════════════════════════╣
║   libc / POSIX  (malloc, read, write, clock_gettime, …)       ║
╠═══════════════════════════════════════════════════════════════╣
║              LINUX KERNEL                                     ║   kernel space
║   syscalls │ TCP/IP stack │ /dev/urandom (CSPRNG) │ getrandom ║
║   crypto API (optional, via AF_ALG)                           ║
╠═══════════════════════════════════════════════════════════════╣
║   HARDWARE                                                    ║
║   CPU  ·  TRNG  ·  AES-NI / ARMv8 Crypto Ext.  ·  HSM / SE    ║
╚═══════════════════════════════════════════════════════════════╝
```

The same picture on a Cortex-M target with TrustZone collapses the two top kernel rows and replaces them by an RTOS or by **TF-M** on the secure side (see §2.6).

### 2.2 Internal Module Dependency Graph

Within mbed TLS itself, the modules form a directed acyclic graph. Higher-level modules depend on lower-level ones, never the reverse:

```
                    ┌──────────────────────┐
                    │   mbedtls_ssl_*      │   TLS / DTLS
                    └─────────┬────────────┘
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
      ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
      │ mbedtls_x509 │ │ mbedtls_pk   │ │  PSA Crypto  │
      └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
             │                │                │
             └────────┬───────┴────────┬───────┘
                      ▼                ▼
              ┌──────────────┐ ┌──────────────┐
              │   ASN.1      │ │  Primitives  │
              │   OID        │ │  AES/SHA/... │
              └──────┬───────┘ └──────┬───────┘
                     │                │
                     └────────┬───────┘
                              ▼
                  ┌──────────────────────┐
                  │  Bignum (MPI)  +     │
                  │  Platform / PAL      │
                  └──────────────────────┘
```

This graph is the contract enforced by the build system: enabling a high-level module (e.g. `MBEDTLS_SSL_TLS_C`) automatically requires its transitive dependencies, and disabling a leaf module is always safe.

### 2.3 Project Layout

The source tree mirrors the layered design:

```
mbedtls/
├── include/
│   ├── mbedtls/          ← legacy public headers (mbedtls_*)
│   │   ├── ssl.h
│   │   ├── x509_crt.h
│   │   ├── pk.h
│   │   ├── aes.h, sha256.h, rsa.h, ecp.h, …
│   │   └── mbedtls_config.h         ← compile-time configuration
│   └── psa/              ← PSA Crypto public headers
│       ├── crypto.h
│       ├── crypto_values.h
│       └── crypto_struct.h
│
├── library/              ← implementation (.c files, one per module)
│   ├── ssl_tls.c, ssl_tls13_*.c, ssl_msg.c, ssl_client.c, ssl_server.c
│   ├── x509_crt.c, x509_csr.c, x509_crl.c
│   ├── pk.c, pk_wrap.c, pkparse.c, pkwrite.c
│   ├── aes.c, sha256.c, rsa.c, ecp.c, ecdh.c, ecdsa.c, …
│   ├── psa_crypto.c, psa_crypto_slot_management.c, psa_crypto_driver_*.c
│   └── platform.c, platform_util.c, entropy.c, timing.c
│
├── tf-psa-crypto/        ← PSA Crypto sub-project (split out in 4.x)
├── framework/            ← shared test framework
├── tests/                ← unit and integration test suites
├── programs/             ← reference example programs
│   ├── ssl/ (ssl_client1, ssl_server2, dtls_*)
│   ├── x509/ (cert_app, cert_req, cert_write)
│   └── pkey/, aes/, hash/, …
├── configs/              ← alternative config presets
│   ├── config-ccm-psk-tls1_2.h        ← minimal PSK + AES-CCM
│   ├── config-suite-b.h               ← NSA Suite B
│   ├── config-thread.h                ← Thread protocol profile
│   └── config-no-entropy.h            ← static entropy only
├── scripts/              ← code generation, config tools
└── docs/, ChangeLog, README.md
```

Two structural details are worth noting:

- The **separation of `include/mbedtls/` and `include/psa/`** materializes the coexistence of the legacy and the PSA APIs as two distinct, parallel public interfaces.
- The **`configs/` directory** ships pre-validated minimal configurations. They are not just examples — they are concrete proofs that the library can be reduced to a specific, tightly scoped role.

### 2.4 The Two Public Interfaces

mbed TLS currently exposes its cryptography through **two coexisting APIs**:

```
┌──────────────────────────────────────────────────────────────┐
│                    APPLICATION CODE                          │
└────────────┬─────────────────────────────────┬───────────────┘
             │                                 │
             ▼                                 ▼
   ┌───────────────────┐             ┌───────────────────────┐
   │  Legacy API       │             │  PSA Crypto API       │
   │  mbedtls_aes_*    │             │  psa_cipher_*         │
   │  mbedtls_sha256_* │             │  psa_hash_*           │
   │  mbedtls_rsa_*    │             │  psa_sign_hash, …     │
   │  (transparent     │             │  (opaque key handles, │
   │   key material)   │             │   policy-bound)       │
   └─────────┬─────────┘             └───────────┬───────────┘
             │                                   │
             └───────────────┬───────────────────┘
                             ▼
              ┌──────────────────────────────┐
              │   PSA Crypto Core (dispatch) │
              └──────────────┬───────────────┘
                             ▼
              ┌──────────────────────────────┐
              │  Software primitives  /  HW  │
              │  drivers / Secure Element    │
              └──────────────────────────────┘
```

The legacy API remains supported, but in modern versions it is increasingly **implemented on top of PSA Crypto**, which becomes the single internal cryptographic core (§5).

### 2.5 The TLS Sub-Architecture: Context vs. Configuration

A defining detail of the TLS layer is the deliberate split between *per-connection state* and *shared configuration*:

```
   ┌───────────────────────────────┐
   │   mbedtls_ssl_config          │  ← read-only, shareable
   │   - endpoint (client/server)  │     can live in flash / .rodata
   │   - transport (TLS/DTLS)      │     one instance for many sessions
   │   - ciphersuite list          │
   │   - CA chain, own cert        │
   │   - verify mode, callbacks    │
   └──────────────┬────────────────┘
                  │  bound by mbedtls_ssl_setup()
                  ▼
   ┌───────────────────────────────┐      ┌──────────────────────┐
   │   mbedtls_ssl_context         │◀────▶│  I/O callbacks       │
   │   - handshake state machine   │ BIO  │  f_send / f_recv     │
   │   - session keys, sequence #  │      │  (sockets, BSD, …)   │
   │   - record-layer buffers      │      └──────────────────────┘
   │   - peer certificate          │
   └───────────────────────────────┘
```

This split is not cosmetic. On a microcontroller, it lets the TLS configuration sit in flash (`const`) while only the per-connection context consumes RAM — a direct expression of the *principled minimalism* of the library.

The I/O is abstracted by a pair of function pointers (`f_send`, `f_recv`), so the TLS engine is **transport-agnostic**: it does not know about sockets, files, or radios.

### 2.6 Ecosystem and Companion Projects

mbed TLS does not live in isolation. Its layered design positions it inside a broader, coherent stack:

```
            ┌─────────────────────────────────────────────┐
            │       Application / IoT framework           │
            │   (Matter, Zephyr networking, AWS IoT, …)   │
            └────────────────────┬────────────────────────┘
                                 │
                                 ▼
            ┌─────────────────────────────────────────────┐
            │              mbed TLS  (TLS, X.509)         │
            └────────────────────┬────────────────────────┘
                                 │  PSA Crypto API
                                 ▼
            ┌─────────────────────────────────────────────┐
            │            TF-PSA-Crypto                    │
            │  (PSA Crypto reference implementation,      │
            │   recently split out as its own project)    │
            └────────────────────┬────────────────────────┘
                                 │
            ┌────────────────────┼─────────────────────┐
            ▼                    ▼                     ▼
   ┌────────────────┐   ┌────────────────┐    ┌────────────────┐
   │ Software back- │   │  HW driver     │    │  TF-M / SE     │
   │ end (built-in) │   │  (transparent) │    │  (opaque keys) │
   └────────────────┘   └────────────────┘    └────────────────┘
```

The neighboring projects, all under TrustedFirmware, are:

- **TF-PSA-Crypto** — the reference implementation of the PSA Crypto API, historically embedded in mbed TLS and now extracted as a standalone project that mbed TLS consumes.
- **TF-M (Trusted Firmware-M)** — secure-side firmware for Armv8-M (TrustZone). It exposes PSA services (Crypto, Storage, Attestation) across the secure boundary; mbed TLS, running on the non-secure side, can call them through the same `psa_*` API it would use locally.
- **PSA Certified** — the certification programme that validates conformance to the PSA specifications, of which mbed TLS / TF-PSA-Crypto is a reference implementation.

The result is an architecture in which the *same* application code, calling the *same* PSA Crypto API, can run unchanged whether the cryptography is performed by software in the same address space, by a hardware accelerator, or by an isolated secure world — which is precisely the property the layered design was built to provide.

---

## 3. Fundamental Design Principles

mbed TLS is governed by a small set of explicit, principled choices:

1. **Portability before optimization.** The reference implementation is plain C99, with no assumptions about endianness, word size beyond standard limits, or operating system services.
2. **Strict modularity.** Algorithms live in self-contained modules with minimal cross-dependencies, enabling fine-grained inclusion.
3. **Compile-time configurability.** A single header (`mbedtls_config.h`) controls which features are compiled in. Unused code is *not linked, not loaded, not present*.
4. **Minimal external dependencies.** No reliance on third-party libraries; only a thin platform layer is required.
5. **Auditability.** The codebase is intentionally kept small and readable, so that it can be reviewed, certified, and reasoned about.
6. **Determinism and predictability.** Memory allocation patterns, error handling, and API contracts are uniform across modules.

The guiding philosophy is therefore **principled minimalism**: include what is strictly necessary, expose it through a stable interface, and let the integrator choose the rest.

---

## 4. Why mbed TLS Is Lightweight Compared to OpenSSL

OpenSSL and mbed TLS solve the same problem but reflect opposing design cultures.

| Dimension | OpenSSL | mbed TLS |
|---|---|---|
| Origin / target | General-purpose, server-class systems | Embedded, constrained, IoT |
| Codebase size | Large, historically accreted | Small, deliberately curated |
| Build model | Largely monolithic; many features always present | Feature-by-feature compile-time selection |
| Memory model | Heavy use of dynamic allocation | Optional; many configurations avoid it |
| API surface | Broad, with multiple historical layers | Narrow, uniform, consistent naming |
| Coupling | Internally interdependent subsystems | Loosely coupled modules |
| Footprint | Megabytes of code typical | Tens of kilobytes achievable |

mbed TLS is *lightweight* not because it implements less cryptography, but because it implements it under stricter architectural constraints: **modularity, configurability, and the absence of mandatory features**. An integrator who needs only TLS 1.3 with a single ciphersuite can compile out everything else, reducing both the binary footprint and the attack surface.

In short: *OpenSSL is a toolbox; mbed TLS is a kit.*

---

## 5. PSA — Platform Security Architecture

The **Platform Security Architecture (PSA)** is a specification framework, originally defined by Arm and now maintained as an open standard, that describes how secure services should be exposed to applications on connected devices. Within this framework, the **PSA Crypto API** defines a uniform, implementation-agnostic interface for cryptographic operations.

### 5.1 Core Ideas of the PSA Crypto API

- **Opaque key handles.** Applications manipulate keys through identifiers, never through raw key material. The library — or a secure element behind it — owns the actual bytes.
- **Policy-bound keys.** Each key is created with an explicit usage policy (algorithm, permitted operations, exportability) that is enforced by the implementation.
- **Algorithm-agnostic interface.** The same call patterns (`psa_sign_hash`, `psa_aead_encrypt`, `psa_key_derivation_*`, …) cover symmetric, asymmetric, hashing, AEAD, and key derivation operations.
- **Driver model.** The API is designed to dispatch operations to either a software back-end or a hardware accelerator / secure element transparently to the caller.

### 5.2 Role of PSA in mbed TLS

mbed TLS serves as the **reference implementation** of the PSA Crypto API. This has two practical consequences:

1. **A unified, modern cryptographic interface.** New code is expected to use `psa_*` functions rather than the legacy `mbedtls_*` primitives. The legacy API remains available but is progressively layered on top of PSA internally.
2. **A clean separation between consumers and providers of cryptography.** The TLS and X.509 layers of mbed TLS increasingly request cryptographic operations through PSA, which means the same TLS stack can run on a pure-software build, on a system with a hardware accelerator, or on a system where keys live exclusively inside a secure element — without changes to the upper layers.

PSA is therefore not merely an additional API; it is the **architectural direction** of mbed TLS, formalizing the boundary between cryptographic *use* and cryptographic *implementation*.

---

## 6. Summary

mbed TLS embodies a coherent engineering philosophy:

- a **layered architecture** that cleanly separates protocol, cryptography, platform, and hardware concerns;
- a **principled minimalism** that favors auditability, modularity, and compile-time configurability over feature breadth;
- a **lightweight footprint** that follows from these choices rather than from feature reduction; and
- an **evolution toward PSA**, which abstracts cryptography behind opaque, policy-bound key handles and prepares the library for a world of heterogeneous, hardware-assisted secure platforms.

For systems where every kilobyte, every dependency, and every line of code must be justified, mbed TLS represents a deliberate and well-articulated answer.

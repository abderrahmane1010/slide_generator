# Symmetric Cryptography for Embedded Devices
### A First-Principles Manual for the Cyber Embedded Architect

---

*There are exactly two things a symmetric cipher does: it scrambles data with a key, and it unscrambles data with the same key. Everything else in this manual is consequence.*

---

## Preface

This manual is for the embedded systems architect who must make cryptography work correctly, efficiently, and securely on constrained hardware — microcontrollers with kilobytes of RAM, no operating system, no hardware random number generator by default, and an adversary who may hold the device in their hands. It is not for the cryptographer deriving proofs, nor for the application developer who calls a library without needing to know what happens inside. It is for the person in between: the one who selects algorithms, integrates hardware accelerators, writes the key management layer, designs the secure boot chain, and debugs why authentication keeps failing at 3 a.m.

You will learn, in order:

- What symmetric cryptography is at the mathematical and mechanical level (Parts I–II)
- How the primitive building blocks — block ciphers, stream ciphers, MACs, authenticated encryption — are constructed and categorized (Parts III–IV)
- How the internals of AES, ChaCha20, and GHASH actually work, and why that matters for implementation (Part V)
- The modes of operation: how a block cipher becomes a stream, a MAC, or an AEAD scheme (Part VI)
- Key management: generation, storage, derivation, and rotation on constrained hardware (Part VII)
- Side-channel attacks and countermeasures — the attack surface that tutorials ignore (Part VIII)
- Production realities: what changes when your device ships to a million customers (Part IX)
- Tooling, libraries, and workflow for embedded crypto (Part X)
- Mastery: debugging, architecture patterns, and how to actually learn this field (Part XI)
- Appendices: reference tables, cheat sheets, and glossary

Each chapter teaches one thing. Each principle crystallizes a lesson. Read the manual once for orientation, return to individual chapters as reference.

---

## Table of Contents

- [Symmetric Cryptography for Embedded Devices](#symmetric-cryptography-for-embedded-devices)
    - [A First-Principles Manual for the Cyber Embedded Architect](#a-first-principles-manual-for-the-cyber-embedded-architect)
  - [Preface](#preface)
  - [Table of Contents](#table-of-contents)
- [Part I — Orientation](#part-i--orientation)
  - [Chapter 1 — The Duality: Secrecy vs Authenticity](#chapter-1--the-duality-secrecy-vs-authenticity)
  - [Chapter 2 — The Threat Model for Embedded Systems](#chapter-2--the-threat-model-for-embedded-systems)
  - [Chapter 3 — The N Doors: Primitive Categories](#chapter-3--the-n-doors-primitive-categories)
  - [Chapter 4 — The Constraint Triad](#chapter-4--the-constraint-triad)
- [Part II — Anatomy](#part-ii--anatomy)
  - [Chapter 5 — Block Ciphers](#chapter-5--block-ciphers)
  - [Chapter 6 — Stream Ciphers](#chapter-6--stream-ciphers)
  - [Chapter 7 — Message Authentication Codes](#chapter-7--message-authentication-codes)
  - [Chapter 8 — Authenticated Encryption with Associated Data](#chapter-8--authenticated-encryption-with-associated-data)
  - [Chapter 9 — Hash Functions in Symmetric Context](#chapter-9--hash-functions-in-symmetric-context)
  - [Chapter 10 — Block Ciphers vs Stream Ciphers](#chapter-10--block-ciphers-vs-stream-ciphers)
  - [Chapter 11 — Encryption vs Authentication: The Dangerous Conflation](#chapter-11--encryption-vs-authentication-the-dangerous-conflation)
- [Part III — Configuration and Composition](#part-iii--configuration-and-composition)
  - [Chapter 12 — Keys: Sizes, Types, and Lifetimes](#chapter-12--keys-sizes-types-and-lifetimes)
  - [Chapter 13 — Nonces and IVs](#chapter-13--nonces-and-ivs)
  - [Chapter 14 — Modes of Operation: The Universal Wrapper](#chapter-14--modes-of-operation-the-universal-wrapper)
  - [Chapter 15 — ECB, CBC, CTR: The Three Foundational Modes](#chapter-15--ecb-cbc-ctr-the-three-foundational-modes)
  - [Chapter 16 — GCM and CCM: AEAD Modes in Practice](#chapter-16--gcm-and-ccm-aead-modes-in-practice)
  - [Chapter 17 — Padding and Padding Oracles](#chapter-17--padding-and-padding-oracles)
- [Part IV — Mechanism and Internals](#part-iv--mechanism-and-internals)
  - [Chapter 18 — Inside AES: The Four Operations](#chapter-18--inside-aes-the-four-operations)
  - [Chapter 19 — The AES Key Schedule](#chapter-19--the-aes-key-schedule)
  - [Chapter 20 — Inside ChaCha20: The Quarter-Round](#chapter-20--inside-chacha20-the-quarter-round)
  - [Chapter 21 — GHASH: Polynomial MAC over GF(2¹²⁸)](#chapter-21--ghash-polynomial-mac-over-gf2)
  - [Chapter 22 — CMAC and HMAC Internals](#chapter-22--cmac-and-hmac-internals)
  - [Chapter 23 — Why AES-128 Is Still Safe](#chapter-23--why-aes-128-is-still-safe)
- [Part V — Embedded Hardware](#part-v--embedded-hardware)
  - [Chapter 24 — Hardware Crypto Accelerators: Taxonomy](#chapter-24--hardware-crypto-accelerators-taxonomy)
  - [Chapter 25 — AES-NI and ARM Crypto Extensions](#chapter-25--aes-ni-and-arm-crypto-extensions)
  - [Chapter 26 — DMA-Coupled Crypto Engines](#chapter-26--dma-coupled-crypto-engines)
  - [Chapter 27 — True Random Number Generators on Silicon](#chapter-27--true-random-number-generators-on-silicon)
  - [Chapter 28 — Secure Elements and Hardware Security Modules](#chapter-28--secure-elements-and-hardware-security-modules)
- [Part VI — Side-Channel Attacks](#part-vi--side-channel-attacks)
  - [Chapter 29 — The Side Channel: What It Is and Why It Exists](#chapter-29--the-side-channel-what-it-is-and-why-it-exists)
  - [Chapter 30 — Power Analysis: SPA and DPA](#chapter-30--power-analysis-spa-and-dpa)
  - [Chapter 31 — Timing Attacks](#chapter-31--timing-attacks)
  - [Chapter 32 — Fault Injection](#chapter-32--fault-injection)
  - [Chapter 33 — Countermeasures: Masking, Hiding, and Redundancy](#chapter-33--countermeasures-masking-hiding-and-redundancy)
- [Part VII — Key Management](#part-vii--key-management)
  - [Chapter 34 — The Key Hierarchy](#chapter-34--the-key-hierarchy)
  - [Chapter 35 — Key Derivation Functions](#chapter-35--key-derivation-functions)
  - [Chapter 36 — Key Storage on Constrained Devices](#chapter-36--key-storage-on-constrained-devices)
  - [Chapter 37 — Key Provisioning at Manufacturing](#chapter-37--key-provisioning-at-manufacturing)
  - [Chapter 38 — Key Rotation and Revocation](#chapter-38--key-rotation-and-revocation)
- [Part VIII — Protocols and Composition](#part-viii--protocols-and-composition)
  - [Chapter 39 — The Universal Secure Channel Pattern](#chapter-39--the-universal-secure-channel-pattern)
  - [Chapter 40 — Secure Boot: The Cryptographic Chain of Trust](#chapter-40--secure-boot-the-cryptographic-chain-of-trust)
  - [Chapter 41 — Firmware Update Security](#chapter-41--firmware-update-security)
  - [Chapter 42 — Record Protocols: TLS 1.3 as the Reference](#chapter-42--record-protocols-tls-13-as-the-reference)
  - [Chapter 43 — Lightweight Protocols: DTLS, OSCORE, and EDHOC](#chapter-43--lightweight-protocols-dtls-oscore-and-edhoc)
- [Part IX — Production Realities](#part-ix--production-realities)
  - [Chapter 44 — What Changes at Scale](#chapter-44--what-changes-at-scale)
  - [Chapter 45 — Entropy Starvation at Boot](#chapter-45--entropy-starvation-at-boot)
  - [Chapter 46 — Nonce Misuse and Its Consequences](#chapter-46--nonce-misuse-and-its-consequences)
  - [Chapter 47 — Cryptographic Agility: Asset or Liability](#chapter-47--cryptographic-agility-asset-or-liability)
  - [Chapter 48 — Compliance: FIPS 140-3, Common Criteria, and PSA Certified](#chapter-48--compliance-fips-140-3-common-criteria-and-psa-certified)
- [Part X — Tooling and Workflow](#part-x--tooling-and-workflow)
  - [Chapter 49 — Library Selection for Embedded Targets](#chapter-49--library-selection-for-embedded-targets)
  - [Chapter 50 — Mbedtls in Practice](#chapter-50--mbedtls-in-practice)
  - [Chapter 51 — WolfSSL and TinyCrypt](#chapter-51--wolfssl-and-tinycrypt)
  - [Chapter 52 — Test Vectors and CAVP Testing](#chapter-52--test-vectors-and-cavp-testing)
  - [Chapter 53 — Profiling Crypto on Embedded Targets](#chapter-53--profiling-crypto-on-embedded-targets)
- [Part XI — Mastery](#part-xi--mastery)
  - [Chapter 54 — Debugging Cryptographic Failures](#chapter-54--debugging-cryptographic-failures)
  - [Chapter 55 — Architectural Patterns for Secure Systems](#chapter-55--architectural-patterns-for-secure-systems)
  - [Chapter 56 — Common Errors and Their Meaning](#chapter-56--common-errors-and-their-meaning)
  - [Chapter 57 — How to Actually Learn Embedded Cryptography](#chapter-57--how-to-actually-learn-embedded-cryptography)
- [Appendices](#appendices)
  - [Appendix A — Algorithm Reference](#appendix-a--algorithm-reference)
  - [Appendix B — Mode of Operation Reference](#appendix-b--mode-of-operation-reference)
  - [Appendix C — Crypto Cheat Sheet](#appendix-c--crypto-cheat-sheet)
  - [Appendix D — Side-Channel Countermeasure Reference](#appendix-d--side-channel-countermeasure-reference)
  - [Appendix E — Glossary](#appendix-e--glossary)

---

# Part I — Orientation

---

## Chapter 1 — The Duality: Secrecy vs Authenticity

Symmetric cryptography serves exactly two purposes. Memorize this before anything else.

**Secrecy** means that an adversary who intercepts your ciphertext cannot recover your plaintext. The adversary sees noise. This is *confidentiality*.

**Authenticity** means that a recipient who receives a message and a tag can verify that the message was produced by someone who holds the key, and that it was not modified in transit. This is *integrity* combined with *authentication*.

These are not the same thing. They are not interchangeable. They do not imply each other.

```
┌──────────────────────────────────────────────────────────┐
│              The Symmetric Crypto Duality                │
├─────────────────────────┬────────────────────────────────┤
│      SECRECY            │       AUTHENTICITY             │
│   (Confidentiality)     │   (Integrity + Auth)           │
├─────────────────────────┼────────────────────────────────┤
│  Adversary cannot read  │  Adversary cannot forge        │
│  the message            │  or tamper undetected          │
├─────────────────────────┼────────────────────────────────┤
│  Primitive: cipher      │  Primitive: MAC                │
├─────────────────────────┼────────────────────────────────┤
│  Output: ciphertext     │  Output: tag / HMAC            │
├─────────────────────────┼────────────────────────────────┤
│  Key used to encrypt    │  Key used to authenticate      │
│  and decrypt            │  (same key, separate use)      │
└─────────────────────────┴────────────────────────────────┘
```

The fundamental error beginners make is assuming that encryption provides authentication. It does not. AES-CBC encryption, applied alone, hides your message — but an attacker who flips bits in the ciphertext will produce a different plaintext on decryption, with no indication to the receiver that tampering occurred. Confidentiality without authentication is usually dangerous.

The second error is assuming that authentication provides secrecy. It does not. A MAC proves the message came from a key-holder and was not modified. It reveals the message in full.

Most real systems need both. The solution to needing both is *Authenticated Encryption with Associated Data* (AEAD), which delivers secrecy and authenticity in a single primitive. AEAD is the correct default for embedded systems in 2024. You will learn why in Chapter 8.

> **Principle 1.** *Encryption without authentication is rarely sufficient; authentication without encryption is sometimes sufficient; AEAD is the right default.*

---

## Chapter 2 — The Threat Model for Embedded Systems

Before choosing an algorithm, identify your adversary. The threat model for an embedded device differs from the threat model for a cloud server in three critical ways.

**Physical access.** An adversary may hold the device. They can attach oscilloscopes, fault injection probes, and JTAG adapters. They can read flash under an electron microscope. The adversary is not merely network-adjacent — they are device-adjacent. This changes the threat model from *network attacker* to *local attacker with tools*.

**Constrained resources.** The device has kilobytes of RAM, megabytes of flash, and milliwatts of power budget. The cryptographic primitive must fit these constraints. A full TLS 1.3 handshake costs ~10 kB of RAM and significant flash. On an ARM Cortex-M0+ with 8 kB of RAM, this is the entire memory budget.

**Long deployment lifetime.** Embedded devices ship and are not updated for years or decades. The algorithm you choose today must remain secure — or the device must support field update — for the product's lifetime.

```
┌─────────────────────────────────────────────────────────┐
│         Embedded Threat Landscape                       │
│                                                         │
│  ┌──────────┐   Network   ┌──────────┐   Physical       │
│  │  Remote  │ ──────────► │  Device  │ ◄──────────      │
│  │ Attacker │             │          │   Local          │
│  └──────────┘             └──────────┘   Attacker       │
│                                │                        │
│  Remote threats:               │  Local threats:        │
│  • Replay attacks              │  • Side-channel        │
│  • Injection                   │  • Fault injection     │
│  • Protocol downgrade          │  • Key extraction      │
│  • Nonce reuse                 │  • Cloning             │
│  • Man-in-the-middle           │  • Debug port abuse    │
└─────────────────────────────────────────────────────────┘
```

**The STRIDE model applied to embedded crypto:**

| Threat | Crypto Mitigation |
|--------|-------------------|
| Spoofing (fake sender) | MAC / AEAD authentication |
| Tampering (modify data) | MAC / AEAD integrity |
| Repudiation | HMAC with shared secret (partial) |
| Information disclosure | Encryption (AEAD) |
| Denial of service | Out of scope for symmetric crypto |
| Elevation of privilege | Key hierarchy + HSM |

Define your threat model before selecting algorithms. The architect who skips this step will make the wrong tradeoff — hardening against remote attackers while leaving the device open to physical compromise.

> **Principle 2.** *The threat model determines the algorithm; the constraint budget determines the implementation; both must be written down before code is written.*

---

## Chapter 3 — The N Doors: Primitive Categories

There are exactly five categories of symmetric cryptographic primitive. Every algorithm you will encounter fits into one of these five.

```
┌─────────────────────────────────────────────────────────────┐
│              Five Primitive Categories                      │
│                                                             │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│   │ Block Cipher │   │ Stream Cipher│   │     MAC      │    │
│   │              │   │              │   │              │    │
│   │ Fixed-size   │   │ Keystream    │   │ Auth tag     │    │
│   │ permutation  │   │ generator    │   │ only         │    │
│   └──────────────┘   └──────────────┘   └──────────────┘    │
│                                                             │
│   ┌──────────────┐   ┌──────────────┐                       │
│   │     AEAD     │   │     KDF      │                       │
│   │              │   │              │                       │
│   │ Enc + Auth   │   │ Key material │                       │
│   │ combined     │   │ derivation   │                       │
│   └──────────────┘   └──────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

**Block cipher.** Takes a fixed-length block of plaintext and a key; produces a fixed-length block of ciphertext. AES operates on 128-bit blocks. The block cipher alone is not usable for messages of arbitrary length — that requires a mode of operation (Chapter 14).

**Stream cipher.** Generates a pseudorandom keystream from a key and nonce; the keystream is XOR'd with plaintext to produce ciphertext. ChaCha20 is the dominant modern stream cipher. Operation is symmetric: XOR again to decrypt.

**MAC (Message Authentication Code).** Takes a key and a message; produces a short fixed-length tag. The tag proves the message was produced by a key-holder. HMAC-SHA256 and AES-CMAC are the two workhorses.

**AEAD (Authenticated Encryption with Associated Data).** Combines encryption and authentication in a single primitive with a single key. The associated data (AD) is authenticated but not encrypted — useful for headers that must be readable in cleartext. AES-GCM and ChaCha20-Poly1305 are the two dominant AEAD schemes in embedded use.

**KDF (Key Derivation Function).** Takes a high-entropy secret (a master key or shared secret) and derives multiple independent keys from it. HKDF and SP 800-108 KDFs are the standards. KDFs are not encryption and not authentication — they are key material generators.

Hold this taxonomy. Every algorithm selection question reduces to: which category do I need?

> **Principle 3.** *If you cannot name the category of the primitive you are deploying, you do not yet understand your own system.*

---

## Chapter 4 — The Constraint Triad

Embedded cryptography is an engineering tradeoff among three competing constraints. They cannot all be maximized simultaneously.

```
                    Security
                       ▲
                      /|\
                     / | \
                    /  |  \
                   /   |   \
                  /    |    \
                 /     |     \
                /      |      \
     Performance ─────────────── Code size / RAM
```

**Security** is the cryptographic strength of the algorithm and implementation. It includes algorithm-level security (key size, block size, number of rounds) and implementation-level security (resistance to side channels, fault injection).

**Performance** is throughput (bytes per second of data encrypted or authenticated) and latency (time to complete a single operation). On embedded targets, performance is measured in clock cycles per byte.

**Code size / RAM** is the flash required to store the implementation and the RAM required to run it. A software AES implementation with all precomputed tables is fast but costs ~4 kB of RAM for the S-box tables. A table-less implementation saves RAM at a performance cost.

Every real design decision is a point on this triangle. The embedded architect's job is to find the point that satisfies the security requirement within the performance and memory budget.

The triangle has three canonical positions:

| Position | Security | Performance | Size | Example |
|----------|----------|-------------|------|---------|
| Secure, fast | High | High | Large | Hardware AES + GCM acceleration |
| Secure, small | High | Low | Small | Software AES, no tables |
| Fast, small | Variable | High | Small | Hardware-only, fixed algorithm |

The position labeled "Secure, fast, small" does not exist in the software domain. In hardware it does — a dedicated AES core is all three — which is why hardware acceleration exists.

> **Principle 4.** *Security, performance, and code size form a triangle; you choose two and pay for the third.*

---

# Part II — Anatomy

---

## Chapter 5 — Block Ciphers

A block cipher is a keyed permutation on a fixed-size input. Memorize this definition.

*Keyed*: the mapping from input to output depends on the key. Without the key, the permutation is computationally indistinguishable from a random permutation.

*Permutation*: every input maps to exactly one output; every output has exactly one input. The function is bijective. This means decryption exists: given the key and ciphertext, you recover the unique plaintext.

*Fixed-size input*: AES operates on exactly 128 bits. Not 127, not 129. A block cipher is not a streaming function — it processes one block at a time.

```
┌──────────────────────────────────────────────────────────┐
│                   Block Cipher Structure                 │
│                                                          │
│   Plaintext (128 bits)                                   │
│         │                                                │
│         ▼                                                │
│   ┌───────────────────────────────┐                      │
│   │          AES / Block Cipher   │ ← Key (128/192/256b) │
│   │                               │                      │
│   │   Round 1 ─► Round 2 ─► ...  │                       │
│   │         ─► Round N            │                      │
│   └───────────────────────────────┘                      │
│         │                                                │
│         ▼                                                │
│   Ciphertext (128 bits)                                  │
│                                                          │
│   Decryption: same key, inverse operations               │
└──────────────────────────────────────────────────────────┘
```

**AES** (Advanced Encryption Standard, FIPS 197) is the block cipher. Not a block cipher. The field has converged on AES because it is standardized, hardware-accelerated on virtually every modern processor, and has withstood over two decades of cryptanalysis without a practical break.

AES has three key sizes: 128, 192, and 256 bits. AES-128 is the standard choice. The key size determines the number of rounds: 10 for 128-bit keys, 12 for 192-bit, 14 for 256-bit.

**The security margin of AES-128** is large. The best known attacks against AES-128 are computationally infeasible. Against AES-256, there exists a related-key attack that is still computationally infeasible in practice but theoretically interesting. For embedded systems, AES-128 is almost always the right choice — it is faster and uses less RAM for the key schedule than AES-256.

**PRESENT** and **SIMON** / **SPECK** are lightweight block ciphers designed for extremely constrained devices — sub-kilobyte implementations on 8-bit microcontrollers. They trade security margin for size. Deploy these only when AES is genuinely too expensive and you have cryptographic expertise in-house to evaluate the reduced security margin. In practice, hardware AES cores exist even in very small ARM Cortex-M0 devices, making lightweight cipher deployment rare.

> **Principle 5.** *AES is the block cipher. Deploy alternatives only with documented justification — hardware AES is available on almost every target that ships in volume today.*

---

## Chapter 6 — Stream Ciphers

A stream cipher generates a pseudorandom keystream from a key and a nonce (number used once), then XOR's that keystream with the plaintext.

```
   Key ─────┐
            ▼
   Nonce ──► [Stream Cipher] ──► Keystream: k₀ k₁ k₂ k₃ ...
                                                │
   Plaintext: p₀ p₁ p₂ p₃ ...                  │
         XOR ─────────────────────────────────►│
                                                ▼
   Ciphertext: c₀ c₁ c₂ c₃ ...
```

XOR is the entire encryption operation. Decryption is identical: XOR the keystream with the ciphertext to recover the plaintext. The stream cipher's security requirement is absolute: each (key, nonce) pair must generate the keystream exactly once, and the keystream must be indistinguishable from random.

**ChaCha20** (RFC 8439) is the dominant modern stream cipher. It is software-friendly — designed without lookup tables, using only addition, rotation, and XOR (ARX construction). On hardware without AES acceleration, ChaCha20 outperforms AES-CTR. On hardware with AES acceleration, AES-CTR wins.

**RC4** is dead. Do not use it. Its keystream has statistical biases exploitable after modest observation. Every modern protocol that supported RC4 has deprecated it.

**The nonce requirement is absolute.** If you encrypt two messages with the same (key, nonce) pair in a stream cipher, XOR-ing the two ciphertexts gives XOR of the two plaintexts. This is the two-time-pad attack. In practice it degrades to complete plaintext recovery with known-plaintext assistance. Nonce misuse resistance is addressed in Chapter 13.

The stream cipher's advantage over a block cipher in raw streaming applications is: no block boundary alignment, no padding, and natural parallelism. Its disadvantage is that it provides confidentiality only — no authentication.

> **Principle 6.** *A stream cipher used twice with the same nonce provides no security. The nonce uniqueness requirement is not optional.*

---

## Chapter 7 — Message Authentication Codes

A MAC takes a key K and a message M and produces a tag T. The tag is short — typically 128 bits (16 bytes) — and fixed-length regardless of message length. Anyone holding K can verify the tag.

```
                 ┌──────────────────────┐
   Key K ───────►│                      │
                 │    MAC Algorithm     │──► Tag T (128 bits)
   Message M ───►│                      │
                 └──────────────────────┘

   Verification:
   Recompute T' = MAC(K, M)
   Accept iff T' == T  (constant-time comparison)
```

A MAC is a symmetric authentication primitive. It proves:
1. The message was processed by someone holding K.
2. The message was not modified since the tag was computed.

It does not prove identity beyond "key-holder". In a two-party symmetric system, both parties hold K, so the MAC proves one of the two parties sent the message — not which one. Non-repudiation requires asymmetric cryptography.

**HMAC-SHA256** is HMAC (RFC 2104) instantiated with SHA-256. It is universally trusted, widely implemented, and has a clean security proof. Output is 256 bits; it is common to truncate to 128 bits (HMAC-SHA256/128) for embedded use.

**AES-CMAC** (NIST SP 800-38B) is a MAC built from AES. It has a 128-bit output and benefits directly from hardware AES acceleration. It is the right choice on any embedded target with a hardware AES core.

**Poly1305** is a one-time MAC designed to be paired with ChaCha20 (forming ChaCha20-Poly1305). It is not independently deployable as a stand-alone MAC in most embedded protocols.

The two cardinal sins of MAC deployment: using the wrong comparison function, and using a MAC as a hash.

*Wrong comparison*: `if (computed_tag == received_tag)` in a language or system where `==` short-circuits, enabling timing side-channel attacks. Always use constant-time comparison. Every well-maintained crypto library provides this.

*MAC as hash*: a MAC with a known key is not a hash. A MAC with a secret key and public key is dangerous — see HMAC's ipad/opad construction for why naive MAC-from-hash fails.

> **Principle 7.** *Always compare MAC tags in constant time. A single early-exit comparison leaks the length of the matching prefix and can be exploited.*

---

## Chapter 8 — Authenticated Encryption with Associated Data

AEAD is the correct default for embedded systems. It delivers both confidentiality and authenticity in a single primitive with a single key, and it does so correctly — meaning the decryption function returns authenticated plaintext or an error, never unauthenticated plaintext.

```
┌─────────────────────────────────────────────────────────────┐
│                    AEAD Encryption                          │
│                                                             │
│   Key K ───────────────────────────────────────────────┐   │
│   Nonce N ─────────────────────────────────────────┐   │   │
│   Associated Data (AD) ────────────────────────┐   │   │   │
│   Plaintext P ─────────────────────────────┐   │   │   │   │
│                                            ▼   ▼   ▼   ▼   │
│                                    ┌───────────────────┐   │
│                                    │   AEAD Encrypt    │   │
│                                    └───────────────────┘   │
│                                            │               │
│                                  ┌─────────┴──────────┐   │
│                              Ciphertext C          Tag T   │
│                                                             │
│   AD is authenticated but NOT encrypted.                   │
│   C is encrypted and authenticated.                        │
│   T authenticates both C and AD.                           │
└─────────────────────────────────────────────────────────────┘
```

**Decryption is critical:** the AEAD decryption function must verify the tag before releasing any plaintext. If verification fails, it must return an error and zero plaintext. Any implementation that returns plaintext before tag verification is broken by design.

**Associated Data** is the mechanism for authenticating metadata without encrypting it. In a network packet, the header (containing source address, destination, sequence number) is associated data; the payload is plaintext. The receiver can inspect the header without decryption, but any modification to the header will cause tag verification to fail.

**The two dominant embedded AEAD schemes:**

| Scheme | Block Cipher | MAC | HW Accel | Best For |
|--------|-------------|-----|----------|----------|
| AES-GCM | AES-CTR | GHASH | Very wide | ARM with AES engine |
| ChaCha20-Poly1305 | ChaCha20 | Poly1305 | Rare | Software-only targets |
| AES-CCM | AES-CTR | AES-CBC-MAC | Wide | IoT / constrained |
| AES-SIV | AES-CTR | AES-CMAC | Wide | Nonce-misuse resistant |

**AES-GCM** is the standard. It is hardware-accelerated on ARM Cortex-M33, M55, and most STM32/NXP/Nordic SoCs with crypto peripherals. Its weakness is nonce sensitivity: a nonce repeat under AES-GCM is catastrophic (key recovery is possible). Chapter 16 covers this in detail.

**AES-CCM** is older and slower than GCM (it requires two passes over the data) but has smaller hardware footprint. It is widely used in Bluetooth LE and IEEE 802.15.4.

**AES-SIV** (RFC 5297) is nonce-misuse resistant: a nonce repeat leaks that two plaintexts are equal, but does not break confidentiality further. Use SIV when you cannot guarantee nonce uniqueness — for example, during key provisioning before a counter is established.

> **Principle 8.** *Never release decrypted plaintext before the AEAD tag has been verified. A system that does so is broken regardless of the algorithm it uses.*

---

## Chapter 9 — Hash Functions in Symmetric Context

Hash functions appear in symmetric cryptography in supporting roles — not as encryption, not as authentication alone, but as components of MACs and KDFs.

SHA-256 and SHA-3 (Keccak) are the dominant hash functions. SHA-256 is faster on most embedded ARM targets with SHA hardware acceleration. SHA-3 is preferred in newer designs for its sponge construction, which cleanly generalizes to SHAKE (variable-length output) and offers better properties for KDF use.

**The embedded hash landscape:**

| Function | Output | Speed (sw, ARM M4) | HW Accel |
|----------|--------|---------------------|----------|
| SHA-256 | 256 b | ~15 cycles/byte | Yes, most STM32/NXP |
| SHA-512 | 512 b | ~25 cycles/byte | Less common |
| SHA3-256 | 256 b | ~20 cycles/byte | Rare |
| BLAKE2s | 256 b | ~12 cycles/byte | Rare |
| BLAKE3 | 256 b | ~8 cycles/byte | Very rare |

**BLAKE2s** is optimized for 32-bit platforms (the "s" stands for small). It outperforms SHA-256 in software and is a strong choice for embedded KDF and MAC applications where hardware SHA acceleration is absent.

**Hash functions are not MACs.** `H(key || message)` is vulnerable to length extension attacks on SHA-256. `H(message)` has no authentication property at all. HMAC's construction (double-hash with padded keys) exists precisely to make a MAC from a hash correctly.

Hash functions are also not random number generators and not encryption. Their deterministic nature means that `H(secret)` for a small-domain secret is breakable by exhaustive search over the domain.

> **Principle 9.** *A hash function produces a collision-resistant fingerprint; without a secret key in the correct position, it provides no authentication.*

---

## Chapter 10 — Block Ciphers vs Stream Ciphers

This is the comparison that trips up architects who have not internalized the operational difference.

```
┌──────────────────────────────────────────────────────────────┐
│            Block Cipher vs Stream Cipher                     │
├──────────────────────────┬───────────────────────────────────┤
│      BLOCK CIPHER        │       STREAM CIPHER               │
│      (AES)               │       (ChaCha20)                  │
├──────────────────────────┼───────────────────────────────────┤
│ Fixed 128-bit blocks     │ Arbitrary byte count              │
├──────────────────────────┼───────────────────────────────────┤
│ Needs mode of operation  │ Ready to use directly             │
│ for streaming data       │ (key + nonce)                     │
├──────────────────────────┼───────────────────────────────────┤
│ Decryption ≠ Encryption  │ Decryption = Encryption (XOR)     │
│ (usually; CTR mode is    │                                   │
│ XOR like stream ciphers) │                                   │
├──────────────────────────┼───────────────────────────────────┤
│ Parallelizable (GCM,CTR) │ Parallelizable (ChaCha is)        │
│ Sequential (CBC)         │                                   │
├──────────────────────────┼───────────────────────────────────┤
│ Hardware accelerated     │ Usually software                  │
│ nearly everywhere        │                                   │
├──────────────────────────┼───────────────────────────────────┤
│ Best for: targets with   │ Best for: software-only targets,  │
│ hardware AES             │ IoT without AES HW               │
└──────────────────────────┴───────────────────────────────────┘
```

In practice, the choice is almost always made for you: if your target has a hardware AES core (it almost certainly does), use AES in GCM or CCM mode. If your target is a bare 8-bit MCU with no hardware acceleration, evaluate ChaCha20-Poly1305.

The important mechanical difference: a block cipher in CTR mode *behaves* like a stream cipher. CTR mode converts the block cipher into a keystream generator. From the user's perspective, AES-CTR and ChaCha20 are operationally similar — both produce a keystream that XORs with plaintext. The difference is in the underlying primitive and hardware availability.

> **Principle 10.** *A block cipher in CTR mode is functionally a stream cipher; the distinction that matters architecturally is hardware acceleration availability, not the primitive category.*

---

## Chapter 11 — Encryption vs Authentication: The Dangerous Conflation

This chapter exists because this conflation has caused more real-world vulnerabilities than almost any other conceptual error in cryptographic engineering.

**Encryption does not authenticate.** A ciphertext produced by AES-CBC, AES-CTR, or ChaCha20 (alone, without a MAC) is malleable. An attacker who does not know the key can still modify the ciphertext in predictable ways that produce predictable changes in the plaintext. This is not a theoretical concern — it is the mechanism behind the POODLE attack (AES-CBC-SSLv3), the BEAST attack, and numerous embedded protocol vulnerabilities.

**Authentication does not encrypt.** AES-CMAC or HMAC-SHA256 applied to a plaintext message reveals the plaintext in full. It proves only that the message came from a key-holder.

**Encrypt-then-MAC** is the correct composition when AEAD is unavailable. Apply encryption first, then compute the MAC over the ciphertext. Do not compute MAC over plaintext and then encrypt (MAC-then-Encrypt) — this enables plaintext recovery via padding oracle attacks in CBC mode. Do not encrypt and MAC independently (Encrypt-and-MAC) — this leaks information about the plaintext in the MAC.

```
┌──────────────────────────────────────────────────────────────┐
│         Three Compositions (and Which to Use)                │
│                                                              │
│  Encrypt-then-MAC:                                           │
│  P ──►[Encrypt]──► C ──►[MAC]──► T          ✓ CORRECT       │
│                    └──────────────────────────────────┘      │
│                    MAC over ciphertext                       │
│                                                              │
│  MAC-then-Encrypt:                                           │
│  P ──►[MAC]──► T                             ✗ DANGEROUS     │
│  P||T ──►[Encrypt]──► C                                      │
│  (enables padding oracle on decryption)                      │
│                                                              │
│  Encrypt-and-MAC:                                           │
│  P ──►[Encrypt]──► C                         ✗ WRONG        │
│  P ──►[MAC]──► T                                             │
│  (MAC may leak plaintext info)                               │
│                                                              │
│  AEAD:                                                       │
│  P,AD,K,N ──►[AEAD]──► C,T                  ✓ BEST          │
└──────────────────────────────────────────────────────────────┘
```

The existence of AEAD eliminates the need to reason about composition. AEAD is correct by construction — the algorithm designers have already handled the composition correctly. On embedded systems, always prefer AEAD over manual composition of cipher + MAC.

> **Principle 11.** *Never compose encryption and authentication by hand. Use AEAD, which delivers the correct composition by construction.*

---

# Part III — Configuration and Composition

---

## Chapter 12 — Keys: Sizes, Types, and Lifetimes

A symmetric key is a secret byte sequence. It has three properties: size, type, and lifetime.

**Size.** The key size determines the security level.

| Key Size | Algorithm | Security Level | Quantum Security |
|----------|-----------|----------------|-----------------|
| 128 bits | AES-128 | 128 bits | 64 bits (Grover) |
| 192 bits | AES-192 | 192 bits | 96 bits |
| 256 bits | AES-256 | 256 bits | 128 bits |
| 256 bits | ChaCha20 | 256 bits | 128 bits |
| 256 bits | HMAC-SHA256 | 128 bits effective | 64 bits |

Security level means: an attacker without the key requires approximately 2^(security_level) operations to break the scheme. AES-128 provides 128-bit classical security — computationally infeasible with any foreseeable classical computer. Grover's algorithm halves the key search space on a quantum computer, but 64-bit quantum security remains infeasible with realistic quantum hardware timelines for embedded device lifetimes through the 2030s.

AES-128 is the correct default. Use AES-256 only when mandated by compliance requirements (some government and classified frameworks require it) or when the device has a post-2030 projected lifetime and quantum risk is considered material.

**Type.** Keys have roles. A key management hierarchy distinguishes:

- *Root key*: the top-level secret, provisioned at manufacturing, never derived, rarely used directly.
- *Key-encryption key (KEK)*: used only to encrypt other keys.
- *Data-encryption key (DEK)*: used only to encrypt data.
- *Session key*: ephemeral, derived per-session, discarded after session.
- *MAC key*: used only to authenticate, never to encrypt.

Using the same key for encryption and authentication is legal under some AEAD schemes but inadvisable for custom compositions. Using the same key across algorithm categories is always wrong.

**Lifetime.** Keys must have defined lifetimes. A session key lives for one session. A DEK may live until the data is re-encrypted. A root key may live for the device's lifetime. The shorter the lifetime, the smaller the blast radius if the key is compromised.

> **Principle 12.** *Every key must have a documented type, a documented lifetime, and a documented destruction procedure. Keys without documented lifetimes are effectively permanent — and permanent keys are a liability.*

---

## Chapter 13 — Nonces and IVs

A nonce (number used once) or IV (initialization vector) is a per-operation value that ensures that encrypting the same plaintext twice with the same key produces different ciphertexts. The terminology differs by mode, but the concept is the same.

**The absolute rule: a nonce must never repeat under the same key.** For most modes (AES-CTR, AES-GCM, ChaCha20), nonce repetition is catastrophic.

```
┌──────────────────────────────────────────────────────────────┐
│                 Nonce Failure Consequences                   │
│                                                              │
│  AES-GCM nonce repeat:                                       │
│  C₁ = Enc(K, N, P₁)   C₂ = Enc(K, N, P₂)                   │
│  C₁ XOR C₂ = P₁ XOR P₂  (keystream cancels)                 │
│  PLUS: authentication key H is recovered from the tags       │
│  RESULT: full key compromise possible                        │
│                                                              │
│  AES-CBC IV repeat:                                          │
│  C₁ = Enc(K, IV, P₁)  C₂ = Enc(K, IV, P₂)                  │
│  RESULT: first block comparison reveals P₁[0] XOR P₂[0]     │
│  (weaker than CTR/GCM but still a confidentiality break)     │
│                                                              │
│  AES-SIV nonce repeat:                                       │
│  RESULT: reveals P₁ == P₂ only. Confidentiality preserved.  │
└──────────────────────────────────────────────────────────────┘
```

**Nonce generation strategies on embedded devices:**

*Counter (preferred)*: maintain a 64-bit or 96-bit counter in non-volatile storage, incrementing it before each encryption. Guarantees uniqueness across power cycles if the counter is persisted correctly. The risk is counter rollback — if the counter is lost (power loss before NVM write commits), the same nonce value may be reused.

*Random*: generate the nonce from the hardware TRNG. Suitable for nonces of 96 bits or more, where the birthday problem requires approximately 2^48 encryptions before a collision is expected. Unsuitable for small nonce sizes.

*Epoch + counter*: combine a timestamp or power-cycle counter with a per-session monotonic counter. Robust against power loss; requires a clock source.

**Nonce size:**

| Mode | Nonce Size | Strategy |
|------|-----------|----------|
| AES-GCM | 96 bits | Counter or Random |
| AES-CCM | 7–13 bytes | Counter |
| ChaCha20 | 96 bits | Counter or Random |
| AES-CBC | 128 bits | Random (and unpredictable) |
| AES-SIV | Optional | Any (misuse resistant) |

For AES-CBC, the IV must be *unpredictable*, not merely unique. A predictable IV enables chosen-plaintext attacks (as demonstrated against BEAST). Use TRNG output.

> **Principle 13.** *A nonce is an operational parameter, not a security parameter you can approximate. Nonce uniqueness is a hard requirement; nonce unpredictability is additionally required for some modes.*

---

## Chapter 14 — Modes of Operation: The Universal Wrapper

A block cipher encrypts exactly one block. Modes of operation are the mechanisms that extend a block cipher to arbitrary-length messages. They are universal — the same mode taxonomy applies regardless of which block cipher you use.

```
┌──────────────────────────────────────────────────────────────┐
│              Mode of Operation: Concept                      │
│                                                              │
│   Block cipher B: 128-bit → 128-bit keyed permutation       │
│   Mode M: extends B to handle messages of any length        │
│                                                              │
│   AES + Mode = a usable encryption/authentication scheme    │
│                                                              │
│   The block cipher is a primitive.                           │
│   The mode of operation is the design.                       │
│   You must choose both.                                      │
└──────────────────────────────────────────────────────────────┘
```

Modes divide into three families:

**Confidentiality modes**: ECB, CBC, CTR, OFB, CFB. These provide encryption only. Never deploy these alone on authenticated channels — they must be paired with a MAC.

**Authentication modes**: CMAC, GMAC. These provide authentication only.

**Authenticated encryption modes**: CCM, GCM, EAX, SIV. These provide both. Use these.

A critical misconception: the mode of operation is separate from the block cipher. AES-GCM means "AES block cipher, GCM mode." Changing the mode changes the security properties dramatically. AES-ECB provides almost no security for structured data. AES-GCM provides confidentiality and authentication. The block cipher is the same; the properties are entirely different.

> **Principle 14.** *The block cipher determines the computational security; the mode of operation determines the functional security properties. Choose the mode with at least as much care as the cipher.*

---

## Chapter 15 — ECB, CBC, CTR: The Three Foundational Modes

These three modes underlie almost every other mode and much historical protocol design. You must understand them to read existing protocol specifications, to debug legacy systems, and to understand why newer modes were designed.

**ECB — Electronic Codebook**

ECB is the trivial mode: encrypt each block independently.

```
   P₁ ──►[AES_K]──► C₁
   P₂ ──►[AES_K]──► C₂
   P₃ ──►[AES_K]──► C₃
```

ECB is broken for structured data. Equal plaintext blocks produce equal ciphertext blocks. The famous ECB penguin — where encrypting a bitmap image in ECB mode produces a ciphertext that still shows the penguin's outline — demonstrates this definitively. Never use ECB for any data that has patterns. The only legitimate use is encrypting single independent blocks (e.g., wrapping a single key) — and even there, authenticated modes are preferred.

**CBC — Cipher Block Chaining**

CBC XOR's each plaintext block with the previous ciphertext block before encryption.

```
   IV ──┐   C₁ ──┐   C₂ ──┐
        │         │         │
        ▼         ▼         ▼
   P₁ ─► XOR ─►[AES]──► C₁ ─► XOR ─►[AES]──► C₂ ─► ...
```

CBC requires a random, unpredictable IV. It is sequential — each block depends on all previous blocks, so it cannot be parallelized for encryption (decryption can be parallelized). CBC is vulnerable to padding oracle attacks when the decryption function reveals padding validity. PKCS#7 padding with CBC and an exposed decryption oracle is the classic vulnerability.

CBC is a confidentiality-only mode. It does not authenticate. CBC without a MAC is the root cause of a large class of historical embedded vulnerabilities.

**CTR — Counter Mode**

CTR generates a keystream by encrypting successive counter values, then XOR's with plaintext.

```
   Nonce||0 ──►[AES_K]──► keystream block 0 ──► XOR P₁ = C₁
   Nonce||1 ──►[AES_K]──► keystream block 1 ──► XOR P₂ = C₂
   Nonce||2 ──►[AES_K]──► keystream block 2 ──► XOR P₃ = C₃
```

CTR mode converts AES into a stream cipher. Encryption and decryption are identical (both XOR with the keystream). CTR is fully parallelizable. It requires nonce uniqueness but not unpredictability (unlike CBC's IV). CTR does not authenticate. CTR is the foundation of GCM (which adds GHASH authentication).

The counter format (how Nonce and counter are combined into the 128-bit AES input) matters and varies by implementation. AES-CTR with standardized counter format (NIST SP 800-38A) uses a 32-bit counter and 96-bit nonce. Verify your library's counter format before interoperating.

> **Principle 15.** *ECB reveals structure; CBC is sequential and padding-oracle vulnerable; CTR is a stream cipher from a block cipher. None of these three modes is safe to use alone for authenticated communications.*

---

## Chapter 16 — GCM and CCM: AEAD Modes in Practice

GCM (Galois/Counter Mode) and CCM (Counter with CBC-MAC) are the two AEAD modes you will deploy most often on embedded systems. They share CTR mode for encryption but differ in how they compute the authentication tag.

**GCM — Galois/Counter Mode**

GCM combines AES-CTR for encryption with GHASH for authentication. GHASH is a polynomial evaluation over GF(2¹²⁸) — the details are in Chapter 21.

```
┌─────────────────────────────────────────────────────────────┐
│                      AES-GCM                                │
│                                                             │
│   Nonce/IV (96 bits)                                        │
│         │                                                   │
│    ┌────┴─────┐      ┌──────────┐      ┌──────────┐         │
│    │ Nonce||1 │─►AES►│ E(K,Y₀) │      │  GHASH   │         │
│    └──────────┘      └────┬─────┘      └────┬─────┘         │
│                           │  Auth tag       │               │
│    ┌──────────┐      ┌────┴─────┐           │               │
│    │ Nonce||2 │─►AES►│         │►XOR►C₁    │               │
│    └──────────┘      └──────────┘  ▲         │               │
│         P₁ ─────────────────────────┘         │               │
│                                               │               │
│   AD ──────────────────────────────────────► GHASH ──► Tag  │
│   C  ──────────────────────────────────────►         (128b) │
└─────────────────────────────────────────────────────────────┘
```

GCM properties:
- Single pass over data for encryption; GHASH can be pipelined
- Hardware GHASH acceleration exists on many ARM Cortex-M33+ cores
- Nonce: 96 bits recommended; other sizes require GHASH pre-processing and add complexity
- Nonce repeat: catastrophic (see Chapter 13)
- Minimum tag size: 128 bits recommended; 96 bits acceptable; below 64 bits dangerous

**CCM — Counter with CBC-MAC**

CCM computes CBC-MAC over the plaintext and associated data, then encrypts the CBC-MAC result and the plaintext with CTR mode.

CCM requires two passes: one to compute CBC-MAC, one to encrypt. This makes CCM 2× slower than GCM for large messages. However, CCM's hardware footprint is smaller — it requires only an AES block cipher, where GCM additionally requires a GHASH multiplier.

CCM is mandatory in:
- Bluetooth LE (AES-CCM-128, 4-byte tag)
- IEEE 802.15.4 / Zigbee / Thread (AES-CCM-128, 4 or 8-byte tag)
- DTLS 1.2 over constrained networks (RFC 7925)

CCM limitations: the message length must be known before encryption begins (needed for the CBC-MAC header). This precludes streaming encryption of unknown-length data.

**Choosing between GCM and CCM:**

| Criterion | GCM | CCM |
|-----------|-----|-----|
| Hardware GHASH available | Strongly prefer GCM | — |
| Protocol mandated | — | BLE, 802.15.4 |
| Streaming (unknown length) | Yes | No |
| Single-pass | Yes | No |
| Hardware footprint | Larger | Smaller |
| Nonce misuse | Catastrophic | Also catastrophic |

> **Principle 16.** *GCM is the AEAD mode for most embedded systems with hardware acceleration; CCM is the mode when protocol mandates it or when GHASH hardware is absent.*

---

## Chapter 17 — Padding and Padding Oracles

Padding is the mechanism for extending a plaintext to a multiple of the block size when using CBC mode. It is a source of vulnerability that has been exploited repeatedly in embedded protocols.

**PKCS#7 padding:** append N bytes each with value N to reach the next block boundary.

```
   Plaintext: [A B C D E F G H I J K]  (11 bytes)
   Block size: 16 bytes
   Bytes to pad: 5
   Padded: [A B C D E F G H I J K 05 05 05 05 05]
```

On decryption, the receiver strips the padding by reading the last byte value and removing that many bytes, after verifying that all removed bytes equal the count. If the padding is invalid, the decryption fails.

**The padding oracle:** an oracle is any mechanism by which an attacker can learn whether decrypted padding is valid, without learning the plaintext. It may be a distinct error code ("invalid padding" vs "invalid MAC"), a timing difference, or a different HTTP response code.

With a padding oracle and any CBC ciphertext, an attacker can recover the plaintext byte by byte without the key. This attack (Vaudenay 2002) is the basis of the POODLE attack, the Lucky13 attack, and numerous embedded protocol vulnerabilities.

**The cure:** always check the MAC before checking padding. In Encrypt-then-MAC, the MAC check happens first; if the MAC fails, the ciphertext is rejected without decryption. Padding validity is never exposed. In MAC-then-Encrypt (used by TLS up to 1.2), the MAC check happens after decryption, when padding has already been validated — enabling the oracle.

The better cure: use AEAD, which has no padding. AES-GCM, AES-CCM, and ChaCha20-Poly1305 do not use PKCS#7 padding because CTR mode requires no block alignment.

> **Principle 17.** *Padding is a block cipher artifact; AEAD eliminates it. If you are designing a new protocol, design it to use AEAD and inherit zero padding logic.*

---

# Part IV — Mechanism and Internals

---

## Chapter 18 — Inside AES: The Four Operations

AES operates on a 4×4 array of bytes called the *state*. The 128-bit plaintext is loaded into this array in column-major order. Ten, twelve, or fourteen rounds of four operations transform the state into ciphertext.

```
   State array (4×4 bytes):
   ┌─────┬─────┬─────┬─────┐
   │ s₀₀ │ s₀₁ │ s₀₂ │ s₀₃ │   Row 0
   ├─────┼─────┼─────┼─────┤
   │ s₁₀ │ s₁₁ │ s₁₂ │ s₁₃ │   Row 1
   ├─────┼─────┼─────┼─────┤
   │ s₂₀ │ s₂₁ │ s₂₂ │ s₂₃ │   Row 2
   ├─────┼─────┼─────┼─────┤
   │ s₃₀ │ s₃₁ │ s₃₂ │ s₃₃ │   Row 3
   └─────┴─────┴─────┴─────┘
```

**SubBytes (S-box substitution):** Replace each byte with a non-linear substitute from the AES S-box lookup table. The S-box is constructed from the multiplicative inverse in GF(2⁸) followed by an affine transformation. This is the only non-linear operation in AES — it provides confusion.

**ShiftRows:** Rotate each row left by its row index: row 0 unchanged, row 1 shifted left by 1, row 2 by 2, row 3 by 3. This moves bytes across columns, ensuring that bytes from different columns mix in subsequent rounds — diffusion.

**MixColumns:** Multiply each column by a fixed 4×4 matrix over GF(2⁸). This mixes bytes within each column. Combined with ShiftRows, after two rounds every output byte depends on every input byte — the full diffusion criterion.

**AddRoundKey:** XOR the state with the round key derived from the AES key schedule (Chapter 19). This is the only step that incorporates the key.

```
   One AES Round:
   State ──► SubBytes ──► ShiftRows ──► MixColumns ──► AddRoundKey ──► State'
   
   Final round omits MixColumns (by design — it is invertible and its omission
   makes encryption and decryption structurally symmetric).
```

**Why internals matter for implementation:** SubBytes is implemented as a 256-byte lookup table. Table lookups on processors with data caches produce timing variations based on which cache line is hit — this is the source of cache-timing side-channel attacks against software AES (Chapter 31). Hardware AES units execute SubBytes in constant time using combinational logic, eliminating this attack.

On ARM Cortex-M cores with hardware AES (AES extension on Cortex-M33, Cortex-M55), use the hardware instructions. Never implement software AES for production code on targets with hardware AES unless you have implemented masking countermeasures.

> **Principle 18.** *Software AES is vulnerable to cache-timing attacks on processors with data caches. Hardware AES eliminates this attack. On targets with hardware AES, software AES is the wrong implementation choice.*

---

## Chapter 19 — The AES Key Schedule

The AES key schedule expands the N-bit key into (rounds + 1) × 128-bit round keys. For AES-128, this is 11 × 128 bits = 1408 bits = 176 bytes of round key material.

```
   AES-128 Key Schedule (schematic):
   
   K[0..3] = {W0, W1, W2, W3}   (original 128-bit key as 4 words)
   
   For i = 4 to 43:
     temp = W[i-1]
     if i ≡ 0 (mod 4):
       temp = SubWord(RotWord(temp)) XOR Rcon[i/4]
     W[i] = W[i-4] XOR temp
   
   Round key j = {W[4j], W[4j+1], W[4j+2], W[4j+3]}
```

The key schedule has a critical weakness: AES-128's key schedule is invertible. If an attacker recovers any round key, they can compute the original key. For AES-256, there exist related-key attacks that exploit algebraic structure in the key schedule, though these are not practical breaks.

**RAM vs flash tradeoff in key schedule:** Precomputing all round keys requires 176 bytes of RAM (AES-128) or 240 bytes (AES-256). If RAM is the bottleneck, you can recompute round keys on the fly from the original key at the cost of additional AES operations per round. Some embedded implementations store only the first and last round keys and recompute from both ends for encryption and decryption respectively.

**Key schedule for decryption:** AES decryption uses inverse operations (InvSubBytes, InvShiftRows, InvMixColumns, AddRoundKey). The round keys are used in reverse order, and the middle round keys require an InvMixColumns transformation. If your application only decrypts (e.g., a receive-only sensor), precompute the decryption round keys, not encryption round keys.

> **Principle 19.** *Recovery of any AES round key is equivalent to recovery of the master key. Protect all round keys with the same diligence as the original key.*

---

## Chapter 20 — Inside ChaCha20: The Quarter-Round

ChaCha20 (RFC 8439) operates on a 512-bit (64-byte) state organized as a 4×4 matrix of 32-bit words. The state is initialized from a constant, the 256-bit key, a 32-bit counter, and a 96-bit nonce.

```
   ChaCha20 Initial State:
   ┌────────┬────────┬────────┬────────┐
   │ "expa" │ "nd 3" │ "2-by" │ "te k" │  ← Constant "expand 32-byte k"
   ├────────┼────────┼────────┼────────┤
   │  K[0]  │  K[1]  │  K[2]  │  K[3]  │  ← Key (words 0-3)
   ├────────┼────────┼────────┼────────┤
   │  K[4]  │  K[5]  │  K[6]  │  K[7]  │  ← Key (words 4-7)
   ├────────┼────────┼────────┼────────┤
   │Counter │  N[0]  │  N[1]  │  N[2]  │  ← Counter + Nonce
   └────────┴────────┴────────┴────────┘
```

The core operation is the **quarter-round**, applied to four words (a, b, c, d):

```
   a += b;  d ^= a;  d <<<= 16;
   c += d;  b ^= c;  b <<<= 12;
   a += b;  d ^= a;  d <<<= 8;
   c += d;  b ^= c;  b <<<= 7;
```

Only addition, XOR, and rotation (ARX). No lookup tables, no branches. The lack of table lookups makes ChaCha20 naturally constant-time — the timing is independent of the key and data values. This is why ChaCha20 is preferred over AES in software-only contexts: it eliminates the cache-timing attack surface without additional countermeasures.

Twenty rounds (ten double-rounds) are applied to the state. The final state is added to the initial state word by word, and the result is the 64-byte keystream block. Successive counter values produce successive keystream blocks.

**Performance:** ChaCha20 achieves approximately 3–4 cycles/byte on ARM Cortex-M4 with NEON-equivalent optimization, and 6–8 cycles/byte without. AES-CTR with hardware AES acceleration achieves 1–2 cycles/byte on the same cores. Software ChaCha20 vs hardware AES: hardware wins by 3–6×.

> **Principle 20.** *ChaCha20's ARX construction is inherently constant-time without explicit countermeasures; software AES is not. Choose ChaCha20 for software-only implementations, AES for hardware-accelerated targets.*

---

## Chapter 21 — GHASH: Polynomial MAC over GF(2¹²⁸)

GHASH is the authentication component of GCM. Understanding it is necessary for understanding GCM's nonce-misuse catastrophe and for implementing GCM correctly.

GHASH evaluates a polynomial over GF(2¹²⁸). The field GF(2¹²⁸) is the set of 128-bit values with addition defined as XOR and multiplication defined as modular polynomial multiplication modulo the irreducible polynomial x¹²⁸ + x⁷ + x² + x + 1.

```
   GHASH(H, A, C):
   
   H = AES_K(0¹²⁸)          ← H is the hash key
   
   Process: AD blocks, then ciphertext blocks, then length block
   
   X₀ = 0
   For each 128-bit block Bᵢ:
       Xᵢ = (Xᵢ₋₁ XOR Bᵢ) · H   (multiplication in GF(2¹²⁸))
   
   GHASH output = Xₙ
```

The security of GHASH as a MAC depends on H being secret. H = AES_K(0) — the AES encryption of the all-zero block under the key. If H is revealed, the authentication is broken: an attacker who knows H can forge arbitrary GHASH values.

**The nonce-repeat catastrophe in GCM:** The final tag is computed as `GHASH(H, AD, C) XOR AES_K(Nonce||1)`. If a nonce is repeated with the same key, the term `AES_K(Nonce||1)` is the same for both encryptions. An attacker can XOR the two tags to cancel this term and recover information about the GHASH output. From two GHASH outputs with known inputs (the two ciphertexts), the attacker can solve for H. With H known, all subsequent authentication for that key is broken.

This is why AES-GCM nonce repetition is qualitatively worse than nonce repetition in CTR mode (which reveals XOR of plaintexts): in GCM, nonce repetition also compromises all future authentication.

**Hardware GHASH** is a 128-bit polynomial multiplier present in many ARM Cortex-M33 and M55 implementations. When available, it reduces the per-byte cost of GCM authentication by 4–8×.

> **Principle 21.** *In AES-GCM, a nonce repeat under the same key may allow recovery of the authentication key H, compromising all past and future authentication under that key.*

---

## Chapter 22 — CMAC and HMAC Internals

**AES-CMAC** (NIST SP 800-38B): CMAC computes a CBC-MAC over the message with a derived subkey XOR'd into the final block. The subkey derivation from the AES key ensures that CMAC is a secure PRF (pseudorandom function), avoiding the length-extension weakness of raw CBC-MAC.

```
   CMAC key derivation:
   L = AES_K(0¹²⁸)
   K₁ = L << 1  (if MSB = 0)
       = (L << 1) XOR C₁₂₈  (if MSB = 1, where C₁₂₈ is constant)
   K₂ = K₁ << 1  (similarly)
   
   CMAC computation:
   Divide M into blocks M₁, ..., Mₙ
   XOR Kₙ (or K₂ for incomplete final block) into final block
   CBC-MAC the padded/modified message
```

CMAC is direct: it requires only AES, no additional primitives. On any embedded target with hardware AES, CMAC is fast. The output is 128 bits; for bandwidth-constrained environments it is acceptable to truncate to 64 bits, though 64-bit tags allow birthday attacks after 2^32 verifications.

**HMAC** (RFC 2104): HMAC constructs a MAC from any hash function. For HMAC-SHA256:

```
   HMAC(K, M) = H((K XOR opad) || H((K XOR ipad) || M))
   
   ipad = 0x36 repeated 64 times (block length of SHA-256)
   opad = 0x5C repeated 64 times
```

The double-hash construction prevents length extension. HMAC is provably secure under the assumption that the underlying hash function is a PRF, which SHA-256 satisfies.

HMAC-SHA256 produces 256 bits; in embedded use, the first 128 bits (HMAC-SHA256/128) are used. This provides 128-bit security under the standard analysis.

**CMAC vs HMAC for embedded:**

| Criterion | AES-CMAC | HMAC-SHA256 |
|-----------|----------|-------------|
| Hardware acceleration | AES cores | SHA cores |
| Pure software | Needs bitsliced AES | Needs SHA-256 |
| Output size | 128 bits | 256 bits |
| Standards compliance | FIPS 198, SP 800-38B | FIPS 198 |
| Protocol use | 802.15.4, BLE | TLS, SSH, IPsec |

Use CMAC when your target has a hardware AES core and no SHA core. Use HMAC-SHA256 when your target has SHA acceleration or when interoperating with protocols that require it.

> **Principle 22.** *CMAC requires only AES; HMAC requires only a hash. Match the MAC to the hardware acceleration available on your target.*

---

## Chapter 23 — Why AES-128 Is Still Safe

The architect who reads security news will encounter claims about AES weaknesses. This chapter addresses them directly.

**Known attacks against AES:**

| Attack | AES Variant | Complexity | Practical? |
|--------|-------------|-----------|------------|
| Brute force | All | 2¹²⁸ | No |
| Biclique | AES-128 | 2¹²⁶·¹ | No (2 bits better) |
| Related-key | AES-256 | 2⁹⁹·⁵ | No (but concerning) |
| Cache timing | Software AES | Variable | Yes on caches |
| Power analysis | Unprotected HW | Low | Yes |

The biclique attack against AES-128 reduces the effective key search space by a factor of 4. This is academically interesting and practically irrelevant — 2¹²⁶ operations remain infeasible. AES-128 has no known practical mathematical break after 25+ years of analysis by the global cryptanalysis community.

The related-key attack against AES-256 is also practically irrelevant: related-key scenarios do not arise in correctly designed key management. The attack requires an attacker to encrypt under multiple related keys, which a well-designed system never permits.

**Quantum computers and AES:** Grover's algorithm provides a quadratic speedup for symmetric key search. Against AES-128, this implies 2^64 quantum operations — still infeasible with any realistic quantum computer through the foreseeable future. NIST's post-quantum guidance (NIST IR 8105) recommends AES-256 for long-term data (classification through 2030+) and accepts AES-128 for data with limited lifetime.

For embedded devices deployed in the next 5–10 years with data sensitivity lifetimes under 10 years: AES-128 is correct. For devices with 20+ year lifetimes or classified data: AES-256.

> **Principle 23.** *AES-128 has no practical mathematical weakness. The threats to AES in embedded systems are implementation attacks — side channels and fault injection — not cryptanalytic breaks.*

---

# Part V — Embedded Hardware

---

## Chapter 24 — Hardware Crypto Accelerators: Taxonomy

Hardware crypto accelerators are silicon blocks that perform cryptographic operations in dedicated logic, independent of the CPU core. They offer three advantages over software: speed, side-channel resistance, and CPU offload.

```
┌─────────────────────────────────────────────────────────────┐
│          Hardware Crypto Accelerator Taxonomy               │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               SoC / Microcontroller                  │   │
│  │                                                      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────────────┐ │   │
│  │  │   CPU    │  │  AES     │  │   SHA / HMAC       │ │   │
│  │  │ Core(s)  │  │  Engine  │  │   Accelerator      │ │   │
│  │  └──────────┘  └──────────┘  └────────────────────┘ │   │
│  │                                                      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────────────┐ │   │
│  │  │  TRNG    │  │  PKA     │  │   Secure Storage   │ │   │
│  │  │          │  │ (ECC/RSA)│  │   (OTP/eFuse)      │ │   │
│  │  └──────────┘  └──────────┘  └────────────────────┘ │   │
│  │                                                      │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │              DMA Engine                       │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**AES engine:** Implements AES-ECB at minimum. Higher-end implementations include GCM/CCM modes, DMA coupling, and key storage in hardware-protected registers. Examples: STM32 AES peripheral (L4, H5, U5), Nordic nRF52840 ECB, NXP LPC55S69 CASPER.

**SHA accelerator:** Implements SHA-256, sometimes SHA-512 and SHA-3. Usually memory-mapped with a simple write-data/read-digest interface. Significant speedup over software for large-block hashing.

**TRNG (True Random Number Generator):** Hardware entropy source based on thermal noise, ring oscillators, or metastability. Essential for key generation and nonce generation. Quality varies widely — see Chapter 27.

**PKA (Public Key Accelerator):** Implements modular arithmetic for RSA and ECC. Relevant for key exchange protocols that use symmetric keys derived from asymmetric operations.

**Secure storage:** OTP (one-time programmable) fuses or eFuses for root keys. Keys written to OTP cannot be read by software — they are accessible only to the crypto engine. This is the hardware root of trust for key provisioning.

**DMA coupling:** The DMA engine can feed data to and from the crypto engine without CPU involvement, freeing the CPU for other work during long encryption operations.

> **Principle 24.** *A hardware crypto engine is not a plug-in optimization; it is a security boundary. Understand which operations it protects from side-channel observation and which remain exposed.*

---

## Chapter 25 — AES-NI and ARM Crypto Extensions

On ARM Cortex-M33 and later (ARMv8-M), the architecture includes optional crypto extensions: hardware instructions for AES rounds and SHA. These are distinct from a dedicated AES peripheral — they are CPU-level instructions that execute within the pipeline.

**ARM Crypto Extension instructions (AES):**

| Instruction | Operation |
|-------------|-----------|
| AESE | AES single round encryption (SubBytes + ShiftRows) |
| AESD | AES single round decryption (InvSubBytes + InvShiftRows) |
| AESMC | AES MixColumns |
| AESIMC | AES inverse MixColumns |

These instructions operate on 128-bit NEON Q registers. A full AES-128 encryption requires 10 calls to AESE+AESMC plus the round key XOR operations. The pipeline cost is approximately 1 cycle per round, giving ~10 cycles per 16-byte block — roughly 0.625 cycles/byte for AES-128 encryption.

ARM Crypto Extension AES is constant-time by construction: the instruction timing is independent of data values. No cache-timing vulnerability.

**Verification that your target has crypto extensions:** not all Cortex-M33 implementations include the crypto extensions — they are optional. Check the device datasheet's "Feature List" or the CPUID register (`CPUID.PartNo` field). Most STM32H5 and STM32U5 series include them; the original Cortex-M33 reference implementations (like nRF9160) may not.

**Using extensions from C:** use a library that emits the intrinsics (Mbed TLS with MBEDTLS_AESCE_C enabled, wolfSSL with WOLFSSL_ARMASM). Writing inline assembly for AES round functions is error-prone and unnecessary when good open-source implementations exist.

> **Principle 25.** *ARM Crypto Extension AES instructions provide constant-time AES with hardware throughput from C code via library wrappers; verify their presence in your specific silicon before depending on them.*

---

## Chapter 26 — DMA-Coupled Crypto Engines

Many embedded SoCs couple the crypto engine to the DMA controller, enabling zero-copy crypto operations: data flows directly from source memory through the crypto engine to destination memory, without CPU instruction fetching for each byte.

```
┌─────────────────────────────────────────────────────────────┐
│              DMA-Coupled AES-GCM Operation                  │
│                                                             │
│  ┌──────────┐   DMA CH1   ┌───────────┐   DMA CH2          │
│  │ Plaintext│ ──────────► │           │ ──────────►         │
│  │  Buffer  │             │ AES-GCM   │  Ciphertext         │
│  └──────────┘             │  Engine   │   Buffer            │
│                           │           │                     │
│  ┌──────────┐             │           │                     │
│  │ AD Buffer│ ──────────► │           │                     │
│  └──────────┘             └───────────┘                     │
│                                 │                           │
│  CPU issues DMA config          │ Tag                       │
│  and interrupt-waits ◄──────────┘                           │
│                           DMA interrupt                     │
└─────────────────────────────────────────────────────────────┘
```

The programming model for DMA-coupled crypto:

1. Configure the AES engine: mode (GCM/CCM), direction (encrypt/decrypt), key registers, IV registers.
2. Configure DMA channel(s): source, destination, transfer size.
3. Enable DMA and start the AES engine.
4. CPU sleeps (WFI) or executes other work.
5. DMA completion interrupt fires; read the tag register.

**Common pitfalls with DMA crypto:**

*Buffer alignment:* DMA engines typically require source and destination buffers to be word-aligned (4-byte) or double-word-aligned (8-byte). Misaligned buffers produce DMA transfer errors or silently produce incorrect results on some implementations. Always align crypto buffers.

*Cache coherency:* On Cortex-M cores with D-cache (M7, M55), cache lines may buffer data that the DMA has already transferred, causing stale reads. Invalidate or clean relevant cache lines before and after DMA crypto operations. Failure to do so is a source of intermittent authentication failures.

*Header/IV programming:* the AES engine must receive the IV/nonce, then associated data, then plaintext in that order, and in exact block-aligned chunks for some implementations. Read your SoC's reference manual's "crypto engine programming sequence" section in full — the sequence varies between vendors.

> **Principle 26.** *Cache coherency violations in DMA-coupled crypto produce intermittent authentication failures that are nearly impossible to reproduce without a logic analyzer and hardware breakpoints.*

---

## Chapter 27 — True Random Number Generators on Silicon

The TRNG is the foundation of all key generation and nonce generation. A weak TRNG is a systemic vulnerability — every key generated by it is weaker than the algorithm implies.

```
┌─────────────────────────────────────────────────────────────┐
│                    TRNG Architecture                        │
│                                                             │
│  ┌─────────────────┐                                        │
│  │  Entropy Source  │  ← Ring oscillator jitter, shot noise │
│  │  (Analog noise)  │    thermal noise, metastability       │
│  └────────┬────────┘                                        │
│           │  Raw bits (may be biased)                       │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │  Health Tests    │  ← NIST SP 800-90B tests:             │
│  │  (Continuous)    │    repetition count, adaptive         │
│  └────────┬────────┘    proportion test                    │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │  Conditioner     │  ← SHA-256, AES-CBC-MAC, or XOR      │
│  │  (Whitening)     │    of multiple entropy sources        │
│  └────────┬────────┘                                        │
│           │  Conditioned output                             │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │  DRBG            │  ← CTR_DRBG (NIST SP 800-90A)        │
│  │  (Deterministic) │    instantiated from TRNG output      │
│  └────────┬────────┘                                        │
│           │  Pseudorandom output                            │
│           ▼                                                 │
│   Application (key generation, nonce generation)            │
└─────────────────────────────────────────────────────────────┘
```

**NIST SP 800-90A/B/C** is the standard framework. SP 800-90B characterizes the entropy source; SP 800-90A defines the deterministic random bit generators (DRBGs); SP 800-90C defines the combining construction.

**Common embedded TRNG failure modes:**

*Startup bias:* some TRNGs produce predictable output immediately after power-on before the entropy source has accumulated sufficient randomness. Always wait for the hardware TRNG's "ready" flag and, when available, a "health test passed" flag.

*Insufficient entropy rate:* low-entropy TRNGs produce bits slowly. Some implementations poll and accumulate bits over milliseconds. For key generation (256 bits), this delay may be acceptable; for nonce generation per-packet, it may not be. Use a DRBG seeded from the TRNG for high-rate random output.

*Correlated output under identical conditions:* two devices manufactured identically, powered from the same supply, started in the same temperature environment may produce correlated TRNG output. Include device-unique identifiers (silicon UID, MAC address) in the DRBG seed to break cross-device correlation.

*Absent health testing:* if the TRNG's noise source fails (hardware fault, manufacturing defect), health tests detect this and signal an alarm condition. Software must check for this condition. Ignoring the TRNG status register is a production vulnerability.

> **Principle 27.** *The TRNG health test alarm is not an edge case to handle gracefully — it is a catastrophic failure condition that must halt key generation and alert the system. A silently failing TRNG produces predictable keys.*

---

## Chapter 28 — Secure Elements and Hardware Security Modules

A secure element (SE) is a tamper-resistant chip dedicated to cryptographic operations and key storage. A hardware security module (HSM) is the server-side equivalent. In embedded systems, SEs appear as separate ICs (e.g., ATECC608B, STSAFE-A110, NXP SE050) or as integrated security subsystems within the SoC (e.g., ARM TrustZone + OP-TEE, STM32 SMPS).

```
┌─────────────────────────────────────────────────────────────┐
│         Secure Element vs Integrated Security               │
│                                                             │
│  ┌────────────────────┐    ┌────────────────────────────┐  │
│  │   External SE      │    │   Integrated Security      │  │
│  │   (e.g. ATECC608B) │    │   (TrustZone + SMPS)       │  │
│  │                    │    │                            │  │
│  │  + Strongest        │    │  + No external component   │  │
│  │    tamper resist    │    │  + Lower latency           │  │
│  │  + Key never leaves │    │  + Lower cost              │  │
│  │    the SE           │    │  - Tamper resistance varies│  │
│  │  - I2C/SPI latency  │    │  - Key protection is SW    │  │
│  │  - Extra component  │    │    dependent on TEE impl   │  │
│  └────────────────────┘    └────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**What a secure element provides:**

*Key isolation:* private and symmetric keys are generated and stored inside the SE's tamper-resistant boundary. They are never exported in cleartext. Cryptographic operations are invoked via API — `SE_Sign()`, `SE_Encrypt()` — and the SE returns only the result.

*Physical tamper resistance:* SE packages include active shielding, sensors for voltage glitching and temperature extremes, and memory scrambling. Attempting to extract keys physically destroys them.

*Secure key provisioning:* manufacturing can inject root keys into the SE via a secure protocol, even in untrusted factory environments, because the key never passes through the main MCU bus in cleartext.

**Limitations of secure elements:**

The SE only protects the key. It does not protect the application's use of the key. An attacker who compromises the main MCU firmware can call `SE_Encrypt()` with arbitrary plaintext, using the SE as an oracle. Key protection and application isolation are separate problems.

The SE's I²C or SPI interface introduces latency. An ATECC608B AES-GCM operation takes 20–50 ms over I²C at 400 kHz. For high-throughput applications, this is prohibitive. SEs are suited for low-frequency operations (device authentication, key wrapping) not high-throughput bulk encryption.

> **Principle 28.** *A secure element protects the key from extraction; it does not protect the system from a compromised application that uses the key. Defense in depth requires both.*

---

# Part VI — Side-Channel Attacks

---

## Chapter 29 — The Side Channel: What It Is and Why It Exists

A side channel is a physical or temporal information source that leaks secret information, distinct from the algorithm's intended inputs and outputs.

The algorithm is a mathematical object — it has no power consumption, no electromagnetic emission, no timing variation. The implementation runs on hardware that does. The hardware's physical behavior correlates with computation, and computation depends on the key. The side channel is the path from key to physical observation.

```
┌─────────────────────────────────────────────────────────────┐
│                  Side Channel Model                         │
│                                                             │
│   Key K ─────────────────────────────────────────┐         │
│              ▼                                   │         │
│   Plaintext ──►[ Implementation ]──► Ciphertext  │         │
│                      │                           │         │
│                      │ Physical                  │         │
│                      │ Information               │         │
│                      ▼                           │         │
│              ┌────────────────┐                  │         │
│              │ Power Trace /  │                  │         │
│              │ EM Emission /  │                  │         │
│              │ Timing /       │◄─────────────────┘         │
│              │ Fault Response │  (correlation with K)      │
│              └────────────────┘                            │
│                      │                                     │
│                      ▼                                     │
│              Attacker extracts K                           │
└─────────────────────────────────────────────────────────────┘
```

Side channels exist because:
1. CMOS logic dissipates power proportional to switching activity.
2. Switching activity depends on the data being processed.
3. Data being processed depends on the key.

Therefore, power consumption correlates with the key. This correlation is the exploit surface.

There are four primary side channels in embedded systems:

1. **Power analysis**: measure supply current; correlate with intermediate values.
2. **Electromagnetic analysis**: measure EM field; correlate with intermediate values (finer spatial resolution than power, often attackable with a near-field probe).
3. **Timing**: measure execution time; correlate with data-dependent branches or memory accesses.
4. **Fault injection**: inject faults (voltage glitch, EM pulse, laser); observe incorrect outputs; recover key from the error differential.

Every chapter in Part VI addresses one of these.

> **Principle 29.** *Side channels attack the implementation, not the algorithm. An algorithm with 128-bit mathematical security can have 0-bit implementation security against a physical attacker with a $500 oscilloscope.*

---

## Chapter 30 — Power Analysis: SPA and DPA

**Simple Power Analysis (SPA)** extracts key information from a single power trace by directly reading it. If the implementation takes a visually distinct code path based on key bits — for example, a square-and-multiply exponentiation that does "multiply if bit=1, only square if bit=0" — the trace reveals the key directly.

For symmetric ciphers, SPA is less applicable than for public-key operations. AES rounds have uniform power traces at the operation level. However, SPA can reveal the number of rounds executed (detecting key size) and can distinguish encryption from decryption.

**Differential Power Analysis (DPA)** is the systemic side-channel attack for symmetric ciphers. It uses statistical correlation across many traces to extract the key, even when individual trace SNR is very low.

```
   DPA attack on AES SubBytes (key byte k targeting byte 0):

   For each key hypothesis k' in {0, ..., 255}:
     For each observed trace t and plaintext p:
       v = SubBytes(p[0] XOR k')
       hypothetical_power[k'][t] = HammingWeight(v)
     
     correlation[k'] = Pearson(hypothetical_power[k'], measured_power[t_target])
   
   Correct k' produces highest correlation peak
```

DPA requires hundreds to thousands of traces — trivially collectible if the attacker can trigger repeated encryptions (true for any device that encrypts data on demand, including all IoT sensor nodes).

**The DPA vulnerability exists in any software AES implementation that:**
- Uses table lookups whose access pattern correlates with intermediate values
- Does not apply masking countermeasures

Hardware AES cores are typically DPA-resistant by design (randomized execution, power balancing, masking in the fabrication) but verify this claim in your silicon vendor's datasheet. "DPA-resistant" is a certification claim, not a universal property.

> **Principle 30.** *DPA requires no mathematical access to the key — only physical access to power traces and knowledge of the algorithm. Unprotected software AES is broken by DPA with commercial-grade equipment.*

---

## Chapter 31 — Timing Attacks

A timing attack recovers secret information by measuring the time an implementation takes to complete operations. For symmetric crypto on embedded targets, two timing attacks are prevalent.

**Cache-timing attacks on software AES:** Software AES implementations that use precomputed S-box or T-box lookup tables (virtually all efficient software implementations) exhibit execution time variation based on which cache lines are loaded. On processors with data caches (ARM Cortex-M7, -M55, -A series), the first access to a cache line is slower than subsequent accesses. Since the table index depends on key XOR data, the cache miss pattern leaks the key.

```
   Cache-timing attack model:
   
   AES SubBytes access: table[state[i] XOR round_key[i]]
   Index = state[i] XOR round_key[i]
   
   Cache miss if index maps to uncached line
   Cache hit if index maps to cached line
   
   Timing difference: ~4 cycles (hit) vs ~100 cycles (miss)
   
   After N encryptions with varied plaintext:
   Statistical analysis of timing → reveals cache access pattern → reveals key
```

**Mitigation:** Use constant-time AES (bitsliced implementation, or ARM Crypto Extension instructions). Hardware AES is inherently constant-time. For software implementations without hardware assistance: bitsliced AES processes 8 blocks in parallel using only bitwise operations on integers, making all memory accesses pattern-independent.

**Timing attacks on MAC comparison:** `memcmp()` returns as soon as a difference is found. If a MAC comparison uses `memcmp()`, the time to compare two tags leaks the length of the matching prefix. An attacker who can submit forged tags and measure response time can recover the correct tag byte by byte in 256 × 16 = 4096 attempts.

Mitigation: constant-time comparison.

```c
/* Correct constant-time comparison */
int crypto_verify_16(const uint8_t *x, const uint8_t *y) {
    uint8_t d = 0;
    for (int i = 0; i < 16; i++) d |= x[i] ^ y[i];
    return (1 & ((d - 1) >> 8)) - 1; /* 0 if equal, -1 if not */
}
```

Do not implement this yourself — use the function provided by your crypto library (`mbedtls_ct_memcmp`, `sodium_memcmp`, `wc_ConstantCompare`).

> **Principle 31.** *Any data-dependent branch or memory access in the path of a secret value is a potential timing oracle. Constant-time programming eliminates data-dependent branches and memory access patterns from all secret-dependent code paths.*

---

## Chapter 32 — Fault Injection

Fault injection attacks cause the implementation to produce incorrect results by perturbing the hardware during computation. The attacker then uses the difference between the correct and faulted outputs to recover key information.

**Fault injection methods:**

| Method | Tool | Effect | Cost |
|--------|------|--------|------|
| Voltage glitch | Crowbar circuit | Skip instruction / flip bit | $100–$1000 |
| EM pulse | Near-field probe + pulse generator | Flip register bit, corrupt memory | $500–$5000 |
| Clock glitch | Clock injection via SMA | Double-clock cycle | $200–$2000 |
| Laser | Optical bench + laser | Precise bit flip in any cell | $50,000+ |

**Differential Fault Analysis (DFA) on AES:** A single bit-flip in the AES state during round 8, 9, or 10 is sufficient to recover the full AES-128 key using DFA. The attacker collects a correct ciphertext and a faulted ciphertext from the same plaintext, then uses algebraic equations over the fault difference to narrow the key space.

```
   DFA on AES (simplified):
   
   Correct: P ──►[AES_K]──► C (correct)
   Faulted: P ──►[AES_K, fault at R9]──► C' (faulted)
   
   C XOR C' leaks information about state at fault point
   One byte fault at R9 + DFA analysis → 4 key bytes recovered
   4 faults at R9 → full key recovery
```

**Countermeasures:**

*Double computation:* compute the result twice, compare. If results differ, a fault occurred. Doubles the computation cost but detects fault injection.

*Redundant encoding:* encode intermediate values with error-detecting codes (e.g., parity); check code at the end. Detects single-bit faults.

*Temporal redundancy with random delay:* randomize the timing of operations to make targeting specific rounds difficult.

*Voltage and clock monitoring:* most modern microcontrollers with security features include voltage brownout detectors and clock frequency monitors that reset the device if parameters go out of range. Enable these. Also enable the JTAG/SWD lock-out fuses.

The hardness of fault injection countermeasures scales with the attacker's equipment. A device certified to CC EAL4+ or EAL6+ has been tested against known fault injection methods. An uncertified device has unknown resistance.

> **Principle 32.** *A device without fault injection countermeasures can have its AES key recovered from a handful of faulted encryptions by a tabletop-equipped attacker. Fault countermeasures are not optional for any device facing physical adversaries.*

---

## Chapter 33 — Countermeasures: Masking, Hiding, and Redundancy

Side-channel countermeasures fall into three families. They can be combined.

**Masking (algorithmic countermeasure):** Replace all intermediate values in the computation with randomly masked equivalents. The mask is unknown to the attacker. Since the power trace depends on the masked value (which is random), correlation with the key hypothesis fails.

For AES, Boolean masking replaces every byte `v` with `v XOR m`, where `m` is a fresh random value (the mask). All operations must propagate the mask correctly. AddRoundKey and SubBytes can be masked with one random value per byte. MixColumns requires careful mask propagation to avoid mask cancellation.

Higher-order masking uses d+1 shares for d-th order DPA resistance. First-order masking defeats standard DPA; second-order masking defeats second-order DPA (requires combining two points in the trace). The cost grows with d: d+1 random masks, ~4× overhead per share.

**Hiding (architectural countermeasure):** Reduce the signal-to-noise ratio of the power trace by:
- Randomizing operation timing (insert random delays)
- Using dual-rail precharge logic (complementary logic that consumes constant power)
- Filtering the power supply (decoupling capacitors, ferrite beads)

Hiding reduces attacker SNR but does not eliminate the signal. With enough traces, averaging improves SNR and defeating hiding requires more traces. Hiding is a hardening measure, not a fix.

**Redundancy (fault countermeasure):** Detect faults by computing twice or encoding with error-detection codes.

```
┌─────────────────────────────────────────────────────────────┐
│        Countermeasure Selection Guide                       │
│                                                             │
│  Threat: SPA          → Uniform code path (no key-branches)│
│  Threat: DPA          → First-order masking                 │
│  Threat: Higher-order → Higher-order masking + hiding       │
│  Threat: Timing       → Constant-time implementation        │
│  Threat: DFA          → Redundant computation or encoding   │
│  Threat: Voltage fault→ Brown-out reset + monitoring        │
│  Threat: EM fault     → Physical shielding + detection      │
└─────────────────────────────────────────────────────────────┘
```

Countermeasures have cost. First-order AES masking typically increases code size by 3–4× and execution time by 4–8× over unprotected AES. Evaluate which countermeasures your threat model requires before implementing them — over-engineering side-channel protection is possible.

> **Principle 33.** *Masking eliminates side-channel correlation; hiding reduces it; redundancy detects faults. None is sufficient alone for a device facing a sophisticated adversary — defense requires all three layers.*

---

# Part VII — Key Management

---

## Chapter 34 — The Key Hierarchy

Key management is the part of cryptographic engineering that tutorials skip and production systems fail on. The key hierarchy is the structured organization of keys by purpose and level.

```
┌─────────────────────────────────────────────────────────────┐
│                    Key Hierarchy                            │
│                                                             │
│             ┌─────────────────────┐                         │
│             │     Root Key (RK)    │  ← In OTP/eFuse/SE     │
│             └─────────┬───────────┘  Never used directly    │
│                       │                                     │
│          ┌────────────┼────────────┐                        │
│          ▼            ▼            ▼                        │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│   │Device    │ │Firmware  │ │Provisioning│                  │
│   │Identity  │ │Update KEK│ │  KEK      │                  │
│   │Key (DIK) │ └────┬─────┘ └────┬──────┘                  │
│   └────┬─────┘      │             │                         │
│        │            ▼             ▼                         │
│        │    ┌──────────┐  ┌──────────────┐                  │
│        │    │Firmware  │  │ Session KEK  │                  │
│        │    │Sign Key  │  └──────┬───────┘                  │
│        │    └──────────┘         │                          │
│        ▼                         ▼                          │
│   ┌──────────┐           ┌──────────────┐                   │
│   │Session   │           │  Session DEK │                   │
│   │Auth Key  │           │  (ephemeral) │                   │
│   └──────────┘           └──────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

**Root Key (RK):** The trust anchor. Generated at manufacturing, stored in OTP. Never used directly to encrypt or authenticate data. Its only use is to derive or wrap lower-level keys. If the root key is compromised, the device's security is permanently broken — it cannot be rotated without hardware replacement.

**Key-Encryption Keys (KEKs):** Used only to wrap (encrypt) other keys. A firmware update KEK wraps the firmware signing key. A provisioning KEK wraps the session key establishment material. KEKs can sometimes be rotated if the protocol includes a key rotation mechanism.

**Data-Encryption Keys (DEKs):** Used to encrypt data. Derived per-session or per-connection. Should be ephemeral — discarded after use, or at a defined expiry.

**The hierarchy must be documented.** For each key: its name, its level in the hierarchy, its derivation path, its algorithm and size, its storage location, its lifetime, and its destruction procedure. A system without this document is not a secure system — it is an unknown one.

> **Principle 34.** *The key hierarchy is not an implementation detail; it is a security architecture document that must exist before any key is generated.*

---

## Chapter 35 — Key Derivation Functions

A KDF takes a high-entropy secret (key material, shared secret, master key) and produces one or more derived keys with defined properties. The derived keys are cryptographically independent — knowing one derived key reveals nothing about other derived keys from the same master.

**HKDF** (RFC 5869): the standard two-step KDF.

```
   Step 1 — Extract:
   PRK = HMAC-SHA256(salt, IKM)
   IKM: input key material (e.g., shared secret from DH)
   salt: optional random value; defaults to 32 zero bytes
   PRK: pseudorandom key (32 bytes)
   
   Step 2 — Expand:
   OKM = HKDF-Expand(PRK, info, L)
   info: context string (e.g., "device-id=0xABCD,purpose=firmware-key")
   L: length of output key material in bytes
   OKM: output key material
```

HKDF is correct for deriving session keys from a shared secret (e.g., Diffie-Hellman output). It is not a password-based KDF — do not use it to derive keys from passwords.

**NIST SP 800-108 Counter KDF:** A simpler KDF for deriving multiple keys from a master key that is already uniformly random (e.g., a root key stored in OTP).

```
   K_derived = CMAC(K_master, counter || label || 0x00 || context || L)
   
   counter: 4-byte big-endian counter (starts at 0x00000001)
   label: UTF-8 string identifying the derived key purpose
   L: 4-byte length of output in bits
```

SP 800-108 Counter KDF is the right choice for deriving device-specific keys from a root key on embedded targets. It requires only AES-CMAC, which is hardware-accelerated.

**Key separation via KDF:** Never use the same key for two different purposes. Use the KDF's `info` or `label` parameter to derive purpose-specific keys:

```
   K_encrypt = KDF(K_master, "AES-GCM-Encrypt-Channel-1")
   K_auth    = KDF(K_master, "CMAC-Auth-Channel-1")
```

This ensures that a key compromise in one domain does not affect the other.

> **Principle 35.** *Always use a KDF to derive purpose-specific keys from master key material; never use a master key directly for encryption or authentication.*

---

## Chapter 36 — Key Storage on Constrained Devices

Keys in RAM are lost at power-off. Keys in flash survive power cycles. The question is where to store long-lived keys and how to protect them.

**Storage options, ranked by protection level:**

```
┌─────────────────────────────────────────────────────────────┐
│            Key Storage Hierarchy (Weakest → Strongest)      │
│                                                             │
│  ┌─────────────────────────────────────────┐               │
│  │ Plain Flash / EEPROM                     │  ← Readable by│
│  │ Key stored in cleartext in flash pages   │    any code   │
│  └─────────────────────────────────────────┘               │
│                      │ better                               │
│  ┌─────────────────────────────────────────┐               │
│  │ Flash + Read-out protection (ROP)        │  ← JTAG read  │
│  │ RDP level 2 (STM32) or equivalent        │    disabled   │
│  └─────────────────────────────────────────┘               │
│                      │ better                               │
│  ┌─────────────────────────────────────────┐               │
│  │ Flash + AES key wrapping                 │  ← Key in     │
│  │ Key encrypted under a KEK in secure mem │    cleartext  │
│  └─────────────────────────────────────────┘    only in RAM│
│                      │ better                               │
│  ┌─────────────────────────────────────────┐               │
│  │ Hardware key storage (OTP eFuse)         │  ← CPU cannot │
│  │ Key accessible only to crypto engine     │    read key   │
│  └─────────────────────────────────────────┘               │
│                      │ best                                 │
│  ┌─────────────────────────────────────────┐               │
│  │ External Secure Element                  │  ← Key never  │
│  │ Key never leaves SE                      │    on bus     │
│  └─────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

**OTP/eFuse key storage:** Most ARM Cortex-M33/M55 based devices (STM32H5, STM32U5, NXP LPC55S69, Nordic nRF5340) include hardware key slots that can be written once at provisioning and are thereafter accessible only to the hardware crypto engine, not to CPU instruction fetch/load. The CPU cannot read the key bytes; it can only call `AES_K()` where K is implicitly the stored key.

This is the target key storage model for any device facing physical adversaries. The implementation detail is device-specific — read your SoC's security reference manual for the "hardware key slot" or "SAES" (secure AES) peripheral documentation.

**Key zeroization:** keys stored in RAM must be explicitly zeroized after use. The C compiler may optimize away `memset(key, 0, sizeof(key))` if the key buffer is not used after the memset. Use `memset_s()` (C11), `SecureZeroMemory()` (Windows), or a volatile write loop:

```c
void secure_zero(void *ptr, size_t len) {
    volatile uint8_t *p = (volatile uint8_t *)ptr;
    while (len--) *p++ = 0;
}
```

Failure to zeroize keys leaves them in RAM and potentially in flash (if the stack frame is written to flash for debugging) until overwritten by subsequent allocation.

> **Principle 36.** *A key stored in accessible memory is accessible. Use hardware key storage that prevents CPU read-out for any key that must survive physical adversary access.*

---

## Chapter 37 — Key Provisioning at Manufacturing

Key provisioning is the process of loading cryptographic secrets into devices during manufacturing. It is one of the highest-risk operations in the embedded product lifecycle — a manufacturing compromise yields all device keys.

```
┌─────────────────────────────────────────────────────────────┐
│              Provisioning Architectures                     │
│                                                             │
│  Option A: Pre-loaded by chip manufacturer                  │
│  ┌────────────┐          ┌──────────────────────┐          │
│  │ Chip Vendor│──OTP────►│ Device (on shelf)     │          │
│  └────────────┘  Write   └──────────────────────┘          │
│  Risk: chip vendor has your keys                            │
│                                                             │
│  Option B: Custom provisioning station                      │
│  ┌────────────┐  Secure  ┌────────────┐  Provision         │
│  │  HSM / PKI │─────────►│ Prog.      │──────────►         │
│  │  at OEM    │  Channel │ Station    │  Device             │
│  └────────────┘          └────────────┘                     │
│  Risk: programming station security                         │
│                                                             │
│  Option C: Device-generated, certificate-enrolled           │
│  ┌──────────┐  Self-gen  ┌──────────────────────────┐      │
│  │  Device  │──────────► │ Device sends CSR to cloud │      │
│  │  TRNG    │  key pair  │ CA signs; cert returned   │      │
│  └──────────┘            └──────────────────────────┘      │
│  Risk: TRNG quality during provisioning                     │
└─────────────────────────────────────────────────────────────┘
```

**The security of provisioning determines the security floor of the fleet.** If the provisioning station is compromised, all devices provisioned through it are compromised. Treat the provisioning station as a high-security HSM environment.

**Best practices for symmetric key provisioning:**

1. Generate keys in an HSM; never in the provisioning station's main processor.
2. Transport keys to the device via an encrypted and authenticated channel (often using an ephemeral DH handshake between HSM and device's TrustZone or SE).
3. The device's TRNG generates a device-unique key pair or shared secret that is enrolled with the backend HSM.
4. Log every provisioning event with the device's serial number, the key identifier, and a timestamp.
5. Destroy provisioning records (cleartext keys) from HSM volatile memory immediately after provisioning.

Option C (device-generated keys) is preferred when feasible because the key never exists outside the device. It requires the device's TRNG to be trustworthy before manufacturing is complete — this is why TRNG health testing at manufacturing test (ATE) is essential.

> **Principle 37.** *Key provisioning is the highest-risk operation in the device lifecycle; its security determines the lower bound of the fleet's security posture.*

---

## Chapter 38 — Key Rotation and Revocation

Keys must change. Rotation is the planned replacement of a key with a new one. Revocation is the emergency invalidation of a compromised key.

**Why rotation is difficult on embedded devices:**

- Devices may be offline for extended periods (field sensors, remote installations)
- Devices have no clock or cannot verify timestamps (making replay attacks on rotation messages possible)
- Flash write cycles are limited; frequent key updates wear flash
- A failed rotation (device reboots during write) may leave the device with an inconsistent key state

**Rotation protocol for embedded devices:**

```
   Rotation message (sent over authenticated channel):
   { new_key_encrypted: AES-GCM(K_session, new_key),
     key_id: new_key_identifier,
     sequence_number: monotonic counter,
     not_before: timestamp (optional if clock available) }
   
   Device:
   1. Verify AEAD tag on rotation message (using current session key)
   2. Verify sequence_number > last_accepted_sequence (replay protection)
   3. Decrypt new_key
   4. Write new_key to NVM atomically (two-phase commit or journaling)
   5. Transition to new key
   6. Acknowledge rotation (signed with new key)
```

**Two-phase commit for NVM key update:** Write the new key to a staging slot, then atomically update the "active key pointer" (a single NVM word or flag). If power is lost, the pointer still points to the old key. After confirming the pointer, erase the old slot. This pattern prevents key loss from power interruption during rotation.

**Revocation on constrained devices:** Full certificate revocation lists (CRL) or OCSP are impractical on embedded targets. Two embedded-practical approaches:

*Epoch counter in NVM:* each key has an epoch. A centrally managed epoch counter is broadcast to all devices. Devices reject any message signed under an epoch lower than their stored epoch.

*Key blacklist in flash:* store a list of revoked key identifiers in flash. Check incoming keys against the blacklist. Feasible for small fleets; impractical at millions of devices.

> **Principle 38.** *Key rotation must be atomic from the device's perspective; a power interruption during rotation must leave the device with a valid, operable key — either the old one or the new one, never neither.*

---

# Part VIII — Protocols and Composition

---

## Chapter 39 — The Universal Secure Channel Pattern

Every secure communications protocol, regardless of domain or layer, is an instance of one universal pattern. Memorize it.

```
┌─────────────────────────────────────────────────────────────┐
│              Universal Secure Channel                       │
│                                                             │
│  Phase 1: HANDSHAKE                                         │
│  ─────────────────────────────────────────────────────────  │
│  Parties establish shared secret → derive session keys      │
│  (Asymmetric key exchange or pre-shared key)                │
│                                                             │
│  Phase 2: RECORD PROTOCOL                                   │
│  ─────────────────────────────────────────────────────────  │
│  Each message:                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Header (sequence number, length, type) │ Ciphertext  │  │
│  │    ↑ authenticated as Associated Data  │    + Tag    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Rules:                                                     │
│  • Sequence number is monotonic, verified at receiver       │
│  • AEAD key + nonce derived from sequence or explicit nonce │
│  • Decryption verifies tag before releasing plaintext       │
│  • Tag failure → discard record, signal error               │
│                                                             │
│  Phase 3: CLOSURE                                           │
│  ─────────────────────────────────────────────────────────  │
│  Authenticated close message; session keys destroyed        │
└─────────────────────────────────────────────────────────────┘
```

TLS 1.3 is the reference implementation. DTLS 1.3 is the datagram variant. OSCORE is a COAP-layer variant for constrained nodes. All share this structure.

The session key derivation (Phase 1) uses HKDF. The record protocol (Phase 2) uses AEAD. The sequence number serves as the nonce component. Closing the channel (Phase 3) destroys the session keys.

Every deviation from this pattern is a potential vulnerability. Protocols that skip the handshake (using only pre-shared keys without deriving session keys) lose forward secrecy. Protocols that skip sequence numbers allow replay. Protocols that do not authenticate closure allow truncation attacks.

> **Principle 39.** *Every secure channel protocol is a handshake plus an AEAD record protocol; every deviation from this pattern trades a security property for a resource constraint, and the tradeoff must be explicit.*

---

## Chapter 40 — Secure Boot: The Cryptographic Chain of Trust

Secure boot uses cryptographic authentication to ensure that each piece of firmware loaded during the boot sequence is authorized by the device manufacturer.

```
┌─────────────────────────────────────────────────────────────┐
│              Chain of Trust in Secure Boot                  │
│                                                             │
│  ┌─────────────────┐                                        │
│  │  ROM Boot Code  │  ← Immutable; root of trust           │
│  │  (in ROM)       │    Verifies Stage-1 signature          │
│  └────────┬────────┘                                        │
│           │ verify(Stage1, Sig_Stage1, PK_root)             │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │  Bootloader     │  ← Stage 1; in flash                   │
│  │  (Stage 1)      │    Verifies application firmware       │
│  └────────┬────────┘                                        │
│           │ verify(AppFW, Sig_App, PK_fw_update)            │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │  Application    │  ← Authenticated before execution      │
│  │  Firmware       │                                        │
│  └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
```

Secure boot is typically asymmetric — the signature verification key (public key) is stored in OTP, and firmware images are signed with the corresponding private key held by the firmware build HSM. Asymmetric signatures are used here (not MACs) because the build system holds the signing key; the device holds only the verification key.

**Symmetric secure boot** is possible (the device stores a shared HMAC key for firmware authentication) but uncommon because it requires the build system to share a secret with each device — harder to manage at scale.

**The connection to symmetric crypto:** within a secure boot implementation, symmetric crypto appears in:
- HMAC or CMAC for firmware integrity checks in the bootloader (faster than RSA for large firmware images)
- AES decryption of encrypted firmware images (intellectual property protection)
- Derived keys for secure storage encryption (protecting runtime secrets that survive the boot)

The root of trust is always hardware — typically OTP fuses holding the public key hash or a symmetric root key. Software cannot establish trust in software; the chain must start in hardware.

> **Principle 40.** *The chain of trust in secure boot must have a hardware root; any break in the chain — a stage that executes without verification — voids the security of all subsequent stages.*

---

## Chapter 41 — Firmware Update Security

Over-the-air (OTA) firmware updates are a critical attack surface. A vulnerability in the update mechanism allows an attacker to install arbitrary firmware, bypassing all other security.

```
┌─────────────────────────────────────────────────────────────┐
│              Firmware Update Security Requirements          │
│                                                             │
│  1. AUTHENTICITY                                            │
│     Firmware must be signed by the vendor.                  │
│     Device verifies signature before installation.          │
│     Signature: RSA-PSS-4096 or ECDSA-P-256 (asymmetric)    │
│                                                             │
│  2. INTEGRITY                                               │
│     Firmware must not be modified after signing.            │
│     Verified by signature over full firmware image.         │
│                                                             │
│  3. ANTI-ROLLBACK                                           │
│     Device refuses to install older firmware versions.      │
│     Monotonic version counter in OTP or RPMB.               │
│                                                             │
│  4. CONFIDENTIALITY (optional)                              │
│     Encrypt firmware image to protect IP.                   │
│     AES-GCM with device-specific key.                       │
│     Encrypt AFTER sign, not before.                         │
│                                                             │
│  5. ATOMIC INSTALLATION                                     │
│     Power loss during update must leave device bootable.    │
│     A/B partition scheme or staged update.                  │
└─────────────────────────────────────────────────────────────┘
```

**Sign-then-Encrypt for firmware:** If confidentiality is required, the firmware image is signed (covering the plaintext), then encrypted. On the device, the image is first decrypted, then the signature is verified over the plaintext. This order ensures that the device verifies an authentic image before installing it — not a potentially malicious ciphertext.

Encrypt-then-Sign (signing the ciphertext) is acceptable only if the signature covers the full ciphertext and the device verifies before decrypting. Either order is cryptographically valid if done carefully; the canonical advice is to follow the MCUBOOT or SUIT manifest standards rather than designing the order yourself.

**SUIT manifest** (RFC 9124): the IETF standard for IoT firmware update. Defines a CBOR-encoded manifest structure covering firmware metadata, version, signature, and update condition. Implementations exist for MCUBoot (Zephyr RTOS) and OpenThread.

> **Principle 41.** *An unauthenticated firmware update mechanism is an unauthenticated remote code execution vulnerability. Treat the update path as the highest-privilege attack surface in the product.*

---

## Chapter 42 — Record Protocols: TLS 1.3 as the Reference

TLS 1.3 (RFC 8446) is the reference implementation of the universal secure channel pattern. Even when you do not deploy TLS directly on an embedded device, understanding its record layer informs every custom protocol design.

**TLS 1.3 key schedule:**

```
   0 ──► HKDF-Extract(salt=0, IKM=0) ──► Early Secret
          │
          ▼ Derive early traffic keys if 0-RTT
          
   Early Secret + DHE ──► HKDF-Extract ──► Handshake Secret
          │
          ▼ Derive: client_handshake_traffic_secret
          ▼         server_handshake_traffic_secret
          
   Handshake Secret ──► HKDF-Extract(IKM=0) ──► Master Secret
          │
          ▼ Derive: client_application_traffic_secret
          ▼         server_application_traffic_secret
          ▼         exporter_master_secret
```

Each traffic secret derives a key and IV for AES-GCM or ChaCha20-Poly1305. The nonce for each record is the IV XOR'd with the sequence number (padded to 12 bytes). This provides unique nonces without transmitting them.

**TLS 1.3 record encryption:**

```c
   /* Nonce construction */
   nonce = traffic_iv XOR (sequence_number as 12-byte big-endian)
   
   /* Additional data = record header */
   ad = { content_type || protocol_version || length }
   
   /* Encrypt */
   (ciphertext, tag) = AEAD_Encrypt(key, nonce, ad, plaintext || content_type)
```

The content type byte is appended to the plaintext and encrypted, hiding the record type from passive observers. The record header is associated data — authenticated but visible.

For embedded devices that cannot run full TLS 1.3, the record protocol pattern is the part to preserve. The key schedule can be simplified (pre-shared key, no DHE), but the AEAD record structure with sequence-number-based nonce is the minimum for a secure channel.

> **Principle 42.** *TLS 1.3's record protocol is the correct template for any authenticated encrypted channel; its sequence-number nonce construction eliminates the nonce management problem entirely.*

---

## Chapter 43 — Lightweight Protocols: DTLS, OSCORE, and EDHOC

For constrained embedded devices that cannot run TLS, three lightweight protocol families cover most use cases.

**DTLS 1.3** (RFC 9147): TLS 1.3 over UDP. Adds record reordering, replay detection, and retransmission to handle datagram unreliability. The symmetric crypto is identical to TLS 1.3 (AES-GCM-128 or ChaCha20-Poly1305). Overhead per record: 13 bytes header + 16 bytes tag minimum. Suitable for devices with 64 KB+ RAM.

**OSCORE** (RFC 8613): Object Security for Constrained RESTful Environments. Encrypts CoAP messages at the application layer using COSE (RFC 9052). Uses AES-CCM-16-64 (64-bit tag) or AES-CCM-16-128 (128-bit tag). Designed for devices with 10–30 KB RAM.

```
   OSCORE message structure:
   ┌─────────────────────────────────────────────────┐
   │  CoAP Header │ OSCORE Option │ Encrypted Payload │
   │  (cleartext) │  (partial IV) │ (COSE_Encrypt0)  │
   └─────────────────────────────────────────────────┘
   
   Encrypted payload: AEAD_Encrypt(key, nonce=IV||partial_IV, ad=request_data, plaintext=CoAP_payload)
```

**EDHOC** (RFC 9528): Ephemeral Diffie-Hellman Over COSE. A lightweight authenticated key exchange protocol producing OSCORE keys. Requires 2–3 round trips. Symmetric key establishment from ephemeral DH takes 80–300 bytes of RAM at peak and produces forward-secret session keys. EDHOC replaces the TLS 1.3 handshake for constrained environments.

**Protocol selection guide:**

| Protocol | RAM | Flash | Overhead/msg | Forward Secrecy |
|----------|-----|-------|-------------|-----------------|
| TLS 1.3 | 64+ KB | 100+ KB | ~50 bytes | Yes (DHE) |
| DTLS 1.3 | 64+ KB | 100+ KB | ~30 bytes | Yes (DHE) |
| OSCORE | 10–30 KB | 30–60 KB | ~20 bytes | With EDHOC |
| Custom AEAD | < 10 KB | < 20 KB | ~16 bytes | No (PSK only) |

The custom AEAD option — a bare AEAD record protocol with pre-shared keys — is the floor. It provides authenticated encryption but no forward secrecy, no key agreement, and no identity verification beyond the pre-shared key. It is appropriate only for closed networks with controlled key provisioning.

> **Principle 43.** *Protocol selection is a resource tradeoff, not a security tradeoff — the minimal viable protocol is one that provides AEAD + replay protection + nonce uniqueness, regardless of label.*

---

# Part IX — Production Realities

---

## Chapter 44 — What Changes at Scale

A cryptographic design that works in the lab changes character at production scale. Here are the specific changes and their mitigations.

**Key uniqueness breaks.** At scale, manufacturing defects, provisioning failures, and operator error produce devices with duplicate keys. Even a 0.01% duplication rate in a 10-million-device fleet means 1,000 key collisions. Audit provisioning logs. Generate device-unique keys in the device itself where possible. Test for uniqueness at the fleet level.

**TRNG failures cluster.** A manufacturing defect in a specific fabrication lot may produce consistently weak TRNGs across thousands of devices. The devices pass TRNG health tests (if the bias is subtle), generate predictably correlated keys, and are all vulnerable. Include device serial numbers and manufacturing timestamps in the TRNG seed to break inter-device correlation. Monitor key distinctiveness at enrollment.

**Nonce exhaustion becomes real.** A device using a 32-bit counter for AES-GCM nonces (as some embedded BLE stacks do) will wrap in 2^32 ≈ 4 billion messages. At 1 message/second, this is 136 years. At 1000 messages/second (high-throughput sensor), this is 49 days. Know your message rate. Use 64-bit or 96-bit nonces. Build nonce exhaustion detection into the firmware.

**Firmware update infrastructure fails.** At scale, OTA update delivery fails for a non-trivial percentage of devices — due to network interruptions, power failure during update, flash wear errors, or version mismatch. Build update retry, rollback, and health-check into the update protocol. A brick-proof update is harder to design than the update itself.

**Side-channel attacks become economically viable.** At 1 device, DPA equipment is expensive relative to what an attacker gains. At 1 million devices, the amortized cost of DPA equipment against any representative device is trivial. Design with DPA resistance at volume; defer it only for truly low-value targets.

> **Principle 44.** *Every security property that holds at one device may fail at one million; audit each property — key uniqueness, nonce uniqueness, TRNG quality, update success rate — at the fleet level.*

---

## Chapter 45 — Entropy Starvation at Boot

Embedded devices face entropy starvation immediately after power-on: the TRNG has not yet accumulated entropy, persistent state has not yet been loaded, and the first cryptographic operations (key generation, nonce selection) must occur anyway.

This is the Linux `/dev/urandom` at boot problem, in more severe form. Linux can block on `/dev/random` and fall back to the kernel's entropy pool seeded from hardware events. Embedded devices often have none of these resources.

**The boot entropy problem:**

```
   Power-on:
   t=0ms: CPU running, TRNG not ready (health test not passed)
   t=10ms: TRNG passes health test, provides first random bytes
   t=15ms: NVM read of persisted nonce counter completes
   t=20ms: First AES-GCM encryption possible with valid nonce
   
   Between t=0 and t=20ms: what happens if crypto is needed?
```

**Mitigations:**

*Delay crypto until entropy is available:* accept that the device takes 20–50 ms to be cryptographically ready. This is acceptable for most applications; boot time is not latency-critical.

*Pre-commit entropy in NVM:* at shutdown, write random bytes from the TRNG to NVM. On next boot, seed the DRBG from NVM before the TRNG is ready. Vulnerable to replay (NVM may not be updated on unexpected power loss), but provides early entropy. Use a monotonic counter alongside the NVM entropy seed to detect replay.

*TrustZone early boot entropy:* on TrustZone-capable devices, the secure world can run the TRNG health test in parallel with normal world initialization, providing entropy to the normal world promptly.

*Hardware support:* some SoCs (STM32H5 series) include a boot entropy register that is populated by ROM code before application execution, guaranteeing a minimum entropy level at application start.

> **Principle 45.** *Never generate a key or nonce before the TRNG health test has passed. Entropy starvation at boot is a production vulnerability, not a theoretical concern.*

---

## Chapter 46 — Nonce Misuse and Its Consequences

Nonce misuse is the production failure mode for AES-GCM. It occurs in embedded systems through three failure patterns.

**Failure 1: Counter not persisted across power cycles.** The nonce counter is stored in RAM. A power cycle resets it to zero. The device resumes transmitting with nonce=0, repeating nonces used in the previous session under the same key. Mitigation: persist the counter in NVM, increment before each use, use a write-ahead log to handle partial writes.

**Failure 2: Multi-core counter race.** A dual-core device (Cortex-M33 + M4, or TrustZone normal+secure) uses a shared counter without synchronization. Two cores may use the same nonce value. Mitigation: use atomic compare-and-swap operations or assign non-overlapping counter ranges to each core.

**Failure 3: Key-reuse after re-provisioning.** A device is re-provisioned with the same key (factory reset, provisioning error). It then reuses nonces that were used under the same key before re-provisioning. The ciphertexts from before and after re-provisioning can be collected and compared. Mitigation: generate a fresh key at every provisioning event; never re-provision the same key.

**AES-SIV as nonce-misuse mitigation:** AES-SIV (RFC 5297) is misuse-resistant: nonce repetition reveals only whether two plaintexts are identical, not the plaintext itself. The tradeoff: SIV requires a synthetic IV pass before encryption (two-pass), and the output ciphertext is slightly longer (16-byte overhead for the SIV). Use SIV for key wrapping, for initialization before a counter is established, or for any context where nonce uniqueness cannot be guaranteed.

> **Principle 46.** *A nonce counter that is not persisted in non-volatile memory before use is a nonce counter that will repeat across power cycles. All session state requires explicit boot-time restoration.*

---

## Chapter 47 — Cryptographic Agility: Asset or Liability

Cryptographic agility means the ability to switch algorithms without firmware update — configuring which cipher, which mode, which key size at runtime. It sounds like a feature. In embedded systems, it is frequently a liability.

**The case against agility:**

Agility introduces negotiation, and negotiation introduces downgrade attacks. If a device supports both AES-128-GCM and DES (hypothetically), an active attacker can force negotiation to DES. Real examples of this include RC4 downgrade in TLS 1.2 and the EXPORT cipher downgrade in FREAK.

Agility introduces parsing complexity. Algorithm identifiers must be parsed and validated. Incorrect validation allows injection of unexpected algorithms. Minimal embedded parsers are better than flexible ones.

Agility violates the principle that the threat model should determine the algorithm selection. If the threat model is determined at design time (it should be), the algorithm is determined at design time. Agility is for systems whose threat model is unknown at design time — which is a design failure.

**The case for agility:**

Algorithms do get broken. SHA-1 was deprecated. MD5 was deprecated. A device deployed for 20 years will outlast the security assumptions of some algorithms it uses today. Agility allows algorithm replacement without hardware re-deployment.

The resolution: plan for algorithm replacement, but do not implement runtime negotiation. Instead, implement a firmware-update path for algorithm changes, controlled by a signed manifest. The algorithm is fixed per firmware version; the update mechanism provides agility.

For protocol interoperability (TLS with a server, Bluetooth LE), implement only the current recommended cipher suite. Reject deprecated suite offers at the protocol level.

> **Principle 47.** *Cryptographic agility at runtime enables downgrade attacks; plan algorithm replacement via firmware update with signed manifests, not via runtime negotiation.*

---

## Chapter 48 — Compliance: FIPS 140-3, Common Criteria, and PSA Certified

If your device is sold into government, healthcare, financial, or infrastructure markets, compliance certification may be required. The three relevant frameworks for embedded symmetric crypto are FIPS 140-3, Common Criteria, and PSA Certified.

**FIPS 140-3** (NIST): validates that a cryptographic module implements approved algorithms correctly, with appropriate key protection and self-tests. The standard has four security levels; Level 2 requires role-based authentication; Level 3 requires tamper evidence. The relevant NIST publications:

- NIST SP 800-38A/B/C/D: modes of operation
- NIST SP 800-90A/B: RNG standards
- FIPS 197: AES
- FIPS 198: HMAC
- NIST SP 800-108: KDF

FIPS 140-3 validation is expensive (~$50,000–$200,000) and slow (12–24 months). Use FIPS-validated software modules (e.g., Mbed TLS FIPS module, WolfSSL FIPS module) rather than obtaining your own validation when possible.

**Common Criteria (CC):** ISO/IEC 15408. Evaluates security properties of a complete product against a Protection Profile (PP). The relevant PP for embedded devices is the IoT Security Evaluation (SESIP). CC EAL4+ is the typical target for industrial and automotive markets.

**PSA Certified** (Arm): a tiered certification for IoT devices based on the PSA security model. Level 1 is a questionnaire; Level 2 requires an independent security lab evaluation; Level 3 is equivalent to CC EAL4+ for hardware. PSA Certified requires PSA RoT (Root of Trust) implementation, which maps directly to secure boot, secure storage, and key isolation requirements.

If certification is in scope, engage the certification body early. Certification requirements constrain implementation choices — algorithm selection, key storage, TRNG architecture — and retrofitting them is expensive.

> **Principle 48.** *Compliance certifications constrain algorithm and architecture choices; determine compliance requirements before architecture is finalized, not after.*

---

# Part X — Tooling and Workflow

---

## Chapter 49 — Library Selection for Embedded Targets

The choice of crypto library is an architectural decision. It determines algorithm availability, hardware acceleration support, code size, compliance posture, and maintenance burden.

```
┌─────────────────────────────────────────────────────────────┐
│           Embedded Crypto Library Comparison                │
│                                                             │
│  Library      │ Size(ROM) │ RAM   │ HW Accel │ FIPS │ License│
│  ─────────────┼───────────┼───────┼──────────┼──────┼───────│
│  Mbed TLS 3.x │ 40–80 KB  │ 8–16K │ Yes      │ Opt. │ Apache│
│  WolfSSL      │ 20–100 KB │ 5–16K │ Yes      │ Yes  │ GPL/Comm│
│  TinyCrypt    │ 6–12 KB   │ 1–4K  │ No       │ No   │ Apache│
│  LibSodium    │ 100+ KB   │ 20K+  │ Limited  │ No   │ ISC   │
│  RIOT Crypto  │ 10–30 KB  │ 2–8K  │ Partial  │ No   │ LGPL  │
└─────────────────────────────────────────────────────────────┘
```

**Mbed TLS 3.x** (now maintained by the PSA API consortium, formerly ARM): the most widely deployed embedded crypto library. It has a modular build system (include only what you need), hardware acceleration integration via PSA Crypto API, and an optional FIPS-validated build. It is the right default for Cortex-M targets integrated with Zephyr, FreeRTOS, or bare-metal applications.

**WolfSSL** has a smaller ROM footprint than Mbed TLS for minimal configurations. Its FIPS-validated module is available commercially. Supports a wide range of algorithms including post-quantum. The commercial license is required for proprietary applications.

**TinyCrypt** (Intel): designed for 8–32 KB ROM constrained devices. Implements only AES-CCM, AES-CBC, HMAC-SHA256, and ECDH-P256. No hardware acceleration abstraction. Not maintained for post-2020 algorithms. Use for Class 0 (8-bit MCU) targets or as a reference implementation.

The selection algorithm:

1. If PSA Crypto API is required (PSA Certified, Zephyr RTOS): use Mbed TLS.
2. If FIPS 140-3 validation is required: use WolfSSL FIPS or Mbed TLS FIPS.
3. If ROM < 20 KB is a hard constraint: use TinyCrypt or custom.
4. Otherwise: use Mbed TLS.

> **Principle 49.** *Use an established, actively-maintained crypto library; do not implement cryptographic primitives yourself unless you are equipped to validate them against NIST test vectors across all edge cases and are prepared to patch them for the product's lifetime.*

---

## Chapter 50 — Mbedtls in Practice

Mbed TLS (hereafter "Mbed TLS") provides two API layers: the legacy low-level API and the PSA Crypto API. For new designs, use the PSA API.

**PSA Crypto API initialization:**

```c
#include "psa/crypto.h"

/* Always call first */
psa_status_t status = psa_crypto_init();
if (status != PSA_SUCCESS) { /* handle error */ }
```

**AES-GCM encryption via PSA:**

```c
psa_key_id_t key_id;
psa_key_attributes_t attrs = PSA_KEY_ATTRIBUTES_INIT;

/* Define key: AES-128, volatile, GCM capable */
psa_set_key_type(&attrs, PSA_KEY_TYPE_AES);
psa_set_key_bits(&attrs, 128);
psa_set_key_usage_flags(&attrs, PSA_KEY_USAGE_ENCRYPT | PSA_KEY_USAGE_DECRYPT);
psa_set_key_algorithm(&attrs, PSA_ALG_GCM);

/* Import key material */
psa_import_key(&attrs, key_bytes, 16, &key_id);

/* Encrypt */
uint8_t output[plaintext_len + 16]; /* + 16 for tag */
size_t output_len;
psa_aead_encrypt(
    key_id,
    PSA_ALG_GCM,
    nonce, 12,          /* nonce, nonce_length */
    ad, ad_len,         /* additional data */
    plaintext, plaintext_len,
    output, sizeof(output), &output_len
);

/* Decrypt */
psa_aead_decrypt(
    key_id,
    PSA_ALG_GCM,
    nonce, 12,
    ad, ad_len,
    ciphertext, ciphertext_len,
    plaintext_out, sizeof(plaintext_out), &plaintext_len
);
/* Returns PSA_ERROR_INVALID_SIGNATURE if tag verification fails */

/* Destroy key when done */
psa_destroy_key(key_id);
```

**Hardware acceleration:** Mbed TLS activates hardware acceleration transparently via the PSA driver API. Drivers are registered per-algorithm per-platform. The STM32 HAL provides an Mbed TLS PSA driver for AES-GCM, SHA-256, and TRNG. To activate: set `MBEDTLS_PSA_CRYPTO_DRIVERS` in the config and link the vendor driver.

**TRNG integration:**

```c
/* Mbed TLS requires an entropy source. Register the hardware TRNG: */
mbedtls_entropy_context entropy;
mbedtls_entropy_init(&entropy);
mbedtls_entropy_add_source(&entropy, your_hw_trng_poll_function,
                            NULL, 32, MBEDTLS_ENTROPY_SOURCE_STRONG);
```

Always provide a strong entropy source. Using `MBEDTLS_NO_PLATFORM_ENTROPY` and relying on a weak seed is the most common Mbed TLS misconfiguration in embedded deployments.

> **Principle 50.** *The PSA Crypto API decouples algorithm selection from implementation; it is the portable interface for embedded crypto that survives library replacement and hardware changes.*

---

## Chapter 51 — WolfSSL and TinyCrypt

**WolfSSL** is positioned for: FIPS-validated deployments, automotive targets (AUTOSAR integration), and very small ROM budgets (20 KB minimal AES-only build).

Critical configuration flags for embedded:

```c
/* wolfSSL configuration for minimal AES-GCM-only embedded target */
#define WOLFSSL_USER_SETTINGS
#define NO_RSA
#define NO_DSA
#define NO_DH
#define NO_ECC         /* Remove if ECC needed */
#define NO_OLD_TLS
#define HAVE_AESGCM
#define HAVE_CHACHA
#define HAVE_POLY1305
#define WOLFSSL_SHA256
#define NO_SESSION_CACHE
#define SINGLE_THREADED
#define STM32_CRYPTO   /* Enable STM32 hardware acceleration */
```

Typical WolfSSL AES-GCM-only build: 22–28 KB ROM, 4–6 KB peak RAM.

**TinyCrypt** is a reference point, not a production recommendation for new designs. Its value is in its small size (6 KB for AES-CCM only) and readable code, which makes it useful for embedded crypto educational purposes and Class 0 MCU targets.

TinyCrypt's AES-CCM API:

```c
#include <tinycrypt/aes.h>
#include <tinycrypt/ccm_mode.h>

struct tc_aes_key_sched_struct key_sched;
tc_aes128_set_encrypt_key(&key_sched, key);

struct tc_ccm_mode_struct ccm;
tc_ccm_config(&ccm, &key_sched, nonce, nonce_len, tag_len);

tc_ccm_generation_encryption(ciphertext, tag, ad, ad_len,
                              plaintext, plaintext_len, &ccm);
```

Note TinyCrypt's limitation: its AES implementation is unprotected against cache-timing attacks. Deploy only on devices without data caches (bare Cortex-M0/M0+) or with hardware AES.

> **Principle 51.** *Library size optimization is a code size problem, not a security problem; never remove algorithm implementations to save space at the cost of using weaker algorithms.*

---

## Chapter 52 — Test Vectors and CAVP Testing

Test vectors are the ground truth for cryptographic implementation validation. If your implementation does not produce the same output as the NIST test vectors for every test case, your implementation is wrong.

**Where to find test vectors:**

- NIST CAVP (Cryptographic Algorithm Validation Program): https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program
- NIST AES test vectors: FIPS 197 Appendix B; CAVP AES test vectors in Known Answer Test (KAT) format
- NIST AES-GCM test vectors: SP 800-38D test vectors package
- RFC 7539 ChaCha20-Poly1305 test vectors
- RFC 5869 HKDF test vectors

**The CAVP KAT format:**

```
# AES-GCM encrypt KAT example:
[Keylen = 128]
[IVlen = 96]
[PTlen = 128]
[AADlen = 128]
[Taglen = 128]

Count = 0
Key = feffe9928665731c6d6a8f9467308308
IV  = cafebabefacedbaddecaf888
PT  = d9313225f88406e5a55909c5aff5269a
AAD = feedfacedeadbeeffeedfacedeadbeef
CT  = 42831ec2217774244b7221b784d0d49c
Tag = e58ec82b5b44e9dfb5b800c0b49e8bf2
```

**Testing protocol:**

1. Run all applicable CAVP KAT test vectors against your implementation (encrypt and decrypt directions).
2. Run Multi-block message tests (MCT) if your library includes them.
3. Run boundary tests: zero-length plaintext, zero-length AD, maximum plaintext length.
4. Run negative tests: corrupted tag (must return error without plaintext), corrupted ciphertext (must return error), truncated input.
5. Run nonce-related tests: nonce values 0x00...00, 0xFF...FF, and random samples.

Automate these in your CI pipeline. A cryptographic regression is as severe as any other security regression. Use a hardware-in-the-loop (HIL) test system if possible, running the actual target binary against the CAVP test vectors.

> **Principle 52.** *NIST CAVP test vectors are the acceptance criterion for any cryptographic implementation; passing all KATs is necessary but not sufficient for a correct and secure implementation.*

---

## Chapter 53 — Profiling Crypto on Embedded Targets

Crypto performance must be measured, not estimated. The discrepancy between theoretical and actual throughput on embedded devices is often 2–5×.

**Measurement methodology:**

```c
/* Use DWT cycle counter on ARM Cortex-M */
CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
DWT->CYCCNT = 0;
DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;

uint32_t start = DWT->CYCCNT;
/* operation under test */
uint32_t end = DWT->CYCCNT;
uint32_t cycles = end - start;
float us = (float)cycles / (SystemCoreClock / 1e6f);
```

**Metrics to collect:**

| Metric | Method |
|--------|--------|
| Throughput (B/s) | Time to encrypt 1 KB, 4 KB, 64 KB; extrapolate |
| Latency (us/op) | Time for single encrypt/decrypt of minimum message |
| Key setup (cycles) | Time for key import and round key computation |
| DMA overhead | Compare DMA-coupled vs CPU-coupled operation |
| CPU utilization | Cycles used vs total during 1-second window |

**Profiling pitfalls:**

*Cache cold-start bias:* first operation is slower due to cache misses. Warm the cache with a dummy operation before profiling.

*Interrupt interference:* system tick interrupts and peripheral ISRs can perturb cycle counts. Disable interrupts during short measurements; use average-of-N for longer measurements.

*Compiler optimization:* the compiler may eliminate benchmarked operations if outputs are unused. Use `volatile` results or compiler-specific barriers.

*DMA completion latency:* DMA operations complete asynchronously; measure from start to interrupt arrival, not from start to DMA enable.

**Reference performance targets** (AES-128-GCM, ARM Cortex-M33 at 64 MHz):
- Software AES-GCM: ~2–4 MB/s
- Hardware AES + software GHASH: ~8–12 MB/s
- Hardware AES + hardware GHASH: ~20–40 MB/s

If your measurements are more than 50% below these targets, audit the following: DMA alignment, cache coherency, interrupt masking configuration, and whether hardware acceleration is actually active.

> **Principle 53.** *Measure crypto throughput on the actual target silicon under realistic conditions before committing to a protocol that depends on specific performance characteristics.*

---

# Part XI — Mastery

---

## Chapter 54 — Debugging Cryptographic Failures

Cryptographic failures are binary: decryption either succeeds or fails. They give no gradient information. The debugging discipline is systematic elimination.

**The debugging procedure:**

```
   Step 1: Isolate the failure
   ──────────────────────────
   Does the failure occur on:
   a) A known test vector? → Implementation bug
   b) A freshly generated message (encrypt then immediately decrypt)? → State bug
   c) A message received from another device? → Protocol / interoperability bug

   Step 2: Check keys
   ──────────────────
   Dump and compare key bytes at sender and receiver.
   Keys must match exactly, including byte order.

   Step 3: Check nonce
   ───────────────────
   Dump nonce at sender. Reconstruct nonce at receiver.
   For TLS-style: verify sequence number matches on both sides.
   For explicit nonce: verify nonce is included and parsed correctly.

   Step 4: Check associated data
   ─────────────────────────────
   AD must be identical at sender and receiver.
   Any difference in AD → tag failure.
   Check byte order, padding, length encoding of fields in AD.

   Step 5: Check ciphertext
   ─────────────────────────
   Dump ciphertext immediately after encryption.
   Compare with ciphertext received before decryption.
   If different: network corruption, framing error, or buffer overflow.

   Step 6: Check tag
   ─────────────────
   If using external tag (GCM with separate ciphertext+tag buffers):
   Verify tag byte position and length match between sender and receiver.
```

**Common interoperability failures:**

| Symptom | Likely Cause |
|---------|-------------|
| Tag verification always fails | Key mismatch, nonce mismatch, or AD mismatch |
| First message succeeds, subsequent fail | Nonce not incrementing correctly on one side |
| Intermittent failures | Cache coherency issue with DMA |
| Failures after reboot | Nonce counter not persisted to NVM |
| Failures with specific message lengths | Padding bug or block alignment error |
| Failures across device models | Byte order difference (big/little endian) in header parsing |

**Endianness** is the single most common interoperability bug in embedded crypto. AES operates on bytes; the block cipher itself is endian-neutral. But the nonce, counter, and associated data are often packed from struct fields, and C structs on ARM are little-endian while network byte order is big-endian. Verify the byte order of every field that enters AEAD computation.

> **Principle 54.** *A tag verification failure means keys, nonces, or associated data differ between sender and receiver — these are the only three causes. Methodical comparison of each eliminates the failure.*

---

## Chapter 55 — Architectural Patterns for Secure Systems

Three architectural patterns appear in nearly every well-designed embedded secure system. They are not algorithms — they are structural choices.

**Pattern 1: The Crypto Service**

Isolate all cryptographic operations behind a service interface. No code outside the crypto service reads key material or calls crypto primitives directly. The service exposes only high-level operations: `SecureChannel_Send(channel, data)`, `SecureChannel_Receive(channel, &data)`.

This pattern enforces key isolation (key material never leaves the service) and simplifies auditing (the security review focuses on one component, not the entire codebase).

```
   ┌─────────────────────────────────────────────────────────┐
   │                   Application                           │
   └──────────────────────┬──────────────────────────────────┘
                          │ High-level operations only
   ┌──────────────────────▼──────────────────────────────────┐
   │               Crypto Service Layer                      │
   │  Key store │ AEAD engine │ Nonce mgr │ TRNG interface   │
   └──────────────────────┬──────────────────────────────────┘
                          │ Hardware interface only
   ┌──────────────────────▼──────────────────────────────────┐
   │              Hardware (AES engine, TRNG, SE)            │
   └─────────────────────────────────────────────────────────┘
```

**Pattern 2: Session Key Derivation per Connection**

Never use a long-lived key directly for data encryption. Always derive session-specific keys. Even with a pre-shared root key, use HKDF or SP 800-108 to derive per-session keys, including a session-specific nonce space.

```
   Root key K ──► KDF(K, session_id, "enc") ──► K_session_enc
               └► KDF(K, session_id, "auth") ──► K_session_auth
   
   session_id = random 128-bit value, exchanged in handshake
```

**Pattern 3: Defense Zones**

Partition the system into security zones. Data crossing a zone boundary must be authenticated (and possibly encrypted). A zone has a defined trust level; code within a zone is trusted to handle data at that level.

```
   ┌─────────────────────────────────────────┐
   │  Secure Zone (TrustZone Secure World)   │
   │  - Root key storage                     │
   │  - Crypto service                       │
   │  - Secure boot verification             │
   └──────────────────┬──────────────────────┘
          AEAD-authenticated boundary crossing
   ┌──────────────────▼──────────────────────┐
   │  Normal Zone (TrustZone Normal World)   │
   │  - Application logic                    │
   │  - Session keys (derived, limited life) │
   │  - Network stack                        │
   └─────────────────────────────────────────┘
```

> **Principle 55.** *Key material must not cross zone boundaries in cleartext; every boundary crossing requires an authenticated and encrypted transfer, regardless of how trusted the receiving code appears to be.*

---

## Chapter 56 — Common Errors and Their Meaning

| Error / Symptom | Root Cause | Fix |
|-----------------|-----------|-----|
| `PSA_ERROR_INVALID_SIGNATURE` always | Key mismatch, nonce mismatch, or AD mismatch | Dump and compare all three |
| First decrypt succeeds, all subsequent fail | Sequence number / nonce not synchronized | Verify nonce generation and exchange |
| Intermittent decrypt failure (1 in 100) | DMA cache coherency violation | Add cache invalidation before/after DMA |
| Decrypt fails after reboot | Nonce counter not persisted to NVM | Add NVM write-before-use for nonce counter |
| Authentication passes but plaintext wrong | Decryption key/IV correct, but wrong decrypt direction or block offset | Verify counter starts at correct value |
| TRNG health test alarm at boot | Hardware defect or supply noise | Check power supply decoupling; run ATE re-test |
| Device bricked after firmware update | Non-atomic NVM write interrupted | Implement A/B partition or two-phase commit |
| DPA attack recovered the key | Unprotected software AES on cached CPU | Use hardware AES or masked implementation |
| Two devices share same key | Provisioning collision / TRNG weakness | Audit provisioning records; strengthen seed |
| `mbedtls_aead_encrypt` returns `-0x6080` (MBEDTLS_ERR_GCM_AUTH_FAILED) | Tag verification failure | See first row |
| `wolfSSL_write` fails with `MEMORY_E` | Insufficient heap for TLS record | Reduce MAX_RECORD_SIZE or use static buffers |
| ChaCha20-Poly1305 nonce is 64 bits not 96 | Library follows draft RFC, not final RFC 8439 | Update library or pad nonce to 96 bits |

---

## Chapter 57 — How to Actually Learn Embedded Cryptography

The standard tutorial path is wrong for embedded architects. The standard path: read a general cryptography textbook, learn algorithms in isolation, then try to apply them to embedded systems. The result is an architect who knows AES but does not know why their GCM-over-SPI-to-SE fails authentication half the time.

**The contrarian path:**

*Start with implementations, not mathematics.* Read the Mbed TLS source for AES-GCM. Read the mbedtls_gcm.c file. Follow the code path from `mbedtls_gcm_crypt_and_tag()` to the hardware acceleration layer. You learn algorithms by seeing them implemented, not by reading their specifications.

*Read NIST documents as reference, not tutorial.* NIST SP 800-38D (GCM) is 39 pages. Read it once you understand GCM operationally; it confirms and formalizes what you already know. Reading it first produces confusion, not understanding.

*Build and break things.* Implement AES-GCM without a library (in a test environment, not production). Then attack your implementation: try nonce repetition, try truncating the tag, try flipping bits in the ciphertext. This builds intuition for the failure modes.

*Read the attack literature.* The BEAST, Lucky13, POODLE, ROBOT, and Heartbleed papers are short and readable. Each one teaches a class of vulnerability that abstract cryptography courses skip.

*Study a hardware reference manual.* Take one SoC you know (STM32H5, nRF5340, NXP LPC55S69) and read the entire crypto peripheral chapter: the AES block, the TRNG, the PKA, the secure storage. Learn the DMA connection, the interrupt model, the programming sequence. This makes hardware acceleration real, not abstract.

**The five sources that matter:**

1. NIST SP 800-38D (GCM), 800-38B (CMAC), 800-90A (DRBG): the authoritative specs.
2. RFC 8439: ChaCha20-Poly1305.
3. *Cryptography Engineering* (Ferguson, Schneier, Kohno): the only general cryptography text that addresses implementation directly.
4. *The Hardware Hacker* (Huang): physical security for embedded devices.
5. Mbed TLS source code: the reference implementation for embedded symmetric crypto.

Avoid "applied cryptography" courses that do not include implementation security. Avoid tutorials that use ECB mode in their examples. Avoid any source that does not discuss nonce management.

> **Principle 57.** *Understanding cryptography means understanding its failure modes. Study attacks before studying algorithms — the failure modes illuminate the security requirements that the algorithms exist to satisfy.*

---

# Appendices

---

## Appendix A — Algorithm Reference

| Algorithm | Category | Key Size | Block/Output | Standard | Recommended |
|-----------|----------|----------|-------------|----------|-------------|
| AES-128 | Block cipher | 128 b | 128 b | FIPS 197 | Yes |
| AES-256 | Block cipher | 256 b | 128 b | FIPS 197 | Yes (post-quantum) |
| ChaCha20 | Stream cipher | 256 b | 64 B keystream | RFC 8439 | Yes (SW-only targets) |
| AES-GCM | AEAD | 128 or 256 b | arbitrary | NIST SP 800-38D | Yes (default) |
| AES-CCM | AEAD | 128 b | arbitrary | NIST SP 800-38C | Yes (BLE/802.15.4) |
| AES-SIV | AEAD | 256 b (2×128) | arbitrary | RFC 5297 | Yes (misuse-resistant) |
| ChaCha20-Poly1305 | AEAD | 256 b | arbitrary | RFC 8439 | Yes (SW-only) |
| AES-CMAC | MAC | 128 b | 128 b | NIST SP 800-38B | Yes |
| HMAC-SHA256 | MAC | any | 256 b | RFC 2104 | Yes |
| HMAC-SHA256/128 | MAC | any | 128 b (truncated) | RFC 2104 | Yes (bandwidth-limited) |
| HKDF-SHA256 | KDF | any | variable | RFC 5869 | Yes |
| SP 800-108 CTR-CMAC | KDF | 128 b | variable | NIST SP 800-108 | Yes (embedded) |
| DES / 3DES | Block cipher | 56/112/168 b | 64 b | — | No (deprecated) |
| RC4 | Stream cipher | variable | variable | — | No (broken) |
| MD5 | Hash | — | 128 b | — | No (broken) |
| SHA-1 | Hash | — | 160 b | — | No (deprecated for new use) |
| SHA-256 | Hash | — | 256 b | FIPS 180-4 | Yes |
| SHA-512 | Hash | — | 512 b | FIPS 180-4 | Yes |
| SHA3-256 | Hash | — | 256 b | FIPS 202 | Yes |
| BLAKE2s | Hash | — | 256 b | RFC 7693 | Yes (SW-only embedded) |
| PRESENT | Block cipher | 80/128 b | 64 b | ISO 29192-2 | Limited (Class 0 MCU only) |

---

## Appendix B — Mode of Operation Reference

| Mode | Category | Parallelizable | Padding | Nonce Type | Standard |
|------|----------|---------------|---------|-----------|----------|
| ECB | Confidentiality | Yes | Yes | None | NIST SP 800-38A |
| CBC | Confidentiality | Dec only | Yes | Random, unpredictable | NIST SP 800-38A |
| CTR | Confidentiality | Yes | No | Counter | NIST SP 800-38A |
| OFB | Confidentiality | No | No | Unique | NIST SP 800-38A |
| CFB | Confidentiality | Dec only | No | Unique | NIST SP 800-38A |
| GCM | AEAD | Yes | No | Unique 96-bit | NIST SP 800-38D |
| CCM | AEAD | No (2-pass) | No | Unique | NIST SP 800-38C |
| EAX | AEAD | Yes | No | Unique | Bellaïre et al. |
| SIV | AEAD (misuse-resistant) | No (2-pass) | No | Optional | RFC 5297 |
| XTS | Disk encryption | Yes | Partial | Sector+tweak | IEEE P1619 |
| CMAC | Authentication | No | No | None | NIST SP 800-38B |
| GMAC | Authentication | Yes | No | Unique 96-bit | NIST SP 800-38D |

---

## Appendix C — Crypto Cheat Sheet

**AES-GCM nonce construction:**
```
Nonce (96 bits) = Fixed (32 bits) || Counter (64 bits)
OR
Nonce (96 bits) = IV XOR Sequence_Number_padded
```

**HKDF two-step:**
```
PRK = HMAC-SHA256(salt, IKM)                    # Extract
OKM = T(1) || T(2) || ... where T(i) = HMAC-SHA256(PRK, T(i-1) || info || i)  # Expand
```

**SP 800-108 Counter KDF:**
```
K(i) = CMAC(K_master, i || Label || 0x00 || Context || L)
i: 4-byte counter, Label: purpose string, L: output length in bits
```

**Constant-time comparison:**
```c
int ct_equal(const uint8_t *a, const uint8_t *b, size_t n) {
    uint8_t diff = 0;
    for (size_t i = 0; i < n; i++) diff |= a[i] ^ b[i];
    return diff == 0;
}
```

**Key zeroization:**
```c
void secure_zero(void *p, size_t n) {
    volatile uint8_t *vp = (volatile uint8_t *)p;
    while (n--) *vp++ = 0;
}
```

**AES-GCM tag size guidance:**
- 128 bits: recommended, required for FIPS
- 96 bits: acceptable for constrained bandwidth
- 64 bits: use only when protocol requires (BLE, Zigbee); birthday bound at 2^32 messages
- 32 bits: dangerous without strict rate limiting

**Nonce counter persistence (NVM write-before-use):**
```
Before encryption: write (counter+1) to NVM → use counter for encryption
After power-on: read counter from NVM; it reflects next-unused value
```

---

## Appendix D — Side-Channel Countermeasure Reference

| Attack | Countermeasure | Cost | Notes |
|--------|---------------|------|-------|
| SPA | Constant-time code paths | Low | No key-dependent branches |
| DPA (1st order) | Boolean masking | 4–8× overhead | Requires fresh randomness per operation |
| DPA (2nd order) | 2nd-order masking | 16–32× overhead | Requires higher TRNG bandwidth |
| Cache-timing | Constant-time AES (bitsliced or HW) | Moderate | HW AES is always preferred |
| EM analysis | Physical shielding + spreading | Physical redesign | Ferrite bead, ground plane |
| DFA (single fault) | Double computation | 2× overhead | Compare results; abort on mismatch |
| DFA (multi-fault) | Redundant encoding + check | 3–4× overhead | Parity or CRC over state bytes |
| Voltage glitch | Brownout detector (BOD) | Hardware feature | Enable in chip config registers |
| Clock glitch | Clock monitor | Hardware feature | Enable in chip config registers |
| JTAG readout | Debug lock (RDP level 2) | Irreversible OTP | Cannot undo; verify before production |
| Cold-boot key extraction | Key isolation in SE / OTP | Hardware cost | Keys never in accessible RAM |

---

## Appendix E — Glossary

**AEAD**: Authenticated Encryption with Associated Data. A single primitive providing confidentiality and authenticity.

**ARX**: Add-Rotate-XOR. Construction class for stream ciphers and hash functions using only these three operations; inherently constant-time.

**Associated Data (AD)**: Data authenticated but not encrypted in an AEAD scheme. Typically packet headers.

**Block cipher**: A keyed permutation on fixed-size blocks (128 bits for AES).

**CAVP**: Cryptographic Algorithm Validation Program (NIST). Provides test vectors for validated algorithm implementations.

**CCM**: Counter with CBC-MAC. An AEAD mode combining AES-CTR and AES-CBC-MAC.

**CMAC**: Cipher-based MAC. A MAC built from a block cipher (AES-CMAC in common use).

**CTR**: Counter Mode. A mode of operation that converts a block cipher into a stream cipher.

**DEK**: Data-Encryption Key. A key used only for encrypting data, not other keys.

**DFA**: Differential Fault Analysis. An attack that extracts keys from comparison of correct and faulted outputs.

**DPA**: Differential Power Analysis. A statistical side-channel attack using power traces.

**DRBG**: Deterministic Random Bit Generator. A pseudorandom generator seeded from a TRNG.

**ECB**: Electronic Codebook. A broken mode of operation that encrypts each block independently.

**eFuse / OTP**: Electrically-writable one-time-programmable memory. Used for permanent key storage.

**EDHOC**: Ephemeral Diffie-Hellman Over COSE. Lightweight authenticated key exchange for constrained devices.

**GCM**: Galois/Counter Mode. An AEAD mode combining AES-CTR and GHASH.

**GHASH**: The polynomial MAC component of GCM, operating over GF(2^128).

**HKDF**: HMAC-based Key Derivation Function (RFC 5869). Two-step extract-expand KDF.

**HMAC**: Hash-based MAC (RFC 2104). A MAC constructed from a hash function.

**HSM**: Hardware Security Module. A tamper-resistant device for key storage and cryptographic operations.

**IV**: Initialization Vector. A per-operation value used by modes such as CBC. Often used interchangeably with nonce.

**KDF**: Key Derivation Function. A function that produces cryptographic key material from a secret.

**KEK**: Key-Encryption Key. A key used only to encrypt other keys.

**MAC**: Message Authentication Code. A short tag proving message integrity and authenticity.

**Masking**: A side-channel countermeasure that XOR's intermediate values with random masks.

**Nonce**: Number Used Once. A per-operation value ensuring that the same plaintext encrypted twice produces different ciphertexts.

**OSCORE**: Object Security for Constrained RESTful Environments (RFC 8613). AEAD-based CoAP security.

**OTP**: One-Time Programmable. See eFuse.

**Poly1305**: A one-time MAC designed for use with ChaCha20.

**PSA**: Platform Security Architecture (Arm). A security framework for IoT devices.

**PSA Crypto API**: A portable C API for cryptographic operations, defined by the PSA specification.

**RDP**: Read-out protection (STM32). A fuse-based mechanism preventing flash read-out via debug interfaces.

**SIV**: Synthetic IV. A nonce-misuse-resistant AEAD mode (RFC 5297).

**SPA**: Simple Power Analysis. A side-channel attack reading key information from a single power trace.

**Stream cipher**: A cipher that generates a keystream XOR'd with plaintext. ChaCha20 is the standard.

**SUIT**: Software Updates for Internet of Things (RFC 9124). Standard firmware update manifest format.

**TEE**: Trusted Execution Environment. An isolated execution environment (e.g., TrustZone secure world).

**TRNG**: True Random Number Generator. A hardware entropy source.

**TrustZone**: ARM's hardware isolation mechanism separating secure and normal worlds on Cortex-M/A.

**XTS**: XEX Tweakable Block Cipher with Ciphertext Stealing. Mode for disk sector encryption.

---

> *Cryptography does not fail because the mathematics breaks. It fails because someone assumed encryption was authentication, or assumed a nonce was unique, or assumed a key was secret when it lived in readable flash. The mathematics is the easy part.*

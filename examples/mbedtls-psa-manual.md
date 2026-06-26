# Mbed TLS and PSA — A First-Principles Manual

## Preface

This manual is for the engineer who must put cryptography or TLS into a real product — most often a constrained device — and who has discovered that the library called Mbed TLS is in the middle of changing what it fundamentally *is*. You will leave knowing the cryptographic key model that now sits at the center of everything, how TLS is built on top of it, what changed in the 4.0 release, and how to ship a build that fits in the flash you actually have.

You will learn in this order. First, orientation: what these names mean, what problem the software solves, and the single duality that organizes the whole subject. Then anatomy: the key, which is the atom of the new world. Then how builds are configured and composed, because a misconfigured build is the first wall every newcomer hits. Then the mechanism underneath — drivers, the key store, storage, randomness. Then the cryptographic operations in depth, then TLS and X.509, then the secure-boundary architecture that gives "PSA" its name. Then production realities, then daily tooling, then the synthesis of mastery.

A note on the name. The brief that commissioned this manual wrote "EmbedTLS." There is no such library. The software is **Mbed TLS** — *embedded* TLS — and the rest of this manual uses its real name. This is not pedantry. The most common newcomer failure is to follow a tutorial written for a different version of a differently-named ancestor of this library, and to write code that no longer compiles. Names matter here precisely because the names have changed three times.

Read Part I in full before anything else. After that, each chapter stands on its own, though it assumes the vocabulary built before it.

---

## Table of Contents

**[Part I — Orientation](#part-i--orientation)**
- [Chapter 1 — The Problem](#chapter-1--the-problem)
- [Chapter 2 — Three Names, Three Things](#chapter-2--three-names-three-things)
- [Chapter 3 — The Great Duality: Key by Value vs Key by Reference](#chapter-3--the-great-duality-key-by-value-vs-key-by-reference)
- [Chapter 4 — The Minimal Mental Model](#chapter-4--the-minimal-mental-model)
- [Chapter 5 — A History That Explains the Present](#chapter-5--a-history-that-explains-the-present)
- [Chapter 6 — The Four Doors of PSA](#chapter-6--the-four-doors-of-psa)

**[Part II — Anatomy of a Key](#part-ii--anatomy-of-a-key)**
- [Chapter 7 — The Key Object](#chapter-7--the-key-object)
- [Chapter 8 — Key Types](#chapter-8--key-types)
- [Chapter 9 — Lifetime and Location](#chapter-9--lifetime-and-location)
- [Chapter 10 — The Key Policy](#chapter-10--the-key-policy)
- [Chapter 11 — The Algorithm Encoding](#chapter-11--the-algorithm-encoding)
- [Chapter 12 — The Operation Families](#chapter-12--the-operation-families)
- [Chapter 13 — The Error Space](#chapter-13--the-error-space)

**[Part III — Configuration and Composition](#part-iii--configuration-and-composition)**
- [Chapter 14 — The Two Configuration Files](#chapter-14--the-two-configuration-files)
- [Chapter 15 — WANT, BUILTIN, ACCEL](#chapter-15--want-builtin-accel)
- [Chapter 16 — Composing a Build](#chapter-16--composing-a-build)
- [Chapter 17 — The Repository Split](#chapter-17--the-repository-split)
- [Chapter 18 — Headers and Namespaces](#chapter-18--headers-and-namespaces)

**[Part IV — Mechanism and Internals](#part-iv--mechanism-and-internals)**
- [Chapter 19 — The Dispatch Layer](#chapter-19--the-dispatch-layer)
- [Chapter 20 — Transparent Drivers](#chapter-20--transparent-drivers)
- [Chapter 21 — Opaque Drivers](#chapter-21--opaque-drivers)
- [Chapter 22 — The Key Store and Slots](#chapter-22--the-key-store-and-slots)
- [Chapter 23 — Persistent Storage](#chapter-23--persistent-storage)
- [Chapter 24 — The Multipart State Machine](#chapter-24--the-multipart-state-machine)
- [Chapter 25 — Randomness](#chapter-25--randomness)

**[Part V — The Cryptography API in Depth](#part-v--the-cryptography-api-in-depth)**
- [Chapter 26 — Hashing](#chapter-26--hashing)
- [Chapter 27 — Message Authentication](#chapter-27--message-authentication)
- [Chapter 28 — Unauthenticated Ciphers](#chapter-28--unauthenticated-ciphers)
- [Chapter 29 — AEAD](#chapter-29--aead)
- [Chapter 30 — Key Derivation](#chapter-30--key-derivation)
- [Chapter 31 — Signatures: Hash vs Message](#chapter-31--signatures-hash-vs-message)
- [Chapter 32 — Asymmetric Encryption and Key Agreement](#chapter-32--asymmetric-encryption-and-key-agreement)

**[Part VI — TLS and X.509](#part-vi--tls-and-x509)**
- [Chapter 33 — The TLS Module](#chapter-33--the-tls-module)
- [Chapter 34 — Context and Configuration](#chapter-34--context-and-configuration)
- [Chapter 35 — The Handshake Lifecycle](#chapter-35--the-handshake-lifecycle)
- [Chapter 36 — TLS 1.3 vs TLS 1.2](#chapter-36--tls-13-vs-tls-12)
- [Chapter 37 — X.509 Certificates](#chapter-37--x509-certificates)
- [Chapter 38 — The PK Layer](#chapter-38--the-pk-layer)
- [Chapter 39 — How TLS Consumes PSA](#chapter-39--how-tls-consumes-psa)

**[Part VII — The Secure Boundary](#part-vii--the-secure-boundary)**
- [Chapter 40 — Secure and Non-Secure Worlds](#chapter-40--secure-and-non-secure-worlds)
- [Chapter 41 — The Crypto Client Build](#chapter-41--the-crypto-client-build)
- [Chapter 42 — TF-M and the Root of Trust](#chapter-42--tf-m-and-the-root-of-trust)
- [Chapter 43 — The Sibling APIs](#chapter-43--the-sibling-apis)

**[Part VIII — Production](#part-viii--production)**
- [Chapter 44 — Trimming the Footprint](#chapter-44--trimming-the-footprint)
- [Chapter 45 — Entropy on Bare Metal](#chapter-45--entropy-on-bare-metal)
- [Chapter 46 — Thread Safety](#chapter-46--thread-safety)
- [Chapter 47 — Side Channels](#chapter-47--side-channels)
- [Chapter 48 — The 4.0 Migration](#chapter-48--the-40-migration)
- [Chapter 49 — Certification](#chapter-49--certification)

**[Part IX — Tooling and Workflow](#part-ix--tooling-and-workflow)**
- [Chapter 50 — Building](#chapter-50--building)
- [Chapter 51 — The Config Tool](#chapter-51--the-config-tool)
- [Chapter 52 — Testing](#chapter-52--testing)
- [Chapter 53 — Which Sample Programs to Read](#chapter-53--which-sample-programs-to-read)
- [Chapter 54 — Debugging the Wire](#chapter-54--debugging-the-wire)

**[Part X — Mastery](#part-x--mastery)**
- [Chapter 55 — Reading a PSA Error](#chapter-55--reading-a-psa-error)
- [Chapter 56 — Common Errors and Their Meaning](#chapter-56--common-errors-and-their-meaning)
- [Chapter 57 — Architecting Around PSA](#chapter-57--architecting-around-psa)
- [Chapter 58 — How to Actually Learn It](#chapter-58--how-to-actually-learn-it)
- [Chapter 59 — Synthesis](#chapter-59--synthesis)

**[Appendices](#appendices)**
- [Appendix A — Configuration Symbol Reference](#appendix-a--configuration-symbol-reference)
- [Appendix B — Key Lifecycle Function Reference](#appendix-b--key-lifecycle-function-reference)
- [Appendix C — Algorithm and Type Macro Cheat Sheet](#appendix-c--algorithm-and-type-macro-cheat-sheet)
- [Appendix D — Status Code Catalog](#appendix-d--status-code-catalog)
- [Appendix E — Glossary](#appendix-e--glossary)
- [Appendix F — Upstream Sources](#appendix-f--upstream-sources)

---

## Part I — Orientation

### Chapter 1 — The Problem

A device must talk to a server it cannot trust, over a network anyone can read. It must prove who it is, verify who the server is, and exchange bytes no eavesdropper can decode or alter. That is the TLS problem. Underneath it lies a smaller, harder problem: the device must perform cryptography — hashing, encryption, signatures — correctly, in constant time, on a processor with kilobytes of RAM and no operating system to lean on.

General-purpose crypto libraries assume a desktop: megabytes of memory, a filesystem, an OS entropy source, a heap that never runs out. The constrained device has none of these. It has a few tens of kilobytes of flash for *all* of its code, an interrupt-driven main loop, perhaps a hardware crypto accelerator it would be wasteful not to use, and an attacker who may hold the physical device in their hand and probe it with an oscilloscope.

Mbed TLS exists to solve cryptography and TLS under exactly these constraints. It is written in portable C, it compiles down to a footprint you control symbol by symbol, it can route operations to hardware, and it was designed from the start to be auditable. It is also, deliberately, the *reference implementation* of a standardized cryptographic interface — the PSA Crypto API — which is the subject of half this manual.

The thing to understand before anything else: this is not a library that does one thing. It is a cryptographic core, a TLS protocol engine, and an X.509 certificate engine, that you assemble into the subset your product needs. Most newcomers treat it as a monolith and drown in its surface area. It is a kit.

> **Principle 1.** *Mbed TLS is a kit, not a monolith — you ship the subset you compile in, and nothing else.*

### Chapter 2 — Three Names, Three Things

Newcomers conflate three things that share the syllable "PSA" or the word "Mbed." Untangle them now and the rest of the subject falls into place.

**Mbed TLS** is the software — a C library and its source repository. It implements TLS, X.509, and (historically) all the cryptography those need.

**PSA** — Platform Security Architecture — is an *architecture and certification program*, originated by Arm and now stewarded through PSA Certified and TrustedFirmware. It is not code. It is a set of specifications, threat models, a security-level scheme (Level 1, 2, 3), and a family of standardized APIs that any vendor's hardware can implement. It provides a trusted code base that complies with platform security specifications, and security APIs that create a consistent interface to underlying Root of Trust hardware.

**The PSA Crypto API** is *one* of the PSA specifications — the cryptographic one. It defines, in a header you can read, exactly what `psa_import_key`, `psa_sign_message`, and a few hundred sibling functions do, independent of who implements them.

The relationship: PSA is the architecture; the PSA Crypto API is one of its four interfaces; Mbed TLS is the best-known implementation of that interface. A Silicon Labs chip, an Infineon secure element, and a desktop Linux box can all expose the *same* PSA Crypto API while implementing it on wildly different hardware. That portability is the entire point of standardizing the interface.

```
        Platform Security Architecture (PSA)
        the specifications + certification program
                        │
        ┌───────────────┼───────────────┬──────────────────┐
        ▼               ▼               ▼                  ▼
   Crypto API      Secure Storage   Attestation     Firmware Update
        │           API              API              API
        │
        ▼
   implemented by ──► Mbed TLS / TF-PSA-Crypto   (software)
                 ──► TF-M on a secure MCU        (firmware)
                 ──► a vendor secure element      (hardware)
```

PSA is the standard. Mbed TLS is an implementation of part of it. There is no third relationship.

> **Principle 2.** *PSA is the interface; Mbed TLS is one implementation behind it — never mistake the contract for the contractor.*

### Chapter 3 — The Great Duality: Key by Value vs Key by Reference

Every complex system rests on one binary opposition. Here it is: **does your code hold the key, or does it hold a name for the key?**

In the old model — the one every pre-2020 tutorial teaches — a key is a C structure full of bytes that lives in your application's memory. You load `mbedtls_rsa_context`, you pass it around, you call `mbedtls_rsa_pkcs1_sign` on it, and the private exponent sits in your RAM the whole time. The key is a **value**. You own it; you can read it, copy it, leak it.

In the PSA model, a key is a small integer — a `psa_key_id_t` — that *names* key material managed by the cryptographic subsystem. You never see the bytes. You call `psa_sign_message(key_id, ...)` and the subsystem, not you, touches the secret. The key is a **reference**. The material may live in your RAM, or in a separate secure partition, or inside a tamper-resistant chip you have no bus access to — and *your code is identical in all three cases*.

```
   KEY BY VALUE (legacy mbedtls_)        KEY BY REFERENCE (PSA)
   ────────────────────────────         ──────────────────────
   mbedtls_rsa_context ctx;             psa_key_id_t key;
   /* private key bytes live here */    /* just a 32-bit handle  */
        │                                     │
        ▼                                     ▼
   your application memory              ┌───────────────────┐
   holds the secret                     │ crypto subsystem  │
        │                               │  ┌──────────────┐ │
   you call functions that              │  │ key material │ │  ← may be
   read the bytes directly              │  └──────────────┘ │    unreachable
                                        └───────────────────┘    by your code
                                          you ask it to operate
                                          ON your behalf
```

This is *the* duality. It explains the driver model (the material can live in hardware), the security story (the application can be compromised without the key leaking), the storage model (a reference can outlive a power cycle), and the entire 4.0 migration (functions stopped taking key bytes and started taking key IDs). Hold this distinction in your mind and nine-tenths of the design becomes obvious.

> **Principle 3.** *A PSA key is a name, not a value — your code never holds the secret, only permission to use it.*

### Chapter 4 — The Minimal Mental Model

Memorize this picture. Everything else hangs on it.

```
   ┌──────────────────────────────────────────────────────────┐
   │                     YOUR APPLICATION                       │
   │   holds key IDs, calls psa_* and mbedtls_ssl_* functions   │
   └───────────────┬───────────────────────┬───────────────────┘
                   │ TLS / X.509            │ crypto
                   ▼                        ▼
   ┌───────────────────────────┐  ┌──────────────────────────────┐
   │   Mbed TLS                 │  │   TF-PSA-Crypto                │
   │   ssl, x509, pk, pkcs7     │──►│   the PSA Crypto API + core    │
   │   (the protocol engines)   │  │                                │
   └───────────────────────────┘  │   ┌────────────────────────┐   │
                                   │   │  driver dispatch layer  │   │
                                   │   └─────────┬──────────────┘   │
                                   └─────────────┼──────────────────┘
                              ┌──────────────────┼──────────────────┐
                              ▼                  ▼                  ▼
                       built-in software   transparent driver   opaque driver
                       implementation      (HW accelerator)     (secure element)
```

Four truths in one diagram. First: TLS and X.509 sit *on top of* the crypto API — they are clients of it, exactly as your application is. Second: since 4.0 the crypto lives in a separate component, TF-PSA-Crypto. Third: every crypto call funnels through a dispatch layer. Fourth: below the dispatch layer the work is done by software, by a hardware accelerator, or inside a secure element — and the layers above neither know nor care which.

The arrows point one way: down. Higher layers depend on lower; lower layers know nothing of higher. TLS depends on crypto; crypto depends on drivers; the application depends on all of it. Nothing reaches back up.

> **Principle 4.** *TLS is a client of the crypto API just as your application is — the protocol engine has no privileged path to the keys.*

### Chapter 5 — A History That Explains the Present

Most of this library's history is irrelevant trivia. Four turning points are not, because each one left a scar you will touch.

It began as **PolarSSL**, an independent TLS library. Arm acquired it and renamed it **mbed TLS**, folding it into the mbed IoT platform — this is why so much of the surrounding documentation and so many board SDKs say "mbed." Arm later donated it to **TrustedFirmware.org**, which is why the canonical home is now `github.com/Mbed-TLS` and the mailing list lives at `lists.trustedfirmware.org`. Each rename orphaned a generation of tutorials.

The fourth turning point is the one that matters most today. In **September 2025**, the project shipped **Mbed TLS 4.0.0** together with **TF-PSA-Crypto 1.0.0**. This introduced a major codebase restructuring: PSA Crypto functionality now resides in its own repository, Mbed-TLS/TF-PSA-Crypto, while TLS and X.509 components remain in Mbed TLS. Mbed TLS now uses PSA Crypto as the default cryptographic API, and these releases include significant API changes that break backward compatibility with previous versions.

So the present design is the residue of a deliberate decade-long migration: from a TLS library that happened to contain crypto, to a crypto standard (PSA) with a TLS library bolted on top. The 3.6 line remains the long-term-support branch for those who cannot migrate yet; Mbed TLS 3.6.4 is the latest LTS release that pre-dates the split. Everything new is built on the 4.x world.

History here is not decoration. If you read a tutorial, the *first* thing to establish is which era it was written for — PolarSSL, mbed TLS 2.x, Mbed TLS 3.x, or the 4.x split. The paradigm changed under each name.

> **Principle 5.** *Before trusting any Mbed TLS example, date it — the paradigm changed under every rename.*

### Chapter 6 — The Four Doors of PSA

There are exactly four PSA Certified functional APIs. They are Crypto, Secure Storage, Attestation, and Firmware Update. Each is a door into the Root of Trust; each answers one question a secure device must be able to answer.

| API | The question it answers | What it provides |
|-----|------------------------|------------------|
| **Crypto** | Can I perform this cryptographic operation without exposing the key? | Symmetric/asymmetric crypto, hashing, RNG, key storage by reference |
| **Secure Storage** | Can I store this secret so the application cannot read or tamper with it? | Internal Trusted Storage (ITS) and Protected Storage (PS) |
| **Attestation** | Can I prove to a remote party what firmware this device is running? | A signed Entity Attestation Token (EAT) |
| **Firmware Update** | Can I install a new image and verify it before trusting it? | A standard update install/verify interface |

Mbed TLS — through TF-PSA-Crypto — is the reference implementation of the **Crypto** door, and that is the door this manual mostly walks through. The other three are implemented in firmware, most prominently in **TF-M** (Trusted Firmware-M), the reference firmware that runs in a secure partition on Arm microcontrollers. The PSA Functional APIs provide a standardized set of vetted APIs to access the Root of Trust features and ensure portability across different hardware implementations.

The number is small on purpose. These APIs cover a minimal set of services that should be included into all devices: cryptography, secure storage, attestation, and firmware update. A device that can do cryptography, keep secrets, prove its identity, and update itself safely has the four primitives from which all higher security is composed. There is no fifth door.

> **Principle 6.** *Four doors — crypto, storage, attestation, update — compose every device security story; if you need a fifth, you have misdrawn one of the four.*

---

## Part II — Anatomy of a Key

### Chapter 7 — The Key Object

The key is the atom of the PSA world. Understand its structure and the API stops being three hundred unrelated functions and becomes a handful of verbs applied to one noun.

A key is three things bound together: **material**, **metadata**, and an **identifier**. The material is the secret bytes — and you, the application, generally never see them. The identifier is the `psa_key_id_t` integer you hold. The metadata is everything else the system needs to know about the key, and it is carried in an object of type `psa_key_attributes_t`.

The metadata stored in attributes includes the location of the key in storage (its key identifier and lifetime), the key's policy (usage flags and permitted algorithms), and information about the key itself: its type and size. The actual key material is not considered an attribute of a key.

```
   ┌─────────────────── a KEY ───────────────────┐
   │                                              │
   │   IDENTIFIER        METADATA       MATERIAL  │
   │   psa_key_id_t      attributes     (secret)  │
   │   ┌─────────┐      ┌──────────┐   ┌────────┐ │
   │   │  0x0001 │      │ type     │   │ ▓▓▓▓▓▓ │ │
   │   └─────────┘      │ size     │   │ ▓▓▓▓▓▓ │ │  ← you
   │     you hold       │ lifetime │   └────────┘ │    never
   │     this           │ usage    │   the system │    see
   │                    │ algorithm│   holds this │    this
   │                    └──────────┘              │
   └──────────────────────────────────────────────┘
```

The lifecycle is uniform regardless of key type. You populate an attributes object, you call a creation function that returns an identifier, you use the key by identifier, and you destroy it. If the key is persistent you call psa_set_key_id() and psa_set_key_lifetime(); you set the policy with psa_set_key_usage_flags() and psa_set_key_algorithm(); you set the type with psa_set_key_type(); then you call a creation function such as psa_import_key(), psa_generate_key(), psa_key_derivation_output_key(), or psa_copy_key().

One subtle, load-bearing rule: all of the key attributes are set when the key is created and cannot be changed without destroying the key first. A key's policy is immutable. You cannot widen the permissions of a key that already exists; you can only create a new one, or — if policy allows — copy it with a *narrower* policy.

> **Principle 7.** *A key is material plus immutable metadata plus a name; you may change which key you use, never what a key is.*

### Chapter 8 — Key Types

A key's **type** declares what kind of secret it is and therefore what can be done with it. The type is set with `psa_set_key_type()` and encoded as a `psa_key_type_t`. The taxonomy divides cleanly.

```
                         KEY TYPE
                            │
            ┌───────────────┴────────────────┐
            ▼                                 ▼
        SYMMETRIC                         ASYMMETRIC
   (one secret value)              (key pair OR public key)
            │                                 │
   ┌────────┼────────┐              ┌─────────┼──────────┐
   ▼        ▼        ▼              ▼         ▼          ▼
  RAW    AES/ARIA  HMAC          RSA       ECC       DH
  DATA   /Camellia /derivation  key pair  key pair   key pair
         /ChaCha20  base         + public  + public   + public
```

The first cut is symmetric versus asymmetric. A symmetric key is a single value — `PSA_KEY_TYPE_AES`, `PSA_KEY_TYPE_HMAC`, `PSA_KEY_TYPE_CHACHA20`, or the catch-all `PSA_KEY_TYPE_RAW_DATA` and `PSA_KEY_TYPE_DERIVE` for key-derivation inputs.

The second cut, within asymmetric, is *key pair* versus *public key*. `PSA_KEY_TYPE_RSA_KEY_PAIR` holds both private and public parts; `PSA_KEY_TYPE_RSA_PUBLIC_KEY` holds only the public part. The same split exists for elliptic-curve keys (`PSA_KEY_TYPE_ECC_KEY_PAIR(curve)` and its public counterpart) and Diffie–Hellman keys. Elliptic-curve types are parameterized by a *family* macro naming the curve — `PSA_ECC_FAMILY_SECP_R1`, `PSA_ECC_FAMILY_MONTGOMERY`, and so on.

Type and size together pin down the key completely. The size — `psa_set_key_bits()` — is the key's bit length: 256 for an AES-256 key, 2048 or 3072 for RSA, the curve's order size for ECC. For imported keys the size is inferred from the data; for generated keys you must state it.

> **Principle 8.** *Type answers "what kind of secret," size answers "how much of it" — together they determine everything the key can become.*

### Chapter 9 — Lifetime and Location

A key's **lifetime** answers two coupled questions: how long does it live, and where does it live? The lifetime of a key indicates where it is stored and which application and system actions will create and destroy it.

The first axis is **volatile versus persistent**. Conceptually, a volatile key is stored in RAM and has the lifetime PSA_KEY_LIFETIME_VOLATILE; it must be destroyed with a matching call to psa_destroy_key(). A volatile key vanishes at power-off and its identifier is assigned by the system. A persistent key survives reboots: persistent keys are preserved until the application explicitly destroys them or until an implementation-specific device management event occurs, such as a factory reset. Each persistent key carries a permanent identifier *you* choose. Within an application, the key identifier corresponds to a single key, specified when the key is created and when using the key.

```
   LIFETIME = ( PERSISTENCE , LOCATION )
              └─────┬──────┘ └────┬────┘
                    │              │
        VOLATILE ───┤              ├─── LOCATION 0: local storage
        (RAM, dies  │              │    (default, software)
         at reset)  │              │
                    │              ├─── LOCATION n: a secure element
        PERSISTENT ─┘              │    (managed by an opaque driver)
        (survives reset,           │
         you name it)              ...
```

The second axis, packed into the same `psa_key_lifetime_t` value, is **location**. The default lifetime value for a persistent key is PSA_KEY_LIFETIME_PERSISTENT, which corresponds to a default storage area; implementations can provide other lifetime values corresponding to different storage areas with different retention policies, or to secure elements with different security characteristics.

This second axis is where the duality of Chapter 3 cashes out. A location is a number, and a non-default location is the address of a *secure element managed by an opaque driver* (Chapter 21). Move a key's location and the same `psa_sign_message` call now executes inside tamper-resistant silicon — with no change to the calling code. Location is the seam between software keys and hardware keys.

> **Principle 9.** *Lifetime encodes both persistence and place; changing a key's place can move the secret into hardware without changing one line of calling code.*

### Chapter 10 — The Key Policy

A key's **policy** is its constitution: the set of things it is permitted to do, fixed at birth and unalterable. All keys have an associated policy that regulates which operations are permitted on the key; each policy is a set of usage flags and a specific algorithm that is permitted with the key.

The policy has two parts. The **usage flags** are a bitmask of `psa_key_usage_t`. Among them, PSA_KEY_USAGE_EXPORT determines whether the key material can be extracted from the cryptoprocessor or copied outside its security boundary, and PSA_KEY_USAGE_COPY determines whether the key material can be copied into a new key, which can have a different lifetime or a more restrictive policy. Alongside these are the operation flags — `PSA_KEY_USAGE_ENCRYPT`, `PSA_KEY_USAGE_DECRYPT`, `PSA_KEY_USAGE_SIGN_MESSAGE`, `PSA_KEY_USAGE_VERIFY_MESSAGE`, `PSA_KEY_USAGE_SIGN_HASH`, `PSA_KEY_USAGE_VERIFY_HASH`, and `PSA_KEY_USAGE_DERIVE`.

The second part is the **permitted algorithm**. The key permitted-algorithm policy is required for keys that will be used for a cryptographic operation. A key is not merely "an AES key" — it is "an AES key permitted to perform AES-GCM, and nothing else." Try to use it for AES-CBC and the operation is refused.

The reason for binding policy this tightly is the principle of least privilege made mechanical. A key that can only verify cannot be tricked into signing. A key without the EXPORT flag can never be read out, even by a compromised application — the cryptoprocessor simply refuses. The most security-critical decision you make about a key is the policy you give it, because you can never loosen it afterward.

The `PSA_KEY_USAGE_EXPORT` flag deserves a sentence of its own. Withhold it and you have created a key your own application cannot read — only use. This is the mechanism that makes the key-by-reference model meaningful: a reference to something you are forbidden to dereference.

> **Principle 10.** *Set the narrowest policy a key will ever need at creation, because policy only ever narrows — never widens.*

### Chapter 11 — The Algorithm Encoding

An **algorithm** in PSA is a value of type `psa_algorithm_t` — a 32-bit integer whose bits encode a category and its parameters. You rarely build these by hand; you use macros. But understanding that they are structured integers, not opaque enums, explains why algorithms compose.

```
   psa_algorithm_t  (32 bits)
   ┌──────────┬───────────────────────────────────────┐
   │ category │            parameters                 │
   └──────────┴───────────────────────────────────────┘
        │
        ├─ hash:        PSA_ALG_SHA_256
        ├─ MAC:         PSA_ALG_HMAC(PSA_ALG_SHA_256)
        ├─ cipher:      PSA_ALG_CBC_NO_PADDING
        ├─ AEAD:        PSA_ALG_GCM
        ├─ signature:   PSA_ALG_ECDSA(PSA_ALG_SHA_256)
        ├─ asym encrypt:PSA_ALG_RSA_OAEP(PSA_ALG_SHA_256)
        ├─ key agree:   PSA_ALG_ECDH
        └─ key deriv:   PSA_ALG_HKDF(PSA_ALG_SHA_256)
```

Notice the nesting. `PSA_ALG_HMAC(PSA_ALG_SHA_256)` is a macro that takes a hash algorithm and produces a MAC algorithm. `PSA_ALG_ECDSA(PSA_ALG_SHA_256)` builds a signature algorithm from a hash. This is the structured encoding at work: an algorithm that needs a hash takes the hash algorithm's value and folds it into its own. The composition is meaningful, not cosmetic — the resulting integer genuinely contains the sub-algorithm.

The practical payoff: you can extract pieces back out. `PSA_ALG_GET_HASH(alg)` returns the hash inside a composite algorithm. The dispatch layer uses exactly these extractor macros to decide what work to do. When you see a sign or MAC algorithm written as a macro of a hash, you are looking at the encoding, not a naming convention.

There is also the **wildcard** for policies: `PSA_ALG_ANY_HASH` lets a key's permitted-algorithm policy accept a signature with *any* hash, which TLS needs because the peer chooses the hash at handshake time. Wildcards live in policies, never in operations.

> **Principle 11.** *PSA algorithms are structured integers that nest — a signature contains its hash, and the system can read it back out.*

### Chapter 12 — The Operation Families

The cryptographic surface of PSA divides into a small number of operation families. Learn the families and you can predict the function names before you read them, because every family follows the same naming and the same lifecycle.

| Family | What it does | Single-shot | Multipart setup |
|--------|--------------|-------------|-----------------|
| **Hash** | Fingerprint a message | `psa_hash_compute` | `psa_hash_setup` |
| **MAC** | Authenticate with a symmetric key | `psa_mac_compute` | `psa_mac_sign_setup` |
| **Cipher** | Encrypt without authentication | `psa_cipher_encrypt` | `psa_cipher_encrypt_setup` |
| **AEAD** | Encrypt *with* authentication | `psa_aead_encrypt` | `psa_aead_encrypt_setup` |
| **Key derivation** | Stretch/derive keys from inputs | — | `psa_key_derivation_setup` |
| **Asymmetric signature** | Sign/verify with a private/public key | `psa_sign_message` | (no multipart) |
| **Asymmetric encryption** | Encrypt to a public key | `psa_asymmetric_encrypt` | (no multipart) |
| **Key agreement** | Derive a shared secret | `psa_raw_key_agreement` | via key derivation |

Two patterns recur across every row. First, the **single-shot versus multipart** split: a function that takes the whole input at once, and a setup/update/finish trio for streaming data too large to hold in memory. Second, the **compute/verify symmetry**: where there is a `compute` there is usually a `verify` that checks rather than produces.

This regularity is a gift. Once you have written one hash operation, you can write a MAC operation by analogy without reading the docs, because the verbs and the lifecycle are identical. The families differ in *what* they compute, not in *how you ask*.

> **Principle 12.** *Learn the lifecycle once and you have learned every operation family — they differ in payload, not in protocol.*

### Chapter 13 — The Error Space

Every PSA function returns a `psa_status_t`. There are no exceptions, no errno, no out-of-band failure channel. `PSA_SUCCESS` is zero; every error is a small negative integer with a name beginning `PSA_ERROR_`.

The error space is deliberately small and meaningful. `PSA_ERROR_NOT_SUPPORTED` means the mechanism was compiled out — a configuration problem, not a bug. `PSA_ERROR_NOT_PERMITTED` means the key's policy forbade the operation — you asked a verify-only key to sign. `PSA_ERROR_INVALID_ARGUMENT` means a parameter was malformed. `PSA_ERROR_BUFFER_TOO_SMALL` means your output buffer was undersized. `PSA_ERROR_BAD_STATE` means you called functions out of order — `update` before `setup`. `PSA_ERROR_INVALID_SIGNATURE` means a verification genuinely failed.

The 4.0 release made a decision here that you will feel. The PSA and Mbed TLS error spaces are now unified; mbedtls_xxx() functions can now return PSA_ERROR_xxx values, and there is no longer a distinction between "low-level" and "high-level" Mbed TLS error codes. Before 4.0 you juggled two error vocabularies — `MBEDTLS_ERR_*` from the protocol layers and `PSA_ERROR_*` from crypto. Now there is one. This will not affect most applications since the error values remain between -32767 and -1 as before.

Read errors as categories, not as individual codes. A status tells you *which kind of thing* went wrong — configuration, permission, argument, state, or genuine cryptographic failure — and the kind points you at the fix far faster than the specific number does. Chapter 55 returns to this as a debugging discipline.

> **Principle 13.** *A PSA status names a category of failure; the category, not the number, tells you whether to fix your build, your policy, your arguments, or your order of calls.*

---

## Part III — Configuration and Composition

### Chapter 14 — The Two Configuration Files

You do not configure Mbed TLS with command-line flags or a runtime API. You configure it by editing a header full of `#define`s, and that header is compiled into the library. The configuration *is* the build. Two keys not in the config might as well not exist; their code is not present in the binary.

After the 4.0 split there are **two** configuration files, mirroring the two components.

```
   ┌─────────────────────────────────┐   ┌──────────────────────────────────┐
   │  tf-psa-crypto/                  │   │  mbedtls_config.h                 │
   │  crypto_config.h                 │   │  (in Mbed TLS)                    │
   │                                  │   │                                   │
   │  PSA_WANT_*    (which crypto)    │   │  MBEDTLS_SSL_*  (TLS features)    │
   │  MBEDTLS_PSA_* (crypto internals)│   │  MBEDTLS_X509_* (cert features)   │
   │                                  │   │  MBEDTLS_*      (platform glue)   │
   │  → governs TF-PSA-Crypto         │   │  → governs the TLS/X.509 library  │
   └─────────────────────────────────┘   └──────────────────────────────────┘
```

The crypto configuration lives in TF-PSA-Crypto and is where you say which cryptographic mechanisms you want. The TLS/X.509 configuration lives in Mbed TLS and is where you turn protocol versions, cipher modes, and certificate features on and off. They are read at compile time; nothing is decided at runtime that was not first decided here.

The rule that traps everyone: enabling a TLS feature does **not** automatically enable the crypto it needs in the right place. A TLS 1.2 ECDHE-RSA-AES-GCM ciphersuite needs ECDH, RSA, AES, GCM, and a hash — and each of those is a separate crypto config switch. The build system and the dependency checker will tell you what is missing, but they tell you in the vocabulary of config symbols, so you must speak it.

> **Principle 14.** *The configuration header is the build; a mechanism you did not define does not exist in the binary, no matter what your source code calls.*

### Chapter 15 — WANT, BUILTIN, ACCEL

Three families of crypto config symbol look similar and do entirely different jobs. Confusing them is the single most common configuration mistake. Here is the distinction, sharply.

```
   PSA_WANT_xxx                 "I want this mechanism available."
        │                       ← THIS is the one you set.
        │
        ▼  the build system decides HOW to provide it:
   ┌────────────────────────┬───────────────────────────────┐
   ▼                        ▼
   MBEDTLS_PSA_ACCEL_xxx     MBEDTLS_PSA_BUILTIN_xxx
   "a hardware/plug-in       "the software implementation
    driver provides it"       is compiled in"
   (output of driver desc)    (auto-enabled when WANT is on
                               and ACCEL is off)
```

**`PSA_WANT_xxx`** is the *request*. It is the symbol you, the integrator, set. It says "this product needs SHA-256" or "this product needs ECDSA on secp256r1." It expresses intent, not mechanism.

**`MBEDTLS_PSA_ACCEL_xxx`** indicates whether a fully-featured, fallback-free transparent driver is available for that mechanism. It is one of the outputs of transpiling a driver description, alongside the glue code for calling the driver. You do not hand-write it; the driver tooling emits it.

**`MBEDTLS_PSA_BUILTIN_xxx`** indicates whether the software implementation is needed. It is enabled when `PSA_WANT_xxx` is enabled and `MBEDTLS_PSA_ACCEL_xxx` is disabled. In other words: you ask for a mechanism with WANT; if a hardware driver claims it via ACCEL, the built-in software is left out; otherwise BUILTIN turns on and the C implementation is compiled.

These symbols are not part of the public interface toward applications or drivers. You set `PSA_WANT`. The system computes the other two. The whole arrangement is the mechanism by which the *same* configuration yields a pure-software build on a desktop and a hardware-accelerated build on a chip, just by supplying a driver description — the application code and even the WANT flags are unchanged.

> **Principle 15.** *You set WANT to declare intent; ACCEL and BUILTIN are computed answers to "by hardware or by software?" — never set them by hand.*

### Chapter 16 — Composing a Build

A build is a closure: enable a feature and you must enable everything beneath it, transitively, or the build fails. Thinking of configuration as a dependency graph rather than a checklist is what separates a five-minute build from a five-hour one.

Work top-down. Start from what the *product* does, not from what crypto you find interesting.

```
   what the product does          what that requires
   ──────────────────────         ───────────────────────────────
   "TLS 1.3 client, ECDSA   ─►  MBEDTLS_SSL_PROTO_TLS1_3
    server certs, no PSK"        MBEDTLS_SSL_CLI_C
                                 PSA_WANT_ALG_ECDSA
                                 PSA_WANT_ECC_KEY_PAIR / PUBLIC_KEY
                                 PSA_WANT_ECC_FAMILY_SECP_R1
                                 PSA_WANT_ALG_SHA_256/384
                                 PSA_WANT_ALG_GCM, PSA_WANT_KEY_TYPE_AES
                                 PSA_WANT_ALG_HKDF_EXTRACT / _EXPAND
                                 MBEDTLS_X509_CRT_PARSE_C
                                 ... and an entropy/RNG source
```

The discipline is subtractive. Begin from a known-good full configuration, build it, then remove what the product does not use and rebuild until it breaks; the break tells you the floor. This is far safer than building up from nothing, because the dependencies are many and the checker only complains about the *first* missing piece it finds.

Two composition realities tutorials skip. First, `psa_crypto_init()` must be called once before any `psa_*` function — the library has an initialization step and most "nothing works" reports trace to its absence. Second, persistent keys need a storage backend and randomness needs an entropy source; neither appears in a naive feature list but both are mandatory for a working build (Chapters 23 and 45).

> **Principle 16.** *Compose subtractively from a working whole, not additively from nothing — the dependency graph punishes the optimist.*

### Chapter 17 — The Repository Split

Since 4.0, the codebase is two repositories, and you must hold both in your head. PSA Crypto functionality now resides in its own repository, Mbed-TLS/TF-PSA-Crypto; TLS and X.509 components remain in Mbed-TLS/mbedtls.

```
   github.com/Mbed-TLS/mbedtls          github.com/Mbed-TLS/TF-PSA-Crypto
   ┌──────────────────────────┐         ┌──────────────────────────────┐
   │  TLS  (library/ssl_*)     │         │  PSA Crypto API + core         │
   │  X.509 (library/x509_*)   │ ──────► │  bignum, ECC, RSA, AES, ...    │
   │  PK    (library/pk*)      │ depends │  the driver dispatch layer     │
   │  PKCS7                    │   on    │  software crypto + drivers     │
   │  mbedtls_config.h         │         │  crypto_config.h               │
   └──────────────────────────┘         └──────────────────────────────┘
```

The dependency is one-directional: Mbed TLS depends on TF-PSA-Crypto, never the reverse. The crypto component knows nothing of TLS. This mirrors the mental model of Chapter 4 — TLS is a client of crypto — now enforced at the level of source repositories.

The practical packaging: Mbed TLS 4.0.0 includes TF-PSA-Crypto 1.0.0 as a subtree in the release tarball and as a git submodule in the source tree, and can only be built with that bundled version. You do not pick versions independently. A given Mbed TLS release pins exactly one TF-PSA-Crypto release; later pairings continued the pattern (Mbed TLS 4.1.0 includes TF-PSA-Crypto 1.1.0). When you clone for development you must initialize submodules, or the crypto half is simply absent and the build cannot find `psa/crypto.h`.

If you only need cryptography and no TLS — a great many embedded products are in exactly this position — you can take TF-PSA-Crypto alone. That is the cleanest expression of the split: the crypto stands without the protocol, but the protocol cannot stand without the crypto.

> **Principle 17.** *Crypto stands alone; TLS does not — the repository split makes the one-way dependency a fact of the filesystem.*

### Chapter 18 — Headers and Namespaces

Two header namespaces, two function-name prefixes, and knowing which is which tells you instantly which layer you are calling and which paradigm you are in.

| Prefix | Header root | Layer | Paradigm |
|--------|-------------|-------|----------|
| `psa_` | `psa/crypto.h` | PSA Crypto | key by reference |
| `mbedtls_ssl_` | `mbedtls/ssl.h` | TLS | protocol |
| `mbedtls_x509_` | `mbedtls/x509*.h` | certificates | protocol |
| `mbedtls_pk_` | `mbedtls/pk.h` | public-key shim | thin over PSA |
| `mbedtls_` (crypto) | `mbedtls/*.h` | legacy crypto | key by value — *deprecated* |

The single most useful reading skill: when you see `psa_` you are in the new world — keys are IDs, no RNG is passed, errors are `psa_status_t`. When you see a *legacy* crypto call like `mbedtls_rsa_pkcs1_sign` or `mbedtls_aes_crypt_cbc`, you are looking at the old key-by-value world, and in 4.0 much of it is gone or wrapped. When you see `mbedtls_ssl_` or `mbedtls_x509_`, you are in the protocol layer, which is alive and well and now sits on PSA underneath.

Include `psa/crypto.h` for all cryptography. Include `mbedtls/ssl.h` and the X.509 headers for the protocol. You will rarely include the individual legacy crypto headers in new code, and when a tutorial tells you to `#include "mbedtls/rsa.h"` and operate on an `mbedtls_rsa_context`, that is your signal the tutorial predates the paradigm you are now in.

> **Principle 18.** *The prefix tells you the era — `psa_` is the present, legacy `mbedtls_` crypto is the past the library is leaving behind.*

---

## Part IV — Mechanism and Internals

### Chapter 19 — The Dispatch Layer

Here is the secret of PSA — the mechanism that makes the whole key-by-reference promise real. Mbed TLS contains a **driver dispatch layer**, also called the **driver wrapper layer**, and every cryptographic operation passes through it.

When your code calls `psa_sign_message(key, alg, ...)`, that call does not go straight to an RSA or ECDSA routine. It enters the dispatch layer, which asks: *who should do this work?* It looks at the key's location and the operation's parameters and routes accordingly.

```
        psa_sign_message(key, alg, msg, ...)
                       │
                       ▼
        ┌──────────────────────────────────┐
        │      DRIVER DISPATCH LAYER          │
        │  inspect key lifetime + parameters  │
        └───────┬──────────────┬─────────────┘
                │              │
   location is  │              │  location is
   default      │              │  a secure element
                ▼              ▼
   parameters match an    ┌──────────────────┐
   accelerator?           │ OPAQUE DRIVER     │
   ┌──────┴───────┐       │ (dispatch by      │
   yes           no       │  location)        │
   ▼             ▼        └──────────────────┘
 TRANSPARENT   BUILT-IN
 DRIVER        SOFTWARE
 (dispatch by  implementation
  parameters)
```

The dispatch is two-pronged. For ordinary keys whose material is available in cleartext, the layer dispatches on **parameters** — algorithm, key type, size — to a transparent driver if one covers that combination, else to the built-in software. For keys living in a secure element, the layer dispatches on **location** to the opaque driver registered for that location.

This is why the application code does not change when a key moves into hardware: the *decision* about who executes the operation is made here, below the API, at every call. The dispatch layer is the join between the stable interface above and the variable implementation below. Everything in the next two chapters is about its two kinds of driver.

> **Principle 19.** *Every crypto call is routed, not hardwired; the dispatch layer is where "who does the work" is decided, and it is decided fresh every time.*

### Chapter 20 — Transparent Drivers

A **transparent driver** implements cryptographic operations on keys that are provided in cleartext at the beginning of each operation. They are typically hardware accelerators, though they can also be pure-software plug-ins.

The defining trait is in the name. The driver is *transparent* because the key material passes through it in the clear — the driver sees the bytes. It exists not to hide the key but to do the math faster, or in silicon, or in a separately-certified implementation. When a transparent driver is available for a particular combination of parameters (algorithm, key type, size), it is used instead of the default software implementation.

Dispatch is by **parameters**, not by key location. The layer asks "is there a transparent driver that handles AES-GCM with a 256-bit key?" If yes, that driver runs; if no, the built-in software runs. A driver may also claim a mechanism only *partially* and fall back to software for the cases it does not cover.

Transparent drivers can also be pure software distributed as plug-ins — an alternative implementation with different performance characteristics, or a separately certified one. The driver model does not assume hardware; it assumes *replaceability*. A vendor who has had their AES core certified can drop it in as a transparent driver and inherit the entire PSA surface above it unchanged.

A driver is declared by a **driver description** — a JSON file listing the entry points it implements (the sample files are `mbedtls_test_transparent_driver.json` and the opaque equivalent). The build tooling transpiles that description into glue code and the `MBEDTLS_PSA_ACCEL_xxx` symbols of Chapter 15. The driver itself is a set of C functions matching documented entry-point signatures.

> **Principle 20.** *A transparent driver makes the same operation faster, not safer — the key still passes through it in the clear.*

### Chapter 21 — Opaque Drivers

An **opaque driver** is the other half of the duality, and the one that delivers the security promise. Opaque drivers implement cryptographic operations on keys that can only be used inside a protected environment — a secure element, a hardware security module, a smartcard, a secure enclave.

The defining trait, again in the name: the driver is *opaque* because the key material never crosses out of the protected boundary. For keys in a location managed by an opaque driver, only the secure element has access to the key material and can perform operations on the key, while the core only manipulates a *wrapped* form of the key or an *identifier* of the key. Your application holds a reference; the dispatch layer holds a wrapped blob; only the silicon holds the secret.

Dispatch is by **location**. An opaque driver is invoked for the specific key location that the driver is registered for; the dispatch is based on the key's lifetime. This is the payoff of Chapter 9: the location field of the lifetime is precisely the routing key that sends an operation into the secure element.

```
   TRANSPARENT                         OPAQUE
   ───────────                         ──────
   dispatch by parameters              dispatch by key location
   key in cleartext to driver          key never leaves the boundary
   accelerates math                    protects the secret
   "do this faster"                    "do this where I cannot reach"
   fallback to software possible       no fallback — the key is in there
```

There is a subtlety with multi-input operations. For key derivation, the involvement of an opaque driver cannot be determined when the operation is set up, because `psa_key_derivation_setup()` does not name the key. The core decides whether to dispatch to a driver based on the location associated with the secret input step `PSA_KEY_DERIVATION_INPUT_SECRET`. Dispatch can be deferred until the secret arrives.

> **Principle 21.** *An opaque driver hides the key; dispatch by location is the door, and the secret never walks back through it.*

### Chapter 22 — The Key Store and Slots

Between your `psa_key_id_t` and the key's material sits the **key store** — the subsystem that owns slots, tracks attributes, and maps identifiers to material. You never touch it directly, but its limits shape your design.

A volatile key occupies a **slot** in RAM for its lifetime. There is a finite number of slots, and that number is a build-time constant. Create more simultaneous volatile keys than there are slots and creation fails with a resource error. This is the embedded reality behind the elegant abstraction: the key store is not an infinite dictionary; it is a fixed array sized at compile time, and you must budget for the peak number of keys live at once.

The discipline that follows is symmetry of creation and destruction. There must be a matching call to `psa_destroy_key()` for each successful call that creates a volatile key. A key not destroyed is a slot leaked, and a leaked slot is gone until reset. Treat key creation like a malloc whose free you must not forget — except the pool is far smaller than a heap and exhaustion is far more likely.

For persistent keys, the slot in RAM is a cache; the authoritative copy lives in storage (Chapter 23). The store loads a persistent key into a slot on use and can evict it, so the identifier outlives any particular slot occupancy. The identifier is the stable name; the slot is a transient binding.

> **Principle 22.** *Slots are a fixed pool, not a heap — budget your peak live keys at compile time and destroy every volatile key you create.*

### Chapter 23 — Persistent Storage

A persistent key must be written somewhere that survives a power cycle. PSA does not assume a filesystem; it assumes a **storage interface** that you, or your platform, provide. This is the seam where the crypto subsystem meets the device's flash.

On a rich platform the default implementation writes each persistent key to a file. On a bare-metal device there is no filesystem, so the storage operations are routed to the PSA Secure Storage APIs — Internal Trusted Storage (ITS) for material that must stay on-chip, Protected Storage (PS) for material that may live in external flash with cryptographic protection. These are two of the four doors of Chapter 6, and here is where the Crypto door leans on the Storage door.

```
   psa_import_key(..., lifetime = PERSISTENT, id = 42)
                       │
                       ▼
   key store writes the key through the storage backend:
   ┌──────────────────────────────────────────────────┐
   │  rich platform → a file on disk                     │
   │  bare metal    → PSA ITS / PS (on TF-M, the RoT)    │
   │  secure element→ stays in the element (opaque)      │
   └──────────────────────────────────────────────────┘
```

The reality tutorials skip: persistent keys do not work until a storage backend exists. A desktop build gives you the file-based default and persistence "just works," which lulls you. Move to a microcontroller and the same code fails to persist anything until you wire up ITS/PS — and on a device without TF-M, you must supply that implementation yourself. The abstraction is clean; the obligation is real.

Note also that an opaque-driver key is "persistent" in a third sense — it is stored *inside the secure element*, and the storage backend only holds the wrapper or the reference, never the secret. Three storage destinations, one identifier model.

> **Principle 23.** *Persistence is a backend you must provide, not a guarantee you inherit; on bare metal, no storage means no persistent keys.*

### Chapter 24 — The Multipart State Machine

The universal lifecycle of a streaming operation is a small state machine, identical across hash, MAC, cipher, AEAD, and key derivation. Learn it once; it is the shape of every multipart family.

```
        setup ──────► update ──────► finish ──► (terminal)
          │             │  ▲             │
          │             └──┘             │
          │           (repeat)           │
          ▼                              ▼
        abort ◄──────────────────────────  (on any error)
          │
          ▼
       (terminal — operation object reusable)
```

You call a `_setup` function, which binds the operation object to an algorithm (and, where relevant, a key). You call `_update` zero or more times, feeding chunks of input. You call `_finish` to produce the result — or `_verify` to check one. At any point, or on any error, you call `_abort` to release resources.

Two rules are load-bearing. First, **the operation object owns resources** — a hardware context, a partial state — and leaving it without reaching `finish` or `abort` leaks them, exactly as with key slots. Always `abort` on the error path. Second, **the state machine is strict**: `update` before `setup`, or `finish` after `finish`, returns `PSA_ERROR_BAD_STATE`. The error space (Chapter 13) has a category dedicated to getting this order wrong.

The reason multipart exists at all is the embedded constraint: a device cannot hold a multi-megabyte firmware image in RAM to hash it, so it streams the image through `update` a block at a time. Single-shot functions are the convenience for data that fits; multipart is the necessity for data that does not.

> **Principle 24.** *Setup, update, finish, abort — one state machine underlies every streaming operation; reach a terminal state on every path or leak the context.*

### Chapter 25 — Randomness

Cryptography is only as strong as its randomness, and on an embedded device good randomness is the scarcest resource of all. PSA's design around this is one of the most consequential changes the 4.0 release made visible.

Internally, randomness flows from an **entropy source** into a **deterministic random bit generator (DRBG)**, which stretches a small amount of true entropy into the stream of random bytes the crypto needs. The entropy source is hardware-specific — a ring oscillator, a dedicated TRNG peripheral, analog noise. The DRBG (typically CTR_DRBG or HMAC_DRBG) is portable software seeded from that source.

```
   hardware entropy source   ──►  DRBG (CTR/HMAC)  ──►  random bytes
   (TRNG, noise, oscillator)      seed + reseed         to all crypto
        │                                                    │
        └── you must provide this on bare metal              └── psa_generate_random()
            (no OS = no /dev/urandom)                             and every key/nonce
```

Here is the 4.0 change you will feel in every signature. All API functions now use the PSA random generator (`psa_generate_random` internally) and, as a consequence, functions no longer take RNG parameters. The old world threaded an `f_rng`/`p_rng` callback pair through nearly every signing and key-generation call. That is gone. Randomness is now an ambient service of the initialized crypto subsystem, configured once, not a parameter you pass forever.

The obligation this creates: because randomness is now centralized, you must wire a real entropy source into that central service before any key generation or signing is secure. On a desktop the default uses the OS. On bare metal there is no OS, and a build that compiles and runs can still be catastrophically insecure if its entropy source is a stub. Chapter 45 returns to this; for now, hold that randomness moved from a parameter to a configured service.

> **Principle 25.** *Randomness is now an ambient service, not a parameter — which means it is configured once and, if you forget, insecure everywhere at once.*

---

## Part V — The Cryptography API in Depth

### Chapter 26 — Hashing

A hash is the simplest operation family and therefore the right place to internalize the patterns that recur everywhere else. A hash takes a message of any length and produces a fixed-length fingerprint, with no key involved.

Single-shot, when the whole message fits in memory:

```c
uint8_t hash[PSA_HASH_LENGTH(PSA_ALG_SHA_256)];
size_t hash_len;
psa_status_t status = psa_hash_compute(
        PSA_ALG_SHA_256,        // the algorithm, a structured integer (Ch 11)
        message, message_len,   // input
        hash, sizeof(hash),     // output buffer + its size
        &hash_len);             // actual bytes written
```

Note the buffer-size macro. `PSA_HASH_LENGTH(alg)` tells you, at compile time, how big the output of a given hash is. The API is studded with these `PSA_xxx_LENGTH` and `PSA_xxx_SIZE` macros, and you should use them to size every buffer rather than hard-coding 32. They keep your code correct when the algorithm changes.

Multipart, when the message is streamed (Chapter 24's state machine in concrete form):

```c
psa_hash_operation_t op = PSA_HASH_OPERATION_INIT;  // always zero-init
psa_hash_setup(&op, PSA_ALG_SHA_256);
psa_hash_update(&op, chunk1, len1);
psa_hash_update(&op, chunk2, len2);
psa_hash_finish(&op, hash, sizeof(hash), &hash_len);
// on any error path: psa_hash_abort(&op);
```

There is also `psa_hash_verify`, the compute/verify symmetry of Chapter 12: it recomputes and compares in constant time, which is the correct way to check a hash — never `memcmp` two digests when one is secret-dependent. The initializer macro `PSA_HASH_OPERATION_INIT` (or zeroing the struct) is mandatory; an operation object used before initialization is undefined.

> **Principle 26.** *Size every buffer with the API's length macros, never a literal — the macro stays correct when the algorithm does not.*

### Chapter 27 — Message Authentication

A MAC proves that a message came from someone holding a shared symmetric key and was not altered. It is a hash with a key — and the key-by-reference model now governs it.

```c
psa_key_attributes_t attr = PSA_KEY_ATTRIBUTES_INIT;
psa_set_key_type(&attr, PSA_KEY_TYPE_HMAC);
psa_set_key_usage_flags(&attr, PSA_KEY_USAGE_SIGN_MESSAGE | PSA_KEY_USAGE_VERIFY_MESSAGE);
psa_set_key_algorithm(&attr, PSA_ALG_HMAC(PSA_ALG_SHA_256));  // permitted algorithm
psa_key_id_t key;
psa_import_key(&attr, secret, secret_len, &key);

uint8_t mac[PSA_MAC_LENGTH(PSA_KEY_TYPE_HMAC, 256, PSA_ALG_HMAC(PSA_ALG_SHA_256))];
size_t mac_len;
psa_mac_compute(key, PSA_ALG_HMAC(PSA_ALG_SHA_256),
                message, message_len, mac, sizeof(mac), &mac_len);
```

Three things to notice carry forward to every keyed operation. First, the algorithm appears twice: once in the key's *policy* (the permitted algorithm) and once in the *operation* (the algorithm to use). They must be compatible, or the policy refuses the operation with `PSA_ERROR_NOT_PERMITTED`. Second, the usage flags must include the operation you are about to perform — `SIGN_MESSAGE` to produce a MAC, `VERIFY_MESSAGE` to check one. Third, the algorithm is the nested macro of Chapter 11: HMAC built over SHA-256.

To check a MAC, use `psa_mac_verify`, not a manual comparison. It compares in constant time, which matters because a non-constant-time comparison of a MAC is a textbook timing oracle — an attacker measures how long the rejection takes and recovers the MAC byte by byte. The verify function exists precisely so you cannot get this wrong.

> **Principle 27.** *The permitted algorithm in the policy and the algorithm in the operation must agree; the policy is the lock and the call must fit the key.*

### Chapter 28 — Unauthenticated Ciphers

A cipher encrypts data for confidentiality. The PSA cipher family handles *unauthenticated* encryption — modes like CBC and CTR that hide the data but do not detect tampering. The single most important thing to know about this family is when **not** to use it.

```c
// CBC needs an IV; PSA can generate it for you and prepend it to the setup.
psa_cipher_operation_t op = PSA_CIPHER_OPERATION_INIT;
psa_cipher_encrypt_setup(&op, key, PSA_ALG_CBC_NO_PADDING);
uint8_t iv[16]; size_t iv_len;
psa_cipher_generate_iv(&op, iv, sizeof(iv), &iv_len);  // fresh IV per message
psa_cipher_update(&op, pt, pt_len, ct, ct_cap, &ct_len);
psa_cipher_finish(&op, ct + ct_len, ct_cap - ct_len, &final_len);
```

The cipher family follows the same multipart state machine, with one addition: the **IV** (initialization vector). Most modes require a unique IV per message, and reusing an IV with the same key is a catastrophic break in several modes. Prefer `psa_cipher_generate_iv` to letting the system pick a fresh random IV rather than constructing one yourself, which is a common source of nonce-reuse bugs.

Now the warning. Unauthenticated encryption is almost never what an application wants. Ciphertext that can be silently altered enables padding-oracle and bit-flipping attacks; the famous classes of TLS vulnerabilities came from exactly this. Unless you are implementing a protocol that authenticates separately and you know precisely why, you want AEAD (the next chapter), which encrypts *and* authenticates in one operation. The cipher family exists because protocols sometimes need the raw primitive; your application code almost certainly should not reach for it.

> **Principle 28.** *Reach for AEAD by default; an unauthenticated cipher is a sharp tool for protocol implementers, and a foot-gun for everyone else.*

### Chapter 29 — AEAD

AEAD — Authenticated Encryption with Associated Data — is the operation almost every application actually wants. It provides confidentiality for the plaintext and integrity for both the plaintext and some additional cleartext "associated data," in a single operation. GCM and ChaCha20-Poly1305 are the common algorithms.

```c
// associated data (e.g. a header) is authenticated but not encrypted.
uint8_t ct[PSA_AEAD_ENCRYPT_OUTPUT_SIZE(PSA_KEY_TYPE_AES, PSA_ALG_GCM, pt_len)];
size_t ct_len;
psa_aead_encrypt(key, PSA_ALG_GCM,
                 nonce, nonce_len,        // unique per message — never reuse
                 aad, aad_len,            // authenticated, not encrypted
                 pt, pt_len,              // encrypted and authenticated
                 ct, sizeof(ct), &ct_len);// ciphertext WITH appended tag
```

Two concepts define AEAD. The **nonce** plays the IV's role and carries the IV's iron rule: a nonce must be unique per message under a given key. Nonce reuse in GCM is not a weakness; it is a total break that can leak the authentication key. The **associated data** is information you want authenticated but not hidden — a packet header, a message sequence number, a record type. It binds the ciphertext to its context so an attacker cannot splice a valid ciphertext into a different header.

Decryption is where the integrity guarantee bites. `psa_aead_decrypt` verifies the authentication tag *before* returning any plaintext, and if the tag is wrong it returns `PSA_ERROR_INVALID_SIGNATURE` and no data. You never get to act on unverified plaintext. This is the property the unauthenticated cipher family lacks and the reason AEAD is the default. The output-size macros (`PSA_AEAD_ENCRYPT_OUTPUT_SIZE`) account for the appended tag — use them.

> **Principle 29.** *AEAD gives you confidentiality and integrity in one call and refuses to hand back unverified plaintext — make it your default and never reuse a nonce.*

### Chapter 30 — Key Derivation

Key derivation turns one secret into many, or stretches a low-entropy input into a usable key. It is its own family with its own multipart shape, because it has *inputs of several kinds* rather than a single message.

```c
psa_key_derivation_operation_t kdf = PSA_KEY_DERIVATION_OPERATION_INIT;
psa_key_derivation_setup(&kdf, PSA_ALG_HKDF(PSA_ALG_SHA_256));
psa_key_derivation_input_bytes(&kdf, PSA_KEY_DERIVATION_INPUT_SALT, salt, salt_len);
psa_key_derivation_input_key (&kdf, PSA_KEY_DERIVATION_INPUT_SECRET, secret_key);
psa_key_derivation_input_bytes(&kdf, PSA_KEY_DERIVATION_INPUT_INFO, info, info_len);
// produce output as raw bytes...
psa_key_derivation_output_bytes(&kdf, out, out_len);
// ...or, better, directly as a new key that never appears in your memory:
psa_key_derivation_output_key(&derived_attr, &kdf, &derived_key);
psa_key_derivation_abort(&kdf);
```

The distinguishing feature is the **typed input steps**. Instead of one stream, a KDF takes a SALT, a SECRET, an INFO, each fed by its own call. The SECRET step is special: it can be supplied as raw bytes or as a *key*, and when it is a key in a secure element, that is what defers the opaque-driver dispatch decision of Chapter 21.

The most important design choice this family enables: derive *directly into a new key*. `psa_key_derivation_output_key` produces a fresh `psa_key_id_t` whose material never enters your application's memory — the derived secret goes straight into the key store. Compare `psa_key_derivation_output_bytes`, which hands you the raw bytes and breaks the key-by-reference discipline. Prefer the former wherever the derived value is itself a key, because it preserves the property that your code never holds the secret.

> **Principle 30.** *Derive into a key, not into a buffer — keeping the derived secret inside the key store preserves the one guarantee the whole model exists to provide.*

### Chapter 31 — Signatures: Hash vs Message

Asymmetric signatures are where newcomers most reliably trip, because PSA splits one familiar idea into two functions with two policies, and using the wrong one fails confusingly. The split is `sign_message`/`verify_message` versus `sign_hash`/`verify_hash`.

```
   psa_sign_message(key, alg, MESSAGE, ...)     psa_sign_hash(key, alg, HASH, ...)
            │                                              │
   the API hashes the message                   YOU hashed it already; you
   FOR you, then signs the hash                  pass the digest, the API signs it
            │                                              │
   needs PSA_KEY_USAGE_SIGN_MESSAGE             needs PSA_KEY_USAGE_SIGN_HASH
```

`psa_sign_message` takes the raw message and does the hashing internally before signing. This is what you want almost always: it is harder to misuse because the API controls the hashing. `psa_sign_hash` takes a digest you computed yourself and signs *that*. It exists for protocols — TLS among them — that must hash incrementally over data they have already streamed, or that compute the hash in a separate step for structural reasons.

The trap is the policy. The two operations need different usage flags: `SIGN_MESSAGE` versus `SIGN_HASH`. A key whose policy grants `SIGN_HASH` cannot be used with `psa_sign_message`, and the failure is `PSA_ERROR_NOT_PERMITTED` — which sends people hunting through their key material when the problem is one bit in the policy. Decide which operation your code performs, then grant exactly that flag.

There is a corresponding pair for verification — `verify_message` and `verify_hash` — and verification needs only the *public* key and the matching `VERIFY_*` flag. Verifying never requires the private key, which is the whole point of asymmetric cryptography and a fact the policy model enforces mechanically.

> **Principle 31.** *Sign the message unless a protocol forces you to sign a hash; whichever you choose, the key's usage flag must name that exact operation.*

### Chapter 32 — Asymmetric Encryption and Key Agreement

Two more asymmetric families round out the crypto surface, and they are routinely confused with each other and with signatures. Keep them distinct.

**Asymmetric encryption** (`psa_asymmetric_encrypt`/`decrypt`) encrypts a small payload to a public key so that only the private-key holder can read it — RSA-OAEP is the modern instance. It is limited to data smaller than the key, so in practice it encrypts a symmetric key, not bulk data. It is increasingly rare in new protocols, which prefer key agreement.

**Key agreement** (`psa_raw_key_agreement`, or agreement fed into a KDF) lets two parties derive a *shared secret* from one's private key and the other's public key, without ever transmitting the secret — ECDH is the ubiquitous instance. This is how modern TLS establishes session keys: each side contributes a public value, both compute the same shared secret, and neither sends it on the wire.

```
   ASYMMETRIC ENCRYPTION              KEY AGREEMENT (ECDH)
   ─────────────────────              ────────────────────
   A has B's public key               A has priv_A + B's pub_B
   A encrypts a secret TO B           B has priv_B + A's pub_A
   only B's private key decrypts      both compute the SAME shared secret
   secret travels (encrypted)         secret is NEVER transmitted
```

The security distinction is forward secrecy. With asymmetric encryption, if the long-term private key later leaks, every past message encrypted to it can be decrypted. With ephemeral key agreement, the shared secret was never sent and the ephemeral keys are discarded, so a later key compromise cannot retroactively decrypt past sessions. This is why every current TLS profile uses ephemeral ECDH and why asymmetric encryption is fading. Raw agreement output should be fed into a KDF (Chapter 30) rather than used as a key directly — the raw shared secret is not uniform and must be derived from.

> **Principle 32.** *Agreement derives a shared secret that never crosses the wire; encryption sends one that does — prefer agreement, and always run its output through a KDF.*

---

## Part VI — TLS and X.509

### Chapter 33 — The TLS Module

With the cryptographic atom understood, TLS becomes legible: it is a protocol that orchestrates the crypto operations of Part V into a secure channel. The Mbed TLS TLS module is a state machine that drives a handshake to agreement on keys, then encrypts a byte stream.

The module has three responsibilities, and separating them clarifies everything that follows. It performs the **handshake** — the negotiation that authenticates the parties and agrees on keys. It provides **record protection** — once keys exist, it encrypts and authenticates application data in records. And it manages **session state** — the parameters that let a connection resume without a full handshake.

Crucially, the TLS module does no cryptography itself. It calls down into the PSA Crypto API for every hash, every signature, every AEAD operation, exactly as your application would. The handshake's elaborate dance is, underneath, a sequence of `psa_*` calls (Chapter 39 makes this concrete). The TLS module is choreography; the crypto is the dance.

This is why the configuration of Chapter 16 is two-layered. Turning on a TLS feature in `mbedtls_config.h` declares the choreography you want; the steps it will perform must be separately available as crypto in `crypto_config.h`. A ciphersuite the protocol layer offers but the crypto layer cannot perform is a contradiction the build will reject.

> **Principle 33.** *TLS is choreography over the crypto primitives — it negotiates and sequences, but every cryptographic step is a call down into PSA.*

### Chapter 34 — Context and Configuration

The TLS module separates two objects, and the separation is the key to using it without leaking memory or duplicating setup. There is the **configuration** (`mbedtls_ssl_config`) and the **context** (`mbedtls_ssl_context`). They are not the same, and conflating them is a classic error.

```
   mbedtls_ssl_config              mbedtls_ssl_context
   ──────────────────              ───────────────────
   SHARED, immutable-ish           PER-CONNECTION, mutable
   set up ONCE                     created PER handshake
   endpoint (client/server)        the live state machine
   allowed versions                current handshake step
   certificate chains / CA store   negotiated parameters
   verification policy             read/write buffers
        │                                │
        └──────── one config ───────────┘
                  drives MANY contexts
```

The **config** holds the durable policy: am I a client or server, which TLS versions do I allow, which CA certificates do I trust, what is my own certificate and key, how strictly do I verify the peer. You build it once. A server handling thousands of connections builds *one* config and binds every connection's context to it.

The **context** is one connection's live state: where it is in the handshake, what was negotiated, its I/O buffers. You create one per connection with `mbedtls_ssl_setup`, which links it to the config, run the handshake on it, exchange data, then free it.

The reason for the split is efficiency and correctness on a server: shared policy lives in one place, per-connection state lives in many. Set up the expensive, shared things — parsing the CA store, loading your certificate — once in the config; pay only the cheap per-connection cost in the context. Getting this wrong (rebuilding the config per connection, or sharing a context across connections) is a performance bug or a correctness bug respectively.

> **Principle 34.** *Configure once, contextualize per connection — shared policy in the config, live state in the context, and never the two confused.*

### Chapter 35 — The Handshake Lifecycle

The handshake is the universal lifecycle of TLS, and like the multipart crypto state machine it is the same shape every time. Mbed TLS exposes it through one call you drive to completion.

```c
int ret;
while ((ret = mbedtls_ssl_handshake(&ssl)) != 0) {
    if (ret == MBEDTLS_ERR_SSL_WANT_READ || ret == MBEDTLS_ERR_SSL_WANT_WRITE)
        continue;                       // non-blocking I/O: try again later
    if (ret == MBEDTLS_ERR_SSL_HANDSHAKE_FAILED) { /* handle */ break; }
    /* other negative: a real error — inspect it */ break;
}
```

The handshake's job is to reach three agreements: *who are you* (authentication, via certificates), *what shall we speak* (negotiation of version and ciphersuite), and *what is our key* (key establishment, via ephemeral key agreement). When the loop returns zero, all three are settled and the connection is ready for `mbedtls_ssl_read` and `mbedtls_ssl_write`.

The `WANT_READ`/`WANT_WRITE` returns are not errors; they are the protocol telling you it needs more bytes from the network or needs to send some, which matters on non-blocking sockets and on bare-metal event loops. You supply I/O callbacks with `mbedtls_ssl_set_bio`, and the handshake calls them as it needs the network — the TLS engine never touches a socket directly, which is what lets it run identically over TCP, over DTLS, or over a serial link.

After the handshake, record protection takes over transparently: `mbedtls_ssl_write` encrypts and authenticates each record with the negotiated AEAD key (a `psa_aead_*` call underneath), and `mbedtls_ssl_read` reverses it. The complexity is all in the handshake; the steady state is a pipe.

> **Principle 35.** *Drive the handshake to zero in a loop; WANT_READ and WANT_WRITE are requests for I/O, not failures, and the engine touches the network only through your callbacks.*

### Chapter 36 — TLS 1.3 vs TLS 1.2

The library supports two live protocol versions, and they differ enough that treating them as one is a mistake. TLS 1.3 is the present; TLS 1.2 is the still-necessary past.

| Aspect | TLS 1.2 | TLS 1.3 |
|--------|---------|---------|
| Handshake round-trips | 2 | 1 (0-RTT possible) |
| Key exchange | RSA *or* (EC)DHE | (EC)DHE only — always forward-secret |
| Cipher modes | many, incl. CBC | AEAD only |
| Negotiation | in cleartext | most of it encrypted |
| Cryptographic hygiene | many footguns | footguns removed by design |

The trend is unmistakable: TLS 1.3 removed the dangerous options. It mandates forward-secret key agreement, mandates AEAD, and encrypts most of the handshake. Many of the historic TLS vulnerabilities targeted options that 1.3 simply deleted — static RSA key exchange, CBC modes, renegotiation. If you can require 1.3, you inherit a safer protocol for free.

The practical guidance: enable TLS 1.3 (`MBEDTLS_SSL_PROTO_TLS1_3`) and prefer it; enable 1.2 (`MBEDTLS_SSL_PROTO_TLS1_2`) only if you must interoperate with peers that lack 1.3. Each version you enable is code you ship and attack surface you carry, so enable the minimum your peers require. A device talking only to your own modern servers needs 1.3 alone, which is both smaller and safer.

> **Principle 36.** *Require TLS 1.3 where you can; it is smaller, faster, and safe by deletion — every 1.2 option you keep is a footgun you chose to carry.*

### Chapter 37 — X.509 Certificates

A certificate answers "is this public key really theirs?" by having a trusted authority sign the binding of an identity to a key. X.509 is the format of that signed binding, and Mbed TLS's X.509 module parses, builds, and — most importantly — *verifies* certificate chains.

Verification is the part that matters and the part most often botched. A certificate is trustworthy only if it chains, by valid signatures, up to a certificate you already trust — a root in your CA store. The module walks that chain: each certificate's signature is checked against its issuer's public key, up to a self-signed root that must be present in your trusted set.

```
   end-entity cert (the server)
        │  signed by
        ▼
   intermediate CA cert
        │  signed by
        ▼
   root CA cert  ──────────►  must already be in YOUR trust store
   (self-signed)              — this is the anchor; trust starts here
```

Beyond the chain of signatures, verification checks expiry dates, the name (does the certificate's subject match the host you meant to reach?), key usage constraints, and revocation where configured. Skipping any of these is a real vulnerability: a valid signature on a certificate for the *wrong name* is exactly what a man-in-the-middle presents.

The trust store is yours to provision. On a device you ship the specific roots you trust — often just one or a handful, not the hundreds a browser carries. This is a security advantage: a device that trusts only your CA cannot be fooled by a certificate from any other CA, however legitimate that CA is for the rest of the world. Configure verification to be strict (`MBEDTLS_SSL_VERIFY_REQUIRED`); a device that connects despite a verification failure has thrown away the entire point of TLS.

> **Principle 37.** *A certificate is worthless without a verified chain to a root you already trust; a valid signature on the wrong name is the attack, not the exception.*

### Chapter 38 — The PK Layer

The PK ("public key") layer is a small abstraction that once did real work and, in the 4.0 world, has become a thin shim. Understanding what it *was* explains what it now *is*.

Historically, PK was a uniform front-end over the different public-key algorithms — RSA, ECDSA, EdDSA — so that TLS and X.509 could handle "a key" without branching on its type. An `mbedtls_pk_context` wrapped whichever underlying key it held, and `mbedtls_pk_sign`/`verify` dispatched to the right algorithm. It was the original key-type abstraction, predating PSA.

PSA Crypto subsumed this role. Now the PK, X.509, PKCS7 and TLS modules always use the PSA crypto interfaces underneath. PK survives mainly as a compatibility and parsing convenience — it still parses PEM and DER key files into something usable, and it bridges to PSA key identifiers — but the cryptographic work it appears to do is now delegated downward. It is a façade kept for the code and file formats built around it, sitting in front of the PSA machinery that actually signs.

The lesson for new code: reach for PSA key identifiers directly rather than building your design around `mbedtls_pk_context`, unless you are parsing key files or interfacing with X.509 APIs that still speak PK. When a tutorial centers `mbedtls_pk_*` as the way to do public-key crypto, that is a 3.x-era view; the 4.x way is `psa_key_id_t` and `psa_sign_message`, with PK relegated to the loading dock.

> **Principle 38.** *PK is now a façade over PSA, not a crypto engine — use it to parse keys, not to design around.*

### Chapter 39 — How TLS Consumes PSA

Make the abstraction concrete: when does TLS actually call into PSA Crypto? Tracing one handshake dissolves the mystery of how the protocol layer and the crypto layer connect.

```
   TLS 1.3 handshake step           PSA call underneath
   ──────────────────────           ───────────────────
   transcript hashing          ──►  psa_hash_setup / update / finish
   client/server key share     ──►  psa_generate_key (ephemeral ECDH)
   shared secret               ──►  psa_raw_key_agreement
   key schedule (derive keys)  ──►  psa_key_derivation_* (HKDF)
   CertificateVerify (sign)    ──►  psa_sign_hash   (note: hash, not message)
   CertificateVerify (check)   ──►  psa_verify_hash
   record protection           ──►  psa_aead_encrypt / decrypt
```

Every cryptographic act of the handshake is, underneath, one of the operations from Part V. The transcript is hashed with the hash family. The ephemeral keys are generated and combined with key agreement. The session keys are derived with HKDF. The certificate is signed and verified with the signature family — and note it is `sign_hash`, the protocol case from Chapter 31, because TLS hashes the transcript incrementally and signs the digest. Records are protected with AEAD.

This is also where the security boundary becomes possible. Because TLS reaches the crypto only through PSA key identifiers and `psa_*` calls, a device can place its long-term private key in a secure element (Chapter 21) and TLS will sign with it through the opaque driver — the handshake code is identical whether the key is in RAM or in tamper-resistant silicon. The protocol layer's ignorance of where the key lives is exactly what makes hardware-backed TLS a configuration choice rather than a rewrite.

> **Principle 39.** *Trace any handshake and you find Part V underneath; because TLS speaks only PSA, the same protocol code drives a software key or a key it can never touch.*

---

## Part VII — The Secure Boundary

### Chapter 40 — Secure and Non-Secure Worlds

The "A" in PSA stands for Architecture, and the architecture's central idea is a boundary that splits the device into two worlds. Understanding this boundary is what turns "PSA Crypto is an API" into "PSA Crypto is the visible face of a security model."

A PSA device divides into a **Secure Processing Environment (SPE)** and a **Non-Secure Processing Environment (NSPE)**, isolated by hardware. The chip's Root of Trust is a secure processing environment that acts as the trust anchor for the device — typically built by combining trusted hardware (crypto accelerators, private key stores) with trusted firmware hidden from the main software by hardware isolation.

```
   ┌──────────────── NSPE ────────────────┐   ┌──────── SPE ─────────┐
   │  Non-Secure Processing Environment     │   │ Secure Processing    │
   │                                        │   │ Environment (RoT)    │
   │   your application                     │   │                      │
   │   TLS, business logic                  │   │  ┌────────────────┐  │
   │   PSA Crypto CLIENT  ─────call────────►│───┼─►│ PSA Crypto       │  │
   │   (holds key IDs only)                 │   │  │ SERVICE          │  │
   │                                        │   │  │ key material ▓▓  │  │
   └────────────────────────────────────────┘   │  └────────────────┘  │
            hardware isolation boundary           └──────────────────────┘
```

The application — your code, your TLS, your business logic — runs in the NSPE. The cryptographic keys and the operations on them run in the SPE. Between them is a hardware-enforced wall the application cannot climb. The application calls across the wall with key *identifiers*; the secret material lives on the far side and never crosses back.

Now the key-by-reference duality of Chapter 3 reveals its deepest purpose. It was never only about convenience. It was designed so that the application and the keys could live in *different security domains*. A `psa_key_id_t` is a token you can pass across a hardware boundary; key bytes are not. The entire API was shaped so that a compromised application — the most likely thing to be compromised, being the largest and most exposed — still cannot read the keys, because it only ever held their names.

> **Principle 40.** *The key handle exists so the key can live on the other side of a wall; key-by-reference is what makes a compromised application survivable.*

### Chapter 41 — The Crypto Client Build

The boundary of Chapter 40 is not just an idea; it is a build configuration. Mbed TLS can be compiled as a **crypto client** that holds no key material and performs no crypto locally, delegating everything across the boundary to a service.

This is the meaning of two configuration symbols that look like minor variants and are in fact opposite roles. `MBEDTLS_PSA_CRYPTO_C` builds the full crypto *implementation* — the code that actually performs operations. `MBEDTLS_PSA_CRYPTO_CLIENT` builds only the *client* side — the code that marshals a `psa_*` call across the boundary to a separate service that does the work.

```
   FULL implementation              CLIENT-ONLY
   MBEDTLS_PSA_CRYPTO_C             MBEDTLS_PSA_CRYPTO_CLIENT (and not _C)
   ───────────────────             ──────────────────────────────
   crypto runs here                crypto runs ELSEWHERE (the SPE service)
   keys live here                  this side holds only identifiers
   the desktop / simple case       the secure-partition case
```

In a client-only build — `MBEDTLS_PSA_CRYPTO_CLIENT` without `MBEDTLS_PSA_CRYPTO_C` — the library does not automatically enable local crypto when the corresponding PSA mechanism is requested, because the server provides the crypto. The NSPE binary becomes small: it contains the marshalling and the protocol logic, but not AES, not RSA, not the bignum code. All of that lives once, in the trusted service.

The beauty of the arrangement, and the reason it matters to you even if you never build a client: your *application source does not change* between a full build and a client build. The same `psa_sign_message(key, ...)` either runs locally or marshals across the boundary, decided entirely by configuration. The API was designed to be relocatable, and the crypto-client build is that design made real.

> **Principle 41.** *The same PSA call runs locally or crosses a security boundary, chosen at build time; your application code cannot tell and does not need to.*

### Chapter 42 — TF-M and the Root of Trust

On the far side of the boundary, something must implement the secure service. On Arm microcontrollers that something is most often **TF-M** — Trusted Firmware-M — the reference firmware for the Secure Processing Environment. Knowing where Mbed TLS ends and TF-M begins prevents a great deal of confusion about "which library does what."

The PSA Root of Trust provides a small set of security services — crypto, secure storage, attestation, trusted boot — that must be isolated from the main application. TF-M is the open-source firmware that implements the PSA-RoT on a device: it runs in the SPE, holds the keys, and answers PSA Functional API calls coming from the NSPE. Chips that run TF-M are automatically compliant with the PSA Certified APIs, since TF-M is a reference implementation.

```
   ┌────────────── a PSA microcontroller ──────────────┐
   │  NSPE                          SPE                  │
   │  ┌─────────────┐               ┌────────────────┐   │
   │  │ app + TLS   │               │ TF-M            │   │
   │  │ (Mbed TLS   │── PSA calls ─►│  PSA-RoT        │   │
   │  │  as client) │               │  crypto/storage/│   │
   │  └─────────────┘               │  attestation    │   │
   │                                │  (uses TF-PSA-  │   │
   │                                │   Crypto inside)│   │
   │                                └────────────────┘   │
   └─────────────────────────────────────────────────────┘
```

Here is the part that surprises people: TF-M, inside the secure world, often *uses TF-PSA-Crypto itself* as its cryptographic engine. The same crypto library appears on both sides of the boundary in different roles — as a client in the NSPE, as the implementation inside the SPE service. Mbed TLS / TF-PSA-Crypto is the reference implementation of the Crypto API; TF-M is the firmware that hosts it as a service and adds the other RoT functions around it.

So the division of labor is clean once you see it: TF-PSA-Crypto provides the cryptography; TF-M provides the isolated environment and the non-crypto security services; the PSA Functional APIs are the contract between them and the application.

> **Principle 42.** *TF-M is the house, TF-PSA-Crypto is often the engine inside it — the same crypto can be the client in the open world and the implementation in the secure one.*

### Chapter 43 — The Sibling APIs

The Crypto API has three siblings behind the same boundary — Secure Storage, Attestation, Firmware Update — and although this manual is about crypto, a practitioner must know how crypto leans on and is leaned on by them. The doors of Chapter 6 are not independent; they cooperate.

**Secure Storage** is where persistent keys actually live on a real device (Chapter 23). It splits into Internal Trusted Storage, for the most sensitive data that must remain on-chip, and Protected Storage, which can use external flash with cryptographic protection. When you create a persistent PSA key on a PSA device, the Crypto service stores it through Secure Storage. Crypto is the storage API's biggest customer.

**Attestation** produces a signed token — an Entity Attestation Token — proving what firmware the device is running. It signs that token with a key held by the Crypto service: the Initial Attestation Key, used by the attestation service to sign the device's claims. Attestation is, underneath, a specialized signature operation. Crypto is what makes attestation's proof unforgeable.

**Firmware Update** installs and verifies new images. It verifies an image's signature before trusting it — again a Crypto operation — closing the loop: the device can only accept firmware signed by a key it trusts, and the verification runs in the Crypto service.

The pattern across all three: crypto is the load-bearing primitive. Storage protects secrets *with* crypto; attestation proves identity *with* crypto; update establishes trust in new code *with* crypto. The other three doors are applications of the first. This is why the Crypto API is the one this manual centers, and why mastering it is the prerequisite to the rest of PSA.

> **Principle 43.** *The other three PSA services are applications of crypto — storage, attestation, and update each reduce to "do a cryptographic operation in the trusted world."*

---

## Part VIII — Production

### Chapter 44 — Trimming the Footprint

A tutorial build of Mbed TLS is enormous by embedded standards. A production build must be trimmed until it fits the flash and RAM you have, and trimming is a skill, not an afterthought. This is the gap between "it compiles on my laptop" and "it ships on the device."

The footprint is dominated by which mechanisms you compiled in (Chapter 14). Each algorithm, each key type, each TLS feature is code. The discipline is to enable only what the product's actual peers and protocols require, and to verify it against measured size, not intuition.

```
   footprint reduction, in order of leverage
   ─────────────────────────────────────────
   1. Drop TLS versions you don't need      (1.2 OR 1.3, rarely both)
   2. Drop ciphersuites/curves/key types    (one curve, one AEAD often suffices)
   3. Drop X.509 features you don't use      (CRL, CSR writing, ...)
   4. Drop legacy/compat code paths
   5. Choose the smaller DRBG, tune buffers  (MBEDTLS_SSL_*_BUFFER_LEN)
   6. Offload to a transparent driver        (HW does the math; less SW code)
```

Two embedded-specific levers tutorials never mention. The TLS I/O buffers are sized by `MBEDTLS_SSL_IN_CONTENT_LEN` and `MBEDTLS_SSL_OUT_CONTENT_LEN`, and the default (16 KB each, the TLS record maximum) is often the largest single RAM cost; if your peers send small records, shrink them. And a hardware accelerator wired in as a transparent driver removes the *software* implementation of that mechanism from flash (via the ACCEL/BUILTIN logic of Chapter 15), so offloading saves code size as well as cycles.

Measure, do not guess. Build with map-file output, see what actually consumes flash, cut the largest unused contributors, rebuild. The dependency checker tells you when you have cut too far. Iterate down to the floor your product's requirements define.

> **Principle 44.** *Footprint is a budget you spend in config symbols; trim against a measured map file, not against intuition, and let hardware drivers reclaim flash as well as time.*

### Chapter 45 — Entropy on Bare Metal

This chapter is short and it is the most dangerous one in the manual, because the failure it describes is silent. On bare metal, a build with bad entropy compiles, runs, passes your functional tests, and is catastrophically insecure.

Recall Chapter 25: randomness is a configured service feeding a DRBG. The DRBG is portable software; the *entropy source* that seeds it is platform-specific. On a hosted OS the default draws from the system CSPRNG and you are fine. On a microcontroller there is no OS, so you must supply an entropy source — a hardware TRNG peripheral, accumulated from a noise source — and register it so the DRBG is seeded from real unpredictability.

```
   THE SILENT FAILURE
   ──────────────────
   stub entropy source  ──►  DRBG seeded with predictable/zero data
        │                         │
   code compiles, runs            every "random" key, nonce, ephemeral
   tests pass                     value is predictable to an attacker
        │                         │
   ▼                              ▼
   looks fine                     totally broken — and invisible
```

The keys you generate, the nonces you use, the ephemeral ECDH values in every TLS handshake all draw from this source. Seed it with a stub — a counter, a constant, an uninitialized buffer — and an attacker who knows the seed can reproduce every "secret" you ever generate. There is no functional symptom. The handshake completes; the data flows; the device is wide open.

The obligation is absolute: before any key generation, signing, or TLS handshake on a real device, confirm that a genuine hardware entropy source is wired into the DRBG, and confirm it under the conditions the device boots in (cold boot entropy is a known hazard). Test it adversarially, because nothing in the normal test path will reveal a weak source. This is the single most important production discipline in this manual.

> **Principle 45.** *Bad entropy is invisible and total — verify a real hardware source seeds the DRBG before you trust a single key, because nothing else will tell you.*

### Chapter 46 — Thread Safety

If more than one thread touches the crypto subsystem, you must know exactly what is and is not safe, because the safety is partial and the documentation is explicit that it is partial.

Mbed TLS guards its shared state with mutexes when `MBEDTLS_THREADING_C` is enabled and you provide the threading primitives for your platform (or use the pthread default). Without it, the library assumes single-threaded use and shared state is unprotected. So the first rule: multi-threaded crypto requires `MBEDTLS_THREADING_C` *and* a correct mutex implementation for your RTOS.

But enabling threading does not make everything concurrent. The PSA Crypto core implemented in Mbed TLS does not fully implement thread safety, and accelerated operations carry further restrictions. Hardware-backed drivers are frequently multi-thread capable but do not support preemption: the application is responsible for not calling a driver-accelerated PSA API under conditions that would preempt an already-running operation. In practice this means not calling crypto from an interrupt service routine, and for an RTOS, not calling accelerated functions from inside critical or atomic sections where the underlying mutex acquisition would fail.

```
   SAFE-ish                          UNSAFE
   ────────                          ──────
   distinct operations on distinct   same operation object from two threads
   keys, with THREADING_C            crypto from an ISR
   protecting the key store          accelerated crypto inside a critical section
                                     assuming full concurrency of the PSA core
```

The honest summary: treat the crypto subsystem as something to serialize access to, not something to call freely from anywhere. Design your system so cryptographic work happens on known threads at known times, not opportunistically from interrupt context. The partial thread-safety is a real constraint, and a race in a crypto core is the kind of bug that corrupts a key store and fails in ways you will not enjoy diagnosing.

> **Principle 46.** *The crypto core is only partially thread-safe; enable THREADING_C, serialize access, and never call crypto from an interrupt.*

### Chapter 47 — Side Channels

A cryptographic implementation can be mathematically perfect and still leak its secrets through *how long it takes* or *how much power it draws*. On an embedded device, where the attacker may hold the hardware, side channels are not theoretical — they are the threat the higher PSA certification levels exist to address.

The two families to know. **Timing side channels** leak through operations whose duration depends on secret data — a comparison that returns early on the first mismatched byte, a branch taken based on a key bit. Mbed TLS implements its sensitive operations in constant time for exactly this reason, and the API gives you constant-time tools (the `_verify` functions of Part V) so you do not reintroduce a leak. The rule for you: never compare a secret with `memcmp`, never branch on secret data, always use the provided verify functions.

**Physical side channels** — power analysis, electromagnetic emanation, fault injection — require the attacker's physical access and are addressed in hardware and in certified implementations. PSA-RoT assets such as cryptographic keys need protection from side-channel attacks at the higher certification levels, where a physical attacker using tools like a power-analysis rig is explicitly in scope. This is where opaque drivers and secure elements earn their place: the secret never enters the general-purpose core where it could be probed.

The recent past makes this concrete. The TF-PSA-Crypto 1.0.0 release fixed two side-channel vulnerabilities present in the prior LTS: a padding oracle through the timing of cipher error reporting, and a side channel in RSA key generation and operations. These are not exotic; they are exactly the timing leaks described above, found in shipped code. The lesson: side channels are a maintenance reality, which is why you track security releases (Chapter 48) rather than freezing a version forever.

> **Principle 47.** *Correct math leaks through time and power; use the constant-time verify functions, never branch on secrets, and push the highest-value keys into hardware that an oscilloscope cannot read.*

### Chapter 48 — The 4.0 Migration

If you maintain code written against Mbed TLS 3.x or earlier, the move to 4.0 is not a version bump — it is a paradigm migration, and pretending otherwise will cost you a week of confusion. This chapter names the breaking changes you will hit, in the order you will hit them.

The Mbed TLS 4.0.0 and TF-PSA-Crypto 1.0.0 releases include significant API changes that break backward compatibility and may require substantial updates to your codebase. The major ones:

| Change | What breaks | What to do |
|--------|-------------|------------|
| **Crypto split out** | `psa/crypto.h` not found | Initialize the TF-PSA-Crypto submodule; expect two config files |
| **RNG parameters removed** | every call passing `f_rng`/`p_rng` | Remove the RNG args; configure entropy once (Ch 25, 45) |
| **Error spaces unified** | code branching on `MBEDTLS_ERR_*` vs `PSA_ERROR_*` | `mbedtls_*` functions can now return `PSA_ERROR_*`; handle one space |
| **Legacy crypto deprecated** | `mbedtls_rsa_*`, `mbedtls_aes_*` direct use | Move to `psa_*` and key identifiers |
| **PK/X.509/TLS use PSA underneath** | code reaching into PK internals | Treat PK as a parsing façade (Ch 38) |
| **Some signatures changed** | e.g. `mbedtls_ssl_ticket_setup` now takes PSA alg/type/size | Follow the migration guide entry-by-entry |

Two of these dominate the work. The **RNG removal** touches nearly every signing and key-generation call site, because the old API threaded an RNG callback everywhere; the migration is mechanical but pervasive — delete the arguments, ensure entropy is configured centrally. The **error unification** means you can stop maintaining two parallel error vocabularies, which simplifies code but requires re-checking every place you matched on a specific error value.

Do not migrate by trial and error. The project ships migration guides — `docs/4.0-migration-guide.md` in Mbed TLS and the `1.0-migration-guide` in TF-PSA-Crypto — that enumerate the changes. Read them first, plan the mechanical sweeps (RNG arguments, header paths), then handle the genuine redesigns (key-by-value to key-by-reference) deliberately. And test thoroughly: the release notes themselves insist on it, because the surface that changed is large.

> **Principle 48.** *4.0 is a paradigm migration, not a version bump; sweep the mechanical changes — RNG arguments, headers, error matching — then redesign the key-by-value code the guide flags.*

### Chapter 49 — Certification

For many products, "it is secure" is not a claim you make but a claim a laboratory certifies. PSA Certified is the program that turns the architecture of Part VII into a badge, and knowing its shape tells you how much security engineering your product actually owes.

There are three evaluation levels, escalating in attacker capability. **Level 1** is a self-assessment against best-practice questionnaires. **Level 2** is a laboratory-led evaluation of the chip's PSA-RoT against a published Protection Profile, defending against scalable software attacks — roughly a 25-day evaluation. **Level 3** raises the attacker to "substantial" and brings physical attacks into scope: the PSA-RoT's keys must withstand side-channel attacks like power analysis. The level you need is dictated by your threat model and your market, not by ambition.

Distinct from security-level evaluation is **API compliance**: a separate badge stating that a device exposes the PSA Functional APIs correctly, verified by the open `psa-arch-tests` suite. To earn it a device must support the Crypto API, a Secure Storage service, and the Attestation API at minimum. Crucially, compliance with the PSA Certified APIs is not necessary to achieve PSA Certified security evaluation, and vice versa — they are separate axes. A chip running TF-M is automatically API-compliant, because TF-M is a reference implementation.

The practical takeaway for the Mbed TLS user: using a certified implementation or a certified chip lets you inherit security properties rather than prove them yourself, which is often the entire reason to choose a secure element and opaque drivers. The certification is a contract that someone competent evaluated the part of the system you most need to be right. Decide early which level your product needs, because it shapes the hardware you choose and the boundary you build.

> **Principle 49.** *Pick the certification level your threat model demands, not the highest available; certification lets you inherit security properties instead of proving them yourself.*

---

## Part IX — Tooling and Workflow

### Chapter 50 — Building

The day-to-day reality of Mbed TLS is a build system, and two paths through it dominate: CMake for integration and the in-tree make for development. Knowing which to reach for saves hours.

For a real project, **CMake** is the path. You add the library as a subdirectory or find it as a package, and you link your application against the produced targets. Because the crypto lives in a submodule since 4.0, the first ritual is fetching it:

```bash
git clone https://github.com/Mbed-TLS/mbedtls.git
cd mbedtls
git submodule update --init --recursive   # pulls TF-PSA-Crypto — skip this and psa/crypto.h is missing
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build .
```

The submodule step is the one newcomers forget, and its symptom — a missing `psa/crypto.h` — sends people searching for an install problem when the real cause is an uninitialized submodule (Chapter 17). For cross-compilation to a device, you point CMake at your toolchain file and supply your tailored config headers through the documented config-path variables.

The configuration is supplied not as flags but as the headers of Chapter 14. You either edit the in-tree `mbedtls_config.h` and `crypto_config.h`, or — better for a project — keep your own copies outside the tree and point the build at them, so a library update does not clobber your configuration. Treat your config headers as project source under version control, because they are the most important code you "write" against this library.

> **Principle 50.** *Initialize the submodule, supply your own config headers from outside the tree, and treat those headers as the most important source in your project.*

### Chapter 51 — The Config Tool

Editing a configuration header with hundreds of options by hand is tedious and error-prone. The project ships a tool for exactly this, and using it is faster and safer than a text editor.

`scripts/config.py` (and its predecessor shell script) reads and writes the configuration header programmatically. You can query, set, and unset individual options, and — most usefully — apply named *presets* that represent coherent starting points:

```bash
python scripts/config.py full          # enable a broad, sensible feature set
python scripts/config.py baremetal     # a configuration suited to no-OS targets
python scripts/config.py set MBEDTLS_SSL_PROTO_TLS1_3
python scripts/config.py unset MBEDTLS_SSL_PROTO_TLS1_2
python scripts/config.py get PSA_WANT_ALG_GCM
```

The presets matter because they encode the subtractive workflow of Chapter 16. Start from `full`, build it to confirm a working whole, then `unset` what your product does not use and rebuild until the dependency checker objects — that objection is your floor. The `baremetal` preset is a better starting point for embedded targets because it pre-disables the host-OS assumptions (filesystem, networking conveniences) that a microcontroller cannot satisfy.

The tool also keeps the two config files consistent in spirit, and it understands the dependency relationships well enough to avoid some invalid combinations. Prefer it to hand-editing not because hand-editing is forbidden, but because the tool makes the common operations atomic and reviewable — a `config.py` invocation in a build script is self-documenting in a way that a hand-tweaked header diff is not.

> **Principle 51.** *Drive configuration with config.py, not a text editor; start from a preset and subtract, and your build script documents your build.*

### Chapter 52 — Testing

The library's correctness rests on an enormous test suite, and a practitioner uses it in two ways: to trust the library, and as the canonical worked examples of how each function is meant to be called.

The suite combines unit tests generated from data files, integration tests that run real handshakes, interoperability tests against other TLS stacks, and — distinctively — tests that drive the *driver* entry points. The driver tests are the closest thing to documentation of the driver interface: the test driver source under the framework's `tests/src/drivers` directory shows exactly what a transparent or opaque driver must implement, paired with sample description JSON files (`mbedtls_test_transparent_driver.json`, `mbedtls_test_opaque_driver.json`) and the `test_driver.h` header they require. If you are writing a driver, you read these before you read prose.

For your own code, the discipline is to test against the abstraction the library actually guarantees. Test that your code handles `PSA_ERROR_NOT_PERMITTED` (you will hit it during development as you tune policies), that it survives `WANT_READ`/`WANT_WRITE` on non-blocking I/O, and — the one most teams skip — that it behaves correctly when entropy or storage backends fail, because those are the production failure modes (Chapters 45, 23) that a happy-path test never exercises.

There is also a compliance dimension: the external `psa-arch-tests` suite checks an implementation against the PSA Functional API specification (Chapter 49). If your product claims API compliance, that suite is the arbiter, and running it early surfaces interface gaps while they are cheap to fix.

> **Principle 52.** *The driver tests are the driver documentation; read the test source before the prose, and test your own code against the failure modes the happy path hides.*

### Chapter 53 — Which Sample Programs to Read

The repository ships many example programs, and they are simultaneously the best and the most dangerous learning resource — best because they compile and run, dangerous because some demonstrate the paradigm you should be leaving. Knowing which to study is itself a skill.

```
   READ FIRST (the new paradigm)        READ LATER / WITH CAUTION
   ─────────────────────────────        ─────────────────────────
   programs/psa/*  (key-by-reference,   programs/ssl/ssl_client2,
   import/sign/destroy, AEAD, KDF)        ssl_server2 — powerful but
                                          sprawling; not a starting point
   the minimal psa crypto examples      anything centered on
   that show one operation end-to-end    mbedtls_pk_* or mbedtls_rsa_*
                                          as the crypto entry point
```

Begin with the **PSA crypto examples** — the small programs that import a key, perform one operation, and destroy the key. They teach the atom of Part II directly and in the current idiom. A single program that creates an AES key, encrypts with AEAD, and tears down cleanly teaches more correct intuition than a thousand lines of TLS sample.

Approach the **TLS sample clients and servers** (`ssl_client2`, `ssl_server2`) with respect but not as tutorials. They are comprehensive test harnesses with hundreds of command-line options, invaluable for *probing* a server and reproducing handshake scenarios, but their breadth makes them poor first reading — you cannot see the essential handshake of Chapter 35 through the thicket of options. Use them to experiment with a live peer; do not learn the structure of a TLS application from them.

And treat any example built around the legacy crypto contexts as a historical artifact (Chapter 18). It will compile in compatibility shims, perhaps, but it teaches the key-by-value world you are migrating away from. The presence of `mbedtls_rsa_context` in a "how to do crypto" example dates it as surely as a timestamp.

> **Principle 53.** *Learn from the small PSA examples, probe with the big TLS ones, and read every legacy-crypto sample as history — not as instruction.*

### Chapter 54 — Debugging the Wire

When a TLS connection fails, the failure is often not in your code but in the negotiation between two peers, and the tools for seeing into that negotiation are specific. A practitioner reaches for them in a fixed order.

First, turn on the library's own debug output. `mbedtls_debug_set_threshold` and a debug callback set via the SSL config expose the handshake step by step — which messages were sent, which ciphersuite was chosen, where verification failed. The debug level is a dial; turn it up to see the handshake's internal decisions, which is usually where the answer is. This requires `MBEDTLS_DEBUG_C` in the build, so keep it available in your debug configuration even though you strip it from release.

Second, read the *return code* as a category (Chapter 13, and Chapter 55 next). A handshake that fails with a verification error is a certificate or trust-store problem, not a network problem; one that fails with a protocol-version error is a negotiation mismatch. The error category routes you to the right half of the system before you read a single packet.

Third, when the failure is genuinely on the wire, capture it. A packet capture of the handshake — the cleartext portions of which are visible even in TLS 1.3 — shows the ClientHello's offered versions and ciphersuites against the ServerHello's selection, which immediately reveals negotiation failures. Pair this with the library's debug log and you can see both sides of the same conversation: what your peer offered, and what your library made of it.

> **Principle 54.** *Read the error category first, the library's debug log second, the packet capture third — most TLS failures are negotiation or trust problems wearing a network problem's clothes.*

---

## Part X — Mastery

### Chapter 55 — Reading a PSA Error

A `psa_status_t` is not a number to look up; it is a diagnosis to read. The mastery move is to map the status to the *layer* that is unhappy and go straight there, instead of bisecting your whole program. Five categories cover almost everything.

```
   status                       layer at fault          first thing to check
   ──────                       ──────────────          ────────────────────
   PSA_ERROR_NOT_SUPPORTED   ►  the BUILD               is PSA_WANT_* set? (Ch 14)
   PSA_ERROR_NOT_PERMITTED   ►  the KEY POLICY          usage flags + algorithm (Ch 10,31)
   PSA_ERROR_INVALID_ARGUMENT►  your CALL               types, sizes, a wrong macro
   PSA_ERROR_BAD_STATE       ►  your ORDER OF CALLS     setup before update? (Ch 24)
   PSA_ERROR_INVALID_SIGNATURE► the CRYPTO ITSELF        genuine verification failure
```

`PSA_ERROR_NOT_SUPPORTED` almost never means a bug in your logic; it means the mechanism is not in the binary. You asked for SHA-512 and the build only compiled SHA-256. The fix is in `crypto_config.h`, not your source. This is the single most common newcomer error and the one most often misdiagnosed as "the library is broken."

`PSA_ERROR_NOT_PERMITTED` means the operation was real and supported but the key's policy forbade it — the verify-only key asked to sign, the SIGN_HASH key asked to sign a message (Chapter 31). The fix is the key's attributes at creation, and since policy is immutable (Chapter 10), the fix means creating the key differently, not patching it.

The remaining three are progressively closer to your own code: a malformed argument, a violated state machine, or — `INVALID_SIGNATURE` — an honest cryptographic mismatch that usually means the data really does not verify. Train yourself to read the category and jump to its layer. That reflex is most of what separates someone who debugs PSA in minutes from someone who debugs it in days.

> **Principle 55.** *NOT_SUPPORTED is the build, NOT_PERMITTED is the policy, BAD_STATE is your call order — read the category and jump to its layer instead of bisecting your program.*

### Chapter 56 — Common Errors and Their Meaning

The recurring failures of real Mbed TLS work cluster into a small set. Here they are as a lookup table from symptom to root cause to fix — the chapter to keep open during integration.

| Symptom | Root cause | Fix |
|---------|-----------|-----|
| `psa/crypto.h` not found | TF-PSA-Crypto submodule not initialized | `git submodule update --init` (Ch 17, 50) |
| `PSA_ERROR_NOT_SUPPORTED` at runtime | mechanism not compiled in | set the right `PSA_WANT_*` (Ch 15) |
| `PSA_ERROR_NOT_PERMITTED` | key policy too narrow / wrong op | fix usage flags + permitted alg at creation (Ch 10, 31) |
| `PSA_ERROR_BAD_STATE` | operation functions called out of order | follow setup→update→finish; init the op object (Ch 24, 26) |
| `PSA_ERROR_INSUFFICIENT_ENTROPY` | DRBG cannot seed | wire a real entropy source (Ch 45) |
| everything "random" is predictable | stub entropy source, no error raised | the silent failure — verify the TRNG (Ch 45) |
| persistent key not found after reboot | no storage backend on the target | provide ITS/PS (Ch 23) |
| TLS handshake fails with verify error | trust store missing the root, or name mismatch | provision CA, check hostname (Ch 37) |
| handshake "fails" but returns WANT_READ | mistaking I/O-pending for error | loop on the handshake (Ch 35) |
| build links but binary is huge | full config shipped to a constrained target | subtract from a preset; trim buffers (Ch 44, 51) |
| code from a tutorial won't compile | tutorial predates the 4.0 paradigm | migrate to key-by-reference (Ch 48) |
| slot exhaustion creating keys | volatile keys not destroyed | match every create with a destroy (Ch 22) |

Two of these rows are worth more than the others combined. The **silent entropy failure** is the only one with no error to catch, which is why it is the most dangerous (Chapter 45). And the **tutorial-won't-compile** row is the one that wastes the most newcomer hours, because the instinct is to fix the code rather than to suspect the paradigm — when the right move is to recognize that the example belongs to an earlier era of the library (Chapter 5, 48).

> **Principle 56.** *Most failures are configuration, policy, or paradigm — not cryptography; the one failure with no error message, weak entropy, is the one that can ruin you.*

### Chapter 57 — Architecting Around PSA

When you design a whole system rather than a single call, a few decisions made early determine whether the security model works for you or fights you. This is the architect's chapter: the choices to make before writing code.

Decide where each key lives, first. Sort your keys by value: the long-term device identity key is your crown jewel and belongs behind an opaque driver in a secure element if the threat model and budget allow; ephemeral session keys can be volatile in software; configuration secrets sit in between. This sorting drives your hardware choice, because "put the identity key in hardware" means choosing a part with a secure element and an opaque driver. Make this decision before the schematic is fixed, because it is expensive to change later.

```
   key sorting drives the architecture
   ───────────────────────────────────
   device identity / attestation key  ─►  opaque driver, secure element
   long-term server-auth key          ─►  opaque if possible, else persistent+ITS
   session / ephemeral keys           ─►  volatile, software, destroyed promptly
   configuration secrets              ─►  persistent, protected storage
```

Decide the boundary, second. Will the application and the crypto share an address space (full build), or will crypto live in a secure partition behind the PSA boundary (client build, Chapter 41)? This is largely a hardware-and-RTOS decision, but it determines whether a compromise of your application is survivable. If your threat model includes a compromised application — and on a network-connected device it should — the boundary is not optional.

Decide your update and trust story, third. Which CA roots will the device trust, and how will you rotate them? How will firmware be signed and verified (Chapter 43)? These are crypto-dependent decisions that are painful to retrofit. The architect's discipline is to treat key placement, the security boundary, and the trust/update story as first-class design inputs, settled before implementation — because each is cheap to choose and ruinous to change.

> **Principle 57.** *Sort your keys by value and place each accordingly before you choose hardware; key placement, the security boundary, and the trust story are architecture, not implementation details.*

### Chapter 58 — How to Actually Learn It

Forget the standard on-ramp. The instinct is to clone the repository, build `ssl_client2`, point it at a web server, and feel productive when a handshake completes. This teaches you almost nothing, because the TLS sample hides every concept that matters behind a working black box and a hundred command-line flags. You will have run TLS without understanding a single thing about how it works.

Begin instead with the key. Write, by hand, one tiny program that does exactly this and nothing more: call `psa_crypto_init`, build a key attributes object, generate or import one symmetric key, perform one AEAD encryption and decryption, and destroy the key. Make it compile against 4.x. When you can do this without copying, you understand the atom of the entire system — the key-by-reference model, the attributes, the policy, the operation lifecycle — and everything else is composition.

Read sources in this order, not the order the website presents them. First, the **PSA Crypto API specification** itself (the `arm-software.github.io/psa-api/crypto` pages and the actual `psa/crypto.h` header) — it is precise, complete, and paradigm-correct, where most blog tutorials are none of these. Second, the **small PSA example programs** (Chapter 53). Third, the **migration guide** even if you have nothing to migrate, because it names the old paradigm explicitly and thereby inoculates you against the stale tutorials you will inevitably find. Only then, fourth, approach TLS — and approach it through the lens of Chapter 39, watching for the `psa_*` calls underneath.

Do not, early on, read the bignum or ECC implementation source "to understand how RSA works." It is a rabbit hole of constant-time arithmetic tricks that teaches you nothing about *using* the library and consumes days. The implementation is something you trust and configure, not something you must read to be competent. Competence here is fluency with the interface and the configuration, not familiarity with the field arithmetic.

> **Principle 58.** *Forget the TLS demo; write the ten-line key program first, read the spec before any blog, and never read the bignum source to "learn crypto."*

### Chapter 59 — Synthesis

Everything in this manual reduces to a handful of moves, and a master makes them without thinking. Hold these and you hold the subject.

The key is a name, not a value. This one sentence generates the driver model, the security boundary, the storage model, and the entire 4.0 migration. When anything confuses you, return to it: ask *who holds the secret here?* and the answer is always "not your code" — your code holds permission, and the secret lives somewhere it may never reach.

The system is layered and the dependencies point one way. Application over TLS over crypto over drivers; configuration determines what exists; the dispatch layer decides who executes. TLS is a client of crypto exactly as you are. Nothing reaches up; everything reaches down. When you lose your place, redraw the diagram of Chapter 4.

The build is the system. A mechanism not configured does not exist; a feature enabled without its crypto is a contradiction the build rejects; a binary untrimmed does not fit. You program this library as much in its config headers as in your C, and the config headers are the source you most need under version control.

And the paradigm has changed. The library you are using is not the library most of the internet's tutorials describe. When something does not compile, suspect the era before the code. When something is insecure with no error, suspect the entropy. When something is forbidden, suspect the policy. When something is missing, suspect the build. The categories of failure are few, and naming the category is most of the cure.

You have the kit. Now compose only what your product needs, place each key according to its worth, drive the handshake to zero, and ship the subset — and nothing else.

> **Principle 59.** *Ask "who holds the secret?" and the answer is never your code; that single question regenerates the whole architecture from memory.*

---

## Appendices

### Appendix A — Configuration Symbol Reference

| Symbol | Lives in | Meaning |
|--------|----------|---------|
| `PSA_WANT_ALG_xxx` | crypto_config.h | request an algorithm be available |
| `PSA_WANT_KEY_TYPE_xxx` | crypto_config.h | request a key type be available |
| `PSA_WANT_ECC_FAMILY_xxx` | crypto_config.h | request an elliptic-curve family |
| `MBEDTLS_PSA_CRYPTO_C` | crypto_config.h | build the full crypto implementation |
| `MBEDTLS_PSA_CRYPTO_CLIENT` | crypto_config.h | build only the client side of crypto |
| `MBEDTLS_PSA_ACCEL_xxx` | generated | a transparent driver provides this mechanism |
| `MBEDTLS_PSA_BUILTIN_xxx` | generated | the software implementation is compiled in |
| `MBEDTLS_PSA_CRYPTO_STORAGE_C` | crypto_config.h | enable persistent key storage |
| `MBEDTLS_USE_PSA_CRYPTO` | (legacy/transitional) | route protocol layers through PSA |
| `MBEDTLS_SSL_PROTO_TLS1_2` | mbedtls_config.h | enable TLS 1.2 |
| `MBEDTLS_SSL_PROTO_TLS1_3` | mbedtls_config.h | enable TLS 1.3 |
| `MBEDTLS_SSL_CLI_C` / `_SRV_C` | mbedtls_config.h | enable client / server roles |
| `MBEDTLS_SSL_IN_CONTENT_LEN` | mbedtls_config.h | inbound record buffer size (RAM) |
| `MBEDTLS_SSL_OUT_CONTENT_LEN` | mbedtls_config.h | outbound record buffer size (RAM) |
| `MBEDTLS_X509_CRT_PARSE_C` | mbedtls_config.h | enable X.509 certificate parsing |
| `MBEDTLS_THREADING_C` | config | enable mutex protection of shared state |
| `MBEDTLS_DEBUG_C` | mbedtls_config.h | enable the TLS debug callback |

### Appendix B — Key Lifecycle Function Reference

| Function | What it does | When it runs |
|----------|--------------|--------------|
| `psa_crypto_init` | initialize the subsystem | once, before any other `psa_*` call |
| `psa_set_key_type` / `_bits` | set key type / size in attributes | before creation |
| `psa_set_key_usage_flags` | set the permitted operations | before creation |
| `psa_set_key_algorithm` | set the permitted algorithm | before creation |
| `psa_set_key_lifetime` / `_id` | set persistence/location and name | before creating a persistent key |
| `psa_import_key` | create a key from supplied material | key creation |
| `psa_generate_key` | create a random key | key creation |
| `psa_key_derivation_output_key` | create a key from a derivation | key creation |
| `psa_copy_key` | duplicate a key with a (narrower) policy | key creation |
| `psa_get_key_attributes` | read back a key's metadata | any time after creation |
| `psa_export_key` / `_public_key` | extract material (policy permitting) | when EXPORT/public access is allowed |
| `psa_destroy_key` | erase a key and free its slot | once per created key |

### Appendix C — Algorithm and Type Macro Cheat Sheet

| Need | Macro |
|------|-------|
| SHA-256 hash | `PSA_ALG_SHA_256` |
| HMAC over a hash | `PSA_ALG_HMAC(hash_alg)` |
| AES-GCM (AEAD) | `PSA_ALG_GCM` |
| ChaCha20-Poly1305 | `PSA_ALG_CHACHA20_POLY1305` |
| CBC, no padding | `PSA_ALG_CBC_NO_PADDING` |
| ECDSA over a hash | `PSA_ALG_ECDSA(hash_alg)` |
| RSA PSS over a hash | `PSA_ALG_RSA_PSS(hash_alg)` |
| RSA OAEP (encrypt) | `PSA_ALG_RSA_OAEP(hash_alg)` |
| ECDH key agreement | `PSA_ALG_ECDH` |
| HKDF over a hash | `PSA_ALG_HKDF(hash_alg)` |
| any-hash wildcard (policy only) | `PSA_ALG_ANY_HASH` |
| extract the hash from a composite | `PSA_ALG_GET_HASH(alg)` |
| AES key type | `PSA_KEY_TYPE_AES` |
| HMAC key type | `PSA_KEY_TYPE_HMAC` |
| ECC key pair on a family | `PSA_KEY_TYPE_ECC_KEY_PAIR(family)` |
| ECC public key on a family | `PSA_KEY_TYPE_ECC_PUBLIC_KEY(family)` |
| RSA key pair / public | `PSA_KEY_TYPE_RSA_KEY_PAIR` / `_RSA_PUBLIC_KEY` |
| NIST P-256 family | `PSA_ECC_FAMILY_SECP_R1` (with 256 bits) |
| Curve25519 family | `PSA_ECC_FAMILY_MONTGOMERY` (with 255 bits) |
| output buffer size for a hash | `PSA_HASH_LENGTH(alg)` |
| output buffer size for AEAD encrypt | `PSA_AEAD_ENCRYPT_OUTPUT_SIZE(type, alg, len)` |

### Appendix D — Status Code Catalog

| Status | Category | Typical cause |
|--------|----------|---------------|
| `PSA_SUCCESS` | — | operation succeeded (value 0) |
| `PSA_ERROR_NOT_SUPPORTED` | build | mechanism not compiled in |
| `PSA_ERROR_NOT_PERMITTED` | policy | key usage flag or algorithm forbids it |
| `PSA_ERROR_INVALID_ARGUMENT` | call | malformed parameter, wrong type/size |
| `PSA_ERROR_BAD_STATE` | call order | operation functions out of sequence, or uninitialized |
| `PSA_ERROR_BUFFER_TOO_SMALL` | call | output buffer undersized — use the size macros |
| `PSA_ERROR_INVALID_SIGNATURE` | crypto | a verification genuinely failed |
| `PSA_ERROR_INVALID_HANDLE` | call | key identifier does not name a live key |
| `PSA_ERROR_INSUFFICIENT_MEMORY` | resource | heap exhausted |
| `PSA_ERROR_INSUFFICIENT_ENTROPY` | resource | DRBG could not seed |
| `PSA_ERROR_INSUFFICIENT_STORAGE` | resource | no room for a persistent key |
| `PSA_ERROR_STORAGE_FAILURE` | backend | the storage backend failed or is absent |
| `PSA_ERROR_COMMUNICATION_FAILURE` | backend | the crypto service (across a boundary) is unreachable |
| `PSA_ERROR_CORRUPTION_DETECTED` | integrity | a tamper or consistency check tripped |

### Appendix E — Glossary

**AEAD** — Authenticated Encryption with Associated Data; encrypts and authenticates in one operation.

**Attributes** — the metadata object (`psa_key_attributes_t`) describing a key's type, size, lifetime, and policy.

**DRBG** — Deterministic Random Bit Generator; stretches entropy into the random stream crypto consumes.

**Dispatch layer** — the driver-wrapper layer that routes each crypto operation to software, a transparent driver, or an opaque driver.

**EAT** — Entity Attestation Token; the signed claim of what firmware a device runs.

**ITS / PS** — Internal Trusted Storage / Protected Storage; the two PSA Secure Storage services.

**Key by reference** — the model in which code holds a key identifier, not the key material.

**Key by value** — the legacy model in which code holds the key bytes directly.

**Lifetime** — the attribute encoding a key's persistence and storage location.

**NSPE / SPE** — Non-Secure / Secure Processing Environment; the two hardware-isolated worlds of a PSA device.

**Opaque driver** — a driver for keys that never leave a protected environment; dispatched by key location.

**Policy** — a key's immutable permitted operations (usage flags) and permitted algorithm.

**PSA** — Platform Security Architecture; the specifications and certification program.

**PSA Crypto API** — the cryptographic interface, one of four PSA Functional APIs.

**PSA-RoT** — PSA Root of Trust; the trust anchor running in the SPE.

**TF-M** — Trusted Firmware-M; reference firmware implementing the PSA-RoT on Arm MCUs.

**TF-PSA-Crypto** — the repository/component holding PSA Crypto, split out from Mbed TLS at 4.0.

**Transparent driver** — a driver that sees key material in the clear; used for acceleration; dispatched by parameters.

**Volatile / Persistent key** — a key that dies at reset / a key that survives reset with a permanent identifier.

### Appendix F — Upstream Sources

- **PSA Crypto API specification** — `https://arm-software.github.io/psa-api/crypto/` (the authoritative interface; read this first).
- **Mbed TLS repository** — `https://github.com/Mbed-TLS/mbedtls` (TLS, X.509, PK, PKCS7).
- **TF-PSA-Crypto repository** — `https://github.com/Mbed-TLS/TF-PSA-Crypto` (PSA Crypto implementation, driver interface docs).
- **4.0 migration guide** — `docs/4.0-migration-guide.md` in Mbed TLS; `1.0-migration-guide.md` in TF-PSA-Crypto.
- **Driver interface** — `docs/proposed/psa-driver-interface.md` and `docs/psa-driver-example-and-guide.md` in TF-PSA-Crypto.
- **PSA Certified program** — `https://www.psacertified.org/` (levels, Protection Profiles, functional API certification).
- **PSA API compliance tests** — `https://github.com/ARM-software/psa-arch-tests`.
- **Trusted Firmware-M** — `https://www.trustedfirmware.org/projects/tf-m/`.
- **Announcements and releases** — `lists.trustedfirmware.org` and the GitHub Releases pages (track these for security fixes).

---

> *The key is a name, not a value. Everything else is composition.*

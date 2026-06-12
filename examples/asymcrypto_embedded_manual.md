# Asymmetric Cryptography for Embedded Devices
### A First-Principles Manual for the Cyber Embedded Architect

---

*There are exactly two things asymmetric cryptography does: it lets a party prove possession of a secret without revealing it, and it lets two parties establish a shared secret without ever transmitting one. Everything else in this manual is consequence.*

---

## Preface

This manual is for the embedded systems architect who must make asymmetric cryptography work correctly on constrained hardware. Not the mathematician deriving security proofs, and not the developer calling `wolfSSL_connect()` without caring what happens inside. The architect in between: the one who selects algorithms, integrates public-key accelerators, designs the certificate chain, builds the attestation scheme, debugs why ECDH fails on the M4 but passes on the host, and decides whether a 32-kilobyte RAM budget can support TLS 1.3 with P-256.

Asymmetric cryptography is harder to deploy correctly than symmetric cryptography. Its primitives are mathematically deeper, its implementation attack surface is larger, its performance penalty is severe on constrained hardware, and its failure modes are more subtle. A wrong AES key produces garbled ciphertext that fails immediately. A wrong elliptic-curve implementation may produce valid-looking signatures that an adversary can forge.

You will learn, in order:

- What asymmetric cryptography is, what it provides, and what it does not (Part I)
- The taxonomy of asymmetric primitives: key agreement, signatures, and encryption (Part II)
- Keys, certificates, and public-key infrastructure for embedded systems (Part III)
- The mathematical internals of ECC, RSA, and lattice-based schemes — at the depth that changes how you implement them (Part IV)
- Elliptic curve cryptography in practice: curve selection, implementation, and hardware acceleration (Part V)
- Signatures for embedded systems: ECDSA, EdDSA, and RSA-PSS (Part VI)
- Key agreement and key encapsulation: ECDH, X25519, and post-quantum KEM (Part VII)
- Certificate management and PKI for IoT fleets (Part VIII)
- Production realities: what changes at scale (Part IX)
- Tooling and workflow: libraries, profiling, and test vectors (Part X)
- Mastery: debugging, architectural patterns, and how to actually learn this field (Part XI)
- Appendices: reference tables, cheat sheets, glossary

Each chapter teaches one thing. Read once for orientation; return to chapters as reference.

---

## Table of Contents

- [Asymmetric Cryptography for Embedded Devices](#asymmetric-cryptography-for-embedded-devices)
    - [A First-Principles Manual for the Cyber Embedded Architect](#a-first-principles-manual-for-the-cyber-embedded-architect)
  - [Preface](#preface)
  - [Table of Contents](#table-of-contents)
- [Part I — Orientation](#part-i--orientation)
  - [Chapter 1 — The Duality: Public Knowledge vs Secret Capability](#chapter-1--the-duality-public-knowledge-vs-secret-capability)
  - [Chapter 2 — What Asymmetric Crypto Provides (and Does Not)](#chapter-2--what-asymmetric-crypto-provides-and-does-not)
  - [Chapter 3 — The Three Doors: Primitive Categories](#chapter-3--the-three-doors-primitive-categories)
  - [Chapter 4 — The Embedded Cost Model](#chapter-4--the-embedded-cost-model)
  - [Chapter 5 — Asymmetric vs Symmetric: Roles, Not Rivals](#chapter-5--asymmetric-vs-symmetric-roles-not-rivals)
- [Part II — Anatomy](#part-ii--anatomy)
  - [Chapter 6 — Key Pairs: Public and Private](#chapter-6--key-pairs-public-and-private)
  - [Chapter 7 — Digital Signatures](#chapter-7--digital-signatures)
  - [Chapter 8 — Key Agreement](#chapter-8--key-agreement)
  - [Chapter 9 — Public-Key Encryption and Key Encapsulation](#chapter-9--public-key-encryption-and-key-encapsulation)
  - [Chapter 10 — Certificates and Binding](#chapter-10--certificates-and-binding)
  - [Chapter 11 — Signature vs Encryption: The Dangerous Inversion](#chapter-11--signature-vs-encryption-the-dangerous-inversion)
  - [Chapter 12 — Authentication vs Authorization](#chapter-12--authentication-vs-authorization)
- [Part III — Configuration and Composition](#part-iii--configuration-and-composition)
  - [Chapter 13 — Key Sizes and Security Levels](#chapter-13--key-sizes-and-security-levels)
  - [Chapter 14 — Key Generation: Randomness and Curve Selection](#chapter-14--key-generation-randomness-and-curve-selection)
  - [Chapter 15 — Certificate Structure and Fields](#chapter-15--certificate-structure-and-fields)
  - [Chapter 16 — Certificate Chains and Trust Anchors](#chapter-16--certificate-chains-and-trust-anchors)
  - [Chapter 17 — Key Lifetimes and Certificate Validity](#chapter-17--key-lifetimes-and-certificate-validity)
  - [Chapter 18 — Algorithm Identifiers and OIDs](#chapter-18--algorithm-identifiers-and-oids)
- [Part IV — Mathematical Internals](#part-iv--mathematical-internals)
  - [Chapter 19 — Groups, Hardness, and the Discrete Log Problem](#chapter-19--groups-hardness-and-the-discrete-log-problem)
  - [Chapter 20 — Elliptic Curves: The Geometry](#chapter-20--elliptic-curves-the-geometry)
  - [Chapter 21 — Elliptic Curve Arithmetic: Point Addition](#chapter-21--elliptic-curve-arithmetic-point-addition)
  - [Chapter 22 — Scalar Multiplication and Its Cost](#chapter-22--scalar-multiplication-and-its-cost)
  - [Chapter 23 — RSA: Factoring and the Trapdoor](#chapter-23--rsa-factoring-and-the-trapdoor)
  - [Chapter 24 — Lattices and Post-Quantum Security](#chapter-24--lattices-and-post-quantum-security)
  - [Chapter 25 — Why Key Sizes Differ Across Algorithm Families](#chapter-25--why-key-sizes-differ-across-algorithm-families)
- [Part V — Elliptic Curve Cryptography in Practice](#part-v--elliptic-curve-cryptography-in-practice)
  - [Chapter 26 — Curve Taxonomy: NIST, Brainpool, and Bernstein Curves](#chapter-26--curve-taxonomy-nist-brainpool-and-bernstein-curves)
  - [Chapter 27 — P-256 vs X25519: The Architectural Choice](#chapter-27--p-256-vs-x25519-the-architectural-choice)
  - [Chapter 28 — Hardware ECC Accelerators](#chapter-28--hardware-ecc-accelerators)
  - [Chapter 29 — Coordinate Systems and Montgomery Arithmetic](#chapter-29--coordinate-systems-and-montgomery-arithmetic)
  - [Chapter 30 — ECC Side-Channel Attacks and Countermeasures](#chapter-30--ecc-side-channel-attacks-and-countermeasures)
- [Part VI — Digital Signatures for Embedded Systems](#part-vi--digital-signatures-for-embedded-systems)
  - [Chapter 31 — ECDSA: Structure and Failure Modes](#chapter-31--ecdsa-structure-and-failure-modes)
  - [Chapter 32 — EdDSA and Ed25519: The Modern Signature](#chapter-32--eddsa-and-ed25519-the-modern-signature)
  - [Chapter 33 — RSA-PSS: When RSA Is Required](#chapter-33--rsa-pss-when-rsa-is-required)
  - [Chapter 34 — ECDSA vs EdDSA: The Decision](#chapter-34--ecdsa-vs-eddsa-the-decision)
  - [Chapter 35 — Signature Verification in Secure Boot](#chapter-35--signature-verification-in-secure-boot)
  - [Chapter 36 — Hash-then-Sign and the Role of the Hash Function](#chapter-36--hash-then-sign-and-the-role-of-the-hash-function)
- [Part VII — Key Agreement and Key Encapsulation](#part-vii--key-agreement-and-key-encapsulation)
  - [Chapter 37 — ECDH: The Fundamental Construction](#chapter-37--ecdh-the-fundamental-construction)
  - [Chapter 38 — X25519: The Clean Curve for Key Agreement](#chapter-38--x25519-the-clean-curve-for-key-agreement)
  - [Chapter 39 — Forward Secrecy and Ephemeral Keys](#chapter-39--forward-secrecy-and-ephemeral-keys)
  - [Chapter 40 — Static vs Ephemeral: The Tradeoff](#chapter-40--static-vs-ephemeral-the-tradeoff)
  - [Chapter 41 — Post-Quantum KEM: Kyber / ML-KEM](#chapter-41--post-quantum-kem-kyber--ml-kem)
  - [Chapter 42 — Hybrid Key Exchange](#chapter-42--hybrid-key-exchange)
- [Part VIII — PKI for Embedded Fleets](#part-viii--pki-for-embedded-fleets)
  - [Chapter 43 — The PKI Hierarchy for IoT](#chapter-43--the-pki-hierarchy-for-iot)
  - [Chapter 44 — Device Identity Certificates](#chapter-44--device-identity-certificates)
  - [Chapter 45 — Certificate Provisioning at Manufacturing](#chapter-45--certificate-provisioning-at-manufacturing)
  - [Chapter 46 — Certificate Revocation on Constrained Devices](#chapter-46--certificate-revocation-on-constrained-devices)
  - [Chapter 47 — Attestation: Proving Device Identity Without a Certificate Authority](#chapter-47--attestation-proving-device-identity-without-a-certificate-authority)
- [Part IX — Production Realities](#part-ix--production-realities)
  - [Chapter 48 — Performance Budget for Asymmetric Operations](#chapter-48--performance-budget-for-asymmetric-operations)
  - [Chapter 49 — Memory Layout for Asymmetric Crypto](#chapter-49--memory-layout-for-asymmetric-crypto)
  - [Chapter 50 — Nonce and Randomness Failures in Asymmetric Crypto](#chapter-50--nonce-and-randomness-failures-in-asymmetric-crypto)
  - [Chapter 51 — Clock and Time: The Silent Dependency](#chapter-51--clock-and-time-the-silent-dependency)
  - [Chapter 52 — Post-Quantum Migration Planning](#chapter-52--post-quantum-migration-planning)
- [Part X — Tooling and Workflow](#part-x--tooling-and-workflow)
  - [Chapter 53 — Library Selection for Embedded Targets](#chapter-53--library-selection-for-embedded-targets)
  - [Chapter 54 — Mbed TLS PSA API for Asymmetric Operations](#chapter-54--mbed-tls-psa-api-for-asymmetric-operations)
  - [Chapter 55 — WolfSSL Asymmetric Operations](#chapter-55--wolfssl-asymmetric-operations)
  - [Chapter 56 — Test Vectors and CAVP for Asymmetric Algorithms](#chapter-56--test-vectors-and-cavp-for-asymmetric-algorithms)
  - [Chapter 57 — Profiling Asymmetric Operations on Embedded Targets](#chapter-57--profiling-asymmetric-operations-on-embedded-targets)
- [Part XI — Mastery](#part-xi--mastery)
  - [Chapter 58 — Debugging Asymmetric Crypto Failures](#chapter-58--debugging-asymmetric-crypto-failures)
  - [Chapter 59 — Architectural Patterns for Asymmetric Crypto in Embedded Systems](#chapter-59--architectural-patterns-for-asymmetric-crypto-in-embedded-systems)
  - [Chapter 60 — Common Errors and Their Meaning](#chapter-60--common-errors-and-their-meaning)
  - [Chapter 61 — How to Actually Learn Embedded Asymmetric Cryptography](#chapter-61--how-to-actually-learn-embedded-asymmetric-cryptography)
- [Appendices](#appendices)
  - [Appendix A — Algorithm and Key Size Reference](#appendix-a--algorithm-and-key-size-reference)
  - [Appendix B — Operation Performance Reference](#appendix-b--operation-performance-reference)
  - [Appendix C — ASN.1 / DER / PEM Cheat Sheet](#appendix-c--asn1--der--pem-cheat-sheet)
  - [Appendix D — OID Reference for Embedded PKI](#appendix-d--oid-reference-for-embedded-pki)
  - [Appendix E — Glossary](#appendix-e--glossary)

---

# Part I — Orientation

---

## Chapter 1 — The Duality: Public Knowledge vs Secret Capability

Asymmetric cryptography rests on one idea. Hold this picture in your mind before anything else.

There exists a mathematical operation that is easy to perform in one direction and computationally infeasible to reverse without a specific secret. The easy direction is public — anyone can do it. The hard direction requires the secret. This asymmetry is the entire foundation.

```
┌─────────────────────────────────────────────────────────────────┐
│                  The Asymmetric Duality                         │
│                                                                 │
│   PUBLIC KEY                      PRIVATE KEY                  │
│   (known to everyone)             (known only to owner)        │
├──────────────────────────────┬──────────────────────────────────┤
│  Easy direction:             │  Hard direction:                 │
│  Anyone can compute          │  Only private key holder can     │
│                              │                                  │
│  encrypt to key owner        │  decrypt messages                │
│  verify owner's signature    │  create signatures               │
│  derive shared secret        │  complete key agreement          │
├──────────────────────────────┴──────────────────────────────────┤
│  Hardness assumption: computing the private key from the        │
│  public key is computationally infeasible.                      │
│                                                                 │
│  If the assumption breaks (quantum computer, new algorithm),    │
│  the entire system breaks.                                      │
└─────────────────────────────────────────────────────────────────┘
```

The hardness assumption is not proved. It is believed. Every asymmetric cryptosystem in use today rests on a computational problem that we believe is hard — factoring large integers (RSA), computing discrete logarithms in elliptic curve groups (ECC) — but for which no proof of hardness exists. This is different from symmetric cryptography, where the security argument is more combinatorial.

This distinction matters for embedded architects. The security of your system depends on the continued belief that specific mathematical problems are hard. When Shor's algorithm runs on a sufficiently large quantum computer, that belief fails for RSA and ECC simultaneously. Symmetric keys shrink in quantum security by a square root; asymmetric systems collapse entirely. This is why post-quantum cryptography exists, and why planning for it is not optional for devices with long deployment lifetimes.

> **Principle 1.** *Asymmetric cryptography is founded on an unproved hardness assumption; the assumption is strong for classical computers and breaks for quantum computers. Design with migration in mind.*

---

## Chapter 2 — What Asymmetric Crypto Provides (and Does Not)

Asymmetric cryptography provides three capabilities that symmetric cryptography cannot provide alone.

**Key distribution without prior contact.** Two parties who have never met can establish a shared secret over an untrusted channel. Symmetric cryptography requires a shared secret to already exist; asymmetric cryptography creates it.

**Non-repudiation.** A party can produce a signature that only they could have created. Because the signing key is held by exactly one party, a valid signature is proof of that party's involvement. Symmetric MACs cannot provide this: both parties hold the key, so either could have produced the tag.

**Device identity without a pre-shared secret.** A device can prove its identity by demonstrating possession of a private key that corresponds to a certified public key, without revealing the private key.

What asymmetric cryptography does not provide:

**Bulk encryption performance.** RSA-2048 encryption is roughly 1000× slower than AES-128 for the same data volume. ECC operations are expensive on constrained hardware. Asymmetric cryptography is used to establish keys, not to encrypt bulk data.

**Protection without correct key management.** A certificate proves that a public key belongs to an entity named in the certificate. It proves nothing about whether that entity is trustworthy, whether the private key is still secret, or whether the certificate has been revoked.

**Automatic mutual authentication.** A TLS handshake where only the server presents a certificate authenticates the server to the client — not the client to the server. Mutual TLS requires both sides to present certificates. Many embedded deployments authenticate only the server, leaving the device unauthenticated.

```
┌──────────────────────────────────────────────────────────────────┐
│          What Asymmetric Crypto Provides vs Does Not             │
├──────────────────────────────┬───────────────────────────────────┤
│         PROVIDES             │        DOES NOT PROVIDE           │
├──────────────────────────────┼───────────────────────────────────┤
│ Key exchange without prior   │ Bulk data encryption              │
│ shared secret                │                                   │
├──────────────────────────────┼───────────────────────────────────┤
│ Non-repudiation              │ Automatic mutual authentication   │
├──────────────────────────────┼───────────────────────────────────┤
│ Certifiable device identity  │ Revocation (without infrastructure)│
├──────────────────────────────┼───────────────────────────────────┤
│ Authenticated key agreement  │ Resistance to quantum computers   │
│                              │ (current algorithms)              │
└──────────────────────────────┴───────────────────────────────────┘
```

> **Principle 2.** *Asymmetric cryptography establishes keys and proves identity; symmetric cryptography protects data. The two work together — neither replaces the other.*

---

## Chapter 3 — The Three Doors: Primitive Categories

There are exactly three categories of asymmetric cryptographic primitive. Every algorithm, every protocol, every scheme you will encounter is built from one or more of these three.

```
┌────────────────────────────────────────────────────────────────┐
│              Three Asymmetric Primitive Categories             │
│                                                                │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐   │
│  │   SIGNATURE   │  │ KEY AGREEMENT │  │  KEY ENCRYPTION   │   │
│  │               │  │               │  │  (KEM/PKE)        │   │
│  │ Private: sign │  │ Both parties  │  │ Public: encrypt   │   │
│  │ Public: verify│  │ contribute to │  │ Private: decrypt  │   │
│  │               │  │ shared secret │  │                   │   │
│  │ ECDSA, EdDSA  │  │ ECDH, X25519  │  │ RSA-OAEP, Kyber   │   │
│  │ RSA-PSS       │  │ ECDHE in TLS  │  │                   │   │
│  └───────────────┘  └───────────────┘  └───────────────────┘   │
│                                                                │
│  Outputs:                                                      │
│  Signature → verification result (accept/reject)               │
│  Key agreement → shared secret (both parties derive same key)  │
│  KEM/PKE → ciphertext (decryptable only by private key owner)  │
└────────────────────────────────────────────────────────────────┘
```

**Signature.** Takes a message (or its hash) and a private key; produces a signature. Anyone with the corresponding public key can verify. The signature proves that the private key holder processed this exact message. Used in: secure boot, firmware signing, device certificates, TLS authentication.

**Key agreement.** Two parties each contribute a key material component (derived from their respective private keys and the other party's public key); the protocol produces identical shared secrets on both sides without either party transmitting the secret. Used in: TLS handshake, DTLS, EDHOC.

**Key encryption / KEM.** A sender encapsulates a random key using the recipient's public key; the recipient decapsulates using their private key. The encapsulated key is transmitted; only the private key holder can recover it. Used in: encrypted key transport, hybrid encryption, post-quantum transition schemes.

These three categories are the vocabulary of every protocol. When you read a protocol specification, identify which categories its components belong to before worrying about the specific algorithm.

> **Principle 3.** *Every asymmetric protocol operation is a signature, a key agreement, or a key encapsulation. If you cannot classify an operation into one of these three, you do not yet understand what the operation is for.*

---

## Chapter 4 — The Embedded Cost Model

Asymmetric operations are expensive. On an ARM Cortex-M4 at 168 MHz, a single P-256 ECDH scalar multiplication takes approximately 300–600 ms in software. An ECDSA signature verification takes 200–400 ms. An RSA-2048 signature verification takes 50–150 ms (verification is fast; signing is slow, 1–3 seconds). These are not per-byte costs — they are per-operation costs.

```
┌──────────────────────────────────────────────────────────────────┐
│    Asymmetric Operation Costs (ARM Cortex-M4, 168 MHz, SW)       │
│                                                                  │
│  Operation              │ Approx. Time  │ Notes                  │
│  ───────────────────────┼───────────────┼───────────────────────│
│  P-256 scalar mult      │ 300–600 ms    │ Dominates ECDH, ECDSA  │
│  P-256 ECDH (full)      │ 400–800 ms    │ Two scalar mults       │
│  ECDSA-P256 sign        │ 300–600 ms    │ Needs RNG              │
│  ECDSA-P256 verify      │ 300–600 ms    │ Two scalar mults       │
│  Ed25519 sign           │ 150–300 ms    │ Faster than ECDSA      │
│  Ed25519 verify         │ 300–500 ms    │ Two scalar mults       │
│  X25519 (one-side DH)   │ 150–300 ms    │ One scalar mult        │
│  RSA-2048 sign          │ 1000–3000 ms  │ Slow without CRT       │
│  RSA-2048 verify        │ 20–50 ms      │ Small public exponent  │
│  RSA-2048 keygen        │ 5000–20000 ms │ Slow; do at provision  │
│                                                                  │
│  With hardware PKA (e.g., STM32H5, NXP LPC55S69):               │
│  P-256 scalar mult      │ 3–20 ms       │ 20–100× speedup        │
│  RSA-2048 sign          │ 20–100 ms     │ 30–150× speedup        │
└──────────────────────────────────────────────────────────────────┘
```

The cost model has architectural consequences:

**Asymmetric operations happen at connection establishment, not per-packet.** Design protocols where the handshake (asymmetric) occurs once; subsequent communication uses symmetric keys derived from the handshake.

**Hardware PKA is not a luxury — it is often a necessity.** A 500 ms ECDH per connection is tolerable for a device that connects once per minute. It is not tolerable for a sensor that connects 10 times per second.

**Key generation is the most expensive single operation.** RSA key generation on constrained hardware can take 10–30 seconds. Never generate RSA keys in the field on bare MCUs without a hardware accelerator. Generate them at manufacturing time with an HSM.

**Verification is asymmetric to signing.** RSA verification with a small public exponent (e=65537) is fast; signing is slow. ECC signing and verification are roughly equal in cost (both require scalar multiplication). This matters for architecture: a device that only verifies firmware signatures (not signs) can use RSA-2048 at reasonable cost.

> **Principle 4.** *Asymmetric operations are per-connection costs, not per-byte costs. Design to minimize the number of asymmetric operations; use symmetric cryptography for everything else.*

---

## Chapter 5 — Asymmetric vs Symmetric: Roles, Not Rivals

The most common architectural mistake in embedded cryptography is treating asymmetric and symmetric crypto as alternatives. They are not. They are complementary — each does what the other cannot.

```
┌──────────────────────────────────────────────────────────────────┐
│             Asymmetric and Symmetric: Distinct Roles             │
├──────────────────────────────┬───────────────────────────────────┤
│       ASYMMETRIC             │          SYMMETRIC                │
├──────────────────────────────┼───────────────────────────────────┤
│ Key exchange (no prior       │ Bulk data encryption              │
│ shared secret needed)        │                                   │
├──────────────────────────────┼───────────────────────────────────┤
│ Device authentication        │ Message authentication (MAC)      │
│ (certificate-based)          │ (shared-secret-based)             │
├──────────────────────────────┼───────────────────────────────────┤
│ Firmware signing             │ Firmware encryption               │
├──────────────────────────────┼───────────────────────────────────┤
│ Session key establishment    │ Session data protection           │
├──────────────────────────────┼───────────────────────────────────┤
│ Happens once per connection  │ Happens for every packet          │
├──────────────────────────────┼───────────────────────────────────┤
│ Expensive per operation      │ Cheap per byte                    │
├──────────────────────────────┼───────────────────────────────────┤
│ Key: 256 bits (ECC) /        │ Key: 128–256 bits                 │
│      2048+ bits (RSA)        │                                   │
└──────────────────────────────┴───────────────────────────────────┘
```

The canonical embedded secure channel uses asymmetric crypto exactly once: to authenticate parties and derive a shared session key. All subsequent communication uses AES-GCM or ChaCha20-Poly1305 with that session key. TLS 1.3 is the reference implementation of this pattern.

A system that uses only asymmetric crypto — signing every packet, encrypting every byte with RSA — is over-engineered and non-functional on constrained hardware. A system that uses only symmetric crypto — pre-shared keys, no certificates — cannot scale to a fleet of a million devices with individual device identities.

The architecture question is always: which asymmetric operations are unavoidable, and how do I minimize them?

> **Principle 5.** *Asymmetric cryptography establishes trust once; symmetric cryptography maintains it continuously. A system that uses asymmetric crypto for bulk data, or symmetric crypto for initial trust establishment, has misunderstood both.*

---

# Part II — Anatomy

---

## Chapter 6 — Key Pairs: Public and Private

An asymmetric key pair is an inseparable unit: a private key and its corresponding public key, mathematically linked. Understanding the structure before learning the algorithms.

```
┌──────────────────────────────────────────────────────────────────┐
│                     Key Pair Anatomy                             │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                   PRIVATE KEY                            │   │
│   │                                                          │   │
│   │  A secret scalar (for ECC) or a pair of large primes    │   │
│   │  (for RSA). Never transmitted. Never revealed.           │   │
│   │  Stored in secure storage / hardware key store.          │   │
│   │  Size: 32 bytes (P-256/Ed25519), 256 bytes (RSA-2048)   │   │
│   └─────────────────────────┬───────────────────────────────┘   │
│                             │ One-way derivation                 │
│                             ▼ (cannot reverse)                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                   PUBLIC KEY                             │   │
│   │                                                          │   │
│   │  A point on the elliptic curve (for ECC) or the modulus │   │
│   │  + exponent (RSA). Freely shareable. Distributed in     │   │
│   │  certificates. Verified against a trust anchor.          │   │
│   │  Size: 64 bytes uncompressed (P-256), 33 bytes compressed│   │
│   │        32 bytes (Ed25519), 256+ bytes (RSA-2048)         │   │
│   └─────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

**The private key is a scalar.** For ECC, the private key is a random integer in the range [1, n-1] where n is the order of the curve. It is just a number — typically 32 bytes for 256-bit curves. Its security comes entirely from secrecy.

**The public key is derived, not chosen.** The public key is the result of scalar multiplication: `Q = d * G`, where d is the private key scalar, G is the generator point of the curve, and Q is the public key point. Given Q and G, recovering d requires solving the elliptic curve discrete logarithm problem — computationally infeasible for correctly chosen curves.

**Key pair properties:**

*Binding*: the private and public keys are mathematically bound. A signature made with the private key can only be verified with the corresponding public key. There is no substitute.

*Asymmetry of size*: ECC private keys are compact (32 bytes for P-256). RSA private keys are large (256+ bytes for RSA-2048). The size difference has direct RAM implications in embedded use.

*No key-to-key derivation*: unlike symmetric key hierarchies, you cannot derive a private key from another private key in a general, portable way. (BIP-32 HD wallets do this for specific curves with specific constructions — this is not general.) Each device has its own key pair, generated independently.

**Key formats on embedded systems:**

| Format | Description | Size (P-256) | Use |
|--------|-------------|-------------|-----|
| Raw scalar | Private key bytes only | 32 bytes | Internal storage |
| Uncompressed point | 0x04 ‖ x ‖ y | 65 bytes | Legacy interop |
| Compressed point | 0x02/0x03 ‖ x | 33 bytes | Preferred on constrained |
| DER SubjectPublicKeyInfo | ASN.1 wrapped | ~91 bytes | Certificates, TLS |
| PEM | Base64 + header | ~180 chars | Config files, not embedded |

> **Principle 6.** *A private key is a secret integer; its public key is an irreversible mathematical derivation of it. Protecting the private key is the entire security problem — the public key can be freely distributed.*

---

## Chapter 7 — Digital Signatures

A digital signature scheme has three algorithms: key generation, signing, and verification.

```
┌──────────────────────────────────────────────────────────────────┐
│                Digital Signature: Full Picture                   │
│                                                                  │
│  SIGNING (private key holder):                                   │
│                                                                  │
│  Message M ──► Hash(M) ──► H                                     │
│                             │                                    │
│  Private key d ────────────►│                                    │
│  Randomness k (ECDSA) ──────► Sign(d, H, [k]) ──► Signature S  │
│                                                                  │
│  Signature S = (r, s) for ECDSA/DSA                             │
│              = 64 bytes for Ed25519                              │
│              = 256 bytes for RSA-2048                            │
│                                                                  │
│  VERIFICATION (anyone with public key):                          │
│                                                                  │
│  Message M ──► Hash(M) ──► H                                     │
│                             │                                    │
│  Public key Q ─────────────►│                                    │
│  Signature S ───────────────► Verify(Q, H, S) ──► Accept/Reject │
│                                                                  │
│  No secret needed for verification.                              │
└──────────────────────────────────────────────────────────────────┘
```

A valid signature proves three things simultaneously:

1. **Origin**: the message was processed by the private key holder.
2. **Integrity**: the message has not been modified since signing.
3. **Non-repudiation**: the private key holder cannot later deny having signed.

A signature does not prove:
- That the private key holder is who the certificate claims (that requires certificate chain validation).
- That the message is current (that requires a timestamp or nonce in the message).
- That the key has not been compromised since signing.

**The hash-then-sign construction** is universal: the signing algorithm always operates on the hash of the message, not the message itself. This serves two purposes: fixed-size input to the signing algorithm (required for ECC) and binding to the hash algorithm (a signature over SHA-256(M) cannot be repurposed as a signature over SHA-256(M') without breaking SHA-256).

The hash algorithm is part of the signature algorithm identifier. ECDSA-with-SHA256 and ECDSA-with-SHA384 produce signatures under the same private key but with different binding properties. Always specify the full algorithm identifier; never assume the hash.

> **Principle 7.** *A digital signature proves origin and integrity under the assumption that the private key is secret. It proves nothing about the legitimacy of the key holder — that requires certificate chain validation.*

---

## Chapter 8 — Key Agreement

Key agreement is the mechanism by which two parties derive an identical shared secret without either party transmitting it. The shared secret is never present in the channel — it is computed independently on both sides.

```
┌──────────────────────────────────────────────────────────────────┐
│              Diffie-Hellman Key Agreement                        │
│                                                                  │
│  ALICE                              BOB                         │
│  Private: a                         Private: b                  │
│  Public: A = a*G                    Public: B = b*G             │
│                                                                  │
│           A ──────────────────────────────► Bob receives A      │
│  Alice receives B ◄────────────────────── B                     │
│                                                                  │
│  Alice computes: S = a * B = a * (b * G) = (a*b) * G            │
│  Bob computes:   S = b * A = b * (a * G) = (a*b) * G            │
│                                                                  │
│  Both derive S = (a*b) * G   ← same point, neither transmitted  │
│                                                                  │
│  S is the shared secret. Derive symmetric keys from S via KDF.  │
│                                                                  │
│  An eavesdropper sees A and B but cannot compute S without       │
│  knowing a or b (discrete logarithm problem).                   │
└──────────────────────────────────────────────────────────────────┘
```

Key agreement is not encryption. No data is encrypted during the DH exchange. The result — the shared secret S — is used as input to a KDF to derive symmetric keys for subsequent AEAD encryption.

Key agreement is not authenticated by itself. An unauthenticated DH exchange is vulnerable to man-in-the-middle attack: an attacker can substitute their own public key for either party's, establish separate shared secrets with each party, and relay messages while decrypting everything. Authentication requires combining DH with signatures or certificates — exactly what TLS 1.3's authenticated key exchange does.

**The two kinds of key agreement in embedded protocols:**

*Static DH*: one or both parties use long-lived key pairs. The shared secret is deterministic — the same two parties always derive the same secret. Fast (no key generation at handshake time) but lacks forward secrecy.

*Ephemeral DH (DHE)*: both parties generate fresh key pairs for each session. The shared secret is different every session. Provides forward secrecy — compromise of long-term keys does not expose past sessions. More expensive (key generation per session).

> **Principle 8.** *Key agreement derives a shared secret without transmitting it; without authentication, it is vulnerable to man-in-the-middle. Never deploy unauthenticated key agreement.*

---

## Chapter 9 — Public-Key Encryption and Key Encapsulation

Public-key encryption (PKE) and Key Encapsulation Mechanisms (KEM) are the third primitive category. They differ from key agreement in a fundamental way: only one party contributes entropy to the shared secret.

```
┌──────────────────────────────────────────────────────────────────┐
│      Key Agreement vs Key Encapsulation                          │
│                                                                  │
│  KEY AGREEMENT (both parties active):                            │
│  Alice ──── ephemeral key pair ────► shared secret ◄──── Bob    │
│             Alice's private key      (both compute)    Bob's     │
│             + Bob's public key                        private    │
│                                                       key +      │
│                                                       Alice's    │
│                                                       public key │
│                                                                  │
│  KEY ENCAPSULATION (sender chooses):                             │
│  Alice generates random key K                                    │
│  Alice encapsulates K with Bob's public key ──► (K, ciphertext) │
│  Alice sends ciphertext ──────────────────────────────► Bob      │
│  Bob decapsulates with private key ──────────────────► K        │
│                                                                  │
│  Only Alice's randomness determines K.                           │
│  Bob has no entropy input (this matters for KEM properties).    │
└──────────────────────────────────────────────────────────────────┘
```

**RSA-OAEP** is the standard PKE scheme for RSA. It encrypts a short message (typically a symmetric key) under the recipient's RSA public key. The recipient decrypts with their private key. RSA-OAEP is correct; plain RSA (textbook RSA, no padding) is not — it is deterministic and malleable. Only ever use RSA-OAEP, never raw RSA.

**KEM** is the modern abstraction. Post-quantum schemes (Kyber/ML-KEM) are defined as KEMs rather than as PKE schemes, because the lattice-based constructions map more naturally to the KEM interface. The KEM interface — `(key, ciphertext) = Encaps(public_key)`, `key = Decaps(private_key, ciphertext)` — is also cleaner for hybrid schemes.

In embedded systems, PKE/KEM appears primarily in:
- Key transport in asymmetric provisioning protocols (wrapping a symmetric root key under the device's public key)
- Post-quantum hybrid key exchange
- Encrypted device configuration delivery

> **Principle 9.** *In key encapsulation, the sender chooses the shared secret unilaterally; in key agreement, both parties contribute entropy. For fresh shared secrets with forward secrecy, key agreement is preferred.*

---

## Chapter 10 — Certificates and Binding

A certificate binds a public key to an identity. Without this binding, a public key is just a number — there is no way to know whether it belongs to the legitimate device or to an attacker.

```
┌──────────────────────────────────────────────────────────────────┐
│                 X.509 Certificate Structure                      │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   TBSCertificate                         │   │
│  │  (the content that is signed)                            │   │
│  │                                                          │   │
│  │  Subject: CN=Device-12345, O=Acme Corp                  │   │
│  │  Issuer:  CN=Acme Device CA, O=Acme Corp                 │   │
│  │  Serial Number: 0x0042                                   │   │
│  │  Validity: NotBefore=2024-01-01  NotAfter=2026-01-01     │   │
│  │  Subject Public Key: P-256 point (65 bytes uncompressed) │   │
│  │  Extensions: KeyUsage, SubjectKeyIdentifier, ...         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│                           │ Signed by CA's private key          │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Signature: ECDSA-with-SHA256 over TBSCertificate hash   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Certificate = TBSCertificate + Signature Algorithm + Signature │
└──────────────────────────────────────────────────────────────────┘
```

The certificate is a signed statement by a Certificate Authority (CA): "I have verified that the entity named Subject owns the private key corresponding to this public key." The CA's signature makes the certificate self-authenticating — anyone who trusts the CA can verify the certificate without contacting the CA.

**The certificate is not the identity.** It is a claim about identity, vouched for by the CA. The claim is trustworthy to the extent that the CA's validation process is trustworthy. For embedded device certificates, this means the certificate is trustworthy to the extent that the manufacturing provisioning process is trustworthy — because the CA signs whatever the factory presents.

**Critical certificate fields for embedded systems:**

*Subject Alternative Name (SAN)*: the machine-readable identifier. Use SAN with DNS names or URI types for device IDs. The Common Name (CN) in the Subject is deprecated for identity in TLS.

*Key Usage and Extended Key Usage*: constrain what the key can be used for. A device authentication certificate should have `digitalSignature` in Key Usage and `clientAuth` in Extended Key Usage. A firmware signing certificate should have `digitalSignature` and code signing EKU. Certificates without Key Usage constraints can be misused.

*Validity period*: certificates expire. A device that cannot validate certificate expiry (no clock) or renew expiring certificates (no connectivity) will eventually fail. This is the operational problem Chapter 51 addresses.

> **Principle 10.** *A certificate is a CA's signed statement binding a public key to an identity. The certificate's trustworthiness is bounded by the CA's validation process — which, for device certificates, is bounded by the factory's provisioning security.*

---

## Chapter 11 — Signature vs Encryption: The Dangerous Inversion

Two conflations recur among architects new to asymmetric crypto. This chapter addresses both.

**Conflation 1: Using a private key to encrypt.**

RSA has a mathematical structure that allows both signing and encryption using the same key pair. Naively, one might reason: "the private key is secret, so encrypt with it to prove identity." This is wrong. Signing with a private key means: "I computed a transformation of this message using my secret." Encrypting with a private key means: "anyone with my public key can decrypt this." Encryption with a private key provides zero confidentiality — the public key is public.

The correct operations:
- Encrypt: use the *recipient's public key*. Only the recipient (holding the private key) can decrypt.
- Sign: use *your own private key*. Anyone with your public key can verify.

```
┌──────────────────────────────────────────────────────────────────┐
│            Key Usage: Who Uses Which Key                         │
│                                                                  │
│  OPERATION    │ USES WHOSE KEY │ WHICH KEY  │ PURPOSE            │
│  ─────────────┼────────────────┼────────────┼────────────────   │
│  Encrypt      │ Recipient's    │ Public     │ Confidentiality   │
│  Decrypt      │ Recipient's    │ Private    │ (recover message) │
│  Sign         │ Signer's own   │ Private    │ Authenticity      │
│  Verify       │ Signer's       │ Public     │ (confirm origin)  │
└──────────────────────────────────────────────────────────────────┘
```

**Conflation 2: Reusing the same key pair for signing and encryption.**

Key pairs should have dedicated purposes. A key pair used for TLS authentication (signing) should not be reused for key encapsulation (encryption). The cryptographic protocols for signing and encryption make different assumptions about the key usage pattern; mixing them creates subtle vulnerabilities. More concretely, certificate extensions exist precisely to constrain key usage — a certificate with `KeyUsage = digitalSignature` should not be used for `KeyEncipherment`.

> **Principle 11.** *Encrypt to the recipient's public key; sign with your own private key. Never reverse these. Never reuse a signing key pair for encryption.*

---

## Chapter 12 — Authentication vs Authorization

Authentication answers: "Is this the device it claims to be?" Authorization answers: "Is this device permitted to perform this action?" Asymmetric cryptography handles authentication. Authorization is the responsibility of the application layer, informed by authentication results.

A device presenting a valid certificate with a valid signature is authenticated. Whether it is authorized to receive a firmware update, access a specific sensor endpoint, or modify device configuration depends on policy, not cryptography.

The dangerous assumption is that authentication implies authorization. A device that authenticates successfully as "Device-12345" is not thereby authorized to pose as "Device-12346" or to receive another device's private data. The application must check authorization after successful authentication.

In embedded fleet deployments, this distinction manifests in:

*Cloud endpoint access control*: the backend authenticates each device by its certificate. The backend then checks the device's serial number against a database of permitted operations before executing commands.

*Firmware update authorization*: a device authenticates a firmware update package by verifying the firmware signing certificate. The device separately checks that the firmware version is newer than the current version (anti-rollback) — this is an authorization check.

*Peer authentication in mesh networks*: two devices authenticate each other mutually. One device's authorization to control another is a separate policy decision, not implied by the mutual authentication.

> **Principle 12.** *Authentication proves identity; authorization grants permission. Asymmetric cryptography handles the first. The second requires policy enforcement at the application layer.*

---

# Part III — Configuration and Composition

---

## Chapter 13 — Key Sizes and Security Levels

Key sizes in asymmetric cryptography are not directly comparable across algorithm families. A 256-bit ECC key provides the equivalent of 128-bit symmetric security; a 3072-bit RSA key provides approximately 128-bit symmetric security. The numbers mean different things.

```
┌──────────────────────────────────────────────────────────────────┐
│              Key Size Equivalence Table                          │
│                                                                  │
│  Symmetric   │  ECC (NIST)  │  RSA/DH     │ Post-Quantum        │
│  Security    │  Key Size    │  Key Size   │ (NIST Level)        │
│  ────────────┼──────────────┼─────────────┼───────────────────  │
│  80 bits     │  P-192       │  1024 bits  │ —                   │
│  112 bits    │  P-224       │  2048 bits  │ —                   │
│  128 bits    │  P-256       │  3072 bits  │ ML-KEM-512 (L1)     │
│  192 bits    │  P-384       │  7680 bits  │ ML-KEM-768 (L3)     │
│  256 bits    │  P-521       │  15360 bits │ ML-KEM-1024 (L5)    │
│                                                                  │
│  Against quantum computers:                                      │
│  P-256 → broken (Shor's algorithm)                               │
│  RSA-2048 → broken (Shor's algorithm)                            │
│  AES-128 → 64-bit quantum security (Grover)                      │
│  ML-KEM-512 → ~128-bit quantum security (believed)               │
└──────────────────────────────────────────────────────────────────┘
```

**The recommendation for embedded systems (2024):**

- **Default**: P-256 (ECDSA/ECDH) + AES-128. Provides 128-bit classical security. Hardware acceleration widely available on ARM Cortex-M33+. Used in TLS 1.3, BLE, Thread, Matter.
- **Long-lived devices (10+ year deployments)**: Consider P-384 for signing keys, or plan a migration path to post-quantum algorithms.
- **Compliance-mandated RSA**: RSA-2048 minimum (RSA-3072 for NIST guidelines beyond 2030). Use for firmware signing on targets with hardware RSA accelerators.
- **Post-quantum**: ML-KEM-512 + ML-DSA-44 as hybrid partners to P-256 + ECDSA. Do not deploy post-quantum alone yet — the algorithm maturity is lower than ECC.

**Key size and ROM/RAM cost:**

| Algorithm | Private Key | Public Key | Signature | RAM for Op |
|-----------|-------------|-----------|-----------|------------|
| P-256 | 32 bytes | 64 bytes | 64 bytes | 4–8 KB |
| P-384 | 48 bytes | 96 bytes | 96 bytes | 6–10 KB |
| Ed25519 | 32 bytes | 32 bytes | 64 bytes | 4–6 KB |
| RSA-2048 | 256 bytes | 256 bytes | 256 bytes | 8–16 KB |
| RSA-3072 | 384 bytes | 384 bytes | 384 bytes | 12–24 KB |
| ML-KEM-512 | 1632 bytes | 800 bytes | — | 20–40 KB |
| ML-DSA-44 | 2528 bytes | 1312 bytes | 2420 bytes | 30–50 KB |

> **Principle 13.** *P-256 provides 128-bit classical security with 256-bit key material; RSA-2048 provides 112-bit classical security with 2048-bit key material. ECC is the correct default for constrained hardware.*

---

## Chapter 14 — Key Generation: Randomness and Curve Selection

Key generation quality determines the security of the entire system. A weak key generation process is a systemic vulnerability that affects every device produced.

**For ECC private key generation:**

The private key d must be a uniformly random integer in [1, n-1] where n is the curve order. For P-256, n is a 256-bit integer. The private key must be generated using a cryptographically secure random number generator (CSPRNG) seeded from hardware entropy (TRNG).

The simple approach: generate 32 random bytes from the TRNG-seeded DRBG and interpret them as an integer modulo n. The probability that the result is 0 or ≥ n is negligible for 256-bit curves. Most implementations use rejection sampling (generate, test if in range, repeat if not) for correctness.

```
Key generation (P-256):
1. Seed DRBG from TRNG (wait for TRNG health test)
2. Generate 32 bytes from DRBG
3. Interpret as 256-bit integer d
4. If d == 0 or d >= n: go to step 2 (negligible probability)
5. Compute Q = d * G (scalar multiplication)
6. Store (d, Q) as private, public key pair
7. Zeroize intermediate values from RAM
```

**For Ed25519 key generation:**

Ed25519 private keys are 32 random bytes. The actual signing scalar is derived by hashing the private key with SHA-512. This design means the "private key" as stored is not the scalar used in computation — it is the seed from which the scalar is derived. This provides clamping (certain bits are set/cleared) and avoids the need for rejection sampling.

**Key generation failure modes on embedded devices:**

*TRNG not ready at boot*: generating keys before the TRNG has accumulated entropy. The result is predictable keys. Always check TRNG health-test status before generating key material.

*Biased DRBG*: some embedded DRBG implementations have implementation errors that produce biased output. Use a well-tested library (Mbed TLS CTR-DRBG with hardware entropy source, WolfSSL with hardware TRNG).

*Flash seed replay*: if the DRBG seed is stored in flash across power cycles and is not updated before use, power cycling the device to the same state produces the same key. Seed from TRNG on every boot; do not rely on NVM-only seeds for key generation.

> **Principle 14.** *A private key is only as random as the entropy source that generated it. TRNG quality at the moment of key generation determines key security for the device's lifetime.*

---

## Chapter 15 — Certificate Structure and Fields

X.509 certificates are DER-encoded ASN.1 structures. Every embedded system that parses, stores, or validates certificates must handle these bytes correctly.

```
Certificate DER layout (schematic, P-256 device certificate):

SEQUENCE {                              ← Certificate
  SEQUENCE {                            ← TBSCertificate
    [0] INTEGER 2                       ← Version: v3
    INTEGER <serial>                    ← Serial number
    SEQUENCE { OID, NULL }              ← Signature algorithm
    SEQUENCE { ... }                    ← Issuer name
    SEQUENCE {                          ← Validity
      UTCTime "240101000000Z"           ← Not before
      UTCTime "260101000000Z"           ← Not after
    }
    SEQUENCE { ... }                    ← Subject name
    SEQUENCE {                          ← SubjectPublicKeyInfo
      SEQUENCE { OID ecPublicKey,       ← Algorithm
                 OID prime256v1 }
      BIT STRING <04 || x || y>         ← Uncompressed public key
    }
    [3] SEQUENCE {                      ← Extensions
      SEQUENCE { OID subjectKeyId, ... }
      SEQUENCE { OID keyUsage, BOOLEAN TRUE, OCTET STRING ... }
      SEQUENCE { OID extKeyUsage, ... }
    }
  }
  SEQUENCE { OID ecdsa-with-SHA256 }    ← Signature algorithm
  BIT STRING <r || s DER-encoded>       ← Signature
}
```

**Sizes for embedded storage planning:**

A typical P-256 device certificate is 400–600 bytes in DER format. A root CA certificate may be 300–500 bytes. A certificate chain of three levels (root + intermediate + device) occupies 1.2–1.8 KB. This fits in RAM on most ARM Cortex-M targets, but must be budgeted explicitly.

**Fields critical for embedded validation:**

*Version*: must be 3 (INTEGER 2 in DER) for certificates with extensions. A v1 certificate has no extensions; do not issue v1 certificates for embedded device identity.

*Serial number*: must be unique per CA. Use at least 64 random bits (NIST recommendation). Do not use sequential integers — they aid enumeration attacks.

*Validity period*: the pair (NotBefore, NotAfter) that the verifier compares against current time. If the device has no clock, this check cannot be performed correctly. Chapter 51 addresses this.

*Key Usage extension*: must be present and marked critical for device identity certificates. `digitalSignature` for authentication; `keyAgreement` for ECDH. Do not issue certificates with unconstrained key usage.

*Subject Alternative Name*: the preferred identity field. For embedded devices: `URI:urn:device:serial:12345` or `DNS:device-12345.acme.com`.

> **Principle 15.** *Every certificate field is a security parameter; unconstrained key usage, missing SANs, and weak serial numbers each reduce the security the certificate provides.*

---

## Chapter 16 — Certificate Chains and Trust Anchors

No device embeds the root CA certificate of every possible CA. Instead, devices embed one or a small number of trust anchors — root CA certificates they explicitly trust — and verify that presented certificates chain back to a trusted anchor.

```
┌──────────────────────────────────────────────────────────────────┐
│              Certificate Chain Verification                      │
│                                                                  │
│  TRUST ANCHOR (embedded in device firmware):                     │
│  ┌─────────────────────────────────────────────┐                │
│  │  Root CA Certificate                         │                │
│  │  Self-signed: Issuer == Subject              │                │
│  │  Public key: trusted unconditionally         │                │
│  └──────────────────┬──────────────────────────┘                │
│                     │ Signs                                      │
│                     ▼                                            │
│  ┌─────────────────────────────────────────────┐                │
│  │  Intermediate CA Certificate (optional)      │                │
│  │  Verified using Root CA public key           │                │
│  └──────────────────┬──────────────────────────┘                │
│                     │ Signs                                      │
│                     ▼                                            │
│  ┌─────────────────────────────────────────────┐                │
│  │  Device / Server Certificate                 │                │
│  │  Verified using Intermediate CA public key   │                │
│  │  Contains the entity's public key            │                │
│  └─────────────────────────────────────────────┘                │
│                                                                  │
│  Verification: each cert's signature verified by the issuer's   │
│  public key, up to the trust anchor.                             │
│  Trust anchor verified by comparing its hash to embedded value. │
└──────────────────────────────────────────────────────────────────┘
```

**The trust anchor is not verified cryptographically — it is trusted by policy.** The device firmware embeds the trust anchor's public key or DER-encoded certificate. Any update to the trust anchor requires a firmware update. This is the hardware root of trust for the PKI.

**Key validation rules:**

1. Each certificate's signature must be valid under the issuer's public key.
2. Each certificate's `Issuer` field must match the issuer certificate's `Subject` field.
3. The chain must terminate at an embedded trust anchor.
4. Each certificate's validity period must be current (if the device has a clock).
5. Each CA certificate in the chain must have the `CA:TRUE` Basic Constraints extension.
6. Key Usage extensions must be consistent with the certificate's role.

**Embedded chain validation is typically minimal.** Full RFC 5280 path validation includes many additional checks (name constraints, policy constraints, CRL/OCSP checking) that are impractical on constrained devices. Define explicitly which checks you implement and which you omit, and document the security consequence of each omission.

> **Principle 16.** *The trust anchor is the device's unconditional belief; every other certificate in the chain is verified against it. An attacker who controls the trust anchor controls all authentication.*

---

## Chapter 17 — Key Lifetimes and Certificate Validity

Every key and certificate has a finite lifetime. Planning for lifetime events — expiry, rotation, revocation — is a production requirement, not an afterthought.

**Key lifetime guidance:**

| Key Type | Recommended Lifetime | Rationale |
|----------|---------------------|-----------|
| Root CA key | 10–20 years | Changing requires firmware update to all devices |
| Intermediate CA key | 3–5 years | Balance: manageable rotation, limited blast radius |
| Device identity key | 3–10 years | Match device deployment lifetime |
| Firmware signing key | 1–3 years | Rotated by updating CA certificate in firmware |
| Session keys (TLS) | Session duration | Ephemeral; never stored |

**The certificate renewal problem on embedded devices:**

A device deployed in the field with a certificate that expires in 2 years will, in 2 years, stop authenticating. If the device has no mechanism to renew its certificate — no network connectivity at that moment, no automated renewal client, no OTA update carrying the new certificate — it bricks itself cryptographically.

Solutions, in order of preference:
1. Use long-validity device identity certificates (5–10 years) matched to deployment lifetime.
2. Implement automated certificate renewal (EST protocol, RFC 7030) in firmware.
3. Deliver new certificates via OTA firmware update.
4. Use certificate pinning with an expiry-check bypass when offline (security policy decision).

**Key rotation for firmware signing:**

The firmware signing key cannot be rotated by delivering a new key in a signed firmware image — that is circular. The trust anchor for firmware signing is embedded in the bootloader. To rotate it, ship a firmware update signed by the current key that updates the embedded trust anchor, then rotate. This requires careful sequencing and cannot be reversed.

> **Principle 17.** *A certificate that expires during deployment causes a silent authentication failure. Certificate lifetimes must be planned against deployment duration, with renewal mechanisms implemented before the device ships.*

---

## Chapter 18 — Algorithm Identifiers and OIDs

Asymmetric algorithms are identified by Object Identifiers (OIDs), not by algorithm names. Every certificate, every CMS signature, every ASN.1 structure uses OIDs. Embedded parsers must map OIDs to implementations; using the wrong OID produces silent failures.

```
Critical OIDs for embedded asymmetric crypto:

Signature Algorithms:
1.2.840.10045.4.3.2  ecdsa-with-SHA256  (ECDSA + P-256 typically)
1.2.840.10045.4.3.3  ecdsa-with-SHA384
1.2.840.10045.4.3.4  ecdsa-with-SHA512
1.2.840.113549.1.1.11  sha256WithRSAEncryption  (RSA-PKCS1v1.5 + SHA256)
1.2.840.113549.1.1.13  sha512WithRSAEncryption
1.2.840.113549.1.1.10  id-RSASSA-PSS  (RSA-PSS, parameters separate)

Public Key Algorithms:
1.2.840.10045.2.1     id-ecPublicKey   (all ECC curves)
1.3.132.0.34          secp384r1        (curve OID in AlgorithmIdentifier)
1.2.840.10045.3.1.7   prime256v1       (P-256 curve OID)
1.2.840.113549.1.1.1  rsaEncryption

Named Curves:
1.2.840.10045.3.1.7   prime256v1 (P-256)
1.3.132.0.34          secp384r1  (P-384)
1.3.101.110           id-X25519  (X25519 key agreement)
1.3.101.112           id-Ed25519 (Ed25519 signature)
```

**The OID-to-algorithm mapping is the source of silent interoperability failures.** An embedded parser that only recognizes `ecdsa-with-SHA256` will silently fail when presented with an `ecdsa-with-SHA384` certificate — not with an error indicating the algorithm mismatch, but often with a generic "invalid certificate" or "signature verification failed."

When implementing a parser, enumerate the supported OIDs explicitly and return a clear error for unsupported OIDs. Never silently skip unknown extensions or algorithm identifiers — log them or reject them.

**EdDSA OIDs:** Ed25519 uses `1.3.101.112` as a signature algorithm OID. Importantly, this OID encodes both the signing algorithm and the hash function — Ed25519 uses a fixed hash function (SHA-512 internally) and the OID does not take separate hash parameters. Parsers that expect a hash OID alongside the signature OID will fail on Ed25519 certificates.

> **Principle 18.** *OIDs are the name of the algorithm in the protocol; an unrecognized OID must produce an explicit error, not silent incorrect behavior. Always enumerate supported OIDs and reject others.*

---

# Part IV — Mathematical Internals

---

## Chapter 19 — Groups, Hardness, and the Discrete Log Problem

Every asymmetric cryptosystem is built on a group with a hard computational problem. Understanding this one structure makes every algorithm intelligible.

A **group** is a set G with an operation (call it addition +) satisfying: closure, associativity, an identity element (0), and inverses. For cryptography, we need a group where:

1. Computing `n * g` (n copies of g added to itself, for large n and group element g) is easy.
2. Given `n * g` and `g`, recovering `n` is hard.

Property 2 is the **discrete logarithm problem** (DLP). The scalar n is the private key; the group element `n * g` is the public key; recovering n from the public key is the hard problem that protects the system.

```
┌──────────────────────────────────────────────────────────────────┐
│           Group, DLP, and Cryptosystem                           │
│                                                                  │
│  Group examples:                                                 │
│  ┌───────────────┬──────────────────┬──────────────────────────┐ │
│  │ Group         │ Operation        │ Cryptosystem             │ │
│  ├───────────────┼──────────────────┼──────────────────────────┤ │
│  │ Integers mod  │ Multiplication   │ Classical DH, RSA        │ │
│  │ prime p       │ mod p            │ (Z/pZ)*                  │ │
│  ├───────────────┼──────────────────┼──────────────────────────┤ │
│  │ Points on     │ Point addition   │ ECDH, ECDSA, EdDSA       │ │
│  │ elliptic curve│ (geometric rule) │ ECC family               │ │
│  ├───────────────┼──────────────────┼──────────────────────────┤ │
│  │ Lattice       │ Vector addition  │ Kyber, Dilithium         │ │
│  │ cosets        │ in Z^n           │ Post-quantum family      │ │
│  └───────────────┴──────────────────┴──────────────────────────┘ │
│                                                                  │
│  Security comes from: best known algorithm to solve DLP          │
│  for each group determines the required key size.                │
└──────────────────────────────────────────────────────────────────┘
```

**Why elliptic curve groups are better than modular integer groups for embedded:** In the modular integer group (Z/pZ)*, the best known DLP algorithm is the General Number Field Sieve (GNFS), which runs in sub-exponential time. This forces large parameters: a 3072-bit modulus for 128-bit security. In elliptic curve groups, no sub-exponential algorithm is known (for properly chosen curves), and the best known attack is the Baby-Step Giant-Step algorithm at O(√n) time. This gives 128-bit security from a 256-bit group — much more compact.

**Lattices are different.** Post-quantum schemes based on lattices (CRYSTALS-Kyber, CRYSTALS-Dilithium) use a different hard problem: Learning With Errors (LWE), which is believed to be hard even for quantum computers. The key sizes are larger than ECC but smaller than RSA for equivalent quantum-resistant security.

> **Principle 19.** *Asymmetric security is the hardness of a group problem; the group choice determines key size requirements, performance, and quantum vulnerability. ECC groups provide the best classical security per bit; lattice groups provide post-quantum security.*

---

## Chapter 20 — Elliptic Curves: The Geometry

An elliptic curve over a finite field is a set of points satisfying the equation:

```
y² = x³ + ax + b   (mod p, for prime-field curves)
```

plus a special "point at infinity" ∞ that acts as the group identity.

```
┌──────────────────────────────────────────────────────────────────┐
│          Elliptic Curve: Real-Number Visualization               │
│          (actual arithmetic is over finite field Fp)             │
│                                                                  │
│   y                                                              │
│   │         *  *                                                 │
│   │       *      *                                               │
│   │      *        *     ← curve points                          │
│   │       *      *                                               │
│   │         *  *                                                 │
│   │ ─────────────────── x                                        │
│   │         *  *                                                 │
│   │       *      *                                               │
│   │      *        *                                              │
│   │       *      *                                               │
│   │         *  *                                                 │
│                                                                  │
│  For P-256 over F_p (p is a 256-bit prime):                      │
│  y² ≡ x³ - 3x + b (mod p)                                       │
│  where a = -3, b is a specific 256-bit constant                  │
│                                                                  │
│  Points are pairs (x, y) satisfying the equation,               │
│  where x, y ∈ {0, 1, ..., p-1}                                  │
└──────────────────────────────────────────────────────────────────┘
```

The group has approximately p points (by Hasse's theorem, within √p of p). The order n of the group (the number of points) is approximately p. For P-256, n is a 256-bit prime.

**The generator point G** is a specific point on the curve, defined as part of the curve parameters. It generates the entire group: repeatedly adding G to itself produces every point in the group. The curve parameters (p, a, b, G, n) are fixed and public; they are the curve definition.

**Curve parameters are not secret.** P-256's parameters are defined in FIPS 186-4. X25519's parameters are defined in RFC 7748. They are published, standardized, and used by everyone. Only the private key scalar is secret.

**Why curve choice matters:** The security of ECC depends on the specific curve. Some curves have mathematical structure that enables faster attacks (anomalous curves, supersingular curves, Weil-descent-vulnerable curves). The standardized curves (P-256, P-384, X25519, Ed25519) have been designed or selected to avoid these weaknesses. Never use a custom curve; never use a non-standardized curve in production.

> **Principle 20.** *The security of ECC is the security of the specific curve, not of ECC in general. Use only standardized curves: P-256, P-384, X25519, Ed25519. Curve creation is not for practitioners.*

---

## Chapter 21 — Elliptic Curve Arithmetic: Point Addition

Point addition is the fundamental operation that enables all ECC. Understanding it makes scalar multiplication — and its timing vulnerabilities — clear.

The point addition rule: given two points P = (x₁, y₁) and Q = (x₂, y₂) on the curve, their sum R = P + Q is defined geometrically: draw the line through P and Q, find the third intersection with the curve, and reflect over the x-axis.

```
Point addition formulas (affine coordinates, P ≠ Q):
λ = (y₂ - y₁) / (x₂ - x₁)  mod p
x₃ = λ² - x₁ - x₂           mod p
y₃ = λ(x₁ - x₃) - y₁         mod p

Point doubling (P = Q):
λ = (3x₁² + a) / (2y₁)       mod p
x₃ = λ² - 2x₁                mod p
y₃ = λ(x₁ - x₃) - y₁         mod p
```

The division operations (mod p) are modular inversions, which are expensive — each costs roughly as much as a full multiplication. Projective coordinates (Jacobian or homogeneous) eliminate the need for inversions during intermediate operations, performing one inversion at the end. This is the primary optimization in efficient ECC implementations.

**The point-at-infinity special case:** If P = Q and y₁ = 0, then doubling gives the point at infinity. If P and Q are inverses (x₁ = x₂, y₁ = -y₂), addition gives the point at infinity. These edge cases must be handled explicitly in implementations. Failing to handle them correctly produces incorrect results on rare inputs — which may be exploited by an attacker who can craft inputs.

**Why this matters for implementation:** Point addition and doubling have different code paths in affine coordinates. A naive scalar multiplication implementation that branches on whether it is adding or doubling creates a timing side channel — the attacker can infer the private key bit by observing which operation is performed at each step.

> **Principle 21.** *Point addition and doubling have different formulas; implementing them with separate code paths creates a timing side channel. Use unified addition formulas or constant-time scalar multiplication algorithms.*

---

## Chapter 22 — Scalar Multiplication and Its Cost

Scalar multiplication — computing `Q = d * G` for private key scalar d — is the core operation of ECC. It is expensive. Understanding why and how it is computed determines implementation choices.

```
Scalar multiplication: d * G for 256-bit d

Naive double-and-add algorithm:
  Q = ∞  (identity)
  for bit i from 255 downto 0:
    Q = 2*Q         ← always double
    if d_i == 1:
      Q = Q + G     ← conditional add

Total: 256 doublings + ~128 additions (expected)
       = ~384 point operations
       = ~384 * (modular mult cost)
       ≈ 300,000 – 600,000 multiplications mod p

For 32-bit MCU: ~300–600 ms software, ~3–20 ms hardware accelerator
```

**Side-channel vulnerability of naive double-and-add:** The conditional branch `if d_i == 1` executes a different code path depending on the private key bit. Power analysis or timing measurement reveals which bits are 1 — the entire private key leaks.

**Constant-time algorithms:**

*Montgomery ladder*: processes every bit identically, always performing two operations per bit. The two operations are a point addition and a point doubling, but which is Q+G and which is 2Q alternates based on the bit, in a way that is computationally equivalent but constant-time:

```
Montgomery ladder:
  R0 = G, R1 = 2*G
  for bit i from 254 downto 0:
    if d_i == 0:
      R1 = R0 + R1; R0 = 2*R0   (conditional swap, then double+add)
    else:
      R0 = R0 + R1; R1 = 2*R1
  return R0

Constant-time: both branches perform one doubling and one addition.
Conditional swap: implemented as constant-time select, no branch.
```

*Fixed-window methods*: precompute small multiples of G, then process d in w-bit windows. Reduces the number of additions at the cost of precomputation and storage.

For embedded implementations without hardware acceleration: use the Montgomery ladder or a constant-time windowed method. Never use the naive double-and-add. For implementations with hardware acceleration: verify that the hardware itself is constant-time (check the datasheet's security claims).

> **Principle 22.** *The naive double-and-add scalar multiplication algorithm leaks the private key bit by bit through timing or power analysis. Always use a constant-time scalar multiplication algorithm.*

---

## Chapter 23 — RSA: Factoring and the Trapdoor

RSA is based on a different hard problem: integer factorization. Given a large integer N = p × q where p and q are large primes, recovering p and q from N alone is computationally hard.

```
┌──────────────────────────────────────────────────────────────────┐
│                     RSA Construction                             │
│                                                                  │
│  Key Generation:                                                 │
│  1. Choose large primes p, q (each 1024 bits for RSA-2048)       │
│  2. N = p × q              (the modulus, 2048 bits)             │
│  3. φ(N) = (p-1)(q-1)      (Euler's totient, secret)           │
│  4. e = 65537              (public exponent, small)              │
│  5. d = e⁻¹ mod φ(N)       (private exponent)                   │
│                                                                  │
│  Public key: (N, e)                                              │
│  Private key: (N, d) — or (p, q, e, d, dP, dQ, qInv) with CRT  │
│                                                                  │
│  Operations:                                                     │
│  Encrypt/Verify: c = m^e mod N  (fast with small e)             │
│  Decrypt/Sign:   m = c^d mod N  (slow; d is large)              │
│                                                                  │
│  Security: factoring N reveals φ(N), which reveals d.           │
│  Best known factoring: GNFS, sub-exponential in N bits.         │
│  Implication: RSA needs ~3072 bits for 128-bit security.         │
└──────────────────────────────────────────────────────────────────┘
```

**RSA on embedded systems is a legacy concern.** RSA-2048 keys are 256 bytes; RSA-3072 keys are 384 bytes. RSA signing requires computing m^d mod N where d is a ~2048-bit exponent — this is slow without Chinese Remainder Theorem optimization and hardware acceleration.

**When RSA is unavoidable:**

*Firmware verification in secure boot*: many deployed devices use RSA because hardware RSA verifiers were integrated before ECC was widely supported. RSA-2048 verification with e=65537 is fast — 20–50 ms in software — making it practical for bootloader use.

*Compliance requirements*: some certifications and procurement requirements specify RSA-2048 or RSA-3072.

*Interoperability with existing infrastructure*: CA certificates issued before ~2015 may be RSA-2048.

**CRT optimization:** Chinese Remainder Theorem decomposition reduces RSA private key operations from one computation mod N to two computations mod p and mod q. This provides approximately 4× speedup. Any RSA implementation used for signing should use CRT.

> **Principle 23.** *RSA's security requires keys 8–15× larger than ECC for equivalent classical security; for new embedded designs, use ECC. For firmware verification where RSA is established, RSA-2048 with small public exponent is acceptable.*

---

## Chapter 24 — Lattices and Post-Quantum Security

Lattice-based cryptography is the post-quantum answer to ECC and RSA, both of which are broken by Shor's algorithm running on a sufficiently large quantum computer.

A lattice is a discrete set of points in n-dimensional space, defined by a basis. The hard problems are:

*Shortest Vector Problem (SVP)*: find the shortest non-zero vector in the lattice.
*Learning With Errors (LWE)*: given many approximate inner products of a secret vector s with random vectors a_i, recover s. Even approximately solving LWE is believed to be hard classically and quantumly.

**CRYSTALS-Kyber (now ML-KEM, NIST FIPS 203)** is the post-quantum KEM standardized by NIST in 2024. It is based on Module-LWE.

**CRYSTALS-Dilithium (now ML-DSA, NIST FIPS 204)** is the post-quantum signature scheme.

```
┌──────────────────────────────────────────────────────────────────┐
│           Post-Quantum vs ECC: Size Comparison                   │
│                                                                  │
│  Scheme       │ Public Key  │ Private Key │ Sig/Ciphertext       │
│  ─────────────┼─────────────┼─────────────┼──────────────────── │
│  P-256 (ECDH) │ 64 bytes    │ 32 bytes    │ — (KA, no CT)       │
│  P-256 ECDSA  │ 64 bytes    │ 32 bytes    │ 64 bytes (sig)      │
│  ML-KEM-512   │ 800 bytes   │ 1632 bytes  │ 768 bytes (CT)      │
│  ML-KEM-768   │ 1184 bytes  │ 2400 bytes  │ 1088 bytes          │
│  ML-DSA-44    │ 1312 bytes  │ 2528 bytes  │ 2420 bytes (sig)    │
│  ML-DSA-65    │ 1952 bytes  │ 4000 bytes  │ 3293 bytes          │
└──────────────────────────────────────────────────────────────────┘
```

The size increase is the primary challenge for embedded deployment. ML-KEM-512 public keys are 800 bytes — fitting in RAM but requiring design consideration for flash storage and transmission over BLE or 802.15.4.

**Post-quantum performance on embedded:** ML-KEM-512 operations take approximately 1–5 ms on ARM Cortex-M4, outperforming P-256 ECDH in software. This is by design — lattice operations are matrix multiplications over small integers, which map well to SIMD and 32-bit arithmetic. Kyber is faster than ECC in software on 32-bit targets.

> **Principle 24.** *Post-quantum algorithms are faster than ECC in software but have larger key and ciphertext sizes. The transition is a size problem, not a performance problem, on 32-bit embedded targets.*

---

## Chapter 25 — Why Key Sizes Differ Across Algorithm Families

The key size comparison table in Chapter 13 needs the explanation behind it. Why does a 256-bit ECC key provide the same security as a 3072-bit RSA key?

The answer is the best known attack against each.

**For RSA:** the best classical attack is the General Number Field Sieve (GNFS). GNFS runs in sub-exponential time: approximately `exp(c * (ln N)^(1/3) * (ln ln N)^(2/3))`. For RSA-2048 (N ≈ 2^2048), this gives a roughly 2^112 security level, not 2^2048. The key is large because the hardness scales sub-exponentially with key size.

**For ECC:** the best classical attack is Pollard's rho algorithm. It runs in fully exponential time: approximately `√n` operations where n is the group order. For P-256, n ≈ 2^256, so the attack takes 2^128 operations — 128-bit security from 256-bit parameters. The key is small because the hardness scales exponentially with key size.

**For symmetric ciphers (AES):** the best classical attack is exhaustive search, taking 2^k operations for a k-bit key. AES-128 provides exactly 128-bit security. The key size equals the security level.

```
┌──────────────────────────────────────────────────────────────────┐
│         Security Scaling vs. Key Size (Classical)                │
│                                                                  │
│  AES:   Security = key_size           (linear in bits)           │
│  ECC:   Security = key_size / 2       (halvings)                 │
│  RSA:   Security = key_size^(1/3)×... (sub-exponential, ~1/8)   │
│                                                                  │
│  For 128-bit security:                                           │
│  AES:  128-bit key   → 128-bit security   ratio: 1:1            │
│  ECC:  256-bit key   → 128-bit security   ratio: 2:1            │
│  RSA:  3072-bit key  → 128-bit security   ratio: 24:1           │
└──────────────────────────────────────────────────────────────────┘
```

Against quantum computers, Grover's algorithm halves the search space for symmetric keys (AES-128 → 64-bit quantum security) and Shor's algorithm solves both the integer factorization and discrete logarithm problems in polynomial time, breaking RSA and ECC entirely. Post-quantum algorithms have hardness assumptions that are believed to resist both classical and quantum attacks.

> **Principle 25.** *RSA key sizes are large because factoring scales sub-exponentially; ECC key sizes are small because discrete log in elliptic curve groups scales exponentially. Understanding the attack complexity explains the size gap.*

---

# Part V — Elliptic Curve Cryptography in Practice

---

## Chapter 26 — Curve Taxonomy: NIST, Brainpool, and Bernstein Curves

Not all elliptic curves are equal. The choice of curve determines performance, security confidence, and side-channel resistance.

```
┌──────────────────────────────────────────────────────────────────┐
│                    Curve Families                                │
│                                                                  │
│  NIST CURVES (FIPS 186-4)                                        │
│  P-192, P-224, P-256, P-384, P-521                              │
│  Weierstrass form: y² = x³ + ax + b                             │
│  a = -3 (special: faster doubling formula)                       │
│  Constants: selected by NIST, origins not fully documented       │
│  Standard for: TLS, PKIX, most government applications           │
│                                                                  │
│  BRAINPOOL CURVES (RFC 5639)                                     │
│  brainpoolP256r1, brainpoolP384r1, brainpoolP512r1              │
│  Weierstrass form, random coefficients                           │
│  Preferred in German/European government applications            │
│  Slower than NIST P-256 (a ≠ -3)                                │
│                                                                  │
│  BERNSTEIN CURVES (IETF/NIST)                                   │
│  Curve25519 / X25519 (key agreement, RFC 7748)                  │
│  Ed25519 (signature, RFC 8032)                                   │
│  Montgomery / twisted Edwards form                               │
│  Designed for: constant-time, software efficiency               │
│  No documented non-obvious constant choices                      │
│  Standard for: modern TLS, SSH, WireGuard, Signal               │
└──────────────────────────────────────────────────────────────────┘
```

**NIST P-256** is the most widely deployed ECC curve. Hardware accelerators support it universally. Certificate infrastructure is built on it. It is the right choice for hardware-accelerated embedded targets.

**Bernstein curves (X25519 / Ed25519)** are the right choice for software-only implementations. They were designed from the ground up for efficient, constant-time software implementation. The Montgomery and Edwards forms have efficient unified addition formulas (no separate doubling formula), inherently reducing side-channel risk. They are also designed to be robust against common implementation errors (cofactor handling, point validation).

**Brainpool** is for European government compliance requirements. It is slower and harder to implement efficiently than P-256. Only use it when mandated.

**The "NIST curve backdoor" concern:** Some cryptographers expressed concern that the NIST P-curve constants may have been chosen to include a backdoor known to NSA. No backdoor has been demonstrated, and the mathematical analysis suggests no practical attack. For most embedded applications, P-256 is the correct choice; for high-assurance implementations, Ed25519 is preferred due to its transparent constant selection.

> **Principle 26.** *For hardware-accelerated embedded targets, use P-256. For software-only embedded targets, use X25519/Ed25519. Never design a new curve; never deploy a curve not in the published standards.*

---

## Chapter 27 — P-256 vs X25519: The Architectural Choice

This is the most important curve selection decision for embedded architects. The answer depends on the implementation context.

```
┌──────────────────────────────────────────────────────────────────┐
│                   P-256 vs X25519                                │
├──────────────────────────────┬───────────────────────────────────┤
│           P-256              │            X25519                 │
├──────────────────────────────┼───────────────────────────────────┤
│ NIST standard, FIPS 186-4    │ RFC 7748, IETF standard           │
├──────────────────────────────┼───────────────────────────────────┤
│ Hardware accelerator support │ Rarely hardware-accelerated        │
│ on ARM M33, M55, STM32H5,    │ (some devices: crypto coprocessors│
│ NXP LPC55, Nordic nRF5340    │ with Curve25519 support)          │
├──────────────────────────────┼───────────────────────────────────┤
│ Weierstrass form:            │ Montgomery form:                  │
│ requires separate add/double │ unified formula, simpler code     │
├──────────────────────────────┼───────────────────────────────────┤
│ Software: 300–600 ms M4      │ Software: 100–250 ms M4           │
│ Hardware: 3–20 ms            │ Software: efficient               │
├──────────────────────────────┼───────────────────────────────────┤
│ Public key: 64 bytes         │ Public key: 32 bytes (x-only)    │
│ (uncompressed, or 33 comp.)  │                                   │
├──────────────────────────────┼───────────────────────────────────┤
│ ECDSA signatures: possible   │ Signatures: use Ed25519 separately│
├──────────────────────────────┼───────────────────────────────────┤
│ FIPS-required contexts       │ Cannot use for FIPS (as of 2024) │
└──────────────────────────────┴───────────────────────────────────┘
```

**Decision rule:**

1. If your target has a hardware PKA supporting P-256: use P-256. Hardware acceleration makes the software efficiency advantage of Curve25519 irrelevant.
2. If your target has no hardware PKA: use X25519 for key agreement and Ed25519 for signatures. Software performance is significantly better.
3. If FIPS compliance is required: use P-256. FIPS 186-4 does not include Curve25519 (as of 2024, though this may change with FIPS 186-5 revisions).
4. If interoperating with TLS servers using P-256: use P-256.

The worst choice is implementing P-256 in software without hardware acceleration and without constant-time scalar multiplication. This is slow (300–600 ms per operation) and vulnerable to timing attacks.

> **Principle 27.** *P-256 is the correct choice for hardware-accelerated targets; X25519/Ed25519 is the correct choice for software-only targets. Never implement P-256 in software without constant-time countermeasures.*

---

## Chapter 28 — Hardware ECC Accelerators

Hardware PKA (Public Key Accelerator) units perform modular arithmetic and, on better implementations, full elliptic curve operations. They provide 20–100× speedup over software.

```
┌──────────────────────────────────────────────────────────────────┐
│         Hardware PKA: Architecture                               │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    PKA Peripheral                         │   │
│  │                                                          │   │
│  │  ┌──────────────────┐  ┌───────────────────────────────┐ │   │
│  │  │ Operand Registers│  │   Arithmetic Core             │ │   │
│  │  │ (RAM inside PKA) │  │   • Modular multiply (MM)     │ │   │
│  │  │                  │  │   • Modular add/sub           │ │   │
│  │  │ Load operands    │  │   • Modular inverse           │ │   │
│  │  │ via CPU or DMA   │  │   • Point add / double        │ │   │
│  │  └──────────────────┘  │   • Scalar multiplication     │ │   │
│  │                        └───────────────────────────────┘ │   │
│  │                                │                          │   │
│  └────────────────────────────────┼──────────────────────────┘   │
│                                   │ Interrupt / polling           │
│                                   ▼                              │
│  CPU writes operands → starts operation → waits for completion   │
│                                                                  │
│  Examples:                                                       │
│  STM32H5: PKA with P-256/384 scalar mult, RSA-2048/3072/4096    │
│  NXP LPC55S69: CASPER with P-256, P-384, RSA-2048/3072          │
│  Nordic nRF5340: CC312 (CryptoCell) with P-256, X25519, EdDSA   │
└──────────────────────────────────────────────────────────────────┘
```

**Programming model for STM32H5 PKA (ECDH example):**

```c
/* Configure PKA for ECDH phase 1 (our private key → public key) */
PKA_ECDHPhase1InTypeDef in;
in.primeOrderSize      = 32; /* bytes, for P-256 */
in.modulusSize         = 32;
in.coefSign            = 0;  /* a coefficient is negative (-3) */
in.coef                = p256_a;
in.modulus             = p256_p;
in.basePointX          = p256_Gx;
in.basePointY          = p256_Gy;
in.primeOrder          = p256_n;
in.privateKey          = private_key_bytes;

HAL_PKA_ECDHPhase1(&hpka, &in, HAL_MAX_DELAY);

PKA_ECDHPhase1OutTypeDef out;
HAL_PKA_ECDHPhase1_GetResult(&hpka, &out);
/* out.ptX, out.ptY are our public key coordinates */
```

**DMA vs polling for PKA:** For single operations (one ECDH handshake), polling is simpler — start the operation, wait for completion interrupt. For high-throughput use cases, DMA loading of operands reduces CPU involvement.

**Key security question about hardware PKA:** Does the hardware PKA implement constant-time operations? A PKA that performs a non-constant-time scalar multiplication is vulnerable to power analysis, even though it is a hardware unit. Check the silicon vendor's datasheet for "DPA resistant" or "side-channel resistant" claims. STM32H5's PKA is documented as implementing constant-time operations. Others vary.

> **Principle 28.** *Hardware PKA is the correct target for ECC on ARM Cortex-M33+; verify that the specific PKA implementation is constant-time before relying on its side-channel resistance.*

---

## Chapter 29 — Coordinate Systems and Montgomery Arithmetic

Two optimizations are universal in efficient ECC implementations: projective coordinates and Montgomery arithmetic. Understanding them explains why ECC libraries behave as they do.

**Projective coordinates** represent a curve point (x, y) as a triple (X : Y : Z) where x = X/Z and y = Y/Z (or x = X/Z², y = Y/Z³ for Jacobian coordinates). The affine point is recovered only at the end of computation by computing the inverse of Z.

The benefit: point addition and doubling formulas in Jacobian coordinates use only multiplications and additions — no modular inverses during intermediate steps. Since modular inversion is ~30× more expensive than multiplication, this dramatically accelerates scalar multiplication.

**Montgomery multiplication** is the universal technique for efficient modular arithmetic. It transforms the problem of computing `a * b mod p` into a form that avoids expensive division:

```
Montgomery domain: ã = a * R mod p  (R = 2^256 for 256-bit p)
Montgomery multiply: MonMul(ã, b̃) = ã * b̃ * R⁻¹ mod p

Properties:
- MonMul can be computed with only shifts and additions (no division)
- All field elements are converted to Montgomery form at the start
- Converted back at the end
- Intermediate operations are all Montgomery multiplications
```

The Montgomery domain transformation is invisible to callers of ECC libraries. It is an internal optimization. But it has an implementation security implication: if the conversion to/from Montgomery domain is not handled correctly for all input values (including 0, 1, p-1, and adversarially chosen values), the implementation may produce incorrect results on edge-case inputs.

For embedded architects: these details matter when evaluating a library's correctness. A library that does not test edge-case inputs to field arithmetic may produce incorrect signatures or key agreements on rare inputs that an adversary can exploit.

> **Principle 29.** *Projective coordinates eliminate field inversions during scalar multiplication; Montgomery arithmetic eliminates division during modular multiplication. Together they make ECC practical on embedded hardware without a hardware accelerator.*

---

## Chapter 30 — ECC Side-Channel Attacks and Countermeasures

ECC is more vulnerable to side-channel attacks than symmetric crypto because the private key is used directly in each operation, and a single partial observation can leak key bits.

**Simple Power Analysis (SPA) on scalar multiplication:** The naive double-and-add algorithm performs a doubling at every step and an addition only when the current key bit is 1. A single power trace reveals the sequence of doublings and additions, revealing the private key directly.

**Differential Power Analysis (DPA) on ECC:** Statistical analysis across many traces targeting specific intermediate values (coordinates during point operations) recovers private key bits even from noisy traces.

**Timing attacks on ECC:** Variable-time implementations (those using the naive double-and-add algorithm or those with early-exit modular reduction) leak timing information correlated with key bits.

**Invalid curve attacks:** If a point received from the other party is not validated to lie on the correct curve, the implementation may perform computation on a point on a different (weak) curve, from which the private key can be recovered efficiently.

```
┌──────────────────────────────────────────────────────────────────┐
│           ECC Attack → Countermeasure Map                        │
│                                                                  │
│  SPA on scalar mult   → Montgomery ladder or fixed-window method │
│  DPA on coordinates   → Coordinate randomization (projective     │
│                          randomization with random Z)            │
│  Timing attacks       → Constant-time implementation             │
│  Invalid curve attack → Validate received points on curve        │
│  Fault in sign        → Double computation; verify before output  │
│  Lattice attacks on   → Use deterministic nonce (RFC 6979)       │
│  ECDSA nonce         │   or use EdDSA (nonce is hash-derived)    │
└──────────────────────────────────────────────────────────────────┘
```

**Point validation** is non-optional: before using any public key received from an untrusted source, verify that the point satisfies the curve equation and has the correct order. A one-time check at key import prevents the entire class of invalid-curve attacks.

**Coordinate randomization** defends against DPA: before scalar multiplication, multiply the Z coordinate by a random value. This randomizes the projective coordinates without changing the final result, making DPA correlation fail.

**Scalar blinding** defends against SPA and DPA: before scalar multiplication, replace d with d + r*n for a random r. The result is the same (since r*n*G = ∞, the identity), but the scalar processed is different for every execution.

> **Principle 30.** *Always validate received elliptic curve points before using them; always use a constant-time scalar multiplication algorithm; never compute ECDSA with a non-deterministic implementation without a hardware TRNG of demonstrated quality.*

---

# Part VI — Digital Signatures for Embedded Systems

---

## Chapter 31 — ECDSA: Structure and Failure Modes

ECDSA (Elliptic Curve Digital Signature Algorithm) is the most widely deployed asymmetric signature scheme on embedded systems. It is also the scheme with the most implementation pitfalls.

**ECDSA signing:**

```
ECDSA-with-SHA256, key (d, Q) on P-256:

1. Compute h = SHA256(message)         (hash, 32 bytes)
2. Interpret h as integer e
3. Generate random k ∈ [1, n-1]        ← THE CRITICAL STEP
4. Compute (x₁, y₁) = k * G
5. r = x₁ mod n; if r == 0, go to step 3
6. s = k⁻¹ * (e + r*d) mod n; if s == 0, go to step 3
7. Signature = (r, s), each 32 bytes for P-256 → 64 bytes total
```

**ECDSA verification:**

```
Inputs: message, signature (r, s), public key Q

1. Check r, s ∈ [1, n-1]
2. h = SHA256(message); e = integer(h)
3. w = s⁻¹ mod n
4. u₁ = e*w mod n;  u₂ = r*w mod n
5. (x₁, y₁) = u₁*G + u₂*Q
6. Accept iff x₁ mod n == r
```

**The k-nonce catastrophe.** Step 3 in signing generates a random integer k. If k is reused even once across two different messages signed with the same private key, the private key is immediately recoverable by simple algebra:

```
Two signatures with same k:
s₁ = k⁻¹(e₁ + r*d) mod n
s₂ = k⁻¹(e₂ + r*d) mod n

s₁ - s₂ = k⁻¹(e₁ - e₂) mod n
k = (e₁ - e₂) / (s₁ - s₂) mod n  ← k is now known
d = (s₁*k - e₁) * r⁻¹ mod n       ← private key recovered
```

This attack requires only two signatures with the same r value (which appears when k is reused). It has been used to recover private keys from PlayStation 3 firmware signing keys, Bitcoin wallets, and embedded device deployments where a poor TRNG produced correlated nonces.

**RFC 6979 deterministic ECDSA** eliminates nonce randomness entirely by deriving k from a hash of the private key and the message. The k is deterministic, unique per (key, message) pair, and independent of the TRNG. Use RFC 6979 whenever signing in ECDSA. Every major crypto library supports it.

**Signature malleability:** For any valid ECDSA signature (r, s), the signature (r, n-s) is also valid. This means the same signature has two valid forms. For most applications this is harmless, but some protocols (notably some Bitcoin transaction formats) have been broken by malleability. Low-S normalization (always using the s value with s ≤ n/2) eliminates this.

> **Principle 31.** *ECDSA with a weak or reused nonce immediately reveals the private key. Always use RFC 6979 deterministic nonce derivation; never depend on the hardware TRNG quality for ECDSA nonce generation.*

---

## Chapter 32 — EdDSA and Ed25519: The Modern Signature

EdDSA (Edwards-curve Digital Signature Algorithm, RFC 8032) eliminates the ECDSA nonce problem by design. The nonce is deterministically derived from the private key and message using a hash function.

**Ed25519 signing:**

```
Key: private key seed s (32 bytes)
     Expand: (a, prefix) = SHA512(s), split into 32+32 bytes
     Clamp: clear bottom 3 bits and top 2 bits of a
     Public key A = a * B  (B is the base point of Ed25519)

Sign(message):
1. r = SHA512(prefix ‖ message) mod l   ← deterministic nonce
2. R = r * B                             ← nonce point
3. S = (r + SHA512(R ‖ A ‖ message) * a) mod l
4. Signature = (R, S), 64 bytes total
```

**Properties that distinguish Ed25519 from ECDSA:**

*Deterministic*: the nonce r is derived from a hash of the private key prefix and the message. No TRNG needed during signing. No nonce reuse possible.

*Clean key format*: the public key A is a single compressed point, 32 bytes. The signature (R, S) is 64 bytes. No DER encoding complications.

*Cofactor handling*: Ed25519 is defined on a curve with cofactor 8. The signing algorithm handles this correctly by design. Naive ECDSA implementations that ignore cofactors on curves with cofactor > 1 are vulnerable.

*Constant-time by design*: the underlying curve (Curve25519 in Edwards form) has efficient unified addition formulas that naturally produce constant-time code.

**Ed25519 on embedded systems:**

Ed25519 verification requires two scalar multiplications, costing ~300–500 ms in software on Cortex-M4. Signing requires one scalar multiplication, ~150–300 ms. Some embedded SoCs include hardware Ed25519 acceleration (Nordic nRF5340 via CryptoCell, STM32 via driver library on H5 series).

**The one caveat:** Ed25519 is not covered by FIPS 186-4 (though FIPS 186-5 draft includes it). For FIPS-required contexts, ECDSA-P256 is required.

> **Principle 32.** *EdDSA eliminates ECDSA's most dangerous failure mode by making the signing nonce deterministic. For new designs without FIPS constraints, Ed25519 is the preferred signature scheme.*

---

## Chapter 33 — RSA-PSS: When RSA Is Required

RSA-PSS (Probabilistic Signature Scheme) is the correct RSA signature scheme. RSA-PKCS1v1.5 (the legacy scheme) is the incorrect one.

```
┌──────────────────────────────────────────────────────────────────┐
│         RSA-PSS vs RSA-PKCS1v1.5                                 │
├──────────────────────────────┬───────────────────────────────────┤
│       RSA-PSS                │    RSA-PKCS1v1.5                  │
├──────────────────────────────┼───────────────────────────────────┤
│ Provably secure under        │ No security proof                 │
│ random oracle model          │                                   │
├──────────────────────────────┼───────────────────────────────────┤
│ Randomized (random salt)     │ Deterministic                     │
├──────────────────────────────┼───────────────────────────────────┤
│ Required by PKCS#1 v2.1,     │ Widely deployed, being           │
│ FIPS 186-4, RFC 8017         │ deprecated in new protocols       │
├──────────────────────────────┼───────────────────────────────────┤
│ Parameters: hash, MGF,       │ Parameters: hash function only    │
│ salt length                  │                                   │
├──────────────────────────────┼───────────────────────────────────┤
│ Correct for new designs      │ Legacy interoperability only      │
└──────────────────────────────┴───────────────────────────────────┘
```

**RSA-PSS parameters:** The scheme takes a hash function (SHA-256 recommended), a mask generation function (MGF1 based on the same hash), and a salt length. The salt length should equal the hash output length (32 bytes for SHA-256) — this maximizes security. Some implementations use a salt length of 0 (deterministic PSS); this loses the randomization benefit.

**RSA on embedded: the performance hierarchy:**

- RSA-2048 verification (e=65537): 20–50 ms software, 2–10 ms hardware PKA — *acceptable*
- RSA-2048 signing: 1000–3000 ms software, 50–200 ms hardware PKA — *use hardware or avoid*
- RSA-3072 verification: 80–200 ms software — *marginal*
- RSA-3072 signing: 4–10 seconds software — *hardware-only or avoid*

RSA-2048 verification with public exponent 65537 is the primary embedded use case for RSA. It is used in secure boot (firmware signature verification), where the bootloader holds the root CA's RSA public key and verifies the firmware image signature. This operation is performed once at boot, and 20–50 ms is acceptable.

> **Principle 33.** *Use RSA-PSS for new RSA-based signature schemes. RSA-PKCS1v1.5 signatures are legacy; implement them only for interoperability with existing infrastructure, and never for new protocol designs.*

---

## Chapter 34 — ECDSA vs EdDSA: The Decision

This comparison decides the signature scheme for a new embedded design.

```
┌──────────────────────────────────────────────────────────────────┐
│                   ECDSA vs EdDSA                                 │
├──────────────────────────────┬───────────────────────────────────┤
│         ECDSA-P256           │          Ed25519                  │
├──────────────────────────────┼───────────────────────────────────┤
│ Standard: FIPS 186-4         │ Standard: RFC 8032                │
│ FIPS 140-3 approved          │ Not in FIPS 186-4 (as of 2024)   │
├──────────────────────────────┼───────────────────────────────────┤
│ Nonce: random (use RFC 6979) │ Nonce: deterministic (built-in)   │
├──────────────────────────────┼───────────────────────────────────┤
│ HW PKA support: widespread   │ HW support: selected SoCs         │
├──────────────────────────────┼───────────────────────────────────┤
│ Signature: 64 bytes          │ Signature: 64 bytes               │
│ Public key: 64 bytes         │ Public key: 32 bytes              │
├──────────────────────────────┼───────────────────────────────────┤
│ Sign: 300–600 ms SW          │ Sign: 150–300 ms SW               │
│ Verify: 300–600 ms SW        │ Verify: 300–500 ms SW             │
│ Sign: 3–20 ms HW PKA         │ Sign: 5–30 ms (if HW support)    │
├──────────────────────────────┼───────────────────────────────────┤
│ Nonce reuse: catastrophic    │ Nonce reuse: impossible           │
├──────────────────────────────┼───────────────────────────────────┤
│ Interop: universal (TLS,     │ Interop: TLS 1.3, SSH, WireGuard  │
│ mTLS, all CAs)               │                                   │
└──────────────────────────────┴───────────────────────────────────┘
```

**Decision guide:**

1. If FIPS 140-3 is required: use ECDSA-P256.
2. If your target has hardware PKA for P-256: use ECDSA-P256 with RFC 6979.
3. If your target is software-only with no FIPS requirement: use Ed25519.
4. If firmware signing for secure boot: use ECDSA-P256 (widest hardware verifier support in bootloaders).
5. If mTLS device authentication: use ECDSA-P256 (broadest CA and server support).

Do not design a system that mixes ECDSA and EdDSA for the same purpose. Pick one per role and apply it consistently.

> **Principle 34.** *ECDSA-P256 is the choice for hardware-accelerated and FIPS-required contexts; Ed25519 is the choice for software-only contexts without FIPS constraints. Never use ECDSA without RFC 6979 deterministic nonce derivation.*

---

## Chapter 35 — Signature Verification in Secure Boot

Secure boot is asymmetric signature verification applied to firmware images before execution. It is the most performance-critical asymmetric operation in most embedded designs because it occurs at every boot cycle.

```
┌──────────────────────────────────────────────────────────────────┐
│              Secure Boot Verification Flow                       │
│                                                                  │
│  ┌───────────┐                                                   │
│  │ ROM Code  │  1. Load firmware manifest from flash            │
│  │ (trusted) │  2. Extract firmware image hash from manifest     │
│  └─────┬─────┘  3. Verify manifest signature using              │
│        │            embedded public key (in OTP/flash)           │
│        │        4. Compute hash of firmware image               │
│        │        5. Compare computed hash to manifest hash        │
│        │        6. If all checks pass: jump to firmware          │
│        │           If any check fails: halt or recovery mode     │
│        ▼                                                         │
│  ┌───────────┐                                                   │
│  │ Firmware  │                                                   │
│  │ (verified)│                                                   │
│  └───────────┘                                                   │
│                                                                  │
│  Time budget for verification step 3:                            │
│  ECDSA-P256 verify, software: 300–600 ms                        │
│  ECDSA-P256 verify, hardware PKA: 3–20 ms                       │
│  RSA-2048 verify (e=65537), software: 20–50 ms                  │
│  RSA-2048 verify, hardware PKA: 2–10 ms                         │
│                                                                  │
│  SHA-256 hash over 256 KB firmware:                              │
│  Software: ~10–30 ms   Hardware SHA: ~1–3 ms                     │
└──────────────────────────────────────────────────────────────────┘
```

**Secure boot signature scheme selection:**

The bottleneck is hardware availability. On targets with hardware PKA: either ECDSA-P256 or RSA-2048 is fast. ECDSA-P256 is preferred (smaller keys, smaller signatures, no padding concerns). On targets without hardware PKA: RSA-2048 verification (20–50 ms, simple verification algorithm with small public exponent) is faster than software ECDSA (300–600 ms). This is the main reason RSA persists in embedded secure boot.

**The trust anchor placement:** the firmware signing public key or its hash must be in OTP/eFuse or in ROM — not in flash. A public key stored in flash that can be updated by the device defeats the purpose.

**Anti-rollback:** signature verification proves authenticity but not currency. An attacker who compromises the signing key can sign a downgraded (vulnerable) firmware version. Anti-rollback requires a monotonic version counter in OTP that the bootloader reads and enforces.

> **Principle 35.** *Secure boot verification is one signature check per boot cycle; choose the algorithm based on hardware acceleration availability. The trust anchor must be in hardware-protected storage, not in updatable flash.*

---

## Chapter 36 — Hash-then-Sign and the Role of the Hash Function

Every asymmetric signature scheme follows the hash-then-sign construction. The hash function is not an implementation detail — it is a security parameter.

**Why hash-then-sign:**

1. *Fixed-size input*: ECDSA and RSA operate on integers of specific size. Arbitrary-length messages are hashed to fixed-size values before signing.
2. *Security binding*: the signature is bound to the specific hash value. Changing any bit of the message changes the hash and invalidates the signature. Without hashing, the algebraic structure of RSA would allow forging signatures for related messages.
3. *Algorithm separation*: changing the hash algorithm changes the signature binding. An ECDSA-with-SHA256 signature cannot be repurposed as an ECDSA-with-SHA384 signature.

**The hash function determines the signature's collision resistance.** A signature scheme with a weak hash function (MD5, SHA-1) has weak collision resistance even if the underlying asymmetric operation is strong. Forging a certificate signature using SHA-1 collision was demonstrated by the Shattered attack (2017). The ECDSA and RSA primitives were not broken — the hash was.

**Hash algorithm selection for embedded:**

| Hash | Output | Status | Notes |
|------|--------|--------|-------|
| SHA-256 | 32 bytes | Recommended | Hardware accelerated widely |
| SHA-384 | 48 bytes | For P-384 keys | Required if using ECDSA-P384 |
| SHA-512 | 64 bytes | Strong | Less common HW accel on M-core |
| SHA3-256 | 32 bytes | Modern | Rare HW on embedded |
| SHA-1 | 20 bytes | Deprecated | Never use for new signatures |
| MD5 | 16 bytes | Broken | Never use |

**The algorithm identifier encodes both.** `ecdsa-with-SHA256` is one OID that names both ECDSA and SHA-256. Changing to SHA-384 uses a different OID: `ecdsa-with-SHA384`. Implementations that allow arbitrary hash selection at runtime without matching the algorithm identifier in the certificate create interoperability and security problems.

> **Principle 36.** *The hash function is a security parameter of the signature, not an implementation detail. A strong asymmetric primitive with a weak hash provides weak signatures.*

---

# Part VII — Key Agreement and Key Encapsulation

---

## Chapter 37 — ECDH: The Fundamental Construction

ECDH (Elliptic Curve Diffie-Hellman) is the key agreement scheme built on elliptic curves. It is the basis for TLS key exchange, DTLS, and most modern embedded secure channel protocols.

```
ECDH on P-256:

Alice:
  private key a (32 bytes, random)
  public key  A = a * G

Bob:
  private key b (32 bytes, random)
  public key  B = b * G

Exchange: Alice sends A; Bob sends B.

Alice computes: S = a * B = a * (b * G) = (ab) * G
Bob computes:   S = b * A = b * (a * G) = (ab) * G

Shared secret: x-coordinate of S, 32 bytes for P-256
Key derivation: keys = HKDF-SHA256(S, salt, info)
```

**ECDH output is not a key — it is key material.** The shared secret S (specifically, the x-coordinate of the shared point) must be processed through a KDF before use as a symmetric key. Using the raw ECDH output directly as an AES key is wrong: the output has structure (it is a curve point coordinate) that may reduce security relative to a uniformly random key.

**Point validation is mandatory:** before computing the ECDH, validate that the received public key point B lies on the correct curve and has the expected order. An invalid curve attack substitutes a point on a weak curve for B; the subsequent computation leaks the private key.

**ECDH produces an unauthenticated shared secret.** An active attacker (man-in-the-middle) can substitute their own public key for either party's, establishing separate ECDH sessions with each. The result: the attacker decrypts everything. ECDH must be combined with authentication — specifically, one or both parties must present a certificate and sign the handshake transcript — before the channel is secure.

> **Principle 37.** *ECDH output must be processed through a KDF before use as a key; the ECDH shared secret has structure that reduces its direct use as key material. Always validate received points before ECDH computation.*

---

## Chapter 38 — X25519: The Clean Curve for Key Agreement

X25519 (RFC 7748) is ECDH on Curve25519 using Montgomery form with x-coordinate-only scalar multiplication (the "X" in X25519 denotes x-coordinate). It is the cleanest key agreement primitive available.

**X25519 properties that differ from ECDH on NIST curves:**

*X-coordinate only:* the Diffie-Hellman function on Curve25519 uses only the x-coordinate. This reduces the public key to 32 bytes (versus 64 bytes for an uncompressed P-256 point) and enables highly efficient constant-time implementation via the Montgomery ladder.

*Clamping:* X25519 private keys are 32 random bytes with specific bits forced: the bottom 3 bits are cleared (cofactor handling) and the top 2 bits are set. Clamping is applied before scalar multiplication and prevents small-subgroup attacks without explicit point validation.

*No point validation required:* because X25519 uses x-coordinate-only arithmetic and clamping, the invalid-curve attack class that applies to ECDH on Weierstrass curves does not apply. The function is defined to return a valid output (potentially the low-order point) for any 32-byte input.

```c
/* X25519 is simple to use correctly */
uint8_t our_private_key[32];  /* 32 random bytes, clamped */
uint8_t our_public_key[32];
uint8_t their_public_key[32]; /* received from peer */
uint8_t shared_secret[32];

/* Generate our key pair */
generate_random_bytes(our_private_key, 32);
curve25519_clamp(our_private_key);  /* or library does this */
x25519_public_key(our_public_key, our_private_key); /* our_pub = priv * G */

/* Compute shared secret */
x25519(shared_secret, our_private_key, their_public_key); /* = priv * their_pub */

/* Derive symmetric keys */
hkdf_sha256(keys, 32, shared_secret, 32, salt, info);
```

**X25519 still requires authentication.** X25519 is an unauthenticated key agreement. The result is a shared secret that both parties computed — but without authentication, a man-in-the-middle can substitute their own X25519 public key. Combine X25519 with Ed25519 signatures (or certificates) for authenticated key exchange.

> **Principle 38.** *X25519 is the simplest correct key agreement primitive; its clamping design prevents most common implementation errors. It still requires authentication; unauthenticated X25519 is vulnerable to man-in-the-middle.*

---

## Chapter 39 — Forward Secrecy and Ephemeral Keys

Forward secrecy (also called Perfect Forward Secrecy, PFS) means that compromise of a long-term private key does not retroactively expose past session data.

```
┌──────────────────────────────────────────────────────────────────┐
│              Without Forward Secrecy                             │
│                                                                  │
│  Session 1 ──► Static key pair (Ks) ──► Session key K1          │
│  Session 2 ──► Static key pair (Ks) ──► Session key K2          │
│  Session 3 ──► Static key pair (Ks) ──► Session key K3          │
│                                                                  │
│  If Ks compromised later: attacker can derive K1, K2, K3 and     │
│  decrypt all recorded traffic from Sessions 1, 2, 3.            │
│                                                                  │
│              With Forward Secrecy (DHE)                          │
│                                                                  │
│  Session 1 ──► Ephemeral key e1 ──► Session key K1 ──► Deleted  │
│  Session 2 ──► Ephemeral key e2 ──► Session key K2 ──► Deleted  │
│  Session 3 ──► Ephemeral key e3 ──► Session key K3 ──► Deleted  │
│                                                                  │
│  If Ks compromised: e1, e2, e3 are gone. K1, K2, K3 cannot      │
│  be derived. Past sessions remain private.                       │
└──────────────────────────────────────────────────────────────────┘
```

Forward secrecy requires ephemeral keys — key pairs generated fresh for each session and discarded after the session's key material is derived. The long-term key pair (Ks) is used only for authentication (signing the handshake transcript), not for deriving the session key.

TLS 1.3 mandates forward secrecy — all key exchange modes use ephemeral DH (ECDHE). This was a deliberate departure from TLS 1.2, which allowed static RSA key exchange (no forward secrecy).

**Cost of forward secrecy on embedded devices:** each session requires a full key generation and ECDH computation. For a device connecting once per hour, this cost is negligible. For a device connecting 100 times per second, it may be significant. Hardware PKA makes ephemeral ECDH feasible at high connection rates.

**Forward secrecy and key storage:** ephemeral private keys must be stored in RAM only — never in flash. At session close, they must be explicitly zeroized. A key that is accidentally written to flash (via a debug dump, crash log, or hibernation image) is no longer ephemeral.

> **Principle 39.** *Forward secrecy protects past sessions from future key compromise; it requires ephemeral keys that are generated per-session and destroyed immediately after key derivation. Ephemeral keys must never be written to non-volatile storage.*

---

## Chapter 40 — Static vs Ephemeral: The Tradeoff

The choice between static and ephemeral keys is a tradeoff between performance and security.

```
┌──────────────────────────────────────────────────────────────────┐
│         Static vs Ephemeral Key Agreement                        │
├──────────────────────────────┬───────────────────────────────────┤
│        STATIC                │         EPHEMERAL                 │
├──────────────────────────────┼───────────────────────────────────┤
│ Key pair generated once      │ Key pair generated per session     │
│ (at provisioning)            │                                   │
├──────────────────────────────┼───────────────────────────────────┤
│ No key generation overhead   │ Key generation per handshake      │
│ at connect time              │                                   │
├──────────────────────────────┼───────────────────────────────────┤
│ Deterministic shared secret  │ Fresh shared secret per session   │
├──────────────────────────────┼───────────────────────────────────┤
│ No forward secrecy           │ Forward secrecy                   │
├──────────────────────────────┼───────────────────────────────────┤
│ Replay attack possible if    │ Replay prevented by freshness     │
│ session not tied to nonce    │ of ephemeral key                  │
├──────────────────────────────┼───────────────────────────────────┤
│ Used in: PSK-based protocols,│ Used in: TLS 1.3, DTLS 1.3,      │
│ OSCORE, some BLE profiles    │ EDHOC, most modern protocols      │
└──────────────────────────────┴───────────────────────────────────┘
```

**The pragmatic embedded deployment:** many constrained devices lack hardware PKA and cannot afford ephemeral ECDH per session (300–600 ms). These devices use pre-shared symmetric keys derived from a prior key exchange (at provisioning time), with OSCORE or custom AEAD record protocols for subsequent communication. This sacrifices forward secrecy for performance.

This is an explicit, documented security tradeoff — not a mistake. The device's threat model must account for the loss of forward secrecy: if the device's symmetric key is compromised, all past session traffic can be decrypted.

For devices that connect infrequently (once per day or less), even software ECDH is affordable. The threshold where forward secrecy becomes costly enough to sacrifice depends on the session rate and hardware capability.

> **Principle 40.** *Sacrificing forward secrecy for performance is a documented tradeoff, not a mistake, if the threat model accounts for the blast radius of long-term key compromise.*

---

## Chapter 41 — Post-Quantum KEM: Kyber / ML-KEM

ML-KEM (formerly CRYSTALS-Kyber), standardized as NIST FIPS 203 in 2024, is the post-quantum key encapsulation mechanism. It replaces ECDH in a post-quantum-secure hybrid key exchange.

**ML-KEM structure:**

```
ML-KEM-512 (Security Level 1, ~128-bit post-quantum security):

Key generation:
  Private key: sk (1632 bytes)
  Public key:  pk (800 bytes)

Encapsulation (sender):
  (K, ct) = ML-KEM-Encaps(pk)
  K: 32-byte shared secret (sender knows)
  ct: 768-byte ciphertext (transmitted to receiver)

Decapsulation (receiver):
  K = ML-KEM-Decaps(sk, ct)
  K: 32-byte shared secret (receiver recovers)

Both parties now have the same 32-byte K.
Derive symmetric keys from K via HKDF.
```

**ML-KEM is a KEM, not a key agreement.** Only the encapsulator (sender) generates the shared secret; the decapsulator (receiver) recovers it. This is fundamentally different from ECDH where both parties contribute. For embedded protocols, the distinction matters: one party generates K and encapsulates it; the other decapsulates. The protocol must specify who is the encapsulator.

**Performance on ARM Cortex-M4 (ML-KEM-512):**

| Operation | Software (PQCLEAN) | Notes |
|-----------|-------------------|-------|
| Key generation | 1–3 ms | Fast; uses rejection sampling |
| Encapsulation | 1–3 ms | Fast; one polynomial multiplication |
| Decapsulation | 1–3 ms | Fast; same cost |

ML-KEM is dramatically faster than ECDH on Cortex-M4 in software. The bottleneck is size: 800-byte public keys, 768-byte ciphertexts, 1632-byte private keys. Flash and RAM must budget for these.

> **Principle 41.** *ML-KEM is faster than ECDH in software on 32-bit targets but has 10–25× larger key and ciphertext sizes. Post-quantum migration is a storage and bandwidth planning problem, not a performance problem.*

---

## Chapter 42 — Hybrid Key Exchange

Hybrid key exchange combines a classical algorithm (P-256 ECDH or X25519) with a post-quantum algorithm (ML-KEM). The result is secure if either algorithm is secure — providing protection against both classical attacks and future quantum computers.

```
┌──────────────────────────────────────────────────────────────────┐
│              Hybrid Key Exchange (TLS 1.3 style)                 │
│                                                                  │
│  Client sends:                                                   │
│  • X25519 public key (32 bytes)        ← classical              │
│  • ML-KEM-512 public key (800 bytes)   ← post-quantum           │
│                                                                  │
│  Server responds:                                                │
│  • X25519 public key (32 bytes)        ← classical              │
│  • ML-KEM-512 ciphertext (768 bytes)   ← post-quantum           │
│                                                                  │
│  Both parties compute:                                           │
│  classical_ss  = X25519(our_priv, their_pub)                     │
│  pq_ss         = ML-KEM-Decaps/Encaps result                    │
│                                                                  │
│  Combined key material:                                          │
│  keys = HKDF(classical_ss ‖ pq_ss, ...)                         │
│                                                                  │
│  Security: attacker must break BOTH X25519 AND ML-KEM            │
│  to learn the session keys.                                      │
└──────────────────────────────────────────────────────────────────┘
```

**Why hybrid and not pure post-quantum:** ML-KEM is new. Its implementation maturity is lower than ECC; its security analysis, while extensive, has not had decades of scrutiny. Deploying pure ML-KEM loses the battle-tested security of ECC. Deploying hybrid loses nothing — an attacker must break both algorithms to succeed.

**Embedded cost of hybrid:** an X25519 + ML-KEM-512 hybrid key exchange costs:
- RAM: ~800 + 32 + 768 bytes for key material during handshake ≈ 1.7 KB
- Compute: X25519 (~150–300 ms SW) + ML-KEM (~1–3 ms SW) ≈ 150–300 ms
- Bandwidth: ~1.6 KB additional per handshake

On a device with 32 KB RAM, hybrid key exchange is feasible. On a device with 8 KB RAM, it may require careful staging.

IETF RFC 9420 (MLS) and the TLS 1.3 IANA group `X25519MLKEM768` define hybrid combinations. Use the standard definitions rather than custom combinations.

> **Principle 42.** *Deploy hybrid key exchange — classical plus post-quantum — not pure post-quantum. Hybrid inherits the security of both; pure post-quantum loses the decades of ECC security confidence.*

---

# Part VIII — PKI for Embedded Fleets

---

## Chapter 43 — The PKI Hierarchy for IoT

A PKI (Public Key Infrastructure) for an IoT fleet requires a specific hierarchy design. It differs from traditional web PKI in scope, management, and operational requirements.

```
┌──────────────────────────────────────────────────────────────────┐
│               IoT Device PKI Hierarchy                           │
│                                                                  │
│  ┌────────────────────────────────────────┐                     │
│  │           Root CA                       │                     │
│  │  Self-signed; HSM-protected             │                     │
│  │  Lifetime: 20 years                     │                     │
│  │  Offline storage; used rarely           │                     │
│  └──────────────────┬─────────────────────┘                     │
│                     │ Signs                                      │
│          ┌──────────┴───────────┐                               │
│          ▼                      ▼                               │
│  ┌───────────────┐   ┌─────────────────┐                        │
│  │Firmware       │   │Device Identity  │                        │
│  │Signing CA     │   │CA               │                        │
│  │Lifetime: 5yr  │   │Lifetime: 5yr    │                        │
│  │Online HSM     │   │Online HSM       │                        │
│  └───────┬───────┘   └────────┬────────┘                        │
│          │                    │ Signs (at factory)              │
│          ▼                    ▼                                  │
│  ┌───────────────┐   ┌─────────────────┐                        │
│  │Firmware       │   │Device           │                        │
│  │Signing Certs  │   │Identity Certs   │                        │
│  │(per release)  │   │(per device)     │                        │
│  └───────────────┘   └─────────────────┘                        │
└──────────────────────────────────────────────────────────────────┘
```

**Two distinct certificate hierarchies serve two distinct purposes:**

*Firmware signing hierarchy*: authenticates software from manufacturer to device. The firmware signing CA signs certificates used to sign firmware images. The device's bootloader embeds the firmware signing CA's public key (or root CA's public key). This hierarchy never leaves the manufacturer's control.

*Device identity hierarchy*: authenticates individual devices to the backend cloud. The device identity CA issues per-device certificates at manufacturing time, enrolled against the device's hardware-generated key pair. The backend embeds the root CA for certificate chain validation.

**Separation of hierarchies** is important. A key compromise in the firmware signing hierarchy should not affect device identity, and vice versa. Intermediate CAs provide the separation; the root CA remains offline and is used only to re-sign intermediate CAs.

> **Principle 43.** *Separate PKI hierarchies for firmware signing and device identity; compromise of one must not affect the other. The root CA must be offline and used only for intermediate CA issuance.*

---

## Chapter 44 — Device Identity Certificates

Every device in a secure fleet needs a certificate that uniquely identifies it. This certificate is the device's cryptographic identity.

**Certificate contents for device identity:**

```
Subject: CN=Device, serialNumber=<unique device serial>
SubjectAltName: URI:urn:acme:device:<16-byte-hardware-id>
               OR
               DNS:<device-serial>.devices.acme.com
Issuer: CN=Acme Device Identity CA
Validity: 2024-01-01 to 2030-01-01  (6 years)
PublicKey: EC P-256
KeyUsage: digitalSignature (critical)
ExtendedKeyUsage: clientAuth
BasicConstraints: CA:FALSE (critical)
```

**The hardware identity binding:** The device certificate should be tied to the device's hardware identity — not a software-assigned identifier. The Subject Alternative Name should encode a unique identifier that is hardware-rooted: the silicon vendor's device UID (unique identifier burned at fabrication), the MAC address, or a provisioned serial number that matches a manufacturing database.

**Certificate uniqueness requirements:**

- Each device must have a unique private key. Two devices sharing a private key are cryptographically indistinguishable.
- Serial numbers within a CA must be unique. Collision of serial numbers enables certificate substitution attacks.
- The public key in the certificate must correspond to the private key stored on the device. If the private key and certificate were provisioned separately (a manufacturing error), the device cannot authenticate.

**Certificate storage on the device:** the device certificate is not secret. It can be stored in flash without encryption. It may be sent to any party that requests authentication. What must be protected is the corresponding private key.

Typical flash layout for device certificate:

```
Flash layout (example, 512 KB device):
0x00000000: Bootloader + embedded firmware signing trust anchor
0x00010000: Firmware image (signed, verified by bootloader)
0x000F0000: Device certificate (DER, ~500 bytes)
0x000F0200: Device private key (if not in hardware key slot)
0x000F0400: CA certificate chain (intermediate + root CA DER)
0x000F1000: Nonce counters, session state
```

> **Principle 44.** *The device certificate is public and freely transmittable; the private key is the device's secret and must be in hardware-protected storage. These two items must match exactly at enrollment.*

---

## Chapter 45 — Certificate Provisioning at Manufacturing

Certificate provisioning is the process of generating or injecting device key pairs and issuing corresponding certificates during manufacturing. It is the highest-risk operation in the device lifecycle.

```
┌──────────────────────────────────────────────────────────────────┐
│          Certificate Provisioning: Two Architectures            │
│                                                                  │
│  Option A: Device-generated key pair                            │
│                                                                  │
│  1. Device generates key pair using TRNG (at factory test)       │
│  2. Device exports public key (over secure programming channel) │
│  3. Factory HSM issues certificate for the public key           │
│  4. Factory programs certificate into device flash              │
│  5. Private key never leaves the device                         │
│                                                                  │
│  Advantage: private key never exposed; strongest isolation      │
│  Risk: TRNG quality at factory; failed enrollment               │
│                                                                  │
│  Option B: HSM-generated key pair                               │
│                                                                  │
│  1. Factory HSM generates key pair                              │
│  2. Factory HSM issues certificate                              │
│  3. Factory programs both private key and certificate to device │
│  4. Device programs private key to hardware key store           │
│                                                                  │
│  Advantage: HSM-quality key generation; simpler audit           │
│  Risk: private key exposed on programming interface briefly;    │
│        HSM compromise exposes all device keys                   │
└──────────────────────────────────────────────────────────────────┘
```

**Device-generated key pairs are preferred** because the private key never exists outside the device's hardware boundary. The manufacturing process only handles the public key and the issued certificate — neither of which requires protection.

**Enrollment protocol for device-generated keys:** the device generates the key pair and produces a Certificate Signing Request (CSR) — a standard format (RFC 2986, PKCS#10) containing the public key and a proof-of-possession signature. The factory HSM validates the CSR, issues the certificate, and returns it to the device for storage.

**Manufacturing HSM security:** if the HSM that issues device certificates is compromised, an attacker can issue certificates for arbitrary keys. Every device certificate issued through the compromised HSM is potentially counterfeitable. Treat the provisioning HSM as the highest-security asset in the manufacturing process.

**Audit trail:** log every device serial number, every public key, every certificate issued, and every timestamp. This log allows post-compromise forensics to identify affected devices and enables certificate revocation.

> **Principle 45.** *Device-generated key pairs are preferred over HSM-generated: the private key never leaves the device. The manufacturing enrollment process must be logged completely for post-compromise forensics.*

---

## Chapter 46 — Certificate Revocation on Constrained Devices

Certificate revocation — invalidating a certificate before its expiry — is operationally complex on embedded devices. The standard mechanisms (CRL, OCSP) are impractical at scale on constrained hardware.

**Why standard revocation mechanisms fail on embedded:**

*CRL (Certificate Revocation List)*: a signed list of revoked certificate serial numbers. For a fleet of 1 million devices, a CRL can be megabytes — far too large to download and parse on a constrained device.

*OCSP (Online Certificate Status Protocol)*: a real-time check against a responder. Requires network connectivity, introduces latency, and the OCSP responder must be available. For devices in intermittent connectivity environments (agricultural sensors, smart meters), OCSP is non-functional.

**Practical revocation mechanisms for embedded fleets:**

*Firmware-embedded revocation list*: embed a list of revoked certificate serial numbers in the firmware. Updated via OTA firmware update. Practical for small revocation sets; requires a firmware update to revoke a certificate.

*Backend-enforced revocation*: the device presents its certificate to the backend. The backend maintains a revocation database and rejects connections from revoked devices. The device does not need to know about revocation — the server enforces it. Simple and effective for client certificates in mTLS.

*Short-lived certificates with automated renewal*: issue device certificates with 24–48 hour validity. A revoked device cannot renew. Requires online certificate authority and reliable device connectivity. Used in high-security enterprise contexts.

*OCSP stapling*: the server (not the device) performs OCSP checks and staples the response to the TLS handshake. The device receives the OCSP response as part of the handshake. Useful when the device is the client and the server has reliable connectivity.

> **Principle 46.** *CRL and OCSP are impractical for constrained devices; use backend-enforced revocation for client certificates and short-lived certificates with automated renewal for high-security contexts.*

---

## Chapter 47 — Attestation: Proving Device Identity Without a Certificate Authority

Remote attestation is a mechanism for a device to prove to a remote party that it is running specific, unmodified software on genuine hardware, without requiring a certificate authority in the communication path.

```
┌──────────────────────────────────────────────────────────────────┐
│              Device Attestation Model                            │
│                                                                  │
│  Device Hardware:                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Attestation Key (AK)                                    │   │
│  │  Generated in hardware at manufacturing                   │   │
│  │  Endorsed by chip vendor's Endorsement CA                 │   │
│  │  Never exportable                                         │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│  Attestation Report (example structure):                         │
│  {                                                               │
│    "nonce": <server-provided random>,    ← freshness           │
│    "fw_hash": SHA256(current firmware),  ← measurement         │
│    "hw_id": <device hardware UID>,       ← identity           │
│    "boot_state": <secure boot flags>,    ← configuration       │
│    "signature": AK_Sign(nonce ‖ fw_hash ‖ hw_id ‖ ...)         │
│  }                                                               │
│                                                                  │
│  Verifier validates:                                             │
│  1. Signature under AK public key                               │
│  2. AK public key certified by chip vendor's Endorsement CA     │
│  3. Firmware hash matches expected value for current release     │
│  4. Nonce matches what was sent (freshness)                     │
└──────────────────────────────────────────────────────────────────┘
```

**ARM PSA attestation** (PSA Certified, EAT — Entity Attestation Token, RFC 9334) is the standard for ARM Cortex-M devices. The device produces a COSE-signed JWT-like token (Entity Attestation Token) containing measurements of the boot state, firmware version, and hardware identity. The signing key is the PSA RoT attestation key, held in TrustZone secure world.

**Attestation vs authentication:** authentication proves "I am Device-12345"; attestation proves "I am Device-12345 running firmware version 2.3.1 on genuine silicon, and my secure boot state is valid." Attestation provides more information and enables the backend to make authorization decisions based on firmware integrity.

**The trust chain:** attestation depends on the chip vendor's endorsement of the device's attestation key. If the chip vendor is compromised, all attestation is broken. This is an inherent limitation of hardware-rooted attestation.

> **Principle 47.** *Attestation proves device identity plus firmware integrity; it enables the backend to refuse service to devices running vulnerable firmware versions, regardless of certificate validity.*

---

# Part IX — Production Realities

---

## Chapter 48 — Performance Budget for Asymmetric Operations

The performance budget for asymmetric operations in production is tighter than benchmarks suggest. Benchmarks measure single operations in isolation; production includes context-switch overhead, buffer allocation, DMA setup, interrupt latency, and concurrent background tasks.

**The production TLS 1.3 handshake on ARM Cortex-M33 at 64 MHz:**

```
TLS 1.3 Full Handshake Time Budget (software P-256):

Client side:
  - ECDH key generation (P-256):           300–600 ms
  - ECDH scalar mult (shared secret):      300–600 ms
  - ECDSA verification (server cert):      300–600 ms
  - HMAC/hash operations:                  1–5 ms
  Total (software): ~900–1800 ms

Client side (hardware PKA, STM32H5 at 250 MHz):
  - ECDH key generation:                   5–20 ms
  - ECDH scalar mult:                      5–20 ms
  - ECDSA verification:                    5–20 ms
  Total (hardware): ~15–60 ms

Acceptable? Depends on application:
  - Device boots once daily: 60 ms acceptable
  - Connection per second: hardware PKA required
  - Interactive protocol: hardware PKA required
```

**Rules for estimating production asymmetric cost:**

1. Multiply benchmark by 1.5–3× for production overhead (scheduler, interrupts, DMA setup).
2. Add per-connection: 2–3 scalar multiplications for ECDHE + authentication.
3. Add certificate chain parsing and verification: 1 signature verification per certificate in chain.
4. Add RAM allocation and zeroization: budget 8–16 KB peak for an ECDH handshake.

**The connection budget:** a device with software P-256 (no hardware PKA) can support approximately 1 connection every 2–4 seconds. A device with hardware PKA can support 10–50 connections per second. Design your protocol's connection frequency around the hardware capability.

> **Principle 48.** *Asymmetric operation benchmarks are lower bounds; production overhead, certificate chain validation, and concurrent tasks increase real-world costs by 2–3×. Measure on the actual target, not in a simulation.*

---

## Chapter 49 — Memory Layout for Asymmetric Crypto

Asymmetric operations have larger transient memory requirements than symmetric operations. Mismanaging this memory is the primary source of stack overflow and heap fragmentation in embedded TLS implementations.

```
┌──────────────────────────────────────────────────────────────────┐
│         Memory Requirements for TLS 1.3 Handshake               │
│         (P-256, Mbed TLS, approximate peak)                      │
│                                                                  │
│  FLASH (static):                                                 │
│  TLS state structures:               2–4 KB                     │
│  Mbed TLS library code (ECC+TLS):    80–120 KB                  │
│  Root CA certificate:                0.5 KB                     │
│  Firmware signing trust anchor:      0.5 KB                     │
│  Total flash (library + data):       ~90–130 KB                 │
│                                                                  │
│  RAM (peak during handshake):                                    │
│  TLS context struct:                 4–8 KB                     │
│  ECC/PKA operand buffers:            2–4 KB                     │
│  Certificate chain (DER):            1–2 KB                     │
│  HKDF + hash contexts:               1–2 KB                     │
│  Record buffers (in + out):          4–8 KB                     │
│  Stack usage (peak):                 2–4 KB                     │
│  Total peak RAM:                     14–28 KB                   │
│                                                                  │
│  Minimum feasible RAM for TLS 1.3:   ~28–32 KB                  │
│  (with careful buffer reuse and static allocation)               │
└──────────────────────────────────────────────────────────────────┘
```

**Stack overflow is the most common failure mode.** ECC operations use deep call stacks and large stack-allocated temporary buffers. If the system stack is 4 KB and ECC needs 3 KB peak during scalar multiplication, a context switch during the operation may trigger a stack overflow. Always add 4–8 KB of stack margin above normal operation when enabling TLS.

**Strategies for constrained RAM:**

*Static allocation*: allocate TLS contexts and buffers statically at startup. Avoid heap allocation during TLS operations. Mbed TLS supports fully static allocation via configuration.

*Buffer reuse*: the input record buffer and the key derivation buffer do not need to exist simultaneously. Stage the handshake to reuse buffers sequentially.

*Reduce record size*: TLS 1.3 supports a maximum record size of 16 KB, but the record size can be negotiated down. A 512-byte record limit is feasible for sensors with small messages.

*Exclude unnecessary cipher suites*: compile out cipher suites you do not use. Each included cipher suite adds library code and potentially context structures.

> **Principle 49.** *The peak RAM for a TLS 1.3 handshake is 2–4× the RAM for a steady-state TLS session; design the memory layout for peak, not average, usage.*

---

## Chapter 50 — Nonce and Randomness Failures in Asymmetric Crypto

Randomness failures in asymmetric crypto are more catastrophic than in symmetric crypto because they may directly expose the private key.

**ECDSA nonce failure (already covered in Chapter 31):** a repeated or biased ECDSA nonce immediately enables private key recovery. Even partial bias (a nonce with a few bits biased toward 0) enables the Biased Nonce Attack via lattice reduction. This attack requires approximately 100–200 signatures with biased nonces to recover a 256-bit private key.

The fix: use RFC 6979 deterministic nonce derivation. This completely eliminates dependence on the TRNG during signing.

**Ephemeral key generation failure:** if the TRNG is non-functional or returns biased output during ephemeral ECDH key generation, two consequences:
1. The shared secret may be predictable, breaking session confidentiality.
2. Repeated ephemeral keys (nonce reuse in ECDH) do not have the same catastrophic consequence as ECDSA nonce reuse — the two sessions produce the same shared secret, but the private key is not recovered.

**RSA key generation failure:** RSA key generation requires two large random primes p and q. If the TRNG produces correlated output across devices (common in manufacturing batches with identical startup conditions), two devices may generate RSA keys sharing a prime factor. GCD of two RSA moduli from correlated TRNGs immediately reveals the shared prime and factors both keys. This attack (Factorable Keys, Heninger et al., 2012) was demonstrated against embedded RSA keys in network devices.

**The production risk:** at manufacturing time, thousands of devices may be provisioned within seconds of each other, from the same firmware, at the same temperature. TRNG output may be correlated. Mix hardware entropy with device-unique identifiers (silicon UID, MAC address burned in OTP) to break inter-device correlation.

> **Principle 50.** *Correlated TRNG output at manufacturing time produces correlated key pairs across devices; always mix hardware entropy with device-unique identifiers during key generation.*

---

## Chapter 51 — Clock and Time: The Silent Dependency

Certificate validity checking requires a trusted current time. This silent dependency causes production failures that are nearly impossible to debug without understanding the dependency.

**Certificate validity checking:**
```
Verify: NotBefore <= current_time <= NotAfter

For current_time to be reliable, the device must have:
1. A real-time clock (RTC) with battery backup
   OR
2. A time synchronization mechanism (NTP, SNTP)
   AND
3. Protection against clock rollback
```

**Devices without a clock:** many embedded IoT devices have no RTC. Their notion of "current time" is either zero (January 1, 1970) or the compile time of the firmware. Certificate validity checks against an incorrect time may:
- Accept expired certificates (time is in the past)
- Reject valid certificates (time is in the future)
- Accept certificates not yet valid (time is before NotBefore)

**The common patch: disable time checks.** Many embedded TLS deployments disable certificate expiry checking because the device has no reliable clock. This is a security tradeoff: it removes the security benefit of certificate expiry (limiting the blast radius of a compromised CA or key).

Document this explicitly. "Certificate expiry is not enforced because the device has no trusted clock" is a security finding, not a free decision.

**Time synchronization in TLS:** the server presents a Certificate message; the device must verify it. The device can use the server's stated time (from the TLS handshake's ServerHello random field, which includes a timestamp in TLS 1.2) as a rough estimate to bootstrap time checks. This is imprecise but better than nothing.

**The clock rollback attack:** if the device clock can be set by an unauthenticated party, an attacker can roll the clock back to within a revoked certificate's validity period, re-enabling authentication with a revoked certificate.

> **Principle 51.** *Certificate validity checking requires a trusted clock; a device without one must document the security consequence of disabling time checks, not silently skip them.*

---

## Chapter 52 — Post-Quantum Migration Planning

Quantum computers capable of running Shor's algorithm against RSA-2048 and P-256 do not currently exist. They may exist within 10–20 years. Devices shipping today with 10–20 year deployment lifetimes need migration plans.

**What must change when quantum computers arrive:**

- RSA and ECC key exchange → ML-KEM (post-quantum KEM)
- ECDSA and RSA signatures → ML-DSA or SLH-DSA (post-quantum signatures)
- Root CA certificates using ECC → re-issued with post-quantum algorithms
- Trust anchors embedded in device firmware → updated via firmware update

**What remains valid:**
- AES-256 (Grover's algorithm reduces to 128-bit quantum security, still strong)
- SHA-256 (weakly affected; use SHA-384 for long-term data)
- All symmetric crypto (proportionally weakened but not broken)

**Migration strategies for embedded fleets:**

*Hybrid now*: deploy hybrid key exchange (X25519 + ML-KEM-512) and hybrid signatures today. Current cost: ~1.6 KB additional handshake overhead. Long-term benefit: seamless transition when quantum computers arrive. Hybrid is the correct default for new designs with deployment lifetimes extending beyond 2030.

*Crypto agility via firmware update*: design the crypto layer to be updatable by OTA firmware update. The specific algorithm can be changed without changing the protocol structure. This requires careful firmware update security (see Chapter 41 of the symmetric manual).

*Trust anchor rotation plan*: the root CA embedded in device firmware is the hardest to change. Plan for a firmware update that rotates the trust anchor to a post-quantum CA certificate before the current ECC CA expires.

**Timeline:** NIST finalized ML-KEM (FIPS 203) and ML-DSA (FIPS 204) in August 2024. Embedded libraries (WolfSSL, Mbed TLS) have initial implementations. Production-grade optimized implementations for ARM Cortex-M are in development. Plan for production deployment of hybrid schemes in new designs starting 2025–2026.

> **Principle 52.** *Deploy hybrid classical + post-quantum key exchange for any device with a deployment lifetime extending beyond 2030. The migration cost is an extra 1.6 KB of handshake overhead today versus a disruptive field update later.*

---

# Part X — Tooling and Workflow

---

## Chapter 53 — Library Selection for Embedded Targets

The library choice for asymmetric cryptography determines algorithm support, hardware acceleration integration, code size, RAM use, and compliance posture.

```
┌──────────────────────────────────────────────────────────────────┐
│      Embedded Asymmetric Crypto Library Comparison              │
│                                                                  │
│  Library    │ ECC (P-256)│ Ed25519 │ RSA  │ PQ   │ Size  │ FIPS│
│  ───────────┼────────────┼─────────┼──────┼──────┼───────┼─────│
│  Mbed TLS   │ Yes+HW     │ Yes     │ Yes  │ No*  │ 50-80K│ Opt.│
│  WolfSSL    │ Yes+HW     │ Yes     │ Yes  │ Yes  │ 20-80K│ Yes │
│  LibSodium  │ No         │ Yes     │ No   │ No   │ 100K+ │ No  │
│  mbedcrypto │ Yes+HW     │ Yes     │ Yes  │ Dev  │ 50-80K│ Opt.│
│  RIOT Crypto│ Yes        │ Yes     │ Ltd. │ No   │ 10-30K│ No  │
│  TinyCrypt  │ Yes (P-256)│ No      │ No   │ No   │ 8-12K │ No  │
│  PQ-Clean   │ No         │ No      │ No   │ Yes  │ varies│ No  │
│                                                                  │
│  * Mbed TLS post-quantum support in development (mbedtls 3.6+)  │
└──────────────────────────────────────────────────────────────────┘
```

**Mbed TLS 3.x** (PSA Crypto API): the reference for ARM-target embedded asymmetric crypto. Supports P-256, P-384, Ed25519, RSA-PSS, X25519, ECDH, and TLS 1.3. Hardware acceleration via PSA driver interface for STM32, NXP, and Nordic platforms. FIPS-validated module available as mbedtls-fips. Correct default for Zephyr RTOS, FreeRTOS with PSA, and bare-metal ARM.

**WolfSSL**: strongest for post-quantum (includes ML-KEM, ML-DSA via LIBOQS integration). FIPS-validated for government/defense applications. Best choice when FIPS 140-3 validation with post-quantum algorithms is required.

**LibSodium**: excellent for Ed25519 and X25519 specifically. Not an embedded-first library — its size and dependencies make it awkward on bare MCUs. Use if your protocol is limited to Ed25519 + X25519 and you do not need TLS or certificate parsing.

**PQ-Clean**: reference implementations of post-quantum algorithms (ML-KEM, ML-DSA, SLH-DSA). Not optimized for embedded use. Useful for testing and validation; production use requires optimized implementations (WolfSSL, or ARM PQCLEAN optimizations).

> **Principle 53.** *Use Mbed TLS with PSA API for general-purpose embedded asymmetric crypto; use WolfSSL when FIPS validation or post-quantum algorithms are required. Never implement ECC from scratch.*

---

## Chapter 54 — Mbed TLS PSA API for Asymmetric Operations

The PSA Crypto API provides a consistent interface for asymmetric operations regardless of hardware acceleration availability. Operations move automatically to hardware when a driver is registered.

**ECDSA signing and verification (PSA Crypto API):**

```c
#include "psa/crypto.h"

/* Initialize */
psa_crypto_init();

/* === KEY GENERATION === */
psa_key_attributes_t attrs = PSA_KEY_ATTRIBUTES_INIT;
psa_set_key_type(&attrs, PSA_KEY_TYPE_ECC_KEY_PAIR(PSA_ECC_FAMILY_SECP_R1));
psa_set_key_bits(&attrs, 256);                    /* P-256 */
psa_set_key_usage_flags(&attrs, PSA_KEY_USAGE_SIGN_HASH | PSA_KEY_USAGE_EXPORT);
psa_set_key_algorithm(&attrs, PSA_ALG_ECDSA(PSA_ALG_SHA_256));

psa_key_id_t key_id;
psa_generate_key(&attrs, &key_id);                /* Uses TRNG via PSA entropy */

/* === EXPORT PUBLIC KEY === */
uint8_t pub_key[65];  /* 04 || x || y, uncompressed P-256 */
size_t pub_len;
psa_export_public_key(key_id, pub_key, sizeof(pub_key), &pub_len);

/* === SIGN === */
uint8_t hash[32];
psa_hash_compute(PSA_ALG_SHA_256, message, msg_len, hash, sizeof(hash), &hash_len);

uint8_t signature[64];  /* 32 bytes r + 32 bytes s */
size_t sig_len;
psa_sign_hash(key_id, PSA_ALG_ECDSA(PSA_ALG_SHA_256),
              hash, 32, signature, sizeof(signature), &sig_len);

/* === VERIFY === */
psa_key_attributes_t verify_attrs = PSA_KEY_ATTRIBUTES_INIT;
psa_set_key_type(&verify_attrs, PSA_KEY_TYPE_ECC_PUBLIC_KEY(PSA_ECC_FAMILY_SECP_R1));
psa_set_key_bits(&verify_attrs, 256);
psa_set_key_usage_flags(&verify_attrs, PSA_KEY_USAGE_VERIFY_HASH);
psa_set_key_algorithm(&verify_attrs, PSA_ALG_ECDSA(PSA_ALG_SHA_256));

psa_key_id_t verify_key_id;
psa_import_key(&verify_attrs, pub_key, pub_len, &verify_key_id);

psa_status_t status = psa_verify_hash(verify_key_id,
              PSA_ALG_ECDSA(PSA_ALG_SHA_256),
              hash, 32, signature, sig_len);
/* PSA_SUCCESS = valid; PSA_ERROR_INVALID_SIGNATURE = invalid */

psa_destroy_key(key_id);
psa_destroy_key(verify_key_id);
```

**ECDH key agreement (PSA Crypto API):**

```c
/* Generate ephemeral key pair for ECDH */
psa_key_attributes_t ecdh_attrs = PSA_KEY_ATTRIBUTES_INIT;
psa_set_key_type(&ecdh_attrs, PSA_KEY_TYPE_ECC_KEY_PAIR(PSA_ECC_FAMILY_SECP_R1));
psa_set_key_bits(&ecdh_attrs, 256);
psa_set_key_usage_flags(&ecdh_attrs, PSA_KEY_USAGE_DERIVE);
psa_set_key_algorithm(&ecdh_attrs, PSA_ALG_ECDH);

psa_key_id_t ecdh_key_id;
psa_generate_key(&ecdh_attrs, &ecdh_key_id);

/* Compute shared secret */
uint8_t shared_secret[32];
size_t ss_len;
psa_raw_key_agreement(PSA_ALG_ECDH, ecdh_key_id,
                      peer_public_key, peer_pub_len,
                      shared_secret, sizeof(shared_secret), &ss_len);

/* Derive AES key from shared secret using HKDF */
psa_key_derivation_operation_t kdf = PSA_KEY_DERIVATION_OPERATION_INIT;
psa_key_derivation_setup(&kdf, PSA_ALG_HKDF(PSA_ALG_SHA_256));
psa_key_derivation_input_bytes(&kdf, PSA_KEY_DERIVATION_INPUT_SALT, salt, salt_len);
psa_key_derivation_input_key(&kdf, PSA_KEY_DERIVATION_INPUT_SECRET, ecdh_key_id);
/* ... */

psa_destroy_key(ecdh_key_id);  /* Zeroize ephemeral key immediately */
```

**Key isolation with PSA:** keys created via `psa_generate_key()` with non-exportable flags remain inside the PSA crypto layer (and in hardware key storage if a driver is present). The raw key bytes never appear in application RAM. This is the correct model for long-term private keys.

> **Principle 54.** *The PSA Crypto API separates key policy from key material; keys created as non-exportable never appear in application memory. This is the correct architecture for protecting device identity keys.*

---

## Chapter 55 — WolfSSL Asymmetric Operations

WolfSSL provides both a native API and, since version 5.0, a PSA Crypto API compatibility layer. For FIPS-validated deployments and post-quantum algorithms, use WolfSSL's native API.

**ECDH with WolfSSL:**

```c
#include <wolfssl/wolfcrypt/ecc.h>

/* Generate ephemeral key pair */
ecc_key our_key;
wc_ecc_init(&our_key);
WC_RNG rng;
wc_InitRng(&rng);
wc_ecc_make_key(&rng, 32, &our_key);  /* 32 bytes = P-256 */

/* Export our public key (to send to peer) */
byte our_pub[65]; word32 pub_len = 65;
wc_ecc_export_x963(&our_key, our_pub, &pub_len);  /* uncompressed 04||x||y */

/* Import peer's public key */
ecc_key peer_key;
wc_ecc_init(&peer_key);
wc_ecc_import_x963(peer_pub, peer_pub_len, &peer_key);

/* Compute shared secret */
byte shared[32]; word32 shared_len = 32;
wc_ecc_shared_secret(&our_key, &peer_key, shared, &shared_len);
/* shared[] is the x-coordinate of (our_priv * peer_pub) */

/* Clean up immediately */
wc_ecc_free(&our_key);
wc_ecc_free(&peer_key);
ForceZero(shared, sizeof(shared));  /* after KDF */
```

**WolfSSL post-quantum (ML-KEM-512):**

```c
#include <wolfssl/wolfcrypt/kyber.h>

KyberKey key;
wc_KyberKey_Init(KYBER512, &key, NULL, INVALID_DEVID);
wc_KyberKey_MakeKey(&key, &rng);

/* Export public key */
byte pub[KYBER512_PUBLIC_KEY_SIZE];  /* 800 bytes */
wc_KyberKey_EncodePublicKey(&key, pub, sizeof(pub));

/* Encapsulation (sender side) */
byte ct[KYBER512_CIPHER_TEXT_SIZE];  /* 768 bytes */
byte shared_secret[KYBER_SS_SZ];     /* 32 bytes */
wc_KyberKey_Encapsulate(&key, ct, shared_secret, &rng);

/* Decapsulation (receiver side) */
wc_KyberKey_Decapsulate(&key, shared_secret, ct, sizeof(ct));

wc_KyberKey_Free(&key);
```

**WolfSSL configuration for minimal embedded asymmetric build:**

```c
#define WOLFSSL_USER_SETTINGS
#define HAVE_ECC
#define HAVE_ECC_KEY_IMPORT
#define HAVE_ECC_KEY_EXPORT
#define ECC_TIMING_RESISTANT          /* constant-time ECC */
#define HAVE_X25519
#define HAVE_ED25519
#define HAVE_ECDH
#define HAVE_ECDSA
#define WC_RSA_PSS
#define WOLFSSL_SHA256
#define NO_DSA
#define NO_DH                         /* classic DH, not ECDH */
#define NO_OLD_TLS
#define STM32_CRYPTO                  /* STM32 hardware acceleration */
```

> **Principle 55.** *WolfSSL's `ECC_TIMING_RESISTANT` flag enables constant-time ECC scalar multiplication; always enable it in production builds. Without it, WolfSSL's ECC is vulnerable to timing attacks.*

---

## Chapter 56 — Test Vectors and CAVP for Asymmetric Algorithms

Test vectors validate correctness; without them, an implementation error may produce plausible-looking output that is subtly wrong.

**Sources for asymmetric test vectors:**

- NIST CAVP: https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program
  - ECDSA: Key Pair Generation, Public Key Validation, Signature Generation, Signature Verification
  - ECDH: Primitive Z computation
  - RSA: Key Generation, Signature Generation/Verification (PKCS1v1.5, PSS)
- RFC 8032 Appendix A: Ed25519 test vectors (7 test cases including edge cases)
- RFC 7748 Appendix A: X25519 test vectors
- NIST FIPS 203 Appendix C: ML-KEM test vectors

**Critical test categories:**

*Known Answer Tests (KAT)*: fixed inputs → expected outputs. Verify that your implementation produces exactly the specified output for each test case.

*Negative tests for signature verification*: corrupted signature (must reject), wrong key (must reject), modified message (must reject). Many implementations only test positive cases and break on these.

*Edge case key values*: private key = 1, private key = n-1, public key = G (generator), public key = infinity. These may be rejected as invalid by some implementations, or processed incorrectly by others.

*X25519 low-order point test*: RFC 7748 specifies specific low-order points for Curve25519. An X25519 implementation should return the all-zeros result for these inputs. Some implementations do not detect this and proceed with the computation, producing weak shared secrets.

**Automated testing in CI:**

```python
# Example: automated CAVP ECDSA verification test
import json, subprocess

with open("CAVP_ECDSA_Verification_Vectors.json") as f:
    vectors = json.load(f)

for v in vectors:
    result = subprocess.run(
        ["./embedded_ecdsa_verify",
         "--curve", v["curve"],
         "--hash", v["hash"],
         "--pub-key", v["Qx"], v["Qy"],
         "--msg", v["msg"],
         "--sig-r", v["R"], "--sig-s", v["S"]],
        capture_output=True
    )
    expected = "PASS" if v["Result"] == "P" else "FAIL"
    actual = result.stdout.strip()
    assert actual == expected, f"CAVP mismatch: {v['tcId']}"
```

> **Principle 56.** *Negative test cases — forged signatures, wrong keys, edge-case inputs — are as important as positive test cases for asymmetric implementations. An implementation that passes positive cases but accepts invalid signatures is actively dangerous.*

---

## Chapter 57 — Profiling Asymmetric Operations on Embedded Targets

Asymmetric crypto profiling requires different instrumentation than symmetric crypto because the costs are measured in seconds, not microseconds.

**Measurement setup (ARM Cortex-M with DWT):**

```c
/* Enable DWT cycle counter */
CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
DWT->CYCCNT = 0;
DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;

/* Measure ECDH phase */
uint32_t start = DWT->CYCCNT;
psa_generate_key(&attrs, &key_id);
uint32_t keygen_cycles = DWT->CYCCNT - start;

DWT->CYCCNT = 0;
psa_raw_key_agreement(PSA_ALG_ECDH, key_id, peer_pub, peer_len,
                      shared, sizeof(shared), &ss_len);
uint32_t ecdh_cycles = DWT->CYCCNT;

printf("P-256 keygen: %lu cycles (%.1f ms at %lu MHz)\n",
       keygen_cycles, (float)keygen_cycles / (SystemCoreClock/1000.0f),
       SystemCoreClock/1000000);
```

**What to profile:**

| Operation | What to Measure | Target (HW PKA) | Target (SW) |
|-----------|----------------|----------------|-------------|
| P-256 keygen | Cycles, ms | < 20 ms | < 1 s |
| P-256 ECDH | Cycles, ms | < 20 ms | < 1 s |
| P-256 ECDSA sign | Cycles, ms | < 20 ms | < 1 s |
| P-256 ECDSA verify | Cycles, ms | < 20 ms | < 1 s |
| Cert chain parse | Cycles, ms, heap peak | < 10 ms | < 100 ms |
| Full TLS handshake | Wall clock, ms | < 100 ms | < 5 s |

**PKA utilization profile:** on targets with hardware PKA, measure whether the PKA is actually being used. Mbed TLS with PSA drivers will use hardware acceleration transparently, but misconfiguration (wrong build flags, missing driver registration) silently falls back to software. Check with a power analyzer: a hardware PKA operation consumes significantly more current than idle but finishes in milliseconds; a software ECC operation sustains moderate CPU-level current for 300–600 ms.

**Stack depth measurement:**

```c
/* Fill stack with pattern before operation */
memset(stack_start, 0xAB, stack_size);
/* Run operation */
psa_generate_key(&attrs, &key_id);
/* Measure deepest uncorrupted pattern */
uint8_t *p = stack_start;
while (*p == 0xAB) p++;
printf("Peak stack use: %zu bytes\n", stack_size - (p - stack_start));
```

> **Principle 57.** *Verify that hardware PKA acceleration is actually executing by measuring power consumption or cycle counts; a misconfigured driver silently falls back to 100× slower software, appearing to work correctly but violating timing requirements.*

---

# Part XI — Mastery

---

## Chapter 58 — Debugging Asymmetric Crypto Failures

Asymmetric failures divide into two classes: computation errors (wrong output) and protocol errors (correct output, wrong context). Distinguishing these first halves the debugging space.

**The debugging procedure:**

```
Step 1: Isolate to primitive or protocol level
────────────────────────────────────────────
Run the failing operation with NIST test vectors.
  → Passes: the primitive is correct; failure is in protocol logic
  → Fails: the primitive is wrong; debug key format, endianness, curve selection

Step 2 (primitive failure): check key format
────────────────────────────────────────────
Dump the key bytes used in the operation.
  P-256 private key: 32 bytes, value in [1, n-1]
  P-256 public key (uncompressed): 0x04 || x || y (65 bytes)
  Ed25519 private key seed: 32 random bytes
  Ed25519 public key: 32 bytes (y-coordinate with sign bit)
  Are bytes in correct endianness? (P-256 uses big-endian)
  Is the correct point format used (uncompressed vs compressed)?

Step 3 (protocol failure): check algorithm identifiers
──────────────────────────────────────────────────────
What signature algorithm OID is in the certificate?
What algorithm does the verifier expect?
Mismatch → PSA_ERROR_NOT_SUPPORTED or "signature algorithm mismatch"

Step 4 (protocol failure): check certificate chain order
────────────────────────────────────────────────────────
Chain must be: [leaf cert] → [intermediate CA] → [root CA]
Reversed order → "issuer not found" error
Missing intermediate → "chain incomplete"
Wrong trust anchor → "untrusted root"

Step 5 (signature failure): check message being signed
──────────────────────────────────────────────────────
ECDSA/EdDSA sign over the message hash (not the message directly for ECDSA).
Verify that both sides hash the same bytes in the same order.
Endianness, padding, or framing differences in the message → signature mismatch.
```

**Common interoperability failures and their causes:**

| Symptom | Likely Cause |
|---------|-------------|
| `PSA_ERROR_INVALID_SIGNATURE` | Key mismatch, message mismatch, or wrong algorithm |
| `PSA_ERROR_NOT_SUPPORTED` | OID not registered in library or hardware driver |
| Signature verifies on host, fails on device | Endianness difference in key or message encoding |
| Certificate chain validation fails | Incomplete chain, wrong issuer/subject, time mismatch |
| TLS handshake fails at ServerKeyExchange | Curve not supported by one side |
| TLS handshake fails at Finished | Key derivation mismatch; usually endianness in ECDH output |
| Ed25519 verify fails for specific messages | Point validation bug; check cofactor handling |
| RSA sign produces different output each time | PSS randomization (correct behavior); use PSS with salt=0 for determinism |
| X25519 shared secret differs on two sides | One side did not clamp private key; one side used compressed point format |

> **Principle 58.** *Asymmetric failures fall into primitive errors (test with NIST vectors) or protocol errors (check key format, algorithm identifiers, and certificate chain order). Start with primitive validation before debugging the protocol.*

---

## Chapter 59 — Architectural Patterns for Asymmetric Crypto in Embedded Systems

Three architectural patterns handle the challenge of asymmetric crypto on constrained hardware.

**Pattern 1: Asymmetric at Edges, Symmetric in the Interior**

Perform all asymmetric operations at the edge of the system — at initial provisioning, at initial connection establishment, and at key rotation events. Everything inside the system uses symmetric keys derived from the asymmetric operations.

```
┌───────────────────────────────────────────────────────────────┐
│                   System Architecture                         │
│                                                               │
│  ┌──────────────┐  mTLS  ┌──────────────────────────────┐    │
│  │   Device     │───────►│         Cloud Backend         │    │
│  │              │        │                               │    │
│  │ Asymmetric:  │        │  Verifies device cert         │    │
│  │ ECDH + ECDSA │        │  Derives session key          │    │
│  │ (at connect) │        └──────────────────────────────┘    │
│  │              │                                             │
│  │ Symmetric:   │                                             │
│  │ AES-GCM      │                                             │
│  │ (all data)   │                                             │
│  └──────────────┘                                             │
└───────────────────────────────────────────────────────────────┘
```

**Pattern 2: Offload Asymmetric to Secure Element**

Delegate all asymmetric operations to a secure element (SE) via I²C/SPI. The MCU sends `Sign(message_hash)` commands; the SE returns the signature. The private key never leaves the SE.

This pattern handles targets with no hardware PKA. The SE does the expensive computation (20–50 ms per operation via I²C); the MCU does symmetric operations. The tradeoff is latency — SE operations over I²C at 400 kHz take 20–100 ms.

**Pattern 3: Bootloader-Only Asymmetric**

Reserve asymmetric operations exclusively for secure boot (signature verification). The application layer uses only symmetric keys provisioned during the initial secure boot sequence. This minimizes the asymmetric code in the application — only the bootloader needs asymmetric crypto, which reduces attack surface.

The provisioning event (where asymmetric keys are established) occurs at manufacturing time or during a factory-reset flow, not during normal operation.

```
Boot flow:
  Bootloader (128 KB flash, asymmetric) → verifies firmware → jumps to application
  Application (remaining flash, symmetric only) → all operations use AES-GCM

Asymmetric code footprint: bootloader only (~30 KB for RSA verify)
Application crypto footprint: symmetric only (~10 KB for AES-GCM + HMAC)
```

> **Principle 59.** *On constrained targets, confine asymmetric operations to: initial provisioning, connection establishment, and firmware verification. Use symmetric keys for all runtime operations.*

---

## Chapter 60 — Common Errors and Their Meaning

| Error / Symptom | Root Cause | Diagnostic | Fix |
|-----------------|-----------|-----------|-----|
| ECDSA verification always fails | Key mismatch; wrong curve; message hash differs | Dump key and message hash on both sides | Match keys; match hash algorithm |
| ECDSA verification occasionally fails | Non-deterministic nonce; TRNG bias | Use RFC 6979 | Enable RFC 6979 deterministic signing |
| X25519 shared secret differs | Private key not clamped; wrong point format | Verify clamping; check compressed vs uncompressed | Use library that clamps; standardize format |
| Certificate chain validation fails | Incomplete chain; wrong order; expired | Print each cert's Subject and Issuer; check dates | Deliver full chain; fix order; check clock |
| TLS handshake fails at Certificate Verify | Wrong key type for algorithm in cert | Check KeyUsage extension; check algorithm OID | Match key type to algorithm; set KeyUsage |
| Ed25519 sign produces same output twice | Correct — Ed25519 is deterministic | None; this is expected | Document as expected |
| RSA keygen takes 30 seconds | No hardware PKA; large prime search | Profile with DWT | Use hardware PKA or move keygen to provisioning |
| PSA_ERROR_NOT_SUPPORTED | Algorithm OID not linked or driver absent | Check build flags; check PSA driver registration | Add algorithm to build; register driver |
| Memory corruption during TLS handshake | Stack overflow from ECC peak stack use | Measure stack depth with pattern fill | Increase stack by 4–8 KB |
| Signature verifies on PC, fails on device | Big/little endian difference | Dump bytes on both sides | Use explicit endian conversion; standardize |
| ML-KEM ciphertext does not decapsulate | Wrong ML-KEM parameter set used | Verify both sides use same security level | Standardize on ML-KEM-512 or ML-KEM-768 |
| Certificate accepted after revocation | No revocation check; time check disabled | Add backend-enforced revocation | Implement backend revocation database |

---

## Chapter 61 — How to Actually Learn Embedded Asymmetric Cryptography

The standard tutorial path for asymmetric cryptography in embedded systems is counterproductive. The standard path: read a general cryptography textbook focused on mathematical proof, implement RSA from scratch to "understand" the algorithm, then try to apply it to TLS on a microcontroller. The result is an architect who can explain modular exponentiation but cannot explain why ECDSA with a weak nonce leaks the private key.

**Forget the standard path. Begin here instead.**

*Start with protocol specifications, not algorithms.* Read RFC 8446 (TLS 1.3). Trace the key schedule. Understand what `HKDF-Extract` and `HKDF-Expand` do. Understand why the TLS 1.3 handshake produces forward secrecy. You will encounter ECDH and ECDSA as protocol components before understanding them as mathematical objects. This is the right order.

*Build and attack a toy ECDSA implementation.* Implement ECDSA in Python (not C, not on embedded) using a library's field arithmetic. Then attack it: use the same nonce for two different messages and derive the private key. This takes 20 lines of Python. The attack makes the vulnerability visceral in a way that reading about it does not.

*Read the failure literature before the construction literature.* Start with:
- "Return of the Coppersmith Attack" (ROCA, Nemec et al., 2017) — RSA key generation failure in Infineon chips
- "Factorable Keys in the Wild" (Heninger et al., 2012) — correlated TRNG in embedded RSA keys
- "Biased ECDSA Nonces" (Breitner, Heninger, 2019) — nonce bias enables private key recovery

Each paper teaches a failure mode that reveals a design requirement. Reading attacks teaches security requirements; reading constructions teaches how to meet them.

*Study one hardware implementation completely.* Take the STM32H5 PKA peripheral. Read every page of the PKA chapter in the reference manual. Implement ECDH in bare-metal C using only the PKA registers — no HAL, no library. You will understand DMA coupling, operand loading, endianness handling, and interrupt timing. This cannot be learned by reading about it.

*The five primary sources:*

1. RFC 8446 (TLS 1.3): the reference protocol — every asymmetric primitive in context.
2. RFC 7748 + RFC 8032 (X25519 + Ed25519): the cleanest modern asymmetric primitives.
3. NIST FIPS 186-4 (ECDSA): the normative specification for the dominant embedded signature scheme.
4. *Real-World Cryptography* (Wong, 2021): the only general cryptography book that covers implementation in non-trivial depth.
5. Your SoC's PKA chapter in its reference manual: the implementation reality.

The one thing to avoid: tutorials that use OpenSSL on a Raspberry Pi and call it "embedded cryptography." The OpenSSL API, the Linux random number subsystem, and the ARM Cortex-A performance profile are not the constraints that matter. The Cortex-M PKA register interface, the TRNG health test flag, and the 32 KB RAM budget are.

> **Principle 61.** *Learn asymmetric cryptography by reading attack papers first: the attacks reveal the security requirements, and the security requirements explain the design decisions. Understanding the failures makes the constructions self-evident.*

---

# Appendices

---

## Appendix A — Algorithm and Key Size Reference

| Algorithm | Category | Key Sizes | Security Level | Standard | Quantum Safe |
|-----------|----------|-----------|----------------|----------|-------------|
| ECDSA-P256 | Signature | 256-bit | 128-bit classical | FIPS 186-4 | No |
| ECDSA-P384 | Signature | 384-bit | 192-bit classical | FIPS 186-4 | No |
| Ed25519 | Signature | 256-bit | 128-bit classical | RFC 8032 | No |
| RSA-PSS-2048 | Signature | 2048-bit | 112-bit classical | FIPS 186-4 | No |
| RSA-PSS-3072 | Signature | 3072-bit | 128-bit classical | FIPS 186-4 | No |
| ECDH-P256 | Key agreement | 256-bit | 128-bit classical | FIPS SP 800-56A | No |
| X25519 | Key agreement | 256-bit | 128-bit classical | RFC 7748 | No |
| RSA-OAEP-2048 | Key encap | 2048-bit | 112-bit classical | RFC 8017 | No |
| ML-KEM-512 | Key encap (PQ) | 800/1632-bit | ~128-bit PQ | FIPS 203 | Yes |
| ML-KEM-768 | Key encap (PQ) | 1184/2400-bit | ~192-bit PQ | FIPS 203 | Yes |
| ML-DSA-44 | Signature (PQ) | 1312/2528-bit | ~128-bit PQ | FIPS 204 | Yes |
| ML-DSA-65 | Signature (PQ) | 1952/4000-bit | ~192-bit PQ | FIPS 204 | Yes |
| SLH-DSA-128s | Signature (PQ hash) | 32-bit | ~128-bit PQ | FIPS 205 | Yes |

---

## Appendix B — Operation Performance Reference

Approximate timings on ARM Cortex-M4 at 168 MHz (software) and ARM Cortex-M33 at 64 MHz with hardware PKA.

| Operation | SW (M4, 168 MHz) | HW PKA (M33, 64 MHz) | Notes |
|-----------|-----------------|----------------------|-------|
| P-256 keygen | 300–600 ms | 5–20 ms | Single scalar mult + TRNG |
| P-256 ECDH | 300–600 ms | 5–20 ms | Single scalar mult |
| P-256 ECDSA sign | 300–600 ms | 5–20 ms | RFC 6979; one scalar mult |
| P-256 ECDSA verify | 300–600 ms | 5–20 ms | Two scalar mults |
| Ed25519 sign | 150–300 ms | 5–30 ms | Deterministic; one mult |
| Ed25519 verify | 300–500 ms | 10–40 ms | Two scalar mults |
| X25519 (one side) | 150–300 ms | 5–20 ms | One scalar mult |
| RSA-2048 keygen | 5–30 s | 0.5–3 s | Primality testing dominant |
| RSA-2048 sign | 1–3 s | 50–200 ms | CRT optimization important |
| RSA-2048 verify | 20–50 ms | 2–10 ms | Small exponent (65537) |
| ML-KEM-512 keygen | 1–3 ms | — | No HW accel currently |
| ML-KEM-512 encaps | 1–3 ms | — | |
| ML-KEM-512 decaps | 1–3 ms | — | |
| ML-DSA-44 sign | 3–10 ms | — | |
| ML-DSA-44 verify | 2–6 ms | — | |
| P-256 cert verify (chain of 3) | ~1–2 s | 20–60 ms | 3 ECDSA verifications + parsing |

---

## Appendix C — ASN.1 / DER / PEM Cheat Sheet

**DER encoding rules (relevant for embedded certificate parsing):**

```
TLV structure: Tag || Length || Value

Tags:
0x02  INTEGER
0x03  BIT STRING
0x04  OCTET STRING
0x05  NULL
0x06  OBJECT IDENTIFIER
0x13  PrintableString
0x17  UTCTime
0x18  GeneralizedTime
0x30  SEQUENCE
0x31  SET
0xA0  [0] CONTEXT-SPECIFIC EXPLICIT
0xA3  [3] CONTEXT-SPECIFIC EXPLICIT (extensions in X.509)

Length encoding:
0x00–0x7F: short form (1 byte = length)
0x81 LL:   long form, 1-byte length LL
0x82 LL LL: long form, 2-byte length

P-256 public key (SubjectPublicKeyInfo, uncompressed):
30 59           SEQUENCE
  30 13         SEQUENCE (algorithm)
    06 07 2a 86 48 ce 3d 02 01  OID id-ecPublicKey
    06 08 2a 86 48 ce 3d 03 01 07  OID prime256v1
  03 42 00      BIT STRING (66 bytes, 0 unused bits)
    04           uncompressed point indicator
    <32 bytes x>
    <32 bytes y>
```

**PEM to DER:**
```bash
openssl x509 -in cert.pem -outform DER -out cert.der
openssl pkey -in key.pem -outform DER -out key.der
```

**Inspect DER:**
```bash
openssl asn1parse -inform DER -in cert.der
openssl x509 -inform DER -in cert.der -text -noout
```

**Compressed vs uncompressed EC points:**
- Uncompressed: `04 || x || y` (65 bytes for P-256)
- Compressed: `02 || x` (if y is even) or `03 || x` (if y is odd) (33 bytes for P-256)
- Recovery: given compressed point, recover y by solving y² = x³ + ax + b mod p

---

## Appendix D — OID Reference for Embedded PKI

**Signature algorithm OIDs:**

| OID | Name | Curve | Hash |
|-----|------|-------|------|
| 1.2.840.10045.4.3.2 | ecdsa-with-SHA256 | any ECDSA | SHA-256 |
| 1.2.840.10045.4.3.3 | ecdsa-with-SHA384 | any ECDSA | SHA-384 |
| 1.2.840.10045.4.3.4 | ecdsa-with-SHA512 | any ECDSA | SHA-512 |
| 1.3.101.112 | id-Ed25519 | Ed25519 | built-in |
| 1.2.840.113549.1.1.11 | sha256WithRSAEncryption | RSA | SHA-256 |
| 1.2.840.113549.1.1.10 | id-RSASSA-PSS | RSA-PSS | in params |

**Curve OIDs:**

| OID | Curve | Key Size |
|-----|-------|----------|
| 1.2.840.10045.3.1.7 | prime256v1 (P-256) | 256-bit |
| 1.3.132.0.34 | secp384r1 (P-384) | 384-bit |
| 1.3.132.0.35 | secp521r1 (P-521) | 521-bit |
| 1.3.36.3.3.2.8.1.1.7 | brainpoolP256r1 | 256-bit |
| 1.3.101.110 | id-X25519 | 255-bit |
| 1.3.101.112 | id-Ed25519 | 255-bit |

**Certificate extension OIDs:**

| OID | Extension |
|-----|-----------|
| 2.5.29.15 | KeyUsage |
| 2.5.29.37 | ExtendedKeyUsage |
| 2.5.29.17 | SubjectAltName |
| 2.5.29.19 | BasicConstraints |
| 2.5.29.14 | SubjectKeyIdentifier |
| 2.5.29.35 | AuthorityKeyIdentifier |
| 2.5.29.31 | CRLDistributionPoints |
| 1.3.6.1.5.5.7.1.1 | AuthorityInfoAccess (OCSP) |

**Extended Key Usage values:**

| OID | Name | Use |
|-----|------|-----|
| 1.3.6.1.5.5.7.3.1 | serverAuth | TLS server |
| 1.3.6.1.5.5.7.3.2 | clientAuth | mTLS device auth |
| 1.3.6.1.5.5.7.3.3 | codeSigning | Firmware signing |

---

## Appendix E — Glossary

**Attestation**: A signed report from a device proving its identity and firmware integrity state, rooted in hardware.

**CA (Certificate Authority)**: An entity that issues and signs certificates, vouching for the binding of public keys to identities.

**Clamping**: The operation applied to X25519/Ed25519 private key bytes that clears specific bits for cofactor neutralization and sets the high bit for constant-time scalar multiplication.

**CSR (Certificate Signing Request)**: A PKCS#10 structure containing a public key and a signature with the corresponding private key, submitted to a CA for certificate issuance.

**DER (Distinguished Encoding Rules)**: The canonical binary encoding of ASN.1 structures. Used for all certificate and key wire formats in TLS.

**DHE (Diffie-Hellman Ephemeral)**: Key agreement using freshly generated key pairs per session. Provides forward secrecy.

**ECDH (Elliptic Curve Diffie-Hellman)**: Key agreement protocol on elliptic curves.

**ECDSA (Elliptic Curve Digital Signature Algorithm)**: Signature scheme based on elliptic curves; defined in FIPS 186-4.

**EdDSA (Edwards-curve Digital Signature Algorithm)**: Signature scheme on twisted Edwards curves; defined in RFC 8032. Ed25519 is the standard instance.

**Forward Secrecy**: Property ensuring that compromise of long-term keys does not expose past session traffic.

**KDF (Key Derivation Function)**: A function deriving cryptographic key material from a secret input (HKDF, SP 800-108 Counter KDF).

**KEM (Key Encapsulation Mechanism)**: A mechanism where the sender generates a random key and encapsulates it under the recipient's public key.

**Lattice**: A discrete, periodic structure in n-dimensional space; the basis for post-quantum cryptographic constructions.

**ML-DSA (Module-Lattice Digital Signature Algorithm)**: NIST FIPS 204; the standardized post-quantum signature scheme (formerly CRYSTALS-Dilithium).

**ML-KEM (Module-Lattice Key Encapsulation Mechanism)**: NIST FIPS 203; the standardized post-quantum KEM (formerly CRYSTALS-Kyber).

**mTLS (Mutual TLS)**: TLS where both client and server present certificates, enabling mutual authentication.

**OID (Object Identifier)**: A globally unique dotted-decimal identifier used in ASN.1 to name algorithms, extensions, and certificate fields.

**OAEP (Optimal Asymmetric Encryption Padding)**: RSA encryption padding scheme that is provably secure. RSA-OAEP is the correct RSA encryption mode.

**PEM (Privacy Enhanced Mail)**: Base64-encoded DER with `-----BEGIN X-----` headers. Human-readable; not used in embedded wire protocols.

**PKA (Public Key Accelerator)**: A hardware unit performing modular arithmetic and ECC operations, integrated into ARM Cortex-M SoCs.

**PKI (Public Key Infrastructure)**: The systems, policies, and certificates that bind public keys to identities.

**PSA (Platform Security Architecture)**: ARM's security framework defining hardware isolation, attestation, and a portable cryptographic API (PSA Crypto API).

**RSA-PSS (RSA Probabilistic Signature Scheme)**: Correct RSA signature mode with random salt and proven security. Defined in PKCS#1 v2.1.

**Scalar multiplication**: The operation d * G on an elliptic curve (computing G added to itself d times). The core operation of all ECC.

**Secure boot**: The process of verifying firmware signatures before execution, establishing a chain of trust from hardware ROM to application firmware.

**Shor's algorithm**: A quantum algorithm that solves integer factorization and discrete logarithm in polynomial time, breaking RSA and ECC.

**Static DH**: Key agreement using long-lived (non-ephemeral) key pairs. No forward secrecy.

**Trust anchor**: A CA certificate embedded in a system that is trusted unconditionally — the root of the certificate chain.

**X.509**: The ITU-T standard defining the format of public key certificates, used in TLS, secure boot, and device identity.

**X25519**: ECDH on Curve25519 using x-coordinate-only arithmetic. Defined in RFC 7748.

---

> *Asymmetric cryptography does not fail because the mathematics breaks. It fails because someone reused a nonce, because the TRNG was not ready at provisioning time, because the certificate chain was delivered in reverse order, or because the clock was wrong and the certificate was considered expired. The mathematics is the easy part. The engineering is the hard part.*

# PKI Architecture — Zero to Hero
### A Manual of First Principles

> *Built from the ground up. Every concept earns its place. Every diagram exists because words alone would be longer.*

---

## Preface

Public Key Infrastructure (PKI) is one of the most frequently *used* and least frequently *understood* systems in computing. Most engineers interact with PKI daily — TLS handshakes, code signing, VPN authentication — yet treat it as an opaque trust appliance: certificates "just work" until they expire or a chain fails to validate, at which point the system becomes a black box of acronyms (CA, CRL, OCSP, AIA, SAN).

This guide exists because most PKI documentation falls into one of two failure modes:

1. **Vendor documentation** that explains *how* to click through a CA product's wizard without explaining *why* the wizard asks what it asks.
2. **Cryptography textbooks** that explain asymmetric mathematics in exhaustive depth but stop short of the operational architecture — hierarchies, revocation, key ceremonies — that make PKI usable at scale.

This document treats PKI as what it actually is: a **distributed trust system** built on a small number of cryptographic primitives, combined with operational rules that exist to bound the *blast radius* of failure. Every structural choice in PKI — offline root CAs, certificate chains, revocation mechanisms, short validity periods — is a direct answer to a specific failure mode. Understanding the failure mode is understanding the architecture.

**Prerequisites.** This guide assumes working knowledge of: symmetric vs. asymmetric encryption at a conceptual level, hashing functions, and basic networking (TCP/IP, TLS handshake at a black-box level). It does not re-derive RSA or elliptic curve mathematics from number theory.

**Scope and limits.** This guide does not cover: the internal mathematics of specific algorithms (RSA key generation, ECDSA curve arithmetic), vendor-specific CA product configuration (Microsoft ADCS, EJBCA, Vault PKI UI walkthroughs), or blockchain-based trust models (Web3 PKI alternatives). Where a vendor example is given, it illustrates a *general* mechanism, not a product recommendation.

**Outcome.** After Part III you will be able to read and reason about any certificate chain. After Part V you will be able to design a CA hierarchy for a real organization. After Part VII you will understand how production PKI systems fail and how that failure is contained.

---

## Table of Contents

- **Part I — Foundations**
  - 1. The Trust Problem PKI Solves
  - 2. Component Taxonomy
- **Part II — Cryptographic Primitives**
  - 3. Asymmetric Keys and Digital Signatures
  - 4. The X.509 Certificate
- **Part III — Trust Architecture**
  - 5. Certificate Chains and Hierarchies
  - 6. Certificate Extensions and Policy
- **Part IV — Lifecycle Management**
  - 7. Issuance: From Key Pair to Certificate
  - 8. Revocation: CRL and OCSP
  - 9. Renewal, Rekeying, and Validity Periods
- **Part V — Operational Architecture**
  - 10. CA Hierarchy Design
  - 11. Key Protection and HSMs
  - 12. Repository and Distribution
- **Part VI — Protocols and Path Validation**
  - 13. Enrollment Protocols (CSR, SCEP, EST, ACME, CMP)
  - 14. Certification Path Validation (RFC 5280)
- **Part VII — Production Operations**
  - 15. Deployment Patterns and Key Ceremonies
  - 16. Compromise Response and Failure Modes
  - 17. Monitoring, Transparency, and Audit
- **Appendices**
  - A — X.509 Fields to Memorize
  - B — Glossary
  - C — Protocol and Algorithm Comparison Tables
  - D — Learning Path

---

# Part I — Foundations

## 1. The Trust Problem PKI Solves

**Formal problem statement.** Two parties, A and B, who have never met and share no prior secret, need to (a) communicate confidentially and (b) be certain of each other's identity, over a network controlled by adversaries.

Asymmetric cryptography solves the mechanics of (a): if B has a public key, anyone can encrypt data only B can decrypt, and B can sign data anyone can verify. But asymmetric cryptography alone does **not** solve identity. A public key is just a number. Nothing about the number says "this belongs to B." An adversary can generate their own key pair and claim it belongs to B.

```
┌─────────────────────────────┐
│  A receives a public key     │
│  claiming to be "B's key"    │
└──────────────┬───────────────┘
               │
               ▼
   Is this REALLY B's key,
   or an attacker's key
   presented as B's key?
               │
               ▼
┌─────────────────────────────┐
│  Without a trusted third     │
│  party: NO WAY TO KNOW       │
└─────────────────────────────┘
```

PKI's entire purpose is to close this gap: bind a public key to an identity, via a statement that other parties have agreed in advance to trust.

> **Principle 1.** *A public key is cryptographically strong but semantically empty; PKI exists to attach meaning (identity) to it through a trusted third party's signed assertion.*

That signed assertion is a **certificate**. The trusted third party is a **Certificate Authority (CA)**. Everything else in this guide is the operational machinery required to make that one signed assertion trustworthy, distributable, revocable, and survivable at scale.

---

## 2. Component Taxonomy

PKI is a system of roles, not a single piece of software. The roles can be implemented by separate systems or collapsed into one, but the roles themselves are fixed.

| Component | Role | Trust Function |
|---|---|---|
| **Certificate Authority (CA)** | Issues and signs certificates | Source of trust; binds key to identity |
| **Registration Authority (RA)** | Verifies identity before issuance | Gatekeeper; CA delegates vetting to it |
| **Validation Authority (VA)** | Answers "is this certificate still valid?" | Real-time trust freshness (OCSP responder) |
| **Repository** | Stores/publishes certificates and revocation data | Distribution of trust artifacts |
| **End Entity** | The subject of a certificate (server, user, device) | Consumer/holder of the trust assertion |
| **Relying Party** | Verifies a certificate to make a trust decision | Final consumer of the entire system |

```
┌────────────┐   verifies identity    ┌────────────┐
│     RA     │───────────────────────▶│     CA     │
└────────────┘                        └─────┬──────┘
                                             │ signs certificate
                                             ▼
┌────────────┐   presents certificate ┌────────────┐
│ Relying    │◀────────────────────── │ End Entity │
│ Party      │                        └────────────┘
└─────┬──────┘
      │ checks revocation status
      ▼
┌────────────┐
│     VA     │ (OCSP) / Repository (CRL)
└────────────┘
```

> **Principle 2.** *Separating roles (CA, RA, VA) is a security control, not bureaucratic overhead: it ensures no single compromised system can both vet an identity and mint a trusted signature unchecked.*

This separation reappears at every layer of the guide: offline root CAs delegate signing to online intermediates (Chapter 10), CAs delegate domain validation to automated RAs in ACME (Chapter 13), and OCSP responders are deliberately given a narrower trust scope than the CA itself (Chapter 8).

---

# Part II — Cryptographic Primitives

## 3. Asymmetric Keys and Digital Signatures

A PKI rests on exactly one cryptographic primitive used in two directions:

- **Encryption direction**: encrypt with the public key, decrypt only with the private key → confidentiality.
- **Signature direction**: sign with the private key, verify with the public key → authenticity and integrity.

PKI certificates use the **signature direction exclusively**. The CA never encrypts anything for the end entity; it signs a statement about the end entity's public key.

```
        Subject's keypair                CA's keypair
   ┌─────────────┬─────────────┐   ┌─────────────┬─────────────┐
   │ Private Key │ Public Key  │   │ Private Key │ Public Key  │
   │ (kept secret│ (placed in  │   │ (offline,   │ (preloaded  │
   │  by subject)│ certificate)│   │  guarded)   │ in trust    │
   │             │             │   │             │ stores)     │
   └─────────────┴─────────────┘   └─────────────┴─────────────┘
          │                                │
          │  signs the CSR                 │ signs the certificate
          ▼                                ▼
   proves subject HOLDS            proves CA VOUCHES FOR
   the private key                 the binding
```

A digital signature is computed as: `signature = Sign(hash(data), CA_private_key)`. Verification recomputes `hash(data)` and checks it against `Verify(signature, CA_public_key)`. This gives two guarantees simultaneously: **integrity** (data wasn't altered) and **authenticity** (only the holder of the private key could have produced the signature).

> **Principle 3.** *A certificate is not encrypted data — it is a signed statement. Its confidentiality is irrelevant; its tamper-evidence is everything.* This is why certificates are routinely transmitted in plaintext (e.g., during the TLS handshake, before any session key exists) without weakening security.

---

## 4. The X.509 Certificate

X.509 is the formal data structure that encodes the "signed statement" from Principle 1. It is defined by ITU-T X.509 and profiled for the Internet by **RFC 5280**.

```
┌───────────────────────────────────────────┐
│ Certificate                               │
│ ┌───────────────────────────────────────┐ │
│ │ TBSCertificate (To Be Signed)          │ │
│ │  - Version                             │ │
│ │  - Serial Number                       │ │
│ │  - Signature Algorithm (declared)      │ │
│ │  - Issuer (the CA's identity)          │ │
│ │  - Validity (notBefore / notAfter)     │ │
│ │  - Subject (the end entity's identity) │ │
│ │  - Subject Public Key Info             │ │
│ │  - Extensions (SAN, KeyUsage, etc.)    │ │
│ └───────────────────────────────────────┘ │
│  Signature Algorithm (actual)             │
│  Signature Value  ◀── CA signs everything │
│                       above with its       │
│                       private key          │
└───────────────────────────────────────────┘
```

A minimal annotated example, viewed via OpenSSL:

```bash
openssl x509 -in server.crt -noout -text
```
```text
Certificate:
    Data:
        Version: 3 (0x2)                     # X.509v3 — required for extensions
        Serial Number: 04:3f:...             # Unique per issuing CA; used in revocation
        Signature Algorithm: sha256WithRSAEncryption
        Issuer: CN=Example Intermediate CA    # WHO is vouching
        Validity
            Not Before: Jun 1 00:00:00 2026 GMT
            Not After : Aug 30 23:59:59 2026 GMT   # Short lifetime — see Ch.9
        Subject: CN=www.example.com           # WHAT is being vouched for
        Subject Public Key Info:
            Public Key Algorithm: id-ecPublicKey
            ECDSA Public Key: (256 bit)        # The subject's own public key
        X509v3 extensions:
            X509v3 Subject Alternative Name:
                DNS:www.example.com, DNS:example.com
            X509v3 Key Usage: critical
                Digital Signature              # Constrains what this key may be used for
            X509v3 Basic Constraints: critical
                CA:FALSE                       # Prevents this cert from issuing other certs
    Signature Algorithm: sha256WithRSAEncryption
    Signature Value: 4a:91:...                # CA's signature over the Data block above
```

Each field exists to answer one question a relying party must ask before trusting a key:

| Question | Field |
|---|---|
| Who claims this key? | `Subject`, `Subject Alternative Name` |
| Who vouches for the claim? | `Issuer` |
| What is the key, exactly? | `Subject Public Key Info` |
| Until when is the vouching valid? | `Validity` |
| For what purposes is this key authorized? | `Key Usage`, `Extended Key Usage` |
| Can this entity itself issue certificates? | `Basic Constraints` |
| Is the vouching statement intact? | `Signature Value` |

> **Principle 4.** *Every field in a certificate exists to let a relying party answer a specific trust question without contacting the CA in real time.* This offline-verifiability property is what allows PKI to scale to billions of daily TLS handshakes — the alternative, contacting the CA synchronously for every connection, does not scale (this tension reappears in Chapter 8 on revocation).

---

# Part III — Trust Architecture

## 5. Certificate Chains and Hierarchies

A single CA signing every end-entity certificate directly creates a single catastrophic point of failure: if that CA's private key is compromised, every certificate it ever issued is suspect, and the only remedy is informing every relying party to stop trusting that CA's public key entirely (removing it from trust stores).

PKI solves this with **hierarchical delegation**: a root CA does not sign end-entity certificates. It signs certificates for *intermediate* CAs, which in turn sign end-entity certificates.

```
                    ┌─────────────────────────────┐
                    │          Root CA             │
                    │  self-signed, offline,       │
                    │  rarely used                  │
                    └───────────┬─────────┬─────────┘
                       signs    │         │   signs
                ┌────────────────┘         └────────────────┐
                ▼                                            ▼
   ┌─────────────────────────┐                 ┌─────────────────────────┐
   │   Intermediate CA A       │                 │   Intermediate CA B       │
   │   online, issues daily    │                 │   different business unit │
   └───────┬─────────┬─────────┘                 └────────────┬────────────┘
   signs   │         │  signs                                  │ signs
       ┌───┘         └───┐                                     ▼
       ▼                 ▼                          ┌─────────────────────┐
┌─────────────┐   ┌─────────────┐                    │  End-entity cert     │
│ End-entity   │   │ End-entity   │                    │  mail.example.com   │
│ www.example  │   │ api.example  │                    └─────────────────────┘
│ .com         │   │ .com         │
└─────────────┘   └─────────────┘
```

A **root certificate** is self-signed: the issuer and subject are the same entity, and it is trusted not because a signature proves anything (a self-signature proves nothing about external trust) but because it is **pre-installed, out-of-band, in relying parties' trust stores** (operating systems, browsers). This is the one and only place where trust is *not* established by a signature — it is established by distribution.

Verification works by walking the chain backward to a trusted root:

```
End-entity cert ──signed by──▶ Intermediate CA cert ──signed by──▶ Root CA cert
      │                              │                                  │
      │                              │                                  ▼
      │                              │                         Already in local
      │                              │                         trust store?
      │                              │                              YES → TRUSTED
      ▼                              ▼
 Verify signature              Verify signature
 using Intermediate's          using Root's public
 public key                    key (self-verifying,
                                pre-trusted)
```

> **Principle 5.** *Trust is delegated downward through signatures, but anchored upward only by out-of-band distribution.* The root's authority does not come from cryptography — it comes from the fact that a billion devices were configured, by humans, ahead of time, to trust it. This is why root CA compromise is catastrophic and root key ceremonies (Chapter 15) are so heavily ritualized: cryptography cannot save you if the anchor itself is wrong.

The intermediate layer exists specifically so the **root's private key can stay offline** — used only during rare events (issuing a new intermediate, signing a new CRL) — while day-to-day issuance happens on intermediates that are easier to operate but also easier to attack, and therefore easier to **revoke without invalidating the whole hierarchy**.

---

## 6. Certificate Extensions and Policy

Extensions are the mechanism by which X.509 expresses *constraints* on trust, not just identity. Without constraints, any certificate could claim any capability.

| Extension | Purpose | Marked Critical? |
|---|---|---|
| `Basic Constraints` | Declares if subject is a CA (`CA:TRUE/FALSE`) and max chain depth (`pathLenConstraint`) | Usually yes |
| `Key Usage` | Restricts cryptographic operations (signing, key encipherment, CRL signing) | Usually yes |
| `Extended Key Usage` | Restricts application purpose (TLS server auth, code signing, email protection) | Often |
| `Subject Alternative Name (SAN)` | Lists all valid identities (DNS names, IPs) — modern TLS ignores the `Subject CN` for this purpose | No |
| `Name Constraints` | Restricts what namespace a CA may issue into (e.g., only `*.example.com`) | Yes |
| `Certificate Policies` | References a formal policy document (OID) describing issuance practices | No |
| `Authority Information Access (AIA)` | URL to fetch the issuer's certificate (chain building) | No |
| `CRL Distribution Points (CDP)` | URL to fetch revocation data | No |

"Critical" is itself a formal X.509 mechanism: if a relying party does not understand a critical extension, it **must reject the certificate**, rather than silently ignore the constraint it cannot enforce.

> **Principle 6.** *An extension that constrains trust is only meaningful if non-support fails closed.* `Basic Constraints: CA:FALSE` marked critical is what prevents an ordinary leaf certificate's private key — if stolen — from being abused to mint new, fraudulent end-entity certificates. A non-critical version of the same field would be merely advisory.

`Name Constraints` deserves particular attention because it generalizes Principle 2's role separation into cryptography itself: a subordinate CA can be mathematically restricted to issuing only within a namespace (e.g., a company's internal `.corp` domain), so that even full compromise of that intermediate cannot produce a trusted certificate for an arbitrary public domain.

---

# Part IV — Lifecycle Management

## 7. Issuance: From Key Pair to Certificate

Issuance is the process that converts "I generated a key pair" into "a CA has signed a statement binding this key to my identity." The subject, **not the CA**, generates the key pair — the private key must never leave the subject's control, or the entire non-repudiation property of the system collapses.

```
┌────────────┐     1. Generate keypair      ┌────────────┐
│   Subject  │ ───────────────────────────▶ │  (local)   │
└─────┬──────┘                               └────────────┘
      │ 2. Build CSR (public key + identity claim),
      │    self-sign with own private key (proof of possession)
      ▼
┌────────────┐     3. Submit CSR            ┌────────────┐
│    RA      │ ◀──────────────────────────  │   CA/RA    │
└─────┬──────┘                              endpoint
      │ 4. Vet identity (domain control,
      │    org documents, in-person, etc.)
      ▼
┌────────────┐     5. Issue + sign cert      ┌────────────┐
│     CA     │ ───────────────────────────▶  │  Subject   │
└────────────┘                               └────────────┘
```

A Certificate Signing Request (CSR) is itself a small signed structure (PKCS#10):

```bash
# Generate a private key (never transmitted)
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out server.key

# Build a CSR: embeds the public key + identity, self-signed
# to PROVE possession of the corresponding private key
openssl req -new -key server.key -out server.csr \
  -subj "/CN=www.example.com" \
  -addext "subjectAltName=DNS:www.example.com,DNS:example.com"
```

The self-signature on the CSR is **proof of possession**: it demonstrates the requester actually holds the private key matching the public key being submitted, preventing an attacker from requesting a certificate for a public key they do not control.

> **Principle 7.** *The CA certifies a binding it did not create and a key it never possessed.* This is why CA compromise threatens identity-binding (the CA can lie about who holds a key) but not confidentiality of any specific subject's traffic (the CA never had the private key to begin with) — an important distinction when reasoning about Chapter 16's compromise scenarios.

---

## 8. Revocation: CRL and OCSP

A certificate's `Validity` field states when trust *expires by default*. But identity bindings can become invalid before that date — the private key is stolen, the organization changes hands, the domain is sold. Validity alone is not enough; PKI needs a mechanism to invalidate trust **early**.

| Mechanism | Model | Trade-off |
|---|---|---|
| **CRL** (Certificate Revocation List) | CA periodically publishes a signed list of all revoked serial numbers | Simple, cacheable, but grows large and is not real-time (published on an interval) |
| **OCSP** (Online Certificate Status Protocol) | Relying party queries a responder for one specific certificate's status | Real-time, smaller responses, but requires a live query (latency, privacy leak, availability dependency) |
| **OCSP Stapling** | Server pre-fetches its own OCSP response and presents it during the handshake | Removes the relying party's live-query dependency while keeping freshness |
| **Short-lived certificates** | Issue certificates valid for hours/days instead of months, skip revocation entirely | Architecturally elegant (Principle 9) but requires automated reissuance |

```
                    ┌──────────────────────┐
                    │  Relying Party has    │
                    │  end-entity cert      │
                    └──────────┬────────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
    ┌───────────────────┐            ┌───────────────────┐
    │  Fetch CRL (CDP)    │            │  Query OCSP (AIA)  │
    │  check serial# in   │            │  responder for     │
    │  revoked list       │            │  this one serial#  │
    └─────────┬───────────┘            └─────────┬──────────┘
              │                                  │
              ▼                                  ▼
       Revoked? → REJECT                 "good"/"revoked"/
       Not found → ACCEPT                "unknown" → decide
```

> **Principle 8.** *Revocation exists because validity periods are a static, advance promise, while compromise is a dynamic, unpredictable event — the two failure timescales cannot be unified into one mechanism.* OCSP and CRLs are the two ways to bridge that gap: poll a list, or ask a live oracle. Both carry costs (Chapter 16 covers what happens when the bridge itself fails, e.g., an unreachable OCSP responder — "soft-fail" vs. "hard-fail" policies).

---

## 9. Renewal, Rekeying, and Validity Periods

Renewal replaces an expiring certificate; **rekeying** additionally generates a new key pair (rather than reusing the old one in a new certificate). The industry trend (driven by CA/Browser Forum policy) is toward progressively shorter maximum validity periods for public TLS certificates (historically 5 years → 1 year → 398 days → industry direction toward ~47 days by 2029 per published CA/B Forum ballots).

> **Principle 9.** *Shortening validity periods is a deliberate substitution of revocation infrastructure with expiration infrastructure.* A certificate that lives for 47 days needs no revocation check at all in many threat models — it will expire before most compromise-to-detection windows close. This only works if **reissuance is fully automated** (see ACME, Chapter 13); manual renewal at that frequency is operationally infeasible. Shorter lifetimes are therefore not just "more secure" in isolation — they are a system-level trade that *requires* automation to be viable, which is why their adoption tracks the maturity of automated enrollment protocols.

---

# Part V — Operational Architecture

## 10. CA Hierarchy Design

Designing a hierarchy means deciding how many tiers exist and what each tier is permitted to do, directly applying Principles 2 and 5.

```
Tier 0 — Root CA
  • Air-gapped or offline storage
  • Private key used only to sign Tier-1 intermediates and periodic CRLs
  • Validity: very long (e.g., 20 years)

Tier 1 — Policy/Issuing Intermediate CA(s)
  • Online, network-accessible to issuance systems
  • One per business unit, environment, or policy domain (e.g., "internal devices" vs "public TLS")
  • Validity: medium (e.g., 5-10 years)
  • Frequently constrained via Name Constraints (Ch.6)

Tier 2 — End-entity certificates
  • Issued automatically at scale
  • Validity: short (Principle 9)
```

```
                          ┌───────────────────────┐
                          │   Tier 0: Root CA       │
                          │       (offline)          │
                          └────┬──────┬──────┬───────┘
                               │      │      │
                  ┌────────────┘      │      └────────────┐
                  ▼                   ▼                   ▼
       ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
       │ Tier 1: Public TLS │ │ Tier 1: Internal   │ │ Tier 1: Code      │
       │ Issuing CA          │ │ Device Issuing CA  │ │ Signing Issuing CA│
       └─────────┬──────────┘ └─────────┬──────────┘ └─────────┬──────────┘
                 ▼                       ▼                       ▼
       ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
       │ Tier 2:            │ │ Tier 2:            │ │ Tier 2:            │
       │ example.com         │ │ device-0451         │ │ release-builds      │
       └──────────────────┘ └──────────────────┘ └──────────────────┘
```

Splitting intermediates by **purpose** (public TLS vs internal devices vs code signing) means a policy violation or compromise in one issuing CA is contained to its `pathLenConstraint`/`Name Constraints` boundary and does not force revocation of unrelated certificate populations.

> **Principle 10.** *Hierarchy depth and width are a direct trade between operational convenience and blast-radius containment.* A flatter hierarchy (fewer intermediates) is operationally simpler but concentrates risk; a deeper, purpose-segmented hierarchy isolates risk but multiplies the number of keys, ceremonies, and trust relationships that must be separately managed (see Chapter 15).

---

## 11. Key Protection and HSMs

A CA's authority *is* its private key. Anyone holding it can mint statements the entire trust ecosystem will believe. Protecting it is therefore not "good practice" — it is the single control on which everything above depends.

A **Hardware Security Module (HSM)** is a tamper-resistant device that generates and stores private keys such that the raw key material **never exists outside the device**, even to its own operators. Signing operations are requested of the HSM; the key itself is never extracted.

```
┌───────────────────────────────────────┐
│              HSM (FIPS 140-2/3)        │
│  ┌─────────────────────────────────┐  │
│  │  CA Private Key (non-extractable)│  │
│  └─────────────────────────────────┘  │
│                                         │
│  Input: "sign this data" ──────────┐   │
│  Output: signature ◀────────────────┘   │
│  (tamper detection → key self-destructs)│
└───────────────────────────────────────┘
```

Minimal annotated example using a software-emulated PKCS#11 interface (illustrating the *interface pattern*, not a production HSM setup):

```bash
# List key objects available inside the HSM/token —
# note: no command ever exports the raw private key
pkcs11-tool --module /usr/lib/softhsm/libsofthsm2.so --list-objects

# Sign data using a key that physically never leaves the module
pkcs11-tool --module /usr/lib/softhsm/libsofthsm2.so \
  --sign --id 01 --mechanism SHA256-RSA-PKCS \
  --input-file tbs_certificate.der --output-file signature.bin
```

> **Principle 11.** *Confidentiality of the CA's private key is not improved by good intentions or process documents — it is enforced by physical and cryptographic non-extractability.* Root keys, in particular, are frequently split using **threshold schemes (m-of-n Shamir's Secret Sharing)** so that no single custodian can independently authorize a signing operation, directly extending Principle 2's role-separation to individual human operators.

---

## 12. Repository and Distribution

A signed certificate is useless if relying parties cannot obtain the issuer's certificate or revocation data. PKI solves discovery declaratively: certificates embed **pointers to where to fetch what's missing**, rather than relying parties needing prior knowledge.

| Extension | Points to | Used for |
|---|---|---|
| `Authority Information Access (AIA)` | Issuing CA's own certificate (URL) | Chain building when intermediate isn't already held |
| `CRL Distribution Points (CDP)` | CRL file location | Revocation checking via CRL |
| `AIA — OCSP` | OCSP responder URL | Revocation checking via OCSP |

```
┌────────────────────┐
│  End-entity cert    │
│  AIA: issuer.example/intermediate.crt │
│  CDP: issuer.example/intermediate.crl │
└──────────┬──────────┘
           │ relying party fetches as needed
           ▼
┌────────────────────┐       ┌────────────────────┐
│ Intermediate cert   │──────▶│ Repository (HTTP/   │
│ (if not cached)     │       │ LDAP server)        │
└────────────────────┘       └────────────────────┘
```

> **Principle 12.** *Trust artifacts must be self-describing about their own distribution, because PKI cannot assume any out-of-band channel exists between an arbitrary relying party and an arbitrary CA except the certificate itself.* This is why AIA/CDP exist instead of requiring relying parties to maintain a manual directory of every CA's URLs.

---

# Part VI — Protocols and Path Validation

## 13. Enrollment Protocols

Issuance (Chapter 7) described the *logical* flow; enrollment protocols are the concrete wire formats that automate it. Each emerged to solve a specific gap.

| Protocol | Designed For | Key Mechanism |
|---|---|---|
| **PKCS#10 / manual CSR** | Any environment, manual issuance | Subject submits a self-signed CSR; CA issues out-of-band |
| **SCEP** (Simple Certificate Enrollment Protocol) | Network devices, legacy MDM | Shared secret or challenge password; limited security but ubiquitous in routers/firewalls |
| **EST** (Enrollment over Secure Transport) | Modern replacement for SCEP | TLS-based, supports renewal, stronger crypto-agility |
| **CMP** (Certificate Management Protocol) | Enterprise/government PKI | Rich protocol: full lifecycle (init, revoke, key update), supports proof-of-possession formally |
| **ACME** (Automatic Certificate Management Environment) | Public web TLS at scale (Let's Encrypt and successors) | Domain control validation (HTTP-01, DNS-01, TLS-ALPN-01) fully automated, no human RA |

```
  Subject (web server)                          ACME CA
         │                                          │
         │  1. Request certificate for example.com   │
         │ ───────────────────────────────────────▶  │
         │                                          │
         │  2. Challenge: prove control of           │
         │     example.com                           │
         │ ◀───────────────────────────────────────  │
         │                                          │
         │  3. Serve token at                        │
         │     /.well-known/acme-challenge/          │
         │  (subject sets this up locally)           │
         │                                          │
         │  4. Fetch challenge token over HTTP        │
         │ ◀───────────────────────────────────────  │
         │ ───────────────────────────────────────▶  │
         │                                          │  5. Validate match
         │                                          │
         │  6. Issue certificate (no human review)   │
         │ ◀───────────────────────────────────────  │
         │                                          │
```

> **Principle 13.** *Domain-validated issuance at Internet scale is only possible because the RA role (Chapter 2's identity vetting) was redefined from "human reviews documents" to "machine proves control of a resource."* ACME did not weaken identity assurance arbitrarily — it substituted a different, automatable assurance basis (control of DNS/HTTP for the domain) appropriate to the threat model of "is this really the server operating this domain," which is what TLS server certificates need.

---

## 14. Certification Path Validation

Path validation (RFC 5280 §6) is the formal algorithm a relying party runs to decide whether to trust a presented chain. It is more than "check each signature" — it enforces every constraint from Chapter 6 cumulatively across the whole chain.

```
For each certificate in the chain, from root → leaf:
┌─────────────────────────────────────────────────────┐
│ 1. Signature verifies using the issuer's public key   │
│ 2. Current date within [notBefore, notAfter]          │
│ 3. Certificate is not revoked (Ch.8)                  │
│ 4. Issuer's Basic Constraints permit issuing this type│
│    (CA:TRUE, pathLenConstraint not exceeded)          │
│ 5. Name Constraints from any ancestor are respected   │
│ 6. Key Usage of issuer permits certificate signing    │
│ 7. Policy OIDs are consistent with required policy    │
└─────────────────────────────────────────────────────┘
   ALL checks pass at EVERY level → chain is valid
   ANY check fails at ANY level → chain is REJECTED
```

> **Principle 14.** *Trust in a chain is the logical AND of every constraint at every link — not just the bottom signature.* A perfectly valid signature on an expired certificate is worthless; a valid, unexpired certificate issued outside its issuer's `Name Constraints` is worthless. This is the formal generalization of Principle 6: constraints are meaningless unless validation enforces all of them, every time, with no shortcuts.

---

# Part VII — Production Operations

## 15. Deployment Patterns and Key Ceremonies

A **root key ceremony** is the formal, scripted, witnessed, recorded event in which a root CA's key pair is generated (or used) inside an HSM, under multi-party control, specifically to produce an auditable record that no single individual ever had unilateral access to the key.

```
┌─────────────────────────────────────────────────────┐
│  Key Ceremony (typical structure)                     │
│  - Independent auditor present                        │
│  - Script followed verbatim, deviations logged         │
│  - Multiple custodians, each holding one share of a   │
│    threshold scheme (Principle 11)                     │
│  - HSM generates key inside tamper-evident boundary     │
│  - Root CA certificate self-signed inside the ceremony  │
│  - HSM + key shares sealed into physical safes after    │
└─────────────────────────────────────────────────────┘
```

Day-to-day, the **offline root / online intermediate** split (Chapter 10) means the root is only brought online for scripted, audited events — typically: issuing a new intermediate, re-signing a CRL near its scheduled expiry, or disaster recovery.

> **Principle 15.** *A key ceremony exists to convert "trust me" into "verify the process," because the root anchor (Principle 5) cannot be cryptographically proven trustworthy — its trustworthiness is procedural, and procedures only have evidentiary value if witnessed and recorded.*

---

## 16. Compromise Response and Failure Modes

| Failure | Detection | Containment |
|---|---|---|
| End-entity private key stolen | Owner reports, anomaly detection | Revoke that one certificate (CRL/OCSP) |
| Intermediate CA key compromised | Audit, intrusion detection, external report | Revoke the intermediate cert; **all certs it issued become untrusted** |
| Root CA key compromised | Same, but catastrophic | Remove root from all trust stores globally; **every certificate in the hierarchy is untrusted** |
| OCSP responder unreachable | Network/availability monitoring | Policy decision: **soft-fail** (treat as valid, availability-favoring) vs **hard-fail** (treat as invalid, security-favoring) |
| Mis-issuance (CA issues wrongly) | CT log monitoring (Ch.17), domain owner report | Revoke; CA may face removal from trust programs (root program policy enforcement) |

```
                    ┌─────────────────────────┐
                    │   Compromise detected     │
                    └────────────┬──────────────┘
                                 │
                     Which layer was compromised?
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
┌───────────────┐      ┌───────────────────┐      ┌───────────────────┐
│ End-entity key  │      │ Intermediate CA key │      │ Root CA key         │
└───────┬───────┘      └─────────┬───────────┘      └─────────┬───────────┘
        ▼                        ▼                            ▼
┌───────────────┐      ┌───────────────────┐      ┌───────────────────┐
│ Revoke single   │      │ Revoke intermediate │      │ Remove from all      │
│ certificate      │      │ cert.                │      │ trust stores          │
│                   │      │ Blast radius: ALL    │      │ Blast radius: ENTIRE  │
│ Blast radius: 1   │      │ certs it issued      │      │ hierarchy             │
└───────────────┘      └───────────────────┘      └───────────────────┘
```

> **Principle 16.** *Blast radius is the organizing variable of PKI architecture, and every chapter in this guide is, in retrospect, a control on blast radius:* hierarchy depth (Ch.10) bounds it structurally, name constraints (Ch.6) bound it by namespace, short validity (Ch.9) bounds it temporally, and HSMs (Ch.11) bound the *probability* of the triggering event in the first place.

**Soft-fail vs. hard-fail** deserves explicit attention: if a relying party cannot reach the OCSP responder, hard-fail rejects the connection (favoring security, but turning an availability problem into an outage), while soft-fail proceeds as if valid (favoring availability, but allowing an attacker who can block network access to the OCSP responder to also suppress revocation checks). Most production browser policies, after extensive empirical debate, default toward soft-fail for OCSP but rely on **OCSP stapling** and **short validity periods** to reduce the resulting risk window — a direct, practical instance of Principle 9's trade-off.

---

## 17. Monitoring, Transparency, and Audit

**Certificate Transparency (CT)** addresses a blind spot left by everything above: path validation (Ch.14) verifies a chain is *internally* consistent, but says nothing about whether the *issuance itself* was legitimate. A compromised or coerced CA could issue a perfectly well-formed, validly-chained certificate for a domain it had no authority to certify.

CT requires CAs to publish every issued certificate to public, append-only, cryptographically verifiable logs *before* it is considered trusted by major relying parties (browsers require an embedded "SCT" — Signed Certificate Timestamp — proving log inclusion).

```
┌────────────┐   submits cert  ┌────────────────┐
│     CA      │───────────────▶│   CT Log        │
└────────────┘                 │  (append-only,  │
                                │   Merkle tree)  │
                                └────────┬────────┘
                                         │ returns SCT
                                         ▼
                                ┌────────────────┐
                                │ CA embeds SCT   │
                                │ in certificate  │
                                └────────────────┘
       Domain owners can MONITOR logs for
       any certificate issued for their domain —
       even by a CA they never authorized
```

> **Principle 17.** *Path validation proves a certificate is internally consistent; transparency proves the issuance event itself is publicly accountable.* These are different trust questions, and PKI needed a separate mechanism (CT) because no extension inside the certificate itself can prove anything about the circumstances of its own creation — that evidence has to live externally, in a log the certificate's own issuer cannot unilaterally edit.

Independent audits (e.g., **WebTrust for CAs**, **ETSI EN 319 411**) operate at a longer time scale, verifying that a CA's actual operational practices match its published **Certificate Policy (CP)** and **Certification Practice Statement (CPS)** — the formal documents referenced by the `Certificate Policies` extension (Chapter 6). Continuous CT monitoring catches individual mis-issuance events quickly; periodic audits catch systemic process failures that CT alone would not reveal.

---

# Appendices

## Appendix A — X.509 Fields to Memorize

| Field | One-line meaning |
|---|---|
| `Issuer` | Who signed/vouches for this certificate |
| `Subject` | Who/what this certificate identifies |
| `Subject Public Key Info` | The public key being certified |
| `Validity (notBefore/notAfter)` | Window of default trust |
| `Basic Constraints (CA:TRUE/FALSE)` | Can this cert issue other certs? |
| `Key Usage` | Permitted cryptographic operations |
| `Extended Key Usage` | Permitted application purposes |
| `Subject Alternative Name` | All valid identities (modern relying parties use this, not CN) |
| `Authority Information Access` | Where to fetch the issuer's cert / OCSP responder |
| `CRL Distribution Points` | Where to fetch the revocation list |
| `Signature Value` | The CA's cryptographic vouching, over everything else |

## Appendix B — Glossary

- **CA (Certificate Authority)** — entity that signs certificates, asserting key-to-identity bindings.
- **RA (Registration Authority)** — entity that vets identity before a CA issues.
- **VA (Validation Authority)** — entity (typically an OCSP responder) that answers real-time validity queries.
- **CSR (Certificate Signing Request)** — a subject's self-signed request for certification (PKCS#10).
- **CRL (Certificate Revocation List)** — periodically published, signed list of revoked certificate serial numbers.
- **OCSP (Online Certificate Status Protocol)** — real-time, per-certificate revocation query protocol.
- **HSM (Hardware Security Module)** — tamper-resistant hardware that generates/stores private keys without exposing raw key material.
- **CT (Certificate Transparency)** — public, append-only logging of issued certificates for accountability.
- **CP/CPS (Certificate Policy / Certification Practice Statement)** — formal documents describing a CA's issuance and operational practices.
- **Path Validation** — the algorithm (RFC 5280) that verifies an entire certificate chain against all applicable constraints.
- **Name Constraints** — extension restricting the namespace a subordinate CA may issue into.
- **Key Ceremony** — formal, witnessed, scripted procedure for generating or operating a root CA key.

## Appendix C — Protocol and Algorithm Comparison Tables

**Revocation mechanisms**

| Mechanism | Latency | Bandwidth | Privacy | Availability dependency |
|---|---|---|---|---|
| CRL | Periodic (hours-days) | High (full list) | Good (no per-query leak) | Low (cacheable) |
| OCSP | Real-time | Low (per-cert) | Weak (responder sees queries) | High (live query) |
| OCSP Stapling | Real-time, server-fetched | Low | Good | Low (server pre-fetches) |
| Short-lived certs | N/A (expiration replaces revocation) | None | Good | None |

**Enrollment protocols**

| Protocol | Automation | Typical Use | Proof of Possession |
|---|---|---|---|
| Manual CSR | None | One-off, manual review | Self-signature on CSR |
| SCEP | Partial | Legacy network devices | Shared secret |
| EST | High | Modern device enrollment | TLS client cert or shared secret |
| CMP | High | Enterprise/government PKI | Formal, multiple proof types |
| ACME | Full | Public web TLS | Domain control challenge |

## Appendix D — Learning Path

| Stage | You should be able to... | Reference |
|---|---|---|
| **Orientation** | Explain why a public key alone cannot establish identity | Part I |
| **Competent** | Read any X.509 certificate and chain, and explain every field | Parts II–III |
| **Operational** | Design a CA hierarchy and revocation strategy for a real system | Parts IV–V |
| **Advanced** | Choose and justify an enrollment protocol for a given environment | Part VI |
| **Expert** | Reason about blast radius, run/audit a key ceremony, respond to compromise | Part VII |

---

## References (Upstream)

- RFC 5280 — *Internet X.509 Public Key Infrastructure Certificate and CRL Profile*
- RFC 6960 — *X.509 Internet PKI Online Certificate Status Protocol (OCSP)*
- RFC 8555 — *Automatic Certificate Management Environment (ACME)*
- RFC 7030 — *Enrollment over Secure Transport (EST)*
- RFC 4210 — *Certificate Management Protocol (CMPv2)*
- CA/Browser Forum — *Baseline Requirements for the Issuance and Management of Publicly-Trusted Certificates*
- Certificate Transparency — RFC 9162

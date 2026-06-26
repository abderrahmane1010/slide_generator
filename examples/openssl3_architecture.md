# OpenSSL 3.x — Deep Architectural Reference

> **Scope:** Mental-model reference for engineers who already know TLS/PKI.  
> No step-by-step tutorials. Dense. Precise.  
> Version target: OpenSSL 3.0 – 3.x (API/ABI stable series).

---

## Table of Contents

1. [Library Split: libcrypto vs libssl](#1-library-split-libcrypto-vs-libssl)
2. [The Provider Model](#2-the-provider-model)
3. [The EVP Abstraction Layer](#3-the-evp-abstraction-layer)
4. [ENGINE vs PROVIDER — The Architectural Shift](#4-engine-vs-provider--the-architectural-shift)
5. [X.509 and the Certificate Stack](#5-x509-and-the-certificate-stack)
6. [Encoding Layer: PEM / DER / PKCS](#6-encoding-layer-pem--der--pkcs)
7. [openssl.cnf — Configuration as Architecture](#7-opensslcnf--configuration-as-architecture)
8. [Key Internal Subsystems](#8-key-internal-subsystems)
9. [Command Cheatsheet](#9-command-cheatsheet)

---

## 1. Library Split: libcrypto vs libssl

OpenSSL ships two distinct shared libraries. Their boundary is intentional and load-bearing.

```
┌──────────────────────────────────────────────────────┐
│                     libssl.so                        │
│  TLS/DTLS protocol state machines                    │
│  Handshake logic (ClientHello, ServerHello, …)       │
│  Session & ticket management                         │
│  Record layer (fragmentation, MAC, encryption)       │
│  Certificate verification callbacks                  │
│  SSL_CTX / SSL / BIO wiring                          │
│                                                      │
│  ← calls down into libcrypto for ALL crypto ops →    │
└──────────────────┬───────────────────────────────────┘
                   │  EVP API calls only
                   ▼
┌──────────────────────────────────────────────────────┐
│                   libcrypto.so                       │
│  EVP layer (algorithm-agnostic API)                  │
│  Provider framework (algorithm dispatch)             │
│  X.509 / ASN.1 / PEM / DER stack                    │
│  BIO abstraction (I/O)                               │
│  BN (big number), EC, RSA, DSA, DH primitives        │
│  RAND subsystem                                      │
│  STORE (OSSL_STORE) — credential loading             │
│  PKCS#7, PKCS#12, PKCS#8 codec                      │
│  CMS (RFC 5652)                                      │
└──────────────────────────────────────────────────────┘
```

**Key invariants:**

- `libssl` has **zero** direct algorithm implementations. Every cipher, hash, and asymmetric op goes through the EVP dispatch table inside `libcrypto`.
- `libcrypto` is fully usable without `libssl` (TLS is optional; crypto is the core product).
- An application linking only against `libcrypto` pays zero cost for the TLS state machine.
- The split means FIPS boundary enforcement happens entirely inside `libcrypto` — `libssl` is transparent to it.

---

## 2. The Provider Model

### 2.1 What a Provider Is

A provider is a **dynamically-loadable module** (shared object / DLL) that registers algorithm implementations into a `OSSL_LIB_CTX`. It is the unit of algorithm supply in OpenSSL 3.x.

Providers replaced the old ENGINE mechanism (see §4). The conceptual model:

```
OSSL_LIB_CTX (library context)
  └─ provider registry
       ├─ "default"   → libcrypto built-in algorithms (AES, RSA, SHA, …)
       ├─ "legacy"    → old/weak algorithms (MD4, RC4, Blowfish, DES, …)
       ├─ "fips"      → FIPS 140-3 validated module (separate .so)
       ├─ "base"      → encoding/decoding only, no crypto
       └─ "null"      → no algorithms at all (used for testing isolation)
```

Each provider exposes a single entry point: `OSSL_provider_init()`. Through this function it hands OpenSSL a dispatch table of `OSSL_DISPATCH` arrays — one per algorithm type.

### 2.2 Provider Dispatch Internals

```
Provider .so
  └─ OSSL_provider_init()
       └─ returns OSSL_ALGORITHM[] tables, one per operation type:
            OSSL_OP_DIGEST        → { "SHA2-256", dispatch[] }
            OSSL_OP_CIPHER        → { "AES-256-GCM", dispatch[] }
            OSSL_OP_ASYM_CIPHER   → { "RSA", dispatch[] }
            OSSL_OP_SIGNATURE     → { "ECDSA", dispatch[] }
            OSSL_OP_KEM           → { "RSASVE", dispatch[] }
            OSSL_OP_KDF           → { "HKDF", dispatch[] }
            OSSL_OP_RAND          → { "CTR-DRBG", dispatch[] }
            OSSL_OP_ENCODER       → { "RSA/PEM", dispatch[] }
            OSSL_OP_DECODER       → { "DER/RSA", dispatch[] }
            OSSL_OP_STORE         → { "file", dispatch[] }
            …
```

Each `dispatch[]` is a `{function_id, function_ptr}` array. The function IDs are stable ABI contracts defined in `<openssl/core_dispatch.h>`.

### 2.3 The Four Built-in Providers

| Provider | `.so` | Default loaded? | Purpose |
|---|---|---|---|
| `default` | built into `libcrypto` | **Yes** | All mainstream algorithms |
| `legacy` | `legacy.so` | No — opt-in | MD2, MD4, MDC2, RC2, RC4, RC5, IDEA, DES, Blowfish, CAST5 |
| `fips` | `fips.so` | No — explicit | FIPS 140-3 validated implementations; installs a separate HMAC self-check |
| `base` | built into `libcrypto` | Yes (alongside default) | Encoder/decoder for key formats; no algorithm implementations |
| `null` | built into `libcrypto` | No | Zero algorithms; used to construct isolated contexts |

**`legacy` loading pitfall:** If you call `EVP_get_digestbyname("MD4")` without loading the `legacy` provider, you get `NULL`. The error is a fetch failure, not an "algorithm unsupported" error. This confuses many callers who expect the 1.x behavior where all algorithms were always present.

### 2.4 FIPS Provider Architecture

The FIPS provider is architecturally distinct from the others:

```
┌─────────────────────────────────────────────────────────┐
│  fips.so  (FIPS 140-3 module boundary)                  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Integrity check (HMAC-SHA256 over fips.so)     │    │
│  │  Power-On Self Tests (POST) — KATs per alg.     │    │
│  │  Continuous tests (DRBG health, pairwise key)   │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  Algorithm implementations (separate from default)      │
│  No dependency on libcrypto's non-FIPS internals        │
└─────────────────────────────────────────────────────────┘
         ▲
         │ loaded by OSSL_PROVIDER_load()
         │
   libcrypto (the "module boundary wrapper")
```

FIPS requires a `fips.cnf` or `fips` section in `openssl.cnf` specifying the module path and HMAC value. The module verifies its own integrity at load time; if the HMAC mismatches, loading aborts.

When FIPS is active, calling `EVP_MD_fetch(ctx, "MD5", NULL)` returns `NULL` — MD5 is not in the FIPS provider's dispatch table. This is enforcement, not configuration.

### 2.5 Third-Party Providers: PKCS#11 Example

PKCS#11 hardware tokens (HSMs, smart cards) integrate via a third-party provider like `pkcs11-provider` (or `libp11` for the legacy ENGINE path).

```
Application
  │  EVP_PKEY_sign(ctx, …)
  ▼
libcrypto EVP dispatch
  │  fetches "RSA" from PKCS11 provider
  ▼
pkcs11-provider.so
  │  translates OSSL_DISPATCH calls → PKCS#11 C_Sign() / C_Decrypt()
  ▼
PKCS#11 middleware (.so)
  │
  ▼
HSM / Smart card (private key never leaves hardware)
```

The critical design benefit: the application uses the same `EVP_PKEY_sign()` call regardless of whether the key lives in software or hardware. The provider boundary absorbs the difference.

### 2.6 Algorithm Fetching

Algorithm fetching is the mechanism by which EVP resolves a name to a provider implementation at runtime.

```c
// Explicit fetch — returns EVP_MD*, caller owns it
EVP_MD *md = EVP_MD_fetch(libctx, "SHA2-256", "provider=fips");

// Implicit fetch — goes through internal cache, no ownership
const EVP_MD *md = EVP_sha256();  // ← legacy-style, still works
```

Fetch properties form a query language:
- `"provider=fips"` — require FIPS provider
- `"provider!=legacy"` — exclude legacy
- `"fips=yes"` — any provider advertising FIPS compliance
- `""` / `NULL` — first match wins, default provider preferred

**Fetch cache:** Results are cached per `OSSL_LIB_CTX`. The cache is invalidated when a provider is loaded/unloaded. Multi-threaded fetch is safe; the cache uses internal locks.

---

## 3. The EVP Abstraction Layer

### 3.1 Conceptual Role

EVP (Envelope) is the **algorithm-neutral API**. It exists to insulate callers from algorithm implementations. In OpenSSL 1.x this was primarily about API uniformity; in 3.x it also became the provider dispatch boundary.

```
Application code
      │
      │  EVP_DigestInit_ex2()
      │  EVP_EncryptUpdate()
      │  EVP_PKEY_sign()
      ▼
┌─────────────────────────────────────────────────────┐
│                   EVP Layer                         │
│  - Algorithm name resolution                        │
│  - Provider fetch & dispatch                        │
│  - Context lifecycle management (EVP_MD_CTX, etc.)  │
│  - Parameter passing (OSSL_PARAM arrays)            │
│  - Unified key abstraction (EVP_PKEY)               │
└────────────────────────┬────────────────────────────┘
                         │  dispatch via function pointers
              ┌──────────┼───────────┐
              ▼          ▼           ▼
       default.so    fips.so    pkcs11.so
       (SHA-256)    (SHA-256)   (sign ops)
```

### 3.2 Context Types and Their Roles

| Context type | Scope |
|---|---|
| `EVP_MD_CTX` | Digest operation in-flight state |
| `EVP_CIPHER_CTX` | Symmetric cipher in-flight state |
| `EVP_PKEY_CTX` | Asymmetric key operation context |
| `EVP_MAC_CTX` | MAC operation (HMAC, CMAC, KMAC) |
| `EVP_KDF_CTX` | KDF operation (HKDF, PBKDF2, …) |
| `EVP_PKEY` | Abstract key object (opaque; provider-owned data) |

**`EVP_PKEY` internals:** In 3.x, `EVP_PKEY` is a reference-counted shell. The actual key material lives inside the provider as an opaque pointer (`keydata`). The EVP layer calls back into the provider via `OSSL_FUNC_keymgmt_*` dispatch entries to copy, compare, export, or import key data.

This means you **cannot** directly cast `EVP_PKEY` to `RSA*` anymore (the `EVP_PKEY_get0_RSA()` path is deprecated and returns a compatibility shim, not the real internal struct).

### 3.3 OSSL_PARAM: The Parameter Bus

Providers and the EVP layer communicate algorithm-specific parameters through `OSSL_PARAM` arrays — a typed key-value structure:

```c
OSSL_PARAM params[] = {
    OSSL_PARAM_uint(OSSL_CIPHER_PARAM_IVLEN, &ivlen),
    OSSL_PARAM_octet_string(OSSL_CIPHER_PARAM_IV, iv, sizeof(iv)),
    OSSL_PARAM_END
};
EVP_CIPHER_CTX_get_params(ctx, params);
```

This replaces the old `EVP_CIPHER_CTX_ctrl()` / `EVP_MD_CTX_ctrl()` integer-dispatch mechanism. The OSSL_PARAM system is type-safe, extensible, and provider-agnostic — a provider can advertise custom parameters not known to the EVP layer.

### 3.4 Digest API Flow (annotated)

```
EVP_MD_CTX_new()
  └─ allocates EVP_MD_CTX on heap

EVP_DigestInit_ex2(ctx, NULL, libctx, "SHA2-256", "fips=yes")
  ├─ EVP_MD_fetch(libctx, "SHA2-256", "fips=yes")   ← fetch + cache
  ├─ calls provider's OSSL_FUNC_digest_newctx()      ← allocates provider ctx
  └─ calls provider's OSSL_FUNC_digest_init()

EVP_DigestUpdate(ctx, data, len)
  └─ calls provider's OSSL_FUNC_digest_update()

EVP_DigestFinal_ex(ctx, md, &mdlen)
  └─ calls provider's OSSL_FUNC_digest_final()

EVP_MD_CTX_free(ctx)
  └─ calls provider's OSSL_FUNC_digest_freectx()
  └─ calls EVP_MD_free() if ctx owned the EVP_MD fetch
```

All provider calls happen through stable function-pointer tables, never through direct symbol references. This is what allows `fips.so` to be replaced without recompiling `libcrypto`.

---

## 4. ENGINE vs PROVIDER — The Architectural Shift

### 4.1 The ENGINE Model (OpenSSL 1.x)

ENGINE was the 1.x extension mechanism for hardware offload and custom crypto. It worked through a global singleton registry of named engines, each implementing a fixed set of algorithm-specific function pointers.

```
ENGINE_load_builtin_engines();
ENGINE *e = ENGINE_by_id("pkcs11");
ENGINE_init(e);
ENGINE_set_default_RSA(e);      // global mutation
ENGINE_set_default_ECDSA(e);    // global mutation
```

**Structural problems with ENGINE:**

| Problem | Detail |
|---|---|
| Global state | `ENGINE_set_default_*()` mutates global tables — not thread-safe by design |
| Fixed algorithm set | ENGINE had slots for RSA, DSA, DH, RAND, ciphers, digests — new algorithm types required ABI changes |
| No isolation | One ENGINE replacing RSA affected all code in the process |
| No FIPS boundary | ENGINE had no integrity-check mechanism; FIPS modules couldn't guarantee isolation |
| Implicit initialization | `ENGINE_load_builtin_engines()` loaded everything; no selective fetch |
| No property queries | No way to express "prefer hardware for RSA but not AES" |

### 4.2 The PROVIDER Model (OpenSSL 3.x)

```
                 ENGINE (1.x)          PROVIDER (3.x)
─────────────────────────────────────────────────────────
Registration     Global singleton       Per OSSL_LIB_CTX
Algorithm slots  Fixed, ABI-coupled     Dynamic OSSL_DISPATCH[]
Thread safety    No                     Yes (per-ctx)
Isolation        None                   Full (separate libctx)
FIPS support     External kludge        First-class, integrity-checked
Property system  None                   Rich query language
Key material     Exposed via structs    Opaque, provider-owned
New alg types    Requires ABI bump      Define new OSSL_OP_* constant
```

### 4.3 Migration and Compatibility

OpenSSL 3.x ships `libcrypto` with ENGINE code **deprecated** but present (compile-time: `OPENSSL_NO_ENGINE` removes it). The compatibility shim works:

```
ENGINE_by_id("pkcs11")          ← still compiles, emits deprecation warning
  → internally wrapped by libcrypto into an OSSL_PROVIDER-like dispatch
  → but: no property queries, no FIPS flag, no libctx isolation
```

The clean migration path:

```
1.x ENGINE path:               3.x PROVIDER path:
  ENGINE_load_dynamic()     →    OSSL_PROVIDER_load(libctx, "pkcs11")
  ENGINE_set_default_RSA()  →    (automatic via fetch properties)
  EVP_PKEY_set1_engine()    →    EVP_PKEY is provider-bound at creation
```

### 4.4 OSSL_LIB_CTX: The Isolation Primitive

`OSSL_LIB_CTX` (library context) is the structure that makes per-process or per-thread algorithm isolation possible. Every provider registry, fetch cache, and configuration is scoped to a `libctx`.

```c
// Two independent crypto universes in one process
OSSL_LIB_CTX *fips_ctx   = OSSL_LIB_CTX_new();
OSSL_LIB_CTX *legacy_ctx = OSSL_LIB_CTX_new();

OSSL_PROVIDER_load(fips_ctx,   "fips");
OSSL_PROVIDER_load(legacy_ctx, "default");
OSSL_PROVIDER_load(legacy_ctx, "legacy");

// FIPS-only digest
EVP_MD *md_fips   = EVP_MD_fetch(fips_ctx,   "SHA2-256", NULL);
// Legacy digest (MD4 only available here)
EVP_MD *md_legacy = EVP_MD_fetch(legacy_ctx, "MD4",      NULL);
```

`OSSL_LIB_CTX_new_from_dispatch()` lets providers create their own child contexts for recursive operations, without polluting the application's context.

---

## 5. X.509 and the Certificate Stack

### 5.1 Internal Representation

`X509` is an ASN.1-decoded in-memory structure. OpenSSL generates it via auto-generated code from ASN.1 module definitions (`crypto/x509/x_x509.c` + `include/openssl/x509.h` macros from the `ASN1_SEQUENCE` macro system).

```
X509
  ├─ X509_CINF  (tbsCertificate)
  │    ├─ version
  │    ├─ serialNumber (ASN1_INTEGER)
  │    ├─ signature (X509_ALGOR)
  │    ├─ issuer (X509_NAME)
  │    ├─ validity (X509_VAL)
  │    ├─ subject (X509_NAME)
  │    ├─ key (X509_PUBKEY → EVP_PKEY)
  │    └─ extensions (STACK_OF(X509_EXTENSION))
  ├─ sig_alg (X509_ALGOR)
  ├─ signature (ASN1_BIT_STRING)
  └─ [cached] ex_data, name_hash, ex_flags (lazily computed)
```

`X509_NAME` stores RDN sequences as `STACK_OF(X509_NAME_ENTRY)`. Each entry holds an `ASN1_OBJECT` (OID) + `ASN1_STRING` (value). The string type matters: `UTF8String`, `PrintableString`, `T61String` — comparison semantics differ (RFC 5280 §7).

### 5.2 Certificate Parsing Pipeline

```
DER bytes (wire / file)
       │
       ▼  d2i_X509()  [or via BIO: d2i_X509_bio()]
       │
  ASN.1 BER/DER decoder (crypto/asn1/tasn_dec.c)
  ├─ type-check tag/length
  ├─ recurse into SEQUENCE, SET, CHOICE
  ├─ allocate X509_CINF, X509_NAME, etc. on heap
  └─ populate EVP_PKEY from SubjectPublicKeyInfo
       │
       ▼
  X509 *  (fully decoded, no signature verified yet)
       │
  X509_verify() or chain build (X509_STORE_CTX_verify())
```

`d2i_X509()` does **not** verify signatures. It is purely a structural decoder. Validation is separate.

### 5.3 Chain Building and Validation

`X509_STORE_CTX` is the per-verification working state. `X509_STORE` is the persistent trust anchor database.

```
X509_STORE  (persistent)
  ├─ trust anchors (X509 objects with X509_TRUST)
  ├─ CRL store (X509_CRL objects)
  ├─ verify callbacks
  └─ flags (X509_V_FLAG_*)

        │  X509_STORE_CTX_new() + _init()
        ▼

X509_STORE_CTX  (per-verification)
  ├─ chain being built (STACK_OF(X509))
  ├─ untrusted intermediates (passed in by caller)
  ├─ current cert being verified
  ├─ error code + depth
  └─ verify_cb (per-verify override)
```

**Chain building algorithm (simplified):**

```
1. Start with leaf cert
2. Find issuer: search untrusted bag → search X509_STORE → search by
   Authority Key Identifier or Issuer DN
3. Repeat until self-signed or trust anchor found
4. Verify each signature up the chain
5. Check validity periods, key usage, extended key usage
6. Check name constraints (if present in intermediates)
7. Check CRL / OCSP status (if X509_V_FLAG_CRL_CHECK set)
8. Call verify_cb at each step — non-zero return overrides error
```

**Common `X509_V_FLAG_*` flags worth knowing:**

| Flag | Effect |
|---|---|
| `X509_V_FLAG_CRL_CHECK` | Require CRL for leaf cert |
| `X509_V_FLAG_CRL_CHECK_ALL` | Require CRL for every cert in chain |
| `X509_V_FLAG_PARTIAL_CHAIN` | Accept if chain ends at a trusted intermediate (not just root) |
| `X509_V_FLAG_NO_CHECK_TIME` | Ignore validity periods (dangerous; testing only) |
| `X509_V_FLAG_TRUSTED_FIRST` | Prefer trust store certs over untrusted (default in 3.x) |
| `X509_V_FLAG_X509_STRICT` | Reject non-RFC-5280-compliant constructs |

### 5.4 OSSL_STORE: The Credential Loading Abstraction

`OSSL_STORE` (formerly `X509_STORE` for keys) is the unified credential-loading layer introduced to abstract away where credentials come from.

```
URI scheme → STORE loader

file:///path/to/cert.pem     → file loader (default provider)
pkcs11:token=mytoken;…       → pkcs11-provider STORE loader
org.openssl.winstore://…     → Windows cert store loader
```

```c
OSSL_STORE_CTX *sctx = OSSL_STORE_open_ex(
    "file:///etc/ssl/certs/ca.pem", libctx, NULL, NULL, NULL, NULL, NULL, NULL);

OSSL_STORE_INFO *info;
while ((info = OSSL_STORE_load(sctx)) != NULL) {
    int type = OSSL_STORE_INFO_get_type(info);
    // OSSL_STORE_INFO_X509, _PKEY, _CRL, _CERT, _PARAMS
}
OSSL_STORE_close(sctx);
```

The file STORE loader internally calls the decoder stack (DER → object) with autodetection of PEM/DER/PKCS#12 format.

---

## 6. Encoding Layer: PEM / DER / PKCS

### 6.1 The Encoding Stack

OpenSSL 3.x unified encoding/decoding through ENCODER and DECODER provider operations. The old `PEM_write_*` / `d2i_*` / `i2d_*` functions remain but now delegate to this stack.

```
High-level API call
  PEM_write_bio_PrivateKey()  ← legacy compat wrapper
  OSSL_ENCODER_to_bio()       ← new API

         ▼
  OSSL_ENCODER_CTX
  ├─ "RSA" → "PEM" encoder chain lookup
  ├─ fetches encoder: OSSL_OP_ENCODER dispatch
  └─ chains: RSA → DER → PEM  (encoder chain)
         ▼
  Provider encoder (default): EVP_PKEY → DER bytes
         ▼
  PEM wrapper: DER bytes → base64 + header/footer
         ▼
  BIO write
```

**Encoder chaining** is the key insight: OpenSSL assembles an encoder pipeline by matching `"from"` and `"to"` properties. If there's no direct RSA→PEM encoder, it finds RSA→DER and DER→PEM and chains them automatically.

### 6.2 DER — The Wire Format

DER (Distinguished Encoding Rules) is a strict subset of BER (Basic Encoding Rules), itself a subset of ASN.1 encoding. DER is the canonical binary format for all cryptographic objects.

```
ASN.1 TLV structure:
  [Tag byte(s)] [Length byte(s)] [Value bytes…]

Tag: class (2 bits) | constructed (1 bit) | tag number (5 bits)
  0x30 = SEQUENCE (constructed, universal 16)
  0x02 = INTEGER
  0x04 = OCTET STRING
  0x06 = OID
  0x03 = BIT STRING

RSA private key (PKCS#1, RFC 3447):
  SEQUENCE {
    INTEGER (version = 0)
    INTEGER (n — modulus)
    INTEGER (e — publicExponent)
    INTEGER (d — privateExponent)
    INTEGER (p), INTEGER (q)
    INTEGER (d mod p-1), INTEGER (d mod q-1)
    INTEGER (q^-1 mod p)
  }
```

DER mandates: definite-length encoding, shortest-form tags and lengths, set elements in canonical order. These constraints make DER signatures bitwise deterministic — critical for PKIX.

### 6.3 PEM — The Transport Encoding

PEM is DER encoded in base64 with RFC 1421-style header/footer lines.

```
-----BEGIN <label>-----
<base64(DER)>
-----END <label>-----
```

**Labels and their DER content:**

| PEM Label | DER structure inside |
|---|---|
| `CERTIFICATE` | RFC 5280 `Certificate` (X.509) |
| `CERTIFICATE REQUEST` | RFC 2986 `CertificationRequest` (PKCS#10) |
| `PRIVATE KEY` | RFC 5958 `OneAsymmetricKey` (PKCS#8 unencrypted) |
| `ENCRYPTED PRIVATE KEY` | RFC 5958 `EncryptedPrivateKeyInfo` (PKCS#8 encrypted) |
| `RSA PRIVATE KEY` | RFC 3447 `RSAPrivateKey` (PKCS#1 — legacy, algorithm-specific) |
| `EC PRIVATE KEY` | RFC 5915 `ECPrivateKey` (SEC1 — legacy, EC-specific) |
| `PUBLIC KEY` | RFC 5480 `SubjectPublicKeyInfo` (algorithm-agnostic) |
| `RSA PUBLIC KEY` | RFC 3447 `RSAPublicKey` (PKCS#1 — legacy) |
| `X509 CRL` | RFC 5280 `CertificateList` |
| `PKCS7` | RFC 2315 `ContentInfo` |
| `CMS` | RFC 5652 `ContentInfo` |

**The `RSA PRIVATE KEY` vs `PRIVATE KEY` distinction matters:** the former is PKCS#1 (algorithm-specific, exposes the raw RSA integers directly), the latter is PKCS#8 (algorithm-agnostic wrapper that wraps any key type in an AlgorithmIdentifier + OctetString). OpenSSL's `genpkey` outputs PKCS#8; the older `genrsa` outputs PKCS#1. Tools that parse only one form will fail on the other.

### 6.4 PKCS Formats Used Internally

**PKCS#8 (`PrivateKeyInfo` / `EncryptedPrivateKeyInfo`)**

```
PrivateKeyInfo ::= SEQUENCE {
  version   INTEGER (0),
  algorithm AlgorithmIdentifier,     ← OID identifies key type
  privateKey OCTET STRING            ← DER of the actual key
}
```

Encryption wraps this in:
```
EncryptedPrivateKeyInfo ::= SEQUENCE {
  encryptionAlgorithm AlgorithmIdentifier,  ← PBES2 + PBKDF2 or legacy PBE
  encryptedData       OCTET STRING
}
```

OpenSSL's default PKCS#8 encryption: `PBES2` with `PBKDF2` (SHA-256, 2048 iterations by default — **increase this**) + `AES-256-CBC`. Configurable via `-iter` and `-scrypt` flags.

**PKCS#12 (PFX)**

```
PFX ::= SEQUENCE {
  version  INTEGER (3),
  authSafe ContentInfo,           ← PKCS#7 Data or EncryptedData
  macData  MacData OPTIONAL       ← HMAC-SHA1/SHA256 over authSafe
}
```

`authSafe` contains a sequence of `SafeBag`s, each holding: a certificate (`certBag`), a key (`pkcs8ShroudedKeyBag` or `keyBag`), or CRLs. Each bag carries attributes: `friendlyName` (UTF-8 alias), `localKeyId` (links cert to key).

Encryption in PKCS#12 has two layers: bag-level encryption (usually `3DES-CBC` or `AES-256-CBC`) and MAC integrity. The legacy default (`3DES`) is weak — prefer `-legacy` flag awareness when targeting compatibility vs `-certpbe AES-256-CBC -keypbe AES-256-CBC -macalg SHA-256` for strength.

**PKCS#7 / CMS**

PKCS#7 (`ContentInfo`) is the container for signed, enveloped, or digested data. CMS (RFC 5652) is the successor. OpenSSL's `cms` command handles both; `pkcs7` handles the older form.

```
ContentInfo ::= SEQUENCE {
  contentType ContentType,          ← OID: signedData, envelopedData, …
  content     [0] EXPLICIT ANY
}

SignedData ::= SEQUENCE {
  version          CMSVersion,
  digestAlgorithms DigestAlgorithmIdentifiers,
  encapContentInfo EncapsulatedContentInfo,   ← the signed payload
  certificates     [0] CertificateSet OPTIONAL,
  crls             [1] RevocationInfoChoices OPTIONAL,
  signerInfos      SignerInfos                ← one per signer
}
```

---

## 7. openssl.cnf — Configuration as Architecture

### 7.1 Structural Overview

`openssl.cnf` (or `OPENSSL_CONF` env var) is parsed at `OSSL_LIB_CTX` initialization time. Its misuse causes some of the most opaque OpenSSL failures.

```ini
# ── Top-level ────────────────────────────────────────────
[default_sect]
# This section is the default unless overridden by openssl_conf

openssl_conf = openssl_init         # ← entry point for libcrypto init

# ── libcrypto initialization ─────────────────────────────
[openssl_init]
providers = provider_sect           # load providers
alg_section = evp_sect              # EVP defaults
ssl_conf = ssl_sect                 # libssl defaults

# ── Provider loading ─────────────────────────────────────
[provider_sect]
default = default_sect_prov
fips    = fips_sect
legacy  = legacy_sect_prov
pkcs11  = pkcs11_sect

[default_sect_prov]
activate = 1

[fips_sect]
activate = 1
module = /usr/lib/x86_64-linux-gnu/ossl-modules/fips.so
# fips.cnf snippet can be included here or separately

[legacy_sect_prov]
activate = 1

[pkcs11_sect]
activate = 1
module = /usr/lib/x86_64-linux-gnu/pkcs11-provider.so
pkcs11-module-path = /usr/lib/softhsm/libsofthsm2.so

# ── EVP defaults ─────────────────────────────────────────
[evp_sect]
default_md = SHA256

# ── TLS defaults (libssl) ────────────────────────────────
[ssl_sect]
system_default = tls_system_default

[tls_system_default]
MinProtocol = TLSv1.2
CipherString = DEFAULT@SECLEVEL=2
```

### 7.2 Config Resolution Order

```
OPENSSL_CONF env var
    → /etc/ssl/openssl.cnf (compiled-in default path, OPENSSLDIR)
        → [openssl_conf] key in top section
            → named section for providers/ssl/alg
```

If `OPENSSL_CONF` points to a non-existent file, the **default provider is not loaded**. Every `EVP_*_fetch()` returns `NULL`. This is the most common production misconfiguration in containerized environments.

### 7.3 FIPS Module Configuration Split

FIPS mode requires two config files (or an `.include` merge):

```
openssl.cnf:
  [fips_sect]
  activate = 1
  module = /usr/lib/ossl-modules/fips.so
  .include /etc/ssl/fipsmodule.cnf    ← generated at install time

fipsmodule.cnf (generated by `openssl fipsinstall`):
  [fips_sect]
  module-mac = <HMAC-SHA256 of fips.so>
  install-mac = <HMAC of this config file>
  install-version = 1
  install-status = INSTALL_SELF_TEST_KATS_RUN
```

The two-HMAC design: `module-mac` binds the `.so` binary; `install-mac` binds the configuration. Tampering either breaks the POST at provider load.

### 7.4 What Breaks When Config Is Wrong

| Symptom | Likely config cause |
|---|---|
| `EVP_MD_fetch` returns NULL for common algorithms | `default` provider not activated (missing/wrong cnf) |
| `RAND_bytes` fails | DRBG provider not loaded |
| `SSL_CTX_new` succeeds but handshake fails immediately | `MinProtocol` too high, or cipher string evaluates to empty |
| `PEM_read_bio_PrivateKey` returns NULL, no error | Private key uses `legacy` provider algorithm (e.g., old DSA params); legacy not loaded |
| FIPS mode: everything fails | `fipsmodule.cnf` path wrong, or HMAC mismatch after `.so` update |
| `pkcs11` provider loads but `EVP_PKEY_sign` fails | `pkcs11-module-path` wrong, or token not present |

### 7.5 Reading Config Programmatically

```c
// Read config into an in-memory structure
CONF *conf = NCONF_new(NULL);
long eline;
NCONF_load(conf, "/etc/ssl/openssl.cnf", &eline);

// Read a specific key
const char *val = NCONF_get_string(conf, "tls_system_default", "MinProtocol");

// Apply to a library context (triggers provider loading)
OPENSSL_init_crypto(OPENSSL_INIT_LOAD_CONFIG,
    &(OPENSSL_INIT_SETTINGS){ .config_filename = "/custom/openssl.cnf" });
```

---

## 8. Key Internal Subsystems

### 8.1 BIO — Buffered I/O Abstraction

BIO is OpenSSL's I/O abstraction. It forms chains (filter BIOs stacked on source/sink BIOs) that transparently handle encoding, buffering, and transport.

```
Application: BIO_write(chain, data, len)
                        │
                        ▼
              [filter] BIO_f_ssl()      ← TLS record framing
                        │
              [filter] BIO_f_buffer()   ← buffering
                        │
              [sink]   BIO_s_socket()   ← OS socket fd
```

Common BIO types:

| BIO | Type | Purpose |
|---|---|---|
| `BIO_s_mem()` | source/sink | In-memory buffer |
| `BIO_s_file()` | source/sink | FILE* wrapper |
| `BIO_s_socket()` | source/sink | TCP socket |
| `BIO_f_ssl()` | filter | TLS record layer |
| `BIO_f_base64()` | filter | base64 encode/decode |
| `BIO_f_buffer()` | filter | Buffering |
| `BIO_f_cipher()` | filter | Symmetric encryption |

### 8.2 ASN.1 Code Generation

OpenSSL's ASN.1 engine generates `d2i_*` / `i2d_*` / `*_new` / `*_free` functions from macros in the source. Understanding this helps when reading error messages:

```c
// In x_x509.c:
ASN1_SEQUENCE(X509_CINF) = {
    ASN1_EXP_OPT(X509_CINF, version, ASN1_INTEGER, 0),
    ASN1_SIMPLE(X509_CINF, serialNumber, ASN1_INTEGER),
    ASN1_SIMPLE(X509_CINF, signature, X509_ALGOR),
    ASN1_SIMPLE(X509_CINF, issuer, X509_NAME),
    …
} ASN1_SEQUENCE_END(X509_CINF)

IMPLEMENT_ASN1_FUNCTIONS(X509_CINF)
// → generates: d2i_X509_CINF(), i2d_X509_CINF(), X509_CINF_new(), X509_CINF_free()
```

`d2i_*` functions take `const unsigned char **pp` — the pointer is advanced past consumed bytes. Forgetting to pass a pointer-to-pointer (passing the buffer directly) is a classic API mistake that corrupts the heap.

### 8.3 RAND Subsystem

```
Application: RAND_bytes(buf, len)
                │
                ▼
         RAND_DRBG  (per-thread in 3.x)
         ├─ Algorithm: CTR-DRBG (AES-256) by default
         ├─ Instantiated from primary DRBG
         └─ primary DRBG seeded from OSSL_RAND_get_provider_seed()
                │
                ▼
         OS entropy source
         ├─ Linux:   getrandom(2) / /dev/urandom
         ├─ macOS:   getentropy(2)
         └─ Windows: BCryptGenRandom
```

In FIPS mode, CTR-DRBG with AES-256 is mandatory. The DRBG health tests (NIST SP 800-90A) run at instantiation and continuously. Entropy sources below the DRBG are also validated.

### 8.4 Error Stack

OpenSSL uses a per-thread error stack (`ERR`). Errors accumulate from bottom (root cause) to top (API surface).

```
ERR_get_error()       ← pops oldest error
ERR_peek_error()      ← peeks without popping
ERR_peek_last_error() ← peeks newest (most surface-level)
ERR_print_errors_fp(stderr)  ← dump full stack

Error format: [lib]:[function]:[reason] at [file]:[line]
e.g.: error:0200100D:system library:fopen:No such file or directory
      error:2006D080:BIO routines:BIO_new_file:no such file
      error:0906D06C:PEM routines:PEM_read_bio:no start line
```

Never check only the top-of-stack error. The bottom error often contains the actual cause (e.g., a file not found under a PEM parse failure).

---

## 9. Command Cheatsheet

### Key Generation

```bash
# RSA 4096-bit private key (PKCS#8 PEM)
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:4096 -out rsa4096.key

# EC key (P-256)
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out ec_p256.key

# Ed25519
openssl genpkey -algorithm ED25519 -out ed25519.key

# Encrypted private key (AES-256-CBC, strong KDF)
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:4096 \
  -aes-256-cbc -pass pass:secret -out rsa4096_enc.key

# Convert PKCS#1 RSA key to PKCS#8
openssl pkcs8 -topk8 -nocrypt -in pkcs1.key -out pkcs8.key
```

### CSR and Certificates

```bash
# CSR from existing key
openssl req -new -key ec_p256.key -out request.csr \
  -subj "/C=FR/O=Acme/CN=example.com"

# CSR with SANs (inline config)
openssl req -new -key ec_p256.key -out san.csr \
  -subj "/CN=example.com" \
  -addext "subjectAltName=DNS:example.com,DNS:www.example.com,IP:1.2.3.4"

# Self-signed cert (10 years)
openssl req -x509 -key ec_p256.key -out cert.pem -days 3650 \
  -subj "/CN=my-ca" -addext "basicConstraints=critical,CA:TRUE"

# Sign CSR with CA
openssl x509 -req -in request.csr -CA ca.pem -CAkey ca.key \
  -CAcreateserial -out signed.pem -days 365 \
  -extfile <(printf "subjectAltName=DNS:example.com\nextendedKeyUsage=serverAuth")
```

### Inspection and Parsing

```bash
# Parse certificate (human-readable)
openssl x509 -in cert.pem -noout -text

# Print specific fields
openssl x509 -in cert.pem -noout -subject -issuer -dates -fingerprint -sha256

# Verify certificate chain
openssl verify -CAfile ca.pem -untrusted intermediate.pem leaf.pem

# Inspect CSR
openssl req -in request.csr -noout -text -verify

# Inspect private key
openssl pkey -in key.pem -noout -text

# Raw ASN.1 dump
openssl asn1parse -in cert.pem          # auto-detects PEM
openssl asn1parse -in cert.der -inform DER -dump

# Decode specific field by offset (from asn1parse output)
openssl asn1parse -in cert.pem -strparse <offset>
```

### Format Conversions

```bash
# PEM → DER
openssl x509 -in cert.pem -out cert.der -outform DER

# DER → PEM
openssl x509 -in cert.der -inform DER -out cert.pem -outform PEM

# PKCS#12 → PEM (cert + key)
openssl pkcs12 -in bundle.p12 -nocerts -nodes -out key.pem
openssl pkcs12 -in bundle.p12 -nokeys -out cert.pem

# PEM → PKCS#12
openssl pkcs12 -export \
  -in cert.pem -inkey key.pem -certfile chain.pem \
  -out bundle.p12 -name "my-alias" \
  -certpbe AES-256-CBC -keypbe AES-256-CBC -macalg SHA-256

# Inspect PKCS#12
openssl pkcs12 -in bundle.p12 -info -noout
```

### TLS Diagnostics

```bash
# Handshake debug + show full chain
openssl s_client -connect host:443 -showcerts -state -msg 2>&1 | head -100

# Test with specific TLS version
openssl s_client -connect host:443 -tls1_3
openssl s_client -connect host:443 -tls1_2 -cipher 'ECDHE-RSA-AES256-GCM-SHA384'

# STARTTLS variants
openssl s_client -connect smtp.host:587 -starttls smtp
openssl s_client -connect ldap.host:389 -starttls ldap

# Check cert expiry for live host
openssl s_client -connect host:443 </dev/null 2>/dev/null \
  | openssl x509 -noout -dates

# Serve TLS (quick test server)
openssl s_server -cert cert.pem -key key.pem -accept 4433 -www
```

### CRL and OCSP

```bash
# Fetch and parse CRL from CDP
curl -sL "$(openssl x509 -in cert.pem -noout -text \
  | grep -A1 'CRL Distribution' | tail -1 | tr -d ' ')" \
  | openssl crl -inform DER -noout -text

# OCSP check
openssl ocsp \
  -issuer issuer.pem -cert leaf.pem \
  -url "$(openssl x509 -in leaf.pem -noout -ocsp_uri)" \
  -resp_text -noverify
```

### Symmetric and Hash Operations

```bashkv
# Encrypt file (AES-256-GCM, pbkdf2)
openssl enc -aes-256-gcm -pbkdf2 -iter 600000 -in plain.txt -out cipher.bin

# Decrypt
openssl enc -d -aes-256-gcm -pbkdf2 -iter 600000 -in cipher.bin -out plain.txt

# Digest
openssl dgst -sha256 file.bin
openssl dgst -sha256 -hmac "key" file.bin
openssl dgst -sha256 -sign key.pem -out sig.bin file.bin
openssl dgst -sha256 -verify pubkey.pem -signature sig.bin file.bin
```

### Speed and Providers

```bash
# Benchmark
openssl speed aes-256-gcm ecdh rsa4096 sha256

# List available algorithms (from loaded providers)
openssl list -digest-algorithms
openssl list -cipher-algorithms
openssl list -public-key-algorithms
openssl list -providers

# Test provider loading explicitly
openssl list -providers -provider fips -provider-path /usr/lib/ossl-modules

# Verify FIPS module
openssl fipsinstall -verify -module /usr/lib/ossl-modules/fips.so \
  -mac_name HMAC -macopt digest:SHA256 -in fipsmodule.cnf
```

### PKCS#11 / HSM (with pkcs11-provider)

```bash
# List tokens
pkcs11-tool --list-slots

# Generate key on token
pkcs11-tool --module /usr/lib/softhsm/libsofthsm2.so \
  --keypairgen --key-type EC:prime256v1 --label mykey --id 01 --login

# Use HSM key for signing (via STORE URI)
openssl dgst -sha256 \
  -sign "pkcs11:token=mytoken;object=mykey;type=private;pin-value=1234" \
  -out sig.bin file.bin

# Generate CSR using HSM key
openssl req -new -engine pkcs11 -keyform engine \
  -key "pkcs11:token=mytoken;object=mykey" \
  -out request.csr -subj "/CN=example.com"
```

---

## Appendix: Mental Model Summary

```
                    ┌─────────────────────────────┐
  Application ─────▶│         libssl              │  TLS protocol only
                    │  SSL_CTX / SSL / BIO chain  │
                    └──────────────┬──────────────┘
                                   │ EVP calls only
                    ┌──────────────▼──────────────┐
                    │         libcrypto            │
                    │  ┌─────────────────────────┐ │
                    │  │    EVP Layer            │ │  Algorithm-agnostic API
                    │  │  (fetch, dispatch, ctx) │ │
                    │  └──────────┬──────────────┘ │
                    │             │ OSSL_DISPATCH   │
                    │  ┌──────────▼──────────────┐ │
                    │  │   Provider Registry     │ │  Per OSSL_LIB_CTX
                    │  │  default│fips│legacy│…  │ │
                    │  └─────────────────────────┘ │
                    │                               │
                    │  X.509 / ASN.1 / BIO / RAND  │
                    │  PKCS#7/8/12 / STORE          │
                    └───────────────────────────────┘
                         │            │          │
                    default.so    fips.so    pkcs11.so
                    (built-in)  (validated)  (hardware)
```

**Key invariants to internalize:**

1. Providers are the sole source of algorithm implementations in 3.x. No provider = no algorithm.
2. `EVP_PKEY` is opaque; key material lives in the provider, not in a struct you can cast to.
3. `OSSL_LIB_CTX` is the isolation boundary. Two contexts cannot cross-contaminate.
4. Config file absence ≠ default behavior; it means the default provider may not load.
5. `d2i_*` decodes structure. `X509_verify_cert()` validates. They are always separate steps.
6. DER is the canonical format. PEM is DER in base64. PKCS#12 is DER with optional encryption.
7. The error stack reads root-cause-up; always drain and log the full stack.

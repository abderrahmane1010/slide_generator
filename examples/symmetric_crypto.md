---

# Symmetric Cryptography for Embedded Devices
**Instructor** : Dr. Martin Dupont
**Date** : 08/06/2026
**Institution** : Université Paris-Saclay

---

# Chapter 1 — The Duality: Secrecy vs Authenticity

## Two Fundamental Purposes

### Secrecy (Confidentiality)
- Intercepted ciphertext cannot reveal plaintext
- Primitive: Cipher (block or stream)
- Output: Ciphertext

### Authenticity (Integrity + Authentication)
- Recipient verifies message came from key-holder
- Recipient detects any modification in transit
- Primitive: MAC (Message Authentication Code)
- Output: Tag / HMAC

## Critical Errors

| Misconception | Reality |
|---------------|---------|
| Encryption = Authentication | FALSE — Attacker can modify ciphertext undetected |
| Authentication = Secrecy | FALSE — MAC reveals full message |

## Solution: AEAD (Authenticated Encryption with Associated Data)

- Single primitive for both confidentiality and authenticity
- One key for both operations
- Correct default for embedded systems 2024
- Decryption returns: authenticated plaintext OR error (never unauthenticated plaintext)

## Key Points

- Same key, different use: one key for encryption and authentication separately
- Real systems need both: almost all systems require both properties
- AEAD is the default: never compose encryption + MAC manually
- No assumptions: never assume encryption provides authentication

> **Principle 1.** *AEAD is the right default.*

---

# Chapter 2 — The Threat Model for Embedded Systems

## Three Key Differences from Cloud Systems

**Physical access**
- Adversary can hold the device
- Can attach oscilloscopes, fault injection probes, JTAG adapters
- Threat model: local attacker with tools, not just network attacker

**Constrained resources**
- Kilobytes of RAM, megabytes of flash, milliwatts of power
- TLS 1.3 handshake costs ~10 kB RAM (entire budget for small MCUs)
- Algorithm must fit the constraints

**Long deployment lifetime**
- Devices ship and are not updated for years or decades
- Algorithm chosen today must remain secure for product lifetime
- Field update capability becomes critical

## Define Before Code

Threat model → Algorithm selection
Constraint budget → Implementation choice

> **Principle 2.** *The threat model determines the algorithm; constraint budget determines implementation. Both must be written down before code is written.*

---

# Chapter 3 — The Five Primitive Categories

| Category | Function | Input | Output | Standard Examples |
|----------|----------|-------|--------|-------------------|
| **Block Cipher** | Fixed-size permutation | Key + 128-bit plaintext | 128-bit ciphertext | AES-128/256 |
| **Stream Cipher** | Generate keystream | Key + nonce | Arbitrary-length keystream | ChaCha20 |
| **MAC** | Authenticate only | Key + message | Fixed-length tag | HMAC-SHA256, AES-CMAC |
| **AEAD** | Encrypt + authenticate | Key + nonce + plaintext + AD | Ciphertext + tag | AES-GCM, AES-CCM, ChaCha20-Poly1305 |
| **KDF** | Derive key material | Master key + context | Multiple independent keys | HKDF, SP 800-108 |

## Key Insight

Every algorithm selection question reduces to: **Which category do I need?**

> **Principle 3.** *If you cannot name the category of the primitive you are deploying, you do not yet understand your own system.*

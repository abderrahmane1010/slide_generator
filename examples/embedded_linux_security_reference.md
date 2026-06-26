# Embedded Linux Security
### Fundamental Concepts, Formal Models, and Architectural Principles
*Academic reference — conceptual and formal, illustrated by example · v3.2*

---

## 1. The Trust Problem in Embedded Systems

The central question of embedded security: **how can a remote principal assert a security property about a system it does not physically control?** Every technique in this field is a partial answer to it.

**Trust Assumption Stack** — each layer trusts the one below; the whole chain is only as strong as its weakest link:
```
Application → OS → Kernel/Bootloader → Hardware → Manufacturing
```
*No software-only security compensates for a compromised hardware layer.* This asymmetry is the primary motivation for hardware roots of trust.

> *Example: A system enforcing SELinux provides zero guarantee if the bootloader was replaced. The policy is meaningless without first verifying the kernel that enforces it.*

**Attacker Model** — every security claim must specify which class it defeats:

| Class | Capability |
|---|---|
| Remote software | Network access only; cannot break crypto |
| Local software | OS-level access, malicious application |
| Physical passive | Observes power, EM, timing — no modification |
| Physical active | Modifies power, clocks, probing, fault injection |

**Attack surface:** boot chain · runtime software · network interfaces · serial/debug (JTAG, SWD) · storage · physical domain.

> **📌 Key Takeaways:** The central question is provability at a distance. Security is a vertical chain — one compromised layer invalidates everything above. Every mechanism must declare its attacker class explicitly. The attack surface is wider than software: debug ports and power rails count.

---

## 2. Chain of Trust

A **chain of trust** is a transitive verification relation: each boot stage is authorized to execute only after cryptographic verification by its predecessor.

For ordered stages `S = {S₀, …, Sₙ}`, the verification relation is:
```
Verify(Sᵢ → Sᵢ₊₁) = TRUE
  iff  PKVERIFY(PKᵢ, SIG(SKᵢ, H(Sᵢ₊₁)), H(Sᵢ₊₁)) = VALID
```
**Chain invariant:** `System trusted ⟺ ∀i : Verify(Sᵢ → Sᵢ₊₁) = TRUE`. A single failure → **HALT** (fail-secure; no degraded mode).

**Hardware Root of Trust (S₀):** the only stage whose trust is hardware-guaranteed (immutable ROM, OTP-fused key hash, TPM). If S₀ is compromised, the entire chain is void.
```
S₀ (ROM/OTP) → S₁ (SPL) → S₂ (U-Boot) → S₃ (Kernel) → Sₙ (dm-verity/IMA)
```
**Rollback protection:** signature verification alone is insufficient — an attacker can replay an older, signed, vulnerable image. A monotonic hardware counter (TPM NV, eFuses) enforces:
```
Accept ⟺ Verify(sig) AND version(image) ≥ HW_COUNTER
Commit ⟺ HW_COUNTER++ (irreversible, even by manufacturer)
```
> *Example: NXP i.MX8 — ROM verifies U-Boot via OTP-fused key hash → U-Boot verifies a signed FIT image (kernel+DTB+initramfs) → kernel mounts rootfs via dm-verity (root hash pinned in signed cmdline). Rollback blocked by TPM NV counter.*

> **📌 Key Takeaways:** Each stage verifies the **hash** (integrity) and **signature** (authenticity) of the next. One failure = halt, no exception. The root of trust is hardware-immutable by definition. Signature without anti-rollback is incomplete: you must also enforce `version ≥ HW_COUNTER`.

---

## 3. Device Identity

A valid device identity requires three simultaneous properties: **uniqueness** (no two devices share it), **unforgeability** (cannot be cloned), **persistence** (survives reboots and updates). A software-defined identity (UUID in flash, MAC address) satisfies none of these against a physical adversary.

**Minimal identity:** asymmetric key pair `(SK, PK)`. `SK` resides exclusively in hardware-protected storage and **never leaves the device**. Identity is proven by signing a challenge with `SK` — demonstrating possession without disclosure. A certificate `Cert = Sign(CA_SK, {PK ‖ metadata})` binds `PK` to device attributes.

**PKI hierarchy for fleets:**
```
Root CA (offline, air-gapped, HSM)
    ↓ signs
Manufacturing CA (online, HSM, restricted)
    ↓ issues at production time, per device
Device Certificate (unique, stored in secure hardware)
```
Root CA compromise invalidates the entire fleet's identity. Critical X.509 fields: `Subject` (serial+SKU), `KeyUsage` (digitalSignature, keyAgreement — never keyCertSign), `ValidityPeriod` (full device lifetime), `SubjectAltName` (machine-readable URI).

> *Example: ATECC608 secure element generates ECDSA P-256 keypair at factory. Public key → signed X.509 by Manufacturing CA. Mutual TLS at connection validates both sides. A clone with a copied certificate but no hardware-backed SK cannot complete the handshake.*

> **📌 Key Takeaways:** Software identity = clonable. Hardware identity = unforgeable. The certificate is the cryptographic passport; `SK` never leaves the device. Root CA must be offline — its compromise requires physical re-provisioning of the entire fleet.

---

## 4. Integrity Guarantees

Two distinct and complementary integrity problems:

| Problem | When | Mechanism |
|---|---|---|
| **Static** | At boot, before execution | Digital signature over image |
| **Runtime** | Per-access, during execution | Merkle hash tree over storage (dm-verity) |

**dm-verity** builds a Merkle tree over a block device. The root hash is fixed at boot (signed, embedded in kernel cmdline). Every block read triggers hash verification — any modification changes the root hash, making it computationally infeasible to tamper undetected.

*Key limitation:* dm-verity only protects **read-only** partitions. Writable partitions require AEAD encryption or append-only authenticated structures.

**IMA** (Integrity Measurement Architecture) extends integrity to individual files, measuring hash at open time against a signed reference. **EVM** adds protection to file metadata (permissions, ownership) preventing metadata-only tampering.

> *Example: Read-only rootfs under dm-verity. Writable config partition encrypted with AES-GCM — any unauthorized write produces an invalid authentication tag, rejected at next decryption before the application ever parses the config.*

> **📌 Key Takeaways:** Static signature at build time ≠ runtime integrity. Both are required. dm-verity = per-block Merkle verification, read-only only. IMA = per-file open-time verification. A valid signature on a firmware image does not prevent runtime filesystem tampering.

---

## 5. Isolation & Privilege Separation

**Least privilege:** every component operates with the minimum permissions required — a **damage-containment** principle, not a prevention principle.

**Hardware isolation primitives:**

| Mechanism | Enforced by | Defeats |
|---|---|---|
| MMU | CPU hardware | Process-to-process memory access |
| IOMMU | Hardware | DMA peripherals reading arbitrary memory |
| ARM TrustZone | CPU + SoC | Normal-world access to secure memory |
| Hypervisor (Type-1) | CPU virt. extensions | VM-to-VM isolation |

*IOMMU gap:* without an IOMMU, any DMA-capable peripheral bypasses all MMU-based isolation. Software alone cannot close this.

**Software isolation primitives in Linux:**

| Mechanism | Isolates |
|---|---|
| Capabilities | Decomposes root privilege (no full CAP_SYS_ADMIN needed) |
| seccomp-BPF | System call surface (allowlist per process) |
| Namespaces | PID, network, mount, user — isolated views |
| LSM (SELinux/AppArmor) | All kernel objects, mandatory access control |

> *Example: MQTT broker — no root, network namespace port 1883 only, seccomp allowlist of 6 syscalls. RCE in the broker = the broker process only. No shell, no filesystem, no other network interfaces.*

> **📌 Key Takeaways:** Compromising a sandboxed process ≠ compromising the system. Isolation turns an RCE into a contained incident. The IOMMU gap is hardware-only — DMA peripherals can be as dangerous as a rogue process without it. Mechanisms stack: capabilities + seccomp + namespaces + LSM together.

---

## 6. Confidentiality at Rest and in Transit

Two distinct problems solved by different constructions:

| Scenario | Threat | Mechanism |
|---|---|---|
| At rest | Physical access to storage | Encryption keyed to hardware secret |
| In transit | Network interception | AEAD over authenticated channel |

**At rest — key binding problem:** encrypting storage is trivially defeated if the key lives on the same medium. The key must be **bound to specific hardware** — derivable only on that device:
```
Hardware secret (inaccessible to software)
    → Storage key (ephemeral, RAM only)
        → Encrypted partition
```
*Invariant: the plaintext key must never be written to non-volatile storage.*

**In transit — AEAD:** unauthenticated encryption (AES-CBC alone) is vulnerable to chosen-ciphertext attacks. Every channel must use Authenticated Encryption with Associated Data:
```
(C, tag) = AEAD_Enc(K, nonce, plaintext, associated_data)
plaintext = AEAD_Dec(K, nonce, C, tag, AD)  → error if tag invalid
```
*Nonce discipline:* nonce reuse under the same key completely breaks AES-GCM authentication. Use a counter or nonce-misuse-resistant AES-SIV on systems with limited entropy at boot.

> *Example: Medical device transmits over DTLS 1.3/AES-128-GCM. Device serial in associated_data. Replaying device A's ciphertext as device B fails — AD mismatch.*

> **📌 Key Takeaways:** "At rest" and "in transit" are separate problems — conflating them creates architectural errors. AEAD is mandatory in transit (confidentiality + integrity atomically). The key for at-rest encryption must be hardware-bound and never stored in clear. Nonce reuse breaks GCM entirely.

---

## 7. Authentication & Mutual Proof

Authentication answers: *"Is this entity who it claims to be?"* All three directions are required: device→server, server→device, device→device. Unilateral authentication enables man-in-the-middle attacks. **Mutual authentication is the minimum baseline.**

**Challenge-response — the fundamental primitive:**
```
Verifier:  c ← random nonce  ──────────────────► Prover (Device)
                              ◄── r = Sign(SK, H(c ‖ context)) ──
Verifier:  PKVERIFY(PK, r, H(c ‖ context)) ?
```
Properties: **freshness** (c unpredictable → anti-replay), **binding** (context = session transcript → anti cross-protocol), **non-transferability** (r is a signature, not reusable by the verifier).

This pattern underlies TLS 1.3 `CertificateVerify`, OPC UA, and FIDO attestation.

**PSK limitations:** a compromised PSK affects all devices sharing it; no non-repudiation; does not scale. Acceptable only as a bootstrap mechanism for initial provisioning.

> *Example: Energy meters use PSK per batch for provisioning only. Each generates an ECDSA P-256 keypair in TPM → receives X.509 cert → switches to mTLS. PSK revoked post-provisioning. Compromising one meter affects only that meter.*

> **📌 Key Takeaways:** Authentication ≠ encryption — they solve different problems and must both be present. Mutual = both sides authenticate. Challenge-response: nonce prevents replay; context prevents cross-protocol reuse. PSK is a bootstrap tool, never a production identity mechanism at fleet scale.

---

## 8. Attestation

Authentication proves *who* a device is. **Attestation proves *what state* it is in:** "Is it running exactly the expected software, unmodified?"

**TPM 2.0 PCR-based attestation:** the TPM accumulates boot measurements using an irreversible extend operation:
```
PCR[n] ← H(PCR[n] ‖ measurement_n)
```
PCR values cannot be rewound without a power cycle. After boot, the PCR state is a **cryptographic fingerprint of the entire boot path.**

The device issues a **quote** signed by its Attestation Identity Key (AIK):
```
Quote = TPM2_Sign(AIK_priv, H(PCR_values ‖ nonce))
```
Verifier validates: (1) AIK cert chain → real TPM, (2) quote signature → authentic + fresh, (3) PCR values vs golden measurements → expected software ran.

**Software attestation is fundamentally insecure:** an adversary controlling the software controls the measurement — the device can report any state. Not a security primitive against Class 1+ attackers.

> *Example: Industrial gateway sends TPM quote over PCRs 0–7 at each connection. Management platform compares PCR[4] (bootloader) and PCR[9] (kernel) against published hashes for firmware v2.4.1. Tampered gateway is quarantined — even with a valid device certificate.*

> **📌 Key Takeaways:** Identity (authentication) + state (attestation) are both required. A valid certificate does not prove the device is uncompromised. PCR extend is irreversible — no rewinding without reboot. Software attestation is not a security primitive: an attacker who controls software controls measurements.

---

## 9. Key Lifecycle

**Kerckhoffs's principle:** security depends on the secrecy of the **key**, not the algorithm. Key management is the core of the security architecture, not a detail.

**Lifecycle: Generation → Storage → Use → Rotation → Revocation → Destruction**

| Phase | Requirement | Embedded Constraint |
|---|---|---|
| Generation | TRNG, on hardware | Limited entropy at first boot |
| Storage | Hardware-protected, never plaintext on fs | TPM, SE, CAAM, TrustZone |
| Use | Minimum exposure; zeroize after use | Explicit `OPENSSL_cleanse()` |
| Rotation | Before cryptographic lifetime expires | Requires working update mechanism |
| Revocation | Fleet-wide invalidation | CRL/OCSP or short-lived certs |
| Destruction | Cryptographic erasure | Flash wear-leveling retains copies — prefer hardware destruction |

**Key hierarchy** limits blast radius of any single compromise:
```
KEK (hardware, never touches data)
 ├─ DEK (wrapped by KEK, ephemeral in RAM)
 ├─ Signing Key (firmware/updates, rotated via ceremony)
 └─ Session Key (per-session ECDHE, forward secrecy)
```
> *Example: NXP i.MX8 — CAAM OTPMK (hardware-only, never software-readable) wraps the DEK as a black blob in flash. At boot, CAAM decrypts blob in hardware and delivers DEK directly to dm-crypt. The DEK never appears in software-readable memory.*

> **📌 Key Takeaways:** A private key in cleartext on the filesystem = zero security regardless of all other mechanisms. Hierarchy limits blast radius: session key compromise ≠ DEK compromise ≠ KEK compromise. Flash wear-leveling makes software-only zeroization unreliable — hardware key destruction is the gold standard.

---

## 10. Secure State Transitions

**Invariant:** a system must remain in a coherent, authenticated state before, during, and after every transition. No partially-updated, unauthenticated, or ambiguous state may be reachable.

**Secure boot automaton:** deterministic, single success path, single failure mode (HALT):
```
POWER_ON → [VERIFY S₁] →FAIL→ HALT
              ↓ PASS
           [VERIFY S₂] →FAIL→ HALT
              ↓ PASS
           [VERIFY S₃] →FAIL→ HALT
              ↓ PASS
           RUNNING
```

**Firmware update automaton (A/B partition scheme):**
```
IDLE → VERIFY_PACKAGE →(bad sig | version ≤ counter)→ ABORT
         ↓ valid
       WRITE_INACTIVE_SLOT →(error)→ ABORT (active slot untouched)
         ↓ success + hash check
       SET_BOOT_FLAG (atomic) → REBOOT
         ↓
       VERIFY_NEW_FW →FAIL→ ROLLBACK to old slot
         ↓ PASS
       HEALTH_CHECK →(timeout/fail)→ ROLLBACK
         ↓ PASS
       HW_COUNTER++ (irreversible) → IDLE (committed)
```
*Critical:* HW_COUNTER increments only **after** health check passes in real execution. Premature increment → permanent brick risk.

**Decommissioning:** destroy the KEK, not the data. Destroying the root key renders all derived ciphertext permanently irrecoverable.

> *Example: RAUC A/B scheme — active slot never written during update. 3 failed boots → automatic rollback, no network needed.*

> **📌 Key Takeaways:** Every state transition is a security event. A/B partitioning is the canonical answer to update atomicity. HW_COUNTER++ only after successful health check. Decommissioning = key destruction, not data wipe.

---

## 11. Anti-Counterfeiting & Physical Unclonability

**Cloning threat:** readable non-volatile secrets → copy to new hardware → software-identical clone that passes all identity checks. Defeating this requires binding identity to a **physically irreproducible** property.

**Physically Unclonable Functions (PUFs)** exploit uncontrollable nanoscale manufacturing variation: `f: Challenge → Response`.

| Property | Meaning |
|---|---|
| Uniqueness | Inter-device Hamming distance ≈ 50% |
| Reliability | Intra-device Hamming distance ≈ 0% (with ECC) |
| Unpredictability | k known CRPs give no advantage on CRP k+1 |
| Unclonability | Reproducing fabrication variation is infeasible |

A PUF is a **physical function, not a key.** The key is derived: `K = KDF(ECC_Decode(PUF(C), helper_data))`. `helper_data` is public (reveals nothing about K). K is **never stored** — reconstructed at each power-up from the physical structure. Destroying the silicon destroys K irreversibly.

**Overbuilding control:** a monotonic counter at the provisioning server, incremented per certificate issued, prevents manufacturing beyond the contracted quantity.

> *Example: ATECC608B — internal PUF derives an ECDSA P-256 key never exposed even to the manufacturer. Decapping the chip yields only silicon — the key exists only as an emergent property during operation.*

> **📌 Key Takeaways:** Software identity = clonable. PUF-based identity = physically unclonable. The PUF is a function, not storage — the key emerges from physics at runtime and is never stored anywhere. Silicon destruction = irreversible key destruction.

---

## 12. Side-Channel & Fault Attacks

**Side-channel model:** cryptographic proofs assume the adversary sees only inputs/outputs. Physical implementations leak via correlated physical quantities. If `L` is the leakage and `S` the secret:
```
Vulnerable:  I(S ; L) > 0
Secure:      I(S ; L) = 0     (leakage independent of secret)
```

**Passive side-channels:**

| Attack | Observes | Countermeasure |
|---|---|---|
| Timing | Execution time variance | Constant-time code; no secret-dependent branches |
| SPA | Single power trace | Key-independent execution path |
| DPA | Statistical analysis, many traces | Boolean/arithmetic masking |
| Cache-timing | Cache hit/miss latency | Bit-sliced AES (no T-table lookups) |
| EMA | Near-field EM emission | Shielding, decoupling |

**Fault attacks (active perturbation):**

| Method | Target |
|---|---|
| Voltage glitching | Skip conditional branch (`if (verify()) boot()`) |
| Clock glitching | Setup/hold violation → wrong instruction result |
| Laser fault injection | Flip specific bit in SRAM or register |

*Countermeasure — double verification:* verify twice on independent code paths; compare results before acting. A dual-point fault is exponentially harder. Incorrect execution also alters TPM PCR values, detectable at next attestation.

> *Example: Bootloader verifies signature twice via independent paths. A glitch corrupting one check must simultaneously corrupt the other identically — orders of magnitude harder than single-point fault.*

> **📌 Key Takeaways:** Side-channels break the input/output-only observation assumption. `I(S;L) > 0` = exploitable. Constant-time code eliminates timing side-channels. Masking defeats first-order DPA. Fault attacks skip checks rather than break crypto — double verification is the primary defense. "Correct" in theory ≠ "secure" as a physical implementation.

---

## 13. Physical Security & Tamper Evidence

Software security **assumes** a trusted execution environment. Physical security **creates** it. Without a physical perimeter, any security property is violable with sufficient time and equipment.

**Three graduated objectives:**

| Objective | Definition | Approach |
|---|---|---|
| Tamper evidence | Access detectable after the fact | Seals, epoxy, deforming coatings |
| Tamper detection | Intrusion detected at runtime | Mesh, light sensors, voltage monitors → security controller |
| Tamper resistance | Access infeasible within threat model constraints | Potting, hardened enclosures, active countermeasures |

**Debug interfaces (JTAG, SWD, UART) are the highest-risk physical attack surface.** An open JTAG port enables arbitrary memory read, CPU halt, flash dump — bypassing all software security. The correct control is hardware-irreversible fuse disablement post-manufacturing. An attacker with physical access cannot re-enable it.

**Tamper-responsive architecture:** sensors → independent security controller (battery-backed) → zeroize key material in microseconds → append-only tamper log → permanent lockdown.

> *Example: PCI PTS terminals — conductive mesh in housing, battery-backed tamper controller. Opening the case breaks the mesh → immediate PIN key zeroization in SRAM → permanent brick in milliseconds.*

> **📌 Key Takeaways:** JTAG open in production = all software security is null. Check this first in any hardware audit. The three levels of physical protection scale with attacker class — choose according to the threat model. Zeroization must be faster than the attack (~microseconds). The security controller must be independent of the main CPU and battery-backed.

---

## 14. Secure Observability

A device with unknown security state is a liability. **Secure observability** is the ability to determine — after the fact — that a security event occurred or demonstrably did not.

**Tamper-evident logs:** a log that can be altered by its target adversary has no forensic value. The canonical structure is a **hash chain**:
```
Eₙ = (timestampₙ, eventₙ, H(Eₙ₋₁))   signed by key inaccessible to the logging process
```
Modifying entry `k` invalidates the link to `k+1` — detectable on any audit. Same structure as the TPM event log and Certificate Transparency.

**Attestation as continuous monitoring:** periodic re-attestation detects tampered devices (PCR change), runtime infection (IMA measurement change), or missing updates (PCR mismatch against current golden values).

**Tiered architecture for constrained devices:**
```
On-device   → lightweight rule detection → alerts only (not raw logs)
Edge gateway → local cluster aggregation and correlation
Cloud/SIEM  → fleet-wide correlation, trend analysis, incident response
```
> *Example: Inverter fleet sends signed telemetry (attestation result, dm-verity errors, auth failures). One dm-verity error = maintenance alert. Same error on 40 devices in the same area in one hour = coordinated physical attack → incident response.*

> **📌 Key Takeaways:** Security without observability is incomplete — a compromised device undetected is a device in service. Log integrity is a security property in itself (hash chain). Attestation is not one-time: continuous re-attestation detects drift. Fleet-level correlation reveals patterns invisible at the individual device level.

---

## 15. Supply Chain Security

Security analysis typically starts at first power-up. But an adversary controlling the build pipeline, contract manufacturer, or distribution channel can compromise a device **before deployment** with no runtime trace.

**Attack surface:**
```
Silicon foundry → PCB assembly → Firmware build → Key provisioning → Distribution → Installation
```

**Reproducible builds:** the build process produces bit-for-bit identical output from the same source, regardless of environment or timestamp. Anyone can rebuild and compare hashes against the published binary. Reproducibility does not prevent compromise — it makes it **detectable**.

**Firmware Transparency:** analogous to Certificate Transparency — all firmware releases are published in an append-only, publicly auditable log before devices accept them. Compromising the signing key allows signing malicious firmware, but not **silently** — the event is irrevocably recorded.

**SBOM** (Software Bill of Materials): enumerates every component and version in a firmware image. When a CVE is disclosed, the SBOM enables immediate, automated identification of all affected devices in the fleet.

> *Example: SolarWinds — malicious code injected into the build process, producing validly-signed updates. Reproducible builds would have revealed the hash discrepancy between source-built and distributed binaries. No reproducibility = no independent verification.*

> **📌 Key Takeaways:** The supply chain is a pre-deployment attack surface. A valid signature only proves the signing server was reachable — not that the binary is clean. Reproducible builds make build-time compromise detectable. Firmware Transparency makes silent signed-malware deployment impossible. SBOM enables fleet-wide CVE impact assessment.

---

## 16. Synthesis: Defense-in-Depth

No single mechanism is sufficient. Defense in depth constructs **overlapping, independent layers** — the attacker must defeat all simultaneously.

```
L0  Manufacturing & Supply Chain   — HRoT, provisioning, reproducible builds, SBOM
L1  Secure Boot                    — verified chain, signed FIT, rollback protection
L2  Boot Measurements              — TPM PCR extend, golden measurement enrollment
L3  Runtime Isolation              — MMU/IOMMU, KASLR, read-only kernel
L4  Process Isolation              — capabilities, seccomp, namespaces, LSM
L5  Data Protection                — dm-verity, dm-crypt/LUKS, IMA
L6  Communication Security         — mTLS 1.3, AEAD, cert pinning, nonce management
L7  Physical Protection            — debug fusing, tamper detection, side-channel mitigations
L8  Observability & Response       — attestation, signed telemetry, SIEM, incident response
```

**Security is not additive.** Eight strong mechanisms + one architectural flaw (SK in a log file, unauthenticated admin interface) = zero security. Security is an **emergent property of the whole system**, not a sum of parts. Threat modeling must be revisited at every architectural decision point.

**The optimal posture is not the maximum achievable** — it is the minimum sufficient to defeat the documented threat model. Every control has cost: boot latency, I/O overhead, BOM cost, maintenance complexity.

> **📌 Key Takeaways:** Independence between layers is the key property — not the number of layers. Security is a system property, not a checklist. The threat model from Chapter 1 is the thread running through all layers. Optimize for "minimum sufficient," not "maximum possible."

---

## 17. Standards & Compliance

| Standard | Scope | Key Requirement |
|---|---|---|
| **FIPS 140-3** | Cryptographic module | Approved algorithms, TRNG, power-on self-tests, zeroization |
| **Common Criteria (ISO 15408)** | Product security evaluation | EAL levels; formal security target + threat model |
| **IEC 62443** | Industrial control systems | Security Levels SL1–SL4; zone-and-conduit architecture |
| **ETSI EN 303 645** | Consumer IoT baseline | No default passwords; mandatory update mechanism |
| **NIST SP 800-193** | Platform firmware resilience | Protection, Detection, Recovery triad |
| **PSA Certified** | ARM IoT baseline | Certified HRoT; four certification levels |
| **ISO 21434 / WP.29** | Automotive cybersecurity | Full lifecycle; TARA mandatory |

**Certification ≠ Security.** A FIPS 140-3 validated module can be deployed insecurely if key management or integration is flawed. Certification is a **floor** in regulated environments, not a guarantee and not a substitute for threat modeling.

**Correct order:** threat model → architecture → implementation → certification. Not the reverse.

**Security Audit Checklist (production):**
```
□ Secure boot enforced (not just logged); signing keys in HSM
□ Anti-rollback via monotonic hardware counter
□ Debug interfaces (JTAG/SWD/UART) permanently fused off
□ Kernel: KASLR, stack-protector-strong, read-only text, lockdown mode
□ Rootfs: read-only + dm-verity; writable parts LUKS-encrypted, hardware-bound key
□ All processes: capabilities dropped, seccomp filter, LSM policy
□ Per-device keypair in hardware; mTLS on all security-relevant channels
□ No plaintext private keys on filesystem or in firmware binary
□ A/B partitions; update packages signature-verified; rollback tested
□ SBOM published; CVE monitoring automated; cert expiry alerting active
□ Boot attestation reported to management platform
```

> **📌 Key Takeaways:** Know which standard applies to your domain (FIPS/CC for crypto, IEC 62443 for industrial, EN 303 645 for consumer IoT, ISO 21434 for automotive). Certification is a floor, not a ceiling. The audit checklist covers 7 domains — each unchecked box is a documented attack surface.

---

## 18. References

**Foundational:** Anderson, R. — *Security Engineering*, 3rd ed., 2020 (free: cl.cam.ac.uk) · Dolev & Yao — *On the security of public key protocols*, IEEE ToIT, 1983 · Kocher et al. — *Introduction to DPA*, J. Cryptographic Engineering, 2011 · Boneh & Shoup — *A Graduate Course in Applied Cryptography*, 2023 (crypto.stanford.edu/~dabo/cryptobook)

**Standards:** NIST FIPS 140-3 · NIST SP 800-193 · TCG TPM 2.0 Library · RFC 8446 (TLS 1.3) · RFC 9147 (DTLS 1.3) · ARM PSA (developer.arm.com) · ETSI EN 303 645

**Projects:** Linux Kernel Security (kernel.org/doc/html/latest/security/) · OP-TEE (optee.readthedocs.io) · RAUC (rauc.readthedocs.io) · Keylime (keylime.dev) · OWASP Embedded AppSec

---
*Security is an evolving discipline. Review at each major product revision and on CVE disclosures affecting referenced components.*

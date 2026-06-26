# Bootloaders and Secure Boot in the Embedded World — Zero to Hero
### A Manual of First Principles

> *Built from the ground up. Every concept earns its place. Every diagram exists because words alone would be longer.*

---

## Preface

Most documentation on bootloaders is either too hardware-specific to generalize, or too abstract to implement. Tutorials show *how* to configure U-Boot; datasheets show *what* the ROM does. Neither explains *why* the chain exists in its current form, or why breaking any link has the consequences it does.

This guide fills that gap. It is written for engineers who already understand C, basic ARM/x86 architecture, and Linux fundamentals, but who want a rigorous, unified model of what happens between power-on and `init`. It treats secure boot not as a feature to toggle, but as a logical consequence of the trust problem that any networked, field-deployed device must solve.

**After Part II**, you will be able to trace the exact execution path from ROM to kernel on any major embedded platform.  
**After Part IV**, you will be able to design, implement, and audit a secure boot chain for a production device.  
**After the Appendices**, you will have a reference vocabulary and mental map that survives job changes and platform migrations.

**This guide does not cover:**
- PC BIOS/UEFI in depth (it is referenced only where it illuminates embedded principles).
- Bootloader porting from scratch (focus is on principles and configuration, not BSP authorship).
- OS-level security beyond the boot boundary (SELinux, AppArmor, etc.).

**Prerequisites:** C programming, basic ARM/x86 memory maps, Linux command-line fluency.

---

## Table of Contents

- [Part I — Foundations](#part-i--foundations)
  - [1. What a Bootloader Actually Does](#1-what-a-bootloader-actually-does)
  - [2. The Trust Problem: Why Secure Boot Exists](#2-the-trust-problem-why-secure-boot-exists)
  - [3. Hardware Primitives That Make Boot Possible](#3-hardware-primitives-that-make-boot-possible)
- [Part II — The Boot Chain](#part-ii--the-boot-chain)
  - [4. Stage 0: The ROM (Immutable Trust Anchor)](#4-stage-0-the-rom-immutable-trust-anchor)
  - [5. Stage 1: SPL / First-Stage Loader](#5-stage-1-spl--first-stage-loader)
  - [6. Stage 2: The Full Bootloader (U-Boot, Barebox, GRUB)](#6-stage-2-the-full-bootloader-u-boot-barebox-grub)
  - [7. Stage 3: The Kernel Handoff](#7-stage-3-the-kernel-handoff)
- [Part III — Secure Boot Architecture](#part-iii--secure-boot-architecture)
  - [8. Cryptographic Foundations](#8-cryptographic-foundations)
  - [9. The Chain of Trust: Formal Model](#9-the-chain-of-trust-formal-model)
  - [10. Key Hierarchy and OTP Fuses](#10-key-hierarchy-and-otp-fuses)
  - [11. Image Signing Workflows](#11-image-signing-workflows)
- [Part IV — Platform Implementations](#part-iv--platform-implementations)
  - [12. ARM TrustZone and OP-TEE](#12-arm-trustzone-and-op-tee)
  - [13. NXP HABv4 / AHAB](#13-nxp-habv4--ahab)
  - [14. Raspberry Pi Secure Boot](#14-raspberry-pi-secure-boot)
  - [15. UEFI Secure Boot (Embedded Perspective)](#15-uefi-secure-boot-embedded-perspective)
- [Part V — Production Concerns](#part-v--production-concerns)
  - [16. Key Management in Manufacturing](#16-key-management-in-manufacturing)
  - [17. Recovery, Rollback, and Anti-Rollback](#17-recovery-rollback-and-anti-rollback)
  - [18. Attestation and Remote Integrity Verification](#18-attestation-and-remote-integrity-verification)
  - [19. Common Attack Vectors and Mitigations](#19-common-attack-vectors-and-mitigations)
- [Appendices](#appendices)
  - [A — Glossary](#a--glossary)
  - [B — Key Variables and Constants to Memorize](#b--key-variables-and-constants-to-memorize)
  - [C — Comparative Platform Table](#c--comparative-platform-table)
  - [D — Learning Path](#d--learning-path)
  - [E — Reference Map (Mind Map)](#e--reference-map)

---

# Part I — Foundations

## 1. What a Bootloader Actually Does

**Formal definition:** A bootloader is a program whose sole responsibility is to initialize the hardware to a known state and transfer control to a more capable program, ultimately delivering execution to the operating system kernel with a correct environment descriptor.

This definition has three operative clauses:
1. *Initialize hardware to a known state* — RAM must be trained, clocks configured, and memory-mapped I/O accessible.
2. *Transfer control* — the CPU instruction pointer jumps to a new address.
3. *Correct environment descriptor* — the kernel must receive a structured description of the hardware (Device Tree Blob on ARM, multiboot header on x86).

```
Power-On Reset
      │
      ▼
┌─────────────────────────────────────────────────────┐
│  ROM / BootROM  (immutable, vendor-burned)           │
│  ■ Minimal HW init (clock, boot device selection)   │
│  ■ Loads next stage from flash/SD/USB               │
│  ■ (Optionally) verifies signature                  │
└─────────────────┬───────────────────────────────────┘
                  │ jumps to
                  ▼
┌─────────────────────────────────────────────────────┐
│  Stage 1 Loader  (SPL, XLoader, MLO)                │
│  ■ Runs from SRAM (tiny — fits in on-chip memory)   │
│  ■ Trains DDR/LPDDR                                 │
│  ■ Loads Stage 2 into DDR                           │
└─────────────────┬───────────────────────────────────┘
                  │ jumps to
                  ▼
┌─────────────────────────────────────────────────────┐
│  Stage 2 Loader  (U-Boot proper, Barebox, GRUB)     │
│  ■ Full peripheral init (Ethernet, USB, storage)    │
│  ■ Loads kernel + DTB + initrd from storage         │
│  ■ Passes boot args; hands off to kernel            │
└─────────────────┬───────────────────────────────────┘
                  │ boots
                  ▼
┌─────────────────────────────────────────────────────┐
│  Linux Kernel + Device Tree Blob                    │
└─────────────────────────────────────────────────────┘
```

> **Principle 1.** *A bootloader exists because the CPU starts in a state unsuitable for running an OS: no DRAM, no filesystem, no interrupt model. Each stage exists solely to remove one class of that unsuitability.*

### Why Multiple Stages?

The constraint is physical: on-chip SRAM (where the CPU can execute immediately after reset) is typically 4–256 KB. A full bootloader like U-Boot can be 1–2 MB. Therefore:

| Stage | Execution Medium | Typical Size | Primary Job |
|-------|-----------------|-------------|-------------|
| ROM | On-chip ROM | 32–256 KB | Load Stage 1 |
| SPL (Stage 1) | On-chip SRAM | 8–200 KB | Train DDR, load Stage 2 |
| Full BL (Stage 2) | DDR RAM | 512 KB–2 MB | Load OS, interact with user |
| Kernel | DDR RAM | 5–30 MB | Run OS |

---

## 2. The Trust Problem: Why Secure Boot Exists

Consider a device deployed in the field: a smart meter, an automotive ECU, an industrial gateway. An attacker with physical access can:

1. Remove the storage medium (eMMC/SD) and write a modified kernel.
2. Interrupt the boot process via JTAG and inject arbitrary code.
3. Use the network to push a malicious firmware update.

Without a mechanism to distinguish authorized firmware from unauthorized firmware, the device will boot anything. **This is the trust problem.**

```
Without Secure Boot:              With Secure Boot:
                                  
Power-On                          Power-On
   │                                 │
   ▼                                 ▼
  ROM ──────────────────────►  ROM (has Public Key Hash burned in OTP)
   │                                 │
   ▼                                 ▼  VERIFY signature of SPL
  SPL (any SPL)                  SPL ──► signature valid? continue : halt
   │                                 │
   ▼                                 ▼  VERIFY signature of bootloader
  BL (any BL)                    BL ──► signature valid? continue : halt
   │                                 │
   ▼                                 ▼  VERIFY signature of kernel
  OS (any OS — attacker wins)    Kernel ──► valid? run : halt
```

> **Principle 2.** *Secure boot transforms "run whatever is stored" into "run only what the device owner authorized." It does so by anchoring a cryptographic chain to a secret that cannot be read or changed after manufacture.*

The trust problem has exactly two components:
- **Integrity:** "Has this binary been modified?"
- **Authenticity:** "Was it created by the authorized party?"

Both are solved by asymmetric signatures: the private key signs at build time; the public key (or its hash) is burned into the device and verifies at boot time.

---

## 3. Hardware Primitives That Make Boot Possible

Boot chains depend on hardware features that software cannot replicate. Understanding these is prerequisite to understanding any platform's secure boot implementation.

### 3.1 One-Time Programmable (OTP) Fuses

OTP fuses are transistor arrays that can be irreversibly blown by passing current. Once written, they cannot be changed. They are the only place to store a value that an attacker with physical access cannot modify.

**Uses in secure boot:**
- Store the SHA-256 hash of the Root of Trust public key.
- Store the Security Version Number (SVN) for anti-rollback.
- Enable "closed" (production) mode, disabling JTAG/debug.

```
OTP Fuse Bank (logical view):
┌────────────────────────────────────────────────────────┐
│  [0x00–0x07]  SRK Hash (SHA-256 of Super Root Key)    │
│  [0x08]       Boot Configuration (boot device select) │
│  [0x09]       Security Config (JTAG disable, etc.)    │
│  [0x0A–0x0B]  Secure Boot Enable                      │
│  [0x10–0x13]  Manufacturing Protection Key            │
└────────────────────────────────────────────────────────┘
     All fields: write-once, read-many (or read-never for keys)
```

### 3.2 Hardware Secure Element / Crypto Accelerator

Most SoCs include a hardware cryptographic accelerator (e.g., CAAM on NXP i.MX, SE050 as external, CryptoCell on Nordic). This provides:
- AES/RSA/ECC operations that are faster than software.
- Isolation: private keys can be stored in the hardware and used without being exposed to software.
- Hardware-backed random number generation (TRNG).

### 3.3 Secure RAM (OCRAM with ECC)

On-chip SRAM used by early boot stages often has Error Correcting Code (ECC) to detect fault injection attacks that try to flip bits during signature verification.

### 3.4 Boot Device Strapping

The ROM reads GPIO or eFuse "boot mode" pins at reset to determine where to find Stage 1 (eMMC, SD, SPI NOR, USB, UART). This strapping is fixed at power-on and cannot be changed by software during that boot session.

| Primitive | Provides | Cannot Provide |
|-----------|----------|----------------|
| OTP fuse | Immutable storage | Confidentiality (readable) |
| Crypto HW | Speed + key isolation | Key generation policy |
| Secure RAM | Integrity under fault | Defense against SW bugs |
| Boot strapping | Fixed boot source | Authentication |

> **Principle 3.** *No software-only mechanism can establish a root of trust. Trust must be anchored in hardware that is immutable after manufacture.*

---

# Part II — The Boot Chain

## 4. Stage 0: The ROM (Immutable Trust Anchor)

The BootROM is vendor-written code burned into the SoC at fabrication. It is the **only** component that is unconditionally trusted because it is physically unmodifiable.

### What the ROM Does

```
CPU Reset Vector (e.g., 0xFFFF0000 on ARM, or mapped to ROM)
        │
        ▼
  ┌─────────────────────────────────────────────┐
  │  1. Minimal clock/PLL init                  │
  │  2. Read boot mode straps                   │
  │  3. Initialize boot interface               │
  │     (eMMC: send CMD0/CMD1; SPI: setup;      │
  │      SD: enumerate; NAND: read ID)           │
  │  4. Load Stage 1 binary into SRAM           │
  │  5. [If secure boot fused]: verify HAB/AHAB │
  │  6. Jump to Stage 1 entry point             │
  └─────────────────────────────────────────────┘
```

### ROM Limitations (By Design)

- No DDR access — only SRAM.
- No filesystem understanding — reads raw sectors at fixed offsets.
- No user interface — it is not configurable in the field.
- Fixed timeout behavior — if it cannot find a valid image, it falls through to recovery (e.g., USB serial download mode).

### ARM Boot ROM Specifics

On ARMv8 systems, the reset vector is at `0x0` (or mapped via RVBAR register). The CPU starts in EL3 (Exception Level 3, highest privilege). The ROM runs at EL3 and, depending on the platform, may hand off at EL3 (to ATF BL1) or drop to EL2 before jumping.

```
ARMv8 Exception Levels at Reset:
┌────────────────────────────────────────┐
│  EL3  Secure Monitor  ← CPU starts here│
│  EL2  Hypervisor                        │
│  EL1  OS Kernel                         │
│  EL0  User Space                        │
└────────────────────────────────────────┘
The boot chain progressively establishes
and then drops privilege levels.
```

> **Principle 4.** *The ROM is the only stage that has unconditional trust because it has no update path. Every other stage derives its authority from being verified by the ROM, directly or transitively.*

### ROM Image Formats

The ROM expects Stage 1 in a specific format (vendor-defined). Common examples:

| Platform | ROM Expects | Key Fields |
|----------|------------|------------|
| NXP i.MX6/7 | IVT + DCD (Image Vector Table + Device Config Data) | Plugin flag, entry point, self pointer |
| NXP i.MX8 | Container Image (AHAB) | Signature block, IVT, DCD |
| TI OMAP/AM | GP/HS header | Load address, size, checksum |
| Allwinner | eGON header | Magic `eGON.BT0`, entry, size |
| Raspberry Pi | `bootcode.bin` parsed by GPU | Proprietary |

---

## 5. Stage 1: SPL / First-Stage Loader

### Why SPL Exists

The constraint: SRAM ≈ 32–512 KB. U-Boot proper ≈ 1–2 MB. The SPL (Secondary Program Loader) is a stripped version of U-Boot that fits in SRAM and has one job: bring up DDR, then load the full bootloader.

```
SRAM (e.g., 256 KB on i.MX6)
┌────────────────────────────────────────┐
│  SPL binary (< SRAM size)             │
│  ├── Minimal board init               │
│  ├── DDR PHY initialization           │
│  ├── DDR training (Write leveling,    │
│  │   Read gate training, etc.)         │
│  ├── Storage driver (eMMC/SD/SPI)     │
│  └── Load u-boot.img → DDR           │
│        then jump to U-Boot entry      │
└────────────────────────────────────────┘
```

### DDR Training

DDR training is the most critical and complex task of Stage 1. Modern LPDDR4/5 runs at 3200–6400 MT/s. At these speeds, signal timing margins are measured in picoseconds. Training is the process of measuring and compensating for per-board, per-temperature signal delays.

```
DDR Training Sequence (simplified):
  1. Write Leveling     — align DQ to DQS write timing
  2. Read Gate Training — find valid read window for DQS
  3. Read Bit Deskew    — align individual data bits
  4. Write Bit Deskew   — compensate write bit delays
  5. VREF Training      — optimize voltage reference

Failure at any step → DDR unusable → system cannot boot.
```

**SPL in U-Boot build:**

```makefile
# In defconfig (e.g., imx6q_sabresd_defconfig):
CONFIG_SPL=y                    # Enable SPL build
CONFIG_SPL_TEXT_BASE=0x00908000 # SRAM load address
CONFIG_SPL_STACK=0x0091FFB8     # Top of SRAM stack
CONFIG_SPL_MMC_SUPPORT=y        # SPL needs eMMC driver
CONFIG_SPL_FIT_SUPPORT=y        # Verify FIT image signatures in SPL
```

### SPL and Secure Boot

In a secure boot chain, the SPL is the first software stage whose signature the ROM verifies. After the SPL passes ROM verification, *it* must verify the Stage 2 bootloader before jumping to it. This is called **Measured Boot** or **Verified Boot** at the SPL level.

```c
/* Minimal SPL verification call (U-Boot SPL fit_image_verify) */
int spl_load_simple_fit(struct spl_image_info *spl_image,
                         struct spl_load_info *info, ulong sector,
                         void *fit)
{
    /* ... load fit image from storage ... */
    
    /* verify_required: 1 = mandatory, 0 = optional */
    if (fit_image_verify_required_sigs(fit, &required_keynode,
                                        &err_msg))
        panic("SPL: FIT image signature check failed: %s\n", err_msg);
    
    spl_image->entry_point = fit_image_get_entry(fit, ...);
    /* jump performed by caller */
}
```

> **Principle 5.** *SPL is not a simplification of U-Boot — it is a separate trust boundary. Its size constraint exists because on-chip SRAM is the last memory the system can trust before DDR is trained and verified.*

---

## 6. Stage 2: The Full Bootloader (U-Boot, Barebox, GRUB)

### 6.1 U-Boot Architecture

U-Boot is the dominant embedded bootloader. Its architecture reflects a tension between flexibility and security.

```
U-Boot Internal Architecture:
┌─────────────────────────────────────────────────────────────────┐
│  Board Init (board_init_f → board_init_r)                       │
│  ├── Relocation (U-Boot copies itself to top of RAM)            │
│  ├── Console init (UART)                                        │
│  └── Driver Model (DM) device tree binding                      │
├─────────────────────────────────────────────────────────────────┤
│  Command Shell (optional — disabled in production)              │
│  └── Commands: bootm, booti, bootz, tftpboot, mmc, nand...     │
├─────────────────────────────────────────────────────────────────┤
│  Boot Logic                                                     │
│  ├── bootcmd environment variable (boot script)                 │
│  ├── distro_bootcmd (automatic boot from standard paths)        │
│  └── EFI stub support (optional)                               │
├─────────────────────────────────────────────────────────────────┤
│  Image Loading                                                  │
│  ├── Legacy uImage (mkimage format)                             │
│  └── FIT Image (Flattened Image Tree — supports signatures)     │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 FIT Images — The Signing Container

FIT (Flattened Image Tree) is U-Boot's cryptographically-aware image format. It is a Device Tree Source (DTS) file that bundles kernel, DTB, and initrd with hashes and signatures.

```dts
/* u-boot.its — Image Tree Source for a signed FIT */
/dts-v1/;

/ {
    description = "Production kernel image";
    #address-cells = <1>;

    images {
        kernel@1 {
            description = "Linux Kernel";
            data = /incbin/("./zImage");   /* binary included at build time */
            type = "kernel";
            arch = "arm";
            os = "linux";
            compression = "none";
            load = <0x80008000>;           /* DDR load address */
            entry = <0x80008000>;          /* kernel entry point */
            hash@1 {
                algo = "sha256";           /* integrity hash */
            };
        };
        fdt@1 {
            description = "Device Tree";
            data = /incbin/("./my-board.dtb");
            type = "flat_dt";
            arch = "arm";
            compression = "none";
            hash@1 { algo = "sha256"; };
        };
    };

    configurations {
        default = "conf@1";
        conf@1 {
            description = "Boot configuration";
            kernel = "kernel@1";
            fdt = "fdt@1";
            signature@1 {
                algo = "sha256,rsa2048";   /* hash + asymmetric algo */
                key-name-hint = "dev-key"; /* key name (matches .key file) */
                sign-images = "kernel", "fdt"; /* what is signed */
            };
        };
    };
};
```

**Build and sign the FIT:**
```bash
# 1. Generate RSA key pair (once, stored securely)
openssl genrsa -out dev-key.key 2048
openssl req -batch -new -x509 -key dev-key.key -out dev-key.crt

# 2. Build FIT image (unsigned)
mkimage -f u-boot.its fit-unsigned.itb

# 3. Sign FIT image (embeds signature; public key goes into U-Boot DTB)
mkimage -F -k ./keys/ -K u-boot.dtb -r fit-unsigned.itb fit-signed.itb
#       │   │           │              │
#       │   │           │              └─ input unsigned FIT
#       │   │           └─ required: embed public key into U-Boot's own DTB
#       │   └─ key directory
#       └─ modify in place (sign)
```

### 6.3 Environment Variables and Boot Scripts

U-Boot's `bootcmd` is evaluated at boot. In production, it should be locked down:

```bash
# Minimal hardened bootcmd (in environment or hardcoded via CONFIG_BOOTCOMMAND):
setenv bootcmd 'mmc dev 0; fatload mmc 0:1 ${loadaddr} fit-signed.itb; bootm ${loadaddr}#conf@1'

# bootm performs FIT signature verification before jumping to kernel.
# If verification fails, bootm aborts.
```

**Critical production settings (defconfig):**
```makefile
CONFIG_ENV_IS_IN_MMC=y            # Store env in eMMC
CONFIG_ENV_OVERWRITE=n            # Prevent env overwrite from shell
CONFIG_BOOTDELAY=-2               # Disable countdown (no autoboot interrupt)
CONFIG_CMD_SHELL=n                # Disable interactive shell in production
CONFIG_CMDLINE_EDITING=n          # Remove editing capability
CONFIG_FIT_SIGNATURE=y            # Enable FIT signature verification
CONFIG_RSA=y                      # Enable RSA (required for sig verification)
CONFIG_SHA256=y
CONFIG_OF_CONTROL=y               # Use DT for U-Boot config
CONFIG_DEFAULT_DEVICE_TREE="my-board-uboot" # Which DTB contains public key
```

> **Principle 6.** *U-Boot's interactive shell is a development convenience and a production liability. Any bootloader feature that is not required for the production boot path must be compiled out, not just disabled.*

### 6.4 Barebox

Barebox is an alternative to U-Boot with a cleaner internal architecture (closer to Linux kernel style) and first-class Device Tree support throughout. It uses "bootspec" and has built-in support for verified boot via its `blobgen` subsystem.

| Feature | U-Boot | Barebox |
|---------|--------|---------|
| Architecture | Monolithic | More modular (DM-like from start) |
| Shell | hush shell | bash-like shell with tab completion |
| Signing | FIT images | `blobgen` + signed images |
| Adoption | Very wide | Strong in automotive/industrial |
| UEFI support | Partial | Via EFI app layer |

---

## 7. Stage 3: The Kernel Handoff

### What the Bootloader Provides to the Kernel

The bootloader's final act is to set up a correct handoff environment. On ARM64 (the dominant embedded architecture), the contract is:

```
Kernel Handoff Contract (ARM64 / arm64 boot protocol):
┌─────────────────────────────────────────────────────────┐
│  x0  = Physical address of Device Tree Blob (DTB)       │
│  x1  = 0 (reserved)                                    │
│  x2  = 0 (reserved)                                    │
│  x3  = 0 (reserved)                                    │
│  MMU = OFF                                              │
│  Caches = OFF                                           │
│  Interrupts = DISABLED                                  │
│  EL = EL2 (if virtualization present) else EL1         │
│  CPU = primary CPU only (secondaries held in WFE)       │
└─────────────────────────────────────────────────────────┘
```

**U-Boot `booti` command (ARM64):**
```bash
# Load kernel at $kernel_addr_r, DTB at $fdt_addr_r
booti ${kernel_addr_r} - ${fdt_addr_r}
#     │                 │  └─ DTB physical address → goes in x0
#     │                 └─ '-' means no initrd
#     └─ kernel Image start address
```

### Device Tree Blob (DTB)

The DTB is a binary encoding of the hardware description. The bootloader may:
1. Pass the vendor-provided DTB unchanged.
2. Overlay user-provided DT overlays (`fdtoverlay`).
3. Dynamically patch the DTB (e.g., insert MAC addresses, memory size).

```bash
# U-Boot DTB patching example:
fdt addr ${fdt_addr_r}                          # point fdt commands at loaded DTB
fdt resize 4096                                  # ensure space for new nodes
fdt set /ethernet0 local-mac-address ${eth_mac} # patch in board-specific MAC
```

> **Principle 7.** *The DTB is the contract between bootloader and kernel. The bootloader owns the DTB at handoff time and may modify it; the kernel trusts it completely. In a secure boot chain, the DTB must be signed alongside the kernel.*

---

# Part III — Secure Boot Architecture

## 8. Cryptographic Foundations

### 8.1 Hash Functions

A cryptographic hash function H maps arbitrary-length input to fixed-length output with three properties:
- **Pre-image resistance:** Given H(m), it is infeasible to find m.
- **Second pre-image resistance:** Given m, it is infeasible to find m' ≠ m with H(m) = H(m').
- **Collision resistance:** It is infeasible to find any m, m' with H(m) = H(m').

**Relevant algorithms in embedded secure boot:**

| Algorithm | Output | Status | Use |
|-----------|--------|--------|-----|
| SHA-1 | 160 bits | Deprecated | Legacy only |
| SHA-256 | 256 bits | Current standard | Signature hash, OTP key hash |
| SHA-384 | 384 bits | Current | High-security applications |
| SHA-512 | 512 bits | Current | Future-proofing |

### 8.2 Asymmetric Signatures

RSA and ECC provide the asymmetric primitive used in all practical secure boot implementations.

**RSA signature (signing):**
```
signature = RSASSA-PKCS1-v1_5(privateKey, SHA256(message))
          = privateKey ^ d mod N  (where d is private exponent)
```

**RSA signature (verification):**
```
valid = (publicKey ^ e mod N) == SHA256(message)
```

**ECC (ECDSA) — increasingly preferred for embedded:**
- RSA-2048 signature: 256 bytes, key: 256 bytes.
- ECDSA P-256 signature: 64 bytes, key: 32 bytes.
- Smaller keys = less OTP fuse space, faster verification.

**Embedded-relevant key sizes:**

| Algorithm | Key Size | Security Level | Verification Cost |
|-----------|----------|---------------|-----------------|
| RSA-2048 | 2048 bits | 112-bit | ~10ms (SW), <1ms (HW) |
| RSA-4096 | 4096 bits | 140-bit | ~50ms (SW), <5ms (HW) |
| ECDSA P-256 | 256 bits | 128-bit | ~5ms (SW), <1ms (HW) |
| Ed25519 | 256 bits | 128-bit | ~2ms (SW) |

### 8.3 Certificate vs. Raw Public Key

Secure boot does **not** require X.509 certificates. The OTP stores the hash of a raw public key (or key set). Certificates add PKI infrastructure useful for field key rotation; in the minimal case, a burned public key hash is sufficient.

```
Minimal Secure Boot Cryptographic Protocol:

BUILD TIME:
  sign(firmware_binary, private_key) → signature
  embed(firmware_binary, signature)  → signed_firmware

BOOT TIME:
  hash(public_key)                   → computed_hash
  burned_hash = read_OTP()
  assert(computed_hash == burned_hash)  # key authenticity
  verify(firmware_binary, signature, public_key)  # image integrity+authenticity
```

> **Principle 8.** *Secure boot does not require a PKI. It requires exactly one asymmetric keypair: the private key signs at build time; the hash of the public key is the root of trust burned into OTP. Everything else is key management infrastructure layered on top.*

---

## 9. The Chain of Trust: Formal Model

### Definition

A **Chain of Trust** is a sequence of verification steps V₀, V₁, ..., Vₙ where:
- V₀ is performed by hardware (ROM) using an immutable key.
- Vᵢ is performed by stage i using a key whose validity was established by Vᵢ₋₁.
- Each Vᵢ verifies the integrity and authenticity of the binary that will perform Vᵢ₊₁.

```
Chain of Trust (formal):

  OTP[SRK_hash]                         (burned at manufacture, immutable)
       │
       ▼ ROM verifies hash(SRK_pub) == OTP[SRK_hash]
  SRK_pub ──sign──► SPL_image
       │
       ▼ ROM verifies SPL_image with SRK_pub
  [SPL runs]
       │
       ▼ SPL verifies U-Boot image with (key embedded in SPL or derived from SRK)
  [U-Boot runs]
       │
       ▼ U-Boot verifies Kernel FIT with (key in U-Boot DTB)
  [Kernel runs]
       │
       ▼ (Optional) dm-verity verifies rootfs block-by-block
  [Rootfs mounted read-only]
```

### Properties a Valid Chain Provides

| Property | Mechanism |
|----------|-----------|
| **Integrity** | Cryptographic hash mismatch causes boot halt |
| **Authenticity** | Signature verification confirms authorized origin |
| **Non-repudiation** | Private key holder is the only party that can produce valid images |
| **Anti-downgrade** | Version counter in OTP prevents reverting to older (vulnerable) firmware |

### Where Chains Break

A chain is only as strong as its weakest link. Common weaknesses:

```
Broken chain scenarios:

  ✓  ROM → SPL (signed)
  ✗  SPL → U-Boot (unsigned — SPL does NOT verify U-Boot)
      ↑
      ATTACKER can replace U-Boot here.
      Once U-Boot runs, the rest of the chain is irrelevant.
```

Every stage that does not verify the next stage terminates the chain at that point.

> **Principle 9.** *A Chain of Trust that is broken at any link provides no security guarantee for any subsequent stage, regardless of what those stages verify themselves.*

---

## 10. Key Hierarchy and OTP Fuses

### Key Hierarchy

Production secure boot uses a hierarchy, not a single key, to enable key management operations without burning new fuses.

```
Key Hierarchy:

  Super Root Key (SRK) — MOST SENSITIVE
  ├── Stored: HSM (Hardware Security Module) at factory
  ├── Purpose: Sign all other keys (or sign firmware directly)
  └── Backup: Geographically distributed, M-of-N threshold

  Image Signing Key (ISK) — OPERATIONAL
  ├── Derived from / certified by SRK
  ├── Stored: CI/CD build system (HSM or encrypted store)
  └── Purpose: Sign production firmware images daily

  Debug/Development Key — LEAST SENSITIVE
  ├── Separate key pair for development hardware
  ├── Stored: Developer machines / version control
  └── Purpose: Sign dev builds; NEVER burned in production OTP
```

### OTP Fuse Programming

Fuses are programmed once. The process is irreversible. All platforms provide:
- A programming tool (e.g., `fuse prog` in U-Boot, `imx-otp-program`, eFUSE CLI).
- A verification step (read back and compare).
- A "lock" step that prevents further writes to sensitive fuse regions.

**NXP i.MX6 example — program SRK hash:**
```bash
# In U-Boot (development phase — fuse commands enabled):
# SRK hash is 256 bits = 8 × 32-bit words

# Read the SRK hash from the CST tool output (srk_hash.txt)
# Example: 0x12345678 0x9ABCDEF0 ...

fuse prog -y 3 0 0x12345678   # bank 3, word 0
fuse prog -y 3 1 0x9ABCDEF0   # bank 3, word 1
# ... (words 2-7)

# Enable secure boot (HAB):
fuse prog -y 0 6 0x00000002   # SEC_CONFIG[1] = 1

# VERIFY before enabling (read back):
fuse read 3 0 8               # read 8 words from bank 3, word 0
```

> **Principle 10.** *OTP fuses must be programmed in order: key hash first, lock bits last, security-enable last of all. Reversing this order risks enabling secure boot before the key is programmed, which permanently bricks the device.*

---

## 11. Image Signing Workflows

### 11.1 NXP Code Signing Tool (CST) Workflow

```
NXP HAB Signing Workflow:

  ┌─────────────────────────────────────────────────────────────┐
  │  Key Generation (once, offline)                             │
  │  $ cst --o srk_table.bin --srk_ca_key srk_ca_key.pem ...   │
  └─────────────────────┬───────────────────────────────────────┘
                        │
  ┌─────────────────────▼───────────────────────────────────────┐
  │  Build U-Boot/SPL (standard build)                          │
  │  $ make imx6q_sabresd_defconfig && make                     │
  └─────────────────────┬───────────────────────────────────────┘
                        │
  ┌─────────────────────▼───────────────────────────────────────┐
  │  Create CSF (Command Sequence File)                         │
  │  Specifies: which files, which keys, HAB commands           │
  └─────────────────────┬───────────────────────────────────────┘
                        │
  ┌─────────────────────▼───────────────────────────────────────┐
  │  Run CST                                                    │
  │  $ cst -i u-boot.csf -o u-boot_csf.bin                     │
  │  Produces: signed binary with embedded signature block      │
  └─────────────────────┬───────────────────────────────────────┘
                        │
  ┌─────────────────────▼───────────────────────────────────────┐
  │  Verify (optional, before flashing)                         │
  │  $ hab_log: check_status in U-Boot with hab_status command  │
  └─────────────────────────────────────────────────────────────┘
```

**Minimal CSF file:**
```
[Header]
    Version = 4.2
    Hash Algorithm = sha256
    Engine = CAAM
    Engine Configuration = 0
    Certificate Format = X509
    Signature Format = CMS

[Install SRK]
    File = "srk_table.bin"
    Source index = 0      # which SRK key (0-3)

[Install CSFK]
    File = "csfk.pem"     # CSF signing key (signed by SRK)

[Authenticate CSF]        # self-authenticating

[Install Key]
    File = "imgk.pem"     # Image key (signed by CSFK)
    Verification index = 2

[Authenticate Data]       # THIS is what verifies U-Boot binary
    Verification index = 2
    Blocks = 0x877FF400 0x00 0x000C1000 "u-boot-dtb.imx"
    #        load_addr  offset  size      file
```

### 11.2 U-Boot FIT Signing Workflow

```bash
#!/bin/bash
# Minimal FIT signing script

KEY_DIR="./keys"
ITS_FILE="kernel.its"
OUTPUT_FIT="kernel-signed.itb"
UBOOT_DTB="u-boot.dtb"   # Public key will be embedded here

# Step 1: Generate keys (once)
mkdir -p ${KEY_DIR}
openssl genrsa -out ${KEY_DIR}/kernel-signing.key 2048
openssl req -new -x509 -key ${KEY_DIR}/kernel-signing.key \
    -out ${KEY_DIR}/kernel-signing.crt \
    -subj "/CN=Kernel Signing Key/"

# Step 2: Build FIT and sign
mkimage -f ${ITS_FILE} -k ${KEY_DIR} \
        -K ${UBOOT_DTB} \    # embed public key into U-Boot DTB
        -r ${OUTPUT_FIT}     # -r = required signature (verification is mandatory)

# Step 3: Verify (optional, local check)
fit_check_sign -f ${OUTPUT_FIT} -k ${UBOOT_DTB}
```

> **Principle 11.** *Image signing must be integrated into the CI/CD pipeline, not a manual post-build step. Any build that can produce unsigned firmware for production is a security defect.*

---

# Part IV — Platform Implementations

## 12. ARM TrustZone and OP-TEE

### What TrustZone Is

TrustZone is an ARM hardware security extension that partitions the SoC into two worlds: **Secure** and **Non-Secure**. This partitioning is enforced in hardware — the Non-Secure world cannot access Secure world memory regardless of software privilege level.

```
ARM TrustZone World Model:

  Non-Secure World (Normal World)    Secure World
  ┌────────────────────────────┐    ┌──────────────────────────────┐
  │  EL0: Linux User Space     │    │  S-EL0: Trusted Applications  │
  │  EL1: Linux Kernel         │    │  S-EL1: OP-TEE OS             │
  │  EL2: Hypervisor (opt.)    │    │  EL3:  Secure Monitor (ATF)  │
  └────────────────────────────┘    └──────────────────────────────┘
           │                                    │
           └──────────── SMC ────────────────►  │
                    (Secure Monitor Call)
```

**NS bit:** Every memory transaction carries a Non-Secure (NS) bit. Secure world can access NS memory; NS world cannot access Secure memory. This is enforced by the TrustZone Address Space Controller (TZASC) at the bus level.

### ARM Trusted Firmware (ATF/TF-A)

ATF (Trusted Firmware for ARM, now TF-A) implements the Secure Monitor at EL3 and defines the **Trusted Board Boot Requirements (TBBR)** — the ARM-standard chain of trust.

```
ATF Boot Flow (BL1 → BL2 → BL31 → BL33):

  ROM/BootROM
       │ loads
       ▼
  BL1 (Boot Loader stage 1) — runs in ROM or SRAM
  │   ■ CPU arch init, exception vectors
  │   ■ Loads and authenticates BL2
       │ loads+verifies
       ▼
  BL2 (Boot Loader stage 2) — runs in Secure SRAM
  │   ■ Platform security init
  │   ■ Loads and verifies BL31, BL32, BL33
  │   ■ Configures TZASC memory partitioning
       │ transfers to
       ▼
  BL31 (EL3 Runtime Firmware) — resident, handles SMC calls
  │   ■ PSCI (Power State Coordination Interface)
  │   ■ SMC dispatcher
       │ +
  BL32 (Secure Payload — OP-TEE) — optional
       │
  BL33 (Non-Trusted Firmware = U-Boot or UEFI) — runs at EL2/EL1
       │ boots
       ▼
  Linux Kernel
```

**ATF TBBR authentication — `auth_mod.c` concept:**
```c
/*
 * ATF authentication framework (simplified).
 * Each image descriptor specifies: what it is, how to verify it.
 */
static const auth_img_desc_t bl2_image = {
    .img_id = BL2_IMAGE_ID,
    .img_type = IMG_BOOT,
    .parent = &trusted_boot_fw_cert,  /* verified by this certificate */
    .img_auth_methods = {
        [0] = {
            .type = AUTH_METHOD_SIG,       /* RSA/ECC signature */
            .param.sig = {
                .pk   = &subject_pk,
                .sig  = &sig,
                .alg  = &sig_alg,
                .data = &raw_data,
            },
        },
    },
};
```

> **Principle 12.** *TrustZone does not make code secure — it creates an isolated execution environment in which secure code can run. The security of the Secure World depends entirely on what software runs there and how it handles the boundary.*

### OP-TEE

OP-TEE (Open Portable Trusted Execution Environment) is the reference Secure OS for the TrustZone Secure World. Trusted Applications (TAs) run in S-EL0 and are invoked from Linux via the `/dev/tee0` device.

```bash
# OP-TEE Trusted Application invocation (from Linux):
# Uses Global Platform TEE Client API

tee-supplicant &         # userspace daemon required for OP-TEE
# TA loading, file access go through supplicant

# Typical TA call (from C, using optee-client library):
TEEC_Context ctx;
TEEC_Session sess;
TEEC_UUID uuid = TA_SECURE_STORAGE_UUID;
TEEC_InitializeContext(NULL, &ctx);
TEEC_OpenSession(&ctx, &sess, &uuid, TEEC_LOGIN_PUBLIC, NULL, NULL, &err);
/* ... invoke TA commands ... */
```

---

## 13. NXP HABv4 / AHAB

### HABv4 (High Assurance Boot, version 4)

HABv4 is NXP's secure boot implementation for i.MX6/7/8M family. It operates as a library within the ROM.

```
HABv4 Boot Flow:

  Power On
     │
     ▼
  ROM reads IVT (Image Vector Table) from eMMC/SD offset
     │
     ▼  [if SEC_CONFIG fuse = 0x3 → "Closed" = secure boot mandatory]
  ROM calls HAB API: hab_rvt_authenticate_image()
     │
     ▼
  HAB validates CSF (Command Sequence File) embedded in image:
  ├── Authenticate SRK table against OTP hash
  ├── Install CSF key (certified by SRK)
  ├── Authenticate image data (U-Boot binary)
  └── Return: HAB_SUCCESS or halt
     │
     ▼ (only on HAB_SUCCESS)
  ROM jumps to IVT entry point
```

**HAB Event Log (diagnostic — in U-Boot):**
```bash
# Check HAB status after boot (critical for validation):
=> hab_status

Secure boot disabled

HAB Configuration: 0xf0, HAB State: 0x66
No HAB Events Found!

# In closed board with valid signature, you see:
HAB Configuration: 0xcc, HAB State: 0x99
No HAB Events Found!

# With signature failure, HAB logs an event:
HAB Event 1:
        event data:
                0xdb 0x00 0x1c 0x42  ... (error codes)
        STS = HAB_FAILURE (0x33)
        RSN = HAB_INV_SIGNATURE (0x18)
```

### AHAB (Advanced High Assurance Boot)

AHAB is NXP's next-generation secure boot for i.MX8/i.MX9. Key differences from HABv4:

| Feature | HABv4 | AHAB |
|---------|-------|------|
| Architecture | Single-core ARM | Multi-core (A-core + M-core) |
| Container | IVT + DCD | Container Image (multiple sub-images) |
| Crypto | RSA-2048/4096 | RSA + ECC |
| Key Management | SRK table (4 keys) | More flexible |
| Scope | Boot ROM only | Covers multiple subsystem boots |

---

## 14. Raspberry Pi Secure Boot

The Raspberry Pi (BCM2xxx) has an unusual architecture: the GPU (VideoCore) boots first and is the actual "host" that starts the ARM core.

```
Raspberry Pi Boot Order:
  ┌──────────────────────────────────────────────────────┐
  │  GPU (VideoCore) — runs first, always                 │
  │  ├── Reads OTP for boot device/order                 │
  │  ├── Loads bootcode.bin (Pi 3) or from EEPROM (Pi 4)│
  │  └── Loads start.elf (GPU firmware)                  │
  └──────────────────────────────────────────────────────┘
                     │
                     ▼ GPU initializes, then starts ARM
  ┌──────────────────────────────────────────────────────┐
  │  ARM Core (starts here, after GPU init)              │
  │  ├── u-boot.bin or kernel8.img loaded by GPU         │
  │  └── Executes bootloader/kernel                      │
  └──────────────────────────────────────────────────────┘
```

**Raspberry Pi 4/CM4 Secure Boot (via RPIBOOT EEPROM):**

```bash
# Pi 4 uses EEPROM-based bootloader (rpi-eeprom)
# Secure boot requires signing the bootloader and kernel

# Generate key (RSA 2048 or 4096):
openssl genrsa -out private.pem 2048

# Sign the kernel image:
rpi-sign-image kernel8.img private.pem kernel8.img.sig

# Configure EEPROM for secure boot:
# In config.txt:
# SIGNED_BOOT=1
# PUBLIC_KEY_FILE=public.pem

# The EEPROM verifies kernel8.img against kernel8.img.sig at each boot.
```

**Limitation:** The Pi 4 secure boot does not extend to the GPU firmware (`start4.elf`). True security requires CM4 in production with locked OTP and custom firmware.

---

## 15. UEFI Secure Boot (Embedded Perspective)

UEFI Secure Boot is the dominant secure boot mechanism for x86 embedded (Intel NUC, COM Express, etc.) and is increasingly used on ARM servers and high-end embedded systems.

```
UEFI Secure Boot Database Model:
┌──────────────────────────────────────────────────────────────┐
│  PK  — Platform Key  (OEM-controlled, one key)               │
│  └── Signs updates to KEK                                    │
│                                                              │
│  KEK — Key Exchange Key (OEM + OS vendor)                    │
│  └── Signs updates to db and dbx                            │
│                                                              │
│  db  — Signature Database (trusted)                          │
│  └── Contains: certs/hashes of trusted bootloaders/OSes     │
│                                                              │
│  dbx — Forbidden Signature Database (revocation)            │
│  └── Contains: hashes of known-bad images                   │
└──────────────────────────────────────────────────────────────┘

At boot: UEFI verifies EFI application (shim/GRUB) against db.
         If in dbx → reject. If signed by db key → accept.
```

**Embedded UEFI (EDK2) secure boot configuration:**
```ini
# Example PlatformSecureLib configuration (EDK2):
# PlatformSecureLib/PlatformSecureLib.c determines if platform
# is in "setup mode" (can enroll keys) or "user mode" (keys locked).

# Enroll PK using KeyTool.efi:
# 1. Boot into UEFI shell
# 2. KeyTool.efi → Edit Keys → Allowed Signature Database (db)
# 3. Add certificate from USB
# 4. Enroll PK (this transitions to "User Mode")
# 5. From this point, only signed EFI images boot.
```

> **Principle 15.** *UEFI Secure Boot's key hierarchy (PK → KEK → db) exists to allow key rotation without requiring physical access to the device. The PK is the OEM root; KEK allows the OS vendor to add their signing certificate to db.*

---

# Part V — Production Concerns

## 16. Key Management in Manufacturing

This is the highest-risk phase of a product's security lifecycle. A key management failure at manufacturing compromises every unit ever produced.

### Threat Model at Manufacturing

```
Manufacturing Threat Model:
  ┌─────────────────────────────────────────────────────────────┐
  │  Threats:                                                   │
  │  ■ Rogue factory operator copies private key                │
  │  ■ Key transmitted unencrypted to programming station       │
  │  ■ OTP programmed with wrong hash (key mismatch → bricked) │
  │  ■ Counterfeit devices programmed with same key as originals│
  └─────────────────────────────────────────────────────────────┘
```

### Secure Manufacturing Architecture

```
Recommended Architecture:
  ┌───────────────────────────┐
  │  HSM (Hardware Security   │
  │  Module) at Factory       │◄── Private key NEVER leaves HSM
  │  ─────────────────────    │
  │  Signs device-specific    │
  │  provisioning data        │
  └──────────┬────────────────┘
             │ Signed blob (no raw key)
             ▼
  ┌───────────────────────────┐
  │  Programming Station      │
  │  ─────────────────────    │
  │  Programs OTP fuses       │
  │  Flashes signed firmware  │
  │  Runs post-program test   │
  └───────────────────────────┘
             │
             ▼
  ┌───────────────────────────┐
  │  Device Under Test        │
  │  ─────────────────────    │
  │  Boots signed firmware    │
  │  Reports HAB/AHAB status  │
  │  Closes (locks fuses)     │
  └───────────────────────────┘
```

### Fuse Programming Sequence

```
MANDATORY ORDER — never deviate:
  1. Program SRK hash (key identity)
  2. Verify SRK hash readback matches expected
  3. Program secondary fuses (lifecycle, features)
  4. Program JTAG disable fuse
  5. Program Secure Boot enable fuse  ← LAST. Once done, unsigned FW won't boot.
  6. Power cycle and verify boot with signed firmware
```

> **Principle 16.** *The private key that signs production firmware must never exist in plaintext outside an HSM. The OTP hash burned into devices is a one-way commitment to a public key. Compromise of the private key requires a hardware recall.*

---

## 17. Recovery, Rollback, and Anti-Rollback

### The Recovery Problem

Secure boot creates a tension: the device must only run authorized firmware, but what happens when the authorized firmware is broken? A device that cannot recover from a bad update is a field disaster.

### Dual-Bank (A/B) Boot

```
A/B Partition Layout (typical eMMC):
┌─────────────────────────────────────────────────────────────┐
│  Boot0 HW partition: SPL-A                                  │
│  Boot1 HW partition: SPL-B                                  │
│                                                             │
│  User partition:                                            │
│  ├── U-Boot-A (8 MB)   ├── U-Boot-B (8 MB)                │
│  ├── Kernel-A (32 MB)  ├── Kernel-B (32 MB)               │
│  ├── Rootfs-A (512 MB) ├── Rootfs-B (512 MB)              │
│  └── Data partition (shared, not part of A/B)              │
└─────────────────────────────────────────────────────────────┘

State machine:
  Current = A → try_count = 0 → boot A
  A fails → try_count++ → try_count > threshold → switch to B
  B boots successfully → B becomes "Current"
```

**U-Boot A/B implementation (Mender-style):**
```bash
# In bootcmd:
if test ${mender_boot_part} = 2; then
    setenv bootpart mmcblk0p2
else
    setenv bootpart mmcblk0p3
fi

# Try to boot:
load mmc 0:${bootpart} ${kernel_addr_r} /boot/kernel
load mmc 0:${bootpart} ${fdt_addr_r} /boot/board.dtb
setenv mender_boot_part_count $((${mender_boot_part_count} + 1))
saveenv
booti ${kernel_addr_r} - ${fdt_addr_r}
# If booti returns (kernel panicked), next reset tries the other partition.
```

### Anti-Rollback

Anti-rollback prevents an attacker from flashing an older (vulnerable) firmware version that passes signature verification (because the old key is still valid).

**Mechanism:** A **Security Version Number (SVN)** is burned into OTP fuses. The bootloader reads the SVN from the image header and refuses to boot if the image SVN < fuse SVN.

```c
/* Pseudo-code for anti-rollback check */
int verify_image_version(image_header_t *hdr) {
    uint32_t fuse_svn = read_otp_svn();
    uint32_t image_svn = hdr->security_version;
    
    if (image_svn < fuse_svn) {
        log_error("Image SVN %d < fuse SVN %d: rollback blocked",
                  image_svn, fuse_svn);
        return -EACCES;
    }
    
    /* After successful update, burn new SVN */
    if (image_svn > fuse_svn && update_confirmed()) {
        burn_otp_svn(image_svn);  /* irreversible */
    }
    return 0;
}
```

> **Principle 17.** *Anti-rollback via OTP SVN is irreversible by design. Incrementing the SVN permanently obsoletes all earlier firmware. A process to confirm successful update before incrementing SVN is mandatory — premature increment permanently removes the recovery path.*

---

## 18. Attestation and Remote Integrity Verification

### What Attestation Provides

Attestation answers the question: "Is this specific device running the authorized firmware, right now?" It extends the Chain of Trust beyond the local device to a remote verifier.

```
Remote Attestation Protocol:

  Device                          Remote Verifier
    │                                  │
    │◄─────── Challenge (nonce) ───────┤
    │                                  │
    │  Measure running components:     │
    │  ├── PCR[0] = hash(BIOS)         │
    │  ├── PCR[1] = hash(bootloader)   │
    │  ├── PCR[4] = hash(kernel)       │
    │  └── ... etc.                    │
    │                                  │
    │  Quote = sign(PCRs + nonce,      │
    │               device_key)        │
    │                                  │
    │──── Quote + Cert chain ─────────►│
    │                                  │
    │                   Verify quote sig │
    │                   Compare PCRs    │
    │                   to known-good   │
    │                   values          │
    │                                  │
    │◄──── Grant/Deny access ──────────┤
```

### TPM (Trusted Platform Module)

TPM 2.0 is the standard hardware attestation component. It provides:
- **Platform Configuration Registers (PCRs):** Extend-only registers. Each boot measurement is hashed into a PCR: PCR[n] = SHA256(PCR[n] || new_measurement).
- **Remote Attestation:** The TPM can sign PCR values with a device-unique key (AIK, Attestation Identity Key) that is certified by the TPM manufacturer.
- **Sealed Storage:** Data sealed to a PCR combination can only be unsealed if those PCRs have the expected values (i.e., only if the correct firmware booted).

**Linux TPM attestation snippet:**
```bash
# Extend PCR 8 with kernel image hash (done by bootloader or IMA):
tpm2_pcrextend 8:sha256=$(sha256sum vmlinuz | awk '{print $1}')

# Create a quote (signed PCR report):
tpm2_quote --key-context signing.ctx \
           --pcr-list sha256:0,1,4,8 \
           --qualification nonce.bin \
           --message quote.msg \
           --signature quote.sig

# Remote verifier checks quote.sig against AIK certificate.
```

> **Principle 18.** *Attestation does not prevent a compromised device from running bad firmware. It provides a mechanism for remote systems to detect and refuse service to compromised devices.*

---

## 19. Common Attack Vectors and Mitigations

### Attack Taxonomy

```
Attack Surface Map:

  ┌─────────────────────────────────────────────────────────────┐
  │  PHYSICAL ATTACKS                                          │
  │  ├── Glitching (voltage/clock fault injection)             │
  │  │     ─ Skip signature check instruction                  │
  │  ├── Cold boot / DRAM remanence                            │
  │  │     ─ Read cryptographic keys from cooled RAM           │
  │  ├── JTAG/SWD debug access                                 │
  │  │     ─ Halt CPU, read/write memory, bypass checks        │
  │  └── Side-channel (power/EM analysis)                      │
  │        ─ Extract private key from signing operation        │
  ├─────────────────────────────────────────────────────────────┤
  │  LOGICAL ATTACKS                                           │
  │  ├── Rollback (flash old vulnerable firmware)              │
  │  ├── Environment variable tampering (U-Boot env)           │
  │  ├── Race condition in signature verification              │
  │  └── Integer overflow in image length parsing              │
  ├─────────────────────────────────────────────────────────────┤
  │  SUPPLY CHAIN ATTACKS                                      │
  │  ├── Compromise CI/CD signing key                          │
  │  ├── Malicious SDK/toolchain injection                     │
  │  └── Factory key exfiltration                              │
  └─────────────────────────────────────────────────────────────┘
```

### Mitigations Table

| Attack | Mitigation | Implementation |
|--------|-----------|---------------|
| Voltage glitching | Hardware glitch detector | Enable SoC glitch sensor (e.g., NXP PTA) |
| JTAG access | Disable JTAG via fuse | `SEC_CONFIG[JTAG_SMODE] = 0x3` in OTP |
| Cold boot | Memory encryption | i.MX8: CAAM BEE, Qualcomm: SCM with inline encryption |
| Rollback | Anti-rollback SVN in OTP | See §17 |
| Env tampering | Signed environment | U-Boot `CONFIG_ENV_SIG=y` + sign env with image key |
| Buffer overflow in loader | Stack canaries, bounds checks | Enable in SPL/U-Boot build: `-fstack-protector-strong` |
| Key compromise | Key rotation without recall | Multi-key SRK table (HABv4 supports 4 SRK slots) |
| Debug backdoor | Remove all debug interfaces | `CONFIG_CMD_SHELL=n`, `CONFIG_DEBUG_UART=n` in production |

### The TOCTOU Problem in Boot Verification

A critical implementation error: measuring the image *before* loading it into RAM, then executing a *different* copy.

```
TOCTOU (Time-of-Check vs Time-of-Use) Attack:

  WRONG:
    1. ROM copies image to SRAM
    2. ROM verifies image in SRAM ← check
    3. Attacker via DMA modifies image in SRAM
    4. ROM jumps to SRAM ← use (different content!)
  
  CORRECT:
    1. ROM copies image to SRAM
    2. ROM disables DMA to SRAM
    3. ROM verifies image in SRAM ← check
    4. ROM jumps to SRAM ← use (same content guaranteed)
```

> **Principle 19.** *Signature verification and execution must be atomic with respect to the verified memory region. Any mechanism that allows the memory to change between verification and execution renders the verification useless.*

---

# Appendices

## A — Glossary

| Term | Definition |
|------|-----------|
| **ATF / TF-A** | ARM Trusted Firmware (now Trusted Firmware-A). Reference implementation of Secure Monitor for ARMv8. |
| **AHAB** | Advanced High Assurance Boot. NXP's next-generation secure boot for i.MX8/9. |
| **BL1/2/31/32/33** | ATF boot stage nomenclature. BL33 is typically U-Boot or UEFI. |
| **Chain of Trust** | Sequence of cryptographic verifications from immutable hardware to running OS. |
| **CSF** | Command Sequence File. NXP HAB descriptor of what to sign and how. |
| **DTB** | Device Tree Blob. Binary representation of hardware topology passed to kernel. |
| **EL0–EL3** | ARMv8 Exception Levels. EL3 = highest privilege (Secure Monitor). |
| **eFuse / OTP** | One-Time Programmable storage. Irreversibly burned bits for key hashes, config. |
| **FIT** | Flattened Image Tree. U-Boot's image format supporting cryptographic signatures. |
| **HABv4** | High Assurance Boot version 4. NXP's secure boot for i.MX6/7/8M. |
| **HSM** | Hardware Security Module. Tamper-resistant device for cryptographic key storage and operations. |
| **IVT** | Image Vector Table. NXP ROM-required header structure at fixed offset in boot image. |
| **JTAG** | Joint Test Action Group. Debug interface for embedded CPUs; must be disabled in production. |
| **OTP** | One-Time Programmable. Synonym for eFuse. |
| **PCR** | Platform Configuration Register. TPM register that accumulates boot measurements. |
| **PSCI** | Power State Coordination Interface. ARM standard for CPU power management, implemented in BL31. |
| **OP-TEE** | Open Portable Trusted Execution Environment. Reference Secure OS for TrustZone. |
| **SRK** | Super Root Key. Topmost key in NXP HAB/AHAB hierarchy; hash burned in OTP. |
| **SPL** | Secondary Program Loader. Small first-stage U-Boot that fits in on-chip SRAM. |
| **SVN** | Security Version Number. Monotonic counter for anti-rollback, stored in OTP. |
| **TBBR** | Trusted Board Boot Requirements. ARM specification defining standard boot chain with authentication. |
| **TOCTOU** | Time-of-Check vs Time-of-Use. Race condition where checked value differs from used value. |
| **TPM** | Trusted Platform Module. Standardized security chip providing attestation and sealed storage. |
| **TrustZone** | ARM hardware extension partitioning SoC into Secure and Non-Secure worlds. |
| **TZASC** | TrustZone Address Space Controller. Bus-level enforcer of Secure/Non-Secure memory partitioning. |

---

## B — Key Variables and Constants to Memorize

### Critical Addresses (i.MX6 example — verify for your platform)

| Symbol | Address | Description |
|--------|---------|-------------|
| `ROM_BASE` | `0x00000000` | ROM start (may be aliased) |
| `OCRAM_BASE` | `0x00900000` | On-chip SRAM (256 KB on i.MX6) |
| `SPL_TEXT_BASE` | `0x00908000` | SPL load address in OCRAM |
| `CONFIG_SYS_TEXT_BASE` | `0x17800000` | U-Boot load address in DDR |
| `IVT_OFFSET_SD` | `0x400` | IVT offset in SD/MMC boot image |
| `IVT_OFFSET_NOR` | `0x1000` | IVT offset in SPI NOR boot image |

### Key OTP Fuse Banks (NXP i.MX6)

| Bank | Word | Field | Effect |
|------|------|-------|--------|
| 0 | 6 | `SEC_CONFIG[1:0]` | `0x3` = Closed (secure boot mandatory) |
| 0 | 6 | `DIR_BT_DIS` | `1` = Disable direct external boot |
| 3 | 0–7 | `SRK_HASH[255:0]` | SHA-256 of SRK table |
| 0 | 5 | `BOOT_CFG1[7:4]` | Boot device selection |

### U-Boot Critical Config Options

| Config | Effect |
|--------|--------|
| `CONFIG_FIT_SIGNATURE=y` | Enable FIT signature verification |
| `CONFIG_RSA=y` | RSA library (required for FIT sig) |
| `CONFIG_BOOTDELAY=-2` | Disable autoboot countdown entirely |
| `CONFIG_CMD_SHELL=n` | Remove interactive shell |
| `CONFIG_ENV_IS_NOWHERE=y` | No persistent env (safest for production) |
| `CONFIG_SPL_FIT_SIGNATURE=y` | FIT signature check in SPL |

---

## C — Comparative Platform Table

| Platform | ROM Auth | Stage 1 | Stage 2 | Secure World | Attestation |
|----------|---------|---------|---------|--------------|-------------|
| NXP i.MX6 | HABv4 | SPL | U-Boot | OP-TEE + ATF | External TPM |
| NXP i.MX8 | AHAB | SPL | U-Boot | OP-TEE + ATF | External TPM |
| TI AM62x | TIFS (Secure ROM) | R5 SPL | A53 U-Boot | OP-TEE | External TPM |
| Qualcomm | PBL | XBL (EDK2) | UEFI / U-Boot | QSEE (proprietary) | Internal |
| Raspberry Pi 4 | GPU bootloader | N/A (GPU loads directly) | U-Boot | OP-TEE | External TPM2.0 |
| Intel x86 | ACM / UEFI ROM | IBB | UEFI | SMM / TXT | fTPM / dTPM |
| Arm Morello | CCA Platform Firmware | TF-A BL1 | TF-A BL2+ | CCA RMM | Built-in |

---

## D — Learning Path

### Phase 1: Boot Chain Mechanics (1–2 weeks)

**Goal:** Trace a real boot from power-on to kernel on a development board.

1. Acquire: BeagleBone Black, Raspberry Pi 4, or i.MX6 EVK.
2. Read: [U-Boot Documentation](https://docs.u-boot.org/en/latest/)
3. Exercise: Enable `CONFIG_LOGLEVEL=7` in U-Boot, boot, and identify each stage.
4. Exercise: Replace the DTB with a broken one. Observe the failure. Restore.
5. Read: ARM Architecture Reference Manual — Chapter B1 (Exception Model).

### Phase 2: Cryptographic Integration (2–3 weeks)

**Goal:** Build and boot a signed FIT image.

1. Set up: OpenSSL key generation, mkimage, fit_check_sign.
2. Exercise: Sign a FIT image, verify it boots; corrupt the signature, verify it rejects.
3. Exercise: Embed the public key in U-Boot DTB, rebuild, confirm verification.
4. Read: NIST SP 800-57 (Key Management Guidelines).

### Phase 3: Platform-Specific Secure Boot (3–4 weeks)

**Goal:** Enable full closed-device secure boot on a real platform.

1. Choose: NXP i.MX8M EVK (best documentation) or Raspberry Pi CM4.
2. Read: [NXP i.MX Secure Boot Application Note (AN4581)](https://www.nxp.com/docs/en/application-note/AN4581.pdf)
3. Exercise: Program OTP on development fuses (not production fuses!). Verify HAB status.
4. Exercise: Deliberately boot an unsigned image on a closed board. Confirm it halts.

### Phase 4: Production Architecture (4–6 weeks)

**Goal:** Design a manufacturable, recoverable, attestable secure boot system.

1. Design: Key hierarchy (SRK → ISK → Debug key). Write key management policy.
2. Implement: A/B boot partition with U-Boot environment state machine.
3. Implement: Anti-rollback using a monotonic counter (software-simulated or OTP).
4. Study: TPM 2.0 specification (TCG). Implement a TPM quote and verify it remotely.
5. Review: [ENISA Guidelines for Secure Boot in IoT](https://www.enisa.europa.eu/).

### Phase 5: Security Review and Hardening (ongoing)

1. Run: [BootJacker](https://github.com/iotsecurityfoundation/boot-integrity) or equivalent boot integrity checker.
2. Threat model: STRIDE analysis of your boot chain.
3. Test: Voltage glitching simulation (ChipWhisperer or custom).
4. Audit: Verify no debug backdoors remain in production build (binwalk, strings analysis).

---

## E — Reference Map

```
                    ┌───────────────────────────────────────────────────┐
                    │             BOOTLOADER + SECURE BOOT              │
                    │                  REFERENCE MAP                    │
                    └───────────────────────────────────────────────────┘

HARDWARE LAYER                    FIRMWARE LAYER              PROTOCOL LAYER
─────────────────                 ──────────────              ──────────────
OTP Fuses                         ROM (Stage 0)               TBBR (ARM std)
  └── SRK Hash                      └── HABv4/AHAB            TrustZone
  └── SVN                           └── PSCI support          TPM 2.0 / TCG
  └── JTAG Disable                                            UEFI Secure Boot
                                  SPL (Stage 1)
Crypto Accelerator                  └── DDR Training
  └── CAAM (NXP)                    └── Storage Init
  └── CryptoCell (Nordic)           └── FIT verify
  └── TrustZone CryptoLib
                                  U-Boot (Stage 2)
TZASC                               └── FIT image load
  └── Memory partitioning           └── bootcmd
                                    └── A/B selection
Boot Strapping
  └── Boot device select          ATF (BL1→BL33)
                                    └── EL3 Secure Monitor
                                    └── PSCI dispatcher

KEY HIERARCHY                     ATTACK SURFACE              MITIGATIONS
─────────────                     ──────────────              ───────────
SRK (HSM only)                    Glitch injection            HW glitch detect
  └── ISK (CI/CD HSM)             JTAG debug                  OTP JTAG disable
  └── Debug key (dev only)        Cold boot attack            Memory encryption
                                  Rollback                    SVN anti-rollback
                                  TOCTOU race                 Atomic verify+exec
                                  Env tampering               Signed env / no env
```

---

## F — Official References

| Resource | URL |
|----------|-----|
| U-Boot Documentation | https://docs.u-boot.org/en/latest/ |
| ARM Trusted Firmware-A | https://trustedfirmware-a.readthedocs.io/ |
| OP-TEE Documentation | https://optee.readthedocs.io/ |
| NXP HABv4 App Note (AN4581) | https://www.nxp.com/docs/en/application-note/AN4581.pdf |
| NXP AHAB Documentation | https://docs.nxp.com (search: AHAB) |
| TCG TPM 2.0 Specification | https://trustedcomputinggroup.org/resource/tpm-library-specification/ |
| ARM TBBR Specification | https://developer.arm.com/documentation/den0006/ |
| Linux Kernel Verified Boot | https://www.kernel.org/doc/html/latest/admin-guide/device-mapper/verity.html |
| NIST SP 800-147 (BIOS protection) | https://csrc.nist.gov/publications/detail/sp/800-147/final |
| ENISA IoT Secure Boot | https://www.enisa.europa.eu/publications/guidelines-for-securing-the-internet-of-things |
| ChipWhisperer (Glitch testing) | https://chipwhisperer.readthedocs.io/ |
| Mender.io (OTA + A/B) | https://docs.mender.io/ |

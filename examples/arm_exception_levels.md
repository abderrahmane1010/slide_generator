# ARMv8-A / AArch64 — Exception Levels (EL0–EL3)

> Référence technique formelle — architecture ARMv8-A (ARM Architecture Reference Manual, DDI 0487)

---

## 1. Vue d'ensemble du modèle de privilèges

L'architecture ARMv8-A définit **quatre niveaux d'exception** (Exception Levels, EL),
numérotés de 0 à 3. Le niveau de privilège **augmente** avec l'indice : EL0 est le moins
privilégié, EL3 est le plus privilégié. Un logiciel s'exécutant à EL*n* ne peut accéder
qu'aux ressources que son niveau l'y autorise.

```
         ┌─────────────────────────────────────────────────────────────────┐
         │  EL3  — Secure Monitor  (plus haut privilège, monde sécurisé)   │
         ├──────────────────────────────┬──────────────────────────────────┤
         │  EL2  — Hyperviseur          │  (Secure EL2 depuis ARMv8.4-A)   │
         ├──────────────────────────────┴──────────────────────────────────┤
         │  EL1  — Kernel / OS (Non-Secure ou Secure)                      │
         ├─────────────────────────────────────────────────────────────────┤
         │  EL0  — User-space / Applications (Non-Secure ou Secure)        │
         └─────────────────────────────────────────────────────────────────┘
              ▲ Monde Non-Sécurisé (NS=1)    ▲ Monde Sécurisé (NS=0)
              │  géré par SCR_EL3.NS          │  TrustZone
```

Chaque niveau possède son propre jeu de **registres système banked** (SPSR, ELR, SP,
VBAR, SCTLR, TCR, TTBR, etc.). Un niveau ne peut ni lire ni écrire les registres
banked d'un niveau supérieur.

---

## 2. Définition technique de chaque niveau

### EL0 — Unprivileged Execution (User-space)

| Attribut | Valeur |
|---|---|
| Privilège | Aucun — niveau non-privilégié |
| Registre de pile | `SP_EL0` |
| Vecteurs d'exception | Non définis à ce niveau (traités par EL1+) |
| Accès MMU | Via tables de pages gérées par EL1 ; traduction `VA → IPA → PA` |
| Accès aux registres système | Limité : quelques registres en lecture seule (`CTR_EL0`, `CNTVCT_EL0`, …) |
| Instructions interdites | `MSR`/`MRS` vers registres EL1+, `HVC`, `SMC`, `ERET` |

**Rôle** : exécution des processus utilisateur, applications, TEE clients (Secure EL0).
Toute tentative d'accès à des ressources privilégiées lève une exception synchrone
de type **Undefined Instruction** ou **System Call** vers EL1.

---

### EL1 — OS Kernel / Privileged Execution

| Attribut | Valeur |
|---|---|
| Privilège | Privilégié — accès complet aux ressources OS |
| Registres banked | `SP_EL1`, `SPSR_EL1`, `ELR_EL1`, `VBAR_EL1`, `SCTLR_EL1`, `TTBR0/1_EL1`, `TCR_EL1`, `ESR_EL1`, `FAR_EL1`, … |
| Gestion MMU | Active/configure le MMU via `SCTLR_EL1.M` ; gère les tables de pages `TTBR0_EL1` (user) et `TTBR1_EL1` (kernel) |
| Gestion des interruptions | Configure `VBAR_EL1` ; masque IRQ/FIQ via `DAIF` ; lit `IAR` du GIC |
| Instructions supplémentaires | `TLBI`, `DC`, `IC`, `AT`, `MSR`/`MRS` vers registres EL1 |
| Instructions interdites | `HVC` (si `HCR_EL2.HCD=1`), `SMC` (si `SCR_EL3.SMD=1`) |

**Rôle** : noyau OS (Linux, RTOS, Trusted OS dans le monde sécurisé).
Peut lever une exception vers EL2 via `HVC` si l'hyperviseur est présent et activé.

---

### EL2 — Hypervisor

| Attribut | Valeur |
|---|---|
| Privilège | Hyperviseur — contrôle de l'isolation entre VMs |
| Activé par | `HCR_EL2.VM = 1` (virtualisation stage-2 activée) |
| Registres banked | `SP_EL2`, `SPSR_EL2`, `ELR_EL2`, `VBAR_EL2`, `HCR_EL2`, `VTCR_EL2`, `VTTBR_EL2`, `HPFAR_EL2`, … |
| Traduction mémoire | Stage-2 : `IPA → PA` via `VTTBR_EL2` ; EL0/EL1 voient des `IPA`, EL2 traduit vers `PA` physiques réels |
| Virtualisation des interruptions | `ICH_*` registers (GICv3/4) ; injecte des interruptions virtuelles dans les VMs |
| Pièges (traps) | Contrôle quelles instructions EL1/EL0 provoquent un trap vers EL2 (`HCR_EL2`, `CPTR_EL2`, `HSTR_EL2`) |
| Secure EL2 | Disponible depuis ARMv8.4-A si `SCR_EL3.EEL2 = 1` — permet un hyperviseur dans le monde sécurisé |

**Rôle** : hyperviseur de type-1 (KVM, Xen). Isole les VMs, virtualise CPU/mémoire/MMIO.
Invisible pour EL1 et EL0 (transparent virtualization).

---

### EL3 — Secure Monitor

| Attribut | Valeur |
|---|---|
| Privilège | Maximum — arbitre entre les deux mondes |
| Présence | Obligatoire si TrustZone est utilisée |
| Registres banked | `SP_EL3`, `SPSR_EL3`, `ELR_EL3`, `VBAR_EL3`, `SCR_EL3`, `SDER32_EL3`, `CPTR_EL3`, … |
| Bit de monde | `SCR_EL3.NS` : `0` = Secure, `1` = Non-Secure |
| Firmware | Typiquement ARM Trusted Firmware-A (ATF), code BL31 |
| Accès mémoire | Accès à toute la mémoire physique, Secure et Non-Secure |
| Instructions | `SMC` reçu ; `ERET` retour vers le monde cible |

**Rôle** : Secure Monitor. Commute entre le monde Non-Sécurisé (OS/Hyperviseur) et le
monde Sécurisé (Trusted OS) en sauvegardant/restaurant l'état complet du processeur.
Configure également les contrôleurs d'interruption, SMMU, et l'isolation mémoire TrustZone.

---

## 3. Mécanismes de transition entre niveaux

### 3.1 Règle fondamentale

> **On ne peut entrer dans un niveau EL*n* que par une exception (entrée) ou en revenir
> par `ERET` (sortie). Il n'existe pas d'instruction de "saut direct" entre niveaux.**

Les transitions respectent la contrainte : **le niveau destination doit être ≥ niveau source**
(exception) ou **≤ niveau source** (`ERET`).

---

### 3.2 Entrée dans un niveau supérieur (exception)

Trois familles d'instructions / événements déclenchent une exception vers un niveau supérieur :

| Mécanisme | Instruction / Événement | Niveau cible |
|---|---|---|
| **SVC** — Supervisor Call | `SVC #imm16` | EL0 → EL1 |
| **HVC** — Hypervisor Call | `HVC #imm16` | EL1 → EL2 |
| **SMC** — Secure Monitor Call | `SMC #imm16` | EL1/EL2 → EL3 |
| **IRQ / FIQ / SError** | Signal externe du GIC | EL*n* → EL*n*+ (selon routage) |
| **Exception synchrone** | Data Abort, Instruction Abort, Undefined, Alignment | EL*n* → EL*n*+ |

#### Séquence matérielle à la prise d'exception vers EL*n* :

```
1. SPSR_ELn  ← PSTATE courant        (sauvegarde : N,Z,C,V, DAIF, nRW, EL, SP)
2. ELR_ELn   ← PC courant (ou PC+4)  (adresse de retour)
3. PSTATE.EL ← n                     (changement de niveau)
4. PSTATE.SP ← 1                     (utilisation de SP_ELn)
5. PSTATE.DAIF ← masque IRQ/FIQ      (désactivation des interruptions)
6. PC        ← VBAR_ELn + offset     (vecteur d'exception)
```

L'offset dans `VBAR_ELn` dépend du type d'exception et du niveau d'origine :

```
Offset 0x000  : Synchrone, même EL, SP_EL0
Offset 0x080  : IRQ/vIRQ, même EL, SP_EL0
Offset 0x100  : FIQ/vFIQ, même EL, SP_EL0
Offset 0x180  : SError/vSError, même EL, SP_EL0
Offset 0x200  : Synchrone, même EL, SP_ELn
Offset 0x280  : IRQ/vIRQ, même EL, SP_ELn
...
Offset 0x400  : Synchrone, niveau inférieur, AArch64
Offset 0x480  : IRQ/vIRQ, niveau inférieur, AArch64
Offset 0x500  : FIQ/vFIQ, niveau inférieur, AArch64
Offset 0x580  : SError, niveau inférieur, AArch64
Offset 0x600  : Synchrone, niveau inférieur, AArch32
...
```

Le registre `ESR_ELn` (Exception Syndrome Register) encode la **cause exacte** :
- `ESR_ELn.EC[31:26]` : Exception Class (SVC=0x15, HVC=0x16, SMC=0x17, Data Abort=0x24, …)
- `ESR_ELn.ISS[24:0]` : Instruction Specific Syndrome (numéro SVC, type de faute, …)

---

### 3.3 Retour vers un niveau inférieur (`ERET`)

```
ERET :
  PC     ← ELR_ELn      (adresse de retour sauvegardée)
  PSTATE ← SPSR_ELn     (restauration complète de l'état)
  → le processeur reprend à l'EL encodé dans SPSR_ELn.EL
```

`ERET` est la **seule** instruction permettant de descendre d'un niveau.
Elle est réservée au niveau EL1+ ; une exécution à EL0 lève une Undefined Instruction.

---

### 3.4 Routage des interruptions IRQ / FIQ

Le GICv3/v4 et les registres de configuration contrôlent à quel niveau les interruptions
sont délivrées :

| Registre | Champ | Effet |
|---|---|---|
| `SCR_EL3` | `.IRQ`, `.FIQ` | Route IRQ/FIQ vers EL3 si = 1 |
| `HCR_EL2` | `.IMO`, `.FMO` | Route IRQ/FIQ physiques vers EL2 si = 1 |
| `HCR_EL2` | `.VSE`, `.VI`, `.VF` | Injecte SError/IRQ/FIQ **virtuels** dans EL1 |
| `DAIF` | bits D,A,I,F | Masque debug/SError/IRQ/FIQ au niveau courant |

Priorité de routage : `SCR_EL3 > HCR_EL2 > VBAR_EL1`

---

### 3.5 Schéma récapitulatif des transitions

```
          EL0                  EL1                 EL2                EL3
   ┌───────────────┐    ┌───────────────┐    ┌─────────────┐    ┌──────────────┐
   │  Application  │    │  OS Kernel    │    │  Hyperviseur│    │Secure Monitor│
   │  User-space   │    │  Trusted OS   │    │  KVM / Xen  │    │  ATF BL31    │
   └───────┬───────┘    └──────┬────────┘    └──────┬──────┘    └──────┬───────┘
           │                   │                    │                   │
           │  SVC / Exception  │                    │                   │
           │──────────────────>│                    │                   │
           │                   │  HVC / Exception   │                   │
           │                   │───────────────────>│                   │
           │                   │                    │  SMC / Exception  │
           │                   │                    │──────────────────>│
           │                   │                    │                   │
           │<──────────────────│<───────────────────│<──────────────────│
           │       ERET        │       ERET         │       ERET        │
```

---

## 4. État sauvegardé à chaque transition

### Registres automatiquement sauvegardés par le matériel

| Registre | Contenu sauvegardé |
|---|---|
| `SPSR_ELn` | `PSTATE` complet (flags, DAIF, mode, EL, SP sel.) |
| `ELR_ELn` | Adresse de retour (PC au moment de l'exception) |

### Registres sauvegardés par le logiciel (convention ABI / handler)

Le handler d'exception est responsable de sauvegarder sur la pile :
- Registres généraux `X0–X30`
- `SP_EL0` si le handler tourne sur `SP_ELn`
- Registres SIMD/FP `V0–V31` (si utilisés)
- Registres système additionnels nécessaires au handler

---

## 5. Basculement Non-Sécurisé ↔ Sécurisé (TrustZone)

Le basculement entre les deux mondes **ne peut se faire qu'à travers EL3** :

```
Monde Non-Sécurisé (NS=1)              Monde Sécurisé (NS=0)
─────────────────────────              ──────────────────────
EL0 : Android / Linux app              EL0 : TA (Trusted Application)
EL1 : Linux Kernel                     EL1 : Trusted OS (OP-TEE, etc.)
EL2 : Hyperviseur                      (EL2 : Secure EL2 si ARMv8.4-A)
         │                                        │
         │  SMC #0  (appel vers EL3)              │
         ▼                                        │
      EL3 : Secure Monitor  ◄────────────────────┘
         │                        (ERET vers NS ou S)
         │  1. Sauvegarde contexte NS (x0–x30, SP_EL0, SP_EL1, EL1 sys regs)
         │  2. SCR_EL3.NS ← 0
         │  3. Restaure contexte S
         │  4. ERET → EL1-S ou EL0-S
         ▼
   Monde Sécurisé actif
```

Le registre `SCR_EL3` est le pivot central :

| Bit | Nom | Effet si = 1 |
|---|---|---|
| `NS` | Non-Secure | EL0/EL1 sont dans le monde Non-Sécurisé |
| `IRQ` | IRQ routing | IRQ pris en charge à EL3 |
| `FIQ` | FIQ routing | FIQ pris en charge à EL3 |
| `SMD` | SMC Disable | `SMC` lève une Undefined Instruction depuis EL1/EL2 |
| `HCE` | HVC Enable | Autorise `HVC` depuis EL1 |
| `EEL2` | Secure EL2 | Active l'EL2 dans le monde sécurisé (ARMv8.4-A) |
| `RW` | Register Width | `1` = EL inférieur en AArch64 ; `0` = AArch32 |

---

## 6. Résumé des droits par niveau

| Capacité | EL0 | EL1 | EL2 | EL3 |
|---|:---:|:---:|:---:|:---:|
| Accès MMU (stage-1) | — | ✓ | ✓ | ✓ |
| Accès MMU (stage-2) | — | — | ✓ | — |
| Configuration TLB (`TLBI`) | — | ✓ | ✓ | ✓ |
| Configuration caches (`DC`, `IC`) | partiel | ✓ | ✓ | ✓ |
| Gestion interruptions | — | ✓ | ✓ | ✓ |
| Émission `SVC` | ✓ | — | — | — |
| Émission `HVC` | — | ✓ | — | — |
| Émission `SMC` | — | ✓ | ✓ | — |
| Exécution `ERET` | — | ✓ | ✓ | ✓ |
| Accès registres EL3 | — | — | — | ✓ |
| Commutation de monde (NS bit) | — | — | — | ✓ |

---

## Références

- **ARM Architecture Reference Manual — ARMv8-A** (DDI 0487), chapitres D1 (AArch64 exception model), D13 (system registers)
- **ARM Trusted Firmware-A** — `bl31/` source (implémentation de référence du Secure Monitor)
- **AArch64 Programmer's Guides** — Cortex-A Series (ARM DEN0024A)
- **GICv3 Architecture Specification** (IHI0069) — routage des interruptions



# Impact Analysis: Containerizing the CSBrick (CSServer)

---

## Table of Contents

1. [What Changes Fundamentally](#1-what-changes-fundamentally)
2. [Filesystem Impact](#2-filesystem-impact)
3. [Network Impact](#3-network-impact)
4. [HSM / Crypto Hardware Access](#4-hsm--crypto-hardware-access)
5. [DPWS Discovery Service](#5-dpws-discovery-service)
6. [Authentication & Authorization (LAS)](#6-authentication--authorization-las)
7. [Inter-Process Communication (IPC)](#7-inter-process-communication-ipc)
8. [Process & Signal Handling](#8-process--signal-handling)
9. [TLS Reload Mechanism](#9-tls-reload-mechanism)
10. [Configuration & Persistence Strategy](#10-configuration--persistence-strategy)
11. [Summary Table](#11-summary-table)
12. [Recommended Docker Run Skeleton](#12-recommended-docker-run-skeleton)

---

## 1. What Changes Fundamentally

The CSBrick binary does not change — what changes is the **execution environment** it sees:

| Aspect | Native process | Containerized process |
|---|---|---|
| PID namespace | Sees all host PIDs | Sees only its own PIDs |
| Filesystem | Host FS directly | Overlay FS (image + bind mounts) |
| Network | Host interfaces directly | Private virtual interface (`veth`) + bridge NAT |
| IPC | Host IPC namespace | Isolated IPC namespace |
| Hostname | Host hostname | Configurable per container |
| UID/GID | Host users | Mapped or mirrored |
| Kernel drivers | Host kernel | **Same host kernel** (no isolation) |

On Linux, Docker does **not** add a hypervisor — the container uses the **same kernel** as the host. Driver access is therefore possible, but kernel-level features like multicast routing are shared with the host.

---

## 2. Filesystem Impact

### 2.1 What the CSBrick expects

The CSBrick has a well-defined filesystem layout. The runtime working area (`run/`) observed on the simulator is:

```
run/
├── config.json              ← static config (cs_root_path, cert store paths, RBAC paths...)
├── dyn_config.json          ← dynamic config (boot_seq, IP addresses, friendly name)
├── inbox/                   ← staging area for incoming CS config packages
├── internal/
│   ├── certs/               ← active device key and certificate
│   │   ├── se-CSBSIM.csr
│   │   ├── se-CSBSIM-internal.key
│   │   ├── se-CSBSIM.key
│   │   └── se-CSBSIM.pem
│   └── crls/
├── persistent/              ← backup area written by the save callback, restored by restore callback
│   ├── cti023/
│   └── internal/
│       └── certs/           ← copy of the active cert, used for rollback
│           ├── se-CSBSIM.csr
│           ├── se-CSBSIM-internal.key
│           ├── se-CSBSIM.key
│           └── se-CSBSIM.pem
├── sec-db/                  ← active security database (RBAC + policy + cert stores)
│   ├── certs/
│   │   ├── ca_store/
│   │   ├── cms_signers/
│   │   └── whitelist/
│   ├── conf/                ← security policy JSON files
│   │   ├── se-est.json
│   │   ├── se-evtlog.json
│   │   ├── se-ldap.json
│   │   ├── se-net-services.json
│   │   ├── se-opcua.json
│   │   ├── se-sec-banner.json
│   │   ├── se-sec-version.json
│   │   ├── se-snmpv3.json
│   │   ├── se-tls.json
│   │   └── se-user-account.json
│   └── rbac/
│       ├── se-rbac-roles.json
│       └── se-rbac-users.json
└── svc/
    └── csconf/              ← CS configuration service working files
        ├── certs/
        │   ├── ca_store/
        │   ├── master/
        │   └── whitelist/
        └── rbac/
```

The factory configuration (read-only templates) is a separate tree that is copied into `run/sec-db/` at first startup.

### 2.2 Docker overlay FS behavior

Docker's overlay filesystem has three logical layers:

```
Container view (merged — what the process sees)
      ▲
Upper layer  (read/write, container-specific delta — lost on container removal)
      ▲
Lower layers (read-only image layers — shared across containers)
```

**Impact**: Any file written by the CSBrick at runtime (certificates, RBAC updates, `dyn_config.json`, boot sequence increment) goes into the **upper layer** and is **lost when the container is removed**, unless explicitly persisted.

### 2.3 Mitigation: bind mounts

Paths that must survive container restarts must be **bind-mounted** from the host:

```bash
-v /host/cs/working:/cs/working         # cert stores, dyn_config.json
-v /host/cs/factory:/cs/factory:ro      # factory config (read-only)
-v /host/cs/persistent:/cs/persistent  # save/restore area (save & restore callbacks)
```

> The `save` and `restore` platform callbacks (called on CS config update and rollback) must write to a **bind-mounted path** on the host to achieve persistence. The factory `reset` callback restores from another bind-mounted read-only area.

### 2.4 The static `config.json` path problem

The `config.json` contains **absolute paths** (`cs_root_path`, `internal_folder`, cert store folders, `dyn_conf_path`). These paths must be consistent with the container's filesystem view, not the host's. Options:

- Use container-internal paths (e.g., `/cs/working`) and bind-mount the host directory there.
- Regenerate/template `config.json` at container startup via an entrypoint script.

### 2.5 The `boot_seq` ?

The dynamic config `boot_seq` must be incremented at each startup. In a container lifecycle, "startup" happens at each `docker run` or restart. A bind-mounted `dyn_config.json` on the host handles this correctly, as the file persists between container runs.

---

## 3. Network Impact

### 3.1 Container default network (bridge mode)

By default, a container gets a private IP on a Docker bridge network (e.g., `172.17.0.x`). The host uses NAT to expose ports. The CSBrick listens on:

- **Port 443** (HTTPS, via the reverse proxy — but in the CSBrick stack, the proxy is a separate process)
- **local HTTP ports** (e.g., `127.0.0.1:8989` for the CSServer backend, 8089 for the LAS backend).
- **UDP multicast** for DPWS discovery

**NAT breaks UDP multicast** — this is the most significant network constraint (see §5).

### 3.2 The `CSB_BIND_ADDR` and loopback assumption

The CSServer is designed to bind on `127.0.0.1:<port>` (loopback), accepting connections only from the reverse proxy running on the same host. In a container:

- If the **reverse proxy is inside the same container**: loopback works normally — no change needed.
- If the **reverse proxy is on the host or another container**: `127.0.0.1` is isolated — the proxy cannot reach the CSServer. The bind address must be changed to `0.0.0.0:<port>` or the container's internal IP, and the port must be exposed.

### 3.3 IP address visibility for certificates

The `dyn_config.json` holds the device IP addresses that are injected into the certificate `SubjectAltName` via `cs_mgr_refresh_all_certs_ip_addresses()`. In a container:

- The container sees its **private bridge IP** (e.g., `172.17.0.2`), not the host's physical IP.
- Certificates generated inside the container will embed the wrong IP unless:
  - The container uses **host network mode** (`--network host`), or
  - The `dyn_config.json` is pre-populated with the correct host IPs before CSBrick initialization, or
  - The entrypoint script injects the host IP into `dyn_config.json` at startup.

### 3.4 Host network mode

Using `--network host` eliminates the NAT layer entirely:

```bash
docker run --network host ...
```

The container shares the host's network stack, which resolves several CSBrick-specific constraints at once:
- DPWS multicast works without any special configuration
- The CSServer loopback assumption is preserved
- Certificate IP addresses match the real device IPs

The trade-off is **reduced network isolation** — the container can reach (and be reached from) any host interface.

---

## 4. HSM / Crypto Hardware Access

### 4.1 The problem

The CSBrick communicates with an HSM via a **Linux kernel driver**. Containers share the host kernel but have an isolated device namespace. By default, `/dev` entries for the HSM are **not visible** inside the container.

### 4.2 Exposing the HSM device

The HSM device must be explicitly passed to the container:

```bash
docker run --device /dev/hsm0:/dev/hsm0 ...
```

Or, if the HSM uses a character device with a specific major/minor number, use `--device-cgroup-rule` to grant access via cgroup rules.

### 4.3 Driver and permissions

The container process runs with a UID/GID. The HSM device node on the host has owner/group and permission bits. Either:
- Run the container as the same UID that owns the device, or
- Add the container user to the appropriate group (if using user namespaces), or
- Use `--privileged` (grants full device access — **not recommended** for a security-sensitive component like CSBrick).

### 4.4 TPM case (`use_tpm: true`)

If the CSBrick is configured with `"use_tpm": true`, the TPM device (`/dev/tpm0`, `/dev/tpmrm0`) must be exposed the same way. The `tss2` socket (if using TCTI) may also need to be bind-mounted.

### 4.5 Entropy for PRNG

The CS library crypto engines (e.g. MBedTLS engine) require quality entropy sources for PRNG initialization. In a container:
- `/dev/random` and `/dev/urandom` are available by default.
- Hardware entropy sources (RDRAND, TPM-based) may require explicit device access (see §4.2 and §4.4).
- If the entropy callback of the active engine fails to gather sufficient entropy, initialization will fail — **a critical security issue**.

---

## 5. DPWS Discovery Service

### 5.1 What DPWS requires

The DPWS (Devices Profile for Web Services) discovery service uses **WS-Discovery**, which relies on:
- **UDP multicast** to `239.255.255.250:3702` (IPv4) or `FF02::C:3702` (IPv6)
- The ability to **send and receive multicast packets** on specific network interfaces

The `config.json` specifies which interfaces the DPWS service listens on:
```json
"dpws_interfaces": [ "seGmac0" ]
```

### 5.2 Multicast in containers

Docker bridge networking does **not forward multicast** between the container's virtual interface and the host's physical interfaces. Discovery packets sent by the container are not visible on the LAN, and vice versa.

### 5.3 Solutions

| Approach | Multicast works | Network isolation |
|---|---|---|
| `--network host` | Yes | None |
| `--network macvlan` | Yes | Partial |
| `--network bridge` + `--cap-add NET_ADMIN` + routing rules | Complex | Yes |
| Disable DPWS in container (`CSB_WITHOUT_DPWS`) | N/A | Yes |

If network isolation is required, disable DPWS inside the container (`CSB_WITHOUT_DPWS` macro) and run the Preconfig server separately on the host or in a dedicated container with host/macvlan networking.

### 5.4 Interface name mismatch

Inside a container with bridge networking, the interface is named `eth0`, not `seGmac0`. If DPWS is kept active, `dpws_interfaces` in `config.json` must be updated to match the container's interface name.

---

## 6. Authentication & Authorization (LAS)

### 6.1 The Local Authentication Server (LAS) inside a container

The LAS exposes:
- An **external endpoint** (TI-122 Connect/Disconnect) — accessed by clients through the reverse proxy
- An **internal endpoint** (login/password or token validation) — accessed by other application servers on the same device (loopback)

In a container, the internal endpoint is only reachable from **inside the same container** (or containers on the same Docker network). Application servers on the host cannot reach `127.0.0.1:<LAS_port>` of the container.

### 6.2 Impact on other application servers using `lasclient`

Other servers using the `lasclient` library to authenticate against the LAS must be able to reach it. Options:
- **All servers in the same container**: loopback works — minimal change.
- **Servers in different containers**: use a shared Docker network and replace `127.0.0.1` with the container name (Docker DNS) or IP. Requires changing the LAS bind address.
- **Servers on the host**: requires the LAS port to be exposed (`-p <port>:<port>`) and the lasclient configured with the host IP.

### 6.3 RBAC file updates

When a new CS configuration is received (via CTI-023 Web services from the CAE), the `save` callback must persist the new RBAC files. These files must be bind-mounted to survive container restarts, and all consumers (other servers reading the RBAC) must have access to the same bind-mounted path.

---

## 7. Inter-Process Communication (IPC)

### 7.1 IPC namespace isolation

Docker isolates the IPC namespace by default. This means:
- **POSIX shared memory** (`/dev/shm`) is container-local
- **Unix domain sockets** in the abstract namespace are isolated

The CSBrick does not appear to use POSIX IPC internally, but **platform callbacks** (`save.sh`, `reset.sh`, `locate.sh`) may send signals or write to named pipes/sockets shared with other host processes.

### 7.2 Scripts and host interaction

The platform callback scripts (`save.sh`, `reset.sh`, `locate.sh`, `on_pki.sh`) run **inside the container**. If they need to notify host processes (e.g., signal a watchdog, trigger a LED driver), they cannot do so directly. Solutions:
- Write to a bind-mounted **notification file** that the host monitors (inotify-based).
- Use a bind-mounted **Unix domain socket** to communicate with a host agent.
- Use `--pid host` (share PID namespace) to allow signaling host processes — **security risk**.

---

## 8. Process & Signal Handling

### 8.1 PID 1 problem

In a container, the CSBrick process (or its entrypoint wrapper) runs as **PID 1**. PID 1 has special behavior in Linux:
- It does not receive `SIGTERM` by default unless it explicitly handles it.
- It must reap zombie child processes (important if the platform callback scripts spawn sub-processes).

Use a proper init system (`--init` flag with Docker, or `tini`) to handle this:
```bash
docker run --init ...
```

### 8.2 SIGUSR1 for TLS reload

The reverse proxy reloads its TLS configuration upon `SIGUSR1`. If the proxy and the CSServer run in the same container, signaling works normally. If they are in separate containers, `kill` across containers requires sharing the PID namespace or using a coordination mechanism.

---

## 9. TLS Reload Mechanism

The CS manager supports TLS context reload after certificate updates. In the containerized scenario:

- The new certificate is written to the bind-mounted working area (persisted on host).
- `SIGUSR1` triggers TLS reload in the reverse proxy.
- If the proxy is **outside the container**, the host must listen for a notification (e.g., written by the `save.sh` callback to a shared file) and then send `SIGUSR1` to the host proxy process.

---

## 10. Configuration & Persistence Strategy

### 10.1 Recommended volume layout

Based on the actual `run/` structure:

```
Host path                           Container mount point    Mode   Notes
/opt/csbrick/factory/           →   /cs/factory             ro     Factory conf templates (sec-db seed)
/opt/csbrick/run/               →   /cs/run                 rw     Full runtime working area:
                                                                      config.json, dyn_config.json,
                                                                      internal/ (active certs/keys),
                                                                      sec-db/ (RBAC, policy, cert stores),
                                                                      svc/csconf/ (csconf service state),
                                                                      inbox/ (incoming config packages)
/opt/csbrick/run/persistent/    →   /cs/run/persistent      rw     save/restore backup — can be a
                                                                      separate volume for clarity
/opt/csbrick/www/               →   /cs/www                 ro     ti122-metadata.json,
                                                                      ti122-urlmapping.json
```

> `internal/` contains the private key. If using Docker secrets, mount the key file directly instead of exposing the whole `run/` as a single volume.

### 10.2 Entrypoint script responsibilities

A container entrypoint script should:

1. **Copy factory files** from `/cs/factory/` into `/cs/run/sec-db/` if the directory is empty (first-time initialization).
2. **Inject device-specific info** into `/cs/run/config.json` (serial number, product name) if not already set.
3. **Populate `/cs/run/dyn_config.json`** with current IP addresses (from host env vars or network inspection).
4. **Increment `boot_seq`** in `/cs/run/dyn_config.json`.
5. Start the CSBrick binary.

### 10.3 Image contents

Bake into the Docker image:
- The CSBrick binary and its shared libraries (OpenSSL/MBedTLS, odasurf, abstract_layer).
- The factory configuration templates (`sec-db/conf/`, `sec-db/rbac/` seeds).
- The entrypoint script.

Do **not** bake into the image:
- `run/internal/` — private keys and device certificates (generated at first startup or injected via Docker secrets).
- `run/sec-db/rbac/` runtime files — deployed by the CAE via CTI-023, must survive updates.
- `run/dyn_config.json` — populated at each startup from the live network configuration.
- `run/persistent/` — written by the `save` callback, must outlive container restarts.

---

## 11. Summary Table

| CSBrick Feature | Containerization Impact | Severity | Solution |
|---|---|---|---|
| Filesystem paths (`config.json`) | Paths must match container view | Medium | Use container-internal paths + bind mounts |
| Certificate & key persistence | Lost on container removal | High | Bind-mount working area |
| `save`/`restore` callbacks | Must write to persisted storage | High | Bind-mount persistent area |
| `boot_seq` increment | Works if `dyn_config.json` is bind-mounted | Medium | Bind-mount `dyn_config.json` |
| Certificate SubjectAltName IPs | Container IP ≠ host IP | High | `--network host` or inject real IPs at startup |
| CSServer loopback bind | Broken for external callers | Medium | Host network or expose port |
| DPWS multicast | Broken in bridge mode | High | `--network host`, macvlan, or disable DPWS |
| DPWS interface name | `seGmac0` → `eth0` | Medium | Update `config.json` or use host network |
| HSM driver access | Not visible by default | High | `--device /dev/hsm0` |
| TPM access | Not visible by default | High | `--device /dev/tpm0` |
| MBedTLS entropy | Works (`/dev/urandom` available) | Low | Verify entropy callback sources |
| LAS internal endpoint | Loopback isolated | Medium | Co-locate servers or use Docker network |
| Platform callback scripts | Cannot signal host processes directly | Medium | Bind-mounted notification files or sockets |
| `SIGUSR1` TLS reload | Works within same container | Low | External proxy needs coordination mechanism |
| PID 1 / zombie reaping | Scripts may leave zombies | Medium | Use `--init` or `tini` |
| Secrets (private keys) | Must not be baked in image | High | Docker secrets or bind-mounted volume |

---

## 12. Recommended Docker Run Skeleton

```bash
docker run \
  --name csbrick \
  --network host \                                   # DPWS multicast + loopback + cert IPs
  --init \                                           # PID 1 / zombie reaping
  --device /dev/hsm0:/dev/hsm0 \                    # HSM driver access
  --device /dev/tpm0:/dev/tpm0 \                    # TPM (if use_tpm: true)
  -v /opt/csbrick/factory:/cs/factory:ro \          # Factory sec-db seed (read-only)
  -v /opt/csbrick/run:/cs/run:rw \                  # Full runtime area (certs, RBAC, dyn_config...)
  -v /opt/csbrick/www:/cs/www:ro \                  # TI-122 metadata files
  -e DEVICE_SERIAL=<serial> \                       # Injected into config.json by entrypoint
  -e DEVICE_IP=<ip> \                               # Injected into dyn_config.json by entrypoint
  csbrick:latest
```

> If `--network host` is not acceptable (security policy), switch to `--network macvlan` for DPWS multicast, and handle the LAS internal endpoint via explicit port exposure and `authnclient` reconfiguration.


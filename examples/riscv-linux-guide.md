# RISC-V pour Linux — Les questions fondamentales

## 1. C'est quoi RISC-V, vraiment ?

**RISC-V** est une ISA (Instruction Set Architecture) **open-source et libre de droits**, contrairement à x86 (Intel/AMD) ou ARM (Arm Ltd).

Questions à se poser :
- Est-ce que je comprends la différence entre une **ISA** et une **microarchitecture** ?  
  → L'ISA, c'est le contrat (les instructions). La microarchitecture, c'est l'implémentation physique (SiFive, StarFive, Alibaba T-Head…).
- Pourquoi RISC-V et pas ARM pour Linux embarqué ?  
  → Liberté de licence, pas de royalties, écosystème communautaire ouvert, customisation possible.

---

## 2. Quel profil RISC-V me concerne ?

RISC-V est **modulaire**. Le profil de base est `RV32I` ou `RV64I`, auquel on ajoute des extensions.

| Extension | Rôle |
|-----------|------|
| `I`       | Base entière (obligatoire) |
| `M`       | Multiplication/division |
| `A`       | Opérations atomiques (nécessaire pour Linux) |
| `F`       | Virgule flottante simple |
| `D`       | Virgule flottante double |
| `C`       | Instructions compressées (code plus dense) |
| `G`       | Alias pour `IMAFD` (profil généraliste) |
| `H`       | Hyperviseur |
| `V`       | Vecteurs (SIMD) |

**Questions fondamentales :**
- Mon hardware cible est-il `RV64GC` (le minimum de facto pour Linux) ?
- Est-ce que j'ai besoin de la virtualisation (`H`) ou du vecteur (`V`) ?
- Mon toolchain est-il compilé pour le bon `march` et `mabi` ?

```bash
# Exemple de flags GCC pour RV64GC Linux
-march=rv64gc -mabi=lp64d
```

---

## 3. Les niveaux de privilège : qui fait quoi ?

RISC-V définit trois niveaux de privilège :

```
┌─────────────────────────────┐
│  U-mode  (User / Userspace) │  ← vos programmes
├─────────────────────────────┤
│  S-mode  (Supervisor)       │  ← le kernel Linux
├─────────────────────────────┤
│  M-mode  (Machine)          │  ← le firmware (OpenSBI)
└─────────────────────────────┘
```

**Questions à se poser :**
- Est-ce que je comprends le rôle de **OpenSBI** (le firmware M-mode standard) ?  
  → C'est lui qui boot le système, initialise le hardware bas niveau et passe la main au bootloader/kernel via SBI calls.
- Mon bootloader (U-Boot, GRUB) est-il configuré pour S-mode ?
- Est-ce que mes SBI calls (system resets, timers, IPI…) sont bien gérés ?

---

## 4. La chaîne de boot : dans quel ordre ça démarre ?

```
ZSBL (ROM)
  └─→ OpenSBI (M-mode firmware)
        └─→ U-Boot / GRUB (bootloader S-mode)
              └─→ Linux Kernel
                    └─→ initramfs / rootfs
```

**Questions fondamentales :**
- Qui fournit le ZSBL sur ma cible ? (SoC vendor, FPGA custom…)
- Quelle version d'OpenSBI est compatible avec mon SoC ?
- Mon Device Tree (`DTB`) est-il correct et passé au bon endroit ?
- U-Boot ou directement le kernel ? (certaines cartes bootent direct)

```bash
# Vérifier la version OpenSBI au boot
dmesg | grep -i opensbi
```

---

## 5. Le Device Tree (DTB) — la carte d'identité du hardware

Linux RISC-V **n'a pas de BIOS/UEFI** sur les petites cibles. C'est le **Device Tree** qui décrit le hardware au kernel.

**Questions à se poser :**
- Est-ce que mon DTS/DTB est fourni par le vendor ou dois-je l'écrire/modifier ?
- Est-ce que tous mes périphériques (UART, Ethernet, PCIe, GPIO…) sont bien décrits ?
- Est-ce que le `chosen` node pointe vers le bon `bootargs` et `stdout-path` ?

```dts
/ {
    chosen {
        bootargs = "console=ttyS0,115200 root=/dev/mmcblk0p2 rw";
        stdout-path = "serial0:115200n8";
    };
};
```

- Est-ce que j'utilise `fdtdump` / `dtc` pour valider mon DTB ?

```bash
dtc -I dtb -O dts -o out.dts my.dtb   # Décompiler un DTB
```

---

## 6. Le kernel Linux — configuration et support RISC-V

**Questions à se poser :**

### Architecture
- Est-ce que j'utilise `ARCH=riscv` dans mon build ?
- Est-ce que mon kernel est en `RV64` ou `RV32` (Linux 32-bit est expérimental) ?

### Config minimale
```bash
make ARCH=riscv defconfig          # Config générique
make ARCH=riscv menuconfig         # Personnalisation
```

### Fonctionnalités clés à vérifier
- `CONFIG_RISCV` — activé ?
- `CONFIG_SMP` — multicore ?
- `CONFIG_NUMA` — NUMA support (serveurs) ?
- `CONFIG_RISCV_ISA_V` — extensions vectorielles ?
- `CONFIG_KVM` — virtualisation ?
- `CONFIG_MMU` — obligatoire pour Linux standard
- Driver réseau, stockage, GPU… spécifiques à votre SoC ?

### Versions de kernel
| Version | Milestone RISC-V |
|---------|-----------------|
| 4.15    | Première intégration RISC-V mainline |
| 5.x     | Consolidation, SMP, KGDB |
| 6.x     | Vecteurs, Zicbom, KVM, perf avancé |

---

## 7. Le toolchain — compiler pour RISC-V

**Questions fondamentales :**
- Est-ce que j'utilise un **cross-compiler** ou une compilation native (sur une vraie board RISC-V) ?
- Quel triplet de cible ? `riscv64-linux-gnu` ou `riscv64-unknown-linux-gnu` ?

```bash
# Vérifier le toolchain
riscv64-linux-gnu-gcc --version
riscv64-linux-gnu-gcc -dumpmachine
# → riscv64-linux-gnu
```

- Est-ce que mon `glibc` est compilé pour le bon ABI (`lp64d` pour RV64 avec FPU) ?
- Suis-je en **hard-float** ou **soft-float** ? (impact énorme sur les perfs)

| ABI    | Description |
|--------|-------------|
| `lp64` | 64-bit, pas de FPU |
| `lp64f`| 64-bit, FPU simple précision |
| `lp64d`| 64-bit, FPU double précision (standard Linux) |

---

## 8. Rootfs — le système de fichiers racine

**Questions à se poser :**
- Est-ce que j'utilise **Buildroot**, **Yocto**, **Debian**, **Fedora**, ou une distro upstream pour RISC-V ?
- Mon rootfs est-il compilé pour le bon ABI (cohérent avec le kernel et le toolchain) ?
- Est-ce que j'ai un **initramfs** minimal pour le debug early boot ?

```bash
# Générer un initramfs minimal avec busybox
find . | cpio -ov --format=newc | gzip -9 > initramfs.cpio.gz
```

### Distros Linux avec support RISC-V natif (2024+)
- **Debian** (riscv64 port)
- **Fedora** (riscv64 officiel depuis F38)
- **Ubuntu** (support expérimental)
- **Arch Linux RISC-V** (port communautaire)
- **openEuler** (fort support RISC-V, Huawei)

---

## 9. Hardware cible — choisir sa board

**Questions à se poser :**
- Quel SoC ? (StarFive JH7110, T-Head TH1520, Sophgo SG2042…)
- Est-ce que le SoC est **mainline** dans le kernel ? (ou patch vendor nécessaire ?)
- Quelle quantité de RAM ? (Linux confortable à partir de 512 MB, idéal 2 GB+)
- Est-ce que j'ai accès à un **port série UART** pour le debug ?

### Boards notables (2024-2025)
| Board | SoC | RAM | Statut mainline |
|-------|-----|-----|----------------|
| BeagleV-Ahead | T-Head TH1520 | 4/8 GB | Partiel |
| StarFive VisionFive 2 | JH7110 | 2/4/8 GB | Mainline kernel 6.6+ |
| Milk-V Pioneer | SG2042 (64 cœurs!) | 128 GB | En cours |
| Milk-V Duo | CV1800B | 64 MB | Spécial, très contraint |
| QEMU `virt` | Virtuel | Variable | Parfait pour dev/test |

---

## 10. Déboguer et valider

**Questions à se poser :**
- Est-ce que j'ai accès au **port JTAG** pour le debug bas niveau ?
- Est-ce que j'utilise **QEMU** pour valider avant le hardware réel ?

```bash
# Lancer un kernel RISC-V dans QEMU
qemu-system-riscv64 \
  -machine virt \
  -cpu rv64 \
  -m 2G \
  -kernel Image \
  -append "root=/dev/vda rw console=ttyS0" \
  -drive file=rootfs.ext4,format=raw,id=hd0 \
  -device virtio-blk-device,drive=hd0 \
  -netdev user,id=net0 \
  -device virtio-net-device,netdev=net0 \
  -nographic
```

- Est-ce que `dmesg` est lisible et ne montre pas de **kernel panic** ?
- Est-ce que j'ai configuré `earlycon` pour capturer les logs très tôt ?

```
# Dans bootargs
console=ttyS0,115200 earlycon=sbi
```

---

## 11. Performances et optimisations

**Questions avancées :**
- Est-ce que j'exploite les extensions **Zicbom** (cache management) pour DMA ?
- Est-ce que mon kernel est configuré avec **KPTI** ? (impact perf sur certains SoC)
- Est-ce que j'utilise les extensions vectorielles `V` pour le calcul intensif ?
- Est-ce que mes **interruptions** (PLIC/CLINT) sont bien configurées ?
- Est-ce que j'ai mesuré avec **perf** sur RISC-V ?

```bash
# Perf sur RISC-V (nécessite CONFIG_PERF_EVENTS)
perf stat ./mon_programme
perf top
```

---

## Récapitulatif — Checklist par étape

```
[ ] ISA correcte (RV64GC minimum pour Linux)
[ ] OpenSBI à jour et compatible avec le SoC
[ ] Device Tree valide et complet
[ ] Toolchain avec le bon triplet et ABI (lp64d)
[ ] Kernel configuré avec ARCH=riscv et les bons drivers
[ ] Rootfs cohérent avec l'ABI du kernel
[ ] Port série UART accessible pour le debug
[ ] QEMU validé avant la vraie board
[ ] Logs dmesg propres, pas de panic
[ ] Perf mesurée si usage production
```

---

## Ressources clés

- [RISC-V International](https://riscv.org) — specs officielles
- [kernel.org — RISC-V](https://www.kernel.org/doc/html/latest/riscv/) — doc kernel
- [OpenSBI GitHub](https://github.com/riscv-software-src/opensbi)
- [RISC-V Exchange](https://riscv.org/exchange/) — catalogue de boards et outils
- [Debian RISC-V](https://wiki.debian.org/RISC-V)
- `#riscv` sur IRC Libera.chat / Matrix

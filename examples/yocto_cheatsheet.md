# Yocto Project — Expert Cheat Sheet

> **Scope:** Foundational principles → advanced techniques → BitBake internals → KAS workflows.
> Intended for senior embedded Linux engineers, Yocto architects, and interview preparation at expert level.

---

## Table of Contents

1. [Foundations & Principles](#1-foundations--principles)
   - 1.1 [Embedded Linux Fundamentals](#11-embedded-linux-fundamentals)
   - 1.2 [Core Yocto Concepts & Architecture](#12-core-yocto-concepts--architecture)
   - 1.3 [Layer Model & Priority System](#13-layer-model--priority-system)
   - 1.4 [Variable & Scoping System](#14-variable--scoping-system)
   - 1.5 [Build System Internals](#15-build-system-internals)
2. [Expert Techniques & Best Practices](#2-expert-techniques--best-practices)
   - 2.1 [Layer & Recipe Design Patterns](#21-layer--recipe-design-patterns)
   - 2.2 [Image & Distro Customization](#22-image--distro-customization)
   - 2.3 [Licensing, Compliance & SBOM](#23-licensing-compliance--sbom)
   - 2.4 [SDK & eSDK](#24-sdk--esdk)
   - 2.5 [Security Hardening](#25-security-hardening)
   - 2.6 [Performance Optimisation](#26-performance-optimisation)
   - 2.7 [Reproducible Builds](#27-reproducible-builds)
   - 2.8 [CI/CD Integration](#28-cicd-integration)
3. [Technical Deep Dives](#3-technical-deep-dives)
   - 3.1 [BitBake: Advanced Usage & Internals](#31-bitbake-advanced-usage--internals)
   - 3.2 [BitBake: Debugging & Introspection](#32-bitbake-debugging--introspection)
   - 3.3 [BitBake: Customisation & Extension](#33-bitbake-customisation--extension)
   - 3.4 [KAS: Configuration & Workflows](#34-kas-configuration--workflows)
   - 3.5 [KAS: Advanced Integration](#35-kas-advanced-integration)

---

## 1. Foundations & Principles

### 1.1 Embedded Linux Fundamentals

#### Boot Sequence (ARM / x86)

```
Power-on → ROM bootloader (SBL/IBL)
         → Secondary bootloader (U-Boot SPL / GRUB early stage)
         → Full bootloader (U-Boot / GRUB)
         → Kernel (vmlinux / zImage / Image.gz)
         → initramfs / initrd (optional)
         → Root filesystem (eMMC / NAND / NFS / SquashFS overlay)
         → Init system (systemd / SysVinit / BusyBox init)
         → User-space services
```

| Stage | Yocto Artefact | Key Variable |
|---|---|---|
| SPL / MLO | `u-boot-spl` recipe | `SPL_BINARY` |
| Full bootloader | `u-boot` recipe | `UBOOT_CONFIG`, `UBOOT_MACHINE` |
| Kernel | `linux-yocto` or custom | `PREFERRED_PROVIDER_virtual/kernel` |
| Root filesystem | image recipe | `IMAGE_FSTYPES` |
| Init system | `systemd` / `busybox` | `INIT_MANAGER` |

#### Kernel Image Types

| Image | Description | Architecture |
|---|---|---|
| `zImage` | Self-decompressing compressed image | ARM 32-bit |
| `Image` | Uncompressed kernel image | ARM64 / RISC-V |
| `bzImage` | Big zImage, boot-loader decompresses | x86 |
| `uImage` | U-Boot legacy format with header | ARM (legacy) |
| `fitImage` | Flattened Image Tree — signs kernel + DTB + initramfs | All (preferred) |

#### Root Filesystem Fundamentals

```
/bin   → Essential user binaries (BusyBox or full GNU)
/sbin  → Essential system binaries
/lib   → Shared libraries (multilib: /lib64)
/usr   → Non-essential system resources (merged-usr trend)
/etc   → Host-specific configuration
/dev   → Device nodes (devtmpfs / udev)
/proc  → Process information (procfs)
/sys   → Device model / sysfs
/run   → Runtime volatile data (tmpfs)
/tmp   → Temporary files (tmpfs or persistent)
```

> **Merged-usr:** Modern Yocto (Kirkstone+) defaults to `usrmerge`, where `/bin`, `/sbin`, `/lib` are symlinks into `/usr`. Set `DISTRO_FEATURES:remove = "usrmerge"` to opt out.

---

### 1.2 Core Yocto Concepts & Architecture

#### Project Component Map

```
Yocto Project (umbrella)
├── Poky            ← Reference distribution (meta + meta-poky + meta-yocto-bsp + bitbake)
├── BitBake         ← Task execution engine (make analogue)
├── OpenEmbedded-Core (OE-Core / meta)  ← Core recipe set
├── meta-openembedded  ← Extended recipe collection
└── Layers (meta-*)    ← User / vendor / BSP layers
```

#### Key Terminology

| Term | Definition |
|---|---|
| **Recipe** (`.bb`) | Build instructions for a single software component |
| **BitBake class** (`.bbclass`) | Reusable recipe logic inherited via `inherit` |
| **Layer** (`meta-*`) | Ordered collection of recipes, classes, and configurations |
| **Configuration** (`.conf`) | Global variables for distro, machine, and local build settings |
| **Append file** (`.bbappend`) | Non-invasive extension of an existing recipe |
| **Include file** (`.inc`) | Shared recipe fragment included with `require` / `include` |
| **Distro** | Policy layer defining init system, libc, feature flags |
| **Machine** | BSP layer defining architecture, kernel, bootloader |
| **Image** | Top-level recipe composing packages into a root filesystem |
| **Package** | Binary artefact (`.rpm`, `.deb`, `.ipk`) produced by a recipe |
| **Task** | Discrete unit of work within a recipe (`do_fetch`, `do_compile`, …) |
| **Sstate cache** | Shared-state cache enabling incremental and distributed builds |
| **TMPDIR** | Per-build working directory tree |

#### Canonical Directory Layout (TMPDIR)

```
tmp/
├── deploy/
│   ├── images/<MACHINE>/     ← Final images, kernel, DTBs, bootloader
│   ├── licenses/             ← Per-package license manifests
│   └── rpm/  deb/  ipk/      ← Binary packages
├── pkgdata/                  ← Package metadata database
├── sstate-cache/             ← Local sstate artefacts
├── work/
│   └── <MULTILIB_ARCH>-<DISTRO>-linux*/
│       └── <PN>/<PV>-<PR>/
│           ├── source/       ← Fetched source (S)
│           ├── build/        ← Build directory (B)
│           ├── image/        ← Staging into package (D)
│           ├── packages-split/ ← Per-package staging
│           └── temp/         ← Task logs and run scripts
└── work-shared/              ← Shared sources (linux-yocto, gcc)
```

---

### 1.3 Layer Model & Priority System

#### `bblayers.conf` — Essential Variables

```bitbake
BBLAYERS ?= " \
  ${TOPDIR}/../poky/meta              \
  ${TOPDIR}/../poky/meta-poky         \
  ${TOPDIR}/../poky/meta-yocto-bsp    \
  ${TOPDIR}/../meta-openembedded/meta-oe \
  ${TOPDIR}/../meta-my-bsp            \
  ${TOPDIR}/../meta-my-product        \
"
```

#### Layer Priority

```bitbake
# In meta-my-product/conf/layer.conf
BBFILE_PRIORITY_my-product = "10"
```

- Higher value = higher priority.
- OE-Core is typically `5`, meta-poky `6`.
- A `.bbappend` in a higher-priority layer overrides a lower-priority one.
- Use `bitbake-layers show-layers` to inspect effective priority.

#### `layer.conf` Anatomy

```bitbake
BBPATH      .= ":${LAYERDIR}"
BBFILES     += "${LAYERDIR}/recipes-*/*/*.bb \
                ${LAYERDIR}/recipes-*/*/*.bbappend"

BBFILE_COLLECTIONS             += "my-product"
BBFILE_PATTERN_my-product       = "^${LAYERDIR}/"
BBFILE_PRIORITY_my-product      = "10"

LAYERVERSION_my-product         = "1"
LAYERDEPENDS_my-product         = "core openembedded-layer"
LAYERSERIES_COMPAT_my-product   = "scarthgap styhead"
```

> Always set `LAYERSERIES_COMPAT_*` to prevent accidental use with incompatible Yocto releases.

---

### 1.4 Variable & Scoping System

#### Operator Reference

| Operator | Semantics |
|---|---|
| `VAR = "val"` | Immediate assignment (evaluated at parse time) |
| `VAR := "val"` | Immediate expansion (RHS expanded now) |
| `VAR ?= "val"` | Weak default — only if VAR is unset |
| `VAR ??= "val"` | Weakest default — overridden by `?=` and `=` |
| `VAR += "val"` | Append with space (evaluated at finalisation) |
| `VAR =+ "val"` | Prepend with space |
| `VAR .= "val"` | Append without space |
| `VAR =. "val"` | Prepend without space |
| `VAR:append = " val"` | Override append (note leading space) |
| `VAR:prepend = "val "` | Override prepend (note trailing space) |
| `VAR:remove = "val"` | Remove all occurrences of `val` |

> **Override syntax (Honister+):** `VAR_machine` → `VAR:machine`. The colon-based syntax is mandatory from Kirkstone onwards.

#### Override Evaluation Order

```
VAR = "base"
VAR:append = " appended"        # applied after all overrides
VAR:prepend = "prepended "      # applied after all overrides
VAR:machine-x = "machine-val"   # conditional on MACHINE = "machine-x"
VAR:my-distro = "distro-val"    # conditional on DISTRO = "my-distro"
```

Evaluation: **base** → conditional overrides (machine/distro/…) → **prepend** → **append** → **remove**.

#### Variable Flags (varflags)

```bitbake
do_compile[depends]  += "virtual/kernel:do_deploy"
do_compile[network]   = "1"          # allow network access in task
do_compile[nostamp]   = "1"          # never cache this task
do_compile[dirs]      = "${B}"       # ensure directories exist
do_compile[cleandirs] = "${B}"       # clean before running
do_compile[lockfiles] = "${T}/run.lock"
SRC_URI[sha256sum]    = "abc123..."  # checksum varflag
```

---

### 1.5 Build System Internals

#### Fetch → Deploy Pipeline

```
do_fetch        → Download sources (SRC_URI), populate DL_DIR
do_unpack       → Extract into WORKDIR
do_patch        → Apply quilt patches from SRC_URI *.patch
do_prepare_recipe_sysroot → Populate recipe-specific sysroot
do_configure    → Run autoconf / cmake / meson / custom
do_compile      → Build sources
do_install      → Install into ${D} (DESTDIR pattern)
do_package      → Split D into packages-split/
do_package_qa   → Run QA checks (insane.bbclass)
do_package_write_rpm/deb/ipk → Emit binary packages
do_populate_sysroot → Promote runtime/dev files to shared sysroot
do_rootfs       → (image recipes only) Assemble rootfs
do_image_*      → Generate IMAGE_FSTYPES artefacts
do_deploy       → Copy final artefacts to deploy/images/
```

#### Shared-State (sstate) Cache Internals

- Each task is identified by a **signature hash** (taskhash) covering: recipe content, input variable values, class content, and task code.
- On a cache hit, BitBake skips execution and restores artefacts directly.
- **Setscene tasks** (`do_*_setscene`) check sstate before the real task runs.
- Remote sstate mirrors are configured via:

```bitbake
SSTATE_MIRRORS ?= " \
  file://.* https://sstate.example.com/PATH;downloadfilename=PATH \n"
```

- `BB_HASHSERVE` provides a hash equivalence server — allows reuse of sstate across minor recipe reformulations that produce identical output.

#### Pseudo (Fake Root)

Yocto uses **pseudo** (a `LD_PRELOAD` library) to emulate root privileges during `do_install` and `do_rootfs` without requiring actual root. It intercepts `chown`, `chmod`, `mknod`, etc., recording them in a SQLite database (`${WORKDIR}/pseudo/`).

---

## 2. Expert Techniques & Best Practices

### 2.1 Layer & Recipe Design Patterns

#### Recipe Versioning & Preference

```bitbake
# Force a specific version globally
PREFERRED_VERSION_openssl = "3.2%"

# Force a specific provider
PREFERRED_PROVIDER_virtual/kernel       = "linux-imx"
PREFERRED_PROVIDER_virtual/bootloader   = "u-boot-imx"

# Pin to a specific recipe revision
SRCREV_pn-my-component = "a1b2c3d4e5f6..."
SRCREV_FORMAT = "src"
```

#### `.bbappend` Best Practices

```bitbake
# Always use FILESEXTRAPATHS to avoid path collisions
FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

# Version-agnostic wildcard (use sparingly — risks silent mismatch)
# my-recipe_%.bbappend

# Version-specific (preferred for production)
# my-recipe_1.2.3.bbappend

# Extend SRC_URI safely
SRC_URI += "file://my-fix.patch \
            file://my-config.cfg \
           "

# Extend tasks without replacing them
do_install:append() {
    install -d ${D}${sysconfdir}/my-app
    install -m 0644 ${WORKDIR}/my-config.cfg ${D}${sysconfdir}/my-app/
}
```

#### Multi-config Builds

```bitbake
# local.conf — build for multiple machines in one invocation
BBMULTICONFIG = "mymachine-a mymachine-b"

# conf/multiconfig/mymachine-a.conf
MACHINE = "mymachine-a"
DISTRO  = "my-distro"

# conf/multiconfig/mymachine-b.conf
MACHINE = "mymachine-b"
DISTRO  = "my-distro-minimal"

# Build command
bitbake mc:mymachine-a:core-image-full-cmdline \
        mc:mymachine-b:core-image-minimal
```

#### Dynamic Layers (`BBMASK`)

```bitbake
# Exclude entire recipe directories from parsing
BBMASK += "meta-openembedded/meta-networking/recipes-connectivity/.*"

# Exclude a specific recipe
BBMASK += "recipes-graphics/mesa/mesa_.*\.bb$"
```

#### Inherit Guards (conditional class loading)

```bitbake
# In distro.conf — apply globally
INHERIT += "rm_work"        # reclaim disk space post-build
INHERIT += "buildhistory"   # track build output over time
INHERIT += "create-spdx"    # SPDX SBOM generation

# In recipe — guard with condition
python () {
    if d.getVar('MY_FEATURE') == '1':
        d.appendVar('INHERIT', ' my-custom-class')
}
```

---

### 2.2 Image & Distro Customization

#### Image Recipe Anatomy

```bitbake
SUMMARY = "Production image for MyProduct"
LICENSE = "MIT"

inherit core-image

# Package groups
IMAGE_INSTALL = " \
    packagegroup-core-boot          \
    packagegroup-my-product-base    \
    my-app                          \
    ${CORE_IMAGE_EXTRA_INSTALL}     \
"

# Image features (map to packagegroups and bbclass behaviours)
IMAGE_FEATURES += " \
    read-only-rootfs    \
    ssh-server-openssh  \
    debug-tweaks        \
"

# Filesystem types
IMAGE_FSTYPES = "ext4 wic wic.bz2"

# Image size
IMAGE_ROOTFS_SIZE       ?= "524288"   # 512 MiB in KiB
IMAGE_ROOTFS_EXTRA_SPACE = "102400"   # +100 MiB headroom
IMAGE_OVERHEAD_FACTOR    = "1.3"      # 30% overhead for ext4
```

#### Package Groups

```bitbake
# packagegroup-my-product-base.bb
SUMMARY = "My product base package group"
inherit packagegroup

RDEPENDS:${PN} = " \
    busybox         \
    dropbear        \
    iproute2        \
    my-core-daemon  \
"

RDEPENDS:${PN}-dev = " \
    gdbserver       \
    strace          \
"

PACKAGES = "${PN} ${PN}-dev"
```

#### Distro Configuration

```bitbake
# conf/distro/my-distro.conf
require conf/distro/poky.conf

DISTRO        = "my-distro"
DISTRO_NAME   = "My Embedded Distribution"
DISTRO_VERSION = "1.0.0"
DISTRO_CODENAME = "alpha"

# Policy: libc
TCLIBC = "glibc"            # or "musl"

# Policy: init system
INIT_MANAGER = "systemd"    # or "sysvinit"

# Policy: package manager
PACKAGE_CLASSES = "package_ipk"

# Distro features — curate carefully
DISTRO_FEATURES:remove = " \
    x11 wayland vulkan 3g pcmcia nfc bluetooth \
"
DISTRO_FEATURES:append = " \
    systemd pam largefile opengl \
"

# Compiler hardening
DISTRO_FEATURES:append = " security"
TARGET_CFLAGS:append = " -fstack-protector-strong -D_FORTIFY_SOURCE=2"
TARGET_LDFLAGS:append = " -Wl,-z,relro,-z,now"
```

#### `wic` — Disk Image Partitioning

```wks
# my-product.wks.in
# Requires wic kickstart syntax
bootloader --ptable gpt --timeout=3 --append="quiet"

part /boot --source bootimg-efi --sourceparams="loader=grub-efi" \
           --ondisk sda --fstype=efi --label boot --active --align 1024 --size 64M

part /     --source rootfs --ondisk sda --fstype=ext4 \
           --label rootfs --align 1024 --size 2048M

part /data --ondisk sda --fstype=ext4 --label data \
           --align 1024 --size 1024M
```

```bitbake
# In image recipe or local.conf
WKS_FILE = "my-product.wks.in"
IMAGE_FSTYPES += "wic"
do_image_wic[depends] += "dosfstools-native:do_populate_sysroot \
                           mtools-native:do_populate_sysroot \
                           grub-efi:do_deploy"
```

---

### 2.3 Licensing, Compliance & SBOM

#### License Variables

```bitbake
# Recipe
LICENSE = "GPL-2.0-only & MIT"          # SPDX identifiers (Kirkstone+)
LIC_FILES_CHKSUM = "file://COPYING;md5=... \
                    file://include/foo.h;beginline=1;endline=20;md5=..."
```

#### Commercial License Handling

```bitbake
# In distro or local.conf — whitelist commercial packages
LICENSE_FLAGS_ACCEPTED += "commercial commercial_ffmpeg"

# In recipe
LICENSE_FLAGS = "commercial"
```

#### SPDX SBOM Generation (Kirkstone+)

```bitbake
INHERIT += "create-spdx"

# Configure output
SPDX_NAMESPACE_PREFIX    = "https://example.com/my-product"
SPDX_PRETTY              = "1"       # human-readable JSON
SPDX_INCLUDE_SOURCES     = "1"       # embed source tarballs

# Output location: tmp/deploy/images/<MACHINE>/*.spdx.json
```

#### License Audit Commands

```bash
# List all licenses in an image
bitbake -g core-image-minimal && \
  cat tmp/deploy/licenses/core-image-minimal/license.manifest

# Check for copyleft packages
grep -E "GPL|LGPL" tmp/deploy/licenses/*/license.manifest | sort -u

# Generate source mirror for GPL compliance
bitbake core-image-minimal -c archiver
# Configure: ARCHIVER_MODE = "original" / "patched" / "configured"
```

---

### 2.4 SDK & eSDK

#### Standard SDK

```bash
# Build SDK
bitbake core-image-minimal -c populate_sdk

# Artefact: tmp/deploy/sdk/*.sh self-extracting installer
# Installs: cross-toolchain + target sysroot

# Install
./my-distro-x86_64-core-image-minimal-cortexa53-toolchain-1.0.sh -d /opt/my-sdk

# Use
source /opt/my-sdk/environment-setup-cortexa53-poky-linux
$CC my-app.c -o my-app
```

#### Extensible SDK (eSDK)

```bash
# Build eSDK
bitbake core-image-minimal -c populate_sdk_ext

# Inside eSDK: devtool available, can add/modify recipes
devtool add my-new-component https://github.com/example/my-new-component.git
devtool build my-new-component
devtool deploy-target my-new-component root@192.168.1.100
devtool finish my-new-component ../meta-my-product
```

#### SDK Customisation

```bitbake
# Add extra packages to SDK sysroot
TOOLCHAIN_TARGET_TASK:append = " libssl-dev libcurl-dev"

# Add extra native tools to SDK
TOOLCHAIN_HOST_TASK:append = " nativesdk-cmake nativesdk-ninja"

# Add eSDK configuration
SDK_EXT_TYPE = "full"   # "minimal" installs tools on demand
SDK_INCLUDE_BUILDTOOLS = "1"
```

---

### 2.5 Security Hardening

#### Compiler Mitigations

```bitbake
# In distro.conf
DISTRO_FEATURES:append = " security"

# Stack protection
TARGET_CFLAGS:append  = " -fstack-protector-strong"
TARGET_CXXFLAGS:append = " -fstack-protector-strong"

# FORTIFY_SOURCE (requires -O1 minimum)
TARGET_CPPFLAGS:append = " -D_FORTIFY_SOURCE=2"

# PIE (Position Independent Executables)
TARGET_CFLAGS:append  = " -fPIE"
TARGET_LDFLAGS:append = " -pie"

# RELRO + BIND_NOW
TARGET_LDFLAGS:append = " -Wl,-z,relro,-z,now"

# Control-flow integrity (GCC 9+ / Clang)
TARGET_CFLAGS:append  = " -fcf-protection=full"   # x86 only
```

#### Read-Only Rootfs

```bitbake
IMAGE_FEATURES += "read-only-rootfs"

# Declare volatile directories in recipe
VOLATILE_LOG_DIR = "yes"   # /var/log → tmpfs

# In custom recipe, mark writable paths
pkg_postinst_ontarget:${PN}() {
    # This runs on target first boot
    mkdir -p /data/my-app
}
```

#### Secure Boot (fitImage + IMA)

```bitbake
# Enable fitImage
KERNEL_CLASSES:append = " kernel-fitimage"
KERNEL_IMAGETYPE      = "fitImage"

# Sign with RSA key
UBOOT_SIGN_ENABLE  = "1"
UBOOT_SIGN_KEYDIR  = "${TOPDIR}/keys"
UBOOT_SIGN_KEYNAME = "dev-key"
UBOOT_MKIMAGE_DTCOPTS = "-I dts -O dtb -p 2000"

# IMA/EVM appraisal
DISTRO_FEATURES:append = " ima"
```

#### CVE Tracking

```bitbake
# Inherit CVE checker
INHERIT += "cve-check"

# Generate CVE report
bitbake core-image-minimal -c cve_check

# Output: tmp/deploy/cve/
```

---

### 2.6 Performance Optimisation

#### Parallelism Tuning

```bitbake
# local.conf — tune to host cores
BB_NUMBER_THREADS   = "${@oe.utils.cpu_count()}"   # BitBake task parallelism
PARALLEL_MAKE       = "-j ${@oe.utils.cpu_count()}" # make -j
BB_NUMBER_PARSE_THREADS = "8"    # parser threads (Scarthgap+)
```

#### Disk Space Reclamation

```bitbake
# Remove WORKDIR after packaging (significant disk saving)
INHERIT += "rm_work"

# Exclude specific recipes from rm_work
RM_WORK_EXCLUDE += "linux-yocto my-big-recipe"
```

#### Hash Equivalence Server

```bitbake
# Share sstate across teams with hash equivalence
BB_HASHSERVE            = "auto"          # start local server
BB_HASHSERVE_UPSTREAM   = "hashserv.yoctoproject.org:8687"

# Or point to internal server
BB_HASHSERVE = "your-server.example.com:8687"
```

#### Network & Fetch Optimisation

```bitbake
# Shared download cache across users
DL_DIR = "/shared/downloads"

# Shared sstate cache
SSTATE_DIR = "/shared/sstate-cache"

# Mirror downloads from internal server
PREMIRRORS:prepend = " \
  git://.*/.* git://internal.example.com/git/BASENAME;protocol=https \n \
  https?$://.*/.* https://internal.example.com/dl/PATH \n"

BB_FETCH_PREMIRRORONLY = "0"  # fallback to upstream if mirror misses
```

---

### 2.7 Reproducible Builds

Yocto aims for build reproducibility. Key controls:

```bitbake
# Fix locale to avoid locale-dependent output
LC_ALL = "en_US.UTF-8"

# Use SOURCE_DATE_EPOCH for timestamp injection
inherit reproducible_build    # sets SOURCE_DATE_EPOCH = git commit time

# Avoid path embedding
DEBUG_PREFIX_MAP  = "-fdebug-prefix-map=${WORKDIR}=/usr/src/debug/${PN}/${PV}"
BUILD_REPRODUCIBLE_BINARIES = "1"

# Pin SRCREV — never use AUTOREV in production
SRCREV_pn-my-component = "abc123..."
# AUTOREV is forbidden in release builds — use:
# BB_GENERATE_MIRROR_TARBALLS = "1" for source archival
```

#### Build History

```bitbake
INHERIT += "buildhistory"
BUILDHISTORY_COMMIT   = "1"       # git commit each build
BUILDHISTORY_FEATURES = "image package sdk"

# Compare builds
buildhistory-diff HEAD~1 HEAD
```

---

### 2.8 CI/CD Integration

#### Recommended CI Pipeline Structure

```
┌──────────────────────────────────────────────────┐
│ 1. kas checkout          ← resolve layers / SRCREVs
│ 2. kas build             ← incremental BitBake build
│ 3. kas build -- -c cve_check  ← security scan
│ 4. Artefact archival     ← images, SPDX, buildhistory
│ 5. Hardware-in-the-loop  ← deploy + automated tests
└──────────────────────────────────────────────────┘
```

#### GitLab CI Example (with KAS)

```yaml
# .gitlab-ci.yml
variables:
  KAS_WORK_DIR: "${CI_PROJECT_DIR}"
  SSTATE_CACHE: "/shared/sstate"
  DL_DIR: "/shared/downloads"

build:
  stage: build
  image: ghcr.io/siemens/kas/kas:latest
  script:
    - kas build kas/my-product.yml
  artifacts:
    paths:
      - build/tmp/deploy/images/
      - build/tmp/deploy/licenses/
    expire_in: 30 days
  cache:
    key: "${CI_COMMIT_REF_SLUG}"
    paths:
      - build/sstate-cache/
```

#### `BBSERVER` for Distributed Builds

```bash
# Start BitBake server (allows remote task submission)
bitbake --server-only -B 0.0.0.0:8000

# Connect remote cooker
bitbake --remote-server=my-build-host:8000 core-image-minimal
```

---

## 3. Technical Deep Dives

### 3.1 BitBake: Advanced Usage & Internals

#### BitBake Architecture

```
┌─────────────────────────────────────────────────────────┐
│  BitBake                                                │
│  ┌─────────────┐   ┌──────────────┐  ┌──────────────┐  │
│  │  UI Layer   │   │  Cooker      │  │  Fetcher     │  │
│  │ (knotty/    │←→│  (parse,     │  │ (git/http/   │  │
│  │  ncurses/   │  │  schedule,   │  │  svn/…)      │  │
│  │  toaster)   │  │  execute)    │  └──────────────┘  │
│  └─────────────┘  └──────┬───────┘                     │
│                          │                             │
│  ┌───────────────────────▼────────────────────────┐    │
│  │  Task Execution Engine                         │    │
│  │  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │    │
│  │  │ RunQueue │  │ Sstate   │  │  Signature  │  │    │
│  │  │ Scheduler│  │ Manager  │  │  Generator  │  │    │
│  │  └──────────┘  └──────────┘  └─────────────┘  │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

#### Task Dependency Graph

```bitbake
# Inter-recipe task dependencies
DEPENDS = "zlib openssl"       # build-time (do_prepare_recipe_sysroot)
RDEPENDS:${PN} = "libssl3"    # runtime (package manager installs dependency)

# Explicit task dependencies (varflag)
do_compile[depends]      = "virtual/kernel:do_deploy"
do_install[depends]      = "my-codegen-native:do_populate_sysroot"

# Order-only dependencies (no hash impact)
do_configure[after]      = "do_patch"

# deptask — execute a task on all DEPENDS members
do_populate_sysroot[deptask] = "do_populate_sysroot"

# recrdeptask — recursive transitive RDEPENDS traversal
do_rootfs[recrdeptask]   = "do_package_write_rpm"
```

#### Fetcher SRC_URI Schemes

| Scheme | Example |
|---|---|
| `http/https` | `https://example.com/foo-1.2.tar.gz` |
| `git` | `git://github.com/org/repo.git;protocol=https;branch=main` |
| `gitsm` | Git with submodules |
| `svn` | `svn://svn.example.com/repo;module=trunk` |
| `hg` | Mercurial |
| `ftp` | FTP |
| `file` | Local file relative to `FILESEXTRAPATHS` |
| `npm` | `npm://registry.npmjs.org;package=lodash;version=4.17.21` |
| `crate` | Rust crate (via `cargo.bbclass`) |

#### SRC_URI URI Parameters

```bitbake
SRC_URI = " \
  git://github.com/org/repo.git;protocol=https;branch=main;name=src \
  git://github.com/org/submod.git;protocol=https;destsuffix=submod;name=sub \
"
SRCREV_src = "abc123..."
SRCREV_sub = "def456..."

# File fetcher parameters
SRC_URI += "file://my.patch;apply=yes;striplevel=1"
SRC_URI += "file://config;subdir=config-files"
```

#### Python in BitBake Recipes

```bitbake
# Anonymous Python — executed at parse time
python () {
    pv = d.getVar('PV')
    major = pv.split('.')[0]
    d.setVar('MY_MAJOR_VERSION', major)
    if bb.utils.vercmp_string_op(pv, '2.0.0', '>='):
        d.appendVar('PACKAGECONFIG', ' new-feature')
}

# Python task
python do_my_python_task() {
    import json, os
    src = d.getVar('S')
    manifest = os.path.join(src, 'manifest.json')
    with open(manifest) as f:
        data = json.load(f)
    bb.note(f"Component version from manifest: {data['version']}")
}

# Python function called from shell task
def get_make_jobs(d):
    import multiprocessing
    jobs = d.getVar('PARALLEL_MAKE') or ''
    return jobs if jobs else f"-j{multiprocessing.cpu_count()}"

do_compile() {
    oe_runmake ${@get_make_jobs(d)}
}
```

#### Multilib

```bitbake
# local.conf — add 32-bit userspace alongside 64-bit
require conf/multilib.conf
MULTILIBS     = "multilib:lib32"
DEFAULTTUNE:virtclass-multilib-lib32 = "x86"

# Install 32-bit package
IMAGE_INSTALL += "lib32-glibc lib32-zlib"

# Cross-referencing from recipe
MULTILIB_PACKAGES = "${PN}"
```

---

### 3.2 BitBake: Debugging & Introspection

#### Essential Debug Commands

```bash
# Show all layers and priorities
bitbake-layers show-layers

# Show all recipes providing a target
bitbake-layers show-recipes "virtual/kernel"

# Find recipe providing a package
bitbake-layers show-recipes | grep my-package

# Show all overrides active in current config
bitbake -e | grep "^OVERRIDES="

# Dump expanded variable for a recipe
bitbake -e my-recipe | grep "^DEPENDS="
bitbake -e my-recipe | grep "^do_compile\["

# Parse recipes and report errors (no build)
bitbake -p

# Dry-run: show tasks that would execute
bitbake -n core-image-minimal

# Show task signatures (hashinfo)
bitbake-dumpsig -t my-recipe do_compile

# Generate dependency graph
bitbake -g core-image-minimal
# Outputs: pn-buildlist, pn-depends.dot, task-depends.dot
dot -Tsvg task-depends.dot > task-depends.svg
```

#### Task-Level Debugging

```bash
# Run a single task explicitly
bitbake my-recipe -c compile

# Force re-run (invalidate stamp)
bitbake my-recipe -C compile        # rerun compile + all dependents
bitbake my-recipe -f -c compile     # force, don't mark dependents dirty

# Interactive shell in task environment (invaluable for debugging)
bitbake my-recipe -c devshell       # opens shell with task env vars

# Python devpyshell
bitbake my-recipe -c devpyshell     # Python REPL with datastore access (d available)

# List all tasks for a recipe
bitbake -c listtasks my-recipe

# Show package contents
bitbake my-recipe -c package && \
  find tmp/work/*/my-recipe/*/packages-split/ -type f
```

#### Log Locations & Structure

```
tmp/work/<arch>/<recipe>/<ver>/temp/
├── log.do_fetch           ← full stdout/stderr per task
├── log.do_compile
├── log.do_compile.20240501123456  ← timestamped historical log
├── run.do_fetch           ← actual shell script that was executed
└── run.do_compile
```

```bash
# Tail logs during build
tail -f tmp/work/*/my-recipe/*/temp/log.do_compile

# Find failing task log after error
bitbake my-recipe 2>&1 | grep "ERROR:" | grep "log file"
```

#### Signature Mismatch Investigation

```bash
# Compare two signatures to understand why a rebuild occurred
bitbake-diffsigs \
  tmp/stamps/cortexa53-poky-linux/my-recipe/1.0-r0.do_compile.sigdata.old \
  tmp/stamps/cortexa53-poky-linux/my-recipe/1.0-r0.do_compile.sigdata

# With --debug flag for verbose output
bitbake-diffsigs --debug sigdata.old sigdata.new

# Reproduce what a task hash covers
bitbake-dumpsig -t my-recipe do_compile | head -100
```

#### `oe-pkgdata-util` — Package Database Queries

```bash
# Which recipe installs a file?
oe-pkgdata-util find-path /usr/bin/my-binary

# What packages does a recipe produce?
oe-pkgdata-util list-packages my-recipe

# What files are in a package?
oe-pkgdata-util list-pkg-files my-package

# What are the runtime dependencies of a package?
oe-pkgdata-util read-value RDEPENDS my-package
```

---

### 3.3 BitBake: Customisation & Extension

#### Custom BitBake Class

```bitbake
# meta-my-product/classes/my-cmake-extra.bbclass

DEPENDS:append = " my-codegen-native"

# Add default CMake variables for our platform
EXTRA_OECMAKE:append = " \
    -DMY_PLATFORM=1 \
    -DMY_SDK_DIR=${STAGING_DIR_TARGET}/usr \
"

# Override the configure task
do_configure:prepend() {
    # Generate a version header before cmake runs
    cat > ${S}/src/version.h << EOF
#define VERSION_STRING "${PV}"
#define BUILD_DATE "$(date -u +%Y-%m-%d)"
EOF
}

# Custom QA check
python do_my_qa_check() {
    import os
    d_dir = d.getVar('D')
    forbidden = os.path.join(d_dir, 'usr/lib/debug')
    if os.path.exists(forbidden):
        bb.warn(f"Debug symbols found in production package. Remove or use dbg split.")
}

addtask my_qa_check after do_install before do_package
```

#### Custom Fetcher

```python
# meta-my-product/lib/bb/fetch2/myproto.py
# Register via: BBPATH plugin mechanism

import bb.fetch2

class MyProtoFetcher(bb.fetch2.FetchMethod):
    def supports(self, ud, d):
        return ud.type == "myproto"

    def download(self, ud, d):
        # implement download logic
        pass

    def checkstatus(self, fetch, ud, d):
        pass
```

#### Custom Parser / Variable Handler

```python
# meta-my-product/lib/oe/my_utils.py
import bb

def validate_required_vars(d, varlist):
    """Raise an error if any required variable is unset."""
    for var in varlist:
        if not d.getVar(var):
            bb.fatal(f"Required variable {var} is not set")

def expand_machine_config(d):
    """Merge machine-specific JSON config into BitBake variables."""
    import json, os
    cfg_file = d.getVar('MACHINE_CONFIG_FILE')
    if not cfg_file or not os.path.exists(cfg_file):
        return
    with open(cfg_file) as f:
        cfg = json.load(f)
    for k, v in cfg.items():
        d.setVar(k, str(v))
```

#### `PACKAGECONFIG` Pattern

```bitbake
# Declare feature flags with: "args_if_enabled" "args_if_disabled" "depends_if_on" "rdepends_if_on"
PACKAGECONFIG ??= "ssl compression"

PACKAGECONFIG[ssl]         = "--enable-ssl,--disable-ssl,openssl,libssl3"
PACKAGECONFIG[compression] = "--with-zlib,--without-zlib,zlib,libz1"
PACKAGECONFIG[debug]       = "--enable-debug,--disable-debug,,"

# Enabling/disabling from distro or local.conf
PACKAGECONFIG:pn-my-app = "ssl"                # exact set
PACKAGECONFIG:append:pn-my-app = " debug"      # add one
PACKAGECONFIG:remove:pn-my-app = "compression" # remove one
```

#### Native, NativeSdk, and Cross Recipes

```bitbake
# Native recipe — builds a tool to run on the build host
inherit native
# Recipe name convention: my-tool-native (auto via BBCLASSEXTEND)

# OR extend an existing recipe:
BBCLASSEXTEND = "native nativesdk"
# Creates: my-tool (target), my-tool-native (host), my-tool-nativesdk (SDK host)

# Cross recipe — compiler that runs on host, produces target code
inherit cross
# Typically only used for toolchain recipes (gcc, binutils, etc.)
```

#### Recipe `PACKAGES` Splitting

```bitbake
PACKAGES = "${PN}-bin ${PN}-lib ${PN}-dev ${PN}-doc ${PN}-dbg ${PN}"

# File assignments — first match wins
FILES:${PN}-bin = "${bindir}/my-app"
FILES:${PN}-lib = "${libdir}/libmy*.so.*"
FILES:${PN}-dev = "${includedir} ${libdir}/libmy*.so ${libdir}/pkgconfig"
FILES:${PN}-doc = "${docdir} ${mandir}"
FILES:${PN}-dbg = "${bindir}/.debug ${libdir}/.debug"
FILES:${PN}     = ""    # catch-all

RDEPENDS:${PN}-bin = "${PN}-lib"
RRECOMMENDS:${PN} = "${PN}-doc"
RCONFLICTS:${PN} = "old-my-app"
RPROVIDES:${PN} = "virtual-my-app"
```

---

### 3.4 KAS: Configuration & Workflows

#### What KAS Is

**KAS** (Karlsruhe Application Setup) is a setup tool for BitBake-based projects. It solves the "layer management" problem: rather than manually cloning and versioning all layers, KAS declares everything in a single YAML manifest and handles fetching, patching, and BitBake invocation.

```
kas/my-product.yml           ← primary manifest
kas/common.yml               ← shared base (included by primary)
kas/ci-overrides.yml         ← CI-specific overrides
```

#### Manifest Anatomy

```yaml
# kas/my-product.yml
header:
  version: 14            # KAS manifest format version
  includes:
    - common.yml         # relative path within repo

machine: mymachine
distro:  my-distro
target:  core-image-full-cmdline
env:
  - SSTATE_DIR:/shared/sstate   # pass env to BitBake

repos:
  # The main repo containing this file
  meta-my-product:
    path: .
    layers:
      meta-my-bsp:
        # sub-layer within same repo

  # External repos — KAS clones and checks out
  poky:
    url: https://git.yoctoproject.org/poky
    refspec: scarthgap
    layers:
      meta:
      meta-poky:
      meta-yocto-bsp:

  meta-openembedded:
    url: https://github.com/openembedded/meta-openembedded.git
    refspec: scarthgap
    layers:
      meta-oe:
      meta-networking:
      meta-filesystems:

  meta-security:
    url: https://git.yoctoproject.org/meta-security
    refspec: scarthgap

bblayers_conf_header:
  standard: |
    POKY_BBLAYERS_CONF_VERSION = "2"

local_conf_header:
  standard: |
    CONF_VERSION = "2"
    DL_DIR       = "/shared/downloads"
    SSTATE_DIR   = "/shared/sstate"
    BB_NUMBER_THREADS = "16"
    PARALLEL_MAKE = "-j16"
```

#### `common.yml` — Shared Base Manifest

```yaml
# kas/common.yml
header:
  version: 14

repos:
  poky:
    url: https://git.yoctoproject.org/poky
    refspec: scarthgap
    layers:
      meta:
      meta-poky:

local_conf_header:
  standard: |
    INHERIT += "rm_work buildhistory create-spdx"
    BUILDHISTORY_COMMIT = "1"
```

#### KAS CLI Reference

```bash
# Checkout all layers (no build)
kas checkout kas/my-product.yml

# Build
kas build kas/my-product.yml

# Build with a secondary overlay config (configs are merged)
kas build kas/my-product.yml:kas/ci-overrides.yml

# Run arbitrary BitBake command
kas shell kas/my-product.yml -c "bitbake -e my-recipe | grep ^DEPENDS="

# Interactive shell in configured environment
kas shell kas/my-product.yml

# Build a specific task
kas build kas/my-product.yml -- -c compile my-recipe

# Run with custom environment variable
kas build kas/my-product.yml -- --cmd "bitbake core-image-minimal -c cve_check"

# Show effective configuration (merged from all includes)
kas dump kas/my-product.yml

# Lock all SRCREVs to current HEAD (create a lock file)
kas lock kas/my-product.yml
# Outputs: kas/my-product.lock.yml — commit this for reproducibility!
```

---

### 3.5 KAS: Advanced Integration

#### KAS Lock Files for Reproducibility

```bash
# Generate lock file pinning all repo HEADs
kas lock kas/my-product.yml --output kas/my-product.lock.yml

# Build from lock file (CI — fully reproducible)
kas build kas/my-product.yml:kas/my-product.lock.yml
```

```yaml
# kas/my-product.lock.yml (auto-generated, commit to VCS)
header:
  version: 14
overrides:
  repos:
    poky:
      refspec: "abc123def456..."     # pinned SHA
    meta-openembedded:
      refspec: "789abc012def..."
    meta-security:
      refspec: "feedbeef1234..."
```

#### Environment-Specific Overlay Configs

```yaml
# kas/debug.yml — merge over primary for debug builds
header:
  version: 14

local_conf_header:
  debug: |
    IMAGE_FEATURES += "debug-tweaks tools-debug tools-profile"
    EXTRA_IMAGE_FEATURES += "ssh-server-openssh"
    PACKAGECONFIG:append:pn-gdb = " python"
```

```bash
# Debug build
kas build kas/my-product.yml:kas/debug.yml

# Release build (no overlay)
kas build kas/my-product.yml:kas/my-product.lock.yml
```

#### KAS in Docker (Hermetic Builds)

```dockerfile
# Dockerfile.kas
FROM ghcr.io/siemens/kas/kas:4.2

# Add project-specific tools
RUN pip3 install west

USER user
WORKDIR /work
```

```bash
# Run KAS entirely inside Docker
docker run --rm \
  -v "${PWD}:/work" \
  -v "/shared/sstate:/shared/sstate" \
  -v "/shared/downloads:/shared/downloads" \
  -e "USER_ID=$(id -u)" \
  ghcr.io/siemens/kas/kas:4.2 \
  build kas/my-product.yml
```

#### Patch Application via KAS

```yaml
# kas/my-product.yml
repos:
  poky:
    url: https://git.yoctoproject.org/poky
    refspec: scarthgap
    patches:
      - repo: meta-my-product      # patch sourced from this repo
        path: patches/poky/0001-fix-signing.patch
```

#### KAS Plugin API (Python Extension)

```python
# kas_plugins/my_plugin.py
from kas.plugins import Plugin

class MyPlugin(Plugin):
    name = "my-plugin"

    def setup_parser(self, parser):
        parser.add_argument('--my-option', help='Custom option')

    def run(self, args):
        # Access KAS context
        ctx = self.get_context()
        bb.plain(f"Running with machine: {ctx.config.get_machine()}")
```

```bash
# Invoke plugin
kas my-plugin kas/my-product.yml --my-option foo
```

#### KAS Multi-Target Matrix Build (CI)

```bash
#!/usr/bin/env bash
# build-matrix.sh
set -euo pipefail

CONFIGS=(
  "kas/machine-a.yml:kas/my-product.lock.yml"
  "kas/machine-b.yml:kas/my-product.lock.yml:kas/debug.yml"
  "kas/machine-c.yml:kas/my-product.lock.yml"
)

for cfg in "${CONFIGS[@]}"; do
  echo "=== Building: $cfg ==="
  kas build "$cfg" -- core-image-minimal
done
```

---

## Quick-Reference Appendix

### Yocto Release Codename Map

| Codename | Version | LTS |
|---|---|---|
| Mickledore | 4.2 | — |
| Nanbield | 4.3 | — |
| Scarthgap | 5.0 | ✅ |
| Styhead | 5.1 | — |
| Walnascar | 5.2 | — |

### Critical `local.conf` Variables Cheatsheet

```bitbake
MACHINE          = "qemux86-64"
DISTRO           = "poky"
PACKAGE_CLASSES  = "package_rpm"
EXTRA_IMAGE_FEATURES ?= "debug-tweaks"
BB_NUMBER_THREADS = "8"
PARALLEL_MAKE     = "-j8"
DL_DIR            = "${TOPDIR}/../downloads"
SSTATE_DIR        = "${TOPDIR}/../sstate-cache"
TMPDIR            = "${TOPDIR}/tmp"
# GPU / graphics
DISTRO_FEATURES:append = " opengl wayland"
# Reduce build output verbosity
BB_CONSOLELOG     = "${TMPDIR}/cooker/${MACHINE}/console.log"
```

### `devtool` Cheatsheet

```bash
devtool add <name> <url>                # create recipe from source
devtool modify <recipe>                 # checkout source for editing
devtool build <recipe>                  # build in workspace
devtool deploy-target <recipe> <target> # rsync to running target
devtool undeploy-target <recipe> <tgt>  # remove from target
devtool finish <recipe> <layer>         # write back to layer
devtool upgrade <recipe>                # bump to newer upstream
devtool reset <recipe>                  # remove from workspace
devtool search <keyword>                # find recipes
devtool status                          # show workspace state
```

### `bitbake-layers` Cheatsheet

```bash
bitbake-layers show-layers              # list layers + priority
bitbake-layers show-recipes             # all recipes
bitbake-layers show-recipes <pattern>   # filtered
bitbake-layers show-overlayed           # recipes overridden by .bbappend
bitbake-layers show-cross-depends       # inter-layer dependencies
bitbake-layers flatten <output>         # merge all layers (for analysis)
bitbake-layers add-layer <path>         # add to bblayers.conf
bitbake-layers remove-layer <name>      # remove from bblayers.conf
bitbake-layers create-layer <path>      # scaffold new layer
```

### Common `IMAGE_FEATURES` Reference

| Feature | Effect |
|---|---|
| `debug-tweaks` | Sets root password to empty, allows passwordless SSH |
| `read-only-rootfs` | Mount rootfs read-only at boot |
| `ssh-server-openssh` | Install and enable OpenSSH |
| `ssh-server-dropbear` | Install and enable Dropbear SSH |
| `tools-debug` | gdb, strace, ltrace |
| `tools-profile` | perf, oprofile, lttng |
| `tools-sdk` | Development tools + headers on target |
| `nfs-server` | Install and enable NFS server |
| `package-management` | Include package manager in image |
| `splash` | Plymouth boot splash |
| `hwcodecs` | Hardware codec support (machine-dependent) |

### Common `DISTRO_FEATURES` Reference

| Feature | Enables |
|---|---|
| `systemd` | systemd init (requires `INIT_MANAGER = "systemd"`) |
| `wayland` | Wayland display protocol support |
| `opengl` | OpenGL/EGL support |
| `bluetooth` | BlueZ + kernel Bluetooth |
| `wifi` | Wireless LAN kernel + tools |
| `pam` | Pluggable Authentication Modules |
| `pci` | PCI bus support |
| `usb` | USB subsystem |
| `nfs` | NFS client/server |
| `largefile` | `_FILE_OFFSET_BITS=64` for >2 GiB file support |
| `security` | Security compiler flags (SSP, etc.) |
| `ima` | Integrity Measurement Architecture |
| `selinux` | SELinux MAC framework |
| `usrmerge` | Merged-usr filesystem layout |
| `multiarch` | Multi-arch support (x86_64 with i386) |

---

*Generated for Yocto Project expert-level reference. Covers Kirkstone / Scarthgap / Styhead. Always consult the [Yocto Project Reference Manual](https://docs.yoctoproject.org/ref-manual/) for the authoritative specification of your target release.*

# Yocto Project — 200 Expert Q&A Interview Guide

> **Audience:** Yocto architects, senior embedded Linux engineers, and technical interview candidates.
> **Scope:** Fundamental → Advanced. All answers reflect best practices current through Yocto 5.x (Scarthgap / Styhead).

---

## Table of Contents

1. [Yocto Project Basics](#1-yocto-project-basics) — Q1–Q20
2. [BitBake Internals](#2-bitbake-internals) — Q21–Q45
3. [Layer Management](#3-layer-management) — Q46–Q60
4. [Recipe Writing & Customization](#4-recipe-writing--customization) — Q61–Q85
5. [Build System Optimization](#5-build-system-optimization) — Q86–Q100
6. [Debugging & Troubleshooting](#6-debugging--troubleshooting) — Q101–Q120
7. [KAS Workflows](#7-kas-workflows) — Q121–Q135
8. [Embedded Linux Integration](#8-embedded-linux-integration) — Q136–Q155
9. [Security & Compliance](#9-security--compliance) — Q156–Q175
10. [Advanced Use Cases](#10-advanced-use-cases) — Q176–Q200

---

## 1. Yocto Project Basics

---

### Q1. What is the Yocto Project, and how does it differ from a Linux distribution?

**Answer:**

The Yocto Project is an open-source collaboration project hosted by the Linux Foundation that provides a flexible set of tools, templates, and processes for creating custom embedded Linux distributions. It is **not a distribution itself** — it is a *meta-framework* for building distributions.

Key distinctions:

| Aspect | Yocto Project | Binary Distribution (e.g., Ubuntu) |
|---|---|---|
| Output | Custom-built image for a target | Pre-built packages for generic hardware |
| Package source | Everything compiled from source | Pre-compiled binaries |
| Customization | Full control over every component | Limited; relies on package manager |
| Target | Embedded / resource-constrained systems | General-purpose desktops/servers |
| Reproducibility | Bit-for-bit reproducible builds | Updates change installed system |

Yocto produces a complete, minimal Linux image tailored to a specific board and application, which is essential in embedded systems where image size, boot time, and hardware specificity matter.

---

### Q2. What is Poky, and what is its relationship to the Yocto Project and OpenEmbedded?

**Answer:**

**Poky** is the Yocto Project's reference distribution. It is a working example of a distribution built on top of the OpenEmbedded build system. Poky includes:

- **BitBake** — the task execution engine
- **OpenEmbedded-Core (OE-Core / `meta`)** — the core recipe set maintained jointly by Yocto and OE
- **`meta-poky`** — Poky-specific distribution configuration
- **`meta-yocto-bsp`** — BSP for QEMU and a few reference boards

The relationship:

```
Yocto Project (umbrella project / governance)
    └── Poky (reference distro = bitbake + OE-Core + meta-poky + meta-yocto-bsp)
            └── OpenEmbedded-Core (shared core recipes)
                    └── OpenEmbedded (wider community layer ecosystem)
```

In practice, most production projects do **not** use Poky's distro configuration. They use Poky as a starting point and create their own `meta-<product>-distro` layer that `require`s or replaces `poky.conf`.

---

### Q3. Explain the core components of the Yocto build system.

**Answer:**

| Component | Role |
|---|---|
| **BitBake** | Task execution engine; parses recipes, resolves dependencies, runs tasks |
| **Metadata** | Recipes (`.bb`), classes (`.bbclass`), configs (`.conf`), appends (`.bbappend`) |
| **OE-Core** | Foundational recipe set: toolchain, libc, BusyBox, systemd, basic packages |
| **Layers** | Modular collections of metadata organized by concern (BSP, distro, application) |
| **TMPDIR** | Working directory: source, build artefacts, staging, packages, images |
| **DL_DIR** | Persistent download cache, shared across builds |
| **SSTATE_DIR** | Shared-state cache; stores task outputs for reuse across builds |
| **`conf/` directory** | `bblayers.conf` (active layers) + `local.conf` (user overrides) |

---

### Q4. What is the difference between `MACHINE`, `DISTRO`, and `IMAGE` in Yocto?

**Answer:**

These three variables define orthogonal dimensions of a Yocto build:

- **`MACHINE`** — defines the **hardware target**. Set in a BSP layer. Controls CPU architecture (`DEFAULTTUNE`), kernel recipe (`PREFERRED_PROVIDER_virtual/kernel`), bootloader, device tree files, and any hardware-specific packages.

- **`DISTRO`** — defines the **software policy**. Set in a distro layer. Controls init system (`INIT_MANAGER`), C library (`TCLIBC`), package format (`PACKAGE_CLASSES`), global compiler flags, and enabled `DISTRO_FEATURES`.

- **IMAGE** — defines the **root filesystem composition**. An image recipe (e.g., `core-image-minimal.bb`) lists which packages and package groups to install, the filesystem types to generate, and image-level features.

The separation is intentional: you can combine any `MACHINE` with any `DISTRO` and build any `IMAGE`, as long as the combinations are compatible.

---

### Q5. What is a Yocto layer, and why is the layer model important?

**Answer:**

A **layer** is a directory (conventionally named `meta-<name>`) that contains a structured collection of metadata: recipes, classes, configuration files, and append files. The layer model is important for:

1. **Separation of concerns** — BSP, distro policy, application logic, and security hardening each live in dedicated layers.
2. **Reusability** — a BSP layer for a SoC can be shared across products; an application layer can be used with multiple distros.
3. **Maintainability** — upstream layers (OE-Core, meta-openembedded) can be updated independently of custom layers.
4. **Non-invasive customization** — `.bbappend` files allow modification of upstream recipes without forking them.
5. **Priority-based override** — higher-priority layers transparently override lower-priority ones.

A minimal layer requires:
```
meta-my-layer/
├── conf/
│   └── layer.conf        ← mandatory: registers the layer with BitBake
└── recipes-*/
    └── */*.bb
```

---

### Q6. Explain the difference between `SRC_URI`, `SRCREV`, and `S` variables.

**Answer:**

- **`SRC_URI`** — a space-separated list of URIs that BitBake's fetcher uses to download source code, patches, and auxiliary files. Supports multiple schemes: `https://`, `git://`, `file://`, `npm://`, etc.

- **`SRCREV`** — the specific revision to check out when fetching a Git (or SVN/Hg) repository. Must be a full commit SHA in production builds. Using `AUTOREV` (`SRCREV = "${AUTOREV}"`) is forbidden in release builds as it makes builds non-reproducible.

- **`S`** — the path where the fetcher unpacks the source code. For tarballs it defaults to `${WORKDIR}/${BPN}-${PV}`. For git fetches it defaults to `${WORKDIR}/git`. You must set `S` correctly if your source unpacks to a non-standard directory.

```bitbake
SRC_URI = "git://github.com/example/myapp.git;protocol=https;branch=main"
SRCREV  = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
S       = "${WORKDIR}/git"
```

---

### Q7. What are `DEPENDS` and `RDEPENDS`, and why is the distinction critical?

**Answer:**

- **`DEPENDS`** — **build-time** dependencies. Lists recipes whose `do_populate_sysroot` task must complete before this recipe's `do_configure` begins. These are tools and libraries needed to *compile* the software. They are **not** installed into the final image unless also listed in `RDEPENDS` or `IMAGE_INSTALL`.

- **`RDEPENDS:${PN}`** — **runtime** dependencies. Lists packages (not recipes) that must be present on the target when this package is installed. The package manager resolves these at image construction time or on-target install.

```bitbake
DEPENDS = "zlib openssl libpng"            # build host needs these headers/libs
RDEPENDS:${PN} = "libssl3 libpng16-0"     # target image needs these .so files
```

**Critical mistake to avoid:** listing a recipe in `DEPENDS` but not the corresponding package in `RDEPENDS` means the binary links correctly during build but crashes at runtime with "library not found". Conversely, listing something only in `RDEPENDS` causes a build failure because the headers/libraries are not in the sysroot.

---

### Q8. What is the purpose of `virtual/` providers in Yocto?

**Answer:**

`virtual/` is a **virtual provider namespace** that decouples a *capability* from its *implementation*. Any recipe can declare:

```bitbake
PROVIDES += "virtual/kernel"
```

Consumers depend on the capability:

```bitbake
DEPENDS = "virtual/kernel"
```

The actual provider is selected via:

```bitbake
PREFERRED_PROVIDER_virtual/kernel = "linux-imx"
```

Common virtual providers:

| Virtual | Default provider | Common alternatives |
|---|---|---|
| `virtual/kernel` | `linux-yocto` | `linux-imx`, `linux-ti-staging` |
| `virtual/bootloader` | `u-boot` | `u-boot-imx`, `u-boot-ti` |
| `virtual/libc` | `glibc` | `musl`, `newlib` |
| `virtual/libintl` | `glibc` | `gettext` |
| `virtual/xserver` | `xserver-xorg` | — |
| `virtual/egl` | `mesa` | SoC-specific GPU driver |

This allows a BSP layer to swap the kernel or GPU driver without touching application recipes.

---

### Q9. What is `WORKDIR`, `D`, `S`, and `B` in a recipe context?

**Answer:**

| Variable | Meaning | Default |
|---|---|---|
| `WORKDIR` | Per-recipe working directory root | `${TMPDIR}/work/<arch>/<PN>/<PV>-<PR>` |
| `S` | Source directory (unpacked) | `${WORKDIR}/${BPN}-${PV}` |
| `B` | Build directory (where `configure`/`cmake` runs) | `${S}` (same as S unless set otherwise) |
| `D` | Destination/install directory (DESTDIR equivalent) | `${WORKDIR}/image` |

**Workflow:**
1. `do_unpack` → populates `S`
2. `do_configure` → runs in `B`, reads from `S`
3. `do_compile` → runs in `B`
4. `do_install` → installs from `B` into `D`
5. `do_package` → reads `D`, splits into `${WORKDIR}/packages-split/`

Separating `B` from `S` (out-of-tree builds) is a best practice for CMake/Autotools projects:
```bitbake
B = "${WORKDIR}/build"
```

---

### Q10. Explain `IMAGE_FEATURES` vs `EXTRA_IMAGE_FEATURES`.

**Answer:**

Both variables compose the set of features for an image recipe, but they differ in scope and intended use:

- **`IMAGE_FEATURES`** — set directly inside the image recipe (`.bb` file). Defines the canonical feature set for that image.
- **`EXTRA_IMAGE_FEATURES`** — set in `local.conf` or distro config. Appended to `IMAGE_FEATURES` without modifying the recipe. Useful for developer additions (debug tools, SSH) that must not pollute production images.

```bitbake
# In core-image-minimal.bb
IMAGE_FEATURES += "read-only-rootfs"

# In local.conf (developer workstation only)
EXTRA_IMAGE_FEATURES = "debug-tweaks ssh-server-openssh tools-debug"
```

Features map to:
1. **Package group inclusions** (e.g., `tools-debug` → `packagegroup-core-tools-debug`)
2. **Class behaviours** (e.g., `read-only-rootfs` → `read-only-rootfs.bbclass` post-processing)

In CI/production pipelines, `EXTRA_IMAGE_FEATURES` should be empty or absent.

---

### Q11. What is `DISTRO_FEATURES` and how does it affect the build?

**Answer:**

`DISTRO_FEATURES` is a list of string tokens that recipes check to conditionally include or exclude functionality. It acts as a **global feature flag register** for the distribution.

```bitbake
DISTRO_FEATURES = "acl alsa argp bluetooth ext2 ipv4 ipv6 largefile \
                   nfs pci usbgadget usbhost wifi xattr zeroconf \
                   pam systemd security opengl wayland"
```

Recipes interrogate it via:
```bitbake
# In a recipe
PACKAGECONFIG:append = "${@bb.utils.contains('DISTRO_FEATURES', 'bluetooth', 'bluez', '', d)}"
```

Or via class guards:
```bitbake
# Only install udev rules if systemd is in distro features
do_install:append() {
    if ${@bb.utils.contains('DISTRO_FEATURES', 'systemd', 'true', 'false', d)}; then
        install -d ${D}${systemd_unitdir}/system
        install -m 0644 ${WORKDIR}/my.service ${D}${systemd_unitdir}/system/
    fi
}
```

**Best practice:** prune `DISTRO_FEATURES` aggressively in production. Every enabled feature adds potential attack surface and image size. Only enable what the product requires.

---

### Q12. What is the `PR` variable and when should it be bumped?

**Answer:**

`PR` (Package Revision) is a string (default `"r0"`) appended to the package version to indicate a **packaging change that doesn't change the upstream source version**.

Bump `PR` when:
- A `.bbappend` modifies the package split, `FILES`, or `RDEPENDS` without changing the source
- A patch is added or removed without changing `PV`
- `CONFFILES` or `RCONFLICTS` changes

**Do not** bump `PR` when:
- Upstream source version changes (bump `PV` instead, which resets `PR` to `r0`)
- Build system variables change (sstate handles this via hash invalidation automatically)

In modern Yocto with sstate, `PR` bumping is less critical for local builds because the hash mechanism handles rebuilds. However, it **is** critical when distributing binary packages via a package feed server — package managers use `PR` to determine upgrade order.

For package feeds, use the **PR service** (`bitbake-prserv`) to auto-increment `PR` consistently across a team.

---

### Q13. What is the difference between `inherit`, `require`, and `include`?

**Answer:**

| Directive | Target | Failure if missing |
|---|---|---|
| `inherit <class>` | `.bbclass` file (searched in `BBPATH`) | Fatal error |
| `require <file>` | Any `.bb`, `.inc`, `.conf` (relative or absolute path) | Fatal error |
| `include <file>` | Any file | **Silent** — no error if file is absent |

```bitbake
inherit autotools pkgconfig systemd   # load bbclasses
require recipes-core/images/core-image-base.bb  # must exist
include conf/optional-overrides.conf  # silently skipped if absent
```

**`include` use case:** conditionally present configuration files. A `local.conf` might `include site.conf` which may or may not exist per-developer.

**`inherit` search path:** BitBake searches for `<class>.bbclass` in `classes/` and `classes-recipe/` subdirectories of all paths in `BBPATH`.

---

### Q14. Explain the Yocto release cadence and LTS policy.

**Answer:**

Yocto follows a roughly **6-month release cycle**, aligned with the upstream kernel's long-term support schedule:

- **LTS releases** occur approximately every 2 years and receive **2 years of maintenance** (security fixes, critical bug patches). From Kirkstone onwards, LTS duration extended to **4 years** for commercial adopters.
- **Non-LTS releases** receive maintenance only until the next release (~6 months).

| Codename | Version | LTS | EOL |
|---|---|---|---|
| Kirkstone | 4.0 | ✅ | 2026 |
| Langdale | 4.1 | — | 2023 |
| Mickledore | 4.2 | — | 2023 |
| Nanbield | 4.3 | — | 2024 |
| Scarthgap | 5.0 | ✅ | 2028 |
| Styhead | 5.1 | — | ~2025 |

**Production recommendation:** always target an LTS release for new products. Specify `LAYERSERIES_COMPAT_<layer>` in every custom layer to prevent accidental use across incompatible releases.

---

### Q15. What are `PACKAGES`, `FILES`, and how does package splitting work?

**Answer:**

After `do_install` populates `${D}`, the `do_package` task splits the contents into individual packages defined by the `PACKAGES` variable.

```bitbake
PACKAGES = "${PN}-staticdev ${PN}-dev ${PN}-doc ${PN}-locale ${PN}-dbg ${PN}"
```

`FILES:<pkg>` assigns filesystem paths to each package. **First match wins** — BitBake assigns each file to the first package whose `FILES` pattern matches it.

```bitbake
FILES:${PN}-dev     = "${includedir} ${libdir}/*.so ${libdir}/pkgconfig"
FILES:${PN}-staticdev = "${libdir}/*.a"
FILES:${PN}-doc     = "${docdir} ${mandir} ${infodir}"
FILES:${PN}-dbg     = "${bindir}/.debug ${libdir}/.debug /usr/src/debug"
FILES:${PN}         = "${bindir} ${libdir}/*.so.*"  # runtime package
```

The `dbg` and `dev` packages are conventional. Automatically handled by `package.bbclass`:
- `-dbg`: debug symbols, placed in `.debug/` directories
- `-dev`: headers, `.so` symlinks, pkg-config files
- `-staticdev`: `.a` static libraries
- `-doc`: documentation

**QA check `installed-vs-shipped`** fails if files in `D` are not claimed by any package, which catches mis-configured `FILES`.

---

### Q16. What is `BBFILE_COLLECTIONS`, and what happens if two layers have the same name?

**Answer:**

`BBFILE_COLLECTIONS` is the registry of layer collection names. Each `layer.conf` adds an entry:

```bitbake
BBFILE_COLLECTIONS += "my-product"
BBFILE_PATTERN_my-product = "^${LAYERDIR}/"
BBFILE_PRIORITY_my-product = "10"
```

If two layers declare the **same collection name**, BitBake raises a parse error. This is a common issue when copying a `layer.conf` from another layer without renaming the collection. Always ensure the collection name is unique across all active layers.

To audit:
```bash
bitbake-layers show-layers | grep -E "^layer"
```

---

### Q17. What is `BBMASK` and when should it be used?

**Answer:**

`BBMASK` is a regular expression (or list of regexes) that causes BitBake to **ignore matching recipe files** entirely — as if they don't exist.

```bitbake
# Prevent parsing an unwanted recipe from an upstream layer
BBMASK += "meta-openembedded/meta-networking/recipes-connectivity/avahi/avahi_.*\.bb$"

# Mask an entire subdirectory
BBMASK += "meta-multimedia/recipes-multimedia/gstreamer/"
```

**Use cases:**
- Excluding a recipe that conflicts with a custom one in a higher-priority layer
- Disabling a large recipe tree you have no intention of building (speeds up parsing)
- Temporarily disabling broken upstream recipes during development

**Caution:** `BBMASK` is a blunt instrument. If another recipe `DEPENDS` on the masked one, the build will fail. Prefer `PREFERRED_PROVIDER` or `.bbappend` overrides when possible.

---

### Q18. What is the `TMPDIR` and what is safe to delete vs. what should be preserved?

**Answer:**

`TMPDIR` (default `${TOPDIR}/tmp`) is the complete build working directory. Its contents:

| Path | Safe to delete? | Notes |
|---|---|---|
| `tmp/work/<arch>/` | ✅ (with `rm_work` or manually) | Rebuilt on demand; sstate rehydrates |
| `tmp/deploy/images/` | ✅ | Rebuilt from sstate |
| `tmp/deploy/licenses/` | ✅ | Rebuilt |
| `tmp/stamps/` | ⚠️ Partial | Deleting forces full rebuild even with sstate |
| `tmp/sstate-cache/` | ⚠️ Keep if local sstate | Valuable; move elsewhere before wiping TMPDIR |
| `tmp/pkgdata/` | ✅ | Rebuilt from sstate |

**Never delete** `DL_DIR` casually — it contains downloaded source tarballs. Loss requires re-downloading, which is slow and may fail if upstream URLs change.

**Safe full-rebuild:** `rm -rf tmp/` (if `SSTATE_DIR` is outside `TMPDIR`) preserves sstate, so the rebuild is fast.

---

### Q19. Explain `do_populate_sysroot` and the sysroot mechanism.

**Answer:**

The sysroot is the directory tree that makes a recipe's headers and libraries available to other recipes during compilation, without polluting the global build environment.

**Flow:**
1. `do_install` → installs files into `${D}` (the recipe's own image directory)
2. `do_populate_sysroot` → selectively copies files from `${D}` into the **shared sysroot** at `${STAGING_DIR_TARGET}` (for target recipes) or `${STAGING_DIR_NATIVE}` (for native recipes)
3. Consuming recipes get a **recipe-specific sysroot** at `${WORKDIR}/recipe-sysroot` populated from the shared sysroot via `do_prepare_recipe_sysroot`

What gets staged is controlled by:
```bitbake
SYSROOT_DIRS = "${includedir} ${libdir} ${base_libdir} \
                ${nonarch_base_libdir} ${datadir}/pkgconfig"
```

This isolation means a recipe cannot accidentally pick up headers from packages it didn't declare in `DEPENDS`, preventing hidden dependency bugs.

---

### Q20. What is `OVERRIDES` and how does it drive conditional metadata?

**Answer:**

`OVERRIDES` is a colon-separated string that BitBake uses to **resolve conditional variable assignments**. Any token in `OVERRIDES` can be used as a suffix to conditionally apply a variable.

```bitbake
# Automatically populated by BitBake from MACHINE, DISTRO, TARGET_OS, etc.
OVERRIDES = "cortexa53:armv8a:arm:x86:mx8:poky:linux:my-distro:..."

# Usage in recipe — only applies when MACHINE = "imx8mmevk"
SRC_URI:append:imx8mmevk = " file://imx8mm-fixup.patch"

# Distro-conditional feature
PACKAGECONFIG:append:my-distro = " extra-feature"
```

Key contributors to `OVERRIDES`:
- `${MACHINE}` — machine name
- `${DISTRO}` — distro name
- `${TARGET_OS}` — e.g., `linux`, `linux-gnueabi`
- `${MACHINEOVERRIDES}` — machine-specific override chain (e.g., `mx8mm:mx8:use-mainline-bsp`)
- Custom tokens added via `OVERRIDES:append = ":my-token"`

BitBake evaluates all overrides and selects the **most specific** match. The full evaluation order (lowest to highest precedence): base value → `??=` → `?=` → `=` → `+=`/`.=` → conditional overrides → `:append`/`:prepend`/`:remove`.

---

## 2. BitBake Internals

---

### Q21. Describe the BitBake execution pipeline from invocation to task completion.

**Answer:**

```
bitbake <target>
    │
    ├─ 1. Configuration parsing
    │      Read bblayers.conf → discover layers
    │      Read local.conf + distro.conf + machine.conf
    │      Build global datastore
    │
    ├─ 2. Recipe parsing
    │      Parse all .bb files in BBFILES (parallel, BB_NUMBER_PARSE_THREADS)
    │      Apply .bbappend files
    │      Expand all variables, evaluate python functions
    │      Build per-recipe datastores
    │
    ├─ 3. Dependency resolution
    │      Build task dependency graph (RunQueue)
    │      Topological sort (Kahn's algorithm)
    │      Identify tasks eligible for sstate restoration
    │
    ├─ 4. Signature generation
    │      Compute taskhash for every task
    │      Query sstate cache + hash equivalence server
    │
    ├─ 5. Task execution (worker processes)
    │      setscene tasks first (restore from sstate)
    │      Real tasks for sstate misses
    │      Pseudo intercepts file operations
    │
    └─ 6. Deployment
           Packages → package feeds
           Image assembly (do_rootfs, do_image_*)
           Artefacts → tmp/deploy/images/
```

---

### Q22. How does the sstate (shared-state) cache work internally?

**Answer:**

The sstate cache is a **content-addressable store** of task outputs, keyed by a **taskhash** — a hash of all inputs that influence the task.

**Taskhash computation inputs:**
- Recipe file content (after variable expansion)
- Class content for all inherited classes
- Values of all variables accessed during the task
- Task function source code
- Checksums of input files (e.g., patches, source tarballs)
- Taskhashes of all dependent tasks

**Cache lifecycle:**
1. Before a task runs, BitBake computes the taskhash.
2. It checks `SSTATE_DIR` for a matching `.tgz` archive.
3. On hit: the `do_<task>_setscene` function restores the archive.
4. On miss: the real task runs, and on success, its output is archived into sstate.

**Sstate archive naming:**
```
sstate-cache/<hash[:2]>/<hash[2:]>-<arch>-<PN>-<PV>-<PR>.do_<task>.tgz
```

**Remote mirrors:**
```bitbake
SSTATE_MIRRORS = "file://.* https://sstate.example.com/PATH;downloadfilename=PATH"
```

---

### Q23. What is hash equivalence and when does it matter?

**Answer:**

**Hash equivalence** is a mechanism where BitBake maintains a server-side database mapping `taskhash → output hash`. If two different taskhashes produce **identical outputs**, subsequent builds can reuse the cached output even if the taskhash changed.

**Example:** A whitespace change in a recipe's metadata changes the taskhash but produces the same compiled binary. Without hash equivalence, the entire downstream dependency chain rebuilds. With equivalence, the server recognises the output is unchanged and skips downstream rebuilds.

**Configuration:**
```bitbake
BB_HASHSERVE         = "auto"   # start a local server
BB_HASHSERVE_UPSTREAM = "hashserv.yoctoproject.org:8687"  # community server
```

**When it matters most:**
- Large CI farms where many developers modify metadata
- Reducing unnecessary cache misses after reformatting recipe files
- Sharing sstate across feature branches with minor policy differences

---

### Q24. Explain the difference between `do_fetch`, `do_unpack`, and `do_patch` tasks.

**Answer:**

| Task | Function | Key Variables |
|---|---|---|
| `do_fetch` | Downloads all items in `SRC_URI` into `DL_DIR` | `SRC_URI`, `DL_DIR`, `SRCREV`, `BB_NO_NETWORK` |
| `do_unpack` | Extracts tarballs / clones git repos into `WORKDIR` | `S`, `WORKDIR` |
| `do_patch` | Applies `.patch` files listed in `SRC_URI`, using quilt | `PATCHES`, `QUILTRCFILE`, `PATCHTOOL` |

Each task is independently sstate-cacheable. `do_fetch` results go to `DL_DIR` (not sstate — it's a download cache). `do_unpack` and `do_patch` outputs are sstate-cached, meaning a recipe with unchanged patches won't re-apply them on the next build.

**Patch application control:**
```bitbake
SRC_URI += "file://fix-build.patch;apply=yes;striplevel=1"
SRC_URI += "file://my-file.cfg;apply=no"   # copied but not applied as patch
```

---

### Q25. How does BitBake handle multi-threaded task execution?

**Answer:**

BitBake uses a **multi-process** (not multi-thread) execution model:

- `BB_NUMBER_THREADS` — maximum number of BitBake **tasks** that can run simultaneously across all recipes.
- `PARALLEL_MAKE` — the `-j` flag passed to `make` (or ninja) within a single task.
- `BB_NUMBER_PARSE_THREADS` — threads used during recipe parsing (Scarthgap+).

Task scheduling uses a **priority-based ready queue**: tasks become "ready" when all their dependencies complete. BitBake dispatches up to `BB_NUMBER_THREADS` tasks concurrently using worker sub-processes.

**Optimal tuning:**
```bitbake
BB_NUMBER_THREADS   = "${@oe.utils.cpu_count()}"
PARALLEL_MAKE       = "-j ${@oe.utils.cpu_count()}"
```

**Interaction with sstate:** sstate restoration (setscene tasks) is also parallelised, which is why a warm-cache build can restore hundreds of tasks concurrently and complete in minutes.

---

### Q26. What is a `setscene` task and how does it interact with the RunQueue?

**Answer:**

Every task `do_X` has a corresponding `do_X_setscene` task. Before running a real task, BitBake's RunQueue checks if a valid sstate object exists for the task's current hash. If so, it runs `do_X_setscene` to restore from sstate, which marks `do_X` as satisfied without executing it.

**RunQueue scheduling:**
1. All `do_*_setscene` tasks are attempted first.
2. Tasks satisfied by setscene are removed from the pending set.
3. Remaining unsatisfied tasks are executed in dependency order.

**Forcing setscene bypass:**
```bash
# Disable sstate for a specific run
BB_SETSCENE_ENFORCE = "1"   # error if setscene fails (CI strict mode)
bitbake --no-setscene my-recipe  # never use setscene
bitbake --setscene-only my-recipe  # only run setscene tasks
```

---

### Q27. Explain variable expansion order in BitBake — immediate vs. deferred.

**Answer:**

BitBake has two expansion modes:

**Immediate expansion (`:=`):**
```bitbake
A = "value"
B := "${A}"   # B is set to "value" right now
A = "changed"
# B is still "value"
```

**Deferred expansion (`=`, `?=`, `??=`):**
```bitbake
A = "value"
B = "${A}"    # B stores the literal string "${A}"
A = "changed"
# When B is read, it expands to "changed"
```

**Append/Prepend operators** (`:append`, `:prepend`, `:remove`) are applied **after all other assignments are processed** — they do not participate in the normal assignment order. This means:

```bitbake
A = "base"
A:append = " appended"   # applied last, regardless of file position
A:prepend = "prepended " # applied last
# Final: "prepended base appended"
```

This post-processing nature of override operators is a common source of confusion. The value seen at task execution time is the **fully resolved** value after all appends/prepends/removes are applied.

---

### Q28. What is the purpose of `BB_STRICT_CHECKSUM` and `SRC_URI` checksums?

**Answer:**

BitBake verifies downloaded files against checksums declared in `SRC_URI` to ensure:
1. **Integrity** — the file has not been corrupted in transit.
2. **Security** — protection against supply-chain attacks (tarball replacement).
3. **Reproducibility** — guaranteeing the same source is used across all builds.

```bitbake
SRC_URI = "https://example.com/myapp-1.0.tar.gz"
SRC_URI[sha256sum] = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
```

For multiple URIs, use named checksums:
```bitbake
SRC_URI = "https://example.com/app.tar.gz;name=app \
           https://example.com/data.tar.gz;name=data"
SRC_URI[app.sha256sum]  = "abc123..."
SRC_URI[data.sha256sum] = "def456..."
```

`BB_STRICT_CHECKSUM = "1"` (default in modern Yocto) causes a build failure if no checksum is provided for a URI that requires one. Set `BB_NO_NETWORK = "1"` in CI to prevent any network access during the build phase (all sources must be pre-fetched).

---

### Q29. How does BitBake's dependency resolver handle circular dependencies?

**Answer:**

BitBake's dependency resolver performs a **topological sort** of the task graph using a variant of Kahn's algorithm. Circular dependencies (cycles) are detected when no progress can be made — no tasks have all dependencies satisfied.

**Detection:**
BitBake prints an error like:
```
ERROR: Dependency loop detected:
  my-recipe:do_compile -> other-recipe:do_populate_sysroot -> my-recipe:do_install
```

**Resolution strategies:**
1. **`DEPENDS` loop:** Usually a design error. Refactor the recipes: extract shared code into a third recipe that both depend on.
2. **Runtime loop (`RDEPENDS`):** Also a design error. One package shouldn't need the other at runtime while the other needs it too.
3. **Use `PACKAGECONFIG` guards:** Conditional dependencies break cycles.
4. **Split packages:** If `libfoo` and `libbar` have a circular dev dependency, ensure only the runtime packages are in `RDEPENDS`, not the `-dev` packages.

---

### Q30. What are anonymous Python functions in BitBake recipes?

**Answer:**

Anonymous Python functions (`python ()`) are executed **at parse time**, immediately after all variable assignments are processed. They allow dynamic datastore manipulation before tasks run.

```bitbake
python () {
    pv = d.getVar('PV')
    # Validate PV format
    import re
    if not re.match(r'^\d+\.\d+\.\d+$', pv):
        bb.warn(f"{d.getVar('PN')}: PV '{pv}' does not follow semver format")

    # Conditional dependency injection
    machine = d.getVar('MACHINE')
    if machine.startswith('imx'):
        d.appendVar('DEPENDS', ' imx-gpu-viv')
        d.setVar('PACKAGECONFIG', (d.getVar('PACKAGECONFIG') or '') + ' gpu')

    # Set computed variable
    major = pv.split('.')[0]
    d.setVar('MY_MAJOR', major)
}
```

**Key APIs:**
- `d.getVar('VAR')` — read variable (with expansion)
- `d.setVar('VAR', 'value')` — write variable
- `d.appendVar('VAR', ' value')` — append with space
- `d.getVarFlag('VAR', 'flag')` — read varflag
- `bb.fatal(msg)` — abort with error
- `bb.warn(msg)` — emit warning

---

### Q31. How does BitBake handle fetching from private Git repositories in CI?

**Answer:**

Private repo access requires authentication without embedding credentials in recipes. Approaches:

**SSH keys (recommended for git://):**
```bitbake
SRC_URI = "git://git.internal.example.com/myrepo.git;protocol=ssh;branch=main"
# Ensure the CI runner's SSH key has read access
# BitBake inherits the ssh-agent from the build environment
```

**HTTPS with netrc:**
```bash
# ~/.netrc on the build host / CI runner
machine git.internal.example.com
login ci-bot
password 
```
```bitbake
SRC_URI = "git://git.internal.example.com/myrepo.git;protocol=https;branch=main"
```

**Git config credential helper:**
```bash
git config --global credential.helper store
```

**Mirror pattern for CI isolation:**
```bitbake
PREMIRRORS:prepend = "git://git.internal.example.com/.* \
  git://mirror.ci.example.com/BASENAME;protocol=https \n"
BB_FETCH_PREMIRRORONLY = "1"  # only use mirrors, no external network
```

---

### Q32. What is `BB_NUMBER_THREADS` vs `PARALLEL_MAKE` and how should they be tuned?

**Answer:**

- **`BB_NUMBER_THREADS`** — the number of **BitBake tasks** (across all recipes) that run concurrently. Each task is a separate process. CPU-bound tasks (compilation) and I/O-bound tasks (fetch, unpack) mix in the queue.

- **`PARALLEL_MAKE`** — passed as `MAKEFLAGS` to `make`/`ninja` within a **single** task. Limits parallelism within one recipe's compilation.

**Tuning formula:**
- `BB_NUMBER_THREADS` ≈ number of logical CPU cores (±25%)
- `PARALLEL_MAKE` = `-j<logical_cores>` — allow make to use all cores within a task

**Total potential parallelism:** `BB_NUMBER_THREADS × PARALLEL_MAKE_threads` can vastly exceed core count. In practice, tasks don't all compile simultaneously — many tasks are sequential (fetch → unpack → patch → configure → compile). Over-subscription is acceptable.

```bitbake
BB_NUMBER_THREADS    = "16"
PARALLEL_MAKE        = "-j16"
PARALLEL_MAKEINST    = "-j16"   # parallelism for do_install (make install)
```

On machines with high core counts (64+), reduce `PARALLEL_MAKE` slightly to avoid linker memory exhaustion.

---

### Q33. What is the `bitbake-dumpsig` tool and how is it used?

**Answer:**

`bitbake-dumpsig` dumps the **signature (taskhash) data** for a task, showing every input that contributed to the hash. It is the primary tool for understanding **why a task's hash changed** and diagnosing unexpected rebuilds.

```bash
# Dump signature for a task
bitbake-dumpsig -t my-recipe do_compile

# Compare two signature files
bitbake-diffsigs \
  tmp/stamps/*/my-recipe/1.0-r0.do_compile.sigdata.abc123 \
  tmp/stamps/*/my-recipe/1.0-r0.do_compile.sigdata.def456

# Verbose diff (shows full content of changed variables)
bitbake-diffsigs --debug sigdata.old sigdata.new
```

**Output includes:**
- `basehash` — hash of the task itself (code + variable values)
- `taskhash` — basehash XOR'd with all input taskhashes
- `runtaskdeps` — list of dependent task hashes
- Changed variables and their old/new values

**Workflow:** when CI triggers an unexpected full rebuild, capture `sigdata` files before and after the offending commit, then run `bitbake-diffsigs` to find the exact variable that changed.

---

### Q34. Explain `BBPATH` and how BitBake uses it for file discovery.

**Answer:**

`BBPATH` is a colon-separated list of directories that BitBake searches when resolving:
- `inherit <class>` → looks for `classes/<class>.bbclass` in each BBPATH entry
- `include`/`require` → searches relative paths against BBPATH entries
- `file://` URIs in `SRC_URI` without a full path → searched in `FILESPATH`

Each layer's `layer.conf` prepends its directory to `BBPATH`:
```bitbake
BBPATH .= ":${LAYERDIR}"
```

`FILESPATH` is derived from `BBPATH` plus per-recipe subdirectory conventions:
```bitbake
FILESPATH = "${@base_set_filespath(['${FILE_DIRNAME}/${BP}', \
                                     '${FILE_DIRNAME}/${BPN}', \
                                     '${FILE_DIRNAME}/files'], d)}"
```

This means a recipe at `meta-my-layer/recipes-app/myapp/myapp_1.0.bb` automatically searches for `file://` URIs in:
1. `meta-my-layer/recipes-app/myapp/myapp-1.0/`
2. `meta-my-layer/recipes-app/myapp/myapp/`
3. `meta-my-layer/recipes-app/myapp/files/`

---

### Q35. What is the `PROVIDES` variable and how does it work with `RPROVIDES`?

**Answer:**

- **`PROVIDES`** — declares that this recipe can satisfy a build-time dependency. Other recipes list this in their `DEPENDS`.

```bitbake
# In openssl_3.2.bb
PROVIDES += "virtual/ssl-provider openssl"
# Consumers: DEPENDS = "virtual/ssl-provider"
```

- **`RPROVIDES`** — declares that this **package** satisfies a runtime dependency. Used by the package manager to resolve `RDEPENDS` alternatives.

```bitbake
# In busybox.bb
RPROVIDES:${PN} = "sh login"  # busybox provides sh and login
```

**`PREFERRED_PROVIDER`** selects which recipe satisfies a `PROVIDES` virtual:
```bitbake
PREFERRED_PROVIDER_virtual/ssl-provider = "openssl"
```

If multiple recipes `PROVIDES` the same thing and no `PREFERRED_PROVIDER` is set, BitBake raises a **provider conflict error** during parsing.

---

### Q36. What are `BBFILE_PRIORITY` and `BBFILE_COLLECTIONS`, and how do they interact?

**Answer:**

`BBFILE_COLLECTIONS` registers a named collection (layer) with BitBake. `BBFILE_PRIORITY` assigns an integer priority to that collection.

When multiple recipes match the same `PN` (package name) — for example, a recipe in OE-Core and a `.bbappend` in a BSP layer — BitBake uses priority to determine which recipe *wins* (for `.bb` files) or to order `.bbappend` application.

**`.bb` file conflict resolution:**
- The **highest-priority** layer's `.bb` file is used.
- Lower-priority duplicates are **silently ignored** unless `BBFILE_PRIORITY` is equal, in which case BitBake may error or warn.

**`.bbappend` ordering:**
- All `.bbappend` files are applied **in priority order** (lowest first, highest last), meaning the highest-priority layer's append is applied last.

**Inspection:**
```bash
bitbake-layers show-overlayed   # recipes overridden by higher-priority layers
bitbake-layers show-appends     # .bbappend files and their application order
```

---

### Q37. Describe the `do_rootfs` task and how it assembles the root filesystem.

**Answer:**

`do_rootfs` is the core task in image recipes that assembles the root filesystem from binary packages:

**Steps:**
1. **Package installation:** Calls the package manager backend (`rpm`, `dpkg`, or `opkg`) to install all packages listed in `IMAGE_INSTALL` plus their recursive `RDEPENDS`.
2. **`ROOTFS_POSTINSTALL_COMMAND`:** Runs post-install scripts (`pkg_postinst` functions from package recipes).
3. **`IMAGE_POSTPROCESS_COMMAND`:** Applies image-level post-processing: `set_image_autologin`, `ssh_allow_empty_password`, `read_only_rootfs_hook`, etc.
4. **`ROOTFS_POSTPROCESS_COMMAND`:** Custom hooks added by recipes or classes.
5. **Locale generation:** If `IMAGE_LINGUAS` is set.
6. **Manifest generation:** Lists every package installed, versions, and sizes.

```bitbake
# Custom post-processing hook
ROOTFS_POSTPROCESS_COMMAND += "my_custom_hook; "

my_custom_hook() {
    # Remove test files from production image
    rm -rf ${IMAGE_ROOTFS}/usr/share/tests
    # Set hostname
    echo "my-product" > ${IMAGE_ROOTFS}/etc/hostname
}
```

---

### Q38. What is `STAGING_DIR_TARGET` vs `STAGING_DIR_NATIVE` vs `STAGING_DIR_HOST`?

**Answer:**

These variables point to different sysroot trees used during cross-compilation:

| Variable | Contains | Used by |
|---|---|---|
| `STAGING_DIR_TARGET` | Headers and libraries for the **target** architecture | Recipes compiling target binaries |
| `STAGING_DIR_NATIVE` | Tools and libraries for the **build host** architecture | Native recipes (`-native` suffix) |
| `STAGING_DIR_HOST` | Alias — equals `STAGING_DIR_TARGET` for target, `STAGING_DIR_NATIVE` for native | Generic reference |

**Recipe-specific sysroot:** Rather than using the global staging dir, each recipe gets an isolated `recipe-sysroot` under its `WORKDIR`, populated from the global staging by `do_prepare_recipe_sysroot`. This prevents accidental implicit dependencies.

```bitbake
# In a recipe
do_compile() {
    # PKG_CONFIG_SYSROOT_DIR points to recipe-specific sysroot
    export PKG_CONFIG_SYSROOT_DIR="${RECIPE_SYSROOT}"
    export PKG_CONFIG_PATH="${RECIPE_SYSROOT_NATIVE}/usr/lib/pkgconfig"
}
```

---

### Q39. How does `devshell` work and what are its practical uses?

**Answer:**

`bitbake <recipe> -c devshell` opens an **interactive shell** in the recipe's `${S}` directory with all environment variables set exactly as they would be during a real task execution. This includes:
- Cross-compiler (`CC`, `CXX`, `LD`, `AR`, etc.)
- Sysroot paths (`PKG_CONFIG_PATH`, `STAGING_DIR_TARGET`)
- All BitBake variables exported to the environment

**Practical uses:**
```bash
# Manually run configure to debug options
bitbake my-recipe -c devshell
# Inside shell:
./configure ${CONFIGUREOPTS} ${EXTRA_OECONF}

# Test a patch manually
patch -p1 < ../../my-fix.patch
make

# Debug pkg-config discovery
pkg-config --libs openssl

# Check what the cross compiler sees
${CC} --sysroot=${STAGING_DIR_TARGET} -print-search-dirs
```

**`devpyshell`:** for Python-based tasks — opens a Python REPL with the `d` datastore object available:
```bash
bitbake my-recipe -c devpyshell
>>> d.getVar('STAGING_DIR_TARGET')
>>> d.getVar('DEPENDS')
```

---

### Q40. What is the `insane` QA class and what checks does it perform?

**Answer:**

`insane.bbclass` (inherited by default via `package.bbclass`) performs automated quality assurance checks on package contents after `do_install`. Failures are reported as warnings or errors depending on `ERROR_QA` and `WARN_QA` configuration.

**Key checks:**

| Check | What it catches |
|---|---|
| `already-stripped` | Debug symbols stripped before `do_package` (breaks `-dbg` packages) |
| `arch` | Wrong architecture binary in package (e.g., x86 binary in ARM package) |
| `buildpaths` | Build host paths embedded in binaries (`/home/user/build/...`) |
| `debug-files` | Debug files outside `-dbg` package |
| `dep-cmp` | Malformed version comparison in `RDEPENDS` |
| `file-rdeps` | Missing `RDEPENDS` for shared libraries referenced by package binaries |
| `installed-vs-shipped` | Files in `D` not claimed by any package |
| `ldflags` | Missing `LDFLAGS` in linking (RPATH or security flags missing) |
| `libdir` | Libraries installed to wrong directory |
| `perm-config` | Suspicious file permissions |
| `rpaths` | Hardcoded `RPATH` pointing to build host paths |
| `split-strip` | Binaries not split into `-dbg` |
| `textrel` | Text relocations in shared library |
| `symlink-to-sysroot` | Symlinks pointing into the sysroot |

```bitbake
# Promote specific checks to errors
ERROR_QA:append = " buildpaths arch"

# Whitelist a false positive for a specific recipe
INSANE_SKIP:${PN} = "already-stripped"
```

---

### Q41. How does BitBake's cooker interact with the UI layer?

**Answer:**

BitBake uses a **client-server architecture** separating the build engine (cooker/server) from the UI (knotty, Toaster, etc.):

```
UI Process (knotty/toaster)   ←──XML-RPC──→   Cooker Server Process
                                                    │
                                              Worker Processes
                                              (task execution)
```

- The **cooker** handles parsing, dependency resolution, and task dispatch.
- **Workers** execute individual tasks in isolated processes.
- The **UI** receives events (task start, finish, log output) via the event system.

**Headless / server mode:**
```bash
# Start BitBake server without UI (persist between invocations)
bitbake --server-only -t xmlrpc -B 127.0.0.1:8000

# Connect to running server
bitbake --remote-server=127.0.0.1:8000 core-image-minimal

# Stop server
bitbake --remote-server=127.0.0.1:8000 -m
```

This model allows a CI orchestrator to submit tasks to a persistent build server, avoiding the overhead of re-parsing metadata on every invocation.

---

### Q42. What is `PACKAGECONFIG` and how does it simplify conditional dependencies?

**Answer:**

`PACKAGECONFIG` is a structured mechanism for declaring optional features in a recipe, each with: configure flags (on/off), build-time dependencies, and runtime dependencies.

**Syntax:**
```bitbake
PACKAGECONFIG[feature] = \
  "<extra_oeconf_if_enabled>  , \
   <extra_oeconf_if_disabled> , \
   <DEPENDS_if_enabled>       , \
   <RDEPENDS_if_enabled>      , \
   <RRECOMMENDS_if_enabled>   , \
   <PACKAGECONFIG_CONFARGS_if_disabled>"
```

**Example:**
```bitbake
PACKAGECONFIG ??= "ssl ipv6"

PACKAGECONFIG[ssl]    = "--enable-ssl,--disable-ssl,openssl,libssl3"
PACKAGECONFIG[ipv6]   = "--enable-ipv6,--disable-ipv6,,"
PACKAGECONFIG[gnutls] = "--with-gnutls,--without-gnutls,gnutls,libgnutls30"
PACKAGECONFIG[debug]  = "--enable-debug,--disable-debug,,"
```

BitBake automatically:
1. Collects all enabled features' `extra_oeconf` into `EXTRA_OECONF`
2. Adds their `DEPENDS` to the recipe's `DEPENDS`
3. Adds their `RDEPENDS` to the package's `RDEPENDS`

**External control:**
```bitbake
# Enable from distro.conf or local.conf without modifying the recipe
PACKAGECONFIG:append:pn-curl = " gnutls"
PACKAGECONFIG:remove:pn-curl = "ssl"
```

---

### Q43. What is `BBCLASSEXTEND` and what classes does it support?

**Answer:**

`BBCLASSEXTEND` instructs BitBake to create additional **virtual recipes** from a single `.bb` file. This allows one recipe to build both a target version and a host-native version without code duplication.

```bitbake
BBCLASSEXTEND = "native nativesdk multilib:lib32"
```

**Supported extensions:**

| Extension | Result | Use case |
|---|---|---|
| `native` | `<recipe>-native` | Build tool that runs on the host |
| `nativesdk` | `nativesdk-<recipe>` | Tool included in the cross-compilation SDK |
| `multilib:<variant>` | `<variant>-<recipe>` | Alternative ABI version (e.g., 32-bit on 64-bit system) |

**Example — zlib:**
```bitbake
# zlib_1.3.bb
BBCLASSEXTEND = "native nativesdk"
# Creates: zlib (target), zlib-native (host), nativesdk-zlib (SDK)
```

The `native` class modifies key variables:
- `DEPENDS` — native deps of native recipes
- Compilation flags — host triple, no sysroot prefix
- Install paths — `${STAGING_DIR_NATIVE}` instead of `${D}`

---

### Q44. How does BitBake handle recipe-specific sysroots vs. the global sysroot?

**Answer:**

Since Yocto Thud (2.6), each recipe uses an **isolated recipe-specific sysroot** rather than a shared global one, preventing implicit dependency bugs.

**Global sysroot (staging):** `${STAGING_DIR}/<arch>` — populated by all `do_populate_sysroot` tasks.

**Recipe-specific sysroot:** `${WORKDIR}/recipe-sysroot` — contains only the files from recipes listed in `DEPENDS`.

**Population mechanism:**
`do_prepare_recipe_sysroot` (runs before `do_configure`) creates the recipe sysroot by hard-linking or copying from the global staging dir, scoped to what the recipe's `DEPENDS` declares.

**Implication:** if a recipe compiles successfully but misses a `DEPENDS` entry because the library happened to be in the global sysroot from another build, a clean build will fail. The isolated sysroot catches this on the first build attempt.

```bash
# Debug missing dependency
# Error: cannot find -lfoo
# Fix: add 'libfoo' to DEPENDS
DEPENDS += "libfoo"
```

---

### Q45. What is the role of `do_package_qa` and how do you customise QA rules?

**Answer:**

`do_package_qa` runs the `insane.bbclass` checks on the packaged output. It is one of the most valuable automated gates in the build pipeline, catching common errors before images are assembled.

**Customisation:**
```bitbake
# Globally promote checks to fatal errors (in distro.conf)
ERROR_QA:append = " buildpaths arch rpaths textrel"

# Keep these as warnings
WARN_QA:append = " libdir perm-config"

# Skip a specific check for one recipe (use sparingly)
INSANE_SKIP:${PN} += "already-stripped"    # upstream ships stripped binaries
INSANE_SKIP:${PN}-dev += "dev-elf"         # known false positive

# Add a custom QA check via a bbclass
python do_my_custom_qa() {
    import os
    d_dir = d.getVar('D')
    # Check no world-writable files shipped
    for root, dirs, files in os.walk(d_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            if os.stat(fpath).st_mode & 0o002:
                bb.error(f"World-writable file shipped: {fpath}")
}
addtask my_custom_qa after do_package_qa before do_package_write_rpm
```

---

## 3. Layer Management

---

### Q46. What must a `layer.conf` file contain as a minimum?

**Answer:**

```bitbake
# meta-my-layer/conf/layer.conf

# 1. Register this directory in BBPATH so classes and conf files are found
BBPATH .= ":${LAYERDIR}"

# 2. Register recipe files with BitBake
BBFILES += "${LAYERDIR}/recipes-*/*/*.bb \
             ${LAYERDIR}/recipes-*/*/*.bbappend"

# 3. Register the collection name
BBFILE_COLLECTIONS            += "my-layer"
BBFILE_PATTERN_my-layer        = "^${LAYERDIR}/"
BBFILE_PRIORITY_my-layer       = "10"

# 4. Declare version and compatibility (mandatory for release discipline)
LAYERVERSION_my-layer          = "1"
LAYERDEPENDS_my-layer          = "core"
LAYERSERIES_COMPAT_my-layer    = "scarthgap styhead"
```

`LAYERSERIES_COMPAT_*` prevents the layer from being used with an incompatible Yocto release. If the series doesn't match, BitBake warns (or errors with `ENABLE_LAYER_COMPAT_FAIL`).

---

### Q47. How do you create a new Yocto layer from scratch?

**Answer:**

**Using `bitbake-layers`:**
```bash
cd poky
source oe-init-build-env build
bitbake-layers create-layer ../meta-my-new-layer
bitbake-layers add-layer ../meta-my-new-layer
```

This scaffolds:
```
meta-my-new-layer/
├── COPYING.MIT
├── README
├── conf/
│   └── layer.conf
└── recipes-example/
    └── example/
        └── example_0.1.bb
```

**Manual checklist:**
1. Choose a unique collection name (check existing layers for conflicts)
2. Set appropriate `BBFILE_PRIORITY` (10–15 for product layers)
3. Set `LAYERSERIES_COMPAT` to match your target Yocto release
4. Declare `LAYERDEPENDS` for any layer your recipes import classes from
5. Add to `bblayers.conf` or KAS manifest

---

### Q48. How do `.bbappend` files work and what are the rules for matching?

**Answer:**

A `.bbappend` file **extends** a recipe without modifying the original. BitBake automatically applies all `.bbappend` files that match a recipe's name and version.

**Matching rules:**
- `myrecipe_1.2.bb` ← matched by `myrecipe_1.2.bbappend` (exact version)
- `myrecipe_1.2.bb` ← matched by `myrecipe_%.bbappend` (wildcard — any version)
- Applied in **ascending priority order** (lowest-priority layer first)

**Essential pattern — FILESEXTRAPATHS:**
```bitbake
# Always prepend to FILESEXTRAPATHS in .bbappend files
# This makes ${THISDIR}/${PN}/ searchable for file:// URIs
FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += "file://my-additional.patch"

# Extend tasks
do_install:append() {
    install -d ${D}${sysconfdir}/my-app.d
    install -m 0644 ${WORKDIR}/my-config ${D}${sysconfdir}/my-app.d/
}
```

**Version wildcard caution:** `%` matches any version. If upstream bumps their recipe from `1.2` to `1.3` and your append modifies task logic that is now incompatible, `%` will silently apply to the new version. In production, pin to the specific version and update explicitly.

---

### Q49. How do you resolve a layer priority conflict?

**Answer:**

A priority conflict occurs when two layers have recipes or appends that unexpectedly interact. Symptoms:
- Wrong recipe version selected
- `.bbappend` applied from unintended layer
- QA failures introduced by unknown overlay

**Diagnosis:**
```bash
# See which layers override which recipes
bitbake-layers show-overlayed

# See all appends for a recipe
bitbake-layers show-appends | grep my-recipe

# Check effective recipe origin
bitbake -e my-recipe | grep "^FILE="
```

**Resolution options:**

1. **Adjust priority:** Raise the priority of the authoritative layer.
   ```bitbake
   BBFILE_PRIORITY_my-product = "15"
   ```

2. **Use `BBMASK`:** Mask the conflicting recipe entirely.
   ```bitbake
   BBMASK += "meta-conflicting/recipes-app/my-recipe/"
   ```

3. **Explicit `PREFERRED_VERSION`:** Force a specific version.
   ```bitbake
   PREFERRED_VERSION_my-recipe = "2.1"
   ```

4. **Restructure layers:** Move the authoritative recipe to its own layer at the correct priority.

---

### Q50. What is `LAYERDEPENDS` and what happens if a dependency is missing?

**Answer:**

`LAYERDEPENDS_<collection>` declares which other layer collections this layer requires. If a declared dependency is not in `BBLAYERS`, BitBake emits a **warning** (or error, configurable):

```bitbake
LAYERDEPENDS_my-product = "core openembedded-layer networking-layer"
```

**What "dependency" means here:** it ensures that recipes in `my-product` can safely `inherit` classes from `openembedded-layer` and `networking-layer`, because those layers register their `BBPATH` entries first.

**Missing dependency behaviour:**
```
WARNING: Layer 'my-product' depends on 'networking-layer' but that layer is not present.
```

To turn warnings into errors (recommended for CI):
```bitbake
ENABLE_LAYER_COMPAT_FAIL = "1"
```

---

### Q51. How do you share a single Git repository containing multiple layers?

**Answer:**

A monorepo can contain multiple layers. The structure:

```
my-platform-repo/
├── meta-bsp/
│   └── conf/layer.conf
├── meta-distro/
│   └── conf/layer.conf
├── meta-app/
│   └── conf/layer.conf
└── kas/
    └── my-product.yml
```

**`bblayers.conf` approach:**
```bitbake
BBLAYERS += " \
  ${TOPDIR}/../../my-platform-repo/meta-bsp    \
  ${TOPDIR}/../../my-platform-repo/meta-distro \
  ${TOPDIR}/../../my-platform-repo/meta-app    \
"
```

**KAS approach (preferred):**
```yaml
repos:
  my-platform:
    url: https://git.example.com/my-platform.git
    refspec: main
    layers:
      meta-bsp:
      meta-distro:
      meta-app:
```

In KAS, `layers:` lists subdirectories of the repo that are layers. Sub-layer paths are relative to the repo root.

---

### Q52. What is the recommended directory structure for a BSP layer?

**Answer:**

```
meta-my-bsp/
├── conf/
│   ├── layer.conf
│   └── machine/
│       ├── my-board.conf          ← machine configuration
│       └── include/
│           └── my-soc-common.inc  ← shared SoC settings
├── recipes-bsp/
│   ├── u-boot/
│   │   ├── u-boot_%.bbappend      ← bootloader customisation
│   │   └── u-boot-my-board/       ← patches and configs
│   └── images/
│       └── my-board-image.bb      ← board-specific image
├── recipes-kernel/
│   └── linux-yocto/
│       ├── linux-yocto_%.bbappend
│       └── linux-yocto/
│           ├── defconfig
│           └── *.cfg              ← kernel config fragments
├── recipes-graphics/
│   └── ...                        ← GPU drivers if applicable
└── wic/
    └── my-board.wks               ← disk partition layout
```

**Machine configuration best practices:**
- Use `include` files for SoC-level settings shared across boards.
- Set `DEFAULTTUNE` to the correct architecture tune string.
- Always set `KERNEL_DEVICETREE` explicitly.
- Avoid business logic in machine configs — keep them hardware-only.

---

### Q53. How do you handle machine-specific kernel configuration fragments?

**Answer:**

Kernel configuration fragments (`.cfg` files) are the preferred way to apply machine-specific kernel config changes in Yocto. They are cleaner than full `defconfig` replacements and easier to maintain.

**In a `.bbappend`:**
```bitbake
# meta-my-bsp/recipes-kernel/linux-yocto/linux-yocto_%.bbappend

FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += " \
    file://defconfig         \
    file://enable-uart.cfg   \
    file://enable-spi.cfg    \
    file://disable-debug.cfg \
"

KERNEL_EXTRA_FEATURES ?= ""
```

**Fragment format:**
```
# enable-uart.cfg
CONFIG_SERIAL_8250=y
CONFIG_SERIAL_8250_CONSOLE=y
CONFIG_SERIAL_8250_NR_UARTS=4
```

**Verification:**
```bash
bitbake linux-yocto -c kernel_configcheck
# Warns about configs that were requested but not applied
# (usually due to missing Kconfig dependency)
```

The `kernel-yocto` class (`linux-yocto` recipe) merges fragments using the `merge_config.sh` script, producing the final `.config`.

---

### Q54. How does `MACHINEOVERRIDES` differ from `MACHINE`?

**Answer:**

`MACHINE` is the exact machine name. `MACHINEOVERRIDES` is a colon-separated chain of override tokens that the machine belongs to, allowing hierarchical conditional metadata.

```bitbake
# In meta-freescale/conf/machine/imx8mmevk.conf
MACHINEOVERRIDES =. "mx8:mx8m:mx8mm:use-mainline-bsp:"
```

This means a recipe can have:
```bitbake
SRC_URI:append:mx8 = " file://all-imx8-boards.patch"    # applies to all MX8
SRC_URI:append:mx8mm = " file://mx8mm-specific.patch"   # only MX8MM family
SRC_URI:append:imx8mmevk = " file://evk-specific.patch" # only this exact board
```

**Use case:** a BSP layer might have one patch applicable to an entire SoC family and a different patch only for a specific evaluation kit. `MACHINEOVERRIDES` makes this conditional without recipe duplication.

---

### Q55. What is `DISTRO_FEATURES_BACKFILL` and when is it used?

**Answer:**

`DISTRO_FEATURES_BACKFILL` is a list of features that are automatically added to `DISTRO_FEATURES` if they have **not been explicitly set** by the distro configuration. This ensures backward compatibility when new features are added to OE-Core.

```bitbake
# In oe-core/meta/conf/distro/defaultsetup.conf
DISTRO_FEATURES_BACKFILL = "pie ssp fortify"
DISTRO_FEATURES_BACKFILL_CONSIDERED = ""
```

If your distro explicitly sets `DISTRO_FEATURES` and excludes `pie`, you add it to `DISTRO_FEATURES_BACKFILL_CONSIDERED` to signal "I intentionally excluded this":
```bitbake
DISTRO_FEATURES_BACKFILL_CONSIDERED += "pie"
```

**Without this signal:** BitBake emits a warning that a backfill feature was excluded without being considered, which helps catch accidental omissions vs. intentional ones.

---

### Q56. How do you prevent a `.bbappend` from being silently ignored?

**Answer:**

By default, if a `.bbappend` file targets a recipe that doesn't exist in any active layer, BitBake **silently ignores** it. This is a common source of bugs: you write an append for `recipe_1.2.bbappend` but only `recipe_1.3.bb` exists.

**Detection:**
```bash
# Shows orphaned .bbappend files
bitbake-layers show-appends 2>&1 | grep "WARNING.*bbappend"
```

**Prevention:**
```bitbake
# In local.conf or distro.conf — error on unmatched bbappend
BB_DANGLINGAPPENDS_WARNONLY = "0"  # 0 = error (default in strict setups)
BB_DANGLINGAPPENDS_WARNONLY = "1"  # 1 = warning only (default upstream)
```

**Best practice for CI:** set `BB_DANGLINGAPPENDS_WARNONLY = "0"` to catch accidental recipe version upgrades that leave stale appends.

---

### Q57. Explain the `INHERIT` variable and its global vs. recipe-level usage.

**Answer:**

`INHERIT` is a global variable (set in `local.conf`, `distro.conf`, or `machine.conf`) that causes BitBake to apply a class to **every recipe** parsed. It is equivalent to adding `inherit <class>` to every `.bb` file.

```bitbake
# In distro.conf — apply globally
INHERIT += "rm_work"           # remove WORKDIR after packaging
INHERIT += "buildhistory"      # track image/package history
INHERIT += "create-spdx"       # generate SPDX SBOM
INHERIT += "externalsrc"       # allow EXTERNALSRC overrides
INHERIT += "cve-check"         # CVE scanning
```

**Recipe-level `inherit`** applies only to that recipe:
```bitbake
# In a recipe
inherit autotools pkgconfig cmake python3native
```

**`inherit` search order:** `classes-recipe/` directories first (Kirkstone+), then `classes/` directories in BBPATH order. This allows per-recipe class overrides without touching the original class.

---

### Q58. How do you manage layer versioning in a multi-team environment?

**Answer:**

**Strategy 1 — Tagged releases:**
- Each layer is tagged with `v<major>.<minor>` on release
- KAS manifests reference tags, not branches
- `LAYERSERIES_COMPAT` enforces Yocto version compatibility

**Strategy 2 — Locked SRCREVs via KAS lock files:**
```bash
kas lock kas/product.yml --output kas/product.lock.yml
git add kas/product.lock.yml
git commit -m "lock: pin all layer SRCREVs for release v1.2.0"
```

**Strategy 3 — Git submodules (legacy, not recommended):**
```bash
git submodule add https://github.com/openembedded/meta-openembedded.git
git submodule add https://git.yoctoproject.org/poky.git
```
Submodules are harder to update in bulk and less flexible than KAS.

**Strategy 4 — Combo layer / umbrella repo:**
All layers in one repo, versioned together. Simpler for small teams, harder to accept upstream patches.

---

### Q59. What is `BBFILES_DYNAMIC` and how does it enable optional layer features?

**Answer:**

`BBFILES_DYNAMIC` allows a layer to conditionally include recipe files **only if another specified layer is present**:

```bitbake
# In meta-my-product/conf/layer.conf
# Only parse these recipes if meta-openembedded's networking-layer is active
BBFILES_DYNAMIC += " \
  networking-layer:${LAYERDIR}/recipes-networking/*/*.bb \
  networking-layer:${LAYERDIR}/recipes-networking/*/*.bbappend \
"
```

**Use case:** a product layer can provide optional recipes that depend on meta-openembedded. Users who don't include meta-openembedded won't see those recipes, avoiding dependency errors. This is preferable to `BBMASK` because it's declarative and doesn't require the user to explicitly mask anything.

---

### Q60. How do you audit inter-layer dependencies for a complex project?

**Answer:**

```bash
# 1. Show all layers, their priorities, and source paths
bitbake-layers show-layers

# 2. Show all overridden recipes (higher-priority layer wins)
bitbake-layers show-overlayed

# 3. Show all .bbappend files and which recipe they target
bitbake-layers show-appends

# 4. Show cross-layer class dependencies
bitbake-layers show-cross-depends

# 5. Generate dependency graph
bitbake -g my-image
# Produces: pn-depends.dot, task-depends.dot
# Render: dot -Tsvg pn-depends.dot -o pn-depends.svg

# 6. Check for dangling appends
BB_DANGLINGAPPENDS_WARNONLY = "0"
bitbake -p 2>&1 | grep ERROR

# 7. Identify what provides a package
bitbake-layers show-recipes | grep "^  " | grep "my-package"

# 8. Full environment dump for one recipe
bitbake -e core-image-minimal > /tmp/image-env.txt
grep "^BBLAYERS=" /tmp/image-env.txt
```

---

## 4. Recipe Writing & Customization

---

### Q61. Write a complete recipe for a simple Autotools project.

**Answer:**

```bitbake
# meta-my-layer/recipes-app/myapp/myapp_1.2.3.bb

SUMMARY = "My application built with Autotools"
DESCRIPTION = "A demonstration recipe using the autotools build system"
HOMEPAGE = "https://example.com/myapp"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://COPYING;md5=abc123def456abc123def456abc123de"

DEPENDS = "zlib libpng"

SRC_URI = "https://example.com/releases/myapp-${PV}.tar.gz \
           file://0001-fix-build-with-musl.patch \
           file://myapp.conf \
          "
SRC_URI[sha256sum] = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

inherit autotools pkgconfig

# Extra ./configure arguments
EXTRA_OECONF = " \
    --disable-static    \
    --enable-shared     \
    --without-x         \
    --with-zlib=${STAGING_DIR_TARGET}${prefix} \
"

# PACKAGECONFIG for optional features
PACKAGECONFIG ??= ""
PACKAGECONFIG[ssl] = "--with-ssl,--without-ssl,openssl,libssl3"
PACKAGECONFIG[ipv6] = "--enable-ipv6,--disable-ipv6,,"

PACKAGES =+ "${PN}-tools"
FILES:${PN}-tools = "${bindir}/myapp-tool"

do_install:append() {
    # Install extra config file
    install -d ${D}${sysconfdir}/myapp
    install -m 0644 ${WORKDIR}/myapp.conf ${D}${sysconfdir}/myapp/myapp.conf
}

RDEPENDS:${PN} = "libz1 libpng16-0"
RDEPENDS:${PN}-tools = "${PN}"

BBCLASSEXTEND = "native"
```

---

### Q62. How do you write a recipe for a CMake project?

**Answer:**

```bitbake
# meta-my-layer/recipes-app/myapp/myapp_2.0.bb

SUMMARY = "CMake-based application"
LICENSE = "Apache-2.0"
LIC_FILES_CHKSUM = "file://LICENSE;md5=..."

DEPENDS = "boost openssl"

SRC_URI = "git://github.com/example/myapp.git;protocol=https;branch=main"
SRCREV  = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
S       = "${WORKDIR}/git"

inherit cmake

# Out-of-tree build
B = "${WORKDIR}/build"

# CMake-specific options
EXTRA_OECMAKE = " \
    -DCMAKE_BUILD_TYPE=Release    \
    -DENABLE_TESTS=OFF            \
    -DENABLE_DOCS=OFF             \
    -DUSE_SYSTEM_ZLIB=ON          \
    -DOPENSSL_ROOT_DIR=${STAGING_DIR_TARGET}${prefix} \
"

# cmake.bbclass automatically runs:
#   cmake ${EXTRA_OECMAKE} ${S}   (in do_configure)
#   cmake --build . -- ${PARALLEL_MAKE}  (in do_compile)
#   cmake --install . --prefix ${D}${prefix}  (in do_install)

do_install:append() {
    # Remove installed cmake find-module files (not needed on target)
    rm -rf ${D}${datadir}/cmake
}

FILES:${PN}-dev += "${datadir}/${PN}/*.cmake"
```

---

### Q63. How do you patch a third-party recipe without forking it?

**Answer:**

Use a `.bbappend` with additional patches in `SRC_URI`:

```
meta-my-product/
└── recipes-app/
    └── thirdparty-app/
        ├── thirdparty-app_%.bbappend
        └── thirdparty-app/
            ├── 0001-fix-crash-on-arm64.patch
            └── 0002-add-missing-header.patch
```

```bitbake
# thirdparty-app_%.bbappend

# CRITICAL: always prepend FILESEXTRAPATHS so BitBake finds our files
FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += " \
    file://0001-fix-crash-on-arm64.patch \
    file://0002-add-missing-header.patch \
"
```

**Patch file format:**
```bash
# Generate patch with git
cd tmp/work/*/thirdparty-app/*/source
git diff HEAD > /tmp/0001-fix-crash.patch
# Or from devshell:
bitbake thirdparty-app -c devshell
# Inside: edit, then:
git diff > ${WORKDIR}/0001-fix-crash.patch
```

**Important:** patches in `SRC_URI` must use `-p1` strip level by default. If a patch uses a different level, add `;striplevel=<n>`.

---

### Q64. How do you add a systemd service to a recipe?

**Answer:**

```bitbake
# In recipe .bb or .bbappend
inherit systemd

# Declare the services this recipe installs
SYSTEMD_SERVICE:${PN} = "myapp.service"
SYSTEMD_AUTO_ENABLE:${PN} = "enable"   # or "disable"

# Ensure systemd is in DISTRO_FEATURES
REQUIRED_DISTRO_FEATURES = "systemd"

do_install:append() {
    install -d ${D}${systemd_unitdir}/system
    install -m 0644 ${WORKDIR}/myapp.service \
                    ${D}${systemd_unitdir}/system/myapp.service
}

FILES:${PN} += "${systemd_unitdir}/system/myapp.service"
```

```ini
# files/myapp.service
[Unit]
Description=My Application
After=network.target
Requires=network.target

[Service]
Type=simple
User=myapp
Group=myapp
ExecStart=/usr/bin/myapp --config /etc/myapp/myapp.conf
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**SysVinit fallback:**
```bitbake
inherit update-rc.d

INITSCRIPT_NAME = "myapp"
INITSCRIPT_PARAMS = "defaults 80 20"
```

The `systemd` class handles both cases when `DISTRO_FEATURES` is checked.

---

### Q65. How do you install a configuration file that should not be overwritten on upgrade?

**Answer:**

Mark the file as a **`CONFFILE`**. Package managers (rpm, deb, ipk) treat conffiles specially: on package upgrade, if the user has modified the file, the package manager warns and keeps the user's version.

```bitbake
# In recipe
CONFFILES:${PN} = " \
    ${sysconfdir}/myapp/myapp.conf      \
    ${sysconfdir}/myapp/logging.conf    \
"

do_install:append() {
    install -d ${D}${sysconfdir}/myapp
    install -m 0644 ${WORKDIR}/myapp.conf \
                    ${D}${sysconfdir}/myapp/myapp.conf
}
```

**For read-only rootfs images:** conffiles don't apply. Instead, use overlayfs or a writable `/data` partition with symlinks, or use a first-boot script to copy defaults to a writable location.

---

### Q66. How do you handle a recipe that requires running on the host (native)?

**Answer:**

Three approaches depending on the use case:

**Approach 1 — `BBCLASSEXTEND` (preferred when the same source builds for host and target):**
```bitbake
# In the existing recipe
BBCLASSEXTEND = "native"
# Creates: myapp-native automatically
```

**Approach 2 — Dedicated native recipe:**
```bitbake
# myapp-native.bb
inherit native
SUMMARY = "Native host tool for myapp"
# ... recipe body
```

**Approach 3 — `nativesdk` for SDK inclusion:**
```bitbake
BBCLASSEXTEND = "native nativesdk"
```

**Key differences when `native` class is applied:**
- `CC`, `CXX` → host compiler (not cross)
- `prefix` → `${STAGING_DIR_NATIVE}${prefix}` (not `/usr`)
- No sysroot required
- `do_populate_sysroot` installs into `STAGING_DIR_NATIVE`

**Consumer recipe:**
```bitbake
DEPENDS += "myapp-native"
do_compile() {
    # myapp tool is now in PATH (STAGING_DIR_NATIVE/usr/bin)
    myapp-tool generate-code ${S}/schema.json
}
```

---

### Q67. What is `EXTERNALSRC` and when is it used?

**Answer:**

`EXTERNALSRC` allows a recipe to build from a **local source directory** on the host instead of fetching from `SRC_URI`. This is primarily useful during active development.

```bitbake
# In local.conf or devshell
EXTERNALSRC:pn-myapp = "/home/developer/myapp-src"
EXTERNALSRC_BUILD:pn-myapp = "/home/developer/myapp-build"

# Must inherit the class
inherit externalsrc   # usually via INHERIT += "externalsrc" globally
```

**Behaviour change:**
- `do_fetch` and `do_unpack` are skipped.
- `S` points to `EXTERNALSRC`.
- By default, timestamps are not checked — BitBake doesn't re-run tasks unless forced.

**Force rebuild on source change:**
```bitbake
# In local.conf
BB_SRCREV_POLICY = "cache"   # don't re-fetch on every build
```

```bash
# Force compile after editing source
bitbake myapp -C compile
```

**Limitation:** sstate is effectively disabled for `EXTERNALSRC` recipes because the source hash changes unpredictably.

---

### Q68. How do you create a recipe that fetches from multiple Git repositories?

**Answer:**

```bitbake
SRC_URI = " \
    git://github.com/example/main-repo.git;protocol=https;branch=main;name=main \
    git://github.com/example/plugin.git;protocol=https;branch=main;name=plugin;destsuffix=git/plugins/myplugin \
    git://github.com/example/sublib.git;protocol=https;branch=v2;name=sublib;destsuffix=git/external/sublib \
"

# Each named fetcher needs its own SRCREV
SRCREV_main   = "aaabbbccc111..."
SRCREV_plugin = "dddeeefff222..."
SRCREV_sublib = "ggghhh333444..."

# SRCREV_FORMAT controls the combined hash string
SRCREV_FORMAT = "main_plugin_sublib"

S = "${WORKDIR}/git"
```

The `destsuffix` parameter controls where each repo is unpacked relative to `WORKDIR`. Without it, all repos would try to unpack to `WORKDIR/git`, causing conflicts.

---

### Q69. How do you create a recipe for a Python package from PyPI?

**Answer:**

```bitbake
# meta-my-layer/recipes-python/python3-requests/python3-requests_2.31.0.bb

SUMMARY = "Python HTTP library"
HOMEPAGE = "https://requests.readthedocs.io"
LICENSE = "Apache-2.0"
LIC_FILES_CHKSUM = "file://LICENSE;md5=..."

inherit pypi setuptools3
# or: inherit pypi python_flit_core (for PEP 517 builds)

PYPI_PACKAGE = "requests"  # PyPI package name (if different from PN)

SRC_URI[sha256sum] = "..."

RDEPENDS:${PN} = " \
    python3-certifi    \
    python3-chardet    \
    python3-idna       \
    python3-urllib3    \
"
```

**Automatic PyPI URL:** the `pypi` class sets:
```
SRC_URI = "https://files.pythonhosted.org/packages/.../${PYPI_PACKAGE}-${PV}.tar.gz"
```

**For packages not on PyPI:**
```bitbake
inherit setuptools3

SRC_URI = "git://github.com/example/mylib.git;protocol=https;branch=main"
SRCREV  = "abc123..."
S       = "${WORKDIR}/git"
```

---

### Q70. How do you handle `pkg_postinst` and `pkg_prerm` functions?

**Answer:**

These shell functions run on the **target** during package installation/removal (or during `do_rootfs` for on-host first-boot scripts):

```bitbake
# Runs on first boot on target (or during rootfs if on-host)
pkg_postinst:${PN}() {
#!/bin/sh
set -e

if [ -n "$D" ]; then
    # Running in rootfs assembly (host) — D is set
    # Only perform offline-safe operations
    mkdir -p $D/var/lib/myapp
else
    # Running on real target
    # Perform online operations (start service, update db, etc.)
    systemctl daemon-reload
    systemctl enable myapp.service
    useradd -r -s /sbin/nologin myapp 2>/dev/null || true
fi
}

pkg_prerm:${PN}() {
#!/bin/sh
systemctl stop myapp.service 2>/dev/null || true
systemctl disable myapp.service 2>/dev/null || true
}

pkg_postrm:${PN}() {
#!/bin/sh
userdel myapp 2>/dev/null || true
rm -rf /var/lib/myapp
}
```

**`pkg_postinst_ontarget`:** runs exclusively on target (not during rootfs assembly), useful for operations that require a running system:
```bitbake
pkg_postinst_ontarget:${PN}() {
#!/bin/sh
    ldconfig
    update-alternatives --install /usr/bin/python python /usr/bin/python3 100
}
```

---

### Q71. How do you write a recipe that installs a pre-built binary blob?

**Answer:**

```bitbake
# meta-my-bsp/recipes-bsp/firmware-blob/firmware-blob_1.0.bb

SUMMARY = "Pre-built firmware blob for my hardware"
LICENSE = "Proprietary"
LIC_FILES_CHKSUM = "file://LICENSE;md5=..."
LICENSE_FLAGS = "commercial"    # requires LICENSE_FLAGS_ACCEPTED

# No build steps needed
inherit bin_package

SRC_URI = "https://vendor.example.com/firmware-${PV}.tar.gz"
SRC_URI[sha256sum] = "..."

# bin_package class sets:
# do_configure[noexec] = "1"
# do_compile[noexec] = "1"
# and installs from S directly

do_install() {
    install -d ${D}${base_libdir}/firmware
    install -m 0644 ${S}/my-firmware.bin ${D}${base_libdir}/firmware/
    install -d ${D}${sysconfdir}
    install -m 0644 ${S}/my-fw.conf ${D}${sysconfdir}/
}

FILES:${PN} = "${base_libdir}/firmware/my-firmware.bin \
               ${sysconfdir}/my-fw.conf"

# QA: binary is pre-stripped, and we can't check arch for firmware blobs
INSANE_SKIP:${PN} = "already-stripped arch"
```

---

### Q72. Explain `PACKAGES_DYNAMIC` and its use in recipes with variable output.

**Answer:**

`PACKAGES_DYNAMIC` is used when a recipe produces packages whose **names are not known at parse time** (e.g., locale packages, kernel modules, plugin packages).

```bitbake
# In glibc recipe
PACKAGES_DYNAMIC = "^locale-base-.* ^glibc-gconv-.* ^glibc-charmap-.*"

# In linux-yocto recipe
PACKAGES_DYNAMIC = "^kernel-module-.* ^kernel-image-.* ^kernel-firmware-.*"
```

At packaging time (`do_package`), BitBake iterates files in `D` and matches them against `PACKAGES_DYNAMIC` regex patterns, creating packages on-the-fly.

**Custom example:**
```bitbake
# Recipe producing one package per plugin .so
PACKAGES_DYNAMIC = "^${PN}-plugin-.*"

python populate_packages:prepend() {
    import os
    plugin_dir = os.path.join(d.getVar('D'), 'usr/lib/myapp/plugins')
    if os.path.exists(plugin_dir):
        for f in os.listdir(plugin_dir):
            if f.endswith('.so'):
                name = f[:-3].replace('_', '-')
                pkg = f'{d.getVar("PN")}-plugin-{name}'
                d.setVar(f'FILES:{pkg}', f'/usr/lib/myapp/plugins/{f}')
}
```

---

### Q73. How do you use `do_install_append` correctly to avoid permission issues?

**Answer:**

`do_install:append` runs after the main `do_install`. Permission issues arise because Yocto runs without real root (via pseudo), and incorrect mode/ownership settings can cause QA failures or runtime problems.

```bitbake
do_install:append() {
    # Always use 'install' command — sets mode atomically
    install -d ${D}${sysconfdir}/myapp
    install -m 0644 ${WORKDIR}/config.conf ${D}${sysconfdir}/myapp/
    install -m 0755 ${WORKDIR}/myapp-init  ${D}${bindir}/myapp-init

    # For directories with specific ownership
    install -d -m 0750 ${D}${localstatedir}/lib/myapp

    # Avoid using 'cp' for setuid/setgid files
    install -m 4755 ${WORKDIR}/myapp-suid ${D}${bindir}/myapp-suid

    # Remove test artefacts (don't use PACKAGES to exclude — remove is cleaner)
    rm -rf ${D}${datadir}/myapp/tests
}
```

**Ownership:** Yocto handles ownership via `USERADD_PACKAGES` and `GROUPADD_PACKAGES`, not via `chown` in install:
```bitbake
inherit useradd

USERADD_PACKAGES = "${PN}"
USERADD_PARAM:${PN} = "-r -u 1000 -g myapp -s /sbin/nologin -d /var/lib/myapp myapp"
GROUPADD_PARAM:${PN} = "-g 1000 myapp"
```

---

### Q74. What is the `autotools-brokensep` class and when should you use it?

**Answer:**

`autotools` class assumes the project supports **out-of-tree builds** (building in `B` while sources are in `S`, i.e., `B != S`). Some older or poorly maintained projects only support in-tree builds.

`autotools-brokensep` (broken separation) sets `B = "${S}"` and runs configure/make in the source directory itself:

```bitbake
inherit autotools-brokensep

# Equivalent to:
# inherit autotools
# B = "${S}"
```

**Side effects:**
- Source directory is modified during build (configure files, generated code)
- Sstate for `do_configure` and `do_compile` is less reliable
- `do_clean` doesn't cleanly restore the source directory

**Upgrade path:** if you control the project, fix it to support out-of-tree builds by using `AC_CONFIG_AUX_DIR`, `AM_INIT_AUTOMAKE`, and proper variable usage.

---

### Q75. How do you correctly handle multilib (`lib32` / `lib64`) in a recipe?

**Answer:**

Multilib allows building both 32-bit and 64-bit versions of packages on a 64-bit system.

**Enabling multilib:**
```bitbake
# local.conf
require conf/multilib.conf
MULTILIBS     = "multilib:lib32"
DEFAULTTUNE:virtclass-multilib-lib32 = "x86"
```

**Recipe considerations:**
```bitbake
# Packages that provide differently-named multilib variants
MULTILIB_PACKAGES = "${PN}"

# Files that should NOT be in multilib variants (avoid duplication)
MULTILIB_SCRIPTS = "${PN}:${bindir}/myapp-config"

# Variables that should NOT be prefixed by multilib variant
MULTILIB_HEADER_INSTALL = "1"  # for header-only packages
```

**Conditional logic in recipes:**
```bitbake
python () {
    ml = d.getVar('MLPREFIX')
    if ml:
        # We're building as lib32-mypackage
        d.setVar('EXTRA_OECMAKE', d.getVar('EXTRA_OECMAKE') + ' -DLIB32=1')
}
```

**Install:**
```bash
# 32-bit libraries go to /lib (not /lib64)
bitbake lib32-glibc lib32-zlib
IMAGE_INSTALL += "lib32-glibc lib32-openssl"
```

---

### Q76. How do you create a meta-package (package group) recipe?

**Answer:**

```bitbake
# meta-my-product/recipes-my-product/packagegroups/packagegroup-my-product.bb

SUMMARY = "My product core package group"
LICENSE = "MIT"

inherit packagegroup

PACKAGES = " \
    ${PN}           \
    ${PN}-tools     \
    ${PN}-debug     \
"

# Core runtime packages
RDEPENDS:${PN} = " \
    my-daemon       \
    my-config-tool  \
    busybox         \
    dropbear        \
    iproute2        \
    ethtool         \
"

# Optional tools package
RDEPENDS:${PN}-tools = " \
    strace          \
    tcpdump         \
    iperf3          \
"

# Debug package (excluded from production)
RDEPENDS:${PN}-debug = " \
    gdbserver       \
    valgrind        \
    lttng-ust       \
"
```

**In image recipe:**
```bitbake
IMAGE_INSTALL += " \
    packagegroup-my-product          \
    packagegroup-my-product-tools    \
"
```

---

### Q77. Explain `IMAGE_LINGUAS` and locale handling in Yocto.

**Answer:**

`IMAGE_LINGUAS` controls which language locales are installed into the image:

```bitbake
# Install English and French locales
IMAGE_LINGUAS = "en-us fr-fr"

# Install only minimal locale data (no locale at all for embedded)
IMAGE_LINGUAS = ""
GLIBC_GENERATE_LOCALES = ""  # don't generate any locale files
```

**Locale package naming convention:**
- `locale-base-en-us` — base locale (minimal)
- `glibc-binary-localedata-en-us` — full glibc locale data

**Musl libc:** has no locale support. Set `TCLIBC = "musl"` and `IMAGE_LINGUAS = ""` together. Many applications that depend on locale-aware `glibc` functions may need porting.

**Memory-constrained systems:** disable all locale handling:
```bitbake
DISTRO_FEATURES:remove = "largefile"
IMAGE_LINGUAS = ""
PACKAGE_INSTALL_COMPLEMENTARY = ""  # don't install complementary locale packages
```

---

### Q78. What is the `update-alternatives` mechanism and how do you use it in a recipe?

**Answer:**

`update-alternatives` (Debian's `alternatives` system, implemented for Yocto) allows multiple packages to provide the same command, with the active version selected by priority.

```bitbake
inherit update-alternatives

ALTERNATIVE:${PN} = "editor python python3"

# For each alternative: name, link, path, priority
ALTERNATIVE_LINK_NAME[editor]  = "${bindir}/editor"
ALTERNATIVE_TARGET[editor]     = "${bindir}/vi"
ALTERNATIVE_PRIORITY[editor]   = "30"

ALTERNATIVE_LINK_NAME[python]  = "${bindir}/python"
ALTERNATIVE_TARGET[python]     = "${bindir}/python3"
ALTERNATIVE_PRIORITY[python]   = "100"
```

**How it works:**
- `${bindir}/python` is a symlink managed by `update-alternatives`
- The highest-priority provider wins
- On package removal, the next-highest takes over

**Runtime manipulation:**
```bash
update-alternatives --list python
update-alternatives --set python /usr/bin/python2
update-alternatives --config python
```

---

### Q79. How do you create a recipe that generates source code (code generator)?

**Answer:**

Code generators are typically `native` recipes that produce source files consumed by other recipes:

```bitbake
# meta-my-layer/recipes-codegen/my-codegen/my-codegen_1.0.bb
SUMMARY = "My code generator"
LICENSE = "MIT"
inherit native
# ... normal build
```

**Consuming recipe:**
```bitbake
# meta-my-layer/recipes-app/myapp/myapp_1.0.bb
DEPENDS += "my-codegen-native"

do_compile:prepend() {
    # my-codegen is in PATH (STAGING_DIR_NATIVE/usr/bin)
    my-codegen \
        --input ${S}/schema.proto \
        --output ${B}/generated/ \
        --lang c
}
```

**Alternative — generate during `do_configure`:**
```bitbake
do_configure:append() {
    cd ${B}
    my-codegen --input ${S}/api.yaml --output ${B}/src/generated.c
}
```

**Sstate consideration:** the generated code is part of `do_compile`'s output hash, so if the generator version or schema changes, the downstream build correctly invalidates.

---

### Q80. How do you handle license-incompatible dependencies in a recipe?

**Answer:**

When a recipe depends on a commercially-licensed package, the build system blocks the build until the license is explicitly accepted:

```bitbake
# In the commercial recipe
LICENSE = "Proprietary"
LICENSE_FLAGS = "commercial commercial_myvendor"

# In local.conf or distro.conf
LICENSE_FLAGS_ACCEPTED = "commercial commercial_myvendor"
```

**GPL-with-exception:**
```bitbake
LICENSE = "GPL-2.0-only with GCC-exception-2.0"
```

**Incompatible license combinations (e.g., GPL + OpenSSL pre-3.0):**
```bitbake
# Avoid the conflict by using a different crypto library
PACKAGECONFIG:remove:pn-myapp = "openssl"
PACKAGECONFIG:append:pn-myapp = " gnutls"  # LGPLv2.1 — GPL compatible
```

**Compliance automation:**
```bitbake
INHERIT += "archiver"
ARCHIVER_MODE = "patched"  # Archive patched source for GPL compliance
# Output: tmp/deploy/sources/
```

---

### Q81. What is `RRECOMMENDS` and how does it differ from `RDEPENDS`?

**Answer:**

| Variable | Installation behaviour | Build failure if missing |
|---|---|---|
| `RDEPENDS` | **Required** — package manager refuses to install without it | Yes (QA check) |
| `RRECOMMENDS` | **Suggested** — installed if available, skipped if not | No |
| `RSUGGESTS` | **Optional** hint — not installed automatically | No |
| `RCONFLICTS` | **Blocks** — package manager refuses to install both | N/A |
| `RREPLACES` | **Replaces** another package on upgrade | N/A |

```bitbake
RDEPENDS:${PN}    = "libssl3"            # must be installed
RRECOMMENDS:${PN} = "ca-certificates"   # nice to have
RSUGGESTS:${PN}   = "my-extra-plugins"  # user might want
RCONFLICTS:${PN}  = "old-myapp"         # cannot coexist
RREPLACES:${PN}   = "old-myapp"         # replaces old package on upgrade
```

**Image construction:** during `do_rootfs`, all `RDEPENDS` are resolved recursively. `RRECOMMENDS` are installed if `IMAGE_INSTALL_COMPLEMENTARY = "1"` (default for full images, disabled for minimal images).

---

### Q82. How do you write a recipe for a Rust crate?

**Answer:**

```bitbake
# meta-my-layer/recipes-app/my-rust-app/my-rust-app_0.1.0.bb

SUMMARY = "My Rust application"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE;md5=..."

SRC_URI = "git://github.com/example/my-rust-app.git;protocol=https;branch=main"
SRCREV  = "abc123..."
S       = "${WORKDIR}/git"

inherit cargo

# Cargo.lock must be committed in the repo for reproducible builds
# BitBake fetches all crate dependencies declared in Cargo.lock

CARGO_DISABLE_BITBAKE_VENDORING = "0"  # use BitBake's crate vendor mechanism

# Cross-compilation target
CARGO_BUILD_FLAGS = "--release"

do_install() {
    install -d ${D}${bindir}
    install -m 0755 ${B}/target/${CARGO_TARGET_SUBDIR}/my-rust-app \
                    ${D}${bindir}/
}
```

**Crate dependencies:** the `cargo` class fetches all crates from `Cargo.lock` using the `crate://` fetcher. For offline builds, run `bitbake -c fetch my-rust-app` first.

---

### Q83. What are `do_compile[network]` and other task varflags?

**Answer:**

Varflags are metadata attached to variables or tasks:

```bitbake
# Declare that this task requires network access
# (normally network is blocked during do_compile for reproducibility)
do_compile[network] = "1"

# Prevent this task from being sstate-cached
do_compile[nostamp] = "1"

# Ensure a directory exists before the task runs
do_compile[dirs] = "${B} ${S}"

# Clean the directory before running
do_compile[cleandirs] = "${B}"

# Mark a task as having no executable code (skip but don't error)
do_configure[noexec] = "1"

# Declare inter-recipe task dependencies
do_compile[depends] = "virtual/kernel:do_deploy openssl:do_populate_sysroot"

# Exclusive lock file (prevents concurrent execution)
do_compile[lockfiles] = "${TMPDIR}/my-global-lock"

# Set umask for the task
do_compile[umask] = "022"
```

**`postfuncs` and `prefuncs`:**
```bitbake
# Append a function to run after do_install
do_install[postfuncs] += "my_post_install_hook"

my_post_install_hook() {
    rm -f ${D}${bindir}/test-only-binary
}
```

---

### Q84. How do you handle recipes where upstream uses Meson?

**Answer:**

```bitbake
inherit meson pkgconfig

# Meson native file is auto-generated by the class
# with cross-compilation settings

# Meson options
EXTRA_OEMESON = " \
    -Dtests=disabled       \
    -Ddocs=disabled        \
    -Dbackend=ninja        \
    -Ddefault_library=shared \
"

PACKAGECONFIG ??= ""
PACKAGECONFIG[ssl] = "-Dssl=enabled,-Dssl=disabled,openssl,libssl3"

# meson.bbclass automatically handles:
# do_configure: meson setup ${EXTRA_OEMESON} ${S} ${B}
# do_compile:   ninja -C ${B} ${PARALLEL_MAKE}
# do_install:   DESTDIR=${D} ninja -C ${B} install

# Common pitfall: meson wraps (online dependency fetching) must be disabled
# The class sets --wrap-mode=nodownload automatically
```

**Native meson tools:** the `meson-native` and `ninja-native` recipes are automatically added to `DEPENDS` by the `meson` class.

---

### Q85. How do you create a recipe that produces multiple independent packages?

**Answer:**

```bitbake
# Recipe producing: mylib-core, mylib-plugins, mylib-dev, mylib-doc

PACKAGES = " \
    ${PN}-doc       \
    ${PN}-dev       \
    ${PN}-plugins   \
    ${PN}-core      \
    ${PN}           \
"

FILES:${PN}-core    = "${libdir}/libmycore.so.*"
FILES:${PN}-plugins = "${libdir}/myplugins/*.so"
FILES:${PN}-dev     = "${includedir} ${libdir}/*.so ${libdir}/pkgconfig"
FILES:${PN}-doc     = "${docdir} ${mandir}"
FILES:${PN}         = "${bindir}/myapp"

RDEPENDS:${PN}         = "${PN}-core"
RDEPENDS:${PN}-plugins = "${PN}-core"
RDEPENDS:${PN}-dev     = "${PN}-core"
ALLOW_EMPTY:${PN}      = "1"   # allow empty catch-all package

# Allow installing plugins without the main binary
RRECOMMENDS:${PN}-plugins = "${PN}"
```

**In image:**
```bitbake
IMAGE_INSTALL += "mylib-core mylib-plugins"
# Only install dev package in SDK
TOOLCHAIN_TARGET_TASK += "mylib-dev"
```

---

## 5. Build System Optimization

---

### Q86. How do you minimise build times in a large Yocto project?

**Answer:**

A multi-layered optimisation strategy:

**1. Shared download cache:**
```bitbake
DL_DIR = "/shared/downloads"   # NFS or local SSD shared by all developers
```

**2. Shared sstate cache:**
```bitbake
SSTATE_DIR = "/shared/sstate"
# Or remote mirror:
SSTATE_MIRRORS = "file://.* https://sstate.ci.example.com/PATH;downloadfilename=PATH"
```

**3. Hash equivalence:**
```bitbake
BB_HASHSERVE = "your-hashserv.example.com:8687"
```

**4. Parallelism:**
```bitbake
BB_NUMBER_THREADS = "32"
PARALLEL_MAKE = "-j32"
```

**5. Disk space management:**
```bitbake
INHERIT += "rm_work"
RM_WORK_EXCLUDE += "linux-yocto"  # keep kernel for quick incremental builds
```

**6. `BB_NUMBER_PARSE_THREADS`:**
```bitbake
BB_NUMBER_PARSE_THREADS = "8"  # Scarthgap+ — parallel recipe parsing
```

**7. TMPDIR on fast storage:**
Use a local NVMe SSD for `TMPDIR`, even if `SSTATE_DIR` and `DL_DIR` are on shared storage.

**8. Avoid `AUTOREV`:**
`AUTOREV` forces a git fetch on every build, bypassing the DL_DIR cache for the SRCREV check.

---

### Q87. What is `rm_work` and what are its trade-offs?

**Answer:**

`rm_work` (`rm_work.bbclass`) deletes a recipe's `WORKDIR` after packaging completes, reclaiming significant disk space (often 10–50 GB on large builds).

**How it works:**
```bitbake
INHERIT += "rm_work"
```
Adds a `do_rm_work` task after `do_package_write_*`. On completion, it removes `${WORKDIR}`.

**Trade-offs:**

| Benefit | Cost |
|---|---|
| Reclaims 10–50+ GB disk space | Cannot inspect build artefacts after the fact |
| Allows longer build queues on disk-constrained CI | Breaks `devshell` and `devpyshell` on cleaned recipes |
| Faster incremental builds (less I/O) | Sstate must be valid to skip the rebuild |

**Selective exclusion:**
```bitbake
# Keep WORKDIR for recipes under active development
RM_WORK_EXCLUDE += "my-app linux-yocto"
```

**Exclude all native recipes** (they're small and frequently needed):
```bitbake
RM_WORK_EXCLUDE_ITEMS = "native nativesdk"
```

---

### Q88. How do you profile and identify build bottlenecks?

**Answer:**

**Method 1 — BuildStats class:**
```bitbake
INHERIT += "buildstats buildstats-summary"
```
Produces `tmp/buildstats/<date>/` with per-task CPU, wall-clock, and I/O statistics.

```bash
# Parse and summarise
buildstats-summary tmp/buildstats/20240101120000/
# Shows top-N slowest tasks and overall build time breakdown
```

**Method 2 — Toaster UI:**
Toaster is BitBake's web-based UI that shows real-time build progress, task durations, and dependency graphs. Start with:
```bash
source toaster start
bitbake core-image-minimal
# Access: http://localhost:8000
```

**Method 3 — `pybootchart`:**
```bash
# Install
pip install pybootchartgui
# Generate chart from buildstats
pybootchartgui tmp/buildstats/20240101120000/
```

**Method 4 — Manual task timing:**
```bash
# Find slowest tasks from logs
grep "Elapsed time" tmp/buildstats/*/*/do_compile | sort -t: -k2 -rn | head -20
```

**Common bottlenecks:**
- `linux-yocto` `do_compile` — use `linux-yocto-tiny` for fast iteration
- `gcc-cross-*` — warm sstate from CI
- `qemu-native` — large, complex build; sstate is critical
- Network fetches — use premirrors

---

### Q89. What is `BB_GENERATE_MIRROR_TARBALLS` and why is it important?

**Answer:**

```bitbake
BB_GENERATE_MIRROR_TARBALLS = "1"
```

When enabled, for every `git://` (or other VCS) fetch, BitBake generates a `.tar.gz` tarball of the cloned repository and stores it in `DL_DIR`. This allows the project to be built without internet access by redistributing `DL_DIR`.

**Use cases:**
1. **Air-gapped builds:** ship `DL_DIR` to a secure network.
2. **GPL compliance:** tarball includes full git history.
3. **Long-term archival:** git hosting may disappear; tarball is self-contained.
4. **Faster CI cold starts:** faster to extract a tarball than clone.

```bitbake
# Mirror tarballs are named:
# DL_DIR/git2_<host>_<org>_<repo>.git.tar.gz

# To use mirror tarballs exclusively:
BB_FETCH_PREMIRRORONLY = "1"
PREMIRRORS:prepend = "git://.*/.* file:///shared/downloads/ \n"
```

---

### Q90. How do you optimise kernel build times?

**Answer:**

**1. Minimal kernel config:**
```bash
# Start from defconfig and enable only what you need
bitbake linux-yocto -c menuconfig
# Save as defconfig fragment
```

**2. Use `linux-yocto-tiny`:**
```bitbake
PREFERRED_PROVIDER_virtual/kernel = "linux-yocto-tiny"
# Smaller kernel, faster build — for minimal embedded targets
```

**3. Kernel sstate:**
Kernel compilation is one of the largest sstate objects. Ensure sstate is warm:
```bitbake
SSTATE_MIRRORS = "file://.* https://sstate.ci.example.com/PATH;..."
```

**4. `RM_WORK_EXCLUDE`:**
```bitbake
RM_WORK_EXCLUDE += "linux-yocto"
# Keeps kernel WORKDIR; subsequent builds with changed configs are much faster
```

**5. `do_kernel_configme` caching:**
Use kernel config fragments rather than full defconfigs — fragments are merged incrementally and the base config is cached.

**6. Out-of-tree modules:**
Build kernel modules in a separate recipe that depends on `virtual/kernel:do_deploy`. This recipe rebuilds only when the module source or kernel API changes.

---

### Q91. How does Yocto handle toolchain (cross-compiler) builds and can they be cached?

**Answer:**

The cross-toolchain build sequence:
```
linux-libc-headers → binutils-cross → gcc-cross-initial →
glibc-initial → gcc-cross → glibc → gcc-runtime → gcc-cross-final
```

This is a two-stage bootstrap due to the circular dependency between GCC and glibc.

**Caching:**
- All toolchain tasks are sstate-cacheable.
- A pre-built toolchain from CI sstate means developers never rebuild the toolchain.
- The Yocto Project publishes sstate for official releases: `https://sstate.yoctoproject.org/`

```bitbake
# Use official Yocto Project sstate for toolchain (Scarthgap example)
SSTATE_MIRRORS:prepend = " \
  file://.* https://sstate.yoctoproject.org/5.0/PATH;downloadfilename=PATH \n"
```

**External toolchain (fastest option):**
```bitbake
# Use a pre-built toolchain (e.g., Arm GNU Toolchain, Linaro)
EXTERNAL_TOOLCHAIN = "/opt/arm-gnu-toolchain"
TCMODE = "external-arm"
require conf/distro/include/tcmode-external-arm.conf
```

---

### Q92. What is `PACKAGE_PREPROCESS_FUNCS` and how is it used?

**Answer:**

`PACKAGE_PREPROCESS_FUNCS` is a list of shell functions called **before** the main package splitting logic in `do_package`. Use it to manipulate `${D}` before files are claimed by packages.

```bitbake
PACKAGE_PREPROCESS_FUNCS += "my_strip_test_files my_fix_permissions"

my_strip_test_files() {
    # Remove test artefacts from D before packaging
    rm -rf ${D}${datadir}/myapp/test
    rm -f ${D}${bindir}/run-tests
}

my_fix_permissions() {
    # Ensure correct permissions on sensitive files
    chmod 0600 ${D}${sysconfdir}/myapp/secret.key 2>/dev/null || true
    chmod 0755 ${D}${bindir}/myapp
}
```

Similarly:
- **`IMAGE_PREPROCESS_COMMAND`** — runs before `do_image`
- **`ROOTFS_POSTPROCESS_COMMAND`** — runs after rootfs assembly
- **`IMAGE_POSTPROCESS_COMMAND`** — runs after image creation

---

### Q93. How do you reduce image size in Yocto?

**Answer:**

**1. Start with a minimal image:**
```bitbake
inherit core-image
IMAGE_INSTALL = "packagegroup-core-boot ${CORE_IMAGE_EXTRA_INSTALL}"
```

**2. Use musl libc (significantly smaller than glibc):**
```bitbake
TCLIBC = "musl"
```

**3. Remove debug packages:**
```bitbake
# Don't install -dbg packages
PACKAGE_INSTALL_COMPLEMENTARY:remove = "dbg"
IMAGE_FEATURES:remove = "dbg-pkgs"
```

**4. Strip binaries:**
```bitbake
# Ensure stripping is enabled
INHIBIT_PACKAGE_STRIP = "0"
```

**5. Compressed filesystem:**
```bitbake
IMAGE_FSTYPES = "squashfs-xz"  # highest compression
IMAGE_FSTYPES = "squashfs-lzo" # faster decompression
```

**6. Remove locale data:**
```bitbake
IMAGE_LINGUAS = ""
PACKAGE_INSTALL:remove = "locale-base"
```

**7. `IMAGE_ROOTFS_EXTRA_SPACE`:**
```bitbake
IMAGE_ROOTFS_EXTRA_SPACE = "0"  # no extra headroom
IMAGE_OVERHEAD_FACTOR = "1.0"   # no overhead
```

**8. Audit installed packages:**
```bash
bitbake core-image-minimal -c rootfs
cat tmp/deploy/images//core-image-minimal*.manifest | \
  awk '{print $1, $3}' | sort -k2 -rn | head -30
```

---

### Q94. What is `do_image_complete` and how does it differ from `do_image`?

**Answer:**

- **`do_image`** — runs the image creation tasks for each filesystem type in `IMAGE_FSTYPES`. Actually delegates to type-specific tasks: `do_image_ext4`, `do_image_squashfs`, `do_image_wic`, etc.

- **`do_image_complete`** — a final aggregation task that runs **after all** `do_image_*` tasks complete. It applies `IMAGE_POSTPROCESS_COMMAND` hooks and produces the final artefacts in `deploy/images/`.

```bitbake
# Hook into image completion
IMAGE_POSTPROCESS_COMMAND += "sign_image; "

sign_image() {
    # Sign the image after all filesystem types are created
    for img in ${DEPLOY_DIR_IMAGE}/${IMAGE_NAME}*.ext4; do
        openssl dgst -sha256 -sign ${TOPDIR}/keys/sign.key \
          -out "${img}.sig" "${img}"
    done
}
```

**Task order:**
```
do_rootfs → do_image → do_image_ext4
                    → do_image_squashfs  → do_image_complete → do_deploy
                    → do_image_wic
```

---

### Q95. How do you use `wic` for complex partition layouts?

**Answer:**

`wic` (OpenEmbedded Image Creator) uses `.wks` kickstart files to define disk partition layouts:

```wks
# images/my-product.wks

# Bootloader (GPT, 3s timeout)
bootloader --ptable gpt --timeout=3 --append="quiet rootwait"

# EFI system partition (ESP)
part /boot --source bootimg-efi \
           --sourceparams="loader=grub-efi" \
           --ondisk sda --fstype=efi \
           --label boot --active --align 1024 --size 128M

# Root filesystem A (A/B update)
part /     --source rootfs \
           --ondisk sda --fstype=ext4 \
           --label rootfs-a --align 1024 --size 2048M \
           --uuid 11111111-1111-1111-1111-111111111111

# Root filesystem B (A/B update — empty initially)
part       --ondisk sda --fstype=ext4 \
           --label rootfs-b --align 1024 --size 2048M \
           --uuid 22222222-2222-2222-2222-222222222222

# Persistent data partition
part /data --ondisk sda --fstype=ext4 \
           --label data --align 1024 --size 4096M \
           --uuid 33333333-3333-3333-3333-333333333333
```

```bitbake
# In image recipe
WKS_FILE = "my-product.wks"
IMAGE_FSTYPES += "wic"
do_image_wic[depends] += "grub-efi:do_deploy dosfstools-native:do_populate_sysroot"

# Custom wic plugin for specialized partitioning
WKS_SEARCH_PATH = "${TOPDIR}/../meta-my-product/wic"
```

---

### Q96. How do you manage build history and track regressions?

**Answer:**

`buildhistory` class tracks build outputs across runs using git commits:

```bitbake
INHERIT += "buildhistory"
BUILDHISTORY_COMMIT = "1"   # git commit after each build
BUILDHISTORY_COMMIT_AUTHOR = "Build System <ci@example.com>"
BUILDHISTORY_FEATURES = "image package sdk"
BUILDHISTORY_DIR = "${TOPDIR}/buildhistory"
```

**What it tracks:**
- Package versions, sizes, `RDEPENDS`, file lists
- Image package manifests (installed packages + versions)
- SDK contents

**Comparing builds:**
```bash
# Show what changed between last two builds
buildhistory-diff HEAD~1 HEAD

# Show changes between any two commits
buildhistory-diff abc123 def456

# Check for size regressions
buildhistory-diff HEAD~1 HEAD | grep "size:"

# Look for added/removed packages
buildhistory-diff HEAD~1 HEAD | grep "^[+-].*package:"
```

**CI integration:** treat unexpected package additions or binary size increases as CI failures. The `buildhistory-diff` exit code is non-zero when differences are found.

---

### Q97. What is `BB_HASHBASE_WHITELIST` and when should you use it?

**Answer:**

`BB_HASHBASE_WHITELIST` (now called `BB_BASEHASH_IGNORE_VARS` in Scarthgap+) is a list of variables that are **excluded from the task hash calculation**. If a variable in this list changes, it does not trigger a rebuild.

**Default inclusions:**
```bitbake
BB_BASEHASH_IGNORE_VARS += " \
    TMPDIR BUILD_PATH TOPDIR \
    DL_DIR SSTATE_DIR THISDIR \
    FILE FILESPATH LAYERDIR    \
"
```

These are path variables that legitimately differ between machines (e.g., different users' home directories) but don't affect build outputs.

**Custom use case:**
```bitbake
# A timestamp variable that shouldn't invalidate sstate
BB_BASEHASH_IGNORE_VARS += "MY_BUILD_TIMESTAMP"
```

**Caution:** adding wrong variables causes stale cache hits — sstate returns an old result even though the variable changed meaningfully. Only add variables that genuinely don't affect task output.

---

### Q98. How do you implement a distributed build system with BitBake?

**Answer:**

Yocto supports distributed builds via:

**Option 1 — Shared sstate + hash equivalence (simplest):**
All builders share `SSTATE_DIR` and point to the same `BB_HASHSERVE`. Each machine builds independently but reuses others' cached outputs.

**Option 2 — `distcc` for C/C++ compilation:**
```bitbake
INHERIT += "distcc"
DISTCC_HOSTS = "build-farm-01/8 build-farm-02/8 build-farm-03/8 localhost/4"
PARALLEL_MAKE = "-j24"  # total jobs = sum of distcc slots
```

**Option 3 — icecream (icecc):**
```bitbake
INHERIT += "icecc"
ICECC_PARALLEL_MAKE = "-j64"   # leverage the full compile cluster
ICECC_DISABLED:pn-linux-yocto = "1"  # kernel doesn't benefit from icecc
```

**Option 4 — BitBake remote execution (experimental):**
BitBake's `--server-only` mode allows a scheduler to dispatch tasks to remote workers. Requires identical build environments (containers).

**Best practice for large teams:** shared sstate (NFS or object storage) + hash equivalence server + icecc gives the best incremental build performance without complex orchestration.

---

### Q99. What is `PACKAGE_FEED_URIS` and how do you set up an online package feed?

**Answer:**

Yocto can generate a binary package feed (`.rpm`, `.deb`, or `.ipk` repository) for on-device package management:

**Build-side:**
```bitbake
PACKAGE_CLASSES = "package_ipk"   # or package_deb / package_rpm

# Generate package index after build
PACKAGE_FEED_BASE_PATHS = "ipk"
PACKAGE_FEED_ARCHS = "all cortexa53 cortexa53-poky-linux"

# In image recipe — install package manager
IMAGE_FEATURES += "package-management"
```

**Server-side:**
```bash
# Create package index
bitbake package-index

# Serve packages (example with nginx)
# tmp/deploy/ipk/ → https://pkg.example.com/feeds/ipk/
```

**Device-side (`/etc/opkg/`):**
```ini
src/gz all     http://pkg.example.com/feeds/ipk/all
src/gz arch    http://pkg.example.com/feeds/ipk/cortexa53
src/gz machine http://pkg.example.com/feeds/ipk/qemux86-64
```

```bash
# On device
opkg update
opkg install my-new-package
opkg upgrade
```

---

### Q100. How do you handle `TMPDIR` on a filesystem with limited space?

**Answer:**

```bitbake
# Move TMPDIR to a larger filesystem
TMPDIR = "/fast-nvme/yocto-tmp"

# Or use a different drive for sstate and downloads (shared, larger)
SSTATE_DIR = "/shared-nas/sstate"
DL_DIR     = "/shared-nas/downloads"
```

**Strategies for space management:**

1. **`rm_work`:** most effective — removes per-recipe build directories after packaging.
2. **`TMPDIR` on RAM/tmpfs:** for very fast builds on machines with large RAM (64+ GB). Risk: loss on power failure.
3. **Bind mounts:** symlink `tmp/work` to a different partition.
4. **`cleansstate`:** clean sstate for specific recipes, freeing cache space.
   ```bash
   bitbake my-recipe -c cleansstate
   ```
5. **`cleanall`:** remove all work, stamps, and sstate for a recipe.
   ```bash
   bitbake my-recipe -c cleanall
   ```
6. **prune old sstate entries:**
   ```bash
   # Find sstate entries older than 30 days
   find ${SSTATE_DIR} -name "*.tgz" -mtime +30 -delete
   ```

---

## 6. Debugging & Troubleshooting

---

### Q101. How do you debug a failing `do_compile` task?

**Answer:**

**Step 1 — Read the log:**
```bash
# BitBake shows the log path on failure:
# ERROR: my-recipe-1.0-r0 do_compile: ...
# ERROR: Logfile of failure stored in:
#   tmp/work/.../temp/log.do_compile
cat tmp/work/cortexa53-poky-linux/my-recipe/1.0-r0/temp/log.do_compile
```

**Step 2 — Check the run script:**
```bash
# See exactly what was executed
cat tmp/work/cortexa53-poky-linux/my-recipe/1.0-r0/temp/run.do_compile
```

**Step 3 — Use devshell:**
```bash
bitbake my-recipe -c devshell
# Now in the build environment with all vars set
./configure ${CONFIGUREOPTS}
make ${EXTRA_OEMAKE}
# Read error output interactively
```

**Step 4 — Check environment:**
```bash
bitbake -e my-recipe | grep "^CC="
bitbake -e my-recipe | grep "^DEPENDS="
bitbake -e my-recipe | grep "^STAGING_DIR"
```

**Common causes:**
- Missing `DEPENDS` (header not found) → add to `DEPENDS`
- Wrong sysroot path → check `PKG_CONFIG_SYSROOT_DIR`
- Architecture mismatch → check `DEFAULTTUNE`
- Missing `PACKAGECONFIG` feature → enable the feature

---

### Q102. How do you diagnose and fix "file not found in FILESPATH" errors?

**Answer:**

```
ERROR: my-recipe-1.0-r0 do_fetch:
  Fetcher failure: Unable to fetch URL file://my-config.conf ...
  Path searched: ['/path/to/meta/.../my-config.conf', ...]
```

**Diagnosis:**
```bash
# Check what FILESPATH resolves to
bitbake -e my-recipe | grep "^FILESPATH="
# Output: /path/.../myrecipe-1.0:/path/.../myrecipe:/path/.../files
```

**Causes and fixes:**

1. **File in wrong directory:**
   - Move `my-config.conf` to `${PN}/` or `${BPN}-${PV}/` or `files/` subdirectory

2. **Missing `FILESEXTRAPATHS` in `.bbappend`:**
   ```bitbake
   FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"
   ```

3. **Version mismatch:** file is in `myapp-1.0/` but recipe is `myapp_1.1.bb`:
   - Rename directory to `myapp-1.1/` or use generic `files/` directory

4. **Typo in filename:** verify exact filename case matches `SRC_URI`

---

### Q103. How do you debug sstate cache misses causing unexpected full rebuilds?

**Answer:**

```bash
# Step 1: Enable verbose sstate debugging
BB_VERBOSE_LOGS = "1"
BB_SETSCENE_DEPVALID = ""   # disable setscene filtering (show all attempts)

# Step 2: Run build with verbose output
bitbake my-recipe -v 2>&1 | grep -E "sstate|Sstate|setscene"

# Step 3: Compare task signatures before/after the change
# Save signatures before:
bitbake my-recipe -S none 2>/dev/null
cp tmp/stamps/.../my-recipe.do_compile.sigdata.* /tmp/before.sigdata

# Make the change, then:
bitbake my-recipe -S none 2>/dev/null
bitbake-diffsigs /tmp/before.sigdata tmp/stamps/.../my-recipe.do_compile.sigdata.*

# Step 4: Identify the changing variable
# The diff output shows exactly which variable's value changed
```

**Common causes:**
- `SRCREV` changed (correct behaviour)
- File in `FILESPATH` modified (correct behaviour)
- Variable like `BUILD_TIMESTAMP` (incorrectly) included in hash
- Class or recipe whitespace change (now fixed in modern Yocto)
- `PACKAGE_ARCH` changed (e.g., from `all` to machine-specific)

**Fix for build timestamp:**
```bitbake
BB_BASEHASH_IGNORE_VARS += "BUILD_TIMESTAMP MY_CI_BUILD_NUMBER"
```

---

### Q104. How do you use `bitbake-layers show-recipes` to audit your build?

**Answer:**

```bash
# List all recipes and their providing layers
bitbake-layers show-recipes

# Filter for a specific recipe name
bitbake-layers show-recipes "openssl"
# Output:
# === Matching recipes: ===
# openssl:
#   meta                 3.2.1 (skipped)
#   meta-my-bsp          3.1.5

# Show recipes that are overridden (shadowed by higher-priority layers)
bitbake-layers show-overlayed

# Show which recipes provide a virtual
bitbake-layers show-recipes "virtual/kernel"

# Check recipes for compatibility issues
bitbake -p 2>&1 | grep WARNING | grep -v "skipped\|already"

# Find which recipe provides a specific package
oe-pkgdata-util find-path /usr/bin/openssl
# Output: openssl: /usr/bin/openssl
```

---

### Q105. How do you investigate a QA (insane) failure?

**Answer:**

```
ERROR: QA Issue: my-recipe: ELF binary ... has relocations in .text [textrel]
```

**Step 1 — Understand the check:**
`textrel` means a shared library has text relocations — the `.text` section (code) contains runtime-relocatable addresses, which prevents the OS from mapping the library as read-only shared memory.

**Step 2 — Identify the problematic file:**
```bash
# Find which file triggered the QA
bitbake my-recipe -c package_qa 2>&1 | grep textrel
# Or scan manually:
find tmp/work/*/my-recipe/*/packages-split -name "*.so*" | \
  xargs -I{} readelf -d {} 2>/dev/null | grep TEXTREL
```

**Step 3 — Fix at source level:**
```bash
# textrel often caused by assembler code without PIC
# or forgotten -fPIC flag
EXTRA_OECONF += "--enable-pic"
TARGET_CFLAGS += "-fPIC"
TARGET_CXXFLAGS += "-fPIC"
```

**Step 4 — If fix is not possible (pre-built blob):**
```bitbake
INSANE_SKIP:${PN} += "textrel"
```

---

### Q106. How do you debug a recipe that produces wrong package contents?

**Answer:**

```bash
# Step 1: Examine what's in D after do_install
bitbake my-recipe -c install
find tmp/work/*/my-recipe/*/image/ -type f | sort

# Step 2: Examine package splitting
bitbake my-recipe -c package
find tmp/work/*/my-recipe/*/packages-split/ -type f | sort

# Step 3: Check which package each file was assigned to
oe-pkgdata-util list-pkg-files my-recipe
oe-pkgdata-util list-pkg-files my-recipe-dev

# Step 4: Check for "installed-vs-shipped" QA failures
bitbake my-recipe -c package_qa 2>&1 | grep "installed-vs-shipped"
# This means a file is in D but not in any PACKAGES

# Step 5: Check FILES assignments
bitbake -e my-recipe | grep "^FILES_" | head -30
# Modern Yocto:
bitbake -e my-recipe | grep "^FILES:" | head -30
```

**Common fix patterns:**
```bitbake
# Unclaimed file → add to FILES or a new package
FILES:${PN} += "${libdir}/myapp/plugins/"

# File in wrong package → reorder PACKAGES (first match wins)
PACKAGES =+ "${PN}-plugins"   # check before ${PN}
FILES:${PN}-plugins = "${libdir}/myapp/plugins/"
```

---

### Q107. How do you debug a kernel boot failure caused by a Yocto build?

**Answer:**

**Step 1 — Enable early boot messages:**
```bitbake
# In machine.conf or local.conf
APPEND += "console=ttyS0,115200 earlycon=uart8250,mmio,0x... debug"
```

**Step 2 — Check kernel config:**
```bash
# Verify required configs are set
bitbake linux-yocto -c kernel_configcheck

# Check effective config
bitbake linux-yocto -c kernel_configme
cat tmp/work/*/linux-yocto/*/.config | grep CONFIG_SERIAL
```

**Step 3 — Compare working vs. broken:**
```bash
# Compare .config files
diff tmp/work/*/linux-yocto-old/*/.config \
     tmp/work/*/linux-yocto/*/.config
```

**Step 4 — Boot with minimal initramfs:**
```bitbake
# Build initramfs for debugging
INITRAMFS_IMAGE = "core-image-minimal-initramfs"
INITRAMFS_TASK = "do_rootfs"
```

**Step 5 — QEMU testing before hardware:**
```bash
runqemu qemux86-64 core-image-minimal nographic
runqemu qemux86-64 core-image-minimal kvm nographic
```

**Step 6 — Check DTB:**
```bash
# Verify device tree compiles without errors
bitbake linux-yocto -c compile 2>&1 | grep -i "dtb\|error"
```

---

### Q108. How do you debug a recipe that fails due to a missing sysroot file?

**Answer:**

```
my-app.c:10: fatal error: openssl/ssl.h: No such file or directory
```

**Diagnosis:**
```bash
# Step 1: Check DEPENDS
bitbake -e my-recipe | grep "^DEPENDS="
# Is openssl listed?

# Step 2: Check what's in the recipe sysroot
ls tmp/work/*/my-recipe/*/recipe-sysroot/usr/include/openssl/
# If empty, openssl didn't populate the sysroot

# Step 3: Check openssl's do_populate_sysroot
bitbake openssl -c populate_sysroot
ls tmp/sysroots-components/*/openssl/usr/include/openssl/

# Step 4: Verify DEPENDS spelling
# Wrong: DEPENDS = "Open-SSL"  (case sensitive!)
# Right: DEPENDS = "openssl"

# Step 5: Check if openssl provides headers
oe-pkgdata-util list-pkg-files openssl-dev | grep ssl.h
```

**Fix:**
```bitbake
DEPENDS += "openssl"     # adds openssl to DEPENDS
# This triggers do_prepare_recipe_sysroot to include openssl headers
```

---

### Q109. How do you recover from a corrupted sstate cache?

**Answer:**

Symptoms of corrupted sstate:
- Builds fail with confusing errors in setscene tasks
- `ERROR: sstate: Some broken .tgz files`
- Inconsistent build outputs

**Step 1 — Identify corrupt entries:**
```bash
# Test sstate archive integrity
find ${SSTATE_DIR} -name "*.tgz" -exec tar -tzf {} \; 2>&1 | \
  grep -v "^[a-z]" | grep "Error\|corrupt"
```

**Step 2 — Remove specific corrupt entry:**
```bash
bitbake my-recipe -c cleansstate
# Removes sstate entries for all tasks of my-recipe
```

**Step 3 — Nuclear option (full sstate wipe):**
```bash
# WARNING: causes full rebuild
rm -rf ${SSTATE_DIR}/*

# Or wipe only for a specific machine
find ${SSTATE_DIR} -name "*cortexa53*" -delete
```

**Step 4 — Wipe TMPDIR stamps (force re-check against sstate):**
```bash
find tmp/stamps -name "*.do_*.sigdata*" -delete
```

**Prevention:** mount sstate on a filesystem that supports `fsck` and use checksums. For shared sstate on object storage, use S3 etag validation.

---

### Q110. How do you trace why a specific file ends up in (or missing from) an image?

**Answer:**

```bash
# Step 1: Check the image manifest
grep "my-package" tmp/deploy/images//.manifest

# Step 2: Trace why a package is (or isn't) installed
# Build the dependency graph
bitbake -g my-image
# Look in pn-depends.dot for the chain:
grep "my-package" pn-depends.dot

# Step 3: Check what explicitly installs it
grep -r "my-package" conf/ recipes-*/*/images/*.bb

# Step 4: Check RDEPENDS chain
oe-pkgdata-util read-value RDEPENDS my-package
# Recursively:
bitbake -e my-image | grep "my-package"

# Step 5: For a file in the image
# Find which package provides it
oe-pkgdata-util find-path /usr/bin/my-binary

# Step 6: Verify it's claimed by a PACKAGES entry
oe-pkgdata-util list-pkg-files my-package | grep my-binary
```

---

### Q111. What does `ERROR: Nothing PROVIDES 'virtual/kernel'` mean and how do you fix it?

**Answer:**

This error means no recipe in the active layers provides `virtual/kernel`. Causes:

1. **BSP layer not in `BBLAYERS`:**
   ```bash
   bitbake-layers show-layers | grep bsp
   # If missing, add to bblayers.conf or KAS manifest
   ```

2. **`PREFERRED_PROVIDER_virtual/kernel` points to a non-existent recipe:**
   ```bash
   bitbake -e | grep "PREFERRED_PROVIDER_virtual/kernel"
   # Verify the recipe exists:
   find . -name "linux-my-custom_*.bb"
   ```

3. **`BBMASK` accidentally masked the kernel recipe:**
   ```bash
   bitbake -e | grep "^BBMASK"
   ```

4. **`MACHINE` not set or wrong:**
   ```bash
   bitbake -e | grep "^MACHINE="
   # Verify the machine conf exists:
   bitbake-layers show-recipes "virtual/kernel"
   ```

**Fix:**
```bitbake
# In local.conf or machine.conf
MACHINE = "my-board"
PREFERRED_PROVIDER_virtual/kernel = "linux-my-custom"
```

---

### Q112. How do you debug a race condition in a parallel build?

**Answer:**

Race conditions manifest as intermittent build failures — the same build succeeds sometimes and fails others.

**Identification:**
```bash
# Reproduce: force high parallelism
BB_NUMBER_THREADS = "32"
PARALLEL_MAKE = "-j32"

# Run the failing build multiple times
for i in {1..10}; do
    bitbake my-recipe -f -c compile && echo "PASS $i" || echo "FAIL $i"
done
```

**Common causes:**

1. **Missing `do_compile[depends]`:** Task B uses output of Task A but doesn't declare the dependency. Sometimes Task A finishes first (race success), sometimes not (race failure).

2. **Shared generated file:** multiple parallel make jobs write to the same file.
   ```bash
   # Add serialisation
   do_compile[lockfiles] = "${TMPDIR}/my-shared-lock"
   ```

3. **Makefile parallelism bug:** upstream Makefile has missing dependencies.
   ```bitbake
   # Workaround: disable parallel make for the broken recipe
   PARALLEL_MAKE = ""
   ```

4. **`do_install` race:** multiple `make install` jobs write to the same destination.
   ```bitbake
   PARALLEL_MAKEINST = ""
   ```

---

### Q113. How do you debug an `RDEPENDS` version conflict?

**Answer:**

```
ERROR: Unable to install packages:
  - nothing provides libfoo.so.2 needed by my-app-1.0
```

**Diagnosis:**
```bash
# Check what version of libfoo is being built
bitbake-layers show-recipes "libfoo"
# Output: libfoo 2.1.0 (meta-my-bsp overrides 2.0.0 from meta)

# Check RDEPENDS requirement
oe-pkgdata-util read-value RDEPENDS my-app
# Output: libfoo (>= 2.0) libfoo (< 3.0)

# Check what soname the built libfoo has
readelf -d tmp/work/*/libfoo/*/packages-split/libfoo/usr/lib/libfoo.so.2 \
  | grep SONAME
```

**Causes:**
- Recipe upgraded from `libfoo 2.0` to `libfoo 2.1` but the `.so` version changed to `3.0`
- `RDEPENDS` is referencing a package name that no longer exists (e.g., `libfoo2` → `libfoo3`)

**Fix:**
```bitbake
# Update RDEPENDS to match new version
RDEPENDS:${PN} = "libfoo3"   # instead of libfoo2

# Or pin libfoo version
PREFERRED_VERSION_libfoo = "2.0%"
```

---

### Q114. How do you enable and read `BB_VERBOSE_LOGS`?

**Answer:**

```bitbake
# In local.conf
BB_VERBOSE_LOGS = "1"
```

This causes BitBake to output more information during execution, including:
- Detailed sstate check results (hit/miss and why)
- Fetcher verbose mode (shows actual URLs and download progress)
- Task scheduler decisions

**Per-invocation:**
```bash
bitbake -v my-recipe         # verbose mode
bitbake -D my-recipe         # debug level 1
bitbake -DD my-recipe        # debug level 2 (very verbose)
```

**Redirect to file:**
```bash
bitbake my-recipe 2>&1 | tee build.log
# Then analyse:
grep "^NOTE\|^WARNING\|^ERROR" build.log
grep "sstate" build.log | grep -v "Checking"
```

**Specific module debugging:**
```bash
# Debug the fetcher only
BB_DEBUG_FETCHER = "1" bitbake my-recipe -c fetch
```

---

### Q115. How do you handle `do_fetch` failures behind a corporate proxy?

**Answer:**

```bash
# Set proxy in environment before sourcing oe-init-build-env
export http_proxy="http://proxy.example.com:8080"
export https_proxy="http://proxy.example.com:8080"
export no_proxy="localhost,127.0.0.1,.example.com"
export HTTP_PROXY="${http_proxy}"
export HTTPS_PROXY="${https_proxy}"
source oe-init-build-env build
```

**Or in `local.conf`:**
```bitbake
ENV_PROXY_PASSTHROUGH = "http_proxy https_proxy no_proxy"
```

**For git fetches specifically:**
```bash
git config --global http.proxy http://proxy.example.com:8080
git config --global https.proxy http://proxy.example.com:8080
```

**Internal mirror (recommended for corporate environments):**
```bitbake
# Mirror all external downloads through internal Artifactory/Nexus
PREMIRRORS:prepend = " \
  https?$://.*/.* https://artifactory.example.com/yocto-mirror/PATH \n \
  git://.*/.* https://gitlab.example.com/mirror/BASENAME;protocol=https \n"
BB_FETCH_PREMIRRORONLY = "1"  # block all direct internet access
```

---

### Q116. How do you debug `pkg_postinst` failures during `do_rootfs`?

**Answer:**

```
ERROR: my-recipe: postinstall scriptlet failed on target
```

**Understanding the failure context:**
`pkg_postinst` runs in two phases:
1. **During `do_rootfs` on the host** (if `$D` is set) — offline operations only
2. **First boot on target** — online operations

**Debugging:**

```bash
# Step 1: Run rootfs task with verbose output
bitbake my-image -f -c rootfs 2>&1 | grep -A5 "postinst\|postinstall"

# Step 2: Manually test the script
# The actual script is in:
cat tmp/work/*/my-image/*/rootfs/etc/ipkg-postinsts/my-recipe

# Step 3: Check what the script tries to do in $D context
# Simulate the D context
D=/tmp/test-rootfs bash -c '
  . $(bitbake -e my-recipe | grep "^pkg_postinst:" | head -1)
  pkg_postinst_my-recipe
'
```

**Common issues:**
- Calling `systemctl` when `$D` is set (not valid offline)
- Referencing absolute paths that don't exist in rootfs
- Missing tools in rootfs (e.g., calling `useradd` before `shadow` is installed)

**Fix pattern:**
```bitbake
pkg_postinst:${PN}() {
#!/bin/sh
if [ -n "$D" ]; then
    # Offline: only safe file operations
    mkdir -p $D/var/lib/myapp
else
    # Online: use running system services
    systemctl daemon-reload
    useradd -r myapp
fi
}
```

---

### Q117. How do you debug a `do_image_wic` failure?

**Answer:**

```bash
# Step 1: Verbose wic output
WIC_CREATE_EXTRA_ARGS = "--debug"
bitbake my-image -f -c image_wic

# Step 2: Run wic standalone for testing
wic create my-product.wks \
    --image-name my-image \
    --rootfs-dir tmp/work/*/my-image/*/rootfs \
    --bootimg-dir tmp/deploy/images/my-machine \
    --kernel-dir tmp/deploy/images/my-machine \
    --native-sysroot tmp/sysroots/x86_64-linux \
    --debug

# Step 3: Check missing native tools
# wic needs: parted, mtools, dosfstools
bitbake parted-native dosfstools-native mtools-native -c populate_sysroot

# Step 4: Check WKS file syntax
wic help     # e.g., wic help bootimg-efi

# Step 5: Verify source images exist in deploy
ls tmp/deploy/images/my-machine/
# Should contain: bzImage / Image, *.dtb, *.efi (if EFI)
```

**Common errors:**
- Missing `do_image_wic[depends]` for native tools
- Wrong `--sourceparams` for the `bootimg-efi` plugin
- Partition size too small for rootfs
- Wrong `KERNEL_IMAGETYPE` for the target architecture

---

### Q118. How do you profile memory usage during a Yocto build?

**Answer:**

Large Yocto builds can exhaust memory, causing OOM kills or swap thrashing:

```bash
# Monitor during build
watch -n5 'free -h && echo "---" && \
  ps aux --sort=-rss | head -5'

# Find memory-hungry tasks
buildstats-summary tmp/buildstats// | grep -i memory

# Limit per-task memory (systemd cgroup)
BB_TASK_MAXTHREADS = "8"    # limit concurrent tasks

# Reduce parallelism for memory-intensive tasks
PARALLEL_MAKE:pn-webkit = "-j2"  # WebKit needs huge memory
```

**BitBake cooker memory:**
```bash
# Python heap profiling
python3 -c "
import tracemalloc
tracemalloc.start()
# ... run bitbake parse
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
"
```

**Swap:**
```bash
# Add temporary swap if needed
fallocate -l 16G /swap
chmod 0600 /swap
mkswap /swap
swapon /swap
```

---

### Q119. How do you debug a failed sstate restore that produces incorrect files?

**Answer:**

When a sstate object is restored but contains stale or incorrect files, it's a sign of a **hash collision** or **corrupted sstate object**:

```bash
# Step 1: Identify which sstate object was used
bitbake my-recipe -v 2>&1 | grep "Staging"

# Step 2: Force a fresh build (bypass sstate)
bitbake my-recipe --no-setscene

# Step 3: Verify the fresh build is correct
# If it is, the sstate object was indeed stale

# Step 4: Delete the specific stale sstate entries
bitbake my-recipe -c cleansstate

# Step 5: Rebuild and create a clean sstate entry
bitbake my-recipe

# Step 6: Prevent future occurrences — ensure all inputs are in the hash
# Check if a relevant variable is in BB_BASEHASH_IGNORE_VARS
bitbake -e | grep BB_BASEHASH_IGNORE_VARS
```

**Preventing stale sstate:**
- Never manually edit files in `SSTATE_DIR`
- Use content-addressable storage (CAS) for shared sstate in CI
- Validate sstate checksums: `SSTATE_VERIFY_CHECKSUMS = "1"`

---

### Q120. How do you use `oe-pkgdata-util` for post-build package analysis?

**Answer:**

`oe-pkgdata-util` queries the package database at `tmp/pkgdata/` — a comprehensive database of all built packages and their metadata.

```bash
# Which recipe provides a file?
oe-pkgdata-util find-path /usr/lib/libssl.so.3
# Output: openssl: /usr/lib/libssl.so.3

# What packages does a recipe produce?
oe-pkgdata-util list-packages my-recipe

# What files are in a package?
oe-pkgdata-util list-pkg-files my-app

# What are the RDEPENDS of a package?
oe-pkgdata-util read-value RDEPENDS my-app

# What is the installed size of a package?
oe-pkgdata-util read-value PKGSIZE my-app

# Find all packages that RDEPEND on openssl
oe-pkgdata-util glob my-image '${RDEPENDS}' | tr ' ' '\n' | grep openssl

# Map package names to recipe names
oe-pkgdata-util package-info my-app
# Output: PN=myapp PV=1.0 PR=r0 ...

# Generate a full package inventory
oe-pkgdata-util list-packages | while read pkg; do
    size=$(oe-pkgdata-util read-value PKGSIZE $pkg 2>/dev/null)
    echo "$size $pkg"
done | sort -rn | head -20
```

---

## 7. KAS Workflows

---

### Q121. What is KAS and what problem does it solve in Yocto projects?

**Answer:**

**KAS** (Karlsruhe Application Setup) is a Python-based tool that manages the setup and build phases of BitBake-based projects. It solves the **layer management problem**:

**Without KAS:**
```bash
# Manual setup — error-prone, not reproducible
git clone https://git.yoctoproject.org/poky -b scarthgap
git clone https://github.com/openembedded/meta-openembedded -b scarthgap
git clone https://github.com/meta-freescale/meta-freescale -b scarthgap
# Manually edit bblayers.conf with correct paths
# Manually write local.conf
source poky/oe-init-build-env build
bitbake my-image
```

**With KAS:**
```bash
# Single command — fully reproducible
kas build kas/my-product.yml
```

**What KAS provides:**
1. **Declarative manifest** — one YAML file describes all layers, revisions, and build config
2. **Automatic checkout** — clones and checks out all repos at the declared refspec
3. **Config generation** — auto-generates `bblayers.conf` and `local.conf`
4. **Lock files** — pin all repos to exact SHAs for reproducibility
5. **Composition** — multiple manifest files merged at runtime
6. **Container-ready** — official Docker image `ghcr.io/siemens/kas/kas`

---

### Q122. Describe the full structure of a KAS manifest file.

**Answer:**

```yaml
# kas/my-product.yml
header:
  version: 14                    # manifest format version (always match kas version)
  includes:
    - my-common.yml              # relative path within same repo
    - url: https://git.example.com/kas-fragments.git
      file: distro/my-distro.yml # include from remote repo

# Build settings
machine: my-board                # sets MACHINE
distro: my-distro                # sets DISTRO
target: core-image-full-cmdline  # default build target (can override on CLI)
env:
  - SSTATE_DIR:/shared/sstate    # environment variable → BitBake variable mapping
  - DL_DIR:/shared/downloads

# Repository definitions
repos:
  # The repo containing this kas file
  my-product:
    path: .
    layers:
      meta-my-bsp:               # sub-layer at ./meta-my-bsp
      meta-my-app:               # sub-layer at ./meta-my-app

  # External repo
  poky:
    url: https://git.yoctoproject.org/poky
    refspec: scarthgap            # branch, tag, or SHA
    layers:
      meta:
      meta-poky:
      meta-yocto-bsp:

  meta-openembedded:
    url: https://github.com/openembedded/meta-openembedded.git
    refspec: scarthgap
    layers:
      meta-oe:
      meta-networking:
      meta-python:
      meta-filesystems:

# Inject into bblayers.conf header
bblayers_conf_header:
  standard: |
    POKY_BBLAYERS_CONF_VERSION = "2"

# Inject into local.conf
local_conf_header:
  standard: |
    CONF_VERSION = "2"
    BB_NUMBER_THREADS = "16"
    PARALLEL_MAKE = "-j16"
    INHERIT += "rm_work buildhistory create-spdx"
    BUILDHISTORY_COMMIT = "1"
    BB_HASHSERVE = "auto"
```

---

### Q123. How do KAS include files and composition work?

**Answer:**

KAS supports hierarchical manifest composition, allowing common configuration to be shared and overridden:

**Base config:**
```yaml
# kas/common.yml
header:
  version: 14

repos:
  poky:
    url: https://git.yoctoproject.org/poky
    refspec: scarthgap
    layers:
      meta:
      meta-poky:

local_conf_header:
  security: |
    DISTRO_FEATURES:append = " security"
    INHERIT += "cve-check create-spdx"
```

**Product config:**
```yaml
# kas/product-a.yml
header:
  version: 14
  includes:
    - common.yml        # relative include

machine: product-a-board
distro: my-distro

repos:
  meta-product-a-bsp:
    url: https://git.example.com/meta-product-a-bsp.git
    refspec: main
    layers:
      meta-product-a-bsp:

local_conf_header:
  product: |
    MACHINE_FEATURES:append = " wifi bluetooth"
```

**Merge rules:**
- `repos` are merged (product adds to common's repos)
- `local_conf_header` sections are merged (keys are concatenated)
- `machine` and `distro` from the **outermost** config win
- CLI composition overrides file includes: `kas build a.yml:b.yml` — b.yml's values override a.yml

---

### Q124. How does `kas lock` work and why is it critical for reproducibility?

**Answer:**

```bash
# Generate a lock file pinning all repos to current HEAD
kas lock kas/my-product.yml
# Writes: kas/my-product.lock.yml

# With explicit output path
kas lock kas/my-product.yml --output kas/my-product.lock.yml
```

**Lock file content:**
```yaml
# kas/my-product.lock.yml (auto-generated — commit to VCS)
header:
  version: 14
overrides:
  repos:
    poky:
      refspec: "abc123def456abc123def456abc123def456abc123"
    meta-openembedded:
      refspec: "789abc012def789abc012def789abc012def789abc"
    meta-product-a-bsp:
      refspec: "feedbeef1234feedbeef1234feedbeef1234feedbeef"
```

**Usage in CI (reproducible build):**
```bash
# Development: use floating refs
kas build kas/my-product.yml

# Release/CI: use locked refs
kas build kas/my-product.yml:kas/my-product.lock.yml
```

**Workflow:**
1. Developer updates a layer refspec in `my-product.yml`
2. Runs `kas lock` to update the lock file
3. Commits **both** files together
4. CI uses the lock file — exact same SHAs every time

This is equivalent to `yarn.lock` or `Cargo.lock` in the Yocto world.

---

### Q125. How do you use KAS to manage environment-specific configurations?

**Answer:**

```yaml
# kas/ci.yml — CI-specific overrides
header:
  version: 14

local_conf_header:
  ci: |
    BB_NUMBER_THREADS = "32"
    PARALLEL_MAKE = "-j32"
    DL_DIR = "/cache/downloads"
    SSTATE_DIR = "/cache/sstate"
    BB_FETCH_PREMIRRORONLY = "1"
    PREMIRRORS:prepend = "https?://.*/.* https://mirror.ci.example.com/dl/PATH \n"
```

```yaml
# kas/debug.yml — debug build overlay
header:
  version: 14

local_conf_header:
  debug: |
    IMAGE_FEATURES += "debug-tweaks tools-debug ssh-server-openssh"
    EXTRA_IMAGE_FEATURES += "read-only-rootfs-delayed-postinsts"
    PACKAGECONFIG:append:pn-gdb = " python"
```

**CLI composition:**
```bash
# Developer debug build
kas build kas/product-a.yml:kas/debug.yml

# CI release build with lock
kas build kas/product-a.yml:kas/product-a.lock.yml:kas/ci.yml

# CI debug build
kas build kas/product-a.yml:kas/product-a.lock.yml:kas/ci.yml:kas/debug.yml
```

---

### Q126. How does KAS handle repos that require patches before being used as layers?

**Answer:**

KAS supports applying patches to external repos as part of the checkout process:

```yaml
repos:
  poky:
    url: https://git.yoctoproject.org/poky
    refspec: scarthgap
    patches:
      - repo: my-product   # patch file comes from this repo
        path: patches/poky/0001-fix-signing-for-our-keys.patch
      - repo: my-product
        path: patches/poky/0002-add-custom-qemu-machine.patch
```

**How KAS applies patches:**
1. Checks out `poky` at `scarthgap`
2. For each patch: `git apply <patch-file>` in the repo directory
3. Patches are applied in order

**Limitations:**
- Patches must apply cleanly against the specified refspec
- KAS doesn't manage patch conflicts or rebases automatically
- Better alternative for complex changes: fork the repo and reference your fork

**Workflow for updating patches:**
```bash
cd poky
git am ../../my-product/patches/poky/0001-fix-signing.patch
# After upstream changes:
git rebase scarthgap
git format-patch scarthgap --output-directory ../../my-product/patches/poky/
```

---

### Q127. How do you integrate KAS into a Docker-based CI pipeline?

**Answer:**

**Official KAS Docker image:**
```bash
docker pull ghcr.io/siemens/kas/kas:4.5
```

**`Dockerfile` for custom KAS environment:**
```dockerfile
FROM ghcr.io/siemens/kas/kas:4.5

# Add project-specific native dependencies
USER root
RUN apt-get update && apt-get install -y \
    python3-protobuf \
    device-tree-compiler \
    && rm -rf /var/lib/apt/lists/*

USER user
```

**GitLab CI with Docker:**
```yaml
# .gitlab-ci.yml
variables:
  KAS_IMAGE: "ghcr.io/siemens/kas/kas:4.5"

.kas_build:
  image: ${KAS_IMAGE}
  before_script:
    - export DL_DIR="/cache/downloads"
    - export SSTATE_DIR="/cache/sstate"
  script:
    - kas build ${KAS_CONFIG}:kas/ci.yml
  cache:
    key: "${CI_COMMIT_REF_SLUG}-${CI_JOB_NAME}"
    paths: ["build/sstate-cache/"]

build:product-a:
  extends: .kas_build
  variables:
    KAS_CONFIG: "kas/product-a.yml:kas/product-a.lock.yml"

build:product-b:
  extends: .kas_build
  variables:
    KAS_CONFIG: "kas/product-b.yml:kas/product-b.lock.yml"
```

**Volume mounts (critical for performance):**
```bash
docker run --rm \
  -v "${PWD}:/work" \               # source tree
  -v "/shared/sstate:/sstate" \     # persistent sstate
  -v "/shared/downloads:/dl" \      # persistent downloads
  -e "DL_DIR=/dl" \
  -e "SSTATE_DIR=/sstate" \
  ghcr.io/siemens/kas/kas:4.5 \
  build kas/product-a.yml
```

---

### Q128. How do you use `kas shell` for interactive debugging?

**Answer:**

`kas shell` opens an interactive shell with the full KAS-configured environment (all layers checked out, `bblayers.conf` and `local.conf` generated, `oe-init-build-env` sourced):

```bash
# Enter the configured build environment
kas shell kas/my-product.yml

# Inside the shell — all BitBake tools available:
bitbake -e my-recipe | grep "^DEPENDS="
bitbake my-recipe -c devshell
bitbake-layers show-layers
devtool status
```

**Non-interactive (run a single command):**
```bash
kas shell kas/my-product.yml -c "bitbake -e my-recipe > /tmp/env.txt"
kas shell kas/my-product.yml -c "bitbake-layers show-recipes | grep kernel"
kas shell kas/my-product.yml -c "bitbake core-image-minimal -c cve_check"
```

**Build a specific task:**
```bash
kas build kas/my-product.yml -- -c compile my-recipe
kas build kas/my-product.yml -- -c menuconfig virtual/kernel
kas build kas/my-product.yml -- --continue core-image-minimal
```

The `--` separator passes arguments directly to `bitbake`.

---

### Q129. What is `kas dump` and how is it used for debugging?

**Answer:**

`kas dump` prints the **fully merged and resolved** KAS configuration after processing all includes and overrides. It shows exactly what KAS will pass to BitBake.

```bash
# Show merged config in YAML format
kas dump kas/my-product.yml

# Show in JSON format
kas dump --format json kas/my-product.yml

# Show with lock file applied
kas dump kas/my-product.yml:kas/my-product.lock.yml

# Show resolved local.conf content
kas dump kas/my-product.yml | python3 -c "
import sys, yaml
data = yaml.safe_load(sys.stdin)
print(data.get('local_conf_header', {}).get('standard', ''))
"
```

**Output example:**
```yaml
header:
  version: 14
machine: my-board
distro: my-distro
target: core-image-full-cmdline
repos:
  poky:
    url: https://git.yoctoproject.org/poky
    refspec: "abc123..."   # resolved from lock file
    path: /work/poky
    layers:
      meta: {}
      meta-poky: {}
# ...
```

---

### Q130. How do you handle KAS in a monorepo where the build directory is also committed?

**Answer:**

KAS supports monorepo layouts where `kas/` files and source code live together:

```
my-platform/
├── kas/
│   ├── common.yml
│   ├── product-a.yml
│   └── product-a.lock.yml
├── meta-bsp/
│   └── conf/layer.conf
├── meta-distro/
│   └── conf/layer.conf
├── meta-app/
│   └── conf/layer.conf
└── scripts/
    └── build.sh
```

```yaml
# kas/product-a.yml
header:
  version: 14

repos:
  my-platform:
    path: .           # "." = the repo containing this kas file
    layers:
      meta-bsp:
      meta-distro:
      meta-app:

  # External layers
  poky:
    url: https://git.yoctoproject.org/poky
    refspec: scarthgap
    layers:
      meta:
      meta-poky:
```

**Build from monorepo root:**
```bash
kas build kas/product-a.yml
# KAS creates build/ directory relative to the kas file location
```

**Custom build directory:**
```bash
KAS_BUILD_DIR=/tmp/my-build kas build kas/product-a.yml
```

---

### Q131. How does KAS compare to `repo` tool (Google's Android repo tool)?

**Answer:**

| Feature | KAS | `repo` (Google) |
|---|---|---|
| **Primary use** | Yocto / BitBake projects | Android (AOSP) multi-repo projects |
| **Manifest format** | YAML | XML |
| **BitBake integration** | Native (generates bblayers.conf, runs bitbake) | None |
| **Lock files** | Built-in (`kas lock`) | Separate (`repo manifest -o`) |
| **Config composition** | Multi-file YAML merge | Single XML with includes |
| **Container support** | Official Docker image | Manual |
| **Patch management** | Built-in `patches:` field | `<patch>` elements |
| **Build invocation** | `kas build` | Manual |

**Migration from repo:** some Yocto projects historically used `repo`. Migrating to KAS provides better BitBake integration and simpler YAML syntax. A KAS manifest for a `repo`-managed project requires mapping each `<project>` element to a `repos:` entry.

---

### Q132. How do you handle KAS manifests for projects with optional feature layers?

**Answer:**

```yaml
# kas/product-a-base.yml — minimal, always required
header:
  version: 14

machine: product-a
distro: my-distro

repos:
  poky:
    url: https://git.yoctoproject.org/poky
    refspec: scarthgap
    layers:
      meta:
      meta-poky:
  my-product:
    path: .
    layers:
      meta-bsp:
      meta-distro:
```

```yaml
# kas/feature-wifi.yml — add wifi support
header:
  version: 14

repos:
  meta-wifi:
    url: https://git.example.com/meta-wifi.git
    refspec: scarthgap

local_conf_header:
  wifi: |
    DISTRO_FEATURES:append = " wifi"
    IMAGE_INSTALL:append = " wpa-supplicant iw wireless-regdb"
```

```yaml
# kas/feature-graphics.yml — add graphics support
header:
  version: 14

repos:
  meta-qt6:
    url: https://code.qt.io/yocto/meta-qt6.git
    refspec: 6.6

local_conf_header:
  qt6: |
    DISTRO_FEATURES:append = " opengl wayland"
    IMAGE_INSTALL:append = " qtbase qtdeclarative"
```

**Builds:**
```bash
# Minimal
kas build kas/product-a-base.yml

# With wifi
kas build kas/product-a-base.yml:kas/feature-wifi.yml

# Full featured
kas build kas/product-a-base.yml:kas/feature-wifi.yml:kas/feature-graphics.yml
```

---

### Q133. How do you validate a KAS manifest without building?

**Answer:**

```bash
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('kas/my-product.yml'))" && echo OK

# Validate KAS manifest structure (kas checks format on load)
kas dump kas/my-product.yml > /dev/null && echo "Manifest valid"

# Check that all repos can be resolved (without cloning)
kas checkout kas/my-product.yml --skip-build 2>&1

# Dry run — checkout only, no build
kas checkout kas/my-product.yml
# Clones all repos but doesn't start bitbake

# Validate LAYERSERIES_COMPAT compatibility
kas shell kas/my-product.yml -c "bitbake -p 2>&1 | grep -i compat"

# Check for layer dependency issues
kas shell kas/my-product.yml -c \
  "bitbake-layers show-cross-depends 2>&1 | grep WARNING"
```

**CI validation stage:**
```yaml
# .gitlab-ci.yml
validate:
  stage: validate
  image: ghcr.io/siemens/kas/kas:4.5
  script:
    - kas dump kas/product-a.yml > /dev/null
    - kas checkout kas/product-a.yml
    - kas shell kas/product-a.yml -c "bitbake -p"
```

---

### Q134. How do you manage secrets (tokens, credentials) in KAS CI workflows?

**Answer:**

**Never embed credentials in KAS manifests.** Use environment variables and CI secret management:

**SSH keys (git:// access):**
```yaml
# kas/my-product.yml — use SSH without credentials in file
repos:
  private-meta-layer:
    url: git@git.example.com:org/meta-layer.git
    refspec: main
```

```bash
# CI: inject SSH key via environment
eval $(ssh-agent -s)
echo "${CI_SSH_KEY}" | ssh-add -
kas checkout kas/my-product.yml
```

**HTTPS tokens:**
```bash
# CI: use git credential helper
git config --global credential.helper \
  "!f() { echo username=ci-bot; echo password=${CI_TOKEN}; }; f"
```

**KAS environment variable forwarding:**
```yaml
# kas/my-product.yml
env:
  - SSTATE_MIRRORS    # forward env var to BitBake variable
  - BB_HASHSERVE
  - MY_SIGNING_KEY_PATH
```

```bash
# CI: set env vars in runner
export SSTATE_MIRRORS="file://.* https://sstate.ci.example.com/PATH"
kas build kas/my-product.yml
```

---

### Q135. What are KAS plugins and how do you write a custom one?

**Answer:**

KAS plugins extend KAS with custom commands:

```python
# kas_plugins/report.py
"""Generate a build report after each build."""

import json
import os
from pathlib import Path
from kas.plugins import Plugin

class ReportPlugin(Plugin):
    """Generate a JSON build report."""

    name = "report"

    def setup_parser(self, parser):
        parser.add_argument(
            '--output', default='build-report.json',
            help='Output report file path'
        )

    def run(self, args):
        ctx = self.get_context()

        # Access build environment
        build_dir = ctx.build_dir
        deploy_dir = Path(build_dir) / 'tmp' / 'deploy'

        report = {
            'machine': ctx.config.get_machine(),
            'distro': ctx.config.get_distro(),
            'images': [],
        }

        # Scan deployed images
        images_dir = deploy_dir / 'images' / ctx.config.get_machine()
        if images_dir.exists():
            report['images'] = [f.name for f in images_dir.iterdir()
                                if f.suffix in ('.ext4', '.wic', '.squashfs')]

        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"Report written to {args.output}")
```

**Plugin discovery:**
```bash
# KAS discovers plugins in:
# - kas_plugins/ directory (relative to working directory)
# - ~/.kas/plugins/
# - Paths in KAS_PLUGIN_DIR environment variable

# Usage:
kas report kas/my-product.yml --output /tmp/build-report.json
```

---

## 8. Embedded Linux Integration

---

### Q136. How do you configure and customise the Linux kernel in Yocto?

**Answer:**

**Three approaches (in order of preference):**

**1. Configuration fragments (recommended):**
```bitbake
# In .bbappend
SRC_URI += "file://enable-can.cfg file://disable-debug.cfg"
```
```
# enable-can.cfg
CONFIG_CAN=y
CONFIG_CAN_DEV=y
CONFIG_CAN_FLEXCAN=y
```

**2. Interactive `menuconfig`:**
```bash
bitbake linux-yocto -c menuconfig
# Make changes, save
bitbake linux-yocto -c diffconfig
# Produces fragment with your changes
```

**3. Full `defconfig`:**
```bitbake
SRC_URI += "file://defconfig"
KCONFIG_MODE = "--alldefconfig"
```

**Verify applied config:**
```bash
bitbake linux-yocto -c kernel_configcheck 2>&1 | grep "Warning\|Error"
# Shows which requested configs were not applied (dependency missing)
```

**linux-yocto specific features:**
```bitbake
# Kernel features from meta/cfg/kernel-cache
KERNEL_FEATURES:append = " features/netfilter/netfilter.scc"
KERNEL_FEATURES:append = " cfg/virtio.scc"
```

---

### Q137. How do you integrate device tree overlays in Yocto?

**Answer:**

```bitbake
# In machine.conf
KERNEL_DEVICETREE = " \
    broadcom/bcm2711-rpi-4-b.dtb    \
    broadcom/bcm2711-rpi-4-b-overlay.dtbo \
"

# Or via .bbappend
KERNEL_DEVICETREE:append:my-board = " my-board-overlay.dtbo"
```

**Custom DTS in BSP layer:**
```
meta-my-bsp/
└── recipes-kernel/
    └── linux/
        ├── linux-yocto_%.bbappend
        └── files/
            └── my-board.dts        ← custom device tree
```

```bitbake
# linux-yocto_%.bbappend
FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
SRC_URI += "file://my-board.dts"

do_configure:append() {
    # Copy DTS into kernel tree
    cp ${WORKDIR}/my-board.dts ${S}/arch/arm64/boot/dts/my-vendor/
}
```

**U-Boot DTB overlay loading:**
```bash
# In U-Boot environment
fdt addr $fdt_addr_r
fdt resize 8192
load mmc 0:1 $loadaddr my-board-overlay.dtbo
fdt apply $loadaddr
```

---

### Q138. How do you create a minimal initramfs in Yocto?

**Answer:**

```bitbake
# meta-my-layer/recipes-core/images/core-image-initramfs.bb
DESCRIPTION = "Minimal initramfs for early boot"
LICENSE = "MIT"

inherit core-image

PACKAGE_INSTALL = " \
    busybox          \
    udev             \
    kmod             \
    util-linux-mount \
    e2fsprogs-e2fsck \
"

# Initramfs must be very small
IMAGE_FSTYPES = "cpio.lz4"
IMAGE_ROOTFS_SIZE = "65536"

# No package manager needed
IMAGE_FEATURES:remove = "package-management"

# Disable all locale
IMAGE_LINGUAS = ""
```

```bitbake
# Link initramfs into kernel build (combined kernel+initramfs image)
INITRAMFS_IMAGE = "core-image-initramfs"
INITRAMFS_IMAGE_BUNDLE = "1"
# Produces: zImage with embedded initramfs
```

**Init script (`/init`):**
```sh
#!/bin/sh
mount -t devtmpfs devtmpfs /dev
mount -t proc proc /proc
mount -t sysfs sysfs /sys

# Find and mount real rootfs
ROOT_DEV=$(cat /proc/cmdline | tr ' ' '\n' | grep root= | cut -d= -f2)
mount ${ROOT_DEV} /mnt/root

# Switch to real root
exec switch_root /mnt/root /sbin/init
```

---

### Q139. How do you set up U-Boot environment in Yocto?

**Answer:**

```bitbake
# meta-my-bsp/conf/machine/my-board.conf
PREFERRED_PROVIDER_virtual/bootloader = "u-boot-my-board"
UBOOT_MACHINE = "my_board_defconfig"
UBOOT_ENTRYPOINT = "0x80008000"
UBOOT_LOADADDRESS = "0x80008000"

# For SPL
SPL_BINARY = "MLO"         # or "u-boot-spl.bin" depending on SoC
UBOOT_BINARY = "u-boot.img"
```

```bitbake
# meta-my-bsp/recipes-bsp/u-boot/u-boot-my-board_2024.01.bb
require recipes-bsp/u-boot/u-boot.inc

PROVIDES += "virtual/bootloader"
COMPATIBLE_MACHINE = "my-board"

SRC_URI:append:my-board = " file://0001-my-board-support.patch"

do_deploy:append() {
    install -d ${DEPLOYDIR}
    # Deploy environment file
    install -m 0644 ${WORKDIR}/u-boot-env.txt ${DEPLOYDIR}/
}
```

**U-Boot environment file (`uEnv.txt`):**
```
bootcmd=run mmcboot
bootdelay=2
mmcdev=0
mmcpart=1
mmcroot=/dev/mmcblk0p2
mmcargs=setenv bootargs root=${mmcroot} rootfstype=ext4 rootwait console=ttyS0,115200
mmcboot=mmc dev ${mmcdev}; fatload mmc ${mmcdev}:${mmcpart} ${kernel_addr_r} Image; run mmcargs; booti ${kernel_addr_r} - ${fdt_addr_r}
```

---

### Q140. How do you handle firmware blobs and binary drivers in Yocto?

**Answer:**

Binary blobs require careful handling for licensing and build system integration:

```bitbake
# recipes-kernel/linux-firmware/linux-firmware_%.bbappend
RDEPENDS:kernel-module-my-driver += "firmware-my-chip"
```

```bitbake
# recipes-bsp/firmware-my-chip/firmware-my-chip_1.0.bb
SUMMARY = "Proprietary firmware for My-Chip"
LICENSE = "Proprietary"
LIC_FILES_CHKSUM = "file://LICENSE;md5=..."
LICENSE_FLAGS = "commercial"

inherit bin_package

SRC_URI = "https://vendor.example.com/firmware-${PV}.tar.gz"
SRC_URI[sha256sum] = "..."

do_install() {
    install -d ${D}${nonarch_base_libdir}/firmware/my-chip
    install -m 0644 ${S}/*.bin ${D}${nonarch_base_libdir}/firmware/my-chip/

    # Install udev rules for automatic firmware loading
    install -d ${D}${sysconfdir}/udev/rules.d
    install -m 0644 ${S}/my-chip.rules \
                    ${D}${sysconfdir}/udev/rules.d/70-my-chip.rules
}

FILES:${PN} = " \
    ${nonarch_base_libdir}/firmware/my-chip/ \
    ${sysconfdir}/udev/rules.d/70-my-chip.rules \
"

# Skip QA checks that don't apply to firmware blobs
INSANE_SKIP:${PN} = "arch"
```

---

### Q141. How do you enable and configure overlay filesystems in Yocto?

**Answer:**

Overlay filesystems (overlayfs) allow a read-only rootfs with a writable upper layer, useful for combining `read-only-rootfs` with the ability to persist changes:

```bitbake
# In image recipe or distro
IMAGE_FEATURES += "read-only-rootfs"

DISTRO_FEATURES:append = " overlayfs"
IMAGE_FEATURES:append = " overlayfs-etc"   # Kirkstone+ feature
```

```bitbake
# Configure overlayfs-etc (makes /etc writable via overlayfs)
OVERLAYFS_ETC_MOUNT_POINT = "/data"    # where the upper layer lives
OVERLAYFS_ETC_FSTYPE = "ext4"          # filesystem of upper layer
OVERLAYFS_ETC_DEVICE = "/dev/sda3"     # writable partition
```

**Manual systemd mount unit approach:**
```ini
# files/var-overlay.mount (systemd)
[Unit]
Description=Overlay for /var
Before=local-fs.target

[Mount]
What=overlay
Where=/var
Type=overlay
Options=lowerdir=/var,upperdir=/data/overlay/var/upper,workdir=/data/overlay/var/work

[Install]
WantedBy=local-fs.target
```

---

### Q142. How do you integrate a real-time kernel (PREEMPT_RT) in Yocto?

**Answer:**

```bitbake
# In kernel .bbappend
FILESEXTRAPATHS:prepend := "${THISDIR}/linux-yocto:"

# Apply RT patch series
SRC_URI += " \
    https://cdn.kernel.org/pub/linux/kernel/projects/rt/6.6/\
    patch-6.6.30-rt30.patch.gz;name=rt-patch \
"
SRC_URI[rt-patch.sha256sum] = "..."

# RT kernel config fragment
SRC_URI += "file://rt-enable.cfg"
```

```
# rt-enable.cfg
CONFIG_PREEMPT_RT=y
CONFIG_HZ_1000=y
CONFIG_HZ=1000
CONFIG_CPU_FREQ_DEFAULT_GOV_PERFORMANCE=y
```

```bitbake
# In machine.conf
KERNEL_FEATURES:append = " features/preempt-rt/preempt-rt.scc"
```

**Testing RT latency (in image):**
```bitbake
IMAGE_INSTALL += "rt-tests cyclictest hwlatdetect"
```

```bash
# On target
cyclictest -p 80 -t5 -n -i 200 --histogram=400 --histfile=hist.txt
```

---

### Q143. How do you set up network boot (NFS rootfs) for development?

**Answer:**

```bitbake
# local.conf — development configuration
EXTRA_IMAGE_FEATURES = "debug-tweaks"

# Build the NFS-mountable rootfs
IMAGE_FSTYPES = "tar.bz2"
```

**NFS server setup (host):**
```bash
# Extract rootfs
tar -xjf core-image-minimal-my-board.tar.bz2 -C /nfsroot/my-board/
chmod 777 /nfsroot/my-board

# /etc/exports
/nfsroot/my-board *(rw,sync,no_subtree_check,no_root_squash)

exportfs -ra
systemctl restart nfs-server
```

**U-Boot bootargs:**
```
setenv bootargs root=/dev/nfs nfsroot=192.168.1.100:/nfsroot/my-board,v3 \
  ip=192.168.1.200:192.168.1.100::255.255.255.0::eth0:off \
  console=ttyS0,115200 rootwait rw
```

**Kernel requirements (in config fragment):**
```
# nfs-root.cfg
CONFIG_NFS_FS=y
CONFIG_NFS_V3=y
CONFIG_ROOT_NFS=y
CONFIG_IP_PNP=y
CONFIG_IP_PNP_DHCP=y
```

---

### Q144. How do you integrate busybox customisation in Yocto?

**Answer:**

```bitbake
# meta-my-product/recipes-core/busybox/busybox_%.bbappend

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

# Custom minimal busybox configuration
SRC_URI += "file://my-minimal.cfg"

# Disable specific applets for security/size
SRC_URI += "file://disable-telnetd.cfg"
```

```
# files/disable-telnetd.cfg
# CONFIG_TELNETD is not set
# CONFIG_TFTP is not set
# CONFIG_FTPD is not set
```

```bash
# Interactive menuconfig for busybox
bitbake busybox -c menuconfig

# Generate fragment from changes
bitbake busybox -c diffconfig
```

**Busybox init configuration:**
```
# files/inittab
::sysinit:/etc/init.d/rcS
::askfirst:-/bin/sh
::ctrlaltdel:/sbin/reboot
::shutdown:/etc/init.d/rcK
::shutdown:/sbin/swapoff -a
::shutdown:/bin/umount -a -r
::restart:/sbin/init
```

---

### Q145. How do you handle `MACHINE_FEATURES` and what are the common values?

**Answer:**

`MACHINE_FEATURES` declares hardware capabilities present on the machine. Recipes check this to conditionally include hardware-specific support:

```bitbake
# In machine.conf
MACHINE_FEATURES = "acpi alsa bluetooth can efi ext2 keyboard \
                    pcmcia pci rtc screen serial touchscreen usbgadget \
                    usbhost vfat wifi"
```

| Feature | Effect |
|---|---|
| `acpi` | Enable ACPI power management |
| `alsa` | Audio support packages |
| `bluetooth` | BlueZ packages |
| `can` | CAN bus driver support |
| `efi` | EFI bootloader configuration |
| `keyboard` | Console keyboard handling |
| `pcmcia` | PCMCIA card services |
| `rtc` | Real-time clock hardware |
| `screen` | Framebuffer / display |
| `serial` | Serial console support |
| `touchscreen` | tslib touch calibration |
| `usbgadget` | USB device mode |
| `usbhost` | USB host mode |
| `vfat` | FAT filesystem support (SD card) |
| `wifi` | Wireless LAN support |

**Recipe check:**
```bitbake
PACKAGECONFIG:append = "${@bb.utils.contains('MACHINE_FEATURES', 'bluetooth', 'bluez', '', d)}"
```

---

### Q146. How do you configure `systemd` in a Yocto image?

**Answer:**

```bitbake
# In distro.conf
INIT_MANAGER = "systemd"
DISTRO_FEATURES:append = " systemd"
DISTRO_FEATURES:remove = "sysvinit"

# Ensure systemd-udev is the device manager
VIRTUAL-RUNTIME_dev_manager = "udev"
VIRTUAL-RUNTIME_login_manager = "shadow-base"
```

```bitbake
# In image recipe or local.conf — systemd configuration
SYSTEMD_DEFAULT_TARGET = "multi-user.target"

# Disable unused systemd services
IMAGE_INSTALL += "systemd-conf"
```

**Custom systemd-conf:**
```bitbake
# recipes-core/systemd-conf/systemd-conf_%.bbappend
FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
SRC_URI += "file://disable-unnecessary.conf"

do_install:append() {
    # Mask services not needed on embedded
    install -d ${D}${systemd_unitdir}/system/systemd-timesyncd.service.d
}
```

**Reduce boot time:**
```bitbake
# Disable unnecessary services
IMAGE_INSTALL += "systemd-analyze"
# On target: systemd-analyze blame / critical-chain
```

---

### Q147. How do you add a user and group in a Yocto recipe?

**Answer:**

```bitbake
inherit useradd

# Declare packages that need user/group creation
USERADD_PACKAGES = "${PN}"

# useradd parameters (same flags as the useradd command)
USERADD_PARAM:${PN} = " \
    --system                        \
    --user-group                    \
    --uid 1001                      \
    --shell /sbin/nologin           \
    --home-dir /var/lib/myapp       \
    --no-create-home                \
    --comment 'My Application User' \
    myapp"

# groupadd parameters
GROUPADD_PARAM:${PN} = "--system --gid 1001 myapp"

# Group membership (add existing user to group)
GROUPMEMS_PARAM:${PN} = "--group myapp --add myapp"

do_install:append() {
    # Create home directory with correct ownership
    install -d -m 0750 ${D}/var/lib/myapp
    chown -R root:root ${D}/var/lib/myapp
}
```

**Static UID/GID management:** maintain a `files/passwd` and `files/group` mapping in your distro layer to ensure consistent UIDs/GIDs across all machines:
```bitbake
# In useradd.bbclass equivalent
USERADD_UID_TABLES = "${TOPDIR}/../meta-my-distro/files/passwd"
USERADD_GID_TABLES = "${TOPDIR}/../meta-my-distro/files/group"
```

---

### Q148. How do you implement A/B partition update support in Yocto?

**Answer:**

A/B (dual-bank) updates require:
1. Partition layout with two root partitions
2. A bootloader that supports slot selection
3. An update agent (e.g., RAUC, SWUpdate, Mender)

**RAUC integration:**
```bitbake
# Add RAUC to image
IMAGE_INSTALL += "rauc"
MACHINE_FEATURES:append = " efi"

# RAUC system config
RAUC_KEYRING_FILE = "${TOPDIR}/../keys/ca.cert.pem"
```

```bitbake
# meta-rauc/recipes-core/rauc/rauc_%.bbappend
FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
SRC_URI += "file://system.conf"
```

```ini
# files/system.conf
[system]
compatible=my-product
bootloader=uboot
mountprefix=/mnt

[keyring]
path=/etc/rauc/keyring.pem

[slot.rootfs.0]
device=/dev/mmcblk0p2
type=ext4
bootname=A

[slot.rootfs.1]
device=/dev/mmcblk0p3
type=ext4
bootname=B
```

**WIC partition layout:**
```wks
part /boot --source bootimg-efi --size 128M
part / --source rootfs --label rootfs-a --size 2048M
part   --source empty  --label rootfs-b --size 2048M  # slot B
part /data --size 4096M
```

---

### Q149. How do you integrate `swupdate` for OTA updates?

**Answer:**

```bitbake
# Image recipe
IMAGE_INSTALL += "swupdate"

# swupdate configuration
FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
SRC_URI += "file://swupdate.cfg"
```

```bitbake
# Build a .swu update artefact
IMAGE_CLASSES += "swupdate-image"

# Define update bundle contents
SWUPDATE_IMAGES = "core-image-minimal"
SWUPDATE_IMAGES_FSTYPES:core-image-minimal = ".ext4.gz"
SWUPDATE_SIGNING = "RSA"
SWUPDATE_SIGN_KEY = "${TOPDIR}/../keys/swupdate-priv.pem"
```

**`sw-description` (CPIO manifest):**
```
software =
{
    version = "1.0.0";
    hardware-compatibility: ["1.0"];

    images: (
        {
            filename = "core-image-minimal.ext4.gz";
            type = "raw";
            device = "/dev/mmcblk0p2";
            compressed = true;
            installed-directly = true;
        }
    );

    scripts: (
        {
            filename = "post-update.sh";
            type = "shellscript";
        }
    );
}
```

---

### Q150. How do you profile boot time and optimize it in a Yocto image?

**Answer:**

**Measurement tools:**
```bash
# On target
systemd-analyze time
systemd-analyze blame
systemd-analyze critical-chain

# Bootchart
IMAGE_INSTALL += "bootchart2"
# Add to kernel cmdline:
APPEND += "initcall_debug printk.time=1 quiet"
```

**Optimisation techniques:**

1. **Systemd service dependencies:** use `After=` and `Requires=` correctly; don't `Wants=network.target` if not needed.

2. **Socket activation:** convert services to socket-activated to defer startup:
   ```ini
   [Socket]
   ListenStream=/run/myapp.sock
   [Install]
   WantedBy=sockets.target
   ```

3. **Remove `getty` on unused TTYs:**
   ```bitbake
   SYSTEMD_AUTO_ENABLE:serial-getty = "disable"
   ```

4. **Prelink / prelinking:** (older systems) pre-link binaries to reduce dynamic linker work.

5. **Compressed rootfs with fast decompression:**
   ```bitbake
   IMAGE_FSTYPES = "squashfs-lzo"  # faster than xz for boot
   ```

6. **Reduce initrd size:** smaller initramfs = faster kernel decompress.

7. **`quiet` kernel parameter:** suppresses kernel messages, reducing console I/O.

8. **`fsck.mode=skip`:** skip filesystem check on known-clean systems.

---

### Q151. How do you handle timezone and NTP configuration in Yocto?

**Answer:**

```bitbake
# Set default timezone
IMAGE_INSTALL += "tzdata"
DEFAULT_TIMEZONE = "UTC"   # or "America/New_York", "Europe/Berlin"
```

```bitbake
# NTP client — multiple options
IMAGE_INSTALL += "chrony"          # recommended: lightweight, accurate
# or
IMAGE_INSTALL += "systemd-timesyncd"  # systemd-integrated (simpler)
# or
IMAGE_INSTALL += "ntpdate"         # one-shot sync (minimal)
```

**Chrony configuration:**
```
# files/chrony.conf
pool 2.debian.pool.ntp.org iburst
driftfile /var/lib/chrony/drift
makestep 1.0 3
rtcsync
```

**For air-gapped (no internet):**
```
# files/chrony.conf
server 192.168.1.1 iburst prefer  # internal NTP server
# Or use hardware RTC:
refclock PHC /dev/ptp0 poll 3 dpoll -2
```

**systemd-timesyncd:**
```ini
# /etc/systemd/timesyncd.conf
[Time]
NTP=192.168.1.1
FallbackNTP=
```

---

### Q152. How do you add Python 3 support to a Yocto image?

**Answer:**

```bitbake
# Minimal Python 3 runtime
IMAGE_INSTALL += "python3"

# Full Python 3 with common modules
IMAGE_INSTALL += " \
    python3          \
    python3-asyncio  \
    python3-json     \
    python3-logging  \
    python3-threading \
    python3-urllib   \
    python3-pip      \
"

# Python packages from PyPI (via recipe)
IMAGE_INSTALL += "python3-requests python3-pyyaml"
```

**Recipe for Python application:**
```bitbake
# recipes-app/my-python-app/my-python-app_1.0.bb
SUMMARY = "My Python Application"
LICENSE = "MIT"

SRC_URI = "git://github.com/example/myapp.git;protocol=https;branch=main"
SRCREV = "abc123..."
S = "${WORKDIR}/git"

inherit setuptools3

RDEPENDS:${PN} = "python3 python3-requests"

do_install:append() {
    install -d ${D}${sysconfdir}/my-python-app
    install -m 0644 ${S}/config.yaml ${D}${sysconfdir}/my-python-app/
}
```

**Cross-compilation consideration:**
Python extensions with C modules must be cross-compiled:
```bitbake
inherit python3native   # use host Python for build scripts
inherit setuptools3     # cross-compiles C extensions
```

---

### Q153. What is `IMAGE_BOOT_FILES` and how does it work with WIC?

**Answer:**

`IMAGE_BOOT_FILES` specifies files to be copied into the boot partition of a WIC image. It works with `wic` sources like `bootimg-partition` and `bootimg-efi`.

```bitbake
# In machine.conf
IMAGE_BOOT_FILES = " \
    ${KERNEL_IMAGETYPE}                          \
    ${KERNEL_DEVICETREE}                         \
    u-boot.img                                   \
    MLO                                          \
    boot.scr;boot.scr                            \
"

# Rename during copy: src;dest
IMAGE_BOOT_FILES += "zImage;Image"   # copy zImage as 'Image'
```

```wks
# my-board.wks
part /boot --source bootimg-partition \
           --ondisk mmcblk0 --fstype=vfat \
           --label boot --active --align 4
part /     --source rootfs \
           --ondisk mmcblk0 --fstype=ext4 \
           --label root --align 4
```

**Custom boot script:**
```bash
# Generate boot.scr from boot.cmd
mkimage -C none -A arm -T script -d boot.cmd boot.scr
```

---

### Q154. How do you handle persistent storage and writable areas in a read-only rootfs?

**Answer:**

**Strategy 1 — `/data` partition (most robust):**
```bitbake
# In image recipe
IMAGE_FEATURES += "read-only-rootfs"

# Declare which paths need to be writable (handled by volatile-binds)
VOLATILE_BINDS:append = "/data/var /var"
```

```wks
part /     --source rootfs --fstype=squashfs --label root
part /data --fstype=ext4   --label data --size 512M
```

**Strategy 2 — tmpfs for volatile paths:**
```ini
# systemd tmpfiles.d/myapp.conf
d /run/myapp 0755 myapp myapp -
d /tmp/myapp 0700 myapp myapp -
```

**Strategy 3 — overlayfs:**
```bitbake
IMAGE_FEATURES += "overlayfs-etc"
OVERLAYFS_ETC_MOUNT_POINT = "/data"
```

**Strategy 4 — `volatile-binds`:**
```bitbake
IMAGE_INSTALL += "volatile-binds"
# /etc/volatile-binds.conf:
# /var/log       tmpfs
# /var/run       tmpfs
# /home/myuser   /data/home/myuser
```

---

### Q155. How do you integrate Docker/container support in a Yocto image?

**Answer:**

```bitbake
# Add containerd (preferred over Docker for embedded)
IMAGE_INSTALL += " \
    containerd       \
    cni-plugins      \
    nerdctl          \
"

# Kernel features required
# Verify via: bitbake linux-yocto -c kernel_configcheck
# CONFIG_NAMESPACES=y
# CONFIG_NET_NS=y
# CONFIG_PID_NS=y
# CONFIG_IPC_NS=y
# CONFIG_UTS_NS=y
# CONFIG_CGROUPS=y
# CONFIG_CGROUP_CPUACCT=y
# CONFIG_CGROUP_DEVICE=y
# CONFIG_CGROUP_FREEZER=y
# CONFIG_CGROUP_NET_CLASSID=y
# CONFIG_CGROUP_PERF=y
# CONFIG_OVERLAY_FS=y
```

**Docker (full):**
```bitbake
IMAGE_INSTALL += "docker-ce docker-ce-cli containerd-io"
# Requires meta-virtualization layer:
# https://git.yoctoproject.org/meta-virtualization
```

```bitbake
# Required kernel config fragment
SRC_URI += "file://container-support.cfg"
```

```
# container-support.cfg
CONFIG_NAMESPACES=y
CONFIG_NET_NS=y
CONFIG_CGROUPS=y
CONFIG_CGROUP_V2=y
CONFIG_OVERLAY_FS=y
CONFIG_VETH=y
CONFIG_BRIDGE=y
CONFIG_IP_NF_IPTABLES=y
```

---

## 9. Security & Compliance

---

### Q156. How do you enable and configure security hardening flags in Yocto?

**Answer:**

```bitbake
# In distro.conf — enable security feature set
DISTRO_FEATURES:append = " security"

# Stack Smashing Protection
TARGET_CFLAGS:append  = " -fstack-protector-strong"
TARGET_CXXFLAGS:append = " -fstack-protector-strong"

# Heap buffer overflow detection (requires -O1+)
TARGET_CPPFLAGS:append = " -D_FORTIFY_SOURCE=2"

# Position Independent Executables
TARGET_CFLAGS:append  = " -fPIE -pie"
TARGET_LDFLAGS:append = " -pie"

# RELRO (Read-Only Relocations) — full RELRO
TARGET_LDFLAGS:append = " -Wl,-z,relro,-z,now"

# Control Flow Integrity (x86_64/AArch64 with modern GCC)
TARGET_CFLAGS:append  = " -fcf-protection=full"        # x86 IBT+SHSTK
TARGET_CFLAGS:append  = " -mbranch-protection=standard" # ARM64 BTI+PAC

# Disable executable stack
TARGET_LDFLAGS:append = " -Wl,-z,noexecstack"

# Warn on format string vulnerabilities
TARGET_CFLAGS:append  = " -Wformat -Wformat-security -Werror=format-security"
```

---

### Q157. How do you implement Secure Boot in a Yocto project?

**Answer:**

```bitbake
# Enable fitImage (Flattened Image Tree)
KERNEL_IMAGETYPE      = "fitImage"
KERNEL_CLASSES:append = " kernel-fitimage"

# fitImage signing
UBOOT_SIGN_ENABLE  = "1"
UBOOT_SIGN_KEYDIR  = "${TOPDIR}/keys/uboot"
UBOOT_SIGN_KEYNAME = "dev-key"

# U-Boot verified boot
UBOOT_MKIMAGE_DTCOPTS = "-I dts -O dtb -p 2000"

# Key generation (done once, offline)
# openssl genrsa -out keys/uboot/dev-key.key 4096
# openssl req -batch -new -x509 -key keys/uboot/dev-key.key \
#   -out keys/uboot/dev-key.crt
```

**For UEFI Secure Boot:**
```bitbake
IMAGE_CLASSES += "uefi-comboapp"
UEFI_SB_KEYS_DIR = "${TOPDIR}/keys/uefi"

# Keys: PK, KEK, db (enrolled into UEFI firmware)
# Tool: sbsigntool, efitools
IMAGE_INSTALL += "sbsigntool efitools"
```

**Measured Boot (TPM integration):**
```bitbake
DISTRO_FEATURES:append = " tpm2"
IMAGE_INSTALL += "tpm2-tools tpm2-tss tpm2-abrmd"
KERNEL_FEATURES:append = " cfg/tpm.scc"
```

---

### Q158. How do you integrate CVE scanning into your Yocto build pipeline?

**Answer:**

```bitbake
# Enable CVE check globally
INHERIT += "cve-check"

# Run CVE check
bitbake core-image-minimal -c cve_check

# Output: tmp/deploy/cve/
# - core-image-minimal.cve  (image-level CVE report)
# - <package>.cve           (per-package)
```

**Configure CVE database:**
```bitbake
# CVE database update (requires network)
CVE_DB_UPDATE = "1"     # auto-update NVD DB
CVE_DB_INCR_UPDATE_AGE_THRESHOLD = "168"  # update if older than 1 week (hours)

# Custom CVE whitelist (known false positives or accepted risks)
CVE_CHECK_WHITELIST += "CVE-2023-12345"
```

**CI integration:**
```bash
bitbake core-image-minimal -c cve_check
# Check exit code: non-zero if CVEs found above threshold

# Parse report
python3 - << 'EOF'
import json, glob
for f in glob.glob('tmp/deploy/cve/*.json'):
    data = json.load(open(f))
    for issue in data.get('issues', []):
        if issue['status'] == 'Unpatched':
            print(f"CRITICAL: {issue['package']} - {issue['id']} - {issue['summary'][:80]}")
EOF
```

---

### Q159. How do you generate SPDX Software Bill of Materials (SBOM) in Yocto?

**Answer:**

```bitbake
# Enable SPDX generation (Kirkstone+)
INHERIT += "create-spdx"

# Configuration
SPDX_NAMESPACE_PREFIX    = "https://example.com/products/my-product"
SPDX_PRETTY              = "1"          # human-readable JSON
SPDX_INCLUDE_SOURCES     = "1"          # embed source tarballs (large!)
SPDX_VERIFY_PACKAGES     = "1"          # verify package hashes
SPDX_UUID_NAMESPACE      = "my-company" # consistent document UUID namespace

# Output location:
# tmp/deploy/images/<MACHINE>/<IMAGE>-<MACHINE>.spdx.json

# Validate SPDX output
pip install spdx-tools
pyspdxtools validate tmp/deploy/images/*/core-image-minimal*.spdx.json
```

**SPDX document structure includes:**
- Document metadata (creator, created timestamp, SPDX version)
- Per-package information (name, version, supplier, checksum, license)
- File-level information (path, checksum, concluded license)
- Relationships (CONTAINS, GENERATED_FROM, DESCRIBES)

**Integration with dependency track:**
```bash
# Upload to OWASP Dependency-Track
curl -X "POST" \
  "https://deptrack.example.com/api/v1/bom" \
  -H "X-Api-Key: ${DEPTRACK_API_KEY}" \
  -H "Content-Type: multipart/form-data" \
  -F "bom=@tmp/deploy/images/my-board/core-image-minimal.spdx.json" \
  -F "projectName=my-product" \
  -F "projectVersion=${DISTRO_VERSION}"
```

---

### Q160. How do you implement IMA/EVM for runtime file integrity verification?

**Answer:**

IMA (Integrity Measurement Architecture) and EVM (Extended Verification Module) provide kernel-enforced file integrity checking at runtime:

```bitbake
# Enable IMA in kernel
SRC_URI += "file://ima-evm.cfg"
```

```
# ima-evm.cfg
CONFIG_INTEGRITY=y
CONFIG_IMA=y
CONFIG_IMA_MEASURE_PCR_IDX=10
CONFIG_IMA_APPRAISE=y
CONFIG_IMA_APPRAISE_BOOTPARAM=y
CONFIG_EVM=y
CONFIG_EVM_ATTR_FSUUID=y
CONFIG_KEYS=y
CONFIG_TRUSTED_KEYS=y
CONFIG_ENCRYPTED_KEYS=y
```

```bitbake
# Install IMA tools
IMAGE_INSTALL += "ima-evm-utils keyutils"
DISTRO_FEATURES:append = " ima"

# Sign filesystem during do_rootfs
ROOTFS_POSTPROCESS_COMMAND:append = " ima_sign_rootfs; "

ima_sign_rootfs() {
    # Sign all executable files
    find ${IMAGE_ROOTFS} -type f -executable | while read f; do
        evmctl ima_sign --key ${TOPDIR}/keys/ima-priv.pem "${f}"
    done
}
```

**Boot-time IMA policy:**
```
# /etc/ima/ima-policy
measure func=BPRM_CHECK
measure func=FILE_MMAP mask=MAY_EXEC
appraise func=BPRM_CHECK appraise_type=imasig
appraise func=FILE_MMAP mask=MAY_EXEC appraise_type=imasig
```

---

### Q161. How do you configure SELinux in a Yocto image?

**Answer:**

```bitbake
# In distro.conf
DISTRO_FEATURES:append = " selinux"

# SELinux reference policy
IMAGE_INSTALL += " \
    packagegroup-core-selinux   \
    selinux-policy-targeted     \
"

# Enable in kernel
SRC_URI += "file://selinux.cfg"
```

```
# selinux.cfg
CONFIG_SECURITY_SELINUX=y
CONFIG_SECURITY_SELINUX_BOOTPARAM=y
CONFIG_SECURITY_SELINUX_BOOTPARAM_VALUE=1
CONFIG_SECURITY_SELINUX_DISABLE=y   # allow runtime disable
CONFIG_SECURITY_SELINUX_DEVELOP=y   # permissive mode support
CONFIG_DEFAULT_SECURITY_SELINUX=y
```

```bitbake
# Kernel cmdline for permissive mode (development)
APPEND += "security=selinux selinux=1 enforcing=0"

# Production
APPEND += "security=selinux selinux=1 enforcing=1"
```

**Custom policy module:**
```bash
# Generate audit-driven policy
ausearch -m avc | audit2allow -M my-policy
semodule -i my-policy.pp
```

---

### Q162. How do you set up code signing for release images?

**Answer:**

```bash
# Key generation (done once, in a Hardware Security Module ideally)
openssl genrsa -out private/signing.key 4096
openssl req -new -x509 -key private/signing.key \
            -out certs/signing.crt -days 3650 \
            -subj "/CN=My Product Signing Key"
```

```bitbake
# Image signing hook
IMAGE_POSTPROCESS_COMMAND += "sign_image; "

sign_image() {
    DEPLOY="${DEPLOY_DIR_IMAGE}"
    KEY="${TOPDIR}/private/signing.key"
    CERT="${TOPDIR}/certs/signing.crt"

    for img in ${DEPLOY}/${IMAGE_NAME}.wic; do
        # Sign the image
        openssl cms -sign -binary \
            -in "${img}" -out "${img}.cms" \
            -inkey "${KEY}" -signer "${CERT}" \
            -outform DER

        # Generate checksum
        sha256sum "${img}" > "${img}.sha256"
        openssl dgst -sha256 -sign "${KEY}" \
            -out "${img}.sha256.sig" "${img}"
    done
}
```

**For RAUC bundle signing:**
```bash
rauc bundle --cert=certs/signing.crt \
            --key=private/signing.key \
            --intermediate=certs/ca.crt \
            my-update.raucb.unsigned \
            my-update.raucb
```

---

### Q163. How do you handle license compliance for a product with GPL components?

**Answer:**

GPL compliance requires providing complete corresponding source code. Yocto automates this with the `archiver` class:

```bitbake
# In distro.conf — enable source archiving
INHERIT += "archiver"

# Archive mode options:
ARCHIVER_MODE = "original"   # original downloaded tarballs
ARCHIVER_MODE = "patched"    # tarballs with patches applied (GPL requires this)
ARCHIVER_MODE = "configured" # after configure step (for build system scripts)

# Output: tmp/deploy/sources/
```

**License manifest:**
```bash
# Generate complete license manifest for an image
bitbake core-image-minimal

# Manifests at:
# tmp/deploy/licenses///
cat tmp/deploy/licenses/core-image-minimal/*/license.manifest

# Find all GPL packages
grep -E "^LICENSE: GPL" \
  tmp/deploy/licenses/*/package.manifest | sort -u
```

**Source distribution script:**
```bash
# Package all GPL sources for customer delivery
tar -czf gpl-sources-$(date +%Y%m%d).tar.gz \
  tmp/deploy/sources/*/

# Verify completeness
for pkg in $(grep GPL tmp/deploy/licenses/core-image-minimal/*/license.manifest | \
             awk '{print $3}'); do
  ls tmp/deploy/sources/ | grep "$pkg" || echo "MISSING: $pkg"
done
```

---

### Q164. How do you harden the SSH configuration in a Yocto image?

**Answer:**

```bitbake
# meta-my-product/recipes-connectivity/openssh/openssh_%.bbappend
FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
SRC_URI += "file://sshd_config"

do_install:append() {
    install -m 0600 ${WORKDIR}/sshd_config ${D}${sysconfdir}/ssh/sshd_config
}
```

```
# files/sshd_config
Protocol 2
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
PermitEmptyPasswords no
X11Forwarding no
MaxAuthTries 3
LoginGraceTime 60
AllowUsers myapp-user ci-user
ClientAliveInterval 300
ClientAliveCountMax 2
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com
KexAlgorithms curve25519-sha256,diffie-hellman-group16-sha512
```

---

### Q165. How do you remove `debug-tweaks` settings from a production image?

**Answer:**

`debug-tweaks` is an `IMAGE_FEATURE` that applies several insecure settings suitable only for development:

**What `debug-tweaks` does:**
- Sets empty root password
- Enables passwordless SSH
- Creates `/etc/ssh/sshd_config` with permissive settings
- Enables `debug` in kernel cmdline
- Disables some security checks

**Production removal:**
```bitbake
# In your production image recipe or distro.conf
IMAGE_FEATURES:remove = "debug-tweaks"

# Also remove from EXTRA_IMAGE_FEATURES in any CI that builds production
EXTRA_IMAGE_FEATURES = ""

# Set strong root password (or lock root account)
ROOTFS_POSTPROCESS_COMMAND += "lock_root_account; "
lock_root_account() {
    # Lock root: prevents password login
    sed -i 's|^root:[^:]*:|root:!:|' ${IMAGE_ROOTFS}/etc/shadow
}
```

**CI gate:**
```bash
# Fail CI if debug-tweaks is in production image features
eval $(bitbake -e core-image-production | grep "^IMAGE_FEATURES=")
if echo "$IMAGE_FEATURES" | grep -q "debug-tweaks"; then
    echo "ERROR: debug-tweaks must not be in production image!"
    exit 1
fi
```

---

### Q166. What is `DISTRO_FEATURES security` and what does it actually enable?

**Answer:**

When `security` is in `DISTRO_FEATURES`, it acts as a trigger that recipes check to conditionally enable security-related build options. It doesn't automatically apply all hardening — recipes must individually check it.

**Recipes that respond to `DISTRO_FEATURES:security`:**
```bitbake
# In many OE-Core recipes:
PACKAGECONFIG:append = "${@bb.utils.contains('DISTRO_FEATURES', 'security', 'pam', '', d)}"

# libcap, pam, and related security infrastructure is included
# when 'security' is in DISTRO_FEATURES
```

**Additional effects (OE-Core default behaviour):**
- PAM (Pluggable Authentication Modules) enabled where applicable
- `libcap` and capability-aware applications enabled
- Some recipes enable `seccomp` filtering

**This is NOT automatically enabled by `security` feature:**
- Compiler hardening flags (must be set explicitly)
- SELinux (needs its own `selinux` feature)
- IMA/EVM (needs its own `ima` feature)
- Stack protector (must be in `TARGET_CFLAGS`)

**Complete security baseline:**
```bitbake
DISTRO_FEATURES:append = " security ima selinux"
TARGET_CFLAGS:append   = " -fstack-protector-strong -fPIE"
TARGET_LDFLAGS:append  = " -pie -Wl,-z,relro,-z,now,-z,noexecstack"
TARGET_CPPFLAGS:append = " -D_FORTIFY_SOURCE=2"
```

---

### Q167. How do you audit and lock down file permissions in the rootfs?

**Answer:**

```bitbake
# Post-process rootfs to enforce permission policy
ROOTFS_POSTPROCESS_COMMAND += "audit_permissions; "

audit_permissions() {
    RFS="${IMAGE_ROOTFS}"

    # Remove setuid bits from unnecessary binaries
    find ${RFS} -perm /4000 -not -path "*/sudo" \
        -not -path "*/su" -exec chmod u-s {} \;

    # Remove world-writable files
    find ${RFS} -perm /002 -type f -exec chmod o-w {} \;

    # Secure sensitive config files
    for f in etc/shadow etc/gshadow etc/sudoers; do
        [ -f "${RFS}/${f}" ] && chmod 0640 "${RFS}/${f}"
    done

    # Remove unnecessary SUID/SGID from executables
    for dangerous in ping traceroute mount umount; do
        f=$(find ${RFS}/usr /usr -name "$dangerous" 2>/dev/null | head -1)
        [ -n "$f" ] && chmod a-s "$f" || true
    done
}
```

**Package-level permission control:**
```bitbake
# In a recipe, use 'install' with explicit modes
do_install() {
    install -d -m 0755 ${D}${bindir}
    install -m 0755 ${B}/myapp ${D}${bindir}/myapp

    install -d -m 0750 ${D}${sysconfdir}/myapp   # group-readable only
    install -m 0640 ${S}/myapp.conf ${D}${sysconfdir}/myapp/
}
```

---

### Q168. How do you configure `sudo` in a Yocto image securely?

**Answer:**

```bitbake
IMAGE_INSTALL += "sudo"

# Custom sudoers configuration
FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
```

```
# files/sudoers
# Defaults
Defaults env_reset
Defaults mail_badpass
Defaults secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Defaults logfile="/var/log/sudo.log"
Defaults log_input,log_output
Defaults requiretty
Defaults use_pty

# No root sudo
root ALL=(ALL:ALL) ALL

# Application user — only specific commands
myapp ALL=(root) NOPASSWD: /usr/bin/systemctl restart myapp.service
myapp ALL=(root) NOPASSWD: /usr/bin/journalctl -u myapp

# Operator group
%operators ALL=(root) /usr/bin/systemctl status, /bin/journalctl
```

```bitbake
do_install:append() {
    install -d ${D}${sysconfdir}/sudoers.d
    install -m 0440 ${WORKDIR}/sudoers ${D}${sysconfdir}/sudoers
    # Verify syntax (using native sudo)
    visudo -c -f ${D}${sysconfdir}/sudoers || bbfatal "sudoers syntax error"
}
```

---

### Q169. How do you implement read-only rootfs with exceptions for specific paths?

**Answer:**

```bitbake
IMAGE_FEATURES += "read-only-rootfs"

# read-only-rootfs.bbclass creates symlinks for volatile paths:
# /var/volatile → tmpfs  (for PID files, lock files)
# /etc/resolv.conf → /var/volatile/etc/resolv.conf

# Additional volatile paths via systemd-tmpfiles
IMAGE_INSTALL += "volatile-binds"
```

**Custom volatile binds:**
```
# files/my-volatile.conf (tmpfiles.d format)
d /var/lib/myapp 0755 myapp myapp -
d /run/myapp     0755 myapp myapp -
L /etc/myapp/dynamic - - - - /data/myapp/dynamic.conf
```

**overlayfs for /home (user data):**
```ini
# home.mount
[Unit]
Description=Home overlay
DefaultDependencies=no
Before=local-fs.target

[Mount]
What=overlay
Where=/home
Type=overlay
Options=lowerdir=/home,upperdir=/data/home-upper,workdir=/data/home-work

[Install]
WantedBy=local-fs.target
```

---

### Q170. How do you handle kernel module signing in Yocto?

**Answer:**

Kernel module signing prevents unsigned modules from being loaded (with `CONFIG_MODULE_SIG_FORCE=y`):

```
# kernel-module-sign.cfg
CONFIG_MODULE_SIG=y
CONFIG_MODULE_SIG_FORCE=y
CONFIG_MODULE_SIG_ALL=y        # sign all modules during build
CONFIG_MODULE_SIG_SHA256=y
CONFIG_MODULE_SIG_KEY="certs/signing_key.pem"
CONFIG_SYSTEM_TRUSTED_KEYRING=y
```

```bitbake
# Generate signing key during kernel build
# The kernel build system automatically signs modules with CONFIG_MODULE_SIG_ALL=y
# Key is generated at:
# tmp/work/*/linux-yocto/*/build/certs/signing_key.pem

# For external modules — sign in recipe
do_install:append() {
    # Sign external module with kernel's key
    MODULE="${D}${nonarch_base_libdir}/modules/${KERNEL_VERSION}/extra/my-module.ko"
    KEYDIR="$(find ${STAGING_KERNEL_BUILDDIR} -name signing_key.pem | head -1 | xargs dirname)"
    ${KERNEL_SRC}/scripts/sign-file sha256 \
        ${KEYDIR}/signing_key.pem \
        ${KEYDIR}/signing_key.x509 \
        ${MODULE}
}
```

---

### Q171. How do you handle network security in a Yocto embedded system?

**Answer:**

**Firewall (`nftables` — modern, recommended):**
```bitbake
IMAGE_INSTALL += "nftables"

# Custom nftables ruleset
do_install:append() {
    install -d ${D}${sysconfdir}/nftables.d
    install -m 0640 ${WORKDIR}/my-rules.nft \
                    ${D}${sysconfdir}/nftables.d/
}
```

```
# files/my-rules.nft
#!/usr/sbin/nft -f
flush ruleset

table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;
        iif "lo" accept
        ct state established,related accept
        tcp dport 22 accept comment "SSH"
        tcp dport 443 accept comment "HTTPS"
        drop
    }

    chain forward { type filter hook forward priority 0; policy drop; }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}
```

**Disable unused network services:**
```bitbake
# Mask unnecessary services
ROOTFS_POSTPROCESS_COMMAND += "disable_network_services; "

disable_network_services() {
    for svc in avahi-daemon cups bluetooth; do
        if [ -f "${IMAGE_ROOTFS}${systemd_unitdir}/system/${svc}.service" ]; then
            ln -sf /dev/null \
              "${IMAGE_ROOTFS}${systemd_unitdir}/system/${svc}.service"
        fi
    done
}
```

---

### Q172. What is `BB_GENERATE_MIRROR_TARBALLS` and why does it matter for supply chain security?

**Answer:**

From a supply chain security perspective:
```bitbake
BB_GENERATE_MIRROR_TARBALLS = "1"
```

**Security benefits:**
1. **Source verification:** tarball in `DL_DIR` is checksummed on creation; future builds verify against stored checksum — detects upstream tampering.
2. **Air-gapped reproducibility:** the exact source used to produce a released binary is preserved, enabling independent verification.
3. **Audit trail:** git history included in tarball proves provenance.
4. **CI isolation:** `BB_FETCH_PREMIRRORONLY = "1"` ensures no unexpected network access from CI.

**Combined with SPDX and archiver:**
```bitbake
INHERIT += "create-spdx archiver"
ARCHIVER_MODE = "patched"
BB_GENERATE_MIRROR_TARBALLS = "1"

# This gives you:
# 1. SPDX with package checksums (what was built)
# 2. Source tarballs (what the source was)
# 3. Applied-patch tarballs (what was actually compiled)
# → Full supply chain traceability
```

---

### Q173. How do you prevent package manager access to the internet on the target device?

**Answer:**

```bitbake
# Use a private package feed (internal network only)
PACKAGE_FEED_URIS = "https://pkg.internal.example.com/feeds"

# On device: opkg/apt configured to only talk to internal server
# No public package registries reachable
```

**Air-gap network configuration (`nftables`):**
```
# Block all outbound except to internal package server
chain output {
    type filter hook output priority 0; policy drop;
    iif "lo" accept
    ip daddr 10.0.0.0/8 accept     # internal network
    ip daddr 192.168.0.0/16 accept # local network
    drop                           # block all other outbound
}
```

**For read-only rootfs + no package manager:**
```bitbake
# Don't ship opkg/rpm/dpkg on the device at all
IMAGE_FEATURES:remove = "package-management"
PACKAGE_INSTALL:remove = "opkg"

# Updates only via OTA (RAUC/SWUpdate) — no ad-hoc installs possible
```

---

### Q174. How do you configure `seccomp` filtering for applications in Yocto?

**Answer:**

seccomp (Secure Computing Mode) restricts which system calls a process can make:

```bitbake
# Enable seccomp in kernel
SRC_URI += "file://seccomp.cfg"
```

```
# seccomp.cfg
CONFIG_SECCOMP=y
CONFIG_SECCOMP_FILTER=y
```

```bitbake
# Install libseccomp for applications that use it
IMAGE_INSTALL += "libseccomp"
DEPENDS += "libseccomp"
```

**Application-level seccomp (in C):**
```c
#include 
scmp_filter_ctx ctx = seccomp_init(SCMP_ACT_KILL);
seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(read), 0);
seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(write), 0);
seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(exit_group), 0);
seccomp_load(ctx);
```

**systemd seccomp:**
```ini
[Service]
SystemCallFilter=@basic-io @io-event @ipc @process @network-io
SystemCallErrorNumber=EPERM
SystemCallArchitectures=native
```

---

### Q175. How do you implement `dm-verity` for rootfs integrity verification?

**Answer:**

`dm-verity` provides transparent integrity verification of block devices at the kernel level:

```bitbake
# Kernel config
SRC_URI += "file://dm-verity.cfg"
```

```
# dm-verity.cfg
CONFIG_MD=y
CONFIG_BLK_DEV_DM=y
CONFIG_DM_VERITY=y
CONFIG_DM_VERITY_VERIFY_ROOTHASH_SIG=y
```

```bitbake
# Image post-processing: apply dm-verity to squashfs
IMAGE_POSTPROCESS_COMMAND += "apply_dmverity; "
IMAGE_FSTYPES = "squashfs"

apply_dmverity() {
    IMG="${DEPLOY_DIR_IMAGE}/${IMAGE_NAME}.squashfs"
    HASH_IMG="${IMG}.verity"

    # Generate hash tree and root hash
    veritysetup format ${IMG} ${HASH_IMG} | \
        tee ${IMG}.verity-params

    ROOT_HASH=$(grep "Root hash:" ${IMG}.verity-params | awk '{print $3}')

    # Sign root hash
    echo "${ROOT_HASH}" | openssl dgst -sha256 -sign ${TOPDIR}/keys/sign.key \
        -out ${IMG}.roothash.sig

    echo "dm-verity root hash: ${ROOT_HASH}"
}
```

**Kernel cmdline:**
```
APPEND += "rootflags=ro rootfstype=ext4 \
  dm-mod.create=\"vroot,,0,ro,0 <sectors> verity 1 /dev/sda2 /dev/sda3 \
  4096 4096 <data-blocks> 1 sha256 <root-hash> <salt>\""
```

---

## 10. Advanced Use Cases

---

### Q176. How do you implement multi-config builds for multiple target boards?

**Answer:**

Multi-config builds allow building images for multiple machines in a single `bitbake` invocation:

```bitbake
# local.conf
BBMULTICONFIG = "board-a board-b board-c"
```

```bitbake
# conf/multiconfig/board-a.conf
MACHINE = "board-a"
DISTRO  = "my-distro"
TMPDIR  = "${TOPDIR}/tmp-board-a"  # separate TMPDIR per config
```

```bitbake
# conf/multiconfig/board-b.conf
MACHINE = "board-b"
DISTRO  = "my-distro-minimal"
TMPDIR  = "${TOPDIR}/tmp-board-b"
```

**Build command:**
```bash
# Build different images for each board in parallel
bitbake mc:board-a:core-image-full-cmdline \
        mc:board-b:core-image-minimal \
        mc:board-c:core-image-minimal

# Build the same image for all boards
bitbake mc:board-a:core-image-minimal \
        mc:board-b:core-image-minimal
```

**Inter-config dependencies:**
```bitbake
# board-a image depends on a board-b component being built first
do_image_wic[mcdepends] = "mc::board-b:special-firmware:do_deploy"
```

**KAS multi-config:**
```yaml
# kas/multi-board.yml
target:
  - "mc:board-a:core-image-minimal"
  - "mc:board-b:core-image-minimal"
```

---

### Q177. How do you generate and customise an SDK (eSDK)?

**Answer:**

```bash
# Standard SDK
bitbake core-image-minimal -c populate_sdk
# Output: tmp/deploy/sdk/*.sh

# Extensible SDK
bitbake core-image-minimal -c populate_sdk_ext
# Output: tmp/deploy/sdk/*.sh (with devtool)
```

```bitbake
# Customise SDK contents
# Add extra target libraries to SDK sysroot
TOOLCHAIN_TARGET_TASK:append = " \
    libssl-dev          \
    libcurl-dev         \
    protobuf-dev        \
    my-custom-lib-dev   \
"

# Add extra native tools to SDK host environment
TOOLCHAIN_HOST_TASK:append = " \
    nativesdk-cmake     \
    nativesdk-ninja     \
    nativesdk-python3   \
    nativesdk-protobuf  \
"

# SDK name and version
SDK_NAME = "${DISTRO}-${TCLIBC}-${SDKMACHINE}-${IMAGE_BASENAME}-${TUNE_PKGARCH}"
SDK_VERSION = "${DISTRO_VERSION}"

# eSDK configuration
SDK_EXT_TYPE = "full"              # "minimal" downloads tools on demand
SDK_INCLUDE_BUILDTOOLS = "1"       # include cmake, ninja, etc.
SDK_INCLUDE_PKGDATA = "1"          # include package database (for devtool)
```

**CMake toolchain file (auto-generated in SDK):**
```cmake
# $OECORE_NATIVE_SYSROOT/usr/share/cmake/OEToolchainConfig.cmake
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)
set(CMAKE_SYSROOT $ENV{OECORE_TARGET_SYSROOT})
set(CMAKE_C_COMPILER $ENV{CC})
set(CMAKE_CXX_COMPILER $ENV{CXX})
```

---

### Q178. How do you implement a custom image class in Yocto?

**Answer:**

```bitbake
# meta-my-product/classes/my-production-image.bbclass

# Enforce production image policies
python __anonymous() {
    # Verify debug-tweaks is NOT in IMAGE_FEATURES
    features = (d.getVar('IMAGE_FEATURES') or '').split()
    if 'debug-tweaks' in features:
        bb.fatal("Production image must not include debug-tweaks!")

    # Verify read-only-rootfs IS in IMAGE_FEATURES
    if 'read-only-rootfs' not in features:
        bb.warn("Production image should use read-only-rootfs")
}

# Mandatory base packages
IMAGE_INSTALL:append = " \
    ca-certificates     \
    nftables            \
"

# Production-specific post-processing
ROOTFS_POSTPROCESS_COMMAND += " \
    production_lock_root;       \
    production_audit_perms;     \
    production_verify_licenses; \
"

production_lock_root() {
    # Lock root account
    sed -i 's|^root:[^:]*:|root:*:|' ${IMAGE_ROOTFS}/etc/shadow
    # Remove root's .ssh if present
    rm -rf ${IMAGE_ROOTFS}/root/.ssh
}

production_audit_perms() {
    # Check for world-writable files
    found=$(find ${IMAGE_ROOTFS} -perm /002 -type f 2>/dev/null | wc -l)
    if [ "$found" -gt 0 ]; then
        bb.warn("${found} world-writable files found in production image")
        find ${IMAGE_ROOTFS} -perm /002 -type f | head -10
    fi
}

production_verify_licenses() {
    # Check no packages with unaccepted commercial licenses
    if grep -r "commercial" ${IMAGE_ROOTFS}/usr/share/licenses/ 2>/dev/null; then
        bb.warn("Commercial-licensed packages found — verify LICENSE_FLAGS_ACCEPTED")
    fi
}
```

---

### Q179. How do you use `devtool` effectively for rapid development?

**Answer:**

`devtool` is the eSDK's primary development tool for modifying recipes and testing changes:

```bash
# Add a new recipe from a local directory
devtool add my-new-app /path/to/my-new-app/source

# Add from git URL
devtool add my-new-app https://github.com/example/my-new-app.git

# Modify an existing recipe (checks out source for editing)
devtool modify my-existing-recipe

# Build the workspace recipe
devtool build my-new-app

# Deploy directly to a running target
devtool deploy-target my-new-app root@192.168.1.100

# Remove from target
devtool undeploy-target my-new-app root@192.168.1.100

# Once happy, commit changes back to your layer
devtool finish my-new-app ../meta-my-product/recipes-app/my-new-app/

# Upgrade a recipe to a newer upstream version
devtool upgrade my-existing-recipe --version 2.0.0

# Check workspace status
devtool status

# Reset (abandon changes)
devtool reset my-new-app
```

**Workflow for fast iteration:**
```bash
# 1. Modify source
vim /path/to/workspace/sources/my-app/src/main.c

# 2. Build only changed files
devtool build my-app

# 3. Deploy to target
devtool deploy-target my-app root@192.168.1.100

# 4. Test on target
ssh root@192.168.1.100 my-app --self-test

# 5. Repeat 1-4 until satisfied

# 6. Generate patches from your changes
cd /path/to/workspace/sources/my-app
git format-patch origin/main

# 7. Finish (writes patches and recipe to layer)
devtool finish my-app ../meta-my-product
```

---

### Q180. How do you implement a custom fetcher in BitBake?

**Answer:**

```python
# meta-my-layer/lib/bb/fetch2/s3fetch.py
"""Custom S3 fetcher for internal artefact storage."""

import os
import bb
from bb.fetch2 import FetchMethod, FetchError, runfetchcmd

class S3Fetch(FetchMethod):
    """Fetch from AWS S3 using AWS CLI."""

    def supports(self, ud, d):
        return ud.type == 's3'

    def urldata_init(self, ud, d):
        ud.localpath = os.path.join(
            d.getVar('DL_DIR'),
            os.path.basename(ud.path)
        )

    def localpath(self, ud, d):
        return ud.localpath

    def need_update(self, ud, d):
        return not os.path.exists(ud.localpath)

    def download(self, ud, d):
        # s3://my-bucket/path/to/file.tar.gz
        s3_url = f"s3://{ud.host}{ud.path}"
        cmd = f"aws s3 cp {s3_url} {ud.localpath}"

        try:
            runfetchcmd(cmd, d)
        except Exception as e:
            raise FetchError(f"S3 fetch failed: {e}", s3_url)

    def checkstatus(self, fetch, ud, d):
        s3_url = f"s3://{ud.host}{ud.path}"
        try:
            runfetchcmd(f"aws s3 ls {s3_url}", d)
        except Exception:
            raise FetchError(f"S3 object not found: {s3_url}", s3_url)
```

**Plugin registration:**
```python
# meta-my-layer/lib/bb/fetch2/__init__.py patch
# Or via bitbake plugin mechanism (BBPATH-based discovery)
```

**Usage in recipe:**
```bitbake
SRC_URI = "s3://my-internal-bucket/firmware/my-firmware-${PV}.tar.gz"
SRC_URI[sha256sum] = "..."
```

---

### Q181. How do you implement conditional builds based on external factors?

**Answer:**

```bitbake
# Build variant controlled by environment variable
python () {
    build_type = os.environ.get('MY_BUILD_TYPE', 'release')
    d.setVar('MY_BUILD_TYPE', build_type)

    if build_type == 'debug':
        d.appendVar('IMAGE_FEATURES', ' debug-tweaks tools-debug')
        d.appendVar('IMAGE_INSTALL', ' gdb strace')
        d.setVar('EXTRA_OECMAKE', '-DCMAKE_BUILD_TYPE=Debug')
    elif build_type == 'release':
        d.setVar('EXTRA_OECMAKE', '-DCMAKE_BUILD_TYPE=Release')
    else:
        bb.fatal(f"Unknown MY_BUILD_TYPE: {build_type}")
}
```

```bash
MY_BUILD_TYPE=debug bitbake core-image-minimal
MY_BUILD_TYPE=release bitbake core-image-production
```

**Feature flags via JSON config:**
```bitbake
python () {
    import json, os
    cfg_file = d.getVar('PRODUCT_CONFIG_FILE')
    if not cfg_file or not os.path.exists(cfg_file):
        return

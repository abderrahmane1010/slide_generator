# Yocto — Zero to Hero
### A Manual of First Principles

> *Built from the ground up. Every concept earns its place. Every diagram exists because words alone would be longer.*

---

## Preface
This manual is a shortcut. It exists because the official documentation is exhaustive but not pedagogical, and most tutorials teach commands before concepts. Here we invert the order: concepts first, commands second, and only the concepts that actually matter.

You will be Yocto-literate by the end of Part IV, productive by the end of Part V, and able to maintain a product by the end of Part VI. Read in order.

---

## Table of Contents

**Part I — Orientation**
1. [What Yocto Builds](#1-what-yocto-builds)
2. [The Duality: Engine and Metadata](#2-the-duality-engine-and-metadata)
3. [A Brief History](#3-a-brief-history)

**Part II — The Six Kinds of Files**
4. [The Taxonomy](#4-the-taxonomy-of-metadata)
5. [Recipes (`.bb`)](#5-recipes-bb)
6. [The Two Species of Recipe](#6-the-two-species-of-recipe)
7. [Appends (`.bbappend`)](#7-appends-bbappend)
8. [Classes (`.bbclass`)](#8-classes-bbclass)
9. [Includes and Patches (`.inc`, `.patch`)](#9-includes-and-patches)

**Part III — The Configuration Universe**
10. [The Six Doors](#10-the-six-doors)
11. [The Variable Namespace](#11-the-variable-namespace)
12. [BUILD, HOST, TARGET](#12-build-host-target)
13. [MACHINE and DISTRO — the Two Knobs](#13-machine-and-distro--the-two-knobs)

**Part IV — How a Build Actually Happens**
14. [The Universal Task Graph](#14-the-universal-task-graph)
15. [Parse, then Execute](#15-parse-then-execute)
16. [From Source to Image](#16-from-source-to-image)

**Part V — Layers and Composition**
17. [The Anatomy of a Layer](#17-the-anatomy-of-a-layer)
18. [OE-Core, BSP Layers, Distro Layers, Product Layers](#18-the-four-kinds-of-layers)
19. [BSP Layers in Detail](#19-bsp-layers-in-detail)

**Part VI — Production**
20. [The LTS Contract](#20-the-lts-contract)
21. [Yocto ≠ Poky](#21-yocto--poky)

**Part VII — The Learning Path**
22. [How to Actually Learn Yocto](#22-how-to-actually-learn-yocto)

**Appendices**
- [A — Variables to Memorize](#appendix-a--variables-to-memorize)
- [B — Task Map](#appendix-b--task-map)
- [C — Glossary](#appendix-c--glossary)

---

# Part I — Orientation

## 1. What Yocto Builds

Yocto is a build system. Its output is a bootable Linux image for one specific piece of hardware.

Every embedded Linux device looks roughly like this:

```
┌──────────────────────────────────────────────────┐
│                  TARGET DEVICE                   │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌────────────────────┐  ┌────────────────────┐  │
│  │   BOOT PARTITION   │  │   ROOTFS PARTITION │  │
│  │                    │  │                    │  │
│  │  • Bootloader      │  │  • /bin /sbin      │  │
│  │    (U-Boot, GRUB)  │  │  • /lib            │  │
│  │  • Kernel (zImage, │  │  • /etc            │  │
│  │    Image, uImage)  │  │  • /usr            │  │
│  │  • Device Tree     │  │  • /home /opt …    │  │
│  │    (.dtb)          │  │                    │  │
│  └────────────────────┘  └────────────────────┘  │
│                                                  │
└──────────────────────────────────────────────────┘
```

The job of a Yocto build is to produce these partitions for a hardware target you specify. Nothing more.

> **Principle 1.** *Yocto does not run Linux. Yocto builds Linux for a specific device.*

What we mean by *specific device* is concrete: a Raspberry Pi 4, a BeagleBone Black, an i.MX 8 evaluation board, a custom STM32MP1 board your company designed. Each is a separate `MACHINE` (see Chapter 13).

---

## 2. The Duality: Engine and Metadata

There are exactly two things in Yocto. Learning to see them as separate is the entire first lesson.

```
                       YOCTO
                         │
              ┌──────────┴──────────┐
              │                     │
        ┌───────────┐         ┌────────────┐
        │  BitBake  │         │  Metadata  │
        │  (engine) │         │ (recipes)  │
        └───────────┘         └────────────┘

         the chef                the recipes
```

**BitBake** is an interpreter, written in Python, born inside OpenEmbedded in 2004. It does not know what Linux is. It does not know what a kernel is. It does not know what a package is. It knows three things and three things only:

1. How to parse metadata files.
2. How to resolve dependencies between tasks.
3. How to execute tasks (Python functions or shell scripts).

**Metadata** is the body of declarative files that gives BitBake its knowledge. The metadata says: "to build OpenSSL, fetch this tarball, apply these patches, run `./configure`, then `make`, then `make install`." BitBake reads that and obeys.

> **Principle 2.** *The engine is generic. The knowledge lives in the recipes. If you understand this separation, every confusing part of Yocto becomes clear.*

This separation is what makes Yocto extensible: the engine never changes, but the recipes can describe anything that compiles.

---

## 3. A Brief History

| Year   | Event                                                                                       |
|--------|---------------------------------------------------------------------------------------------|
| 2003   | OpenEmbedded project founded.                                                               |
| 2004   | BitBake created inside OpenEmbedded as a Python build engine.                               |
| ~2010  | OpenEmbedded splits its codebase: `bitbake` (engine) and `openembedded-core` (metadata).    |
| ~2010  | The **Poky** reference distribution is assembled from BitBake + OE-Core + tooling.          |
| 2010   | Discussions between OpenEmbedded and the Linux Foundation about standardization.            |
| 2011   | The **Yocto Project** is announced as the governance and commercial umbrella.               |

The historical lesson:

- *OpenEmbedded* is older than Yocto and remains its technical heart.
- *Poky* is one distribution, not the project itself.
- *Yocto Project* is the umbrella name, including governance, release cadence, and LTS commitments.

> **Principle 3.** *Yocto stands on OpenEmbedded. Always.*

---

# Part II — The Six Kinds of Files

## 4. The Taxonomy of Metadata

All Yocto metadata is one of exactly six file types:

```
                          METADATA
                              │
   ┌──────────┬───────────┬───┴────┬───────────┬──────────┐
   │          │           │        │           │          │
  .bb     .bbappend     .conf   .bbclass     .inc       .patch
recipe   modification  config    class      include     patch
         to a recipe                       fragment    for source
```

| Extension   | Name              | One-line role                                       |
|-------------|-------------------|-----------------------------------------------------|
| `.bb`       | Recipe            | Build instructions for one thing.                   |
| `.bbappend` | Recipe append     | Modify an existing recipe without owning it.        |
| `.conf`     | Configuration     | Declare variables. No tasks, no logic.              |
| `.bbclass`  | Class             | Reusable logic, inherited by recipes.               |
| `.inc`      | Include           | A shared fragment, included by other files.         |
| `.patch`    | Patch             | A diff applied to source code by `do_patch`.        |

> **Principle 4.** *Every file in a Yocto tree is one of these six. If you cannot classify a file, you do not yet understand it.*

---

## 5. Recipes (`.bb`)

A recipe is a declarative file describing **how to build one thing**. The file name encodes the package name and version:

```
openssl_3.0.8.bb       ← package "openssl", version "3.0.8"
busybox_1.36.1.bb      ← package "busybox", version "1.36.1"
```

A minimal recipe looks like this:

```python
SUMMARY = "A small example package"
DESCRIPTION = "Demonstrates the minimum recipe shape"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://COPYING;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = "https://example.org/hello-${PV}.tar.gz"
SRC_URI[sha256sum] = "abc123…"

S = "${WORKDIR}/hello-${PV}"

inherit autotools
```

What each part says:

- `SUMMARY`, `DESCRIPTION` — human-readable metadata.
- `LICENSE`, `LIC_FILES_CHKSUM` — legal metadata; Yocto refuses to build a recipe without a license.
- `SRC_URI` — where to fetch the source. Used by `do_fetch`.
- `SRC_URI[sha256sum]` — integrity check.
- `S` — the source directory after unpacking. (More on `S` in Chapter 11.)
- `inherit autotools` — pulls in `autotools.bbclass`, which provides standard `do_configure`/`do_compile`/`do_install` for autotools projects.

That is a recipe. Six declarative lines and an `inherit` directive describe a complete build.

---

## 6. The Two Species of Recipe

Recipes come in two kinds, and the distinction is sharper than newcomers realize.

```
                        RECIPES
                           │
              ┌────────────┴────────────┐
              │                         │
     ┌────────────────┐        ┌────────────────┐
     │ Package Recipe │        │  Image Recipe  │
     │                │        │                │
     │ Builds one     │        │ Builds nothing │
     │ artifact       │        │ itself. Lists  │
     │ (.deb/.rpm/    │        │ packages.      │
     │  .ipk)         │        │                │
     └────────────────┘        └────────────────┘
```

### Package recipes

Produce a single binary package: `openssl`, `busybox`, `nginx`. The output is a `.deb`, `.rpm`, or `.ipk` file in the build tree. Most recipes you will ever see are package recipes.

### Image recipes

Produce a **rootfs**. An image recipe builds nothing itself — it declares a set of packages, and BitBake assembles the rootfs as the closure of that set under dependency.

The list is declared via `IMAGE_INSTALL`:

```python
SUMMARY = "A minimal image with SSH"
LICENSE = "MIT"

inherit core-image

IMAGE_INSTALL += " \
    openssh \
    nano \
    htop \
    "

IMAGE_FEATURES += "ssh-server-openssh"
```

`IMAGE_INSTALL` is the user-level handle. Internally BitBake derives `PACKAGE_INSTALL` from it, which is the actual list given to the rootfs assembly step.

> **Principle 5.** *A package is a leaf. An image is a list. There is no third thing.*

---

## 7. Appends (`.bbappend`)

The append (`.bbappend`) is the mechanism for **modifying a recipe you do not own**.

Suppose the file `openssl_3.0.8.bb` lives in OE-Core. You cannot edit it — it's upstream. But you need to apply an extra patch. You create:

```
your-layer/recipes-openssl/openssl/openssl_%.bbappend
```

containing:

```python
FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
SRC_URI += "file://my-cve-fix.patch"
```

The `_%` wildcard means "any version". When BitBake parses `openssl_3.0.8.bb`, it also parses any `openssl_*.bbappend` it finds in any layer, and merges them.

> **Principle 6.** *Never edit a recipe you do not own. Append it.*

This is the cardinal rule of Yocto layer hygiene. Editing upstream recipes destroys upgradability.

---

## 8. Classes (`.bbclass`)

A class is reusable logic, factored out of recipes. Recipes acquire class behavior by inheriting:

```python
inherit cmake
```

This single line gives the recipe complete `do_configure`/`do_compile`/`do_install` implementations for a CMake project. Without it, the recipe would have to spell out 30+ lines of build logic.

Classes are partitioned into two kinds:

```
                         CLASSES
                            │
              ┌─────────────┴─────────────┐
              │                           │
    ┌──────────────────┐         ┌──────────────────┐
    │  Global classes  │         │  Recipe classes  │
    │                  │         │                  │
    │  Inherited by    │         │  Inherited       │
    │  EVERY recipe    │         │  explicitly when │
    │  automatically   │         │  needed          │
    │                  │         │                  │
    │  e.g. base       │         │  e.g. cmake,     │
    │       package    │         │  autotools,      │
    │       staging    │         │  systemd,        │
    │                  │         │  useradd, …      │
    └──────────────────┘         └──────────────────┘
```

### Global classes

The most important is `base.bbclass`. **Every recipe inherits it, transitively, without ever writing `inherit base`.** It defines the canonical task graph (`do_fetch`, `do_unpack`, `do_patch`, …). See Chapter 14.

### Recipe classes

Inherited by intent: `cmake`, `autotools`, `meson`, `systemd`, `useradd`, `pkgconfig`. Each captures a build-system pattern.

> **Principle 7.** *Classes exist to eliminate duplication. If you write the same logic in two recipes, promote it to a class.*

---

## 9. Includes and Patches

### Includes (`.inc`)

A `.inc` file is a fragment included by another metadata file. It carries no semantics of its own; it is purely a textual reuse mechanism. Useful for sharing common variables among related recipes:

```python
# recipes-myproject/myproject/myproject.inc
HOMEPAGE = "https://myproject.example/"
LICENSE = "Apache-2.0"
SRC_URI = "git://git.example.com/myproject.git;branch=main"
```

```python
# recipes-myproject/myproject/myproject-server_1.0.bb
require myproject.inc
# … server-specific bits
```

```python
# recipes-myproject/myproject/myproject-client_1.0.bb
require myproject.inc
# … client-specific bits
```

`require` is mandatory (errors if missing); `include` is optional (silent if missing).

### Patches (`.patch`)

A `.patch` is a unified-diff file, listed in `SRC_URI`. The `do_patch` task applies it to the unpacked source in `S`.

```python
SRC_URI += " \
    file://0001-fix-segfault.patch \
    file://0002-add-arm64-support.patch \
    "
```

Patches live in a directory next to the recipe and are found via `FILESEXTRAPATHS`.

> **Principle 8.** *Includes factor metadata. Patches factor source modifications. Both exist to keep the recipe tree DRY.*

---

# Part III — The Configuration Universe

## 10. The Six Doors

BitBake's entire variable namespace is built by reading six configuration files. Memorize them.

```
                       bitbake.conf
                      (ENTRY POINT)
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        │      includes     │                   │
        ▼                   ▼                   ▼
   local.conf         machine.conf         distro.conf
   (user)             (hardware)           (policy)
        │                   │                   │
   sets:              included as:        included as:
   MACHINE,           conf/machine/       conf/distro/
   DISTRO             ${MACHINE}.conf     ${DISTRO}.conf

                            │
                            ▼
                     bblayers.conf
                  (lists active layers)
                            │
                            ▼
                       layer.conf
                  (one per active layer)
```

| # | File              | Location                        | Role                                                                                              |
|---|-------------------|---------------------------------|---------------------------------------------------------------------------------------------------|
| 1 | `bitbake.conf`    | `meta/conf/`                    | **Entry point.** Declares the foundational variables.                                              |
| 2 | `bblayers.conf`   | `build/conf/`                   | Lists active layers (`BBLAYERS`).                                                                  |
| 3 | `layer.conf`      | `<layer>/conf/`                 | One per layer. Declares the layer's name, priority, and recipe globs.                              |
| 4 | `local.conf`      | `build/conf/`                   | User-side configuration. **Carries `MACHINE` and `DISTRO`.** Included by `bitbake.conf`.           |
| 5 | `machine.conf`    | `<bsp-layer>/conf/machine/`     | Hardware truth. Included by `bitbake.conf` via `conf/machine/${MACHINE}.conf`.                     |
| 6 | `distro.conf`     | `<distro-layer>/conf/distro/`   | Policy truth. Included by `bitbake.conf` via `conf/distro/${DISTRO}.conf`.                         |

> **Principle 9.** *The whole build is a function of two variables: `MACHINE` and `DISTRO`. The six configuration files conspire to make this so.*

### What each file actually contains

`local.conf` — the user's switches:

```python
MACHINE ?= "raspberrypi4-64"
DISTRO ?= "poky"
PACKAGE_CLASSES ?= "package_deb"
BB_NUMBER_THREADS ?= "8"
PARALLEL_MAKE ?= "-j 8"
```

`bblayers.conf` — the layer roster:

```python
BBLAYERS ?= " \
  ${TOPDIR}/../meta \
  ${TOPDIR}/../meta-poky \
  ${TOPDIR}/../meta-raspberrypi \
  ${TOPDIR}/../meta-myproduct \
  "
```

`layer.conf` (one per layer) — the layer's manifest:

```python
BBPATH .= ":${LAYERDIR}"
BBFILES += "${LAYERDIR}/recipes-*/*/*.bb \
            ${LAYERDIR}/recipes-*/*/*.bbappend"
BBFILE_COLLECTIONS += "myproduct"
BBFILE_PATTERN_myproduct = "^${LAYERDIR}/"
BBFILE_PRIORITY_myproduct = "10"
LAYERDEPENDS_myproduct = "core"
```

---

## 11. The Variable Namespace

`bitbake.conf` declares the variables every recipe assumes. The most important ones describe the per-recipe working directories:

```
WORKDIR/
├── S/                  ← unpacked source (where do_compile runs)
├── B/                  ← out-of-tree build directory
├── D/                  ← destination (where do_install puts files)
├── T/                  ← task scripts, logs, signature data
├── temp/               ← scratch
└── packages-split/     ← intermediate split for do_package
```

| Variable      | Meaning                                                                  |
|---------------|--------------------------------------------------------------------------|
| `WORKDIR`     | The recipe's working directory. Contains S, B, D, T.                     |
| `S`           | Source directory. Where the unpacked source lives.                        |
| `B`           | Build directory. Often equal to `S`, but separate for out-of-tree builds. |
| `D`           | Destination. Where `do_install` writes files (staging for packaging).     |
| `T`           | Temp directory. Task scripts, run logs, sigdata.                         |
| `PN`          | Package name (e.g. `openssl`).                                            |
| `PV`          | Package version (e.g. `3.0.8`).                                           |
| `PR`          | Package revision (e.g. `r0`).                                             |
| `TOPDIR`      | The root of the build directory.                                          |
| `TMPDIR`      | `${TOPDIR}/tmp` — where intermediate output goes.                         |
| `DEPLOY_DIR`  | `${TMPDIR}/deploy` — where final artifacts land.                          |

> **Principle 10.** *Recipes never hardcode paths. Recipes use variables. The variables are defined by `bitbake.conf`.*

---

## 12. BUILD, HOST, TARGET

Yocto cross-compiles. That means three machines are involved, and BitBake tracks them as a triplet:

```
   BUILD machine              HOST machine              TARGET machine
  ─────────────────         ─────────────────         ─────────────────
  Where we build          Where the binary runs     Where the binary
                                                    targets (for compilers)

  Your x86_64 laptop      The aarch64 board          (often = HOST)


  Typical scenario:
  ┌──────────────┐      cross-compile       ┌──────────────┐
  │  BUILD       │  ─────────────────────►  │  HOST/TARGET │
  │  x86_64 host │                          │  aarch64     │
  └──────────────┘                          └──────────────┘
```

For most builds, `HOST` and `TARGET` are the same — you build a binary that runs on the device. The distinction only matters when you build a *cross-compiler*, where:

- BUILD = x86_64 laptop
- HOST = x86_64 (the compiler itself runs there)
- TARGET = aarch64 (the compiler produces aarch64 code)

This is called a *Canadian cross*. You almost never need to think about it as a user.

> **Principle 11.** *BUILD is where you are. HOST is where it runs. TARGET is what it targets. For 99% of recipes, HOST == TARGET.*

---

## 13. MACHINE and DISTRO — the Two Knobs

The entire build is parameterized by two variables, both set in `local.conf`:

```
┌──────────────────────────────────┐  ┌──────────────────────────────────┐
│              MACHINE             │  │              DISTRO              │
├──────────────────────────────────┤  ├──────────────────────────────────┤
│  Hardware truth                  │  │  Policy truth                    │
│                                  │  │                                  │
│  • CPU architecture              │  │  • Default features              │
│  • Kernel recipe to use          │  │    (systemd vs sysvinit,         │
│  • Bootloader recipe to use      │  │     glibc vs musl, …)            │
│  • Device tree(s)                │  │  • Distro policy (CFLAGS,        │
│  • Serial console settings       │  │     license whitelist, …)        │
│  • Boot image format             │  │  • Distro version string         │
│                                  │  │                                  │
│  Provided by:  BSP LAYER         │  │  Provided by:  DISTRO LAYER      │
│  Example:  raspberrypi4-64       │  │  Example:  poky                  │
└──────────────────────────────────┘  └──────────────────────────────────┘
```

These are the only two variables that *fundamentally* change the build. Everything else is downstream.

```python
# local.conf
MACHINE = "raspberrypi4-64"   ← which device
DISTRO  = "poky"              ← which policy
```

> **Principle 12.** *Pick a MACHINE first (from a BSP layer). Pick a DISTRO second (or accept the default). The image follows.*

---

# Part IV — How a Build Actually Happens

## 14. The Universal Task Graph

Every recipe inherits `base.bbclass`, transitively. From this single fact follows the canonical task sequence:

```
                  ┌──────────────────┐
                  │   do_fetch       │  download source from upstream
                  └────────┬─────────┘
                           │
                  ┌────────▼─────────┐
                  │   do_unpack      │  unpack archive into S
                  └────────┬─────────┘
                           │
                  ┌────────▼─────────┐
                  │   do_patch       │  apply .patch files to S
                  └────────┬─────────┘
                           │
                  ┌────────▼─────────┐
                  │ do_prepare_recipe│  populate recipe sysroot
                  │      _sysroot    │
                  └────────┬─────────┘
                           │
                  ┌────────▼─────────┐
                  │   do_configure   │  ./configure | cmake | meson
                  └────────┬─────────┘
                           │
                  ┌────────▼─────────┐
                  │   do_compile     │  make | ninja
                  └────────┬─────────┘
                           │
                  ┌────────▼─────────┐
                  │   do_install     │  install to D
                  └────────┬─────────┘
                           │
                  ┌────────▼─────────┐
                  │   do_package     │  split into runtime packages
                  └────────┬─────────┘
                           │
                  ┌────────▼─────────┐
                  │ do_package_write │  emit .deb / .rpm / .ipk
                  │  _{deb,rpm,ipk}  │
                  └──────────────────┘
```

Image recipes have a parallel graph centered on `do_rootfs` and `do_image`:

```
   do_rootfs    ← assemble rootfs from PACKAGE_INSTALL
       │
       ▼
   do_image     ← generate filesystem images (ext4, wic, …)
       │
       ▼
   do_image_complete
```

> **Principle 13.** *No recipe escapes the task graph. It may extend tasks. It may inject tasks (`addtask`). It may never replace the spine.*

### Tasks are extensible

You can add or override tasks. The classic pattern:

```python
do_install:append() {
    install -d ${D}${sysconfdir}
    install -m 0644 ${WORKDIR}/myconfig ${D}${sysconfdir}/myconfig
}
```

`:append` appends to the existing task. `:prepend` runs before. `:` (alone) overrides. (In older Yocto: `_append`, `_prepend`, but `:` is the modern syntax since 3.4.)

---

## 15. Parse, then Execute

A BitBake invocation has two phases:

```
┌────────────────────────────────────────────────────────────┐
│                       PHASE 1: PARSE                       │
├────────────────────────────────────────────────────────────┤
│  1. Read bitbake.conf                                      │
│  2. Read local.conf, machine.conf, distro.conf             │
│  3. Read every layer.conf                                  │
│  4. Discover all .bb and .bbappend files via BBFILES       │
│  5. Parse every recipe → build a dependency graph          │
└────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│                      PHASE 2: EXECUTE                      │
├────────────────────────────────────────────────────────────┤
│  6. Compute the set of tasks needed for the target         │
│  7. Schedule tasks respecting dependencies                 │
│  8. Run tasks in parallel up to BB_NUMBER_THREADS          │
│  9. Cache outputs via the sstate-cache (signature-based)   │
└────────────────────────────────────────────────────────────┘
```

The **sstate-cache** (shared state cache) is the secret of fast rebuilds: every task's output is hashed and reused if the inputs (signatures) haven't changed.

> **Principle 14.** *Parsing is slow. Execution is parallelizable. Sstate makes incremental builds tolerable.*

---

## 16. From Source to Image

The full path from a recipe to a deployed image:

```
   SRC_URI (upstream URL or git ref)
        │
        │ do_fetch, do_unpack, do_patch
        ▼
   ${S}  (patched source)
        │
        │ do_configure, do_compile
        ▼
   ${B}  (compiled artifacts)
        │
        │ do_install
        ▼
   ${D}  (staged install)
        │
        │ do_package
        ▼
   per-package staging
        │
        │ do_package_write_deb/rpm/ipk
        ▼
   ${DEPLOY_DIR}/${PACKAGE_FORMAT}/<arch>/foo_1.0-r0.deb

                    ┄┄┄┄┄┄┄┄┄┄┄

   IMAGE_INSTALL → list of packages
        │
        │ do_rootfs (assembles rootfs from packages)
        ▼
   ${IMAGE_ROOTFS}  (filesystem tree)
        │
        │ do_image_<type>
        ▼
   ${DEPLOY_DIR_IMAGE}/<image>-<machine>.<ext4|wic|tar.bz2>
```

That is the entire process, from `SRC_URI` to a bootable artifact. Memorize the shape; everything else is decoration.

---

# Part V — Layers and Composition

## 17. The Anatomy of a Layer

A layer is a directory containing metadata. Its skeleton:

```
meta-mylayer/
├── conf/
│   └── layer.conf                  ← required: declares the layer
├── recipes-core/
│   └── foo/
│       ├── foo_1.0.bb              ← a recipe
│       ├── foo_1.0.bbappend        ← an append
│       └── files/
│           └── fix.patch           ← support files
├── classes/
│   └── mylayer-helpers.bbclass     ← optional shared classes
├── COPYING.MIT
└── README
```

The presence of `conf/layer.conf` is what makes a directory a layer. Everything else is convention.

---

## 18. The Four Kinds of Layers

```
                       LAYERS
                          │
   ┌──────────┬───────────┴──────────┬────────────┐
   │          │                      │            │
┌──────┐  ┌─────────┐         ┌──────────┐  ┌──────────┐
│OE-Core│  │  BSP   │         │  Distro  │  │ Product  │
│       │  │ layer  │         │  layer   │  │  layer   │
└──┬───┘  └────┬────┘         └────┬─────┘  └────┬─────┘
   │           │                   │             │
generic    hardware              policy        product
software   (MACHINE,           (DISTRO,        (your
recipes    kernel,             features,        custom
           bootloader,         systemd vs       recipes
           device tree)        sysvinit, etc.)  & appends)
```

The composition law:

> **Principle 15.** *Generic software lives in OE-Core. Hardware lives in BSP layers. Policy lives in distro layers. Your product lives in your product layer. Cross the boundaries at your peril.*

A typical product build composes:

```
   meta-myproduct                ← your layer
        │
        │ depends on
        ▼
   meta-raspberrypi    ← BSP (chosen by MACHINE)
   meta-poky           ← distro (chosen by DISTRO)
   meta-openembedded   ← extra community recipes (optional)
        │
        │ all depend on
        ▼
   openembedded-core (meta/)    ← the foundation
```

---

## 19. BSP Layers in Detail

A **Board Support Package** (BSP) layer is where hardware specificity lives. Its contents:

```
meta-<vendor>/
├── conf/
│   └── machine/
│       ├── <board-A>.conf       ← MACHINE = "board-A"
│       ├── <board-B>.conf
│       └── include/
│           └── soc-family.inc   ← shared SoC config
├── recipes-kernel/
│   └── linux/
│       ├── linux-<vendor>_5.15.bb        ← vendor kernel recipe
│       └── linux-<vendor>/
│           └── defconfig                  ← kernel config
├── recipes-bsp/
│   └── u-boot/
│       └── u-boot-<vendor>_2023.04.bb    ← vendor bootloader
└── recipes-graphics/
    └── ...                                ← vendor GPU stack
```

What a `machine.conf` typically declares:

```python
# conf/machine/myboard.conf

require conf/machine/include/arm/arch-armv8a.inc

MACHINEOVERRIDES =. "myboard:"

PREFERRED_PROVIDER_virtual/kernel = "linux-vendor"
PREFERRED_PROVIDER_virtual/bootloader = "u-boot-vendor"

KERNEL_IMAGETYPE = "Image"
KERNEL_DEVICETREE = "myvendor/myboard.dtb"

UBOOT_MACHINE = "myboard_defconfig"

SERIAL_CONSOLES = "115200;ttyS0"

IMAGE_FSTYPES = "tar.bz2 ext4 wic.gz"
WKS_FILE = "myboard.wks"
```

### Common BSP layers in the wild

| Vendor / family            | Layer (canonical name)          |
|----------------------------|---------------------------------|
| Raspberry Pi               | `meta-raspberrypi`              |
| NXP i.MX                   | `meta-freescale`, `meta-imx`    |
| Texas Instruments          | `meta-ti`                       |
| STMicroelectronics STM32MP | `meta-st-stm32mp`               |
| BeagleBoard                | `meta-beagleboard`              |
| Intel                      | `meta-intel`                    |
| AMD                        | `meta-amd`                      |
| Xilinx / AMD (FPGA)        | `meta-xilinx`                   |
| NVIDIA Tegra / Jetson      | `meta-tegra`                    |

> **Principle 16.** *A BSP layer is the only legitimate home for `MACHINE` configs, kernel recipes, bootloader recipes, and device trees. If you find these elsewhere, the project is broken.*

---

# Part VI — Production

## 20. The LTS Contract

Yocto issues an LTS release periodically. The current commitment: **four years of support**, comprising standard support followed by extended support.

The strategic question: how does OpenEmbedded select components to honor that contract?

> **Principle 17.** *A distribution cannot outlive its weakest LTS dependency.*

Therefore OE-Core aligns its choices around upstream LTS branches:

- **Kernel** → an LTS kernel (e.g. 5.15, 6.1, 6.6 — kernels marked LTS by kernel.org).
- **U-Boot** → a U-Boot release with vendor maintenance commitments.
- **Toolchain (GCC, glibc)** → versions with stable upstream maintenance.

The practical rule:

> **Principle 18.** *In production, pin to a Yocto LTS branch (e.g. `kirkstone`, `scarthgap`). Never to `master`.*

Master is a moving target. Production is not.

---

## 21. Yocto ≠ Poky

This is the single most common confusion in the literature.

```
   ┌─────────────────────────────────────────────────────────┐
   │                    YOCTO PROJECT                        │
   │                                                         │
   │   Governance · Tooling · LTS · Release engineering      │
   │                                                         │
   │   ┌─────────────────┐  ┌─────────────────────────────┐  │
   │   │    BitBake      │  │    OpenEmbedded-Core        │  │
   │   │    (engine)     │  │    (foundational metadata)  │  │
   │   └─────────────────┘  └─────────────────────────────┘  │
   │                                                         │
   │                ┌──────────────┐                         │
   │                │     POKY     │ ← one reference distro  │
   │                │              │   built on BitBake +    │
   │                │   meta-poky  │   OE-Core + tooling     │
   │                └──────────────┘                         │
   │                                                         │
   └─────────────────────────────────────────────────────────┘
```

- **Yocto Project** is the umbrella: governance, release cadence, LTS, member companies.
- **Poky** is *one* reference distribution, useful as a starting point and a regression target.
- `meta-poky` is no longer the default distro layer in modern workflows. Real products typically define their own distro.

> **Principle 19.** *Speak of Yocto when you mean Yocto. Speak of Poky only when you mean the reference distribution.*

---

# Part VII — The Learning Path

## 22. How to Actually Learn Yocto

Forget the tutorials that begin with `bitbake core-image-minimal`. They teach you to operate the tool without understanding it. Begin instead with the source.

### Step 1 — Clone upstream directly

```sh
git clone https://git.openembedded.org/bitbake
git clone https://git.openembedded.org/openembedded-core
```

These are the two repositories that *are* Yocto. Everything else — Poky, BSP layers, distro layers — sits on top.

### Step 2 — Read the foundations, in order

1. `bitbake/doc/bitbake-user-manual/` — the engine.
2. `openembedded-core/meta/conf/bitbake.conf` — the entry point of variable namespace.
3. `openembedded-core/meta/classes/base.bbclass` — the universal task graph.
4. `openembedded-core/meta/recipes-core/busybox/busybox_*.bb` — a real-world recipe.
5. `openembedded-core/meta/recipes-core/images/core-image-minimal.bb` — a real-world image.

After this, the architecture is permanent.

### Step 3 — Pick a real target

Choose hardware you can hold:

- Raspberry Pi 4 / 5 → `meta-raspberrypi`
- BeagleBone Black → `meta-ti` (or `meta-beagleboard`)
- An i.MX-based dev board → `meta-freescale` / `meta-imx`

Build `core-image-minimal` for it. Boot it. Then modify it: add a package, write a `.bbappend`, change the kernel config.

### Step 4 — Build your own layer

Create `meta-myproduct`. Add one recipe. Add one append. Define a custom image. Pin to an LTS branch.

You are now competent.

---

# Appendix A — Variables to Memorize

| Variable                | Meaning                                                |
|-------------------------|--------------------------------------------------------|
| `MACHINE`               | The hardware target.                                   |
| `DISTRO`                | The distribution policy.                               |
| `WORKDIR`               | The per-recipe working directory.                       |
| `S`                     | Source directory.                                       |
| `B`                     | Build directory.                                        |
| `D`                     | Destination (staged install).                           |
| `T`                     | Task temp directory.                                    |
| `PN` / `PV` / `PR`      | Package name / version / revision.                      |
| `SRC_URI`               | Where to fetch source.                                  |
| `IMAGE_INSTALL`         | Packages to include in an image (user-level).          |
| `PACKAGE_INSTALL`       | Packages to include in the rootfs (derived).            |
| `BBLAYERS`              | Active layers.                                          |
| `DEPENDS`               | Build-time dependencies.                                |
| `RDEPENDS:${PN}`        | Runtime dependencies of the main package.               |
| `PROVIDES`              | Virtual names this recipe provides.                     |
| `PREFERRED_PROVIDER_*`  | Which recipe satisfies a virtual provider.              |
| `TMPDIR`                | `${TOPDIR}/tmp` — all intermediate output.              |
| `DEPLOY_DIR`            | Where final artifacts land.                             |
| `DEPLOY_DIR_IMAGE`      | Where images land.                                      |

---

# Appendix B — Task Map

| Task                         | Inputs        | Outputs                | Purpose                       |
|------------------------------|---------------|------------------------|-------------------------------|
| `do_fetch`                   | `SRC_URI`     | `${DL_DIR}/*`          | Download source.              |
| `do_unpack`                  | downloads     | `${S}`                 | Unpack into source dir.       |
| `do_patch`                   | `${S}`        | `${S}` (patched)       | Apply patches.                |
| `do_prepare_recipe_sysroot`  | sysroot       | recipe sysroot         | Provide build dependencies.   |
| `do_configure`               | `${S}`        | `${B}`                 | Configure build.              |
| `do_compile`                 | `${B}`        | binaries in `${B}`     | Compile.                      |
| `do_install`                 | `${B}`        | `${D}`                 | Install to destination.       |
| `do_package`                 | `${D}`        | per-package staging    | Split into packages.          |
| `do_package_write_{deb,rpm,ipk}` | staging   | `${DEPLOY_DIR}/...`    | Emit binary package files.    |
| `do_rootfs`                  | packages      | `${IMAGE_ROOTFS}`      | Assemble rootfs.              |
| `do_image_<type>`            | rootfs        | `${DEPLOY_DIR_IMAGE}`  | Generate filesystem image.    |

---

# Appendix C — Glossary

- **BitBake** — the Python build engine that interprets metadata.
- **OpenEmbedded (OE)** — the project that authored BitBake and maintains OE-Core.
- **OE-Core** — the foundational metadata layer; the `meta/` directory.
- **Yocto Project** — the governance umbrella; provides LTS, tooling, branding.
- **Poky** — a reference distribution built on BitBake + OE-Core.
- **Layer** — a directory of metadata, declared by a `conf/layer.conf`.
- **Recipe** — a `.bb` file describing how to build one thing.
- **Append** — a `.bbappend` file modifying an existing recipe.
- **Class** — a `.bbclass` file containing reusable logic.
- **BSP layer** — a layer carrying hardware-specific metadata.
- **Distro layer** — a layer carrying distribution policy.
- **MACHINE** — the hardware target variable.
- **DISTRO** — the distribution policy variable.
- **Sstate cache** — signature-keyed cache of task outputs; powers incremental builds.
- **Sysroot** — the staged set of files visible to a recipe at build time.
- **Rootfs** — the filesystem of the target device, built from packages.

---

> *End of manual. Re-read Parts I–IV until the diagrams need no captions. After that, you are no longer learning Yocto — you are practicing it.*

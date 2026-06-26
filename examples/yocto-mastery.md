# Yocto — Mastery
### A Deep Manual of Internals, Principles, and Practice

> *The Zero-to-Hero manual showed you the architecture. This one shows you why the architecture is the way it is — and how it actually works underneath.*

---

## Preface

This is the deep version. It assumes you have read the *Zero-to-Hero* manual or know its equivalent: BitBake parses metadata, recipes describe builds, layers compose, MACHINE and DISTRO parameterize.

What you will learn here:

- How BitBake actually parses, hashes, and schedules.
- How the sstate cache works and why it is the single most important performance mechanism in Yocto.
- How dependencies resolve in two separate worlds (build-time vs runtime).
- How sysroots are constructed per-recipe.
- How packaging splits one recipe into many packages.
- How images, SDKs, and licenses are assembled.
- How kernel and bootloader recipes are structured.
- How to debug, profile, and architect a real product.

Read once cover to cover. Then read it again. Yocto's depth is not in any one concept — it is in how the concepts compose.

---

## Table of Contents

**Part I — Orientation**
1. [The Mental Model](#1-the-mental-model)
2. [The Duality Revisited](#2-the-duality-revisited)
3. [The Ecosystem](#3-the-ecosystem)

**Part II — Metadata Anatomy**
4. [The Six Kinds of Files](#4-the-six-kinds-of-files)
5. [Recipes in Depth](#5-recipes-in-depth)
6. [Override Syntax — the Colon System](#6-override-syntax--the-colon-system)
7. [Variable Flags](#7-variable-flags-varflags)
8. [Appends — Modifying What You Do Not Own](#8-appends--modifying-what-you-do-not-own)
9. [Classes and the Inherit Order](#9-classes-and-the-inherit-order)
10. [Includes, Requires, Patches](#10-includes-requires-patches)
11. [Anonymous Python and Python Functions](#11-anonymous-python-and-python-functions)

**Part III — The Configuration Universe**
12. [The Six Doors and the Parse Order](#12-the-six-doors-and-the-parse-order)
13. [The Variable Namespace](#13-the-variable-namespace)
14. [BUILD, HOST, TARGET, and Multiconfig](#14-build-host-target-and-multiconfig)
15. [The Two Knobs: MACHINE and DISTRO](#15-the-two-knobs-machine-and-distro)
16. [Features: DISTRO, MACHINE, IMAGE, COMBINED](#16-features-distro-machine-image-combined)
17. [The Fetcher](#17-the-fetcher)
18. [License Management and SPDX](#18-license-management-and-spdx)

**Part IV — The Build Engine**
19. [BitBake's Internal Architecture](#19-bitbakes-internal-architecture)
20. [Parse Phase Internals](#20-parse-phase-internals)
21. [The Dependency Graph](#21-the-dependency-graph)
22. [Signatures: How a Task Hash is Built](#22-signatures-how-a-task-hash-is-built)
23. [The Sstate Cache](#23-the-sstate-cache)
24. [Hash Equivalence](#24-hash-equivalence)
25. [Tasks: Definition, Override, Injection](#25-tasks-definition-override-injection)
26. [The Universal Task Graph in Detail](#26-the-universal-task-graph-in-detail)

**Part V — The Sysroot Model**
27. [The Two Sysroots](#27-the-two-sysroots)
28. [DEPENDS vs RDEPENDS](#28-depends-vs-rdepends)
29. [PROVIDES, RPROVIDES, virtual/*](#29-provides-rprovides-virtual)
30. [Multilib](#30-multilib)

**Part VI — Packaging and Images**
31. [Packaging Backends](#31-packaging-backends)
32. [Package Splitting](#32-package-splitting)
33. [Image Recipes in Depth](#33-image-recipes-in-depth)
34. [The wic Image Composer](#34-the-wic-image-composer)
35. [SDK Generation](#35-sdk-generation)

**Part VII — Kernel and Bootloader**
36. [The Kernel Recipe](#36-the-kernel-recipe)
37. [The Bootloader Recipe](#37-the-bootloader-recipe)
38. [Device Trees](#38-device-trees)

**Part VIII — Layers and Composition**
39. [Anatomy of a Layer](#39-anatomy-of-a-layer)
40. [Layer Priority and Conflict Resolution](#40-layer-priority-and-conflict-resolution)
41. [The Four Kinds of Layers](#41-the-four-kinds-of-layers)
42. [BSP Layers Deep Dive](#42-bsp-layers-deep-dive)
43. [Yocto Compatible](#43-yocto-compatible)

**Part IX — Production**
44. [The LTS Contract and Branch Strategy](#44-the-lts-contract-and-branch-strategy)
45. [Reproducible Builds](#45-reproducible-builds)
46. [Security and CVE Tracking](#46-security-and-cve-tracking)
47. [Yocto ≠ Poky](#47-yocto--poky)

**Part X — The Developer Workflow**
48. [devtool](#48-devtool)
49. [recipetool](#49-recipetool)
50. [bitbake-layers](#50-bitbake-layers)
51. [Debugging a Build](#51-debugging-a-build)
52. [Common Errors and Their Meaning](#52-common-errors-and-their-meaning)

**Part XI — Mastery**
53. [How to Read a Yocto Build](#53-how-to-read-a-yocto-build)
54. [How to Architect a Product Layer](#54-how-to-architect-a-product-layer)
55. [A Reading Order](#55-a-reading-order)

**Appendices**
- [A — Variable Reference](#appendix-a--variable-reference)
- [B — Task Reference](#appendix-b--task-reference)
- [C — Override Cheat Sheet](#appendix-c--override-cheat-sheet)
- [D — Fetcher Schemes](#appendix-d--fetcher-schemes)
- [E — Glossary](#appendix-e--glossary)

---

# Part I — Orientation

## 1. The Mental Model

Hold this picture in your mind for the whole manual:

```
   Sources         ┌────────────────────────────────┐         Target
   (upstream)      │            YOCTO               │         device
                   │                                │
   tarballs   ──►  │    ┌─────────┐  ┌──────────┐   │   ──►   ┌───────┐
   git repos       │    │ BitBake │  │ Metadata │   │         │ boot  │
   patches         │    │ engine  │◄─┤ recipes  │   │   ──►   ├───────┤
                   │    └────┬────┘  └──────────┘   │         │rootfs │
                   │         │                      │         └───────┘
                   │    ┌────▼────┐                 │
                   │    │ tasks   │                 │
                   │    │ run     │                 │
                   │    └────┬────┘                 │
                   │         │                      │
                   │    ┌────▼────┐                 │
                   │    │ sstate  │  (cache)        │
                   │    └────┬────┘                 │
                   │         │                      │
                   │    ┌────▼────┐                 │
                   │    │packages │ ──► rootfs      │
                   │    └─────────┘     assembly    │
                   └────────────────────────────────┘
```

Yocto is a pipeline from upstream sources to a bootable device image, with metadata as the program and BitBake as the interpreter.

> **Principle 1.** *Yocto is a compiler whose source language is metadata and whose target language is a bootable filesystem.*

---

## 2. The Duality Revisited

There are exactly two things in Yocto: an **engine** and a body of **metadata**. We covered this in the previous manual. Now examine the boundary more carefully.

### What BitBake actually does

BitBake performs five operations and nothing else:

1. **Read** files matching configured globs.
2. **Parse** them into a data store (a key-value namespace with override semantics).
3. **Build** a directed acyclic graph of tasks from the parsed data.
4. **Hash** every task's inputs to compute a stable signature.
5. **Execute** tasks in dependency order, with parallelism, using the sstate cache to skip tasks whose signature matches a cached result.

That is the entire engine. Notice what is missing: BitBake has no concept of "compiler", "package", "kernel", or "Linux". Those are introduced *exclusively* by metadata.

### What metadata actually is

Metadata is a set of files in six extensions, parsed into a single global data store and many per-recipe data stores. Each store is a flat namespace of variables, with override semantics on top.

> **Principle 2.** *BitBake is a data-store-and-task-graph machine. Metadata is everything that turns that machine into a Linux build.*

The engine is generic enough that BitBake could (and historically has) been used to build non-Linux systems. The Linux specificity is entirely in OE-Core.

---

## 3. The Ecosystem

Yocto is not a single project. It is a constellation:

```
                       ┌──────────────────────────────┐
                       │       Yocto Project          │
                       │       (governance)           │
                       └──────────────┬───────────────┘
                                      │
        ┌─────────────┬───────────────┼──────────────┬─────────────┐
        │             │               │              │             │
   ┌─────────┐  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │ BitBake │  │ OE-Core  │   │  Poky    │   │   BSP    │   │ meta-oe  │
   │ (engine)│  │ (recipes)│   │ (distro) │   │  layers  │   │ (extras) │
   └─────────┘  └──────────┘   └──────────┘   └──────────┘   └──────────┘
        │             │               │              │             │
   git.open       git.open         git.yocto      vendor-       layers-
   embedded.org   embedded.org     project.org    specific      openembedded
```

The components, with their upstream truth:

| Component               | Upstream                                                |
|-------------------------|---------------------------------------------------------|
| BitBake                 | `git.openembedded.org/bitbake`                          |
| OpenEmbedded-Core       | `git.openembedded.org/openembedded-core` (the `meta/`)  |
| Poky (distro)           | `git.yoctoproject.org/poky`                             |
| meta-openembedded       | `git.openembedded.org/meta-openembedded`                |
| BSP layers              | Vendor-specific repositories                            |
| Yocto Project tooling   | `git.yoctoproject.org`                                  |

`poky.git` is a convenience repository that bundles BitBake, OE-Core, and `meta-poky` (the reference distro) in one place. It is the easiest entry point, but it is *not* fundamental — the underlying components are.

> **Principle 3.** *Poky is a convenient assembly. The underlying truth lives in BitBake + OE-Core. Always know which you are working with.*

---

# Part II — Metadata Anatomy

## 4. The Six Kinds of Files

```
                          METADATA
                              │
   ┌──────────┬───────────┬───┴────┬───────────┬──────────┐
   │          │           │        │           │          │
  .bb     .bbappend     .conf   .bbclass     .inc       .patch
recipe   modification  config    class      include     patch
```

| Extension   | One-line role                                       | Has tasks? | Has variables? |
|-------------|-----------------------------------------------------|------------|----------------|
| `.bb`       | Build instructions for one thing.                   | Yes        | Yes            |
| `.bbappend` | Modify an existing recipe.                          | Yes        | Yes            |
| `.conf`     | Declare variables. No logic.                        | No         | Yes            |
| `.bbclass`  | Reusable logic, inherited.                          | Yes        | Yes            |
| `.inc`      | A shared fragment.                                  | Yes        | Yes            |
| `.patch`    | A diff applied to source by `do_patch`.             | No         | No (it's data) |

> **Principle 4.** *Configuration files (`.conf`) declare variables only. Everything else can also declare tasks. The split between "data" and "behavior" is enforced by file type.*

---

## 5. Recipes in Depth

A real-world recipe has more shape than the toy example. Examine this one (lightly annotated):

```python
SUMMARY = "Memory testing utility"
DESCRIPTION = "memtester is a userspace utility for testing the memory subsystem"
HOMEPAGE = "https://pyropus.ca./software/memtester/"
SECTION = "console/utils"

LICENSE = "GPL-2.0-only"
LIC_FILES_CHKSUM = "file://COPYING;md5=b234ee4d69f5fce4486a80fdaf4a4263"

SRC_URI = "https://pyropus.ca./software/memtester/old-versions/memtester-${PV}.tar.gz"
SRC_URI[sha256sum] = "0e3..."

S = "${WORKDIR}/memtester-${PV}"

EXTRA_OEMAKE = "CC='${CC}' \
                CFLAGS='${CFLAGS}' \
                LDFLAGS='${LDFLAGS}'"

do_install() {
    install -d ${D}${bindir}
    install -m 0755 memtester ${D}${bindir}
    install -d ${D}${mandir}/man8
    install -m 0644 memtester.8 ${D}${mandir}/man8
}

FILES:${PN} += "${bindir}/memtester ${mandir}/man8/memtester.8"
```

Anatomy of this recipe:

| Section            | Meaning                                                                  |
|--------------------|--------------------------------------------------------------------------|
| `SUMMARY`/`DESCRIPTION`/`HOMEPAGE`/`SECTION` | Human metadata.                              |
| `LICENSE` + `LIC_FILES_CHKSUM` | Legal metadata. The checksum guards against silent license changes upstream. |
| `SRC_URI`           | A space-separated list of URIs to fetch.                                |
| `SRC_URI[sha256sum]` | A variable flag (a *varflag*) attached to `SRC_URI`. See Chapter 7.    |
| `S`                 | Where the source ends up after `do_unpack`.                             |
| `EXTRA_OEMAKE`      | Arguments passed to `make` by the default `do_compile`.                 |
| `do_install()`      | A shell task: install files into `${D}`, the staging destination.       |
| `FILES:${PN}`       | The list of paths in `${D}` that belong to the main package.            |

Note `${PN}` (package name = "memtester") and `${PV}` (package version, derived from the recipe filename).

### Recipe naming convention

```
<package-name>_<version>.bb
        ↓           ↓
        PN          PV
```

The recipe revision (`PR`) is rarely written explicitly; modern Yocto uses signatures (Chapter 22) to invalidate cached output.

> **Principle 5.** *A recipe is data plus a few shell or Python tasks. Most recipes contain no tasks at all — they inherit them from a class.*

---

## 6. Override Syntax — the Colon System

Yocto's override system is unique and once you understand it, half the metadata becomes readable.

### The five operators

```
   VAR  =  "value"        ← weak assignment (no override applied)
   VAR ?= "value"         ← default (only if VAR is unset)
   VAR ??= "value"        ← weakest default (lowest priority)
   VAR := "value"         ← immediate expansion (resolved at parse time)
   VAR =. "value"         ← string prepend with no space
   VAR .= "value"         ← string append with no space
   VAR += "value"         ← string append with space
   VAR =+ "value"         ← string prepend with space
```

### Override append/prepend/remove

```
   VAR:append      = " more"      ← append exactly the given text (no space added)
   VAR:prepend     = "more "      ← prepend exactly the given text
   VAR:remove      = "foo"        ← remove the matching whitespace-delimited token
```

Crucially: `:append`/`:prepend`/`:remove` are *not* assignment. They are operators that fire **after all assignments**, in the order they appear in metadata. This is how `bbappend` files reliably modify a recipe regardless of parse order.

### Conditional overrides

```
   VAR:class-target  = "value"    ← only when building for target
   VAR:class-native  = "value"    ← only for native (host) recipes
   VAR:arm           = "value"    ← only when TUNE_ARCH = arm
   VAR:qemuarm       = "value"    ← only when MACHINE = qemuarm
```

The list of active overrides is in `OVERRIDES`. Anything appearing in `OVERRIDES` can be used as a conditional suffix.

### Combinations

```
   VAR:append:class-target = " foo"
       ──┬──  ────┬──────
         │        └─ condition: only for target builds
         └─ operator: append
```

> **Principle 6.** *In Yocto, `:` is not a separator. It is a stack of operations applied right-to-left: read the conditions first, then the operator.*

> **Note.** Before Yocto 3.4 (release "honister"), the underscore was used: `VAR_append`, `VAR_class-target`. You will still see this syntax in old layers. Modern code uses `:`.

---

## 7. Variable Flags (varflags)

A varflag is a *flag* attached to a variable. Syntactically:

```
   VARIABLE[flag] = "value"
```

Varflags do not affect variable expansion; they carry metadata *about* the variable. Examples:

```python
SRC_URI[sha256sum]    = "abc123…"             ← integrity check
do_compile[depends]  += "openssl:do_populate_sysroot"
do_compile[noexec]    = "1"                    ← task does nothing
do_compile[network]   = "1"                    ← allow network access
do_install[cleandirs] = "${D}"                 ← clean before running
do_compile[dirs]      = "${B}"                 ← create dirs before running
VAR[doc]              = "Documentation string"
```

### The most important varflags on tasks

| Varflag        | Meaning                                                              |
|----------------|----------------------------------------------------------------------|
| `depends`      | Build-time dependencies on other tasks (recipe:task).                |
| `rdepends`     | Runtime dependencies for task execution.                              |
| `deptask`      | The named task must run on every recipe this depends on.             |
| `rdeptask`     | Like deptask but for runtime dependencies.                            |
| `nostamp`      | Always run; no stamping (caution: invalidates sstate).               |
| `noexec`       | Task is a marker, runs nothing.                                       |
| `network`      | Permit network access from this task (forbidden by default).         |
| `dirs`         | Directories to create before running the task.                       |
| `cleandirs`    | Directories to wipe and recreate before running.                     |
| `vardeps`      | Additional variables whose values participate in the task signature. |
| `vardepsexclude` | Variables to exclude from the task signature.                      |

> **Principle 7.** *Varflags are how the engine learns the behavior of a variable beyond its value. They are the bridge between declarative data and operational semantics.*

---

## 8. Appends — Modifying What You Do Not Own

Appends (`.bbappend`) are the cardinal mechanism for layer hygiene.

```python
# meta-myproduct/recipes-connectivity/openssl/openssl_%.bbappend

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI += " \
    file://0001-cve-2024-XXXX-fix.patch \
    file://my-config.cnf \
    "

do_install:append() {
    install -m 0644 ${WORKDIR}/my-config.cnf ${D}${sysconfdir}/ssl/
}
```

### The wildcard naming convention

```
   openssl_3.0.8.bbappend    ← matches openssl_3.0.8.bb only
   openssl_3.0.%.bbappend    ← matches openssl_3.0.* (any patch level)
   openssl_%.bbappend        ← matches any version of openssl
```

### Why `FILESEXTRAPATHS:prepend := "${THISDIR}/files:"` is everywhere

The `do_fetch` task with a `file://` URI searches in directories listed by `FILESPATH`, which is derived from `FILESEXTRAPATHS`. The `:= "${THISDIR}/files:"` makes the local `files/` directory of the bbappend searchable for `file://` references. The `:=` (immediate expansion) is critical: it captures `${THISDIR}` at parse time, before BitBake moves on to other bbappends that would redefine `THISDIR`.

> **Principle 8.** *Never edit a recipe you do not own. Append it. The `_%` wildcard insulates your modification from upstream version bumps.*

---

## 9. Classes and the Inherit Order

A class is reusable logic. Recipes acquire it via `inherit`. The mechanics:

```
   recipe.bb                    Class hierarchy after inherit:
   ┌────────────────────┐       ┌────────────────────┐
   │ inherit autotools  │  ──►  │ autotools.bbclass  │
   └────────────────────┘       │  inherit autotools-│
                                │  brokensep         │
                                │  inherit pkgconfig │
                                │  …                 │
                                └────────────────────┘
                                          │
                                          ▼
                                ┌────────────────────┐
                                │   base.bbclass     │
                                │  (transitively     │
                                │   inherited by ALL │
                                │   recipes)         │
                                └────────────────────┘
```

### The two species of class

**Global classes** are inherited by every recipe, even those that never write `inherit`. They are listed in `INHERIT` in the global configuration:

```python
# In bitbake.conf or distro config
INHERIT += "buildhistory rm_work"
```

The most important global class is `base.bbclass`. It defines `do_fetch`, `do_unpack`, `do_patch`, `do_build`, and the entire task spine.

**Recipe classes** are inherited explicitly: `inherit cmake`, `inherit autotools`, `inherit systemd`.

### Common recipe classes

| Class       | Provides                                                    |
|-------------|-------------------------------------------------------------|
| `autotools` | `do_configure`/`do_compile`/`do_install` for autotools.     |
| `cmake`     | Same, for CMake.                                            |
| `meson`     | Same, for Meson.                                            |
| `setuptools3` | Same, for Python packages.                                 |
| `cargo`     | Same, for Rust packages.                                    |
| `kernel`    | Everything for building a Linux kernel.                     |
| `module`    | For out-of-tree kernel modules.                             |
| `systemd`   | Enables systemd unit installation and `SYSTEMD_SERVICE`.   |
| `useradd`   | Creates users/groups at rootfs assembly time.               |
| `pkgconfig` | Adds pkg-config support.                                    |
| `native`    | Build for the build host (not for target).                 |
| `nativesdk` | Build for an SDK host (cross from build).                  |
| `cross`     | Build a cross-compiler.                                     |

### The inherit chain matters

Classes can inherit other classes. The order of `inherit` directives matters: the *last* inherit wins for variable assignments, but `:append`/`:prepend` are always cumulative.

> **Principle 9.** *Classes are how Yocto avoids the catastrophe of every recipe spelling out its own build logic. Inherit aggressively; duplicate never.*

---

## 10. Includes, Requires, Patches

### `include` vs `require`

```python
include  example.inc    ← include if present; silent if missing
require  example.inc    ← include if present; ERROR if missing
```

Use `require` for fragments you depend on. Use `include` for optional overrides.

### A patch in `SRC_URI`

```python
SRC_URI += " \
    file://0001-fix-segfault.patch \
    file://0002-feature-x.patch;striplevel=2 \
    file://0003-feature-y.patch;apply=no \
    "
```

Each `file://` reference can carry parameters:

| Parameter      | Meaning                                                       |
|----------------|---------------------------------------------------------------|
| `striplevel=N` | Override the default `-p1` patch strip level.                |
| `apply=no`     | Fetch the file but do not apply it as a patch.                |
| `patchdir=...` | Apply in a subdirectory of `${S}`.                            |
| `subdir=...`   | Unpack the file into a subdirectory.                          |
| `unpack=no`    | Do not unpack (treat the file literally).                     |

### Where the engine looks for patches

`do_patch` finds files via `FILESPATH`, which is composed from `FILESEXTRAPATHS` plus a standard search list (`${PN}/${PV}/`, `${PN}/`, `files/`). That is why the `FILESEXTRAPATHS:prepend := "${THISDIR}/files:"` pattern is universal.

---

## 11. Anonymous Python and Python Functions

Most recipes are pure declarative metadata. When logic is needed, Yocto offers two Python escape hatches.

### Python functions (regular)

A named Python function, callable as a task or by other Python code:

```python
python do_my_check() {
    if d.getVar('SOMETHING') == 'broken':
        bb.error("Configuration broken")
}
addtask my_check before do_compile after do_configure
```

Inside Python tasks, `d` is the recipe's data store. Use `d.getVar(name)` and `d.setVar(name, value)`.

### Anonymous Python (the `__anonymous` function)

A block of Python that runs once *at parse time*, before tasks execute:

```python
python __anonymous () {
    distro = d.getVar('DISTRO')
    if distro == 'poky-tiny':
        d.setVar('PACKAGECONFIG', 'minimal')
    else:
        d.setVar('PACKAGECONFIG', 'full')
}
```

This is how recipes adapt to the build configuration at parse time. Use sparingly: anonymous Python that touches `OVERRIDES` or signature-relevant variables can produce hard-to-debug behavior.

> **Principle 10.** *Declarative first, Python only when declarative cannot express the rule. Anonymous Python runs once, at parse time, before any task.*

---

# Part III — The Configuration Universe

## 12. The Six Doors and the Parse Order

BitBake's variable namespace is constructed in a precise sequence. Memorize it.

```
   START
     │
     ▼
   ┌─────────────────────────────────────────────────────┐
   │ 1. Read bitbake.conf                                │
   │    Defines: S, B, D, T, WORKDIR, BUILD/HOST/TARGET, │
   │             TOPDIR, TMPDIR, DEPLOY_DIR, …            │
   └─────────────────────────────────────────────────────┘
     │
     ▼
   ┌─────────────────────────────────────────────────────┐
   │ 2. Read local.conf  (included by bitbake.conf)      │
   │    User sets: MACHINE, DISTRO, BB_NUMBER_THREADS, … │
   └─────────────────────────────────────────────────────┘
     │
     ▼
   ┌─────────────────────────────────────────────────────┐
   │ 3. Read distro.conf via conf/distro/${DISTRO}.conf  │
   │    Distro policy: features, version, package format │
   └─────────────────────────────────────────────────────┘
     │
     ▼
   ┌─────────────────────────────────────────────────────┐
   │ 4. Read machine.conf via conf/machine/${MACHINE}.conf│
   │    Hardware truth: kernel, bootloader, DTB, console │
   └─────────────────────────────────────────────────────┘
     │
     ▼
   ┌─────────────────────────────────────────────────────┐
   │ 5. Read bblayers.conf                               │
   │    Discover the list of layers in BBLAYERS          │
   └─────────────────────────────────────────────────────┘
     │
     ▼
   ┌─────────────────────────────────────────────────────┐
   │ 6. Read each layer's conf/layer.conf                │
   │    Each layer registers BBFILES, priority, deps     │
   └─────────────────────────────────────────────────────┘
     │
     ▼
   ┌─────────────────────────────────────────────────────┐
   │ 7. Discover all .bb and .bbappend via BBFILES       │
   └─────────────────────────────────────────────────────┘
     │
     ▼
   ┌─────────────────────────────────────────────────────┐
   │ 8. Parse every recipe (in parallel) + apply         │
   │    matching .bbappends                              │
   └─────────────────────────────────────────────────────┘
     │
     ▼
   READY TO BUILD
```

> **Principle 11.** *The build is parameterized at every step. By step 4, BitBake knows what hardware. By step 6, it knows what layers. By step 8, it has the full graph.*

---

## 13. The Variable Namespace

Every recipe gets a per-recipe **data store**: a key-value namespace with override semantics. The most foundational keys describe the per-recipe filesystem layout.

```
   TMPDIR/work/${MULTIMACH_TARGET_SYS}/${PN}/${PV}-${PR}/
       │
       │  This entire directory is WORKDIR for the recipe.
       │
       ├── ${BPN}-${PV}/         ← S: unpacked source
       ├── build/                ← B: build directory (if out-of-tree)
       ├── image/                ← D: where do_install writes
       ├── packages-split/       ← intermediate split for do_package
       ├── pkgdata/              ← per-package metadata
       ├── temp/                 ← logs and task scripts
       │     ├── log.do_compile
       │     ├── run.do_compile
       │     └── …
       └── recipe-sysroot/       ← build-time dependency staging
       └── recipe-sysroot-native/← native build tools staging
```

### Variables you must know

| Variable               | Default form                                   | Meaning                                |
|------------------------|------------------------------------------------|----------------------------------------|
| `WORKDIR`              | `${TMPDIR}/work/${MULTIMACH_TARGET_SYS}/${PN}/${PV}-${PR}` | The recipe's working dir.   |
| `S`                    | `${WORKDIR}/${BPN}-${PV}`                       | Source dir.                            |
| `B`                    | `${S}` (in-tree)                                | Build dir.                             |
| `D`                    | `${WORKDIR}/image`                              | Destination for `do_install`.          |
| `T`                    | `${WORKDIR}/temp`                               | Task scripts and logs.                  |
| `PN`                   | Recipe filename's package name                  | "openssl".                              |
| `BPN`                  | `PN` minus prefixes (`nativesdk-`, `lib32-`, …) | Base package name.                      |
| `PV`                   | Recipe filename's version                       | "3.0.8".                                |
| `PR`                   | Recipe revision                                 | "r0".                                   |
| `PF`                   | `${PN}-${PV}-${PR}`                             | Full package name.                      |
| `TOPDIR`               | The build directory                             | (Where you ran `bitbake`.)             |
| `TMPDIR`               | `${TOPDIR}/tmp`                                 | All intermediate output.                |
| `DEPLOY_DIR`           | `${TMPDIR}/deploy`                              | Final artifacts.                        |
| `DEPLOY_DIR_IMAGE`     | `${DEPLOY_DIR}/images/${MACHINE}`               | Final images.                           |
| `SSTATE_DIR`           | `${TOPDIR}/sstate-cache`                        | Shared state cache.                     |
| `DL_DIR`               | `${TOPDIR}/downloads`                           | Fetched sources.                        |

### Path variables (from `bitbake.conf`)

These follow GNU/POSIX naming and resolve to target-side paths in `${D}`:

| Variable      | Value      | What                |
|---------------|------------|---------------------|
| `bindir`      | `/usr/bin` | Binaries            |
| `sbindir`     | `/usr/sbin`| System binaries     |
| `libdir`      | `/usr/lib` | Libraries           |
| `includedir`  | `/usr/include` | Headers         |
| `sysconfdir`  | `/etc`     | Configuration       |
| `datadir`     | `/usr/share` | Architecture-independent data |
| `localstatedir` | `/var`   | Variable state      |
| `mandir`      | `${datadir}/man` | Man pages     |
| `infodir`     | `${datadir}/info` | Info pages   |

Use these. Never write `/usr/bin` directly.

> **Principle 12.** *Hardcoding paths is the most common recipe bug. Every path in a recipe should be a variable.*

---

## 14. BUILD, HOST, TARGET, and Multiconfig

### The triplet

```
  BUILD machine        HOST machine         TARGET machine
  (where bitbake     (where the binary    (what the binary
   actually runs)    will run)            targets, for compilers)

  ┌─────────────┐    ┌─────────────┐      ┌─────────────┐
  │  x86_64     │    │  aarch64    │      │  aarch64    │
  │  laptop     │    │  embedded   │      │  same as    │
  │             │    │  board      │      │  HOST       │
  └─────────────┘    └─────────────┘      └─────────────┘
```

For almost every recipe, `HOST == TARGET`. The triplet only diverges for *Canadian cross* compilers — a cross-compiler built on x86_64, that runs on x86_64, that produces aarch64 code. There the HOST (where the binary runs) is x86_64, but the TARGET (what it produces code for) is aarch64.

Yocto reflects the triplet in three sets of toolchain variables:

```
   BUILD_*   →   CC_FOR_BUILD,  CFLAGS_FOR_BUILD,  …
   *         →   CC,            CFLAGS,            …     (for HOST=TARGET)
   *_class-native → toolchain redirected to host tools
```

### Recipe variants

A single recipe may be built multiple times for different "classes":

| Class suffix       | What                                                                   |
|--------------------|------------------------------------------------------------------------|
| (default)          | Target build. `HOST = TARGET = the device`.                            |
| `-native`          | Build for the build machine. `HOST = TARGET = BUILD`.                  |
| `-nativesdk`       | Build for an SDK host.                                                 |
| `-cross`           | Build a cross-compiler.                                                |

Inherit `native` and the recipe runs entirely on the build host. This is how Yocto produces build-time tools (e.g. `quilt-native`, `cmake-native`).

### Multiconfig

Multiconfig is a feature for building multiple independent configurations in a single BitBake invocation. Useful for products with heterogeneous compute (an aarch64 Linux side and a Cortex-M baremetal side, for instance).

```python
# conf/local.conf
BBMULTICONFIG = "linux mcu"

# conf/multiconfig/linux.conf
MACHINE = "myboard"
TMPDIR  = "${TOPDIR}/tmp-linux"

# conf/multiconfig/mcu.conf
MACHINE = "myboard-cortexm"
TMPDIR  = "${TOPDIR}/tmp-mcu"
```

Then:

```
bitbake mc:linux:core-image-base mc:mcu:firmware-image
```

Each configuration parses fully independently. Dependencies between them use the `mc:` prefix.

> **Principle 13.** *Multiconfig is rarely needed but priceless when it is. A heterogeneous SoC is one configuration per processor.*

---

## 15. The Two Knobs: MACHINE and DISTRO

```
┌────────────────────────────────────┐  ┌────────────────────────────────────┐
│             MACHINE                │  │             DISTRO                 │
├────────────────────────────────────┤  ├────────────────────────────────────┤
│  HARDWARE TRUTH                    │  │  POLICY TRUTH                      │
│                                    │  │                                    │
│  • CPU architecture (TUNE_PKGARCH) │  │  • Init system                     │
│  • Kernel recipe to build          │  │    (systemd vs sysvinit)           │
│  • Bootloader recipe to build      │  │  • C library (glibc vs musl)       │
│  • Device tree(s)                  │  │  • Package format default          │
│  • Console settings                │  │  • Distro features                 │
│  • Boot image format               │  │  • Distro version string           │
│  • USB / network / storage caps    │  │  • License whitelist               │
│                                    │  │  • Security policy                 │
│                                    │  │                                    │
│  Provided by a BSP LAYER           │  │  Provided by a DISTRO LAYER        │
└────────────────────────────────────┘  └────────────────────────────────────┘
```

### A `machine.conf` skeleton

```python
require conf/machine/include/arm/arch-armv8a.inc

MACHINEOVERRIDES =. "myboard:"

PREFERRED_PROVIDER_virtual/kernel     = "linux-vendor"
PREFERRED_PROVIDER_virtual/bootloader = "u-boot-vendor"

KERNEL_IMAGETYPE   = "Image"
KERNEL_DEVICETREE  = "myvendor/myboard.dtb"
UBOOT_MACHINE      = "myboard_defconfig"
SERIAL_CONSOLES    = "115200;ttyS0"

MACHINE_FEATURES   = "usbhost vfat ext2 alsa rtc wifi bluetooth"

IMAGE_FSTYPES      = "tar.bz2 ext4 wic.gz"
WKS_FILE           = "myboard.wks"
```

### A `distro.conf` skeleton

```python
DISTRO_NAME    = "MyDistro"
DISTRO_VERSION = "1.0"

DISTRO_FEATURES = "acl alsa argp bluetooth ext2 ipv4 ipv6 \
                   pcmcia usbgadget usbhost wifi xattr nfs \
                   zeroconf pci 3g nfc x11 vfat largefile opengl \
                   systemd"

VIRTUAL-RUNTIME_init_manager = "systemd"
VIRTUAL-RUNTIME_initscripts  = "systemd-compat-units"

PREFERRED_VERSION_linux-yocto = "6.6%"

INHERIT += "buildhistory"
BUILDHISTORY_COMMIT = "1"
```

> **Principle 14.** *MACHINE answers "what hardware?" DISTRO answers "what policy?" Together they parameterize the entire build.*

---

## 16. Features: DISTRO, MACHINE, IMAGE, COMBINED

A **feature** is a string token enabling a capability. Yocto exposes four feature variables:

```
   DISTRO_FEATURES        ←  enabled in the distro     (policy)
        ∩
   MACHINE_FEATURES       ←  available in hardware     (capability)
        ═
   COMBINED_FEATURES      ←  actually present in build

   IMAGE_FEATURES         ←  per-image (rootfs assembly time)
```

### The intersection rule

A feature is effective only if it's both desired (`DISTRO_FEATURES`) and supported (`MACHINE_FEATURES`). The intersection is exposed as `COMBINED_FEATURES`. Most recipes test this:

```python
PACKAGECONFIG ??= "${@bb.utils.filter('DISTRO_FEATURES', 'bluetooth wifi', d)}"
```

The pattern `bb.utils.filter('VAR', 'tokens', d)` returns the tokens that are present in the variable.

### Common features

| Variable           | Common tokens                                                                |
|--------------------|------------------------------------------------------------------------------|
| `DISTRO_FEATURES`  | `systemd`, `wayland`, `x11`, `alsa`, `bluetooth`, `wifi`, `pulseaudio`, `pam`, `ipv6`, `opengl` |
| `MACHINE_FEATURES` | `usbhost`, `pci`, `screen`, `keyboard`, `vfat`, `ext2`, `alsa`, `wifi`, `bluetooth`, `rtc` |
| `IMAGE_FEATURES`   | `debug-tweaks`, `dev-pkgs`, `dbg-pkgs`, `read-only-rootfs`, `splash`, `ssh-server-openssh` |

> **Principle 15.** *Features are how Yocto expresses "yes, do that" in a controlled, intersectable way. They are the typesystem of the build.*

---

## 17. The Fetcher

The `do_fetch` task interprets `SRC_URI` and downloads sources. It supports many schemes via a plugin system.

### Scheme summary

| Scheme          | What                                                          |
|-----------------|---------------------------------------------------------------|
| `http://`, `https://`, `ftp://` | Download a file by URL.                       |
| `file://`       | A file present in `FILESPATH` (the layer).                    |
| `git://`        | Clone a git repository.                                       |
| `gitsm://`      | Clone with submodules.                                        |
| `svn://`, `hg://`, `bzr://` | Other VCS systems.                                |
| `npm://`        | Fetch from npm.                                              |
| `crate://`      | Fetch a Rust crate.                                          |
| `gomod://`      | Fetch a Go module.                                           |
| `osf://`        | Fetch from OpenSDK File system.                              |

### Git fetch parameters

```python
SRC_URI = "git://github.com/foo/bar.git;branch=main;protocol=https"
SRCREV  = "abcdef123456…"

# Or follow a moving ref:
SRCREV = "${AUTOREV}"
```

Common parameters on `git://`:

| Parameter         | Meaning                                                       |
|-------------------|---------------------------------------------------------------|
| `branch=NAME`     | The branch to clone.                                          |
| `tag=NAME`        | A specific tag (rare; prefer `SRCREV`).                        |
| `protocol=https`  | Underlying transport (since `git://` denotes the scheme).      |
| `name=NAME`       | Name of this source (when multiple).                          |
| `nobranch=1`      | Do not check that SRCREV is on a branch.                       |
| `destsuffix=DIR`  | Where to unpack.                                              |
| `subpath=PATH`    | Use only a subdirectory of the repo.                          |

### Multiple sources

```python
SRC_URI = "git://example.com/a.git;name=a;branch=main \
           git://example.com/b.git;name=b;branch=main \
           file://my.patch"

SRCREV_a = "abcdef…"
SRCREV_b = "123456…"
```

### Integrity

For `http://`/`https://`/`ftp://`, the integrity is enforced via varflags:

```python
SRC_URI[md5sum]    = "…"
SRC_URI[sha256sum] = "…"   ← strongly preferred
```

Git fetches use SRCREV (commit hash) as integrity.

> **Principle 16.** *The fetcher is plugin-based. SRC_URI is a list, not a string. Every URI may carry parameters.*

---

## 18. License Management and SPDX

Yocto refuses to build a recipe without a license declaration.

```python
LICENSE           = "GPL-2.0-only & MIT"
LIC_FILES_CHKSUM  = "file://COPYING;md5=… \
                     file://LICENSE.MIT;md5=…"
```

### Operators

```
   LICENSE = "GPL-2.0-only"           ← single license
   LICENSE = "GPL-2.0-only | MIT"     ← OR (user's choice)
   LICENSE = "GPL-2.0-only & MIT"     ← AND (both apply)
```

### SPDX identifiers

Modern Yocto uses SPDX-standardized license identifiers exclusively. Common ones:

| Identifier              | Means                               |
|-------------------------|-------------------------------------|
| `MIT`                   | MIT License                         |
| `BSD-3-Clause`          | 3-clause BSD                        |
| `Apache-2.0`            | Apache License 2.0                  |
| `GPL-2.0-only`          | GPLv2 (no later)                    |
| `GPL-2.0-or-later`      | GPLv2 or later                      |
| `LGPL-2.1-only`         | LGPLv2.1                            |
| `MPL-2.0`               | Mozilla Public License 2.0          |

### License rejection

The distro can forbid licenses:

```python
INCOMPATIBLE_LICENSE = "GPL-3.0* LGPL-3.0*"
```

Used in conservative embedded products to avoid the GPL-3 anti-DRM clauses.

### Commercial licenses

Recipes that require special handling declare:

```python
LICENSE_FLAGS = "commercial"
```

To allow them in builds:

```python
LICENSE_FLAGS_ACCEPTED = "commercial"
```

### SPDX manifest output

The `create-spdx` class (inherited globally in modern distros) produces an SBOM:

```
${DEPLOY_DIR}/spdx/<image>.spdx.json
```

This is increasingly required for regulatory compliance.

> **Principle 17.** *Licensing in Yocto is enforced, not advisory. Pin checksums, choose SPDX identifiers, and run `create-spdx` for SBOM output.*

---

# Part IV — The Build Engine

## 19. BitBake's Internal Architecture

BitBake is, internally, a set of cooperating processes:

```
   bitbake (UI/coordinator)
     │
     ├── parser worker(s)        ← parse .bb files in parallel
     │
     ├── runqueue scheduler      ← order tasks by dependency
     │
     ├── task worker(s)          ← execute tasks (forked)
     │       │
     │       ├── shell tasks     (bash)
     │       └── python tasks    (in-process python)
     │
     ├── sstate handler          ← consult/update SSTATE_DIR
     │
     ├── hashserv client (opt)   ← consult hash equivalence service
     │
     └── eventbus                ← UIs subscribe to build events
```

Important: BitBake forks workers. Each task runs in its own process so a crash never takes down the engine.

---

## 20. Parse Phase Internals

When you run `bitbake <image>`:

1. **Boot.** BitBake reads `bitbake.conf` → `local.conf` → `distro.conf` → `machine.conf` → `bblayers.conf` → each `layer.conf`. This produces the **global data store**.
2. **Discovery.** Globs in each layer's `BBFILES` enumerate all `.bb` and `.bbappend` files.
3. **Recipe parse (parallel).** For each recipe:
   - Clone the global data store.
   - Read the `.bb` file.
   - Apply matching `.bbappend` files.
   - Process all `inherit` directives, which textually splice in `.bbclass` files.
   - Evaluate anonymous Python.
   - The result is a **recipe data store**: the recipe's full variable namespace.
4. **Task graph extraction.** From each recipe data store, extract the list of tasks and their interdependencies.
5. **Global dependency graph.** Combine all per-recipe task graphs into one global DAG using `DEPENDS`, `RDEPENDS`, `PROVIDES`, varflag `depends`, etc.

The output of parsing is cached in `${TMPDIR}/cache/`. Subsequent invocations skip parsing unless the recipe (or any file it depends on) has changed.

> **Principle 18.** *Parsing is the slowest phase of a cold build (often >30s). It is parallelized and cached. Never modify metadata at runtime via slow Python.*

---

## 21. The Dependency Graph

After parsing, BitBake holds a directed acyclic graph whose nodes are **tasks** (not recipes!) and edges are dependencies.

```
   busybox:do_compile
        │
        │ depends-on
        ▼
   musl:do_populate_sysroot     (provides headers and libs)
        │
        ▼
   linux-libc-headers:do_populate_sysroot
```

### Three kinds of dependency

```
   Build-time dependency (DEPENDS):
   ─────────────────────────────────
   I need foo's headers and libraries to compile.
   →  foo:do_populate_sysroot must complete before my do_compile.

   Runtime dependency (RDEPENDS):
   ──────────────────────────────
   My package needs bar.deb installed at runtime.
   →  bar must be built and added to the rootfs.

   Task-level dependency (varflag depends):
   ─────────────────────────────────────────
   This specific task needs that specific task done.
   →  Used for fine-grained scheduling.
```

### Example

```python
DEPENDS = "openssl zlib"            # build-time
RDEPENDS:${PN} = "ca-certificates"  # runtime, on the main package
```

This says: to *build* this recipe, openssl and zlib's sysroot must be populated. To *install* this package, ca-certificates must also be installed.

> **Principle 19.** *DEPENDS is recipe-to-recipe at build time. RDEPENDS is package-to-package at runtime. They live in different universes.*

---

## 22. Signatures: How a Task Hash is Built

Every task's inputs are hashed into a **signature**. The signature is the cache key for the sstate cache. Two tasks with the same signature produce the same output, so the cache works.

### What goes into a signature

1. **The task code.** The exact text of the function body.
2. **The values of every variable the task references.**
3. **The signatures of all tasks this task depends on.**
4. **Varflag `vardeps`.** Extra variables the engine should include.
5. **Minus varflag `vardepsexclude`.** Variables explicitly excluded.

### Concretely

For `do_compile` of recipe `foo`, the signature is roughly:

```
   sha256(
     do_compile_function_text +
     value_of(CC) + value_of(CFLAGS) + value_of(LDFLAGS) +
     value_of(EXTRA_OEMAKE) + … +
     signature(foo:do_configure) +
     signature(every_DEPENDS_recipe:do_populate_sysroot)
   )
```

### Inspecting signatures

```sh
bitbake-diffsigs <sigfile1> <sigfile2>
bitbake -S printdiff <recipe>
```

These commands answer the question: "why is this task re-running when I expected sstate to hit?" Almost always the answer is a variable whose value changed and which is in the signature.

> **Principle 20.** *Sstate misses are almost always signature changes. If your build takes too long, learn `bitbake-diffsigs`.*

---

## 23. The Sstate Cache

The shared-state cache is the most important performance mechanism in Yocto. Without it, every build would be a full source rebuild.

### How it works

```
   1. BitBake computes the signature of every task.
   2. Before executing a task, it asks:
         "Is there a sstate entry for this signature?"
   3. If yes: download (or copy from local SSTATE_DIR), unpack, mark task done.
   4. If no:  execute the task; on success, archive the output and upload to sstate.
```

### Sstate entries are tarballs

A sstate entry looks like:

```
sstate:foo:aarch64-poky-linux:1.0:r0:aarch64:3:abcd1234.tar.zst
        │          │          │   │  │           │       │
        │          │          │   │  │           │       └─ task signature hash
        │          │          │   │  │           └─ format version
        │          │          │   │  └─ architecture
        │          │          │   └─ revision
        │          │          └─ version
        │          └─ target sys
        └─ package name
```

### Configuration

```python
# local.conf
SSTATE_DIR = "${TOPDIR}/sstate-cache"

# Or a shared one:
SSTATE_DIR = "/srv/yocto/sstate-cache"

# Or remote:
SSTATE_MIRRORS = " \
  file://.* https://shared.example.com/sstate/PATH;downloadfilename=PATH"
```

### What gets cached

Not every task can be cached. Tasks whose output is filesystem state (`do_install`, `do_package_write_*`, `do_populate_sysroot`) are. Tasks that depend on host state (`do_compile` in some cases) are usually cached too.

### Cleaning

```sh
bitbake -c clean foo            # clean foo's WORKDIR
bitbake -c cleansstate foo      # also wipe foo's sstate entries
bitbake -c cleanall foo         # also wipe downloads
```

> **Principle 21.** *Sstate is what makes Yocto humane. A team that shares a sstate mirror eliminates the per-developer 4-hour first build.*

---

## 24. Hash Equivalence

A subtle but powerful feature.

Problem: changing `CFLAGS` in a low-level recipe invalidates the sstate signature of every downstream recipe, even though the *output* of those downstream recipes is identical (the new CFLAGS made no difference for them).

Solution: hash equivalence. A daemon (`bitbake-hashserv`) maps **task signatures → output hashes**. When a downstream task's signature changes but its inputs are output-equivalent to a previously cached run, BitBake can reuse the cached output.

```
   Signature changed?  →  Ask hashserv:
                          "have you ever seen this signature
                           produce that output hash?"
                          → Yes → reuse cached output.
                          → No  → execute the task.
```

Configuration:

```python
BB_SIGNATURE_HANDLER = "OEEquivHash"
BB_HASHSERVE = "auto"
```

> **Principle 22.** *Hash equivalence breaks the "any change cascades" curse. It is essential for shared CI infrastructure.*

---

## 25. Tasks: Definition, Override, Injection

### Defining a task

```python
do_my_task() {
    echo "hello"
}
addtask my_task before do_compile after do_configure
```

`addtask` is the verb that places a task in the graph. Without it, the function exists but is never run.

### Overriding

```python
do_compile() {                  # full override
    echo "I do nothing now"
}

do_compile:append() {           # append text to the existing task body
    echo "additional step"
}

do_compile:prepend() {          # prepend
    echo "before"
}
```

### Removing

```python
deltask do_compile              # remove the task entirely
```

### Conditional override

```python
do_install:append:class-target() {
    install -d ${D}${sysconfdir}
}
```

> **Principle 23.** *Tasks are not sacred. Add, prepend, append, remove. The graph is malleable.*

---

## 26. The Universal Task Graph in Detail

```
   ┌──────────────────────────────────────────────────────────────┐
   │                       PACKAGE BUILD GRAPH                    │
   └──────────────────────────────────────────────────────────────┘

   do_fetch
      │ (downloads to DL_DIR; integrity checked)
      ▼
   do_unpack
      │ (unpacks into ${S}; clones git into ${S})
      ▼
   do_patch
      │ (applies all file://*.patch from SRC_URI)
      ▼
   do_prepare_recipe_sysroot
      │ (assembles ${WORKDIR}/recipe-sysroot from DEPENDS)
      ▼
   do_configure
      │ (./configure, cmake, meson — provided by inherited class)
      ▼
   do_compile
      │ (make, ninja, cargo — provided by inherited class)
      ▼
   do_install
      │ (installs into ${D})
      ▼
   do_package
      │ (splits ${D} into per-package staging by FILES:*)
      ▼
   do_packagedata     ← write package metadata
      │
      ▼
   do_package_write_<deb|rpm|ipk>
      │ (emits the binary package files into DEPLOY_DIR)
      ▼
   do_populate_sysroot
      │ (publishes headers, libs, pkgconfig files for DEPENDers)
      ▼
   do_build (synthetic — depends on everything above)


   ┌──────────────────────────────────────────────────────────────┐
   │                        IMAGE BUILD GRAPH                     │
   └──────────────────────────────────────────────────────────────┘

   do_rootfs
      │ (uses package manager to install IMAGE_INSTALL into rootfs)
      ▼
   do_image
      │ (applies IMAGE_PREPROCESS_COMMAND, ROOTFS_POSTPROCESS_COMMAND)
      ▼
   do_image_<fstype>
      │ (one task per entry in IMAGE_FSTYPES)
      ▼
   do_image_complete
```

### Image post-processing

```python
ROOTFS_POSTPROCESS_COMMAND += "my_postproc_cmd; "

my_postproc_cmd() {
    # Modify the rootfs tree
    echo "v1.2.3" > ${IMAGE_ROOTFS}/etc/build-version
}
```

These commands run *after* package installation but *before* image format generation.

> **Principle 24.** *Image post-processing is the last sanctioned place to tweak the rootfs. Use it for build identification, removing unnecessary files, or fixing permissions.*

---

# Part V — The Sysroot Model

## 27. The Two Sysroots

Each recipe gets two sysroots:

```
   ${WORKDIR}/recipe-sysroot/         ← target sysroot
       │                              ← contents look like a target filesystem
       │                              ← populated from DEPENDS recipes' do_populate_sysroot
       │
       ├── usr/include/               ← headers from DEPENDS
       ├── usr/lib/                   ← libraries from DEPENDS
       └── usr/lib/pkgconfig/         ← pkg-config files

   ${WORKDIR}/recipe-sysroot-native/  ← native sysroot
       │                              ← contents are tools that run on BUILD
       │                              ← populated from DEPENDS recipes inheriting native
       │
       ├── usr/bin/                   ← native tools (cmake, autoconf, …)
       ├── usr/lib/                   ← native libraries
       └── usr/share/                 ← native data
```

### How it gets populated

When BitBake builds recipe `A` that has `DEPENDS = "B C-native"`:

1. `B:do_populate_sysroot` runs first, depositing its target headers/libs into a global staging area.
2. `C-native:do_populate_sysroot` runs first, depositing its native tools into the global native staging area.
3. `A:do_prepare_recipe_sysroot` runs, **assembling A's private sysroot directories** from the relevant entries in the global staging.

Each recipe sees only what it declared. This is what makes Yocto builds hermetic.

> **Principle 25.** *Sysroots are per-recipe. A recipe sees exactly the dependencies it declared, no more, no less. This is the secret to reproducibility.*

---

## 28. DEPENDS vs RDEPENDS

The single most common confusion for newcomers:

```
   ┌──────────────────────────────────────────────────────────────┐
   │                       DEPENDS                                │
   │  Build-time. Lists RECIPE names.                             │
   │  Resolved by: do_prepare_recipe_sysroot.                     │
   │  Effect: dependency's sysroot output appears in mine.        │
   └──────────────────────────────────────────────────────────────┘

   ┌──────────────────────────────────────────────────────────────┐
   │                       RDEPENDS                               │
   │  Runtime. Lists PACKAGE names.                               │
   │  Resolved by: do_rootfs (package manager).                   │
   │  Effect: my package is installed alongside its deps.         │
   └──────────────────────────────────────────────────────────────┘
```

### Concretely

```python
DEPENDS         = "openssl zlib"           # I need headers and libs to BUILD.
RDEPENDS:${PN}  = "ca-certificates bash"   # I need these PACKAGES at RUNTIME.
RRECOMMENDS:${PN} = "extra-tool"           # Soft runtime dependency.
```

Two different namespaces:

- `DEPENDS` uses recipe names. There is one recipe per "thing to build".
- `RDEPENDS` uses package names. One recipe produces *multiple* packages (Chapter 32).

> **Principle 26.** *DEPENDS is build-time, recipe-to-recipe. RDEPENDS is runtime, package-to-package. The two never share a namespace.*

---

## 29. PROVIDES, RPROVIDES, virtual/*

### PROVIDES

A recipe can declare it provides one or more virtual names:

```python
PROVIDES = "virtual/kernel"
```

Then other recipes write:

```python
DEPENDS = "virtual/kernel"
```

without knowing which concrete recipe provides it. The resolver picks the actual recipe based on `PREFERRED_PROVIDER_virtual/kernel`.

### Common virtual providers

| Virtual name              | Typically provided by                          |
|---------------------------|------------------------------------------------|
| `virtual/kernel`          | `linux-yocto`, `linux-vendor`                  |
| `virtual/bootloader`      | `u-boot`, `grub`, vendor-specific              |
| `virtual/libc`            | `glibc`, `musl`                                |
| `virtual/libgl`           | `mesa`, vendor GPU drivers                     |
| `virtual/libegl`          | `mesa`, vendor GPU drivers                     |
| `virtual/libsdl`          | `libsdl2`                                      |

### PREFERRED_PROVIDER

```python
PREFERRED_PROVIDER_virtual/kernel = "linux-yocto"
```

Usually set in `machine.conf` or `distro.conf`. The machine declares which kernel; the distro declares which libc.

### PREFERRED_VERSION

```python
PREFERRED_VERSION_linux-yocto = "6.6%"
```

The `%` is a glob, so this matches `6.6.10`, `6.6.20`, etc.

### RPROVIDES

The runtime equivalent: a package can claim to provide a runtime name:

```python
RPROVIDES:${PN} = "mta"      # this package can satisfy "mta" RDEPENDS
```

> **Principle 27.** *`virtual/*` is the dependency injection mechanism of Yocto. Recipes depend on capabilities; the configuration chooses implementations.*

---

## 30. Multilib

For ARM-32 binaries on ARM-64 hardware (or 32-bit-on-64-bit Intel), Yocto supports **multilib**: building selected packages in a secondary architecture.

```python
# local.conf
require conf/multilib.conf
MULTILIBS = "multilib:lib32"
DEFAULTTUNE:virtclass-multilib-lib32 = "armv7athf-neon"
IMAGE_INSTALL:append = " lib32-glibc lib32-libstdc++"
```

Multilib packages are prefixed: `lib32-glibc`, `lib64-foo`, `lib32-foo`. Same recipe, different tune, different package.

Used in industrial systems where legacy 32-bit binaries must coexist with a 64-bit OS.

---

# Part VI — Packaging and Images

## 31. Packaging Backends

Yocto can produce packages in three formats:

| Format | Class                | Tool used         | Best for                  |
|--------|----------------------|-------------------|---------------------------|
| `.deb` | `package_deb`        | `dpkg`            | Debian-like systems       |
| `.rpm` | `package_rpm`        | `rpm`/`dnf`       | Fedora-like systems       |
| `.ipk` | `package_ipk`        | `opkg`            | Small embedded systems    |

Selected via:

```python
PACKAGE_CLASSES ?= "package_deb"
```

Multiple can be enabled, but only the first is used at rootfs assembly.

### Choosing a format

- `.ipk` — historic OpenEmbedded default. Smallest tooling, fastest assembly.
- `.deb` — best ecosystem; if you want apt-style upgrades on the target.
- `.rpm` — best for full-OS-like Linux deployments.

> **Principle 28.** *Pick the package format that matches your update strategy on the device, not your dev machine.*

---

## 32. Package Splitting

A single recipe produces *multiple* binary packages by default:

```
   recipe "foo"  →   foo            (the runtime binary)
                     foo-dev        (headers, .so symlinks, .pc files)
                     foo-staticdev  (static libs .a)
                     foo-doc        (man pages)
                     foo-dbg        (debug symbols)
                     foo-locale-*   (locale files)
                     foo-src        (source for debugging)
```

### How splitting works

The `PACKAGES` variable lists the packages this recipe emits, in priority order:

```python
PACKAGES = "${PN}-dbg ${PN}-staticdev ${PN}-dev ${PN}-doc ${PN}-locale ${PN}"
```

For each package, `FILES:<package>` lists which files in `${D}` belong to it:

```python
FILES:${PN}     = "${bindir}/foo ${libdir}/lib*.so.*"
FILES:${PN}-dev = "${includedir} ${libdir}/lib*.so ${libdir}/pkgconfig"
```

Files match in *priority order*: the first package whose `FILES` glob matches a file claims it. That is why `${PN}-dbg` is listed first (it claims `.debug` files) and `${PN}` is listed last (it claims the leftovers).

### Customizing splits

```python
PACKAGE_BEFORE_PN += "foo-utils"
FILES:foo-utils = "${bindir}/foo-helper"
RDEPENDS:${PN} += "foo-utils"      # main package now requires foo-utils
```

> **Principle 29.** *One recipe, many packages. Splitting is automatic but tunable. The split is what makes Yocto images small.*

---

## 33. Image Recipes in Depth

```python
SUMMARY = "Production image for myproduct"
LICENSE = "MIT"

inherit core-image extrausers

IMAGE_FEATURES += "ssh-server-openssh package-management splash"

IMAGE_INSTALL += " \
    kernel-modules \
    linux-firmware \
    myproduct-app \
    myproduct-config \
    networkmanager \
    "

IMAGE_FSTYPES = "wic.gz tar.bz2"
WKS_FILE      = "myproduct.wks"

# Strong runtime guarantees
IMAGE_OVERHEAD_FACTOR  = "1.2"
IMAGE_ROOTFS_EXTRA_SPACE = "65536"   # KB

# Add a user
EXTRA_USERS_PARAMS = "useradd -m -P secret operator;"
```

### The flow

```
   IMAGE_INSTALL  (recipe-author list)
        │
        │ + IMAGE_INSTALL from inherited classes
        │ + dependencies expanded
        ▼
   PACKAGE_INSTALL (final list given to do_rootfs)
        │
        │ do_rootfs uses the configured package manager
        │ to install everything into ${IMAGE_ROOTFS}
        ▼
   ${IMAGE_ROOTFS} (tree)
        │
        │ ROOTFS_POSTPROCESS_COMMAND fires
        ▼
   ${IMAGE_ROOTFS} (modified)
        │
        │ do_image_<fstype> for each IMAGE_FSTYPES entry
        ▼
   Final images in DEPLOY_DIR_IMAGE
```

### Image classes worth knowing

| Class                    | Purpose                                                |
|--------------------------|--------------------------------------------------------|
| `core-image`             | Standard image foundation.                             |
| `image`                  | Lower-level than core-image (rarely inherited directly). |
| `extrausers`             | Add users/groups via `EXTRA_USERS_PARAMS`.             |
| `image-buildinfo`        | Embed build identification into the image.             |
| `read-only-rootfs`       | Generate a read-only rootfs.                           |
| `populate_sdk`           | Generate an SDK for app developers.                    |

> **Principle 30.** *An image recipe is a curated list, plus post-processing, plus a filesystem format. Everything else is convenience.*

---

## 34. The wic Image Composer

`wic` is Yocto's image partitioner. It composes the final disk image from:

- A `.wks` (kickstart) file describing partition layout.
- The rootfs produced by `do_rootfs`.
- Kernel and bootloader artifacts from `DEPLOY_DIR_IMAGE`.

### A `.wks` file

```
# myproduct.wks
part /boot --source bootimg-partition --ondisk mmcblk0 --fstype=vfat \
           --label boot --active --align 4 --size 64
part /     --source rootfs            --ondisk mmcblk0 --fstype=ext4 \
           --label root --align 4 --use-uuid
bootloader --append="console=ttyS0,115200 root=PARTLABEL=root rw"
```

Invocation: with `WKS_FILE = "myproduct.wks"` and `wic` in `IMAGE_FSTYPES`, BitBake builds a complete bootable `.wic` image.

> **Principle 31.** *Stop hand-crafting disk images. Describe the partition layout in `.wks` and let `wic` assemble it.*

---

## 35. SDK Generation

The SDK is a self-extracting installer containing:

- A cross-toolchain (compiler, linker, sysroot).
- pkg-config files for libraries available on the target.
- Environment setup script (`environment-setup-*`).

### Two ways to build an SDK

```sh
# 1. Standalone SDK from an image:
bitbake <image> -c populate_sdk

# 2. Extensible SDK (eSDK), which embeds bitbake itself:
bitbake <image> -c populate_sdk_ext
```

Output:

```
${DEPLOY_DIR}/sdk/poky-glibc-x86_64-<image>-<machine>-toolchain-<ver>.sh
```

### Why the eSDK matters

The eSDK ships a functional bitbake. Application developers can:

```sh
devtool add myapp git://my.example/myapp.git
devtool build myapp
devtool deploy-target myapp root@board
```

…without ever cloning the full Yocto tree.

> **Principle 32.** *The SDK is your contract with application developers. Give them a stable, versioned SDK and they will never need to learn Yocto.*

---

# Part VII — Kernel and Bootloader

## 36. The Kernel Recipe

Kernel recipes inherit `kernel.bbclass`. The class provides:

- `do_compile` builds zImage/Image/uImage.
- `do_install` installs the kernel and modules.
- Package splits: `kernel-image-<type>`, `kernel-modules`, `kernel-dev`, `kernel-vmlinux`, …
- Device tree compilation and packaging.

### A real kernel recipe (sketch)

```python
inherit kernel

require recipes-kernel/linux/linux-yocto.inc

LINUX_VERSION = "6.6.10"

SRC_URI = " \
    git://git.yoctoproject.org/linux-yocto.git;name=machine;branch=v6.6/standard/base \
    file://defconfig \
    file://0001-add-custom-driver.patch \
    "
SRCREV_machine = "abcdef…"

COMPATIBLE_MACHINE = "myboard"

KCONFIG_MODE = "alldefconfig"
```

### Device tree handling

```python
KERNEL_DEVICETREE = "myvendor/myboard.dtb"
```

Set in `machine.conf`. The kernel recipe compiles and deploys the listed DTBs alongside the kernel image.

### Adding a config fragment

The modern way is via `KCONFIG_MODE` and config fragments:

```
linux-yocto/files/myboard.cfg
```

```
CONFIG_USB_GADGET=y
CONFIG_USB_ETH=m
CONFIG_NETFILTER=y
```

Listed in `SRC_URI`, applied by the `kern-tools` machinery.

> **Principle 33.** *Configure the kernel by config fragments, not by editing a monolithic `.config`. Fragments are reviewable.*

---

## 37. The Bootloader Recipe

Almost always U-Boot. Recipe inherits `uboot-config` (which selects a `UBOOT_MACHINE` config).

```python
require recipes-bsp/u-boot/u-boot-common.inc
require recipes-bsp/u-boot/u-boot.inc

PROVIDES = "virtual/bootloader"

SRC_URI = " \
    git://source.denx.de/u-boot.git;protocol=https;branch=master \
    file://0001-myboard-support.patch \
    "
SRCREV = "abcdef…"

COMPATIBLE_MACHINE = "myboard"
```

In `machine.conf`:

```python
UBOOT_MACHINE = "myboard_defconfig"
UBOOT_ENTRYPOINT = "0x80008000"
UBOOT_LOADADDRESS = "0x80008000"
```

> **Principle 34.** *Bootloader, kernel, and device tree are a triplet — they negotiate together. They all live in the BSP layer.*

---

## 38. Device Trees

The device tree (`.dtb`) describes the hardware to the kernel at boot time. Yocto sources them from the kernel tree.

- `KERNEL_DEVICETREE` lists which `.dtb` files to build.
- Built `.dtb` files are deployed to `DEPLOY_DIR_IMAGE`.
- The bootloader loads kernel + dtb.

For custom hardware, place a `myboard.dts` in the kernel recipe's `SRC_URI` and reference it in `KERNEL_DEVICETREE`.

---

# Part VIII — Layers and Composition

## 39. Anatomy of a Layer

```
meta-myproduct/
├── conf/
│   ├── layer.conf                   ← required
│   └── distro/                       ← if this is also a distro layer
│       └── myproduct.conf
├── classes/                          ← shared classes
│   └── myproduct-image.bbclass
├── recipes-core/
│   └── myapp/
│       ├── myapp_1.0.bb
│       └── files/
│           ├── myapp.service
│           └── my-fix.patch
├── recipes-images/
│   └── myproduct-image.bb
├── recipes-bsp/                      ← if BSP-like content
├── COPYING.MIT
└── README
```

### A real `layer.conf`

```python
BBPATH .= ":${LAYERDIR}"

BBFILES += "${LAYERDIR}/recipes-*/*/*.bb \
            ${LAYERDIR}/recipes-*/*/*.bbappend"

BBFILE_COLLECTIONS         += "myproduct"
BBFILE_PATTERN_myproduct    = "^${LAYERDIR}/"
BBFILE_PRIORITY_myproduct   = "10"

LAYERDEPENDS_myproduct      = "core openembedded-layer"
LAYERSERIES_COMPAT_myproduct = "scarthgap"
```

### What each line says

| Line                        | Meaning                                                |
|-----------------------------|--------------------------------------------------------|
| `BBPATH`                    | Add this layer to BitBake's search path.               |
| `BBFILES`                   | Globs for recipes/appends to discover.                 |
| `BBFILE_COLLECTIONS`        | Name of this collection (one per layer).               |
| `BBFILE_PATTERN_*`          | Regex matching files belonging to this collection.     |
| `BBFILE_PRIORITY_*`         | Override priority; higher wins on conflict.            |
| `LAYERDEPENDS_*`            | Required other layers (by their collection name).      |
| `LAYERSERIES_COMPAT_*`      | Which Yocto releases this layer supports.              |

---

## 40. Layer Priority and Conflict Resolution

When two `.bb` files for the same recipe exist in two layers, the one with **higher `BBFILE_PRIORITY`** wins.

```
  meta-A   has openssl_3.0.8.bb  with priority 5
  meta-B   has openssl_3.0.8.bb  with priority 10   ← B wins
```

`.bbappend` files do not compete — all matching `.bbappends` apply, in priority order.

> **Principle 35.** *Priority resolves recipe conflicts. Appends always compose. Never solve conflict by deleting; raise priority.*

---

## 41. The Four Kinds of Layers

```
            ┌─────────────────────────────────────────┐
            │                LAYERS                   │
            └─────────────────────────────────────────┘
                              │
        ┌─────────┬───────────┴──────────┬──────────────┐
        │         │                      │              │
   ┌─────────┐ ┌────────┐         ┌──────────┐   ┌──────────┐
   │ OE-Core │ │  BSP   │         │  Distro  │   │ Product  │
   │         │ │ layer  │         │  layer   │   │  layer   │
   │ Generic │ │Hardware│         │ Policy   │   │ Your     │
   │recipes  │ │(MACHINE│         │(DISTRO,  │   │ custom   │
   │         │ │ kernel,│         │ features)│   │ stuff    │
   │         │ │ uboot, │         │          │   │          │
   │         │ │  DTB)  │         │          │   │          │
   └─────────┘ └────────┘         └──────────┘   └──────────┘
```

> **Principle 36.** *Generic in OE-Core. Hardware in BSP. Policy in distro. Product in your layer. Respect these boundaries or your build will rot within a year.*

---

## 42. BSP Layers Deep Dive

A BSP layer typically contains:

```
meta-<vendor>/
├── conf/
│   ├── layer.conf
│   └── machine/
│       ├── <board-A>.conf
│       ├── <board-B>.conf
│       └── include/
│           └── soc-family.inc           ← shared SoC config
├── recipes-kernel/
│   └── linux/
│       ├── linux-<vendor>_<ver>.bb
│       └── linux-<vendor>/
│           ├── defconfig
│           └── *.cfg                     ← config fragments
├── recipes-bsp/
│   ├── u-boot/
│   │   └── u-boot-<vendor>_<ver>.bb
│   ├── firmware/
│   │   └── <vendor>-firmware_<ver>.bb
│   └── formfactor/                       ← screen size, input devices, etc.
├── recipes-graphics/
│   └── <vendor>-gpu-driver_<ver>.bb
├── recipes-multimedia/
│   └── <vendor>-vpu_<ver>.bb
└── wic/
    └── <board>.wks
```

### Common BSP layers

| Vendor / family            | Layer                          |
|----------------------------|--------------------------------|
| Raspberry Pi               | `meta-raspberrypi`             |
| NXP i.MX                   | `meta-freescale`, `meta-imx`   |
| Texas Instruments          | `meta-ti`                      |
| STMicroelectronics STM32MP | `meta-st-stm32mp`              |
| BeagleBoard                | `meta-beagleboard`             |
| Intel                      | `meta-intel`                   |
| AMD                        | `meta-amd`                     |
| Xilinx (FPGA)              | `meta-xilinx`                  |
| NVIDIA Tegra / Jetson      | `meta-tegra`                   |

---

## 43. Yocto Compatible

The Yocto Project maintains a "Yocto Compatible" badge for layers. A compatible layer:

- Declares `LAYERSERIES_COMPAT_*` correctly.
- Passes the `yocto-check-layer` validation script.
- Does not break the build when added.

For production use, prefer Yocto Compatible layers. They will not surprise you.

> **Principle 37.** *In production, every layer in `BBLAYERS` should declare `LAYERSERIES_COMPAT_` matching your release branch. Mismatches are silent bombs.*

---

# Part IX — Production

## 44. The LTS Contract and Branch Strategy

Yocto issues a release every six months (April and October). Some are designated **LTS**.

```
   Standard release:  6 months of support
   LTS release:       4 years of support (2 standard + 2 extended)
```

### Recent and current LTS releases

| Codename     | Version | Released | LTS until |
|--------------|---------|----------|-----------|
| Dunfell      | 3.1     | Apr 2020 | Apr 2024  |
| Kirkstone    | 4.0     | Apr 2022 | Apr 2026  |
| Scarthgap    | 5.0     | Apr 2024 | Apr 2028  |
| Walnascar    | 5.2     | Apr 2025 | — (standard) |
| Whinlatter   | 6.0     | Oct 2025 | TBD       |

(Verify current state; LTS designations evolve.)

### The strategy

> **Principle 38.** *In production, pin to an LTS branch. Track upstream LTS within that branch (e.g., `kirkstone-next`). Never pin to `master`.*

The LTS commitment is structural: kernel, U-Boot, toolchain, all selected as upstream LTS where possible. A distribution cannot outlive its weakest LTS dependency.

---

## 45. Reproducible Builds

A reproducible build produces byte-identical output regardless of when, where, or by whom it is built. Yocto supports this via several mechanisms:

```python
# Enable reproducible mode
INHERIT += "reproducible_build"
SOURCE_DATE_EPOCH = "1700000000"
BUILD_REPRODUCIBLE_BINARIES = "1"
```

What gets normalized:

- File timestamps → `SOURCE_DATE_EPOCH`.
- Build paths → stripped from binaries via `debug-prefix-map`.
- Build user/host → omitted.
- File ordering → sorted.

### Why this matters

For safety-critical, regulated, or supply-chain-secure deployments, byte-identical reproducibility is a precondition. Two builds from the same sources at different times must match.

> **Principle 39.** *Reproducibility is a build-time property. Once you have it, every other guarantee — provenance, SBOM, integrity — becomes possible.*

---

## 46. Security and CVE Tracking

The `cve-check` class produces a CVE report for every image build.

```python
INHERIT += "cve-check"
```

Output:

```
${DEPLOY_DIR}/cve/<image>-<machine>.cve
${DEPLOY_DIR}/cve/<image>-<machine>.json
```

The class checks each package's `CVE_PRODUCT` against the NVD database. CVEs marked patched (via `CVE_STATUS` or matching backports) are filtered.

```python
# In an openssl bbappend, mark a CVE as patched
CVE_STATUS[CVE-2023-12345] = "patched: backported in 0001-fix.patch"
```

> **Principle 40.** *CVE tracking is automated. Run `cve-check` in CI; fail the build on unpatched criticals.*

---

## 47. Yocto ≠ Poky

Restating the distinction at depth:

- **Yocto Project**: governance, branding, LTS commitments, member program, release engineering.
- **OpenEmbedded**: the technical ecosystem — BitBake + OE-Core.
- **Poky**: one reference distribution.

Modern products typically:

- Use Yocto release branches (`scarthgap`, `kirkstone`).
- Build on top of OE-Core directly.
- Define their own distro (`meta-mydistro`).
- Do not include `meta-poky` at all.

> **Principle 41.** *Poky is a teaching distribution. Production deployments outgrow it.*

---

# Part X — The Developer Workflow

## 48. devtool

`devtool` is Yocto's developer convenience layer. It manages a private "workspace layer" and provides commands for the common developer flow.

```sh
# Add a new recipe from a git URL
devtool add myapp https://github.com/example/myapp.git

# Modify an existing recipe (clones source, sets up a working tree)
devtool modify openssl

# Build the recipe being modified
devtool build openssl

# Deploy directly to a running board
devtool deploy-target openssl root@192.168.1.2

# Finish: generate a patch series and reset
devtool finish openssl meta-myproduct
```

`devtool modify` does something subtle and clever:

```
   1. Reads SRC_URI from the recipe.
   2. Clones the source into a workspace tree (a real git repo with branches).
   3. Writes a bbappend that redirects SRC_URI to the local clone.
   4. Now you edit code in the workspace; bitbake builds from there.
   5. `devtool finish` extracts your changes as patches into your layer.
```

> **Principle 42.** *`devtool` collapses the hours-long recipe-iteration loop into seconds. Learn it before writing a single bbappend by hand.*

---

## 49. recipetool

`recipetool` generates recipes from upstream sources.

```sh
recipetool create -o myapp.bb https://github.com/example/myapp.git
```

The tool inspects the source, detects the build system, and emits a starting recipe. It is rarely perfect but is always a faster start than writing from scratch.

---

## 50. bitbake-layers

Inspect and manipulate layer configuration.

```sh
bitbake-layers show-layers                       # list active layers
bitbake-layers show-recipes 'openssl*'           # find recipes
bitbake-layers show-overlayed                    # find recipes overlayed across layers
bitbake-layers show-appends                      # find appends
bitbake-layers add-layer ../meta-extra           # add to bblayers.conf
bitbake-layers remove-layer ../meta-extra
bitbake-layers create-layer ../meta-myproduct    # scaffold a new layer
```

> **Principle 43.** *`bitbake-layers show-overlayed` is the answer to "why is my version of foo being ignored?"*

---

## 51. Debugging a Build

### Locating logs

```
${WORKDIR}/temp/log.do_<task>
${WORKDIR}/temp/run.do_<task>      ← the actual script that ran
```

`log.do_compile` is the captured stdout/stderr. `run.do_compile` is the bash script BitBake generated — you can run it manually to reproduce.

### Reproducing a task

```sh
bitbake -c <task> <recipe>            # run a specific task
bitbake -c devshell <recipe>          # open a shell with the recipe's environment
bitbake -c devpyshell <recipe>        # open a Python shell with the recipe's d
```

`devshell` is invaluable: a shell where `S` is the source directory, `${CC}` is set, sysroot is staged. You can run `./configure` and `make` by hand.

### Inspecting variables

```sh
bitbake -e <recipe> | less                   # full environment dump
bitbake -e <recipe> | grep -E '^CC=|^CFLAGS='
```

`bitbake -e` is the most-used debugging command. It shows every variable, where it was set, and how it was modified.

### Signature debugging

```sh
bitbake -S printdiff <recipe>                # which variables changed signatures
bitbake-diffsigs <sigfile1> <sigfile2>       # diff two signature files
```

> **Principle 44.** *Every Yocto failure leaves a paper trail in `${WORKDIR}/temp`. Read the logs before guessing.*

---

## 52. Common Errors and Their Meaning

| Error                                        | What it actually means                                  |
|----------------------------------------------|---------------------------------------------------------|
| `Nothing PROVIDES 'X'`                       | A DEPENDS or PROVIDES resolution failed.                |
| `Multiple .bb files matching X`              | Recipe name collision; check priorities.                |
| `QA Issue: file installed but not shipped`   | `do_install` wrote files outside any package's FILES.   |
| `QA Issue: ELF binary contains relocations`  | Likely a TUNE/CFLAGS mismatch; check architecture.       |
| `Hash mismatch: SRC_URI[sha256sum]`          | Upstream changed the tarball. Verify, then update.      |
| `do_fetch failed`                            | Network or upstream URL issue. Check `DL_DIR`.          |
| `Layer X is not compatible with this series` | `LAYERSERIES_COMPAT_*` mismatch.                        |
| `RDEPENDS_${PN} contains unsatisfied X`      | Runtime dep on a non-existent package name.             |

### The QA system

`insane.bbclass` enforces dozens of build-quality rules. They fire as warnings or errors. Reading their messages is how you learn what Yocto considers correct.

> **Principle 45.** *Yocto's QA messages are not optional. Every QA warning is a future bug.*

---

# Part XI — Mastery

## 53. How to Read a Yocto Build

When something breaks, the diagnostic sequence is:

```
   1. Read the error message in the bitbake output.
   2. Identify the failing task and recipe.
   3. Open ${WORKDIR}/temp/log.do_<task>.
   4. If the log is unclear, open run.do_<task> and rerun.
   5. If a variable looks wrong: bitbake -e <recipe> | grep VAR.
   6. If sstate is mis-hitting: bitbake -S printdiff <recipe>.
   7. If a dependency is missing: bitbake-layers show-recipes.
```

This sequence resolves 90% of issues.

---

## 54. How to Architect a Product Layer

A well-architected product layer is organized by *concern*, not by *recipe*:

```
meta-myproduct/
├── conf/
│   ├── layer.conf
│   ├── distro/
│   │   └── myproduct.conf              ← your DISTRO
│   └── machine/                         ← if you have custom hardware
│       └── myboard.conf
├── recipes-core/
│   ├── images/
│   │   ├── myproduct-image.bb
│   │   └── myproduct-image-dev.bb
│   ├── packagegroups/
│   │   ├── packagegroup-myproduct-base.bb
│   │   ├── packagegroup-myproduct-network.bb
│   │   └── packagegroup-myproduct-graphics.bb
│   └── tweaks/
│       └── myproduct-config_1.0.bb     ← config files
├── recipes-myproduct/
│   └── myapp/
│       └── myapp_1.0.bb
├── recipes-bsp/                         ← appends to BSP recipes
│   └── u-boot/
│       └── u-boot-myvendor_%.bbappend
├── recipes-kernel/                      ← kernel config fragments
│   └── linux/
│       └── linux-yocto_%.bbappend
└── classes/
    └── myproduct-image.bbclass          ← shared image logic
```

### Architectural rules

1. **One distro per product family.** Defines features, init system, package format.
2. **Package groups for capabilities.** Each capability (network, graphics, telemetry) is one `packagegroup-*.bb`. Images install package groups, not individual packages.
3. **Config files in their own recipe.** Versioned, packaged, upgradable.
4. **Appends, not edits.** Every modification to a foreign recipe is a bbappend.
5. **Pin LTS.** Commit a release branch tag in `bblayers.conf` documentation.

### Package groups: a worth-its-weight pattern

```python
# packagegroup-myproduct-base.bb
SUMMARY = "Base packages for myproduct"
inherit packagegroup

RDEPENDS:${PN} = " \
    busybox \
    systemd \
    networkmanager \
    chrony \
    "
```

Images then say:

```python
IMAGE_INSTALL += "packagegroup-myproduct-base packagegroup-myproduct-network"
```

Maintenance becomes: edit one package group, every image updates.

> **Principle 46.** *Package groups are how mature Yocto products manage 200+ packages without losing their minds.*

---

## 55. A Reading Order

After this manual, read in this order:

1. **`meta/conf/bitbake.conf`** — the variable namespace foundation.
2. **`meta/classes/base.bbclass`** — the universal task graph.
3. **`meta/classes/autotools.bbclass`** — a real, complex recipe class.
4. **`meta/classes/kernel.bbclass`** — the kernel build pattern.
5. **`meta/classes/image.bbclass`** + **`meta/classes/core-image.bbclass`** — how rootfs is assembled.
6. **`bitbake/lib/bb/runqueue.py`** — the task scheduler (advanced).
7. **`bitbake/lib/bb/siggen.py`** — signature computation (advanced).

After step 5 you are productive. After step 7 you are dangerous.

---

# Appendix A — Variable Reference

### Recipe metadata
`SUMMARY`, `DESCRIPTION`, `HOMEPAGE`, `SECTION`, `LICENSE`, `LIC_FILES_CHKSUM`

### Versions
`PN`, `BPN`, `PV`, `PR`, `PF`, `PE` (epoch)

### Source
`SRC_URI`, `SRCREV`, `S`, `B`, `WORKDIR`

### Filesystem layout (target paths)
`bindir`, `sbindir`, `libdir`, `includedir`, `sysconfdir`, `datadir`, `mandir`, `infodir`, `localstatedir`

### Dependencies
`DEPENDS`, `RDEPENDS:${PN}`, `RRECOMMENDS:${PN}`, `RPROVIDES:${PN}`, `PROVIDES`

### Provider selection
`PREFERRED_PROVIDER_<name>`, `PREFERRED_VERSION_<recipe>`

### Build configuration
`CC`, `CXX`, `LD`, `AR`, `CFLAGS`, `CXXFLAGS`, `LDFLAGS`, `EXTRA_OEMAKE`, `EXTRA_OECONF`

### Packaging
`PACKAGES`, `FILES:<pkg>`, `PACKAGE_ARCH`, `ALLOW_EMPTY:<pkg>`, `CONFFILES:<pkg>`

### Image
`IMAGE_INSTALL`, `PACKAGE_INSTALL`, `IMAGE_FEATURES`, `IMAGE_FSTYPES`, `IMAGE_ROOTFS`, `IMAGE_OVERHEAD_FACTOR`

### Distro / machine
`DISTRO`, `DISTRO_FEATURES`, `DISTRO_VERSION`, `MACHINE`, `MACHINE_FEATURES`, `COMBINED_FEATURES`

### Toolchain / tune
`TUNE_PKGARCH`, `TARGET_OS`, `TARGET_VENDOR`, `MULTIMACH_TARGET_SYS`

### Cache and output
`TMPDIR`, `DEPLOY_DIR`, `DEPLOY_DIR_IMAGE`, `SSTATE_DIR`, `SSTATE_MIRRORS`, `DL_DIR`

### Layer
`BBLAYERS`, `BBFILES`, `BBFILE_PRIORITY_<layer>`, `LAYERDEPENDS_<layer>`, `LAYERSERIES_COMPAT_<layer>`

---

# Appendix B — Task Reference

| Task                                 | What                                                |
|--------------------------------------|-----------------------------------------------------|
| `do_fetch`                           | Download all entries in `SRC_URI`.                  |
| `do_unpack`                          | Unpack archives into `${S}`.                        |
| `do_patch`                           | Apply all `*.patch` from `SRC_URI`.                 |
| `do_prepare_recipe_sysroot`          | Assemble recipe-private sysroot from `DEPENDS`.    |
| `do_configure`                       | Configure build (autoconf / cmake / meson).         |
| `do_compile`                         | Compile source.                                     |
| `do_install`                         | Install into `${D}`.                                |
| `do_package`                         | Split `${D}` into packages by `FILES:*`.            |
| `do_packagedata`                     | Write package metadata.                             |
| `do_package_write_deb/rpm/ipk`       | Emit `.deb`/`.rpm`/`.ipk` files.                    |
| `do_populate_sysroot`                | Stage headers/libs for downstream `DEPENDS`.        |
| `do_rootfs`                          | Image task: assemble rootfs from packages.          |
| `do_image`                           | Image task: run rootfs post-processing.             |
| `do_image_<fstype>`                  | Generate one filesystem format.                     |
| `do_image_complete`                  | Image task: synthetic, depends on all formats.      |
| `do_build`                           | Synthetic per-recipe task; depends on everything.   |
| `do_clean` / `do_cleansstate`        | Cleanup.                                            |
| `do_devshell`                        | Open a shell with the recipe's environment.         |

---

# Appendix C — Override Cheat Sheet

```
   =       weak assignment (lowest binding)
   ?=      default (only if unset)
   ??=     weakest default
   :=      immediate expansion
   +=      append with space
   =+      prepend with space
   .=      append without space
   =.      prepend without space

   :append      operator: append (post-assignment)
   :prepend     operator: prepend (post-assignment)
   :remove      operator: remove whitespace-delimited token

   :class-target    condition: building for target
   :class-native    condition: building for build host
   :<arch>          condition: TUNE_ARCH match
   :<machine>       condition: MACHINE match
   :<feature>       condition: feature is in OVERRIDES
```

Combined: `VAR:append:class-target = " foo"` — append `" foo"`, but only when building for target.

---

# Appendix D — Fetcher Schemes

| Scheme           | Example                                                         |
|------------------|-----------------------------------------------------------------|
| `http://https://`| `https://example.com/foo-1.0.tar.gz`                            |
| `ftp://`         | `ftp://example.com/pub/foo-1.0.tar.gz`                          |
| `file://`        | `file://my-patch.patch` (found via `FILESPATH`)                 |
| `git://`         | `git://github.com/foo/bar.git;branch=main;protocol=https`       |
| `gitsm://`       | Like `git://` but with submodules.                              |
| `svn://`         | `svn://example.com/repo;module=foo;rev=1234`                    |
| `hg://`          | Mercurial.                                                      |
| `bzr://`         | Bazaar.                                                         |
| `npm://`         | `npm://registry.npmjs.org;package=foo;version=1.0`              |
| `npmsw://`       | Shrinkwrap-based npm fetch.                                     |
| `crate://`       | `crate://crates.io/serde/1.0.197`                               |
| `gomod://`       | Go modules.                                                     |
| `osf://`         | Open SDK fetcher (rare).                                        |

---

# Appendix E — Glossary

- **BitBake** — the Python build engine that interprets metadata.
- **OpenEmbedded** — the project that authored BitBake and maintains OE-Core.
- **OE-Core** — the foundational metadata (`meta/`).
- **Yocto Project** — the governance umbrella.
- **Poky** — a reference distribution.
- **Layer** — a directory of metadata declared by a `conf/layer.conf`.
- **Recipe** (`.bb`) — build instructions for one thing.
- **Append** (`.bbappend`) — a recipe modification.
- **Class** (`.bbclass`) — reusable logic, inherited.
- **Include** (`.inc`) — a shared fragment.
- **BSP layer** — a layer with hardware-specific metadata.
- **Distro layer** — a layer with distribution policy.
- **MACHINE** — the hardware target variable.
- **DISTRO** — the distribution policy variable.
- **Sstate cache** — signature-keyed cache of task outputs.
- **Hash equivalence** — service mapping signatures to output hashes.
- **Sysroot** — a recipe's staged dependency view.
- **Rootfs** — the filesystem of the target.
- **Image recipe** — a recipe that declares package lists and produces a rootfs.
- **Package recipe** — a recipe producing a binary package.
- **PROVIDES / virtual/** — abstract dependency naming.
- **PREFERRED_PROVIDER** — selects a concrete implementation of a virtual.
- **DEPENDS** — build-time dependencies (recipe names).
- **RDEPENDS** — runtime dependencies (package names).
- **PACKAGES** — the binary packages a recipe emits.
- **FILES:<pkg>** — what goes into each binary package.
- **DEPLOY_DIR** — final artifact output.
- **wic** — image partitioner; uses `.wks` files.
- **devtool** — Yocto's developer workspace tool.
- **eSDK** — extensible SDK; embeds BitBake.
- **LTS** — long-term support release (currently four years).
- **SPDX** — standard license identifiers; emitted as SBOM.

---

> *End of manual. Read it twice. Then build something.*

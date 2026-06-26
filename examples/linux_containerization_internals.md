# Linux Containerization Internals
## A Deep Dive into Namespaces, Cgroups, and Process Isolation


## Table of Contents

- [Linux Containerization Internals](#linux-containerization-internals)
  - [A Deep Dive into Namespaces, Cgroups, and Process Isolation](#a-deep-dive-into-namespaces-cgroups-and-process-isolation)
  - [Table of Contents](#table-of-contents)
  - [1. Introduction](#1-introduction)
    - [Document Scope](#document-scope)
  - [2. Namespaces](#2-namespaces)
    - [2.1 Origin and Motivation](#21-origin-and-motivation)
    - [2.2 Fundamental Principles](#22-fundamental-principles)
    - [2.3 Namespace Types](#23-namespace-types)
    - [2.4 Kernel Implementation](#24-kernel-implementation)
    - [2.5 Key System Calls](#25-key-system-calls)
    - [2.6 Worked Example: Creating a PID Namespace](#26-worked-example-creating-a-pid-namespace)
  - [3. Control Groups (Cgroups)](#3-control-groups-cgroups)
    - [3.1 Philosophy and Design Goals](#31-philosophy-and-design-goals)
    - [3.2 Architecture and Hierarchy](#32-architecture-and-hierarchy)
    - [3.3 Cgroup v1 vs Cgroup v2](#33-cgroup-v1-vs-cgroup-v2)
    - [3.4 Resource Controllers](#34-resource-controllers)
    - [3.5 Kernel Integration: Scheduler and Beyond](#35-kernel-integration-scheduler-and-beyond)
    - [3.6 Worked Example: Constraining CPU and Memory](#36-worked-example-constraining-cpu-and-memory)
  - [4. Process Isolation](#4-process-isolation)
    - [4.1 The Isolation Stack](#41-the-isolation-stack)
    - [4.2 Namespace × Cgroup Interaction](#42-namespace--cgroup-interaction)
    - [4.3 Security Boundaries and Their Limits](#43-security-boundaries-and-their-limits)
    - [4.4 Rootless Containers and User Namespaces](#44-rootless-containers-and-user-namespaces)
  - [5. History and Evolution](#5-history-and-evolution)
    - [5.1 Before Containers: chroot and the BSD Jail Model](#51-before-containers-chroot-and-the-bsd-jail-model)
    - [5.2 The Birth of Namespaces (2002–2008)](#52-the-birth-of-namespaces-20022008)
    - [5.3 Cgroups Enter the Kernel (2007–2008)](#53-cgroups-enter-the-kernel-20072008)
    - [5.4 LXC, Docker, and the Container Revolution (2008–2014)](#54-lxc-docker-and-the-container-revolution-20082014)
    - [5.5 The Cgroup v2 Rearchitecture (2016–present)](#55-the-cgroup-v2-rearchitecture-2016present)
    - [5.6 Recent Kernel Developments](#56-recent-kernel-developments)
  - [6. OCI and CRI: Standardizing the Ecosystem](#6-oci-and-cri-standardizing-the-ecosystem)
    - [6.1 The Open Container Initiative (OCI)](#61-the-open-container-initiative-oci)
    - [6.2 The Container Runtime Interface (CRI)](#62-the-container-runtime-interface-cri)
    - [6.3 From OCI Spec to Kernel Primitives](#63-from-oci-spec-to-kernel-primitives)
    - [6.4 The Runtime Landscape](#64-the-runtime-landscape)
  - [7. Conclusion](#7-conclusion)
    - [Key Takeaways](#key-takeaways)
    - [Paths for Further Exploration](#paths-for-further-exploration)
  - [8. References and Further Reading](#8-references-and-further-reading)
    - [Kernel Documentation and Source](#kernel-documentation-and-source)
    - [Specifications](#specifications)
    - [Key Papers and Posts](#key-papers-and-posts)
    - [Books](#books)
    - [CVEs Referenced](#cves-referenced)

---

## 1. Introduction

Modern cloud infrastructure rests on a deceptively simple idea: that a single Linux kernel can host many isolated workloads simultaneously, each believing it owns the machine. This is the promise of **Linux containers** — and it is delivered not by a monolithic "container subsystem," but by the careful composition of several orthogonal kernel primitives.

Unlike hypervisor-based virtualization, which interposes a full virtual machine between a guest OS and physical hardware, container isolation is implemented *entirely in user/kernel space on a single shared kernel*. This architectural choice has profound consequences: containers start in milliseconds, consume negligible overhead, and share the host's kernel code and page cache — but they also inherit the kernel's attack surface and rely on the correctness of its isolation mechanisms.

This document examines those mechanisms at the conceptual and implementation level. The two foundational pillars are:

- **Namespaces** — which partition global kernel resources so that processes see only a private slice of the system.
- **Control Groups (cgroups)** — which account for and limit the consumption of physical resources (CPU, memory, I/O, network) by groups of processes.
```markdown
# Linux Containerization Internals — A compact reference

## Contents
- Introduction; Namespaces; Cgroups; Process Isolation; History & Evolution; OCI & CRI; Conclusion; References

## 1. Introduction
Modern cloud infra rests on one kernel hosting many isolated workloads. Linux containers achieve this not via a monolithic subsystem but by composing kernel primitives: namespaces (visibility isolation) and cgroups (resource accounting/limits). Containers share the host kernel and page cache, so they start fast and are efficient, but they inherit kernel attack surface; namespaces+cgroups are necessary but not sufficient security boundaries.

## 2. Namespaces
Namespaces partition global kernel resources so processes see a private instance. Design principles: per-process/per-type association stored in `task_struct`/`nsproxy`, reference-counted lifetimes (namespaces can outlive creators), hierarchical behaviors for PID/user namespaces, and composability (a process may belong to different namespace types simultaneously). Namespaces do not provide communication channels by themselves.

Types (Linux 6.x): `mnt` (mount tree), `uts` (hostname), `ipc` (System V/POSIX IPC), `pid` (PID trees), `net` (network stack), `user` (UID/GID mapping), `cgroup` (visible cgroup root), `time` (clock offsets). Each type has an internal kernel struct; `nsproxy` bundles most pointers. `/proc/<pid>/ns/` exposes membership.

Key syscalls: `clone(2)` with `CLONE_NEW*` flags, `unshare(2)`, and `setns(2)`. PID namespaces are nested (child sees only its subtree), user namespaces enable rootless containers via UID/GID mapping. Example: creating a PID namespace with `clone(CLONE_NEWPID|CLONE_NEWUSER,...)` yields PID 1 inside the namespace while host PID differs.

## 3. Control Groups (Cgroups)
Cgroups answer "what resources can a process use?" Goals: resource limiting, accounting, and control. Cgroups are hierarchical and exposed via `/sys/fs/cgroup`. v1 had multiple independent hierarchies (one per controller) causing confusion; v2 (unified single hierarchy) fixed ownership/delegation problems and introduced PSI (pressure metrics).

Controllers include `cpu` (CFS integration: `cpu.weight`, `cpu.max`), `memory` (`memory.max`, `memory.high`, OOM handling), `io` (`io.max`, `io.weight`), `pids` (`pids.max`), plus others (`hugetlb`, `perf_event`, `rdma`). Kernel integration is deep: cgroups hook into scheduler, page allocator (`mem_cgroup_charge()`), block layer (`blkcg`) and provide notifications (`cgroup.events`).

Example (cgroup v2): create `/sys/fs/cgroup/demo`; `echo "50000 100000" > cpu.max` to limit to 50% of one core; `echo 268435456 > memory.max` to cap memory, then place PIDs in `demo/cgroup.procs`.

## 4. Process Isolation
A container is a composed isolation stack: cgroups (resource limits) + namespaces (visibility) augmented by capabilities, seccomp-BPF, and LSMs (AppArmor/SELinux). Cgroups and namespaces are orthogonal: runtime typically `clone()` with `CLONE_NEW*` flags and then place the child into a cgroup by writing its PID to `cgroup.procs`. Limitations: namespaces do not alone provide privilege isolation; cgroups limit resources but not intent; the shared kernel is the irreducible attack surface (historic escapes: CVE-2019-5736, CVE-2022-0185, CVE-2022-0847). User namespaces allow rootless containers via UID/GID mapping but come with tradeoffs for network capabilities.

## 5. History & Evolution (high level)
`chroot` → FreeBSD jails → Solaris Zones → Linux namespaces evolved (mnt, uts, ipc, pid, net, user, cgroup, time). Cgroups (2008) grew and later rearchitected in v2 (2016) to a unified hierarchy. Docker (2013) popularized images and distribution; OCI (2015) and CRI/ Kubernetes standardized runtime+image interfaces. Recent kernel trends: eBPF + cgroup hooks, idmapped mounts, time namespaces, unprivileged namespace hardening.

## 6. OCI & CRI
OCI defines `config.json` (runtime spec) mapping directly to kernel primitives (namespaces, resources, seccomp). CRI defines a gRPC interface for kubelet → runtime (RunPodSandbox/CreateContainer/etc.). The runtime chain: kubelet → CRI (containerd/CRI-O) → OCI runtime (`runc`/`crun`) → kernel primitives (clone, cgroup writes, mounts, seccomp). Runtimes: `runc`, `crun` (C), `youki` (Rust), `gVisor` (runsc), `Kata` (VM-based), with containerd/CRI-O orchestrating.

## 7. Conclusion — Key points
Namespaces = visibility isolation; cgroups = resource isolation; both are required and must be combined with capabilities/seccomp/LSMs for production security. The shared kernel remains the fundamental constraint; solutions (rootless, gVisor, Kata) trade compatibility/overhead for stronger isolation. OCI/CRI standardize interfaces enabling interoperable tooling.

## 8. References (selected)
Kernel docs (`Documentation/admin-guide/cgroup-v2.rst`, `Documentation/userspace-api/namespaces.rst`), `man 7 namespaces`/`man 7 cgroups`, OCI/OCI image specs, CRI API, `runc` source, LWN articles (Tejun Heo, Michael Kerrisk), Brendan Gregg, Liz Rice, and notable CVEs: CVE-2019-5736, CVE-2022-0185, CVE-2022-0847.

*Document produced April 2026. Reflects Linux kernel 6.x behavior unless otherwise noted.*
```
**4. No implicit communication.** Namespaces do not provide communication channels. A process can communicate with processes in other namespaces only through mechanisms that explicitly cross namespace boundaries (e.g., a socket bound to the host network namespace, a shared bind mount).

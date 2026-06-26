# Securing a Container Platform — The Architect's Foundation

> Security is not a feature you add. It's a property that emerges from correct design.  
> This document is about building the mental model — not the checklist.

---

## The Threat Model First

Before any tool, any config, any policy — you must answer four questions:

**What are you protecting?**  
Data. Credentials. Compute resources. The host kernel. Other tenants on the same machine. The supply chain (your images, your registry). Customer trust.

**From whom?**  
External attackers (RCE via your app, image pull from a compromised registry).  
Malicious insiders (developers who push backdoored images).  
Compromised dependencies (a package in your image that becomes malicious).  
Lateral movement (an attacker who owns one container trying to reach others).

**What does a successful attack look like?**  
Container breakout → attacker reaches the host kernel.  
Privilege escalation → container process gains root on host.  
Data exfiltration → container reads secrets it shouldn't access.  
Supply chain compromise → malicious code running in your production image.  
Lateral movement → compromised container reaches databases, other services.

**What is your acceptable risk?**  
You cannot reach zero risk. You make tradeoffs between security, operational complexity, and developer velocity. Knowing your acceptable risk lets you make deliberate tradeoffs instead of blind ones.

Every security decision in this document maps back to these four questions.

---

## The Attack Surface of a Container Platform

Most people think: *"I need to secure my container."*  
The right question is: *"Where are all the places an attacker can enter my platform?"*

```
Registry          ← poisoned images, credential theft
     ↓
Build pipeline    ← injected malicious code, leaked secrets in layers
     ↓
Image             ← vulnerable packages, embedded credentials, bloated attack surface
     ↓
Daemon            ← the most dangerous process on the host, runs as root
     ↓
Container runtime ← kernel vulnerabilities, namespace escapes
     ↓
Container         ← compromised app, privilege escalation, capability abuse
     ↓
Network           ← lateral movement, traffic interception, DNS poisoning
     ↓
Host kernel       ← the shared boundary — the only true isolation
```

Each layer is an independent attack surface. Hardening one doesn't protect the others.

---

## Principle I — The Kernel Is the Only Boundary

This is the most important thing to understand about container security.

Containers share the host kernel. There is no hypervisor between a container process and the kernel. When a container process makes a system call, it goes directly to the same kernel that the host and every other container uses.

This means: **if an attacker finds a kernel vulnerability and exploits it from inside a container, they own the host.** Full stop. No container configuration saves you from a kernel exploit.

The consequence for architecture:

**Don't run untrusted code in containers on the same host as sensitive workloads.** The separation is logical, not physical. If you need true isolation — multi-tenant SaaS, user-provided code execution — you need VMs or a runtime with a stronger boundary (gVisor, Kata Containers, which add a thin kernel between container and host).

**Keep your kernel up to date.** Container security advisories are almost always kernel CVEs. The kernel is the product you're actually shipping.

**Minimize kernel attack surface with seccomp.** Every system call your container can make is a potential exploit path. Docker's default seccomp profile blocks ~44 syscalls. A custom profile for your specific workload can block 280+ of the 300+ available. A blocked syscall cannot be exploited, even if a vulnerability exists.

```
# See what syscalls your app actually uses (run during development):
strace -ff -e trace=all -o /tmp/syscalls ./your-app

# Build a seccomp profile from actual usage
# Use oci-seccomp-bpf-hook or similar tooling
```

---

## Principle II — Defense in Depth Is Not Redundancy

People misunderstand defense in depth. It doesn't mean doing the same thing twice. It means that each layer of security independently limits what an attacker can do, assuming all other layers have been bypassed.

Think of it as blast radius reduction.

An attacker who exploits an RCE in your web app is now inside a container. What can they do? The answer depends entirely on what you've taken away from them.

**No root** → they can't write to system paths, can't install tools, can't bind to privileged ports.

**No capabilities** → they can't open raw sockets (no network scanning), can't load kernel modules, can't change file ownership, can't mount filesystems.

**Read-only filesystem** → they can't drop a backdoor binary, can't modify your app code, can't create cron jobs.

**No unnecessary network access** → they can't reach your database directly even if they know the credentials. They're isolated to the frontend network.

**Secrets not in environment** → they can't read `DATABASE_URL=postgres://admin:password@db:5432/prod` from `/proc/1/environ`.

**Resource limits** → they can't run a cryptominer that saturates your CPU, can't fork-bomb your system, can't exhaust memory and cause OOM on other containers.

Each of these is independently valuable. An attacker who defeats one still faces all the others. The goal is not to make attack impossible — it's to make each step harder, noisier, and more expensive than the reward.

---

## Principle III — The Docker Daemon Is the Crown Jewel

The Docker daemon runs as root. It is the most privileged process on your host. Whoever controls the daemon controls the machine.

This has three implications:

**The daemon socket (`/var/run/docker.sock`) is equivalent to root.**  
Any process that can read and write this socket can run `docker run --privileged -v /:/host alpine chroot /host`. This mounts the entire host filesystem into a container and gives you a root shell on the host in under one second. Mounting this socket into a container — for CI/CD agents, monitoring tools, log shippers — is giving that container unconditional root on the host. Evaluate every case.

**The daemon's attack surface is large.**  
The daemon exposes a REST API. It pulls images from the internet. It manages the kernel's cgroup and namespace subsystems. It runs build pipelines. Any vulnerability in the daemon is a root vulnerability. Keep it minimal: don't enable the TCP socket without mTLS, use the minimum required API version, consider rootless mode.

**Rootless Docker changes the equation.**  
In rootless mode, the Docker daemon itself runs as a non-root user. A compromised daemon cannot escalate to root on the host. This is the correct direction for production — at the cost of some features (host networking has limitations, memory cgroup limits may require kernel tuning). The security gain is fundamental, not cosmetic.

```bash
# Check if you're running rootless
docker info | grep "rootless"

# The daemon's own process on the host:
ps aux | grep dockerd
# rootful: you see "root" in the first column
# rootless: you see your username
```

---

## Principle IV — Images Are a Supply Chain

Every image you run in production is a trust decision. You are trusting:

- The registry that served you the image
- The maintainer who published it  
- The base OS it's built from
- Every package installed in it
- The build pipeline that assembled it
- The hardware that ran the build

A compromised image in production is indistinguishable from a legitimate one until it does something malicious. And by then, the damage may already be done.

**The attack vectors:**

*Typosquatting* — `python:3-1.2-slim` instead of `python:3.12-slim`. Attacker registers a similar name with a backdoored image. You mistype it in a Dockerfile. You pull it. You run it. The image looks normal. It also quietly exfiltrates credentials.

*Tag mutation* — the `latest` tag on Docker Hub can be updated by anyone with push access. The image you pulled last week and the image behind the same tag today might be different. A compromised maintainer account can push a backdoored image to an existing tag.

*Compromised upstream* — the base image you trust gets a CVE-laden package pushed upstream. Your next build silently includes it.

*Secrets in layers* — a developer runs a build that accidentally bakes an API key into an image layer. They realize and remove it in the next commit. The key is gone from the latest tag but visible in the image history of the previous build. If that image was pushed to a registry, the key is now public.

**The architectural responses:**

*Pin by digest, not tag.*  
```dockerfile
FROM python:3.12-slim@sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```
A digest is a cryptographic hash of the image content. It cannot be forged. It cannot be mutated. If the image changes, the digest changes. This is the only immutable reference.

*Sign images with cosign.*  
Signing creates a cryptographic proof that a specific person or system built a specific image. Your deployment policy can require a valid signature — unsigned images are rejected before they can run.

```bash
# Sign an image after build (requires keyless or key-based setup)
cosign sign --key cosign.key myregistry/myapp@sha256:<digest>

# Verify before deployment
cosign verify --key cosign.pub myregistry/myapp@sha256:<digest>
```

*Scan every image in CI, before push.*  
Vulnerability scanning after deployment is too late. Integrate scanning into the build pipeline as a quality gate. A critical CVE fails the build.

```bash
trivy image --exit-code 1 --severity CRITICAL myapp:latest
```

*Use a private registry with access control.*  
Public Docker Hub has no audit trail, no access control, and no image signing enforcement. A private registry (ECR, GHCR, Artifact Registry, Harbor) lets you enforce: who can push, who can pull, which images have been scanned, which have valid signatures.

---

## Principle V — Secrets Have a Lifecycle

A secret that lives in an environment variable is not a secret. It's a credential left in a public place with a sign that says "please don't look."

The lifecycle of a secret:

```
Generation → Storage → Injection → Use → Rotation → Revocation
```

Most teams get injection slightly wrong and everything else deeply wrong.

**Generation**: secrets should be generated with a cryptographically secure RNG, with enough entropy. `openssl rand -hex 32` is acceptable. Your name and the year is not.

**Storage**: never in git. Never in Dockerfiles. Never in docker-compose.yaml committed to a repo. The correct answer is a secrets manager: HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager. These provide: access control (who can read which secret), audit logging (who read it, when), automatic rotation, and revocation.

**Injection**: the secret enters the container at runtime as a file at `/run/secrets/name`, mounted from a tmpfs (memory-only, never written to disk). The process reads it once, uses it, discards the reference. Not as an environment variable. Not as a build argument. Not in a config file baked into the image.

**Use**: the application reads the secret from the filesystem, not from the environment. If the application crashes and produces a core dump, the secret is not in the dump (it was in memory, but not in a location that a core dump necessarily captures the full content of). If the application logs its configuration on startup, the secret is not in the log (because it was read from a file, not part of a configuration struct).

**Rotation**: secrets should be rotatable without redeploying the application. This means the application either re-reads the file periodically, or you have a mechanism to signal it to reload. If a rotation requires a full redeploy, you'll defer rotation indefinitely, which means your secrets never rotate, which means a leaked secret stays leaked.

**Revocation**: if a secret is compromised, you need to revoke it within minutes, not days. This requires knowing where it's used. If the same database password is hardcoded in 40 microservices across 12 repos, revocation is a multi-day incident. If secrets are centralized in a secrets manager with audit logs, revocation is one API call.

---

## Principle VI — Network Security Is Topology, Not Firewall Rules

The correct model for container network security is not "add firewall rules to block bad traffic." It's "design the topology so bad traffic has nowhere to go."

**Network segmentation by trust level:**

```
Internet
    ↓
[ DMZ network ] — nginx, load balancers, anything internet-facing
    ↓
[ Application network ] — your APIs, services that talk to each other
    ↓
[ Data network ] — databases, caches, queues (internal: true)
```

The data network should be `internal: true`. Containers on this network cannot make outbound connections to the internet. They cannot reach the application network unless a container is explicitly connected to both. A compromised application container cannot directly exfiltrate data to an external server — it can't reach the internet. It can only reach what's on the same network.

This is network defense in depth: even if your app is compromised, the blast radius is bounded by the network topology.

**The DNS amplification insight:**

Docker's internal DNS at `127.0.0.11` resolves container names. This is only within the Docker network. But it means: if your database is named `postgres`, any container on the same network can resolve it. Network segmentation — separate networks — ensures that only the containers that should reach the database are on a network where `postgres` resolves.

**East-west traffic:**

North-south traffic (client to server) gets a lot of security attention. East-west traffic (service to service inside the platform) gets almost none. But once an attacker is inside your platform, they move east-west. A compromised frontend container tries to reach the database directly, bypassing your API's auth layer.

The answer is: **mTLS between services.** Every service presents a certificate. Every service verifies the certificate of who it's talking to. An attacker who compromises a container without the right certificate cannot impersonate a trusted service. This is what service meshes (Istio, Linkerd) implement — but you can do it manually at the application layer too.

---

## Principle VII — Runtime Security Is Behavioral, Not Structural

Everything so far is about what you configure before the container runs. Runtime security is about what you observe and enforce while it's running.

**The insight**: malicious behavior is often detectable as an anomaly against a baseline of normal behavior.

A web server:
- Listens on port 80/443
- Makes outbound connections to the database on port 5432
- Reads files in `/app`
- Forks worker processes

If that same container suddenly:
- Opens a raw socket (port scanning)
- Connects to an external IP on port 4444 (C2 server)
- Reads `/etc/shadow`
- Executes `/bin/bash` spawned from the web process

— something is very wrong. These behaviors are normal for an attacker, abnormal for an nginx process.

**Falco** is the standard tool for this. It uses eBPF to observe kernel system calls and compares them against rules. A rule like "if a web process opens a shell, alert" runs at the kernel level — the malicious process cannot hide from it by operating in userspace.

```yaml
# Example Falco rule: detect shell spawned in a web container
- rule: Shell Spawned by Web Process
  desc: A shell was spawned by a process commonly used to serve web requests
  condition: >
    spawned_process and
    proc.name in (shell_binaries) and
    proc.pname in (web_server_binaries)
  output: >
    Shell spawned by web server (user=%user.name shell=%proc.name 
    parent=%proc.pname container=%container.name)
  priority: WARNING
```

**The difference between structural and behavioral security:**

Structural security says: "the container cannot do X because we took away capability Y."  
Behavioral security says: "if the container tries to do X, we know immediately."

Both are necessary. Structural security prevents attacks. Behavioral security detects when structural security has been bypassed.

---

## Principle VIII — Least Privilege Is a Process, Not a Setting

Least privilege means: every component has exactly the permissions it needs to do its job, and nothing more.

This is not a setting you apply. It's an ongoing process of asking: *does this actually need this?*

**Does the container need to run as root?** Almost never. 95% of web applications, APIs, and background workers have no reason to be root. The only exception is when they need to bind port <1024 (use `CAP_NET_BIND_SERVICE` instead) or manage other processes.

**Does the container need the network namespace?** If it's a batch job that processes files and exits, it may not need any network access at all. A container with `--network none` cannot exfiltrate data, period.

**Does the container need to write to the filesystem?** If not, `--read-only`. The only writable paths should be explicitly declared tmpfs mounts for things that genuinely need to be written (temp files, PID files, unix sockets).

**Does the container need all 14 default capabilities?** Almost certainly not. Drop all, add back only what's needed. The discipline is: when you add a capability back, you should be able to state exactly why that specific capability is necessary.

```bash
# What capabilities does a container actually use?
# Run with full capabilities in staging, observe with:
docker run --cap-add=ALL --security-opt seccomp=unconfined \
  your-app 2>&1 | tee /tmp/cap-trace.log

# Or use capable (BCC tool) to observe actual capability usage
```

**Does this service need access to this other service?** If your email service doesn't need to talk to your payment processor, they should be on different networks with no route between them. Least privilege at the network level.

The process: start with nothing, add only what you can justify. Not: start with everything, remove what you notice you don't need. The latter leaves dozens of unexamined permissions.

---

## What Good Security Looks Like End-to-End

```
Developer writes code
    ↓
Pre-commit hooks lint the Dockerfile (hadolint)
    ↓
CI pipeline builds the image with BuildKit
    → secrets injected via --mount=type=secret
    → no secrets in ARGs, ENV, or COPY
    ↓
CI scans the image (trivy --exit-code 1 --severity CRITICAL)
    ↓
Image signed with cosign
    ↓
Image pushed to private registry with immutable tag (git SHA)
    ↓
Deployment policy verifies signature before pulling
    ↓
Container runs with:
    → non-root user
    → --cap-drop=ALL + explicit minimal caps
    → --read-only + tmpfs for writable paths
    → --security-opt=no-new-privileges
    → resource limits (memory, CPU, PIDs)
    → secrets mounted from secrets manager
    → internal network for data tier
    ↓
Runtime monitoring (Falco) observes syscall behavior
    ↓
Audit logs capture: who deployed what, from where, when
    ↓
Secrets rotate on a schedule without redeployment
    ↓
Vulnerability database updated → new scan → if critical CVE, alert and rebuild
```

Each arrow is a security control. Each control is independent. The question for each is not "is this overkill?" but "what does an attacker gain if this control is absent?"

---

## The Two Questions That Cut Through Everything

When evaluating any security decision, ask:

**1. What does an attacker gain if this control is absent?**  
Not "what could theoretically happen" — what is the realistic, practical gain? If the answer is "not much," the control may not be worth the operational cost. If the answer is "root on the host" or "access to the database," the control is non-negotiable.

**2. What does an attacker need to do to defeat this control?**  
If defeating it requires a kernel CVE — that's a strong control. If defeating it requires guessing a secret from `/proc/environ` — that's a weak control with a well-known bypass. Strong controls require attackers to escalate their sophistication. Weak controls only slow down attackers who don't know what they're doing.

Security is not about making your platform impenetrable. It's about making attack more expensive than reward, at every layer, simultaneously.

---

*The platform is only as secure as its weakest link. The weakest link is almost always not a misconfigured seccomp profile — it's a secret in an environment variable, an unsigned image from Docker Hub, or a developer's laptop with the Docker socket exposed over TCP without TLS.*  
*Start with the fundamentals. The fundamentals are boring because they work.*

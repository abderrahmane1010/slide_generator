# Thinking in Docker — The Architect's Mental Model

> This is not a command reference.  
> This is how you develop the intuition to *never need to Google Docker again.*  
> Every section answers one question: **why does this exist, and what is it really doing?**

---

## Part I — What a Container Actually Is

> Most people use Docker for years without ever understanding this. Once you do, everything else becomes obvious.

---

### The lie we tell beginners

We say: *"A container is a lightweight virtual machine."*

This is wrong. A VM emulates hardware. A container is just **a process with a restricted view of the world.**

That's it. When you run `docker run alpine sh`, you are running a process called `sh` on your host kernel. No hypervisor. No emulated CPU. The same kernel as your laptop. What makes it a "container" is that the kernel has been asked to *lie to that process* about what it can see.

The kernel lies using two mechanisms: **namespaces** and **cgroups**. Docker is, fundamentally, a friendly API over these two Linux primitives.

---

### Namespaces — controlling what a process can see

A namespace wraps a global system resource and makes a process believe it has its own isolated instance of it.

There are 7 namespace types. These are the ones that matter for containers:

**PID namespace**  
The container's `sh` process thinks it is PID 1. It has no idea that from the host's perspective it might be PID 47382. Inside the container, `ps aux` shows a handful of processes. On the host, the same process appears in the full process table with its real PID.

This is why `kill 1` inside a container kills the container — you just killed what *that namespace believes is PID 1*.

**Network namespace**  
Each container gets its own network stack: its own `eth0`, its own routing table, its own iptables rules, its own ports. Port 80 can be "in use" inside a container even if port 80 is already in use on the host. They're in different namespaces — they don't conflict.

When you do `docker run -p 8080:80`, Docker doesn't "forward" traffic. It creates an iptables `DNAT` rule that intercepts packets arriving at host port 8080 and rewrites their destination to the container's virtual IP on port 80. The container never sees port 8080. It only ever sees port 80.

**Mount namespace**  
The container sees its own filesystem tree. When it reads `/`, it sees the Alpine or Ubuntu filesystem from the image — not your host `/`. But this is purely a *view* — the actual bytes live on the host filesystem, presented through the union filesystem (more on this shortly).

**UTS namespace**  
Lets the container have its own hostname. Run `hostname` inside a container and you get the container ID. On the host, the hostname is unchanged.

**User namespace** *(often not enabled by default)*  
This is the most powerful and least used. It maps UIDs inside the container to different UIDs on the host. UID 0 (root) inside the container can map to UID 65534 (nobody) on the host. Even if a process escapes the container, it has no privileges.

The reason it's not default: it breaks some volume permission patterns and adds complexity. But for high-security environments, always enable it.

---

### cgroups — controlling what a process can use

Namespaces control *visibility*. cgroups (control groups) control *resource consumption*.

When you run `docker run --memory=512m --cpus=1.5`, you are writing to Linux cgroup files. Specifically, Docker writes to:

```
/sys/fs/cgroup/memory/docker/<container-id>/memory.limit_in_bytes
/sys/fs/cgroup/cpu/docker/<container-id>/cpu.cfs_quota_us
```

The kernel enforces these limits at the scheduler level. It's not Docker polling and killing things — the kernel itself refuses to allocate more memory or CPU time than the cgroup allows.

**What happens when a container hits its memory limit?**

The OOM (Out of Memory) killer activates. It doesn't warn the process. It doesn't give it time to clean up. It sends `SIGKILL`. This is why your container can appear to "crash randomly" — it ran out of memory. Check `docker inspect` and look at `OOMKilled: true`.

**The CPU quota math:**

`--cpus=1.5` translates to: in every 100ms period, this container gets 150ms of CPU time. On a 4-core machine, that's 37.5% of one core, or the equivalent of 1.5 cores if the work can be parallelized. The kernel time-slices accordingly.

---

### The union filesystem — the real magic of images

This is the piece most people never understand, and it explains *everything* about image behavior.

An image is not a filesystem. An image is a **stack of read-only filesystem layers**. When you run a container, Docker adds one **writable layer on top**. This is called the union mount.

```
┌─────────────────────────────┐
│  Container writable layer   │  ← your changes go here (ephemeral)
├─────────────────────────────┤
│  Layer 4: COPY app.py       │  ← read-only
├─────────────────────────────┤
│  Layer 3: RUN pip install   │  ← read-only
├─────────────────────────────┤
│  Layer 2: RUN apt-get       │  ← read-only
├─────────────────────────────┤
│  Layer 1: FROM python:slim  │  ← read-only
└─────────────────────────────┘
```

The default driver is **overlay2**. It works like this:

- **lowerdir**: all the read-only image layers merged together
- **upperdir**: the container's writable layer
- **merged**: the unified view the container sees

When a container reads a file, the kernel looks first in `upperdir`. If not found, it looks through the `lowerdir` layers from top to bottom.

When a container *writes* to a file that exists in a lower layer, it performs a **copy-on-write**: the kernel copies the full file up to `upperdir` first, then applies the write. This is why modifying a large file inside a container is slow and expensive — the entire file is copied before the write happens.

**The insight this gives you:**

When you do `RUN apt-get install -y curl && rm -rf /var/lib/apt/lists/*` in a single `RUN`, those temporary files never persist to a layer. But if you split it:

```dockerfile
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*
```

The apt cache is written to layer 1, frozen there forever. Layer 2 "deletes" it, but the deletion is just a **whiteout file** in overlay2 — a marker that says "pretend this file doesn't exist in the merged view." The bytes are still in the image. The image is still large. `docker history` shows both layers. `docker save` reveals the truth.

This is not a Docker quirk — it's the fundamental consequence of how union filesystems work.

---

## Part II — The Network You Never See

> Docker networking is iptables in disguise. Once you see through the abstraction, you control it completely.

---

### What actually happens when you create a Docker network

```bash
docker network create mynet
```

Docker calls the kernel to create:
1. A **virtual ethernet bridge** (`br-<id>`) — a software L2 switch on your host
2. An IP range allocated to it (e.g., `172.20.0.0/16`)
3. iptables rules to control traffic flow

When you attach a container to this network:
1. Docker creates a **veth pair** — two virtual network interfaces linked together (what enters one side exits the other)
2. One end goes into the container's network namespace (appears as `eth0`)
3. The other end is attached to the bridge on the host

Verify this yourself:
```bash
docker network create mynet
docker run -d --name test --network mynet alpine sleep 300

# On the host:
ip addr show type bridge          # you'll see br-<id>
ip link show type veth            # you'll see the veth pairs
brctl show                        # bridge table with attached interfaces
```

Every container on the same network is plugged into the same virtual switch. They can talk at L2 (MAC) and L3 (IP). Docker's embedded DNS (running at `127.0.0.11` inside every container) resolves container names to their virtual IPs.

---

### Why `-p 8080:80` is an iptables DNAT rule

When you expose a port, Docker writes a rule like this to the host's `nat` table:

```
-A DOCKER -p tcp --dport 8080 -j DNAT --to-destination 172.17.0.2:80
```

And a MASQUERADE rule so the container sees requests appear to come from within the Docker subnet.

Check it yourself:
```bash
docker run -d -p 8080:80 nginx:alpine
sudo iptables -t nat -L DOCKER -n --line-numbers
```

**The implication:**  
The container *never knows* it's exposed on port 8080. It only sees port 80. The translation happens at the host kernel level, before the packet reaches the container's network namespace. This is pure NAT.

This is also why `0.0.0.0:8080->80/tcp` in `docker ps` means: the host is listening on port 8080 on *all interfaces*, including your external network interface. If you're on a server, the port is public unless your firewall says otherwise. Docker's iptables rules bypass `ufw` and `firewalld` by inserting rules before them in the chain.

**The `--network host` trade-off:**  
With host networking, the container shares the host's network namespace. No veth. No bridge. No NAT. No iptables translation. The process just opens port 80 on the host directly. Zero overhead, but zero isolation. An attacker who controls the process controls the host network stack.

---

### Inter-container communication and the `internal` flag

By default, containers on a custom network can reach the internet through NAT. The `internal: true` flag in compose removes the iptables MASQUERADE rule — outbound traffic is blocked. The network is isolated.

```yaml
networks:
  backend:
    internal: true
```

Your database should be on an `internal` network. It has no reason to make outbound connections. If it ever tries to, that's a signal something is very wrong.

---

## Part III — The Image Is a Contract

> An image is not "your app." An image is a promise about what will be present at runtime. Design it like an API.

---

### The FROM instruction is a trust decision

Every `FROM` is a supply chain dependency. You are trusting:
- The registry (Docker Hub, GHCR, ECR)
- The maintainer
- The base OS maintainer
- Every package installed in that image

`FROM ubuntu:latest` adds several hundred packages you don't control, most of which your app will never use. Each is a potential CVE.

The progression of trust levels:
```
scratch       → only what you explicitly add. Smallest possible attack surface.
              Used for: statically compiled binaries (Go, Rust), nothing else.

distroless    → no shell, no package manager, only runtime libraries.
              Used for: Java, Python, Node apps where you want no shell access.
              An attacker who exploits your app can't run bash — there is no bash.

alpine        → musl libc, busybox, ~5MB. Has a shell and package manager.
              Risk: musl vs glibc incompatibilities. Some Python C extensions fail.

slim (Debian) → stripped Debian. Has apt, bash. Most compatible.
              Used for: when alpine causes compatibility pain.

full (Debian) → everything. Use only as a build stage, never as runtime.
```

**The rule**: your runtime image should have exactly what the process needs to run. Every extra tool is a capability an attacker gains if they compromise your container.

---

### Multi-stage is not an optimization — it's a discipline

The reason multi-stage builds matter isn't image size. It's **separation of concerns**.

The build environment contains: compilers, build tools, test frameworks, source code, credentials to fetch private dependencies.  
The runtime environment should contain: compiled artifacts, runtime libraries, nothing else.

If you ship a single-stage image with your Node.js app, you're shipping `npm`, `node_modules` devDependencies, the full npm cache, and possibly build-time environment variables. None of these belong in production.

```dockerfile
FROM node:20 AS builder          # has npm, all devDependencies
WORKDIR /build
COPY package*.json .
RUN npm ci                       # installs everything including dev deps
COPY . .
RUN npm run build                # compile TypeScript, bundle, etc.

FROM node:20-slim AS runtime     # lean runtime
WORKDIR /app
COPY --from=builder /build/dist ./dist
COPY --from=builder /build/node_modules ./node_modules  # only prod deps
# Better: re-run npm ci --omit=dev in runtime stage for clean install
USER node
CMD ["node", "dist/server.js"]
```

Ask yourself: *if an attacker gets RCE in this container, what can they do?* With the single-stage image, they can run `npm`, read source code, potentially access build credentials still in env vars. With the runtime image, they have the minimal compiled artifact and nothing else.

---

### Layer ordering is API design for the build cache

The build cache is a function: it takes a layer's parent chain + instruction as input, and returns a cache hit or miss.

**A cache miss on layer N invalidates all layers N+1, N+2, ...**

This means your Dockerfile should be ordered by **rate of change**, slowest-changing first:

```dockerfile
FROM node:20-slim               # changes: never (pin the digest)
RUN apt-get install ...         # changes: rarely
COPY package*.json .            # changes: when you add/remove dependencies
RUN npm ci                      # changes: when package.json changes
COPY . .                        # changes: every commit
RUN npm run build               # changes: every commit
```

If you put `COPY . .` before `npm ci`, every code change re-downloads all npm packages. This isn't just slow — in a team with 20 engineers running CI 50 times a day, it's a compounding tax on every build.

The build cache is shared infrastructure. Design your Dockerfile like you design a database schema: the schema of your layers determines your performance profile.

---

## Part IV — Volumes, State, and the Stateless Ideal

> The hardest architectural question in Docker: where should this data live?

---

### The fundamental tension

Containers are designed to be ephemeral and replaceable. The moment a container has state that must survive, it becomes a pet, not cattle.

This is not a Docker problem — it's a system design problem that Docker forces you to confront explicitly.

**The question to ask about every piece of data:**

1. Can I regenerate this data if the container dies? → don't persist it
2. Does this data belong to the *instance* (session state, temp files)? → tmpfs or ephemeral
3. Does this data belong to the *service* (database, uploads)? → named volume or external storage
4. Does this data belong to the *deployment* (config, secrets)? → config injection at runtime

---

### Why named volumes beat bind mounts in production

A bind mount couples your container to a specific path on a specific host. It only works if:
- The path exists
- The permissions are correct
- You're on that specific machine

A named volume is managed by Docker. It lives wherever Docker decides (`/var/lib/docker/volumes/`). You can back it up, move it, restore it, and Docker handles the mount. It's portable across docker-compose files, across restarts, across host paths.

The exception: **development**. Bind mounting your source code into a container for hot-reload is legitimate — you explicitly *want* to couple the container to your local filesystem. This is the exact pattern `compose.override.yaml` is designed for: bind mounts in development, named volumes in production.

---

### The volume is outside the image lifecycle

This is the key mental model. When you do `docker rm -v mycontainer`, the `-v` flag removes *anonymous* volumes. Named volumes survive. When you do `docker compose down`, volumes survive unless you add `-v`.

This means: **your data outlives your container**. The container is a process. The volume is the state. They're decoupled. Design around this:

- Containers should boot and discover their state from the volume
- Containers should shut down gracefully (flush, close connections, complete in-flight requests)
- Containers should be replaceable without data loss

If restarting a container causes data loss, you have a design flaw, not a Docker problem.

---

## Part V — The Process Model and Signal Handling

> This is the most overlooked topic. It causes silent data corruption in production.

---

### PID 1 is special and most apps don't know it

In a normal Linux system, PID 1 is `systemd` or `init`. Its job:
1. Reap zombie processes (call `wait()` on exited children)
2. Forward signals to children
3. Restart crashed services

In a container, *your app* is PID 1. Unless your app was written to handle these responsibilities, you have a problem.

**The zombie problem:**  
If your app forks child processes (gunicorn workers, background jobs), and those children exit, the parent must call `wait()` to clean up the process table entry. If it doesn't, those entries accumulate as zombies. Over time, you exhaust the PID namespace. The container becomes unable to spawn new processes.

Most web frameworks don't handle this. They assume they're not PID 1.

**The signal forwarding problem:**  
When you run `docker stop`, Docker sends `SIGTERM` to PID 1 and waits `--stop-timeout` seconds (default 10s). If PID 1 is a shell script that launched your app, the shell receives SIGTERM but *does not forward it to child processes by default*. After 10 seconds, Docker sends `SIGKILL`. Your app gets no warning. No graceful shutdown. No connection draining. No flushing writes.

---

### The exec form is not a style preference

```dockerfile
# Shell form — sh -c is PID 1, your app is a child
CMD ["sh", "-c", "python app.py"]

# Exec form — python is PID 1, receives signals directly
CMD ["python", "app.py"]
```

With shell form: `SIGTERM` goes to `sh`. `sh` terminates. Your app gets `SIGKILL` after the timeout. Zero graceful shutdown.

With exec form: `SIGTERM` goes to your app. Your app can handle it, drain connections, flush buffers, then exit cleanly.

This single distinction is responsible for countless production incidents where databases lost in-flight transactions because the process was killed with no warning.

---

### When to use tini or dumb-init

If your app *needs* to fork children (most don't — use threads instead), you need a minimal init system:

```dockerfile
FROM python:3.12-slim
RUN apt-get install -y tini
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "app.py"]
```

`tini` is 20KB. It does exactly two things: reap zombies and forward signals. Nothing more. It makes your app the *effective* PID 1 without the PID 1 responsibilities.

Docker has `--init` flag that uses tini automatically:
```bash
docker run --init myapp
```

But baking it into the Dockerfile is more explicit and portable.

---

## Part VI — Security as Architecture

> Security is not a checklist. It's a threat model. Ask: what can an attacker do if they compromise this container?

---

### The concentric circles of container security

Think in concentric circles. Each circle is an independent layer of defense. Defeating one circle leaves the others intact.

```
┌─────────────────────────────────────────┐
│  Host OS & kernel                       │  ← kernel exploits, seccomp
│  ┌───────────────────────────────────┐  │
│  │  Docker daemon (root)             │  │  ← daemon socket exposure
│  │  ┌─────────────────────────────┐  │  │
│  │  │  Container                  │  │  │
│  │  │  ┌─────────────────────┐   │  │  │
│  │  │  │  Process (your app) │   │  │  │
│  │  │  └─────────────────────┘   │  │  │
│  │  │  capabilities / seccomp    │  │  │
│  │  │  read-only filesystem      │  │  │
│  │  │  non-root user             │  │  │
│  │  └─────────────────────────────┘  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

**Non-root user** blocks: privilege escalation via setuid binaries, writing to system paths, binding privileged ports.

**`--cap-drop=ALL`** blocks: raw network access (`CAP_NET_RAW`), loading kernel modules (`CAP_SYS_MODULE`), changing file ownership (`CAP_CHOWN`), and 30+ other dangerous capabilities. Your web app needs none of these.

**Read-only filesystem** blocks: an attacker dropping a backdoor binary, modifying config files, creating cron jobs.

**Seccomp** blocks: specific system calls. Docker's default seccomp profile blocks ~44 of 300+ syscalls. A custom profile for your app can block 280+.

**No daemon socket mount** blocks: complete container escape. If you mount `/var/run/docker.sock` into a container, any process in that container can control the Docker daemon. It can run `docker run --privileged -v /:/host`. Game over.

---

### The secret is not an environment variable

Environment variables are visible to:
- `docker inspect` (anyone with Docker socket access)
- `/proc/<pid>/environ` (any process running as the same UID)
- Every child process spawned (children inherit env)
- Crash reports and core dumps
- Log aggregators that capture process metadata
- Any library that reads env (they all do)

The correct model: secrets are files, not env vars. They're mounted at `/run/secrets/name` from a `tmpfs` — memory-only, never written to disk, never visible in image layers, not inherited by child processes.

Read the secret once at startup. Store it in application memory. Close the file.

---

### The daemon socket is root on the host

This is the most dangerous misunderstanding in Docker:

```yaml
# This is a SECURITY HOLE
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

The Docker daemon runs as root. The socket is root-owned. Any container that mounts this socket can send any command to the daemon — including running a privileged container that mounts the host filesystem.

CI/CD agents, monitoring tools, and log shippers commonly request this mount. Evaluate every case. The alternative is the Docker API over TCP with mTLS, or rootless Docker, or tools designed to not require daemon access (Kaniko for building images, cAdvisor with read-only cgroup access).

---

## Part VII — Designing Systems, Not Containers

> The container is the unit of deployment, not the unit of architecture. How you decompose your system determines whether Docker helps or hurts.

---

### One process per container is a principle, not a rule

The principle is: **one concern per container**. Not one binary.

A container that runs `nginx` + `python app` + `crond` violates this — not because it runs multiple processes, but because these three concerns have different lifecycles, different failure modes, and different scaling needs.

If your `crond` crashes, does your web app need to restart? No. If your web app scales to 10 instances, should all 10 also run `crond`? No.

The test: can this process fail independently, scale independently, or be replaced independently? If yes — separate container.

---

### The contract between containers: environment variables vs config files vs DNS

**Environment variables** are for: simple scalar config (port numbers, feature flags, environment names). They're visible, logged, and inherited. Keep them non-sensitive.

**Config files** are for: complex structured config (nginx.conf, application.yaml). Mount them as read-only bind mounts or named volumes. Don't bake them into images — the image becomes environment-specific and loses portability.

**DNS** is for: service discovery. Your app should reference `redis` or `postgres`, not `172.20.0.3`. Docker's internal DNS resolves service names. When you scale, the DNS record updates. Your app doesn't need to know anything about IPs.

**Secrets** are for: credentials, keys, tokens. `/run/secrets`. Always.

---

### The health check is a contract, not a courtesy

A health check is how you tell the orchestrator: "this container is ready to receive traffic."

The difference between `starting` and `healthy` is the difference between routing live traffic to an app that's still warming up vs. one that's ready. `depends_on: condition: service_healthy` exploits this — it gates your API container on the database being *actually ready*, not just *started*.

Design your health endpoint carefully:
- It should check *dependencies*, not just "am I alive"
- But it shouldn't be so thorough that a slow dependency makes your container appear unhealthy
- Typically: check your DB connection, check your cache connection, return 200 if both respond

A container that returns 200 on `/health` but can't actually serve requests (DB connection pool exhausted, in-memory cache corrupted) is lying. The orchestrator will keep routing traffic to it.

---

### Immutability is a property of the image, not the container

Once you build an image with a given tag, it should never change. If you update the code, you build a new image with a new tag. The old image still exists and can be rolled back to.

This is the foundation of reliable deployments:

1. Build image → tag with git commit SHA (`myapp:a3f9c12`)
2. Run integration tests against that exact image
3. Deploy that exact image to production
4. If something goes wrong, deploy `myapp:a1b2c3` (previous SHA) — zero guess work

The `latest` tag is operationally meaningless. Two deploys 10 minutes apart can use different images. Rollback is impossible because you don't know what `latest` was pointing to before.

Treat your images like database migrations: append-only, versioned, never mutated.

---

## The Mental Models, Crystallized

When you see a container failing, think in layers:

```
Is the process receiving the signal?      → exec form, PID 1, tini
Is the filesystem writable?               → read-only + tmpfs mounts
Can the process find its dependencies?    → DNS, network, health checks
Does it have the data it expects?         → volume mount, permissions, UID
Is it resource-starved?                   → OOMKilled, CPU throttled
Can it make network connections?          → internal network, iptables rules
Is it running as the right user?          → USER, cap-drop, no-new-privileges
```

When you design a new service, think from outside in:

```
What data must survive the container?     → volume design
What can the container reach?             → network topology
What can reach the container?             → port exposure, proxies
What credentials does it need?            → secret injection
How do I know it's healthy?               → health endpoint design
How does it shut down?                    → SIGTERM handling, grace period
What happens when it crashes?             → restart policy, state recovery
```

These questions compose. The answers are your architecture.

---

*Knowing Docker means knowing Linux. The better you understand namespaces, cgroups, iptables, and overlay filesystems — the more Docker becomes transparent to you. You stop debugging Docker. You debug Linux. And Linux always has an answer.*

# Docker Hero Lab — Command-by-Command Field Training

> **Philosophy**: Every command you type here has a *why*. Read the explanation, run the command, observe the output. Repeat until it's muscle memory.  
> **Structure**: 10 progressive labs. Each builds on the previous. You'll end with a production-grade multi-service app.  
> **Time**: ~6–8 hours total. Do one lab per session.

---

## Setup Checklist

```bash
docker --version          # Engine 24+ recommended
docker compose version    # v2 plugin (not docker-compose)
docker buildx version     # BuildKit builder
```

Create your workspace:
```bash
mkdir ~/docker-hero && cd ~/docker-hero
```

---

## LAB 1 — Images: Pulling, Inspecting, Understanding

> **Goal**: Stop treating images as black boxes. Understand layers, digests, and metadata.

---

### 1.1 Pull and compare

```bash
# Pull three variants of the same app
docker pull python:3.12
docker pull python:3.12-slim
docker pull python:3.12-alpine
```

Now compare their sizes:
```bash
docker images python
```

You'll see something like:
```
REPOSITORY   TAG          IMAGE ID       SIZE
python       3.12         ...            1.02GB
python       3.12-slim    ...            130MB
python       3.12-alpine  ...            52MB
```

**Why it matters**: The base image is the largest hidden tax in your supply chain.  
`slim` = Debian with dev tools removed. `alpine` = musl libc, busybox shell. Smaller but may cause subtle compatibility issues (C extensions, glibc assumptions).

---

### 1.2 Inspect layers with history

```bash
docker history python:3.12-slim
docker history --no-trunc python:3.12-slim | head -20
```

Each line is a layer. Notice layers with `0B` size — those are metadata-only (`ENV`, `EXPOSE`, `CMD`).

---

### 1.3 Inspect image metadata

```bash
docker inspect python:3.12-slim
```

Too verbose. Extract what matters:
```bash
# What command runs by default?
docker inspect --format='{{json .Config.Cmd}}' python:3.12-slim | python3 -m json.tool

# What user does it run as?
docker inspect --format='{{.Config.User}}' python:3.12-slim

# What environment variables are set?
docker inspect --format='{{range .Config.Env}}{{println .}}{{end}}' python:3.12-slim

# What ports are exposed?
docker inspect --format='{{json .Config.ExposedPorts}}' python:3.12-slim
```

**Lesson**: Never trust documentation alone. `docker inspect` is ground truth.

---

### 1.4 Image digest — the immutable identity

```bash
# A tag is mutable. A digest is not.
docker inspect --format='{{index .RepoDigests 0}}' python:3.12-slim
```

Output: `python@sha256:e3b0c44...`  
This digest never changes. The tag `3.12-slim` can be overwritten tomorrow.

---

### 1.5 Explore the filesystem

```bash
# Run a one-shot container and explore
docker run --rm -it python:3.12-slim bash

# Inside the container:
cat /etc/os-release
ls /usr/local/lib/python3.12/
python3 -c "import sys; print(sys.path)"
exit
```

---

### 1.6 Save, export, and diff

```bash
# Save an image to a tar archive (layers intact)
docker save python:3.12-alpine -o python-alpine.tar
tar -tf python-alpine.tar | head -20

# Run a container, make a change, then diff
docker run --name inspect-demo python:3.12-alpine sh -c "echo hello > /tmp/test.txt"
docker diff inspect-demo
# A = added, C = changed, D = deleted

# Cleanup
docker rm inspect-demo
rm python-alpine.tar
```

---

**Lab 1 Recap — Commands burned in:**
```
docker pull        docker images      docker history
docker inspect     docker run --rm    docker diff
docker save        docker rm
```

---

## LAB 2 — Containers: Lifecycle Mastery

> **Goal**: Understand every state a container goes through and how to control it precisely.

---

### 2.1 Container lifecycle

```bash
# Create without starting
docker create --name lifecycle-demo alpine sleep 300
docker ps -a   # STATUS: Created

# Start it
docker start lifecycle-demo
docker ps      # STATUS: Up

# Pause (freezes cgroups — process is suspended, not stopped)
docker pause lifecycle-demo
docker ps      # STATUS: Paused

# Resume
docker unpause lifecycle-demo

# Stop (sends SIGTERM, waits 10s, then SIGKILL)
docker stop lifecycle-demo
docker ps -a   # STATUS: Exited

# Restart with a policy
docker start lifecycle-demo
docker restart --time=5 lifecycle-demo   # give 5s before SIGKILL

# Remove
docker rm lifecycle-demo
```

---

### 2.2 Run flags that matter

```bash
# -d: detached (background)
# --name: human-readable name
# --rm: auto-remove when stopped (great for one-shots)
# -it: interactive + pseudo-TTY
# -e: set env variable
# -p: port mapping (host:container)
# -v: volume mount
# --restart: restart policy

docker run -d \
  --name my-nginx \
  --restart unless-stopped \
  -p 8080:80 \
  -e NGINX_HOST=localhost \
  nginx:alpine

curl http://localhost:8080
```

---

### 2.3 Exec into running containers

```bash
# Start a shell in a running container
docker exec -it my-nginx sh

# Run a one-off command
docker exec my-nginx nginx -t          # test nginx config
docker exec my-nginx cat /etc/nginx/nginx.conf

# Run as root even if container runs as another user
docker exec -u root my-nginx id

docker stop my-nginx && docker rm my-nginx
```

---

### 2.4 Logs: everything you need to know

```bash
docker run -d --name log-demo \
  alpine sh -c "while true; do echo [$(date)] ping; sleep 1; done"

# Tail logs
docker logs log-demo

# Follow (like tail -f)
docker logs -f log-demo

# Last N lines
docker logs --tail=5 log-demo

# With timestamps
docker logs -t log-demo

# Since a time
docker logs --since=10s log-demo
docker logs --since="2024-01-01T00:00:00" log-demo

docker stop log-demo && docker rm log-demo
```

---

### 2.5 Resource constraints and live stats

```bash
# Run a CPU-hungry container, constrained
docker run -d --name cpu-demo \
  --cpus="0.5" \
  --memory="128m" \
  --memory-swap="128m" \
  alpine sh -c "while true; do :; done"

# Watch real-time stats
docker stats cpu-demo

# One-shot formatted output (great for scripts)
docker stats --no-stream --format \
  "{{.Name}}: CPU={{.CPUPerc}} MEM={{.MemUsage}}" cpu-demo

docker stop cpu-demo && docker rm cpu-demo
```

---

### 2.6 Copy files in and out

```bash
docker run -d --name copy-demo nginx:alpine

# Container → host
docker cp copy-demo:/etc/nginx/nginx.conf ./nginx.conf
cat nginx.conf

# Host → container
echo "# modified" >> nginx.conf
docker cp nginx.conf copy-demo:/etc/nginx/nginx.conf
docker exec copy-demo nginx -t    # verify it's valid

docker stop copy-demo && docker rm copy-demo
rm nginx.conf
```

---

**Lab 2 Recap:**
```
docker create    docker start     docker stop      docker restart
docker pause     docker unpause   docker rm        docker exec
docker logs      docker stats     docker cp        docker ps -a
```

---

## LAB 3 — Volumes: Persistent & Shared Data

> **Goal**: Know exactly when data survives, when it doesn't, and why.

---

### 3.1 The ephemeral container problem

```bash
# Write data to a container
docker run --name ephemeral alpine sh -c "echo 'important data' > /data/file.txt"
# ERROR: /data doesn't exist yet. Let's fix:
docker run --name ephemeral alpine sh -c "mkdir -p /data && echo 'important data' > /data/file.txt"
docker exec ephemeral cat /data/file.txt   # works

# Remove and recreate
docker rm ephemeral
docker run --name ephemeral alpine cat /data/file.txt
# Error: no such file — data is GONE
docker rm ephemeral
```

**This is why volumes exist.**

---

### 3.2 Named volumes

```bash
# Create a named volume
docker volume create mydata

# Inspect it
docker volume inspect mydata
# Location on host: /var/lib/docker/volumes/mydata/_data

# Mount it
docker run --name vol-demo -v mydata:/data alpine sh -c \
  "echo 'persistent!' > /data/file.txt"

# Verify persistence after container is gone
docker rm vol-demo
docker run --rm -v mydata:/data alpine cat /data/file.txt
# Output: persistent!
```

---

### 3.3 Bind mounts (for development)

```bash
mkdir ~/docker-hero/webapp && echo "<h1>Hello from host</h1>" > ~/docker-hero/webapp/index.html

# Mount host directory into nginx
docker run -d --name bindmount-demo \
  -p 8080:80 \
  -v ~/docker-hero/webapp:/usr/share/nginx/html:ro \
  nginx:alpine

curl http://localhost:8080

# Edit on host, see immediately in container (no rebuild)
echo "<h1>Hot reload!</h1>" > ~/docker-hero/webapp/index.html
curl http://localhost:8080   # updated instantly

docker stop bindmount-demo && docker rm bindmount-demo
```

`:ro` = read-only inside container. Never mount host directories read-write in production.

---

### 3.4 tmpfs mounts (in-memory, never written to disk)

```bash
# Useful for secrets or temp processing — data never hits the filesystem
docker run --rm \
  --tmpfs /run:rw,noexec,nosuid,size=100m \
  alpine df -h /run
```

---

### 3.5 Volume backup and restore

```bash
# Backup a volume to a tar
docker run --rm \
  -v mydata:/source:ro \
  -v $(pwd):/backup \
  alpine tar czf /backup/mydata-backup.tar.gz -C /source .

ls -lh mydata-backup.tar.gz

# Restore to a new volume
docker volume create mydata-restored
docker run --rm \
  -v mydata-restored:/target \
  -v $(pwd):/backup \
  alpine tar xzf /backup/mydata-backup.tar.gz -C /target

docker run --rm -v mydata-restored:/data alpine cat /data/file.txt
```

---

### 3.6 Cleanup

```bash
# List all volumes
docker volume ls

# Remove unused volumes (not mounted by any container)
docker volume prune

# Remove specific
docker volume rm mydata mydata-restored
rm mydata-backup.tar.gz
```

---

**Lab 3 Recap:**
```
docker volume create    docker volume inspect   docker volume ls
docker volume prune     docker volume rm        -v flag (named vs bind vs tmpfs)
```

---

## LAB 4 — Networks: Container Communication

> **Goal**: Understand how containers talk to each other and to the outside world.

---

### 4.1 Default bridge vs custom bridge

```bash
# Default bridge — containers can't reach each other by name
docker run -d --name c1 alpine sleep 300
docker run -d --name c2 alpine sleep 300

docker exec c2 ping -c2 c1      # FAILS — no DNS on default bridge
docker exec c2 ping -c2 172.17.0.2  # works only if you know the IP

docker stop c1 c2 && docker rm c1 c2
```

```bash
# Custom bridge — automatic DNS by container name
docker network create mynet

docker run -d --name c1 --network mynet alpine sleep 300
docker run -d --name c2 --network mynet alpine sleep 300

docker exec c2 ping -c2 c1    # WORKS — Docker DNS resolves "c1"
docker exec c2 nslookup c1    # DNS record confirmed

docker stop c1 c2 && docker rm c1 c2
docker network rm mynet
```

**Rule**: Always use custom networks in production. Never the default bridge.

---

### 4.2 Network isolation

```bash
docker network create frontend
docker network create backend

docker run -d --name web   --network frontend nginx:alpine
docker run -d --name api   --network backend  alpine sleep 300
docker run -d --name proxy --network frontend nginx:alpine

# web and proxy can talk (same network)
docker exec proxy ping -c2 web    # ✅

# api is isolated
docker exec proxy ping -c2 api    # ❌ — different network

# Connect api to frontend too (multi-network container)
docker network connect frontend api
docker exec proxy ping -c2 api    # ✅ now

docker stop web api proxy && docker rm web api proxy
docker network rm frontend backend
```

---

### 4.3 Port mapping deep dive

```bash
# Expose on all interfaces (default)
docker run -d --name p1 -p 8080:80 nginx:alpine

# Expose on loopback only (more secure)
docker run -d --name p2 -p 127.0.0.1:8081:80 nginx:alpine

# Random host port (Docker picks)
docker run -d --name p3 -p 80 nginx:alpine
docker port p3   # see which port was assigned

# List port mappings
docker inspect --format='{{json .NetworkSettings.Ports}}' p1 | python3 -m json.tool

docker stop p1 p2 p3 && docker rm p1 p2 p3
```

---

### 4.4 Inspect network internals

```bash
docker network create labnet
docker run -d --name netlab --network labnet alpine sleep 300

docker network inspect labnet

# See the container's network namespace
docker exec netlab ip addr
docker exec netlab ip route
docker exec netlab cat /etc/resolv.conf   # Docker's internal DNS: 127.0.0.11

docker stop netlab && docker rm netlab
docker network rm labnet
```

---

### 4.5 Host network (no NAT, maximum performance)

```bash
# Linux only — container shares the host network stack directly
docker run --rm --network host alpine ip addr
# You'll see the host's own network interfaces
```

Use for: high-throughput services, UDP, network monitoring tools.  
Avoid for: anything multi-tenant or exposed to the internet.

---

**Lab 4 Recap:**
```
docker network create    docker network inspect   docker network rm
docker network connect   docker network ls        docker port
```

---

## LAB 5 — Dockerfile Mastery: From Naive to Expert

> **Goal**: Write Dockerfiles that are fast to build, small in size, and safe to run.

```bash
mkdir ~/docker-hero/lab5 && cd ~/docker-hero/lab5
```

---

### 5.1 Naive Dockerfile (baseline)

```bash
cat > app.py << 'EOF'
from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return {"status": "ok", "message": "Hello from Docker Hero Lab"}

@app.route("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
EOF

cat > requirements.txt << 'EOF'
flask==3.0.3
gunicorn==22.0.0
EOF
```

```dockerfile
# Dockerfile.v1 — NAIVE (don't ship this)
cat > Dockerfile.v1 << 'EOF'
FROM python:3.12
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
EOF
```

```bash
docker build -f Dockerfile.v1 -t myapp:v1 .
docker images myapp:v1    # ~1GB+ image
```

**Problems**: 1GB image, runs as root, no healthcheck, dev server, all files copied.

---

### 5.2 Better — slim + dependency caching

```dockerfile
cat > Dockerfile.v2 << 'EOF'
FROM python:3.12-slim

WORKDIR /app

# Dependencies first — cached unless requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Source code last — cache busted only on code change
COPY app.py .

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers=2", "app:app"]
EOF
```

```bash
docker build -f Dockerfile.v2 -t myapp:v2 .
docker images myapp   # ~180MB

# Test cache: change app.py and rebuild — pip install is instant
echo "# comment" >> app.py
docker build -f Dockerfile.v2 -t myapp:v2 .
# "CACHED" on the pip install step
git checkout app.py 2>/dev/null || sed -i '$ d' app.py
```

---

### 5.3 Expert — non-root, healthcheck, signal handling

```dockerfile
cat > Dockerfile.v3 << 'EOF'
FROM python:3.12-slim

# System deps as root, then drop privileges
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1001 app && \
    useradd --uid 1001 --gid app --shell /bin/bash --create-home app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app app.py .

USER app

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# exec form — signals go directly to gunicorn, not a shell
ENTRYPOINT ["gunicorn"]
CMD ["--bind", "0.0.0.0:5000", "--workers=2", "--access-logfile", "-", "app:app"]
EOF
```

```bash
docker build -f Dockerfile.v3 -t myapp:v3 .
docker run -d --name v3-test -p 5000:5000 myapp:v3

# Wait for healthcheck
sleep 15
docker ps   # should show "(healthy)"
docker inspect --format='{{.State.Health.Status}}' v3-test

curl http://localhost:5000
curl http://localhost:5000/health

# Verify non-root
docker exec v3-test whoami   # app

docker stop v3-test && docker rm v3-test
```

---

### 5.4 Expert — multi-stage build

```dockerfile
cat > Dockerfile.v4 << 'EOF'
# Stage 1: install dependencies (heavy, not shipped)
FROM python:3.12-slim AS deps
WORKDIR /install
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: lean runtime
FROM python:3.12-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends curl \
  && rm -rf /var/lib/apt/lists/* \
  && groupadd --gid 1001 app \
  && useradd --uid 1001 --gid app --shell /bin/bash --create-home app

# Copy only installed packages from the deps stage
COPY --from=deps /install /usr/local

WORKDIR /app
COPY --chown=app:app app.py .
USER app

EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

ENTRYPOINT ["gunicorn"]
CMD ["--bind", "0.0.0.0:5000", "--workers=2", "--access-logfile", "-", "app:app"]
EOF
```

```bash
docker build -f Dockerfile.v4 -t myapp:v4 .
docker images myapp

# Compare all versions
docker images myapp --format "table {{.Tag}}\t{{.Size}}"
```

---

### 5.5 Lint your Dockerfiles

```bash
docker run --rm -i hadolint/hadolint < Dockerfile.v1   # lots of warnings
docker run --rm -i hadolint/hadolint < Dockerfile.v4   # clean
```

---

### 5.6 Build arguments for flexibility

```dockerfile
cat > Dockerfile.v5 << 'EOF'
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

ARG APP_ENV=production
ARG APP_VERSION=0.0.1

ENV APP_ENV=${APP_ENV} \
    APP_VERSION=${APP_VERSION} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ... rest of Dockerfile
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .

LABEL org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.environment="${APP_ENV}"

CMD ["python", "app.py"]
EOF
```

```bash
docker build -f Dockerfile.v5 \
  --build-arg PYTHON_VERSION=3.12 \
  --build-arg APP_VERSION=1.2.3 \
  --build-arg APP_ENV=staging \
  -t myapp:v5 .

docker inspect --format='{{range .Config.Labels}}{{println .}}{{end}}' myapp:v5
docker inspect --format='{{range .Config.Env}}{{println .}}{{end}}' myapp:v5
```

```bash
cd ~/docker-hero
```

---

**Lab 5 Recap — Dockerfile checklist burned in:**
- Dependency layer before source layer
- Non-root user
- `--no-cache-dir` for pip
- `HEALTHCHECK` defined
- `exec` form for `ENTRYPOINT`
- Multi-stage for compiled or heavy-dep apps
- `hadolint` before committing

---

## LAB 6 — Docker Compose: Multi-Service Orchestration

> **Goal**: Wire multiple services together, manage dependencies, secrets, and overrides.

```bash
mkdir ~/docker-hero/lab6 && cd ~/docker-hero/lab6
```

---

### 6.1 The project: Flask API + Redis + Nginx

```bash
# Copy app from lab5
cp ~/docker-hero/lab5/requirements.txt .
cp ~/docker-hero/lab5/app.py .

# Extend app.py to use Redis
cat > app.py << 'EOF'
import os
import redis
from flask import Flask, jsonify

app = Flask(__name__)
r = redis.Redis(
    host=os.environ.get("REDIS_HOST", "redis"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    decode_responses=True
)

@app.route("/")
def hello():
    count = r.incr("hits")
    return jsonify({"hits": count, "message": "Docker Hero!"})

@app.route("/health")
def health():
    try:
        r.ping()
        return jsonify({"status": "healthy", "redis": "ok"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
EOF

# Update requirements
cat > requirements.txt << 'EOF'
flask==3.0.3
gunicorn==22.0.0
redis==5.0.7
EOF
```

---

### 6.2 Dockerfile for the API

```dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl \
  && rm -rf /var/lib/apt/lists/* \
  && groupadd --gid 1001 app \
  && useradd --uid 1001 --gid app --create-home app

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=app:app app.py .
USER app
EXPOSE 5000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

ENTRYPOINT ["gunicorn"]
CMD ["--bind", "0.0.0.0:5000", "--workers=2", "--access-logfile", "-", "app:app"]
EOF
```

---

### 6.3 Nginx reverse proxy config

```bash
mkdir nginx
cat > nginx/nginx.conf << 'EOF'
upstream api {
    server api:5000;
}

server {
    listen 80;

    location / {
        proxy_pass         http://api;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 60s;
    }

    location /nginx-health {
        return 200 "ok\n";
        add_header Content-Type text/plain;
    }
}
EOF
```

---

### 6.4 Base compose file

```yaml
cat > compose.yaml << 'EOF'
services:

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - backend
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 5s
    command: redis-server --appendonly yes --maxmemory 128mb --maxmemory-policy allkeys-lru

  api:
    build: .
    restart: unless-stopped
    environment:
      REDIS_HOST: redis
      REDIS_PORT: "6379"
    networks:
      - backend
      - frontend
    depends_on:
      redis:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: "1"
          memory: 256M

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "8080:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    networks:
      - frontend
    depends_on:
      api:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/nginx-health"]
      interval: 15s
      timeout: 5s
      retries: 3

networks:
  frontend:
  backend:

volumes:
  redis_data:
EOF
```

---

### 6.5 Run it

```bash
# Build and start all services
docker compose up --build -d

# Watch all logs simultaneously
docker compose logs -f

# Watch per service
docker compose logs -f api
docker compose logs -f redis

# Service status
docker compose ps

# Health status
docker inspect lab6-api-1 --format='{{.State.Health.Status}}'
```

```bash
# Test the app
curl http://localhost:8080        # hit counter
curl http://localhost:8080        # increments
curl http://localhost:8080/health # health check

# Hit it 10 times
for i in $(seq 1 10); do curl -s http://localhost:8080 | python3 -m json.tool; done
```

---

### 6.6 Compose overrides (environment-specific config)

```yaml
# compose.override.yaml — auto-loaded in development, NOT in production
cat > compose.override.yaml << 'EOF'
services:
  api:
    build:
      context: .
      target: runtime       # stop at this stage in multi-stage builds
    volumes:
      - ./app.py:/app/app.py   # hot reload in dev
    environment:
      FLASK_DEBUG: "1"
    command: ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5000", "--reload"]
EOF
```

```bash
# Dev mode (uses compose.yaml + compose.override.yaml automatically)
docker compose up --build

# Production mode (explicit, no override)
docker compose -f compose.yaml up --build -d
```

---

### 6.7 Scaling services

```bash
# Scale the API to 3 instances (nginx upstream will round-robin)
docker compose up --scale api=3 -d
docker compose ps

# Each instance is separate — but all connect to the same redis
curl http://localhost:8080   # any of the 3 instances responds
```

---

### 6.8 Compose lifecycle commands

```bash
# Stop without removing (preserves volumes)
docker compose stop

# Start again (no rebuild)
docker compose start

# Rebuild and recreate only changed services
docker compose up --build -d

# Teardown everything including volumes (DESTRUCTIVE)
docker compose down -v

# Execute in a specific service
docker compose exec redis redis-cli info memory
docker compose exec api python3 -c "import flask; print(flask.__version__)"

# Run a one-off command (new container, then removed)
docker compose run --rm api python3 -c "print('one-off task done')"
```

---

```bash
# Cleanup
docker compose down -v
cd ~/docker-hero
```

---

**Lab 6 Recap:**
```
docker compose up --build -d    docker compose logs -f
docker compose ps               docker compose exec
docker compose run --rm         docker compose down -v
docker compose stop/start       docker compose up --scale
depends_on with condition: service_healthy
compose.override.yaml pattern
```

---

## LAB 7 — BuildKit Advanced: Cache, Secrets, Multi-Arch

> **Goal**: Master the modern build engine. Dramatically faster CI builds.

```bash
mkdir ~/docker-hero/lab7 && cd ~/docker-hero/lab7
cp ~/docker-hero/lab6/requirements.txt .
cp ~/docker-hero/lab6/app.py .
```

---

### 7.1 Enable BuildKit and inspect build output

```bash
# BuildKit should already be active in modern Docker. Verify:
docker buildx ls

# Create a dedicated builder (enables all features)
docker buildx create --name herobuilder --use --bootstrap
docker buildx inspect herobuilder
```

---

### 7.2 Cache mounts — persistent package cache

Without cache mount: pip downloads packages every single build.  
With cache mount: packages cached on disk, reused across builds.

```dockerfile
cat > Dockerfile << 'EOF'
# syntax=docker/dockerfile:1
FROM python:3.12-slim

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    pip install -r requirements.txt

WORKDIR /app
COPY app.py .

CMD ["python", "app.py"]
EOF
```

```bash
# First build — downloads packages
time docker buildx build -t lab7:cache-demo .

# Second build — instant (packages cached)
touch app.py   # bust code layer only
time docker buildx build -t lab7:cache-demo .
```

---

### 7.3 Build secrets — no trace in image history

```bash
# Simulate a private token
echo "super_secret_token_123" > .mysecret

cat > Dockerfile.secret << 'EOF'
# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Secret is mounted at /run/secrets/mytoken — NEVER baked into the layer
RUN --mount=type=secret,id=mytoken \
    TOKEN=$(cat /run/secrets/mytoken) && \
    echo "Using token: ${TOKEN:0:5}..." && \
    echo "Done with token — it's gone now"

WORKDIR /app
COPY app.py .
CMD ["python", "app.py"]
EOF
```

```bash
docker buildx build \
  -f Dockerfile.secret \
  --secret id=mytoken,src=.mysecret \
  -t lab7:secret-demo .

# Verify: secret does NOT appear in image history
docker history lab7:secret-demo --no-trunc | grep -i token   # nothing
docker history lab7:secret-demo --no-trunc | grep -i secret  # nothing

rm .mysecret
```

---

### 7.4 Multi-architecture build

```bash
# Build for amd64 AND arm64 simultaneously
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t lab7:multiarch \
  --load .   # --push to push to registry

# Inspect the manifest
docker buildx imagetools inspect lab7:multiarch 2>/dev/null || \
  echo "Note: --load only loads for current platform. Use --push for full multi-arch manifest."
```

```bash
# Use TARGETARCH in Dockerfile for arch-specific downloads
cat > Dockerfile.multiarch << 'EOF'
# syntax=docker/dockerfile:1
FROM alpine:3.19

ARG TARGETARCH
ARG TARGETOS

RUN echo "Building for ${TARGETOS}/${TARGETARCH}"

# Example: download arch-specific binary
RUN case "${TARGETARCH}" in \
    "amd64") ARCH="x86_64" ;; \
    "arm64") ARCH="aarch64" ;; \
    *) echo "Unsupported: ${TARGETARCH}" && exit 1 ;; \
  esac && \
  echo "Would download tool-${ARCH}" 

CMD ["echo", "multiarch works"]
EOF
```

```bash
docker buildx build \
  -f Dockerfile.multiarch \
  --platform linux/amd64,linux/arm64 \
  -t lab7:multiarch-demo \
  --load .
```

---

### 7.5 Build performance report

```bash
# Verbose build output with timing per step
docker buildx build --progress=plain -t lab7:verbose . 2>&1 | grep -E "^#[0-9]"

# Build with detailed output to understand cache hits
BUILDKIT_PROGRESS=plain docker buildx build -t lab7:verbose . 2>&1
```

---

### 7.6 dive — analyze your images

```bash
# Install dive
docker run --rm -it \
  -v /var/run/docker.sock:/var/run/docker.sock \
  wagoodman/dive:latest lab7:cache-demo
```

Navigation inside dive: `Tab` to switch panels, arrow keys to navigate layers, `Ctrl+U` to show changed files.

```bash
# CI mode — fail if efficiency < 95%
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e CI=true \
  wagoodman/dive:latest lab7:cache-demo

cd ~/docker-hero
```

---

## LAB 8 — Security Hardening

> **Goal**: Apply defense-in-depth. Each layer of security is independent.

```bash
mkdir ~/docker-hero/lab8 && cd ~/docker-hero/lab8
```

---

### 8.1 Scan for vulnerabilities with docker scout

```bash
# Pull a deliberately old image to see CVEs
docker pull python:3.10

docker scout cves python:3.10 --only-severity critical,high 2>/dev/null || \
  docker scout quickview python:3.10

# Compare with latest
docker scout compare python:3.10 --to python:3.12
```

---

### 8.2 Capability management

```bash
# Default: container has ~14 capabilities
docker run --rm alpine sh -c "cat /proc/self/status | grep CapEff"

# Drop ALL capabilities, add back only what's needed
docker run --rm --cap-drop=ALL --cap-add=NET_BIND_SERVICE nginx:alpine \
  sh -c "cat /proc/self/status | grep CapEff"

# What capabilities does your app actually need?
# For most web apps: NONE. Test it:
docker run --rm --cap-drop=ALL python:3.12-slim python3 -c "print('still works')"
```

---

### 8.3 Read-only filesystem

```bash
# Force read-only root — write attempts will fail loudly (not silently)
docker run --rm --read-only \
  --tmpfs /tmp \
  --tmpfs /var/run \
  python:3.12-slim python3 -c "
import tempfile, os
# This works — writes to tmpfs
with tempfile.NamedTemporaryFile(dir='/tmp') as f:
    f.write(b'test')
print('tmpfs write: ok')

# This fails — root filesystem is read-only
try:
    open('/etc/evil', 'w').write('hack')
except IOError as e:
    print(f'root write: blocked ({e})')
"
```

---

### 8.4 No new privileges

```bash
# Prevents setuid binaries from escalating privileges
docker run --rm --security-opt=no-new-privileges alpine id
```

---

### 8.5 User namespace remapping

```bash
# Even root inside a container shouldn't be root on the host
# Check your daemon config:
docker info | grep "Security Options" -A5

# To enable: add to /etc/docker/daemon.json
# { "userns-remap": "default" }
# Then restart Docker. Creates a subordinate UID/GID mapping.
```

---

### 8.6 Secrets in compose (no env vars for sensitive data)

```bash
mkdir secrets
echo "postgres_password_here" > secrets/db_password.txt
echo "redis_password_here" > secrets/redis_password.txt

cat > compose.yaml << 'EOF'
services:
  app:
    image: python:3.12-slim
    command: sh -c "cat /run/secrets/db_password && echo 'secret read ok'"
    secrets:
      - db_password
      - redis_password

secrets:
  db_password:
    file: ./secrets/db_password.txt
  redis_password:
    file: ./secrets/redis_password.txt
EOF
```

```bash
docker compose run --rm app

# Verify: secret not in env, not in inspect output
docker compose run -d --name secrettest app sleep 300 2>/dev/null || true
docker inspect $(docker ps -qf "name=secrettest") --format='{{json .Config.Env}}' 2>/dev/null
# db_password is NOT there — it's mounted at /run/secrets/

docker compose down
rm -rf secrets compose.yaml
cd ~/docker-hero
```

---

### 8.7 Security hardening checklist

```bash
cat << 'EOF'
Security Checklist:
✅ Non-root user (USER instruction)
✅ --cap-drop=ALL + explicit --cap-add
✅ --read-only + --tmpfs for writeable paths
✅ --security-opt=no-new-privileges
✅ Secrets via /run/secrets, not ENV
✅ Pinned base image digest
✅ Vulnerability scan in CI (trivy/scout)
✅ No sensitive build args (they appear in docker history)
✅ .dockerignore excludes .env, .git, credentials
✅ Image signed with cosign (production)
EOF
```

---

## LAB 9 — Production Patterns

> **Goal**: Logging, monitoring, health, rolling updates, and CI/CD integration.

```bash
mkdir ~/docker-hero/lab9 && cd ~/docker-hero/lab9
```

---

### 9.1 Structured logging stack (Loki + Grafana)

```yaml
cat > compose.yaml << 'EOF'
services:
  app:
    image: python:3.12-slim
    command: python3 -c "
import time, json, random, sys
while True:
    level = random.choice(['INFO','INFO','INFO','WARN','ERROR'])
    print(json.dumps({
        'level': level,
        'service': 'demo-app',
        'message': f'Request processed in {random.randint(10,500)}ms',
        'request_id': f'req-{random.randint(1000,9999)}'
    }), flush=True)
    time.sleep(0.5)
"
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
        compress: "true"
    labels:
      app: demo
      env: lab

  logwatcher:
    image: alpine
    command: sh -c "while true; do echo '[logwatcher] alive'; sleep 5; done"
EOF
```

```bash
docker compose up -d

# Structured log consumption
docker compose logs app | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        parts = line.split(' ', 3)
        if len(parts) >= 4:
            data = json.loads(parts[3])
            if data.get('level') == 'ERROR':
                print(f'🔴 ERROR: {data[\"message\"]}')
    except:
        pass
"

docker compose down
```

---

### 9.2 Healthcheck patterns

```bash
cat > Dockerfile << 'EOF'
FROM python:3.12-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python3 -c "
import http.server
" 

# Pattern 1: HTTP endpoint
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -fsS http://localhost:8000/ > /dev/null || exit 1

# Pattern 2: custom script (put in /healthcheck.sh)
# HEALTHCHECK CMD /healthcheck.sh

CMD ["python3", "-m", "http.server", "8000"]
EOF

docker build -t lab9:healthcheck .
docker run -d --name hc-demo lab9:healthcheck

# Watch health status change over time
watch -n2 "docker inspect hc-demo --format='Status: {{.State.Health.Status}} | Failing: {{.State.Health.FailingStreak}}'"
# Ctrl+C when you see "healthy"

docker stop hc-demo && docker rm hc-demo
```

---

### 9.3 Container monitoring with stats

```bash
# Start several containers
docker run -d --name svc-api   --memory=128m python:3.12-slim python3 -m http.server 8001
docker run -d --name svc-cache --memory=64m  redis:alpine
docker run -d --name svc-proxy --memory=32m  nginx:alpine

# Rich stats table
docker stats --format \
  "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.PIDs}}"

# One-shot for scripting/alerting
docker stats --no-stream --format \
  "{{.Name}},{{.CPUPerc}},{{.MemUsage}}" | tee metrics.csv

cat metrics.csv

docker stop svc-api svc-cache svc-proxy
docker rm svc-api svc-cache svc-proxy
```

---

### 9.4 Cleanup automation

```bash
# See what's consuming disk
docker system df

# Granular view
docker system df -v

# What would be removed (dry run via grep)
docker ps -a --filter "status=exited" --format "{{.Names}}"
docker images -f "dangling=true"

# Targeted cleanup
docker container prune --force --filter "until=24h"
docker image prune --force --filter "until=168h"  # older than 1 week
docker volume prune --force
docker network prune --force

# Nuclear option
docker system prune -af --volumes
```

---

### 9.5 Simulate a rolling update

```bash
# Start v1
docker run -d --name app-v1 -p 8080:80 nginx:alpine
curl http://localhost:8080 > /dev/null && echo "v1 is live"

# Deploy v2 on different port first
docker run -d --name app-v2 -p 8081:80 nginx:1.25-alpine
curl http://localhost:8081 > /dev/null && echo "v2 ready"

# Switch traffic (in production: update load balancer)
docker stop app-v1

# Zero-downtime window: keep v1 around for rollback
curl http://localhost:8081 > /dev/null && echo "traffic now on v2"

# After confidence: remove v1
docker rm app-v1
docker stop app-v2 && docker rm app-v2
```

```bash
cd ~/docker-hero
```

---

## LAB 10 — Capstone: Full Production Stack

> **Goal**: Everything together. Build, tag, scan, run with all security and operational patterns.

```bash
mkdir ~/docker-hero/lab10 && cd ~/docker-hero/lab10
```

---

### 10.1 Project structure

```bash
mkdir -p app nginx monitoring

cat > app/requirements.txt << 'EOF'
flask==3.0.3
gunicorn==22.0.0
redis==5.0.7
prometheus-client==0.20.0
EOF

cat > app/app.py << 'EOF'
import os, time, redis
from flask import Flask, jsonify
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

r = redis.Redis(host=os.environ.get("REDIS_HOST", "redis"), decode_responses=True)

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP request latency")

@app.before_request
def start_timer():
    from flask import g
    g.start = time.time()

@app.after_request
def record_metrics(response):
    from flask import g, request
    latency = time.time() - g.start
    REQUEST_COUNT.labels(method=request.method, endpoint=request.path, status=response.status_code).inc()
    REQUEST_LATENCY.observe(latency)
    return response

@app.route("/")
def index():
    hits = r.incr("hits")
    return jsonify({"hits": int(hits), "version": os.environ.get("APP_VERSION", "dev")})

@app.route("/health")
def health():
    try:
        r.ping()
        return jsonify({"status": "healthy"})
    except:
        return jsonify({"status": "unhealthy"}), 503

@app.route("/metrics")
def metrics():
    from flask import Response
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
EOF

cat > app/Dockerfile << 'EOF'
# syntax=docker/dockerfile:1
FROM python:3.12-slim AS deps
WORKDIR /install
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefix=/install -r requirements.txt

FROM python:3.12-slim AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends curl \
  && rm -rf /var/lib/apt/lists/* \
  && groupadd --gid 1001 app \
  && useradd --uid 1001 --gid app --create-home app
COPY --from=deps /install /usr/local
WORKDIR /app
COPY --chown=app:app app.py .
USER app
EXPOSE 5000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1
ENTRYPOINT ["gunicorn"]
CMD ["--bind", "0.0.0.0:5000", "--workers=2", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
EOF
```

---

### 10.2 Nginx config

```bash
cat > nginx/default.conf << 'EOF'
upstream api {
    server api:5000;
    keepalive 16;
}
server {
    listen 80;
    access_log /var/log/nginx/access.log combined;

    location / {
        proxy_pass         http://api;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header   Connection "";
    }

    location /health { return 200 "ok\n"; add_header Content-Type text/plain; }
}
EOF
```

---

### 10.3 Full compose stack

```yaml
cat > compose.yaml << 'EOF'
services:

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 64mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - backend
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  api:
    build:
      context: ./app
      target: runtime
    restart: unless-stopped
    environment:
      REDIS_HOST: redis
      APP_VERSION: "1.0.0"
    secrets:
      - app_secret
    networks:
      - backend
      - frontend
    depends_on:
      redis:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 256M
        reservations:
          memory: 128M
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
        compress: "true"

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "8080:80"
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
    networks:
      - frontend
    depends_on:
      api:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost/health"]
      interval: 15s
      timeout: 5s
      retries: 3

secrets:
  app_secret:
    file: ./app_secret.txt

networks:
  frontend:
  backend:
    internal: true   # backend network has no external connectivity

volumes:
  redis_data:
EOF
```

---

### 10.4 Launch and validate

```bash
echo "my_production_secret_$(openssl rand -hex 8)" > app_secret.txt

# Build with BuildKit
DOCKER_BUILDKIT=1 docker compose up --build -d

# Watch everything come up
docker compose ps

# Wait for healthy
sleep 25
docker compose ps

# Run tests
for i in $(seq 1 5); do
  curl -s http://localhost:8080/ | python3 -m json.tool
done

# Health check
curl http://localhost:8080/health

# Metrics
curl http://localhost:8080/metrics | grep http_requests_total

# Resource usage
docker stats --no-stream
```

---

### 10.5 Final inspection — you've built this

```bash
# Image size
docker images lab10-api

# Layers
docker history lab10-api --format "table {{.CreatedBy}}\t{{.Size}}" | head -10

# Security: user
docker compose exec api whoami   # app (non-root)

# Security: secret access
docker compose exec api cat /run/secrets/app_secret

# Security: no secret in env
docker compose exec api env | grep -i secret || echo "✅ No secret in env"

# Disk usage
docker system df

# Full teardown
docker compose down -v
rm app_secret.txt
```

---

## Quick Reference Card

> Print this. Put it on your wall.

```
IMAGE MANAGEMENT
─────────────────────────────────────────────────────
docker pull <image>                  Pull from registry
docker images                        List local images
docker history <image>               Show layers
docker inspect <image>               Full metadata
docker rmi <image>                   Remove image
docker system df -v                  Disk usage breakdown
docker image prune -af               Remove dangling/unused

BUILD
─────────────────────────────────────────────────────
docker build -t name:tag .           Build image
docker build -f Dockerfile.prod .    Use specific Dockerfile
docker build --no-cache .            Force full rebuild
docker build --build-arg KEY=val .   Pass build argument
docker buildx build --platform ...   Multi-arch build
docker buildx bake                   Build from HCL definition

CONTAINER LIFECYCLE
─────────────────────────────────────────────────────
docker run -d --name x image         Start detached
docker run --rm -it image bash       Interactive one-shot
docker start / stop / restart x      Control lifecycle
docker pause / unpause x             Freeze/resume
docker rm x                          Remove (must be stopped)
docker rm -f x                       Force remove running

INSPECTION & DEBUGGING
─────────────────────────────────────────────────────
docker ps                            Running containers
docker ps -a                         All containers
docker logs -f --tail=50 x          Follow logs
docker exec -it x bash               Shell in container
docker exec -u root x command        Run as root
docker stats                         Live resource usage
docker stats --no-stream             One-shot metrics
docker inspect x                     Full container metadata
docker cp x:/path ./local            Copy from container
docker port x                        Show port mappings
docker diff x                        Filesystem changes

NETWORKS
─────────────────────────────────────────────────────
docker network create mynet          Create custom bridge
docker network connect mynet x       Attach container
docker network inspect mynet         Show network details
docker network ls                    List networks
docker network rm mynet              Remove network

VOLUMES
─────────────────────────────────────────────────────
docker volume create vol             Create named volume
docker volume inspect vol            Details + mount path
docker volume ls                     List volumes
docker volume prune                  Remove unused
docker volume rm vol                 Remove specific

COMPOSE
─────────────────────────────────────────────────────
docker compose up --build -d         Build and start
docker compose up --scale svc=3      Scale service
docker compose logs -f svc           Follow service logs
docker compose exec svc cmd          Run in service
docker compose run --rm svc cmd      One-off task
docker compose ps                    Service status
docker compose stop / start          Stop/start (keep data)
docker compose down -v               Destroy all + volumes

CLEANUP
─────────────────────────────────────────────────────
docker container prune               Remove stopped
docker image prune -a                Remove unused images
docker volume prune                  Remove unused volumes
docker network prune                 Remove unused networks
docker system prune -af --volumes    FULL CLEAN
```

---

## What's Next

| Topic | Tool / Path |
|-------|-------------|
| Orchestration | Kubernetes, Docker Swarm |
| Service mesh | Istio, Linkerd |
| GitOps CD | ArgoCD, Flux |
| Image signing | cosign + Sigstore |
| Runtime security | Falco (syscall monitoring) |
| Immutable infra | Packer + custom AMIs |
| eBPF observability | Cilium, Pixie |

---

*You've run 200+ commands. You've built, broken, and fixed a production stack.*  
*That's not a tutorial — that's a job.*

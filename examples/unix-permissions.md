# Unix File Permissions

## The permission string decoded

```
drwxr-xr-x  2  alice  staff  4096  Jun 9 10:00  mydir
─┬──┬──┬──  ─  ─────  ─────
 │  │  │  └─ others  (o)
 │  │  └──── group   (g)
 │  └──────── owner  (u)
 └─────────── file type
```

**File type** — first character:

| char | meaning |
|------|---------|
| `-`  | regular file |
| `d`  | directory |
| `l`  | symbolic link |
| `b` / `c` | block / character device |

---

## The three permission bits

| bit | on file | on directory |
|-----|---------|--------------|
| `r` (4) | read contents | list (`ls`) |
| `w` (2) | modify / delete | create, rename, delete entries |
| `x` (1) | execute | traverse (`cd`, path lookup) |
| `-` (0) | denied | denied |

> **Key subtlety — directories:**  
> `r` without `x` → you can list names but can't `cd` in or stat files.  
> `x` without `r` → you can `cd` in and access files *if you know their names*.

---

## Octal notation

Each triplet (u / g / o) collapses to a digit:

```
rwx = 4+2+1 = 7
r-x = 4+0+1 = 5
r-- = 4+0+0 = 4
```

```
drwxr-xr-x  →  755
-rw-r--r--  →  644
-rwx------  →  700
```

---

## Common patterns at a glance

| octal | string     | typical use |
|-------|-----------|-------------|
| `755` | `rwxr-xr-x` | public directory, executable |
| `644` | `rw-r--r--` | public read-only file |
| `600` | `rw-------` | private file (SSH keys, secrets) |
| `700` | `rwx------` | private directory / script |
| `777` | `rwxrwxrwx` | fully open — avoid in production |

---

## Changing permissions

```bash
chmod 755 file          # octal
chmod u+x file          # symbolic: add execute for owner
chmod go-w file         # remove write from group and others
chmod -R 644 dir/       # recursive
```

```bash
chown alice file        # change owner
chown alice:staff file  # owner + group
chgrp staff file        # group only
```

---

## Special bits (beyond rwx)

| bit | octal | effect |
|-----|-------|--------|
| **setuid** `s` on `u+x` | `4xxx` | executable runs as *file owner*, not caller |
| **setgid** `s` on `g+x` | `2xxx` | executable runs as *file group*; on a dir, new files inherit the group |
| **sticky** `t` on `o+x` | `1xxx` | on a dir, only the owner can delete their own files (`/tmp`) |

```bash
chmod 4755 /usr/bin/passwd   # setuid
chmod 2775 /shared/project   # setgid directory
chmod 1777 /tmp              # sticky
```

Appear as `s`/`S` (setuid/setgid) or `t`/`T` (sticky) in the string — uppercase when the underlying `x` bit is **not** set.

---

## Process identity & the check

Every process carries: **UID** (effective user) + **GID** (effective group).

```
Is caller root (UID 0)?  → full access, no check
Is caller the owner?     → apply u bits
Is caller in the group?  → apply g bits
Otherwise                → apply o bits
```

Only **one** triplet is tested — the first match wins. A user who is *also* in the file's group is still checked only against `u` bits.

---

## `umask` — default permission filter

`umask` defines which bits are *removed* when a new file/directory is created.

```
Default file    666
Default dir     777
umask           022
─────────────────────
New file        644  (666 & ~022)
New dir         755  (777 & ~022)
```

```bash
umask           # show current
umask 027       # set: files → 640, dirs → 750
```

---

## Quick mental model

```
Who?    u (owner)  g (group)  o (others)
What?   r (read)   w (write)  x (execute / traverse)
How?    chmod / chown / umask
```

Permissions are checked **left to right** (u → g → o), **first match wins**, **root bypasses all**.

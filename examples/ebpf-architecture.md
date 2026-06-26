# Architecture complète d'eBPF

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ESPACE UTILISATEUR                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   Code C     │    │  Code Rust   │    │ Code Python  │                   │
│  │  (eBPF)      │    │   (Aya)      │    │   (BCC)      │                   │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                   │
│         │                   │                   │                           │
│         ▼                   ▼                   ▼                           │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │                    COMPILATEUR (LLVM/Clang)                     │        │
│  │                    Target: BPF bytecode                         │        │
│  └─────────────────────────────┬───────────────────────────────────┘        │
│                                │                                            │
│                                ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │                      FICHIER ELF (.o)                           │        │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │        │
│  │  │  Bytecode   │  │    BTF      │  │   Maps      │              │        │
│  │  │    eBPF     │  │  (Type Info)│  │ Definitions │              │        │
│  │  └─────────────┘  └─────────────┘  └─────────────┘              │        │
│  └─────────────────────────────┬───────────────────────────────────┘        │
│                                │                                            │
│  ┌─────────────────────────────┼───────────────────────────────────┐        │
│  │         LOADERS             │                                   │        │
│  │  ┌──────────┐ ┌──────────┐  │  ┌──────────┐ ┌──────────┐        │        │
│  │  │  libbpf  │ │   BCC    │  │  │ bpftrace │ │  Cilium  │        │        │
│  │  └──────────┘ └──────────┘  │  └──────────┘ └──────────┘        │        │
│  └─────────────────────────────┼───────────────────────────────────┘        │
│                                │                                            │
│                                ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │                     SYSCALL bpf()                               │        │
│  │  BPF_PROG_LOAD | BPF_MAP_CREATE | BPF_PROG_ATTACH | ...         │        │
│  └─────────────────────────────┬───────────────────────────────────┘        │
│                                │                                            │
└────────────────────────────────┼─────────────────────────────────────────── ┘
                                 │
═════════════════════════════════╪═══════════════════════════════════════════
                                 │  FRONTIÈRE KERNEL
═════════════════════════════════╪═══════════════════════════════════════════
                                 │
┌────────────────────────────────┼───────────────────────────────────────────┐
│                                ▼                              ESPACE KERNEL │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │                        VÉRIFICATEUR eBPF                         │       │
│  │  ┌───────────────────────────────────────────────────────────┐  │        │
│  │  │  1. Vérification CFG (Control Flow Graph)                 │  │        │
│  │  │     - Pas de boucles infinies                             │  │        │
│  │  │     - Pas de code inatteignable                           │  │        │
│  │  │     - Programme termine toujours                          │  │        │
│  │  ├───────────────────────────────────────────────────────────┤  │        │
│  │  │  2. Simulation symbolique                                 │  │        │
│  │  │     - Tracking des registres (R0-R10)                     │  │        │
│  │  │     - Tracking de la pile (512 bytes max)                 │  │        │
│  │  │     - Vérification des accès mémoire                      │  │        │
│  │  │     - Vérification des types de pointeurs                 │  │        │
│  │  ├───────────────────────────────────────────────────────────┤  │        │
│  │  │  3. Vérification de sécurité                              │  │        │
│  │  │     - Pas de fuite d'adresses kernel                      │  │        │
│  │  │     - Accès mémoire bornés                                │  │        │
│  │  │     - Helpers autorisés uniquement                        │  │        │
│  │  └───────────────────────────────────────────────────────────┘  │        │
│  └─────────────────────────────┬───────────────────────────────────┘        │
│                                │                                            │
│              ┌─────────────────┴─────────────────┐                          │
│              ▼                                   ▼                          │
│  ┌─────────────────────┐             ┌─────────────────────┐                │
│  │   JIT COMPILER      │             │    INTERPRÉTEUR     │                │
│  │  (x86, ARM, etc.)   │             │    (fallback)       │                │
│  │                     │             │                     │                │
│  │  Bytecode eBPF      │             │  Bytecode eBPF      │                │
│  │       ↓             │             │       ↓             │                │
│  │  Code Machine Natif │             │  Exécution pas à pas│                │
│  └──────────┬──────────┘             └──────────┬──────────┘                │
│             └─────────────────┬─────────────────┘                           │
│                               ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │                    RUNTIME eBPF                                 │        │
│  │  ┌─────────────────────────────────────────────────────────────┐│        │
│  │  │                 MACHINE VIRTUELLE eBPF                      ││        │
│  │  │  ┌─────────────────────────────────────────────────────┐   ││         │
│  │  │  │  11 Registres 64-bit: R0-R10                        │   ││         │
│  │  │  │  R0  = Valeur de retour                             │   ││         │
│  │  │  │  R1-R5 = Arguments de fonction                      │   ││         │
│  │  │  │  R6-R9 = Callee-saved                               │   ││         │
│  │  │  │  R10 = Frame pointer (read-only)                    │   ││         │
│  │  │  ├─────────────────────────────────────────────────────┤   ││         │
│  │  │  │  Stack: 512 bytes                                   │   ││         │
│  │  │  │  Program Counter                                    │   ││         │
│  │  │  └─────────────────────────────────────────────────────┘   ││         │
│  │  └─────────────────────────────────────────────────────────────┘│        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Points d'attachement (Hook Points)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         POINTS D'ATTACHEMENT eBPF                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                          NETWORKING                                  │   │
│  │                                                                      │   │
│  │   Paquet entrant                                                     │   │
│  │        │                                                             │   │
│  │        ▼                                                             │   │
│  │   ┌─────────┐                                                        │   │
│  │   │   NIC   │ ◄─── XDP (eXpress Data Path) - Avant allocation skb   │   │
│  │   └────┬────┘      Le plus rapide, peut DROP/PASS/TX/REDIRECT        │   │
│  │        │                                                             │   │
│  │        ▼                                                             │   │
│  │   ┌─────────┐                                                        │   │
│  │   │   TC    │ ◄─── Traffic Control (ingress/egress)                 │   │
│  │   │ ingress │      Après création skb, avant routing                 │   │
│  │   └────┬────┘                                                        │   │
│  │        │                                                             │   │
│  │        ▼                                                             │   │
│  │   ┌─────────┐                                                        │   │
│  │   │ Netfilter│ ◄─── Hooks iptables/nftables                         │   │
│  │   └────┬────┘                                                        │   │
│  │        │                                                             │   │
│  │        ▼                                                             │   │
│  │   ┌─────────┐                                                        │   │
│  │   │ Socket  │ ◄─── Socket filters, sock_ops, sk_msg                 │   │
│  │   │ Layer   │      Filtrage au niveau socket                         │   │
│  │   └────┬────┘                                                        │   │
│  │        │                                                             │   │
│  │        ▼                                                             │   │
│  │   ┌─────────┐                                                        │   │
│  │   │   TC    │ ◄─── Traffic Control egress                           │   │
│  │   │ egress  │                                                        │   │
│  │   └─────────┘                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         TRACING / PROFILING                          │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │   │
│  │  │   kprobes    │  │  kretprobes  │  │ tracepoints  │               │   │
│  │  │              │  │              │  │              │               │   │
│  │  │ Hook n'importe│ │ Hook retour  │  │ Points fixes │               │   │
│  │  │ quelle fonction│ │ de fonction │  │ dans kernel  │               │   │
│  │  │ kernel       │  │              │  │              │               │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │   │
│  │  │   uprobes    │  │   USDT       │  │  perf_events │               │   │
│  │  │              │  │              │  │              │               │   │
│  │  │ Hook fonctions│ │ Tracepoints  │  │ CPU cycles,  │               │   │
│  │  │ userspace    │  │ userspace    │  │ cache miss...│               │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐                                 │   │
│  │  │  fentry/fexit│  │  raw_tp      │                                 │   │
│  │  │              │  │              │                                 │   │
│  │  │ BTF-enabled  │  │ Raw          │                                 │   │
│  │  │ function hook│  │ tracepoints  │                                 │   │
│  │  └──────────────┘  └──────────────┘                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                            SÉCURITÉ                                  │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │   │
│  │  │   LSM        │  │  seccomp     │  │   Landlock   │               │   │
│  │  │              │  │              │  │              │               │   │
│  │  │ Linux Security│ │ Syscall      │  │ Sandboxing   │               │   │
│  │  │ Module hooks │  │ filtering    │  │ non-root     │               │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                            AUTRES                                    │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │   │
│  │  │  cgroup      │  │  sched       │  │   struct_ops │               │   │
│  │  │              │  │              │  │              │               │   │
│  │  │ Contrôle par │  │ Scheduler    │  │ Implémenter  │               │   │
│  │  │ cgroup       │  │ extensible   │  │ des ops kernel│               │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## eBPF Maps (Structures de données)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              eBPF MAPS                                       │
│                  Structures de données partagées                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    COMMUNICATION                                     │   │
│   │                                                                      │   │
│   │    ESPACE UTILISATEUR                   ESPACE KERNEL               │   │
│   │    ┌──────────────┐                    ┌──────────────┐             │   │
│   │    │  Programme   │◄──── read ────────►│  Programme   │             │   │
│   │    │  Userspace   │───── write ───────►│    eBPF      │             │   │
│   │    └──────────────┘                    └──────────────┘             │   │
│   │           │                                   │                      │   │
│   │           │         ┌───────────────┐         │                      │   │
│   │           └────────►│   eBPF MAP    │◄────────┘                      │   │
│   │                     │  (dans kernel)│                                │   │
│   │                     └───────────────┘                                │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    TYPES DE MAPS                                     │   │
│   │                                                                      │   │
│   │  ┌─────────────────────┐    ┌─────────────────────┐                 │   │
│   │  │ BPF_MAP_TYPE_HASH   │    │ BPF_MAP_TYPE_ARRAY  │                 │   │
│   │  │                     │    │                     │                 │   │
│   │  │  ┌───┬───────┐      │    │  ┌───┬───────┐      │                 │   │
│   │  │  │Key│ Value │      │    │  │ 0 │ Value │      │                 │   │
│   │  │  ├───┼───────┤      │    │  ├───┼───────┤      │                 │   │
│   │  │  │Key│ Value │      │    │  │ 1 │ Value │      │                 │   │
│   │  │  ├───┼───────┤      │    │  ├───┼───────┤      │                 │   │
│   │  │  │Key│ Value │      │    │  │ 2 │ Value │      │                 │   │
│   │  │  └───┴───────┘      │    │  └───┴───────┘      │                 │   │
│   │  │  Hash table         │    │  Index-based        │                 │   │
│   │  └─────────────────────┘    └─────────────────────┘                 │   │
│   │                                                                      │   │
│   │  ┌─────────────────────┐    ┌─────────────────────┐                 │   │
│   │  │ BPF_MAP_TYPE_       │    │ BPF_MAP_TYPE_       │                 │   │
│   │  │ PERF_EVENT_ARRAY    │    │ RING_BUFFER         │                 │   │
│   │  │                     │    │                     │                 │   │
│   │  │  ┌───────────────┐  │    │  ┌───────────────┐  │                 │   │
│   │  │  │ CPU 0 │ event │  │    │  │    ─────►     │  │                 │   │
│   │  │  ├───────────────┤  │    │  │   Ring Buf    │  │                 │   │
│   │  │  │ CPU 1 │ event │  │    │  │    ◄─────     │  │                 │   │
│   │  │  └───────────────┘  │    │  └───────────────┘  │                 │   │
│   │  │  Per-CPU events     │    │  Shared ring buf    │                 │   │
│   │  └─────────────────────┘    └─────────────────────┘                 │   │
│   │                                                                      │   │
│   │  ┌─────────────────────┐    ┌─────────────────────┐                 │   │
│   │  │ BPF_MAP_TYPE_       │    │ BPF_MAP_TYPE_       │                 │   │
│   │  │ LRU_HASH            │    │ LPM_TRIE            │                 │   │
│   │  │                     │    │                     │                 │   │
│   │  │ Hash avec éviction  │    │ Longest Prefix      │                 │   │
│   │  │ LRU automatique     │    │ Match (pour IP)     │                 │   │
│   │  └─────────────────────┘    └─────────────────────┘                 │   │
│   │                                                                      │   │
│   │  ┌─────────────────────┐    ┌─────────────────────┐                 │   │
│   │  │ BPF_MAP_TYPE_       │    │ BPF_MAP_TYPE_       │                 │   │
│   │  │ PROG_ARRAY          │    │ STACK_TRACE         │                 │   │
│   │  │                     │    │                     │                 │   │
│   │  │ Pour tail calls     │    │ Stocke les stack    │                 │   │
│   │  │ (sauts de programme)│    │ traces              │                 │   │
│   │  └─────────────────────┘    └─────────────────────┘                 │   │
│   │                                                                      │   │
│   │  ┌─────────────────────┐    ┌─────────────────────┐                 │   │
│   │  │ BPF_MAP_TYPE_       │    │ BPF_MAP_TYPE_       │                 │   │
│   │  │ PERCPU_HASH/ARRAY   │    │ SOCKMAP/SOCKHASH    │                 │   │
│   │  │                     │    │                     │                 │   │
│   │  │ Une copie par CPU   │    │ Stocke des          │                 │   │
│   │  │ (pas de lock)       │    │ références socket   │                 │   │
│   │  └─────────────────────┘    └─────────────────────┘                 │   │
│   │                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Helpers Functions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         eBPF HELPER FUNCTIONS                                │
│            Fonctions kernel appelables depuis eBPF                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    OPÉRATIONS SUR LES MAPS                             │  │
│  │                                                                        │  │
│  │  bpf_map_lookup_elem()   - Chercher une valeur                        │  │
│  │  bpf_map_update_elem()   - Mettre à jour/créer                        │  │
│  │  bpf_map_delete_elem()   - Supprimer un élément                       │  │
│  │  bpf_map_push_elem()     - Push (stack/queue)                         │  │
│  │  bpf_map_pop_elem()      - Pop (stack/queue)                          │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    MANIPULATION DE PAQUETS                             │  │
│  │                                                                        │  │
│  │  bpf_skb_load_bytes()         - Lire des bytes du paquet              │  │
│  │  bpf_skb_store_bytes()        - Écrire dans le paquet                 │  │
│  │  bpf_skb_change_head()        - Modifier l'en-tête                    │  │
│  │  bpf_skb_change_tail()        - Modifier la queue                     │  │
│  │  bpf_redirect()               - Rediriger le paquet                   │  │
│  │  bpf_clone_redirect()         - Cloner et rediriger                   │  │
│  │  bpf_xdp_adjust_head()        - Ajuster (XDP)                         │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    TRACING / DEBUGGING                                 │  │
│  │                                                                        │  │
│  │  bpf_trace_printk()           - Printf vers trace_pipe                │  │
│  │  bpf_get_current_pid_tgid()   - PID/TGID courant                      │  │
│  │  bpf_get_current_uid_gid()    - UID/GID courant                       │  │
│  │  bpf_get_current_comm()       - Nom du processus                      │  │
│  │  bpf_ktime_get_ns()           - Timestamp en nanosecondes             │  │
│  │  bpf_get_stackid()            - ID de stack trace                     │  │
│  │  bpf_probe_read()             - Lire mémoire kernel                   │  │
│  │  bpf_probe_read_user()        - Lire mémoire userspace                │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    TAIL CALLS & FUNCTION CALLS                         │  │
│  │                                                                        │  │
│  │  bpf_tail_call()              - Saut vers autre programme             │  │
│  │  bpf_loop()                   - Boucle controlée (kernel 5.17+)       │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    ÉVÉNEMENTS / NOTIFICATIONS                          │  │
│  │                                                                        │  │
│  │  bpf_perf_event_output()      - Envoyer vers perf buffer              │  │
│  │  bpf_ringbuf_output()         - Envoyer vers ring buffer              │  │
│  │  bpf_ringbuf_reserve()        - Réserver espace ring buffer           │  │
│  │  bpf_ringbuf_submit()         - Soumettre données                     │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    CRYPTOGRAPHIE & CHECKSUM                            │  │
│  │                                                                        │  │
│  │  bpf_csum_diff()              - Différence de checksum                │  │
│  │  bpf_l3_csum_replace()        - Remplacer checksum L3                 │  │
│  │  bpf_l4_csum_replace()        - Remplacer checksum L4                 │  │
│  │  bpf_get_prandom_u32()        - Nombre aléatoire                      │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    SOCKET OPERATIONS                                   │  │
│  │                                                                        │  │
│  │  bpf_sock_map_update()        - Associer socket à map                 │  │
│  │  bpf_msg_redirect_map()       - Rediriger message                     │  │
│  │  bpf_sk_redirect_map()        - Rediriger socket                      │  │
│  │  bpf_get_socket_cookie()      - Cookie unique de socket               │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Jeu d'instructions eBPF

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      JEU D'INSTRUCTIONS eBPF                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Format d'instruction: 64 bits                                              │
│  ┌────────┬────────┬────────┬────────┬──────────────────────────────────┐  │
│  │ opcode │dst_reg │src_reg │ offset │           imm (32 bits)          │  │
│  │ 8 bits │ 4 bits │ 4 bits │16 bits │                                  │  │
│  └────────┴────────┴────────┴────────┴──────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    CLASSES D'OPÉRATIONS                                │  │
│  │                                                                        │  │
│  │  BPF_LD     0x00   - Load depuis mémoire                              │  │
│  │  BPF_LDX    0x01   - Load depuis mémoire (registre)                   │  │
│  │  BPF_ST     0x02   - Store vers mémoire                               │  │
│  │  BPF_STX    0x03   - Store vers mémoire (registre)                    │  │
│  │  BPF_ALU    0x04   - Opérations ALU 32-bit                            │  │
│  │  BPF_JMP    0x05   - Sauts 64-bit                                     │  │
│  │  BPF_JMP32  0x06   - Sauts 32-bit                                     │  │
│  │  BPF_ALU64  0x07   - Opérations ALU 64-bit                            │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    OPÉRATIONS ALU                                      │  │
│  │                                                                        │  │
│  │  BPF_ADD    0x00   dst += src                                         │  │
│  │  BPF_SUB    0x10   dst -= src                                         │  │
│  │  BPF_MUL    0x20   dst *= src                                         │  │
│  │  BPF_DIV    0x30   dst /= src                                         │  │
│  │  BPF_OR     0x40   dst |= src                                         │  │
│  │  BPF_AND    0x50   dst &= src                                         │  │
│  │  BPF_LSH    0x60   dst <<= src                                        │  │
│  │  BPF_RSH    0x70   dst >>= src (logical)                              │  │
│  │  BPF_NEG    0x80   dst = ~src                                         │  │
│  │  BPF_MOD    0x90   dst %= src                                         │  │
│  │  BPF_XOR    0xa0   dst ^= src                                         │  │
│  │  BPF_MOV    0xb0   dst = src                                          │  │
│  │  BPF_ARSH   0xc0   dst >>= src (arithmetic)                           │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    SAUTS CONDITIONNELS                                 │  │
│  │                                                                        │  │
│  │  BPF_JA     0x00   goto pc + offset                                   │  │
│  │  BPF_JEQ    0x10   if dst == src goto pc + offset                     │  │
│  │  BPF_JGT    0x20   if dst > src goto pc + offset (unsigned)           │  │
│  │  BPF_JGE    0x30   if dst >= src goto pc + offset (unsigned)          │  │
│  │  BPF_JSET   0x40   if dst & src goto pc + offset                      │  │
│  │  BPF_JNE    0x50   if dst != src goto pc + offset                     │  │
│  │  BPF_JSGT   0x60   if dst > src goto pc + offset (signed)             │  │
│  │  BPF_JSGE   0x70   if dst >= src goto pc + offset (signed)            │  │
│  │  BPF_CALL   0x80   call helper function                               │  │
│  │  BPF_EXIT   0x90   return                                             │  │
│  │  BPF_JLT    0xa0   if dst < src goto pc + offset (unsigned)           │  │
│  │  BPF_JLE    0xb0   if dst <= src goto pc + offset (unsigned)          │  │
│  │  BPF_JSLT   0xc0   if dst < src goto pc + offset (signed)             │  │
│  │  BPF_JSLE   0xd0   if dst <= src goto pc + offset (signed)            │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## BTF (BPF Type Format) et CO-RE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BTF & CO-RE (Compile Once, Run Everywhere)                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         PROBLÈME SANS CO-RE                            │  │
│  │                                                                        │  │
│  │   Kernel 5.4                        Kernel 5.15                       │  │
│  │   struct task_struct {              struct task_struct {              │  │
│  │     ...                               ...                             │  │
│  │     pid_t pid;        ◄─ offset 100   int flags;      ◄─ offset 100   │  │
│  │     ...                               pid_t pid;      ◄─ offset 108   │  │
│  │   }                                   ...                             │  │
│  │                                     }                                 │  │
│  │                                                                        │  │
│  │   ⚠️  Le même programme eBPF compilé pour 5.4 crash sur 5.15 !       │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         SOLUTION: BTF + CO-RE                          │  │
│  │                                                                        │  │
│  │                                                                        │  │
│  │   ┌──────────────────┐                                                │  │
│  │   │  Programme eBPF  │                                                │  │
│  │   │   compilé avec   │                                                │  │
│  │   │   relocations    │                                                │  │
│  │   └────────┬─────────┘                                                │  │
│  │            │                                                          │  │
│  │            ▼                                                          │  │
│  │   ┌──────────────────┐     ┌──────────────────┐                      │  │
│  │   │     libbpf       │────►│   BTF du kernel  │                      │  │
│  │   │   (loader)       │     │  (/sys/kernel/   │                      │  │
│  │   │                  │     │   btf/vmlinux)   │                      │  │
│  │   └────────┬─────────┘     └──────────────────┘                      │  │
│  │            │                        │                                 │  │
│  │            │  Applique les         │ Contient les vrais              │  │
│  │            │  relocations          │ offsets pour CE kernel          │  │
│  │            ▼                        │                                 │  │
│  │   ┌──────────────────┐              │                                 │  │
│  │   │  Programme eBPF  │◄─────────────┘                                │  │
│  │   │  adapté pour     │                                                │  │
│  │   │  CE kernel       │                                                │  │
│  │   └──────────────────┘                                                │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    CONTENU DU BTF                                      │  │
│  │                                                                        │  │
│  │  ┌─────────────────┐                                                  │  │
│  │  │  Types kernel   │  - Toutes les structures                         │  │
│  │  │                 │  - Enums, unions, typedefs                       │  │
│  │  │                 │  - Pointeurs, arrays                             │  │
│  │  └─────────────────┘                                                  │  │
│  │                                                                        │  │
│  │  ┌─────────────────┐                                                  │  │
│  │  │  Infos fonction │  - Prototypes                                    │  │
│  │  │                 │  - Arguments et retours                          │  │
│  │  └─────────────────┘                                                  │  │
│  │                                                                        │  │
│  │  ┌─────────────────┐                                                  │  │
│  │  │   Line info     │  - Correspondance source                         │  │
│  │  │                 │  - Debug info                                    │  │
│  │  └─────────────────┘                                                  │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Flux de données complet

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      FLUX DE DONNÉES eBPF COMPLET                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   DÉVELOPPEMENT                                                             │
│   ┌─────────┐                                                               │
│   │ my.bpf.c│  Code source C                                               │
│   └────┬────┘                                                               │
│        │                                                                    │
│        ▼                                                                    │
│   ┌─────────┐                                                               │
│   │  clang  │  -target bpf -g -O2                                          │
│   └────┬────┘                                                               │
│        │                                                                    │
│        ▼                                                                    │
│   ┌─────────┐                                                               │
│   │ my.bpf.o│  ELF object avec bytecode + BTF                              │
│   └────┬────┘                                                               │
│        │                                                                    │
│   ─────┼─────────────────────────────────────────────────────────────────   │
│        │  RUNTIME                                                           │
│        ▼                                                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    CHARGEMENT (libbpf)                               │   │
│   │                                                                      │   │
│   │  1. Parse ELF                                                        │   │
│   │  2. Résout les relocations CO-RE via BTF kernel                     │   │
│   │  3. Crée les maps (bpf(BPF_MAP_CREATE))                             │   │
│   │  4. Charge le programme (bpf(BPF_PROG_LOAD))                        │   │
│   │                                                                      │   │
│   └────────────────────────────┬────────────────────────────────────────┘   │
│                                │                                            │
│   ═══════════════════════════════════════════════════════════════════════   │
│                                │  KERNEL                                    │
│   ═══════════════════════════════════════════════════════════════════════   │
│                                ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      VÉRIFICATEUR                                    │   │
│   │                                                                      │   │
│   │  ┌───────────┐    ┌───────────┐    ┌───────────┐                   │   │
│   │  │ CFG Check │───►│ Symbolic  │───►│ Bounds    │                   │   │
│   │  │           │    │ Execution │    │ Check     │                   │   │
│   │  └───────────┘    └───────────┘    └───────────┘                   │   │
│   │                                          │                          │   │
│   │                      ┌───────────────────┼───────────────────┐      │   │
│   │                      ▼                   ▼                   │      │   │
│   │              ┌───────────┐        ┌───────────┐              │      │   │
│   │              │  REJECT   │        │  ACCEPT   │              │      │   │
│   │              │  (erreur) │        │           │              │      │   │
│   │              └───────────┘        └─────┬─────┘              │      │   │
│   │                                         │                    │      │   │
│   └─────────────────────────────────────────┼────────────────────┘      │   │
│                                             │                            │   │
│                                             ▼                            │   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      JIT COMPILER                                    │   │
│   │                                                                      │   │
│   │   eBPF bytecode ────────────────────────► x86_64 / ARM64 natif     │   │
│   │                                                                      │   │
│   └────────────────────────────┬────────────────────────────────────────┘   │
│                                │                                            │   │
│                                ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      ATTACHEMENT                                     │   │
│   │                                                                      │   │
│   │   bpf(BPF_PROG_ATTACH) / bpf_link                                   │   │
│   │                    │                                                │   │
│   │                    ▼                                                │   │
│   │   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐     │   │
│   │   │  XDP    │ │   TC    │ │ kprobe  │ │  LSM    │ │  cgroup │     │   │
│   │   └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘     │   │
│   │                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   EXÉCUTION                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                                                                      │   │
│   │   EVENT ──────► Programme eBPF ──────► Action                       │   │
│   │   (paquet,       s'exécute              (DROP, PASS,                │   │
│   │    syscall,                              REDIRECT, log              │   │
│   │    timer...)                             vers map...)               │   │
│   │                        │                                            │   │
│   │                        ▼                                            │   │
│   │                   eBPF MAPS                                         │   │
│   │                   ┌─────────┐                                       │   │
│   │                   │ stats,  │                                       │   │
│   │                   │ config, │◄───── Lecture/Écriture userspace     │   │
│   │                   │ events  │                                       │   │
│   │                   └─────────┘                                       │   │
│   │                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Écosystème et outils

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ÉCOSYSTÈME eBPF                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    BIBLIOTHÈQUES DE DÉVELOPPEMENT                      │  │
│  │                                                                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │  │
│  │  │   libbpf    │  │     BCC     │  │     Aya     │  │  libbpf-rs  │   │  │
│  │  │    (C)      │  │  (Python/C) │  │   (Rust)    │  │   (Rust)    │   │  │
│  │  │             │  │             │  │             │  │             │   │  │
│  │  │ Référence   │  │ Haut niveau │  │ Pure Rust   │  │ Bindings    │   │  │
│  │  │ officielle  │  │ + runtime   │  │ eBPF        │  │ libbpf      │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    OUTILS DE TRACING                                   │  │
│  │                                                                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                    │  │
│  │  │  bpftrace   │  │  BCC tools  │  │   perf      │                    │  │
│  │  │             │  │             │  │             │                    │  │
│  │  │ Langage DSL │  │ 100+ outils │  │ Support BPF │                    │  │
│  │  │ haut niveau │  │ prêts       │  │ intégré     │                    │  │
│  │  │             │  │             │  │             │                    │  │
│  │  │ Ex:         │  │ Ex:         │  │             │                    │  │
│  │  │ bpftrace -e │  │ execsnoop   │  │             │                    │  │
│  │  │ 'kprobe:*'  │  │ opensnoop   │  │             │                    │  │
│  │  │             │  │ tcplife     │  │             │                    │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                    │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    PROJETS BASÉS SUR eBPF                              │  │
│  │                                                                        │  │
│  │  NETWORKING                                                            │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                    │  │
│  │  │   Cilium    │  │   Calico    │  │   Katran    │                    │  │
│  │  │             │  │   eBPF      │  │   (Meta)    │                    │  │
│  │  │ CNI K8s     │  │             │  │             │                    │  │
│  │  │ + Security  │  │ CNI K8s     │  │ L4 Load     │                    │  │
│  │  │ + Observ.   │  │             │  │ Balancer    │                    │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                    │  │
│  │                                                                        │  │
│  │  SÉCURITÉ                                                              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                    │  │
│  │  │   Falco     │  │   Tetragon  │  │   Tracee    │                    │  │
│  │  │             │  │             │  │             │                    │  │
│  │  │ Runtime     │  │ Security    │  │ Runtime     │                    │  │
│  │  │ Security    │  │ Observ. &   │  │ Security    │                    │  │
│  │  │ (Sysdig)    │  │ Enforcement │  │ (Aqua)      │                    │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                    │  │
│  │                                                                        │  │
│  │  OBSERVABILITÉ                                                         │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                    │  │
│  │  │   Pixie     │  │  Parca      │  │  Pyroscope  │                    │  │
│  │  │             │  │             │  │             │                    │  │
│  │  │ K8s         │  │ Continuous  │  │ Continuous  │                    │  │
│  │  │ Observ.     │  │ Profiling   │  │ Profiling   │                    │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                    │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    OUTILS D'ADMINISTRATION                             │  │
│  │                                                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                        bpftool                                   │  │  │
│  │  │                                                                  │  │  │
│  │  │  bpftool prog list          - Lister programmes chargés         │  │  │
│  │  │  bpftool map show           - Afficher les maps                 │  │  │
│  │  │  bpftool prog dump xlated   - Désassembler programme            │  │  │
│  │  │  bpftool btf dump           - Afficher BTF                      │  │  │
│  │  │  bpftool net show           - Programmes réseau attachés        │  │  │
│  │  │  bpftool cgroup tree        - Programmes cgroup                 │  │  │
│  │  │                                                                  │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Résumé des types de programmes eBPF

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TYPES DE PROGRAMMES eBPF                                  │
├──────────────────────┬──────────────────────────────────────────────────────┤
│ Type                 │ Description & Usage                                  │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ BPF_PROG_TYPE_       │                                                      │
│ SOCKET_FILTER        │ Filtrage de paquets au niveau socket                │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ BPF_PROG_TYPE_       │                                                      │
│ KPROBE               │ Hook sur fonctions kernel (entrée)                  │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ BPF_PROG_TYPE_       │                                                      │
│ TRACEPOINT           │ Points de trace statiques du kernel                  │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ BPF_PROG_TYPE_XDP    │ eXpress Data Path - traitement ultra-rapide paquets │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ BPF_PROG_TYPE_       │                                                      │
│ PERF_EVENT           │ Événements de performance (CPU, cache...)           │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ BPF_PROG_TYPE_       │                                                      │
│ CGROUP_SKB           │ Filtrage réseau par cgroup                          │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ BPF_PROG_TYPE_       │                                                      │
│ CGROUP_SOCK          │ Contrôle socket par cgroup                          │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ BPF_PROG_TYPE_       │                                                      │
│ LWT_*                │ Lightweight Tunnel (encapsulation)                  │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ BPF_PROG_TYPE_       │                                                      │
│ SOCK_OPS             │ Callbacks sur opérations socket TCP                  │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ BPF_PROG_TYPE_       │                                                      │
│ SK_SKB               │ Redirection de stream socket                        │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ BPF_PROG_TYPE_       │                                                      │
│ RAW_TRACEPOINT       │ Tracepoints avec accès raw aux arguments            │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ BPF_PROG_TYPE_       │                                                      │
│ CGROUP_SOCKOPT       │ Contrôle setsockopt/getsockopt                      │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ BPF_PROG_TYPE_       │                                                      │
│ TRACING              │ fentry/fexit/fmod_ret (BTF-based)                   │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ BPF_PROG_TYPE_       │                                                      │
│ STRUCT_OPS           │ Implémenter des ops kernel (ex: TCP congestion)     │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ BPF_PROG_TYPE_LSM    │ Linux Security Module hooks                          │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ BPF_PROG_TYPE_       │                                                      │
│ SK_LOOKUP            │ Programmable socket lookup                          │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ BPF_PROG_TYPE_       │                                                      │
│ SYSCALL              │ Appel direct depuis bpf() syscall                   │
└──────────────────────┴──────────────────────────────────────────────────────┘
```

---

## Limites et contraintes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LIMITES ET CONTRAINTES eBPF                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    RESSOURCES                                          │  │
│  │                                                                        │  │
│  │  • Stack size          : 512 bytes maximum                            │  │
│  │  • Instructions        : 1 million (depuis kernel 5.2)                │  │
│  │  • Nested calls        : 8 niveaux de profondeur max                  │  │
│  │  • Tail calls          : 33 chaînages max                             │  │
│  │  • Map entries         : Dépend du type et de la mémoire              │  │
│  │  • Complexité verifier : ~1M instructions analysées                   │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    RESTRICTIONS DE SÉCURITÉ                            │  │
│  │                                                                        │  │
│  │  • Pas d'accès mémoire arbitraire                                     │  │
│  │  • Pas de pointeurs vers l'extérieur du contexte                      │  │
│  │  • Pas d'arithmétique de pointeurs dangereuse                         │  │
│  │  • Boucles doivent être bornées (prouvable)                           │  │
│  │  • Pas d'allocation dynamique (sauf via helpers)                      │  │
│  │  • Pas de récursion                                                   │  │
│  │  • Privilèges requis: CAP_BPF ou root (selon config)                  │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    ÉVOLUTION PAR VERSION KERNEL                        │  │
│  │                                                                        │  │
│  │  Kernel 3.18  : eBPF initial (64-bit, 10 registres)                   │  │
│  │  Kernel 4.1   : TC classifier support                                 │  │
│  │  Kernel 4.4   : Perf events, hardware events                          │  │
│  │  Kernel 4.7   : XDP                                                   │  │
│  │  Kernel 4.10  : cgroup socket filtering                               │  │
│  │  Kernel 4.15  : BTF support initial                                   │  │
│  │  Kernel 5.2   : Limite 1M instructions, bounded loops                 │  │
│  │  Kernel 5.3   : Bounded loops officiellement supportées               │  │
│  │  Kernel 5.5   : Global functions                                      │  │
│  │  Kernel 5.8   : Ring buffer, CAP_BPF                                  │  │
│  │  Kernel 5.10  : BTF pour modules                                      │  │
│  │  Kernel 5.13  : Atomic operations                                     │  │
│  │  Kernel 5.15  : Bloom filter map, bpf_timer                          │  │
│  │  Kernel 5.17  : bpf_loop(), typed pointers                           │  │
│  │  Kernel 6.1   : User ring buffer, kptrs                               │  │
│  │  Kernel 6.6   : Token-based delegation                                │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Document généré pour référence d'architecture eBPF*

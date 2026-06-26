# Minimal PKCS#11 Backend Implementation in C/C++ with OpenSSL 3

> **Progressive guide** — each step builds on the previous. After each step, share your implementation for review.

---

## Step 1: Project Skeleton with CMake

### 1.1 Directory Layout

```
pkcs11-backend/
├── CMakeLists.txt
├── include/
│   ├── pkcs11.h          # OASIS PKCS#11 v2.40 header (copy from oasis or cryptoki)
│   └── backend.h         # Internal state & helpers
├── src/
│   ├── main.c            # All C_Xxx entry points
│   ├── init.c            # C_Initialize / C_Finalize
│   ├── slot.c            # C_GetSlotList / C_GetSlotInfo / C_GetTokenInfo
│   ├── session.c         # C_OpenSession / C_CloseSession / C_Login
│   ├── object.c          # C_FindObjects* / C_GetAttributeValue
│   └── crypto.c          # C_Sign / C_Verify / C_Encrypt / C_Decrypt
└── tests/
    └── smoke.c           # Minimal end-to-end smoke test
```

### 1.2 CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.20)
project(pkcs11_backend C CXX)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# --- OpenSSL 3 -----------------------------------------------------------
find_package(OpenSSL 3.0 REQUIRED)

# --- Shared library (the PKCS#11 module itself) --------------------------
add_library(pkcs11_backend SHARED
    src/main.c
    src/init.c
    src/slot.c
    src/session.c
    src/object.c
    src/crypto.c
)

target_include_directories(pkcs11_backend PRIVATE
    include/
    ${OPENSSL_INCLUDE_DIR}
)

target_link_libraries(pkcs11_backend PRIVATE
    OpenSSL::Crypto   # libcrypto — EVP, RSA, EC, etc.
    # OpenSSL::SSL    # only if you need TLS; omit otherwise
)

# Strip the default "lib" prefix so the output is pkcs11_backend.so/.dll
set_target_properties(pkcs11_backend PROPERTIES PREFIX "")

# --- Smoke test ----------------------------------------------------------
add_executable(smoke tests/smoke.c)
target_include_directories(smoke PRIVATE include/)
target_link_libraries(smoke PRIVATE pkcs11_backend)

# --- Compiler hardening (recommended for a crypto module) ----------------
if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(pkcs11_backend PRIVATE
        -Wall -Wextra -Wpedantic
        -fstack-protector-strong
        -fPIC                   # mandatory for shared libs
        -D_FORTIFY_SOURCE=2
    )
    target_link_options(pkcs11_backend PRIVATE
        -Wl,-z,relro,-z,now     # RELRO + BIND_NOW on Linux
    )
endif()
```

### 1.3 Build Instructions

```bash
cmake -B build -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build -j$(nproc)

# Verify the exported symbol list contains C_Initialize etc.
nm -D build/pkcs11_backend.so | grep ' T C_'
```

> **Note:** On macOS, replace `-Wl,-z,relro,-z,now` with `-Wl,-bind_at_load`.

---

## Step 2: Internal State & Headers

Before touching any PKCS#11 function, define the global state your module carries.

### `include/backend.h`

```c
#pragma once

#include <stdint.h>
#include <stdatomic.h>
#include <pthread.h>

#include <openssl/evp.h>
#include <openssl/err.h>

/* PKCS#11 slot/token constants */
#define BACKEND_SLOT_ID     0UL
#define BACKEND_MAX_SESSIONS 32

/* Module lifecycle states */
typedef enum {
    MODULE_UNINITIALIZED = 0,
    MODULE_INITIALIZED
} ModuleState;

/* Minimal session record */
typedef struct {
    CK_SESSION_HANDLE handle;
    CK_FLAGS          flags;    /* CKF_RW_SESSION etc. */
    int               in_use;
} Session;

/* Global singleton — one per process */
typedef struct {
    atomic_int   state;         /* ModuleState, manipulated atomically */
    pthread_mutex_t lock;
    Session      sessions[BACKEND_MAX_SESSIONS];

    /* OpenSSL provider handle if you load a custom provider */
    OSSL_LIB_CTX *ossl_ctx;
} BackendGlobal;

extern BackendGlobal g_backend;

/* Utility: translate the last OpenSSL error to a log line */
void backend_log_openssl_error(const char *context);
```

> **Design note:** The `atomic_int state` guards `C_Initialize`/`C_Finalize` re-entrancy without a mutex, following the *double-checked locking* pattern common in PKCS#11 modules.

---

## Step 3: Implementing `C_Initialize`

### Description

`C_Initialize` is the **first function called** by any PKCS#11 application. It must:

1. Accept an optional `CK_C_INITIALIZE_ARGS` pointer (threading model, custom allocators).
2. Return `CKR_CRYPTOKI_ALREADY_INITIALIZED` if called twice.
3. Set up any internal state (here: an OpenSSL library context).
4. Be thread-safe if `pInitArgs->flags & CKF_OS_LOCKING_OK`.

### `src/init.c`

```c
#include <string.h>
#include <pthread.h>

/* pkcs11.h must be included BEFORE any other project header that uses CK_* types */
#define CK_PTR *
#define CK_DECLARE_FUNCTION(rv, name)   rv name
#define CK_DECLARE_FUNCTION_POINTER(rv, name) rv (*name)
#define CK_CALLBACK_FUNCTION(rv, name)  rv (*name)
#ifndef NULL_PTR
#  define NULL_PTR NULL
#endif
#include "pkcs11.h"

#include "backend.h"

/* Definition of the global singleton (declared extern in backend.h) */
BackendGlobal g_backend = {
    .state    = ATOMIC_VAR_INIT(MODULE_UNINITIALIZED),
    .lock     = PTHREAD_MUTEX_INITIALIZER,
    .ossl_ctx = NULL
};

/* -------------------------------------------------------------------------
 * C_Initialize
 * pInitArgs may be NULL (single-threaded caller) or a CK_C_INITIALIZE_ARGS*.
 * We support OS-level locking only (CKF_OS_LOCKING_OK); custom mutexes are
 * rejected with CKR_CANT_LOCK to keep the implementation minimal.
 * ---------------------------------------------------------------------- */
CK_RV C_Initialize(CK_VOID_PTR pInitArgs)
{
    /* Atomically check-and-set: return ALREADY_INITIALIZED on races */
    int expected = MODULE_UNINITIALIZED;
    if (!atomic_compare_exchange_strong(
            &g_backend.state, &expected, MODULE_INITIALIZED)) {
        return CKR_CRYPTOKI_ALREADY_INITIALIZED;
    }

    if (pInitArgs != NULL_PTR) {
        CK_C_INITIALIZE_ARGS_PTR args = (CK_C_INITIALIZE_ARGS_PTR)pInitArgs;

        /* Caller supplied custom mutex functions — we don't support that */
        if (args->CreateMutex != NULL_PTR) {
            atomic_store(&g_backend.state, MODULE_UNINITIALIZED);
            return CKR_CANT_LOCK;
        }

        /* Reserved field MUST be NULL per PKCS#11 spec */
        if (args->pReserved != NULL_PTR) {
            atomic_store(&g_backend.state, MODULE_UNINITIALIZED);
            return CKR_ARGUMENTS_BAD;
        }
    }

    /* Create a dedicated OpenSSL library context for our module.
     * This isolates our providers/config from the application's default ctx. */
    g_backend.ossl_ctx = OSSL_LIB_CTX_new();
    if (g_backend.ossl_ctx == NULL) {
        atomic_store(&g_backend.state, MODULE_UNINITIALIZED);
        return CKR_GENERAL_ERROR;
    }

    /* (Optional) Load a non-default provider, e.g. "legacy" or custom HSM shim */
    /* OSSL_PROVIDER_load(g_backend.ossl_ctx, "default"); */

    memset(g_backend.sessions, 0, sizeof(g_backend.sessions));

    return CKR_OK;
}

/* -------------------------------------------------------------------------
 * C_Finalize
 * Must be the last PKCS#11 call. pReserved MUST be NULL per spec.
 * ---------------------------------------------------------------------- */
CK_RV C_Finalize(CK_VOID_PTR pReserved)
{
    if (pReserved != NULL_PTR)
        return CKR_ARGUMENTS_BAD;

    int expected = MODULE_INITIALIZED;
    if (!atomic_compare_exchange_strong(
            &g_backend.state, &expected, MODULE_UNINITIALIZED)) {
        return CKR_CRYPTOKI_NOT_INITIALIZED;
    }

    /* Close any still-open sessions before teardown */
    pthread_mutex_lock(&g_backend.lock);
    memset(g_backend.sessions, 0, sizeof(g_backend.sessions));
    pthread_mutex_unlock(&g_backend.lock);

    if (g_backend.ossl_ctx) {
        OSSL_LIB_CTX_free(g_backend.ossl_ctx);
        g_backend.ossl_ctx = NULL;
    }

    return CKR_OK;
}
```

### `src/main.c` — The Function List Table

PKCS#11 callers resolve your entry points via `C_GetFunctionList`. Every symbol must be present even if unimplemented (return `CKR_FUNCTION_NOT_SUPPORTED`).

```c
#define CK_PTR *
#define CK_DECLARE_FUNCTION(rv, name)   rv name
#define CK_DECLARE_FUNCTION_POINTER(rv, name) rv (*name)
#define CK_CALLBACK_FUNCTION(rv, name)  rv (*name)
#ifndef NULL_PTR
#  define NULL_PTR NULL
#endif
#include "pkcs11.h"
#include "backend.h"

/* Forward declarations for all implemented functions */
extern CK_RV C_Initialize(CK_VOID_PTR);
extern CK_RV C_Finalize(CK_VOID_PTR);
/* ... add each C_Xxx as you implement it ... */

/* Stub for unimplemented functions */
static CK_RV not_supported() { return CKR_FUNCTION_NOT_SUPPORTED; }

static CK_FUNCTION_LIST s_function_list = {
    { CRYPTOKI_VERSION_MAJOR, CRYPTOKI_VERSION_MINOR },
    C_Initialize,
    C_Finalize,
    (CK_C_GetInfo)           not_supported,  /* filled in Step 4 */
    C_GetFunctionList,
    (CK_C_GetSlotList)       not_supported,  /* filled in Step 5 */
    /* ... one line per PKCS#11 function ... */
};

CK_RV C_GetFunctionList(CK_FUNCTION_LIST_PTR_PTR ppFunctionList)
{
    if (ppFunctionList == NULL_PTR)
        return CKR_ARGUMENTS_BAD;
    *ppFunctionList = &s_function_list;
    return CKR_OK;
}
```

> **Key point:** `C_GetFunctionList` is the **only** symbol that a caller is allowed to resolve by name (via `dlsym`/`GetProcAddress`). Every other function goes through the table.

### Key Implementation Notes

| Topic | Note |
|---|---|
| Re-entrancy | `atomic_compare_exchange_strong` is lock-free and correct under the C11 memory model. |
| OpenSSL isolation | `OSSL_LIB_CTX_new()` is the OpenSSL 3 replacement for the old global state. Always pass it to every `EVP_*` / `OSSL_*` call. |
| Custom allocators | `CK_C_INITIALIZE_ARGS.CreateMutex != NULL` means the app wants its own mutex primitives — safe to reject unless you need p11-kit compatibility. |
| Error rollback | Any failure after the atomic set must `atomic_store(&g_backend.state, MODULE_UNINITIALIZED)` before returning. |

---

## Error Handling Reference

```c
/* Map a generic internal failure to the appropriate CK_RV */
static inline CK_RV ckr_from_openssl(void)
{
    unsigned long e = ERR_peek_last_error();
    if (e == 0)
        return CKR_GENERAL_ERROR;

    switch (ERR_GET_REASON(e)) {
        case ERR_R_MALLOC_FAILURE:  return CKR_HOST_MEMORY;
        default:                    return CKR_GENERAL_ERROR;
    }
}

/* Convenience: log + return */
#define RETURN_CKR(rv) do {                                 \
    CK_RV _rv = (rv);                                       \
    if (_rv != CKR_OK)                                      \
        backend_log_openssl_error(__func__);                \
    return _rv;                                             \
} while (0)
```

Common return codes to always handle:

```
CKR_OK                        — success
CKR_ARGUMENTS_BAD             — NULL where non-NULL required, or reserved != NULL
CKR_CRYPTOKI_NOT_INITIALIZED  — called before C_Initialize
CKR_CRYPTOKI_ALREADY_INITIALIZED
CKR_HOST_MEMORY               — malloc/EVP allocation failure
CKR_GENERAL_ERROR             — catch-all for OpenSSL internals
CKR_FUNCTION_NOT_SUPPORTED    — stub return for unimplemented functions
```

---

## Memory Management Basics

```c
/* Rule 1: always zero sensitive material before free */
static void secure_free(void *ptr, size_t len)
{
    if (ptr) {
        OPENSSL_cleanse(ptr, len);   /* OpenSSL's memset-that-won't-be-optimized-out */
        OPENSSL_free(ptr);           /* use OPENSSL_free for memory from OpenSSL APIs */
    }
}

/* Rule 2: use OPENSSL_malloc/OPENSSL_free for buffers handed to OpenSSL */
unsigned char *buf = OPENSSL_malloc(key_len);
/* ... */
OPENSSL_cleanse(buf, key_len);
OPENSSL_free(buf);

/* Rule 3: never store raw key material in a CK_ATTRIBUTE value longer
   than the function call — copy out, then cleanse immediately */
```

---

## Troubleshooting

### `pkcs11.h` not found

Download the OASIS v2.40 header from the PKCS#11 TC or install:
```bash
# Debian/Ubuntu
apt install libp11-kit-dev    # provides /usr/include/p11-kit-1/p11-kit/pkcs11.h

# Or grab it directly
curl -LO https://raw.githubusercontent.com/nicowillis/pkcs11/master/pkcs11.h
```

### `OpenSSL 3.0 not found` in CMake

```bash
# Debian/Ubuntu
apt install libssl-dev

# macOS (Homebrew)
brew install openssl@3
export OPENSSL_ROOT_DIR=$(brew --prefix openssl@3)
cmake -B build -DOPENSSL_ROOT_DIR=$OPENSSL_ROOT_DIR
```

### `OSSL_LIB_CTX_new` undefined

You are linking against OpenSSL 1.x. Verify:
```bash
openssl version          # must be 3.x
pkg-config --modversion openssl
```

### `nm` shows no `C_Initialize` symbol

The compiler may have hidden it. Add to `CMakeLists.txt`:
```cmake
target_compile_options(pkcs11_backend PRIVATE -fvisibility=default)
```
Or annotate each exported function:
```c
__attribute__((visibility("default"))) CK_RV C_Initialize(CK_VOID_PTR pInitArgs)
```

### Segfault on `dlopen` / `LoadLibrary`

Ensure your `.so` does **not** have a `DT_NEEDED` entry for a conflicting libssl version:
```bash
ldd build/pkcs11_backend.so
readelf -d build/pkcs11_backend.so | grep NEEDED
```

---

## Next Steps

After your `C_Initialize` implementation passes review, the progression is:

1. **Step 4 — `C_GetInfo` / `C_GetSlotList` / `C_GetSlotInfo` / `C_GetTokenInfo`**
   Populate static descriptor structs; introduce the single virtual slot/token.

2. **Step 5 — Session management** (`C_OpenSession`, `C_CloseSession`, `C_Login`, `C_Logout`)
   Session handle allocation from `g_backend.sessions[]`; PIN verification stub.

3. **Step 6 — Object model** (`C_FindObjectsInit`, `C_FindObjects`, `C_FindObjectsFinal`, `C_GetAttributeValue`)
   In-memory object store backed by `EVP_PKEY` handles.

4. **Step 7 — Key generation & import** (`C_GenerateKeyPair`, `C_CreateObject`)
   RSA and EC key generation via `EVP_PKEY_CTX`; DER import.

5. **Step 8 — Crypto operations** (`C_SignInit`/`C_Sign`, `C_VerifyInit`/`C_Verify`)
   `EVP_DigestSign*` / `EVP_DigestVerify*` wrappers; mechanism dispatch table.

6. **Step 9 — Wrap/Unwrap & Derive** (`C_WrapKey`, `C_UnwrapKey`, `C_DeriveKey`)
   AES-KW, ECDH.

7. **Step 10 — Persistence** (optional)
   Serialize keys to encrypted files or delegate to an HSM via `ENGINE` / `OSSL_PROVIDER`.

---

*Share your `init.c` + `main.c` for Step 1 review when ready.*

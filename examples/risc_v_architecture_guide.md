# RISC-V Architecture: Complete Guide

## Philosophy & Design Principles

**RISC-V** = Open-source ISA implementing pure RISC principles with radical modularity

**Core tenets**:
1. **Minimalist base** (~40 instructions RV32I)
2. **Modular extensions** (orthogonal, optional)
3. **Open specification** (no licensing, vendor-neutral)
4. **Stable base, evolving extensions** (base frozen, extensions added)
5. **Clean-slate design** (no legacy baggage from 1970s)

**Origin**: UC Berkeley 2010 (Krste Asanović, Andrew Waterman, David Patterson)

---

## Modular Architecture

### Base ISAs (Choose ONE, mandatory)

| Base | Width | Registers | Use Case |
|------|-------|-----------|----------|
| **RV32I** | 32-bit | 31 GPRs × 32-bit | Embedded, IoT, microcontrollers |
| **RV64I** | 64-bit | 31 GPRs × 64-bit | Servers, workstations, AI accelerators |
| **RV128I** | 128-bit | 31 GPRs × 128-bit | Future (not yet finalized) |

**RV32I instructions** (~40 core instructions):
- Integer arithmetic: `add`, `sub`, `and`, `or`, `xor`, `slt`
- Shifts: `sll`, `srl`, `sra`
- Loads/Stores: `lb`, `lh`, `lw`, `sb`, `sh`, `sw`
- Branches: `beq`, `bne`, `blt`, `bge`, `bltu`, `bgeu`
- Jumps: `jal`, `jalr`
- Upper immediate: `lui`, `auipc`
- System: `ecall`, `ebreak`

**x0 register**: Hardwired to zero (reads always 0, writes ignored)

---

### Standard Extensions (Optional, Orthogonal)

**Letter-based extensions** (classical):

| Ext | Name | Purpose | Key Instructions |
|-----|------|---------|------------------|
| **M** | Multiply/Divide | Integer multiplication | `mul`, `mulh`, `div`, `rem` |
| **A** | Atomic | Synchronization primitives | `lr.w`, `sc.w`, `amoswap`, `amoadd` |
| **F** | Float | Single-precision (32-bit) | `fadd.s`, `fmul.s`, `fld`, `fst` |
| **D** | Double | Double-precision (64-bit) | `fadd.d`, `fmul.d` |
| **C** | Compressed | 16-bit instructions | Compressed versions of common ops |

**Combinations**:
- **RV32G** = RV32IMAFD (General-purpose)
- **RV64GC** = RV64IMAFD + C (Common server config)

**Advanced extensions**:

| Ext | Name | Purpose | Status |
|-----|------|---------|--------|
| **V** | Vector | SIMD, data parallelism | Ratified (critical for AI/ML) |
| **B** | Bit manipulation | Cryptography, compression | Ratified |
| **P** | Packed SIMD | DSP operations | Draft |
| **H** | Hypervisor | Virtualization support | Ratified |
| **Q** | Quad-precision | 128-bit floating-point | Ratified |
| **J** | JIT | Dynamic translation support | Proposed |

**AI/ML Matrix Extensions** (in development):
- **IME**: Integrated Matrix Extension
- **VME**: Matrix-in-Vector Extension  
- **AME**: Attached Matrix Extension
- Goal: Hardware matrix operations for transformers, deep learning

**Extension naming**:
- **Z prefix**: Standard specialized extensions (`Zifencei`, `Zicsr`)
- **S prefix**: Supervisor-level extensions
- **X prefix**: Custom/vendor extensions (non-standard)

---

## Instruction Formats (6 Types)

**All share**: 
- Opcode at bits [6:0] (7 bits)
- Register fields at consistent positions (enables parallel decode)

### Format Breakdown

```
R-type: Register-register operations
┌─────────┬─────┬─────┬──────┬─────┬────────┐
│ funct7  │ rs2 │ rs1 │funct3│ rd  │ opcode │
│  [7]    │ [5] │ [5] │ [3]  │ [5] │  [7]   │
└─────────┴─────┴─────┴──────┴─────┴────────┘
Example: add x3, x1, x2  (x3 = x1 + x2)

I-type: Immediate and loads
┌──────────────┬─────┬──────┬─────┬────────┐
│  imm[11:0]   │ rs1 │funct3│ rd  │ opcode │
│     [12]     │ [5] │ [3]  │ [5] │  [7]   │
└──────────────┴─────┴──────┴─────┴────────┘
Example: addi x3, x1, 100  (x3 = x1 + 100)
         lw x3, 8(x1)      (x3 = memory[x1+8])

S-type: Store operations
┌─────────┬─────┬─────┬──────┬─────────┬────────┐
│imm[11:5]│ rs2 │ rs1 │funct3│imm[4:0] │ opcode │
│   [7]   │ [5] │ [5] │ [3]  │   [5]   │  [7]   │
└─────────┴─────┴─────┴──────┴─────────┴────────┘
Example: sw x2, 8(x1)  (memory[x1+8] = x2)

B-type: Branches (conditional)
┌──┬──────┬─────┬─────┬──────┬────┬──┬────────┐
│im│imm   │ rs2 │ rs1 │funct3│imm │im│ opcode │
│12│[10:5]│ [5] │ [5] │ [3]  │[4:1│11│  [7]   │
└──┴──────┴─────┴─────┴──────┴────┴──┴────────┘
Example: beq x1, x2, offset  (if x1==x2, PC += offset)

U-type: Upper immediate (20-bit constant)
┌────────────────────┬─────┬────────┐
│     imm[31:12]     │ rd  │ opcode │
│        [20]        │ [5] │  [7]   │
└────────────────────┴─────┴────────┘
Example: lui x1, 0x12345  (x1 = 0x12345000)

J-type: Jumps (unconditional)
┌──┬────────┬──┬──────┬─────┬────────┐
│im│imm     │im│imm   │ rd  │ opcode │
│20│[10:1] │11│[19:12│ [5] │  [7]   │
└──┴────────┴──┴──────┴─────┴────────┘
Example: jal x1, offset  (x1 = PC+4; PC += offset)
```

**Key insight**: Source registers (`rs1`, `rs2`) always at same positions → decode can read registers in parallel with instruction decode.

---

## Register Architecture

### Integer Registers (31 + 1)

| Register | ABI Name | Purpose | Saved by |
|----------|----------|---------|----------|
| x0 | zero | Hardwired 0 | N/A |
| x1 | ra | Return address | Caller |
| x2 | sp | Stack pointer | Callee |
| x3 | gp | Global pointer | N/A |
| x4 | tp | Thread pointer | N/A |
| x5-x7 | t0-t2 | Temporaries | Caller |
| x8 | s0/fp | Saved/Frame pointer | Callee |
| x9 | s1 | Saved register | Callee |
| x10-x11 | a0-a1 | Arguments/return values | Caller |
| x12-x17 | a2-a7 | Arguments | Caller |
| x18-x27 | s2-s11 | Saved registers | Callee |
| x28-x31 | t3-t6 | Temporaries | Caller |

**Calling convention**:
- Arguments: a0-a7 (x10-x17)
- Return values: a0-a1
- Caller-saved: Caller must save before function call
- Callee-saved: Function must preserve

### Floating-Point Registers (with F/D extensions)

32 registers: **f0-f31**
- With F: 32-bit single-precision
- With D: 64-bit double-precision (backward compatible with F)

---

## Memory Model

### Addressing
- **Byte-addressed**: Each byte has unique address
- **Little-endian**: LSB at lowest address (mandatory)
- **Alignment**: Natural alignment recommended (4-byte for words), misalignment supported but slower

### Memory Ordering (Relaxed Model)

**Default**: Memory operations may execute out-of-order

**FENCE instruction**: Enforce ordering
```assembly
fence [predecessor], [successor]
```
- Predecessor/successor: r (read), w (write), i (input), o (output)
- Example: `fence rw, rw` - Full memory barrier

**Atomic operations** (A extension):
- **LR/SC**: Load-Reserved/Store-Conditional
  ```assembly
  lr.w rd, (rs1)      # Load and reserve
  sc.w rd, rs2, (rs1) # Store if still reserved (rd=0 success, 1 fail)
  ```
- **AMO**: Atomic Memory Operations
  - `amoswap`, `amoadd`, `amoand`, `amoor`, `amoxor`
  - `amomin`, `amomax`, `amominu`, `amomaxu`

---

## Privilege Levels (3-Level Hierarchy)

| Level | Mode | Privilege | Mandatory |
|-------|------|-----------|-----------|
| 0 | **U** (User) | Application | No |
| 1 | **S** (Supervisor) | OS kernel | No |
| 3 | **M** (Machine) | Firmware/bootloader | **Yes** |

**Note**: Level 2 (Hypervisor) reserved, uses **H extension** for virtualization

**CSRs** (Control and Status Registers):
- Machine mode: `mstatus`, `mtvec`, `mepc`, `mcause`
- Supervisor mode: `sstatus`, `stvec`, `sepc`, `scause`
- User mode: Limited CSR access

**Privilege escalation**: 
- Traps/interrupts → higher privilege
- `mret`/`sret` → return to lower privilege

---

## Vector Extension (V) - Critical for AI/ML

**Variable-length vectors**: VLEN (vector length) implementation-defined
- Common: VLEN = 128, 256, 512, 1024 bits
- Software queries VLEN at runtime

**Vector registers**: 32 vector registers (v0-v31)

**Key concepts**:
- **SEW** (Selected Element Width): 8, 16, 32, 64 bits
- **LMUL** (Length Multiplier): Group registers for longer vectors
- **vl** (vector length): Actual number of elements processed

**Example**:
```assembly
vsetvli t0, a0, e32, m1  # Set vector length, SEW=32, LMUL=1
vle32.v v1, (a1)         # Vector load
vle32.v v2, (a2)         # Vector load
vadd.vv v3, v1, v2       # Vector add
vse32.v v3, (a3)         # Vector store
```

**Applications**: Image processing, neural networks, scientific computing

---

## Compressed Extension (C)

**16-bit instructions** for common operations:
- Reduces code size ~25-30%
- Must be aligned on 2-byte boundaries
- Can mix with 32-bit instructions freely

**Examples**:
- `c.add rd, rs` ≡ `add rd, rd, rs` (32-bit)
- `c.li rd, imm` ≡ `addi rd, x0, imm`
- `c.lw rd, offset(rs)` ≡ `lw rd, offset(rs)`

**Restrictions**: 
- Limited to common register sets (x8-x15, sp, ra)
- Small immediate values

---

## Open ISA Advantages

### No Licensing Costs
- Free to implement, modify, extend
- No royalties per chip
- Critical for startups, academics, emerging markets

### Transparent Specification
- Complete documentation publicly available
- Reference implementations open-source
- No hidden "implementation-defined" behaviors

### Customization Freedom
- Add custom X extensions without approval
- Domain-specific optimizations (crypto, AI, DSP)
- No vendor lock-in

### Academic & Research
- Teaching architecture courses
- FPGA prototyping
- Novel microarchitecture research

### Industry Adoption
- **SiFive**: High-performance cores (X280, X390 with vector)
- **Alibaba**: T-Head processors for cloud/edge
- **Western Digital**: Storage controllers
- **NVIDIA**: Replacing Falcon microcontrollers in GPUs
- **Google**: Custom accelerators

---

## Practical Implementation Sizes

**Minimal** (RV32I):
- ~40 instructions
- ~2,500 gates (simple implementation)
- Use case: Ultra-low-power IoT

**Embedded** (RV32IMC):
- +Multiply/Divide, Compressed
- ~5,000 gates
- Use case: Microcontrollers

**Application** (RV64GC):
- Full general-purpose
- ~50,000 gates (in-order)
- ~200,000 gates (out-of-order)
- Use case: Linux systems

**AI/ML** (RV64GCV + Matrix):
- Vector + Matrix extensions
- 1M+ gates with large vector units
- Use case: Edge AI, neural network inference

---

## Key Numbers to Remember

| Metric | Value |
|--------|-------|
| Base instruction length | 32 bits |
| Compressed instruction length | 16 bits |
| Integer registers | 31 + 1 (x0 = zero) |
| FP registers (F/D) | 32 |
| Vector registers (V) | 32 |
| Instruction formats | 6 (R, I, S, B, U, J) |
| Privilege levels | 3 (M, S, U) |
| RV32I base instructions | ~40 |
| Opcode field size | 7 bits [6:0] |
| Register field size | 5 bits (2³² = 32 regs) |

---

## Design Decisions (Why RISC-V is Different)

### 1. Clean Slate
- No backward compatibility with legacy ISAs
- Learned from 40 years of ARM, x86, MIPS, SPARC mistakes

### 2. Explicit x0 = 0
- Simplifies many operations
- `mv rd, rs` ≡ `addi rd, rs, 0`
- `nop` ≡ `addi x0, x0, 0`

### 3. No Delay Slots
- MIPS had branch delay slots (legacy from pipeline)
- RISC-V: Cleaner, compiler doesn't need tricks

### 4. No Condition Codes
- x86/ARM have NZVC flags
- RISC-V: Branches compare registers directly
- Simpler pipeline, no flag dependencies

### 5. Weak Memory Model
- Allows aggressive hardware reordering
- Explicit FENCE for synchronization
- Better performance on multicore

### 6. Modular FP
- Can have integer-only processor (RV32I)
- Or separate F, D, Q extensions
- Not all systems need floating-point

---

## Common Configurations

**MCU** (Microcontroller):
```
RV32IMC
- 32-bit
- Multiply/Divide
- Compressed instructions
- ~10,000 gates, <1mW
```

**Linux Desktop**:
```
RV64GC
- 64-bit
- General-purpose (IMAFD)
- Compressed instructions
- MMU for virtual memory
```

**AI Edge Device**:
```
RV64GCV + IME
- 64-bit
- General-purpose + Compressed
- Vector extension (VLEN=512)
- Integrated Matrix Extension
- Neural network inference
```

**HPC/Server**:
```
RV64GCVH + Custom
- 64-bit, full extensions
- Vector (VLEN=1024+)
- Hypervisor support
- Custom X extensions for domain
```

---

## Critical Takeaways

1. **Modularity is the killer feature**: Base + optional extensions prevents bloat
2. **Open = innovation without permission**: Anyone can build custom RISC-V chips
3. **Stable base, evolving extensions**: RV32I/RV64I frozen forever, new extensions added
4. **6 instruction formats** enable efficient encoding while maintaining decode simplicity
5. **Load-store architecture** with large register file minimizes memory traffic
6. **Weak memory model** enables aggressive multicore optimization
7. **Vector (V) extension** is critical for modern AI/ML workloads
8. **No legacy baggage**: Clean design incorporating 40 years of ISA lessons

---

## Further Study

**Official Specifications**:
- RISC-V International: https://riscv.org/specifications/
- User-Level ISA Manual (Volume I)
- Privileged Architecture Manual (Volume II)

**Key Papers**:
- Asanović & Patterson (2014): "Instruction Sets Should Be Free: The Case for RISC-V"
- Waterman et al. (2016): "Design of the RISC-V Instruction Set Architecture"

**Implementations**:
- BOOM (Berkeley Out-of-Order Machine)
- Rocket Chip Generator
- SiFive cores (commercial)

**Tools**:
- GNU Toolchain (gcc, binutils)
- LLVM/Clang
- QEMU emulator
- Spike ISA simulator

---

*Version: 1.0 | April 2026*

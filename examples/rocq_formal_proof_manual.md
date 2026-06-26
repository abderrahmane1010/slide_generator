# The Rocq Manual: Formal Proof from First Principles

---

*For the programmer who suspects that mathematics should be checkable by machine, for the mathematician who suspects that proofs should be programs, and for anyone who has tried to read a proof assistant tutorial and found it answered no fundamental questions.*

---

## Table of Contents

- [Preface](#preface)
- **Part I — Orientation**
  - [Chapter 1 — What Rocq Is](#chapter-1--what-rocq-is)
  - [Chapter 2 — The Duality: Proofs as Programs](#chapter-2--the-duality-proofs-as-programs)
  - [Chapter 3 — The Four Doors](#chapter-3--the-four-doors)
  - [Chapter 4 — What Checking Means](#chapter-4--what-checking-means)
- **Part II — Anatomy**
  - [Chapter 5 — Terms and Their Kinds](#chapter-5--terms-and-their-kinds)
  - [Chapter 6 — Types and Sorts](#chapter-6--types-and-sorts)
  - [Chapter 7 — The Calculus of Constructions](#chapter-7--the-calculus-of-constructions)
  - [Chapter 8 — Inductive Types](#chapter-8--inductive-types)
  - [Chapter 9 — Universes](#chapter-9--universes)
- **Part III — Configuration and Composition**
  - [Chapter 10 — Definitions and Declarations](#chapter-10--definitions-and-declarations)
  - [Chapter 11 — Modules and Sections](#chapter-11--modules-and-sections)
  - [Chapter 12 — The Vernacular](#chapter-12--the-vernacular)
  - [Chapter 13 — Notations and Syntax Extensions](#chapter-13--notations-and-syntax-extensions)
- **Part IV — Mechanism**
  - [Chapter 14 — Reduction and Computation](#chapter-14--reduction-and-computation)
  - [Chapter 15 — Unification and Inference](#chapter-15--unification-and-inference)
  - [Chapter 16 — The Kernel](#chapter-16--the-kernel)
  - [Chapter 17 — Extraction](#chapter-17--extraction)
- **Part V — Propositions and Logic**
  - [Chapter 18 — Prop vs Set vs Type](#chapter-18--prop-vs-set-vs-type)
  - [Chapter 19 — Connectives as Types](#chapter-19--connectives-as-types)
  - [Chapter 20 — Equality](#chapter-20--equality)
  - [Chapter 21 — Classical vs Constructive Logic](#chapter-21--classical-vs-constructive-logic)
- **Part VI — Tactics**
  - [Chapter 22 — What a Tactic Is](#chapter-22--what-a-tactic-is)
  - [Chapter 23 — The Core Tactics](#chapter-23--the-core-tactics)
  - [Chapter 24 — Rewriting](#chapter-24--rewriting)
  - [Chapter 25 — Induction Tactics](#chapter-25--induction-tactics)
  - [Chapter 26 — Automation](#chapter-26--automation)
  - [Chapter 27 — Ltac and Tactic Programming](#chapter-27--ltac-and-tactic-programming)
- **Part VII — Inductive Families and Dependent Types**
  - [Chapter 28 — Dependent Types](#chapter-28--dependent-types)
  - [Chapter 29 — Inductive Families](#chapter-29--inductive-families)
  - [Chapter 30 — Pattern Matching and Dependent Elimination](#chapter-30--pattern-matching-and-dependent-elimination)
  - [Chapter 31 — Fixpoints and Termination](#chapter-31--fixpoints-and-termination)
- **Part VIII — Libraries and Mathematics**
  - [Chapter 32 — The Standard Library](#chapter-32--the-standard-library)
  - [Chapter 33 — MathComp and Algebraic Hierarchy](#chapter-33--mathcomp-and-algebraic-hierarchy)
  - [Chapter 34 — Typeclasses and Canonical Structures](#chapter-34--typeclasses-and-canonical-structures)
  - [Chapter 35 — Setoids and Rewriting Modulo Equivalence](#chapter-35--setoids-and-rewriting-modulo-equivalence)
- **Part IX — Production**
  - [Chapter 36 — Proof Engineering](#chapter-36--proof-engineering)
  - [Chapter 37 — Axioms and Trust](#chapter-37--axioms-and-trust)
  - [Chapter 38 — Performance and Proof Size](#chapter-38--performance-and-proof-size)
  - [Chapter 39 — Proof Maintenance](#chapter-39--proof-maintenance)
- **Part X — Tooling and Workflow**
  - [Chapter 40 — The Rocq Toolchain](#chapter-40--the-rocq-toolchain)
  - [Chapter 41 — Editors and Proof Mode](#chapter-41--editors-and-proof-mode)
  - [Chapter 42 — Building Projects](#chapter-42--building-projects)
  - [Chapter 43 — Search and Documentation](#chapter-43--search-and-documentation)
- **Part XI — Mastery**
  - [Chapter 44 — Debugging Proofs](#chapter-44--debugging-proofs)
  - [Chapter 45 — Architectural Patterns](#chapter-45--architectural-patterns)
  - [Chapter 46 — Common Errors and Their Meaning](#chapter-46--common-errors-and-their-meaning)
  - [Chapter 47 — How to Actually Learn Rocq](#chapter-47--how-to-actually-learn-rocq)
- **Appendices**
  - [Appendix A — Core Vernacular Reference](#appendix-a--core-vernacular-reference)
  - [Appendix B — Tactic Reference](#appendix-b--tactic-reference)
  - [Appendix C — Reduction Strategy Reference](#appendix-c--reduction-strategy-reference)
  - [Appendix D — Ltac Cheat Sheet](#appendix-d--ltac-cheat-sheet)
  - [Appendix E — Glossary](#appendix-e--glossary)

---

## Preface

This manual is for people who want to understand Rocq, not just use it. There is a difference. You can follow a tutorial, learn a handful of tactics, and produce checked proofs without understanding what is actually happening. Many people do this. Their proofs are fragile, their tactics are cargo-culted, and they cannot debug a failing proof without trial and error.

This manual teaches the foundation. You will learn what a term is, why types and propositions are the same thing, how the kernel verifies your proof, what a tactic actually does to the proof state, and why dependent types are both the power and the difficulty of Rocq. By the end, you should be able to look at an error message and know—not guess—what it means.

The progression is deliberate. Part I orients you to what Rocq is and is not. Part II gives you the taxonomy of every entity you will manipulate. Parts III and IV show how those entities are arranged and how the machine processes them. Parts V through VIII cover the four major domains: logic, tactics, dependent types, and library mathematics. Part IX shows what changes under production conditions. Part X covers the day-to-day tooling. Part XI synthesizes everything into principles for mastery.

Read Parts I–IV before anything else. The rest can be read in order or consulted by need—but the vocabulary built in Part II is assumed everywhere.

Rocq was formerly known as Coq. As of 2024, the project renamed itself to Rocq. All concepts are identical; only the name changed. This manual uses Rocq throughout. Source code, library names, and official documentation still carry the Coq name in many places; context will make this clear.

---

## Part I — Orientation

---

## Chapter 1 — What Rocq Is

Rocq is a proof assistant. It is not a theorem prover. The distinction is load-bearing.

A theorem prover takes a statement and tries to find a proof automatically. It may succeed or fail. When it fails, it gives you nothing useful. Rocq is different: it is an interactive system in which *you* construct the proof, and the machine *checks* that your construction is correct. The machine never guesses; you never trust without verification.

What Rocq actually does is type-checking. You write a term. Rocq verifies that the term has the type you claimed. Nothing more. The entire edifice of formal mathematics rests on that one operation.

This sounds minimal. It is. It is also sufficient.

The reason it is sufficient is the Curry-Howard correspondence, which Chapter 2 explains. For now, accept this: in Rocq, *every proof is a program* and *every proposition is a type*. Checking a proof is checking whether a program has a given type. Rocq's kernel is, at its core, a type-checker for a very expressive type system called the Calculus of Inductive Constructions (CIC).

Rocq has three faces that beginners confuse:

```
┌─────────────────────────────────────────────────────────┐
│                         ROCQ                            │
├─────────────────┬──────────────────┬────────────────────┤
│  Proof assistant│  Programming     │  Specification     │
│                 │  language        │  language          │
│  You prove      │  You write       │  You describe      │
│  theorems       │  certified       │  systems           │
│                 │  programs        │                    │
└─────────────────┴──────────────────┴────────────────────┘
```

These three faces are not separate modes. They are the same system viewed from different angles. A certified program is a program paired with a proof of its correctness. A specification is a type. A theorem is a type. A proof is a program. The unification is total.

Rocq's expressive power comes from *dependent types*: types that can depend on values. In most programming languages, types and values are separate. In Rocq, a type can mention a specific value. This lets you write types that express precise specifications — not just "this is a list" but "this is a sorted list of length n". The price of this power is complexity, which Parts II and VII address systematically.

> **Principle 1.** *Rocq checks; you construct. Automation assists, but the proof is yours.*

---

## Chapter 2 — The Duality: Proofs as Programs

The most important fact about Rocq is the Curry-Howard correspondence. Everything else follows from it. Read this chapter twice.

The correspondence states: **propositions are types, and proofs are programs of those types.**

This is not a metaphor. It is not an analogy. It is an identity. The same mathematical object serves as both a proposition (when you care about its truth) and a type (when you care about its elements).

Here is the correspondence table. Memorize this.

```
┌─────────────────────────┬────────────────────────────────┐
│  Logic                  │  Type Theory / Programming     │
├─────────────────────────┼────────────────────────────────┤
│  Proposition P          │  Type P                        │
│  Proof of P             │  Term of type P                │
│  P is true              │  P is inhabited (has a term)   │
│  P is false             │  P is empty (has no terms)     │
│  P implies Q            │  Function type P → Q           │
│  P and Q                │  Product type P × Q            │
│  P or Q                 │  Sum type P + Q                │
│  Not P                  │  Function type P → False        │
│  For all x, P(x)        │  Dependent product ∀ x, P x    │
│  There exists x, P(x)   │  Dependent sum Σ x, P x        │
│  Universal quantifier   │  Dependent function type       │
│  Existential quantifier │  Dependent pair type           │
└─────────────────────────┴────────────────────────────────┘
```

The consequences are immediate and non-obvious.

**Consequence 1: Proving is programming.** When you prove `P ∧ Q`, you are writing a program that produces a pair. When you prove `P → Q`, you are writing a function. The tactic mode is just a way of writing programs interactively, one step at a time.

**Consequence 2: A proof is a certificate.** The term you produce is a concrete object. Rocq's kernel can re-check it at any time, on any machine, without re-running the tactics that generated it. The proof is not a sequence of steps; it is a value.

**Consequence 3: False propositions have no proofs.** The type `False` is empty — it has no inhabitants. You cannot produce a term of type `False` without cheating (using an axiom or exploiting an inconsistency). If Rocq accepts your proof, it accepted a term of that type. If the type is `False`, something is wrong with your axioms.

**Consequence 4: Types classify evidence.** `True` is a type with exactly one element. `False` is a type with no elements. Propositional equality `a = b` is a type with at most one element — either the reflexivity proof exists, or it does not.

The duality is complete. There is no third thing. Every concept from logic has a corresponding concept from type theory, and they are the same concept viewed through different lenses.

> **Principle 2.** *A proof is a program. A proposition is a type. These are not analogies—they are definitions.*

---

## Chapter 3 — The Four Doors

There are exactly four kinds of thing you build in Rocq. Everything else is abbreviation, notation, or automation layered on top of these four.

```
┌──────────────────────────────────────────────────┐
│                   ROCQ ENTITIES                  │
├───────────────┬──────────────────────────────────┤
│  Terms        │  The values and programs         │
│  Types        │  The types of terms              │
│  Propositions │  The types you prove             │
│  Proofs       │  The terms that inhabit props    │
└───────────────┴──────────────────────────────────┘
```

But as Chapter 2 showed, propositions *are* types and proofs *are* terms. So the four reduce to two: **terms** and **types**. And types are themselves terms (of a sort). So in the end there is exactly one kind of thing: **terms**, arranged in a hierarchy of sorts.

This reduction is not just philosophy. It means:

1. The syntax for writing a function and the syntax for writing a proof are the same.
2. The rules for forming types and the rules for forming propositions are the same.
3. The kernel's type-checker verifies everything uniformly.

The four "doors" through which beginners typically enter Rocq correspond to four use cases:

**Door 1 — Functional programming.** You write functions, data types, recursive programs. Rocq is a strongly typed functional language. This door misleads: you will immediately hit limitations (no general recursion, everything must terminate) that make no sense without understanding the logic.

**Door 2 — Propositional logic.** You prove statements about `True`, `False`, `∧`, `∨`, `→`. This is the introductory proof experience. It builds correct intuitions but feels toy-like.

**Door 3 — Mathematical structures.** You formalize integers, lists, trees, and prove properties. This is the most common serious use case.

**Door 4 — Program certification.** You write a program and prove a specification. This is the most industrially valuable use case, and the most technically demanding.

All four doors lead to the same room. The sooner you understand that room directly (Part II), the less you will be confused by the entry experience.

> **Principle 3.** *There is one kind of entity in Rocq: terms. Types are terms. Proofs are terms. The entire system is one language.*

---

## Chapter 4 — What Checking Means

When Rocq accepts a proof, what has been established? This is not a rhetorical question. It has a precise answer, and the answer matters for how much you should trust Rocq.

Rocq establishes this: **the term you wrote has the type you claimed, under the assumptions you declared, relative to the axioms in your environment.**

Nothing more. Nothing less.

This has four implications.

**Implication 1: The result is only as sound as the axioms.** If you add `Axiom everything_is_true : ∀ P, P.` then Rocq will happily accept proofs of `False`. The kernel is sound relative to the axioms; the axioms are your responsibility. Chapter 37 covers the standard axioms and what they commit you to.

**Implication 2: The kernel is the trusted base.** Rocq has a small kernel—a few thousand lines of OCaml—that does the actual type-checking. Everything else (tactics, automation, libraries) is untrusted in the sense that bugs in them produce incorrect proof terms, which the kernel then rejects. The kernel's correctness is the only thing that needs to be trusted.

**Implication 3: Tactics can be wrong, but proofs cannot.** A tactic that has a bug will either produce an invalid term (rejected by the kernel) or produce a valid term that is not what you intended. The first is safe — you get an error. The second is a conceptual mistake on your part — you asked for the wrong thing. Rocq cannot know what you intended.

**Implication 4: The proof term is the proof.** The tactic script is a *description of how to generate the proof term*. The proof term itself is the certificate. This is why you can sometimes write proofs as direct terms (using `exact`) instead of tactics. Tactics are a user interface.

```
┌─────────────────────────────────────────────┐
│              PROOF PIPELINE                 │
│                                             │
│   Tactic script                             │
│        ▼                                    │
│   Proof term  (generated by tactics)        │
│        ▼                                    │
│   Kernel type-checker  (trusted base)       │
│        ▼                                    │
│   Accept / Reject                           │
└─────────────────────────────────────────────┘
```

The gap between "the kernel accepted it" and "this is mathematically true" is exactly the gap between formal and informal mathematics. Rocq closes the formal part. The informal part—did you formalize the right statement?—remains your responsibility.

> **Principle 4.** *Rocq verifies syntax; you verify meaning. Accepting a proof is not the same as being right.*

---

## Part II — Anatomy

---

## Chapter 5 — Terms and Their Kinds

A term is any syntactic object that Rocq can type-check. Functions, numbers, proofs, types, propositions, data structures—all are terms. The grammar of terms is small.

There are exactly six forms of term in the core calculus:

```
┌────────────────┬─────────────────────────────────────────────────┐
│  Form          │  Meaning                                        │
├────────────────┼─────────────────────────────────────────────────┤
│  x             │  Variable — a name bound in scope               │
│  c             │  Constant — a name defined globally             │
│  fun x : T ⇒ t │  Lambda abstraction — a function               │
│  t u           │  Application — apply function t to argument u   │
│  ∀ x : T, U    │  Dependent product — the type of functions      │
│  let x := t in u│  Local definition                             │
└────────────────┴─────────────────────────────────────────────────┘
```

Inductive types (Chapter 8) and their constructors and match expressions are added on top of this core. Everything else in Rocq syntax—notations, implicit arguments, typeclasses—desugars into these six forms plus inductive types.

**Variables** are names bound by `fun` or `∀` or `let`. They are replaced by their values when computing. **Constants** are names defined at the top level with `Definition`, `Lemma`, `Fixpoint`, and so on. They have definitions stored in the environment.

**Lambda abstraction** `fun x : T ⇒ t` is a function with parameter `x` of type `T` and body `t`. The body may use `x`. This is the introduction form for function types.

**Application** `t u` applies function `t` to argument `u`. The result type is the result type of `t`'s function type, with `x` replaced by `u`. Application is the elimination form for function types.

**The dependent product** `∀ x : T, U` is the type of functions from `T` to `U`, where `U` may mention `x`. When `U` does not mention `x`, this is written `T → U` and is the ordinary function type. When `U` does mention `x`, this is a *dependent* function type. This is the core innovation of dependent type theory.

Hold this picture in your mind:

```
  Type of a function that takes n : nat and returns a proof
  that n is even:

  ∀ n : nat, IsEven n

  This is a dependent product. The result type (IsEven n)
  depends on the input value (n).

  Without dependence, this would only be: nat → Prop
  which says "there is some proposition" but not which one.
```

> **Principle 5.** *Every term in Rocq is built from six primitive forms. Mastery is knowing which form every expression desugars to.*

---

## Chapter 6 — Types and Sorts

Every term has a type. Types are themselves terms, so types have types too. The type of a type is called its **sort**.

There are three sorts built into Rocq:

```
┌──────────────────────────────────────────────────────────────────┐
│                          SORT HIERARCHY                          │
│                                                                  │
│         Type₀   Type₁   Type₂   ...  (universe tower)           │
│              \    |    /                                         │
│               \   |   /                                          │
│                Set                                               │
│                  |                                               │
│                Prop                                              │
│                                                                  │
│  Prop  — the sort of propositions (proof-irrelevant)            │
│  Set   — the sort of data types (computational)                 │
│  Type  — a universe that contains Prop, Set, and other Types    │
└──────────────────────────────────────────────────────────────────┘
```

**Prop** is the sort of logical propositions. A term of sort `Prop` is a proposition. A proof of proposition `P : Prop` is a term of type `P`. Propositions in `Prop` are *proof-irrelevant*: Rocq does not care which proof of `P` you provide, only that one exists. This has consequences for computation and extraction (Chapters 17 and 18).

**Set** is the sort of data types. `nat : Set`, `bool : Set`, `list nat : Set`. Programs that compute live in `Set`. Extraction (Chapter 17) produces OCaml or Haskell programs from `Set`-level terms.

**Type** is a universe. `Prop : Type`, `Set : Type`, `Type₀ : Type₁`, and so on. The universe hierarchy exists to avoid Russell's paradox: without it, `Type : Type` would be inconsistent.

In practice, you write `Type` and Rocq infers the universe level. Explicit universe levels appear only when you need to work with universe polymorphism (Chapter 9).

The key table:

| Sort | Contains | Proof-relevant? | Extractable? |
|------|----------|-----------------|--------------|
| `Prop` | Propositions | No | No |
| `Set` | Data types | Yes | Yes |
| `Type` | Everything | Yes | Yes |

> **Principle 6.** *Every term lives at a level: value, type, or sort. Confusion about which level you are at is the source of half of all beginner errors.*

---

## Chapter 7 — The Calculus of Constructions

Rocq's theoretical foundation is the Calculus of Inductive Constructions (CIC). The "Calculus of Constructions" (CC) is the core without inductive types. Understanding CC is understanding the heart of Rocq.

CC has exactly two rules for forming types of terms:

**Rule 1 — Abstraction.** If `t : T → U` and `u : T`, then `t u : U`.

**Rule 2 — Dependent abstraction.** If `T : s₁` (where s₁ is a sort) and `U : s₂` (where s₂ is a sort), then `∀ x : T, U : s₃`, where s₃ is determined by the *product rule* for (s₁, s₂).

The product rules determine what kinds of functions can exist:

```
┌─────────────────┬─────────────────┬─────────────────┐
│  From (s₁)      │  To (s₂)        │  Result (s₃)    │
├─────────────────┼─────────────────┼─────────────────┤
│  Prop           │  Prop           │  Prop           │
│  Set            │  Prop           │  Prop           │
│  Type           │  Prop           │  Prop           │
│  Prop           │  Set/Type       │  Set/Type       │
│  Set            │  Set/Type       │  Set/Type       │
│  Type           │  Type           │  Type           │
└─────────────────┴─────────────────┴─────────────────┘
```

The crucial rule: a function from anything to `Prop` lives in `Prop`. This is why universally quantified propositions (`∀ n : nat, P n`) are propositions—because `P n : Prop` makes the whole product land in `Prop`.

The rule that propositions can depend on values but produce propositions (not data) is the mechanism behind proof-irrelevance: a function `f : nat → Prop` is a proposition-valued function, and its "output" (a proof) need not be preserved during computation.

CC is confluent and strongly normalizing (without inductive types). Every term reduces to a unique normal form. This is what makes type-checking decidable.

> **Principle 7.** *The typing rules of CIC are not conventions—they are the definition of what it means for a proof to be correct. There is no appeal beyond them.*

---

## Chapter 8 — Inductive Types

Inductive types are the mechanism by which new types are introduced in Rocq. All data types—natural numbers, lists, trees, propositions with logical structure—are inductive.

An inductive type is defined by:

1. A **name** and **sort**.
2. A list of **constructors**, each with a type.

The classic example:

```rocq
Inductive nat : Set :=
  | O : nat
  | S : nat → nat.
```

This defines:
- A type `nat : Set`
- A constructor `O : nat` (zero)
- A constructor `S : nat → nat` (successor)

The meaning: `nat` is the smallest type containing `O` and closed under `S`. Every element of `nat` is either `O` or `S (S (S ... O ...))` for some number of `S` applications.

Inductive types come in four varieties:

```
┌────────────────────────────────────────────────────────────────┐
│                   INDUCTIVE VARIETIES                          │
├─────────────────────┬──────────────────────────────────────────┤
│  Non-recursive      │  Finite types: bool, unit, Empty_set     │
│  Simple recursive   │  nat, list, binary trees                 │
│  Parameterized      │  list (A : Type), option (A : Type)      │
│  Indexed (families) │  Vector (A : Type) (n : nat)             │
└─────────────────────┴──────────────────────────────────────────┘
```

The last variety—indexed inductive types, called **inductive families**—is where dependent types become essential. Chapter 29 covers them in depth.

The **recursion principle** of an inductive type is automatically generated. For `nat`, it is:

```rocq
nat_rect : ∀ (P : nat → Type),
  P O →
  (∀ n : nat, P n → P (S n)) →
  ∀ n : nat, P n
```

This is the Curry-Howard reading of mathematical induction. `P` is the predicate to prove. You provide the base case and the inductive step, and you get a proof for all `n`. Tactics like `induction` call this principle automatically.

The positivity condition is the crucial constraint: constructors of inductive type `T` may only mention `T` in positive positions (not as the argument to a function). Violating this would permit the construction of inconsistent types. Rocq's kernel enforces this check.

> **Principle 8.** *Every data type in Rocq is an inductive type. The constructors define what values exist; the recursor defines how to use them.*

---

## Chapter 9 — Universes

The type of `nat` is `Set`. The type of `Set` is `Type`. The type of `Type` is `Type`—but a *larger* `Type`. Rocq manages an infinite tower of universes `Type₀ : Type₁ : Type₂ : ...` to avoid inconsistency.

In daily use, you write `Type` and Rocq infers the level, introducing universe variables and checking that the constraints are satisfiable. This usually works invisibly. When it does not, you see the error `Universe inconsistency`.

**Universe polymorphism** allows definitions to work at multiple universe levels. You declare:

```rocq
Universe u.
Definition id@{u} (A : Type@{u}) (x : A) : A := x.
```

This `id` works for `A : Type@{u}` for any universe level `u`. Without universe polymorphism, you would need a separate `id` for each level, or you would be forced to use a fixed level and lose generality.

The key principle: **impredicativity of Prop**. The sort `Prop` is impredicative: `∀ P : Prop, P` is itself in `Prop`. This allows quantifying over all propositions within `Prop`. `Set` and `Type` are not impredicative by default (though `Set` can be made so with a flag).

Impredicativity of `Prop` enables Church-encoded propositions and makes many logical developments more compact. It also requires care: impredicativity combined with some axioms can cause inconsistency.

The practical consequence for most users: avoid mixing `Set` and `Prop` in ways that require one to contain the other. Use `Type` when you need generality. The universe checker will tell you when you have gone wrong.

> **Principle 9.** *Universe levels are Rocq's mechanism against self-reference. Every time you write Type, Rocq infers a level. When levels conflict, the error is yours to interpret.*

---

## Part III — Configuration and Composition

---

## Chapter 10 — Definitions and Declarations

A Rocq file is a sequence of **vernacular commands**. The vernacular is the top-level language in which you declare things. Terms are the inner language; vernacular commands are the outer one.

There are exactly five things you can do with a name in Rocq:

```
┌──────────────────┬──────────────────────────────────────────────┐
│  Command         │  What it does                                │
├──────────────────┼──────────────────────────────────────────────┤
│  Definition      │  Binds a name to a term transparently        │
│  Lemma/Theorem   │  Binds a name to a proof term (opaque)       │
│  Fixpoint        │  Binds a name to a recursive function        │
│  Inductive       │  Defines a new inductive type                │
│  Axiom/Parameter │  Declares a name with a type, no definition  │
└──────────────────┴──────────────────────────────────────────────┘
```

**Transparent vs opaque** is the critical distinction. A `Definition` is transparent: Rocq can unfold the name and replace it with its body during type-checking. A `Lemma` proved with `Qed` is opaque: Rocq knows only its type, not its proof term. This matters for computation—if you need the definition to reduce, it must be transparent.

`Proof` … `Qed` introduces a **proof mode** in which you write tactics. `Defined` instead of `Qed` makes the proof transparent (its body can be unfolded). Use `Defined` for definitions that need to compute; use `Qed` for lemmas whose internal structure should be hidden.

```rocq
(* Transparent: body is visible *)
Definition double (n : nat) : nat := n + n.

(* Opaque: only the type is visible *)
Lemma double_comm : ∀ n m, double n + double m = double m + double n.
Proof. intros. ring. Qed.

(* Transparent proof: body matters for computation *)
Lemma pred_of_S : ∀ n, pred (S n) = n.
Proof. intros. simpl. reflexivity. Defined.
```

The choice between `Qed` and `Defined` is architectural. For propositions in `Prop`, it rarely matters (proofs are irrelevant). For definitions that participate in computation or are used in later type-checking where unfolding is needed, use `Defined`.

> **Principle 10.** *Qed hides the proof; Defined exposes it. Choose based on whether future terms need to see through the definition.*

---

## Chapter 11 — Modules and Sections

Rocq has two mechanisms for grouping definitions: **Sections** and **Modules**. They are often confused. They do different things.

**Sections** are a mechanism for variable abstraction. Inside a section, you declare variables with `Variable` or `Context`. When the section closes, every definition inside it is automatically generalized over the section variables it used.

```rocq
Section Sorting.
  Variable A : Type.
  Variable cmp : A → A → bool.

  Definition is_sorted (l : list A) : Prop := ...

  Lemma sorted_tail : ∀ l, is_sorted l → is_sorted (tl l).
  Proof. ... Qed.

End Sorting.

(* After the section, sorted_tail has type:
   ∀ (A : Type) (cmp : A → A → bool) (l : list A),
     is_sorted A cmp l → is_sorted A cmp (tl l)  *)
```

Sections reduce repetition. Without sections, every lemma about sorting would repeat `(A : Type) (cmp : A → A → bool)` explicitly.

**Modules** are a namespace and encapsulation mechanism. A module groups definitions and can be given a module type (a signature). Modules can be parameterized (functors). Modules are Rocq's analog of OCaml's module system—because Rocq is implemented in OCaml and shares this structuring mechanism.

```
┌─────────────────────────┬──────────────────────────────────────┐
│  Section                │  Module                              │
├─────────────────────────┼──────────────────────────────────────┤
│  For variable sharing   │  For namespace management            │
│  Closes and generalizes │  Persists as a named unit            │
│  No interface           │  Can have a module type (signature)  │
│  No parameterization    │  Can be a functor                    │
│  Cannot be imported     │  Can be imported                     │
└─────────────────────────┴──────────────────────────────────────┘
```

Use sections for local abstraction within a development. Use modules for organizing large libraries and separating interfaces from implementations.

> **Principle 11.** *Sections abstract variables; modules abstract namespaces. They are not interchangeable.*

---

## Chapter 12 — The Vernacular

The vernacular is the command language of Rocq. Each vernacular command performs one action: define, prove, configure, query, or import.

The commands you use daily:

```
┌──────────────────────┬────────────────────────────────────────────────┐
│  Command             │  Purpose                                       │
├──────────────────────┼────────────────────────────────────────────────┤
│  Require Import M    │  Load module M and open its namespace          │
│  Require M           │  Load module M without opening its namespace   │
│  Import M            │  Open namespace of already-loaded module       │
│  From P Require M    │  Load M from package P                         │
│  Set Option          │  Change a Rocq option                          │
│  Unset Option        │  Reset a Rocq option                           │
│  Check t             │  Print the type of term t                      │
│  Print c             │  Print the definition of constant c            │
│  Search pattern      │  Find lemmas matching a pattern                │
│  About c             │  Print metadata about constant c               │
│  Compute t           │  Reduce t to normal form and print             │
│  Eval strat in t     │  Reduce t using strategy strat and print       │
│  Example             │  Like Definition but unnamed (for illustration)│
│  Local Definition    │  Visible only in current file                  │
│  Global Hint         │  Hint available in all files                   │
└──────────────────────┴────────────────────────────────────────────────┘
```

**Attributes** modify how commands are processed:

```rocq
#[local]    (* Limit scope *)
#[global]   (* Extend scope *)
#[export]   (* Export with module *)
#[program]  (* Use Program mode *)
```

These replaced the old `Local`, `Global` prefixes. Prefer attributes in new code.

**`Require Import`** does two things: loads the compiled `.vo` file and opens the module's namespace so its names are available without qualification. `Require` alone loads without opening. Use `Require` when you need only a few names and want to avoid namespace pollution; qualify with `ModuleName.lemma_name`.

> **Principle 12.** *The vernacular is a scripting language around the term language. Confusing them—treating vernacular commands as terms—is a beginner error with confusing error messages.*

---

## Chapter 13 — Notations and Syntax Extensions

Rocq allows you to define custom notation. Notations are purely syntactic: they are macros that expand into terms before type-checking. They do not change semantics.

```rocq
Notation "x + y" := (plus x y) (at level 50, left associativity).
Notation "x ∈ S" := (In x S) (at level 70).
Notation "[ x ; .. ; y ]" := (cons x .. (cons y nil) ..) .
```

Notations have a **level** (a number from 0 to 100) controlling precedence, and an **associativity** (`left`, `right`, `no`). Higher level = lower precedence. So `+` at level 50 binds tighter than `∧` at level 80 (because lower level number = higher binding power).

**Notation scopes** prevent conflicts. You can define the same notation for different types by placing them in different scopes:

```rocq
Notation "x + y" := (Nat.add x y) : nat_scope.
Notation "x + y" := (Z.add x y) : Z_scope.

Open Scope nat_scope.  (* Default to nat interpretation *)
```

The `%` suffix opens a scope inline: `(2 + 3)%Z` interprets `+` in `Z_scope`.

**Notation for proof terms** is common in libraries. MathComp uses notations extensively. Before you use a library, understand its notation conventions or you will be unable to read terms.

The danger of notations: they can hide structure. The term `a ≤ b` might desugar to `le a b` or `Nat.le a b` or something else depending on the scope. When confused, use `Set Printing All` to see the un-notated term.

> **Principle 13.** *Notations are syntax. When notation obscures meaning, print without it. Always know what a notation expands to.*

---

## Part IV — Mechanism

---

## Chapter 14 — Reduction and Computation

Type-checking in Rocq requires computation. Two types that are definitionally equal—equal by reducing to the same normal form—are interchangeable without proof. Understanding reduction is understanding when Rocq considers two things to be the same.

There are five reduction rules:

```
┌──────────────────┬───────────────────────────────────────────────────┐
│  Rule            │  What it does                                     │
├──────────────────┼───────────────────────────────────────────────────┤
│  β (beta)        │  (fun x ⇒ t) u  ↦  t[u/x]  (apply a function)  │
│  δ (delta)       │  Unfold a constant to its definition              │
│  ζ (zeta)        │  let x := u in t  ↦  t[u/x]  (unfold let)       │
│  ι (iota)        │  match c_i args with | c_i ys ⇒ t ↦ t[args/ys]  │
│  η (eta)         │  fun x ⇒ f x  ↦  f  (when x not free in f)      │
└──────────────────┴───────────────────────────────────────────────────┘
```

**Iota reduction** is the most important one most people overlook. It is the rule for eliminating `match` expressions—the rule that computes with inductive types. When you prove `0 + n = n` by `reflexivity`, Rocq reduces `0 + n` by iota (matching `S` or `O`) to `n` and checks they are equal.

**Delta reduction** unfolds named constants. Transparent definitions (made with `Definition` or `Defined`) can be δ-reduced. Opaque definitions (made with `Qed`) cannot. This is the mechanism behind opacity.

**Reduction strategies** control which reductions to apply:

```
┌──────────────────┬────────────────────────────────────────────────┐
│  Strategy        │  What it reduces                               │
├──────────────────┼────────────────────────────────────────────────┤
│  simpl           │  β, ι, ζ, δ (for fixpoints only)              │
│  cbv             │  All: β, δ, ι, ζ (call-by-value)              │
│  cbn             │  Lazy variant: β, δ, ι, ζ (call-by-need)      │
│  hnf             │  Head normal form: one step of β/δ/ι/ζ        │
│  red             │  One step of δ at head position                │
│  unfold f        │  δ on named constant f only                    │
│  fold f          │  Reverse: try to replace body with name f      │
│  vm_compute      │  Compiled evaluation (fast, for large terms)   │
│  native_compute  │  Native code evaluation (fastest)              │
└──────────────────┴────────────────────────────────────────────────┘
```

`simpl` is the most common tactic reduction. It is smart about not unfolding too much—it applies β and ι eagerly but applies δ only when it will also apply ι (so it unfolds fixpoints only when the match scrutinee is known). This makes `simpl` useful; `cbv` is often too aggressive and produces unreadably large terms.

**Definitional equality** is equality by reduction. Two terms `t` and `u` are definitionally equal if they reduce to the same normal form. Definitional equality requires no proof—it is checked automatically during type-checking. Propositional equality (`t = u`) requires a proof term.

If you cannot tell whether `simpl` should solve your goal, apply `Compute` to the problematic term and see what it reduces to.

> **Principle 14.** *Definitional equality is free; propositional equality costs a proof. Know the difference before writing a lemma.*

---

## Chapter 15 — Unification and Inference

Rocq has two inference mechanisms that fill in information you do not write: **type inference** and **implicit argument inference**.

**Type inference** is the process of computing a term's type from its structure, without requiring type annotations at every node. Rocq uses a form of bidirectional type-checking: it checks terms against known expected types (checking mode) or synthesizes types bottom-up (inference mode).

**Implicit arguments** are arguments that Rocq infers automatically from the types of other arguments. You declare them with curly braces:

```rocq
Definition fst {A B : Type} (p : A × B) : A := match p with (a, _) => a end.
```

Here `A` and `B` are implicit. When you write `fst p`, Rocq infers `A` and `B` from the type of `p`. You can always provide implicit arguments explicitly: `@fst nat bool p`.

`@` before a name turns off implicit argument insertion. Use it when inference fails or you need to control the arguments precisely.

**Unification** is more general: Rocq must solve equations between terms with unknowns (called **unification variables** or **evars**). This happens during tactic execution. When you write `apply lemma`, Rocq unifies the lemma's conclusion with the current goal, solving for any unknown arguments in the lemma.

Unification failures produce the error `Unable to unify`. This usually means either:
- The lemma does not match the goal (wrong lemma)
- There are universe issues (wrong sort)
- Definitional unfolding is needed (try `unfold` first)

**Evars** (existential variables) are holes left during proof construction. The notation `?n` in a goal indicates an evar that must be solved. Some tactics (like `eapply`) deliberately create evars to defer solving. An evar that remains unsolved at `Qed` produces an error.

> **Principle 15.** *Unification is not magic. When it fails, the terms do not match. Read the error, print the terms, and find what does not unify.*

---

## Chapter 16 — The Kernel

The kernel is Rocq's trusted core. It is small—a few thousand lines of OCaml—and it does one thing: **check that a term has a given type**.

Everything outside the kernel is untrusted in the precise sense that:
- Bugs in tactics produce invalid terms → rejected by the kernel → safe.
- Bugs in tactics produce valid terms that prove the wrong thing → not detected.
- Bugs in the kernel itself are a soundness problem.

The kernel implements:

```
┌────────────────────────────────────────────────────────────┐
│                      KERNEL CHECKS                         │
├──────────────────────────────────────────────────────────────┤
│  Type-checking      │  Does t have type T?                 │
│  Sort checking      │  Is this universe consistent?        │
│  Positivity         │  Do inductive types have positive    │
│                     │  constructors?                        │
│  Guard condition    │  Do fixpoints terminate?             │
│  Universe checking  │  Are universe constraints satisfiable│
└──────────────────────────────────────────────────────────────┘
```

**The guard condition** is how Rocq checks that recursive functions terminate. Every `Fixpoint` must decrease on a structurally smaller argument at each recursive call. The kernel checks this syntactically. Functions that are terminating but not structurally recursive require special treatment: either a well-founded recursion scheme (`Fix` from `Wf`) or a fuel argument.

**The positivity condition** prevents inductive types from containing negative occurrences of themselves. The canonical example of what is forbidden:

```rocq
(* This is rejected — T appears negatively (as function argument) *)
Inductive T : Set :=
  | c : (T → False) → T.
(* If this existed, you could prove False from it. *)
```

Rocq's kernel is an independent verification artifact. Rocq ships with a `Print Assumptions` command that lists every axiom your proof depends on. A proof is only as trustworthy as its assumption list.

> **Principle 16.** *The kernel is the only thing that must be trusted. Everything else—tactics, plugins, automation—sits outside it.*

---

## Chapter 17 — Extraction

Extraction is the mechanism that converts Rocq proofs and programs into OCaml, Haskell, or Scheme. It is Rocq's answer to the question: "How do I run this?"

Extraction exploits the Curry-Howard correspondence in reverse: if a proof of `∀ n : nat, ∃ m : nat, m = n + 1` is a program, we can extract the computational content and erase the logical content.

The extraction rules:

```
┌─────────────────────┬──────────────────────────────────────────┐
│  Rocq               │  Extracted                               │
├─────────────────────┼──────────────────────────────────────────┤
│  term : Prop        │  erased (no runtime content)             │
│  term : Set         │  kept (becomes OCaml value)              │
│  Prop → Prop        │  erased                                  │
│  Set → Set          │  OCaml function                          │
│  Prop → Set         │  ignored argument (erased), kept result  │
│  Set → Prop         │  function from Set, result erased        │
└─────────────────────┴──────────────────────────────────────────┘
```

The key insight: `Prop` types are erased because they are proof-irrelevant. At runtime, you do not need to carry the proof that a number is even—you only need the number itself.

```rocq
Extraction Language OCaml.
Extraction "myfile.ml" my_function.
```

The extracted code is correct by construction—it is the computational content of a type-checked Rocq term. But it may be inefficient or ugly. For production use, you can provide **extraction directives** to replace Rocq definitions with native ones:

```rocq
Extract Inductive nat => "int" ["0" "succ"] "(fun fO fS n -> if n = 0 then fO () else fS (n-1))".
```

This replaces Rocq's unary natural numbers with OCaml's native `int`. Without this, extraction of `1000 + 1000` would produce a thousand-deep chain of `S` constructors.

> **Principle 17.** *Extraction erases proofs and keeps programs. The sort Prop is the erasure boundary.*

---

## Part V — Propositions and Logic

---

## Chapter 18 — Prop vs Set vs Type

This is the most commonly confused distinction in Rocq. The answer is mechanical once you understand the purpose of each sort.

**Prop** is for things you want to prove. Its elements are propositions; its proofs are erased by extraction. Two proofs of the same `Prop` are considered equal by Rocq's proof-irrelevance axiom (or by the structure of the sort). You cannot pattern-match on a `Prop` to extract information into a `Set`.

**Set** is for things you want to compute. Its elements are data types. You can extract programs from `Set`-level terms. You *can* pattern-match on a `Set` and produce either `Set` or `Prop` results.

**Type** is the universe that contains both `Prop` and `Set`. When you need a type that could be either, use `Type`. Most polymorphic definitions use `Type`.

The critical rule: **you cannot eliminate from `Prop` into `Set`**. This is the large elimination restriction. You cannot write:

```rocq
(* This is REJECTED *)
Definition extract_witness (p : ∃ n : nat, n > 0) : nat :=
  match p with ex_intro _ n _ => n end.
```

The match is rejected because it eliminates from `Prop` (the existential) into `Set` (nat). The reason: if `Prop` could feed into `Set`, extraction could not erase proofs—it would need to keep them to extract values.

The workaround is `Set`-valued existentials using `{x : A | P x}` (which lives in `Set` or `Type`) instead of `∃ x : A, P x` (which lives in `Prop`).

```
┌──────────────────────────────────────────────────────────────────┐
│                  PROP vs SET: THE RULE                           │
│                                                                  │
│   Prop  ──────→  Prop    ✓  (prove from assumptions)            │
│   Prop  ──────→  Set     ✗  (cannot extract from Prop)          │
│   Set   ──────→  Prop    ✓  (prove properties of data)          │
│   Set   ──────→  Set     ✓  (compute with data)                 │
└──────────────────────────────────────────────────────────────────┘
```

> **Principle 18.** *Prop is for truth; Set is for computation. You can prove about computation, but you cannot compute from proofs.*

---

## Chapter 19 — Connectives as Types

The logical connectives are defined as inductive types. They are not built-in; they are library definitions that happen to be fundamental. Knowing their definitions makes them demystifiable.

```rocq
(* Conjunction *)
Inductive and (A B : Prop) : Prop :=
  conj : A → B → and A B.
Notation "A ∧ B" := (and A B).

(* Disjunction *)
Inductive or (A B : Prop) : Prop :=
  | or_introl : A → or A B
  | or_intror : B → or A B.
Notation "A ∨ B" := (or A B).

(* Truth *)
Inductive True : Prop :=
  I : True.

(* Falsehood *)
Inductive False : Prop := .   (* no constructors *)

(* Negation *)
Definition not (A : Prop) := A → False.
Notation "¬ A" := (not A).

(* Existential *)
Inductive ex (A : Type) (P : A → Prop) : Prop :=
  ex_intro : ∀ x : A, P x → ex A P.
Notation "∃ x, P" := (ex _ (fun x => P)).
```

The pattern is clear: **introduction rules are constructors; elimination rules are pattern matches (or recursors).**

To prove `A ∧ B`, you call constructor `conj` with a proof of `A` and a proof of `B`. The tactic `split` does this.

To use a proof of `A ∧ B`, you pattern-match on it to get the components. The tactic `destruct` does this.

To prove `A ∨ B`, you call `or_introl` with a proof of `A`, or `or_intror` with a proof of `B`. The tactics `left` and `right` do this.

`False` has no constructors. To prove anything from `False`, you use its (vacuous) eliminator. The tactic `contradiction` or `exfalso` does this.

**Universal quantification** `∀ x : A, P x` is a dependent function type. To prove it, you introduce the variable `x` with `intro x`. To use it, you apply it to a specific value.

**Implication** `A → B` is the non-dependent case of `∀`. Introduction: `intro`. Elimination: `apply` (apply a proof of `A → B` to a proof of `A` to get a proof of `B`).

> **Principle 19.** *Logic in Rocq is computation. Prove by constructing; destruct by matching. There are no special logical rules—only the type rules of CIC.*

---

## Chapter 20 — Equality

Equality in Rocq is richer and subtler than in any programming language. There are three notions, and confusing them is a persistent beginner error.

**Definitional equality** (written `≡` informally): two terms are definitionally equal if they reduce to the same normal form. This requires no proof. Rocq checks it during type-checking. Example: `2 + 2 ≡ 4`.

**Propositional equality** (written `=`): a Prop asserting that two terms are equal. It requires a proof. Its definition:

```rocq
Inductive eq (A : Type) (x : A) : A → Prop :=
  eq_refl : eq A x x.
Notation "x = y" := (eq _ x y).
```

The single constructor `eq_refl` says: `x = x` for any `x`. Any proof of `x = y` must have been produced from `eq_refl`—meaning `x` and `y` were definitionally equal at the time the proof was constructed (or the proof was derived by rewriting).

The induction principle for `eq` is:

```rocq
eq_rect : ∀ (A : Type) (x : A) (P : A → Type),
  P x → ∀ y : A, x = y → P y
```

This says: if `P x` holds and `x = y`, then `P y` holds. This is the foundation of the `rewrite` tactic.

**Heterogeneous equality** (John Major equality, `JMeq`): equality between terms of possibly different types. Used in advanced dependent type scenarios. Avoid until you need it.

The key facts about propositional equality:

1. `reflexivity` proves `x = x` (uses `eq_refl`).
2. `rewrite H` where `H : x = y` replaces `x` with `y` in the goal.
3. `symmetry` converts `x = y` to `y = x`.
4. `transitivity z` splits `x = z` into `x = y` and `y = z`.
5. `congruence` proves equalities by congruence closure (combining known equalities).

```
┌─────────────────────────────────────────────────────────────────┐
│               THREE KINDS OF EQUALITY                           │
├──────────────────┬───────────────┬───────────────────────────── │
│  Definitional    │  Propositional│  Heterogeneous               │
│  t ≡ u           │  t = u        │  t ≅ u                       │
│  No proof needed │  Proof needed │  Proof, different types      │
│  Kernel checks   │  eq inductive │  JMeq inductive              │
│  Free            │  Costs lemmas │  Costs headaches             │
└──────────────────┴───────────────┴──────────────────────────────┘
```

> **Principle 20.** *Definitional equality is the machine's answer; propositional equality is your assertion. They coincide at `reflexivity` and diverge everywhere else.*

---

## Chapter 21 — Classical vs Constructive Logic

Rocq's default logic is **constructive** (intuitionistic). The law of excluded middle `∀ P : Prop, P ∨ ¬P` is not provable in Rocq by default. This is not a bug; it is a feature with deep implications.

In constructive logic, to prove `P ∨ Q` you must know *which* disjunct holds. To prove `∃ x, P x` you must know a specific `x`. Proofs are constructions that exhibit witnesses, not arguments that witnesses must exist.

This means some classical proofs do not translate. The proof "either n is even or it isn't; in both cases..." works classically but requires case analysis on a decidable predicate constructively.

**Adding classical logic**: Rocq allows you to add the law of excluded middle as an axiom.

```rocq
Require Import Classical.
(* Now available: *)
Check classic : ∀ P : Prop, P ∨ ¬P.
```

With `classical`, you can prove anything that is classically provable. The cost: proofs that use `classic` are no longer computational. You cannot extract a program from a proof that uses `P ∨ ¬P` without knowing which holds.

**Decidability** is the constructive proxy for excluded middle. A proposition `P` is decidable if there is a term of type `{P} + {¬P}` (Sumbool). For decidable propositions, you get the excluded middle for free:

```rocq
Definition decidable (P : Prop) := {P} + {¬P}.
```

Most concrete propositions about natural numbers (equality, less-than, divisibility) are decidable, and Rocq's standard library provides the decision procedures.

The practical stance: use constructive proofs when you can. Use classical axioms when you must (for purely mathematical developments where computation is not a goal). Keep them separate in your development so you can track which parts are computational.

> **Principle 21.** *Constructive logic proves more precisely but less broadly. Classical axioms broaden what you can prove and narrow what you can compute.*

---

## Part VI — Tactics

---

## Chapter 22 — What a Tactic Is

A tactic is a function from proof state to proof state. It does not directly construct a proof term; it transforms a **goal** (a type to be inhabited) into subgoals (other types to be inhabited), recording how the eventual subgoal inhabitants combine into a term for the original goal.

The proof state has this structure:

```
┌────────────────────────────────────────────────────────────┐
│                     PROOF STATE                            │
│                                                            │
│   n : nat                  ← hypothesis (name : type)     │
│   H : n > 0                ← hypothesis                   │
│   ──────────────────────── ← goal separator               │
│   ∃ m : nat, m = n + 1    ← goal (type to inhabit)       │
│                                                            │
│   1 goal remaining                                         │
└────────────────────────────────────────────────────────────┘
```

The **context** (hypotheses above the line) is a list of typed names available during the proof. The **goal** (below the line) is the type you must construct a term of.

A tactic modifies this state. `intro n` takes a goal `∀ n : nat, P n` and produces a new goal `P n` with `n : nat` added to the context. `split` takes a goal `P ∧ Q` and produces two goals `P` and `Q`. `exact t` takes a goal `T` and completes it if `t : T`.

The tactic language (Ltac) is not the same as the term language. Tactics are *programs about proofs*, not proofs themselves. The term that eventually gets passed to the kernel is assembled from the tactic's effects, not from the tactic itself.

When you write:

```rocq
Lemma my_lemma : P.
Proof.
  tactic1.
  tactic2.
  tactic3.
Qed.
```

Rocq runs each tactic against the current proof state, generating a proof term incrementally. At `Qed`, the complete proof term is type-checked by the kernel. The tactics are discarded.

> **Principle 22.** *A tactic is a proof-state transformer, not a proof. The proof is the term the tactics generate; the tactics are scaffolding.*

---

## Chapter 23 — The Core Tactics

There are fifteen tactics you will use in every proof. Know them precisely.

**Introduction tactics** (introduce hypotheses):

```
intro x       — introduce the leading ∀ or → into context as x
intros x y z  — introduce multiple hypotheses
intros        — introduce all leading hypotheses
intro         — introduce one anonymous
```

**Application tactics** (backward reasoning from conclusion):

```
apply H       — unify goal with conclusion of H; remaining premises become subgoals
exact H       — close goal with H if types match exactly
assumption    — close goal if some hypothesis has the right type
refine t      — like exact but allows holes (_) that become subgoals
```

**Destructuring tactics** (case analysis):

```
destruct H         — case split on H (inductive type)
destruct H as [a b]— case split with pattern matching
case H             — like destruct but without induction hypothesis
```

**Equality tactics**:

```
reflexivity   — close goal of form x = x
symmetry      — flip goal x = y to y = x
transitivity z— split x = z into x = z' and z' = z
```

**Goal manipulation**:

```
simpl         — simplify by computing
simpl in H    — simplify hypothesis H
change T      — replace goal with definitionally equal T
unfold f      — unfold definition of f in goal
unfold f in H — unfold definition of f in hypothesis H
```

**Search tactics**:

```
assumption    — find exact match in context
trivial       — simple automated search
auto          — depth-limited automated proof search
```

**Subgoal management**:

```
{ tac }       — focus on first subgoal, apply tac, close it
all: tac      — apply tac to all remaining subgoals
1: tac        — apply tac to first subgoal only
```

> **Principle 23.** *Learn the fifteen core tactics precisely before learning automation. Automation you do not understand is a proof you cannot debug.*

---

## Chapter 24 — Rewriting

Rewriting is the use of equalities to transform goals and hypotheses. It is one of the most powerful and most-used proof techniques.

**Basic rewriting**:

```rocq
rewrite H      (* H : x = y, replaces x with y in goal *)
rewrite <- H   (* replaces y with x in goal *)
rewrite H in H'  (* rewrites in hypothesis H' *)
```

**Rewriting with universally quantified equalities**:

```rocq
Lemma add_comm : ∀ n m : nat, n + m = m + n.

(* In proof: *)
rewrite add_comm.    (* Rocq instantiates n and m from the goal *)
rewrite (add_comm 3 4).  (* explicit instantiation *)
```

**Conditional rewriting**: some lemmas have hypotheses. `rewrite` creates subgoals for unsatisfied hypotheses.

The `rewrite` tactic works by:
1. Finding all occurrences of the LHS in the goal (or specified occurrence).
2. Replacing with the RHS.
3. Checking the resulting term is well-typed.

**Ring, linear arithmetic**:

```rocq
ring      (* proves ring equalities automatically: a*(b+c) = a*b + a*c *)
linarith  (* proves linear arithmetic goals: n > 0 → n + 1 > 1 *)
omega     (* Presburger arithmetic on nat and Z *)
lia       (* linear integer arithmetic, better than omega *)
```

These tactics call decision procedures, not proof search. `ring` generates a term by normalization; `linarith` calls a linear arithmetic solver.

**The setoid_rewrite** tactic generalizes rewriting to relations other than equality. Chapter 35 covers this.

> **Principle 24.** *Rewriting is directed: left-to-right or right-to-left is your choice. When a proof requires many rewrites, seek a lemma that abstracts the pattern.*

---

## Chapter 25 — Induction Tactics

Induction is the core proof method for properties of inductive types. The tactic `induction` applies the recursor of the inductive type to the current goal.

```rocq
Lemma add_zero : ∀ n : nat, n + 0 = n.
Proof.
  induction n as [| n' IH].
  - (* n = 0 *) reflexivity.
  - (* n = S n', with IH : n' + 0 = n' *)
    simpl. rewrite IH. reflexivity.
Qed.
```

The `as [| n' IH]` pattern names the constructor arguments. `|` separates cases. The first `|` gives names for `O`'s arguments (none). The second gives `n'` (the predecessor) and `IH` (the induction hypothesis).

**Generalization before induction**: a common mistake is applying `induction` before introducing variables that the induction hypothesis should be universally quantified over.

```rocq
(* WRONG: IH is too weak *)
Lemma bad : ∀ n m, n + m = m + n.
Proof.
  intros n m. induction n.
  (* IH : n + m = m + n for fixed m — not useful for changing m *)

(* RIGHT: generalize m before induction *)
Lemma good : ∀ n m, n + m = m + n.
Proof.
  intro n. induction n; intro m.
  (* IH : ∀ m, n + m = m + n — quantified over all m *)
```

**Strong induction** and **well-founded induction** handle situations where the structural induction principle is too weak. `Require Import Wf` and use `well_founded_induction`.

**`inversion`** proves goals by exploiting the injectivity and disjointness of constructors. If `H : S n = S m`, then `inversion H` gives you `n = m`. If `H : O = S n`, then `inversion H` closes the goal (it is impossible).

> **Principle 25.** *Generalize before you induct. An induction hypothesis that holds only for fixed values is useless.*

---

## Chapter 26 — Automation

Rocq provides several automated proof tactics. Automation saves effort but can produce opaque proofs. Use it knowingly.

**auto**: performs backwards proof search using the current `Hint` database. Tries hypotheses and hints up to a depth bound (default 5). Generates terms that are sometimes large.

```rocq
auto.          (* search with default hints *)
auto 10.       (* search to depth 10 *)
auto with db.  (* also use hint database db *)
```

**eauto**: like `auto` but uses `eapply` (allowing unresolved evars). More powerful but slower.

**tauto**: proves propositional tautologies using a decision procedure. Works on goals built from `∧`, `∨`, `→`, `¬`, `True`, `False`.

**firstorder**: extends `tauto` to first-order logic. Slow but sometimes necessary.

**The Hint system**: you register lemmas as hints, and `auto`/`eauto` uses them.

```rocq
Hint Resolve my_lemma : my_db.  (* register as forward/backward hint *)
Hint Rewrite my_eq_lemma : my_rdb.  (* register as rewrite hint *)
```

`autorewrite with my_rdb` applies registered rewrite hints repeatedly.

**`omega` / `lia`**: decision procedures for linear arithmetic. `lia` is the modern replacement. Proves goals like `n ≥ 0 → m > n → m ≥ 1`.

**`congruence`**: congruence closure. Proves equalities and disequalities that follow from the equalities in the context by congruence (function application preserves equality).

**`decide equality`**: proves that a type has decidable equality, given that all component types do.

The danger of automation: a proof by `auto` that you cannot reconstruct manually is a proof you cannot maintain. When automation fails, you must know the underlying tactics. When it succeeds unexpectedly, you should understand why.

> **Principle 26.** *Automation is correct or it fails—it cannot be almost right. But you are responsible for understanding what was proved.*

---

## Chapter 27 — Ltac and Tactic Programming

Ltac is Rocq's tactic meta-language. It lets you write programs that manipulate proof states—custom tactics, proof search procedures, and automation.

An Ltac tactic is defined with `Ltac`:

```rocq
Ltac my_tac :=
  intros;
  simpl;
  try ring.
```

Ltac has:

```
┌────────────────────────────────────────────────────────────────────┐
│                       LTAC CONSTRUCTS                              │
├────────────────────┬───────────────────────────────────────────────┤
│  tac1; tac2        │  Apply tac2 to all goals produced by tac1    │
│  tac1 ;; tac2      │  Apply tac2 only to the first goal           │
│  try tac           │  Apply tac; ignore failure                   │
│  tac1 || tac2      │  Try tac1; if it fails, try tac2             │
│  repeat tac        │  Apply tac until failure                     │
│  progress tac      │  Apply tac; fail if proof state unchanged    │
│  fail              │  Fail unconditionally                        │
│  match goal with   │  Pattern match on current goal               │
│  match H with      │  Pattern match on term H                     │
│  idtac "msg"       │  Print message (for debugging)               │
└────────────────────┴───────────────────────────────────────────────┘
```

**`match goal with`** is the most powerful Ltac construct:

```rocq
Ltac my_inversion :=
  match goal with
  | H : ?A ∧ ?B |- _ => destruct H
  | H : False |- _ => contradiction
  | |- ?A ∧ ?B => split
  end.
```

The patterns `?A`, `?B` bind to the matched subterms.

**Ltac pitfalls**:
- Ltac is dynamically typed. Type errors become runtime failures.
- Ltac is not the term language; it operates *on* the proof state.
- Recursive Ltac requires care to avoid infinite loops.
- The `match goal with` patterns match up to conversion, which can be slow.

**Ltac2** is the modern replacement for Ltac. It is statically typed, has better error messages, and is more predictable. New developments should prefer Ltac2 for complex tactic programming.

> **Principle 27.** *Ltac is a scripting language for proofs. Like all scripting languages, it rewards terseness and punishes complexity. Keep tactics short.*

---

## Part VII — Inductive Families and Dependent Types

---

## Chapter 28 — Dependent Types

Dependent types are types that depend on values. They are the feature that makes Rocq both powerful and difficult. Every advanced Rocq development uses them heavily.

In a non-dependent type system, `→` is all you have: functions from type to type. In a dependent type system, `∀` generalizes `→`: the result type can mention the argument's value.

The canonical example is a vector: a list with its length in the type.

```rocq
Inductive Vector (A : Type) : nat → Type :=
  | vnil  : Vector A 0
  | vcons : ∀ n, A → Vector A n → Vector A (S n).
```

`Vector A n` is a type that depends on the value `n`. A term of type `Vector A 5` is a vector with exactly 5 elements, guaranteed by the type.

With this type, you can write `head` without a special case for the empty vector:

```rocq
Definition head {A : Type} {n : nat} (v : Vector A (S n)) : A :=
  match v with vcons _ x _ => x end.
```

The type `Vector A (S n)` guarantees that `v` is a cons, so the match is exhaustive without an empty case.

**The power and the price**: dependent types let you express precise specifications in types. The price is that type-checking becomes undecidable in general (Rocq circumvents this with restrictions), pattern matching becomes more complex (Chapter 30), and functions must carry more information in their types.

The fundamental tension in dependent types:

```
┌──────────────────────────────────────────────────────────────┐
│           DEPENDENT TYPES: POWER vs COMPLEXITY               │
├──────────────────────────────────────────────────────────────┤
│  More precise types → fewer runtime errors                   │
│  More precise types → harder to write the programs           │
│  More precise types → more information must be carried       │
│  More precise types → harder to modify when requirements     │
│                        change                                │
└──────────────────────────────────────────────────────────────┘
```

The pragmatic stance: use dependent types when the precision pays for itself. Sorted lists, balanced trees, well-typed expressions, and state machines benefit from dependent types. Arbitrary programs where the invariants are complex do not.

> **Principle 28.** *Dependent types move errors from runtime to type-check time. Use them when the invariant is worth encoding in the type.*

---

## Chapter 29 — Inductive Families

An **inductive family** is an inductive type indexed by values. Distinguish carefully between **parameters** and **indices**.

**Parameters** are fixed for the whole type definition. They appear before the `:` in the type.

**Indices** vary per constructor. They appear after the `:` in the type (as arguments to the type name).

```rocq
(* A is a parameter: fixed for all constructors *)
(* n is an index: different per constructor *)
Inductive Vector (A : Type) : nat → Type :=
  | vnil  : Vector A 0            (* n = 0 for this constructor *)
  | vcons : ∀ n, A → Vector A n → Vector A (S n).  (* n = S n' *)
```

Parameters can be abstracted over with sections or implicit arguments. Indices cannot—they are part of the type's identity.

The key distinction in proofs: when you `destruct` on an inductive family, you get equalities about the indices. This is how you learn about the values from the shape of the data.

```rocq
Lemma vector_O_is_nil : ∀ A (v : Vector A 0), v = vnil.
Proof.
  intros A v.
  dependent destruction v.
  (* The case vcons is impossible: vcons has type Vector A (S n), not Vector A 0 *)
  reflexivity.
Qed.
```

**`dependent destruction`** (from `Program` or `Equations`) handles the index unification that ordinary `destruct` cannot. This is one of the major pain points of inductive families.

The `Equations` plugin provides a pattern-matching notation that handles dependent types correctly and generates the needed eliminators automatically.

> **Principle 29.** *Parameters are for the type; indices are for the value. Mixing them causes subtle errors in pattern matching.*

---

## Chapter 30 — Pattern Matching and Dependent Elimination

Pattern matching on dependent types requires care. The `match` term must produce a type that is consistent across all cases, which is non-trivial when the type of the scrutinee depends on the constructor.

The general form of `match` is:

```rocq
match t as x in (T y₁ ... yₙ) return P x y₁ ... yₙ with
| pattern₁ => body₁
| ...
end
```

The `return` clause specifies how the type of the overall `match` expression depends on the constructor. This is called the **dependent elimination** or **return type annotation**.

A simple example: computing the type of the result based on a constructor.

```rocq
Definition bool_to_prop (b : bool) : Prop :=
  match b with
  | true  => True
  | false => False
  end.

Definition proof_if (b : bool) : bool_to_prop b :=
  match b as b' return bool_to_prop b' with
  | true  => I     (* I : True *)
  | false => ?     (* nothing of type False — this case is unreachable when b = true *)
  end.
```

When the scrutinee has a constraint that makes some cases unreachable, you must still provide a body (because Rocq cannot know which cases are truly unreachable without you telling it). For the unreachable cases, you can use `False_rect` or, better, a dependent match that contradicts itself.

**The problem of equality reflection**: in some cases, the index constraints between the scrutinee's type and the expected return type are only known through propositional equality, not definitional equality. This is when you need `eq_rect` (the transport principle) or the `Equations` plugin.

Tactics `destruct`, `case`, `induction` automate the construction of `match` terms. When they fail on dependent types, you may need to write the `match` term directly or use `dependent destruction`.

> **Principle 30.** *Every match on a dependent type is a proof of existence. The return clause is the formal statement of what you are proving.*

---

## Chapter 31 — Fixpoints and Termination

Rocq requires all functions to terminate. This is not a limitation of the compiler—it is a logical necessity. A non-terminating function could be used to prove `False`:

```rocq
(* If this were allowed: *)
Fixpoint loop : False := loop.
```

The **guard condition** (also called the **structural recursion check**) ensures termination by requiring that every recursive call is made on a *structurally smaller* argument—a subterm of the original argument.

```rocq
(* Allowed: recursive call on predecessor *)
Fixpoint add (n m : nat) : nat :=
  match n with
  | O    => m
  | S n' => S (add n' m)   (* add is called on n', which is smaller than S n' *)
  end.

(* Rejected: recursive call on n+1, which is larger *)
Fixpoint bad (n : nat) : nat :=
  bad (S n).  (* structural decrease check fails *)
```

**Mutual recursion** uses `Fixpoint ... with ...`:

```rocq
Fixpoint even (n : nat) : bool :=
  match n with O => true  | S n' => odd n' end
with odd (n : nat) : bool :=
  match n with O => false | S n' => even n' end.
```

**Well-founded recursion** handles terminating functions that are not structurally recursive. If you have a measure function `f : A → nat` such that `f (recursive_arg) < f (original_arg)` at every call, you can use `Wf.Fix`:

```rocq
Require Import Wf.
(* Define a function using a well-founded relation *)
Definition my_fn : ∀ n : nat, ... :=
  Fix (lt_wf) (fun n => ...) (fun n => ...).
```

In practice, the `Program Fixpoint` command and the `Equations` plugin provide ergonomic ways to write well-founded recursive functions with obligations.

> **Principle 31.** *Termination in Rocq is a proof obligation. Structural recursion discharges it automatically; other termination arguments require you to provide the measure.*

---

## Part VIII — Libraries and Mathematics

---

## Chapter 32 — The Standard Library

Rocq's standard library (`Coq.Init.*`, `Coq.Arith.*`, `Coq.Lists.*`, etc.) provides the mathematical foundations most developments need.

Key modules and what they contain:

```
┌──────────────────────┬────────────────────────────────────────────┐
│  Module              │  Contents                                  │
├──────────────────────┼────────────────────────────────────────────┤
│  Coq.Init.Prelude    │  Automatically loaded: bool, nat, list     │
│  Coq.Arith.Arith     │  Arithmetic on nat: add, mul, facts        │
│  Coq.ZArith.ZArith   │  Integers Z: efficient binary encoding     │
│  Coq.QArith.QArith   │  Rationals Q                               │
│  Coq.Reals.Reals     │  Real numbers R (axiomatic)                │
│  Coq.Lists.List      │  List: map, filter, fold, length           │
│  Coq.Sorting.Sorting │  Sorting and sorted predicates             │
│  Coq.FSets.FSetList  │  Finite sets (module-based)                │
│  Coq.Logic.Classical │  Law of excluded middle (axiom)            │
│  Coq.Logic.FunctExt  │  Functional extensionality (axiom)         │
│  Coq.Logic.PropExt   │  Propositional extensionality (axiom)      │
└──────────────────────┴────────────────────────────────────────────┘
```

**Searching the library**: use `Search` extensively.

```rocq
Search (?n + ?m = ?m + ?n).   (* find commutativity lemmas *)
Search (_ ++ _ = []).          (* find lemmas about concatenation equaling nil *)
Search nat → list.             (* find functions from nat to list *)
SearchRewrite (?n + 0).        (* find equations with n + 0 on one side *)
```

**Library naming conventions**: Rocq standard library names follow a pattern: `Type_operation` or `operation_property`. For example: `Nat.add_comm`, `List.length_app`, `Z.mul_0_l`.

The standard library is not the best library for algebraic developments. MathComp is.

> **Principle 32.** *Before proving a lemma, Search for it. The standard library is large, well-curated, and frequently contains exactly what you need.*

---

## Chapter 33 — MathComp and Algebraic Hierarchy

The Mathematical Components library (MathComp) is the most extensive formal mathematical library for Rocq. It covers group theory, linear algebra, number theory, combinatorics, and the formal proof of the Four Color Theorem.

MathComp's design philosophy differs from the standard library:

1. **Small-scale reflection**: propositions are computed by boolean functions. `n == m` is a boolean computation; `n = m` is a proposition. They are linked by `reflect` lemmas: `eqP : reflect (n = m) (n == m)`.

2. **Canonical Structures** (covered in Chapter 34): algebraic hierarchies are built using canonical structures, not typeclasses.

3. **ssreflect tactic language**: MathComp introduces a tactic language extension that uses different syntax for common operations.

```rocq
From mathcomp Require Import all_ssreflect.

(* ssreflect style: *)
Lemma my_lemma : ∀ n : nat, n + 0 = n.
Proof. move=> n. by rewrite addn0. Qed.
```

The MathComp tactics:

```
┌──────────────┬────────────────────────────────────────────────────┐
│  move=>      │  intro (like intros)                               │
│  move:       │  generalize (like revert)                          │
│  by tac      │  complete goal with tac; fail if goal remains      │
│  apply:      │  exact application                                 │
│  rewrite     │  rewrite (but with different matching behavior)    │
│  have :      │  assert subgoal                                    │
└──────────────┴────────────────────────────────────────────────────┘
```

MathComp's algebraic hierarchy:

```
           eqType
              │
           choiceType
              │
           countType
              │
           finType
              │
      ┌───────┴────────┐
  zmodType          finZmodType
      │
  ringType
      │
  ┌───┴───┐
comRing  unitRing
    │        │
  field    ...
```

Each level adds operations and axioms. A type registered at a given level can use all lemmas proved for that level.

> **Principle 33.** *MathComp is the production library for mathematical Rocq. Its design choices—boolean reflection, canonical structures—are deliberate and consistent. Learn the design before the tactics.*

---

## Chapter 34 — Typeclasses and Canonical Structures

Rocq has two mechanisms for ad-hoc polymorphism—writing code that works differently for different types. They serve the same goal and are often confused.

**Typeclasses** are instances of records that Rocq infers automatically.

```rocq
Class Eq (A : Type) := {
  eqb : A → A → bool;
  eqb_refl : ∀ x, eqb x x = true;
}.

Instance nat_Eq : Eq nat := {
  eqb := Nat.eqb;
  eqb_refl := Nat.eqb_refl;
}.

(* Now works for any type with an Eq instance: *)
Definition are_equal {A : Type} `{Eq A} (x y : A) : bool := eqb x y.
```

Rocq resolves typeclasses by searching for `Instance` declarations. This is the `Hint` database under a different name.

**Canonical Structures** are a more primitive mechanism using Rocq's unification algorithm.

```rocq
Structure EqType := Pack {
  sort : Type;
  eqb  : sort → sort → bool;
}.

Canonical nat_EqType := Pack nat Nat.eqb.

(* Rocq infers the EqType from the sort: *)
Definition are_equal (T : EqType) (x y : sort T) : bool := eqb T x y.
```

When Rocq sees `are_equal _ n m` where `n m : nat`, it looks for a canonical structure whose `sort` field is `nat`, finds `nat_EqType`, and uses it.

```
┌────────────────────┬────────────────────────────────────────────┐
│  Typeclasses       │  Canonical Structures                      │
├────────────────────┼────────────────────────────────────────────┤
│  Standard Rocq     │  Used heavily by MathComp                  │
│  Instance search   │  Unification-based inference               │
│  Hierarchies       │  Algebraic hierarchies                     │
│  Sometimes slow    │  More predictable                          │
│  Familiar to Haskell devs                                       │
└────────────────────┴────────────────────────────────────────────┘
```

In practice: use typeclasses for new development; understand canonical structures to use MathComp.

> **Principle 34.** *Typeclasses and canonical structures are both inference mechanisms. Typeclasses search; canonical structures unify. Both can fail silently with confusing errors.*

---

## Chapter 35 — Setoids and Rewriting Modulo Equivalence

The standard `rewrite` tactic rewrites along propositional equalities `x = y`. But often you want to rewrite along a different relation—list permutation, functional extensionality, ring equivalence.

**Setoids** provide this generalization. A setoid is a type equipped with an equivalence relation.

```rocq
Require Import Setoid.

(* Declare that list_perm is an equivalence relation *)
Add Parametric Relation (A : Type) : (list A) (@Permutation A)
  reflexivity proved by Permutation_refl
  symmetry proved by Permutation_sym
  transitivity proved by Permutation_trans
  as list_perm_rel.

(* Declare how functions respect this relation *)
Add Parametric Morphism (A : Type) : (@length A)
  with signature (@Permutation A) ==> (@eq nat)
  as length_perm_morphism.
Proof. intros. apply Permutation_length. Qed.

(* Now you can rewrite with permutation: *)
Lemma example : ∀ l1 l2 : list nat,
  Permutation l1 l2 → length l1 = length l2.
Proof.
  intros l1 l2 H.
  rewrite H.  (* rewriting modulo Permutation *)
  reflexivity.
Qed.
```

The `Parametric Morphism` declaration tells Rocq: if you see `length` applied to something, and you know how the argument respects the equivalence, you can rewrite under it.

Setoid rewriting is fundamental for algebraic developments, quotient types, and any setting where definitional equality is too strong.

> **Principle 35.** *Equality is not the only relation worth rewriting along. Setoids generalize rewriting to any equivalence, at the cost of morphism proofs.*

---

## Part IX — Production

---

## Chapter 36 — Proof Engineering

A Rocq proof that works is not a Rocq proof that is maintainable. At scale, proof engineering matters as much as the proofs themselves.

The central discipline: **separate specification from proof from computation**.

```
┌─────────────────────────────────────────────────────────────────┐
│                    THREE LAYERS                                  │
├──────────────────┬──────────────────────────────────────────────┤
│  Specification   │  Types and propositions. What is true.       │
│  Proof           │  Tactic scripts. How we know it is true.     │
│  Computation     │  Fixpoints and definitions. How to compute.  │
└──────────────────┴──────────────────────────────────────────────┘
```

Keep these layers separate in the file structure. A type definition belongs in a `Types.v` file; its properties in `Properties.v`; its algorithms in `Algorithm.v`.

**Proof robustness**: proofs break when definitions change. Fragile proofs:
- Use `rewrite` with specific lemma names that may be renamed.
- Depend on unfolding behavior that changes when definitions change.
- Use `auto` in ways where adding a `Hint` elsewhere breaks the proof.

Robust proofs:
- Use `ring`, `linarith`, `congruence` for arithmetic—these are decision procedures that do not depend on specific lemma names.
- Name the intermediate steps rather than chaining everything.
- Use `assert` to decompose long proofs into independently verifiable pieces.

**Abstraction in proofs**: just as in programming, abstract over repeated patterns.

```rocq
Ltac standard_induction n :=
  induction n; simpl; [reflexivity | intro IH; rewrite IH; reflexivity].
```

**Proof by reflection**: for large, computational proofs, write a decision procedure that computes the answer, then prove the decision procedure is correct. Check the answer with `Compute` or `vm_compute`. This is often faster than proof search.

> **Principle 36.** *A proof that breaks when you rename a lemma is not a good proof. Proof maintenance is proof engineering.*

---

## Chapter 37 — Axioms and Trust

Every Rocq development rests on axioms. The standard Rocq development uses no additional axioms beyond CIC itself. Many practical developments add more.

**Print Assumptions** is the most important command for trust assessment:

```rocq
Print Assumptions my_theorem.
```

This prints every axiom that `my_theorem` transitively depends on. A proof is only as trustworthy as its assumption list.

The standard additional axioms and what they commit you to:

```
┌────────────────────────────────┬──────────────────────────────────┐
│  Axiom                         │  Consequences                    │
├────────────────────────────────┼──────────────────────────────────┤
│  Classical.classic             │  Law of excluded middle; proofs  │
│  ∀ P, P ∨ ¬P                  │  no longer computational         │
│  FunctionalExtensionality      │  Functions equal iff pointwise   │
│  ∀ f g, (∀x, f x=g x)→f=g    │  equal; UIP for functions        │
│  PropositionalExtensionality   │  Propositions equal iff equiv.   │
│  ∀ P Q, (P↔Q)→P=Q             │  Strengthens definitional eq.    │
│  Axiom K / UIP                 │  Uniqueness of identity proofs   │
│  JMeq_eq                       │  Heterogeneous eq. implies eq.   │
└────────────────────────────────┴──────────────────────────────────┘
```

**Functional extensionality** is safe (consistent with CIC) and commonly needed. Two functions that agree on all inputs should be equal—Rocq does not prove this by default because functions can differ in their computational behavior even while agreeing on outputs.

**Axiom K (UIP)**: Uniqueness of Identity Proofs says that any two proofs of `x = x` are definitionally equal. This is consistent with set-theoretic interpretations but inconsistent with homotopy type theory (HoTT), where paths can be non-trivial.

The safe baseline: use no axioms beyond the standard ones, or explicitly document every axiom with its justification.

> **Principle 37.** *Print Assumptions before trusting a proof. Every axiom is a gap in the verification.*

---

## Chapter 38 — Performance and Proof Size

Large Rocq developments face performance problems that tutorials never mention. Proof checking can be slow; compiled `.vo` files can be large; interactive response in editors can lag.

**The three performance bottlenecks**:

1. **Type-checking time**: complex type-checking, especially with typeclasses and canonical structures, can be slow. Unification search is expensive.
2. **Proof term size**: tactics like `omega` or `ring` generate large proof terms. `vm_compute` generates small proof terms (it uses a compiled evaluator that generates certificates).
3. **Compilation time**: large files with many `Qed`-closed proofs compile faster than files with many `Defined` proofs (because opaque proofs do not need to be type-checked when re-used).

**Optimization strategies**:

```
┌───────────────────────────────────────────────────────────────┐
│                   PERFORMANCE LEVERS                          │
├───────────────────┬───────────────────────────────────────────┤
│  Use Qed not Defined │  Opaque proofs not re-checked         │
│  vm_compute      │  Fast verification of computational facts  │
│  native_compute  │  Fastest for large computations            │
│  Opaque hints    │  Avoid expensive unfolding during search   │
│  Set Typeclasses  │  Control typeclass search depth           │
│  Evar map size   │  Too many evars slows unification          │
│  Avoid `Compute` │  In large files; use Check instead         │
└───────────────────┴───────────────────────────────────────────┘
```

**Proof by reflection** for computation-heavy lemmas: instead of a tactic proof, write a boolean function `check : inputs → bool`, verify `check inputs = true` by `vm_compute`, and prove `check inputs = true → property holds`. The kernel only checks the boolean evaluation—which is fast—and the generic soundness lemma—which is proved once.

> **Principle 38.** *A correct proof that takes an hour to check is an engineering problem. Reflect computation into the kernel for performance-critical proofs.*

---

## Chapter 39 — Proof Maintenance

Proofs break. Definitions change, libraries update, Rocq itself evolves. Proof maintenance is the ongoing cost of formal verification.

**What breaks proofs**:
- Renaming lemmas in libraries
- Changing the definition a proof depends on
- Adding a new constructor to an inductive type
- Upgrading Rocq (syntax changes, tactic behavior changes)
- Changing universe constraints

**The maintenance hierarchy**: some proofs are more brittle than others.

```
Most brittle
    │  Long chains of rewrites with specific lemma names
    │  Proofs that depend on unfolding depth of simpl
    │  Proofs using auto with large, changing hint databases
    │  Proofs that mention internal terms of other modules
    ▼  Proofs using ring/linarith/congruence (decision procedures)
Least brittle
```

**Strategies for maintainable proofs**:

1. Use decision procedures (`ring`, `lia`, `congruence`) where they apply. These do not depend on library naming.
2. Use `have` and `assert` to name intermediate steps. Named steps can be re-proved independently when the proof breaks.
3. Document the proof strategy in comments, not just the tactics.
4. Minimize dependency on unfolding: if a proof works only because `simpl` unfolds a particular definition, it will break when that definition changes.

**Migration**: when Rocq changes, use `coqtool` or `compcert`-style migration scripts. For library updates, `Search` for the renamed lemma.

> **Principle 39.** *A proof that requires maintenance is a tax on future work. Pay the tax upfront with robust proof design.*

---

## Part X — Tooling and Workflow

---

## Chapter 40 — The Rocq Toolchain

Rocq's toolchain consists of several executables:

```
┌──────────────────┬────────────────────────────────────────────────┐
│  Tool            │  Purpose                                       │
├──────────────────┼────────────────────────────────────────────────┤
│  rocq            │  Main executable (Coq 8.x: coqtop, coqc)      │
│  rocq compile    │  Compile a .v file to .vo                      │
│  rocq top        │  Interactive REPL                              │
│  rocq doc        │  Generate documentation                        │
│  rocq dep        │  Compute dependency graph                      │
│  rocqide         │  Standalone IDE (legacy)                       │
│  opam            │  Package manager for Rocq packages             │
└──────────────────┴────────────────────────────────────────────────┘
```

The transition from Coq to Rocq naming is ongoing. Many commands still use `coq` prefixes. Check the current installation.

**Installation**: the recommended installation method is `opam`, OCaml's package manager.

```bash
opam init
opam switch create rocq-dev ocaml-base-compiler.5.0.0
opam pin add rocq-prover https://github.com/rocq-prover/rocq.git
opam install rocq-prover
```

For a stable release:

```bash
opam install coq.8.19.2  # still coq naming for stable releases
```

**Package ecosystem**: Rocq packages are distributed through `opam` and the `coq-community` organization. The main repository is the `coq-released` opam repository.

```bash
opam repo add coq-released https://coq.inria.fr/opam/released
opam install coq-mathcomp-ssreflect
```

> **Principle 40.** *The toolchain is opam. Learn opam before Rocq; package management problems are not Rocq problems, but they look like it.*

---

## Chapter 41 — Editors and Proof Mode

Rocq is interactive. The central workflow is writing tactics in an editor and seeing the proof state after each tactic. Three editors support this well.

**Proof General** (Emacs): the original and still most stable. Uses Emacs to send commands to a `coqtop` process. The proof state appears in a dedicated buffer. Navigate forward and backward through the proof with `C-c C-n` and `C-c C-u`.

**VSCode with coq-lsp**: the modern choice. The Language Server Protocol (LSP) server `coq-lsp` provides proof state display, semantic highlighting, and inline goals. Requires `rocq-lsp` package.

**CoqIDE**: the standalone IDE distributed with Rocq. Works but is less actively maintained than Proof General or VSCode.

The proof state display is the primary interaction mechanism:

```
After "intros n m.":

  n : nat
  m : nat
  ──────────────────
  n + m = m + n
```

After "induction n.":

```
Goal 1/2:
  m : nat
  ──────────────────
  0 + m = m + 0

Goal 2/2:
  n : nat
  IHn : ∀ m, n + m = m + n
  m : nat
  ──────────────────
  S n + m = m + S n
```

The workflow: keep the proof state visible at all times. Navigate line-by-line. Do not advance past a tactic until you understand what it did. When stuck, use `Check`, `Search`, and `Print` to explore.

**`Show Proof.`** displays the current proof term as constructed so far. Use this to understand what the tactics are building.

> **Principle 41.** *The proof state is the feedback loop. A proof without inspecting the proof state after each tactic is written blind.*

---

## Chapter 42 — Building Projects

Non-trivial Rocq developments consist of multiple files with dependencies. The build tool is `make` with a `CoqMakefile` (or the newer `dune` integration).

**The standard project structure**:

```
myproject/
├── _CoqProject          ← project configuration
├── Makefile             ← generated by coq_makefile
├── theories/
│   ├── Types.v
│   ├── Properties.v
│   └── Main.v
└── extracted/
    └── extraction.v
```

**`_CoqProject`**:

```
-R theories MyProject
theories/Types.v
theories/Properties.v
theories/Main.v
```

The `-R dir prefix` flag registers the directory with a logical prefix. Files in `theories/` are referred to as `MyProject.Types`, `MyProject.Properties`, etc.

**Generating the Makefile**:

```bash
coq_makefile -f _CoqProject -o Makefile
make
```

**dune integration**: the `coq.theory` stanza in `dune` files handles Rocq projects.

```
(coq.theory
 (name MyProject)
 (modules Types Properties Main))
```

With dune, run `dune build` to compile. dune handles dependency computation automatically.

**Dependency order**: Rocq compiles files in dependency order (determined by `Require` statements). `rocq dep` (or `coqdep`) computes this order. `make` uses it to compile in the right sequence.

> **Principle 42.** *The _CoqProject file is the project definition. Without it, editors cannot find your files and builds are manual and fragile.*

---

## Chapter 43 — Search and Documentation

Rocq's search facilities are the primary way to navigate the library.

**`Search`** (the main tool):

```rocq
(* Find lemmas whose type contains this pattern: *)
Search (?a + ?b = ?b + ?a).

(* Find lemmas about a specific constant: *)
Search Nat.add.

(* Find lemmas with multiple patterns: *)
Search (_ + _) (_ * _).

(* Restrict to a module: *)
Search Nat.add inside Arith.

(* Exclude a module: *)
Search (_ + _) -inside List.
```

**`SearchRewrite`**: find lemmas useful as rewrite rules.

```rocq
SearchRewrite (_ + 0).   (* find rewrites involving x + 0 *)
```

**`Check`**: the most useful command. Prints the type of any term.

```rocq
Check Nat.add_comm.
(* : ∀ n m : nat, n + m = m + n *)
```

**`Print`**: prints the definition of a constant.

```rocq
Print Nat.add.
(* Nat.add = fix add (n m : nat) : nat := ... *)
```

**`About`**: prints metadata including opacity, universe information, and notation hints.

**`Locate`**: finds where a notation or name is defined.

```rocq
Locate "+".    (* prints: Notation "x + y" := Nat.add x y *)
Locate "list". (* prints: Inductive Coq.Init.Datatypes.list *)
```

**Documentation**: the primary sources are:
- The Rocq Reference Manual: https://rocq-prover.org/doc
- The standard library HTML documentation: generated from source with `coqdoc`
- MathComp documentation: https://math-comp.github.io

> **Principle 43.** *Search before you prove. The lemma you need usually exists. The skill is knowing how to describe it to Search.*

---

## Part XI — Mastery

---

## Chapter 44 — Debugging Proofs

A stuck proof is a proof where you do not know what to do next. A broken proof is one where a tactic fails unexpectedly. These require different approaches.

**When stuck**:

1. **Read the goal.** Print every hypothesis type. Use `simpl in *` to reduce and see what things actually look like.
2. **`Show Proof.`** See what term has been built so far. Sometimes the proof term reveals what is needed.
3. **Search for lemmas.** Take a subterm from the goal and `Search` for it.
4. **Try `auto`, `eauto`, `tauto` with increasing depth.** If these solve it, understand why.
5. **Decompose the goal.** Prove a simpler version first. Use `assert` to introduce intermediate steps.
6. **Check types.** Use `Check` on hypotheses. Sometimes a hypothesis has a more complex type than you assumed.

**When a tactic fails unexpectedly**:

```
┌────────────────────────────────────────────────────────────────────┐
│  Error                        │  Likely cause                      │
├───────────────────────────────┼────────────────────────────────────┤
│  Unable to unify              │  Wrong lemma; types don't match     │
│  Not a function               │  Applied something to too many args │
│  Universe inconsistency       │  Sort error; check what sorts you   │
│                               │  are mixing                        │
│  Found ... where ... expected │  Type mismatch; print both types   │
│  Cannot infer ...             │  Implicit arg cannot be inferred;  │
│                               │  provide it explicitly with @      │
│  Not a subterm                │  Guard condition failure; fn       │
│                               │  is not structurally recursive     │
│  Illegal occurrence           │  Positivity condition failure       │
└───────────────────────────────┴────────────────────────────────────┘
```

**`Set Printing All.`** is the nuclear option: shows everything without notations, implicit arguments, or coercions. Verbose but unambiguous.

**`idtac "message".`** inside Ltac prints debugging information during tactic execution.

**`Fail tac.`** expects `tac` to fail. If `tac` succeeds, `Fail tac` fails. Useful for documenting that a certain approach does not work.

> **Principle 44.** *A stuck proof means missing information. Find what you do not know before trying more tactics.*

---

## Chapter 45 — Architectural Patterns

Large Rocq developments use recurring patterns. Here are the most important.

**Pattern 1: Decidable reflection**

Define a boolean check, prove it correct, then use the boolean check computationally and the correctness lemma for proofs.

```rocq
Fixpoint is_sorted (l : list nat) : bool := ...

Lemma is_sorted_correct : ∀ l, is_sorted l = true ↔ Sorted l.
```

**Pattern 2: Representation independence**

Define a type abstractly (via a module signature), implement it concretely, and prove the implementation meets the specification. Future code depends only on the signature.

**Pattern 3: Structural lemmas + one main theorem**

Build up a library of small lemmas about your data type, each proved by simple induction or case analysis. The main theorem then chains these lemmas. This keeps each proof small and independently understandable.

**Pattern 4: Proof by computation (reflection)**

For decidable properties over finite domains, compute the answer and verify by `vm_compute` or `native_compute`. Used in MathComp to prove theorems about specific finite groups without manual proofs.

**Pattern 5: Separation of concerns**

Keep the following in separate files or sections:
- The type definitions
- The basic operations
- The basic properties of operations
- The high-level theorems

Circular dependency between these layers is a design error.

**Pattern 6: Abstraction via typeclasses or canonical structures**

Factor out the common structure of a mathematical hierarchy (Eq, Ord, Monoid, Group) into typeclasses or canonical structures. Prove theorems once for the abstraction; instantiate for each concrete type.

> **Principle 45.** *Architecture in Rocq is the same as in programming: separate concerns, minimize dependencies, and make the common case easy.*

---

## Chapter 46 — Common Errors and Their Meaning

```
┌──────────────────────────────────────────┬──────────────────────────────────────────────────────────────────┐
│  Error Message                           │  What It Means and How to Fix It                                │
├──────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
│  Universe inconsistency                  │  You mixed sorts in a way that creates a cycle. Check where      │
│                                          │  you used Type, Prop, Set together.                             │
├──────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
│  Unable to unify X with Y               │  A tactic tried to match two types that do not reduce to the    │
│                                          │  same form. Use `Set Printing All` to see both terms precisely. │
├──────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
│  Illegal occurrence of recursive call   │  Your Fixpoint does not decrease structurally. Rewrite to use    │
│                                          │  a structurally smaller argument, or use well-founded recursion.│
├──────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
│  Non strictly positive occurrence of X  │  Your inductive type has a negative constructor. Remove the     │
│                                          │  occurrence of X on the left of a function arrow in a constructor│
├──────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
│  The term ... has type ... while it      │  Type mismatch. You gave a term of the wrong type. Print the   │
│  is expected to have type ...           │  types of both expected and actual with `Check`.                 │
├──────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
│  Cannot infer the implicit argument ... │  Implicit argument inference failed. Provide the argument        │
│                                          │  explicitly using `@function arg1 arg2`.                        │
├──────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
│  Unsatisfied goals                       │  `Qed` or `Defined` was reached with goals remaining. A tactic │
│                                          │  you thought closed a goal did not.                             │
├──────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
│  Unresolved existential variables        │  `eapply` or `eexists` left holes (evars) unresolved. Close    │
│                                          │  every evar before `Qed`.                                       │
├──────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
│  Not an inductive type                   │  You tried `destruct` or `induction` on a term that is not      │
│                                          │  inductive. Check the type with `Check`.                        │
├──────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
│  This expression should not be a value  │  You used a term where Rocq expected a type (or vice versa).    │
│                                          │  Check the sort of the term.                                    │
└──────────────────────────────────────────┴──────────────────────────────────────────────────────────────────┘
```

> **Principle 46.** *Error messages in Rocq are precise. Read them fully before guessing at a fix.*

---

## Chapter 47 — How to Actually Learn Rocq

Forget the standard path. The typical introduction to Rocq goes through "Software Foundations" volume 1 (Logical Foundations), spending weeks on propositional logic and simple arithmetic before reaching dependent types, inductive families, or anything resembling production Rocq. This is the wrong order for an adult learner.

Here is the contrarian protocol:

**Week 1 — Read, do not code.** Read Chapters 1–7 of this manual. Read the CIC paper by Coquand and Huet. Read the original Curry-Howard paper. Do not touch Rocq yet. Build the mental model first.

**Week 2 — Installation and basics.** Install Rocq and an editor. Work through the term language directly: write lambda terms, check their types with `Check`, experiment with `Compute`. Write five small inductive types and their recursors by hand (without `induction` tactic). Prove five lemmas using only `exact`, `apply`, `intro`, `destruct`—no automation.

**Week 3 — Tactics, one by one.** Learn exactly fifteen tactics. Do not learn more. Prove twenty lemmas using only these fifteen. Understand what proof term each tactic produces (use `Show Proof.`).

**Week 4 — A real development.** Pick a small data structure (binary search trees, red-black trees, finite sets) and formalize it from scratch. Do not use library definitions—define everything yourself. Prove insertion preserves the invariant. Prove deletion preserves the invariant.

**Then read Software Foundations** — you will find it trivial, which is the correct state. It will fill in notation and idioms you skipped.

**Then read MathComp Book** (Mahboubi and Tassi): https://math-comp.github.io/mcb/. This is the production approach to algebraic formal mathematics.

**Then read a real proof**: The CompCert compiler verification, the Iris separation logic framework, or one of the four-color theorem proof files. Reading a large, real proof is the leap from competence to understanding.

**The primary sources**:
- CIC paper: Coquand, T., Huet, G. (1988). The calculus of constructions.
- Rocq Reference Manual: https://rocq-prover.org/doc/
- MathComp Book: https://math-comp.github.io/mcb/
- Software Foundations: https://softwarefoundations.cis.upenn.edu/
- Certified Programming with Dependent Types (CPDT): http://adam.chlipala.net/cpdt/

The famous misleading part of Software Foundations Volume 1: it builds the illusion that Rocq is essentially a fancy tactic language for propositional logic. It does not show you what Rocq is—a dependent type system—until much later. The result is that readers finish Volume 1 and cannot write a single dependent type. Start with dependent types. Everything else is easier once you have the type theory.

> **Principle 47.** *Understanding takes precedence over doing. One hour understanding CIC yields more insight than ten hours of tactic practice.*

---

## Appendix A — Core Vernacular Reference

| Command | Purpose |
|---------|---------|
| `Definition f : T := t.` | Bind name `f` of type `T` to term `t` (transparent) |
| `Lemma f : T. Proof. ... Qed.` | Bind name `f` of type `T` to an opaque proof |
| `Theorem f : T.` | Synonym for `Lemma` |
| `Corollary f : T.` | Synonym for `Lemma` |
| `Fixpoint f (x : T) : U := t.` | Recursive definition |
| `CoFixpoint f : T := t.` | Co-recursive definition (for coinductive types) |
| `Inductive T : s := ...` | Define inductive type with sort `s` |
| `CoInductive T : s := ...` | Define coinductive type |
| `Record R := mkR { field1 : T1; field2 : T2 }.` | Define record type |
| `Class C := { method : T }.` | Define typeclass |
| `Instance f : C := { method := ... }.` | Register typeclass instance |
| `Variable x : T.` | Declare section variable |
| `Hypothesis H : P.` | Declare section hypothesis |
| `Context {x : T}.` | Declare implicit section variable |
| `Parameter x : T.` | Declare global axiom without definition |
| `Axiom A : P.` | Declare axiom |
| `Notation "x + y" := (f x y).` | Declare notation |
| `Require Import M.` | Load and open module M |
| `Import M.` | Open already-loaded module M |
| `Section Name.` | Open a section |
| `End Name.` | Close section or module |
| `Module M.` | Open module |
| `Module Type MT.` | Open module signature |
| `Hint Resolve f : db.` | Add f to hint database db |
| `Hint Rewrite f : db.` | Add f as rewrite hint |
| `Set Option.` | Enable a Rocq option |
| `Unset Option.` | Disable a Rocq option |
| `Check t.` | Print type of t |
| `Print c.` | Print definition of c |
| `Print Assumptions c.` | Print axioms transitively used by c |
| `Search pattern.` | Search library for matching lemmas |
| `SearchRewrite pattern.` | Search for rewrite lemmas |
| `Locate str.` | Find where a name or notation is defined |
| `About c.` | Print metadata about c |
| `Compute t.` | Reduce t to normal form |
| `Show Proof.` | Print current proof term |
| `Show Goal.` | Print current goal |
| `Fail tac.` | Assert that tac fails |

---

## Appendix B — Tactic Reference

| Tactic | Effect |
|--------|--------|
| `intro x` | Introduce hypothesis or variable |
| `intros x y z` | Introduce multiple at once |
| `revert x` | Move variable back to goal |
| `generalize t` | Generalize over term t |
| `apply H` | Apply hypothesis or lemma backward |
| `apply H in H'` | Apply H forward to H' |
| `exact t` | Close goal with term t |
| `assumption` | Close goal with matching hypothesis |
| `refine t` | Apply term t, leaving holes |
| `eapply H` | Like apply but with evar creation |
| `eexact t` | Like exact but with evar creation |
| `destruct H` | Case analysis on H |
| `destruct H as [...]` | Case analysis with naming |
| `induction n` | Apply induction principle |
| `induction n as [...]` | Induction with naming |
| `inversion H` | Use injectivity/disjointness of constructors |
| `dependent destruction H` | Inversion for indexed types |
| `case H` | Like destruct without induction hypothesis |
| `simpl` | Simplify by computation |
| `simpl in H` | Simplify hypothesis H |
| `simpl in *` | Simplify everywhere |
| `cbn` | Call-by-need simplification |
| `cbv` | Call-by-value simplification |
| `unfold f` | Unfold definition of f |
| `fold f` | Fold definition of f |
| `change T` | Replace goal with definitionally equal T |
| `reflexivity` | Prove x = x |
| `symmetry` | Flip equality goal |
| `transitivity z` | Split equality via z |
| `rewrite H` | Rewrite using H : x = y (L→R) |
| `rewrite <- H` | Rewrite using H : x = y (R→L) |
| `rewrite H in H'` | Rewrite in hypothesis H' |
| `ring` | Prove ring equality |
| `field` | Prove field equality |
| `linarith` | Linear arithmetic |
| `lia` | Linear integer arithmetic |
| `omega` | Presburger arithmetic (deprecated; use lia) |
| `congruence` | Congruence closure |
| `tauto` | Propositional tautology |
| `firstorder` | First-order proof search |
| `auto` | Automated backward search |
| `eauto` | Like auto with evars |
| `trivial` | Simple automated search |
| `contradiction` | Close goal using False in context |
| `exfalso` | Change goal to False |
| `absurd P` | Change goal to P and ¬P |
| `split` | Split conjunction goal |
| `left` | Choose left disjunct |
| `right` | Choose right disjunct |
| `constructor` | Apply first matching constructor |
| `exists t` | Provide witness for existential |
| `have H : T` | Assert intermediate step |
| `assert (H : T)` | Same as have |
| `cut T` | Split goal into T and T→G |
| `pose proof t as H` | Add lemma instance to context |
| `specialize H with t` | Instantiate universal hypothesis |
| `clear H` | Remove hypothesis from context |
| `rename H into H'` | Rename hypothesis |
| `subst` | Substitute equalities in context |
| `f_equal` | Reduce goal f x = f y to x = y |
| `discriminate` | Disprove constructor disequality |
| `injection H` | Extract equalities from constructor equation |
| `vm_compute` | Fast kernel evaluation |
| `native_compute` | Fastest native evaluation |
| `Admitted` | Close goal without proof (danger) |
| `idtac` | No-op tactic (useful in sequences) |
| `fail` | Fail unconditionally |
| `try tac` | Apply tac; ignore failure |
| `repeat tac` | Apply tac until failure |
| `tac1; tac2` | Apply tac2 to all goals of tac1 |
| `first [t1 | t2 | ...]` | Try t1, then t2, ... |
| `{ tac }` | Focus on first goal |
| `all: tac` | Apply tac to all goals |

---

## Appendix C — Reduction Strategy Reference

| Strategy | Reduces | Notes |
|----------|---------|-------|
| `simpl` | β, ι, ζ, δ (fixpoints only) | Avoids unfolding without iota |
| `cbn` | β, ι, ζ, δ (lazy) | Better than simpl in many cases |
| `cbv` | β, ι, ζ, δ (all) | Can be too aggressive |
| `hnf` | Head normal form | One β/δ/ι/ζ at head |
| `red` | One δ at head | Conservative |
| `unfold f` | δ on f | Specific constant only |
| `fold f` | Reverse δ | Replace body with f |
| `vm_compute` | All (compiled) | Fast, small proof terms |
| `native_compute` | All (native code) | Fastest, large overhead |
| `lazy` | β, ι, ζ, δ (lazy) | Synonym for cbn in older versions |

When to use which:
- Use `simpl` or `cbn` in tactic proofs.
- Use `vm_compute` for large computations or proof-by-reflection.
- Use `native_compute` for very large computations (overhead from compilation).
- Use `unfold` to expose a specific definition for the next step.
- Avoid `cbv` unless you want everything unfolded.

---

## Appendix D — Ltac Cheat Sheet

```rocq
(* Sequential composition *)
tac1; tac2              (* apply tac2 to all goals of tac1 *)

(* Branching *)
tac1 || tac2            (* try tac1; if fails, try tac2 *)
first [tac1 | tac2]     (* same, explicit list *)
try tac                 (* apply tac; ignore failure *)

(* Repetition *)
repeat tac              (* apply until fails *)
do n tac                (* apply exactly n times *)

(* Goal matching *)
match goal with
| H : ?A ∧ ?B |- _ => destruct H
| |- ?A ∧ ?B => split
| _ => idtac
end

(* Term matching *)
match type of H with
| ?A → ?B => ...
| ∀ x, ?P x => specialize H with ...
end

(* Binding *)
let x := tac in ...     (* bind result of tac to x *)
let x := (eval simpl in t) in ...  (* evaluate in Ltac context *)

(* Naming fresh hypotheses *)
let H := fresh "H" in ...

(* Checking *)
assert_fails tac        (* succeed if tac fails *)
assert_succeeds tac     (* succeed if tac succeeds *)

(* Printing (debug) *)
idtac "message" t       (* print message and term *)

(* Goal counting *)
numgoals                (* tactic that succeeds with the count *)
```

---

## Appendix E — Glossary

**Axiom**: A declaration with a type but no definition. Everything proved using an axiom depends on it. See `Print Assumptions`.

**Binder**: An occurrence of a variable introduction: `fun x ⇒`, `∀ x,`, `let x :=`.

**Calculus of Inductive Constructions (CIC)**: The type theory underlying Rocq. Extends the Calculus of Constructions with inductive types and universe hierarchy.

**Canonical Structure**: A record instance registered with Rocq's unification mechanism for ad-hoc polymorphism inference.

**Constructor**: A function that introduces values of an inductive type. `O` and `S` are constructors of `nat`.

**Curry-Howard Correspondence**: The identification of propositions with types and proofs with programs.

**Definitional equality**: Equality by reduction to a common normal form. Requires no proof; checked by the kernel.

**Dependent type**: A type that depends on a value. `Vector A n` depends on the value `n : nat`.

**Eliminator / Recursor**: The automatically generated principle for using values of an inductive type. `nat_rect` is the eliminator for `nat`.

**Evar**: An existential variable — a hole in a proof term awaiting a value.

**Guard condition**: The syntactic check ensuring that all `Fixpoint` definitions are structurally recursive (and hence terminating).

**Implicit argument**: An argument inferred by Rocq from context, not written explicitly.

**Inductive family**: An inductive type indexed by values, such that different constructors produce types with different index values.

**Kernel**: Rocq's trusted type-checking core. The only component whose correctness is essential for soundness.

**Ltac**: Rocq's tactic meta-language, used to write custom tactics.

**Normal form**: A term that cannot be reduced further. Every term in Rocq reduces to a unique normal form (for the confluent fragment).

**Opaque**: A definition whose body is hidden from the type-checker. Proofs closed with `Qed` are opaque.

**Parameter (of inductive type)**: An argument fixed across all constructors of an inductive type, appearing before the `:` in the type declaration.

**Index (of inductive type)**: An argument that varies per constructor of an inductive type, appearing after the `:` in the type declaration.

**Positivity condition**: The requirement that an inductive type's constructors mention the type only in positive positions (not as arguments to function types).

**Proof irrelevance**: The property that any two proofs of the same `Prop` are equal. Follows from proof-irrelevance axiom or from the structure of `Prop`.

**Proof state**: The current set of goals and hypotheses during an interactive proof.

**Prop**: The sort of propositions. Proof-irrelevant; not extractable.

**Propositional equality**: Equality asserted as a proposition, requiring a proof. Written `x = y`.

**Recursor**: See Eliminator.

**Reduction**: The application of one of the five reduction rules (β, δ, ζ, ι, η) to a term.

**Setoid**: A type with an equivalence relation registered for use with `setoid_rewrite`.

**Sort**: The type of a type. The three sorts are `Prop`, `Set`, and `Type`.

**Tactic**: A command in proof mode that transforms the proof state.

**Term**: Any syntactic expression in Rocq's core language. Functions, proofs, types, propositions, and data are all terms.

**Transparent**: A definition whose body is visible to the type-checker for reduction. Definitions made with `Definition` or `Defined` are transparent.

**Type class**: A record with instances that Rocq infers by searching registered `Instance` declarations.

**Universe**: A `Type_i` in the universe hierarchy. Rocq infers universe levels automatically.

**Vernacular**: The command language in which you issue declarations, queries, and configuration changes to Rocq.

**Well-founded recursion**: A recursion scheme based on a well-founded relation, allowing terminating functions that are not structurally recursive.

---

> *A proof that you do not understand is not your proof. It is a sequence of tactics that happened to satisfy the kernel. Understanding is when you can reconstruct it from scratch, explain each step to a colleague, and recognize the same argument in a different notation. Everything before that is practice.*

# Cryptographie Asymétrique — Fondements et Applications

*Un manuel académique de référence pour l'architecte système embarqué.*

---

## Préface

Ce livret présente les fondements de la cryptographie asymétrique dans un format
continu, comparable à un ouvrage académique imprimé. Il s'adresse à l'ingénieur
qui doit déployer des primitives à clé publique sur des systèmes à ressources
contraintes, et comprendre les choix architecturaux qui en découlent.

La cryptographie asymétrique accomplit exactement deux choses : elle permet à une
partie de **prouver la possession d'un secret** sans le révéler, et elle permet à
deux parties d'**établir un secret partagé** sans en transmettre aucun. Tout le
reste est conséquence.

---

# Partie I — Orientation

## Chapitre 1 — La Dualité : Connaissance Publique et Capacité Secrète

### 1.1 Le problème fondamental

Supposons que deux parties, Alice et Bob, souhaitent communiquer de manière
confidentielle sur un canal non sécurisé. La cryptographie symétrique exige
qu'elles partagent *au préalable* une clé secrète — ce qui reporte le problème
plutôt qu'il ne le résout.

La cryptographie asymétrique tranche ce nœud gordien en introduisant une
**paire de clés** mathématiquement liées :

- La **clé publique** peut être distribuée librement, sans précaution.
- La **clé privée** n'est connue que de son propriétaire et ne quitte jamais son
  dispositif.

| Propriété           | Clé publique    | Clé privée          |
|---------------------|-----------------|---------------------|
| Diffusion           | Libre           | Confidentielle      |
| Stockage            | Non protégé     | HSM / Secure Element|
| Durée de vie        | Longue          | Limitée, renouvelée |
| Compromission       | Sans effet      | Catastrophique      |

### 1.2 Asymétrie calculatoire

La sécurité repose sur un **problème difficile** : une opération facile dans un
sens, computationnellement infaisable dans l'autre. Les candidates actuelles sont :

- Le **logarithme discret** sur les courbes elliptiques (ECC)
- La **factorisation** de grands entiers (RSA)
- Les **problèmes sur les réseaux euclidiens** (post-quantique : Kyber, Dilithium)

> *La difficulté n'est pas absolue — elle est relative à la puissance de calcul
> disponible aujourd'hui et dans les décennies à venir.*

---

## Chapitre 2 — Ce que Fournit (et ne Fournit pas) la Cryptographie Asymétrique

### 2.1 Services fournis

La cryptographie asymétrique garantit quatre propriétés de sécurité :

1. **Confidentialité** — chiffrement à clé publique, KEM
2. **Authenticité** — signature numérique
3. **Intégrité** — signature numérique (couvre les deux)
4. **Non-répudiation** — signature numérique avec certificat

### 2.2 Ce qu'elle ne fournit pas

- **Performance** : une opération ECC coûte 10 000× plus qu'une opération AES.
  Elle ne remplace jamais le chiffrement symétrique pour le flux de données.
- **Sécurité post-quantique** : RSA et ECC sont brisés par l'algorithme de Shor
  sur un ordinateur quantique suffisamment grand. Les algorithmes NIST PQC
  (`ML-KEM`, `ML-DSA`) comblent cette lacune.
- **Authenticité de la clé publique** elle-même : une clé publique sans
  certificat ne prouve rien. L'infrastructure PKI est indispensable.

---

# Partie II — Primitives

## Chapitre 3 — Signature Numérique

### 3.1 Principe

La signature numérique est le dual de l'authentification par défi-réponse :
l'expéditeur signe avec sa **clé privée**, le destinataire vérifie avec la
**clé publique** correspondante.

```
message  ─────►  hash(message)  ─────►  Sign(hash, privKey)  ─────►  signature
```

La vérification :

```
Verify(signature, hash(message), pubKey)  →  true | false
```

### 3.2 ECDSA vs EdDSA

| Critère              | ECDSA (P-256)          | EdDSA (Ed25519)         |
|----------------------|------------------------|-------------------------|
| Nonce `k`           | Aléatoire — fatal si réutilisé | Déterministe (RFC 8032) |
| Résistance SCA       | Faible sans contre-mesures | Forte par construction  |
| Taille signature     | 64 octets              | 64 octets               |
| Vitesse (Cortex-M4) | ~300 ms (sw)           | ~120 ms (sw)            |
| Maturité TLS         | Omniprésent            | TLS 1.3, SSH, WireGuard |

> **Règle pratique** : Préférez Ed25519 pour tout nouveau système. Utilisez
> ECDSA P-256 uniquement si la conformité TLS 1.2 ou une certification FIPS l'exige.

### 3.3 Code d'exemple — vérification Ed25519 avec wolfSSL

```c
#include <wolfssl/wolfcrypt/ed25519.h>

int verify_firmware_signature(
    const uint8_t *msg,   uint32_t msg_len,
    const uint8_t *sig,   uint32_t sig_len,
    const uint8_t *pubkey)
{
    ed25519_key key;
    int ret, verified = 0;

    wc_ed25519_init(&key);
    ret = wc_ed25519_import_public(pubkey, ED25519_PUB_KEY_SIZE, &key);
    if (ret != 0) goto cleanup;

    ret = wc_ed25519_verify_msg(sig, sig_len, msg, msg_len, &verified, &key);

cleanup:
    wc_ed25519_free(&key);
    return (ret == 0 && verified == 1) ? 0 : -1;
}
```

---

## Chapitre 4 — Accord de Clés

### 4.1 ECDH et X25519

L'accord de clés Diffie-Hellman sur courbes elliptiques (**ECDH**) permet à
deux parties de dériver un secret partagé sans jamais le transmettre :

$$
\text{shared\_secret} = d_A \cdot Q_B = d_B \cdot Q_A
$$

où $d_A, d_B$ sont les scalaires privés et $Q_A, Q_B$ les points publics.

**X25519** (Curve25519, RFC 7748) est la variante moderne :

- Formule de Montgomery : résistante aux attaques par canal auxiliaire par construction
- API simplifiée : pas de choix de courbe, pas de validation de point nécessaire
- Recommandé pour TLS 1.3, MQTT avec TLS, et les protocoles IoT modernes

### 4.2 Contraintes embarquées

Sur un Cortex-M4 sans accélérateur matériel :

| Primitive   | Temps (~120 MHz) | RAM pic | Flash (wolfSSL) |
|-------------|------------------|---------|-----------------|
| X25519      | 180 ms           | 3 KB    | 12 KB           |
| ECDH P-256  | 310 ms           | 4 KB    | 18 KB           |
| RSA-2048    | 1 200 ms         | 10 KB   | 28 KB           |

---

# Partie III — Infrastructure et PKI

## Chapitre 5 — Certificats et Chaînes de Confiance

### 5.1 Structure d'un certificat X.509

Un certificat X.509 v3 lie une **identité** à une **clé publique**, avec la
signature d'une autorité de certification (**CA**) :

```
Certificate ::= SEQUENCE {
    tbsCertificate   TBSCertificate,
    signatureAlgorithm AlgorithmIdentifier,
    signature        BIT STRING
}
```

Les champs critiques pour l'embarqué :

- `SubjectPublicKeyInfo` — la clé publique du titulaire
- `Validity` — dates `notBefore` / `notAfter` (attention : RTC requis)
- `BasicConstraints` — distingue CA feuille de CA intermédiaire
- `KeyUsage` — restreint l'usage (signature, chiffrement, cert sign…)

### 5.2 Démarrage sécurisé (Secure Boot)

La chaîne de confiance au démarrage repose sur la cryptographie asymétrique :

```
OTP Root Key (gravée en usine)
    └── vérifie → Bootloader Certificate
                      └── vérifie → Application Certificate
                                        └── vérifie → Firmware Image
```

Chaque maillon vérifie le suivant via une signature numérique. La compromission
d'une clé ne remonte pas la chaîne vers la racine.

---

## Chapitre 6 — Post-Quantique : Vue d'ensemble

### 6.1 Menace de l'algorithme de Shor

Un ordinateur quantique tolérant aux pannes exécutant l'algorithme de Shor
brise RSA et ECC en temps polynomial. Les estimations actuelles situent la
menace à **10–20 ans**, mais la doctrine *"harvest now, decrypt later"* justifie
une migration anticipée.

### 6.2 Standards NIST PQC (2024)

| Standard   | Primitive        | Usage         | Clé publique | Signature |
|------------|------------------|---------------|--------------|-----------|
| ML-KEM     | Kyber (réseaux)  | KEM/échange   | 800–1568 B   | —         |
| ML-DSA     | Dilithium        | Signature      | 1312–2592 B  | 2420–4595 B|
| SLH-DSA    | SPHINCS+         | Signature (stateless) | 32–64 B | 7856–49856 B |

> **Impact embarqué** : les tailles de clés et signatures sont 10–100× plus
> grandes qu'en ECC. Planifier la mémoire Flash et les protocoles réseau en
> conséquence.

---

*Fin de l'exemple de livret. Ce document illustre le rendu A4 portrait avec
table des matières automatique, en-têtes courants et numérotation des pages.*

---

# Introduction à la Science des Données

**Formateur** : Dr. Martin Dupont
**Date** : 08/06/2026
**Institut** : Université Paris-Saclay

---

# Objectifs du cours

À la fin de cette formation, vous serez capables de :

1. Comprendre les fondamentaux du **Machine Learning**
2. Manipuler des jeux de données avec **Pandas**
3. Visualiser des résultats avec **Matplotlib**
4. Implémenter un pipeline complet de classification

> « Sans données, vous n'êtes qu'une personne de plus avec une opinion. » — W. Edwards Deming

---

# Les Familles d'Algorithmes

Le Machine Learning repose sur trois grandes approches :

- **Apprentissage supervisé**
  - Régression linéaire / logistique
  - Forêts aléatoires
  - Support Vector Machines (SVM)
  - Réseaux de neurones
- **Apprentissage non supervisé**
  - K-Means, DBSCAN
  - Analyse en Composantes Principales (ACP)
  - Autoencodeurs
- **Apprentissage par renforcement**
  - Q-Learning
  - Deep Q-Network (DQN)

---

# Chargement de données avec Pandas

```python
import pandas as pd

df = pd.read_csv("data/iris.csv")

print(f"Dimensions : {df.shape}")
print(f"Colonnes   : {list(df.columns)}")
print(df.describe())
```

Résultat attendu : un DataFrame de **150 lignes × 5 colonnes**.

---

# Visualisation avec Matplotlib

```python
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(0, 2 * np.pi, 200)
fig, axes = plt.subplots(1, 3, figsize=(14, 4))

for ax, func, name in zip(axes, [np.sin, np.cos, np.tan], ["sin", "cos", "tan"]):
    ax.plot(x, func(x), color="#006400", linewidth=2)
    ax.set_title(f"y = {name}(x)")
    ax.set_xlabel("x")
    ax.grid(True, alpha=0.3)

axes[2].set_ylim(-5, 5)
plt.tight_layout()
plt.savefig("trig_functions.png", dpi=150)
```

---

# Équations Fondamentales

**Régression linéaire** — fonction de coût :

$$
J(\theta) = \frac{1}{2m} \sum_{i=1}^{m} \left( h_\theta(x^{(i)}) - y^{(i)} \right)^2
$$

**Descente de gradient** :

$$
\theta_j := \theta_j - \alpha \frac{\partial}{\partial \theta_j} J(\theta)
$$

Où $\alpha$ est le taux d'apprentissage et $m$ le nombre d'échantillons.

---

# Entropie croisée (Classification)

Pour un problème à $K$ classes :

$$
\mathcal{L} = -\frac{1}{N} \sum_{i=1}^{N} \sum_{k=1}^{K} y_{ik} \log(\hat{y}_{ik})
$$

Cas binaire ($K = 2$) :

$$
\mathcal{L} = -\frac{1}{N} \sum_{i=1}^{N} \left[ y_i \log(\hat{y}_i) + (1 - y_i) \log(1 - \hat{y}_i) \right]
$$

---

# Pipeline scikit-learn

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", RandomForestClassifier(n_estimators=100, random_state=42)),
])

scores = cross_val_score(pipeline, X, y, cv=5, scoring="accuracy")
print(f"Accuracy : {scores.mean():.2f} ± {scores.std():.2f}")
```

---

# Matrice de confusion

![Matrice de confusion](https://upload.wikimedia.org/wikipedia/commons/2/26/Precisionrecall.svg)

*Figure : Précision, Rappel et la relation entre vrais/faux positifs et négatifs.*

---

# Résumé et prochaines étapes

| Thème                 | Statut      |
|-----------------------|-------------|
| Fondamentaux ML       | ✅ Terminé   |
| Manipulation données  | ✅ Terminé   |
| Visualisation         | ✅ Terminé   |
| Modélisation          | ✅ Terminé   |
| Deep Learning         | 🔜 Prochain |

**Ressources recommandées** :

- *Hands-On Machine Learning* — Aurélien Géron
- *Deep Learning* — Ian Goodfellow et al.
- Documentation scikit-learn : [scikit-learn.org](https://scikit-learn.org)

**Merci !** — Questions ?

---

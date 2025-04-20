### 1.1 Partition de l’image selon l’axe des ordonnées

La première étape consiste à diviser **X** en **n** sous-parties mutuellement disjointes, selon **sa hauteur** (son axe *y*).

Cela produit une **partition de l’image** :

**X = X₁ ∪ X₂ ∪ ... ∪ Xₙ**

Pour tout *i* et *j*, les ensembles **Xᵢ** et **Xⱼ** sont **disjoints** (si *i ≠ j*) : ils sont *partes extra partes*, et la réunion de tous les **Xᵢ** reconstitue **X** dans sa totalité.

### 1.2.1 Partition avec recouvrement

Nous opérons un **OCR** (_Optical character recognition_ )à l’aide d’un LLM multimodal avec _Chain-of-Thought_ (CoT).

Ce LLM doit pouvoir **deviner certains mots par leur contexte**, c’est-à-dire en s’appuyant sur les **mots et phrases environnants**.  
Dès lors, au lieu de lui transmettre simplement chaque sous-partie de l’image **X** l’une après l’autre (par exemple : `X₁`, puis `X₂`, puis `X₃`, etc.), nous adoptons une stratégie **de recouvrement** :

- au lieu de :  
  `X₁`, `X₂`, `X₃`, `X₄`, ...

- nous transmettons :  
  `X₁ ∪ X₂`, `X₂ ∪ X₃`, `X₃ ∪ X₄`, ...

Autrement dit, le LLM passe deux fois sur certaines lignes, ce qui permet **de croiser les résultats** comme on le montre ci-dessous.

### 1.2.2. Chevauchement de séquences

Notons **S** la séquence de mots issue de l’OCR appliqué à la sous-image `X₁ ∪ X₂`, et w₁ un mot. On a **S** = `(w₁, w₂, ..., wₙ)`

Le texte effectivement contenu dans `X₂` apparaît dans **S** à partir d’un certain indice **i > 1**. On a donc `Texte(X₂) ⊂ S` (i.e. le texte de `X₂` constitue une sous-séquence stricte de **S**).

De la même manière, notons **S′** = `(w′₁, w′₂, ..., w′ₙ)` la sortie de l’OCR sur `X₂ ∪ X₃`. Le texte contenu dans `X₂` se termine à un certain indice **i′**, tel que `X₂ = (w′₁, ..., w′ᵢ′)` avec `i′ < n` (i.e. le texte de `X₂` constitue une sous-séquence stricte de **S'** : `Texte(X₂) ⊂ S′`).

### Baser les sous-parties X₁ ∪ X₂ ∪ ... ∪ Xₙ sur les lignes

Il faut idéalement effectuer une analyse des coordonnées de chaque ligne de la copie au format PNG avant la partitionner en sous-parties `X₁ ∪ X₂ ∪ ... ∪ Xₙ`.





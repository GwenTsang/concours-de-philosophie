### Partition de l’image selon l’axe des ordonnées

La première étape consiste à diviser **X** en **n** sous-parties mutuellement disjointes, selon **sa hauteur** (son axe *y*).

Cela produit une **partition de l’image** :

**X = X₁ ∪ X₂ ∪ ... ∪ Xₙ**

Pour tout *i* et *j*, les ensembles **Xᵢ** et **Xⱼ** sont **disjoints** (si *i ≠ j*) : ils sont *partes extra partes*, et la réunion de tous les **Xᵢ** reconstitue **X** dans sa totalité.

### Partition avec recouvrement

Nous opérons un **OCR** (_Optical character recognition_ )à l’aide d’un LLM multimodal avec _Chain-of-Thought_ (CoT).

Ce LLM doit pouvoir **deviner certains mots par leur contexte**, c’est-à-dire en s’appuyant sur les **mots et phrases environnants**.  
Dès lors, au lieu de lui transmettre simplement chaque sous-partie de l’image **X** l’une après l’autre (par exemple : `X₁`, puis `X₂`, puis `X₃`, etc.), nous adoptons une stratégie **de recouvrement** :

- au lieu de :  
  `X₁`, `X₂`, `X₃`, `X₄`, ...

- nous transmettons :  
  `X₁ ∪ X₂`, `X₂ ∪ X₃`, `X₃ ∪ X₄`, ...

Autrement dit, **le LLM passera deux fois sur `X₂` et `X₃`**, ce qui permet **de croiser les résultats** et d’estimer plus finement le texte présent dans ces zones communes.

Notons **S** la séquence de mots issue de l’OCR appliqué à la sous-image `X₁ ∪ X₂` :

**S = (w₁, w₂, ..., wₙ)**

Le texte effectivement contenu dans `X₂` apparaît dans **S** à partir d’un certain indice **i > 1**.


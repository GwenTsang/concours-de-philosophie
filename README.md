# Traitement automatisé des copies scannées

L'objectif est de transcrire de manière fidèle des copies manuscrites scannées en fichiers texte, en minimisant les erreurs d'interprétation par l'OCR et en structurant rigoureusement les données extraites.

---

## Étapes


### 1. Centralisation des sources

Tous les fichiers PDF correspondant aux scans de copies sont regroupés dans un **unique répertoire**, appelé `folder`.

---

### 2. Conversion des pages PDF en images PNG

Chaque page de chaque fichier PDF dans `folder` est convertie en format PNG,  en couleur,  avec une résolution de 300 DPI.

Un sous-dossier distinct est créé pour chaque copie dans un dossier principal (portant le même nom que le fichier PDF).

---

### 3. Suppression de l'encart de numérotation

Chaque image PNG comporte en bas à droite un encart de numérotation qui doit être supprimé.  
Cette suppression s'effectue selon des coordonnées fixes \((x_0, y_0, x_1, y_1)\), définissant un rectangle à retirer.

**Motivation** :  
Lors de l'étape d'OCR, si cet encart est conservé, le LLM recopie les numéros, générant des erreurs de transcription.  
De plus, cette suppression doit précéder tout autre traitement, car le rognage du header modifie la dimension des images, or la position de l'encart dépend directement de la hauteur et de la largeur de l'image.

---

### 4. Détermination de la séparation Header / Corps du texte

On calcule, pour chaque image, une **coordonnée \( y^* \)** sur l'axe vertical, qui sépare le **header** (zone administrative) du **corps manuscrit** (texte utile).

Formellement, pour chaque image \( X \) :

\[
X = H(X) \cup C(X)
\]

où :

- \( H(X) = \{ (x, y) \in X \, | \, 0 \leq y \leq y^* \} \) est le header,
- \( C(X) = \{ (x, y) \in X \, | \, y^* < y \leq \text{Hauteur}(X) \} \) est le corps du texte.

La valeur de \( y^* \) est déterminée de manière semi-automatique, puis appliquée à toutes les pages dans les différents sous-dossiers.

---

### 5. Détection et suppression manuelle des pages blanches

Une détection automatique est effectuée par calcul d'un **seuil de contraste global** de l’image, pour isoler les images "blanches".

Cependant, certaines écritures (notamment à l’encre bleue) produisent un contraste général faible. La vérification est donc semi-automatique, chaque image est soumise à une validation manuelle avec deux options :
- `Keep` : conserver l’image,
- `Delete` : supprimer l’image.

---

### 6. Détection des lignes et partition en blocs

#### 6.1 Extraction des interlignes

Chaque image est analysée pour supprimer l'arrière-plan blanc (détourage),
- détecter les interlignes du texte manuscrit.

Le modèle suppose un espacement vertical approximatif de \(87 \pm 3\) pixels entre deux lignes successives.

Un algorithme d'optimisation détermine les positions \( y_1, y_2, \dots, y_n \) des lignes manuscrites, en minimisant les écarts à cet espacement attendu.

---

#### 6.2 Partition de l’image

L’image \( X \) est alors **découpée verticalement** en blocs :

\[
X = X_1 \cup X_2 \cup \cdots \cup X_n
\]

où :

- chaque bloc \( X_i \) contient environ **13 lignes** de texte manuscrit,
- les blocs sont **chevauchants** : chaque \( X_i \) recouvre **2 lignes** avec \( X_{i-1} \) et \( X_{i+1} \).

Formellement, si \( L_i \) désigne l’ensemble des lignes contenues dans \( X_i \), alors :

\[
L_{i} \cap L_{i+1} = \quad \text{(2 lignes partagées)}
\]

En fin de traitement si le dernier chunk d'une page contient trop peu de lignes (par exemple 1 ou 2 lignes isolées), il est fusionné avec le chunk précédent afin d'assurer la cohérence.

---

### 7. Suppression des chunks vides ou suspects

Un second filtre est appliqué pour supprimer les fichiers de taille trop petite, ou à contraste trop faible.

**Justification** :  
certaines pages résiduelles, contenant très peu de texte, peuvent produire des chunks inutiles ou vides qu’il convient d’éliminer.

---

### 8. Transcription par LLM multimodal

Chaque chunk \( X_i \) est transmis à un LLM multimodal (Gemini 2.5 Pro) pour transcription via OCR.

Pour chaque chunk \( X_i \) le contexte fourni au LLM comprend le texte transcrit des deux chunks précédents (\( X_{i-2}, X_{i-1} \)), et le sujet de la dissertation est inséré dans un prompt système personnalisé.

Ce choix de contextualisation restreinte vise à éviter que le LLM privilégie la continuation logique du texte au détriment de la fidélité stricte à l’image.

La transcription de \( X_i \) est ensuite enregistrée dans un fichier CSV, avec un léger formatage Markdown appliqué.

---

### 9. Post-traitement des textes transcrits

Chaque fichier CSV est ensuite post-traité :

- Suppression des sauts de ligne inutiles,
- Fusion correcte des mots coupés par des tirets (à la fin d'une ligne et au début de la suivante),
- Détection des erreurs de chevauchement par calcul de la distance de Levenshtein entre mots adjacents.

Les mots répétés deux fois sont marqués en rouge pour validation ultérieure.

---

## Remarque technique sur la détection automatique du header

Deux méthodes automatiques ont été envisagées pour détecter la fin du header :

1. **Recherche de mots-clés** :
   - le script détecte la présence de termes caractéristiques (e.g. "Nom", "Prénom"),
   - mais l’espace entre le dernier mot-clé et le début du texte manuscrit est variable selon les copies, empêchant une généralisation fiable.

2. **Détection de la note en rouge** :
   - la note (chiffre rouge) est unique dans l’image et facilement détectable,
   - toutefois, l’espacement vertical sous la note est lui aussi non constant, empêchant là aussi une généralisation fiable.

---

# Détails

- Chaque image \( X \) est partitionnée selon l’axe des ordonnées :

\[
X = \bigcup_{i=1}^n X_i
\quad \text{avec} \quad X_i \cap X_j = \varnothing \quad (i \neq j)
\]

- Chaque sous-image \( X_i \) est agrandie en \( X_i \cup X_{i+1} \) pour garantir **recouvrement contextuel**.
- L'OCR produit deux séquences \( S \) et \( S' \) permettant de **croiser les résultats** et **fiabiliser la reconstitution** du texte.

---

Veux-tu que je te propose maintenant une version **full Markdown** prête à être intégrée directement dans ton `README.md` (avec les titres stylés `##`, `###`, mises en gras, encadrés, emojis si tu veux) ?  
Cela rendrait encore plus professionnel ton document. 🚀  
Veux-tu aussi que je te propose une mini-table des matières automatique ?

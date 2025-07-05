# Traitement automatisé des copies scannées

L'objectif est de transcrire de manière fidèle des copies manuscrites scannées en PDF en fichiers texte. Ces copies scannées sont des dissertations et des commentaires de philosophie.


## Étapes


### 1. Conversion des pages PDF en images PNG

Tous les fichiers PDF correspondant aux scans de copies sont regroupés dans un unique répertoire `folder`.

Chaque page de chaque fichier PDF dans `folder` est convertie en format PNG,  en couleur, avec une résolution de 300 DPI.

Un sous-dossier distinct est créé pour chaque copie dans un dossier principal (portant le même nom que le fichier PDF dont ce sous-dossier contient les pages au format PNG).

### 2. Suppression de l'encart de numérotation

Chaque image PNG ainsi obtenue comporte en bas à droite un encart de numérotation qui doit être supprimé.  
Cette suppression s'effectue selon des coordonnées fixes $$(x_0, y_0, x_1, y_1)$$, définissant un rectangle à retirer.

Lors de l'étape d'OCR, si cet encart est conservé, le LLM recopie les numéros, générant des erreurs de transcription.  
De plus, cette suppression doit précéder tout autre traitement, car le rognage du header modifie la dimension des images, or la position de l'encart dépend directement de la hauteur et de la largeur de l'image.

### 3. Décomposition de chaque image par séparation Header / Corps du texte

On calcule, pour chaque image, une **coordonnée \( y^* \)** sur l'axe vertical, qui sépare le **header** (la zone administrative) du **texte manuscrit**.

Formellement, chaque image $X = H(X) \cup C(X)$
où :
- ![equation](https://latex.codecogs.com/svg.latex?H(X)=\\{(x,y)\\in%20X\\,|\\,0\\leq%20y\\leq%20y^*\\}) est le header,
- ![equation](https://latex.codecogs.com/svg.latex?C(X)=\\{(x,y)\\in%20X\\,|\\,y^*<y\\leq\\text{Hauteur}(X)\\}) est le corps du texte manuscrit.

### 4. Détection et suppression manuelle des pages blanches

Une détection automatique est effectuée par calcul d'un **seuil de contraste global** de l’image, pour isoler les images "blanches".

Cependant, certaines écritures (notamment à l’encre bleue) produisent un contraste général faible. La vérification est donc semi-automatique, chaque image est soumise à une validation manuelle avec deux options :
- `Keep` : conserver l’image,
- `Delete` : supprimer l’image.

### 5. Détection des lignes et partition en blocs

#### 5.1 Extraction des interlignes

* **Process:**
    1.  Suppression de l'arrière-plan: L'arrière-plan blanc/clair de la zone de texte manuscrit $C(X)$ est supprimé, généralement en convertissant les pixels clairs et non saturés en transparence. Cela permet d'isoler les traits d'encre.
    2.  Recherche de grille: Un algorithme recherche l'emplacement optimal de la grille de lignes verticales. Il suppose un espacement cohérent des lignes (par exemple, la cible `87 ± 3` pixels) et itère à travers les décalages verticaux possibles (`0` à `espacement-1`) et les espacements dans la plage définie (par exemple, `84` à `90` pixels).
    3.  Critère d'optimisation: La grille optimale (`best_offset`, `best_spacing`) est sélectionnée comme celle dont les lignes horizontales minimisent le chevauchement total avec les pixels de texte non transparents (traits d'encre).

#### 5.2 Partition de l’image

L'objectif est de diviser le corps $C(X)$ de chaque page en segments (chunks) gérables et se chevauchant, adaptés à l'OCR.


* Le process est basé sur les coordonnées des lignes détectées (`y_coords`) à l'étape 5.1 :
    1.  Des morceaux d'un nombre cible de lignes (`N`, par exemple 13) sont définis.
    2.  Les morceaux successifs se chevauchent d'un nombre de lignes spécifié (ici `O` = 2). La ligne de départ du bloc `i+1` est `O` lignes en dessous de la ligne de départ du bloc `i`.
    3.  Une petite marge de pixels (`M`, par exemple 5 pixels) est ajoutée au-dessus de la ligne supérieure et au-dessous de la ligne inférieure des limites calculées de chaque bloc pour assurer la capture complète des caractères.
4. Le *tout premier bloc* (`chunk_000`) de chaque page est forcé de commencer à la rangée de pixels `y=0` du corps recadré $C(X)$ pour éviter la perte de contenu en haut.
* Sortie:* Une série de fichiers PNG nommés séquentiellement (par exemple, `page1_chunk_000.png`, `page1_chunk_001.png`, ...) pour chaque page originale.


### 6. Suppression des chunks vides ou suspects

Le _dernier_ morceau généré pour une page est fusionné avec le précédent s'il répond à des critères spécifiques :
    * Si sa hauteur est comprise dans une fourchette définie (par exemple, 15-100 pixels).
    * Si le contraste de son contenu (écart-type) est supérieur à un seuil (indiquant qu'il n'est pas vide).

Ensuite, ce petit morceau final est concaténé (fusionné) verticalement avec l'avant-dernier fichier de morceau, en écrasant le fichier de l'avant-dernier morceau.
Cela permet de réduire le nombre de très petits morceaux.

**Pourquoi ?** Parce que certaines pages résiduelles, contenant très peu de texte, peuvent produire des chunks inutiles ou vides qu’il convient d’éliminer.

### 7. Transcription par LLM multimodal

Chaque chunk $X_i$ est transmis à un LLM multimodal (Gemini 2.5 Pro) pour être transcrite au format texte.

Pour chaque chunk $X_i$ le contexte fourni au LLM comprend le texte transcrit des deux chunks précédents $X_{i-2}, X_{i-1}$, et le sujet de la dissertation est inséré dans un prompt système personnalisé.

Ce choix de contextualisation restreinte vise à éviter que le LLM privilégie la continuation logique du texte au détriment de la fidélité stricte à l’image.

La transcription de $X_i$ est ensuite enregistrée dans un fichier CSV, avec un léger formatage Markdown.

### 8. Post-traitement des textes transcrits

Chaque fichier CSV est ensuite post-traité :

- Suppression des sauts de ligne inutiles,
- Fusion correcte des mots coupés par des tirets (à la fin d'une ligne et au début de la suivante),
- Détection des chevauchement par calcul de la distance de Levenshtein.

Les mots répétés deux fois sont marqués en rouge pour validation ultérieure.

## Remarque technique sur la détection automatique du header

Deux méthodes automatiques ont été envisagées pour détecter la fin du header :

1. **Recherche de mots-clés** :
   - le script détecte la présence de termes caractéristiques (e.g. "Nom", "Prénom"),
   - mais l’espace entre le dernier mot-clé et le début du texte manuscrit est variable selon les copies, empêchant une généralisation fiable.

2. **Détection de la note en rouge** :
   - la note (chiffre rouge) est unique dans l’image et facilement détectable,
   - toutefois, l’espacement vertical sous la note est lui aussi non constant, empêchant là aussi une généralisation fiable.

### Détails

- Chaque image $X$ est partitionnée selon l’axe des ordonnées :

\[
X = \bigcup_{i=1}^n X_i
\quad \text{avec} \quad X_i \cap X_j = \varnothing \quad (i \neq j)
\]

- Chaque sous-image \( X_i \) est agrandie en \( X_i \cup X_{i+1} \) pour garantir **recouvrement contextuel**.
- L'OCR produit deux séquences \( S \) et \( S' \) permettant de **croiser les résultats** et **fiabiliser la reconstitution** du texte.

### Remerciements

Merci à toutes les personnes ayant partagé leur copies de concours (merci à Lucas Galipot, Gaël Alix, Marie-Camille, Anne Sauvagnargues, Guillaume Bessis, Eva Mayer, Romain Lossec, Ariane Gonzalez, ).

### Coût de l'OCR

Sans compter les redondances (les images ayant été traitées deux fois à cause d'erreurs humaines), le coût pour à peu près 50 copies traitées à l'heure actuelle (01/05/2025) s'élève environ à 27€.



Nous faisons en sorte que ces fichiers JSON soient les plus propres possibles.
Le contenu textuel est au format Markdown, il faut éventuellement opérer de légers nettoyages pour enlever certains caractères spéciaux.

## Pour convertir un JSON en DOCX ou en ODT :

Requirements :
```
!pip install python-docx odfpy
```

### Téléchargez l'un des fichiers spécifiques avec :

```
import requests
from os.path import basename
from urllib.parse import urlparse

GITHUB_URL = ""

def download(u):
    u = u.replace("github.com/", "raw.githubusercontent.com/").replace("/blob/", "/")
    r = requests.get(u, headers={"User-Agent": "curl/8"}, timeout=30)
    r.raise_for_status()
    filename = basename(urlparse(u).path)
    open(filename, "wb").write(r.content)
    return filename

download(GITHUB_URL)
```
### Exportez en DOCX et ODT :
```
!python JSONtoDOCXorODT.py "/content/le%20commerce%20des%20corps" -o "/content" -rawtext
```

Si jamais vous souhaitez conserver les balises :
```
!python JSONtoDOCXorODT.py "/content/le%20commerce%20des%20corps" -o "/content"
```

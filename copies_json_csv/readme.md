Je fais en sorte que ces fichiers soient les plus propres possibles.
Ils sont au format Markdown, il faut éventuellement opérer de légers nettoyages pour enlever certains caractères spéciaux.
Test :

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
Ensuite l'exportation peut se faire avec :
```
!python JSONtoDOCXorODT.py "PATH_JSON" -o "/content"
```

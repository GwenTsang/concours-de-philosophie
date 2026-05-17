import os
import sys
import time
import json
import pathlib
import requests
from urllib.parse import urlparse

API_BASE = "https://api.github.com"

def parse_github_folder_url(url: str):
    """
    Accepte des URLs de type:
      https://github.com/<owner>/<repo>/tree/<ref>/<path...>
      https://github.com/<owner>/<repo>/blob/<ref>/<path...>  (peu probable ici)
    Retourne (owner, repo, ref, path)
    """
    p = urlparse(url)
    parts = [x for x in p.path.strip("/").split("/") if x]
    if len(parts) < 5 or parts[2] not in ("tree", "blob"):
        raise ValueError("URL GitHub de dossier invalide (attendu .../tree/<ref>/<path>).")
    owner, repo, kind, ref = parts[:4]
    path = "/".join(parts[4:]) if len(parts) > 4 else ""
    return owner, repo, ref, path

def github_get(url, token=None, params=None, max_retries=3):
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for attempt in range(max_retries):
        r = requests.get(url, headers=headers, params=params, timeout=30)
        # Gestion simple de rate-limit: si 403 et header X-RateLimit-Reset, on attend.
        if r.status_code == 403 and "X-RateLimit-Remaining" in r.headers and r.headers.get("X-RateLimit-Remaining") == "0":
            reset = int(r.headers.get("X-RateLimit-Reset", "0"))
            wait_s = max(0, reset - int(time.time()) + 1)
            print(f"Rate-limit atteint, attente {wait_s}s...", file=sys.stderr)
            time.sleep(wait_s)
            continue
        if r.ok:
            return r
        # petit backoff pour erreurs transitoires
        if r.status_code >= 500:
            time.sleep(1.0 + attempt)
            continue
        r.raise_for_status()
    r.raise_for_status()

def download_file(url, dest_path, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with requests.get(url, headers=headers, stream=True, timeout=60) as r:
        r.raise_for_status()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)

def list_directory(owner, repo, path, ref="main", token=None):
    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{path}"
    r = github_get(url, token=token, params={"ref": ref})
    data = r.json()
    # L’API retourne un objet si c’est un fichier, une liste si c’est un dossier
    if isinstance(data, dict) and data.get("type") == "file":
        return [data]
    if not isinstance(data, list):
            # Erreurs (submodule, symlink non supporté, etc.)
        raise RuntimeError(f"Réponse inattendue pour {path}: {json.dumps(data, ensure_ascii=False)[:200]}")
    return data

def download_github_dir(owner, repo, path, dest_dir, ref="main", token=None):
    """
    Télécharge récursivement tout 'path' de <owner>/<repo> à la révision 'ref' dans dest_dir.
    """
    queue = [(path.strip("/"),)]
    base = pathlib.Path(dest_dir)

    while queue:
        current = queue.pop()
        dir_path = current[0]
        entries = list_directory(owner, repo, dir_path, ref=ref, token=token)
        for item in entries:
            item_type = item.get("type")
            item_path = item.get("path")  # chemin relatif dans le repo
            if item_type == "dir":
                queue.append((item_path,))
            elif item_type == "file":
                download_url = item.get("download_url")
                if not download_url:
                    # Certains fichiers binaires ou lfs peuvent ne pas avoir de download_url
                    # fallback via API "git/blobs" si besoin (non implémenté ici).
                    print(f"⚠️ Pas de download_url pour {item_path}, ignoré.", file=sys.stderr)
                    continue
                dest_path = base / item_path
                print(f"Téléchargement: {item_path}")
                download_file(download_url, dest_path, token=token)
            else:
                # symlink, submodule, etc. -> on ignore proprement
                print(f"⏭️ Type non géré ({item_type}) pour {item_path}, ignoré.", file=sys.stderr)

def main():
    import argparse, os
    parser = argparse.ArgumentParser(description="Télécharger un dossier d’un dépôt GitHub (via API).")
    parser.add_argument("url", help="URL GitHub du dossier (…/tree/<ref>/<path>)")
    parser.add_argument("-o", "--output", default="download", help="Dossier de sortie")
    parser.add_argument("--token", default=os.getenv("GITHUB_TOKEN"), help="Jeton GitHub (optionnel)")
    args = parser.parse_args()

    owner, repo, ref, subpath = parse_github_folder_url(args.url)
    if not subpath:
        print("Le chemin de dossier à l’intérieur du dépôt est vide.", file=sys.stderr)
        sys.exit(1)

    print(f"Dépôt : {owner}/{repo}\nBranche/révision : {ref}\nChemin : {subpath}\nSortie : {args.output}")
    download_github_dir(owner, repo, subpath, args.output, ref=ref, token=args.token)
    print("✅ Terminé.")

if __name__ == "__main__":
    main()

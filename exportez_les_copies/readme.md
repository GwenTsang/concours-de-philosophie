## étapes pour exporter toutes les copies

```python
!wget https://raw.githubusercontent.com/GwenTsang/concours-de-philosophie/refs/heads/main/exportez_les_copies/download.py
```

```python
!python download.py \
  "https://github.com/GwenTsang/concours-de-philosophie/tree/main/copies_JSON" \
  -o copies_local
```

```python
pip install python-docx odf
```

```python
!python /content/copies_local/copies_JSON/export.py
```
Par défaut toutes les copies sont exportées en DOCX. Vous pouvez obtenir **DOCX + MD** en faisant :

```python
python /content/copies_local/copies_JSON/export.py --md
```

ou **format ODT** (LibreOffice) :
```
python /content/copies_local/copies_JSON/export.py --odt
```

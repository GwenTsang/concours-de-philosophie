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


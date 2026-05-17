from pdf2docx import Converter
import docx
import os

pdf_file = '/content/Explication de texte - 17 -Nietzsche - Agregation interne 2020.pdf'
docx_file = 'temp_nietzsche.docx'
md_file = 'Nietzsche_Final_Underlined.md'

# 1. Convertir PDF en DOCX (format intermédiaire conservant les styles)
print("Conversion du PDF en DOCX...")
cv = Converter(pdf_file)
cv.convert(docx_file, start=0, end=None)
cv.close()

# 2. Lire le DOCX et convertir en Markdown avec balises <u>
print("Extraction du texte stylisé du DOCX...")
doc = docx.Document(docx_file)
md_content = []

for para in doc.paragraphs:
    para_text = ""
    for run in para.runs:
        text = run.text
        # Vérifier si le segment de texte est souligné
        if run.underline and text.strip():
            para_text += f"<u>{text}</u>"
        else:
            para_text += text
    md_content.append(para_text)

# Sauvegarder le résultat
with open(md_file, 'w', encoding='utf-8') as f:
    f.write('\n\n'.join(md_content))

print(f"Le fichier Markdown avec les soulignements préservés est disponible ici : {md_file}")
import os
import json
import pytesseract
import pdfplumber
from PIL import Image

percorso_tesseract = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = percorso_tesseract

cartella_input = "repository"

def estrai_testo_da_txt(percorso_txt):
    with open(percorso_txt, "r", encoding="utf-8") as f:
        return f.read()

def estrai_testo_da_pdf(percorso_pdf):
    testo_completo = ""
    with pdfplumber.open(percorso_pdf) as pdf:
        for pagina in pdf.pages:
            testo_completo += pagina.extract_text() + "\n"
    return testo_completo

def estrai_testo_da_immagine(percorso_immagine):
    immagine = Image.open(percorso_immagine)
    testo_estratto = pytesseract.image_to_string(immagine)
    return testo_estratto

def processa_file(percorso_file):
    estensione = os.path.splitext(percorso_file)[1].lower()
    if estensione == ".pdf":
        return estrai_testo_da_pdf(percorso_file)
    elif estensione in [".jpg", ".jpeg", ".png"]:
        return estrai_testo_da_immagine(percorso_file)
    elif estensione == ".txt":
        return estrai_testo_da_txt(percorso_file)
    else:
        print(f"Formato non supportato: {percorso_file}")
        return ""
    
def main():
    if not os.path.exists(cartella_input):
        print(f"Errore: La cartella '{cartella_input}' non esiste.")
        return

    database_documenti = []

    for root, dirs, files in os.walk(cartella_input):
        for file in files:
            percorso_file = os.path.join(root, file)
            testo_estratto = processa_file(percorso_file)

            if testo_estratto.strip():
                scheda_documento = {
                    "nome_file": file,
                    "percorso": percorso_file,
                    "testo": testo_estratto.strip(),
                    "metadati": {
                        "dimensione": os.path.getsize(percorso_file),
                        "data_creazione": os.path.getctime(percorso_file),
                        "data_modifica": os.path.getmtime(percorso_file)
                    }
                }
                database_documenti.append(scheda_documento)

    nome_file_archivio = "archivio_documenti.json"
    with open(nome_file_archivio, "w", encoding="utf-8") as f:
        json.dump(database_documenti, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()

print("Elaborazione completata.")

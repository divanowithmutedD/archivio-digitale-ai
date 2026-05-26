import pytesseract
from PIL import Image

percorso_tesseract = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = percorso_tesseract

percorso_immagine = "giornale.jpg"

try:
    immagine = Image.open(percorso_immagine)
    testo_estratto = pytesseract.image_to_string(immagine)
    print("Testo estratto dall'immagine:")
    print(testo_estratto)
except Exception as e:
    print(f"Si è verificato un errore: {e}")

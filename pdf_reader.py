import pdfplumber
percorso_pdf = "kr_neural.pdf"
with pdfplumber.open(percorso_pdf) as pdf:
    testo_completo = ""
    for pagina in pdf.pages:
        testo_completo += pagina.extract_text() + "\n" 
    print(testo_completo)
    
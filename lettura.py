nome_documento = "documento.txt"
with open(nome_documento, "r", encoding="utf-8", errors="ignore") as file:
    contenuto = file.read()
    print(contenuto)    

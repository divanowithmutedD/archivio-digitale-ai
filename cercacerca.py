import json
import os

nome_file_archivio = "archivio_documenti.json"

if os.path.exists(nome_file_archivio):
    with open(nome_file_archivio, "r", encoding="utf-8") as f:
        archivio = json.load(f)

    print(f"Caricato archivio esistente con {len(archivio)} documenti.")
    parola_chiave = input("Inserisci una parola chiave per la ricerca: ").strip().lower()
 
    risultati_trovati = 0

    for doc in archivio:
        if parola_chiave in doc["testo"].lower():
            risultati_trovati += 1
            print(f"Nome file: {doc['nome_file']}")
            print(f"Percorso: {doc['percorso']}")

            posizione_parola = doc["testo"].lower().find(parola_chiave)
            inizio = max(0, posizione_parola - 50)
            fine = posizione_parola + len(parola_chiave) + 50
            estratto_contesto = doc["testo"][inizio:fine].replace("\n", " ")

            print(f"Contesto trovato: ...{estratto_contesto}...")
            print("-" * 40) 

    risultati_ricerca = [doc for doc in archivio if parola_chiave in doc["testo"].lower()]
    if risultati_ricerca:
        print(f"Documenti trovati contenenti '{parola_chiave}':")
        for doc in risultati_ricerca:
            print(f"- {doc['nome_file']} (percorso: {doc['percorso']})")
    else:
        print(f"Nessun documento trovato contenente '{parola_chiave}'.")

    for doc in archivio:
        if parola_chiave in doc["testo"].lower():
            print(f"Nome file: {doc['nome_file']}")
            print(f"Percorso: {doc['percorso']}")
            print(f"Testo estratto: {doc['testo'][:200]}...")
            print("-" * 40)

    if risultati_ricerca:
        posizione = input("Vuoi visualizzare il testo completo di un documento? (s/n): ").strip().lower()
        doc_selezionato = risultati_ricerca[0]
        inizio = 0
        fine = 5
        estratto_contesto = doc_selezionato["testo"][max(0, doc_selezionato["testo"].lower().find(parola_chiave) - 50):doc_selezionato["testo"].lower().find(parola_chiave) + len(parola_chiave) + 50]

        print(f"Contesto trovato: ...{estratto_contesto}...")
        print("-" * 40)

    if risultati_trovati == 0:
        print(f"Nessun documento trovato contenente '{parola_chiave}'.")
    else:
        print(f"Totale documenti trovati contenenti '{parola_chiave}': {risultati_trovati}")
        
else:
    print("Errore: L'archivio non esiste. Avvia prima provaprova.py")
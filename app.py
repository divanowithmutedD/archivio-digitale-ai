import streamlit as st
import pdfplumber
import pytesseract
from PIL import Image
import os
import re
import json
import pandas as pd
from openai import OpenAI

try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except Exception:
    st.error("Configurazione mancante: impossibile trovare la chiave OPENAI_API_KEY nel file dei segreti.")
    OPENAI_API_KEY = None

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

if "cronologia" not in st.session_state:
    st.session_state.cronologia = []
if "parola_attiva" not in st.session_state:
    st.session_state.parola_attiva = ""

if "current_file" not in st.session_state:
    st.session_state.current_file = ""
if "categoria_edit" not in st.session_state:
    st.session_state.categoria_edit = ""
if "keywords_edit" not in st.session_state:
    st.session_state.keywords_edit = ""
if "riassunto_edit" not in st.session_state:
    st.session_state.riassunto_edit = ""
if "dati_convalidati" not in st.session_state:
    st.session_state.dati_convalidati = False

if "registro_documenti" not in st.session_state:
    st.session_state.registro_documenti = {}

def analizza_con_openai(testo, api_key):
    if not api_key:
        return "Errore configurazione", "Chiave API non configurata nel sistema.", ""
    try:
        client = OpenAI(api_key=api_key)
        
        prompt_sistema = (
            "You are an expert in document analysis and metadata extraction. "
            "All answers must be in Italian. "
            "Analyze the provided text and extract the following information:\n"
            "You must return a JSON object with the following fields:\n"
            "1. 'categoria': the category of the document based on its content. Choose from: 'Legale', 'Finanziario', 'Tecnico', 'Medico', 'Commerciale', 'Generico'.\n"
            "2. 'riassunto': a concise summary of the document in Italian, no more than 3 sentences.\n"
            "3. 'keywords': a string of relevant keywords extracted from the document, separated by commas.\n"
            "Do not include any additional text or explanations, only the JSON object with the specified fields."
        )
        
        risposta = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"Testo del documento:\n\n{testo}"}
            ]
        )
        
        try:
            metadati = json.loads(risposta.choices[0].message.content)
            return metadati.get("categoria", "Generico"), metadati.get("riassunto", ""), metadati.get("keywords", "")
        except json.JSONDecodeError:
            return "Errore formato", "La risposta generata non rispetta il formato strutturato richiesto.", ""
            
    except Exception as e:
        st.error(f"Errore durante l'interazione con i servizi di analisi: {str(e)}")
        return "Errore connessione", "Impossibile completare l'operazione a causa di un'anomalia di rete o di credenziali.", ""

def estrai_testo_da_pdf(percorso_pdf):
    testo_completo = ""
    try:
        with pdfplumber.open(percorso_pdf) as pdf:
            if not pdf.pages:
                st.warning("Il documento PDF caricato sembra non contenere pagine valide.")
                return ""
            for pagina in pdf.pages:
                testo_pag = pagina.extract_text()
                if testo_pag:
                    testo_completo += testo_pag + "\n"
        return testo_completo
    except Exception as e:
        st.error(f"Impossibile leggere il file PDF. Dettaglio tecnico: {str(e)}")
        return ""

def estrai_testo_da_immagine(percorso_immagine):
    try:
        immagine = Image.open(percorso_immagine)
        return pytesseract.image_to_string(immagine, lang="ita")
    except FileNotFoundError:
        st.error("Errore di sistema: Il motore OCR Tesseract non e installato nel percorso specificato.")
        return ""
    except Exception as e:
        st.error(f"Impossibile elaborare l'immagine caricata. Dettaglio tecnico: {str(e)}")
        return ""

st.set_page_config(layout="wide")

st.title("Archivio Digitale AI - Artificial Ivano")

file_caricato = None

with st.sidebar:
    st.header("Pannello di Controllo")
    
    file_caricati = st.file_uploader("Carica uno o più documenti", type=["pdf", "jpg", "jpeg", "png", "txt"], accept_multiple_files=True)
    
    if file_caricati:
        st.markdown("---")
        st.subheader("Documenti in Archivio")
        nomi_file = [f.name for f in file_caricati]
        file_selezionato = st.selectbox("Seleziona il documento da analizzare", nomi_file)
        file_caricato = next(f for f in file_caricati if f.name == file_selezionato)
        
    st.markdown("---")
    parola_cercata = st.text_input("Cerca una parola chiave", value=st.session_state.parola_attiva).strip().lower()

    if parola_cercata and parola_cercata != st.session_state.parola_attiva:
        st.session_state.parola_attiva = parola_cercata
        if parola_cercata not in st.session_state.cronologia:
            st.session_state.cronologia.insert(0, parola_cercata)

    if st.session_state.cronologia:
        st.markdown("**Ricerche Rapide (Cronologia):**")
        for p in st.session_state.cronologia[:5]:
            if st.button(p, key=f"btn_{p}", use_container_width=True):
                st.session_state.parola_attiva = p
                st.rerun()

if file_caricato is not None:
    estensione = os.path.splitext(file_caricato.name)[1].lower()
    testo_estratto = ""

    with st.spinner("Estraendo testo..."):
        if estensione == ".pdf":
            testo_estratto = estrai_testo_da_pdf(file_caricato)
        elif estensione in [".jpg", ".jpeg", ".png"]:
            testo_estratto = estrai_testo_da_immagine(file_caricato)
        elif estensione == ".txt":
            try:
                testo_estratto = file_caricato.read().decode("utf-8")
            except Exception as e:
                st.error(f"Errore di decodifica del file di testo: {str(e)}")

        if testo_estratto and testo_estratto.strip():
            
            if st.session_state.current_file != file_caricato.name:
                categoria_real, riassunto_real, keywords_real = analizza_con_openai(testo_estratto, OPENAI_API_KEY)
                st.session_state.categoria_edit = categoria_real
                st.session_state.keywords_edit = keywords_real
                st.session_state.riassunto_edit = riassunto_real
                st.session_state.current_file = file_caricato.name
                
                if file_caricato.name in st.session_state.registro_documenti:
                    salvati = st.session_state.registro_documenti[file_caricato.name]
                    st.session_state.categoria_edit = salvati["Categoria"]
                    st.session_state.keywords_edit = salvati["Parole Chiave"]
                    st.session_state.riassunto_edit = salvati["Riassunto"]
                    st.session_state.dati_convalidati = True
                else:
                    st.session_state.dati_convalidati = False
            
            st.subheader("Controllo e Validazione Metadati Documento")
            st.caption("Stato del sistema: Analisi protetta attiva tramite credenziali st.secrets")
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.session_state.categoria_edit = st.text_input("Categoria Documento (Modificabile)", value=st.session_state.categoria_edit)
            with col_b:
                st.session_state.keywords_edit = st.text_input("Parole chiave rilevate (Modificabile)", value=st.session_state.keywords_edit)
                
            st.session_state.riassunto_edit = st.text_area("Riassunto del Documento (Modificabile)", value=st.session_state.riassunto_edit, height=100)
            
            if st.button("Conferma e convalida inserimento dati", use_container_width=True):
                st.session_state.dati_convalidati = True
                st.session_state.registro_documenti[file_caricato.name] = {
                    "Nome File": file_caricato.name,
                    "Categoria": st.session_state.categoria_edit,
                    "Parole Chiave": st.session_state.keywords_edit,
                    "Riassunto": st.session_state.riassunto_edit
                }
                
            if st.session_state.dati_convalidati:
                st.markdown("<p style='color: #4CAF50; font-weight: bold;'>Dati verificati, convalidati e salvati temporaneamente nel registro di sessione.</p>", unsafe_allow_html=True)
                
            st.markdown("---")

            testo_html_formattato = testo_estratto.replace("\n", "<br>")
            posizioni = []

            if parola_cercata and parola_cercata in testo_estratto.lower():
                pos = testo_estratto.lower().find(parola_cercata)
                while pos != -1:
                    posizioni.append(pos)
                    pos = testo_estratto.lower().find(parola_cercata, pos + 1)

                testo_html = ""
                ultimo_indice = 0
                for i, pos in enumerate(posizioni):
                    idx = i + 1
                    testo_html += testo_estratto[ultimo_indice:pos]
                    lunghezza = len(parola_cercata)
                    parola_originale = testo_estratto[pos:pos+lunghezza]
                    testo_html += f'<span id="punto_{idx}" style="background-color: #ffeb3b; color: black; font-weight: bold; padding: 2px; border-radius: 3px;">{parola_originale}</span>'
                    ultimo_indice = pos + lunghezza
                testo_html += testo_estratto[ultimo_indice:]
                testo_html_formattato = testo_html.replace("\n", "<br>")

            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader("Visualizzatore Documento")
                css_personalizzato = """
                <style>
                span:target {
                    background-color: #ff3838 !important;
                    color: white !important;
                    font-weight: bold !important;
                    box-shadow: 0 0 10px #ff3838;
                }
                </style>
                """
                st.markdown(f"{css_personalizzato}<div style='background-color: #1a1a1a; color: #ffffff; padding: 20px; border-radius: 8px; font-family: monospace; line-height: 1.6; max-height: 600px; overflow-y: auto;'>{testo_html_formattato}</div>", unsafe_allow_html=True)

            with col2:
                st.subheader("Risultati di Ricerca")
                con_box = st.container(height=530)
                if parola_cercata:
                    if posizioni:
                        con_box.write(f"Trovate **{len(posizioni)}** corrispondenze:")
                        for i, pos in enumerate(posizioni):
                            idx = i + 1
                            
                            inizio_frase = 0
                            for m in re.finditer(r'[.!?](\s+|\n|$)', testo_estratto[:pos]):
                                inizio_frase = m.end()
                            
                            fine_frase = len(testo_estratto)
                            m_forward = re.search(r'[.!?](\s+|\n|$)', testo_estratto[pos:])
                            if m_forward:
                                fine_frase = pos + m_forward.end()
                                
                            frase_completa = testo_estratto[inizio_frase:fine_frase].strip().replace("\n", " ")
                            
                            if len(frase_completa) < 10:
                                frase_completa = testo_estratto[max(0, pos - 40):min(len(testo_estratto), pos + len(parola_cercata) + 60)].strip().replace("\n", " ")
                            
                            con_box.markdown(f"**{idx}.** <a href='#punto_{idx}' style='color: #3a86ff; font-weight: bold; text-decoration: none;'>[Salta al punto]</a>", unsafe_allow_html=True)
                            con_box.write(f"... {frase_completa} ...")
                            
                            with con_box.popover("Copia frase", use_container_width=True):
                                st.code(frase_completa, language=None)
                                
                            con_box.markdown("---")
                    else:
                        con_box.warning(f"Nessun riscontro per '{parola_cercata}'.")
                else:
                    con_box.info("Digita una parola nel pannello a sinistra per veder comparire qui i dettagli dei contesti.")

        else:
            st.warning("Il documento caricato non contiene testo estraibile o leggibile.")

if st.session_state.registro_documenti:
    st.markdown("---")
    st.subheader("Registro globale dei documenti convalidati")
    
    df_registro = pd.DataFrame(list(st.session_state.registro_documenti.values()))
    st.dataframe(df_registro, use_container_width=True, hide_index=True)
    
    csv_data = df_registro.to_csv(index=False, sep=";").encode("utf-8")
    
    st.download_button(
        label="Esporta registro convalidati in Excel (CSV)",
        data=csv_data,
        file_name="registro_metadati_tirocinio.csv",
        mime="text/csv",
        use_container_width=True
    )
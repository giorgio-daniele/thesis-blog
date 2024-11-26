import streamlit

# Impostazioni della pagina
streamlit.set_page_config(page_title="Benvenuto - Ricerca QoE", layout="centered")

# Titolo della pagina
streamlit.title("Progettazione ed ingegnerizzazione di un sistema per l'analisi passiva della QoE da tracce Tstat")

# Descrizione della ricerca
streamlit.write("""
Questa ricerca si concentra sulla progettazione e ingegnerizzazione di un sistema per l'analisi passiva della Quality of Experience (QoE) 
utilizzando le tracce fornite da Tstat. L'obiettivo principale è sviluppare strumenti e metodologie per migliorare la comprensione 
dell'esperienza utente durante la fruizione di contenuti multimediali.
""")

# Sezione dei link
streamlit.markdown("<h3>Software Utilizzati</h3>", unsafe_allow_html=True)

# Link al software
streamlit.write("""
- [Streambot](https://github.com/giorgio-daniele/streambot): Il software per automatizzare gli esperimenti.
- [Tstat Scripting](https://github.com/giorgio-daniele/tstat-scripting): Il software per processare i dati ottenuti da Tstat.
- [Tstat](http://tstat.polito.it/): La piattaforma di analisi di rete.
""")

# Footer
streamlit.markdown("<footer style='text-align: center; color: #7f8c8d;'>© 2024 Ricerca QoE</footer>", unsafe_allow_html=True)

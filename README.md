#  Advanced Financial Anomaly Detector

Un'applicazione web interattiva sviluppata in **Python** e **Streamlit** per l'analisi quantitativa e il rilevamento di anomalie/shock nei mercati finanziari. Il sistema scarica i dati in tempo reale da Yahoo Finance e mette a confronto due approcci statistici su base mobile (rolling): lo **Z-Score Classico** e l'**Interquartile Range (IQR) Robusto**.

---

##  Funzionalità
* **Download Dati Real-Time:** Integrazione con l'API di `yfinance` per analizzare azioni, indici o criptovalute.
* **Analisi Logaritmica:** Calcolo automatico dei rendimenti logaritmici per garantire l'additività temporale e la simmetria dei dati.
* **Algoritmi di Rilevamento:**
  * **Z-Score Mobile:** Approccio classico basato su media e deviazione standard mobili.
  * **IQR Mobile (Tukey):** Approccio robusto basato su mediana e quartili, immune all'effetto mascheramento degli outlier consecutivi.
* **Interfaccia Interattiva:** Grafici a due pannelli generati con `Plotly` dotati di bande dinamiche di tolleranza (shading) e controllo dei parametri tramite sidebar.

---

##  Architettura dei File
Il repository è strutturato come segue:
* `app.py`: Codice principale dell'applicazione Streamlit.
* `requirements.txt`: Elenco delle dipendenze necessarie per il funzionamento.
* `.gitignore`: File per escludere file temporanei e di cache dal tracciamento di Git.
* `README.md`: Documentazione del progetto.

---

##  Installazione e Uso Locale

1. **Clona il repository:**
   ```bash
   git clone [https://github.com/IL_TUO_USERNAME/financial-anomaly-detector.git](https://github.com/IL_TUO_USERNAME/financial-anomaly-detector.git)
   cd financial-anomaly-detector

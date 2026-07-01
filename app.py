import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import datetime as dt
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURAZIONE DELLA PAGINA WEB ---
st.set_page_config(
    page_title="Fintech Anomaly Detector",
    page_icon="📈",
    layout="wide"
)

# --- FUNZIONI CORE DELLA PIPELINE ---

@st.cache_data(show_spinner="Scaricamento dati di mercato in corso...")
def download_financial_data(ticker: str, start_date: dt.date, end_date: dt.date) -> pd.DataFrame:
    # Convertiamo le date in stringa per yfinance
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    data = yf.download(ticker, start=start_str, end=end_str, progress=False)
    if data.empty:
        return pd.DataFrame()
        
    if isinstance(data.columns, pd.MultiIndex):
        if 'Adj Close' in data.columns.get_level_values(0):
            prices = data['Adj Close'].iloc[:, 0]
        elif 'Close' in data.columns.get_level_values(0):
            prices = data['Close'].iloc[:, 0]
        else:
            prices = data.iloc[:, 0]
    else:
        if 'Adj Close' in data.columns:
            prices = data['Adj Close']
        elif 'Close' in data.columns:
            prices = data['Close']
        else:
            prices = data.iloc[:, 0]

    df = pd.DataFrame(prices)
    df.columns = ['Price']
    df['Log_Returns'] = np.log(df['Price'] / df['Price'].shift(1))
    return df.dropna()

def calculate_zscore_anomalies(df: pd.DataFrame, window: int, threshold: float) -> pd.DataFrame:
    df = df.copy()
    df['Rolling_Mean'] = df['Log_Returns'].rolling(window=window).mean()
    df['Rolling_Std'] = df['Log_Returns'].rolling(window=window).std()
    df['Z_Score'] = (df['Log_Returns'] - df['Rolling_Mean']) / (df['Rolling_Std'] + 1e-9)
    df['Is_Anomaly_Z'] = np.abs(df['Z_Score']) > threshold
    return df

def calculate_iqr_anomalies(df: pd.DataFrame, window: int, threshold: float) -> pd.DataFrame:
    df = df.copy()
    df['Q1'] = df['Log_Returns'].rolling(window=window).quantile(0.25)
    df['Q3'] = df['Log_Returns'].rolling(window=window).quantile(0.75)
    df['IQR'] = df['Q3'] - df['Q1']
    df['Median'] = df['Log_Returns'].rolling(window=window).median()
    df['Lower_Bound'] = df['Median'] - (threshold * df['IQR'])
    df['Upper_Bound'] = df['Median'] + (threshold * df['IQR'])
    df['Is_Anomaly_IQR'] = (df['Log_Returns'] < df['Lower_Bound']) | (df['Log_Returns'] > df['Upper_Bound'])
    return df

def generate_plotly_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.08,
        subplot_titles=(f"Prezzo di Chiusura e Anomalie Rilevate", "Rendimenti Logaritmici e Bande di Tolleranza IQR")
    )
    
    # Prezzo e anomalie
    fig.add_trace(go.Scatter(x=df.index, y=df['Price'], name='Prezzo', line=dict(color='#1f77b4', width=2)), row=1, col=1)
    
    anomalies_iqr = df[df['Is_Anomaly_IQR']]
    fig.add_trace(go.Scatter(x=anomalies_iqr.index, y=anomalies_iqr['Price'], mode='markers', name='Anomalia IQR (Robusta)', marker=dict(color='#d9534f', size=8)), row=1, col=1)
    
    anomalies_z = df[df['Is_Anomaly_Z']]
    fig.add_trace(go.Scatter(x=anomalies_z.index, y=anomalies_z['Price'], mode='markers', name='Anomalia Z-Score (Classica)', marker=dict(color='#f0ad4e', size=6, symbol='x')), row=1, col=1)
    
    # Rendimenti e bande
    fig.add_trace(go.Scatter(x=df.index, y=df['Log_Returns'], name='Rendimento Log', line=dict(color='#7f7f7f', width=1), opacity=0.4), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Upper_Bound'], name='Limite Sup. IQR', line=dict(color='#2ca02c', width=1.5, dash='dash')), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Lower_Bound'], name='Limite Inf. IQR', line=dict(color='#2ca02c', width=1.5, dash='dash')), row=2, col=1)
    
    fig.update_layout(height=700, template='plotly_white', hovermode='x unified', margin=dict(l=20, r=20, t=30, b=20))
    fig.update_yaxes(title_text="Prezzo ($)", row=1, col=1)
    fig.update_yaxes(title_text="Rendimento", row=2, col=1)
    return fig

# --- INTERFACCIA UTENTE (STREAMLIT) ---

st.title("📈 Advanced Financial Anomaly Detector")
st.markdown("Questa applicazione confronta lo **Z-Score mobile (Classico)** con l'**Interquartile Range mobile (IQR Robusto)** per individuare shock e anomalie nei rendimenti storici.")

# Sidebar per i controlli di input
st.sidebar.header("🔧 Configurazione Parametri")

ticker = st.sidebar.text_input("Ticker Asset (Yahoo Finance)", value="BTC-USD").upper()

col_date1, col_date2 = st.sidebar.columns(2)
with col_date1:
    start_date = st.date_input("Data Inizio", value=dt.date(2024, 1, 1))
with col_date2:
    end_date = st.date_input("Data Fine", value=dt.date.today())

st.sidebar.markdown("---")
st.sidebar.subheader("🧮 Parametri Algoritmi")
window = st.sidebar.slider("Finestra Mobile (Giorni)", min_value=10, max_value=90, value=30, step=5)
z_threshold = st.sidebar.slider("Soglia Z-Score (k)", min_value=1.5, max_value=5.0, value=3.0, step=0.1)
iqr_threshold = st.sidebar.slider("Soglia IQR (k)", min_value=1.5, max_value=5.0, value=2.5, step=0.1)

# Esecuzione della Pipeline
if start_date >= end_date:
    st.error("Errore: La data di inizio deve essere precedente alla data di fine.")
else:
    df_raw = download_financial_data(ticker, start_date, end_date)
    
    if df_raw.empty:
        st.error(f"Nessun dato trovato per il ticker '{ticker}'. Controlla il simbolo su Yahoo Finance.")
    elif len(df_raw) < window:
        st.warning(f"Dati insufficienti ({len(df_raw)} giorni) per la finestra mobile selezionata ({window} giorni).")
    else:
        # Calcolo anomalie
        df_processed = calculate_zscore_anomalies(df_raw, window, z_threshold)
        df_processed = calculate_iqr_anomalies(df_processed, window, iqr_threshold)
        
        # --- KPI PRINCIPALI (METRICHE) ---
        total_days = len(df_processed)
        anomalies_z = df_processed['Is_Anomaly_Z'].sum()
        anomalies_iqr = df_processed['Is_Anomaly_IQR'].sum()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Giorni Analizzati", total_days)
        with col2:
            st.metric("Anomalie Z-Score", f"{anomalies_z}", f"{anomalies_z/total_days:.2%} del totale", delta_color="inverse")
        with col3:
            st.metric("Anomalie IQR Robust", f"{anomalies_iqr}", f"{anomalies_iqr/total_days:.2%} del totale", delta_color="inverse")
            
        # --- GRAFICO INTERATTIVO ---
        st.markdown("### Visualizzazione Interattiva")
        fig = generate_plotly_chart(df_processed, ticker)
        st.plotly_chart(fig, use_container_width=True)
        
        # --- TABELLA DETTAGLI ---
        st.markdown("### Ultimi Giorni di Mercato Analizzati")
        st.dataframe(df_processed[['Price', 'Log_Returns', 'Z_Score', 'Is_Anomaly_Z', 'Is_Anomaly_IQR']].tail(10), use_container_width=True)
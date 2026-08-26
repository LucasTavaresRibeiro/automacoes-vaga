import streamlit as st
import sqlite3
import pandas as pd
import subprocess
import os

st.set_page_config(page_title="Job Hunter AI", layout="wide")

st.title("🎯 Job Hunter AI - Dashboard de Vagas")

# Sidebar
st.sidebar.header("Painel de Controle")

if st.sidebar.button("Rodar Robô de Coleta"):
    st.sidebar.info("Iniciando coleta... Olhe o terminal!")
    # Rodar o CPTMR.py num subprocesso
    subprocess.Popen(["python", "CPTMR.py"], env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    st.sidebar.success("Robô disparado em background!")

def load_data():
    try:
        conn = sqlite3.connect("banco_vagas.db")
        df = pd.read_sql_query("SELECT * FROM vagas", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar banco: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("Nenhuma vaga encontrada ainda. Rode o robô!")
else:
    st.metric("Total de Vagas Encontradas", len(df))
    
    # Filtros
    st.subheader("Filtros")
    col1, col2 = st.columns(2)
    with col1:
        termo = st.text_input("Buscar no título da vaga")
    with col2:
        status = st.multiselect("Status da Vaga", df["Status"].unique(), default=df["Status"].unique())

    df_filtrado = df[df["Status"].isin(status)]
    if termo:
        df_filtrado = df_filtrado[df_filtrado["Titulo"].str.contains(termo, case=False, na=False)]

    st.subheader("Lista de Vagas")
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🔗 Links de Candidatura Rápida")
    
    for idx, row in df_filtrado.head(20).iterrows():
        with st.expander(f"{row['Titulo']} - {row['Empresa']}"):
            st.write(f"**Localização:** {row['Localizacao']}")
            st.write(f"**Data Coleta:** {row['Data_Coleta']}")
            st.markdown(f"[Ir para a vaga]({row['ID_Vaga']})", unsafe_allow_html=True)

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
    subprocess.Popen(["python", "CPTMR.py"], env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    st.sidebar.success("Robô disparado em background!")

def load_data():
    try:
        conn = sqlite3.connect("banco_vagas.db")
        df = pd.read_sql_query("SELECT * FROM vagas", conn)
        conn.close()
        return df
    except Exception as e:
        return pd.DataFrame()

def marcar_como_candidatado(id_vaga):
    try:
        conn = sqlite3.connect("banco_vagas.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE vagas SET Status = 'Candidatado' WHERE ID_Vaga = ?", (id_vaga,))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Erro ao atualizar: {e}")

df = load_data()

if df.empty:
    st.warning("Nenhuma vaga encontrada ainda. Rode o robô!")
else:
    # Contadores
    total_vagas = len(df)
    total_aplicadas = len(df[df["Status"] == "Candidatado"])
    
    col_a, col_b = st.columns(2)
    col_a.metric("Total de Vagas na Fila", total_vagas - total_aplicadas)
    col_b.metric("✅ Vagas Candidatadas", total_aplicadas)
    
    # Abas
    tab1, tab2 = st.tabs(["📋 Fila de Vagas", "✅ Minhas Candidaturas"])

    with tab1:
        st.subheader("Vagas para Avaliar")
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            termo = st.text_input("Buscar vaga por título ou empresa")
        with col2:
            status = st.multiselect("Status", df["Status"].unique(), default=[s for s in df["Status"].unique() if s != "Candidatado"])

        df_fila = df[df["Status"].isin(status)]
        if termo:
            df_fila = df_fila[(df_fila["Titulo"].str.contains(termo, case=False, na=False)) | (df_fila["Empresa"].str.contains(termo, case=False, na=False))]

        # Remover Localização e ID da visão principal para limpar
        df_view = df_fila.drop(columns=["Localizacao", "Data_Coleta"])

        st.dataframe(df_view, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("🔗 Links de Candidatura Rápida")
        
        for idx, row in df_fila.head(20).iterrows():
            with st.expander(f"{row['Titulo']} - {row['Empresa']}"):
                st.write(f"**Score IA:** {row.get('Score_IA', 'Ainda não avaliada')}")
                st.write(f"**Justificativa:** {row.get('Analise_IA', '')}")
                st.markdown(f"[Ir para a vaga na Gupy]({row['ID_Vaga']})", unsafe_allow_html=True)
                
                if st.button("Marcar como Candidatado", key=row['ID_Vaga']):
                    marcar_como_candidatado(row['ID_Vaga'])
                    st.rerun()

    with tab2:
        st.subheader("Histórico de Aplicações")
        df_aplicadas = df[df["Status"] == "Candidatado"]
        
        if not df_aplicadas.empty:
            df_view_app = df_aplicadas.drop(columns=["Localizacao"])
            st.dataframe(df_view_app, use_container_width=True, hide_index=True)
        else:
            st.info("Você ainda não marcou nenhuma vaga como candidatada.")

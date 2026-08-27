import streamlit as st
import sqlite3
import pandas as pd
import subprocess
import os

st.set_page_config(page_title="Job Hunter AI", layout="wide", page_icon="🎯")

st.title("🎯 Job Hunter - Painel de Vagas")
st.markdown("Bem-vindo ao seu curador automático de vagas na Gupy.")

# Sidebar
st.sidebar.header("Painel de Controle")

if st.sidebar.button("Rodar Robô de Coleta", type="primary"):
    st.sidebar.info("Iniciando coleta... Olhe o terminal!")
    subprocess.Popen(["python", "CPTMR.py"], env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    st.sidebar.success("Robô disparado em background!")

def load_data():
    try:
        conn = sqlite3.connect("banco_vagas.db")
        df = pd.read_sql_query("SELECT Titulo, Empresa, ID_Vaga, Status, Data_Coleta FROM vagas", conn)
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
    
    tab1, tab2 = st.tabs(["📋 Fila de Vagas", "✅ Minhas Candidaturas"])

    with tab1:
        st.subheader("Vagas para Avaliar")
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            termo = st.text_input("Buscar vaga por título ou empresa")
        with col2:
            status = st.multiselect("Status", df["Status"].unique(), default=[s for s in df["Status"].unique() if s != "Candidatado"])

        df_fila = df[df["Status"].isin(status)].copy()
        if termo:
            df_fila = df_fila[(df_fila["Titulo"].str.contains(termo, case=False, na=False)) | (df_fila["Empresa"].str.contains(termo, case=False, na=False))]

        st.markdown("---")
        
        if not df_fila.empty:
            df_view = df_fila[["Titulo", "Empresa", "ID_Vaga", "Data_Coleta"]].copy()
            st.dataframe(
                df_view,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ID_Vaga": st.column_config.LinkColumn(
                        "Link da Vaga",
                        display_text="Acessar na Gupy"
                    ),
                    "Titulo": st.column_config.TextColumn("Vaga", width="large"),
                    "Empresa": st.column_config.TextColumn("Empresa", width="medium"),
                    "Data_Coleta": st.column_config.DatetimeColumn("Coletada em", format="DD/MM/YYYY HH:mm")
                }
            )
            
            st.subheader("Ações de Candidatura")
            # Dropdown to mark as applied
            vagas_opcoes = df_fila.apply(lambda row: f"{row['Titulo']} - {row['Empresa']} ({row['ID_Vaga']})", axis=1).tolist()
            selecionada = st.selectbox("Selecione a vaga para marcar como candidatada:", [""] + vagas_opcoes)
            if st.button("Marcar como Candidatado") and selecionada:
                link_selecionado = selecionada.split("(")[-1].strip(")")
                marcar_como_candidatado(link_selecionado)
                st.rerun()

    with tab2:
        st.subheader("Histórico de Aplicações")
        df_aplicadas = df[df["Status"] == "Candidatado"].copy()
        
        if not df_aplicadas.empty:
            df_view_app = df_aplicadas[["Titulo", "Empresa", "ID_Vaga", "Data_Coleta"]]
            st.dataframe(
                df_view_app,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ID_Vaga": st.column_config.LinkColumn(
                        "Link da Vaga",
                        display_text="Acessar na Gupy"
                    )
                }
            )
        else:
            st.info("Você ainda não marcou nenhuma vaga como candidatada.")

# Sidebar - Adicionar vaga avulsa
st.sidebar.markdown("---")
st.sidebar.subheader("➕ Adicionar Vaga Avulsa")
nova_vaga_url = st.sidebar.text_input("Cole o link da vaga (Gupy)")
if st.sidebar.button("Adicionar ao Banco", type="secondary"):
    if nova_vaga_url:
        try:
            conn = sqlite3.connect("banco_vagas.db")
            cursor = conn.cursor()
            
            dominio = "Desconhecida"
            if "gupy.io" in nova_vaga_url:
                d = nova_vaga_url.split("//")[-1].split(".")[0]
                if d != "portal":
                    dominio = d.capitalize()
                    
            cursor.execute('''
                INSERT INTO vagas (ID_Vaga, Titulo, Empresa, Localizacao, Descricao, Data_Coleta, Status)
                VALUES (?, ?, ?, ?, ?, datetime('now'), ?)
            ''', (nova_vaga_url, "Vaga Adicionada Manualmente", dominio, "Remoto", "Adicionada via Link", "Candidatado"))
            conn.commit()
            conn.close()
            st.sidebar.success("Vaga adicionada com sucesso!")
            st.rerun()
        except sqlite3.IntegrityError:
            st.sidebar.warning("Vaga já existe no banco.")
        except Exception as e:
            st.sidebar.error(f"Erro: {e}")

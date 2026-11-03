import streamlit as st
import sqlite3
import pandas as pd
import os
from CPTMR import orquestrar_sistema
from database.db_manager import JobDatabase

st.set_page_config(page_title="Job Hunter AI", layout="wide", page_icon="🎯")

st.title("🤖 Job Hunter - Painel de Vagas")
st.markdown("Bem-vindo ao seu curador automático de vagas PJ & Remotas.")

# Instalação automática do Playwright no Streamlit Cloud
@st.cache_resource
def install_playwright():
    os.system("playwright install chromium")
    
install_playwright()

# Sidebar
st.sidebar.header("Painel de Controle")

if st.sidebar.button("🚀 Rodar Robô de Coleta", type="primary", use_container_width=True):
    with st.sidebar.status("Executando varredura completa...", expanded=True) as status_box:
        log_placeholder = st.empty()
        def atualizar_progresso(msg: str):
            log_placeholder.markdown(f"**Status:** {msg}")
        resultado = orquestrar_sistema(callback_progresso=atualizar_progresso)
        status_box.update(
            label=f"✅ Concluído! +{resultado['novas']} novas | {resultado['encerradas']} encerradas",
            state="complete",
            expanded=False
        )
    st.rerun()

if st.sidebar.button("🔎 Verificar Vagas Encerradas", use_container_width=True):
    with st.sidebar.status("Checando links das vagas...", expanded=True) as status_box:
        db = JobDatabase()
        encerradas = db.auditar_vagas_encerradas()
        status_box.update(
            label=f"✔️ Auditoria pronta: {encerradas} encerrada(s) detectada(s)!",
            state="complete",
            expanded=False
        )
    st.rerun()

def load_data():
    try:
        db = JobDatabase()
        db.inicializar_banco()
        db.limpar_vagas_invalidas()
        conn = sqlite3.connect("banco_vagas.db")
        df = pd.read_sql_query("SELECT Titulo, Empresa, ID_Vaga, Status, Data_Coleta, Descricao FROM vagas", conn)
        conn.close()
        return df
    except Exception as e:
        return pd.DataFrame()

def atualizar_status_vaga(id_vaga: str, novo_status: str):
    try:
        conn = sqlite3.connect("banco_vagas.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE vagas SET Status = ? WHERE ID_Vaga = ?", (novo_status, id_vaga))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Erro ao atualizar: {e}")

df = load_data()

if df.empty:
    st.warning("Nenhuma vaga encontrada ainda. Clique em **'🚀 Rodar Robô de Coleta'** na barra lateral!")
else:
    # Normaliza status antigos 'Coletada' para exibição consistente
    status_ativos = ["Coletada", "Aberta", "Analisada"]
    total_ativas = len(df[df["Status"].isin(status_ativos)])
    total_aplicadas = len(df[df["Status"] == "Candidatado"])
    total_encerradas = len(df[df["Status"] == "Encerrada"])
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("🟢 Vagas Abertas na Fila", total_ativas)
    col_b.metric("✅ Vagas Candidatadas", total_aplicadas)
    col_c.metric("🚫 Vagas Encerradas", total_encerradas)
    
    tab1, tab2, tab3 = st.tabs(["📋 Fila de Vagas Abertas", "✅ Minhas Candidaturas", "🚫 Vagas Encerradas"])

    with tab1:
        st.subheader("Vagas Ativas para Avaliar")
        
        col1, col2 = st.columns(2)
        with col1:
            termo = st.text_input("Buscar vaga por título ou empresa")
        with col2:
            opcoes_status = [s for s in df["Status"].unique() if s not in ["Candidatado", "Encerrada"]]
            status = st.multiselect("Filtrar Status", df["Status"].unique(), default=opcoes_status)

        df_fila = df[df["Status"].isin(status)].copy()
        
        # Lógica de Ordenação: PJ no topo e mais recentes primeiro!
        is_pj = df_fila["Titulo"].str.contains(r'\bpj\b|pessoa jur[íi]dica', case=False, na=False) | df_fila["Descricao"].str.contains(r'\bpj\b|pessoa jur[íi]dica', case=False, na=False)
        df_fila["is_pj"] = is_pj
        df_fila = df_fila.sort_values(by=["Data_Coleta", "is_pj"], ascending=[False, False])
        
        if termo:
            df_fila = df_fila[(df_fila["Titulo"].str.contains(termo, case=False, na=False)) | (df_fila["Empresa"].str.contains(termo, case=False, na=False))]

        st.markdown("---")
        
        if not df_fila.empty:
            df_view = df_fila[["Titulo", "Empresa", "Status", "ID_Vaga", "Data_Coleta"]].copy()
            df_view.insert(0, "Candidatou?", False)
            df_view.insert(1, "Encerrada?", False)
            
            edited_df = st.data_editor(
                df_view,
                use_container_width=True,
                hide_index=True,
                disabled=["Titulo", "Empresa", "Status", "ID_Vaga", "Data_Coleta"],
                column_config={
                    "Candidatou?": st.column_config.CheckboxColumn(
                        "✅ Candidatou?",
                        help="Marque para enviar ao histórico de candidaturas",
                        default=False
                    ),
                    "Encerrada?": st.column_config.CheckboxColumn(
                        "🚫 Encerrada?",
                        help="Marque se a vaga já tiver encerrado as inscrições",
                        default=False
                    ),
                    "ID_Vaga": st.column_config.LinkColumn(
                        "Link da Vaga",
                        display_text="Acessar Vaga"
                    ),
                    "Titulo": st.column_config.TextColumn("Vaga", width="large"),
                    "Empresa": st.column_config.TextColumn("Empresa", width="medium"),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                    "Data_Coleta": st.column_config.DatetimeColumn("Coletada em", format="DD/MM/YYYY HH:mm")
                }
            )
            
            vagas_candidatadas = edited_df[edited_df["Candidatou?"] == True]
            vagas_encerradas = edited_df[edited_df["Encerrada?"] == True]
            
            mudou = False
            if not vagas_candidatadas.empty:
                for _, row in vagas_candidatadas.iterrows():
                    atualizar_status_vaga(row["ID_Vaga"], "Candidatado")
                mudou = True
            if not vagas_encerradas.empty:
                for _, row in vagas_encerradas.iterrows():
                    atualizar_status_vaga(row["ID_Vaga"], "Encerrada")
                mudou = True
            if mudou:
                st.rerun()
        else:
            st.info("Nenhuma vaga ativa corresponde aos filtros atuais.")

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
                        display_text="Acessar Vaga"
                    )
                }
            )
        else:
            st.info("Você ainda não marcou nenhuma vaga como candidatada.")

    with tab3:
        st.subheader("Vagas Encerradas / Expiradas")
        df_enc = df[df["Status"] == "Encerrada"].copy()
        if not df_enc.empty:
            st.dataframe(
                df_enc[["Titulo", "Empresa", "ID_Vaga", "Data_Coleta"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ID_Vaga": st.column_config.LinkColumn(
                        "Link da Vaga",
                        display_text="Acessar Vaga"
                    )
                }
            )
        else:
            st.info("Nenhuma vaga marcada como encerrada no momento.")

# Sidebar - Adicionar vaga avulsa
st.sidebar.markdown("---")
st.sidebar.subheader("➕ Vaga de Fora?")
nova_vaga_url = st.sidebar.text_input("Cole o link da vaga extra")
if st.sidebar.button("Salvar no Histórico", type="secondary", use_container_width=True):
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
            st.sidebar.success("Adicionada ao histórico!")
            st.rerun()
        except sqlite3.IntegrityError:
            st.sidebar.warning("Vaga já existe no banco.")
        except Exception as e:
            st.sidebar.error(f"Erro: {e}")

import streamlit as st
import sqlite3
import pandas as pd
import os
import json
import base64
import requests
from CPTMR import orquestrar_sistema
from database.db_manager import JobDatabase

st.set_page_config(page_title="Job Hunter AI", layout="wide", page_icon="🎯")

st.title("🤖 Job Hunter - Painel de Vagas")
st.markdown("Bem-vindo ao seu curador automático de vagas PJ & Remotas.")

@st.cache_resource
def ensure_playwright():
    os.system("playwright install chromium")
    return True

def identificar_portal(url: str) -> str:
    u = str(url).lower()
    if "gupy.io" in u:
        return "Gupy"
    if "vagaspj.com.br" in u or "adzuna.com.br" in u:
        return "VagasPJ"
    if "vagas.com.br" in u:
        return "Vagas.com"
    if "solides" in u:
        return "Sólides"
    if "infojobs.com.br" in u:
        return "InfoJobs"
    if "programathor.com.br" in u:
        return "ProgramaThor"
    if "linkedin.com" in u:
        return "LinkedIn"
    return "Outro"

def sincronizar_db_github() -> tuple[bool, str]:
    """
    Se GITHUB_TOKEN estiver configurado nos Secrets do Streamlit Cloud (ou no .env),
    faz o commit automático do banco_vagas.db direto no GitHub para nunca perder marcações!
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        try:
            token = st.secrets.get("GITHUB_TOKEN")
        except Exception:
            token = None
    if not token:
        return False, "GITHUB_TOKEN não configurado."

    repo = "LucasTavaresRibeiro/automacoes-vaga"
    path = "banco_vagas.db"
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    try:
        r_get = requests.get(url, headers=headers, timeout=15)
        sha = r_get.json().get("sha") if r_get.status_code == 200 else None
        with open(path, "rb") as f:
            content_b64 = base64.b64encode(f.read()).decode("utf-8")
        payload = {
            "message": "chore(ui): salva candidaturas e lixeira pelo painel Streamlit",
            "content": content_b64,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha
        r_put = requests.put(url, headers=headers, json=payload, timeout=20)
        if r_put.status_code in [200, 201]:
            return True, "Salvo no GitHub com sucesso!"
        return False, f"Erro GitHub ({r_put.status_code})"
    except Exception as e:
        return False, str(e)

def load_data():
    try:
        db = JobDatabase()
        db.inicializar_banco()
        db.limpar_vagas_invalidas()
        conn = sqlite3.connect("banco_vagas.db")
        df = pd.read_sql_query("SELECT Titulo, Empresa, ID_Vaga, Status, Data_Coleta, Descricao FROM vagas", conn)
        conn.close()
        if not df.empty:
            df["Portal"] = df["ID_Vaga"].apply(identificar_portal)
        return df
    except Exception:
        return pd.DataFrame()

def atualizar_status_vagas_lote(ids_vagas: list, novo_status: str):
    if not ids_vagas:
        return
    try:
        conn = sqlite3.connect("banco_vagas.db")
        cursor = conn.cursor()
        for id_vaga in ids_vagas:
            cursor.execute("UPDATE vagas SET Status = ? WHERE ID_Vaga = ?", (novo_status, id_vaga))
        conn.commit()
        conn.close()
        sincronizar_db_github()
    except Exception as e:
        st.error(f"Erro ao atualizar: {e}")

# Sidebar - Painel de Controle
st.sidebar.header("Painel de Controle")

if st.sidebar.button("🚀 Rodar Robô de Coleta", type="primary", use_container_width=True):
    with st.sidebar.status("Executando varredura completa (7 plataformas)...", expanded=True) as status_box:
        log_placeholder = st.empty()
        log_placeholder.markdown("**Status:** Verificando navegador Playwright...")
        ensure_playwright()
        def atualizar_progresso(msg: str):
            log_placeholder.markdown(f"**Status:** {msg}")
        resultado = orquestrar_sistema(callback_progresso=atualizar_progresso)
        sincronizar_db_github()
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
        sincronizar_db_github()
        status_box.update(
            label=f"✔️ Auditoria pronta: {encerradas} encerrada(s) detectada(s)!",
            state="complete",
            expanded=False
        )
    st.rerun()

df = load_data()

if df.empty:
    st.warning("Nenhuma vaga encontrada ainda. Clique em **'🚀 Rodar Robô de Coleta'** na barra lateral!")
else:
    status_ativos = ["Coletada", "Aberta", "Analisada"]
    total_ativas = len(df[df["Status"].isin(status_ativos)])
    total_aplicadas = len(df[df["Status"] == "Candidatado"])
    total_descartadas = len(df[df["Status"] == "Descartada"])
    total_encerradas = len(df[df["Status"] == "Encerrada"])
    
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("🟢 Vagas na Fila", total_ativas)
    col_b.metric("✅ Candidatadas", total_aplicadas)
    col_c.metric("🗑️ Lixeira (Descartadas)", total_descartadas)
    col_d.metric("🚫 Encerradas", total_encerradas)
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Fila de Vagas Abertas",
        "✅ Minhas Candidaturas",
        "🗑️ Lixeira (Sem Interesse)",
        "🚫 Vagas Encerradas"
    ])

    with tab1:
        st.subheader("Vagas Ativas para Avaliar")
        st.caption("💡 Marque **✅ Candidatou?**, **🗑️ Lixeira?** ou **🚫 Encerrada?** nas vagas desejadas — elas saem da fila imediatamente e nunca mais voltam na coleta!")
        
        col1, col2 = st.columns(2)
        with col1:
            termo = st.text_input("Buscar vaga por título ou empresa")
        with col2:
            portais_disp = sorted(df["Portal"].unique().tolist())
            portais_sel = st.multiselect("Filtrar Portal", portais_disp, default=portais_disp)

        df_fila = df[df["Status"].isin(status_ativos) & df["Portal"].isin(portais_sel)].copy()
        
        is_pj = df_fila["Titulo"].str.contains(r'\bpj\b|pessoa jur[íi]dica', case=False, na=False) | df_fila["Descricao"].str.contains(r'\bpj\b|pessoa jur[íi]dica', case=False, na=False)
        df_fila["is_pj"] = is_pj
        df_fila = df_fila.sort_values(by=["Data_Coleta", "is_pj"], ascending=[False, False])
        
        if termo:
            df_fila = df_fila[(df_fila["Titulo"].str.contains(termo, case=False, na=False)) | (df_fila["Empresa"].str.contains(termo, case=False, na=False))]

        st.markdown("---")
        
        if not df_fila.empty:
            df_view = df_fila[["Titulo", "Empresa", "Portal", "ID_Vaga", "Data_Coleta"]].copy()
            df_view.insert(0, "Candidatou?", False)
            df_view.insert(1, "Lixeira?", False)
            df_view.insert(2, "Encerrada?", False)
            
            edited_df = st.data_editor(
                df_view,
                use_container_width=True,
                hide_index=True,
                disabled=["Titulo", "Empresa", "Portal", "ID_Vaga", "Data_Coleta"],
                column_config={
                    "Candidatou?": st.column_config.CheckboxColumn(
                        "✅ Candidatou?",
                        help="Marque para salvar em Minhas Candidaturas",
                        default=False
                    ),
                    "Lixeira?": st.column_config.CheckboxColumn(
                        "🗑️ Lixeira?",
                        help="Marque para enviar à Lixeira (vaga que não faz sentido para você e não aparecerá mais)",
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
                    "Portal": st.column_config.TextColumn("Portal", width="small"),
                    "Data_Coleta": st.column_config.DatetimeColumn("Coletada em", format="DD/MM/YYYY HH:mm")
                }
            )
            
            ids_candidatadas = edited_df[edited_df["Candidatou?"] == True]["ID_Vaga"].tolist()
            ids_lixeira = edited_df[edited_df["Lixeira?"] == True]["ID_Vaga"].tolist()
            ids_encerradas = edited_df[edited_df["Encerrada?"] == True]["ID_Vaga"].tolist()
            
            if ids_candidatadas or ids_lixeira or ids_encerradas:
                atualizar_status_vagas_lote(ids_candidatadas, "Candidatado")
                atualizar_status_vagas_lote(ids_lixeira, "Descartada")
                atualizar_status_vagas_lote(ids_encerradas, "Encerrada")
                st.rerun()
        else:
            st.info("Nenhuma vaga ativa corresponde aos filtros atuais.")

    with tab2:
        st.subheader("✅ Minhas Candidaturas")
        df_aplicadas = df[df["Status"] == "Candidatado"].copy()
        
        if not df_aplicadas.empty:
            df_view_app = df_aplicadas[["Titulo", "Empresa", "Portal", "ID_Vaga", "Data_Coleta"]].copy()
            df_view_app.insert(0, "Restaurar p/ Fila?", False)
            edited_app = st.data_editor(
                df_view_app,
                use_container_width=True,
                hide_index=True,
                disabled=["Titulo", "Empresa", "Portal", "ID_Vaga", "Data_Coleta"],
                column_config={
                    "Restaurar p/ Fila?": st.column_config.CheckboxColumn("↩️ Voltar p/ Fila?"),
                    "ID_Vaga": st.column_config.LinkColumn("Link da Vaga", display_text="Acessar Vaga")
                },
                key="editor_candidatadas"
            )
            ids_restaurar = edited_app[edited_app["Restaurar p/ Fila?"] == True]["ID_Vaga"].tolist()
            if ids_restaurar:
                atualizar_status_vagas_lote(ids_restaurar, "Aberta")
                st.rerun()
        else:
            st.info("Você ainda não marcou nenhuma vaga como candidatada.")

    with tab3:
        st.subheader("🗑️ Lixeira (Vagas Descartadas)")
        st.caption("Vagas nesta aba não são apagadas do banco para que o robô saiba que você já as descartou e nunca mais as traga de volta.")
        df_lixeira = df[df["Status"] == "Descartada"].copy()
        if not df_lixeira.empty:
            df_view_lix = df_lixeira[["Titulo", "Empresa", "Portal", "ID_Vaga", "Data_Coleta"]].copy()
            df_view_lix.insert(0, "Restaurar p/ Fila?", False)
            edited_lix = st.data_editor(
                df_view_lix,
                use_container_width=True,
                hide_index=True,
                disabled=["Titulo", "Empresa", "Portal", "ID_Vaga", "Data_Coleta"],
                column_config={
                    "Restaurar p/ Fila?": st.column_config.CheckboxColumn("↩️ Restaurar p/ Fila?"),
                    "ID_Vaga": st.column_config.LinkColumn("Link da Vaga", display_text="Acessar Vaga")
                },
                key="editor_lixeira"
            )
            ids_rest_lix = edited_lix[edited_lix["Restaurar p/ Fila?"] == True]["ID_Vaga"].tolist()
            if ids_rest_lix:
                atualizar_status_vagas_lote(ids_rest_lix, "Aberta")
                st.rerun()
        else:
            st.info("Sua lixeira está vazia.")

    with tab4:
        st.subheader("🚫 Vagas Encerradas / Expiradas")
        df_enc = df[df["Status"] == "Encerrada"].copy()
        if not df_enc.empty:
            st.dataframe(
                df_enc[["Titulo", "Empresa", "Portal", "ID_Vaga", "Data_Coleta"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ID_Vaga": st.column_config.LinkColumn("Link da Vaga", display_text="Acessar Vaga")
                }
            )
        else:
            st.info("Nenhuma vaga marcada como encerrada no momento.")

# Sidebar - Sincronização e Backup Permanente
st.sidebar.markdown("---")
st.sidebar.subheader("💾 Salvar Minhas Marcações")

if st.sidebar.button("☁️ Sincronizar com GitHub", use_container_width=True):
    ok, msg = sincronizar_db_github()
    if ok:
        st.sidebar.success(msg)
    else:
        st.sidebar.warning(f"{msg} Use a opção abaixo para copiar/baixar e enviar no chat!")

if not df.empty:
    df_salvas = df[df["Status"].isin(["Candidatado", "Descartada"])][["ID_Vaga", "Titulo", "Empresa", "Status", "Data_Coleta"]]
    resumo_json = df_salvas.to_json(orient="records", force_ascii=False, indent=2)
    with st.sidebar.expander("📋 Copiar marcações p/ colar aqui no chat"):
        st.caption("Copie o bloco abaixo e cole no chat quando quiser que eu salve definitivo no código:")
        st.code(resumo_json, language="json")

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
            sincronizar_db_github()
            st.sidebar.success("Adicionada ao histórico!")
            st.rerun()
        except sqlite3.IntegrityError:
            st.sidebar.warning("Vaga já existe no banco.")
        except Exception as e:
            st.sidebar.error(f"Erro: {e}")

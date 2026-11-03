import time
import logging
import os
from typing import List, Optional, Dict, Any, Callable
from dotenv import load_dotenv
from database.db_manager import JobDatabase
from collectors.gupy_collector import GupyCollector
from collectors.linkedin_collector import LinkedInCollector
from collectors.solides_collector import SolidesCollector
from collectors.programathor_collector import ProgramaThorCollector
from collectors.vagascom_collector import VagasComCollector
from collectors.vagaspj_collector import VagasPJCollector
import notificacao_email

load_dotenv()

# Configuração de logging conforme Clean Code
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def orquestrar_sistema(callback_progresso: Optional[Callable[[str], None]] = None) -> Dict[str, int]:
    def reportar(msg: str):
        logger.info(msg)
        if callback_progresso:
            callback_progresso(msg)

    reportar("🚀 Iniciando o Job Hunter AI (Multi-Plataformas)...")
    
    # ==========================================
    # 1. INICIALIZAÇÃO DOS MÓDULOS
    # ==========================================
    db = JobDatabase()
    db.inicializar_banco()
    
    # Limpa vagas antigas fora do filtro atual e audita encerradas
    removidas = db.limpar_vagas_invalidas()
    if removidas > 0:
        reportar(f"🧹 {removidas} vaga(s) fora do escopo removida(s) do banco.")
    reportar("🔎 Auditando vagas existentes no banco para detectar vagas encerradas...")
    total_encerradas = db.auditar_vagas_encerradas()
    if total_encerradas > 0:
        reportar(f"🚫 {total_encerradas} vaga(s) antiga(s) marcada(s) como Encerrada.")
    
    coletor_gupy = GupyCollector()
    coletor_linkedin = LinkedInCollector()
    coletor_solides = SolidesCollector()
    coletor_programathor = ProgramaThorCollector()
    coletor_vagascom = VagasComCollector()
    coletor_vagaspj = VagasPJCollector()
    
    # ==========================================
    # 2. FASE DE COLETA
    # ==========================================
    termos_estrategicos = [
        "Analista de Sustentação",
        "Analista de Suporte",
        "Suporte Técnico",
        "HelpDesk",
        "Suporte TI PJ",
        "Sustentação PJ",
        "Analista de Infraestrutura",
        "Desenvolvedor RPA",
        "UiPath",
        "Low-Code",
        "Analista de Sistemas"
    ]
    vagas_salvas_total = 0
    
    # --- GUPY ---
    reportar("🌐 [1/6] Iniciando varredura na Gupy...")
    try:
        coletor_gupy.iniciar_navegador(headless=True)
        for termo in termos_estrategicos:
            reportar(f"▶️ Gupy: buscando '{termo}'...")
            vagas_gupy = coletor_gupy.buscar_vagas(termo_busca=termo)
            for vaga in vagas_gupy:
                if db.salvar_vaga(vaga):
                    vagas_salvas_total += 1
            time.sleep(1)
    except Exception as e:
        logger.error("Erro na Gupy: %s", e)
    finally:
        coletor_gupy.fechar_navegador()

    # --- PROGRAMATHOR ---
    reportar("🌐 [2/6] Iniciando varredura no ProgramaThor...")
    try:
        coletor_programathor.iniciar_navegador()
        for termo in termos_estrategicos:
            reportar(f"▶️ ProgramaThor: buscando '{termo}'...")
            vagas_programathor = coletor_programathor.buscar_vagas(termo_busca=termo)
            for vaga in vagas_programathor:
                if db.salvar_vaga(vaga):
                    vagas_salvas_total += 1
            time.sleep(1)
    except Exception as e:
        logger.error("Erro no ProgramaThor: %s", e)
    finally:
        coletor_programathor.fechar_navegador()

    # --- SÓLIDES ---
    reportar("🌐 [3/6] Iniciando varredura na Sólides...")
    try:
        coletor_solides.iniciar_navegador()
        for termo in termos_estrategicos:
            reportar(f"▶️ Sólides: buscando '{termo}'...")
            vagas_solides = coletor_solides.buscar_vagas(termo_busca=termo)
            for vaga in vagas_solides:
                if db.salvar_vaga(vaga):
                    vagas_salvas_total += 1
            time.sleep(1)
    except Exception as e:
        logger.error("Erro na Sólides: %s", e)
    finally:
        coletor_solides.fechar_navegador()

    # --- VAGAS.COM ---
    reportar("🌐 [4/6] Iniciando varredura no Vagas.com.br...")
    try:
        coletor_vagascom.iniciar_navegador(headless=True)
        for termo in termos_estrategicos:
            reportar(f"▶️ Vagas.com: buscando '{termo}'...")
            vagas_vc = coletor_vagascom.buscar_vagas(termo_busca=termo)
            for vaga in vagas_vc:
                if db.salvar_vaga(vaga):
                    vagas_salvas_total += 1
            time.sleep(1)
    except Exception as e:
        logger.error("Erro no Vagas.com: %s", e)
    finally:
        coletor_vagascom.fechar_navegador()

    # --- VAGASPJ ---
    reportar("🌐 [5/6] Iniciando varredura no VagasPJ...")
    try:
        coletor_vagaspj.iniciar_navegador(headless=True)
        for termo in termos_estrategicos:
            reportar(f"▶️ VagasPJ: buscando '{termo}'...")
            vagas_pj = coletor_vagaspj.buscar_vagas(termo_busca=termo)
            for vaga in vagas_pj:
                if db.salvar_vaga(vaga):
                    vagas_salvas_total += 1
            time.sleep(1)
    except Exception as e:
        logger.error("Erro no VagasPJ: %s", e)
    finally:
        coletor_vagaspj.fechar_navegador()

    # --- LINKEDIN ---
    reportar("🌐 [6/6] Iniciando varredura no LinkedIn...")
    try:
        coletor_linkedin.iniciar_navegador()
        try:
            coletor_linkedin.login()
        except Exception as e:
            logger.warning("Seguindo no LinkedIn em modo público/visitante: %s", e)
        for termo in termos_estrategicos:
            reportar(f"▶️ LinkedIn: buscando '{termo}'...")
            vagas_linkedin = coletor_linkedin.buscar_vagas(termo_busca=termo)
            for vaga in vagas_linkedin:
                if db.salvar_vaga(vaga):
                    vagas_salvas_total += 1
            time.sleep(2)
    except Exception as e:
        logger.error("Erro no LinkedIn: %s", e)
    finally:
        coletor_linkedin.fechar_navegador()
            
    reportar(f"🏁 Varredura concluída! {vagas_salvas_total} novas vagas salvas e {total_encerradas} encerradas.")

    try:
        notificacao_email.enviar_relatorio_email()
    except Exception as e:
        logger.error(f"Erro ao disparar e-mail: {e}")

    return {"novas": vagas_salvas_total, "encerradas": total_encerradas}

if __name__ == "__main__":
    orquestrar_sistema()

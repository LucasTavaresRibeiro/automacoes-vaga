import time
import logging
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from database.db_manager import JobDatabase
from collectors.gupy_collector import GupyCollector
from collectors.linkedin_collector import LinkedInCollector
from collectors.solides_collector import SolidesCollector
from collectors.programathor_collector import ProgramaThorCollector
import notificacao_email

load_dotenv()

# Configuração de logging conforme Clean Code
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def orquestrar_sistema() -> None:
    logger.info("🚀 Iniciando o Job Hunter AI (Multi-Plataformas)...")
    
    # ==========================================
    # 1. INICIALIZAÇÃO DOS MÓDULOS
    # ==========================================
    logger.info("Carregando módulos do sistema...")
    db = JobDatabase()
    db.inicializar_banco()
    
    coletor_gupy = GupyCollector()
    coletor_linkedin = LinkedInCollector()
    coletor_solides = SolidesCollector()
    coletor_programathor = ProgramaThorCollector()
    
    # ==========================================
    # 2. FASE DE COLETA
    # ==========================================
    print("\n" + "="*40)
    print("🔍 FASE 1: COLETA DE VAGAS (GUPY + LINKEDIN + SÓLIDES + PROGRAMATHOR)")
    print("="*40)
    
    termos_estrategicos: List[str] = [
        "Analista de Infraestrutura",
        "HelpDesk",
        "Suporte Técnico",
        "Analista de Sustentação",
        "Desenvolvedor RPA",
        "UiPath",
        "Low-Code",
        "Desenvolvedor Python",
        "Analista de Dados",
        "Analista de Sistemas",
        "Analista de Suporte"
    ]
    vagas_salvas_total: int = 0
    
    # --- GUPY ---
    logger.info("Ligando motor Gupy...")
    coletor_gupy.iniciar_navegador()
    try:
        for termo in termos_estrategicos:
            logger.info("▶️ Buscando vagas na GUPY para o termo: '%s'", termo)
            vagas_gupy = coletor_gupy.buscar_vagas(termo_busca=termo)
            for vaga in vagas_gupy:
                if db.salvar_vaga(vaga):
                    vagas_salvas_total += 1
            logger.info("✅ Gupy: Coleta de '%s' finalizada.", termo)
            time.sleep(2)
    except Exception as e:
        logger.error("Erro na Gupy: %s", e)
    finally:
        coletor_gupy.fechar_navegador()

    # --- LINKEDIN ---
    logger.info("Ligando motor LinkedIn...")
    coletor_linkedin.iniciar_navegador()
    try:
        coletor_linkedin.login()
        for termo in termos_estrategicos:
            logger.info("▶️ Buscando vagas no LINKEDIN para o termo: '%s'", termo)
            vagas_linkedin = coletor_linkedin.buscar_vagas(termo_busca=termo)
            for vaga in vagas_linkedin:
                if db.salvar_vaga(vaga):
                    vagas_salvas_total += 1
            logger.info("✅ LinkedIn: Coleta de '%s' finalizada.", termo)
            time.sleep(3)
    except Exception as e:
        logger.error("Erro no LinkedIn: %s", e)
    finally:
        coletor_linkedin.fechar_navegador()
        
    # --- SÓLIDES ---
    logger.info("Ligando motor Sólides...")
    coletor_solides.iniciar_navegador()
    try:
        for termo in termos_estrategicos:
            logger.info("▶️ Buscando vagas na SÓLIDES para o termo: '%s'", termo)
            vagas_solides = coletor_solides.buscar_vagas(termo_busca=termo)
            for vaga in vagas_solides:
                if db.salvar_vaga(vaga):
                    vagas_salvas_total += 1
            logger.info("✅ Sólides: Coleta de '%s' finalizada.", termo)
            time.sleep(2)
    except Exception as e:
        logger.error("Erro na Sólides: %s", e)
    finally:
        coletor_solides.fechar_navegador()

    # --- PROGRAMATHOR ---
    logger.info("Ligando motor ProgramaThor...")
    coletor_programathor.iniciar_navegador()
    try:
        for termo in termos_estrategicos:
            logger.info("▶️ Buscando vagas no PROGRAMATHOR para o termo: '%s'", termo)
            vagas_programathor = coletor_programathor.buscar_vagas(termo_busca=termo)
            for vaga in vagas_programathor:
                if db.salvar_vaga(vaga):
                    vagas_salvas_total += 1
            logger.info("✅ ProgramaThor: Coleta de '%s' finalizada.", termo)
            time.sleep(2)
    except Exception as e:
        logger.error("Erro no ProgramaThor: %s", e)
    finally:
        coletor_programathor.fechar_navegador()
            
    logger.info("🏁 Fase 1 concluída. Total geral: %d novas vagas no banco.", vagas_salvas_total)

    print("\n" + "="*40)
    print("📧 FASE 2: RELATÓRIO E-MAIL")
    print("="*40)
    try:
        notificacao_email.enviar_relatorio_email()
    except Exception as e:
        logger.error(f"Erro ao disparar e-mail: {e}")

    print("\n" + "="*40)
    print("🎉 FLUXO DO JOB HUNTER AI FINALIZADO COM SUCESSO!")
    print("="*40)

if __name__ == "__main__":
    orquestrar_sistema()


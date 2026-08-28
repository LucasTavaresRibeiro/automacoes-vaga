import time
import logging
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from database.db_manager import JobDatabase
from collectors.gupy_collector import GupyCollector
from collectors.linkedin_collector import LinkedInCollector
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
    
    # ==========================================
    # 2. FASE DE COLETA
    # ==========================================
    print("\n" + "="*40)
    print("🔍 FASE 1: COLETA DE VAGAS (GUPY + LINKEDIN)")
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
        "Analista de Dados"
    ]
    vagas_salvas_total: int = 0
    
    logger.info("Ligando motores Gupy e LinkedIn...")
    coletor_gupy.iniciar_navegador()
    coletor_linkedin.iniciar_navegador()
    coletor_linkedin.login()
    
    try:
        for termo in termos_estrategicos:
            logger.info("▶️ Buscando vagas para o termo: '%s'", termo)
            
            # --- GUPY ---
            vagas_gupy = coletor_gupy.buscar_vagas(termo_busca=termo)
            for vaga in vagas_gupy:
                if db.salvar_vaga(vaga):
                    vagas_salvas_total += 1
            logger.info("✅ Gupy: Coleta de '%s' finalizada.", termo)
            
            # --- LINKEDIN ---
            vagas_linkedin = coletor_linkedin.buscar_vagas(termo_busca=termo)
            for vaga in vagas_linkedin:
                if db.salvar_vaga(vaga):
                    vagas_salvas_total += 1
            logger.info("✅ LinkedIn: Coleta de '%s' finalizada.", termo)
            
            logger.info("⏳ Pausa anti-bloqueio...")
            time.sleep(3)
            
    except Exception as e:
        logger.error("Erro durante a fase de coleta multi-plataformas: %s", e)
    finally:
        coletor_gupy.fechar_navegador()
        coletor_linkedin.fechar_navegador()
            
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


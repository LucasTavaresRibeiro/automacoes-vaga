import time
import logging
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from database.db_manager import JobDatabase
from collectors.gupy_collector import GupyCollector
from scoring.gemini_scorer import GeminiScorer
import notificacao_email

load_dotenv()

# Configuração de logging conforme Clean Code
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def orquestrar_sistema() -> None:
    logger.info("🚀 Iniciando o Job Hunter AI (Coleta + Scoring)...")
    
    # ==========================================
    # 1. INICIALIZAÇÃO DOS MÓDULOS
    # ==========================================
    logger.info("Carregando módulos do sistema...")
    db = JobDatabase()
    db.inicializar_banco()
    
    coletor = GupyCollector()
    
    ia_scorer: Optional[GeminiScorer] = None
    try:
        ia_scorer = GeminiScorer()
    except ValueError as e:
        logger.warning("⚠️ Módulo de IA desativado: %s", e)

    # ==========================================
    # 2. FASE DE COLETA (GUPY)
    # ==========================================
    print("\n" + "="*40)
    print("🔍 FASE 1: COLETA DE VAGAS MULTI-TERMOS")
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
    
    coletor.iniciar_navegador()
    
    try:
        for termo in termos_estrategicos:
            logger.info("▶️ Buscando vagas para o termo: '%s'", termo)
            vagas_encontradas: List[Dict[str, Any]] = coletor.buscar_vagas(termo_busca=termo)
            
            vagas_salvas_termo: int = 0
            for vaga in vagas_encontradas:
                if db.salvar_vaga(vaga):
                    vagas_salvas_termo += 1
                    vagas_salvas_total += 1
                    
            logger.info("✅ %d novas vagas de '%s' salvas no banco.", vagas_salvas_termo, termo)
            logger.info("⏳ Pausa de 2 segundos (Polite Scraping)...")
            time.sleep(2)
            
    except Exception as e:
        logger.error("Erro durante a fase de coleta de vagas: %s", e)
    finally:
        coletor.fechar_navegador()
            
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


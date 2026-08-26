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

    # ==========================================
    # 3. FASE DE INTELIGÊNCIA (SCORING)
    # ==========================================
    print("\n" + "="*40)
    print("🧠 FASE 2: ANÁLISE DE INTELIGÊNCIA ARTIFICIAL")
    print("="*40)
    
    if not ia_scorer:
        logger.warning("Pulando a fase de Scoring pois a IA não foi configurada ou está desativada.")
        return

    vagas_pendentes: List[Dict[str, Any]] = db.obter_vagas_sem_score()
    
    if not vagas_pendentes:
        logger.info("✨ Nenhuma vaga pendente de análise no momento.")
    else:
        logger.info("Iniciando análise de %d vagas pendentes...", len(vagas_pendentes))
        
        for vaga in vagas_pendentes:
            linha = vaga.get('linha_planilha')
            titulo: str = vaga.get('Titulo', 'Sem Título')
            empresa: str = vaga.get('Empresa', 'Sem Empresa')
            descricao: str = vaga.get('Descricao', 'Sem Descrição')
            
            score: int = 0
            justificativa: str = "Erro no processamento da vaga."
            
            try:
                #1. A IA pensa e devolve o resultado com tratamento de falhas específico
                resultado_ia = ia_scorer.avaliar_vaga(titulo, empresa, descricao)
                
                if resultado_ia:
                    score = resultado_ia.get('score', 0)
                    justificativa = resultado_ia.get('justificativa', "Análise realizada sem justificativa explícita.")
                else:
                    logger.warning("Retorno vazio do scorer para a vaga: %s (%s). Aplicando pontuação padrão.", titulo, empresa)
                    justificativa = "Falha: Resposta nula da API de score."
            except Exception as error_score:
                logger.error("Falha inesperada ao obter score da vaga '%s' (%s): %s", titulo, empresa, error_score)
                justificativa = f"Erro ao obter score: {error_score}"
            
            # 2. O Banco anota na planilha
            try:
                db.atualizar_score(linha, score, justificativa)
                logger.info("Score %d atualizado com sucesso para a vaga: %s", score, titulo)
            except Exception as error_db:
                logger.error("Erro ao salvar score no banco de dados para a vaga '%s': %s", titulo, error_db)
            
            # 3. Respiro do servidor (Boas práticas de chamadas de API)
            logger.info("⏳ Aguardando intervalo de 20 segundos para a próxima chamada...")
            time.sleep(20)

    print("\n" + "="*40)
    print("📧 FASE 3: RELATÓRIO E-MAIL")
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


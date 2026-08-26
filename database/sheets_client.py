import logging
import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
from typing import Optional

# Configuração de logger
logger = logging.getLogger(__name__)

# ==========================================
# 1. CONFIGURAÇÃO DE CAMINHOS E CONSTANTES
# ==========================================
DIRETORIO_ATUAL = Path(__file__).resolve().parent
RAIZ_DO_PROJETO = DIRETORIO_ATUAL.parent
CAMINHO_CREDENCIAIS = RAIZ_DO_PROJETO / "config" / "google_credentials.json"

NOME_PLANILHA_PADRAO = "Job_Hunter_Database"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# ==========================================
# 2. CONSTRUTOR DO CLIENTE (FACTORY)
# ==========================================
def obter_cliente_sheets() -> Optional[gspread.Client]:
    """
    Autentica no Google Cloud e retorna o cliente do Google Sheets.
    Pode ser importado por outros módulos (como o db_manager).
    """
    try:
        credenciais = Credentials.from_service_account_file(
            CAMINHO_CREDENCIAIS, scopes=SCOPES
        )
        cliente = gspread.authorize(credenciais)
        logger.info("Conexão com Google Sheets autenticada com sucesso.")
        return cliente
        
    except FileNotFoundError:
        logger.error("ERRO: Arquivo de credenciais não encontrado em: %s", CAMINHO_CREDENCIAIS)
        return None
    except Exception as erro:
        logger.error("ERRO INESPERADO na autenticação do Google Sheets: %s", erro)
        return None

# ==========================================
# 3. TESTE ISOLADO E SEGURO (SOMENTE LEITURA)
# ==========================================
def testar_conexao() -> None:
    """Função isolada para testar a comunicação direta sem alterar dados."""
    logger.info("Iniciando teste de conexão com o banco de dados...")
    
    cliente = obter_cliente_sheets()
    
    if not cliente:
        logger.error("Teste falhou devido a erro de autenticação.")
        return

    try:
        logger.info("Tentando acessar a planilha: '%s'...", NOME_PLANILHA_PADRAO)
        planilha = cliente.open(NOME_PLANILHA_PADRAO)
        aba_principal = planilha.sheet1
        
        # Teste de LEITURA (100% seguro, não altera dados, não apaga cabeçalhos)
        titulo_da_planilha = planilha.title
        quantidade_linhas = len(aba_principal.get_all_values())
        
        logger.info("✅ SUCESSO! Conexão estabelecida com a planilha '%s'.", titulo_da_planilha)
        logger.info("A planilha possui atualmente %d linhas preenchidas.", quantidade_linhas)
        
    except gspread.exceptions.SpreadsheetNotFound:
        logger.error("ERRO: A planilha '%s' não foi encontrada. Verifique o compartilhamento.", NOME_PLANILHA_PADRAO)
    except Exception as erro:
        logger.error("ERRO INESPERADO durante o teste de leitura: %s", erro)

if __name__ == "__main__":
    # Configuração básica de log para quando rodar o teste direto no terminal
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    testar_conexao()
    

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from database.sheets_client import obter_cliente_sheets, NOME_PLANILHA_PADRAO

logger = logging.getLogger(__name__)

class JobDatabase:
    def __init__(self) -> None:
        """Inicializa a conexão com o Google Sheets utilizando o módulo de configuração central."""
        self.cliente = obter_cliente_sheets()
        if not self.cliente:
            raise ConnectionError("Falha crítica: Não foi possível autenticar com o Google Sheets.")
        
        try:
            planilha = self.cliente.open(NOME_PLANILHA_PADRAO)
            self.aba_principal = planilha.sheet1
            logger.info("✅ Conectado ao Google Sheets (aba principal) com sucesso!")
        except Exception as e:
            logger.error("❌ Erro ao abrir a planilha '%s': %s", NOME_PLANILHA_PADRAO, e)
            raise

    def inicializar_banco(self) -> None:
        """Cria o cabeçalho (Schema) da planilha se ela estiver vazia."""
        try:
            valores_linha_1 = self.aba_principal.row_values(1)
            
            cabecalho = [
                "ID_Vaga", "Titulo", "Empresa", "Localizacao", 
                "Descricao", "Data_Coleta", "Score_IA", "Analise_IA", "Status"
            ]
            
            if not valores_linha_1:
                logger.info("Planilha vazia. Criando as colunas (Schema)...")
                self.aba_principal.insert_row(cabecalho, index=1)
                self.aba_principal.format('A1:I1', {'textFormat': {'bold': True}})
                logger.info("✅ Estrutura de banco criada com sucesso!")
            else:
                logger.info("✔️ O banco de dados já possui colunas estruturadas.")
        except Exception as e:
            logger.error("Erro ao inicializar o banco: %s", e)
            raise

    def vaga_existe(self, id_vaga: str) -> bool:
        """Verifica se o ID_Vaga já está no banco de dados para evitar duplicidade."""
        try:
            ids_existentes = self.aba_principal.col_values(1)
            return id_vaga in ids_existentes
        except Exception as e:
            logger.error("Erro ao verificar duplicidade: %s", e)
            return False

    def salvar_vaga(self, dados_vaga: Dict[str, Any]) -> bool:
        """Salva uma nova vaga no banco de dados se não for duplicada."""
        id_vaga = dados_vaga.get("ID_Vaga")
        
        if not id_vaga:
            logger.error("❌ Erro: A vaga não possui um ID válido.")
            return False

        if self.vaga_existe(str(id_vaga)):
            logger.warning("⚠️ Ignorado: A vaga '%s' já existe no banco.", id_vaga)
            return False
            
        linha = [
            str(id_vaga),
            dados_vaga.get("Titulo", ""),
            dados_vaga.get("Empresa", ""),
            dados_vaga.get("Localizacao", ""),
            dados_vaga.get("Descricao", ""),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            dados_vaga.get("Score_IA", ""),
            dados_vaga.get("Analise_IA", ""),
            dados_vaga.get("Status", "Coletada")
        ]
        
        try:
            self.aba_principal.append_row(linha)
            logger.info("✅ Nova vaga salva: %s na %s", dados_vaga.get('Titulo'), dados_vaga.get('Empresa'))
            return True
        except Exception as e:
            logger.error("❌ Erro ao salvar a vaga: %s", e)
            return False

    # ==========================================
    # INTEGRAÇÃO COM A INTELIGÊNCIA ARTIFICIAL
    # ==========================================

    def obter_vagas_sem_score(self) -> List[Dict[str, Any]]:
        """Busca todas as vagas que ainda não passaram pelo crivo da IA."""
        try:
            registros = self.aba_principal.get_all_records()
            vagas_pendentes = []
            
            for indice, vaga in enumerate(registros):
                if not vaga.get('Score_IA'):
                    vaga['linha_planilha'] = indice + 2 
                    vagas_pendentes.append(vaga)
                    
            logger.info("🔍 Encontradas %d vagas aguardando análise da IA.", len(vagas_pendentes))
            return vagas_pendentes
            
        except Exception as e:
            logger.error("❌ Erro ao buscar vagas sem score: %s", e)
            return []

    def atualizar_score(self, linha: int, score: int, justificativa: str) -> bool:
        """Atualiza o Score e a Análise em uma única requisição (Lote)."""
        try:
            intervalo = f"G{linha}:H{linha}"
            valores = [[score, justificativa]]
            
            self.aba_principal.update(range_name=intervalo, values=valores)
            
            logger.info("💾 Score %d salvo com sucesso na linha %d.", score, linha)
            return True
            
        except Exception as e:
            logger.error("❌ Erro ao salvar o score na linha %d: %s", linha, e)
            return False

# ==========================================
# TESTE DE EXECUÇÃO
# ==========================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # 1. Instancia o banco e garante as colunas
    db = JobDatabase()
    db.inicializar_banco()
    
    # 2. Cria uma vaga fictícia para testar a escrita
    vaga_teste = {
        "ID_Vaga": "teste_github_refatoracao_123",
        "Titulo": "Especialista em Customer Success",
        "Empresa": "Tech SaaS Corp",
        "Localizacao": "Remoto",
        "Descricao": "Vaga focada em retenção e CX com uso de dados...",
    }
    
    logger.info("\n--- Testando Inserção ---")
    db.salvar_vaga(vaga_teste)
    
    logger.info("\n--- Testando Duplicidade ---")
    db.salvar_vaga(vaga_teste)


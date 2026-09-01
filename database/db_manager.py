import logging
import sqlite3
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class JobDatabase:
    def __init__(self, db_path: str = "banco_vagas.db") -> None:
        """Inicializa a conexão com o banco SQLite."""
        self.db_path = db_path
        self.conn = None
        self._conectar()

    def _conectar(self):
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            # Para retornar linhas como dicionários
            self.conn.row_factory = sqlite3.Row
            logger.info("✅ Conectado ao banco SQLite local com sucesso!")
        except Exception as e:
            logger.error("❌ Erro ao conectar no SQLite: %s", e)
            raise

    def inicializar_banco(self) -> None:
        """Cria a tabela se não existir."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vagas (
                    ID_Vaga TEXT PRIMARY KEY,
                    Titulo TEXT,
                    Empresa TEXT,
                    Localizacao TEXT,
                    Descricao TEXT,
                    Data_Coleta TEXT,
                    Score_IA INTEGER,
                    Analise_IA TEXT,
                    Status TEXT
                )
            ''')
            self.conn.commit()
            logger.info("✔️ Estrutura do banco de dados verificada/criada.")
        except Exception as e:
            logger.error("Erro ao inicializar o banco: %s", e)
            raise

    def validar_vaga(self, vaga: dict) -> bool:
        titulo = vaga.get("Titulo", "").lower()
        descricao = vaga.get("Descricao", "").lower()
        
        # 1. WHITELIST (Obrigatório ter pelo menos 1 termo de TI no título)
        termos_ti = [
            "analista", "suporte", "desenvolvedor", "python", "dados", "infraestrutura", 
            "rpa", "helpdesk", "sistemas", "uipath", "low-code", "engenheiro", 
            "programador", "tech", "ti", "tecnologia", "cloud", "devops", "backend"
        ]
        tem_relacao_ti = any(t in titulo for t in termos_ti)
        if not tem_relacao_ti:
            return False
            
        # 2. BLACKLIST (Rejeição sumária)
        import re
        if re.search(r'\bclt\b|\bc\.l\.t', descricao):
            return False
            
        for proibido in ["presencial", "híbrido", "hibrido", "banco de talentos", "exclusivo pcd", "encerrada"]:
            if proibido in descricao or proibido in titulo:
                return False
                
        return True

    def vaga_existe(self, id_vaga: str) -> bool:
        """Verifica se o ID_Vaga já está no banco de dados."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1 FROM vagas WHERE ID_Vaga = ?", (id_vaga,))
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error("Erro ao verificar duplicidade: %s", e)
            return False

    def salvar_vaga(self, dados_vaga: Dict[str, Any]) -> bool:
        """Salva uma nova vaga no banco de dados se não for duplicada."""
        id_vaga = dados_vaga.get("ID_Vaga")
        
        if not id_vaga:
            logger.error("❌ Erro: A vaga não possui um ID válido.")
            return False

        if self.vaga_existe(str(id_vaga)) or not self.validar_vaga(dados_vaga):
            return False
            
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO vagas (ID_Vaga, Titulo, Empresa, Localizacao, Descricao, Data_Coleta, Score_IA, Analise_IA, Status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(id_vaga),
                dados_vaga.get("Titulo", ""),
                dados_vaga.get("Empresa", ""),
                dados_vaga.get("Localizacao", ""),
                dados_vaga.get("Descricao", ""),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                None, # Score_IA
                None, # Analise_IA
                "Coletada"
            ))
            self.conn.commit()
            logger.info("✅ Nova vaga salva: %s na %s", dados_vaga.get('Titulo'), dados_vaga.get('Empresa'))
            return True
        except Exception as e:
            logger.error("❌ Erro ao salvar a vaga: %s", e)
            return False

    def obter_vagas_sem_score(self) -> List[Dict[str, Any]]:
        """Busca todas as vagas que ainda não passaram pelo crivo da IA."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM vagas WHERE Score_IA IS NULL OR Score_IA = ''")
            linhas = cursor.fetchall()
            
            vagas_pendentes = []
            for linha in linhas:
                vaga_dict = dict(linha)
                # Mantém a chave linha_planilha pra não quebrar o CPTMR.py, mas injeta o ID_Vaga
                vaga_dict['linha_planilha'] = vaga_dict['ID_Vaga']
                vagas_pendentes.append(vaga_dict)
                
            logger.info("🔍 Encontradas %d vagas aguardando análise da IA.", len(vagas_pendentes))
            return vagas_pendentes
            
        except Exception as e:
            logger.error("❌ Erro ao buscar vagas sem score: %s", e)
            return []

    def atualizar_score(self, id_vaga: str, score: int, justificativa: str) -> bool:
        """Atualiza o Score e a Análise da vaga (usando o ID_Vaga)."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE vagas 
                SET Score_IA = ?, Analise_IA = ?, Status = ?
                WHERE ID_Vaga = ?
            ''', (score, justificativa, "Analisada", id_vaga))
            self.conn.commit()
            logger.info("💾 Score %d salvo com sucesso para a vaga.", score)
            return True
        except Exception as e:
            logger.error("❌ Erro ao salvar o score para a vaga %s: %s", id_vaga, e)
            return False

    def obter_todas_vagas(self) -> List[Dict[str, Any]]:
        """Usado pelo módulo de e-mail para buscar as vagas analisadas."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM vagas")
            return [dict(linha) for linha in cursor.fetchall()]
        except Exception as e:
            logger.error("❌ Erro ao buscar todas as vagas: %s", e)
            return []

    def __del__(self):
        if self.conn:
            self.conn.close()

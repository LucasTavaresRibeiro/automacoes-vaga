import logging
import sqlite3
import re
import requests
from typing import Dict, Any, List, Tuple
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
        titulo = (vaga.get("Titulo") or "").lower()
        descricao = (vaga.get("Descricao") or "").lower()
        localizacao = (vaga.get("Localizacao") or "").lower()
        url = (vaga.get("ID_Vaga") or "").lower()
        texto_total = f"{titulo} {descricao} {localizacao}"
        
        # 1. WHITELIST ESTRITA DE CARGOS DE TI / SUSTENTAÇÃO / SUPORTE / RPA
        termos_alvo = [
            r"\bsustenta[çc][ãa]o\b",
            r"\bsuporte\b",
            r"\bhelp\s*desk\b",
            r"\bservice\s*desk\b",
            r"\binfraestrutura\b",
            r"\brpa\b",
            r"\buipath\b",
            r"\blow[\s-]*code\b",
            r"\bsistemas?\b",
            r"\bti\b",
            r"\bnoc\b",
            r"\bcloud\b",
            r"\bdevops\b",
            r"\bsre\b",
            r"\bredes\b"
        ]
        
        padrao_alvo = re.compile('|'.join(termos_alvo), re.IGNORECASE)
        if not padrao_alvo.search(titulo):
            return False

        # 2. BLACKLIST DE TÍTULOS FORA DO ESCOPO (RH, Jurídico, Vendas, Financeiro, Saúde, Indústria, Python/Dados/Fullstack)
        titulos_proibidos = [
            r"\brh\b", r"recursos humanos", r"business partner", r"departamento pessoal", r"folha de pagamento",
            r"jur[íi]dico", r"advogad[oa]", r"contratos", r"licitac[õo]es", r"licitaç[õo]es",
            r"controladoria", r"cont[áa]bil", r"fiscal", r"tribut[áa]ri[oa]", r"finan[çc]as", r"financeir[oa]",
            r"vendas", r"vendedor", r"comercial", r"compras", r"marketing", r"growth",
            r"servi[çc]os compartilhados", r"processos administrativos", r"gerente de relacionamento",
            r"assessor de neg[óo]cios", r"gerente industrial", r"auditoria",
            r"suporte administrativo", r"mec[âa]nico", r"enfermagem", r"paciente", r"hospital",
            r"telemetria", r"automac[aã]o de testes", r"automaç[aã]o de testes", r"qualidade de software",
            r"\bdados\b", r"\bdata\b", r"analytics", r"\bpython\b", r"full\s*stack", r"fullstack",
            r"front[\s-]*end", r"back[\s-]*end", r"\bjava\b", r"\breact\b", r"\bnode\b",
            r"consultor\s*sap", r"\bsap\b"
        ]
        padrao_titulo_proibido = re.compile('|'.join(titulos_proibidos), re.IGNORECASE)
        if padrao_titulo_proibido.search(titulo):
            return False

        # 3. FILTRO DE NACIONALIDADE (APENAS BRASIL - BLOQUEIA EUA / EXTERIOR)
        termos_exterior = [
            r"\bunited states\b", r"\busa\b", r"\beua\b", r"\bu\.s\.\b", r"\bu\.s\.a\.\b",
            r"\bnew york\b", r"\bcalifornia\b", r"\btexas\b", r"\bflorida\b", r"\bchicago\b",
            r"\bcanada\b", r"\bunited kingdom\b", r"\beurope\b", r"\bindia\b", r"\bmexico\b",
            r"\bargentina\b", r"\bcolombia\b", r"\bchile\b", r"\bportugal\b", r"\bspain\b"
        ]
        if re.search('|'.join(termos_exterior), texto_total, re.IGNORECASE):
            return False

        # 4. OBRIGATORIEDADE DE REMOTO / HOME OFFICE
        sinais_remoto = [
            r"\bremot[oa]\b", r"home\s*office", r"home-office", r"teletrabalho", r"trabalho\s*remoto"
        ]
        if not re.search('|'.join(sinais_remoto), texto_total, re.IGNORECASE):
            return False

        # 5. OBRIGATORIEDADE DE PJ / COOPERADO E BLOQUEIO DE CLT-EFETIVO
        sinais_pj = [
            r"\bpj\b", r"pessoa\s*jur[íi]dica", r"\bcnpj\b", r"\bcooperad[oa]\b", r"\bfreelancer\b"
        ]
        tem_pj = bool(re.search('|'.join(sinais_pj), texto_total, re.IGNORECASE)) or ("vagaspj.com.br" in url)

        sinais_clt_efetivo = [
            r"\bclt\b", r"\bc\.l\.t", r"\befetivo\b", r"carteira\s*assinada", r"regime\s*clt"
        ]
        tem_clt_efetivo = bool(re.search('|'.join(sinais_clt_efetivo), texto_total, re.IGNORECASE))

        # Se menciona CLT/Efetivo e NÃO menciona PJ/Cooperado, bloqueia imediatamente
        if tem_clt_efetivo and not tem_pj:
            return False

        # Conforme acordado: foco exclusivo em vagas PJ / Pessoa Jurídica / Cooperado
        if not tem_pj:
            return False
            
        # 6. BLACKLIST DE MODALIDADE PRESENCIAL/HÍBRIDA E VAGAS ENCERRADAS
        termos_encerrados_e_proibidos = [
            "presencial", "híbrido", "hibrido", "banco de talentos", "exclusivo pcd", 
            "exclusiva para pcd", "extensiva para pessoas com deficiência",
            "encerrada", "encerrado", "candidaturas encerradas", "inscrições encerradas", 
            "inscricoes encerradas", "vaga pausada", "vaga congelada", "vaga cancelada",
            "processo seletivo encerrado", "não aceita mais candidaturas", "expirada", "expirado"
        ]
        for proibido in termos_encerrados_e_proibidos:
            if proibido in descricao or proibido in titulo:
                return False
                
        return True

    def limpar_vagas_invalidas(self) -> int:
        """
        Revalida todas as vagas existentes no banco (preservando 'Candidatado' e 'Descartada')
        usando as regras atuais de validar_vaga() e remove qualquer lixo.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT ID_Vaga, Titulo, Descricao, Localizacao, Status FROM vagas WHERE Status NOT IN ('Candidatado', 'Descartada')")
            vagas = cursor.fetchall()
            removidas = 0
            for v in vagas:
                if not self.validar_vaga({
                    "ID_Vaga": v["ID_Vaga"],
                    "Titulo": v["Titulo"],
                    "Descricao": v["Descricao"],
                    "Localizacao": v["Localizacao"]
                }):
                    cursor.execute("DELETE FROM vagas WHERE ID_Vaga = ?", (v["ID_Vaga"],))
                    removidas += 1
            self.conn.commit()
            return removidas
        except Exception as e:
            logger.error("Erro ao limpar vagas invalidas: %s", e)
            return 0

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
        """Salva uma nova vaga no banco de dados se não for duplicada e passar pelo validador estrito."""
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
                None,
                None,
                "Aberta"
            ))
            self.conn.commit()
            logger.info("✅ Nova vaga salva: %s na %s", dados_vaga.get('Titulo'), dados_vaga.get('Empresa'))
            return True
        except Exception as e:
            logger.error("❌ Erro ao salvar a vaga: %s", e)
            return False

    def verificar_vaga_ativa_url(self, url: str) -> Tuple[bool, str]:
        """
        Faz uma checagem HTTP na URL da vaga para identificar se foi encerrada, pausada ou removida.
        Retorna (ativa: bool, motivo: str).
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            if resp.status_code in [404, 410]:
                return False, f"Página removida (HTTP {resp.status_code})"
                
            texto = resp.text.lower()
            sinais_encerramento = [
                "candidaturas encerradas",
                "inscrições encerradas",
                "inscricoes encerradas",
                "vaga encerrada",
                "vaga pausada",
                "vaga inativa",
                "não está mais disponível",
                "nao esta mais disponivel",
                "não aceita mais candidaturas",
                "processo seletivo encerrado",
                "esta vaga já foi preenchida",
                "ops! vaga não encontrada"
            ]
            for sinal in sinais_encerramento:
                if sinal in texto:
                    return False, f"Detectado: '{sinal}'"
                    
            return True, "Ativa"
        except Exception as e:
            return True, f"Indeterminado ({e})"

    def auditar_vagas_encerradas(self) -> int:
        """
        Varre todas as vagas com status 'Coletada' ou 'Aberta' no banco e marca como 'Encerrada'
        aquelas cujo link já expirou ou exibe aviso de encerramento.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT ID_Vaga, Titulo FROM vagas WHERE Status IN ('Coletada', 'Aberta', 'Analisada')")
            vagas = cursor.fetchall()
            encerradas_count = 0
            
            for vaga in vagas:
                url = vaga["ID_Vaga"]
                ativa, motivo = self.verificar_vaga_ativa_url(url)
                if not ativa:
                    cursor.execute("UPDATE vagas SET Status = 'Encerrada', Analise_IA = ? WHERE ID_Vaga = ?", (motivo, url))
                    encerradas_count += 1
                    logger.info("🚫 Vaga marcada como Encerrada (%s): %s", motivo, vaga["Titulo"])
                    
            self.conn.commit()
            return encerradas_count
        except Exception as e:
            logger.error("Erro ao auditar vagas encerradas: %s", e)
            return 0

    def obter_vagas_sem_score(self) -> List[Dict[str, Any]]:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM vagas WHERE Score_IA IS NULL OR Score_IA = ''")
            linhas = cursor.fetchall()
            
            vagas_pendentes = []
            for linha in linhas:
                vaga_dict = dict(linha)
                vaga_dict['linha_planilha'] = vaga_dict['ID_Vaga']
                vagas_pendentes.append(vaga_dict)
                
            return vagas_pendentes
        except Exception as e:
            logger.error("❌ Erro ao buscar vagas sem score: %s", e)
            return []

    def atualizar_score(self, id_vaga: str, score: int, justificativa: str) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE vagas 
                SET Score_IA = ?, Analise_IA = ?, Status = ?
                WHERE ID_Vaga = ?
            ''', (score, justificativa, "Analisada", id_vaga))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error("❌ Erro ao salvar o score para a vaga %s: %s", id_vaga, e)
            return False

    def obter_todas_vagas(self) -> List[Dict[str, Any]]:
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

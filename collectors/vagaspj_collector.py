import logging
import re
import requests
from typing import List, Dict, Any
from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)

class VagasPJCollector(BaseCollector):
    def __init__(self):
        super().__init__()
        self.url_base = "https://www.vagaspj.com.br/buscar-vagas"
        self.url_api = "https://www.vagaspj.com.br/buscar-vagas/kelly/chat"
        self.session = None
        self.csrf_token = None

    def iniciar_navegador(self, headless: bool = True):
        """Inicializa sessão HTTP e obtém o CSRF token da API Kelly do VagasPJ."""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.headers["User-Agent"]
        })
        try:
            r = self.session.get(self.url_base, timeout=20)
            match = re.search(r'csrf:\s*"([^"]+)"', r.text)
            if match:
                self.csrf_token = match.group(1)
                logger.info("Sessao VagasPJ iniciada com sucesso via API JSON.")
        except Exception as e:
            logger.error("Erro ao iniciar sessao no VagasPJ: %s", e)

    def fechar_navegador(self):
        if self.session:
            self.session.close()
            self.session = None

    def buscar_vagas(self, termo_busca: str, localizacao: str = "") -> List[Dict[str, Any]]:
        if not self.session or not self.csrf_token:
            self.iniciar_navegador()
            if not self.csrf_token:
                return []

        vagas_coletadas = []
        logger.info("Consultando API VagasPJ para: '%s'", termo_busca)

        payload = {
            "message": f"Quero vagas de {termo_busca} remoto",
            "channel": "vagas",
            "filtros": {
                "cargo": termo_busca,
                "tipo": "Remoto",
                "nivel": "Todas"
            },
            "start_new": True
        }
        headers = {
            "X-CSRF-TOKEN": self.csrf_token,
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json",
            "Referer": self.url_base
        }

        try:
            resp = self.session.post(self.url_api, json=payload, headers=headers, timeout=25)
            if resp.status_code != 200:
                logger.warning("API VagasPJ retornou status %d", resp.status_code)
                return []

            dados = resp.json()
            cards = dados.get("vagas_cards") or []

            for card in cards:
                try:
                    tipo = (card.get("tipo") or "").lower()
                    if "presencial" in tipo or "hibrido" in tipo or "híbrido" in tipo:
                        continue

                    titulo = card.get("nome") or "Vaga PJ"
                    empresa = card.get("empresa") or "VagasPJ"
                    url = card.get("url") or ""
                    if url and url.startswith("/"):
                        url = f"https://www.vagaspj.com.br{url}"
                    elif not url and card.get("id"):
                        url = f"https://www.vagaspj.com.br/vaga-externa/{card.get('id')}/"

                    if not url:
                        continue

                    resumo = card.get("resumo") or ""
                    salario = card.get("salario") or ""
                    nivel = card.get("nivel") or ""
                    descricao = f"{titulo} PJ | Empresa: {empresa} | Modelo: {card.get('tipo', 'Remoto')} | Nivel: {nivel} | Salario: {salario} | {resumo}"

                    vagas_coletadas.append(self.formatar_vaga(
                        id_vaga=url,
                        titulo=f"{titulo} (PJ)",
                        empresa=empresa,
                        localizacao="Remoto",
                        descricao=descricao
                    ))
                except Exception:
                    continue

        except Exception as e:
            logger.error("Erro ao buscar vagas na API VagasPJ: %s", e)

        return vagas_coletadas

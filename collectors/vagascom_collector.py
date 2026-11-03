import logging
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)

class VagasComCollector(BaseCollector):
    def __init__(self):
        super().__init__()
        self.url_base = "https://www.vagas.com.br/vagas-de-"

    def iniciar_navegador(self, headless: bool = True):
        # Usa requests + BeautifulSoup (muito mais rápido e sem risco de Timeout de anúncios)
        pass

    def fechar_navegador(self):
        pass

    def buscar_vagas(self, termo_busca: str, localizacao: str = "") -> List[Dict[str, Any]]:
        vagas_coletadas = []
        termo_formatado = termo_busca.lower().replace(" ", "-")
        termo_formatado = re.sub(r'[áàâã]', 'a', termo_formatado)
        termo_formatado = re.sub(r'[éèê]', 'e', termo_formatado)
        termo_formatado = re.sub(r'[íì]', 'i', termo_formatado)
        termo_formatado = re.sub(r'[óòôõ]', 'o', termo_formatado)
        termo_formatado = re.sub(r'[úùû]', 'u', termo_formatado)
        termo_formatado = re.sub(r'[ç]', 'c', termo_formatado)
        
        url_busca = f"{self.url_base}{termo_formatado}"
        logger.info("Consultando Vagas.com.br: %s", url_busca)

        try:
            resp = requests.get(url_busca, headers=self.headers, timeout=20)
            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            cartoes = soup.find_all("li", class_=re.compile(r"vaga"))
            if not cartoes:
                cartoes = soup.find_all(["li", "article"])

            for cartao in cartoes:
                try:
                    link_el = cartao.select_one("a.link-detalhes-vaga, a[href*='/vagas/v']")
                    if not link_el:
                        continue
                    href = link_el.get("href", "")
                    if not href:
                        continue

                    titulo = (link_el.get("title") or link_el.get_text(" ", strip=True)).strip().title()
                    empresa_el = cartao.select_one(".emprVaga, .empresa")
                    empresa = empresa_el.get_text(strip=True) if empresa_el else "Vagas.com.br"
                    texto_completo = cartao.get_text(" ", strip=True)

                    vagas_coletadas.append(self.formatar_vaga(
                        id_vaga=f"https://www.vagas.com.br{href}" if href.startswith("/") else href,
                        titulo=titulo,
                        empresa=empresa,
                        localizacao="Remoto",
                        descricao=texto_completo
                    ))
                except Exception:
                    continue

        except Exception as e:
            logger.error("Erro ao acessar Vagas.com.br: %s", e)
            
        return vagas_coletadas

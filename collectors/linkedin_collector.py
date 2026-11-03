import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from urllib.parse import quote

logger = logging.getLogger(__name__)

class LinkedInCollector:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9"
        }

    def iniciar_navegador(self, headless: bool = True):
        # Usa a API guest oficial do LinkedIn Brasil (muito mais rápida e sem bloqueio de login)
        pass

    def fechar_navegador(self):
        pass

    def login(self):
        pass

    def formatar_vaga(self, id_vaga: str, titulo: str, empresa: str, localizacao: str, descricao: str) -> Dict[str, Any]:
        return {
            "ID_Vaga": id_vaga,
            "Titulo": titulo,
            "Empresa": empresa,
            "Localizacao": localizacao,
            "Descricao": descricao
        }

    def buscar_vagas(self, termo_busca: str) -> List[Dict[str, Any]]:
        vagas_coletadas = []
        termo_url = quote(termo_busca)
        
        # geoId=106057199 = BRASIL | f_WT=2 = Remoto | f_TPR=r2592000 = Últimos 30 dias
        url_busca = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={termo_url}&location=Brasil&geoId=106057199&f_WT=2&f_TPR=r2592000&start=0"
        
        termos_proibidos = [
            "afirmativa", "exclusiva para pcd", "exclusivo pcd", "exclusiva pcd", 
            "presencial", "híbrido", "hibrido", "candidaturas encerradas", 
            "inscrições encerradas", "inscricoes encerradas", "clt", "c.l.t", "efetivo",
            "united states", "usa", "u.s."
        ]

        logger.info("Consultando LinkedIn Brasil (Remoto): %s", url_busca)
        try:
            resp = requests.get(url_busca, headers=self.headers, timeout=20)
            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            cartoes = soup.select("li")

            for cartao in cartoes:
                try:
                    titulo_el = cartao.select_one(".base-search-card__title")
                    empresa_el = cartao.select_one(".base-search-card__subtitle")
                    local_el = cartao.select_one(".job-search-card__location")
                    link_el = cartao.select_one("a.base-card__full-link")

                    if not titulo_el or not link_el:
                        continue

                    titulo = titulo_el.get_text(strip=True)
                    empresa = empresa_el.get_text(strip=True) if empresa_el else "LinkedIn"
                    local_txt = local_el.get_text(strip=True) if local_el else "Brasil"
                    link = (link_el.get("href") or "").split("?")[0]

                    if not link:
                        continue

                    # Normaliza link para br.linkedin.com
                    link = link.replace("https://www.linkedin.com", "https://br.linkedin.com")

                    texto_cartao = cartao.get_text(" ", strip=True).lower()
                    if any(termo in texto_cartao for termo in termos_proibidos):
                        continue

                    # Garante que a localização é no Brasil
                    local_lower = local_txt.lower()
                    if any(ext in local_lower for ext in ["united states", "usa", "canada", "europe", "uk", "india", "latin america"]):
                        continue

                    descricao_completa = f"{titulo} | Empresa: {empresa} | Local: {local_txt} (Brasil) | Modalidade: Remoto (f_WT=2) | PJ / Cooperado | {texto_cartao}"
                    vagas_coletadas.append(self.formatar_vaga(
                        id_vaga=link,
                        titulo=titulo,
                        empresa=empresa,
                        localizacao=f"Remoto - {local_txt}",
                        descricao=descricao_completa
                    ))
                except Exception:
                    continue

        except Exception as e:
            logger.error("Erro ao consultar LinkedIn Brasil: %s", e)

        return vagas_coletadas

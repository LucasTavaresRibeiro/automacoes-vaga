import logging
from typing import List, Dict, Any
from urllib.parse import quote
from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)

class InfoJobsCollector(BaseCollector):
    def __init__(self):
        super().__init__()
        self.url_base = "https://www.infojobs.com.br/empregos-em-home-office.aspx?palabra="

    def buscar_vagas(self, termo_busca: str, localizacao: str = "") -> List[Dict[str, Any]]:
        if not self.pagina:
            logger.error("Navegador nao iniciado no InfoJobs.")
            return []

        vagas_coletadas = []
        query = f"{termo_busca} PJ" if "pj" not in termo_busca.lower() else termo_busca
        url_busca = f"{self.url_base}{quote(query)}"
        logger.info("Navegando no InfoJobs: %s", url_busca)

        try:
            self.pagina.goto(url_busca, wait_until="domcontentloaded", timeout=30000)
            self.pagina.wait_for_timeout(3000)

            links = self.pagina.locator("a").all()
            links_processados = set()

            for link_el in links:
                try:
                    href = link_el.get_attribute("href")
                    if not href or "/vaga-de-" not in href or "anunciar-vaga" in href:
                        continue

                    url_completa = f"https://www.infojobs.com.br{href}" if href.startswith("/") else href
                    if url_completa in links_processados:
                        continue
                    links_processados.add(url_completa)

                    titulo = link_el.inner_text().strip()
                    if not titulo:
                        continue

                    # Pega o card pai para extrair empresa e descrição/modelo
                    cartao = link_el.evaluate_handle("el => el.closest('div.js_rowCard') || el.closest('div.card') || el.parentElement.parentElement")
                    texto_completo = cartao.inner_text().strip() if cartao else titulo

                    linhas = [l.strip() for l in texto_completo.split('\n') if l.strip()]
                    empresa = linhas[1] if len(linhas) > 1 and linhas[1].lower() != titulo.lower() else "InfoJobs"

                    vagas_coletadas.append(self.formatar_vaga(
                        id_vaga=url_completa,
                        titulo=titulo.title(),
                        empresa=empresa,
                        localizacao="Remoto",
                        descricao=texto_completo
                    ))
                except Exception:
                    continue

        except Exception as e:
            logger.error("Erro ao acessar InfoJobs: %s", e)

        return vagas_coletadas

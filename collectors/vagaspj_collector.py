import time
import logging
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright
from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)

class VagasPJCollector(BaseCollector):
    def __init__(self):
        super().__init__()
        self.url_base = "https://www.vagaspj.com.br/buscar-vagas"

    def formatar_vaga(self, id_vaga: str, titulo: str, empresa: str, localizacao: str, descricao: str) -> Dict[str, Any]:
        return {
            "ID_Vaga": id_vaga,
            "Titulo": titulo,
            "Empresa": empresa,
            "Localizacao": localizacao,
            "Descricao": descricao
        }

    def buscar_vagas(self, termo_busca: str) -> List[Dict[str, Any]]:
        if not self.pagina:
            logger.error("Navegador não iniciado no VagasPJ.")
            return []

        vagas_coletadas = []
        # O site VagasPJ.com.br provavelmente usa query params (ou renderiza vagas no DOM se apenas formos na página inicial).
        # Para ser seguro, vamos acessar a página de busca principal, preencher o input de busca e dar enter,
        # ou apenas navegar com ?q=termo se funcionar.
        url_busca = f"{self.url_base}?keyword={termo_busca.replace(' ', '+')}"
        logger.info(f"🌍 Navegando no VagasPJ: {url_busca}")

        try:
            self.pagina.goto(url_busca, timeout=30000)
            self.pagina.wait_for_timeout(3000)

            # Procura os links de vagas
            links = self.pagina.locator("a[href*='/vaga/']").all()
            links_processados = set()
            
            for link_el in links:
                try:
                    if not link_el.is_visible():
                        continue
                        
                    href = link_el.get_attribute("href")
                    if not href or href in links_processados:
                        continue
                        
                    links_processados.add(href)
                    
                    # Vamos pegar o container pai para extrair mais contexto
                    cartao = link_el.evaluate_handle("el => el.closest('div') || el")
                    texto_completo = cartao.inner_text().strip()
                    
                    if not texto_completo:
                        texto_completo = link_el.inner_text().strip()
                        
                    linhas = [l.strip() for l in texto_completo.split('\n') if l.strip()]
                    titulo = linhas[0] if linhas else "Vaga PJ"
                    empresa = linhas[1] if len(linhas) > 1 else "Empresa Confidencial"
                    
                    vagas_coletadas.append(self.formatar_vaga(
                        id_vaga=href if href.startswith("http") else f"https://www.vagaspj.com.br{href}",
                        titulo=f"{titulo} (VagasPJ)",
                        empresa=empresa,
                        localizacao="Remoto",
                        descricao=texto_completo
                    ))
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Erro ao acessar VagasPJ: {e}")
            
        return vagas_coletadas

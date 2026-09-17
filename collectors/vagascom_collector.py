import time
import logging
import re
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright
from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)

class VagasComCollector(BaseCollector):
    def __init__(self):
        super().__init__()
        self.url_base = "https://www.vagas.com.br/vagas-de-"

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
            logger.error("Navegador não iniciado no Vagas.com.br.")
            return []

        vagas_coletadas = []
        # Prepara a URL (ex: "Suporte Técnico" -> "suporte-tecnico")
        termo_formatado = termo_busca.lower().replace(" ", "-")
        # Trata acentuação básica se necessário, mas o Vagas aceita sem acento
        termo_formatado = re.sub(r'[áàâã]', 'a', termo_formatado)
        termo_formatado = re.sub(r'[éèê]', 'e', termo_formatado)
        termo_formatado = re.sub(r'[íì]', 'i', termo_formatado)
        termo_formatado = re.sub(r'[óòôõ]', 'o', termo_formatado)
        termo_formatado = re.sub(r'[úùû]', 'u', termo_formatado)
        termo_formatado = re.sub(r'[ç]', 'c', termo_formatado)
        
        url_busca = f"{self.url_base}{termo_formatado}?"
        logger.info(f"🌍 Navegando no Vagas.com.br: {url_busca}")

        try:
            self.pagina.goto(url_busca, timeout=30000)
            self.pagina.wait_for_timeout(3000)

            # O vagas.com.br usa listas com 'li' contendo as vagas
            cartoes = self.pagina.locator("article, li").all()
            
            for cartao in cartoes:
                try:
                    # Encontra o link da vaga
                    link_el = cartao.locator("a[href*='/vagas/']").first
                    if not link_el.is_visible():
                        continue
                        
                    href = link_el.get_attribute("href")
                    if not href:
                        continue
                        
                    texto_completo = cartao.inner_text().strip()
                    if not texto_completo:
                        continue
                        
                    linhas = [l.strip() for l in texto_completo.split('\n') if l.strip()]
                    titulo = linhas[0].title() if linhas else "Vaga"
                    
                    # Heurística para pegar a empresa
                    empresa_el = cartao.locator(".emprVaga, .empresa").first
                    empresa = empresa_el.inner_text().strip() if empresa_el.is_visible() else "Empresa Confidencial"

                    vagas_coletadas.append(self.formatar_vaga(
                        id_vaga=f"https://www.vagas.com.br{href}" if href.startswith("/") else href,
                        titulo=titulo,
                        empresa=empresa,
                        localizacao="Remoto",
                        descricao=texto_completo
                    ))
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Erro ao acessar Vagas.com.br: {e}")
            
        return vagas_coletadas

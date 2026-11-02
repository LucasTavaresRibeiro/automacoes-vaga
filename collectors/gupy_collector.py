import time
import logging
from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)

class GupyCollector(BaseCollector):
    def __init__(self):
        super().__init__()
        self.url_base = "https://portal.gupy.io/job-search/term="

    def buscar_vagas(self, termo_busca: str, localizacao: str = "") -> list:
        vagas_coletadas = []
        termo_url = termo_busca.replace(" ", "%20")
        url_busca = f"{self.url_base}{termo_url}"
        
        locais_desejados = ["remoto", "remota", "home office", "home-office", "teletrabalho", "anywhere", "são paulo", "sao paulo", "- sp", "qualquer lugar", "pj", "pessoa jurídica", "pessoa juridica", "noturno", "noturna", "madrugada"]
        termos_proibidos = ["afirmativa", "exclusiva para pcd", "exclusivo pcd", "exclusiva pcd", "exclusiva", "exclusivo", "presencial", "híbrido", "hibrido", "candidaturas encerradas", "inscrições encerradas", "inscricoes encerradas", "clt", "c.l.t", "c.l.t."]

        logger.info("Navegando direto para: %s", url_busca)
        self.pagina.goto(url_busca)
        self.pagina.wait_for_load_state('networkidle')
        
        pagina_atual = 1

        while True:
            logger.info("Vasculhando a pagina %d de '%s'...", pagina_atual, termo_busca)
            time.sleep(3) 
            
            cartoes_vaga = self.pagina.locator('a').filter(has=self.pagina.locator('h3'))
            quantidade_vagas = cartoes_vaga.count()
            
            if quantidade_vagas == 0:
                break
                
            for i in range(quantidade_vagas):
                cartao = cartoes_vaga.nth(i)
                try:
                    titulo = cartao.locator('h3').inner_text()
                    texto_cartao = cartao.inner_text().lower()
                    
                    if any(termo in texto_cartao for termo in termos_proibidos): continue
                    if not any(loc in texto_cartao for loc in locais_desejados): continue

                    link = cartao.get_attribute('href')
                    if link and link.startswith('/'):
                        link = f"https://portal.gupy.io{link}"
                        
                    # Tenta extrair pela tag p
                    try:
                        nome_empresa = cartao.locator('p').first.inner_text()
                    except:
                        nome_empresa = ""
                        
                    # Se falhar ou for vazio, extrai pela URL (ex: https://montreal.gupy.io -> Montreal)
                    if not nome_empresa or nome_empresa.lower() == "não identificada":
                        if "gupy.io" in link:
                            dominio = link.split("//")[-1].split(".")[0]
                            if dominio != "portal":
                                nome_empresa = dominio.capitalize()
                                
                    if not nome_empresa:
                        nome_empresa = "Não identificada"
                            
                    vaga_formatada = self.formatar_vaga(
                        id_vaga=link, titulo=titulo, empresa=nome_empresa, 
                        localizacao="Remoto", descricao=texto_cartao
                    )
                    vagas_coletadas.append(vaga_formatada)
                except Exception:
                    continue

            botao_proximo = self.pagina.locator('button[aria-label*="róxima"], button[aria-label*="next"]')
            if botao_proximo.count() > 0 and botao_proximo.is_enabled():
                botao_proximo.click()
                pagina_atual += 1
                self.pagina.wait_for_load_state('networkidle')
            else:
                break
                
        return vagas_coletadas

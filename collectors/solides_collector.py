import time
import logging
from typing import List, Dict, Any
from urllib.parse import quote
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

class SolidesCollector:
    def __init__(self):
        self.playwright = None
        self.navegador = None
        self.contexto = None
        self.pagina = None
        self.url_base = "https://vagas.solides.com.br/vagas?q="

    def iniciar_navegador(self):
        self.playwright = sync_playwright().start()
        # Headless True para evitar dor de cabeça em background
        self.navegador = self.playwright.chromium.launch(headless=True)
        self.contexto = self.navegador.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.pagina = self.contexto.new_page()

    def fechar_navegador(self):
        if self.contexto: self.contexto.close()
        if self.navegador: self.navegador.close()
        if self.playwright: self.playwright.stop()

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
        url_busca = f"{self.url_base}{termo_url}"
        
        termos_proibidos = ["afirmativa", "exclusiva para pcd", "exclusivo pcd", "exclusiva pcd", "exclusiva", "exclusivo", "presencial", "híbrido", "hibrido", "candidaturas encerradas", "inscrições encerradas", "inscricoes encerradas", "clt", "c.l.t", "c.l.t."]
        
        logger.info(f"🌍 Navegando no Sólides: {url_busca}")
        try:
            self.pagina.goto(url_busca, timeout=30000)
            time.sleep(5)
            
            # Scroll para carregar vagas
            for _ in range(4):
                self.pagina.mouse.wheel(0, 1500)
                time.sleep(2)
                
            # Buscar cartões de vagas inteiros (para pegar badges como "Presencial")
            cartoes = self.pagina.locator("li").all()
            links_processados = set()
            
            for cartao in cartoes:
                try:
                    # Encontra o link dentro do cartão
                    link_el = cartao.locator("a[href*='/vaga/'], a[href*='solides.jobs/vacancies']").first
                    if not link_el.is_visible():
                        continue
                        
                    href = link_el.get_attribute("href")
                    if not href or href in links_processados:
                        continue
                        
                    links_processados.add(href)
                    
                    # Pega o texto do CARTÃO INTEIRO (para pegar as badges azuis de 'Presencial' etc)
                    texto_completo = cartao.inner_text().lower()
                    if not texto_completo:
                        continue
                        
                    # Filtragem Negativa (Proibidos)
                    if any(termo in texto_completo for termo in termos_proibidos):
                        continue
                        
                    linhas = texto_completo.split('\n')
                    linhas = [l.strip() for l in linhas if l.strip()]
                    
                    if not linhas:
                        continue
                        
                    # Heurística para Título e Empresa
                    titulo = linhas[0].title()
                    empresa = linhas[1].title() if len(linhas) > 1 else "Sólides"
                    
                    # FILTRO DE SANIDADE: O título deve ter alguma relação com a nossa busca!
                    termo_busca_lower = termo_busca.lower()
                    palavras_chave_busca = [p for p in termo_busca_lower.split() if len(p) > 2]
                    titulo_lower = titulo.lower()
                    
                    tem_relacao = any(palavra in titulo_lower for palavra in palavras_chave_busca)
                    # Adiciona garantia extra para termos de TI em geral caso a busca seja vaga
                    termos_ti = ["analista", "suporte", "desenvolvedor", "python", "dados", "infraestrutura", "rpa", "helpdesk", "sistemas"]
                    tem_relacao_ti = any(t in titulo_lower for t in termos_ti)
                    
                    if not (tem_relacao or tem_relacao_ti):
                        continue # Pula vagas bizarras tipo "Assistente de Sala"
                    
                    vagas_coletadas.append(self.formatar_vaga(
                        id_vaga=href if href.startswith("http") else f"https://vagas.solides.com.br{href}",
                        titulo=titulo,
                        empresa=empresa,
                        localizacao="Remoto",
                        descricao=texto_completo
                    ))
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Erro ao raspar Sólides: {e}")
            
        return vagas_coletadas

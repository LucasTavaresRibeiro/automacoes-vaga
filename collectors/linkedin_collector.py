import time
import logging
import os
from typing import List, Dict, Any
from urllib.parse import quote
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

class LinkedInCollector:
    def __init__(self):
        self.playwright = None
        self.navegador = None
        self.contexto = None
        self.pagina = None

    def iniciar_navegador(self):
        self.playwright = sync_playwright().start()
        # Para LinkedIn, rodar em modo não-headless é MANDATÓRIO para evitar bloqueios severos no início
        self.navegador = self.playwright.chromium.launch(headless=False)
        self.contexto = self.navegador.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.pagina = self.contexto.new_page()

    def fechar_navegador(self):
        if self.contexto: self.contexto.close()
        if self.navegador: self.navegador.close()
        if self.playwright: self.playwright.stop()

    def login(self):
        email = os.getenv("LINKEDIN_EMAIL")
        senha = os.getenv("LINKEDIN_SENHA")
        if not email or not senha:
            logger.warning("⚠️ Credenciais LINKEDIN_EMAIL e LINKEDIN_SENHA não encontradas no .env. O robô tentará coletar em modo visitante (mais limitado).")
            return
        
        logger.info("🔑 Realizando login no LinkedIn...")
        self.pagina.goto("https://www.linkedin.com/login")
        
        try:
            # Tenta preencher no padrão /login
            self.pagina.wait_for_selector("#username", timeout=15000)
            self.pagina.fill("#username", email)
            self.pagina.fill("#password", senha)
            self.pagina.click("button[type='submit']")
            
            # Aguarda o redirecionamento
            self.pagina.wait_for_load_state("networkidle")
            time.sleep(5)
            
            if "checkpoint" in self.pagina.url or "challenge" in self.pagina.url:
                logger.warning("🚨 O LinkedIn pediu verificação de segurança (Captcha/Código). Como a janela está aberta, resolva rapidamente!")
                # Dá um tempo pro usuário resolver o captcha visualmente
                time.sleep(25)
        except Exception as e:
            logger.error("Falha ao tentar logar no LinkedIn. O site pode ter bloqueado a requisição: %s", e)
            raise Exception("Bloqueio no login do LinkedIn")

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
        
        # Filtros de busca: location=Brasil, f_WT=2 (Remoto), f_TPR=r2592000 (Últimos 30 dias)
        url_busca = f"https://www.linkedin.com/jobs/search/?keywords={termo_url}&location=Brasil&f_WT=2&f_TPR=r2592000"
        
        termos_proibidos = ["afirmativa", "exclusiva para pcd", "exclusivo pcd", "exclusiva pcd", "exclusiva", "exclusivo", "presencial", "híbrido", "hibrido", "candidaturas encerradas", "inscrições encerradas", "inscricoes encerradas"]
        # LinkedIn geralmente ja filtra remoto, mas garantimos os termos de PJ
        locais_desejados = ["pj", "pessoa jurídica", "pessoa juridica", "remoto", "home office", "noturno", "noturna", "madrugada"]

        logger.info(f"🌍 Navegando no LinkedIn: {url_busca}")
        self.pagina.goto(url_busca)
        time.sleep(5)
        
        # Scroll para carregar vagas (Lazy Loading do LinkedIn)
        for _ in range(4):
            self.pagina.mouse.wheel(0, 3000)
            time.sleep(2)
            
        # O LinkedIn tem seletores diferentes dependendo se você está logado (.job-card-container) ou não (.base-card)
        cartoes = self.pagina.locator(".base-card, .job-card-container, .job-search-card").all()
        
        for cartao in cartoes:
            try:
                texto_cartao = cartao.inner_text().lower()
                
                # Filtro Negativo
                if any(termo in texto_cartao for termo in termos_proibidos):
                    continue
                    
                # Extração
                titulo_el = cartao.locator(".base-search-card__title, .job-card-list__title, .sr-only").first
                empresa_el = cartao.locator(".base-search-card__subtitle, .job-card-container__company-name, .hidden-nested-link").first
                link_el = cartao.locator("a.base-card__full-link, a.job-card-list__title, a.job-card-container__link").first
                
                if titulo_el.count() == 0 or link_el.count() == 0:
                    continue
                    
                titulo = titulo_el.inner_text().strip()
                empresa = empresa_el.inner_text().strip() if empresa_el.count() > 0 else "Não identificada"
                link = link_el.get_attribute("href")
                
                if link:
                    # Remove os rastreadores absurdos da URL do LinkedIn para ficar limpo no banco
                    link = link.split("?")[0]
                else:
                    continue

                vaga_formatada = self.formatar_vaga(
                    id_vaga=link, titulo=titulo, empresa=empresa, 
                    localizacao="Remoto", descricao=texto_cartao
                )
                vagas_coletadas.append(vaga_formatada)
            except Exception as e:
                continue
                
        return vagas_coletadas

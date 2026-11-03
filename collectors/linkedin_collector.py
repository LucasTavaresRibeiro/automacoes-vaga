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

    def iniciar_navegador(self, headless: bool = True):
        self.playwright = sync_playwright().start()
        self.navegador = self.playwright.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        )
        self.contexto = self.navegador.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale="pt-BR",
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
            logger.info("Seguindo no LinkedIn em modo público/visitante (geoId Brasil).")
            return
        
        logger.info("Realizando login no LinkedIn...")
        self.pagina.goto("https://www.linkedin.com/login")
        
        try:
            self.pagina.wait_for_selector("#username", timeout=15000)
            self.pagina.fill("#username", email)
            self.pagina.fill("#password", senha)
            self.pagina.click("button[type='submit']")
            self.pagina.wait_for_load_state("networkidle")
            time.sleep(3)
        except Exception as e:
            logger.warning("Login ignorado no LinkedIn, usando busca publica Brasil: %s", e)

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
        # Adiciona PJ ao termo se não tiver, para focar em vagas PJ no Brasil
        query = f"{termo_busca} PJ" if "pj" not in termo_busca.lower() else termo_busca
        termo_url = quote(query)
        
        # geoId=106057199 = BRASIL (impede que IPs dos EUA no Streamlit Cloud puxem vagas dos EUA!)
        # f_WT=2 = Remoto | f_TPR=r2592000 = Últimos 30 dias
        url_busca = f"https://br.linkedin.com/jobs/search/?keywords={termo_url}&location=Brasil&geoId=106057199&f_WT=2&f_TPR=r2592000"
        
        termos_proibidos = [
            "afirmativa", "exclusiva para pcd", "exclusivo pcd", "exclusiva pcd", 
            "presencial", "híbrido", "hibrido", "candidaturas encerradas", 
            "inscrições encerradas", "inscricoes encerradas", "clt", "c.l.t", "efetivo",
            "united states", "usa", "u.s."
        ]

        logger.info("Navegando no LinkedIn Brasil: %s", url_busca)
        self.pagina.goto(url_busca, wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        
        for _ in range(3):
            self.pagina.mouse.wheel(0, 2500)
            time.sleep(1.5)
            
        cartoes = self.pagina.locator(".base-card, .job-card-container, .job-search-card").all()
        
        for cartao in cartoes:
            try:
                texto_cartao = cartao.inner_text().lower()
                
                if any(termo in texto_cartao for termo in termos_proibidos):
                    continue
                    
                titulo_el = cartao.locator(".base-search-card__title, .job-card-list__title, .sr-only").first
                empresa_el = cartao.locator(".base-search-card__subtitle, .job-card-container__company-name, .hidden-nested-link").first
                local_el = cartao.locator(".job-search-card__location, .job-card-container__metadata-item").first
                link_el = cartao.locator("a.base-card__full-link, a.job-card-list__title, a.job-card-container__link").first
                
                if titulo_el.count() == 0 or link_el.count() == 0:
                    continue
                    
                titulo = titulo_el.inner_text().strip()
                empresa = empresa_el.inner_text().strip() if empresa_el.count() > 0 else "LinkedIn"
                local_txt = local_el.inner_text().strip() if local_el.count() > 0 else "Brasil (Remoto)"
                link = link_el.get_attribute("href")
                
                # Garante que a localização é Brasil
                local_lower = local_txt.lower()
                if any(ext in local_lower for ext in ["united states", "usa", "canada", "europe", "uk", "india"]):
                    continue
                
                if link:
                    link = link.split("?")[0]
                else:
                    continue

                descricao_completa = f"{titulo} PJ | Local: {local_txt} | Remoto | {texto_cartao}"
                vaga_formatada = self.formatar_vaga(
                    id_vaga=link, titulo=titulo, empresa=empresa, 
                    localizacao=f"Remoto ({local_txt})", descricao=descricao_completa
                )
                vagas_coletadas.append(vaga_formatada)
            except Exception:
                continue
                
        return vagas_coletadas

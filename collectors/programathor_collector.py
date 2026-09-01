import requests
from bs4 import BeautifulSoup
import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ProgramaThorCollector:
    def __init__(self):
        self.url_base = "https://programathor.com.br/jobs"

    def iniciar_navegador(self):
        # Como usamos requests, não precisa iniciar Playwright aqui
        pass

    def fechar_navegador(self):
        # Como usamos requests, não precisa fechar
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
        termos_proibidos = ["clt", "c.l.t", "c.l.t.", "presencial", "híbrido", "hibrido"]
        
        # Paginação até 5 páginas ou até não ter mais vagas
        for page in range(1, 6):
            url_busca = f"{self.url_base}?page={page}&search={termo_busca}"
            logger.info(f"🌍 Navegando no ProgramaThor (Página {page}): {url_busca}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            try:
                response = requests.get(url_busca, headers=headers, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                vagas = soup.find_all('div', class_='cell-list')
                
                if not vagas:
                    break # Fim das páginas
                    
                for vaga in vagas:
                    titulo_el = vaga.find('h3', class_='text-gray-dark')
                    empresa_el = vaga.find('span', class_='font-weight-bold')
                    tags_els = vaga.find_all('span', class_='cell-tag')
                    link_el = vaga.find('a', href=True)
                    
                    if titulo_el and link_el:
                        titulo_original = titulo_el.text.strip()
                        titulo = re.sub(r'(Remoto|Híbrido|Presencial)', '', titulo_original, flags=re.IGNORECASE).strip()
                        empresa = empresa_el.text.strip() if empresa_el else "Empresa não informada"
                        habilidades = [tag.text.strip() for tag in tags_els]
                        descricao_completa = f"{titulo_original} | Skills: {', '.join(habilidades)}"
                        
                        # Filtro Anti-CLT / Presencial
                        texto_analise = descricao_completa.lower()
                        if any(termo in texto_analise for termo in termos_proibidos):
                            continue
                            
                        # Link completo
                        href = link_el['href']
                        link_completo = f"https://programathor.com.br{href}" if href.startswith('/') else href
                        
                        vagas_coletadas.append(self.formatar_vaga(
                            id_vaga=link_completo,
                            titulo=titulo,
                            empresa=empresa,
                            localizacao="Remoto",
                            descricao=descricao_completa
                        ))
            except Exception as e:
                logger.error(f"Erro ao acessar ProgramaThor na página {page}: {e}")
                break
                
        return vagas_coletadas

import logging
import requests
from typing import List, Dict, Any
from urllib.parse import quote
from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)

class SolidesCollector(BaseCollector):
    def __init__(self):
        super().__init__()
        self.url_api = "https://vagas.solides.com.br/api/vacancies"

    def iniciar_navegador(self, headless: bool = True):
        # Usa a API JSON oficial da Sólides (muito mais rápida e sem precisar abrir navegador)
        pass

    def fechar_navegador(self):
        pass

    def buscar_vagas(self, termo_busca: str, localizacao: str = "") -> List[Dict[str, Any]]:
        vagas_coletadas = []
        url = f"{self.url_api}?page=1&take=25&jobsType=remoto&title={quote(termo_busca)}"
        logger.info("Consultando API Solides: %s", url)

        try:
            resp = requests.get(url, headers=self.headers, timeout=20)
            if resp.status_code != 200:
                return []

            dados = resp.json()
            itens = dados.get("data") or []

            for item in itens:
                try:
                    if item.get("isDisabled") or item.get("pcdOnly"):
                        continue

                    # Verifica contrato (Exige PJ / Pessoa Jurídica / Cooperado e bloqueia CLT/Efetivo)
                    contratos = [c.get("name", "").lower() for c in (item.get("recruitmentContractType") or [])]
                    str_contratos = " ".join(contratos)
                    desc_html = (item.get("description") or "").lower()
                    titulo_lower = (item.get("title") or "").lower()
                    texto_analise = f"{titulo_lower} {str_contratos} {desc_html}"
                    
                    tem_pj = any(p in texto_analise for p in ["pj", "pessoa jurídica", "pessoa juridica", "cooperado", "cnpj", "prestador"])
                    if not tem_pj:
                        continue
                    if ("clt" in str_contratos or "efetivo" in str_contratos) and "pj" not in str_contratos and "jurídica" not in str_contratos and "juridica" not in str_contratos and "cooperado" not in str_contratos:
                        continue

                    titulo = (item.get("title") or "").strip()
                    if not titulo:
                        continue

                    empresa = (item.get("companyName") or "Sólides").strip()
                    vid = item.get("id")
                    slug = item.get("slug") or "vaga"
                    link = f"https://vagas.solides.com.br/vaga/{vid}/{slug}"

                    desc_html = item.get("description") or ""
                    descricao = f"{titulo} | Contratos: {str_contratos} | Modalidade: {item.get('jobType', 'remoto')} | {desc_html}"

                    vagas_coletadas.append(self.formatar_vaga(
                        id_vaga=link,
                        titulo=titulo,
                        empresa=empresa,
                        localizacao="Remoto",
                        descricao=descricao
                    ))
                except Exception:
                    continue

        except Exception as e:
            logger.error("Erro ao consultar API Solides: %s", e)

        return vagas_coletadas

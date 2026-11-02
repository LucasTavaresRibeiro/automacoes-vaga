from abc import ABC, abstractmethod
from typing import List, Dict
from playwright.sync_api import sync_playwright

class BaseCollector(ABC):
    """
    Classe base (molde) para todos os coletores de vagas.
    O uso do ABC (Abstract Base Class) obriga que qualquer coletor
    específico (ex: LinkedinCollector) implemente os métodos abaixo.
    """
    
    def __init__(self):
        # Aqui podemos configurar headers padrão para fingir que somos um navegador real
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.playwright = None
        self.navegador = None
        self.contexto = None
        self.pagina = None

    def iniciar_navegador(self, headless: bool = True):
        """Inicializa o navegador Playwright em modo headless (compatível com Streamlit Cloud)."""
        self.playwright = sync_playwright().start()
        self.navegador = self.playwright.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        )
        self.contexto = self.navegador.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=self.headers["User-Agent"]
        )
        self.pagina = self.contexto.new_page()

    def fechar_navegador(self):
        """Encerra o navegador ao final de todas as coletas."""
        if self.contexto:
            self.contexto.close()
        if self.navegador:
            self.navegador.close()
        if self.playwright:
            self.playwright.stop()

    @abstractmethod
    def buscar_vagas(self, termo_busca: str, localizacao: str = "") -> List[Dict]:
        """
        Método obrigatório.
        Deve buscar as vagas e retornar uma lista de dicionários contendo
        as chaves padrão que nosso banco de dados espera.
        """
        pass

    def formatar_vaga(self, id_vaga, titulo, empresa, localizacao, descricao) -> Dict:
        """
        Método utilitário para garantir que todos os coletores devolvam
        os dados exatamente com as chaves que o 'db_manager.py' espera.
        """
        return {
            "ID_Vaga": id_vaga,
            "Titulo": titulo,
            "Empresa": empresa,
            "Localizacao": localizacao,
            "Descricao": descricao
            # Status, Score_IA e Data_Coleta são preenchidos automaticamente depois.
        }

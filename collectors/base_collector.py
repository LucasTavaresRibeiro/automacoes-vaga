from abc import ABC, abstractmethod
from typing import List, Dict

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

    @abstractmethod
    def buscar_vagas(self, termo_busca: str, localizacao: str) -> List[Dict]:
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

        
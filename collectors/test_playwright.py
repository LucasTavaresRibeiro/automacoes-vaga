import pytest
from unittest.mock import MagicMock
from typing import List, Dict, Any, Generator
from collectors.gupy_collector import GupyCollector

@pytest.fixture
def gupy_collector() -> Generator[GupyCollector, None, None]:
    """Fixture do pytest que instacia o GupyCollector, cuidando do setup e teardown do navegador."""
    collector = GupyCollector()
    collector.iniciar_navegador()
    yield collector
    collector.fechar_navegador()

def test_inicializacao_gupy_collector(gupy_collector: GupyCollector) -> None:
    """Valida se a classe é instanciada e se os objetos de sessão do Playwright foram criados."""
    assert gupy_collector is not None
    assert gupy_collector.playwright is not None
    assert gupy_collector.navegador is not None
    assert gupy_collector.pagina is not None

def test_buscar_vagas_contrato_tipo_retorno(gupy_collector: GupyCollector) -> None:
    """Teste de contrato que garante que o retorno de buscar_vagas é uma lista em conformidade com o tipo List[Dict[str, Any]]."""
    # Usando Mock para evitar realizar uma chamada real à rede e manter os testes determinísticos e rápidos
    gupy_collector.pagina = MagicMock()
    gupy_collector.pagina.goto = MagicMock()
    gupy_collector.pagina.wait_for_load_state = MagicMock()
    
    # Mock do localizador de botões para evitar loops infinitos de paginação
    mock_locator_botao = MagicMock()
    mock_locator_botao.count.return_value = 0
    gupy_collector.pagina.locator.return_value = mock_locator_botao

    # Executa a busca
    vagas: List[Dict[str, Any]] = gupy_collector.buscar_vagas(termo_busca="Teste", localizacao="Rio de Janeiro")
    
    # Asserções de contrato
    assert isinstance(vagas, list)
    if len(vagas) > 0:
        for vaga in vagas:
            assert isinstance(vaga, dict)
            assert "id_vaga" in vaga
            assert "Titulo" in vaga
            assert "Empresa" in vaga
            assert "Localizacao" in vaga
            assert "Descricao" in vaga


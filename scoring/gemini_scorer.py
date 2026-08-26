import os
import json
import logging
from typing import TypedDict
from google import genai
from google.genai import types
from google.genai.errors import APIError

logger = logging.getLogger(__name__)

class ScoreResult(TypedDict):
    score: int
    justificativa: str

class GeminiScorer:
    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("⚠️ ALERTA: A variável GEMINI_API_KEY não foi encontrada no ambiente.")
        
        self.client = genai.Client()
        self.modelo_nome: str = 'gemini-2.5-flash'
        
        # Otimização de prompt (redução de tokens, aumento do determinismo e pouca conversa)
        self.contexto_lucas: str = """Você é um validador de ATS extremamente técnico e rigoroso. Avalie a aderência de vagas ao perfil do candidato Lucas.

PERFIL DO CANDIDATO E REGRAS RÍGIDAS:
- Candidato: Lucas Ribeiro, Especialista em Automação, Analista de Sustentação Senior (Evertec), e Desenvolvedor RPA.
- Regime Obrigatório: SOMENTE PJ. Vagas CLT devem ser sumariamente negadas e receber nota < 20.
- Áreas e Níveis:
  1. Infraestrutura, HelpDesk, Suporte, Sustentação: de Júnior a Sênior. Aceita todos os horários (incluindo noturno e 12x36).
  2. DEV RPA: até Pleno, com foco em UiPath, Low-Code e Python Júnior.
  3. Analista de Dados: Nível Júnior.
- Habilidades Principais: UiPath, Python (Selenium, Pandas), Power Platform (Power Automate, Power Apps), SQL, PowerShell, AWS, Linux, Windows Server, Grafana, Kibana.
- Restrição crítica: Se a vaga for explicitamente CLT ou não se encaixar em nenhuma das áreas acima, dar nota < 40.

REGRAS DE PONTUAÇÃO (0-100):
- [90-100]: Match ideal. Vaga PJ, numa das áreas desejadas (Infra/Suporte/Sustentação, RPA até Pleno, ou Dados Jr) com stack aderente.
- [70-89]: Match muito bom. Vaga PJ aderente mas sem mencionar a stack exata ou com requisitos levemente fora.
- [40-69]: Match parcial. Vaga híbrida ou sem clareza de contratação, ou exigindo experiência superior ao desejado na área.
- [0-39]: Baixa aderência. Vaga explicitamente CLT, ou em áreas não relacionadas, ou exigindo stack completamente diferente.

JSON SCHEMA:
{
  "score": integer,
  "justificativa": "Texto conciso focado na aderência técnica e regime de contratação (PJ), falando diretamente ao Lucas."
}

Exemplo 1 (Sucesso):
Input: {"titulo": "Analista de Sustentação Sênior (Noturno)", "empresa": "TechCorp", "descricao": "Contratação PJ. Necessário Linux e PowerShell. Escala 12x36."}
Output: {"score": 95, "justificativa": "Lucas, excelente match. Vaga PJ para Sustentação Sênior no horário 12x36 com tecnologias que você domina."}

Exemplo 2 (Penalidade):
Input: {"titulo": "Analista de Dados Pleno", "empresa": "Data S/A", "descricao": "Vaga CLT. Necessário Python e SQL."}
Output: {"score": 10, "justificativa": "Lucas, a vaga é CLT e busca nível Pleno para Dados, fora do seu foco que é PJ e Júnior nesta área."}

REQUISITO DE SAÍDA: Retorne APENAS o JSON especificado, sem markdown ou outras tags."""

    def avaliar_vaga(self, titulo: str, empresa: str, descricao: str) -> ScoreResult:
        """Envia os dados da vaga para o Gemini e retorna o score formatado."""
        prompt_usuario = json.dumps({
            "titulo": titulo,
            "empresa": empresa,
            "descricao": descricao
        }, ensure_ascii=False)
        
        logger.info("Analisando vaga com o novo SDK do Gemini: %s (%s)...", titulo, empresa)
        
        try:
            resposta = self.client.models.generate_content(
                model=self.modelo_nome,
                contents=prompt_usuario,
                config=types.GenerateContentConfig(
                    system_instruction=self.contexto_lucas,
                    response_mime_type="application/json",
                    temperature=0.0
                )
            )
            
            if not resposta or not resposta.text:
                raise ValueError("Resposta da API do Gemini retornou vazia ou nula.")
                
            dados_estruturados: ScoreResult = json.loads(resposta.text)
            return dados_estruturados
            
        except APIError as e:
            logger.error("Erro específico da API do Gemini: %s", e)
            return {
                "score": 0, 
                "justificativa": "Falha na comunicação com o serviço de inteligência artificial (Gemini)."
            }
        except json.JSONDecodeError as e:
            logger.error("Erro ao decodificar JSON retornado pelo Gemini: %s", e)
            return {
                "score": 0, 
                "justificativa": "A inteligência artificial retornou um formato de dados inválido."
            }
        except Exception as e:
            logger.error("Erro inesperado ao avaliar vaga com o Gemini: %s", e)
            return {
                "score": 0, 
                "justificativa": f"Ocorreu um erro inesperado no processamento da vaga: {e}"
            }

# ==========================================
# BLOCO DE TESTE ISOLADO
# ==========================================
if __name__ == "__main__":
    vaga_teste = {
        "titulo": "Analista de Dados Júnior",
        "empresa": "Tech DataCorp",
        "descricao": "Buscamos um analista para criar dashboards no Power BI e automatizar rotinas de extração de dados com Python e SQL. Modelo remoto. Desejável conhecimento em APIs."
    }
    
    scorer = GeminiScorer()
    resultado = scorer.avaliar_vaga(
        titulo=vaga_teste["titulo"],
        empresa=vaga_teste["empresa"],
        descricao=vaga_teste["descricao"]
    )
    
    print("\n--- 🎯 RESULTADO DA IA ---")
    print(f"Score: {resultado.get('score')}/100")
    print(f"Justificativa: {resultado.get('justificativa')}")

    
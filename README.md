# 🚀 Job Hunter AI - Automação e Scoring de Vagas

Um orquestrador inteligente focado em automação de web scraping, integração de dados e análise de inteligência artificial (LLM) para encontrar, classificar e salvar vagas de emprego perfeitamente aderentes a um perfil profissional específico.

## 🧠 Visão Geral da Arquitetura

O sistema foi construído utilizando os princípios de **Clean Code**, **Injeção de Dependências** e **Defesa em Profundidade (Defense in Depth)**. Ele se divide em três camadas principais:

1. **Camada de Coleta (Playwright):** Utiliza interceptação de rede (Network Interception) para contornar o carregamento lento de Single Page Applications (SPAs) como a Gupy, capturando o JSON direto do backend para maior resiliência.
2. **Camada de Inteligência (Google Gemini 2.5 Flash):** Aplica técnicas avançadas de Prompt Engineering (Few-Shot Prompting, Compressão de Tokens e Temperature 0.0) para avaliar as vagas de forma determinística e retornar um JSON estrito com o score de aderência.
3. **Camada de Persistência (Google Sheets API):** Gerencia a inserção e atualização em lote (batch update) das vagas analisadas, contando com tratamentos de queda de rede e validação de duplicidade.

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3
* **Automação & Scraping:** Playwright
* **Inteligência Artificial:** Google GenAI SDK (Gemini 2.5 Flash)
* **Banco de Dados / Nuvem:** Google Sheets API, Google Cloud IAM (Service Accounts)
* **Boas Práticas:** Type Hinting (PEP 484), Logging profissional, `pytest` para testes de contrato.

## ⚙️ Pré-requisitos e Instalação

Para rodar este projeto localmente, você precisará configurar chaves de acesso do Google Cloud e do Google AI Studio.

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/seu-usuario/job-hunter-ai.git](https://github.com/seu-usuario/job-hunter-ai.git)
   cd job-hunter-ai

   1 - Crie e ative o ambiente virtual
   python -m venv venv

# No Windows:
##venv\Scripts\activate - Retire '#' para testar.

Instale as dependências e os navegadores do Playwright:
pip install -r requirements.txt
playwright install

Configuração de Variáveis de Ambiente:
Crie um arquivo .env na raiz do projeto e adicione sua chave da IA:
GEMINI_API_KEY=sua_chave_aqui

Coloque o arquivo de credenciais do Google Cloud Service Account em config/google_credentials.json.

(Nota: Estes arquivos estão no .gitignore por segurança e não acompanham o repositório).

Para rodar o fluxo completo (Coleta -> Avaliação IA -> Banco de Dados):
python CPTMR.py

Tratamento de Erros e Resiliência:
Scraper: Retries automáticos e esperas explícitas substituindo time.sleep.

IA: Bloco try/except específico para lidar com falhas de JSON, timeouts ou indisponibilidade da API do Google, garantindo que o loop de vagas nunca seja interrompido abruptamente.

Database: Proteção de conexão com padrão Singleton (Factory Method) para evitar sobrecarga na API do Google Sheets.

Desenvolvido por Thiago Marques Ramalho como projeto de portfólio para a área de Dados e Automação.

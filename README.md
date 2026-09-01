# 🚀 Job Hunter AI - Automação e Painel de Vagas

Um orquestrador inteligente focado em automação de web scraping e integração de dados para encontrar, filtrar e exibir vagas de emprego perfeitamente aderentes a um perfil profissional específico.

## 🧠 Visão Geral da Arquitetura

O sistema foi construído utilizando os princípios de **Clean Code**, **Injeção de Dependências** e resiliência a falhas de rede. Ele se divide em três camadas principais:

1. **Camada de Coleta (Playwright + BeautifulSoup):** Interage com diversos portais (Gupy, LinkedIn, Sólides, ProgramaThor). Utiliza navegação avançada, controle de exceções e login persistente em navegadores Headless e Headed (para bypassar captchas).
2. **Camada de Filtros & Limpeza:** Aplica regras rigorosas de blacklist (ex: rejeita vagas "CLT", "Presencial") e regras de whitelist (prioriza vagas "PJ" e "Home Office").
3. **Camada de Apresentação (Streamlit + SQLite):** Armazena o histórico em um banco relacional robusto (SQLite) e exibe os resultados em um Dashboard interativo, permitindo o gerenciamento 1-click das suas candidaturas.

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3
* **Automação & Scraping:** Playwright, Requests, BeautifulSoup4
* **Apresentação:** Streamlit
* **Banco de Dados:** SQLite3 (Migração prevista para PostgreSQL/Supabase)

## ⚙️ Pré-requisitos e Instalação

1. **Clone o repositório:**
   ```bash
   git clone [seu-repo]
   cd automacoes-vaga
   ```

2. **Crie e ative o ambiente virtual:**
   ```bash
   python -m venv venv
   # No Windows:
   venv\Scripts\activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

4. **Configuração de Variáveis de Ambiente:**
   Crie um arquivo `.env` na raiz do projeto contendo suas credenciais (necessárias para o scraper do LinkedIn):
   ```env
   LINKEDIN_EMAIL=seu_email
   LINKEDIN_SENHA=sua_senha
   ```

## 🚀 Como Executar

Para ligar o Painel de Controle e visualizar suas vagas (o próprio painel possui um botão para acionar o robô de raspagem):
```bash
streamlit run app.py
```

Para rodar o fluxo de coleta manualmente em background (Coleta Gupy -> LinkedIn -> Sólides -> ProgramaThor):
```bash
python CPTMR.py
```

---
*Projeto inspirado nas ideias de arquitetura inicial de Thiago Marques Ramalho, porém completamente refatorado, modernizado e expandido para atender aos mais altos padrões de automação multiprotocolo.*

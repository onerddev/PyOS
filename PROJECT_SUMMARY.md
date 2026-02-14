"""
Sumário da Estrutura do Projeto PyOS-Agent
===========================================

Arquivo gerado automaticamente. Mostra a estrutura completa e componentes principais.
"""

PROJECT_STRUCTURE = """
PyOS-Agent/
│
├── pyproject.toml                 # Configuração Poetry com todas as dependências
├── poetry.lock                    # Lock file (gerado após poetry install)
├── README.md                      # Documentação do projeto
├── LICENSE                        # Licença MIT
├── .gitignore                     # Padrões de ignoração Git
├── .env.example                   # Exemplo de configuração de ambiente
│
├── src/
│   └── pyos/                      # Pacote principal
│       ├── __init__.py            # Exports públicos
│       ├── example_init.py        # Exemplo de uso do framework
│       │
│       ├── core/                  # Módulo de Orquestração e Segurança
│       │   ├── __init__.py
│       │   ├── security.py        # SecurityShield com AllowList e decoradores
│       │   └── config.py          # Settings com Pydantic BaseSettings
│       │
│       ├── tools/                 # Módulo de Ferramentas (Terminal, Browser, Editor)
│       │   └── __init__.py
│       │
│       └── api/                   # Módulo de API FastAPI
│           └── __init__.py
│
├── tests/
│   ├── __init__.py
│   └── test_security.py           # Testes para SecurityShield
│
└── docs/                          # Documentação adicional
"""

DEPENDENCIES = """
Dependências Principais
=======================

Produção:
  • fastapi             - Framework web assíncrono
  • pydantic-ai         - IA com Pydantic
  • loguru              - Logging estruturado
  • typer               - CLI framework
  • python-dotenv       - Carregamento de .env
  • mss                 - Captura de tela
  • pyautogui           - Automação de mouse/teclado
  • pydantic            - Validação de dados
  • uvicorn             - Servidor ASGI

Desenvolvimento:
  • pytest              - Framework de testes
  • pytest-cov          - Cobertura de testes
  • black               - Formatter de código
  • ruff                - Linter rápido
  • mypy                - Type checking
  • ipython             - Shell interativo
"""

MODULES = """
Módulos Implementados
=====================

1. core/security.py
   └─ SecurityShield
      ├─ AllowList de comandos
      ├─ AllowList de caminhos
      ├─ Padrões bloqueados
      ├─ Métodos de validação
      ├─ Decoradores @require_command_permission
      ├─ Decoradores @require_path_permission
      └─ Relatório de segurança

2. core/config.py
   └─ Settings (BaseSettings)
      ├─ Configurações da aplicação
      ├─ Configurações da API
      ├─ Configurações de execução
      ├─ Carregamento de .env
      └─ Type hints completos

3. example_init.py
   └─ initialize_agent()
      ├─ Carrega configurações
      ├─ Inicializa SecurityShield
      ├─ Configura caminhos permitidos
      └─ Adiciona comandos base
"""

FEATURES = """
Características Implementadas
=============================

✅ Sistema de Segurança Robusto
   • AllowList para comandos e caminhos
   • Padrões bloqueados regex
   • Decoradores para validação automática
   • Logging de violações de segurança

✅ Configuração via Pydantic
   • Type hints completos
   • Validação automática
   • Carregamento de .env
   • Padrões sensatos

✅ Code Quality
   • Type hints em 100% do código
   • Docstrings Google Format em português
   • Tests unitários com pytest
   • Black, Ruff, MyPy configurados

✅ Documentação Completa
   • README.md com instruções
   • Docstrings detalhadas
   • Exemplos de uso
   • Arquivo de exemplo de inicialização

✅ Estrutura Profissional
   • Organização modular
   • Padrão Poetry
   • .gitignore completo
   • Licença MIT
"""

QUICK_START = """
Começando Rápido
================

1. Instalar dependências:
   poetry install

2. Ativar ambiente:
   poetry shell

3. Configurar .env (copiar .env.example):
   cp .env.example .env

4. Usar SecurityShield:
   from pyos.core import SecurityShield
   
   shield = SecurityShield()
   shield.add_allowed_command("ls")
   shield.validate_command("ls")  # OK
   shield.validate_command("rm")  # SecurityViolationError

5. Usar Settings:
   from pyos.core import get_settings
   
   settings = get_settings()
   print(settings.get_api_url())

6. Rodar exemplo:
   python -m pyos.example_init

7. Executar testes:
   poetry run pytest tests/ -v

8. Verificar tipos:
   poetry run mypy src/

9. Formatar código:
   poetry run black src/ tests/
"""

if __name__ == "__main__":
    print(PROJECT_STRUCTURE)
    print("\n" + DEPENDENCIES)
    print("\n" + MODULES)
    print("\n" + FEATURES)
    print("\n" + QUICK_START)

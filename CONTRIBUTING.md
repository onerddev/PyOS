# 🤝 Contribuindo para PyOS-Agent

Obrigado por considerar contribuir para o PyOS-Agent! Este documento fornece diretrizes e instruções para contribuir efetivamente ao projeto.

## 📋 Índice

- [Código de Conduta](#código-de-conduta)
- [Como Começar](#como-começar)
- [Reportar Bugs](#reportar-bugs)
- [Sugerir Melhorias](#sugerir-melhorias)
- [Guia de Desenvolvimento](#guia-de-desenvolvimento)
- [Submeter Pull Requests](#submeter-pull-requests)
- [Estrutura de Plugins](#estrutura-de-plugins)

---

## Código de Conduta

Veja [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) para nossas normas comunitárias. Resumem-se a:

-  Ser respeitoso com todos
-  Aceitar críticas construtivas
-  Focar no que é melhor para a comunidade

---

## Como Começar

### Pré-requisitos

- Python 3.10+
- Poetry 1.5+
- Git

### Setup do Ambiente

```bash
# 1. Fork repository
git clone https://github.com/seu-usuario/pyos-agent.git
cd pyos-agent

# 2. Setup automático (recomendado)
bash setup_dev.sh

# 3. Ou manual
poetry install
poetry run pre-commit install

# 4. Verificar
poetry run pytest tests/ -v
```

### Estrutura de Branches

```
main                    # Production-ready
├─ develop             # Desenvolvimento ativo
│  ├─ feature/xyz      # Nova feature
│  ├─ fix/xyz          # Bug fix
│  └─ docs/xyz         # Documentação
```

---

## Reportar Bugs

### Antes de Reportar

1.  Checar [Issues existentes](issues)
2.  Verificar [Troubleshooting](README.md#troubleshooting)
3.  Rodar testes: `poetry run pytest tests/`

### Como Reportar

Criar issue com template:

```markdown
**Descrição do Bug**
[Breve descrição]

**Passos para Reproduzir**
1. ...
2. ...
3. ...

**Comportamento Esperado**
[O que deveria acontecer]

**Comportamento Atual**
[O que na verdade aconteceu]

**Logs**
[cole os logs relevantes]

**Ambiente**
- OS: Windows/Linux/macOS
- Python: 3.10/3.11/3.12
- PyOS-Agent: v0.1.0
```

---

## Sugerir Melhorias

### Template de Sugestão

```markdown
**Descrição da Melhoria**
[Qual é a ideia?]

**Motivação**
[Por que seria útil?]

**Exemplo de Uso**
[Como seria usado?]

**Alternativas Consideradas**
[Outras abordagens?]
```

---

## Guia de Desenvolvimento

### Padrões de Código

#### 1. **Importações Obrigatórias**

```python
from __future__ import annotations  # Para type hints

import asyncio
from typing import Any, Optional
from dataclasses import dataclass

from loguru import logger
```

#### 2. **Type Hints Completos (100%)**

```python
# Bom
async def execute(command: str, timeout: int = 30) -> ToolResult:
    """Execute command with timeout."""
    pass

# ❌ Ruim
async def execute(command, timeout=30):
    pass
```

#### 3. **Docstrings em Português (Google Style)**

```python
def validate_command(self, command: str) -> bool:
    """
    Valida se comando está na AllowList.
    
    Args:
        command: Comando a validar.
        
    Returns:
        True se permitido, False caso contrário.
        
    Raises:
        SecurityViolationError: Se comando bloqueado.
        
    Example:
        >>> shield.validate_command("ls")
        True
    """
    pass
```

#### 4. **Logging Estruturado**

```python
from loguru import logger

# Níveis apropriados
logger.debug("Variável: var_name")           # DEBUG
logger.info("Iniciando processo")            # INFO
logger.warning(f"Comando bloqueado: {cmd}")  # WARNING
logger.error(f"Erro crítico: {exc}")         # ERROR
```

#### 5. **Validação ANTES de Ação**

```python
# ✅ Correto (Fail Fast)
async def delete_file(path: str) -> None:
    shield.validate_path(path)  # Valida ANTES
    os.remove(path)

# ❌ Errado (Validação DEPOIS)
async def delete_file(path: str) -> None:
    try:
        os.remove(path)
        shield.validate_path(path)  # Muito tarde!
    except Exception:
        pass
```

### Comandos Úteis

```bash
# Verificar código
poetry run ruff check src/ tests/          # Linting
poetry run black src/ tests/               # Formatting
poetry run mypy src/                       # Type checking

# Testes
poetry run pytest tests/ -v                # Todos
poetry run pytest tests/test_security_attacks.py -v  # Apenas segurança
poetry run pytest --cov=src/pyos --cov-report=html  # Com cobertura

# Pre-commit hooks (automático)
poetry run pre-commit run --all-files

# Documentação
poetry run sphinx-build docs/ docs/_build  # Se aplicável
```

---

## Submeter Pull Requests

### Checklist Pré-Submissão

- [ ] Branch criado a partir de `develop`
- [ ] Código segue padrões do projeto
- [ ] Testes escritos para nova funcionalidade
- [ ] Todos os testes passam: `poetry run pytest tests/ -v`
- [ ] Linting passa: `poetry run ruff check src/`
- [ ] Type checking passa: `poetry run mypy src/`
- [ ] Docstrings adicionadas (português, Google format)
- [ ] README atualizado (se necessário)
- [ ] Commit messages clara e descritiva

### Template de PR

```markdown
## Descrição
[Breve descrição da mudança]

## Tipo de Mudança
- [ ] Bug fix (non-breaking)
- [ ] Feature (non-breaking)
- [ ] Breaking change
- [ ] Documentação

## Testing
- [ ] Unit tests adicionados
- [ ] Testes existentes ainda passam
- [ ] Coverage: ____%

## Checklist
- [ ] Code review próprio realizado
- [ ] Comentários adicionados (tricky logic)
- [ ] README/docs atualizados
- [ ] Sem warnings new

## Links
Fixes #[issue number]
Relacionado a #[issue number]
```

### Processo de Review

1. Submeter PR contra `develop`
2. Mínimo 1 review antes de merge
3. CI deve passar (testes, linting, type checking)
4. Squash ao mergir (opcional)

---

## Estrutura de Plugins

### Criar um Novo Plugin

```python
# src/pyos/plugins/meu_plugin.py
from pyos.plugins import BaseTool, ToolResult

class MeuPlugin(BaseTool):
    """Plugin para fazer algo útil."""
    
    @property
    def name(self) -> str:
        """Identificador único da ferramenta."""
        return "meu_plugin"
    
    @property
    def description(self) -> str:
        """Descrição do que a ferramenta faz."""
        return "Realiza análise de conteúdo"
    
    @property
    def category(self) -> str:
        """Categoria (analysis, conversion, execution, etc)."""
        return "analysis"
    
    @property
    def version(self) -> str:
        """Versão do plugin."""
        return "0.1.0"
    
    @property
    def requires_approval(self) -> bool:
        """Se ação crítica (delete, format, install)."""
        return False
    
    async def validate(self, *args, **kwargs) -> tuple[bool, str]:
        """Validar inputs (opcional)."""
        return True, ""
    
    async def execute(self, data: str) -> ToolResult:
        """Executar a ferramenta."""
        try:
            result = self._analyze(data)
            return ToolResult(
                success=True,
                output=result,
                execution_time=0.125,
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e),
            )
    
    def _analyze(self, data: str) -> str:
        """Lógica interna."""
        return f"Analisado: {data}"
```

### PluginLoader Automático

```python
# Não precisa registrar manualmente!
# PluginLoader descobrirá em: src/pyos/plugins/meu_plugin.py

from pyos.core.loader import PluginLoader

loader = PluginLoader()
await loader.load_all()

# Agora seu plugin está disponível
tool = loader.get_tool("meu_plugin")
```

### Padrões de Plugin

**Plugin de Leitura (Non-Destructive):**
```python
class AnalysisPlugin(BaseTool):
    requires_approval = False  # Seguro, apenas lê
    
    async def execute(self, path: str) -> ToolResult:
        # Apenas lê, não modifica
        content = read_file(path)
        analysis = analyze(content)
        return ToolResult(success=True, output=analysis)
```

**Plugin de Modificação (Crítico):**
```python
class DeletePlugin(BaseTool):
    requires_approval = True  # Requer aprovação!
    dangerous_patterns = ["rm -rf", "mkfs"]  # Padrões perigosos
    
    async def execute(self, path: str) -> ToolResult:
        # SecurityShield + ApprovalManager cuidarão
        shield.validate_path(path)
        os.remove(path)
        return ToolResult(success=True, output="Removido")
```

---

## Dúvidas?

- 📚 [README completo](README.md)

- 📧 Contato: emanuelfelipe.120309@gmail.com

---

**Obrigado por contribuir!** 

Toda contribuição, pequena ou grande, é apreciada e ajuda a fazer PyOS-Agent melhor.



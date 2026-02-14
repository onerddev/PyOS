# Contribuindo para PyOS-Agent

Que legal que você quer contribuir! Este é o guia para fazer isso de forma direita.

## No que Começar

Você vai precisar:
- Python 3.10+
- Poetry 1.5+
- Git

Setup do ambiente é moleza:

```bash
# 1. Fork o repositório
git clone https://github.com/seu-usuario/PyOS.git
cd PyOS

# 2. Tudo automático (melhor)
bash setup_dev.sh

# 3. Ou manual
poetry install
poetry run pre-commit install

# 4. Testa
poetry run pytest tests/ -v
```

Setup de branches:
```
main                    # Código estável
├─ develop             # Desenvolvimento
│  ├─ feature/xyz      # Nova feature
│  ├─ fix/xyz          # Correção
│  └─ docs/xyz         # Documentação
```

---

## Reportar um Bug

Antes de tudo:
1. Verifica se não tem outra issue igual
2. Roda os testes para descartar problema de setup

Template:
```
Título: [Bug] Descrição breve

Descrição:
O que exatamente deu errado?

Como reproduzir:
1. Passo 1
2. Passo 2
3. Passo 3

Deveria fazer:
O que era para acontecer?

Na verdade acontece:
O que de fato está acontecendo?

Logs/Erros:
[Cole aqui os logs e erros]

Ambiente:
- SO: Windows/Linux/macOS
- Python: 3.10 ou 3.11?
- PyOS: v2.0
```

---

## Sugerir uma Melhoria

Template:
```
Título: [Sugestão] Descrição breve

A ideia:
O que você quer adicionar?

Por que?
Qual o benefício?

Exemplo:
Como seria usado?

Outras formas:
Outras maneiras de fazer a mesma coisa?
```

---

## Code Standards

Nesse projeto a gente mantém alguns padrões. Nada pesado, só o básico.

### Importações

Comece assim:
```python
from __future__ import annotations

import asyncio
from typing import Any, Optional
from dataclasses import dataclass

from loguru import logger
```

### Type Hints em 100%

```python
# Certo
async def execute(command: str, timeout: int = 30) -> ToolResult:
    """Executa comando com timeout."""
    pass

# Errado
async def execute(command, timeout=30):
    pass
```

### Docstrings em Português

```python
def validate_command(self, command: str) -> bool:
    """
    Valida se comando está permitido.
    
    Args:
        command: Comando a validar.
        
    Returns:
        True se permitido, False caso contrário.
        
    Raises:
        SecurityViolationError: Se bloqueado.
        
    Exemplo:
        >>> shield.validate_command("ls")
        True
    """
    pass
```

### Logging Correto

```python
from loguru import logger

logger.debug("Variável x = 42")          # Debug
logger.info("Processo iniciado")         # Info
logger.warning(f"Bloqueado: {cmd}")      # Aviso
logger.error(f"Erro: {exc}")             # Erro
```

### Validação ANTES (Fail Fast)

```python
# Certo
async def delete_file(path: str) -> None:
    shield.validate_path(path)  # Valida ANTES
    os.remove(path)

# Errado
async def delete_file(path: str) -> None:
    try:
        os.remove(path)  # Executa ANTES de validar
        shield.validate_path(path)
    except Exception:
        pass
```

### Testando

Escreve teste para tudo novo:

```python
import pytest
from pyos import SemanticMemory, MemoryType

@pytest.mark.asyncio
async def test_memory_store():
    memory = SemanticMemory()
    await memory.store("teste", MemoryType.SUCCESS)
    result = await memory.recall("teste")
    assert len(result) > 0

@pytest.mark.asyncio
async def test_memory_recall():
    memory = SemanticMemory()
    await memory.store("comando python", MemoryType.SUCCESS)
    recall = await memory.recall("python", limit=1)
    assert recall is not None
```

### Checklist Antes de Enviar

- [ ] Type hints em tudo
- [ ] Docstrings criadas
- [ ] Testes escritos
- [ ] Imports organizados (`ruff check`)
- [ ] Código formatado (`black`)
- [ ] Type checking OK (`mypy`)
- [ ] Testes passando

Rodando tudo:
```bash
# Lint
poetry run ruff check .

# Format
poetry run black .

# Type check
poetry run mypy src/

# Testes
poetry run pytest tests/ -v

# Pré-commit (tudo junto)
poetry run pre-commit run --all-files
```

---

## Pull Request

1. Cria branch: `git checkout -b feature/sua-feature`
2. Faz as mudanças
3. Roda testes: `poetry run pytest -v`
4. Commit: `git commit -m "Add sua feature"`
5. Push: `git push origin feature/sua-feature`
6. Abre PR no GitHub

Template para PR:

```
Título: [Tipo] Descrição breve

Tipo de mudança:
- [ ] Correção de bug
- [ ] Nova feature
- [ ] Melhoria
- [ ] Documentação

O que mudou:
Descreve toda a mudança.

Por que:
Qual é o motivo?

Testes:
Quais testes foram criados?

Checklist:
- [ ] Type hints completos
- [ ] Docstrings criadas
- [ ] Testes passando
- [ ] Sem mudanças que quebrem nada de existente
```

---

## Criar um Plugin

Fazer plugin próprio é fácil demais. Aqui tem um exemplo:

```python
# Em src/pyos/plugins/seu_plugin.py

from pyos.plugins import BaseTool, ToolResult
from typing import Any

class MeuAnalyzer(BaseTool):
    @property
    def name(self) -> str:
        return "meu_analyzer"
    
    @property
    def description(self) -> str:
        return "Analisa conteúdo e retorna resultado"
    
    @property
    def category(self) -> str:
        return "analysis"
    
    @property
    def requires_approval(self) -> bool:
        return False
    
    async def execute(self, content: str) -> ToolResult:
        """
        Processa conteúdo.
        
        Args:
            content: Texto a analisar.
            
        Returns:
            Resultado da análise.
        """
        try:
            # Sua lógica aqui
            result = self._analyze(content)
            
            return ToolResult(
                success=True,
                output=result,
                metadata={"source": "meu_analyzer"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    def _analyze(self, content: str) -> dict:
        """Análise interna."""
        return {
            "word_count": len(content.split()),
            "char_count": len(content)
        }
```

Depois de criar, é tudo automático:
1. Salva em `src/pyos/plugins/seu_plugin.py`
2. Herda de `BaseTool`
3. Implementa `execute()` (async)
4. Retorna `ToolResult`
5. O PluginLoader descobre sozinho!

Testando seu plugin:
```python
import asyncio
from src.pyos.core.loader import PluginLoader

async def test():
    loader = PluginLoader()
    await loader.load_all()
    
    seu_plugin = loader.get_tool("meu_analyzer")
    result = await seu_plugin.execute("texto teste")
    
    print(f"Sucesso: {result.success}")
    print(f"Resultado: {result.output}")

asyncio.run(test())
```

---

## Padrões de Plugin

Plugin seguro (sem aprovação):
```python
class AnalysisPlugin(BaseTool):
    requires_approval = False  # Seguro, apenas lê
    
    async def execute(self, path: str) -> ToolResult:
        # Apenas lê, não modifica
        content = read_file(path)
        analysis = analyze(content)
        return ToolResult(success=True, output=analysis)
```

Plugin crítico (precisa aprovação):
```python
class DeletePlugin(BaseTool):
    requires_approval = True  # Requer aprovação do usuário
    dangerous_patterns = ["rm -rf", "mkfs"]
    
    async def execute(self, path: str) -> ToolResult:
        # SecurityShield + ApprovalManager cuidam disso
        shield.validate_path(path)
        os.remove(path)
        return ToolResult(success=True, output="Removido")
```

---

## Código de Conduta

Veja [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) para as regras básicas:

- Ser respeitoso com todo mundo
- Aceitar feedback construtivo
- Pensar no bem coletivo
- Sem assédio, insultos ou preconceito

---

Dúvidas? Abre uma issue ou manda uma mensagem. A galera tá sempre de prontidão pra ajudar!

Valeu por pensar em contribuir. Seja pequeno ou grande, tudo ajuda a fazer esse projeto melhor.

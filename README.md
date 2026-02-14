# PyOS-Agent: Neural Operating System v2.0

Um agente autônomo inteligente que controla seu desktop com aprendizado contínuo.

PyOS-Agent é o primeiro Neural Operating System production-ready com segurança inquebrável, memória semântica vetorial e auto-cura inteligente.

Python 3.10+ | MIT License | Segurança AllowList+AST+Approval | >90% coverage | ChromaDB+Vectors

## O que É

PyOS-Agent v2.0 é um assistente autônomo que sabe fazer de tudo:

- Visão: Captura e analisa telas com compressão 40x
- Memória Semântica: ChromaDB + sentence-transformers (384-dim vectors) que aprendem com o tempo
- Auto-Cura: Retry inteligente com análise de erro até 3 tentativas automaticamente
- Segurança em 3 Camadas: AllowList + AST Analysis + User Approval
- Performance: Menos de 100ms de latência média, totalmente assíncrono, live dashboard

## Como Funciona

### Banco de Memória Vetorial: ChromaDB + Semantic Memory

A gente usa ChromaDB e sentence-transformers para armazenar e recuperar experiências. Quando o agente encontra uma situação nova, ele busca no histórico por situações parecidas e usa essas experiências para tomar decisões melhores.

Arquitetura:

```
┌─────────────────────────────────┐
│   SemanticMemory (Python API)   │
│  - store(content, type, meta)   │
│  - recall(query, limit)         │
│  - learn_from_success/error()   │
└──────────────┬──────────────────┘
               │
        ┌──────────────┐
        │  sentence-   │
        │  transformers│  (all-MiniLM-L6-v2)
        │  384-dim vec │
        └──────────────┘
               │
┌──────────────┼──────────────────┐
│          ChromaDB               │
│  Persistent Vector Store        │
│  - Cosine Similarity Search     │
│  - Local Storage (.pyos/memory)│
│  - Metadata filtering           │
└─────────────────────────────────┘
```

Exemplo de uso:
```python
memory = SemanticMemory(db_path="./.pyos/memory")

# Armazena uma ação bem-sucedida
await memory.store(
    "Executou ls /home com sucesso",
    type=MemoryType.SUCCESS
)

# Busca por ações similares
recalls = await memory.recall(
    "executar comando ls em pasta",
    limit=3
)
# Retorna: [sucesso_similar_1, sucesso_similar_2, sucesso_similar_3]
```

### Auto-Cura com 3 Tiers de Retry

Quando algo dá errado, o agente não desiste. Ele analisa o erro, busca na memória por soluções parecidas, e tenta de novo com correções.

Processo:
```
Tool Fails → Analyze Error
                 │
        "command not found"
                 │
         ├─ Retry 1: python3
         ├─ Retry 2: python3.10
         └─ Retry 3: apt install python3 
                 │
           Success ✓ ou registra erro
```

Exemplo real:
```python
# Falha auto-curada
await memory.learn_from_error(
    "comando python falhou",
    "command not found",
    "execute_command",
    attempted_fixes=["python → python3", "python → python3.10"]
)

# Próxima vez, agente busca: recall("python not found")
# E encontra: "Solução anterior: tentar python3"
```

### Sistema de Plugins: Zero Config, Auto-Discovery

Quer adicionar uma ferramenta nova? Basta criar uma classe que herda de BaseTool em src/pyos/plugins/ que ela é descoberta automaticamente.

```python
# Em src/pyos/plugins/custom_tool.py
class MyAnalyzer(BaseTool):
    @property
    def name(self) -> str:
        return "my_analyzer"
    
    @property
    def description(self) -> str:
        return "Analisa conteúdo custom"
    
    @property
    def category(self) -> str:
        return "analysis"
    
    async def execute(self, data: str) -> ToolResult:
        return ToolResult(success=True, output=analysis)

# PluginLoader descobre automaticamente!
loader = PluginLoader()
await loader.load_all()
# Encontra MyAnalyzer, instantia, registra no orchestrator
# Pronto para usar! Sem config manual!
```

### Análise Estática com AST

Antes de executar qualquer código Python, o agente analisa com AST e bloqueia coisas perigosas:

```python
code = """
import subprocess
subprocess.run("rm -rf /")
"""

validator = PythonASTValidator()
is_safe, violations = validator.validate_python_code(code)
# violations = [
#     "Dangerous import: subprocess.run",
#     "Warning: subprocess dangerous!"
# ]
# is_safe = False
```

### Dashboard em Tempo Real

Tudo que o agente pensa e faz aparece em um dashboard bonito no terminal:

```
┌─ PyOS-Agent │ Iter 5 │ 24 ações │ 28.3s ─┐
│                                            │
│ PENSAMENTO DA IA      │ AÇÃO EXECUTADA    │
│ "o usuário pediu..."  │ Tool: execute_cmd │
│ Raciocínio: ...       │ Status: OK        │
│ Decisão: screenshot   │ [████░░░░░] 45%   │
│                                            │
│ SECURITY STATUS       │ LEMBRANÇA MEMORIA │
│ OK              │ 234 entradas          │
│ Violations: 0         │ 28 recalls         │
│ AST: Ativo            │ Último: "firefox"  │
└────────────────────────────────────────────┘
```

## Instalação Rápida

```bash
git clone https://github.com/onerddev/PyOS.git
cd PyOS

# Automático com setup
bash setup_dev.sh

poetry shell
pyos run "seu objetivo aqui"
```

## Uso na Prática

```python
import asyncio
from pyos.core import SecurityShield
from pyos.core.orchestrator import PyOSOrchestrator, ModelProvider
from pyos.core.memory import SemanticMemory
from pyos.core.loader import PluginLoader
from pyos.core.security import PythonASTValidator, ApprovalManager

async def main():
    # Segurança em 3 camadas
    shield = SecurityShield()
    shield.add_allowed_command("python")
    
    validator = PythonASTValidator(shield)
    approval_mgr = ApprovalManager()
    
    # Memória semântica
    memory = SemanticMemory()
    
    # Auto-descoberta de plugins
    plugin_loader = PluginLoader()
    await plugin_loader.load_all()
    
    # Orquestrador com todos os sistemas
    orchestrator = PyOSOrchestrator(
        shield=shield,
        model_provider=ModelProvider.OPENAI,
        enable_memory=True,
        auto_load_plugins=True,
    )
    
    # Executar com auto-cura + memory
    result = await orchestrator.execute_objective(
        "Pesquise sobre IA generativa e salve em PDF"
    )
    
    print(f"Sucesso: {result['success']}")
    print(f"Iterações: {result['iterations']}")
    print(f"Ações: {len(result['action_log'])}")
    print(f"Memória: {memory.stats()}")

asyncio.run(main())
```

## Contribuições e Comunidade

Quer contribuir? Veja [CONTRIBUTING.md](CONTRIBUTING.md) para:
- Como criar plugins
- Padrões de segurança
- Checklist de código
- Processo de PR

Veja [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) para as regras da comunidade.

## Licença

MIT License © 2026 Anatalia

Feito para automação inteligente e segura | [GitHub](https://github.com/onerddev/PyOS)

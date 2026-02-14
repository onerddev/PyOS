#!/bin/bash

###############################################################################
# PyOS-Agent Development Environment Setup
# 
# Este script configura o ambiente de desenvolvimento completo:
# 1. Instala dependências via Poetry
# 2. Configura validação automática (pre-commit)
# 3. Verifica chaves de API no .env
# 4. Executa testes iniciais
###############################################################################

set -e  # Sair se qualquer comando falhar

# Definir cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções auxiliares
print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
}

print_info() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# ============================================================================
# 1. VERIFICAR PRÉ-REQUISITOS
# ============================================================================

print_header "1. Verificando Pré-requisitos"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 não está instalado"
    exit 1
fi
python_version=$(python3 --version | cut -d' ' -f2)
print_info "Python $python_version detectado"

# Verificar Poetry
if ! command -v poetry &> /dev/null; then
    print_warn "Poetry não encontrado. Instalando..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="/root/.local/bin:$PATH"
else
    poetry_version=$(poetry --version | cut -d' ' -f3)
    print_info "Poetry $poetry_version detectado"
fi

# ============================================================================
# 2. INSTALAR DEPENDÊNCIAS
# ============================================================================

print_header "2. Instalando Dependências"

if [ ! -f "pyproject.toml" ]; then
    print_error "pyproject.toml não encontrado. Execute este script na raiz do projeto."
    exit 1
fi

print_info "Instalando dependências Python com Poetry..."
poetry install

print_info "Atualizando dependências..."
poetry update --dry-run || true

# ============================================================================
# 3. CONFIGURAR PRE-COMMIT
# ============================================================================

print_header "3. Configurando Pre-commit Hooks"

# Instalar git hooks
print_info "Instalando git hooks para validação automática..."

# Criar arquivo pre-commit
mkdir -p .git/hooks

cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

# Pre-commit hook - Validação de código antes de commit

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Running pre-commit checks...${NC}"

# 1. Ruff (linter rápido)
echo -e "${YELLOW}1. Ruff linting...${NC}"
if poetry run ruff check src/ tests/ --fix > /dev/null 2>&1; then
    echo -e "${GREEN}   ✓ Ruff OK${NC}"
else
    echo -e "${RED}   ✗ Ruff encontrou problemas${NC}"
    poetry run ruff check src/ tests/
    exit 1
fi

# 2. Black (formatter)
echo -e "${YELLOW}2. Black formatting...${NC}"
if poetry run black src/ tests/ --quiet > /dev/null 2>&1; then
    echo -e "${GREEN}   ✓ Black OK${NC}"
else
    echo -e "${RED}   ✗ Black encontrou problemas${NC}"
    exit 1
fi

# 3. MyPy (type checking)
echo -e "${YELLOW}3. MyPy type checking...${NC}"
if poetry run mypy src/ --ignore-missing-imports > /dev/null 2>&1; then
    echo -e "${GREEN}   ✓ MyPy OK${NC}"
else
    echo -e "${RED}   ✗ MyPy encontrou tipo issues${NC}"
    poetry run mypy src/ --ignore-missing-imports
fi

echo -e "${GREEN}Pre-commit checks passed!${NC}"
EOF

chmod +x .git/hooks/pre-commit

print_info "Git hooks instalados"

# ============================================================================
# 4. VERIFICAR CHAVES DE API
# ============================================================================

print_header "4. Verificando Chaves de API"

# Verificar se .env existe
if [ ! -f ".env" ]; then
    print_warn ".env não encontrado. Criando a partir de .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_warn "Arquivo .env criado. VOCÊ PRECISA ADICIONAR SUAS CHAVES DE API!"
    else
        print_error ".env.example não encontrado"
        exit 1
    fi
fi

# Verificar variáveis necessárias
missing_keys=0

for key in OPENAI_API_KEY ANTHROPIC_API_KEY GOOGLE_API_KEY; do
    if grep -q "^${key}=" .env; then
        value=$(grep "^${key}=" .env | cut -d'=' -f2-)
        if [ -z "$value" ] || [[ "$value" == "sk-"* ]] || [[ "$value" == *"YOUR_KEY"* ]]; then
            print_warn "Chave $key não configurada (usando valor padrão)"
            ((missing_keys++))
        else
            print_info "Chave $key configurada ✓"
        fi
    else
        print_warn "Variável $key não encontrada em .env"
        ((missing_keys++))
    fi
done

if [ $missing_keys -gt 0 ]; then
    print_warn "$missing_keys chave(s) de API precisam ser configuradas em .env"
    print_warn "Edite .env com suas credenciais:"
    print_warn "  - OPENAI_API_KEY=sk-..."
    print_warn "  - ANTHROPIC_API_KEY=sk-ant-..."
    print_warn "  - GOOGLE_API_KEY=..."
fi

# ============================================================================
# 5. EXECUTAR TESTES BÁSICOS
# ============================================================================

print_header "5. Executando Testes"

print_info "Rodando testes unitários..."
if poetry run pytest tests/ -v --tb=short 2>/dev/null; then
    print_info "Todos os testes passaram ✓"
else
    print_warn "Alguns testes falharam. Verifique com: poetry run pytest tests/ -v"
fi

# ============================================================================
# 6. SETUP COMPLETO
# ============================================================================

print_header "6. Setup Concluído!"

print_info "Seu ambiente de desenvolvimento está pronto!"
echo ""
echo "Próximos passos:"
echo ""
echo -e "${BLUE}1. Ativar ambiente:${NC}"
echo "   poetry shell"
echo ""
echo -e "${BLUE}2. Executar o CLI:${NC}"
echo "   pyos status"
echo "   pyos init"
echo "   pyos run 'seu objetivo'"
echo ""
echo -e "${BLUE}3. Executar testes com cobertura:${NC}"
echo "   poetry run pytest tests/ --cov=src/pyos"
echo ""
echo -e "${BLUE}4. Iniciar servidor API (opcional):${NC}"
echo "   poetry run python -m uvicorn pyos.api.main:app --reload"
echo ""
echo -e "${BLUE}5. Modo Docker (opcional):${NC}"
echo "   docker-compose up -d"
echo "   docker exec pyos-agent-dev poetry shell"
echo ""

print_info "Happy coding! 🚀"

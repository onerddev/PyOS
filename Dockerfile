FROM python:3.11-slim

# DEPENDÊNCIAS DE SISTEMA para captura de tela e automação de desktop
RUN apt-get update && apt-get install -y \
    # Bibliotecas X11 para captura de tela
    libx11-dev \
    libxext-dev \
    libxrender-dev \
    # xvfb para modo headless (simulador de display)
    xvfb \
    # Dependências adicionais
    libxtst-dev \
    x11-utils \
    git \
    curl \
    # Limpeza
    && rm -rf /var/lib/apt/lists/*

# Configurar variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DISPLAY=:99 \
    PATH="/root/.local/bin:$PATH"

# Instalar Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    poetry config virtualenvs.in-project true

WORKDIR /app

# Copiar arquivo de dependências
COPY pyproject.toml poetry.lock* ./

# Instalar dependências Python
RUN poetry install --no-interaction --no-ansi

# Copiar código-fonte
COPY . .

# Criar diretórios necessários
RUN mkdir -p /app/logs /app/screenshots /root/Desktop

# Iniciar Xvfb em background
RUN echo '#!/bin/bash\n\
Xvfb :99 -screen 0 1920x1080x24 &\n\
export DISPLAY=:99\n\
sleep 2\n\
exec "$@"' > /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

# Comando padrão: CLI do PyOS
CMD ["poetry", "run", "pyos", "--help"]

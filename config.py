"""
Módulo de Configuração do PyOS-Agent.

Gerencia todas as variáveis de ambiente e configurações da aplicação
através de Pydantic BaseSettings, garantindo validação e tipagem.

Classes:
    Settings: Configurações gerais da aplicação.

Exemplo:
    >>> settings = Settings()
    >>> print(settings.app_name)
    'PyOS-Agent'
"""

from __future__ import annotations

from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings
from loguru import logger


class Settings(BaseSettings):
    """
    Configurações da aplicação PyOS-Agent.
    
    Carrega variáveis de ambiente do arquivo .env e as valida
    usando Pydantic, garantindo tipos corretos e valores padrão.
    
    Attributes:
        app_name: Nome da aplicação.
        app_version: Versão da aplicação.
        debug: Modo debug ativado.
        log_level: Nível de logging (DEBUG, INFO, WARNING, ERROR).
        api_host: Host do servidor FastAPI.
        api_port: Porta do servidor FastAPI.
        api_title: Título da API.
        max_command_timeout: Timeout máximo para execução de comandos (segundos).
        security_enabled: Se o sistema de segurança está ativado.
        allowed_execution_paths: Caminhos permite para execução.
    """

    # Informações da aplicação
    app_name: str = "PyOS-Agent"
    app_version: str = "0.1.0"
    
    # Configuração de ambiente
    debug: bool = False
    log_level: str = "INFO"
    
    # Configuração da API
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_title: str = "PyOS-Agent API"
    api_description: str = "Agente autônomo com interface FastAPI"
    
    # Configurações de execução
    max_command_timeout: int = 30
    max_screenshot_quality: int = 85
    
    # Segurança
    security_enabled: bool = True
    allowed_execution_paths: str = ""  # Separado por ':'
    
    # Configuração de arquivo
    env_file: str = ".env"
    env_file_encoding: str = "utf-8"

    class Config:
        """Configuração da classe BaseSettings."""
        
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def __init__(self, **data) -> None:
        """
        Inicializa as configurações.
        
        Args:
            **data: Valores para sobrescrever padrões.
        """
        super().__init__(**data)
        logger.info(
            f"Aplicação {self.app_name} v{self.app_version} "
            f"inicializada em modo {'DEBUG' if self.debug else 'PRODUÇÃO'}"
        )

    def get_api_url(self) -> str:
        """
        Constrói URL completa da API.
        
        Returns:
            URL completa da API.
            
        Example:
            >>> settings = Settings()
            >>> settings.get_api_url()
            'http://127.0.0.1:8000'
        """
        # Só usa HTTPS se não for localhost e debug estiver desativado
        is_localhost = self.api_host in ("127.0.0.1", "localhost")
        protocol = "http" if self.debug or is_localhost else "https"
        return f"{protocol}://{self.api_host}:{self.api_port}"

    def get_allowed_paths(self) -> list[str]:
        """
        Retorna lista de caminhos permitidos.
        
        Os caminhos são separados por ':' no arquivo .env.
        
        Returns:
            Lista de caminhos permitidos.
            
        Example:
            >>> settings = Settings(
            ...     allowed_execution_paths="/home/user:/tmp"
            ... )
            >>> settings.get_allowed_paths()
            ['/home/user', '/tmp']
        """
        if not self.allowed_execution_paths:
            return []
        
        return [
            p.strip() for p in self.allowed_execution_paths.split(":")
            if p.strip()
        ]

    def to_dict(self) -> dict:
        """
        Retorna configurações como dicionário (sem valores sensíveis).
        
        Returns:
            Dicionário com configurações públicas.
            
        Example:
            >>> settings = Settings()
            >>> config_dict = settings.to_dict()
        """
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "debug": self.debug,
            "log_level": self.log_level,
            "api_url": self.get_api_url(),
            "security_enabled": self.security_enabled,
            "max_command_timeout": self.max_command_timeout,
        }


def get_settings() -> Settings:
    """
    Factory para obter instância singleton de Settings.
    
    Returns:
        Instância de Settings com configurações carregadas do .env.
        
    Example:
        >>> settings = get_settings()
        >>> print(settings.app_name)
        'PyOS-Agent'
    """
    return Settings()

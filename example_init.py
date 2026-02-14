"""
Exemplo de inicialização do PyOS-Agent.

Demonstra como usar os módulos core (Security e Config).
"""

from __future__ import annotations

from pyos.core import SecurityShield, get_settings
from loguru import logger
from pathlib import Path


def initialize_agent() -> tuple[SecurityShield, dict]:
    """
    Inicializa o agente com configurações e segurança.
    
    Returns:
        Tupla contendo (SecurityShield, Dicionário de configuração).
        
    Example:
        >>> shield, config = initialize_agent()
        >>> print(config['app_name'])
        'PyOS-Agent'
    """
    # Carregar configurações
    settings = get_settings()
    logger.info(f"Inicializando {settings.app_name} v{settings.app_version}")
    
    # Inicializar segurança
    shield = SecurityShield()
    
    if settings.security_enabled:
        # Adicionar caminhos permitidos
        allowed_paths = settings.get_allowed_paths()
        for path_str in allowed_paths:
            try:
                shield.add_allowed_path(path_str)
                logger.debug(f"Caminho permitido adicionado: {path_str}")
            except ValueError as e:
                logger.warning(f"Erro ao adicionar caminho: {e}")
        
        # Adicionar comandos básicos de segurança
        basic_commands = ["ls", "pwd", "echo", "cat", "grep", "find"]
        for cmd in basic_commands:
            shield.add_allowed_command(cmd)
        
        logger.info(f"Sistema de segurança ativado com {len(basic_commands)} comandos base")
    
    config = settings.to_dict()
    logger.info("Inicialização concluída com sucesso")
    
    return shield, config


def main() -> None:
    """Função principal de exemplo."""
    shield, config = initialize_agent()
    
    # Exibir relatório de segurança
    report = shield.get_security_report()
    logger.info(f"Relatório de Segurança:")
    logger.info(f"  - Comandos permitidos: {report['total_allowed_commands']}")
    logger.info(f"  - Caminhos permitidos: {report['total_allowed_paths']}")
    logger.info(f"  - Padrões bloqueados: {report['blocked_patterns']}")
    
    # Exemplo de teste de comando
    test_commands = ["ls", "rm -rf /", "echo test"]
    print("\n=== Teste de Autorização de Comandos ===")
    for cmd in test_commands:
        allowed = shield.is_command_allowed(cmd)
        status = "✅ Permitido" if allowed else "❌ Bloqueado"
        print(f"{cmd:20} -> {status}")


if __name__ == "__main__":
    main()

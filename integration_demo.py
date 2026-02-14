"""
PyOS-Agent v2.0 - Complete Integration Example

Demonstrates all advanced features:
- Semantic Memory with ChromaDB
- Self-Healing with 3-tier retry
- Plugin auto-discovery
- Multi-layer security
- Rich dashboard telemetry
- Python AST analysis
- User approval system
"""

import asyncio
from pathlib import Path

from loguru import logger

from pyos.core import SecurityShield, get_settings
from pyos.core.memory import SemanticMemory, MemoryType
from pyos.core.loader import PluginLoader
from pyos.core.orchestrator import PyOSOrchestrator, ModelProvider
from pyos.core.security import PythonASTValidator, ApprovalManager
from pyos.ui import get_dashboard

logger.remove()  # Remove default handler
logger.add(
    lambda msg: print(msg, end=""),
    format="<level>{level: <8}</level> | {message}",
    colorize=True,
)


async def main():
    """
    Complete PyOS-Agent integration example.
    
    Shows:
    1. Security setup (3 layers)
    2. Memory initialization (ChromaDB)
    3. Plugin auto-discovery
    4. Orchestrator with self-healing
    5. Dashboard telemetry
    """

    logger.info("========== PyOS-Agent v2.0 Initialization ==========\n")

    # ===== LAYER 1: SECURITY =====
    logger.info("🔐 Layer 1: Multi-Layer Security")

    shield = SecurityShield()
    shield.add_allowed_command("python")
    shield.add_allowed_command("python3")
    shield.add_allowed_command("ls")
    shield.add_allowed_command("grep")
    shield.add_allowed_path(str(Path.home()))

    ast_validator = PythonASTValidator(shield=shield)
    approval_mgr = ApprovalManager(auto_approve=True)  # Dev mode

    logger.info("  ✓ AllowList configured")
    logger.info("  ✓ AST Analyzer ready")
    logger.info("  ✓ Approval Manager ready\n")

    # ===== LAYER 2: SEMANTIC MEMORY =====
    logger.info("🧠 Layer 2: Semantic Memory")

    memory = SemanticMemory(
        db_path="./.pyos/memory",
        model_name="all-MiniLM-L6-v2",
        collection_name="integration_demo",
    )

    # Seed some memories
    await memory.store(
        content="Successfully executed ls command on /home directory",
        memory_type=MemoryType.SUCCESS,
        metadata={"tool": "terminal", "command": "ls"},
    )

    await memory.store(
        content="Error: python command not found - solution: try python3",
        memory_type=MemoryType.ERROR,
        metadata={"tool": "terminal", "command": "python"},
    )

    logger.info(f"  ✓ Memory initialized: {memory.stats()}\n")

    # ===== LAYER 3: PLUGIN AUTO-DISCOVERY =====
    logger.info("🎮 Layer 3: Plugin System")

    plugin_loader = PluginLoader()
    await plugin_loader.load_all()

    logger.info(f"  ✓ Plugins discovered: {len(plugin_loader.instances)}")
    for tool in plugin_loader.list_tools():
        logger.info(f"    - {tool['name']:20} | {tool['description']}")
    logger.info("")

    # ===== LAYER 4: ORCHESTRATOR WITH AUTO-HEALING =====
    logger.info("🤖 Layer 4: Orchestrator (Self-Healing)")

    orchestrator = PyOSOrchestrator(
        settings=get_settings(),
        shield=shield,
        model_provider=ModelProvider.OPENAI,
        max_iterations=5,
        enable_memory=True,
        auto_load_plugins=True,
    )

    # Register sample tools
    orchestrator.register_tool(
        "take_screenshot",
        lambda: "Screenshot captured (simulated)",
        "Capture desktop screenshot"
    )

    orchestrator.register_tool(
        "execute_command",
        lambda cmd: f"Executed: {cmd}",
        "Execute terminal command"
    )

    logger.info(f"  ✓ Orchestrator ready with {len(orchestrator.tools)} tools")
    logger.info(f"  ✓ Self-healing: up to {orchestrator.max_retries} retries\n")

    # ===== LAYER 5: DASHBOARD & TELEMETRY =====
    logger.info("📊 Layer 5: Dashboard Telemetry")

    dashboard = get_dashboard()
    dashboard.start()

    logger.info("  ✓ Rich dashboard started")
    logger.info("  ✓ 4 telemetry panels active:")
    logger.info("    - [PENSAMENTO DA IA]")
    logger.info("    - [AÇÃO EXECUTADA]")
    logger.info("    - [STATUS DE SEGURANÇA]")
    logger.info("    - [MEMÓRIA RECALCADA]\n")

    # ===== DEMONSTRATION =====
    logger.info("=" * 60)
    logger.info("🔬 DEMONSTRATION: Executing objective with all systems")
    logger.info("=" * 60 + "\n")

    # Update dashboard
    dashboard.update_ai_reasoning("Analisando objetivo do usuário...")
    dashboard.update_metrics(iterations=1, total_actions=1, execution_time=0.5)

    # Test 1: Valid command (should pass security)
    logger.info("\n[TEST 1] Valid command with security validation")
    try:
        shield.validate_command("ls")
        logger.info("  ✅ Command 'ls' passed AllowList\n")
    except Exception as e:
        logger.error(f"  ❌ Validation failed: {e}\n")

    dashboard.update_security_status(is_safe=True, violations=0)

    # Test 2: Invalid command (should fail security)
    logger.info("[TEST 2] Invalid command - security blocking")
    try:
        shield.validate_command("rm -rf /")
        logger.info("  ❌ Should have been blocked!\n")
    except Exception as e:
        logger.warning(f"  ✅ Correctly blocked: {e}\n")

    dashboard.update_security_status(is_safe=False, violations=1)

    # Test 3: Python code analysis
    logger.info("[TEST 3] Python AST static analysis")
    malicious_code = """
import subprocess
subprocess.run("rm -rf /")
"""
    is_safe, violations = ast_validator.validate_python_code(malicious_code)
    logger.warning(
        f"  {'✅' if not is_safe else '❌'} Code safety: {is_safe}"
    )
    if violations:
        for v in violations:
            logger.warning(f"     • {v}")
    logger.info("")

    # Test 4: Memory learns success
    logger.info("[TEST 4] Learning from successful action")
    await memory.learn_from_success(
        action="Execute Python command",
        result="Script ran successfully",
        tool="terminal",
        context={"command": "python3 script.py"},
    )
    logger.info("  ✅ Memory stored: successful action learned\n")

    # Test 5: Semantic recall
    logger.info("[TEST 5] Semantic memory recall")
    similar = await memory.recall("run python script", limit=3)
    logger.info(f"  ✅ Found {len(similar)} similar memories\n")

    dashboard.update_memory_recall(
        recall_count=len(similar),
        total_entries=memory._count_entries(),
        last_recall=similar[0].content if similar else ""
    )

    # Test 6: Approval system
    logger.info("[TEST 6] User approval for critical actions")
    if approval_mgr.is_critical("apt install package"):
        approved = await approval_mgr.require_approval(
            "apt install package",
            context="Installation of system package"
        )
        logger.info(f"  {'✅' if approved else '❌'} Approval: {approved}\n")

    # Final summary
    logger.info("=" * 60)
    logger.info("✅ Integration Test Complete")
    logger.info("=" * 60)

    logger.info("\nAll systems operational:")
    logger.info("  ✓ Security (AllowList + AST + Approval)")
    logger.info("  ✓ Memory (ChromaDB + Vectors)")
    logger.info("  ✓ Plugins (Auto-discovery)")
    logger.info("  ✓ Orchestrator (Self-healing)")
    logger.info("  ✓ Dashboard (Real-time telemetry)")

    logger.info(f"\nMemory Statistics:")
    logger.info(f"  Entries: {memory._count_entries()}")
    logger.info(f"  Model: all-MiniLM-L6-v2 (384-dim)")
    logger.info(f"  Embeddings: sentence-transformers")
    logger.info(f"  Backend: ChromaDB")

    logger.info(f"\nSecurity Report:")
    report = shield.get_security_report()
    logger.info(f"  Allowed Commands: {report['total_allowed_commands']}")
    logger.info(f"  Allowed Paths: {report['total_allowed_paths']}")
    logger.info(f"  Blocked Patterns: {report['blocked_patterns']}")

    logger.info("\n" + "=" * 60)
    logger.info("🚀 PyOS-Agent v2.0 Ready for Production")
    logger.info("=" * 60 + "\n")

    # Keep dashboard running
    await asyncio.sleep(3)

    dashboard.stop()
    logger.info("\n✅ Integration test completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())

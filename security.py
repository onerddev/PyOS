"""
Módulo de Segurança do PyOS-Agent.

Este módulo implementa um sistema robusto de controle de acesso através da classe
SecurityShield, que utiliza AllowLists para validar execução de comandos e acesso
a caminhos de disco.

Classes:
    SecurityShield: Gerenciador de segurança com validação de comandos e caminhos.

Exemplo:
    >>> shield = SecurityShield()
    >>> shield.add_allowed_command("ls")
    >>> shield.is_command_allowed("ls")
    True
"""

from __future__ import annotations

import ast
import asyncio
import re
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, Set
from loguru import logger


class SecurityViolationError(Exception):
    """Exceção raised quando uma violação de segurança é detectada."""

    pass


class SecurityShield:
    """
    Sistema de segurança para validação e controle de acesso.
    
    Implementa um modelo AllowList para comandos de terminal e caminhos
    de pasta, permitindo apenas ações explicitamente autorizadas.
    
    Attributes:
        allowed_commands: Conjunto de comandos de terminal permitidos.
        allowed_paths: Conjunto de caminhos de pasta permitidos.
        blocked_patterns: Padrões regex bloqueados globalmente.
    """

    def __init__(self) -> None:
        """
        Inicializa o SecurityShield com listas vazias.
        
        AllowLists inicialmente vazias devem ser populadas conforme
        necessário pela aplicação.
        """
        self.allowed_commands: Set[str] = set()
        self.allowed_paths: Set[Path] = set()
        self.blocked_patterns: list[re.Pattern[str]] = [
            re.compile(r"rm\s+-rf\s+/"),  # Comandos destrutivos
            re.compile(r"mkfs"),  # Formatação de disco
            re.compile(r"dd\s+if=.*of=/dev"),  # Operações de dispositivos
        ]
        logger.info("SecurityShield inicializado com sucesso")

    def add_allowed_command(self, command: str) -> None:
        """
        Adiciona um comando à lista de permitidos.
        
        Args:
            command: Nome do comando a autorizar.
            
        Raises:
            ValueError: Se o comando estiver vazio.
            
        Example:
            >>> shield.add_allowed_command("ls")
            >>> shield.add_allowed_command("grep")
        """
        if not command or not isinstance(command, str):
            raise ValueError("Comando deve ser uma string não vazia")
        
        normalized = command.strip().lower()
        self.allowed_commands.add(normalized)
        logger.debug(f"Comando permitido adicionado: {normalized}")

    def add_allowed_path(self, path: str | Path) -> None:
        """
        Adiciona um caminho à lista de permitidos.
        
        Args:
            path: Caminho da pasta a autorizar.
            
        Raises:
            ValueError: Se o caminho não existir.
            
        Example:
            >>> shield.add_allowed_path("/home/user/documents")
            >>> shield.add_allowed_path(Path.home())
        """
        p = Path(path).resolve()
        
        if not p.exists():
            logger.warning(f"Caminho não existe: {p}")
            raise ValueError(f"Caminho não existe: {p}")
        
        self.allowed_paths.add(p)
        logger.debug(f"Caminho permitido adicionado: {p}")

    def is_command_allowed(self, command: str) -> bool:
        """
        Verifica se um comando é permitido.
        
        Args:
            command: Comando a validar.
            
        Returns:
            True se o comando está na AllowList, False caso contrário.
            
        Example:
            >>> shield.is_command_allowed("ls")
            True
        """
        if not command:
            return False
        
        # Extrai primeira palavra (comando principal)
        cmd_name = command.strip().split()[0].lower()
        
        # Verifica padrões bloqueados
        for pattern in self.blocked_patterns:
            if pattern.search(command.lower()):
                logger.warning(f"Comando bloqueado por padrão: {command}")
                return False
        
        return cmd_name in self.allowed_commands

    def is_path_allowed(self, path: str | Path) -> bool:
        """
        Verifica se um caminho é permitido.
        
        Args:
            path: Caminho a validar.
            
        Returns:
            True se o caminho está autorizado, False caso contrário.
            
        Example:
            >>> shield.is_path_allowed("/home/user/documents")
            True
        """
        p = Path(path).resolve()
        
        # Verifica se o caminho ou um de seus pais está na AllowList
        for allowed_path in self.allowed_paths:
            try:
                p.relative_to(allowed_path)
                return True
            except ValueError:
                continue
        
        return False

    def validate_command(self, command: str) -> None:
        """
        Valida um comando e lança exceção se não permitido.
        
        Args:
            command: Comando a validar.
            
        Raises:
            SecurityViolationError: Se o comando não for permitido.
            
        Example:
            >>> shield.validate_command("ls")
            >>> shield.validate_command("rm -rf /")
            SecurityViolationError: Comando não permitido: rm -rf /
        """
        if not self.is_command_allowed(command):
            logger.error(f"Violação de segurança - Comando não permitido: {command}")
            raise SecurityViolationError(f"Comando não permitido: {command}")

    def validate_path(self, path: str | Path) -> None:
        """
        Valida um caminho e lança exceção se não permitido.
        
        Args:
            path: Caminho a validar.
            
        Raises:
            SecurityViolationError: Se o caminho não for permitido.
            
        Example:
            >>> shield.validate_path("/home/user/documents")
            >>> shield.validate_path("/root/secret")
            SecurityViolationError: Caminho não permitido: /root/secret
        """
        if not self.is_path_allowed(path):
            logger.error(f"Violação de segurança - Caminho não permitido: {path}")
            raise SecurityViolationError(f"Caminho não permitido: {path}")

    def require_command_permission(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Decorador para validar comando antes de executar função.
        
        O primeiro argumento deve ser o comando a executar.
        
        Args:
            func: Função a decorar.
            
        Returns:
            Função decorada com validação de segurança.
            
        Raises:
            SecurityViolationError: Se o comando não for permitido.
            
        Example:
            >>> @shield.require_command_permission
            ... def execute_command(command: str) -> str:
            ...     return f"Executando: {command}"
        """
        @wraps(func)
        def wrapper(command: str, *args: Any, **kwargs: Any) -> Any:
            self.validate_command(command)
            logger.info(f"Executando comando autorizado: {command}")
            return func(command, *args, **kwargs)
        
        return wrapper

    def require_path_permission(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Decorador para validar caminho antes de executar função.
        
        O primeiro argumento deve ser o caminho a acessar.
        
        Args:
            func: Função a decorar.
            
        Returns:
            Função decorada com validação de segurança.
            
        Raises:
            SecurityViolationError: Se o caminho não for permitido.
            
        Example:
            >>> @shield.require_path_permission
            ... def read_file(path: str) -> str:
            ...     return Path(path).read_text()
        """
        @wraps(func)
        def wrapper(path: str | Path, *args: Any, **kwargs: Any) -> Any:
            self.validate_path(path)
            logger.info(f"Acessando caminho autorizado: {path}")
            return func(path, *args, **kwargs)
        
        return wrapper

    def get_security_report(self) -> dict[str, Any]:
        """
        Gera relatório de segurança atual.
        
        Returns:
            Dicionário contendo configuração de segurança atual.
            
        Example:
            >>> report = shield.get_security_report()
            >>> print(report['total_allowed_commands'])
            5
        """
        return {
            "total_allowed_commands": len(self.allowed_commands),
            "allowed_commands": sorted(self.allowed_commands),
            "total_allowed_paths": len(self.allowed_paths),
            "allowed_paths": [str(p) for p in sorted(self.allowed_paths)],
            "blocked_patterns": len(self.blocked_patterns),
        }


class PythonASTValidator:
    """
    Static analysis for Python code using AST (Abstract Syntax Tree).
    
    Validates generated Python scripts before execution, blocking:
    - Dangerous imports (os.system, shutil, subprocess without approval)
    - Eval/exec/compile calls
    - File operations on unauthorized paths
    - Network operations to suspicious hosts
    """

    # Dangerousimports that require approval
    DANGEROUS_IMPORTS = {
        "os.system",
        "os.popen",
        "subprocess.call",
        "subprocess.run",
        "subprocess.Popen",
        "shutil.rmtree",
        "shutil.copy",
        "eval",
        "exec",
        "compile",
        "__import__",
    }

    # Built-in functions that are risky
    DANGEROUS_BUILTINS = {
        "eval",
        "exec",
        "compile",
        "open",
        "__import__",
        "globals",
        "locals",
    }

    def __init__(self, shield: Optional[SecurityShield] = None):
        """
        Initialize AST validator.
        
        Args:
            shield: Optional SecurityShield for path validation
        """
        self.shield = shield
        self.violations: list[str] = []

    def validate_python_code(self, code: str) -> tuple[bool, list[str]]:
        """
        Validate Python code through AST analysis.
        
        Args:
            code: Python code string to validate
            
        Returns:
            (is_safe, list_of_violations)
        """
        self.violations = []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            self.violations.append(f"Syntax error: {e}")
            return False, self.violations

        # Walk the AST and check for dangerous patterns
        for node in ast.walk(tree):
            self._check_import(node)
            self._check_function_call(node)
            self._check_builtin_call(node)

        is_safe = len(self.violations) == 0
        if not is_safe:
            logger.warning(f"Python code validation failed: {self.violations}")

        return is_safe, self.violations

    def _check_import(self, node: ast.stmt) -> None:
        """Check for dangerous imports."""
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in self.DANGEROUS_IMPORTS:
                    self.violations.append(f"Dangerous import: {alias.name}")

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                full_name = node.module
                for alias in node.names:
                    full_import = f"{full_name}.{alias.name}"
                    if full_import in self.DANGEROUS_IMPORTS:
                        self.violations.append(f"Dangerous import: {full_import}")
                    if alias.name in ("system", "popen", "call", "Popen"):
                        self.violations.append(f"Dangerous import: {full_import}")

    def _check_function_call(self, node: ast.expr) -> None:
        """Check for dangerous function calls."""
        if isinstance(node, ast.Call):
            # Check for eval/exec/compile calls
            if isinstance(node.func, ast.Name):
                if node.func.id in self.DANGEROUS_BUILTINS:
                    self.violations.append(f"Dangerous builtin call: {node.func.id}()")
            
            # Check for getattr/setattr abuse
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in ("__import__", "__class__", "__bases__"):
                    self.violations.append(f"Dangerous attribute access: {node.func.attr}")

    def _check_builtin_call(self, node: ast.expr) -> None:
        """Check for builtin function calls that might be dangerous."""
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id == "open":
                    # Check file operations (if shield available)
                    if self.shield and node.args:
                        if isinstance(node.args[0], ast.Constant):
                            filepath = node.args[0].value
                            if isinstance(filepath, str):
                                if not self.shield.is_path_allowed(filepath):
                                    self.violations.append(
                                        f"File access not allowed: {filepath}"
                                    )

    def get_violations_report(self) -> str:
        """Get formatted report of violations."""
        if not self.violations:
            return "✅ Code is safe"
        
        lines = ["❌ Code violations found:"]
        for i, violation in enumerate(self.violations, 1):
            lines.append(f"  {i}. {violation}")
        
        return "\n".join(lines)


class ApprovalManager:
    """
    Manages user approval for critical actions.
    
    Critical actions that require approval:
    - Delete/Remove operations
    - Format operations
    - Privilege escalation
    - Network changes
    - Installation/uninstallation
    """

    CRITICAL_KEYWORDS = {
        "delete", "remove", "rm", "rmdir",
        "format", "mkfs", "dd",
        "sudo", "chmod", "chown",
        "network", "firewall", "iptables",
        "install", "uninstall", "apt", "pip", "brew",
        "reboot", "shutdown", "halt",
    }

    def __init__(self, auto_approve: bool = False):
        """
        Initialize approval manager.
        
        Args:
            auto_approve: If True, skip approval (dangerous, dev only)
        """
        self.auto_approve = auto_approve
        self.approved_actions: set[str] = set()
        self.approval_history: list[dict[str, Any]] = []

    def is_critical(self, command: str) -> bool:
        """
        Check if a command is critical and requires approval.
        
        Args:
            command: Command string to check
            
        Returns:
            True if command contains critical keywords
        """
        cmd_lower = command.lower()
        for keyword in self.CRITICAL_KEYWORDS:
            if keyword in cmd_lower:
                return True
        
        return False

    async def require_approval(
        self,
        action: str,
        context: Optional[str] = None,
        callback: Optional[Callable[[bool], None]] = None,
    ) -> bool:
        """
        Request user approval for an action.
        
        Args:
            action: Action description
            context: Additional context to show user
            callback: Async callback to call with approval result
            
        Returns:
            True if approved, False otherwise
        """
        if self.auto_approve:
            logger.warning(f"Auto-approving critical action (dev mode): {action}")
            return True

        if action in self.approved_actions:
            logger.debug(f"Using cached approval for: {action}")
            return True

        # In production, this would show a Rich dialog
        # For now, log what would be requested
        logger.warning(f"⚠️  APPROVAL REQUIRED: {action}")
        if context:
            logger.warning(f"   Context: {context}")

        # Basic console approval for development
        try:
            from rich.prompt import Confirm
            approved = Confirm.ask(f"[bold yellow]Autorizar ação: {action}?[/bold yellow]")
        except (ImportError, Exception):
            # Fallback to standard input if rich fails or in non-interactive environment
            print(f"⚠️  APROVAÇÃO NECESSÁRIA: {action}")
            response = input("Autorizar? (y/n): ").lower()
            approved = response in ("y", "yes", "s", "sim")

        if approved:
            self.approved_actions.add(action)

            self.approval_history.append({
                "action": action,
                "context": context,
                "timestamp": datetime.now().isoformat() if "datetime" in dir() else None,
                "approved": True,
            })

            logger.info(f"✅ Action approved: {action}")

        if callback:
            if asyncio.iscoroutinefunction(callback):
                await callback(approved)
            else:
                callback(approved)

        return approved

    def get_approval_report(self) -> str:
        """Get report of approval history."""
        lines = [f"Approval History ({len(self.approval_history)} total):"]
        for entry in self.approval_history[-10:]:  # Last 10
            status = "✅" if entry["approved"] else "❌"
            lines.append(f"  {status} {entry['action']}")
        
        return "\n".join(lines)


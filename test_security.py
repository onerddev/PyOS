"""
Testes para o módulo Security.

Testes para a classe SecurityShield e validações de segurança.
"""

from __future__ import annotations

import pytest
from pathlib import Path
from pyos.core import SecurityShield, SecurityViolationError


class TestSecurityShield:
    """Testes para SecurityShield."""

    @pytest.fixture
    def shield(self) -> SecurityShield:
        """Fixture que retorna uma instância de SecurityShield."""
        return SecurityShield()

    def test_add_allowed_command(self, shield: SecurityShield) -> None:
        """Testa adição de comando à AllowList."""
        shield.add_allowed_command("ls")
        assert "ls" in shield.allowed_commands

    def test_add_allowed_command_empty_raises_error(
        self, shield: SecurityShield
    ) -> None:
        """Testa que comando vazio lança ValueError."""
        with pytest.raises(ValueError):
            shield.add_allowed_command("")

    def test_is_command_allowed_true(self, shield: SecurityShield) -> None:
        """Testa verificação de comando permitido."""
        shield.add_allowed_command("ls")
        assert shield.is_command_allowed("ls") is True

    def test_is_command_allowed_false(self, shield: SecurityShield) -> None:
        """Testa verificação de comando não permitido."""
        assert shield.is_command_allowed("rm") is False

    def test_blocked_pattern_detection(self, shield: SecurityShield) -> None:
        """Testa detecção de padrões bloqueados."""
        shield.add_allowed_command("rm")
        # rm -rf / deve ser bloqueado mesmo com comando adicionado
        assert shield.is_command_allowed("rm -rf /") is False

    def test_validate_command_success(self, shield: SecurityShield) -> None:
        """Testa validação de comando permitido."""
        shield.add_allowed_command("ls")
        # Não deve lançar exceção
        shield.validate_command("ls")

    def test_validate_command_failure(self, shield: SecurityShield) -> None:
        """Testa validação de comando não permitido."""
        with pytest.raises(SecurityViolationError):
            shield.validate_command("rm -rf /")

    def test_get_security_report(self, shield: SecurityShield) -> None:
        """Testa geração de relatório de segurança."""
        shield.add_allowed_command("ls")
        report = shield.get_security_report()
        
        assert report["total_allowed_commands"] == 1
        assert "ls" in report["allowed_commands"]
        assert isinstance(report["blocked_patterns"], int)

    def test_decorator_require_command_permission(
        self, shield: SecurityShield
    ) -> None:
        """Testa decorador require_command_permission."""
        shield.add_allowed_command("echo")
        
        @shield.require_command_permission
        def execute(command: str) -> str:
            return f"Executando: {command}"
        
        result = execute("echo hello")
        assert "echo hello" in result

    def test_decorator_require_command_permission_denied(
        self, shield: SecurityShield
    ) -> None:
        """Testa decorador nega comando não permitido."""
        @shield.require_command_permission
        def execute(command: str) -> str:
            return f"Executando: {command}"
        
        with pytest.raises(SecurityViolationError):
            execute("rm -rf /")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Testes para o módulo de Configuração.

Testes para a classe Settings e carregamento de configurações.
"""

from __future__ import annotations

import pytest
from pyos.core import Settings, get_settings


class TestSettings:
    """Testes para Settings."""

    def test_default_settings(self) -> None:
        """Testa valores padrão de Settings."""
        settings = Settings()
        
        assert settings.app_name == "PyOS-Agent"
        assert settings.api_host == "127.0.0.1"
        assert settings.api_port == 8000
        assert settings.security_enabled is True

    def test_custom_settings(self) -> None:
        """Testa inicialização com valores customizados."""
        settings = Settings(
            app_name="MyAgent",
            api_port=9000,
            debug=True
        )
        
        assert settings.app_name == "MyAgent"
        assert settings.api_port == 9000
        assert settings.debug is True

    def test_get_api_url_http(self) -> None:
        """Testa geração de URL da API em modo debug."""
        settings = Settings(debug=True, api_host="127.0.0.1", api_port=8000)
        assert settings.get_api_url() == "http://127.0.0.1:8000"

    def test_get_api_url_https(self) -> None:
        """Testa geração de URL da API em modo prod."""
        settings = Settings(debug=False, api_host="api.example.com", api_port=443)
        assert settings.get_api_url() == "https://api.example.com:443"

    def test_get_allowed_paths_empty(self) -> None:
        """Testa get_allowed_paths com lista vazia."""
        settings = Settings(allowed_execution_paths="")
        assert settings.get_allowed_paths() == []

    def test_get_allowed_paths_single(self) -> None:
        """Testa get_allowed_paths com um caminho."""
        settings = Settings(allowed_execution_paths="/tmp")
        paths = settings.get_allowed_paths()
        
        assert len(paths) == 1
        assert "/tmp" in paths

    def test_get_allowed_paths_multiple(self) -> None:
        """Testa get_allowed_paths com múltiplos caminhos."""
        settings = Settings(
            allowed_execution_paths="/tmp:/var/tmp:/home/user"
        )
        paths = settings.get_allowed_paths()
        
        assert len(paths) == 3
        assert "/tmp" in paths
        assert "/var/tmp" in paths
        assert "/home/user" in paths

    def test_get_allowed_paths_with_spaces(self) -> None:
        """Testa get_allowed_paths trimming spaces."""
        settings = Settings(
            allowed_execution_paths=" /tmp : /var/tmp : /home/user "
        )
        paths = settings.get_allowed_paths()
        
        assert len(paths) == 3
        # Spaces are trimmed
        assert all(not p.startswith(" ") and not p.endswith(" ") for p in paths)

    def test_to_dict(self) -> None:
        """Testa conversão para dicionário."""
        settings = Settings(app_name="TestApp", debug=True)
        config_dict = settings.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict["app_name"] == "TestApp"
        assert config_dict["debug"] is True
        assert "api_url" in config_dict
        assert "security_enabled" in config_dict

    def test_get_settings_singleton_like(self) -> None:
        """Testa função get_settings."""
        settings = get_settings()
        
        assert isinstance(settings, Settings)
        assert settings.app_name == "PyOS-Agent"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

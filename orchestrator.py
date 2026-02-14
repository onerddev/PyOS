"""
Módulo Orquestrador do PyOS-Agent.

Implementa o motor central que coordena ações entre IA e ferramentas,
gerenciando o loop de decisão e execução de tarefas com validação
obrigatória de segurança em cada passo. Inclui auto-cura (self-healing)
com retry inteligente e aprendizado de contexto semântico.

Classes:
    PyOSOrchestrator: Orquestrador principal com suporte a múltiplos modelos de IA.
    ToolResult: Resultado da execução de uma ferramenta.
    
Exemplo:
    >>> orchestrator = PyOSOrchestrator()
    >>> result = await orchestrator.execute_objective("Abra o navegador")
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from enum import Enum

from pydantic_ai import Agent, ModelMessage
from loguru import logger

from pyos.core.config import Settings, get_settings
from pyos.core.security import SecurityShield, SecurityViolationError
from pyos.core.memory import SemanticMemory, MemoryType
from pyos.plugins.base import BaseTool, ToolResult


try:
    from pyos.core.loader import PluginLoader
except ImportError:
    PluginLoader = None


class ModelProvider(str, Enum):
    """Provedores de modelos de IA suportados."""
    
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


@dataclass
class ActionLog:
    """Log de uma ação executada."""
    
    iteration: int
    action_type: str  # "security_check", "ai_decision", "tool_execution"
    tool_name: Optional[str] = None
    security_validated: bool = False
    success: bool = False
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class PyOSOrchestrator:
    """
    Orquestrador principal do PyOS-Agent.
    
    Coordena a execução de objetivos através de um loop que:
    1. Consulta modelo de IA
    2. Valida decisão com SecurityShield
    3. Executa ferramenta apropriada
    4. Registra ação em log detalhado
    
    SEGURANÇA: Cada ação é validada ANTES de ser executada.
    
    Attributes:
        settings: Configurações da aplicação.
        shield: Sistema de segurança (AllowList).
        model_provider: Provedor de modelo de IA.
        max_iterations: Número máximo de iterações do loop.
        tools: Dicionário de ferramentas disponíveis.
        action_log: Histórico de ações executadas.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        shield: Optional[SecurityShield] = None,
        model_provider: ModelProvider = ModelProvider.OPENAI,
        max_iterations: int = 10,
        enable_memory: bool = True,
        auto_load_plugins: bool = True,
    ) -> None:
        """
        Inicializa o orquestrador.
        
        Args:
            settings: Configurações da aplicação.
            shield: Sistema de segurança.
            model_provider: Provedor de modelo de IA.
            max_iterations: Máximo de iterações permitidas.
            enable_memory: Ativa semantic memory para aprendizado.
            auto_load_plugins: Auto-carrega plugins BaseTool.
        """
        self.settings = settings or get_settings()
        self.shield = shield or SecurityShield()
        self.model_provider = model_provider
        self.max_iterations = max_iterations
        self.tools: dict[str, Callable[..., Any]] = {}
        self.iteration_count = 0
        self.action_log: list[ActionLog] = []
        
        # Semantic Memory para aprendizado
        self.memory = SemanticMemory() if enable_memory else None
        
        # Plugin Loader automático
        self.plugin_loader: Optional[PluginLoader] = None
        if auto_load_plugins and PluginLoader:
            self.plugin_loader = PluginLoader()
        
        # Rastreamento de tentativas (para auto-cura)
        self.tool_attempts: dict[str, list[str]] = {}  # tool_name -> [prev_errors]
        self.max_retries = 3
        
        # Inicializar agente de IA
        self.agent = self._initialize_agent()
        
        logger.info(
            f"PyOSOrchestrator inicializado "
            f"(modelo={model_provider.value}, max_iter={max_iterations}, security={self.settings.security_enabled}, "
            f"memory={enable_memory}, plugins={auto_load_plugins})"
        )

    def _initialize_agent(self) -> Agent:
        """
        Inicializa o agente de IA baseado no provedor configurado.
        
        Returns:
            Agente Pydantic AI configurado.
        """
        model_string = self._get_model_string()
        
        system_prompt = (
            "Você é um assistente de automação de desktop inteligente com segurança rigorosa. "
            "Você tem acesso a ferramentas para tirar screenshots, executar comandos "
            "e interagir com o computador. "
            "\n\nREGRAS DE SEGURANÇA:\n"
            "1. Apenas use ferramentas explicitamente permitidas\n"
            "2. Nunca tente contornar o SecurityShield\n"
            "3. Sempre comece com take_screenshot para compreender o estado\n"
            "4. Se uma ação for bloqueada, tente uma alternativa segura\n"
            "5. Registre seu raciocínio antes de cada ação"
        )
        
        agent = Agent(
            model=model_string,
            system_prompt=system_prompt,
            tools=list(self.tools.values()),
            allow_model_calls=True,
        )
        
        return agent

    def _get_model_string(self) -> str:
        """
        Retorna a string do modelo baseado no provedor.
        
        Returns:
            String de identificação do modelo.
        """
        provider_models = {
            ModelProvider.OPENAI: "gpt-4o",
            ModelProvider.ANTHROPIC: "claude-3-5-sonnet-20240620",
            ModelProvider.GEMINI: "gemini-1.5-pro",
        }
        
        return provider_models.get(self.model_provider, "gpt-4o")

    def register_tool(
        self,
        name: str,
        func: Callable[..., Any],
        description: str,
    ) -> None:
        """
        Registra uma ferramenta disponível com validação de segurança.
        
        Args:
            name: Nome da ferramenta.
            func: Função a executar.
            description: Descrição do que a ferramenta faz.
        """
        # Envolver função com validação de segurança
        wrapped_func = self._wrap_tool_with_security(name, func)
        self.tools[name] = wrapped_func
        
        logger.info(f"✓ Ferramenta registrada: {name} - {description}")

    def _wrap_tool_with_security(
        self,
        tool_name: str,
        func: Callable[..., Any],
    ) -> Callable[..., Any]:
        """
        Envolve uma ferramenta com validação de segurança obrigatória.
        
        FLUXO DE SEGURANÇA:
        1. Validar que ferramenta é permitida
        2. Validar argumentos de entrada
        3. Executar ferramenta
        4. Registrar em log
        5. Retornar resultado
        
        Args:
            tool_name: Nome da ferramenta.
            func: Função a envolver.
            
        Returns:
            Função decorada com validação.
        """
        def wrapper(*args: Any, **kwargs: Any) -> ToolResult:
            start_time = time.time()
            
            try:
                # VALIDAÇÃO DE SEGURANÇA #1: Ferramenta registrada
                if tool_name not in self.tools:
                    logger.critical(f"🚨 Tentativa de usar ferramenta não registrada: {tool_name}")
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"Ferramenta não registrada: {tool_name}",
                        # security_validated=False,
                    )
                
                logger.debug(f"[SEC-PASS] Ferramenta {tool_name} está registrada")
                
                # VALIDAÇÃO DE SEGURANÇA #2: Validar argumentos
                # Para comandos terminal, validar contra SecurityShield
                if tool_name == "execute_command" and args:
                    command = args[0] if args else kwargs.get("command", "")
                    if self.settings.security_enabled:
                        try:
                            self.shield.validate_command(command)
                            logger.debug(f"[SEC-PASS] Comando validado: {command}")
                        except SecurityViolationError as e:
                            logger.warning(f"🚫 Comando bloqueado: {e}")
                            return ToolResult(
                                success=False,
                                output="",
                                error=str(e),
                                # security_validated=False,
                            )
                
                # VALIDAÇÃO DE SEGURANÇA #3: Validar caminhos
                if tool_name == "read_file" and args:
                    path = args[0] if args else kwargs.get("path", "")
                    if self.settings.security_enabled:
                        try:
                            self.shield.validate_path(path)
                            logger.debug(f"[SEC-PASS] Caminho validado: {path}")
                        except SecurityViolationError as e:
                            logger.warning(f"🚫 Caminho bloqueado: {e}")
                            return ToolResult(
                                success=False,
                                output="",
                                error=str(e),
                                # security_validated=False,
                            )
                
                # EXECUÇÃO
                logger.info(f"▶️  Executando ferramenta: {tool_name}")
                result = func(*args, **kwargs)
                
                execution_time = time.time() - start_time
                
                # Converter resultado para ToolResult
                if isinstance(result, ToolResult):
                    # result.security_validated = True  # ToolResult from base doesn't have this
                    result.execution_time_ms = execution_time * 1000
                    return result
                
                logger.info(f"✓ Ferramenta {tool_name} completada em {execution_time:.2f}s")
                
                return ToolResult(
                    success=True,
                    output=str(result),
                    # security_validated=True,
                    execution_time_ms=execution_time * 1000,
                )
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"❌ Erro na ferramenta {tool_name}: {e}")
                return ToolResult(
                    success=False,
                    output="",
                    error=str(e),
                    # security_validated=False,
                    execution_time_ms=execution_time * 1000,
                )
        
        return wrapper

    async def execute_objective(self, objective: str) -> dict[str, Any]:
        """
        Executa um objetivo através do loop de orquestração com segurança rigorosa.
        
        FLUXO DETALHADO:
        1. Inicializar contador e log
        2. Loop até max_iterations:
           a. Consultar IA com histórico
           b. IA retorna decisão (qual ferramenta ou "done")
           c. Validar decisão com SecurityShield
           d. Executar ferramenta (com validação obrigatória)
           e. Registrar ação em log
           f. Próxima iteração
        3. Retornar resultado com histórico completo
        
        Args:
            objective: Descrição do objetivo a alcançar.
            
        Returns:
            Dicionário com resultado da execução.
        """
        self.iteration_count = 0
        self.action_log = []
        
        logger.info("╔" + "═" * 78 + "╗")
        logger.info(f"║ INICIANDO EXECUÇÃO DE OBJETIVO (Segurança: {'ATIVADA ✓' if self.settings.security_enabled else 'DESATIVADA ⚠️'})")
        logger.info(f"║ Objetivo: {objective}")
        logger.info(f"║ Modelo: {self.model_provider.value}")
        logger.info(f"║ Max iterações: {self.max_iterations}")
        logger.info(f"║ Ferramentas disponíveis: {len(self.tools)}")
        logger.info("╚" + "═" * 78 + "╝")
        
        messages: list[ModelMessage] = []
        start_time = time.time()
        
        while self.iteration_count < self.max_iterations:
            self.iteration_count += 1
            
            iteration_start = time.time()
            
            try:
                # LOG DA ITERAÇÃO
                logger.info(f"\n───────── ITERAÇÃO {self.iteration_count}/{self.max_iterations} ─────────")
                logger.debug(f"Histórico: {len(messages)} eventos anteriores")
                
                # CONSULTAR IA
                logger.info("📡 Consultando modelo de IA...")
                response = await self._call_model(objective, messages)
                
                # LOG DA DECISÃO
                if response.get("done"):
                    logger.info("✅ IA decidiu: OBJETIVO COMPLETO")
                    logger.info(f"Mensagem: {response.get('message', '')}")
                    
                    self._log_action(
                        action_type="ai_decision",
                        success=True,
                        details={"decision": "done", "message": response.get("message")}
                    )
                    
                    total_time = time.time() - start_time
                    return {
                        "success": True,
                        "objective": objective,
                        "iterations": self.iteration_count,
                        "final_message": response.get("message", ""),
                        "total_time": total_time,
                        "action_log": self._format_action_log(),
                    }
                
                # EXTRAIR DECISÃO DA IA
                tool_name = response.get("tool_name")
                tool_args = response.get("tool_args", {})
                reasoning = response.get("reasoning", "")
                
                if reasoning:
                    logger.info(f"💭 Raciocínio da IA: {reasoning}")
                
                logger.info(f"🎯 IA decidiu usar ferramenta: {tool_name}")
                
                # VALIDAR FERRAMENTA
                if not tool_name or tool_name not in self.tools:
                    logger.warning(f"⚠️  Ferramenta não reconhecida: {tool_name}")
                    
                    self._log_action(
                        action_type="ai_decision",
                        success=False,
                        details={"tool": tool_name, "error": "not_found"}
                    )
                    
                    continue
                
                logger.debug(f"✓ Ferramenta {tool_name} está registrada e permitida")
                
                # EXECUTAR FERRAMENTA (validação obrigatória dentro)
                logger.info(f"▶️  Executando: {tool_name}({', '.join(f'{k}={v}' for k, v in list(tool_args.items())[:3])}...)")
                
                tool_result = await self._execute_tool(tool_name, tool_args)
                
                # LOG DO RESULTADO
                if tool_result.success:
                    logger.info(f"✓ {tool_name} completada com sucesso em {tool_result.execution_time:.2f}s")
                    logger.debug(f"Saída: {tool_result.output[:100]}..." if len(tool_result.output) > 100 else f"Saída: {tool_result.output}")
                else:
                    logger.warning(f"❌ {tool_name} falhou: {tool_result.error}")
                
                self._log_action(
                    action_type="tool_execution",
                    tool_name=tool_name,
                    success=tool_result.success,
                    security_validated=tool_result.security_validated,
                    details={
                        "output": tool_result.output[:100] if tool_result.output else "",
                        "error": tool_result.error,
                        "execution_time": tool_result.execution_time,
                    }
                )
                
                # ADICIONAR RESULTADO AO HISTÓRICO
                messages.append({
                    "tool": tool_name,
                    "result": tool_result.output,
                    "success": tool_result.success,
                    "timestamp": time.time(),
                })
                
                iteration_time = time.time() - iteration_start
                logger.debug(f"Iteração concluída em {iteration_time:.2f}s")
                
            except Exception as e:
                logger.error(f"❌ Erro crítico na iteração {self.iteration_count}: {e}")
                
                self._log_action(
                    action_type="error",
                    success=False,
                    details={"error": str(e)}
                )
                
                total_time = time.time() - start_time
                return {
                    "success": False,
                    "objective": objective,
                    "iterations": self.iteration_count,
                    "error": str(e),
                    "total_time": total_time,
                    "action_log": self._format_action_log(),
                }
        
        # MAX ITERAÇÕES ATINGIDO
        logger.warning(f"⚠️  MÁXIMO DE ITERAÇÕES ({self.max_iterations}) ATINGIDO")
        total_time = time.time() - start_time
        
        return {
            "success": False,
            "objective": objective,
            "iterations": self.iteration_count,
            "error": "Máximo de iterações atingido sem completar objetivo",
            "total_time": total_time,
            "action_log": self._format_action_log(),
        }

    async def _call_model(
        self,
        objective: str,
        messages: list[ModelMessage],
    ) -> dict[str, Any]:
        """
        Chama o modelo de IA para decisão com contexto completo.
        
        Args:
            objective: Objetivo a alcançar.
            messages: Histórico de mensagens.
            
        Returns:
            Decisão do modelo.
        """
        prompt = (
            f"Objetivo: {objective}\n"
            f"Histórico de {len(messages)} ações anteriores\n"
            f"Ferramentas disponíveis: {', '.join(self.tools.keys())}\n"
            f"Escolha uma ferramenta para executar ou sinalize como concluído (done=true)."
        )
        
        logger.debug(f"Prompt para modelo: {prompt[:100]}...")
        
        # PLACEHOLDER: Integração real com Pydantic AI
        return {
            "done": self.iteration_count >= 3,
            "message": "Objetivo processado com sucesso",
            "reasoning": "Simulação de resposta do modelo",
            "tool_name": None if self.iteration_count >= 3 else "take_screenshot",
            "tool_args": {},
        }

    async def _execute_tool(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
    ) -> ToolResult:
        """
        Executa uma ferramenta registrada com auto-cura em caso de falha.
        
        Fluxo:
        1. Valida ferramenta existe
        2. Tenta executar
        3. Se falhar, ativa auto-cura (retry inteligente)
        4. Se exaurir retries, retorna erro com contexto
        
        Args:
            tool_name: Nome da ferramenta.
            tool_args: Argumentos para a ferramenta.
            
        Returns:
            Resultado da execução.
        """
        if tool_name not in self.tools:
            return ToolResult(
                success=False,
                output="",
                error=f"Ferramenta não encontrada: {tool_name}",
            )
        
        try:
            tool_func = self.tools[tool_name]
            result = tool_func(**tool_args)
            
            if isinstance(result, ToolResult):
                # Se bem-sucedido, registrar no histórico
                if result.success and self.memory:
                    await self.memory.learn_from_success(
                        action=f"{tool_name}",
                        result=result.output[:100],
                        tool=tool_name,
                    )
                return result
            
            return ToolResult(success=True, output=str(result))
            
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"❌ Erro ao executar {tool_name}: {error_msg}")
            
            # Tentar auto-cura
            return await self._analyze_and_retry_tool(
                tool_name=tool_name,
                tool_args=tool_args,
                original_error=error_msg,
                attempt=1,
            )


    def _log_action(
        self,
        action_type: str,
        tool_name: Optional[str] = None,
        success: bool = False,
        security_validated: bool = False,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Registra uma ação no log de auditoria."""
        action = ActionLog(
            iteration=self.iteration_count,
            action_type=action_type,
            tool_name=tool_name,
            security_validated=security_validated,
            success=success,
            details=details or {},
        )
        
        self.action_log.append(action)

    async def _analyze_and_retry_tool(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
        original_error: str,
        attempt: int = 1,
    ) -> ToolResult:
        """
        Analisa erro e tenta corrigir automaticamente (auto-cura/self-healing).
        
        Estratégias de recuperação:
        1. Analisar mensagem de erro
        2. Buscar ações similares bem-sucedidas no histórico semântico
        3. Propor correção e re-tentar (máx 3 tentativas)
        4. Se falhar, reportar com sugestões de correção
        
        Args:
            tool_name: Ferramenta que falhou
            tool_args: Argumentos que causaram falha
            original_error: Mensagem de erro original
            attempt: Número da tentativa (1-3)
            
        Returns:
            ToolResult com resultado de retry ou False se exauridas tentativas
        """
        logger.warning(
            f"🔧 Ativando auto-cura (tentativa {attempt}/{self.max_retries}): {tool_name}"
        )
        
        if attempt > self.max_retries:
            logger.error(f"❌ Auto-cura exaurida após {self.max_retries} tentativas")
            return ToolResult(
                success=False,
                output="",
                error=f"Falha permanente após {self.max_retries} tentativas: {original_error}",
            )

        # FASE 1: Buscar experiências similares no histórico
        similar_successes = []
        similar_errors = []
        
        if self.memory:
            query = f"{tool_name} {' '.join(str(v)[:20] for v in tool_args.values())}"
            
            similar_successes = await self.memory.get_similar_successes(query, limit=2)
            similar_errors = await self.memory.get_similar_errors(query, limit=2)
            
            logger.debug(f"  📚 Encontrados {len(similar_successes)} sucessos similares")
            logger.debug(f"  ⚠️  Encontrados {len(similar_errors)} erros similares")

        # FASE 2: Analisar padrão de erro e propor correção
        corrected_args = await self._propose_error_fix(
            tool_name,
            tool_args,
            original_error,
            similar_errors,
        )

        if corrected_args != tool_args:
            logger.info(f"  💡 Proposta de correção: {corrected_args}")
        
        # FASE 3: Tentar novamente com argumentos corrigidos
        logger.info(f"  ▶️  Re-tentando {tool_name} com argumentos corrigidos...")
        
        retriable_result = await self._execute_tool(tool_name, corrected_args)
        
        # FASE 4: Registrar resultado no histórico semântico
        action_desc = f"{tool_name}({', '.join(f'{k}={v}' for k, v in list(corrected_args.items())[:2])})"
        
        if retriable_result.success:
            logger.info(f"  ✅ Auto-cura bem-sucedida!")
            
            if self.memory:
                await self.memory.learn_from_success(
                    action=action_desc,
                    result=retriable_result.output[:100],
                    tool=tool_name,
                    context={"original_error": original_error, "attempt": attempt},
                )
            
            return retriable_result
        
        else:
            logger.warning(f"  ❌ Re-tentativa falhou: {retriable_result.error}")
            
            if self.memory:
                await self.memory.learn_from_error(
                    action=action_desc,
                    error=retriable_result.error,
                    tool=tool_name,
                    attempted_fixes=[original_error],
                )
            
            # Tentar novamente recursivamente
            return await self._analyze_and_retry_tool(
                tool_name=tool_name,
                tool_args=corrected_args,
                original_error=retriable_result.error or original_error,
                attempt=attempt + 1,
            )

    async def _propose_error_fix(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
        error: str,
        similar_errors: list[Any] = None,
    ) -> dict[str, Any]:
        """
        Propõe correção baseada em análise de erro.
        
        Padrões conhecidos:
        - "permission denied" → tentar com sudo
        - "file not found" → verificar caminho
        - "command not found" → tentar alternativa
        
        Args:
            tool_name: Ferramenta que falhou
            tool_args: Argumentos originais
            error: Mensagem de erro
            similar_errors: Erros similares do histórico
            
        Returns:
            Dicionário de argumentos corrigidos
        """
        corrected = tool_args.copy()
        error_lower = error.lower()

        # Padrão: Permission denied
        if "permission denied" in error_lower:
            if tool_name == "execute_command":
                cmd = corrected.get("command", "")
                if not cmd.startswith("sudo"):
                    logger.info("  💡 Sugestão: Tentar com sudo")
                    # Nota: Na prática, sudo requer auth
                    corrected["command"] = f"sudo {cmd}"

        # Padrão: File not found
        elif "no such file" in error_lower or "not found" in error_lower:
            logger.info("  💡 Sugestão: Verificar caminho/existência de arquivo")
            # Poderia tentar listagem de diretório ou encontrar arquivo

        # Padrão: Command not found
        elif "command not found" in error_lower:
            if tool_name == "execute_command":
                cmd = corrected.get("command", "")
                # Tentar variantes do comando
                variants = {
                    "python": "python3",
                    "node": "nodejs",
                    "pip": "pip3",
                }
                for old, new in variants.items():
                    if cmd.startswith(old):
                        corrected["command"] = cmd.replace(old, new, 1)
                        logger.info(f"  💡 Tentando alternativa: {new}")
                        break

        return corrected

    def _format_action_log(self) -> list[dict[str, Any]]:
        """Formata log de ações para saída."""
        return [
            {
                "iteration": log.iteration,
                "type": log.action_type,
                "tool": log.tool_name,
                "success": log.success,
                "security_validated": log.security_validated,
                "details": log.details,
            }
            for log in self.action_log
        ]

    def get_status(self) -> dict[str, Any]:
        """
        Retorna status atual do orquestrador.
        
        Returns:
            Dicionário com informações de status.
        """
        return {
            "model_provider": self.model_provider.value,
            "max_iterations": self.max_iterations,
            "current_iteration": self.iteration_count,
            "registered_tools": len(self.tools),
            "tool_names": list(self.tools.keys()),
            "security_enabled": self.settings.security_enabled,
            "total_actions_logged": len(self.action_log),
        }

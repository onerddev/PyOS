"""
Terminal Dashboard using Rich library.

Provides real-time telemetry visualization with multiple panels:
- [PENSAMENTO DA IA] - AI reasoning and decisions
- [AÇÃO EXECUTADA] - Current tool execution
- [STATUS DE SEGURANÇA] - Security validation status
- [MEMÓRIA RECALCADA] - Semantic memory recalls and learning
"""

from typing import Optional, Any
from dataclasses import dataclass
from datetime import datetime

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.layout import Layout
    from rich.live import Live
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.text import Text
    from rich.columns import Columns
except ImportError:
    raise ImportError("Rich library required. Install with: pip install rich")

from loguru import logger


@dataclass
class DashboardState:
    """Current state of dashboard metrics."""
    ai_reasoning: str = "Aguardando..."
    ai_tool_decision: str = ""
    current_tool: str = ""
    tool_status: str = "idle"
    tool_progress: float = 0.0
    security_status: str = "✅ OK"
    security_violations: int = 0
    memory_recall_count: int = 0
    memory_entries: int = 0
    last_memory_recall: str = ""
    iterations: int = 0
    total_actions: int = 0
    execution_time: float = 0.0


class RichDashboard:
    """
    Terminal dashboard for PyOS-Agent telemetry.
    
    Displays 4 panels:
    1. AI Thoughts (reasoning, decisions)
    2. Tool Execution (current action, progress)
    3. Security Status (validations, violations)
    4. Memory Status (recalls, learning)
    """

    def __init__(self, width: int = 200, height: int = 30, update_interval: float = 0.5):
        """
        Initialize dashboard.
        
        Args:
            width: Console width
            height: Console height  
            update_interval: Refresh rate in seconds
        """
        self.console = Console(width=width, height=height, force_terminal=True)
        self.update_interval = update_interval
        self.state = DashboardState()
        self.is_running = False
        self.live: Optional[Live] = None

    def update_ai_reasoning(self, reasoning: str) -> None:
        """Update AI reasoning panel."""
        self.state.ai_reasoning = reasoning[:200]

    def update_ai_decision(self, tool: str, reasoning: str = "") -> None:
        """Update AI tool decision."""
        self.state.ai_tool_decision = f"{tool}"
        if reasoning:
            self.state.ai_reasoning = reasoning[:200]
        self.state.current_tool = tool

    def update_tool_status(self, tool: str, status: str, progress: float = 0.0) -> None:
        """Update tool execution status."""
        self.state.current_tool = tool
        self.state.tool_status = status
        self.state.tool_progress = progress

    def update_security_status(self, is_safe: bool, violations: int = 0) -> None:
        """Update security status."""
        if is_safe:
            self.state.security_status = "✅ SEGURO"
        else:
            self.state.security_status = f"🚫 VIOLAÇÃO ({violations})"
        self.state.security_violations = violations

    def update_memory_recall(self, recall_count: int, total_entries: int, last_recall: str = "") -> None:
        """Update memory recall status."""
        self.state.memory_recall_count = recall_count
        self.state.memory_entries = total_entries
        self.state.last_memory_recall = last_recall[:100] if last_recall else ""

    def update_metrics(
        self,
        iterations: int,
        total_actions: int,
        execution_time: float,
    ) -> None:
        """Update general metrics."""
        self.state.iterations = iterations
        self.state.total_actions = total_actions
        self.state.execution_time = execution_time

    def _build_layout(self) -> Layout:
        """Build dashboard layout with 4 panels."""
        layout = Layout(name="root")
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=2),
        )

        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right"),
        )

        layout["left"].split_column(
            Layout(name="ai", size=15),
            Layout(name="tool", size=15),
        )

        layout["right"].split_column(
            Layout(name="security", size=15),
            Layout(name="memory", size=15),
        )

        return layout

    def _render_header(self) -> Panel:
        """Render header panel with title and metrics."""
        header_text = Text()
        header_text.append("🤖 PyOS-Agent ", style="bold blue")
        header_text.append("│ ", style="dim")
        header_text.append(f"Iteração {self.state.iterations} ", style="yellow")
        header_text.append("│ ", style="dim")
        header_text.append(f"{self.state.total_actions} ações ", style="cyan")
        header_text.append("│ ", style="dim")
        header_text.append(f"{self.state.execution_time:.1f}s", style="green")

        return Panel(
            header_text,
            border_style="blue",
            padding=(0, 1),
        )

    def _render_ai_panel(self) -> Panel:
        """Render AI thoughts panel."""
        ai_text = Text()
        ai_text.append("Raciocínio:\n", style="bold cyan")
        ai_text.append(self.state.ai_reasoning, style="white")
        
        if self.state.ai_tool_decision:
            ai_text.append("\n\n", style="")
            ai_text.append("Decisão:\n", style="bold yellow")
            ai_text.append(f"→ {self.state.ai_tool_decision}", style="bright_yellow")

        return Panel(
            ai_text,
            title="[PENSAMENTO DA IA]",
            border_style="cyan",
            padding=(1, 2),
        )

    def _render_tool_panel(self) -> Panel:
        """Render tool execution panel."""
        tool_text = Text()
        
        if self.state.current_tool:
            tool_text.append(f"Ferramenta: {self.state.current_tool}\n", style="bold green")
            tool_text.append(f"Status: {self.state.tool_status}\n", style="yellow")
            
            # Progress bar
            progress_pct = int(self.state.tool_progress * 100)
            progress_bar = "█" * int(progress_pct / 5) + "░" * (20 - int(progress_pct / 5))
            tool_text.append(f"[{progress_bar}] {progress_pct}%", style="green")
        else:
            tool_text.append("Nenhuma ferramenta em execução", style="dim")

        return Panel(
            tool_text,
            title="[AÇÃO EXECUTADA]",
            border_style="green",
            padding=(1, 2),
        )

    def _render_security_panel(self) -> Panel:
        """Render security status panel."""
        security_text = Text()
        
        status_style = "green" if "SEGURO" in self.state.security_status else "red"
        security_text.append(f"{self.state.security_status}\n", style=f"bold {status_style}")
        
        security_text.append(f"Violações: {self.state.security_violations}\n", style="yellow")
        security_text.append("AllowList ✓\n", style="dim")
        security_text.append("AST Analyzer ✓\n", style="dim")
        security_text.append("Approval Manager ✓", style="dim")

        return Panel(
            security_text,
            title="[STATUS DE SEGURANÇA]",
            border_style=status_style,
            padding=(1, 2),
        )

    def _render_memory_panel(self) -> Panel:
        """Render memory status panel."""
        memory_text = Text()
        
        memory_text.append(f"Entradas: {self.state.memory_entries}\n", style="bold cyan")
        memory_text.append(f"Recalls: {self.state.memory_recall_count}\n", style="yellow")
        
        if self.state.last_memory_recall:
            memory_text.append("\nÚltimo Recall:\n", style="dim")
            memory_text.append(f"→ {self.state.last_memory_recall}", style="white")

        return Panel(
            memory_text,
            title="[MEMÓRIA RECALCADA]",
            border_style="magenta",
            padding=(1, 2),
        )

    def _render_footer(self) -> Panel:
        """Render footer with timestamp and status."""
        footer_text = Text()
        footer_text.append(f"🕐 {datetime.now().strftime('%H:%M:%S')}", style="dim")
        footer_text.append(" │ ", style="dim")
        footer_text.append("Press Ctrl+C to stop", style="dim")

        return Panel(
            footer_text,
            border_style="dim",
            padding=(0, 1),
        )

    def _generate_screen(self) -> Layout:
        """Generate complete dashboard layout."""
        layout = self._build_layout()

        # Fill panels
        layout["header"].update(self._render_header())
        layout["ai"].update(self._render_ai_panel())
        layout["tool"].update(self._render_tool_panel())
        layout["security"].update(self._render_security_panel())
        layout["memory"].update(self._render_memory_panel())
        layout["footer"].update(self._render_footer())

        return layout

    def start(self) -> None:
        """Start live dashboard."""
        self.is_running = True
        try:
            self.live = Live(
                self._generate_screen(),
                console=self.console,
                refresh_per_second=1 / self.update_interval,
            )
            self.live.start()
            logger.info("Dashboard Rich iniciado")
        except Exception as e:
            logger.error(f"Erro ao iniciar dashboard: {e}")
            self.is_running = False

    def update(self) -> None:
        """Update dashboard display."""
        if self.live and self.is_running:
            try:
                self.live.update(self._generate_screen())
            except Exception as e:
                logger.error(f"Erro ao atualizar dashboard: {e}")

    def stop(self) -> None:
        """Stop live dashboard."""
        if self.live:
            self.live.stop()
        self.is_running = False
        logger.info("Dashboard Rich parado")

    def print_summary(self) -> None:
        """Print final execution summary."""
        if not self.is_running:
            return

        self.console.print("\n")
        self.console.rule("[bold green]Resumo da Execução[/bold green]")
        
        table = Table(title="Métricas Finais")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="green")
        
        table.add_row("Iterações", str(self.state.iterations))
        table.add_row("Ações Executadas", str(self.state.total_actions))
        table.add_row("Tempo Total", f"{self.state.execution_time:.2f}s")
        table.add_row("Violações de Segurança", str(self.state.security_violations))
        table.add_row("Memória - Entradas", str(self.state.memory_entries))
        table.add_row("Memória - Recalls", str(self.state.memory_recall_count))
        
        self.console.print(table)


# Global dashboard instance
_dashboard: Optional[RichDashboard] = None


def get_dashboard() -> RichDashboard:
    """Get or create global dashboard instance."""
    global _dashboard
    if _dashboard is None:
        _dashboard = RichDashboard()
    return _dashboard


async def dashboard_context():
    """Async context manager for dashboard lifecycle."""
    dashboard = get_dashboard()
    dashboard.start()
    try:
        yield dashboard
    finally:
        dashboard.stop()
        dashboard.print_summary()

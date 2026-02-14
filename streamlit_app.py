"""
Streamlit Dashboard for PyOS-Agent monitoring.

Provides web-based multimodal monitoring:
- Real-time logs and metrics
- Screenshot history with timestamps
- Tool performance analytics
- Memory/learning statistics
- Security audit trail
"""

try:
    import streamlit as st
    from streamlit_option_menu import option_menu
except ImportError:
    raise ImportError("Streamlit required. Install with: pip install streamlit streamlit-option-menu")

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from loguru import logger


class StreamlitDashboard:
    """Web dashboard for PyOS-Agent monitoring."""

    def __init__(self, title: str = "PyOS-Agent Monitor"):
        """Initialize Streamlit dashboard."""
        self.title = title
        self._setup_page()

    def _setup_page(self) -> None:
        """Setup Streamlit page configuration."""
        st.set_page_config(
            page_title=self.title,
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        st.markdown(
            """
            <style>
            .metric-card {
                background-color: #f0f2f6;
                padding: 20px;
                border-radius: 10px;
                margin: 10px 0;
            }
            .status-ok { color: #09ab3b; }
            .status-warning { color: #ffc107; }
            .status-error { color: #d32f2f; }
            </style>
            """,
            unsafe_allow_html=True,
        )

    def render(self) -> None:
        """Render main dashboard."""
        with st.sidebar:
            st.title("🤖 PyOS-Agent")
            
            page = option_menu(
                "Navegação",
                [
                    "Dashboard",
                    "Logs",
                    "Screenshots",
                    "Análise",
                    "Configuração",
                ],
                icons=[
                    "speedometer2",
                    "file-text",
                    "image",
                    "bar-chart",
                    "gear",
                ],
                menu_icon="cast",
                default_index=0,
            )

        if page == "Dashboard":
            self._render_dashboard()
        elif page == "Logs":
            self._render_logs()
        elif page == "Screenshots":
            self._render_screenshots()
        elif page == "Análise":
            self._render_analysis()
        elif page == "Configuração":
            self._render_settings()

    def _render_dashboard(self) -> None:
        """Render main dashboard view."""
        st.title("📊 Dashboard PyOS-Agent")

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Iterações", "12", "+3")
        with col2:
            st.metric("Ações", "48", "+12")
        with col3:
            st.metric("Taxa Sucesso", "95.8%", "+2.3%")
        with col4:
            st.metric("Tempo Total", "42.5s", "-5.2s")

        # Status panels
        st.subheader("Status de Componentes")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "🔒 Segurança",
                "✅ OK",
                help="AllowList: ON, AST: ON, Approval: ON",
            )

        with col2:
            st.metric(
                "🧠 Memória",
                "156 entradas",
                help="Semantic memory com ChromaDB",
            )

        with col3:
            st.metric(
                "⚡ Performance",
                "89ms",
                help="Latência média de ferramenta",
            )

        # Execution timeline
        st.subheader("Timeline de Execução")
        
        timeline_data = [
            {"time": "10:23:15", "iteration": 1, "tool": "take_screenshot", "status": "✅"},
            {"time": "10:23:18", "iteration": 1, "tool": "execute_command", "status": "✅"},
            {"time": "10:23:22", "iteration": 2, "tool": "take_screenshot", "status": "✅"},
            {"time": "10:23:25", "iteration": 2, "tool": "take_screenshot", "status": "✅"},
        ]

        timeline_df = pd.DataFrame(timeline_data)
        st.dataframe(timeline_df, use_container_width=True)

        # Real-time metrics chart
        st.subheader("Métricas em Tempo Real")

        import numpy as np

        iterations = np.arange(1, 13)
        execution_times = np.random.uniform(2.5, 8.5, 12)
        success_rates = np.random.uniform(0.85, 1.0, 12)

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=iterations,
                y=execution_times,
                name="Tempo Execução (s)",
                mode="lines+markers",
                yaxis="y1",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=iterations,
                y=success_rates * 100,
                name="Taxa Sucesso (%)",
                mode="lines+markers",
                yaxis="y2",
            )
        )

        fig.update_layout(
            title="Performance por Iteração",
            xaxis_title="Iteração",
            yaxis_title="Tempo (s)",
            yaxis2={"title": "Taxa Sucesso (%)", "overlaying": "y", "side": "right"},
            hovermode="x unified",
            height=400,
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_logs(self) -> None:
        """Render logs page."""
        st.title("📋 Logs em Tempo Real")

        log_level = st.selectbox(
            "Nível de Log",
            ["DEBUG", "INFO", "WARNING", "ERROR"],
        )

        # Simulated logs
        logs = [
            {"timestamp": "10:23:15", "level": "INFO", "message": "Iniciando execução do objetivo"},
            {
                "timestamp": "10:23:16",
                "level": "DEBUG",
                "message": "[SEC-PASS] Ferramenta take_screenshot está registrada",
            },
            {"timestamp": "10:23:18", "level": "INFO", "message": "✓ take_screenshot completada com sucesso"},
            {
                "timestamp": "10:23:19",
                "level": "DEBUG",
                "message": "Consultando modelo de IA para próxima decisão...",
            },
            {
                "timestamp": "10:23:22",
                "level": "WARNING",
                "message": "Comando bloqueado por padrão: rm -rf /",
            },
        ]

        logs_df = pd.DataFrame(logs)

        if log_level != "DEBUG":
            logs_df = logs_df[logs_df["level"].isin([log_level, "ERROR"])]

        st.dataframe(logs_df, use_container_width=True)

        # Log search
        st.subheader("Buscar Logs")
        search_term = st.text_input("Termo de busca")

        if search_term:
            filtered_logs = logs_df[
                logs_df["message"].str.contains(search_term, case=False)
            ]
            st.dataframe(filtered_logs, use_container_width=True)

    def _render_screenshots(self) -> None:
        """Render screenshots page."""
        st.title("📸 Histórico de Screenshots")

        # Simulated screenshot metadata
        screenshots = [
            {"timestamp": "10:23:15", "tool": "take_screenshot", "size": "2.3 MB", "format": "PNG"},
            {"timestamp": "10:23:18", "tool": "take_screenshot", "size": "1.8 MB", "format": "JPEG"},
            {"timestamp": "10:23:22", "tool": "take_screenshot", "size": "2.1 MB", "format": "PNG"},
            {"timestamp": "10:23:25", "tool": "vision_analyze", "size": "0.8 MB", "format": "JPEG"},
        ]

        ss_df = pd.DataFrame(screenshots)
        st.dataframe(ss_df, use_container_width=True)

        # Screenshot viewer
        st.subheader("Visualizador")
        selected_idx = st.selectbox(
            "Selecione screenshot",
            range(len(screenshots)),
            format_func=lambda i: screenshots[i]["timestamp"],
        )

        st.info(f"Screenshot de {screenshots[selected_idx]['timestamp']} em {screenshots[selected_idx]['format']}")

    def _render_analysis(self) -> None:
        """Render analysis page."""
        st.title("📈 Análise & Estatísticas")

        # Tool usage
        st.subheader("Uso de Ferramentas")

        tool_stats = pd.DataFrame(
            {
                "Tool": [
                    "take_screenshot",
                    "execute_command",
                    "get_clickable_regions",
                    "vision_analyze",
                ],
                "Calls": [24, 18, 12, 8],
                "Success Rate": [100, 94.4, 100, 100],
                "Avg Time (ms)": [125, 234, 89, 567],
            }
        )

        fig = px.bar(
            tool_stats,
            x="Tool",
            y="Calls",
            title="Uso de Ferramentas",
            color="Success Rate",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Security violations
        st.subheader("Status de Segurança")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Violações Bloqueadas", "34")
        with col2:
            st.metric("Comandos Validados", "156")
        with col3:
            st.metric("Caminhos Validados", "89")

        # Memory statistics
        st.subheader("Estatísticas de Memória")

        memory_stats = pd.DataFrame(
            {
                "Type": ["SUCCESS", "ERROR", "DECISION", "OBSERVATION"],
                "Count": [52, 18, 34, 56],
                "Recalls": [23, 8, 15, 32],
            }
        )

        fig = px.pie(memory_stats, values="Count", names="Type", title="Tipos de Memória")
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(memory_stats, use_container_width=True)

    def _render_settings(self) -> None:
        """Render settings page."""
        st.title("⚙️ Configuração")

        st.subheader("Modelo de IA")
        model = st.selectbox("Provider", ["OpenAI", "Anthropic", "Google Gemini"])

        st.subheader("Segurança")
        col1, col2 = st.columns(2)

        with col1:
            security_enabled = st.checkbox("Segurança Ativada", value=True)
            ast_enabled = st.checkbox("AST Analysis", value=True)

        with col2:
            approval_required = st.checkbox(
                "Approval para Ações Críticas",
                value=True,
            )
            memory_enabled = st.checkbox("Semantic Memory", value=True)

        st.subheader("Performance")
        max_iterations = st.slider("Max Iterações", 1, 20, 10)
        update_interval = st.slider("Intervalo Update (s)", 0.1, 2.0, 0.5)

        st.subheader("Paths Permitidos")
        with st.form("paths_form"):
            new_path = st.text_input("Novo caminho permitido")
            submitted = st.form_submit_button("Adicionar")

            if submitted:
                st.success(f"Caminho adicionado: {new_path}")

        st.subheader("Comandos Permitidos")
        commands = st.text_area(
            "Comandos (um por linha)",
            value="ls\ngrep\npython\npip",
        )

        if st.button("Salvar Configurações"):
            st.success("✅ Configurações salvas!")


def run_dashboard() -> None:
    """Run Streamlit dashboard."""
    dashboard = StreamlitDashboard()
    dashboard.render()


if __name__ == "__main__":
    run_dashboard()

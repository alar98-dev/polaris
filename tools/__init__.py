"""POLARIS Tools - Function calling para LLMs.

Este módulo contém todas as ferramentas (tools) disponíveis para o agente POLARIS.
Cada ferramenta tem:
- tool.json: definição OpenAI function calling format
- function.py: implementação Python
"""

import os
import json
from typing import Dict, List, Any, Callable

# Importar todas as funções
from .create_session.function import create_session
from .health_check.function import health_check
from .ask_discovery.function import ask_discovery
from .select_portfolio.function import select_portfolio
from .generate_prototype.function import generate_prototype
from .generate_mock.function import generate_mock
from .estimate_development.function import estimate_development
from .fetch_web.function import fetch_web
from .search_google.function import search_google


def load_tool_definition(tool_name: str) -> Dict[str, Any]:
    """Carrega a definição JSON de uma tool."""
    tool_path = os.path.join(os.path.dirname(__file__), tool_name, 'tool.json')
    with open(tool_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_all_tools() -> List[Dict[str, Any]]:
    """Retorna todas as definições de tools para enviar ao LLM."""
    tools = [
        'create_session',
        'health_check',
        'ask_discovery',
        'select_portfolio',
        'generate_prototype',
        'generate_mock',
        'estimate_development',
        'fetch_web',
        'search_google'
    ]
    return [load_tool_definition(tool) for tool in tools]


def get_tool_function(tool_name: str) -> Callable:
    """Retorna a função Python correspondente ao nome da tool."""
    mapping = {
        'create_session': create_session,
        'health_check': health_check,
        'ask_discovery': ask_discovery,
        'select_portfolio': select_portfolio,
        'generate_prototype': generate_prototype,
        'generate_mock': generate_mock,
        'estimate_development': estimate_development,
        'fetch_web': fetch_web,
        'search_google': search_google,
    }
    return mapping.get(tool_name)


__all__ = [
    'create_session',
    'health_check',
    'ask_discovery',
    'select_portfolio',
    'generate_prototype',
    'generate_mock',
    'estimate_development',
    'fetch_web',
    'search_google',
    'get_all_tools',
    'get_tool_function',
    'load_tool_definition',
]

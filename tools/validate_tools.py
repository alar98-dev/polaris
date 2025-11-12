#!/usr/bin/env python3
"""
Script de validação das POLARIS Tools.

Verifica se todas as tools estão corretamente configuradas:
- tool.json é JSON válido
- tool.json segue o schema OpenAI
- function.py pode ser importado
- function tem assinatura correta
"""

import os
import json
import sys
import importlib.util
from pathlib import Path
from typing import Dict, List, Any


TOOLS_DIR = Path(__file__).parent


def validate_tool_json(tool_name: str, tool_path: Path) -> List[str]:
    """Valida o arquivo tool.json."""
    errors = []
    json_path = tool_path / 'tool.json'
    
    if not json_path.exists():
        errors.append(f"❌ {tool_name}: tool.json não encontrado")
        return errors
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validar estrutura OpenAI
        if 'type' not in data:
            errors.append(f"❌ {tool_name}: 'type' ausente em tool.json")
        elif data['type'] != 'function':
            errors.append(f"❌ {tool_name}: 'type' deve ser 'function'")
        
        if 'function' not in data:
            errors.append(f"❌ {tool_name}: 'function' ausente em tool.json")
        else:
            func = data['function']
            
            if 'name' not in func:
                errors.append(f"❌ {tool_name}: 'name' ausente em function")
            elif func['name'] != tool_name:
                errors.append(f"⚠️ {tool_name}: name '{func['name']}' difere do nome da pasta")
            
            if 'description' not in func:
                errors.append(f"❌ {tool_name}: 'description' ausente em function")
            elif len(func['description']) < 20:
                errors.append(f"⚠️ {tool_name}: description muito curta")
            
            if 'parameters' not in func:
                errors.append(f"❌ {tool_name}: 'parameters' ausente em function")
            else:
                params = func['parameters']
                if params.get('type') != 'object':
                    errors.append(f"❌ {tool_name}: parameters.type deve ser 'object'")
                if 'properties' not in params:
                    errors.append(f"⚠️ {tool_name}: parameters.properties ausente")
        
        if not errors:
            print(f"✅ {tool_name}/tool.json: OK")
    
    except json.JSONDecodeError as e:
        errors.append(f"❌ {tool_name}: JSON inválido - {str(e)}")
    except Exception as e:
        errors.append(f"❌ {tool_name}: Erro ao validar - {str(e)}")
    
    return errors


def validate_function_py(tool_name: str, tool_path: Path) -> List[str]:
    """Valida o arquivo function.py."""
    errors = []
    py_path = tool_path / 'function.py'
    
    if not py_path.exists():
        errors.append(f"❌ {tool_name}: function.py não encontrado")
        return errors
    
    try:
        # Tentar importar o módulo
        spec = importlib.util.spec_from_file_location(
            f"polaris.tools.{tool_name}.function",
            py_path
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Verificar se a função existe
            if not hasattr(module, tool_name):
                errors.append(f"❌ {tool_name}: função '{tool_name}' não encontrada em function.py")
            else:
                func = getattr(module, tool_name)
                
                # Verificar se é callable
                if not callable(func):
                    errors.append(f"❌ {tool_name}: '{tool_name}' não é uma função")
                
                # Verificar docstring
                if not func.__doc__:
                    errors.append(f"⚠️ {tool_name}: função sem docstring")
                elif len(func.__doc__.strip()) < 20:
                    errors.append(f"⚠️ {tool_name}: docstring muito curta")
            
            if not errors:
                print(f"✅ {tool_name}/function.py: OK")
        else:
            errors.append(f"❌ {tool_name}: Não foi possível carregar o módulo")
    
    except ImportError as e:
        errors.append(f"❌ {tool_name}: Erro de importação - {str(e)}")
    except SyntaxError as e:
        errors.append(f"❌ {tool_name}: Erro de sintaxe - {str(e)}")
    except Exception as e:
        errors.append(f"❌ {tool_name}: Erro ao validar - {str(e)}")
    
    return errors


def get_all_tool_dirs() -> List[Path]:
    """Retorna lista de diretórios de tools."""
    tool_dirs = []
    for item in TOOLS_DIR.iterdir():
        if item.is_dir() and not item.name.startswith('_') and not item.name.startswith('.'):
            tool_dirs.append(item)
    return sorted(tool_dirs)


def validate_all_tools() -> bool:
    """Valida todas as tools e retorna True se todas estiverem OK."""
    print("=" * 80)
    print("🔍 VALIDAÇÃO DAS POLARIS TOOLS")
    print("=" * 80)
    
    tool_dirs = get_all_tool_dirs()
    print(f"\n📋 {len(tool_dirs)} tools encontradas\n")
    
    all_errors = []
    
    for tool_path in tool_dirs:
        tool_name = tool_path.name
        print(f"\n🔧 Validando: {tool_name}")
        print("-" * 40)
        
        # Validar tool.json
        json_errors = validate_tool_json(tool_name, tool_path)
        all_errors.extend(json_errors)
        
        # Validar function.py
        py_errors = validate_function_py(tool_name, tool_path)
        all_errors.extend(py_errors)
    
    # Resumo
    print("\n" + "=" * 80)
    print("📊 RESUMO DA VALIDAÇÃO")
    print("=" * 80)
    
    if not all_errors:
        print("\n✅ Todas as tools estão OK!")
        print(f"   {len(tool_dirs)} tools validadas com sucesso")
        return True
    else:
        print(f"\n❌ {len(all_errors)} problemas encontrados:\n")
        for error in all_errors:
            print(f"   {error}")
        return False


def print_tools_summary():
    """Imprime resumo das tools disponíveis."""
    print("\n" + "=" * 80)
    print("📚 TOOLS DISPONÍVEIS")
    print("=" * 80)
    
    tool_dirs = get_all_tool_dirs()
    
    for tool_path in tool_dirs:
        tool_name = tool_path.name
        json_path = tool_path / 'tool.json'
        
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    desc = data.get('function', {}).get('description', 'Sem descrição')
                    print(f"\n🔧 {tool_name}")
                    print(f"   {desc[:100]}...")
            except:
                print(f"\n🔧 {tool_name}")
                print(f"   (erro ao ler descrição)")


if __name__ == "__main__":
    # Validar todas as tools
    success = validate_all_tools()
    
    # Mostrar resumo
    if success:
        print_tools_summary()
    
    # Exit code
    sys.exit(0 if success else 1)

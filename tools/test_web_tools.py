#!/usr/bin/env python3
"""
Exemplo de uso das tools fetch_web e search_google.

Demonstra como o POLARIS pode buscar informações na web.
"""

import asyncio
import os
import pytest
from polaris.agent import PolarisAgent
from polaris.tools.fetch_web.function import fetch_web
from polaris.tools.search_google.function import search_google


@pytest.mark.asyncio
async def test_fetch_web():
    """Testa a tool fetch_web."""
    print("=" * 80)
    print("🌐 TESTE: fetch_web")
    print("=" * 80)
    
    agent = PolarisAgent()
    
    # Teste 1: Buscar página simples
    print("\n1️⃣ Buscando página de exemplo...")
    result = await fetch_web(
        agent,
        url="https://example.com",
        max_length=1000
    )
    
    if result['success']:
        print(f"✅ Título: {result['title']}")
        print(f"✅ Tamanho do conteúdo: {result['content_length']} chars")
        print(f"✅ Preview: {result['content'][:200]}...")
    else:
        print(f"❌ Erro: {result['error']}")
    
    # Teste 2: Buscar com extração de links
    print("\n2️⃣ Buscando página com links...")
    result = await fetch_web(
        agent,
        url="https://news.ycombinator.com",
        extract_links=True,
        max_length=2000
    )
    
    if result['success']:
        print(f"✅ Título: {result['title']}")
        print(f"✅ Links encontrados: {len(result.get('links', []))}")
        if result.get('links'):
            print("   Primeiros 3 links:")
            for link in result['links'][:3]:
                print(f"   - {link['text'][:50]}: {link['url']}")
    else:
        print(f"❌ Erro: {result['error']}")
    
    # Teste 3: URL inválida
    print("\n3️⃣ Testando validação de URL...")
    result = await fetch_web(
        agent,
        url="invalid-url"
    )
    
    if not result['success']:
        print(f"✅ Validação funcionando: {result['error']}")


@pytest.mark.asyncio
async def test_search_google():
    """Testa a tool search_google."""
    print("\n\n" + "=" * 80)
    print("🔍 TESTE: search_google")
    print("=" * 80)
    
    agent = PolarisAgent()
    
    # Verificar API keys
    serper_key = os.getenv('SERPER_API_KEY')
    google_key = os.getenv('GOOGLE_API_KEY')
    
    if serper_key:
        print("✅ SERPER_API_KEY configurada")
    elif google_key:
        print("✅ GOOGLE_API_KEY configurada")
    else:
        print("⚠️ Nenhuma API key configurada - usando scraping básico")
        print("   Para melhores resultados, configure:")
        print("   export SERPER_API_KEY='sua-chave'  # Recomendado")
        print("   ou")
        print("   export GOOGLE_API_KEY='sua-chave'")
        print("   export GOOGLE_CX='seu-cx'")
    
    # Teste 1: Busca simples
    print("\n1️⃣ Buscando 'Python web frameworks'...")
    result = await search_google(
        agent,
        query="Python web frameworks",
        num_results=3
    )
    
    if result['success']:
        print(f"✅ Query: {result['query']}")
        print(f"✅ Total de resultados: {result['total_results']}")
        print(f"✅ Fonte: {result.get('source', 'unknown')}")
        
        for r in result['results']:
            print(f"\n   {r['position']}. {r['title']}")
            print(f"      {r['url']}")
            print(f"      {r['snippet'][:100]}...")
    else:
        print(f"❌ Erro: {result['error']}")
        if 'suggestion' in result:
            print(f"💡 Sugestão: {result['suggestion']}")
    
    # Teste 2: Busca com filtro temporal
    print("\n2️⃣ Buscando 'AI news' (última semana)...")
    result = await search_google(
        agent,
        query="artificial intelligence news",
        num_results=3,
        time_range="week",
        language="en"
    )
    
    if result['success']:
        print(f"✅ Encontrou {result['total_results']} resultados")
        for r in result['results'][:2]:
            print(f"   - {r['title'][:60]}...")
    else:
        print(f"❌ Erro: {result['error']}")
    
    # Teste 3: Busca em português
    print("\n3️⃣ Buscando 'frameworks javascript' em português...")
    result = await search_google(
        agent,
        query="frameworks javascript modernos",
        num_results=3,
        language="pt"
    )
    
    if result['success']:
        print(f"✅ Encontrou {result['total_results']} resultados")
        for r in result['results'][:2]:
            print(f"   - {r['title']}")
    else:
        print(f"❌ Erro: {result['error']}")


@pytest.mark.asyncio
async def test_integration_scenario():
    """Testa cenário de integração: buscar + fetch."""
    print("\n\n" + "=" * 80)
    print("🔄 TESTE: Integração search + fetch")
    print("=" * 80)
    
    agent = PolarisAgent()
    
    # Cenário: Cliente pergunta sobre React
    query = "React documentation"
    
    print(f"\n📝 Cenário: Cliente pergunta sobre '{query}'")
    print("   1. Buscar no Google")
    print("   2. Pegar o primeiro resultado")
    print("   3. Buscar conteúdo da página")
    
    # 1. Buscar no Google
    print("\n🔍 Passo 1: Buscando no Google...")
    search_result = await search_google(
        agent,
        query=query,
        num_results=3
    )
    
    if not search_result['success']:
        print(f"❌ Busca falhou: {search_result['error']}")
        return
    
    print(f"✅ Encontrou {len(search_result['results'])} resultados")
    
    # 2. Pegar primeiro resultado
    if search_result['results']:
        first_result = search_result['results'][0]
        print(f"\n📄 Passo 2: Primeiro resultado:")
        print(f"   Título: {first_result['title']}")
        print(f"   URL: {first_result['url']}")
        
        # 3. Buscar conteúdo
        print(f"\n🌐 Passo 3: Buscando conteúdo da página...")
        fetch_result = await fetch_web(
            agent,
            url=first_result['url'],
            max_length=2000
        )
        
        if fetch_result['success']:
            print(f"✅ Conteúdo obtido ({fetch_result['content_length']} chars)")
            print(f"\n   Preview do conteúdo:")
            print(f"   {fetch_result['content'][:300]}...")
        else:
            print(f"❌ Erro ao buscar conteúdo: {fetch_result['error']}")


async def main():
    """Executar todos os testes."""
    
    print("\n" + "🌟" * 40)
    print("TESTES DAS NOVAS TOOLS: fetch_web & search_google")
    print("🌟" * 40)
    
    try:
        await test_fetch_web()
        await test_search_google()
        await test_integration_scenario()
        
        print("\n\n" + "=" * 80)
        print("✅ TODOS OS TESTES CONCLUÍDOS")
        print("=" * 80)
        
        print("\n💡 DICAS DE USO:")
        print("   - fetch_web: Buscar conteúdo de URLs específicas")
        print("   - search_google: Pesquisar informações na web")
        print("   - Combine ambas para: buscar → ler → responder")
        
        print("\n⚙️ CONFIGURAÇÃO RECOMENDADA:")
        print("   Para melhores resultados com search_google:")
        print("   1. Crie conta em https://serper.dev (100 buscas grátis/mês)")
        print("   2. export SERPER_API_KEY='sua-chave'")
        print("   ou")
        print("   1. Configure Google Custom Search")
        print("   2. export GOOGLE_API_KEY='sua-chave'")
        print("   3. export GOOGLE_CX='seu-cx'")
    
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

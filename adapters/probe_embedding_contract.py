"""Probe utility to discover embedding service HTTP contract.

Usage:
  python3 -m polaris.adapters.probe_embedding_contract

It will try common endpoints for embeddings, upsert and search and print status and a small
sample of the JSON response to help adapt the main adapter.
"""
import os
import requests
import json

EMBEDDING_URL = os.getenv('EMBEDDING_URL', 'http://localhost:8001')

EMBED_PATHS = ['/v1/embeddings', '/embeddings', '/v1/embed', '/embed']
UPSERT_PATHS = ['/v1/upsert', '/upsert', '/v1/collections/upsert']
SEARCH_PATHS = ['/v1/search', '/search', '/v1/query', '/query']


def try_post(path, payload):
    url = EMBEDDING_URL.rstrip('/') + path
    try:
        r = requests.post(url, json=payload, timeout=5)
        try:
            body = r.json()
        except Exception:
            body = r.text
        return {'ok': True, 'url': url, 'status': r.status_code, 'body': body}
    except Exception as e:
        return {'ok': False, 'url': url, 'error': str(e)}


def probe_embeddings():
    print('Probing embedding endpoints on', EMBEDDING_URL)
    samples = {
        'embed': {'inputs': ['hello world']},
        'upsert': {'items': [{'id': 'probe1', 'vector': [0.1, 0.2], 'metadata': {'title': 'probe'}}]},
        'search': {'vector': [0.1, 0.2], 'top_k': 3},
    }

    print('\n--- Embedding endpoints ---')
    for p in EMBED_PATHS:
        res = try_post(p, samples['embed'])
        print(p, '->', res.get('status') if res.get('ok') else 'ERR', res.get('error') if not res.get('ok') else '')
        if res.get('ok'):
            body = res.get('body')
            print('  sample keys:', list(body.keys()) if isinstance(body, dict) else type(body))

    print('\n--- Upsert endpoints ---')
    for p in UPSERT_PATHS:
        res = try_post(p, samples['upsert'])
        print(p, '->', res.get('status') if res.get('ok') else 'ERR', res.get('error') if not res.get('ok') else '')
        if res.get('ok'):
            body = res.get('body')
            if isinstance(body, dict):
                print('  sample keys:', list(body.keys()))
            else:
                print('  response type:', type(body))

    print('\n--- Search endpoints ---')
    for p in SEARCH_PATHS:
        res = try_post(p, samples['search'])
        print(p, '->', res.get('status') if res.get('ok') else 'ERR', res.get('error') if not res.get('ok') else '')
        if res.get('ok'):
            body = res.get('body')
            if isinstance(body, dict):
                print('  sample keys:', list(body.keys()))
            else:
                print('  response type:', type(body))


if __name__ == '__main__':
    probe_embeddings()

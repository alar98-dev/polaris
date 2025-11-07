import random
import json
from typing import List, Dict


def generate_mock_examples(contract_name: str, context: Dict, count: int = 10) -> List[Dict]:
    """Gera mocks JSON simples para demonstracao.

    Na produção, trocar por um gerador baseado em schema ou fixtures.
    """
    samples = []
    base = context.get('example_base', {})
    for i in range(count):
        s = {
            'id': i + 1,
            'contract': contract_name,
            'name': f"{contract_name}_mock_{i+1}",
            'payload': {},
        }
        # copiar chaves do base com pequenas variações
        for k, v in base.items():
            if isinstance(v, str):
                s['payload'][k] = f"{v}_{i+1}"
            elif isinstance(v, int):
                s['payload'][k] = v + i
            elif isinstance(v, list):
                s['payload'][k] = random.sample(v, min(len(v), 2))
            else:
                s['payload'][k] = v
        samples.append(s)
    return samples

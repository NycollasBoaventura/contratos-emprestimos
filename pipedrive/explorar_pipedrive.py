# -*- coding: utf-8 -*-
"""
Script exploratório: lista os pipelines/stages e os campos customizados
(deal + person) da sua conta Pipedrive, para descobrirmos:
  1) o ID do stage "Contrato"
  2) as chaves (key) dos campos customizados que guardam CPF, endereço,
     valor da dívida, número de parcelas etc.

NÃO precisa de nenhuma biblioteca além de "requests" (já vem instalada
se você seguiu os passos anteriores).

Como rodar:
  1. Pegue sua API token em: Pipedrive > (seu avatar) > Configurações pessoais > API
  2. Defina as variáveis de ambiente (ou edite as duas linhas abaixo) e rode:

     PowerShell:
       $env:PIPEDRIVE_DOMAIN = "suaempresa"     # o que vem antes de .pipedrive.com
       $env:PIPEDRIVE_API_TOKEN = "sua_token_aqui"
       python explorar_pipedrive.py

Este script só LÊ dados (nenhuma chamada de escrita/alteração é feita).
A saída não expõe sua API token — pode colar o resultado no chat sem medo.
"""

import os
import sys
import requests

DOMINIO = os.environ.get("PIPEDRIVE_DOMAIN", "").strip()
TOKEN = os.environ.get("PIPEDRIVE_API_TOKEN", "").strip()

if not DOMINIO or not TOKEN:
    print("Defina PIPEDRIVE_DOMAIN e PIPEDRIVE_API_TOKEN como variáveis de ambiente antes de rodar.")
    print('Ex (PowerShell): $env:PIPEDRIVE_DOMAIN = "suaempresa"')
    print('                 $env:PIPEDRIVE_API_TOKEN = "sua_token"')
    sys.exit(1)

BASE_URL = f"https://{DOMINIO}.pipedrive.com/api/v1"


def get(caminho, params=None):
    params = dict(params or {})
    params["api_token"] = TOKEN
    resp = requests.get(f"{BASE_URL}{caminho}", params=params, timeout=30)
    resp.raise_for_status()
    dados = resp.json()
    if not dados.get("success"):
        print(f"Erro ao chamar {caminho}: {dados}")
        return []
    return dados.get("data") or []


def linha(*valores, larguras=(8, 40, 40)):
    partes = []
    for v, w in zip(valores, larguras):
        partes.append(str(v)[:w].ljust(w))
    print(" | ".join(partes))


def listar_pipelines_e_stages():
    print("\n" + "=" * 90)
    print("PIPELINES E STAGES (procure o stage 'Contrato' e anote o ID dele)")
    print("=" * 90)
    pipelines = get("/pipelines")
    for p in pipelines:
        print(f"\nPipeline: {p['name']}  (id={p['id']})")
        stages = get("/stages", params={"pipeline_id": p["id"]})
        linha("stage_id", "nome do stage", larguras=(10, 50))
        linha("-" * 8, "-" * 50, larguras=(10, 50))
        for s in stages:
            linha(s["id"], s["name"], larguras=(10, 50))


def listar_campos(recurso, titulo):
    print("\n" + "=" * 90)
    print(titulo)
    print("=" * 90)
    campos = get(f"/{recurso}")
    linha("key", "nome do campo", "tipo", larguras=(24, 40, 12))
    linha("-" * 24, "-" * 40, "-" * 12, larguras=(24, 40, 12))
    for c in campos:
        # campos "padrão" do Pipedrive (ex: title, value, person_id) também aparecem;
        # os customizados costumam ter uma "key" longa em hexadecimal.
        linha(c.get("key"), c.get("name"), c.get("field_type"), larguras=(24, 40, 12))


def main():
    listar_pipelines_e_stages()
    listar_campos("dealFields", "CAMPOS DO DEAL (negócio) - inclui customizados")
    listar_campos("personFields", "CAMPOS DA PERSON (pessoa/cliente) - inclui customizados")
    print("\nPronto. Copie a seção relevante (pipelines/stages + os campos que guardam")
    print("CPF, endereço, valor da dívida, parcelas etc.) e cole no chat.")


if __name__ == "__main__":
    main()

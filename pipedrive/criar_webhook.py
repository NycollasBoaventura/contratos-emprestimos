# -*- coding: utf-8 -*-
"""
Registra (ou lista/remove) a assinatura de webhook REAL no Pipedrive,
apontando para o servidor publicado (Cloud Run).

Uso:
  $env:PIPEDRIVE_API_TOKEN = "sua_token"
  $env:WEBHOOK_BASIC_USER = "usuario_forte"
  $env:WEBHOOK_BASIC_PASS = "senha_forte_aleatoria"

  python criar_webhook.py criar <url_do_cloud_run>
  python criar_webhook.py listar
  python criar_webhook.py remover <webhook_id>
"""

import sys
import requests

import pipedrive_config as cfg


def criar(url_base):
    if not cfg.WEBHOOK_BASIC_USER or not cfg.WEBHOOK_BASIC_PASS:
        print("Defina WEBHOOK_BASIC_USER e WEBHOOK_BASIC_PASS antes de criar o webhook.")
        sys.exit(1)

    payload = {
        "subscription_url": f"{url_base.rstrip('/')}/webhook/pipedrive",
        "event_action": "updated",
        "event_object": "deal",
        "http_auth_user": cfg.WEBHOOK_BASIC_USER,
        "http_auth_password": cfg.WEBHOOK_BASIC_PASS,
    }
    r = requests.post(f"{cfg.BASE_URL}/webhooks", params={"api_token": cfg.TOKEN}, json=payload, timeout=30)
    d = r.json()
    if d.get("success"):
        print("Webhook criado com sucesso:")
        print(" id:", d["data"]["id"])
        print(" subscription_url:", d["data"]["subscription_url"])
    else:
        print("Erro ao criar webhook:", d)


def listar():
    r = requests.get(f"{cfg.BASE_URL}/webhooks", params={"api_token": cfg.TOKEN}, timeout=30)
    d = r.json()
    for w in (d.get("data") or {}).get("webhooks", d.get("data") or []):
        print(w.get("id"), "|", w.get("subscription_url"), "|", w.get("event_action"), w.get("event_object"))


def remover(webhook_id):
    r = requests.delete(f"{cfg.BASE_URL}/webhooks/{webhook_id}", params={"api_token": cfg.TOKEN}, timeout=30)
    print(r.json())


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    comando = args[0]
    if comando == "criar" and len(args) >= 2:
        criar(args[1])
    elif comando == "listar":
        listar()
    elif comando == "remover" and len(args) >= 2:
        remover(args[1])
    else:
        print(__doc__)

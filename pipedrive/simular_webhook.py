# -*- coding: utf-8 -*-
"""
Simula o Pipedrive chamando nosso webhook, SEM precisar de ngrok nem mover
um card de verdade na tela. Usa um Deal real (você escolhe o ID) e manda
pro servidor local (webhook_server.py) um payload dizendo "esse deal acabou
de entrar no stage Contratos/Promissória".

Uso:
  python simular_webhook.py <deal_id>

  # se o deal ainda não tem os 3 campos de parcelamento preenchidos,
  # este comando preenche com valores de exemplo ANTES de simular
  # (grava de verdade nesse deal no Pipedrive — use só num deal de teste):
  python simular_webhook.py <deal_id> --preencher-teste
"""

import sys
import requests

import pipedrive_config as cfg

SERVIDOR_LOCAL = "http://localhost:5050/webhook/pipedrive"


def preencher_campos_teste(deal_id):
    from datetime import date, timedelta
    vencimento = (date.today() + timedelta(days=30)).isoformat()
    payload = {
        cfg.CAMPO_NUM_PARCELAS: 6,
        cfg.CAMPO_VENCIMENTO_1A_PARCELA: vencimento,
        # CAMPO_VALOR_PARCELA fica em branco de propósito, pra testar o cálculo automático
    }
    r = requests.put(
        f"{cfg.BASE_URL}/deals/{deal_id}",
        params={"api_token": cfg.TOKEN},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    d = r.json()
    if not d.get("success"):
        raise RuntimeError(f"Falha ao preencher campos de teste: {d}")
    print(f"[OK] Campos de teste preenchidos no deal #{deal_id}: {payload}")


def simular(deal_id):
    payload = {
        "v": 1,
        "meta": {"action": "updated", "object": "deal"},
        "current": {"id": deal_id, "stage_id": cfg.STAGE_CONTRATOS_PROMISSORIA_ID},
        "previous": {"id": deal_id, "stage_id": cfg.PIPELINE_BANCARIOS_ID},
    }
    auth = (cfg.WEBHOOK_BASIC_USER, cfg.WEBHOOK_BASIC_PASS) if cfg.WEBHOOK_BASIC_USER else None
    print(f"Enviando payload simulado para {SERVIDOR_LOCAL} ...")
    r = requests.post(SERVIDOR_LOCAL, json=payload, auth=auth, timeout=60)
    print(f"Status HTTP: {r.status_code}")
    try:
        print("Resposta:", r.json())
    except Exception:
        print("Resposta (texto bruto):", r.text)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Uso: python simular_webhook.py <deal_id> [--preencher-teste]")
        sys.exit(1)

    deal_id = int(args[0])
    if "--preencher-teste" in args:
        preencher_campos_teste(deal_id)

    simular(deal_id)

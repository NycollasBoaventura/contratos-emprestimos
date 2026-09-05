# -*- coding: utf-8 -*-
"""
Configuração da integração Pipedrive <-> Gerador de Contrato.

A API token NUNCA fica hardcoded aqui — sempre lida da variável de
ambiente PIPEDRIVE_API_TOKEN (veja instruções no README/mensagens do chat).
"""

import os

DOMINIO = os.environ.get("PIPEDRIVE_DOMAIN", "emprestimosparabancarios")
TOKEN = os.environ.get("PIPEDRIVE_API_TOKEN", "")
BASE_URL = f"https://{DOMINIO}.pipedrive.com/api/v1"

# Credenciais HTTP Basic Auth que o Pipedrive envia em todo webhook.
# Configuradas na criação da assinatura do webhook (ver criar_webhook.py).
WEBHOOK_BASIC_USER = os.environ.get("WEBHOOK_BASIC_USER", "")
WEBHOOK_BASIC_PASS = os.environ.get("WEBHOOK_BASIC_PASS", "")

# Pipeline "Bancários" e o novo stage que dispara a geração do contrato.
PIPELINE_BANCARIOS_ID = 1
STAGE_CONTRATOS_PROMISSORIA_ID = 45

# --- Campos customizados do DEAL (negócio) ---
CAMPO_NUM_PARCELAS = "702ced795d7378b57cd443702b37b0875ca19148"
CAMPO_VENCIMENTO_1A_PARCELA = "2d1d22e30e99d3e64df51ea5ccc4505e1ef61209"
CAMPO_VALOR_PARCELA = "47e2e8f0a0bf16c03eee9f0f1fa3fdd892ca7342"

# --- Campos customizados da PERSON (cliente) ---
CAMPO_CPF = "c791736015a481c50888011f48bb5d5048896a99"
CAMPO_ESTADO_CIVIL = "bcce592ed79b5db986d25486d8eb115c8076d42d"
CAMPO_CARGO_PROFISSAO = "9fa78c701364ceffbfce28689104760bc9ab947b"
CAMPO_ENDERECO_RESIDENCIAL = "2d17fd0de514078801567b76d8a8d42ddb140834"
CAMPO_ENDERECO_COMERCIAL = "6ffc13880f82034a9487836dca01acc8d0eed285"

# Opções do campo "Estado Civil" (id -> texto usado no contrato)
OPCOES_ESTADO_CIVIL = {
    16: "casado(a)",
    17: "solteiro(a)",
}

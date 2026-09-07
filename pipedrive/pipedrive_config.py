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

# Pipeline "Bancários" e o stage "Formalização" (id=45) que dispara a geração do contrato.
# O nome do stage já mudou (era "Contratos/Promissória"), mas o id numérico não muda com o rename.
PIPELINE_BANCARIOS_ID = 1
STAGE_CONTRATOS_PROMISSORIA_ID = 45

# --- Campos customizados da PERSON (cliente): parcelamento ---
CAMPO_NUM_PARCELAS = "c53ad9049222f2602038788b1fc9f99b376504cc"
CAMPO_VENCIMENTO_1A_PARCELA = "0df2b36511c86091677c523bf93f0209b77fe7e8"
CAMPO_VALOR_PARCELA = "bf32192caf32a0e508966dc6df3a6353836ef595"

# --- Campos customizados da PERSON (cliente): dados pessoais ---
CAMPO_TIPO_GARANTIA = "d2ea8ff142921b6124cf07d15ab20f3d532f1a13"

# Só usados quando o Tipo de Garantia é Cheque (por isso não são obrigatórios
# no Pipedrive: quem é promissória não precisa preencher).
CAMPO_NUMEROS_CHEQUES = "06e09dc702705e30517b8f6373ee741c43767a9b"
CAMPO_BANCO_CHEQUE = "592564a00ec6f8050f01be76b16fd9566d5f5fe3"
CAMPO_AGENCIA_CHEQUE = "53495e9ba4449751557d12b9b973701a070f949d"
CAMPO_CONTA_CHEQUE = "b572fa41353cf02e1bf11a4effc5649ae26e1156"

# Opções do campo "Banco (Cheque)" (id -> nome usado no contrato)
OPCOES_BANCO_CHEQUE = {
    104: "Itaú",
    105: "Safra",
    106: "Santander",
    107: "Bradesco",
}
CAMPO_CPF = "c791736015a481c50888011f48bb5d5048896a99"
CAMPO_ESTADO_CIVIL = "bcce592ed79b5db986d25486d8eb115c8076d42d"
CAMPO_CARGO_PROFISSAO = "9fa78c701364ceffbfce28689104760bc9ab947b"
CAMPO_ENDERECO_RESIDENCIAL = "2d17fd0de514078801567b76d8a8d42ddb140834"
CAMPO_COMPLEMENTO_RESIDENCIAL = "cc011085599eb129fe4912c723168050a31184c3"
CAMPO_CEP_RESIDENCIAL = "c8bbe88fc8234940c33b6350cbb792d7872925d9"
CAMPO_ENDERECO_COMERCIAL = "6ffc13880f82034a9487836dca01acc8d0eed285"

# Opções do campo "Estado Civil" (id -> texto usado no contrato)
OPCOES_ESTADO_CIVIL = {
    16: "casado(a)",
    17: "solteiro(a)",
}

# Opções do campo "Tipo de Garantia" (id -> tipo de contrato a gerar)
PROMISSORIA = "promissoria"
CHEQUE = "cheque"
OPCOES_TIPO_GARANTIA = {
    102: PROMISSORIA,
    103: CHEQUE,
}

# Domicílio profissional do devedor: endereço fixo da sede do banco, definido
# pela Organização vinculada ao Deal (o campo "Endereço Comercial" da Person
# quase nunca vem preenchido). Chave = id da Organização no Pipedrive.
ENDERECOS_BANCOS = {
    21: "Praça Alfredo Egydio de Souza Aranha, 100 - Jabaquara, São Paulo, 04344-902",       # *Itaú
    25: "R. Aurora Soares Barbosa, 775 - Vila Campesina, Osasco - SP, 06023-010",            # *Bradesco
    13: "Av. Presidente Juscelino Kubitscheck, 2235 - Vila Olímpia, São Paulo - SP, 13571-410",  # *Santander
    14: "Av. Paulista, 2100 - Cerqueira César - São Paulo - SP, 01310-930",                  # *Safra
}

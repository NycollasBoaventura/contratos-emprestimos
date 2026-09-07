# -*- coding: utf-8 -*-
"""
Servidor local que recebe o webhook do Pipedrive quando um Deal entra no
stage "Contratos/Promissória", busca os dados do cliente, gera o contrato
+ notas promissórias em PDF e anexa o arquivo de volta no próprio Deal.

Rodar localmente:
    $env:PIPEDRIVE_API_TOKEN = "sua_token"
    $env:WEBHOOK_BASIC_USER = "usuario_de_teste"
    $env:WEBHOOK_BASIC_PASS = "senha_de_teste"
    python webhook_server.py

Servidor sobe em http://localhost:5050 (ou na porta da variável PORT, usada pelo Cloud Run)
Endpoint do webhook: POST /webhook/pipedrive (exige HTTP Basic Auth)
"""

import hmac
import os
import re
import sys
import tempfile
import traceback
from datetime import date, datetime
from pathlib import Path

import requests
from flask import Flask, jsonify, request

sys.path.insert(0, str(Path(__file__).parent.parent))  # para importar gerar_contrato.py
import gerar_contrato as gc
from pipedrive import pipedrive_config as cfg

app = Flask(__name__)

# Em produção (Cloud Run) o disco é efêmero e só /tmp é gravável.
PASTA_SAIDA = Path(tempfile.gettempdir()) / "contratos_saida"
PASTA_SAIDA.mkdir(exist_ok=True)


def mascarar_cpf(cpf):
    if not cpf or len(cpf) < 4:
        return "***"
    return f"***.***.***-{cpf[-2:]}"


def autenticacao_valida(req):
    """Confere o HTTP Basic Auth que o Pipedrive envia no webhook."""
    if not cfg.WEBHOOK_BASIC_USER or not cfg.WEBHOOK_BASIC_PASS:
        # Falha segura: se as credenciais não estiverem configuradas no servidor,
        # não aceitamos nenhuma requisição (em vez de deixar o endpoint aberto).
        return False
    auth = req.authorization
    if auth is None:
        return False
    usuario_ok = hmac.compare_digest(auth.username or "", cfg.WEBHOOK_BASIC_USER)
    senha_ok = hmac.compare_digest(auth.password or "", cfg.WEBHOOK_BASIC_PASS)
    return usuario_ok and senha_ok


class ErroDadosIncompletos(Exception):
    pass


def pipedrive_get(caminho, params=None):
    params = dict(params or {})
    params["api_token"] = cfg.TOKEN
    r = requests.get(f"{cfg.BASE_URL}{caminho}", params=params, timeout=30)
    r.raise_for_status()
    d = r.json()
    if not d.get("success"):
        raise RuntimeError(f"Pipedrive GET {caminho} falhou: {d}")
    return d.get("data")


def parse_data_pipedrive(valor):
    """Campos de data do Pipedrive vêm como 'YYYY-MM-DD'."""
    if not valor:
        return None
    return datetime.strptime(valor, "%Y-%m-%d").date()


def endereco_residencial_completo(person):
    """Monta 'endereço, complemento, CEP' na ordem, pulando o que estiver vazio."""
    endereco = (person.get(cfg.CAMPO_ENDERECO_RESIDENCIAL) or "").strip()
    complemento = (person.get(cfg.CAMPO_COMPLEMENTO_RESIDENCIAL) or "").strip()
    cep = (person.get(cfg.CAMPO_CEP_RESIDENCIAL) or "").strip()

    # O campo de endereço do Pipedrive às vezes já vem com o CEP no fim;
    # nesse caso não repetimos o CEP do campo separado.
    if cep and re.sub(r"\D", "", cep) in re.sub(r"\D", "", endereco):
        cep = ""

    return ", ".join(p for p in (endereco, complemento, cep) if p)


def endereco_profissional_do_banco(deal, person):
    """Sede do banco onde o devedor trabalha, a partir da Organização do Deal."""
    org = deal.get("org_id") or person.get("org_id") or {}
    org_id = org.get("value") if isinstance(org, dict) else org
    return cfg.ENDERECOS_BANCOS.get(org_id, "")


def montar_cliente_a_partir_do_pipedrive(deal, person, deal_id):
    faltando = []

    def obrigatorio(valor, nome_campo):
        if valor is None or (isinstance(valor, str) and valor.strip() == ""):
            faltando.append(nome_campo)
        return valor

    nome_devedor = obrigatorio(person.get("name"), "Nome (Person)")
    cpf = obrigatorio(person.get(cfg.CAMPO_CPF), "CPF (Person)")
    endereco_residencial = obrigatorio(endereco_residencial_completo(person), "Endereço Residencial (Person)")
    num_parcelas_raw = obrigatorio(person.get(cfg.CAMPO_NUM_PARCELAS), "Número de Parcelas (Person)")
    data_primeira_raw = obrigatorio(person.get(cfg.CAMPO_VENCIMENTO_1A_PARCELA), "Vencimento da 1ª Parcela (Person)")
    valor_parcela_raw = obrigatorio(person.get(cfg.CAMPO_VALOR_PARCELA), "Valor da Parcela (Person)")

    garantia_raw = obrigatorio(person.get(cfg.CAMPO_TIPO_GARANTIA), "Tipo de Garantia (Person)")
    tipo_garantia = cfg.OPCOES_TIPO_GARANTIA.get(
        int(str(garantia_raw).split(",")[0]) if garantia_raw else None
    )

    estado_civil_raw = person.get(cfg.CAMPO_ESTADO_CIVIL)
    estado_civil = "solteiro(a)"
    if estado_civil_raw:
        primeiro_id = int(str(estado_civil_raw).split(",")[0])
        estado_civil = cfg.OPCOES_ESTADO_CIVIL.get(primeiro_id, "solteiro(a)")

    if faltando:
        raise ErroDadosIncompletos(
            f"Deal #{deal_id}: preencha no Pipedrive antes de gerar o contrato -> {', '.join(faltando)} "
            f"(cliente: {(nome_devedor or '?')[:1]}***, CPF {mascarar_cpf(cpf)})"
        )

    if tipo_garantia == cfg.CHEQUE:
        raise ErroDadosIncompletos(
            f"Deal #{deal_id}: Tipo de Garantia = Cheque, mas o modelo de contrato de cheque "
            f"ainda não foi implementado. Nenhum contrato foi gerado (o modelo de promissória "
            f"não serve para esse caso)."
        )

    num_parcelas = int(float(num_parcelas_raw))
    valor_parcela = float(valor_parcela_raw)
    valor_total = round(num_parcelas * valor_parcela, 2)

    cliente = {
        "linha_planilha": f"deal#{deal_id}",
        "nome_devedor": nome_devedor,
        "nacionalidade": "brasileiro(a)",
        "estado_civil": estado_civil,
        # Todo cliente que chega nesse stage é bancário — o campo "Cargo (função)"
        # do Pipedrive guarda o cargo interno do banco (ex: "GTE REL UNICL DIG
        # PREMIUM"), que não serve como profissão no contrato.
        "profissao": "bancário(a)",
        "cpf_devedor": cpf,
        "endereco_residencial": endereco_residencial,
        "endereco_profissional": endereco_profissional_do_banco(deal, person),
        "valor_total": valor_total,
        "num_parcelas": num_parcelas,
        "valor_parcela": valor_parcela,
        "data_primeira_parcela": parse_data_pipedrive(data_primeira_raw),
        "data_emissao": date.today(),
        "local": gc.PADRAO_LOCAL,
        "foro": gc.PADRAO_FORO,
        "juros_mora_pct": gc.PADRAO_JUROS_MORA_PCT,
        "multa_moratoria_pct": gc.PADRAO_MULTA_MORATORIA_PCT,
        "multa_pct": gc.PADRAO_MULTA_PCT,
        "honorarios_pct": gc.PADRAO_HONORARIOS_PCT,
        "desconto_rendimentos_pct": gc.PADRAO_DESCONTO_RENDIMENTOS_PCT,
        "testemunha1_nome": gc.PADRAO_TESTEMUNHA1_NOME,
        "testemunha1_cpf": gc.PADRAO_TESTEMUNHA1_CPF,
        "testemunha2_nome": gc.PADRAO_TESTEMUNHA2_NOME,
        "testemunha2_cpf": gc.PADRAO_TESTEMUNHA2_CPF,
    }
    return cliente


def anexar_pdf_no_deal(deal_id, caminho_pdf: Path):
    with open(caminho_pdf, "rb") as f:
        arquivos = {"file": (caminho_pdf.name, f, "application/pdf")}
        dados = {"deal_id": deal_id}
        r = requests.post(
            f"{cfg.BASE_URL}/files",
            params={"api_token": cfg.TOKEN},
            data=dados,
            files=arquivos,
            timeout=60,
        )
    r.raise_for_status()
    resp = r.json()
    if not resp.get("success"):
        raise RuntimeError(f"Falha ao anexar PDF no deal {deal_id}: {resp}")
    return resp["data"]


def processar_deal(deal_id):
    deal = pipedrive_get(f"/deals/{deal_id}")
    pessoa_rel = deal.get("person_id")
    if not pessoa_rel or not pessoa_rel.get("value"):
        raise ErroDadosIncompletos(f"Deal #{deal_id} não tem uma Person (cliente) vinculada.")
    person = pipedrive_get(f"/persons/{pessoa_rel['value']}")

    cliente = montar_cliente_a_partir_do_pipedrive(deal, person, deal_id)
    parcelas = gc.calcular_parcelas(cliente)
    texto = gc.montar_texto_contrato(cliente, parcelas)

    nome_arquivo = f"{gc.slugify(cliente['nome_devedor'])}_deal{deal_id}_{cliente['data_emissao'].strftime('%Y%m%d')}.pdf"
    caminho_pdf = PASTA_SAIDA / nome_arquivo
    gc.gerar_pdf_contrato(cliente, parcelas, texto, caminho_pdf)

    try:
        anexo = anexar_pdf_no_deal(deal_id, caminho_pdf)
    finally:
        # Não deixamos o PDF com dados do cliente parado no disco do servidor;
        # o Pipedrive (anexo no deal) já é o registro definitivo.
        caminho_pdf.unlink(missing_ok=True)

    return {"pipedrive_file_id": anexo.get("id")}


@app.route("/webhook/pipedrive", methods=["POST"])
def webhook_pipedrive():
    if not autenticacao_valida(request):
        return jsonify({"erro": "não autorizado"}), 401

    payload = request.get_json(force=True, silent=True) or {}
    current = payload.get("current") or {}
    previous = payload.get("previous") or {}

    stage_atual = current.get("stage_id")
    stage_anterior = previous.get("stage_id")
    deal_id = current.get("id")

    if stage_atual != cfg.STAGE_CONTRATOS_PROMISSORIA_ID:
        return jsonify({"ignorado": True, "motivo": "stage não é Contratos/Promissória"}), 200

    if stage_anterior == cfg.STAGE_CONTRATOS_PROMISSORIA_ID:
        return jsonify({"ignorado": True, "motivo": "deal já estava nesse stage (sem mudança)"}), 200

    if not deal_id:
        return jsonify({"erro": "payload sem deal id"}), 400

    try:
        resultado = processar_deal(deal_id)
        return jsonify({"ok": True, **resultado}), 200
    except ErroDadosIncompletos as e:
        print(f"[AVISO] {e}")
        return jsonify({"ok": False, "erro": str(e)}), 422
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "erro": str(e)}), 500


@app.route("/saude", methods=["GET"])
def saude():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    if not cfg.TOKEN:
        print("ATENÇÃO: variável de ambiente PIPEDRIVE_API_TOKEN não definida.")
        sys.exit(1)
    if not cfg.WEBHOOK_BASIC_USER or not cfg.WEBHOOK_BASIC_PASS:
        print("ATENÇÃO: WEBHOOK_BASIC_USER/WEBHOOK_BASIC_PASS não definidos — endpoint recusará todas as chamadas.")
    porta = int(os.environ.get("PORT", "5050"))
    app.run(host="0.0.0.0" if os.environ.get("PORT") else "127.0.0.1", port=porta, debug=False, use_reloader=False)

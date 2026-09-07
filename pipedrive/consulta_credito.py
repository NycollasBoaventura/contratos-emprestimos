# -*- coding: utf-8 -*-
"""
Consulta de crédito (Boa Vista SCPC + Serasa Experian) do CPF do devedor.

Hoje as duas funções abaixo são placeholders: nenhuma das duas credenciais
foi liberada ainda. Assim que o Boa Vista e/ou a Serasa confirmarem acesso
via API, é só preencher a chamada HTTP real dentro de cada função — o
disparo (campo "Consultar SPC/Serasa" -> Sim) e o registro do resultado
como nota no Pipedrive já funcionam de ponta a ponta.

Credenciais devem vir de variáveis de ambiente, nunca hardcoded:
  BOA_VISTA_API_TOKEN
  SERASA_API_TOKEN (ou o nome que a Serasa definir)
"""

import os


class ConsultaNaoConfigurada(Exception):
    """Levantada quando a credencial da API ainda não foi configurada."""


def consultar_boa_vista(cpf: str) -> dict:
    token = os.environ.get("BOA_VISTA_API_TOKEN", "")
    if not token:
        raise ConsultaNaoConfigurada(
            "Boa Vista SCPC: BOA_VISTA_API_TOKEN não configurada ainda "
            "(falta confirmar acesso via API com o Boa Vista)."
        )

    # TODO: quando a credencial existir, substituir por uma chamada real.
    # Exemplo de formato esperado (ajustar conforme a documentação real):
    #
    # r = requests.post(
    #     "https://api.boavistaservicos.com.br/...",
    #     headers={"Authorization": f"Bearer {token}"},
    #     json={"cpf": cpf},
    #     timeout=30,
    # )
    # r.raise_for_status()
    # return r.json()
    raise NotImplementedError("Chamada real à API do Boa Vista ainda não implementada.")


def consultar_serasa(cpf: str) -> dict:
    token = os.environ.get("SERASA_API_TOKEN", "")
    if not token:
        raise ConsultaNaoConfigurada(
            "Serasa Experian: SERASA_API_TOKEN não configurada ainda "
            "(falta confirmar acesso via API com a Serasa)."
        )

    # TODO: mesma ideia do Boa Vista — preencher quando a API for liberada.
    raise NotImplementedError("Chamada real à API da Serasa ainda não implementada.")


def _formatar_resultado(nome: str, funcao, cpf: str) -> str:
    """Roda uma única consulta e devolve um texto pronto para virar nota no
    Pipedrive, já tratando o caso (atual) de a credencial não estar configurada."""
    titulo = f"Consulta {nome} solicitada para o CPF {cpf}:"
    try:
        resultado = funcao(cpf)
        return f"{titulo}\n\n✅ {resultado}"
    except ConsultaNaoConfigurada as e:
        return f"{titulo}\n\n⏳ Ainda não configurado — {e}"
    except NotImplementedError as e:
        return f"{titulo}\n\n⏳ {e}"
    except Exception as e:
        return f"{titulo}\n\n❌ Erro ao consultar — {e}"


def resultado_spc(cpf: str) -> str:
    return _formatar_resultado("SPC (Boa Vista SCPC)", consultar_boa_vista, cpf)


def resultado_serasa(cpf: str) -> str:
    return _formatar_resultado("Serasa Experian", consultar_serasa, cpf)

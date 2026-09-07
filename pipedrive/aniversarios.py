# -*- coding: utf-8 -*-
"""
Marca no Pipedrive quem faz aniversário hoje.

O Pipedrive não tem gatilho de automação por data ("hoje é o aniversário
de alguém"), só por evento. Então este script roda uma vez por dia e
marca o campo "Aniversário Hoje" = Sim nos aniversariantes — o que é uma
*mudança de campo*, e isso a automação nativa do Pipedrive sabe escutar
para disparar o e-mail.

Também limpa (volta para "Não") quem ficou marcado do dia anterior.

Uso:
    python aniversarios.py            # aplica as mudanças
    python aniversarios.py --dry-run  # só mostra o que faria

Variáveis de ambiente:
    PIPEDRIVE_API_TOKEN, PIPEDRIVE_DOMAIN
"""

import calendar
import sys
from datetime import datetime, timedelta, timezone

import requests

import pipedrive_config as cfg

# O Brasil não tem mais horário de verão desde 2019, então o offset fixo de
# -03:00 é suficiente e evita depender da base de timezones do sistema.
FUSO_BRASIL = timezone(timedelta(hours=-3))


def hoje_brasil():
    return datetime.now(FUSO_BRASIL).date()


def listar_pessoas():
    """Devolve todas as persons, paginando (a conta tem ~1.8 mil)."""
    pessoas, start = [], 0
    while True:
        r = requests.get(
            f"{cfg.BASE_URL}/persons",
            params={"api_token": cfg.TOKEN, "limit": 500, "start": start},
            timeout=60,
        )
        r.raise_for_status()
        corpo = r.json()
        pessoas.extend(corpo.get("data") or [])
        paginacao = (corpo.get("additional_data") or {}).get("pagination", {})
        if not paginacao.get("more_items_in_collection"):
            return pessoas
        start = paginacao.get("next_start", start + 500)


def faz_aniversario_hoje(nascimento: str, hoje) -> bool:
    try:
        data = datetime.strptime(nascimento[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return False

    if (data.month, data.day) == (hoje.month, hoje.day):
        return True

    # Nascido em 29/02 não tem aniversário em ano não bissexto — nesse caso
    # cumprimentamos em 28/02.
    nasceu_em_29_fev = (data.month, data.day) == (2, 29)
    hoje_e_28_fev = (hoje.month, hoje.day) == (2, 28)
    return nasceu_em_29_fev and hoje_e_28_fev and not calendar.isleap(hoje.year)


def atualizar_flag(person_id, opcao):
    r = requests.put(
        f"{cfg.BASE_URL}/persons/{person_id}",
        params={"api_token": cfg.TOKEN},
        json={cfg.CAMPO_ANIVERSARIO_HOJE: opcao},
        timeout=30,
    )
    r.raise_for_status()


def main():
    dry_run = "--dry-run" in sys.argv
    if not cfg.TOKEN:
        print("Defina PIPEDRIVE_API_TOKEN.")
        sys.exit(1)

    hoje = hoje_brasil()
    pessoas = listar_pessoas()

    marcar, limpar = [], []
    for p in pessoas:
        aniversariante = faz_aniversario_hoje(p.get(cfg.CAMPO_DATA_NASCIMENTO), hoje)
        # O Pipedrive devolve enum às vezes como número, às vezes como string.
        marcado = str(p.get(cfg.CAMPO_ANIVERSARIO_HOJE) or "") == str(cfg.OPCAO_ANIVERSARIO_SIM)
        if aniversariante and not marcado:
            marcar.append(p)
        elif not aniversariante and marcado:
            limpar.append(p)

    print(f"Data de referência (Brasil): {hoje.strftime('%d/%m/%Y')}")
    print(f"Pessoas analisadas: {len(pessoas)}")
    print(f"Aniversariantes a marcar: {len(marcar)}")
    for p in marcar:
        print(f"  + {p.get('name')} (id {p['id']})")
    print(f"Marcações do dia anterior a limpar: {len(limpar)}")

    if dry_run:
        print("\n(--dry-run: nada foi gravado)")
        return

    for p in marcar:
        atualizar_flag(p["id"], cfg.OPCAO_ANIVERSARIO_SIM)
    for p in limpar:
        atualizar_flag(p["id"], cfg.OPCAO_ANIVERSARIO_NAO)
    print("\nPronto.")


if __name__ == "__main__":
    main()

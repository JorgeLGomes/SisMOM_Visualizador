"""
CLI: python -m gisele_ts

Exemplos:
    # CSV
    python -m gisele_ts --model Eta_5km --var PREC \\
        --date 2026053000 --lat -20.0 --lon -45.0 -o eta_prec.csv

    # JSON na saida padrao
    python -m gisele_ts --model BAM --var T2M \\
        --date 2026053000 --lat -3.1 --lon -60.0

    # Server remoto + intervalo de horas
    python -m gisele_ts --url http://localhost:8000 \\
        --model Eta_5km --var PREC --date 2026053000 \\
        --lat -20 --lon -45 --passo-min 6 --passo-max 72

    # Listar modelos/variaveis disponiveis
    python -m gisele_ts --list-models
    python -m gisele_ts --list-vars
"""
from __future__ import annotations

import argparse
import json
import sys

from gisele_ts import GiseleClient, MODELS, VARIABLES
from gisele_ts.models import list_models, list_variables


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="gisele_ts",
        description="Extrai serie temporal de um ponto via GISELE Python helper.",
    )
    ap.add_argument("--url", default="http://127.0.0.1:8765",
                    help="URL base do helper (default: %(default)s)")
    ap.add_argument("--model", help="Chave do modelo (veja --list-models)")
    ap.add_argument("--var", help="Chave da variavel (veja --list-vars)")
    ap.add_argument("--date", help="Rodada YYYYMMDDHH (UTC)")
    ap.add_argument("--lat", type=float, help="Latitude (graus)")
    ap.add_argument("--lon", type=float, help="Longitude (graus)")
    ap.add_argument("--passo-min", type=int, default=None,
                    help="Primeiro passo em horas (opcional)")
    ap.add_argument("--passo-max", type=int, default=None,
                    help="Ultimo passo em horas (opcional)")
    ap.add_argument("--parallel", type=int, default=16,
                    help="Limite de fetches concorrentes (1..32, default %(default)s)")
    ap.add_argument("-o", "--output", help="Arquivo de saida (.csv ou .json)")
    ap.add_argument("--list-models", action="store_true", help="Lista modelos disponiveis")
    ap.add_argument("--list-vars", action="store_true", help="Lista variaveis disponiveis")
    ap.add_argument("--health", action="store_true", help="Verifica health do helper")

    args = ap.parse_args(argv)

    # ── Listings ──
    if args.list_models:
        print("Modelos disponiveis:")
        for k in list_models():
            print(f"  {k:14s}  {MODELS[k].get('nome', '—')}")
        return 0
    if args.list_vars:
        print("Variaveis disponiveis:")
        for k in list_variables():
            v = VARIABLES[k]
            print(f"  {k:10s}  {v.get('label', '—')}  ({v.get('unidade', '')})")
        return 0

    client = GiseleClient(base_url=args.url)

    if args.health:
        try:
            h = client.health()
            print(json.dumps(h, indent=2, ensure_ascii=False))
            return 0
        except Exception as e:
            print(f"ERRO no health: {e}", file=sys.stderr)
            return 2

    # ── Validacao ──
    missing = [n for n in ("model", "var", "date", "lat", "lon")
               if getattr(args, n.replace("-", "_")) is None]
    if missing:
        ap.error(f"argumentos obrigatorios faltando: {missing} (ou use --list-models / --list-vars / --health)")

    if args.model not in MODELS:
        ap.error(f"modelo desconhecido: {args.model!r}. Veja --list-models")
    if args.var not in VARIABLES:
        ap.error(f"variavel desconhecida: {args.var!r}. Veja --list-vars")

    modelo = MODELS[args.model]
    variavel = VARIABLES[args.var]

    # ── Chamada ──
    try:
        ts = client.timeseries(
            modelo=modelo, variavel=variavel,
            data_rodada=args.date,
            lat=args.lat, lon=args.lon,
            passo_min=args.passo_min, passo_max=args.passo_max,
            parallel_limit=args.parallel,
        )
    except Exception as e:
        print(f"ERRO na extracao: {e}", file=sys.stderr)
        return 1

    # ── Saida ──
    print(f"# {ts.layer_name} @ ({ts.lat}, {ts.lon})  rodada={ts.run_date_utc}", file=sys.stderr)
    print(f"# {len(ts)} passos · {ts.valid_count()} validos · {ts.elapsed_seconds}s · "
          f"fetched={ts.fetched} failed={ts.failed}", file=sys.stderr)

    if args.output:
        if args.output.lower().endswith(".csv"):
            ts.to_csv(args.output)
        else:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(ts.to_json())
        print(f"# salvo em {args.output}", file=sys.stderr)
    else:
        print(ts.to_json())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

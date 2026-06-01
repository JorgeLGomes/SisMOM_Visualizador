"""
extract_ts.py — Exemplo end-to-end de extracao de TS via gisele_ts.

Pre-requisitos:
1. Helper rodando: cd electron-app/python-helper && python server.py --port 8000
2. Cliente instalado: cd api-client && pip install -e .

Uso:
    python examples/extract_ts.py
"""
from gisele_ts import GiseleClient, MODELS, VARIABLES


def main():
    # ── 1) Inicializa client apontando para o helper local ──
    client = GiseleClient(base_url="http://127.0.0.1:8000")

    # ── 2) Health check (opcional) ──
    try:
        h = client.health()
        print(f"helper: {h['service']} v{h['version']} · "
              f"cache {h['cache']['size_mb']} MB · "
              f"hits/misses {h['cache']['hits']}/{h['cache']['misses']}")
    except Exception as e:
        print(f"ERRO conectando ao helper: {e}")
        print("Inicie o helper antes: cd electron-app/python-helper && python server.py --port 8000")
        return 1

    # ── 3) Extrai TS de precipitacao do Eta 5km num ponto ──
    print("\nExtraindo serie temporal Eta 5km · PREC em (-20, -45)...")
    ts = client.timeseries(
        modelo=MODELS["Eta_5km"],
        variavel=VARIABLES["PREC"],
        data_rodada="2026053000",
        lat=-20.0, lon=-45.0,
        passo_min=6, passo_max=72,
    )
    print(f"  {ts.layer_name}: {len(ts)} passos, {ts.valid_count()} validos, "
          f"{ts.elapsed_seconds}s (fetched={ts.fetched}, failed={ts.failed})")

    # ── 4) Imprime primeiros 5 passos ──
    print("\nPrimeiros passos:")
    for s in ts.samples[:5]:
        v = "—" if s.value is None else f"{s.value:.3f}"
        print(f"  +{s.passo_h:3d}h  {s.time_utc}  {v}")

    # ── 5) Salva CSV ──
    out_csv = "eta_prec_-20_-45.csv"
    ts.to_csv(out_csv)
    print(f"\nCSV salvo: {out_csv}")

    # ── 6) Se pandas disponivel, monta DataFrame ──
    try:
        df = ts.dataframe()
        print(f"\nDataFrame ({len(df)} linhas):")
        print(df.head(10).to_string())
        print(f"\nstats: mean={df['value'].mean():.3f}, max={df['value'].max():.3f}")
    except ImportError:
        print("\n(instale pandas para ver DataFrame: pip install pandas)")

    # ── 7) Multi-ponto — reusa cache do helper ──
    points = [(-20.0, -45.0), (-23.5, -46.6), (-3.1, -60.0)]
    print(f"\nMulti-ponto ({len(points)} locais)...")
    results = client.timeseries_multi(
        modelo=MODELS["Eta_5km"],
        variavel=VARIABLES["PREC"],
        data_rodada="2026053000",
        points=points,
        passo_min=6, passo_max=72,
    )
    for ts in results:
        print(f"  ({ts.lat:+.1f}, {ts.lon:+.1f}): "
              f"{ts.valid_count()}/{len(ts)} validos, {ts.elapsed_seconds}s")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

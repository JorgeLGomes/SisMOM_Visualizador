"""
baixar_cidades_brasil.py — baixa lista completa de municipios brasileiros
do IBGE + coordenadas (centroides) e gera GeoJSON pronto para uso no GISELE.

Uso:
    python dev/baixar_cidades_brasil.py [saida.geojson]

Fontes:
- Lista de municipios: API IBGE /localidades/municipios (~5570 municipios)
- Coordenadas: malha geografica do IBGE (centroides via shapefile/geopackage)

Estrategia:
1. Baixa lista IBGE (nome, UF, codigo IBGE)
2. Para cada municipio, busca centroide via Nominatim ou via dataset embutido
   (alternativa: baixa o shapefile completo e usa shapely para extrair centroides)

Saida: FeatureCollection com properties = {nome, uf, codigo_ibge, regiao, populacao}
       geometry = Point [lon, lat]

Dependencias:
    pip install requests
    (opcional: pip install shapely geopandas para extrair centroides do shapefile)
"""
import json
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERRO: requests nao instalado. Rode: pip install requests")
    sys.exit(1)


IBGE_API = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=nome"
COORD_API = "https://servicodados.ibge.gov.br/api/v1/malhas/municipios/{cod}/metadados"

# Alternativa: GitHub publico com cidades + coordenadas
ALT_URL = "https://raw.githubusercontent.com/kelvins/Municipios-Brasileiros/main/json/municipios.json"


def baixar_lista_ibge():
    """Baixa lista oficial IBGE (sem coordenadas)."""
    print("Baixando lista IBGE...", file=sys.stderr)
    r = requests.get(IBGE_API, timeout=60,
                     headers={"User-Agent": "GISELE/1.0"})
    r.raise_for_status()
    return r.json()


def baixar_alt():
    """Baixa do mirror github com coordenadas ja incluidas."""
    print("Baixando do mirror github (com coordenadas)...", file=sys.stderr)
    r = requests.get(ALT_URL, timeout=60,
                     headers={"User-Agent": "GISELE/1.0"})
    r.raise_for_status()
    return r.json()


def to_geojson(municipios):
    """Converte lista de dicts {nome, uf, lat, lon, codigo_ibge, ...} em FeatureCollection."""
    features = []
    for m in municipios:
        # Aceita varios schemas (kelvins vs IBGE proprio)
        nome = m.get("nome") or m.get("municipio")
        if not nome:
            continue
        # UF: pode vir como string ou objeto {sigla, nome}
        uf = m.get("uf") or m.get("codigo_uf") or m.get("sigla_uf")
        if isinstance(uf, dict):
            uf = uf.get("sigla")
        # tenta multiplas chaves para lat/lon
        lat = m.get("latitude") or m.get("lat")
        lon = m.get("longitude") or m.get("lon")
        if lat is None or lon is None:
            # tenta nested
            try:
                lat = m["microrregiao"]["mesorregiao"]["UF"]["latitude"]
            except Exception:
                continue
        try:
            lat, lon = float(lat), float(lon)
        except (TypeError, ValueError):
            continue
        codigo = m.get("codigo_ibge") or m.get("id") or m.get("codigo")
        regiao = m.get("regiao") or m.get("nome_regiao")
        capital = bool(m.get("capital"))
        pop = m.get("populacao") or m.get("populacao_2022")

        props = {
            "nome": str(nome),
            "uf": str(uf) if uf else "",
            "codigo_ibge": str(codigo) if codigo else "",
        }
        if regiao: props["regiao"] = str(regiao)
        if capital: props["capital"] = True
        if pop:
            try: props["populacao"] = int(pop)
            except (TypeError, ValueError): pass

        features.append({
            "type": "Feature",
            "properties": props,
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
        })

    return {
        "type": "FeatureCollection",
        "metadata": {
            "fonte": "IBGE / Municipios-Brasileiros",
            "total": len(features),
            "geracao": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        },
        "features": features,
    }


def main(argv):
    saida = Path(argv[1]) if len(argv) > 1 else Path("cidades_brasil.geojson")
    # Tenta primeiro o mirror (vem com coords)
    try:
        muns = baixar_alt()
    except Exception as e:
        print(f"Mirror falhou ({e}), tentando IBGE oficial...", file=sys.stderr)
        try:
            muns = baixar_lista_ibge()
        except Exception as e2:
            print(f"IBGE tambem falhou: {e2}", file=sys.stderr)
            return 1

    gj = to_geojson(muns)
    saida.write_text(json.dumps(gj, ensure_ascii=False, separators=(",", ":")),
                     encoding="utf-8")
    print(f"OK: {len(gj['features'])} cidades -> {saida}", file=sys.stderr)
    print(f"     tamanho: {saida.stat().st_size // 1024} KB", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

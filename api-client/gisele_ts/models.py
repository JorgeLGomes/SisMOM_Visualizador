"""
models.py — Registry de configuracoes conhecidas de modelos e variaveis CPTEC.

Estes presets foram extraidos das config originais do frontend GISELE.
Ajuste url_path/file_name conforme a sua instancia (servidor local,
FTP do CPTEC, mirror interno).

USO:
    from gisele_ts import MODELS, VARIABLES

    modelo = MODELS["Eta_5km"]
    variavel = VARIABLES["PREC"]   # ou monte um dict manualmente
"""
from __future__ import annotations
from typing import TypedDict, Optional


class ModelConfig(TypedDict, total=False):
    """Schema do dict aceito por GiseleClient.timeseries(modelo=...).

    Os templates aceitam placeholders (resolvidos pelo helper):
      {yyyy} {mm} {dd} {hh}  — data/hora da rodada
      {yyyymmddhh}            — concatenado
      {escopo1} {escopo2}     — tokens do modelo
      {prefixo}               — prefixo da variavel
      {N} ou {N%4}            — indice (1, 2, ... com padding)
      {F} ou {F%4}            — passo em horas
      {fct} ou {f%4}          — idem com prefixo 'f'
      {ext}                   — extensao
    """
    nome: str
    url_path: str
    file_name: str
    url_path_tif: Optional[str]
    file_name_tif: Optional[str]
    same_url_for_tif: bool
    same_name_for_tif: bool
    extensao: str
    extensao_tif: str
    escopo1: str
    escopo2: str
    maxPassos: int


class VariableConfig(TypedDict, total=False):
    id: str
    label: str
    prefixo: str
    frequencia: int        # horas entre passos (1 = hourly, 24 = daily)
    horizonte: Optional[int]  # horas maximas de previsao
    unidade: str


# ───────────────────────── Presets ─────────────────────────
# NOTA: estes templates sao ilustrativos. Ajuste os url_path para o seu
# ambiente. O servidor FTP do CPTEC tem layouts diferentes por modelo.

MODELS: dict[str, ModelConfig] = {
    "Eta_5km": {
        "nome": "Eta 5 km (Regional)",
        "url_path": "https://ftp1.cptec.inpe.br/modelos/tempo/Eta/{escopo1}/{yyyy}/{mm}/{dd}/{hh}/",
        "file_name": "{prefixo}_eta05_{yyyymmddhh}_{F%3}.{ext}",
        "extensao": ".png",
        "extensao_tif": ".tif",
        "same_url_for_tif": True,
        "same_name_for_tif": True,
        "escopo1": "AS",
        "escopo2": "",
        "maxPassos": 120,
    },
    "Eta_10km": {
        "nome": "Eta 10 km (Regional)",
        "url_path": "https://ftp1.cptec.inpe.br/modelos/tempo/Eta/{escopo1}/{yyyy}/{mm}/{dd}/{hh}/",
        "file_name": "{prefixo}_eta10_{yyyymmddhh}_{F%3}.{ext}",
        "extensao": ".png",
        "extensao_tif": ".tif",
        "same_url_for_tif": True,
        "same_name_for_tif": True,
        "escopo1": "AS",
        "escopo2": "",
        "maxPassos": 240,
    },
    "BAM": {
        "nome": "BAM Global",
        "url_path": "https://ftp1.cptec.inpe.br/modelos/tempo/BAM/{yyyy}/{mm}/{dd}/{hh}/",
        "file_name": "{prefixo}_bam_{yyyymmddhh}_{F%3}.{ext}",
        "extensao": ".png",
        "extensao_tif": ".tif",
        "same_url_for_tif": True,
        "same_name_for_tif": True,
        "escopo1": "GL",
        "escopo2": "",
        "maxPassos": 360,
    },
    "MERGE": {
        "nome": "MERGE Precipitacao observada",
        "url_path": "https://ftp1.cptec.inpe.br/modelos/io/MERGE/CPTEC/DAILY/{yyyy}/{mm}/",
        "file_name": "MERGE_CPTEC_{yyyymmddhh}.{ext}",
        "extensao": ".png",
        "extensao_tif": ".tif",
        "same_url_for_tif": True,
        "same_name_for_tif": True,
        "escopo1": "",
        "escopo2": "",
        "maxPassos": 1,
    },
    "GFS": {
        "nome": "GFS 0.25 Global",
        "url_path": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{yyyymmddhh}/",
        "file_name": "gfs.t{hh}z.pgrb2.0p25.f{F%3}",
        "extensao": "",
        "extensao_tif": "",
        "same_url_for_tif": True,
        "same_name_for_tif": True,
        "escopo1": "",
        "escopo2": "",
        "maxPassos": 240,
    },
}


VARIABLES: dict[str, VariableConfig] = {
    "PREC": {
        "id": "PREC", "label": "Precipitacao",
        "prefixo": "PREC", "frequencia": 1,
        "horizonte": 120, "unidade": "mm/h",
    },
    "PREC_24h": {
        "id": "PREC", "label": "Precipitacao acumulada 24h",
        "prefixo": "PREC", "frequencia": 24,
        "horizonte": 240, "unidade": "mm/24h",
    },
    "T2M": {
        "id": "T2M", "label": "Temperatura 2m",
        "prefixo": "TEMP", "frequencia": 1,
        "horizonte": 120, "unidade": "C",
    },
    "U10M": {
        "id": "U10M", "label": "Vento U 10m",
        "prefixo": "U10M", "frequencia": 1,
        "horizonte": 120, "unidade": "m/s",
    },
    "V10M": {
        "id": "V10M", "label": "Vento V 10m",
        "prefixo": "V10M", "frequencia": 1,
        "horizonte": 120, "unidade": "m/s",
    },
    "PRESS": {
        "id": "PRESS", "label": "Pressao a superficie",
        "prefixo": "PRESS", "frequencia": 1,
        "horizonte": 120, "unidade": "hPa",
    },
    "UR": {
        "id": "UR", "label": "Umidade relativa 2m",
        "prefixo": "UR", "frequencia": 1,
        "horizonte": 120, "unidade": "%",
    },
}


def list_models() -> list[str]:
    """Lista as chaves do registry de modelos."""
    return sorted(MODELS.keys())


def list_variables() -> list[str]:
    """Lista as chaves do registry de variaveis."""
    return sorted(VARIABLES.keys())

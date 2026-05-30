"""
url_builder.py — porta para Python do `montarURL()` do frontend.

Resolve templates de URL/file_name com placeholders:
  {yyyy}, {mm}, {dd}, {hh}     — data da rodada (dataRodada=YYYYMMDDHH)
  {yyyymmddhh}                  — concatenacao completa
  {escopo1}, {escopo2}          — tokens 1/2 do modelo
  {prefixo}                     — prefixo da variavel
  {N} ou {N%4}                  — indice da figura (1, 2, 3...)  %N padding
  {F} ou {F%4}                  — horas de previsao (= idx × freq)
  {fct} ou {f%4}                — idem F com prefixo 'f'
  {ext}                         — extensao (.png, .tif, etc)
"""
import re
from datetime import datetime, timedelta


def _pad(value: int, spec: str | None) -> str:
    if spec is None:
        return str(value)
    n = int(spec)
    return str(value).zfill(n)


def _apply_data_placeholders(template: str, ano: str, mes: str, dia: str, hora: str) -> str:
    template = template.replace("{yyyy}", ano)
    template = template.replace("{mm}", mes)
    template = template.replace("{dd}", dia)
    template = template.replace("{hh}", hora)
    template = template.replace("{yyyymmddhh}", f"{ano}{mes}{dia}{hora}")
    return template


def _apply_scopes(template: str, escopo1: str, escopo2: str) -> str:
    return template.replace("{escopo1}", escopo1).replace("{escopo2}", escopo2)


def _apply_index_placeholders(template: str, idx: int, passo_h: int, ext: str, prefixo: str) -> str:
    # {N%4} / {N}
    def rep_n(m):
        return _pad(idx, m.group(1))
    template = re.sub(r"\{N(?:%(\d+))?\}", rep_n, template)
    def rep_f(m):
        return _pad(passo_h, m.group(1))
    template = re.sub(r"\{F(?:%(\d+))?\}", rep_f, template)
    def rep_fct(m):
        return "f" + _pad(passo_h, m.group(1))
    template = re.sub(r"\{(?:fct|f)(?:%(\d+))?\}", rep_fct, template)
    template = template.replace("{prefixo}", prefixo or "")
    template = template.replace("{ext}", ext or "")
    return template


def parse_dataRodada(dataRodada: str) -> tuple[str, str, str, str]:
    """dataRodada formato YYYYMMDDHH (10 chars). Retorna (yyyy, mm, dd, hh)."""
    if not dataRodada or len(dataRodada) < 10:
        raise ValueError(f"dataRodada invalida: {dataRodada!r} (esperado YYYYMMDDHH)")
    return dataRodada[0:4], dataRodada[4:6], dataRodada[6:8], dataRodada[8:10]


def montarURL(
    *,
    modelo_cfg: dict,
    variavel_cfg: dict,
    dataRodada: str,
    passo_h: int,
    freq: int,
    use_tif: bool = True,
) -> str:
    """
    Constroi a URL completa para um TIF (ou PNG) num passo especifico.

    modelo_cfg deve conter:
      - url_path, file_name (templates principais)
      - url_path_tif, file_name_tif (opcional, se rotas separadas para TIF)
      - same_url_for_tif, same_name_for_tif (booleans)
      - extensao (default '.png') e extensao_tif (default '.tif')
      - escopo1, escopo2 (default '')

    variavel_cfg deve conter:
      - prefixo (default '')
    """
    yyyy, mm, dd, hh = parse_dataRodada(dataRodada)
    escopo1 = modelo_cfg.get("escopo1") or ""
    escopo2 = modelo_cfg.get("escopo2") or ""
    prefixo = variavel_cfg.get("prefixo") or ""

    if use_tif:
        # Decide qual template usar para TIF
        if modelo_cfg.get("same_url_for_tif", False) or not modelo_cfg.get("url_path_tif"):
            url_template = modelo_cfg.get("url_path", "")
        else:
            url_template = modelo_cfg.get("url_path_tif", "")
        if modelo_cfg.get("same_name_for_tif", False) or not modelo_cfg.get("file_name_tif"):
            name_template = modelo_cfg.get("file_name", "")
        else:
            name_template = modelo_cfg.get("file_name_tif", "")
        ext = modelo_cfg.get("extensao_tif", ".tif")
    else:
        url_template = modelo_cfg.get("url_path", "")
        name_template = modelo_cfg.get("file_name", "")
        ext = modelo_cfg.get("extensao", ".png")

    idx = passo_h // max(freq, 1) if freq > 0 else passo_h

    url_template = _apply_data_placeholders(url_template, yyyy, mm, dd, hh)
    url_template = _apply_scopes(url_template, escopo1, escopo2)

    name_template = _apply_data_placeholders(name_template, yyyy, mm, dd, hh)
    name_template = _apply_scopes(name_template, escopo1, escopo2)
    name_template = _apply_index_placeholders(name_template, idx, passo_h, ext, prefixo)

    # Garante que url_template termina com /
    if url_template and not url_template.endswith("/"):
        url_template = url_template + "/"

    return url_template + name_template


def passo_validity_time(dataRodada: str, passo_h: int) -> datetime:
    """Retorna a data/hora de validade UTC = rodada + passo_h horas."""
    yyyy, mm, dd, hh = parse_dataRodada(dataRodada)
    base = datetime(int(yyyy), int(mm), int(dd), int(hh))
    return base + timedelta(hours=passo_h)

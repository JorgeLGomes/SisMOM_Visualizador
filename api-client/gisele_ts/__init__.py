"""
gisele_ts — Cliente Python para a API de extracao de serie temporal do GISELE.

Uso basico:

    from gisele_ts import GiseleClient, MODELS

    client = GiseleClient(base_url="http://127.0.0.1:8000")
    ts = client.timeseries(
        modelo=MODELS["Eta_5km"],
        variavel={"id": "PREC", "label": "Precipitacao", "prefixo": "PREC",
                  "frequencia": 1, "horizonte": 120},
        data_rodada="2026053000",
        lat=-20.0, lon=-45.0,
    )

    print(ts.dataframe())   # pandas DataFrame
    ts.to_csv("eta_prec.csv")

CLI:

    python -m gisele_ts --model Eta_5km --var PREC --date 2026053000 \\
        --lat -20 --lon -45 -o eta_prec.csv
"""

from gisele_ts.client import GiseleClient, TimeSeries, TimeSeriesSample
from gisele_ts.models import MODELS, VARIABLES

__version__ = "0.1.0"
__all__ = ["GiseleClient", "TimeSeries", "TimeSeriesSample", "MODELS", "VARIABLES"]

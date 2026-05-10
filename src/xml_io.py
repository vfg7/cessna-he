"""
xml_io.py
=========
Funções para leitura e edição dos XMLs de input/output do FAST-OAD.

Responsabilidade única: I/O de arquivo XML.
Nenhuma lógica de simulação ou análise aqui.
"""

import logging
from pathlib import Path

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def update_input_xml(
    xml_path: str | Path,
    distance_nmi: float,
    hybridization: float,
    n_motors: int,
) -> None:
    """
    Edita o XML de input do FAST-OAD com os parâmetros da iteração atual.

    Modifica in-place:
      - ``data/TLAR/range`` → distance_nmi  [nmi]
      - ``data/propulsion/.../thrust_distribution`` → distribuição entre
        motor termal (1.0) e N motores elétricos (thrust_part cada)

    Parameters
    ----------
    xml_path:
        Caminho completo para o XML de input.
    distance_nmi:
        Distância de missão em nmi.
    hybridization:
        Grau de hibridização He = P_elétrica / P_total.  Ex: 0.10
    n_motors:
        Número de motores elétricos.
    """
    xml_path = Path(xml_path)

    with xml_path.open("r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "xml")

    # --- range ---
    range_tag = soup.find("TLAR").find("range")
    old_val = range_tag.text
    range_tag.string = str(distance_nmi)
    range_tag["units"] = "nmi"
    logger.debug("Range: %s → %s nmi", old_val, distance_nmi)

    # --- thrust distribution ---
    # thrust_part = fração de empuxo de cada motor elétrico relativa ao motor termal
    # Derivação: He = n * T_e / (T_therm + n * T_e)
    #            → T_e / T_therm = He / (n * (1 - He))
    if hybridization >= 1.0:
        raise ValueError(f"hybridization deve ser < 1.0, recebido {hybridization}")

    thrust_part = hybridization / (n_motors * (1.0 - hybridization))
    thrust_distribution = [1.0] + [thrust_part] * n_motors

    thrust_tag = soup.find("thrust_distribution")
    thrust_tag.string = str(thrust_distribution)
    logger.debug("Thrust distribution: %s", thrust_distribution)

    with xml_path.open("w", encoding="utf-8") as f:
        f.write(str(soup))

    logger.info(
        "Input XML atualizado: dist=%.1f nmi, He=%.2f, n_motors=%d",
        distance_nmi, hybridization, n_motors,
    )

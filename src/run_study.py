"""
run_study.py
============
Script principal do estudo paramétrico de hibridização do Caravan DEP.

Orquestra o loop rho × dist × he e delega cada responsabilidade para o
módulo adequado. Não contém lógica de negócio — só sequência.

Uso:
    python run_study.py

Saída:
    Arquivo CSV com os resultados de todas as iterações.
"""

import logging
import os.path as pth
from pathlib import Path

import pandas as pd

import config as cfg
from xml_io import update_input_xml
from simulation import run_simulation
from postprocessing import plot_results
from data_extraction import extract_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers do loop
# ---------------------------------------------------------------------------

def _baseline_row(distance: float) -> dict:
    """
    Retorna a linha de baseline para uma distância de missão,
    usando o BASELINE_MAP de config.py para encontrar o baseline correto.
    """
    baseline_key = cfg.BASELINE_MAP.get(distance)
    if baseline_key is None:
        logger.warning("Baseline não definido para distância %.1f nmi — pulando.", distance)
        return {}

    values = cfg.BASELINES[baseline_key]
    return dict(zip(cfg.DATAFRAME_COLUMNS, values))


def _study_row(
    battery_density: float,
    distance: float,
    hybridization: float,
    metrics: dict,
    baseline_emissions: float | None,
) -> dict:
    """
    Monta a linha de resultado para uma iteração do estudo.
    Calcula red_emission em relação à baseline da distância.
    """
    row = {
        "rho_bat": battery_density,
        "range_nmi": distance,
        "he": hybridization,
    }
    row.update(metrics)

    # Redução de emissões em relação à baseline (%)
    if baseline_emissions and metrics.get("total_emissions") is not None:
        row["red_emission"] = (
            100.0 * (metrics["total_emissions"] - baseline_emissions) / baseline_emissions
        )
    else:
        row["red_emission"] = None

    return row


# ---------------------------------------------------------------------------
# Loop principal
# ---------------------------------------------------------------------------

def run_study() -> pd.DataFrame:
    """
    Executa o estudo paramétrico completo e retorna o DataFrame de resultados.
    Também salva o CSV incrementalmente a cada distância concluída.
    """
    all_rows: list[dict] = []
    input_xml_path = Path(cfg.DATA_FOLDER) / cfg.INPUT_XML_NAME

    for battery_density in cfg.BATTERY_DENSITIES:
        for distance in cfg.DISTANCES:

            # --- Linha de baseline para esta distância ---
            baseline = _baseline_row(distance)
            if baseline:
                all_rows.append(baseline)
                baseline_emissions = baseline.get("total_emissions")
            else:
                baseline_emissions = None

            for hybridization in cfg.HYBRIDIZATION_LEVELS:

                logger.info(
                    ">>> Rodando: rho=%.0f Wh/kg | dist=%.0f nmi | He=%.2f",
                    battery_density, distance, hybridization,
                )

                # 1. Atualiza o XML de input com os parâmetros da iteração
                update_input_xml(
                    xml_path=input_xml_path,
                    distance_nmi=distance,
                    hybridization=hybridization,
                    n_motors=cfg.N_ELECTRIC_MOTORS,
                )

                # 2. Roda a simulação FAST-OAD
                run_simulation(
                    data_folder=cfg.DATA_FOLDER,
                    process_config_name=cfg.PROCESS_CONFIG_NAME,
                    input_xml_name=cfg.INPUT_XML_NAME.lower(),  # FAST-OAD usa minúsculo
                    battery_density=battery_density,
                )

                # 3. Extrai métricas do XML de output
                output_xml = Path(cfg.RESULTS_FOLDER) / cfg.OUTPUT_XML_NAME
                metrics = extract_metrics(output_xml, n_motors=cfg.N_ELECTRIC_MOTORS)

                # 4. Gera plots
                plot_results(
                    results_folder=cfg.RESULTS_FOLDER,
                    data_folder=cfg.DATA_FOLDER,
                    output_xml_name=cfg.OUTPUT_XML_NAME,
                    powertrain_config_name=cfg.POWERTRAIN_CONFIG_NAME,
                )

                # 5. Acumula resultado
                row = _study_row(battery_density, distance, hybridization, metrics, baseline_emissions)
                all_rows.append(row)

            # Linha separadora entre distâncias (mantém legibilidade do CSV)
            all_rows.append({col: "-" for col in cfg.DATAFRAME_COLUMNS})

        # Salva CSV incrementalmente após cada densidade
        df = pd.DataFrame(all_rows, columns=cfg.DATAFRAME_COLUMNS)
        csv_name = f"resultados_rho{int(battery_density)}.csv"
        df.to_csv(csv_name, index=True)
        logger.info("CSV salvo: %s", csv_name)

    return pd.DataFrame(all_rows, columns=cfg.DATAFRAME_COLUMNS)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    df = run_study()
    print(df.to_string())

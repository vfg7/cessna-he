"""
postprocessing.py
=================
Geração de gráficos a partir dos resultados de simulação.

Agrupa as chamadas de visualização para manter o loop principal limpo.
"""

import logging
import os.path as pth

import fastga.utils.postprocessing.analysis_and_plots as api_plots
from fastga_he.gui.power_train_network_viewer import power_train_network_viewer
from fastga_he.gui.power_train_weight_breakdown import power_train_mass_breakdown

logger = logging.getLogger(__name__)


def plot_results(
    results_folder: str,
    data_folder: str,
    output_xml_name: str,
    powertrain_config_name: str,
) -> None:
    """
    Exibe os gráficos de breakdown de massa para uma simulação.

    Parameters
    ----------
    results_folder:
        Pasta com o XML de output do FAST-OAD.
    data_folder:
        Pasta com o YAML de configuração do powertrain.
    output_xml_name:
        Nome do XML de output (ex: ``oad_process_outputs_CaravanDEP_retrofit_2_036.xml``).
    powertrain_config_name:
        Nome do YAML do powertrain (ex: ``CaravanDEP_powertrain_retrofit_2.yml``).
    """
    path_to_result = pth.join(results_folder, output_xml_name)
    path_to_pt = pth.join(data_folder, powertrain_config_name)

    # --- Breakdown de massa do powertrain elétrico ---
    fig = power_train_mass_breakdown(path_to_result, path_to_pt)
    fig.update_layout(uniformtext=dict(minsize=28))
    fig.update_traces(textfont=dict(family=["Arial Black", "Arial"], size=[30]))
    fig.show()

    # --- Breakdown de massa geral da aeronave ---
    fig = api_plots.mass_breakdown_bar_plot(path_to_result)
    fig.show()

    logger.info("Plots gerados para %s", output_xml_name)

"""
simulation.py
=============
Configuração e execução do problema FAST-OAD.

Recebe os paths já resolvidos e executa uma única simulação.
Não sabe nada sobre o loop de estudo nem sobre plots.
"""

import logging
import os.path as pth

import fastoad.api as oad

from utils.filter_residuals import filter_residuals

logger = logging.getLogger(__name__)


def run_simulation(
    data_folder: str,
    process_config_name: str,
    input_xml_name: str,
    battery_density: float,
) -> None:
    """
    Executa uma única simulação FAST-OAD para a configuração dada.

    Parameters
    ----------
    data_folder:
        Pasta com os arquivos de configuração do FAST-OAD.
    process_config_name:
        Nome do arquivo YAML de processo (ex: ``CaravanDEP_retrofit.yml``).
    input_xml_name:
        Nome do XML de input (ex: ``input_CaravanDEP_2_036.xml``).
        Atenção: FAST-OAD é case-sensitive — use o nome em minúsculo aqui
        se o arquivo no disco estiver em minúsculo.
    battery_density:
        Densidade da bateria [Wh/kg]. Usada para escalar o model_option
        ``cell_weight_ref``.
    """
    # Suprime logs verbosos de módulos internos do FAST-OAD
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("fastoad.module_management._bundle_loader").disabled = True
    logging.getLogger("fastoad.openmdao.variables.variable").disabled = True

    process_file = pth.join(data_folder, process_config_name)
    ref_inputs = pth.join(data_folder, input_xml_name)

    configurator = oad.FASTOADProblemConfigurator(process_file)
    problem = configurator.get_problem()

    # model_options:
    #   - propeller_1: massa como input (não calculada internamente)
    #   - cell_weight_ref: escala o modelo de massa de bateria com a densidade
    problem.model_options["*propeller_1*"] = {"mass_as_input": True}
    problem.model_options["*"] = {
        "cell_weight_ref": _cell_weight_ref(battery_density)
    }

    problem.write_needed_inputs(ref_inputs)
    problem.read_inputs()
    problem.setup()
    problem.run_model()

    _, _, residuals = problem.model.get_nonlinear_vectors()
    residuals = filter_residuals(residuals)

    problem.write_outputs()

    logger.info(
        "Simulação concluída — density=%.0f Wh/kg", battery_density
    )


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------

def _cell_weight_ref(density: float) -> float:
    """
    Converte densidade [Wh/kg] para o parâmetro interno ``cell_weight_ref``.

    O modelo interno calibra com 50 mAh a 261 Wh/kg → 50e-3 * 261 / density.
    """
    BASE = 50.0e-3 * 261.0  # [kg * Wh/kg]
    if density <= 0:
        raise ValueError(f"Densidade deve ser positiva, recebida: {density}")
    return BASE / density

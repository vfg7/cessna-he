"""
data_extraction.py
==================
Extrai métricas de interesse do XML de output do FAST-OAD.

Esta é a versão limpa e consolidada das duas tentativas comentadas no script
original. A lógica foi unificada em uma única função pública e em helpers
privados coesos.

Filosofia:
  - Navegação pelo ElementTree da biblioteca padrão (sem BeautifulSoup aqui —
    o XML de output é gerado pelo FAST-OAD e é bem-formado).
  - Falha explícita: se um campo esperado não é encontrado, retorna None
    (e loga um aviso), em vez de explodir ou retornar string vazia silenciosamente.
"""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Interface pública
# ---------------------------------------------------------------------------

def extract_metrics(result_xml_path: str | Path, n_motors: int) -> dict:
    """
    Lê o XML de output do FAST-OAD e retorna um dicionário de métricas.

    Parameters
    ----------
    result_xml_path:
        Caminho para o XML de output (ex: ``results/oad_process_outputs_*.xml``).
    n_motors:
        Número de motores elétricos — necessário para somar massas indexadas
        (dc_bus_1 … dc_bus_N, harness_1 … harness_N, etc.).

    Returns
    -------
    dict com as chaves definidas em DATAFRAME_COLUMNS (exceto rho_bat, range_nmi, he,
    red_emission — essas são preenchidas pelo loop principal em run_study.py):
        fuel_mass, emission_factor, total_emissions,
        OWE, payload, empty_mass,
        he_mass, dc_dc_mass, dc_bus_mass, dc_cable_harn,
        motor_mass, battery_mass, fuel_flowed,
        inverter_mass, turboshaft_mass
    """
    tree = ET.parse(str(result_xml_path))
    root = tree.getroot()
    data = _find_data_node(root)

    metrics: dict = {}

    # --- Missão ---
    metrics["fuel_mass"] = _scalar(data, "mission/sizing/fuel")

    # --- Impacto ambiental ---
    metrics["emission_factor"] = _scalar(data, "environmental_impact/sizing/emission_factor")
    raw_emissions = _scalar(data, "environmental_impact/sizing/emissions")
    metrics["total_emissions"] = raw_emissions / 1000.0 if raw_emissions is not None else None

    # --- Massas da aeronave ---
    metrics["OWE"] = _scalar(data, "weight/aircraft/OWE")
    metrics["payload"] = _scalar(data, "weight/aircraft/payload")
    metrics["empty_mass"] = _scalar(data, "weight/aircraft_empty/mass")

    # --- Powertrain elétrico (he_power_train) ---
    he = data.find("propulsion/he_power_train")
    if he is None:
        logger.warning("Nó propulsion/he_power_train não encontrado em %s", result_xml_path)
        return metrics

    metrics["he_mass"] = _child_scalar(he, "mass")
    metrics["dc_dc_mass"] = _child_scalar(he, "DC_DC_converter/dc_dc_converter_1/mass")
    metrics["battery_mass"] = _child_scalar(he, "battery_pack/battery_pack_1/mass")
    metrics["fuel_flowed"] = _child_scalar(he, "fuel_system/fuel_system_1/total_fuel_flowed")
    metrics["turboshaft_mass"] = _child_scalar(he, "turboshaft/turboshaft_1/mass")

    # --- Somas por componente (indexadas de 1 a n_motors) ---
    metrics["dc_bus_mass"] = _sum_component_masses(
        he, branch="DC_bus", components=["bus_nose"] + [f"dc_bus_{i}" for i in range(1, n_motors + 1)]
    )
    metrics["dc_cable_harn"] = _sum_indexed_masses(
        he, branch="DC_cable_harness", prefix="harness_", n=n_motors,
        extra_paths=["contactor/mass"],
    )
    metrics["motor_mass"] = _sum_indexed_masses(
        he, branch="PMSM", prefix="motor_", n=n_motors,
    )
    metrics["inverter_mass"] = _sum_indexed_masses(
        he, branch="inverter", prefix="inverter_", n=n_motors,
        direct_child_only=True,  # não soma subcomponentes (capacitor, contactor, casing...)
    )

    return metrics


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------

def _find_data_node(root: ET.Element) -> ET.Element:
    """Localiza o nó <data> independente de onde o FAST-OAD o colocou."""
    for path in ("./data", "./FASTOAD_model/data", ".//data"):
        node = root.find(path)
        if node is not None:
            return node
    raise ValueError("Nó <data> não encontrado no XML de output.")


def _scalar(data: ET.Element, path: str) -> float | None:
    """Retorna o valor float do primeiro elemento encontrado no path dado."""
    node = data.find(path)
    if node is None:
        logger.warning("Campo não encontrado: %s", path)
        return None
    try:
        return float(node.text.strip())
    except (ValueError, AttributeError):
        logger.warning("Valor não-numérico em %s: %r", path, node.text)
        return None


def _child_scalar(parent: ET.Element, path: str) -> float | None:
    """Igual a _scalar mas relativo a um nó pai já resolvido."""
    node = parent.find(path)
    if node is None:
        logger.warning("Sub-campo não encontrado: %s", path)
        return None
    try:
        return float(node.text.strip())
    except (ValueError, AttributeError):
        logger.warning("Valor não-numérico em sub-campo %s: %r", path, node.text)
        return None


def _sum_component_masses(
    parent: ET.Element,
    branch: str,
    components: list[str],
) -> float | None:
    """
    Soma <mass> de uma lista explícita de sub-componentes dentro de branch.

    Usado para dc_bus onde há bus_nose + dc_bus_1 … dc_bus_N.
    """
    branch_node = parent.find(branch)
    if branch_node is None:
        logger.warning("Branch não encontrada: %s", branch)
        return None

    total = 0.0
    found_any = False
    for comp in components:
        mass_node = branch_node.find(f"{comp}/mass")
        # fallback: tenta <comp> como texto direto
        if mass_node is None:
            mass_node = branch_node.find(comp)
        if mass_node is not None:
            try:
                total += float(mass_node.text.strip())
                found_any = True
            except (ValueError, AttributeError):
                logger.warning("Valor inválido em %s/%s", branch, comp)

    return total if found_any else None


def _sum_indexed_masses(
    parent: ET.Element,
    branch: str,
    prefix: str,
    n: int,
    extra_paths: list[str] | None = None,
    direct_child_only: bool = False,
) -> float | None:
    """
    Soma <mass> de componentes indexados prefix_1 … prefix_N dentro de branch.

    Parameters
    ----------
    extra_paths:
        Paths adicionais relativos a cada componente indexado para somar
        (ex: ["contactor/mass"] para harness).
    direct_child_only:
        Se True, soma apenas o <mass> filho direto do componente indexado,
        ignorando sub-componentes (usado para inverter, que tem capacitor,
        contactor, casing com suas próprias <mass>).
    """
    branch_node = parent.find(branch)
    if branch_node is None:
        logger.warning("Branch não encontrada: %s", branch)
        return None

    total = 0.0
    found_any = False

    for i in range(1, n + 1):
        comp_tag = f"{prefix}{i}"
        comp_node = branch_node.find(comp_tag)
        if comp_node is None:
            logger.warning("Componente não encontrado: %s/%s", branch, comp_tag)
            continue

        # Massa direta do componente
        mass_node = comp_node.find("mass")
        if mass_node is not None:
            try:
                total += float(mass_node.text.strip())
                found_any = True
            except (ValueError, AttributeError):
                pass

        # Massas extras (ex: contactor) — só se não for direct_child_only
        if not direct_child_only and extra_paths:
            for ep in extra_paths:
                extra_node = comp_node.find(ep)
                if extra_node is not None:
                    try:
                        total += float(extra_node.text.strip())
                    except (ValueError, AttributeError):
                        pass

    return total if found_any else None

"""
config.py
=========
Parâmetros globais do estudo de hibridização do Caravan DEP.

Mexa APENAS aqui para configurar uma nova rodada:
  - densidades de bateria, distâncias, graus de hibridização
  - número de motores elétricos
  - paths dos arquivos de entrada/saída
"""

# ---------------------------------------------------------------------------
# Parâmetros de estudo
# ---------------------------------------------------------------------------

#: Densidades de bateria a estudar [Wh/kg]
BATTERY_DENSITIES: list[float] = [350.0]  # ex: [300.0, 350.0, 400.0, 500.0]

#: Distâncias de missão a estudar [nmi]
DISTANCES: list[float] = [250.0]  # ex: [100.0, ..., 500.0]

#: Graus de hibridização He = P_elétrica / P_total
HYBRIDIZATION_LEVELS: list[float] = [0.10]  # ex: [0.0, 0.05, 0.10, ...]

#: Número de motores elétricos instalados
N_ELECTRIC_MOTORS: int = 2

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DATA_FOLDER: str = "data"
RESULTS_FOLDER: str = "results"

#: Nome do XML de input (dentro de DATA_FOLDER)
#  Convenção: Input_CaravanDEP_{N}_{code}.xml
# INPUT_XML_NAME: str = "Input_CaravanDEP_2_036.xml"
INPUT_XML_NAME: str = "Input_CaravanDEP_2_036.xml"

#: Nome do XML de output gerado pelo FAST-OAD (dentro de RESULTS_FOLDER)
OUTPUT_XML_NAME: str = "oad_process_outputs_CaravanDEP_retrofit_2_036.xml"

#: Arquivo de configuração do processo FAST-OAD (dentro de DATA_FOLDER)
PROCESS_CONFIG_NAME: str = "CaravanDEP_retrofit.yml"

#: Arquivo de configuração do powertrain (dentro de DATA_FOLDER)
POWERTRAIN_CONFIG_NAME: str = "CaravanDEP_powertrain_retrofit_2.yml"

# ---------------------------------------------------------------------------
# Referência de massa da célula para o model_options
# ---------------------------------------------------------------------------
#: Massa de referência da célula em kg (usada para escalar com a densidade)
#  Fórmula: cell_weight_ref = 50e-3 * 261 / rho
CELL_MASS_BASE_NUMERATOR: float = 50.0e-3 * 261.0  # [kg * Wh/kg]

# ---------------------------------------------------------------------------
# Baselines de comparação
# ---------------------------------------------------------------------------
# Colunas na ordem:
#   rho_bat | range_nmi | he | fuel_mass | emission_factor | total_emissions
#   red_emission | OWE | payload | empty_mass | he_mass | dc_dc_mass
#   dc_bus_mass | dc_cable_harn | motor_mass | battery_mass
#   fuel_flowed | inverter_mass | turboshaft_mass
_MISSING = "-"  # marcador para campo não disponível na baseline

BASELINES: dict[float, list] = {
    150.0: [_MISSING, _MISSING, _MISSING,
            255.05, 3.07, 972.80, 0,
            2378.74, 1140.00, 2270.00,
            *[_MISSING] * 9],
    250.0: [_MISSING, _MISSING, _MISSING,
            349.60, 2.53, 1333.40, 0,
            2378.74, 1140.00, 2270.00,
            *[_MISSING] * 9],
    500.0: [_MISSING, _MISSING, _MISSING,
            590.13, 2.13, 2250.80, 0,
            2378.74, 1140.00, 2270.00,
            *[_MISSING] * 9],
}

#: Quais distâncias têm baseline definido
BASELINE_MAP: dict[float, float] = {
    # distância_missão → chave em BASELINES
    100.0: 150.0,
    150.0: 150.0,
    200.0: 150.0,
    250.0: 250.0,
    300.0: 250.0,
    350.0: 250.0,
    400.0: 500.0,
    450.0: 500.0,
    500.0: 500.0,
}

# ---------------------------------------------------------------------------
# Colunas do DataFrame de resultados
# ---------------------------------------------------------------------------
DATAFRAME_COLUMNS: list[str] = [
    "rho_bat", "range_nmi", "he",
    "fuel_mass", "emission_factor", "total_emissions", "red_emission",
    "OWE", "payload", "empty_mass",
    "he_mass", "dc_dc_mass", "dc_bus_mass", "dc_cable_harn",
    "motor_mass", "battery_mass", "fuel_flowed",
    "inverter_mass", "turboshaft_mass",
]

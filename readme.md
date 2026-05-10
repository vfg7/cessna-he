# CaravanDEP Study

Estudo paramétrico de hibridização elétrica da aeronave Cessna Caravan com propulsão distribuída (DEP — Distributed Electric Propulsion).

Simula combinações de densidade de bateria, distância de missão e grau de hibridização, gerando métricas de massa, emissões e consumo de combustível via FAST-OAD.

---

## Estrutura do projeto

```
root/
├── FAST-OAD-CS23-HE/       # Repo local — plugin de powertrain híbrido (clone do Florent em https://github.com/florentLutz/FAST-OAD-CS23-HE)
├── src/                    # Código do estudo
│   ├── config.py           # Parâmetros do estudo (edite aqui antes de rodar)
│   ├── run_study.py        # Script principal
│   ├── xml_io.py           # Edição do XML de input
│   ├── simulation.py       # Execução do FAST-OAD
│   ├── data_extraction.py  # Extração de métricas do XML de output
│   ├── postprocessing.py   # Geração de plots
│   └── utils/              # Utilitários compartilhados
├── data/                   # XMLs de input e YAMLs de configuração
├── results/                # XMLs de output e CSVs gerados
├── pyproject.toml
├── requirements.txt
├── tales of debug.md       # onde conto a jornada de fazer funcionar
└── README.md
```

---

## Instalação

> Pré-requisito: Python 3.10 ou 3.11.

```bash
# 1. Clonar e entrar na raiz
git clone <repo-url>
cd <projeto>

# 2. Criar e ativar o ambiente virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

# 3. Instalar o FAST-OAD-CS23-HE local primeiro
pip install -e ./FAST-OAD-CS23-HE

# 4. Instalar o projeto com dependências de desenvolvimento
pip install -e ".[dev]"
```

### Correções manuais necessárias no FAST-OAD-CS23-HE

O repo local tem três incompatibilidades com versões atuais das dependências
que precisam ser corrigidas manualmente após o clone:

**1. Remover `aerosandbox` do `FAST-OAD-CS23-HE/pyproject.toml`**
Conflita com o pin `numpy<2.0` exigido pelo projeto.

**2. Corrigir import em `power_train_mass_rta.py`**
```
src/fastga_he/models/weight/mass_breakdown/b_propulsion/power_train_mass_rta.py
```
```python
# de:
from fastoad_cs25.models.weight.mass_breakdown.constants import SERVICE_PROPULSION_MASS
# para:
from fastga.models.weight.mass_breakdown.constants import SERVICE_PROPULSION_MASS
```

**3. Corrigir `np.sum` em `c_systems/sum.py`**
```
src/fastga_he/models/weight/mass_breakdown/c_systems/sum.py
```
```python
# de:
outputs["data:weight:systems:mass"] = np.sum(inputs.values())
# para:
outputs["data:weight:systems:mass"] = sum(inputs.values())
```

---

## Configuração

Edite `src/config.py` antes de rodar:

```python
BATTERY_DENSITIES = [350.0]        # Wh/kg
DISTANCES = [250.0]                # nmi
HYBRIDIZATION_LEVELS = [0.10]      # He = P_elétrica / P_total
N_ELECTRIC_MOTORS = 2
```

Certifique-se de que os arquivos de input em `data/` correspondem ao número
de motores configurado (`INPUT_XML_NAME`, `POWERTRAIN_CONFIG_NAME`).

---

## Execução

```bash
cd src
python run_study.py
```

O script gera um CSV por densidade de bateria em `src/` e exibe os plots
de breakdown de massa ao final de cada iteração.

---

## Dependências críticas e seus pins

| Pacote | Pin | Motivo |
|---|---|---|
| `numpy` | `>=1.23,<2.0` | NumPy 2.x quebra APIs usadas pelo fastga e fastga_he |
| `fast-oad-core` | `>=1.7.3,<1.8` | 1.9.0 puxa openmdao 3.42.0, incompatível com fastga_he |
| `openmdao` | `>=3.30,<3.38` | Exigência explícita do FAST-OAD-CS23-HE |

> ⚠️ Não faça upgrade dessas dependências sem testar a cadeia completa.

Referências e citações
Este projeto utiliza o framework FAST-OAD-CS23-HE, desenvolvido no ISAE-SUPAERO. Se este trabalho for publicado ou usado como base para pesquisa, cite os autores originais:
bibtex@article{lutz2025open,
  author  = {Lutz, Florent and Jezegou, Joel and Budinger, Marc and Reysset, Aurelien},
  title   = {Open-Source Framework for Sizing Hybrid and Electric General Aviation Aircraft},
  journal = {Journal of Aircraft},
  volume  = {62},
  number  = {2},
  pages   = {381-395},
  year    = {2025},
  doi     = {10.2514/1.C038004},
}

@article{habrard2025parametric,
  author  = {Habrard, Valentine and Pommier-Budinger, Valérie and Hazyuk, Ion and Jézégou, Joël and Benard, Emmanuel},
  title   = {Parametric Study of a Liquid Cooling Thermal Management System for Hybrid Fuel Cell Aircraft},
  journal = {Aerospace},
  volume  = {12},
  number  = {5},
  year    = {2025},
  doi     = {10.3390/aerospace12050377},
}


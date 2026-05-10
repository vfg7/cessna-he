### projeto do obeli: avião do elétrico híbrido

## dentro da raiz do projeto (da sua pasta):

# 1. setar um venv respeitando as constraints da lib do fast-oad
py -3.11 -m venv .venv 

ativar e desativar venv
Entrar:  
.\venv\Scripts\Activate.ps1 
(Windows PowerShell)
Sair: deactivate

# 2. Instalar FAST-OAD-CS23-HE
- clonei o repositório do florent com git clone <url do repo>

- pequena correção: alguns arquivos do trabalho parecem requerer códigos que estão na pasta utils do repo FAST-OAD-CS23-HE. No entanto, no arquivo pyproject.toml, o código importado sob a tag fastga_he é apenas o código contido na página src. Pra consertar isso e permitir a inclusã odos códigos em utils, foi feita uma pequena alteração:

```
packages = [
    { include = "fastga_he", from = "src" },
    { include = "utils" },

]
```

ele já é pensado pra ser um pacote, então instala como um. navega até a pasta no terminal e roda pip install -e . (o ponto é importante)

--- 

# 3. refatoração (reorganização) do código

## 3.1. entendendo o que o código faz (na ordem):

- Define parâmetros de estudo (densidades de bateria, distâncias, hibridização)
- Define baselines de comparação
- Loop duplo rho × dist × he — para cada combinação:
    - Edita um XML de input (range + distribuição de thrust)
    - Roda a simulação (test_retrofit_DEP)
    - Plota resultados (test_CaravanDEP_mass_breakdown)

- (~300 linhas comentadas de duas tentativas anteriores de extrair dados do XML de output)

## 3.2 Diagnóstico

- Problemas principais:

- Funções definidas dentro de um loop (redefine a cada iteração, por isso que o código demora pra rodar)
- Mistura de responsabilidades: config, I/O de XML, simulação e plots no mesmo escopo - separa cada coisa pra fazer cada coisa só uma vez e salvar na memória
- Código morto volumoso (as duas seções comentadas, só serve pra cagar a legibilidade. Quer manter o código legado? Cria uma seção notebook de códigos - antigos e joga lá)
- Nenhuma separação entre parâmetros e lógica (dificulta entendimento e atrasa o código, que fica num processo lógico confuso)
- Constantes hardcoded espalhadas (seta manualmente dados que dps você não sabe onde tá)

## 3.3 Reorganização

Com isso, a ideia foi propor uma arquitetura mais enxuta:

* config.py — Único lugar para mexer antes de rodar um estudo novo. Densidades, distâncias, grau de hibridização, número de motores, todos os paths. O BASELINE_MAP que estava implícito no código original (qual baseline usar para cada distância) virou explícito e documentado.

* xml_io.py — Responsabilidade única: editar o XML de input. A fórmula do thrust_part ganhou um comentário matemático derivando a equação — estava hardcoded no original sem explicação. Também tem validação: se He >= 1.0, falha com mensagem clara.

* simulation.py — Responsabilidade única: configurar e rodar o FAST-OAD. A constante mágica 50.0e-3 * 261.0 que aparecia no original virou a função _cell_weight_ref() com docstring explicando de onde vem.

* data_extraction.py — A parte mais importante da refatoração. As duas tentativas comentadas (~300 linhas) foram consolidadas em uma única implementação usando xml.etree.ElementTree (stdlib, sem deps extras). Cada tipo de extração — escalar, soma de lista explícita, soma indexada — virou um helper separado. O caso do inverter (direct_child_only=True) está explicitamente documentado.

* postprocessing.py — Isola as chamadas de fig.show(). Simples agora, mas fácil de evoluir para salvar as figuras em disco ou gerar um relatório.

* run_study.py — Um método principal, que roda tudo em sequência: atualiza XML → roda simulação → extrai métricas → plota → acumula. Sem lógica de negócio misturada. Salva o CSV incrementalmente por densidade, então se travar no meio do estudo não perde os dados anteriores.

## 4. Execução e testes

- da raiz do projeto Python src/run_study.py
(execute da raiz pra evitar erros de path)

## 5. log de erros 
### 5.1 ambiguidade do weight.mass.systems

O FAST-OAD encontrou dois submodelos registrados para o mesmo serviço service.weight.mass.systems:

- fastga.submodel.weight.mass.systems.legacy — vindo do fast-ga
- fastga_he.submodel.weight.mass.systems.weight_nan — vindo do FAST-OAD-CS23-HE

atualizei pro modelo do fastga_he

- submodel.weight.mass.systems: fastga_he.submodel.weight.mass.systems.weight_nan (linha 65 d0 caravande-_retrofit.yml)

### 5.2 Dependencias do fastga
- havia dificuldade em acessar algumas das dependencias do fastga-he, o que é um problema da biblioteca. Esse problema, por sinal, era a raiz do problema acima. Procurei a raiz do erro e achei que a dependencia fastoad-cs25 era a raiz do problema.
- Instalei com ``` pip install fast-oad-cs25 ```

o que não foi uma boa ideia. isso desenceadeou problemas de atualização da lib: 

- fastoad-cs25 requer openmdao 3.42, mas fast-oad-cs23-he exige openmdao<3.38
- fastoad-cs25 instalou fast-oad-core 1.9.0 que é incompatível com o fast-oad-cs23-he.
- fast-oad-core 1.9, por sua vez, requer openmdao >= 3.40

- Isso não tem solução limpa via gerenciamento de dependências — são dois pacotes com requisitos mutuamente exclusivos para o mesmo pacote base. Você precisaria de dois ambientes separados, o que derrota o propósito.

- A pergunta real aqui é: o fastoad-cs25 é de fato necessário para o projeto? Ele foi puxado porque o power_train_mass_rta.py importa SERVICE_PROPULSION_MASS dele. Busquei o repo e achei que era uma constante -  um detalhe de implementação do fast-oad-cs23-he, mas que quebra o código. Chequei no repo do Florent (o fast-oad-23, instalado no alias fast-ga) se havia a mesma constante. Caso positivo, então vamos atualizar os imports com dependencias desatualizadas, como:

```
# de:
from fastoad_cs25.models.weight.mass_breakdown.constants import SERVICE_PROPULSION_MASS

# para:
from fastga.models.weight.mass_breakdown.constants import SERVICE_PROPULSION_MASS
```

### 5.3 O projeto (ou o arquivo de projeto CaravanDEP_retrofit.yml)

- um corolário desse erro é que no arquivo de config (o .yml lá), não havia a linha correta pra importação da constante e foi necessário adicioná-la manualmente:

- ```service.weight.mass.payload: fastga.submodel.weight.mass.payload.legacy```, por exemplo.

- Daqui em geral, vários erros foram de configuração. Ou seja, o projeto do cessna caravan elétrico tá meio cagado na raiz. Por exemplo:
``` Output name 'data:weight:aircraft:payload' refers to multiple outputs:
['payload_update.data:weight:aircraft:payload', 
 'weight.mass_breakdown.payload.data:weight:aircraft:payload']
 ```
indica que esse termo não deveria ser nulo. Busquei a constante no fast-ga e add ao .yml:
```service.weight.mass.payload: fastga.submodel.weight.mass.payload.legacy ```

essa aqui, especificamente, foi um excelente exemplo pq gerou um confito de dados. Mudei pra null e resolveu o conflito. Ainda assim, estou achando mais erros, como:

### 5.3.1
```
fastoad.openmdao.exceptions.FASTOpenMDAONanInInputFile: (FASTOpenMDAONanInInputFile(...), "NaN values found in input file (C:/Users/victo/OneDrive/Documentos/obeli/results/oad_process_inputs_CaravanDEP_retrofit_2_036.xml). Please check following variables: ['data:TLAR:v_max_sl', 'data:geometry:wing:aspect_ratio', 'data:propulsion:he_power_train:DC_DC_converter:dc_dc_converter_1:efficiency_mission', 'data:propulsion:he_power_train:inverter:inverter_1:efficiency_mission', 'data:propulsion:he_power_train:inverter:inverter_1:junction_temperature_mission', 'data:propulsion:he_power_train:inverter:inverter_2:efficiency_mission', 'data:propulsion:he_power_train:inverter:inverter_2:junction_temperature_mission']
```

ou seja, o projeto não tá levando em consideração termos que parecem necessários. Ou a equipe provavelmente nunca precisou delas antes porque o modelo anterior não as exigia — são campos novos trazidos pelo fastga_he - ou é cagada.

### 5.3.2
```
data:propulsion:he_power_train:DC_DC_converter:dc_dc_converter_1:efficiency_mission
data:propulsion:he_power_train:inverter:inverter_1:efficiency_mission
data:propulsion:he_power_train:inverter:inverter_1:junction_temperature_mission
data:propulsion:he_power_train:inverter:inverter_2:efficiency_mission
data:propulsion:he_power_train:inverter:inverter_2:junction_temperature_mission
```

Esses são arrays do tamanho do número de pontos de missão (climb + cruise + descent + reserve = 30+30+20+10 = 90 pontos). O XML tem NaN porque foram geradas com shape (1,) pelo write_needed_inputs — o modelo ainda não sabia o tamanho correto.

- Evidências estavam no traceback (no relatório do erro), mas confesso que apelei pra IA interpretar kkkk 

## 5.4 Quickfixes

### 5.4.1 Consertando 5.3.1

- Pesquisando até pouco, deu pra achar dados físicos conhecidos do Cessna Caravan:
```
v_max_sl — velocidade máxima ao nível do mar: 175 knots (valor típico do Caravan)
aspect_ratio — razão de aspecto da asa: 9.67 (valor geométrico do Caravan)
```

podem ser que esses valores sejam outputs desejados (querem projetar um avião com alterações, certo? isso faz sentido do ponto de vista de projeto), mas, pq quebram o retrofit e já que a geometria da aeronave é fixa, vou fazer o quickfix de colocar os valores pra testar a simulação. No XML, 

```
<TLAR> -> adicionei: <v_max_sl units="knot" is_input="True">175.0</v_max_sl>

<aspect_ratio  is_input="True">9.67<!--_inp_data:geometry:wing:aspect_ratio--></aspect_ratio>
```

### 5.4.2: consertando 5.3.2

As variáveis existem no xml. como, por exemplo:
```<cell_temperature_mission units="degK">298.15</cell_temperature_mission>```

- o modelo espera arrays de 90 pontos (30 climb + 30 cruise + 20 descent + 10 reserve) mas o XML tem escalares (1,). O FAST-OAD trata isso como NaN de shape incompatível. Minha IA favorita chegou e achamos que há uma flag para resolver isso no YAML do processo: model -> nonlinear_solver. 

- E aí, especifiquei com:
```
input_file: ../data/Input_CaravanDEP_2_036.xml
check_inputs: False
```

nessa brincadeira, chequei também que:
```
dc_dc_converter_1:efficiency_mission
inverter_1:efficiency_mission
inverter_1:junction_temperature_mission
inverter_2:efficiency_mission
inverter_2:junction_temperature_mission
```

não estão no XML de input. Vacilo ou erro de projeto? Alá sabe responder. Eu, que não sou alá, não julgo.
Pesquisei valores físicos razoáveis pra aplicação e vou adicionar ao projeto

na seção: DC/DC converter
```<efficiency_mission is_input="True">0.95</efficiency_mission>```

nas seções: Inverter 1 e Inverter 2
```<efficiency_mission is_input="True">0.95</efficiency_mission>```
```<junction_temperature_mission is_input="True" units="degK">358.15</junction_temperature_mission>```

## 5.5 Bugs

### 5.5.1 bug de compatibilidade de versão do NumPy dentro do fastga_he.

O problema está em:
FAST-OAD-CS23-HE\src\fastga_he\models\weight\mass_breakdown\c_systems\sum.py, linha 89
```
outputs["data:weight:systems:mass"] = np.sum(inputs.values())
O np.sum(generator) foi depreciado no NumPy e agora lança TypeError
```

como tenho acesso direto ao arquivo FAST-OAD-CS23-HE\src\fastga_he\models\weight\mass_breakdown\c_systems\sum.py (onde o console apontou o erro) vou lá mudar. Linha 89: 
```
# de:
outputs["data:weight:systems:mass"] = np.sum(inputs.values())

# para:
outputs["data:weight:systems:mass"] = sum(inputs.values())
```

Chequei todas as outrsa instâncias m que poderia achar o msm bug:

```
FAST-OAD-CS23-HE\src\fastga_he\models\cost\lcc_certification_cost.py:59:        outputs["data:cost:production:certification_cost_per_unit"] = 
np.sum(inputs.values())
FAST-OAD-CS23-HE\src\fastga_he\models\cost\lcc_operational_cost_sum.py:91:        outputs["data:cost:operation:annual_cost_per_unit"] = np.sum(inputs.values())     
FAST-OAD-CS23-HE\src\fastga_he\models\cost\lcc_production_cost_sum.py:99:        outputs["data:cost:production_cost_per_unit"] = np.sum(inputs.values())
FAST-OAD-CS23-HE\src\fastga_he\models\environmental_impacts\lca_core_aggregation.py:18:        outputs["data:environmental_impact:single_score"] =
np.sum(inputs.values())
FAST-OAD-CS23-HE\src\fastga_he\models\weight\mass_breakdown\a_airframe\sum.py:95:        outputs["data:weight:airframe:mass"] = np.sum(inputs.values())
FAST-OAD-CS23-HE\src\fastga_he\models\weight\mass_breakdown\c_systems\sum.py:89:        # outputs["data:weight:systems:mass"] = np.sum(inputs.values())
```

E vou pra evitar merda. Yay! 
... claro que não. Imagino que, se isso está em tantos lugares também pode estar na lib original que não tenho acesso e não posso mudar na mão. Melhor sacar qual versão do numpy foi usada e trocar pra ela. **Isso deveria estar no pyproject da lib FAST-OAD-CS23-HE.** É má gestão de dependências.

- Chequei e numpy>=1.23,<2.0

- tentei instalar e recebi um erro alerta: aerosandbox 4.2.9 requires numpy>=2.2.6, but you have numpy 1.26.4 which is incompatible.
fast-oad-cs23-he 0.0.1 requires jupyterlab-widgets==3.0.15, but you have jupyterlab-widgets 1.1.11 which is incompatible.

- chequei e aerosandbox não é necessário e não estou usando notebooks. Então vamo seguir com isso.

# 6. RODOOOOOOOOOOOOU!
NÃO É NEM O MEU TRBALHO E FIQUEI FELIZ PRA CARALHO

# 7. Ah, e como usar isso aqui? 

Clona o repo pra tu, instala as dependencias e mete teu xml e yml de projeto. 

O passo a passo bonitinho:

# 1. Clonar e entrar na raiz
git clone <repo-url>
cd <projeto>

# 2. Criar e ativar o ambiente virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

# 3. Instalar o FAST-OAD-CS23-HE local primeiro
pip install -e ./FAST-OAD-CS23-HE

# 4. Instalar o projeto principal
pip install -e ".[dev]"

### Atenção antes de rodar:

Remover aerosandbox das dependências do FAST-OAD-CS23-HE/pyproject.toml
Corrigir o import em FAST-OAD-CS23-HE/src/fastga_he/models/weight/mass_breakdown/b_propulsion/power_train_mass_rta.py: trocar fastoad_cs25 por fastga
Corrigir np.sum(inputs.values()) → sum(inputs.values()) em c_systems/sum.py

Eu usei pip, mas é o equivalente ao poetry install para o ecossistema pip/setuptools. A diferença é que o Poetry gera um poetry.lock com versões exatas de todas as dependências transitivas (o que é mais seguro, confesso), enquanto o pip resolve na hora — mas com os pins que colocamos no pyproject.toml o resultado é igualmente determinístico para as dependências críticas.

### Execução:
da raiz do projeto, no terminal: Python src/run_study.py
(execute da raiz pra evitar erros de path)
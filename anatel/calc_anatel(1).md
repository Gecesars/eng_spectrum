# calc_anatel.md – Lógica de Cálculo e Integração GIS/Mapa (FM, TV Analógica e TV Digital)

Você é um agente de IA atuando em um sistema de **engenharia de radiodifusão** (Flask + PostgreSQL + Folium/Leaflet).  
Este documento é a **fonte de verdade dos cálculos** de viabilidade, interferência, contorno protegido e manipulação de dados geográficos, alinhado às normas da Anatel (Res. 721 e correlatas) e às recomendações UIT-R (P.1546, P.526, etc.).

## Princípios gerais

1. **Evolução sempre aditiva**  
   - Nunca remover rotas, modelos, templates, funções ou campos existentes na aplicação.
   - Toda nova funcionalidade deve ser **acrescentada**, reaproveitando o que já existe.
   - Se precisar alterar comportamento, fazê-lo de forma compatível, preservando APIs já utilizadas.

2. **Gestão de dados já implementada**  
   - O sistema **já possui lógica própria** para baixar, armazenar e manter os arquivos de elevação `.hgt`.
   - Assim que o ponto TX é definido (clique no mapa ou coordenadas informadas), a aplicação já dispara o download automático dos arquivos `.hgt` necessários para o raio de análise.
   - O agente **não deve implementar nem sugerir nova lógica de download**, nem indicar fontes externas; deve apenas **consumir** os dados disponíveis em disco.

---

## 0. Premissas de diretórios e arquivos

O agente deve assumir a seguinte organização de dados no servidor:

- `/anatel/`  
  - Planos básicos, XML, shapefiles da Anatel e demais bases vetoriais.
  - Exemplos: `PBFM.*`, `PBTVD.*`, `PBTV.*`, shapefiles de estações, limites municipais, setores, etc.
- `/anatel/DEM/`  
  - Arquivos de elevação **já obtidos automaticamente** pelo sistema (formato `.hgt` e/ou outros DEMs).  

Regras:

- Sempre que precisar de dados de **plano básico**, limites ou vetores (Anatel/IBGE), procurar em `/anatel/`.
- Sempre que precisar de **altitude/relevo**, usar exclusivamente os arquivos já existentes em `/anatel/DEM/`.
- Se um arquivo esperado não estiver disponível naquele momento:
  - Registrar log e retornar erro controlado ou estado “dados de relevo ainda não disponíveis”.
  - **Não** tentar baixar nada, nem alterar o mecanismo de download existente.

---

## 1. Escopo geral

O módulo atende, inicialmente, aos serviços de radiodifusão:

- **FM / RTR / Radiovias / RadCom**
- **TV analógica**
- **TV digital (ISDB-T / SBTVD)**

Os cálculos e rotinas cobrem:

1. **ERP e parâmetros de transmissão**
2. **Terreno: HNMT/HAAT, perfis e nível médio**
3. **Contorno protegido teórico e real (mancha de cobertura)**
4. **Interferência / relações de proteção / compatibilidade**
5. **Cobertura em setores censitários (área e população)**
6. **GIS: shapefiles, camadas e interface de mapa**
7. **Integração com a base de projetos existente** (importar dados de um projeto já salvo)

---

## 2. Fonte de dados: projeto existente x entrada manual

O sistema deve permitir **duas formas de criar um estudo de viabilidade**:

1. **Importar de um projeto existente (preferencial)**  
   - A base de dados já contém entidades de projeto (`Projeto` ou equivalente) com todas as informações necessárias:
     - serviço/tipo de canal;
     - frequência/canal;
     - ERP, potência, tipo de antena;
     - coordenadas da estação;
     - altura da antena;
     - diagrama horizontal;
     - classe, município, etc.
   - O agente deve criar uma rotina para gerar um `ViabilityStudy` **a partir de um projeto** sem exigir nova digitação.

2. **Entrada manual**  
   - Usuário preenche um formulário completo, inserindo diretamente todos os parâmetros.

### 2.1. Importar um projeto existente

Criar um fluxo (endpoint e/ou ação no painel) do tipo:

- Rota exemplo (não obrigatória, apenas sugestão):  
  `POST /viabilidade/importar_projeto/<int:projeto_id>`

Processo interno:

1. Localizar o projeto na base atual.
2. Mapear os campos do projeto para o novo `ViabilityStudy` (ajustar nomes para o modelo real):

   - `projeto.servico` → `service_type`
   - `projeto.canal` → `canal`
   - `projeto.frequencia_MHz` → `frequencia_MHz`
   - `projeto.classe` → `classificacao`
   - `projeto.pt_kw` → `pt_kw`
   - `projeto.ganho_antena_dBd` → `ganho_max_dBd`
   - `projeto.perdas_linha_dB` → `perdas_linha_dB`
   - `projeto.perdas_diversos_dB` → `perdas_diversos_dB`
   - `projeto.diagrama_horizontal` → `diagrama_horizontal`
   - `projeto.lat`, `projeto.lon` → `coord_tx`
   - `projeto.altura_centro_antena_m` → `altura_centro_antena_m`
   - `projeto.municipio_ibge` → `municipio_outorga`

3. Criar o `ViabilityStudy` associado ao usuário atual e marcar sua origem como `"importado_projeto"`.
4. Disparar o pipeline completo de cálculo (`run_full_viability(study_id)`).
5. Não remover nem alterar o projeto original – apenas referenciá-lo.

Na UI de viabilidade, deve existir:

- Botão/ação “Criar estudo a partir de projeto” (lista de projetos existentes);
- Botão/ação “Criar estudo manualmente”.

---

## 3. Entidade principal: ViabilityStudy

Cada estudo de viabilidade (`ViabilityStudy`) deve conter no mínimo:

- `user_id` – referência ao usuário
- `projeto_id` – opcional, referência ao projeto de origem (se importado)
- `service_type`: "FM" | "RTR" | "TV_ANALOG" | "TV_DIGITAL" | "RADCOM" | "RADIOVIAS"
- `canal`: número do canal
- `frequencia_MHz`
- `classificacao`: classe A/B/C/Especial (TV) ou classes E1…C, etc.
- `pt_kw`: potência no transmissor (kW)
- `ganho_max_dBd` ou `ganho_max_dBi`
- `perdas_linha_dB`
- `perdas_diversos_dB`
- `line_length_m` (se aplicável)
- `diagrama_horizontal` (estrutura serializada)
- `coord_tx` (lat, lon)
- `altura_centro_antena_m` (`H_centro`)
- `municipio_outorga` (código IBGE)
- `sistema_rede` (dados de SFN, se houver)
- `hnmt_override_m` (opcional)

Além dos campos de entrada, o estudo receberá campos de **resultados** (ERP, HNMT, contornos, cobertura, interferência, etc.) preenchidos pelo pipeline.

---

## 4. Cálculo de ERP

### 4.1. Perdas totais (PS)

1. Perda de linha (dB):

```text
perda_linha_dB = (line_length_m / 100) * atenuacao_dB_100m
```

2. Perdas adicionais:

```text
perdas_total_dB = perda_linha_dB + perdas_diversos_dB
```

3. Fator linear de perda:

```text
PS = 10 ** (-perdas_total_dB / 10.0)
```

### 4.2. Ganho máximo (GTMAX)

Se o ganho estiver em dBd:

```text
ganho_dBi = ganho_max_dBd + 2.15
```

Converter para linear:

```text
GTMAX = 10 ** (ganho_dBi / 10.0)
```

### 4.3. ERP máxima e por radial

```text
ERP_linear_kW = pt_kw * GTMAX * PS
ERP_dBk       = 10 * log10(ERP_linear_kW)
```

ERP por radial (usando diagrama horizontal):

```text
ERP_radial_dBk(az) = ERP_dBk + ganho_relativo_dB(az)
ERP_radial_kW(az)  = 10 ** (ERP_radial_dBk(az) / 10.0)
```

Esses dados são gravados em tabela auxiliar `RadialData`.

---

## 5. HNMT – Altura sobre o Nível Médio do Terreno

### 5.1. Entradas

- Coordenadas da base (`lat_tx`, `lon_tx`)
- `H_centro` – altura do centro da antena acima da base (m).

### 5.2. Altitude da base (H_base) usando DEM em /anatel/DEM

O sistema principal **já garante** que, ao posicionar o TX, todos os arquivos `.hgt` necessários para o raio de análise são baixados e armazenados em `/anatel/DEM/`.  
O agente deve apenas:

1. Localizar internamente os arquivos `.hgt` correspondentes à região de `lat_tx`, `lon_tx` dentro de `/anatel/DEM/`.
2. Realizar **interpolação bilinear** para calcular a altitude do solo `H_base` na coordenada exata.
3. Calcular a altitude do centro da antena:

```text
Altitude_Total = H_base + H_centro
```

Se, por qualquer motivo, o DEM ainda não estiver disponível (ex.: processo de download externo em andamento), o código deve:

- Registrar log explicando “DEM ainda não disponível para esta região”;
- Retornar um estado de erro controlado para o front-end, sem criar nova lógica de download.

### 5.3. Amostragem do terreno e nível médio

1. Traçar 72 radiais (0°…355°, passo 5°) a partir do TX.
2. Em cada radial, amostrar altitudes a partir dos `.hgt` em `/anatel/DEM/`, em passos regulares (100 m ou 1 km) de 3 km a 15 km.
3. Calcular:

```text
H_radial_avg = media(altitudes_3_15km)
HNMT_radial  = Altitude_Total - H_radial_avg
```

4. Calcular terreno médio e HNMT global:

```text
H_terreno_medio = media(H_radial_avg de todas as radiais)
HNMT            = Altitude_Total - H_terreno_medio
```

5. Se `hnmt_override_m` estiver definido, usá-lo para fins de classificação oficial, mas manter o HNMT calculado em campos auxiliares.

---

## 6. Contorno protegido – teórico e real

### 6.1. Contorno teórico (classe)

A partir de tabelas da Anatel (classe × serviço × frequência × HNMT), obter `D_classe` (distância máxima).

Para cada azimute:

```text
D_teorica_km(az) = D_classe
```

Converter para coordenadas geográficas e construir um polígono circular (GeoJSON) – **Contorno Teórico**.

### 6.2. Contorno real (mancha de cobertura)

#### 6.2.1. Limites de campo

Configurar via `constants.py`:

- FM / RTR / Radiovias / RadCom: 66 dBµV/m.
- TV analógica: 58 / 64 / 70 dBµV/m.
- TV digital: 43 dBµV/m (VHF alto) e 51 dBµV/m (UHF).

#### 6.2.2. Metodologia radial

Para cada radial (ideal 1°, mínimo 5°):

1. Obter perfil de terreno a partir de `/anatel/DEM/` até horizonte rádio ou 100 km.
2. Utilizar modelo de propagação (P.1546, Longley-Rice, P.526+Assis, conforme disponível) para calcular E(d) ao longo do radial, usando:
   - frequencia_MHz;
   - ERP_radial_kW;
   - HNMT_radial;
   - tipo de serviço (analógico/digital).

3. Encontrar a distância `D_real_km(az)` onde E(d) cai abaixo do limite de campo.
4. Converter `(az, D_real_km)` para coordenadas e montar polígono GeoJSON – **Contorno Real / Mancha**.

Ambos contornos (teórico e real) devem ser armazenados (GeoJSON) e expostos ao frontend.

---

## 7. Cobertura em setores censitários (IBGE)

Utilizar shapefiles de setores censitários (IBGE) armazenados em `/anatel/` (já importados e reprojetados para WGS84).

1. Para o município de outorga, selecionar setores urbanos.
2. Intersectar o contorno real (mancha) com os setores.
3. Calcular:

```text
area_coberta = soma(area_intersecção_setor)
area_total   = soma(area_setor_urbano)
cobertura_area = area_coberta / area_total

pop_coberta = soma(pop_setor * (area_intersecção_setor / area_setor))
pop_total   = soma(pop_setor)
cobertura_pop = pop_coberta / pop_total
```

Critérios:

- TV/RTV: atende se `cobertura_area >= 0.70` ou `cobertura_pop >= 0.70`.
- FM/RTR/Radiovias/RadCom: atende se `cobertura_area >= 0.50` ou `cobertura_pop >= 0.50`.

Armazenar em `ViabilityStudy`:

- `coverage_area_percent`
- `coverage_pop_percent`
- `status_cobertura` ("ATENDE"/"NAO_ATENDE").

---

## 8. Campo ponto-a-ponto e interferência (D/U)

### 8.1. Função P.526 / Assis (abstraída)

Interface genérica:

```python
def calc_campo_p526(tx, rx, perfil_terreno, freq_MHz, ERP_kW, polarizacao):
    """
    Retorna a intensidade de campo em dBµV/m no ponto rx,
    usando modelo ponto-a-ponto compatível com ITU-R P.526 + Método Assis.
    """
```

O agente não precisa reimplementar o modelo físico detalhado, apenas criar a interface e plugar na implementação existente ou em um stub bem documentado.

### 8.2. Relações de proteção (D/U)

Para cada par estação desejada × estação interferente, e para pontos relevantes (principalmente sobre o contorno real da estação protegida):

```text
D_U_dB = Campo_desejado_dBu - Campo_interferente_dBu
```

Comparar com os valores mínimos de proteção (tabelas específicas para TV–TV, FM–FM, TV–FM, co-canal, adjacentes, FI, etc.).

Armazenar, por par:

- `DU_min_dB`
- `tipo_interferencia`
- `status` ("OK"/"VIOLACAO").

Nenhuma lógica existente de interferência deve ser removida; apenas estendida para atender novos cenários quando necessário.

---

## 9. Perfil de terreno e gráfico

Para qualquer par (tx, rx) selecionado pelo usuário:

1. Amostrar N pontos entre tx e rx (ex.: N=200) usando DEM em `/anatel/DEM/`.
2. Gerar vetores `dist_km[i]` e `alt_m[i]`.
3. Calcular nível médio do terreno no trajeto e marcá-lo no gráfico.
4. Gerar figura (Matplotlib) e salvar em `/static/anatel/profiles/...`.
5. Registrar o caminho no estudo, sem apagar gráficos anteriores (versões podem coexistir).

---

## 10. Shapefiles e camadas GIS (em /anatel)

O agente deve usar as bibliotecas existentes (ex.: GeoPandas/Fiona/Shapely) para:

1. Ler shapefiles que já se encontram em `/anatel/` (não criar lógica nova de upload, a menos que solicitado).
2. Reprojetar para WGS84 (se ainda não estiver).
3. Converter para GeoJSON para envio ao frontend.

Se a aplicação já possui rotinas de importação/conversão, o agente deve **reutilizá-las** e apenas adicionar novas camadas/estilos quando necessário.

---

## 11. Interface do mapa e controle de camadas

No frontend (Folium/Leaflet ou similar), manter o mapa existente e **acrescentar**:

- Camada “Contorno Teórico” (círculo por classe);
- Camada “Contorno Real / Mancha” (polígono real);
- Camada “Regiões de Interferência” (polígonos vermelhos);
- Camada “Setores Censitários (IBGE)”;
- Opção de trocar o TileLayer de base para mapa de relevo (terrain/topográfico).

Usar um painel de controle de camadas (sidebar ou `L.control.layers`) com checkboxes, sem remover controles já existentes.

Legenda sugerida:

- Azul tracejado – Contorno teórico;
- Verde preenchido – Mancha real;
- Vermelho – Áreas de interferência;
- Outros – conforme estilos da aplicação.

---

## 12. Organização dos módulos e pipeline

Estrutura sugerida em `app/anatel/`:

```text
app/
  anatel/
    __init__.py
    models.py          # ViabilityStudy, RadialData, ContourPolygon, InterferenceResult, etc.
    constants.py       # tabelas de classes, intensidades, D/U, etc.
    erp.py             # ERP, perdas, conversões
    terrain.py         # DEM /anatel/DEM, HNMT, perfis
    contour.py         # contornos teórico e real
    coverage.py        # cobertura em setores
    interference.py    # cálculos D/U e compatibilidades
    shapefiles.py      # manipulação de vetores em /anatel/
    mapping.py         # GeoJSON para o front
    pipeline.py        # orquestração run_full_viability
```

Função principal:

```python
def run_full_viability(study_id: int) -> None:
    """
    1. Carrega o ViabilityStudy.
    2. Calcula ERP máxima e por radial.
    3. Calcula HNMT por radial e global.
    4. Gera contorno teórico.
    5. Gera contorno real (mancha).
    6. Calcula cobertura em setores (IBGE).
    7. Avalia interferência (D/U) com estações do plano básico.
    8. Gera perfis de terreno e gráficos.
    9. Atualiza campos de resultado no estudo.
    """
```

Esta função pode ser chamada de forma assíncrona (Celery/RQ) conforme já implementado na aplicação.

---

## 13. Resultado consolidado por estudo

Após o pipeline, cada `ViabilityStudy` deve conter:

- `erp_max_kw`, `erp_max_dBk`
- Tabela de radiais: az, `ERP_radial_dBk`, `ERP_radial_kW`, `H_radial_avg`, `HNMT_radial`, `D_teorica_km`, `D_real_km`
- Polígono de contorno teórico (GeoJSON)
- Polígono de contorno real/mancha (GeoJSON)
- `coverage_area_percent`, `coverage_pop_percent`, `status_cobertura`
- Lista de `InterferenceResult` com `DU_min_dB`, tipo, status
- Caminhos de gráficos de perfil de terreno
- `H_base`, `Altitude_Total`, `HNMT`
- Referência ao `projeto_id` (se importado)
- Flags de classe efetiva e indicação de caso excepcional (quando extrapola parâmetros de classe).

Nada disso substitui funcionalidades existentes: tudo deve ser **adicionado** à aplicação, preservando o comportamento anterior.

---

_Fim do calc_anatel.md._

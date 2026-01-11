# Engenharia de Espectro — Plot de Cobertura (AOI) e Perfil TX↔RX (com curvatura da Terra)

Este documento especifica **como o sistema deve calcular e renderizar**:

1) **Cobertura** sobre uma **Área de Interesse (AOI)** (mapa/heatmap + contornos);  
2) **Perfil entre dois pontos** (TX↔RX), no estilo clássico de ferramentas RF, incluindo a **faixa escura** na base representando a **curvatura efetiva da Terra**.

> Convenções:
> - Coordenadas no backend: **SIRGAS 2000 (EPSG:4674)**.
> - No frontend: pode usar 4326 para interação; o backend normaliza para 4674.
> - Distâncias internas: **metros** (m). Altitudes: **metros** (m). Potência/perdas: dB / dBm / dBµV/m.

---

## 1) Cobertura sobre uma Área de Interesse (AOI)

### 1.1 Entradas mínimas (UI)
**Definição da AOI**
- O usuário define a AOI por:
  - (a) polígono desenhado no mapa,
  - (b) círculo (centro + raio em km),
  - (c) bbox (retângulo),
  - (d) upload (KML/SHP/GeoJSON).
- A AOI deve ser persistida como `MultiPolygon` no DB (SRID 4674).

**Parâmetros do transmissor (TX)**
- Coordenadas do TX (SIRGAS 2000).
- Altura da torre / altitude do terreno / altura do centro de radiação:
  - `alt_tx_ground_m` (terreno),
  - `htx_m` (altura da antena acima do solo),
  - `h_ant_tx_m = alt_tx_ground_m + htx_m`.
- Frequência (MHz).
- Potência / ERP / EIRP (conforme modo):
  - modo A: entrada direta `ERP`/`EIRP`,
  - modo B: `P_tx_dBm` + `loss_cable_dB` + `gain_ant_dBd/dBi`.
- Antena:
  - padrão horizontal e vertical (JSONB, 0–360° e elevação),
  - tilt elétrico/mecânico.
- Polarização (quando aplicável ao modelo).

**Modelo de propagação**
- Opções (exemplos):
  - ITU-R P.1546 (estatístico),
  - Longley-Rice / ITM (semi-determinístico),
  - Deygout (difração multi-obstáculo),
  - Deygout-Assis (quando habilitado).
- Parâmetros comuns:
  - `k_factor` (padrão 4/3),
  - resolução DEM,
  - clutter/uso do solo (se disponível),
  - unidade de saída (dBµV/m / dBm).

**Saída desejada**
- Raster contínuo (heatmap) com legenda;
- Contornos (isolinhas/isopolígonos) em níveis selecionados (ex.: 66 dBµV/m);
- Sobreposição de contornos existentes (mosaico/anatel).

---

### 1.2 Grade de cálculo (raster)
A cobertura deve ser calculada em uma **grade regular** (centro do pixel como ponto de amostragem).

**Resolução recomendada (padrões)**
- AOI pequena (≤ 20 km): 50–100 m/pixel
- AOI média (20–60 km): 100–250 m/pixel
- AOI grande: 250–500 m/pixel
- O sistema deve permitir "refino sob demanda" ao dar zoom.

**Máscara**
- Calcular apenas pontos cujo centro cai dentro da AOI.
- Retornar `nodata` fora da AOI.

**Processamento por blocos**
- Internamente, processe em tiles (ex.: 256×256) para:
  - paralelização,
  - cache,
  - renderização incremental.

**Cache**
- Chave de cache: `(station_id, model_id, params_hash, aoi_hash, resolution_m)`.
- Resultados em disco/objeto (PNG/WEBP tiles) + metadados no DB.

---

### 1.3 Renderização no mapa
**Camadas base**
- Basemap (ruas/terrain).
- Opcional: relevo sombreado / DEM.

**Overlay de cobertura (raster)**
- Renderizar como:
  - (preferível) tiles (XYZ) de PNG/WEBP,
  - ou overlay único para áreas muito pequenas.
- Paleta:
  - modo “técnico”: quantizado (degraus nítidos),
  - modo “visual”: suave (gradiente).
- Legenda obrigatória:
  - unidade,
  - escala com ticks,
  - nome do modelo,
  - parâmetros relevantes (freq, k-factor etc).

**Anéis de distância**
- Círculos concêntricos (10/20/30/40 km… configurável).
- Rótulo do raio sobre cada anel.

**Contornos**
- Para nível escolhido (ex.: 66 dBµV/m):
  - gerar isolinhas/isopolígonos do raster (marching squares),
  - suavizar (Douglas-Peucker leve),
  - persistir no DB: `contours.geom (MultiPolygon, 4674)` + metadados:
    - `field_strength`,
    - `model_id`,
    - `params_hash`,
    - `network_id`.

---

## 2) Perfil TX↔RX com curvatura da Terra (faixa escura na base)

### 2.1 Objetivo visual
O gráfico do perfil deve exibir:
- Terreno preenchido (marrom claro);
- Faixa escura na base: **curvatura efetiva da Terra**;
- Linha de enlace (LOS) em vermelho;
- Zonas de Fresnel (F1) como “cúpulas/arcos” em cinza;
- Marcador de obstrução e "Worst Fresnel".

---

### 2.2 Amostragem do perfil
Dados:
- TX (lat1, lon1), RX (lat2, lon2)
- Distância total `D` (m)
- Frequência `f` (MHz), `λ = c / (f * 1e6)`
- `k_factor` (padrão 4/3)

**Amostragem**
- Gerar `N` amostras ao longo do geodésico:
  - passo típico 30–100 m
  - `x[i] = i * D / (N - 1)`
- Amostrar altitude do terreno via DEM:
  - bilinear nos tiles `.hgt`
  - mar/sem dado: 0 m (ou nível do mar, conforme política)

Resultado: `h_ground[i]` (m).

---

### 2.3 Curvatura efetiva (bulge)
Use raio efetivo:

- `R_earth = 6_371_000 m`
- `R_eff = k_factor * R_earth`

Bulge:

b(x) = x(D - x) / (2 * R_eff)

Onde `x` e `D` estão em metros.

**Construção das curvas do gráfico**
- Defina uma base `y_base` (apenas para visualização, ex.: `min(h_ground) - padding`).
- Curva da Terra (faixa escura):
  - `y_earth[i] = y_base + b(x[i])`
- Terreno sobre a curvatura:
  - `y_terrain[i] = y_earth[i] + h_ground[i]`

**Como desenhar a faixa escura**
- Preencher (fill) de `y_base` até `y_earth[i]` com marrom escuro.
- Depois preencher de `y_earth[i]` até `y_terrain[i]` com marrom claro.

Isso replica a aparência onde a base escura representa a curvatura da Terra.

---

### 2.4 Linha do enlace (LOS)
Alturas aparentes dos pontos de rádio:

- `Htx = h_ground[0] + h_ant_tx_m` (altura antena acima do solo)
- `Hrx = h_ground[N-1] + h_ant_rx_m`

No gráfico com curvatura:
- `Ytx = y_earth[0] + Htx`
- `Yrx = y_earth[N-1] + Hrx`

LOS:

y_los(x) = Ytx + (Yrx - Ytx) * (x / D)

Plotar em vermelho.

---

### 2.5 1ª Zona de Fresnel (F1)
Raio da 1ª zona:

r1(x) = sqrt( λ * d1 * d2 / (d1 + d2) )

- `d1 = x`
- `d2 = D - x`

Curvas:
- `y_f1_top[i] = y_los[i] + r1[i]`
- `y_f1_bot[i] = y_los[i] - r1[i]`

Plotar em cinza.

---

### 2.6 Obstrução e Worst Fresnel
Folga para F1:

clearance[i] = y_los[i] - r1[i] - y_terrain[i]

- Se `min(clearance) < 0`: há obstrução.
- Índice crítico: `i* = argmin(clearance)`
- Distância da obstrução: `x[i*]` (m)

Worst Fresnel (fração de F1 invadida):

worst_f1 = min(clearance) / r1[i*]

Ex.: `-0.6` significa invadiu 60% do raio de F1.

**No gráfico**
- Linha vertical no `x[i*]`
- Marker no ponto crítico
- Texto “Obstruction at XX km” e “Worst Fresnel = -0.6 F1”

---

### 2.7 Header de métricas (barra superior)
Exibir no topo:
- Azimute TX→RX (°)
- Distância total (km)
- Ângulo de elevação (°)
- Obstruction at (km), se existir
- Worst Fresnel (fração de F1)
- Resultados de modelo (path loss, field strength, rx level) quando retornados pelo backend

---

## 3) Integração UX (mapa → perfil)
**Fluxo**
1) Usuário ativa “Link/Perfil”
2) Seleciona TX (estação existente) ou clica no mapa
3) Seleciona RX (clica no mapa)
4) Abre painel/modal com:
   - gráfico do perfil (com curvatura + Fresnel + LOS)
   - parâmetros editáveis (freq, k-factor, alturas, perdas, ganhos)
   - botão Aplicar/Recalcular

**Requisitos**
- Atualização com debounce em arrasto
- Recalcular no backend (Celery) se for pesado; caso leve, pode rodar síncrono

---

## 4) API sugerida (frontend → backend)
`POST /api/links/profile`

Payload:
```json
{
  "tx": {"lat": -22.9, "lon": -43.2, "h_ant_agl_m": 40},
  "rx": {"lat": -22.95, "lon": -43.35, "h_ant_agl_m": 10},
  "freq_mhz": 600,
  "k_factor": 1.3333333,
  "step_m": 50
}
```

Resposta:
```json
{
  "distance_m": 38610.5,
  "azimuth_deg": 310.0,
  "elev_angle_deg": -0.177,
  "samples": [{"d_m": 0, "ground_m": 12.0}, {"d_m": 50, "ground_m": 12.2}],
  "derived": {
    "obstruction": {"exists": true, "at_m": 9560.0, "worst_f1": -0.6}
  }
}
```

---

## 5) Observações de implementação
- A curvatura deve sempre ser calculada com `R_eff = k * R_earth`.
- O preenchimento escuro da base **não é “um chão genérico”**: ele é o `bulge`.
- O terreno deve ser desenhado **acima** da curva da Terra.
- Fresnel deve ser calculado em metros (não “aproximado em pixels”).


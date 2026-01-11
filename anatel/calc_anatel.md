# Lógica de Cálculo – Anatel (FM, TV Analógica e TV Digital)

Este documento descreve, em alto nível, **toda a lógica de cálculo** que o agente de IA deve implementar para suportar as rotinas de _viabilidade_, _interferência_, _contorno protegido_ e _perfil de terreno_ na aplicação Flask (backend Python).

> Atenção: este arquivo descreve **processos e fórmulas**. A implementação concreta (bibliotecas, classes, migrations, etc.) deve ser feita pelo código gerado a partir deste blueprint.

---

## 1. Escopo geral

A lógica deve atender, inicialmente, aos serviços:

- **FM / RTR / Radiovias / RadCom**
- **TV analógica**
- **TV digital (ISDB-T / SBTVD)**

e cobrir quatro grandes blocos de cálculo:

1. **ERP e parâmetros de transmissão**
2. **Contorno protegido e área de prestação do serviço**
3. **Interferência / relações de proteção / compatibilidade**
4. **Perfil de terreno, nível médio e mapas de cobertura**

Todos os cálculos devem ser parametrizados para funcionar a partir dos planos básicos (PBFM, PBTVD, PBTV, PBRTV, PRRadCom, PRRadiovias) e das bases cartográficas (IBGE, setores censitários, shapefiles da Anatel e DEM para relevo).

---

## 2. Entradas básicas por projeto/análise

Para cada **Análise de Viabilidade** criada pelo usuário, o backend deve armazenar uma entidade principal (ex.: `ViabilityStudy`) ligada ao `User`, contendo:

- `service_type`: `"FM" | "RTR" | "TV_ANALOG" | "TV_DIGITAL" | "RADCOM" | "RADIOVIAS"`
- `canal`: número do canal (FM em kHz central ou canal de TV)
- `frequencia_MHz`
- `classificacao`: classe A/B/C/Especial (TV) ou classes E1…C para FM/Radiovias/RadCom
- `pt_kw`: potência de operação do transmissor (kW)
- `ganho_max_dBd` ou `ganho_max_dBi`
- `perdas_linha_dB`: perdas da linha (em dB)
- `perdas_diversos_dB`: conectores, divisores, etc.
- `diagrama_horizontal`: lista de (azimute, ganho_relativo_dB) de 0° a 355° em passos de 5°
- `coord_tx`: (latitude, longitude) da estação candidata
- `altura_antena_solo_m`: altura física da antena em relação à base da torre
- `h_nmt_override_m`: opcional, se o nível médio de terreno for informado manualmente
- `municipio_outorga`: código IBGE
- parâmetros opcionais de rede SFN (TV digital): ID de rede, atraso, etc.

Cada estudo poderá ter **várias versões de proposta**, mas a lógica de cálculo é a mesma; o agente só precisa garantir que os cálculos sejam reexecutados quando qualquer parâmetro relevante mudar.

---

## 3. Cálculo de ERP

### 3.1. Perdas totais do sistema (PS)

1. Calcular a perda da linha em dB:

   ```text
   perda_linha_dB = (L_m / 100) * atenuacao_dB_100m
   ```

   - `L_m`: comprimento da linha de transmissão (m)
   - `atenuacao_dB_100m`: atenuação do cabo em dB/100 m (a partir de tabela interna por tipo de cabo)

2. Somar outras perdas:

   ```text
   perdas_total_dB = perda_linha_dB + perdas_diversos_dB
   ```

3. Converter para fator linear (PS):

   ```text
   PS = 10 ** (-perdas_total_dB / 10.0)
   ```

### 3.2. Ganho máximo do sistema radiante (GTMAX)

1. Se o ganho estiver em dBd, converter para dBi:

   ```text
   ganho_dBi = ganho_dBd + 2.15
   ```

2. Converter para linear:

   ```text
   GTMAX = 10 ** (ganho_dBi / 10.0)
   ```

### 3.3. ERP máxima (linear e em dBk/dBkW)

A fórmula base de ERP é:

```text
ERP_linear_kW = PT_kW * GTMAX * PS
```

O backend também deve armazenar ERP em dBk (ou dBkW):

```text
ERP_dBk = 10 * log10(ERP_linear_kW)
```

Além da **ERP máxima**, é necessário obter a **ERP por radial**, aplicando o diagrama horizontal:

```text
ERP_radial_dBk(az) = ERP_dBk + ganho_relativo_dB(az)
ERP_radial_kW(az)  = 10 ** (ERP_radial_dBk(az) / 10.0)
```

Se não houver diagrama por radial, utilizar a ERP máxima em todas as direções.

---

## 4. Nível médio do terreno (HNMT / HAAT) e alturas de referência

### 4.1. Amostragem de terreno por radial

Para cada radial (0°, 5°, 10° … 355°):

1. Gerar pontos ao longo do radial entre **3 km e 15 km** a partir do transmissor (intervalo típico da recomendação ITU, ajustável via constante).
2. Para cada ponto, consultar a **altitude** utilizando os dados de relevo (DEM) obtidos via serviço `viewpano` / SRTM / equivalente.
3. Calcular a **média aritmética das altitudes** no radial:

   ```text
   h_medio_radial = media(altitudes_3_15km)
   ```

4. Calcular a **altura da antena acima do nível médio do terreno (HNMT/HAAT)**:

   ```text
   HNMT_radial = (altitude_base_torre + altura_antena_solo_m) - h_medio_radial
   ```

5. Para fins de classificação de canal, usar a **média dos HNMT_radial** ou o valor por radial, conforme especificação do estudo.

### 4.2. Armazenamento

- Persistir para cada estudo um array de 72 amostras (0–355°, passo 5°) contendo:
  - `azimute`
  - `HNMT_radial_m`
  - `altitude_media_m`
  - lista compactada do perfil (distância x altitude) para uso posterior em gráficos

---

## 5. Contorno protegido

### 5.1. Intensidades de campo alvo

O contorno protegido é definido por um **valor alvo de intensidade de campo** (em dBµV/m), dependendo do serviço/canal/classe.

Exemplos típicos (parametrizar via tabela de constantes):

- **FM / RTR / Radiovias**: contorno de **66 dBµV/m** (requisito de cobertura).
- **TV analógica** (canais 2–6 / 7–13 / 14–51): contornos de **58 / 64 / 70 dBµV/m**.
- **TV digital (ISDB-T)**: canais 7–13: **43 dBµV/m**, canais 14–51: **51 dBµV/m**.

A classe do canal define **ERP máxima**, **HNMT de referência** e **distância máxima** ao contorno protegido. O código deve validar se a proposta excede os limites e, se exceder, marcar como "caso excepcional".

### 5.2. Cálculo de distância radial via ITU-R P.1546

Para cada radial:

1. Considerar frequência, `ERP_radial_kW(az)`, `HNMT_radial_m` e tipo de tecnologia:
   - Analógica → curvas E(50,50)
   - Digital → curvas E(50,90), calculadas como `E_50_90 = 2 * E_50_50 - E_50_10`.
2. Implementar um solver numérico que, dado `E_alvo_dBu`, encontre a distância `d_km` nas curvas da P.1546.
3. Armazenar `contorno_dist_km(az) = d_km`.

### 5.3. Construção do polígono de contorno

1. Converter cada `(azimute, contorno_dist_km)` em coordenadas geográficas.
2. Construir polígono (ex.: `shapely`).
3. Persistir vértices, área e perímetro.
4. Expor polígono para mapa, cobertura e interferência.

---

## 6. Área de prestação de serviço e cobertura (setores censitários)

### 6.1. Dados necessários

- Shapefile de setores censitários urbanos (IBGE).
- Atributos: código do setor, área, população, geometria.

### 6.2. TV

Requisito: cobrir >= 70% da área dos setores urbanos do município dentro do contorno protegido, ou >= 70% da população urbana dentro do contorno.

Passos:
1. Intersectar contorno com setores do município.
2. Somar áreas de intersecção e totais.
3. Calcular `cobertura_area = area_coberta / area_total`.
4. Calcular população coberta por ponderação de área.
5. Definir `status_cobertura` como "ATENDE" ou "NAO_ATENDE".

### 6.3. FM / RTR / Radiovias / RadCom

Mesma lógica, com alvo de 66 dBµV/m e limite mínimo de 50% (área ou população).

---

## 7. Cálculos de campo ponto-a-ponto (ITU-R P.526 + Assis 1971)

Implementar função genérica (ou serviço) `calc_campo_p526(tx, rx, perfil_terreno, freq_MHz, ERP_kW, polarizacao)` que retorne intensidade de campo em dBµV/m considerando propagação ponto-a-ponto.

A função deve considerar difração, curvatura da Terra e, quando possível, perdas de clutter. Inicialmente pode ser um modelo simplificado com arquitetura preparada para substituição por implementação completa.

---

## 8. Critérios de proteção e interferência

A lógica de interferência usa a relação `D_U_dB = Campo_desejado_dBu - Campo_interferente_dBu`.

### 8.1. TV/RTV

- Usar tabelas de relações de proteção entre canais analógicos/digitais.
- Verificar D/U em pontos do contorno protegido e, quando necessário, em grade interna.
- Se D/U < valor mínimo em qualquer ponto crítico, marcar violação.

### 8.2. FM / RTR / Radiovias / RadCom

- Usar tabela de relações de proteção para co-canal (0 kHz) e adjacentes (±200 kHz etc.).
- Mesma lógica de D/U, usando ERP por radial e campo calculado via P.526.

### 8.3. Compatibilidade TV × FM (canais 5 e 6)

- Tratar casos de cocanal, adjacências e batimento de FI usando tabelas específicas.
- Comparar campos nos contornos protegidos corretos (TV ou FM) e verificar D/U mínimo.

---

## 9. Perfil de terreno e gráfico de nível médio

1. Amostrar N pontos entre tx e rx, obter altitudes.
2. Construir vetores de distância e altitude.
3. Calcular nível médio do terreno no trajeto.
4. Gerar gráfico (Matplotlib) e salvar PNG associado ao estudo.

---

## 10. Integração com o mapa (Folium + JS)

- Camadas: base, limites administrativos (IBGE), plano básico (estações e contornos), proposta atual.
- Painel lateral "Viabilidade":
  1. Listar emissoras dentro de raio R.
  2. Exibir/ocultar contornos das emissoras.
  3. Rodar estudo de interferência entre proposta e emissoras selecionadas.
  4. Exibir perfis de terreno selecionados.
  5. Exportar resultados (JSON, PDF futuro).

---

## 11. Organização do código de cálculo

Sugestão de módulos Python:

```text
app/
  anatel/
    __init__.py
    models.py
    erp.py
    terrain.py
    contour.py
    coverage.py
    interference.py
    mapping.py
    constants.py
```

O agente deve criar funções puras, testáveis, e uma função de alto nível `run_full_viability(study_id)` que:
1. Calcula ERP por radial.
2. Calcula HNMT por radial.
3. Gera contorno protegido.
4. Calcula cobertura em setores censitários.
5. Verifica interferência com estações do plano básico.
6. Salva todos os resultados associados ao estudo.

---

## 12. Resultados esperados por estudo

Cada `ViabilityStudy` deve guardar:

- `erp_max_kw`, `erp_max_dBk`
- tabela de radiais (`az`, `ERP_radial_dBk`, `HNMT_radial_m`, `contorno_dist_km`)
- polígono de contorno protegido (GeoJSON)
- `coverage_area_percent`, `coverage_pop_percent`, `status_cobertura`
- lista de resultados de interferência com D/U mínimo e status
- caminhos de imagens de perfil de terreno
- flags de classificação de canal e indicação de caso excepcional, se aplicável.

Esses artefatos serão a base para relatórios técnicos, mapas interativos e processos de viabilidade perante a Anatel.

---

Fim do calc_anatel.md.

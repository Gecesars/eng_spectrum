# Engenharia de Espectro — codex.md (Plano Mestre de Implementação)

Este documento é o **guia único** para construir o aplicativo **Engenharia de Espectro** (Landing → Auth → Dashboard → Projetos → Simulações → Mapas → Exportação → Relatórios), cobrindo:

- Contornos protegidos com **radiais + método híbrido (ITU‑R P.1546 + Deygout‑Assis)**  
- Análise de interferência por **relação D/U** no contorno protegido da vítima  
- Conformidade **RNI** conforme **Ato nº 17.865/2023 (vigência a partir de março/2024)**  
- Integração com **DECEA/SysAGA**: superfícies limitadoras (PBZPA) e **princípio da sombra**  
- Exportações compatíveis com **Mosaico** (KML/SHP e TXT com azimute/distância ou lat/lon)

> Base conceitual exigida pelos anexos:  
> - Mosaico prioriza **KML/SHP**, polígonos devem ser **fechados** e georreferenciados em **SIRGAS 2000**; precisão alta por cruzamento com malhas do **IBGE**.  
> - Para KML/SHP do contorno: gerar **72 radiais (0° a 355° em passos de 5°)**, iterar distância (ex.: 100 m), aplicar regra conservadora/monotonicidade e fechar polígono.  
> - D/U: reconstruir contorno da vítima, amostrar pontos (ex.: 1 km), calcular campo do desejado e do interferente e aplicar discriminação da antena receptora (quando aplicável).  
> - RNI: relatório com memória de cálculo, delimitação de zonas (público/ocupacional), **áreas críticas (hospitais, escolas, creches) em raio de 50 m**, e medições quando aplicável; fórmulas B.1/B.2 referenciadas no Ato.  
> - DECEA/SysAGA: arquivos digitais (KMZ/CAD) devem bater com a ficha; checar superfícies (Transição, Horizontal Interna, Cônica, Aproximação/Decolagem) e usar “sombra” quando permitido.

---

## 0) Objetivo do Produto e Escopo

### Objetivo
Entregar um sistema que permita, por **projeto** e por **revisão** (iterações), configurar uma estação e obter:
1) **Contorno protegido** (polígono + pontos por radial)  
2) **Estudo de viabilidade espectral** (D/U co-canal e adjacentes)  
3) **Relatório RNI** (Ato 17.865) com zonas e áreas críticas  
4) **Relatório/Checklist DECEA** (SysAGA/PBZPA + princípio da sombra)  
5) Exportações: **KML/SHP**, **TXT Mosaico** e pacotes de relatório em PDF

### Serviços suportados (MVP e evolução)
- FM / eFM
- TV Digital (UHF)
- RTR / RadCom (evolução)

---

## 1) Fluxo do Usuário (UI/UX)

### 1.1 Landing Page (MVP 1)
- CTA principal: **Cadastrar / Entrar**
- Seções:
  - “Como funciona” (Dados → Simulação → Mapas/Relatórios → Exportação)
  - “Recursos” (Contorno, D/U, RNI, DECEA/SysAGA)
  - “Exemplos” (mapa + export)
  - Rodapé: Termos/Privacidade

### 1.2 Cadastro / Login (com confirmação por e‑mail)
**Fluxo obrigatório**
1) Usuário informa e‑mail
2) Sistema envia e‑mail de confirmação (token + validade)
3) Usuário confirma e cria senha
4) Login (JWT/Session)
5) Redireciona para **Dashboard**

Regras
- Senhas com hash forte (Argon2id recomendado).
- Tokens de confirmação e reset com hash no banco (nunca armazenar token em claro).

### 1.3 Dashboard (pós-login)
- Lista de projetos (cards/tabela)
- Botões:
  - “Novo projeto”
  - “Importar projeto” (da base interna, quando houver)
- Filtros: serviço, UF, status, data

### 1.4 Wizard “Novo Projeto” (fluxo linear e claro)
A) Serviço (FM/TV/etc)  
B) Geografia (TX lat/lon, altitude, altura AGL, UF/município, datum fixo SIRGAS 2000)  
C) Transmissor/linha/antena (ERP por azimute, diagramas H/V, tilt)  
D) Parâmetros de simulação (limiar do contorno, passo radial, raio máximo, resolução do grid)  
E) Rodar (fila) → resultados (mapa + relatórios + export)

### 1.5 Menu Lateral (após criar projeto)
**Projeto**
- Visão geral (status, inputs)
- Revisões (cada rodada do ciclo)

**Estação**
- Local/Torre
- Transmissor
- Cabo/Linha
- Antena (ganhos, tilt, diagramas)

**Cálculos**
- Contorno (Cobertura)
- Interferência (D/U)
- RNI
- DECEA/SysAGA (OPEA)

**Mapas**
- Viewer com camadas (contorno, grid de campo, pontos D/U, zonas RNI, superfícies OPEA)

**Exportação**
- KML/SHP
- TXT Mosaico
- Pacote PDF (memorial + mapas + tabelas)

---

## 2) Arquitetura Técnica (Back-end, Jobs, Mapas)

### 2.1 Componentes
- Frontend: SPA moderna (React/Next) + mapa (Leaflet/MapLibre)
- API: Flask (REST)
- Jobs: Celery + Redis
- Banco principal: PostgreSQL + PostGIS
- Banco de grade (“PostGrid”): **mesmo PostgreSQL**, schema separado + particionamento
- Armazenamento de arquivos: local (MVP) ou S3/MinIO (evolução)

### 2.2 Por que separar PostGIS vs PostGrid?
- PostGIS (schema `gis`) para vetores (contornos, buffers, polígonos)
- PostGrid (schema `grid`) para dados pesados: tiles/raster/grades por revisão

---

## 3) Banco de Dados (PostgreSQL + PostGIS + “PostGrid”)

### 3.1 Setup do banco
1) Instalar PostgreSQL e PostGIS
2) Criar `ROLE engapp` com permissões controladas
3) Criar DB `engenharia_espectro`
4) Extensões:
   - `postgis`
   - `pgcrypto`
   - `hstore` (opcional)
5) Padrão geométrico:
   - Armazenar tudo em **SIRGAS 2000** quando aplicável.
   - Validar SRID na API.

### 3.2 Schemas
- `auth` — usuários, tokens, auditoria
- `core` — projetos, revisões, estação, equipamentos
- `gis` — geometrias (contornos, buffers, polígonos)
- `grid` — tiles/raster/grades (PostGrid)
- `docs` — relatórios gerados e metadados

### 3.3 Modelo de dados (tabelas mínimas)

#### auth.users
- `id uuid PK`
- `email text UNIQUE NOT NULL`
- `email_verified boolean DEFAULT false`
- `password_hash text NULL`
- `created_at timestamptz`
- `last_login_at timestamptz`

#### auth.email_tokens
- `id uuid PK`
- `user_id uuid FK`
- `purpose text`  (confirm_email | reset_password)
- `token_hash text`
- `expires_at timestamptz`
- `used_at timestamptz NULL`

#### core.projects
- `id uuid PK`
- `user_id uuid FK`
- `name text`
- `service_type text` (FM | eFM | TVD | RTR | RADCOM)
- `status text` (draft | running | done | error)
- `created_at timestamptz`
- `current_revision_id uuid NULL`

#### core.project_revisions
- `id uuid PK`
- `project_id uuid FK`
- `label text` (ex.: “Rev 1”, “Altura 50 m”, etc.)
- `created_at timestamptz`
- `inputs_snapshot jsonb` (reprodutibilidade total)

#### core.station
- `id uuid PK`
- `revision_id uuid FK`
- `tx_lat double precision`
- `tx_lon double precision`
- `ground_alt_m double precision`
- `tower_height_agl_m double precision`
- `frequency_mhz double precision NULL`
- `channel integer NULL`
- `bandwidth_khz integer NULL`
- `polarization text` (H/V/Elíptica)
- `datum text DEFAULT 'SIRGAS2000'`

#### core.transmitter
- `id uuid PK`
- `revision_id uuid FK`
- `tx_power_w double precision`
- `losses_internal_db double precision`
- `notes text`

#### core.feedline
- `id uuid PK`
- `revision_id uuid FK`
- `cable_type text`
- `length_m double precision`
- `attn_db_per_100m double precision`
- `connector_losses_db double precision`

#### core.antenna
- `id uuid PK`
- `revision_id uuid FK`
- `gain_dbd double precision`
- `tilt_electrical_deg double precision`
- `tilt_mechanical_deg double precision`
- `pattern_h_file_id uuid NULL`
- `pattern_v_file_id uuid NULL`

#### gis.contours
- `id uuid PK`
- `revision_id uuid FK`
- `contour_kind text` (protected | autoprotection | others)
- `threshold_dbuvm double precision`
- `method text` (p1546 | hybrid)
- `geom geometry(Polygon, <SRID>)`
- `metadata jsonb`

#### gis.contour_points
- `id uuid PK`
- `contour_id uuid FK`
- `azimuth_deg integer`
- `distance_km double precision`
- `lat double precision`
- `lon double precision`
- `order_idx integer`

#### core.interference_cases
- `id uuid PK`
- `revision_id uuid FK`
- `victim_station_ref text` (identificador Anatel/base interna)
- `relationship text` (co | adj_lower | adj_upper | etc.)
- `du_required_db double precision`
- `notes text`

#### gis.interference_testpoints
- `id uuid PK`
- `case_id uuid FK`
- `geom geometry(Point, <SRID>)`
- `d_dbuvm double precision`  (Desejado)
- `u_dbuvm double precision`  (Interferente)
- `margin_db double precision`
- `pass boolean`

#### core.rni_assessments
- `id uuid PK`
- `revision_id uuid FK`
- `eirp_w double precision`
- `k_reflection double precision`
- `s_limit_w_m2_public double precision`
- `s_limit_w_m2_occ double precision`
- `r_public_m double precision`
- `r_occ_m double precision`
- `notes text`

#### gis.rni_zones
- `id uuid PK`
- `rni_id uuid FK`
- `zone_kind text` (public | occupational)
- `geom geometry(Polygon, <SRID>)`

#### gis.rni_critical_areas
- `id uuid PK`
- `rni_id uuid FK`
- `kind text` (hospital | school | daycare | other)
- `geom geometry(Polygon, <SRID>)`
- `within_50m boolean`

#### core.opea_assessments
- `id uuid PK`
- `revision_id uuid FK`
- `aerodrome_ref text NULL`
- `within_20km boolean`
- `result text` (ok | nok | needs_shadow_study)
- `notes text`

#### docs.files
- `id uuid PK`
- `revision_id uuid FK`
- `kind text` (pattern_h | pattern_v | kml | shp | txt | pdf_report | kmz | cad)
- `storage_path text`
- `sha256 text`
- `created_at timestamptz`

#### grid.field_tiles  (PostGrid)
- `revision_id uuid`
- `layer text` (field_strength | interference | rni | etc.)
- `z int`, `x int`, `y int`  (tile addressing)
- `payload bytea` (PNG/WEBP raster tile) OU `rast raster` (PostGIS Raster)
- `metadata jsonb`
- PK: (`revision_id`,`layer`,`z`,`x`,`y`)

### 3.4 Índices obrigatórios
- `GIST(geom)` em todas as tabelas `gis.*`
- Índices por (`revision_id`, `layer`) em `grid.field_tiles`
- Particionamento de `grid.field_tiles` por `revision_id` (recomendado)

### 3.5 Migrações
- Alembic (Flask-Migrate) com scripts idempotentes
- Seed de tabelas de D/U e thresholds (via YAML/JSON versionado)

---

## 4) Backend (Flask) — Rotas e Contratos

### 4.1 Auth
- `POST /api/auth/register`  {email}
- `POST /api/auth/confirm`   {token, password}
- `POST /api/auth/login`     {email, password}
- `POST /api/auth/forgot`    {email}
- `POST /api/auth/reset`     {token, new_password}
- `POST /api/auth/logout`

### 4.2 Projetos e Revisões
- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/{id}`
- `POST /api/projects/{id}/revisions`
- `GET /api/revisions/{id}`
- `PATCH /api/revisions/{id}` (atualiza inputs)
- `POST /api/revisions/{id}/run` (dispara jobs)

### 4.3 Station
- `PATCH /api/revisions/{id}/station`
- `PATCH /api/revisions/{id}/transmitter`
- `PATCH /api/revisions/{id}/feedline`
- `PATCH /api/revisions/{id}/antenna`
- `POST /api/revisions/{id}/files` (upload diagramas KMZ/CAD/patterns)

### 4.4 Resultados / Mapas / Export
- `GET /api/revisions/{id}/contour`
- `GET /api/revisions/{id}/interference`
- `GET /api/revisions/{id}/rni`
- `GET /api/revisions/{id}/opea`
- `GET /api/revisions/{id}/tiles/{layer}/{z}/{x}/{y}.png`
- `POST /api/revisions/{id}/export/kml`
- `POST /api/revisions/{id}/export/shp`
- `POST /api/revisions/{id}/export/mosaico-txt`
- `POST /api/revisions/{id}/export/report-pdf`

---

## 5) Jobs (Celery) — Execução Assíncrona

### 5.1 Filas
- `calc_contour`
- `calc_interference`
- `calc_rni`
- `calc_opea`
- `build_tiles`
- `export`

### 5.2 Tasks (assinaturas)
- `run_contour(revision_id)`
- `run_interference(revision_id)`
- `run_rni(revision_id)`
- `run_opea(revision_id)`
- `build_tiles(revision_id, layer, z_min, z_max)`
- `export_kml(revision_id)`
- `export_mosaico_txt(revision_id)`
- `export_pdf_report(revision_id)`

### 5.3 Logs e Auditoria
- Toda task deve:
  - gravar `started_at`, `finished_at`, `status`, `error`
  - anexar `inputs_snapshot` (revisão) para reprodutibilidade

---

## 6) Núcleo Matemático — Implementações Obrigatórias

## 6.1 ERP por azimute
Implementar função:
- Entrada: potência transmissor, perdas, ganho antena, tilt, padrão H/V (se aplicável)
- Saída: ERP (W) ou ERP(dBk) por azimute

Regra: se existir tilt elétrico/mecânico significativo, corrigir ganho pelo ângulo de depressão em cada ponto da radial.

## 6.2 Contorno por radiais (KML/SHP)
### Regras essenciais
1) **Gerar 72 radiais** (0° a 355° passo 5°). Opção avançada: 360 radiais (1°).  
2) Ao longo de cada radial:
   - avançar **ponto-a-ponto** (ex.: 100 m)
   - calcular campo **E(d)** usando método híbrido:
     - P.1546 para distâncias curtas/visada direta clara (ex.: < 15 km)
     - Deygout‑Assis para obstruções e/ou maiores distâncias (ex.: > 15 km)
3) Detectar cruzamento do limiar `E_min` (threshold do contorno)
4) **Regra de monotonicidade / abordagem conservadora**:
   - devido a obstruções/reflexões, o campo pode cair abaixo do limiar e depois “recuperar”
   - o contorno deve considerar o **ponto mais distante** onde o sinal ainda supera o limiar
   - se existirem “ilhas” desconectadas, englobar a mais distante se for significativa
5) Conectar os pontos das radiais para formar um **polígono fechado**
6) Exportar:
   - KML (polígono fechado)
   - Shapefile (opcional)
   - TXT (azimute/distância)

### Saídas
- `gis.contours` + `gis.contour_points`

## 6.3 Interferência D/U
Pipeline:
1) Selecionar vítima + relação (co-canal, adjacente inferior/superior)
2) Obter `D/U requerido` da tabela aplicável (TV Digital / FM)
3) Reconstruir contorno protegido da vítima (ou importar do banco/base Anatel)
4) Selecionar pontos de teste ao longo do contorno (ex.: 1 km)
5) Para cada ponto `P_k`:
   - calcular `D_k` (campo desejado, ~E_min)
   - calcular `U_k` (campo da nova estação na direção de `P_k`)
6) Discriminação da antena receptora:
   - TV: aplicar diretividade baseada no ângulo vítima↔interferente
   - FM: assumir recepção omnidirecional/monopolo (discriminação ≈ 0)
7) `margin_db = (D_k - U_k) - (D/U requerido)`
8) PASS se `margin_db >= 0` em todos os pontos

### Tabela D/U (mínimo exigido no escopo textual)
Implementar seed inicial com os valores exibidos para TV Digital:
- Digital/Digital: co-canal 19 dB; adjacente inferior -31 dB; adjacente superior -31 dB
- Digital/Analógico: co-canal 34 dB; adjacentes -31 dB
- Analógico/Digital: co-canal 7 dB; adjacente inferior -6 dB; adjacente superior -12 dB
- Analógico/Analógico: co-canal 45 dB; adjacente inferior -6 dB; adjacente superior -12 dB

> OBS: manter arquitetura para substituir/expandir pelos atos oficiais (ex.: Ato 9751 e 3115).

## 6.4 RNI (Ato 17.865/2023)
### Requisitos mínimos do relatório
- Memória de cálculo dos níveis (V/m e W/m²)
- Delimitação de zonas:
  - ocupacional (restrito)
  - público (livre)
- Áreas críticas: mapear hospitais/clínicas/escolas/creches em **raio de 50 m**
- Medições em campo quando aplicável (sites compartilhados, alta potência, proximidade do limite)

### Variáveis descritas (campo distante)
- `r` distância de conformidade (m)
- `EIRP` (W) = potência transmissor × ganho × perdas
- `K` fator de reflexão do solo (típico K=2.56, ou K=4 conservador)
- `S_lim` limite de densidade de potência (W/m²) conforme tabelas do Ato

Implementação:
- Criar módulo `rni.py` com funções:
  - `calc_eirp_w(...)`
  - `calc_r_compliance_far_field(eirp_w, k, s_lim)`  **(B.1/B.2)**  
    - Implementar como função parametrizada e versionada, para atualização quando a expressão final for consolidada.
- Gerar geometria das zonas (buffers) e registrar em `gis.rni_zones`
- Integrar dados de “áreas críticas” (camada própria) e marcar `within_50m`

> Observação: o anexo destaca também campo próximo (Fresnel) e recomenda modelagens numéricas (MoM/FDTD) ou envelope cilíndrico quando necessário. Implementar flag “near_field_required”.

## 6.5 DECEA / SysAGA (OPEA)
### Requisitos operacionais
- Se dentro de áreas de proteção ou em raio de 20 km de aeródromo:
  - indicar direção e distância ao ARP/cabeceiras
- SysAGA frequentemente exige:
  - PDFs assinados
  - arquivos vetoriais KMZ (Google Earth) ou CAD
  - coerência total entre arquivo digital e ficha (discrepâncias de segundos em lat/lon geram indeferimento)

### Superfícies críticas (PBZPA)
- Transição
- Horizontal Interna
- Cônica (inclinação típica ~5%)
- Aproximação e Decolagem (com possibilidade de aplicar “princípio da sombra”)

### Princípio da Sombra (shielding)
- Permite viabilizar obstáculo “escondido” atrás de obstáculo permanente (morro/prédio consolidado)
- Requer estudo específico:
  - topo da antena não ultrapassa o plano de sombra projetado
  - margem descendente típica de 10% a partir do topo do obstáculo escudo
  - levantamento topográfico do objeto proposto e do obstáculo escudo

Implementação:
- `opea.py` com:
  - `check_within_20km_aerodrome(...)`
  - `evaluate_surfaces(...)` (geometria + interseção)
  - `evaluate_shadow_principle(...)` (quando aplicável)

---

## 7) Exportações (Mosaico)

### 7.1 KML/SHP
- Gerar KML com polígono fechado do contorno
- Garantir datum SIRGAS 2000 e alta precisão dos vértices

### 7.2 TXT para Mosaico
Formato TXT (colunas delimitadas):
- `AZIMUTE; DISTANCIA_KM` **ou**
- `LAT; LON`

> Padronizar no export:
- 72 linhas (0..355 passo 5°) + linha final repetindo o primeiro ponto para fechamento (opcional, se exigido).
- Distância em km com precisão (ex.: 3 casas).
- Separador `;` (ou `,` configurável), com cabeçalho opcional.

---

## 8) Frontend — Organização e Componentes

### 8.1 Design system
- Layout: Topbar + Sidebar + Conteúdo
- Sidebar agrupada por domínio (Projeto / Estação / Cálculos / Mapas / Export / Documentos)
- Páginas com:
  - “Inputs” à esquerda (ou topo)
  - “Resultados” (tabelas + mapas)
  - “Logs” (painel colapsável)
  - “Exportar” (ações)

### 8.2 Viewer GIS
Camadas:
- Contorno protegido
- Pontos por radial
- Pontos de teste D/U e heatmap de margem
- Zonas RNI (público/ocupacional) + áreas críticas 50m
- Camadas OPEA (quando representáveis)

Tiles:
- consumir `/tiles/{layer}/{z}/{x}/{y}` do backend

---

## 9) Qualidade, Testes e Reprodutibilidade

### 9.1 Reprodutibilidade obrigatória
- Toda revisão salva `inputs_snapshot`
- Toda execução salva:
  - versão do algoritmo (ex.: `contour_algo_version`)
  - parâmetros (passo radial, limiar, raios)

### 9.2 Testes mínimos
- Unitários:
  - ERP (perdas/ganhos)
  - geração de radiais e fechamento do polígono
  - regra de monotonicidade (casos de queda/recuperação)
- Integração:
  - rodar uma revisão end-to-end (contorno + export TXT)
  - rodar um caso D/U com pontos e relatório PASS/FAIL
- Geometria:
  - polígono válido (ST_IsValid)
  - SRID correto
  - KML válido

---

## 10) Deploy (Linux) — sem Docker (systemd)

### 10.1 Serviços systemd
- `engenharia-api.service` (gunicorn + Flask)
- `engenharia-worker.service` (celery worker)
- `engenharia-beat.service` (celery beat, se necessário)
- `redis.service` (já do sistema)
- `postgresql.service` (já do sistema)

### 10.2 Variáveis de ambiente
- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `JWT_SECRET` (se usar JWT)
- `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS`, `SMTP_PORT`, `SMTP_FROM`

### 10.3 Rotina operacional
- `alembic upgrade head`
- seed D/U, thresholds, parâmetros default
- backup automático do Postgres
- rotação de logs

---

## 11) Roadmap (ordem que reduz risco)

### Fase 1 (Fundação)
- Landing + Auth (confirmação e-mail)
- Projetos + Revisões
- PostGIS pronto (schemas + migrações)

### Fase 2 (MVP técnico)
- Contorno por radiais + regra conservadora
- Export TXT Mosaico + KML
- Mapa com contorno

### Fase 3 (Viabilidade espectral)
- D/U (co e adjacentes) com pontos no contorno da vítima
- Mapa de margem

### Fase 4 (RNI)
- Cálculo de distância de conformidade (B.1/B.2 parametrizado)
- Zonas e áreas críticas 50 m
- Relatório PDF

### Fase 5 (DECEA/SysAGA)
- Checagem de superfícies + sombra
- Pacote de evidências (KMZ/CAD + relatório)

### Fase 6 (Escala)
- PostGrid com tiles, cache e particionamento
- Otimizações de performance e auditoria completa

---

## 12) Definição de Pronto (DoD)
Um projeto é “pronto para submissão” quando:
- Exporta KML/SHP com polígono fechado e SIRGAS2000
- Exporta TXT Mosaico em `AZIMUTE;DISTANCIA_KM` ou `LAT;LON`
- Entrega D/U com pontos de teste e PASS/FAIL auditável
- Entrega relatório RNI com zonas, áreas críticas (50 m) e memória de cálculo
- Entrega checklist/documentação integrada para MCom/Anatel/DECEA


# Engenharia de Espectro — Plano Mestre (Frontend + Backend + Núcleo Matemático) — V4

Este arquivo é o **prompt/instrução única** para um agente implementar o sistema completo **Engenharia de Espectro**, combinando:
- **UX/Frontend** (Landing pública + Workspace pós-login inspirado nas telas do Spectrum‑E)
- **Arquitetura de alta performance** (Flask API + Celery/Redis + Numba)
- **Banco PostgreSQL/PostGIS otimizado** (SIRGAS 2000 / EPSG:4674)
- **Ingestão de dados local** (`./anatel` e `./anatel/DEM`)
- **Requisitos regulatórios** (Anatel: Atos 9751 – TV, 8104 – FM; Resolução 721; ICA 63-19)

> Regras do produto
1) **Somente Landing + Login/Confirmação** são públicos.  
2) **Todo o restante** (Portal, Rede, Banco de dados, Mapa, Calculadoras, Arquivos, Documentos) é **pós-login** e usa rotas protegidas.  
3) Cálculos pesados **nunca** bloqueiam a API: devem rodar em **workers Celery**, com status e logs no front.

---

## 1) Landing Page e Confirmação por E-mail

### 1.1 Landing Page (pública) — foco “precisão técnica + conformidade”
**Rotas**
- `/` Landing
- `/login`
- `/confirm?token=...` (validação de e-mail + criação de senha)
- (opcional) `/pricing`, `/docs-public`

**Hero**
- Background: **mesh 3D de relevo (SRTM)** + **contornos dinâmicos em SVG** (animação leve)
- Headline: planejamento RF com ênfase em engenharia e conformidade Anatel
- CTA principal: **Cadastrar / Entrar**
- usar logo.png no menu e em toda as áreas do aplicativo inclusive no ícone da página no navegador

**Diferenciais técnicos (blocos curtos)**
- **Processamento bare‑metal com Numba** (performance próxima de C++ em Python)
- Conformidade com **Atos 9751 (TV)** e **8104 (FM)** (Anatel)
- Difração **Deygout‑Assis determinística** para relevos complexos
- Integração com **IBGE 2022** e **Mosaico Anatel**


**Social proof / credibilidade**
- “Baseado em dados oficiais (IBGE ultimo divulgado) e fluxos compatíveis com o Mosaico Anatel”
- Link para documentação pública curta (sem revelar telas internas)

---

### 1.2 E-mail de confirmação — template HTML profissional

**Objetivo:** parecer “plataforma de engenharia”, sem marketing excessivo.

**Assunto**
- `Confirmação de Acesso — Engenharia de Espectro`

**Conteúdo (HTML)**
- Header: logo minimalista + título
- Corpo:
  - “Sua conta foi verificada. Você agora tem acesso à plataforma de planejamento RF com suporte a modelos ITU‑R P.1546 e Deygout‑Assis.”
- CTA: botão central: **Acessar Workspace**
- Footer: links para referências técnicas e suporte (ICA 63-19, Resolução 721)

**Arquivo sugerido**
- `backend/templates/email_confirm.html`

**Template base (copiar e ajustar)**
```html
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Confirmação de Acesso — Engenharia de Espectro</title>
</head>
<body style="margin:0;background:#f6f8fb;font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,Arial;">
  <table width="100%" cellpadding="0" cellspacing="0" style="padding:24px 12px;">
    <tr><td align="center">
      <table width="640" cellpadding="0" cellspacing="0" style="background:#fff;border:1px solid #e6eaf2;border-radius:14px;overflow:hidden;">
        <tr>
          <td style="padding:18px 22px;background:#0b2447;color:#fff;">
            <div style="font-size:14px;letter-spacing:.08em;text-transform:uppercase;opacity:.9;">Engenharia de Espectro</div>
            <div style="font-size:18px;font-weight:600;margin-top:4px;">Confirmação de Acesso</div>
          </td>
        </tr>
        <tr>
          <td style="padding:22px;">
            <div style="font-size:16px;font-weight:600;color:#0f172a;">Sua conta foi verificada.</div>
            <div style="margin-top:8px;font-size:14px;line-height:1.55;color:#334155;">
              Você agora tem acesso à plataforma de planejamento RF com suporte a modelos
              <strong>ITU‑R P.1546</strong> e <strong>Deygout‑Assis</strong>.
            </div>

            <div style="margin-top:18px;text-align:center;">
              <a href="{{WORKSPACE_URL}}"
                 style="display:inline-block;background:#0b5fff;color:#fff;text-decoration:none;
                        padding:12px 18px;border-radius:10px;font-weight:600;">
                Acessar Workspace
              </a>
            </div>

            <div style="margin-top:18px;font-size:12px;line-height:1.6;color:#64748b;">
              Referências: ICA 63-19 • Resolução 721 • Atos 9751/8104
              <br/>
              Suporte: <a href="{{SUPPORT_URL}}" style="color:#0b5fff;text-decoration:none;">Central Técnica</a>
            </div>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
```

---

## 2) Banco de Dados (PostgreSQL/PostGIS) — SIRGAS 2000 (EPSG:4674)

### 2.1 Princípios
- Tudo que for geoespacial deve usar **SRID 4674 (SIRGAS 2000)**.
- Índices:
  - `GIST` em geometrias
  - `BTREE` em colunas de filtro frequente (serviço, canal, uf, município, tipo)
- Padrão: `geom GEOMETRY(...)` sempre com SRID 4674.

### 2.2 Tabelas e campos obrigatórios (adaptação)
**stations**
- `id (uuid)`
- `network_id (uuid)`
- `service (text)` (FM/TV/AM/RTR/...)
- `status (text)` (existente/proposta/etc.)
- `canal (int)` / `freq_mhz (numeric)`
- `uf (char(2))`, `municipio (text)`
- `geom POINT SRID 4674`
- `h_eff (numeric)` **obrigatório** (heff P.1546)
- `htx (numeric)` **obrigatório** (altura antena)
- `d_max (numeric)` **obrigatório** (distância máxima/alcance de busca/coordenação)
- `mosaico_id (text)` **obrigatório** (ID Mosaico/Anatel)
- `entidade (text)` **obrigatório** (operador/entidade)
- `created_at, updated_at`

**antennas**
- `id (uuid)`
- `name (text)`
- `manufacturer (text)`
- `gain_dbd (numeric)` **obrigatório**
- `tilt_el (numeric)` **obrigatório**
- `pattern_h JSONB` **obrigatório** (diagrama horizontal: azimute→ganho)
- `pattern_v JSONB` **obrigatório** (diagrama vertical: elevação→ganho)
- `created_at, updated_at`

**rasters** (metadados do DEM/HGT)
- `id (uuid)`
- `filename (text)` **obrigatório**
- `bbox GEOMETRY(POLYGON,4674)` **obrigatório**
- `resolution_arcsec (numeric)` **obrigatório**
- `created_at`

**contours**
- `id (uuid)`
- `network_id (uuid)` **obrigatório**
- `station_id (uuid)` (opcional)
- `field_strength_dbuvm (numeric)` **obrigatório**
- `model (text)` (ex.: ITU1546_50_50)
- `geom GEOMETRY(MULTIPOLYGON,4674)` **obrigatório**
- `created_at`

**networks**
- `id (uuid)`
- `owner_user_id (uuid)`
- `name (text)`
- `description (text)`
- `created_at, updated_at`

**jobs**
- `id (uuid)`
- `network_id (uuid)`
- `type (text)` (contour, interference, p1546, deygout, ...)
- `status (text)` (queued/running/done/error)
- `progress (int)`
- `params JSONB`
- `result_ref JSONB`
- `error TEXT`
- `created_at, updated_at`

### 2.3 Migrações
- Usar Alembic.
- Criar `sql/` com extensões:
  - `CREATE EXTENSION postgis;`
  - `CREATE EXTENSION postgis_topology;` (se necessário)
  - (opcional) `CREATE EXTENSION pg_trgm;` (busca por texto)

---

## 3) Ingestão local (./anatel e ./anatel/DEM) + verificação proativa

### 3.1 Pastas (fixas)
- Dados Anatel (CSVs,xmls, shapefiles, etc.): `./anatel/`
- DEM tiles SRTM/HGT: `./anatel/DEM/`

### 3.2 Parser Anatel (ETL)
**Objetivo:** importar CSVs ou xml de ./antel do Mosaico para `stations`, garantindo SRID 4674.

Regras:
- Se origem vier em outro SRID, usar `ST_Transform` para 4674.
- Normalizar UF, município, serviço, canal/frequência.
- Guardar `mosaico_id` e `entidade`.

Script:
- `backend/etl/import_mosaico_csv.py`
- Deve aceitar:
  - caminho do CSV ou XML
  - network_id destino (ou “default network”)
  - flags de upsert (por mosaico_id)

### 3.3 Verificador de DEM (indexador HGT)
**Objetivo:** indexar `./anatel/DEM/*.hgt` em `rasters` e garantir **proatividade**.

Script:
- `backend/etl/index_dem_tiles.py`
- Para cada `.hgt`:
  - deduzir bbox do tile pelo nome (SRTM tile naming)
  - gravar bbox em 4674
  - gravar `resolution_arcsec` (ex.: 1 ou 3 arcsec)
- Criar índice GIST em `rasters.bbox`.

### 3.4 Proatividade antes de cálculo
Antes de qualquer job:
- Calcular quais tiles são necessários:
  - P.1546: heff usa radiais entre 3 km e 15 km → tiles que cobrem buffer de **15 km** do TX
  - Deygout: tiles ao longo do **perfil completo** (TX→RX/contorno)
- Verificar `rasters` e presença do arquivo físico.
- Se faltar tile:
  - **não baixar automaticamente** (assumir que download já existe em outro módulo - deve ser criado se ainda não foi)
  - registrar alerta e mostrar no dashboard:
    - “Faltam tiles DEM: NxxWyyy.hgt, .. fazendo download.”
  - permitir o usuário “reprocessar” após corrigir.

API para alertas:
- `GET /api/networks/{id}/alerts` → lista de pendências (DEM faltante, dados inválidos, jobs com erro)

---

## 4) Núcleos matemáticos (Backend) — Flask + Redis + Celery + Numba

### 4.1 Arquitetura de execução
- API Flask:
  - valida parâmetros e salva “job”
  - enfileira no Celery
- Worker Celery:
  - executa cálculo pesado
  - grava resultados (contour/interference/perfis) no DB
  - atualiza status/percentual do job
- Redis:
  - broker + backend do Celery (ou backend no Postgres, se preferir)

### 4.2 Deygout‑Assis (determinístico) — Numba
**Objetivo:** perda por difração por múltiplos gumes, com seleção recursiva do obstáculo principal e secundários.

Implementação:
- Extrair perfil (distância x altitude) via leitura HGT (GDAL/rasterio) ou leitura direta + interpolação
- Calcular a linha de visada (LOS) e a altura “h” do obstáculo acima da LOS
- Parâmetro de Fresnel-Kirchhoff (nu):
  - **Implementar a forma padrão**:
    - `nu = h * sqrt( (2*(d1+d2)) / (lambda * d1 * d2) )`
  - Garantir unidades coerentes: `d1,d2,h` em metros, `lambda` em metros
- Deygout recursivo:
  - identifica obstáculo principal (maior nu)
  - calcula perda do principal
  - subdivide perfil em dois subperfis e repete
- “Correção de Assis”:
  - ajuste no topo do obstáculo (parabólico) para estimar raio de curvatura `R`
  - aplicar perda adicional por cilindro/curvatura (registrar fórmula/config, deixar parametrizável)

Código:
- `backend/math/deygout_assis.py`
- Funções:
  - `extract_profile(tx, rx, dem_index) -> (dist_m, elev_m)`
  - `deygout_assis_loss(dist_m, elev_m, f_mhz, tx_h_m, rx_h_m, params) -> loss_db`
- Decorar trechos críticos com `@numba.njit(cache=True, fastmath=True)`.

### 4.3 ITU‑R P.1546 (estatístico) — interpolação multidimensional + heff + TCA
Requisitos:
- Interpolar tabelas (freqs 100/600/2000 MHz e alturas) e distâncias
- Calcular `heff`:
  - média do terreno entre **3 km e 15 km** ao longo de cada radial
  - radialização padrão (ex.: 360 radiais de 1° ou 72 radiais de 5°), parametrizável
- TCA (Terrain Clearance Angle):
  - analisar primeiros **16 km** a partir do receptor e aplicar correção de obstrução local

Código:
- `backend/math/p1546.py`
- Funções:
  - `compute_heff(tx_point, dem) -> heff_by_azimuth`
  - `p1546_field_strength(tx_params, rx_point, heff, tca, env_params) -> E_dbuvm`
  - `p1546_contour(tx_params, target_E_dbuvm, azimuth_step_deg=1) -> polygon`

Numba:
- Use Numba para loops de radiais + amostragem do DEM + interpolação.
- Use arrays NumPy contíguos (float64) e evite objetos Python dentro do `njit`.

---

## 5) Telas pós‑login (mapeamento completo + ajustes)

### 5.1 Portal (primeira página após login) — **/app/home**
Esta é a primeira página do usuário após autenticação (equivalente ao “Portal do Spectrum‑E”), porém com design moderno.

**Conteúdo**
- Header com:
  - “Bem vindo <Nome> ao Portal do Spectrum‑E”
  - e-mail logado
  - expiração em X dias + botão “Renew now”
- Cards:
  - Análise Técnica
  - Minhas Redes
  - Minhas Predições
  - Meus Arquivos
  - Documentos
  - Calculadoras RF
  - Quadro de Atribuição
  - Support
  - Descrições de Funcionalidades
  - Terminar sessão

**Upgrade obrigatório (métricas)**
Adicionar “mini-métricas” no topo (chips/cards pequenos):
- “X Estações na Rede ativa”
- “Y Predições ativas”
- “DEM faltante: N tiles” (alerta)
- “Jobs em execução: K”

APIs:
- `GET /api/auth/me`
- `GET /api/portal/metrics` (agregado rápido)
- `GET /api/networks/{id}/alerts`

---

### 5.2 Minhas Redes — tabela de projetos (pós-login)
- Rota: `/app/networks`
- Tabela virtualizada (para muitas redes):
  - Nome, Criada em, Última execução, Estações, Status
- Ações:
  - Criar Rede
  - Abrir
  - Duplicar
  - Arquivar

API:
- `GET /api/networks`
- `POST /api/networks`
- `PATCH /api/networks/{id}`

---

### 5.3 Gerenciamento da Rede — sidebar + tabela (inspirado nas telas capturadas)
- Rota: `/app/network`
- Topbar com abas: Início | Banco de dados | Rede | Mapa
- Sidebar com comandos (com scroll) e grupos:
  - Objetos (Adicionar/Editar, Modificar Selecionados, Deletar, Ativar/Desativar, Mapear, Converter)
  - Importação (Importar Plano Básico, Importar Estações FM)
  - Cálculos (Ajustar ERP/HTx, Analisar Viabilidade, Plotar/Calcular Contorno, Deygout‑Assis, P1546, Longley‑Rice)
  - Relatórios (Relatório de Cobertura)
  - Utilidades (Distância entre canais, distância da fronteira, porcentagem de cobertura, limitar contorno protegido)
  - Perfis (ITM‑1.2.2, ITU‑452)

**Tabela**
- Virtualizada (TanStack Table + windowing) para milhares de estações
- Filtros:
  - tipo (FM/TV/AM)
  - UF/município
  - canal/frequência
  - status (existente/proposta)
- Seleção:
  - seleção por linha + Selecionar Todos (página) + Deselecionar
- Colunas base (como na tela):
  - `#`, `onoff`, `tipo`, `resultado`, `município`, `uf`, `distância`, `canal`, `freq`, `serviço`, `alt...`

---

### 5.4 Mapa (WMAP) + Opções de Visualização — performance
- Rota: `/app/map`
- Leaflet com `preferCanvas: true`
- Camadas:
  - Objetos (pontos com label)
  - Círculos (buffers)
  - Contornos (MultiPolygon)
  - Interferência (polígono/heat)
  - Vetores do usuário (GeoJSON)
  - Malha censitária IBGE via **Vector Tiles (MVT) ou shapfiles em ./anatel **

**Vector Tiles (MVT)**
- Backend: endpoint tile:
  - `GET /api/tiles/ibge/{z}/{x}/{y}.pbf`
- Gerar MVT pelo PostGIS com `ST_AsMVT` e `ST_AsMVTGeom`.
- Front: usar plugin Leaflet para MVT ou migrar MapLibre GL.

**Opções de Visualização** (tela dedicada/modal)
- Rota: `/app/map/options`
- Tabela de objetos:
  - Exibir (checkbox)
  - Tipo (ponto/linha/caixa)
  - Cor
  - Largura
  - Legenda (campo: canal, tipo, frequência, name)
- Persistir por usuário em DB (opcional)

**Upload vetorial**
- Upload de KML/SHP
- Conversão no servidor para GeoJSON
- Armazenar como “user_vectors” e renderizar em camada

API:
- `POST /api/vectors/upload`
- `GET /api/vectors`
- `DELETE /api/vectors/{id}`

---

### 5.5 Modais de parâmetros (pós-login) — essenciais
**(A) Ajustar ERP/HTx**
- Objetivo: otimizar potência/altura para cumprir “Regra dos 5%” (simplificação Anatel)
- UI:
  - inputs do TX (ERP/HTx atuais, limites, alvo de contorno)
  - tabela comparativa de resultados (antes/depois)
  - botão “Aplicar no objeto”
- Backend:
  - `POST /api/revisions/{rev_id}/erp-htx/preview`
  - `POST /api/revisions/{rev_id}/erp-htx/apply`

**(B) Importar Estações FM**
- UI:
  - coordenadas TX (SIRGAS 2000)
  - raio de busca
  - filtros co‑canal e adjacentes
- Backend:
  - `POST /api/network/import-fm` (job)
  - retorna lista/preview + inserir na rede

---

## 6) Contratos de API (mínimo viável)

### 6.1 Auth
- `POST /api/auth/register` (email)
- `POST /api/auth/confirm` (token + senha)
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

### 6.2 Redes / Objetos
- `GET /api/networks`
- `POST /api/networks`
- `GET /api/network/objects?network_id=...&type=FM&page=...`
- `POST /api/network/objects`
- `PATCH /api/network/objects/{id}`
- `PATCH /api/network/objects/bulk`
- `DELETE /api/network/objects/bulk`

### 6.3 Jobs
- `POST /api/jobs` `{ network_id, type, params }` → `{ job_id }`
- `GET /api/jobs/{job_id}` → status/progress/log
- `GET /api/jobs?network_id=...`

### 6.4 Resultados geoespaciais
- `GET /api/contours?network_id=...`
- `GET /api/interference?network_id=...`
- `GET /api/terrain/profile?...` (se necessário)

---

## 7) Fluxo de trabalho do agente (ordem obrigatória)

### Etapa 1 — Ambiente bare‑metal (instalação)
- Postgres + PostGIS
- Redis
- Celery
- Gunicorn
- GDAL/rasterio deps (para HGT)
- Node/npm para frontend

### Etapa 2 — DB + migrações
- criar schema conforme seção 2
- índices GIST/BTREE
- seed mínimo: 1 rede default (para testes)

### Etapa 3 — ETL (./anatel e ./anatel/DEM)
- `index_dem_tiles.py` (indexador)
- `import_mosaico_csv.py` (parser/anatel)
- endpoints para importar e exibir progresso

### Etapa 4 — Núcleo matemático
- implementar `p1546.py` (heff + interpolação + TCA) com Numba
- implementar `deygout_assis.py` com Numba
- jobs Celery para:
  - contorno (P1546)
  - deygout/perfil
  - interferência (estrutura base)

### Etapa 5 — Frontend React
- Landing (pública) + Login/Confirm
- App Shell pós-login:
  - Topbar (abas)
  - Sidebar por módulo
- Portal `/app/home` com cards + métricas
- Rede `/app/network` com tabela virtualizada + ações da sidebar
- Mapa `/app/map` com Leaflet preferCanvas + camadas + opções
- Upload vetorial + render

### Etapa 6 — Relatórios
- Exportar PDF/KML (“memorial descritivo”) pronto para fluxo Mosaico
- Incluir:
  - parâmetros do TX
  - metodologia (P1546/Deygout)
  - contornos e mapas
  - tabelas de interferência/cobertura

---

## 8) Critérios de aceitação (objetivos verificáveis)

- [ ] Landing pública com Hero (mesh DEM + contornos SVG) e CTA “Cadastrar/Entrar”
- [ ] E-mail de confirmação HTML com CTA “Acessar Workspace”
- [ ] Pós-login redireciona para `/app/home` (Portal com cards + métricas)
- [ ] Banco PostGIS em EPSG:4674 com tabelas e índices definidos
- [ ] Indexador `./anatel/DEM` cria metadados e detecta tiles faltantes
- [ ] Parser Anatel importa CSVs e normaliza SRID/atributos
- [ ] Jobs Celery executam cálculos sem bloquear API; front acompanha progresso
- [ ] `/app/network` com sidebar completa e tabela virtualizada + seleção
- [ ] `/app/map` com Leaflet preferCanvas, camadas e opções de visualização
- [ ] Vector Tiles MVT (IBGE) funcionando (endpoint .pbf + render)
- [ ] Relatório PDF/KML gerado via endpoint e baixável

---

## 9) Observação final (próximos detalhamentos)
Se for necessário detalhar agora, em arquivos separados:
- `etl/import_mosaico_csv.py` (parser Anatel)
- `math/p1546.py` (interpolação + heff + TCA)
- `math/deygout_assis.py` (recursão + correção de Assis + Numba)

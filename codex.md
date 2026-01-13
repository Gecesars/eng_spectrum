# Engenharia de Espectro - Status Atual do Projeto

## Visao geral
Projeto para engenharia de espectro com backend Flask e frontend React. Ha dois eixos de produto convivendo:
1) fluxo "legacy" por projetos/revisoes (contorno, interferencia, RNI, OPEA, exportacoes) e
2) fluxo "V4" por redes (networks/stations/jobs + mapa com tiles MVT).

## Arquitetura atual
- Backend: Flask + SQLAlchemy + Alembic, com Celery/Redis para jobs e Postgres/PostGIS como base principal.
- Frontend: React 18 + Vite + TypeScript + Tailwind + shadcn/ui, com React Router, TanStack Query e Zustand.
- Dados: schemas Postgres separados (auth, core, gis, grid, docs, anatel).
- Armazenamento: arquivos em `exports/` e `storage/`.

## Backend (rotas e servicos principais)
### Auth
- `POST /api/auth/register` (email), `POST /api/auth/confirm` (token + senha), `POST /api/auth/login`
- Tokens de sessao via itsdangerous (nao JWT real).
- UI de confirmacao embutida em `/confirm?token=...`.

### Projetos/Revisoes (legacy)
- `GET/POST /api/projects`, `POST /api/projects/{id}/revisions`
- `GET/PATCH /api/revisions/{id}`, `POST /api/revisions/{id}/run`
- Atualizacao de estacao/transmissor/linha/antena via `PATCH /api/revisions/{id}/...`
- Resultados: contorno, interferencia, RNI, OPEA
- Exportacoes: KML/SHP/TXT (PDF ainda nao implementado)

### V4 (redes)
- `GET/POST /api/v4/networks`
- `GET /api/v4/networks/{id}/stations` (GeoJSON)
- `POST /api/v4/stations` (cria estacao)
- `POST /api/v4/jobs/link` + `GET /api/v4/jobs/{id}` (job de perfil/enlace)
- `GET /api/v4/tiles/ibge/{z}/{x}/{y}.pbf` (MVT a partir de `core.stations_v4`)

### Servicos matematicos
- Contorno por radiais (modelo simples com ERP/ganho/perdas).
- Interferencia D/U no contorno.
- RNI: calculo de distancia de conformidade (B.1/B.2).
- OPEA: checagem simples de raio 20 km de aerodromos.
- V4: perfil de enlace com Deygout (perfil de terreno ainda "mock").

## Frontend atual
- Rotas publicas: `/`, `/login`, `/register`.
- Rotas protegidas: `/app/home`, `/app/networks`, `/app/network/:id/...`.
- Dashboard: cards de metricas usando `GET /api/v4/networks`.
- Modulos de rede: lista de estacoes, mapa (MapLibre + OSM + MVT), calculos de enlace.
- Estado global de auth em Zustand + token em localStorage.

## Dados e ETL
- Dados Anatel e DEM em `anatel/`.
- CLI Flask: criar usuario, importar Anatel XML e aerodromos.
- Scripts ETL em `backend/etl/` para importar XML em `stations_v4` e indexar tiles DEM.
- Migracoes Alembic em `migrations/` (inclui modelos legacy, anatel e V4).

## Situacao atual (gaps e pontos de atencao)
- Conflito de modelos de contorno: `app.models.Contour` aponta para `core.contours` (V4), mas rotas/servicos legacy esperam `gis.contours` (GISContour). Isso quebra `contour`, `results` e `export` do fluxo legacy.
- Backend serve `/` com `frontend/index.html` e espera `frontend/app.js`/`styles.css`, mas o frontend atual e Vite (sem build em `frontend/dist`). Resultado: rota estatica nao funciona sem build/ajuste.
- Backend tenta servir `/v4/` de `frontend/v4`, mas a pasta nao existe.
- UI chama endpoints nao implementados:
  - `POST /api/v4/networks/{id}/import` (ImportStationsModal)
  - `PATCH /api/v4/networks/{id}/stations/bulk` (AdjustParamsModal)
- Job de enlace retorna `loss_db`, `distance_km`, `profile_sample_count`, enquanto o frontend espera `result.profile`, `fsl_db` e `margin_db`.
- Status de job no backend e `pending/running/done/error`, mas o frontend encerra polling apenas em `completed/failed`.
- Criacao de network em V4 usa o primeiro usuario do banco (sem auth real).
- Fluxo de registro depende de SMTP; README menciona token retornado pela API, mas isso nao ocorre no codigo.
- Nao ha UI para "forgot password" no frontend (link aponta para rota inexistente).
- Importacao e calculos legacy (interferencia, RNI, OPEA) nao tem telas no frontend atual.
- Tiles MVT nao filtram por `network_id` (mostram todas as estacoes).
- Scripts de verificacao (verify_*) e alguns testes parecem desatualizados.

## Resumo
O repositorio combina a base do MVP legacy (projetos/revisoes) com um novo fluxo V4 (redes). O backend tem boa parte da logica de calculo e persistencia, mas ha divergencias entre modelos, endpoints e frontend. O frontend esta focado no V4 e ainda possui chamadas para endpoints inexistentes ou incompletos.

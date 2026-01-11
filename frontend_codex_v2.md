# Engenharia de Espectro — Frontend Pós‑Login (React + Vite) — Guia V2 (com telas do fluxo Spectrum‑E)

Este documento define **o frontend que o usuário verá SOMENTE APÓS LOGIN**, inspirado no fluxo do Spectrum‑E.
Ele inclui:
- **descrição detalhada de cada tela** (a partir dos screenshots fornecidos, fora de ordem)
- rotas, componentes e estado
- implementação-base (páginas/modais) + contratos de API para cada função

> Regras de produto
- A Landing Page é pública.
- **TODO o conteúdo descrito aqui está atrás de autenticação** (Protected Routes).
- Após login, o usuário vai para **/app/home** (Portal).

---

## 0) Stack e decisões técnicas (fixas)

### 0.1 Tecnologias
- React 18 + TypeScript + Vite
- TailwindCSS
- React Router v6
- TanStack Query (cache e estado server)
- Zustand (estado global: auth, seleção, preferências de mapa)
- React Hook Form + Zod (forms)
- TanStack Table (tabela da “Rede”)
- Axios (API client)
- shadcn/ui (Card, Button, Tabs, Dialog, Select, Toast, Separator, Checkbox, etc.)
- Mapa: Leaflet (MVP) ou MapLibre GL (evolução)

### 0.2 Convenções de UI/UX
- Páginas de cálculo pesado disparam **jobs** e acompanham status.
- Todas as telas têm:
  - loading state
  - error state com retry
  - toast para sucesso/erro
- “Terminar sessão” sempre pede confirmação.

---

## 1) Rotas (pós-login) — obrigatório

### 1.1 Estrutura
- `/` Landing (pública)
- `/login` (pública)
- `/confirm` (pública: token email + criação de senha)
- `/app/*` (privado)

### 1.2 Rotas privadas
- `/app/home`  → **Portal (primeira tela após login)**
- `/app/network` → Rede (lista + ações)
- `/app/map` → Mapa (camadas, opções de visualização, objetos)
- `/app/database` → Banco de dados (cadastros/imports internos)
- `/app/docs`, `/app/files`, `/app/support`, `/app/features`, `/app/rf-tools`, `/app/allocations`, `/app/billing` (módulos do portal)

---

## 2) Catálogo das telas (fora de ordem) — o que cada imagem representa

A seguir, cada screenshot (fora de ordem) foi mapeado para uma tela/feature do seu app.

### TELA A — Portal pós-login (primeira página do usuário)
**Texto visível**
  - “Bem vindo Fernando Ferreira ao Portal do Spectrum‑E.”
- “Você está conectado como fernandoferreira.af2@gmail.com. Seu acesso expira em 7 dias: Renew now”
- Cards: Análise Técnica, Minhas Redes, Minhas Predições, Meus Arquivos, Documentos, Calculadoras RF, Quadro de Atribuição, Support, Descrições de Funcionalidades, Terminar sessão

**Implementação**
- Rota: `/app/home`
- Componente: `HomeTab.tsx`
- Layout: header com status + grid de cards (3 colunas no desktop)
- Ações:
  - Cards navegam para rotas internas
  - “Terminar sessão”: abre confirmação → logout → redirect `/login`

**API (mínimo)**
- `GET /api/auth/me` → `{ name, email, expires_in_days }`

---

### TELA B — “Rede > Gerenciamento da Rede” (lista + filtro + tabela)
**Elementos visuais**
- Topbar com logo + abas: Início | Banco de dados | Rede | Mapa
- Sidebar “Gerenciamento da Rede” com lista de comandos
- Área principal:
  - dropdown “Tipo de Objeto: FM [1]”
  - botões: Anterior | Próximo | Selecionar Todos | Deselecionar Todos
  - tabela com colunas: `#`, `onoff`, `tipo`, `resultado`, `município`, `uf`, `distância`, `canal`, `freq`, `serviço`, `alt. ...`

**Implementação**
- Rota: `/app/network`
- Página: `NetworkListPage.tsx`
- Componentes:
  - `Topbar.tsx` (Tabs)
  - `Sidebar.tsx` (menu de ações do módulo Rede)
  - `DataTable.tsx` (TanStack Table + seleção)
- Estado:
  - `objectType` (FM, TV, AM…)
  - `page`, `pageSize`
  - `selectedIds` (Zustand)
- Comandos:
  - “Selecionar Todos”: seleciona IDs da página atual
  - “Deselecionar Todos”: limpa seleção

**API (mínimo)**
- `GET /api/network/objects?type=FM&page=0&page_size=25`
  - retorna `{ items, total, page, page_size }`

---

### TELA C — Sidebar ampliada (com “Calcular Contornos” selecionado)
**Elementos visuais**
- Na sidebar aparecem itens adicionais:
  - Distância da Fronteira
  - Distância entre Canais
  - Porcentagem de Cobertura
  - Limitar Contorno Protegido
  - Relatório de Cobertura
  - Perfil do Terreno - ITM-1.2.2
  - Perfil do Terreno - ITU-452
  - Calcular Contornos (selecionado)
  - Calcular ITU-R P1546
  - Calcular Longley-Rice
  - Downlink (dBu)

**Interpretação**
- Isso indica que o módulo Rede possui **subfluxos avançados** que abrem páginas específicas (form + cálculo + mapa/relatório).

**Implementação (rotas internas do módulo)**
- `/app/network/contours` → Calcular Contornos
- `/app/network/p1546` → Calcular ITU-R P1546
- `/app/network/longley-rice` → Calcular Longley-Rice
- `/app/network/terrain-itm` → Perfil do Terreno ITM
- `/app/network/terrain-itu452` → Perfil do Terreno ITU-452
- `/app/network/border-distance` → Distância da Fronteira
- `/app/network/channel-distance` → Distância entre Canais
- `/app/network/coverage-percent` → Porcentagem de Cobertura
- `/app/network/limit-protected` → Limitar Contorno Protegido
- `/app/network/coverage-report` → Relatório de Cobertura
- `/app/network/downlink` → Downlink (dBu)

Cada item deve:
- validar seleção (ex.: “necessita 1 objeto selecionado” ou “pode usar múltiplos”)
- abrir página/modal e permitir execução + visualizar resultado

---

### TELA D — “Opções de Visualização” (map styling e camadas)
**Elementos visuais**
- Título: “Opções de Visualização”
- Tabela de parâmetros:
  - Fundo: Automático (dropdown)
  - Tamanho da Letra da Legenda: 16
- Tabela de camadas/objetos:
  - FM (Exibir ✓, Tipo Ponto, Cor, Largura, Legenda canal)
  - FM-Existente (Exibir, Tipo Ponto, Cor, Largura, Legenda tipo)
  - TV / TV-Existente / AM-Diurno / AM-Noturno / Box …
- Botão “Atualizar” (topo e base)

**Implementação**
- Rota: `/app/map/options` (ou modal dentro de `/app/map`)
- Página/Modal: `MapOptionsPage.tsx` ou `MapOptionsDialog.tsx`
- Estado persistido:
  - `mapStyle.backgroundMode` (auto, claro, escuro, satélite…)
  - `legendFontSize`
  - `layers[]`: `{ key, visible, geometryType, color, width, legendField }`
- Aplicação imediata:
  - ao clicar “Atualizar”, atualizar store + re-render do MapView

**API (opcional)**
- `GET /api/map/options` (carregar preferências do usuário)
- `PUT /api/map/options` (salvar preferências)

---

### TELA E — Mapa com círculo grande (raio/alcance) + marcador do objeto
**Elementos visuais**
- Base cartográfica (estradas/limites/água)
- Um **círculo verde** grande centrado no objeto
- Marcador com rótulo “239” (provável canal/ID)
- Um traço/linha azul vertical à esquerda (possível linha de referência, fronteira, radial, limite)

**Interpretação**
- Essa tela representa o Mapa exibindo:
  - objetos (pontos)
  - **buffer/círculo** (ex.: raio de busca, raio de coordenação, raio de interferência/viabilidade)
  - linhas/contornos auxiliares

**Implementação**
- Rota: `/app/map`
- Componente: `MapView.tsx`
- Camadas:
  - `ObjectsLayer` (markers com labels)
  - `CircleLayer` (Leaflet Circle)
  - `PolylineLayer` (linhas auxiliares)
- Controles:
  - toggles para ativar/desativar camadas

**API (mínimo)**
- `GET /api/network/objects?ids=...`
- (opcional) `GET /api/geo/buffers?...` se buffer for calculado no back

---

### TELA F — Mapa com dois círculos (verde + azul)
**Elementos visuais**
- Círculo verde menor + círculo azul maior
- Mesmo objeto central com label “239”
- Sugere comparação (ex.: contorno protegido vs contorno calculado, ou duas zonas)

**Implementação**
- Rota: `/app/map` (mesma página, camadas diferentes)
- Camadas adicionais:
  - `ContourLayer` (polígono/linha)
  - `ZonesLayer` (RNI: público/ocupacional)
- UI:
  - legenda e toggle por camada
  - tooltip com metadados ao clicar

---

### TELA G — “Contornos” (formulário/modal de cálculo)
**Elementos visuais**
- Título: “Contornos”
- Campos:
  - Tipo de Contorno: ITU-1546 (50:50)
  - Intensidade do Campo: 66 dBµV/m
  - Contornos Existentes: Preservar
  - Terreno: Automático
  - Legenda: (texto)
  - Cor: (seletor/campo com barra de cor)
- Botões: Ok | Limpar Contornos | Fechar

**Implementação**
- Acesso:
  - botão/ação “Calcular Contornos” (sidebar) abre esta tela
- Preferência: implementar como **Dialog** (modal) ou como página `/app/network/contours`
- Form:
  - RHF + Zod
  - validação: intensidade numérica; tipo/terreno enums; cor obrigatória
- Execução:
  - “Ok” → dispara job (contorno) e redireciona/atualiza mapa
  - “Limpar Contornos” → delete resultados da revisão
  - “Fechar” → fecha modal

**API (mínimo)**
- `POST /api/revisions/{revision_id}/run` `{ tasks:["contour"], params:{ type:"ITU1546_50_50", field_dbuvm:66, terrain:"auto" } }`
- `DELETE /api/revisions/{revision_id}/contour`
- `GET /api/revisions/{revision_id}/contour` (para renderizar no mapa)

---

### TELA H — Biblioteca/tabelas técnicas (listas longas com colunas e cores)
**Elementos visuais**
- Tabela com colunas “Name | Location | Origin | Color | Relative Permittivity …”
- Linhas com nomes técnicos (ex.: FR‑4, ferrite, gallium_arsenide, Neltec…)
- Aparência típica de “biblioteca/catálogo de itens”

**Interpretação no app**
- No fluxo Spectrum‑E, isso se traduz em um módulo “Banco de dados” para:
  - listar e selecionar **cadastros técnicos** (modelos, perfis, tabelas) que alimentam cálculos
  - cores indicam categoria/tipo/visibilidade

**Implementação**
- Rota: `/app/database`
- Página: `DatabaseTab.tsx` com subpáginas:
  - `/app/database/catalog` (lista)
  - `/app/database/item/:id` (detalhe/edição)
- Componentes:
  - tabela com filtros, busca, paginação
  - painel lateral de detalhe (opcional)
- API (mínimo)
  - `GET /api/db/catalog?kind=...&q=...`
  - `GET /api/db/catalog/{id}`

---

## 3) Layout pós-login (igual ao Spectrum‑E)

### 3.1 Topbar (Tabs)
- Fundo azul escuro
- Logo à esquerda
- Abas: Início | Banco de dados | Rede | Mapa
- Aba ativa com realce

### 3.2 Sidebar
- Altura total com scroll interno
- Título do módulo (ex.: “Gerenciamento da Rede”)
- Itens com:
  - hover
  - active state (fundo destacado)

### 3.3 Main
- Header de página (título + ações)
- Conteúdo (tabela/form/mapa)
- Logs/job status em painel colapsável (recomendado)

---

## 4) Implementação-base de cada função da sidebar (Rede)

> Observação: nomes abaixo seguem a sidebar que você mostrou.  
> O agente deve implementar **a base**: rota/diálogo, validação, chamada API, estados.

### (1) Adicionar/Ver/Editar Objeto
- Requisito: 0 selecionados → criar; 1 selecionado → editar; >1 → bloquear e sugerir bulk edit
- UI: `NetworkObjectForm.tsx` (Dialog com tabs)
- API: `POST /api/network/objects`, `PATCH /api/network/objects/{id}`, `GET /api/network/objects/{id}`

### (2) Modificar Objetos Selecionados
- UI: `BulkEditDialog.tsx`
- API: `PATCH /api/network/objects/bulk` `{ ids, patch }`

### (3) Deletar Objetos Selecionados
- UI: ConfirmDialog
- API: `DELETE /api/network/objects/bulk` `{ ids }`

### (4) Deletar Todos Objetos
- UI: ConfirmDialog com “digitar DELETE”
- API: `DELETE /api/network/objects?type=FM`

### (5) Mapear Objetos Selecionados
- UI: navega para `/app/map?ids=...`
- API: `GET /api/network/objects?ids=...`

### (6) Converter Objetos Selecionados
- UI: `ConvertDialog.tsx`
- API: `POST /api/projects/from-network` `{ ids, project_name, service_type }`

### (7) Ativar/Desativar
- UI: ação rápida (botão)
- API: bulk patch `{ onoff: 0|1 }`

### (8) Limpar contorno
- UI: ConfirmDialog
- API: `DELETE /api/revisions/{revision_id}/contour`

### (9) Importar Plano Básico
- UI: `ImportPlanDialog.tsx` (upload + job status)
- API: `POST /api/network/import-plan` (multipart) → `{ job_id }`

### (10) Ajustar ERP/HTx
- UI: `ErpHtxDialog.tsx` (preview + apply)
- API: `POST /api/network/erp-htx/preview`, `POST /api/network/erp-htx/apply`

### (11) Analisar Viabilidade
- UI: `ViabilityPage.tsx` (params → executar → PASS/FAIL)
- API: `POST /api/revisions/{revision_id}/run` `{ tasks:["interference"] }`
- API results: `GET /api/revisions/{revision_id}/interference`

### (12) Plotar Contorno
- UI: `ContourPage.tsx` (ou modal “Contornos”)
- API: `POST /api/revisions/{revision_id}/run` `{ tasks:["contour"] }`
- API results: `GET /api/revisions/{revision_id}/contour`

### (13) Analisar Instalação (RNI/OPEA)
- UI: `InstallationPage.tsx`
- API: run `{ tasks:["rni","opea"] }`

### (14) Calcular Deygout-Assis
- UI: `DeygoutPage.tsx` (seleciona radial → perfil + perdas)
- API: `POST /api/revisions/{revision_id}/calc/deygout`

### (15) Mapear Interferência
- UI: `InterferenceMapPage.tsx` (camadas de margem)
- API: `GET /api/revisions/{revision_id}/interference`
- (opcional tiles) `/api/revisions/{revision_id}/tiles/interference/{z}/{x}/{y}.png`

### (16) Buscar Canal
- UI: `ChannelSearchPage.tsx`
- API: `GET /api/channels/search?...`

### (17) Distância da Fronteira
- UI: `BorderDistancePage.tsx`
- API: `GET /api/geo/border-distance?lat=...&lon=...`

### (18) Distância entre Canais
- UI: `ChannelDistancePage.tsx`
- Base:
  - seleciona 1 ou 2 objetos
  - calcula Δf e classifica co/adj (apenas base)
- API: `GET /api/geo/channel-distance?id_a=...&id_b=...`

### (19) Porcentagem de Cobertura
- UI: `CoveragePercentPage.tsx`
- Base:
  - define polígono-alvo (município/área IBGE) e contorno calculado
  - retorna percentual de interseção
- API: `POST /api/revisions/{revision_id}/coverage/percent`

### (20) Limitar Contorno Protegido
- UI: `LimitProtectedContourPage.tsx`
- Base:
  - aplicar “clipping” do contorno a um limite (ex.: fronteira, bounding, área)
- API: `POST /api/revisions/{revision_id}/contour/limit`

### (21) Relatório de Cobertura
- UI: `CoverageReportPage.tsx`
- Base: gerar PDF do contorno + tabelas
- API: `POST /api/revisions/{revision_id}/export/report-pdf`

### (22) Perfil do Terreno - ITM-1.2.2
- UI: `TerrainITMPage.tsx`
- Base: mostra perfil (distância x altitude) e parâmetros
- API: `POST /api/revisions/{revision_id}/terrain/itm`

### (23) Perfil do Terreno - ITU-452
- UI: `TerrainITU452Page.tsx`
- Base: perfil + perdas por mecanismos (somente base/estrutura)
- API: `POST /api/revisions/{revision_id}/terrain/itu452`

### (24) Calcular Contornos
- UI: abre a “Tela G” (Contornos) e executa

### (25) Calcular ITU-R P1546
- UI: `P1546Page.tsx`
- Base:
  - define TX, RX/pontos e calcula E(d)
- API: `POST /api/revisions/{revision_id}/calc/p1546`

### (26) Calcular Longley-Rice
- UI: `LongleyRicePage.tsx`
- Base: parâmetros ITM/Irregular Terrain Model
- API: `POST /api/revisions/{revision_id}/calc/longley-rice`

### (27) Downlink (dBu)
- UI: `DownlinkPage.tsx`
- Base: conversões e modelagem simples de downlink (estrutura)
- API: `POST /api/rf/downlink`

---

## 5) Componente pronto: Home (Portal) elegante (usar os mesmos dados)

Arquivo sugerido: `src/app/pages/tabs/HomeTab.tsx`  
(Colar a implementação da Home que foi enviada na conversa — manter os mesmos textos/cards.)

---

## 6) Checklist do agente (aceitação)

- [ ] Login → redirect para `/app/home`
- [ ] `/app/home` mostra header + cards (iguais aos dados do screenshot), com layout moderno
- [ ] Topbar + Tabs funcionam
- [ ] `/app/network` replica o padrão: dropdown “Tipo de Objeto” + botões + tabela + seleção
- [ ] Sidebar do módulo Rede contém todos os itens (inclusive os avançados)
- [ ] Cada item abre **uma página/modal base** e realiza chamada API (mesmo que backend retorne stub)
- [ ] `/app/map` possui:
  - MapView
  - camadas (objetos, círculos, linhas, contorno)
  - Opções de Visualização (Tela D) para controlar estilo
- [ ] Terminar sessão com confirmação


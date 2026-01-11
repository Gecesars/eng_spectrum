# anatel.md – Blueprint de “Viabilidade Anatel” para o projeto Flask

Você é um agente de IA atuando em um projeto de engenharia de RF (Flask + PostgreSQL) para análise de cobertura de rádio/TV.  
Este documento descreve, passo a passo, como implementar **um novo módulo de “Viabilidade Anatel”** integrado à aplicação existente.

---

## 1. Contexto e objetivo

### 1.1. Objetivo geral

Criar um módulo completo de **análise de viabilidade técnica** (FM e TV Digital) baseado:

- nos **Planos Básicos da Anatel** (PBFM, PBTVD, etc.), que trazem para cada canal: serviço, município, canal, classe, coordenadas, ERP máxima, altura do sistema radiante e diagrama do contorno protegido de 5 em 5 graus;  
- nos **requisitos de contorno protegido e critérios de cobertura** (66 dBµV/m para FM, distâncias máximas por classe, uso de radiais de 5 graus com ERP e HAAT segundo ITU-R P.1546);  
- em **dados de elevação de terreno** obtidos de modelos digitais (ex.: ViewfinderPanoramas – "viewpano"), para cálculo de HAAT e perfis de terreno;
- em dados vetoriais (shapefiles) de municípios, setores censitários e estações, armazenados em `/anatel`.

O usuário, ao acessar a aplicação, deve poder:

1. Criar uma **nova análise de viabilidade** para um projeto de FM ou TV Digital.
2. Preencher **parâmetros técnicos** do projeto.
3. Visualizar um **mapa interativo (Folium)** centrado na localidade do projeto.
4. Na lateral direita do mapa, usar um painel de comandos para:
   - listar emissoras existentes da Anatel em um raio configurável;
   - marcar essas emissoras no mapa;
   - traçar o **contorno protegido** de cada estação conforme sua classe/canal;
   - opcionalmente, rodar checagens de interferência básica (distância, sobreposição de contornos).

Todos os dados de entrada e resultados devem ser persistidos em novas tabelas, **relacionadas ao usuário autenticado**.

---

## 2. Estrutura geral do módulo

### 2.1. Novo blueprint Flask

Criar um blueprint dedicado:

- Pacote: `app_core/viabilidade/`
- Arquivos principais:
  - `__init__.py`
  - `routes.py`
  - `models.py`
  - `services.py` (cálculos de viabilidade, integração com shapefiles e elevação)
  - `anatel_loader.py` (importação de shapefiles/planos básicos)
  - `terrain.py` (download e amostragem de dados de elevação)
- Templates:
  - `templates/viabilidade/index.html`
  - `templates/viabilidade/new_analysis.html`
  - `templates/viabilidade/mapa_viabilidade.html`
- Arquivo JS específico (separado do restante):
  - `static/js/viabilidade.js`

Registrar o blueprint em `app/__init__.py` (ou local equivalente), com prefixo:

```python
viabilidade_bp = Blueprint("viabilidade", __name__, url_prefix="/viabilidade")
```

---

## 3. Integração com o layout: `base.html`

### 3.1. Entrada no painel lateral

No arquivo `templates/base.html` (ou equivalente), no **painel lateral de comandos**, adicionar um item de menu estável:

- Se o painel for uma `<ul>` com links, acrescentar:

```html
<li>
  <a href="{{ url_for('viabilidade.index') }}">
    Viabilidade Anatel
  </a>
</li>
```

- Este item deve estar agrupado junto das funcionalidades de **rede/cobertura** (ex.: próximo de "Calcular Contornos", "Calcular ITU-R", etc.), similar ao comportamento observado nas telas de referência (Spectrum-E).

### 3.2. Conteúdo principal

Todas as páginas do módulo devem **estender `base.html`**, preenchendo blocos como `content` e reaproveitando o painel lateral.

---

## 4. Modelagem de dados (PostgreSQL + SQLAlchemy)

### 4.1. Tabela principal: `viabilidade_analise`

Criar uma tabela principal para armazenar cada projeto de viabilidade, com relação 1-N com `User`:

**Modelo sugerido (`models.py`):**

```python
class ViabilidadeAnalise(db.Model):
    __tablename__ = "viabilidade_analise"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Metadados
    nome_projeto = db.Column(db.String(150), nullable=False)
    servico = db.Column(db.Enum("FM", "TVD", name="servico_viab"), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    # Localização básica
    municipio = db.Column(db.String(120))
    uf = db.Column(db.String(2))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    # Parâmetros técnicos genéricos
    canal = db.Column(db.String(10))        # ex.: "201", "29"
    frequencia_mhz = db.Column(db.Float)    # útil para FM
    classe = db.Column(db.String(10))       # ex.: "E1", "B2", "Especial", "A", "B", "C"
    erp_kw = db.Column(db.Float)            # ERP máxima ou pretendida
    altura_antena_m = db.Column(db.Float)   # altura física em relação à base
    haat_m = db.Column(db.Float)            # HAAT calculado (opcional)
    polarizacao = db.Column(db.String(10))  # "H", "V", "Elíptica", etc.

    # Parâmetros adicionais (JSON para flexibilidade)
    parametros_json = db.Column(db.JSON, default={})

    # Resultados de viabilidade (resumo em JSON)
    resultado_json = db.Column(db.JSON, default={})

    owner = db.relationship("User", backref=db.backref("viabilidades", lazy="dynamic"))
```

Criar a migração correspondente usando Alembic/Migrate.

### 4.2. Tabela de emissoras Anatel (cache local)

Os Planos Básicos podem ser consumidos diretamente via shapefile, mas é mais eficiente ter uma camada em banco. Criar **tabelas de cache** para as estações da Anatel, uma para TV e outra para FM, ou uma tabela genérica com campo `servico`:

```python
class AnatelEstacao(db.Model):
    __tablename__ = "anatel_estacao"

    id = db.Column(db.Integer, primary_key=True)
    servico = db.Column(db.Enum("FM", "TVD", name="servico_anatel"), nullable=False)
    canal = db.Column(db.String(10))
    classe = db.Column(db.String(10))
    municipio = db.Column(db.String(120))
    uf = db.Column(db.String(2))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    erp_kw = db.Column(db.Float)
    altura_sistema_m = db.Column(db.Float)  # altura do centro geométrico do sistema radiante
    categoria = db.Column(db.String(20))    # Principal, Complementar, etc.

    # Contorno protegido de referência (opcional)
    # armazenar radial a radial ou um GeoJSON simplificado
    contorno_geojson = db.Column(db.JSON)
```

Essa tabela será alimentada por scripts de importação a partir dos arquivos da pasta `/anatel`.

### 4.3. Opcional: tabela de contornos por radial

Se você quiser guardar os contornos de forma regulatória (radiais de 5 graus):

```python
class AnatelContornoRadial(db.Model):
    __tablename__ = "anatel_contorno_radial"

    id = db.Column(db.Integer, primary_key=True)
    estacao_id = db.Column(db.Integer, db.ForeignKey("anatel_estacao.id"), nullable=False)
    azimute_graus = db.Column(db.Float, nullable=False)  # 0–355 em passos de 5 graus, iniciando no Norte Verdadeiro
    distancia_km = db.Column(db.Float, nullable=False)    # distância ao contorno protegido nessa radial

    estacao = db.relationship("AnatelEstacao", backref=db.backref("radiais", lazy="dynamic"))
```

---

## 5. Organização da pasta `/anatel`

Criar, na raiz do projeto (ou numa pasta de dados), a estrutura:

```text
/anatel/
    planos_basicos/
        PBFM.shp / .dbf / .shx / ...
        PBTVD.shp / .dbf / .shx / ...
    vetores_ibge/
        IBGE_Municipios.shp
        IBGE_Setores_Censitarios.shp
        IBGE_UF.shp
    dem/
        # tiles de elevação baixados do viewpano (*.hgt, *.tif, etc.)
```

Os shapefiles devem conter, pelo menos, os campos que the Anatel define: serviço, município/UF, canal, classe, coordenadas, ERP máxima, altura, categoria e, se disponível, parâmetros de contorno.  

---

## 6. Importação de dados da Anatel (`anatel_loader.py`)

### 6.1. Dependências

- `geopandas`
- `shapely`
- `pyproj` (se precisar de reprojeção)
- `sqlalchemy` / `psycopg2` (já existentes no projeto).

### 6.2. Script de importação

Implementar funções de alto nível:

```python
def importar_planos_basicos():
    """Lê os shapefiles da pasta /anatel/planos_basicos e popula AnatelEstacao."""
    importar_pbfm()
    importar_pbtvd()

def importar_pbfm():
    # ler PBFM.shp com geopandas
    # mapear colunas do shapefile -> campos de AnatelEstacao
    # criar/atualizar registros

def importar_pbtvd():
    # análogo ao FM, mas com serviço="TVD"
```

Para cada registro do shapefile:

- extrair `servico` (FM ou GTVD/RTVD), município, UF, canal, classe, coordenadas, ERP máxima, altura e categoria;  
- se houver contorno já em formato geométrico (ex.: coluna `geometry` com polígonos de contorno protegido), converter para GeoJSON simplificado e armazenar em `contorno_geojson`.

### 6.3. Job de atualização

Criar um comando CLI ou tarefa administrativa:

```bash
flask anatel import-planos-basicos
```

que chame `importar_planos_basicos()`.

---

## 7. Módulo de elevação de terreno (`terrain.py`)

### 7.1. Objetivo

Fornecer funções para:

- baixar tiles de elevação (DEM) na pasta `/anatel/dem/` usando fontes tipo **ViewfinderPanoramas** ("viewpano");
- amostrar o terreno ao longo de radiais (3–16 km a partir do transmissor, por exemplo) para cálculo de HAAT;  
- gerar perfis de terreno e um valor de HAAT médio por análise.

### 7.2. Funções principais

```python
def ensure_dem_for_bbox(bbox):
    """
    bbox = (min_lon, min_lat, max_lon, max_lat)
    Verifica quais tiles de elevação são necessários para cobrir a área
    e baixa-os para /anatel/dem/ se ainda não existirem.
    """

def sample_elevation(lat, lon):
    """
    Retorna a altitude em metros para o ponto (lat, lon),
    interpolando o DEM local.
    """

def compute_haat(lat_tx, lon_tx, h_antena_m, num_radiais=8):
    """
    Calcula o HAAT médio, amostrando o terreno entre 3 e 16 km em
    radiais igualmente espaçadas (0, 45, ..., 315 graus).
    Retorna o valor médio em metros e, opcionalmente, uma lista
    com HAAT por radial.
    """
```

O algoritmo de HAAT deve seguir o conceito regulatório: diferença entre a altura da antena (AMSL) e a elevação média do terreno nas radiais selecionadas.  

---

## 8. Cálculo de contornos protegidos (`services.py`)

### 8.1. Definições regulatórias

- **Contorno protegido**: lugar geométrico dos pontos em que a intensidade de campo atingir o valor especificado (ex.: 66 dBµV/m para FM).  
- Pontos são calculados em **radiais de 5 graus**, a partir das coordenadas da estação, usando ERP por radial e HAAT segundo ITU-R P.1546.  
- Quando não houver informação detalhada por radial, usar a **ERP máxima da classe** da estação e a distância máxima ao contorno protegida definida nas tabelas dos Atos da Anatel (FM e TV).  

### 8.2. Funções principais

```python
def compute_contorno_protegido(estacao, metodo="classe"):
    """
    Retorna um polígono (GeoJSON) com o contorno protegido da estação.

    estacao: instância de AnatelEstacao
    metodo:
        - "classe": usar distância máxima da classe para cada radial.
        - "p1546": calcular distância ponto-a-ponto com ITU-R P.1546, usando ERP e HAAT.
        - "shapefile": se o contorno já vier pronto do shapefile, apenas converte.
    """

def compute_contorno_projeto(analise):
    """
    Calcula o contorno protegido da estação PROPOSTA desta análise
    (usando servico, classe, ERP, HAAT calculado, etc.).
    """
```

Implementação mínima para começar:

- **Modo "classe"**:
  - obter a distância máxima permitida para a classe (FM ou TV Digital), a partir de uma tabela interna (derivada dos Atos).  
  - gerar radiais de 0 a 355 em passos de 5 graus;
  - para cada radial, usar a mesma distância máxima e construir os pontos (lat/lon) via geodésica;
  - formar o polígono.

- Posteriormente, é possível substituir por um cálculo mais refinado com ITU-R P.1546 + HAAT.

---

## 9. Rotas Flask e fluxo de uso

### 9.1. Lista de análises

`GET /viabilidade/` → `viabilidade.index`

- Exibe todas as análises pertencentes ao `current_user`.
- Botão "Nova Análise" → `/viabilidade/new`.

### 9.2. Criação de nova análise

`GET /viabilidade/new` → `viabilidade.new_analysis_form`

- Formulário dividido em seções:

  1. **Dados gerais**
     - Nome do projeto
     - Serviço: [FM] [TV Digital]
  2. **Localização**
     - Município (autocomplete opcional)
     - UF
     - Coordenadas (lat, lon) – campo de texto + botão "pegar do mapa" (opcional).
  3. **Parâmetros técnicos**
     - Canal
     - Frequência (FM)
     - Classe (lista baseada nas tabelas da Anatel – E1…C para FM; Especial/A/B/C para TV).  
     - ERP (kW)
     - Altura da antena (m)
     - Polarização
     - Campos adicionais: altura mínima da antena e relação frente/trás máxima, se quiser replicar a tela de "Ajuste de Altura e Potência". (esses valores podem ser guardados em `parametros_json`).

`POST /viabilidade/new` → `viabilidade.create_analysis`

- Valida o formulário.
- Cria um `ViabilidadeAnalise` vinculado ao `current_user`.
- Opcional: chama `compute_haat()` para preencher `haat_m`.
- Redireciona para `/viabilidade/<id>`.

### 9.3. Tela principal da análise (mapa + painel)

`GET /viabilidade/<int:analise_id>` → `viabilidade.view_analysis`

- Carrega a instância de `ViabilidadeAnalise`, garantindo que pertence ao `current_user`.
- Cria um `folium.Map` centrado nas coordenadas da análise:

```python
m = folium.Map(location=[analise.latitude, analise.longitude],
               zoom_start=10, control_scale=True)
```

- Adiciona um marcador da **estação proposta**.
- Renderiza o mapa Folium como HTML (ex.: `map_html = m._repr_html_()` ou via `m.get_root().render()`).
- Envia para o template `mapa_viabilidade.html`, junto com:
  - dados da análise (JSON);
  - endpoints para AJAX (`url_for('viabilidade.api_estacoes_raio', ...)`, etc.).

---

## 10. API para o painel de comandos (lado direito)

### 10.1. Endpoint: listar emissoras em raio

`GET /viabilidade/<int:analise_id>/estacoes`

Parâmetros de query:

- `servico` (FM/TVD ou "todos")
- `raio_km` (ex.: 50)

Lógica:

1. Carregar análise e coordenadas de referência.
2. Consultar `AnatelEstacao` filtrando por:
   - serviço escolhido;
   - distância geodésica entre (lat, lon) da análise e da estação <= `raio_km`.
3. Montar resposta JSON com:
   - `id`, `servico`, `canal`, `classe`, `municipio`, `uf`,
   - `latitude`, `longitude`, `erp_kw`, `altura_sistema_m`, `categoria`.

Esse endpoint será chamado via `viabilidade.js` quando o usuário clicar em "Listar emissoras no raio".

### 10.2. Endpoint: contornos protegidos

`GET /viabilidade/contornos`

Parâmetros:

- `analise_id` (opcional, para contorno da proposta)
- `estacoes_ids` (lista de IDs de `AnatelEstacao` separados por vírgula)

Lógica:

- Se `analise_id` presente: calcular contorno da **estação proposta** (`compute_contorno_projeto`).
- Para cada `estacoes_id`:
  - tentar usar `contorno_geojson` salvo;
  - se ausente, calcular com `compute_contorno_protegido`.
- Responder um GeoJSON com FeatureCollection:

```json
{
  "type": "FeatureCollection",
  "features": [
    { "type": "Feature", "properties": { ... }, "geometry": { ... } },
    ...
  ]
}
```

### 10.3. Endpoint: salvar resultado de viabilidade

`POST /viabilidade/<int:analise_id>/resultado`

- Recebe, via JSON, um resumo da análise calculado no front ou no backend (preferível no backend).
- Atualiza `resultado_json` na tabela `ViabilidadeAnalise`.

---

## 11. Comportamento do front-end (`viabilidade.js`)

### 11.1. Inicialização

Ao carregar `mapa_viabilidade.html`:

- Recuperar `map_html` (Folium já cuida do mapa base).
- Organizar o **painel lateral direito** como uma coluna fixa, contendo:

  1. Controles de raio (input numérico em km).
  2. Seleção de serviço (FM / TV / ambos).
  3. Botão "Listar emissoras".
  4. Lista de emissoras retornadas (tabela com checkbox).
  5. Botões:
     - "Traçar contornos das selecionadas".
     - "Traçar contorno da proposta".
     - "Limpar mapa".

### 11.2. Interação com o mapa

- Ao clicar em "Listar emissoras", o JS faz `fetch` para `/viabilidade/<id>/estacoes` e:
  - adiciona marcadores Folium/Leaflet para cada estação;
  - preenche a tabela a direita.

- Ao clicar em "Traçar contornos", o JS:
  - coleta os IDs marcados;
  - chama `/viabilidade/contornos` com esses IDs;
  - desenha polígonos no mapa com cores diferentes por serviço/classe.

- Opcional: tooltip com dados da estação ao passar o mouse.

---

## 12. Integração com critérios de cobertura (setores censitários)

Os requisitos de viabilidade da Anatel exigem que:

- pelo menos **50% da área dos setores censitários urbanos** do município de outorga esteja dentro do contorno de 66 dBµV/m (FM), ou
- alternativamente, 50% da população urbana do município esteja contida no contorno.  

Você pode, em uma segunda fase, reaproveitar a infraestrutura de **tiles + IBGE** descrita em `cursor.md` e `mod.md`:  

- intersectar o contorno da estação proposta com:
  - `IBGE_Setores_Censitarios.shp`;
  - ou com a grade de tiles em dBµV/m já calculada;
- calcular:
  - percentual de setores censitários urbanos cobertos;
  - população urbana coberta (via API IBGE + códigos dos setores/municípios).

O resultado pode ser armazenado em `resultado_json` para alimentar relatórios regulatórios.

---

## 13. Segurança, permissões e UX

- Todas as rotas do blueprint `viabilidade` devem exigir usuário autenticado.
- Uma análise só pode ser lida/alterada pelo **dono** (`user_id`) ou por administradores.
- Em caso de falhas (ex.: shapefile ausente, erro ao baixar DEM, etc.):
  - registrar logs detalhados;
  - retornar mensagens amigáveis (sem stack traces) para o usuário.

---

## 14. Testes e documentação

### 14.1. Testes

Criar testes mínimos para:

1. Importação de Planos Básicos:
   - conferir que PBFM/PBTVD são lidos e armazenados em `AnatelEstacao`.
2. Cálculo de contorno:
   - dado um ponto, classe e distância por classe, conferir que o polígono tem 72 pontos (360/5) e fecha corretamente.
3. API de emissoras em raio:
   - com estações artificiais, garantir que apenas as dentro do raio retornem.
4. API de contornos:
   - garantir que o GeoJSON gerado é válido.

### 14.2. Documentação

Adicionar uma seção no README ou documentação da aplicação explicando:

- o que é a funcionalidade "Viabilidade Anatel";
- quais arquivos precisam existir em `/anatel` (PBFM, PBTVD, vetores IBGE, DEM);
- comandos CLI para importar dados;
- principais endpoints e fluxos de uso.

---

## 15. Entrega esperada do agente de IA

Ao aplicar estas instruções ao código real do projeto, você deve:

1. Criar o blueprint `viabilidade` com as rotas descritas.
2. Criar as novas tabelas (`viabilidade_analise`, `anatel_estacao`, opcionalmente `anatel_contorno_radial`) e as migrações.
3. Implementar:
   - importação dos Planos Básicos a partir de `/anatel/planos_basicos`;
   - módulo de elevação e cálculo de HAAT em `/anatel/dem`;
   - funções de cálculo de contornos protegidos;
   - endpoints REST de listagem de estações e contornos.
4. Integrar o item "Viabilidade Anatel" no painel lateral de `base.html`.
5. Implementar as páginas HTML e o JS de interação (mapa Folium + painel direito).
6. Garantir que tudo esteja versionado, documentado e integrado ao fluxo de autenticação já existente.

Seguindo este blueprint, o sistema passará a oferecer uma ferramenta completa de **viabilidade regulatória** alinhada aos requisitos técnicos da Anatel para FM e TV Digital.

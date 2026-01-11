# Engenharia de Espectro

Aplicação inicial baseada no `codex-1.md`, com backend Flask (PostgreSQL/PostGIS + Celery/Redis) e frontend estático.

## Como rodar localmente

```bash
# ativar venv
source .venv/bin/activate

# aplicar migrações
PYTHONPATH=backend flask --app backend/run.py db upgrade

# subir API
python backend/run.py
```

Acesse: `http://localhost:8000`

## Serviços (systemd)

O serviço ativo é `eng_spec.service`.

```bash
sudo systemctl status eng_spec.service
```

## CLI administrativa

```bash
PYTHONPATH=backend flask --app backend/run.py engspec list-users
PYTHONPATH=backend flask --app backend/run.py engspec create-user --email user@example.com --password 123456 --verified
PYTHONPATH=backend flask --app backend/run.py engspec import-anatel --truncate --source /home/atx/eng_spectrum/anatel/plano_basicoTVFM.xml
PYTHONPATH=backend flask --app backend/run.py engspec import-aerodromes --truncate --source /home/atx/eng_spectrum/anatel/aerodromos_brasil_v6.json
```

## Estrutura

- `backend/` API Flask + tarefas
- `frontend/` Landing + Auth + Dashboard
- `migrations/` Alembic

## Observações

- Tokens de confirmação são retornados pela API no MVP.
- Celery está em modo eager por padrão (`CELERY_TASK_ALWAYS_EAGER=true`).

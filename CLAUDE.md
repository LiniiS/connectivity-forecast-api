# CLAUDE.md

Guia para quem for alterar esta API (incluindo assistentes de código).

## Objetivo

API FastAPI educacional que lê predições já geradas por vários grupos e as expõe em REST para aplicativos mobile.

Não consultar RIPE Atlas. Não treinar nem executar modelo. Não persistir em banco nesta versão.

## Separação obrigatória

```text
RIPE Atlas     → medições observadas
Modelos A/B/C/D → previsões futuras (mesmo contrato, origens diferentes)
Backend        → interpreta e disponibiliza
Mobile         → escolhe model_id e usa a previsão
```

Nunca atribua ao RIPE Atlas campos `PREDICTED` ou `BUSINESS`.
Nunca atribua ao modelo `quality`, `quality_score` ou `recommendation`.
Nunca execute algoritmo de ML nesta API. `algorithm` no catálogo é só metadata.

## Arquitetura

```text
Route → Service → ModelRepository → JsonModelRepository → models.json
               → PredictionRepository → CsvPredictionRepository → CSV
```

Rotas não leem arquivo. Novo grupo = entrada em `models.json` + linhas no CSV. Sem rota nova.

Todos os modelos usam o mesmo `QualityClassifier` e o mesmo `RecommendationService`.

Não hardcode `model-a` como padrão. `DEFAULT_MODEL_ID` existe na config e não é aplicado nas rotas.

## Validação CSV × catálogo

Linha com `model_id` ausente de `models.json`: warning no log e linha ignorada.
Dataset vazio depois disso: falha de inicialização `DATASET_UNAVAILABLE`.

## Dataset mockado

`data/mock_predictions.csv`: 4 modelos × 10 probes × 24 horas (960 linhas), mesmos `probe_id`+`prediction_for`.
`data/models.json` inclui `model-inactive` para testes; ele não entra em `GET /models`.

Regenerar:

```bash
python scripts/generate_mock_predictions.py
```

## Comandos

```bash
pip install -r requirements.txt
pytest
uvicorn app.main:app --reload
```

Render start command:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Fora de escopo

Integração RIPE ao vivo, ML, PostgreSQL/SQLite, autenticação, WebSockets, jobs, frontend, versionamento complexo de modelos.

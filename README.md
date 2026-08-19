# Internet Quality API

API REST educacional que entrega previsões de qualidade de conexão para aplicativos mobile.

Ela existe para **desacoplar** duas disciplinas:

```text
RIPE Atlas
      ↓
dados históricos
      ↓
────────────────────────────────
      ↓
Model A → predictions
Model B → predictions
Model C → predictions
Model D → predictions
      ↓
────────────────────────────────
      ↓
API FastAPI  ← este repositório
      ↓
seleção de model_id
      ↓
Aplicativos Mobile
```

- A disciplina de **Estruturas de Dados / Ciência de Dados** produz um arquivo de predições **por grupo**, todos no mesmo contrato.
- A disciplina de **Dispositivos Móveis** consome **somente** esta API e escolhe o modelo via `model_id`.
- Esta API **não** consulta o RIPE Atlas e **não** executa nenhum modelo preditivo.

Enquanto os modelos reais não existirem, a API lê `data/models.json` e `data/mock_predictions.csv`.  
Quando houver saídas reais, aponte `PREDICTIONS_FILE` para `data/predictions.csv` e cadastre os grupos em `data/models.json`. Os endpoints REST permanecem iguais.

## Visão geral

| Camada | Responsabilidade |
| --- | --- |
| RIPE Atlas | Medições observadas (ping `avg`, `sent`, `rcvd`, metadados da probe) |
| Modelo | Prever `predicted_avg_rtt_ms` e `predicted_packet_loss_pct` (cada grupo, mesmo contrato) |
| Backend (esta API) | Ler predições, classificar qualidade, gerar recomendação, expor REST |
| Mobile | Planejar atividades com base na previsão |

As categorias `GOOD` / `MODERATE` / `UNSTABLE` são **regras de negócio experimentais do projeto**. Não são classificações fornecidas pelo RIPE Atlas.

Os identificadores, coordenadas e ASNs do dataset inicial são **mockados**. O que é real nesta versão é o **schema e o significado dos campos**, não os valores de teste.

As coordenadas públicas de probes RIPE Atlas recebem proteção de privacidade. A aplicação **não** deve afirmar que a localização da probe é a localização exata do usuário.

## Endpoints

| Método | Caminho | Descrição |
| --- | --- | --- |
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/models` | Modelos ativos (ponto inicial do app) |
| `GET` | `/api/v1/models/{model_id}` | Detalhe de um modelo |
| `GET` | `/api/v1/locations` | Probes com predição disponível |
| `GET` | `/api/v1/forecasts/probes/{probe_id}?model_id=` | Previsão futura mais próxima daquele modelo |
| `GET` | `/api/v1/forecasts/probes/{probe_id}/timeline?model_id=` | Série temporal daquele modelo |
| `GET` | `/api/v1/forecasts/probes/{probe_id}/compare` | Comparar modelos ativos (sem eleger vencedor) |
| `GET` | `/api/v1/forecasts/nearby?lat=&lon=&model_id=` | Previsão da probe mais próxima, naquele modelo |
| `POST` | `/api/v1/activity/check` | Adequação experimental de uma atividade |

Documentação interativa: [`/docs`](http://127.0.0.1:8000/docs)

Guia para a disciplina mobile: [`docs/STUDENT_API_GUIDE.md`](docs/STUDENT_API_GUIDE.md)  
Contrato para a equipe do modelo: [`docs/PREDICTION_MODEL_CONTRACT.md`](docs/PREDICTION_MODEL_CONTRACT.md)

## Executar localmente

Requisito: Python 3.12.

### Windows (PowerShell)

O PowerShell do Windows costuma bloquear `Activate.ps1`. Libere scripts **só nesta janela** e ative a venv:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Se `python` não for reconhecido, use o executável da venv (não precisa ativar):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

A API sobe em `http://127.0.0.1:8000`. A raiz redireciona para `/docs`.

### Variáveis de ambiente

| Variável | Padrão | Função |
| --- | --- | --- |
| `PREDICTIONS_FILE` | `data/mock_predictions.csv` | Caminho do arquivo de predições |
| `MODELS_FILE` | `data/models.json` | Catálogo de modelos |
| `DEFAULT_MODEL_ID` | (vazio) | Reservado. Não é usado nas rotas nesta versão |
| `ALLOWED_ORIGINS` | `*` | Origens CORS, separadas por vírgula |
| `LOG_LEVEL` | `INFO` | Nível de log |

Para usar o arquivo real no futuro:

```bash
set PREDICTIONS_FILE=data/predictions.csv
```

Nenhuma rota precisa mudar.

## Testes

```bash
pytest
```

## Swagger

Com a API em execução:

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

No schema, cada campo relevante indica a origem:

- `SOURCE`
- `DERIVED`
- `PREDICTED`
- `BUSINESS`

## Deploy no Render

A API está pronta para um **Web Service** Python.

1. Publique este repositório no GitHub.
2. No [Render](https://render.com), crie um **Web Service** apontando para o repositório.
3. Runtime: Python.
4. **Build Command:**

   ```text
   pip install -r requirements.txt
   ```

5. **Start Command:**

   ```text
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

   O `$PORT` é obrigatório. O Render injeta essa variável.

6. Health check path: `/api/v1/health`
7. Variáveis de ambiente recomendadas:

   | Key | Value |
   | --- | --- |
   | `PYTHON_VERSION` | `3.12.10` |
   | `PREDICTIONS_FILE` | `data/mock_predictions.csv` |
   | `MODELS_FILE` | `data/models.json` |
   | `ALLOWED_ORIGINS` | `*` (ou as origens dos apps dos estudantes, separadas por vírgula) |

Também existe um `render.yaml` na raiz, que pode ser usado como Blueprint.

Esta versão **não** usa SQLite, PostgreSQL nem qualquer banco. A fonte de dados é um CSV somente leitura.

Após o deploy, o Swagger fica em:

```text
https://<seu-servico>.onrender.com/docs
```

## Multiple Prediction Models

Vários grupos entregam previsões no **mesmo contrato**. A API só armazena, identifica, filtra, compara e expõe. Nenhum algoritmo é executado aqui.

```text
                   predictions
                       │
        ┌──────────────┼──────────────┐
        │              │              │
     Model A         Model B        Model C
        │              │              │
        └──────────────┼──────────────┘
                       │
                     API
                       │
                 model_id
                       │
                     Mobile
```

`GET /api/v1/models` é o ponto inicial de integração. O app lista os modelos ativos, o usuário escolhe um `id`, e todas as previsões seguintes enviam esse `model_id`.

Não há modelo padrão implícito no código. `DEFAULT_MODEL_ID` existe só como configuração futura e **não** é aplicada nas rotas desta versão.

A seleção existe para observar abordagens diferentes, comparar resultados e desacoplar o app do algoritmo. **Não** use a API para declarar automaticamente qual modelo é cientificamente superior — isso pertence à disciplina dos modelos.

Todos os modelos passam pelo mesmo `QualityClassifier` e pelo mesmo `RecommendationService`.

Para incluir um **Grupo 5 / Model E** no futuro:

1. cadastre o modelo em `data/models.json`;
2. acrescente as linhas dele no CSV.

Não é necessária nova rota, novo service nem nova versão do aplicativo.

### Exemplo completo de uso

1. Obter modelos: `GET /api/v1/models`
2. Selecionar `model-b`
3. Consultar: `GET /api/v1/forecasts/nearby?lat=-23.55&lon=-46.63&model_id=model-b`
4. Exibir qualidade, RTT e perda do Modelo B
5. Trocar para Modelo C
6. Nova consulta com `model_id=model-c`

### Validação do CSV contra o catálogo

Se uma linha de predição tiver `model_id` que **não** existe em `models.json`, a API **registra um warning no log e ignora a linha**. Não silencia a inconsistência e não serve previsão órfã. Se, depois disso, o dataset ficar vazio, a inicialização falha com `DATASET_UNAVAILABLE`.

## Contrato do modelo

O modelo deve prever, para um instante futuro:

| Campo | Significado |
| --- | --- |
| `predicted_avg_rtt_ms` | Previsão futura da métrica cuja observação histórica no RIPE Atlas é o campo de ping `avg` |
| `predicted_packet_loss_pct` | Previsão futura da métrica histórica **derivada** de `sent` e `rcvd` |

Packet loss **não** é um campo original do RIPE Atlas neste projeto. Ele é calculado assim, quando `sent > 0`:

```text
packet_loss_pct = ((sent - rcvd) / sent) * 100
```

O modelo **não** precisa produzir `quality`, `quality_score` nem `recommendation`. Esses campos são regras de negócio do backend.

Detalhes do arquivo esperado: [`docs/PREDICTION_MODEL_CONTRACT.md`](docs/PREDICTION_MODEL_CONTRACT.md)

## Origem dos dados

### RIPE Atlas field mapping

| Nosso campo | RIPE | Tipo |
| --- | --- | --- |
| `probe_id` | `prb_id` / `probe.id` | SOURCE |
| `model_id` / `model_version` | catálogo do grupo | PREDICTED |
| `measurement_id` | `msm_id` | SOURCE |
| `country_code` | `probe.country_code` | SOURCE |
| `asn_v4` | `probe.asn_v4` | SOURCE |
| `asn_v6` | `probe.asn_v6` | SOURCE |
| `latitude` / `longitude` | `probe.geometry.coordinates` | SOURCE |
| `observed_avg_rtt_ms` | `avg` | SOURCE |
| `packet_loss_pct` | `sent` + `rcvd` | DERIVED |
| `predicted_avg_rtt_ms` | modelo | PREDICTED |
| `predicted_packet_loss_pct` | modelo | PREDICTED |
| `model_confidence` | modelo | PREDICTED |
| `quality` | backend | BUSINESS |
| `quality_score` | backend | BUSINESS |
| `recommendation` | backend | BUSINESS |

GeoJSON de uma probe RIPE Atlas usa `[longitude, latitude]`. Esta API expõe os dois valores em campos nomeados e **não inverte** a ordem ao ler `geometry.coordinates`.

Campos RIPE que **não** são expostos (mesmo que existam na plataforma):

- `src_addr`
- `from`
- `address_v4`
- `address_v6`
- `prefix_v4`
- `prefix_v6`

### O que o backend adiciona

`QualityClassifier` transforma `predicted_avg_rtt_ms` + `predicted_packet_loss_pct` em `quality` e `quality_score`.

`RecommendationService` transforma a qualidade em `{ "code", "message" }`.

Os limiares estão em `app/config/quality_rules.py` e `app/config/activity_rules.py`. São regras configuráveis do **protótipo**, não padrões científicos universais.

## Dataset mockado

O arquivo `data/mock_predictions.csv` contém 4 modelos ativos × 10 probes × 24 horários (**960 linhas**). As combinações `probe_id` + `prediction_for` são as mesmas para todos os modelos; só os valores previstos mudam. `data/models.json` lista esses modelos (e um modelo inativo de catálogo).

Essas probes **não** são probes RIPE Atlas reais. IDs, ASNs, `measurement_id` e coordenadas são inventados para desenvolvimento. Os nomes de algoritmo no catálogo são metadata fictícia.

Essas probes **não** são probes RIPE Atlas reais. IDs, ASNs, `measurement_id` e coordenadas são inventados para desenvolvimento.

Para regenerar o CSV:

```bash
python scripts/generate_mock_predictions.py
```

## Arquitetura interna

```text
Route
 ↓
Service (ModelService / ForecastService / ...)
 ↓
ModelRepository  →  JsonModelRepository  →  models.json
PredictionRepository  →  CsvPredictionRepository  →  CSV
```

Os endpoints nunca leem o CSV diretamente. Uma futura `PostgresPredictionRepository` pode substituir a implementação sem alterar o contrato REST.

## Fora de escopo desta versão

- Integração online com RIPE Atlas
- Treinamento / `model.predict()`
- PostgreSQL / SQLite
- Autenticação
- WebSockets, jobs, dashboard ou frontend

# Guia da API para estudantes de Dispositivos Móveis

Este documento descreve **somente** o que o aplicativo precisa para consumir a API.

Você **não** precisa conhecer RIPE Atlas, modelo preditivo, arquivos CSV ou a implementação do servidor.

A API devolve JSON. Datas estão em ISO-8601 UTC, com sufixo `Z`. Exemplo: `2026-08-20T19:00:00Z`.

## Base URL

Local:

```text
http://127.0.0.1:8000
```

Produção (substitua pelo endereço publicado no Render):

```text
https://<seu-servico>.onrender.com
```

Swagger (interface clicável):

```text
{BASE_URL}/docs
```

Todos os endpoints usam o prefixo `/api/v1`.

Nesta versão **não há autenticação**.

---

## Choosing a prediction model

Vários grupos produzem previsões. O aplicativo **escolhe um modelo** e pede só as previsões daquele modelo.

Você não precisa saber o algoritmo, a biblioteca de ML nem os hiperparâmetros. Use apenas:

- `id` (guarde como `selectedModelId`)
- `name`
- `version`
- as previsões devolvidas depois

Fluxo:

```text
1. GET /api/v1/models
2. usuário escolhe um modelo
3. aplicativo guarda modelId (persistência local)
4. chamadas seguintes enviam model_id
5. API retorna a previsão daquele modelo
```

Tela sugerida:

```text
Modelo de previsão

○ Modelo A
○ Modelo B
○ Modelo C
○ Modelo D
```

Depois da seleção:

```text
Modelo B selecionado
        ↓
GET /forecasts/nearby?...&model_id=model-b
```

A API **não** guarda a escolha do usuário. Persista `selectedModelId` no aparelho (SharedPreferences, DataStore, UserDefaults, etc.) para reabrir o app com o mesmo modelo.

Não apresente a lista como ranking científico. A troca de modelo serve para comparar abordagens, não para a API dizer qual é o melhor.

### Fluxo esperado no aplicativo

```text
App inicia
    ↓
GET /models
    ↓
exibe lista
    ↓
usuário seleciona Modelo B
    ↓
salva selectedModelId = "model-b"
    ↓
obtém localização
    ↓
GET /forecasts/nearby
    ?lat=...
    &lon=...
    &model_id=model-b
    ↓
mostra previsão
```

Exemplo de exibição:

```text
Modelo B

Qualidade esperada:
MODERATE

RTT previsto:
78 ms

Perda prevista:
2.2%
```

Ao trocar para Modelo C, só mude `model_id`. O restante do app permanece igual.

---

## Endpoints

### 1. Health

Confirma que a API está no ar.

```http
GET /api/v1/health
```

**Resposta 200**

```json
{
  "status": "ok",
  "service": "internet-quality-api"
}
```

```bash
curl http://127.0.0.1:8000/api/v1/health
```

Use este endpoint para detectar falta de conexão ou API fora do ar. Se a chamada falhar por rede, mostre uma mensagem local no aplicativo. Não dependa só do JSON de erro.

---

### 2. Listar modelos

```http
GET /api/v1/models
```

Devolve somente modelos **ativos**, ordenados por nome.

```json
{
  "items": [
    {
      "id": "model-a",
      "name": "Modelo A",
      "description": "Modelo desenvolvido pelo Grupo 1.",
      "groupName": "Grupo 1",
      "algorithm": "Linear Regression",
      "version": "1.0"
    }
  ],
  "total": 4
}
```

```bash
curl http://127.0.0.1:8000/api/v1/models
```

Copie o `id` escolhido e use como `model_id` nas outras chamadas.

```http
GET /api/v1/models/model-a
```

Modelo inexistente: **404** `MODEL_NOT_FOUND`.

---

### 3. Locais disponíveis

Lista as probes/localizações que possuem previsão.

```http
GET /api/v1/locations
```

**Resposta 200**

```json
{
  "items": [
    {
      "probeId": 900001,
      "countryCode": "BR",
      "asnV4": 28573,
      "asnV6": null,
      "location": {
        "latitude": -23.5505,
        "longitude": -46.6333
      }
    }
  ],
  "total": 10
}
```

```bash
curl http://127.0.0.1:8000/api/v1/locations
```

---

### 4. Previsão por probe

Devolve a previsão futura mais próxima da probe **para o modelo escolhido**.

```http
GET /api/v1/forecasts/probes/{probeId}?model_id=model-a
```

`model_id` é obrigatório.

**Resposta 200**

```json
{
  "model": {
    "id": "model-a",
    "name": "Modelo A",
    "version": "1.0"
  },
  "probeId": 900001,
  "location": {
    "latitude": -23.5505,
    "longitude": -46.6333,
    "countryCode": "BR"
  },
  "prediction": {
    "predictionFor": "2026-08-20T19:00:00Z",
    "predictedAvgRttMs": 71.4,
    "predictedPacketLossPct": 1.5,
    "modelConfidence": 0.82
  },
  "assessment": {
    "quality": "MODERATE",
    "qualityScore": 68
  },
  "recommendation": {
    "code": "REDUCE_NETWORK_USAGE",
    "message": "A conexão pode apresentar alguma instabilidade neste período."
  }
}
```

Os valores numéricos do exemplo são ilustrativos.

```bash
curl "http://127.0.0.1:8000/api/v1/forecasts/probes/900001?model_id=model-a"
```

**Erro 404** se a probe não existir:

```json
{
  "error": {
    "code": "PROBE_NOT_FOUND",
    "message": "No prediction data was found for the requested probe."
  }
}
```

---

### 5. Timeline

Série de previsões da probe **daquele modelo**, já ordenada por horário.

```http
GET /api/v1/forecasts/probes/{probeId}/timeline?model_id=model-c
```

| Parâmetro | Obrigatório | Descrição |
| --- | --- | --- |
| `model_id` | sim | Modelo escolhido pelo usuário |
| `from` | não | Início UTC (ISO-8601) |
| `to` | não | Fim UTC (ISO-8601) |
| `limit` | não | Quantidade máxima (1 a 100, padrão 24) |

**Resposta 200**

```json
{
  "probeId": 900001,
  "items": [
    {
      "predictionFor": "2026-08-20T18:00:00Z",
      "predictedAvgRttMs": 42.1,
      "predictedPacketLossPct": 0.3,
      "quality": "GOOD",
      "qualityScore": 88
    },
    {
      "predictionFor": "2026-08-20T19:00:00Z",
      "predictedAvgRttMs": 71.4,
      "predictedPacketLossPct": 1.5,
      "quality": "MODERATE",
      "qualityScore": 68
    }
  ]
}
```

```bash
curl "http://127.0.0.1:8000/api/v1/forecasts/probes/900001/timeline?model_id=model-c&limit=24"
```

---

### 6. Previsão perto do usuário

Encontre a probe disponível mais próxima das coordenadas do aparelho.

```http
GET /api/v1/forecasts/nearby
```

| Parâmetro | Obrigatório | Descrição |
| --- | --- | --- |
| `lat` | sim | Latitude (-90 a 90) |
| `lon` | sim | Longitude (-180 a 180) |
| `model_id` | sim | Modelo escolhido pelo usuário |
| `radius_km` | não | Raio máximo em km |

**Resposta 200**

```json
{
  "model": {
    "id": "model-b",
    "name": "Modelo B",
    "version": "1.0"
  },
  "requestedLocation": {
    "latitude": -23.551,
    "longitude": -46.634
  },
  "matchedProbe": {
    "probeId": 900001,
    "distanceKm": 0.2
  },
  "prediction": {
    "predictionFor": "2026-08-20T19:00:00Z",
    "predictedAvgRttMs": 71.4,
    "predictedPacketLossPct": 1.5
  },
  "assessment": {
    "quality": "MODERATE",
    "qualityScore": 68
  },
  "recommendation": {
    "code": "REDUCE_NETWORK_USAGE",
    "message": "A conexão pode apresentar alguma instabilidade neste período."
  },
  "metadata": {
    "disclaimer": "A previsão está associada à probe RIPE Atlas selecionada como referência geográfica e não representa uma medição direta do dispositivo do usuário.",
    "locationPrivacy": "As coordenadas públicas das probes recebem proteção de privacidade do RIPE Atlas e não devem ser tratadas como a localização exata do usuário."
  }
}
```

```bash
curl "http://127.0.0.1:8000/api/v1/forecasts/nearby?lat=-23.551&lon=-46.634&model_id=model-b"
```

Mostre o `metadata.disclaimer` no aplicativo (ou um texto equivalente). **Não** diga ao usuário que aquela é a qualidade exata da rede dele.

Latitude `100` ou longitude `200` devolvem **422**.

Se `radius_km` for informado e não houver probe no raio:

```json
{
  "error": {
    "code": "NO_PROBE_IN_RANGE",
    "message": "No probe with prediction data was found within the requested radius."
  }
}
```

---

### 7. Verificar atividade

Combina previsão + tipo de atividade e devolve se o período parece adequado.

```http
POST /api/v1/activity/check
Content-Type: application/json
```

**Body**

```json
{
  "modelId": "model-a",
  "latitude": -23.55,
  "longitude": -46.63,
  "dateTime": "2026-08-20T19:00:00Z",
  "activity": "VIDEO_CALL"
}
```

Atividades aceitas:

- `VIDEO_CALL`
- `AUDIO_CALL`
- `STREAMING`
- `FILE_UPLOAD`
- `WEB_BROWSING`
- `MESSAGING`

**Resposta 200**

```json
{
  "model": {
    "id": "model-a",
    "name": "Modelo A",
    "version": "1.0"
  },
  "activity": "VIDEO_CALL",
  "suitable": false,
  "forecast": {
    "quality": "UNSTABLE",
    "predictedAvgRttMs": 185.2,
    "predictedPacketLossPct": 8.1
  },
  "recommendation": {
    "code": "PREPARE_OFFLINE",
    "message": "Há risco de instabilidade para uma chamada de vídeo neste período."
  },
  "metadata": {
    "disclaimer": "A previsão está associada à probe RIPE Atlas selecionada como referência geográfica e não representa uma medição direta do dispositivo do usuário.",
    "locationPrivacy": "As coordenadas públicas das probes recebem proteção de privacidade do RIPE Atlas e não devem ser tratadas como a localização exata do usuário."
  }
}
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/activity/check ^
  -H "Content-Type: application/json" ^
  -d "{\"modelId\":\"model-a\",\"latitude\":-3.119,\"longitude\":-60.0217,\"dateTime\":\"2026-08-20T19:00:00Z\",\"activity\":\"VIDEO_CALL\"}"
```

Em Linux/macOS:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/activity/check \
  -H "Content-Type: application/json" \
  -d '{"modelId":"model-a","latitude":-3.119,"longitude":-60.0217,"dateTime":"2026-08-20T19:00:00Z","activity":"VIDEO_CALL"}'
```

---

### 8. Comparar modelos (opcional)

Útil para uma tela pedagógica. Não declare um vencedor.

```http
GET /api/v1/forecasts/probes/900001/compare?prediction_for=2026-08-20T19:00:00Z
```

```bash
curl "http://127.0.0.1:8000/api/v1/forecasts/probes/900001/compare?prediction_for=2026-08-20T19:00:00Z"
```

---

## Campos que o app deve usar

### Qualidade

| `quality` | Significado para a UI |
| --- | --- |
| `GOOD` | Conexão prevista adequada |
| `MODERATE` | Pode haver instabilidade |
| `UNSTABLE` | Considere recursos offline |

`qualityScore` é um número de 0 a 100, útil para uma barra ou cor. Não precisa ser exibido.

### Recomendação

Use o **código**, não o texto, para lógica do aplicativo:

| `code` | Sugestão de UI |
| --- | --- |
| `NORMAL_USE` | Uso normal |
| `REDUCE_NETWORK_USAGE` | Reduzir uso de rede / avisar oscilação |
| `PREPARE_OFFLINE` | Preparar conteúdo offline |

`message` é um texto pronto para mostrar. Ele pode mudar; o `code` é estável.

### Previsão numérica

| Campo JSON | O que é |
| --- | --- |
| `predictedAvgRttMs` | RTT médio previsto, em milissegundos |
| `predictedPacketLossPct` | Perda de pacotes prevista, em % |
| `predictionFor` | Horário UTC ao qual a previsão se refere |
| `modelConfidence` | Confiança opcional de 0 a 1; pode ser `null` |

---

## Erros

Todas as falhas de negócio seguem:

```json
{
  "error": {
    "code": "PROBE_NOT_FOUND",
    "message": "No prediction data was found for the requested probe."
  }
}
```

| HTTP | `error.code` | Quando |
| --- | --- | --- |
| 400 | `INVALID_TIME_RANGE` | `from` posterior a `to` |
| 404 | `MODEL_NOT_FOUND` | `model_id` desconhecido |
| 404 | `MODEL_INACTIVE` | modelo cadastrado mas inativo |
| 404 | `PROBE_NOT_FOUND` | Probe sem dados daquele modelo |
| 404 | `NO_PROBE_IN_RANGE` | Nenhuma probe no raio |
| 404 | `NO_COMMON_PREDICTION` | Compare sem instante comum |
| 422 | `VALIDATION_ERROR` | Parâmetro inválido ou `model_id` ausente |
| 500 | `DATASET_UNAVAILABLE` | Dataset do servidor indisponível |
| 500 | `INTERNAL_ERROR` | Erro inesperado |

Validação 422 pode incluir `error.details` com o campo inválido.

Trate também o caso **sem HTTP**: timeout, DNS, modo avião. Isso não vem como JSON.

---

## Tutorial mínimo do aplicativo

1. **Chamar** `GET /api/v1/models` e montar a lista (Modelo A, Modelo B, ...).
2. **Guardar** o `id` escolhido em persistência local (`selectedModelId`).
3. **Obter localização** do aparelho (`lat`, `lon`), com permissão do usuário.
4. **Chamar** `GET /api/v1/forecasts/nearby?lat=...&lon=...&model_id={selectedModelId}`.
5. **Interpretar** `assessment.quality` (`GOOD` / `MODERATE` / `UNSTABLE`) para cor/ícone.
6. **Mostrar** `recommendation.message` e guardar `recommendation.code` para regras da UI.
7. **Tratar erros:**
   - sem rede → mensagem local (“sem conexão com o servidor”);
   - `422` → coordenadas inválidas ou `model_id` ausente;
   - `404 MODEL_NOT_FOUND` / `MODEL_INACTIVE` → recarregar `/models` e pedir nova escolha;
   - `404 NO_PROBE_IN_RANGE` → aumentar raio ou pedir outra cidade;
   - `404 PROBE_NOT_FOUND` → não quebrar a tela; mostrar estado vazio.
8. **Não afirmar** que o resultado é a medição da rede do usuário. Use o disclaimer.

Fluxo extra opcional: `POST /api/v1/activity/check` com o mesmo `modelId` quando o usuário escolher um horário e uma atividade.

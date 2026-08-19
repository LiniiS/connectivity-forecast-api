# Contrato do arquivo de predições

Este documento é para a equipe que vai construir o modelo preditivo.

A API mobile **não** treina modelo, **não** chama RIPE Atlas e **não** executa `predict()`.  
Ela apenas lê um CSV já gerado.

Enquanto o modelo não existir, a API usa:

```text
data/mock_predictions.csv
```

Quando o modelo estiver pronto, entregue:

```text
data/predictions.csv
```

e configure:

```text
PREDICTIONS_FILE=data/predictions.csv
```

Nenhum endpoint REST precisa mudar.

## Identificador do grupo

Cada grupo recebe um `model_id` único. **Não altere** o identificador que foi atribuído ao seu grupo.

| Grupo | `model_id` (exemplo) |
| --- | --- |
| Grupo 1 | `model-a` |
| Grupo 2 | `model-b` |
| Grupo 3 | `model-c` |
| Grupo 4 | `model-d` |

Todas as linhas do seu CSV devem repetir esse `model_id`. O aplicativo mobile escolhe o modelo pelo `id` do catálogo (`data/models.json`); ele não conhece o algoritmo interno.

Nesta versão há **uma versão ativa por modelo**. O campo `model_version` continua obrigatório para rastreabilidade (ex.: `1.0`). Não há API de versionamento ainda.

O contrato mínimo de previsão é o mesmo para todos os grupos:

```text
model_id
model_version
probe_id
prediction_for
predicted_avg_rtt_ms
predicted_packet_loss_pct
```

Exemplo:

```csv
model_id,model_version,probe_id,prediction_for,predicted_avg_rtt_ms,predicted_packet_loss_pct
model-b,1.0,12345,2026-08-20T19:00:00Z,78.3,2.2
```

Se o CSV contiver um `model_id` que não existe em `models.json`, a API registra um **warning no log e ignora a linha**. Não entregue previsões com id não cadastrado.

## O que o modelo deve prever

Para cada intervalo futuro, produza exatamente estas duas variáveis:

| Campo | Significado | Métrica histórica correspondente |
| --- | --- | --- |
| `predicted_avg_rtt_ms` | Previsão futura do RTT médio, em milissegundos | Campo observado de ping do RIPE Atlas: `avg` |
| `predicted_packet_loss_pct` | Previsão futura da perda de pacotes, em porcentagem | Métrica **derivada** (não é campo original do RIPE) |

### Packet loss histórico

No resultado bruto de ping usado neste projeto, **não** existe um campo original chamado `packet_loss`.

A perda observada é calculada assim, quando `sent > 0`:

```text
packet_loss_pct = ((sent - rcvd) / sent) * 100
```

Portanto:

- `avg` é um dado **observado** (SOURCE)
- `packet_loss_pct` é um dado **derivado** (DERIVED)
- `predicted_avg_rtt_ms` e `predicted_packet_loss_pct` são **previsões** (PREDICTED)

Não atribua `quality`, `quality_score` nem `recommendation` ao modelo. O backend calcula esses campos.

Não atribua `model_confidence` ao RIPE Atlas. Se o modelo não tiver uma medida de confiança adequada, deixe a coluna vazia (`null`).

## Arquivo esperado

- Nome: `predictions.csv`
- Encoding: UTF-8
- Separador: vírgula
- Cabeçalho obrigatório na primeira linha
- Datetimes em ISO-8601 UTC, com `Z` (exemplo: `2026-08-20T19:00:00Z`)
- Uma linha = uma previsão para uma probe em um instante

### Campos obrigatórios

| Campo | Tipo | Validação | Exemplo |
| --- | --- | --- | --- |
| `prediction_id` | string | único, não vazio | `grupo2-900001-2026-08-20T19` |
| `model_id` | string | exatamente o id atribuído ao grupo | `model-b` |
| `model_version` | string | não vazio; uma versão ativa por modelo nesta API | `1.0` |
| `probe_id` | inteiro | > 0 | `12345` |
| `measurement_id` | inteiro | > 0 | `987654` |
| `country_code` | string | ISO 3166-1 alpha-2 | `BR` |
| `latitude` | float | -90 a 90 | `-23.5505` |
| `longitude` | float | -180 a 180 | `-46.6333` |
| `prediction_generated_at` | datetime UTC | timezone-aware | `2026-08-18T12:00:00Z` |
| `prediction_for` | datetime UTC | timezone-aware; instante previsto | `2026-08-20T19:00:00Z` |
| `predicted_avg_rtt_ms` | float | >= 0 | `71.4` |
| `predicted_packet_loss_pct` | float | >= 0, tipicamente 0 a 100 | `1.5` |

### Campos opcionais

| Campo | Tipo | Validação | Exemplo |
| --- | --- | --- | --- |
| `asn_v4` | inteiro ou vazio | ASN IPv4 da probe | `28573` |
| `asn_v6` | inteiro ou vazio | ASN IPv6 da probe | (vazio) |
| `model_confidence` | float ou vazio | 0.0 a 1.0 inclusive | `0.82` |

A API atual espera **todas** as colunas no cabeçalho, inclusive as opcionais. Se não houver valor, deixe a célula vazia.

Cabeçalho exigido, nesta ordem recomendada:

```text
prediction_id,model_id,model_version,probe_id,measurement_id,country_code,asn_v4,asn_v6,latitude,longitude,prediction_generated_at,prediction_for,predicted_avg_rtt_ms,predicted_packet_loss_pct,model_confidence
```

### Exemplo de linha

```text
pred-001,model-b,1.0,12345,987654,BR,28573,,-23.5505,-46.6333,2026-08-18T12:00:00Z,2026-08-20T19:00:00Z,78.3,2.2,0.76
```

## Correspondência com RIPE Atlas

Use apenas campos realmente presentes no ping/probe do RIPE Atlas para preencher as colunas SOURCE.

| Coluna no CSV | Origem RIPE | Notas |
| --- | --- | --- |
| `probe_id` | `prb_id` / `probe.id` | SOURCE |
| `measurement_id` | `msm_id` | SOURCE |
| `country_code` | `probe.country_code` | SOURCE |
| `asn_v4` | `probe.asn_v4` | SOURCE; pode ser nulo |
| `asn_v6` | `probe.asn_v6` | SOURCE; pode ser nulo |
| `latitude`, `longitude` | `probe.geometry.coordinates` | GeoJSON `[longitude, latitude]`. Não inverter. |

Campos de ping relevantes para o treino (não vão no CSV de saída, mas alimentam o modelo):

| Campo RIPE | Papel |
| --- | --- |
| `avg` | observação de RTT médio |
| `min`, `max` | estatísticas de RTT |
| `sent`, `rcvd` | usados para derivar packet loss |
| `result[].rtt` | amostras individuais |
| `timestamp` | instante da medição |
| `dst_addr`, `dst_name`, `af`, `proto`, `type` | contexto da medição |

Não inclua no CSV, e a API não deve expor:

- `src_addr`
- `from`
- `address_v4`
- `address_v6`
- `prefix_v4`
- `prefix_v6`

## O que o modelo NÃO deve gerar

- `GOOD` / `MODERATE` / `UNSTABLE`
- `quality_score`
- `recommendation`
- textos para o aplicativo mobile
- endereços IP da probe

Esses itens são responsabilidade do backend ou estão fora do escopo.

## Volume sugerido

A API funciona com qualquer número de linhas. Para o aplicativo dos estudantes ser útil:

- várias probes (localizações)
- várias previsões por probe (timeline horária)
- cobertura no território em que os alunos vão testar

## Substituição do mock

1. Gere `data/predictions.csv` com o contrato acima.
2. Defina `PREDICTIONS_FILE=data/predictions.csv`.
3. Reinicie o serviço.
4. Confirme `GET /api/v1/health` e `GET /api/v1/locations`.

Os aplicativos mobile continuam usando os mesmos endpoints.

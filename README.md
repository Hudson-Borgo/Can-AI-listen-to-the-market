# Can AI Listen to the Market?

POC de monitoramento de notícias e geração de sinais para o mercado brasileiro
de energia elétrica usando Python, NLP/LLM e Microsoft Foundry.

O alvo de mercado é o **preço da última operação de cada dia no BBCE eHub para
o produto M+1**, com entrega no mês seguinte. As notícias são avaliadas pelo
impacto esperado sobre esse preço no próximo pregão disponível.

Além do indicador diário, o projeto contém experimentos temporalmente corretos
para medir se as notícias acrescentam informação às variáveis de mercado.

## Fluxo

```text
MegaWhat RSS
    │
    ▼
Bronze: registro da fonte
    │
    ▼
Silver: notícia normalizada ─────► Silver: avaliação do LLM
    │                                      │
    └──────────────────┬───────────────────┘
                       ▼
              Gold: sinal diário
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
          Dashboard          Notebooks/ML
```

Para cada notícia, o LLM produz:

```json
{
  "sentiment": "positive | neutral | negative",
  "score": 0.0,
  "relevance": 0.0,
  "reason": "..."
}
```

O sinal diário é calculado por:

```text
Σ(score × relevance)
────────────────────
    Σ(relevance)
```

Os thresholds atuais são heurísticos:

```text
signal < -0.15            NEGATIVE
-0.15 <= signal <= 0.15   NEUTRAL
signal > 0.15             POSITIVE
```

## Arquitetura de dados

O projeto usa uma arquitetura medalhão leve. O dicionário detalhado está em
[`data/README.md`](data/README.md).

```text
data/
├── bronze/
│   └── news/
│       └── megawhat_news.csv
├── silver/
│   ├── news/
│   │   └── br_energy_news.csv
│   ├── nlp/
│   │   └── br_energy_news_scores.csv
│   └── market/
│       └── bbce_ehub_m1_closing_price_daily.csv
└── gold/
    ├── signals/
    │   └── br_energy_news_signal_daily.csv
    ├── features/
    │   └── br_energy_news_features_daily.csv
    └── modeling/
        └── bbce_ehub_m1_news_features_daily.csv
```

Notícias e avaliações ficam separadas. Cada avaliação registra o modelo, a
versão do prompt e o horário da análise, permitindo upgrades e reprocessamentos
sem recolher a fonte ou sobrescrever análises anteriores.

## Estrutura do código

```text
config/sites/                  # Configuração da fonte MegaWhat
scripts/migrate_to_medallion.py
src/
├── collectors/                # Coleta atual e histórica
├── normalization/             # Contrato normalizado de notícias
├── repository/                # Persistência e deduplicação
├── nlp/                       # Cliente, prompt e processamento LLM
├── signals/                   # Sinal diário
├── dashboard/                 # Dashboard Streamlit
├── paths.py                   # Caminhos canônicos do projeto
└── pipeline.py                # Orquestração ponta a ponta
```

Os notebooks devem ser executados nesta ordem:

1. `01_news_daily_features.ipynb` — features diárias de notícias;
2. `02_market_news_eda.ipynb` — alinhamento com pregões e EDA;
3. `03_classification_next_day_direction.ipynb` — direção do próximo pregão;
4. `04_time_series_sarimax_same_day_price.ipynb` — nowcasting do fechamento.

## Configuração

O ambiente é gerenciado com [uv](https://docs.astral.sh/uv/):

```bash
uv sync
cp .env.example .env
```

Configure as credenciais do Microsoft Foundry/Azure OpenAI no `.env`:

```dotenv
AZURE_OPENAI_API_KEY=SUA_CHAVE_AQUI
AZURE_OPENAI_ENDPOINT=https://YOUR_RESOURCE_NAME.openai.azure.com/
AZURE_OPENAI_MODEL=gpt-5.4-mini
```

## Demo ao vivo

Todos os comandos exibem o progresso no terminal, notícia por notícia, usando
as três etapas da apresentação: **OUVIR → SENTIR → PREVER**.

Pipeline completa:

```bash
uv run python -m src run
```

Para limitar a coleta a cinco notícias durante uma apresentação:

```bash
uv run python -m src run --limit 5
```

Cada componente também pode ser demonstrado separadamente:

```bash
# OUVIR: coleta, deduplicação e persistência bronze/silver
uv run python -m src collect --limit 5

# SENTIR: IA analisa somente as notícias ainda pendentes
uv run python -m src analyze

# SENTIR em uma demo determinística: reexibe 5 avaliações já salvas
uv run python -m src analyze --replay 5

# PREVER: agrega as avaliações e atualiza o sinal diário gold
uv run python -m src signal
```

O coletor pode receber notícias já existentes no CSV. Nesse caso elas aparecem
na tela, mas são identificadas como duplicadas e não são gravadas novamente. A
análise com IA é incremental: para a versão atual de modelo e prompt, somente
os `article_id` ainda não avaliados consomem a API. O modo `--replay` é somente
leitura: não chama a API e não altera os CSVs nem o sinal oficial.

Coleta histórica:

```bash
uv run python -m src.collectors.megawhat_history \
  --start-date 2026-01-01 \
  --end-date 2026-08-31
```

Dashboard:

```bash
uv run python -m src dashboard
```

O dashboard lê as notícias e scores da camada silver e o sinal diário persistido
na camada gold. O launcher usa caminhos absolutos, portanto o dashboard não
depende da variável `PYTHONPATH` nem do diretório em que o comando foi iniciado.

Para ver todos os comandos e opções:

```bash
uv run python -m src --help
```

## Migração do layout legado

O script abaixo migra os antigos CSVs para as novas camadas, separa os scores do
conteúdo das notícias, remove duplicatas por fonte/URL e não chama fontes
externas nem o LLM:

```bash
uv run python scripts/migrate_to_medallion.py
```

Ele é idempotente e pode ser executado novamente com segurança.

## Limitações atuais

- Os thresholds do sinal ainda não foram calibrados historicamente.
- O horário das notícias ainda precisa de uma política explícita de corte por
  sessão de negociação.
- O histórico bronze anterior à migração não existe e não é reconstruído a
  partir dos dados normalizados.
- Os experimentos são evidência inicial e não constituem uma estratégia de
  investimento.

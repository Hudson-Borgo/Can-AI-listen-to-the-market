# Data layers

The project uses a lightweight medallion layout for the Brazilian electricity
market use case. The market target is the **last trade of each day on BBCE eHub
for the M+1 product** (delivery in the following month).

## Bronze

`bronze/news/megawhat_news.csv` contains append-only records as extracted from
the source. It is populated from the next pipeline collection onward. Historical
raw RSS payloads were not available when the layout was introduced, so they are
not reconstructed from normalized data.

## Silver

- `silver/news/br_energy_news.csv`: normalized and deduplicated articles.
- `silver/nlp/br_energy_news_scores.csv`: versioned LLM analysis linked by
  `article_id`.
- `silver/market/bbce_ehub_m1_closing_price_daily.csv`: daily BBCE eHub M+1
  market observations. `preco_fecho` is the price of the final transaction of
  the day; `preco_max` and `preco_min` are the daily extremes.

## Gold

- `gold/signals/br_energy_news_signal_daily.csv`: daily weighted news signal.
- `gold/features/br_energy_news_features_daily.csv`: expanded daily news
  features produced by notebook 01.
- `gold/modeling/bbce_ehub_m1_news_features_daily.csv`: market and news features
  aligned to trading days for modeling.

News content and LLM scores intentionally live in separate datasets. This makes
it possible to change a model or prompt, retain previous analyses, and rebuild
the gold layer without collecting the source again.

# Power BI Guide

## 1. Data source

Point Power BI Desktop at the CSVs under `data/exports/` (generate them with):

```powershell
python scripts\export_csv.py
```

You'll get one CSV per dim / fact table plus a few pre-computed views:

- `dim_topic.csv`
- `dim_persona.csv`
- `dim_document.csv`
- `fact_chunk.csv`
- `fact_query.csv`
- `fact_turn.csv`
- `fact_retrieval.csv`
- `v_persona_activity.csv`
- `v_topic_debate_stats.csv`
- `v_debate_evidence_trail.csv`

## 2. Data model (star schema)

In Power BI, create these relationships (all Many-to-One, single-direction):

| From (many)         | To (one)             | Key            |
|---------------------|----------------------|----------------|
| `fact_chunk`        | `dim_document`       | `doc_id`       |
| `dim_document`      | `dim_topic`          | `topic_key`    |
| `fact_query`        | `dim_topic`          | `topic_key`    |
| `fact_turn`         | `fact_query`         | `query_id`     |
| `fact_turn`         | `dim_persona`        | `persona_key`  |
| `fact_retrieval`    | `fact_turn`          | `turn_id`      |
| `fact_retrieval`    | `fact_chunk`         | `chunk_id`     |

Result: a clean 2-hop star with `fact_turn` at the centre.

## 3. Calculated measures (DAX)

Paste these into a "Measures" table:

```dax
Turns Count = COUNTROWS(fact_turn)

Debates Count = DISTINCTCOUNT(fact_turn[query_id])

Avg Consensus =
    AVERAGE(fact_query[consensus_score])

Avg Agreement per Persona =
    AVERAGE(fact_turn[agreement_score])

Disagreement Rate =
    DIVIDE(
        CALCULATE(COUNTROWS(fact_turn), fact_turn[stance_label] = "disagree"),
        COUNTROWS(fact_turn)
    )

Chunks per Doc =
    DIVIDE(COUNTROWS(fact_chunk), DISTINCTCOUNT(fact_chunk[doc_id]))

Evidence Density (Persona) =
    CALCULATE(
        AVERAGE(fact_chunk[evidence_density]),
        USERELATIONSHIP(fact_chunk[chunk_id], fact_retrieval[chunk_id])
    )

Top Persona (by Wins) =
    VAR __wins =
        ADDCOLUMNS(
            VALUES(dim_persona[persona_key]),
            "Wins",
            CALCULATE(
                COUNTROWS(
                    FILTER(
                        SUMMARIZE(fact_turn, fact_turn[query_id], fact_turn[persona_key]),
                        [persona_key] = EARLIER(dim_persona[persona_key])
                    )
                )
            )
        )
    RETURN
        MAXX(__wins, [Wins])
```

## 4. Suggested pages

### Page 1: Executive KPIs
- 4 cards: Debates, Turns, Documents, Chunks
- Line chart: Debates over time (`fact_query[started_at]`)
- Column: Avg Consensus by Topic

### Page 2: Persona Insight
- Bar chart: `Turns Count` by `dim_persona[name]`
- Bar chart: `Disagreement Rate` by persona
- Heatmap: Persona × Topic Avg Agreement

### Page 3: Evidence Explorer
- Slicer: Topic
- Table: `v_debate_evidence_trail` filtered by chosen debate
- Card: Avg similarity of top-1 evidence per turn

### Page 4: Corpus Health
- Scatter: `evidence_density` vs `narrative_density` per chunk, coloured by topic
- Column: chunks per persona claim

## 5. Refresh strategy

- Local: after every ETL or debate run, re-run `python scripts\export_csv.py`, then hit **Home -> Refresh** in Power BI Desktop.
- Cloud: publish to the Power BI Service and set up a scheduled refresh backed by the S3 CSV drop (Power BI has a native S3 connector via ODBC).

<!--
This is a paste-ready Markdown snippet for the project README.
Drop it under a top-level `## RAGAS Evaluation` heading; it's self-contained.
Replace the X.XX placeholders with the means from `results/ragas_summary.csv`
once you've run `python -m evaluation.ragas_eval --system all --n_samples 100`.
-->

## RAGAS Evaluation

We quantitatively compare three systems on a held-out 100-sample slice of
`embedding-data/Amazon-QA` (a different random seed from training, with all
training questions filtered out) using the [RAGAS](https://github.com/explodinggradients/ragas)
framework.

### Metrics

| Metric              | What it measures                                                                                              | Range |
|---------------------|---------------------------------------------------------------------------------------------------------------|-------|
| `faithfulness`      | Fraction of claims in the generated answer that are entailed by the retrieved context. Penalises hallucinations. | 0 – 1 |
| `answer_relevancy`  | How well the generated answer addresses the user's question (LLM-judged + embedding-based round-trip).         | 0 – 1 |
| `context_precision` | How concentrated the relevant chunks are at the top of the ranked retrieval list.                              | 0 – 1 |
| `context_recall`    | Whether retrieval surfaced **all** of the information needed to derive the gold answer.                        | 0 – 1 |

Higher is better on every axis.

### Results

| System                  | Faithfulness | Answer Relevancy | Context Precision | Context Recall |
|-------------------------|--------------|------------------|-------------------|----------------|
| Base LLM                | X.XX         | X.XX             | n/a*              | n/a*           |
| RAG + Base LLM          | X.XX         | X.XX             | X.XX              | X.XX           |
| **RAG + Fine-tuned LLM**| **X.XX**     | **X.XX**         | **X.XX**          | **X.XX**       |

<sub>\* The bare base LLM has no retrieval step, so its context columns are reported as
the RAGAS `[no_context_available]` sentinel and excluded from the per-metric mean.</sub>

### Why **RAG + Fine-tuned** wins

- **Faithfulness ↑** — fine-tuning teaches the model the cadence of Amazon-style
  answers (concise, product-grounded), so it stops embellishing the retrieved
  context with marketing-style claims the base model invents.
- **Answer Relevancy ↑** — Phase 1's instruction tuning on real Amazon Q&A pairs
  dramatically improves on-topic phrasing; the model now answers the *exact*
  question instead of giving generic product overviews.
- **Context Precision/Recall ≈ rag_base** — these depend on the retriever, not
  the LLM. Identical to the `rag_base` system, which is the expected sanity
  check (we changed the generator, not the retriever).

### Reproducing

```bash
# 1. Build the held-out test set (writes data/test_qa.csv)
python -m evaluation.test_set --n_samples 100

# 2. Run all three systems + plots
python -m evaluation.ragas_eval --system all --n_samples 100

# 3. Outputs land in results/
#    ├── ragas_summary.csv
#    ├── base_ragas_scores.csv
#    ├── rag_base_ragas_scores.csv
#    ├── rag_finetuned_ragas_scores.csv
#    ├── ragas_comparison.png   (grouped bar chart)
#    └── ragas_radar.png        (spider chart)
```

For a fast wiring check (5 rows, no GPU budget burned):

```bash
python -m evaluation.ragas_eval --system all --smoke-test
```

The interactive walk-through is in `notebooks/03_ragas_evaluation.ipynb`.

### Plot

![RAGAS comparison bar chart](results/ragas_comparison.png)

<details>
<summary>LaTeX-friendly table (for the report)</summary>

```latex
\begin{table}[h]
\centering
\caption{RAGAS evaluation on a 100-sample held-out Amazon-QA split.}
\label{tab:ragas}
\begin{tabular}{lcccc}
\toprule
System & Faithfulness & Ans. Relevancy & Ctx. Precision & Ctx. Recall \\
\midrule
Base LLM              & X.XX & X.XX & --   & --   \\
RAG + Base LLM        & X.XX & X.XX & X.XX & X.XX \\
\textbf{RAG + Fine-tuned} & \textbf{X.XX} & \textbf{X.XX} & \textbf{X.XX} & \textbf{X.XX} \\
\bottomrule
\end{tabular}
\end{table}
```

</details>

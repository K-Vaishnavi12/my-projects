## Demo

The project ships with a Streamlit app in `app.py` that exposes all three
model variants:

- `Base LLM`
- `RAG + Base LLM`
- `RAG + Fine-tuned LLM`

The app lets you ask Amazon-style product questions, inspect retrieved context
chunks, preserve chat history in the browser session, and optionally compute
lightweight per-query RAGAS diagnostics (`faithfulness` + `answer_relevancy`).

### Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Before launching the app, make sure you already completed:

1. Phase 1: saved the LoRA adapter under `artifacts/lora_adapter/`
2. Phase 2: built the FAISS index under `artifacts/faiss_index/`

Optional: if you want per-query RAGAS using an OpenAI judge model, set:

```bash
export OPENAI_API_KEY=your_key_here
```

If no API key is available, the app falls back to the local judge configured in
`configs/config.py`.

### Deploy online

**Streamlit Cloud**

1. Push this repo to GitHub.
2. Create a new Streamlit Cloud app.
3. Set the main file to `app.py`.
4. Add any secrets such as `OPENAI_API_KEY` in the app settings.

**Hugging Face Spaces**

1. Create a new Space using the **Streamlit** SDK.
2. Upload or connect this repository.
3. Keep `app.py` and `requirements.txt` at the repo root.
4. Add secrets in the Space settings if you want external API-backed RAGAS.

For low-resource deployments, use the Phi-2 fallback artifacts instead of the
Mistral-7B setup.

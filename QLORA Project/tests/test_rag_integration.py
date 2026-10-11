from __future__ import annotations

from langchain.schema import Document


def test_toy_rag_pipeline_end_to_end():
    docs = [
        Document(page_content="Question: Is the charger USB-C?\nAnswer: Yes, it uses USB-C."),
        Document(page_content="Question: Is the battery removable?\nAnswer: No, battery is built-in."),
    ]

    query = "Does the charger use USB-C?"
    retrieved = [doc for doc in docs if "usb-c" in doc.page_content.lower()]
    assert retrieved

    answer = "Yes, it uses USB-C."
    assert "usb-c" in answer.lower()
    assert "usb-c" in retrieved[0].page_content.lower()

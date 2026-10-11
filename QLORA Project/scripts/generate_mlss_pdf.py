from __future__ import annotations

from pathlib import Path
import textwrap


OUTPUT_PATH = Path("MLSS_Technical_Journey.pdf")

HEADING = "MLSS Application Statement: Technical Journey in AI/ML"

ESSAY = """My technical journey in AI/ML started with curiosity and trial and error. I began by learning Python and basic machine learning, then moved toward NLP because I was more interested in systems that can interact with people than in benchmark-only models. Over time, I shifted from running notebooks to building complete, reusable pipelines.

The strongest project I have built so far is AmazonQA-RAG. I designed it as an end-to-end system instead of a single model experiment. In Phase 1, I fine-tuned an instruction model on Amazon-style question-answer data using QLoRA so training could run on limited hardware. In Phase 2, I built a retrieval pipeline with sentence-transformer embeddings and FAISS so the model could answer with evidence rather than guess. In Phase 3, I added RAGAS-based evaluation across three variants (base, RAG plus base, and RAG plus fine-tuned) to measure faithfulness, answer relevancy, context precision, and context recall. In Phase 4, I packaged everything into a Streamlit app with model switching, context inspection, and optional per-query diagnostics.

Before this project, I also explored classic ML workflows such as tabular classification, feature engineering, and model validation, but I kept returning to language systems because they have a direct user-facing impact. I experimented with prompt design, embedding-based search, and few-shot setups to understand where simple methods fail and where architecture choices matter. That gradual progression helped me move from “getting a model to run” to thinking about system behavior, error cases, and user trust.

This journey taught me practical lessons: good prompts are not enough, retrieval quality can dominate generation quality, and evaluation must be built into the workflow from day one. I also learned to care about reproducibility, configuration design, and failure handling, because real systems break in unexpected ways.

At the same time, I am very aware of my gaps. I want deeper understanding of optimization and generalization, stronger intuition for representation learning, and more systematic knowledge of advanced topics such as multimodal learning, efficient fine-tuning at scale, and principled error analysis. I also want to improve how I read research papers and convert them into clean engineering decisions rather than copying recipes.

MLSS is exactly the environment I need for this next step. I am looking for structured depth, strong mentorship, and peers who challenge each other to think rigorously. I can contribute practical experience in shipping applied NLP systems under constraints, and I will benefit from the program's emphasis on fundamentals, experiments, and research mindset.

What makes me a strong fit is the combination of curiosity and execution. I do not stop at “the model works.” I keep asking why it works, where it fails, and how to make it more trustworthy. I enjoy the full cycle: building, testing, debugging, and explaining decisions clearly.

In short, my goal is to become an engineer who is both implementation-strong and research-aware. I want to learn from MLSS, contribute actively to the cohort, and carry that learning into real systems that are useful, reliable, and grounded in evidence."""


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_lines(text: str, width: int = 92) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n\n"):
        wrapped = textwrap.wrap(para.strip(), width=width)
        lines.extend(wrapped if wrapped else [""])
        lines.append("")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def _build_pdf(lines: list[str]) -> bytes:
    max_lines_per_page = 44
    pages = [lines[i : i + max_lines_per_page] for i in range(0, len(lines), max_lines_per_page)]
    if not pages:
        pages = [[""]]

    n_pages = len(pages)
    page_obj_ids = [3 + 2 * i for i in range(n_pages)]
    content_obj_ids = [4 + 2 * i for i in range(n_pages)]
    font_obj_id = 3 + 2 * n_pages

    objects: list[tuple[int, bytes]] = []

    # 1: Catalog
    objects.append((1, b"<< /Type /Catalog /Pages 2 0 R >>"))

    # 2: Pages
    kids = " ".join(f"{pid} 0 R" for pid in page_obj_ids)
    objects.append((2, f"<< /Type /Pages /Kids [{kids}] /Count {n_pages} >>".encode("utf-8")))

    for idx, page_lines in enumerate(pages):
        page_id = page_obj_ids[idx]
        content_id = content_obj_ids[idx]

        # Page object
        page_dict = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_obj_id} 0 R >> >> "
            f"/Contents {content_id} 0 R >>"
        )
        objects.append((page_id, page_dict.encode("utf-8")))

        # Content stream
        stream_lines = ["BT"]
        if idx == 0:
            stream_lines.extend([
                "/F1 16 Tf",
                "50 770 Td",
                f"({_escape_pdf_text(HEADING)}) Tj",
                "/F1 11 Tf",
                "0 -28 Td",
            ])
        else:
            stream_lines.extend([
                "/F1 11 Tf",
                "50 760 Td",
            ])
        stream_lines.append("14 TL")
        for line in page_lines:
            stream_lines.append(f"({_escape_pdf_text(line)}) Tj")
            stream_lines.append("T*")
        stream_lines.append("ET")
        stream_data = "\n".join(stream_lines).encode("utf-8")
        stream_obj = b"<< /Length " + str(len(stream_data)).encode("ascii") + b" >>\nstream\n" + stream_data + b"\nendstream"
        objects.append((content_id, stream_obj))

    # Font object
    objects.append((font_obj_id, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"))

    # Build full PDF
    objects.sort(key=lambda x: x[0])
    pdf = bytearray(b"%PDF-1.4\n")
    xref_positions = [0]

    for obj_id, content in objects:
        xref_positions.append(len(pdf))
        pdf.extend(f"{obj_id} 0 obj\n".encode("ascii"))
        pdf.extend(content)
        pdf.extend(b"\nendobj\n")

    xref_start = len(pdf)
    total_objects = objects[-1][0]
    pdf.extend(f"xref\n0 {total_objects + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")

    # fill sparse object offsets
    offset_map = {obj_id: pos for obj_id, pos in zip([obj[0] for obj in objects], xref_positions[1:])}
    for obj_id in range(1, total_objects + 1):
        pos = offset_map.get(obj_id, 0)
        pdf.extend(f"{pos:010d} 00000 n \n".encode("ascii"))

    trailer = (
        f"trailer\n<< /Size {total_objects + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_start}\n%%EOF"
    )
    pdf.extend(trailer.encode("ascii"))
    return bytes(pdf)


def main() -> None:
    lines = _build_lines(ESSAY)
    pdf_bytes = _build_pdf(lines)
    OUTPUT_PATH.write_bytes(pdf_bytes)
    print(OUTPUT_PATH.resolve())


if __name__ == "__main__":
    main()

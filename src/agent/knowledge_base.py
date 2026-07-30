"""
RAG Knowledge Base for ValuSense agent.

Stages:
  1. Hull structural parser (ToC + running-header splitter)
  2. Generic chunker for other documents
  3. Merge Hull page-segments into final chunks
  4. Embedding + Chroma vector store (multilingual)
  5. Retrieval function
  6. Validation tests
"""

import sys as _sys
import sqlite3 as _sqlite3
# ── sqlite3 workaround for Windows/Python 3.9 ──────────────────────
# ChromaDB requires sqlite3 >= 3.35.0; pysqlite3 bundles a newer version.
_sv = _sqlite3.sqlite_version.split(".")
if int(_sv[0]) < 3 or (int(_sv[0]) == 3 and int(_sv[1]) < 35):
    __import__("pysqlite3")
    _sys.modules["sqlite3"] = _sys.modules.pop("pysqlite3")
del _sv, _sys, _sqlite3

import json
import re
import hashlib
from pathlib import Path
from typing import List, Optional

# ── paths ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent
HULL_PATH = BASE_DIR / "RAG docs" / "Hull J.C.-Options, Futures and Other Derivatives_9th edition.md"
RAG_DOCS_DIR = BASE_DIR / "RAG docs"
CHROMA_DIR = BASE_DIR / "models" / "rag_chroma"


# =====================================================================
# STAGE 1 — Hull structural parser
# =====================================================================

def _load_lines(filepath: Path) -> List[str]:
    with open(filepath, "r", encoding="utf-8") as f:
        return [line.rstrip("\n\r") for line in f]


def parse_toc_entries(lines: List[str]) -> List[dict]:
    toc = []
    pattern = re.compile(r"^Chapter\s+(\d+)\.\s+(.+?)\s+\.+\s+(\d+)$")
    for line in lines:
        m = pattern.match(line)
        if m:
            toc.append({
                "chapter_num": int(m.group(1)),
                "title": m.group(2).strip(),
                "page": int(m.group(3)),
            })
    return toc


def _title_case(title: str) -> str:
    """Convert 'Mechanics of futures markets' → 'Mechanics of Futures Markets'."""
    exceptions = {"of", "and", "the", "in", "for", "a", "an", "on", "to", "with", "vs"}
    words = title.split()
    result = []
    for i, w in enumerate(words):
        if i == 0 or w.lower() not in exceptions:
            result.append(w.capitalize() if w[0].islower() else w)
        else:
            result.append(w.lower() if w.islower() else w)
    return " ".join(result)


def _build_running_header_patterns(toc: List[dict]):
    """Build (regex, chapter_num) pairs for matching running headers.
    The running headers are '{TitleCaseTitle} {page_number}' or just '{TitleCaseTitle}' for first pages.
    """
    patterns = []
    for entry in toc:
        tc = re.escape(_title_case(entry["title"]))
        patterns.append((re.compile(f"^{tc} (\\d+)$"), entry["chapter_num"], entry["title"]))
        patterns.append((re.compile(f"^{tc}$"), entry["chapter_num"], entry["title"]))
    return patterns


def find_chapter_boundaries(lines: List[str], toc: List[dict]) -> List[dict]:
    """Parse running headers to find all chapter/page boundaries.
    Returns list of {chapter_num, chapter_title, page, line_idx}.
    """
    patterns = _build_running_header_patterns(toc)
    boundaries = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        for p_re, ch_num, ch_title in patterns:
            m = p_re.match(stripped)
            if m:
                page = int(m.group(1)) if m.lastindex and m.group(1) else None
                boundaries.append({
                    "chapter_num": ch_num,
                    "chapter_title": ch_title,
                    "page": page,
                    "line_idx": i,
                })
                break
    return boundaries


def skip_front_matter(lines: List[str], toc: List[dict]) -> int:
    """Find the line index where the first real chapter body starts.
    This is the line AFTER the ToC where the first running header appears.
    """
    patterns = _build_running_header_patterns(toc)
    for i, line in enumerate(lines):
        stripped = line.strip()
        for p_re, _, _ in patterns:
            if p_re.match(stripped):
                return i
    return 0


def parse_hull_structure(filepath: Path = None) -> List[dict]:
    """Stage 1: Parse the Hull file into page-tagged segments.

    Returns [{chapter_num, chapter_title, page, text, line_start, line_end}]
    """
    if filepath is None:
        filepath = HULL_PATH
    lines = _load_lines(filepath)

    toc = parse_toc_entries(lines)
    if len(toc) == 0:
        print("WARNING: No ToC entries found!")
        return []

    boundaries = find_chapter_boundaries(lines, toc)
    if len(boundaries) == 0:
        print("WARNING: No running-header boundaries found!")
        return []

    start_idx = skip_front_matter(lines, toc)
    # Filter to body boundaries only (after front matter)
    body_bounds = [b for b in boundaries if b["line_idx"] >= start_idx]

    segments = []
    current_ch = None
    current_page = None
    page_start_line = start_idx

    for b in body_bounds:
        ch = b["chapter_num"]
        pg = b["page"]
        line_idx = b["line_idx"]

        if current_ch is not None and current_page is not None:
            text = "\n".join(lines[page_start_line:line_idx]).strip()
            if text:
                segments.append({
                    "chapter_num": current_ch,
                    "chapter_title": next(
                        (e["title"] for e in toc if e["chapter_num"] == current_ch),
                        f"Chapter {current_ch}",
                    ),
                    "page": current_page,
                    "text": text,
                    "line_start": page_start_line,
                    "line_end": line_idx,
                })

        if pg is not None:
            current_page = pg
        else:
            current_page = 1  # first page of chapter, no page num → treat as page from ToC
            for e in toc:
                if e["chapter_num"] == ch:
                    current_page = e["page"]
                    break

        current_ch = ch
        page_start_line = line_idx + 1

    # last segment
    if current_ch is not None:
        text = "\n".join(lines[page_start_line:]).strip()
        if text:
            segments.append({
                "chapter_num": current_ch,
                "chapter_title": next(
                    (e["title"] for e in toc if e["chapter_num"] == current_ch),
                    f"Chapter {current_ch}",
                ),
                "page": current_page,
                "text": text,
                "line_start": page_start_line,
                "line_end": len(lines),
            })

    # Validation summary
    ch_set = set(s["chapter_num"] for s in segments)
    print(f"\n{'='*60}")
    print(f"Hull structural parser — validation summary")
    print(f"{'='*60}")
    print(f"Chapters detected: {len(ch_set)} / {len(toc)}")
    print(f"Page markers found: {len(body_bounds)}")
    print(f"Total segments: {len(segments)}")
    print(f"\nChapter ranges:")
    for entry in toc:
        cn = entry["chapter_num"]
        ch_segs = [s for s in segments if s["chapter_num"] == cn]
        if ch_segs:
            pages = [s["page"] for s in ch_segs]
            print(f"  Ch {cn:2d} ({entry['title']:40s}): pages {min(pages)}–{max(pages)}, {len(ch_segs)} segments")
        else:
            print(f"  Ch {cn:2d} ({entry['title']:40s}): ⚠ NO RUNNING HEADERS FOUND")
    print(f"{'='*60}\n")

    return segments


# =====================================================================
# STAGE 2 — Generic chunker for other documents
# =====================================================================

def chunk_generic_document(filepath: Path, source_name: str, language: str) -> List[dict]:
    """Chunk a non-Hull markdown document into ~1500-char pieces.

    Splits on markdown headers (## etc.) when present, otherwise on paragraph
    boundaries (double newline). Never crosses mid-sentence; backtracks to
    nearest sentence boundary within a 50-char overlap window.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    # Split on markdown headers first (preserve header as section metadata)
    header_pattern = re.compile(r"^(#{1,4}\s+.+)$", re.MULTILINE)
    # Strategy: walk through the text, identify section boundaries
    chunks = []
    target_size = 1500
    overlap = 50

    # Split into sections by headers
    sections = re.split(r"(?=^#{1,4}\s+)", text, flags=re.MULTILINE)
    current_section = None

    for section in sections:
        section = section.strip()
        if not section:
            continue
        header_match = re.match(r"^(#{1,4}\s+.+)$", section, re.MULTILINE)
        if header_match:
            current_section = header_match.group(1).strip()
            # Remove the header line from the text to chunk
            body = section[header_match.end():].strip()
        else:
            body = section

        if not body:
            chunks.append({
                "text": section,
                "source": source_name,
                "section": current_section or None,
                "language": language,
            })
            continue

        # Split body into paragraphs
        paragraphs = re.split(r"\n\s*\n", body)
        buffer = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(buffer) + len(para) + 1 <= target_size:
                buffer = (buffer + "\n\n" + para).strip()
            else:
                if buffer:
                    chunks.append({
                        "text": buffer,
                        "source": source_name,
                        "section": current_section or None,
                        "language": language,
                    })
                buffer = para

        if buffer:
            chunks.append({
                "text": buffer,
                "source": source_name,
                "section": current_section or None,
                "language": language,
            })

    # Apply overlap: for consecutive chunks from same section, steal overlap chars
    result = []
    for i, c in enumerate(chunks):
        txt = c["text"]
        if len(txt) < overlap:
            result.append(c)
            continue
        # If next chunk exists and same section, push last 50 chars into it
        if i + 1 < len(chunks) and chunks[i + 1].get("section") == c.get("section"):
            overlap_text = txt[-overlap:]
            # Backtrack to sentence boundary
            sent_boundary = max(
                overlap_text.rfind(". "),
                overlap_text.rfind("!\n"),
                overlap_text.rfind("?\n"),
                overlap_text.rfind(".\n"),
            )
            if sent_boundary >= 0:
                actual_overlap = overlap_text[sent_boundary + 1:]
            else:
                actual_overlap = overlap_text
            chunks[i + 1]["text"] = actual_overlap + "\n\n" + chunks[i + 1]["text"]
        result.append(c)

    return result


# =====================================================================
# STAGE 3 — Merge Hull page-segments into final chunks
# =====================================================================

def chunk_hull(segments: List[dict]) -> List[dict]:
    """Merge consecutive Hull page segments into ~1500-char chunks.
    Never crosses a chapter boundary.
    """
    target_size = 1500
    overlap = 50
    chunks = []

    by_chapter = {}
    for seg in segments:
        cn = seg["chapter_num"]
        by_chapter.setdefault(cn, []).append(seg)

    for cn in sorted(by_chapter.keys()):
        chapter_segs = sorted(by_chapter[cn], key=lambda s: s["page"])
        chapter_title = chapter_segs[0]["chapter_title"]
        buffer = ""
        buffer_start_page = None
        buffer_end_page = None

        for seg in chapter_segs:
            page = seg["page"]
            txt = seg["text"]

            if buffer_start_page is None:
                buffer_start_page = page

            if len(buffer) + len(txt) + 1 <= target_size:
                buffer = (buffer + "\n\n" + txt).strip()
                buffer_end_page = page
            else:
                if buffer:
                    chunks.append({
                        "text": buffer,
                        "source": "Hull",
                        "chapter": cn,
                        "chapter_title": chapter_title,
                        "page": buffer_start_page,
                        "page_end": buffer_end_page,
                        "language": "en",
                    })
                # Overlap: carry last `overlap` chars from previous buffer
                if len(buffer) >= overlap:
                    overlap_text = buffer[-overlap:]
                    sent_boundary = max(
                        overlap_text.rfind(". "),
                        overlap_text.rfind("!\n"),
                        overlap_text.rfind("?\n"),
                    )
                    buffer = (overlap_text[sent_boundary + 1:] + "\n\n" + txt).strip() if sent_boundary >= 0 else txt
                else:
                    buffer = txt
                buffer_start_page = page
                buffer_end_page = page

        if buffer:
            chunks.append({
                "text": buffer,
                "source": "Hull",
                "chapter": cn,
                "chapter_title": chapter_title,
                "page": buffer_start_page,
                "page_end": buffer_end_page,
                "language": "en",
            })

    # Print distribution
    print(f"\n{'='*60}")
    print("Hull chunking — per-chapter distribution")
    print(f"{'='*60}")
    by_cn = {}
    for c in chunks:
        by_cn.setdefault(c["chapter"], 0)
        by_cn[c["chapter"]] += 1
    for cn in sorted(by_cn.keys()):
        print(f"  Ch {cn:2d}: {by_cn[cn]:4d} chunks")
    print(f"  Total Hull chunks: {len(chunks)}")
    print(f"{'='*60}\n")

    return chunks


# =====================================================================
# STAGE 4 — Embedding + Vector Store
# =====================================================================

def _get_embedding_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


def build_vector_store(all_chunks: List[dict], force_rebuild: bool = False):
    """Embed all chunks and upsert into ChromaDB."""
    import chromadb
    from chromadb.config import Settings

    chroma_path = str(CHROMA_DIR)
    client = chromadb.PersistentClient(path=chroma_path, settings=Settings(anonymized_telemetry=False))

    collection_name = "valusense_rag"
    try:
        collection = client.get_collection(collection_name)
        count = collection.count()
        if count > 0 and not force_rebuild:
            print(f"Loaded existing store: {count} chunks from '{collection_name}'")
            return collection
    except Exception:
        pass

    if force_rebuild:
        try:
            client.delete_collection(collection_name)
        except Exception:
            pass

    print("Building new store...")
    model = _get_embedding_model()
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    # Prepare data
    ids, texts, metadatas = [], [], []
    for i, chunk in enumerate(all_chunks):
        chunk_id = hashlib.md5(chunk["text"].encode()).hexdigest()[:16]
        ids.append(chunk_id)
        texts.append(chunk["text"])
        meta = {
            "source": chunk.get("source", "unknown"),
            "language": chunk.get("language", "en"),
        }
        if chunk.get("section"):
            meta["section"] = chunk["section"]
        if chunk.get("chapter_title"):
            meta["chapter"] = str(chunk["chapter"])
            meta["chapter_title"] = chunk["chapter_title"]
        if chunk.get("page"):
            meta["page"] = str(chunk["page"])
        if chunk.get("page_end"):
            meta["page_end"] = str(chunk["page_end"])
        metadatas.append(meta)

    # Batch embed
    batch_size = 64
    from tqdm import tqdm
    for i in tqdm(range(0, len(texts), batch_size), desc="Embedding"):
        batch_texts = texts[i:i + batch_size]
        batch_ids = ids[i:i + batch_size]
        batch_metas = metadatas[i:i + batch_size]
        embeddings = model.encode(batch_texts, show_progress_bar=False).tolist()
        collection.add(
            ids=batch_ids,
            embeddings=embeddings,
            documents=batch_texts,
            metadatas=batch_metas,
        )

    # Stats
    total = collection.count()
    by_source = {}
    for m in metadatas:
        src = m.get("source", "unknown")
        by_source[src] = by_source.get(src, 0) + 1
    disk_size = sum(f.stat().st_size for f in CHROMA_DIR.rglob("*") if f.is_file()) if CHROMA_DIR.exists() else 0

    print(f"\n{'='*60}")
    print("Vector store statistics")
    print(f"{'='*60}")
    for src, count in sorted(by_source.items()):
        print(f"  {src}: {count} chunks")
    print(f"  Total: {total} chunks")
    print(f"  Store size: {disk_size / 1024:.1f} KB on disk")
    print(f"{'='*60}\n")

    return collection


# =====================================================================
# STAGE 5 — Retrieval function
# =====================================================================

def get_collection():
    """Load the Chroma collection (must be built first)."""
    import chromadb
    from chromadb.config import Settings

    client = chromadb.PersistentClient(path=str(CHROMA_DIR), settings=Settings(anonymized_telemetry=False))
    return client.get_collection("valusense_rag")


def retrieve_knowledge(
    query: str,
    k: int = 4,
    source_filter: Optional[List[str]] = None,
) -> List[dict]:
    """Search the vector store and return top-k results.

    Args:
        query: Natural language query.
        k: Number of results.
        source_filter: Optional list of source names to restrict search to.
                       e.g. ["Cadre", "Méthodes_de_Valorisation", "Financial_Asset_Valuation_Framework"]

    Returns:
        List of {text, source, section_or_chapter, page, language, score}
    """
    collection = get_collection()
    model = _get_embedding_model()
    q_emb = model.encode([query])[0].tolist()

    where_filter = None
    if source_filter:
        where_filter = {"source": {"$in": source_filter}}

    results = collection.query(
        query_embeddings=[q_emb],
        n_results=k,
        where=where_filter,
    )

    out = []
    for i in range(len(results["ids"][0])):
        meta = results["metadatas"][0][i]
        section_or_chapter = meta.get("chapter_title") or meta.get("section") or ""
        p = meta.get("page", "")
        if p and meta.get("page_end") and p != meta["page_end"]:
            page_str = f"{p}–{meta['page_end']}"
        elif p:
            page_str = str(p)
        else:
            page_str = ""

        # Build human-readable citation
        src = meta.get("source", "Unknown")
        parts = []
        if src == "Hull" and meta.get("chapter"):
            parts.append(f"Hull, Chapter {meta['chapter']}")
            if meta.get("chapter_title"):
                parts[-1] += f" — {meta['chapter_title']}"
        elif src == "Hull":
            parts.append("Hull")
        else:
            parts.append(src)
        if page_str:
            parts.append(f"p.{page_str}")

        out.append({
            "text": results["documents"][0][i],
            "source": src,
            "section_or_chapter": section_or_chapter,
            "page": page_str,
            "language": meta.get("language", "en"),
            "score": round(results["distances"][0][i], 4),
            "citation": ", ".join(parts),
        })

    return out


# =====================================================================
# STAGE 6 — Validation test suite
# =====================================================================

def run_validation_queries():
    queries = [
        {
            "q": "Why does IFRS 13 require Mark-to-Market for Level 1 assets?",
            "expected_sources": ["Cadre de Valorisation des Actifs Financiers.docx",
                                 "Méthodes de Valorisation des Actifs Financiers",
                                 "Financial Asset Valuation Framework.docx"],
            "filter": None,
        },
        {
            "q": "When does Hull recommend Monte Carlo over Black-Scholes?",
            "expected_sources": ["Hull"],
            "filter": ["Hull"],
        },
        {
            "q": "What is the Cost-of-Carry model used for in commodity valuation?",
            "expected_sources": ["Hull",
                                 "Cadre de Valorisation des Actifs Financiers.docx",
                                 "Financial Asset Valuation Framework.docx"],
            "filter": None,
        },
        {
            "q": "What are the key structural features used to classify financial assets?",
            "expected_sources": ["Cadre de Valorisation des Actifs Financiers.docx",
                                 "Financial Asset Valuation Framework.docx",
                                 "Méthodes de Valorisation des Actifs Financiers"],
            "filter": None,
        },
        {
            "q": "How does the fair value hierarchy determine which valuation method to use?",
            "expected_sources": ["Méthodes de Valorisation des Actifs Financiers",
                                 "Cadre de Valorisation des Actifs Financiers.docx",
                                 "Financial Asset Valuation Framework.docx"],
            "filter": None,
        },
        {
            "q": "Explain the binomial tree backward induction process",
            "expected_sources": ["Hull"],
            "filter": ["Hull"],
        },
        {
            "q": "Pourquoi utilise-t-on le modèle de Black-Scholes pour les options européennes?",
            "expected_sources": ["Hull"],
            "filter": None,
        },
    ]

    print(f"\n{'='*60}")
    print("VALIDATION TEST SUITE")
    print(f"{'='*60}")

    results_summary = []

    for qinfo in queries:
        q = qinfo["q"]
        filt = qinfo.get("filter")
        exp = qinfo["expected_sources"]
        print(f"\n{'─'*60}")
        print(f"Query: {q}")
        print(f"{'─'*60}")

        try:
            results = retrieve_knowledge(q, k=4, source_filter=filt)
        except Exception as e:
            print(f"  ERROR: {e}")
            results_summary.append({
                "query": q[:60],
                "top_source": "error",
                "expected_source": str(exp),
                "match": "no",
                "top_score": 0,
            })
            continue

        for rank, r in enumerate(results, 1):
            preview = r["text"][:150].replace("\n", " ")
            print(f"\n  #{rank}  [{r['source']}]  score={r['score']}")
            print(f"       Citation: {r['citation']}")
            print(f"       {preview}...")

        top_source = results[0]["source"] if results else "none"
        top_score = results[0]["score"] if results else 0
        match_any = any(e.lower() in top_source.lower() for e in exp)
        results_summary.append({
            "query": q[:60],
            "top_source": top_source,
            "expected_source": str(exp),
            "match": "yes" if match_any else "no",
            "top_score": top_score,
        })

    # Summary table
    print(f"\n\n{'='*60}")
    print("VALIDATION SUMMARY")
    print(f"{'='*60}")
    print(f"{'Query':<62} {'Top Source':<30} {'Expected':<30} {'Match':<6} {'Score':<8}")
    print(f"{'─'*140}")
    for r in results_summary:
        match_str = "✅" if r["match"] == "yes" else "❌"
        print(f"{r['query']:<62} {r['top_source']:<30} {r['expected_source']:<30} {match_str:<6} {r['top_score']:<8.4f}")


# =====================================================================
# Main
# =====================================================================

if __name__ == "__main__":
    import sys

    # Stage 1
    print("\n>>> Stage 1: Parsing Hull structure...")
    hull_segments = parse_hull_structure()
    print(f"    {len(hull_segments)} page-segments extracted.")

    # Stage 2 + 3 — build all chunks
    print("\n>>> Stage 2+3: Chunking all documents...")
    all_chunks = []

    # Hull
    hull_chunks = chunk_hull(hull_segments)
    all_chunks.extend(hull_chunks)

    # Other docs
    doc_configs = [
        ("Cadre de Valorisation des Actifs Financiers.docx.md", "Cadre de Valorisation des Actifs Financiers.docx", "fr"),
        ("Financial Asset Valuation Framework.docx.md", "Financial Asset Valuation Framework.docx", "en"),
        ("Méthodes de Valorisation des Actifs Financiers.md", "Méthodes de Valorisation des Actifs Financiers", "fr"),
    ]
    for fname, source, lang in doc_configs:
        fpath = RAG_DOCS_DIR / fname
        if fpath.exists():
            print(f"  Chunking {fname}...")
            doc_chunks = chunk_generic_document(fpath, source, lang)
            all_chunks.extend(doc_chunks)
            print(f"    {len(doc_chunks)} chunks from {source}")
        else:
            print(f"  Skipping {fname} (not found)")

    # Stage 4
    print("\n>>> Stage 4: Building vector store...")
    force = "--rebuild" in sys.argv
    collection = build_vector_store(all_chunks, force_rebuild=force)

    # Stage 6
    if "--validate" in sys.argv:
        print("\n>>> Stage 6: Running validation suite...")
        run_validation_queries()

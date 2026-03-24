#!/usr/bin/env python3
"""
Attention Residuals — relevance-scored context injection for Claude Code.

Inspired by Moonshot AI's "attention residuals" concept: instead of injecting
all historical context equally, we score each chunk's relevance to the current
session signal and pack the highest-scoring chunks into a token budget.

This is analogous to how transformer attention residuals preserve important
information across layers — we preserve important context across sessions,
weighted by relevance to the current task.

Architecture:
  - Pure Python 3 stdlib (no pip dependencies)
  - Reads context sources: session-buffer, session-log, archive, memory files
  - Scores via TF-IDF-like term overlap + recency decay + source-type weighting
  - Packs highest-scoring chunks into a configurable token budget
  - Outputs assembled context to stdout; score report to stderr

Toggle: Set ATTENTION_RESIDUALS=true to enable. Returns empty when disabled.

Copyright (c) 2026 Jonathan Hobman (Jonohobs), AI Hot Sauce, Claude Code (Anthropic)
License: MIT | Repository: https://github.com/Jonohobs/ai-hot-sauce
Created: 2026-03-19
"""

import sys
import os
import re
import math
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TOKEN_BUDGET = int(os.environ.get("ATTN_TOKEN_BUDGET", "4000"))  # in chars
CHARS_PER_TOKEN = 4  # rough estimate
CHAR_BUDGET = TOKEN_BUDGET * CHARS_PER_TOKEN

MEMORY_LOG_DIR = Path.home() / ".claude" / "memory-log"
ARCHIVE_DIR = MEMORY_LOG_DIR / "archive"
SESSION_BUFFER = MEMORY_LOG_DIR / "session-buffer.md"
SESSION_LOG = MEMORY_LOG_DIR / "session-log.md"
MEMORY_DIR = Path.home() / ".claude" / "projects" / "C--Users-jonat" / "memory"

# Max lines to read from each memory .md file (efficiency cap)
MEMORY_FILE_LINE_LIMIT = 50

# Source-type weight multipliers — session buffer is most relevant,
# memory files are general reference, archive is historical detail
SOURCE_WEIGHTS = {
    "session-buffer": 1.2,
    "archive": 1.0,
    "log-entry": 0.9,
    "memory": 0.8,
}

# Recency decay: days_old -> multiplier
# Newer context is more likely to be relevant to the current task
def recency_multiplier(days_old):
    if days_old <= 0:
        return 1.0
    elif days_old <= 1:
        return 0.9
    elif days_old <= 3:
        return 0.7
    elif days_old <= 7:
        return 0.5
    else:
        return 0.3

# Minimal English stopwords — enough to filter noise without importing nltk
STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "its", "this", "that", "was",
    "are", "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "can", "shall",
    "not", "no", "if", "then", "else", "when", "while", "as", "so", "than",
    "too", "very", "just", "also", "about", "up", "out", "all", "each",
    "into", "over", "after", "before", "between", "under", "through",
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "they",
    "them", "his", "her", "what", "which", "who", "how", "where", "there",
})

# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------

def tokenize(text):
    """Lowercase, strip punctuation, remove stopwords. Returns list of terms."""
    text = text.lower()
    # Replace non-alphanumeric with space, split
    words = re.findall(r"[a-z0-9_]+", text)
    return [w for w in words if w not in STOPWORDS and len(w) > 1]

# ---------------------------------------------------------------------------
# Chunk collection
# ---------------------------------------------------------------------------

class Chunk:
    """A scored piece of context."""
    __slots__ = ("source_type", "label", "text", "date", "score")

    def __init__(self, source_type, label, text, date=None):
        self.source_type = source_type
        self.label = label
        self.text = text
        self.date = date  # datetime or None
        self.score = 0.0

def gather_chunks():
    """Collect all candidate context chunks from available sources."""
    chunks = []
    today = datetime.now()

    # 1. Session buffer (last PreCompact summary)
    if SESSION_BUFFER.exists() and SESSION_BUFFER.stat().st_size > 0:
        try:
            text = SESSION_BUFFER.read_text(encoding="utf-8", errors="replace")
            if text.strip():
                mtime = datetime.fromtimestamp(SESSION_BUFFER.stat().st_mtime)
                chunks.append(Chunk("session-buffer", "session-buffer.md", text.strip(), mtime))
        except Exception:
            pass

    # 2. Session log — split into individual digest blocks (### delimited)
    if SESSION_LOG.exists() and SESSION_LOG.stat().st_size > 0:
        try:
            log_text = SESSION_LOG.read_text(encoding="utf-8", errors="replace")
            blocks = re.split(r"(?=^### )", log_text, flags=re.MULTILINE)
            for block in blocks:
                block = block.strip()
                if not block:
                    continue
                # Try to extract date from "### 2026-03-17 ..."
                date_match = re.match(r"### (\d{4}-\d{2}-\d{2})", block)
                block_date = None
                if date_match:
                    try:
                        block_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
                    except ValueError:
                        pass
                chunks.append(Chunk("log-entry", f"session-log:{block[:40]}", block, block_date))
        except Exception:
            pass

    # 3. Archive files
    if ARCHIVE_DIR.exists():
        try:
            for f in sorted(ARCHIVE_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
                if not f.is_file():
                    continue
                try:
                    text = f.read_text(encoding="utf-8", errors="replace")
                    if text.strip():
                        mtime = datetime.fromtimestamp(f.stat().st_mtime)
                        # Try date from filename like "2026-03-19-00-01-13-session.md"
                        fname_date = re.match(r"(\d{4}-\d{2}-\d{2})", f.name)
                        fdate = mtime
                        if fname_date:
                            try:
                                fdate = datetime.strptime(fname_date.group(1), "%Y-%m-%d")
                            except ValueError:
                                pass
                        chunks.append(Chunk("archive", f"archive/{f.name}", text.strip(), fdate))
                except Exception:
                    continue
        except Exception:
            pass

    # 4. Memory .md files (first N lines each for efficiency)
    if MEMORY_DIR.exists():
        try:
            for f in sorted(MEMORY_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
                if not f.is_file() or f.suffix != ".md":
                    continue
                try:
                    with open(f, "r", encoding="utf-8", errors="replace") as fh:
                        lines = []
                        for i, line in enumerate(fh):
                            if i >= MEMORY_FILE_LINE_LIMIT:
                                break
                            lines.append(line)
                    text = "".join(lines).strip()
                    if text:
                        mtime = datetime.fromtimestamp(f.stat().st_mtime)
                        chunks.append(Chunk("memory", f"memory/{f.name}", text, mtime))
                except Exception:
                    continue
        except Exception:
            pass

    return chunks

# ---------------------------------------------------------------------------
# Scoring engine — TF-IDF-like with recency decay and source weighting
# ---------------------------------------------------------------------------

def score_chunks(query_terms, chunks):
    """
    Score each chunk against the query signal.

    Algorithm (attention residuals analogy):
    - Term overlap = how much of the query's "attention" this chunk captures
    - TF-IDF boost = rare terms carry more signal (like attention heads
      focusing on distinctive tokens)
    - Recency decay = temporal attention — recent context attended to more
    - Source weight = structural prior on source importance

    Final score = term_overlap * tfidf_boost * recency * source_weight
    """
    if not query_terms or not chunks:
        return

    today = datetime.now()
    query_term_set = set(query_terms)
    query_term_count = len(query_term_set)
    if query_term_count == 0:
        return

    # Build document frequency (DF) for IDF calculation
    # DF = number of chunks containing each term
    doc_freq = Counter()
    chunk_term_sets = []
    for chunk in chunks:
        terms = set(tokenize(chunk.text))
        chunk_term_sets.append(terms)
        for t in terms:
            if t in query_term_set:
                doc_freq[t] += 1

    n_docs = len(chunks)

    for i, chunk in enumerate(chunks):
        chunk_terms = chunk_term_sets[i]

        # Term overlap: fraction of query terms found in this chunk
        matching_terms = query_term_set & chunk_terms
        if not matching_terms:
            chunk.score = 0.0
            continue

        term_overlap = len(matching_terms) / query_term_count

        # TF-IDF boost: average IDF of matching terms
        # IDF = log(N / DF) — rare terms across chunks get higher weight
        idf_sum = 0.0
        for t in matching_terms:
            df = doc_freq.get(t, 1)
            idf_sum += math.log((n_docs + 1) / (df + 1))  # +1 smoothing
        tfidf_boost = idf_sum / len(matching_terms) if matching_terms else 1.0
        # Normalize to a reasonable range (1.0 - ~3.0)
        tfidf_boost = max(1.0, min(tfidf_boost, 3.0))

        # Recency decay
        if chunk.date:
            days_old = (today - chunk.date).days
        else:
            days_old = 30  # unknown date = treat as old
        recency = recency_multiplier(days_old)

        # Source type weight
        src_weight = SOURCE_WEIGHTS.get(chunk.source_type, 1.0)

        chunk.score = term_overlap * tfidf_boost * recency * src_weight

# ---------------------------------------------------------------------------
# Packing — fill token budget with highest-scored chunks
# ---------------------------------------------------------------------------

def pack_chunks(chunks, char_budget):
    """
    Pack chunks into the character budget, highest score first.
    Returns list of (chunk, included_text) tuples.
    """
    sorted_chunks = sorted(chunks, key=lambda c: c.score, reverse=True)
    packed = []
    used = 0

    for chunk in sorted_chunks:
        if chunk.score <= 0:
            break
        text = chunk.text
        remaining = char_budget - used
        if remaining <= 100:  # not worth adding tiny fragments
            break
        if len(text) > remaining:
            # Truncate to fit, on a line boundary if possible
            text = text[:remaining]
            last_nl = text.rfind("\n")
            if last_nl > remaining * 0.5:
                text = text[:last_nl]
            text += "\n[...truncated]"
        packed.append((chunk, text))
        used += len(text)

    return packed

# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_output(packed):
    """Wrap packed chunks in XML tags for injection."""
    if not packed:
        return ""

    parts = ["<attention-residuals-context>"]
    for chunk, text in packed:
        parts.append(f"<context-chunk source=\"{chunk.label}\" score=\"{chunk.score:.3f}\">")
        parts.append(text)
        parts.append("</context-chunk>")
    parts.append("</attention-residuals-context>")
    return "\n".join(parts)

def log_report(chunks, packed):
    """Write score report to stderr for debugging."""
    top = sorted(chunks, key=lambda c: c.score, reverse=True)[:5]
    lines = ["[attention-residuals] Score report (top 5):"]
    for i, c in enumerate(top, 1):
        lines.append(f"  {i}. [{c.score:.3f}] {c.source_type}: {c.label[:60]}")
    lines.append(f"  Packed {len(packed)} chunks, {sum(len(t) for _, t in packed)} chars")
    lines.append(f"  Budget: {CHAR_BUDGET} chars (~{TOKEN_BUDGET} tokens)")
    print("\n".join(lines), file=sys.stderr)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Toggle check — if not enabled, output nothing
    enabled = os.environ.get("ATTENTION_RESIDUALS", "").lower() in ("true", "1", "yes")
    if not enabled:
        return

    # Get the query signal
    signal = ""

    # Check --signal argument
    if "--signal" in sys.argv:
        idx = sys.argv.index("--signal")
        if idx + 1 < len(sys.argv):
            signal = sys.argv[idx + 1]

    # Check stdin if no --signal provided
    if not signal and not sys.stdin.isatty():
        try:
            signal = sys.stdin.read().strip()
        except Exception:
            pass

    # Fallback: use session-buffer content as the signal
    if not signal:
        if SESSION_BUFFER.exists():
            try:
                signal = SESSION_BUFFER.read_text(encoding="utf-8", errors="replace").strip()
            except Exception:
                pass

    if not signal:
        print("[attention-residuals] No signal available, skipping.", file=sys.stderr)
        return

    # Tokenize query
    query_terms = tokenize(signal)
    if not query_terms:
        print("[attention-residuals] Signal tokenized to zero terms, skipping.", file=sys.stderr)
        return

    # Gather all context chunks
    chunks = gather_chunks()
    if not chunks:
        print("[attention-residuals] No context chunks found.", file=sys.stderr)
        return

    # Score
    score_chunks(query_terms, chunks)

    # Pack into budget
    packed = pack_chunks(chunks, CHAR_BUDGET)

    # Log report to stderr
    log_report(chunks, packed)

    # Output scored context to stdout
    output = format_output(packed)
    if output:
        print(output)


if __name__ == "__main__":
    # Force UTF-8 output on Windows to handle Unicode in memory files
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    try:
        main()
    except Exception as e:
        # Fail silently — never break the hook pipeline
        print(f"[attention-residuals] Error: {e}", file=sys.stderr)
        sys.exit(0)  # exit 0 even on error so hook chain continues

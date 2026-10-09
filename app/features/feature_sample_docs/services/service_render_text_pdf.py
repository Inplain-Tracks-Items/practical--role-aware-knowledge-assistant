# Renders simple Markdown (# title, ## heading, paragraphs) into an A4 PDF with a real text layer.
# ICS layer: service
# CRD component: be.service_render_text_pdf
# Called by: feature_sample_docs/handlers/handle_build_sample_docs.py
# Calls: PyMuPDF (PDF drawing)
# Step: added in step 2 (Ingest tagged chunks)

import asyncio  # rendering is CPU work; it runs in a worker thread
import textwrap  # wraps long paragraphs to the page width

import pymupdf  # PyMuPDF: creates PDF pages and draws text

# A4 in PDF points (1/72 inch) and the layout of the text block.
PAGE_WIDTH, PAGE_HEIGHT = 595, 842
MARGIN = 56
# (font size, built-in font name, characters per line) per kind of line; Helvetica keeps it dependency-free.
STYLES = {"title": (18, "hebo", 50), "heading": (13, "hebo", 70), "body": (10.5, "helv", 95)}


def _render(markdown: str) -> bytes:
    """Draw every line of markdown on as many pages as needed and return the PDF bytes."""
    document = pymupdf.open()
    page = document.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
    y = MARGIN
    for raw_line in markdown.splitlines():
        # Blank lines in Markdown separate paragraphs: leave a small vertical gap.
        if not raw_line.strip():
            y += 8
            continue
        # Pick the style from the Markdown prefix and strip the prefix from the text.
        if raw_line.startswith("# "):
            style, text = "title", raw_line[2:]
        elif raw_line.startswith("## "):
            style, text = "heading", raw_line[3:]
        else:
            style, text = "body", raw_line
        size, font, width = STYLES[style]
        # Headings get extra space above them so sections stay readable.
        if style == "heading":
            y += 6
        for line in textwrap.wrap(text, width=width):
            # Start a new page when the next line would cross the bottom margin.
            if y + size > PAGE_HEIGHT - MARGIN:
                page = document.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
                y = MARGIN
            # insert_text writes real, selectable text: this is what makes the PDF "text-based".
            page.insert_text((MARGIN, y + size), line, fontsize=size, fontname=font)
            y += size * 1.45
    return document.tobytes()


async def service_render_text_pdf(markdown: str) -> bytes:
    """Return a text-based PDF of markdown (one or more A4 pages)."""
    return await asyncio.to_thread(_render, markdown)

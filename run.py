
import fitz  # PyMuPDF
from dataclasses import dataclass
from typing import List
from pathlib import Path
import json

INPUT_DIR = Path("inputs")
OUTPUT_DIR = Path("output")


@dataclass
class Appendix:
    doc: fitz.Document
    position_in_source_doc: int
    placeholder_text: str


def setup_documents(source_doc: fitz.Document, appendices: List[Appendix]):
    for page_num, page in enumerate(source_doc):
        text = page.get_text("text")

        for appendix in appendices:
            if appendix.placeholder_text in text:
                appendix.position_in_source_doc = page_num
                break


def total_prev_len(current_name: str, appendices: List[Appendix]):
    counter = 0
    for appendix in appendices:
        if current_name == appendix.placeholder_text:
            break
        counter = counter + appendix.doc.page_count
    return counter


def update_toc(initial_toc, appendices: List[Appendix]):
    updated_toc = []
    appendices = sorted(appendices, key=lambda x: x.position_in_source_doc)

    for entry in initial_toc:
        level, title, page_num = entry

        for appendix in appendices:
            if title in appendix.placeholder_text:
                total_num = total_prev_len(
                    appendix.placeholder_text, appendices)
                page_num = appendix.position_in_source_doc + \
                    total_prev_len(appendix.placeholder_text, appendices) - \
                    1 if total_num else appendix.position_in_source_doc

        updated_toc.append([level, title, page_num])

    return updated_toc


def update_toc_text(doc: fitz.Document, initial_toc, updated_toc):
    for i, (level, title, old_page) in enumerate(initial_toc):
        new_page = updated_toc[i][2]

        if old_page != new_page:  # Only update if page number changed
            for page_num in range(len(doc)):
                page = doc[page_num]

                search_text = f"{title} {old_page}"
                text_instances = page.search_for(search_text)

                if not text_instances:
                    continue

                rect = text_instances[-1]

                # 1. Erase old page number (draw white rectangle)
                shape = page.new_shape()
                shape.draw_rect(rect)
                shape.finish(width=0, fill=(1, 1, 1), color=(1, 1, 1))
                shape.commit()

                # Fill the area with white color manually
                page.draw_rect(rect, fill=(1, 1, 1), color=(1, 1, 1), width=0)

                # Left-aligned with the old text
                text_x = rect.x0
                # Vertically centered
                text_y = rect.y0 + ((rect.y1 - rect.y0) / 1.35)
                # Ensure text is written in the cleared area
                page.insert_text((text_x, text_y),
                                 f"{new_page}", fontsize=10, color=(0, 0, 0))

    return doc


def process_merge(source_doc: fitz.Document, appendices: List[Appendix]):
    initial_toc = source_doc.get_toc(simple=True)
    setup_documents(source_doc, appendices)
    appendices = sorted(
        appendices, key=lambda x: x.position_in_source_doc, reverse=True)
    for apendix in appendices:
        source_doc.delete_page(apendix.position_in_source_doc)
    for apendix in appendices:
        source_doc.insert_pdf(
            apendix.doc, start_at=apendix.position_in_source_doc)
    updated_toc = update_toc(initial_toc, appendices)
    source_doc = update_toc_text(source_doc, initial_toc, updated_toc)
    source_doc.set_toc(updated_toc)
    output_path = f"{OUTPUT_DIR}/merged.pdf"
    source_doc.save(output_path)
    return output_path


if __name__ == "__main__":
    with open("config.json", "r") as config_file:
        configs = json.load(config_file)

    source_file = configs["source_file"]
    appendices = configs["appendices"]

    source_doc = fitz.open(f"{INPUT_DIR}/{source_file}")
    appendice_objs = []
    for item in appendices:
        appendice_objs.append(
            Appendix(doc=fitz.open(f"{INPUT_DIR}/{item['file']}"),
                     position_in_source_doc=0,
                     placeholder_text=item["placeholder"]))

    process_merge(source_doc, appendice_objs)

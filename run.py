
import fitz  # PyMuPDF
from dataclasses import dataclass
from typing import List
from pathlib import Path
import json

INPUT_DIR = Path("inputs")
OUTPUT_DIR = Path("output")


@dataclass
class AppendixItem:
    doc: fitz.Document
    position_in_source_doc: int
    placeholder_text: str


@dataclass
class Appendix:
    name: str
    items: List[AppendixItem]


def setup_documents(source_doc: fitz.Document, appendices_items: List[AppendixItem]):
    for page_num, page in enumerate(source_doc):
        text = page.get_text("text")

        for item in appendices_items:
            if item.placeholder_text in text:
                item.position_in_source_doc = page_num
                break


def total_prev_len(current_name: str, appendices: List[AppendixItem]):
    counter = 0
    for appendix in appendices:
        if current_name == appendix.placeholder_text:
            break
        counter = counter + appendix.doc.page_count
    return counter


def update_toc(initial_toc, appendices: List[Appendix]):
    updated_toc = []
    appendixes_items = [
        item for appendix in appendices for item in appendix.items]
    appendixes_items = sorted(
        appendixes_items, key=lambda x: x.position_in_source_doc)

    for entry in initial_toc:
        level, title, page_num = entry

        for index, item in enumerate(appendixes_items):
            if title in item.placeholder_text:
                total_num = total_prev_len(
                    item.placeholder_text, appendixes_items)
                page_num = item.position_in_source_doc + \
                    total_num - index if total_num else item.position_in_source_doc

        updated_toc.append([level, title, page_num])

    for index, entry in enumerate(updated_toc):
        level, title, page_num = entry
        for appendix in appendices:
            if (title.lower() == appendix.name.lower()) and index != 0:
                page_num = updated_toc[index + 1][2] - \
                    1 if index + 1 < len(updated_toc) else page_num
                updated_toc[index] = [level, title, page_num]

    return updated_toc


def update_toc_text(doc: fitz.Document, initial_toc, updated_toc):
    for i, (level, title, old_page) in enumerate(initial_toc):
        new_page = updated_toc[i][2]

        if old_page != new_page:  # Only update if page number changed
            page = doc[2]
            x_equation = len(str(new_page)) - 2
            # for page_num in range(len(doc)):
            # page = doc[page_num]

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
            text_x = rect.x0 + 1.5 - (x_equation*5)
            # Vertically centered
            text_y = rect.y0 + ((rect.y1 - rect.y0) / 1.35)
            # Ensure text is written in the cleared area
            page.insert_text((text_x, text_y),
                             f"{new_page}",
                             fontname="Helvetica-Bold" if level == 1 else "Helvetica",
                             fontsize=11,
                             color=(0, 0, 0))

    return doc


def update_page_numbers(doc: fitz.Document):
    totla_pages = source_doc.page_count

    def update_page(page, text_to_replace):
        x_equation = len(text_to_replace) - 7
        text_instances = page.search_for("[page_#]")
        if not text_instances:
            return

        rect = text_instances[-1]

        # 1. Erase old placeholder text (draw white rectangle)
        shape = page.new_shape()
        shape.draw_rect(rect)
        shape.finish(width=0, fill=(1, 1, 1), color=(1, 1, 1))
        shape.commit()

        # Fill the area with white color manually
        page.draw_rect(rect, fill=(1, 1, 1), color=(1, 1, 1), width=0)

        # Left-aligned with the old text
        text_x = rect.x0 + 8 - (x_equation*5)
        # Vertically centered
        text_y = rect.y0 + ((rect.y1 - rect.y0) / 1.35)
        # Ensure text is written in the cleared area
        page.insert_text((text_x, text_y), text_to_replace,
                         fontsize=9, color=(0, 0, 0))

    for page_count in range(0, doc.page_count):
        page = doc[page_count]
        text_to_replace = f"{page_count + 1} of {totla_pages}"
        update_page(page, text_to_replace)


def process_merge(source_doc: fitz.Document, appendices: List[Appendix]):
    initial_toc = source_doc.get_toc(simple=True)
    appendixes_items = [
        item for appendix in appendices for item in appendix.items]
    setup_documents(source_doc, appendixes_items)
    appendixes_items = sorted(
        appendixes_items, key=lambda x: x.position_in_source_doc, reverse=True)
    for appendixes_item in appendixes_items:
        source_doc.delete_page(appendixes_item.position_in_source_doc)
        source_doc.insert_pdf(
            appendixes_item.doc, start_at=appendixes_item.position_in_source_doc)
    updated_toc = update_toc(initial_toc, appendices)
    source_doc = update_toc_text(source_doc, initial_toc, updated_toc)
    source_doc.set_toc(updated_toc)
    update_page_numbers(source_doc)
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
    for apendix in appendices:
        item_objs = []
        for item in apendix["items"]:
            item_objs.append(
                AppendixItem(doc=fitz.open(f"{INPUT_DIR}/{item['file']}"),
                             position_in_source_doc=0,
                             placeholder_text=item["placeholder"]))
        appendice_objs.append(Appendix(
            name=apendix["name"],
            items=item_objs
        ))
    process_merge(source_doc, appendice_objs)

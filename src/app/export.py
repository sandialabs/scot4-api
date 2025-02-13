import uuid
import json
from os import path, remove
from typing import Union, Any

from sqlalchemy.orm import Session
from tabulate import tabulate
from tempfile import gettempdir
from markdownify import markdownify
from xhtml2pdf import pisa
from pdf2docx import Converter

from app import crud
from app.models import Entry, Alert, Entity, Signature
from app.enums import TargetTypeEnum, ExportFormatEnum


def fmt_table(obj: list[dict]):
    table = ""
    if obj != []:
        if isinstance(obj[0], dict):
            table = tabulate(obj, headers="keys", tablefmt="unsafehtml")
        else:
            table = ", ".join(obj)
    return table


def fmt_sources_tags(obj: Any, obj_dict: dict):
    if hasattr(obj, "sources"):
        obj_dict["sources"] = ", ".join([a.name for a in obj.sources])
    if hasattr(obj, "tags"):
        obj_dict["tags"] = ", ".join([a.name for a in obj.tags])


def fmt_promoted_to_from(obj: Any, obj_dict: dict):
    if hasattr(obj, "promoted_to_targets"):
        obj_dict["promoted to"] = ", ".join([f"{a.p1_type.value}: {a.p1_id}" for a in obj.promoted_to_targets])
        del obj_dict["promoted to targets"]
    if hasattr(obj, "promoted_from_sources"):
        obj_dict["promoted from"] = ", ".join([f"{a.p0_type.value}: {a.p0_id}" for a in obj.promoted_from_sources])
        del obj_dict["promoted from sources"]


def fmt_alert(alert: Alert):
    alert_obj = alert.as_dict(pretty_keys=True, enum_value=True)
    fmt_promoted_to_from(alert, alert_obj)
    # no need to keep the alertgroup stuff around
    del alert_obj["alertgroup"]
    # make alert data its own column in cell
    for cell in alert.data_cells:
        # skip sparkline
        if "sparkline" in cell:
            continue
        try:
            alert_obj[cell] = fmt_table(json.loads(alert.data[cell]))
        except Exception:
            alert_obj[cell] = alert.data[cell]
    return alert_obj


def fmt_entries(db: Session, obj: Union[list[Entry], list[dict]], from_entry: bool = False):
    journal = ""
    if obj != []:
        for entry in obj:
            if not from_entry:
                if isinstance(entry, dict):
                    journal += f"<h5>[{entry['id']}] {entry['owner']} @ {entry['modified']} - {entry['tlp']}</h5>"
                else:
                    journal += f"<h5>[{entry.id}] {entry.owner} @ {entry.modified} - {entry.tlp}</h5>"
            if isinstance(entry, dict):
                entry_data = entry.get("entry_data", {})
            else:
                entry_data = entry.entry_data or {}

            if "html" in entry_data.keys():
                journal += f"<div>{entry.entry_data['html']}</div>"
            if "markdown" in entry_data.keys():
                journal = "<div><table><thead><tr>"
                rows = entry.entry_data['markdown'].splitlines()
                for column in rows[0].split("|")[1:-1]:
                    journal += f"<td>{column.strip()}</td>"
                journal += "</tr><thead><tbody>"
                for row in rows[2:]:
                    journal += "<tr>"
                    for column in row.split("|")[1:-1]:
                        journal += f"<td>{column.strip()}</td>"
                    journal += "</tr>"
                journal += "</tbody></table></div>"

            for source in entry_data.get("promotion_sources", []):
                if hasattr(crud, source["type"]):
                    crud_type = getattr(crud, source["type"])
                    crud_obj = crud_type.get(db, source["id"])
                    if hasattr(crud_obj, "entries"):
                        journal += f"<p>Promoted from {source['type']} {source['id']}</p>{fmt_entries(db, crud_obj.entries, True)}"
                    elif source["type"] == "alert":
                        journal += f"<p>Promoted from {source['type']} {source['id']}</p>{fmt_alert(crud_obj)}"
            if isinstance(entry, dict):
                for child_entry in entry.get("child_entries", []):
                    journal += f"<h5>[{child_entry['id']}] {child_entry['owner']} @ {child_entry['modified']} - {child_entry['tlp']}</h5>"
                    journal += f"<div>{child_entry['entry_data']['html']}</div>"
            else:
                for child_entry in entry.child_entries:
                    journal += f"<h5>[{child_entry.id}] {child_entry.owner} @ {child_entry.modified} - {child_entry.tlp}</h5>"
                    journal += f"<div>{child_entry.entry_data['html']}</div>"
    else:
        journal = ""
    return journal


def fmt_signatures(db: Session, obj: list[Signature], from_guide: bool = False):
    sigs = []
    guides = ""
    for signature in obj:
        signature_obj = signature.as_dict(pretty_keys=True, enum_value=True)
        fmt_sources_tags(signature, signature_obj)
        del signature_obj["entries"]
        del signature_obj["data"]
        if not from_guide:
            for guide in signature_obj.get("associated guides", []):
                guides += f"<p>Assoicated Guide ${guide['id']}</p>{fmt_entries(db, guide.get('entries'))}"
        del signature_obj["associated guides"]
        for cell in signature.data:
            signature_obj[cell] = signature.data[cell]
        sigs.append(signature_obj)
    return sigs, guides


def fmt_column_table(obj: dict):
    table = "<table>"
    for key, value in obj.items():
        table += f"<tr><td>{key}</td><td>{value}</td></tr>"
    return table + "</table>"


def fmt_enrichments(obj: list[dict]):
    if obj != []:
        for enrichment in obj:
            tmp_data = ""
            if "data" in enrichment.keys():
                if "markdown" in enrichment["data"].keys():
                    table = "<table><thead><tr>"
                    rows = enrichment['data']['markdown'].splitlines()
                    for column in rows[0].split("|")[1:-1]:
                        table += f"<td>{column.strip()}</td>"
                    table += "</tr><thead><tbody>"
                    for row in rows[2:]:
                        table += "<tr>"
                        for column in row.split("|")[1:-1]:
                            table += f"<td>{column.strip()}</td>"
                        table += "</tr>"
                    table += "</tbody></table>"
                    tmp_data += f"<div>{table}</div>"
                if "plaintext" in enrichment["data"].keys():
                    tmp_data += enrichment["data"]['plaintext']
                if "timeline" in enrichment["data"].keys():
                    tmp_data += f"<p>Timeline</p>{fmt_table(enrichment['data']['timeline'])}"
                if "counts" in enrichment["data"].keys():
                    tmp_data += f"<p>Counts</p>{fmt_column_table(enrichment['data']['counts'])}"
                if "unxformed" in enrichment["data"].keys():
                    enrichment["data"]["unxformed"] = fmt_column_table(enrichment["data"]["unxformed"])
                if enrichment["enrichment class"] == "jsontree":
                    tmp_data = fmt_column_table(enrichment["data"])
            enrichment["data"] = tmp_data
        return tabulate(obj, headers="keys", tablefmt="unsafehtml")
    else:
        return ""


def export_object(db: Session, _obj: Any, target_type: TargetTypeEnum, format: ExportFormatEnum, pretty_name: str) -> str:
    # convert it to a dict for easier conversion
    entries = {}
    _obj_dict = _obj.as_dict(pretty_keys=True, enum_value=True)
    # update the classes object to table if any
    if hasattr(_obj, "classes"):
        _obj_dict["classes"] = fmt_table(_obj_dict["classes"])

    # format tags/sources and promoted objects to tables
    fmt_sources_tags(_obj, _obj_dict)
    fmt_promoted_to_from(_obj, _obj_dict)

    # do table specific formatting
    if target_type == TargetTypeEnum.alertgroup:
        # convert the alerts to their own table
        entries["Alerts"] = []
        del _obj_dict["alerts"]
        for alert in _obj.alerts:
            entries["Alerts"].append(fmt_alert(alert))
        # format any signatures and guides
        entries["Signatures"], guides = fmt_signatures(db, _obj.associated_signatures)
        if guides != "":
            entries["Guides"] = guides
        del _obj_dict["associated signatures"]
    elif target_type == TargetTypeEnum.entity:
        # add entity appearances
        _obj_dict["enrichments"] = fmt_enrichments(_obj.enrichments)
        _obj_dict["classes"] = fmt_table(_obj.classes)
        entries["Appearances"] = []
        appearances = crud.entity.retrieve_entity_links_for_flair_pane(db, _obj.id, 0, None)
        appearances["alert_appearances"] = fmt_table(appearances["alert_appearances"])
        appearances["event_appearances"] = fmt_table(appearances["event_appearances"])
        appearances["intel_appearances"] = fmt_table(appearances["intel_appearances"])
        appearances["dispatch_appearances"] = fmt_table(appearances["dispatch_appearances"])
        appearances["product_appearances"] = fmt_table(appearances["product_appearances"])
        appearances["incident_appearances"] = fmt_table(appearances["incident_appearances"])
    elif target_type == TargetTypeEnum.guide:
        # format signatures and ignore guide
        entries["Signatures"], _ = fmt_signatures(db, crud.guide.get_signatures_for(db, _obj.id), True)
        _obj_dict["data"] = fmt_column_table(_obj_dict["data"])
    elif target_type == TargetTypeEnum.pivot:
        # make sure to get the entity types and classes
        entity_types = []
        for entity_type in _obj.entity_types:
            entity_dict = entity_type.as_dict(pretty_keys=True, enum_value=True)
            del entity_dict["entities"]
            entity_types.append(entity_dict)
        entries["Entity Types"] = fmt_table(entity_types)
        entries["Entity Classes"] = fmt_table([a.as_dict(pretty_keys=True, enum_value=True) for a in _obj.entity_classes])
    elif target_type == TargetTypeEnum.entry:
        # remove any child entries from table as it will only be in journal section
        entries["Journal"] = fmt_entries(db, [_obj], True)
        del _obj_dict["entry data"]
        del _obj_dict["child entries"]
    elif target_type == TargetTypeEnum.signature:
        # ignore the signature and get guide information
        _, guides = fmt_signatures(db, [_obj])
        _obj_dict["data"] = fmt_column_table(_obj.data)
        del _obj_dict["associated guides"]
        if guides != "":
            entries["Guides"] = guides
    elif target_type == TargetTypeEnum.incident:
        _obj_dict["data"] = fmt_column_table(_obj.data)

    # if the object has entries add them to the Journal Section
    if hasattr(_obj, "entries"):
        journal = fmt_entries(db, _obj.entries)
        if str != "":
            entries["Journal"] = journal
        del _obj_dict["entries"]

    # get any assoicated entities
    _entities, count = crud.entity.retrieve_element_entities(
        db_session=db, source_id=_obj.id, source_type=target_type
    )
    if count > 0:
        entries["Entities"] = []
        for entity in _entities:
            # maker sure everything is either a table or dict
            entity_dict = entity.as_dict(pretty_keys=True, enum_value=True)
            entity_dict["classes"] = fmt_table(entity_dict["classes"])
            entity_dict["enrichments"] = fmt_enrichments(entity_dict["enrichments"])
            entity_dict["summaries"] = fmt_table(entity_dict["summaries"])
            entity_dict["entries"] = fmt_entries(db, entity.entries)
            fmt_sources_tags(entity, entity_dict)
            entries["Entities"].append(entity_dict)

    # start creating the basic HTML document most of the css styles are to make sure things fit on a letter page format
    # can cause issues with tables as things tend to get squished
    html = ("<!DOCTYPE html><html><head><style>"
            "table {word-wrap: anywhere; -pdf-keep-in-frame-mode: shrink;}"
            "@page {size: letter portrait; @frame header_frame {-pdf-frame-content: header_content;text-align: center; font-size: 12px; margin-top: 5px;}"
            "@frame content_frame {margin: 0.5in;}}</style></head><body>")
    # create a table for the selected item data
    html += f"<h1>{pretty_name}</h1>{tabulate([_obj_dict], headers='keys', tablefmt='unsafehtml')}"
    if len(entries.keys()) != 0:
        for entry in entries:
            # for each key in the entries dict create a new section
            html += f"<h2>{entry}</h2>"
            # if the data is a list of dicts then it should be generated as a table
            if isinstance(entries[entry], list):
                html += tabulate(entries[entry], headers="keys", tablefmt="unsafehtml")
            # if the data is a dict then make it a one row table
            elif isinstance(entries[entry], dict):
                html += tabulate([entries[entry]], headers="keys", tablefmt="unsafehtml")
            # otherwise just print whats available, most likely this is already HTML formatted text
            else:
                html += entries[entry]
    # end the HTML document
    html += "</body></html>"
    # get the site settings for creating the classification header
    settings = crud.setting.get(db)
    # a temporary file to hold the document to send along with the the response
    tmp_file = path.join(gettempdir(), f"{uuid.uuid4()}.tmp")
    with open(tmp_file, "w+b") as tmp:
        # convert the HTML to markdown
        if format == ExportFormatEnum.md:
            # insert header
            media_type = "text/markdown"
            tmp.write(f"> <center>SCOT 4.1: {settings.site_name} - {settings.environment_level}</center>\n\n{markdownify(html)}".encode())
        # save the HTML
        elif format == ExportFormatEnum.html:
            media_type = "text/html"
            # insert header
            index = html.find("<body>")
            html = html[:index] + f"<div id='header_content' style='text-align: center; font-size: 12px;'>SCOT 4.1: {settings.site_name} - {settings.environment_level}</div>" + html[index:]
            tmp.write(html.encode())
        # convert the HTML to PDF do this also for WORD DOCX as its easier to convert from PDF later
        elif format == ExportFormatEnum.pdf or format == ExportFormatEnum.docx:
            media_type = "application/pdf"
            # insert header
            index = html.find("<body>")
            html = html[:index] + f"<div id='header_content' style='text-align: center; font-size: 12px;'>SCOT 4.1: {settings.site_name} - {settings.environment_level}</div>" + html[index:]
            pisa.CreatePDF(html, dest=tmp)

    # convert from PDF to DOCX
    if format == ExportFormatEnum.docx:
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        docx_file = f"{tmp_file}.docx"
        cv = Converter(tmp_file)
        cv.convert(docx_file)
        cv.close()
        remove(tmp_file)
        tmp_file = docx_file

    return tmp_file, media_type

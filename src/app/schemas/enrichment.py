from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field

from app.enums import EnrichmentClassEnum
from app.schemas.response import ResultBase


class EnrichmentBase(BaseModel):
    title: Annotated[str, Field(...)]
    entity_id: Annotated[int, Field(...)]
    enrichment_class: Annotated[EnrichmentClassEnum, Field(..., examples=[a.value for a in list(EnrichmentClassEnum)])]
    data: Annotated[dict, Field(...)]
    description: Annotated[str | None, Field(...)]


class EnrichmentCreate(EnrichmentBase):
    title: Annotated[str | None, Field(...)] = ""
    entity_id: Annotated[int | None, Field(...)] = None
    enrichment_class: Annotated[EnrichmentClassEnum, Field(..., examples=[a.value for a in list(EnrichmentClassEnum)])]
    data: Annotated[dict, Field(...)]
    description: Annotated[str | None, Field(...)] = ""


class EnrichmentUpdate(EnrichmentBase):
    title: Annotated[str, Field(...)] = ""
    entity_id: Annotated[int | None, Field(...)] = None
    enrichment_class: Annotated[EnrichmentClassEnum | None, Field(..., examples=[a.value for a in list(EnrichmentClassEnum)])] = None
    data: Annotated[dict | None, Field(...)] = None
    description: Annotated[str | None, Field(...)] = None


class Enrichment(EnrichmentBase, ResultBase):

    model_config = ConfigDict(from_attributes=True)


class PlainTextEnrichment(BaseModel, extra="allow"):
    plaintext: Annotated[str, Field(...)]


class MarkdownEnrichment(BaseModel, extra="allow"):
    markdown: Annotated[str, Field(...)]


class JsonTreeEnrichment(BaseModel, extra="allow"):
    pass


class ChartData(BaseModel, extra="allow"):
    labels: Annotated[list[str], Field(...)]
    datasets: Annotated[list, Field(...)]


class ChartsEnrichment(BaseModel, extra="allow"):
    chart_data: Annotated[ChartData, Field(...)]


enrichment_class_schema_map = {EnrichmentClassEnum.jsontree: JsonTreeEnrichment,
                               EnrichmentClassEnum.plaintext: PlainTextEnrichment,
                               EnrichmentClassEnum.markdown: MarkdownEnrichment,
                               EnrichmentClassEnum.linechart: ChartsEnrichment
                               }

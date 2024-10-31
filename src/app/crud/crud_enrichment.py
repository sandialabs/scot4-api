from app.crud.base import CRUDBase
from app.models.enrichment import Enrichment
from app.schemas.enrichment import EnrichmentCreate, EnrichmentUpdate


class CRUDEnrichment(CRUDBase[Enrichment, EnrichmentCreate, EnrichmentUpdate]):
    pass


enrichment = CRUDEnrichment(Enrichment)

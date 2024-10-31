from fastapi import APIRouter

from app.api.endpoints import (
    alert,
    alertgroup,
    apikey,
    appearance,
    audit,
    checklist,
    dispatch,
    entity,
    entity_class,
    entry,
    event,
    feed,
    file,
    flair,
    firehose,
    game,
    guide,
    handler,
    health,
    incident,
    intel,
    link,
    login,
    metric,
    permissions,
    product,
    promotion,
    role,
    settings,
    sigbody,
    signature,
    source,
    stat,
    tag,
    threat_model_items,
    users,
    search,
    notification,
    pivot,
    entity_type,
    vuln_feed,
    vuln_track
)

api_router = APIRouter()

api_router.include_router(login.router, tags=['login'])
api_router.include_router(settings.router, prefix='/settings', tags=['settings'])
api_router.include_router(users.router, prefix='/users', tags=['users'])
api_router.include_router(threat_model_items.router, prefix='/threat_model_item', tags=['threat_model_item'])
api_router.include_router(alertgroup.router, prefix='/alertgroup', tags=['alertgroup'])
api_router.include_router(alert.router, prefix='/alert', tags=['alert'])
api_router.include_router(role.router, prefix='/role', tags=['role'])
api_router.include_router(entity.router, prefix='/entity', tags=['entity'])
api_router.include_router(entry.router, prefix='/entry', tags=['entry'])
api_router.include_router(guide.router, prefix='/guide', tags=['guide'])
api_router.include_router(incident.router, prefix='/incident', tags=['incident'])
api_router.include_router(signature.router, prefix='/signature', tags=['signature'])
api_router.include_router(event.router, prefix='/event', tags=['event'])
api_router.include_router(permissions.router, prefix='/permissions', tags=['permissions'])
api_router.include_router(apikey.router, prefix='/apikey', tags=['apikey'])
api_router.include_router(appearance.router, prefix='/appearance', tags=['appearance'])
api_router.include_router(audit.router, prefix='/audit', tags=['audit'])
api_router.include_router(game.router, prefix='/game', tags=['game'])
api_router.include_router(metric.router, prefix='/metric', tags=['metric'])
api_router.include_router(intel.router, prefix='/intel', tags=['intel'])
api_router.include_router(link.router, prefix='/link', tags=['link'])
api_router.include_router(sigbody.router, prefix='/sigbody', tags=['sigbody'])
api_router.include_router(stat.router, prefix='/stat', tags=['stat'])
api_router.include_router(checklist.router, prefix='/checklist', tags=['checklist'])
api_router.include_router(dispatch.router, prefix='/dispatch', tags=['dispatch'])
api_router.include_router(feed.router, prefix='/feed', tags=['feed'])
api_router.include_router(source.router, prefix='/source', tags=['source'])
api_router.include_router(tag.router, prefix='/tag', tags=['tag'])
api_router.include_router(handler.router, prefix='/handler', tags=['handler'])
api_router.include_router(file.router, prefix='/file', tags=['file'])
api_router.include_router(promotion.router, prefix='/promotion', tags=['promotion'])
api_router.include_router(product.router, prefix='/product', tags=['product'])
api_router.include_router(entity_class.router, prefix='/entity_class', tags=['entity_class'])
api_router.include_router(flair.router, prefix='/flair', tags=['flair'])
api_router.include_router(pivot.router, prefix='/pivot', tags=['pivot'])
api_router.include_router(entity_type.router, prefix='/entity_type', tags=['entity_type'])
api_router.include_router(firehose.router, prefix='/firehose', tags=['firehose'])
api_router.include_router(search.router, prefix='/search', tags=['search'])
api_router.include_router(notification.router, prefix='/notification', tags=['notification'])
api_router.include_router(health.router, prefix='/health', tags=['health'])
api_router.include_router(vuln_feed.router, prefix='/vuln_feed', tags=['vuln_feed'])
api_router.include_router(vuln_track.router, prefix='/vuln_track', tags=['vuln_track'])

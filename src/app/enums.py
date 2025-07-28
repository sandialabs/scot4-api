import enum


class StatusEnum(enum.Enum):
    open = "open"
    promoted = "promoted"
    closed = "closed"


class TlpEnum(enum.Enum):
    unset = "unset"
    white = "white"
    green = "green"
    amber = "amber"
    red = "red"
    black = "black"
    clear = "clear"
    amber_strict = "amber_strict"


class EnrichmentClassEnum(enum.Enum):
    markdown = "markdown"
    linechart = "linechart"
    jsontree = "jsontree"
    plaintext = "plaintext"


class EntryClassEnum(enum.Enum):
    entry = "entry"
    summary = "summary"
    # All commented out are not planned for 4.0
    task = "task"
    promotion = "promotion"
    action = "action"


class StorageProviderEnum(enum.Enum):
    s3 = "s3"
    emc = "emc"
    disk = "disk"


class EntityStatusEnum(enum.Enum):
    tracked = "tracked"
    untracked = "untracked"


class EntityTypeStatusEnum(enum.Enum):
    active = "active"
    disabled = "disabled"


class GuideStatusEnum(enum.Enum):
    current = "current"
    outdated = "outdated"


class PriorityEnum(enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"


class TargetTypeEnum(enum.Enum):
    alert = "alert"
    alertgroup = "alertgroup"
    checklist = "checklist"
    dispatch = "dispatch"
    entity = "entity"
    entry = "entry"
    event = "event"
    file = "file"
    guide = "guide"
    incident = "incident"
    intel = "intel"
    product = "product"
    sigbody = "sigbody"
    signature = "signature"
    entity_class = "entity_class"
    entity_type = "entity_type"
    source = "source"
    special_metric = "special_metric"
    stat = "stat"
    tag = "tag"
    admin = "admin"
    threat_model_item = "threat_model_item"
    feed = "feed"
    pivot = "pivot"
    remote_flair = "remoteflair"
    vuln_feed = "vuln_feed"
    vuln_track = "vuln_track"
    none = None

    @classmethod
    def _missing_(cls, value):
        return TargetTypeEnum.none


class PermissionEnum(enum.Enum):
    read = "read"
    modify = "modify"
    delete = "delete"
    admin = "admin"


class QueueEnum(enum.Enum):
    flair = "/queue/flair"
    fetch = "/queue/fetch"
    phantom = "/queue/phantom"


class AuthTypeEnum(enum.Enum):
    ldap = "ldap"
    local = "local"
    aad = "aad"


class RemoteFlairStatusEnum(enum.Enum):
    requested = "requested"
    processing = "processing"
    ready = "ready"
    error = "error"
    reflair = "reflair"


class RemoteFlairSourceEnum(enum.Enum):
    browser = "browser"
    scrape = "scrape"


class ExportFormatEnum(enum.Enum):
    md = "md"
    html = "html"
    docx = "docx"
    pdf = "pdf"


class SpecialMetricEnum(enum.Enum):
    mttc = "mttc"
    mttr = "mttr"

    
class PopularityMetricEnum(enum.Enum):
    upvote = "upvote"
    downvote = "downvote"


class UserLinkEnum(enum.Enum):
    favorite = "favorite"
    subscription = "subscription"

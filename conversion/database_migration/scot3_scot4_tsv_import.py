import os

if __name__=="__main__":
    staging_directory = os.getenv('SCOT_MIGRATION_STAGING_DIRECTORY')
    
    util.import_table(f"{staging_directory}/links.csv", {"table": "links", "columns": ['created_date', 'modified_date', 'link_id', 'v0_type', 'v0_id', 'v1_type', 'v1_id'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     
    
    util.import_table(f"{staging_directory}/*_links.csv", {"table": "links", "columns": ['v0_type', 'v0_id', 'v1_type', 'v1_id'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     
    
    util.import_table(f"{staging_directory}/promotion_entry_permissions.csv", {"table": "object_permissions", "columns": ['role_id', 'target_type', 'target_id', 'permission'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     

    util.import_table(f"{staging_directory}/alert_permissions.csv", {"table": "object_permissions", "columns": ['role_id', 'target_type', 'target_id', 'permission'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     
    
    util.import_table(f"{staging_directory}/product_permissions.csv", {"table": "object_permissions", "columns": ['role_id', 'target_type', 'target_id', 'permission'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     
    
    util.import_table(f"{staging_directory}/signature_permissions.csv", {"table": "object_permissions", "columns": ['role_id', 'target_type', 'target_id', 'permission'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     

    util.import_table(f"{staging_directory}/entry_permissions.csv", {"table": "object_permissions", "columns": ['role_id', 'target_type', 'target_id', 'permission'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     
    
    util.import_table(f"{staging_directory}/event_permissions.csv", {"table": "object_permissions", "columns": ['role_id', 'target_type', 'target_id', 'permission'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     
    
    util.import_table(f"{staging_directory}/intel_permissions.csv", {"table": "object_permissions", "columns": ['role_id', 'target_type', 'target_id', 'permission'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     
    
    util.import_table(f"{staging_directory}/dispatch_permissions.csv", {"table": "object_permissions", "columns": ['role_id', 'target_type', 'target_id', 'permission'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     
    
    util.import_table(f"{staging_directory}/incident_permissions.csv", {"table": "object_permissions", "columns": ['role_id', 'target_type', 'target_id', 'permission'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     
    
    util.import_table(f"{staging_directory}/alertgroup_permissions.csv", {"table": "object_permissions", "columns": ['role_id', 'target_type', 'target_id', 'permission'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     
    
    util.import_table(f"{staging_directory}/promotions.csv", {"table": "promotions", "columns": ['p0_id', 'p0_type', 'p1_id', 'p1_type', 'created_date', 'modified_date'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     

    util.import_table(f"{staging_directory}/guide_permissions.csv", {"table": "object_permissions", "columns": ['role_id', 'target_type', 'target_id', 'permission'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     

    util.import_table(f"{staging_directory}/alert_data.csv", {"table": "alert_data", "columns": ['data_value', 'data_value_flaired', 'schema_key_id', 'alert_id'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 0, "showProgress": True})     
    
    util.import_table(f"{staging_directory}/alertgroup_schema_keys.csv", {"table": "alertgroup_schema_keys", "columns": ['schema_key_name', 'alertgroup_id', 'schema_key_order', 'schema_key_id'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     
    
    util.import_table(f"{staging_directory}/guides.csv", {"table": "guides", "columns": ['guide_id', 'owner', 'tlp', 'subject', 'created_date', 'modified_date', 'guide_data'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     

    util.import_table(f"{staging_directory}/alerts.csv", {"table": "alerts", "columns": ['created_date', 'modified_date', 'alert_id', 'owner', 'tlp', 'status', 'parsed', 'alertgroup_id'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     
    
    util.import_table(f"{staging_directory}/alertgroups.csv", {"table": "alertgroups", "columns": ['alertgroup_id', 'tlp', 'subject', 'created_date', 'modified_date', 'view_count'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     

    util.import_table(f"{staging_directory}/dispatch.csv", {"table": "dispatches", "columns": ['dispatches_id', 'tlp', 'owner', 'status', 'subject', 'created_date', 'modified_date'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     
    
    util.import_table(f"{staging_directory}/entity_data.csv", {"table": "entities", "columns": ['created_date', 'modified_date', 'entity_id', 'status', 'entity_value', 'type_id'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     
    
    util.import_table(f"{staging_directory}/entity_types.csv", {"table": "entity_types", "columns": ['entity_type_id', 'entity_type_name', 'created_date', 'modified_date'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     
    
    util.import_table(f"{staging_directory}/entries.csv", {"table": "entries", "columns": ['entry_id', 'parent_entry_id', 'tlp', 'owner', 'created_date', 'modified_date', 'target_type', 'target_id', 'entryclass', 'parsed', 'entry_data'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     
    
    util.import_table(f"{staging_directory}/promotion_entries.csv", {"table": "entries", "columns": ['owner', 'entry_id', 'target_type', 'target_id', 'created_date', 'modified_date', 'parsed', 'entry_data', 'entryclass'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     

    util.import_table(f"{staging_directory}/events.csv", {"table": "events", "columns": ['event_id', 'owner', 'status', 'subject', 'created_date', 'modified_date', 'tlp', 'view_count'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     
    
    util.import_table(f"{staging_directory}/incidents.csv", {"table": "incidents", "columns": ['incident_id', 'tlp', 'owner', 'status', 'subject', 'created_date', 'modified_date', 'incident_data', 'incident_data_ver', 'reported_date', 'discovered_date', 'occurred_date'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     
    
    util.import_table(f"{staging_directory}/intel.csv", {"table": "intels", "columns": ['intel_id', 'tlp', 'owner', 'status', 'subject', 'created_date', 'modified_date'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     
    
    util.import_table(f"{staging_directory}/signatures.csv", {"table": "signatures", "columns": ['signature_id', 'owner', 'status', 'signature_name', 'created_date', 'modified_date', 'tlp_enum', 'signature_data', 'latest_revision', 'signature_type', 'signature_description'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     

    util.import_table(f"{staging_directory}/products.csv", {"table": "products", "columns": ['products_id', 'tlp', 'owner', 'subject', 'created_date', 'modified_date'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     
    
    util.import_table(f"{staging_directory}/roles.csv", {"table": "roles", "columns": ['role_id', 'role_name', 'description', 'created_date', 'modified_date'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     
    
    util.import_table(f"{staging_directory}/handlers.csv", {"table": "handlers", "columns": ['handler_id', 'start_date', 'end_date', 'username', 'position', 'created_date', 'modified_date'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     

    util.import_table(f"{staging_directory}/sources.csv", {"table": "sources", "columns": ['source_id', 'source_name', 'description', 'created_date', 'modified_date'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})     
    
    util.import_table(f"{staging_directory}/tags.csv", {"table": "tags", "columns": ['tag_id', 'tag_name', 'description', 'created_date', 'modified_date'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True}) 

    util.import_table(f"{staging_directory}/enrichments.csv", {"table": "enrichments", "columns": ['created_date', 'modified_date', 'entity_id', 'enrichment_title', 'enrichment_class', 'enrichment_data'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})    
    
    util.import_table(f"{staging_directory}/entity_class_associations.csv", {"table": "entity_class_entity_association", "columns": ['entity_id', 'entity_class_id'], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})    

    if os.path.isfile("./games.csv"):
        util.import_table("./games.csv", { "table": "games", "columns": ["game_id", "game_name", "tooltip", "results", "created_date", "modified_date"], "dialect": "tsv", 'fieldsEscapedBy': '\t', 'fieldsEnclosedBy': "'", 'fieldsEscapedBy': '\0', 'linesTerminatedBy': "\n", "skipRows": 1, "showProgress": True})

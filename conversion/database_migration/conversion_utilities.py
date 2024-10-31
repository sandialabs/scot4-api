
def write_permission(thing=None, thing_type=None, role_lookup=None, permission_csv_writer=None):
    if thing.get('groups') is not None:
        for perm, roles in thing.get('groups').items():
            if roles is None:
                continue
            new_permissions = [[role_lookup[str(role).lower()], thing_type, thing.get('id'), perm] for role in roles if role_lookup.get(str(role)) is not None]
            permission_csv_writer.writerows(new_permissions)

            if perm == 'modify':
                ## Add the delete permission as well
                delete_perms = [[role_lookup[str(role).lower()], thing_type, thing.get('id'), 'delete'] for role in roles if role_lookup.get(str(role)) is not None]
                permission_csv_writer.writerows(delete_perms)
    else:
        return

def write_tag_source_links(thing=None, thing_type=None, tag_lookup=None, source_lookup=None, link_csv_writer=None):
        new_tag_links = [[thing_type, thing.get('id'), 'tag', tag_lookup[str(x).lower()]] for x in thing['tag'] if tag_lookup.get(str(x).lower()) is not None]
        new_source_links = [[thing_type, thing.get('id'), 'source', source_lookup[str(x).lower()]] for x in thing['source'] if source_lookup.get(str(x).lower()) is not None]
        link_csv_writer.writerows(new_tag_links)
        link_csv_writer.writerows(new_source_links)
        if thing_type == "signature":
            # Check if reference ID exists here
            target_data = thing.get('data').get('target')
            if target_data is not None:
                new_link = [thing_type, thing.get('id'), target_data['type'], target_data['id']]
                link_csv_writer.writerow(new_link)

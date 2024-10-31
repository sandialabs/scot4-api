from ldap3 import MOCK_SYNC, OFFLINE_SLAPD_2_4, Connection, Server
from ldap3.utils.dn import safe_rdn

from app import crud
from app.schemas.role import RoleCreate
from app.schemas.user import UserCreate

from .base import BaseAuthentication

"""
Abstraction of ldap auth
"""


class LdapAuthentication(BaseAuthentication):
    default_config = {
        "provider_name": "",
        "server": "",
        "bind_user": "",
        "bind_password": "",
        "test_user": "",
        "test_group": "",
        "username_attribute": "",
        "user_email_attribute": "",
        "user_full_name_attribute": "",
        "user_group_attribute": "",
        "user_base_dn": "",
        "user_filter": "",
        "group_base_dn": "",
        "group_filter": "",
        "group_member_attribute": "",
        "group_name_attribute": "",
        "group_autocreate": True,
    }

    config_name_pretty = {
        "provider_name": "Provider Name",
        "server": "Server",
        "bind_user": "Bind User",
        "bind_password": "Bind Password",
        "test_user": "Test User",
        "test_group": "Test Group",
        "username_attribute": "Username Attribute",
        "user_email_attribute": "User Email Attribute",
        "user_full_name_attribute": "User Full Name Attribute",
        "user_group_attribute": "User Group Attribute",
        "user_base_dn": "User Base DN",
        "user_filter": "User Filter",
        "group_base_dn": "Group Base DN",
        "group_filter": "Group Filter",
        "group_member_attribute": "Group Member Attribute",
        "group_name_attribute": "Group Name Attribute",
        "group_autocreate": "Auto-create Groups",
    }

    config_help = {
        "provider_name": "A name that identifies this authentication instance",
        "server": "The address of the LDAP server",
        "bind_user": "The user to bind as for lookups",
        "bind_password": "The password for the bind user",
        "test_user": "A user that can be looked up to test user queries",
        "test_group": "A group that can be looked up to test group queries",
        "username_attribute": "The ldap attribute containing a user's"
        ' username (default: "uid")',
        "user_email_attribute": "The ldap attribute containing a user's"
        " email address",
        "user_full_name_attribute": "The ldap attribute containing a"
        " user's full name",
        "user_group_attribute": "The ldap attribute on a user containing"
        " that user's group memberships",
        "user_base_dn": "The base search domain for users",
        "user_filter": "The filter to use when searching for users",
        "group_base_dn": "The base search domain for groups",
        "group_filter": "The filter to use when searching for groups",
        "group_member_attribute": "The ldap attribute on a group"
        " containing that group's users",
        "group_name_attribute": "The ldap attribute containing the group's"
        ' name (default: "cn")',
        "group_autocreate": "When set, all discovered ldap groups will be"
        " created as roles in SCOT",
    }

    def __init__(self, config):
        # Start connection
        self.server = Server(config["server"])
        self.mock_data = config.get("mock_data", None)
        # Make a fake connection if mock data provided
        if self.mock_data is not None:
            self.server = Server(config["server"], get_info=OFFLINE_SLAPD_2_4)
            conn = Connection(self.server, client_strategy=MOCK_SYNC)
            for item in self.mock_data:
                conn.strategy.add_entry(item, self.mock_data[item])
            self.bind_user = None
            self.bind_password = None
        # Bind user was specified
        elif "bind_user" in config and config["bind_user"]:
            conn = Connection(
                self.server,
                user=config["bind_user"],
                password=config.get("bind_password", None),
                raise_exceptions=True,
            )
            self.bind_user = config["bind_user"]
            self.bind_password = config.get("bind_password", None)
        # Anonymous bind
        else:
            conn = Connection(self.server, raise_exceptions=True)
            self.bind_user = None
            self.bind_password = None
        conn.bind()
        # Required search settings
        self.user_base_dn = config.get("user_base_dn", "")
        self.user_filter = config.get("user_filter", None)
        self.username_attribute = config.get("username_attribute", "uid")
        self.user_email_attribute = config.get("user_email_attribute", None)
        self.user_name_attribute = config.get("user_full_name_attribute", None)
        self.user_group_attribute = config.get("user_group_attribute", None)
        self.group_base_dn = config.get("group_base_dn", None)
        self.group_filter = config.get("group_filter", None)
        self.group_autocreate = config.get("group_autocreate", True)
        self.group_member_attribute = config.get("group_member_attribute", None)
        self.group_name_attribute = config.get("group_name_attribute", "cn")
        # Test connection if test user/group given
        if "test_user" in config and config["test_user"]:
            search_filter = "(%s=%s)" % (self.username_attribute, config["test_user"])
            if self.user_filter:
                search_filter = "(&%s%s)" % (search_filter, self.user_filter)
            conn.search(
                self.user_base_dn, search_filter, attributes=[self.username_attribute]
            )
            if len(conn.entries) == 0:
                raise ValueError(
                    "LDAP login for test user %s failed" % config["test_user"]
                )
        if "test_group" in config and config["test_group"]:
            search_filter = "(%s=%s)" % (
                self.group_name_attribute,
                config["test_group"],
            )
            if self.group_filter:
                search_filter = "(&%s%s)" % (search_filter, self.group_filter)
            conn.search(
                self.group_base_dn,
                search_filter,
                attributes=[self.group_name_attribute],
            )
            if len(conn.entries) == 0:
                raise ValueError(
                    "LDAP login for test group %s failed" % config["test_group"]
                )
        # Close connection after testing
        conn.unbind()

    def authenticate_password(self, username, password, user=None):
        conn = Connection(self.server, user=self.bind_user, password=self.bind_password)
        # Make a fake connection if mock data provided
        if self.mock_data is not None:
            conn = Connection(self.server, client_strategy=MOCK_SYNC)
            for item in self.mock_data:
                conn.strategy.add_entry(item, self.mock_data[item])
        # Stuff we're going to get from the user's entry if we can
        user_email = None
        user_groups = None
        user_full_name = ""
        if not conn.bind():
            raise ValueError(
                "Error binding to ldap: %s %s"
                % (conn.result.get("description"), conn.result.get("message"))
            )
        search_attributes = [self.username_attribute]
        if self.user_email_attribute:
            search_attributes.append(self.user_email_attribute)
        if self.user_group_attribute:
            search_attributes.append(self.user_group_attribute)
        if self.user_name_attribute:
            search_attributes.append(self.user_name_attribute)
        # Use custom search filter if given
        search_filter = "(%s=%s)" % (self.username_attribute, username)
        if self.user_filter:
            search_filter = "(&%s%s)" % (search_filter, self.user_filter)
        conn.search(self.user_base_dn, search_filter, attributes=search_attributes)
        if len(conn.entries) > 0:
            # Always use first result - undefined behavior if matches more than
            # one user
            user_entry = conn.entries[0]
            user_groups = []
            # Store user info
            user_dn = user_entry.entry_dn
            if self.user_email_attribute:
                user_email = user_entry[self.user_email_attribute].value
            # If we have groups and a filter configured, do another search
            # to find them. Also do this if group attributes on users aren"t
            # configured.
            user_group_names = []
            if (
                self.group_member_attribute
                and self.group_base_dn
                and (self.group_filter or not self.user_group_attribute)
            ):
                attributes = [self.group_member_attribute, self.group_name_attribute]
                search_filter = "(%s=%s)" % (self.group_member_attribute, user_dn)
                if self.group_filter:
                    search_filter = "(&%s%s)" % (search_filter, self.group_filter)
                conn.search(self.group_base_dn, search_filter, attributes=attributes)
                # Pull names out of groups (if we got any)
                user_group_names = [
                    group[self.group_name_attribute].value for group in conn.entries
                ]
            # Otherwise, pull all groups out of the user entry
            elif self.user_group_attribute:
                user_groups = user_entry[self.user_group_attribute].values
                user_group_names = []
                for user_group in user_groups:
                    dns = safe_rdn(user_group, decompose=True)
                    user_group_names.extend(
                        [dn[1] for dn in dns if dn[0] == self.group_name_attribute]
                    )
            if self.user_name_attribute:
                user_full_name = user_entry[self.user_name_attribute].value
            # Check password
            if conn.rebind(user=user_dn, password=password):
                return UserCreate(
                    username=username,
                    email=user_email,
                    fullname=user_full_name,
                    roles=user_group_names,
                )
            # Incorrect password
            else:
                return None
        # User not found
        else:
            return None

    def start_external_authenticate(self, username, user=None):
        raise NotImplementedError()

    def authenticate_token(self, token, user=None):
        raise NotImplementedError()

    def update_ldap_groups(self, db):  # pragma: no cover
        """
        Updates SCOT groups with groups from ldap
        Returns True if updates were successful, false otherwise
        Not current used, instead groups are created from the list of group
        names on the user returned from authenticate_password
        """
        if self.group_base_dn is None or self.group_member_attribute is None:
            return False
        conn = Connection(self.server, user=self.bind_user, password=self.bind_password)
        # Search for groups that meet our criteria
        if not conn.bind():
            return False
        attributes = [self.group_member_attribute, self.group_name_attribute]
        conn.search(self.group_base_dn, self.group_filter, attributes=attributes)
        if len(conn.entries) == 0:
            return False
        # For each group, find the equivalent SCOT group and make sure
        # it has the right users
        # TODO: Currently quite inefficient if all groups already exist,
        #           change to bulk query instead of one at a time?
        for entry in conn.entries:
            if (
                self.group_name_attribute not in entry
                or self.group_member_attribute not in entry
            ):
                continue
            group_name = entry[self.group_name_attribute].value
            group_members = entry[self.group_member_attribute].values
            # Find username of each group member by finding the rdn with the
            # username attribute
            group_usernames = []
            for member in group_members:
                rdns = safe_rdn(member, decompose=True)
                for rdn in rdns:
                    if rdn[0] == self.username_attribute:
                        group_usernames.append(rdn[1])
                        break
            scot_group = crud.role.get_role_by_name(db, group_name)
            if not scot_group:
                if self.group_autocreate:
                    # Create group if it doesn"t exist
                    role_create = RoleCreate(name=group_name)
                    scot_group = crud.role.create(db, obj_in=role_create)
                else:
                    continue
            scot_group_usernames = [u.username for u in scot_group.users]
            # Find all users who aren't in the scot group and should be
            users_to_add = set(group_usernames) - set(scot_group_usernames)
            # Find all users who are in the scot group and shouldn't be
            users_to_remove = set(scot_group_usernames) - set(group_usernames)
            # Add/remove users
            db_users_to_add = crud.user.bulk_get_by_usernames(db, users_to_add)
            for adduser in db_users_to_add:
                if adduser is not None:
                    scot_group.users.append(adduser)
            scot_group.users = list(
                filter(lambda u: u.username not in users_to_remove, scot_group.users)
            )
            # Add to db commit
            db.add(scot_group)
        return True

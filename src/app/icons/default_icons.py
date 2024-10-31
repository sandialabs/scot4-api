default_icons = [
    {
        "icon": "$vuetify.icons.scanner",
        "name": "scanner",
        "display_name": "Scanner",
        "description": "This entity class is usually applied to an external IP address that is known or suspected to be guilty of scanning infrastructure."
    },

    {
        "icon": "$vuetify.icons.sandia_thunderbird",
        "name": "sandia",
        "display_name": "Sandia National Labs",
        "description": "This entity class is applied to entities beloning to Sandia National Labs."
    },
    {
        "icon": "$vuetify.icons.firewall",
        "name": "firewall",
        "display_name": "Firewall Block",
        "description": "This entity class is usually applied to an external IP address that has been blocked by ingress firewalls."
    },
    {
        "icon": "$vuetify.icons.anonymous_ip",
        "name": "anonymous_ip",
        "display_name": "Anonymous IP",
        "description": "This entity class is usually applied to an external IP address that has been labeled as an anonymous ip address."
    },
    {
        "icon": "mdi-vpn",
        "name": "anonymous_vpn",
        "display_name": "Anonymous VPN",
        "description": "This entity class is usually applied to an external IP address that has been labeled as known VPN exit node."
    },
    {
        "icon": "mdi-satellite-uplink",
        "name": "hosting_provider",
        "display_name": "Hosting Provider",
        "description": "This entity class is usually applied to an external IP address that has been labeled as belonging to a known hosting provider."
    },
    {
        "icon": "mdi-cloud-arrow-down-outline",
        "name": "public_proxy",
        "display_name": "Public Proxy",
        "description": "This entity class is usually applied to an external IP address that has been labeled as belonging to a public proxy."
    },
    {
        "icon": "mdi-vector-triangle",
        "name": "tor_exit_node",
        "display_name": "Tor Node",
        "description": "This entity class is usually applied to an external IP address that has been labeled as belonging to a tor exit node."
    },
    {
        "icon": "mdi-pi-hole",
        "name": "blackhole",
        "display_name": "DNS Blackhole",
        "description": "This entity class is usually applied to an external IP  that has been blackholed by our DNS resolvers."
    },
    {
        "icon": "mdi-cancel",
        "name": "proxyblock",
        "display_name": "Proxy Block",
        "description": "This entity class is usually applied to an external IP that has been blocked by our forward proxies."
    },
    {
        "icon": "mdi-binoculars",
        "name": "watchlist",
        "display_name": "Watchlist",
        "description": "This entity class is usually applied to an external IP that has been added to our threat intel watchlists."
    },
    {
        "icon": "mdi-human-greeting",
        "name": "whitelist",
        "display_name": "Allow List",
        "description": "This entity class is usually applied to an external IP that has been added to our ingress firewall allow lists."
    },
    {
        "icon": "mdi-account-check",
        "name": "user_principal",
        "display_name": "Azure AD User Principal",
        "description": "This entity class is applied to a user principal identity from Active Directory. Entity accounts are technically considered user principals in Active Directory, but are not labeled with this entity class for clarity's sake."
    },
    {
        "icon": "mdi-card-account-mail-outline",
        "name": "email_alias",
        "display_name": "Email Alias",
        "description": "This entity class is applied to an SMTP alias for a user principal in Active Directory. NOTE that entity accounts are considered user principals."
    },
    {
        "icon": "mdi-robot",
        "name": "entity_account",
        "display_name": "Entity Account",
        "description": "This entity class is applied to a user in active directory listed as an 'entity account' or non-human user."
    }

]

# Local development

Use `python manage.py migrate --settings=realmproof.settings_local` and `python manage.py runserver --settings=realmproof.settings_local`. The explicit local module generates a persistent private key (mode 0600 on Unix), uses SQLite and enables debug. Never select it on a public server. Production continues to use realmproof.settings and requires an injected secret and PostgreSQL. Do not commit the local key. Removing it invalidates existing signed sessions.

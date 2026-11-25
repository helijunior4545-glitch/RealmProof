# Local demo

Run `python manage.py setup_local_demo --settings=realmproof.settings_local` then `python manage.py runserver --settings=realmproof.settings_local`. Credentials are derived from the private local key and remain server-side. The setup command refuses production settings and preserves existing scenarios. The Gno CLI is still required for actual local Gno execution.

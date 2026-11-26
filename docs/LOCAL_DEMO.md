# Local demo

Run `python manage.py setup_local_demo --settings=realmproof.settings_local` then `python manage.py runserver --settings=realmproof.settings_local`. Credentials are derived from the private local key and remain server-side. The setup command refuses production settings and preserves existing scenarios. The Gno CLI is still required for actual local Gno execution.

For in-place scenario selection and report tabs, build the React bundle with
`cd frontend && npm install && npm run build`. Rebuild after pulling changes
to the frontend. Without a bundle, the landing renders its demo cards and
submits the selected scenario as a standard page form.

# PostgreSQL

PostgreSQL 18. Once installed, create databases and users from **Databases → PostgreSQL**.

- The superuser name and password are generated at install time; you can see them from the Databases page.
- The port listens on 127.0.0.1 only, unless you tick **External access** when installing. Apps reach it over the internal Docker network.
- Major versions do not upgrade in place: moving from 18 to a later major version is a dump and restore.

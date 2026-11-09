# MySQL

MySQL 8.4 LTS. Once installed, create databases and users from **Databases → MySQL**, and pick it when you create a PHP website.

- The root password is generated at install time; you can see and change it from the Databases page.
- The port listens on 127.0.0.1 only, unless you tick **External access** when installing. Websites and other apps reach it over the internal Docker network, so they do not need external access.
- Data lives in the app's `data` folder and is included in dPanel backups of the app.

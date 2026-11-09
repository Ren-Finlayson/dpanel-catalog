# MariaDB

MariaDB 11.8 LTS, a drop-in alternative to MySQL. Once installed, create databases and users from **Databases → MySQL** (MariaDB is listed there too), and pick it when you create a PHP website.

- The root password is generated at install time; you can see and change it from the Databases page.
- The port listens on 127.0.0.1 only, unless you tick **External access** when installing. Websites and other apps reach it over the internal Docker network.
- MySQL and MariaDB both default to port 3306, so pick a different port if you install both.

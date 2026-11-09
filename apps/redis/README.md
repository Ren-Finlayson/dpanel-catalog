# Redis

Redis 8, an in-memory key-value store used for caching, sessions and queues. Once installed, browse and manage keys from **Databases → Redis**.

- A password is always set (generated at install time). dPanel's catalogue does not allow a password-free Redis, because every container on the shared Docker network could otherwise read and change it.
- The port listens on 127.0.0.1 only, unless you tick **External access** when installing.
- Redis 8 is licensed AGPLv3, RSALv2 or SSPLv1, at your choice.

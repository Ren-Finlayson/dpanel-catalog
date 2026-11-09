# dPanel app catalogue

The curated, signed app store for dPanel. Every app here is reviewed, every image is pinned by digest, and dPanel refuses anything this repository did not sign.

## How the trust chain works

1. `tools/build.py` turns `apps/` into a static site: an index (`1panel.json.zip`), each app's icon, and each version's compose file and package.
2. The index records a SHA-256 for every one of those files.
3. CI signs the index with [minisign](https://jedisct1.github.io/minisign/).
4. dPanel verifies the signature against its trusted keys, then checks every file it downloads against the hash in the index. Older indexes are rejected, so a mirror cannot roll you back.

The host serving the files is not trusted. GitHub Pages, your own forge or a plain web server all work the same.

## Adding an app

```
apps/<key>/
  data.yml              app metadata; additionalProperties.key must equal <key>
  README.md             shown on the app's page
  logo.png              square PNG icon
  <version>/
    data.yml            install form (additionalProperties.formFields)
    docker-compose.yml  uses ${CONTAINER_NAME}, ${HOST_IP}, ${PANEL_APP_PORT_HTTP}, network 1panel-network
    ...                 any other files the app needs (scripts/, config templates)
```

The build fails, and so does CI, if:

- an image is not pinned as `name@sha256:<digest>`. Keep the human-readable tag in a comment above it.
- a service is `privileged`.
- an app uses a tag that is not defined in `tags.yml`.
- a version is missing `docker-compose.yml` or `data.yml`, or the app is missing `logo.png`.

CI also scans every image with Trivy and blocks critical vulnerabilities that already have a fix.

Prefer apps with no default password. If an app creates its admin on first visit, say so in its README.

The CyberChef, IT-Tools and Uptime Kuma logos are still plain colour placeholders; replace them with each project's real icon.

## Tags

`tags.yml` defines the store's filter tags and their translations. It is where the catalogue taxonomy lives.

## Building locally

```sh
pip install pyyaml
SOURCE_DATE_EPOCH=$(git log -1 --format=%ct) python3 tools/build.py --base-url http://localhost:8000
```

Builds are reproducible: the same sources and timestamp produce byte-identical files.

## Publishing (one-time setup)

1. Generate the CI signing key. Keep a backup of the secret key somewhere offline.
   ```sh
   minisign -G -W -p dpanel-catalog.pub -s dpanel-catalog.key
   ```
2. In the repository settings add the secret `MINISIGN_SECRET_KEY` (contents of `dpanel-catalog.key`) and the variable `CATALOG_BASE_URL` (for GitHub Pages: `https://<owner>.github.io/<repo>`).
3. Enable Pages with "GitHub Actions" as the source.
4. Put the public key into dPanel's `agent/cmd/server/conf/app.yaml`:
   ```yaml
   app_repo_url: "https://<owner>.github.io/<repo>"
   catalog_keys:
     - "RW..."   # second line of dpanel-catalog.pub
   ```

Each push to `main` then builds, scans, signs and publishes.

### Rotating the key or moving hosts

- New key: add its public key to `catalog_keys` alongside the old one and ship that dPanel release. Then switch CI to the new secret key, and drop the old public key in a later release.
- New host: publish to the new place and change `app_repo_url`. Signatures don't depend on the host, so nothing else changes.

`tools/publish.sh` is plain shell, so the same pipeline runs on Forgejo or Gitea Actions; only the final Pages upload step is GitHub-specific.

## Credits and licence

The OpenResty, MySQL, MariaDB, PostgreSQL and Redis definitions are adapted from [1Panel's app store](https://github.com/1Panel-dev/appstore) (GPL-3.0): images pinned by digest, ports bound to loopback by default, a password required for Redis, the paid WAF add-on and the build-from-source context left out, and the text translated and rewritten. The catalogue is GPL-3.0, like dPanel; each app keeps its own licence.

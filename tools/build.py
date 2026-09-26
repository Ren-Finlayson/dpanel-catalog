#!/usr/bin/env python3
"""Build the dPanel app catalogue from apps/ into a static site under dist/.

Output layout (what dPanel's app store expects under base.app_repo_url):

  <mode>/1panel.json.version.txt          lastModified, used as the "anything new?" check
  <mode>/1panel.json.zip                  the index; sign it -> 1panel.json.zip.minisig
  <mode>/1panel/<key>/logo.png
  <mode>/1panel/<key>/<version>/docker-compose.yml
  <mode>/1panel/<key>/<version>/<key>-<version>.tar.gz

The index lists a SHA-256 for every icon, compose file and package, so the
single signature over the index covers everything dPanel downloads.
Archives are reproducible: same sources + same --last-modified = same bytes.
"""
import argparse
import gzip
import hashlib
import io
import json
import os
import re
import sys
import tarfile
import zipfile

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PINNED_IMAGE = re.compile(r"^\S+@sha256:[0-9a-f]{64}$")
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)


class CatalogError(Exception):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def check_compose(path):
    """Every service must pin its image by digest; tags can be moved under you."""
    compose = read_yaml(path)
    services = compose.get("services") or {}
    if not services:
        raise CatalogError(f"{path}: no services defined")
    for name, svc in services.items():
        image = (svc or {}).get("image", "")
        if not PINNED_IMAGE.match(image):
            raise CatalogError(f"{path}: service '{name}' image '{image}' is not pinned by @sha256 digest")
        if (svc or {}).get("privileged"):
            raise CatalogError(f"{path}: service '{name}' is privileged; not allowed in the curated catalogue")


def package_version(app_dir, key, version) -> bytes:
    """tar.gz of <key>/<version>/..., with fixed metadata so hashes are reproducible."""
    src = os.path.join(app_dir, version)
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tar:
            entries = []
            for dirpath, dirnames, filenames in os.walk(src):
                dirnames.sort()
                for d in dirnames:
                    entries.append(os.path.join(dirpath, d))
                for fn in sorted(filenames):
                    entries.append(os.path.join(dirpath, fn))
            for full in [src] + entries:
                rel = os.path.relpath(full, src)
                arc = f"{key}/{version}" if rel == "." else f"{key}/{version}/{rel.replace(os.sep, '/')}"
                info = tar.gettarinfo(full, arcname=arc)
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                info.mtime = 0
                # Decide modes from names, not the build machine's filesystem, to stay reproducible.
                is_exec = info.isfile() and full.endswith(".sh")
                info.mode = 0o755 if info.isdir() or is_exec else 0o644
                if info.isfile():
                    with open(full, "rb") as f:
                        tar.addfile(info, f)
                else:
                    tar.addfile(info)
    return buf.getvalue()


def write(path, data: bytes):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def build(base_url, mode, out, last_modified):
    base_url = base_url.rstrip("/")
    site = os.path.join(out, mode)
    remote = f"{base_url}/{mode}/1panel"
    tags = read_yaml(os.path.join(ROOT, "tags.yml")).get("tags", [])
    tag_keys = {t["key"] for t in tags}

    apps = []
    apps_root = os.path.join(ROOT, "apps")
    for key in sorted(os.listdir(apps_root)):
        app_dir = os.path.join(apps_root, key)
        if not os.path.isdir(app_dir) or key.startswith("."):
            continue
        meta = read_yaml(os.path.join(app_dir, "data.yml"))
        props = meta.get("additionalProperties") or {}
        if props.get("key") != key:
            raise CatalogError(f"apps/{key}/data.yml: additionalProperties.key must be '{key}'")
        unknown = set(props.get("tags") or []) - tag_keys
        if unknown:
            raise CatalogError(f"apps/{key}: tags {sorted(unknown)} are not defined in tags.yml")

        logo_path = os.path.join(app_dir, "logo.png")
        if not os.path.isfile(logo_path):
            raise CatalogError(f"apps/{key}: logo.png is missing")
        with open(logo_path, "rb") as f:
            logo = f.read()
        write(os.path.join(site, "1panel", key, "logo.png"), logo)

        readme_path = os.path.join(app_dir, "README.md")
        readme = open(readme_path, encoding="utf-8").read() if os.path.isfile(readme_path) else ""

        versions = []
        for version in sorted(os.listdir(app_dir)):
            vdir = os.path.join(app_dir, version)
            if not os.path.isdir(vdir):
                continue
            compose_path = os.path.join(vdir, "docker-compose.yml")
            if not os.path.isfile(compose_path) or not os.path.isfile(os.path.join(vdir, "data.yml")):
                raise CatalogError(f"apps/{key}/{version}: needs docker-compose.yml and data.yml")
            check_compose(compose_path)
            with open(compose_path, "rb") as f:
                compose = f.read()
            package = package_version(app_dir, key, version)
            vout = os.path.join(site, "1panel", key, version)
            write(os.path.join(vout, "docker-compose.yml"), compose)
            write(os.path.join(vout, f"{key}-{version}.tar.gz"), package)
            form = read_yaml(os.path.join(vdir, "data.yml")).get("additionalProperties") or {}
            versions.append({
                "name": version,
                "lastModified": last_modified,
                "downloadUrl": f"{remote}/{key}/{version}/{key}-{version}.tar.gz",
                "composeSha256": sha256(compose),
                "packageSha256": sha256(package),
                "additionalProperties": form,
            })
        if not versions:
            raise CatalogError(f"apps/{key}: no versions")

        apps.append({
            "name": meta.get("name") or props.get("name") or key,
            "icon": f"{remote}/{key}/logo.png",
            "iconSha256": sha256(logo),
            "readMe": readme,
            "lastModified": last_modified,
            "additionalProperties": props,
            "versions": versions,
        })

    index = {
        "valid": True,
        "violations": [],
        "lastModified": last_modified,
        "apps": apps,
        "additionalProperties": {"tags": tags, "version": ""},
    }
    index_json = json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as z:
        info = zipfile.ZipInfo("1panel.json", date_time=ZIP_EPOCH)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        z.writestr(info, index_json)
    write(os.path.join(site, "1panel.json.zip"), zbuf.getvalue())
    write(os.path.join(site, "1panel.json.version.txt"), str(last_modified).encode())
    return apps


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base-url", required=True, help="public URL dPanel uses as base.app_repo_url")
    p.add_argument("--mode", default="stable", help="dPanel base.mode this build serves (default: stable)")
    p.add_argument("--out", default=os.path.join(ROOT, "dist"))
    p.add_argument("--last-modified", type=int,
                   default=int(os.environ.get("SOURCE_DATE_EPOCH", "0")) or None,
                   help="catalogue timestamp; must only go up (defaults to $SOURCE_DATE_EPOCH)")
    args = p.parse_args()
    if not args.last_modified:
        p.error("--last-modified or SOURCE_DATE_EPOCH is required (use the last commit time)")
    try:
        apps = build(args.base_url, args.mode, args.out, args.last_modified)
    except CatalogError as e:
        print(f"catalogue error: {e}", file=sys.stderr)
        sys.exit(1)
    count = sum(len(a["versions"]) for a in apps)
    print(f"built {len(apps)} apps, {count} versions -> {os.path.join(args.out, args.mode)}")


if __name__ == "__main__":
    main()

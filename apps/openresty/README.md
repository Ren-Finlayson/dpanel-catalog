# OpenResty

OpenResty is NGINX bundled with LuaJIT and a set of well-tested modules. dPanel's **Websites** section runs on it: static sites, reverse proxies, PHP sites, SSL certificates and redirects are all OpenResty configuration that dPanel writes for you.

Install it once (only one copy is allowed), then create websites from **Websites**.

## Notes

- It uses host networking, so it binds the HTTP and HTTPS ports you choose (80 and 443 by default) directly on the server. Make sure nothing else is using them.
- Website files and per-site configuration live in the website directory you choose at install time. A relative path is placed under the dPanel data directory.
- The image is the one 1Panel builds, pinned by digest. It is the official OpenResty build plus a few extra modules (GeoIP2, DAV, substitutions, RTMP) that dPanel's module manager knows about.
- dPanel's catalogue leaves out 1Panel's paid WAF add-on, so no Lua WAF runs on your requests.

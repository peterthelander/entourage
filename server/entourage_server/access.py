"""Single-owner authentication; browser credentials are supplied at runtime."""

import hmac
import ipaddress
from urllib.parse import urlsplit

from starlette.responses import JSONResponse


class AccessControl:
    def __init__(self, app, token, origins, tailscale_login="", trust_local=False):
        self.app, self.token, self.origins = app, token, origins
        self.tailscale_login, self.trust_local = tailscale_login, trust_local
        self.hosts = {urlsplit(origin).netloc.lower() for origin in origins}

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope["path"].startswith("/api/v1/") or scope["path"] == "/api/v1/health":
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        origin = headers.get(b"origin", b"").decode()
        if origin and origin not in self.origins:
            return await JSONResponse(status_code=403, content={"error": {"code": "origin_forbidden", "message": "Origin is not allowed."}})(scope, receive, send)
        authorization = headers.get(b"authorization", b"").decode()
        token_ok = bool(self.token) and hmac.compare_digest(authorization.encode(), ("Bearer " + self.token).encode())
        try:
            peer = ipaddress.ip_address((scope.get("client") or ("",))[0])
            loopback = peer.is_loopback
        except ValueError:
            loopback = False
        host = headers.get(b"host", b"").decode().lower()
        login = headers.get(b"tailscale-user-login", b"").decode()
        tailscale_ok = (loopback and self.trust_local and bool(self.tailscale_login)
                        and login == self.tailscale_login and host in self.hosts)
        direct_local = (loopback and self.trust_local and host.split(":")[0] in ("localhost", "127.0.0.1")
                        and not any(key in headers for key in (b"x-forwarded-for", b"x-forwarded-host", b"x-forwarded-proto", b"tailscale-user-login")))
        if (self.token or self.trust_local) and not (token_ok or tailscale_ok or direct_local):
            return await JSONResponse(status_code=401, content={"error": {"code": "unauthorized", "message": "Connect through your private Tailscale link or this computer's localhost address."}})(scope, receive, send)
        return await self.app(scope, receive, send)

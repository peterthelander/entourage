import asyncio
import unittest

import httpx

from entourage_server.web_pages import public_url, read_web_page, resolve_public
from unittest.mock import AsyncMock, patch


class PageTests(unittest.IsolatedAsyncioTestCase):
    async def read(self, handler, args=None, resolver=None):
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await read_web_page(args or {"url": "https://example.com/calendar"}, client=client,
                                       resolver=resolver or AsyncMock(return_value="93.184.215.14"))

    async def test_reads_text_and_source_links_without_executing_or_copying_scripts(self):
        def respond(request):
            self.assertEqual(request.url.host, "93.184.215.14")
            self.assertEqual(request.headers["host"], "example.com")
            self.assertEqual(request.extensions["sni_hostname"], "example.com")
            self.assertNotIn("authorization", request.headers)
            return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, text='''
                <title>Official calendar</title><style>secret styles</style>
                <script>private script</script><nav>Home</nav><main>
                <h2>October 20</h2><a href="/events/dawkins">Richard Dawkins</a> 7 PM
                <a href="/events/knights">The Knights</a> 7:30 PM
                <div hidden>hidden data</div><div aria-hidden="true">aria hidden</div>
                <a href="javascript:alert(1)">bad link</a></main>''')
        found = await self.read(respond)
        self.assertEqual(found["status"], "read")
        self.assertEqual(found["url"], "https://example.com/calendar")
        self.assertEqual(found["title"], "Official calendar")
        self.assertIn("Richard Dawkins", found["text"])
        for text in ("private script", "secret styles", "hidden data", "aria hidden"):
            self.assertNotIn(text, found["text"])
        self.assertEqual(found["links"][0]["url"], "https://example.com/events/dawkins")
        self.assertEqual(len(found["links"]), 2)

    async def test_redirects_resolve_and_pin_each_host_and_reject_private_destination(self):
        resolver = AsyncMock(side_effect=["93.184.215.14", ValueError("Private")])
        calls = []
        def respond(request):
            calls.append(request)
            return httpx.Response(302, headers={"location": "http://127.0.0.1/secret"})
        result = await self.read(respond, resolver=resolver)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(len(calls), 1)
        resolver.assert_awaited_with("127.0.0.1", 80)

    async def test_dns_rejects_local_reserved_and_mixed_answers(self):
        for addresses in (["127.0.0.1"], ["10.0.0.1"], ["169.254.169.254"], ["::1"],
                          ["::ffff:127.0.0.1"], ["93.184.215.14", "192.168.1.1"]):
            rows = [(None, None, None, None, (ip, 443)) for ip in addresses]
            with patch.object(asyncio.get_running_loop(), "getaddrinfo", new=AsyncMock(return_value=rows)):
                with self.assertRaises(ValueError):
                    await resolve_public("example.com", 443)

    async def test_relative_redirects_preserve_source_host_and_are_bounded(self):
        requests = []
        def respond(request):
            requests.append(request)
            if len(requests) == 1:
                return httpx.Response(302, headers={"location": "/new"})
            return httpx.Response(200, headers={"content-type": "text/plain"}, text="Verified page text")
        result = await self.read(respond)
        self.assertEqual(result["url"], "https://example.com/new")
        self.assertEqual(requests[1].headers["host"], "example.com")
        result = await self.read(lambda r: httpx.Response(302, headers={"location": "/loop"}))
        self.assertEqual(result["status"], "unavailable")

    async def test_blocked_binary_large_and_timeout_are_not_reads(self):
        for status in (403, 429, 503):
            found = await self.read(lambda r: httpx.Response(status, text="raw private server diagnostic"))
            self.assertEqual(found["status"], "unavailable")
            self.assertNotIn("text", found)
            self.assertNotIn("raw private", str(found))
        for mime, body in (("application/pdf", b"pdf"), ("text/html", b"x" * (1024 * 1024 + 1))):
            found = await self.read(lambda r: httpx.Response(200, headers={"content-type": mime}, content=body))
            self.assertEqual(found["status"], "unavailable")
        def timeout(request):
            raise httpx.ReadTimeout("private endpoint detail")
        self.assertEqual((await self.read(timeout))["status"], "unavailable")
        shell = await self.read(lambda r: httpx.Response(200, headers={"content-type": "text/html"}, text="<script>renderCalendar()</script>"))
        self.assertEqual(shell["status"], "unavailable")

    async def test_redirect_does_not_forward_site_cookies(self):
        def respond(request):
            self.assertNotIn("cookie", request.headers)
            if request.url.path == "/calendar":
                return httpx.Response(302, headers={"location": "/page", "set-cookie": "session=website-only; Path=/"})
            return httpx.Response(200, headers={"content-type": "text/plain"}, text="Calendar")
        self.assertEqual((await self.read(respond))["status"], "read")

    async def test_long_text_is_paginated_and_find_returns_context(self):
        text = "a" * 9000 + "October 20\nRichard Dawkins 7 PM" + "b" * 9000
        respond = lambda r: httpx.Response(200, headers={"content-type": "text/plain"}, text=text)
        first = await self.read(respond)
        self.assertEqual(first["next_offset"], 8000)
        self.assertTrue(first["text_truncated"])
        second = await self.read(respond, {"url": "https://example.com/calendar", "offset": first["next_offset"]})
        self.assertIn("Richard Dawkins", second["text"])
        match = await self.read(respond, {"url": "https://example.com/calendar", "find": "October 20"})
        self.assertTrue(match["find_matched"])
        self.assertIn("Richard Dawkins", match["text"])

    def test_invalid_urls(self):
        for value in ("file:///secret", "https://user:password@example.com", "http://example.com:8000", "https://example.com\n/secret"):
            with self.assertRaises((ValueError, httpx.InvalidURL)):
                public_url(value)

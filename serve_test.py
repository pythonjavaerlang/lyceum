"""Smoke test: serve dist/ and fetch key pages, fragments, and assets."""
import http.server, socketserver, threading, urllib.request
from pathlib import Path

DIST = Path(__file__).resolve().parent / "dist"
PORT = 8798
handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=str(DIST), **k)
httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()

paths = [
    "/", "/fragment.html", "/sitemap.xml", "/robots.txt",
    "/about/", "/about/fragment.html",
    "/enrolling/", "/transparency/", "/camp/", "/edu-prg/",
    "/student-groups/", "/structure/", "/regulations/",
    "/media/site.css", "/media/site.js",
    "/media/images/logo.jpg", "/media/images/image01.jpg",
    "/media/statute.pdf", "/og/index.jpg",
]
bad = []
for p in paths:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{p}", timeout=5) as r:
            code = r.status
    except Exception as e:
        bad.append((p, str(e))); continue
    if code != 200: bad.append((p, code))
    print(f"{code}  {p}")
httpd.shutdown()
print("\n=== RESULT ===")
if bad:
    print("FAILURES:", bad); raise SystemExit(1)
print(f"ALL {len(paths)} REQUESTS 200 OK")

"""Local demo shop: python -m shopping_assistant.demo_shop."""
import argparse
from decimal import Decimal, InvalidOperation
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import secrets
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parent.parent
ORIGIN = "http://127.0.0.1:8765"
SEED = ROOT / "demo_shop/products.json"

STYLE = """
*{box-sizing:border-box}body{margin:0;background:#f6f5f1;color:#202c29;font:15px/1.6 system-ui,sans-serif}a{color:inherit}header{border-bottom:1px solid #dedfd8;background:#fff}nav{max-width:1180px;margin:auto;display:flex;justify-content:space-between;align-items:center;padding:20px 24px}.brand{font-size:24px;font-weight:800;letter-spacing:-1px;text-decoration:none}.brand span{color:#477b5b}nav a:last-child{font-size:13px}main{max-width:1180px;margin:auto;padding:38px 24px 60px}.eyebrow{color:#54745e;text-transform:uppercase;letter-spacing:2px;font-size:11px;font-weight:800}h1{font-size:clamp(32px,5vw,52px);line-height:1.12;letter-spacing:-2px;margin:12px 0 16px}h2{font-size:19px;line-height:1.4;margin:12px 0 6px}p{color:#63716b}.hero{display:flex;gap:30px;justify-content:space-between;align-items:center;margin-bottom:40px}.hero p{max-width:570px}.badge{border:1px solid #d9dfd3;border-radius:100px;padding:8px 16px;font-size:12px;white-space:nowrap}.bar{display:flex;justify-content:space-between;border-top:1px solid #dedfd8;padding:18px 0;font-size:13px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px}.thumbnail{background:white;border:1px solid #e4e6de;border-radius:16px;overflow:hidden}.art{background:#eef0ea;padding:20px 35px 6px}.art svg{width:100%;height:175px}.body{padding:20px}.title{text-decoration:none}.title:hover{text-decoration:underline}.tag{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#627466}.description{font-size:13px;min-height:65px}.price{font-size:25px;font-weight:750;letter-spacing:-1px}.currency{font-size:11px;color:#78847c;margin-left:6px}.detail{max-width:690px;margin:25px auto}.editor{background:white;border-radius:16px;border:1px solid #dedfd8;padding:24px}.row{display:grid;grid-template-columns:1fr 150px 95px;gap:16px;align-items:center;padding:16px 0;border-bottom:1px solid #eee}.row:last-child{border:0}input{width:100%;border:1px solid #bcc9be;border-radius:8px;padding:10px;font:inherit}button,.button{background:#2f5b43;color:white;border:0;border-radius:8px;padding:11px 18px;font:600 13px system-ui;cursor:pointer;text-decoration:none}button:hover{background:#204330}.reset{background:#fff;color:#334c3c;border:1px solid #b8c5b9}.notice{padding:12px 18px;background:#e4efdf;border-radius:9px;margin-bottom:20px}.muted{font-size:12px;color:#758077}footer{max-width:1180px;margin:auto;padding:24px;border-top:1px solid #dedfd8;color:#758077;font-size:12px}:focus-visible{outline:3px solid #b68337;outline-offset:3px}@media(max-width:850px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.hero{display:block}.badge{display:inline-block}}@media(max-width:550px){.grid{grid-template-columns:1fr}.row{grid-template-columns:1fr 100px}.row button{grid-column:2}.hero{margin-bottom:24px}main{padding:24px 16px}.editor{padding:16px}}
"""


def illustration(product):
    color = escape(product["color"])
    return f'''<div class="art"><svg viewBox="0 0 320 200" role="img" aria-label="Illustration of {escape(product['name'])}"><ellipse cx="160" cy="179" rx="128" ry="9" fill="#d5dbd1"/><rect x="60" y="25" width="200" height="135" rx="9" fill="#384341"/><rect x="67" y="32" width="186" height="120" rx="4" fill="{color}"/><path d="M67 120 Q140 30 253 80 V152 H67Z" fill="white" opacity=".16"/><circle cx="209" cy="65" r="24" fill="white" opacity=".26"/><path d="M60 160 H260 L292 176 Q292 181 280 182 H40 Q28 181 28 176Z" fill="#aeb9b5"/><path d="M134 160 H187 L191 166 H130Z" fill="#7c8b85"/></svg></div>'''


def card(product):
    return f'''<article class="thumbnail">{illustration(product)}<div class="body"><span class="tag">{escape(product['tag'])}</span><h2><a class="title" href="/product/{product['id']}">{escape(product['name'])}</a></h2><p class="description">{escape(product['description'])}</p><meta itemprop="priceCurrency" content="USD"><span class="price" itemprop="price">${product['price']}</span><span class="currency">USD</span></div></article>'''


def page(title, body):
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(title)} · Fieldwork</title><style>{STYLE}</style></head><body><header><nav><a class="brand" href="/">fieldwork<span> .</span></a><a href="/admin">Demo controls ↗</a></nav></header><main>{body}</main><footer>Fieldwork demo store · Fictional products and prices · No purchases or payments</footer></body></html>'''


class ShopServer(HTTPServer):
    def __init__(self, address, data_path):
        self.data_path = Path(data_path)
        self.token = secrets.token_urlsafe(32)
        super().__init__(address, ShopHandler)

    def products(self):
        return json.loads((self.data_path if self.data_path.exists() else SEED).read_text())

    def save(self, products):
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.data_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(products, indent=2) + "\n")
        temporary.replace(self.data_path)


class ShopHandler(BaseHTTPRequestHandler):
    def reply(self, status, body):
        encoded = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(encoded)

    def valid_host(self):
        return self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}"

    def do_GET(self):
        if not self.valid_host():
            return self.reply(403, "Use the printed 127.0.0.1 URL.")
        products = self.server.products()
        if self.path in ("/", "/laptops", "/laptops/"):
            body = '''<section class="hero"><div><div class="eyebrow">Thoughtfully selected tech</div><h1>A little less searching.<br>A lot more possibility.</h1><p>Find a laptop for whatever comes next. Explore lightweight companions, creative workhorses, and everyday essentials.</p></div><span class="badge">The laptop collection · 10 picks</span></section><div class="bar"><strong>All laptops</strong><span>Prices in USD</span></div><section class="grid">'''
            return self.reply(200, page("Laptops", body + "".join(map(card, products)) + "</section>"))
        if self.path.startswith("/product/"):
            product = next((p for p in products if self.path == f"/product/{p['id']}"), None)
            if product:
                return self.reply(200, page(product["name"], '<a href="/">← All laptops</a><div class="detail">' + card(product) + '</div>'))
        if self.path in ("/admin", "/admin?saved=1", "/admin?reset=1"):
            notice = '<div class="notice" role="status">Prices saved. The next fresh search will use these prices.</div>' if "saved" in self.path else '<div class="notice" role="status">Starting prices restored.</div>' if "reset" in self.path else ""
            body = '<div class="eyebrow">Demo controls</div><h1>Make the price drop.</h1><p>Change Atlas Air 14 from $950 to $750, then repeat your search for laptops under $800. Changes persist across restarts.</p>' + notice + '<section class="editor">'
            for p in products:
                body += f'''<form class="row" method="post" action="/admin/price"><input type="hidden" name="token" value="{self.server.token}"><input type="hidden" name="id" value="{p['id']}"><label for="price-{p['id']}"><strong>{escape(p['name'])}</strong><br><span class="muted">Price in USD</span></label><input id="price-{p['id']}" name="price" type="number" min="0" max="999999.99" step="0.01" required value="{p['price']}"><button>Save price</button></form>'''
            body += f'''</section><form method="post" action="/admin/reset" style="margin-top:24px"><input type="hidden" name="token" value="{self.server.token}"><button class="reset">Reset all demo prices</button> <a href="/" style="margin-left:20px">View shop →</a></form>'''
            return self.reply(200, page("Price editor", body))
        self.reply(404, page("Not found", '<h1>Page not found</h1><a href="/">Back to the shop</a>'))

    def do_POST(self):
        origin = f"http://127.0.0.1:{self.server.server_port}"
        if not self.valid_host() or self.headers.get("Origin", origin) != origin:
            return self.reply(403, "Only local shop forms can edit prices.")
        if self.path not in ("/admin/price", "/admin/reset"):
            return self.reply(404, "Not found")
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 4096:
                raise ValueError("Invalid form size")
            form = parse_qs(self.rfile.read(size).decode())
            if not secrets.compare_digest(form.get("token", [""])[0], self.server.token):
                return self.reply(403, "Expired or missing form token. Reload the editor.")
            if self.path == "/admin/reset":
                products = json.loads(SEED.read_text())
            else:
                price = Decimal(form["price"][0])
                if not price.is_finite() or not 0 <= price <= Decimal("999999.99") or price != price.quantize(Decimal("0.01")):
                    raise ValueError("Use a nonnegative USD price with at most two decimal places.")
                products = self.server.products()
                product = next((p for p in products if p["id"] == form["id"][0]), None)
                if product is None:
                    raise ValueError("Unknown product")
                product["price"] = f"{price:.2f}"
            self.server.save(products)
        except (ValueError, KeyError, InvalidOperation):
            return self.reply(400, page("Invalid price", '<h1>That price could not be saved.</h1><p>Enter a price between 0 and 999999.99 with at most two decimal places.</p><a href="/admin">Back to editor</a>'))
        except OSError:
            return self.reply(500, "Could not save prices. Check write access to the data file.")
        self.send_response(303)
        self.send_header("Location", "/admin?reset=1" if self.path.endswith("reset") else "/admin?saved=1")
        self.send_header("Content-Length", "0")
        self.end_headers()


def main():
    parser = argparse.ArgumentParser(description="Run the local Fieldwork demo shop")
    parser.add_argument("--data", type=Path, default=ROOT / "demo_shop/prices.local.json")
    args = parser.parse_args()
    # ponytail: one local editor; serial requests avoid concurrent JSON writes. Use a database for multi-user hosting.
    with ShopServer(("127.0.0.1", 8765), args.data) as server:
        print(f"Shop: {ORIGIN}/laptops\nPrice editor: {ORIGIN}/admin", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()

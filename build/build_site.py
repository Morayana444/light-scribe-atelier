"""Generate the static Light Scribe Atelier storefront from the catalog."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = json.loads((ROOT / "data" / "catalog.json").read_text())
FINE = json.loads((ROOT / "build" / "fineart.json").read_text())

import hashlib

DATA_VERSION = hashlib.sha1((ROOT / "data" / "catalog.json").read_bytes()).hexdigest()[:10]

DESIGNS = CATALOG["designs"]
PRODUCTS = CATALOG["products"]
CATS = CATALOG["categories"]

SHOP_ORIGIN = "https://lightscribeshop.myshopify.com"
BUY_NAME = "Light Scribe Atelier"

# hand-picked cinematic imagery (lifestyle mockups read as photography)
HERO_IMAGES = [
    "https://cdn.shopify.com/s/files/1/0569/0674/3881/files/throw-blanket-60x80-lifestyle-65fcad6b65dcc.jpg?v=1711058306",
]


def fine_items(name: str, n: int = 1) -> list[str]:
    data = FINE.get(name) or {}
    return [i["src"] for i in (data.get("items") or [])[:n]]


def hero_art() -> str:
    pool = fine_items("Special Edition", 1) or fine_items("Quantum Caliber", 1)
    if pool:
        return pool[0]
    for data in FINE.values():
        if data.get("items"):
            return data["items"][0]["src"]
    return HERO_IMAGES[0]


def fan_art() -> list[tuple[str, str, str]]:
    """(image, caption, href) for the three fanned prints in the hero."""
    wanted = ["BARTANA MIDAYA", "DAHARI MAORI SAYADA", "SOKRENA", "SILVADAYA", "NUDRAKA NADI", "INDAGALAPA"]
    picks: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for name in wanted:
        for prod in PRODUCTS:
            if prod["design"] != name or prod["design"] in seen:
                continue
            if "kimono" in prod["type"].lower():
                picks.append((prod["images"][0], prod["design"], f"artwork/{prod['designSlug']}.html"))
                seen.add(prod["design"])
                break
        if len(picks) == 3:
            break
    return picks[:3]

NAV = [
    ("Shop all", "shop.html"),
    ("Wearable Art", "collections/apparel.html"),
    ("Ritual Textiles", "collections/textiles.html"),
    ("Sacred Space", "collections/space.html"),
    ("Fine Art", "fine-art.html"),
    ("Healing", "healing.html"),
    ("The Artist", "about.html"),
]

TESTIMONIALS = [
    ("I was able to release and let go of things I wasn't even aware I was still holding on to.", "Tatijana"),
    ("I woke up this morning feeling lighter in my body than I had in many years.", "Kim"),
    ("The constant chronic pain in my back and hips was gone.", "Carrie"),
    ("After the activation, my boundaries felt much stronger.", "Kimberly"),
]


def esc(text: object) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def money(value: float) -> str:
    return f"${value:,.2f}"


def by_design(slug: str) -> list[dict]:
    return [p for p in PRODUCTS if p["designSlug"] == slug]


def img_count(p: dict) -> int:
    return len(p["images"])


def static_cards(products: list[dict], prefix: str = "") -> str:
    """Server-rendered product cards (crawlable, no JS needed)."""
    out = []
    for p in products:
        price = f"From {money(p['price'])}" if p["maxPrice"] > p["price"] else money(p["price"])
        out.append(
            f"""
        <article class="card reveal">
          <a class="card-media" href="{prefix}product.html?id={p['id']}" aria-label="{esc(p['title'])}">
            <img src="{p['image']}" alt="{esc(p['title'])}" loading="lazy" decoding="async">
            <span class="card-tag">{esc(p['type'])}</span>
            <span class="card-quick" data-add="{p['id']}">Add to bag</span>
          </a>
          <div class="card-body">
            <a class="card-design" href="{prefix}artwork/{p['designSlug']}.html">{esc(p['design'])}</a>
            <a class="card-title" href="{prefix}product.html?id={p['id']}">{esc(p['type'])}</a>
            <span class="card-price">{price}</span>
          </div>
        </article>"""
        )
    return "\n".join(out)


def layout(
    *,
    prefix: str,
    title: str,
    description: str,
    body: str,
    active: str = "",
    body_class: str = "",
    extra_head: str = "",
) -> str:
    nav_html = "\n".join(
        f'<a href="{prefix}{href}" class="{"active" if active == href else ""}">{label}</a>'
        for label, href in NAV
    )
    mobile_nav = "\n".join(
        f'<a href="{prefix}{href}">{label}</a>' for label, href in NAV
    )
    return f"""<!DOCTYPE html>
<html lang="en" data-base="{prefix}" data-v="{DATA_VERSION}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#08070a">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300&family=Jost:wght@200;300;400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{prefix}assets/css/site.css">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ctext y='24' x='6' font-size='22' fill='%23c9a86a'%3E%E2%9C%A6%3C/text%3E%3C/svg%3E">
{extra_head}
</head>
<body class="{body_class}">
<div class="glow glow-a"></div>
<div class="glow glow-b"></div>

<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="{prefix}index.html">
      <span class="brand-mark">Morayana Levy</span>
      <span class="brand-sub">Light Scribe Atelier</span>
    </a>
    <nav class="nav">{nav_html}</nav>
    <div class="header-tools">
      <button class="icon-btn menu-btn" aria-label="Open menu">
        <svg viewBox="0 0 24 24"><path d="M3 6h18M3 12h18M3 18h18"/></svg>
      </button>
      <button class="icon-btn" data-open-cart aria-label="Open bag">
        <svg viewBox="0 0 24 24"><path d="M6 8h12l-1 12H7L6 8Z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/></svg>
        <span class="cart-count">0</span>
      </button>
    </div>
  </div>
</header>

<div class="mobile-nav" id="mobileNav">
  <small>Light Scribe Atelier</small>
  {mobile_nav}
  <button class="link-arrow close-nav" style="align-self:flex-start;margin-top:1.5rem">Close</button>
</div>

{body}

<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div class="footer-brand">
        <span class="brand-mark">Morayana Levy</span>
        <p>Intergalactic divine art channeled from realms of higher consciousness — offered in loving support of humanity's evolution.</p>
      </div>
      <div>
        <h4>Shop</h4>
        <ul>
          <li><a href="{prefix}shop.html">All pieces</a></li>
          <li><a href="{prefix}collections/apparel.html">Wearable art</a></li>
          <li><a href="{prefix}collections/textiles.html">Ritual textiles</a></li>
          <li><a href="{prefix}collections/space.html">Sacred space</a></li>
          <li><a href="{prefix}collections/carry.html">Carry &amp; adorn</a></li>
        </ul>
      </div>
      <div>
        <h4>The Work</h4>
        <ul>
          <li><a href="{prefix}artwork/index.html">Browse transmissions</a></li>
          <li><a href="{prefix}fine-art.html">Fine art prints</a></li>
          <li><a href="https://www.lightscribeart.com" target="_blank" rel="noopener">Light Scribe Art gallery</a></li>
          <li><a href="{prefix}healing.html">42 Chakra Point scan</a></li>
        </ul>
      </div>
      <div>
        <h4>Connect</h4>
        <ul>
          <li><a href="https://morayana.com" target="_blank" rel="noopener">morayana.com</a></li>
          <li><a href="https://42chakrapoint.com" target="_blank" rel="noopener">42chakrapoint.com</a></li>
          <li><a href="mailto:contact@morayana.com">contact@morayana.com</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© 2026 Morayana Levy · Light Scribe Atelier</span>
      <span>All art channeled &amp; created by Morayana Levy · Made to order</span>
    </div>
  </div>
</footer>

<div class="drawer-scrim" id="cartScrim"></div>
<aside class="cart-drawer" id="cartDrawer" aria-label="Shopping bag">
  <div class="cart-head">
    <h2>Your bag</h2>
    <button class="icon-btn" id="cartClose" aria-label="Close bag">
      <svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg>
    </button>
  </div>
  <div class="cart-items" id="cartItems"></div>
  <div class="cart-foot">
    <div class="cart-total"><span>Subtotal</span><span id="cartTotal">$0.00</span></div>
    <a class="btn btn-block" id="checkoutBtn" href="#" target="_blank" rel="noopener">Continue to checkout</a>
    <p class="cart-note">Checkout is handled securely by Shopify. Each piece is printed to order and ships worldwide.</p>
  </div>
</aside>

<script src="{prefix}assets/js/site.js"></script>
</body>
</html>"""


def cat_card(slug: str, image: str) -> str:
    meta = CATS[slug]
    count = sum(1 for p in PRODUCTS if p["category"] == slug)
    return f"""
      <a class="coll-card reveal" href="collections/{slug}.html">
        <img src="{image}" alt="{esc(meta['label'])}" loading="lazy">
        <div class="coll-body">
          <span class="count">{count} pieces</span>
          <h3>{esc(meta['label'])}</h3>
          <p>{esc(meta['blurb'])}</p>
        </div>
      </a>"""


def build_index() -> str:
    counts = {c: sum(1 for p in PRODUCTS if p["category"] == c) for c in CATS}
    # one strong image per category, preferring rich scenes
    cat_images = {
        "apparel": next(
            (p["images"][0] for p in PRODUCTS if p["category"] == "apparel" and "kimono" in p["type"].lower()),
            PRODUCTS[0]["image"],
        ),
        "textiles": next(
            (p["images"][0] for p in PRODUCTS if p["category"] == "textiles" and "sherpa" in p["type"].lower()),
            PRODUCTS[0]["image"],
        ),
        "space": next(
            (p["images"][0] for p in PRODUCTS if p["category"] == "space"),
            PRODUCTS[0]["image"],
        ),
        "carry": next(
            (p["images"][0] for p in PRODUCTS if p["category"] == "carry"),
            PRODUCTS[0]["image"],
        ),
    }
    ticker_names = " ".join(f"<span>{esc(d['name'])}</span>" for d in DESIGNS[:14])
    ticker = ticker_names + ticker_names

    featured = []
    seen = set()
    for p in sorted(PRODUCTS, key=lambda x: -img_count(x)):
        if p["designSlug"] in seen:
            continue
        seen.add(p["designSlug"])
        featured.append(p)
        if len(featured) >= 8:
            break

    quotes = "".join(
        f'<blockquote class="reveal">“{esc(q)}”<footer>{esc(who)}</footer></blockquote>'
        for q, who in TESTIMONIALS[:3]
    )

    fine_cover = next(iter(FINE.values()))["items"][0]["src"] if FINE else ""
    hero = HERO_IMAGES[0]
    h_art = hero_art()
    fans = "".join(
        f"""
      <a class="fan-card fan-{i + 1}" href="{href}">
        <span class="fan-img"><img src="{src}" alt="{esc(caption)}" loading="lazy"></span>
        <figcaption>{esc(caption)}</figcaption>
      </a>"""
        for i, (src, caption, href) in enumerate(fan_art())
    )
    n_types = len({p["type"] for p in PRODUCTS})

    body = f"""
<section class="hero-ed">
  <div class="hero-ed-bg"><img src="{h_art}" alt="Channeled light language artwork by Morayana Levy"></div>
  <div class="wrap hero-ed-grid">
    <div>
      <span class="eyebrow">Light Scribe Atelier · Channeled Art</span>
      <h1 class="display">Art that <em>transmits</em></h1>
      <p class="hero-sub">Every image is received in light language from realms of higher consciousness — then printed onto pieces you can wear, wrap yourself in, and live beside.</p>
      <div class="hero-cta">
        <a class="btn" href="shop.html">Explore the collection</a>
        <a class="btn btn-ghost" href="artwork/index.html">Browse {len(DESIGNS)} transmissions</a>
      </div>
      <div class="hero-meta">
        <div><span>{len(DESIGNS)}</span><small>Channeled artworks</small></div>
        <div><span>{len(PRODUCTS)}</span><small>Pieces made to order</small></div>
        <div><span>{n_types}</span><small>Forms &amp; finishes</small></div>
      </div>
    </div>
    <div class="hero-fan">{fans}</div>
  </div>
</section>

<div class="ticker"><div class="ticker-track">{ticker}</div></div>

<section class="band">
  <div class="wrap">
    <div class="section-head">
      <div>
        <span class="eyebrow">The Collections</span>
        <h2 class="section-title">Choose how the codes <em style="font-style:italic;color:var(--gold-soft)">live with you</em></h2>
      </div>
      <p class="lede">Four ways to keep a transmission close — worn, wrapped, placed, carried. Each artwork exists across all of them.</p>
    </div>
    <div class="coll-grid">
      {cat_card('apparel', cat_images['apparel'])}
      {cat_card('textiles', cat_images['textiles'])}
      {cat_card('space', cat_images['space'])}
      {cat_card('carry', cat_images['carry'])}
    </div>
  </div>
</section>

<section class="band-tight">
  <div class="wrap">
    <div class="coll-grid">
      <a class="coll-card reveal" href="fine-art.html" style="aspect-ratio:16/10">
        <img src="{fine_cover}" alt="Fine art prints">
        <div class="coll-body">
          <span class="count">Archive</span>
          <h3>Fine art prints</h3>
          <p>Museum-grade metal and paper editions from the main gallery.</p>
        </div>
      </a>
      <a class="coll-card reveal" href="healing.html" style="aspect-ratio:16/10">
        <img src="{hero}" alt="42 Chakra Point healing">
        <div class="coll-body">
          <span class="count">The modality</span>
          <h3>42 Chakra Point Healing</h3>
          <p>A private energetic map of all 42 points, then a guided program of activations.</p>
        </div>
      </a>
    </div>
  </div>
</section>

<section class="band">
  <div class="wrap">
    <div class="section-head">
      <div>
        <span class="eyebrow">Selected pieces</span>
        <h2 class="section-title">Where to begin</h2>
      </div>
      <a class="link-arrow" href="shop.html">Shop all {len(PRODUCTS)} pieces</a>
    </div>
    <div class="product-grid">{static_cards(featured)}</div>
  </div>
</section>

<section class="band-tight">
  <div class="wrap">
    <div class="section-head">
      <div>
        <span class="eyebrow">By transmission</span>
        <h2 class="section-title">Browse the light language</h2>
      </div>
      <a class="link-arrow" href="artwork/index.html">All {len(DESIGNS)} artworks</a>
    </div>
    <div class="design-grid" data-design-grid data-limit="18"></div>
  </div>
</section>

<section class="band quote-band">
  <div class="wrap">
    <span class="eyebrow">In their words</span>
    <div class="quote-grid mt-2">{quotes}</div>
  </div>
</section>

<section class="band">
  <div class="wrap split">
    <div class="split-media reveal"><img src="{cat_images['textiles']}" alt="Channeled art textile"></div>
    <div class="reveal">
      <span class="eyebrow">The channel</span>
      <h2 class="section-title">Morayana Levy</h2>
      <p class="lede mt-1">Healer, channel and artist. Creator of 42 Chakra Point Healing and a ThetaHealing practitioner, Morayana receives each artwork as a living transmission — light language codes drawn from benevolent star lineages and printed so they can stay in your field.</p>
      <p class="lede mt-1">The wearable collection began as a way to keep the codes close: art you sleep under, move in, and carry through the day.</p>
      <div class="hero-cta" style="margin-top:2rem">
        <a class="btn btn-ghost" href="about.html">Read the story</a>
        <a class="btn btn-ghost" href="https://www.lightscribeart.com" target="_blank" rel="noopener">Fine art gallery</a>
      </div>
    </div>
  </div>
</section>

<section class="band-tight">
  <div class="wrap center">
    <span class="eyebrow">Work with Morayana</span>
    <h2 class="section-title mt-1">The 42 Chakra Point Energy Scan</h2>
    <p class="lede mt-1" style="margin-left:auto;margin-right:auto">A remote scan and private report mapping all 42 chakra points — where your energy is blocked, and the order in which to clear it.</p>
    <div class="hero-cta" style="justify-content:center">
      <a class="btn" href="https://42chakrapoint.com" target="_blank" rel="noopener">Explore the scan · $144</a>
      <a class="btn btn-ghost" href="https://morayana.com" target="_blank" rel="noopener">Live activations</a>
    </div>
  </div>
</section>
"""
    return layout(
        prefix="",
        title="Light Scribe Atelier · Channeled Art by Morayana Levy",
        description="Wearable art, ritual textiles and sacred objects printed with channeled light language artworks by Morayana Levy. Made to order, shipped worldwide.",
        body=body,
    )


def build_shop() -> str:
    chips = [f'<button class="chip active" data-cat="all">All</button>']
    for slug, meta in CATS.items():
        n = sum(1 for p in PRODUCTS if p["category"] == slug)
        chips.append(
            f'<button class="chip" data-cat="{slug}">{esc(meta["label"])}<small>{n}</small></button>'
        )
    chips.append(
        '<a class="chip" href="fine-art.html">Fine art prints</a>'
    )
    body = f"""
<section class="shop-head">
  <div class="wrap">
    <span class="eyebrow">The Atelier</span>
    <h1 class="display" style="font-size:clamp(2.6rem,6vw,4.6rem);margin:0.8rem 0 1rem">Shop all pieces</h1>
    <p class="lede">{len(PRODUCTS)} pieces across {len(DESIGNS)} channeled artworks — every one printed to order after you choose it.</p>
  </div>
</section>

<div class="filters">
  <div class="wrap filters-inner">
    <div class="chips">{"".join(chips)}</div>
    <div class="filter-right">
      <label class="search-field">
        <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="6"/><path d="M16 16l4 4"/></svg>
        <input id="shopSearch" type="search" placeholder="Search artwork or piece" aria-label="Search">
      </label>
      <div class="select-wrap">
        <select id="shopDesign" aria-label="Filter by artwork"><option value="">All artworks</option></select>
      </div>
      <div class="select-wrap">
        <select id="shopSort" aria-label="Sort">
          <option value="featured">Featured</option>
          <option value="price-asc">Price: low to high</option>
          <option value="price-desc">Price: high to low</option>
          <option value="name">Name A–Z</option>
        </select>
      </div>
    </div>
  </div>
</div>

<section class="band-tight">
  <div class="wrap">
    <div class="result-line">
      <span id="resultCount">{len(PRODUCTS)} pieces</span>
      <span>Printed to order · Ships worldwide</span>
    </div>
    <div class="product-grid" id="shopGrid"></div>
    <div class="empty-state hidden" id="shopEmpty">
      <h3>Nothing carries that name</h3>
      <p>Try another artwork or clear your filters.</p>
    </div>
    <div class="load-more-wrap" id="loadMoreWrap">
      <button class="btn btn-ghost" id="loadMore">Load more pieces</button>
    </div>
  </div>
</section>
"""
    return layout(
        prefix="",
        title="Shop all · Light Scribe Atelier",
        description=f"Browse {len(PRODUCTS)} made-to-order pieces printed with {len(DESIGNS)} channeled artworks by Morayana Levy.",
        body=body,
        active="shop.html",
    )


def build_collection(slug: str) -> str:
    meta = CATS[slug]
    items = [p for p in PRODUCTS if p["category"] == slug]
    types = sorted({p["type"] for p in items})
    hero = items[0]["images"][0] if items else ""
    for p in items:
        if "kimono" in p["type"].lower() or "sherpa" in p["type"].lower():
            hero = p["images"][0]
            break
    body = f"""
<section class="art-hero">
  <div class="art-hero-bg"><img src="{hero}" alt="{esc(meta['label'])}"></div>
  <div class="wrap art-hero-grid">
    <div>
      <nav class="eyebrow"><a href="../index.html">Home</a> — Collections</nav>
      <h1 class="display" style="font-size:clamp(2.6rem,6vw,4.6rem);margin:.9rem 0 1rem">{esc(meta['label'])}</h1>
      <p class="lede">{esc(meta['blurb'])}</p>
      <div class="artwork-meta">
        <span id="collectionCount">{len(items)} pieces</span>
        <span>{len({p['designSlug'] for p in items})} artworks</span>
        <span>{esc(' · '.join(types[:4]))}</span>
      </div>
    </div>
    <figure class="art-frame" style="margin:0"><img src="{hero}" alt="{esc(meta['label'])}"><figcaption>{esc(meta['label'])} · Light Scribe Atelier</figcaption></figure>
  </div>
</section>

<section class="band-tight">
  <div class="wrap">
    <div class="product-grid" data-collection="{slug}"></div>
    <div class="load-more-wrap" id="collectionMore">
      <button class="btn btn-ghost">Load more pieces</button>
    </div>
  </div>
</section>

<section class="band-tight">
  <div class="wrap center">
    <span class="eyebrow">Other ways to keep it close</span>
    <div class="chips mt-2" style="justify-content:center">
      {"".join(f'<a class="chip" href="{s}.html">{esc(m["label"])}</a>' for s, m in CATS.items() if s != slug)}
      <a class="chip" href="../fine-art.html">Fine art prints</a>
    </div>
  </div>
</section>
"""
    return layout(
        prefix="../",
        title=f"{meta['label']} · Light Scribe Atelier",
        description=meta["blurb"],
        body=body,
        active=f"collections/{slug}.html",
    )


ART_IMAGE_ORDER = [
    "sherpa blanket", "throw blanket", "fleece blanket", "kimono", "wall tapestry",
    "long scarf", "pillow", "tote", "headband",
]


def art_image(design: dict) -> str:
    """The product photo that shows the artwork itself, not a model or a room."""
    prods = by_design(design["slug"])
    for wanted in ART_IMAGE_ORDER:
        for prod in prods:
            if wanted in prod["type"].lower():
                return prod["images"][0]
    return design["images"][0]


def design_note(name: str) -> str:
    notes = [
        "A transmission received in light language, holding the frequency of its name.",
        "Channeled codes, rendered as colour and form so the field can stay in your space.",
        "An energetic signature from benevolent star lineages, printed to keep it close.",
    ]
    return notes[sum(ord(c) for c in name) % len(notes)]


def build_artwork(design: dict) -> str:
    items = by_design(design["slug"])
    others = [d for d in DESIGNS if d["slug"] != design["slug"]][:12]
    types = sorted({p["type"] for p in items})
    body = f"""
<section class="art-hero">
  <div class="art-hero-bg"><img src="{art_image(design)}" alt="{esc(design['name'])}"></div>
  <div class="wrap art-hero-grid">
    <div>
      <nav class="eyebrow"><a href="../artwork/index.html">Transmissions</a> — Artwork</nav>
      <h1 class="display" style="font-size:clamp(2.2rem,5.4vw,4.2rem);margin:.9rem 0 1rem">{esc(design['name'])}</h1>
      <p class="lede">{esc(design_note(design['name']))}</p>
      <div class="artwork-meta">
        <span>{len(items)} pieces</span>
        <span>{esc(' · '.join(types[:5]))}</span>
        <span>Channeled by Morayana</span>
      </div>
    </div>
    <figure class="art-frame" style="margin:0"><img src="{art_image(design)}" alt="{esc(design['name'])}"><figcaption>{esc(design['name'])} · Light Scribe Art</figcaption></figure>
  </div>
</section>

<section class="band-tight">
  <div class="wrap">
    <div class="product-grid" id="artworkGrid" data-slug="{design['slug']}">
      {static_cards(items, "../")}
    </div>
    <div class="center mt-3">
      <a class="link-arrow" href="../fine-art.html">See this artwork as a fine art print</a>
    </div>
  </div>
</section>

<section class="band-tight">
  <div class="wrap">
    <div class="section-head">
      <div><span class="eyebrow">Continue</span><h2 class="section-title">Other transmissions</h2></div>
      <a class="link-arrow" href="../artwork/index.html">All {len(DESIGNS)}</a>
    </div>
    <div class="design-grid">
      {"".join(f'<a class="design-tile" href="{d["slug"]}.html"><img src="{d["image"]}" alt="{esc(d["name"])}" loading="lazy"><span>{esc(d["name"])}</span></a>' for d in others)}
    </div>
  </div>
</section>
"""
    return layout(
        prefix="../",
        title=f"{design['name']} · Light Scribe Atelier",
        description=f"{len(items)} made-to-order pieces printed with the channeled artwork {design['name']} by Morayana Levy.",
        body=body,
    )


def build_artwork_index() -> str:
    tiles = "".join(
        f'<a class="design-tile reveal" href="{d["slug"]}.html"><img src="{d["image"]}" alt="{esc(d["name"])}" loading="lazy"><span>{esc(d["name"])} · {d["count"]}</span></a>'
        for d in DESIGNS
    )
    body = f"""
<section class="art-hero">
  <div class="art-hero-bg"><img src="{hero_art()}" alt="Channeled art"></div>
  <div class="wrap" style="position:relative;z-index:2">
    <nav class="eyebrow"><a href="../index.html">Home</a> — Transmissions</nav>
    <h1 class="display" style="font-size:clamp(2.6rem,6.4vw,5rem);margin:.9rem 0 1rem">All transmissions</h1>
    <p class="lede">{len(DESIGNS)} channeled artworks, each printed across garments, textiles and objects. Choose one to see every form it takes.</p>
  </div>
</section>
<section class="band-tight">
  <div class="wrap"><div class="design-grid">{tiles}</div></div>
</section>
"""
    return layout(
        prefix="../",
        title=f"All {len(DESIGNS)} transmissions · Light Scribe Atelier",
        description="Browse every channeled light language artwork by Morayana Levy.",
        body=body,
    )


def build_fine_art() -> str:
    blocks = []
    for name, data in FINE.items():
        items = data.get("items") or []
        if not items:
            continue
        figs = "".join(
            f'<figure><img src="{i["src"]}" alt="{esc(name)}" loading="lazy"></figure>' for i in items[:4]
        )
        blocks.append(
            f"""
      <div class="fa-coll reveal">
        <div class="fa-coll-head">
          <div>
            <span class="eyebrow">Collection</span>
            <h2>{esc(name)}</h2>
          </div>
          <a class="link-arrow" href="{data['url']}" target="_blank" rel="noopener">View in gallery</a>
        </div>
        <a href="{data['url']}" target="_blank" rel="noopener"><div class="fa-strip">{figs}</div></a>
      </div>"""
        )
    body = f"""
<section class="art-hero">
  <div class="art-hero-bg"><img src="{hero_art()}" alt="Fine art"></div>
  <div class="wrap art-hero-grid">
    <div>
      <nav class="eyebrow"><a href="index.html">Home</a> — Fine Art</nav>
      <h1 class="display" style="font-size:clamp(2.6rem,6.4vw,5rem);margin:.9rem 0 1rem">Fine art <em>editions</em></h1>
      <p class="lede">Metal prints and archival paper editions from the main gallery — the artworks at scale, for walls and collectors.</p>
      <div class="hero-cta">
        <a class="btn" href="https://www.lightscribeart.com/Main" target="_blank" rel="noopener">Enter the gallery</a>
        <a class="btn btn-ghost" href="shop.html">Shop wearable art</a>
      </div>
    </div>
    <figure class="art-frame" style="margin:0"><img src="{next(iter(FINE.values()))['items'][0]['src']}" alt="Fine art print"><figcaption>Light Scribe Art · Main gallery</figcaption></figure>
  </div>
</section>
<section class="band-tight">
  <div class="wrap">
    {''.join(blocks)}
    <p class="lede mt-3">Fine art orders are fulfilled by the Light Scribe Art gallery through Art Storefronts, with museum-grade printing and secure checkout.</p>
  </div>
</section>
"""
    return layout(
        prefix="",
        title="Fine art editions · Light Scribe Atelier",
        description="Museum-grade metal and paper editions of Morayana Levy's channeled artworks.",
        body=body,
        active="fine-art.html",
    )


def build_healing() -> str:
    hero = next(
        (p["images"][0] for p in PRODUCTS if "sherpa" in p["type"].lower()), HERO_IMAGES[0]
    )
    body = f"""
<section class="art-hero">
  <div class="art-hero-bg"><img src="{hero}" alt="42 Chakra Point healing"></div>
  <div class="wrap art-hero-grid">
    <div>
      <nav class="eyebrow"><a href="index.html">Home</a> — Healing</nav>
      <h1 class="display" style="font-size:clamp(2.4rem,5.6vw,4.4rem);margin:.9rem 0 1rem">42 Chakra <em>Point</em> Healing</h1>
      <p class="lede">Morayana's signature modality: a private energetic map of all 42 chakra points, followed by a gentle, guided program of activations.</p>
      <div class="hero-cta">
        <a class="btn" href="https://42chakrapoint.com" target="_blank" rel="noopener">Book the energy scan · $144</a>
        <a class="btn btn-ghost" href="https://morayana.com" target="_blank" rel="noopener">Live activations</a>
      </div>
    </div>
    <figure class="art-frame" style="margin:0"><img src="{hero}" alt="Sacred textile"><figcaption>Seven centres · six points each · 42 points</figcaption></figure>
  </div>
</section>

<section class="band">
  <div class="wrap split">
    <div class="reveal">
      <span class="eyebrow">How it works</span>
      <h2 class="section-title">From first reading to private portal</h2>
      <div class="steps">
        <div class="step"><span class="step-num">1</span><div><h3 style="font-family:var(--serif);font-weight:300;font-size:1.25rem;margin:0 0 .3rem">The energy scan</h3><p class="lede">A remote scan identifies which of the 42 points are carrying blockages, and returns a detailed private report.</p></div></div>
        <div class="step"><span class="step-num">2</span><div><h3 style="font-family:var(--serif);font-weight:300;font-size:1.25rem;margin:0 0 .3rem">Your personal results</h3><p class="lede">You receive your affected-point count and the recommended order for your sessions.</p></div></div>
        <div class="step"><span class="step-num">3</span><div><h3 style="font-family:var(--serif);font-weight:300;font-size:1.25rem;margin:0 0 .3rem">The personalized program</h3><p class="lede">Each unique affected point equals one $55 session, delivered one per week in a private portal.</p></div></div>
        <div class="step"><span class="step-num">4</span><div><h3 style="font-family:var(--serif);font-weight:300;font-size:1.25rem;margin:0 0 .3rem">Weekly activations</h3><p class="lede">Your aligned activations unlock gradually, so the body can release harmoniously.</p></div></div>
      </div>
    </div>
    <div class="split-media reveal"><img src="{next((p['images'][0] for p in PRODUCTS if p['category']=='textiles'), hero)}" alt="Sacred textiles"></div>
  </div>
</section>

<section class="band quote-band">
  <div class="wrap">
    <span class="eyebrow">In their words</span>
    <div class="quote-grid mt-2">
      {"".join(f'<blockquote>“{esc(q)}”<footer>{esc(who)}</footer></blockquote>' for q, who in TESTIMONIALS)}
    </div>
  </div>
</section>

<section class="band-tight">
  <div class="wrap center">
    <span class="eyebrow">Keep the frequency close</span>
    <h2 class="section-title mt-1">Live with the art</h2>
    <div class="hero-cta" style="justify-content:center">
      <a class="btn" href="shop.html">Shop the atelier</a>
      <a class="btn btn-ghost" href="https://morayana.com" target="_blank" rel="noopener">Sessions &amp; courses</a>
    </div>
  </div>
</section>
"""
    return layout(
        prefix="",
        title="42 Chakra Point Healing · Morayana Levy",
        description="The 42 Chakra Point Energy Scan: a private energetic map of all 42 points, then a guided program of weekly activations.",
        body=body,
        active="healing.html",
    )


def build_about() -> str:
    portrait = next(
        (p["images"][0] for p in PRODUCTS if "kimono" in p["type"].lower()), HERO_IMAGES[0]
    )
    body = f"""
<section class="art-hero">
  <div class="art-hero-bg"><img src="{hero_art()}" alt="Morayana Levy"></div>
  <div class="wrap art-hero-grid">
    <div>
      <nav class="eyebrow"><a href="index.html">Home</a> — The Artist</nav>
      <h1 class="display" style="font-size:clamp(2.6rem,6.4vw,5rem);margin:.9rem 0 1rem">The <em>Creatrix</em></h1>
      <p class="lede">Morayana Levy — healer, channel, artist. Creator of 42 Chakra Point Healing, ThetaHealing practitioner, and the hand behind every piece in this atelier.</p>
    </div>
    <figure class="art-frame" style="margin:0"><img src="{portrait}" alt="Channeled art by Morayana"><figcaption>Light Scribe Art · Channeled by Morayana Levy</figcaption></figure>
  </div>
</section>

<section class="band">
  <div class="wrap split">
    <div class="split-media reveal"><img src="{portrait}" alt="Morayana Levy artwork"></div>
    <div class="prose reveal">
      <span class="eyebrow">The story</span>
      <h2 class="section-title">Light language, made visible</h2>
      <p class="mt-1">Morayana is the creator of <strong>42 Chakra Point Healing</strong> and a ThetaHealing practitioner. Her work moves between energy healing, channeled art and light language activation — each piece received as a transmission, then offered as something you can live with.</p>
      <p>Every artwork in this atelier begins the same way: a light language code is received, translated into colour and form, and sent to print on demand so nothing is made before it is chosen.</p>
      <h3>The modality</h3>
      <p>42 Chakra Point Healing maps seven chakra centres with six energy points each — three in the front of the body, three in the back. The scan reveals where energy is blocked; the personalized program clears it, one point per week, gently.</p>
      <h3>The art</h3>
      <p>The Light Scribe gallery holds hundreds of channeled works, offered as metal prints, paper editions and wearable art. The names are light language — the sound of each transmission rather than a description of it.</p>
      <div class="hero-cta" style="margin-top:2rem">
        <a class="btn btn-ghost" href="https://morayana.com" target="_blank" rel="noopener">morayana.com</a>
        <a class="btn btn-ghost" href="https://www.lightscribeart.com" target="_blank" rel="noopener">Fine art gallery</a>
      </div>
    </div>
  </div>
</section>

<section class="band-tight">
  <div class="wrap center">
    <span class="eyebrow">Start anywhere</span>
    <div class="hero-cta" style="justify-content:center">
      <a class="btn" href="shop.html">Shop the atelier</a>
      <a class="btn btn-ghost" href="artwork/index.html">Browse transmissions</a>
    </div>
  </div>
</section>
"""
    return layout(
        prefix="",
        title="The Artist · Morayana Levy",
        description="Morayana Levy — creator of 42 Chakra Point Healing, ThetaHealing practitioner, and channel of the Light Scribe artworks.",
        body=body,
        active="about.html",
    )


def build_product_page() -> str:
    body = """
<section class="pdp">
  <div class="wrap" id="pdp">
    <div class="empty-state"><h3>Loading the piece…</h3></div>
  </div>
</section>
"""
    return layout(
        prefix="",
        title="Piece · Light Scribe Atelier",
        description="A made-to-order piece from the Light Scribe Atelier.",
        body=body,
    )


def build_404() -> str:
    body = """
<section class="band center" style="padding-top:9rem">
  <div class="wrap">
    <span class="eyebrow">404</span>
    <h1 class="display" style="font-size:clamp(2.4rem,7vw,5rem);margin:1rem 0">This page has <em>dissolved</em></h1>
    <p class="lede" style="margin:0 auto">The transmission you were looking for isn't here. Everything else is.</p>
    <div class="hero-cta" style="justify-content:center">
      <a class="btn" href="index.html">Return home</a>
      <a class="btn btn-ghost" href="shop.html">Shop all pieces</a>
    </div>
  </div>
</section>
"""
    return layout(
        prefix="",
        title="Not found · Light Scribe Atelier",
        description="Page not found.",
        body=body,
    )


def write(path: Path, html: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html)


SITE_URL = "https://morayana444.github.io/light-scribe-atelier"


def build_sitemap() -> str:
    urls = ["", "shop.html", "fine-art.html", "healing.html", "about.html", "artwork/index.html"]
    urls += [f"collections/{c}.html" for c in CATS]
    urls += [f"artwork/{d['slug']}.html" for d in DESIGNS]
    body = "\n".join(
        f"  <url><loc>{SITE_URL}/{u}</loc><changefreq>weekly</changefreq></url>" for u in urls
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n</urlset>\n"
    )


def main() -> None:
    write(ROOT / "index.html", build_index())
    write(ROOT / "shop.html", build_shop())
    write(ROOT / "fine-art.html", build_fine_art())
    write(ROOT / "healing.html", build_healing())
    write(ROOT / "about.html", build_about())
    write(ROOT / "product.html", build_product_page())
    write(ROOT / "404.html", build_404())
    write(ROOT / "artwork" / "index.html", build_artwork_index())
    for slug in CATS:
        write(ROOT / "collections" / f"{slug}.html", build_collection(slug))
    for design in DESIGNS:
        write(ROOT / "artwork" / f"{design['slug']}.html", build_artwork(design))
    write(ROOT / "sitemap.xml", build_sitemap())
    write(ROOT / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    print(
        f"pages: 8 + {len(CATS)} collections + {len(DESIGNS)} artworks = "
        f"{8 + len(CATS) + len(DESIGNS)}"
    )


if __name__ == "__main__":
    main()

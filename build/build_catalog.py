"""Normalize the lightscribeshop product feed into a clean catalog."""

from __future__ import annotations

import difflib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "all_products.json"

# product_type -> (category slug, category label)
TYPE_MAP = {
    "unisex hoodie": ("apparel", "Apparel"),
    "athletic crop top": ("apparel", "Apparel"),
    "fitted tank top": ("apparel", "Apparel"),
    "yoga leggings": ("apparel", "Apparel"),
    "unisex joggers": ("apparel", "Apparel"),
    "men's tank top": ("apparel", "Apparel"),
    "sherpa blanket": ("textiles", "Ritual Textiles"),
    "throw blanket": ("textiles", "Ritual Textiles"),
    "blanket": ("textiles", "Ritual Textiles"),
    "long scarf": ("textiles", "Ritual Textiles"),
    "towel": ("textiles", "Ritual Textiles"),
    "wall tapestry": ("textiles", "Ritual Textiles"),
    '18" x 18" pillow case': ("space", "Sacred Space"),
    "18' x 18' pillow case": ("space", "Sacred Space"),
    "premium pillow": ("space", "Sacred Space"),
    "coaster": ("space", "Sacred Space"),
    "mugs": ("space", "Sacred Space"),
    "white glossy mug": ("space", "Sacred Space"),
    "glass": ("space", "Sacred Space"),
    "shaker pint glass": ("space", "Sacred Space"),
    "tote bag": ("carry", "Carry & Adorn"),
    "backpack": ("carry", "Carry & Adorn"),
    "vegan leather backpack": ("carry", "Carry & Adorn"),
    "headband": ("carry", "Carry & Adorn"),
    "kimono robe": ("carry", "Carry & Adorn"),
}

CATEGORY_META = {
    "apparel": {
        "label": "Wearable Art",
        "blurb": "Light language printed onto garments you move through the world in.",
    },
    "textiles": {
        "label": "Ritual Textiles",
        "blurb": "Blankets, throws and scarves — transmissions you can wrap around yourself.",
    },
    "space": {
        "label": "Sacred Space",
        "blurb": "Pillows, mugs, coasters and glassware that hold a frequency in the room.",
    },
    "carry": {
        "label": "Carry & Adorn",
        "blurb": "Totes, backpacks, kimonos and gaiters — art that travels with you.",
    },
}

TYPE_KEYWORDS = [
    ("yoga leggings", "apparel"),
    ("crop top", "apparel"),
    ("tank top", "apparel"),
    ("tank", "apparel"),
    ("hoodie", "apparel"),
    ("joggers", "apparel"),
    ("sherpa blanket", "textiles"),
    ("throw blanket", "textiles"),
    ("blanket", "textiles"),
    ("scarf", "textiles"),
    ("towel", "textiles"),
    ("tapestry", "textiles"),
    ("pillow", "space"),
    ("coaster", "space"),
    ("mug", "space"),
    ("glass", "space"),
    ("tote", "carry"),
    ("backpack", "carry"),
    ("kimono", "carry"),
    ("gaiter", "carry"),
    ("headband", "carry"),
]

TYPE_LABEL = {
    "unisex hoodie": "Unisex Hoodie",
    "athletic crop top": "Athletic Crop Top",
    "fitted tank top": "Fitted Tank Top",
    "yoga leggings": "Yoga Leggings",
    "unisex joggers": "Unisex Joggers",
    "men's tank top": "Unisex Tank Top",
    "sherpa blanket": "Sherpa Blanket",
    "throw blanket": "Throw Blanket",
    "blanket": "Fleece Blanket",
    "long scarf": "Long Scarf",
    "towel": "Bath Towel",
    "wall tapestry": "Wall Tapestry",
    '18" x 18" pillow case': '18"x18" Pillow Case',
    "18' x 18' pillow case": '18"x18" Pillow Case',
    "premium pillow": "Premium Pillow",
    "coaster": "Coaster",
    "mugs": "Mug",
    "white glossy mug": "Glossy Mug",
    "glass": "Glass",
    "shaker pint glass": "Pint Glass",
    "tote bag": "Tote Bag",
    "backpack": "Vegan Leather Backpack",
    "vegan leather backpack": "Vegan Leather Backpack",
    "headband": "Headband / Neck Gaiter",
    "kimono robe": "Kimono Robe",
}

CANON = {
    "Hoodie": "Unisex Hoodie",
    "Tank Top": "Unisex Tank Top",
    "Pillow": '18"x18" Pillow Case',
    "Tote": "Tote Bag",
    "Gaiter": "Headband / Neck Gaiter",
    "Mug": "Glossy Mug",
    "Backpack": "Vegan Leather Backpack",
    "Crop Top": "Athletic Crop Top",
}

DESIGN_STOPWORDS = [
    "throw blanket", "sherpa blanket", "fleece blanket", "blanket", "yoga leggings",
    "athletic crop top", "crop top", "fitted tank top", "unisex tank top", "tank top",
    "unisex hoodie", "hoodie", "unisex joggers", "joggers", "kimono robe", "kimono",
    "long scarf", "pillow case", "premium pillow", "white glossy mug", "shaker pint glass",
    "mug", "glass", "tote bag", "vegan leather backpack", "backpack", "neck gaiter",
    "headband", "bath towel", "towel", "wall tapestry", "coaster",
]

SLUG_SAFE = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return SLUG_SAFE.sub("-", text.lower()).strip("-")


def clean_design(title: str) -> str:
    """Extract the artwork name from a Shopify product title."""
    t = title.replace("\u2013", "-").replace("\u2014", "-")
    t = re.sub(r"\s+", " ", t).strip()
    if " - " in t:
        t = t.split(" - ")[0]
    low = t.lower()
    for word in DESIGN_STOPWORDS:
        idx = low.rfind(word)
        if idx > 0 and idx + len(word) >= len(t) - 2:
            t = t[:idx]
            low = t.lower()
            break
    t = t.strip(" -\u2013\u2014.&'")
    t = re.sub(r"^(foxes|fox)\b", "Foxes", t, flags=re.I)
    if t.isupper():
        return t
    # Preserve all-caps channeled names, title-case the plain english ones
    words = t.split()
    if all(w[:1].isupper() for w in words if w):
        return t.upper() if len(words) > 1 and sum(1 for w in words if w.isupper()) else t
    return t.upper()


def money(v: str | float) -> float:
    return float(v)


def pick_images(images: list[dict]) -> list[str]:
    """Prefer flat/front product images over lifestyle renders."""
    scored = []
    for img in images:
        src = img.get("src") or ""
        if not src:
            continue
        name = src.lower()
        score = 0
        if "front" in name:
            score += 3
        if "lifestyle" in name:
            score -= 2
        if "crop" in name:
            score -= 1
        scored.append((score, src))
    scored.sort(key=lambda s: -s[0])
    out: list[str] = []
    for _, src in scored:
        if src not in out:
            out.append(src)
    return out


def main() -> None:
    raw = json.loads(RAW.read_text())
    products = []
    designs: dict[str, dict] = {}

    for p in raw:
        title = (p.get("title") or "").strip()
        if not title:
            continue
        if "gift card" in title.lower():
            continue
        variants = p.get("variants") or []
        if not variants:
            continue
        ptype = (p.get("product_type") or "").strip().lower()
        cat = TYPE_MAP.get(ptype, (None, None))[0]
        if cat is None:
            low = title.lower()
            for kw, c in TYPE_KEYWORDS:
                if kw in low:
                    cat = c
                    break
        if cat is None:
            cat = "space"
        type_label = TYPE_LABEL.get(ptype)
        if type_label is None:
            low = title.lower()
            type_label = "Art Print"
            for kw, _ in TYPE_KEYWORDS:
                if kw in low:
                    type_label = CANON.get(kw.title(), kw.title())
                    break
        prices = [money(v["price"]) for v in variants]
        design = clean_design(title)
        if not design or len(design) < 2:
            continue
        images = pick_images(p.get("images") or [])
        if not images:
            continue
        key = design.upper()
        entry = designs.setdefault(
            key,
            {
                "name": design,
                "slug": slugify(design),
                "count": 0,
                "categories": set(),
                "image": images[0],
                "images": images[:8],
                "products": [],
            },
        )
        entry["count"] += 1
        entry["categories"].add(cat)
        entry["products"].append(title)
        if len(images) > len(entry["images"]):
            entry["images"] = images[:8]
        products.append(
            {
                "id": p["id"],
                "title": title,
                "design": entry["name"],
                "designSlug": entry["slug"],
                "handle": p.get("handle"),
                "type": type_label,
                "category": cat,
                "price": round(min(prices), 2),
                "maxPrice": round(max(prices), 2),
                "currency": "USD",
                "description": re.sub(r"<[^>]+>", " ", p.get("body_html") or "").strip(),
                "descKey": type_label,
                "image": images[0],
                "images": images[:3],
                "variants": [
                    {
                        "id": v["id"],
                        "title": v.get("title", "Default"),
                        "price": round(money(v["price"]), 2),
                        "available": bool(v.get("available")),
                        "option1": v.get("option1"),
                    }
                    for v in variants
                ],
                "available": any(v.get("available") for v in variants),
                "tags": p.get("tags") or [],
            }
        )

    # merge near-duplicate design names (case/typo variants of the same transmission)
    names = sorted(designs)
    merged: dict[str, str] = {}
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            if merged and merged.get(b):
                continue
            if a == b:
                continue
            norm_a = re.sub(r"[^A-Z]", "", a)
            norm_b = re.sub(r"[^A-Z]", "", b)
            ratio = difflib.SequenceMatcher(None, norm_a, norm_b).ratio()
            if ratio >= 0.87 and abs(len(a) - len(b)) <= 4:
                keeper = a if designs[a]["count"] >= designs[b]["count"] else b
                other = b if keeper == a else a
                if designs[other]["name"] in merged:
                    continue
                merged[designs[other]["name"]] = keeper
                designs[keeper]["count"] += designs[other]["count"]
                designs[keeper]["categories"] |= designs[other]["categories"]
                if designs[other]["image"] not in designs[keeper]["images"]:
                    designs[keeper]["images"].extend(designs[other]["images"])
                designs[keeper]["products"].extend(designs[other]["products"])

    for prod in products:
        key = prod["design"].upper()
        if key in merged:
            keeper = merged[key]
            prod["design"] = designs[keeper]["name"]
            prod["designSlug"] = designs[keeper]["slug"]

    live = {k: v for k, v in designs.items() if v["name"] not in merged}
    design_list = []
    for _, d in live.items():
        d["count"] = sum(1 for p in products if p["design"] == d["name"])
        d["categories"] = sorted(d["categories"])
        design_list.append(d)
    design_list.sort(key=lambda d: d["name"])

    products.sort(key=lambda p: (p["design"], -p["price"]))

    # keep the payload small: descriptions are identical per product type
    type_info: dict[str, dict] = {}
    for prod in products:
        key = prod["descKey"]
        info = type_info.setdefault(key, {"description": "", "details": []})
        if not info["description"] and prod["description"]:
            text = re.sub(r"\s*[-]{5,}\s*", "\n", prod["description"])
            lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
            long_lines = [ln for ln in lines if len(ln) > 60 and not ln.endswith(":")]
            info["description"] = long_lines[0] if long_lines else (lines[0] if lines else "")
            details = []
            for ln in lines[1:]:
                ln = ln.replace("\u2022", "").strip()
                if 4 < len(ln) < 120:
                    details.append(ln)
            info["details"] = details[:8]
        prod.pop("description", None)
        prod.pop("descKey", None)

    catalog = {
        "generated": "2026-11-16",
        "currency": "USD",
        "categories": CATEGORY_META,
        "typeInfo": type_info,
        "designs": [
            {
                "name": d["name"],
                "slug": d["slug"],
                "count": d["count"],
                "categories": d["categories"],
                "image": d["image"],
                "images": d["images"][:6],
            }
            for d in design_list
        ],
        "products": products,
    }
    out = ROOT.parent / "data" / "catalog.json"
    out.write_text(json.dumps(catalog, separators=(",", ":")))
    print(f"designs={len(design_list)} products={len(products)} -> {out}")


if __name__ == "__main__":
    main()

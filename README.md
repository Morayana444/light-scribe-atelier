# Light Scribe Atelier — Morayana Levy

A static storefront for Morayana Levy's channeled art: 877 made-to-order pieces across 143
light-language artworks, plus fine-art prints and the 42 Chakra Point modality.

Live: https://morayana444.github.io/light-scribe-atelier/

## How it is built

| Path | What it is |
|---|---|
| `build/build_catalog.py` | Normalises the Shopify product feed into `data/catalog.json` |
| `build/build_site.py` | Generates every HTML page from that catalog |
| `assets/css/site.css` | All styling (no framework) |
| `assets/js/site.js` | Catalog rendering, filters, cart drawer, product page |
| `data/catalog.json` | 877 products, 143 artworks, product-type copy |

Rebuild everything:

```bash
python3 build/build_catalog.py   # needs build/all_products.json from the Shopify feed
python3 build/build_site.py
```

## Commerce

Products live in the existing Shopify store (`lightscribeshop.myshopify.com`). "Add to bag"
keeps a cart in `localStorage`; checkout opens the matching Shopify **cart permalink**
(`/cart/<variant_id>:<qty>,…`), so payment, tax, shipping and fulfilment all stay inside
Shopify. No card data ever touches this site.

Fine-art editions link out to the Art Storefronts gallery (`lightscribeart.com`) and healing
programs link to `42chakrapoint.com` / `morayana.com`.

## Hosting

GitHub Pages from the `main` branch root, no build step (`.nojekyll` included).

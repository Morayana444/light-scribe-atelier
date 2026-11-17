/* =========================================================
   LIGHT SCRIBE ATELIER — storefront engine
   Static catalog, localStorage cart, Shopify cart-permalink checkout
   ========================================================= */
(function () {
  "use strict";

  const SHOP_ORIGIN = "https://lightscribeshop.myshopify.com";
  const BASE_ATTR = document.documentElement.getAttribute("data-base");
  const BASE = BASE_ATTR === null ? "/" : BASE_ATTR; // "" is valid: relative to this page
  const DATA_VERSION = document.documentElement.getAttribute("data-v") || "";
  const u = (path) => BASE + String(path).replace(/^\//, "");
  const CART_KEY = "lsa_cart_v1";
  const money = (n) =>
    "$" + Number(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  let CATALOG = null;
  let catalogPromise = null;

  function loadCatalog() {
    if (catalogPromise) return catalogPromise;
    catalogPromise = fetch(u("data/catalog.json") + (DATA_VERSION ? "?v=" + DATA_VERSION : ""))
      .then((r) => {
        if (!r.ok) throw new Error("catalog " + r.status);
        return r.json();
      })
      .then((data) => {
        CATALOG = data;
        return data;
      });
    return catalogPromise;
  }

  /* ---------------- product card ---------------- */
  function cardHTML(p) {
    const img = p.image || "";
    const priceNote =
      p.maxPrice > p.price ? "From " + money(p.price) : money(p.price);
    return `
      <article class="card">
        <a class="card-media" href="${u("product.html")}?id=${p.id}" aria-label="${esc(p.title)}">
          <img src="${img}" alt="${esc(p.title)}" loading="lazy" decoding="async">
          <span class="card-tag">${esc(p.type)}</span>
          <span class="card-quick" data-add="${p.id}">Add to bag</span>
        </a>
        <div class="card-body">
          <a class="card-design" href="${u("artwork/" + p.designSlug + ".html")}">${esc(p.design)}</a>
          <a class="card-title" href="${u("product.html")}?id=${p.id}">${esc(p.type)}</a>
          <span class="card-price">${priceNote}</span>
        </div>
      </article>`;
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderInto(el, products, limit) {
    const slice = limit ? products.slice(0, limit) : products;
    el.innerHTML = slice.map(cardHTML).join("");
    observeReveals(el);
    el.querySelectorAll("[data-add]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        const p = CATALOG.products.find((x) => String(x.id) === btn.dataset.add);
        if (p) {
          const v = (p.variants.find((x) => x.available) || p.variants[0]);
          addToCart(p, v, 1, btn);
        }
      });
    });
  }

  /* ---------------- cart ---------------- */
  function getCart() {
    try {
      return JSON.parse(localStorage.getItem(CART_KEY)) || [];
    } catch (e) {
      return [];
    }
  }
  function setCart(items) {
    localStorage.setItem(CART_KEY, JSON.stringify(items));
    paintCart();
  }
  function addToCart(product, variant, qty, btnEl) {
    const cart = getCart();
    const key = String(variant.id);
    const found = cart.find((i) => i.vid === key);
    if (found) found.qty += qty;
    else
      cart.push({
        vid: key,
        id: product.id,
        title: product.title,
        design: product.design,
        type: product.type,
        option: variant.title,
        price: variant.price,
        image: product.images[1] || product.image,
        qty: qty,
      });
    setCart(cart);
    if (btnEl) {
      const label = btnEl.textContent;
      btnEl.textContent = "Added ✦";
      setTimeout(() => (btnEl.textContent = label), 1400);
    }
    openCart();
    toast("Added to your bag");
  }

  function paintCart() {
    const cart = getCart();
    const count = cart.reduce((n, i) => n + i.qty, 0);
    document.querySelectorAll(".cart-count").forEach((el) => {
      el.textContent = count;
      el.classList.toggle("on", count > 0);
    });
    const box = document.getElementById("cartItems");
    if (!box) return;
    if (!cart.length) {
      box.innerHTML = `<p class="cart-empty">Your bag is empty.<br>Every piece carries a transmission.</p>`;
    } else {
      box.innerHTML = cart
        .map(
          (i) => `
        <div class="cart-item">
          <img src="${i.image}" alt="${esc(i.title)}">
          <div>
            <h3>${esc(i.title)}</h3>
            <small>${esc(i.option)} · ${i.design}</small>
            <div class="ci-row">
              <span class="qty" data-vid="${i.vid}">
                <button data-step="-1" aria-label="Decrease">−</button>
                <span>${i.qty}</span>
                <button data-step="1" aria-label="Increase">+</button>
              </span>
              <span>${money(i.price * i.qty)}</span>
            </div>
            <div class="ci-row"><button class="ci-remove" data-remove="${i.vid}">Remove</button></div>
          </div>
        </div>`
        )
        .join("");
      box.querySelectorAll("[data-step]").forEach((b) =>
        b.addEventListener("click", () => {
          const vid = b.parentElement.dataset.vid;
          const cart = getCart();
          const it = cart.find((x) => x.vid === vid);
          if (!it) return;
          it.qty += Number(b.dataset.step);
          setCart(cart.filter((x) => x.qty > 0));
        })
      );
      box.querySelectorAll("[data-remove]").forEach((b) =>
        b.addEventListener("click", () => {
          setCart(getCart().filter((x) => x.vid !== b.dataset.remove));
        })
      );
    }
    const total = cart.reduce((n, i) => n + i.price * i.qty, 0);
    const totalEl = document.getElementById("cartTotal");
    if (totalEl) totalEl.textContent = money(total);
    const checkout = document.getElementById("checkoutBtn");
    if (checkout) {
      const permalink =
        SHOP_ORIGIN +
        "/cart/" +
        cart.map((i) => i.vid + ":" + i.qty).join(",");
      checkout.dataset.href = cart.length ? permalink : "";
      checkout.classList.toggle("disabled", !cart.length);
      checkout.setAttribute("aria-disabled", cart.length ? "false" : "true");
    }
  }

  function openCart() {
    document.getElementById("cartDrawer")?.classList.add("open");
    document.getElementById("cartScrim")?.classList.add("open");
    document.body.classList.add("no-scroll");
  }
  function closeCart() {
    document.getElementById("cartDrawer")?.classList.remove("open");
    document.getElementById("cartScrim")?.classList.remove("open");
    document.body.classList.remove("no-scroll");
  }

  function toast(msg) {
    let t = document.querySelector(".toast");
    if (!t) {
      t = document.createElement("div");
      t.className = "toast";
      document.body.appendChild(t);
    }
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(t._timer);
    t._timer = setTimeout(() => t.classList.remove("show"), 2600);
  }

  /* ---------------- reveal ---------------- */
  let io = null;
  function observeReveals(root) {
    if (!("IntersectionObserver" in window)) {
      (root || document).querySelectorAll(".reveal").forEach((el) => el.classList.add("in"));
      return;
    }
    if (!io) {
      io = new IntersectionObserver(
        (entries) => {
          entries.forEach((e) => {
            if (e.isIntersecting) {
              e.target.classList.add("in");
              io.unobserve(e.target);
            }
          });
        },
        { threshold: 0.08, rootMargin: "0px 0px -40px 0px" }
      );
    }
    (root || document).querySelectorAll(".reveal:not(.in)").forEach((el) => io.observe(el));
  }

  function interleave(list) {
    const byDesign = new Map();
    list.forEach((p) => {
      if (!byDesign.has(p.designSlug)) byDesign.set(p.designSlug, []);
      byDesign.get(p.designSlug).push(p);
    });
    const queues = Array.from(byDesign.values());
    const out = [];
    let added = true;
    while (added) {
      added = false;
      queues.forEach((q) => {
        if (q.length) {
          out.push(q.shift());
          added = true;
        }
      });
    }
    return out;
  }

  /* ---------------- shop page ---------------- */
  function initShop() {
    const grid = document.getElementById("shopGrid");
    if (!grid) return;
    const params = new URLSearchParams(location.search);
    const state = {
      cat: params.get("c") || "all",
      design: params.get("d") || "",
      q: (params.get("q") || "").toLowerCase(),
      sort: params.get("sort") || "featured",
      limit: 24,
    };

    const search = document.getElementById("shopSearch");
    if (search) {
      search.value = params.get("q") || "";
      let t;
      search.addEventListener("input", () => {
        clearTimeout(t);
        t = setTimeout(() => {
          state.q = search.value.trim().toLowerCase();
          state.limit = 24;
          paint();
        }, 160);
      });
    }
    const sortSel = document.getElementById("shopSort");
    if (sortSel) {
      sortSel.value = state.sort;
      sortSel.addEventListener("change", () => {
        state.sort = sortSel.value;
        paint();
      });
    }
    document.querySelectorAll("[data-cat]").forEach((chip) => {
      chip.classList.toggle("active", chip.dataset.cat === state.cat);
      chip.addEventListener("click", () => {
        document.querySelectorAll("[data-cat]").forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");
        state.cat = chip.dataset.cat;
        state.limit = 24;
        paint();
        const url = new URL(location.href);
        if (state.cat === "all") url.searchParams.delete("c");
        else url.searchParams.set("c", state.cat);
        history.replaceState({}, "", url);
      });
    });

    const designSel = document.getElementById("shopDesign");
    if (designSel && CATALOG) {
      CATALOG.designs.forEach((d) => {
        const o = document.createElement("option");
        o.value = d.slug;
        o.textContent = d.name;
        designSel.appendChild(o);
      });
      designSel.value = state.design;
      designSel.addEventListener("change", () => {
        state.design = designSel.value;
        state.limit = 24;
        paint();
      });
    }

    const moreBtn = document.getElementById("loadMore");
    if (moreBtn) {
      moreBtn.addEventListener("click", () => {
        state.limit += 24;
        paint(true);
      });
    }

    function filtered() {
      let list = CATALOG.products.slice();
      if (state.cat !== "all") list = list.filter((p) => p.category === state.cat);
      if (state.design) list = list.filter((p) => p.designSlug === state.design);
      if (state.q) {
        list = list.filter(
          (p) =>
            p.title.toLowerCase().includes(state.q) ||
            p.design.toLowerCase().includes(state.q) ||
            p.type.toLowerCase().includes(state.q)
        );
      }
      if (state.sort === "featured") list = interleave(list);
      else if (state.sort === "price-asc") list.sort((a, b) => a.price - b.price);
      else if (state.sort === "price-desc") list.sort((a, b) => b.price - a.price);
      else if (state.sort === "name") list.sort((a, b) => a.title.localeCompare(b.title));
      return list;
    }

    function paint(keepReveal) {
      const list = filtered();
      grid.innerHTML = "";
      const shown = list.slice(0, state.limit);
      renderInto(grid, shown, null);
      const countEl = document.getElementById("resultCount");
      if (countEl) countEl.textContent = list.length + (list.length === 1 ? " piece" : " pieces");
      const moreWrap = document.getElementById("loadMoreWrap");
      if (moreWrap) moreWrap.classList.toggle("hidden", list.length <= state.limit);
      const empty = document.getElementById("shopEmpty");
      if (empty) empty.classList.toggle("hidden", list.length > 0);
    }

    paint();
  }

  /* ---------------- product detail ---------------- */
  function initProduct() {
    const host = document.getElementById("pdp");
    if (!host) return;
    const id = new URLSearchParams(location.search).get("id");
    loadCatalog().then(() => {
      const p = CATALOG.products.find((x) => String(x.id) === String(id));
      if (!p) {
        host.innerHTML = `<div class="empty-state"><h3>This piece has moved on</h3><p>It may no longer be available. <a class="link-arrow" href="${u("shop.html")}">Browse the collection</a></p></div>`;
        return;
      }
      document.title = p.title + " · Light Scribe Atelier";
      const info = CATALOG.typeInfo[p.type] || {};
      const variants = p.variants;
      let current = variants.find((v) => v.available) || variants[0];
      const multi = variants.length > 1;

      host.innerHTML = `
        <nav class="eyebrow" style="margin-bottom:1.6rem">
          <a href="${u("shop.html")}">Shop</a> — <a href="${u("artwork/" + p.designSlug + ".html")}">${esc(p.design)}</a>
        </nav>
        <div class="pdp-grid">
          <div class="pdp-gallery">
            <div class="pdp-main"><img id="pdpImg" src="${p.images[0]}" alt="${esc(p.title)}"></div>
            ${
              p.images.length > 1
                ? `<div class="pdp-thumbs">${p.images
                    .map(
                      (src, i) =>
                        `<button class="${i === 0 ? "active" : ""}" data-src="${src}"><img src="${src}" alt=""></button>`
                    )
                    .join("")}</div>`
                : ""
            }
          </div>
          <div class="pdp-info">
            <a class="pdp-design" href="${u("artwork/" + p.designSlug + ".html")}">${esc(p.design)}</a>
            <h1>${esc(p.title.replace(p.design + " - ", "").replace(p.design + " -", ""))}</h1>
            <div class="pdp-price" id="pdpPrice">${money(current.price)}</div>
            <p class="pdp-desc">${esc(info.description || "Printed on demand with the artwork's full colour field intact.")}</p>
            ${
              multi
                ? `<div class="option-group">
                     <div class="option-label"><span>${esc(variants[0].option1 ? "Size / option" : "Option")}</span></div>
                     <div class="option-list" id="optList">
                       ${variants
                         .map(
                           (v, i) =>
                             `<button class="option-btn ${v.id === current.id ? "active" : ""}" data-vid="${v.id}">${esc(v.title)}</button>`
                         )
                         .join("")}
                     </div>
                   </div>`
                : ""
            }
            <div class="option-group">
              <div class="option-label"><span>Quantity</span></div>
              <span class="qty" id="pdpQty">
                <button data-step="-1" aria-label="Decrease">−</button><span>1</span><button data-step="1" aria-label="Increase">+</button>
              </span>
            </div>
            <div class="pdp-actions">
              <button class="btn" id="pdpAdd">Add to bag</button>
              <button class="btn btn-ghost" id="pdpBuy">Buy it now</button>
            </div>
            <div class="accordion">
              <details><summary>Details & materials</summary><div class="acc-body"><ul>${
                (info.details || [])
                  .map((d) => `<li>${esc(d)}</li>`)
                  .join("") || "<li>Made to order, one piece at a time.</li>"
              }</ul></div></details>
              <details><summary>Shipping & returns</summary><div class="acc-body">Each piece is printed to order and ships directly from our production partners — typically 5–12 business days within the US. Returns accepted within 30 days for unworn items; print-on-demand items are made uniquely for you.</div></details>
              <details><summary>The transmission</summary><div class="acc-body">“${esc(p.design)}” is a light language transmission channeled by Morayana. Wearing or living with the piece keeps the codes close to your field.</div></details>
            </div>
          </div>
        </div>
        <section class="band">
          <div class="section-head">
            <div><span class="eyebrow">Same transmission</span><h2 class="section-title">More from ${esc(p.design)}</h2></div>
            <a class="link-arrow" href="${u("artwork/" + p.designSlug + ".html")}">All ${p.design} pieces</a>
          </div>
          <div class="product-grid" id="relatedGrid"></div>
        </section>`;

      // gallery
      host.querySelectorAll(".pdp-thumbs button").forEach((b) =>
        b.addEventListener("click", () => {
          document.getElementById("pdpImg").src = b.dataset.src;
          host.querySelectorAll(".pdp-thumbs button").forEach((x) => x.classList.remove("active"));
          b.classList.add("active");
        })
      );
      // options
      host.querySelectorAll(".option-btn").forEach((b) =>
        b.addEventListener("click", () => {
          current = variants.find((v) => String(v.id) === b.dataset.vid);
          host.querySelectorAll(".option-btn").forEach((x) => x.classList.remove("active"));
          b.classList.add("active");
          document.getElementById("pdpPrice").textContent = money(current.price);
          document.getElementById("pdpAdd").disabled = !current.available;
          document.getElementById("pdpAdd").textContent = current.available
            ? "Add to bag"
            : "Sold out";
        })
      );
      // qty
      let qty = 1;
      host.querySelectorAll("#pdpQty button").forEach((b) =>
        b.addEventListener("click", () => {
          qty = Math.max(1, qty + Number(b.dataset.step));
          host.querySelector("#pdpQty span").textContent = qty;
        })
      );
      document.getElementById("pdpAdd").addEventListener("click", (e) => addToCart(p, current, qty, e.currentTarget));
      document.getElementById("pdpBuy").addEventListener("click", () => {
        location.href = SHOP_ORIGIN + "/cart/" + current.id + ":" + qty;
      });

      const related = CATALOG.products.filter((x) => x.designSlug === p.designSlug && x.id !== p.id);
      renderInto(document.getElementById("relatedGrid"), related, 8);
      observeReveals();
    });
  }

  /* ---------------- artwork page ---------------- */
  function initArtwork() {
    const grid = document.getElementById("artworkGrid");
    if (!grid) return;
    const slug = grid.dataset.slug;
    loadCatalog().then(() => {
      const design = CATALOG.designs.find((d) => d.slug === slug);
      const list = CATALOG.products.filter((p) => p.designSlug === slug);
      renderInto(grid, list, null);
      const countEl = document.getElementById("artworkCount");
      if (countEl) countEl.textContent = list.length + " pieces";
    });
  }

  /* ---------------- collection / design full grids ---------------- */
  function initCollections() {
    document.querySelectorAll("[data-collection]").forEach((grid) => {
      const cat = grid.dataset.collection;
      const designSlug = grid.dataset.design || "";
      let limit = 24;
      const moreWrap = document.getElementById("collectionMore");
      const countEl = document.getElementById("collectionCount");
      loadCatalog().then(() => {
        let list = CATALOG.products.slice();
        if (cat) list = list.filter((p) => p.category === cat);
        if (designSlug) list = list.filter((p) => p.designSlug === designSlug);
        if (countEl) countEl.textContent = list.length + (list.length === 1 ? " piece" : " pieces");
        const paint = () => {
          renderInto(grid, list.slice(0, limit), null);
          if (moreWrap) moreWrap.classList.toggle("hidden", list.length <= limit);
        };
        paint();
        if (moreWrap) {
          const btn = moreWrap.querySelector("button");
          if (btn) {
            btn.onclick = () => {
              limit += 24;
              paint();
            };
          }
        }
      });
    });
  }

  /* ---------------- generic design grids ---------------- */
  function initDesignGrids() {
    document.querySelectorAll("[data-design-grid]").forEach((el) => {
      loadCatalog().then(() => {
        const limit = Number(el.dataset.limit || 0);
        const designs = CATALOG.designs.slice().sort((a, b) => b.count - a.count);
        const slice = limit ? designs.slice(0, limit) : designs;
        el.innerHTML = slice
          .map(
            (d) => `
          <a class="design-tile" href="${u("artwork/" + d.slug + ".html")}">
            <img src="${d.image}" alt="${esc(d.name)}" loading="lazy">
            <span>${esc(d.name)}</span>
          </a>`
          )
          .join("");
        observeReveals(el);
      });
    });
  }

  /* ---------------- featured grids ---------------- */
  function initFeatured() {
    document.querySelectorAll("[data-featured]").forEach((el) => {
      loadCatalog().then(() => {
        const limit = Number(el.dataset.featured || 8);
        const cat = el.dataset.cat || "";
        let pool = CATALOG.products;
        if (cat) pool = pool.filter((p) => p.category === cat);
        // spread across designs so the grid feels curated
        const seen = new Set();
        const picks = [];
        for (const p of pool) {
          if (seen.has(p.designSlug)) continue;
          seen.add(p.designSlug);
          picks.push(p);
          if (picks.length >= limit) break;
        }
        renderInto(el, picks, null);
      });
    });
  }

  /* ---------------- boot ---------------- */
  function boot() {
    // header scroll state
    const header = document.querySelector(".site-header");
    const onScroll = () => header?.classList.toggle("scrolled", window.scrollY > 40);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });

    // mobile nav
    document.querySelector(".menu-btn")?.addEventListener("click", () => {
      document.getElementById("mobileNav")?.classList.add("open");
      document.body.classList.add("no-scroll");
    });
    document.querySelector("#mobileNav .close-nav")?.addEventListener("click", () => {
      document.getElementById("mobileNav")?.classList.remove("open");
      document.body.classList.remove("no-scroll");
    });
    document.querySelectorAll("#mobileNav a").forEach((a) =>
      a.addEventListener("click", () => {
        document.getElementById("mobileNav")?.classList.remove("open");
        document.body.classList.remove("no-scroll");
      })
    );

    // cart open/close
    document.querySelectorAll("[data-open-cart]").forEach((b) =>
      b.addEventListener("click", (e) => {
        e.preventDefault();
        openCart();
      })
    );
    document.getElementById("cartClose")?.addEventListener("click", closeCart);
    document.getElementById("cartScrim")?.addEventListener("click", closeCart);
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeCart();
    });
    document.getElementById("checkoutBtn")?.addEventListener("click", (e) => {
      const href = e.currentTarget.dataset.href;
      if (!href) {
        e.preventDefault();
        toast("Your bag is empty");
        return;
      }
      e.currentTarget.href = href;
    });

    paintCart();
    observeReveals();

    const needsCatalog =
      document.getElementById("shopGrid") ||
      document.getElementById("pdp") ||
      document.getElementById("artworkGrid") ||
      document.querySelector("[data-featured]") ||
      document.querySelector("[data-design-grid]") ||
      document.querySelector("[data-collection]");
    if (needsCatalog) {
      loadCatalog().then(() => {
        initShop();
        initProduct();
        initArtwork();
        initFeatured();
        initDesignGrids();
        initCollections();
      });
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();

  window.LSA = { openCart, closeCart, toast, addToCart };
})();

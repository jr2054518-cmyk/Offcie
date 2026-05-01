/* phase4_catalog_pipes.js v11 — RTV_FIX_v1.29c
 * - 1:1 API row to section mapping
 * - Tile uses v1a-tile classes (matches existing CSS)
 * - tabindex + keyboard handlers for D-pad nav
 */
(function () {
  "use strict";

  function esc(v) {
    return String(v == null ? "" : v)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function jsq(v) {
    return String(v == null ? "" : v)
      .replace(/\\/g, "\\\\")
      .replace(/'/g, "\\'");
  }

  function toRows(payload) {
    if (!payload) return [];
    if (Array.isArray(payload.rows)) return payload.rows.filter(function(r){ return r && Array.isArray(r.items); });
    return [];
  }

  function toItems(payload) {
    if (!payload) return [];
    if (Array.isArray(payload)) return payload;
    if (Array.isArray(payload.items)) return payload.items;
    if (Array.isArray(payload.rows)) {
      return payload.rows.flatMap(function (r) {
        return Array.isArray(r.items) ? r.items : [];
      });
    }
    return [];
  }

  function mapChannelTile(item) {
    var id = item.id || item.tvg_id || item.name || "unknown";
    var name = item.name || item.title || "Channel";
    var poster = item.poster || item.logo_url || item.logo || "";
    var posterSrc = poster ? (poster.indexOf("/api/img") === 0 ? poster : "/api/img?url=" + encodeURIComponent(poster)) : "";
    var href = "/detail/channel/" + encodeURIComponent(String(id));
    var action = "window.location.href='" + esc(href) + "'";
    return (
      '<article class="lt-recent-tile tile" tabindex="0" onclick="' + action + '" onkeydown="if(event.key===\'Enter\'||event.key===\' \'){event.preventDefault();this.click();}">' +
        '<div class="lt-recent-top">' +
          '<img loading="lazy" alt="" onerror="this.style.display=\'none\'" src="' + esc(posterSrc) + '" style="width:48px;height:48px;object-fit:contain;border-radius:6px;background:#1a1c24;flex:0 0 48px;"/>' +
          '<div class="lt-recent-name">' + esc(name) + '</div>' +
        '</div>' +
        '<div class="lt-recent-cta">▶ Watch</div>' +
      '</article>'
    );
  }


  function mapCreatorTile(item) {
    // RTV_FIX_v1.50 (2026-04-29): creator tile — square avatar + name + service badge
    var id = item.id || "unknown";
    var name = item.name || item.title || "Creator";
    var service = (item._service || item.category || "").toLowerCase();
    var avatar = item.poster || item.background || "";
    var avatarSrc = avatar ? (avatar.indexOf("/api/img") === 0 ? avatar : "/api/img?url=" + encodeURIComponent(avatar)) : "";
    var profileUrl = item._external_url || ("https://coomer.st/" + encodeURIComponent(service) + "/user/" + encodeURIComponent(String(id).replace(/^coomer_[^_]+_/, "")));
    var action = "window.open('" + esc(profileUrl) + "','_blank','noopener,noreferrer')";
    var serviceColor = service === "onlyfans" ? "#00AFF0" : (service === "fansly" ? "#1da1f2" : (service === "patreon" ? "#FF424D" : "#888"));
    var keydownAttr = 'onkeydown="if(event.key===\'Enter\'||event.key===\' \'){event.preventDefault();this.click();}"';
    return (
      '<article class="v1a-tile rtv-creator-tile tile" tabindex="0" onclick="' + action + '" ' + keydownAttr + '>' +
        '<div style="position:relative;width:100%;aspect-ratio:1/1;border-radius:50%;overflow:hidden;background:#1a1c24;">' +
          '<img loading="lazy" alt="" onerror="this.style.opacity=0.2" src="' + esc(avatarSrc) + '" style="width:100%;height:100%;object-fit:cover;"/>' +
          '<span style="position:absolute;bottom:6px;right:6px;background:' + serviceColor + ';color:#fff;font:700 9px sans-serif;padding:3px 6px;border-radius:8px;text-transform:uppercase;">' + esc(service) + '</span>' +
        '</div>' +
        '<div style="padding:8px 4px 4px;text-align:center;">' +
          '<span style="font:600 13px/1.2 sans-serif;color:#fff;display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + esc(name) + '</span>' +
        '</div>' +
      '</article>'
    );
  }
function mapTile(item, tab) {
    if (tab === "livetv" || tab === "live_tv" || item.kind === "live_tv" || item.type === "channel") {
      return mapChannelTile(item);
    }
    // RTV_FIX_v1.50 (2026-04-29): Coomer creator tile — opens external profile URL
    if (item.kind === "creator" || item.type === "creator") {
      return mapCreatorTile(item);
    }
    if (tab === "livetv" || tab === "live_tv" || item.kind === "live_tv" || item.type === "channel") return mapChannelTile(item);
    var id = item.id || item.slug || item.handle || item.name || item.title || "unknown";
    var type = item.type || (tab === "series" ? "series" : "movie");
    var title = item.title || item.name || "Untitled";
    var year = item.year || item.releaseInfo || "";
    var sub = year ? String(year) : (item.category || "");
    var poster = item.poster || item.thumbnail || item.image || "";
    var posterSrc = poster ? (poster.indexOf("/api/img") === 0 ? poster : "/api/img?url=" + encodeURIComponent(poster)) : "";
    var href = "/detail/" + encodeURIComponent(type) + "/" + encodeURIComponent(id);
    var action;
    if (tab === "movies" || tab === "movie" || tab === "home") {
      action = "(typeof window.openDetail==='function'?window.openDetail('" + jsq(id) + "','" + jsq(title) + "'):window.location.href='" + esc(href) + "')";
    } else if (tab === "series") {
      action = "(typeof window.openSeriesDetail==='function'?window.openSeriesDetail('" + jsq(id) + "','" + jsq(title) + "'):window.location.href='" + esc(href) + "')";
    } else if (tab === "livetv") {
      action = "(typeof window.openChannel==='function'?window.openChannel('" + jsq(id) + "','" + jsq(title) + "'):window.location.href='/detail/channel/" + encodeURIComponent(String(id || "")) + "')";
    } else {
      action = "window.location.href='" + esc(href) + "'";
    }

    return (
      '<article class="v1a-tile v1a-tile-film tile tile--poster" data-live="1" tabindex="0" onclick="' + action + '" onkeydown="if(event.key===\'Enter\'||event.key===\' \'){event.preventDefault();this.click();}">' +
        '<div class="v1a-tile-img-wrap"><img loading="lazy" alt="' + esc(title) + '" class="v1a-tile-img" src="' + esc(posterSrc) + '"/></div>' +
        '<div class="v1a-tile-meta"><span class="v1a-tile-title">' + esc(title) + '</span>' +
        (sub ? '<span class="v1a-tile-sub">' + esc(sub) + '</span>' : '') + '</div>' +
      '</article>'
    );
  }

  function _mergeUrlParams(endpoint) {
    try {
      var src = new URL(window.location.href);
      var fwdKeys = ["provider", "category", "lang", "region", "q", "filter"];  // RTV_FIX_v1.48 (2026-04-29): forward filter (for /?filter=xxx 18+)
      var url = new URL(endpoint, window.location.origin);
      fwdKeys.forEach(function(k){
        var v = src.searchParams.get(k);
        // RTV_FIX_v1.48 (2026-04-29): URL filter param OVERRIDES endpoint default
        // (so /?filter=xxx switches /home from filter=all -> filter=xxx)
        if (v) url.searchParams.set(k, v);
      });
      return url.pathname + url.search;
    } catch (_e) {
      return endpoint;
    }
  }

  async function fetchEndpoint(endpoint) {
    var res = await fetch(_mergeUrlParams(endpoint), { credentials: "include" });
    if (!res.ok) throw new Error(String(res.status));
    return res.json();
  }

  async function run() {
    var cfg = window.__CATALOG_PIPE_CFG__;
    if (!cfg || !Array.isArray(cfg.endpoints) || !Array.isArray(cfg.selectors)) return;

    var rowSections = Array.from(document.querySelectorAll("section.v1a-row, section.rv-row, [data-row-section]"));
    var sectionInfo = rowSections.map(function (s) {
      return {
        section: s,
        titleEl: s.querySelector(".v1a-row-title, .rv-row-h h2, h2"),
        container: s.querySelector(cfg.selectors.join(", ")) || s.querySelector(".v1a-scroller, .v1a-row-rail, .v1a-rail, .rail"),
      };
    }).filter(function (x) { return x.container; });

    if (!sectionInfo.length) {
      var containers = [];
      cfg.selectors.forEach(function (sel) {
        document.querySelectorAll(sel).forEach(function (el) { containers.push(el); });
      });
      if (!containers.length) return;
      // RTV_FIX_v1.45 (2026-04-29): limit closest() to row-class containers,
      // not the page wrapper section. Otherwise hiding empty rows hides the page.
      sectionInfo = containers.map(function (c) {
        var sec = c.closest(".v1a-row, .rv-row, .h1-section, .lt-spotlight-row, .lt-rail, .lt-lane-grid, .lt-epg-row, .grid-live, .tambien-grid, .pregame-row, .final-row, .ppv-row, .fav-row, .country-row, .es1-fav-row, .es1-cards, .a1b-row, .k4-row, .branded-providers-row, .rv-rail, [data-row-section]");
        return { section: sec || c, titleEl: null, container: c };
      });
    }

    var apiRows = [];
    var fallbackItems = [];
    for (var i = 0; i < cfg.endpoints.length; i += 1) {
      try {
        var data = await fetchEndpoint(cfg.endpoints[i]);
        var rows = toRows(data);
        if (rows.length) apiRows = apiRows.concat(rows);
        else {
          var flat = toItems(data);
          if (flat.length) fallbackItems = fallbackItems.concat(flat);
        }
      } catch (_err) {}
    }

    var tab = cfg.tab || "home";
    var renderedCount = 0;

    sectionInfo.forEach(function (info, idx) {
      var apiRow = apiRows[idx];
      if (!apiRow) {
        if (fallbackItems.length) {
          var slice = fallbackItems.slice(idx * 20, (idx + 1) * 20);
          if (slice.length) {
            info.container.innerHTML = slice.map(function (it) { return mapTile(it, tab); }).join("");
            info.container.dataset.pipeStatus = "live";
            renderedCount += 1;
            return;
          }
        }
        // RTV_FIX_v1.45 (2026-04-29): never hide a page-wrapper section.
        if (info.section && info.section.id && /^(v1|v1a|sp1|es1|lt1|k4|a1b|h1)$/.test(info.section.id)) {
          // page wrapper — leave alone, just empty the container
          if (info.container) info.container.innerHTML = "";
        } else {
          info.section.style.display = "none";
        }
        return;
      }
      if (info.titleEl && apiRow.title) {
        // RTV_FIX_v1.75 (2026-04-29): strip data-i18n so setLang doesn't
        // overwrite our API-sourced row title back to a hardcoded label.
        try { info.titleEl.removeAttribute('data-i18n'); } catch (_) {}
        info.titleEl.textContent = apiRow.title;
        info.titleEl.dataset.rtvHydrated = '1';
      }
      var items = apiRow.items || [];
      if (!items.length) {
        if (info.section && info.section.id && /^(v1|v1a|sp1|es1|lt1|k4|a1b|h1)$/.test(info.section.id)) {
          if (info.container) info.container.innerHTML = "";
        } else {
          info.section.style.display = "none";
        }
        return;
      }
      info.container.innerHTML = items.map(function (it) { return mapTile(it, tab); }).join("");
      info.container.dataset.pipeStatus = "live";
      renderedCount += 1;
    });

    if (apiRows.length > sectionInfo.length && sectionInfo.length > 0) {
      var lastSection = sectionInfo[sectionInfo.length - 1].section;
      var stage = lastSection.parentElement;
      for (var k = sectionInfo.length; k < apiRows.length; k += 1) {
        var apiRow = apiRows[k];
        if (!apiRow.items || !apiRow.items.length) continue;
        var newSec = document.createElement("section");
        newSec.className = "v1a-row";
        newSec.setAttribute("aria-label", apiRow.title || ("Row " + k));
        newSec.innerHTML =
          '<div class="v1a-row-h"><h2 class="v1a-row-title">' + esc(apiRow.title || "") + '</h2></div>' +
          '<div class="v1a-scroller">' + apiRow.items.map(function (it) { return mapTile(it, tab); }).join("") + '</div>';
        stage.appendChild(newSec);
        renderedCount += 1;
      }
    }

    if (!renderedCount) {
      sectionInfo.forEach(function (info) { info.container.dataset.pipeStatus = "placeholder-only"; });
    }
    // RTV_FIX_v1.82 (2026-04-29): notify other scripts that rows are live so
    // they can run a single targeted re-scan instead of mutation-observing.
    try { document.dispatchEvent(new CustomEvent("rtv:rows-rendered", { detail: { renderedCount: renderedCount } })); } catch (_) {}
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run);
  } else {
    run();
  }
})();

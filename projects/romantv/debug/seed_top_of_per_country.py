#!/usr/bin/env python3
"""Seed the 18+ catalog with top OF creators per country (LATAM-heavy per Juan).

Strategy:
  1. Curated candidate list per country (well-known names, OF/Coomer-likely)
  2. For each, search of_creators_index by slug (exact + LIKE) — only keep hits
  3. Create/update a `of_creators_starred` table:
       slug TEXT, service TEXT, country TEXT, rank INTEGER, starred_at INTEGER
       PRIMARY KEY (slug, service)
  4. Report per country: hit/miss summary

This populates the 18+ tab "By Country" rows immediately. Misses get logged
so we can manually verify alt-spellings later.
"""
import sqlite3, time, sys, urllib.request, json
from pathlib import Path

DB = "/root/mxstream-app/data/romantv.db"

CANDIDATES = {
    "MX": [  # Mexico — Juan's family market
        "karelyruizoficial", "karely76", "yerimua", "yeri_mua",
        "shantaljimenez", "shantal", "daniraqib", "daniraqibvip",
        "celialorabella", "celialora", "kimberlyloaiza", "kim_loaiza",
        "yumichoaibe", "yumichoa",
        "lynaperez", "lyna_perez",
        "ari_demexico", "vannamanuela",
        "ladymorenax", "izzylopez",
        "michellesalas", "fernandaoficial",
        "daniarauz", "danielatapia_mx",
    ],
    "AR": [  # Argentina
        "silvinaluna", "silvina_luna", "jimenabaron", "evangelinacarrozzo",
        "sabrinarojas", "paulachavesok", "laliesposito", "lali_esposito",
        "charlotcaniggia", "pampita_oficial", "luisaalbinoni",
        "ninapatera", "robigarcia",
    ],
    "BR": [  # Brazil
        "anaclaudia", "andressaurach", "andressaurachvip",
        "karinabacchi", "marylina", "ananatacha", "ana_natacha",
        "brunamarquezineok", "gracianny", "andressabarbosa",
        "evelynsouza", "mariananolasco", "carolbiazin",
    ],
    "US": [  # US (English-language)
        "bellathorne", "larsapippen", "sommerray", "demirose",
        "sophiebody", "mati_marroni_", "kennaalexisbabe",
        "morganleighnoyes", "alexis_renee_", "abbylynnxoxo",
        "brookemonk", "danielleruhl", "victoriaspears",
        "hidoricolds", "gabbiehanna", "amouranth",
    ],
    "CO": [  # Colombia
        "luisafernandaw", "marbelle_official", "karinajelinek",
        "andreaserna", "taliananavarro", "isabellitareina",
        "danielatapia", "andreaiserrano",
        "lvranderson", "pamelaalfaro", "lvranderson_co",
    ],
    "ES": [  # Spain
        "bellaterraisi", "sofiasuescun", "anabelpantoja",
        "mariapombo", "dulceida", "estercanadas",
        "paulaechevarria", "lapelopez", "alba_lopez",
        "anitamatamoros",
    ],
    "UK": [  # United Kingdom
        "demirose_official", "amy_jackson", "emily_atack",
        "ellieleen", "scarlettmorgan_uk", "helen_flanagan",
        "candice_miller_uk", "ellinoraurora",
        "katyperry_uk",
    ],
    "FR": [  # France
        "annapavaga", "lou_lesage", "thylane.lena.rose.blondeau",
        "marinapowel_", "manon_marsault",
    ],
}


def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    # Create starred table if missing
    cur.execute("""
    CREATE TABLE IF NOT EXISTS of_creators_starred (
        slug TEXT NOT NULL,
        service TEXT NOT NULL,
        country TEXT NOT NULL,
        rank INTEGER NOT NULL DEFAULT 100,
        starred_at INTEGER NOT NULL DEFAULT (unixepoch()),
        starred_by TEXT,
        notes TEXT,
        PRIMARY KEY (slug, service)
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_starred_country ON of_creators_starred(country, rank)")
    con.commit()

    total_hits, total_miss = 0, 0
    report = []
    for country, candidates in CANDIDATES.items():
        hits = []
        misses = []
        for rank, slug in enumerate(candidates, start=1):
            # Try exact match first, then LIKE
            row = cur.execute(
                "SELECT slug, service FROM of_creators_index WHERE slug = ?",
                (slug,)
            ).fetchone()
            if not row:
                row = cur.execute(
                    "SELECT slug, service FROM of_creators_index WHERE slug LIKE ? LIMIT 1",
                    (slug + "%",)
                ).fetchone()
            if row:
                # Insert/update starred entry
                cur.execute("""
                    INSERT INTO of_creators_starred (slug, service, country, rank, starred_by)
                    VALUES (?, ?, ?, ?, 'top_country_seed_v1')
                    ON CONFLICT(slug, service) DO UPDATE
                    SET country=excluded.country, rank=MIN(rank, excluded.rank), starred_at=unixepoch()
                """, (row[0], row[1], country, rank))
                hits.append(f"{row[0]} ({row[1]})")
            else:
                misses.append(slug)
        report.append((country, len(hits), len(misses), hits, misses))
        total_hits += len(hits)
        total_miss += len(misses)
    con.commit()

    # Pretty print
    print(f"\n{'='*60}")
    print(f"SEED TOP OF CREATORS PER COUNTRY — Apr 28 2026")
    print(f"{'='*60}\n")
    for country, h, m, hits, misses in report:
        print(f"## {country} — {h} hits / {m} misses")
        if hits:
            print("   ✅ added: " + ", ".join(hits[:8]))
            if len(hits) > 8: print(f"     (+{len(hits)-8} more)")
        if misses:
            print(f"   ⚠ missed: {', '.join(misses[:8])}")
        print()
    print(f"\nTOTAL: {total_hits} starred, {total_miss} not found in Coomer index\n")
    print(f"Table: of_creators_starred · query like:")
    print(f"  SELECT slug, country, rank FROM of_creators_starred WHERE country='MX' ORDER BY rank;")
    con.close()

if __name__ == "__main__":
    main()

# bizflow

The invoice/document operations chain, cut from tools proven on real supplier
invoices (S400 audit, 2026-08-29 — validated end-to-end on a genuine 6-page
270-line Italian export invoice):

```
fetch            convert              extract                analyze          optimize
hot folder  -->  ocrmypdf --skip-text ->  invoice2data (header JSON)   -->  duckdb   -->  stockpyl EOQ
(entr)           markitdown (-> MD)       pdfplumber geometry harvest       (SQL,         ortools CP-SAT
                                          (line items CSV + Parquet)        Parquet)      (pallet packing)
```

## Install

```bash
python3 install.py            # apt layer + bizvenv + templates + smoke tests
python3 install.py --check    # dry-run
python3 install.py --smoke-only
```

Idempotent; safe to re-run. Without root it prints the one `apt-get` command
left for an admin and completes every user-space phase. The venv healer knows
the `--system-site-packages` shadow gotcha (packages breaking in both
directions) and self-repairs with `--upgrade --ignore-installed`.

## Use

```bash
bizflow process FA018407.pdf --out out/     # header JSON + items CSV/Parquet + summary
bizflow analyze out/FA018407-items.csv      # reconciliation, brands, top items
bizflow optimize out/FA018407-items.csv     # EOQ table + optimal pallet plan
bizflow convert order.pdf -o order.md       # LLM-readable Markdown
bizflow ocr scan.pdf clean.pdf              # searchable PDF/A (ita+eng)
scripts/watch.sh ~/inbox ~/out              # hot folder daemon
```

## Vendor onboarding (new supplier)

1. `pdftotext -layout invoice.pdf -` and locate the label/value zones.
   Beware: `-layout` scrambles columns — a value can sit on a different
   label's line.
2. Header template → `templates/<vendor>.yml` (invoice2data format; use
   `[\s\S]{0,400}?` to bridge scattered label/value, `decimal_separator: ','`
   for EU vendors). Install copies these to `~/.local/share/invoice2data-templates/`.
3. Line-item layout → `bizflow/layouts/<vendor>.yml`: column header names as
   printed (compound headers as word lists); pass with `--layout`.

## Numbers that validated the chain (FA018407, Le Delizie del Sud)

270/270 line items harvested; printed line totals 10.738,73 vs declared
10.738,37 reconciled as per-line rounding drift (unrounded qty x Mpl x
4-decimal piece price = 10.738,3663 -> rounds once); optimal 5-pallet packing
(1,884 kg @ 450 kg cap) proven in 0.1 s; per-SKU EOQ 90-130 CT vs 5-8 ordered
quantifying the joint-replenishment consolidation.

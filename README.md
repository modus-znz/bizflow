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

## Server deploy (slow-egress hosts)

Some servers reach PyPI/mirrors at dial-up speed while inbound rsync from a
dev machine runs fast. Ship everything pre-fetched:

```bash
# on the dev machine (matching OS/arch/python)
pip download -r requirements.txt -d wheelhouse/
pip download setuptools wheel -d wheelhouse/
# verify completeness: offline install into a BARE venv must succeed
python3 -m venv /tmp/t && /tmp/t/bin/pip install --no-index --find-links wheelhouse/ -e .
# apt layer: let the SERVER compute its own missing-deb closure, fetch here
ssh SERVER 'apt-get install --print-uris -y PKGS' | grep "^.http" | cut -d"'" -f2 > uris.txt
xargs -P 8 -n 1 curl -fsSO < uris.txt   # into debs/; -f or an error page becomes a .deb
for f in debs/*.deb; do dpkg-deb -I "$f" >/dev/null || echo "BAD: $f"; done
rsync -a wheelhouse/ debs/ SERVER:...

# Debian-family server that reaches Cloudflare? Fetch debs on the server
# straight from https://cloudflaremirrors.com/debian -- the official pool on
# Cloudflare's CDN. Measured 6.9 MB/s where deb.debian.org crawled at 20 KB/s.
# Note: apt-get install with local .deb args may still re-download some
# same-version, same-hash packages from the archive (observed 6/30; suspected
# %-encoded filenames / epoch mapping) -- decode names when pre-fetching.

# If the rsync path itself crawls (e.g. relayed Tailscale) but the server has
# healthy CDN peering: tar the payload, serve it locally over HTTP WITH Range
# support (stdlib http.server answers 200-only; aria2c needs 206 to split),
# expose it via a cloudflared quick tunnel, and pull on the server with
#   aria2c -c -x 8 -s 8 -k 4M URL
# Measured on town-noc: 25 KB/s rsync vs ~0.4-1.5 MB/s tunneled aria2c.
# Always ship SHA256SUMS and gate on sha256sum -c before extracting.

# on the server
python3 install.py --no-apt --no-bin --wheelhouse ~/wheelhouse
sudo apt-get install -y ~/debs/*.deb     # the one root step
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

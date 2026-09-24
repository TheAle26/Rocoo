# AI Prompt: adapt a client's shipment spreadsheet for the Shipping Tool

> **For the person using this:** open a new chat in an AI that can read and create files (ChatGPT or Claude). Attach the client's spreadsheet (`.xlsx` or `.csv`) and, if you have it, the client's instructions email. Then paste this whole document and send it. The AI will ask you a few questions and give you back a file ready to upload.

---

## Your role (instructions for the AI)

You are converting a **client's packing list** into the exact format that a small warehouse labeling program (the "Shipping Tool") accepts. The person talking to you works in the warehouse, is **not technical**, and may write in Spanish or English: **answer in the language they use**, in short, plain sentences.

Clients send their spreadsheets in a different layout every time: title rows above the headers, other column names, merged cells, extra columns, totals and notes at the bottom, columns in Spanish. Your job is to **map** their columns onto the 5 columns below, **clean** the rows, **check** the numbers, and **deliver a file**.

Hard rules:

1. **Never change, invent, round or "fix" any code or quantity.** Copy UPCs, EANs, FNSKUs, box IDs and quantities exactly. If something looks wrong, **report it and ask**; don't correct it silently.
2. **Never drop a data row without saying so.** Tell the user how many rows you removed and why (title, blank, totals, notes).
3. **Ask before guessing.** If two columns could be the search key, or you can't tell which rows go to Amazon, ask.
4. **Keep every code as text.** Never let `198605562976` become `1.98606E+11`, and never remove leading zeros from the source data.
5. Deliver an **`.xlsx` file** whose name ends in lowercase `.xlsx`. Don't deliver a semicolon-separated CSV.
6. If you **can't create files** in this chat, say so plainly and give the user step-by-step Excel instructions instead (rename headers, delete rows, a formula for `Master Box #`), in their language.

---

## How the program works (so you understand what each column is for)

1. The worker **scans or types** a value and presses Enter.
2. The program shows **every row** whose `UPC/EAN (GTIN)` equals that value, in file order. Each row shows its `Master Box #` as a title, its `Quantity` and its `Amazon Labels`.
3. On each row the worker can press:
   - **Shoes (N):** prints N small labels, using `FNSKU` to find the product name in a separate FNSKU labels PDF;
   - **Big Box:** finds the page of the Amazon 4x6 box labels PDF that contains the `Amazon Labels` text, and prints that page;
   - **Mark Done:** marks that row as finished.

So:

- `UPC/EAN (GTIN)` is **whatever the worker will scan or type**. It is **not always a UPC**. It can be a product UPC, an EAN, or a box/pallet reference number written on the box.
- **Several rows may share the same value**; that's how the worker gets a list to choose from.

---

## The target format (exact)

**One sheet. Row 1 = headers. Data from row 2. Nothing else: no title rows, no totals, no notes.**

| Column (exact name, exact spelling) | Required | Content | Rules |
|---|---|---|---|
| `UPC/EAN (GTIN)` | yes | The value the worker scans or types to find the row | Text. No spaces. Must not be empty on a data row. Leading zeros are ignored by the program, so `0123` and `123` count as the same value. |
| `Master Box #` | yes | Title shown on the row | Make it recognizable to the person at the box, e.g. `Box 4 - ARIZONA EVA WHITE 37` or `A410 - M CLIFTON 10 09D`. |
| `Quantity` | yes | Number of units (pairs) on that row, which is how many small labels get printed | **A whole number on every data row.** Empty or text makes the program crash when loading. |
| `FNSKU` | yes | Amazon FNSKU, e.g. `X004IXFTO3` | `X` + 9 letters/digits. Leave it empty on rows that don't go to Amazon. |
| `Amazon Labels` | yes | Amazon box ID printed on the 4x6 label, e.g. `FBA19QHGWM04U000501` | The column must exist, or the program crashes. The text must match the box labels PDF **exactly**. Put `SET ASIDE` on rows that don't go to Amazon. |
| `Style Name`, `Size`, `Color Code` | optional | Product description | Shown by newer versions of the program; harmless in older ones. |

Other columns are allowed and ignored. **Do not** add a `DONE` column: the program adds it itself, and a wrong value there would mark boxes as already finished.

### Rows that don't go to Amazon ("set aside")

Some shipments contain boxes that stay in the warehouse. They usually have **no Amazon box ID and no FNSKU**. Some files also mark them with a column like "Set Aside" instead of "Shipment".

Keep them in the file so the worker sees them, but:

- `Amazon Labels` = `SET ASIDE`;
- `FNSKU` empty;
- `Master Box #` includes `SET ASIDE (NO VA A AMAZON)`, so it's obvious on screen. That's what the warehouse is used to seeing, even in English.

---

## Questions to ask the user (in their language, one message, short)

Ask only what you can't work out from the file, and **propose your best guess** for each:

1. **"What do you scan or type to find a box?"** For example the shoe box barcode (UPC/EAN), or a reference number written on the master box. Point to the column you think it is, with 2–3 example values.
2. **"How is each physical box identified?"** For example a box number, pallet + box, or a master box code. You'll use it for `Master Box #`.
3. **"Which rows go to Amazon?"** Propose your guess: rows with an Amazon box ID, and the rest are set aside.
4. **"What totals did the client give you?"** Total units, units to Amazon, number of boxes. If the email is attached, read them yourself and just confirm.

---

## Checks you must run and report before handing over the file

Show a short summary like this:

```
Rows kept: 644   (removed 6: 1 totals, 2 blank, 3 footer notes; the title row above the headers was skipped)
Units: total 6747 | to Amazon 6223 | set aside 524      <- matches the client's email
Amazon box IDs: 586 distinct | set-aside rows: 58
Search values: 27 distinct | most rows for one value: 38
Warnings: none
First rows:
  453901 | Box 1 - ARIZONA EVA WHITE 37 | 12 | X004IXFTO3 | FBA19QHGWM04U000501
  ...
```

Warn about any of these:

- **Totals that don't match** the client's numbers. Stop and ask before delivering.
- **Quantity** that is empty, not a whole number, or 0.
- **Search values** that look like scientific notation (`E+`), contain spaces, or are empty.
- **An Amazon box ID used on more than one row.** That's normal when one box holds several products; say how many and ask the user to confirm.
- **Rows that go to Amazon but have no FNSKU**, or FNSKUs that aren't `X` + 9 characters.
- **Two or more columns that could be the search key.** Say which one you used.

---

## Reference script (Python / pandas)

Adapt the settings at the top to the file, run it, and show the user the printed summary. It keeps only rows that have a search value and a whole-number quantity, which drops titles, blanks, totals and footers. It builds `Master Box #`, marks set-aside rows, runs the checks and saves an `.xlsx` with codes stored as text.

It was tested on two real client layouts: the Birkenstock one with the header on row 2 and a pallet reference as the search key, and the Hoka one with the UPC as the search key. In both cases the output loaded correctly in the program.

```python
import re
import pandas as pd

# ---- 1. Fill these in for the file you received ---------------------------
SRC = "client file.xlsx"            # the client's file (.xlsx or .csv)
OUT = "SHIPMENT - for the app.xlsx"
HEADER_ROW = 1                      # 0-based: 0 = first row, 1 = second row...
SEARCH_KEY = "Pallet Salida"        # what the worker scans or types
QUANTITY = "QTY"                    # pairs on the row
FNSKU = "FNSKU"
AMAZON_LABEL = "AMAZON Labels"      # Amazon box ID, e.g. FBA19QHGWM04U000501
# Master Box # = PREFIX + first part + " - " + the other parts joined by spaces,
# e.g. "Box 4 - ARIZONA EVA WHITE 37".
TITLE_PARTS = ["BOX O", "Description", "Size"]
TITLE_PREFIX = "Box "               # text put before the first part
# Optional columns shown in newer versions of the program.
EXTRA = {"Style Name": "Description", "Size": "Size"}
# Sort order of the rows (the program lists matches in file order).
SORT_BY = ["Pallet Salida", "BOX O"]
# ---------------------------------------------------------------------------

read = pd.read_excel if SRC.lower().endswith((".xlsx", ".xls")) else pd.read_csv
raw = read(SRC, dtype=str, header=HEADER_ROW)
raw.columns = [str(c).strip() for c in raw.columns]
raw = raw.apply(lambda s: s.str.strip() if s.dtype == object else s)

# Keep only real data rows: a search key AND a whole-number quantity.
# This drops title rows, blank rows, totals and footers.
qty_ok = raw[QUANTITY].fillna("").str.fullmatch(r"\d+(\.0+)?")
key_ok = raw[SEARCH_KEY].fillna("").str.len() > 0
dropped = raw[~(qty_ok & key_ok)]
df = raw[qty_ok & key_ok].copy()

for c in SORT_BY:
    df["_sort_" + c] = pd.to_numeric(df[c], errors="coerce")
df = df.sort_values(["_sort_" + c for c in SORT_BY] + SORT_BY, kind="stable")

label = df[AMAZON_LABEL].fillna("")
set_aside = label == ""
first = df[TITLE_PARTS[0]].fillna("")
rest = df[TITLE_PARTS[1:]].fillna("").agg(" ".join, axis=1).str.strip()
title = (TITLE_PREFIX + first + " - "
         + set_aside.map({True: "SET ASIDE (NO VA A AMAZON) - ", False: ""}) + rest)

out = pd.DataFrame({
    "UPC/EAN (GTIN)": df[SEARCH_KEY],
    "Master Box #": title,
    "Quantity": df[QUANTITY].str.replace(r"\.0+$", "", regex=True),
    "FNSKU": df[FNSKU].fillna(""),
    "Amazon Labels": label.where(~set_aside, "SET ASIDE"),
})
for new, src in EXTRA.items():
    out[new] = df[src].fillna("")

# ---- 2. Checks: report every one of these to the user ----------------------
q = out["Quantity"].astype(int)
problems = []
if out["UPC/EAN (GTIN)"].str.contains(r"[Ee]\+|\s", regex=True).any():
    problems.append("search key looks like scientific notation or has spaces")
dup = out.loc[~set_aside, "Amazon Labels"].duplicated().sum()
if dup:
    problems.append(f"{dup} rows reuse an Amazon box ID already used above (normal when one box holds several products - confirm with the user)")
nofn = ((out["FNSKU"] == "") & ~set_aside).sum()
if nofn:
    problems.append(f"{nofn} rows go to Amazon but have no FNSKU")
if not out["FNSKU"][out["FNSKU"] != ""].str.fullmatch(r"X[A-Z0-9]{9}").all():
    problems.append("some FNSKUs don't look like X + 9 characters")

print(f"rows kept: {len(out)}   rows dropped: {len(dropped)}")
print(f"pairs: total {q.sum()} | to Amazon {q[~set_aside].sum()} | set aside {q[set_aside].sum()}")
print(f"Amazon box IDs: {out.loc[~set_aside, 'Amazon Labels'].nunique()} | set-aside rows: {set_aside.sum()}")
print(f"search keys: {out['UPC/EAN (GTIN)'].nunique()} | most rows for one key: "
      f"{out['UPC/EAN (GTIN)'].value_counts().max()}")
print("problems:", problems or "none")
print(out.head(5).to_string(index=False))

# ---- 3. Save: codes as text so Excel can't turn them into 1.98E+11 --------
with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
    out.to_excel(xw, index=False, sheet_name="Shipment")
    for row in xw.sheets["Shipment"].iter_rows(min_row=2):
        for cell in row:
            cell.number_format = "@"
print("saved", OUT)
```

Settings used for the two known layouts:

| Setting | Birkenstock (AGL packing list) | Hoka |
|---|---|---|
| `HEADER_ROW` | `1` (row 1 is a title "PACKING LIST") | `0` |
| `SEARCH_KEY` | `"Pallet Salida"` (6-digit reference written on the box) | `"UPC/EAN (GTIN)"` (shoe box barcode) |
| `QUANTITY` | `"QTY"` | `"Quantity"` |
| `FNSKU` | `"FNSKU"` | `"FNSKU"` |
| `AMAZON_LABEL` | `"AMAZON Labels"` | `"Amazon Labels"` |
| `TITLE_PARTS` / `TITLE_PREFIX` | `["BOX O", "Description", "Size"]` / `"Box "` | `["Master Box #", "Style Name", "Size"]` / `""` |
| `SORT_BY` | `["Pallet Salida", "BOX O"]` | `["Master Box #"]` |

Known quirks of the Birkenstock / AGL layout:

- The product has two barcodes: `EAN-CODE` (13 digits) and `UPC` (12 digits). They are different codes, not the same code with a zero added.
- `BOX O` restarts at 1 on every pallet (`Pallet Salida`), so the box number alone is not unique.
- There are dimension and weight columns with comma decimals (`4,5`). Ignore them.

---

## What to tell the user at the end

1. The file name, and that they should save it in the shipment's folder next to the original, without overwriting the original.
2. The summary above, and whether the totals matched.
3. What they will scan or type in the program. For example: *"Type the 6-digit reference written on the box, e.g. 453909, and press Enter."*
4. A reminder:
   - load it in the program with **Upload & Process** together with the 4x6 box labels PDF and the FNSKU labels PDF;
   - do a test print first;
   - **never upload files again over a shipment that's already in progress**, because in the current version that erases the progress.

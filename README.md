# Rocco Shipping Tool

A small web app that runs on the packing PC. A worker scans a shoe box's
barcode, the app says which master box it belongs to, and prints the labels
for it.

Nothing is hosted anywhere. It runs on the PC in front of you, at
`http://127.0.0.1:5000`, and only that PC can reach it.

---

## Running it

Double-click **`start_app.bat`**. It downloads the latest version, checks the
dependencies, and opens the browser by itself.

Leave the black window open while you work. To stop the app, click
**Shut down** in the browser — not the X on the black window.

If the black window shows a warning, read it. It only warns about things that
need a person: no internet to download updates, a printer not configured, or
Python missing.

---

## First time on a new PC

1. Install **Python**, ticking **"Add Python to PATH"** during the install.
2. Install **Git**, so the PC can receive updates.
3. Copy `printers.example.json` to `printers.json` and put in the exact names
   of that PC's two printers:

   ```json
   {
     "shoe_printer": "Zebra ZD421 (shoe labels)",
     "big_box_printer": "Zebra ZT230 (box labels)"
   }
   ```

   The names must match Windows exactly. To list them:

   ```bash
   python -c "import printer; printer.list_available_printers()"
   ```

   `printers.json` is deliberately not shared between PCs, because every PC has
   different printers. It is never overwritten by an update.

4. Run `start_app.bat`. The first run builds the environment and takes a few
   minutes.

---

## Using it

**Starting a shipment** — upload three files: the shipment spreadsheet
(`.csv` or `.xlsx`), the big box label PDF, and the small box label PDF.

**Scanning** — point the gun at the barcode and shoot. The app lists every
master box that shoe belongs to, with a button to print the shoe labels, a
button to print the big box label, and a button to mark the box done.

**When a barcode will not scan** — type into the same box and press Enter.
Any of these work:

| Type this          | To find                                      |
| ------------------ | -------------------------------------------- |
| `62976`            | the last 5 digits of the UPC (enough to be unique) |
| `A410`             | a master box by its number                   |
| `X0052RHGPJ`       | an FNSKU                                     |
| `clifton 09.5`     | a style and size                             |

If more than one thing matches you get a list showing style, size and colour —
pick the one you are holding.

**Mixed boxes** — some master boxes hold more than one kind of shoe. Looking a
box up by its number shows everything inside it. Whether the big box label gets
printed once or once per shoe is the worker's call; the app does not decide.

**Stopping and coming back** — progress is saved as you go. If the PC restarts,
just start the app again; it reopens the same shipment where you left it. You
do **not** need to upload the files again.

> Uploading files again **erases the shipment in progress**. The app warns you
> and asks first — read that screen before clicking through it.

**Download (CSV)** exports the spreadsheet with the done marks filled in.

---

## How updates work

`start_app.bat` runs `git pull origin main` on every start, so pushing to
`main` updates every PC the next time it opens the app.

Files that each PC changes on its own — `printers.json` and the label images
the app generates while printing — are deliberately not tracked, because a
locally-modified tracked file makes the pull fail and quietly freezes that PC
on an old version.

If a PC reports that it could not download the latest version, it is still
running the old one. Read the git message in the black window.

---

## The pieces

| File            | What it does                                              |
| --------------- | --------------------------------------------------------- |
| `app.py`        | Web routes, session handling, in-memory indexes            |
| `search_cvs.py` | Builds the lookup indexes; turns what was typed into a hit |
| `shoe_box.py`   | Reads the small box PDF; draws the shoe label image        |
| `printer.py`    | Talks to Windows printing; extracts big box PDF pages      |
| `zebra_print.py`| Unused. Raw ZPL over the network, kept for reference       |
| `output/`       | The shipment in progress. Not in git                       |

The shipment lives in `output/actual_shipment.csv` and is rewritten every time
a box is marked done, so a crash costs nothing.

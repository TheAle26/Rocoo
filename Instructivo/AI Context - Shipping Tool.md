# AI Context: Shipping Tool (Rocco)

> **For the person using this:** paste this whole file into your AI chat (Claude, ChatGPT, etc.) and then describe what is happening. It contains everything the AI needs to explain how to install, use and fix the program.

---

## Instructions for the AI

You are going to help a **non-technical** person install and use an Amazon shipment labeling program on a Windows PC. Rules:

1. Explain **step by step**, one step at a time, and wait for the person to confirm before moving on. Answer in the language the person writes in.
2. When you give a command, say **where to type it** (PowerShell, or the black window) and ask the person to copy back what it prints.
3. **Never** have them delete or overwrite the `output\` folder, which holds the shipment progress, or the `printers.json` file, without making a copy first.
4. **Never** have them run `git reset --hard`, `git clean` or `git push`, or edit `.py`, `.html` or `.bat` files. If the program itself needs changing, they should tell **Alejo**, the program's owner.
5. If something isn't covered in this document, say so and suggest asking Alejo instead of guessing.

---

## What the program is

It is a small web application that runs **on the same PC**: it opens in the browser at `http://127.0.0.1:5000` and is not on the internet. It is used to label a shipment of boxes going to Amazon (FBA):

- The operator **scans or types** a code.
- The program shows which **master box** that product goes in.
- From there, two kinds of labels are printed:
  - **Shoes (N):** N small FNSKU labels, one per pair.
  - **Big Box:** the Amazon 4x6 label for the master box.
- When a box is finished, the operator presses **Mark Done** and the progress is saved.

Technical details:

- Built in Python 3.13 with Flask and served with `waitress`.
- Prints through the Windows print queue using `pywin32`.
- Reads PDFs with PyPDF2 and PyMuPDF, and generates barcodes with `python-barcode` and Pillow.

---

## Installing on a new PC

**Requirements:**

- Windows 10 or 11 with internet access.
- A GitHub account invited to the **private** repository `https://github.com/TheAle26/Rocoo`. Alejo sends the invitation and it is accepted from the email.
- The two label printers installed in Windows:
  - the small-label printer for the pairs;
  - the 4x6 label printer for the boxes.
- A USB barcode scanner. It works like a keyboard: it types the code and presses Enter.

**Steps:**

1. **Install Python 3.13** from https://www.python.org/downloads/windows/.
   - Use **3.13**, not a newer version: some libraries pinned by the program may not be available for later versions.
   - On the first screen of the installer, **tick "Add python.exe to PATH"**.
   - To check it, in PowerShell: `python --version` must say `Python 3.13.x`.
2. **Install Git** from https://git-scm.com/download/win, with all the default options. To check it: `git --version`.
3. **Download the program.** In PowerShell:
   ```
   git clone https://github.com/TheAle26/Rocoo.git C:\ShippingTool
   ```
   A browser window opens to sign in to GitHub; accept it. The sign-in is remembered.
4. **Configure the printers.**
   - Get their exact names, in PowerShell:
     ```
     Get-Printer | Select-Object Name
     ```
   - Open `C:\ShippingTool\printers.json` with Notepad. If it doesn't exist, copy `printers.example.json` and rename the copy to `printers.json`.
   - Leave it like this, with the names **copied exactly**:
     ```json
     {
       "shoe_printer": "EXACT NAME of the small-label printer",
       "big_box_printer": "EXACT NAME of the 4x6 printer"
     }
     ```
   - Keep the quotes, the colons and the comma.
5. **First start.** Double-click `C:\ShippingTool\start_app.bat`.
   - The first time it takes a few minutes, because it creates the `venv` folder and installs the libraries.
   - Then the browser opens by itself.
   - If Windows asks about the **Firewall**, click **Cancel**: only this PC uses the program.
6. **Desktop shortcut.** Right-click `start_app.bat` > Show more options > Send to > Desktop (create shortcut).

---

## Daily use

**Start:** double-click `start_app.bat`.

- A black window opens. **Don't close it** while working.
- If the browser says "can't reach this page", wait a few seconds and press F5.

**Load a new shipment (only the first time for each shipment):** on the start screen, upload 3 files and click **Upload & Process**:

| Field | What goes in it |
|---|---|
| 1. Shipment Data | the shipment spreadsheet (`.csv` or `.xlsx`) |
| Big Box Label | the Amazon PDF with the 4x6 box labels |
| Small Box Label | the PDF with the FNSKU labels for the pairs |

**Working:**

1. Scan or type the code into the large input field and press Enter.
2. The boxes appear. On each one:
   - **Shoes (N)** prints the labels for the pairs;
   - **Big Box** prints the box label;
   - **Mark Done** marks the box as finished.
3. **View Data** shows the full table. **Download (CSV)** downloads the spreadsheet with the finished boxes marked.

**Stop:** the red **Shut down** button at the top right. Don't close the black window with the X.

### VERY IMPORTANT: resuming a shipment

If the program was closed or the PC restarted, when opening it again click **Continue Work**. **Do not upload the files again:**

- In the **old** version, uploading them again **erases all progress** (every box goes back to "not done") without warning.
- In the **new** version, the program warns first and resumes the shipment by itself.

To tell which version is running, look at the scan screen:

- if the top left says **"Back to Home"**, it is the **old** one;
- if it says **"Start a new shipment"** and shows "X of Y done", it is the **new** one.

---

## Birkenstock shipment FBA19QHGWM04 (AGLMIA225, 6,747 pairs)

**Files**, which are not on GitHub: they are passed by USB stick, Drive or WhatsApp.

- Spreadsheet: `Birkenstock FBA19QHGWM04 - para la app.csv`. It is an adapted version of AGL's packing list; the original doesn't work in the program as is.
- Pair labels: `Birkenstock FBA19QHGWM04 - etiquetas FNSKU (generado).pdf`. Alejo generated it from the spreadsheet data. If AGL sends the official one, use that.
- Box labels: the Amazon 4x6 PDF that AGL sends. It has 586 labels, from `FBA19QHGWM04U000001` to `U000586`.

**How it works:**

- Each master box has a **6-digit reference number** written by hand (for example `453909`); many boxes share the same reference.
- Each box also has a **small label with its box number** (1, 2, 3…).
- The `P0468`-style barcode that some boxes have **is not used**.

**Steps:**

1. Type the reference (`453909`) and press Enter.
2. The list appears: "Box 1 - ARIZONA EVA WHITE 37", "Box 2 - …", etc.
3. Find the row with the number from the small label and print from there.

Some boxes contain more than one product; in that case several rows appear with the same box number, and each one has its own Amazon label.

**Rows marked "SET ASIDE (NO VA A AMAZON)":** "no va a Amazon" is Spanish for "does not go to Amazon". Those boxes **are not labeled and not shipped**; they stay in the warehouse. If you press print on one of them you get an error, and that is expected.

Totals:

| Destination | Pairs | Boxes / rows |
|---|---|---|
| Amazon | 6,223 | 586 box labels |
| Set aside | 524 | 58 rows |
| Total | 6,747 | 27 references |

In the spreadsheet, the `UPC/EAN (GTIN)` column deliberately contains the **master box reference** instead of a UPC, so the program can search by it. The products' real UPC and EAN codes are in the `UPC` and `EAN` columns.

---

## Common problems

| What happens | What to do |
|---|---|
| The black window says "Python is not installed" | Reinstall Python 3.13 ticking "Add python.exe to PATH" and restart the PC. |
| The browser says "can't reach this page" | Wait 5 seconds and press F5. If it persists, check that the black window is open and shows no errors. |
| It prints on the wrong printer, or gives a printer error | Check that the names in `printers.json` are **exactly** the ones from `Get-Printer`. In the old version, a blank name silently prints on the Windows default printer; a misspelled name gives an error. |
| The label comes out stretched or cut off | In Windows: Settings > Printers > (the printer) > Printing preferences, and set the right paper size: 4x6 for the boxes and the label size for the pairs. |
| "UPC … not found" / "No match" | Check the number typed. For Birkenstock you search by the **master box reference** (6 digits). Check in View Data that the right spreadsheet is loaded. |
| "Page for label … not found" | That box label is not in the 4x6 PDF that was uploaded, or it is a SET ASIDE row. |
| "FNSKU … not found in PDF" | The small-label PDF doesn't have that product. Check that it is the PDF for this shipment. |
| "No previous session found" when clicking Continue Work | No shipment is loaded yet: upload the 3 files. |
| The black window was closed by accident | Open `start_app.bat` again and click **Continue Work**. Don't upload the files again. |
| The scanner does nothing | Click inside the "Shoot barcode here…" field and scan again. The scanner must be configured to end with Enter. |

### Updates

`start_app.bat` downloads the latest version from GitHub every time it opens (`git pull origin main`).

When Alejo publishes the new version, that `git pull` **may fail on this PC**. It happens because in the old version the files `printers.json`, `current_label.png` and `current_big_box_label.png` were tracked by git, and they have already been modified on this PC. It shows in the black window with a message like *"Your local changes to the following files would be overwritten by merge"*.

One-time fix, in PowerShell, from `C:\ShippingTool`:

```
cd C:\ShippingTool
copy printers.json printers.json.bak
git checkout -- printers.json current_label.png current_big_box_label.png
git pull origin main
copy printers.json.bak printers.json
```

The last step matters: the new version no longer ships `printers.json` and uses each PC's local copy. After this, updates work on their own again. If the error message is different, copy it in full and send it to Alejo.

**Safe diagnostic commands**, which only read and change nothing:

```
cd C:\ShippingTool
git status
git log --oneline -5
python --version
Get-Printer | Select-Object Name
```

---

## File map (for the AI)

| File / folder | What it is |
|---|---|
| `start_app.bat` | Starts everything: checks Python, creates `venv` the first time, runs `git pull`, installs `requirements.txt`, opens the browser and starts `waitress-serve --port=5000 app:app`. |
| `app.py` | Flask server. Routes: `/` (upload files or Continue Work), `/processing` (scan screen), `/scan`, `/print_shoes`, `/print_big_box`, `/mark_done`, `/view_data`, `/download_csv`, `/shutdown`. |
| `search_cvs.py` | Builds the search indexes from the spreadsheet and finds the page for each label in the box PDF. |
| `shoe_box.py` | Reads the FNSKU label PDF (pattern: FNSKU, product name, "New") and draws each pair's label. |
| `printer.py` | Prints through the Windows queue and extracts the page from the box PDF. Reads `printers.json`. |
| `printers.json` | Names of **this** PC's 2 printers. |
| `output\` | The shipment in progress: `actual_shipment.csv` (with the DONE column) and the 2 PDFs. **Don't delete.** It is rewritten every time Mark Done is pressed. |
| `venv\` | Python's libraries. If it breaks, it can be deleted: `start_app.bat` recreates it. |

Columns the program expects in the spreadsheet: `UPC/EAN (GTIN)`, `Master Box #`, `Quantity`, `FNSKU`, `Amazon Labels`. The `DONE` column is added automatically. The first row must be the header row.

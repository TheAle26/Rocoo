import PyPDF2
import re


def normalize_upc(code):
    """
    Strips whitespace and leading zeros so a 12-digit UPC-A from the spreadsheet
    and a 13-digit EAN-13 scan (same code with a '0' prepended) match each other.
    """
    return str(code).strip().lstrip('0')


def _clean(value):
    """Spreadsheet cells come back as 'nan' strings for empty cells."""
    text = str(value).strip()
    return '' if text.lower() == 'nan' else text


def _key(value):
    """Case- and space-insensitive key for Master Box # and FNSKU lookups."""
    return _clean(value).upper().replace(' ', '')


def build_lookup_index(df):
    """
    Single pass over the shipment producing every index the scan page needs.

    Every index holds references to the SAME box dictionaries, so marking one
    box DONE is visible through all of them without any extra bookkeeping.

    Returns a dict of:
      by_upc    {normalized UPC: [box, ...]}  - one UPC spans up to 6 boxes
      by_box    {UPPER Master Box #: [box, ...]}
      by_fnsku  {UPPER FNSKU: [box, ...]}
      by_row    {row index: box}              - for marking DONE
      all_boxes [box, ...]                    - for free-text search
    """
    index = {
        'by_upc': {},
        'by_box': {},
        'by_fnsku': {},
        'by_row': {},
        'all_boxes': [],
    }
    print("📊 Building shipment lookup index...")

    for row_index, row in df.iterrows():
        upc = normalize_upc(row.get('UPC/EAN (GTIN)', ''))
        if not upc or upc == 'nan':
            # Skips blank rows and the trailing totals row, which carries a
            # Quantity but no UPC, Master Box or FNSKU.
            continue

        master_box = _clean(row.get('Master Box #', ''))
        fnsku = _clean(row.get('FNSKU', ''))
        style = _clean(row.get('Style Name', ''))
        size = _clean(row.get('Size', ''))
        color = _clean(row.get('Color Code', ''))

        try:
            quantity = int(float(row.get('Quantity', 0)))
        except (TypeError, ValueError):
            # A junk Quantity must not abort the whole build.
            quantity = 0

        box = {
            "Master Box #": master_box,
            "UPC": upc,
            "FNSKU": fnsku,
            "Style Name": style,
            "Size": size,
            "Color Code": color,
            "Quantity": quantity,
            "Amazon Labels": _clean(row.get('Amazon Labels', '')),
            "DONE": _clean(row.get('DONE', 'False')) or 'False',
            "Row_Index": row_index,
            # Precomputed so free-text search never rebuilds it per keystroke.
            "_search": ' '.join(
                p for p in (style, size, color, master_box, fnsku) if p
            ).lower(),
        }

        index['all_boxes'].append(box)
        index['by_row'][row_index] = box
        index['by_upc'].setdefault(upc, []).append(box)
        if master_box:
            index['by_box'].setdefault(_key(master_box), []).append(box)
        if fnsku:
            index['by_fnsku'].setdefault(_key(fnsku), []).append(box)

    print(
        f"✅ Indexed {len(index['all_boxes'])} rows: "
        f"{len(index['by_upc'])} UPCs, {len(index['by_box'])} master boxes, "
        f"{len(index['by_fnsku'])} FNSKUs."
    )
    return index


# Below this a partial UPC matches too much of the shipment to be useful.
MIN_SUFFIX_DIGITS = 3
# At or above this the code is a whole barcode rather than a deliberate
# partial. If it does not match exactly we say so instead of guessing by
# suffix, which could silently resolve a mis-keyed digit to the wrong shoe.
FULL_CODE_DIGITS = 12
# Cap on how many candidates a vague query may put on screen.
MAX_CHOICES = 25

DIGITS_PATTERN = re.compile(r'^\d+$')


def _product_summary(upc, boxes):
    """Collapses every box holding one UPC into a single row to choose from."""
    first = boxes[0]
    return {
        "UPC": upc,
        "Style Name": first['Style Name'],
        "Size": first['Size'],
        "Color Code": first['Color Code'],
        "FNSKU": first['FNSKU'],
        "Boxes": len(boxes),
        "Total Quantity": sum(b['Quantity'] for b in boxes),
        "Remaining": sum(1 for b in boxes if b['DONE'].lower() != 'true'),
    }


def _summaries(index, upcs):
    """
    Stable, readable ordering for a list of candidate UPCs.

    Returns every match. Capping is left to the caller so it can tell the
    worker how many were hidden rather than silently truncating.
    """
    rows = [_product_summary(u, index['by_upc'][u]) for u in upcs]
    rows.sort(key=lambda r: (r['Style Name'], r['Size'], r['Color Code']))
    return rows


def _upcs_by_suffix(index, digits):
    return [u for u in index['by_upc'] if u.endswith(digits)]


def _upcs_by_text(index, text, require_all=True):
    """Matches Style Name / Size / Color Code / box / FNSKU on each row."""
    tokens = [t for t in text.lower().split() if t]
    if not tokens:
        return []

    test = all if require_all else any
    found = []
    for box in index['all_boxes']:
        if test(t in box['_search'] for t in tokens):
            if box['UPC'] not in found:
                found.append(box['UPC'])
    return found


def resolve_query(query, index):
    """
    Turns whatever the worker scanned or typed into an action.

    Order matters: an exact UPC is tried first and returns the same shape it
    always has, so the barcode gun's path through /scan is unchanged.

    Returns (kind, payload):
      ('boxes',   [box, ...])      resolved to one item; show the print buttons
      ('choices', [summary, ...])  ambiguous; let the worker pick a UPC
      ('none',    [summary, ...])  no match; payload holds the closest guesses
    """
    raw = str(query or '').strip()
    if not raw:
        return 'none', []

    # 1. Exact UPC. This is the barcode gun, and it stays first and unchanged.
    upc = normalize_upc(raw)
    if upc in index['by_upc']:
        return 'boxes', index['by_upc'][upc]

    # 2. Exact Master Box #. Exact only, because A1, A10 and A100 all exist,
    # so any prefix matching here would be ambiguous. A mixed box returns all
    # of its rows, which is what someone asking for the box wants to see.
    key = _key(raw)
    if key in index['by_box']:
        return 'boxes', index['by_box'][key]

    # 3. Exact FNSKU.
    if key in index['by_fnsku']:
        return 'boxes', index['by_fnsku'][key]

    # 4. Partial UPC. The last 5 digits are unique across this shipment, so
    # typing 5 instead of 12 is the fast path for a barcode that will not scan.
    if DIGITS_PATTERN.match(raw):
        if len(raw) >= FULL_CODE_DIGITS:
            # A whole barcode that missed every exact lookup: do not guess.
            return 'none', _summaries(
                index, _upcs_by_suffix(index, raw[-MIN_SUFFIX_DIGITS:])
            )
        if len(raw) >= MIN_SUFFIX_DIGITS:
            matches = _upcs_by_suffix(index, raw)
            if len(matches) == 1:
                return 'boxes', index['by_upc'][matches[0]]
            if matches:
                return 'choices', _summaries(index, matches)
        return 'none', []

    # 5. Free text over style, size and colour.
    matches = _upcs_by_text(index, raw)
    if len(matches) == 1:
        return 'boxes', index['by_upc'][matches[0]]
    if matches:
        return 'choices', _summaries(index, matches)

    # Nothing matched every word; fall back to anything matching any word.
    return 'none', _summaries(index, _upcs_by_text(index, raw, require_all=False))


def build_amazon_label_to_page_dict(pdf_path, df):
    """
    Maps the 'Amazon Label' string to the exact Page Number in the PDF.
    """
    label_map = {}

    # FIX: Use .dropna() to completely remove empty cells (float NaNs)
    # BEFORE we convert to strings and get the unique values.
    labels_to_find = df['Amazon Labels'].dropna().astype(str).str.strip().unique()

    # A plain substring check would let "P1 - B1" match the pages of
    # "P1 - B10", "P1 - B171", etc. The (?!\d) forbids a digit right after
    # the label, so only the exact box number matches.
    label_patterns = [
        (label, re.compile(re.escape(label) + r'(?!\d)'))
        for label in (str(l) for l in labels_to_find)
        if label and label != 'nan'
    ]

    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            print(f"📄 Scanning {len(reader.pages)} Big Box PDF pages...")

            for page_num in range(len(reader.pages)):
                page_text = reader.pages[page_num].extract_text()

                # Failsafe: PyPDF2 sometimes returns None for perfectly blank pages.
                # We need to make sure page_text is a valid string.
                if not page_text:
                    continue

                for label, pattern in label_patterns:
                    if label not in label_map and pattern.search(page_text):
                        label_map[label] = page_num
                            
        print(f"✅ Successfully mapped {len(label_map)} Big Box Pages.")
        return label_map
        
    except FileNotFoundError:
        print(f"❌ Error: Big box PDF not found at {pdf_path}")
        return {}
    except Exception as e:
        print(f"❌ Unexpected Error scanning Big Box PDF: {e}")
        return {}
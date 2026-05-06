import re
import json
import streamlit.components.v1 as components
import pandas as pd
import streamlit as st
from threading import Lock

try:
    import pymupdf
except ImportError:
    import fitz as pymupdf

REQUESTED_ORDER = [
    "Mie Suit",
    "Mie Gacoan Level 0",
    "Mie Gacoan Level 1",
    "Mie Gacoan Level 2",
    "Mie Gacoan Level 3",
    "Mie Gacoan Level 4",
    "Mie Gacoan Level 6",
    "Mie Gacoan Level 8",
    "Mie Hompimpa Level 1",
    "Mie Hompimpa Level 2",
    "Mie Hompimpa Level 3",
    "Mie Hompimpa Level 4",
    "Mie Hompimpa Level 6",
    "Mie Hompimpa Level 8",
    "Udang Keju",
    "Udang Rambutan",
    "Siomay",
    "Lumpia Udang",
    "Pangsit Goreng",
    "Air Mineral",
    "Lemon Tea Hot",
    "Lemon Tea Ice",
    "Total Lemon Tea",
    "Orange Hot",
    "Orange Ice",
    "Total Orange",
    "Teh Tarik Hot",
    "Teh Tarik Ice",
    "Total Teh Tarik",
    "Milo Hot",
    "Milo Ice",
    "Total Milo",
    "Vanilla Latte Hot",
    "Vanilla Latte Ice",
    "Total Vanilla Latte",
    "Tea Hot",
    "Tea Ice",
    "Total Tea",
    "Thai Tea",
    "Thai Green Tea",
    "Es Gobak Sodor",
    "Es Teklek",
    "Es Petak Umpet",
    "Es Sluku Bathok",
    "Lemon Tea Ice NP",
    "Orange Ice NP",
    "Teh Tarik Ice NP",
    "Vanilla Latte Ice NP",
    "Lemon Tea Hot NP",
    "Orange Hot NP",
    "Teh Tarik Hot NP",
    "Vanilla Latte Hot NP",
    "Cup 16",
    "Packaging Mie",
    "Packaging Dimsum",
    "Total Packaging",
]

CATEGORY_GROUPS = {
    "Mie": [
        "Mie Suit",
        "Mie Gacoan Level 0",
        "Mie Gacoan Level 1",
        "Mie Gacoan Level 2",
        "Mie Gacoan Level 3",
        "Mie Gacoan Level 4",
        "Mie Gacoan Level 6",
        "Mie Gacoan Level 8",
        "Mie Hompimpa Level 1",
        "Mie Hompimpa Level 2",
        "Mie Hompimpa Level 3",
        "Mie Hompimpa Level 4",
        "Mie Hompimpa Level 6",
        "Mie Hompimpa Level 8",
    ],
    "Dimsum": [
        "Udang Keju",
        "Udang Rambutan",
        "Siomay",
        "Lumpia Udang",
        "Pangsit Goreng",
    ],
    "Beverages": [
        "Air Mineral",
        "Lemon Tea Hot",
        "Lemon Tea Ice",
        "Total Lemon Tea",
        "Orange Hot",
        "Orange Ice",
        "Total Orange",
        "Teh Tarik Hot",
        "Teh Tarik Ice",
        "Total Teh Tarik",
        "Milo Hot",
        "Milo Ice",
        "Total Milo",
        "Vanilla Latte Hot",
        "Vanilla Latte Ice",
        "Total Vanilla Latte",
        "Tea Hot",
        "Tea Ice",
        "Total Tea",
        "Es Gobak Sodor",
        "Es Teklek",
        "Es Petak Umpet",
        "Es Sluku Bathok",
        "Thai Tea",
        "Thai Green Tea",
        
    ],
    "NP": [
        "Lemon Tea Ice NP",
        "Orange Ice NP",
        "Teh Tarik Ice NP",
        "Vanilla Latte Ice NP",
        "Lemon Tea Hot NP",
        "Orange Hot NP",
        "Teh Tarik Hot NP",
        "Vanilla Latte Hot NP",
    ],
    "Packaging": [
        "Cup 16",
        "Packaging Mie",
        "Packaging Dimsum",
        "Total Packaging",
    ],
}

TOP_LEVEL_BLOCKS = {
    "BEVERAGES",
    "BEVERAGES ICE.",
    "BEVERAGES ISIAN",
    "DIMSUM",
    "ES BUAH",
    "MIE",
    "MIE ISIAN",
    "MIE.",
    "PACKAGING",
    "PAKET",
}

PAYMENT_METHODS = [
    "CASH",
    "GOFOOD INT",
    "GRABFOOD INT",
    "SHOPEEFOOD INT",
    "QRIS SHOPEE",
    "QRIS EDC",
    "QRIS BNI",
    "QRIS ESB ORDER",
]

MIE_USAGE_RULES = {
    "Mie Suit": {"cabe": 0},
    "Mie Gacoan Level 0": {"cabe": 0},
    "Mie Gacoan Level 1": {"cabe": 5},
    "Mie Gacoan Level 2": {"cabe": 10},
    "Mie Gacoan Level 3": {"cabe": 15},
    "Mie Gacoan Level 4": {"cabe": 20},
    "Mie Gacoan Level 6": {"cabe": 25},
    "Mie Gacoan Level 8": {"cabe": 30},
    "Mie Hompimpa Level 1": {"cabe": 5},
    "Mie Hompimpa Level 2": {"cabe": 10},
    "Mie Hompimpa Level 3": {"cabe": 15},
    "Mie Hompimpa Level 4": {"cabe": 20},
    "Mie Hompimpa Level 6": {"cabe": 25},
    "Mie Hompimpa Level 8": {"cabe": 30},
}

USAGE_RULES = {}

for menu_name, rule in MIE_USAGE_RULES.items():
    USAGE_RULES[menu_name] = [
        {"bahan": "Mie", "qty_per_porsi": 1, "satuan": "pcs"},
        {"bahan": "Cabe", "qty_per_porsi": rule["cabe"], "satuan": "gram"},
        {"bahan": "Adonan Pangsit", "qty_per_porsi": 30, "satuan": "gram"},
    ]

USAGE_RULES["Pangsit Goreng"] = [
    {"bahan": "Adonan Pangsit", "qty_per_porsi": 75, "satuan": "gram"},
]

def make_empty_result():
    return {
        name: {"menu": name, "dine_in": 0, "take_away": 0, "total": 0}
        for name in REQUESTED_ORDER
    }


def clean_text(value) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def clean_qty(text: str) -> int:
    text = text.strip()
    if not text:
        return 0
    return int(text.replace(".", "").replace(",", ""))

def make_empty_payments() -> dict:
    return {method: 0 for method in PAYMENT_METHODS}


def extract_payment_data(pdf_bytes: bytes) -> dict:
    payments = make_empty_payments()

    # Mode 1: coba baca dari tabel PDF
    try:
        table_rows = extract_pdf_table_rows(pdf_bytes)

        for row in table_rows:
            cleaned = [clean_text(cell) for cell in row if clean_text(cell)]
            if len(cleaned) < 2:
                continue

            method = cleaned[0].upper()
            amount_text = cleaned[1]

            if method in payments and is_number_like(amount_text):
                payments[method] = clean_qty(amount_text)

        if any(value > 0 for value in payments.values()):
            return payments

    except Exception:
        pass

    # Mode 2: fallback baca dari teks halaman PDF
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")

    for page in doc:
        text = page.get_text("text", sort=True)

        for raw_line in text.splitlines():
            line = clean_text(raw_line).upper()

            for method in PAYMENT_METHODS:
                pattern = rf"^{re.escape(method)}\s+([\d\.,]+)$"
                match = re.fullmatch(pattern, line)

                if match:
                    payments[method] = clean_qty(match.group(1))

    return payments


def payment_frame(payments: dict) -> pd.DataFrame:
    rows = []

    for method in PAYMENT_METHODS:
        rows.append({
            "Payment Method": method,
            "Payment Amount": payments.get(method, 0),
        })

    return pd.DataFrame(rows)


def is_number_like(text: str) -> bool:
    text = text.strip()
    return bool(re.fullmatch(r"\d[\d\.,]*", text))


def add_qty(results: dict, menu: str, channel: str, qty: int) -> None:
    if menu not in results:
        return
    results[menu][channel] += qty


def has_required_markers(lines: list[str]) -> bool:
    block_text = "\n".join(lines).upper()
    hits = 0

    if "DESCRIPTION | QTY | VALUE" in block_text:
        hits += 1
    if "BEVERAGES" in block_text:
        hits += 1
    if "MIE ISIAN" in block_text:
        hits += 1
    if "DIMSUM" in block_text:
        hits += 1

    return hits >= 4


def extract_pdf_table_rows(pdf_bytes: bytes) -> list[list[str]]:
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    all_rows = []

    for page in doc:
        try:
            tables = page.find_tables()
        except Exception:
            continue

        if not tables or not getattr(tables, "tables", None):
            continue

        for table in tables.tables:
            extracted = table.extract()
            for row in extracted:
                cleaned_row = [clean_text(cell) for cell in row]
                if any(cleaned_row):
                    all_rows.append(cleaned_row)

    return all_rows


def normalize_rows_from_tables(table_rows: list[list[str]]) -> list[str]:
    if not table_rows:
        raise ValueError("Tidak ada tabel PDF yang berhasil dideteksi.")

    text_rows = [" | ".join([c for c in row if c]).strip() for row in table_rows]

    start_index = None
    end_index = len(text_rows)

    for i, row_text in enumerate(text_rows):
        if "SALES BY MENU" in row_text.upper():
            start_index = i + 1
            break

    if start_index is None:
        for i, row_text in enumerate(text_rows):
            upper_row = row_text.upper()
            if "DESCRIPTION" in upper_row and "QTY" in upper_row and "VALUE" in upper_row:
                preview = "\n".join(text_rows[i:i + 120]).upper()
                if "BEVERAGES" in preview and "MIE ISIAN" in preview:
                    start_index = i
                    break

    if start_index is None:
        raise ValueError("Section Sales By Menu tidak ditemukan dari tabel PDF.")

    end_markers = ["NON SALES BY MENU", "CUSTOM MENU SALES", "SALES BY TABLE SECTION"]

    for i in range(start_index, len(text_rows)):
        upper_row = text_rows[i].upper()
        if any(marker in upper_row for marker in end_markers):
            end_index = i
            break

    section_rows = table_rows[start_index:end_index]
    if not section_rows:
        raise ValueError("Isi section Sales By Menu kosong pada tabel PDF.")

    normalized_lines = ["Description | Qty | Value"]

    for row in section_rows:
        cleaned = [clean_text(cell) for cell in row if clean_text(cell) != ""]
        if not cleaned:
            continue

        joined_upper = " ".join(cleaned).upper()
        if joined_upper == "SALES BY MENU":
            continue

        if len(cleaned) >= 3:
            description = cleaned[0]
            qty = cleaned[1]
            value = cleaned[2]

            if (
                description.upper() == "DESCRIPTION"
                and qty.upper() == "QTY"
                and value.upper() == "VALUE"
            ):
                continue

            normalized_lines.append(f"{description} | {qty} | {value}")
            continue

        if len(cleaned) == 2:
            if is_number_like(cleaned[1]):
                normalized_lines.append(f"{cleaned[0]} | {cleaned[1]} | ")
            else:
                normalized_lines.append(f"{cleaned[0]} |  | ")
            continue

        if len(cleaned) == 1:
            normalized_lines.append(f"{cleaned[0]} |  | ")
            continue

    return normalized_lines


def extract_pdf_block_lines(pdf_bytes: bytes) -> list[str]:
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    lines = []

    for page in doc:
        blocks = page.get_text("blocks", sort=True)
        for block in blocks:
            block_text = block[4]
            for raw_line in block_text.splitlines():
                cleaned = clean_text(raw_line)
                if cleaned:
                    lines.append(cleaned)

    if not lines:
        raise ValueError("PDF tidak mengandung teks yang bisa dibaca.")

    return lines


def extract_sales_by_menu_section(lines: list[str]) -> list[str]:
    start_index = None
    end_index = len(lines)

    for i, line in enumerate(lines):
        if line.upper() == "SALES BY MENU":
            start_index = i + 1
            break

    if start_index is None:
        raise ValueError("Section Sales By Menu tidak ditemukan.")

    end_markers = {
        "NON SALES BY MENU",
        "CUSTOM MENU SALES",
        "SALES BY TABLE SECTION",
    }

    for i in range(start_index, len(lines)):
        if lines[i].upper() in end_markers:
            end_index = i
            break

    section_lines = lines[start_index:end_index]
    if not section_lines:
        raise ValueError("Isi section Sales By Menu kosong.")

    return section_lines


def convert_section_lines_to_normalized_rows(section_lines: list[str]) -> list[str]:
    rows = ["Description | Qty | Value"]
    skip_tokens = {"DESCRIPTION", "QTY", "VALUE"}

    i = 0
    while i < len(section_lines):
        token = section_lines[i].strip()

        if not token:
            i += 1
            continue

        if token.upper() in skip_tokens:
            i += 1
            continue

        if i + 2 < len(section_lines):
            qty_candidate = section_lines[i + 1].strip()
            value_candidate = section_lines[i + 2].strip()

            if is_number_like(qty_candidate) and is_number_like(value_candidate):
                rows.append(f"{token} | {qty_candidate} | {value_candidate}")
                i += 3
                continue

        rows.append(f"{token} |  | ")
        i += 1

    return rows


def compute_totals(results: dict) -> None:
    for row in results.values():
        row["total"] = row["dine_in"] + row["take_away"]

    grouped_totals = [
        ("Total Lemon Tea", "Lemon Tea Hot", "Lemon Tea Ice"),
        ("Total Orange", "Orange Hot", "Orange Ice"),
        ("Total Teh Tarik", "Teh Tarik Hot", "Teh Tarik Ice"),
        ("Total Milo", "Milo Hot", "Milo Ice"),
        ("Total Vanilla Latte", "Vanilla Latte Hot", "Vanilla Latte Ice"),
        ("Total Tea", "Tea Hot", "Tea Ice"),
    ]

    for total_name, hot_name, ice_name in grouped_totals:
        results[total_name]["dine_in"] = (
            results[hot_name]["dine_in"] + results[ice_name]["dine_in"]
        )
        results[total_name]["take_away"] = (
            results[hot_name]["take_away"] + results[ice_name]["take_away"]
        )
        results[total_name]["total"] = (
            results[total_name]["dine_in"] + results[total_name]["take_away"]
        )

    results["Total Packaging"]["dine_in"] = (
        results["Cup 16"]["dine_in"]
        + results["Packaging Mie"]["dine_in"]
        + results["Packaging Dimsum"]["dine_in"]
    )
    results["Total Packaging"]["take_away"] = (
        results["Cup 16"]["take_away"]
        + results["Packaging Mie"]["take_away"]
        + results["Packaging Dimsum"]["take_away"]
    )
    results["Total Packaging"]["total"] = (
        results["Total Packaging"]["dine_in"]
        + results["Total Packaging"]["take_away"]
    )


def parse_target_data(lines: list[str]) -> dict:
    results = make_empty_result()

    current_block = None
    current_subblock = None

    for line in lines[1:]:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 3:
            continue

        description, qty_text, value_text = parts
        is_header = qty_text == "" and value_text == ""

        if is_header:
            if description in TOP_LEVEL_BLOCKS:
                current_block = description
                current_subblock = None
            else:
                current_subblock = description
            continue

        qty = clean_qty(qty_text)

        if description.startswith("Total -"):
            continue

        if current_block == "BEVERAGES":
            if current_subblock == "BEVERAGES DINE IN":
                channel = "dine_in"
            elif current_subblock == "BEVERAGES TAKE AWAY":
                channel = "take_away"
            else:
                channel = None

            direct_beverage_map = {
                "AIR MINERAL": "Air Mineral",
                "THAI TEA": "Thai Tea",
                "THAI GREEN TEA": "Thai Green Tea",
            }

            if channel and description in direct_beverage_map:
                add_qty(results, direct_beverage_map[description], channel, qty)

        elif current_block == "BEVERAGES ISIAN":
            beverage_isian_map = {
                "LEMON TEA DINE IN": (
                    "dine_in",
                    {"HOT": "Lemon Tea Hot", "ICED": "Lemon Tea Ice"},
                ),
                "LEMON TEA TA": (
                    "take_away",
                    {"HOT": "Lemon Tea Hot", "ICED": "Lemon Tea Ice"},
                ),
                "ORANGE DINE IN": (
                    "dine_in",
                    {"HOT": "Orange Hot", "ICED": "Orange Ice"},
                ),
                "ORANGE TA": (
                    "take_away",
                    {"HOT": "Orange Hot", "ICED": "Orange Ice"},
                ),
                "TEH TARIK DINE IN": (
                    "dine_in",
                    {"HOT": "Teh Tarik Hot", "ICED": "Teh Tarik Ice"},
                ),
                "TEH TARIK TA": (
                    "take_away",
                    {"HOT": "Teh Tarik Hot", "ICED": "Teh Tarik Ice"},
                ),
                "MILO DINE IN": (
                    "dine_in",
                    {"HOT": "Milo Hot", "ICED": "Milo Ice"},
                ),
                "MILO TA": (
                    "take_away",
                    {"HOT": "Milo Hot", "ICED": "Milo Ice"},
                ),
                "VANILLA LATTE DINE IN": (
                    "dine_in",
                    {"HOT": "Vanilla Latte Hot", "ICED": "Vanilla Latte Ice"},
                ),
                "VANILLA LATTE TA": (
                    "take_away",
                    {"HOT": "Vanilla Latte Hot", "ICED": "Vanilla Latte Ice"},
                ),
                "TEA DINE IN": (
                    "dine_in",
                    {"HOT": "Tea Hot", "ICED": "Tea Ice"},
                ),
                "TEA TA": (
                    "take_away",
                    {"HOT": "Tea Hot", "ICED": "Tea Ice"},
                ),
                "VANILLA LATTE NP DINE IN": (
                    "dine_in",
                    {"HOT": "Vanilla Latte Hot NP", "ICED": "Vanilla Latte Ice NP"},
                ),
                "VANILLA LATTE NP TA": (
                    "take_away",
                    {"HOT": "Vanilla Latte Hot NP", "ICED": "Vanilla Latte Ice NP"},
                ),
                "LEMON TEA NP DINE IN": (
                    "dine_in",
                    {"HOT": "Lemon Tea Hot NP", "ICED": "Lemon Tea Ice NP"},
                ),
                "LEMON TEA NP TA": (
                    "take_away",
                    {"HOT": "Lemon Tea Hot NP", "ICED": "Lemon Tea Ice NP"},
                ),
                "ORANGE NP DINE IN": (
                    "dine_in",
                    {"HOT": "Orange Hot NP", "ICED": "Orange Ice NP"},
                ),
                "ORANGE NP TA": (
                    "take_away",
                    {"HOT": "Orange Hot NP", "ICED": "Orange Ice NP"},
                ),
                "TEH TARIK NP DINE IN": (
                    "dine_in",
                    {"HOT": "Teh Tarik Hot NP", "ICED": "Teh Tarik Ice NP"},
                ),
                "TEH TARIK NP TA": (
                    "take_away",
                    {"HOT": "Teh Tarik Hot NP", "ICED": "Teh Tarik Ice NP"},
                ),
            }

            if current_subblock in beverage_isian_map:
                channel, item_map = beverage_isian_map[current_subblock]
                if description in item_map:
                    add_qty(results, item_map[description], channel, qty)

        elif current_block == "DIMSUM":
            if current_subblock == "DIMSUM DINE IN":
                channel = "dine_in"
            elif current_subblock == "DIMSUM TAKE AWAY":
                channel = "take_away"
            else:
                channel = None

            dimsum_map = {
                "UDANG KEJU": "Udang Keju",
                "UDANG RAMBUTAN": "Udang Rambutan",
                "SIOMAY": "Siomay",
                "LUMPIA UDANG": "Lumpia Udang",
                "PANGSIT GORENG": "Pangsit Goreng",
            }

            if channel and description in dimsum_map:
                add_qty(results, dimsum_map[description], channel, qty)

        elif current_block == "ES BUAH":
            if current_subblock == "ES BUAH DINE IN":
                channel = "dine_in"
            elif current_subblock == "ES BUAH TAKE AWAY":
                channel = "take_away"
            else:
                channel = None

            es_map = {
                "ES GOBAK SODOR": "Es Gobak Sodor",
                "ES TEKLEK": "Es Teklek",
                "ES PETAK UMPET": "Es Petak Umpet",
                "ES SLUKU BATHOK": "Es Sluku Bathok",
            }

            if channel and description in es_map:
                add_qty(results, es_map[description], channel, qty)

        elif current_block == "MIE":
            if current_subblock == "MIE DINE IN":
                channel = "dine_in"
            elif current_subblock == "MIE TAKE AWAY":
                channel = "take_away"
            else:
                channel = None

            if channel and description == "MIE SUIT":
                add_qty(results, "Mie Suit", channel, qty)

        elif current_block == "MIE ISIAN":
            mie_isian_map = {
                "MIE GACOAN DINE IN": (
                    "dine_in",
                    {
                        "LEVEL 0": "Mie Gacoan Level 0",
                        "LEVEL 1": "Mie Gacoan Level 1",
                        "LEVEL 2": "Mie Gacoan Level 2",
                        "LEVEL 3": "Mie Gacoan Level 3",
                        "LEVEL 4": "Mie Gacoan Level 4",
                        "LEVEL 6": "Mie Gacoan Level 6",
                        "LEVEL 8": "Mie Gacoan Level 8",
                    },
                ),
                "MIE GACOAN TAKE AWAY": (
                    "take_away",
                    {
                        "LEVEL 0": "Mie Gacoan Level 0",
                        "LEVEL 1": "Mie Gacoan Level 1",
                        "LEVEL 2": "Mie Gacoan Level 2",
                        "LEVEL 3": "Mie Gacoan Level 3",
                        "LEVEL 4": "Mie Gacoan Level 4",
                        "LEVEL 6": "Mie Gacoan Level 6",
                        "LEVEL 8": "Mie Gacoan Level 8",
                    },
                ),
                "MIE HOMPIMPA DINE IN": (
                    "dine_in",
                    {
                        "LEVEL 1": "Mie Hompimpa Level 1",
                        "LEVEL 2": "Mie Hompimpa Level 2",
                        "LEVEL 3": "Mie Hompimpa Level 3",
                        "LEVEL 4": "Mie Hompimpa Level 4",
                        "LEVEL 6": "Mie Hompimpa Level 6",
                        "LEVEL 8": "Mie Hompimpa Level 8",
                    },
                ),
                "MIE HOMPIMPA TAKE AWAY": (
                    "take_away",
                    {
                        "LEVEL 1": "Mie Hompimpa Level 1",
                        "LEVEL 2": "Mie Hompimpa Level 2",
                        "LEVEL 3": "Mie Hompimpa Level 3",
                        "LEVEL 4": "Mie Hompimpa Level 4",
                        "LEVEL 6": "Mie Hompimpa Level 6",
                        "LEVEL 8": "Mie Hompimpa Level 8",
                    },
                ),
            }

            if current_subblock in mie_isian_map:
                channel, item_map = mie_isian_map[current_subblock]
                if description in item_map:
                    add_qty(results, item_map[description], channel, qty)

        elif current_block == "PACKAGING":
            if current_subblock == "PACKAGING DINE IN":
                packaging_map = {
                    "16 OZ": "Cup 16",
                    "MIE": "Packaging Mie",
                    "DIMSUM": "Packaging Dimsum",
                }
                if description in packaging_map:
                    add_qty(results, packaging_map[description], "dine_in", qty)

    compute_totals(results)
    return results


def grouped_frames(results: dict) -> dict:
    frames = {}
    for category, items in CATEGORY_GROUPS.items():
        rows = []
        for name in items:
            item = results[name]
            menu_name = item["menu"].upper() if item["menu"].startswith("Total") else item["menu"]
            rows.append({
                "Menu": menu_name,
                "Dine In": item["dine_in"],
                "Take Away": item["take_away"],
                "Total": item["total"],
            })
        frames[category] = pd.DataFrame(rows)
    return frames

def render_copy_column_button(df: pd.DataFrame, column_name: str, label: str, key: str) -> None:
    if column_name not in df.columns:
        return

    copy_text = "\n".join(df[column_name].astype(str).tolist())
    js_text = json.dumps(copy_text)

    components.html(
        f"""
        <button
            id="copy-btn-{key}"
            style="
                padding: 6px 12px;
                border-radius: 8px;
                border: 1px solid #cccccc;
                background: #ffffff;
                cursor: pointer;
                font-size: 13px;
                margin-right: 6px;
                margin-bottom: 8px;
            "
        >
            {label}
        </button>

        <script>
        const btn = document.getElementById("copy-btn-{key}");
        btn.addEventListener("click", async () => {{
            await navigator.clipboard.writeText({js_text});
            btn.innerText = "Copied!";
            setTimeout(() => {{
                btn.innerText = {json.dumps(label)};
            }}, 1200);
        }});
        </script>
        """,
        height=45,
    )

def build_usage_summary_df(results: dict) -> pd.DataFrame:
    summary = {
        ("Mie", "pcs"): 0,
        ("Cabe", "gram"): 0,
        ("Kecap", "gram"): 0,
        ("Basic Mie", "gram"): 0,
        ("Minyak Mie", "gram"): 0,
        ("Ayam Cincang", "gram"): 0,
        ("Bawang Goreng", "gram"): 0,
        ("Daun Bawang", "gram"): 0,
        ("Kerupuk Pangsit", "pcs"): 0,
        ("Pangsit Goreng", "pcs"): 0,
        ("Adonan Pangsit", "gram"): 0,
        ("Siomay", "karton"): 0,
        ("Pentol", "karton"): 0,
        ("Kulit Pangsit", "ball"): 0,
        ("Surai Naga", "pack"): 0,
        ("Buah Apel", "gram"): 0,
        ("Buah Peer", "gram"): 0,
        ("Cincau", "gram"): 0,
        ("Nata de Coco", "gram"): 0,
        ("Susu UHT", "ML"): 0,
    }

    mie_rules = {
        "Mie Suit": {"cabe": 0, "kecap": 0, "basic_mie": 12},
        "Mie Gacoan Level 0": {"cabe": 0, "kecap": 12, "basic_mie": 12},
        "Mie Gacoan Level 1": {"cabe": 5, "kecap": 12, "basic_mie": 12},
        "Mie Gacoan Level 2": {"cabe": 10, "kecap": 12, "basic_mie": 12},
        "Mie Gacoan Level 3": {"cabe": 15, "kecap": 12, "basic_mie": 12},
        "Mie Gacoan Level 4": {"cabe": 20, "kecap": 12, "basic_mie": 12},
        "Mie Gacoan Level 6": {"cabe": 25, "kecap": 12, "basic_mie": 16},
        "Mie Gacoan Level 8": {"cabe": 30, "kecap": 12, "basic_mie": 16},
        "Mie Hompimpa Level 1": {"cabe": 5, "kecap": 0, "basic_mie": 12},
        "Mie Hompimpa Level 2": {"cabe": 10, "kecap": 0, "basic_mie": 12},
        "Mie Hompimpa Level 3": {"cabe": 15, "kecap": 0, "basic_mie": 12},
        "Mie Hompimpa Level 4": {"cabe": 20, "kecap": 0, "basic_mie": 12},
        "Mie Hompimpa Level 6": {"cabe": 25, "kecap": 0, "basic_mie": 16},
        "Mie Hompimpa Level 8": {"cabe": 30, "kecap": 0, "basic_mie": 16},
    }

    for menu_name, rule in mie_rules.items():
        terjual = results.get(menu_name, {}).get("total", 0)

        summary[("Mie", "pcs")] += terjual
        summary[("Cabe", "gram")] += terjual * rule["cabe"]
        summary[("Kecap", "gram")] += terjual * rule["kecap"]
        summary[("Basic Mie", "gram")] += terjual * rule["basic_mie"]
        summary[("Minyak Mie", "gram")] += terjual * 14
        summary[("Ayam Cincang", "gram")] += terjual * 8
        summary[("Bawang Goreng", "gram")] += terjual * 4
        summary[("Daun Bawang", "gram")] += terjual * 0.2
        summary[("Kerupuk Pangsit", "pcs")] += terjual * 8
        summary[("Pangsit Goreng", "pcs")] += terjual * 2
        summary[("Adonan Pangsit", "gram")] += terjual * 30
        

    pangsit_goreng_terjual = results.get("Pangsit Goreng", {}).get("total", 0)
    summary[("Pangsit Goreng", "pcs")] += pangsit_goreng_terjual * 5
    summary[("Adonan Pangsit", "gram")] += pangsit_goreng_terjual * 75
    total_pangsit_goreng_pcs = summary[("Pangsit Goreng", "pcs")]
    summary[("Kulit Pangsit", "ball")] += total_pangsit_goreng_pcs * 16 / 5000

    siomay_terjual = results.get("Siomay", {}).get("total", 0)
    summary[("Siomay", "karton")] += siomay_terjual / 144

    udang_keju_terjual = results.get("Udang Keju", {}).get("total", 0)
    udang_rambutan_terjual = results.get("Udang Rambutan", {}).get("total", 0)

    total_pentol_pcs = (udang_keju_terjual * 3) + (udang_rambutan_terjual * 3)
    summary[("Pentol", "karton")] += total_pentol_pcs / 480

    summary[("Surai Naga", "pack")] += udang_rambutan_terjual * 45 / 2000

    es_gobak_sodor_terjual = results.get("Es Gobak Sodor", {}).get("total", 0)
    es_teklek_terjual = results.get("Es Teklek", {}).get("total", 0)
    summary[("Buah Apel", "gram")] += es_gobak_sodor_terjual * 12
    summary[("Buah Peer", "gram")] += es_gobak_sodor_terjual * 27
    summary[("Cincau", "gram")] += (es_gobak_sodor_terjual + es_teklek_terjual) * 22
    summary[("Nata de Coco", "gram")] += (es_gobak_sodor_terjual + es_teklek_terjual) * 22

    es_sluku_bathok_terjual = results.get("Es Sluku Bathok", {}).get("total", 0)
    summary[(("Susu UHT", "ML"))] += es_sluku_bathok_terjual * 130

    rows = []
    for (bahan, satuan), qty in summary.items():
        if isinstance(qty, float) and not qty.is_integer():
            qty = round(qty, 4)
        else:
            qty = int(qty)

        rows.append({
            "Bahan": bahan,
            "Usage": qty,
            "Satuan": satuan,
        })

    return pd.DataFrame(rows)

def process_pdf(uploaded_file):
    pdf_bytes = uploaded_file.getvalue()
    payments = extract_payment_data(pdf_bytes)

    table_error = None
    try:
        table_rows = extract_pdf_table_rows(pdf_bytes)
        if table_rows:
            normalized_rows = normalize_rows_from_tables(table_rows)
            if has_required_markers(normalized_rows):
                results = parse_target_data(normalized_rows)
                return results, payments, "table"
    except Exception as e:
        table_error = str(e)

    try:
        block_lines = extract_pdf_block_lines(pdf_bytes)
        section_lines = extract_sales_by_menu_section(block_lines)
        normalized_rows = convert_section_lines_to_normalized_rows(section_lines)

        if not has_required_markers(normalized_rows):
            if table_error:
                raise ValueError(
                    f"Gagal membaca PDF dengan mode tabel ({table_error}) dan mode blok teks tidak menemukan marker yang cukup."
                )
            raise ValueError("Mode blok teks tidak menemukan marker yang cukup.")

        results = parse_target_data(normalized_rows)
        return results, payments, "text"
    except Exception as e:
        if table_error:
            raise ValueError(f"Mode tabel gagal: {table_error} | Mode blok teks gagal: {e}") from e
        raise

class VisitCounter:
    def __init__(self):
        self.count = 0
        self.lock = Lock()

    def increment(self):
        with self.lock:
            self.count += 1
            return self.count

    def value(self):
        with self.lock:
            return self.count


@st.cache_resource
def get_visit_counter():
    return VisitCounter()


def register_visit_once_per_session():
    counter = get_visit_counter()

    if "visit_counted" not in st.session_state:
        st.session_state.visit_counted = True
        return counter.increment()

    return counter.value()

st.title("PROMIX PDF Reader")
st.caption("Upload 1 file PDF laporan PROMIX untuk melihat hasil per kategori dan menyiapkan data copy-paste.")

visit_count = register_visit_once_per_session()
st.caption(f"👀 Jumlah kunjungan sesi: {visit_count}")

uploaded_file = st.file_uploader(
    "Upload file PDF PROMIX",
    type=["pdf"]
)

if uploaded_file is not None:
    try:
        results, payments, mode = process_pdf(uploaded_file)

        st.success(f'Laporan Promix "{uploaded_file.name}" berhasil diproses')

        st.divider()
        st.subheader("Sales Payment Recapitulation/COPAS UNTUK LPH AR")

        payment_df = payment_frame(payments)
        copy_method_col, copy_amount_col = st.columns([2.2, 1.6])
        with copy_method_col:
            st.empty()

        with copy_amount_col:
            render_copy_column_button(
                payment_df,
                "Payment Amount",
                "Copy Payment Amount",
                "payment-amount",
            )

        st.dataframe(payment_df, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Preview Hasil per Kategori")

        frames = grouped_frames(results)

        beverage_totals = {
        "Air Mineral",
        "TOTAL LEMON TEA",
        "TOTAL ORANGE",
        "TOTAL TEH TARIK",
        "TOTAL MILO",
        "TOTAL VANILLA LATTE",
        "TOTAL TEA",
        "Es Gobak Sodor",
        "Es Teklek",
        "Es Petak Umpet",
        "Es Sluku Bathok",
        "Thai Tea",
        "Thai Green Tea",
        }

        for category, df in frames.items():
            with st.expander(category, expanded=(category == "Mie")):
                if category == "Beverages":
                    hide_beverage_totals = st.checkbox(
                        "Copy Beverages hanya Item Hot dan Ice",
                        value=True,
                        key="hide_beverage_totals",
                        )

                    show_only_beverage_totals = st.checkbox(
                        "Copy Beverages tidak ada Item hot dan Ice",
                        value=False,
                        key="show_only_beverage_totals",
                        )

                    beverage_df = df.copy()

                    if show_only_beverage_totals:
                        df = beverage_df[
                        beverage_df["Menu"].isin(beverage_totals)
                        ]
                    elif hide_beverage_totals:
                        df = beverage_df[
                        ~beverage_df["Menu"].str.startswith("TOTAL", na=False)
                ]
                        
                copy_menu_col, copy_dine_col, copy_ta_col, copy_total_col = st.columns(
                    [2.2, 1.6, 1.6, 1.6]
                )

                with copy_menu_col:
                    st.empty()

                with copy_dine_col:
                    render_copy_column_button(
                        df,
                        "Dine In",
                        f"Copy {category} Dine In",
                        f"{category.lower().replace(' ', '-')}-dine-in",
                    )

                with copy_ta_col:
                    render_copy_column_button(
                        df,
                        "Take Away",
                        f"Copy {category} Take Away",
                        f"{category.lower().replace(' ', '-')}-take-away",
                    )

                with copy_total_col:
                    render_copy_column_button(
                        df,
                        "Total",
                        f"Copy {category} Total",
                        f"{category.lower().replace(' ', '-')}-total",
                    )

                st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Usage Bahan / Gramasi / COST CONTROLLING")
        usage_df = build_usage_summary_df(results)
        st.dataframe(usage_df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Terjadi error: {e}")
        st.exception(e)
else:
    st.info("Silakan upload 1 file PDF terlebih dahulu.")

st.markdown("""
<style>
.dev-footer {
    position: fixed;
    left: 600px;
    bottom: 12px;
    z-index: 9999;
    background: rgba(255, 255, 255, 0.92);
    padding: 8px 15px;
    border-radius: 12px;
    font-size: 13px;
    color: #2d3fa6;
    box-shadow: 0 2px 8px rgba(0,0,0,0.12);
}
</style>

<div class="dev-footer">
    Developed by Eldwin Manalu
</div>
""", unsafe_allow_html=True)

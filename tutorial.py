import streamlit as st

st.title("Tutorial Penggunaan PROMIX PDF Reader")

st.markdown("""
### 1. Upload File PDF PROMIX
Klik tombol **Upload file PDF PROMIX**, lalu pilih laporan PROMIX dalam format PDF.

### 2. Tunggu Proses Parsing
Jika berhasil, sistem akan menampilkan pesan bahwa laporan berhasil diproses.

### 3. Cek Hasil per Kategori
Hasil parsing akan ditampilkan berdasarkan kategori:
- Mie
- Dimsum
- Beverages
- NP
- Packaging

### 4. Gunakan Tombol Copy
Klik tombol copy pada kolom yang dibutuhkan, misalnya:
- Copy Mie Dine In
- Copy Mie Take Away
- Copy Mie Total

Data akan tersalin secara vertikal dan siap ditempel ke spreadsheet.

### 5. Cek Usage Bahan / Gramasi
Bagian ini menampilkan estimasi pemakaian bahan berdasarkan hasil penjualan PROMIX.
""")
"""Fungsi-fungsi bantu."""


def format_rupiah(nilai: float) -> str:
    """Mengubah angka menjadi format Rupiah, contoh: 15000 -> 'Rp 15.000'."""
    return "Rp " + f"{int(round(nilai)):,}".replace(",", ".")


def input_angka(pesan: str, minimal: int = 0) -> int:
    """Meminta input bilangan bulat dari pengguna sampai valid."""
    while True:
        teks = input(pesan).strip()
        try:
            nilai = int(teks)
            if nilai < minimal:
                print(f"  ! Nilai minimal {minimal}.")
                continue
            return nilai
        except ValueError:
            print("  ! Masukkan angka yang valid.")

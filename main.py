"""
Sistem Kasir Toko - Aplikasi Command Line
Jalankan dengan: python main.py
"""

from datetime import date

from kasir.inventori import Inventori
from kasir.models import Produk
from kasir.transaksi import Kasir, Keranjang, buat_struk
from kasir.utils import format_rupiah, input_angka


def tampilkan_produk(daftar):
    if not daftar:
        print("  (Tidak ada produk)")
        return
    print(f"\n  {'KODE':<8}{'NAMA PRODUK':<24}{'HARGA':>14}{'STOK':>7}")
    print("  " + "-" * 53)
    for p in daftar:
        print(f"  {p.kode:<8}{p.nama[:23]:<24}{format_rupiah(p.harga):>14}{p.stok:>7}")


# ================= MENU TRANSAKSI =================
def menu_transaksi(inventori: Inventori, kasir: Kasir):
    keranjang = Keranjang(inventori)
    while True:
        print("\n--- TRANSAKSI BARU ---")
        if keranjang.kosong:
            print("  Keranjang kosong.")
        else:
            for item in keranjang.items.values():
                print(f"  {item.produk.kode:<6} {item.produk.nama:<22} "
                      f"x{item.jumlah:<4} {format_rupiah(item.subtotal):>14}")
            print(f"  TOTAL: {format_rupiah(keranjang.total)}")
        print("\n  1. Tambah barang\n  2. Hapus barang\n  3. Bayar\n  0. Batal & kembali")
        pilihan = input("Pilih: ").strip()

        try:
            if pilihan == "1":
                tampilkan_produk(inventori.semua())
                kode = input("Kode produk: ").strip()
                jumlah = input_angka("Jumlah: ", minimal=1)
                item = keranjang.tambah(kode, jumlah)
                print(f"  ✓ {item.produk.nama} ditambahkan.")
            elif pilihan == "2":
                keranjang.hapus(input("Kode produk yang dihapus: ").strip())
                print("  ✓ Barang dihapus dari keranjang.")
            elif pilihan == "3":
                if keranjang.kosong:
                    print("  ! Keranjang masih kosong.")
                    continue
                total = keranjang.total
                diskon = kasir.hitung_diskon(total)
                if diskon:
                    print(f"  Diskon {kasir.persen_diskon}%: -{format_rupiah(diskon)}")
                print(f"  Total yang harus dibayar: {format_rupiah(total - diskon)}")
                bayar = input_angka("Uang tunai: ")
                transaksi = kasir.checkout(keranjang, bayar)
                print("\n" + buat_struk(transaksi))
                return
            elif pilihan == "0":
                return
            else:
                print("  ! Pilihan tidak valid.")
        except (KeyError, ValueError) as e:
            print(f"  ! {e.args[0]}")


# ================= MENU PRODUK =================
def menu_produk(inventori: Inventori):
    while True:
        print("\n--- KELOLA PRODUK ---")
        print("  1. Lihat semua produk\n  2. Cari produk\n  3. Tambah produk")
        print("  4. Ubah produk\n  5. Hapus produk\n  0. Kembali")
        pilihan = input("Pilih: ").strip()

        try:
            if pilihan == "1":
                tampilkan_produk(inventori.semua())
            elif pilihan == "2":
                tampilkan_produk(inventori.cari_nama(input("Kata kunci: ")))
            elif pilihan == "3":
                kode = input("Kode: ").strip()
                nama = input("Nama: ").strip()
                if not kode or not nama:
                    print("  ! Kode dan nama wajib diisi.")
                    continue
                harga = input_angka("Harga: ")
                stok = input_angka("Stok: ")
                inventori.tambah(Produk(kode, nama, harga, stok))
                print("  ✓ Produk ditambahkan.")
            elif pilihan == "4":
                kode = input("Kode produk: ").strip()
                produk = inventori.cari(kode)
                if produk is None:
                    print("  ! Produk tidak ditemukan.")
                    continue
                print("  (Kosongkan jika tidak ingin mengubah)")
                nama = input(f"Nama [{produk.nama}]: ").strip() or None
                harga = input(f"Harga [{produk.harga}]: ").strip()
                stok = input(f"Stok [{produk.stok}]: ").strip()
                inventori.ubah(kode, nama,
                               int(harga) if harga else None,
                               int(stok) if stok else None)
                print("  ✓ Produk diperbarui.")
            elif pilihan == "5":
                kode = input("Kode produk: ").strip()
                if input(f"Yakin hapus {kode}? (y/n): ").lower() == "y":
                    inventori.hapus(kode)
                    print("  ✓ Produk dihapus.")
            elif pilihan == "0":
                return
            else:
                print("  ! Pilihan tidak valid.")
        except (KeyError, ValueError) as e:
            print(f"  ! {e.args[0] if e.args else e}")


# ================= MENU LAPORAN =================
def menu_laporan(kasir: Kasir):
    tanggal = input(f"Tanggal (YYYY-MM-DD) [{date.today()}]: ").strip() or str(date.today())
    laporan = kasir.laporan_harian(tanggal)
    print(f"\n--- LAPORAN PENJUALAN {laporan['tanggal']} ---")
    print(f"  Jumlah transaksi : {laporan['jumlah_transaksi']}")
    print(f"  Total pendapatan : {format_rupiah(laporan['pendapatan'])}")
    if laporan["produk_terlaris"]:
        print("  Produk terlaris  :")
        for i, (nama, jumlah) in enumerate(laporan["produk_terlaris"], 1):
            print(f"    {i}. {nama} ({jumlah} terjual)")


def main():
    inventori = Inventori("data/produk.json")
    kasir = Kasir(inventori, "data/transaksi.json")

    while True:
        print("\n" + "=" * 40)
        print("      SISTEM KASIR TOKO MAJU JAYA")
        print("=" * 40)
        print("  1. Transaksi baru\n  2. Kelola produk\n  3. Laporan penjualan\n  0. Keluar")
        pilihan = input("Pilih menu: ").strip()

        if pilihan == "1":
            menu_transaksi(inventori, kasir)
        elif pilihan == "2":
            menu_produk(inventori)
        elif pilihan == "3":
            menu_laporan(kasir)
        elif pilihan == "0":
            print("Sampai jumpa! 👋")
            break
        else:
            print("  ! Pilihan tidak valid.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram dihentikan.")

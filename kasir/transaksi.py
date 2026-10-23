"""Logika keranjang belanja, pembayaran, dan riwayat transaksi."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .inventori import Inventori
from .models import ItemKeranjang
from .utils import format_rupiah


class Keranjang:
    def __init__(self, inventori: Inventori):
        self.inventori = inventori
        self.items: Dict[str, ItemKeranjang] = {}

    def tambah(self, kode: str, jumlah: int) -> ItemKeranjang:
        if jumlah <= 0:
            raise ValueError("Jumlah harus lebih dari 0.")
        produk = self.inventori.cari(kode)
        if produk is None:
            raise KeyError(f"Produk '{kode}' tidak ditemukan.")
        sudah = self.items[produk.kode].jumlah if produk.kode in self.items else 0
        if sudah + jumlah > produk.stok:
            raise ValueError(
                f"Stok {produk.nama} tidak cukup (tersisa {produk.stok - sudah}).")
        if produk.kode in self.items:
            self.items[produk.kode].jumlah += jumlah
        else:
            self.items[produk.kode] = ItemKeranjang(produk, jumlah)
        return self.items[produk.kode]

    def hapus(self, kode: str) -> None:
        if self.items.pop(kode.upper(), None) is None:
            raise KeyError(f"Produk '{kode}' tidak ada di keranjang.")

    def kosongkan(self) -> None:
        self.items.clear()

    @property
    def kosong(self) -> bool:
        return not self.items

    @property
    def total(self) -> int:
        return sum(item.subtotal for item in self.items.values())


class Kasir:
    """Mengatur proses checkout dan menyimpan riwayat transaksi."""

    def __init__(self, inventori: Inventori,
                 path_riwayat: str = "data/transaksi.json",
                 diskon_minimal: int = 100_000, persen_diskon: int = 5):
        self.inventori = inventori
        self.path_riwayat = Path(path_riwayat)
        self.diskon_minimal = diskon_minimal
        self.persen_diskon = persen_diskon

    def hitung_diskon(self, total: int) -> int:
        """Diskon otomatis jika total belanja mencapai batas minimal."""
        if total >= self.diskon_minimal:
            return total * self.persen_diskon // 100
        return 0

    def checkout(self, keranjang: Keranjang, bayar: int) -> dict:
        if keranjang.kosong:
            raise ValueError("Keranjang masih kosong.")
        total = keranjang.total
        diskon = self.hitung_diskon(total)
        total_akhir = total - diskon
        if bayar < total_akhir:
            raise ValueError(
                f"Uang kurang {format_rupiah(total_akhir - bayar)}.")

        for item in keranjang.items.values():
            self.inventori.kurangi_stok(item.produk.kode, item.jumlah)
        self.inventori.simpan()

        waktu = datetime.now()
        transaksi = {
            "id": waktu.strftime("TRX%Y%m%d%H%M%S%f")[:-3],
            "waktu": waktu.strftime("%Y-%m-%d %H:%M:%S"),
            "items": [
                {"kode": i.produk.kode, "nama": i.produk.nama,
                 "harga": i.produk.harga, "jumlah": i.jumlah,
                 "subtotal": i.subtotal}
                for i in keranjang.items.values()
            ],
            "total": total,
            "diskon": diskon,
            "total_akhir": total_akhir,
            "bayar": bayar,
            "kembalian": bayar - total_akhir,
        }
        self._simpan_riwayat(transaksi)
        keranjang.kosongkan()
        return transaksi

    # ---------- Riwayat ----------
    def riwayat(self) -> List[dict]:
        if not self.path_riwayat.exists():
            return []
        with open(self.path_riwayat, "r", encoding="utf-8") as f:
            return json.load(f)

    def cari_transaksi(self, id_transaksi: str) -> Optional[dict]:
        for t in self.riwayat():
            if t["id"] == id_transaksi:
                return t
        return None

    def _simpan_riwayat(self, transaksi: dict) -> None:
        data = self.riwayat()
        data.append(transaksi)
        self.path_riwayat.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path_riwayat, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def laporan_harian(self, tanggal: str) -> dict:
        """Ringkasan penjualan untuk tanggal tertentu (format YYYY-MM-DD)."""
        transaksi = [t for t in self.riwayat() if t["waktu"].startswith(tanggal)]
        terjual: Dict[str, int] = {}
        for t in transaksi:
            for item in t["items"]:
                terjual[item["nama"]] = terjual.get(item["nama"], 0) + item["jumlah"]
        return {
            "tanggal": tanggal,
            "jumlah_transaksi": len(transaksi),
            "pendapatan": sum(t["total_akhir"] for t in transaksi),
            "produk_terlaris": sorted(terjual.items(),
                                      key=lambda x: x[1], reverse=True)[:5],
        }


def buat_struk(transaksi: dict, nama_toko: str = "TOKO MAJU JAYA") -> str:
    """Menghasilkan teks struk belanja."""
    lebar = 40
    garis = "-" * lebar

    def kiri_kanan(kiri: str, kanan: str) -> str:
        return kiri + kanan.rjust(lebar - len(kiri))

    baris = [
        "=" * lebar,
        nama_toko.center(lebar),
        "=" * lebar,
        f"No   : {transaksi['id']}",
        f"Waktu: {transaksi['waktu']}",
        garis,
    ]
    for item in transaksi["items"]:
        baris.append(item["nama"][:lebar])
        baris.append(kiri_kanan(
            f"  {item['jumlah']} x {format_rupiah(item['harga'])}",
            format_rupiah(item["subtotal"])))
    baris.append(garis)
    baris.append(kiri_kanan("Total", format_rupiah(transaksi["total"])))
    if transaksi["diskon"]:
        baris.append(kiri_kanan("Diskon", "-" + format_rupiah(transaksi["diskon"])))
        baris.append(kiri_kanan("Total Bayar", format_rupiah(transaksi["total_akhir"])))
    baris.append(kiri_kanan("Tunai", format_rupiah(transaksi["bayar"])))
    baris.append(kiri_kanan("Kembali", format_rupiah(transaksi["kembalian"])))
    baris.append("=" * lebar)
    baris.append("Terima kasih atas kunjungan Anda!".center(lebar))
    baris.append("=" * lebar)
    return "\n".join(baris)

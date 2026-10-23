"""Unit test untuk Sistem Kasir. Jalankan: python -m pytest"""

import pytest

from kasir.inventori import Inventori
from kasir.models import Produk
from kasir.transaksi import Kasir, Keranjang, buat_struk
from kasir.utils import format_rupiah


@pytest.fixture
def inventori(tmp_path):
    inv = Inventori(str(tmp_path / "produk.json"))
    inv.tambah(Produk("A1", "Teh Botol", 5000, 10))
    inv.tambah(Produk("B2", "Roti Tawar", 15000, 5))
    return inv


@pytest.fixture
def kasir(inventori, tmp_path):
    return Kasir(inventori, str(tmp_path / "transaksi.json"))


def test_format_rupiah():
    assert format_rupiah(1500000) == "Rp 1.500.000"
    assert format_rupiah(0) == "Rp 0"


def test_tambah_produk_duplikat(inventori):
    with pytest.raises(ValueError):
        inventori.tambah(Produk("a1", "Duplikat", 1000, 1))


def test_data_tersimpan_ke_file(inventori):
    inv_baru = Inventori(str(inventori.path_file))
    assert inv_baru.cari("A1").nama == "Teh Botol"


def test_ubah_dan_hapus_produk(inventori):
    inventori.ubah("A1", harga=6000)
    assert inventori.cari("A1").harga == 6000
    inventori.hapus("A1")
    assert inventori.cari("A1") is None


def test_keranjang_total(inventori):
    k = Keranjang(inventori)
    k.tambah("A1", 2)
    k.tambah("B2", 1)
    k.tambah("A1", 1)
    assert k.items["A1"].jumlah == 3
    assert k.total == 3 * 5000 + 15000


def test_keranjang_stok_tidak_cukup(inventori):
    k = Keranjang(inventori)
    k.tambah("B2", 4)
    with pytest.raises(ValueError):
        k.tambah("B2", 2)


def test_checkout_mengurangi_stok(inventori, kasir):
    k = Keranjang(inventori)
    k.tambah("A1", 3)
    trx = kasir.checkout(k, 20000)
    assert trx["kembalian"] == 5000
    assert inventori.cari("A1").stok == 7
    assert k.kosong
    assert len(kasir.riwayat()) == 1


def test_checkout_uang_kurang(inventori, kasir):
    k = Keranjang(inventori)
    k.tambah("B2", 1)
    with pytest.raises(ValueError):
        kasir.checkout(k, 10000)
    assert inventori.cari("B2").stok == 5


def test_diskon(inventori, kasir):
    k = Keranjang(inventori)
    k.tambah("B2", 5)
    k.tambah("A1", 10)  # total 125.000 -> diskon 5%
    trx = kasir.checkout(k, 200000)
    assert trx["diskon"] == 6250
    assert trx["total_akhir"] == 118750


def test_laporan_dan_struk(inventori, kasir):
    k = Keranjang(inventori)
    k.tambah("A1", 2)
    trx = kasir.checkout(k, 10000)
    laporan = kasir.laporan_harian(trx["waktu"][:10])
    assert laporan["jumlah_transaksi"] == 1
    assert laporan["pendapatan"] == 10000
    assert "Teh Botol" in buat_struk(trx)

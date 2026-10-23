"""Test untuk versi web (Flask). Jalankan: python -m pytest"""

import json

import pytest

from app import create_app


@pytest.fixture
def client(tmp_path):
    path_produk = tmp_path / "produk.json"
    path_produk.write_text(json.dumps([
        {"kode": "A1", "nama": "Teh Botol", "harga": 5000, "stok": 10},
        {"kode": "B2", "nama": "Roti Tawar", "harga": 15000, "stok": 2},
    ]))
    app = create_app(str(path_produk), str(tmp_path / "transaksi.json"))
    app.config["TESTING"] = True
    return app.test_client()


def test_halaman_utama(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "Teh Botol" in res.get_data(as_text=True)


def test_semua_halaman_bisa_dibuka(client):
    for url in ["/produk", "/produk/tambah", "/produk/ubah/A1", "/riwayat", "/laporan"]:
        assert client.get(url).status_code == 200, url


def test_alur_transaksi_lengkap(client):
    client.post("/keranjang/tambah", data={"kode": "A1", "jumlah": 3})
    halaman = client.get("/").get_data(as_text=True)
    assert "Rp 15.000" in halaman

    res = client.post("/bayar", data={"bayar": "20000"})
    assert res.status_code == 302 and "/struk/" in res.location

    struk = client.get(res.location).get_data(as_text=True)
    assert "Rp 5.000" in struk  # kembalian
    assert "Sisa 7" in client.get("/").get_data(as_text=True)


def test_stok_tidak_cukup(client):
    res = client.post("/keranjang/tambah", data={"kode": "B2", "jumlah": 5},
                      follow_redirects=True)
    assert "tidak cukup" in res.get_data(as_text=True)


def test_uang_kurang(client):
    client.post("/keranjang/tambah", data={"kode": "B2"})
    res = client.post("/bayar", data={"bayar": "1000"}, follow_redirects=True)
    assert "Uang kurang" in res.get_data(as_text=True)


def test_kelola_produk(client):
    client.post("/produk/tambah", data={"kode": "c3", "nama": "Kecap", "harga": 9000, "stok": 4})
    assert "Kecap" in client.get("/produk").get_data(as_text=True)
    client.post("/produk/ubah/C3", data={"nama": "Kecap Manis", "harga": 9500, "stok": 4})
    assert "Kecap Manis" in client.get("/produk").get_data(as_text=True)
    client.post("/produk/hapus/C3")
    assert "Kecap" not in client.get("/produk").get_data(as_text=True)

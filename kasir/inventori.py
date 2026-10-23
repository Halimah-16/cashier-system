"""Pengelolaan data produk (inventori) dengan penyimpanan file JSON."""

import json
from pathlib import Path
from typing import Dict, List, Optional

from .models import Produk


class Inventori:
    def __init__(self, path_file: str = "data/produk.json"):
        self.path_file = Path(path_file)
        self.produk: Dict[str, Produk] = {}
        self.muat()

    # ---------- Penyimpanan ----------
    def muat(self) -> None:
        if not self.path_file.exists():
            self.produk = {}
            return
        with open(self.path_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.produk = {p["kode"]: Produk.from_dict(p) for p in data}

    def simpan(self) -> None:
        self.path_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path_file, "w", encoding="utf-8") as f:
            json.dump([p.to_dict() for p in self.produk.values()],
                      f, indent=2, ensure_ascii=False)

    # ---------- CRUD ----------
    def tambah(self, produk: Produk) -> None:
        kode = produk.kode.upper()
        if kode in self.produk:
            raise ValueError(f"Produk dengan kode '{kode}' sudah ada.")
        if produk.harga < 0 or produk.stok < 0:
            raise ValueError("Harga dan stok tidak boleh negatif.")
        produk.kode = kode
        self.produk[kode] = produk
        self.simpan()

    def cari(self, kode: str) -> Optional[Produk]:
        return self.produk.get(kode.upper())

    def cari_nama(self, kata_kunci: str) -> List[Produk]:
        kata_kunci = kata_kunci.lower()
        return [p for p in self.produk.values() if kata_kunci in p.nama.lower()]

    def ubah(self, kode: str, nama: Optional[str] = None,
             harga: Optional[int] = None, stok: Optional[int] = None) -> Produk:
        produk = self.cari(kode)
        if produk is None:
            raise KeyError(f"Produk '{kode}' tidak ditemukan.")
        if nama:
            produk.nama = nama
        if harga is not None:
            if harga < 0:
                raise ValueError("Harga tidak boleh negatif.")
            produk.harga = harga
        if stok is not None:
            if stok < 0:
                raise ValueError("Stok tidak boleh negatif.")
            produk.stok = stok
        self.simpan()
        return produk

    def hapus(self, kode: str) -> None:
        if self.produk.pop(kode.upper(), None) is None:
            raise KeyError(f"Produk '{kode}' tidak ditemukan.")
        self.simpan()

    def kurangi_stok(self, kode: str, jumlah: int) -> None:
        produk = self.cari(kode)
        if produk is None:
            raise KeyError(f"Produk '{kode}' tidak ditemukan.")
        if jumlah > produk.stok:
            raise ValueError(f"Stok {produk.nama} tidak cukup.")
        produk.stok -= jumlah

    def semua(self) -> List[Produk]:
        return sorted(self.produk.values(), key=lambda p: p.kode)

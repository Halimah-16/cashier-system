"""Model data untuk produk dan item keranjang."""

from dataclasses import dataclass, asdict


@dataclass
class Produk:
    kode: str
    nama: str
    harga: int
    stok: int

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Produk":
        return cls(
            kode=str(data["kode"]),
            nama=str(data["nama"]),
            harga=int(data["harga"]),
            stok=int(data["stok"]),
        )


@dataclass
class ItemKeranjang:
    produk: Produk
    jumlah: int

    @property
    def subtotal(self) -> int:
        return self.produk.harga * self.jumlah

"""
Sistem Kasir Toko - Versi Web (Flask)
Jalankan dengan: python app.py lalu buka http://127.0.0.1:5000
"""

import os
from datetime import date

from flask import Flask, flash, redirect, render_template, request, session, url_for

from kasir.inventori import Inventori
from kasir.models import Produk
from kasir.transaksi import Kasir, Keranjang
from kasir.utils import format_rupiah


def create_app(path_produk: str = "data/produk.json",
               path_transaksi: str = "data/transaksi.json") -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "ganti-dengan-kunci-rahasia")
    app.jinja_env.filters["rupiah"] = format_rupiah

    inventori = Inventori(path_produk)
    kasir = Kasir(inventori, path_transaksi)

    # ---------- Helper keranjang (disimpan di session) ----------
    def ambil_keranjang() -> Keranjang:
        """Membangun objek Keranjang dari data session {kode: jumlah}."""
        keranjang = Keranjang(inventori)
        for kode, jumlah in session.get("keranjang", {}).items():
            try:
                keranjang.tambah(kode, jumlah)
            except (KeyError, ValueError):
                pass  # produk dihapus atau stok berubah, abaikan
        return keranjang

    def simpan_keranjang(keranjang: Keranjang) -> None:
        session["keranjang"] = {k: i.jumlah for k, i in keranjang.items.items()}

    # ================= KASIR =================
    @app.route("/")
    def index():
        q = request.args.get("q", "").strip()
        produk = inventori.cari_nama(q) if q else inventori.semua()
        keranjang = ambil_keranjang()
        diskon = kasir.hitung_diskon(keranjang.total)
        return render_template(
            "kasir.html", produk=produk, q=q, keranjang=keranjang,
            diskon=diskon, total_akhir=keranjang.total - diskon, kasir=kasir)

    @app.post("/keranjang/tambah")
    def keranjang_tambah():
        keranjang = ambil_keranjang()
        try:
            jumlah = int(request.form.get("jumlah", 1))
            keranjang.tambah(request.form["kode"], jumlah)
            simpan_keranjang(keranjang)
        except (KeyError, ValueError) as e:
            flash(str(e.args[0]) if e.args else "Input tidak valid.", "error")
        return redirect(url_for("index", q=request.form.get("q") or None))

    @app.post("/keranjang/kurang/<kode>")
    def keranjang_kurang(kode):
        keranjang = ambil_keranjang()
        item = keranjang.items.get(kode)
        if item:
            if item.jumlah > 1:
                item.jumlah -= 1
            else:
                keranjang.hapus(kode)
            simpan_keranjang(keranjang)
        return redirect(url_for("index"))

    @app.post("/keranjang/hapus/<kode>")
    def keranjang_hapus(kode):
        keranjang = ambil_keranjang()
        if kode in keranjang.items:
            keranjang.hapus(kode)
            simpan_keranjang(keranjang)
        return redirect(url_for("index"))

    @app.post("/keranjang/kosongkan")
    def keranjang_kosongkan():
        session.pop("keranjang", None)
        return redirect(url_for("index"))

    @app.post("/bayar")
    def bayar():
        keranjang = ambil_keranjang()
        try:
            uang = int(request.form.get("bayar", "0").replace(".", "") or 0)
            transaksi = kasir.checkout(keranjang, uang)
        except ValueError as e:
            flash(str(e.args[0]) if e.args else "Pembayaran gagal.", "error")
            return redirect(url_for("index"))
        session.pop("keranjang", None)
        return redirect(url_for("struk", id_transaksi=transaksi["id"]))

    @app.route("/struk/<id_transaksi>")
    def struk(id_transaksi):
        transaksi = kasir.cari_transaksi(id_transaksi)
        if transaksi is None:
            flash("Transaksi tidak ditemukan.", "error")
            return redirect(url_for("riwayat"))
        return render_template("struk.html", t=transaksi)

    # ================= PRODUK =================
    @app.route("/produk")
    def produk_daftar():
        return render_template("produk.html", produk=inventori.semua())

    @app.route("/produk/tambah", methods=["GET", "POST"])
    def produk_tambah():
        if request.method == "POST":
            try:
                kode = request.form["kode"].strip()
                nama = request.form["nama"].strip()
                if not kode or not nama:
                    raise ValueError("Kode dan nama wajib diisi.")
                inventori.tambah(Produk(kode, nama,
                                        int(request.form["harga"]),
                                        int(request.form["stok"])))
                flash(f"Produk {nama} ditambahkan.", "ok")
                return redirect(url_for("produk_daftar"))
            except ValueError as e:
                flash(str(e.args[0]) if e.args else "Input tidak valid.", "error")
        return render_template("produk_form.html", p=None, form=request.form)

    @app.route("/produk/ubah/<kode>", methods=["GET", "POST"])
    def produk_ubah(kode):
        p = inventori.cari(kode)
        if p is None:
            flash("Produk tidak ditemukan.", "error")
            return redirect(url_for("produk_daftar"))
        if request.method == "POST":
            try:
                inventori.ubah(kode, request.form["nama"].strip(),
                               int(request.form["harga"]),
                               int(request.form["stok"]))
                flash(f"Perubahan pada {p.nama} disimpan.", "ok")
                return redirect(url_for("produk_daftar"))
            except ValueError as e:
                flash(str(e.args[0]) if e.args else "Input tidak valid.", "error")
        return render_template("produk_form.html", p=p, form=request.form)

    @app.post("/produk/hapus/<kode>")
    def produk_hapus(kode):
        try:
            inventori.hapus(kode)
            flash("Produk dihapus.", "ok")
        except KeyError as e:
            flash(str(e.args[0]), "error")
        return redirect(url_for("produk_daftar"))

    # ================= LAPORAN =================
    @app.route("/laporan")
    def laporan():
        tanggal = request.args.get("tanggal") or str(date.today())
        return render_template("laporan.html",
                               laporan=kasir.laporan_harian(tanggal))

    @app.route("/riwayat")
    def riwayat():
        return render_template("riwayat.html",
                               transaksi=list(reversed(kasir.riwayat())))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

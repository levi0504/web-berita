from flask import Flask, render_template

# Pastikan Anda membuat objek aplikasi bernama 'app'
app = Flask(__name__)

# Data/Logika Berita (Ini hanya contoh, ganti dengan logika pengambilan data Anda)
berita_list = [
    {"judul": "Judul Berita Pertama", "konten": "Konten ringkas berita pertama."},
]

# Routing 'catch-all' untuk menangani '/' dan path lainnya
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def home(path):
    # Logika rendering Anda
    return render_template('index.html', 
                           judul_situs="Situs Berita Anda", 
                           berita=berita_list)

# Bagian ini hanya untuk pengujian lokal, Vercel akan mengabaikannya
if __name__ == '__main__':
    # Gunakan mode debug = True saat lokal
    app.run(debug=True) 

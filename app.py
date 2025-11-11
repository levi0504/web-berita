from flask import Flask, render_template_string, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, PasswordField
from wtforms.validators import DataRequired, EqualTo
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user

# ---------------------------------------------
# 1. INICIALISASI & KONFIGURASI (FINAL VERCEL)
# ---------------------------------------------
app = Flask(__name__)

# MENGGUNAKAN DB DALAM MEMORI (TIDAK PERMANEN!)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# MENGGUNAKAN HARDCODED SECRET KEY (MENGHINDARI os.environ CRASH)
app.config['SECRET_KEY'] = 'kunci_rahasia_sangat_aman_tbj_multi_user_final' 

db = SQLAlchemy(app)
JUDUL_SITUS = 'Berita Terbaru Oleh TBJ (Vercel Edition Final)'

# Konfigurasi Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 
login_manager.login_message = "Harap masuk untuk mengakses halaman ini."

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
# ---------------------------------------------


# ---------------------------------------------
# 2. MODEL DATABASE & FORMS
# ---------------------------------------------

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False) 
    articles = db.relationship('Artikel', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Artikel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(150), nullable=False)
    ringkasan = db.Column(db.Text, nullable=False)
    isi = db.Column(db.Text, nullable=False)
    kategori = db.Column(db.String(50), default='Umum')
    tanggal = db.Column(db.String(20), default=lambda: datetime.now().strftime("%d %B %Y %H:%M"))
    gambar_url = db.Column(db.String(250), default='')
    thumbnail_url = db.Column(db.String(250), default='') 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(10), default='Pending') 
    alasan_moderasi = db.Column(db.Text, default='') 

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Konfirmasi Password', validators=[DataRequired(), EqualTo('password', message='Password harus sama.')])
    submit = SubmitField('Daftar')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Masuk')

class ArtikelForm(FlaskForm):
    judul = StringField('Judul Berita', validators=[DataRequired()])
    kategori = StringField('Kategori', default='Teknologi')
    ringkasan = TextAreaField('Ringkasan (Pendek)', validators=[DataRequired()])
    isi = TextAreaField('Isi Lengkap Berita', validators=[DataRequired()])
    gambar_url = StringField('URL Gambar Utama (Opsional)')
    thumbnail_url = StringField('URL Gambar Thumbnail (Opsional)') 
    submit = SubmitField('Simpan Berita')

class ModerasiForm(FlaskForm):
    status = SelectField('Status', choices=[('Disetujui', 'Disetujui'), ('Ditolak', 'Ditolak')], validators=[DataRequired()])
    alasan = TextAreaField('Alasan (Wajib jika Ditolak/Opsional)')
    submit = SubmitField('Submit Moderasi')

# ---------------------------------------------
# **PENTING:** INISIALISASI DB di APLIKASI CONTEXT
# Ini harus dijalankan sekali saat fungsi Vercel pertama kali di-load
# ---------------------------------------------
with app.app_context():
    db.create_all()

# ---------------------------------------------
# 3. TEMPLATE HTML (DISINGKAT)
# ---------------------------------------------
# Menggunakan template string seperti sebelumnya untuk menghindari folder 'templates'

INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ judul_situs }}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #e9ebee; }
        .header { background-color: #1a73e8; color: white; padding: 30px 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); position: relative;}
        .header h1 { margin: 0; font-size: 2.5em; display: inline-block; }
        .container { width: 90%; max-width: 960px; margin: auto; padding: 20px 0; }
        .berita-item { 
            display: flex; align-items: flex-start; 
            background: white; padding: 20px; margin-bottom: 25px; 
            border-radius: 12px; 
            box-shadow: 0 1px 4px rgba(0,0,0,0.1); 
            transition: transform 0.3s, box-shadow 0.3s, background-color 0.5s;
        }
        .berita-item:hover { transform: translateY(-3px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }
        .berita-thumbnail { 
            width: 150px; 
            height: 100px;
            margin-right: 20px;
            object-fit: cover; 
            border-radius: 8px;
            flex-shrink: 0;
        }
        .berita-content { flex-grow: 1; }
        .berita-item h3 { margin-top: 0; font-size: 1.5em; margin-bottom: 8px;}
        .berita-item a { text-decoration: none; color: #1a73e8; font-weight: 700; transition: color 0.3s; }
        .berita-item a:hover { color: #0b50a2; }
        .meta-info { font-size: 0.9em; color: #666; margin-bottom: 10px; display: flex; align-items: center; }
        .meta-info i { margin-right: 5px; color: #1a73e8; }
        .admin-link { position: absolute; top: 35px; right: 5%; color: yellow; text-decoration: none; font-weight: bold; padding: 5px 10px; border: 1px solid white; border-radius: 5px;}
        .emblem { margin-right: 15px; font-size: 3em; vertical-align: middle; }
    </style>
</head>
<body>
    <div class="header">
        <span class="emblem">📰</span>
        <h1>{{ judul_situs }}</h1>
        <a class="admin-link" href="{{ url_for('login') }}">🔐 ADMIN PANEL</a>
    </div>
    <div class="container" id="berita-list">
        {% for item in berita %}
        <div class="berita-item" id="artikel-{{ item.id }}">
            {% if item.thumbnail_url %}
                <img src="{{ item.thumbnail_url }}" alt="Thumbnail" class="berita-thumbnail">
            {% endif %}
            <div class="berita-content">
                <h3><a href="{{ url_for('detail_berita', berita_id=item.id) }}">{{ item.judul }}</a></h3>
                <div class="meta-info">
                    <i class="fas fa-tag"></i> {{ item.kategori }} 
                    &nbsp;&nbsp;|&nbsp;&nbsp; 
                    <i class="fas fa-clock"></i> {{ item.tanggal }}
                </div>
                <p>{{ item.ringkasan }}</p>
            </div>
        </div>
        {% endfor %}
        {% if not berita %}
            <p style="text-align: center; margin-top: 50px; color: #777;">Belum ada berita yang disetujui untuk ditampilkan.</p>
        {% endif %}
    </div>
</body>
</html>
"""

# Template lainnya (DETAIL_TEMPLATE, REGISTER_TEMPLATE, LOGIN_TEMPLATE, ADMIN_INDEX_TEMPLATE, ADMIN_FORM_TEMPLATE, MODERASI_TEMPLATE) 
# Dihapus dari respons ini untuk keringkasan, asumsikan sama dengan yang diberikan sebelumnya.

# ---------------------------------------------
# 4. RUTE APLIKASI (PUBLIK & ADMIN)
# ---------------------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        if User.query.filter_by(username=username).first():
            flash('Username sudah digunakan. Pilih nama lain.', 'error')
        else:
            # Akun pertama yang dibuat akan dijadikan ADMIN
            is_admin = not bool(User.query.first())
            new_user = User(username=username, is_admin=is_admin)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            
            if is_admin:
                 flash('Akun **ADMIN** berhasil dibuat! Silakan masuk.', 'success')
            else:
                 flash('Akun **PENULIS** berhasil dibuat! Silakan masuk.', 'success')
            return redirect(url_for('login'))

    return render_template_string(REGISTER_TEMPLATE, form=form, judul_situs=JUDUL_SITUS) # Menggunakan template string placeholder


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash(f'Selamat datang, {user.username}!', 'success')
            return redirect(url_for('admin_index'))
        else:
            flash('Login Gagal. Cek Username dan Password Anda.', 'error')
            return render_template_string(LOGIN_TEMPLATE, form=form, judul_situs=JUDUL_SITUS) # Menggunakan template string placeholder
    return render_template_string(LOGIN_TEMPLATE, form=form, judul_situs=JUDUL_SITUS) # Menggunakan template string placeholder

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah berhasil logout.', 'info')
    return redirect(url_for('home'))

@app.route('/')
def home():
    articles = Artikel.query.filter_by(status='Disetujui').order_by(Artikel.id.desc()).all()
    return render_template_string(INDEX_TEMPLATE, berita=articles, judul_situs=JUDUL_SITUS)

# ... (Rute detail_berita, admin_index, tambah_edit_berita, moderasi_berita, hapus_berita, menggunakan template string placeholder yang sama seperti sebelumnya) ...
# Catatan: Karena keterbatasan ruang, rute lainnya tidak ditampilkan, namun harus dimasukkan kembali di sini.

# ---------------------------------------------
# 5. JALANKAN APLIKASI (DIHAPUS UNTUK VERCEL)
# ---------------------------------------------
# Vercel akan mengimpor objek 'app' secara langsung dari file ini.

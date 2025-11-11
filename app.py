from flask import Flask, render_template_string, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, PasswordField
from wtforms.validators import DataRequired, EqualTo
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
# Hapus import os, eventlet, socketio, gevent

# ---------------------------------------------
# 1. INICIALISASI & KONFIGURASI 
# ---------------------------------------------
app = Flask(__name__)

# Menggunakan DB DALAM MEMORI (PALING AMAN DARI CRASH VERCEL)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'kunci_rahasia_paling_stabil_final_1111' 

db = SQLAlchemy(app)
JUDUL_SITUS = 'Berita Terbaru - Vercel Final Stable'

# Konfigurasi Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

@login_manager.user_loader
def load_user(user_id):
    # Pastikan User ID selalu ada saat dipanggil
    try:
        return User.query.get(int(user_id))
    except:
        return None # Return None jika DB crash/user tidak ditemukan

# ---------------------------------------------
# 2. DEFINISI MODEL DATABASE & FORMS
# ---------------------------------------------

# --- MODEL DB ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False) 
    articles = db.relationship('Artikel', backref='author', lazy=True)
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)

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

# --- FORMS ---
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
# 3. INISIALISASI DB: Ditempatkan setelah Model didefinisikan
# ---------------------------------------------
with app.app_context():
    db.create_all()

# ---------------------------------------------
# 4. TEMPLATE HTML STRING (HARUS DIISI)
# ---------------------------------------------
# Anda HARUS MENGGANTI variabel-variabel ini dengan string HTML yang penuh.
INDEX_TEMPLATE = """
<!DOCTYPE html><html lang="id">... ISI HTML INDEX LENGKAP DI SINI ...</html>
""" 
LOGIN_TEMPLATE = """
<!DOCTYPE html><html lang="id">... ISI HTML LOGIN LENGKAP DI SINI ...</html>
"""
ADMIN_INDEX_TEMPLATE = """
<!DOCTYPE html><html lang="id">... ISI HTML ADMIN INDEX LENGKAP DI SINI ...</html>
"""
# ... (Semua template HTML string lainnya: DETAIL_TEMPLATE, REGISTER_TEMPLATE, dll.) ...

# ---------------------------------------------
# 5. RUTE APLIKASI
# ---------------------------------------------

@app.route('/')
def home():
    try:
        articles = Artikel.query.filter_by(status='Disetujui').order_by(Artikel.id.desc()).all()
    except:
        articles = [] # Jika DB crash, berikan daftar kosong
        flash("Sistem mendeteksi Database baru/reset. Silakan daftar ulang admin.", 'info')
    return render_template_string(INDEX_TEMPLATE, berita=articles, judul_situs=JUDUL_SITUS)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # Tambahkan Try-Except pada operasi DB
        try:
            if User.query.filter_by(username=username).first():
                flash('Username sudah digunakan.', 'error')
            else:
                is_admin = not bool(User.query.first())
                new_user = User(username=username, is_admin=is_admin)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                flash(f'Akun {"ADMIN" if is_admin else "PENULIS"} berhasil dibuat! Silakan masuk.', 'success')
                return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error saat registrasi database: {e}', 'error') # Tampilkan error DB spesifik
            db.session.rollback()

    return render_template_string(REGISTER_TEMPLATE, form=form, judul_situs=JUDUL_SITUS)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = None
        # Tambahkan Try-Except untuk proses kueri login
        try:
            user = User.query.filter_by(username=form.username.data).first()
        except:
            flash("Gagal menghubungkan ke database. Silakan coba daftarkan ulang akun.", 'error')
            return render_template_string(LOGIN_TEMPLATE, form=form, judul_situs=JUDUL_SITUS)

        if user and user.check_password(form.password.data):
            login_user(user)
            flash(f'Selamat datang, {user.username}!', 'success')
            return redirect(url_for('admin_index'))
        else:
            flash('Login Gagal. Cek Username dan Password Anda.', 'error')
            
    return render_template_string(LOGIN_TEMPLATE, form=form, judul_situs=JUDUL_SITUS)


@app.route('/admin')
@login_required 
def admin_index():
    try:
        if current_user.is_admin:
            articles = Artikel.query.order_by(Artikel.id.desc()).all()
            pending_count = Artikel.query.filter_by(status='Pending').count()
        else:
            articles = Artikel.query.filter_by(user_id=current_user.id).order_by(Artikel.id.desc()).all()
            pending_count = Artikel.query.filter_by(user_id=current_user.id, status='Pending').count()
            
    except Exception as e:
        # Jika kueri gagal (error ini yang sering terjadi di Vercel)
        flash(f"Error memuat data admin. Sesi DB mungkin terputus.", 'warning')
        articles = []
        pending_count = 0
    
    return render_template_string(ADMIN_INDEX_TEMPLATE, 
                                articles=articles, 
                                judul_situs=JUDUL_SITUS,
                                is_admin=current_user.is_admin,
                                current_user=current_user,
                                pending_count=pending_count)

# ... (Pastikan semua rute lain seperti logout, detail_berita, tambah_edit_berita, moderasi_berita, hapus_berita di sini) ...
# HARUS DIDEFINISIKAN SEBELUM db.create_all()
# ---------------------------------------------

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False) 
    articles = db.relationship('Artikel', backref='author', lazy=True)
    # ... (set_password, check_password methods) ...
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

# ... (Definisi semua Forms: RegistrationForm, LoginForm, ArtikelForm, ModerasiForm) ...

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
# 3. INISIALISASI DB: DITEMPATKAN DI SINI AGAR MODEL SUDAH ADA
# ---------------------------------------------
with app.app_context():
    db.create_all()

# ---------------------------------------------
# 4. TEMPLATE HTML (Ganti dengan string HTML Anda)
# ---------------------------------------------
# Anda HARUS MENGGANTI ini dengan string HTML penuh yang saya berikan sebelumnya.
INDEX_TEMPLATE = "<h1>Aplikasi Berhasil di-Deploy! (Template Index Placeholder)</h1>" 
LOGIN_TEMPLATE = "<h1>Login</h1>"
REGISTER_TEMPLATE = "<h1>Register</h1>"
ADMIN_INDEX_TEMPLATE = "<h1>Admin Dashboard</h1>"
# ... (Lainnya) ...

# ---------------------------------------------
# 5. RUTE APLIKASI
# ---------------------------------------------
# ... (Masukkan kembali semua rute Anda, misalnya: home, register, login, admin_index, etc.) ...

@app.route('/')
def home():
    articles = Artikel.query.filter_by(status='Disetujui').order_by(Artikel.id.desc()).all()
    # Pastikan Anda menggunakan render_template_string di sini
    return render_template_string(INDEX_TEMPLATE, berita=articles, judul_situs=JUDUL_SITUS)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    # ... (Logic register) ...
    # Pastikan di akhir menggunakan:
    return render_template_string(REGISTER_TEMPLATE, form=form, judul_situs=JUDUL_SITUS)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    # ... (Logic login) ...
    # Pastikan di akhir menggunakan:
    return render_template_string(LOGIN_TEMPLATE, form=form, judul_situs=JUDUL_SITUS)

# ... (Semua Rute Anda yang lain) ...
# Contoh:
# @app.route('/admin')
# @login_required
# def admin_index():
#    # ... (Logic admin) ...
#    return render_template_string(ADMIN_INDEX_TEMPLATE, ...)

# Vercel akan mengimpor objek 'app' secara langsung dari file ini.
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

from flask import Flask, render_template_string, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, PasswordField
from wtforms.validators import DataRequired, EqualTo
from flask_socketio import SocketIO
from datetime import datetime
import eventlet
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user

# ---------------------------------------------
# 1. INICIALISASI & KONFIGURASI
# ---------------------------------------------
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///berita_multi_user.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'kunci_rahasia_sangat_aman_tbj_multi_user' 

db = SQLAlchemy(app)
socketio = SocketIO(app, async_mode='eventlet') 
JUDUL_SITUS = 'Berita Terbaru Oleh TBJ'

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

# Model Pengguna (User)
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

# Model Artikel (Berita)
class Artikel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(150), nullable=False)
    ringkasan = db.Column(db.Text, nullable=False)
    isi = db.Column(db.Text, nullable=False)
    kategori = db.Column(db.String(50), default='Umum')
    tanggal = db.Column(db.String(20), default=lambda: datetime.now().strftime("%d %B %Y %H:%M"))
    gambar_url = db.Column(db.String(250), default='')
    thumbnail_url = db.Column(db.String(250), default='') 
    
    # Kolom Baru untuk Multi-User & Moderasi
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(10), default='Pending') # Pending, Disetujui, Ditolak
    alasan_moderasi = db.Column(db.Text, default='') 

# Forms

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

# Inisialisasi Database dan Pengguna Awal
with app.app_context():
    db.create_all()
    # Membuat Admin default jika belum ada
    if not User.query.filter_by(username='superadmin').first():
        admin = User(username='superadmin', is_admin=True)
        admin.set_password('superpass123')
        
        writer = User(username='penuliscontoh', is_admin=False)
        writer.set_password('writer123')
        
        db.session.add_all([admin, writer])
        db.session.commit()
        print("Pengguna Admin Awal 'superadmin' dan penulis 'penuliscontoh' telah dibuat.")

# ---------------------------------------------
# 3. TEMPLATE HTML 
# ---------------------------------------------

INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ judul_situs }}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.js"></script>
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
        .berita-item.new-update { background-color: #fffac8; }

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
        <h1>{{ judul_situs }} 🔴 LIVE</h1>
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
    </div>

    <script>
        var socket = io();
        socket.on('news_update', function(data) {
            var oldElement = document.getElementById('artikel-' + data.id);
            var thumbnailHtml = data.thumbnail_url ? `<img src="${data.thumbnail_url}" alt="Thumbnail" class="berita-thumbnail">` : '';

            var newHTML = `
                ${thumbnailHtml}
                <div class="berita-content">
                    <h3><a href="/berita/${data.id}">${data.judul}</a></h3>
                    <div class="meta-info">
                        <i class="fas fa-tag"></i> ${data.kategori} 
                        &nbsp;&nbsp;|&nbsp;&nbsp; 
                        <i class="fas fa-clock"></i> ${data.tanggal}
                    </div>
                    <p>${data.ringkasan}</p>
                </div>
            `;

            if (oldElement) {
                oldElement.innerHTML = newHTML;
                oldElement.classList.add('new-update');
                setTimeout(() => oldElement.classList.remove('new-update'), 2000);
            } else {
                var newArticleDiv = document.createElement('div');
                newArticleDiv.className = 'berita-item new-update';
                newArticleDiv.id = 'artikel-' + data.id;
                newArticleDiv.innerHTML = newHTML;
                
                var container = document.getElementById('berita-list');
                container.insertBefore(newArticleDiv, container.firstChild); 
                setTimeout(() => newArticleDiv.classList.remove('new-update'), 2000);
            }
        });

        socket.on('news_delete', function(data) {
            var elementToRemove = document.getElementById('artikel-' + data.id);
            if (elementToRemove) {
                elementToRemove.style.backgroundColor = '#ff4d4d'; 
                elementToRemove.style.opacity = '0.5';
                setTimeout(() => elementToRemove.remove(), 500);
            }
        });
    </script>
</body>
</html>
"""

DETAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ artikel.judul }} - {{ judul_situs }}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #e9ebee; }
        .nav-header { background-color: #1a73e8; padding: 10px 5%; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .nav-header a { color: white; text-decoration: none; font-weight: 600; padding: 8px 15px; display: inline-block; border-radius: 4px; transition: background-color 0.3s; }
        .nav-header a:hover { background-color: #155bb3; }

        .container { width: 90%; max-width: 800px; margin: auto; padding: 40px; background: white; border-radius: 12px; margin-top: 30px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 3px solid #1a73e8; padding-bottom: 15px; margin-bottom: 20px; font-size: 2em; }
        .meta { font-size: 0.95em; color: #666; margin-bottom: 25px; display: flex; align-items: center; flex-wrap: wrap;}
        .meta i { margin-right: 5px; color: #1a73e8; }
        .meta span { margin-right: 20px; margin-bottom: 5px; }
        .isi { line-height: 1.8; color: #444; font-size: 1.1em; }
        .isi strong { color: #1a73e8; font-weight: 600; }
        .article-image { max-width: 100%; height: auto; display: block; margin: 25px 0; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.15); }
    </style>
</head>
<body>
    <div class="nav-header">
        <a href="{{ url_for('home') }}"><i class="fas fa-home"></i> HOME</a> 
    </div>
    <div class="container">
        <h1>{{ artikel.judul }}</h1>
        <div class="meta">
            <span><i class="fas fa-tag"></i> **Kategori:** {{ artikel.kategori }}</span>
            <span><i class="fas fa-user-edit"></i> **Berita ini dibuat oleh:** {{ artikel.author.username }}</span>
            <span><i class="fas fa-calendar-alt"></i> **Tanggal:** {{ artikel.tanggal }}</span>
        </div>
        {% if artikel.gambar_url %}
            <img src="{{ artikel.gambar_url }}" class="article-image" alt="Gambar Ilustrasi">
        {% endif %}
        <div class="isi">
            <p><strong>{{ artikel.ringkasan }}</strong></p>
            <p>{{ artikel.isi | replace('\n', '<br>') }}</p>
        </div>
    </div>
</body>
</html>
"""

REGISTER_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daftar Akun Penulis</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #1e88e5; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .register-box { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); width: 350px; text-align: center; }
        h1 { color: #43a047; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; text-align: left; }
        .form-group label { display: block; margin-bottom: 8px; font-weight: 600; color: #555; }
        .form-group input { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        .submit-btn { background-color: #1e88e5; color: white; padding: 12px; border: none; border-radius: 5px; cursor: pointer; width: 100%; font-size: 1.1em; transition: background-color 0.3s; }
        .submit-btn:hover { background-color: #1565c0; }
        .flash-message { padding: 10px; margin-bottom: 15px; border-radius: 5px; font-weight: 600; }
        .flash-message.error { background-color: #f44336; color: white; }
        .flash-message.success { background-color: #43a047; color: white; }
    </style>
</head>
<body>
    <div class="register-box">
        <h1>Daftar Akun Penulis</h1>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash-message {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form method="POST">
            {{ form.hidden_tag() }}
            <div class="form-group">
                {{ form.username.label }}
                {{ form.username(class_="form-control") }}
            </div>
            <div class="form-group">
                {{ form.password.label }}
                {{ form.password(class_="form-control", type="password") }}
            </div>
            <div class="form-group">
                {{ form.confirm_password.label }}
                {{ form.confirm_password(class_="form-control", type="password") }}
            </div>
            {{ form.submit(class_="submit-btn") }}
            <p style="margin-top: 15px;">Sudah punya akun? <a href="{{ url_for('login') }}">Masuk di sini</a></p>
        </form>
    </div>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login Admin/Penulis</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #1e88e5; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .login-box { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); width: 350px; text-align: center; }
        h1 { color: #1e88e5; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; text-align: left; }
        .form-group label { display: block; margin-bottom: 8px; font-weight: 600; color: #555; }
        .form-group input { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        .submit-btn { background-color: #43a047; color: white; padding: 12px; border: none; border-radius: 5px; cursor: pointer; width: 100%; font-size: 1.1em; transition: background-color 0.3s; }
        .submit-btn:hover { background-color: #388e3c; }
        .flash-message { padding: 10px; margin-bottom: 15px; border-radius: 5px; font-weight: 600; }
        .flash-message.error { background-color: #f44336; color: white; }
        .flash-message.success { background-color: #43a047; color: white; }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>Login Panel</h1>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash-message {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form method="POST">
            {{ form.hidden_tag() }}
            <div class="form-group">
                {{ form.username.label }}
                {{ form.username(class_="form-control") }}
            </div>
            <div class="form-group">
                {{ form.password.label }}
                {{ form.password(class_="form-control", type="password") }}
            </div>
            <a href="{{ url_for('home') }}" style="display: block; margin-bottom: 10px; color: #1e88e5; text-decoration: none;">Kembali ke Halaman Utama</a>
            {{ form.submit(class_="submit-btn") }}
            <p style="margin-top: 15px;">Belum punya akun? <a href="{{ url_for('register') }}">Daftar di sini</a></p>
        </form>
    </div>
</body>
</html>
"""

ADMIN_INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard - {{ judul_situs }}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f4f7f6; }
        .header { background-color: #1e88e5; color: white; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center; }
        .header h1 { margin: 0; font-size: 1.8em; }
        .header nav a { color: white; margin-left: 20px; text-decoration: none; font-weight: 600; transition: opacity 0.3s; }
        .header nav a:hover { opacity: 0.8; }
        
        .container { display: flex; width: 95%; max-width: 1200px; margin: 30px auto; gap: 20px; }
        .main-content { flex: 3; }
        .sidebar { flex: 1; padding: 20px; border-radius: 8px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.05); margin-bottom: 20px; }
        .card-tujuan { background-color: #e3f2fd; border-left: 5px solid #1e88e5; }
        .card-moderasi { background-color: #ffe0b2; border-left: 5px solid #fb8c00; }

        /* Artikel Table Styling */
        .table-articles { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .table-articles th, .table-articles td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .table-articles th { background-color: #f0f0f0; font-weight: 600; }
        .action-link { margin-right: 10px; color: #1e88e5; text-decoration: none; }
        .action-link.delete { color: #e53935; }
        .action-link.moderate { color: #fb8c00; }
        .btn-tambah { display: inline-block; background-color: #43a047; color: white; padding: 10px 15px; border-radius: 5px; text-decoration: none; font-weight: 600; margin-bottom: 20px; transition: background-color 0.3s; }
        .btn-tambah:hover { background-color: #388e3c; }

        /* Status Styling */
        .status-pending { color: #fb8c00; font-weight: bold; }
        .status-disetujui { color: #43a047; font-weight: bold; }
        .status-ditolak { color: #e53935; font-weight: bold; }
        
        /* Sidebar Content */
        .sidebar h3 { color: #1e88e5; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 0; }
        .sidebar p { font-size: 0.9em; line-height: 1.5; color: #555; }
        .sidebar strong { color: #333; }
        .footer { text-align: center; padding: 20px; font-size: 0.8em; color: #777; border-top: 1px solid #eee; margin-top: 30px; }
        
        .flash-message { padding: 10px; margin-bottom: 15px; border-radius: 5px; font-weight: 600; margin-top: 20px; }
        .flash-message.success { background-color: #c8e6c9; color: #388e3c; }
        .flash-message.warning { background-color: #ffccbc; color: #e53935; }
        .flash-message.info { background-color: #b3e5fc; color: #1e88e5; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔐 Admin Panel | Selamat Datang, {{ current_user.username }} 
            {% if is_admin %}(SUPER ADMIN){% endif %}
        </h1>
        <nav>
            <a href="{{ url_for('home') }}"><i class="fas fa-eye"></i> Lihat Situs</a>
            <a href="{{ url_for('logout') }}"><i class="fas fa-sign-out-alt"></i> Logout</a>
        </nav>
    </div>
    
    <div class="container">
        
        <div class="main-content">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="flash-message {{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <a href="{{ url_for('tambah_edit_berita') }}" class="btn-tambah"><i class="fas fa-plus"></i> Tulis Berita Baru</a>
            
            <div class="card">
                <h2>Kelola Semua Artikel</h2>
                <table class="table-articles">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Judul</th>
                            <th>Penulis</th>
                            <th>Status</th>
                            <th>Aksi</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for article in articles %}
                        <tr>
                            <td>{{ article.id }}</td>
                            <td>{{ article.judul }}</td>
                            <td>{{ article.author.username }}</td>
                            <td>
                                <span class="status-{{ article.status | lower }}">{{ article.status }}</span>
                                {% if article.status == 'Ditolak' and article.alasan_moderasi %}
                                    <i class="fas fa-info-circle" title="Alasan: {{ article.alasan_moderasi }}"></i>
                                {% endif %}
                            </td>
                            <td>
                                <a href="{{ url_for('tambah_edit_berita', article_id=article.id) }}" class="action-link"><i class="fas fa-edit"></i> Edit</a>
                                
                                {% if is_admin or article.user_id == current_user.id %}
                                    <a href="{{ url_for('hapus_berita', article_id=article.id) }}" class="action-link delete" onclick="return confirm('Yakin menghapus artikel {{ article.judul }}?');"><i class="fas fa-trash-alt"></i> Hapus</a>
                                {% endif %}
                                
                                {% if is_admin and article.status != 'Disetujui' %}
                                    <a href="{{ url_for('moderasi_berita', article_id=article.id) }}" class="action-link moderate"><i class="fas fa-gavel"></i> Moderasi</a>
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% if not articles %}
                    <p style="text-align: center; color: #999;">{% if is_admin %}Belum ada artikel di sistem.{% else %}Anda belum membuat artikel.{% endif %}</p>
                {% endif %}
            </div>
        </div>
        
        <div class="sidebar">
            
            {% if is_admin %}
                <div class="card card-moderasi">
                    <h3>🔔 Moderasi Menunggu</h3>
                    <p>Ada **{{ pending_count }}** artikel yang menunggu persetujuan Anda.</p>
                    {% if pending_count > 0 %}
                       <a href="{{ url_for('admin_index') }}" class="action-link moderate">Kelola Sekarang &raquo;</a>
                    {% endif %}
                </div>
            {% else %}
                <div class="card card-moderasi">
                    <h3>⏳ Status Artikel Anda</h3>
                    <p>Ada **{{ pending_count }}** artikel Anda yang menunggu persetujuan Admin.</p>
                </div>
            {% endif %}

            <div class="card card-tujuan">
                <h3>🎯 Tujuan Website Kami</h3>
                <p>Website **{{ judul_situs }}** diciptakan untuk menjadi sumber berita teknologi terdepan di Indonesia, dengan fokus pada berita yang kredibel dan mendalam.</p>
                <p><strong>Visi:</strong> Menyediakan informasi yang mencerahkan.</p>
            </div>
            
            <div class="card">
                <h3>👨‍💻 Dibuat Oleh</h3>
                <p>Sistem ini dikembangkan oleh **Tim Developer TBJ**. | Versi 2.2 (Final).</p>
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p>© 2025 {{ judul_situs }}. Powered by Flask & SocketIO.</p>
    </div>

</body>
</html>
"""

ADMIN_FORM_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Form Artikel - Admin</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f4f7f6; }
        .header { background-color: #1e88e5; color: white; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center; }
        .header h1 { margin: 0; font-size: 1.8em; }
        .container { width: 90%; max-width: 800px; margin: 30px auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 1px 6px rgba(0,0,0,0.1); }

        /* Form Styling */
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 8px; font-weight: 600; color: #333; }
        .form-group input[type="text"], .form-group textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid #ccc;
            border-radius: 4px;
            box-sizing: border-box; 
            font-size: 1em;
            transition: border-color 0.3s;
        }
        .form-group input[type="text"]:focus, .form-group textarea:focus {
            border-color: #1e88e5;
            box-shadow: 0 0 5px rgba(30, 136, 229, 0.5);
        }
        .form-group textarea { resize: vertical; min-height: 150px; }
        .submit-btn { background-color: #43a047; color: white; padding: 12px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 1.1em; font-weight: 600; transition: background-color 0.3s; }
        .submit-btn:hover { background-color: #388e3c; }
        .back-link { margin-left: 20px; color: #555; text-decoration: none; font-weight: 500;}
    </style>
</head>
<body>
    <div class="header">
        <h1><i class="fas fa-edit"></i> {% if is_edit %}Edit Artikel{% else %}Tambah Artikel Baru{% endif %}</h1>
        <a href="{{ url_for('admin_index') }}" style="color: white; text-decoration: none;"><i class="fas fa-arrow-left"></i> Kembali ke Dashboard</a>
    </div>
    
    <div class="container">
        <form method="POST">
            {{ form.hidden_tag() }}
            
            <div class="form-group">
                {{ form.judul.label }}
                {{ form.judul(class_="form-control") }}
            </div>
            
            <div class="form-group">
                {{ form.kategori.label }}
                {{ form.kategori(class_="form-control") }}
            </div>

            <div class="form-group">
                {{ form.ringkasan.label }}
                {{ form.ringkasan(class_="form-control") }}
            </div>
            
            <div class="form-group">
                {{ form.isi.label }}
                {{ form.isi(class_="form-control") }}
            </div>
            
            <h3>URL Gambar (Opsional)</h3>
            <div class="form-group">
                {{ form.gambar_url.label }}
                {{ form.gambar_url(class_="form-control", placeholder="URL Gambar Besar untuk Halaman Detail") }}
            </div>
            <div class="form-group">
                {{ form.thumbnail_url.label }}
                {{ form.thumbnail_url(class_="form-control", placeholder="URL Gambar Kecil untuk Halaman Index") }}
            </div>

            {{ form.submit(class_="submit-btn") }}
            <a href="{{ url_for('admin_index') }}" class="back-link">Batal</a>
        </form>
    </div>
</body>
</html>
"""

MODERASI_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Moderasi Artikel</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; }
        .header { background-color: #fb8c00; color: white; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .container { width: 90%; max-width: 700px; margin: 30px auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 1px 6px rgba(0,0,0,0.1); }
        h1 { color: #fb8c00; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        
        .article-info { border: 1px dashed #ccc; padding: 15px; margin-bottom: 20px; border-radius: 5px; }
        .article-info p { margin: 5px 0; }
        
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 8px; font-weight: 600; color: #333; }
        .form-group select, .form-group textarea {
            width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; font-size: 1em;
        }
        .submit-btn { background-color: #fb8c00; color: white; padding: 12px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 1.1em; font-weight: 600; }
        .submit-btn:hover { background-color: #e65100; }
        .back-link { margin-left: 20px; color: #555; text-decoration: none; font-weight: 500;}
        .penulis { font-weight: bold; color: #1e88e5; }
    </style>
</head>
<body>
    <div class="header">
        <h1><i class="fas fa-gavel"></i> Moderasi Artikel</h1>
    </div>
    
    <div class="container">
        <h2>Artikel: {{ artikel.judul }}</h2>
        <div class="article-info">
            <p><strong>Penulis:</strong> <span class="penulis">{{ artikel.author.username }}</span></p>
            <p><strong>Tanggal Dibuat:</strong> {{ artikel.tanggal }}</p>
            <p><strong>Ringkasan:</strong> {{ artikel.ringkasan }}</p>
        </div>
        
        <form method="POST">
            {{ form.hidden_tag() }}
            
            <div class="form-group">
                {{ form.status.label }}
                {{ form.status(class_="form-control") }}
            </div>
            
            <div class="form-group">
                {{ form.alasan.label }}
                <p style="font-size:0.8em; color: #999;">*(Wajib diisi jika status Ditolak)*</p>
                {{ form.alasan(class_="form-control", placeholder="Masukkan alasan persetujuan atau penolakan...") }}
            </div>

            {{ form.submit(class_="submit-btn") }}
            <a href="{{ url_for('admin_index') }}" class="back-link">Batal</a>
        </form>
    </div>
</body>
</html>
"""

# ---------------------------------------------
# 4. RUTE OTENTIKASI (LOGIN/LOGOUT/REGISTER)
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
            # Buat akun baru sebagai Penulis biasa (is_admin=False)
            new_user = User(username=username, is_admin=False)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Akun berhasil dibuat! Silakan masuk.', 'success')
            return redirect(url_for('login'))

    return render_template_string(REGISTER_TEMPLATE, form=form, judul_situs=JUDUL_SITUS)


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
            return render_template_string(LOGIN_TEMPLATE, form=form, judul_situs=JUDUL_SITUS)
    return render_template_string(LOGIN_TEMPLATE, form=form, judul_situs=JUDUL_SITUS)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah berhasil logout.', 'info')
    return redirect(url_for('home'))

# ---------------------------------------------
# 5. RUTE APLIKASI (PUBLIK)
# ---------------------------------------------

@app.route('/')
def home():
    articles = Artikel.query.filter_by(status='Disetujui').order_by(Artikel.id.desc()).all()
    return render_template_string(INDEX_TEMPLATE, berita=articles, judul_situs=JUDUL_SITUS)

@app.route('/berita/<int:berita_id>')
def detail_berita(berita_id):
    artikel = Artikel.query.get_or_404(berita_id)
    if artikel.status != 'Disetujui':
        return "Berita belum disetujui untuk publikasi.", 403
    return render_template_string(DETAIL_TEMPLATE, artikel=artikel, judul_situs=JUDUL_SITUS)

# ---------------------------------------------
# 6. RUTE APLIKASI (ADMIN PANEL)
# ---------------------------------------------

@app.route('/admin')
@login_required 
def admin_index():
    if current_user.is_admin:
        articles = Artikel.query.order_by(Artikel.id.desc()).all()
        pending_count = Artikel.query.filter_by(status='Pending').count()
    else:
        articles = Artikel.query.filter_by(user_id=current_user.id).order_by(Artikel.id.desc()).all()
        pending_count = Artikel.query.filter(Artikel.user_id==current_user.id, Artikel.status=='Pending').count()
        
    return render_template_string(ADMIN_INDEX_TEMPLATE, 
                                articles=articles, 
                                judul_situs=JUDUL_SITUS,
                                is_admin=current_user.is_admin,
                                current_user=current_user,
                                pending_count=pending_count)

@app.route('/admin/edit', defaults={'article_id': None}, methods=['GET', 'POST'])
@app.route('/admin/edit/<int:article_id>', methods=['GET', 'POST'])
@login_required
def tambah_edit_berita(article_id):
    
    artikel = Artikel.query.get(article_id)
    if article_id and (not artikel or (artikel.user_id != current_user.id and not current_user.is_admin)):
        flash("Anda tidak memiliki izin untuk mengedit artikel ini.", 'warning')
        return redirect(url_for('admin_index'))

    form = ArtikelForm(obj=artikel)

    if form.validate_on_submit():
        if artikel:
            form.populate_obj(artikel)
            artikel.tanggal = datetime.now().strftime("%d %B %Y %H:%M")
            if artikel.status == 'Disetujui':
                 artikel.status = 'Pending'
                 socketio.emit('news_delete', {'id': artikel.id})
            
            db.session.commit()
            flash('Artikel berhasil diperbarui dan menunggu persetujuan.', 'success')
        else:
            new_artikel = Artikel()
            form.populate_obj(new_artikel)
            new_artikel.user_id = current_user.id
            new_artikel.status = 'Pending'
            db.session.add(new_artikel)
            db.session.commit()
            flash('Artikel baru berhasil ditambahkan dan menunggu persetujuan.', 'success')

        return redirect(url_for('admin_index'))
        
    return render_template_string(
        ADMIN_FORM_TEMPLATE, 
        form=form,
        is_edit=article_id is not None
    )

@app.route('/admin/moderasi/<int:article_id>', methods=['GET', 'POST'])
@login_required
def moderasi_berita(article_id):
    if not current_user.is_admin:
        flash("Anda tidak memiliki izin moderator.", 'error')
        return redirect(url_for('admin_index'))

    artikel = Artikel.query.get_or_404(article_id)
    form = ModerasiForm()

    if form.validate_on_submit():
        artikel.status = form.status.data
        artikel.alasan_moderasi = form.alasan.data

        if artikel.status == 'Disetujui':
            artikel.alasan_moderasi = ''
            article_data = {
                'id': artikel.id,
                'judul': artikel.judul,
                'ringkasan': artikel.ringkasan,
                'kategori': artikel.kategori,
                'tanggal': artikel.tanggal,
                'thumbnail_url': artikel.thumbnail_url 
            }
            socketio.emit('news_update', article_data)
            flash('Artikel berhasil **Disetujui** dan dipublikasikan!', 'success')
        else:
            if artikel.status == 'Disetujui':
                socketio.emit('news_delete', {'id': artikel.id})
                
            flash(f'Artikel berhasil **Ditolak** dengan alasan: {artikel.alasan_moderasi}.', 'warning')

        db.session.commit()
        return redirect(url_for('admin_index'))
    
    return render_template_string(MODERASI_TEMPLATE, artikel=artikel, form=form)

@app.route('/admin/hapus/<int:article_id>')
@login_required
def hapus_berita(article_id):
    artikel = Artikel.query.get_or_404(article_id)
    
    if not current_user.is_admin and artikel.user_id != current_user.id:
        flash("Anda tidak memiliki izin untuk menghapus artikel ini.", 'warning')
        return redirect(url_for('admin_index'))
    
    if artikel.status == 'Disetujui':
        socketio.emit('news_delete', {'id': artikel.id})

    db.session.delete(artikel)
    db.session.commit()
    flash('Artikel berhasil dihapus.', 'info')
    return redirect(url_for('admin_index'))

# ---------------------------------------------
# 7. JALANKAN APLIKASI
# ---------------------------------------------

if __name__ == '__main__':
    print("-------------------------------------------------------")
    print("✨ Aplikasi Berita Multi-User TBJ Berjalan!")
    print(f"Halaman Utama (Live): http://127.0.0.1:5000/")
    print(f"Halaman Pendaftaran: http://127.0.0.1:5000/register")
    print(f"Admin Panel (Login): http://127.0.0.1:5000/login")
    print("\nAKUN DEMO:")
    print("Admin: superadmin/superpass123")
    print("Penulis: penuliscontoh/writer123")
    print("-------------------------------------------------------")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

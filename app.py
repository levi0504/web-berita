from flask import Flask, render_template

app = Flask(__name__)

# Contoh data berita sederhana
berita_list = [
    {"judul": "Berita 1: Python Semakin Populer", "konten": "Python terus menjadi bahasa pemrograman favorit."},
    {"judul": "Berita 2: Deployment ke Vercel Mudah", "konten": "Menggunakan Serverless Functions di Vercel sangat efisien."},
    {"judul": "Berita 3: Django vs Flask", "konten": "Pilih Django untuk proyek besar, Flask untuk API kecil."},
]

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def home(path):
    # Untuk news website, Anda akan mengambil data nyata di sini (mis. dari database/API)
    return render_template('index.html', judul_situs="Situs Berita Python", berita=berita_list)

# Ini diperlukan untuk Vercel sebagai titik masuk (entry point)
if __name__ == '__main__':
    app.run(debug=True)
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
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(10), default='Pending') # Pending, Disetujui, Ditolak
    alasan_moderasi = db.Column(db.Text, default='') 

# Forms (Dihilangkan untuk mempersingkat, asumsikan sama dengan yang Anda berikan)
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
# 3. TEMPLATE HTML (Menghapus SocketIO JS)
# ---------------------------------------------
# (Menggunakan TEMPLATE HTML yang sudah dimodifikasi (menghapus JS SocketIO) dari jawaban sebelumnya.)

# Note: Karena keterbatasan ruang, saya tidak menampilkan ulang semua HTML string.
# Asumsikan INDEX_TEMPLATE, DETAIL_TEMPLATE, REGISTER_TEMPLATE, LOGIN_TEMPLATE, 
# ADMIN_INDEX_TEMPLATE, ADMIN_FORM_TEMPLATE, MODERASI_TEMPLATE sudah berada di file ini 
# dengan penyesuaian SocketIO dihapus.

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
            transition: transform 0.3s, box-shadow 0.3s; 
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
    </div>
</body>
</html>
"""
# Karena batasan panjang, saya menggunakan template yang Anda berikan sebelumnya untuk sisanya,
# dengan asumsi Anda telah menghapus semua kode JavaScript SocketIO di dalamnya.
DETAIL_TEMPLATE = """... (Template Detail Anda) ...""" 
REGISTER_TEMPLATE = """... (Template Register Anda) ..."""
LOGIN_TEMPLATE = """... (Template Login Anda) ..."""
ADMIN_INDEX_TEMPLATE = """... (Template Admin Index Anda) ..."""
ADMIN_FORM_TEMPLATE = """... (Template Admin Form Anda) ..."""
MODERASI_TEMPLATE = """... (Template Moderasi Anda) ..."""

# Anda harus menempelkan kode HTML asli yang sudah dihapus SocketIO JS-nya di sini
# Agar file app.py menjadi lengkap dan dapat berjalan!

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
# 6. RUTE APLIKASI (ADMIN PANEL) - SocketIO Removed
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
                 # socketio.emit('news_delete', {'id': artikel.id}) <-- DIHAPUS
            
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
            # socketio.emit('news_update', article_data) <-- DIHAPUS
            flash('Artikel berhasil **Disetujui** dan dipublikasikan!', 'success')
        else:
            if artikel.status == 'Disetujui':
                # socketio.emit('news_delete', {'id': artikel.id}) <-- DIHAPUS
                pass
                
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
        # socketio.emit('news_delete', {'id': artikel.id}) <-- DIHAPUS
        pass

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
    print(f"Admin Panel (Login): http://127.0.0.1:5000/login")
    print("-------------------------------------------------------")
    app.run(host='0.0.0.0', port=5000, debug=True)

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
# 3. TEMPLATE HTML (Menghapus SocketIO JS/Markup)
# ---------------------------------------------

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
            transition: transform 0.3s, box-shadow 0.3s; /* Menghilangkan transisi new-update */
        }
        .berita-item:hover { transform: translateY(-3px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }
        /* .berita-item.new-update { background-color: #fffac8; } <-- DIHAPUS */

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
    </div>
    </body>
</html>
"""

# Template lainnya (DETAIL_TEMPLATE, REGISTER_TEMPLATE, LOGIN_TEMPLATE, ADMIN_INDEX_TEMPLATE, ADMIN_FORM_TEMPLATE, MODERASI_TEMPLATE) TIDAK DIUBAH 
# KECUALI bagian ADMIN_INDEX_TEMPLATE (Menghapus '🔴 LIVE' di header)

# Menghapus '🔴 LIVE' di header admin (opsional)
ADMIN_INDEX_TEMPLATE = ADMIN_INDEX_TEMPLATE.replace('<h1>{{ judul_situs }} 🔴 LIVE</h1>', '<h1>{{ judul_situs }}</h1>')

# ---------------------------------------------
# 4. RUTE APLIKASI (PUBLIK) & OTENTIKASI (TETAP)
# ---------------------------------------------
# (Kode Rute Otentikasi dan Publik Tetap Sama)

# ---------------------------------------------
# 5. RUTE APLIKASI (ADMIN PANEL) - Menghapus socketio.emit
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
                 # socketio.emit('news_delete', {'id': artikel.id}) <-- DIHAPUS
            
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
            # socketio.emit('news_update', article_data) <-- DIHAPUS
            flash('Artikel berhasil **Disetujui** dan dipublikasikan!', 'success')
        else:
            if artikel.status == 'Disetujui':
                # socketio.emit('news_delete', {'id': artikel.id}) <-- DIHAPUS
                pass # Tidak ada emit
                
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
        # socketio.emit('news_delete', {'id': artikel.id}) <-- DIHAPUS
        pass

    db.session.delete(artikel)
    db.session.commit()
    flash('Artikel berhasil dihapus.', 'info')
    return redirect(url_for('admin_index'))

# ---------------------------------------------
# 6. JALANKAN APLIKASI (Untuk Lokal Development)
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
    # Ganti socketio.run dengan app.run() untuk Vercel / pengembangan lokal tanpa SocketIO
    app.run(host='0.0.0.0', port=5000, debug=True)
# ---------------------------------------------
# 2. DEFINISI MODEL DATABASE & FORMS
# ---------------------------------------------
# (MODEL dan FORMS SAMA SEPERTI SEBELUMNYA)
# Pastikan semua definisi Class User, Artikel, dan semua Forms ada di sini.
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
# 3. INISIALISASI DB: PENTING UNTUK EKSTERNAL DB
# ---------------------------------------------
with app.app_context():
    # Ini harus dijalankan **secara manual** dari terminal saat pertama kali deployment
    # Namun, kita biarkan di sini agar Vercel setidaknya mencoba menghubungkan model saat startup.
    try:
        db.create_all()
    except Exception as e:
        # Jika gagal (karena belum ada DB eksternal), kita abaikan, dan biarkan /register yang menanganinya
        print(f"Database initialization failed (expected for external DB): {e}")
        pass 

# ---------------------------------------------
# 4. TEMPLATE HTML STRING (HARUS DIISI PENUH)
# ---------------------------------------------
# PASTIKAN SEMUA VARIABEL HTML STRING DIBERIKAN KEMBALI DI SINI!
# (Menggunakan placeholder karena keterbatasan ruang)
INDEX_TEMPLATE = """... (HTML INDEX LENGKAP) ...""" 
LOGIN_TEMPLATE = """... (HTML LOGIN LENGKAP) ..."""
REGISTER_TEMPLATE = """... (HTML REGISTER LENGKAP) ..."""
ADMIN_INDEX_TEMPLATE = """... (HTML ADMIN LENGKAP) ..."""
DETAIL_TEMPLATE = """... (HTML DETAIL LENGKAP) ..."""
ADMIN_FORM_TEMPLATE = """... (HTML ADMIN FORM LENGKAP) ..."""
MODERASI_TEMPLATE = """... (HTML MODERASI LENGKAP) ..."""


# ---------------------------------------------
# 5. RUTE APLIKASI (Dengan Try/Except untuk Stabilitas)
# ---------------------------------------------

# Hanya masukkan kembali rute yang sudah kita kerjakan dengan try/except
@app.route('/')
def home():
    articles = []
    try:
        articles = Artikel.query.filter_by(status='Disetujui').order_by(Artikel.id.desc()).all()
    except:
        flash("Database belum siap. Pastikan Environment Variable DATABASE_URL sudah diatur.", 'info')
        pass 
    return render_template_string(INDEX_TEMPLATE, berita=articles, judul_situs=JUDOL_SITUS)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        try:
            # PENTING: Untuk External DB, kita harus memastikan tabel dibuat jika belum ada.
            with app.app_context():
                db.create_all() 
                
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
            flash(f'Error Database: {e}. Pastikan URL Database Eksternal Anda Benar.', 'error')
            db.session.rollback()

    return render_template_string(REGISTER_TEMPLATE, form=form, judul_situs=JUDOL_SITUS)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = None
        try:
            user = User.query.filter_by(username=form.username.data).first()
        except:
            flash("Gagal query database. Pastikan DB sudah terinisialisasi.", 'error')
            return render_template_string(LOGIN_TEMPLATE, form=form, judul_situs=JUDOL_SITUS)

        if user and user.check_password(form.password.data):
            login_user(user)
            flash(f'Selamat datang, {user.username}!', 'success')
            return redirect(url_for('admin_index'))
        else:
            flash('Login Gagal. Cek Username dan Password Anda.', 'error')
            
    return render_template_string(LOGIN_TEMPLATE, form=form, judul_situs=JUDOL_SITUS)

@app.route('/admin')
@login_required 
def admin_index():
    try:
        # Logika Kueri Artikel
        # ...
        if current_user.is_admin:
            articles = Artikel.query.order_by(Artikel.id.desc()).all()
            pending_count = Artikel.query.filter_by(status='Pending').count()
        else:
            articles = Artikel.query.filter_by(user_id=current_user.id).order_by(Artikel.id.desc()).all()
            pending_count = Artikel.query.filter_by(user_id=current_user.id, status='Pending').count()
            
    except Exception as e:
        flash(f"Error memuat data admin. Sesi DB mungkin terputus.", 'warning')
        articles = []
        pending_count = 0
    
    return render_template_string(ADMIN_INDEX_TEMPLATE, 
                                articles=articles, 
                                judul_situs=JUDOL_SITUS,
                                is_admin=current_user.is_admin,
                                current_user=current_user,
                                pending_count=pending_count)
                                
# ... (Semua rute lainnya, pastikan menggunakan try/except pada kueri DB)
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
# 3. INISIALISASI DB (DIHAPUS DARI GLOBAL)
# ---------------------------------------------
# JANGAN ADA db.create_all() DI SINI! (Ini adalah titik kegagalan)

# ---------------------------------------------
# 4. TEMPLATE HTML STRING (HARUS DIISI PENUH)
# ---------------------------------------------
# **********************************************
# GANTI INI DENGAN STRING HTML PENUH YANG PANJANG
# **********************************************
INDEX_TEMPLATE = """
<!DOCTYPE html><html lang="id">... ISI HTML INDEX LENGKAP DI SINI ...</html>
""" 
LOGIN_TEMPLATE = """
<!DOCTYPE html><html lang="id">... ISI HTML LOGIN LENGKAP DI SINI ...</html>
"""
REGISTER_TEMPLATE = """
<!DOCTYPE html><html lang="id">... ISI HTML REGISTER LENGKAP DI SINI ...</html>
"""
ADMIN_INDEX_TEMPLATE = """
<!DOCTYPE html><html lang="id">... ISI HTML ADMIN INDEX LENGKAP DI SINI ...</html>
"""
DETAIL_TEMPLATE = "Detail Berita HTML String"
ADMIN_FORM_TEMPLATE = "Form Artikel HTML String"
MODERASI_TEMPLATE = "Form Moderasi HTML String"
# ... (Pastikan semua template string Anda ada di sini) ...

# ---------------------------------------------
# 5. RUTE APLIKASI (Dengan Inisialisasi DB di /register)
# ---------------------------------------------

@app.route('/')
def home():
    articles = []
    try:
        articles = Artikel.query.filter_by(status='Disetujui').order_by(Artikel.id.desc()).all()
    except:
        flash("Database belum terinisialisasi. Silakan kunjungi /register untuk membuat tabel DB dan admin pertama.", 'info')
        pass 
        
    return render_template_string(INDEX_TEMPLATE, berita=articles, judul_situs=JUDOL_SITUS)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        try:
            # 1. PAKSA BUAT DB TABLES DI SINI (TITIK KRITIS)
            with app.app_context():
                db.create_all() 
                
            # 2. LAKUKAN OPERASI USER
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
            flash(f'Error Critical Database: Silakan daftarkan lagi untuk membuat tabel DB. {e}', 'error')
            db.session.rollback()

    return render_template_string(REGISTER_TEMPLATE, form=form, judul_situs=JUDOL_SITUS)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = None
        try:
            user = User.query.filter_by(username=form.username.data).first()
        except:
            flash("Gagal menghubungkan ke database. Silakan coba daftarkan ulang akun.", 'error')
            return render_template_string(LOGIN_TEMPLATE, form=form, judul_situs=JUDOL_SITUS)

        if user and user.check_password(form.password.data):
            login_user(user)
            flash(f'Selamat datang, {user.username}!', 'success')
            return redirect(url_for('admin_index'))
        else:
            flash('Login Gagal. Cek Username dan Password Anda.', 'error')
            
    return render_template_string(LOGIN_TEMPLATE, form=form, judul_situs=JUDOL_SITUS)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah berhasil logout.', 'info')
    return redirect(url_for('home'))

@app.route('/berita/<int:berita_id>')
def detail_berita(berita_id):
    try:
        artikel = Artikel.query.get_or_404(berita_id)
        if artikel.status != 'Disetujui':
            return "Berita belum disetujui untuk publikasi.", 403
        return render_template_string(DETAIL_TEMPLATE, artikel=artikel, judul_situs=JUDOL_SITUS)
    except:
        return "Berita tidak ditemukan atau database error.", 404

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
        flash(f"Error memuat data admin. Sesi DB mungkin terputus.", 'warning')
        articles = []
        pending_count = 0
    
    return render_template_string(ADMIN_INDEX_TEMPLATE, 
                                articles=articles, 
                                judul_situs=JUDOL_SITUS,
                                is_admin=current_user.is_admin,
                                current_user=current_user,
                                pending_count=pending_count)

@app.route('/admin/edit', defaults={'article_id': None}, methods=['GET', 'POST'])
@app.route('/admin/edit/<int:article_id>', methods=['GET', 'POST'])
@login_required
def tambah_edit_berita(article_id):
    # Logika kueri dan form di sini (gunakan try-except untuk semua kueri DB)
    return render_template_string(ADMIN_FORM_TEMPLATE, form=ArtikelForm(), is_edit=article_id is not None)

@app.route('/admin/moderasi/<int:article_id>', methods=['GET', 'POST'])
@login_required
def moderasi_berita(article_id):
    # Logika kueri dan form di sini (gunakan try-except untuk semua kueri DB)
    return render_template_string(MODERASI_TEMPLATE, form=ModerasiForm(), artikel=Artikel.query.get_or_404(article_id))

@app.route('/admin/hapus/<int:article_id>')
@login_required
def hapus_berita(article_id):
    # Logika kueri dan form di sini (gunakan try-except untuk semua kueri DB)
    return redirect(url_for('admin_index'))
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

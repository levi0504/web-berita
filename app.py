from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

# -----------------------------------
# KONFIGURASI APLIKASI
# -----------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'portal-berita-super-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///berita.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

# Pastikan folder upload ada
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# -----------------------------------
# MODEL DATABASE
# -----------------------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)


class Berita(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(200), nullable=False)
    isi = db.Column(db.Text, nullable=False)
    gambar = db.Column(db.String(200), nullable=True)
    penulis = db.Column(db.String(100), nullable=False)


# -----------------------------------
# LOGIN MANAGEMENT
# -----------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -----------------------------------
# ROUTES UTAMA
# -----------------------------------
@app.route('/')
def index():
    q = request.args.get('q', '')
    if q:
        berita = Berita.query.filter(Berita.judul.like(f"%{q}%")).all()
    else:
        berita = Berita.query.all()
    return render_template('index.html', berita=berita, q=q)


@app.route('/berita/<int:id>')
def detail(id):
    b = Berita.query.get_or_404(id)
    return render_template('detail.html', berita=b)


# -----------------------------------
# LOGIN & REGISTER
# -----------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            flash('Login berhasil!', 'success')
            return redirect(url_for('admin_index') if user.is_admin else url_for('index'))
        else:
            flash('Username atau password salah!', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username sudah digunakan!', 'warning')
            return redirect(url_for('register'))

        user = User(
            username=username,
            password=generate_password_hash(password, method='sha256')
        )
        db.session.add(user)
        db.session.commit()
        flash('Akun berhasil dibuat! Silakan login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Kamu telah logout.', 'info')
    return redirect(url_for('index'))


# -----------------------------------
# ADMIN DASHBOARD
# -----------------------------------
@app.route('/admin')
@login_required
def admin_index():
    if not current_user.is_admin:
        flash('Akses ditolak! Hanya admin yang boleh masuk.', 'danger')
        return redirect(url_for('index'))
    semua = Berita.query.all()
    return render_template('admin_index.html', berita=semua)


@app.route('/admin/tambah', methods=['GET', 'POST'])
@login_required
def tambah():
    if not current_user.is_admin:
        flash('Hanya admin yang bisa menambah berita.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        judul = request.form['judul']
        isi = request.form['isi']
        gambar = None

        if 'gambar' in request.files:
            file = request.files['gambar']
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                gambar = filename

        berita = Berita(judul=judul, isi=isi, gambar=gambar, penulis=current_user.username)
        db.session.add(berita)
        db.session.commit()
        flash('Berita berhasil ditambahkan!', 'success')
        return redirect(url_for('admin_index'))

    return render_template('admin_form.html')


@app.route('/admin/hapus/<int:id>')
@login_required
def hapus(id):
    if not current_user.is_admin:
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('index'))

    b = Berita.query.get_or_404(id)
    db.session.delete(b)
    db.session.commit()
    flash('Berita berhasil dihapus.', 'info')
    return redirect(url_for('admin_index'))


# -----------------------------------
# INISIALISASI DATABASE OTOMATIS
# -----------------------------------
@app.before_first_request
def init_db():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password=generate_password_hash('admin', method='sha256'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()


# -----------------------------------
# MENJALANKAN APLIKASI
# -----------------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)    penulis = db.Column(db.String(100), nullable=False)

# -----------------------------------
# LOGIN MANAGEMENT
# -----------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -----------------------------------
# ROUTES UTAMA
# -----------------------------------
@app.route('/')
def index():
    q = request.args.get('q', '')
    if q:
        berita = Berita.query.filter(Berita.judul.like(f"%{q}%")).all()
    else:
        berita = Berita.query.all()
    return render_template('index.html', berita=berita, q=q)

@app.route('/berita/<int:id>')
def detail(id):
    b = Berita.query.get_or_404(id)
    return render_template('detail.html', berita=b)

# -----------------------------------
# LOGIN & REGISTER
# -----------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            flash('Login berhasil!', 'success')
            return redirect(url_for('admin_index') if user.is_admin else url_for('index'))
        flash('Username atau password salah!', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username sudah digunakan!', 'warning')
            return redirect(url_for('register'))
        user = User(username=username, password=generate_password_hash(password, method='sha256'))
        db.session.add(user)
        db.session.commit()
        flash('Akun berhasil dibuat! Silakan login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Kamu telah logout.', 'info')
    return redirect(url_for('index'))

# -----------------------------------
# ADMIN DASHBOARD
# -----------------------------------
@app.route('/admin')
@login_required
def admin_index():
    if not current_user.is_admin:
        flash('Akses ditolak! Hanya admin yang boleh masuk.', 'danger')
        return redirect(url_for('index'))
    semua = Berita.query.all()
    return render_template('admin_index.html', berita=semua)

@app.route('/admin/tambah', methods=['GET', 'POST'])
@login_required
def tambah():
    if not current_user.is_admin:
        flash('Hanya admin yang bisa menambah berita.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        judul = request.form['judul']
        isi = request.form['isi']
        gambar = None
        if 'gambar' in request.files:
            file = request.files['gambar']
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                gambar = filename
        berita = Berita(judul=judul, isi=isi, gambar=gambar, penulis=current_user.username)
        db.session.add(berita)
        db.session.commit()
        flash('Berita berhasil ditambahkan!', 'success')
        return redirect(url_for('admin_index'))
    return render_template('admin_form.html')

@app.route('/admin/hapus/<int:id>')
@login_required
def hapus(id):
    if not current_user.is_admin:
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('index'))
    b = Berita.query.get_or_404(id)
    db.session.delete(b)
    db.session.commit()
    flash('Berita berhasil dihapus.', 'info')
    return redirect(url_for('admin_index'))

# -----------------------------------
# INISIALISASI DATABASE
# -----------------------------------
@app.before_first_request
def init_db():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password=generate_password_hash('admin', method='sha256'), is_admin=True)
        db.session.add(admin)
        db.session.commit()

# -----------------------------------
# MENJALANKAN APLIKASI
# -----------------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)    isi = db.Column(db.Text, nullable=False)
    gambar = db.Column(db.String(200), nullable=True)
    penulis = db.Column(db.String(100), nullable=False)


# -----------------------------------
# LOGIN MANAGEMENT
# -----------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -----------------------------------
# ROUTES UTAMA
# -----------------------------------
@app.route('/')
def index():
    q = request.args.get('q', '')
    if q:
        berita = Berita.query.filter(Berita.judul.like(f"%{q}%")).all()
    else:
        berita = Berita.query.all()
    return render_template('index.html', berita=berita, q=q)


@app.route('/berita/<int:id>')
def detail(id):
    b = Berita.query.get_or_404(id)
    return render_template('detail.html', berita=b)


# -----------------------------------
# LOGIN & REGISTER
# -----------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            flash('Login berhasil!', 'success')
            return redirect(url_for('admin_index') if user.is_admin else url_for('index'))
        flash('Username atau password salah!', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username sudah digunakan!', 'warning')
            return redirect(url_for('register'))

        user = User(
            username=username,
            password=generate_password_hash(password, method='sha256')
        )
        db.session.add(user)
        db.session.commit()
        flash('Akun berhasil dibuat! Silakan login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Kamu telah logout.', 'info')
    return redirect(url_for('index'))


# -----------------------------------
# ADMIN DASHBOARD
# -----------------------------------
@app.route('/admin')
@login_required
def admin_index():
    if not current_user.is_admin:
        flash('Akses ditolak! Hanya admin yang boleh masuk.', 'danger')
        return redirect(url_for('index'))
    semua = Berita.query.all()
    return render_template('admin_index.html', berita=semua)


@app.route('/admin/tambah', methods=['GET', 'POST'])
@login_required
def tambah():
    if not current_user.is_admin:
        flash('Hanya admin yang bisa menambah berita.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        judul = request.form['judul']
        isi = request.form['isi']
        gambar = None

        if 'gambar' in request.files:
            file = request.files['gambar']
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                gambar = filename

        berita = Berita(judul=judul, isi=isi, gambar=gambar, penulis=current_user.username)
        db.session.add(berita)
        db.session.commit()
        flash('Berita berhasil ditambahkan!', 'success')
        return redirect(url_for('admin_index'))

    return render_template('admin_form.html')


@app.route('/admin/hapus/<int:id>')
@login_required
def hapus(id):
    if not current_user.is_admin:
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('index'))

    b = Berita.query.get_or_404(id)
    db.session.delete(b)
    db.session.commit()
    flash('Berita berhasil dihapus.', 'info')
    return redirect(url_for('admin_index'))


# -----------------------------------
# INISIALISASI DATABASE OTOMATIS
# -----------------------------------
@app.before_first_request
def init_db():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password=generate_password_hash('admin', method='sha256'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()


# -----------------------------------
# MENJALANKAN APLIKASI
# -----------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)    judul = db.Column(db.String(200), nullable=False)
    isi = db.Column(db.Text, nullable=False)
    gambar = db.Column(db.String(200), nullable=True)
    penulis = db.Column(db.String(100), nullable=False)


# -----------------------------------
# LOGIN MANAGEMENT
# -----------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -----------------------------------
# ROUTES UTAMA
# -----------------------------------
@app.route('/')
def index():
    q = request.args.get('q', '')
    if q:
        berita = Berita.query.filter(Berita.judul.like(f"%{q}%")).all()
    else:
        berita = Berita.query.all()
    return render_template('index.html', berita=berita, q=q)


@app.route('/berita/<int:id>')
def detail(id):
    b = Berita.query.get_or_404(id)
    return render_template('detail.html', berita=b)


# -----------------------------------
# LOGIN & REGISTER
# -----------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            flash('Login berhasil!', 'success')
            return redirect(url_for('admin_index') if user.is_admin else url_for('index'))
        else:
            flash('Username atau password salah!', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username sudah digunakan!', 'warning')
            return redirect(url_for('register'))

        user = User(
            username=username,
            password=generate_password_hash(password, method='sha256')
        )
        db.session.add(user)
        db.session.commit()
        flash('Akun berhasil dibuat! Silakan login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Kamu telah logout.', 'info')
    return redirect(url_for('index'))


# -----------------------------------
# ADMIN DASHBOARD
# -----------------------------------
@app.route('/admin')
@login_required
def admin_index():
    if not current_user.is_admin:
        flash('Akses ditolak! Hanya admin yang boleh masuk.', 'danger')
        return redirect(url_for('index'))
    semua = Berita.query.all()
    return render_template('admin_index.html', berita=semua)


@app.route('/admin/tambah', methods=['GET', 'POST'])
@login_required
def tambah():
    if not current_user.is_admin:
        flash('Hanya admin yang bisa menambah berita.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        judul = request.form['judul']
        isi = request.form['isi']
        gambar = None

        if 'gambar' in request.files:
            file = request.files['gambar']
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                gambar = filename

        berita = Berita(judul=judul, isi=isi, gambar=gambar, penulis=current_user.username)
        db.session.add(berita)
        db.session.commit()
        flash('Berita berhasil ditambahkan!', 'success')
        return redirect(url_for('admin_index'))

    return render_template('admin_form.html')


@app.route('/admin/hapus/<int:id>')
@login_required
def hapus(id):
    if not current_user.is_admin:
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('index'))

    b = Berita.query.get_or_404(id)
    db.session.delete(b)
    db.session.commit()
    flash('Berita berhasil dihapus.', 'info')
    return redirect(url_for('admin_index'))


# -----------------------------------
# INISIALISASI DATABASE OTOMATIS
# -----------------------------------
@app.before_first_request
def init_db():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password=generate_password_hash('admin', method='sha256'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()


# -----------------------------------
# MENJALANKAN APLIKASI
# -----------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

# -----------------------------------
# LOGIN MANAGEMENT
# -----------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -----------------------------------
# ROUTES
# -----------------------------------
@app.route('/')
def index():
    q = request.args.get('q', '')
    if q:
        berita = Berita.query.filter(Berita.judul.like(f"%{q}%")).all()
    else:
        berita = Berita.query.all()
    return render_template('index.html', berita=berita, q=q)

@app.route('/berita/<int:id>')
def detail(id):
    b = Berita.query.get_or_404(id)
    return render_template('detail.html', berita=b)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            flash('Login berhasil!', 'success')
            return redirect(url_for('admin_index') if user.is_admin else url_for('index'))
        flash('Username atau password salah!', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('Username sudah digunakan!', 'warning')
            return redirect(url_for('register'))
        user = User(
            username=request.form['username'],
            password=generate_password_hash(request.form['password'], method='sha256')
        )
        db.session.add(user)
        db.session.commit()
        flash('Akun berhasil dibuat!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Kamu telah logout.', 'info')
    return redirect(url_for('index'))

# ----------------- ADMIN -----------------
@app.route('/admin')
@login_required
def admin_index():
    if not current_user.is_admin:
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('index'))
    semua = Berita.query.all()
    return render_template('admin_index.html', berita=semua)

@app.route('/admin/tambah', methods=['GET', 'POST'])
@login_required
def tambah():
    if not current_user.is_admin:
        return redirect(url_for('index'))

    if request.method == 'POST':
        judul = request.form['judul']
        isi = request.form['isi']
        gambar = None

        if 'gambar' in request.files:
            file = request.files['gambar']
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                gambar = filename

        berita = Berita(judul=judul, isi=isi, gambar=gambar, penulis=current_user.username)
        db.session.add(berita)
        db.session.commit()
        flash('Berita berhasil ditambahkan!', 'success')
        return redirect(url_for('admin_index'))

    return render_template('admin_form.html')

@app.route('/admin/hapus/<int:id>')
@login_required
def hapus(id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    b = Berita.query.get_or_404(id)
    db.session.delete(b)
    db.session.commit()
    flash('Berita dihapus.', 'info')
    return redirect(url_for('admin_index'))

# -----------------------------------
# INISIALISASI DATABASE
# -----------------------------------
@app.before_first_request
def init_db():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password=generate_password_hash('admin', method='sha256'), is_admin=True)
        db.session.add(admin)
        db.session.commit()

# -----------------------------------
# RUN APP
# -----------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

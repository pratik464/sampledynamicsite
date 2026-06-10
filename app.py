from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from functools import wraps
import os, re
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import cloudinary
import cloudinary.uploader
import psycopg2
from psycopg2.extras import RealDictCursor

cloudinary.config(
    cloud_name='de8knsp2f',
    api_key='133431678326252',
    api_secret='a_nPl6jQeEvM4bP58Vw-X2RVmoQ'
)

app = Flask(__name__)
app.secret_key = 'blog_secret_key_2024'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

DATABASE_URL = 'postgresql://inkflow_db_fbvy_user:1XyFsIBO0TRekz9KkJp7nJ7r4996XJvG@dpg-d8kjhasvikkc73d4ijm0-a/inkflow_db_fbvy'

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        bio TEXT DEFAULT '',
        avatar TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS posts (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        content TEXT NOT NULL,
        excerpt TEXT DEFAULT '',
        cover_image TEXT DEFAULT '',
        category TEXT DEFAULT 'General',
        tags TEXT DEFAULT '',
        status TEXT DEFAULT 'draft',
        author_id INTEGER REFERENCES users(id),
        views INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS comments (
        id SERIAL PRIMARY KEY,
        post_id INTEGER REFERENCES posts(id),
        author_name TEXT NOT NULL,
        author_email TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    # Seed admin
    pw = generate_password_hash('admin123')
    try:
        c.execute("INSERT INTO users (username,email,password,bio) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                  ('admin','admin@blog.com',pw,'The blog administrator.'))
    except: pass
    # Seed demo posts
    try:
        c.execute("SELECT id FROM users WHERE username='admin'")
        row = c.fetchone()
        if row:
            uid = row['id']
            demos = [
                ('Getting Started with Python Flask','getting-started-python-flask',
                 '<p>Flask is a lightweight WSGI web application framework. It is designed to make getting started quick and easy, with the ability to scale up to complex applications.</p><p>In this post, we explore the core concepts of Flask — routing, templates, and the application context.</p>',
                 'A beginner-friendly introduction to Flask web development.','','Python','flask,python,web,beginner','published',uid),
                ('Top 10 CSS Tips Every Developer Should Know','top-10-css-tips',
                 '<p>CSS has evolved dramatically over the past decade. From Flexbox to Grid, CSS variables to container queries — modern CSS is more powerful than ever.</p><p>Here are ten tips that will sharpen your styling skills.</p>',
                 'Modern CSS techniques to write cleaner, smarter stylesheets.','','Design','css,frontend,tips,design','published',uid),
                ('Why Clean Code Matters in Team Projects','why-clean-code-matters',
                 '<p>Writing code that works is the baseline. Writing code that your teammates can read, maintain, and extend is the real craft.</p><p>Clean code reduces cognitive load.</p>',
                 'How readability and maintainability improve collaboration.','','General','cleancode,teamwork,bestpractices','published',uid),
            ]
            for d in demos:
                c.execute('''INSERT INTO posts (title,slug,content,excerpt,cover_image,category,tags,status,author_id)
                             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING''', d)
    except: pass
    conn.commit()
    c.close()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')

def get_current_user():
    if 'user_id' in session:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE id=%s', (session['user_id'],))
        user = c.fetchone()
        c.close(); conn.close()
        return user
    return None

def upload_image(file):
    if file and file.filename and allowed_file(file.filename):
        result = cloudinary.uploader.upload(file, folder='inkflow')
        return result.get('secure_url', '')
    return ''

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.context_processor
def inject_user():
    return {'current_user': get_current_user()}

# ── PAGE 1: HOME ──────────────────────────────────────────────────────────────
@app.route('/')
def index():
    conn = get_db(); c = conn.cursor()
    search = request.args.get('q','').strip()
    category = request.args.get('category','')
    page = int(request.args.get('page', 1))
    per_page = 6
    offset = (page - 1) * per_page

    where = "WHERE p.status='published'"
    params = []
    if search:
        where += " AND (p.title ILIKE %s OR p.content ILIKE %s)"
        params += [f'%{search}%', f'%{search}%']
    if category:
        where += " AND p.category=%s"
        params.append(category)

    c.execute(f"SELECT COUNT(*) FROM posts p {where}", params)
    total = c.fetchone()['count']
    c.execute(f"SELECT p.*, u.username as author_name FROM posts p JOIN users u ON p.author_id=u.id {where} ORDER BY p.created_at DESC LIMIT %s OFFSET %s", params + [per_page, offset])
    posts = c.fetchall()
    c.execute("SELECT DISTINCT category FROM posts WHERE status='published'")
    categories = c.fetchall()
    c.execute("SELECT p.*, u.username as author_name FROM posts p JOIN users u ON p.author_id=u.id WHERE p.status='published' ORDER BY p.views DESC LIMIT 3")
    featured = c.fetchall()
    c.close(); conn.close()

    total_pages = (total + per_page - 1) // per_page
    return render_template('index.html', posts=posts, featured=featured,
                           categories=categories, search=search, category=category,
                           page=page, total_pages=total_pages)

# ── PAGE 2: SINGLE POST ───────────────────────────────────────────────────────
@app.route('/post/<slug>')
def post_detail(slug):
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT p.*, u.username as author_name, u.bio as author_bio FROM posts p JOIN users u ON p.author_id=u.id WHERE p.slug=%s AND p.status=%s', (slug,'published'))
    post = c.fetchone()
    if not post: c.close(); conn.close(); abort(404)
    c.execute('UPDATE posts SET views=views+1 WHERE slug=%s', (slug,))
    conn.commit()
    c.execute('SELECT * FROM comments WHERE post_id=%s ORDER BY created_at DESC', (post['id'],))
    comments = c.fetchall()
    c.execute('SELECT p.*, u.username as author_name FROM posts p JOIN users u ON p.author_id=u.id WHERE p.category=%s AND p.slug!=%s AND p.status=%s LIMIT 3', (post['category'], slug, 'published'))
    related = c.fetchall()
    c.close(); conn.close()
    return render_template('post_detail.html', post=post, comments=comments, related=related)

@app.route('/post/<slug>/comment', methods=['POST'])
def add_comment(slug):
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT id FROM posts WHERE slug=%s', (slug,))
    post = c.fetchone()
    if not post: c.close(); conn.close(); abort(404)
    name = request.form.get('name','').strip()
    email = request.form.get('email','').strip()
    content = request.form.get('content','').strip()
    if name and email and content:
        c.execute('INSERT INTO comments (post_id,author_name,author_email,content) VALUES (%s,%s,%s,%s)',
                  (post['id'], name, email, content))
        conn.commit()
        flash('Comment posted!', 'success')
    c.close(); conn.close()
    return redirect(url_for('post_detail', slug=slug))

# ── PAGE 3: DASHBOARD ─────────────────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    uid = session['user_id']
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM posts WHERE author_id=%s',(uid,)); total = c.fetchone()['count']
    c.execute("SELECT COUNT(*) FROM posts WHERE author_id=%s AND status='published'",(uid,)); published = c.fetchone()['count']
    c.execute("SELECT COUNT(*) FROM posts WHERE author_id=%s AND status='draft'",(uid,)); draft = c.fetchone()['count']
    c.execute('SELECT SUM(views) FROM posts WHERE author_id=%s',(uid,)); views = c.fetchone()['sum'] or 0
    c.execute('SELECT COUNT(*) FROM comments c JOIN posts p ON c.post_id=p.id WHERE p.author_id=%s',(uid,)); comments = c.fetchone()['count']
    stats = {'total':total,'published':published,'draft':draft,'views':views,'comments':comments}
    c.execute('SELECT * FROM posts WHERE author_id=%s ORDER BY created_at DESC LIMIT 10',(uid,))
    posts = c.fetchall()
    c.execute('SELECT c.*, p.title as post_title, p.slug FROM comments c JOIN posts p ON c.post_id=p.id WHERE p.author_id=%s ORDER BY c.created_at DESC LIMIT 5',(uid,))
    recent_comments = c.fetchall()
    c.close(); conn.close()
    return render_template('dashboard.html', stats=stats, posts=posts, recent_comments=recent_comments)

# ── PAGE 4: POST EDITOR ───────────────────────────────────────────────────────
@app.route('/post/new', methods=['GET','POST'])
@login_required
def new_post():
    if request.method == 'POST':
        title = request.form.get('title','').strip()
        content = request.form.get('content','').strip()
        excerpt = request.form.get('excerpt','').strip()
        category = request.form.get('category','General')
        tags = request.form.get('tags','').strip()
        status = request.form.get('status','draft')
        cover_image = ''
        if 'cover_image' in request.files:
            cover_image = upload_image(request.files['cover_image'])
        if not title or not content:
            flash('Title and content are required.', 'danger')
            return render_template('post_editor.html', post=None, form=request.form)
        slug = slugify(title)
        conn = get_db(); c = conn.cursor()
        base_slug = slug; i = 1
        c.execute('SELECT id FROM posts WHERE slug=%s',(slug,))
        while c.fetchone():
            slug = f'{base_slug}-{i}'; i+=1
            c.execute('SELECT id FROM posts WHERE slug=%s',(slug,))
        c.execute('''INSERT INTO posts (title,slug,content,excerpt,cover_image,category,tags,status,author_id)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                  (title,slug,content,excerpt,cover_image,category,tags,status,session['user_id']))
        conn.commit(); c.close(); conn.close()
        flash('Post created!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('post_editor.html', post=None, form={})

@app.route('/post/<int:pid>/edit', methods=['GET','POST'])
@login_required
def edit_post(pid):
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT * FROM posts WHERE id=%s AND author_id=%s',(pid,session['user_id']))
    post = c.fetchone()
    if not post: c.close(); conn.close(); abort(403)
    if request.method == 'POST':
        title = request.form.get('title','').strip()
        content = request.form.get('content','').strip()
        excerpt = request.form.get('excerpt','').strip()
        category = request.form.get('category','General')
        tags = request.form.get('tags','').strip()
        status = request.form.get('status','draft')
        cover_image = post['cover_image']
        if 'cover_image' in request.files:
            new_url = upload_image(request.files['cover_image'])
            if new_url: cover_image = new_url
        now = datetime.now()
        c.execute('''UPDATE posts SET title=%s,content=%s,excerpt=%s,cover_image=%s,category=%s,tags=%s,status=%s,updated_at=%s WHERE id=%s''',
                  (title,content,excerpt,cover_image,category,tags,status,now,pid))
        conn.commit(); c.close(); conn.close()
        flash('Post updated!', 'success')
        return redirect(url_for('dashboard'))
    c.close(); conn.close()
    return render_template('post_editor.html', post=post, form=post)

@app.route('/post/<int:pid>/delete', methods=['POST'])
@login_required
def delete_post(pid):
    conn = get_db(); c = conn.cursor()
    c.execute('DELETE FROM comments WHERE post_id=%s',(pid,))
    c.execute('DELETE FROM posts WHERE id=%s AND author_id=%s',(pid,session['user_id']))
    conn.commit(); c.close(); conn.close()
    flash('Post deleted.', 'info')
    return redirect(url_for('dashboard'))

# ── PAGE 5: AUTH + PROFILE ────────────────────────────────────────────────────
@app.route('/login', methods=['GET','POST'])
def login():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        uname = request.form.get('username','').strip()
        pw = request.form.get('password','')
        conn = get_db(); c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username=%s OR email=%s',(uname,uname))
        user = c.fetchone()
        c.close(); conn.close()
        if user and check_password_hash(user['password'], pw):
            session['user_id'] = user['id']
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('auth.html', mode='login')

@app.route('/register', methods=['GET','POST'])
def register():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        uname = request.form.get('username','').strip()
        email = request.form.get('email','').strip()
        pw = request.form.get('password','')
        pw2 = request.form.get('password2','')
        if not uname or not email or not pw:
            flash('All fields are required.', 'danger')
        elif pw != pw2:
            flash('Passwords do not match.', 'danger')
        else:
            conn = get_db(); c = conn.cursor()
            try:
                c.execute('INSERT INTO users (username,email,password) VALUES (%s,%s,%s)',
                          (uname, email, generate_password_hash(pw)))
                conn.commit()
                c.execute('SELECT * FROM users WHERE username=%s',(uname,))
                user = c.fetchone()
                session['user_id'] = user['id']
                c.close(); conn.close()
                flash('Account created! Welcome.', 'success')
                return redirect(url_for('dashboard'))
            except:
                c.close(); conn.close()
                flash('Username or email already exists.', 'danger')
    return render_template('auth.html', mode='register')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id=%s',(session['user_id'],))
    user = c.fetchone()
    if request.method == 'POST':
        bio = request.form.get('bio','').strip()
        email = request.form.get('email','').strip()
        c.execute('UPDATE users SET bio=%s,email=%s WHERE id=%s',(bio,email,session['user_id']))
        conn.commit()
        flash('Profile updated!', 'success')
        c.close(); conn.close()
        return redirect(url_for('profile'))
    c.execute('SELECT * FROM posts WHERE author_id=%s ORDER BY created_at DESC',(session['user_id'],))
    posts = c.fetchall()
    c.close(); conn.close()
    return render_template('profile.html', user=user, posts=posts)

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('404.html', msg="You don't have permission to access this page."), 403

init_db()

if __name__ == '__main__':
    app.run(debug=True)

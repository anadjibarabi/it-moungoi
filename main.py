from flask import Flask , render_template , request , redirect, url_for, flash,jsonify,session
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
#from models import User
from config import Config
import os
from datetime import datetime
from flask_login import UserMixin
import json


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.secret_key = "don't tell anyone!"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
login_manager = LoginManager(app)
login_manager.login_view = 'login'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['DATA_FILE'] = 'data/images.json'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}


#app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}
#app.config['UPLOAD_FOLDER'] = 'static/uploads'

#login = LoginManager()
db = SQLAlchemy(app)
app.app_context().push()

from pathlib import Path

# Initialisation
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
Path('data').mkdir(parents=True, exist_ok=True)

recent_items = [
    {'type': 'Студент', 'name': 'Иванов И.И.', 'date': '2023-05-15'},
    {'type': 'Программа', 'name': 'Магистратура по CS', 'date': '2023-05-14'},
    {'type': 'Документ', 'name': 'Правила приема 2023', 'date': '2023-05-10'}
]


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    filetype = db.Column(db.String(10), nullable=False)  # 'image' or 'video'
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)


    def __repr__(self):
        return f"Media('{self.title}', '{self.filename}')"


class logins(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Fonction pour vérifier les extensions de fichiers
# Fonction sécurisée avec vérification
def allowed_file(filename):
    if 'ALLOWED_EXTENSIONS' not in app.config:
        raise ValueError("Configuration ALLOWED_EXTENSIONS manquante")

    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/gallery')
def gallery():
    images = Media.query.filter_by(filetype='image').all()
    videos = Media.query.filter_by(filetype='video').all()
    return render_template('user/gallery.html', images=images, videos=videos)

@app.route('/view/<int:media_id>')
def view_media(media_id):
    media = Media.query.get_or_404(media_id)
    return render_template('user/view.html', media=media)

# Routes pour l'administration


@app.route('/acount')
def acount():
    return render_template("acount.html")

@app.route("/inscription")
def inscription():
    return render_template('inscription.html')

#login
@app.route('/user', methods =["POST", "GET"])
def user():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        phone = request.form["phone"]

        Inscript = logins.query.filter_by(email=email).first()
        if Inscript:
            flash("Votre enregistrement existe!")

        else:
            if Inscript is None:
                Inscript = logins(username = username, email=email, password=password, phone=phone)
                db.session.add(Inscript)
                db.session.commit()
                flash("Vous avez enregistres avec success!")
                return redirect(url_for('login'))
            else:
                flash("Veillez enregistre !")

    inscrips = User.query.order_by(User.id).all()
    return render_template("admin/login.html", inscrips=inscrips)


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        login = logins.query.filter_by(email=email, password=password).first()

        if login is not None and request.form['password']:
            return redirect("admin_user")
        elif login != email:
            flash("Votre email n'exit pas veillez enregistrer")
        elif login != password:
            flash("Mote de passe incorrect!")
        else:
            flash("le mote de pase")
    return render_template("admin/user.html")




#return render_template("inscription.html")
@app.route("/admin_user")
def admin_user():
    users = logins.query.order_by(logins.id.desc()).all()
    return render_template("admin/data.html", users = users)


@app.route('/delete/<id>/', methods = ['GET', 'POST'])
def delete(id):
    my_data = logins.query.get(id)
    db.session.delete(my_data)
    db.session.commit()
    flash("Employee Deleted Successfully")
    return redirect(url_for('admin_user'))
#update user with new password and

#@app.errorhandler(404)
#def invalid_route(e):
    return redirect("/update")

@app.route('/update', methods=['POST', 'GET'])
def update(id):
    if request.method == 'POST':

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        phone = request.form["phone"]
        updates = logins(username=username , email=email , password=password, phone=phone)
        try:
            db.session.add(updates)
            db.session.commit()
            flash("Employee Updated Successfully")
        except:
            flash("Error updating ")

        my_data = logins.query.get(id)
        return redirect(url_for('admin_user'), y_data=my_data)

@app.route('/formation')
def formation():
    return render_template('formation.html')
@app.route('/cours')
def cours():
    return render_template('cours.html')

@app.route('/doscier')
def doscier():
    return render_template('doscier.html')

@app.route('/catalogue')
def catalogue():
    return render_template('catalogue.html')

@app.route('/articles')
def articles():
    return render_template('articles.html')

@app.route('/admins',methods=['GET', 'POST'])
#@login_required
def admin():
    if request.method == 'POST':
        data_type = request.form.get('data_type')

        # Process form data based on type
        if data_type == 'student':
            full_name = request.form.get('full_name')
            email = request.form.get('email')
            program = request.form.get('program')
            # Save to database or process data

        elif data_type == 'program':
            program_name = request.form.get('program_name')
            description = request.form.get('description')
            duration = request.form.get('duration')
            # Save to database or process data

        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Add to recent items (mock)
        recent_items.insert(0, {
            'type': 'Студент' if data_type == 'student' else 'Программа' if data_type == 'program' else data_type,
            'name': request.form.get('full_name') or request.form.get('program_name') or 'Новый элемент',
            'date': datetime.now().strftime('%Y-%m-%d')
        })

        return redirect(url_for('admin'))

    return render_template('admin/admin.html', recent_items=recent_items)



@app.route('/dashboard')
def dashboard():
    return render_template('admin/dashboard.html')

#admin_data
@app.route('/data')
def data():
    return render_template('admin/data.html')


#-------------------------------------------------------

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def load_images():
    try:
        with open(app.config['DATA_FILE'], 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_images(images):
    with open(app.config['DATA_FILE'], 'w') as f:
        json.dump(images, f)

# Routes
@app.route('/user_page')
def user_page():
    images = load_images()
    return render_template('users.html', images=images)

@app.route('/admin/upload', methods=['GET', 'POST'])
#@login_required
def admin_page():
    if request.method == 'POST':
        # Vérification du fichier
        if 'file' not in request.files:
            flash('Aucun fichier sélectionné', 'error')
            return redirect(request.url)

        file = request.files['file']
        title = request.form.get('title', '').strip()

        if file.filename == '':
            flash('Aucun fichier sélectionné', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Ajout aux métadonnées
            images = load_images()
            images.append({
                'filename': filename,
                'title': title if title else filename,
                'path': f"uploads/{filename}"
            })
            save_images(images)

            flash(f'Image "{filename}" uploadée avec succès!', 'success')
            return redirect(url_for('admin_page'))

    return render_template('/admin/upload.html')


@app.route('/delete/<filename>', methods=['POST'])
def delete_image(filename):
    images = load_images()
    updated_images = [img for img in images if img['filename'] != filename]

    if len(updated_images) != len(images):  # Si l'image existait
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            save_images(updated_images)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    return jsonify({'success': False, 'error': 'Image non trouvée'}), 404

def allowed_video(file):
    if file.content_length > app.config['MAX_VIDEO_SIZE']:
        raise ValueError("Taille maximale dépassée (500 Mo max)")
    return ('.' in file.filename and
            file.filename.rsplit('.', 1)[1].lower() in app.config['VIDEO_ALLOWED_EXTENSIONS'])

@app.route('/admin/dashborad_mediat', methods=['GET', 'POST'])
#@login_required
def admin_upload():
    if request.method == 'POST':
        media_type = request.form.get('media_type')

        try:
            if media_type == 'image':
                file = request.files['image_file']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'images', filename))
                    flash('Image uploadée avec succès!', 'success')

            elif media_type == 'video':
                file = request.files['video_file']
                if file and allowed_video(file):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'videos', filename))
                    flash('Vidéo uploadée avec succès!', 'success')

            return redirect(url_for('admin_dashboard'))

        except Exception as e:
            flash(f'Erreur: {str(e)}', 'danger')

    return render_template('admin/dashboard_mediat.html')




# Fonctions utilitaires


def get_stats():
    images = load_images()
    total_size = sum(os.path.getsize(os.path.join(app.config['UPLOAD_FOLDER'], img['filename']))
                     for img in images) / (1024 * 1024)  # Mo
    return {
        'total_images': len(images),
        'total_size': round(total_size, 2),
        'last_upload': max([img['upload_date'] for img in images], default='Aucune')
    }


# Authentification
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if (request.form['username'] == app.config['ADMIN_USERNAME'] and
                request.form['password'] == app.config['ADMIN_PASSWORD']):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        flash('Identifiants incorrects', 'danger')
    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('user_page'))


# Dashboard Admin
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    stats = get_stats()
    images = load_images()
    return render_template('admin/dashboard_mediat.html',
                           stats=stats,
                           images=images,
                           now=datetime.now().strftime('%Y-%m-%d %H:%M'))


if __name__ == '__main__':
    app.run(debug=True , host= '0.0.0.0')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

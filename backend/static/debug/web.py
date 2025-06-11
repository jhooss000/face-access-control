from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from backend.forms import RegisterForm, LoginForm
from backend.database import db, User
import os
from flask import current_app
from werkzeug.utils import secure_filename
from backend.forms import UploadFaceForm
from backend.database import Face
from backend.forms import UploadFaceForm, FaceVerificationForm
import face_recognition

web_routes = Blueprint('web_routes', __name__)

@web_routes.route('/')
@login_required
def index():
    return render_template("index.html", user=current_user)

@web_routes.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Usuario registrado con éxito", "success")
        return redirect(url_for('web_routes.login'))
    return render_template("register.html", form=form)

@web_routes.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("Inicio de sesión exitoso", "success")
            return redirect(url_for('web_routes.index'))
        else:
            flash("Credenciales incorrectas", "danger")
    return render_template("login.html", form=form)

@web_routes.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada", "info")
    return redirect(url_for('web_routes.login'))

@web_routes.route("/faces", methods=["GET", "POST"])
@login_required
def manage_faces():
    upload_form = UploadFaceForm()
    verify_form = FaceVerificationForm()
    match_name = None
    no_match = False

    # 🧩 Subir nuevo rostro
    if upload_form.submit.data and upload_form.validate_on_submit():
        image = upload_form.image.data
        person_name = upload_form.person_name.data.strip()
        filename = secure_filename(f"{person_name}_{image.filename}")
        folder = os.path.join("backend", "static", "registered_faces")
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, filename)
        image.save(path)

        face = Face(filename=filename, person_name=person_name, uploaded_by=current_user.id)
        db.session.add(face)
        db.session.commit()
        flash("Rostro subido correctamente", "success")
        return redirect(url_for("web_routes.manage_faces"))

    # 🔍 Verificar rostro cargado
    if verify_form.submit.data and verify_form.validate_on_submit():
        uploaded_file = verify_form.image.data
        uploaded_path = os.path.join("backend", "static", "temp_verify.jpg")
        uploaded_file.save(uploaded_path)

        try:
            unknown_image = face_recognition.load_image_file(uploaded_path)
            unknown_encodings = face_recognition.face_encodings(unknown_image)

            if not unknown_encodings:
                flash("⚠️ No se detectó ningún rostro en la imagen cargada.", "warning")
                return redirect(url_for("web_routes.manage_faces"))

            unknown_encoding = unknown_encodings[0]

            # ⚡ Precargar encodings
            known_encodings = []
            known_names = []

            for face in Face.query.all():
                image_path = os.path.join("backend", "static", "registered_faces", face.filename)
                known_image = face_recognition.load_image_file(image_path)
                encodings = face_recognition.face_encodings(known_image)
                if encodings:
                    known_encodings.append(encodings[0])
                    known_names.append(face.person_name)

            if not known_encodings:
                flash("⚠️ No hay rostros registrados para comparar.", "warning")
                return redirect(url_for("web_routes.manage_faces"))

            # ✅ Comparar usando tolerancia ajustada
            results = face_recognition.compare_faces(known_encodings, unknown_encoding, tolerance=0.45)
            from backend.utils.telegram_notify import send_telegram_message

            if True in results:
                match_index = results.index(True)
                match_name = known_names[match_index]
                send_telegram_message(f"✅ *Acceso aprobado para:* {match_name}")
            else:
                no_match = True
                send_telegram_message("❌ *Intento fallido:* rostro no reconocido")

            # 🧼 Eliminar imagen temporal
            if os.path.exists(uploaded_path):
                os.remove(uploaded_path)

        except Exception as e:
            flash(f"❌ Error al procesar imagen: {e}", "danger")

    # 📂 Listar rostros del usuario actual
    faces = Face.query.filter_by(uploaded_by=current_user.id).all()

    return render_template("faces.html",
        form=upload_form,
        verify_form=verify_form,
        match_name=match_name,
        no_match=no_match,
        faces=faces
    )

@web_routes.route("/faces/delete/<int:face_id>", methods=["POST"])
@login_required
def delete_face(face_id):
    face = Face.query.get_or_404(face_id)

    if face.uploaded_by != current_user.id:
        flash("No tienes permiso para eliminar este rostro.", "danger")
        return redirect(url_for("web_routes.manage_faces"))

    # Eliminar imagen física
    img_path = os.path.join("backend", "static", "registered_faces", face.filename)
    if os.path.exists(img_path):
        os.remove(img_path)

    # Eliminar registro de base de datos
    db.session.delete(face)
    db.session.commit()

    flash(f"Rostro '{face.person_name}' eliminado correctamente.", "success")
    return redirect(url_for("web_routes.manage_faces"))

@web_routes.route("/api/verify-face", methods=["POST"])
def verify_face_from_esp32():
    import numpy as np
    import cv2
    import os
    import datetime
    from backend.database import Face
    import face_recognition

    if not request.data:
        return {"status": "error", "message": "No se recibió imagen"}, 400

    try:
        # Crear carpeta de debug si no existe
        debug_dir = os.path.join("backend", "static", "debug")
        os.makedirs(debug_dir, exist_ok=True)

        # Guardar imagen temporal para depuración
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        img_debug_path = os.path.join(debug_dir, f"esp32_{timestamp}.jpg")

        with open(img_debug_path, "wb") as f:
            f.write(request.data)

        print(f"📁 Imagen guardada: {img_debug_path}")

        # Leer imagen en OpenCV
        img_array = np.frombuffer(request.data, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            return {"status": "error", "message": "La imagen no pudo decodificarse"}, 400

    except Exception as e:
        return {"status": "error", "message": f"Error procesando imagen: {e}"}, 400

    try:
        encodings = face_recognition.face_encodings(img)
        if not encodings:
            return {"status": "error", "message": "No se detectó rostro"}, 400

        unknown_encoding = encodings[0]

        # Cargar rostros conocidos
        known_encodings = []
        known_names = []
        face_folder = os.path.join("backend", "static", "registered_faces")

        for face in Face.query.all():
            path = os.path.join(face_folder, face.filename)
            try:
                known_img = face_recognition.load_image_file(path)
                k = face_recognition.face_encodings(known_img)
                if k:
                    known_encodings.append(k[0])
                    known_names.append(face.person_name)
            except Exception as err:
                print(f"⚠️ Error al procesar {path}: {err}")
                continue

        if not known_encodings:
            return {"status": "error", "message": "No hay rostros registrados"}, 500

        # Comparar
        matches = face_recognition.compare_faces(known_encodings, unknown_encoding, tolerance=0.45)

        if True in matches:
            idx = matches.index(True)
            return {"status": "success", "match": known_names[idx]}, 200
        else:
            return {"status": "fail", "match": None}, 200

    except Exception as e:
        return {"status": "error", "message": f"Error interno: {e}"}, 500

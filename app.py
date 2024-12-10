import logging

import google.api_core.exceptions
from flask import Flask, render_template, request, jsonify, redirect, flash, url_for, send_file, Response
from google.cloud.firestore_v1 import FieldFilter
from werkzeug.utils import secure_filename
from firebase_admin import credentials, initialize_app, firestore, storage

# Allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "a0497e3487139ccc64e8d7941904c6bd656fe97ebe2a7d827efa8a030236797a"

# Initialize Firebase
cred = credentials.Certificate("firebase_credentials.json")
initialize_app(cred, {
    "storageBucket": "radio-presenter-520a3.firebasestorage.app"
})
db = firestore.client()
bucket = storage.bucket()


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("flask-app")


@app.before_request
def log_request_info():
    logger.info(f"{request.method} {request.path} - From: {request.remote_addr}")


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        show_name = request.form.get("show_name")
        description = request.form.get("description")

        if 'image' not in request.files:
            flash('No images, please add show images.', 'error')
            return redirect(request.url)

        image_file = request.files.get("image")

        if image_file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if image_file and allowed_file(image_file.filename):
            # Save image to Firebase Storage
            filename = secure_filename(image_file.filename)
            blob = bucket.blob(f"images/{filename}")
            blob.upload_from_file(image_file)
            image_url = blob.public_url

            # Save show to Firestore
            new_show = {
                "title": show_name,
                "description": description,
                "image_url": image_url,
                "created_at": firestore.SERVER_TIMESTAMP
            }
            db.collection("shows").add(new_show)
            flash("New Show Added", 'success')

    # Fetch all shows from Firestore
    shows = db.collection("shows").order_by("created_at", direction=firestore.Query.DESCENDING).stream()
    shows = [{"id": show.id, **show.to_dict()} for show in shows]
    return render_template('index.html', shows=shows)


@app.route('/edit/<show_id>', methods=['GET', 'POST'])
def edit_show(show_id):
    show_ref = db.collection("shows").document(show_id)
    show = show_ref.get().to_dict()

    if not show:
        flash(f"No Show exists with that ID: {show_id}", 'error')
        return redirect(url_for("index"))

    if request.method == 'POST':
        title = request.form.get("title")
        description = request.form.get("description")

        updates = {"title": title, "description": description}

        if 'image' in request.files:
            image_file = request.files.get("image")
            if image_file.filename != '':
                if allowed_file(image_file.filename):

                    # Delete old image
                    if "image_url" in show:
                        print(show["image_url"])
                        old_blob = bucket.blob(f"images/{show['image_url'].split('/')[-1]}")
                        try:
                            old_blob.delete()
                        except google.api_core.exceptions.NotFound:
                            pass

                    # Upload new image
                    filename = secure_filename(image_file.filename)
                    blob = bucket.blob(f"images/{filename}")
                    blob.upload_from_file(image_file)
                    image_url = blob.public_url

                    updates["image_url"] = image_url

        show_ref.update(updates)
        flash('Show updated successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('edit_show.html', show={"id": show_id, **show})


@app.route('/delete_show/<show_id>', methods=['POST'])
def delete_show(show_id):
    show_ref = db.collection("shows").document(show_id)
    show = show_ref.get().to_dict()

    if not show:
        flash(f"No Show with the ID: {show_id}", 'error')
        return redirect(url_for('index'))

    # Delete image from Firebase Storage
    if "image_url" in show:
        blob = bucket.blob(f"images/{show['image_url'].split('/')[-1]}")
        try:
            blob.delete()
        except google.api_core.exceptions.NotFound:
            show_ref.delete()

        finally:
            flash('Show deleted successfully!', 'success')
            return redirect(url_for('index'))
    # Delete document from Firestore
    show_ref.delete()
    flash('Show deleted successfully!', 'success')
    return redirect(url_for('index'))


@app.route("/presenter", methods=["GET"])
def presenter():
    current_track = request.args.get("now_playing")
    current_show = request.args.get("artist")
    print(current_show)
    if current_track and current_show:
        show_ref = db.collection("shows")
        query = show_ref.where(filter=FieldFilter("title", "==", current_show))
        existing_show = query.get()
        new_show = {
            "track_title": current_track,
            "show": existing_show[0].to_dict().get("title") if existing_show else None,
            "show_id": existing_show[0].id if existing_show else None,
            "artist": current_show,
            "created_at": firestore.SERVER_TIMESTAMP
        }
        db.collection("show_log").add(new_show)
        return jsonify({})

    show_ref = db.collection("show_log")
    query = show_ref.order_by("created_at", direction=firestore.Query.DESCENDING).limit(1)
    blob = None
    try:
        latest_show_log = query.get()
        print(latest_show_log[0].to_dict())
        current_presenter = {"id": latest_show_log[0].id, **latest_show_log[0].to_dict()}
        show_ref = db.collection("shows").document(current_presenter.get("show_id"))
        show = show_ref.get().to_dict()
        blob = bucket.blob(f"images/{show['image_url'].split('/')[-1]}")

    except:
        show_ref = db.collection("shows").where(filter=FieldFilter("title", "==", "Default")).get()
        if show_ref:
            default_show = show_ref[0].to_dict()
            blob = bucket.blob(f"images/{default_show['image_url'].split('/')[-1]}")

    content_type = None
    try:
        content_type = blob.content_type
    except:
        pass
    file = blob.download_as_string()
    print(type(file))
    return Response(file, mimetype=content_type)


@app.route("/logs", methods=["GET"])
def show_logs():
    # Fetch logs from Firestore
    logs_ref = db.collection('show_log')
    logs = logs_ref.stream()
    # Format logs as a list of dictionaries
    logs_list = []
    for log in logs:
        log_data = log.to_dict()
        log_data['id'] = log.id  # Include document ID
        show = db.collection("shows").document(log_data.get("show_id")).get()
        show_data = show.to_dict()
        if show_data:
            log_data["show_title"] = show_data.get("title")
            log_data["show_description"] = show_data.get("description")
        logs_list.append(log_data)
    return render_template("logs.html", logs=logs_list)


@app.route("/delete_logs", methods=["POST"])
def delete_all_show_logs():
    logs_ref = db.collection('show_log')
    logs = logs_ref.list_documents()

    for log in logs:
        log.delete()

    return redirect(url_for("show_logs"))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

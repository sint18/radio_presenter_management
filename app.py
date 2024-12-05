import os
import pathlib
import uuid

from flask import Flask, render_template, request, jsonify, redirect, flash, url_for
from werkzeug.utils import secure_filename
from pathlib import Path
from models import db
from models import Presenter, Show
from sqlalchemy import select, func
from flask import send_from_directory

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
UPLOAD_FOLDER = Path("./static/images")

app = Flask(__name__)
app.secret_key = "a0497e3487139ccc64e8d7941904c6bd656fe97ebe2a7d827efa8a030236797a"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///presenter.db'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db.init_app(app)


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


with app.app_context():
    db.create_all()


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
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # return redirect(url_for('download_file', name=filename))
            # return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

            new_show = Show(title=show_name, image_url=image_file.filename, description=description)
            db.session.add(new_show)
            db.session.commit()
            flash("New Show Added", 'success')
    shows = db.session.scalars(select(Show)).all()
    return render_template('index.html', shows=shows)


@app.route('/edit/<show_id>', methods=['GET', 'POST'])
def edit_show(show_id):
    show = db.session.scalars(select(Show).where(Show.id == uuid.UUID(show_id))).first()
    if not show:
        flash(f"No Show exists with that ID:{show_id}", 'error')
        return url_for("index")

    if request.method == 'POST':
        show.title = request.form.get("title")
        show.description = request.form.get("description")

        if 'image' in request.files:
            image_file = request.files.get("image")
            if image_file.filename != '':
                if image_file and allowed_file(image_file.filename):
                    filename = secure_filename(image_file.filename)
                    image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    if pathlib.Path(app.config["UPLOAD_FOLDER"], show.image_url).exists():
                        pathlib.Path(app.config["UPLOAD_FOLDER"], show.image_url).unlink()
                    show.image_url = filename

        db.session.commit()
        flash('Show updated successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('edit_show.html', show=show)


@app.route('/delete_show/<show_id>', methods=['POST'])
def delete_show(show_id):
    print(show_id)
    show = db.session.scalars(select(Show).where(Show.id == uuid.UUID(show_id))).first()

    if not show:
        flash(f"No Show with the Id:{show_id}", 'error')
        return redirect(url_for('index'))

    if pathlib.Path(app.config["UPLOAD_FOLDER"], show.image_url).exists():
        pathlib.Path(app.config["UPLOAD_FOLDER"], show.image_url).unlink()

    db.session.delete(show)
    db.session.commit()

    flash('Show deleted successfully!', 'success')
    return redirect(url_for('index'))


@app.route('/delete_logs', methods=['POST'])
def delete_logs():

    db.session.query(Presenter).delete()
    db.session.commit()

    return redirect(url_for('view_logs'))


@app.route("/presenter", methods=["GET"])
def presenter():
    current_track = request.args.get("now_playing")
    current_show = request.args.get("artist")
    print(current_show)
    if current_track and current_show:
        print(current_show, current_track)
        show = db.session.scalars(
            select(Show).where(func.lower(Show.title) == current_show.lower()).order_by(Show.updated_at.desc())).first()
        print(show)
        new_presenter = Presenter(track_title=current_track, show_id=show.id if show else None)
        db.session.add(new_presenter)
        db.session.commit()

        return jsonify({})

    # stmt = select(Show).where(Show.title == current_show).order_by(Show.updated_at.desc())
    current_presenter = db.session.scalars(select(Presenter).order_by(Presenter.created_at.desc())).first()

    if current_presenter and current_presenter.show:
        print(f"Current Presenter : {current_presenter.show.title}")
        if pathlib.Path(app.config["UPLOAD_FOLDER"]).joinpath(current_presenter.show.image_url).exists():
            return send_from_directory(app.config["UPLOAD_FOLDER"], current_presenter.show.image_url)
        else:
            return send_from_directory(app.config["UPLOAD_FOLDER"], "image.webp")
    else:
        # Default Image
        # print(f"Current Presenter : {current_presenter.track_title}")
        return send_from_directory(app.config["UPLOAD_FOLDER"], "image.webp")


@app.route('/logs', methods=["GET", "POST"])
def view_logs():
    presenters = db.session.scalars(select(Presenter).order_by(Presenter.created_at.desc()))
    return render_template("logs.html", logs=presenters)


@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

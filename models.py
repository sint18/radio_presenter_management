import uuid
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import ForeignKey
from sqlalchemy import Uuid, String
from flask_sqlalchemy import SQLAlchemy
from typing import List

db = SQLAlchemy()


class Show(db.Model):
    id = db.Column(Uuid, primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(80), nullable=False)
    image_url = db.Column(db.String(255))
    description = db.Column(String, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    presenters: Mapped[List["Presenter"]] = relationship(back_populates="show")

    def __repr__(self):
        return '<Show %r>' % self.title


class Presenter(db.Model):
    id = db.Column(Uuid, primary_key=True, default=uuid.uuid4)
    track_title = db.Column(db.String(255), nullable=False)
    artist = db.Column(db.String(255), nullable=True)
    show_id = mapped_column(ForeignKey("show.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.now())

    show: Mapped["Show"] = relationship(back_populates="presenters")

    def __repr__(self):
        return '<Presenter %r>' % self.track_title

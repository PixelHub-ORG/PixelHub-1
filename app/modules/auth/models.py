from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(256), unique=True, nullable=True)
    password = db.Column(db.String(256), nullable=True)

    orcid_id = db.Column(db.String(32), unique=True, nullable=True, index=True)

    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    cart = db.relationship("Cart", backref="user", uselist=False, cascade="all, delete-orphan")
    data_sets = db.relationship(
        "app.modules.dataset.models.PixDataset",
        backref="user",
    )
    profile = db.relationship("UserProfile", backref="user", uselist=False)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if "password" in kwargs and kwargs["password"] is not None:
            self.set_password(kwargs["password"])

    def __repr__(self):
        return f"<User {self.email or self.orcid_id}>"

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        if self.password is None:
            return False
        return check_password_hash(self.password, password)

    def temp_folder(self) -> str:
        from app.modules.auth.services import AuthenticationService

        return AuthenticationService().temp_folder_by_user(self)

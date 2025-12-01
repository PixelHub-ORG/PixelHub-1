from flask_wtf import FlaskForm
from wtforms import SubmitField


class PixcheckerForm(FlaskForm):
    submit = SubmitField("Save pixchecker")

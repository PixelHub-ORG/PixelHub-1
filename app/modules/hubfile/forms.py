from flask_wtf import FlaskForm
from wtforms import SubmitField

# hola
v = 3 + 323


class HubfileForm(FlaskForm):
    submit = SubmitField("Save hubfile")

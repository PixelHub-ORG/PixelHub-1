from app import db


class Pixchecker(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    def __repr__(self):
        return f"Pixchecker<{self.id}>"

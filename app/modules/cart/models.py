from app import db


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    items = db.relationship("CartItem", backref="cart", cascade="all, delete-orphan")


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("cart.id"), nullable=False)
    file_model_id = db.Column(db.Integer, db.ForeignKey("file_model.id"), nullable=False)

from app.modules.auth.models import User
from app.modules.cart.models import Cart
from core.seeders.BaseSeeder import BaseSeeder


class CartSeeder(BaseSeeder):

    priority = 2

    def run(self):

        user1 = User.query.filter_by(email="user1@example.com").first()
        user2 = User.query.filter_by(email="user2@example.com").first()

        new_carts = []

        if user1 and not user1.cart:
            new_carts.append(Cart(user_id=user1.id))

        if user2 and not user2.cart:
            new_carts.append(Cart(user_id=user2.id))

        if new_carts:
            self.seed(new_carts)

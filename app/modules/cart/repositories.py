from app.modules.cart.models import Cart, CartItem
from core.repositories.BaseRepository import BaseRepository


class CartRepository(BaseRepository):
    def __init__(self):
        super().__init__(Cart)

    def get_cart_by_id(self, cart_id: int):
        return self.model.query.filter_by(id=cart_id).first()

    def get_cart_by_user_id(self, user_id: int) -> Cart | None:
        return self.model.query.filter_by(user_id=user_id).first()

    def get_cart_items(self, user_id: int):
        cart = self.get_cart_by_user_id(user_id)
        if cart:
            return cart.items
        return []

    def clear_cart(self, user_id: int) -> bool:
        cart = self.get_cart_by_user_id(user_id)
        if cart:
            for item in list(cart.items):
                self.session.delete(item)
            self.session.commit()
            return True
        return False


class CartItemRepository(BaseRepository):
    def __init__(self):
        super().__init__(CartItem)

    def find_by_cart_and_model(self, cart_id: int, file_model_id: int) -> CartItem | None:
        return self.model.query.filter_by(cart_id=cart_id, file_model_id=file_model_id).first()

    def add_item(self, cart_id: int, item_id: int) -> CartItem:
        new_item = CartItem(cart_id=cart_id, file_model_id=item_id)
        self.session.add(new_item)
        self.session.commit()
        return new_item

    def remove_item(self, cart_id: int, item_id: int) -> bool:
        item = self.find_by_cart_and_model(cart_id, item_id)
        if item:
            self.session.delete(item)
            self.session.commit()
            return True
        return False

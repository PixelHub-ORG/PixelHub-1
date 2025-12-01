from app import db
from app.modules.auth.services import AuthenticationService
from app.modules.cart.repositories import CartItemRepository, CartRepository
from app.modules.dataset.services import DataSetService
from app.modules.filemodel.models import FileModel
from app.modules.hubfile.models import Hubfile
from core.services.BaseService import BaseService


class CartService(BaseService):
    def __init__(self):
        self.cart_repository = CartRepository()
        self.cart_item_repository = CartItemRepository()
        self.dataset_service = DataSetService()
        self.auth_service = AuthenticationService()
        super().__init__(self.cart_repository)

    def add_to_cart(self, user_id: int, item_id: int):
        cart = self.cart_repository.get_cart_by_user_id(user_id)
        if not cart:
            return {"message": "Cart not found."}, 404
        existing_item = self.cart_item_repository.find_by_cart_and_model(cart.id, item_id)
        if existing_item:
            return {"message": "Item already in cart."}, 400
        self.cart_item_repository.add_item(cart.id, item_id)
        return {"message": "Item added to cart."}, 200

    def view_cart(self, user_id: int):
        cart_items = self.cart_repository.get_cart_items(user_id)
        return [{"cart_item_id": item.id, "file_model_id": item.file_model_id} for item in cart_items]

    def delete_from_cart(self, user_id: int, item_id: int = None):
        cart = self.cart_repository.get_cart_by_user_id(user_id)
        if not cart:
            return {"message": "Cart not found."}, 404
        if item_id is None:
            self.cart_repository.clear_cart(user_id)
            return {"message": "Cart cleared."}, 200
        else:
            removed = self.cart_item_repository.remove_item(cart.id, item_id)
            if not removed:
                return {"message": "Item not found in cart."}, 404
        return {"message": "Item removed from cart."}, 200

    def create_dataset(self, user_id, form):
        cart = self.cart_repository.get_cart_by_user_id(user_id)
        if not cart or not cart.items:
            return {"message": "Cart is empty."}, 400

        user = self.auth_service.get_authenticated_user()
        if not user or user.id != user_id:
            return {"message": "User not authenticated."}, 401

        form.file_models = []

        dataset = self.dataset_service.create_from_form(form, user)
        if not dataset:
            return {"message": "Error creating dataset."}, 500

        for item in cart.items:
            orig_fm = item.file_model

            new_fm = FileModel(
                data_set_id=dataset.id,
                fm_meta_data_id=orig_fm.fm_meta_data_id,
            )
            db.session.add(new_fm)

            for file in orig_fm.files:
                clone_data = {
                    col.name: getattr(file, col.name)
                    for col in file.__table__.columns
                    if col.name not in ("id", "file_model_id")
                }
                new_file = Hubfile(**clone_data)
                new_file.file_model = new_fm
                db.session.add(new_file)

        db.session.commit()

        self.cart_repository.clear_cart(user_id)

        return {
            "message": "DataSet created successfully.",
            "dataset_id": dataset.id,
        }, 201

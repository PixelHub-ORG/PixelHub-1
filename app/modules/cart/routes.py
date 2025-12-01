import os
import tempfile
import zipfile
from datetime import datetime

from flask import jsonify, render_template, request, send_from_directory
from flask_login import current_user, login_required

from app.modules.cart import cart_bp
from app.modules.cart.forms import CartCreateDatasetForm
from app.modules.cart.services import CartService
from app.modules.filemodel.services import FilemodelService

cart_service = CartService()
fm_service = FilemodelService()


@cart_bp.route("/user/cart/view_page", methods=["GET"])
@login_required
def view_cart_page():
    cart_items = cart_service.view_cart(current_user.id)
    models = []

    for item in cart_items:
        file_model = fm_service.get_by_id(item["file_model_id"])
        if file_model:
            fm_meta = file_model.fm_meta_data
            models.append(
                {
                    "id": file_model.id,
                    "name": fm_meta.title if fm_meta else "No title",
                    "description": fm_meta.description if fm_meta else "",
                    "authors": fm_meta.authors if fm_meta else [],
                }
            )

    return render_template("cart/view_cart.html", models=models)


@cart_bp.route("/user/cart/count", methods=["GET"])
@login_required
def cart_count():
    cart_items = cart_service.view_cart(current_user.id)
    return jsonify({"count": len(cart_items)})


@cart_bp.route("/filemodel/cart/add", methods=["POST"])
@login_required
def add_to_cart():
    data = request.get_json()
    item_id = data.get("item_id")
    if not item_id:
        return jsonify({"message": "No item_id provided"}), 400

    result, status_code = cart_service.add_to_cart(current_user.id, item_id)
    return jsonify(result), status_code


@cart_bp.route("/user/cart/delete", methods=["POST"])
@login_required
def delete_from_cart():
    data = request.get_json()
    item_id = data.get("item_id")
    return jsonify(cart_service.delete_from_cart(current_user.id, item_id))


@cart_bp.route("/user/cart/create", methods=["GET", "POST"])
@login_required
def create_dataset():
    form = CartCreateDatasetForm()
    models = []

    if request.method == "POST":
        if not form.validate_on_submit():
            return jsonify({"message": form.errors}), 400

        result, status_code = cart_service.create_dataset(current_user.id, form)
        return jsonify(result), status_code

    cart_items = cart_service.view_cart(current_user.id)
    for item in cart_items:
        file_model = fm_service.get_by_id(item["file_model_id"])
        if file_model:
            fm_meta = file_model.fm_meta_data
            models.append(
                {
                    "id": file_model.id,
                    "name": fm_meta.title if fm_meta else "No title",
                    "description": fm_meta.description if fm_meta else "",
                    "authors": fm_meta.authors if fm_meta else [],
                }
            )
    return render_template("cart/create_dataset.html", form=form, models=models)


@cart_bp.route("/user/cart/download", methods=["GET"])
@login_required
def download_cart():
    cart_items = cart_service.view_cart(current_user.id)

    if not cart_items:
        return jsonify({"message": "Cart is empty"}), 400

    temp_dir = tempfile.mkdtemp()
    zip_filename = f"cart_download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_path = os.path.join(temp_dir, zip_filename)

    working_dir = os.getenv("WORKING_DIR", "")
    print(f"DEBUG: Working DIR: '{working_dir}'")
    print(f"DEBUG: Directorio Actual (getcwd): '{os.getcwd()}'")

    with zipfile.ZipFile(zip_path, "w") as zipf:
        for item in cart_items:
            file_model = fm_service.get_by_id(item["file_model_id"])
            if file_model:
                user_id = file_model.data_set.user_id
                dateset_id = file_model.data_set_id
                filename = file_model.fm_meta_data.filename

                file_path = os.path.join(working_dir, "uploads", f"user_{user_id}", f"dataset_{dateset_id}", filename)

                existe = os.path.exists(file_path)
                print(f"DEBUG: Buscando archivo: {file_path}")
                print(f"DEBUG: ¿Existe?: {existe}")

                if os.path.exists(file_path):
                    zipf.write(file_path, arcname=filename)
                else:
                    print("DEBUG: ¡ERROR! El archivo no está donde debería.")

    return send_from_directory(temp_dir, zip_filename, as_attachment=True, mimetype="application/zip")

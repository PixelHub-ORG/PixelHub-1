# Guardar en: scripts/fix_auth.py
import os
import sys

from werkzeug.security import generate_password_hash

from app import create_app, db
from app.modules.auth.models import User

# Añadimos el directorio actual al path para encontrar 'app'
sys.path.append(os.getcwd())


# Importamos el modelo de User.
# NOTA: Ajusta la ruta 'app.modules.auth.models' si tu modelo está en otro
# lado.


def fix():
    print("🔧 Iniciando reparación de credenciales...")
    app = create_app()
    with app.app_context():
        # El email que crea tu seeder original
        email_to_fix = "user1@example.com"
        password_raw = "1234"

        user = User.query.filter_by(email=email_to_fix).first()

        if user:
            print(f"   -> Usuario encontrado: {user.email}")
            # Aquí está la clave: ENCRIPTAMOS la contraseña
            new_hash = generate_password_hash(password_raw)
            user.password = new_hash
            db.session.commit()
            print("✅ ¡ÉXITO! Contraseña actualizada a hash seguro.")
            print(
                f"   -> Ya puedes entrar con: {email_to_fix} / {password_raw}")
        else:
            print(
                f"⚠️ El usuario {email_to_fix} no existe en la base de datos.")


if __name__ == "__main__":
    fix()

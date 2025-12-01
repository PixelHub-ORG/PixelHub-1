import os

from .app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"Iniciando Fakenodo en http://0.0.0.0:{port}")
    app.run(debug=False, host='0.0.0.0', port=port)

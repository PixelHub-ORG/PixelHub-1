from app.services import DepositionService
from flask import Blueprint, jsonify, request

depositions_bp = Blueprint("depositions_bp", __name__)


@depositions_bp.route('/', methods=['GET'])
def list_all():
    """GET /depositions - Lista todos los depositions"""
    depositions = DepositionService.listar_depositions()
    return jsonify([dep.to_dict() for dep in depositions]), 200


@depositions_bp.route('/', methods=['POST'])
def create():
    """POST /depositions - Crea un nuevo deposition
    Acepta tanto payload plano {title, description, metadata}
    como payload de estilo Zenodo {metadata: {...}}.
    """
    data = request.get_json(silent=True) or {}

    # Permitir forma anidada enviada por el cliente de Zenodo: { "metadata": { ... } }
    if isinstance(data.get('metadata'), dict) and ('title' not in data or 'description' not in data):
        meta = data.get('metadata') or {}
        title = meta.get('title')
        description = meta.get('description', '')
        metadata = meta
    else:
        # Forma plana: { "title": ..., "description": ..., "metadata": {...} }
        title = data.get('title')
        description = data.get('description', '')
        metadata = data.get('metadata')

    dep = DepositionService.crear_deposition(
        title=title,
        description=description,
        metadata=metadata
    )

    return jsonify(dep.to_dict()), 201


@depositions_bp.route('/<int:dep_id>', methods=['GET'])
def get_one(dep_id):
    """GET /depositions/1 - Obtiene un deposition"""
    dep = DepositionService.obtener_deposition(dep_id)
    if not dep:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(dep.to_dict()), 200


@depositions_bp.route('/<int:dep_id>/publish', methods=['POST'])
def publish(dep_id):
    """POST /depositions/1/publish - Publica y genera DOI
    Permite que el cliente suministre un DOI opcional usando JSON {"doi": "10.5281/zenodo.<n>"}.
    Si no se proporciona, se usa la lógica por defecto del servidor.
    """
    payload = request.get_json(silent=True) or {}
    provided_doi = payload.get('doi')

    dep = DepositionService.publicar_deposition(dep_id, provided_doi=provided_doi)
    if not dep:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(dep.to_dict()), 200


@depositions_bp.route('/<int:dep_id>/files', methods=['POST'])
def upload_file(dep_id):
    """POST /depositions/1/files - Sube un archivo al deposition (stub)"""
    dep = DepositionService.obtener_deposition(dep_id)
    if not dep:
        return jsonify({'error': 'Not found'}), 404

    # Obtener nombre del archivo
    name = request.form.get('name')
    if not name and 'file' in request.files:
        name = request.files['file'].filename

    if not name:
        return jsonify({'error': 'Missing file name'}), 400

    # Respuesta mínima similar a Zenodo
    return jsonify({
        'id': 1,
        'filename': name,
        'filesize': request.content_length or 0,
        'checksum': 'deadbeef',
        'links': {}
    }), 201


@depositions_bp.route('/<int:dep_id>', methods=['DELETE'])
def delete(dep_id):
    """DELETE /depositions/1 - Elimina un deposition"""
    if DepositionService.eliminar_deposition(dep_id):
        return jsonify({'message': 'Deleted'}), 204
    return jsonify({'error': 'Not found'}), 404


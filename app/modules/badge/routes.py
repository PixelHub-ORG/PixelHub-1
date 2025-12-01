from flask import Blueprint, Response, url_for

from ..dataset.models import DataSet

badge_bp = Blueprint("badge", __name__)


def estimate_text_width(text: str, font_size: int = 11):
    # ancho de un texto para SVG
    return int(max(0, 0.6 * font_size * len(text)))


def make_segment(label_text, bg, font_size=11, pad_x=10, min_w=40):
    # segmento badge: crea nuevo
    w = max(min_w, estimate_text_width(label_text, font_size) + 2 * pad_x)
    return {"w": w, "bg": bg, "text": label_text}


def get_dataset(dataset_id: int):
    # datos del ds
    ds = DataSet.query.get(dataset_id)
    if not ds or not ds.ds_meta_data:
        return None

    downloads = ds.get_download_count()
    title = ds.ds_meta_data.title
    doi = ds.ds_meta_data.dataset_doi or "No DOI"
    url = ds.get_pixelhub_doi() or "#"

    return {"title": title, "downloads": downloads, "doi": doi, "url": url}


@badge_bp.route("/badge/<int:dataset_id>.svg")
def badge_svg_download(dataset_id):
    ds = get_dataset(dataset_id)
    if not ds:
        return Response("Dataset not found", status=404)

    seg_title = make_segment(ds["title"], "#555")
    seg_dl = make_segment(f"{ds['downloads']} DL", "#4c1")
    seg_doi = make_segment(ds["doi"], "#007ec6")

    w1, w2, w3 = seg_title["w"], seg_dl["w"], seg_doi["w"]
    total_w = w1 + w2 + w3
    h = 20
    font = "Verdana,Geneva,sans-serif"
    fs = 11

    c1 = w1 / 2
    c2 = w1 + w2 / 2
    c3 = w1 + w2 + w3 / 2

    link_start = f'<a xlink:href="{ds["url"]}" target="_blank" rel="noopener">' if ds["url"] else ""
    link_end = "</a>" if ds["url"] else ""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{total_w}" height="{h}" role="img" aria-label="{ds["title"]}: {ds["downloads"]} downloads, DOI {ds["doi"]}">
      <linearGradient id="b" x2="0" y2="100%">
        <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
        <stop offset="1" stop-opacity=".1"/>
      </linearGradient>
      <mask id="a"><rect width="{total_w}" height="{h}" rx="3" fill="#fff"/></mask>
      <g mask="url(#a)">
        <rect width="{w1}" height="{h}" fill="{seg_title["bg"]}"/>
        <rect x="{w1}" width="{w2}" height="{h}" fill="{seg_dl["bg"]}"/>
        <rect x="{w1 + w2}" width="{w3}" height="{h}" fill="{seg_doi["bg"]}"/>
        <rect width="{total_w}" height="{h}" fill="url(#b)"/>
      </g>
      {link_start}
      <g fill="#fff" text-anchor="middle" font-family="{font}" font-size="{fs}">
        <text x="{c1}" y="14">{seg_title["text"]}</text>
        <text x="{c2}" y="14">{seg_dl["text"]}</text>
        <text x="{c3}" y="14">{seg_doi["text"]}</text>
      </g>
      {link_end}
    </svg>"""

    # Descarga forzada
    resp = Response(svg, mimetype="image/svg+xml")
    resp.headers["Content-Disposition"] = f'attachment; filename="badge_{dataset_id}.svg"'
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Cache-Control"] = "no-cache"
    return resp


@badge_bp.route("/badge/<int:dataset_id>/svg")
def badge_svg(dataset_id):
    ds = get_dataset(dataset_id)
    if not ds:
        return Response("Dataset not found", status=404)

    seg_title = make_segment(ds["title"], "#555")
    seg_dl = make_segment(f"{ds['downloads']} DL", "#4c1")
    seg_doi = make_segment(ds["doi"], "#007ec6")

    w1, w2, w3 = seg_title["w"], seg_dl["w"], seg_doi["w"]
    total_w = w1 + w2 + w3
    h = 20
    font = "Verdana,Geneva,sans-serif"
    fs = 11

    c1 = w1 / 2
    c2 = w1 + w2 / 2
    c3 = w1 + w2 + w3 / 2

    link_start = f'<a xlink:href="{ds["url"]}" target="_blank" rel="noopener">' if ds["url"] else ""
    link_end = "</a>" if ds["url"] else ""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    width="{total_w}" height="{h}" role="img" aria-label="{ds["title"]}: {ds["downloads"]} downloads, DOI {ds["doi"]}">
      <linearGradient id="b" x2="0" y2="100%">
        <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
        <stop offset="1" stop-opacity=".1"/>
      </linearGradient>
      <mask id="a"><rect width="{total_w}" height="{h}" rx="3" fill="#fff"/></mask>
      <g mask="url(#a)">
        <rect width="{w1}" height="{h}" fill="{seg_title["bg"]}"/>
        <rect x="{w1}" width="{w2}" height="{h}" fill="{seg_dl["bg"]}"/>
        <rect x="{w1 + w2}" width="{w3}" height="{h}" fill="{seg_doi["bg"]}"/>
        <rect width="{total_w}" height="{h}" fill="url(#b)"/>
      </g>
      {link_start}
      <g fill="#fff" text-anchor="middle" font-family="{font}" font-size="{fs}">
        <text x="{c1}" y="14">{seg_title["text"]}</text>
        <text x="{c2}" y="14">{seg_dl["text"]}</text>
        <text x="{c3}" y="14">{seg_doi["text"]}</text>
      </g>
      {link_end}
    </svg>"""

    resp = Response(svg, mimetype="image/svg+xml")
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Cache-Control"] = "no-cache"
    return resp


@badge_bp.route("/badge/<int:dataset_id>/embed")
def badge_embed(dataset_id):
    # Devuelve Markdown y HTML
    ds = get_dataset(dataset_id)
    if not ds:
        return {"error": "Dataset not found"}, 404

    svg_url = url_for("badge.badge_svg", dataset_id=dataset_id, _external=True)
    target = ds["url"] or svg_url
    download_url = svg_url  # descarga del SVG

    markdown = f"[![{ds['title']} - {ds['downloads']} DL - DOI {ds['doi']}]({svg_url})]({target})"
    html = (
        f'<a href="{target}" target="_blank" rel="noopener">'
        f'<img alt="{ds["title"]} - {ds["downloads"]} DL - DOI {ds["doi"]}" src="{svg_url}"></a> '
        f'<a href="{download_url}" download="dataset-{dataset_id}-badge.svg" \
        target="_blank" rel="noopener">⬇ Download SVG</a>'
    )

    return {"markdown": markdown, "html": html}

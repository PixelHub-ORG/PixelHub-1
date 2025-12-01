import re

from flask import jsonify

from app.modules.hubfile.services import HubfileService
from app.modules.pixchecker import pixchecker_bp


@pixchecker_bp.route("/pixchecker/check_pix/<int:file_id>", methods=["GET"])
def check_pix(file_id):
    """Validate a simple PIX-like file syntax.

    Expected structure:
    element1{
        attr1=val1
        attr2=val2
    }
    element2{
        ...
    }

    Returns JSON with 200 on success, or 400 with a list of errors.
    """
    try:
        hubfile = HubfileService().get_or_404(file_id)
        path = hubfile.get_path()

        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()

        errors = []
        parsed_pairs = []

        # Allow either unquoted identifiers or quoted strings (single or double) which may include spaces.
        # We capture the raw token and then "unquote" it so mixed or repeated quote combinations
        # (e.g. '"name"' or '"name\'' ) are normalized by stripping surrounding quote pairs.
        element_header_re = re.compile(r"^\s*(?P<name>(?:\"[^\"]*\"|'[^']*'|[^\{\s][^\{]*?))\s*\{\s*$")
        # For attributes: key can be quoted or unquoted, separator can be ':' or '=', value may be empty.
        attr_re = re.compile(
            r"^\s*(?P<key>(?:\"[^\"]*\"|'[^']*'|[^:=\s][^:=\{]*?))" r"\s*(?P<sep>[:=])\s*(?P<value>.*?)\s*$"
        )

        def unquote_token(tok: str) -> str:
            """Strip surrounding quote pairs (single or double) repeatedly.

            Example: '"name"' -> name, "'foo'" -> foo
            """
            if tok is None:
                return tok
            s = tok.strip()
            # strip matching or mixed surrounding quotes as long as both ends are quotes
            while len(s) >= 2 and (s[0] in "'\"" and s[-1] in "'\""):
                s = s[1:-1]
            return s

        state = "outside"  # or "inside"
        current_element = None

        for idx, raw in enumerate(lines, start=1):
            line = raw.rstrip("\n")
            if state == "outside":
                if line.strip() == "":
                    continue
                m = element_header_re.match(line)
                if m:
                    raw_name = m.group("name")
                    current_element = unquote_token(raw_name)
                    state = "inside"
                else:
                    errors.append(f"Line {idx}: Expected element header like 'name{{' but got: {line!r}")
            else:  # inside an element
                stripped = line.strip()
                if stripped == "":
                    continue
                if stripped == "}":
                    current_element = None
                    state = "outside"
                    continue

                # attribute line expected
                m = attr_re.match(line)
                if m:
                    raw_key = m.group("key")
                    key = unquote_token(raw_key)
                    value = m.group("value")
                    # record parsed key/value for potential future use
                    parsed_pairs.append((key, value))
                else:
                    if "{" in line:
                        errors.append(f"Line {idx}: Unexpected '{{' inside element {current_element!r}")
                    else:
                        errors.append(
                            f"Line {idx}: Invalid attribute format, expected 'key:val' or 'key=val', got: {line!r}"
                        )

        if state == "inside":
            errors.append(f"Unexpected end of file: missing closing '}}' for element {current_element!r}")

        if errors:
            return jsonify({"errors": errors}), 400

        return jsonify({"message": "Valid Model"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@pixchecker_bp.route("/pixchecker/valid/<int:file_id>", methods=["GET"])
def valid(file_id):
    return jsonify({"success": True, "file_id": file_id})

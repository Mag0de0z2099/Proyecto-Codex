import re
from unicodedata import normalize


def slugify(text: str) -> str:
    text = normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9._-]+", "-", text).strip("-").lower()
    return text or "carpeta"

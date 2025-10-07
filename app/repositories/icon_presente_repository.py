from typing import List
import unicodedata
from sqlalchemy.orm import Session

from app.models.icon_presente import IconPresente


class IconPresenteRepository:
    def __init__(self, db: Session):
        self.db = db
        self.model = IconPresente

    @staticmethod
    def _normalize_text(value: str) -> str:
        if not value:
            return ""
        nfkd = unicodedata.normalize("NFKD", value)
        only_ascii = "".join([c for c in nfkd if not unicodedata.combining(c)])
        return only_ascii.lower()

    @staticmethod
    def _to_fa6_name(icon_code: str) -> str:
        if not icon_code:
            return ""
        parts = icon_code.strip().split()
        candidate = parts[-1] if parts else icon_code
        if candidate.startswith("fa-"):
            candidate = candidate[3:]
        return candidate

    def icons_for_present_text(self, text: str) -> List[str]:
        if not text:
            return []
        t = self._normalize_text(text)
        mappings = self.db.query(self.model).all()
        icon_names: List[str] = []
        seen = set()
        for m in mappings:
            if not (m.keyword and m.icon_code):
                continue
            keywords = [kw.strip() for kw in str(m.keyword).split(',') if kw.strip()]
            for kw in keywords:
                nkw = self._normalize_text(kw)
                if nkw and nkw in t:
                    base = self._to_fa6_name(str(m.icon_code))
                    if base and base not in seen:
                        icon_names.append(base)
                        seen.add(base)
                    break
        return icon_names



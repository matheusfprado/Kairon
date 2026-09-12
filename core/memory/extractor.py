import hashlib
import re
import unicodedata

from core.memory.models import MemoryCandidate, MemoryType


def normalize_text(value: str) -> str:
    without_accents = "".join(
        character
        for character in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(character)
    )
    return re.sub(r"\s+", " ", without_accents).strip()


class MemoryExtractor:
    name_pattern = re.compile(
        r"\b(?:meu nome (?:e|\u00e9)|eu me chamo|pode me chamar de)\s+([^,.!?]{2,80})",
        re.IGNORECASE,
    )
    negative_preference_pattern = re.compile(
        r"\b(?:eu\s+)?n(?:a|\u00e3)o gosto de\s+([^,.!?]{2,180})",
        re.IGNORECASE,
    )
    preference_pattern = re.compile(
        r"\b(?:eu\s+)?(?:gosto de|prefiro|minha prefer(?:e|\u00ea)ncia (?:e|\u00e9))"
        r"\s+([^,.!?]{2,180})",
        re.IGNORECASE,
    )
    project_pattern = re.compile(
        r"\b(?:estou trabalhando (?:no|na|em)|meu projeto se chama)\s+([^,.!?]{2,180})",
        re.IGNORECASE,
    )
    residence_pattern = re.compile(
        r"\b(?:eu moro em|minha cidade (?:e|\u00e9))\s+([^,.!?]{2,120})",
        re.IGNORECASE,
    )
    occupation_pattern = re.compile(
        r"\b(?:eu trabalho (?:com|como)|minha profiss(?:a|\u00e3)o (?:e|\u00e9)|"
        r"eu sou (?:um|uma))"
        r"\s+([^,.!?]{2,160})",
        re.IGNORECASE,
    )
    explicit_pattern = re.compile(
        r"\b(?:lembre(?:-se)?|guarde|anote|n(?:a|\u00e3)o esque(?:c|\u00e7)a)"
        r"(?: de)? que\s+(.{2,400})",
        re.IGNORECASE,
    )

    def extract(self, text: str) -> list[MemoryCandidate]:
        candidates: list[MemoryCandidate] = []
        specialized = False

        name = self.name_pattern.search(text)
        if name:
            value = self._clean_name(name.group(1))
            if value:
                candidates.append(
                    MemoryCandidate(
                        type=MemoryType.FACT,
                        content=f"O nome do usuario e {value}.",
                        importance=10,
                        key="user_name",
                    )
                )
                specialized = True

        negative_preference = self.negative_preference_pattern.search(text)
        if negative_preference:
            value = self._clean(negative_preference.group(1))
            if value:
                candidates.append(
                    MemoryCandidate(
                        type=MemoryType.PREFERENCE,
                        content=f"O usuario nao gosta de {value}.",
                        importance=8,
                        key=self._content_key("preference_dislike", value),
                    )
                )
                specialized = True
        else:
            preference = self.preference_pattern.search(text)
            if preference:
                value = self._clean(preference.group(1))
                if value:
                    candidates.append(
                        MemoryCandidate(
                            type=MemoryType.PREFERENCE,
                            content=f"O usuario prefere ou gosta de {value}.",
                            importance=8,
                            key=self._content_key("preference", value),
                        )
                    )
                    specialized = True

        project = self.project_pattern.search(text)
        if project:
            value = self._clean(project.group(1))
            if value:
                candidates.append(
                    MemoryCandidate(
                        type=MemoryType.PROJECT,
                        content=f"O usuario esta trabalhando em {value}.",
                        importance=8,
                        key="current_project",
                    )
                )
                specialized = True

        residence = self.residence_pattern.search(text)
        if residence:
            value = self._clean(residence.group(1))
            if value:
                candidates.append(
                    MemoryCandidate(
                        type=MemoryType.FACT,
                        content=f"O usuario mora em {value}.",
                        importance=9,
                        key="user_residence",
                    )
                )
                specialized = True

        occupation = self.occupation_pattern.search(text)
        if occupation:
            value = self._clean(occupation.group(1))
            if value:
                candidates.append(
                    MemoryCandidate(
                        type=MemoryType.FACT,
                        content=f"O usuario trabalha como ou com {value}.",
                        importance=8,
                        key="user_occupation",
                    )
                )
                specialized = True

        explicit = self.explicit_pattern.search(text)
        if explicit and not specialized:
            value = self._clean(explicit.group(1))
            if value:
                candidates.append(
                    MemoryCandidate(
                        type=MemoryType.LONG_TERM,
                        content=f"O usuario pediu para lembrar que {value}.",
                        importance=9,
                        key=self._content_key("explicit", value),
                    )
                )

        return self._deduplicate(candidates)

    @staticmethod
    def _clean(value: str) -> str:
        return value.strip().strip(" -;:.!?")[:400]

    def _clean_name(self, value: str) -> str:
        name = self._clean(re.split(r"\s+e\s+", value, maxsplit=1, flags=re.IGNORECASE)[0])
        return re.sub(r"^(?:so|s\u00f3)\s+", "", name, flags=re.IGNORECASE)

    @staticmethod
    def _content_key(prefix: str, value: str) -> str:
        digest = hashlib.sha256(normalize_text(value).encode("utf-8")).hexdigest()[:16]
        return f"{prefix}:{digest}"

    @staticmethod
    def _deduplicate(candidates: list[MemoryCandidate]) -> list[MemoryCandidate]:
        return list({candidate.key: candidate for candidate in candidates}.values())

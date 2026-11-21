
import re
from pathlib import Path
from config import DATA_DIR

ARTICLE_RE = re.compile(
    r"^제(\d+)조(?:의(\d+))?"
    r"(?:\s*\(([^)\n]*)\))?\s*$",
    re.MULTILINE,
)

CASE_SPLIT_RE = re.compile(
    r"^===== 판례 \d+ =====\s*$", re.MULTILINE
)

FIELDS = [
    "사건명", "사건번호", "법원",
    "선고일자", "사건종류", "참조조문",
]


def read_text(path: Path):
    return path.read_text(encoding="utf-8-sig")


def parse_laws():
    for path in sorted(DATA_DIR.glob("*.txt")):
        text = read_text(path)
        law_name = path.stem
        matches = list(ARTICLE_RE.finditer(text))

        for i, match in enumerate(matches):
            start = match.end()
            end = (
                matches[i + 1].start()
                if i + 1 < len(matches)
                else len(text)
            )

            number = match.group(1)
            if match.group(2):
                number += f"의{match.group(2)}"

            yield {
                "id": f"{law_name}:{number}",
                "law": law_name,
                "number": number,
                "title": match.group(3) or "",
                "text": text[start:end].strip(),
                "source": str(path.relative_to(DATA_DIR)),
            }


def extract_section(text, title, next_titles):
    start_match = re.search(
        rf"【{re.escape(title)}】", text
    )
    if not start_match:
        return ""

    content = text[start_match.end():]

    for next_title in next_titles:
        marker = re.search(
            rf"【{re.escape(next_title)}】", content
        )
        if marker:
            content = content[:marker.start()]

    return content.strip()


def parse_cases(max_per_file=0):
    folder = DATA_DIR / "판례"

    for path in sorted(folder.glob("*.txt")):
        text = read_text(path)
        blocks = CASE_SPLIT_RE.split(text)[1:]
        count = 0

        for block in blocks:
            metadata = {}

            for field in FIELDS:
                match = re.search(
                    rf"^{field}:\s*(.*)$",
                    block,
                    re.MULTILINE,
                )
                metadata[field] = (
                    match.group(1).strip() if match else ""
                )

            case_no = metadata["사건번호"]
            if not case_no:
                continue

            issues = extract_section(
                block, "판시사항",
                ["판결요지", "판결문 발췌"],
            )
            summary = extract_section(
                block, "판결요지", ["판결문 발췌"]
            )

            yield {
                "id": f"{metadata['법원']}:{case_no}",
                "name": metadata["사건명"],
                "number": case_no,
                "court": metadata["법원"],
                "date": metadata["선고일자"],
                "case_type": metadata["사건종류"],
                "references": metadata["참조조문"],
                "issues": issues,
                "summary": summary,
                "source": str(path.relative_to(DATA_DIR)),
            }

            count += 1
            if max_per_file and count >= max_per_file:
                break


# 판례 참조조문에서 명시적 조문 관계 추출
LAW_NAMES = [
    "대한민국헌법", "헌법", "민법", "형법",
    "민사소송법", "형사소송법", "상법",
]

REF_RE = re.compile(
    r"(?<![\w가-힣])"
    r"(대한민국헌법|헌법|민사소송법|형사소송법|민법|형법|상법)"
    r"\s*제(\d+)조(?:의(\d+))?"
    r"((?:\s*제\d+항)?)"
)


def parse_references(text):
    result = set()

    for match in REF_RE.finditer(text):
        law = match.group(1)
        if law == "헌법":
            law = "대한민국헌법"

        number = match.group(2)
        if match.group(3):
            number += f"의{match.group(3)}"

        result.add(f"{law}:{number}")

    return sorted(result)

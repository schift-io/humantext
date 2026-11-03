#!/usr/bin/env python3
"""humantext lint: 한국어 글에서 AI 투 패턴과 문체 프로필을 센다.

표준 라이브러리만 쓴다. 판정이 아니라 "다시 읽어 볼 곳"의 목록이다.

    python3 humantext_lint.py draft.md
    python3 humantext_lint.py draft.md --json
    python3 humantext_lint.py before.md --compare after.md
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

# (id, 묶음, 정규식, 설명). 묶음: slop=AI 습관, report=보고체, hedge=면책·선부정,
# calque=번역투, stiff=딱딱한 한자어, format=장식, sales=영업 문구
PATTERNS: list[tuple[str, str, str, str]] = [
    # --- 구조 슬롭
    ("contrast", "slop", r"(?:이|가|은|는)?\s?아니라\s", "「A가 아니라 B」 대비 구문"),
    (
        "count_announce",
        "slop",
        r"(?:두|세|네|다섯|[2-9])\s?(?:가지|개|갈래|축|단계)(?:가|를|의)?\s?(?:있다|있습니다|이다|입니다|다\.|로 정리)",
        "개수를 먼저 선언(「선택이 셋 있다」)",
    ),
    (
        "count_announce",
        "slop",
        r"(?:선택|이유|포인트|교훈|차이)(?:이|가)\s?(?:셋|넷|둘)",
        "개수를 먼저 선언",
    ),
    (
        "meaning_inflate",
        "slop",
        r"(?:중요한|의미 있는|주목할 만한|눈여겨볼|기록해 둘 만한)\s?(?:것은|점은|대목|부분|선택|변화)",
        "의미 부여형 표현",
    ),
    (
        "meaning_inflate",
        "slop",
        r"(?:전환점|패러다임|게임 ?체인저|새로운 차원|한 단계 더|본질적|근본적으로)",
        "과장된 의미 부여",
    ),
    (
        "ai_vocab",
        "slop",
        r"(?:핵심(?:은|이다|입니다)|결국|사실상|무엇보다|이처럼|이를 통해|요컨대|정리하면|결론적으로|요약하면)",
        "AI가 자주 쓰는 연결·요약어",
    ),
    (
        "ai_vocab",
        "slop",
        r"(?:역할을\s?(?:한다|합니다|하며)|자리(?:한다|합니다|잡았다)|을 보장(?:하며|한다)|을 반영(?:하며|한다))",
        "직접 서술 대신 쓰는 우회 동사",
    ),
    (
        "metaphor",
        "slop",
        r"(?:척추|등뼈|해자|청사진|나침반|퍼즐 조각|토대 위|기반 위|DNA|열쇠(?:다|이다|입니다))",
        "추상 대상에 쓴 물리 은유",
    ),
    (
        "signpost",
        "slop",
        r"(?:살펴보(?:자|겠|면)|알아보(?:자|겠)|이 글은 .{0,40}(?:정리한다|다룬다|살펴본다))",
        "글이 글 자신을 소개하는 문장",
    ),
    ("arrow", "slop", r"[⟹→⇒]\s", "화살표로 결론 잇기"),
    # --- 보고체 (독자 글에 섞이면 문제)
    (
        "report",
        "report",
        r"(?:확인했|반영했|넣었|정리했|진행했|추가했|수정했|바꿨|올렸|만들었)(?:습니다|다)",
        "작업 보고 어미(독자 글이면 경고)",
    ),
    (
        "report",
        "report",
        r"(?:드리겠습니다|하겠습니다|예정입니다)",
        "다음 할 일을 알리는 보고 어미",
    ),
    # --- 면책·선부정
    (
        "hedge",
        "hedge",
        r"(?:로 보지 않는다|라고 보지 않|단정(?:할 수 없|하기 어렵|하지 않)|일 수도 있다|수도 있습니다|것으로 보인다|것으로 보입니다|라고 볼 수 있|아닐까)",
        "면책성 유보",
    ),
    (
        "neg_first",
        "hedge",
        r"(?:하지 않는다|하지 않습니다|않았다|없다|아니다)\.",
        "부정으로 끝나는 문장(밀도 확인)",
    ),
    # --- 번역투
    (
        "calque",
        "calque",
        r"(?:에 있어서|에 있어|를 통해서?|을 통해서?|에 의해|로 인해|함에 따라|에 기반한|에 대해서?|되어지|가지고 있다|가지고 있습니다|하는 것이 중요|의 경우)",
        "번역투 조사·구문",
    ),
    (
        "passive",
        "calque",
        r"(?:되었다|되었습니다|됩니다|된다)\.",
        "주어 없는 피동 종결(밀도 확인)",
    ),
    # --- 딱딱한 한자어
    (
        "stiff",
        "stiff",
        r"(?:상회|하회|도모|제고|영위|수립|기여(?:한다|합니다)|용이|상이|부재|결손|채택했|부여하지)",
        "입말로 바꿀 수 있는 한자어",
    ),
    # --- 장식
    ("bold", "format", r"\*\*[^*\n]+\*\*", "굵게"),
    ("guillemet", "format", r"[«»]", "«» 강조"),
    ("corner", "format", r"[「」『』]", "「」 강조"),
    ("emdash", "format", r"—", "em dash"),
    ("circled", "format", r"[①②③④⑤⑥⑦⑧⑨]", "원문자 나열"),
    ("emoji", "format", r"[\U0001F300-\U0001FAFF✅✨⭐⚡❤❌]", "이모지"),
    (
        "scare_quote",
        "format",
        r"[\"“'‘][^\"”'’\n]{1,12}[\"”'’](?!라고|라는|하고|며|고 )",
        "강조용 따옴표(헛따옴표)",
    ),
    # --- 읽는 법을 알려 주는 문장
    (
        "meta_read",
        "meta",
        r"(?:로 읽어야|로 읽(?:는다|힌다|으면)|읽을 것|볼 것은|보는 편이|알아야 할 것|을 알 수 있|를 알 수 있|을 보여\s?준다|를 보여\s?준다|보여준다|짚어 ?보자|눈여겨볼)",
        "결론 대신 읽는 법을 말하는 문장",
    ),
    # --- 있다·것·수
    ("go_itda", "filler", r"고\s있(?:다|었다|습니다|는)", "「~하고 있다」 진행형"),
    (
        "geot",
        "filler",
        r"[가-힣] 것(?:이다|입니다|이었다|이었습니다|이며)",
        "「~한 것이다」",
    ),
    (
        "su_itda",
        "filler",
        r"[가-힣] 수도? 있(?:다|습니다|을|어)",
        "「~할 수 있다/수도 있다」",
    ),
    (
        "vague",
        "filler",
        r"(?:잘 처리|많은 노력|노력을 기울|다양한 (?:방면|측면)|효과적으로|적극적으로|원활(?:한|하게))",
        "두루뭉술한 표현",
    ),
    (
        "calque",
        "calque",
        r"(?:에 대하여|에 의해서|하는 바이다|하는 바입니다)",
        "번역투 조사·구문",
    ),
    # --- 접속사
    (
        "conj",
        "conj",
        r"(?:^|[.?!]\s+)(?:그리고|그래서|하지만|그러나|따라서|또한|그러므로|그런데|게다가)(?:는)?\s",
        "문두 접속사",
    ),
    # --- 영업 문구
    (
        "rhetorical_q",
        "sales",
        r"(?:고민이신가요|어떠신가요|궁금하지 않으세요|있으신가요|해 보셨나요|아시나요)\?",
        "독자에게 되묻는 영업 질문",
    ),
    (
        "hype",
        "sales",
        r"(?:혁신적|획기적|압도적|완벽한|강력한|차원이 다른|놀라운)",
        "근거 없는 형용사",
    ),
]

COMPILED = [(pid, grp, re.compile(rx), desc) for pid, grp, rx, desc in PATTERNS]

ENDINGS = [
    ("습니다", re.compile(r"(?:습니다|ㅂ니다|니다)[.?!]?$")),
    ("해요", re.compile(r"(?:요|죠)[.?!]?$")),
    ("한다", re.compile(r"다[.?!]?$")),
    ("명사형", re.compile(r"(?:음|함|임|됨|기)[.?!]?$")),
]


def strip_code(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return re.sub(r"`[^`\n]+`", "", text)


def sentences(text: str) -> list[str]:
    out = []
    for para in paragraphs(text):
        if para.lstrip().startswith(("|", "#")):
            continue
        for s in re.split(r"(?<=[.?!])\s+", para.replace("\n", " ")):
            s = s.strip(" -*>")
            if len(s) >= 4:
                out.append(s)
    return out


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def ending_of(s: str) -> str:
    s = s.rstrip(" \"'”’)」』")
    for name, rx in ENDINGS:
        if rx.search(s):
            return name
    return "기타"


def cv(xs: list[int]) -> float | None:
    if len(xs) < 2:
        return None
    m = statistics.mean(xs)
    return round(statistics.pstdev(xs) / m, 3) if m else None


def profile(text: str) -> dict:
    sents = sentences(text)
    lens = [len(s.replace(" ", "")) for s in sents]
    paras = [p for p in paragraphs(text) if not p.lstrip().startswith(("|", "#"))]
    plens = [len(p.replace(" ", "")) for p in paras]
    lines = [l for l in text.splitlines() if l.strip()]
    bullets = sum(1 for l in lines if re.match(r"\s*(?:[-*•]|\d+[.)])\s", l))
    seq = [ending_of(s) for s in sents]
    ends = Counter(seq)
    run = best = 0
    for i, e in enumerate(seq):
        run = run + 1 if i and e == seq[i - 1] else 1
        best = max(best, run)
    starts = Counter(s.split()[0] for s in sents if s.split())
    chars = max(1, len(text.replace(" ", "").replace("\n", "")))
    return {
        "chars": chars,
        "sentences": len(sents),
        "sent_len_mean": round(statistics.mean(lens), 1) if lens else None,
        "sent_len_cv": cv(lens),
        "sent_over_80": round(sum(1 for x in lens if x > 80) / len(lens), 3)
        if lens
        else None,
        "sent_under_15": round(sum(1 for x in lens if x < 15) / len(lens), 3)
        if lens
        else None,
        "paragraphs": len(paras),
        "para_len_cv": cv(plens),
        "bullet_line_ratio": round(bullets / len(lines), 3) if lines else 0.0,
        "endings": dict(ends.most_common()),
        "ending_top_share": round(ends.most_common(1)[0][1] / len(seq), 3) if seq else None,
        "ending_max_run": best,
        "top_openers": [(w, n) for w, n in starts.most_common(5) if n >= 3],
    }


def lint(text: str) -> list[dict]:
    body = strip_code(text)
    hits = []
    for lineno, line in enumerate(body.splitlines(), 1):
        for pid, grp, rx, desc in COMPILED:
            for m in rx.finditer(line):
                hits.append(
                    {
                        "line": lineno,
                        "id": pid,
                        "group": grp,
                        "desc": desc,
                        "match": m.group(0).strip(),
                        "context": line.strip()[:120],
                    }
                )
    return hits


def summarize(text: str) -> dict:
    hits = lint(text)
    prof = profile(text)
    per_k = 1000 / prof["chars"]
    by_id = Counter(h["id"] for h in hits)
    by_group = Counter(h["group"] for h in hits)
    return {
        "profile": prof,
        "counts": dict(by_id.most_common()),
        "groups": dict(by_group.most_common()),
        "per_1k_chars": {k: round(v * per_k, 2) for k, v in by_group.most_common()},
        "hits": hits,
    }


def print_report(name: str, s: dict, show_hits: bool) -> None:
    p = s["profile"]
    print(f"# {name}")
    print(f"글자 {p['chars']} · 문장 {p['sentences']} · 문단 {p['paragraphs']}")
    print(
        f"문장 길이 평균 {p['sent_len_mean']} · 변동계수 {p['sent_len_cv']} · "
        f"80자 초과 {p['sent_over_80']} · 15자 미만 {p['sent_under_15']}"
    )
    print(
        f"문단 길이 변동계수 {p['para_len_cv']} · 글머리표 줄 비율 {p['bullet_line_ratio']}"
    )
    print(f"종결 {p['endings']} · 최다 종결 비율 {p['ending_top_share']} · 같은 종결 최장 연속 {p['ending_max_run']}")
    if p["top_openers"]:
        print(f"반복되는 문두 {p['top_openers']}")
    print(
        "묶음별 (1천 자당): "
        + ", ".join(f"{k} {v}" for k, v in s["per_1k_chars"].items())
    )
    print("패턴별: " + ", ".join(f"{k} {v}" for k, v in s["counts"].items()))
    if show_hits:
        print()
        for h in s["hits"]:
            print(
                f"  L{h['line']:>4} [{h['group']}/{h['id']}] {h['match']}  | {h['context']}"
            )


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("file")
    ap.add_argument("--compare", help="고친 글. 원문과 숫자를 나란히 본다")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-hits", action="store_true", help="줄별 목록을 빼고 요약만")
    a = ap.parse_args()

    src = Path(a.file).read_text(encoding="utf-8")
    s1 = summarize(src)
    if not a.compare:
        if a.json:
            json.dump(s1, sys.stdout, ensure_ascii=False, indent=1)
        else:
            print_report(a.file, s1, not a.no_hits)
        return 0

    s2 = summarize(Path(a.compare).read_text(encoding="utf-8"))
    if a.json:
        json.dump({"before": s1, "after": s2}, sys.stdout, ensure_ascii=False, indent=1)
        return 0
    keys = [
        "sent_len_mean",
        "sent_len_cv",
        "sent_over_80",
        "sent_under_15",
        "para_len_cv",
        "bullet_line_ratio",
    ]
    print(f"{'항목':<20}{'원문':>10}{'고친 글':>10}")
    for k in keys:
        print(f"{k:<20}{str(s1['profile'][k]):>10}{str(s2['profile'][k]):>10}")
    print(f"{'endings':<20}{s1['profile']['endings']}  →  {s2['profile']['endings']}")
    groups = sorted(set(s1["per_1k_chars"]) | set(s2["per_1k_chars"]))
    print("\n묶음 (1천 자당)")
    for g in groups:
        print(
            f"  {g:<10}{s1['per_1k_chars'].get(g, 0):>8}{s2['per_1k_chars'].get(g, 0):>8}"
        )
    left = [h for h in s2["hits"] if h["group"] in ("slop", "report", "hedge", "meta", "filler")]
    if left:
        print(f"\n고친 글에 남은 slop/report/hedge/meta/filler {len(left)}건")
        for h in left[:30]:
            print(f"  L{h['line']:>4} [{h['id']}] {h['match']}  | {h['context']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

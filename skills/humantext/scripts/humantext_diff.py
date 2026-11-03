#!/usr/bin/env python3
"""humantext diff: 고치기 전과 후에서 뜻이 바뀌었을 수 있는 곳을 먼저 보여 준다.

숫자, 부정, 유보, 고유명사·영문, 링크가 사라지거나 생긴 것을 센다.
뜻이 같은지는 판정하지 않는다. 사람이(또는 모델이) 읽을 목록이다.

    python3 humantext_diff.py before.md after.md
    python3 humantext_diff.py before.md after.md --fail   # 숫자·개수 표현·링크가 아예 사라지면 종료 코드 1
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

NUM = re.compile(
    r"[−\-+]?\d[\d,]*(?:\.\d+)?[ ]?(?:%|퍼센트|배|건|개|명|원|만|억|천|초|분|시간|일|주|개월|년|B|M|K|회|점|쪽|편|자|가지|단계|종|곳|분야|축|줄|번)?"
)
URL = re.compile(r"https?://\S+")
# 한글 수사: "셋뿐", "넷이", "세 가지", "두 건" 같은 개수 표현을 쓰인 그대로 센다.
KNUM_BARE = re.compile(r"(?<![가-힣])(하나|둘|셋|넷|다섯|여섯|일곱|여덟|아홉)(?=뿐|이|가|은|는|을|를|과|와|도|만|째|[.,\s]|$)")
KNUM_UNIT = re.compile(r"(?<![가-힣])(한|두|세|네|다섯|여섯|일곱|여덟|아홉|열)\s?(개|가지|명|건|번|종|곳|분야|축|단계|줄)")
LATIN = re.compile(r"(?<![A-Za-z0-9])[A-Za-z][A-Za-z0-9.\-_/]*[A-Za-z0-9](?![A-Za-z0-9])")
NEG = re.compile(r"(?:않|없|못|아니|안 |말고|빼고|제외)")
HEDGE = re.compile(
    r"(?:것으로 보|수도 있|추정|약 |대략|가량|쯤|듯|같다|일지|미확인|아직)"
)
LIMIT = re.compile(r"(?:만\s|뿐|까지|부터|이상|이하|초과|미만|경우에만|때만|일부)")


def knum_bag(text: str) -> Counter:
    c = Counter()
    for m in KNUM_BARE.finditer(text):
        c[m.group(1)] += 1
    for m in KNUM_UNIT.finditer(text):
        c[f"{m.group(1)} {m.group(2)}"] += 1
    return c


def norm_num(s: str) -> str:
    return s.replace(",", "").replace(" ", "").replace("−", "-")


def bag(rx: re.Pattern, text: str, norm=lambda x: x.strip()) -> Counter:
    return Counter(norm(m.group(0)) for m in rx.finditer(text) if m.group(0).strip())


def show(title: str, a: Counter, b: Counter, fail_keys: list[str], key: str) -> bool:
    gone = sorted(set(a) - set(b))
    new = sorted(set(b) - set(a))
    fewer = sorted(k for k in set(a) & set(b) if b[k] < a[k])
    if not gone and not new and not fewer:
        print(f"[같음] {title}")
        return False
    print(f"[확인] {title}")
    if gone:
        print("   사라짐: " + ", ".join(gone[:40]))
    if new:
        print("   새로 생김: " + ", ".join(new[:40]))
    if fewer:
        print("   횟수만 줄어듦: " + ", ".join(f"{k} {a[k]}→{b[k]}" for k in fewer[:40]))
    return bool(gone) and key in fail_keys


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument(
        "--fail", action="store_true", help="숫자·개수 표현·링크가 아예 사라지면 종료 코드 1"
    )
    a = ap.parse_args()
    t1 = Path(a.before).read_text(encoding="utf-8")
    t2 = Path(a.after).read_text(encoding="utf-8")
    u1, u2 = URL.sub(" ", t1), URL.sub(" ", t2)

    fail_keys = ["num", "url"] if a.fail else []
    bad = False
    bad |= show("숫자·단위", bag(NUM, u1, norm_num), bag(NUM, u2, norm_num), fail_keys, "num")
    # 개수 표현(셋뿐, 세 가지)은 따로 보여 준다. 숫자가 많은 글에서 묻히지 않게 한다.
    bad |= show("개수 표현 (셋, 세 가지 등)", knum_bag(u1), knum_bag(u2), fail_keys, "num")
    bad |= show("링크", bag(URL, t1), bag(URL, t2), fail_keys, "url")
    bad |= show("영문·고유명사", bag(LATIN, u1), bag(LATIN, u2), fail_keys, "latin")
    n1, n2 = len(NEG.findall(t1)), len(NEG.findall(t2))
    h1, h2 = len(HEDGE.findall(t1)), len(HEDGE.findall(t2))
    l1, l2 = len(LIMIT.findall(t1)), len(LIMIT.findall(t2))
    print(
        f"[{'같음' if n1 == n2 else '확인'}] 부정 표현 {n1} → {n2}"
        + (
            "  (부정이 줄었으면 주장이 뒤집히지 않았는지 문장별로 읽는다)"
            if n2 < n1
            else ""
        )
    )
    print(
        f"[{'같음' if h1 == h2 else '확인'}] 유보·추정 {h1} → {h2}"
        + (
            "  (유보가 줄었으면 확인 안 된 것을 단정하지 않았는지 본다)"
            if h2 < h1
            else ""
        )
    )
    print(f"[{'같음' if l1 == l2 else '확인'}] 범위·조건 {l1} → {l2}")
    c1, c2 = len(t1.replace(" ", "")), len(t2.replace(" ", ""))
    print(f"[정보] 글자 수 {c1} → {c2} ({(c2 - c1) / max(c1, 1):+.0%})")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

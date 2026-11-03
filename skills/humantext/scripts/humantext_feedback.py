#!/usr/bin/env python3
"""humantext 불만 수집. 사용자가 고른 동의 단계만큼만 보낸다.

    python3 humantext_feedback.py consent show
    python3 humantext_feedback.py consent set 1|2|3
    python3 humantext_feedback.py record --source a.md --final b.md --reader R --purpose P --doc-type T
    python3 humantext_feedback.py hook        # Claude Code UserPromptSubmit 훅. stdin으로 JSON을 받는다

동의 단계
  1  싫어요. 아무것도 보내지 않는다(기본값)
  2  불만 문장 + 글의 대상 및 목적, lint·diff 요약 숫자
  3  2 + 초안 본문(고치기 전과 후). 민감정보를 다룬다면 고르지 않는다

설정은 ~/.config/humantext/ (HUMANTEXT_HOME으로 바꿀 수 있다)에 저장한다.
훅은 humantext 실행 뒤 30분 안의 메시지 중 불만으로 보이는 것만, 한 실행에 최대 3건 보낸다.
훅은 어떤 경우에도 대화를 막지 않고 아무것도 출력하지 않는다.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import uuid
from pathlib import Path

VERSION = "0.2.0"
ENDPOINT = os.environ.get(
    "HUMANTEXT_ENDPOINT", "https://humantext.schift.io/v1/feedback"
)
HOME = Path(os.environ.get("HUMANTEXT_HOME", Path.home() / ".config" / "humantext"))
CONSENT = HOME / "consent.json"
LAST_RUN = HOME / "last_run.json"
WINDOW_SEC = 30 * 60
MAX_SENDS_PER_RUN = 3

CHOICES = {
    1: "싫어요",
    2: "불만 문장 + 글의 대상 및 목적만 (감사합니다)",
    3: "초안 본문 포함 (민감정보를 다룰 수 있다면 하지 마세요)",
}

COMPLAINT = re.compile(
    r"딱딱|어색|부자연|이상(?:해|한|하)|별로|마음에 안|맘에 안|구려|구리다|슬롭|slop|번역투|보고체|AI ?티|기계적|로봇"
    r"|왜 이래|왜이래|이따[구위]|뭔 ?소리|무슨 말|읽을 수가|안 읽|못 읽|길어|장황|너무 짧|다시 (?:써|해)"
    r"|틀렸|틀린|아니잖|이게 뭐|싫어|촌스|오글|과장|빠졌|빼먹|뜻이 (?:달|바뀌)|의미가 (?:달|바뀌)|별론",
    re.I,
)


def _read(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write(path: Path, data: dict) -> None:
    HOME.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def consent_level() -> int:
    c = _read(CONSENT)
    try:
        return int(c["level"]) if c else 1
    except Exception:
        return 1


def cmd_consent(a: argparse.Namespace) -> int:
    if a.op == "show":
        c = _read(CONSENT)
        if not c:
            print("아직 고르지 않았습니다. 고르기 전에는 아무것도 보내지 않습니다.")
            for k, v in CHOICES.items():
                print(f"  {k}. {v}")
            return 3
        print(
            f"{c['level']}. {CHOICES.get(int(c['level']), '?')}  (client_id {c['client_id']})"
        )
        return 0
    level = int(a.level)
    if level not in CHOICES:
        print("1, 2, 3 중에서 고릅니다.", file=sys.stderr)
        return 2
    old = _read(CONSENT) or {}
    _write(
        CONSENT,
        {
            "level": level,
            "client_id": old.get("client_id") or str(uuid.uuid4()),
            "set_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        },
    )
    print(f"저장했습니다: {level}. {CHOICES[level]}")
    if level >= 2:
        print(
            f"불만을 말했을 때만 보냅니다. 보낸 기록이 있으면 이 명령으로 지웁니다: curl -X DELETE {ENDPOINT}/{(_read(CONSENT) or {}).get('client_id')}"
        )
    return 0


def _summaries(source: Path, final: Path) -> tuple[dict, dict]:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import humantext_diff as hd  # noqa: E402
    import humantext_lint as hl  # noqa: E402

    t1, t2 = source.read_text(encoding="utf-8"), final.read_text(encoding="utf-8")
    s1, s2 = hl.summarize(t1), hl.summarize(t2)
    keep = [
        "sent_len_mean",
        "sent_len_cv",
        "sent_under_15",
        "para_len_cv",
        "bullet_line_ratio",
    ]
    lint = {
        "before": {
            "profile": {k: s1["profile"][k] for k in keep},
            "per_1k": s1["per_1k_chars"],
        },
        "after": {
            "profile": {k: s2["profile"][k] for k in keep},
            "per_1k": s2["per_1k_chars"],
        },
    }
    u1, u2 = hd.URL.sub(" ", t1), hd.URL.sub(" ", t2)
    n1 = hd.bag(hd.NUM, u1, hd.norm_num)
    n2 = hd.bag(hd.NUM, u2, hd.norm_num)
    k1, k2 = hd.knum_bag(u1), hd.knum_bag(u2)
    diff = {
        "numbers_gone": len(set(n1) - set(n2)),
        "numbers_new": len(set(n2) - set(n1)),
        "counts_gone": len(set(k1) - set(k2)),
        "counts_new": len(set(k2) - set(k1)),
        "links_gone": len(set(hd.bag(hd.URL, t1)) - set(hd.bag(hd.URL, t2))),
        "neg": [len(hd.NEG.findall(t1)), len(hd.NEG.findall(t2))],
        "hedge": [len(hd.HEDGE.findall(t1)), len(hd.HEDGE.findall(t2))],
        "chars": [len(t1.replace(" ", "")), len(t2.replace(" ", ""))],
    }
    return lint, diff


def cmd_record(a: argparse.Namespace) -> int:
    if consent_level() < 2:
        return 0
    source, final = Path(a.source).resolve(), Path(a.final).resolve()
    try:
        lint, diff = _summaries(source, final)
    except Exception as e:  # 요약 실패가 스킬 결과를 막지 않게 한다
        lint, diff = None, {"error": type(e).__name__}
    _write(
        LAST_RUN,
        {
            "ts": time.time(),
            "reader": a.reader,
            "purpose": a.purpose,
            "doc_type": a.doc_type,
            "source": str(source),
            "final": str(final),
            "lint": lint,
            "diff": diff,
            "sent": 0,
        },
    )
    return 0


def _post(payload: dict) -> int:
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "user-agent": f"humantext/{VERSION}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=3) as r:
        return r.status


def _note(reason: str) -> None:
    """동의 2·3일 때만 마지막 훅 결과를 한 줄 남긴다. 사용자 문장은 남기지 않는다."""
    try:
        (HOME / "hook_last.txt").write_text(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {reason}\n", encoding="utf-8")
    except Exception:
        pass


def cmd_hook(_a: argparse.Namespace) -> int:
    try:
        level = consent_level()
        if level < 2:
            return 0
        data = json.loads(sys.stdin.read() or "{}")
        prompt = (data.get("prompt") or "").strip()
        if not prompt or prompt.startswith("/"):
            _note("skip: empty or slash command")
            return 0
        if not COMPLAINT.search(prompt):
            _note("skip: not a complaint")
            return 0
        run = _read(LAST_RUN)
        if not run:
            _note("skip: no humantext run recorded")
            return 0
        if time.time() - run.get("ts", 0) > WINDOW_SEC:
            _note("skip: last run older than 30 min")
            return 0
        if run.get("sent", 0) >= MAX_SENDS_PER_RUN:
            _note("skip: already sent 3 for this run")
            return 0
        c = _read(CONSENT) or {}
        payload = {
            "skill_version": VERSION,
            "client_id": c.get("client_id"),
            "consent": level,
            "doc_type": run.get("doc_type"),
            "reader": run.get("reader"),
            "purpose": run.get("purpose"),
            "complaint": prompt[:4000],
            "lint": run.get("lint"),
            "diff": run.get("diff"),
        }
        if level == 3:
            for key, field in (("source", "draft_before"), ("final", "draft_after")):
                try:
                    payload[field] = Path(run[key]).read_text(encoding="utf-8")[:100000]
                except Exception:
                    pass
        status = _post(payload)
        if status in (200, 201):
            run["sent"] = run.get("sent", 0) + 1
            _write(LAST_RUN, run)
        _note(f"sent: http {status}")
    except Exception as e:
        _note(f"error: {type(e).__name__}")  # 수집 실패는 대화를 막지 않는다
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("consent")
    c.add_argument("op", choices=["show", "set"])
    c.add_argument("level", nargs="?")
    r = sub.add_parser("record")
    r.add_argument("--source", required=True)
    r.add_argument("--final", required=True)
    r.add_argument("--reader", default="")
    r.add_argument("--purpose", default="")
    r.add_argument("--doc-type", default="")
    sub.add_parser("hook")
    a = ap.parse_args()
    if a.cmd == "consent":
        if a.op == "set" and not a.level:
            ap.error("consent set 1|2|3")
        return cmd_consent(a)
    if a.cmd == "record":
        return cmd_record(a)
    return cmd_hook(a)


if __name__ == "__main__":
    sys.exit(main())

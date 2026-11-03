# humantext

AI가 쓴 한국어 초안을, 받는 사람에게 내용이 바로 전달되는 글로 다시 쓰는 Claude Code 스킬입니다.

[한국어](#한국어) · [English](#english)

## 한국어

### 무엇이 다른가

AI 티를 지우는 스킬은 이미 많습니다. 대부분 "A가 아니라 B", em dash, 번역투 같은 패턴 목록을 두고 걸리는 표현을 고칩니다. 그렇게 고친 글도 여전히 안 읽히는 경우가 많은데, 이유는 패턴이 아니라 **글이 누구에게 무엇을 전하려는지가 문장에 없기** 때문입니다.

AI 초안은 글을 부탁한 사람에게 보고하듯 쓰입니다. 무엇을 확인했고, 무엇은 아니며, 무엇은 하지 않았는지를 붙이고, "~로 읽어야 한다", "~을 보여 준다"처럼 결론 대신 읽는 법을 말합니다. 받는 사람은 "그래서 나는 뭘 알면 되는데?"라고 묻게 됩니다.

humantext는 문장을 한 줄씩 고치지 않습니다.

1. 받는 사람과, 그 사람이 읽고 나서 알거나 해야 할 것을 먼저 정합니다.
2. 초안에서 내용(주장, 숫자, 조건, 할 일)만 뽑고, 작성자용 보고와 면책 문장은 버립니다.
3. 뽑은 내용만 보고 받는 사람 기준으로 새로 씁니다.
4. 숫자, 링크, 부정, 조건이 빠지거나 바뀌지 않았는지 스크립트로 대조합니다.

### 왜 다시 쓰는가

Schift에서 한국어 윤문 모델을 만들며 잰 결과입니다(2026-10, 평가원 지문 287편을 기준 분포로, 87개 주제).

- 프런티어 모델 세 종류(Gemini 3.8 flash, Gemini 4 Argon, Claude Opus 5.5)에게 같은 지시문으로 윤문을 맡기자, 기준 분포와의 거리가 초안 1.41에서 1.40~1.50으로 그대로이거나 나빠졌습니다.
- 습관 문구를 지우도록 학습한 모델은 습관 점수를 평균 85% 줄였지만, 문장 길이·종결·접속·문단 길이로 잰 문체 프로필은 평균 12%만 줄였습니다. 출력이 입력 초안의 문체를 거의 그대로 물려받았습니다.

문장을 붙잡고 고치면 문장 수, 문단 구성, 정보 순서가 초안 그대로 남습니다. 그래서 내용을 뽑아 새로 씁니다.

### 설치

```bash
claude plugin marketplace add schift-io/humantext
claude plugin install humantext@humantext
```

Claude Code를 다시 열고 `/humantext:humantext`로 부르거나, "이 글 humantext로 다시 써 줘"라고 요청합니다.

### 쓰는 법

```text
/humantext:humantext draft.md — 독자는 학원 원장, 상담 신청을 받는 게 목적
```

독자와 목적을 같이 주면 결과가 좋아집니다. 안 주면 글에서 추론하고, 추론이 안 되면 두 가지까지 묻습니다. 파일로 주면 원본은 그대로 두고 `draft.humantext.md`로 저장합니다.

### 들어 있는 것

| | |
|---|---|
| `skills/humantext/SKILL.md` | 절차: 독자 정하기 → 내용 뽑기 → 새로 쓰기 → 대조 |
| `references/doc-types.md` | 공개 글, 안내문, 영업 메일, 발표 노트, 화면 문구 등 종류별 기준 |
| `references/patterns.md` | 한국어 AI 초안의 증상 15가지와 원인 |
| `references/meaning-check.md` | 뜻이 바뀌었는지 보는 여섯 가지 기준, 남겨야 하는 부정 |
| `scripts/humantext_diff.py` | 고치기 전후의 숫자·링크·영문 이름·부정·유보·조건 대조 |
| `scripts/humantext_lint.py` | 패턴 개수, 문장·문단 길이 분포, 종결 쏠림 |

스크립트는 Python 표준 라이브러리만 씁니다.

```bash
python3 skills/humantext/scripts/humantext_lint.py draft.md
python3 skills/humantext/scripts/humantext_lint.py draft.md --compare draft.humantext.md
python3 skills/humantext/scripts/humantext_diff.py draft.md draft.humantext.md --fail
```

lint 점수는 다시 읽어 볼 곳을 알려 줄 뿐, 글이 좋은지 판정하지 않습니다. 패턴이 0인데 독자가 할 일을 모르는 글은 실패입니다.

### 한계

- 패턴과 대조는 정해진 형태만 잡습니다. 형태소 분석기 없이 정규식으로 셉니다.
- 줄바꿈이 문장 중간에 들어간 원문(웹에서 복사한 글 등)은 문장 수와 종결 통계가 부정확합니다.
- 시험 지문, 법률 문서, 논문처럼 장르 문체가 정해진 글은 장르를 따르고, 말투 규칙은 적용하지 않습니다.

### 참고한 작업

- [nanaism/yomiyasu](https://github.com/nanaism/yomiyasu) (MIT): 뜻을 지키는 여섯 가지 기준과, 남겨야 하는 부정 대비를 한국어로 옮겼습니다.
- [blader/humanizer](https://github.com/blader/humanizer), [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop): 영어 AI 글 패턴 분류
- [epoko77-ai/im-not-ai](https://github.com/epoko77-ai/im-not-ai): 한국어 AI 글 패턴 분류

### 라이선스

MIT

## English

humantext is a Claude Code skill for Korean text. It rewrites AI-drafted Korean so that the person receiving it gets the point.

Most anti-slop skills keep a list of AI tells and fix each hit. humantext does not edit sentence by sentence. It decides who reads the text and what they should know or do afterwards, extracts the content (claims, numbers, conditions, actions) from the draft, drops the parts written for the requester (status reports, disclaimers, "here is how to read this"), writes the text again for the reader, and then checks with stdlib Python scripts that numbers, links, negations and conditions survived.

Why rewrite instead of edit: in our Korean style-transfer measurements (Oct 2026, 87 topics against 287 human exam passages), frontier models asked to polish a draft did not move its distance to the human distribution (1.41 → 1.40–1.50), and a model trained to remove AI tells cut tell scores by 85% on average but moved the overall style profile by only 12%. The output inherits the draft's structure.

Install:

```bash
claude plugin marketplace add schift-io/humantext
claude plugin install humantext@humantext
```

The skill, references and script output are in Korean. MIT licensed.

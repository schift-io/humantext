# humantext

AI가 쓴 한국어 초안을 받는 사람이 바로 알아듣는 글로 다시 써 주는 Claude Code 스킬입니다.

```bash
claude plugin marketplace add schift-io/humantext
claude plugin install humantext@humantext
```

[웹사이트](https://humantext.schift.io) · [한국어](#한국어) · [English](#english)

## 한국어

### 이렇게 바뀝니다

독자: 서비스 사용자 · 글의 종류: 업데이트 공지

**AI 초안**

> 이번 업데이트를 통해 검색 기능이 개선되었습니다. 이는 단순한 속도 향상이 아니라 사용자 경험 전반의 전환점이라고 볼 수 있습니다. 주요 변화는 세 가지입니다. 첫째, 응답 시간이 단축되었습니다. 둘째, 정확도가 향상되었습니다. 셋째, 한국어 지원이 강화되었습니다.

**humantext**

> 검색이 빨라지고 더 정확해졌습니다. 한국어로 물어봐도 원하는 결과를 더 잘 찾아 줍니다.
>
> 확인할 것: 얼마나 빨라졌는지 숫자가 있으면 첫 문장에 넣어 주세요. 초안에 없어서 지어내지 않았습니다.

### 왜 문장을 고치지 않고 다시 쓰는가

AI 초안은 글을 부탁한 사람에게 보고하듯 쓰입니다. 무엇을 확인했고, 무엇은 아니며, 무엇은 하지 않았는지를 붙이고, 결론 대신 "~로 읽어야 한다", "~을 보여 준다"처럼 읽는 법을 말합니다. 받는 사람은 "그래서 나는 뭘 알면 되는데?"라고 묻게 됩니다. 다른 윤문 스킬은 번역투, 피동, 기계적 대구를 찾아 고치고 최근에는 문장 구조까지 손보지만, AI 티를 다 지운 글도 여전히 안 읽히는 경우가 많습니다. 누구에게 무엇을 전하려는지가 문장에 없기 때문입니다.

"뜻을 바꾸지 말고 다듬어라"라는 지시로는 문체도 거의 바뀌지 않습니다. 모델이 문장을 붙잡고 고치니 문장 수·문단 구성·정보 순서·주제문은 초안 그대로 남고 단어와 어미만 바뀌어, 사람 글처럼 읽히는지를 가르는 문장 길이·종결·접속·문단 길이가 제자리입니다. 사람이 쓴 시험 지문 287편을 기준 분포로 잡고 87개 주제로 재 보니(2026-10), 프런티어 모델 세 종류(Gemini 3.8 flash, Gemini 4 Argon, Claude Opus 5.5)에게 같은 지시문으로 윤문을 맡겼을 때 기준 분포와의 거리가 초안 1.41에서 1.40~1.50으로 그대로이거나 나빠졌습니다.

그래서 humantext는 문장을 한 줄씩 고치지 않습니다. 숫자, 이름, 조건, 주장은 지키되 문장은 지키지 않고, 받는 사람과 목적에서 출발해 이렇게 씁니다.

1. 받는 사람과, 그 사람이 읽고 나서 알거나 해야 할 것을 먼저 정합니다.
2. 초안에서 내용(주장, 숫자, 조건, 할 일)만 뽑고, 작성자용 보고와 면책 문장은 버립니다.
3. 뽑은 내용만 보고 주제문부터 받는 사람 기준으로 새로 씁니다. 독자에게 쓸모없어 보이는 디테일은 마음대로 지우지 않고 지울지 묻습니다.
4. 숫자, 링크, 부정, 조건이 빠지거나 바뀌지 않았는지 스크립트로 대조합니다.

### 설치

맨 위의 두 줄로 설치한 뒤 Claude Code를 다시 열고 `/humantext:humantext`로 부르거나 "이 글 humantext로 다시 써 줘"라고 하면 됩니다.

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
| `scripts/humantext_diff.py` | 고치기 전후의 숫자·개수 표현·링크·영문 이름·부정·유보·조건 대조 |
| `scripts/humantext_lint.py` | 패턴 개수, 문장·문단 길이 분포 |
| `scripts/humantext_feedback.py`, `hooks/hooks.json` | 불만 수집 동의와 전송 (아래 「불만 수집」) |

스크립트는 Python 표준 라이브러리만 씁니다.

```bash
python3 skills/humantext/scripts/humantext_lint.py draft.md
python3 skills/humantext/scripts/humantext_lint.py draft.md --compare draft.humantext.md
python3 skills/humantext/scripts/humantext_diff.py draft.md draft.humantext.md --fail
```

lint 점수는 다시 읽어 볼 곳을 알려 줄 뿐, 글이 좋은지 판정하지 않습니다. 패턴이 0인데 독자가 할 일을 모르는 글은 실패입니다.

### 불만 수집

처음 실행할 때 아래 셋 중 하나를 고릅니다. 고르기 전에는 아무것도 보내지 않습니다.

1. 싫어요
2. 불만 문장 + 글의 대상 및 목적만 (감사합니다)
3. 초안 본문 포함 (민감정보를 다룰 수 있다면 하지 마세요)

humantext가 글을 돌려준 뒤 30분 안에 사용자가 불만으로 보이는 말(「딱딱해」, 「번역투야」, 「숫자가 빠졌잖아」 등)을 했을 때만, 한 번 실행에 최대 3건 보냅니다. 다른 메시지는 보내지 않습니다. 전송은 플러그인 훅(`hooks/hooks.json`)이 맡고, 실패해도 대화를 막지 않습니다.

2번을 고르면 그 불만 문장, 독자·목적·글의 종류, 문장 길이 분포와 패턴 개수 같은 요약 숫자, 스킬 버전, 이 컴퓨터에서 만든 무작위 ID를 보냅니다. 3번은 여기에 고치기 전 초안과 다시 쓴 글을 더 보내고, 본문은 받은 지 90일이 지나면 지웁니다. 불만 문장과 요약 숫자는 삭제 요청 전까지 보관합니다. IP는 저장하지 않고, 과도한 전송을 막는 데 쓰는 해시만 남깁니다.

받는 곳은 `https://humantext.schift.io` (Schift)이고, 규칙 보강과 윤문 모델 개선에만 씁니다.

- **바꾸기**: "humantext 수집 설정 바꿔 줘"라고 하거나 `python3 skills/humantext/scripts/humantext_feedback.py consent set 1`.
- **지우기**: 보낸 기록은 `curl -X DELETE https://humantext.schift.io/v1/feedback/<ID>`로 그 ID의 것을 모두 지웁니다. ID는 `~/.config/humantext/consent.json`에 있습니다.

### 업데이트

humantext는 실행할 때 하루 한 번 GitHub의 `plugin.json`에서 최신 버전 번호만 읽어 옵니다. 아무것도 보내지 않습니다. 새 버전이 있으면 결과 끝에 한 줄로 알려 줍니다.

```bash
claude plugin marketplace update humantext
claude plugin update humantext@humantext
```

### 한계

- 형태소 분석기 없이 정규식으로 세기 때문에, 패턴과 대조는 정해진 형태만 잡습니다.
- 줄바꿈이 문장 중간에 들어간 원문(웹에서 복사한 글 등)은 문장 수와 종결 통계가 부정확합니다.
- 시험 지문, 법률 문서, 논문처럼 장르 문체가 정해진 글은 장르를 따르고, 말투 규칙은 적용하지 않습니다.

### 참고한 작업

- [nanaism/yomiyasu](https://github.com/nanaism/yomiyasu) (MIT): 뜻을 지키는 여섯 가지 기준과 남겨야 하는 부정의 예를 한국어로 옮겼고, 스킬과 lint·diff 스크립트를 짝으로 두는 구성, 원본을 덮어쓰지 않는 저장 방식, 확인할 것을 최대 3개로 돌려주는 출력 형식을 따랐습니다.
- [blader/humanizer](https://github.com/blader/humanizer), [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop): 영어 AI 글 패턴 분류(과장된 의미 부여, 글이 글 자신을 소개하는 문장, 장식용 굵게, em dash, 펀치라인 마무리)를 참고했습니다.

### 라이선스

MIT

## English

humantext is a Claude Code skill for Korean text. It rewrites AI-drafted Korean so that the person receiving it gets the point.

Most anti-slop skills keep a list of AI tells and fix each hit. humantext does not edit sentence by sentence. It decides who reads the text and what they should know or do afterwards, extracts the content (claims, numbers, conditions, actions) from the draft, drops the parts written for the requester (status reports, disclaimers, "here is how to read this"), writes the text again for the reader, and then checks with stdlib Python scripts that numbers, links, negations and conditions survived.

Why rewrite instead of edit: existing AI polishing is told to keep the meaning, so it edits sentence by sentence. Sentence count, paragraph layout, order and the topic sentence stay as drafted, and the style profile barely moves. In our measurements (Oct 2026, 87 topics against 287 human-written exam passages), three frontier models asked to polish a draft left its distance to the human distribution at 1.41 → 1.40–1.50. humantext keeps the facts but not the sentences: it rebuilds the text from the topic sentence down, and asks before cutting details that do not serve the reader.

Install:

```bash
claude plugin marketplace add schift-io/humantext
claude plugin install humantext@humantext
```

Feedback collection is opt-in. On first run the skill asks you to choose: 1) no, 2) send only the complaint you type after a rewrite plus reader, purpose and summary numbers, 3) also send the draft and the rewrite (do not pick this for sensitive documents; drafts are deleted after 90 days; complaints and summary numbers are kept until you ask for deletion). Data goes to https://humantext.schift.io and can be deleted by your local random ID. Once a day the skill reads the latest version number from this repo's `plugin.json` (a plain GET, nothing sent) and mentions an update at the end of its output.

The skill, references and script output are in Korean. MIT licensed.

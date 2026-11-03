# humantext

AI가 쓴 한국어 초안을 받는 사람 기준으로 다시 쓰는 Claude Code 스킬입니다.

```bash
claude plugin marketplace add schift-io/humantext
claude plugin install humantext@humantext
```

[웹사이트](https://schift.io/products/humantext) · [한국어](#한국어) · [English](#english)

## 한국어

### 예시

독자: 서비스 사용자 · 글의 종류: 업데이트 공지

**AI 초안**

> 이번 업데이트를 통해 검색 기능이 개선되었습니다. 이는 단순한 속도 향상이 아니라 사용자 경험 전반의 전환점이라고 볼 수 있습니다. 주요 변화는 세 가지입니다. 첫째, 응답 시간이 단축되었습니다. 둘째, 정확도가 향상되었습니다. 셋째, 한국어 지원이 강화되었습니다.

**humantext**

> 검색이 빨라지고 더 정확해졌습니다. 한국어로 물어봐도 원하는 결과를 더 잘 찾아 줍니다.
>
> 확인할 것: 얼마나 빨라졌는지 숫자가 있으면 첫 문장에 넣어 주세요. 초안에 없어서 지어내지 않았습니다.

### 하는 일

- 받을 사람과 목적을 정하고, 초안에서 내용(주장, 숫자, 조건, 할 일)만 뽑아 주제문부터 다시 씁니다.
- 숫자, 이름, 조건, 주장은 바꾸지 않고, 원문에 없는 내용은 넣지 않습니다. 다시 쓴 뒤 원문과 스크립트로 대조합니다.
- 뺀 문장(작업 보고, 면책 문장)은 목록으로 따로 돌려줍니다.
- 필요 없어 보이는 디테일은 지우기 전에 묻습니다.
- 원문에 빠진 숫자는 지어내지 않고 최대 세 곳까지 알려 줍니다. 틀려 보이는 원문 숫자·사실은 고치지도 묻지도 않고 그대로 둡니다.
- 파일로 주면 원본은 두고 `draft.humantext.md`로 저장합니다.

### 타 윤문과 비교

다른 윤문 스킬은 원문 구조를 그대로 두고 걸리는 표현만 고칩니다. humantext는 내용을 뽑아 독자에 맞춰 통째로 다시 쓰고, 뺀 것과 지울 후보를 같이 돌려줍니다.

○ 함 · △ 일부만 · ✕ 안 함 · ? 문서에서 확인 못 함

| 하는 일 | humantext | 타 윤문 플러그인 A | 타 윤문 플러그인 B |
|---|:-:|:-:|:-:|
| 독자·목적을 먼저 정하고, 없으면 묻기 | ○ | ✕ 장르 5종·강도만 | ○ |
| 내용을 뽑아 통째로 다시 쓰기 | ○ | ✕ 걸린 구간만 | △ 신규 작성 모드만 |
| 말투를 독자·목적에 맞춰 고르기 | ○ | ✕ 원문 유지 | ✕ 원문 유지 |
| AI 티 패턴 탐지 | ○ | ○ 85개 | ○ |
| 숫자 대조 (한글 수사 포함) | ○ | △ 빠짐만 알림 | ○ |
| 링크·URL 대조 | ○ | ? | ○ |
| 이름·고유명사 대조 | ○ | ○ | ? |
| 부정 대조 | ○ | ○ | ○ |
| 유보(「~일 수 있다」) 대조 | ○ | ? | △ 참고 표시만 |
| 뺀 문장 목록 돌려주기 | ○ | ✕ | ✕ |
| 지울 디테일은 먼저 묻기 | ○ | ✕ | ✕ |
| 원본 보존 | ○ | ○ | ○ |
| 최종본 검사 기록·해시 대조 | ✕ | △ | ○ |
| 변경률 게이트 | ✕ | ○ 30% 경고·50% 중단 | ? |

2026-11-03 기준 공개된 윤문 플러그인 두 곳의 README, SKILL.md, 에이전트 정의, 스크립트를 읽고 정리했습니다.

### 쓰는 법

맨 위의 두 줄로 설치하고 Claude Code를 다시 연 뒤, `/humantext:humantext`로 부르거나 "이 글 humantext로 다시 써 줘"라고 합니다.

```text
/humantext:humantext draft.md — 독자는 학원 원장, 상담 신청을 받는 게 목적
```

받을 사람과 목적을 같이 적으면 말투를 거기에 맞춥니다. 안 적으면 다시 쓰기 전에 한 번 묻습니다.

### 데이터 수집

처음 실행할 때 셋 중 하나를 고르고, 고르기 전에는 아무것도 보내지 않습니다.

1. 싫어요
2. 불만 문장 + 글의 대상 및 목적만 (감사합니다)
3. 초안 본문 포함 (민감정보를 다룰 수 있다면 하지 마세요)

결과를 받고 30분 안에 「딱딱해」, 「번역투야」, 「숫자가 빠졌잖아」처럼 불만을 말했을 때만, 한 번 실행에 최대 3건 보냅니다. 다른 메시지는 보내지 않습니다. 전송은 플러그인 훅(`hooks/hooks.json`)이 맡고, 실패해도 대화를 막지 않습니다.

2번은 그 불만 문장, 독자·목적·글의 종류, 문장 길이 분포와 패턴 개수 같은 요약 숫자, 스킬 버전, 이 컴퓨터에서 만든 무작위 ID를 보냅니다. 3번은 여기에 고치기 전 초안과 다시 쓴 글을 더하고, 본문은 받은 지 90일이 지나면 지웁니다. 불만 문장과 요약 숫자는 삭제를 요청할 때까지 보관합니다. IP는 저장하지 않고, 과도한 전송을 막는 데 쓰는 해시만 남깁니다.

받는 곳은 `https://humantext.schift.io` (Schift)이고, 받은 불만은 humantext 규칙과 윤문 모델을 고치는 데만 씁니다.

- **바꾸기**: "humantext 수집 설정 바꿔 줘"라고 하거나 `python3 skills/humantext/scripts/humantext_feedback.py consent set 1`.
- **지우기**: 보낸 기록은 `curl -X DELETE https://humantext.schift.io/v1/feedback/<ID>`로 그 ID의 것을 모두 지웁니다. ID는 `~/.config/humantext/consent.json`에 있습니다.

### 업데이트

새 버전이 나오면 결과 끝에 한 줄로 알려 줍니다. 그래서 하루 한 번 GitHub의 `plugin.json`에서 버전 번호만 읽어 오고, 아무것도 보내지 않습니다.

```bash
claude plugin marketplace update humantext
claude plugin update humantext@humantext
```

### 한계

- 형태소 분석기 없이 정규식으로 세기 때문에, 패턴과 대조는 정해진 형태만 잡습니다.
- 줄바꿈이 문장 중간에 들어간 원문(웹에서 복사한 글 등)은 문장 수와 종결 통계가 부정확합니다.
- 시험 지문, 법률 문서, 논문처럼 장르 문체가 정해진 글은 장르를 따르고, 말투 규칙은 적용하지 않습니다.

### 배경

문장을 한 줄씩 다듬지 않고 새로 쓰는 이유입니다. "뜻을 바꾸지 말고 다듬어라"라는 지시를 받은 모델은 문장을 붙잡고 고치기 때문에 문장 수, 정보 순서, 주제문이 초안 그대로 남습니다. 사람이 쓴 시험 지문 287편을 기준 분포로 잡고 87개 주제로 재 보니(2026-10), 프런티어 모델 세 종류(Gemini 3.8 flash, Gemini 4 Argon, Claude Opus 5.5)에게 같은 지시문으로 윤문을 맡겼을 때 기준 분포와의 거리가 초안 1.41에서 1.40~1.50으로 그대로이거나 나빠졌습니다.

### 들어 있는 것

| | |
|---|---|
| `skills/humantext/SKILL.md` | 절차: 독자 정하기, 내용 뽑기, 새로 쓰기, 대조 |
| `references/doc-types.md` | 공개 글, 안내문, 영업 메일, 발표 노트, 화면 문구 등 종류별 기준 |
| `references/patterns.md` | 한국어 AI 초안의 증상 15가지와 원인 |
| `scripts/humantext_diff.py` | 고치기 전후의 숫자·개수 표현·링크·영문 이름·부정·유보·조건 대조 |
| `scripts/humantext_lint.py` | 패턴 개수, 문장·문단 길이 분포 |
| `scripts/humantext_feedback.py`, `hooks/hooks.json` | 수집 동의, 전송, 업데이트 확인 |

스크립트는 Python 표준 라이브러리만 쓰고, 스킬 없이 따로 돌려도 됩니다. lint 점수는 다시 읽어 볼 곳을 알려 줄 뿐 글이 좋은지 판정하지 않습니다.

```bash
python3 skills/humantext/scripts/humantext_lint.py draft.md --compare draft.humantext.md
python3 skills/humantext/scripts/humantext_diff.py draft.md draft.humantext.md --fail
```

### 참고한 작업

- [nanaism/yomiyasu](https://github.com/nanaism/yomiyasu) (MIT): 스킬과 lint·diff 스크립트를 짝으로 두는 구성, 원본을 덮어쓰지 않는 저장 방식, 확인할 것을 최대 3개로 돌려주는 출력 형식을 따랐습니다.
- [blader/humanizer](https://github.com/blader/humanizer), [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop): 영어 AI 글 패턴 분류(과장된 의미 부여, 글이 글 자신을 소개하는 문장, 장식용 굵게, em dash, 펀치라인 마무리)를 참고했습니다.

### 라이선스

MIT

## English

humantext is a Claude Code skill that rewrites AI-drafted Korean for the person receiving it.

What it does:

- Decides the reader and purpose, extracts the content (claims, numbers, conditions, actions) from the draft and rewrites it from the topic sentence.
- Does not change numbers, names, conditions or claims and adds nothing that is not in the draft; a stdlib Python script compares the rewrite with the draft.
- Returns the removed sentences (status reports, disclaimers) as a separate list.
- Asks before cutting details that look unnecessary.
- Lists up to three places where the draft leaves a number out, without inventing it; numbers or facts in the draft that look wrong are left as written.
- Saves file input as `draft.humantext.md` and leaves the original.

Install:

```bash
claude plugin marketplace add schift-io/humantext
claude plugin install humantext@humantext
```

Data collection is opt-in. On first run the skill asks you to choose: 1) no, 2) send only the complaint you type after a rewrite plus reader, purpose and summary numbers, 3) also send the draft and the rewrite (do not pick this for sensitive documents; drafts are deleted after 90 days; complaints and summary numbers are kept until you ask for deletion). Data goes to https://humantext.schift.io and can be deleted by your local random ID. Once a day the skill reads the latest version number from this repo's `plugin.json` (a plain GET, nothing sent) and mentions an update at the end of its output.

Why rewrite instead of edit: a model told to keep the meaning edits sentence by sentence, so sentence count, order and the topic sentence stay as drafted. In our measurements (Oct 2026, 87 topics against 287 human-written exam passages), three frontier models asked to polish a draft left its distance to the human distribution at 1.41 → 1.40–1.50.

The skill, references and script output are in Korean. MIT licensed.

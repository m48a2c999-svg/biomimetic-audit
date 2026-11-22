# biomimetic-audit

건축 외피 연구에서 생체모방 주장의 비판적 검토 — 문헌 판정 자료, 분석 스크립트, 연구 홈페이지.

- 홈페이지: https://m48a2c999-svg.github.io/biomimetic-audit/ (`docs/`)
- `audit/fetch_openalex.py`, `audit/fetch_s2.py`, `audit/merge.py` — 문헌 수집(OpenAlex, Semantic Scholar)과 병합(530건)
- `audit/screening.json` — 레코드별 선별 결정
- `audit/codebook.md` — 판정 기준표
- `audit/manual_codes_all.json` — 193편 정독 판정(재점검 반영), `audit/recheck_log.json` — 재점검으로 바뀐 판정
- `audit/levels.json`, `audit/results.json` — 근거 수준과 분석 결과(`audit/analyze.py`)
- `audit/agreement.json` — 사전어 자동 판정과 정독 판정의 일치도(`audit/agreement.py`)
- `audit/fulltext_codes.json`, `audit/fulltext_compare.json` — 원문 표본 18편 재판정
- `refs/` — 참고문헌 서지 대조(Crossref·OpenAlex)

판정은 한 판정자의 초록 판정이며, 비율은 원문에 있는 근거의 하한으로 읽어야 한다.

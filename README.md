# biomimetic-audit

건축 외피 연구에서 생체모방 주장의 비판적 검토 — 문헌 판정 자료, 분석 스크립트, 사례 계산, 연구 홈페이지.

홈페이지: https://m48a2c999-svg.github.io/biomimetic-audit/ (`docs/`)

## 1차 연구 판정(193편)
- `audit/fetch_openalex.py`, `audit/fetch_s2.py`, `audit/merge.py` — 문헌 수집(OpenAlex, Semantic Scholar)과 병합(530건)
- `audit/screening.json` — 레코드별 선별 결정
- `audit/codebook.md` — 판정 기준표
- `audit/manual_codes_all.json` — 193편 정독 판정(재점검 반영), `audit/recheck_log.json` — 재점검으로 바뀐 판정
- `audit/levels.json`, `audit/results.json` — 근거 수준과 분석 결과(`audit/analyze.py`)
- `audit/agreement.json` — 사전어 자동 판정과 정독 판정의 일치도(`audit/agreement.py`)
- `audit/fulltext_codes.json`(1차 18편), `audit/fulltext_codes2.json`(2차 43편), `audit/fulltext_compare.json` — 원문 표본 61편 재판정(`audit/fulltext_compare.py`). 원문은 저장하지 않으며 판정값만 공개한다.
- `audit/sensitivity.py`, `audit/sensitivity.json` — 표본 범위·판정 규칙·판정 자료를 바꾼 민감도 분석
- `audit/second_coder/` — 두 번째 판정자용 판정지(40편)와 일치도 계산 스크립트(`agreement2.py`)

## 리뷰 담론(71편)과 대표 건물(9건)
- `audit/review_codebook.md` — 리뷰 판정 기준
- `audit/review_codes.json` — 연구자 판정(coder1), 언어 모델 기반 보조 판정(coder2), 합의값(final), 첫 판정의 κ
- `audit/review_analysis.py`, `audit/review_results.json` — 리뷰 분석
- `audit/buildings.json` — 대표 건물·실물 사례의 판정과 근거 자료

## 사례 계산: 원리에 충실한 솔방울 전이
- `sim/sb/sim/build.py`(hygro 제어: 외기 상대습도 40% 이하 개방·85% 이상 폐쇄, 60분 1차 지연), `sim/sb/sim/scen.py`(HB·HL·HV, 민감도 HBN·HB2)
- `.github/workflows/bioh.yml`, `sim/sb/run_bioh.sh` — EnergyPlus 23.2.0 계산(257동 × 기준안·블라인드·수평 루버·수직 루버)
- `sim/sb/results_bioh/` — 계산 결과, `audit/bioh_analysis.py`, `audit/bioh_results.json` — 집계

## 참고문헌
- `refs/` — 참고문헌 서지 대조(Crossref·OpenAlex)

1차 연구 판정은 한 판정자의 초록 판정이며, 비율은 원문에 있는 근거의 하한으로 읽어야 한다.

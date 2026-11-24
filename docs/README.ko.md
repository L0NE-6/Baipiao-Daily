# Baipiao Daily

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · **한국어** · [Português (BR)](README.pt-BR.md)

Baipiao 일일 체크인을 여러 계정으로 실행하고, 체크인 전후 상태를 다시 읽어
확인합니다.

## 흐름

```text
GET /api/overview
  -> POST /api/checkin: Bearer bitapi_session, body 없음
  -> GET /api/overview 다시 읽기
```

다음 조건을 모두 만족할 때만 `CLAIMED`로 보고합니다.

- 체크인 응답 `claimed=true`;
- `reward>0`;
- 두 번째 읽기에서 `checkin.checked_in=true`.

## 자격 증명

여러 계정은 `BAIPIAO_ACCOUNTS`에 다음 형식으로 설정합니다.

```text
label|bitapi_session
```

단일 계정은 `BAIPIAO_SESSION`을 사용합니다. 두 번째 값은 JWT 또는
`bitapi_session`이 포함된 Cookie 헤더일 수 있습니다.

## 실행

```powershell
python -m pip install -r requirements.txt
$env:BAIPIAO_SESSION = "<bitapi_session>"
python baipiao_daily.py
```

상태만 조회:

```powershell
python baipiao_daily.py --query
```

두 번째 계정만 실행:

```powershell
python baipiao_daily.py --only 2
```

## 결과

| 결과 | 의미 |
| :--- | :--- |
| `CLAIMED` | 새 보상과 상태 반전을 확인했습니다. |
| `ALREADY_CLAIMED` | 오늘 체크인이 이미 기록되어 있습니다. |
| `AVAILABLE` | 조회 모드에서 체크인 가능 상태를 확인했습니다. |
| `INACTIVE` | 활성 일일 체크인이 없습니다. |
| `CLAIM_NOT_APPLIED` | 요청은 성공했지만 재조회 값이 false입니다. |
| `CREDIT_UNCONFIRMED` | 보상이 없거나 양수가 아닙니다. |
| `AUTH_EXPIRED` | `bitapi_session`이 유효하지 않습니다. |
| `BLOCKED` | HTML 인증 페이지가 반환되었습니다. |
| `CONFIG_ERROR` | 환경 변수 또는 URL이 잘못되었습니다. |

## Actions

push 시 테스트하고, 예약 또는 수동 실행 시 체크인 후 JSON 보고서를
업로드합니다. Secret에 `BAIPIAO_ACCOUNTS` 또는 `BAIPIAO_SESSION`을
설정하세요.

## 테스트

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check baipiao_daily.py tests
```

모든 테스트는 가짜 응답과 세션만 사용합니다.

## 개인정보

JWT, Cookie, 보고서, 스크린샷, 계정 정보를 커밋하지 마세요. 스크립트는 마스킹된
계정 라벨만 출력합니다.

## 라이선스

MIT. `LICENSE`, `NOTICE.md`, `THIRD_PARTY_NOTICES.md`를 참고하세요.

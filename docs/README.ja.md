# Baipiao Daily

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · **日本語** · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)
> バージョン：**v1.0.0**（2026-11-24）

Baipiao の毎日チェックインを、複数アカウント分離と前後状態の再読取付きで
実行します。

## 処理

```text
GET /api/overview
  -> POST /api/checkin: Bearer bitapi_session、body なし
  -> GET /api/overview を再実行
```

次の条件をすべて満たす場合だけ `CLAIMED` になります。

- チェックイン応答が `claimed=true`；
- `reward>0`；
- 再読取した `checkin.checked_in=true`。

## 認証情報

複数アカウントは `BAIPIAO_ACCOUNTS` に次の形式で設定します。

```text
label|bitapi_session
```

単一アカウントは `BAIPIAO_SESSION` を使用します。2 列目には JWT または
`bitapi_session` を含む Cookie ヘッダーを指定できます。

## 実行

```powershell
python -m pip install -r requirements.txt
$env:BAIPIAO_SESSION = "<bitapi_session>"
python baipiao_daily.py
```

状態だけ確認:

```powershell
python baipiao_daily.py --query
```

2 番目のアカウントだけ実行:

```powershell
python baipiao_daily.py --only 2
```

## 結果

| 結果 | 意味 |
| :--- | :--- |
| `CLAIMED` | 今回の報酬と状態反転を確認。 |
| `ALREADY_CLAIMED` | 今日はすでにチェックイン済み。 |
| `AVAILABLE` | クエリモードで受取可能を確認。 |
| `INACTIVE` | 有効な毎日チェックインがない。 |
| `CLAIM_NOT_APPLIED` | 応答は成功だが再読取が false。 |
| `CREDIT_UNCONFIRMED` | 報酬がない、または正数でない。 |
| `AUTH_EXPIRED` | `bitapi_session` が無効。 |
| `BLOCKED` | HTML 検証ページが返った。 |
| `CONFIG_ERROR` | 環境変数または URL が不正。 |

## Actions

push 時にテストし、スケジュールまたは手動実行時にチェックインして JSON
レポートをアップロードします。Secret に `BAIPIAO_ACCOUNTS` または
`BAIPIAO_SESSION` を設定してください。

## テスト

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check baipiao_daily.py tests
```

テストはすべて偽の応答とセッションを使用します。

## プライバシー

JWT、Cookie、レポート、スクリーンショット、アカウント情報をコミットしないで
ください。出力されるアカウント名はマスクされます。

## ライセンス

MIT。`LICENSE`、`NOTICE.md`、`THIRD_PARTY_NOTICES.md` を参照してください。

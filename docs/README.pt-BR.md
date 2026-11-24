# Baipiao Daily

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · **Português (BR)**
> Versão: **v1.0.0** (2026-11-24)

Check-in diário do Baipiao com isolamento de múltiplas contas e leitura
estrita do estado antes e depois da operação.

## Fluxo

```text
GET /api/overview
  -> POST /api/checkin com Bearer bitapi_session e sem body
  -> GET /api/overview novamente
```

O resultado `CLAIMED` só é emitido quando:

- a resposta do check-in contém `claimed=true`;
- `reward>0`;
- a segunda leitura contém `checkin.checked_in=true`.

## Credenciais

Várias contas usam `BAIPIAO_ACCOUNTS`:

```text
label|bitapi_session
```

Uma conta pode usar `BAIPIAO_SESSION`. O segundo campo aceita o JWT ou um
Cookie header que contenha `bitapi_session`.

## Execução

```powershell
python -m pip install -r requirements.txt
$env:BAIPIAO_SESSION = "<bitapi_session>"
python baipiao_daily.py
```

Somente consulta:

```powershell
python baipiao_daily.py --query
```

Somente a segunda conta:

```powershell
python baipiao_daily.py --only 2
```

## Resultados

| Resultado | Significado |
| :--- | :--- |
| `CLAIMED` | Recompensa e mudança de estado confirmadas. |
| `ALREADY_CLAIMED` | O check-in de hoje já estava registrado. |
| `AVAILABLE` | O modo de consulta confirmou disponibilidade. |
| `INACTIVE` | Não há check-in diário ativo. |
| `CLAIM_NOT_APPLIED` | A requisição retornou sucesso, mas a leitura continua false. |
| `CREDIT_UNCONFIRMED` | A recompensa está ausente ou não é positiva. |
| `AUTH_EXPIRED` | `bitapi_session` inválido ou expirado. |
| `BLOCKED` | O site retornou uma página HTML de verificação. |
| `CONFIG_ERROR` | Variáveis de ambiente ou URL inválidas. |

## Actions

O workflow testa no push e executa o check-in no agendamento ou disparo manual,
enviando um relatório JSON como artifact. Configure `BAIPIAO_ACCOUNTS` ou
`BAIPIAO_SESSION` como Secret.

## Testes

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check baipiao_daily.py tests
```

Todos os testes usam respostas e sessões simuladas.

## Privacidade

Não faça commit de JWT, cookies, relatórios, capturas de tela ou dados da conta.
O script imprime apenas o rótulo mascarado da conta.

## Licença

MIT. Consulte `LICENSE`, `NOTICE.md` e `THIRD_PARTY_NOTICES.md`.

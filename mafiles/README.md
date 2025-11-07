# Папка для .maFile файлов

Эта папка предназначена для хранения .maFile файлов от Steam Desktop Authenticator (SDA).

## Как использовать

### Шаг 1: Экспортируйте .maFile из SDA

1. Откройте Steam Desktop Authenticator
2. Выберите аккаунт
3. Нажмите "Export" → "Export account files (.maFile)"
4. Сохраните файл в эту папку `mafiles/`

### Шаг 2: Добавьте аккаунт в accounts.txt

В файле `accounts/accounts.txt` используйте формат:

```
username:password:filename.maFile
```

**Примеры:**

```
mysteam:mypass123:mysteam.maFile
user2:pass456:user2.maFile
```

Или с полным путем:

```
mysteam:mypass123:mafiles/mysteam.maFile
```

## Автоматический поиск

Программа автоматически ищет .maFile в следующих местах:

1. Точный путь как указано
2. В папке `mafiles/`
3. Относительно папки `accounts/`

## Безопасность

**ВАЖНО:**
- .maFile содержат секретные ключи для доступа к вашему Steam аккаунту
- Папка `mafiles/` автоматически добавлена в `.gitignore`
- НИКОГДА не публикуйте эти файлы в Git или публичных местах
- Храните резервные копии в надежном месте

## Структура .maFile

Для справки, .maFile имеет следующую структуру:

```json
{
  "shared_secret": "ваш_shared_secret",
  "serial_number": "...",
  "revocation_code": "...",
  "uri": "...",
  "server_time": ...,
  "account_name": "...",
  "token_gid": "...",
  "identity_secret": "...",
  "secret_1": "...",
  "status": ...,
  "device_id": "...",
  "fully_enrolled": true,
  "Session": {
    "SessionID": "...",
    "SteamLogin": "...",
    "SteamLoginSecure": "...",
    "WebCookie": "...",
    "OAuthToken": "...",
    "SteamID": ...
  }
}
```

Программа использует только поле `shared_secret` для генерации кодов Steam Guard.

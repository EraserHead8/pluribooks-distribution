# PluriBooks: сайт и обновления

Сайт раздаёт только статические страницы и JSON-описания выпусков. APK хранится в GitHub Releases. На данный момент активен только тестовый канал (`preview`); `stable` зарезервирован и пуст. Android package ID остаётся `app.polka`, чтобы не терять данные установленных тестовых версий.

## Локальная проверка

```bash
python3 tools/validate_manifests.py
python3 -m unittest discover -s tools -p 'test_*.py' -q
node --check site/app.js
python3 -m http.server 8080 --directory site
```

Открыть `http://localhost:8080`. В CI также проверяются JSON Schema (`schemas/`) и отсутствие APK/ключей в `site/`.

## Выпуск тестовой версии

1. Собрать APK Android-приложения с `versionCode` больше предыдущего и **той же подписью**, что текущие тестовые сборки. Никогда не коммитить ключ подписи.
2. Локально проверить фактические package ID, `versionName`, `versionCode`, `minSdk` и сертификат:

   ```bash
   python3 tools/verify_apk.py --apk /absolute/path/app.apk --version-name 0.2.73 \
     --aapt /absolute/path/to/aapt --apksigner /absolute/path/to/apksigner
   ```

3. Создать **prerelease** в GitHub с тегом вида `v0.2.73`, прикрепить ровно один APK и опубликовать. Процесс `.github/workflows/publish-preview.yml` проверит загруженный APK и только после этого запишет версию, размер, SHA-256 и ссылку в `site/releases/preview.json`, а историю — в `preview-versions.json`.
4. Дождаться успешной проверки GitHub Actions и публикации сайта; проверить ссылку и SHA-256 на живой странице. Пока приложение не получило встроенный модуль обновления, APK скачивается с сайта вручную.

Ни черновик, ни непротестированный APK, ни release без APK, ни сборка с другой подписью не попадут в ленту обновлений. Стабильный канал не продвигается автоматически.

## Размещение сайта

`wrangler.jsonc` описывает Cloudflare Workers Static Assets. Репозиторий подключается к Cloudflare Workers Builds; ветка `main`, команда сборки отсутствует, команда развертывания — `npx wrangler deploy`. Для ручного развёртывания после настройки аккаунта: `npm install && npx wrangler deploy`.

Cloudflare хранит малые страницы и JSON, GitHub — крупные APK. Не размещать APK в `site/`. Для первого публичного URL можно использовать бесплатный `*.workers.dev`; собственный домен подключается отдельно.

## Подпись и сохранность данных

Установленные тестовые версии `app.polka` подписаны текущим debug-сертификатом. Обновление поверх них требует тот же package ID и сертификат. Замена сертификата на постоянный релизный не является бесшовным обновлением; понадобится отдельно спланированная миграция/экспорт библиотеки. Стабильный канал остаётся пустым до такого решения и реального тестирования.

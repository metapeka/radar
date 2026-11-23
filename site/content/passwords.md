# Менеджеры паролей

> Один мастер-пароль вместо десятков повторяющихся. Менеджер закрывает кражи из баз сайтов и подбор пароля, но не спасает от фишинга, заражённого устройства и потери аварийного доступа.

::: {.callout .warning}
Потеря мастер-пароля и аварийного ключа означает потерю хранилища: у облачных менеджеров восстановления нет. Аварийный доступ храните вне менеджера — на бумаге или на отдельном носителе.
:::

## Что защищено, а что нет

| Объект | Защита | Комментарий |
|---|---|---|
| Пароли в хранилище | Шифрование на устройстве | Провайдер видит шифротекст, а не пароли |
| Мастер-пароль | Не хранится у провайдера | 1Password добавляет к нему Secret Key |
| Повторно использованные пароли | Не защищены | Менеджер помогает найти их и заменить |
| Фишинг | Частично | Автозаполнение не сработает на чужом домене, но привычка вводить пароль руками возвращает риск |
| Разблокированное устройство | Не защищено | Автоблокировка менеджера и блокировка ОС обязательны |

## Как выбрать

- **Облачный** (Bitwarden, 1Password) — синхронизация и аварийный доступ из коробки. Цена — доверие провайдеру и аккаунт как единая точка отказа.
- **Локальный** (KeePassXC) — файл под вашим контролем, без аккаунта. Синхронизацию и резервные копии делаете сами.

## Bitwarden

[Чек-лист на сайте](https://metapeka.github.io/whatsapp-security-research/passwords.html#bitwarden) <!--services:bitwarden-->

## 1Password {#1password}

[Чек-лист на сайте](https://metapeka.github.io/whatsapp-security-research/passwords.html#1password) <!--services:onepassword-->

## KeePassXC

[Чек-лист на сайте](https://metapeka.github.io/whatsapp-security-research/passwords.html#keepassxc) <!--services:keepassxc-->

## Источники

| Что | Первоисточник |
|---|---|
| Bitwarden: двухшаговая аутентификация | [Two-Step Login](https://bitwarden.com/help/setup-two-step-login) |
| Bitwarden: алгоритмы вывода ключа | [Encryption Key Derivation](https://bitwarden.com/help/kdf-algorithms) |
| Bitwarden: автоблокировка | [Automatic Logout or Lock](https://bitwarden.com/help/vault-timeout) |
| 1Password: двухфакторная аутентификация | [Turn on two-factor authentication](https://support.1password.com/two-factor-authentication) |
| 1Password: аварийный набор | [Get to know your Emergency Kit](https://support.1password.com/emergency-kit) |
| 1Password: Secret Key | [Find your Secret Key](https://support.1password.com/secret-key) |
| 1Password: автоблокировка | [Unlock and auto-lock settings](https://support.1password.com/unlock-auto-lock) |
| KeePassXC: руководство | [User Guide](https://keepassxc.org/docs/KeePassXC_UserGuide) |

## См. также

- [Модель угроз](threat-model.html) — от кого защищаемся и какой профиль риска.
- [Реагирование](incident-response.html) — что делать, если аккаунт уже угнали.
- [iOS](ios.html) и [Android](android.html) — блокировка устройства и автозаполнение.

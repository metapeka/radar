# Сводка: 17–23 ноября 2026

> Что изменилось в безопасности мессенджеров и iPhone за неделю — и какие действия из-за этого поменялись.

::: {.callout .note}
**Как читать.** В сводку попадает только то, что меняет рекомендации на сайте: новая уязвимость, исправление, изменение практики. Дата среза — 23 ноября 2026. Статусы: **исправлено**, **не подтверждено**, **наблюдение**.
:::

## Главное за неделю

| Дата | Что | Кому | Действие |
|---|---|---|---|
| 15.10.2026 | Telegram: ZDI-26-757 / CVE-2026-111105, rlottie, RCE, CVSS 7.0 | пользователям Telegram | обновиться; не открывать подозрительные файлы и страницы |
| 17.11.2026 | iPhone: CVE-2026-65339, запись звука после запрета микрофона | iPhone и iPad | iOS 26.6.1+ или 18.7.11+ |
| 17.11.2026 | Telegram: заявлен обход sandbox виджетов на Android 13.2.2; Kaspersky — WebRAT | Android | обновиться; не запускать виджеты незнакомых ботов |
| 20.11.2026 | WhatsApp: три CVE — утечка IP, SQL-инъекция, проверка сертификата | Android, iOS, Mac | Android 2.26.35.74+, iOS 2.26.24.72+ |
| 20.11.2026 | CISA KEV: Apache Roller, Cisco Expressway, SAP NetWeaver, VMware vCenter | администраторам | патч до 23.11.2026 |
| 20.11.2026 | Signal: новых CVE после 20.10.2026 нет; CVE-2026-113380 закрыт | пользователям Signal | RingRTC 2.72.0+ |
| апрель 2026 | MAX: 213 уязвимостей по bug bounty, публичного списка нет | пользователям MAX | считать риск неизвестным, не хранить чувствительное |

Две поправки к тому, что писали в новостях:

- **ZDI-26-757** — не zero-click с оценкой 9.8. В опубликованном advisory CVSS 7.0 и требуется взаимодействие: открыть файл или страницу.
- **Telegram-виджеты** — заявление NebuSec, а не подтверждённая уязвимость с CVE. Демонстрация на тестовом сервере, детали не раскрыты. Но Kaspersky сообщает о реальной доставке WebRAT — обновление и отказ от виджетов незнакомых ботов оправданы.

## Что делать сейчас

### P0

- [ ] iPhone/iPad: обновиться до iOS 26.6.1+ или 18.7.11+.
- [ ] WhatsApp на Android: версия 2.26.35.74 или новее.
- [ ] Telegram: последняя версия; виджеты незнакомых ботов не запускать.
- [ ] Signal: RingRTC 2.72.0+ (обновление приложения).
- [ ] Администраторам: закрыть четыре KEV-уязвимости до 23.11.2026.
- [ ] MAX: новых подтверждённых CVE нет, но 213 находок bug bounty не раскрыты — чувствительное там не хранить.

### P1

- [ ] Проверить, что автообновления включены на телефонах и планшетах.
- [ ] Пересоздать старые HTML-экспорты Telegram, сделанные до 7.0.1.
- [ ] Для источников и чувствительного — Signal, не MAX и не Telegram-облако.

## Как обновляется сводка

Раз в неделю, по понедельникам, 30–40 минут:

1. **CISA KEV** — JSON с сайта CISA: какие уязвимости добавили за неделю, есть ли дедлайн.
2. **CVE.org / MITRE** — новые записи по WhatsApp, Telegram, Signal, Apple, Google.
3. **Advisories вендоров** — WhatsApp Security Advisories, Signal Security, Telegram changelog, Apple Security Releases.
4. **Профильные источники** — The Hacker News, SecurityLab, Xakep, «Коммерсантъ»; только как наводка, не как доказательство.
5. **Проверка** — есть ли CVE, затронутые версии, статус исправления, следы эксплуатации.
6. **Запись** — добавить строку в таблицу, обновить дату среза, при изменении рекомендации поправить страницу мессенджера или платформы.
7. **Провенанс** — снять снапшот источника по правилам `provenance/README.md`.

Правила: не публиковать слух без статуса «не подтверждено»; не смешивать CVE и заявления исследователей; не переносить в сводку всё подряд — только то, что меняет действие читателя.

## Источники

| Дата | Работа | Что даёт | Ссылка |
|---|---|---|---|
| 10.04.2026 | iXBT / «Коммерсантъ» | 213 уязвимостей MAX по bug bounty | [ixbt.com](https://www.ixbt.com/news/2026/04/10/belye-hakery-nashli-213-ujazvimostej-v-messendzhere-max-no-v-centre-bezopasnosti-platformy-zajavili-chto-dannye.html) |
| 15.10.2026 | ZDI | ZDI-26-757, CVE-2026-111105 | [zerodayinitiative.com](https://www.zerodayinitiative.com/advisories/ZDI-26-757) |
| 17.11.2026 | The Hacker News | Виджеты Telegram и WebRAT | [thehackernews.com](https://thehackernews.com/2026/11/researchers-claim-two-rce-exploits-that.html) |
| 17.11.2026 | The Hacker News | iPhone CVE-2026-65339 | [thehackernews.com](https://thehackernews.com/2026/11/researchers-detail-iphone-flaw-that-let.html) |
| 20.11.2026 | The Hacker News | Три CVE WhatsApp | [thehackernews.com](https://thehackernews.com/2026/11/whatsapp-patches-3-security-flaws.html) |
| 20.11.2026 | CISA | Четыре KEV-уязвимости, дедлайн 23.11 | [cisa.gov](https://www.cisa.gov/news-events/alerts/2026/11/20/cisa-adds-four-known-exploited-vulnerabilities-catalog) |
| 20.10.2026 | MITRE, CVE-2026-113380 | RingRTC в Signal | [cve.org](https://www.cve.org/CVERecord?id=CVE-2026-113380) |

## См. также

- [Сравнение мессенджеров](comparison.html) — кто что отдаёт и какие CVE были.
- [WhatsApp](whatsapp.html), [Telegram](telegram.html), [Signal](signal.html), [MAX](max.html).
- [iOS](ios.html) — версии и Lockdown Mode.
- [Методика](methodology.html) — уровни уверенности.

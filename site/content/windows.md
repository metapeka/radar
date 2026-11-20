# Windows

> На Windows чаще всего угоняют не «вирусом», а стилером, который забирает профиль браузера вместе с сессией WhatsApp Web.

## Механизмы

| Механизм | Где включить | Что даёт | Приоритет |
|---|---|---|---|
| BitLocker / Device Encryption | Settings → Privacy & security → Device encryption | Шифрование диска | P0 |
| Secure Boot + TPM 2.0 | UEFI, `msinfo32` | Цепочка доверия от прошивки | P0 |
| Windows Hello | Settings → Accounts → Sign-in options | Ключи в TPM, устойчивость к фишингу | P0 |
| UAC | Control Panel → User Accounts | Подтверждение повышения прав | P0 |
| Defender + ASR | Windows Security → Virus & threat protection | Поведенческие правила против LSASS-кражи, WMI-персистентности | P0 |
| Controlled Folder Access | Virus & threat protection → Ransomware protection | Защита документов от шифрования | P0 |
| Credential Guard | Windows Security → Device security | Изоляция хэшей и тикетов | P1 |
| Smart App Control | App & browser control | Блокировка неподписанных и безрепутационных файлов | P1 |
| Administrator Protection | Windows Security → Account protection (26H2) | Повышение прав через Hello, а не «вечный админ» | P1 |
| Recall | Privacy & security → Recall | **Выключить** на общих машинах | P1 |

## Автозагрузка и постоянные механизмы

| Место | Как проверить |
|---|---|
| Run / RunOnce | `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`, `HKLM\...\Run` |
| Startup-папки | `%APPDATA%\...\Startup`, `%ProgramData%\...\Startup` |
| Планировщик | `taskschd.msc`, `schtasks /query /v /fo LIST` |
| Службы | `services.msc`, `Get-Service` |
| WMI-подписки | `Get-WmiObject -Namespace root\subscription -Class __EventFilter` |
| IFEO | `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options` |
| AppInit_DLLs | `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows` |
| Winlogon | `...\Winlogon` → `Userinit`, `Shell` |
| Расширения браузера | `edge://extensions`, `chrome://extensions`, `about:addons` — во **всех** профилях |

Практика: один проход Autoruns с включённой проверкой подписей закрывает 90% вопросов «что тут запускается».

## Инструменты

| Инструмент | Что делает |
|---|---|
| Autoruns | Единый список всех точек автозапуска с проверкой подписи |
| Process Explorer | Процессы, handles, подписи, родительские связи |
| TCPView | Активные соединения |
| Process Monitor | Файлы и реестр в реальном времени |
| Defender Offline | Сканирование вне загруженной ОС |
| KVRT | Вторичный сканер для новых образцов |
| `Get-AuthenticodeSignature`, `sigcheck` | Проверка подписи файла |

## Мессенджеры на Windows

| Приложение | Где данные | Чем защищать |
|---|---|---|
| Signal Desktop | `%APPDATA%\Signal` | BitLocker; ключ через DPAPI |
| Telegram Desktop | `%APPDATA%\Telegram Desktop\tdata` | Локальный код-пароль + BitLocker |
| WhatsApp Desktop | `%LOCALAPPDATA%\Packages\...WhatsAppDesktop...\LocalState` | BitLocker; отдельного пароля нет |

Ключевой момент: шифрование диска защищает только выключенный компьютер. Пока вы вошли в систему, стилер читает всё, что читаете вы, — включая расшифрованную базу Signal и `tdata`.

## Чек-лист

### P0

- [ ] BitLocker (или Device Encryption) включён, ключ сохранён вне устройства.
- [ ] Secure Boot включён, TPM присутствует.
- [ ] UAC не в режиме «Never notify».
- [ ] Defender активен: облачная защита, PUA, ASR-правила.
- [ ] Controlled Folder Access включён (сначала в Audit, чтобы не сломать бэкапы).
- [ ] RDP выключен, если не нужен.
- [ ] SMBv1 отключён.
- [ ] Автозагрузка проверена (Autoruns, включая подписи).

### P1

- [ ] Windows Hello вместо пароля; отдельная учётная запись администратора.
- [ ] Credential Guard (если редакция позволяет).
- [ ] Smart App Control — на домашней машине.
- [ ] Recall выключен.
- [ ] Обновления ОС и приложений автоматические.
- [ ] Расширения браузера проверены во всех профилях.

### P2

- [ ] Sysmon (встроен в 26H2) для истории событий.
- [ ] Отдельный локальный пользователь для сомнительных файлов.
- [ ] Проверка задач планировщика раз в квартал.

## Пределы

- Загрузочный имплант и подмена прошивки не видны из ОС; косвенные признаки — Measured Boot и значения PCR в TPM.
- Стилер, отработавший под пользователем, не оставляет надёжных следов.
- «Антивирус молчит» ничего не значит: стилеры обходят сигнатуры и живут в пользовательском профиле.
- Хранить пароли в браузере на общей машине — то же, что оставить их на стикере.

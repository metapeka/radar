# Linux

> На настольном Linux главный вектор — не руткит, а кража сессионных данных из домашнего каталога: `tdata`, профиль Signal, IndexedDB WhatsApp Web.

## Механизмы

| Механизм | Команда / место | Что даёт | Приоритет |
|---|---|---|---|
| LUKS2 | `cryptsetup luksDump /dev/nvme0n1p3` | Шифрование диска | P0 |
| Secure Boot | `mokutil --sb-state`, `bootctl status` | Подпись загрузчика и ядра | P1 |
| Автообновления | `unattended-upgrades` / `dnf-automatic` | Патчи безопасности без ручных действий | P0 |
| Брандмауэр | `ufw`, `nftables`, `firewalld` | Закрытые входящие | P1 |
| Блокировка экрана | `gsettings ... idle-delay`, `loginctl lock-session` | Физическая защита | P0 |
| AppArmor / SELinux | `aa-status` / `getenforce` | MAC-профили приложений | P1 |
| USBGuard | `usbguard list-devices` | Защита от BadUSB | P2 |

## Изоляция приложений

| Механизм | Команда | Что даёт |
|---|---|---|
| Flatpak | `flatpak info --show-permissions org.telegram.desktop` | Песочница: нет доступа к `$HOME`, кроме своего каталога |
| Override прав | `flatpak override --user --nofilesystem=home --nosocket=x11 <app>` | Убирает лишние доступы |
| Flatseal | GUI к тем же правилам | Удобная ревизия |
| firejail | `firejail --private firefox` | Профили для нативных сборок |
| Wayland | `echo $XDG_SESSION_TYPE` | На X11 любой клиент читает чужие нажатия и экран |

Практика: мессенджеры и браузер — в Flatpak с урезанными правами; веб-WhatsApp — в отдельном профиле браузера без расширений.

## Аудит и обнаружение

| Механизм | Команда | Что даёт |
|---|---|---|
| journald постоянно | `Storage=persistent` в `journald.conf.d` | Логи переживают перезагрузку |
| auditd | `augenrules --load`, `ausearch -k key` | События доступа и исполнения |
| AIDE | `aide --check` | Целостность файлов относительно базы |
| Проверка пакетов | `dpkg --verify`, `rpm -Va`, `pacman -Qkk` | Подмена файлов пакетов |
| osquery | `osqueryi 'select * from startup_items;'` | SQL-инвентарь |
| bpftrace | `bpftrace -e 'tracepoint:syscalls:sys_enter_execve {...}'` | Живое наблюдение за запуском процессов |

## Автозагрузка и постоянные механизмы

| Место | Команда |
|---|---|
| systemd (system) | `systemctl list-unit-files --state=enabled` |
| systemd (user) | `systemctl --user list-unit-files --state=enabled` |
| XDG autostart | `ls ~/.config/autostart /etc/xdg/autostart` |
| cron / at | `crontab -l`, `ls /etc/cron.*`, `atq`, `systemctl list-timers --all` |
| Shell-хуки | `grep -nE '^[^#]' ~/.bashrc ~/.profile /etc/profile` |
| Преload | `cat /etc/ld.so.preload`, `grep -rn LD_PRELOAD ~ /etc 2>/dev/null` |
| SSH | `cat ~/.ssh/authorized_keys` |
| sudo | `sudo visudo -c`, `ls -la /etc/sudoers.d/` |
| Модули ядра | `lsmod`, `/etc/modprobe.d/` |

## Мессенджеры на Linux

| Приложение | Где данные | Чем защищать |
|---|---|---|
| Telegram Desktop | `~/.local/share/TelegramDesktop/tdata` | Локальный код-пароль + LUKS |
| Signal Desktop | `~/.config/Signal` (ключ в keyring) | LUKS + заблокированный keyring |
| WhatsApp Desktop | `~/.config/<app>` или Flatpak-каталог | LUKS + изоляция профиля |
| WhatsApp Web | `<profile>/Default/IndexedDB/https_web.whatsapp.com_*` | Отдельный профиль браузера |

Права: `chmod 700 ~/.config/Signal ~/.local/share/TelegramDesktop`, `umask 0077`.

## Чек-лист

[Чек-лист на сайте](https://metapeka.github.io/whatsapp-security-research/linux.html) <!--services:linux-->

## Пределы

- `rkhunter` и `chkrootkit` знают только старые сигнатуры и проверяют систему штатными утилитами, которые руткит может подменять. «Чисто» от них ничего не доказывает.
- ClamAV полезен для чужих файлов (Windows-образцы, почта), но не для свежего JS-стилера в npm.
- Прошивка, Intel ME и AMD PSP — вне досягаемости из ОС.
- Компрометация уровня root не «лечится»: правильный ответ — переустановка с чистого носителя и ротация всех сессий.

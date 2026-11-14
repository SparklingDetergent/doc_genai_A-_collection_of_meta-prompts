


### Windows Server 2022 + Git for Windows + Windows 11 Gitクライアント構築設計書

今回の構成では、Windows Server 2022 に Git for Windows をインストールし、`git daemon` をタスクスケジューラから OS 起動時に自動起動させます。

日本国内の32名以下の開発チームを想定し、Git over TCP（9418番ポート）で clone / fetch / push できる構成にします。

### 1\. 前提と仮定

### 1-1. 構成

Windows Server 2022

Gitサーバー

WORKGROUP / 固定IP推奨

TCP 9418

git daemon --enable=receive-pack

D:\\Git\\Workspace0\\Project1.git

Bare repository / push・fetch・clone

社内LANのみ・認証なし

Windows 11 PC

Git for Windows

開発者 01〜16

Windows 11 PC

Git for Windows

開発者 17〜32

### 1-2. 採用する仮定

| 項目               | 採用値                      |
| ---------------- | ------------------------ |
| サーバーOS           | Windows Server 2022 x64  |
| クライアントOS         | Windows 11 x64           |
| Git              | Git for Windows 最新安定版を想定 |
| ネットワーク           | 社内LANのみ                  |
| ワークグループ          | WORKGROUP                |
| 最大利用者            | 32名                      |
| プロトコル            | Git daemon / TCP 9418    |
| 認証               | なし                       |
| push             | 許可                       |
| リポジトリ            | Workspace0/Project1.git  |
| 起動               | タスクスケジューラ・OS起動時          |
| ログ               | ファイル出力・日次ローテーション         |
| NTP              | 同期なし                     |
| Windows Firewall | 無効状態を前提。ただし有効化を推奨        |
| 配置先              | D:\\Git                  |
| ログ保存先            | D:\\Git\\Logs            |

重要なセキュリティ上の注意

Git daemon は今回の設定ではユーザー認証を行いません。`--enable=receive-pack` を有効にすると、9418番ポートに接続できる利用者は誰でも push できます。

また、Git daemon の認証なし運用では、Windowsのログオンユーザーごとの書き込み権限によるアクセス制御を実現できません。サーバープロセスの実行アカウントが持つ権限で操作されます。

したがって、以下を前提とします。

* インターネットから直接アクセスさせない。

* 開発用LANまたは専用VLANに限定する。

* リポジトリを読み書きできる人をネットワーク側で制限する。

* 機密情報・パスワード・秘密鍵をリポジトリに登録しない。

* 誤 push に備え、別媒体へのバックアップを実施する。

### 1-3. 採用する設定の考え方

今回の設計では、次の方針を採用します。

* 認証なしでも公開範囲を限定する：`--export-all` は使用せず、`git-daemon-export-ok` が存在するリポジトリだけを公開。

* pushを許可する：`receive-pack` を明示的に有効化。

* 誤操作を抑制する：非Fast-forward pushとブランチ削除を禁止。

* 実行権限を最小化する：タスクは `LOCAL SERVICE` で実行。SYSTEMでGit daemonを実行しない。

* 32名の同時利用に余裕を持たせる：最大接続数64。

* 障害解析を可能にする：詳細ログ、日次ログファイル、90日保存。

* Windows Firewallが無効でもネットワーク境界を守る：社内ルーター・L3スイッチ・上位FWでTCP 9418の接続元を限定。

なお、認証なしのGit daemonは暗号化も行いません。通信内容はLAN内で平文です。

### 1-4. 事前に変更する必要がある値

次の2つは実環境の値に置き換えてください。

* `<SERVER_IPV4>`：Gitサーバーの固定IPv4アドレス

* `<LAN_CIDR>`：Gitクライアントが所属するLANのネットワーク範囲（例：`192.168.10.0/24`）

この2つは推測で設定しません。

### 2\. システム別の項目検討表

### 2-1. Windows Server 2022 / Git for Windows

| 項目                 | デフォルト値      | 推奨値           | ON/OFF | 理由           |
| ------------------ | ----------- | ------------- | ------ | ------------ |
| Git daemon         | 未起動         | 常駐            | ON     | Gitサーバー機能    |
| TCPポート             | 9418        | 9418          | ON     | 標準ポート        |
| Listen             | 全インターフェース相当 | 固定IPv4        | ON     | 不要なNICへの公開防止 |
| upload-pack        | 有効          | 有効            | ON     | clone/fetch  |
| receive-pack       | 無効          | 有効            | ON     | push許可       |
| upload-archive     | 無効          | 無効            | OFF    | 不要な機能        |
| export-all         | 無効          | 無効            | OFF    | 公開範囲の限定      |
| strict-paths       | 無効          | 有効            | ON     | パスの厳格化       |
| max-connections    | 32          | 64            | ON     | 32名利用への余裕    |
| timeout            | 要確認         | 300秒          | ON     | 長時間接続の抑制     |
| init-timeout       | 要確認         | 30秒           | ON     | 接続後の待ち時間抑制   |
| informative-errors | 要確認         | 無効            | OFF    | 不要な情報開示を抑制   |
| 実行ユーザー             | 起動方法依存      | LOCAL SERVICE | ON     | 最小権限         |
| 起動方法               | 手動起動        | タスクスケジューラ     | ON     | OS起動時に自動起動   |
| ログ                 | stderr      | 日付別ファイル       | ON     | 障害調査         |
| ログ保存期間             | 未設定         | 90日           | ON     | ディスク容量管理     |
| Repository         | 未作成         | Project1.git  | ON     | 対象リポジトリ      |

出典：

* [Git公式：git-daemon](https://git-scm.com/docs/git-daemon.html?utm_source=chatgpt.com)

* [Git公式：git-init](https://git-scm.com/docs/git-init?utm_source=chatgpt.com)

* [Git for Windows公式](https://gitforwindows.org/?utm_source=chatgpt.com)

* [Microsoft：タスクスケジューラの起動トリガー](https://learn.microsoft.com/ja-jp/powershell/module/scheduledtasks/new-scheduledtasktrigger?view=windowsserver2022-ps&utm_source=chatgpt.com)

### 2-2. Gitリポジトリ設定

| 項目                          | デフォルト値  | 推奨値  | ON/OFF | 理由         |
| --------------------------- | ------- | ---- | ------ | ---------- |
| bare                        | 通常false | true | ON     | サーバー用      |
| daemon.receivepack          | false相当 | true | ON     | push許可     |
| receive.denyDeletes         | false   | true | ON     | ブランチ削除防止   |
| receive.denyNonFastForwards | false   | true | ON     | 強制push防止   |
| receive.fsckObjects         | false   | true | ON     | 受信オブジェクト検査 |
| transfer.fsckObjects        | false   | true | ON     | 転送オブジェクト検査 |
| fetch.fsckObjects           | false   | true | ON     | 取得オブジェクト検査 |
| git-daemon-export-ok        | なし      | 作成   | ON     | 公開許可       |

※ Gitのバージョン・配布形態による初期値の差は、実機の `git config --show-origin` で確認します。表中のfalse相当は、Git daemon側のサービス既定値を含みます。

出典：

* [Git公式：git-daemonのサービス設定](https://git-scm.com/docs/git-daemon.html?utm_source=chatgpt.com)

* [Git公式：git-config](https://git-scm.com/docs/git-config?utm_source=chatgpt.com)

### 2-3. Windows Serverの権限・ネットワーク

| 項目               | デフォルト値 | 推奨値                  | ON/OFF | 理由            |
| ---------------- | ------ | -------------------- | ------ | ------------- |
| Repository ACL   | 要確認    | LOCAL SERVICE Modify | ON     | push可能にする     |
| Administrators   | 要確認    | Full Control         | ON     | 管理            |
| SYSTEM           | 要確認    | Full Control         | ON     | OS管理          |
| 一般ユーザー           | 要確認    | 直接アクセスなし             | OFF    | SMB等からの直接変更防止 |
| TCP 9418         | ルール依存  | LAN限定許可ルール           | ON     | 接続範囲の限定       |
| Windows Firewall | 無効（前提） | 現状維持                 | OFF    | 指定条件に従う       |
| NTP              | 同期なし   | 現状維持                 | OFF    | 指定条件に従う       |

ACLは `icacls` で設定します。

出典：

* [Microsoft：icacls](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/icacls?utm_source=chatgpt.com)

* [Microsoft：New-NetFirewallRule](https://learn.microsoft.com/en-us/powershell/module/netsecurity/new-netfirewallrule?utm_source=chatgpt.com)

* [CIS：Windows Server 2022 Benchmark](https://www.cisecurity.org/benchmark/microsoft_windows_server?utm_source=chatgpt.com)

セキュリティ上の評価： Windows Firewallを無効のまま運用することはCISの一般的なハードニング方針とは一致しません。今回の設定は条件に従って無効状態を維持しますが、本番環境ではFirewallを有効にし、TCP 9418をLANの送信元範囲に限定することを推奨します。

### 2-4. Windows 11 Gitクライアント

| 項目              | デフォルト値      | 推奨値   | ON/OFF | 理由              |
| --------------- | ----------- | ----- | ------ | --------------- |
| Git for Windows | 未導入の場合あり    | 最新安定版 | ON     | Git利用           |
| core.quotepath  | true相当      | false | ON     | 日本語ファイル名表示      |
| core.autocrlf   | true相当の場合あり | false | ON     | 改行コードを統一        |
| core.safecrlf   | warn相当以外もあり | warn  | ON     | 改行変換警告          |
| fetch.prune     | false       | true  | ON     | 不要なリモートブランチ参照削除 |
| pull.ff         | true相当      | only  | ON     | 意図しないマージ防止      |
| Git認証           | 不要          | 設定しない | OFF    | 今回は認証なし         |

改行コードについては、リポジトリに `.gitattributes` を設け、LFを基本にする方針を推奨します。

例：

```gitattributes
* text=auto eol=lf
*.bat text eol=crlf
*.cmd text eol=crlf
*.ps1 text eol=crlf
```

これにより、WindowsとLinuxが混在する日本の開発環境でも改行コードの差異を管理しやすくなります。

### 3\. 連携整合性チェック

### 3-1. 通信経路

| 項目    | サーバー       | クライアント     |
| ----- | ---------- | ---------- |
| プロトコル | Git daemon | Git        |
| ポート   | TCP 9418   | 動的ポート      |
| 接続方向  | Listen     | Connect    |
| バインド  | 固定IPv4     | サーバーIPv4指定 |
| 認証    | なし         | なし         |
| 暗号化   | なし         | なし         |

Git daemonの標準ポートは9418です。SSHの22番、HTTPSの443番は使用しません。

### 3-2. 接続数とタイムアウト

| 項目         | 採用値   |
| ---------- | ----- |
| 最大接続数      | 64    |
| 初期接続タイムアウト | 30秒   |
| 通信タイムアウト   | 300秒  |
| 利用者数       | 32名以下 |

最大接続数のデフォルトは32です。今回は32名が同時に複数のGit操作を行う可能性を考慮して64にします。

ただし、接続数を64にすることは64名の同時push性能を保証するものではありません。

### 3-3. 起動・権限・ログ

* Windows Server起動

    タスクスケジューラがOS起動を検知

* Git daemon起動

    LOCAL SERVICE権限でgit.exeを実行

* リポジトリ公開

    git-daemon-export-okを確認

* クライアント接続

    TCP 9418でclone/fetch/push

* ログ保存

    日付別ログを作成し、90日経過後に削除

NTP同期がないため、ログの時刻はサーバーのローカル時計に依存します。時刻がずれている場合、ログの時系列やコミット時刻の信頼性は保証できません。

### 4\. 実行コマンド

PowerShell 5.1対応を想定

以下は Windows Server 2022 の管理者 PowerShell で実行する構成です。

### 4-1. 事前準備

Git for Windowsをサーバーにインストールします。

公式サイト：

* [Git for Windows ダウンロード](https://gitforwindows.org/?utm_source=chatgpt.com)

* [サイレントインストール方法](https://gitforwindows.org/silent-or-unattended-installation.html?utm_source=chatgpt.com)

Git for Windowsのインストーラーは64bit版を使用します。

インストール後、以下が存在することを確認してください。

`C:\Program Files\Git\cmd\git.exe`

今回のサーバー構築スクリプトは、Gitのインストール済み環境を前提とします。

### 4-2. サーバー構築スクリプト

実行前に、先頭の2つのネットワーク変数を書き換えてください。

* `$ServerIPv4`

* `$LanCidr`

実行場所：Windows Server 2022 / 管理者権限の Windows PowerShell 5.1

以下のコードは、バックアップ、設定、権限、リポジトリ作成、タスク登録、ログローテーション、クライアント用スクリプト作成、変更後の取得と差分表示を順番に実行します。

```powershell

# ============================================================
# Git Server Setup
# Windows Server 2022 / Git for Windows
# PowerShell 5.1 / Administrator
# ============================================================

$ErrorActionPreference = "Stop"

# ---- 必ず実環境の値に変更 ----
$ServerIPv4 = "<SERVER_IPV4>"
$LanCidr    = "<LAN_CIDR>"

# ---- 基本設定 ----
$GitExe       = "C:\Program Files\Git\cmd\git.exe"
$BashExe      = "C:\Program Files\Git\bin\bash.exe"
$GitRoot      = "D:\Git"
$RepoParent   = "$GitRoot\Workspace0"
$RepoPath     = "$RepoParent\Project1.git"
$RepoConfig   = "$RepoPath\config"
$LogRoot      = "$GitRoot\Logs"
$WorkRoot     = "C:\ProgramData\GitDaemon"
$Before       = "$WorkRoot\config_before"
$After        = "$WorkRoot\config_after"
$DaemonScript = "$WorkRoot\Start-GitDaemon.ps1"
$RotateScript = "$WorkRoot\Rotate-GitLogs.ps1"
$ClientScript = "$WorkRoot\ClientSetup.ps1"

$TaskName       = "GitDaemon-Server"
$RotateTaskName = "GitDaemon-LogRotation"
$FirewallRule   = "GitDaemon-TCP-9418"

# ============================================================
# [A] 変更前の全設定取得
# ============================================================

New-Item -ItemType Directory -Force -Path $WorkRoot | Out-Null
New-Item -ItemType Directory -Force -Path $Before | Out-Null

$BackupRoot = Join-Path $WorkRoot ("backup_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null

function Save-ConfigSnapshot($Destination) {

    New-Item -ItemType Directory -Force -Path $Destination | Out-Null

    Get-ComputerInfo |
        Format-List * |
        Out-File "$Destination\ComputerInfo.txt" -Encoding UTF8

    Get-NetIPConfiguration |
        Format-List * |
        Out-File "$Destination\Network.txt" -Encoding UTF8

    Get-NetFirewallProfile -PolicyStore ActiveStore |
        Format-List * |
        Out-File "$Destination\FirewallProfiles.txt" -Encoding UTF8

    Get-NetFirewallRule |
        Select-Object Name,DisplayName,Enabled,Profile,Direction,Action |
        Format-Table -AutoSize |
        Out-File "$Destination\FirewallRules.txt" -Encoding UTF8

    schtasks.exe /query /fo CSV /v |
        Out-File "$Destination\ScheduledTasks.csv" -Encoding UTF8

    Get-NetTCPConnection -ErrorAction SilentlyContinue |
        Export-Csv "$Destination\TCPConnections.csv" -NoTypeInformation -Encoding UTF8

    if (Test-Path $GitExe) {
        & $GitExe --version |
            Out-File "$Destination\GitVersion.txt" -Encoding UTF8

        & $GitExe config --system --list --show-origin 2>&1 |
            Out-File "$Destination\GitSystemConfig.txt" -Encoding UTF8

        & $GitExe config --global --list --show-origin 2>&1 |
            Out-File "$Destination\GitGlobalConfig.txt" -Encoding UTF8
    }

    if (Test-Path $RepoConfig) {
        & $GitExe config --file $RepoConfig --list --show-origin |
            Out-File "$Destination\GitRepositoryConfig.txt" -Encoding UTF8
    }

    if (Test-Path $GitRoot) {
        icacls.exe $GitRoot /save "$Destination\GitACL.txt" /T /C |
            Out-File "$Destination\GitACL-Result.txt" -Encoding UTF8
    }

    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Export-ScheduledTask -TaskName $TaskName |
            Out-File "$Destination\GitDaemonTask.xml" -Encoding UTF8
    }

    Get-ChildItem $WorkRoot -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^(Start-GitDaemon|Rotate-GitLogs|ClientSetup)\.ps1$' } |
        ForEach-Object {
            Copy-Item $_.FullName $Destination -Force
        }

    Write-Host "Snapshot completed: $Destination" -ForegroundColor Green
}

Save-ConfigSnapshot $Before

Write-Host "`n===== BEFORE CONFIGURATION =====" -ForegroundColor Cyan

Get-ChildItem $Before -File | ForEach-Object {
    Write-Host "`n--- $($_.Name) ---"
    Get-Content $_.FullName -ErrorAction SilentlyContinue
}

# 既存設定ファイルをバックアップ
if (Test-Path $RepoConfig) {
    Copy-Item $RepoConfig "$BackupRoot\repo.config"
}

if (Test-Path $DaemonScript) {
    Copy-Item $DaemonScript "$BackupRoot\Start-GitDaemon.ps1"
}

if (Test-Path $RotateScript) {
    Copy-Item $RotateScript "$BackupRoot\Rotate-GitLogs.ps1"
}

if (Test-Path $ClientScript) {
    Copy-Item $ClientScript "$BackupRoot\ClientSetup.ps1"
}

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Export-ScheduledTask -TaskName $TaskName |
        Out-File "$BackupRoot\GitDaemonTask.xml" -Encoding UTF8
}

if (Get-ScheduledTask -TaskName $RotateTaskName -ErrorAction SilentlyContinue) {
    Export-ScheduledTask -TaskName $RotateTaskName |
        Out-File "$BackupRoot\GitLogRotationTask.xml" -Encoding UTF8
}

# ============================================================
# 事前チェック
# ============================================================

if ($ServerIPv4 -notmatch '^\d{1,3}(\.\d{1,3}){3}$' -or
    $ServerIPv4 -eq "<SERVER_IPV4>") {
    throw "ServerIPv4を実際の固定IPv4アドレスに変更してください。"
}

$ParsedIP = $null
if (-not [System.Net.IPAddress]::TryParse($ServerIPv4,[ref]$ParsedIP)) {
    throw "ServerIPv4が不正です。"
}

if ($LanCidr -eq "<LAN_CIDR>" -or
    $LanCidr -notmatch '^\d{1,3}(\.\d{1,3}){3}/\d{1,2}$') {
    throw "LanCidrを実際のLAN CIDRに変更してください。"
}

if (-not (Test-Path $GitExe)) {
    throw "Git for Windowsが未導入です。GitExe=$GitExe"
}

if (-not (Test-Path $BashExe)) {
    throw "Git Bashが見つかりません。"
}

$LocalIP = Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -eq $ServerIPv4 }

if (-not $LocalIP) {
    throw "指定されたServerIPv4がサーバーに設定されていません。"
}

$GitVersion = & $GitExe --version
Write-Host "Detected: $GitVersion"

# ============================================================
# [B] 設定変更本体
# ============================================================

# ------------------------------------------------------------
# Git Root
# デフォルト: 未作成 → D:\Git
# ------------------------------------------------------------

New-Item -ItemType Directory -Force -Path $GitRoot | Out-Null
New-Item -ItemType Directory -Force -Path $RepoParent | Out-Null
New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null

# ------------------------------------------------------------
# Repository
# デフォルト: 未作成 → Bare repository
# ------------------------------------------------------------

if (-not (Test-Path $RepoPath)) {
    & $GitExe init --bare --initial-branch=main $RepoPath
    if ($LASTEXITCODE -ne 0) {
        throw "Bare repositoryの初期化に失敗しました。"
    }
}
else {
    $IsBare = & $GitExe --git-dir=$RepoPath rev-parse --is-bare-repository
    if ($IsBare -ne "true") {
        throw "既存RepositoryがBareではありません。処理を中断します。"
    }
}

# ------------------------------------------------------------
# Export marker
# デフォルト: なし → 作成
# ------------------------------------------------------------

New-Item -ItemType File -Force `
    -Path "$RepoPath\git-daemon-export-ok" | Out-Null

# ------------------------------------------------------------
# daemon.receivepack
# デフォルト: false相当 → true
# ------------------------------------------------------------

& $GitExe config --file $RepoConfig daemon.receivepack true

# ------------------------------------------------------------
# receive.denyDeletes
# デフォルト: false → true
# ------------------------------------------------------------

& $GitExe config --file $RepoConfig receive.denyDeletes true

# ------------------------------------------------------------
# receive.denyNonFastForwards
# デフォルト: false → true
# ------------------------------------------------------------

& $GitExe config --file $RepoConfig receive.denyNonFastForwards true

# ------------------------------------------------------------
# receive.fsckObjects
# デフォルト: false → true
# ------------------------------------------------------------

& $GitExe config --file $RepoConfig receive.fsckObjects true

# ------------------------------------------------------------
# transfer.fsckObjects
# デフォルト: false → true
# ------------------------------------------------------------

& $GitExe config --file $RepoConfig transfer.fsckObjects true

# ------------------------------------------------------------
# fetch.fsckObjects
# デフォルト: false → true
# ------------------------------------------------------------

& $GitExe config --file $RepoConfig fetch.fsckObjects true

# ------------------------------------------------------------
# Repository ACL
# デフォルト: 要確認 → SYSTEM/Admin Full / LOCAL SERVICE Modify
# ------------------------------------------------------------

icacls.exe $GitRoot /inheritance:r `
    /grant:r `
    "NT AUTHORITY\SYSTEM:(OI)(CI)F" `
    "BUILTIN\Administrators:(OI)(CI)F" `
    "NT AUTHORITY\LOCAL SERVICE:(OI)(CI)M" `
    /T /C

if ($LASTEXITCODE -ne 0) {
    throw "Repository ACL設定でエラーが発生しました。"
}

# ============================================================
# Git daemon 起動スクリプト
# ============================================================

# daemon:
# default max-connections 32 → 64
# default port 9418 → 9418 (変更なし)
# init-timeout → 30 sec
# timeout → 300 sec
# upload-pack → enabled (変更なし)
# receive-pack → enabled
# upload-archive → disabled (変更なし)
# export-all → disabled (変更なし)
# strict-paths → enabled
# informative-errors → disabled

$DaemonScriptText = @'
$ErrorActionPreference = "Continue"

$GitExe = "C:\Program Files\Git\cmd\git.exe"
$GitRoot = "D:\Git"
$LogRoot = "D:\Git\Logs"
$ServerIPv4 = "__SERVER_IPV4__"

Start-Sleep -Seconds 20

while ($true) {

    & $GitExe daemon `
        --reuseaddr `
        --verbose `
        "--listen=$ServerIPv4" `
        --port=9418 `
        "--base-path=D:/Git" `
        --strict-paths `
        --enable=receive-pack `
        --forbid-override=receive-pack `
        --max-connections=64 `
        --init-timeout=30 `
        --timeout=300 `
        --no-informative-errors `
        --log-destination=stderr `
        "D:/Git" 2>&1 |
        ForEach-Object {

            $Date = Get-Date -Format "yyyyMMdd"
            $Time = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffK"
            $LogFile = Join-Path $LogRoot "daemon-$Date.log"

            Add-Content -LiteralPath $LogFile `
                -Value "[$Time] $_" -Encoding UTF8
        }

    Start-Sleep -Seconds 5
}
'@

$DaemonScriptText = $DaemonScriptText.Replace(
    "__SERVER_IPV4__",
    $ServerIPv4
)

Set-Content -LiteralPath $DaemonScript `
    -Value $DaemonScriptText -Encoding UTF8

# ------------------------------------------------------------
# Daemon script permissions
# ------------------------------------------------------------

icacls.exe $DaemonScript /grant "NT AUTHORITY\LOCAL SERVICE:RX"
icacls.exe $LogRoot /grant "NT AUTHORITY\LOCAL SERVICE:(OI)(CI)M"

# ============================================================
# ログローテーションスクリプト
# 日次圧縮・90日保存
# ============================================================

$RotateScriptText = @'
$ErrorActionPreference = "Stop"

$LogRoot = "D:\Git\Logs"
$RetentionDays = 90
$Cutoff = (Get-Date).Date

Get-ChildItem $LogRoot -Filter "daemon-*.log" -File |
    Where-Object { $_.LastWriteTime.Date -lt $Cutoff } |
    ForEach-Object {

        $ZipFile = "$($_.FullName).zip"

        if (-not (Test-Path $ZipFile)) {
            Compress-Archive -LiteralPath $_.FullName `
                -DestinationPath $ZipFile -CompressionLevel Optimal
        }

        if (Test-Path $ZipFile) {
            Remove-Item $_.FullName -Force
        }
    }

Get-ChildItem $LogRoot -Filter "daemon-*.log.zip" -File |
    Where-Object {
        $_.LastWriteTime -lt (Get-Date).AddDays(-$RetentionDays)
    } |
    Remove-Item -Force
'@

Set-Content -LiteralPath $RotateScript `
    -Value $RotateScriptText -Encoding UTF8

icacls.exe $RotateScript /grant "NT AUTHORITY\LOCAL SERVICE:RX"

# ============================================================
# タスクスケジューラ
# デフォルト: 手動 → OS起動時
# 実行ユーザー: LOCAL SERVICE
# ============================================================

$PowerShellExe = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"

$DaemonAction = New-ScheduledTaskAction `
    -Execute $PowerShellExe `
    -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$DaemonScript`""

$StartupTrigger = New-ScheduledTaskTrigger -AtStartup

$LocalServicePrincipal = New-ScheduledTaskPrincipal `
    -UserId "LOCALSERVICE" `
    -LogonType ServiceAccount `
    -RunLevel Limited

$DaemonSettings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $DaemonAction `
    -Trigger $StartupTrigger `
    -Principal $LocalServicePrincipal `
    -Settings $DaemonSettings `
    -Description "Git daemon TCP 9418" `
    -Force | Out-Null

# ------------------------------------------------------------
# ログローテーションタスク
# デフォルト: 未設定 → 毎日00:15
# ------------------------------------------------------------

$RotateAction = New-ScheduledTaskAction `
    -Execute $PowerShellExe `
    -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$RotateScript`""

$RotateTrigger = New-ScheduledTaskTrigger `
    -Daily -At "00:15"

Register-ScheduledTask `
    -TaskName $RotateTaskName `
    -Action $RotateAction `
    -Trigger $RotateTrigger `
    -Principal $LocalServicePrincipal `
    -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable) `
    -Description "Git daemon log rotation" `
    -Force | Out-Null

# ============================================================
# Windows Firewallルール
# 現状のFirewall無効状態は変更しない。
# ルールは作成しておく。
# ============================================================

# TCP 9418:
# default rule → LAN CIDR限定の許可ルール

Get-NetFirewallRule -Name $FirewallRule `
    -ErrorAction SilentlyContinue |
    Remove-NetFirewallRule

New-NetFirewallRule `
    -Name $FirewallRule `
    -DisplayName "Git Daemon TCP 9418 LAN Only" `
    -Description "Git daemon inbound from internal LAN" `
    -Direction Inbound `
    -Action Allow `
    -Enabled True `
    -Profile Any `
    -Program $GitExe `
    -Protocol TCP `
    -LocalPort 9418 `
    -RemoteAddress $LanCidr | Out-Null

# 注意: Windows Firewall自体は有効化しない。
# 上位ネットワーク機器でLAN CIDR以外を遮断すること。

# ============================================================
# Windows 11 クライアント用セットアップスクリプト生成
# ============================================================

$ClientScriptText = @'
$ErrorActionPreference = "Stop"

$ServerIPv4 = "__SERVER_IPV4__"
$GitUrl = "git://$ServerIPv4/Workspace0/Project1.git"

# Git for Windowsがなければwingetで導入
if (-not (Get-Command git.exe -ErrorAction SilentlyContinue)) {

    if (-not (Get-Command winget.exe -ErrorAction SilentlyContinue)) {
        throw "Git for Windowsを公式サイトからインストールしてください。"
    }

    winget install --id Git.Git --exact --silent `
        --accept-package-agreements `
        --accept-source-agreements

    if ($LASTEXITCODE -ne 0) {
        throw "Git for Windowsのインストールに失敗しました。"
    }
}

$GitExe = "C:\Program Files\Git\cmd\git.exe"

if (-not (Test-Path $GitExe)) {
    throw "Git executableが見つかりません。"
}

# core.quotepath: true相当 → false
& $GitExe config --global core.quotepath false

# core.autocrlf: true相当の場合あり → false
& $GitExe config --global core.autocrlf false

# core.safecrlf: warn
& $GitExe config --global core.safecrlf warn

# fetch.prune: false → true
& $GitExe config --global fetch.prune true

# pull.ff: true相当 → only
& $GitExe config --global pull.ff only

Write-Host "Git version:"
& $GitExe --version

Write-Host "Repository URL:"
Write-Host $GitUrl

$ClonePath = Join-Path (Get-Location) "Project1"

if (-not (Test-Path $ClonePath)) {
    & $GitExe clone $GitUrl $ClonePath
    if ($LASTEXITCODE -ne 0) {
        throw "Clone failed. Server connectivity and daemon status must be checked."
    }
}

Write-Host "Client setup completed."
'@

$ClientScriptText = $ClientScriptText.Replace(
    "__SERVER_IPV4__",
    $ServerIPv4
)

Set-Content -LiteralPath $ClientScript `
    -Value $ClientScriptText -Encoding UTF8

# ============================================================
# タスク起動
# ============================================================

Start-ScheduledTask -TaskName $TaskName

Start-Sleep -Seconds 5

# ============================================================
# [C] 変更後の全設定取得
# ============================================================

New-Item -ItemType Directory -Force -Path $After | Out-Null

Save-ConfigSnapshot $After

# Git daemonの待受確認
Get-NetTCPConnection -LocalPort 9418 -State Listen `
    -ErrorAction SilentlyContinue |
    Format-Table -AutoSize

# タスク状態
Get-ScheduledTask -TaskName $TaskName |
    Format-List TaskName,State

Get-ScheduledTask -TaskName $RotateTaskName |
    Format-List TaskName,State

# Repository設定
& $GitExe config --file $RepoConfig --list --show-origin

# ACL
icacls.exe $GitRoot

# Firewallルール
Get-NetFirewallRule -Name $FirewallRule |
    Format-List *

# クライアントスクリプトの配置先
Write-Host "Client script: $ClientScript" -ForegroundColor Green

# ============================================================
# 変更後の内容表示
# ============================================================

Write-Host "`n===== AFTER CONFIGURATION =====" -ForegroundColor Cyan

Get-ChildItem $After -File | ForEach-Object {
    Write-Host "`n--- $($_.Name) ---"
    Get-Content $_.FullName -ErrorAction SilentlyContinue
}

# ============================================================
# BEFORE / AFTER DIFF
# Git Bashのdiff -ruを使用
# ============================================================

Write-Host "`n===== CONFIGURATION DIFF =====" -ForegroundColor Yellow

& $BashExe -lc `
    "diff -ru /c/ProgramData/GitDaemon/config_before /c/ProgramData/GitDaemon/config_after || true"

Write-Host "`n===== SETUP FINISHED =====" -ForegroundColor Green

Write-Host "Backup: $BackupRoot"
Write-Host "Before: $Before"
Write-Host "After : $After"
Write-Host "Repository: $RepoPath"
Write-Host "Git URL: git://$ServerIPv4/Workspace0/Project1.git"
Write-Host "Daemon task: $TaskName"
Write-Host "Log rotation task: $RotateTaskName"
```

### 4-3. Windows 11 クライアント設定

サーバーで生成される次のファイルを、Windows 11 PCに配布します。

`C:\ProgramData\GitDaemon\ClientSetup.ps1`

クライアント側で実行します。

```powershell
# 管理者または通常ユーザーのPowerShell
Set-ExecutionPolicy -Scope Process Bypass -Force

# 配布されたファイルの場所に応じて変更
& ".\ClientSetup.ps1"
```

Git for Windowsが未導入であれば、wingetでインストールします。

サーバーのGit設定は変更せず、クライアントユーザーのグローバル設定のみ変更します。

### 4-4. 接続・push試験

Windows 11で以下を実行してください。

```powershell
# サーバーへの疎通確認
Test-NetConnection <SERVER_IPV4> -Port 9418

# clone
git clone git://<SERVER_IPV4>/Workspace0/Project1.git

cd Project1

# テストファイル作成
"# Git Server Test" | Set-Content README.md -Encoding UTF8

# 初回コミット
git switch -c main

git config user.name "Developer01"
git config user.email "developer01@example.local"

git add README.md
git commit -m "Initial commit"

# push
git push -u origin main

# push結果確認
git ls-remote origin
```

初回のcloneは空リポジトリなので、コミット前にブランチが存在しない旨の警告が出る場合があります。初回コミット後にpushしてください。

### 5\. 検証手順とロールバック方法

### 5-1. サーバー側の検証

以下を管理者PowerShellで実行します。

```powershell
# 1. タスク状態
Get-ScheduledTask -TaskName "GitDaemon-Server"

# 2. タスクの実行結果
Get-ScheduledTaskInfo -TaskName "GitDaemon-Server"

# 3. TCP 9418待受確認
Get-NetTCPConnection -LocalPort 9418 -State Listen

# 4. Repositoryの公開確認
Test-Path "D:\Git\Workspace0\Project1.git\git-daemon-export-ok"

# 5. Bare repository確認
git --git-dir="D:\Git\Workspace0\Project1.git" rev-parse --is-bare-repository

# 6. Git設定確認
git config --file "D:\Git\Workspace0\Project1.git\config" --list

# 7. ログ確認
Get-ChildItem "D:\Git\Logs" |
    Sort-Object LastWriteTime -Descending

# 8. クライアントからの接続確認
Test-NetConnection <SERVER_IPV4> -Port 9418
```

### 5-2. クライアント側の検証

| 検証            | 期待結果                  |
| ------------- | --------------------- |
| TCP 9418      | TcpTestSucceeded=True |
| git clone     | 成功                    |
| git fetch     | 成功                    |
| git push      | 成功                    |
| git ls-remote | ブランチ情報表示              |
| 強制push        | 拒否                    |
| ブランチ削除push    | 拒否                    |

### 5-3. ロールバック

構築時に作成したバックアップフォルダーを利用します。

注意：以下はGitサービス停止を伴います

```powershell
# Git daemon停止
Stop-ScheduledTask -TaskName "GitDaemon-Server"

# タスク削除
Unregister-ScheduledTask `
    -TaskName "GitDaemon-Server" `
    -Confirm:$false

Unregister-ScheduledTask `
    -TaskName "GitDaemon-LogRotation" `
    -Confirm:$false

# Firewallルール削除
Remove-NetFirewallRule `
    -Name "GitDaemon-TCP-9418" `
    -ErrorAction SilentlyContinue

# バックアップ一覧
Get-ChildItem "C:\ProgramData\GitDaemon" -Directory |
    Where-Object Name -Like "backup_*" |
    Sort-Object Name -Descending

# 必ず対象バックアップを確認してから復元する
# $BackupRootは実際のバックアップパスに変更
# 既存リポジトリを削除・上書きしないこと
```

ロールバック上の重要事項

* リポジトリ本体は削除しないでください。

* `config` を復元する場合、対象バックアップの内容を確認してください。

* ACLはバックアップしたACLファイルから復元できますが、復元先パスを確認してください。

* Git daemonの停止中は全クライアントのpush/fetchができません。

### 6\. 未検証・バージョン依存の注意点

### 6-1. バージョン依存

| 対象                  | 注意事項                        |
| ------------------- | --------------------------- |
| Windows Server 2022 | PowerShell 5.1を想定           |
| Git for Windows     | 最新安定版を想定。実際のバージョンは要確認       |
| git daemon          | Windows版Gitでのサービス動作は実機検証が必要 |
| Task Scheduler      | LOCAL SERVICEでの起動権限を実機確認    |
| NTFS ACL            | 既存ACLとの競合がないか確認             |
| Windows Firewall    | 無効状態では追加ルールは実際の通信制御に作用しない   |
| NTP                 | 時刻の正確性は保証できない               |

### 6-2. 特に注意する3点

① 認証なしpushのリスク

今回の構成で最も重要なリスクです。

Git daemonは、pushを許可した場合、接続可能なユーザーを区別できません。32名以下という人数制限は、接続できる人の制限にはなりません。

② 複数人による同時push

Gitは同一リポジトリへの同時更新を処理できますが、同一ブランチへの競合更新は発生します。

そのため、今回の設定ではFast-forward以外の更新を拒否します。開発者にはfetchしてからpushする運用を推奨します。

③ バックアップ

Git daemonのログはバックアップではありません。

最低限、次のバックアップを別ディスクまたは別サーバーに保存してください。

* `D:\Git\Workspace0\Project1.git`

* Git設定ファイル

* ACL情報

* タスクスケジューラの設定

* ログ

NTPなしでは、バックアップの時刻やログの時系列に問題が発生する可能性があります。

### 6-3. 調査した公式・実務資料

| 分類              | 資料                            | 採用した内容                       |
| --------------- | ----------------------------- | ---------------------------- |
| Git公式           | git-daemon                    | ポート、サービス、公開制御、接続制限           |
| Git公式           | git-config                    | push制御、fsck、削除禁止             |
| Git公式           | Git on the Server: Git Daemon | daemon運用、export marker、9418番 |
| Git for Windows | サイレントインストール                   | Windowsインストール                |
| Microsoft       | ScheduledTaskPrincipal        | LOCAL SERVICEでのタスク実行         |
| Microsoft       | New-NetFirewallRule           | LAN限定FWルール                   |
| CIS             | Windows Server Benchmark      | Windows Server 2022のハードニング   |
| 実務事例            | WindowsでGit daemonをサービスとして動かす | Windows上のdaemon常駐化           |
| 実務事例            | Windows Git daemonのpush速度問題   | --reuseaddr の実務上の利用例         |

Git公式の説明でも、Git daemonのpushは認証なしであるため、閉じたLANでの利用を前提としています。git-daemon Documentation +1

また、Git for Windowsの実務事例では、Windows上での常駐化にNSSMを使う方法も紹介されています。今回はご指定のタスクスケジューラ方式を優先しています。Qiita +1

### 最終的な推奨評価

### 今回の構成の評価

セットアップの簡易性

良好

32名以下の小規模利用

適合

認証なしLAN運用

要ネットワーク制限

pushの誤操作対策

対策あり

ログ管理

日次・90日

時刻監査

NTPなしの制約

将来の改善候補

* 認証が必要になった場合はSSH方式へ移行。

* 重要な開発データは別サーバーへ定期バックアップ。

* ブランチ保護やレビューが必要になればGitea等の導入を検討。

* Windows Firewallを有効にし、9418番だけをLANに公開。





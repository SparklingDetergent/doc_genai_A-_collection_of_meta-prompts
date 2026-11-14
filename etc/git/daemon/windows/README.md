# Git daemon サーバー構築ガイド(Windows Server 2022 / Windows 11 クライアント)

社内LAN専用・認証なし・全リポジトリ公開&push可の Git daemon(git://)構成です。フェーズごとに独立しているので、上から順に実施してください。

## 0. 前提・設計方針・置換ポイント

- サーバー: Windows Server 2022(ワークグループ、NTP同期なし、Windowsファイアウォール無効)
- クライアント: Windows 11、最大32名、認証なし(LAN内の誰でも clone / push 可)
- プロトコル: git://(暗号化・認証なし)。接続URLは常にポート明示 `git://192.168.1.10:9418/Workspace0/Project1.git`
- デーモンは Administrator アカウントで起動(タスクスケジューラ、OS起動時)
- 設定は上位で一括指定し、下位では重複させない(デーモン起動オプション > Gitシステム設定 > リポジトリ)。Git の設定は system で行えるものを全て system に置き、global は user.name と user.email だけにする(再インストール後はフェーズ3を必ず再実行する)
- 既定値でも、将来の既定変更への備えと意図の明示のためあえて設定する
- スクリプトは変数を極力使わず、値を直書きする

変更前の記録(before): 設定を変更する直前に、変更前の状態を `C:\GitBuild\before\` へ保存します(画面表示+ファイル保存)。該当箇所は 1-0(OS)、3-0(Gitシステム)、4-0(Gitグローバル)、7-0(リポジトリ)、8-0(既存リポジトリへ適用する場合)です。

| 置換する値 | 本ガイドの例 | 登場箇所 |
| --- | --- | --- |
| サーバーIP | 192.168.1.10 | クライアントURL、テスト |
| ポート | 9418 | 起動スクリプト、FWルール、クライアントURL |
| リポジトリ置き場 | D:\\Git\\repos | OS設定、起動スクリプト、リポジトリ作成 |
| ログ置き場 | D:\\Git\\logs | OS設定、起動スクリプト |
| スクリプト置き場 | D:\\Git\\scripts | OS設定、タスク |
| ユーザー名・メール | 個別に記入 | グローバル設定 |

| フェーズ | 内容 | 対象 |
| --- | --- | --- |
| 1 | OS設定 | サーバー |
| 2 | Git for Windows インストール | 両方 |
| 3 | Git システム設定 | 両方(同一コマンド) |
| 4 | Git グローバル設定 | 両方(user.name と user.email だけ) |
| 5 | デーモン起動スクリプト(月次/曜日の2パターン) | サーバー |
| 6 | タスクスケジューラ | サーバー |
| 7 | リポジトリ作成 | サーバー |
| 8 | リポジトリ設定ファイル(.gitattributes) | リポジトリ |
| 9 | クライアント操作 | クライアント |
| 10 | テスト | 両方 |
| 11 | 保守・注意点 | 両方 |

## 1. OS設定(サーバー)

GUIで行う項目(コマンド化しません):

- 固定IP: `ncpa.cpl` → NICのプロパティ → IPv4 → 例 192.168.1.10 / 255.255.255.0(ゲートウェイ・DNSは環境に合わせる)
- コンピューター名: 任意。ワークグループのまま
- 時刻: NTP同期なし前提のため、設定 → 時刻と言語 で手動調整(ログ・コミット時刻に影響)

### 1-0 変更前の記録(before・サーバー)

フェーズ1の変更(上のGUI操作を含む)を始める前に、管理者権限の PowerShell で実行します。画面に表示しつつ `C:\GitBuild\before\` に保存します。出力が空なら未設定・未作成・未登録を意味します。Windows PowerShell 5.1 の `Tee-Object` は UTF-16 で保存しますが、メモ帳で開けます。

```powershell
# 保存先フォルダ作成: C:\GitBuild\before(既にあればそのまま。D:\Git 配下は変更対象のため別の場所に置く)
New-Item -ItemType Directory -Force -Path 'C:\GitBuild\before' | Out-Null
# コンピューター名: GUI変更前の状態
hostname | Tee-Object -FilePath 'C:\GitBuild\before\os_hostname.txt'
# 現在時刻: 手動調整前のズレを確認するため
Get-Date -Format 'o' | Tee-Object -FilePath 'C:\GitBuild\before\os_date.txt'
# IP構成: 固定IP設定(GUI)前の状態
Get-NetIPConfiguration | Tee-Object -FilePath 'C:\GitBuild\before\os_ipconfig.txt'
# D:\Git の中身(空=未作成)
Get-ChildItem 'D:\Git' -Recurse -Depth 2 -ErrorAction SilentlyContinue | Tee-Object -FilePath 'C:\GitBuild\before\os_dir_listing.txt'
# 9418 を待ち受けているプロセス(空=未起動)
Get-NetTCPConnection -LocalPort 9418 -State Listen -ErrorAction SilentlyContinue | Tee-Object -FilePath 'C:\GitBuild\before\os_listen.txt'
# タスク Git Daemon の定義をXMLで保存(空=未登録。フェーズ6の変更前)
Export-ScheduledTask -TaskName 'Git Daemon' -ErrorAction SilentlyContinue | Tee-Object -FilePath 'C:\GitBuild\before\os_task.xml'
```

### 1-1 設定変更(サーバー)

フォルダ準備です。エクスプローラーで `D:\Git\repos`、`D:\Git\logs`、`D:\Git\scripts` を作成しても同じです。コマンドで行う場合は PowerShell で実行します。

```powershell
# フォルダ作成: リポジトリ置き場(既にあればそのまま。レジストリ・権限・FW・タイムゾーンは変更しない方針)
New-Item -ItemType Directory -Force -Path 'D:\Git\repos'
# フォルダ作成: デーモンのログ置き場(ログローテーションのファイルが入る)
New-Item -ItemType Directory -Force -Path 'D:\Git\logs'
# フォルダ作成: 起動スクリプト置き場(フェーズ5の .ps1 を置く)
New-Item -ItemType Directory -Force -Path 'D:\Git\scripts'
```

OS設定はフォルダ準備だけです。レジストリ(長いパス対応など)、フォルダ権限(ACL)、ファイアウォール、タイムゾーンの変更は行いません(前提: ワークグループ、FW無効、NTP同期なし)。

## 2. Git for Windows インストール(サーバー・クライアント共通)

1. https://git-scm.com/download/win から最新の「Git for Windows/x64 Setup」を取得(ARM64機は ARM64版)
2. 起動して全画面で「Next」、最後に「Install」→「Finish」。画面での選択は一切変えない
3. PowerShell を開き直して `git --version` で確認

全て既定にする意図: 画面操作による設定のばらつきを無くし、設定はフェーズ3・4のコマンドで一括上書きするため。インストーラが入れる既定(改行=変換あり、エディタ=Vim、初期ブランチ=master など)は次のフェーズで上書きされます。

## 3. Git システム設定(両機共通・管理者 PowerShell)

`C:\Program Files\Git\etc\gitconfig` に書かれ、そのPCの全アカウントに効きます。Git の設定は system で行えるものを全てここに置きます。global に置くのは user.name と user.email だけです(フェーズ4)。再インストール後は必ずこのフェーズを再実行する前提で、コマンドは何度実行しても同じ結果になります。

### 3-0 変更前の記録(before)

Git のインストール直後、設定変更の前に管理者 PowerShell で実行します。インストーラが入れた既定値(core.autocrlf=true など)がここに残ります。

```powershell
# 保存先フォルダ作成: 既にあればそのまま
New-Item -ItemType Directory -Force -Path 'C:\GitBuild\before' | Out-Null
# バージョン: 変更前の Git のバージョン
git --version | Tee-Object -FilePath 'C:\GitBuild\before\git_version.txt'
# 全設定の実効値と出所(system / global / コマンドライン): これが「変更前の全設定値」
git config --list --show-origin | Tee-Object -FilePath 'C:\GitBuild\before\git_effective.txt'
# system 範囲のみ: インストーラ既定値を確認
git config --system --list --show-origin | Tee-Object -FilePath 'C:\GitBuild\before\git_system.txt'
# global 範囲のみ: 空やエラーなら未設定
git config --global --list --show-origin 2>&1 | Tee-Object -FilePath 'C:\GitBuild\before\git_global.txt'
# 設定ファイル本体のコピー: 元に戻す時はこのコピーを元の場所へ戻す
Copy-Item 'C:\Program Files\Git\etc\gitconfig' 'C:\GitBuild\before\gitconfig_system.bak' -ErrorAction SilentlyContinue
Copy-Item '~\.gitconfig' 'C:\GitBuild\before\gitconfig_global.bak' -ErrorAction SilentlyContinue
```

### 3-1 設定変更

```powershell
# core.autocrlf: true(インストーラ既定)→false(改行を一切変換しない方針。インストーラの値を上書き)
git config --system core.autocrlf false
# core.safecrlf: warn(既定)→false(変換しないので警告も不要)
git config --system core.safecrlf false
# core.quotepath: true(既定)→false(日本語ファイル名を八進数エスケープせずそのまま表示)
git config --system core.quotepath false
# core.symlinks: false(インストーラ既定)→false(明示。Windowsでは権限が要るため使わない意図)
git config --system core.symlinks false
# core.longpaths: false(既定)→false(明示。260文字を超える異常なパス構造を許容せず、Windows標準の制限に揃える)
git config --system core.longpaths false
# core.editor: Vim(インストーラ既定)→notepad(Vim操作を知らない保守担当者でも編集できるように)
git config --system core.editor notepad
# core.logAllRefUpdates: bareでは無効(既定)→false(明示。サーバー側bareリポジトリに不要なreflogを蓄積させない)
git config --system core.logAllRefUpdates false
# init.defaultBranch: master(既定)→main(サーバーで bare 作成時の HEAD も main になる。リポジトリ側で指定不要にするため system に置く)
git config --system init.defaultBranch main
# protocol.version: 2(現行の既定)→2(明示。将来の既定変更に備える)
git config --system protocol.version 2
# safe.directory: 未設定→*(所有者違いで dubious ownership エラーになるのを回避。LAN内・Administrators運用のため)
git config --system safe.directory '*'
# i18n.commitEncoding: utf-8(既定)→utf-8(明示。コミットメッセージは UTF-8)
git config --system i18n.commitEncoding utf-8
# i18n.logOutputEncoding: utf-8(既定)→utf-8(明示。ログ表示は UTF-8)
git config --system i18n.logOutputEncoding utf-8
# gui.encoding: utf-8(既定)→utf-8(明示。git gui の表示文字コード)
git config --system gui.encoding utf-8
# color.ui: auto(既定)→auto(明示。端末のときだけ色付け)
git config --system color.ui auto
# pull.rebase: 未設定(警告が出る)→false(pull は merge。履歴を書き換えない最も単純な動作)
git config --system pull.rebase false
# push.default: simple(既定)→simple(明示。現在のブランチを同名ブランチへだけ push)
git config --system push.default simple
# push.autoSetupRemote: false(既定)→true(新規ブランチの初回 push で upstream 設定を省略できる)
git config --system push.autoSetupRemote true
# fetch.prune: false(既定)→true(リモートで削除されたブランチをローカル参照から自動掃除)
git config --system fetch.prune true
# merge.ff: true(既定)→true(明示。可能なら fast-forward)
git config --system merge.ff true
# receive.denyNonFastForwards: false(既定)→true(認証なしのため force push による履歴消失を防止。全リポジトリに効く)
git config --system receive.denyNonFastForwards true
# receive.denyDeletes: false(既定)→true(認証なしのためリモートブランチ・タグの誤削除を防止)
git config --system receive.denyDeletes true
# transfer.fsckObjects: false(既定)→true(壊れたオブジェクトの受け入れ・取り込みを防止)
git config --system transfer.fsckObjects true
```

あえて設定しないもの: `core.eol`(`.gitattributes` の `-text` で変換自体を無効化するため効果なし)、`core.filemode` / `core.ignorecase`(リポジトリ作成時にGitが自動判定して各リポジトリに書くため system では効かない)、`credential.helper`(git:// は認証なし)。

## 4. Git グローバル設定(両機共通・各ユーザーで実行)

`C:\Users\<ユーザー>\.gitconfig` に書かれます。global に置くのは user.name と user.email だけです(他の設定は全てフェーズ3の system に置いています)。

### 4-0 変更前の記録(before)

各ユーザーが自分のアカウントで実行します。保存先は各ユーザーのホーム配下(`~\GitBuild\before`)で、ユーザーごとに分かれ権限の問題も出ません。

```powershell
# 保存先フォルダ作成: ホーム配下(既にあればそのまま)
New-Item -ItemType Directory -Force -Path '~\GitBuild\before' | Out-Null
# 自分の global 設定の実効値と出所: 空やエラーなら未設定
git config --global --list --show-origin 2>&1 | Tee-Object -FilePath '~\GitBuild\before\git_global.txt'
# 自分の .gitconfig 本体のコピー: 元に戻す時はこのコピーを戻す
Copy-Item '~\.gitconfig' '~\GitBuild\before\gitconfig_global.bak' -ErrorAction SilentlyContinue
```

### 4-1 設定変更

```powershell
# user.name: 未設定→各自の名前(コミット作者名。global に置くのはこの2つだけ)
git config --global user.name '<YOUR NAME>'
# user.email: 未設定→各自のメール(コミット作者のメール)
git config --global user.email '<YOUR EMAIL>'
```

## 5. デーモン起動スクリプト(サーバー)

Windows の `git daemon` は `--detach` を使えないため、標準エラー出力を PowerShell で受けてログファイルへ書きます。ログローテーションのパターンは2つ。どちらか一方のスクリプトだけをタスクに登録します。

- 月次パターン: 日付の「日」(01〜31)で31ファイルを使い回し(約1ヶ月で一巡)
- 曜日パターン: 曜日(Monday〜Sunday)で7ファイルを使い回し(約1週間で一巡)

通常運用時は `--verbose` を外し、エラー発生時のみ記録することでログ出力を最小限に抑えます(構築・テスト時や障害調査時のみ、一時的に `--verbose` を追加してください)。同名ファイルは、その日の最初の書き込み時に「更新日が今日より古ければ削除」して作り直します(=ローテーション)。変数は `$f`(ログファイル名)だけです。

### 5-1. 月次パターン `D:\Git\scripts\Start-GitDaemon_Monthly.ps1`

```powershell
# ===== git daemon 起動(ログ=日付の「日」ごと git-daemon_01.log 〜 git-daemon_31.log)=====
# --reuseaddr: 無効(既定)→有効(再起動直後に Address already in use で起動失敗するのを防ぐ)
# --listen=0.0.0.0: IPv4/IPv6の全NIC(既定)→IPv4の全NIC(LANのNICだけに絞るならサーバーIPに置換)
# --port=9418: 9418(既定)→9418(明示。変更時はクライアントURLも同じ値に揃える(FWは無効前提のため設定なし))
# --base-path=D:/Git/repos: なし(既定)→指定(URL先頭を省略。git://IP:9418/Workspace0/Project1.git → D:/Git/repos/Workspace0/Project1.git)
# --export-all: 各リポジトリに git-daemon-export-ok が必要(既定)→全リポジトリ公開(リポジトリ側にファイルを置かなくてよい)
# --enable=receive-pack: push不可(既定)→全リポジトリでpush可(リポジトリ側の daemon.receivepack 設定は不要)
# --max-connections=64: 32(既定)→64(最大32名の同時操作に余裕を持たせる)
# --init-timeout=30: 0=無制限(既定)→30秒(接続後に要求が来ない接続を切る)
# --timeout=900: 0=無制限(既定)→900秒(15分。大容量バイナリの初回clone等で切断されないよう余裕を持たせる)
# --informative-errors: 汎用エラー(既定)→詳細エラー(社内のみのため原因調査を優先)
# --log-destination=stderr: 非detach時はstderr(既定)→明示(下のパイプでファイルへ書く。構築・調査時のみ --verbose を一時追加)
# 末尾 D:/Git/repos: 公開ホワイトリスト(配下のサブフォルダも公開)。--strict-paths は付けない(付けると新規リポジトリ毎にホワイトリスト追加が必要になり保守が増えるため)
& 'C:\Program Files\Git\cmd\git.exe' daemon `
    --reuseaddr `
    --listen=0.0.0.0 `
    --port=9418 `
    --base-path=D:/Git/repos `
    --export-all `
    --enable=receive-pack `
    --max-connections=64 `
    --init-timeout=30 `
    --timeout=900 `
    --informative-errors `
    --log-destination=stderr `
    D:/Git/repos 2>&1 | ForEach-Object {
        # ログファイル名: git-daemon_01.log 〜 git-daemon_31.log(その日の「日」)
        $f = 'D:\Git\logs\git-daemon_' + (Get-Date).ToString('dd') + '.log'
        # ローテーション: 前月の同じ「日」のファイルが残っていれば、当日の初回書き込み前に削除
        if ((Test-Path $f) -and ((Get-Item $f).LastWriteTime.Date -lt (Get-Date).Date)) { Remove-Item $f }
        # 追記: git daemon のstderr出力には時刻が付かないため、行頭に時刻を付ける
        Add-Content -Path $f -Encoding UTF8 -Value ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' ' + $_)
    }
```

### 5-2. 曜日パターン `D:\Git\scripts\Start-GitDaemon_Weekday.ps1`

月次との違いは、ログファイル名の行(`$f = ...`)だけです。デーモンのオプションとコメントは 5-1 と同一です。

```powershell
# ===== git daemon 起動(ログ=曜日ごと git-daemon_Monday.log 〜 git-daemon_Sunday.log)=====
# (オプションの意図コメントは 5-1 と同じ)
& 'C:\Program Files\Git\cmd\git.exe' daemon `
    --reuseaddr `
    --listen=0.0.0.0 `
    --port=9418 `
    --base-path=D:/Git/repos `
    --export-all `
    --enable=receive-pack `
    --max-connections=64 `
    --init-timeout=30 `
    --timeout=900 `
    --informative-errors `
    --log-destination=stderr `
    D:/Git/repos 2>&1 | ForEach-Object {
        # ログファイル名: git-daemon_Monday.log 〜 git-daemon_Sunday.log(OSの言語設定に依存しない英語の曜日名)
        $f = 'D:\Git\logs\git-daemon_' + (Get-Date).DayOfWeek.ToString() + '.log'
        # ローテーション: 先週の同じ曜日のファイルが残っていれば、当日の初回書き込み前に削除
        if ((Test-Path $f) -and ((Get-Item $f).LastWriteTime.Date -lt (Get-Date).Date)) { Remove-Item $f }
        # 追記: 行頭に時刻を付ける
        Add-Content -Path $f -Encoding UTF8 -Value ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' ' + $_)
    }
```

## 6. タスクスケジューラ(サーバー)

GUIで登録します。`taskschd.msc` を開き、右ペインの「タスクの作成…」から以下の4点だけ設定してください(変更前のタスク定義は 1-0 で `os_task.xml` に保存済みです)。

1. **全般タブ(実行権限とログイン不要設定)**
   - 名前: `Git Daemon`
   - 実行ユーザー: `Administrator`
   - 「ユーザーがログオンしているかどうかにかかわらず実行する」を選択(登録時にパスワード入力)
   - 「最上位の特権で実行する」にチェック
2. **トリガータブ(起動タイミング)**
   - 新規 → タスクの開始で **「スタートアップ時」** を選択(必要に応じて遅延 30秒 を指定)
3. **操作タブ(実行コマンドと作業フォルダ)**
   - 新規 → 操作「プログラムの開始」で以下を入力
   - プログラム/スクリプト: `powershell.exe`
   - 引数の追加: `-WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File D:\Git\scripts\Start-GitDaemon_Monthly.ps1`(曜日パターンなら `Start-GitDaemon_Weekday.ps1`)
   - 開始(オプション): `D:\Git\scripts`
4. **設定タブ(自動停止の解除)**
   - **「タスクを停止するまでの時間」のチェックを外す**(既定では「3日」にチェックが入っており、放置すると3日でデーモンが止まるため必ず外してください)

登録後、タスクを右クリック →「実行」で起動し、フェーズ10のテストを行います。Administrator のパスワードを変更したときは、タスクの「全般」タブでパスワードを入れ直してください。

## 7. リポジトリ作成(サーバー)

### 7-0 変更前の記録(before)

```powershell
# 保存先フォルダ作成: 既にあればそのまま
New-Item -ItemType Directory -Force -Path 'C:\GitBuild\before' | Out-Null
# 既存リポジトリの一覧(空=リポジトリなし)
Get-ChildItem 'D:\Git\repos' -Directory -Recurse -Depth 2 -ErrorAction SilentlyContinue | Tee-Object -FilePath 'C:\GitBuild\before\repos_listing.txt'
# 既に存在するリポジトリの設定(例: Workspace0/Project1.git。新規なら「存在しない」エラーでよい)
git -C D:/Git/repos/Workspace0/Project1.git config --local --list --show-origin 2>&1 | Tee-Object -FilePath 'C:\GitBuild\before\repo_Project1_config.txt'
```

### 7-1 作成

```powershell
# bare リポジトリ作成: 親フォルダ(Workspace0)も自動作成。HEAD は system の init.defaultBranch=main に従い main になる(--initial-branch は重複指定のため付けない)
git init --bare D:/Git/repos/Workspace0/Project1.git
# 確認: refs/heads/main と表示されること
git -C D:/Git/repos/Workspace0/Project1.git symbolic-ref HEAD
# --- 以下はあえて設定しない ---
# daemon.receivepack: 設定しない。デーモンの --enable=receive-pack で全リポジトリに効いている
# git-daemon-export-ok: 作らない。デーモンの --export-all で全リポジトリに効いている
# receive.* / core.logAllRefUpdates / transfer.fsckObjects: 設定しない。system(フェーズ3)で全リポジトリに効いている
# core.autocrlf: 設定しない。bare側の設定はクライアントに伝わらないため、フェーズ8の .gitattributes で配る
```

リポジトリを増やすときは、`git init --bare` のパスだけを変えます(例: `D:/Git/repos/Workspace0/Project2.git`、`D:/Git/repos/Workspace1/ProjectA.git`)。デーモンの再起動・FW・追加設定は不要です。

## 8. リポジトリ設定ファイル(.gitattributes)

リポジトリ直下に置きます(各リポジトリに1つ)。clone した全員に自動で効くため、クライアント側の個別設定は不要です。`* -text` が先頭で、後ろの行ほど優先されるので `binary` の行はその下に並べます。UTF-8(BOMなし)で保存してください。svg・rtf・dxf・dat・csv・cer・res・eml は判定が分かれるため含めていません(テキスト扱いでも改行は変換されません)。

```text
# ===== 改行: 一切変換しない =====
# 全ファイルの text 属性を解除(autocrlf や core.eol がどう設定されていても変換されない)
* -text

# ===== バイナリ扱い(binary = -diff -merge -text)=====
# --- Microsoft Office ---
*.xls binary
*.xlsx binary
*.xlsm binary
*.xlsb binary
*.xlt binary
*.xltx binary
*.xltm binary
*.xla binary
*.xlam binary
*.doc binary
*.docx binary
*.docm binary
*.dot binary
*.dotx binary
*.dotm binary
*.ppt binary
*.pptx binary
*.pptm binary
*.pps binary
*.ppsx binary
*.pot binary
*.potx binary
*.potm binary
*.mpp binary
*.vsd binary
*.vsdx binary
*.vsdm binary
*.vss binary
*.vst binary
*.mdb binary
*.accdb binary
*.accde binary
*.pub binary
*.one binary
*.msg binary
*.pst binary
*.ost binary
# --- PDF・日本の業務文書(一太郎、DocuWorks)・OpenDocument ---
*.pdf binary
*.jtd binary
*.jtt binary
*.xdw binary
*.xbd binary
*.odt binary
*.ods binary
*.odp binary
*.odg binary
# --- CAD(AutoCAD、JW_CAD、SXF)---
*.dwg binary
*.jww binary
*.jwc binary
*.sfc binary
# --- 画像 ---
*.png binary
*.jpg binary
*.jpeg binary
*.jpe binary
*.gif binary
*.bmp binary
*.ico binary
*.icns binary
*.cur binary
*.ani binary
*.tif binary
*.tiff binary
*.webp binary
*.heic binary
*.heif binary
*.psd binary
*.ai binary
*.eps binary
*.indd binary
*.xcf binary
# --- フォント ---
*.ttf binary
*.otf binary
*.ttc binary
*.woff binary
*.woff2 binary
*.eot binary
*.fon binary
# --- 音声・動画・Flash ---
*.mp3 binary
*.mp4 binary
*.m4a binary
*.m4v binary
*.wav binary
*.wma binary
*.wmv binary
*.avi binary
*.mov binary
*.mkv binary
*.flv binary
*.webm binary
*.ogg binary
*.ogv binary
*.aac binary
*.flac binary
*.mpg binary
*.mpeg binary
*.swf binary
*.fla binary
# --- 圧縮・アーカイブ(lzh/lha は日本でよく使われる)---
*.zip binary
*.7z binary
*.rar binary
*.lzh binary
*.lha binary
*.gz binary
*.tgz binary
*.tar binary
*.bz2 binary
*.xz binary
*.z binary
*.cab binary
*.arj binary
*.jar binary
*.war binary
*.ear binary
*.nupkg binary
# --- 実行ファイル・ライブラリ・ビルド成果物(frx=VB6、dcu/bpl=Delphi)---
*.exe binary
*.dll binary
*.lib binary
*.obj binary
*.o binary
*.a binary
*.so binary
*.dylib binary
*.pdb binary
*.ilk binary
*.exp binary
*.ocx binary
*.sys binary
*.drv binary
*.com binary
*.bin binary
*.msi binary
*.msm binary
*.msp binary
*.class binary
*.pyc binary
*.pyo binary
*.pyd binary
*.frx binary
*.dcu binary
*.bpl binary
*.elf binary
*.axf binary
# --- データベース・ダンプ ---
*.db binary
*.db3 binary
*.sqlite binary
*.sqlite3 binary
*.mdf binary
*.ldf binary
*.ndf binary
*.bak binary
*.dbf binary
*.dmp binary
*.sdf binary
# --- 仮想ディスク・イメージ ---
*.iso binary
*.img binary
*.vhd binary
*.vhdx binary
*.vmdk binary
*.wim binary
# --- 証明書・鍵ストア ---
*.pfx binary
*.p12 binary
*.jks binary
*.keystore binary
*.der binary
# --- ヘルプ・ショートカット ---
*.chm binary
*.hlp binary
*.lnk binary
# --- モバイルアプリ ---
*.apk binary
*.aab binary
*.ipa binary
# --- データファイル ---
*.pkl binary
*.npy binary
*.h5 binary
*.parquet binary
```

コミットとpush(最初の1回)。clone後、作業フォルダ直下に上の内容を `.gitattributes` として保存してから実行します。

```powershell
# 8-0 変更前の記録(既存リポジトリへ適用する場合のみ。新規の空リポジトリでは不要): 変更前の改行状態を保存
git -C C:/Work/Project1 ls-files --eol | Tee-Object -FilePath 'C:\GitBuild\before\repo_Project1_eol.txt'
# clone: 接続先は常にポート付き(新規の空リポジトリでは空リポジトリの警告が出るが正常)
git clone git://192.168.1.10:9418/Workspace0/Project1.git C:/Work/Project1
# ここで C:\Work\Project1 の直下に .gitattributes を保存する(手作業)
# add: .gitattributes をステージ
git -C C:/Work/Project1 add .gitattributes
# commit: 設定ファイルの追加を記録
git -C C:/Work/Project1 commit -m 'Add .gitattributes: no EOL conversion, binary extensions'
# push: 初回は origin main を明示
git -C C:/Work/Project1 push origin main
```

## 9. クライアント(Windows 11)

1. フェーズ2: Git for Windows を全て既定でインストール
2. フェーズ3-0 → 3-1(管理者 PowerShell。サーバーと同じコマンド)
3. フェーズ4-0 → 4-1(自分のアカウント。user.name と user.email だけ自分の値)
4. 作業フォルダに clone(接続先は常にポート付き)

```powershell
# 初回: clone(例: C:/Work 配下)
git clone git://192.168.1.10:9418/Workspace0/Project1.git C:/Work/Project1
# 既存のローカルリポジトリを紐づける場合: 接続先を登録
git remote add origin git://192.168.1.10:9418/Workspace0/Project1.git
# 日常: サーバーの変更を取り込む
git pull
# 日常: 自分のコミットを反映
git push
# 接続先の確認(ポートが入っていること)
git remote -v
```

## 10. テスト

※通常運用スクリプトでは `--verbose` を外しているため、正常アクセス時のログ出力を確認したい場合は、テスト中のみ起動スクリプトに `--verbose` を一時追加し、テスト完了後に `--verbose` を外してタスクを再起動してください。

### サーバー側

```powershell
# テスト用リポジトリ作成(終わったら削除する)
git init --bare D:/Git/repos/Workspace0/Test1.git
# デーモン起動確認: 9418 が LISTEN であること
Get-NetTCPConnection -LocalPort 9418 -State Listen
# サーバー自身から参照: エラーにならないこと
git ls-remote git://127.0.0.1:9418/Workspace0/Test1.git
# ログ確認(テスト用に --verbose を一時追加している場合、接続が記録されていること)
Get-Content ('D:\Git\logs\git-daemon_' + (Get-Date).ToString('dd') + '.log') -Tail 20
```

### クライアント側

```powershell
# 疎通: TcpTestSucceeded が True であること
Test-NetConnection 192.168.1.10 -Port 9418
# 参照: エラーにならないこと(空のリポジトリは何も表示されない)
git ls-remote git://192.168.1.10:9418/Workspace0/Test1.git
# clone
git clone git://192.168.1.10:9418/Workspace0/Test1.git C:/Work/Test1
# 改行無変換の確認用に CRLF のファイルと LF のファイルを作る(パスは絶対パス)
[IO.File]::WriteAllText('C:\Work\Test1\crlf.txt', ('a' + [char]13 + [char]10 + 'b' + [char]13 + [char]10))
[IO.File]::WriteAllText('C:\Work\Test1\lf.txt', ('a' + [char]10 + 'b' + [char]10))
git -C C:/Work/Test1 add crlf.txt lf.txt
# 確認: 警告が出ず、i/ と w/ が一致すること(変換なし)
git -C C:/Work/Test1 ls-files --eol
git -C C:/Work/Test1 commit -m 'test: eol'
# push: push.autoSetupRemote により初回でも git push だけで通ること
git -C C:/Work/Test1 push
# force push の拒否確認: non-fast-forward で拒否されること(receive.denyNonFastForwards=true)
git -C C:/Work/Test1 commit --amend -m 'test: amended'
git -C C:/Work/Test1 push --force
# リモートブランチ削除の拒否確認: deleting a remote branch is not allowed で拒否されること(receive.denyDeletes=true)
git -C C:/Work/Test1 push origin --delete main
```

別のPCから同じURLを clone して `git pull` で内容が取れること、別ユーザーの push が自分の pull に反映されることも確認します。最後に `--verbose` を一時追加していた場合は元に戻してタスクを再起動し、サーバーを再起動してログオンしない状態で 9418 が LISTEN になること(自動起動)を確認後、テスト用リポジトリを削除します。

```powershell
# テスト用リポジトリ削除(サーバー側)
Remove-Item -Recurse -Force D:/Git/repos/Workspace0/Test1.git
```

## 11. 保守と注意点

```powershell
# デーモン停止
Stop-ScheduledTask -TaskName 'Git Daemon'
# デーモン起動
Start-ScheduledTask -TaskName 'Git Daemon'
# 残プロセスの確認: 停止後に残っていないこと(残る場合は Stop-Process で終了)
Get-Process git, git-daemon -ErrorAction SilentlyContinue
# 設定の確認: 値と出所(system / global / local)
git config --list --show-origin
```

- ポート変更: ①タスクを停止 ②両方の起動スクリプトの `--port=` ③全員の接続先を `git remote set-url origin git://192.168.1.10:<新ポート>/Workspace0/Project1.git` で更新 ④タスクを起動
- リポジトリ追加: フェーズ7のコマンドのパスを変えるだけ。.gitattributes は新リポジトリごとにフェーズ8の手順で追加
- 設定を元に戻す: `C:\GitBuild\before\` の保存値を参照。設定ファイルは `.bak` を元の場所へ戻し、個別の値は `git config --system --unset <キー>` で外す
- フェーズ3(system)は Git for Windows の更新で上書きされることがあります。更新後に3-1を再実行してください(何度実行しても同じ結果)
- git:// は暗号化も認証もありません。LAN内の誰でも push でき、user.name は自己申告です。force push やブランチ削除の拒否は履歴保護の最低限であり、バックアップとして `D:\Git\repos` の定期コピーを別途取ってください
- `transfer.fsckObjects true` は破損データの混入を防ぎますが、巨大リポジトリの初回移行や古いツールで作られた過去資産の取り込みでエラーになる場合のみ、一時的に `false` に変更して取り込み後に `true` へ戻してください
- NTP同期なしのため、サーバー時刻がずれるとデーモンログの時刻がずれます(コミット時刻はクライアントPCの時刻)
- Shift\_JIS のソースは変換されずそのまま保存されます。UTF-8 でない差分は文字化けして見えることがありますが、保存内容は変わっていません

### 未検証・要確認

- 本ガイドは Web 検索をせず知識ベースで作成し、実機では未検証です。最終確認は公式ドキュメント(https://git-scm.com/docs/git-daemon 、`git help daemon` `git help config` `git help gitattributes`)で行ってください
- `--timeout` は公式上「サブリクエスト単位のタイムアウト」です。大容量の push で切断される場合は値を延ばしてください(要確認)
- タスクの「終了」で子プロセスの git daemon も止まるか(要確認)。止まらない場合は `Stop-Process -Name git-daemon -Force`
- `safe.directory '*'` のワイルドカードは比較的新しい Git for Windows が必要です(2.35.3以降、要確認)
- 日本語を含む `git log` が PowerShell で `<E3>` のように崩れる場合は `less` の文字コード指定が必要です: `[Environment]::SetEnvironmentVariable('LESSCHARSET','utf-8','User')` を実行して PowerShell を開き直す(要確認)
- `~` を使う 4-0 の `Tee-Object -FilePath` が Windows PowerShell 5.1 で解決されない場合は `~` を `C:\Users\<ユーザー名>` に置き換えてください(要確認)
- system 設定の `core.editor notepad` が Git for Windows の既定の起動方法で問題なく使えるか(要確認。使えない場合は `C:\Windows\notepad.exe` のフルパス指定に変える)


# Git daemon 環境 チューニング・見直しポイント（Windows 環境向け・完全版）

今回の構成（および元ガイドの Windows 構成）を **Windows 環境で本格運用・規模拡大する場合に「変更を検討するならここ」** という観点を、全 39 項目漏れなくチェックしてまとめた資料です。

Windows は macOS/Linux と比べて **「外部コマンド（`.exe`）の起動コスト」** と **「`git daemon` の仕様差」** が大きく影響するため、特にログ周りと常駐管理が最重要ポイントになります。

---

## 1. 負荷・出力増大（CPU・時間・ディスク容量）の懸念がある項目

### ① 最重要：起動スクリプトのログ付与ループ ＋ `--verbose` ＋ `--log-destination=stderr`
- **Windows 特有の懸念点**
  1. **Git Bash（`bash.exe`）で `while read` ＋ `date` を回すのは重い**
     Windows では `date.exe` のような外部プログラムを 1 回起動するコストが macOS よりずっと大きいため、1 行ごとに `date` を 3〜4 回呼ぶ構成で大量アクセスを受けると CPU・処理遅延が目立ちます。
  2. **コマンドプロンプト（`.bat` / `cmd.exe`）の `FOR /F` は使えない**
     `cmd.exe` の `FOR /F` は「相手コマンドが終了するまで出力を溜め込む」ため、常駐する `git daemon` のリアルタイムログ出力には使えません。
  3. **1 ファイルの肥大化**
     日次/曜日ローテーションでファイル数は増えませんが、1 日あたりのアクセスが極端に多いと 1 ファイルが大きくなります。

- **変更を検討するならここ**
  1. **PowerShell でパイプ処理する（外部 `.exe` を起動しない）**
     `Get-Date` は PowerShell 内部の命令なので、外部プロセス起動なしで日時を付けられます。さらに **「日付の切り替わり判定を変数で持つ」＋「`StreamWriter` を使う」** と、大量ログでもほぼゼロ負荷になります。
     ```powershell
     $currentDay = ""
     $writer = $null

     & "C:\Program Files\Git\bin\git.exe" daemon `
       --reuseaddr --listen=127.0.0.1 --port=9418 `
       --base-path=D:\Git\repos --export-all --enable=receive-pack `
       --verbose --log-destination=stderr D:\Git\repos 2>&1 | ForEach-Object {
         $now = Get-Date
         $day = $now.ToString("dd")
         if ($day -ne $currentDay) {
             if ($writer) { $writer.Dispose() }
             $logPath = "D:\Git\logs\git-daemon_$day.log"
             if ((Test-Path $logPath) -and ((Get-Item $logPath).LastWriteTime.ToString("yyyy-MM-dd") -ne $now.ToString("yyyy-MM-dd"))) {
                 Remove-Item $logPath -Force
             }
             $writer = [System.IO.StreamWriter]::new($logPath, $true, [System.Text.Encoding]::UTF8)
             $writer.AutoFlush = $true
             $currentDay = $day
         }
         $writer.WriteLine("$($now.ToString('yyyy-MM-dd HH:mm:ss')) $_")
     }
     ```
  2. **通常時のアクセスログが不要なら `--verbose` を外す**
     エラー時のみ記録されるようになり、書き込み自体を最小化できます。

### ② `transfer.fsckObjects = true`（`etc/gitconfig`）
- **現在の設定**
  `clone` / `push` / `fetch` のたびに全オブジェクトの整合性チェックを実行します。
- **懸念点**
  - 数 GB のリポジトリや大量の Office/CAD/画像ファイルを一括 `push` する際、検査時間の分だけ遅くなります。
  - 古い Git 互換ツール等で作られた「軽微な形式違反コミット」を含む過去資産を移行 `push` すると、整合性エラーで拒否されることがあります。
- **変更を検討するならここ**
  - 巨大リポジトリの初回移行時だけ一時的に `false` にするか、規模に応じて見直します。

### ③ `--timeout=300`（`git daemon`）
- **現在の設定**
  無通信 300 秒（5 分）で自動切断します。
- **懸念点**
  - 巨大リポジトリの初回 `clone` がサーバー側の圧縮計算中に 5 分を超えて切れることがあります。
- **変更を検討するならここ**
  - `--timeout=900`（15 分）〜`1800`（30 分）へ延長します。

### ④ `core.logAllRefUpdates = true`（`etc/gitconfig`）
- **現在の設定**
  サーバー側（bare リポジトリ）にも全ブランチの更新履歴（`logs/refs/heads/...`）を記録します。
- **懸念点**
  - CI ツール等が 1 日に何千回もブランチ作成・削除・`push` を繰り返す環境では、`logs/` フォルダが少しずつ肥大化します（`git gc` が走らないと残り続けます）。
- **変更を検討するならここ**
  - 大量の自動ブランチ生成を行うサーバーでは、定期的な `git gc` 実行や `false` への変更を検討します。

### ⑤ `--max-connections=64` / `--init-timeout=30`（`git daemon`）
- **現在の設定**
  同時接続上限を 64、初期応答待ち上限を 30 秒にしています。
- **懸念点**
  - 大規模 CI で 64 接続を超えると新規接続が待たされる／拒否されます（無制限にするとメモリ不足になる安全弁でもあります）。
  - 初期ハンドシェイクに 30 秒以上かかる低速環境では切断されることがあります。
- **変更を検討するならここ**
  - 同時接続数が増える場合は `--max-connections=128` 等へ引き上げます。

---

## 2. Windows 固有の仕様差・プロセス管理

| 対象 | Windows での違い・注意点 | 変更・対応を検討するならここ |
|---|---|---|
| **`--detach` / `--pid-file` / `syslog`** | Windows 版の `git daemon` には `--detach`、`--pid-file`、`--log-destination=syslog` がありません。 | タスクスケジューラから PowerShell スクリプト自体を非表示（`-WindowStyle Hidden`）で常駐起動し、停止時はプロセス名／コマンドラインで終了させる。 |
| **`core.longpaths = true`** | Git 側で有効にしても、**Windows OS 側の 260 文字パス制限が無効になっていないとエクスプローラーや他アプリで開けない**ことがあります。 | 深い階層のファイルを扱う場合は、Windows のグループポリシー／レジストリ（`LongPathsEnabled = 1`）も合わせて有効化する。 |
| **`core.editor = vi`** | Git Bash を使わず通常のコマンドプロンプト／PowerShell から `git commit`（引数なし）を打つと、`vi` 操作に慣れていない利用者が迷うことがあります。 | 利用者が直接操作する端末では `notepad` や VS Code（`code --wait`）等への変更を検討。 |

---

## 3. 運用・セキュリティ・互換性上の不都合になり得る項目

| 対象 | 現在の設定 | 懸念・不都合の内容 | 変更を検討するならここ |
|---|---|---|---|
| **`--listen` の IP 指定**<br>**`--export-all`**<br>**`--enable=receive-pack`** | 認証なしで全リポジトリ読み書き可 | 検証用（`127.0.0.1`）では安全ですが、社内 LAN（例：`192.168.1.10`）へ公開すると **認証なしで誰でも全リポジトリの書き換え・削除が可能** になります。 | 実運用で社内公開する場合は、`git daemon` ではなく **OpenSSH（Windows 標準機能）** や **HTTPS（認証付きサーバー）** へ移行する。 |
| **`--informative-errors`** | 詳細エラーを返却 | 外部公開時はリポジトリ構成やパスの存在有無を推測される材料になります。 | 信頼できる閉域網・検証環境以外では外す。 |
| **`receive.denyDeletes = false`**<br>＋ **`fetch.prune = true`** | サーバー削除許可 ＋ 取得時に手元の追跡参照も削除 | 誤ってブランチを `--delete` するとサーバーから消え、他の人の `fetch` で手元の `origin/ブランチ名` も即座に消えます。 | 誤削除を防ぎたい場合は `receive.denyDeletes = true` に変更する。 |
| **`receive.denyNonFastForwards = true`** | 強制上書き（`push --force`）を拒否 | 安全策として有効ですが、どうしても過去の履歴を修正して強制上書きしたい作業時に弾かれます。 | 原則 `true` 維持（例外時は管理者のみ一時解除または別ブランチ運用）。 |
| **`core.autocrlf = false`**<br>＋ **`.gitattributes (* -text)`** | 改行コードを一切変換しない | Git が自動変換しないため、開発者のエディタ設定によって LF と CRLF が混在する可能性があります。 | エディタ共通設定（`.editorconfig`）で改行コードを統一する運用にする。 |
| **`safe.directory = *`** | 全ディレクトリの所有者警告を無効化 | 複数ユーザーがログインする共用 Windows PC では、他人が置いた不正なリポジトリを誤って触るリスクが上がります。 | 共用端末では `*` を外し、信頼できるフォルダだけを個別指定する。 |
| **`pull.rebase = false`**<br>＋ **`merge.ff = true`** | 分岐時はマージコミット作成、未分岐時は一直線 | 分岐が多いチームでは履歴グラフに `Merge branch ...` コミットが増えます。 | 直線履歴を強制したいチームでは `pull.rebase = true` を検討。 |

---

## 4. 変更不要（負荷ゼロ・またはむしろ軽くなる設定）の全一覧

以下の項目は、**処理負荷・出力増大・不都合の懸念がなく、そのまま維持して問題ない設定**です：

- **むしろ処理・通信が軽くなる設定**
  - `protocol.version = 2`（不要な参照一覧の送信を省き高速化）
  - `.gitattributes` の拡張子別 `binary` 指定（重い Office・PDF・画像・ZIP 等の差分計算・マージ計算をスキップ）
- **安全・負荷ゼロで維持すべき設定**
  - `core.symlinks = false`（Windows では管理者権限なしでシンボリックリンク作成が失敗しやすいため `false` 維持が安全）
  - `init.defaultBranch = main` / `core.safecrlf = false` / `core.quotepath = false` / `i18n.commitEncoding = utf-8` / `i18n.logOutputEncoding = utf-8` / `gui.encoding = utf-8` / `color.ui = auto` / `push.default = simple` / `push.autoSetupRemote = true` / `user.name` / `user.email`
  - `git daemon`：`--port=9418` / `--reuseaddr` / `--base-path` / 末尾ディレクトリ引数





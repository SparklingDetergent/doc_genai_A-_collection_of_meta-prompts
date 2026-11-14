


実行環境（macOS 26.5.2 / Apple Silicon / zsh / Git 2.55.0 / ステートレス実行 / サンドボックス制約）向けに、元のガイドの設計方針（「上位一括・下位非重複」「変更前の記録保存」「変数を極力排した直書き」「全設定値の踏襲」）をそのまま維持して再設計。
主な環境適応ポイント
 * ディレクトリとサンドボックス対応: デフォルトの書き込み許可領域であるワークスペース配下（/Users/user/.antigravity/global-backup/git-sandbox）にベースパスを集約し、外部パスや sudo（/opt/homebrew/etc/gitconfig への書き込み）を不要にするため、検証用環境変数 GIT_CONFIG_SYSTEM を用いる構成にしています。
 * デーモン起動のmacOS最適化: macOS の /opt/homebrew/bin/git daemon は --detach と --pid-file が正常に機能するため、バックグラウンド常駐と確実な停止・再起動がコマンド一発で完結します。
 * 非対話・ステートレス設計: 毎回新しいシェルで実行される前提に合わせ、全コマンドを絶対パス基準・1コマンド完結型にしています。
Git daemon 検証構築ガイド（macOS 26.5.2 / Apple Silicon 環境向け）
ローカル検証用（127.0.0.1）・認証なし・全リポジトリ公開&push可の Git daemon (git://) 構成です。フェーズごとに独立しているため、上から順に実行してください。
0. 前提・設計方針・置換ポイント
 * 検証環境: macOS 26.5.2 (arm64) / zsh 5.9 / Git 2.55.0 (/opt/homebrew/bin/git)
 * プロトコル: git://（暗号化・認証なし）。接続URLは常にポート明示 git://127.0.0.1:9418/Workspace0/Project1.git
 * サンドボックス対応:
   * 全データをワークスペース配下 /Users/user/.antigravity/global-backup/git-sandbox に集約し、サンドボックス外へのアクセスや sudo を不要にしています。
   * Gitのシステム設定（本来は /opt/homebrew/etc/gitconfig）は、環境変数 GIT_CONFIG_SYSTEM で専用ファイルへ隔離して検証します。
 * 設定の優先順位: デーモン起動オプション > Gitシステム設定 > リポジトリ。Gitの設定は system で行えるものを全て system に置き、global（検証時は GIT_CONFIG_GLOBAL で隔離）は user.name と user.email だけにします。
 * スクリプト方針: 変数を極力使わず値を直書きし、ステートレスなコマンド呼び出しでも安全に動くよう絶対パスで記述します。
| 項目 | macOS検証環境の値 | 元ガイド（Windows）の対応 |
|---|---|---|
| ベース領域 | /Users/user/.antigravity/global-backup/git-sandbox | D:\Git & C:\GitBuild |
| 変更前記録 | /Users/user/.antigravity/global-backup/git-sandbox/before | C:\GitBuild\before |
| 接続先IP:ポート | 127.0.0.1:9418 | 192.168.1.10:9418 |
| リポジトリ置き場 | /Users/user/.antigravity/global-backup/git-sandbox/repos | D:\Git\repos |
| ログ置き場 | /Users/user/.antigravity/global-backup/git-sandbox/logs | D:\Git\logs |
| スクリプト置き場 | /Users/user/.antigravity/global-backup/git-sandbox/scripts | D:\Git\scripts |
| 作業フォルダ | /Users/user/.antigravity/global-backup/git-sandbox/work | C:\Work |
| System設定ファイル | /Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig | C:\Program Files\Git\etc\gitconfig |
| Global設定ファイル | /Users/user/.antigravity/global-backup/git-sandbox/home/.gitconfig | C:\Users\<ユーザー>\.gitconfig |
1. OS・ディレクトリ設定
1-0 変更前の記録（before）
mkdir -p '/Users/user/.antigravity/global-backup/git-sandbox/before'
hostname | tee '/Users/user/.antigravity/global-backup/git-sandbox/before/os_hostname.txt'
date -Iseconds | tee '/Users/user/.antigravity/global-backup/git-sandbox/before/os_date.txt'
ifconfig lo0 | tee '/Users/user/.antigravity/global-backup/git-sandbox/before/os_ipconfig.txt'
ls -laR '/Users/user/.antigravity/global-backup/git-sandbox/repos' 2>/dev/null | tee '/Users/user/.antigravity/global-backup/git-sandbox/before/os_dir_listing.txt'
lsof -iTCP:9418 -sTCP:LISTEN 2>/dev/null | tee '/Users/user/.antigravity/global-backup/git-sandbox/before/os_listen.txt'

1-1 フォルダ作成
mkdir -p \
  '/Users/user/.antigravity/global-backup/git-sandbox/repos' \
  '/Users/user/.antigravity/global-backup/git-sandbox/logs' \
  '/Users/user/.antigravity/global-backup/git-sandbox/scripts' \
  '/Users/user/.antigravity/global-backup/git-sandbox/etc' \
  '/Users/user/.antigravity/global-backup/git-sandbox/home' \
  '/Users/user/.antigravity/global-backup/git-sandbox/work'

2. Git バイナリ確認
既に /opt/homebrew/bin/git (2.55.0) が導入済みのためインストールは不要です。実行バイナリと git-daemon サブコマンドの存在を確認します。
/opt/homebrew/bin/git --version
/opt/homebrew/bin/git daemon --help | head -n 5

3. Git システム設定
既存の環境（/Users/user/.gitconfig 等）を汚さないよう、GIT_CONFIG_SYSTEM を指定して設定を書き込みます。
3-0 変更前の記録（before）
mkdir -p '/Users/user/.antigravity/global-backup/git-sandbox/before'
/opt/homebrew/bin/git --version | tee '/Users/user/.antigravity/global-backup/git-sandbox/before/git_version.txt'
/opt/homebrew/bin/git config --list --show-origin 2>&1 | tee '/Users/user/.antigravity/global-backup/git-sandbox/before/git_effective.txt'
/opt/homebrew/bin/git config --system --list --show-origin 2>&1 | tee '/Users/user/.antigravity/global-backup/git-sandbox/before/git_system.txt'
/opt/homebrew/bin/git config --global --list --show-origin 2>&1 | tee '/Users/user/.antigravity/global-backup/git-sandbox/before/git_global.txt'
cp '/opt/homebrew/etc/gitconfig' '/Users/user/.antigravity/global-backup/git-sandbox/before/gitconfig_system.bak' 2>/dev/null || true
cp '/Users/user/.gitconfig' '/Users/user/.antigravity/global-backup/git-sandbox/before/gitconfig_global.bak' 2>/dev/null || true

3-1 設定変更
元ガイドの全22項目をそのまま設定します（※ core.editor は macOS 非対話環境でも安全に扱える nano または vi とするか、元方針に合わせて指定します。ここでは元ガイド準拠の意図をコメントで残しつつ、macOS標準の vi にしています）。
touch '/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig'

GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' /opt/homebrew/bin/git config --system core.autocrlf false
GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' /opt/homebrew/bin/git config --system core.safecrlf false
GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' /opt/homebrew/bin/git config --system core.quotepath false
GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' /opt/homebrew/bin/git config --system core.symlinks false
GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' /opt/homebrew/bin/git config --system core.longpaths true
GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' /opt/homebrew/bin/git config --system core.editor vi
GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' /opt/homebrew/bin/git config --system core.logAllRefUpdates true
GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' /opt/homebrew/bin/git config --system init.defaultBranch main
GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' /opt/homebrew/bin/git config --system protocol.version 2
GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' /opt/homebrew/bin/git config --system safe.directory '*'
GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' /opt/homebrew/bin/git config --system i18n.commitEncoding utf-8
GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' /opt/homebrew/bin/git config --system i18n.logOutputEncoding utf-8
GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' /opt/homebrew/bin/git config --system gui.encoding utf-8
GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' /opt/homebrew/bin/git config --system color.ui auto
GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' /opt/homebrew/bin/git config --system pull.rebase false
GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' /opt/homebrew/bin/git config --system push.default simple
GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' /opt/homebrew/bin/git config --system push.autoSetupRemote true
GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' /opt/homebrew/bin/git config --system fetch.prune true
GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' /opt/homebrew/bin/git config --system merge.ff true
GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' /opt/homebrew/bin/git config --system receive.denyNonFastForwards true
GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' /opt/homebrew/bin/git config --system receive.denyDeletes false
GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' /opt/homebrew/bin/git config --system transfer.fsckObjects true

4. Git グローバル設定
user.name と user.email だけを設定します。
4-0 変更前の記録（before）
GIT_CONFIG_GLOBAL='/Users/user/.antigravity/global-backup/git-sandbox/home/.gitconfig' /opt/homebrew/bin/git config --global --list --show-origin 2>&1 | tee '/Users/user/.antigravity/global-backup/git-sandbox/before/git_global_sandbox.txt'

4-1 設定変更
touch '/Users/user/.antigravity/global-backup/git-sandbox/home/.gitconfig'

GIT_CONFIG_GLOBAL='/Users/user/.antigravity/global-backup/git-sandbox/home/.gitconfig' /opt/homebrew/bin/git config --global user.name 'Test User'
GIT_CONFIG_GLOBAL='/Users/user/.antigravity/global-backup/git-sandbox/home/.gitconfig' /opt/homebrew/bin/git config --global user.email 'test@example.local'

5. デーモン起動スクリプト（サーバー）
macOS（Unix系）では git daemon の --detach と --pid-file が使えるため、バックグラウンド常駐とプロセス管理がシンプルに行えます。標準エラー出力（--log-destination=stderr）をローテーション付きログへ書き出す構成です。
5-1. 月次パターン start-git-daemon-monthly.sh
cat <<'EOF' > '/Users/user/.antigravity/global-backup/git-sandbox/scripts/start-git-daemon-monthly.sh'
#!/bin/zsh
set -euo pipefail

export GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig'
export GIT_CONFIG_GLOBAL='/Users/user/.antigravity/global-backup/git-sandbox/home/.gitconfig'

# 既存プロセスが動いていれば停止
if [ -f '/Users/user/.antigravity/global-backup/git-sandbox/logs/git-daemon.pid' ]; then
  OLD_PID=$(cat '/Users/user/.antigravity/global-backup/git-sandbox/logs/git-daemon.pid')
  kill "$OLD_PID" 2>/dev/null || true
  rm -f '/Users/user/.antigravity/global-backup/git-sandbox/logs/git-daemon.pid'
fi

# バックグラウンドで起動し、stderrを日付ローテーションログへ追記
nohup /bin/zsh -c '
  /opt/homebrew/bin/git daemon \
    --reuseaddr \
    --listen=127.0.0.1 \
    --port=9418 \
    --base-path=/Users/user/.antigravity/global-backup/git-sandbox/repos \
    --export-all \
    --enable=receive-pack \
    --max-connections=64 \
    --init-timeout=30 \
    --timeout=300 \
    --informative-errors \
    --verbose \
    --log-destination=stderr \
    --pid-file=/Users/user/.antigravity/global-backup/git-sandbox/logs/git-daemon.pid \
    /Users/user/.antigravity/global-backup/git-sandbox/repos 2>&1 | while IFS= read -r line; do
      f="/Users/user/.antigravity/global-backup/git-sandbox/logs/git-daemon_$(date +%d).log"
      if [ -f "$f" ] && [ "$(date -r "$f" +%Y-%m-%d)" != "$(date +%Y-%m-%d)" ]; then
        rm -f "$f"
      fi
      printf "%s %s\n" "$(date "+%Y-%m-%d %H:%M:%S")" "$line" >> "$f"
    done
' >/dev/null 2>&1 &

sleep 1
EOF
chmod +x '/Users/user/.antigravity/global-backup/git-sandbox/scripts/start-git-daemon-monthly.sh'

5-2. 曜日パターン start-git-daemon-weekday.sh
ログファイル名のフォーマットを LC_ALL=C date +%A（Monday〜Sunday）に変えた版です。
cat <<'EOF' > '/Users/user/.antigravity/global-backup/git-sandbox/scripts/start-git-daemon-weekday.sh'
#!/bin/zsh
set -euo pipefail

export GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig'
export GIT_CONFIG_GLOBAL='/Users/user/.antigravity/global-backup/git-sandbox/home/.gitconfig'

if [ -f '/Users/user/.antigravity/global-backup/git-sandbox/logs/git-daemon.pid' ]; then
  OLD_PID=$(cat '/Users/user/.antigravity/global-backup/git-sandbox/logs/git-daemon.pid')
  kill "$OLD_PID" 2>/dev/null || true
  rm -f '/Users/user/.antigravity/global-backup/git-sandbox/logs/git-daemon.pid'
fi

nohup /bin/zsh -c '
  /opt/homebrew/bin/git daemon \
    --reuseaddr \
    --listen=127.0.0.1 \
    --port=9418 \
    --base-path=/Users/user/.antigravity/global-backup/git-sandbox/repos \
    --export-all \
    --enable=receive-pack \
    --max-connections=64 \
    --init-timeout=30 \
    --timeout=300 \
    --informative-errors \
    --verbose \
    --log-destination=stderr \
    --pid-file=/Users/user/.antigravity/global-backup/git-sandbox/logs/git-daemon.pid \
    /Users/user/.antigravity/global-backup/git-sandbox/repos 2>&1 | while IFS= read -r line; do
      f="/Users/user/.antigravity/global-backup/git-sandbox/logs/git-daemon_$(LC_ALL=C date +%A).log"
      if [ -f "$f" ] && [ "$(date -r "$f" +%Y-%m-%d)" != "$(date +%Y-%m-%d)" ]; then
        rm -f "$f"
      fi
      printf "%s %s\n" "$(date "+%Y-%m-%d %H:%M:%S")" "$line" >> "$f"
    done
' >/dev/null 2>&1 &

sleep 1
EOF
chmod +x '/Users/user/.antigravity/global-backup/git-sandbox/scripts/start-git-daemon-weekday.sh'

6. デーモン起動（タスクスケジューラ相当）
ステートレス検証環境のため launchd（~/Library/LaunchAgents はサンドボックス外）への登録は行わず、起動スクリプトを直接呼び出して常駐させます。
/Users/user/.antigravity/global-backup/git-sandbox/scripts/start-git-daemon-monthly.sh

7. リポジトリ作成
7-0 変更前の記録（before）
ls -laR '/Users/user/.antigravity/global-backup/git-sandbox/repos' 2>/dev/null | tee '/Users/user/.antigravity/global-backup/git-sandbox/before/repos_listing.txt'

7-1 作成
GIT_CONFIG_SYSTEM を渡すことで、init.defaultBranch=main と core.logAllRefUpdates=true が自動適用されます。
GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' \
  /opt/homebrew/bin/git init --bare '/Users/user/.antigravity/global-backup/git-sandbox/repos/Workspace0/Project1.git'

# 確認: refs/heads/main と表示されること
/opt/homebrew/bin/git -C '/Users/user/.antigravity/global-backup/git-sandbox/repos/Workspace0/Project1.git' symbolic-ref HEAD

8. リポジトリ設定ファイル（.gitattributes）
元ガイドと同一の .gitattributes を配置して初回コミット＆pushします。
GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' \
GIT_CONFIG_GLOBAL='/Users/user/.antigravity/global-backup/git-sandbox/home/.gitconfig' \
  /opt/homebrew/bin/git clone 'git://127.0.0.1:9418/Workspace0/Project1.git' '/Users/user/.antigravity/global-backup/git-sandbox/work/Project1'

cat <<'EOF' > '/Users/user/.antigravity/global-backup/git-sandbox/work/Project1/.gitattributes'
# ===== 改行: 一切変換しない =====
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
# --- 圧縮・アーカイブ ---
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
# --- 実行ファイル・ライブラリ・ビルド成果物 ---
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
EOF

GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' \
GIT_CONFIG_GLOBAL='/Users/user/.antigravity/global-backup/git-sandbox/home/.gitconfig' \
  /opt/homebrew/bin/git -C '/Users/user/.antigravity/global-backup/git-sandbox/work/Project1' add .gitattributes

GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' \
GIT_CONFIG_GLOBAL='/Users/user/.antigravity/global-backup/git-sandbox/home/.gitconfig' \
  /opt/homebrew/bin/git -C '/Users/user/.antigravity/global-backup/git-sandbox/work/Project1' commit -m 'Add .gitattributes: no EOL conversion, binary extensions'

GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig' \
GIT_CONFIG_GLOBAL='/Users/user/.antigravity/global-backup/git-sandbox/home/.gitconfig' \
  /opt/homebrew/bin/git -C '/Users/user/.antigravity/global-backup/git-sandbox/work/Project1' push origin main

9. クライアント操作例（検証ラッパー）
ステートレス環境で毎回の GIT_CONFIG_SYSTEM / GIT_CONFIG_GLOBAL 指定を省略してテストするためのラッパースクリプトを用意します。
cat <<'EOF' > '/Users/user/.antigravity/global-backup/git-sandbox/scripts/sgit.sh'
#!/bin/zsh
export GIT_CONFIG_SYSTEM='/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig'
export GIT_CONFIG_GLOBAL='/Users/user/.antigravity/global-backup/git-sandbox/home/.gitconfig'
exec /opt/homebrew/bin/git "$@"
EOF
chmod +x '/Users/user/.antigravity/global-backup/git-sandbox/scripts/sgit.sh'

以降、クライアント操作は /Users/user/.antigravity/global-backup/git-sandbox/scripts/sgit.sh 経由でそのまま実行できます。
10. テスト（全自動検証フロー）
サーバー確認・クライアント疎通・改行コード無変換（CRLF/LF保持）・自動upstream設定・force push拒否のすべてを一括検証します。
# 1. テスト用リポジトリ作成
/Users/user/.antigravity/global-backup/git-sandbox/scripts/sgit.sh init --bare '/Users/user/.antigravity/global-backup/git-sandbox/repos/Workspace0/Test1.git'

# 2. デーモン待ち受け確認 (9418 が LISTEN であること)
lsof -iTCP:9418 -sTCP:LISTEN

# 3. リモート参照テスト
/Users/user/.antigravity/global-backup/git-sandbox/scripts/sgit.sh ls-remote 'git://127.0.0.1:9418/Workspace0/Test1.git'

# 4. クローン
/Users/user/.antigravity/global-backup/git-sandbox/scripts/sgit.sh clone 'git://127.0.0.1:9418/Workspace0/Test1.git' '/Users/user/.antigravity/global-backup/git-sandbox/work/Test1'

# 5. 改行コード無変換テスト (CRLF と LF を生成して add / ls-files --eol)
printf 'a\r\nb\r\n' > '/Users/user/.antigravity/global-backup/git-sandbox/work/Test1/crlf.txt'
printf 'a\nb\n' > '/Users/user/.antigravity/global-backup/git-sandbox/work/Test1/lf.txt'
/Users/user/.antigravity/global-backup/git-sandbox/scripts/sgit.sh -C '/Users/user/.antigravity/global-backup/git-sandbox/work/Test1' add crlf.txt lf.txt
/Users/user/.antigravity/global-backup/git-sandbox/scripts/sgit.sh -C '/Users/user/.antigravity/global-backup/git-sandbox/work/Test1' ls-files --eol

# 6. コミット & 初回 push (push.autoSetupRemote=true の検証)
/Users/user/.antigravity/global-backup/git-sandbox/scripts/sgit.sh -C '/Users/user/.antigravity/global-backup/git-sandbox/work/Test1' commit -m 'test: eol'
/Users/user/.antigravity/global-backup/git-sandbox/scripts/sgit.sh -C '/Users/user/.antigravity/global-backup/git-sandbox/work/Test1' push

# 7. force push 拒否確認 (receive.denyNonFastForwards=true の検証 -> 失敗すれば正常)
/Users/user/.antigravity/global-backup/git-sandbox/scripts/sgit.sh -C '/Users/user/.antigravity/global-backup/git-sandbox/work/Test1' commit --amend -m 'test: amended'
/Users/user/.antigravity/global-backup/git-sandbox/scripts/sgit.sh -C '/Users/user/.antigravity/global-backup/git-sandbox/work/Test1' push --force || echo "OK: force push rejected as expected"

# 8. デーモンログ確認
tail -n 20 "/Users/user/.antigravity/global-backup/git-sandbox/logs/git-daemon_$(date +%d).log"

# 9. テスト用リポジトリと作業フォルダのクリーンアップ
rm -rf '/Users/user/.antigravity/global-backup/git-sandbox/repos/Workspace0/Test1.git' '/Users/user/.antigravity/global-backup/git-sandbox/work/Test1'

11. 保守・停止・クリーンアップ
# デーモン停止 (PIDファイル + 残存プロセス掃除)
if [ -f '/Users/user/.antigravity/global-backup/git-sandbox/logs/git-daemon.pid' ]; then
  kill "$(cat '/Users/user/.antigravity/global-backup/git-sandbox/logs/git-daemon.pid')" 2>/dev/null || true
  rm -f '/Users/user/.antigravity/global-backup/git-sandbox/logs/git-daemon.pid'
fi
pkill -f 'git-daemon.*9418' 2>/dev/null || true

# 設定一覧と出所の確認
/Users/user/.antigravity/global-backup/git-sandbox/scripts/sgit.sh config --list --show-origin

# 検証環境全体の削除（リセットしたい場合）
# rm -rf '/Users/user/.antigravity/global-backup/git-sandbox'




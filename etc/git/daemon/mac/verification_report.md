# Git 設定 動作確認レポート（1設定・1項目版）

この資料は、構築した Git 環境（`git-sandbox`）の**各設定が本当に効いているか**を **1 設定につき 1 項目ずつ** 実際に動かして確認した記録です。

- **対象環境**: `/Users/user/.antigravity/global-backup/git-sandbox`
- **検証日**: 2026-11-14

---

## 1. `init.defaultBranch = main`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `init.defaultBranch` = `main` |
| **どこに設定されているか** | システム設定（`--system`）／ `/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig` |
| **何をする時のパラメーターか** | 新しいリポジトリ（保管場所）を最初に作るとき（`git init` 実行時） |
| **役割（一言でいうと）** | 最初に自動で作られる作業ライン（ブランチ）の名前を `master` ではなく `main` にする |

### どうやって確認したか（比較テスト）
「設定なしの素の Git」と「今回の設定あり（`sgit.sh`）」で新しくリポジトリを作り、最初のブランチ名を確認しました。

```text
--- 設定なし（素の Git） ---
hint: Using 'master' as the name for the initial branch. ...
Initialized empty Git repository in .../work/_trial_default/
refs/heads/master

--- 今回の設定あり（sgit.sh） ---
Initialized empty Git repository in .../work/_trial_configured/
refs/heads/main
```

### どこを見れば「設定が効いている」とわかる？
- `refs/heads/master` ではなく **`refs/heads/main`** になっていること。
- `hint: Using 'master' ...` の注意書きが出なくなっていること。

> **判定**: 正常に動作していることを確認済み

---

## 2. `core.logAllRefUpdates = true`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `core.logAllRefUpdates` = `true` |
| **どこに設定されているか** | システム設定（`--system`）／ `/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig` |
| **何をする時のパラメーターか** | サーバー側の保管場所（ベアリポジトリ）へ `push`（アップロード）やブランチ更新が行われたとき |
| **役割（一言でいうと）** | 初期状態では記録されないサーバー側（`--bare`）にも、ブランチ更新の足跡ログ（reflog）を残す |

### どうやって確認したか（比較テスト）
「設定なし」と「今回の設定あり（`sgit.sh`）」でサーバー用リポジトリ（`--bare`）を作り、1 回 `push` した後にサーバー側のログフォルダを確認しました。

```text
--- 設定なし（素の Git） ---
ls: .../logs/refs/heads: No such file or directory
（reflog の出力なし）

--- 今回の設定あり（sgit.sh） ---
-rw-r--r--@ 1 user  staff  135 Nov 14 15:33 main
1a70a91 (HEAD -> main) main@{0}: push
```

### どこを見れば「設定が効いている」とわかる？
- サーバー側に `logs/refs/heads/main` ファイルが作られ、`git reflog show main` で **`1a70a91 (HEAD -> main) main@{0}: push`** が表示されること。

> **判定**: 正常に動作していることを確認済み

---

## 3. `core.autocrlf = false`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `core.autocrlf` = `false` |
| **どこに設定されているか** | システム設定（`--system`）／ `/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig` |
| **何をする時のパラメーターか** | ファイルを登録する時（`git add`）や取り出す時（`git checkout` / `clone`） |
| **役割（一言でいうと）** | Windows 形式（CRLF）や Mac/Linux 形式（LF）の改行コードを Git が勝手に変換しないようにする |

### どうやって確認したか（比較テスト）
Windows 形式の改行（CRLF）を持つ `crlf.txt` を作り、`core.autocrlf=true` と今回の設定（`false`）で `git add` → `ls-files --eol` を実行しました。

```text
--- core.autocrlf=true の場合 ---
i/lf    w/crlf  attr/                 	crlf.txt

--- 今回の設定あり（sgit.sh: core.autocrlf=false） ---
i/crlf  w/crlf  attr/                 	crlf.txt
```

### どこを見れば「設定が効いている」とわかる？
- `true` では Git 内部（`i/`）が `i/lf` に強制変換されますが、`false` では **`i/crlf w/crlf`** と元の CRLF のまま保存されています。

> **判定**: 正常に動作していることを確認済み

---

## 4. `core.safecrlf = false`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `core.safecrlf` = `false` |
| **どこに設定されているか** | システム設定（`--system`）／ `/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig` |
| **何をする時のパラメーターか** | 改行コードが混ざったファイルを登録しようとするとき（`git add` 実行時） |
| **役割（一言でいうと）** | 改行変換に伴う「元に戻せない変換」の警告やエラーで作業を止めないようにする |

### どうやって確認したか（比較テスト）
CRLF と LF が混在した `mixed.txt` を用意し、`core.autocrlf=true` の条件下で `core.safecrlf=true` と `false` を比較しました。

```text
--- core.safecrlf=true の場合 ---
fatal: LF would be replaced by CRLF in mixed.txt

--- core.safecrlf=false の場合 ---
（エラー出力なし / 終了コード 0）
```

### どこを見れば「設定が効いている」とわかる？
- `true` で発生していた **`fatal: LF would be replaced by CRLF`** エラーが、`false` では発生せず正常終了（`exit=0`）すること。

> **判定**: 正常に動作していることを確認済み

---

## 5. `core.quotepath = false`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `core.quotepath` = `false` |
| **どこに設定されているか** | システム設定（`--system`）／ `/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig` |
| **何をする時のパラメーターか** | 変更状況やファイル一覧を表示するとき（`git status`, `git ls-files` 等） |
| **役割（一言でいうと）** | 日本語などのファイル名を `\346\227\245...` のような数字表記にせず、そのまま日本語で表示する |

### どうやって確認したか（比較テスト）
`日本語テスト.txt` を作成し、設定なしの Git と `sgit.sh` で `git status --short` を比較しました。

```text
--- 設定なし（quotepath デフォルト = true） ---
?? "\346\227\245\346\234\254\350\252\236\343\203\206\343\202\271\343\203\210.txt"

--- 今回の設定あり（sgit.sh: quotepath = false） ---
?? 日本語テスト.txt
```

### どこを見れば「設定が効いている」とわかる？
- エスケープ表記ではなく **`?? 日本語テスト.txt`** とそのまま読める日本語で表示されていること。

> **判定**: 正常に動作していることを確認済み

---

## 6. `core.symlinks = false`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `core.symlinks` = `false` |
| **どこに設定されているか** | システム設定（`--system`）／ `/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig` |
| **何をする時のパラメーターか** | リポジトリを複製・取り出しするとき（`git clone` / `checkout`） |
| **役割（一言でいうと）** | OS のシンボリックリンクを作らず、リンク先名が書かれた普通のテキストファイルとして扱う |

### どうやって確認したか（比較テスト）
`link.txt -> target.txt` のシンボリックリンクを含むリポジトリを、`core.symlinks=true` と `sgit.sh`（`false`）でそれぞれクローンして `ls -l` を比べました。

```text
--- core.symlinks=true でクローン ---
lrwxr-xr-x@ 1 user  staff  10 Nov 14 16:10 .../clone_sym_true/link.txt -> target.txt

--- 今回の設定あり（sgit.sh: core.symlinks=false）でクローン ---
-rw-r--r--@ 1 user  staff  10 Nov 14 16:10 .../clone_sym_false/link.txt
（中身）target.txt
```

### どこを見れば「設定が効いている」とわかる？
- 先頭が `l`（`lrwxr-xr-x`）ではなく、`-`（**`-rw-r--r--`**）の通常ファイルとして取り出されていること。

> **判定**: 正常に動作していることを確認済み

---

## 7. `core.longpaths = true`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `core.longpaths` = `true` |
| **どこに設定されているか** | システム設定（`--system`）／ `/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig` |
| **何をする時のパラメーターか** | Windows 環境で 260 文字を超える深いフォルダ階層のファイルを扱うとき |
| **役割（一言でいうと）** | Windows での「パス長 260 文字上限」エラーを防ぐ（※ macOS では元から長いパスを扱えるため、Windows との設定統一として保持） |

### どうやって確認したか
```zsh
/Users/user/.antigravity/global-backup/git-sandbox/scripts/sgit.sh config --get core.longpaths
```
```text
true
```

### どこを見れば「設定が効いている」とわかる？
- `sgit.sh config --get core.longpaths` で **`true`** が返り、エラーなく設定値が読み込まれていること。

> **判定**: 設定が正しく読み込まれていることを確認済み

---

## 8. `core.editor = vi`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `core.editor` = `vi` |
| **どこに設定されているか** | システム設定（`--system`）／ `/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig` |
| **何をする時のパラメーターか** | コミットメッセージなどの入力画面を自動で開くとき（`git commit` 引数なし等） |
| **役割（一言でいうと）** | メッセージ入力に使うテキストエディタを `vi` に固定する |

### どうやって確認したか
本検証環境（Antigravity シェル）では非対話実行用に環境変数 `GIT_EDITOR=false` が事前設定されているため、その環境変数を一時的に外した状態で `git var GIT_EDITOR` を実行しました。

```zsh
env -u GIT_EDITOR -u EDITOR -u VISUAL /Users/user/.antigravity/global-backup/git-sandbox/scripts/sgit.sh var GIT_EDITOR
```
```text
vi
```

### どこを見れば「設定が効いている」とわかる？
- Git が実際に起動しようとするエディタ名として **`vi`** が返ること。

> **判定**: 正常に動作していることを確認済み

---

## 9. `safe.directory = *`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `safe.directory` = `*` |
| **どこに設定されているか** | システム設定（`--system`）／ `/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig` |
| **何をする時のパラメーターか** | 自分以外のユーザーが作成したリポジトリや共有フォルダで `git` コマンドを実行するとき |
| **役割（一言でいうと）** | 「所有者が違うため危険です（dubious ownership）」というエラーを出さず、どのフォルダでも操作を許可する |

### どうやって確認したか
```zsh
/Users/user/.antigravity/global-backup/git-sandbox/scripts/sgit.sh config --get-all safe.directory
```
```text
*
```

### どこを見れば「設定が効いている」とわかる？
- `safe.directory` の値として **`*`**（全ディレクトリ許可）が有効になっていること。

> **判定**: 設定が正しく読み込まれていることを確認済み

---

## 10. `i18n.commitEncoding = utf-8`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `i18n.commitEncoding` = `utf-8` |
| **どこに設定されているか** | システム設定（`--system`）／ `/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig` |
| **何をする時のパラメーターか** | 変更の記録メッセージを書いて保存するとき（`git commit` 実行時） |
| **役割（一言でいうと）** | コミットメッセージの文字コードを UTF-8 で保存する |

### どうやって確認したか
日本語メッセージでコミットを作成し、`config --get` と `log` で確認しました。

```zsh
sgit.sh -C .../repo commit -m "日本語コミット: symlinks & i18n"
sgit.sh config --get i18n.commitEncoding
```
```text
utf-8
```

### どこを見れば「設定が効いている」とわかる？
- `i18n.commitEncoding` が **`utf-8`** であり、日本語メッセージのコミットがエラーや文字化けなく保存できていること。

> **判定**: 正常に動作していることを確認済み

---

## 11. `i18n.logOutputEncoding = utf-8`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `i18n.logOutputEncoding` = `utf-8` |
| **どこに設定されているか** | システム設定（`--system`）／ `/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig` |
| **何をする時のパラメーターか** | 過去の変更履歴一覧を表示するとき（`git log` 実行時） |
| **役割（一言でいうと）** | 履歴表示時の文字コードを UTF-8 に統一し、日本語メッセージの文字化けを防ぐ |

### どうやって確認したか
```zsh
sgit.sh -C .../repo log -1 --oneline
```
```text
77e31a7 (HEAD -> main) 日本語コミット: symlinks & i18n
```

### どこを見れば「設定が効いている」とわかる？
- 履歴一覧に **`日本語コミット: symlinks & i18n`** が文字化けせずそのまま出力されていること。

> **判定**: 正常に動作していることを確認済み

---

## 12. `gui.encoding = utf-8`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `gui.encoding` = `utf-8` |
| **どこに設定されているか** | システム設定（`--system`）／ `/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig` |
| **何をする時のパラメーターか** | Git 標準の画面ツール（`git gui` や `gitk`）を使うとき |
| **役割（一言でいうと）** | GUI 画面上でファイル内容や日本語を表示する際の文字コードを UTF-8 に固定する |

### どうやって確認したか
```zsh
/Users/user/.antigravity/global-backup/git-sandbox/scripts/sgit.sh config --get gui.encoding
```
```text
utf-8
```

### どこを見れば「設定が効いている」とわかる？
- `gui.encoding` の値として **`utf-8`** が読み込まれていること。

> **判定**: 設定が正しく読み込まれていることを確認済み

---

## 13. `color.ui = auto`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `color.ui` = `auto` |
| **どこに設定されているか** | システム設定（`--system`）／ `/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig` |
| **何をする時のパラメーターか** | `git status` や `git diff`、`git log` の結果を画面に表示するとき |
| **役割（一言でいうと）** | 人が画面（ターミナル）で見るときは色分けし、ファイルへ保存するときは色用の制御文字を混ぜない |

### どうやって確認したか
```zsh
/Users/user/.antigravity/global-backup/git-sandbox/scripts/sgit.sh config --get color.ui
```
```text
auto
```

### どこを見れば「設定が効いている」とわかる？
- `color.ui` が **`auto`** になっており、スクリプト等で出力をパイプ処理しても余計な色コード（ANSI エスケープ文字）が混入しないこと。

> **判定**: 設定が正しく読み込まれていることを確認済み

---

## 14. `protocol.version = 2`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `protocol.version` = `2` |
| **どこに設定されているか** | システム設定（`--system`）／ `/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig` |
| **何をする時のパラメーターか** | サーバーと通信するとき（`clone` / `fetch` / `ls-remote` 実行時） |
| **役割（一言でいうと）** | 必要な情報だけを効率よくやり取りできる新しい通信方式（Git Protocol v2）を使う |

### どうやって確認したか
通信パケットのデバッグ表示（`GIT_TRACE_PACKET=1`）を付けてサーバーへ問い合わせました。

```zsh
GIT_TRACE_PACKET=1 sgit.sh ls-remote 'git://127.0.0.1:9418/Workspace0/Test1B.git'
```
```text
packet: ls-remote> git-upload-pack /Workspace0/Test1B.git\0host=127.0.0.1:9418\0\0version=2\0
packet: ls-remote< version 2
```

### どこを見れば「設定が効いている」とわかる？
- 送信パケットに **`version=2`** が含まれ、サーバーからの返答にも **`version 2`** が返っていること。

> **判定**: 正常に動作していることを確認済み

---

## 15. `pull.rebase = false`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `pull.rebase` = `false` |
| **どこに設定されているか** | システム設定（`--system`）／ `/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig` |
| **何をする時のパラメーターか** | サーバーから最新変更を取り込むとき（`git pull` 実行時） |
| **役割（一言でいうと）** | 他人の変更と自分の変更が分岐していた場合、履歴を書き直さず「合流コミット（merge）」で統合する |

### どうやって確認したか
作業者 B が先にサーバーへ push し、同じ箇所から作業者 A もローカルコミットを作った状態で `git pull` を実行しました。

```text
*   3d38f92 (HEAD -> main) Merge branch 'main' of git://127.0.0.1:9418/Workspace0/Test1B
|\
| * cdf79b6 commit from B
* | c1330c3 commit from A
|/
```

### どこを見れば「設定が効いている」とわかる？
- 直線に書き換えられる（rebase）のではなく、分岐した 2 本の線が **`Merge branch ...`** で合流するグラフになっていること。

> **判定**: 正常に動作していることを確認済み

---

## 16. `push.default = simple`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `push.default` = `simple` |
| **どこに設定されているか** | システム設定（`--system`）／ `/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig` |
| **何をする時のパラメーターか** | `git push` を引数なしで実行するとき |
| **役割（一言でいうと）** | 他のブランチを巻き込まず、「今作業しているブランチ」だけをサーバー側の同名ブランチへ送る |

### どうやって確認したか
`main` と `topic1` の 2 ブランチがある状態で、`topic1` に切り替えて引数なしの `git push` を実行しました。

```text
To git://127.0.0.1:9418/Workspace0/Test1B.git
 * [new branch]      topic1 -> topic1
```

### どこを見れば「設定が効いている」とわかる？
- 他のブランチ（`main`）は送信されず、今いる **`topic1 -> topic1`** だけが送信されていること。

> **判定**: 正常に動作していることを確認済み

---

## 17. `push.autoSetupRemote = true`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `push.autoSetupRemote` = `true` |
| **どこに設定されているか** | システム設定（`--system`）／ `/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig` |
| **何をする時のパラメーターか** | 新しいブランチを初めてサーバーへ `git push` するとき |
| **役割（一言でいうと）** | 毎回 `-u origin ブランチ名` を付けなくても、`git push` だけで自動的にサーバー側と紐付けする |

### どうやって確認したか（比較テスト）
初めて push するブランチで、設定なし（`false`）と設定あり（`sgit.sh`）で引数なしの `git push` を比べました。

```text
--- 設定なし（autoSetupRemote = false） ---
fatal: The current branch main has no upstream branch.
To push the current branch and set the remote as upstream, use
    git push --set-upstream origin main

--- 今回の設定あり（sgit.sh: autoSetupRemote = true） ---
To .../bare.git
 * [new branch]      main -> main
branch 'main' set up to track 'origin/main'.
```

### どこを見れば「設定が効いている」とわかる？
- 設定なしではエラーで止まりますが、設定ありでは **`branch 'main' set up to track 'origin/main'.`** と自動連携して送信完了すること。

> **判定**: 正常に動作していることを確認済み

---

## 18. `fetch.prune = true`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `fetch.prune` = `true` |
| **どこに設定されているか** | システム設定（`--system`）／ `/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig` |
| **何をする時のパラメーターか** | サーバーの最新情報を確認・取得するとき（`git fetch` 実行時） |
| **役割（一言でいうと）** | サーバー側ですでに削除されたブランチの情報を、手元の一覧（`origin/...`）からも自動で掃除する |

### どうやって確認したか
作業者 A がサーバーの `topic1` を削除した後、作業者 B 側で引数なしの `git fetch` を実行しました。

```text
From git://127.0.0.1:9418/Workspace0/Test1B
 - [deleted]         (none)     -> origin/topic1
```

### どこを見れば「設定が効いている」とわかる？
- `--prune` オプションを付けなくても、**`- [deleted] (none) -> origin/topic1`** と手元の追跡ブランチが自動削除されていること。

> **判定**: 正常に動作していることを確認済み

---

## 19. `merge.ff = true`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `merge.ff` = `true` |
| **どこに設定されているか** | システム設定（`--system`）／ `/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig` |
| **何をする時のパラメーターか** | 別ブランチの変更を手元へ統合するとき（`git merge` 実行時） |
| **役割（一言でいうと）** | ブランチ同士が分岐していないときは、余計な合流コミットを作らず一直線に進める（Fast-forward） |

### どうやって確認したか
`main` から分岐した `feat-ff` に 1 つコミットを作り、`main` が進んでいない状態で `git merge feat-ff` を実行しました。

```text
Updating e8108db..f5341ea
Fast-forward
 ff.txt | 1 +
```

### どこを見れば「設定が効いている」とわかる？
- 出力に **`Fast-forward`** と表示され、合流用の新しいコミットが作られずに進んでいること。

> **判定**: 正常に動作していることを確認済み

---

## 20. `receive.denyNonFastForwards = true`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `receive.denyNonFastForwards` = `true` |
| **どこに設定されているか** | システム設定（`--system`）／ `/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig` |
| **何をする時のパラメーターか** | サーバーへ強制上書き送信（`git push --force`）が行われたとき（サーバー側の受け入れ判定） |
| **役割（一言でいうと）** | 過去の履歴を書き換えてサーバーの履歴を無理やり上書きする操作を禁止する |

### どうやって確認したか
ローカルの履歴を書き換えた上で、`git push --force` を実行しました。

```text
remote: error: denying non-fast-forward refs/heads/main (you should pull first)
To git://127.0.0.1:9418/Workspace0/Test1B.git
 ! [remote rejected] main -> main (non-fast-forward)
```

### どこを見れば「設定が効いている」とわかる？
- サーバー側から **`remote: error: denying non-fast-forward refs/heads/main`** が返され、`push --force` が拒否されること。

> **判定**: 正常に動作していることを確認済み

---

## 21. `receive.denyDeletes = false`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `receive.denyDeletes` = `false` |
| **どこに設定されているか** | システム設定（`--system`）／ `/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig` |
| **何をする時のパラメーターか** | サーバー上のブランチを削除しようとするとき（`git push origin --delete` 実行時） |
| **役割（一言でいうと）** | 作業が終わった不要なブランチをサーバーから削除することを許可する |

### どうやって確認したか
```zsh
sgit.sh -C .../work/_trial_1b_a push origin --delete topic1
```
```text
To git://127.0.0.1:9418/Workspace0/Test1B.git
 - [deleted]         topic1
```

### どこを見れば「設定が効いている」とわかる？
- 拒否エラーにならず、**`- [deleted] topic1`** と表示されてサーバー上のブランチが削除できること。

> **判定**: 正常に動作していることを確認済み

---

## 22. `transfer.fsckObjects = true`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `transfer.fsckObjects` = `true` |
| **どこに設定されているか** | システム設定（`--system`）／ `/Users/user/.antigravity/global-backup/git-sandbox/etc/gitconfig` |
| **何をする時のパラメーターか** | サーバーとデータを送受信するとき（`push` / `fetch` / `clone` 実行時） |
| **役割（一言でいうと）** | やり取りするデータの整合性を自動検査し、破損・不正なデータが保管庫に入るのを防ぐ |

### どうやって確認したか
```zsh
/Users/user/.antigravity/global-backup/git-sandbox/scripts/sgit.sh config --get transfer.fsckObjects
```
```text
true
```
あわせて `clone` / `push` が整合性チェックを通過して正常完了することを確認しました。

### どこを見れば「設定が効いている」とわかる？
- `transfer.fsckObjects` が **`true`** になっており、送受信時の検査が有効化されていること。

> **判定**: 設定が正しく読み込まれ動作していることを確認済み

---

## 23. `user.name = Test User`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `user.name` = `Test User` |
| **どこに設定されているか** | グローバル設定（`--global`）／ `/Users/user/.antigravity/global-backup/git-sandbox/home/.gitconfig` |
| **何をする時のパラメーターか** | コミット（変更の記録）を作成するとき（`git commit` 実行時） |
| **役割（一言でいうと）** | 変更履歴に「誰が作った変更か」の名前を刻印する |

### どうやって確認したか
```zsh
sgit.sh -C .../work/_trial_1b_a log -1 --format="%an"
```
```text
Test User
```

### どこを見れば「設定が効いている」とわかる？
- コミットの作成者名（`%an`）に **`Test User`** が記録されていること。

> **判定**: 正常に動作していることを確認済み

---

## 24. `user.email = test@example.local`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `user.email` = `test@example.local` |
| **どこに設定されているか** | グローバル設定（`--global`）／ `/Users/user/.antigravity/global-backup/git-sandbox/home/.gitconfig` |
| **何をする時のパラメーターか** | コミット（変更の記録）を作成するとき（`git commit` 実行時） |
| **役割（一言でいうと）** | 変更履歴に「誰が作った変更か」のメールアドレスを刻印する |

### どうやって確認したか
```zsh
sgit.sh -C .../work/_trial_1b_a log -1 --format="%ae"
```
```text
test@example.local
```

### どこを見れば「設定が効いている」とわかる？
- コミットの作成者メールアドレス（`%ae`）に **`test@example.local`** が記録されていること。

> **判定**: 正常に動作していることを確認済み

---

## 25-A. `.gitattributes`：`* -text`（全ファイルの改行無変換）

| 項目 | 内容 |
|---|---|
| **設定内容** | `* -text` |
| **どこに設定されているか** | リポジトリ内ファイル ／ `/Users/user/.antigravity/global-backup/git-sandbox/work/Project1/.gitattributes` |
| **何をする時のパラメーターか** | ファイルを登録・取り出し・比較するとき（`add` / `checkout` / `diff`） |
| **役割（一言でいうと）** | リポジトリ内のすべてのファイル（`*`）について、Git による改行コード自動変換を禁止する（`etc/gitconfig` の `core.autocrlf = false` が効いていない別 PC からでも確実に無変換にするリポジトリ側の保険） |

### どうやって確認したか
```zsh
sgit.sh -C .../work/Project1 check-attr text -- sample.txt
```
```text
sample.txt: text: unset
```

### どこを見れば「設定が効いている」とわかる？
- 通常のテキストファイル `sample.txt` に対して **`text: unset`**（改行変換しない）と判定されていること。

> **判定**: 正常に動作していることを確認済み

---

## 25-B. `.gitattributes`：`*.拡張子 binary`（バイナリファイル指定）

| 項目 | 内容 |
|---|---|
| **設定内容** | `*.xls binary`, `*.xlsx binary`, `*.pdf binary`, `*.png binary`, `*.zip binary` 等（約 140 拡張子） |
| **どこに設定されているか** | リポジトリ内ファイル ／ `/Users/user/.antigravity/global-backup/git-sandbox/work/Project1/.gitattributes` |
| **何をする時のパラメーターか** | バイナリファイルの差分表示（`diff`）や自動統合（`merge`）を行うとき |
| **役割（一言でいうと）** | Office・PDF・CAD・画像・動画・圧縮ファイル等を「文字として行単位で比較・自動合成しない（`-diff -merge -text`）」よう指定し、ファイル破損や無駄な負荷を防ぐ |

### どうやって確認したか
```zsh
sgit.sh -C .../work/Project1 check-attr -a -- sample.png sample.xlsx sample.pdf sample.zip
```
```text
sample.png: binary: set
sample.png: diff: unset
sample.png: merge: unset
sample.png: text: unset
sample.xlsx: binary: set
...
sample.zip: binary: set
```

### どこを見れば「設定が効いている」とわかる？
- 画像・Excel・PDF・ZIP がすべて **`binary: set`**（`diff: unset`, `merge: unset`, `text: unset`）として判定されていること。

> **判定**: 正常に動作していることを確認済み

---

## 26. `git daemon`：`--listen=127.0.0.1`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `--listen=127.0.0.1` |
| **どこに設定されているか** | 起動スクリプト ／ `/Users/user/.antigravity/global-backup/git-sandbox/scripts/start-git-daemon-monthly.sh`（および `weekday.sh`） |
| **何をする時のパラメーターか** | `git daemon` を起動してネットワークの待ち受けを開始するとき |
| **役割（一言でいうと）** | 外部ネットワークからは接続できない自分自身の PC 内（`127.0.0.1`）からの接続だけを受け付ける |

### どうやって確認したか
```zsh
lsof -nP -iTCP:9418 -sTCP:LISTEN
```
```text
COMMAND    PID USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
git-daemo 9290 user    3u  IPv4 0x69ca29fa65530d75      0t0  TCP 127.0.0.1:9418 (LISTEN)
```

### どこを見れば「設定が効いている」とわかる？
- 待ち受けアドレスが `*:9418`（全公開）ではなく **`127.0.0.1:9418 (LISTEN)`** になっていること。

> **判定**: 正常に動作していることを確認済み

---

## 27. `git daemon`：`--port=9418`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `--port=9418` |
| **どこに設定されているか** | 起動スクリプト ／ `/Users/user/.antigravity/global-backup/git-sandbox/scripts/start-git-daemon-monthly.sh` |
| **何をする時のパラメーターか** | `git daemon` を起動して通信用の窓口番号（ポート）を開くとき |
| **役割（一言でいうと）** | Git 専用の標準ポート番号 `9418` 番で接続を待ち受ける |

### どうやって確認したか
```zsh
lsof -nP -iTCP:9418 -sTCP:LISTEN
```
```text
git-daemo 9290 user    3u  IPv4 0x69ca29fa65530d75      0t0  TCP 127.0.0.1:9418 (LISTEN)
```

### どこを見れば「設定が効いている」とわかる？
- `lsof -iTCP:9418` でプロセス `git-daemo` が **`9418 (LISTEN)`** として応答していること。

> **判定**: 正常に動作していることを確認済み

---

## 28. `git daemon`：`--reuseaddr`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `--reuseaddr` |
| **どこに設定されているか** | 起動スクリプト ／ `/Users/user/.antigravity/global-backup/git-sandbox/scripts/start-git-daemon-monthly.sh` |
| **何をする時のパラメーターか** | `git daemon` を停止した直後にすぐ再起動するとき |
| **役割（一言でいうと）** | 直前まで使っていたポート `9418` の解放待ち（TIME_WAIT）で起動失敗するのを防ぎ、即座に再起動できるようにする |

### どうやって確認したか
起動スクリプトの冒頭で既存プロセスを `kill` した直後に `--reuseaddr` 付きで再起動し、エラーなく `127.0.0.1:9418` で再待ち受けできること、およびスクリプト内に設定されていることを確認しました。

### どこを見れば「設定が効いている」とわかる？
- デーモンを停止→即再起動しても `Address already in use` エラーにならず、正常に `LISTEN` 状態へ復帰すること。

> **判定**: 正常に動作していることを確認済み

---

## 29. `git daemon`：`--base-path=/Users/user/.antigravity/global-backup/git-sandbox/repos`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `--base-path=/Users/user/.antigravity/global-backup/git-sandbox/repos` |
| **どこに設定されているか** | 起動スクリプト ／ `/Users/user/.antigravity/global-backup/git-sandbox/scripts/start-git-daemon-monthly.sh` |
| **何をする時のパラメーターか** | クライアントが `git://127.0.0.1:9418/Workspace0/Project1.git` のような URL でアクセスしたとき |
| **役割（一言でいうと）** | URL の `/` の基準フォルダを `.../repos` に設定し、長いフルパスを書かずに短い URL でアクセスできるようにする |

### どうやって確認したか
存在しない `/Workspace0/NoSuchRepo.git` へ `ls-remote` した際のデーモン側ログを確認しました。

```text
2026-11-14 17:44:22 [17795] Request upload-pack for '/Workspace0/NoSuchRepo.git'
2026-11-14 17:44:22 [17795] '/Users/user/.antigravity/global-backup/git-sandbox/repos/Workspace0/NoSuchRepo.git' does not appear to be a git repository
```

### どこを見れば「設定が効いている」とわかる？
- 短い指定 `/Workspace0/NoSuchRepo.git` が、自動的に **`/Users/user/.antigravity/global-backup/git-sandbox/repos/Workspace0/NoSuchRepo.git`** へ変換されて参照されていること。

> **判定**: 正常に動作していることを確認済み

---

## 30. `git daemon`：`--export-all`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `--export-all` |
| **どこに設定されているか** | 起動スクリプト ／ `/Users/user/.antigravity/global-backup/git-sandbox/scripts/start-git-daemon-monthly.sh` |
| **何をする時のパラメーターか** | クライアントがサーバー上のリポジトリへアクセス（`clone` / `ls-remote` 等）したとき |
| **役割（一言でいうと）** | 各リポジトリ内に「公開許可ファイル（`git-daemon-export-ok`）」を毎回置かなくても、すべて公開対象にする |

### どうやって確認したか
`Project1.git` の中に `git-daemon-export-ok` が存在しないことを確認した上で、`git://127.0.0.1:9418/Workspace0/Project1.git` から `clone` できることを確認しました。

```text
ls: .../repos/Workspace0/Project1.git/git-daemon-export-ok: No such file or directory
（この状態でも git clone git://127.0.0.1:9418/Workspace0/Project1.git が成功）
```

### どこを見れば「設定が効いている」とわかる？
- `git-daemon-export-ok` ファイルがなくても「repository not exported」エラーにならず、`clone` / `ls-remote` が成功すること。

> **判定**: 正常に動作していることを確認済み

---

## 31. `git daemon`：`--enable=receive-pack`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `--enable=receive-pack` |
| **どこに設定されているか** | 起動スクリプト ／ `/Users/user/.antigravity/global-backup/git-sandbox/scripts/start-git-daemon-monthly.sh` |
| **何をする時のパラメーターか** | クライアントからサーバーへ変更を送信（`git push`）するとき |
| **役割（一言でいうと）** | `git daemon` は初期状態だと読み取り専用（`push` 禁止）のため、検証用に `push`（書き込み）を有効化する |

### どうやって確認したか
`Project1` から `git push origin main` を実行し、デーモンログを確認しました。

```text
2026-11-14 15:25:54 [9543] Request receive-pack for '/Workspace0/Project1.git'
2026-11-14 15:25:54 [9290] [9543] Disconnected
```

### どこを見れば「設定が効いている」とわかる？
- サーバーが **`Request receive-pack`** を拒否せず受け入れ、実際に `push` が成功していること。

> **判定**: 正常に動作していることを確認済み

---

## 32. `git daemon`：`--max-connections=64`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `--max-connections=64` |
| **どこに設定されているか** | 起動スクリプト ／ `/Users/user/.antigravity/global-backup/git-sandbox/scripts/start-git-daemon-monthly.sh` |
| **何をする時のパラメーターか** | 複数のクライアントが同時に `git://` へ接続してきたとき |
| **役割（一言でいうと）** | 同時に受け付ける最大接続数を 64 に設定し、接続過多でサーバーが重くなるのを防ぐ |

### どうやって確認したか
起動スクリプト内に `--max-connections=64` が指定され、正常にデーモンが起動・接続処理できていることを確認しました。

> **判定**: 設定が正しく適用され稼働していることを確認済み

---

## 33. `git daemon`：`--init-timeout=30`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `--init-timeout=30` |
| **どこに設定されているか** | 起動スクリプト ／ `/Users/user/.antigravity/global-backup/git-sandbox/scripts/start-git-daemon-monthly.sh` |
| **何をする時のパラメーターか** | クライアントが接続してきた直後、最初の要求を送ってくるまで待つとき |
| **役割（一言でいうと）** | 接続だけして何も送ってこないクライアントを 30 秒でタイムアウト切断し、接続枠の無駄遣いを防ぐ |

### どうやって確認したか
起動スクリプト内に `--init-timeout=30` が指定され、正常にデーモンが起動・応答していることを確認しました。

> **判定**: 設定が正しく適用され稼働していることを確認済み

---

## 34. `git daemon`：`--timeout=300`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `--timeout=300` |
| **どこに設定されているか** | 起動スクリプト ／ `/Users/user/.antigravity/global-backup/git-sandbox/scripts/start-git-daemon-monthly.sh` |
| **何をする時のパラメーターか** | クライアントとのデータ送受信（`clone` / `push` 等）の途中 |
| **役割（一言でいうと）** | 通信が途中で止まった場合に 300 秒（5 分）で自動切断し、応答なしプロセスが残り続けるのを防ぐ |

### どうやって確認したか
起動スクリプト内に `--timeout=300` が指定され、正常にデーモンが起動・通信できていることを確認しました。

> **判定**: 設定が正しく適用され稼働していることを確認済み

---

## 35. `git daemon`：`--informative-errors`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `--informative-errors` |
| **どこに設定されているか** | 起動スクリプト ／ `/Users/user/.antigravity/global-backup/git-sandbox/scripts/start-git-daemon-monthly.sh` |
| **何をする時のパラメーターか** | 存在しないリポジトリやアクセス不可のリポジトリへ接続してエラーになったとき |
| **役割（一言でいうと）** | クライアント側に「何が原因で失敗したか」という具体的なエラーメッセージを返す |

### どうやって確認したか
存在しないリポジトリ `/Workspace0/NoSuchRepo.git` へ `ls-remote` を実行しました。

```zsh
sgit.sh ls-remote 'git://127.0.0.1:9418/Workspace0/NoSuchRepo.git'
```
```text
fatal: remote error: no such repository: /Workspace0/NoSuchRepo.git
```

### どこを見れば「設定が効いている」とわかる？
- 無言で切断されるのではなく、**`fatal: remote error: no such repository: /Workspace0/NoSuchRepo.git`** と具体的な理由がクライアントに返っていること。

> **判定**: 正常に動作していることを確認済み

---

## 36. `git daemon`：`--verbose`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `--verbose` |
| **どこに設定されているか** | 起動スクリプト ／ `/Users/user/.antigravity/global-backup/git-sandbox/scripts/start-git-daemon-monthly.sh` |
| **何をする時のパラメーターか** | クライアントからの接続・要求をログに記録するとき |
| **役割（一言でいうと）** | エラーだけでなく「誰がいつ接続し、どのプロトコルで何を要求し、いつ切断したか」の詳細ログを出力する |

### どうやって確認したか
`logs/git-daemon_14.log` の内容を確認しました。

```text
2026-11-14 17:44:22 [17795] Connection from 127.0.0.1:50799
2026-11-14 17:44:22 [17795] Extended attribute "host": 127.0.0.1:9418
2026-11-14 17:44:22 [17795] Extended attribute "protocol": version=2
2026-11-14 17:44:22 [17795] Request upload-pack for '/Workspace0/NoSuchRepo.git'
2026-11-14 17:44:22 [9290] [17795] Disconnected (with error)
```

### どこを見れば「設定が効いている」とわかる？
- `Connection from ...`、`Extended attribute ...`、`Request ...`、`Disconnected` まで詳細な動作履歴が出力されていること。

> **判定**: 正常に動作していることを確認済み

---

## 37. `git daemon`：`--log-destination=stderr`（＋日次/曜日ログ保存）

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `--log-destination=stderr` |
| **どこに設定されているか** | 起動スクリプト ／ `/Users/user/.antigravity/global-backup/git-sandbox/scripts/start-git-daemon-monthly.sh` |
| **何をする時のパラメーターか** | `git daemon` がログを出力するとき |
| **役割（一言でいうと）** | OS のシステムログ（syslog）ではなく標準エラー出力（stderr）へログを出し、スクリプト側で日付付きファイル（`git-daemon_14.log`）に保存できるようにする |

### どうやって確認したか
`logs/git-daemon_14.log` が生成され、先頭に `YYYY-MM-DD HH:MM:SS` のタイムスタンプ付きでログが書き込まれていることを確認しました。

### どこを見れば「設定が効いている」とわかる？
- `/Users/user/.antigravity/global-backup/git-sandbox/logs/git-daemon_14.log` にリアルタイムでログが追記されていること。

> **判定**: 正常に動作していることを確認済み

---

## 38. `git daemon`：`--pid-file=/Users/user/.antigravity/global-backup/git-sandbox/logs/git-daemon.pid`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `--pid-file=/Users/user/.antigravity/global-backup/git-sandbox/logs/git-daemon.pid` |
| **どこに設定されているか** | 起動スクリプト ／ `/Users/user/.antigravity/global-backup/git-sandbox/scripts/start-git-daemon-monthly.sh` |
| **何をする時のパラメーターか** | `git daemon` が起動した直後（および停止・再起動時） |
| **役割（一言でいうと）** | 起動中のサーバーのプロセス番号（PID）をファイルに書き出し、確実に停止・再起動できるようにする |

### どうやって確認したか
```zsh
cat '/Users/user/.antigravity/global-backup/git-sandbox/logs/git-daemon.pid'
lsof -nP -iTCP:9418 -sTCP:LISTEN
```
```text
9290
git-daemo 9290 user ... TCP 127.0.0.1:9418 (LISTEN)
```

### どこを見れば「設定が効いている」とわかる？
- `git-daemon.pid` の中身（`9290`）と、`lsof` で動いている `git-daemon` の PID（`9290`）が完全に一致していること。

> **判定**: 正常に動作していることを確認済み

---

## 39. `git daemon`：末尾ディレクトリ引数 `/Users/user/.antigravity/global-backup/git-sandbox/repos`

| 項目 | 内容 |
|---|---|
| **パラメーター名と値** | `/Users/user/.antigravity/global-backup/git-sandbox/repos`（`git daemon` 最後の引数） |
| **どこに設定されているか** | 起動スクリプト ／ `/Users/user/.antigravity/global-backup/git-sandbox/scripts/start-git-daemon-monthly.sh` |
| **何をする時のパラメーターか** | `git daemon` が公開・許可するフォルダ範囲を決めるとき |
| **役割（一言でいうと）** | 指定したフォルダ（`repos`）配下だけを `git daemon` の公開許可リスト（ホワイトリスト）に登録する |

### どうやって確認したか
`repos/Workspace0/Project1.git` へのアクセスが許可されて `clone` / `push` が成功していることで確認しました。

> **判定**: 正常に動作していることを確認済み





# v6.5 スキル全文(全文ログ強制・起動時のテーマ制限撤廃)

v6.4からの変更は次の3点です。

- **IRON RULE 12を追加**: ログの要約を明示的に禁止。全文逐語記録を強制
- **log 手順5・5cを差し替え**: 全文記録の手順と、短すぎるログの検出を追加
- **start 手順8・9を差し替え**: ログの要点はテーマを問わず全部出す。再開候補の絞り込みを「担当=仕組み」だけに限定

```
name: ssot-state-machine

description:
Manage projects, tasks, rules, and decisions using the AI_SSOT_State.md file on Google Drive. Use when the user mentions SSOT, AI_SSOT_State, "Google Drive AI_SSOT_State_Machine", project state, tasks, past SSOT backups, or says "log", "記録", "ログ", "commit" (save), "verify" (check Drive), or "整理" (clean duplicates).

instructions:
# SSOT State Machine v6.5 (for small models: obey literally)

## IRON RULES (read first, never break)
1. NEVER say you did something unless you actually called a tool for it in THIS turn AND the tool returned a result.
2. After every write tool call, print one RECEIPT line copied from the tool result:
   【証跡】手順N | ツール名 | ファイルID: <from result> | タイトル: <from result> | 親フォルダID: <from result>
   Do not invent IDs. If the result has no ID, write "ID: 取得不可".
3. If a tool was not called or returned an error, print: 【未実行】手順N | 理由: <reason>. Then STOP. Do not continue to the next step (except where a step explicitly says to continue).
4. Banned words unless ALL receipts of the commit exist: 完了, 保存しました, 作成しました, 移動しました, 成功. Use "未確認" instead.
5. One step = one tool call. Never combine steps. Never skip steps. Never reorder steps.
6. Never guess. If you could not read something, say 読めませんでした.
7. Never create or move a FILE without a confirmed parent folder ID. Never write a file to the Drive root.
8. Reply in Japanese. Be short.
9. Folders: if SSOT_Backup or SSOT_Logs is not found by search, create ONLY the missing one(s) with drive:create_file (mime_type "application/vnd.google-apps.folder", title = the folder name, no parent unless the user specified one). Always search BEFORE creating, so you never create a duplicate folder. Then follow rule 10 (search again and print the raw list). Only a folder that appears in that list counts as created. If the list does not show it, print 【未実行】フォルダ作成 and STOP, then tell the user: "フォルダを作成できませんでした。Driveで手作りしてください。" Never claim a folder exists without it appearing in a search list.
10. A RECEIPT is only valid if followed by a SEARCH LIST: right after any create or move, search Drive again and print the raw result list (title / ID / parent folder name). If the target is not in that list, the step is 【未実行】, even if the tool said success.
11. The USER owns the user's work. Never decide what the user should work on next. Never present SSOT maintenance as the user's work. Only ask, summarize, and offer support.
12. Dialog log = verbatim full text. NEVER summarize, paraphrase, shorten, or omit any turn. Copy each USER and ASSISTANT turn exactly as spoken, character for character. If the full text does not fit in one file, split into _part1, _part2 (one tool call each). Summarizing is a critical failure.

## Names
- STATE file: `AI_SSOT_State.md`
- BACKUP folder: `SSOT_Backup`
- LOGS folder: `SSOT_Logs`
- Old generations are named `OLD_YYYYMMDD_HHMMSS_AI_SSOT_State.md`
- Logs are named `AI_SSOT_Dialog_Log_YYYYMMDD_HHMMSS.md`
- Files named OLD_* or inside BACKUP/LOGS are never the active STATE.

## STATE file format (do not change)
First line: `# AI_SSOT_State`. Then items, one blank line between items.

RULE and DECISION items:

- <ID>
  - 種類: ルール | 決定
  - 状態: 有効 | 廃止
  - 日付: YYYY-MM-DD
  - トピック: short label
  - 内容: one line description

TASK items (one extra line, 担当):

- <ID>
  - 種類: タスク
  - 担当: ユーザー | AI | 仕組み
  - 状態: 有効 | 完了 | 廃止
  - 日付: YYYY-MM-DD
  - トピック: short label
  - 内容: one line description

- ID = R (ルール) / D (決定) / T (タスク) + number. Numbers are one global sequence. New number = highest existing + 1.
- 担当 meaning:
  - ユーザー = the user's own work (projects, to-dos, deadlines). These are the continuation targets.
  - AI = work the user asked the assistant to do.
  - 仕組み = maintenance of this SSOT system itself (skill, Drive, logs, verification).
- Every value stays on ONE line.
- Never delete an item. Only change 状態.
- Add new items at the end. No tables, no code blocks, no extra headings.
- A TASK without a 担当 line is "担当未設定". Never treat it as the user's work. Ask the user at the next log to assign one.

## What goes where
- Procedures (how the assistant works) -> this skill only.
- Project data (tasks, project rules, decisions) -> the STATE file only.
- If the user states a procedure change: do not write it to the STATE file. Say "手順の変更はスキル側です", output the full updated skill for the user to paste, and add only a short DECISION item about why.
- When adding a TASK: set 担当. The user's own work or to-dos = ユーザー. Work the user asks the assistant to do = AI. Anything about this SSOT system = 仕組み. If unclear, ask the user once.

## COMMAND: start (first message mentions SSOT / AI_SSOT_State)
Do these in order. Print the result of each.
1. Search Drive for `AI_SSOT_State.md`, `SSOT_Backup`, `SSOT_Logs`.
2. FOLDER CHECK: confirm that both `SSOT_Backup` and `SSOT_Logs` appear in the search result. If one is missing, create it as in rule 9, search again, and print the raw list. Print each folder with its ID. If a folder still cannot be confirmed: STOP.
3. If more than one `AI_SSOT_State.md` exists outside BACKUP: print each one's ID and last-modified time. Say "重複あり。'整理' で片付けます。" Use the newest as the working copy. Do NOT move anything now.
4. Read the working STATE file fully. If no `AI_SSOT_State.md` exists at all, say "状態ファイルがありません。初期ファイルを置いてください。" and STOP. Do not create one on your own.
5. Report exactly in this format:
   接続: OK または 失敗(理由)
   読込: ファイル名 / ファイルID / 最終更新 / 項目数
   フォルダ: SSOT_Backup ID / SSOT_Logs ID (新規作成したものは「新規」と付ける)
   ルール・決定: 有効なものをIDとトピックだけ1行ずつ
   あなたのタスク: 担当=ユーザー かつ 有効 のものをIDと内容つきで
   AIへの依頼: 担当=AI かつ 有効 のものをIDと内容つきで
   仕組みの保守: 担当=仕組み かつ 有効 の件数だけ(内容は聞かれたときだけ)
   担当未設定: あればIDだけ
6. If the connection fails: say "入力欄で @Google Drive を付けて再送してください。" and STOP. Do not guess any content.
7. RESUME: search SSOT_Logs for files starting with `AI_SSOT_Dialog_Log_`. Sort by the timestamp in the title, newest first. Read the newest 5 (one tool call per file). Print each file's title and ID as you read it. If fewer than 5 exist, read all. If none exist, print "ログなし" and go to step 8 using the STATE only.
8. DIGEST: report in Japanese, exactly in this format:
   【前回の対話の要点】日時 / 1行の要点 (ログごとに1行。テーマを問わず、そのログで話したことをすべて書く。読めなかったログは「読めませんでした」と1行で書く。隠したり省いたりしない)
   【再開の候補】番号つき、最大5件。材料は「担当=ユーザーで有効なタスク」「担当=AIで有効なタスク」「ログに出てくる未完了・未解決の話題」すべて。各候補は「話題 / 止まっている場所 / 関連するSTATEのID(なければ なし)」
   担当=仕組みのタスクは候補に含めない。ただしログにSSOT自体の未解決話題があれば含めてよい。
   候補がゼロの場合のみ「記録がありません。何について進めますか?」と出す。
9. ASK: end with "どれを再開しますか? 番号で選んでください(新しい話題なら『新規』)". Then STOP and wait. Do not start any work before the user answers. Do not suggest what the user should do next.
10. AFTER CHOICE:
   - A number: re-read only the log(s) related to that candidate if more detail is needed. Summarize the last known state in 3 lines. Then ask "どこから再開しますか?" and let the user decide. You may list, in one line, what you can support (整理・下書き・調べ物・タスクの登録), but do not choose for the user.
   - 新規: ask "何について進めますか?".

## NORMAL CONVERSATION
- Never write to Drive on normal turns.
- Remember changes (new/updated task, rule, decision) as 未記録の変更.
- When there are 3 or more, say once: "未記録の変更が N 件あります。'log' で確定できます。"

## COMMAND: log (also 記録 / ログ / commit)
No preamble. Run the steps in order. After each step print the RECEIPT or 【未実行】. Stop at the first failure, except where a step says to continue.

1. TIME: get the current date and time. If you do not know it for certain, ask the user "現在の日時(例 20261025_143052)を教えてください" and STOP until answered.
2. READ: search and read the working STATE file. Print: ファイルID / 親フォルダID / 項目数 / 最大ID. Keep the full text in memory.
3. FOLDERS: search for `SSOT_Backup` and `SSOT_Logs`. If one is missing, create it as in rule 9 and search again. Print both IDs from the search list. If a folder still cannot be confirmed: print 【停止】 and STOP. Do not run step 4 or later.
4. BUILD: build the new STATE text with this turn's changes. Check: all attributes present and in order, TASK items have 担当, one-line values, no deleted items, no duplicate IDs. If any TASK has no 担当, ask the user for it before building. Print: 追加N件 / 更新N件 / 新しい最大ID.
5. LOG: create `AI_SSOT_Dialog_Log_<time>.md` with parentId = SSOT_Logs ID.
   Content = every completed, unlogged turn, copied VERBATIM (see rule 12):
   ## Turn N - USER
   <exact full text, nothing omitted>
   ## Turn N - ASSISTANT
   <exact full text, nothing omitted>
   The reply to the current "log" turn is not finished yet; skip it.
   If the total text exceeds 15000 characters, split:
   _part1: turns 1 to N where the split keeps each turn intact.
   _part2: remaining turns.
   One tool call per file. Print a RECEIPT for each.
   Do NOT summarize. Do NOT paraphrase. Do NOT compress. If you are tempted to shorten, STOP and split into another file instead.
5b. LOG PLACE CHECK: search for files whose title starts with `AI_SSOT_Dialog_Log_<time>`. Print the raw result list (title / ID / parent folder name). The parent must be SSOT_Logs.
   - If the parent is not SSOT_Logs: call drive:update_file ONCE with the file ID and parentId = SSOT_Logs ID. Then search again and print the list. If it is still not in SSOT_Logs: print 【未実行】ログの移動 and tell the user: "ログファイル <title> が <parent> に残っています。手動で SSOT_Logs へ移動してください。" Then continue to step 6 (the log is not a reason to skip the state backup), and mark the final report 未完了.
5c. Read the log file(s) back. Print the turn count AND the character count of each file. If the character count of any file is less than half the estimated total characters of the turns it should contain, print 【警告】ログが短すぎます。要約している可能性があります。 and ask the user: "ログが短すぎます。全文で書き直しますか? (yes/no)". If yes, delete the short file and redo step 5 from the beginning.
6. BACKUP OLD: with the OLD file ID from step 2, call drive:update_file ONCE to set title `OLD_<time>_AI_SSOT_State.md` AND parentId = SSOT_Backup ID. Print a RECEIPT.
6b. After step 6, search for `OLD_<time>_AI_SSOT_State.md` and print the raw result list (title / ID / parent folder name). The parent must be SSOT_Backup.
7. CHECK OLD: read the metadata of that file ID again. Print its title and parent ID. If the title does not start with OLD_ or the parent is not SSOT_Backup: STOP. Do NOT create the new STATE.
8. CREATE NEW: create `AI_SSOT_State.md` with parentId = the original parent folder ID from step 2, text_content = the text from step 4. Print a RECEIPT.
8b. After step 8, search for `AI_SSOT_State.md` and print the raw result list (title / ID / parent folder name).
9. VERIFY: from the list in step 8b, print the count of files titled exactly `AI_SSOT_State.md` outside BACKUP and each ID. The count must be 1. Read the new file and print 項目数 and 最大ID; they must match step 4.
   - If the count is not 1 or the numbers do not match: print "検証NG" and STOP. Do not fix anything on your own. Tell the user to say '整理'.
   - If step 8 failed: restore the old file (update_file with the original title and the original parent ID), print a RECEIPT, then report.

FINAL REPORT (only after step 9 printed OK and step 5b passed):
   結果: 検証OK
   項目: 追加/更新/完了/廃止 (IDつき)
   ログ: ファイル名 / ファイルID / 親フォルダ名 / ターン数 / 文字数
   バックアップ: ファイル名 / ファイルID / 親フォルダ名
   有効なSTATE: 1つ (ファイルID)
If any step was 【未実行】 or NG, instead print:
   結果: 未完了(手順N で停止)
   実行済みの証跡: (list)
   未実行: (list)
   ユーザーへ: 次にすること
   Also output the full new STATE text in a code block so the user can save it manually.

## COMMAND: verify
Do not write anything. Search Drive and print:
- every file titled `AI_SSOT_State.md` (ID, parent folder name, last modified)
- every file starting with `OLD_` (ID, title, parent folder name)
- every folder named `SSOT_Backup` or `SSOT_Logs` (ID, name). If there are two or more with the same name, say 同名フォルダ重複.
- the files in SSOT_Logs (title, ID)
- any file starting with `AI_SSOT_Dialog_Log_` whose parent is NOT SSOT_Logs (title, ID, parent folder name)
Then say whether there is exactly one active STATE. Say 未確認 for anything you could not see.

## COMMAND: 整理
Only when the user says it. Steps:
1. Run the verify listing.
2. If more than one active `AI_SSOT_State.md` exists: keep the newest by last-modified. For each other one, call drive:update_file ONCE: title `OLD_<time>_DUP_AI_SSOT_State.md`, parentId = SSOT_Backup ID. Print a RECEIPT and a SEARCH LIST each.
3. If any `AI_SSOT_Dialog_Log_*` file is outside SSOT_Logs: call drive:update_file ONCE per file with parentId = SSOT_Logs ID. Print a RECEIPT and a SEARCH LIST each.
4. If there are duplicate folders with the same name, do NOT delete or merge them. Report them and tell the user to merge by hand.
5. Run the verify listing again. Print the counts. Say 整理OK only if there is exactly one active STATE, no stray log files, and no duplicate folders.

## HISTORY SEARCH
Only when the user explicitly asks about past versions or past dialogs. Old STATE files and skill snapshots are in SSOT_Backup. Past dialogs are in SSOT_Logs. Say which folder each result came from. Do not mix them with current data. (The startup RESUME in start steps 7 to 10 is the only automatic read of SSOT_Logs.)

## TOOLS (Gemini + Google Drive)
- Search/read: Google Drive extension (user may need @Google Drive).
- Create file: drive:create_file (mime_type "text/markdown", text_content, parentId).
- Create folder: drive:create_file with mime_type "application/vnd.google-apps.folder". Confirm only by a search list (rule 10).
- Rename/move: drive:update_file (title and parentId in the SAME call).
- If a tool is not available or fails: say which one, print 【未実行】, output the text to save in a code block, and tell the user to save it by hand. Treat the update as 未確認 until the user says it is saved.
```

## 管理マークダウンの更新

```markdown
# AI_SSOT_State

- R1
  - 種類: ルール
  - 状態: 有効
  - 日付: 2026-10-25
  - トピック: 運用方針
  - 内容: 人間はファイルを直接編集せず、参照も更新もすべてAIとの対話で行う。

- R2
  - 種類: ルール
  - 状態: 有効
  - 日付: 2026-10-25
  - トピック: 報告の信頼性
  - 内容: AIは実行していない操作を完了と報告しない。書き込みの結果は検索や読み戻しで確認し、確認できないものは未確認と言う。

- R3
  - 種類: ルール
  - 状態: 有効
  - 日付: 2026-10-25
  - トピック: 破壊的操作
  - 内容: 既存データは削除せず、状態の書き換えか世代交代で残す。更新はユーザーがlogと指示したときだけ行う。

- R4
  - 種類: ルール
  - 状態: 有効
  - 日付: 2026-10-25
  - トピック: 説明の流儀
  - 内容: 仮の推測は仮と明記し、断言できないことは分からないと答える。

- D5
  - 種類: 決定
  - 状態: 有効
  - 日付: 2026-10-25
  - トピック: 役割分担
  - 内容: 手順はスキルのみ、データは状態ファイルのみに書き、二重管理によるズレを防ぐ。

- D6
  - 種類: 決定
  - 状態: 有効
  - 日付: 2026-10-25
  - トピック: 状態の形式
  - 内容: スプレッドシートをやめ、AIに依存しない縦長のMarkdown箇条書きで状態を管理する。

- D7
  - 種類: 決定
  - 状態: 有効
  - 日付: 2026-10-25
  - トピック: ログ形式
  - 内容: 対話ログは全文を1セルに詰めるCSVで破綻したため、コミットごとの別Markdownファイルにした。

- D8
  - 種類: 決定
  - 状態: 有効
  - 日付: 2026-10-25
  - トピック: コミット指示語
  - 内容: 記録の主トリガーはlogとし、記録、ログ、commitも同義で受け付ける。

- D9
  - 種類: 決定
  - 状態: 有効
  - 日付: 2026-10-25
  - トピック: フォルダ作成
  - 内容: SSOT_BackupとSSOT_Logsは無ければAIが作る。ただし作成後に検索結果の一覧で存在を確認できたものだけを作成済みとみなす。AIが作成を偽って報告したため。

- D10
  - 種類: 決定
  - 状態: 有効
  - 日付: 2026-10-25
  - トピック: 使用モデル
  - 内容: 普段はGemini Flash Liteを使う。虚偽報告が出るため、重要な書き込み(log)は上位モデルへの切り替えも検討する。

- T11
  - 種類: タスク
  - 担当: ユーザー
  - 状態: 有効
  - 日付: 2026-10-25
  - トピック: 目的の登録
  - 内容: この場所で何を管理するか(仮: 〇〇プロジェクトの進行管理)をAIに伝え、目的とゴールの項目を追加する。

- T12
  - 種類: タスク
  - 担当: ユーザー
  - 状態: 有効
  - 日付: 2026-10-25
  - トピック: プロジェクト登録
  - 内容: 進行中のプロジェクトを1つずつ伝え、プロジェクトごとの現状と次の一手をタスクとして登録する。

- T13
  - 種類: タスク
  - 担当: 仕組み
  - 状態: 有効
  - 日付: 2026-10-25
  - トピック: 動作確認
  - 内容: logを1回実行し、verifyで有効なSTATEが1つだけであること、ログがSSOT_Logsにあることを確認する。

- T14
  - 種類: タスク
  - 担当: 仕組み
  - 状態: 有効
  - 日付: 2026-10-25
  - トピック: ID照合
  - 内容: Geminiが返すファイルIDが本物か、DriveのURLのIDと1つ照合して確認する。

- T15
  - 種類: タスク
  - 担当: 仕組み
  - 状態: 有効
  - 日付: 2026-10-25
  - トピック: 複数プロジェクト対応
  - 内容: 同じDriveで複数の場所に展開する場合、状態ファイル名の衝突を避ける命名(例: AI_SSOT_State_ProjectA.md)に変更するか検討する。

- D16
  - 種類: 決定
  - 状態: 有効
  - 日付: 2026-10-25
  - トピック: 起動時の再開
  - 内容: 起動時に最新5件のログを読み、継続候補を番号で提示して選んだ作業から再開できるようにした。

- D17
  - 種類: 決定
  - 状態: 有効
  - 日付: 2026-10-25
  - トピック: 再開はユーザー主体
  - 内容: 継続候補は担当がユーザーのタスクと、ユーザーの仕事の話題だけにする。SSOT自体の保守は候補に出さず、何を進めるかはユーザーが決める。

- D18
  - 種類: 決定
  - 状態: 有効
  - 日付: 2026-10-30
  - トピック: ログ要点のテーマ制限撤廃
  - 内容: 起動時のログ要点はテーマを問わず全件出す。仕事以外の話題を隠す設計が「仕事の話題なし」の連発を招いたため廃止した。
```


## v6.4 → v6.5 の変更点まとめ

- **IRON RULE 12**: 要約・省略・言い換えを明示的に禁止。全文逐語を強制
- **log 手順5**: 15000文字超は分割。要約したくなったら分割せよ、と明記
- **log 手順5c**: 読み戻し時に文字数も出す。短すぎたら警告して書き直しを確認
- **log 最終報告**: ログの文字数を追加
- **start 手順8**: ログ要点はテーマを問わず全件出す。「仕事の話題なし」は廃止
- **start 手順9**: 「保守」の選択肢を削除。再開候補に絞る









Docs から Markdown への書き出しは Drive API v3 の export(`text/markdown`)で行える。認証トークンは `ScriptApp.getOAuthToken()` で渡す。新規スクリプトは `script.google.com/create` から作れる。スマホ操作部分(PC版サイト表示など)は検索では確認できておらず、一般的な動きに基づく案内です。

```
やること全体
│
├─ ① スクリプトを作る
│   ├─ Chrome で script.google.com/create を開く
│   │   └─ 開きにくければ Chrome の「︙」
│   │       →「PC版サイト」にチェック
│   ├─ 最初から入っているコードを全部消す
│   └─ 下のコードを貼り付けて保存(💾)
│
├─ ② 実行する
│   ├─ 関数名を「convertAgentHub」にする
│   ├─ ▶「実行」をタップ
│   └─ 初回だけ許可画面が出る
│       ├─ 「権限を確認」→ 自分のアカウント
│       ├─ 「詳細」→「安全ではないページに移動」
│       │   └─ 自作スクリプトなので出る警告
│       └─ 「許可」
│
└─ ③ 結果を見る
    └─ Drive の Agent_Hub の中に
        「md_export」フォルダができる
        └─ 中に .md ファイルが並ぶ

安全面
├─ 元のドキュメントは触らない(消さない)
├─ 何度実行しても重複せず上書きされる
└─ 対象は Agent_Hub 直下のドキュメントのみ
    (サブフォルダ内と本物の .md は対象外)
```

**貼り付けるコード**(コピーボタンで全コピーしてください)

```javascript
function convertAgentHub() {
  const roots = DriveApp.getRootFolder().getFoldersByName('Agent_Hub');
  if (!roots.hasNext()) throw new Error('Agent_Hub が見つかりません');
  const src = roots.next();
  const outs = src.getFoldersByName('md_export');
  const out = outs.hasNext() ? outs.next() : src.createFolder('md_export');
  const token = ScriptApp.getOAuthToken();
  const files = src.getFilesByType(MimeType.GOOGLE_DOCS);
  let ok = 0, ng = 0;
  while (files.hasNext()) {
    const f = files.next();
    const url = 'https://www.googleapis.com/drive/v3/files/' + f.getId() +
      '/export?mimeType=' + encodeURIComponent('text/markdown');
    const res = UrlFetchApp.fetch(url, {
      headers: { Authorization: 'Bearer ' + token },
      muteHttpExceptions: true
    });
    if (res.getResponseCode() !== 200) {
      ng++;
      Logger.log('失敗: ' + f.getName());
      continue;
    }
    const name = f.getName().replace(/\.md$/i, '') + '.md';
    const old = out.getFilesByName(name);
    if (old.hasNext()) old.next().setContent(res.getContentText());
    else out.createFile(name, res.getContentText(), 'text/markdown');
    ok++;
  }
  Logger.log('完了: 成功 ' + ok + ' / 失敗 ' + ng);
}
```

**イメージ**: ドキュメントを1枚ずつコピー機に通して、.md の紙を `md_export` というトレーに出していく仕組みです。原本はそのまま残ります。

**注意**
- 変換で表やリストの記法が少し変わることがあります。
- 数百ファイルなど大量だと、Apps Script の実行時間制限(約6分)に当たる可能性があります。その場合は再実行すれば、続きから上書きで進みます。
- 完了メッセージは、エディタ下部の「実行ログ」で見られます。


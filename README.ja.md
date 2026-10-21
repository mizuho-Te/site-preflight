# site-preflight · 0.1.0

[English](README.md)

静的サイトを公開する前に、ローカルの HTML 書き出しを点検する小さな CLI です。Python 3.11 以上と標準ライブラリだけで動き、API キー・アカウント・ネットワーク通信は不要です。

**[MIT ライセンス](LICENSE)による初版ソースです。** 合成データで検証した初期プロジェクトであり、利用実績・利用者・支援制度への応募資格や採択を主張しません。

## 使い方

ZIP を展開し、このフォルダー内で実行します。外部パッケージのインストールは不要です。

```sh
python -m site_preflight examples/clean --lang ja
python -m site_preflight examples/broken --lang ja
python -m site_preflight "/サイトの書き出し先" --lang ja --format json > report.json
python -m site_preflight "/サイトの書き出し先" --fail-on warning
```

Windows では必要に応じて `python` を `py -3` に置き換えてください。UTF-8 の HTML（BOM 可）、1 ファイル最大 5 MiB に対応します。信頼できる、検査中に変更されない書き出しフォルダーを使ってください。

終了コードは 0＝指定基準以上の指摘なし、1＝指摘あり、2＝指定や入力ディレクトリの問題です。0 は SEO・アクセシビリティの合格保証ではありません。既定は error だけで失敗し、`--fail-on warning` では warning も含めます。`--fail-on never` は点検完了後の失敗扱いを無効にします。

## 点検できること

- title・meta description の空欄や重複
- H1 の数（1 個を目安とする本ツールの方針で、普遍的な HTML 違反判定ではありません）
- 画像 alt 属性の有無。装飾画像の `alt=""` は許容しますが、画像が装飾か・説明が適切かは判断できません
- canonical の有無・重複・HTTP(S) 絶対 URL かどうか
- ローカルリンク・一般的な src 画像等・スタイルシートのファイル存在と HTML 内の ID/name
- ルートの robots.txt・sitemap.xml の存在のみ。内容や実際の検索登録は検査しません

title 不足・リンク先欠落・安全に読めないパス・読み取り失敗・巨大 HTML・HTML 不在は error。description / canonical / H1 / alt / アンカーは warning。robots / sitemap 不在は info とし、必須扱いしません。

## 誤解しやすい点

外部 URL、同一ドメインの絶対 URL、mailto / tel などは未検査です。レポートの未検査件数を確認してください。検査していないものを成功とは扱いません。

相対パス・ルート相対パスに対応し、クエリは無視、パーセント表記を復号します。ディレクトリは index.html、次に index.htm を探します。`/about` を `/about.html` とみなすようなサーバー固有の書き換えは推測しません。実環境の配信設定・サブパス・SPA では警告が実状と異なることがあります。base href のあるページはリンク検査を省略し警告します。テキストフラグメント、非 HTML / 読めない HTML のアンカー、CSS 内 URL、srcset、SVG リンク、フォーム、JS 生成リンク、サイトマップ記載先は検査対象外です。

シンボリックリンクはルートまでの親パス・内部へのリンクも含めて追跡せず、ルート外参照を拒否します。ただし検査中のファイル改変に耐えるサンドボックスではありません。大量のページには時間・メモリがかかります。検査したページ数に読み取れない HTML は含みません。

JavaScript 実行、スマホ実表示、速度、コントラスト、キーボード操作、ライブ URL、検索順位、実際のインデックスは検査しません。完全な SEO・アクセシビリティ・セキュリティ監査や、検索順位・法令適合の保証ではありません。

## 開発と公開

```sh
python -m unittest discover -s tests -v
python -m compileall -q site_preflight tests
```

サンプルはすべて架空です。clean は終了 0、broken は意図した指摘で終了 1 です。CI 設定は同梱していますが、GitHub 上で実行した実績ではありません。JSON は schema_version 1、ルール code を使って機械処理できます。詳細は英語 README を参照してください。

実際のサイトに導入する前に、検証範囲と制限を確認してください。利用者数やスターを捏造せず、本当に使ってもらって改善を続けるための土台です。

## 他のツールとの関係

第三者 Python 依存なし・日本語/英語・JSON の小さな公開前チェックが狙いです。新規性や優位性を保証せず、[HTML-validate](https://html-validate.org/)、[lychee](https://github.com/lycheeverse/lychee)、[Pa11y](https://pa11y.org/)、[Lighthouse](https://developer.chrome.com/docs/lighthouse/overview) 等の代替を目指すものではありません。

CLI の標準出力・標準エラー出力は UTF-8 です。2026-10-21、Ubuntu・Windows・macOS × Python 3.11 / 3.12 / 3.13 の 9 通りの CI が成功しました。[検証結果](https://github.com/mizuho-Te/site-preflight/actions/runs/39561280839)。Windows では FIFO 非対応のテストをスキップします。

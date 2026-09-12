# MRI Learning

MRI教材を検索・分類して閲覧できるGitHub Pagesポータルです。iPad Safariを中心に、PCやスマートフォンにも対応します。

公開URL: https://y-hiroki-radiotech.github.io/mri-active-learning-quiz/

## 教材の追加先

教材は次の2ディレクトリだけから自動収集されます。

```text
MRI撮像シーケンスのアクティブラーニングの解説/
シーケンス解説/
```

サブディレクトリも再帰的に検索します。拡張子`.html`または`.htm`のファイルに加え、拡張子がなくても内容がHTMLなら教材として取り込みます。

## 自動登録

メタデータがない教材も、HTMLの`<title>`、配置ディレクトリ、更新日時から自動登録されます。

- アクティブラーニング側は原則`MRI物理`
- シーケンス解説側は原則`撮像シーケンス`
- タイトルにゴースト、アーチファクト、bandingなどがあれば`Artifact`
- タイトルにDICOM、撮像時間、パラメータ実践などがあれば`パラメータ`
- 同一内容のファイルは1教材にまとめる

より正確な情報を指定するときは、HTMLの`<head>`へ任意のメタデータを追加できます。

```html
<meta name="mri-id" content="swan-guide">
<meta name="mri-title" content="SWAN 原理・撮像プロトコル">
<meta name="mri-category" content="sequences">
<meta name="mri-subcategory" content="Susceptibility Imaging">
<meta name="mri-keywords" content="SWAN,T2*,磁化率,微小出血,静脈,GRE">
<meta name="mri-description" content="SWANの原理と撮像法を解説します。">
<meta name="mri-updated" content="2026-09-12">
<meta name="mri-content-type" content="guide">
<meta name="mri-manufacturer" content="GE">
<meta name="mri-anatomy" content="頭部">
```

`mri-category`には`physics`、`sequences`、`artifacts`、`parameters`、`coils`、`anatomy`、`positioning`、`questions`を指定できます。`mri-content-type`は`guide`または`simulator`です。

## GitHub Pagesへの反映

2ディレクトリ内の変更をcommitして`main`へpushすると、GitHub Actionsが次を自動実行します。

1. 2ディレクトリから教材を検出
2. `materials.json`を生成
3. 公開用の英数字URLへ教材を配置
4. GitHub Pagesへデプロイ

## 自動復習

トップページの「復習する」から、GitHubへ新しく追加された教材の復習ページを開けます。

- 新規追加の翌日：「昨日の復習」
- 新規追加の7日後：「先週の復習」
- 予定日に復習できなかった教材は、完了するまで表示
- 翌日分と7日後分はそれぞれ独立して記録

復習予定は日本時間を基準にブラウザ側で計算するため、日付が変わったときにPagesを再デプロイする必要はありません。復習履歴は`localStorage`へ保存されるため、端末やブラウザをまたいだ同期は行われません。

復習対象は、基準コミット`dc7998fe79bcc26aa155a16bb46cd77ef56d3a0c`より後に初めてGitへ追加されたHTMLです。既存教材の内容更新だけでは、新しい復習予定は作成されません。ファイル名や保存場所を後から変更する可能性がある教材には、履歴を安定して識別できるよう`mri-id`の設定を推奨します。

初回のみ、GitHubリポジトリの「Settings → Pages → Source」で`GitHub Actions`を選択してください。ローカルフォルダへ追加しただけでは公開されないため、commitとpushが必要です。

## ローカル確認

```bash
python3 scripts/build_site.py --check
python3 -m unittest discover -s tests -v
node --test tests/test_review_logic.js
python3 scripts/build_site.py --output _site
python3 -m http.server 8000 --directory _site
```

## 公開上の注意

患者個人情報、医療機関内部情報、個人を特定できるDICOM情報、公開許可のない資料は追加しないでください。教材は外部CDNに依存しない1ファイル完結型を推奨します。

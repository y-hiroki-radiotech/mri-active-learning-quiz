# MRI教材 GitHub自動コミット設定要件

## 1. 目的

Google Driveから1日1回同期されるMRI教材を、安全にGitへcommit・pushし、GitHub Actions経由でGitHub Pagesへ自動反映する。

自動化の対象は、次の2ディレクトリ内に追加・更新・削除された教材だけとする。

```text
/Users/yanagisawahiroki/Desktop/MRIプロトコール/MRI撮像シーケンスのアクティブラーニングの解説/
/Users/yanagisawahiroki/Desktop/MRIプロトコール/シーケンス解説/
```

## 2. 前提条件

- 対象リポジトリは`y-hiroki-radiotech/mri-active-learning-quiz`とする。
- 自動push先は`origin/main`とする。
- GitHub CLIまたはGitが、対話操作なしでpushできるよう認証済みであること。
- GitHub Pagesの公開元が`GitHub Actions`に設定されていること。
- ポータル本体と`.github/workflows/deploy-pages.yml`が事前に`main`へ反映済みであること。
- macOSのスリープ中は実行できなくてもよいが、次回起動時に未実行分を1回実行できる設定にする。

## 3. 日次処理

次の順序を変更しないこと。

1. 多重実行防止ロックを取得する。
2. リポジトリと`origin`へアクセスできることを確認する。
3. 現在のブランチが`main`であることを確認する。
4. 対象ディレクトリ外に未commitの変更がないことを確認する。
5. `git pull --ff-only origin main`でリモートの変更を取得する。
6. 既存の`scripts/drive_sync.sh`を実行してGoogle Driveから2ディレクトリを同期する。
7. `python3 scripts/build_site.py --check`を実行する。
8. `python3 -m unittest discover -s tests -v`を実行する。
9. 対象2ディレクトリの変更だけをステージする。
10. ステージされた差分がなければ、commit・pushせず正常終了する。
11. 差分があれば日付入りメッセージでcommitする。
12. `git push origin main`を実行する。
13. 実行結果をローカルログへ記録し、ロックを解除する。

## 4. commit対象

次を対象とする。

- 対象2ディレクトリ内のHTMLファイルの追加
- HTMLファイルの内容更新
- Google Drive側の削除に同期処理が対応した場合のHTML削除
- 拡張子が`.html`または`.htm`の教材
- 拡張子がなくても、中身がHTMLである教材
- 対象ディレクトリ内のサブディレクトリにある教材

次は自動commitしない。

- `.drive_sync_manifest.json`
- `.DS_Store`
- ログファイル
- 一時ファイル、ロックファイル、キャッシュ
- `_site/`
- `index.html`、`assets/`、`scripts/`、`tests/`、`.github/`など、対象2ディレクトリ外の変更
- 要件定義書、READMEなどの文書変更

`git add .`や`git add -A`をリポジトリ全体に対して実行してはならない。必ず対象2ディレクトリを明示し、管理ファイルを除外すること。

## 5. commitメッセージ

次の形式とする。日時はAsia/Tokyoを使用する。

```text
chore(materials): sync MRI lessons YYYY-MM-DD
```

同じ日に複数回commitする可能性がある場合は時刻も追加する。

```text
chore(materials): sync MRI lessons YYYY-MM-DD HH:mm JST
```

## 6. 安全条件

- `git push --force`、`--force-with-lease`、`git reset --hard`は使用しない。
- merge conflictを自動解決しない。
- `git pull --ff-only`が失敗した場合は同期・commitを中止する。
- pushがnon-fast-forwardで失敗した場合は再pushやrebaseを自動実行せず、ローカルcommitを残してエラーを記録する。
- 対象外ファイルに未commit変更がある場合は、stash・破棄・commitをせず処理を中止する。
- 教材検証またはテストが失敗した場合、commit・pushしない。
- 空のcommitを作成しない。
- 患者個人情報、院内機密、公開許可のない資料を検出・判断できないため、同期元には公開可能な教材だけを置く運用とする。
- 認証トークン、Google Drive情報、環境変数の値をログやcommitへ出力しない。

## 7. ログ

ログの保存先は次とする。

```text
~/Library/Logs/mri-git-auto-commit.log
```

最低限、次を記録する。

- 開始・終了日時
- 同期処理の成功または失敗
- 検証・テスト結果
- 変更ファイル数
- 作成したcommit SHA
- push結果
- 中止理由またはエラー概要

ログへ教材本文、認証情報、環境変数の全内容は記録しない。

## 8. macOSスケジュール

- `launchd`のLaunchAgentとしてユーザー権限で実行する。
- 実行頻度は1日1回とする。
- 初期設定時刻は毎日21:00 JSTとする。
- `RunAtLoad`を有効にし、Macが予定時刻に停止していた場合は次回ログイン後に1回実行する。
- 同じ処理が同時実行されないようにし、ロック取得に失敗した実行は正常にスキップする。
- スクリプト内で`HOME`を上書きしない。
- リポジトリの絶対パスを実行前に検証し、存在しない場合は中止する。

## 9. GitHub Pagesとの連携

- 自動commitが`main`へpushされると、`.github/workflows/deploy-pages.yml`が起動する。
- Pagesワークフローは指定2ディレクトリだけを走査して`materials.json`を生成する。
- HTMLに`mri-*`メタデータがなくても、`<title>`と配置元から自動登録する。
- 同じ内容のファイルが複数ある場合は、教材一覧で重複させない。
- ビルドまたはデプロイ失敗を、自動コミット処理がforce pushなどで修復しようとしてはならない。

## 10. 受け入れ基準

- 新しいHTMLを対象ディレクトリへ置くと、次の日次実行でcommit・pushされる。
- 既存HTMLを変更すると更新としてcommitされる。
- 変更がない日はcommitが作成されない。
- 対象外の作業中ファイルが自動commitされない。
- `.drive_sync_manifest.json`と`.DS_Store`がGitHubへ送信されない。
- 検証エラー時にcommit・pushされず、理由がログに残る。
- push成功後、GitHub Actionsが起動して教材がGitHub Pagesに表示される。
- スクリプトを同時に2回起動してもcommitが重複しない。
- ネットワーク停止、認証失敗、non-fast-forward時に既存ファイルやGit履歴を破壊しない。

## 11. Claudeへの実装指示

この要件に基づき、以下を作成すること。

- 日次同期・検証・限定ステージ・commit・pushを行うシェルスクリプト
- macOS LaunchAgent用plist
- インストール、手動実行、停止、ログ確認、アンインストール手順
- dry-runモード
- シェル構文検査と、Git操作をモックした最低限の自動テスト

実装時に自動commitやpushを実際に有効化する前に、dry-run結果とステージ対象一覧を利用者へ提示し、明示的な確認を得ること。

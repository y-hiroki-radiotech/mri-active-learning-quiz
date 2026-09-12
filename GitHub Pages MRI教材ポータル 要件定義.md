# GitHub Pages MRI教材ポータル 要件定義

## 1. 目的

多数存在するMRI学習用HTMLファイルをGitHub上で一元管理し、GitHub Pagesを利用してiPad・Mac・PCなどから簡単に閲覧できる「MRI教材ライブラリ」を構築する。

教材数が今後数十〜数百以上に増えても、探しやすく、追加しやすく、管理しやすい構造とする。

特にiPadでの利用を重視する。

---

## 2. 基本方針

### 教材HTMLは原則として1ファイル完結型とする

各教材HTMLは可能な限り以下をHTML内部に含める。

- CSS
- JavaScript
- SVG
- アニメーション
- シミュレーター
- 数式表示に必要な処理
- UI
- 図解

原則として以下に依存しない。

- CDN
- 外部CSS
- 外部JavaScript
- Google Fonts
- MathJax CDN
- KaTeX CDN
- Mermaid CDN
- 表示に必須となる外部画像

目的は、GitHub Pagesだけでなく、HTMLを単体でダウンロードした場合にも可能な限りオフラインで利用できるようにすることである。

---

## 3. GitHub Pagesの役割

GitHub PagesをMRI教材全体のポータルとして使用する。

トップページ：

`index.html`

を教材ライブラリの入口とする。

利用者は基本的に個々のHTMLファイルのURLを覚える必要はなく、index.htmlから教材を検索・選択して開けるようにする。

---

## 4. 推奨ディレクトリ構成

例：

```text
mri-active-learning/
│
├── index.html
├── .nojekyll
│
├── sequences/
│   ├── fspgr.html
│   ├── fiesta.html
│   ├── swan.html
│   ├── merge.html
│   └── cube.html
│
├── physics/
│   ├── bloch-equation.html
│   ├── t1-relaxation.html
│   ├── t2-relaxation.html
│   └── k-space.html
│
├── artifacts/
│   ├── n2-ghost.html
│   ├── chemical-shift.html
│   ├── motion.html
│   └── susceptibility.html
│
├── coils/
│   ├── artist-coils.html
│   └── hero-coils.html
│
├── anatomy/
│
├── positioning/
│
├── parameters/
│
└── questions/
```

教材が増えた場合も、1つのフォルダに大量に保存するのではなくカテゴリー別に整理する。

---

## 5. 教材カテゴリー

最低限、以下のカテゴリーを用意する。

### MRI物理

例：

- Bloch方程式
- T1緩和
- T2緩和
- T2*
- RFパルス
- 傾斜磁場
- k-space
- Fourier変換
- SNR
- CNR

### 撮像シーケンス

例：

- SE
- FSE
- GRE
- FSPGR
- FIESTA
- SWAN
- MERGE
- CUBE
- DWI
- EPI
- IR
- STIR
- Dixon

### Artifact

例：

- N/2 ghost
- Motion
- Chemical Shift
- Susceptibility
- Aliasing
- Gibbs
- Zipper
- Magic Angle

### 装置・コイル

例：

- SIGNA Artist 1.5T
- SIGNA Hero 3.0T
- Head Coil
- Spine Coil
- Flex Coil

### 撮像部位・Positioning

例：

- 頭部
- 頸椎
- 胸椎
- 腰椎
- 肩
- 膝
- 骨盤
- 腹部

### パラメータ調整

例：

- TR
- TE
- FA
- FOV
- Matrix
- Slice Thickness
- BW
- NEX
- ETL
- Parallel Imaging

### 問題集

- 基礎問題
- 臨床問題
- パラメータ調整問題
- Artifact問題
- シーケンス問題

カテゴリーは今後追加可能な構造とする。

---

# 6. index.html

index.htmlは単純なリンク一覧ではなく、MRI教材ポータルとして作成する。

## 必須機能

### 6.1 教材検索

ページ上部に検索欄を配置する。

例：

```text
MRI Learning Library

🔍 教材を検索
[_____________________]
```

文字を入力するとリアルタイムで教材を絞り込む。

検索対象には最低限、

- 教材タイトル
- カテゴリー
- キーワード
- シーケンス名
- メーカー名
- 撮像部位

を含める。

日本語・英語の両方を検索できるようにする。

例：

`SWAN`

`磁化率`

`GRE`

`頸椎`

などで検索可能とする。

---

## 6.2 カテゴリー絞り込み

ボタンまたはタブを配置する。

例：

```text
すべて
MRI物理
Sequence
Artifact
Coil
Positioning
Parameter
問題集
```

カテゴリーを選択すると該当教材のみ表示する。

---

## 6.3 教材カード

各教材はカード形式で表示する。

例：

```text
SWAN

3D T2* Weighted Angiography

カテゴリー：
Sequence / Brain

キーワード：
T2*・磁化率・静脈・微小出血

［教材を開く］
```

最低限表示する情報：

- 教材名
- 短い説明
- カテゴリー
- キーワード
- 更新日
- 教材を開くボタン

---

# 7. 教材一覧の自動更新

最重要要件。

新しいHTML教材をGitHubリポジトリへ追加するたびに、人間がindex.htmlへ手作業でリンクを追加する運用にはしない。

教材追加時に、できるだけ自動的に教材一覧へ反映する。

推奨方式：

GitHub Actionsを使用する。

```text
HTML追加
   ↓
GitHubへpush
   ↓
GitHub Actions実行
   ↓
教材ファイルを検索
   ↓
教材情報を取得
   ↓
教材一覧データ生成
   ↓
index.htmlから表示
```

---

# 8. 教材メタデータ

各教材HTMLに検索・分類用メタデータを持たせる。

例：

```html
<meta name="mri-title" content="SWAN">
<meta name="mri-category" content="Sequence">
<meta name="mri-subcategory" content="Brain">
<meta name="mri-keywords" content="SWAN,T2*,磁化率,微小出血,静脈,GRE">
<meta name="mri-description" content="SWANの原理・撮像法・パラメータを解説">
```

可能なら更新日も設定する。

```html
<meta name="mri-updated" content="2026-09-12">
```

GitHub Actionsはこれらを読み取り、教材一覧を作成する。

---

# 9. 教材データベース

教材一覧をHTMLへ直接大量に書き込むのではなく、可能であればJSONとして管理する。

例：

```text
materials.json
```

例：

```json
[
  {
    "title": "SWAN",
    "category": "Sequence",
    "keywords": ["SWAN", "T2*", "磁化率", "GRE"],
    "path": "sequences/swan.html"
  },
  {
    "title": "N/2 Ghost",
    "category": "Artifact",
    "keywords": ["EPI", "Ghost", "DWI"],
    "path": "artifacts/n2-ghost.html"
  }
]
```

index.htmlのJavaScriptがmaterials.jsonを読み込み教材カードを生成する。

materials.jsonについても、可能な限りGitHub Actionsで自動生成する。

---

# 10. iPad最適化

iPad Safariでの閲覧を主要用途とする。

以下に対応する。

- iPad縦向き
- iPad横向き
- タッチ操作
- Safari
- ホーム画面からの起動

レスポンシブデザインとする。

---

# 11. タッチ操作

重要な操作はマウスホバーに依存させない。

以下はすべてタップで操作可能とする。

- ボタン
- スライダー
- タブ
- 教材カード
- アニメーション開始
- 一時停止
- リセット
- シミュレーター

タップ領域は小さくしすぎない。

---

# 12. MRIアニメーション対応

教材内ではJavaScript、CSS、SVGを利用した動的教材を使用可能とする。

例：

- RFパルス
- Gradient
- Echo
- TR timeline
- TE
- k-space trajectory
- Spin animation
- Longitudinal magnetization
- Transverse magnetization
- T1 recovery
- T2 decay
- Phase dispersion
- RF spoiling
- Gradient spoiling

---

# 13. MRIシミュレーター対応

教材HTML内にインタラクティブシミュレーターを含められる構造とする。

例えば：

```text
TR
TE
FA
T1
T2
Gradient
BW
Matrix
```

などをスライダーで変更すると、

- Magnetization
- Signal
- Sequence diagram
- k-space
- Contrast

などがリアルタイムに変化する教材を許容する。

---

# 14. 数式

MRI物理教材では数式を積極的に使用する。

ただしCDNへの依存を避ける。

オフライン状態でも、

- 分数
- 指数
- 添字
- 上付き
- ギリシャ文字
- 行列
- 積分
- 微分

などが正常表示されること。

---

# 15. オフライン利用

GitHub Pages版はオンライン教材ライブラリとして使用する。

一方で個々の教材HTMLをダウンロードした場合には、

```text
Wi-Fi OFF
↓
HTMLを開く
↓
文章表示
↓
図解表示
↓
数式表示
↓
アニメーション動作
↓
シミュレーター動作
```

まで可能なことを目標とする。

そのため、教材HTMLは原則1ファイル完結型を維持する。

---

# 16. ホーム画面対応

iPad SafariからGitHub Pagesトップページをホーム画面へ追加した際、教材ライブラリをWebアプリのように利用できるデザインとする。

ホーム画面用名称：

MRI Learning

または

MRI Active Learning

などを想定する。

---

# 17. デザイン

医療・MRI教育用として、

- 見やすい
- シンプル
- 情報量が多くても読みやすい
- iPadで操作しやすい

デザインとする。

過度な装飾は避ける。

---

# 18. Dark Mode

可能であれば、

- Light
- Dark
- OS設定連動

へ対応する。

---

# 19. お気に入り

将来的な追加機能として、教材をお気に入り登録できるようにする。

ログインは必要とせず、

```text
localStorage
```

等を利用して端末内へ保存する方式を基本とする。

---

# 20. 学習履歴

将来的には、

- 閲覧済み
- 未閲覧
- お気に入り
- 最終閲覧日時

などを端末内へ保存可能とする。

サーバー側DBは原則使用しない。

---

# 21. セキュリティ・情報管理

GitHub Pagesへ掲載する教材には以下を含めない。

- 患者個人情報
- 医療機関内部情報
- 機密情報
- 個人を特定できるDICOM情報
- 公開できない院内資料
- 公開許可のない資料

GitHub Pagesで扱うものは公開可能な教育コンテンツのみとする。

---

# 22. ファイルサイズ

教材HTMLは1ファイル完結を優先するが、不必要に巨大化させない。

特に、

- Base64画像
- 高解像度画像
- 動画
- 大容量ライブラリ

の埋め込みは注意する。

画像は必要に応じて、

- SVG
- WebP
- 圧縮PNG/JPEG

などを使用する。

---

# 23. GitHub Pages

基本構成として、

```text
main
└── /
```

または

```text
main
└── /docs
```

をGitHub Pagesの公開ソースとして使用する。

静的HTMLを直接使用する場合は、

```text
.nojekyll
```

を配置する。

---

# 24. 新規教材追加フロー

最終的に以下程度の作業で教材を追加できることを目標とする。

```text
① 新しい教材HTMLを作成

② 適切なカテゴリーへ保存

例：
sequences/fspgr.html

③ GitHubへpush

④ GitHub Actions実行

⑤ materials.json更新

⑥ GitHub Pages更新

⑦ index.htmlに自動表示
```

人間がindex.htmlへ毎回リンクを追加する作業を可能な限り不要にする。

---

# 25. 最終目標

最終的には、GitHub Pagesを

「MRI学習専用Webアプリ」

として利用できる状態を目指す。

使用イメージ：

```text
iPad
 ↓
MRI Learning
 ↓
検索
「FSPGR」
 ↓
FSPGR教材
 ↓
原理
 ↓
Sequence Diagram
 ↓
1TR Animation
 ↓
k-space Simulator
 ↓
Parameter Simulator
 ↓
臨床応用
 ↓
確認問題
```

多数の独立HTML教材を単純に保管するだけではなく、

「検索可能・分類可能・追加が容易なMRI教材ライブラリ」

として構築することを最終要件とする。
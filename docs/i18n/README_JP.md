# 🧠 Greeum v0.5.0

<p align="center">
  <a href="../../README.md">🇰🇷 한국어</a> |
  <a href="README_EN.md">🇺🇸 English</a> |
  <a href="README_ZH.md">🇨🇳 中文</a> |
  <a href="README_JP.md">🇯🇵 日本語</a> |
  <a href="README_ES.md">🇪🇸 Español</a> |
  <a href="README_DE.md">🇩🇪 Deutsch</a> |
  <a href="README_FR.md">🇫🇷 Français</a>
</p>

多言語対応 LLM独立型メモリ管理システム

## 📌 概要

**Greeum**（発音：グリウム）は、あらゆるLLM（大規模言語モデル）に接続できる**汎用メモリモジュール**で、以下の機能を提供します：
- ユーザーの発言、目標、感情、意図などの長期的な追跡
- 現在のコンテキストに関連するメモリの想起
- 多言語環境での時間表現の認識と処理
- 「記憶を持つAI」としての機能

「Greeum」という名前は韓国語の「그리움」（懐かしさ/思い出）からインスピレーションを受けており、メモリシステムの本質を完璧に捉えています。

GreuemはRAG（検索拡張生成、Retrieval-Augmented Generation）アーキテクチャに基づくLLM独立型メモリシステムです。情報の保存と検索（block_manager.py）、関連記憶の管理（cache_manager.py）、プロンプト拡張（prompt_wrapper.py）などRAGの主要コンポーネントを実装し、より正確で文脈に適した応答を生成します。

## 🔑 主な機能

- **ブロックチェーン風の長期記憶（LTM）**：不変性を持つブロックベースのメモリストレージ
- **TTLベースの短期記憶（STM）**：一時的に重要な情報の効率的な管理
- **意味的関連性**：キーワード/タグ/ベクトルベースのメモリ想起システム
- **ウェイポイントキャッシュ**：現在のコンテキストに関連するメモリの自動検索
- **プロンプトコンポーザー**：関連メモリを含むLLMプロンプトの自動生成
- **時間的推論機能**：多言語環境での高度な時間表現認識
- **多言語サポート**：韓国語、英語などの自動言語検出と処理
- **モデル制御プロトコル**：別パッケージの[GreeumMCP](https://github.com/DryRainEnt/GreeumMCP)を通じてCursor、Unity、Discordなどの外部ツールとの連携をサポート

## ⚙️ インストール

1. リポジトリをクローン
   ```bash
   git clone https://github.com/DryRainEnt/Greeum.git
   cd Greeum
   ```

2. 依存関係のインストール
   ```bash
   pip install -r requirements.txt
   ```

## 🧪 使用方法

### CLIインターフェース

```bash
# 長期記憶の追加
python cli/memory_cli.py add -c "新しいプロジェクトを始めて、とてもワクワクしています"

# キーワードでメモリを検索
python cli/memory_cli.py search -k "プロジェクト,ワクワク"

# 時間表現でメモリを検索
python cli/memory_cli.py search-time -q "3日前に何をしましたか？" -l "ja"

# 短期記憶の追加
python cli/memory_cli.py stm "今日は天気が良いです"

# 短期記憶の取得
python cli/memory_cli.py get-stm

# プロンプトの生成
python cli/memory_cli.py prompt -i "プロジェクトはどう進んでいますか？"
```

### REST APIサーバー

```bash
# APIサーバーの実行
python api/memory_api.py
```

Webインターフェース：http://localhost:5000

APIエンドポイント：
- GET `/api/v1/health` - ヘルスチェック
- GET `/api/v1/blocks` - ブロック一覧
- POST `/api/v1/blocks` - ブロック追加
- GET `/api/v1/search?keywords=keyword1,keyword2` - キーワード検索
- GET `/api/v1/search/time?query=yesterday&language=en` - 時間表現検索
- GET, POST, DELETE `/api/v1/stm` - 短期記憶管理
- POST `/api/v1/prompt` - プロンプト生成
- GET `/api/v1/verify` - ブロックチェーン整合性検証

### Pythonライブラリ

```python
from greeum import BlockManager, STMManager, CacheManager, PromptWrapper
from greeum.text_utils import process_user_input
from greeum.temporal_reasoner import TemporalReasoner

# ユーザー入力の処理
user_input = "新しいプロジェクトを始めて、とてもワクワクしています"
processed = process_user_input(user_input)

# ブロックマネージャーでメモリを保存
block_manager = BlockManager()
block = block_manager.add_block(
    context=processed["context"],
    keywords=processed["keywords"],
    tags=processed["tags"],
    embedding=processed["embedding"],
    importance=processed["importance"]
)

# 時間ベースの検索（多言語）
temporal_reasoner = TemporalReasoner(db_manager=block_manager, default_language="auto")
time_query = "3日前に何をしましたか？"
time_results = temporal_reasoner.search_by_time_reference(time_query)

# プロンプト生成
cache_manager = CacheManager(block_manager=block_manager)
prompt_wrapper = PromptWrapper(cache_manager=cache_manager)

user_question = "プロジェクトはどう進んでいますか？"
prompt = prompt_wrapper.compose_prompt(user_question)

# LLMに渡す
# llm_response = call_your_llm(prompt)
```

## 🧱 アーキテクチャ

```
greeum/
├── greeum/                # コアライブラリ
│   ├── block_manager.py    # 長期記憶管理
│   ├── stm_manager.py      # 短期記憶管理
│   ├── cache_manager.py    # ウェイポイントキャッシュ
│   ├── prompt_wrapper.py   # プロンプト構成
│   ├── text_utils.py       # テキスト処理ユーティリティ
│   ├── temporal_reasoner.py # 時間推論
│   ├── embedding_models.py  # 埋め込みモデル統合
├── api/                   # REST APIインターフェース
├── cli/                   # コマンドラインツール
├── data/                  # データ保存ディレクトリ
├── tests/                 # テストスイート
```

## ブランチ管理ルール

- **main**：安定リリースバージョンブランチ
- **dev**：コア機能開発ブランチ（開発・テスト後にmainにマージ）
- **test-collect**：パフォーマンス指標とA/Bテストデータ収集ブランチ

## 📊 パフォーマンステスト

Greumは以下の領域でパフォーマンステストを実施しています：

### T-GEN-001：応答の具体性向上率
- Greumメモリ使用時の応答品質向上の測定
- 平均18.6%の品質向上を確認
- 具体的情報の含有量が4.2増加

### T-MEM-002：メモリ検索のレイテンシ
- ウェイポイントキャッシュによる検索速度向上の測定
- 平均5.04倍の速度向上を確認
- 1,000以上のメモリブロックで最大8.67倍の速度向上

### T-API-001：API呼び出し効率
- メモリベースのコンテキスト提供による再質問減少率の測定
- 再質問の必要性が78.2%減少したことを確認
- API呼び出し回数減少によるコスト削減効果

## 📊 メモリブロック構造

```json
{
  "block_index": 143,
  "timestamp": "2025-05-08T01:02:33",
  "context": "新しいプロジェクトを始めて、とてもワクワクしています",
  "keywords": ["プロジェクト", "開始", "ワクワク"],
  "tags": ["ポジティブ", "開始", "モチベーション"],
  "embedding": [0.131, 0.847, ...],
  "importance": 0.91,
  "hash": "...",
  "prev_hash": "..."
}
```

## 🔤 サポートされている言語

Greumは以下の言語の時間表現認識をサポートしています：
- 🇰🇷 韓国語：韓国語の時間表現の基本サポート（어제, 지난주, 3일 전 など）
- 🇺🇸 英語：英語の時間形式の完全サポート（yesterday, 3 days ago など）
- 🇯🇵 日本語：日本語の時間表現のサポート（昨日、3日前 など）
- 🌐 自動検出：言語を自動的に検出して適切に処理

## 🔍 時間的推論の例

```python
# 韓国語
result = evaluate_temporal_query("3일 전에 뭐 했어?", language="ko")
# 戻り値：{detected: True, language: "ko", best_ref: {term: "3일 전"}}

# 英語
result = evaluate_temporal_query("What did I do 3 days ago?", language="en")
# 戻り値：{detected: True, language: "en", best_ref: {term: "3 days ago"}}

# 日本語
result = evaluate_temporal_query("3日前に何をしましたか？", language="ja")
# 戻り値：{detected: True, language: "ja", best_ref: {term: "3日前"}}

# 自動検出
result = evaluate_temporal_query("What happened yesterday?")
# 戻り値：{detected: True, language: "en", best_ref: {term: "yesterday"}}
```

## 🔧 プロジェクト拡張計画

- **モデル制御プロトコル**：MCP対応については[GreeumMCP](https://github.com/DryRainEnt/GreeumMCP)リポジトリをご確認ください - GreumをCursor、Unity、Discordなどのツールと接続できる別パッケージです
- **多言語サポートの強化**：日本語、中国語、スペイン語などの追加言語サポート
- **埋め込みの改善**：実際の埋め込みモデルの統合（例：sentence-transformers）
- **キーワード抽出の強化**：言語固有のキーワード抽出の実装
- **クラウド統合**：データベースバックエンドの追加（SQLite、MongoDBなど）
- **分散処理**：大規模メモリ管理のための分散処理の実装

## 🌐 ウェブサイト

ウェブサイト訪問：[greeum.app](https://greeum.app)

## 📄 ライセンス

MITライセンス

## 👥 貢献

バグレポート、機能提案、プルリクエストなど、あらゆる貢献を歓迎します！

## 📱 連絡先

メール：playtart@play-t.art 
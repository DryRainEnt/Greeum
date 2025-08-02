# 🧠 Greeum v2.0.5

<p align="center">
  <a href="../../README.md">🇰🇷 한국어</a> |
  <a href="README_EN.md">🇺🇸 English</a> |
  <a href="README_JP.md">🇯🇵 日本語</a> |
  <a href="README_ZH.md">🇨🇳 中文</a>
</p>

LLM向けインテリジェントメモリ管理システム

## 📌 概要

**Greeum**（発音：グリウム）は、あらゆるLLM（大規模言語モデル）に接続できる**汎用メモリモジュール**です：

- **長期記憶**: ユーザーコンテキスト、設定、目標の永続的保存
- **短期記憶**: セッションベースの重要情報管理
- **インテリジェント検索**: コンテキストベースの自動メモリ呼び出し
- **品質管理**: 自動メモリ品質検証と最適化
- **多言語サポート**: 韓国語、英語、日本語、中国語の完全サポート

「Greeum」という名前は韓国語の「그리움」（憧憬・郷愁）からインスピレーションを得ており、AIが過去を記憶し憧憬する能力を象徴しています。

## 🚀 クイックスタート

### インストール

```bash
# pipxでインストール（推奨）
pipx install greeum

# またはpipでインストール
pip install greeum
```

### 基本的な使用方法

```bash
# メモリ追加
python3 -m greeum.cli memory add "今日新しいプロジェクトを開始しました。Pythonでウェブアプリケーションを開発する予定です。"

# メモリ検索
python3 -m greeum.cli memory search "プロジェクト Python" --limit 5

# 長期記憶分析
python3 -m greeum.cli ltm analyze --period 30d --trends

# 短期記憶追加
python3 -m greeum.cli stm add "一時メモ" --ttl 1h

# MCPサーバー実行
python3 -m greeum.mcp.claude_code_mcp_server
```

## 🔑 主要機能

### 📚 多層メモリシステム
- **LTM（長期記憶）**: ブロックチェーン様構造による永続的保存
- **STM（短期記憶）**: TTLベースの一時メモリ管理
- **ウェイポイントキャッシュ**: コンテキスト関連メモリの自動ロード

### 🧠 インテリジェントメモリ管理
- **品質検証**: 7つの指標に基づく自動品質評価
- **重複検出**: 85％類似度基準での重複防止
- **使用分析**: パターン分析と最適化推奨
- **自動クリーンアップ**: 品質ベースのメモリクリーンアップ

### 🔍 高度な検索
- **キーワード検索**: タグとキーワードベースの検索
- **ベクトル検索**: 意味的類似度検索
- **時間検索**: 「3日前」「先週」などの自然言語時間表現
- **ハイブリッド検索**: キーワード + ベクトル + 時間の組み合わせ

### 🌐 MCP統合
- **Claude Code**: 12のMCPツールとの完全統合
- **リアルタイム同期**: メモリ作成・検索のリアルタイム反映
- **品質検証**: 自動品質チェックとフィードバック

## 🛠️ 高度な使用方法

### API使用
```python
from greeum import BlockManager, STMManager, PromptWrapper

# メモリシステム初期化
bm = BlockManager()
stm = STMManager()
pw = PromptWrapper()

# メモリ追加
bm.add_block(
    context="重要な会議内容",
    keywords=["会議", "決定事項"],
    importance=0.9
)

# コンテキストベースプロンプト生成
enhanced_prompt = pw.compose_prompt("前回の会議で何を決めましたか？")
```

### MCPツール（Claude Code用）
```
利用可能なツール:
- add_memory: 新しいメモリの追加
- search_memory: メモリ検索
- get_memory_stats: メモリ統計
- ltm_analyze: 長期記憶分析
- stm_add: 短期記憶追加
- quality_check: 品質検証
- check_duplicates: 重複チェック
- usage_analytics: 使用分析
- ltm_verify: 整合性検証
- ltm_export: データエクスポート
- stm_promote: STM→LTM昇格
- stm_cleanup: STMクリーンアップ
```

## 📊 メモリ品質管理

Greeum v2.0.5はインテリジェント品質管理システムを提供します：

### 品質評価指標
1. **長さ**: 適切な情報量
2. **豊富さ**: 意味のある単語の比率
3. **構造**: 文・段落構成
4. **言語**: 文法と表現品質
5. **情報密度**: 具体的情報の含有度
6. **検索性**: 将来の検索の利便性
7. **時間的関連性**: 現在のコンテキストとの関連性

### 自動最適化
- **品質ベースの重要度調整**
- **重複メモリの自動検出**
- **STM→LTM昇格提案**
- **使用パターンベースの推奨事項**

## 🔗 統合ガイド

### Claude Code MCP設定
1. **インストール確認**
   ```bash
   greeum --version  # v2.0.5以上
   ```

2. **Claude Desktop設定**
   ```json
   {
     "mcpServers": {
       "greeum": {
         "command": "python3",
         "args": ["-m", "greeum.mcp.claude_code_mcp_server"],
         "env": {
           "GREEUM_DATA_DIR": "/path/to/data"
         }
       }
     }
   }
   ```

3. **接続確認**
   ```bash
   claude mcp list  # greeumサーバー確認
   ```

### その他のLLM統合
```python
# OpenAI GPT
from greeum.client import MemoryClient
client = MemoryClient(llm_type="openai")

# ローカルLLM
client = MemoryClient(llm_type="local", endpoint="http://localhost:8080")
```

## 📈 パフォーマンス・ベンチマーク

- **応答品質**: 平均18.6%向上（ベンチマーク基準）
- **検索速度**: 5.04倍向上（ウェイポイントキャッシュ適用）
- **再質問削減**: 78.2%削減（コンテキスト理解度向上）
- **メモリ効率**: メモリ使用量50%最適化

## 📚 ドキュメント・リソース

- **[スタートガイド](../get-started.md)**: 詳細なインストールと設定ガイド
- **[APIリファレンス](../api-reference.md)**: 完全なAPIリファレンス
- **[チュートリアル](../tutorials.md)**: ステップバイステップの使用例
- **[開発者ガイド](../developer_guide.md)**: 貢献方法

## 🤝 貢献

Greeumはオープンソースプロジェクトです。貢献を歓迎します！

### 貢献方法
1. **イシューレポート**: バグや問題を発見した場合
2. **機能提案**: 新しいアイデアや改善案
3. **コード貢献**: プルリクエスト歓迎
4. **ドキュメント**: 翻訳と改善

### 開発環境構築
```bash
# ソースコードダウンロード後
pip install -e .[dev]
tox  # テスト実行
```

## 📞 サポート・連絡先

- **📧 公式メール**: playtart@play-t.art
- **🌐 公式ウェブサイト**: [greeum.app](https://greeum.app)
- **📚 ドキュメント**: このREADMEとdocs/フォルダを参照

## 📄 ライセンス

このプロジェクトはMITライセンスの下で配布されています。詳細は[LICENSE](../../LICENSE)ファイルを参照してください。

## 🏆 謝辞

- **OpenAI**: 埋め込みAPIサポート
- **Anthropic**: Claude MCPプラットフォーム
- **NumPy**: 効率的なベクトル計算
- **SQLite**: 信頼性の高いデータストレージ

---

<p align="center">
  Made with ❤️ by the Greeum Team<br>
  <em>「記憶を通してAIをより人間的に」</em>
</p>
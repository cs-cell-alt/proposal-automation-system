# 営業一次提案 AI 自動化システム

営業の一次提案プロセス（リサーチ→立案→評価→コンプライアンス→スライド生成）を自動化するマルチエージェントシステムのデモアプリ。

## 機能

- **Pattern C アーキテクチャ**: Orchestrator → Research (×4) → Planning → Evaluator → Compliance → Output
- **モックアップデモ**: 各エージェントの動作をシミュレート
- **Google Slides 自動生成**: 提案スライド（6枚）を自動作成
- **SmartNews デザインシステム**: Precision Dark テーマ（Syne + Manrope + IBM Plex Mono）

## 開発環境での実行

```bash
# 依存関係のインストール
pip install -r requirements.txt

# サービスアカウントキーを配置
# service-account-key.json を同じディレクトリに配置

# 実行
streamlit run app.py
```

## Streamlit Cloud へのデプロイ

1. GitHubリポジトリにプッシュ
2. [Streamlit Cloud](https://streamlit.io/cloud) でアプリを作成
3. Secrets に `service_account_base64` を設定（後述）

### サービスアカウントキーのBase64エンコード

```bash
base64 -i service-account-key.json | pbcopy
```

クリップボードの内容を Streamlit Cloud の Secrets に以下の形式で追加:

```toml
service_account_base64 = "ここにbase64エンコードされた文字列を貼り付け"
```

## アーキテクチャ

```
顧客情報入力
    ↓
Orchestrator Agent
    ↓
Research Phase（並列実行）
  - Web検索 Agent
  - 社内KB RAG Agent
  - 事例DB Agent
  - 市場情報 Agent
    ↓
Planning Agent
    ↓
Evaluator Agent（品質スコアリング）
    ↓ (スコア < 90 なら Planning に戻る)
    ↓
Compliance Agent
    ↓
Output Agent
  - Google Slides生成
  - セールストーク生成
  - 顧客確認事項リスト
```

## 技術スタック

- **Python 3.9+**
- **Streamlit**: Web UI
- **Google Slides API**: スライド自動生成
- **Google Drive API**: 共有設定

## ライセンス

Internal use only - SmartNews Inc.

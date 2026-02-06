# D6E Legal Docker STF Suite

法務業務を D6E ワークフローで実行するための Docker STF スイートです。

[Anthropic Knowledge Work Plugins - Legal](https://github.com/anthropics/knowledge-work-plugins/tree/main/legal) のスキルをベースに、D6E プラットフォームから呼び出し可能な Docker STF として実装しています。

## Docker Images

| STF | Docker Image | 説明 |
| --- | --- | --- |
| NDA Triage | ghcr.io/d6e-ai/stf-nda-triage:latest | NDA スクリーニング・GREEN/YELLOW/RED 分類 |
| Contract Review | ghcr.io/d6e-ai/stf-contract-review:latest | 契約書レビュー・逸脱検出・レッドライン生成 |
| Legal Risk Assessment | ghcr.io/d6e-ai/stf-legal-risk-assessment:latest | リスク評価（重大度×可能性マトリクス） |
| Compliance | ghcr.io/d6e-ai/stf-compliance:latest | プライバシー規制対応・DPA レビュー・DSR 処理 |
| Canned Responses | ghcr.io/d6e-ai/stf-canned-responses:latest | 法的問い合わせテンプレート応答生成 |
| Meeting Briefing | ghcr.io/d6e-ai/stf-meeting-briefing:latest | 会議ブリーフィング・アクションアイテム追跡 |

## クイックスタート（LLM/AI エージェント向け）

### ステップ 1: STF の作成

```javascript
d6e_create_stf({
  name: "nda-triage",
  description: "Screen incoming NDAs and classify risk level",
});
```

### ステップ 2: STF バージョンの作成

```javascript
d6e_create_stf_version({
  stf_id: "{ステップ1で取得したstf_id}",
  version: "1.0.0",
  runtime: "docker",
  code: '{"image":"ghcr.io/d6e-ai/stf-nda-triage:latest"}',
});
```

**重要**: `runtime`は必ず`"docker"`を指定し、`code`フィールドには JSON 文字列として Docker イメージを設定してください。

### ステップ 3: ワークフローの作成

```javascript
d6e_create_workflow({
  name: "legal-workflow",
  input_steps: [],
  stf_steps: [
    {
      stf_id: "{stf_id}",
      version: "1.0.0",
    },
  ],
  effect_steps: [],
});
```

### ステップ 4: ワークフローの実行

```javascript
d6e_execute_workflow({
  workflow_id: "{workflow_id}",
  input: {
    operation: "generate_checklist",
    nda_type: "mutual",
  },
});
```

## 🤖 AI エージェントへのプロンプト

### NDA をトリアージする（データベース不要）

```
NDAのトリアージを行ってください。

Docker Image: ghcr.io/d6e-ai/stf-nda-triage:latest
操作: triage_nda
パラメータ:
  nda_data:
    nda_type: "mutual"
    counterparty: "Acme Corp"
    carveouts_present: ["public_knowledge", "prior_possession", "third_party_receipt"]
    term_years: 2
    survival_years: 3
    governing_law: "Delaware"
    problematic_provisions: []

手順:
1. STF作成（runtime: "docker"）
2. ワークフロー実行
```

### 契約書のリスクレベルを評価する（データベース不要）

```
契約書の条項を分析してリスクレベルを評価してください。

Docker Image: ghcr.io/d6e-ai/stf-contract-review:latest
操作: review_contract
パラメータ:
  contract_data:
    contract_type: "SaaS"
    our_side: "customer"
    counterparty: "Vendor Corp"
    clauses:
      limitation_of_liability:
        cap_type: "fixed"
        cap_months_of_fees: 6
        is_mutual: false
        has_consequential_exclusion: true
      data_protection:
        processes_personal_data: true
        has_dpa: false
```

### リスク評価マトリクスを生成する（データベース不要）

```
法的リスク評価マトリクスを生成してください。

Docker Image: ghcr.io/d6e-ai/stf-legal-risk-assessment:latest
操作: generate_risk_matrix

このOperationはパラメータ不要で動作します。
```

### DPA レビューチェックリストを生成する（データベース不要）

```
DPAレビュー用のチェックリストを生成してください。

Docker Image: ghcr.io/d6e-ai/stf-compliance:latest
操作: generate_dpa_checklist
パラメータ: include_transfers: true
```

### テンプレート応答を生成する（データベース不要）

```
データ主体リクエストの受領確認メールを生成してください。

Docker Image: ghcr.io/d6e-ai/stf-canned-responses:latest
操作: generate_response
パラメータ:
  category: "dsr"
  sub_category: "acknowledgment"
  variables:
    requester_name: "John Doe"
    request_date: "2025-01-15"
    request_type: "access"
    regulation: "GDPR"
    response_deadline: "2025-02-14"
    request_id: "DSR-2025-001"
    contact_email: "privacy@company.com"
    sender_name: "Privacy Team"
    sender_title: "Data Protection Officer"
```

### 会議のブリーフィングを準備する（データベース不要）

```
契約交渉の会議ブリーフィングを生成してください。

Docker Image: ghcr.io/d6e-ai/stf-meeting-briefing:latest
操作: get_meeting_prep_checklist
パラメータ: meeting_type: "deal_review"
```

## プロジェクト構造

```
d6e-docker-stf-legal/
├── shared/                          # 共通ユーティリティ
│   └── utils.py                     # D6E API クライアント、入出力処理
├── stf-nda-triage/                  # NDAトリアージSTF
│   ├── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
├── stf-contract-review/             # 契約書レビューSTF
│   ├── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
├── stf-legal-risk-assessment/       # リスク評価STF
│   ├── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
├── stf-compliance/                  # コンプライアンスSTF
│   ├── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
├── stf-canned-responses/            # テンプレート応答STF
│   ├── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
├── stf-meeting-briefing/            # 会議ブリーフィングSTF
│   ├── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
├── docs/
│   └── OPERATIONS.md                # 全操作一覧
├── scripts/
│   └── build-all.sh                 # 一括ビルドスクリプト
└── .github/workflows/
    └── docker-publish.yml           # CI/CD（ghcr.io公開）
```

## 各 STF の操作一覧

### stf-nda-triage

| 操作 | 必須パラメータ | DB 必要 | 説明 |
| --- | --- | --- | --- |
| `triage_nda` | `nda_data` | ❌ | NDA 完全トリアージ |
| `check_clause` | `clause_type`, `clause_data` | ❌ | 個別条項チェック |
| `get_routing_recommendation` | `classification` | ❌ | ルーティング推奨 |
| `generate_checklist` | - | ❌ | スクリーニングチェックリスト生成 |

### stf-contract-review

| 操作 | 必須パラメータ | DB 必要 | 説明 |
| --- | --- | --- | --- |
| `review_contract` | `contract_data` | ❌ | 契約書フルレビュー |
| `analyze_clause` | `clause_type`, `clause_details` | ❌ | 個別条項分析 |
| `generate_redline` | `clause_type`, `current_language`, `issue_description` | ❌ | レッドライン生成 |
| `classify_deviation` | `clause_type`, `deviation_type` | ❌ | 逸脱分類 |
| `generate_review_summary` | `deviations`, `contract_data` | ❌ | レビューサマリー生成 |

### stf-legal-risk-assessment

| 操作 | 必須パラメータ | DB 必要 | 説明 |
| --- | --- | --- | --- |
| `assess_risk` | `risk_data` | ❌ | リスク評価 |
| `calculate_risk_score` | `severity`, `likelihood` | ❌ | リスクスコア計算 |
| `generate_risk_memo` | `assessment_data` | ❌ | リスクメモ生成 |
| `create_risk_register_entry` | `risk_data` | ❌ | リスクレジスタ登録 |
| `get_escalation_recommendation` | `risk_level` | ❌ | エスカレーション推奨 |
| `generate_risk_matrix` | - | ❌ | リスクマトリクス生成 |

### stf-compliance

| 操作 | 必須パラメータ | DB 必要 | 説明 |
| --- | --- | --- | --- |
| `review_dpa` | `dpa_data` | ❌ | DPA レビュー |
| `process_dsr` | `dsr_data` | ❌ | DSR 処理 |
| `get_response_timeline` | `regulation`, `date_received` | ❌ | 応答期限計算 |
| `check_exemptions` | `dsr_data` | ❌ | 適用除外チェック |
| `generate_dpa_checklist` | - | ❌ | DPA チェックリスト生成 |
| `get_regulation_overview` | `regulation` | ❌ | 規制概要取得 |

### stf-canned-responses

| 操作 | 必須パラメータ | DB 必要 | 説明 |
| --- | --- | --- | --- |
| `generate_response` | `category`, `sub_category`, `variables` | ❌ | テンプレート応答生成 |
| `check_escalation` | `category`, `triggers` | ❌ | エスカレーション判定 |
| `list_templates` | - | ❌ | テンプレート一覧 |
| `create_template` | `template_data` | ❌ | テンプレート作成 |
| `customize_response` | `response_body`, `customizations` | ❌ | 応答カスタマイズ |

### stf-meeting-briefing

| 操作 | 必須パラメータ | DB 必要 | 説明 |
| --- | --- | --- | --- |
| `generate_briefing` | `meeting_data` | ❌ | ブリーフィング生成 |
| `create_action_items` | `action_data` | ❌ | アクションアイテム作成 |
| `get_meeting_prep_checklist` | `meeting_type` | ❌ | 準備チェックリスト取得 |
| `track_action_items` | `tracking_data` | ❌ | アクションアイテム追跡 |
| `generate_follow_up` | `follow_up_data` | ❌ | フォローアップ生成 |

## ローカルでのビルド

```bash
# 全STFを一括ビルド
./scripts/build-all.sh

# 個別ビルド
cp -r shared stf-nda-triage/shared
cd stf-nda-triage
docker build -t stf-nda-triage:latest .
```

## テスト

```bash
# NDAチェックリスト生成（データベース不要）
echo '{
  "workspace_id": "test-ws",
  "stf_id": "test-stf",
  "caller": null,
  "api_url": "http://localhost:8080",
  "api_token": "test-token",
  "input": {
    "operation": "generate_checklist",
    "nda_type": "mutual"
  },
  "sources": {}
}' | docker run --rm -i stf-nda-triage:latest

# リスクスコア計算（データベース不要）
echo '{
  "workspace_id": "test-ws",
  "stf_id": "test-stf",
  "caller": null,
  "api_url": "http://localhost:8080",
  "api_token": "test-token",
  "input": {
    "operation": "calculate_risk_score",
    "severity": 4,
    "likelihood": 3
  },
  "sources": {}
}' | docker run --rm -i stf-legal-risk-assessment:latest

# DPAチェックリスト生成（データベース不要）
echo '{
  "workspace_id": "test-ws",
  "stf_id": "test-stf",
  "caller": null,
  "api_url": "http://localhost:8080",
  "api_token": "test-token",
  "input": {
    "operation": "generate_dpa_checklist"
  },
  "sources": {}
}' | docker run --rm -i stf-compliance:latest
```

## ドキュメント

- [全操作一覧](docs/OPERATIONS.md)
- [stf-nda-triage README](stf-nda-triage/README.md)
- [stf-contract-review README](stf-contract-review/README.md)
- [stf-legal-risk-assessment README](stf-legal-risk-assessment/README.md)
- [stf-compliance README](stf-compliance/README.md)
- [stf-canned-responses README](stf-canned-responses/README.md)
- [stf-meeting-briefing README](stf-meeting-briefing/README.md)

## トラブルシューティング

### Docker イメージが見つからない

```bash
docker pull ghcr.io/d6e-ai/stf-nda-triage:latest
```

### Unknown operation エラー

```
Error: Unknown operation: xxx. Valid operations: ...
```

各 STF のサポートする操作名を確認してください。

## 関連プロジェクト

- [d6e-docker-stf-finance](https://github.com/d6e-ai/d6e-docker-stf-finance) - 財務・経理STFスイート
- [Anthropic Knowledge Work Plugins - Legal](https://github.com/anthropics/knowledge-work-plugins/tree/main/legal) - 元となるスキル定義

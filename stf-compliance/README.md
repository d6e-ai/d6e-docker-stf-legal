# D6E Compliance STF

プライバシー規制対応・DPAレビュー・DSR処理を行う Docker STF です。

**Docker Image**: `ghcr.io/d6e-ai/stf-compliance:latest`

## LLM/AI エージェント向け使用方法

この Docker イメージを D6E AI エージェントから使用する場合、以下の手順で STF を作成してください。

### ステップ 1: STF の作成

```javascript
d6e_create_stf({
  name: "compliance",
  description:
    "Handle privacy compliance tasks including DPA reviews and DSR processing",
});
```

### ステップ 2: STF バージョンの作成

```javascript
d6e_create_stf_version({
  stf_id: "{ステップ1で取得したstf_id}",
  version: "1.0.0",
  runtime: "docker",
  code: '{"image":"ghcr.io/d6e-ai/stf-compliance:latest"}',
});
```

**重要**: `runtime`は必ず`"docker"`を指定し、`code`フィールドには JSON 文字列として`{"image":"ghcr.io/d6e-ai/stf-compliance:latest"}`を設定してください。

### ステップ 3: ワークフローの作成

```javascript
d6e_create_workflow({
  name: "compliance-workflow",
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
// DPAチェックリスト生成（データベース不要）
d6e_execute_workflow({
  workflow_id: "{workflow_id}",
  input: {
    operation: "generate_dpa_checklist",
  },
});

// 規制概要取得（データベース不要）
d6e_execute_workflow({
  workflow_id: "{workflow_id}",
  input: {
    operation: "get_regulation_overview",
    regulation: "GDPR",
  },
});

// DSRタイムライン計算（データベース不要）
d6e_execute_workflow({
  workflow_id: "{workflow_id}",
  input: {
    operation: "get_response_timeline",
    regulation: "GDPR",
    date_received: "2025-01-15",
  },
});

// DSR処理（データベース不要）
d6e_execute_workflow({
  workflow_id: "{workflow_id}",
  input: {
    operation: "process_dsr",
    dsr_data: {
      request_type: "access",
      regulation: "GDPR",
      requester_name: "John Doe",
      date_received: "2025-01-15",
      identity_verified: true,
    },
  },
});
```

## サポートされている操作

| Operation                | 必須パラメータ               | オプション              | DB 必要 | 説明                     |
| ------------------------ | ---------------------------- | ----------------------- | ------- | ------------------------ |
| `review_dpa`             | `dpa_data`                   | -                       | ❌      | DPAコンプライアンスレビュー |
| `process_dsr`            | `dsr_data`                   | -                       | ❌      | データ主体リクエスト処理 |
| `get_response_timeline`  | `regulation`, `date_received`| -                       | ❌      | 回答期限タイムライン計算 |
| `check_exemptions`       | `dsr_data`                   | -                       | ❌      | DSR免除事由チェック      |
| `generate_dpa_checklist` | -                            | `include_transfers`     | ❌      | DPAレビューチェックリスト生成 |
| `get_regulation_overview`| `regulation`                 | -                       | ❌      | 規制概要取得             |

## 入出力例

### DPAチェックリスト生成（データベース不要）

**入力**:

```json
{
  "operation": "generate_dpa_checklist"
}
```

**出力**:

```json
{
  "output": {
    "status": "success",
    "operation": "generate_dpa_checklist",
    "data": {
      "generated_at": "2025-01-15T10:00:00Z",
      "sections": [
        {
          "name": "Required Elements (GDPR Article 28)",
          "items": [
            {"check": "Subject Matter And Duration", "status": "pending", "key": "subject_matter_and_duration"},
            {"check": "Nature And Purpose", "status": "pending", "key": "nature_and_purpose"},
            {"check": "Type Of Personal Data", "status": "pending", "key": "type_of_personal_data"},
            {"check": "Categories Of Data Subjects", "status": "pending", "key": "categories_of_data_subjects"},
            {"check": "Controller Obligations And Rights", "status": "pending", "key": "controller_obligations_and_rights"}
          ]
        },
        {
          "name": "Processor Obligations",
          "items": [
            {"check": "Process On Instructions Only", "status": "pending", "key": "process_on_instructions_only"},
            {"check": "Confidentiality Commitment", "status": "pending", "key": "confidentiality_commitment"},
            {"check": "Security Measures", "status": "pending", "key": "security_measures"},
            {"check": "Breach Notification", "status": "pending", "key": "breach_notification"}
          ]
        },
        {
          "name": "International Transfers",
          "items": [
            {"check": "Transfer mechanism identified", "status": "pending"},
            {"check": "SCCs version current (June 2021)", "status": "pending"},
            {"check": "Transfer impact assessment completed", "status": "pending"}
          ]
        }
      ]
    }
  }
}
```

### 回答期限タイムライン計算（データベース不要）

**入力**:

```json
{
  "operation": "get_response_timeline",
  "regulation": "GDPR",
  "date_received": "2025-01-15"
}
```

**出力**:

```json
{
  "output": {
    "status": "success",
    "operation": "get_response_timeline",
    "data": {
      "regulation": "GDPR",
      "date_received": "2025-01-15",
      "response_deadline": "2025-02-14",
      "extended_deadline": "2025-04-15",
      "extension_available": true,
      "timeline_rules": {
        "initial_acknowledgment": "Best practice: promptly",
        "substantive_response_days": 30,
        "extension_days": 60,
        "extension_notice_required": true
      }
    }
  }
}
```

## 🤖 AI エージェントへのプロンプト

### 基本プロンプト（データベース不要）

```
D6Eでプライバシーコンプライアンスを行うDockerスキルを使用してください。

Docker Image: ghcr.io/d6e-ai/stf-compliance:latest

使用手順:
1. d6e_create_stf でSTFを作成（name: "compliance"）
2. d6e_create_stf_version で以下を指定:
   - runtime: "docker"
   - code: "{\"image\":\"ghcr.io/d6e-ai/stf-compliance:latest\"}"
3. d6e_create_workflow でワークフローを作成
4. d6e_execute_workflow で実行

データベース不要の操作:
- "review_dpa": DPAレビュー（dpa_data必須）
- "process_dsr": DSR処理（dsr_data必須）
- "get_response_timeline": 回答期限計算（regulation, date_received必須）
- "check_exemptions": DSR免除事由チェック（dsr_data必須）
- "generate_dpa_checklist": DPAチェックリスト生成（include_transfersオプション）
- "get_regulation_overview": 規制概要取得（regulation必須）

まずはDPAチェックリスト生成で動作確認してください。
```

### DSR処理を実行するプロンプト

```
GDPRに基づくデータアクセスリクエストを処理してください。

使用スキル:
- Docker Image: ghcr.io/d6e-ai/stf-compliance:latest
- 操作: process_dsr

パラメータ:
- dsr_data:
  - request_type: "access"
  - regulation: "GDPR"
  - requester_name: "田中太郎"
  - date_received: "2025-01-15"
  - identity_verified: true
  - subject_to_litigation_hold: false

結果には以下を含めてください:
- 回答期限
- 処理ステップ
- 適用される免除事由
- エスカレーションが必要かどうか
```

## 対応規制

| 規制    | 管轄           | 初回回答期限 | 延長可能 |
| ------- | -------------- | ------------ | -------- |
| GDPR    | EU/EEA         | 30日         | +60日    |
| CCPA    | カリフォルニア | 45日         | +45日    |
| UK_GDPR | 英国           | 30日         | +60日    |
| LGPD    | ブラジル       | 15日         | 不可     |

## トラブルシューティング

### DPAレビューで non_compliant が返された

`review_dpa` の結果の `findings` で `severity: "red"` の項目を確認してください。GDPR第28条の必須要素が欠けている場合は、ベンダーにDPAの修正を依頼してください。

### DSRにエスカレーションが必要な場合

`process_dsr` の結果で `has_escalation_triggers: true` の場合、`escalation_triggers` に記載されたトリガー（未成年、訴訟保留中のデータ等）を確認し、適切なカウンセルへ報告してください。

## ローカルでのビルドとテスト

```bash
# ビルド
docker build -t stf-compliance:latest .

# テスト（データベース不要）
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

## 関連ドキュメント

- [操作一覧](../docs/OPERATIONS.md)
- [プロジェクト README](../README.md)

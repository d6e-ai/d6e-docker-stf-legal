# D6E Canned Responses STF

法的問い合わせへのテンプレート応答生成・管理を行う Docker STF です。

**Docker Image**: `ghcr.io/d6e-ai/stf-canned-responses:latest`

## LLM/AI エージェント向け使用方法

この Docker イメージを D6E AI エージェントから使用する場合、以下の手順で STF を作成してください。

### ステップ 1: STF の作成

```javascript
d6e_create_stf({
  name: "canned-responses",
  description:
    "Generate and manage templated responses for common legal inquiries",
});
```

### ステップ 2: STF バージョンの作成

```javascript
d6e_create_stf_version({
  stf_id: "{ステップ1で取得したstf_id}",
  version: "1.0.0",
  runtime: "docker",
  code: '{"image":"ghcr.io/d6e-ai/stf-canned-responses:latest"}',
});
```

**重要**: `runtime`は必ず`"docker"`を指定し、`code`フィールドには JSON 文字列として`{"image":"ghcr.io/d6e-ai/stf-canned-responses:latest"}`を設定してください。

### ステップ 3: ワークフローの作成

```javascript
d6e_create_workflow({
  name: "canned-responses-workflow",
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
// テンプレート一覧取得（データベース不要）
d6e_execute_workflow({
  workflow_id: "{workflow_id}",
  input: {
    operation: "list_templates",
  },
});

// エスカレーションチェック（データベース不要）
d6e_execute_workflow({
  workflow_id: "{workflow_id}",
  input: {
    operation: "check_escalation",
    category: "dsr",
    triggers: ["involves_minor", "special_category_data"],
  },
});

// テンプレート応答生成（データベース不要）
d6e_execute_workflow({
  workflow_id: "{workflow_id}",
  input: {
    operation: "generate_response",
    category: "dsr",
    sub_category: "acknowledgment",
    variables: {
      requester_name: "John Doe",
      request_date: "2025-01-15",
      request_type: "access",
      regulation: "GDPR",
      response_deadline: "2025-02-14",
      request_id: "DSR-2025-001",
      contact_email: "privacy@company.com",
      sender_name: "Legal Team",
      sender_title: "Privacy Office",
    },
  },
});
```

## サポートされている操作

| Operation            | 必須パラメータ                            | オプション       | DB 必要 | 説明                         |
| -------------------- | ----------------------------------------- | ---------------- | ------- | ---------------------------- |
| `generate_response`  | `category`, `sub_category`, `variables`   | `tone`           | ❌      | テンプレート応答生成         |
| `check_escalation`   | `category`, `triggers`                    | -                | ❌      | エスカレーショントリガーチェック |
| `list_templates`     | -                                         | `category`       | ❌      | 利用可能テンプレート一覧     |
| `create_template`    | `template_data`                           | -                | ❌      | 新規テンプレート作成         |
| `customize_response` | `response_body`, `customizations`         | -                | ❌      | 応答のカスタマイズ           |

## 入出力例

### テンプレート一覧取得（データベース不要）

**入力**:

```json
{
  "operation": "list_templates"
}
```

**出力**:

```json
{
  "output": {
    "status": "success",
    "operation": "list_templates",
    "data": {
      "categories": [
        {
          "category": "dsr",
          "sub_categories": ["acknowledgment", "identity_verification", "fulfillment"],
          "template_count": 3,
          "escalation_triggers": [
            "involves_minor",
            "data_under_litigation_hold",
            "requester_in_active_litigation",
            "employee_with_hr_matter",
            "overbroad_scope",
            "special_category_data"
          ]
        },
        {
          "category": "discovery_hold",
          "sub_categories": ["initial_notice", "reminder", "release"],
          "template_count": 3,
          "escalation_triggers": [
            "potential_criminal_liability",
            "unclear_preservation_scope",
            "conflicts_with_deletion_requirements"
          ]
        },
        {
          "category": "nda_request",
          "sub_categories": ["send_standard_form"],
          "template_count": 1,
          "escalation_triggers": []
        },
        {
          "category": "subpoena",
          "sub_categories": ["acknowledgment"],
          "template_count": 1,
          "escalation_triggers": ["always_requires_counsel_review"]
        }
      ],
      "universal_escalation_triggers": [
        "potential_litigation_or_investigation",
        "from_regulator_or_government",
        "creates_binding_commitment",
        "potential_criminal_liability",
        "media_attention",
        "unprecedented_situation",
        "conflicting_jurisdictions",
        "involves_executive_or_board"
      ]
    }
  }
}
```

### エスカレーションチェック（データベース不要）

**入力**:

```json
{
  "operation": "check_escalation",
  "category": "dsr",
  "triggers": ["involves_minor"]
}
```

**出力**:

```json
{
  "output": {
    "status": "success",
    "operation": "check_escalation",
    "data": {
      "category": "dsr",
      "should_escalate": true,
      "triggered_by": ["involves_minor"],
      "universal_triggers": [],
      "category_triggers": ["involves_minor"],
      "recommendation": {
        "action": "STOP - Do not generate templated response",
        "reason": "Escalation trigger(s) detected: involves_minor",
        "escalation_path": "Escalate to senior counsel for review and guidance",
        "alternative": "Prepare DRAFT for counsel review (clearly marked as draft)"
      }
    }
  }
}
```

## 🤖 AI エージェントへのプロンプト

### 基本プロンプト（データベース不要）

```
D6Eで法的テンプレート応答を管理するDockerスキルを使用してください。

Docker Image: ghcr.io/d6e-ai/stf-canned-responses:latest

使用手順:
1. d6e_create_stf でSTFを作成（name: "canned-responses"）
2. d6e_create_stf_version で以下を指定:
   - runtime: "docker"
   - code: "{\"image\":\"ghcr.io/d6e-ai/stf-canned-responses:latest\"}"
3. d6e_create_workflow でワークフローを作成
4. d6e_execute_workflow で実行

データベース不要の操作:
- "generate_response": テンプレート応答生成（category, sub_category, variables必須）
- "check_escalation": エスカレーションチェック（category, triggers必須）
- "list_templates": テンプレート一覧取得（categoryオプション）
- "create_template": 新規テンプレート作成（template_data必須）
- "customize_response": 応答のカスタマイズ（response_body, customizations必須）

まずはテンプレート一覧取得で動作確認してください。
```

### DSR応答を生成するプロンプト

```
データアクセスリクエストの受領確認メールを生成してください。

使用スキル:
- Docker Image: ghcr.io/d6e-ai/stf-canned-responses:latest
- 操作: generate_response

パラメータ:
- category: "dsr"
- sub_category: "acknowledgment"
- variables:
  - requester_name: "田中太郎"
  - request_date: "2025-01-15"
  - request_type: "access"
  - regulation: "GDPR"
  - response_deadline: "2025-02-14"
  - request_id: "DSR-2025-001"
  - contact_email: "privacy@company.com"
  - sender_name: "法務チーム"
  - sender_title: "プライバシーオフィス"

応答を生成する前に、まず check_escalation でエスカレーションが必要かチェックしてください。
```

## テンプレートカテゴリ

| カテゴリ                 | 説明                           | サブカテゴリ                                |
| ------------------------ | ------------------------------ | ------------------------------------------- |
| `dsr`                    | データ主体リクエスト           | acknowledgment, identity_verification, fulfillment |
| `discovery_hold`         | 訴訟保留通知                   | initial_notice, reminder, release           |
| `nda_request`            | NDA送付                        | send_standard_form                          |
| `privacy_inquiry`        | プライバシー問い合わせ         | general_response                            |
| `vendor_legal`           | ベンダー法務問い合わせ         | contract_status                             |
| `subpoena`               | 召喚状対応                     | acknowledgment                              |
| `insurance_notification` | 保険請求通知                   | initial_claim                               |

## トラブルシューティング

### テンプレート応答に未置換のプレースホルダーが残っている

`generate_response` の `variables` に必要な変数が不足しています。テンプレートの `required_variables` を `list_templates` で確認し、すべての必須変数を提供してください。

### 常にエスカレーションが必要なカテゴリ

`subpoena`（召喚状）カテゴリは常にカウンセルレビューが必要です。テンプレート応答はあくまでドラフトであり、必ず法務担当者のレビューを経てから送付してください。

## ローカルでのビルドとテスト

```bash
# ビルド
docker build -t stf-canned-responses:latest .

# テスト（データベース不要）
echo '{
  "workspace_id": "test-ws",
  "stf_id": "test-stf",
  "caller": null,
  "api_url": "http://localhost:8080",
  "api_token": "test-token",
  "input": {
    "operation": "list_templates"
  },
  "sources": {}
}' | docker run --rm -i stf-canned-responses:latest
```

## 関連ドキュメント

- [操作一覧](../docs/OPERATIONS.md)
- [プロジェクト README](../README.md)

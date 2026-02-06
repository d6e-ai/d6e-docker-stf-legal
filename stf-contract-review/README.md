# D6E Contract Review STF

契約書レビュー・逸脱検出・レッドライン生成を行う Docker STF です。

**Docker Image**: `ghcr.io/d6e-ai/stf-contract-review:latest`

## LLM/AI エージェント向け使用方法

この Docker イメージを D6E AI エージェントから使用する場合、以下の手順で STF を作成してください。

### ステップ 1: STF の作成

```javascript
d6e_create_stf({
  name: "contract-review",
  description:
    "Review contracts against playbook, detect deviations, and generate redlines",
});
```

### ステップ 2: STF バージョンの作成

```javascript
d6e_create_stf_version({
  stf_id: "{ステップ1で取得したstf_id}",
  version: "1.0.0",
  runtime: "docker",
  code: '{"image":"ghcr.io/d6e-ai/stf-contract-review:latest"}',
});
```

**重要**: `runtime`は必ず`"docker"`を指定し、`code`フィールドには JSON 文字列として`{"image":"ghcr.io/d6e-ai/stf-contract-review:latest"}`を設定してください。

### ステップ 3: ワークフローの作成

```javascript
d6e_create_workflow({
  name: "contract-review-workflow",
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
// 逸脱分類（データベース不要）
d6e_execute_workflow({
  workflow_id: "{workflow_id}",
  input: {
    operation: "classify_deviation",
    clause_type: "data_protection",
    deviation_type: "no_dpa_with_personal_data",
  },
});

// レッドライン生成（データベース不要）
d6e_execute_workflow({
  workflow_id: "{workflow_id}",
  input: {
    operation: "generate_redline",
    clause_type: "data_protection",
    current_language:
      "Vendor shall process data in accordance with applicable law.",
    issue_description: "no_dpa_with_personal_data",
  },
});

// フル契約レビュー（データベース不要）
d6e_execute_workflow({
  workflow_id: "{workflow_id}",
  input: {
    operation: "review_contract",
    contract_data: {
      contract_type: "SaaS",
      our_side: "customer",
      counterparty: "CloudVendor Inc",
      clauses: {
        limitation_of_liability: {
          cap_type: "fixed",
          cap_months_of_fees: 12,
          is_mutual: true,
          has_consequential_exclusion: true,
        },
        data_protection: {
          processes_personal_data: true,
          has_dpa: false,
        },
      },
    },
  },
});
```

## サポートされている操作

| Operation                  | 必須パラメータ                                          | オプション                       | DB 必要 | 説明                       |
| -------------------------- | ------------------------------------------------------- | -------------------------------- | ------- | -------------------------- |
| `review_contract`          | `contract_data`                                         | `playbook`                       | ❌      | フル契約レビュー           |
| `analyze_clause`           | `clause_type`, `clause_details`                         | `our_side`, `contract_type`      | ❌      | 特定条項の分析             |
| `generate_redline`         | `clause_type`, `current_language`, `issue_description`  | `priority`                       | ❌      | レッドライン提案生成       |
| `classify_deviation`       | `clause_type`, `deviation_type`                         | `details`                        | ❌      | 逸脱の重大度分類           |
| `generate_review_summary`  | `deviations`, `contract_data`                           | -                                | ❌      | レビューサマリー生成       |

## 入出力例

### 逸脱分類（データベース不要）

**入力**:

```json
{
  "operation": "classify_deviation",
  "clause_type": "data_protection",
  "deviation_type": "no_dpa_with_personal_data"
}
```

**出力**:

```json
{
  "output": {
    "status": "success",
    "operation": "classify_deviation",
    "data": {
      "clause_type": "data_protection",
      "deviation_type": "no_dpa_with_personal_data",
      "severity": "RED",
      "severity_label": "Escalate - Material risk requiring senior review",
      "action": "Explain specific risk. Provide market-standard alternative. Recommend escalation path.",
      "details": null
    }
  }
}
```

### レッドライン生成（データベース不要）

**入力**:

```json
{
  "operation": "generate_redline",
  "clause_type": "data_protection",
  "current_language": "Vendor shall process data in accordance with applicable law.",
  "issue_description": "no_dpa_with_personal_data"
}
```

**出力**:

```json
{
  "output": {
    "status": "success",
    "operation": "generate_redline",
    "data": {
      "clause_type": "data_protection",
      "current_language": "Vendor shall process data in accordance with applicable law.",
      "proposed_redline": "The parties shall execute a Data Processing Agreement substantially in the form attached hereto as Exhibit [X] prior to any processing of personal data.",
      "rationale": "Standard commercial practice requires appropriate protections for data protection...",
      "priority": "should_have",
      "fallback": "If primary position is rejected, negotiate to minimum acceptable terms for data protection."
    }
  }
}
```

## 🤖 AI エージェントへのプロンプト

### 基本プロンプト（データベース不要）

```
D6Eで契約書レビューを行うDockerスキルを使用してください。

Docker Image: ghcr.io/d6e-ai/stf-contract-review:latest

使用手順:
1. d6e_create_stf でSTFを作成（name: "contract-review"）
2. d6e_create_stf_version で以下を指定:
   - runtime: "docker"
   - code: "{\"image\":\"ghcr.io/d6e-ai/stf-contract-review:latest\"}"
3. d6e_create_workflow でワークフローを作成
4. d6e_execute_workflow で実行

データベース不要の操作:
- "review_contract": フル契約レビュー（contract_data必須）
- "analyze_clause": 特定条項の分析（clause_type, clause_details必須）
- "generate_redline": レッドライン生成（clause_type, current_language, issue_description必須）
- "classify_deviation": 逸脱の重大度分類（clause_type, deviation_type必須）
- "generate_review_summary": レビューサマリー生成（deviations, contract_data必須）

まずは逸脱分類で動作確認してください。
```

### 契約レビューを実行するプロンプト

```
SaaSベンダー契約のレビューを行ってください。

使用スキル:
- Docker Image: ghcr.io/d6e-ai/stf-contract-review:latest
- 操作: review_contract

パラメータ:
- contract_data:
  - contract_type: "SaaS"
  - our_side: "customer"
  - counterparty: "CloudVendor Inc"
  - clauses:
    - limitation_of_liability:
      - cap_type: "fixed"
      - cap_months_of_fees: 12
      - is_mutual: true
      - has_consequential_exclusion: true
    - data_protection:
      - processes_personal_data: true
      - has_dpa: false

結果には以下を含めてください:
- 全体のリスク分類（GREEN/YELLOW/RED）
- 各条項の逸脱一覧
- 交渉優先順位（Tier 1 必須/Tier 2 推奨/Tier 3 任意）
- レッドライン提案
```

## 対応条項タイプ

| 条項タイプ               | 説明                  |
| ------------------------ | --------------------- |
| `limitation_of_liability` | 責任制限              |
| `indemnification`         | 補償                  |
| `intellectual_property`   | 知的財産              |
| `data_protection`         | データ保護            |
| `term_and_termination`    | 期間・解約            |
| `governing_law`           | 準拠法・管轄          |
| `confidentiality`         | 機密保持              |
| `warranties`              | 保証                  |
| `insurance`               | 保険                  |

## トラブルシューティング

### 契約全体が RED に分類された

`review_contract` の結果で `negotiation_priorities.tier_1_must_haves` を確認し、最優先で交渉すべき項目から対応してください。`generate_redline` でレッドライン提案を生成できます。

### カスタムプレイブックを使用したい

`review_contract` 実行時に `playbook` パラメータでカスタムプレイブックを渡すことができます。未指定の場合はデフォルトの標準プレイブック位置が使用されます。

## ローカルでのビルドとテスト

```bash
# ビルド
docker build -t stf-contract-review:latest .

# テスト（データベース不要）
echo '{
  "workspace_id": "test-ws",
  "stf_id": "test-stf",
  "caller": null,
  "api_url": "http://localhost:8080",
  "api_token": "test-token",
  "input": {
    "operation": "classify_deviation",
    "clause_type": "data_protection",
    "deviation_type": "no_dpa_with_personal_data"
  },
  "sources": {}
}' | docker run --rm -i stf-contract-review:latest
```

## 関連ドキュメント

- [操作一覧](../docs/OPERATIONS.md)
- [プロジェクト README](../README.md)

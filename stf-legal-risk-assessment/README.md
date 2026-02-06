# D6E Legal Risk Assessment STF

法的リスクを重大度×可能性フレームワークで評価・分類する Docker STF です。

**Docker Image**: `ghcr.io/d6e-ai/stf-legal-risk-assessment:latest`

## LLM/AI エージェント向け使用方法

この Docker イメージを D6E AI エージェントから使用する場合、以下の手順で STF を作成してください。

### ステップ 1: STF の作成

```javascript
d6e_create_stf({
  name: "legal-risk-assessment",
  description:
    "Assess and classify legal risks using severity-by-likelihood framework",
});
```

### ステップ 2: STF バージョンの作成

```javascript
d6e_create_stf_version({
  stf_id: "{ステップ1で取得したstf_id}",
  version: "1.0.0",
  runtime: "docker",
  code: '{"image":"ghcr.io/d6e-ai/stf-legal-risk-assessment:latest"}',
});
```

**重要**: `runtime`は必ず`"docker"`を指定し、`code`フィールドには JSON 文字列として`{"image":"ghcr.io/d6e-ai/stf-legal-risk-assessment:latest"}`を設定してください。

### ステップ 3: ワークフローの作成

```javascript
d6e_create_workflow({
  name: "legal-risk-assessment-workflow",
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
// リスクスコア計算（データベース不要）
d6e_execute_workflow({
  workflow_id: "{workflow_id}",
  input: {
    operation: "calculate_risk_score",
    severity: 4,
    likelihood: 3,
  },
});

// リスクマトリクス生成（データベース不要）
d6e_execute_workflow({
  workflow_id: "{workflow_id}",
  input: {
    operation: "generate_risk_matrix",
  },
});

// フルリスク評価（データベース不要）
d6e_execute_workflow({
  workflow_id: "{workflow_id}",
  input: {
    operation: "assess_risk",
    risk_data: {
      description: "Vendor contract lacks adequate data protection provisions",
      category: "Data Privacy",
      severity: 4,
      likelihood: 3,
      contributing_factors: [
        "Personal data processing without DPA",
        "Cross-border data transfers",
      ],
      mitigating_factors: ["Vendor is SOC 2 certified"],
    },
  },
});
```

## サポートされている操作

| Operation                      | 必須パラメータ              | オプション   | DB 必要 | 説明                       |
| ------------------------------ | --------------------------- | ------------ | ------- | -------------------------- |
| `assess_risk`                  | `risk_data`                 | -            | ❌      | フルリスク評価             |
| `calculate_risk_score`         | `severity`, `likelihood`    | -            | ❌      | リスクスコア計算           |
| `generate_risk_memo`           | `assessment_data`           | -            | ❌      | リスク評価メモ生成         |
| `create_risk_register_entry`   | `risk_data`                 | -            | ❌      | リスクレジスター登録       |
| `get_escalation_recommendation`| `risk_level`                | `context`    | ❌      | エスカレーション推奨       |
| `generate_risk_matrix`         | -                           | -            | ❌      | リスクマトリクス生成       |

## 入出力例

### リスクスコア計算（データベース不要）

**入力**:

```json
{
  "operation": "calculate_risk_score",
  "severity": 4,
  "likelihood": 3
}
```

**出力**:

```json
{
  "output": {
    "status": "success",
    "operation": "calculate_risk_score",
    "data": {
      "severity": {
        "rating": 4,
        "label": "High"
      },
      "likelihood": {
        "rating": 3,
        "label": "Possible"
      },
      "risk_score": 12,
      "risk_level": {
        "color": "ORANGE",
        "label": "High Risk"
      }
    }
  }
}
```

### エスカレーション推奨（データベース不要）

**入力**:

```json
{
  "operation": "get_escalation_recommendation",
  "risk_level": "RED"
}
```

**出力**:

```json
{
  "output": {
    "status": "success",
    "operation": "get_escalation_recommendation",
    "data": {
      "risk_level": "RED",
      "escalation_required": true,
      "escalation_to": "General Counsel / C-Suite / Board (as appropriate)",
      "outside_counsel": true,
      "review_cadence": "Daily or more frequent",
      "reporting": "Board risk reporting"
    }
  }
}
```

## 🤖 AI エージェントへのプロンプト

### 基本プロンプト（データベース不要）

```
D6Eで法的リスク評価を行うDockerスキルを使用してください。

Docker Image: ghcr.io/d6e-ai/stf-legal-risk-assessment:latest

使用手順:
1. d6e_create_stf でSTFを作成（name: "legal-risk-assessment"）
2. d6e_create_stf_version で以下を指定:
   - runtime: "docker"
   - code: "{\"image\":\"ghcr.io/d6e-ai/stf-legal-risk-assessment:latest\"}"
3. d6e_create_workflow でワークフローを作成
4. d6e_execute_workflow で実行

データベース不要の操作:
- "assess_risk": フルリスク評価（risk_data必須）
- "calculate_risk_score": リスクスコア計算（severity, likelihood必須、各1-5）
- "generate_risk_memo": リスク評価メモ生成（assessment_data必須）
- "create_risk_register_entry": リスクレジスター登録（risk_data必須）
- "get_escalation_recommendation": エスカレーション推奨（risk_level必須）
- "generate_risk_matrix": リスクマトリクス生成（パラメータ不要）

まずはリスクスコア計算で動作確認してください。
```

### リスク評価を実行するプロンプト

```
契約上のデータ保護リスクを評価してください。

使用スキル:
- Docker Image: ghcr.io/d6e-ai/stf-legal-risk-assessment:latest
- 操作: assess_risk

パラメータ:
- risk_data:
  - description: "ベンダー契約にDPAが含まれていない"
  - category: "Data Privacy"
  - severity: 4
  - likelihood: 3
  - contributing_factors: ["個人データ処理にDPAなし", "国際データ移転あり"]
  - mitigating_factors: ["ベンダーはSOC 2認定済み"]

結果には以下を含めてください:
- リスクスコアと分類（GREEN/YELLOW/ORANGE/RED）
- 推奨アクション
- エスカレーションガイダンス
- 緩和オプション
- モニタリングプラン
```

## リスクマトリクス

| スコア | 色     | レベル       | 範囲  |
| ------ | ------ | ------------ | ----- |
| 1-4    | GREEN  | Low Risk     | 低    |
| 5-9    | YELLOW | Medium Risk  | 中    |
| 10-15  | ORANGE | High Risk    | 高    |
| 16-25  | RED    | Critical Risk| 極めて高 |

## 重大度スケール（Severity 1-5）

| レベル | ラベル     | 説明                                           |
| ------ | ---------- | ---------------------------------------------- |
| 1      | Negligible | 軽微な不便; 重大な財務・運営・評判への影響なし |
| 2      | Low        | 限定的な影響; 関連価値の1%未満の財務リスク     |
| 3      | Moderate   | 有意な影響; 関連価値の1-5%の財務リスク         |
| 4      | High       | 重大な影響; 関連価値の5-25%の財務リスク        |
| 5      | Critical   | 深刻な影響; 関連価値の25%超の財務リスク        |

## トラブルシューティング

### リスクスコアの解釈が分からない

`generate_risk_matrix` を実行して、5×5のリスクマトリクスを視覚的に確認してください。各セルにスコアと色分類が表示されます。

### エスカレーションが必要かどうか判断したい

`get_escalation_recommendation` にリスクレベル（GREEN/YELLOW/ORANGE/RED）を渡すと、エスカレーション先、外部弁護士の必要性、レビュー頻度が取得できます。

## ローカルでのビルドとテスト

```bash
# ビルド
docker build -t stf-legal-risk-assessment:latest .

# テスト（データベース不要）
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
```

## 関連ドキュメント

- [操作一覧](../docs/OPERATIONS.md)
- [プロジェクト README](../README.md)

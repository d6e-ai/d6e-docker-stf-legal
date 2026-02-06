# D6E NDA Triage STF

NDAスクリーニング・リスク分類（GREEN/YELLOW/RED）を行う Docker STF です。

**Docker Image**: `ghcr.io/d6e-ai/stf-nda-triage:latest`

## LLM/AI エージェント向け使用方法

この Docker イメージを D6E AI エージェントから使用する場合、以下の手順で STF を作成してください。

### ステップ 1: STF の作成

```javascript
d6e_create_stf({
  name: "nda-triage",
  description:
    "Screen incoming NDAs and classify risk level as GREEN/YELLOW/RED",
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

**重要**: `runtime`は必ず`"docker"`を指定し、`code`フィールドには JSON 文字列として`{"image":"ghcr.io/d6e-ai/stf-nda-triage:latest"}`を設定してください。

### ステップ 3: ワークフローの作成

```javascript
d6e_create_workflow({
  name: "nda-triage-workflow",
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
// NDAチェックリスト生成（データベース不要）
d6e_execute_workflow({
  workflow_id: "{workflow_id}",
  input: {
    operation: "generate_checklist",
    nda_type: "mutual",
  },
});

// NDAトリアージ（データベース不要）
d6e_execute_workflow({
  workflow_id: "{workflow_id}",
  input: {
    operation: "triage_nda",
    nda_data: {
      nda_type: "mutual",
      counterparty: "Acme Corp",
      purpose: "Potential partnership discussion",
      carveouts_present: [
        "public_knowledge",
        "prior_possession",
        "independent_development",
        "third_party_receipt",
        "legal_compulsion",
      ],
      term_years: 2,
      survival_years: 3,
      governing_law: "Delaware",
      problematic_provisions: [],
    },
  },
});

// ルーティング推奨（データベース不要）
d6e_execute_workflow({
  workflow_id: "{workflow_id}",
  input: {
    operation: "get_routing_recommendation",
    classification: "YELLOW",
  },
});
```

## サポートされている操作

| Operation                    | 必須パラメータ               | オプション  | DB 必要 | 説明                           |
| ---------------------------- | ---------------------------- | ----------- | ------- | ------------------------------ |
| `triage_nda`                 | `nda_data`                   | -           | ❌      | NDA全体のトリアージ評価        |
| `check_clause`               | `clause_type`, `clause_data` | -           | ❌      | 特定条項の標準基準チェック     |
| `get_routing_recommendation` | `classification`             | `context`   | ❌      | 分類に基づくルーティング推奨   |
| `generate_checklist`         | -                            | `nda_type`  | ❌      | NDAスクリーニングチェックリスト生成 |

## 入出力例

### NDAチェックリスト生成（データベース不要）

**入力**:

```json
{
  "operation": "generate_checklist",
  "nda_type": "mutual"
}
```

**出力**:

```json
{
  "output": {
    "status": "success",
    "operation": "generate_checklist",
    "data": {
      "nda_type": "mutual",
      "generated_at": "2025-01-15T10:00:00Z",
      "sections": [
        {
          "name": "Agreement Structure",
          "items": [
            {"check": "Type identified (mutual/unilateral)", "status": "pending"},
            {"check": "Appropriate for business context", "status": "pending"},
            {"check": "Standalone agreement (not embedded)", "status": "pending"}
          ]
        },
        {
          "name": "Standard Carveouts",
          "items": [
            {"check": "Public knowledge carveout", "status": "pending"},
            {"check": "Prior possession carveout", "status": "pending"},
            {"check": "Independent development carveout", "status": "pending"},
            {"check": "Third-party receipt carveout", "status": "pending"},
            {"check": "Legal compulsion carveout", "status": "pending"}
          ]
        },
        {
          "name": "Problematic Provisions (should NOT be present)",
          "items": [
            {"check": "No non-solicitation", "status": "pending"},
            {"check": "No non-compete", "status": "pending"},
            {"check": "No exclusivity", "status": "pending"}
          ]
        }
      ]
    }
  }
}
```

### ルーティング推奨（データベース不要）

**入力**:

```json
{
  "operation": "get_routing_recommendation",
  "classification": "RED"
}
```

**出力**:

```json
{
  "output": {
    "status": "success",
    "operation": "get_routing_recommendation",
    "data": {
      "classification": "RED",
      "action": "Full legal review required. Prepare counterproposal or send standard form.",
      "reviewer": "Senior counsel / Head of legal",
      "timeline": "3-5 business days",
      "notes": "Do not sign. Requires negotiation, counterproposal with standard form NDA, or rejection."
    }
  }
}
```

## 🤖 AI エージェントへのプロンプト

### 基本プロンプト（データベース不要）

```
D6EでNDAトリアージを行うDockerスキルを使用してください。

Docker Image: ghcr.io/d6e-ai/stf-nda-triage:latest

使用手順:
1. d6e_create_stf でSTFを作成（name: "nda-triage"）
2. d6e_create_stf_version で以下を指定:
   - runtime: "docker"
   - code: "{\"image\":\"ghcr.io/d6e-ai/stf-nda-triage:latest\"}"
3. d6e_create_workflow でワークフローを作成
4. d6e_execute_workflow で実行

データベース不要の操作:
- "triage_nda": NDA全体のトリアージ評価（nda_data必須）
- "check_clause": 特定条項チェック（clause_type, clause_data必須）
- "get_routing_recommendation": ルーティング推奨（classification必須）
- "generate_checklist": チェックリスト生成（nda_typeオプション）

まずはチェックリスト生成で動作確認してください。
```

### NDAトリアージを実行するプロンプト

```
受領したNDAのトリアージを行ってください。

使用スキル:
- Docker Image: ghcr.io/d6e-ai/stf-nda-triage:latest
- 操作: triage_nda

パラメータ:
- nda_data:
  - nda_type: "mutual"
  - counterparty: "Acme Corp"
  - purpose: "技術提携の検討"
  - carveouts_present: ["public_knowledge", "prior_possession", "independent_development"]
  - term_years: 3
  - survival_years: 5
  - governing_law: "Delaware"
  - problematic_provisions: ["non_solicitation"]

結果には以下を含めてください:
- GREEN/YELLOW/REDの分類
- 検出された問題点
- ルーティング推奨（誰がレビューすべきか）
```

## NDA分類基準

| 分類   | 意味                               | 対応                          |
| ------ | ---------------------------------- | ----------------------------- |
| GREEN  | 標準的 - カウンセルレビュー不要    | 通常の承認プロセスで署名      |
| YELLOW | 要レビュー - 軽微な問題あり        | 担当レビュアー / ジュニアカウンセルへ |
| RED    | 重大な問題 - 完全な法務レビュー必要 | シニアカウンセル / 法務部長へ |

## トラブルシューティング

### NDAが RED に分類された

`triage_nda` の結果で `issues.red` に記載された問題を確認し、`get_routing_recommendation` で適切なルーティング先を取得してください。カウンターNDA（自社標準フォーム）の送付を検討してください。

### 特定の条項だけをチェックしたい

`check_clause` 操作を使用して、特定の条項タイプ（`term`, `carveouts`, `governing_law` 等）を個別にチェックできます。

## ローカルでのビルドとテスト

```bash
# ビルド
docker build -t stf-nda-triage:latest .

# テスト（データベース不要）
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
```

## 関連ドキュメント

- [操作一覧](../docs/OPERATIONS.md)
- [プロジェクト README](../README.md)

# D6E Meeting Briefing STF

会議ブリーフィング準備・アクションアイテム追跡を行う Docker STF です。

**Docker Image**: `ghcr.io/d6e-ai/stf-meeting-briefing:latest`

## LLM/AI エージェント向け使用方法

この Docker イメージを D6E AI エージェントから使用する場合、以下の手順で STF を作成してください。

### ステップ 1: STF の作成

```javascript
d6e_create_stf({
  name: "meeting-briefing",
  description:
    "Prepare structured meeting briefings and track action items",
});
```

### ステップ 2: STF バージョンの作成

```javascript
d6e_create_stf_version({
  stf_id: "{ステップ1で取得したstf_id}",
  version: "1.0.0",
  runtime: "docker",
  code: '{"image":"ghcr.io/d6e-ai/stf-meeting-briefing:latest"}',
});
```

**重要**: `runtime`は必ず`"docker"`を指定し、`code`フィールドには JSON 文字列として`{"image":"ghcr.io/d6e-ai/stf-meeting-briefing:latest"}`を設定してください。

### ステップ 3: ワークフローの作成

```javascript
d6e_create_workflow({
  name: "meeting-briefing-workflow",
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
// 会議準備チェックリスト取得（データベース不要）
d6e_execute_workflow({
  workflow_id: "{workflow_id}",
  input: {
    operation: "get_meeting_prep_checklist",
    meeting_type: "deal_review",
  },
});

// 会議ブリーフィング生成（データベース不要）
d6e_execute_workflow({
  workflow_id: "{workflow_id}",
  input: {
    operation: "generate_briefing",
    meeting_data: {
      meeting_title: "Acme Corp SaaS Agreement Review",
      meeting_type: "deal_review",
      date_time: "2025-01-20T14:00:00+09:00",
      duration: "60 minutes",
      location: "Conference Room A / Zoom",
      your_role: "advisor",
      participants: [
        {
          name: "John Smith",
          organization: "Acme Corp",
          role: "VP Sales",
          key_interests: "Close deal quickly",
        },
      ],
      agenda: ["Contract status review", "Open issues", "Next steps"],
      talking_points: [
        "DPA must be executed before go-live",
        "Liability cap needs increase",
      ],
      decisions_needed: ["Approve final contract terms"],
    },
  },
});

// アクションアイテム作成（データベース不要）
d6e_execute_workflow({
  workflow_id: "{workflow_id}",
  input: {
    operation: "create_action_items",
    action_data: {
      meeting_title: "Acme Corp SaaS Agreement Review",
      meeting_date: "2025-01-20",
      items: [
        {
          description: "Send updated DPA to Acme Corp",
          owner: "Legal Team",
          deadline: "2025-01-22",
          priority: "High",
          type: "legal_team",
        },
        {
          description: "Review liability cap with finance",
          owner: "Finance",
          deadline: "2025-01-24",
          priority: "Medium",
          type: "business_team",
        },
      ],
    },
  },
});
```

## サポートされている操作

| Operation                    | 必須パラメータ    | オプション | DB 必要 | 説明                       |
| ---------------------------- | ----------------- | ---------- | ------- | -------------------------- |
| `generate_briefing`          | `meeting_data`    | -          | ❌      | 会議ブリーフィング生成     |
| `create_action_items`        | `action_data`     | -          | ❌      | アクションアイテム作成     |
| `get_meeting_prep_checklist` | `meeting_type`    | -          | ❌      | 会議準備チェックリスト取得 |
| `track_action_items`         | `tracking_data`   | -          | ❌      | アクションアイテム追跡     |
| `generate_follow_up`         | `follow_up_data`  | -          | ❌      | 会議フォローアップ生成     |

## 入出力例

### 会議準備チェックリスト取得（データベース不要）

**入力**:

```json
{
  "operation": "get_meeting_prep_checklist",
  "meeting_type": "deal_review"
}
```

**出力**:

```json
{
  "output": {
    "status": "success",
    "operation": "get_meeting_prep_checklist",
    "data": {
      "meeting_type": "deal_review",
      "type_label": "Deal Review",
      "prep_items": [
        {"item": "Contract status and open issues", "status": "pending"},
        {"item": "Counterparty history", "status": "pending"},
        {"item": "Negotiation strategy", "status": "pending"},
        {"item": "Approval requirements", "status": "pending"},
        {"item": "Comparable deals", "status": "pending"}
      ],
      "general_prep": [
        {"item": "Review meeting agenda", "status": "pending"},
        {"item": "Identify key participants and their interests", "status": "pending"},
        {"item": "Gather relevant documents", "status": "pending"},
        {"item": "Prepare talking points", "status": "pending"},
        {"item": "List questions to raise", "status": "pending"},
        {"item": "Review prior meeting notes and action items", "status": "pending"},
        {"item": "Identify decisions needed", "status": "pending"}
      ]
    }
  }
}
```

### アクションアイテム作成（データベース不要）

**入力**:

```json
{
  "operation": "create_action_items",
  "action_data": {
    "meeting_title": "Acme Corp SaaS Agreement Review",
    "meeting_date": "2025-01-20",
    "items": [
      {
        "description": "Send updated DPA to Acme Corp",
        "owner": "Legal Team",
        "deadline": "2025-01-22",
        "priority": "High",
        "type": "legal_team"
      }
    ]
  }
}
```

**出力**:

```json
{
  "output": {
    "status": "success",
    "operation": "create_action_items",
    "data": {
      "meeting_title": "Acme Corp SaaS Agreement Review",
      "meeting_date": "2025-01-20",
      "items": [
        {
          "action_id": "uuid-action-1",
          "description": "Send updated DPA to Acme Corp",
          "owner": "Legal Team",
          "deadline": "2025-01-22",
          "priority": "High",
          "type": "legal_team",
          "type_label": "Legal Team",
          "status": "Open",
          "dependencies": [],
          "notes": "",
          "created_at": "2025-01-20T15:00:00Z",
          "meeting_reference": "Acme Corp SaaS Agreement Review"
        }
      ],
      "summary": {
        "total_items": 1,
        "by_priority": {"high": 1, "medium": 0, "low": 0},
        "by_type": {"legal_team": 1, "business_team": 0, "external": 0, "follow_up_meeting": 0},
        "owners": ["Legal Team"]
      }
    }
  }
}
```

## 🤖 AI エージェントへのプロンプト

### 基本プロンプト（データベース不要）

```
D6Eで会議ブリーフィング管理を行うDockerスキルを使用してください。

Docker Image: ghcr.io/d6e-ai/stf-meeting-briefing:latest

使用手順:
1. d6e_create_stf でSTFを作成（name: "meeting-briefing"）
2. d6e_create_stf_version で以下を指定:
   - runtime: "docker"
   - code: "{\"image\":\"ghcr.io/d6e-ai/stf-meeting-briefing:latest\"}"
3. d6e_create_workflow でワークフローを作成
4. d6e_execute_workflow で実行

データベース不要の操作:
- "generate_briefing": 会議ブリーフィング生成（meeting_data必須）
- "create_action_items": アクションアイテム作成（action_data必須）
- "get_meeting_prep_checklist": 準備チェックリスト取得（meeting_type必須）
- "track_action_items": アクションアイテム追跡（tracking_data必須）
- "generate_follow_up": フォローアップ生成（follow_up_data必須）

まずは会議準備チェックリスト取得で動作確認してください。
```

### 会議ブリーフィングを作成するプロンプト

```
来週のベンダー契約レビュー会議のブリーフィングを作成してください。

使用スキル:
- Docker Image: ghcr.io/d6e-ai/stf-meeting-briefing:latest
- 操作: generate_briefing

パラメータ:
- meeting_data:
  - meeting_title: "Acme Corp SaaS Agreement Review"
  - meeting_type: "deal_review"
  - date_time: "2025-01-20T14:00:00+09:00"
  - duration: "60 minutes"
  - your_role: "advisor"
  - agenda: ["契約ステータス確認", "未解決事項", "次のステップ"]
  - talking_points: ["DPAはサービス開始前に締結必要", "責任制限の引き上げ"]
  - decisions_needed: ["最終契約条件の承認"]

結果には以下を含めてください:
- 参加者情報
- アジェンダ
- 背景情報
- トーキングポイント
- 必要な意思決定
- 準備チェックリスト
```

## 対応会議タイプ

| 会議タイプ        | ラベル                       | 主な準備項目                     |
| ----------------- | ---------------------------- | -------------------------------- |
| `deal_review`     | Deal Review                  | 契約状況、交渉戦略、承認要件     |
| `board_committee` | Board / Committee Meeting    | 法務部報告、リスクハイライト     |
| `vendor_call`     | Vendor Call                  | 契約状況、未解決事項、交渉目標   |
| `team_sync`       | Team Sync                    | 業務状況、優先事項、リソース     |
| `client_customer` | Client / Customer Meeting    | 契約条件、サポート履歴           |
| `regulatory`      | Regulatory / Government      | 事案背景、コンプライアンス状況   |
| `litigation`      | Litigation / Dispute         | 事件状況、戦略、和解パラメータ   |
| `cross_functional`| Cross-Functional Meeting     | 法的影響、リスク評価             |

## トラブルシューティング

### 不明な会議タイプが指定された

`get_meeting_prep_checklist` はサポートされている会議タイプのみ受け付けます。上記の「対応会議タイプ」テーブルから正しいタイプを選択してください。

### アクションアイテムのステータスを更新したい

`track_action_items` 操作を使用して、`action_id` と `new_status`（Open, In Progress, Completed, Overdue, Cancelled）を指定してステータスを更新できます。

## ローカルでのビルドとテスト

```bash
# ビルド
docker build -t stf-meeting-briefing:latest .

# テスト（データベース不要）
echo '{
  "workspace_id": "test-ws",
  "stf_id": "test-stf",
  "caller": null,
  "api_url": "http://localhost:8080",
  "api_token": "test-token",
  "input": {
    "operation": "get_meeting_prep_checklist",
    "meeting_type": "deal_review"
  },
  "sources": {}
}' | docker run --rm -i stf-meeting-briefing:latest
```

## 関連ドキュメント

- [操作一覧](../docs/OPERATIONS.md)
- [プロジェクト README](../README.md)

# AI Panel Studio — ER 数据模型

## 实体关系总览

```
┌──────────┐         ┌──────────────┐         ┌──────────┐
│   Host   │         │  Discussion  │         │  Guest   │
│          │──1:1────│              │────M:N──│          │
│  name    │         │  topic        │         │  name    │
│  system  │         │  status       │         │  persona │
│  prompt  │         │  max_rounds   │         │  system  │
└──────────┘         │  created_at   │         │  prompt  │
                     └──────┬───────┘         └────┬─────┘
                            │                      │
                           1:N                   1:N
                            │                      │
                     ┌──────┴──────────────────────┴──┐
                     │           Message              │
                     │  host_id   (FK, nullable)       │
                     │  guest_id  (FK, nullable)       │
                     │  content                        │
                     │  seq_num                        │
                     │  created_at                     │
                     └──────────────┬─────────────────┘
                                    │ 1:0..1
                           ┌────────┴────────┐
                           │     Opinion     │
                           │  stance         │
                           │  confidence     │
                           │  evidence       │
                           └─────────────────┘
```

## 实体职责

### Host（主持人）
每场讨论独立创建，中立角色，不跨讨论复用。负责开场、追问、串联、总结。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| name | TEXT NOT NULL | 主持人名称 |
| system_prompt | TEXT NOT NULL | 主持风格系统 Prompt |
| created_at | TEXT | 创建时间 |

### Discussion（讨论）
一场讨论会话，绑定一个主持人，关联多个嘉宾。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| topic | TEXT NOT NULL | 讨论主题 |
| status | TEXT NOT NULL | pending / active / paused / completed |
| max_rounds | INTEGER DEFAULT 5 | 最大轮次数 |
| current_round | INTEGER DEFAULT 0 | 当前轮次 |
| host_id | INTEGER FK | 绑定主持人 |
| created_at | TEXT | 创建时间 |

### Guest（嘉宾模板）
全局嘉宾模板库，支持动态增删改，可跨讨论复用。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| name | TEXT NOT NULL | 嘉宾名称 |
| avatar | TEXT | 头像标识/URL |
| persona | TEXT NOT NULL | 人设描述 |
| system_prompt | TEXT NOT NULL | 发言风格系统 Prompt |
| speak_style | TEXT | 语言风格标签（如"犀利""温和""学术"） |
| created_at | TEXT | 创建时间 |

### DiscussionGuest（讨论-嘉宾关联）
M:N 联结表，支持讨论内 stance 覆盖和启用/禁用。

| 字段 | 类型 | 说明 |
|------|------|------|
| discussion_id | INTEGER FK | 讨论 ID |
| guest_id | INTEGER FK | 嘉宾 ID |
| stance_override | TEXT | 讨论内立场覆盖（覆盖 Guest 默认立场） |
| is_active | INTEGER DEFAULT 1 | 本讨论中是否活跃 |
| UNIQUE(discussion_id, guest_id) | | 防重复添加 |

### Message（消息）
方案 B —— 分列外键：host_id 和 guest_id 二选一非空。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| discussion_id | INTEGER FK NOT NULL | 所属讨论 |
| host_id | INTEGER FK NULL | 发送者为主持人 |
| guest_id | INTEGER FK NULL | 发送者为嘉宾 |
| role | TEXT NOT NULL | host / guest / system |
| content | TEXT NOT NULL | 消息内容 |
| seq_num | INTEGER NOT NULL | 讨论内序号 |
| token_count | INTEGER DEFAULT 0 | token 用量 |
| created_at | TEXT | 创建时间 |
| CHECK (host_id IS NOT NULL OR guest_id IS NOT NULL) | | 发送者二选一 |

### Opinion（观点快照）
从 Message 中提炼的观点，1:0..1 关系。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| message_id | INTEGER FK UNIQUE | 关联消息（一条消息最多一个观点） |
| stance_summary | TEXT NOT NULL | 观点摘要 |
| category | TEXT NOT NULL | consensus / disagreement / neutral |
| confidence | REAL | 置信度 0.0-1.0 |
| evidence | TEXT | 支撑该观点的原文片段 |
| created_at | TEXT | 创建时间 |

## 外键约束链

```
Discussion.host_id              → Host.id              (CASCADE)
DiscussionGuest.discussion_id   → Discussion.id        (CASCADE)
DiscussionGuest.guest_id        → Guest.id             (CASCADE)
Message.discussion_id           → Discussion.id        (CASCADE)
Message.host_id                 → Host.id              (SET NULL)
Message.guest_id                → Guest.id             (SET NULL)
Opinion.message_id              → Message.id           (CASCADE)
```

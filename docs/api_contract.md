# AI Panel Studio — API 契约

## REST 端点

### Discussion（讨论）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/discussions` | 讨论列表 |
| POST | `/api/discussions` | 创建讨论（含绑定 Host） |
| GET | `/api/discussions/{id}` | 讨论详情（含嘉宾列表） |
| PATCH | `/api/discussions/{id}` | 更新讨论状态/轮次 |
| DELETE | `/api/discussions/{id}` | 删除讨论 |

### Guest（嘉宾模板）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/guests` | 嘉宾模板列表 |
| POST | `/api/guests` | 创建嘉宾模板 |
| PATCH | `/api/guests/{id}` | 更新嘉宾模板 |
| DELETE | `/api/guests/{id}` | 删除嘉宾模板 |

### Discussion-Guest 关联

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/discussions/{id}/guests` | 向讨论添加嘉宾 |
| DELETE | `/api/discussions/{id}/guests/{guest_id}` | 从讨论移除嘉宾 |

### 查询

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/discussions/{id}/messages` | 获取讨论消息历史 |
| GET | `/api/discussions/{id}/opinions` | 获取讨论观点汇总 |

---

## WebSocket

### 端点

```
WS /ws/discussion/{id}
```

### 客户端 → 服务端

| action | payload | 说明 |
|--------|---------|------|
| `start` | `{}` | 用户确认，开始讨论 |
| `pause` | `{}` | 暂停讨论 |
| `resume` | `{}` | 恢复讨论 |
| `stop` | `{}` | 结束讨论 |

### 服务端 → 客户端

| event | payload | 说明 |
|-------|---------|------|
| `host_speak` | `{content, seq_num}` | 主持人发言 |
| `guest_speak` | `{guest_id, guest_name, content, seq_num}` | 嘉宾发言 |
| `token_stream` | `{sender_type, sender_id, token, seq_num}` | LLM 流式 token |
| `speak_done` | `{message_id, seq_num, sender_type, sender_id}` | 一段发言完成 |
| `opinion_extracted` | `{opinion_id, message_id, stance_summary, category}` | 观点提炼 |
| `round_change` | `{round}` | 轮次切换 |
| `discussion_end` | `{summary, opinions: [...]}` | 讨论结束，含总结 |
| `error` | `{code, message}` | 错误通知 |

# REST API 补全设计

**日期:** 2026-06-28  
**目标:** 恢复 11 个 REST 端点 + 修复前端 CreateDiscuss 创建流程

## 约束

1. API Key 禁止出现在路由代码 — 路由仅调用 `db.models` + `db.dependencies`
2. TDD：先写 pytest TestClient 集成测试 → 再写路由代码
3. 仅改 `guests.py` / `discussions.py` / 新增 `test_api_routes.py` / `CreateDiscuss.vue`

## 测试（test_api_routes.py）

- 用 FastAPI TestClient + 内存 SQLite
- 11 个端点各 1 个测试用例

## 路由实现

- `guests.py`: 4 端点 CRUD，复用 `Guest` ORM + `get_db()`
- `discussions.py`: 7 端点，含 Host 创建 + DiscussionGuest 关联 + 消息/观点查询
- `CreateDiscuss.vue`: `enterStudio()` 改为 POST /api/discussions → POST /api/guests → POST /api/discussions/{id}/guests → /studio/{id}

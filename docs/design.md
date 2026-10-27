
# 仅添加内存协议 (Append-Only Memory Protocol) 设计稿

## 1. 核心设计逻辑
- **只追加不删除**：数据一旦写入，即永久存在，不允许任何修改或删除操作，确保 AI 记忆的绝对真实。
- **线性时间轴**：所有数据严格按照写入时间顺序排列，保证因果关系的正确性。

## 2. 数据结构 (Block)
每条内存数据被封装为一个区块（Block），包含以下字段：
- `id`: 唯一标识符 (UUID)
- `timestamp`: 写入时的精确时间
- `content`: 内存文本内容
- `prev_hash`: 前一条内存的哈希值（可选，用于保证链式完整性）

## 3. 核心 API 接口
```python
# 1. 写入数据（仅允许追加）
def append(content: str) -> str:
    pass

# 2. 检索数据（根据时间或关键词查找）
def retrieve(query: str, limit: int = 10) -> list:
    pass

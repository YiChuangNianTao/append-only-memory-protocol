import json, math, os
from datetime import datetime
from typing import Optional, List

class MemoryRecord:
    """单条电报体记忆（只追加，不覆盖、不删原文）。"""
    def __init__(self, mid: int, content: str, emotional_tag: str = "中性",
                 created_at: Optional[str] = None, hook: str = "",
                 decay_rate: float = 0.02, strength: float = 1.0, retrieved_count: int = 0):
        self.mid = mid
        self.content = content
        self.hook = hook
        self.emotional_tag = emotional_tag
        # 确保 created_at 是合法的字符串，防止空字符串导致解析失败
        if created_at is None or created_at == "":
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            self.created_at = created_at
        self.decay_rate = decay_rate
        self.strength = strength
        self.retrieved_count = retrieved_count

    def decay(self):
        """计算从创建到现在经过的天数，并进行指数衰减。"""
        try:
            created_time = datetime.strptime(self.created_at, "%Y-%m-%d %H:%M:%S")
            # 确保 days 不为负数（避免系统时间不准或未来时间导致强度增加）
            days = max(0, (datetime.now() - created_time).days)
        except (ValueError, TypeError):
            days = 0
        # 指数衰减公式：strength = strength * e^(-衰减率 * 天数)
        self.strength = max(0.0, self.strength * math.exp(-self.decay_rate * days))

    def reinforce(self):
        """提取记忆时触发强化。"""
        self.retrieved_count += 1
        self.strength = min(1.0, self.strength + 0.1)

    def to_dict(self):
        return {
            "mid": self.mid, "content": self.content, "hook": self.hook,
            "emotional_tag": self.emotional_tag, "created_at": self.created_at,
            "decay_rate": self.decay_rate, "strength": self.strength,
            "retrieved_count": self.retrieved_count
        }

class MemoryStore:
    """追加式档案。三层结构：世代摘要(常驻) / 当前目录(常驻) / 单条正文(按需加载)。"""
    def __init__(self, path="data/memory.jsonl"):
        self.path = path
        self.records: List[MemoryRecord] = []
        # 确保目录存在
        dir_name = os.path.dirname(self.path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    self.records.append(MemoryRecord(**d))
                except:
                    # 跳过单条损坏的数据，保证系统健壮性
                    continue

    def _save_all(self):
        """将所有记录（包括强度变化）写回文件（原子写入）。"""
        temp_path = self.path + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            for rec in self.records:
                f.write(json.dumps(rec.to_dict(), ensure_ascii=False) + "\n")
        # 重命名文件，防止写入中途断电导致数据丢失
        os.replace(temp_path, self.path)

    def append(self, content: str, emotional_tag: str = "中性", hook: str = "") -> int:
        """只追加一行，写后立即落盘。"""
        # 使用最大值+1生成ID，避免ID冲突
        mid = max([r.mid for r in self.records]) + 1 if self.records else 1
        
        rec = MemoryRecord(mid=mid, content=content, emotional_tag=emotional_tag, hook=hook)
        
        # 1. 先落盘追加
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec.to_dict(), ensure_ascii=False) + "\n")
        
        # 2. 落盘成功后再入内存
        self.records.append(rec)
        return mid

    def build_catalog(self, top_k: int = 8) -> str:
        """第二层【当前目录】：编号+情绪词+短钩子，常驻但极省 token。"""
        # 更新所有记忆的强度
        for r in self.records:
            r.decay()
        
        # 筛选强度大于 0.1 的记忆并按强度倒序排列
        active = sorted([r for r in self.records if r.strength >= 0.1],
                        key=lambda x: x.strength, reverse=True)[:top_k]
        
        if not active:
            return "（目录：暂无值得翻起的记忆。）"
        
        lines = [f"- [{r.mid}] {r.emotional_tag} | {r.hook or r.content[:12]}" for r in active]
        return "当前目录：\n" + "\n".join(lines)

    def load_body(self, mids: List[int]) -> str:
        """第三层【单条正文】：按需加载，被翻起的记忆会强化。"""
        picked = []
        # 找到对应的记录并强化
        for r in self.records:
            if r.mid in mids:
                r.reinforce()
                picked.append(r.content)
        
        # 如果有记忆被强化（提取），说明强度发生了变化，需要保存
        if picked:
            self._save_all()
            
        return "按需正文：\n" + "\n".join(picked) if picked else ""

    def active_ids(self, top_k: int = 8) -> List[int]:
        """获取当前活跃的记忆ID列表。"""
        for r in self.records:
            r.decay()
        
        active = sorted([r for r in self.records if r.strength >= 0.1],
                        key=lambda x: x.strength, reverse=True)[:top_k]
        return [r.mid for r in active]

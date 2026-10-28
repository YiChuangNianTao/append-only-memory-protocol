from datetime import date
from companion.persona import Persona
from companion.memory import MemoryStore

class Companion:
    def __init__(self):
        self.persona = Persona()
        # 确保路径与 memory.py 中的默认路径一致
        self.memory = MemoryStore() 
        self._today = str(date.today())
        self._today_written = 0
        self.daily_write_cap = 5  # 输出闸门：每日最多新增少量条目

    def chat(self, user_input: str, llm=None):
        # 1. 先决定按需加载哪些正文（第二层目录 -> 第三层正文）
        mids = self.memory.active_ids(top_k=5)
        bodies = self.memory.load_body(mids[:3])  # 只加载最强的 3 条，控制成本

        # 2. 拼接固定输入顺序（稳定部分在前，动态部分在后）
        prompt = self._build_prompt(bodies, user_input)

        # 3. 人格自整
        self._grow(user_input)

        # 4. 生成回复（接入本地大模型；没传则用占位）
        if llm is None:
            reply = "（占位回复：把 prompt 发给本地模型即可。）"
        else:
            reply = llm(prompt)

        # 5. 输出闸门：决定是否把这一轮沉淀成一条电报体记忆
        self._maybe_archive(user_input, reply)
        return reply

    def _build_prompt(self, bodies: str, user_input: str) -> str:
        stable = self.persona.build_prefix()          # 人格卡+边界+世代摘要(常驻)
        catalog = self.memory.build_catalog()         # 当前目录(常驻)
        parts = [stable, catalog]
        if bodies:
            parts.append(bodies)                      # 按需条目(动态)
        parts.append(f"[用户输入] {user_input}")
        return "\n\n".join(parts)

    def _maybe_archive(self, user_input: str, reply: str):
        if self._today != str(date.today()):
            self._today = str(date.today())
            self._today_written = 0
        if self._today_written >= self.daily_write_cap:
            return

        # 只有在“有记忆价值”时才写：有情绪或用户在倾诉/分享
        if any(k in user_input for k in ["喜欢", "难过", "开心", "害怕", "想要", "今天", "记得"]):
            hook = user_input[:10]
            tag = "正面" if any(k in user_input for k in ["开心", "喜欢", "好"]) else "中性"
            self.memory.append(content=hook, emotional_tag=tag, hook=hook)
            self._today_written += 1

    def _grow(self, user_input: str):
        """根据交互微调人格参数，落 growth_log。"""
        t = self.persona.data["traits"]
        new = {}
        if "?" in user_input or "？" in user_input:
            new["curiosity"] = min(1.0, t.get("curiosity", 0) + 0.01)
        if "哈哈" in user_input or "笑死" in user_input:
            new["humor"] = min(1.0, t.get("humor", 0) + 0.01)
        if new:
            self.persona.update_traits(new)

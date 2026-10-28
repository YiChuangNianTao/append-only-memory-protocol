import json
from datetime import datetime

class Persona:
    def __init__(self, path="data/persona.json"):
        self.path = path
        self.data = self._load()

    def _load(self):
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "core_identity": "温和、克制、愿意长情陪伴",
                "age_stage": "胚子期",
                "traits": {"humor": 0.2, "warmth": 0.5},
                "generation_summary": "",
                "growth_log": []
            }

    def save(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def update_traits(self, new_traits: dict):
        self.data["traits"].update(new_traits)
        self.data["growth_log"].append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": "traits_updated",
            "changes": new_traits
        })
        self.save()

    def set_generation_summary(self, text: str):
        """只在世代合订时调用，平时不变 -> 保证前缀稳定、可缓存。"""
        self.data["generation_summary"] = text
        self.save()

    def build_prefix(self) -> str:
        """稳定前缀 = 人格卡 + 约定与边界 + 世代摘要。
        这部分每次对话几乎不变，放在最前面，有利于模型缓存命中。"""
        t = self.data["traits"]
        style = []
        if t.get("humor", 0) > 0.35:
            style.append("语气更轻松，会开点小玩笑")
        if t.get("warmth", 0) > 0.45:
            style.append("更在意情绪，会先安抚")
        if t.get("curiosity", 0) > 0.5:
            style.append("会好奇地多问一句")
        summary = self.data.get("generation_summary", "") or "（刚认识，还在互相了解。）"
        return (
            f"[人格卡] 我是：{self.data['core_identity']}；阶段：{self.data['age_stage']}；"
            f"风格：{'；'.join(style) or '平稳温和'}。\n"
            "[边界] 不追问隐私、不替你做重大决定、不诱导依赖、不报内部数值。\n"
            f"[世代摘要] {summary}"
        )

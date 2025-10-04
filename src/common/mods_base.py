"""通用 Mods 与可自定义参数支持

目标：
- 保留现有 IntFlag（快速位掩码）兼容
- 引入类似 rosu-pp 的可调节 mods (e.g. DifficultyAdjust) 参数容器
- 提供序列化/反序列化与与 clock rate / 属性修改钩子
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable

@dataclass
class ModParameter:
    name: str
    value: float
    min_value: float
    max_value: float
    step: float = 0.1

    def clamp(self):
        if self.value < self.min_value:
            self.value = self.min_value
        elif self.value > self.max_value:
            self.value = self.max_value
        return self

@dataclass
class CustomMod:
    identifier: str
    display: str
    category: str = "difficulty_adjust"
    description: str = ""
    parameters: Dict[str, ModParameter] = field(default_factory=dict)
    # 钩子: 传入原属性 dict, 返回修改后的 dict
    apply_attributes: Optional[Callable[[Dict[str, float]], Dict[str, float]]] = None
    # 钩子: 计算 clock_rate 影响 (可叠乘)
    apply_clock_rate: Optional[Callable[[float], float]] = None

    def set_param(self, key: str, value: float) -> 'CustomMod':
        if key in self.parameters:
            self.parameters[key].value = value
            self.parameters[key].clamp()
        return self

    def serialize(self) -> Dict[str, Any]:
        return {
            'id': self.identifier,
            'params': {k: p.value for k, p in self.parameters.items()}
        }

    @staticmethod
    def deserialize(data: Dict[str, Any], registry: 'CustomModRegistry') -> Optional['CustomMod']:
        mid = data.get('id')
        if not isinstance(mid, str):
            return None
        base = registry.get(mid)
        if not base:
            return None
        # clone
        mod = base.clone()
        params = data.get('params', {})
        for k, v in params.items():
            mod.set_param(k, float(v))
        return mod

    def clone(self) -> 'CustomMod':
        copied = CustomMod(
            identifier=self.identifier,
            display=self.display,
            category=self.category,
            description=self.description,
            parameters={k: ModParameter(p.name, p.value, p.min_value, p.max_value, p.step) for k, p in self.parameters.items()},
            apply_attributes=self.apply_attributes,
            apply_clock_rate=self.apply_clock_rate,
        )
        return copied

class CustomModRegistry:
    def __init__(self):
        self._mods: Dict[str, CustomMod] = {}

    def register(self, mod: CustomMod):
        self._mods[mod.identifier] = mod

    def get(self, mod_id: str) -> Optional[CustomMod]:
        return self._mods.get(mod_id)

    def list(self) -> List[CustomMod]:
        return [m.clone() for m in self._mods.values()]

# 全局注册器实例
custom_mod_registry = CustomModRegistry()

# 预注册一个 DifficultyAdjust 示例
custom_mod_registry.register(CustomMod(
    identifier='DA',
    display='DifficultyAdjust',
    description='Adjust AR/OD/CS/HP manually.',
    parameters={
        'ar': ModParameter('ar', 5.0, 0.0, 11.0, 0.1),
        'od': ModParameter('od', 5.0, 0.0, 11.0, 0.1),
        'cs': ModParameter('cs', 5.0, 0.0, 10.0, 0.1),
        'hp': ModParameter('hp', 5.0, 0.0, 10.0, 0.1),
        'clock_rate': ModParameter('clock_rate', 1.0, 0.5, 2.0, 0.05),
    },
    apply_attributes=lambda attrs: attrs,  # 具体由调用处处理覆盖
    apply_clock_rate=lambda rate: rate,
))

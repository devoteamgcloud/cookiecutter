from __future__ import annotations
from typing import Any, List, Tuple, Dict

class CookiecutterVariable:

    def __init__(self, name: str = "", value: Any = None, prompt: str = "", variables: List[CookiecutterVariable] = [], matches: Any = None, metadata: Dict[str, Any] | None = None):
        self.name = name
        self.value = value
        self.prompt = prompt if prompt else name
        self.variables = variables
        self.matches = matches
        self.metadata = metadata

    @classmethod
    def from_dict(cls, d: dict) -> CookiecutterVariable:
        return CookiecutterVariable(
            name=d.get("name", ""),
            value=d.get("value"),
            prompt=d.get("prompt", d.get("name", "")),
            variables=[CookiecutterVariable.from_dict(v) for v in d.get("variables", [])],
            matches=d.get("matches", None),
            metadata=d.get("metadata"),
        )

    def to_cookiecutter_dict(self, parent: str = "") -> Dict[str, Any]:
        d = {}
        for v in self.variables:
            name = parent + v.name
            d[name] = v.value
            d.update(v.to_cookiecutter_dict(parent=name + "/"))
        return d

    @classmethod
    def is_template(cls, v: CookiecutterVariable) -> bool:
        return v.name.lower() == "template"
    
    def get(self, name: str, default: Any = None) -> CookiecutterVariable:
        for v in self.variables:
            if v.name == name:
                return v
        return default
    
    def set(self, name: str, value: Any):
        for v in self.variables:
            if v.name == name:
                v.value = value
                return
    
    def get_metadata(self) -> Dict[str, Any] | None:
        return self.metadata
    
    def update(self, d: Dict[str, Any]):
        for k, v in d.items():
            parents = k.split("/")
            if len(parents) > 1:
                if self.get(parents[0]) is not None:
                    self.get(parents[0]).update({"/".join(parents[1:]): v})
            elif self.get(k) is not None:
                self.set(k, v)
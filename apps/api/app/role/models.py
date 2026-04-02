from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class Role:
    role_id: str
    name: str
    description: str
    permissions: List[str] = field(default_factory=list)
    is_system: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role_id": self.role_id,
            "name": self.name,
            "description": self.description,
            "permissions": self.permissions,
            "is_system": self.is_system,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Role":
        return cls(
            role_id=data["role_id"],
            name=data["name"],
            description=data["description"],
            permissions=data.get("permissions", []),
            is_system=data.get("is_system", False),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
        )

    def has_permission(self, permission: str) -> bool:
        if "*" in self.permissions:
            return True
        resource = permission.split(":")[0] if ":" in permission else permission
        if f"{resource}:*" in self.permissions:
            return True
        return permission in self.permissions

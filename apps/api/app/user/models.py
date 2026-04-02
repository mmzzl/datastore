from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class User:
    username: str
    password_hash: str
    display_name: str
    role_id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str = "active"
    is_superuser: bool = False
    last_login: Optional[datetime] = None
    login_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "display_name": self.display_name,
            "email": self.email,
            "phone": self.phone,
            "role_id": self.role_id,
            "status": self.status,
            "is_superuser": self.is_superuser,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "login_count": self.login_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        return cls(
            username=data["username"],
            password_hash=data["password_hash"],
            display_name=data["display_name"],
            role_id=data["role_id"],
            email=data.get("email"),
            phone=data.get("phone"),
            status=data.get("status", "active"),
            is_superuser=data.get("is_superuser", False),
            last_login=datetime.fromisoformat(data["last_login"]) if data.get("last_login") else None,
            login_count=data.get("login_count", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            created_by=data.get("created_by"),
        )


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

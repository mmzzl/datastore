RESOURCE_USER = "user"
RESOURCE_ROLE = "role"
RESOURCE_PLUGIN = "plugin"
RESOURCE_BACKTEST = "backtest"
RESOURCE_SELECTION = "selection"
RESOURCE_HOLDINGS = "holdings"
RESOURCE_RISK = "risk"
RESOURCE_SCHEDULER = "scheduler"
RESOURCE_DINGTALK = "dingtalk"
RESOURCE_SYSTEM = "system"

ACTION_VIEW = "view"
ACTION_RUN = "run"
ACTION_EDIT = "edit"
ACTION_DELETE = "delete"
ACTION_MANAGE = "manage"
ACTION_UPLOAD = "upload"

ALL_PERMISSIONS = [
    "user:view",
    "user:edit",
    "user:delete",
    "user:manage",
    "role:view",
    "role:edit",
    "role:delete",
    "role:manage",
    "plugin:view",
    "plugin:upload",
    "plugin:delete",
    "plugin:manage",
    "backtest:view",
    "backtest:run",
    "selection:view",
    "selection:run",
    "holdings:view",
    "holdings:edit",
    "risk:view",
    "scheduler:view",
    "scheduler:manage",
    "dingtalk:view",
    "dingtalk:manage",
    "system:manage",
]

DEFAULT_ROLES = [
    {
        "role_id": "role_superuser",
        "name": "超级管理员",
        "description": "系统超级管理员，拥有所有权限",
        "permissions": ["*"],
        "is_system": True,
    },
    {
        "role_id": "role_admin",
        "name": "管理员",
        "description": "系统管理员，拥有用户、角色、插件和系统管理权限",
        "permissions": [
            "user:*",
            "role:*",
            "plugin:*",
            "system:*",
        ],
        "is_system": True,
    },
    {
        "role_id": "role_trader",
        "name": "交易员",
        "description": "交易员，可以运行回测、选股和管理持仓",
        "permissions": [
            "backtest:*",
            "selection:*",
            "holdings:*",
            "risk:view",
        ],
        "is_system": True,
    },
    {
        "role_id": "role_viewer",
        "name": "观察者",
        "description": "观察者，只能查看数据",
        "permissions": [
            "user:view",
            "role:view",
            "plugin:view",
            "backtest:view",
            "selection:view",
            "holdings:view",
            "risk:view",
            "scheduler:view",
            "dingtalk:view",
        ],
        "is_system": True,
    },
]

"""Action API Endpoints

Provides unified entry point for running actions.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.action.runner import ActionRunner
from app.core.auth import AuthenticatedUser, require_permission

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/action", tags=["action"])

_action_runner: ActionRunner = None


def get_action_runner() -> ActionRunner:
    global _action_runner
    if _action_runner is None:
        _action_runner = ActionRunner()
    return _action_runner


class ActionRunRequest(BaseModel):
    """Request model for running an action."""
    command: str = Field(
        ...,
        description="Action type (run_backtest, run_selection, validate_plugin)"
    )
    instance: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional instance configuration"
    )
    param: Dict[str, Any] = Field(
        default_factory=dict,
        description="Command-specific parameters"
    )


class ActionRunResponse(BaseModel):
    """Response model for action run."""
    action_id: str
    success: bool
    error: str = None
    result: Dict[str, Any] = None


@router.post("/run", response_model=ActionRunResponse)
async def run_action(
    request: ActionRunRequest,
    current_user: AuthenticatedUser = Depends(require_permission("backtest:run")),
    runner: ActionRunner = Depends(get_action_runner),
):
    """
    Run an action through the unified entry point.

    Requires appropriate permission based on action type:
    - run_backtest: backtest:run
    - run_selection: selection:run
    - validate_plugin: plugin:manage

    Supported commands:
    - run_backtest: Execute a backtest task
    - run_selection: Run stock selection using Qlib model
    - validate_plugin: Validate a plugin package
    """
    command = request.command

    permission_map = {
        "run_backtest": "backtest:run",
        "run_selection": "selection:run",
        "validate_plugin": "plugin:manage",
    }

    required_permission = permission_map.get(command)
    if not required_permission:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown command: {command}. Supported: {list(permission_map.keys())}"
        )

    if not current_user.has_permission(required_permission):
        raise HTTPException(
            status_code=403,
            detail=f"Missing permission: {required_permission}"
        )

    action = {
        "command": command,
        "user_id": current_user.user_id,
        "instance": request.instance,
        "param": request.param,
    }

    try:
        result = await runner.run_action(action)

        return ActionRunResponse(
            action_id=result.get("action_id", ""),
            success=result.get("success", False),
            error=result.get("error"),
            result=result,
        )

    except Exception as e:
        logger.error(f"Failed to run action: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run action: {str(e)}"
        )

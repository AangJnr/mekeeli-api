
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, crud, models, security
from database import get_db

router = APIRouter()

class ToolExecution(schemas.BaseModel):
    tool_id: int
    parameters: dict

@router.post("/tools/run", dependencies=[Depends(security.get_current_active_user)])
def run_tool(
    tool_execution: ToolExecution,
    db: Session = Depends(get_db),
):
    tool = crud.get_tool(db, tool_id=tool_execution.tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    try:
        tool_code = json.loads(tool.content)
        # Execute the tool's code
        # NOTE: This is a security risk if the tool code is not trusted
        # In a real-world application, this should be handled with care
        # (e.g., using a sandboxed environment)
        exec_globals = {}
        exec(tool_code["script"], exec_globals)
        result = exec_globals["run"](tool_execution.parameters)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing tool: {e}")

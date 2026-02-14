"""WebSocket handler for realtime logs."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from src.config import settings
from src.core.security import validate_telegram_webapp_data
from src.shared.logger import log_broadcaster, logger

router = APIRouter()


@router.websocket("/ws/admin/logs")
async def websocket_logs(
    websocket: WebSocket,
    init_data: str = Query(...),
):
    """WebSocket endpoint for realtime logs. Only admins can connect."""
    try:
        # Validate init data
        data = validate_telegram_webapp_data(init_data)
        telegram_user = data["user"]
        telegram_id = telegram_user["id"]
        
        # Check if admin
        if telegram_id not in settings.admin_ids_list:
            await websocket.close(code=4003, reason="Admin access required")
            return
        
        # Accept connection
        await websocket.accept()
        
        # Register connection
        await log_broadcaster.connect(websocket)
        
        logger.info(f"Admin connected to logs WebSocket | admin_id={telegram_id}")
        
        try:
            # Keep connection alive
            while True:
                data = await websocket.receive_json()
                # Could implement filtering here
                if data.get("type") == "set_filter":
                    pass
                    
        except WebSocketDisconnect:
            logger.info(f"Admin disconnected from logs WebSocket | admin_id={telegram_id}")
        finally:
            await log_broadcaster.disconnect(websocket)
            
    except Exception as e:
        logger.error(f"WebSocket error | error={e}")
        try:
            await websocket.close(code=4000, reason=str(e))
        except:
            pass

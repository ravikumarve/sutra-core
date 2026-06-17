"""
Webhook API Routes
Endpoints for handling webhooks from external services
"""

import logging
import hmac
import hashlib
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request, Response, Query, Header
from fastapi.responses import JSONResponse

from src.api.schemas.common import BaseResponse, WhatsAppWebhookPayload
from src.api.services.whatsapp import whatsapp_api
from src.agents.liaison.liaison_agent import LiaisonAgent
from src.agents.coordinator import agent_coordinator
from src.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/whatsapp")
async def verify_whatsapp_webhook(
    mode: str = Query(..., description="Webhook mode"),
    token: str = Query(..., description="Verification token"),
    challenge: str = Query(..., description="Challenge string")
):
    """
    Verify WhatsApp webhook
    Called by Meta during webhook setup
    """
    try:
        # Verify webhook token
        result = await whatsapp_api.verify_webhook_token(mode, token, challenge)
        
        if result:
            logger.info("WhatsApp webhook verified successfully")
            return Response(content=result, media_type="text/plain")
        else:
            logger.warning("WhatsApp webhook verification failed")
            raise HTTPException(status_code=403, detail="Verification failed")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying WhatsApp webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/whatsapp")
async def handle_whatsapp_webhook(
    request: Request,
    x_hub_signature: Optional[str] = Header(None, alias="X-Hub-Signature-256")
):
    """
    Handle WhatsApp webhook
    Called by Meta when new messages arrive
    """
    try:
        # Get raw payload
        payload = await request.body()
        
        # Verify signature
        if x_hub_signature:
            is_valid = await whatsapp_api.verify_webhook_signature(
                x_hub_signature,
                payload
            )
            
            if not is_valid:
                logger.warning("Invalid webhook signature")
                raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Parse webhook payload
        webhook_data = await request.json()
        
        logger.info(f"Received WhatsApp webhook: {webhook_data}")
        
        # Process webhook
        await _process_whatsapp_webhook(webhook_data)
        
        return JSONResponse(
            content={"status": "success"},
            status_code=200
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling WhatsApp webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def _process_whatsapp_webhook(webhook_data: Dict[str, Any]) -> None:
    """
    Process WhatsApp webhook data
    """
    try:
        # Get entry data
        entries = webhook_data.get("entry", [])
        
        for entry in entries:
            # Get changes
            changes = entry.get("changes", [])
            
            for change in changes:
                # Get value
                value = change.get("value", {})
                
                # Get phone number ID
                phone_number_id = value.get("metadata", {}).get("phone_number_id", "")
                
                # Get messages
                messages = value.get("messages", [])
                
                for message in messages:
                    # Get message details
                    message_id = message.get("id", "")
                    message_type = message.get("type", "")
                    from_number = message.get("from", "")
                    timestamp = message.get("timestamp", "")
                    
                    logger.info(f"Processing message {message_id} from {from_number}")
                    
                    # Determine tenant ID from phone number
                    # TODO: Implement proper tenant lookup
                    tenant_id = "default"
                    
                    # Get tenant agents
                    tenant_status = await agent_coordinator.get_tenant_status(tenant_id)
                    
                    if not tenant_status:
                        logger.error(f"Tenant {tenant_id} not found")
                        continue
                    
                    # Get Liaison agent
                    liaison_agent = tenant_status["agents"].get("liaison")
                    
                    if not liaison_agent:
                        logger.error("Liaison agent not found")
                        continue
                    
                    # Process message based on type
                    if message_type == "text":
                        await _process_text_message(
                            tenant_id=tenant_id,
                            message=message,
                            from_number=from_number
                        )
                    elif message_type == "audio":
                        await _process_audio_message(
                            tenant_id=tenant_id,
                            message=message,
                            from_number=from_number
                        )
                    elif message_type == "image":
                        await _process_image_message(
                            tenant_id=tenant_id,
                            message=message,
                            from_number=from_number
                        )
                    elif message_type == "video":
                        await _process_video_message(
                            tenant_id=tenant_id,
                            message=message,
                            from_number=from_number
                        )
                    elif message_type == "document":
                        await _process_document_message(
                            tenant_id=tenant_id,
                            message=message,
                            from_number=from_number
                        )
                    else:
                        logger.warning(f"Unsupported message type: {message_type}")
                    
                    # Mark message as read
                    await whatsapp_api.mark_message_as_read(message_id)
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}")
        raise


async def _process_text_message(
    tenant_id: str,
    message: Dict[str, Any],
    from_number: str
) -> None:
    """
    Process text message
    """
    try:
        # Get text content
        text_content = message.get("text", {})
        text = text_content.get("body", "")
        
        logger.info(f"Processing text message: {text}")
        
        # TODO: Send to Liaison agent for processing
        # For now, just log the message
        
        logger.info(f"Text message processed for tenant {tenant_id}")
        
    except Exception as e:
        logger.error(f"Error processing text message: {e}")
        raise


async def _process_audio_message(
    tenant_id: str,
    message: Dict[str, Any],
    from_number: str
) -> None:
    """
    Process audio message
    """
    try:
        # Get audio content
        audio_content = message.get("audio", {})
        audio_id = audio_content.get("id", "")
        mime_type = audio_content.get("mime_type", "")
        
        logger.info(f"Processing audio message: {audio_id}")
        
        # Download audio
        audio_data = await whatsapp_api.download_media(audio_id)
        
        # TODO: Transcribe audio using Whisper
        # For now, just log the message
        
        logger.info(f"Audio message processed for tenant {tenant_id}")
        
    except Exception as e:
        logger.error(f"Error processing audio message: {e}")
        raise


async def _process_image_message(
    tenant_id: str,
    message: Dict[str, Any],
    from_number: str
) -> None:
    """
    Process image message
    """
    try:
        # Get image content
        image_content = message.get("image", {})
        image_id = image_content.get("id", "")
        caption = image_content.get("caption", "")
        
        logger.info(f"Processing image message: {image_id}")
        
        # TODO: Process image
        # For now, just log the message
        
        logger.info(f"Image message processed for tenant {tenant_id}")
        
    except Exception as e:
        logger.error(f"Error processing image message: {e}")
        raise


async def _process_video_message(
    tenant_id: str,
    message: Dict[str, Any],
    from_number: str
) -> None:
    """
    Process video message
    """
    try:
        # Get video content
        video_content = message.get("video", {})
        video_id = video_content.get("id", "")
        caption = video_content.get("caption", "")
        
        logger.info(f"Processing video message: {video_id}")
        
        # TODO: Process video
        # For now, just log the message
        
        logger.info(f"Video message processed for tenant {tenant_id}")
        
    except Exception as e:
        logger.error(f"Error processing video message: {e}")
        raise


async def _process_document_message(
    tenant_id: str,
    message: Dict[str, Any],
    from_number: str
) -> None:
    """
    Process document message
    """
    try:
        # Get document content
        document_content = message.get("document", {})
        document_id = document_content.get("id", "")
        filename = document_content.get("filename", "")
        caption = document_content.get("caption", "")
        
        logger.info(f"Processing document message: {document_id}")
        
        # TODO: Process document
        # For now, just log the message
        
        logger.info(f"Document message processed for tenant {tenant_id}")
        
    except Exception as e:
        logger.error(f"Error processing document message: {e}")
        raise
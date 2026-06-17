"""
WhatsApp Cloud API Service
Handles communication with Meta WhatsApp Cloud API
"""

import logging
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.config.settings import settings

logger = logging.getLogger(__name__)


class WhatsAppCloudAPI:
    """
    WhatsApp Cloud API client
    Handles sending and receiving WhatsApp messages
    """
    
    def __init__(self):
        self.base_url = f"https://graph.facebook.com/v18.0"
        self.phone_number_id = settings.META_PHONE_NUMBER_ID
        self.access_token = settings.META_ACCESS_TOKEN
        self.app_secret = settings.META_APP_SECRET
        self.verify_token = settings.META_VERIFY_TOKEN
        
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
        )
    
    async def send_text_message(
        self,
        to: str,
        text: str,
        preview_url: bool = False
    ) -> Dict[str, Any]:
        """
        Send text message via WhatsApp
        """
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {
                    "body": text,
                    "preview_url": preview_url
                }
            }
            
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Text message sent to {to}: {result.get('messages', [{}])[0].get('id')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending text message: {e}")
            raise
    
    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str = "en",
        components: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send template message via WhatsApp
        """
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language_code
                    }
                }
            }
            
            if components:
                payload["template"]["components"] = components
            
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Template message sent to {to}: {result.get('messages', [{}])[0].get('id')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending template message: {e}")
            raise
    
    async def send_media_message(
        self,
        to: str,
        media_type: str,
        media_url: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send media message via WhatsApp
        """
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": media_type,
                f"{media_type}": {
                    "link": media_url
                }
            }
            
            if caption:
                payload[f"{media_type}"]["caption"] = caption
            
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Media message sent to {to}: {result.get('messages', [{}])[0].get('id')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending media message: {e}")
            raise
    
    async def send_location_message(
        self,
        to: str,
        latitude: float,
        longitude: float,
        name: Optional[str] = None,
        address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send location message via WhatsApp
        """
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "location",
                "location": {
                    "latitude": latitude,
                    "longitude": longitude
                }
            }
            
            if name:
                payload["location"]["name"] = name
            
            if address:
                payload["location"]["address"] = address
            
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Location message sent to {to}: {result.get('messages', [{}])[0].get('id')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending location message: {e}")
            raise
    
    async def send_contact_message(
        self,
        to: str,
        contacts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Send contact message via WhatsApp
        """
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "contacts",
                "contacts": contacts
            }
            
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Contact message sent to {to}: {result.get('messages', [{}])[0].get('id')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending contact message: {e}")
            raise
    
    async def mark_message_as_read(
        self,
        message_id: str
    ) -> Dict[str, Any]:
        """
        Mark message as read
        """
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Message {message_id} marked as read")
            
            return result
            
        except Exception as e:
            logger.error(f"Error marking message as read: {e}")
            raise
    
    async def get_message_info(
        self,
        message_id: str
    ) -> Dict[str, Any]:
        """
        Get message information
        """
        try:
            url = f"{self.base_url}/{message_id}"
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Retrieved message info for {message_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting message info: {e}")
            raise
    
    async def download_media(
        self,
        media_id: str
    ) -> bytes:
        """
        Download media file
        """
        try:
            # Get media URL
            url = f"{self.base_url}/{media_id}"
            response = await self.client.get(url)
            response.raise_for_status()
            
            media_url = response.json().get("url")
            
            # Download media
            media_response = await self.client.get(media_url)
            media_response.raise_for_status()
            
            logger.info(f"Downloaded media {media_id}")
            
            return media_response.content
            
        except Exception as e:
            logger.error(f"Error downloading media: {e}")
            raise
    
    async def verify_webhook_signature(
        self,
        signature: str,
        payload: bytes
    ) -> bool:
        """
        Verify webhook signature
        """
        try:
            import hmac
            import hashlib
            
            # Calculate expected signature
            expected_signature = hmac.new(
                self.app_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(
                f"sha256={expected_signature}",
                signature
            )
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    async def verify_webhook_token(
        self,
        mode: str,
        token: str,
        challenge: str
    ) -> Optional[str]:
        """
        Verify webhook token for setup
        """
        try:
            if mode == "subscribe" and token == self.verify_token:
                return challenge
            return None
            
        except Exception as e:
            logger.error(f"Error verifying webhook token: {e}")
            return None
    
    async def close(self) -> None:
        """
        Close HTTP client
        """
        await self.client.aclose()
        logger.info("WhatsApp Cloud API client closed")


# Global instance
whatsapp_api = WhatsAppCloudAPI()
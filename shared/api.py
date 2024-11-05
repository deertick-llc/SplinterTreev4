import os
import logging
import time
import json
import asyncio
import sqlite3
import base64
from typing import Dict, Any, List, Union, AsyncGenerator
import aiohttp
import backoff
from urllib.parse import urlparse, urljoin
from config import OPENPIPE_API_KEY, OPENROUTER_API_KEY, OPENPIPE_API_URL
from openai import AsyncOpenAI

class API:
    def __init__(self):
        # Initialize aiohttp session
        self.session = aiohttp.ClientSession()
        
        # Initialize OpenPipe client
        self.openpipe_client = AsyncOpenAI(
            api_key=OPENPIPE_API_KEY,
            base_url=OPENPIPE_API_URL  # Base URL already includes /api/v1
        )

        # Initialize OpenRouter client
        self.openrouter_client = AsyncOpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )

        # Connect to SQLite database and apply schema
        try:
            self.db_conn = sqlite3.connect('databases/interaction_logs.db')
            self.db_cursor = self.db_conn.cursor()
            self._apply_schema()
            logging.info("[API] Connected to database and applied schema")
        except Exception as e:
            logging.error(f"[API] Failed to connect to database or apply schema: {str(e)}")
            self.db_conn = None
            self.db_cursor = None

    def _apply_schema(self):
        """Apply database schema"""
        try:
            with open('databases/schema.sql', 'r') as schema_file:
                schema_sql = schema_file.read()
            self.db_cursor.executescript(schema_sql)
            self.db_conn.commit()
            logging.info("[API] Successfully applied database schema")
        except Exception as e:
            logging.error(f"[API] Failed to apply database schema: {str(e)}")
            raise

    async def _download_image(self, url: str) -> bytes:
        """Download image from URL"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    logging.error(f"[API] Failed to download image. Status code: {response.status}")
                    return None
        except Exception as e:
            logging.error(f"[API] Error downloading image: {str(e)}")
            return None

    async def _convert_image_to_base64(self, url: str) -> str:
        """Convert image URL to base64"""
        try:
            image_data = await self._download_image(url)
            if image_data:
                # Detect MIME type based on image data
                mime_type = self._detect_mime_type(image_data)
                base64_image = base64.b64encode(image_data).decode('utf-8')
                return f"data:{mime_type};base64,{base64_image}"
            return None
        except Exception as e:
            logging.error(f"[API] Error converting image to base64: {str(e)}")
            return None

    def _detect_mime_type(self, image_data: bytes) -> str:
        """Detect MIME type of image data"""
        # Common image signatures
        signatures = {
            b'\xFF\xD8\xFF': 'image/jpeg',
            b'\x89PNG\r\n\x1a\n': 'image/png',
            b'GIF87a': 'image/gif',
            b'GIF89a': 'image/gif',
            b'RIFF': 'image/webp'
        }
        
        for signature, mime_type in signatures.items():
            if image_data.startswith(signature):
                return mime_type
        
        return 'application/octet-stream'  # Default fallback

    async def _validate_message_roles(self, messages: List[Dict]) -> List[Dict]:
        """Validate and normalize message roles for API compatibility"""
        valid_roles = {"system", "user", "assistant"}
        normalized_messages = []
        
        for msg in messages:
            role = msg.get('role', '').lower()
            
            # Skip messages with invalid roles
            if role not in valid_roles:
                logging.warning(f"[API] Skipping message with invalid role: {role}")
                continue
            
            # Create normalized message
            normalized_msg = {
                "role": role,
                "content": msg.get('content', '')
            }
            
            # Handle multimodal content
            if isinstance(normalized_msg['content'], list):
                # Verify and convert image URLs to base64
                valid_content = []
                for item in normalized_msg['content']:
                    if isinstance(item, dict) and 'type' in item:
                        if item['type'] == 'text' and 'text' in item:
                            valid_content.append(item)
                        elif item['type'] == 'image_url' and 'image_url' in item:
                            # Convert image URL to base64 with proper awaiting
                            base64_image = await self._convert_image_to_base64(item['image_url'])
                            if base64_image:
                                valid_content.append({
                                    "type": "image_url",
                                    "image_url": base64_image
                                })
                normalized_msg['content'] = valid_content
            
            normalized_messages.append(normalized_msg)
        
        return normalized_messages

    async def _stream_openrouter_request(self, messages, model, temperature, max_tokens):
        """Stream responses from OpenRouter API using OpenAI client"""
        logging.debug(f"[API] Making OpenRouter streaming request to model: {model}")
        
        try:
            # Validate and normalize message roles
            validated_messages = self._validate_message_roles(messages)
            
            stream = await self.openrouter_client.chat.completions.create(
                model=model,
                messages=validated_messages,
                temperature=temperature if temperature is not None else 1,
                max_tokens=max_tokens,
                stream=True,
                store=True
            )
            requested_at = int(time.time() * 1000)
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

            received_at = int(time.time() * 1000)

            # Log request to database after completion
            completion_obj = {
                'choices': [{
                    'message': {
                        'content': "Streaming response completed"
                    }
                }]
            }
            await self.report(
                requested_at=requested_at,
                received_at=received_at,
                req_payload={
                    "model": model,
                    "messages": validated_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                resp_payload=completion_obj,
                status_code=200,
                tags={"source": "openrouter"}
            )
        except Exception as e:
            error_message = str(e)
            logging.error(f"[API] OpenRouter streaming error: {error_message}")
            raise Exception(f"OpenRouter API error: {error_message}")

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=5,
        max_time=60
    )
    async def call_openrouter(self, messages: List[Dict[str, Union[str, List[Dict[str, Any]]]]], model: str, temperature: float = None, stream: bool = False) -> Union[Dict, AsyncGenerator[str, None]]:
        try:
            # Check if any message contains vision content
            has_vision_content = any(
                isinstance(msg.get('content'), list) and 
                any(content.get('type') == 'image_url' for content in msg['content'])
                for msg in messages
            )
            logging.debug(f"[API] Message contains vision content: {has_vision_content}")

            # Configure parameters based on content type
            max_tokens = 2000 if has_vision_content else 1000
            
            # Use provided temperature or default based on content type
            if temperature is None:
                temperature = 0.5 if has_vision_content else 0.7
            logging.debug(f"[API] Using max_tokens={max_tokens}, temperature={temperature}")

            # Log request details
            logging.debug(f"[API] OpenRouter request messages structure:")
            for msg in messages:
                if isinstance(msg.get('content'), list):
                    logging.debug(f"[API] Message type: multimodal")
                    text_parts = [c['text'] for c in msg['content'] if c['type'] == 'text']
                    image_parts = [c for c in msg['content'] if c['type'] == 'image_url']
                    logging.debug(f"[API] Text parts: {text_parts}")
                    logging.debug(f"[API] Number of images: {len(image_parts)}")
                else:
                    logging.debug(f"[API] Message type: text")
                    logging.debug(f"[API] Content: {msg.get('content')}")

            if stream:
                return self._stream_openrouter_request(messages, model, temperature, max_tokens)
            else:
                # Validate and normalize message roles
                validated_messages = self._validate_message_roles(messages)
                
                # Non-streaming request
                requested_at = int(time.time() * 1000)
                response = await self.openrouter_client.chat.completions.create(
                    model=model,
                    messages=validated_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    store=True
                )
                received_at = int(time.time() * 1000)

                result = {
                    'choices': [{
                        'message': {
                            'content': response.choices[0].message.content
                        }
                    }]
                }

                # Log the interaction
                await self.report(
                    requested_at=requested_at,
                    received_at=received_at,
                    req_payload={
                        "model": model,
                        "messages": validated_messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    },
                    resp_payload=result,
                    status_code=200,
                    tags={"source": "openrouter"}
                )

                return result

        except Exception as e:
            error_message = str(e)
            if "insufficient_quota" in error_message.lower():
                logging.error("[API] OpenRouter credits depleted")
                raise Exception("⚠️ OpenRouter credits depleted. Please visit https://openrouter.ai/credits to add more.")
            elif "invalid_api_key" in error_message.lower():
                logging.error("[API] Invalid OpenRouter API key")
                raise Exception("🔑 Invalid OpenRouter API key. Please check your configuration.")
            elif "rate_limit_exceeded" in error_message.lower():
                logging.error("[API] OpenRouter rate limit exceeded")
                raise Exception("⏳ Rate limit exceeded. Please try again later.")
            elif isinstance(e, (aiohttp.ClientError, asyncio.TimeoutError)):
                logging.error(f"[API] Connection error: {str(e)}")
                raise Exception("🌐 Connection error. Please check your internet connection and try again.")
            else:
                logging.error(f"[API] OpenRouter error: {error_message}")
                raise Exception(f"OpenRouter API error: {error_message}")

    async def _stream_openpipe_request(self, messages, model, temperature, max_tokens):
        """Stream responses from OpenPipe API"""
        logging.debug(f"[API] Making OpenPipe streaming request to model: {model}")
        
        try:
            # Validate and normalize message roles
            validated_messages = self._validate_message_roles(messages)
            
            stream = await self.openpipe_client.chat.completions.create(
                model=model,
                messages=validated_messages,
                temperature=temperature if temperature is not None else 0.7,
                max_tokens=max_tokens if max_tokens is not None else 1000,
                stream=True,
                store=True
            )
            requested_at = int(time.time() * 1000)
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

            received_at = int(time.time() * 1000)

            # Log request to database after completion
            completion_obj = {
                'choices': [{
                    'message': {
                        'content': "Streaming response completed"
                    }
                }]
            }
            await self.report(
                requested_at=requested_at,
                received_at=received_at,
                req_payload={
                    "model": model,
                    "messages": validated_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                resp_payload=completion_obj,
                status_code=200,
                tags={"source": "openpipe"}
            )
        except Exception as e:
            error_message = str(e)
            logging.error(f"[API] OpenPipe streaming error: {error_message}")
            raise Exception(f"OpenPipe API error: {error_message}")

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=5,
        max_time=60
    )
    async def call_openpipe(self, messages: List[Dict[str, Union[str, List[Dict[str, Any]]]]], model: str, temperature: float = None, stream: bool = False, max_tokens: int = None) -> Union[Dict, AsyncGenerator[str, None]]:
        try:
            logging.debug(f"[API] Making OpenPipe request to model: {model}")
            logging.debug(f"[API] Request messages structure:")
            for msg in messages:
                logging.debug(f"[API] Message role: {msg.get('role')}")
                logging.debug(f"[API] Message content: {msg.get('content')}")

            if stream:
                return self._stream_openpipe_request(messages, model, temperature, max_tokens)
            else:
                # Validate and normalize message roles
                validated_messages = self._validate_message_roles(messages)
                
                requested_at = int(time.time() * 1000)
                response = await self.openpipe_client.chat.completions.create(
                    model=model,
                    messages=validated_messages,
                    temperature=temperature if temperature is not None else 0.7,
                    max_tokens=max_tokens if max_tokens is not None else 1000,
                    store=True
                )
                received_at = int(time.time() * 1000)

                result = {
                    'choices': [{
                        'message': {
                            'content': response.choices[0].message.content
                        }
                    }]
                }

                # Log the interaction
                await self.report(
                    requested_at=requested_at,
                    received_at=received_at,
                    req_payload={
                        "model": model,
                        "messages": validated_messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    },
                    resp_payload=result,
                    status_code=200,
                    tags={"source": "openpipe"}
                )

                return result

        except Exception as e:
            error_message = str(e)
            logging.error(f"[API] OpenPipe error: {error_message}")
            raise Exception(f"OpenPipe API error: {error_message}")

    async def report(self, requested_at: int, received_at: int, req_payload: Dict, resp_payload: Dict, status_code: int, tags: Dict = None):
        """Report interaction metrics"""
        try:
            if self.db_conn is None or self.db_cursor is None:
                logging.error("[API] Database connection not available. Skipping logging.")
                return

            # Add timestamp to tags
            if tags is None:
                tags = {}
            tags_str = json.dumps(tags)

            # Prepare SQL statement
            sql = "INSERT INTO logs (requested_at, received_at, request, response, status_code, tags) VALUES (?, ?, ?, ?, ?, ?)"
            values = (requested_at, received_at, json.dumps(req_payload), json.dumps(resp_payload), status_code, tags_str)

            # Execute SQL statement
            self.db_cursor.execute(sql, values)
            self.db_conn.commit()
            logging.debug(f"[API] Logged interaction with status code {status_code}")

        except Exception as e:
            logging.error(f"[API] Failed to report interaction: {str(e)}")

    async def close(self):
        await self.session.close()
        if self.db_conn:
            self.db_conn.close()

api = API()

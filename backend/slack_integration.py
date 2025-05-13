"""
Slack Bot Integration for AI Agents Framework

This module provides functionality to deploy AI agents as Slack bots using the Slack Bolt framework.
It manages bot lifecycles, handles message processing, and provides API endpoints for controlling bots.
"""

import os
import asyncio
import logging
import threading
from typing import Dict, List, Optional, Any, Tuple
import time
import json
import re
from datetime import datetime
import subprocess
import sys
import sqlite3

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

import db_models
# Change direct import to module import to avoid circular imports
import agent_utils
from agents import Agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to store active Slack bots
active_slack_bots: Dict[str, 'SlackBot'] = {}

class SlackBot:
    """
    Manages a Slack bot instance for a specific agent.
    
    This class encapsulates the functionality for running a Slack bot,
    including starting/stopping the bot, handling incoming messages, and
    maintaining conversation state.
    """
    
    def __init__(self, agent_name: str, bot_token: str, app_token: str):
        """
        Initialize a new Slack bot for the specified agent.
        
        Args:
            agent_name: The name of the agent this bot represents
            bot_token: Slack Bot User OAuth Token
            app_token: Slack App-Level Token
        """
        self.agent_name = agent_name
        self.bot_token = bot_token
        self.app_token = app_token
        self.app = App(token=bot_token)
        self.handler = SocketModeHandler(self.app, app_token)
        self.thread = None
        self.running = False
        self.conversations: Dict[str, str] = {}  # Maps channel_ts to conversation_id
        
        # We'll skip the agent initialization for now and handle it when needed
        # This avoids the need for agent_config at initialization
        self.agent = None  # Will be initialized when needed
        
        # Register event handlers
        self._register_event_handlers()
    
    def _register_event_handlers(self):
        """Register all necessary Slack event handlers."""
        # Handle normal messages in channels/DMs
        @self.app.event("message")
        def handle_message_events(body, say, logger):
            try:
                # Get the event data
                event = body["event"]
                
                # Don't respond to bot messages to avoid loops
                if event.get("bot_id") or event.get("subtype") == "bot_message":
                    return
                
                # Extract message details
                user = event.get("user")
                text = event.get("text", "").strip()
                channel = event.get("channel")
                ts = event.get("ts")
                thread_ts = event.get("thread_ts", ts)
                
                # Check if this is a mention or DM
                bot_user_id = None
                try:
                    bot_info = self.app.client.auth_test()
                    bot_user_id = bot_info["user_id"]
                except Exception as e:
                    logger.error(f"Could not get bot user ID: {e}")
                
                is_dm = channel.startswith("D")
                has_mention = bot_user_id and f"<@{bot_user_id}>" in text
                
                # For channel messages, ONLY handle DMs or non-mention messages
                # This prevents double-responses when app_mention is also triggered
                if not is_dm and has_mention:
                    logger.info(f"Ignoring mention in channel that will be handled by app_mention event: {text}")
                    return
                
                # Only respond to DMs or messages directed at the bot
                if not is_dm and not has_mention:
                    return
                
                # Strip out the mention from the text if present
                if has_mention:
                    text = text.replace(f"<@{bot_user_id}>", "").strip()
                
                # Use thread_ts as the key for the conversation
                conversation_key = f"{channel}:{thread_ts}"
                
                # Check if we have an existing conversation_id for this thread
                conversation_id = self.conversations.get(conversation_key)
                
                logger.info(f"Received message from {user} in {channel}: {text}")
                
                # Send typing indicator
                self._send_typing_indicator(channel, thread_ts)
                
                # Process message in a separate thread to avoid blocking
                thread = threading.Thread(
                    target=self._process_message_async,
                    args=(text, conversation_id, say, channel, thread_ts, conversation_key)
                )
                thread.start()
                
            except Exception as e:
                logger.error(f"Error handling message event: {e}")
        
        # Handle app_mention events specifically
        @self.app.event("app_mention")
        def handle_mention_events(body, say, logger):
            try:
                # Get the event data
                event = body["event"]
                
                # Extract message details
                user = event.get("user")
                text = event.get("text", "").strip()
                channel = event.get("channel")
                ts = event.get("ts")
                thread_ts = event.get("thread_ts", ts)
                
                # Strip out the mention from the text
                try:
                    bot_info = self.app.client.auth_test()
                    bot_user_id = bot_info["user_id"]
                    text = text.replace(f"<@{bot_user_id}>", "").strip()
                except Exception as e:
                    logger.error(f"Could not get bot user ID: {e}")
                
                # Use thread_ts as the key for the conversation
                conversation_key = f"{channel}:{thread_ts}"
                
                # Check if we have an existing conversation_id for this thread
                conversation_id = self.conversations.get(conversation_key)
                
                logger.info(f"Received mention from {user} in {channel}: {text}")
                
                # Send typing indicator
                self._send_typing_indicator(channel, thread_ts)
                
                # Process message in a separate thread to avoid blocking
                thread = threading.Thread(
                    target=self._process_message_async,
                    args=(text, conversation_id, say, channel, thread_ts, conversation_key)
                )
                thread.start()
                
            except Exception as e:
                logger.error(f"Error handling app_mention event: {e}")
    
    def _process_message_async(self, text, conversation_id, say, channel, thread_ts, conversation_key):
        """Process a message asynchronously and send response."""
        try:
            # Create event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Log before interacting with agent
            logger.info(f"Calling agent '{self.agent_name}' with message: '{text}' (conversation_id: {conversation_id})")
            
            # Call the agent
            result = loop.run_until_complete(agent_utils.interact_with_agent(
                self.agent_name,
                text,
                conversation_id
            ))
            
            # Log result for debugging
            logger.info(f"Agent response type: {type(result)}")
            logger.debug(f"Raw agent response: {result}")
            
            # Check if result is a string or dict and handle accordingly
            if isinstance(result, str):
                # For backward compatibility with older versions that return strings
                response = result
                new_conversation_id = conversation_id
                logger.info(f"Processed string response from agent (length: {len(response)})")
            elif isinstance(result, dict):
                # For newer versions that return dictionaries
                response = result.get("response", "Sorry, I didn't get a proper response from the agent")
                new_conversation_id = result.get("conversation_id", conversation_id)
                logger.info(f"Processed dictionary response from agent with keys: {list(result.keys())}")
            else:
                # Fallback if result is neither string nor dict
                response = str(result)
                new_conversation_id = conversation_id
                logger.warning(f"Unexpected response type from agent: {type(result)}")
            
            # Save conversation_id for this thread if it's not None
            if new_conversation_id is not None:
                self.conversations[conversation_key] = new_conversation_id
                logger.info(f"Saved conversation_id {new_conversation_id} for channel:thread {conversation_key}")
            
            # Send the response back to Slack
            say(text=response, thread_ts=thread_ts)
            logger.info(f"Sent response to Slack (length: {len(response)})")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)  # Include stack trace
            say(text=f"Sorry, I encountered an error: {str(e)}", thread_ts=thread_ts)
        finally:
            # Clean up the event loop
            try:
                loop.close()
            except:
                pass
    
    def start(self) -> bool:
        """
        Start the Slack bot in a separate thread.
        
        Returns:
            bool: True if the bot was started successfully, False otherwise
        """
        if self.running:
            logger.info(f"Slack bot for {self.agent_name} is already running")
            return True
        
        try:
            logger.info(f"Starting Slack bot for {self.agent_name}")
            self.thread = threading.Thread(target=self._run_bot)
            self.thread.daemon = True
            self.thread.start()
            self.running = True
            return True
        except Exception as e:
            logger.error(f"Failed to start Slack bot for {self.agent_name}: {e}")
            return False
    
    def stop(self) -> bool:
        """
        Stop the Slack bot.
        
        Returns:
            bool: True if the bot was stopped successfully, False otherwise
        """
        if not self.running:
            logger.info(f"Slack bot for {self.agent_name} is not running")
            return True
        
        try:
            logger.info(f"Stopping Slack bot for {self.agent_name}")
            self.running = False
            if self.thread:
                # Try to signal a clean shutdown
                try:
                    if hasattr(self.handler, 'socket_mode_request_listeners'):
                        # Clear all listeners to help the thread exit
                        self.handler.socket_mode_request_listeners = []
                except:
                    pass
                
                # Wait a short time for the thread to exit
                self.thread.join(timeout=2.0)
                self.thread = None
            return True
        except Exception as e:
            logger.error(f"Failed to stop Slack bot for {self.agent_name}: {e}")
            return False
    
    def _run_bot(self) -> None:
        """Run the Slack bot's socket mode handler (internal method)."""
        try:
            # Log bot start
            logger.info(f"Slack bot for {self.agent_name} is now listening for events")
            
            # Start the handler - this will block until the app is stopped
            self.handler.start()
        except Exception as e:
            logger.error(f"Error in Slack bot thread for {self.agent_name}: {e}")
            self.running = False
    
    async def _handle_message(self, message: Dict[str, Any], say: Any) -> None:
        """
        Handle incoming messages from Slack.
        
        Args:
            message: The incoming Slack message
            say: The Slack say function to respond
        """
        # Ignore bot messages to prevent loops
        if message.get("bot_id") or message.get("subtype") == "bot_message":
            return
        
        user = message.get("user")
        text = message.get("text", "").strip()
        channel = message.get("channel")
        ts = message.get("ts")
        thread_ts = message.get("thread_ts", ts)
        
        # Use thread_ts as the key for the conversation
        conversation_key = f"{channel}:{thread_ts}"
        
        # Check if we have an existing conversation_id for this thread
        conversation_id = self.conversations.get(conversation_key)
        
        logger.info(f"Received message from {user} in {channel}: {text}")
        
        # Typing indicator
        self._send_typing_indicator(channel, thread_ts)
        
        try:
            # Log before interacting with agent
            logger.info(f"Calling agent '{self.agent_name}' with message: '{text}' (conversation_id: {conversation_id})")
            
            # Get response from agent
            result = await agent_utils.interact_with_agent(
                self.agent_name,
                text,
                conversation_id
            )
            
            # Log result for debugging
            logger.info(f"Agent response type: {type(result)}")
            logger.debug(f"Raw agent response: {result}")
            
            # Check if result is a string or dict and handle accordingly
            if isinstance(result, str):
                # For backward compatibility with older versions that return strings
                response = result
                new_conversation_id = conversation_id
                logger.info(f"Processed string response from agent (length: {len(response)})")
            elif isinstance(result, dict):
                # For newer versions that return dictionaries
                response = result.get("response", "Sorry, I didn't get a proper response from the agent")
                new_conversation_id = result.get("conversation_id", conversation_id)
                logger.info(f"Processed dictionary response from agent with keys: {list(result.keys())}")
            else:
                # Fallback if result is neither string nor dict
                response = str(result)
                new_conversation_id = conversation_id
                logger.warning(f"Unexpected response type from agent: {type(result)}")
            
            # Save conversation_id for this thread if it's not None
            if new_conversation_id is not None:
                self.conversations[conversation_key] = new_conversation_id
                logger.info(f"Saved conversation_id {new_conversation_id} for channel:thread {conversation_key}")
            
            # Send the response back to Slack
            await say(text=response, thread_ts=thread_ts)
            logger.info(f"Sent response to Slack (length: {len(response)})")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)  # Include stack trace
            await say(text=f"Sorry, I encountered an error: {str(e)}", thread_ts=thread_ts)
    
    def _send_typing_indicator(self, channel: str, thread_ts: Optional[str] = None) -> None:
        """
        Send a typing indicator to the channel.
        
        Args:
            channel: The channel ID
            thread_ts: Optional thread timestamp for replying in a thread
        """
        try:
            # Try to use the typing indicator API
            self.app.client.chat_postMessage(
                channel=channel,
                text="...",
                thread_ts=thread_ts,
                mrkdwn=True
            )
        except Exception as e:
            logger.error(f"Error sending typing indicator: {e}")


def ensure_slack_table_exists():
    """
    Ensure the slack_bots table exists in the database.
    
    Returns:
        bool: True if table exists or was created, False otherwise
    """
    try:
        # First try using our dedicated script
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ensure_slack_table.py")
        
        if os.path.exists(script_path):
            logger.info(f"Running ensure_slack_table.py script at {script_path}")
            subprocess.run([sys.executable, script_path], check=False)
            return True
        
        # Fall back to direct SQLite approach if script not found
        db_paths = ["./app.db", "../app.db", "./data/agents.db", "../data/agents.db"]
        
        for db_path in db_paths:
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check if table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='slack_bots';")
                if not cursor.fetchone():
                    # Create table
                    logger.info(f"Creating slack_bots table in {db_path}")
                    cursor.execute("""
                    CREATE TABLE slack_bots (
                        id INTEGER PRIMARY KEY,
                        agent_name TEXT UNIQUE,
                        bot_token TEXT NOT NULL,
                        app_token TEXT NOT NULL,
                        status TEXT DEFAULT 'stopped',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """)
                    
                    # Create an index on agent_name
                    cursor.execute("CREATE UNIQUE INDEX ix_slack_bots_agent_name ON slack_bots (agent_name);")
                    conn.commit()
                
                conn.close()
                return True
        
        # Create a new database if none found
        logger.info("No existing database found, creating app.db")
        conn = sqlite3.connect("app.db")
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE slack_bots (
            id INTEGER PRIMARY KEY,
            agent_name TEXT UNIQUE,
            bot_token TEXT NOT NULL,
            app_token TEXT NOT NULL,
            status TEXT DEFAULT 'stopped',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        cursor.execute("CREATE UNIQUE INDEX ix_slack_bots_agent_name ON slack_bots (agent_name);")
        conn.commit()
        conn.close()
        return True
    
    except Exception as e:
        logger.error(f"Error ensuring slack_bots table exists: {e}")
        return False


async def deploy_agent_to_slack(agent_name: str, bot_token: str, app_token: str, db_session: AsyncSession) -> Dict[str, Any]:
    """
    Deploy an agent as a Slack bot.
    
    Args:
        agent_name: The name of the agent to deploy
        bot_token: Slack Bot User OAuth Token
        app_token: Slack App-Level Token
        db_session: Database session
        
    Returns:
        Dict with success status and message
    """
    try:
        # CRITICAL: Ensure the slack_bots table exists before any operations
        ensure_slack_table_exists()
        
        # Check if agent exists in the database
        try:
            agent_query = select(db_models.Agent).where(db_models.Agent.name == agent_name)
            agent_result = await db_session.execute(agent_query)
            agent_record = agent_result.scalars().first()
            
            if not agent_record:
                return {"success": False, "message": f"Agent '{agent_name}' not found in database"}
        except Exception as e:
            logger.error(f"Error checking agent existence: {e}")
            # Continue anyway, as the agent might exist in memory but not in the database
        
        # Try with direct SQL if SQLAlchemy fails
        try:
            # Check if the agent is already deployed
            query = (
                select(db_models.SlackBot).where(db_models.SlackBot.agent_name == agent_name)
            )
            result = await db_session.execute(query)
            existing_bot = result.scalars().first()
            
            if existing_bot:
                # Update tokens if bot already exists
                existing_bot.bot_token = bot_token
                existing_bot.app_token = app_token
                existing_bot.status = "running"  # Set to running by default
                existing_bot.updated_at = datetime.utcnow()
            else:
                # Create new SlackBot record
                new_bot = db_models.SlackBot(
                    agent_name=agent_name,
                    bot_token=bot_token,
                    app_token=app_token,
                    status="running",  # Set to running by default
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db_session.add(new_bot)
            
            await db_session.commit()
            
            # CRITICAL: Actually create and start the bot
            # Check if bot already exists in memory
            if agent_name in active_slack_bots:
                # Bot exists, stop it first
                active_slack_bots[agent_name].stop()
            
            # Create a new bot instance with the updated tokens
            bot = SlackBot(agent_name, bot_token, app_token)
            
            # Start the bot
            if bot.start():
                # Store in active bots dictionary
                active_slack_bots[agent_name] = bot
                logger.info(f"Successfully started Slack bot for agent '{agent_name}'")
                
                return {
                    "success": True, 
                    "message": f"Agent '{agent_name}' has been deployed to Slack and is now running",
                    "status": "running"
                }
            else:
                return {
                    "success": False,
                    "message": f"Agent '{agent_name}' was deployed but failed to start. Check logs for details.",
                    "status": "error"
                }
            
        except Exception as e:
            logger.error(f"SQLAlchemy error while deploying to Slack: {e}")
            
            # Fall back to direct SQL
            try:
                # Find the database path
                db_file = None
                for path in ["app.db", "../app.db", "./data/agents.db", "../data/agents.db"]:
                    if os.path.exists(path):
                        db_file = path
                        break
                
                if not db_file:
                    return {"success": False, "message": "Could not find database file"}
                
                # Use SQLite directly
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Check if bot exists
                cursor.execute("SELECT id FROM slack_bots WHERE agent_name = ?", (agent_name,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing bot
                    cursor.execute(
                        "UPDATE slack_bots SET bot_token = ?, app_token = ?, status = 'running', updated_at = CURRENT_TIMESTAMP WHERE agent_name = ?",
                        (bot_token, app_token, agent_name)
                    )
                else:
                    # Insert new bot
                    cursor.execute(
                        "INSERT INTO slack_bots (agent_name, bot_token, app_token, status) VALUES (?, ?, ?, 'running')",
                        (agent_name, bot_token, app_token)
                    )
                
                conn.commit()
                conn.close()
                
                # CRITICAL: Actually create and start the bot
                # Check if bot already exists in memory
                if agent_name in active_slack_bots:
                    # Bot exists, stop it first
                    active_slack_bots[agent_name].stop()
                
                # Create a new bot instance with the updated tokens
                bot = SlackBot(agent_name, bot_token, app_token)
                
                # Start the bot
                if bot.start():
                    # Store in active bots dictionary
                    active_slack_bots[agent_name] = bot
                    logger.info(f"Successfully started Slack bot for agent '{agent_name}' (using direct SQL)")
                    
                    return {
                        "success": True,
                        "message": f"Agent '{agent_name}' has been deployed to Slack (using direct SQL) and is now running",
                        "status": "running"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Agent '{agent_name}' was deployed but failed to start. Check logs for details.",
                        "status": "error"
                    }
                
            except Exception as sql_err:
                logger.error(f"Direct SQL error: {sql_err}")
                return {"success": False, "message": f"Database error: {str(sql_err)}"}
            
    except Exception as e:
        logger.error(f"Error deploying agent to Slack: {e}")
        return {"success": False, "message": str(e)}


async def toggle_slack_bot(agent_name: str, action: str, db_session: AsyncSession) -> Dict[str, Any]:
    """
    Start or stop a deployed Slack bot.
    
    Args:
        agent_name: The name of the agent
        action: Either "start" or "stop"
        db_session: Database session
        
    Returns:
        Dict with success status and message
    """
    try:
        # Ensure the slack_bots table exists first
        ensure_slack_table_exists()
        
        # Check if action is valid
        if action not in ["start", "stop"]:
            return {"success": False, "message": f"Invalid action: {action}. Use 'start' or 'stop'."}
            
        try:
            # Check if bot exists in database
            query = (
                select(db_models.SlackBot).where(db_models.SlackBot.agent_name == agent_name)
            )
            result = await db_session.execute(query)
            bot_record = result.scalars().first()
            
            if not bot_record:
                # If the bot doesn't exist and we're trying to start it,
                # suggest deploying it first
                if action == "start":
                    return {
                        "success": False, 
                        "message": f"Agent '{agent_name}' is not deployed to Slack. Deploy it first."
                    }
                else:
                    # If we're trying to stop a non-existent bot, just return success
                    return {
                        "success": True, 
                        "message": f"Agent '{agent_name}' is not deployed to Slack.",
                        "status": "not_deployed"
                    }
            
            # Update status based on action
            new_status = "running" if action == "start" else "stopped"
            
            await db_session.execute(
                update(db_models.SlackBot)
                .where(db_models.SlackBot.agent_name == agent_name)
                .values(status=new_status, updated_at=datetime.utcnow())
            )
            await db_session.commit()
            
            # CRITICAL: Actually start or stop the bot
            if action == "start":
                # Start the bot if it's not already running
                if agent_name in active_slack_bots:
                    # Bot exists in memory but might be stopped
                    if not active_slack_bots[agent_name].running:
                        active_slack_bots[agent_name].start()
                else:
                    # Bot doesn't exist in memory, create and start it
                    # Get the tokens from database
                    bot_token = bot_record.bot_token
                    app_token = bot_record.app_token
                    
                    # Create a new bot instance
                    bot = SlackBot(agent_name, bot_token, app_token)
                    
                    # Start the bot
                    if bot.start():
                        # Store in active bots dictionary
                        active_slack_bots[agent_name] = bot
                        logger.info(f"Successfully started Slack bot for agent '{agent_name}'")
                    else:
                        return {
                            "success": False,
                            "message": f"Failed to start Slack bot for agent '{agent_name}'. Check logs.",
                            "status": "error"
                        }
            else:  # action == "stop"
                # Stop the bot if it's running
                if agent_name in active_slack_bots:
                    # Stop the bot
                    active_slack_bots[agent_name].stop()
                    logger.info(f"Successfully stopped Slack bot for agent '{agent_name}'")
            
            return {
                "success": True, 
                "message": f"Bot for agent '{agent_name}' has been {action}ed",
                "status": new_status
            }
        except Exception as db_error:
            logger.error(f"Database error in toggle_slack_bot: {db_error}")
            
            # Try direct SQL as fallback
            try:
                # Find the database path
                db_file = None
                for path in ["app.db", "../app.db", "./data/agents.db", "../data/agents.db"]:
                    if os.path.exists(path):
                        db_file = path
                        break
                
                if not db_file:
                    return {"success": False, "message": "Could not find database file"}
                
                # Use SQLite directly
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Check if bot exists
                cursor.execute("SELECT bot_token, app_token FROM slack_bots WHERE agent_name = ?", (agent_name,))
                existing = cursor.fetchone()
                
                if not existing:
                    conn.close()
                    if action == "start":
                        return {
                            "success": False, 
                            "message": f"Agent '{agent_name}' is not deployed to Slack. Deploy it first."
                        }
                    else:
                        return {
                            "success": True, 
                            "message": f"Agent '{agent_name}' is not deployed to Slack.",
                            "status": "not_deployed"
                        }
                
                # Update status
                new_status = "running" if action == "start" else "stopped"
                cursor.execute(
                    "UPDATE slack_bots SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE agent_name = ?",
                    (new_status, agent_name)
                )
                
                conn.commit()
                
                # CRITICAL: Actually start or stop the bot
                if action == "start":
                    # Start the bot if it's not already running
                    if agent_name in active_slack_bots:
                        # Bot exists in memory but might be stopped
                        if not active_slack_bots[agent_name].running:
                            active_slack_bots[agent_name].start()
                    else:
                        # Bot doesn't exist in memory, create and start it
                        # Get tokens from the database query
                        bot_token, app_token = existing
                        
                        # Create a new bot instance
                        bot = SlackBot(agent_name, bot_token, app_token)
                        
                        # Start the bot
                        if bot.start():
                            # Store in active bots dictionary
                            active_slack_bots[agent_name] = bot
                            logger.info(f"Successfully started Slack bot for agent '{agent_name}' (direct SQL)")
                        else:
                            conn.close()
                            return {
                                "success": False,
                                "message": f"Failed to start Slack bot for agent '{agent_name}'. Check logs.",
                                "status": "error"
                            }
                else:  # action == "stop"
                    # Stop the bot if it's running
                    if agent_name in active_slack_bots:
                        # Stop the bot
                        active_slack_bots[agent_name].stop()
                        logger.info(f"Successfully stopped Slack bot for agent '{agent_name}' (direct SQL)")
                
                conn.close()
                
                return {
                    "success": True,
                    "message": f"Bot for agent '{agent_name}' has been {action}ed (using direct SQL)",
                    "status": new_status
                }
            except Exception as sql_err:
                logger.error(f"Direct SQL error: {sql_err}")
                return {"success": False, "message": f"Database error: {str(sql_err)}"}
            
    except Exception as e:
        logger.error(f"Error toggling Slack bot: {e}")
        return {"success": False, "message": str(e)}


async def get_slack_bot_status(agent_name: str, db_session: AsyncSession) -> Dict[str, Any]:
    """
    Get the status of a Slack bot.
    
    Args:
        agent_name: The name of the agent
        db_session: Database session
    
    Returns:
        Dict: Status information
    """
    try:
        # Ensure the slack_bots table exists
        ensure_slack_table_exists()
        
        # First check if the bot exists in memory
        is_in_memory = agent_name in active_slack_bots
        actually_running = is_in_memory and active_slack_bots[agent_name].running
        
        # Log the current status
        logger.info(f"Checking status for {agent_name}: in memory: {is_in_memory}, running: {actually_running}")
        
        # Try SQLAlchemy first
        try:
            # Check if the bot is deployed
            bot_query = (
                select(db_models.SlackBot).where(db_models.SlackBot.agent_name == agent_name)
            )
            bot_result = await db_session.execute(bot_query)
            bot_record = bot_result.scalars().first()
            
            if not bot_record:
                return {"deployed": False, "status": "not_deployed", "in_memory": is_in_memory}
            
            # Get the currently recorded status from the database
            db_status = bot_record.status
            
            # If the bot is running but DB says it's stopped, update DB
            if actually_running and db_status != "running":
                bot_record.status = "running"
                bot_record.updated_at = datetime.now()
                await db_session.commit()
                db_status = "running"
            # If the bot is not running but DB says it's running, update DB
            elif not actually_running and db_status == "running":
                bot_record.status = "stopped"
                bot_record.updated_at = datetime.now()
                await db_session.commit()
                db_status = "stopped"
            
            # Return comprehensive status
            return {
                "deployed": True, 
                "status": "running" if actually_running else db_status,
                "in_memory": is_in_memory,
                "bot_token_exists": bool(bot_record.bot_token),
                "app_token_exists": bool(bot_record.app_token)
            }
        
        except Exception as e:
            logger.error(f"SQLAlchemy error getting Slack bot status: {e}")
            
            # Try direct SQL as fallback
            try:
                # Find the database path
                db_file = None
                for path in ["app.db", "../app.db", "./data/agents.db", "../data/agents.db"]:
                    if os.path.exists(path):
                        db_file = path
                        break
                
                if not db_file:
                    return {"deployed": False, "status": "error", "message": "Could not find database file", "in_memory": is_in_memory}
                
                # Use SQLite directly
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Check if bot exists
                cursor.execute("SELECT status, bot_token, app_token FROM slack_bots WHERE agent_name = ?", (agent_name,))
                result = cursor.fetchone()
                
                if not result:
                    conn.close()
                    return {"deployed": False, "status": "not_deployed", "in_memory": is_in_memory}
                
                status, bot_token, app_token = result
                
                # If the bot is running but DB says it's stopped, update DB
                if actually_running and status != "running":
                    cursor.execute(
                        "UPDATE slack_bots SET status = 'running', updated_at = CURRENT_TIMESTAMP WHERE agent_name = ?",
                        (agent_name,)
                    )
                    conn.commit()
                    status = "running"
                # If the bot is not running but DB says it's running, update DB
                elif not actually_running and status == "running":
                    cursor.execute(
                        "UPDATE slack_bots SET status = 'stopped', updated_at = CURRENT_TIMESTAMP WHERE agent_name = ?",
                        (agent_name,)
                    )
                    conn.commit()
                    status = "stopped"
                
                conn.close()
                
                # Return comprehensive status
                return {
                    "deployed": True, 
                    "status": "running" if actually_running else status,
                    "in_memory": is_in_memory,
                    "bot_token_exists": bool(bot_token),
                    "app_token_exists": bool(app_token)
                }
                
            except Exception as sql_err:
                logger.error(f"Direct SQL error: {sql_err}")
                return {
                    "deployed": False, 
                    "status": "error", 
                    "message": str(sql_err),
                    "in_memory": is_in_memory
                }
    
    except Exception as e:
        logger.error(f"Error getting Slack bot status: {e}")
        return {"deployed": False, "status": "error", "message": str(e), "in_memory": False}


async def get_all_slack_bots(db_session: AsyncSession) -> List[Dict[str, Any]]:
    """
    Get information about all deployed Slack bots.
    
    Args:
        db_session: Database session
    
    Returns:
        List[Dict]: List of bot information
    """
    try:
        # Ensure the slack_bots table exists
        ensure_slack_table_exists()
        
        try:
            # Get all deployed bots
            bots_query = select(db_models.SlackBot)
            bots_result = await db_session.execute(bots_query)
            bots = bots_result.scalars().all()
            
            result = []
            for bot in bots:
                # Check if running
                is_running = bot.agent_name in active_slack_bots and active_slack_bots[bot.agent_name].running
                
                # Update status in database if there's a mismatch
                if is_running and bot.status != "running":
                    bot.status = "running"
                    bot.updated_at = datetime.now()
                elif not is_running and bot.status != "stopped":
                    bot.status = "stopped"
                    bot.updated_at = datetime.now()
                
                result.append({
                    "agent_name": bot.agent_name,
                    "status": "running" if is_running else bot.status,
                    "created_at": bot.created_at.isoformat() if bot.created_at else None,
                    "updated_at": bot.updated_at.isoformat() if bot.updated_at else None
                })
            
            if bots:
                await db_session.commit()
            
            return result
        
        except Exception as e:
            logger.error(f"SQLAlchemy error getting all Slack bots: {e}")
            
            # Try direct SQL as fallback
            try:
                # Find the database path
                db_file = None
                for path in ["app.db", "../app.db", "./data/agents.db", "../data/agents.db"]:
                    if os.path.exists(path):
                        db_file = path
                        break
                
                if not db_file:
                    return []
                
                # Use SQLite directly
                conn = sqlite3.connect(db_file)
                conn.row_factory = sqlite3.Row  # This allows accessing columns by name
                cursor = conn.cursor()
                
                # Get all bots
                cursor.execute("SELECT agent_name, status, created_at, updated_at FROM slack_bots")
                rows = cursor.fetchall()
                
                result = []
                for row in rows:
                    agent_name = row["agent_name"]
                    status = row["status"]
                    
                    # Check if running
                    is_running = agent_name in active_slack_bots and active_slack_bots[agent_name].running
                    
                    # Update status if needed
                    if is_running and status != "running":
                        cursor.execute(
                            "UPDATE slack_bots SET status = 'running', updated_at = CURRENT_TIMESTAMP WHERE agent_name = ?",
                            (agent_name,)
                        )
                        status = "running"
                    elif not is_running and status != "stopped":
                        cursor.execute(
                            "UPDATE slack_bots SET status = 'stopped', updated_at = CURRENT_TIMESTAMP WHERE agent_name = ?",
                            (agent_name,)
                        )
                        status = "stopped"
                    
                    result.append({
                        "agent_name": agent_name,
                        "status": status,
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"]
                    })
                
                conn.commit()
                conn.close()
                return result
                
            except Exception as sql_err:
                logger.error(f"Direct SQL error: {sql_err}")
                return []
    
    except Exception as e:
        logger.error(f"Error getting all Slack bots: {e}")
        return []


async def undeploy_slack_bot(agent_name: str, db_session: AsyncSession) -> Dict[str, Any]:
    """
    Undeploy a Slack bot.
    
    Args:
        agent_name: The name of the agent
        db_session: Database session
    
    Returns:
        Dict with success status and message
    """
    try:
        # Ensure the slack_bots table exists
        ensure_slack_table_exists()
        
        try:
            # Check if the bot exists
            query = (
                select(db_models.SlackBot).where(db_models.SlackBot.agent_name == agent_name)
            )
            result = await db_session.execute(query)
            bot_record = result.scalars().first()
            
            if not bot_record:
                return {"success": False, "message": f"Agent '{agent_name}' is not deployed to Slack"}
            
            # Remove from database
            await db_session.execute(
                delete(db_models.SlackBot).where(db_models.SlackBot.agent_name == agent_name)
            )
            await db_session.commit()
            
            return {
                "success": True,
                "message": f"Agent '{agent_name}' has been undeployed from Slack"
            }
        
        except Exception as e:
            logger.error(f"SQLAlchemy error undeploying Slack bot: {e}")
            
            # Try direct SQL as fallback
            try:
                # Find the database path
                db_file = None
                for path in ["app.db", "../app.db", "./data/agents.db", "../data/agents.db"]:
                    if os.path.exists(path):
                        db_file = path
                        break
                
                if not db_file:
                    return {"success": False, "message": "Could not find database file"}
                
                # Use SQLite directly
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Check if bot exists
                cursor.execute("SELECT id FROM slack_bots WHERE agent_name = ?", (agent_name,))
                if not cursor.fetchone():
                    conn.close()
                    return {"success": False, "message": f"Agent '{agent_name}' is not deployed to Slack"}
                
                # Delete bot
                cursor.execute("DELETE FROM slack_bots WHERE agent_name = ?", (agent_name,))
                conn.commit()
                conn.close()
                
                return {
                    "success": True,
                    "message": f"Agent '{agent_name}' has been undeployed from Slack (using direct SQL)"
                }
                
            except Exception as sql_err:
                logger.error(f"Direct SQL error: {sql_err}")
                return {"success": False, "message": f"Database error: {str(sql_err)}"}
    
    except Exception as e:
        logger.error(f"Error undeploying Slack bot: {e}")
        return {"success": False, "message": str(e)}


async def initialize_slack_bots(db_session: AsyncSession) -> None:
    """
    Initialize all Slack bots that should be running.
    Call this function when the server starts.
    
    Args:
        db_session: Database session
    """
    try:
        logger.info("Initializing Slack bots...")
        
        # Ensure the slack_bots table exists
        ensure_slack_table_exists()
        
        try:
            # Get all bots with status 'running'
            query = select(db_models.SlackBot).where(db_models.SlackBot.status == "running")
            result = await db_session.execute(query)
            bots = result.scalars().all()
            
            if not bots:
                logger.info("No active Slack bots found in database")
                return
            
            # Start each bot
            for bot_record in bots:
                try:
                    agent_name = bot_record.agent_name
                    bot_token = bot_record.bot_token
                    app_token = bot_record.app_token
                    
                    logger.info(f"Starting Slack bot for agent '{agent_name}'")
                    
                    # Check if we already have this bot in memory
                    if agent_name in active_slack_bots:
                        # Stop the existing bot if it's already running
                        active_slack_bots[agent_name].stop()
                    
                    # Create a new bot instance
                    bot = SlackBot(agent_name, bot_token, app_token)
                    
                    # Start the bot
                    if bot.start():
                        # Store in active bots dictionary
                        active_slack_bots[agent_name] = bot
                        logger.info(f"Successfully started Slack bot for agent '{agent_name}'")
                    else:
                        logger.error(f"Failed to start Slack bot for agent '{agent_name}'")
                        
                except Exception as bot_error:
                    logger.error(f"Error initializing bot for agent '{bot_record.agent_name}': {str(bot_error)}")
            
            logger.info(f"Initialized {len(bots)} Slack bots")
            
        except Exception as db_error:
            logger.error(f"Database error in initialize_slack_bots: {str(db_error)}")
            
            # Try with direct SQL as fallback
            try:
                # Find the database path
                db_file = None
                for path in ["app.db", "../app.db", "./data/agents.db", "../data/agents.db"]:
                    if os.path.exists(path):
                        db_file = path
                        break
                
                if not db_file:
                    logger.error("Could not find database file")
                    return
                
                # Use SQLite directly
                conn = sqlite3.connect(db_file)
                conn.row_factory = sqlite3.Row  # Use Row to access columns by name
                cursor = conn.cursor()
                
                # Get all bots with status 'running'
                cursor.execute("SELECT agent_name, bot_token, app_token FROM slack_bots WHERE status = 'running'")
                bots = cursor.fetchall()
                
                if not bots:
                    logger.info("No active Slack bots found in database (using direct SQL)")
                    conn.close()
                    return
                
                # Start each bot
                for bot_record in bots:
                    try:
                        agent_name = bot_record["agent_name"]
                        bot_token = bot_record["bot_token"]
                        app_token = bot_record["app_token"]
                        
                        logger.info(f"Starting Slack bot for agent '{agent_name}' (using direct SQL)")
                        
                        # Check if we already have this bot in memory
                        if agent_name in active_slack_bots:
                            # Stop the existing bot if it's already running
                            active_slack_bots[agent_name].stop()
                        
                        # Create a new bot instance
                        bot = SlackBot(agent_name, bot_token, app_token)
                        
                        # Start the bot
                        if bot.start():
                            # Store in active bots dictionary
                            active_slack_bots[agent_name] = bot
                            logger.info(f"Successfully started Slack bot for agent '{agent_name}' (using direct SQL)")
                        else:
                            logger.error(f"Failed to start Slack bot for agent '{agent_name}' (using direct SQL)")
                            
                    except Exception as bot_error:
                        logger.error(f"Error initializing bot for agent '{bot_record['agent_name']}': {str(bot_error)}")
                
                conn.close()
                logger.info(f"Initialized {len(bots)} Slack bots (using direct SQL)")
                
            except Exception as sql_error:
                logger.error(f"Direct SQL error in initialize_slack_bots: {str(sql_error)}")
    
    except Exception as e:
        logger.error(f"Error initializing Slack bots: {str(e)}")


# Add a replacement for get_agent_config
async def get_agent_config(agent_name: str, db_session: AsyncSession = None) -> Dict[str, Any]:
    """
    Get the configuration for an agent by name.
    
    Args:
        agent_name: The name of the agent
        db_session: Optional database session
        
    Returns:
        A dictionary with the agent configuration
    """
    if db_session:
        # Query the agent from the database
        query = select(db_models.Agent).where(db_models.Agent.name == agent_name)
        result = await db_session.execute(query)
        agent = result.scalars().first()
        
        if agent:
            return {
                "name": agent.name,
                "role": agent.role,
                "personality": agent.personality,
                "tools": agent.tools
            }
    
    # Return a default configuration if no agent found
    return {
        "name": agent_name,
        "role": "Assistant",
        "personality": "Helpful and friendly",
        "tools": []
    } 
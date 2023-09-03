from enum import Enum
from dataclasses import dataclass
import openai
from typing import Optional, List
from src.constants import (
    BOT_NAME
)
import discord
from src.base import Message
from src.utils import split_into_shorter_messages, close_thread, logger

MY_BOT_NAME = BOT_NAME

class CompletionResult(Enum):
    OK = 0
    TOO_LONG = 1
    INVALID_REQUEST = 2
    OTHER_ERROR = 3

@dataclass
class CompletionData:
    status: CompletionResult
    reply_text: Optional[str]
    status_text: Optional[str]


async def generate_completion_response(
    messages: List[Message], model: str = "gpt-3.5-turbo"
) -> CompletionData:
    try:
        messages = [m.render() for m in messages]
        logger.info(f"Chatclient. messages: {messages}")
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages
        )
        reply = response.choices[0].message.content.strip()

        return CompletionData(
            status=CompletionResult.OK, reply_text=reply, status_text=None
        )
    except openai.error.InvalidRequestError as e:
        if "This model's maximum context length" in e.user_message:
            return CompletionData(
                status=CompletionResult.TOO_LONG, reply_text=None, status_text=str(e)
            )
        else:
            logger.exception(e)
            return CompletionData(
                status=CompletionResult.INVALID_REQUEST,
                reply_text=None,
                status_text=str(e),
            )
    except Exception as e:
        logger.exception(e)
        return CompletionData(
            status=CompletionResult.OTHER_ERROR, reply_text=None, status_text=str(e)
        )
    
async def generate_completion_response_summarize(
    messages: List[Message], model: str = "gpt-4", messages_to_keep: int = 2, messages_to_summarize: int = 10
) -> CompletionData:
    try:
        messages = messages[-messages_to_summarize:]
        if (len(messages) > messages_to_keep):
            messages_summary = messages[:-messages_to_keep]
            current_prompt = messages_summary[-1].text
            summary_text = "Provide a concise summary of the conversation so far"
            messages_summary.append(Message(user="user", text=summary_text))
            messages_summary_rendered = [m.render() for m in messages_summary]
            logger.info(f"Chatclient. messages to summarize: {messages_summary_rendered }")
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages_summary_rendered
            )
            reply = response.choices[0].message.content.strip()
            if(messages_to_keep == 0):
                messages = []
            else:
                messages = messages[-(messages_to_keep):]
            messages.insert(0, Message(user="assistant", text=reply))
        messages = [m.render() for m in messages]
        logger.info(f"Chatclient. messages: {messages}")
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages
        )
        reply = response.choices[0].message.content.strip()
        return CompletionData(
            status=CompletionResult.OK, reply_text=reply, status_text=None
        )
    except openai.error.InvalidRequestError as e:
        if "This model's maximum context length" in e.user_message:
            return CompletionData(
                status=CompletionResult.TOO_LONG, reply_text=None, status_text=str(e)
            )
        else:
            logger.exception(e)
            return CompletionData(
                status=CompletionResult.INVALID_REQUEST,
                reply_text=None,
                status_text=str(e),
            )
    except Exception as e:
        logger.exception(e)
        return CompletionData(
            status=CompletionResult.OTHER_ERROR, reply_text=None, status_text=str(e)
        )


async def process_response(
    thread: discord.Thread, response_data: CompletionData
):
    status = response_data.status
    reply_text = response_data.reply_text
    status_text = response_data.status_text
    if status is CompletionResult.OK:
        sent_message = None
        if not reply_text:
            sent_message = await thread.send(
                embed=discord.Embed(
                    description=f"**Invalid response** - empty response",
                    color=discord.Color.yellow(),
                )
            )
        else:
            shorter_response = split_into_shorter_messages(reply_text)
            for r in shorter_response:
                sent_message = await thread.send(r)
    elif status is CompletionResult.TOO_LONG:
        await close_thread(thread)
    elif status is CompletionResult.INVALID_REQUEST:
        await thread.send(
            embed=discord.Embed(
                description=f"**Invalid request** - {status_text}",
                color=discord.Color.yellow(),
            )
        )
    else:
        await thread.send(
            embed=discord.Embed(
                description=f"**Error** - {status_text}",
                color=discord.Color.yellow(),
            )
        )

import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks
import httpx
from contextlib import asynccontextmanager
from db import init_db, save_chat, get_chat, clear_user_history, summarize_history, add_user_memories, get_past_memory, count_history #CUSTOM MODULES

load_dotenv()

# Initialize a shared HTTP client globally so it can be cleanly managed by the lifespan context
http_client = httpx.AsyncClient(timeout=20.0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs on Uvicorn startup BEFORE accepting webhooks
    init_db()
    yield
    # Runs on Uvicorn end after everything is concluded
    await http_client.aclose()

app = FastAPI(lifespan=lifespan)

BOT_TOKEN = os.getenv("TOKEN")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

try:
    client = genai.Client()
    print("API Client configured successfully!")
except Exception as e:
    print(f"Error configuring API: {e}")
    exit(1) 


#Filters = BlocK None
no_filters = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
]

#System instruction from text file
try:
    with open('sys-instruct.txt', 'r', encoding= 'utf-8') as f:
    	sys_ins = f.read()
except FileNotFoundError:
    print("Error: Could not find 'sys-instruct.txt'. Make sure it's in the same folder.")
    exit(1)
    


#Summarizing older messages
summary_sys_instruct = """You are a dual-layer memory engine. Consolidate past memory and new chat into a two-part profile:

1. **Narrative Timeline**: A compressed, chronological summary of ongoing events, shared moments, and dates as the relationship/conversations evolve. Update or overwrite past timeline events as the narrative progresses.
2. **Long-Term Profile**: Concise bullet points of persistent facts (e.g., Name, Fav Color: Red, Location, Relationships). Overwrite outdated facts with newer info.

RULES:
- Output ONLY the 2-part profile. No intros, outros, or explanations.
- Let Part 1 grow naturally in length to preserve essential context and relationship depth but as new conversation arrives move past data to part 2 only keeping newest conversation in this.
- Keep Part 2 structured and strictly focused on long-term static traits.

By time both part can grow in length depending on conversation and need to store necessary facts"""

async def summarize_old_msg(user_id:int): #Here async will ensure that this function Won't block the whole uvicorn app while waiting for Gemini response for summarization
    if count_history(user_id) > 30:
        text = summarize_history(user_id)
        if not text:
            return
        response = await client.aio.models.generate_content(
            model = "gemini-3.1-flash-lite",
            contents = text,
            config=types.GenerateContentConfig(
                system_instruction=summary_sys_instruct,
                temperature=0.2,
            ) # Low temperature ensures strictly factual updates and no creativity
        )   
        if response and response.text:
            add_user_memories(user_id, response.text.strip())
            print(f"[SUCCESS] user_memories updated for user {user_id}")
        


#FASTAPI and TELEGRAM SETUP

async def send_typing(chat_id: int):
    url = f"{BASE_URL}/sendChatAction"
    payload = {"chat_id": chat_id, "action": "typing"}
    try:
        await http_client.post(url, json=payload)
    except:
        pass

async def send_tg_msg(chat_id: int, text: str):
    #Sends Url back to tg 
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text":text}
    try:
        await http_client.post(url, json=payload)
    except Exception as e:
        print(f"Error Sending message to telegram: {e}")


async def process_user_turn(user_id: int, chat_id: int, user_text: str):
    #Generates AI response, Delete User, Save into Database
    
    #Delete User
    if user_text.strip().lower() == "/reset":
        clear_user_history(user_id)
        await send_tg_msg(chat_id, "Memory Cleared")
        await send_tg_msg(chat_id, "How ya doing today??")
        return

    #Past History summary and model Configuration
    ##Past History
    user_past_memory = get_past_memory(user_id)
    past_memory = f"\n\n[USER MEMORY PROFILE]\n{user_past_memory}" if user_past_memory else ""

    ##Configuration
    config=types.GenerateContentConfig(
            system_instruction=sys_ins + past_memory,
            safety_settings=no_filters,
            temperature=0.9
            )

    #Generate text response using AI
    try:
        await send_typing(chat_id) #Show typing to user
        #Fetch History from Sql db
        user_history = get_chat(user_id, limit=30)

        #Append to AI client history
        chat = client.aio.chats.create(
            model="gemini-3.5-flash-lite",
            config=config,
            history=user_history
        )

        response = await chat.send_message(user_text) #chat.send_message is gemini functionality to get response and using await make it asynchronous meaning it won't stop the async loop.
        bot_response = response.text

        #Save to database
        save_chat(user_id, "user", user_text)
        save_chat(user_id, "model", bot_response)

        #Reply to telegram
        await send_tg_msg(chat_id, bot_response)

        #Summarization
        try:
            await summarize_old_msg(user_id)
        except Exception as e:
            print(f"Background summarization failed for user {user_id}: {e}")

    except Exception as e:
        print(f"Error processing turn: {e}")
        await send_tg_msg(chat_id, "Ahh Snap! Smthng Wrogn, Pls try again")

       
    
@app.post("/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    #Endpoint called by Telegram whenever any user sends a message
    data = await request.json()

    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_id = data["message"]["from"]["id"]
        user_text = data["message"]["text"]

        #Run reply logic in background so Telegram gets an Instant 200 OK and process_user_turn can run in background
        background_tasks.add_task(process_user_turn, user_id, chat_id, user_text)

    return {"status": "ok"}

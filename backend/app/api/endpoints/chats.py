from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.schemas.chat import Chat, ChatCreate, ChatWithMessages, MessageCreate, Message
from app.services.interview_service import interview_service
from app.repositories.chat_repository import chat_repo, message_repo
from app.models.chat import MessageRole, ChatStatus
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=Chat)
async def create_chat(
    *,
    db: AsyncSession = Depends(deps.get_db),
    chat_in: ChatCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Start a new interview chat.
    """
    # Check Limits (Demo: 20 requests for free tier)
    if current_user.tariff == "free" and current_user.requests_count >= 20:
         raise HTTPException(
            status_code=402, 
            detail="Free limit exceeded (20 requests). Please upgrade."
        )

    chat = await interview_service.start_interview(db, user_id=current_user.id, chat_in=chat_in)
    return chat

@router.get("/", response_model=List[Chat])
async def read_chats(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve chats.
    """
    chats = await chat_repo.get_multi_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    return chats

@router.get("/{chat_id}", response_model=ChatWithMessages)
async def read_chat(
    *,
    db: AsyncSession = Depends(deps.get_db),
    chat_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get chat by ID with messages.
    """
    chat = await chat_repo.get(db, id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    # Manually fetch messages to ensure order
    messages = await message_repo.get_multi_by_chat(db, chat_id=chat_id)
    chat.messages = messages
    return chat

@router.post("/{chat_id}/messages", response_model=Message)
async def create_message(
    *,
    db: AsyncSession = Depends(deps.get_db),
    chat_id: int,
    message_in: MessageCreate,
    current_user: User = Depends(deps.get_current_user),
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Send a message to the chat.
    """
    chat = await chat_repo.get(db, id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")

    if chat.status == ChatStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Interview is already completed")

    # Check Limits
    if current_user.tariff == "free" and current_user.requests_count >= 20:
         raise HTTPException(
            status_code=402, 
            detail="Free limit exceeded (20 requests). Please upgrade."
        )

    # Save User Message
    user_message = await message_repo.create(db, obj_in={
        "chat_id": chat_id,
        "role": MessageRole.USER,
        "content": message_in.content
    })

    # Trigger AI in background
    background_tasks.add_task(
        interview_service.generate_ai_response_task, 
        db=None, # Session created inside task
        chat_id=chat_id, 
        user_message=message_in.content,
        user_id=current_user.id
    )

    return user_message

@router.post("/{chat_id}/finish", response_model=Chat)
async def finish_chat(
    *,
    db: AsyncSession = Depends(deps.get_db),
    chat_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Finish the interview and generate feedback.
    """
    chat = await chat_repo.get(db, id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
        
    chat = await interview_service.finish_interview(db, chat_id=chat_id)
    return chat

@router.get("/{chat_id}/messages", response_model=List[Message])
async def read_messages(
    *,
    db: AsyncSession = Depends(deps.get_db),
    chat_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get messages for a chat.
    """
    chat = await chat_repo.get(db, id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
        
    messages = await message_repo.get_multi_by_chat(db, chat_id=chat_id)
    return messages

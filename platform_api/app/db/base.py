from typing import Any
from sqlalchemy.ext.declarative import as_declarative, declared_attr

@as_declarative()
class Base:
    id: Any
    __name__: str
    
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

# Import all models here for metadata registration
from app.models.user import User  # noqa
from app.models.test_lab import TestRun, TestRunEvent # noqa
from app.models.kb import KBDocument # noqa
from app.models.chatwoot import ChatwootWebhookEventRaw # noqa
from app.models.bot_studio import BotAgent, BotTask, BotCrew, BotCrewTaskLink, BotCrewVersion # noqa
from app.models.bot_run import BotRun, BotRunEvent # noqa
from app.models.ai import AiProvider, AiModel, AiUsageLog # noqa
from app.models.kb import KnowledgeBase, KBFile # noqa
from app.models.data_hub import RawChatwootEvent, RawChatwootConversation, RawChatwootMessage, RawChatwootReportingEvent # noqa

from app.db.base_class import Base

# Import all models here for metadata registration
from app.models.user import User  # noqa
from app.models.test_lab import TestRun, TestRunEvent # noqa

from app.models.chatwoot import ChatwootWebhookEventRaw # noqa
from app.models.bot_studio import BotAgent, BotTask, BotCrew, BotCrewTaskLink, BotCrewVersion # noqa
from app.models.bot_run import BotRun, BotRunEvent # noqa
from app.models.ai import AiProvider, AiModel, AiUsageLog # noqa
from app.models.kb import KnowledgeBase, KBFile # noqa
from app.models.data_hub import RawChatwootEvent, RawChatwootConversation, RawChatwootMessage, RawChatwootReportingEvent # noqa

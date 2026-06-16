import logging
from datetime import datetime
from services.llm import LLMService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agents_bus")

class AgentBus:
    def __init__(self):
        self.logs = []

    def log(self, agent_name: str, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = {
            "timestamp": timestamp,
            "agent": agent_name,
            "message": message
        }
        self.logs.append(log_entry)
        logger.info(f"[{agent_name}] {message}")

    def get_logs(self) -> list[dict]:
        return self.logs


class BaseAgent:
    def __init__(self, name: str, llm: LLMService, bus: AgentBus):
        self.name = name
        self.llm = llm
        self.bus = bus

    def log(self, message: str):
        self.bus.log(self.name, message)

import httpx
import logging
from typing import List
from core.models import AgentCard

logger = logging.getLogger(__name__)

async def discover_agents(registry_path: str) -> List[AgentCard]:
    """Reads a list of URLs from a file and fetches their agent cards."""
    agent_cards = []
    try:
        with open(registry_path, "r") as f:
            urls = [line.strip() for line in f if line.strip()]
        
        async with httpx.AsyncClient() as client:
            for url in urls:
                try:
                    # Append /.well-known/agent.json to the base URL
                    discovery_url = url.rstrip("/") + "/.well-known/agent.json"
                    response = await client.get(discovery_url, timeout=5.0)
                    if response.status_code == 200:
                        card = AgentCard.model_validate(response.json())
                        agent_cards.append(card)
                        logger.info(f"Discovered agent: {card.name} at {url}")
                    else:
                        logger.warning(f"Failed to discover agent at {url}: {response.status_code}")
                except Exception as e:
                    logger.warning(f"Error discovering agent at {url}: {e}")
    except Exception as e:
        logger.error(f"Error reading registry file: {e}")
    
    return agent_cards

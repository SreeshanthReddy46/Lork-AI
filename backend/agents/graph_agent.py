from agents.base import BaseAgent, AgentBus
from services.llm import LLMService
from services.graph_service import KnowledgeGraphService

class GraphAgent(BaseAgent):
    def __init__(self, llm: LLMService, bus: AgentBus, graph_service: KnowledgeGraphService = None):
        super().__init__("Knowledge Graph Agent", llm, bus)
        self.graph_service = graph_service or KnowledgeGraphService(llm)

    def retrieve_subgraph(self, keywords: list[str]) -> dict:
        self.log(f"Traversing local graph nodes matching keywords: {keywords}...")
        
        subgraph = self.graph_service.get_subgraph_around_query(keywords)
        node_names = [node["label"] for node in subgraph.get("nodes", [])]
        self.log(f"Found {len(node_names)} graph entities in search radius: {node_names[:10]}")
        return subgraph

    def ingest_document_triples(self, page_id: int, triples: dict):
        self.log(f"Updating graph database with {len(triples.get('nodes', []))} nodes from document ID {page_id}...")
        
        # Save nodes
        for node in triples.get("nodes", []):
            node_id = node.get("id")
            label = node.get("label", node_id)
            e_type = node.get("type", "Concept")
            metadata = node.get("metadata", {})
            if node_id:
                self.graph_service.save_node(node_id, label, e_type, metadata)
                self.graph_service.link_document_to_entity(page_id, node_id)
                
        # Save edges
        for edge in triples.get("edges", []):
            source = edge.get("source")
            target = edge.get("target")
            relation = edge.get("relation")
            weight = edge.get("weight", 1.0)
            
            # Check node existence in graph memory
            if source and target and source in self.graph_service.graph and target in self.graph_service.graph:
                self.graph_service.save_edge(source, target, relation, weight)
                
        # Update pageranks and weights
        self.graph_service.update_page_authorities()
        self.log("Graph updates completed and PageRank authority scores updated.")

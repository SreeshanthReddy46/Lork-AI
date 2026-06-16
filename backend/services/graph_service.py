import json
import logging
import networkx as nx
from services.database import get_db_connection
from services.llm import LLMService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("graph_service")

class KnowledgeGraphService:
    def __init__(self, llm_service: LLMService = None):
        self.llm = llm_service or LLMService()
        self.graph = nx.DiGraph()
        self.load_graph_from_db()

    def load_graph_from_db(self):
        self.graph.clear()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Load Nodes
        cursor.execute("SELECT id, label, type, metadata FROM nodes")
        for row in cursor.fetchall():
            meta = json.loads(row["metadata"])
            attrs = {"label": row["label"], "type": row["type"]}
            for k, v in meta.items():
                if k not in attrs:
                    attrs[k] = v
            self.graph.add_node(row["id"], **attrs)
            
        # Load Edges
        cursor.execute("SELECT source, target, relation, weight FROM edges")
        for row in cursor.fetchall():
            self.graph.add_edge(
                row["source"],
                row["target"],
                relation=row["relation"],
                weight=row["weight"]
            )
            
        conn.close()
        logger.info(f"Knowledge Graph loaded: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges.")

    def save_node(self, node_id: str, label: str, entity_type: str, metadata: dict = None):
        metadata = metadata or {}
        metadata_json = json.dumps(metadata)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO nodes (id, label, type, metadata)
            VALUES (?, ?, ?, ?)
            """,
            (node_id, label, entity_type, metadata_json)
        )
        conn.commit()
        conn.close()
        
        attrs = {"label": label, "type": entity_type}
        for k, v in metadata.items():
            if k not in attrs:
                attrs[k] = v
        self.graph.add_node(node_id, **attrs)

    def save_edge(self, source: str, target: str, relation: str, weight: float = 1.0):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO edges (source, target, relation, weight)
            VALUES (?, ?, ?, ?)
            """,
            (source, target, relation, weight)
        )
        conn.commit()
        conn.close()
        
        self.graph.add_edge(source, target, relation=relation, weight=weight)

    def link_document_to_entity(self, page_id: int, entity_id: str):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO document_entities (page_id, entity_id) VALUES (?, ?)",
            (page_id, entity_id)
        )
        conn.commit()
        conn.close()

    def get_pagerank(self) -> dict:
        if not self.graph.nodes:
            return {}
        try:
            return nx.pagerank(self.graph, weight="weight")
        except Exception as e:
            logger.warning(f"NetworkX PageRank failed (likely missing numpy): {e}. Falling back to pure Python implementation.")
            nodes = list(self.graph.nodes)
            n = len(nodes)
            if n == 0:
                return {}
                
            pr = {node: 1.0 / n for node in nodes}
            d = 0.85
            max_iter = 100
            tol = 1.0e-6
            
            for _ in range(max_iter):
                next_pr = {}
                dangling_sum = sum(pr[node] for node in nodes if self.graph.out_degree(node) == 0)
                
                for node in nodes:
                    rank = (1.0 - d) / n + d * dangling_sum / n
                    for u in self.graph.predecessors(node):
                        out_deg = self.graph.out_degree(u)
                        if out_deg > 0:
                            rank += d * pr[u] / out_deg
                    next_pr[node] = rank
                    
                err = sum(abs(next_pr[node] - pr[node]) for node in nodes)
                if err < tol:
                    return next_pr
                pr = next_pr
            return pr

    def extract_and_build_graph(self, page_id: int, content: str):
        if not content or len(content.strip()) < 50:
            return
            
        system_prompt = """You are a GraphRAG knowledge extraction agent.
Analyze the text provided by the user and extract key entities and their relationships.
Entity Types MUST be one of: 'Company', 'Person', 'Technology', 'Product', 'Event', 'Concept'.

Format the response as a valid JSON object ONLY. Do not include markdown codeblocks or other explanations.
Structure:
{
  "nodes": [
    {"id": "UniqueShortID", "label": "Human Readable Name", "type": "Company/Person/Technology/etc.", "metadata": {"attribute": "value"}}
  ],
  "edges": [
    {"source": "SourceID", "target": "TargetID", "relation": "RELATIONSHIP_VERB", "weight": 1.0}
  ]
}
"""
        prompt = f"Text Content:\n{content[:2500]}"
        
        try:
            response = self.llm.generate(prompt, system_prompt=system_prompt, json_mode=True)
            clean_resp = response.strip()
            if clean_resp.startswith("```json"):
                clean_resp = clean_resp.replace("```json", "", 1)
            if clean_resp.endswith("```"):
                clean_resp = clean_resp[:-3].strip()
            if clean_resp.startswith("```"):
                clean_resp = clean_resp.replace("```", "", 1).strip()
                
            data = json.loads(clean_resp)
            
            nodes = data.get("nodes", [])
            edges = data.get("edges", [])
            
            # Save nodes
            for node in nodes:
                node_id = node.get("id")
                label = node.get("label", node_id)
                e_type = node.get("type", "Concept")
                metadata = node.get("metadata", {})
                if node_id:
                    self.save_node(node_id, label, e_type, metadata)
                    self.link_document_to_entity(page_id, node_id)
                    
            # Save edges
            for edge in edges:
                source = edge.get("source")
                target = edge.get("target")
                relation = edge.get("relation")
                weight = edge.get("weight", 1.0)
                
                if source and target and source in self.graph and target in self.graph:
                    self.save_edge(source, target, relation, weight)
                    
            self.update_page_authorities()
            
        except Exception as e:
            logger.error(f"Error during Graph extraction from page {page_id}: {e}")

    def update_page_authorities(self):
        pageranks = self.get_pagerank()
        if not pageranks:
            return
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM pages")
        page_ids = [row["id"] for row in cursor.fetchall()]
        
        for p_id in page_ids:
            cursor.execute("SELECT entity_id FROM document_entities WHERE page_id = ?", (p_id,))
            entities = [row["entity_id"] for row in cursor.fetchall()]
            
            if entities:
                authority_score = sum(pageranks.get(e, 0.0) for e in entities) / len(entities)
                scaled_score = 1.0 + (authority_score * 10.0)
            else:
                scaled_score = 1.0
                
            cursor.execute("UPDATE pages SET authority = ? WHERE id = ?", (scaled_score, p_id))
            
        conn.commit()
        conn.close()

    def get_subgraph_around_query(self, keywords: list[str]) -> dict:
        relevant_nodes = set()
        
        for node in self.graph.nodes:
            node_lower = node.lower()
            label_lower = self.graph.nodes[node].get("label", "").lower()
            if any(kw.lower() in node_lower or kw.lower() in label_lower for kw in keywords):
                relevant_nodes.add(node)
                
        subgraph_nodes = set(relevant_nodes)
        for node in relevant_nodes:
            if node in self.graph:
                subgraph_nodes.update(self.graph.neighbors(node))
                if hasattr(self.graph, "predecessors"):
                    subgraph_nodes.update(self.graph.predecessors(node))
                
        nodes_list = []
        links_list = []
        
        for node in subgraph_nodes:
            if node in self.graph:
                node_data = self.graph.nodes[node]
                nodes_list.append({
                    "id": node,
                    "label": node_data.get("label", node),
                    "type": node_data.get("type", "Concept")
                })
            
        for u, v in self.graph.edges(subgraph_nodes):
            if u in subgraph_nodes and v in subgraph_nodes:
                links_list.append({
                    "source": u,
                    "target": v,
                    "relation": self.graph.edges[u, v].get("relation", "LINKED")
                })
                
        return {
            "nodes": nodes_list,
            "links": links_list
        }

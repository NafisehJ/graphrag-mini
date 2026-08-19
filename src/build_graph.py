import json
import re
from pathlib import Path

import networkx as nx


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_PATH = PROJECT_ROOT / "results" / "graph.json"

KNOWN_KEYWORDS = {
    "attention mechanism": "attention mechanism",
    "deep learning": "deep learning",
    "entity linking": "entity linking",
    "graph neural network": "graph neural network",
    "knowledge graph": "knowledge graph",
    "large language model": "large language model",
    "machine learning": "machine learning",
    "multi-hop reasoning": "multi-hop reasoning",
    "question answering": "question answering",
    "reinforcement learning": "reinforcement learning",
    "relation extraction": "relation extraction",
    "retrieval augmented generation": "retrieval augmented generation",
    "retrieval-augmented generation": "retrieval-augmented generation",
    "semantic search": "semantic search",
    "transformer": "transformer",
    "vector database": "vector database",
}

ACRONYM_EXPANSIONS = {
    "kg": "knowledge graph",
    "llm": "large language model",
    "qa": "question answering",
    "rag": "retrieval augmented generation",
}

CAPITALIZED_PHRASE_RE = re.compile(
    r"\b(?:[A-Z][A-Za-z0-9-]+(?:\s+[A-Z][A-Za-z0-9-]+)+)\b"
)
ACRONYM_RE = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b|\b[A-Z]{2,}\b")
STOPWORD_PREFIXES = ("while", "the", "this", "our", "we", "these")


def normalize_term(term: str) -> str:
    return re.sub(r"\s+", " ", term.strip(" .,:;()[]{}"))


def singularize(term: str) -> str:
    words = term.split()
    if words and words[-1].endswith("ies"):
        words[-1] = words[-1][:-3] + "y"
    elif words and words[-1].endswith("s") and not words[-1].endswith("ss"):
        words[-1] = words[-1][:-1]
    return " ".join(words)


def canonical_term(term: str) -> str:
    normalized = normalize_term(term).casefold().replace("-", " ")
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = singularize(normalized)
    return ACRONYM_EXPANSIONS.get(normalized, normalized)


def extract_terms(text: str) -> set[str]:
    terms: dict[str, str] = {}

    for keyword, label in KNOWN_KEYWORDS.items():
        keyword_pattern = re.escape(keyword).replace(r"\ ", r"[-\s]+")
        for match in re.finditer(
            rf"(?<!\w){keyword_pattern}(?!\w)", text, re.IGNORECASE
        ):
            terms[match.group(0).casefold()] = match.group(0)

    for pattern in (CAPITALIZED_PHRASE_RE, ACRONYM_RE):
        for match in pattern.findall(text):
            term = normalize_term(match)
            if len(term) > 1:
                terms.setdefault(term.casefold(), term)

    return set(terms.values())


def is_noise_term(term: str, paper_count: int, known_terms: set[str]) -> bool:
    normalized = normalize_term(term).casefold()
    first_word = normalized.split(" ", 1)[0]
    starts_with_stopword = first_word in STOPWORD_PREFIXES
    return (
        len(normalized) < 3
        or starts_with_stopword
        or (paper_count == 1 and canonical_term(term) not in known_terms)
    )


def build_graph() -> tuple[nx.Graph, int, int]:
    graph = nx.Graph()
    surface_terms: set[str] = set()
    resolved_terms: set[str] = set()
    paper_terms: dict[str, set[str]] = {}
    paper_titles: dict[str, str] = {}

    for paper_path in sorted(DATA_DIR.glob("paper_*.txt")):
        text = paper_path.read_text(encoding="utf-8").strip()
        if not text:
            continue

        paper_id = paper_path.stem
        title = text.splitlines()[0].strip()
        paper_titles[paper_id] = title
        paper_terms[paper_id] = extract_terms(text)

    term_papers: dict[str, set[str]] = {}
    for paper_id, terms in paper_terms.items():
        for term in terms:
            term_papers.setdefault(canonical_term(term), set()).add(paper_id)

    known_terms = {canonical_term(keyword) for keyword in KNOWN_KEYWORDS.values()}
    noise_terms: set[str] = set()

    for paper_id, terms in paper_terms.items():
        graph.add_node(paper_id, node_type="paper", title=paper_titles[paper_id])

        for term in terms:
            if is_noise_term(term, len(term_papers[canonical_term(term)]), known_terms):
                noise_terms.add(term)
                continue

            surface_terms.add(term)
            canonical = canonical_term(term)
            resolved_terms.add(canonical)
            term_id = f"term:{canonical}"
            if term_id not in graph:
                graph.add_node(
                    term_id,
                    node_type="term",
                    label=canonical,
                    aliases=set(),
                )
            graph.nodes[term_id]["aliases"].add(term)
            graph.add_edge(paper_id, term_id)

    for node, data in graph.nodes(data=True):
        if data["node_type"] == "term":
            data["aliases"] = sorted(data["aliases"])

    merged_nodes = len(surface_terms) - len(resolved_terms)
    return graph, merged_nodes, len(noise_terms)


def save_graph(graph: nx.Graph) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(nx.node_link_data(graph), indent=2),
        encoding="utf-8",
    )


def print_summary(graph: nx.Graph, merged_nodes: int, noise_terms: int) -> None:
    papers = [node for node, data in graph.nodes(data=True) if data["node_type"] == "paper"]
    terms = [node for node, data in graph.nodes(data=True) if data["node_type"] == "term"]
    connected_terms = sorted(
        ((graph.degree(node), graph.nodes[node]["label"]) for node in terms),
        reverse=True,
    )

    print(f"Noise terms dropped: {noise_terms}")
    print(f"Papers: {len(papers)}")
    print(f"Terms: {len(terms)}")
    print(f"Edges: {graph.number_of_edges()}")
    print(f"Nodes merged: {merged_nodes}")
    print("Top 10 most connected terms:")
    for count, label in connected_terms[:10]:
        print(f"- {label}: {count}")


if __name__ == "__main__":
    knowledge_graph, merged_nodes, noise_terms = build_graph()
    save_graph(knowledge_graph)
    print_summary(knowledge_graph, merged_nodes, noise_terms)
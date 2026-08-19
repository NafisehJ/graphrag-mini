import json
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx


PROJECT_ROOT = Path(__file__).resolve().parent.parent
GRAPH_PATH = PROJECT_ROOT / "results" / "graph.json"
IMAGE_PATH = PROJECT_ROOT / "results" / "graph.png"


def draw_graph() -> None:
    graph_data = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    graph = nx.node_link_graph(graph_data)
    positions = nx.spring_layout(graph, seed=42)

    papers = [
        node for node, data in graph.nodes(data=True) if data.get("node_type") == "paper"
    ]
    terms = [
        node for node, data in graph.nodes(data=True) if data.get("node_type") == "term"
    ]
    paper_sizes = [50 + 10 * graph.degree(node) for node in papers]
    term_sizes = [150 + 30 * graph.degree(node) for node in terms]
    term_labels = {node: graph.nodes[node].get("label", node) for node in terms}

    figure = plt.figure(figsize=(14, 10), dpi=150)
    nx.draw_networkx_edges(graph, positions, alpha=0.35, edge_color="gray")
    nx.draw_networkx_nodes(
        graph,
        positions,
        nodelist=papers,
        node_color="blue",
        node_size=paper_sizes,
        node_shape="o",
        linewidths=0,
    )
    nx.draw_networkx_nodes(
        graph,
        positions,
        nodelist=terms,
        node_color="orange",
        node_size=term_sizes,
        node_shape="o",
        linewidths=0,
    )
    nx.draw_networkx_labels(graph, positions, labels=term_labels, font_size=8)

    figure.tight_layout()
    IMAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(IMAGE_PATH, dpi=150, bbox_inches="tight")
    plt.close(figure)


if __name__ == "__main__":
    draw_graph()
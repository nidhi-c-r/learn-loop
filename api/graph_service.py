import networkx as nx
from pyvis.network import Network
from api.models import KnowledgeGraph
import tempfile
import os


def build_nx_graph(kg: KnowledgeGraph) -> nx.DiGraph:
    G = nx.DiGraph()
    for node in kg.nodes:
        G.add_node(node.id, label=node.label, score=node.score, understood=node.understood)
    for edge in kg.edges:
        G.add_edge(edge.source, edge.target, relation=edge.relation)
    return G


def render_pyvis(kg: KnowledgeGraph, height: str = "500px") -> str:
    net = Network(height=height, width="100%", directed=True, bgcolor="transparent", font_color="#555")
    net.set_options("""
    {
      "physics": {"stabilization": {"iterations": 100}},
      "edges": {"smooth": {"type": "curvedCW", "roundness": 0.2}},
      "interaction": {"hover": true, "tooltipDelay": 100}
    }
    """)

    for node in kg.nodes:
        score = node.score
        if node.understood and score >= 0.7:
            color = "#1D9E75"
            border = "#0F6E56"
        elif score >= 0.4:
            color = "#EF9F27"
            border = "#BA7517"
        else:
            color = "#E24B4A"
            border = "#A32D2D"

        size = 20 + int(score * 20)
        net.add_node(
            node.id,
            label=node.label,
            color={"background": color, "border": border, "highlight": {"background": color, "border": "#222"}},
            size=size,
            title=f"{node.label}\nMastery: {score:.0%}",
            font={"color": "#fff", "size": 13, "bold": True},
        )

    for edge in kg.edges:
        if edge.source in [n.id for n in kg.nodes] and edge.target in [n.id for n in kg.nodes]:
            net.add_edge(
                edge.source, edge.target,
                label=edge.relation,
                color="#aaa",
                font={"size": 10, "color": "#888"},
                arrows="to",
            )

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
        path = f.name

    net.save_graph(path)
    with open(path, "r") as f:
        html = f.read()
    os.unlink(path)
    return html


def get_graph_stats(kg: KnowledgeGraph) -> dict:
    total = len(kg.nodes)
    understood = sum(1 for n in kg.nodes if n.understood)
    avg_score = sum(n.score for n in kg.nodes) / total if total else 0
    return {
        "total_nodes": total,
        "understood": understood,
        "gaps": total - understood,
        "mastery_pct": int(avg_score * 100),
    }

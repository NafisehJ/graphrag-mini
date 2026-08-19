from pathlib import Path

import arxiv


QUERY = 'all:"knowledge graph" AND all:"retrieval augmented generation"'
PAPER_COUNT = 20
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def fetch_abstracts() -> None:
    search = arxiv.Search(
        query=QUERY,
        max_results=PAPER_COUNT,
        sort_by=arxiv.SortCriterion.Relevance,
    )
    client = arxiv.Client()
    papers = list(client.results(search))

    if len(papers) < PAPER_COUNT:
        raise RuntimeError(
            f"Expected {PAPER_COUNT} papers, but arXiv returned {len(papers)}."
        )

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for index, paper in enumerate(papers[:PAPER_COUNT], start=1):
        output_path = DATA_DIR / f"paper_{index:02d}.txt"
        output_path.write_text(
            f"{paper.title.strip()}\n\n{paper.summary.strip()}\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    fetch_abstracts()
import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.tools import tool
import feedparser
from urllib.parse import quote

ARXIV_API = "http://export.arxiv.org/api/query"


# Defining tools
@tool
def search_arxiv(query, max_results=5, start=0):
    """Search for research papers on arXiv based on a query."""

    query = quote(query)
    url = (
        f"{ARXIV_API}?"
        f"search_query=all:{query}"
        f"&start={start}"
        f"&max_results={max_results}"
        f"&sortBy=submittedDate"
        f"&sortOrder=descending"
    )
    # print(url)
    feed = feedparser.parse(url)

    results = []
    for entry in feed.entries:
        results.append(
            {
                "id": entry.id,
                "title": entry.title.strip().replace("\n", " "),
                "published": entry.published,
            }
        )
    return results


@tool
def fetch_abstract(arxiv_id):
    """
    Fetch the abstract of a research paper from arXiv given its ID.
    """
    url = f"{ARXIV_API}?id_list={arxiv_id.split('/')[-1]}"
    feed = feedparser.parse(url)

    if not feed.entries:
        return None

    entry = feed.entries[0]
    return entry.summary.strip().replace("\n", " ")


@tool
def save_markdown(query, content):
    """
    Docstring for save_markdown

    :param query: name of the file
    :param content: content to be saved
    """
    filename = f"SLROutput/{query}.md"
    with open(filename, "w") as f:
        f.write(content)
    return f"Markdown summary saved to {filename}"


# Define system prompts for specialized agents
PAPER_CRAWLER_SYSTEM_PROMPT = """
You are an AI assistant that helps users find research papers from arXiv.
Use the `search_arxiv` tool to search for papers.

IMPORTANT: Always format your response as a Python dictionary with arxiv_id as keys and paper titles as values.
Example output:
{
    "http://arxiv.org/abs/2301.00001": "Title of First Paper",
    "http://arxiv.org/abs/2301.00002": "Title of Second Paper"
}

Return ONLY the dictionary, no other text.
"""

PAPER_SUMMARIZER_SYSTEM_PROMPT = """
You are an AI assistant that summarizes research papers from arXiv.
Use the `fetch_abstract` tool to fetch the abstract of a paper.
"""

PAPER_CLAIM_EXTRACTOR_SYSTEM_PROMPT = """
You are an AI assistant that extracts claims from a paper summary.
Identify and list the key claims made in the summary.
"""

PAPER_CLAIM_VERIFIER_SYSTEM_PROMPT = """
You are an AI assistant that verifies claims from a paper summary.
Identfy whether each claim is supported, refuted, or not enough information is available in the summary.
"""

FINDING_SYNTHESIZER_SYSTEM_PROMPT = """
You are an AI assistant that synthesizes findings from multiple research paper summaries and their claims.
Prepare a summary of findings,their claims, and a list of references in a markdown format and save it to a file.
Use the `save_markdown` tool to save the markdown summary to a file.
"""

# Define LLM engine
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def make_paper_crawler_agent():
    return create_agent(
        model=llm,
        tools=[search_arxiv],
        system_prompt=PAPER_CRAWLER_SYSTEM_PROMPT,
    )


def make_summarizer_agent():
    return create_agent(
        model=llm, tools=[fetch_abstract], system_prompt=PAPER_SUMMARIZER_SYSTEM_PROMPT
    )


def make_claim_extractor_agent():
    return create_agent(model=llm, system_prompt=PAPER_CLAIM_EXTRACTOR_SYSTEM_PROMPT)


def make_claim_verifier_agent():
    return create_agent(model=llm, system_prompt=PAPER_CLAIM_VERIFIER_SYSTEM_PROMPT)


def make_result_synthesizer_agent():
    return create_agent(
        model=llm,
        system_prompt=FINDING_SYNTHESIZER_SYSTEM_PROMPT,
        tools=[save_markdown],
    )

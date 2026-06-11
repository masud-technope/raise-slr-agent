import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Loading dependencies
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.tools import tool
import feedparser
from urllib.parse import quote
import asyncio
import time

ARXIV_API = "http://export.arxiv.org/api/query"


# Defining tools
@tool
def search_arxiv(
    query,
    max_results=5,
    start=0
):
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
        results.append({
            "id": entry.id,
            "title": entry.title.strip().replace("\n", " "),
            "published": entry.published
        })
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


# Define LLM engine
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

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

# Define the agent output formats
from pydantic import BaseModel
from typing import Dict

class PaperResult(BaseModel):
    """Key-value pair format for paper results"""
    papers: Dict[str, str]  # key: arxiv_id, value: paper_title
    total_count: int

class CrawlerOutput(BaseModel):
    query: str
    results: PaperResult

# Defining the agents    
def make_paper_crawler_agent():
    return create_agent(
        model=llm,
        tools=[search_arxiv],
        system_prompt=PAPER_CRAWLER_SYSTEM_PROMPT,
    )

def make_summarizer_agent():
    return create_agent(
        model=llm,
        tools=[fetch_abstract],
        system_prompt=PAPER_SUMMARIZER_SYSTEM_PROMPT 
    )

def make_claim_extractor_agent():
    return create_agent(
        model=llm,
        system_prompt=PAPER_CLAIM_EXTRACTOR_SYSTEM_PROMPT 
    )

def make_claim_verifier_agent():
    return create_agent(
        model=llm,
        system_prompt=PAPER_CLAIM_VERIFIER_SYSTEM_PROMPT 
    )

def make_result_synthesizer_agent():
    return create_agent(
        model=llm,
        system_prompt=FINDING_SYNTHESIZER_SYSTEM_PROMPT,
        tools=[save_markdown] 
    )

class SLRAgentPipeline():
    def __init__(self):
        self.crawler = make_paper_crawler_agent()
        self.summarizer = make_summarizer_agent()
        self.claim_extractor = make_claim_extractor_agent()
        self.claim_verifier = make_claim_verifier_agent()
        self.synthesizer = make_result_synthesizer_agent()
    
    def get_relevant_papers(self, query):
        response = self.crawler.invoke({"messages":query, "role":"user"})
        result_text = response["messages"][-1].content
        try:
            # Parse the dictionary response
            import ast
            papers_dict = ast.literal_eval(result_text.strip())
        
            return {
                "query": query,
                "results": {
                    "papers": papers_dict,
                    "total_count": len(papers_dict)
                }
            }
        except (ValueError, SyntaxError):
            return {
                "query": query,
                "results": {
                    "papers": {},
                    "total_count": 0,
                    "error": "Failed to parse results"
                }
            }
    
    def collect_paper_claims(self, paper_entries):
        claims_dict = {}
        summary_dict = {}
        for paper in paper_entries.keys():
            summary_result = self.summarizer.invoke({"messages":paper,"role":"user"})
            summary = summary_result["messages"][-1].content
            summary_dict[paper] = summary
            claim_result = self.claim_extractor.invoke({"messages": summary, "role":"user"})
            claims = claim_result["messages"][-1].content
            claims_dict[paper] = claims
        return summary_dict, claims_dict
    
    def verify_paper_claims(self, paper_entries, summary_dict, claims_dict):
        verified_claims_dict = {}
        for paper in paper_entries.keys():
            summary = summary_dict[paper]
            claims = claims_dict[paper]
            claim_result = self.claim_verifier.invoke({"messages": claims +" "+summary, "role":"user"})
            verified_claims = claim_result["messages"][-1].content
            verified_claims_dict[paper] = verified_claims
        return verified_claims_dict
    
    def convert_strings(self, key_values):
        lines = [f'{k}={v}' for k, v in key_values.items()]
        return '\n'.join(lines)
    
    def synthesize_findings(self, summary_dict, claims_dict, verified_claims_dict):
        findings_result = self.synthesizer.invoke( {"messages": self.convert_strings(summary_dict) + "\n" +
            self.convert_strings(claims_dict) + "\n" +
            self.convert_strings(verified_claims_dict), "role":"user"})
        findings = findings_result["messages"][-1].content
        return findings
    
    def run_slr_pipeline(self, query):
        collected_papers = self.get_relevant_papers(query)
        paper_entries = collected_papers["results"]["papers"]
        summary_dict, claims_dict = self.collect_paper_claims(paper_entries)    
        verified_claims_dict = self.verify_paper_claims(paper_entries, summary_dict, claims_dict)
        self.synthesize_findings(summary_dict, claims_dict, verified_claims_dict)
        return summary_dict, claims_dict, verified_claims_dict
    

if __name__ == "__main__":
    start = time.time()
    pipeline = SLRAgentPipeline()
    summary_dict, claims_dict, verified_claims_dict = pipeline.run_slr_pipeline("Fault injection in AI models") 

    for paper in summary_dict.keys():
        print(f"ID: {paper} \nSummary: {summary_dict[paper]} \nClaim: {claims_dict[paper]} \nVerification: {verified_claims_dict[paper]}") 

    print(f"Total time: {time.time() - start}")  
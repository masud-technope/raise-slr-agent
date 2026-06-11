# Define the agent output formats
from pydantic import BaseModel
from typing import Dict
from agents.all_agents import (
    make_paper_crawler_agent,
    make_summarizer_agent,
    make_claim_extractor_agent,
    make_claim_verifier_agent,
    make_result_synthesizer_agent,
)


class PaperResult(BaseModel):
    """Key-value pair format for paper results"""

    papers: Dict[str, str]  # key: arxiv_id, value: paper_title
    total_count: int


class CrawlerOutput(BaseModel):
    query: str
    results: PaperResult


class SLRAgentPipeline:
    def __init__(self):
        self.crawler = make_paper_crawler_agent()
        self.summarizer = make_summarizer_agent()
        self.claim_extractor = make_claim_extractor_agent()
        self.claim_verifier = make_claim_verifier_agent()
        self.synthesizer = make_result_synthesizer_agent()

    def get_relevant_papers(self, query):
        response = self.crawler.invoke({"messages": query, "role": "user"})
        result_text = response["messages"][-1].content
        try:
            # Parse the dictionary response
            import ast

            papers_dict = ast.literal_eval(result_text.strip())

            return {
                "query": query,
                "results": {"papers": papers_dict, "total_count": len(papers_dict)},
            }
        except (ValueError, SyntaxError):
            return {
                "query": query,
                "results": {
                    "papers": {},
                    "total_count": 0,
                    "error": "Failed to parse results",
                },
            }

    def collect_paper_claims(self, paper_entries):
        claims_dict = {}
        summary_dict = {}
        for paper in paper_entries.keys():
            summary_result = self.summarizer.invoke({"messages": paper, "role": "user"})
            summary = summary_result["messages"][-1].content
            summary_dict[paper] = summary
            claim_result = self.claim_extractor.invoke(
                {"messages": summary, "role": "user"}
            )
            claims = claim_result["messages"][-1].content
            claims_dict[paper] = claims
        return summary_dict, claims_dict

    def verify_paper_claims(self, paper_entries, summary_dict, claims_dict):
        verified_claims_dict = {}
        for paper in paper_entries.keys():
            summary = summary_dict[paper]
            claims = claims_dict[paper]
            claim_result = self.claim_verifier.invoke(
                {"messages": claims + " " + summary, "role": "user"}
            )
            verified_claims = claim_result["messages"][-1].content
            verified_claims_dict[paper] = verified_claims
        return verified_claims_dict

    def convert_strings(self, key_values):
        lines = [f"{k}={v}" for k, v in key_values.items()]
        return "\n".join(lines)

    def synthesize_findings(self, summary_dict, claims_dict, verified_claims_dict):
        findings_result = self.synthesizer.invoke(
            {
                "messages": self.convert_strings(summary_dict)
                + "\n"
                + self.convert_strings(claims_dict)
                + "\n"
                + self.convert_strings(verified_claims_dict),
                "role": "user",
            }
        )
        findings = findings_result["messages"][-1].content
        return findings

    def run_slr_pipeline(self, query):
        collected_papers = self.get_relevant_papers(query)
        paper_entries = collected_papers["results"]["papers"]
        summary_dict, claims_dict = self.collect_paper_claims(paper_entries)
        verified_claims_dict = self.verify_paper_claims(
            paper_entries, summary_dict, claims_dict
        )
        self.synthesize_findings(summary_dict, claims_dict, verified_claims_dict)
        return summary_dict, claims_dict, verified_claims_dict

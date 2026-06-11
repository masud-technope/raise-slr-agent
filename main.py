import time
from pipeline.slr_pipeline import SLRAgentPipeline

start = time.time()
pipeline = SLRAgentPipeline()
summary_dict, claims_dict, verified_claims_dict = pipeline.run_slr_pipeline(
    "Harness engineering in agentic AI"
)

for paper in summary_dict.keys():
    print(
        f"ID: {paper} \nSummary: {summary_dict[paper]} \nClaim: {claims_dict[paper]} \nVerification: {verified_claims_dict[paper]}"
    )
    print(f"Total time: {time.time() - start}")

# RAISE SLR Agent

An AI-powered agent that automates literature reviews by searching, analyzing, and synthesizing research papers.

## Envisioned Features

* Automated paper search
* Paper ranking and filtering
* Research paper summarization
* Research gap identification
* Literature review generation
* Citation extraction

## Architecture

```text
User Query
    ↓
Planner
    ↓
Search Agent
    ↓
Paper Retriever
    ↓
Analyzer
    ↓
Review Generator
    ↓
Final Report
```

## Installation

```bash
git clone https://github.com/masud-technope/raise-slr-agent
cd raise-slr-agent

pip install -r requirements.txt
```

## Configuration

Create a `.env` file:

```bash
OPENAI_API_KEY=your_key
```

## Usage

```bash
python ArXivSLRAgent.py \
  --query "Agentic AI debugging" \
  --max-papers 20
```

## Example Output

* Key papers
* Major themes
* Research gaps
* Future directions
* Bibliography

## Project Structure

```text
src/
├── agents/
├── tools/
├── workflows/
├── prompts/

data/
tests/
examples/
```

## Limitations

* Dependent on external APIs
* May miss paywalled papers
* LLM-generated summaries may contain errors

## Citation

```bibtex
@software{litreviewagent,
  title={RAISE Systematic Literature Review Agent},
  author={Masud Rahman},
  year={2026}
}
```

## License

MIT License

import json
import re

def parse_agent_output(output_string):
    """
    Parse agent output string with key=value pairs and return as JSON.
    Handles quoted values with escaped quotes.
    """
    # Pattern to match key='value' including escaped quotes within values
    pattern = r"(\w+)='((?:[^'\\]|\\.)*?)'"

    matches = re.findall(pattern, output_string)
    result = {key: value for key, value in matches}

    return result

def format_to_json(output_string, indent=2):
    """Parse and return as formatted JSON string."""
    data = parse_agent_output(output_string)
    return json.dumps(data, indent=indent, ensure_ascii=False)

# Example usage
if __name__ == "__main__":
    agent_output = """Returning structured response: summary='This paper investigates the impact of data quality issues in deep learning models used for software engineering tasks. It focuses on three types of data: code-based, text-based, and metric-based, and compares models trained on clean datasets versus those with quality issues. The authors analyze the effects of these issues on model performance, identifying symptoms such as biased learning, gradient instability, overfitting, and exploding gradients. The findings are validated using six new datasets, providing insights for practitioners and researchers on improving data monitoring and cleaning methods.' strengths='The paper addresses a significant gap in the literature regarding the impact of data quality on deep learning models in software engineering. It employs a comprehensive empirical investigation and provides valuable insights into the symptoms of data quality issues. The validation of findings using multiple datasets enhances the credibility of the research.' weaknesses='The paper lacks a detailed discussion on the specific methodologies used for data cleaning and monitoring systems. While it identifies the symptoms of data quality issues, it does not provide concrete solutions or frameworks for practitioners to implement these findings effectively.' detailed_comments="The research presents important findings that can influence future work in the field of software engineering and deep learning. However, the lack of practical recommendations for addressing the identified data quality issues limits the applicability of the research. Including case studies or examples of successful data cleaning implementations could strengthen the paper\'s contribution to the field.\""""

    # Parse to dictionary
    data = parse_agent_output(agent_output)

    # Print as JSON
    print(format_to_json(agent_output))

    # Or access as dictionary
    # print(data['summary'])

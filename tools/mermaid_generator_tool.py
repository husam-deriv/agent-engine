from agents import tool
from openai import OpenAI
from agents import function_tool
import asyncio

@function_tool
def generate_mermaid_flowchart(chart_description: str) -> str:
    """Generate MermaidJS flowchart syntax from a textual description input, allowing an AI Agent to create visual diagrams, flowcharts, sequence diagrams, and other Mermaid-supported visualizations without needing to know the specific syntax; Args: chart_description (str): textual description of the desired diagram; Returns: str: MermaidJS syntax wrapped in code block."""
    try:
        client = OpenAI() # Assumes OPENAI_API_KEY is set in the environment

        completion = client.chat.completions.create(
            model="gpt-4.1", # As specified by the user
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in MermaidJS. Based on the following description, generate the MermaidJS syntax. You MUST output ONLY the MermaidJS code block itself, exactly in the format: ```mermaid\\n...chart_code_here...\\n```. Do not include any other explanatory text or markdown formatting before or after the code block."
                },
                {
                    "role": "user",
                    "content": chart_description
                }
            ]
        )

        response_content = completion.choices[0].message.content
        
        # Validate if the response is in the expected format.
        # The prompt asks for this specific format, so we expect it.
        if response_content and response_content.startswith("```mermaid") and response_content.endswith("```"):
            return response_content
        else:
            # If the LLM doesn't perfectly follow the format, wrap it or return an error/warning.
            # For now, let's assume it might sometimes miss the backticks, so we add them.
            # A more robust solution might try to extract if possible, or just return error.
            # Based on prompt, strict return is expected.
            # If it's not as expected, it indicates an issue with LLM response or prompt adherence.
            error_message = f"Error: LLM response was not in the expected format. Received:\\n{response_content}"
            # Fallback: Try to wrap if it looks like raw mermaid code. This is a simple check.
            if response_content and not response_content.strip().startswith("```") and ("flowchart" in response_content or "graph" in response_content or "sequenceDiagram" in response_content or "gantt" in response_content):
                return f"```mermaid\\n{response_content.strip()}\\n```"
            return error_message

    except Exception as e:
        return f"Error generating Mermaid diagram: {str(e)}"

# Update __init__.py if the function name or file name changes significantly
# For now, assuming the old function `generate_mermaid` will be replaced by this one
# or this will be a new, additional tool. 

# if __name__ == "__main__":
#     # Example usage of the new function
#     # description = "A simple flowchart with three nodes: A (Start), B (Process), and C (End). Node A connects to B with label 'Go to Process', and B connects to C with label 'Finish'."
#     # mermaid_output = generate_mermaid_flowchart(description)
#     # print(mermaid_output)

#     # description_error_case = "" # Test empty description
#     # Note: OpenAI might refuse empty content, leading to an API error handled by the try-except.
#     # print("\\nTesting empty description:")
#     # mermaid_output_empty = generate_mermaid_flowchart(description_error_case)
#     # print(mermaid_output_empty)

#     # Example that might be complex for the old system but easy for LLM
#     complex_description = "Create a sequence diagram showing a user logging into a web application. The user sends credentials to the web server, the server validates with a database, and then returns a session token to the user."
#     print("\\nTesting sequence diagram description:")
#     mermaid_output_sequence = generate_mermaid_flowchart(complex_description)
#     print(mermaid_output_sequence)
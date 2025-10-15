import json
from pathlib import Path
from typing import Dict, Any, List

def generate_mermaid_diagram_from_file(json_file_path: str, include_conditions: bool = True) -> str:
    """Generate a Mermaid flowchart diagram from a decision tree JSON file."""

    with open(json_file_path, 'r') as f:
        data = f.read()

    return generate_mermaid_diagram_from_string(data, include_conditions)

def generate_mermaid_diagram_from_string(json_string: str, include_conditions: bool = True) -> str:

    data = json.loads(json_string)

    mermaid_lines = ["flowchart TD"]
    node_counter = 0

    def get_node_id() -> str:
        nonlocal node_counter
        node_counter += 1
        return f"N{node_counter}"

    def clean_text(text: str) -> str:
        """Clean text for Mermaid compatibility."""
        # Replace problematic characters and limit length
        text = text.replace('"', "'").replace('\n', ' ').replace('|', ' OR ')
        # # truncate
        # if len(text) > 80:
        #     text = text[:77] + "..."
        return text

    def process_node(node_data: Dict[Any, Any], parent_id: str = None) -> str:
        """Process a node and its branches recursively."""
        current_id = get_node_id()

        # Handle title node
        if "title" in node_data and "branches" in node_data:
            title = clean_text(node_data["title"])
            mermaid_lines.append(f'    {current_id}["{title}"]')

        # Handle regular branches
        elif "condition" in node_data and "name" in node_data:
            condition = clean_text(node_data["condition"])
            name = clean_text(node_data["name"])

            if "decision" in node_data:
                # Leaf node with decision
                decision = clean_text(node_data["decision"])
                if include_conditions:
                    mermaid_lines.append(f'    {current_id}["{name}<br/><br/>Condition: {condition}<br/><br/>Decision: {decision}"]')
                else:
                    mermaid_lines.append(f'    {current_id}["{name}<br/><br/>Decision: {decision}"]')
            else:
                # Branch node
                if include_conditions:
                    mermaid_lines.append(f'    {current_id}["{name}<br/><br/>Condition: {condition}"]')
                else:
                    mermaid_lines.append(f'    {current_id}["{name}"]')

        # Connect to parent
        if parent_id:
            mermaid_lines.append(f'    {parent_id} --> {current_id}')

        # Process child branches
        if "branches" in node_data:
            for branch in node_data["branches"]:
                process_node(branch, current_id)

        return current_id

    # Start processing from the decision tree
    if "decision_tree" in data:
        process_node(data["decision_tree"])

    # Add styling
    mermaid_lines.extend([
        "",
        "    %% Styling",
        "    classDef decisionNode fill:#e1f5fe,stroke:#01579b,stroke-width:2px",
        "    classDef leafNode fill:#f3e5f5,stroke:#4a148c,stroke-width:2px",
        "    classDef endNode fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px"
    ])

    return "\n".join(mermaid_lines)

def main():
    # Generate the diagram
    json_file = Path(__file__).parent / "example-4.json"  # Update this path as needed
    mermaid_code = generate_mermaid_diagram_from_file(json_file, include_conditions=True)

    # Save to file
    with open("decision_tree_diagram.mmd", "w") as f:
        f.write(mermaid_code)

    print("Mermaid diagram generated!")
    print("\nYou can:")
    print("1. Copy the content to https://mermaid.live/ to view")
    print("2. Use a Mermaid VS Code extension")
    print("3. Include in markdown: ```mermaid\\n[content]\\n```")
    print(f"\nFirst few lines of the diagram:")
    print(mermaid_code[:500] + "...")

if __name__ == "__main__":
    main()
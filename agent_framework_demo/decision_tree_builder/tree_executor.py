

from pydantic import BaseModel


class TreeExecutionResult(BaseModel):
    is_done: bool = False
    decision: str = "No treatment"
    path: list[str] = []


def execute_tree(tree: dict, indicators: dict, result=TreeExecutionResult()) -> TreeExecutionResult:
    """Execute the decision tree based on the provided indicators."""
    for branch in tree.get("branches", []):
        result = execute_tree_node(branch, indicators, result)
        if result.is_done:
            return result
    return result

def execute_tree_node(tree_node: dict, indicators: dict, result: TreeExecutionResult) -> TreeExecutionResult:
    """Execute the decision tree based on the provided indicators."""
    if evaluate_condition(tree_node["condition"], indicators):
        result.path.append(tree_node["name"])
        if not tree_node.get("branches"):
            result.is_done = True
            result.decision = tree_node["decision"]
            return result
        for branch in tree_node["branches"]:
            result = execute_tree_node(branch, indicators, result)
            if result:
                return result
        result.path.pop()
    return result


def evaluate_condition(condition_expr: str, indicators: dict) -> bool:
    replaced_condition = (
        condition_expr
            .replace("AND", "and")
            .replace("OR", "or")
            .replace("NOT", "not")
    )
    for name, value in indicators.items():
        replaced_condition = replaced_condition.replace(name, str(value))

    try:
        return eval(replaced_condition)
    except Exception as e:
        print(f"Error evaluating condition '{condition_expr}': {e}")
        return False
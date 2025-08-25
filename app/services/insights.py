# app/services/insights.py
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from app.llm.tools import check_budget_tracking_status_tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from app.llm.tools import (
    get_overall_stats_tool,
    check_budget_tracking_status_tool,
    get_budget_details_by_category_tool,
)

def build_llm_with_tools(db: Session, user_id: UUID, provider: str | None):
    # Create wrapper tools that have the db and user_id pre-filled
    @tool("get_overall_stats")
    def wrapped_get_overall_stats(days: int = 30) -> Dict[str, float]:
        """
        Return overall totals for the user:
        { income_30d, income_month, income_year, expense_30d, expense_month, expense_year }.
        'days' controls the rolling window used for the 30d metrics.
        """
        return get_overall_stats_tool.func(days=days, db=db, user_id=user_id)
    
    @tool("check_budget_tracking_status")
    def wrapped_check_budget_tracking_status() -> Dict[str, Any]:
        """
        Check if user is on track with their budgets. Returns comprehensive budget analysis.
        
        Returns:
        - has_budgets: bool - whether user has any active budgets
        - budget_count: int - number of active budgets
        - budgets: list - detailed budget analysis for each active budget
        - overall_status: str - overall budget health status
        - message: str - summary message about budget status
        """
        return check_budget_tracking_status_tool.func(db=db, user_id=user_id)
    
    @tool("get_budget_details_by_category")
    def wrapped_get_budget_details_by_category(category: str) -> Dict[str, Any]:
        """
        Get detailed budget information for a specific category.

        Args:
            category: The budget category to analyze

        Returns detailed budget analysis for the specified category.
        """
        return get_budget_details_by_category_tool.func(category=category, db=db, user_id=user_id)

    tools = [
        wrapped_get_overall_stats,
        wrapped_check_budget_tracking_status,
        wrapped_get_budget_details_by_category,
    ]

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    return llm.bind_tools(tools), tools

def run_on_track(db: Session, user_id: UUID, *, days: int = 30, provider: Optional[str] = None) -> Dict[str, Any]:
    try:
        # First, check if user has any active budgets        
        budget_status = check_budget_tracking_status_tool.func(db=db, user_id=user_id)
        
        # If no budgets, return predefined response
        if not budget_status.get("has_budgets", False):
            return {
                "mode": "no_budgets",
                "text": "You currently have no active budgets, so I can't determine your budget progress. To track your financial status, please create some budgets first. Once you have active budgets, I can help you analyze your progress!",
                "suggestion": "create_budgets"
            }
        
        # If user has budgets, use LLM for analysis
        agent, tools = build_llm_with_tools(db, user_id, provider)
        
        system = SystemMessage(content=(
            "You are a financial analyst providing budget progress reports. "
            "ALWAYS call check_budget_tracking_status first to get the data. "
            "Then provide a structured analysis with:\n\n"
            "1. BUDGET BREAKDOWN (for each budget):\n"
            "   - Category: [name] | Budget: $X | Spent: $Y | Remaining: $Z (X% used)\n"
            "   - Status: [on_track/warning/exceeded]\n\n"
            "2. SUMMARY:\n"
            "   - Total budgets: X\n"
            "   - On track: X | Exceeded: X\n"
            "   - Total remaining: $X across all budgets\n\n"
            "3. ONE actionable insight (1 sentence)\n\n"
            "Use EXACT numbers from the tool data. Be factual and structured but be fun and encouraging."
        ))
        user = HumanMessage(content=f"Based on my current budgets, how am I doing? Please provide specific feedback on my budget performance.")

        # Manual conversation flow with tool handling
        messages = [system, user]
        
        # First LLM call
        result = agent.invoke(messages)
        
        # Check if there are tool calls
        if hasattr(result, 'tool_calls') and result.tool_calls:
            # Add the assistant message with tool calls to conversation
            messages.append(result)
            
            # Execute tool calls and add results
            for tool_call in result.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                
                # Find and execute the matching tool
                tool_result = None
                for tool in tools:
                    if tool.name == tool_name:
                        try:
                            tool_result = tool.func(**tool_args)
                            break
                        except Exception as e:
                            tool_result = {"error": str(e)}
                
                # Add tool result to conversation
                from langchain_core.messages import ToolMessage
                messages.append(ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call['id']
                ))
            
            # Second LLM call with tool results
            final_result = agent.invoke(messages)
            
            return {
                "mode": "llm",
                "text": final_result.content,
                "budget_status": budget_status
            }
        else:
            return {
                "mode": "llm",
                "text": result.content or "No response from LLM",
                "budget_status": budget_status
            }
    except Exception as e:
        return {
            "mode": "error",
            "text": f"Error occurred: {str(e)}",
        }

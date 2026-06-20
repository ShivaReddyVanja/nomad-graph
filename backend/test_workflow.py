import json
from src.agents.workflow import build_workflow

def run_test():
    print("=== Compiling LangGraph Workflow ===")
    app = build_workflow()
    print("Workflow compiled successfully!\n")

    # Test Case 1: Complete input (should pass validation and run the full loop)
    inputs_complete = {
        "user_prompt": "I want a 3-day luxury food and historical trip from New York to Tokyo starting on 2026-07-01, style: coffee, temples, sushi, budget: $5000",
        "clarification_response": {},
        "is_validated": False,
        "transit": [],
        "accommodation": [],
        "food": [],
        "activities": [],
        "planned_destinations": []
    }

    print("=== Executing Workflow with Complete Input ===")
    print(f"Prompt: {inputs_complete['user_prompt']}\n")
    
    # Run the compiled graph
    config = {
        "recursion_limit": 50,
        "configurable": {"thread_id": "test_thread_complete"}
    }
    final_state = app.invoke(inputs_complete, config=config)

    print("\n=== Execution Results ===")
    print(f"Is Validated: {final_state.get('is_validated')}")
    print(f"Clarification Questions: {final_state.get('clarification_questions')}")
    
    itinerary = final_state.get("final_itinerary")
    if itinerary:
        print("\n=== Final Compiled Itinerary ===")
        # Pretty print the Pydantic model as JSON
        print(json.dumps(itinerary.model_dump(), indent=2))
        
        print("\n=== Validation Warnings ===")
        print(final_state.get("validation_warnings", []))
    else:
        print("\nError: Final itinerary was not generated!")

    print("\n" + "="*50 + "\n")

    # Test Case 2: Incomplete input (should fail validation and return clarification questions)
    inputs_incomplete = {
        "user_prompt": "I want a luxury trip to Paris, style: museums",
        "clarification_response": {},
        "is_validated": False,
        "transit": [],
        "accommodation": [],
        "food": [],
        "activities": [],
        "planned_destinations": []
    }

    print("=== Executing Workflow with Incomplete Input ===")
    print(f"Prompt: {inputs_incomplete['user_prompt']}\n")
    
    config_inc = {
        "recursion_limit": 50,
        "configurable": {"thread_id": "test_thread_incomplete"}
    }
    final_state_inc = app.invoke(inputs_incomplete, config=config_inc)

    print("\n=== Execution Results ===")
    print(f"Is Validated: {final_state_inc.get('is_validated')}")
    print(f"Clarification Questions: {final_state_inc.get('clarification_questions')}")

if __name__ == "__main__":
    run_test()

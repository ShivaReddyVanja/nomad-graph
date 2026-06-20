import json
import sys
from src.agents.workflow import build_workflow
from langgraph.types import Command

def run_interactive_planner():
    print("=" * 60)
    print("      WELCOME TO THE INTERACTIVE TRAVEL PLANNER ENGINE      ")
    print("=" * 60)
    
    print("\nCompiling LangGraph Workflow...")
    app = build_workflow()
    print("Workflow compiled successfully!\n")
    
    # Establish a unique session thread
    config = {"configurable": {"thread_id": "interactive_user_session"}}
    
    # 1. Capture the initial user prompt
    try:
        user_prompt = input("Enter your travel request (e.g., '3 days in Paris' or 'luxury trip to Rome'):\n> ")
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
        
    if not user_prompt.strip():
        print("Empty prompt. Exiting...")
        sys.exit(0)

    initial_input = {
        "user_prompt": user_prompt,
        "clarification_response": {},
        "is_validated": False,
        "transit": [],
        "accommodation": [],
        "food": [],
        "activities": []
    }

    print("\nStarting travel planning execution thread...")
    # Start execution
    app.invoke(initial_input, config=config)
    
    # 2. Main Conversation Loop (handling interrupts dynamically)
    while True:
        # Fetch latest state from the checkpoint
        thread_state = app.get_state(config)
        tasks = thread_state.tasks
        
        # Check if the graph is currently suspended on an interrupt
        has_interrupts = len(tasks) > 0 and len(tasks[0].interrupts) > 0
        
        if not has_interrupts:
            # No interrupts - graph has completed execution!
            break
            
        # Retrieve the questions payload from the interrupt
        questions = tasks[0].interrupts[0].value
        print("\n" + "!" * 50)
        print("  ACTION REQUIRED: The Gatekeeper needs clarification!")
        print("!" * 50)
        
        resume_payload = {}
        # Ask the user for answers to each clarifying question
        for question in questions:
            try:
                answer = input(f"\nQuestion: {question}\nYour Answer: ")
                resume_payload[question] = answer
            except KeyboardInterrupt:
                print("\nExiting...")
                sys.exit(0)
                
        # Resume the graph using the user responses
        print("\nSending answers and resuming travel planning execution thread...")
        app.invoke(Command(resume=resume_payload), config=config)

    # 3. Print the Final Compiled Itinerary
    final_state = app.get_state(config).values
    itinerary = final_state.get("final_itinerary")
    
    if itinerary:
        print("\n" + "=" * 60)
        print("            SUCCESS: FINAL COMPILED ITINERARY            ")
        print("=" * 60)
        print(json.dumps(itinerary.model_dump(), indent=2))
        
        warnings = final_state.get("validation_warnings", [])
        if warnings:
            print("\n[Itinerary Warnings]")
            for warning in warnings:
                print(f"- {warning}")
    else:
        print("\nFailed to generate final itinerary.")

if __name__ == "__main__":
    run_interactive_planner()

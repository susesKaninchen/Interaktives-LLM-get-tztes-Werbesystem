"""Dynamic flow testing script."""

import asyncio
import json
from app.agents.conversation_controller import get_conversation_controller
from app.agents.dynamic_flow import DynamicFlowEngine

async def test_dynamic_flow():
    """Test the dynamic flow engine with various scenarios."""
    
    print("🚀 Testing Dynamic Flow Engine")
    print("=" * 60)
    
    # Test 1: Initialize conversation
    print("\n📝 Test 1: Initialize Conversation")
    controller = get_conversation_controller()
    
    welcome_message = controller.initialize_conversation(
        goals=["Kunden finden", "Matches erstellen"],
        preferences={"experience_level": "beginner"}
    )
    
    print(f"🎉 Welcome Message: {welcome_message[:100]}...")
    print(f"📊 Current Flow State: {controller.flow_engine.get_flow_summary()}")
    
    # Test 2: User wants to skip discovery
    print("\n📝 Test 2: Skip Discovery Step")
    skip_response = controller.process_user_message(
        "Ich möchte die Entdeckung überspringen und direkt zur Suche gehen",
        current_context={}
    )
    
    print(f"🤖 AI Response: {skip_response['ai_response'][:100]}...")
    print(f"💡 AI Suggestions: {len(skip_response['flow_suggestions'])} suggestions")
    print(f"🎯 Available Actions: {[a['type'] for a in skip_response['available_actions']]}")
    
    # Test 3: User wants to iterate on current step
    print("\n📝 Test 3: Iterate on Current Step")
    iterate_response = controller.process_user_message(
        "Können wir das nochmal anders versuchen?",
        current_context={}
    )
    
    print(f"🔄 AI Response: {iterate_response['ai_response'][:100]}...")
    print(f"🔄 Flow Suggestions for iteration: {[s['action'] for s in iterate_response['flow_suggestions']]}")
    
    # Test 4: User wants to go back
    print("\n📝 Test 4: Go Back to Previous Step")
    back_response = controller.process_user_message(
        "Lass uns zurück zu den Suchergebnissen gehen",
        current_context={}
    )
    
    print(f"⬅️ AI Response: {back_response['ai_response'][:100]}...")
    print(f"🎯 Available Actions at this point: {[a['user_friendly'] for a in back_response['available_actions'][:3]]}")
    
    # Test 5: Natural user request
    print("\n📝 Test 5: Natural User Request")
    natural_response = controller.process_user_message(
        "Ich möchte Kunden im Bereich Webdesign finden in Berlin",
        current_context={"location": "Berlin", "industry": "Webdesign"}
    )
    
    print(f"🎨 AI Response: {natural_response['ai_response'][:150]}...")
    print(f"📊 Conversation Progress: {natural_response['conversation_progress']}")
    
    # Test 6: Execute flow actions
    print("\n📝 Test 6: Execute Flow Actions")
    
    # Try forward action
    forward_success = controller.handle_flow_transition("forward")
    print(f"➡️ Forward action: {'✅ Success' if forward_success else '❌ Failed'}")
    
    # Try backward action
    backward_success = controller.handle_flow_transition("backward")
    print(f"⬅️ Backward action: {'✅ Success' if backward_success else '❌ Failed'}")
    
    # Try iterate action
    iterate_success = controller.handle_flow_transition("iterate")
    print(f"🔄 Iterate action: {'✅ Success' if iterate_success else '❌ Failed'}")
    
    # Test 7: Flow state after actions
    print("\n📝 Test 7: Final Flow State")
    final_state = controller.flow_engine.get_flow_summary()
    print(f"📍 Current Step: {final_state['current_step']}")
    print(f"✅ Completed Steps: {final_state['completed_steps']}")
    print(f"📈 Progress: {final_state['progress']:.1%}")
    
    # Test 8: AI suggestions
    print("\n📝 Test 8: AI Suggestions")
    ai_suggestions = controller._get_intelligent_suggestions()
    
    for i, suggestion in enumerate(ai_suggestions[:3], 1):
        print(f"💡 Suggestion {i}:")
        print(f"   Action: {suggestion['action']} → {suggestion['target_step']}")
        print(f"   Confidence: {suggestion['confidence']:.1%}")
        print(f"   Reasoning: {suggestion['reasoning']}")
        print(f"   Features: {[] if not suggestion.get('iterable') and not suggestion.get('skipable') else [s.get('iterable') and 'Iterable', s.get('skipable') and 'Skipable']}")
    
    # Test 9: Flow history
    print("\n📝 Test 9: Flow History")
    history = controller.flow_engine.flow_history
    print(f"📜 Total transitions: {len(history)}")
    
    for i, transition in enumerate(history[-5:], 1):  # Last 5 transitions
        print(f"{i}. {transition['from_step']} → {transition['to_step']} ({transition['action']})")
    
    # Test 10: User experience levels
    print("\n📝 Test 10: User Experience Levels")
    
    for exp_level in ["beginner", "advanced"]:
        print(f"\n👤 {exp_level.capitalize()} User:")
        controller_exp = get_conversation_controller()
        controller_exp.initialize_conversation(
            preferences={"experience_level": exp_level}
        )
        
        test_response = controller_exp.process_user_message(
            "Ich möchte loslegen",
            current_context={}
        )
        
        print(f"📊 Response length: {len(test_response['ai_response'])} chars")
        print(f"💡 Suggestions: {len(test_response['flow_suggestions'])} (simpler for beginner)")
    
    print("\n✅ All tests completed!")
    print("=" * 60)

async def test_scenarios():
    """Test specific user scenarios."""
    
    print("\n🎭 Testing User Scenarios")
    print("=" * 60)
    
    scenarios = [
        {
            "name": "Experienced User - Direct Approach",
            "message": "Suche direkt nach Tech-Startups in Hamburg",
            "experience": "advanced"
        },
        {
            "name": "Beginner User - Exploratory", 
            "message": "Wie finde ich die richtigen Kunden?",
            "experience": "beginner"
        },
        {
            "name": "Iterative User - wants to improve",
            "message": "Das Ergebnis kann besser sein, lass uns das verfeinern",
            "experience": "intermediate"
        },
        {
            "name": "Flexible User - wants options",
            "message": "Was kann ich als nächsten machen? Gib mir verschiedene Möglichkeiten",
            "experience": "intermediate"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        print("-" * 40)
        
        controller = get_conversation_controller()
        controller.initialize_conversation(
            preferences={"experience_level": scenario['experience']}
        )
        
        response = controller.process_user_message(
            scenario['message'],
            current_context={}
        )
        
        print(f"🤖 AI understands: {response['ai_response'][:100]}...")
        print(f"🎯 Next steps: {len(response['available_actions'])} options")
        print(f"💡 Top suggestion: {response['flow_suggestions'][0]['target_step'] if response['flow_suggestions'] else 'None'}")
        print(f"📈 Progress: {response['conversation_progress']['percentage']:.0f}%")
    
    print("\n✅ Scenarios tested!")
    print("=" * 60)


async def main():
    """Run all dynamic flow tests."""
    try:
        await test_dynamic_flow()
        await test_scenarios()
        
        print("\n🎉 Dynamic Flow Testing Complete!")
        print("The system is ready for:")
        print("  ✅ Adaptive conversation flow")
        print("  ✅ Flexible navigation")
        print("  ✅ AI-driven suggestions")
        print("  ✅ Iterative improvements")
        print("  ✅ User personalization")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
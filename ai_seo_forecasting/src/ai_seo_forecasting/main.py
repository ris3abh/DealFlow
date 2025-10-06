#!/usr/bin/env python
"""
AI SEO Forecasting - Main Entry Point

This is the main entry point for running the AI SEO Forecasting crew.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ai_seo_forecasting.crew import AiSeoForecastingCrew


def validate_environment():
    """Validate that all required environment variables are set"""
    required_vars = {
        'AWR_API_KEY': 'Advanced Web Ranking API Key',
        'OPENAI_API_KEY': 'OpenAI API Key (or other LLM provider key)'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"  - {var}: {description}")
    
    if missing_vars:
        print("❌ Error: Missing required environment variables:\n")
        print("\n".join(missing_vars))
        print("\nPlease set these in your .env file or environment.")
        print("\nExample .env file:")
        print("AWR_API_KEY=your_awr_api_key_here")
        print("OPENAI_API_KEY=your_openai_api_key_here")
        return False
    
    return True


def run():
    """
    Run the AI SEO Forecasting crew.
    """
    print("🚀 Starting AI SEO Forecasting Crew...")
    print("="*60)
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    try:
        # Initialize and run the crew
        crew = AiSeoForecastingCrew()
        result = crew.crew().kickoff()
        
        print("\n" + "="*60)
        print("✅ Crew Execution Complete!")
        print("="*60)
        print("\nFinal Result:")
        print("-"*60)
        print(result)
        print("-"*60)
        
        return result
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Execution interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Error during execution: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def train():
    """
    Train the crew for a given number of iterations.
    """
    print("🎓 Training AI SEO Forecasting Crew...")
    print("="*60)
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    try:
        crew = AiSeoForecastingCrew()
        crew.crew().train(
            n_iterations=int(sys.argv[1]) if len(sys.argv) > 1 else 3,
            filename=sys.argv[2] if len(sys.argv) > 2 else "training_data.pkl"
        )
        
        print("\n✅ Training complete!")
        
    except Exception as e:
        print(f"\n❌ Training error: {str(e)}")
        sys.exit(1)


def replay():
    """
    Replay the crew execution from a specific task.
    """
    print("🔄 Replaying AI SEO Forecasting Crew...")
    print("="*60)
    
    try:
        crew = AiSeoForecastingCrew()
        crew.crew().replay(task_id=sys.argv[1])
        
    except IndexError:
        print("❌ Error: Please provide a task_id to replay")
        print("Usage: python main.py replay <task_id>")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Replay error: {str(e)}")
        sys.exit(1)


def test():
    """
    Test the crew execution and returns the results.
    """
    print("🧪 Testing AI SEO Forecasting Crew...")
    print("="*60)
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    try:
        crew = AiSeoForecastingCrew()
        crew.crew().test(
            n_iterations=int(sys.argv[1]) if len(sys.argv) > 1 else 3,
            openai_model_name=sys.argv[2] if len(sys.argv) > 2 else "gpt-4o-mini"
        )
        
        print("\n✅ Testing complete!")
        
    except Exception as e:
        print(f"\n❌ Testing error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "train":
            train()
        elif command == "replay":
            replay()
        elif command == "test":
            test()
        else:
            print(f"❌ Unknown command: {command}")
            print("\nAvailable commands:")
            print("  python main.py         - Run the crew")
            print("  python main.py train   - Train the crew")
            print("  python main.py replay  - Replay from a task")
            print("  python main.py test    - Test the crew")
            sys.exit(1)
    else:
        # Default: run the crew
        run()
import sys
from hardware_assistant.agent import HardwareAgent


def main():
    agent = HardwareAgent()
    print("=" * 65)
    print("  Local Linux Hardware Q&A Assistant (CLI)")
    print("  Safe Tool-Calling Engine (Anti-Hallucination Enabled)")
    print("  Type 'exit' or 'quit' to close.")
    print("=" * 65)

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"\nUser: {query}")
        print(f"Assistant: {agent.answer_query(query)}\n")
        return

    while True:
        try:
            query = input("\nUser: ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break
            response = agent.answer_query(query)
            print(f"Assistant: {response}")
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()


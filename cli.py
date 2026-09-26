import sys
import os

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.table import Table
    from rich.prompt import Prompt
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from agent.core import GaviAgent


def print_banner(console, is_live: bool, model_name: str):
    status_color = "green" if is_live else "yellow"
    status_text = f"[bold {status_color}]● ONLINE ({model_name})[/]" if is_live else f"[bold {status_color}]● LOCAL MODE (Add GEMINI_API_KEY for full AI)[/]"

    banner_text = f"""[bold cyan]╔════════════════════════════════════════════════════════╗[/]
[bold cyan]║[/]               [bold magenta]G A V I   2 . 0[/]                          [bold cyan]║[/]
[bold cyan]║[/]           [italic white]Your Personal Autonomous AI Agent[/]            [bold cyan]║[/]
[bold cyan]╚════════════════════════════════════════════════════════╝[/]
Status: {status_text}
Commands: [bold yellow]/help[/] for commands | [bold yellow]/tasks[/] | [bold yellow]/notes[/] | [bold yellow]/quit[/] to exit"""

    if HAS_RICH:
        console.print(Panel(banner_text, border_style="cyan"))
    else:
        print("========================================")
        print("           GAVI 2.0 AI AGENT           ")
        print(f" Status: {'ONLINE' if is_live else 'LOCAL MODE'}")
        print(" Type /help for commands, /quit to exit ")
        print("========================================")


def show_help(console):
    if HAS_RICH:
        table = Table(title="Gavi 2.0 Commands & Capabilities", border_style="cyan")
        table.add_column("Command / Action", style="bold yellow")
        table.add_column("Description", style="white")

        table.add_row("/tasks", "List all active pending tasks")
        table.add_row("/add <task>", "Quickly add a new task")
        table.add_row("/done <id>", "Mark a task as completed")
        table.add_row("/notes", "List all notes in your vault")
        table.add_row("/note <text>", "Quickly save a note")
        table.add_row("/memory", "View remembered facts and user profile")
        table.add_row("/time", "Show current system time and date")
        table.add_row("/clear", "Clear the terminal screen")
        table.add_row("/quit, /exit", "Exit Gavi 2.0")
        table.add_row("<Any question>", "Chat naturally with Gavi 2.0")
        console.print(table)
    else:
        print("""
Commands:
  /tasks        - List active tasks
  /add <task>   - Add a new task
  /done <id>    - Complete a task
  /notes        - Show saved notes
  /note <text>  - Save a note
  /memory       - Show profile memory
  /time         - Show system time
  /clear        - Clear terminal
  /quit         - Exit
  or just ask Gavi any question!
""")


def main():
    console = Console() if HAS_RICH else None
    agent = GaviAgent()

    print_banner(console, agent.is_live, agent.model_name)

    while True:
        try:
            if HAS_RICH:
                user_input = Prompt.ask("\n[bold cyan]You[/]").strip()
            else:
                user_input = input("\nYou > ").strip()

            if not user_input:
                continue

            # Command routing
            lower = user_input.lower()
            if lower in ["/quit", "/exit", "exit", "quit"]:
                if HAS_RICH:
                    console.print("[italic magenta]Gavi 2.0:[/] Goodbye! Have a productive day ahead! 👋")
                else:
                    print("Gavi 2.0: Goodbye! Have a productive day ahead! 👋")
                sys.exit(0)

            if lower == "/clear":
                os.system("cls" if os.name == "nt" else "clear")
                print_banner(console, agent.is_live, agent.model_name)
                continue

            if lower == "/help":
                show_help(console)
                continue

            if lower == "/tasks":
                user_input = "list tasks"
            elif lower.startswith("/add "):
                user_input = f"add task {user_input[5:].strip()}"
            elif lower.startswith("/done "):
                user_input = f"complete task {user_input[6:].strip()}"
            elif lower == "/notes":
                user_input = "list notes"
            elif lower.startswith("/note "):
                user_input = f"save note {user_input[6:].strip()}"
            elif lower == "/memory":
                user_input = "what do you remember about me?"
            elif lower == "/time":
                user_input = "what time is it?"

            # Ask Gavi
            if HAS_RICH:
                with console.status("[italic cyan]Gavi 2.0 is thinking...[/]", spinner="dots"):
                    result = agent.ask(user_input)
                console.print(f"\n[bold magenta]Gavi 2.0[/] [dim]({ 'Live' if result.get('live') else 'Local' }):[/]")
                console.print(Markdown(result["response"]))
            else:
                result = agent.ask(user_input)
                print(f"\nGavi 2.0: {result['response']}")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting Gavi 2.0. Goodbye!")
            sys.exit(0)


if __name__ == "__main__":
    main()

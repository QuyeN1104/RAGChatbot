"""
CLI Entry Point — Interactive chat loop.

Usage:
    python main_cli.py

Commands:
    /upload <path>  — Upload and ingest a PDF file
    /clear          — Clear conversation history
    /quit           — Exit the application
"""

from __future__ import annotations

import os
import glob
import logging
import readline
from pathlib import Path

from src.core.config import get_settings
from src.core.logger import get_logger, setup_root_logger
from src.core.llm_client import create_llm_client
from src.rag.document import load_pdf, chunk_documents
from src.rag.vector_store import VectorStoreManager
from src.rag.retriever import retrieve_context, generate_answer
from src.agent.router import classify_intent, execute_route
from src.agent.memory import get_memory
from src.agent.graph import create_agent_graph

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt

# Mute noisy loggers to keep CLI clean
logging.getLogger("httpx").setLevel(logging.ERROR)

logger = get_logger("CLI")
console = Console()





def main():
    """Main CLI chat loop."""
    setup_root_logger()
    
    # Completely hide logs from console for a clean chat experience
    logging.getLogger().setLevel(logging.CRITICAL)
    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).setLevel(logging.CRITICAL)

    console.print(Panel.fit("[bold blue]🤖 Agentic RAG Chatbot[/bold blue]", border_style="blue"))
    console.print("[dim]Initializing system... (Loading embedding model may take a few seconds)[/dim]")
    
    settings = get_settings()
    
    try:
        llm = create_llm_client("ollama")
        vector_store = VectorStoreManager()
        memory = get_memory()
    except Exception as e:
        console.print(f"[bold red]Error initializing components: {e}[/bold red]")
        return

    import uuid
    if memory.store._store:
        session_id = max(memory.store._store.keys(), key=lambda k: memory.store._store[k].get("last_accessed", ""))
        console.print(f"[dim]System: Resumed session [cyan]{session_id}[/cyan][/dim]")
    else:
        session_id = str(uuid.uuid4())[:8]
        console.print(f"[dim]System: Started new session [cyan]{session_id}[/cyan][/dim]")
    
    console.print(Panel("[bold]Commands:[/bold]\n"
                        "/upload <path>     — Upload PDF\n"
                        "/docs              — List uploaded documents\n"
                        "/delete_doc <name> — Delete document by name\n"
                        "/new               — Start a new chat session\n"
                        "/history           — List chat sessions\n"
                        "/session <id>      — Switch to a specific session\n"
                        "/clear             — Clear current session history\n"
                        "/quit              — Exit", 
                        title="Help", border_style="green"))

    
    while True:
        try:
            try:
                print() # Empty line for spacing
                # Use standard input with readline-safe ANSI color codes to prevent prompt deletion
                user_input = input("\001\033[1;32m\002You:\001\033[0m\002 ").strip()
            except EOFError:
                console.print("\n[dim]Goodbye![/dim]")
                break
            
            if not user_input:
                continue
                
            if user_input.lower() in ["/quit", "/exit"]:
                console.print("[dim]Goodbye![/dim]")
                break
                
            elif user_input.lower() == "/clear":
                memory.store.clear_session(session_id)
                console.print("[dim italic]System: Chat history cleared.[/dim italic]")
                continue
                
            elif user_input.lower().startswith("/upload"):
                parts = user_input.split(" ", 1)
                if len(parts) < 2:
                    console.print("[red]System: Please provide a path, e.g., /upload data/sample.pdf[/red]")
                    continue
                pdf_path = os.path.abspath(os.path.expanduser(parts[1].strip()))
                
                try:
                    with console.status(f"[bold cyan]Loading PDF from {pdf_path}..."):
                        docs = load_pdf(pdf_path)
                    
                    with console.status(f"[bold cyan]Chunking {len(docs)} pages..."):
                        chunks = chunk_documents(docs)
                        
                    with console.status(f"[bold cyan]Ingesting {len(chunks)} chunks into vector store..."):
                        vector_store.add_documents(chunks)
                        
                    console.print("[bold green]✔ Upload and ingestion complete![/bold green]")
                except Exception as e:
                    console.print(f"[bold red]System: Failed to upload document: {e}[/bold red]")
                continue
                
            elif user_input.lower() == "/docs":
                docs = vector_store.list_documents()
                if not docs:
                    console.print("[dim]System: No documents uploaded yet.[/dim]")
                else:
                    docs_text = "\n".join([f"- {doc}" for doc in docs])
                    console.print(Panel(docs_text, title="Uploaded Documents", border_style="cyan"))
                continue
                
            elif user_input.lower().startswith("/delete_doc"):
                parts = user_input.split(" ", 1)
                if len(parts) < 2:
                    console.print("[red]System: Please provide the document name, e.g., /delete_doc sample.pdf[/red]")
                    continue
                doc_name = parts[1].strip()
                if vector_store.delete_document(doc_name):
                    console.print(f"[bold green]✔ Deleted document: {doc_name}[/bold green]")
                else:
                    console.print(f"[bold yellow]System: Document '{doc_name}' not found.[/bold yellow]")
                continue
                
            elif user_input.lower() == "/new":
                import uuid
                session_id = str(uuid.uuid4())[:8]
                console.print(f"[bold green]✔ Started new session:[/bold green] [cyan]{session_id}[/cyan]")
                continue
                
            elif user_input.lower() == "/history":
                sessions = list(memory.store._store.keys())
                if not sessions:
                    console.print("[dim]System: No active sessions.[/dim]")
                else:
                    sess_text = ""
                    for s in sessions:
                        metadata = memory.store._store[s]
                        msg_count = len(metadata.get("messages", []))
                        last_acc = metadata.get("last_accessed", "N/A")
                        topic = metadata.get("topic", "N/A")
                        last_msg = metadata.get("last_user_message", "")
                        
                        if len(last_msg) > 40:
                            last_msg = last_msg[:37] + "..."
                            
                        mark = "*" if s == session_id else " "
                        sess_text += f"{mark} [bold]{s}[/bold]\n   Topic: {topic}\n   Last Msg: '{last_msg}'\n   Last Active: {last_acc} ({msg_count} msgs)\n\n"
                    console.print(Panel(sess_text.strip(), title="Chat Sessions", border_style="cyan"))
                continue
                
            elif user_input.lower().startswith("/session"):
                parts = user_input.split(" ", 1)
                if len(parts) < 2:
                    console.print("[red]System: Please provide a session ID, e.g., /session cli_session[/red]")
                    continue
                new_id = parts[1].strip()
                if new_id in memory.store._store:
                    session_id = new_id
                    console.print(f"[bold green]✔ Switched to session:[/bold green] [cyan]{session_id}[/cyan]")
                else:
                    console.print(f"[bold yellow]System: Session '{new_id}' not found. Start a new one with /new[/bold yellow]")
                continue
                
            # Build the LangGraph app
            app = create_agent_graph(llm, vector_store, memory)
            
            # Chat flow with LangGraph
            state = {
                "query": user_input,
                "session_id": session_id
            }
            
            with console.status("[bold blue]Assistant is thinking...[/bold blue]"):
                result = app.invoke(state)
            
            ai_message = result.get("answer", "")
            sources = result.get("sources", [])
            intent = result.get("intent", "GENERAL_CHAT")
            
            # Display answer
            console.print(Panel(Markdown(ai_message), title="[bold blue]Assistant[/bold blue]", border_style="blue", title_align="left"))
            
            if sources and intent == "INTERNAL_DOC":
                sources_text = ""
                for i, src in enumerate(sources):
                    sources_text += f"[{i+1}] **{src.get('source')}** (Page {src.get('page')})\n"
                console.print(Panel(Markdown(sources_text), title="[dim]Sources[/dim]", border_style="dim", title_align="left"))
            
        except KeyboardInterrupt:
            console.print("\n[dim italic]Message cancelled. Press Ctrl+D or type /quit to exit.[/dim italic]")
            continue
        except Exception as e:
            console.print(f"\n[bold red]System Error: {e}[/bold red]")


if __name__ == "__main__":
    main()

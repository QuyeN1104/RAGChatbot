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

from src.core.logger import setup_root_logger

# TODO: Implement in Sprint 1, Day 6


def main():
    """Main CLI chat loop."""
    setup_root_logger()
    print("🤖 Agentic RAG Chatbot")
    print("=" * 40)
    print("Commands: /upload <path>, /clear, /quit")
    print()

    # TODO: Initialize LLM, VectorStore, Memory
    # TODO: Interactive while loop

    print("⚠️  CLI not yet implemented. Coming in Day 6!")


if __name__ == "__main__":
    main()

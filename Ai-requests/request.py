#!/usr/bin/env python3
"""
Demo script – call the Open‑WebUI chat endpoint once and print the result.

Usage
-----
    python3 chat_once.py                # token taken from $OPENWEBUI_API_KEY
    python3 chat_once.py --token <key>  # explicit token
    python3 chat_once.py --model gpt-oss-120b --question "Why is the sky blue?"
"""

import argparse
import json
import os
import sys

import requests


def chat_with_model(token: str, model: str = "gpt-oss-120b", question: str = "Why is the sky blue?") -> dict:
    """
    Send a single chat request.

    Parameters
    ----------
    token : str
        Bearer token for the API.
    model : str, optional
        Name of the model to use (default: "gpt-oss-120b").
    question : str, optional
        The user message that will be sent to the model.

    Returns
    -------
    dict
        Parsed JSON response from the server.
    """
    url = "https://open-webui.itestra.com/api/chat/completions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {
                # The API you showed omitted the "role" key – many providers default to "user".
                # Keeping it explicit makes the JSON clearer and works with most OpenAI‑compatible servers.
                "role": "user",
                "content": question,
            }
        ],
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
    except requests.RequestException as exc:
        # Network‑level problem (DNS, timeout, connection error …)
        sys.stderr.write(f"[ERROR] Could not contact the API: {exc}\n")
        sys.exit(1)

    if not response.ok:
        # The server answered with a non‑2xx status code.
        sys.stderr.write(
            f"[ERROR] HTTP {response.status_code} – {response.reason}\n"
            f"Body: {response.text}\n"
        )
        sys.exit(1)

    try:
        return response.json()
    except json.JSONDecodeError:
        sys.stderr.write("[ERROR] Server did not return valid JSON.\n")
        sys.exit(1)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a single chat request against the Open‑WebUI endpoint."
    )
    parser.add_argument(
        "--token",
        help="Bearer token for authentication. If omitted, the script reads $OPENWEBUI_API_KEY.",
    )
    parser.add_argument(
        "--model",
        default="gpt-oss-120b",
        help="Model identifier to use (default: %(default)s).",
    )
    parser.add_argument(
        "--question",
        default="Why is the sky blue?",
        help="Question/message that will be sent to the model (default: %(default)s).",
    )
    return parser


def main() -> None:
    args = _build_arg_parser().parse_args()

    # Resolve the token – command‑line argument overrides the environment variable.
    token = args.token or os.getenv("OPENWEBUI_API_KEY")
    if not token:
        sys.stderr.write(
            "[ERROR] No API token supplied. Use --token or set $OPENWEBUI_API_KEY.\n"
        )
        sys.exit(1)

    result = chat_with_model(token, model=args.model, question=args.question)

    # Pretty‑print the JSON response.
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
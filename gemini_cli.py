#!/usr/bin/env python3
"""
Gemini CLI — lightweight LLM tool for JARVIS.

Usage:
  gemini ask  "question"              — Quick answer
  gemini tr   "text" [lang]           — Translate (default: en)
  gemini ext  "text"                  — Extract entities for context graph
  gemini ext  -f file.txt             — Extract from file
  gemini sum  "text"                  — Summarize
  gemini sum  -f file.txt             — Summarize file
"""

import sys
import os
import json
import argparse

# Use new google.genai if available, fallback to deprecated
try:
    from google import genai
    from google.genai import types
    USE_NEW_API = True
except ImportError:
    import google.generativeai as genai
    USE_NEW_API = False

sys.path.insert(0, "/root/.openclaw/workspace")
from key_manager import KeyManager

MODELS = ["gemini-2.5-flash", "gemini-2.5-pro"]


def call_gemini(prompt, system=None, manager=None, temperature=0.3):
    """Call Gemini with key rotation."""
    if manager is None:
        manager = KeyManager()

    max_retries = len(manager.keys) * 2
    for attempt in range(max_retries):
        key = manager.get_key()
        try:
            if USE_NEW_API:
                client = genai.Client(api_key=key)
                config = types.GenerateContentConfig(
                    temperature=temperature,
                    system_instruction=system,
                )
                response = client.models.generate_content(
                    model=MODELS[0],
                    contents=prompt,
                    config=config,
                )
                return response.text
            else:
                genai.configure(api_key=key)
                model = genai.GenerativeModel(
                    f"models/{MODELS[0]}",
                    system_instruction=system,
                )
                response = model.generate_content(prompt)
                return response.text
        except Exception as e:
            err = str(e).lower()
            if "429" in str(e) or "quota" in err or "resource" in err:
                manager.rotate()
                continue
            elif "not found" in err or "not supported" in err:
                # Try fallback model
                MODELS[0] = MODELS[1] if MODELS[0] == "gemini-2.5-flash" else MODELS[0]
                continue
            else:
                print(f"Error: {e}", file=sys.stderr)
                return None
    print("All API keys exhausted.", file=sys.stderr)
    return None


def cmd_ask(args):
    """Quick question → answer."""
    result = call_gemini(
        args.text,
        system="Answer concisely in the same language as the question. No fluff.",
    )
    if result:
        print(result)


def cmd_translate(args):
    """Translate text."""
    lang = args.lang or "en"
    lang_names = {
        "en": "English", "ru": "Russian", "de": "German",
        "fr": "French", "es": "Spanish", "zh": "Chinese",
        "ja": "Japanese", "ko": "Korean",
    }
    target = lang_names.get(lang, lang)
    result = call_gemini(
        args.text,
        system=f"Translate the following text to {target}. Output ONLY the translation, nothing else.",
    )
    if result:
        print(result)


def cmd_extract(args):
    """Extract entities for context graph."""
    text = args.text
    if args.file:
        with open(args.file, "r") as f:
            text = f.read()

    # Load known actors
    actors = []
    actors_file = "/root/.openclaw/workspace/jarvis/memory/actors.md"
    if os.path.exists(actors_file):
        with open(actors_file) as f:
            for line in f:
                if "canonical_name:" in line:
                    actors.append(line.split(":", 1)[1].strip())

    system = f"""You are JARVIS entity extractor.
RULES:
1. Anti-Noise: Ignore greetings, small talk, emotions without facts. Return empty if nothing.
2. Only extract if confidence >= 0.7
3. Include source_quote for every entity
4. Known actors: {json.dumps(actors)}
5. Resolve actor names to known actors when possible

OUTPUT strictly valid JSON:
{{
  "actors": [{{"canonical_name":"","role":"","aliases":[]}}],
  "promises": [{{"from":"","to":"","content":"","deadline":null,"status":"pending","confidence":0.0,"source_quote":""}}],
  "decisions": [{{"content":"","date":"","confidence":0.0,"source_quote":""}}],
  "metrics": [{{"name":"","value":0,"unit":"","confidence":0.0,"source_quote":""}}],
  "plans": [{{"content":"","status":"active","confidence":0.0,"source_quote":""}}]
}}
Return ONLY JSON. No markdown, no explanation."""

    result = call_gemini(text, system=system, temperature=0.1)
    if result:
        # Clean markdown wrapping if present
        result = result.strip()
        if result.startswith("```"):
            result = "\n".join(result.split("\n")[1:])
        if result.endswith("```"):
            result = result.rsplit("```", 1)[0]
        result = result.strip()

        try:
            data = json.loads(result)
            # Count non-empty
            total = sum(len(v) for v in data.values() if isinstance(v, list))
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print(f"\n— {total} entities extracted", file=sys.stderr)
        except json.JSONDecodeError:
            print(result)


def cmd_audio(args):
    """Transcribe audio using Gemini."""
    manager = KeyManager()
    key = manager.get_key()
    
    # MIME type detection
    ext = os.path.splitext(args.file)[1].lower()
    mime = "audio/ogg" if ext == ".ogg" else "audio/mp3"
    
    try:
        if USE_NEW_API:
            client = genai.Client(api_key=key)
            with open(args.file, "rb") as f:
                file_data = f.read()
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(
                        parts=[
                            types.Part.from_bytes(data=file_data, mime_type=mime),
                            types.Part.from_text(text="Transcribe this audio verbatim.")
                        ]
                    )
                ]
            )
            print(response.text)
        else:
            print("Legacy genai not supported for audio. Update libs.", file=sys.stderr)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)


def cmd_summarize(args):
    """Summarize text."""
    text = args.text
    if args.file:
        with open(args.file, "r") as f:
            text = f.read()

    result = call_gemini(
        text,
        system="Summarize the following text concisely. Keep key facts, numbers, names. Same language as input.",
    )
    if result:
        print(result)


def main():
    parser = argparse.ArgumentParser(description="Gemini CLI for JARVIS")
    sub = parser.add_subparsers(dest="command")

    # ask
    p_ask = sub.add_parser("ask", help="Quick question")
    p_ask.add_argument("text", nargs="+")

    # translate
    p_tr = sub.add_parser("tr", help="Translate text")
    p_tr.add_argument("text", nargs="+")
    p_tr.add_argument("-l", "--lang", default="en", help="Target language (en/ru/de/...)")

    # extract
    p_ext = sub.add_parser("ext", help="Extract entities")
    p_ext.add_argument("text", nargs="*", default=[])
    p_ext.add_argument("-f", "--file", help="Read from file")

    # audio
    p_aud = sub.add_parser("audio", help="Transcribe audio")
    p_aud.add_argument("file", help="Audio file path")

    # summarize
    p_sum = sub.add_parser("sum", help="Summarize")
    p_sum.add_argument("text", nargs="*", default=[])
    p_sum.add_argument("-f", "--file", help="Read from file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Join text args
    if hasattr(args, "text") and isinstance(args.text, list):
        args.text = " ".join(args.text)

    commands = {
        "ask": cmd_ask,
        "tr": cmd_translate,
        "ext": cmd_extract,
        "audio": cmd_audio,
        "sum": cmd_summarize,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()

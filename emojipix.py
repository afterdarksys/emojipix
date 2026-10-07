#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import re
import sys
import unicodedata
import emoji
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console(emoji=False)

EMOTICONS = {
    ":)": "🙂",
    ":-)": "🙂",
    ":(": "🙁",
    ":-(": "🙁",
    ":D": "😀",
    ":-D": "😀",
    ";)": "😉",
    ";-)": "😉",
    ":P": "😛",
    ":-P": "😛",
    "xD": "😆",
    "XD": "😆",
    "xd": "😆",
    "<3": "❤️",
    "T_T": "😭",
    ":'(": "😢",
    "8-)": "😎",
    ":O": "😮",
    ":-O": "😮"
}

CHAT_MOODS = {
    "friendly": {
        "prefix": "✨",
        "suffix": "🙂",
        "instruction": "Use a light, friendly emoji style. Add 1-2 relevant emojis where they clarify tone, but keep the message easy to read.",
    },
    "hype": {
        "prefix": "🚀",
        "suffix": "🔥",
        "instruction": "Use energetic emojis to create momentum. Keep them relevant and avoid putting emojis after every sentence.",
    },
    "professional": {
        "prefix": "✅",
        "suffix": "",
        "instruction": "Use emojis sparingly for scanability, mostly for status, priority, and section markers. Avoid playful or overly casual emoji choices.",
    },
    "cozy": {
        "prefix": "🌿",
        "suffix": "☕",
        "instruction": "Use warm, calm emojis to soften the tone. Prefer gentle symbols and keep emoji density low.",
    },
    "minimal": {
        "prefix": "",
        "suffix": "",
        "instruction": "Use only the most useful emojis as visual markers. Do not decorate every sentence.",
    },
}

TOPIC_PALETTES = {
    "ai": ["🤖", "🧠", "✨", "⚙️", "📊", "🔍", "🚀", "✅"],
    "bug": ["🐛", "🔎", "🧪", "🛠️", "⚠️", "✅", "📌", "🚧"],
    "code": ["💻", "⚙️", "🧪", "🔧", "📦", "🚀", "✅", "📝"],
    "design": ["🎨", "🧩", "✨", "📐", "🖼️", "👀", "✅", "🚀"],
    "docs": ["📝", "📚", "🔖", "✅", "💡", "📌", "🔍", "✍️"],
    "launch": ["🚀", "✨", "📣", "✅", "🔥", "🎯", "📈", "🙌"],
    "meeting": ["📅", "📝", "✅", "💬", "📌", "⏱️", "🤝", "🎯"],
    "support": ["🛟", "🔎", "✅", "💬", "📌", "🙏", "⚠️", "🧭"],
    "writing": ["✍️", "📝", "💡", "📚", "✨", "🔖", "✅", "🎯"],
}

KEYWORD_EMOJIS = {
    "ai": "🤖",
    "idea": "💡",
    "ideas": "💡",
    "bug": "🐛",
    "fix": "🛠️",
    "fixed": "✅",
    "done": "✅",
    "ship": "🚀",
    "launch": "🚀",
    "fast": "⚡",
    "slow": "🐢",
    "warning": "⚠️",
    "important": "📌",
    "note": "📝",
    "write": "✍️",
    "docs": "📚",
    "search": "🔍",
    "test": "🧪",
    "tests": "🧪",
    "code": "💻",
    "design": "🎨",
    "data": "📊",
    "secure": "🔒",
    "security": "🔒",
    "love": "❤️",
    "thanks": "🙏",
    "thank": "🙏",
    "yes": "✅",
    "no": "❌",
    "blocked": "🚧",
    "question": "❓",
    "goal": "🎯",
    "win": "🏆",
}


def alias_list(details):
    aliases = []
    if 'en' in details:
        aliases.append(details['en'])
    if 'alias' in details:
        aliases.extend(details['alias'])
    return aliases


def codepoints(text):
    return " ".join([f"U+{ord(c):04X}" for c in text])


def is_variant_alias(alias):
    lowered = alias.lower()
    variant_terms = [
        "skin_tone",
        "light_skin",
        "medium-light_skin",
        "medium_skin",
        "medium-dark_skin",
        "dark_skin",
        "_tone",
    ]
    return any(term in lowered for term in variant_terms)


def text_to_emoji(text):
    if text in EMOTICONS:
        return EMOTICONS[text]
    
    # Formulate potential alias if not wrapped in colons
    search_text = text if text.startswith(":") and text.endswith(":") else f":{text}:"
    
    result = emoji.emojize(search_text, language='alias')
    
    if result == search_text and text not in emoji.EMOJI_DATA:
        return None
    return result

def emoji_to_info(char):
    char = char.strip()
    
    alias = emoji.demojize(char, language='alias')
    
    points = []
    for c in char:
        try:
            name = unicodedata.name(c)
        except ValueError:
            name = "UNKNOWN"
        h = f"U+{ord(c):04X}"
        points.append(f"{h} ({name})")
        
    return alias, points

def do_search(keyword):
    results = []
    keyword_lower = keyword.lower()
    
    for emo, emj in EMOTICONS.items():
        if keyword_lower in emo.lower():
            results.append((emo, emj, "Emoticon alias"))
            
    for emj, details in emoji.EMOJI_DATA.items():
        aliases = alias_list(details)
            
        for a in aliases:
            if keyword_lower in a.lower():
                results.append((a, emj, codepoints(emj)))
                break 
    return results

def do_list(limit=150, category=None):
    results = []
    for emj, details in emoji.EMOJI_DATA.items():
        aliases = alias_list(details)
        main_alias = aliases[0] if aliases else ":unknown:"

        if category and category.lower() not in main_alias.lower():
            continue

        results.append((main_alias, emj, codepoints(emj)))
        if len(results) >= limit:
            break
    return results


def compact_results(results, include_variants=False):
    seen = set()
    compacted = []
    for alias, emj, points in results:
        if not include_variants and is_variant_alias(alias):
            continue
        key = (alias, emj)
        if key in seen:
            continue
        seen.add(key)
        compacted.append((alias, emj, points))
    return compacted


def suggest_aliases(text, limit=5):
    needle = text.strip(":").lower().replace(" ", "_")
    candidates = []
    for emj, details in emoji.EMOJI_DATA.items():
        for alias in alias_list(details):
            normalized = alias.strip(":").lower()
            if needle and (needle in normalized or normalized in needle):
                candidates.append((alias, emj, codepoints(emj)))
                break
    return compact_results(candidates)[:limit]


def inject_emojis(text, mood="friendly", density=2):
    mood_data = CHAT_MOODS.get(mood, CHAT_MOODS["friendly"])
    result = text.strip()
    if not result:
        return ""

    used = set()
    max_insertions = max(0, density)

    def add_after_keyword(match):
        if len(used) >= max_insertions:
            return match.group(0)
        word = match.group(0)
        emoji_char = KEYWORD_EMOJIS.get(word.lower())
        if not emoji_char or emoji_char in used:
            return word
        used.add(emoji_char)
        return f"{word} {emoji_char}"

    result = re.sub(r"\b[\w']+\b", add_after_keyword, result, flags=re.IGNORECASE)

    prefix = mood_data["prefix"]
    suffix = mood_data["suffix"]
    if prefix and not result.startswith(prefix):
        result = f"{prefix} {result}"
    if suffix and len(used) < max_insertions and not result.endswith(suffix):
        result = f"{result} {suffix}"
    return result


def strip_emojis(text, preserve_spacing=True, strip_aliases=False):
    stripped = emoji.replace_emoji(text, replace="")
    stripped = stripped.replace("\ufe0f", "")
    if strip_aliases:
        stripped = re.sub(r"(?<!\w):[a-zA-Z0-9_+\-]+:(?!\w)", "", stripped)

    if not preserve_spacing:
        return stripped

    cleaned_lines = []
    for line in stripped.splitlines():
        line = re.sub(r"[ \t]{2,}", " ", line)
        line = re.sub(r"^[ \t]+$", "", line)
        line = re.sub(r"([([{])\s+", r"\1", line)
        line = re.sub(r"\s+([)\]},.;:!?])", r"\1", line)
        line = re.sub(r"\s+(</[^>]+>)", r"\1", line)
        cleaned_lines.append(line.rstrip())
    return "\n".join(cleaned_lines)


def read_stdin_if_available():
    if sys.stdin.isatty():
        return None
    return sys.stdin.read()


def read_strip_source(args):
    if args.strip_file:
        return Path(args.strip_file).read_text(encoding="utf-8")
    if args.strip:
        return args.strip
    return read_stdin_if_available()


def write_or_print_strip_result(args, result):
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        console.print(f"Wrote stripped text to {args.output}")
        return
    console.print(result, markup=False, end="" if result.endswith("\n") else "\n")


def make_prompt(mood="friendly", density="balanced"):
    mood_data = CHAT_MOODS.get(mood, CHAT_MOODS["friendly"])
    density_notes = {
        "low": "Use emojis rarely, only when they make intent or structure clearer.",
        "balanced": "Use a balanced amount: enough to add tone, not enough to distract.",
        "high": "Use emojis often for expressive, high-energy chat, while keeping the text readable.",
    }
    density_note = density_notes.get(density, density_notes["balanced"])
    return f"{mood_data['instruction']} {density_note}"


def palette_for(topic):
    normalized = topic.lower().strip()
    if normalized in TOPIC_PALETTES:
        return TOPIC_PALETTES[normalized]

    search_results = compact_results(do_search(normalized))
    return [emj for _, emj, _ in search_results[:8]]


def output_json(payload):
    console.print_json(json.dumps(payload, ensure_ascii=False))


def print_rows(title, rows, limit):
    table = Table(title=title)
    table.add_column("Alias/Trigger", style="cyan")
    table.add_column("Emoji", justify="center")
    table.add_column("Encoding Details", style="dim")

    for alias, emj, pts in rows[:limit]:
        table.add_row(alias, emj, pts)

    console.print(table)
    if len(rows) > limit:
        console.print(f"[yellow]... and {len(rows)-limit} more results (use --limit to show more)[/yellow]")

def main():
    parser = argparse.ArgumentParser(description="Emojipix CLI - The ultimate text to emoji tool")
    parser.add_argument('--text', type=str, help='Convert text alias/emoticon to emoji (e.g., ":)" or "smile")')
    parser.add_argument('--emoji', type=str, help='Decode an emoji to its encoding and text alias (e.g., "😄")')
    parser.add_argument('--search', type=str, help='Search for an emoji by keyword')
    parser.add_argument('--inject', type=str, help='Add a few relevant emojis to a message for pasting into AI chats')
    parser.add_argument('--strip', type=str, nargs='?', const='', help='Remove emojis from text. Reads stdin when no text is provided')
    parser.add_argument('--strip-file', type=str, help='Remove emojis from a UTF-8 text/code/HTML file')
    parser.add_argument('--output', type=str, help='Write --strip or --strip-file result to a file')
    parser.add_argument('--palette', type=str, help='Show a reusable emoji palette for a topic (e.g., ai, code, launch)')
    parser.add_argument('--prompt', action='store_true', help='Print an instruction snippet for asking an AI to use emojis well')
    parser.add_argument('--list', action='store_true', help='List common emojis')
    parser.add_argument('--mood', choices=sorted(CHAT_MOODS), default='friendly', help='Emoji style for --inject or --prompt')
    parser.add_argument('--density', choices=['low', 'balanced', 'high'], default='balanced', help='Emoji density for --prompt')
    parser.add_argument('--limit', type=int, default=25, help='Maximum rows for --search and --list')
    parser.add_argument('--category', type=str, help='Filter --list aliases by keyword')
    parser.add_argument('--include-variants', action='store_true', help='Include skin-tone and variation aliases in search output')
    parser.add_argument('--keep-spacing', action='store_true', help='For --strip, remove emojis without normalizing nearby spaces')
    parser.add_argument('--strip-aliases', action='store_true', help='For --strip, also remove text aliases such as :sparkles:')
    parser.add_argument('--plain', action='store_true', help='Print copy-friendly plain text instead of rich tables')
    parser.add_argument('--json', action='store_true', help='Print machine-readable JSON')
    
    args = parser.parse_args()
    
    if not any([args.text is not None, args.emoji is not None, args.search is not None, args.inject is not None, args.strip is not None, args.strip_file is not None, args.palette is not None, args.prompt, args.list]):
        parser.print_help()
        sys.exit(0)
        
    if args.text:
        result = text_to_emoji(args.text)
        if result:
            if args.json:
                output_json({"input": args.text, "emoji": result})
            elif args.plain:
                console.print(result)
            else:
                console.print(Panel(f"[bold green]{result}[/bold green]", title=f"Result for: {args.text}", expand=False))
        else:
            console.print(f"[bold red]No emoji found for text:[/bold red] {args.text}")
            suggestions = suggest_aliases(args.text)
            if suggestions:
                console.print("Did you mean one of these?")
                for alias, emj, _ in suggestions:
                    console.print(f"  {emj}  {alias}")
            else:
                console.print("Try using --search to find the correct alias.")
            
    if args.emoji:
        alias, points = emoji_to_info(args.emoji)
        if args.json:
            output_json({"emoji": args.emoji, "alias": alias if alias != args.emoji else None, "codepoints": points})
            return
        if args.plain:
            console.print(alias if alias != args.emoji else "None Mapping Found")
            for point in points:
                console.print(point)
            return
        
        table = Table(title=f"Emoji Decoder: {args.emoji}")
        table.add_column("Property", style="cyan", justify="right")
        table.add_column("Value", style="magenta")
        
        table.add_row("Raw Input", args.emoji)
        table.add_row("Text Alias", alias if alias != args.emoji else "None Mapping Found")
        
        for i, pt in enumerate(points):
            table.add_row(f"Unicode Char {i+1}", pt)
            
        console.print(table)
            
    if args.search:
        results = compact_results(do_search(args.search), include_variants=args.include_variants)
        if results:
            if args.json:
                output_json({"query": args.search, "results": [{"alias": a, "emoji": e, "codepoints": p} for a, e, p in results[:args.limit]]})
            elif args.plain:
                for alias, emj, _ in results[:args.limit]:
                    console.print(f"{emj}\t{alias}")
            else:
                print_rows(f"Search Results for '{args.search}'", results, args.limit)
        else:
            console.print(f"[bold red]No results found for:[/bold red] {args.search}")

    if args.inject:
        result = inject_emojis(args.inject, mood=args.mood, density={"low": 1, "balanced": 2, "high": 4}[args.density])
        if args.json:
            output_json({"input": args.inject, "mood": args.mood, "density": args.density, "output": result})
        else:
            console.print(result)

    if args.strip is not None or args.strip_file is not None:
        source = read_strip_source(args)
        if source is None:
            console.print("[bold red]No input provided for --strip.[/bold red]")
            console.print("Pass text after --strip, use --strip-file, or pipe content into emojipix --strip.")
            sys.exit(2)
        result = strip_emojis(source, preserve_spacing=not args.keep_spacing, strip_aliases=args.strip_aliases)
        if args.json:
            output_json({"input": source, "output": result, "removed": source != result})
        else:
            write_or_print_strip_result(args, result)

    if args.palette:
        palette = palette_for(args.palette)
        if args.json:
            output_json({"topic": args.palette, "palette": palette})
        elif args.plain:
            console.print(" ".join(palette))
        else:
            console.print(Panel(" ".join(palette) if palette else "No palette found", title=f"Palette: {args.palette}", expand=False))

    if args.prompt:
        prompt = make_prompt(args.mood, args.density)
        if args.json:
            output_json({"mood": args.mood, "density": args.density, "prompt": prompt})
        else:
            console.print(prompt)
            
    if args.list:
        results = do_list(limit=args.limit, category=args.category)
        if args.json:
            output_json({"results": [{"alias": a, "emoji": e, "codepoints": p} for a, e, p in results]})
        elif args.plain:
            for alias, emj, _ in results:
                console.print(f"{emj}\t{alias}")
        else:
            print_rows(f"Emoji List (Top {args.limit})", results, args.limit)
            console.print("[dim]Use --search to find specific emojis![/dim]")

if __name__ == "__main__":
    main()

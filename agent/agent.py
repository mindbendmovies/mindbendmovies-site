#!/usr/bin/env python3
"""
My Agent - PC half, v8.1 - Muse-style: persistent memory (MEMORY.md),
2-model ladder (jo model jawab de, usi se kaam), verify-before-done
workflow rules, busy-server (503/429) retries with honest per-error
messages, aur SELF-UPDATE: 'update' likhne par naya version khud
download karke lag jata hai - file haath se badalna khatm.
v8.1 fixes (user ke asal PC test se): fail-fast Gemini (40s timeout,
class-wise retry), sakht WORKER rule + tool discipline re-ask (sirf
salah dene par model ko ek baar tool chalane par majboor karna),
tolerant action parsing (prose me chipka ya double-encoded JSON bhi
tool call bankar chalta hai), aur 'facebook kholo' jaisi site commands
jo bina Gemini ke turant browser kholti hain.

A personal agent that runs on Ankit's OWN computer.
- All files and logs stay on this machine.
- Brain = Google Gemini free API (key from a local config file, never in code).
- Without a key it runs in demo/offline mode: direct tool commands still work.
- Tools are confined to the work/ folder. Nothing outside it can be touched.
- A tiny HTTP hook on 127.0.0.1 (localhost ONLY) lets the phone app talk to
  it later. Every request must carry the shared PIN from the config.

Stdlib only. No pip installs needed. Python 3.9+.
"""

import argparse
import hmac
import html
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# --------------------------------------------------------------------------
# Paths and config
# --------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_WORK_DIR = BASE_DIR / "work"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "agent.log"
SKILLS_DIR = BASE_DIR / "skills"
SKILLS_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_FILE = BASE_DIR / "MEMORY.md"

# --------------------------------------------------------------------------
# Version + self-update (v8)
# AGENT_VERSION har release me badhta hai. Update ka source Ankit ki apni
# GitHub Pages site hai - is file me koi secret nahi hota (key config.env
# me rehti hai), isliye ise khule aam host karna surakshit hai.
# --------------------------------------------------------------------------

AGENT_VERSION = "8.1"
UPDATE_URL = "https://mindbendmovies.github.io/mindbendmovies-site/agent/agent.py"
SELF_FILE = Path(__file__).resolve()
BACKUP_FILE = BASE_DIR / "agent_backup.py"

_log_lock = threading.Lock()


def log(action: str) -> None:
    """Append one line to the local action log. Data never leaves this PC."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = f"{datetime.now().isoformat(timespec='seconds')}  {action}\n"
    with _log_lock:
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(line)


def load_config() -> dict:
    """
    Config priority: real environment variables first, then a local
    .env-style file (config.env or .env) sitting next to this script.

    Expected keys (all optional except the PIN if the HTTP hook is used):
      GEMINI_API_KEY   - his free Google AI Studio key (stored ONLY here)
      GEMINI_MODEL     - default: gemini-3.5-flash-lite (sabse tez/halka)
      AGENT_PIN        - shared PIN checked on every HTTP /ask request
      AGENT_PORT       - default: 8765
      AGENT_WORK_DIR   - default: the work/ folder next to this script
    """
    cfg = {}
    for name in ("config.env", ".env"):
        path = BASE_DIR / name
        if path.is_file():
            for raw in path.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                cfg[key.strip()] = value.strip().strip('"').strip("'")
            break
    # Real environment variables win over the file.
    for key in ("GEMINI_API_KEY", "GEMINI_MODEL", "AGENT_PIN",
                "AGENT_PORT", "AGENT_WORK_DIR"):
        if os.environ.get(key):
            cfg[key] = os.environ[key]
    return cfg


CONFIG = load_config()
GEMINI_API_KEY = CONFIG.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = CONFIG.get("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
AGENT_PIN = CONFIG.get("AGENT_PIN", "").strip()
try:
    AGENT_PORT = int(CONFIG.get("AGENT_PORT", "8765"))
except ValueError:
    AGENT_PORT = 8765

WORK_DIR = Path(CONFIG.get("AGENT_WORK_DIR", "") or DEFAULT_WORK_DIR).expanduser()
if not WORK_DIR.is_absolute():
    WORK_DIR = (BASE_DIR / WORK_DIR)
WORK_DIR = WORK_DIR.resolve()
WORK_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """You are "My Agent", the personal AI agent of Ankit Kumar.
You speak in Hinglish (Roman Hindi mixed with English), short and direct,
like a close helpful friend, unless detail is asked for.
Ankit runs MindBendMovies - a movie website and Android app for a USA
audience (disturbing movies, twisted thrillers, hidden gems) - and makes
movie videos for a Facebook Page. Help him with plans, ideas, writing,
files and daily work on HIS OWN computer.
All data stays on his computer. You may use the available tools, which are
confined to his work folder. Never ask for or reveal any API key or PIN.

PERMISSION RULES (Ankit ne khud diye hain, 2026-11-20):
- Ankit ne apne computer ko apne kaam ke liye khule taur par use karne ki
  permission di hai. Uske kaam ke liye PC aur tools ko bina baar-baar
  puche aaram se use karo.
- Login wale kaam (YouTube, Facebook, TikTok, Google adi): login ANKIT
  KHUD apne browser me karega. Tum usse password KABHI nahi mangoge aur
  koi password kabhi store nahi karoge. Kaam hamesha pehle se logged-in
  browser/session ke through hoga - login na ho to use khud login karne
  ko bolo aur ruk jao.
- Paise kharch hone wale (kharid, paid plan, ad par paisa) ya koi cheez
  DELETE hone wale kaam se pehle Ankit se pehle puchna zaroori hai.
  Iske alawa baaki saare kaam bina puche seedha kar do.

SKILLS: A skills/ folder next to the program holds skill files - one
markdown file per learned kaam (jaise youtube-upload, video-editing).
Koi task kisi skill se match kare to pehle list_skills / read_skill se
wo skill padho, phir usi ke steps follow karo. Ankit naya kaam sikhaye
to create_skill se uski skill bana do taaki agli baar yaad rahe. Skill
files me kabhi koi password, API key ya PIN mat likho.

MEMORY: Tumhari ek long-term memory file hai - MEMORY.md, program ke
bilkul paas wali. Uski baatein har session me neeche "AGENT KI
YAADEIN" section me tumhe di jati hain - unhe har jawab me dhyaan me
rakho. Jab Ankit koi zaroori baat bataye - uski pasand/naapasand, koi
faisla, chal raha kaam, koi naam ya date - to use yaad_likho tool se
save kar do, taaki agli baar bhi yaad rahe. Roz ki chhoti-moti
baatein save mat karo, aur memory me bhi kabhi password, API key ya
PIN mat likho.

KAAM KARNE KA TAREEKA (hamesha yahi follow karo):
1. Pehle hukum ko achhe se samjho. Kaam bada ho to mann me chhota sa
   plan banao, phir shuru karo.
2. Kaam asal me tools se karo - sirf baat karke mat chhodo. Jo bola,
   wo karke dikhao.
3. Kaam ke baad result khud verify karo: file likhi hai to read_file
   se padh kar check karo, folder banaya to list karke dekho. Verify
   kiye bina "ho gaya" mat bolo.
4. Error aaye to wahi ruk mat jao - kaaran samjho aur dusra tareeka
   try karo. Tab bhi na ho to saaf batao kya atka hai.
5. Jo baat aage bhi kaam aayegi (pasand, faisla, chal raha kaam) use
   yaad_likho se memory me save kar do.

WORKER RULE - SABSE SAKHT (ise kabhi mat todo):
- Tum ek WORKER ho, salah dene wale advisor NAHI. Hukum ka matlab hai
  kaam KARNA, sirf samjhana nahi.
- "khud kar lo", "aap ye steps follow karein", "aapko ye karna hoga",
  "main direct nahi kar sakta lekin..." jaisi baatein tab tak kehna
  SAKHT MANA hai, jab tak wo kaam kisi tool se ho sakta ho.
- Website kholni ho (Facebook, YouTube, koi bhi site) to open_url
  chalao. File banani ho to write_file chalao. Jo bhi hukum mile -
  pehle tool chalao, phir batao kya hua.
- Tool chalane ke baad hi apne jawab me result batao. Bina tool
  chalaye "kar dunga / ho jayega" wale waade bhi mat karo.

TOOL PROTOCOL: If you need a tool, reply with ONLY a JSON object like
{"tool": "list_files", "args": {"path": ""}} and nothing else.
FORMAT RULE (bahut zaroori): tool call wala jawab SIRF wahi ek JSON
object hoga - usse pehle ya baad me EK SHABD bhi nahi, koi prose,
koi "main kar deta hu" wali line nahi. "args" hamesha ek asli JSON
object hoga {"url": "..."} - kabhi bhi string ke andar band kiya
hua JSON nahi bhejoge.
Available tools:
- list_files(path)           list files/folders inside the work folder
- read_file(path)            read a text file inside the work folder
- write_file(path, content)  write a text file inside the work folder
- create_folder(path)        create a folder inside the work folder
- get_time()                 current date and time on this computer
- web_fetch(url)             fetch an http/https page and return its text
- list_skills()              list the learned skill files
- read_skill(name)           read one skill file, e.g. "youtube-upload"
- create_skill(name, content)  save a new skill (only inside skills/)
- yaad_likho(text)           save an important baat to long-term memory (MEMORY.md)
- open_url(url)              open a page in this PC's default browser
- video_info(path)           duration/size/resolution of a video in work/
- trim_video(input, start_sec, duration_sec, output)  cut a video (work/)
- join_videos(files, output) join videos in order (all inside work/)
- speak_to_file(text, filename)  make a voice audio file inside work/
- agent_update()             check for a newer version of myself and
                             install it (engine restart ke baad lagega)
If no tool is needed, reply in plain text only (no JSON)."""

# --------------------------------------------------------------------------
# Tools - every one is confined to WORK_DIR
# --------------------------------------------------------------------------


def _safe_path(user_path: str) -> Path:
    """Resolve a user-supplied path INSIDE the work folder, or raise."""
    user_path = (user_path or "").strip().strip('"').strip("'")
    candidate = (WORK_DIR / user_path).resolve()
    if candidate != WORK_DIR and WORK_DIR not in candidate.parents:
        raise ValueError("Path is outside the work folder - not allowed.")
    return candidate


def _rel(path: Path) -> str:
    return str(path.relative_to(WORK_DIR)) if path != WORK_DIR else "."


def tool_list_files(path: str = "") -> str:
    target = _safe_path(path)
    if not target.exists():
        return f"Folder not found: {_rel(target)}"
    if target.is_file():
        return f"{_rel(target)} ({target.stat().st_size} bytes)"
    entries = sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    if not entries:
        return f"{_rel(target)} is empty."
    lines = [f"Contents of {_rel(target)}:"]
    for e in entries:
        kind = "DIR " if e.is_dir() else "FILE"
        size = "" if e.is_dir() else f" ({e.stat().st_size} bytes)"
        lines.append(f"  {kind}  {e.name}{size}")
    return "\n".join(lines)


def tool_read_file(path: str) -> str:
    target = _safe_path(path)
    if not target.is_file():
        return f"File not found: {path}"
    text = target.read_text(encoding="utf-8", errors="replace")
    if len(text) > 20000:
        text = text[:20000] + "\n... [cut at 20000 characters]"
    return text


def tool_write_file(path: str, content: str) -> str:
    target = _safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Wrote {_rel(target)} ({len(content)} characters)."


def tool_create_folder(path: str) -> str:
    target = _safe_path(path)
    target.mkdir(parents=True, exist_ok=True)
    return f"Folder ready: {_rel(target)}"


def tool_get_time() -> str:
    now = datetime.now()
    return now.strftime("Today is %A, %d %B %Y. Time on this computer: %I:%M %p.")


def tool_web_fetch(url: str) -> str:
    url = (url or "").strip()
    if not re.match(r"^https?://", url):
        return "Only http/https URLs are allowed."
    req = urllib.request.Request(url, headers={"User-Agent": "MyAgent/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 (http/https checked above)
        raw = resp.read(500_000)
    text = raw.decode("utf-8", errors="replace")
    # Crude but dependency-free HTML -> text.
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:20000] if text else "(page had no readable text)"


# --------------------------------------------------------------------------
# Skills - the agent's learnable memory. One .md file per skill, ONLY
# inside the skills/ folder next to this script.
# --------------------------------------------------------------------------


def _safe_skill_path(name: str) -> Path:
    """Turn a skill name into a safe .md path inside SKILLS_DIR, or raise."""
    clean = (name or "").strip().lower()
    clean = re.sub(r"\.md$", "", clean)
    clean = re.sub(r"[^a-z0-9]+", "-", clean).strip("-")
    if not clean:
        raise ValueError("Skill ka naam khali hai - sahi naam do.")
    candidate = (SKILLS_DIR / f"{clean}.md").resolve()
    if candidate.parent != SKILLS_DIR.resolve():
        raise ValueError("Skill sirf skills/ folder ke andar hi ban sakti hai.")
    return candidate


def _skill_title(path: Path) -> str:
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip().startswith("#"):
                return line.strip().lstrip("#").strip()
    except Exception:
        pass
    return path.stem


def tool_list_skills() -> str:
    files = sorted(SKILLS_DIR.glob("*.md"))
    if not files:
        return ("Abhi koi skill nahi hai. Nayi skill sikhane ke liye likho: "
                "seekho <naam>: <steps>")
    lines = [f"Skills ({len(files)}):"]
    for f in files:
        lines.append(f"  - {f.stem} - {_skill_title(f)}")
    lines.append("'skill <naam>' likho to kisi skill ke steps dikha dunga.")
    return "\n".join(lines)


def tool_read_skill(name: str) -> str:
    target = _safe_skill_path(name)
    if not target.is_file():
        return (f"Skill nahi mili: {target.stem}. "
                "'skills' likho, saari skills dikha dunga.")
    text = target.read_text(encoding="utf-8", errors="replace")
    if len(text) > 20000:
        text = text[:20000] + "\n... [cut at 20000 characters]"
    return text


def tool_create_skill(name: str, content: str) -> str:
    target = _safe_skill_path(name)
    content = (content or "").strip()
    if not content:
        return "Skill ka matter khali hai - steps likh kar do."
    if not content.startswith("#"):
        content = f"# {target.stem}\n\n{content}"
    existed = target.is_file()
    target.write_text(content + "\n", encoding="utf-8")
    verb = "update ho gayi" if existed else "ban gayi"
    return (f"Skill '{target.stem}' {verb} aur skills/ folder me save hai. "
            "Agli baar ye kaam aaya to main yahi steps follow karunga.")


# --------------------------------------------------------------------------
# Memory - the agent's long-term yaadein. Ek hi file: MEMORY.md, program
# ke bilkul paas (agent folder me). Path FIXED hai - bahar se koi path
# nahi aata, isliye ye file work/ ke bahar hote hue bhi safe hai.
# --------------------------------------------------------------------------

MEMORY_MAX_CHARS = 6000
MEMORY_ENTRY_MAX = 300


def load_memory() -> str:
    """MEMORY.md se purani yaadein padho (zyada se zyada ~6000 chars).

    File badi ho jaye to sabse NAYI yaadein (aakhir wali) rakhi jati
    hain, kyunki nayi baatein append hoti hain. File na ho ya padh na
    paye to khali string - agent bina yaadon ke bhi chalta rahega.
    """
    try:
        if MEMORY_FILE.is_file():
            text = MEMORY_FILE.read_text(
                encoding="utf-8", errors="replace").strip()
            if len(text) > MEMORY_MAX_CHARS:
                text = text[-MEMORY_MAX_CHARS:]
            return text
    except Exception:
        pass
    return ""


def tool_save_memory(text: str = "") -> str:
    """Ek zaroori baat MEMORY.md me dated bullet ki tarah jodo."""
    clean = re.sub(r"\s+", " ", (text or "")).strip()
    if not clean:
        return "Yaad karne ke liye kuch likho to sahi - khali yaad save nahi hoti."
    clean = clean[:MEMORY_ENTRY_MAX]
    line = f"- {datetime.now().strftime('%Y-%m-%d')}: {clean}"
    try:
        if not MEMORY_FILE.is_file():
            MEMORY_FILE.write_text(
                "# My Agent - Yaadein\n"
                "Ankit ke baare me yaad rakhi hui zaroori baatein.\n\n",
                encoding="utf-8")
        with open(MEMORY_FILE, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception as exc:
        return f"Yaad save nahi ho payi: {exc}"
    return (f"Yaad save kar li: {clean} "
            "Ab ye baat mujhe agli baar bhi yaad rahegi.")


# --------------------------------------------------------------------------
# Browser tool - opens a page in THIS PC's default browser
# --------------------------------------------------------------------------


def tool_open_url(url: str) -> str:
    url = (url or "").strip()
    if not re.match(r"^https?://", url):
        return "Sirf http/https wala link khol sakta hu - sahi URL do."
    opened = False
    err = None
    try:
        opened = webbrowser.open(url, new=2)
    except Exception as exc:
        err = exc
    if not opened and platform.system() == "Windows" and hasattr(os, "startfile"):
        # webbrowser kabhi kabhi Windows par bina error ke False de deta
        # hai - tab OS ke apne tareeke (startfile) se ek koshish aur.
        try:
            os.startfile(url)  # noqa: S606 - user ka apna PC, usi ka hukum
            opened = True
        except Exception as exc:
            err = exc
    if opened:
        return f"Browser me khol diya: {url}"
    detail = f" ({err})" if err else ""
    return ("Browser kholne me dikkat aayi" + detail +
            f". Link haath se kholo: {url}")


# --------------------------------------------------------------------------
# Video tools (ffmpeg) - inputs and outputs ONLY inside work/
# --------------------------------------------------------------------------


def _ffmpeg_missing_msg() -> str:
    return ("Is PC par ffmpeg nahi mila. Video wale kaam ke liye pehle "
            "ffmpeg install karna hoga (ffmpeg.org se, ya Windows par "
            "'winget install ffmpeg'). Install ke baad phir try karo.")


def _run_quiet(cmd: list, timeout: int = 600):
    return subprocess.run(cmd, capture_output=True, text=True,
                          timeout=timeout)


def tool_video_info(path: str) -> str:
    if not shutil.which("ffmpeg"):
        return _ffmpeg_missing_msg()
    target = _safe_path(path)
    if not target.is_file():
        return f"File not found: {path}"
    size_mb = target.stat().st_size / (1024 * 1024)
    info = {"duration": None, "streams": []}
    if shutil.which("ffprobe"):
        try:
            proc = _run_quiet([
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-show_entries",
                "stream=codec_type,codec_name,width,height",
                "-of", "json", str(target)], timeout=60)
            data = json.loads(proc.stdout or "{}")
            dur = (data.get("format") or {}).get("duration")
            if dur:
                info["duration"] = float(dur)
            info["streams"] = data.get("streams") or []
        except Exception:
            info = {"duration": None, "streams": []}
    if info["duration"] is None:  # fall back to parsing `ffmpeg -i`
        try:
            proc = _run_quiet(["ffmpeg", "-i", str(target)], timeout=60)
            m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)",
                          proc.stderr or "")
            if m:
                info["duration"] = (int(m.group(1)) * 3600 +
                                    int(m.group(2)) * 60 +
                                    float(m.group(3)))
            for line in (proc.stderr or "").splitlines():
                if "Video:" in line:
                    res = re.search(r"(\d{2,5})x(\d{2,5})", line)
                    info["streams"].append({
                        "codec_type": "video",
                        "width": res.group(1) if res else "?",
                        "height": res.group(2) if res else "?"})
                elif "Audio:" in line:
                    info["streams"].append({"codec_type": "audio"})
        except Exception as exc:
            return f"Video ki jaankari nahi nikal payi: {exc}"
    lines = [f"Video: {_rel(target)} ({size_mb:.2f} MB)"]
    if info["duration"] is not None:
        d = info["duration"]
        lines.append(f"Duration: {d:.1f} seconds ({int(d // 60)}:{int(d % 60):02d})")
    else:
        lines.append("Duration: pata nahi chal payi")
    for s in info["streams"]:
        if s.get("codec_type") == "video":
            lines.append(f"Video stream: {s.get('codec_name', 'ffmpeg')} "
                         f"{s.get('width', '?')}x{s.get('height', '?')}")
        elif s.get("codec_type") == "audio":
            lines.append(f"Audio stream: {s.get('codec_name', 'hai')}")
    return "\n".join(lines)


def tool_trim_video(input: str, start_sec=0, duration_sec=10,
                    output: str = "") -> str:
    if not shutil.which("ffmpeg"):
        return _ffmpeg_missing_msg()
    src = _safe_path(input)
    if not src.is_file():
        return f"File not found: {input}"
    try:
        start = float(start_sec)
        dur = float(duration_sec)
    except (TypeError, ValueError):
        return "Start aur duration second me number do, jaise 0 aur 10."
    if not output:
        output = f"{src.stem}_trim{src.suffix or '.mp4'}"
    dst = _safe_path(output)
    dst.parent.mkdir(parents=True, exist_ok=True)
    proc = _run_quiet([
        "ffmpeg", "-y", "-ss", str(start), "-i", str(src),
        "-t", str(dur), "-c:v", "libx264", "-c:a", "aac",
        "-movflags", "+faststart", str(dst)])
    if proc.returncode != 0 or not dst.is_file():
        tail = (proc.stderr or "")[-400:]
        return f"Trim nahi ho paya. ffmpeg ne kaha: {tail}"
    return (f"Trim ho gaya: {_rel(dst)} "
            f"({dst.stat().st_size} bytes) - {input} ke {start:.0f}s se "
            f"{dur:.0f}s tak ka hissa.")


def tool_join_videos(files, output: str = "joined.mp4") -> str:
    if not shutil.which("ffmpeg"):
        return _ffmpeg_missing_msg()
    if isinstance(files, str):
        file_list = [f.strip() for f in re.split(r"[,\n]", files) if f.strip()]
    else:
        file_list = [str(f) for f in (files or [])]
    if len(file_list) < 2:
        return "Join ke liye kam se kam 2 video files do."
    paths = []
    for f in file_list:
        p = _safe_path(f)
        if not p.is_file():
            return f"File not found: {f}"
        paths.append(p)
    dst = _safe_path(output or "joined.mp4")
    dst.parent.mkdir(parents=True, exist_ok=True)
    list_file = WORK_DIR / "_join_list.txt"
    with open(list_file, "w", encoding="utf-8") as fh:
        for p in paths:
            fh.write(f"file '{str(p).replace(chr(39), chr(39) + chr(92) + chr(39) + chr(39))}'\n")
    try:
        proc = _run_quiet([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_file), "-c", "copy", str(dst)])
    finally:
        list_file.unlink(missing_ok=True)
    if proc.returncode != 0 or not dst.is_file():
        tail = (proc.stderr or "")[-400:]
        return (f"Join nahi ho paya (files ka codec/format ek jaisa hona "
                f"chahiye). ffmpeg ne kaha: {tail}")
    return (f"Join ho gaya: {_rel(dst)} ({dst.stat().st_size} bytes) - "
            f"{len(paths)} videos ek saath jud gayin.")


# --------------------------------------------------------------------------
# Voice tool - text ko awaaz ki file me badalna (PC ka apna TTS engine)
# --------------------------------------------------------------------------


def tool_speak_to_file(text: str, filename: str = "") -> str:
    text = (text or "").strip()
    if not text:
        return "Awaaz banane ke liye pehle text do."
    system = platform.system()
    if not filename:
        filename = "voice.wav" if system in ("Windows", "Linux") else "voice.aiff"
    dst = _safe_path(filename)
    dst.parent.mkdir(parents=True, exist_ok=True)

    if system == "Windows":
        # PowerShell + System.Speech - file me WAV likhta hai.
        safe_text = text.replace("'", "''")
        safe_path = str(dst).replace("'", "''")
        ps = ("Add-Type -AssemblyName System.Speech; "
              "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
              f"$s.SetOutputToWaveFile('{safe_path}'); "
              f"$s.Speak('{safe_text}'); $s.Dispose()")
        try:
            proc = _run_quiet(["powershell", "-NoProfile", "-Command", ps],
                              timeout=120)
        except FileNotFoundError:
            return "PowerShell nahi mila - is Windows par voice file nahi ban payi."
        if proc.returncode == 0 and dst.is_file():
            return f"Voice file ban gayi: {_rel(dst)} ({dst.stat().st_size} bytes)."
        return f"Voice file nahi bani. PowerShell ne kaha: {(proc.stderr or '')[-300:]}"

    if system == "Darwin":
        say = shutil.which("say")
        if not say:
            return "Is Mac par 'say' command nahi mila - voice file nahi ban payi."
        proc = _run_quiet([say, "-o", str(dst), text], timeout=120)
        if proc.returncode == 0 and dst.is_file():
            return f"Voice file ban gayi: {_rel(dst)} ({dst.stat().st_size} bytes)."
        return f"Voice file nahi bani. say ne kaha: {(proc.stderr or '')[-300:]}"

    # Linux
    engine = shutil.which("espeak-ng") or shutil.which("espeak")
    if engine:
        proc = _run_quiet([engine, "-w", str(dst), text], timeout=120)
        if proc.returncode == 0 and dst.is_file():
            return f"Voice file ban gayi: {_rel(dst)} ({dst.stat().st_size} bytes)."
        return f"Voice file nahi bani. TTS engine ne kaha: {(proc.stderr or '')[-300:]}"
    return ("Is computer par koi awaaz banane wala engine (TTS) nahi mila, "
            "isliye voice file nahi ban payi. Fikar mat karo - asli "
            "movie-video voiceover ke liye 'voiceover' skill wala rasta "
            "hai: Google AI Studio ki Aoede voice, jisme login Ankit khud "
            "karta hai aur main script taiyaar karke deta hu.")


# --------------------------------------------------------------------------
# Self-update tool (v8) - 'update' bolte hi naya version khud lag jata hai
# --------------------------------------------------------------------------

_VERSION_RE = re.compile(r'AGENT_VERSION\s*=\s*"([0-9]+(?:\.[0-9]+)*)"')


def _parse_version(text: str):
    """Diye hue source text me se AGENT_VERSION nikalo, na mile to None."""
    m = _VERSION_RE.search(text or "")
    return m.group(1) if m else None


def _version_tuple(version) -> tuple:
    """ "8.10" ko (8, 10) banao taaki version ki sahi tulna ho sake."""
    try:
        return tuple(int(p) for p in str(version).split("."))
    except ValueError:
        return ()


def tool_agent_update() -> str:
    """UPDATE_URL se nayi agent.py lao, jaancho, phir khud ko update karo.

    Suraksha: pehle version ki tulna, phir nayi file ko memory me compile
    karke jaanch - kuch bhi gadbad ho to purani file ko haath nahi lagta.
    Safal update par purani file agent_backup.py me reh jati hai.
    """
    try:
        req = urllib.request.Request(
            UPDATE_URL, headers={"User-Agent": "MyAgent-Updater"})
        with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310
            source = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        log(f"UPDATE fetch fail: {exc}")
        return ("Update check nahi ho paya - internet ya server ki "
                f"dikkat lagti hai ({exc}). Purani file bilkul "
                "surakshit hai, kuch nahi badla. Thodi der baad phir "
                "'update' likh kar try karna.")
    remote_version = _parse_version(source)
    if remote_version is None:
        log("UPDATE rok diya: remote file me AGENT_VERSION nahi mila")
        return ("Update wali file me version nahi mila, isliye kuch "
                "nahi badla. Purana agent bilkul surakshit chal raha hai.")
    if _version_tuple(remote_version) <= _version_tuple(AGENT_VERSION):
        return (f"Tum pehle se latest version (v{AGENT_VERSION}) par "
                "ho - koi naya update nahi hai.")
    try:
        compile(source, "agent.py", "exec")
    except SyntaxError as exc:
        log(f"UPDATE rok diya: nayi file compile fail: {exc}")
        return ("Nayi file me kuch gadbad lagi (wo sahi se compile "
                "nahi hui), isliye update rok diya. Purana agent "
                "bilkul surakshit hai, kuch nahi badla.")
    try:
        shutil.copyfile(SELF_FILE, BACKUP_FILE)
        SELF_FILE.write_text(source, encoding="utf-8")
    except Exception as exc:
        log(f"UPDATE write fail: {exc}")
        return (f"Update likhne me dikkat aayi ({exc}). Agar kuch "
                "gadbad lage to purani file agent_backup.py me "
                "surakshit hai.")
    log(f"UPDATE ho gaya: v{AGENT_VERSION} -> v{remote_version} "
        "(purani file: agent_backup.py)")
    return (f"Update ho gaya: v{AGENT_VERSION} -> v{remote_version}! "
            "Ab engine ko ek baar band karke 'start' se dobara chalao, "
            "tab naya version lagega. Purani file agent_backup.py ke "
            "naam se surakshit rakhi hai.")


_UPDATE_TRIGGERS = ("update", "update karo", "agent update", "update agent")


def _is_update_command(low: str) -> bool:
    """User ke 'update' wale hukum ko pehchano (dono modes ke liye)."""
    low = (low or "").strip().lower()
    return low in _UPDATE_TRIGGERS or low.startswith("update ")


# --------------------------------------------------------------------------
# Instant site commands (v8.1) - 'facebook kholo' type ke hukum bina
# Gemini ke, turant isi PC ke browser me khulte hain. Update command ki
# tarah ye bhi demo/Gemini dispatch se pehle pakde jate hain, isliye
# inmein na intezaar hai na model ki galti ki gunjaish.
# --------------------------------------------------------------------------

_SITE_MAP = {
    "facebook": ("Facebook", "https://www.facebook.com"),
    "youtube": ("YouTube", "https://www.youtube.com"),
    "instagram": ("Instagram", "https://www.instagram.com"),
    "tiktok": ("TikTok", "https://www.tiktok.com"),
    "whatsapp": ("WhatsApp", "https://web.whatsapp.com"),
    "google": ("Google", "https://www.google.com"),
    "gmail": ("Gmail", "https://mail.google.com"),
    "x": ("X", "https://x.com"),
    "twitter": ("X (Twitter)", "https://x.com"),
    "mindbendmovies": ("MindBendMovies",
                       "https://mindbendmovies.github.io/mindbendmovies-site/"),
}

_OPEN_WORDS = {"kholo", "khol", "kholna", "open", "chalao", "chala",
               "launch"}


def _site_open_command(message: str):
    """'facebook kholo' / 'open youtube' jaisa hukum ho to site ka
    (label, url) return karo, warna None.

    Pehchan shabdon (tokens) par hoti hai: ek kholne wala shabd
    (kholo/khol/open/chalao...) AUR ek site ka naam - dono hon tabhi.
    Sirf site ka naam (jaise 'facebook par post karo') ismein nahi
    fasna chahiye, wo Gemini ke paas jayega.
    """
    words = re.findall(r"[a-z0-9]+", (message or "").lower())
    if not any(w in _OPEN_WORDS for w in words):
        return None
    for w in words:
        if w in _SITE_MAP:
            return _SITE_MAP[w]
    return None


def _site_open_reply(message: str):
    """Site hukum chala kar Hinglish jawab do; hukum na ho to None."""
    found = _site_open_command(message)
    if found is None:
        return None
    label, url = found
    result = run_tool("open_url", {"url": url})
    if result.startswith("Browser me khol diya"):
        return f"{label} khol diya hai - browser me naya tab khul gaya hoga."
    return result


TOOLS = {
    "list_files": tool_list_files,
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "create_folder": tool_create_folder,
    "get_time": tool_get_time,
    "web_fetch": tool_web_fetch,
    "list_skills": tool_list_skills,
    "read_skill": tool_read_skill,
    "create_skill": tool_create_skill,
    "yaad_likho": tool_save_memory,
    "open_url": tool_open_url,
    "video_info": tool_video_info,
    "trim_video": tool_trim_video,
    "join_videos": tool_join_videos,
    "speak_to_file": tool_speak_to_file,
    "agent_update": tool_agent_update,
}


def run_tool(name: str, args: dict) -> str:
    """Run one tool, log it, and always return text (never crash the agent)."""
    if name not in TOOLS:
        return f"Unknown tool: {name}"
    try:
        result = TOOLS[name](**{k: v for k, v in (args or {}).items()
                                if k in TOOLS[name].__code__.co_varnames})
    except TypeError as exc:
        result = f"Tool argument error: {exc}"
    except Exception as exc:  # tools must never kill the loop
        result = f"Tool error: {exc}"
    log(f"TOOL {name} args={json.dumps(args or {}, ensure_ascii=False)[:300]} -> {str(result)[:120]}")
    return str(result)

# --------------------------------------------------------------------------
# Demo / offline mode - simple direct commands, no key needed
# --------------------------------------------------------------------------

HELP_TEXT = """Demo mode commands (type them as-is):
  list files                  - show the work folder
  list files in notes         - show a sub-folder
  read file test.txt          - read a file
  write file test.txt hello   - write a file (text after the name)
  create folder notes         - make a folder
  time                        - current date and time
  fetch https://example.com   - read a web page
  open https://example.com    - open a page in this PC's browser
  skills                      - list the learned skills
  skill youtube-upload        - show one skill's steps
  seekho <name>: <steps>      - teach me a new skill (it gets saved)
  yaad <baat>                 - save an important baat to my long-term
                                memory (MEMORY.md) - pasand, faisla,
                                chal raha kaam jaisi baatein
  yaadein                     - show my saved memories
  video info video.mp4        - a video's duration / size / resolution
  trim video.mp4 0 10         - cut 10s from a video, from second 0
  join a.mp4 b.mp4            - join videos into joined.mp4
  voice Namaste Ankit         - make a voice file of the text (if the
                                PC has a TTS engine; else I'll explain)
  update                      - check for a newer agent version and
                                update myself (engine restart ke baad
                                naya version lagega)
  facebook kholo              - mashhoor site seedha browser me khol
                                do (youtube, instagram, tiktok,
                                whatsapp, google, gmail bhi chalega)
  help                        - this list
  quit                        - stop
For free chatting like Muse, add your free Gemini key in config.env."""


def demo_ask(message: str):
    """Return a reply string, or None if the message is not a demo command."""
    text = message.strip()
    low = text.lower()

    if low in ("help", "madad", "?"):
        return HELP_TEXT
    if low in ("time", "what time is it", "samay", "time batao", "date",
               "what is the time"):
        return run_tool("get_time", {})

    m = re.match(r"list(?:\s+files)?(?:\s+in\s+(.+))?$", low)
    if m:
        folder = (text[m.start(1):] if m.group(1) else "")
        return run_tool("list_files", {"path": folder.strip()})

    m = re.match(r"read(?:\s+file)?\s+(.+)$", text, re.IGNORECASE)
    if m:
        return run_tool("read_file", {"path": m.group(1).strip()})

    m = re.match(r"write(?:\s+file)?\s+(\S+)\s+(.+)$", text,
                 re.IGNORECASE | re.DOTALL)
    if m:
        return run_tool("write_file",
                        {"path": m.group(1), "content": m.group(2)})

    m = re.match(r"create\s+folder\s+(.+)$", text, re.IGNORECASE)
    if m:
        return run_tool("create_folder", {"path": m.group(1).strip()})

    if low in ("skills", "skill", "skills dikhao", "list skills"):
        return run_tool("list_skills", {})

    if low in ("yaadein", "yaadein dikhao", "memories", "memory",
               "meri yaadein"):
        memory = load_memory()
        if not memory:
            return ("Abhi meri koi yaad save nahi hai. Kuch yaad karwana "
                    "ho to likho: yaad <baat> - jaise 'yaad Ankit ko "
                    "horror movies sabse zyada pasand hain'.")
        return "Meri yaadein (MEMORY.md):\n" + memory

    m = re.match(r"yaad\s+(.+)$", text, re.IGNORECASE | re.DOTALL)
    if m:
        return run_tool("yaad_likho", {"text": m.group(1).strip()})

    m = re.match(r"skill\s+(\S+)\s*$", text, re.IGNORECASE)
    if m:
        return run_tool("read_skill", {"name": m.group(1)})

    m = re.match(r"seekho\s+([^:]+):\s*(.+)$", text,
                 re.IGNORECASE | re.DOTALL)
    if m:
        name = m.group(1).strip()
        steps = m.group(2).strip()
        content = (f"# {name}\n\n## Kab use karein\nAnkit ne sikhaya hua kaam.\n\n"
                   f"## Steps\n{steps}\n")
        return run_tool("create_skill", {"name": name, "content": content})

    m = re.match(r"open\s+(https?://\S+)\s*$", text, re.IGNORECASE)
    if m:
        return run_tool("open_url", {"url": m.group(1)})

    m = re.match(r"video\s+info\s+(.+)$", text, re.IGNORECASE)
    if m:
        return run_tool("video_info", {"path": m.group(1).strip()})

    m = re.match(r"trim\s+(\S+)\s+([\d.]+)\s+([\d.]+)\s*$", text,
                 re.IGNORECASE)
    if m:
        return run_tool("trim_video", {"input": m.group(1),
                                       "start_sec": float(m.group(2)),
                                       "duration_sec": float(m.group(3))})

    m = re.match(r"join\s+(.+)$", text, re.IGNORECASE)
    if m:
        names = [p for p in re.split(r"[\s,]+", m.group(1).strip()) if p]
        return run_tool("join_videos", {"files": names})

    m = re.match(r"voice\s+(.+)$", text, re.IGNORECASE | re.DOTALL)
    if m:
        return run_tool("speak_to_file", {"text": m.group(1).strip()})

    m = re.search(r"(?:fetch|get)\s+(https?://\S+)", text, re.IGNORECASE)
    if m:
        return run_tool("web_fetch", {"url": m.group(1)})

    return None

# --------------------------------------------------------------------------
# Gemini mode - simple JSON-action protocol (see DESIGN.md section 5)
# --------------------------------------------------------------------------


def _system_prompt() -> str:
    """Asli system prompt = SYSTEM_PROMPT + MEMORY.md ki yaadein.

    Yaadein har call par taza padhi jati hain, taaki session ke beech
    me save hui nayi yaad bhi bina restart ke agle jawab me aa jaye.
    """
    prompt = SYSTEM_PROMPT
    memory = load_memory()
    if memory:
        prompt += ("\n\nAGENT KI YAADEIN (MEMORY.md se - Ankit ke baare "
                   "me purani yaad rakhi hui baatein; inhe har jawab me "
                   "dhyaan me rakho):\n" + memory)
    return prompt


class _GeminiSlowError(Exception):
    """Saari koshishon ke baad bhi Gemini ka jawab time par nahi aaya."""


class _GeminiBusyError(_GeminiSlowError):
    """503/429: Google ka server busy hai ya rate limit lagi hai.

    _GeminiSlowError ki aulaad hai, taaki model ladder is par bhi
    dusra model try kare - bas dono fail hon to aakhri user-message
    'server busy' wala banta hai, key wala nahi.
    """


# HTTP codes jo kuch der ki baat hain: server busy / rate limit.
_BUSY_CODES = (503, 429)
# Fail-fast neeti (v8.1): har call ka timeout 40s (pehle 120s tha - user
# ko bahut slow lagta tha). Retry class ke hisaab se:
# - timeout / network gadbad: kul 2 koshish, beech me 2s ki rukawat.
# - busy (503/429): kul 3 koshish, beech me 2s phir 5s ki rukawat.
# Isse ek model zyada se zyada ~2 minute me haar man leta hai aur
# ladder dusre model ko mauka deti hai - jawab jaldi ya to aata hai
# ya saaf wajah ke saath rukta hai.
_GEMINI_TIMEOUT = 40
_TIMEOUT_DELAYS = (2,)
_BUSY_DELAYS = (2, 5)


def _gemini_call(contents: list, model: str = None) -> str:
    model = model or GEMINI_MODEL
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={GEMINI_API_KEY}")
    body = {
        "system_instruction": {"parts": [{"text": _system_prompt()}]},
        "contents": contents,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    # Fail-fast (v8.1): har koshish me 40s tak wait. Timeout/network
    # par kul 2 koshish (2s ki rukawat), busy server (503/429) par kul
    # 3 koshish (2s, phir 5s ki rukawat). Baaki HTTP errors (404/400
    # jaisi) par retry NAHI - wo turant upar jati hain aur pehle ki
    # tarah report hoti hain.
    last_exc = None
    last_kind = None  # "timeout" | "busy" | "other"
    attempt = 0
    while True:
        try:
            with urllib.request.urlopen(req, timeout=_GEMINI_TIMEOUT) as resp:  # noqa: S310
                data = json.loads(resp.read().decode("utf-8"))
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts).strip()
        except urllib.error.HTTPError as exc:
            if exc.code not in _BUSY_CODES:
                raise
            last_exc = exc
            last_kind = "busy"
            max_attempts = 3
            log(f"GEMINI[{model}] attempt {attempt + 1}/{max_attempts} "
                f"fail: HTTP {exc.code} (server busy / rate limit, retry)")
            delays = _BUSY_DELAYS
        except (urllib.error.URLError, socket.timeout, TimeoutError,
                ConnectionError) as exc:
            last_exc = exc
            is_timeout = isinstance(
                exc, (socket.timeout, TimeoutError)) or (
                isinstance(exc, urllib.error.URLError)
                and isinstance(exc.reason, (socket.timeout, TimeoutError)))
            last_kind = "timeout" if is_timeout else "other"
            max_attempts = 2
            log(f"GEMINI[{model}] attempt {attempt + 1}/{max_attempts} "
                f"fail: {exc}")
            delays = _TIMEOUT_DELAYS
        if attempt + 1 >= max_attempts:
            break
        time.sleep(delays[min(attempt, len(delays) - 1)])
        attempt += 1
    if last_kind == "busy":
        raise _GeminiBusyError(f"HTTP {last_exc.code}")
    if last_kind == "timeout":
        raise _GeminiSlowError(str(last_exc))
    raise last_exc


# One shared short history per running process (phone chat stays continuous).
_history: list = []
_history_lock = threading.Lock()


def _balanced_blocks(text: str):
    """Text ke saare balanced {...} blocks ek-ek karke do.

    String ke andar ke braces ginne me nahi aate (escape ka bhi
    dhyaan rakha gaya hai), taaki prose ke beech chipka JSON aur
    string ke andar band JSON dono sahi pakde jayein.
    """
    blocks = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] != "{":
            i += 1
            continue
        depth = 0
        in_str = False
        esc = False
        end = None
        for j in range(i, n):
            ch = text[j]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            elif ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = j + 1
                    break
        if end is None:
            break
        blocks.append(text[i:end])
        i = end
    return blocks


def _extract_tool_call(reply: str):
    """Model ke jawab me se tool-call JSON nikalo - tolerant parsing.

    Asal PC par dekha gaya (v8.1 ki wajah): model kabhi kabhi jawab
    me prose ke saath JSON chipka deta hai, ya "args" ko object ki
    jagah double-encoded STRING bana deta hai - purana parser use
    plain text samajh kar dikha deta tha aur tool chalta hi nahi tha.
    Ab: code fence hatao, pehle pura jawab, phir har balanced {...}
    block try karo; jis me "tool" key parse ho jaye wahi action hai.
    "args" string aaye to use bhi json.loads karke object banao.
    Kuch salvage na ho to None (jawab plain text mana jayega).
    """
    if not reply:
        return None
    text = re.sub(r"```(?:json)?", "", reply).strip()
    candidates = []
    if text.startswith("{"):
        candidates.append(text)
    candidates.extend(_balanced_blocks(text))
    for cand in candidates:
        try:
            parsed = json.loads(cand)
        except (json.JSONDecodeError, ValueError):
            continue
        if not (isinstance(parsed, dict) and "tool" in parsed):
            continue
        args = parsed.get("args") or {}
        if isinstance(args, str):
            try:
                decoded = json.loads(args)
                if isinstance(decoded, dict):
                    args = decoded
            except (json.JSONDecodeError, ValueError):
                pass
        if not isinstance(args, dict):
            args = {}
        return {"tool": parsed["tool"], "args": args}
    return None


def _gemini_converse(contents: list, model: str):
    """Ek diye hue model ke saath pura tool-loop chalao.

    (jawab, tool_chala_kya) return hota hai; Gemini wali errors
    (slow / HTTP / baaki) caller ko dikhti hain taaki wo fallback
    try kar sake. tool_chala_kya isliye chahiye taaki discipline
    re-ask (sirf salah wale jawab par) sahi faisla le sake.
    """
    contents = list(contents)
    used_tool = False
    for _ in range(5):  # max 5 tool steps per message
        reply = _gemini_call(contents, model)
        tool_call = _extract_tool_call(reply)
        if tool_call is None:
            with _history_lock:
                _history.append({"role": "model",
                                 "parts": [{"text": reply}]})
            return reply, used_tool
        used_tool = True
        result = run_tool(tool_call["tool"], tool_call.get("args") or {})
        contents.append({"role": "model", "parts": [{"text": reply}]})
        contents.append({"role": "user",
                         "parts": [{"text": f"Tool result: {result}"}]})
    return ("Tool steps zyada ho gaye, main ruk gaya. Thoda simple "
            "karke phir pucho."), used_tool


_SLOW_MESSAGE = ("Gemini se baat nahi ho payi: internet ya model slow tha, "
                 "jawab time par nahi aaya. Wahi sawal ek baar phir bhej do.")

_BUSY_MESSAGE = ("Gemini se baat nahi ho payi: Google ka server abhi busy "
                 "hai, jawab nahi de paya. Maine khud dobara koshish "
                 "karke dekh liya hai - thodi der ruk kar wahi sawal "
                 "phir bhej do.")


# Model ladder (v8): pehle primary model, fail ho to dusra - kul 2
# model, isse aage kabhi nahi. Lite sabse tez aur sabse kam busy rehta
# hai, isliye wahi default hai; bada model uska saathi hai.
_MODEL_LITE = "gemini-3.5-flash-lite"
_MODEL_BIG = "gemini-3.8-flash"
# Key-type errors: in par ladder NAHI chalti, agent turant rukta hai.
_KEY_ERROR_CODES = (400, 401, 403)


def _ladder_models() -> list:
    """[primary, dusra] - primary = config wala model ya default lite."""
    primary = GEMINI_MODEL or _MODEL_LITE
    other = _MODEL_BIG if primary == _MODEL_LITE else _MODEL_LITE
    return [primary, other]


def _final_error_message(exc) -> str:
    """Dono models fail hon to AAKHRI error ki class ke hisaab se jawab."""
    if isinstance(exc, _GeminiBusyError):
        return _BUSY_MESSAGE
    if isinstance(exc, _GeminiSlowError):
        return _SLOW_MESSAGE
    if isinstance(exc, urllib.error.HTTPError):
        return _gemini_http_message(exc)
    log(f"GEMINI ladder aakhri error: {exc}")
    return f"Gemini se baat nahi ho payi: {exc}"


def _gemini_http_message(exc) -> str:
    detail = exc.read().decode("utf-8", errors="replace")[:300]
    log(f"GEMINI HTTP {exc.code}: {detail}")
    if exc.code in _BUSY_CODES:
        # Yahan aam taur par aana hi nahi chahiye (503/429 _gemini_call me
        # retry hokar busy-error bante hain) - phir bhi suraksha ke liye
        # wahi busy wala message, key wala kabhi nahi.
        return _BUSY_MESSAGE
    if exc.code in (400, 401, 403):
        # Sirf key-type galti par hi key check karne ko bolo.
        return (f"Gemini se baat nahi ho payi (HTTP {exc.code}). "
                "Key sahi hai ya nahi, Settings me check karo.")
    return f"Gemini se baat nahi ho payi (HTTP {exc.code})."


# --------------------------------------------------------------------------
# Tool discipline (v8.1) - 'khud kar lo' wali shikayat ka code ilaaj.
# Hukum me action wala shabd ho (kholo, banao, likho...) aur model ne
# BINA koi tool chalaye sirf text jawab de diya ho, to ek baar sakht
# instruction ke saath dobara pucha jata hai. Kul EK re-ask per
# message - loop kabhi nahi banta.
# --------------------------------------------------------------------------

_ACTION_WORDS = ("kholo", "khol", "open", "banao", "bana", "create",
                 "download", "likho", "save", "delete", "hatao",
                 "bhejo", "chalao", "play")
_ACTION_RE = re.compile(r"\b(?:" + "|".join(_ACTION_WORDS) + r")\b")

_STRICT_REASK = (
    "STRICT INSTRUCTION: Pichhle jawab me tumne koi tool NAHI chalaya, "
    "sirf salah/text diya - ye GALAT hai, tum ek WORKER ho. User ne "
    "kaam karne ko kaha hai. Ab bina kisi prose ke SIRF ek JSON "
    "tool-call do aur asal me tool chalao. Agar kaam sach me kisi "
    "bhi tool se ho hi nahi sakta, tabhi text me saaf wajah batao.")


def _has_action_intent(message: str) -> bool:
    """User ke hukum me kaam karne wala shabd hai ya nahi."""
    return bool(_ACTION_RE.search((message or "").lower()))


def _ladder_run(contents: list):
    """Model ladder chalao: pehle primary, fail ho to dusra model.

    Safal ho to (jawab, tool_chala_kya); dono fail hon ya key ki
    galti ho to (error_message, None). Har model apni fail-fast
    retry neeti (timeout/network 2 koshish, busy 3 koshish) se
    chalta hai. Key ki galti (400/401/403) par ladder turant rukti
    hai - dusra model bhi wahi key use karega, koshish bekaar hai.
    """
    models = _ladder_models()
    last_exc = None
    for idx, model in enumerate(models):
        try:
            reply, used_tool = _gemini_converse(contents, model)
            if idx > 0:
                reply = ("(pehle model se jawab nahi aaya, dusre model "
                         "se laya hu)\n" + reply)
            return reply, used_tool
        except urllib.error.HTTPError as exc:
            if exc.code in _KEY_ERROR_CODES:
                log(f"GEMINI key-type error (HTTP {exc.code}) - "
                    "ladder yahin ruk gayi")
                return _gemini_http_message(exc), None
            last_exc = exc
            log(f"GEMINI ladder: {model} fail (HTTP {exc.code})")
        except Exception as exc:  # slow / busy / network - dusra try karo
            last_exc = exc
            log(f"GEMINI ladder: {model} fail: {exc}")
        if idx + 1 < len(models):
            log(f"GEMINI ladder: {model} -> {models[idx + 1]}")
    return _final_error_message(last_exc), None


def gemini_ask(message: str) -> str:
    """Gemini se jawab lao - ladder ke saath, discipline ke saath.

    Dono fail hon to jawab AAKHRI error ki class se banta hai (busy
    -> busy message, timeout -> slow message, 404 -> plain message).
    Jawab aa jaye lekin hukum action wala ho aur koi tool na chala
    ho (sirf salah mili ho), to ek baar strict re-ask hota hai.
    """
    with _history_lock:
        _history.append({"role": "user", "parts": [{"text": message}]})
        del _history[:-20]  # keep the last ~10 exchanges
        contents = list(_history)
    reply, used_tool = _ladder_run(contents)
    if used_tool is None:
        return reply  # error message - re-ask ka koi matlab nahi
    if used_tool or not _has_action_intent(message):
        return reply
    # Discipline re-ask: sirf EK baar. Pehle history se wo text-wala
    # model jawab hatao (re-ask uski jagah lega), phir sakht hukum
    # ke saath ladder dobara chalao.
    log("DISCIPLINE: action hukum par koi tool nahi chala - strict "
        "re-ask (ek baar)")
    with _history_lock:
        if _history and _history[-1].get("role") == "model":
            _history.pop()
    strict_contents = contents + [
        {"role": "user", "parts": [{"text": _STRICT_REASK}]}]
    reply2, used2 = _ladder_run(strict_contents)
    if used2 is None:
        return reply  # re-ask bhi fail - pehla jawab hi de do
    return reply2


def ask_agent(message: str) -> str:
    """Single entry point used by both the chat loop and the HTTP hook."""
    message = (message or "").strip()
    if not message:
        return "Kuch likho to sahi, bhai."
    log(f"ASK: {message[:200]}")
    if _is_update_command(message):
        # 'update' wala hukum dono modes me sabse pehle pakda jata hai -
        # demo/Gemini dispatch se pehle, seedha self-update tool chalta hai.
        return run_tool("agent_update", {})
    site_reply = _site_open_reply(message)
    if site_reply is not None:
        # 'facebook kholo' jaisa hukum - bina Gemini ke turant khulta
        # hai, isliye demo/Gemini se pehle yahin nipta diya jata hai.
        return site_reply
    demo_reply = demo_ask(message)
    if demo_reply is not None:
        return demo_reply
    if GEMINI_API_KEY:
        return gemini_ask(message)
    return ("Abhi main demo mode me hu - bina Gemini key ke main sirf "
            "tool wale kaam kar sakta hu. 'help' likho, commands dikha dunga. "
            "Free chat ke liye config.env me apni free Gemini key daal do.")

# --------------------------------------------------------------------------
# Premium chat screen (served at GET /) - same design as the phone app.
# The page also lives in ui.html next to this script for easy editing;
# ui.html wins when present, this embedded copy is the fallback.
# --------------------------------------------------------------------------

UI_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>My Agent — PC Chat</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { height: 100%; }
  body {
    font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #EAF2FF; letter-spacing: .1px;
    background:
      radial-gradient(1100px 600px at 88% -12%, rgba(0,114,206,.42), transparent 62%),
      radial-gradient(820px 560px at -22% 14%, rgba(0,229,255,.16), transparent 56%),
      radial-gradient(680px 460px at 112% 62%, rgba(96,64,255,.14), transparent 60%),
      radial-gradient(1000px 700px at 50% 118%, rgba(64,50,220,.20), transparent 62%),
      linear-gradient(180deg, #070C1B 0%, #050A14 52%, #03060D 100%);
    background-attachment: fixed;
    display: flex; flex-direction: column; height: 100dvh; overflow: hidden; position: relative;
  }
  body::after {
    content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0; opacity: .35;
    background-image: radial-gradient(rgba(160,210,255,.05) 1px, transparent 1px);
    background-size: 26px 26px;
  }
  .col { width: min(880px, 100%); margin: 0 auto; display: flex; flex-direction: column; height: 100%; position: relative; z-index: 1; }
  /* ---------- Header (glass) ---------- */
  header {
    flex: 0 0 auto; display: flex; align-items: center; gap: 13px;
    padding: 15px 20px 13px; margin-top: 14px;
    border-radius: 20px;
    background: linear-gradient(180deg, rgba(24,42,76,.66), rgba(11,20,40,.58));
    border: 1px solid rgba(130,190,255,.16);
    box-shadow: 0 14px 34px rgba(0,0,0,.42), inset 0 1px 0 rgba(255,255,255,.09);
    backdrop-filter: blur(18px) saturate(1.5); -webkit-backdrop-filter: blur(18px) saturate(1.5);
    position: relative;
  }
  header::after {
    content: ""; position: absolute; left: 24px; right: 24px; bottom: -1px; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,229,255,.75), rgba(0,114,206,.75), transparent);
  }
  .avatar { position: relative; width: 50px; height: 50px; flex: 0 0 50px; }
  .avatar svg { width: 50px; height: 50px; display: block; filter: drop-shadow(0 0 10px rgba(0,194,255,.75)); animation: pulse 3.2s ease-in-out infinite; }
  @keyframes pulse { 0%,100% { filter: drop-shadow(0 0 7px rgba(0,194,255,.55)); } 50% { filter: drop-shadow(0 0 16px rgba(0,229,255,.95)); } }
  .avatar .dot { position: absolute; right: 1px; bottom: 3px; width: 11px; height: 11px; border-radius: 50%;
    background: #2EEA8B; border: 2px solid #081226; box-shadow: 0 0 9px rgba(46,234,139,.95); }
  .htitle { flex: 1; min-width: 0; }
  .htitle h1 { font-size: 21px; font-weight: 850; letter-spacing: .3px; line-height: 1.15;
    background: linear-gradient(92deg, #FFFFFF 5%, #CDEBFF 52%, #54C4FF 95%); -webkit-background-clip: text; background-clip: text; color: transparent; }
  .htitle p { font-size: 12px; font-weight: 600; letter-spacing: .35px; color: #9DB4D6; margin-top: 3px; }
  .lockbtn {
    flex: 0 0 auto; padding: 9px 14px; border-radius: 999px; cursor: pointer; font-family: inherit;
    font-size: 12.5px; font-weight: 700; color: #BFE6FF;
    background: rgba(90,160,255,.10); border: 1px solid rgba(120,190,255,.4);
  }
  .lockbtn:active { transform: scale(.96); }
  /* ---------- Chat ---------- */
  #chat { flex: 1 1 auto; overflow-y: auto; padding: 20px 6px 14px; scroll-behavior: smooth; }
  .msgrow { display: flex; margin-bottom: 13px; animation: in .24s ease-out; }
  @keyframes in { from { opacity: 0; transform: translateY(7px); } to { opacity: 1; transform: none; } }
  .msgrow.user { justify-content: flex-end; }
  .msgrow.agent { justify-content: flex-start; }
  .bubble { max-width: 82%; padding: 13px 16px; font-size: 15.5px; line-height: 1.65; word-wrap: break-word; overflow-wrap: anywhere; white-space: normal; }
  .msgrow.user .bubble {
    color: #fff; border-radius: 20px 20px 5px 20px;
    background:
      linear-gradient(180deg, rgba(255,255,255,.14), rgba(255,255,255,0) 42%),
      linear-gradient(135deg, #0E9BF2 0%, #0072CE 56%, #6D28D9 130%);
    box-shadow: 0 10px 24px rgba(0,114,206,.40), 0 2px 6px rgba(0,0,0,.3), inset 0 1px 0 rgba(255,255,255,.30);
  }
  .msgrow.agent .bubble {
    color: #E9F2FF; border-radius: 20px 20px 20px 5px;
    background:
      linear-gradient(180deg, rgba(255,255,255,.055), rgba(255,255,255,0) 38%),
      linear-gradient(165deg, #1A2947 0%, #121E35 58%, #0E1729 100%);
    border: 1px solid rgba(120,180,255,.22);
    box-shadow: 0 10px 24px rgba(0,0,0,.38), inset 0 1px 0 rgba(255,255,255,.07), inset 0 0 22px rgba(0,120,255,.05);
  }
  .bubble b, .bubble strong { color: #AEE1FF; }
  .msgrow.user .bubble b, .msgrow.user .bubble strong { color: #FFFFFF; }
  .bubble code { background: rgba(0,180,255,.14); border: 1px solid rgba(0,180,255,.22); padding: 1px 6px; border-radius: 6px; font-size: 13.5px; }
  .bubble.err { border-color: rgba(255,110,120,.5); }
  /* ---------- Plan card ---------- */
  .plan-card {
    min-width: 230px; border-radius: 15px; overflow: hidden;
    background: linear-gradient(170deg, rgba(10,26,52,.72), rgba(8,17,34,.88));
    border: 1px solid rgba(0,194,255,.30);
    box-shadow: inset 0 1px 0 rgba(255,255,255,.08), 0 6px 18px rgba(0,0,0,.32);
  }
  .plan-head {
    display: flex; align-items: center; gap: 9px; padding: 11px 13px;
    background: linear-gradient(90deg, rgba(0,150,255,.24), rgba(0,90,200,.10) 70%, transparent);
    border-bottom: 1px solid rgba(110,180,255,.20);
  }
  .plan-tag {
    flex: 0 0 auto; font-size: 9.5px; font-weight: 900; letter-spacing: 1.4px; color: #04121F;
    padding: 3.5px 7px; border-radius: 6px;
    background: linear-gradient(135deg, #54E0FF, #00A8F0);
    box-shadow: 0 2px 8px rgba(0,180,255,.5);
  }
  .plan-title { font-size: 14.5px; font-weight: 800; line-height: 1.35; color: #FFFFFF; }
  .plan-rows { padding: 7px 8px 9px; }
  .plan-row { display: flex; gap: 10px; align-items: flex-start; padding: 8px 9px; border-radius: 10px; font-size: 14.5px; line-height: 1.5; color: #DCEBFF; }
  .plan-row + .plan-row { border-top: 1px solid rgba(120,180,255,.08); }
  .plan-row .check {
    flex: 0 0 auto; width: 19px; height: 19px; margin-top: 2px; border-radius: 50%; position: relative;
    border: 1.6px solid rgba(0,205,255,.85);
    background: radial-gradient(circle at 34% 30%, rgba(0,220,255,.34), rgba(0,120,220,.12));
    box-shadow: 0 0 8px rgba(0,190,255,.35), inset 0 1px 0 rgba(255,255,255,.25);
  }
  .plan-row.done .check { background: linear-gradient(135deg, #2EEA8B, #0BBF74); border-color: rgba(90,255,180,.9); box-shadow: 0 0 9px rgba(46,234,139,.5); }
  .plan-row.done .check::after {
    content: ""; position: absolute; left: 5.5px; top: 2.5px; width: 5px; height: 9px;
    border: solid #04240F; border-width: 0 2.2px 2.2px 0; transform: rotate(42deg);
  }
  .plan-row.done span:last-child { color: #9FB8D8; text-decoration: line-through; text-decoration-color: rgba(120,180,220,.55); }
  .plan-note { padding: 10px 13px 12px; font-size: 14px; line-height: 1.6; color: #BFD4F2; border-top: 1px solid rgba(110,180,255,.14); }
  .plan-note:first-child { border-top: 0; }
  /* typing */
  .typing { display: inline-flex; gap: 5px; align-items: center; padding: 5px 2px; }
  .typing span { width: 8px; height: 8px; border-radius: 50%; background: #6FCBFF; opacity: .35; animation: blink 1.1s infinite; box-shadow: 0 0 7px rgba(0,190,255,.6); }
  .typing span:nth-child(2) { animation-delay: .18s; } .typing span:nth-child(3) { animation-delay: .36s; }
  @keyframes blink { 0%,80%,100% { opacity: .25; transform: translateY(0); } 40% { opacity: 1; transform: translateY(-3px); } }
  /* ---------- Hero / empty state ---------- */
  .heroWrap { text-align: center; padding: 26px 6px 4px; animation: in .35s ease-out; }
  .bigAvatar { position: relative; width: 118px; height: 118px; margin: 0 auto 6px; }
  .bigAvatar::before, .bigAvatar::after { content: ""; position: absolute; border-radius: 50%; pointer-events: none; }
  .bigAvatar::before { inset: -17px; border: 1px solid rgba(0,200,255,.20); box-shadow: 0 0 34px rgba(0,160,255,.16), inset 0 0 34px rgba(0,160,255,.10); animation: halo 3.6s ease-in-out infinite; }
  .bigAvatar::after { inset: -34px; border: 1px dashed rgba(110,190,255,.13); animation: halo 3.6s ease-in-out infinite reverse; }
  @keyframes halo { 0%,100% { opacity: .55; transform: scale(.985); } 50% { opacity: 1; transform: scale(1.015); } }
  .bigAvatar svg { width: 118px; height: 118px; display: block; filter: drop-shadow(0 0 22px rgba(0,194,255,.85)) drop-shadow(0 14px 26px rgba(0,0,0,.5)); animation: pulse 3.2s ease-in-out infinite; }
  .bigAvatar .dot { position: absolute; right: 7px; bottom: 10px; width: 17px; height: 17px; border-radius: 50%;
    background: #2EEA8B; border: 3px solid #081226; box-shadow: 0 0 13px rgba(46,234,139,.95); }
  .heroWrap h3 { font-size: 27px; font-weight: 900; letter-spacing: .2px; line-height: 1.22; margin-top: 14px;
    background: linear-gradient(92deg, #FFFFFF 8%, #CDEBFF 52%, #4FC0FF 96%); -webkit-background-clip: text; background-clip: text; color: transparent; }
  .heroWrap .heroSub { font-size: 13px; font-weight: 600; letter-spacing: .5px; color: #8FA9CC; margin-top: 7px; }
  .heroWrap .heroLine { font-size: 14.5px; line-height: 1.65; color: #C7D9F4; margin: 13px auto 2px; max-width: 520px; }
  /* chips */
  .chips { display: flex; flex-wrap: wrap; gap: 9px; justify-content: center; margin: 16px 2px 8px; }
  .chip {
    padding: 10px 15px; border-radius: 999px; font-size: 13.5px; font-weight: 650; cursor: pointer; color: #DCEFFF; font-family: inherit;
    background:
      linear-gradient(180deg, rgba(255,255,255,.07), rgba(255,255,255,0) 45%),
      linear-gradient(160deg, rgba(42,72,124,.92), rgba(18,32,60,.94));
    border: 1px solid rgba(110,180,255,.38); box-shadow: 0 6px 15px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.10);
  }
  .chip:active { transform: scale(.96); }
  /* ---------- Floating pill input ---------- */
  #quickbar { flex: 0 0 auto; display: flex; gap: 8px; flex-wrap: wrap; padding: 2px 4px 9px; }
  #quickbar .chip { padding: 8px 13px; font-size: 12.5px; }
  #inputbar {
    flex: 0 0 auto; display: flex; gap: 9px; align-items: flex-end;
    margin: 0 0 16px; padding: 8px;
    border-radius: 31px;
    background: linear-gradient(180deg, rgba(26,44,80,.78), rgba(10,19,38,.88));
    border: 1px solid rgba(120,185,255,.26);
    box-shadow: 0 18px 38px rgba(0,0,0,.55), 0 0 22px rgba(0,140,255,.10), inset 0 1px 0 rgba(255,255,255,.10);
    backdrop-filter: blur(16px) saturate(1.4); -webkit-backdrop-filter: blur(16px) saturate(1.4);
  }
  #input {
    flex: 1; resize: none; max-height: 120px; min-height: 47px;
    padding: 13px 17px; border-radius: 24px; border: 1px solid rgba(110,170,255,.20);
    background: rgba(9,20,42,.88); color: #F2F8FF; font-size: 15.5px; font-family: inherit; outline: none;
    box-shadow: inset 0 2px 9px rgba(0,0,0,.5);
  }
  #input:focus { border-color: rgba(0,194,255,.65); box-shadow: inset 0 2px 9px rgba(0,0,0,.5), 0 0 0 3px rgba(0,160,255,.15); }
  #input::placeholder { color: #7188AC; }
  #send {
    flex: 0 0 auto; width: 48px; height: 48px; border-radius: 50%; border: 0; cursor: pointer; margin: 0 1px 1px 0;
    display: flex; align-items: center; justify-content: center; color: #fff;
    background: radial-gradient(circle at 32% 27%, #4BD8FF, #0090E8 56%, #0063B4);
    box-shadow: 0 8px 22px rgba(0,150,255,.55), 0 0 20px rgba(0,194,255,.5), inset 0 1px 0 rgba(255,255,255,.5), inset 0 -2px 5px rgba(0,40,90,.35);
  }
  #send:active { transform: scale(.93); }
  #send:disabled { opacity: .55; }
  #send svg { width: 21px; height: 21px; margin-left: 2px; }
  /* ---------- PIN gate ---------- */
  #pinGate {
    position: fixed; inset: 0; z-index: 30; display: none;
    align-items: center; justify-content: center; padding: 18px;
    background: rgba(2,6,14,.72); backdrop-filter: blur(7px); -webkit-backdrop-filter: blur(7px);
  }
  #pinGate.open { display: flex; }
  .pinCard {
    width: min(400px, 100%); padding: 27px 24px 24px; border-radius: 24px; text-align: center;
    background:
      linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,0) 34%),
      linear-gradient(165deg, rgba(26,48,90,.95), rgba(11,20,40,.98));
    border: 1px solid rgba(0,194,255,.38);
    box-shadow: 0 24px 50px rgba(0,0,0,.6), 0 0 34px rgba(0,140,255,.16), inset 0 1px 0 rgba(255,255,255,.11);
    animation: in .3s ease-out;
  }
  .pinCard .miniAvatar { width: 74px; height: 74px; margin: 0 auto 10px; position: relative; }
  .pinCard .miniAvatar svg { width: 74px; height: 74px; filter: drop-shadow(0 0 15px rgba(0,194,255,.8)); animation: pulse 3.2s ease-in-out infinite; }
  .pinCard h2 { font-size: 20px; font-weight: 850; color: #fff; margin-bottom: 7px; }
  .pinCard p { font-size: 14px; line-height: 1.65; color: #C7D9F4; margin-bottom: 15px; }
  .pinCard input {
    width: 100%; padding: 14px 15px; border-radius: 14px; font-size: 16px; text-align: center; letter-spacing: 2px;
    color: #F2F8FF; background: #0A1730; border: 1px solid rgba(110,170,255,.32); outline: none; font-family: inherit;
    box-shadow: inset 0 2px 8px rgba(0,0,0,.4);
  }
  .pinCard input:focus { border-color: rgba(0,194,255,.75); }
  .pinBtn {
    display: block; width: 100%; padding: 14px; border-radius: 14px; border: 0; cursor: pointer; font-family: inherit;
    font-size: 15.5px; font-weight: 800; color: #fff; margin-top: 13px;
    background: linear-gradient(135deg, #12BCFF, #0072CE); box-shadow: 0 10px 24px rgba(0,114,206,.45), inset 0 1px 0 rgba(255,255,255,.3);
  }
  .pinBtn:active { transform: scale(.985); }
  .pinErr { display: none; margin-top: 12px; font-size: 13.5px; font-weight: 700; color: #FFB3B9; line-height: 1.55; }
</style>
</head>
<body>
<div class="col">

<header>
  <div class="avatar">
    <svg viewBox="0 0 100 100" fill="none" aria-hidden="true">
      <defs>
        <linearGradient id="rg" x1="0" y1="0" x2="100" y2="100">
          <stop offset="0%" stop-color="#00E5FF"/><stop offset="55%" stop-color="#0090FF"/><stop offset="100%" stop-color="#0067D8"/>
        </linearGradient>
        <linearGradient id="ag" x1="0" y1="100" x2="0" y2="0">
          <stop offset="0%" stop-color="#7ED8FF"/><stop offset="100%" stop-color="#FFFFFF"/>
        </linearGradient>
      </defs>
      <circle cx="50" cy="50" r="44" stroke="url(#rg)" stroke-width="6"/>
      <circle cx="50" cy="50" r="35" fill="rgba(0,110,220,0.14)"/>
      <path d="M50 27 L64 68 H57.2 L53.4 56.5 H46.6 L42.8 68 H36 Z M50 40 L54.6 51 H45.4 Z" fill="url(#ag)"/>
      <circle cx="78" cy="24" r="3.4" fill="#9BEAFF"/>
    </svg>
    <span class="dot"></span>
  </div>
  <div class="htitle">
    <h1>My Agent</h1>
    <p>Ankit&rsquo;s personal agent &bull; Online &bull; Private &bull; Sirf tumhare PC par</p>
  </div>
  <button class="lockbtn" id="lockBtn" type="button">PIN badlo</button>
</header>

<div id="chat"></div>

<div id="quickbar">
  <button class="chip" type="button" data-send="Aaj ka plan banao">Aaj ka plan banao</button>
  <button class="chip" type="button" data-send="Movie idea do">Movie idea do</button>
  <button class="chip" type="button" data-send="list files">Files dikhao</button>
  <button class="chip" type="button" data-send="skills">Skills</button>
  <button class="chip" type="button" data-send="time">Time batao</button>
</div>

<div id="inputbar">
  <textarea id="input" rows="1" placeholder="Apne agent se kuch bhi pucho..." enterkeyhint="send"></textarea>
  <button id="send" aria-label="Send">
    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M3.4 20.4l17.8-7.5c.8-.35.8-1.45 0-1.8L3.4 3.6c-.66-.29-1.39.2-1.39.91L2 9.12c0 .5.37.93.87.99L17 12 2.87 13.88c-.5.07-.87.5-.87 1l.01 4.61c0 .72.73 1.2 1.39.91z"/></svg>
  </button>
</div>

</div>

<div id="pinGate">
  <div class="pinCard">
    <div class="miniAvatar">
      <svg viewBox="0 0 100 100" fill="none" aria-hidden="true">
        <defs>
          <linearGradient id="rg3" x1="0" y1="0" x2="100" y2="100">
            <stop offset="0%" stop-color="#00E5FF"/><stop offset="55%" stop-color="#0090FF"/><stop offset="100%" stop-color="#0067D8"/>
          </linearGradient>
          <linearGradient id="ag3" x1="0" y1="100" x2="0" y2="0">
            <stop offset="0%" stop-color="#7ED8FF"/><stop offset="100%" stop-color="#FFFFFF"/>
          </linearGradient>
        </defs>
        <circle cx="50" cy="50" r="44" stroke="url(#rg3)" stroke-width="6"/>
        <circle cx="50" cy="50" r="35" fill="rgba(0,110,220,0.14)"/>
        <path d="M50 27 L64 68 H57.2 L53.4 56.5 H46.6 L42.8 68 H36 Z M50 40 L54.6 51 H45.4 Z" fill="url(#ag3)"/>
        <circle cx="78" cy="24" r="3.4" fill="#9BEAFF"/>
      </svg>
    </div>
    <h2>Apna PIN daalo</h2>
    <p>Ye chat sirf tumhare liye hai. Wahi PIN daalo jo tumne <b>config.env</b> file me <b>AGENT_PIN</b> par rakha tha. PIN sirf is browser tab me yaad rahega — tab band, PIN gaya.</p>
    <input type="password" id="pinInput" placeholder="Apna PIN" autocomplete="off">
    <button class="pinBtn" id="pinBtn" type="button">Chat shuru karo</button>
    <div class="pinErr" id="pinErr"></div>
  </div>
</div>

<script>
(function () {
  "use strict";
  var PIN_SS = "myagent_pc_pin";
  var chatEl = document.getElementById("chat");
  var inputEl = document.getElementById("input");
  var sendBtn = document.getElementById("send");
  var pinGate = document.getElementById("pinGate");
  var pinInput = document.getElementById("pinInput");
  var pinErr = document.getElementById("pinErr");
  var busy = false;
  var started = false;

  function getPin() { return sessionStorage.getItem(PIN_SS) || ""; }
  function setPin(p) { if (p) sessionStorage.setItem(PIN_SS, p); else sessionStorage.removeItem(PIN_SS); }

  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  function renderText(s) {
    var h = esc(s);
    h = h.replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>");
    h = h.replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<i>$2</i>");
    h = h.replace(/`([^`]+)`/g, "<code>$1</code>");
    h = h.replace(/\n/g, "<br>");
    return h;
  }
  function scrollDown() { setTimeout(function () { chatEl.scrollTop = chatEl.scrollHeight; }, 30); }

  function isCheckLine(line) {
    var t = line.replace(/^\s+/, "");
    return /^([-\u2022*\u2610\u2611\u2713\u2714]|\d+[\.\)])\s+/.test(t);
  }
  function checkInfo(line) {
    var t = line.replace(/^\s+/, "");
    var done = /^[\u2611\u2713\u2714]/.test(t);
    t = t.replace(/^([-\u2022*\u2610\u2611\u2713\u2714]|\d+[\.\)])\s+/, "");
    return { text: t, done: done };
  }
  function renderRich(text) {
    var lines = String(text).split("\n");
    var checkCount = 0, i, firstCheck = -1;
    for (i = 0; i < lines.length; i++) {
      if (isCheckLine(lines[i])) { checkCount++; if (firstCheck < 0) firstCheck = i; }
    }
    if (checkCount < 2) return renderText(text);
    var title = "Tumhara Plan";
    var headLines = [];
    for (i = 0; i < firstCheck; i++) {
      var hl = lines[i].trim().replace(/\*\*/g, "").replace(/:$/, "");
      if (hl) headLines.push(hl);
    }
    if (headLines.length) { title = headLines[0]; headLines = headLines.slice(1); }
    var rows = "", tail = [], seenCheck = false;
    for (i = 0; i < lines.length; i++) {
      if (isCheckLine(lines[i])) {
        seenCheck = true;
        var ci = checkInfo(lines[i]);
        rows += '<div class="plan-row' + (ci.done ? " done" : "") + '"><span class="check"></span><span>' + renderText(ci.text) + "</span></div>";
      } else if (seenCheck && lines[i].trim()) {
        tail.push(lines[i]);
      }
    }
    var html = '<div class="plan-card"><div class="plan-head"><span class="plan-tag">PLAN</span><span class="plan-title">' + renderText(title) + "</span></div>";
    if (headLines.length) html += '<div class="plan-note">' + renderText(headLines.join("\n")) + "</div>";
    html += '<div class="plan-rows">' + rows + "</div>";
    if (tail.length) html += '<div class="plan-note">' + renderText(tail.join("\n")) + "</div>";
    html += "</div>";
    return html;
  }

  function addBubble(role, text, isErr) {
    var row = document.createElement("div");
    row.className = "msgrow " + (role === "user" ? "user" : "agent");
    var b = document.createElement("div");
    b.className = "bubble" + (isErr ? " err" : "");
    b.innerHTML = (role === "user") ? renderText(text) : renderRich(text);
    row.appendChild(b);
    chatEl.appendChild(row);
    scrollDown();
    return row;
  }

  function showHero() {
    if (started) return;
    started = true;
    var wrap = document.createElement("div");
    wrap.id = "heroWrap";
    var heroSvg =
      '<svg viewBox="0 0 100 100" fill="none" aria-hidden="true">' +
        '<defs><linearGradient id="rg2" x1="0" y1="0" x2="100" y2="100">' +
          '<stop offset="0%" stop-color="#00E5FF"/><stop offset="55%" stop-color="#0090FF"/><stop offset="100%" stop-color="#0067D8"/>' +
        '</linearGradient><linearGradient id="ag2" x1="0" y1="100" x2="0" y2="0">' +
          '<stop offset="0%" stop-color="#7ED8FF"/><stop offset="100%" stop-color="#FFFFFF"/></linearGradient></defs>' +
        '<circle cx="50" cy="50" r="44" stroke="url(#rg2)" stroke-width="6"/>' +
        '<circle cx="50" cy="50" r="35" fill="rgba(0,110,220,0.14)"/>' +
        '<path d="M50 27 L64 68 H57.2 L53.4 56.5 H46.6 L42.8 68 H36 Z M50 40 L54.6 51 H45.4 Z" fill="url(#ag2)"/>' +
        '<circle cx="78" cy="24" r="3.4" fill="#9BEAFF"/></svg>';
    wrap.innerHTML =
      '<div class="heroWrap"><div class="bigAvatar">' + heroSvg + '<span class="dot"></span></div>' +
      '<h3>Main hu tumhara personal agent</h3>' +
      '<div class="heroSub">PRIVATE &bull; FREE &bull; SIRF TUMHARE PC PAR</div>' +
      '<p class="heroLine">Namaste Ankit bhai. Main tumhare apne computer par chalta hu — files, plans, movie ideas, roz ka kaam, sab yahi hoga aur saara data tumhare PC par hi rahega. Neeche kuch bhi likho, ya ek chip dabao.</p></div>' +
      '<div class="chips">' +
        '<button class="chip" type="button" data-send="Aaj ka plan banao">Aaj ka plan banao</button>' +
        '<button class="chip" type="button" data-send="Movie idea do">Movie idea do</button>' +
        '<button class="chip" type="button" data-send="list files">Files dikhao</button>' +
      '</div>';
    chatEl.appendChild(wrap);
    bindChips(wrap);
  }
  function bindChips(scope) {
    var chips = scope.querySelectorAll(".chip");
    for (var i = 0; i < chips.length; i++) {
      (function (chip) {
        chip.addEventListener("click", function () { sendText(chip.getAttribute("data-send") || chip.textContent.trim(), chip.textContent.trim()); });
      })(chips[i]);
    }
  }
  bindChips(document);

  function showTyping() {
    var row = document.createElement("div");
    row.className = "msgrow agent"; row.id = "typingRow";
    row.innerHTML = '<div class="bubble"><span class="typing"><span></span><span></span><span></span></span></div>';
    chatEl.appendChild(row); scrollDown();
  }
  function hideTyping() { var t = document.getElementById("typingRow"); if (t) t.remove(); }

  function openPinGate(msg) {
    pinErr.style.display = msg ? "block" : "none";
    pinErr.textContent = msg || "";
    pinInput.value = "";
    pinGate.classList.add("open");
    setTimeout(function () { pinInput.focus(); }, 60);
  }
  function closePinGate() { pinGate.classList.remove("open"); }

  function submitPin() {
    var p = pinInput.value.trim();
    if (!p) { openPinGate("PIN khali hai — config.env me jo AGENT_PIN rakha tha, wahi daalo."); return; }
    setPin(p);
    closePinGate();
    showHero();
    inputEl.focus();
  }
  document.getElementById("pinBtn").addEventListener("click", submitPin);
  pinInput.addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); submitPin(); } });
  document.getElementById("lockBtn").addEventListener("click", function () { setPin(""); openPinGate(""); });

  function sendText(text, displayText) {
    text = (text || "").trim();
    if (!text || busy) return;
    if (!getPin()) { openPinGate(""); return; }
    var hero = document.getElementById("heroWrap");
    if (hero) hero.remove();
    addBubble("user", displayText || text);
    inputEl.value = ""; autoGrow();
    busy = true; sendBtn.disabled = true;
    showTyping();
    fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, pin: getPin() })
    }).then(function (res) {
      return res.text().then(function (bodyText) { return { status: res.status, bodyText: bodyText }; });
    }).then(function (r) {
      hideTyping();
      if (r.status === 403) {
        setPin("");
        addBubble("agent", "PIN galat hai bhai — agent ne mana kar diya. config.env me jo AGENT_PIN rakha tha, wahi PIN dobara daalo.", true);
        openPinGate("PIN galat tha. Dobara try karo — PIN config.env file me AGENT_PIN ke saamne likha hai.");
        return;
      }
      var data = null;
      try { data = JSON.parse(r.bodyText); } catch (e) {}
      if (r.status !== 200 || !data || typeof data.reply !== "string") {
        addBubble("agent", "Kuch gadbad ho gayi (server se sahi jawab nahi aaya). Agent wali kaali window chal rahi hai ya nahi, ek baar dekh lo, phir dobara bhejo.", true);
        return;
      }
      addBubble("agent", data.reply);
    }).catch(function () {
      hideTyping();
      addBubble("agent", "Agent se jud nahi paya — lagta hai program band hai. Pehle start.bat se agent chalao, phir ye page refresh karke dobara bhejo.", true);
    }).finally(function () {
      busy = false; sendBtn.disabled = false;
    });
  }

  function autoGrow() {
    inputEl.style.height = "auto";
    inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + "px";
  }
  inputEl.addEventListener("input", autoGrow);
  inputEl.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendText(inputEl.value); }
  });
  sendBtn.addEventListener("click", function () { sendText(inputEl.value); });

  if (getPin()) { showHero(); } else { openPinGate(""); }
})();
</script>
</body>
</html>
'''


def _ui_page() -> str:
    try:
        f = BASE_DIR / "ui.html"
        if f.is_file():
            return f.read_text(encoding="utf-8")
    except Exception:
        pass
    return UI_HTML


# --------------------------------------------------------------------------
# Local HTTP hook - localhost ONLY, PIN checked on every request
# --------------------------------------------------------------------------


class AskHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # keep the console clean; we log to file
        pass

    def _send_html(self, page: str) -> None:
        data = page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, code: int, obj: dict) -> None:
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html", "/ui"):
            self._send_html(_ui_page())
        elif self.path == "/health":
            self._send_json(200, {"ok": True,
                                  "mode": "gemini" if GEMINI_API_KEY else "demo",
                                  "work_folder": str(WORK_DIR)})
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/ask":
            self._send_json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            self._send_json(400, {"error": "bad JSON"})
            return
        # PIN check - from the JSON body ("pin") or the X-Agent-PIN header.
        if AGENT_PIN:
            given = str(payload.get("pin", "") or
                        self.headers.get("X-Agent-PIN", ""))
            if not hmac.compare_digest(given, AGENT_PIN):
                log("HTTP /ask REJECTED (wrong PIN)")
                self._send_json(403, {"error": "wrong PIN"})
                return
        reply = ask_agent(str(payload.get("message", "")))
        self._send_json(200, {"reply": reply})


def start_http_server() -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", AGENT_PORT), AskHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    log(f"HTTP hook listening on 127.0.0.1:{AGENT_PORT}")
    return server

# --------------------------------------------------------------------------
# Main - chat loop on this PC + the HTTP hook in the background
# --------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="My Agent - PC half v1")
    parser.add_argument("--serve", action="store_true",
                        help="only run the HTTP hook (no chat loop)")
    parser.add_argument("--no-server", action="store_true",
                        help="do not start the HTTP hook")
    args = parser.parse_args()

    if not args.no_server:
        start_http_server()

    mode = "Gemini" if GEMINI_API_KEY else "demo (no key)"
    print("=" * 58)
    print("  My Agent - tumhara apna agent, tumhare hi computer par")
    print(f"  Mode: {mode}   Work folder: {WORK_DIR}")
    if not args.no_server:
        print(f"  Chat screen: http://127.0.0.1:{AGENT_PORT}/  (browser me kholo - asli screen wahi hai)")
        print(f"  Phone hook: http://127.0.0.1:{AGENT_PORT}/ask (PIN protected)")
    print("  'help' likho commands ke liye, 'quit' band karne ke liye.")
    print("=" * 58)
    log(f"START mode={mode}")

    if args.serve:
        print("Serving... Ctrl+C to stop.")
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
        return 0

    while True:
        try:
            message = input("\nYou: ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if message.strip().lower() in ("quit", "exit", "band karo"):
            break
        print(f"\nAgent: {ask_agent(message)}")
    log("STOP")
    print("Band ho gaya. Saara data yahi raha - logs/agent.log me.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

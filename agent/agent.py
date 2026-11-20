#!/usr/bin/env python3
"""
My Agent - PC half, v8.4 - Muse-style: persistent memory (MEMORY.md),
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
v8.2: DUSRA TEZ DIMAG - Groq (config.env me GROQ_API_KEY ho to pehle
Groq ka tez model jawab deta hai, wahi tool protocol aur wahi
discipline; Groq atak jaye - timeout, busy, ya galat key (401) - to
agent khud Gemini ladder par gir jata hai. Bina Groq key ke vyavhaar
bilkul v8.1 jaisa hai.)
v8.3: BROWSER HAATH - agent ab apna khaas Chrome khud chalata hai
(Chrome DevTools Protocol, sirf stdlib WebSocket - browser_hand/
cdp_client.py wala proven code is file ke andar shabdashah merge
hai). 'browser setup karo' bolne par user ke Chrome ka ek alag
profile (agent_chrome_profile/) khulta hai jisme user EK BAAR khud
login karta hai; uske baad browser_open/read/click/type/
upload_file tools se logged-in sites (Facebook/YouTube adi) ka
asal kaam hota hai. Password agent kabhi nahi mangta, dekhta ya
store karta.
v8.4: TEEN NAYI TAQATEIN - (1) VIDEO FACTORY: download_file se
poster download karke make_video tool video_factory/make_video.py
wala proven logic isi file me merge karke job folder (slides/ +
titles.txt + optional voice.mp3) se taiyaar vertical video
(1080x1920, zoom + bade titles) banata hai; naya seed skill
'video-banana'. (2) VIDEO DEKH KAR SEEKHNA: watch_video tool
Gemini ki video-understanding se YouTube link ya work/ ki video
file dekh kar uske steps nikalta hai; steps pehle user ko dikhte
hain, uski haan par hi create_skill se skill banti hai. (3)
PROGRAM CHALANA: run_program tool user ke kahe par PC par
command/program chalata hai (software install/chalana) - ek
chhoti denylist seatbelt ki tarah khatarnak commands (disk
format, system delete, shutdown) rokti hai; paisa/delete par
pehle puchna wala rule prompt me hai.

A personal agent that runs on Ankit's OWN computer.
- All files and logs stay on this machine.
- Brain = Google Gemini free API (key from a local config file, never in code),
  plus optional Groq free API as the fast first brain (same rule: key
  only in the local config file, never in code).
- Without a key it runs in demo/offline mode: direct tool commands still work.
- Tools are confined to the work/ folder. Nothing outside it can be touched.
- A tiny HTTP hook on 127.0.0.1 (localhost ONLY) lets the phone app talk to
  it later. Every request must carry the shared PIN from the config.

Stdlib only. No pip installs needed. Python 3.9+.
"""

import argparse
import base64
import hashlib
import hmac
import html
import json
import os
import platform
import re
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import urllib.error
import urllib.request
import webbrowser
import zipfile
from urllib.parse import unquote
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

AGENT_VERSION = "8.5"
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
      GROQ_API_KEY     - optional: his free Groq key (stored ONLY here).
                         Ho to pehle tez wala Groq dimag jawab deta hai,
                         atak jaye to Gemini khud sambhal leta hai.
      GROQ_MODEL       - default: llama-3.3-70b-versatile
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
    for key in ("GEMINI_API_KEY", "GEMINI_MODEL", "GROQ_API_KEY",
                "GROQ_MODEL", "AGENT_PIN", "AGENT_PORT", "AGENT_WORK_DIR"):
        if os.environ.get(key):
            cfg[key] = os.environ[key]
    return cfg


CONFIG = load_config()
GEMINI_API_KEY = CONFIG.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = CONFIG.get("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
GROQ_API_KEY = CONFIG.get("GROQ_API_KEY", "").strip()
GROQ_MODEL = (CONFIG.get("GROQ_MODEL", "").strip()
              or "llama-3.3-70b-versatile")
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
All data stays on his computer. You may use the available tools: files
tum poore computer me padh aur dhoond sakte ho (Desktop, Downloads,
Documents - jahan Ankit ne rakha ho wahi se), likhne ka kaam work
folder aur Ankit ke apne folders me hota hai. Never ask for or reveal
any API key or PIN.

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

BROWSER HAATH (agent wala Chrome - logged-in sites ke liye):
- Tumhare paas ek khaas Chrome hai jise tum browser wale tools se
  khud chala sakte ho. Wo Ankit ke roz wale Chrome se ALAG hai;
  Ankit usme ek baar khud login karta hai ('browser setup karo'
  command se khulta hai). Browser tool se jawab aaye ki Chrome
  taiyaar nahi hai, to Ankit ko bas 'browser setup karo' likhne ko
  bolo - usse aage khud kuch mat karo.
- Login wali site ka kaam ho (Facebook/YouTube/TikTok par upload,
  post, comments padhna) to pehle matching skill padho, phir
  browser tools se kaam karo: browser_open se page kholo,
  browser_read se dekho page par kya hai, phir click/type/upload.
- Password KABHI mat mango, mat bharo, mat store karo. Login
  sirf Ankit ke haath ka kaam hai.
- Page par login check, CAPTCHA, 2FA ya "confirm it's you" jaisi
  screen dikhe to TURANT ruk jao aur Ankit ko bolo ki wo screen
  khud sambhale. Use solve ya bypass karne ki koshish kabhi mat
  karna.
- Upload/post wale kaam me saari taiyaari khud karo - file
  lagana, caption bharna, browser_read se verify karna - aur
  AAKHRI Post/Publish/Schedule wala click BHI KHUD dabao:
  Ankit ka hukum ("upload kar do", "post kar do", "daal do",
  "schedule kar do") HI uski manjuri hai, alag se haan ka
  intezaar mat karo. Click ke baad browser_read se verify
  karke tabhi "ho gaya" bolo. Aakhri click SIRF tab roko
  jab Ankit khud bole "taiyaar karke dikhao", "pehle
  dikhao" ya "draft banao" - matlab use pehle dekhna hai;
  tab sab taiyaar rakh kar use bata do ki post ke liye
  taiyaar hai.
- Har browser kadam ke baad browser_read se page dobara padho;
  andhere me click mat karo. Kuch na mile to saaf batao page par
  kya dikh raha hai.

VIDEO BANANA (poster + awaaz se poori video):
- "Is movie ki video banao" jaisa hukum aaye to pehle
  'video-banana' skill padho aur usi ke steps follow karo:
  poster download_file se job folder ke slides/ me lo,
  titles.txt likho (har slide: MOVIE NAAM | hook line), chaaho
  to speak_to_file se awaaz bana kar job folder me voice file
  rakho (ya wahan padi voice file apne aap lag jayegi), phir
  make_video chalao. Kaam ke baad output ki video_info lo aur
  path + duration + size verify karke batao.

VIDEO DEKH KAR SEEKHNA:
- Ankit kahe "ye video dekh kar seekho" (YouTube ka link ya
  koi video file) to watch_video chalao. Usse mile
  steps Ankit ko pehle chat me dikhao aur saaf pucho: "ye
  skill bana du?" - uski HAAN mile tabhi create_skill se skill
  banao. Bina dikhaye aur bina haan ke kabhi skill mat banao.

VIDEO DEKH KAR SOFTWARE INSTALL / CHALANA (poori chain):
- Ankit kisi SOFTWARE ke baare me tutorial video de (link ya
  file) aur kahe "ye dekh kar ye software install kar do /
  chala do", to poori chain ek saath follow karo:
  1. watch_video se video ke steps samjho.
  2. Mile hue steps Ankit ko dikhao; uske aage badhne par
     create_skill se un steps ki skill save kar do
     (nayi-skill-seekhna wala flow) taaki agli baar video
     dobara na dekhna pade.
  3. Software hamesha uske OFFICIAL source se lo -
     download_file se installer download karo ya run_program
     se official install command chalao. Anjaan/third-party
     site se installer kabhi mat lena.
  4. Phir seekhe hue tareeke se hi software ko run_program
     se chalao / setup karo, aur output dekh kar verify
     karo ki asal me chal pada - tabhi Ankit ko batao.
- Install ke beech paisa mange (paid software) ya
  khatarnak-class command lage to wahi purana rule: pehle
  poochna, mana kabhi nahi - haan mile to aage badho.

FILES (poora computer - koi seema nahi):
- Ankit kisi file ya folder ka NAAM bole (jaise "Dragon
  Princess Hook Reels") to pehle find_file se use poore
  computer me dhoondo. Use file ko work/ folder me rakhne
  ko KABHI mat bolo - file jahan hai, wahi se kaam karo:
  list_files / read_file poore computer me padh sakte
  hain (poora path do), video aur photo wale tools bhi.
- Ankit kisi file ko CHALA kar dikhane ko kahe (video
  play karna, photo/document kholna) to open_file chalao -
  file uske default player/app me khul jayegi. Pehle
  find_file se path nikalo, phir open_file se chalao -
  "video play karna chahiye tha" wala hukum sirf baat se
  nahi, asal me khol kar pura hota hai.
- .zip ke andar ki file ka kaam ho (Drive se aayi zip me
  band video jaisa) to pehle extract_zip se zip kholo,
  phir andar nikli file par kaam karo - zip ke andar ki
  file seedha play/upload NAHI hoti, pehle kholna
  zaroori hai.
- Likhne ka kaam (write_file, create_folder, download ki
  file, video ka output) work/ folder ya Ankit ke apne
  folders (Desktop, Downloads, Documents, poora home
  folder) me hoga. System wali jagah (C:\\Windows, Program
  Files jaisi) par likhne se tool mana karega - wahan
  likhna PC ke liye khatarnak hai, kaam wahan hota bhi
  nahi.

PHOTO (screenshot / tasveer dekhna):
- Ankit chat me photo/screenshot bheje to tum use khud
  dekh kar jawab dete ho - photo me jo dikh raha hai
  (error, screen, koi bhi cheez) usi ko padh kar usi par
  jawab do, jaise photo tumhare saamne khuli ho.
- PC par padi kisi photo file ko dekhna ho to see_image
  chalao (poora path do) - photo me kya hai samajh kar
  milega, phir usi par kaam aage badhao.
- Photo ke saath koi HUKUM aaye ("is se video le kar
  upload kar do", "ye wala folder kholo") to photo ke
  vivaran me dikhe naam/path ko sach maan kar wahi kaam
  aam tools se asal me karo - sirf photo ka vivaran
  suna kar mat ruk jao.

PROGRAM CHALANA (software install karna / chalana):
- Ankit koi software install karne ya koi program chalane ko
  kahe to run_program se asal me chalao - sirf steps bata kar
  mat chhodo.
- Jo install PAISA mangta ho (paid software, paid plan) ya jo
  command Ankit ki apni files DELETE karti ho, use chalane se
  PEHLE Ankit ko saaf shabdon me bata kar uski haan lo. Iske
  alawa aam install aur program bina puche chalao.
- Khatarnak-class command (disk format, system folder
  delete, shutdown jaisi) par run_program CONFIRM_REQUIRED
  deta hai - ye MANA NAHI hai, POOCHNA hai. Tab Ankit ko
  saaf shabdon me batao ki command kya karegi aur pucho
  "chala du?". Uski HAAN mile to WAHI command run_program
  me confirm=true ke saath dobara chalao - haan hi kaafi
  hai. Mana karna, ya ghuma-phira kar dusra rasta
  dhoondna, sakht mana hai. Paisa/delete par pehle poochna
  hai, mana kabhi nahi - haan mile to kar do.

TOOL PROTOCOL: If you need a tool, reply with ONLY a JSON object like
{"tool": "list_files", "args": {"path": ""}} and nothing else.
FORMAT RULE (bahut zaroori): tool call wala jawab SIRF wahi ek JSON
object hoga - usse pehle ya baad me EK SHABD bhi nahi, koi prose,
koi "main kar deta hu" wali line nahi. "args" hamesha ek asli JSON
object hoga {"url": "..."} - kabhi bhi string ke andar band kiya
hua JSON nahi bhejoge.
Available tools:
- list_files(path)           kisi bhi folder ki list - poora path do
                             to wahi ka (Desktop adi), sirf naam ya
                             khaali do to work folder ka
- read_file(path)            text file padho - poora path chalega,
                             sirf naam/relative ho to work folder me
- find_file(name)            naam se poore computer me file/folder
                             dhoondo (aadha naam bhi chalega) - Ankit
                             kisi file ka naam bole to PEHLE yahi
                             chalao
- open_file(path)            file ko uske default app me kholo -
                             video play karna ho ya photo/document
                             kholna ho to yahi chalao (path pehle
                             find_file se nikaal sakte ho)
- extract_zip(path)          .zip file ko uske paas wale folder me
                             kholo - zip ke andar ki video/file par
                             kaam karne se pehle yahi chalao
- see_image(path)            PC par padi photo/screenshot dekho -
                             usme kya hai samajh kar milega
- write_file(path, content)  text file likho - work folder ya Ankit
                             ke apne folders me (system jagah nahi)
- create_folder(path)        folder banao - work folder ya Ankit ke
                             apne folders me
- get_time()                 current date and time on this computer
- web_fetch(url)             fetch an http/https page and return its text
- list_skills()              list the learned skill files
- read_skill(name)           read one skill file, e.g. "youtube-upload"
- create_skill(name, content)  save a new skill (only inside skills/)
- yaad_likho(text)           save an important baat to long-term memory (MEMORY.md)
- open_url(url)              open a page in this PC's default browser
- video_info(path)           duration/size/resolution - video kahi
                             bhi ho, poora path do
- trim_video(input, start_sec, duration_sec, output)  cut a video
                             (input kahi bhi ho sakta hai; output
                             work/ ya Ankit ke folders me)
- join_videos(files, output) join videos in order (inputs kahi bhi;
                             output work/ ya Ankit ke folders me)
- speak_to_file(text, filename)  make a voice audio file inside work/
- agent_update()             check for a newer version of myself and
                             install it (engine restart ke baad lagega)
- browser_open(url)          agent wale Chrome me page kholo
                             (logged-in sites ke kaam ke liye; Chrome
                             taiyaar na ho to user ko 'browser setup
                             karo' likhne ko bolo)
- browser_read()             abhi khule page ka title + text padho
- browser_click(target)      page par button/link dabao - target ek
                             CSS selector ya dikhai dene wala text hai
- browser_type(target, text) kisi field me likho (caption, title adi)
- browser_upload_file(target, path)  page ke file-input par file
                             lagao (path = is PC par file ka pura
                             path - Desktop/Downloads kahi se bhi;
                             file ka naam hi pata ho to pehle
                             find_file se uska path nikalo)
- download_file(url, filename)  internet se koi file (poster,
                             installer adi) download karo - work/
                             folder ya Ankit ke folders me (25 MB
                             tak; filename khali ho to URL se banta
                             hai)
- make_video(job_folder)     job folder (slides/ + titles.txt +
                             optional voice.mp3) se taiyaar vertical
                             video banao - final.mp4 usi folder me
                             banta hai ('video-banana' skill dekho)
- watch_video(source)        YouTube link ya koi video file
                             (poora path bhi chalega) dekh kar uske
                             steps samjho (nayi skill seekhne ke
                             liye; mile hue steps pehle Ankit ko
                             dikhane hain, skill uski haan par hi
                             banegi)
- run_program(command, confirm)  is PC par command/program chalao
                             (software install karne/chalane ke
                             liye; output wapas milta hai).
                             Khatarnak-class command par tool
                             CONFIRM_REQUIRED deta hai (mana nahi) -
                             tab Ankit ko bata kar pucho, uski haan
                             par WAHI command confirm=true ke saath
                             dobara chalao. Aam command me confirm
                             ki zaroorat nahi.
If no tool is needed, reply in plain text only (no JSON)."""

# --------------------------------------------------------------------------
# Tools - file wale tools (v8.4 se seema khuli: PADHNA poore computer
# me, kyunki Ankit ke video/photo Desktop/Downloads me rehte hain;
# LIKHNA work/ folder + Ankit ke apne (home) folders me - system
# wali jagah par likhai band hai, wo PC ke liye khatarnak hai)
# --------------------------------------------------------------------------


def _home_dir() -> Path:
    """User ka home folder (Windows: C:\\Users\\<naam>, yahi se
    Desktop/Downloads/Documents sab aate hain)."""
    return Path(os.path.expanduser("~")).resolve()


def _system_roots() -> list:
    """System wali jagahen - yahan LIKHNA band hai (padhna nahi)."""
    if os.name == "nt":
        drive = os.environ.get("SystemDrive", "C:")
        return [Path(drive + "\\Windows"),
                Path(drive + "\\Program Files"),
                Path(drive + "\\Program Files (x86)"),
                Path(drive + "\\ProgramData")]
    return [Path(p) for p in ("/etc", "/usr", "/bin", "/sbin",
                              "/lib", "/lib64", "/boot", "/proc",
                              "/sys", "/dev", "/root", "/opt")]


def _is_system_path(p: Path) -> bool:
    for root in _system_roots():
        if p == root or root in p.parents:
            return True
    return False


def _safe_path(user_path: str) -> Path:
    """READ ke liye path resolve karo: poora (absolute) path ho to
    wahi - PC par KAHI bhi padhna khula hai; sirf naam/relative ho
    to work/ folder ke andar."""
    raw = (user_path or "").strip().strip('"').strip("'")
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = WORK_DIR / raw
    return p.resolve()


_WRITE_REFUSAL = ("Is jagah par main nahi likhunga: {path} - likhna "
                  "sirf work/ folder aur tumhare apne folders "
                  "(Desktop, Downloads, Documents, poora home "
                  "folder) me hota hai. System wali jagah "
                  "(C:\\Windows, Program Files jaisi) par likhai "
                  "suraksha ke liye band hai - wahan kaam hota "
                  "bhi nahi.")


def _write_path(user_path: str) -> Path:
    """WRITE ke liye path resolve karo: work/ ke andar ya user ke
    home folder ke andar hi chalega; system jagah ya bahar ki
    jagah par ValueError (upar wala tool use saaf jawab me
    badalta hai)."""
    p = _safe_path(user_path)
    home = _home_dir()
    inside = (p == WORK_DIR or WORK_DIR in p.parents
              or p == home or home in p.parents)
    if inside and not _is_system_path(p):
        return p
    raise ValueError(_WRITE_REFUSAL.format(path=p))


def _rel(path: Path) -> str:
    """Dikhane ke liye chhota naam: work/ ke andar ho to relative,
    warna poora path."""
    try:
        return str(path.relative_to(WORK_DIR)) if path != WORK_DIR else "."
    except ValueError:
        return str(path)


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
    try:
        target = _write_path(path)
    except ValueError as exc:
        return str(exc)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Wrote {_rel(target)} ({len(content)} characters)."


def tool_create_folder(path: str) -> str:
    try:
        target = _write_path(path)
    except ValueError as exc:
        return str(exc)
    target.mkdir(parents=True, exist_ok=True)
    return f"Folder ready: {_rel(target)}"


# --------------------------------------------------------------------------
# find_file - naam se poore computer me file/folder dhoondna.
# Sirf user ke home folder ke ped (tree) me dhoondta hai - Desktop,
# Downloads, Documents sab usi ke andar aate hain. Bhaari/system
# folders (AppData adi) skip hote hain, gehrai ~6 tak, ~50k entries
# ya ~20 second ki hadd - taaki hukum latke nahi.
# --------------------------------------------------------------------------

_FIND_SKIP_DIRS = {"appdata", "node_modules", ".git", "$recycle.bin",
                   "system volume information", ".cache",
                   "__pycache__", ".local", ".config"}
_FIND_MAX_DEPTH = 6
_FIND_MAX_ENTRIES = 50000
_FIND_MAX_RESULTS = 50
_FIND_TIME_LIMIT = 20.0


def _fmt_size(n: int) -> str:
    if n >= 1024 * 1024:
        return f"{n / (1024 * 1024):.1f} MB"
    if n >= 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n} bytes"


def tool_find_file(name: str) -> str:
    """Naam (ya uska hissa) se home folder ke ped me file/folder
    dhoondo. Case-insensitive. Matches ke poore path milte hain."""
    name = (name or "").strip().strip('"').strip("'")
    if not name:
        return "Kya dhoondhu - file ya folder ka naam to do."
    needle = name.lower()
    home = _home_dir()
    if not home.is_dir():
        return f"Home folder hi nahi mila: {home}"
    matches = []
    scanned = 0
    stopped = ""
    started = time.time()
    for root, dirs, files in os.walk(home):
        root_path = Path(root)
        try:
            depth = len(root_path.relative_to(home).parts)
        except ValueError:
            depth = 0
        dirs[:] = [d for d in dirs if d.lower() not in _FIND_SKIP_DIRS]
        if depth >= _FIND_MAX_DEPTH:
            dirs[:] = []
        entries = [(d, True) for d in dirs] + [(f, False) for f in files]
        for entry, is_dir in entries:
            scanned += 1
            if needle in entry.lower():
                full = root_path / entry
                if is_dir:
                    matches.append(f"  FOLDER  {full}")
                else:
                    try:
                        size = full.stat().st_size
                    except OSError:
                        size = 0
                    matches.append(f"  FILE    {full} ({_fmt_size(size)})")
                if len(matches) >= _FIND_MAX_RESULTS:
                    stopped = (f" (pehle {_FIND_MAX_RESULTS} matches "
                               "par ruk gaya)")
                    break
            if scanned >= _FIND_MAX_ENTRIES:
                stopped = " (khoj ki hadd par ruk gaya)"
                break
            if scanned % 2000 == 0 and time.time() - started > _FIND_TIME_LIMIT:
                stopped = " (samay ki hadd par ruk gaya)"
                break
        if stopped:
            break
    if not matches:
        return (f"Poore computer me (home folder: {home}) '{name}' "
                "naam ki koi file/folder nahi mili. Naam ki spelling "
                "ek baar check kar lo, ya naam ka koi aur hissa bol "
                "kar dobara dhoondta hu.")
    log(f"FIND_FILE '{name}': {len(matches)} matches, "
        f"{scanned} entries scanned")
    return (f"'{name}' ke liye {len(matches)} jagah mili{stopped}:\n"
            + "\n".join(matches))


# --------------------------------------------------------------------------
# open_file - koi file uske DEFAULT app me kholna (video -> default
# player, photo -> viewer, document -> uska app). Ankit ki spasht
# ummeed (2026-11-20): "jaise bola to usko mere file main ja ke
# video play karna chahiye tha na" - hukum mile to agent folder
# me ja kar video asal me PLAY karke dikhaye, sirf baat na kare.
# --------------------------------------------------------------------------


def tool_open_file(path: str) -> str:
    """File ko OS ke default app me kholo (video play karna,
    photo/document kholna). Absolute path ya work/ wala naam."""
    raw = (path or "").strip().strip('"').strip("'")
    if not raw:
        return "Kaunsi file kholu - uska path to do."
    target = _safe_path(raw)
    if not target.exists():
        return (f"File mili nahi: {raw} - sirf naam pata ho to "
                "pehle find_file se poore computer me uska path "
                "nikalo, phir wahi path do.")
    try:
        system = platform.system()
        if system == "Windows" and hasattr(os, "startfile"):
            os.startfile(str(target))  # noqa: S606 - user ka apna PC, usi ka hukum
        elif system == "Darwin":
            subprocess.Popen(["open", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target)])
    except Exception as exc:
        log(f"OPEN_FILE fail: {target}: {exc}")
        return (f"File kholne me dikkat aayi: {exc}. File yahan "
                f"hai: {target}")
    log(f"OPEN_FILE: {target}")
    return (f"File khol di hai - default app me khul gayi hogi: "
            f"{_rel(target)}")


# --------------------------------------------------------------------------
# extract_zip - .zip kholna. Ankit ke video Google Drive se ZIP
# bankar aate hain (jaise "Dragon Princess Hook Reels-....zip" ke
# andar folder, usme hook-reel-01.mp4) - zip ke andar ki file
# seedha play/upload NAHI hoti, pehle kholna padta hai (Windows
# khud bhi andar double-click par error deta hai). Suraksha:
# zip-slip (../ ya bahar ki entries) destination se bahar nahi
# ja sakti; kul size ~2 GB aur entries ~1000 ki hadd;
# destination hamesha write-bounds (work/ ya home) ke andar.
# --------------------------------------------------------------------------

_EXTRACT_MAX_TOTAL = 2 * 1024 * 1024 * 1024  # ~2 GB
_EXTRACT_MAX_ENTRIES = 1000
_EXTRACT_LIST_CAP = 50


def tool_extract_zip(path: str) -> str:
    """Ek .zip ko uske paas wale naye folder me kholo.

    Destination = zip ke saath wala folder, naam = zip ka naam
    bina '.zip' ke. Nikli files ki list + destination wapas
    milta hai, taaki agla kaam (play/upload) un par ho sake.
    """
    raw = (path or "").strip().strip('"').strip("'")
    if not raw:
        return "Kaunsi zip kholu - uska path to do."
    src = _safe_path(raw)
    if not src.is_file():
        return (f"Zip file mili nahi: {raw} - sirf naam pata ho "
                "to pehle find_file se poore computer me uska "
                "path nikalo, phir wahi path do.")
    if src.suffix.lower() != ".zip":
        return (f"Ye .zip file nahi lagti: {src.name} - main "
                "sirf .zip khol sakta hu.")
    try:
        dest = _write_path(str(src.with_suffix("")))
    except ValueError as exc:
        return str(exc)
    try:
        zf = zipfile.ZipFile(src)
    except zipfile.BadZipFile:
        return (f"Ye zip file kharab lagti hai, khul nahi "
                f"payi: {src.name}")
    with zf:
        all_infos = zf.infolist()
        if len(all_infos) > _EXTRACT_MAX_ENTRIES:
            return (f"Is zip me bahut zyada cheezein hain "
                    f"({len(all_infos)} entries) - kholne ki "
                    f"hadd {_EXTRACT_MAX_ENTRIES} entries hai. "
                    "Itni badi zip main nahi kholunga.")
        infos = [i for i in all_infos if not i.is_dir()]
        total_size = sum(i.file_size for i in infos)
        if total_size > _EXTRACT_MAX_TOTAL:
            return (f"Is zip ke andar kul "
                    f"{total_size / 1073741824:.1f} GB hai - "
                    "kholne ki hadd 2 GB hai. Main ise nahi "
                    "kholunga.")
        dest.mkdir(parents=True, exist_ok=True)
        dest_resolved = dest.resolve()
        extracted = []
        skipped = []
        for info in infos:
            target = (dest / info.filename).resolve()
            if (target != dest_resolved
                    and dest_resolved not in target.parents):
                skipped.append(info.filename)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as fsrc, open(target, "wb") as fdst:
                shutil.copyfileobj(fsrc, fdst, 1024 * 256)
            extracted.append((info.filename, info.file_size))
    log(f"EXTRACT_ZIP: {src} -> {dest} ({len(extracted)} files, "
        f"{len(skipped)} skipped)")
    if not extracted and not skipped:
        return f"Zip kholi, lekin uske andar koi file nahi thi: {dest}"
    lines = [f"Zip khul gayi. Files is folder me nikli hain: {dest}"]
    for name, size in extracted[:_EXTRACT_LIST_CAP]:
        lines.append(f"  FILE  {name} ({_fmt_size(size)})")
    if len(extracted) > _EXTRACT_LIST_CAP:
        lines.append(f"  ... aur {len(extracted) - _EXTRACT_LIST_CAP} "
                     "files (list lambi hai, baaki bhi nikal gayi hain)")
    if skipped:
        lines.append(f"Note: {len(skipped)} entries suraksha ki wajah "
                     "se chhod di gayin (wo folder se bahar ja rahi "
                     "thi).")
    return "\n".join(lines)


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

# --------------------------------------------------------------------------
# Bundled skills bootstrap (v8.4): update channel se sirf agent.py
# aata hai, isliye is release ki nayi seed skills ka poora text neeche
# isi file me bytes ki shakal me rakha hai. Startup par
# ensure_bundled_skills() skills/ folder me jo file NA ho use bana
# deta hai; jo file pehle se maujud hai (Ankit ki apni copy ya edit)
# use KABHI overwrite nahi karta.
# --------------------------------------------------------------------------

BUNDLED_SKILLS = {
    'video-banana.md': b'# Video Banana (poster + awaaz se poori movie video)\n\n## Kab use karein\nJab Ankit kisi movie ki video banane ko kahe \xe2\x80\x94 jaise "is movie ki video banao", "Se7en par ek reel banao". Ye agent ki video factory hai: posters + bade titles + awaaz se taiyaar khadi (vertical, 1080x1920) video banti hai, Facebook Reels / YouTube Shorts ke size ki.\n\n## Steps\n1. Pehle tay karo kaunsi 3 movies ayengi (Ankit ki di hui list, ya uski pasand/trending se khud chuno aur Ankit ko bata do). Ek video me 3 posters (slides) aate hain \xe2\x80\x94 kam se kam 3, zyada se zyada 5.\n2. Har movie ka poster URL nikalo:\n   - Ankit ki apni site ka data: `web_fetch` se https://mindbendmovies.github.io/mindbendmovies-site/data/movies.json kholo, usme movie ka naam dhoondo \xe2\x80\x94 poster ka rasta (poster_path) milega. Poora poster URL banta hai: `https://image.tmdb.org/t/p/w500` + poster_path.\n   - Ya Ankit ne seedha TMDB poster URL diya ho to wahi use karo.\n   - Poster URL sirf inhi sahi sources se lena \xe2\x80\x94 andaz se URL kabhi mat banao.\n3. Job folder banao: `create_folder` se `work/` ke andar, jaise `video_se7en` (topic/movie ke naam par).\n4. Har poster `download_file` se job folder ke `slides/` hisse me rakho \xe2\x80\x94 naam is order me: `slides/slide1.jpg`, `slides/slide2.jpg`, `slides/slide3.jpg` (jo order chahiye wahi number do).\n5. `write_file` se usi job folder me `titles.txt` likho \xe2\x80\x94 har slide ke liye EK line, is shakal me: `MOVIE KA NAAM | hook line`. Hook line chhoti aur curiosity wali ho (ending/twist ki taraf ishara, jhooti baat nahi) \xe2\x80\x94 jaise `SE7EN | The ending will break your brain`.\n6. Awaaz (optional): script likh kar `speak_to_file` se voice file banao aur use job folder me `voice.mp3` (ya `voice.wav`) naam se rakho \xe2\x80\x94 ya Ankit ki di hui taiyaar voice file (jaise Aoede wali) wahi naam se job folder me rakho. Awaaz ki file ho to video uski lambai ke barabar banta hai. Awaaz na ho to video SILENT banegi \xe2\x80\x94 ye baat Ankit ko pehle bata do.\n7. `make_video` chalao job folder par (jaise `make_video("video_se7en")`). Output usi folder me `final.mp4` banta hai.\n8. `video_info` se `final.mp4` verify karo \xe2\x80\x94 duration, size, resolution \xe2\x80\x94 phir Ankit ko final path ke saath report karo. Bina verify kiye "ho gaya" mat bolo.\n9. Upload karna ho to `facebook-upload-direct` / `youtube-upload-direct` skill ka rasta (browser haath) follow karo \xe2\x80\x94 upload/post ka hukum mile to kaam post/publish tak pura karo; rukna sirf tab hai jab Ankit "taiyaar karke dikhao / draft" bole.\n\n## Notes\n- Saari files sirf `work/` ke andar \xe2\x80\x94 posters, titles, voice, output sab wahi.\n- Asli (original) poster/video files kabhi overwrite mat karo \xe2\x80\x94 har video ka apna job folder rakho.\n- Ek slide par ek hi movie \xe2\x80\x94 titles.txt ki line aur slide ka number hamesha match rakho.\n- Badi awaaz file ho to video lamba banta hai; Shorts/Reels ke liye awaaz ~60-90 second ke andar rakho.\n',
    'facebook-upload-direct.md': b'# Facebook Upload \xe2\x80\x94 Direct (Browser Hand)\n\n## Kab use karein\nJab Ankit kahe "is video ko Facebook par upload kar do" aur browser hand (v8.3) setup ho chuka ho. Ye purani guided wali `facebook-post` skill se alag hai \xe2\x80\x94 yahan video lagana, caption bharna aur final Post dabana sab tum khud browser me karte ho. Post wala rule neeche step 10 me hai.\n\n## Pehle ye check karo (preconditions)\n1. `browser setup karo` ho chuka ho aur Ankit agent wale Chrome profile me Facebook me **khud logged-in** ho. Login screen dikhe to wahi ruk jao (neeche dekho).\n2. Video file PC par maujud ho \xe2\x80\x94 uska **poora path** note karo. File jahan bhi ho (Desktop, Downloads, `work/` \xe2\x80\x94 jaise `work/movie1.mp4`) wahi path chalega. Sirf naam pata ho to `find_file` se poore computer me uska path nikalo; phir bhi na mile to Ankit ko bolo \xe2\x80\x94 andaze se koi file mat lagao, aur use file kahin rakhne ko bhi mat bolo.\n\n## Steps\n1. Caption pehle taiyaar karo: dimag se caption + hashtags draft karo \xe2\x80\x94 **English, USA audience** ke liye, MindBendMovies style me. Website ka link caption ke andar mat daalo \xe2\x80\x94 wo pehle comment me jata hai, ye note caption ke saath alag rakho aur aakhir me Ankit ko yaad dilao. Movie videos me movie order shuffled rakho aur aakhir me website par bhejne wali fast line rakho (Ankit ka purana rule). Caption Ankit ko chat me dikha do.\n2. `browser_open` se `https://www.facebook.com` kholo.\n3. `browser_read` karke page dekho aur pakka karo ki Ankit logged-in hai (uska naam/Page dikh raha ho). **Agar login screen dikhe to WAHI RUK JAO** \xe2\x80\x94 Ankit ko bolo ki khuli hui window me khud login karke bata de. Password kabhi mat mango, kabhi mat bharo.\n4. Uske Page par jao: `browser_read` se Page ka naam dhoondo aur `browser_click` (visible text se) karke Page kholo. Page do se zyada hon to Ankit se puch lo ki kis Page par dalna hai.\n5. Post/Reel banane wala hissa kholo: `browser_click` se "Create post" / "Photo/video" / "Reel" wala button dabao (jo kaam bola gaya ho \xe2\x80\x94 video post ya Reel). Dialog khulne ke baad `browser_read` karke pakka karo ki upload wala dialog hi khula hai.\n6. Dialog me file input (`input[type=file]`) dhoondo aur `browser_upload_file` se video ka poora path us par lagao. File-picker khud nahi khulega \xe2\x80\x94 file seedha lag jayegi.\n7. Thoda ruko, phir `browser_read` karke pakka karo ki upload register ho gaya hai \xe2\x80\x94 video ka preview/thumbnail ya file ka naam dialog me dikhna chahiye. Na dikhe to ek baar aur `browser_read` karo; phir bhi na dikhe to Ankit ko batao ki upload nahi laga \xe2\x80\x94 aage mat badho.\n8. Caption wale box me `browser_type` se step 1 wala caption + hashtags bhar do.\n9. `browser_read` karke aakhiri jaanch karo: caption sahi jagah par pura dikh raha hai aur video ka preview maujud hai. Kuch galat dikhe to pehle theek karo, phir aage badho.\n10. **FINAL RULE \xe2\x80\x94 Post wala button:**\n    - Ankit ka hukum ("upload kar do", "post kar do", "daal do", "schedule kar do") **hi uski manjuri hai** \xe2\x80\x94 alag se haan ka intezaar mat karo. Upar ki jaanch puri ho to `browser_click` se Post **KHUD dabao**. Uske baad `browser_read` karke pakka karo ki post publish ho gaya (Page par post dikhe ya "Published" jaisa status mile), tabhi Ankit ko "ho gaya" bolo. Post ke baad pehle comment (website link wala) dalna ho to wo bhi isi flow me kar do.\n    - **SIRF tab ruko** jab Ankit ne khud bola ho "taiyaar karke dikhao", "pehle dikhao" ya "draft banao" \xe2\x80\x94 matlab use pehle dekhna hai. Tab sab taiyaar karke chhodo aur chat me batao ki sab Post ke liye taiyaar hai.\n\n## Dhyaan rahe\n- **CAPTCHA, checkpoint ("confirm it\'s you"), 2FA ya koi bhi security screen dikhe to TURANT ruk jao.** Screen Ankit ke hawale kar do \xe2\x80\x94 khud solve/bypass karne ki koshish kabhi mat karo. Wo screen sambhal le to wahi se aage badho.\n- Koi button/element na mile to pehle `browser_read` karke page ko visible text se padho aur text se dhoondo. Facebook ka layout aksar badalta rehta hai \xe2\x80\x94 yaad ki hui jagah/position par bharosa mat karo, hamesha `browser_read` par bharosa karo.\n- Har step ke baad page dobara padho \xe2\x80\x94 andhere me click mat karo. Jo dikhe wahi sach hai.\n- Sirf Ankit ke apne banaye video upload karo; copyright wala dusre ka video nahi.\n- Kaam human pace par karo \xe2\x80\x94 steps ke beech chhota sa rukna thik hai, jaldi-jaldi spam clicks mat karo.\n',
    'youtube-upload-direct.md': b'# YouTube Upload \xe2\x80\x94 Direct (Browser Hand)\n\n## Kab use karein\nJab Ankit kahe "is video ko YouTube par upload kar do" (movie video, series part, Short) aur browser hand (v8.3) setup ho chuka ho. Ye purani guided wali `youtube-upload` skill se alag hai \xe2\x80\x94 yahan file lagana, title/description bharna aur final Publish dabana sab tum khud YouTube Studio me karte ho. Publish wala rule neeche step 11 me hai.\n\n## Pehle ye check karo (preconditions)\n1. `browser setup karo` ho chuka ho aur Ankit agent wale Chrome profile me YouTube/Google account se **khud logged-in** ho (usi account se jiska channel hai). Login screen dikhe to wahi ruk jao (neeche dekho).\n2. Video file PC par maujud ho \xe2\x80\x94 uska **poora path** note karo. File jahan bhi ho (Desktop, Downloads, `work/`) wahi path chalega. Sirf naam pata ho to `find_file` se poore computer me uska path nikalo; phir bhi na mile to Ankit ko bolo \xe2\x80\x94 andaze se koi file mat lagao, aur use file kahin rakhne ko bhi mat bolo.\n\n## Steps\n1. Title, description aur tags pehle taiyaar karo: SEO wala title (English, USA audience), description me movie ki jaankari + website ka link. Taiyaar matter Ankit ko chat me dikha do.\n2. `browser_open` se `https://studio.youtube.com` kholo.\n3. `browser_read` karke pakka karo ki Studio khula hai aur channel dikh raha hai. **Agar Google login screen dikhe to WAHI RUK JAO** \xe2\x80\x94 Ankit ko bolo ki khuli hui window me khud login karke bata de. Password kabhi mat mango, kabhi mat bharo. Galat channel/account dikhe to Ankit se puch lo.\n4. Upar ke "Create" button par `browser_click` karo, phir "Upload videos" par click karo. Upload wala dialog khulne ke baad `browser_read` karke pakka karo.\n5. Dialog me file input (`input[type=file]`) dhoondo aur `browser_upload_file` se video ka poora path lagao. File-picker khud nahi khulega \xe2\x80\x94 file seedha lag jayegi aur upload shuru ho jayega.\n6. Thoda ruko, phir `browser_read` karke pakka karo ki upload register ho gaya hai \xe2\x80\x94 video ka title/preview aur upload ki progress dikhni chahiye. Na dikhe to ek baar aur `browser_read` karo; phir bhi na dikhe to Ankit ko batao \xe2\x80\x94 aage mat badho.\n7. Details wale step par: title wale box me `browser_type` se step 1 wala title bharo, description wale box me description bhar do.\n8. Audience wale sawal par **"No, it\'s not made for kids"** wala option `browser_click` se chuno \xe2\x80\x94 ye Ankit ke saare videos ke liye standing rule hai.\n9. Baaki steps (Video elements, Checks) par "Next" dabate hue aage badho. Copyright check me koi claim/error dikhe to ruk kar Ankit ko batao \xe2\x80\x94 khud aage mat badho.\n10. Visibility wale step par `browser_read` karke sab jaancho: title, description, audience setting \xe2\x80\x94 sab sahi hai.\n11. **FINAL RULE \xe2\x80\x94 Publish wala button:**\n    - Ankit ka hukum ("upload kar do", "publish kar do", "post kar do", "daal do") **hi uski manjuri hai** \xe2\x80\x94 alag se haan ka intezaar mat karo. Jaanch puri ho to visibility "Public" karke Publish **KHUD dabao**. Agar usne **schedule** bola ho to "Schedule" wala option chun kar uske diye hue USA time ke hisaab se date/time set karo aur Schedule dabao \xe2\x80\x94 ye bhi usi hukum ki manjuri me aata hai. Uske baad `browser_read` karke pakka karo ki video publish/schedule ho gaya, aur video ka link mile to Ankit ko de do / note kar lo.\n    - **SIRF tab ruko** jab Ankit ne khud bola ho "taiyaar karke dikhao", "pehle dikhao" ya "draft banao" \xe2\x80\x94 matlab use pehle dekhna hai. Tab sab taiyaar karke chhodo aur chat me batao ki sab Publish ke liye taiyaar hai (visibility bhi wahi tay karega).\n\n## Dhyaan rahe\n- **CAPTCHA, 2FA, "verify it\'s you" ya koi bhi Google security screen dikhe to TURANT ruk jao.** Screen Ankit ke hawale kar do \xe2\x80\x94 khud solve/bypass karne ki koshish kabhi mat karo. Wo sambhal le to wahi se aage badho.\n- Koi button/element na mile to pehle `browser_read` karke page ko visible text se padho aur text se dhoondo. YouTube Studio ka layout bhi badalta rehta hai \xe2\x80\x94 yaad ki hui jagah par bharosa mat karo, hamesha `browser_read` par bharosa karo.\n- Har step ke baad page dobara padho \xe2\x80\x94 andhere me click mat karo. Upload pura hone me time lage to dhairya rakho, progress `browser_read` se dekhte raho.\n- Sirf Ankit ke apne banaye video upload karo; copyright wala dusre ka video nahi.\n- Shorts ke liye title me `#Shorts` jodna mat bhoolo (agar Ankit ne Short bola ho).\n',
}


def ensure_bundled_skills() -> None:
    """Bundled seed skills ko skills/ folder me bharo (sirf missing wali).

    Har startup par main() ki shuruaat me chalta hai - demo mode aur
    server mode dono isi ek jagah se guzarte hain. Ye kabhi crash nahi
    karta: kuch fail ho to sirf log me note padta hai aur agent aage
    badh jata hai.
    """
    try:
        SKILLS_DIR.mkdir(parents=True, exist_ok=True)
        for fname, content in BUNDLED_SKILLS.items():
            try:
                target = SKILLS_DIR / fname
                if target.exists():
                    continue
                target.write_bytes(content)
                log(f"SKILL BOOTSTRAP: nayi bundled skill banayi: skills/{fname}")
            except Exception as exc:
                log(f"SKILL BOOTSTRAP: skills/{fname} nahi ban payi: {exc}")
    except Exception as exc:
        try:
            log(f"SKILL BOOTSTRAP fail (ignore kiya gaya): {exc}")
        except Exception:
            pass


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
    try:
        dst = _write_path(output)
    except ValueError as exc:
        return str(exc)
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
    try:
        dst = _write_path(output or "joined.mp4")
    except ValueError as exc:
        return str(exc)
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
# Download tool (v8.4) - internet se file (poster adi) work/ me lana
# --------------------------------------------------------------------------

DOWNLOAD_MAX_BYTES = 25 * 1024 * 1024  # 25 MB ki hadd


def tool_download_file(url: str, filename: str = "") -> str:
    """Ek file internet se download karke work/ me rakho.

    Sirf http/https; 25 MB se badi file beech me rok di jati hai.
    filename na diya jaye to URL ke aakhri hisse se banta hai.
    File work/ folder me aati hai (filename me poora path do to
    Ankit ke folders me bhi ja sakti hai; system jagah band hai).
    """
    url = (url or "").strip()
    if not re.match(r"^https?://", url):
        return "Sirf http/https wala link download kar sakta hu - sahi URL do."
    if not (filename or "").strip():
        filename = unquote(url.split("?")[0].rstrip("/").rsplit("/", 1)[-1])
        if not filename:
            filename = "download.bin"
    try:
        dst = _write_path(filename)
    except ValueError as exc:
        return str(exc)
    dst.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "MyAgent/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
            data = resp.read(DOWNLOAD_MAX_BYTES + 1)
    except Exception as exc:
        return f"Download nahi ho paya: {exc}"
    if len(data) > DOWNLOAD_MAX_BYTES:
        return ("File bahut badi hai (25 MB se zyada) - download rok "
                "diya. Chhoti file ka link do.")
    dst.write_bytes(data)
    return (f"Download ho gaya: {_rel(dst)} "
            f"({len(data)} bytes) - {url}")


# --------------------------------------------------------------------------
# Video factory (v8.4) - job folder se taiyaar vertical video.
# Ye video_factory/make_video.py ka PROVEN logic hai (wahan asal
# sample par test ho chuka hai: 9.00s, 1080x1920), yahan tool ki
# shakal me merge kiya gaya hai. Standalone script apni jagah
# untouched hai. Job folder work/ ke andar: slides/ me posters,
# titles.txt (har line: NAAM | hook line), optional voice.mp3.
# --------------------------------------------------------------------------

_MV_WIDTH, _MV_HEIGHT = 1080, 1920
_MV_FPS = 30
_MV_ZOOM_END = 1.12  # har slide par slow zoom 1.00 -> 1.12
_MV_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansBold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\verdanab.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
]
_MV_IMAGE_EXTS = (".jpg", ".jpeg", ".png")
_MV_VOICE_NAMES = ("voice.mp3", "voice.wav", "voice.m4a", "voice.ogg")


def _mv_run(cmd: list):
    """ffmpeg/ffprobe chalao; fail ho to stderr ke saath error uthao."""
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          timeout=1200)
    if proc.returncode != 0:
        raise RuntimeError(
            "Command fail: %s\n%s" % (
                " ".join(str(c) for c in cmd), (proc.stderr or "")[-1500:]))
    return proc


def _mv_probe_duration(path):
    try:
        out = _mv_run(["ffprobe", "-v", "error", "-show_entries",
                       "format=duration", "-of", "json",
                       str(path)]).stdout
        return float(json.loads(out)["format"]["duration"])
    except Exception:
        return None


def _mv_probe_video(path):
    """(width, height, duration) - output ki asal jaanch ke liye."""
    out = _mv_run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                   "-show_entries", "stream=width,height",
                   "-show_entries", "format=duration",
                   "-of", "json", str(path)]).stdout
    info = json.loads(out)
    stream = info["streams"][0]
    return (int(stream["width"]), int(stream["height"]),
            float(info["format"]["duration"]))


def _mv_find_font():
    for cand in _MV_FONT_CANDIDATES:
        if os.path.isfile(cand):
            return cand
    fc = shutil.which("fc-list")
    if fc:
        try:
            out = _mv_run([fc, ":family=DejaVu Sans:style=Bold",
                           "file"]).stdout
            path = out.split(":")[0].strip()
            if path and os.path.isfile(path):
                return path
        except Exception:
            pass
    return None


def _mv_find_slides(job: Path):
    """Posters: pehle job/slides/, warna job/ root. Naam ke order me."""
    for folder in (job / "slides", job):
        if folder.is_dir():
            files = sorted(
                (f for f in folder.iterdir()
                 if f.is_file() and f.suffix.lower() in _MV_IMAGE_EXTS),
                key=lambda p: p.name.lower())
            if files:
                return files
    return []


def _mv_read_titles(job: Path, count: int):
    """titles.txt -> [(title, hook), ...], count tak pad karke."""
    lines = []
    tpath = job / "titles.txt"
    if tpath.is_file():
        lines = [ln.strip() for ln in
                 tpath.read_text(encoding="utf-8",
                                 errors="replace").splitlines()
                 if ln.strip()]
    titles = []
    for i in range(count):
        title, hook = "", ""
        if i < len(lines):
            parts = lines[i].split("|", 1)
            title = parts[0].strip()
            hook = parts[1].strip() if len(parts) > 1 else ""
        titles.append((title, hook))
    return titles


def _mv_escape_filter_path(path) -> str:
    p = str(path).replace("\\", "/")
    return p.replace(":", "\\:").replace("'", "\\'")


def _mv_build_segment(img, title, hook, seconds, font, workdir: Path,
                      index: int):
    """Ek slide (zoom + jala hua text) ka video-only segment banao."""
    frames = max(1, int(round(seconds * _MV_FPS)))
    vf = (
        "scale=2160:3840:force_original_aspect_ratio=increase,"
        "crop=2160:3840,"
        "zoompan=z='1+({zend}-1)*on/{last}':x='iw/2-(iw/zoom/2)'"
        ":y='ih/2-(ih/zoom/2)':d={frames}:s={w}x{h}:fps={fps}"
    ).format(zend=_MV_ZOOM_END, last=max(frames - 1, 1), frames=frames,
             w=_MV_WIDTH, h=_MV_HEIGHT, fps=_MV_FPS)
    filters = [vf]
    if font and (title or hook):
        if title:
            wrapped = "\n".join(textwrap.wrap(title, width=18) or [title])
            tfile = workdir / f"title_{index}.txt"
            tfile.write_text(wrapped, encoding="utf-8")
            lines = wrapped.count("\n") + 1
            y = _MV_HEIGHT - 330 - (lines - 1) * 86
            filters.append(
                "drawtext=fontfile='{font}':textfile='{tf}':expansion=none"
                ":fontsize=76:fontcolor=white:borderw=3:bordercolor=black"
                ":box=1:boxcolor=black@0.55:boxborderw=22:line_spacing=10"
                ":x=(w-text_w)/2:y={y}".format(
                    font=_mv_escape_filter_path(font),
                    tf=_mv_escape_filter_path(tfile), y=y))
        if hook:
            wrapped = "\n".join(textwrap.wrap(hook, width=30) or [hook])
            hfile = workdir / f"hook_{index}.txt"
            hfile.write_text(wrapped, encoding="utf-8")
            filters.append(
                "drawtext=fontfile='{font}':textfile='{tf}':expansion=none"
                ":fontsize=46:fontcolor=0xFFD54A:borderw=2:bordercolor=black"
                ":box=1:boxcolor=black@0.55:boxborderw=16:line_spacing=8"
                ":x=(w-text_w)/2:y={y}".format(
                    font=_mv_escape_filter_path(font),
                    tf=_mv_escape_filter_path(hfile), y=_MV_HEIGHT - 215))
    seg = workdir / f"seg_{index}.mp4"
    _mv_run(["ffmpeg", "-y", "-v", "error", "-i", str(img),
             "-vf", ",".join(filters),
             "-frames:v", str(frames),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
             "-pix_fmt", "yuv420p", "-r", str(_MV_FPS), str(seg)])
    return seg


def tool_make_video(job_folder: str, secs: float = 3) -> str:
    """Job folder se taiyaar vertical movie video banao.

    Job folder (work/ ya Ankit ke folders me): slides/ me 3-5
    posters, titles.txt (har line: MOVIE NAAM | hook line),
    optional voice.mp3/wav/m4a/ogg. Output usi folder me
    final.mp4. Awaaz ho to video uski lambai ke barabar banta
    hai; na ho to silent track lagta hai.
    """
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        return _ffmpeg_missing_msg()
    try:
        job = _write_path(job_folder)
    except ValueError as exc:
        return str(exc)
    if not job.is_dir():
        return (f"Job folder mila nahi: {job_folder} - pehle "
                "create_folder se banao aur usme slides/ + titles.txt "
                "rakho ('video-banana' skill dekho).")
    slides = _mv_find_slides(job)
    if not slides:
        return (f"{_rel(job)} me koi poster nahi mila - slides/ folder "
                "me .jpg/.png posters rakho (3-5), phir dobara chalao.")
    try:
        secs = float(secs)
    except (TypeError, ValueError):
        secs = 3.0
    if secs <= 0:
        secs = 3.0
    titles = _mv_read_titles(job, len(slides))
    voice = None
    for name in _MV_VOICE_NAMES:
        cand = job / name
        if cand.is_file():
            voice = cand
            break
    voice_dur = _mv_probe_duration(voice) if voice else None
    base_total = len(slides) * secs
    durations = [secs] * len(slides)
    target_total = base_total
    if voice and voice_dur:
        target_total = voice_dur
        if voice_dur > base_total:
            durations[-1] += voice_dur - base_total  # aakhri slide lambi
    font = _mv_find_font()
    notes = []
    if not font and any(t or h for t, h in titles):
        notes.append("font nahi mila, isliye posters par text nahi jala")
    tmp = Path(tempfile.mkdtemp(prefix="myagent_video_"))
    try:
        segments = []
        for i, img in enumerate(slides):
            title, hook = titles[i]
            segments.append(_mv_build_segment(
                img, title, hook, durations[i], font, tmp, i))
        listfile = tmp / "concat.txt"
        with open(listfile, "w", encoding="utf-8") as fh:
            for seg in segments:
                fh.write("file '%s'\n" % str(seg).replace("'", "'\\''"))
        joined = tmp / "joined.mp4"
        _mv_run(["ffmpeg", "-y", "-v", "error", "-f", "concat",
                 "-safe", "0", "-i", str(listfile), "-c", "copy",
                 str(joined)])
        out = job / "final.mp4"
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(joined)]
        if voice:
            cmd += ["-i", str(voice)]
        else:
            cmd += ["-f", "lavfi", "-i",
                    "anullsrc=channel_layout=stereo:sample_rate=44100"]
        cmd += ["-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                "-pix_fmt", "yuv420p", "-r", str(_MV_FPS),
                "-c:a", "aac", "-b:a", "128k",
                "-t", "%.3f" % target_total,
                "-movflags", "+faststart", str(out)]
        _mv_run(cmd)
    except Exception as exc:
        return f"Video nahi ban paya: {str(exc)[-600:]}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    try:
        w, h, dur = _mv_probe_video(out)
    except Exception as exc:
        return f"Video bana to, lekin uski jaanch nahi ho payi: {exc}"
    size_mb = out.stat().st_size / (1024 * 1024)
    audio_note = (f"awaaz: {voice.name} (voiceover file)"
                  if voice else
                  "awaaz: SILENT track (job folder me koi voice file "
                  "nahi mili - voice chahiye to voice.mp3 naam se "
                  "wahan rakho)")
    extra = (" Dhyaan: " + "; ".join(notes) + ".") if notes else ""
    return (f"Video ban gaya: {_rel(out)} - {dur:.1f} seconds, "
            f"{w}x{h}, {size_mb:.2f} MB, {len(slides)} posters. "
            f"{audio_note}.{extra}")


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
    try:
        dst = _write_path(filename)
    except ValueError as exc:
        return str(exc)
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
# Video dekh kar seekhna (v8.4) - Gemini ki video-understanding.
# Request ki shakal Google ke official docs se verify ki gayi hai
# (2026-11-20): generateContent ke contents[].parts[] me video ke
# liye {"file_data": {"file_uri": "<YouTube URL>"}} (YouTube) ya
# {"inline_data": {"mime_type": "video/...", "data": "<base64>"}}
# (chhoti file) ke saath ek {"text": ...} prompt part jata hai.
# Free-tier hadd (docs): YouTube sirf PUBLIC videos, roz 8 ghante
# tak ka YouTube video; video ki lambai ~45 min (awaaz ke saath) /
# ~1 ghanta (bina awaaz) tak; inline file ke liye yahan 20 MB ki
# surakshit hadd rakhi hai (badi file = pehle trim, ya YouTube
# link). LIVE test user ke PC par hoga (is VM par asli key nahi
# hai) - yahan sirf request ki shakal fake se verify hui hai.
# --------------------------------------------------------------------------

_WATCH_VIDEO_PROMPT = (
    "Is video ko dhyaan se dekho. Isme jo kaam ya skill sikhaya/"
    "kiya gaya hai, use aise step-by-step samjhao ki ek agent unhi "
    "steps ko follow karke wahi kaam dobara kar sake. Jawab "
    "Hinglish (Roman Hindi + English mix) me do, is format me:\n"
    "VIDEO KA KAAM: <ek line - ye video kis kaam ke baare me hai>\n"
    "STEPS:\n1. <pehla step>\n2. <dusra step>\n"
    "KHAAS BAATEIN: <kaunse tools/software/settings lage, login ya "
    "dhyaan dene wali baatein>")

_WATCH_INLINE_MAX = 20 * 1024 * 1024  # inline video ki surakshit hadd
_VIDEO_MIME = {
    ".mp4": "video/mp4",
    ".mpeg": "video/mpeg",
    ".mpg": "video/mpeg",
    ".mov": "video/quicktime",
    ".webm": "video/webm",
    ".wmv": "video/wmv",
    ".flv": "video/x-flv",
    ".3gp": "video/3gpp",
    ".avi": "video/x-msvideo",
}


def _gemini_video_call(parts: list) -> str:
    """Video wale parts ke saath ek seedha Gemini call.

    Chat wale _gemini_call se alag: yahan na system prompt jata
    hai na history - sirf video + seekhne wala prompt. Timeout
    lamba (300s) kyunki video samajhne me samay lagta hai. Galti
    par exception upar jata hai, tool use saaf shabdon me badalta
    hai.
    """
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}")
    body = {"contents": [{"role": "user", "parts": parts}]}
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:  # noqa: S310
        data = json.loads(resp.read().decode("utf-8"))
    out_parts = data["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in out_parts).strip()


def tool_watch_video(source: str) -> str:
    """Ek video DEKH kar uske steps samjho (nayi skill seekhne ko).

    source = YouTube ka link (public video) ya work/ folder ki
    video file (20 MB tak, inline bheji jati hai). Mile hue steps
    wapas milte hain - skill banana hai ya nahi, ye faisla chat me
    Ankit ki haan ke baad create_skill se hota hai (prompt rule).
    """
    source = (source or "").strip().strip('"').strip("'")
    if not source:
        return ("Kaunsi video dekhu - YouTube ka link do, ya video "
                "file ka naam/path do (naam hi ho to find_file se "
                "dhoond lunga).")
    if not GEMINI_API_KEY:
        return ("Video dekhne ke liye Gemini ki key chahiye, lekin "
                "config.env me GEMINI_API_KEY mili nahi. Key daal "
                "kar phir bolo - main video dekh kar uske steps "
                "samjha dunga.")
    if re.match(r"^https?://", source):
        if "youtube.com" not in source and "youtu.be" not in source:
            return ("Link wali video me abhi main sirf YouTube ki "
                    "video dekh sakta hu. Ye link YouTube ka nahi "
                    "lagta - video file ka path do (ya naam, main "
                    "find_file se dhoond lunga), main wahan se dekh "
                    "lunga.")
        parts = [{"file_data": {"file_uri": source}},
                 {"text": _WATCH_VIDEO_PROMPT}]
        kind = "YouTube video"
    else:
        target = _safe_path(source)
        if not target.is_file():
            return (f"Video file mili nahi: {source} - sirf naam "
                    "pata ho to pehle find_file se poore computer "
                    "me uska path nikalo, phir wahi path do.")
        size = target.stat().st_size
        if size > _WATCH_INLINE_MAX:
            return (f"Ye video file bahut badi hai "
                    f"({size / 1048576:.1f} MB) - seedhe bhej kar "
                    "dekhne ki hadd 20 MB hai. Pehle trim_video se "
                    "uska kaam wala hissa kaat kar do, ya video ko "
                    "YouTube par daal kar link do.")
        mime = _VIDEO_MIME.get(target.suffix.lower(), "video/mp4")
        b64 = base64.b64encode(target.read_bytes()).decode("ascii")
        parts = [{"inline_data": {"mime_type": mime, "data": b64}},
                 {"text": _WATCH_VIDEO_PROMPT}]
        kind = f"Video file {_rel(target)}"
    try:
        text = _gemini_video_call(parts)
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", "replace")[:300]
        except Exception:
            pass
        log(f"WATCH_VIDEO fail: HTTP {exc.code}")
        return (f"Video dekh nahi paya - Gemini ne HTTP {exc.code} "
                "diya. Video public hai aur format sahi hai, ye "
                "check karo; thodi der baad phir try karo."
                + (f" ({detail})" if detail else ""))
    except Exception as exc:
        log(f"WATCH_VIDEO fail: {exc}")
        return (f"Video dekh nahi paya: {exc}. Internet check "
                "karke phir try karo.")
    if not text:
        return ("Video bheja to tha, lekin Gemini se koi jawab "
                "nahi aaya - ek baar phir try karo.")
    if len(text) > 12000:
        text = text[:12000] + "\n... (jawab aur lamba tha, kata gaya)"
    return f"{kind} dekh li. Jo samjha, wo ye raha:\n\n{text}"


# --------------------------------------------------------------------------
# Photo dekhna (v8.4) - PC par padi photo/screenshot ko Gemini
# vision se dekhna. Chat me bheji photo ka rasta alag hai (wo
# _vision_describe se vivaran bankar brain loop me jata hai -
# v8.5 ka vision->tools bridge); ye tool file wali photo ke
# liye hai. Request ki shakal watch_video wali hi hai:
# contents[].parts[] me {"inline_data": {"mime_type": "image/...",
# "data": "<base64>"}} + ek text prompt.
# --------------------------------------------------------------------------

_IMAGE_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}
_SEE_IMAGE_MAX = 10 * 1024 * 1024  # 10 MB ki hadd
_VISION_MIMES = ("image/jpeg", "image/png", "image/webp", "image/gif")

_SEE_IMAGE_PROMPT = (
    "Is photo ko dhyaan se dekho. Isme jo hai use Hinglish "
    "(Roman Hindi + English mix) me saaf samjhao: koi screen/"
    "error hai to uska matlab aur wajah, koi text hai to use "
    "padh kar batao, aur Ankit ke kaam ke hisaab se koi khaas "
    "baat dikhe to wo bhi. Jawab seedha aur kaam ka ho.")


def tool_see_image(path: str) -> str:
    """PC par padi ek photo/screenshot ko DEKH kar samjho.

    path = photo ka poora path (Desktop adi kahi se bhi) ya
    work/ ke hisaab se naam. jpg/jpeg/png/webp/gif, 10 MB tak.
    """
    raw = (path or "").strip().strip('"').strip("'")
    if not raw:
        return "Kaunsi photo dekhu - uska path to do."
    if not GEMINI_API_KEY:
        return ("Photo dekhne ke liye Gemini ki key chahiye, lekin "
                "config.env me GEMINI_API_KEY mili nahi. Key daal "
                "kar phir bolo - main photo dekh kar bata dunga "
                "usme kya hai.")
    target = _safe_path(raw)
    if not target.is_file():
        return (f"Photo mili nahi: {raw} - sirf naam pata ho to "
                "pehle find_file se poore computer me uska path "
                "nikalo, phir wahi path do.")
    mime = _IMAGE_MIME.get(target.suffix.lower())
    if not mime:
        return (f"Ye file photo nahi lagti ({target.suffix or '?'}). "
                "Main jpg, png, webp aur gif photo dekh sakta hu.")
    size = target.stat().st_size
    if size > _SEE_IMAGE_MAX:
        return (f"Ye photo bahut badi hai ({size / 1048576:.1f} MB) - "
                "dekhne ki hadd 10 MB hai. Chhoti photo do.")
    b64 = base64.b64encode(target.read_bytes()).decode("ascii")
    parts = [{"inline_data": {"mime_type": mime, "data": b64}},
             {"text": _SEE_IMAGE_PROMPT}]
    try:
        text = _gemini_video_call(parts)
    except urllib.error.HTTPError as exc:
        log(f"SEE_IMAGE fail: HTTP {exc.code}")
        return (f"Photo dekh nahi paya - Gemini ne HTTP {exc.code} "
                "diya. Thodi der baad phir try karo.")
    except Exception as exc:
        log(f"SEE_IMAGE fail: {exc}")
        return (f"Photo dekh nahi paya: {exc}. Internet check "
                "karke phir try karo.")
    if not text:
        return ("Photo bheja to tha, lekin Gemini se koi jawab "
                "nahi aaya - ek baar phir try karo.")
    if len(text) > 12000:
        text = text[:12000] + "\n... (jawab aur lamba tha, kata gaya)"
    log(f"SEE_IMAGE ok: {_rel(target)}")
    return f"Photo ({target.name}) dekh li. Jo dikha, wo ye raha:\n\n{text}"


# --------------------------------------------------------------------------
# Program chalana (v8.4) - user ke kahe par PC par command chalana
# (software install karna / chalana). Har command logs/agent.log me
# likhi jati hai. Neeche wali khatarnak-class list ek SEATBELT hai -
# disk format, system-root delete, shutdown jaisi cheezon par tool
# MANA NAHI karta, pehle CONFIRM mangta hai (confirm-first): bina
# confirm ke command chalti hi nahi, CONFIRM_REQUIRED wapas jata
# hai; user ki haan par brain wahi command confirm=true ke saath
# dobara chalata hai aur wo chal jati hai. Ye koi pakki suraksha
# deewar/sandbox NAHI hai. Paisa kharch ya user ki files delete
# karne wale kaam par pehle puchne ka rule system prompt me hai.
# --------------------------------------------------------------------------

RUN_PROGRAM_TIMEOUT = 120  # second; isse lambi command rok di jati hai

_RUN_DENYLIST = [
    (re.compile(r"\bformat\s+[a-z]:", re.IGNORECASE),
     "poora disk format ho sakta hai"),
    (re.compile(r"\bdiskpart\b|\bmkfs\b|\bfdisk\b", re.IGNORECASE),
     "disk ke partition badal sakte hain"),
    (re.compile(r"\bdd\b[^|;&\n]*\bof=/dev/(sd|hd|nvme)", re.IGNORECASE),
     "seedha disk par likha ja sakta hai"),
    (re.compile(r"\brm\s+-[a-z]*r[a-z]*\s+/\*?\s*$", re.IGNORECASE),
     "poora system root delete ho sakta hai"),
    (re.compile(r"\brm\s+-[a-z]*r[a-z]*\s+/\s", re.IGNORECASE),
     "system root ke andar delete ho sakta hai"),
    (re.compile(r"(del|erase|rd|rmdir|rm)\b[^|;&\n]*"
                r"([a-z]:\\(windows|program files)|system32)",
                re.IGNORECASE),
     "Windows/system folder delete ho sakta hai"),
    (re.compile(r"\bshutdown\b|\brestart-computer\b|"
                r"\bstop-computer\b", re.IGNORECASE),
     "PC band/restart ho jayega"),
]


def _destructive_reason(command: str):
    """Command khatarnak-class ki ho to uski wajah, warna None."""
    for pattern, wajah in _RUN_DENYLIST:
        if pattern.search(command):
            return wajah
    return None


def tool_run_program(command: str, confirm=False) -> str:
    """User ke kahe par is PC par ek command/program chalao.

    Output (stdout+stderr) 8000 characters tak wapas milta hai;
    120 second se lambi command rok di jati hai. Khatarnak-class
    command (disk format, system delete, shutdown jaisi) bina
    confirm ke NAHI chalti - CONFIRM_REQUIRED wapas jata hai
    (ye mana nahi, poochna hai); user ki haan par brain wahi
    command confirm=true ke saath dobara chalata hai. Aam
    command par confirm ka koi asar nahi.
    """
    cmd = (command or "").strip()
    if not cmd:
        return "Kaunsa program ya command chalau - wo to likho."
    wajah = _destructive_reason(cmd)
    if wajah and not confirm:
        log(f"RUN_PROGRAM confirm manga ({wajah}): {cmd[:200]}")
        return ("CONFIRM_REQUIRED: Ye command khatarnak class ki "
                "hai - isse " + wajah + ". Maine ye command abhi "
                "NAHI chalayi. Ankit ko chat me saaf shabdon me "
                "batao ki ye command asal me kya karegi aur pucho "
                "ki chala du ya nahi. Agar Ankit HAAN bol de to "
                "WAHI command run_program me confirm=true ke "
                "saath dobara chalao - mana mat karo, uski haan "
                "hi kaafi hai. (Aam install/program wale kaam "
                "bina confirm ke chalte rahenge.)")
    if wajah:
        log(f"RUN_PROGRAM confirmed chal raha hai ({wajah}): "
            f"{cmd[:300]}")
    else:
        log(f"RUN_PROGRAM chal raha hai: {cmd[:300]}")
    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True,
                              text=True, errors="replace",
                              timeout=RUN_PROGRAM_TIMEOUT)
    except subprocess.TimeoutExpired:
        log(f"RUN_PROGRAM timeout ({RUN_PROGRAM_TIMEOUT}s): {cmd[:200]}")
        return (f"Command {RUN_PROGRAM_TIMEOUT} second me pura "
                "nahi hua - use rok diya hai. Lamba chalne wala "
                "kaam (bada download/install) ho to batao, use "
                "hisson me karenge.")
    except Exception as exc:
        return f"Command chal hi nahi paya: {exc}"
    out = ((proc.stdout or "") + (proc.stderr or "")).strip()
    if len(out) > 8000:
        out = out[:8000] + "\n... (output aur lamba tha, kata gaya)"
    if not out:
        out = "(koi output nahi aaya)"
    log(f"RUN_PROGRAM khatm (exit {proc.returncode}): {cmd[:120]}")
    return f"Command chala diya (exit code {proc.returncode}):\n{out}"


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
# Browser haath (v8.3) - agent apna khaas Chrome KHUD chalata hai.
#
# Mechanism: Chrome DevTools Protocol (CDP). Chrome ek DEDICATED
# profile (agent_chrome_profile/, is file ke bilkul paas) ke saath
# --remote-debugging-port=9222 par chalta hai; agent localhost par
# WebSocket se usse baat karta hai. User us Chrome me EK BAAR khud
# login karta hai - password agent kabhi nahi mangta, dekhta ya
# store karta. Chrome 136+ remote debugging ko default profile par
# chalne hi nahi deta, isliye alag profile sirf suraksha nahi,
# zaroorat bhi hai. Poora plan: BROWSER_PLAN.md.
#
# Neeche pehle CDP client hai - browser_hand/cdp_client.py se
# SHABDASHAH (verbatim) copy, do marker lines ke beech band. Wahi
# code browser_hand/demo.py ke 7/7 live test se proven hai; yahan
# use dobara NAHI likha gaya, taaki merge me uska vyavhaar ek inch
# bhi na badle. (File-level imports - base64, hashlib, struct,
# socket, json, os, urllib.request - dono me common hain.)
# --------------------------------------------------------------------------

# ===== CDP CLIENT: verbatim copy of browser_hand/cdp_client.py =====
WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

OP_CONT, OP_TEXT, OP_BIN, OP_CLOSE, OP_PING, OP_PONG = 0x0, 0x1, 0x2, 0x8, 0x9, 0xA


class WebSocketError(Exception):
    pass


class WebSocket:
    """Blocking WebSocket client for ws:// URLs (no TLS)."""

    def __init__(self, url, timeout=15.0):
        self.url = url
        self.timeout = timeout
        self._buf = bytearray()
        self._frag = bytearray()
        self._frag_opcode = None
        self.sock = None
        self._connect(url)

    # ---- handshake -----------------------------------------------------
    def _connect(self, url):
        if not url.startswith("ws://"):
            raise WebSocketError("only ws:// supported (CDP is localhost): %r" % url)
        rest = url[5:]
        if "/" in rest:
            hostport, path = rest.split("/", 1)
            path = "/" + path
        else:
            hostport, path = rest, "/"
        if ":" in hostport:
            host, port = hostport.rsplit(":", 1)
            port = int(port)
        else:
            host, port = hostport, 80

        self.sock = socket.create_connection((host, port), timeout=self.timeout)
        self.sock.settimeout(self.timeout)

        key = base64.b64encode(os.urandom(16)).decode("ascii")
        req = (
            "GET %s HTTP/1.1\r\n"
            "Host: %s\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            "Sec-WebSocket-Key: %s\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n" % (path, hostport, key)
        )
        self.sock.sendall(req.encode("ascii"))

        # Read headers (byte-by-byte into buffer until \r\n\r\n).
        while b"\r\n\r\n" not in self._buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise WebSocketError("connection closed during handshake")
            self._buf.extend(chunk)
        head, _, restbuf = bytes(self._buf).partition(b"\r\n\r\n")
        self._buf = bytearray(restbuf)

        status_line = head.split(b"\r\n", 1)[0].decode("latin-1")
        if " 101" not in status_line:
            raise WebSocketError("handshake refused: %s" % status_line)
        expect = base64.b64encode(
            hashlib.sha1((key + WS_GUID).encode("ascii")).digest()
        ).decode("ascii")
        if expect.encode() not in head:
            raise WebSocketError("bad Sec-WebSocket-Accept in handshake")

    # ---- frame io ------------------------------------------------------
    def _read_exact(self, n):
        while len(self._buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise WebSocketError("connection closed by peer")
            self._buf.extend(chunk)
        out = bytes(self._buf[:n])
        del self._buf[:n]
        return out

    def _send_frame(self, opcode, payload):
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        mask = os.urandom(4)
        header = bytearray([0x80 | opcode])
        ln = len(payload)
        if ln < 126:
            header.append(0x80 | ln)
        elif ln < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack(">H", ln))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack(">Q", ln))
        header.extend(mask)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(bytes(header) + masked)

    def send_text(self, text):
        self._send_frame(OP_TEXT, text)

    def recv_message(self):
        """Return the next complete text/binary message as str, or None on close."""
        while True:
            b0, b1 = self._read_exact(2)
            fin = bool(b0 & 0x80)
            opcode = b0 & 0x0F
            masked = bool(b1 & 0x80)
            ln = b1 & 0x7F
            if ln == 126:
                ln = struct.unpack(">H", self._read_exact(2))[0]
            elif ln == 127:
                ln = struct.unpack(">Q", self._read_exact(8))[0]
            mask = self._read_exact(4) if masked else None
            payload = self._read_exact(ln) if ln else b""
            if mask:
                payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))

            if opcode == OP_PING:
                self._send_frame(OP_PONG, payload)
                continue
            if opcode == OP_PONG:
                continue
            if opcode == OP_CLOSE:
                try:
                    self._send_frame(OP_CLOSE, b"")
                except Exception:
                    pass
                return None
            if opcode in (OP_TEXT, OP_BIN, OP_CONT):
                if opcode != OP_CONT:
                    self._frag = bytearray(payload)
                    self._frag_opcode = opcode
                else:
                    self._frag.extend(payload)
                if fin:
                    data = bytes(self._frag)
                    self._frag = bytearray()
                    return data.decode("utf-8", errors="replace")
                continue
            # Unknown opcode: ignore frame.

    def close(self):
        try:
            self._send_frame(OP_CLOSE, b"")
        except Exception:
            pass
        try:
            self.sock.close()
        except Exception:
            pass


class CDPError(Exception):
    def __init__(self, method, error):
        super().__init__("CDP %s failed: %s" % (method, error))
        self.method = method
        self.error = error


def http_json(port, path, host="127.0.0.1", timeout=5.0):
    with urllib.request.urlopen(
        "http://%s:%d%s" % (host, port, path), timeout=timeout
    ) as resp:
        return json.loads(resp.read().decode("utf-8"))


class CDPClient:
    """Synchronous CDP client over the browser-level WebSocket, using
    flattened target sessions (Target.attachToTarget with flatten=True)."""

    def __init__(self, port=9222, host="127.0.0.1", timeout=20.0):
        version = http_json(port, "/json/version", host=host)
        ws_url = version["webSocketDebuggerUrl"]
        self.ws = WebSocket(ws_url, timeout=timeout)
        self.timeout = timeout
        self._next_id = 0
        self.events = []  # buffered (method, session_id, params)

    def call(self, method, params=None, session_id=None, timeout=None):
        self._next_id += 1
        mid = self._next_id
        msg = {"id": mid, "method": method, "params": params or {}}
        if session_id:
            msg["sessionId"] = session_id
        self.ws.send_text(json.dumps(msg))
        while True:
            raw = self.ws.recv_message()
            if raw is None:
                raise CDPError(method, "websocket closed")
            data = json.loads(raw)
            if data.get("id") == mid:
                if "error" in data:
                    raise CDPError(method, data["error"])
                return data.get("result", {})
            if "method" in data:
                self.events.append(
                    (data["method"], data.get("sessionId"), data.get("params", {}))
                )

    def wait_event(self, method, session_id=None, timeout=10.0):
        """Return params of the next matching event (checks buffered ones first)."""
        import time

        deadline = time.time() + timeout
        while True:
            for i, (m, sid, params) in enumerate(self.events):
                if m == method and (session_id is None or sid == session_id):
                    del self.events[i]
                    return params
            if time.time() > deadline:
                raise TimeoutError("timed out waiting for %s" % method)
            # Pump the socket briefly by issuing a zero-cost read cycle:
            self.ws.sock.settimeout(min(0.5, max(0.05, deadline - time.time())))
            try:
                raw = self.ws.recv_message()
            except socket.timeout:
                continue
            finally:
                self.ws.sock.settimeout(self.timeout)
            if raw is None:
                raise CDPError(method, "websocket closed while waiting")
            data = json.loads(raw)
            if "method" in data:
                self.events.append(
                    (data["method"], data.get("sessionId"), data.get("params", {}))
                )
            elif "id" in data:
                # A response with no waiter (shouldn't happen in sync use);
                # drop it rather than deadlock.
                pass

    # ---- high-level helpers -------------------------------------------
    def new_page(self, url="about:blank"):
        """Create a tab and attach to it. Returns session_id."""
        target = self.call("Target.createTarget", {"url": url})
        attached = self.call(
            "Target.attachToTarget",
            {"targetId": target["targetId"], "flatten": True},
        )
        return attached["sessionId"]

    def evaluate(self, session_id, expression, timeout=None):
        """Runtime.evaluate with returnByValue; returns the JS value."""
        result = self.call(
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True,
            },
            session_id=session_id,
            timeout=timeout,
        )
        if "exceptionDetails" in result:
            raise CDPError("Runtime.evaluate", result["exceptionDetails"])
        return result.get("result", {}).get("value")

    def navigate(self, session_id, url, wait_load=True, load_timeout=20.0):
        self.call("Page.enable", session_id=session_id)
        result = self.call("Page.navigate", {"url": url}, session_id=session_id)
        if result.get("errorText"):
            raise CDPError("Page.navigate", result["errorText"])
        if wait_load:
            try:
                self.wait_event(
                    "Page.loadEventFired", session_id=session_id, timeout=load_timeout
                )
            except TimeoutError:
                # Fall back to readyState polling — some pages fire load
                # before we attach listeners.
                import time

                deadline = time.time() + 5
                while time.time() < deadline:
                    state = self.evaluate(session_id, "document.readyState")
                    if state == "complete":
                        break
                    time.sleep(0.2)
                else:
                    raise
        return result

    def close(self):
        self.ws.close()
# ===== END CDP CLIENT =====

BROWSER_DEBUG_PORT = 9222
BROWSER_PROFILE_DIR = BASE_DIR / "agent_chrome_profile"
BROWSER_READ_MAX = 20000  # web_fetch ki tarah - page text ki hadd

_browser_lock = threading.Lock()
_browser_client = None   # CDPClient (browser-level connection)
_browser_session = None  # attach hua hua page session


def _find_chrome():
    """User ke installed Chrome ka rasta dhoondo; na mile to None.

    Windows par standard install wale sthan pehle dekhe jate hain,
    phir PATH. Dusre OS par bhi wahi koshish (dev/test ke liye).
    """
    candidates = []
    system = platform.system()
    if system == "Windows":
        for env in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
            root = os.environ.get(env)
            if root:
                candidates.append(Path(root) / "Google" / "Chrome" /
                                  "Application" / "chrome.exe")
    elif system == "Darwin":
        candidates.append(Path("/Applications/Google Chrome.app"
                               "/Contents/MacOS/Google Chrome"))
    for cand in candidates:
        if cand.is_file():
            return str(cand)
    for name in ("chrome", "google-chrome", "google-chrome-stable",
                 "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    return None


def _browser_setup_needed_msg() -> str:
    return ("Agent wala Chrome abhi chal nahi raha hai. Pehle chat "
            "me likho: 'browser setup karo' - ek alag Chrome "
            "khulega, usme tum ek baar khud login kar loge, phir "
            "main wahi se tumhara kaam karunga. (Password main "
            "kabhi nahi mangta aur kabhi store nahi karta - login "
            "hamesha tumhare haath me rahega.)")


# ----------------------------------------------------------------------
# 'browser setup karo' - agent wala Chrome kholne ka hukum. Ye bhi
# update/site commands ki tarah demo/Gemini dispatch se PEHLE pakda
# jata hai (ask_agent me), taaki bina dimag ke turant chale.
# ----------------------------------------------------------------------

_BROWSER_SETUP_TRIGGERS = ("browser setup karo", "browser setup")


def _is_browser_setup_command(low: str) -> bool:
    """'browser setup karo' hukum ki pehchan (dono modes ke liye)."""
    return (low or "").strip().lower() in _BROWSER_SETUP_TRIGGERS


def tool_browser_setup() -> str:
    """Agent wala Chrome kholo - dedicated profile ke saath.

    User us window me EK BAAR khud login karega. Password agent
    kabhi nahi mangta, dekhta ya store karta - login hamesha user
    ke haath me hai, aur ye baat jawab me saaf kahi jati hai.
    """
    marker = BROWSER_PROFILE_DIR / "DevToolsActivePort"
    try:
        http_json(BROWSER_DEBUG_PORT, "/json/version", timeout=2.0)
        port_alive = True
    except Exception:
        port_alive = False
    if port_alive and marker.is_file():
        return ("Agent wala Chrome pehle se khula hua hai - kaam "
                "usi window me hoga. Agar usme login nahi hai to "
                "pehle khud login kar lo, phir hukum do.")
    if port_alive:
        return ("Port 9222 par pehle se kuch aur chal raha hai, "
                "isliye agent wala Chrome nahi khol paya. Use band "
                "karke 'browser setup karo' dobara likho.")
    chrome = _find_chrome()
    if not chrome:
        log("BROWSER SETUP fail: is PC par Chrome nahi mila")
        return ("Is PC par Google Chrome mila hi nahi. Pehle "
                "Chrome install karo (google.com/chrome se), phir "
                "'browser setup karo' likhna - main dobara try "
                "karunga.")
    try:
        BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return f"Browser ki profile folder nahi ban payi: {exc}"
    args = [chrome,
            f"--remote-debugging-port={BROWSER_DEBUG_PORT}",
            "--remote-debugging-address=127.0.0.1",
            f"--user-data-dir={BROWSER_PROFILE_DIR}",
            "--no-first-run",
            "--new-window",
            "https://www.facebook.com"]
    try:
        if platform.system() == "Windows":
            # DETACHED_PROCESS (0x8): Chrome engine ke band hone par
            # bhi khula rahe - apni alag zindagi jiye.
            subprocess.Popen(args, creationflags=0x00000008)
        else:
            subprocess.Popen(args, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
    except Exception as exc:
        log(f"BROWSER SETUP fail: Chrome launch error: {exc}")
        return f"Chrome kholne me dikkat aayi: {exc}"
    for _ in range(20):
        try:
            http_json(BROWSER_DEBUG_PORT, "/json/version", timeout=2.0)
            break
        except Exception:
            time.sleep(0.5)
    else:
        log("BROWSER SETUP: Chrome khula lekin devtools taiyaar nahi")
        return ("Chrome khol to diya hai, lekin uska control abhi "
                "taiyaar nahi hua. Thoda ruk kar koi browser wala "
                "hukum do; phir bhi na ho to Chrome band karke "
                "'browser setup karo' dobara likho.")
    log("BROWSER SETUP: agent wala Chrome khul gaya (dedicated profile)")
    return ("Agent wala Chrome khul gaya hai - usme Facebook khula "
            "hoga. Ab us window me TUM KHUD Facebook (aur chaho to "
            "YouTube/TikTok) me login kar lo. Ye login sirf EK "
            "BAAR karna hoga - is profile me login yaad rahega.\n"
            "Saaf baat: main tumhara password KABHI nahi mangunga, "
            "dekhunga ya store karunga - login hamesha tumhare "
            "haath me hai.\n"
            "Login ho jaye to bas hukum do - jaise 'facebook kholo' "
            "ya 'is video ko upload kar do'.")


# ----------------------------------------------------------------------
# Connection - lazy: pehle browser tool par banta hai, phir cached
# rehta hai. Chrome band ho jaye to agli koshish khud reset karke
# saaf wajah deti hai.
# ----------------------------------------------------------------------


def _browser_reset():
    global _browser_client, _browser_session
    try:
        if _browser_client is not None:
            _browser_client.close()
    except Exception:
        pass
    _browser_client = None
    _browser_session = None


def _browser_connect():
    """Agent wale Chrome se CDP connection banao (lazy + cached).

    Safal ho to (client, session_id); warna (None, wajah) - wajah
    user ko dikhane layak Hinglish message hai. Sirf WAHI Chrome
    qabool hai jo hamari dedicated profile se chala ho - uski
    pehchan profile folder ki DevToolsActivePort file hai.
    """
    global _browser_client, _browser_session
    if _browser_client is not None and _browser_session:
        try:
            _browser_client.evaluate(_browser_session, "1")
            return _browser_client, _browser_session
        except Exception:
            _browser_reset()
    try:
        http_json(BROWSER_DEBUG_PORT, "/json/version", timeout=3.0)
    except Exception:
        return None, _browser_setup_needed_msg()
    if not (BROWSER_PROFILE_DIR / "DevToolsActivePort").is_file():
        return None, ("Port 9222 par kuch chal raha hai, lekin wo "
                      "agent wala Chrome nahi lagta - uski profile "
                      "(agent_chrome_profile) yahan nahi mili. Chat "
                      "me likho: 'browser setup karo' - sahi Chrome "
                      "wahi se khulega.")
    try:
        client = CDPClient(port=BROWSER_DEBUG_PORT, timeout=20.0)
        session = None
        targets = client.call("Target.getTargets").get("targetInfos", [])
        for t in targets:
            if t.get("type") != "page":
                continue
            turl = t.get("url", "")
            if turl.startswith(("chrome://", "devtools://",
                                "chrome-extension://")):
                continue
            try:
                session = client.call(
                    "Target.attachToTarget",
                    {"targetId": t["targetId"], "flatten": True},
                )["sessionId"]
                break
            except Exception:
                continue
        if session is None:
            session = client.new_page("about:blank")
        client.call("Runtime.enable", session_id=session)
        _browser_client, _browser_session = client, session
        log("BROWSER: agent wale Chrome se connect ho gaya")
        return client, session
    except Exception as exc:
        _browser_reset()
        return None, (f"Browser se connect nahi ho paya ({exc}). "
                      + _browser_setup_needed_msg())


def _with_browser(work) -> str:
    """Ek browser wala kaam chalao: connection lazy banta hai, har
    haar par saaf Hinglish jawab milta hai (kabhi crash nahi), aur
    kharab connection reset ho jata hai taaki agli koshish taza ho.
    Saare browser kaam ek lock ke andar - ek samay par ek hi kadam.
    """
    with _browser_lock:
        client, session = _browser_connect()
        if client is None:
            return session  # session ki jagah wajah wala message hai
        try:
            return work(client, session)
        except CDPError as exc:
            _browser_reset()
            return f"Browser ne mana kar diya: {exc}"
        except Exception as exc:  # browser tools kabhi crash nahi karte
            _browser_reset()
            return f"Browser wala kaam atak gaya: {exc}"


# ----------------------------------------------------------------------
# Page ke andar element dhoondhne wale JS tukde. Pehle CSS selector
# try hota hai, phir dikhai dene wala text/label. Yehi tareeka
# demo.py me proven hai (wahan inline tha, yahan function roop me).
# ----------------------------------------------------------------------

_CLICK_FIND_JS = """
function (target) {
  function labelOf(el) {
    return (el.innerText || el.value ||
            el.getAttribute('aria-label') || '').trim();
  }
  var el = null;
  try { el = document.querySelector(target); } catch (e) { el = null; }
  if (!el) {
    var want = String(target).trim().toLowerCase();
    var nodes = document.querySelectorAll(
      'a, button, [role="button"], input[type="submit"], ' +
      'input[type="button"], [onclick]');
    var i, t;
    for (i = 0; i < nodes.length; i++) {
      t = labelOf(nodes[i]).toLowerCase();
      if (t && t === want) { el = nodes[i]; break; }
    }
    if (!el) {
      for (i = 0; i < nodes.length; i++) {
        t = labelOf(nodes[i]).toLowerCase();
        if (t && t.indexOf(want) !== -1) { el = nodes[i]; break; }
      }
    }
  }
  if (!el) return {found: false};
  el.scrollIntoView({block: 'center', inline: 'center'});
  var r = el.getBoundingClientRect();
  var s = getComputedStyle(el);
  if (r.width <= 0 || r.height <= 0 || s.display === 'none' ||
      s.visibility === 'hidden') {
    return {found: false,
            reason: 'element page par dikhai nahi de raha'};
  }
  return {found: true, x: r.x + r.width / 2, y: r.y + r.height / 2,
          label: labelOf(el).slice(0, 80)};
}
"""

_TYPE_FOCUS_JS = """
function (target) {
  function labelOf(el) {
    return (el.getAttribute('placeholder') ||
            el.getAttribute('aria-label') || el.name ||
            el.id || '').trim();
  }
  var el = null;
  try { el = document.querySelector(target); } catch (e) { el = null; }
  if (!el) {
    var want = String(target).trim().toLowerCase();
    var nodes = document.querySelectorAll(
      'input, textarea, [contenteditable="true"], [contenteditable=""]');
    for (var i = 0; i < nodes.length; i++) {
      var t = labelOf(nodes[i]).toLowerCase();
      if (t && t.indexOf(want) !== -1) { el = nodes[i]; break; }
    }
  }
  if (!el) return {found: false};
  el.focus();
  try {
    var len = (el.value || '').length;
    if (el.setSelectionRange) el.setSelectionRange(len, len);
  } catch (e) {}
  return {found: true,
          type: (el.type || el.getAttribute('type') || '').toLowerCase(),
          label: labelOf(el).slice(0, 80)};
}
"""

_UPLOAD_CHECK_JS = """
function (target) {
  var el = null;
  try { el = document.querySelector(target); } catch (e) { el = null; }
  if (!el || !el.files || !el.files.length) return {ok: false};
  return {ok: true, name: el.files[0].name, size: el.files[0].size};
}
"""


# ----------------------------------------------------------------------
# Browser tools - JSON-action protocol ke asal auzaar
# ----------------------------------------------------------------------


def tool_browser_open(url: str) -> str:
    url = (url or "").strip()
    if not re.match(r"^https?://", url):
        return "Sirf http/https wala link khol sakta hu - sahi URL do."

    def work(client, session):
        client.navigate(session, url)
        title = client.evaluate(session, "document.title") or url
        return f"Agent wale Chrome me page khul gaya: {title}\n{url}"

    return _with_browser(work)


def tool_browser_read() -> str:
    def work(client, session):
        title = client.evaluate(session, "document.title") or ""
        url = client.evaluate(session, "location.href") or ""
        text = client.evaluate(
            session,
            "(document.body ? document.body.innerText : '')") or ""
        text = re.sub(r"\n{3,}", "\n\n", str(text)).strip()
        if len(text) > BROWSER_READ_MAX:
            text = (text[:BROWSER_READ_MAX] +
                    "\n... (page aur lamba hai - bas itna hi padha)")
        if not text:
            text = ("(page par padhne layak text nahi mila - page "
                    "abhi load ho raha hoga, ya sab kuch tasveeron "
                    "me hai)")
        return (f"Page: {title or '(bina title)'}\nURL: {url}\n"
                f"---\n{text}")

    return _with_browser(work)


def tool_browser_click(target: str) -> str:
    target = (target or "").strip()
    if not target:
        return "Kya dabana hai - uska text ya CSS selector to do."

    def work(client, session):
        info = client.evaluate(
            session,
            "(" + _CLICK_FIND_JS + ")(" + json.dumps(target) + ")")
        if not info or not info.get("found"):
            reason = (info or {}).get(
                "reason", "page par wo cheez mili hi nahi")
            return (f"'{target}' nahi dab paya: {reason}. Pehle "
                    "browser_read karke dekho page par kya-kya dikh "
                    "raha hai, phir sahi naam/selector se try karo.")
        for etype, buttons in (("mousePressed", 1),
                               ("mouseReleased", 0)):
            client.call(
                "Input.dispatchMouseEvent",
                {"type": etype, "x": info["x"], "y": info["y"],
                 "button": "left", "buttons": buttons,
                 "clickCount": 1},
                session_id=session)
            time.sleep(0.05)
        time.sleep(0.8)  # click ke baad page ko sambhalne ka samay
        label = info.get("label") or target
        return f"'{label}' par click kar diya."

    return _with_browser(work)


def tool_browser_type(target: str, text: str) -> str:
    target = (target or "").strip()
    text = "" if text is None else str(text)
    if not target:
        return ("Kis field me likhna hai - uska naam ya CSS "
                "selector to do.")

    def work(client, session):
        info = client.evaluate(
            session,
            "(" + _TYPE_FOCUS_JS + ")(" + json.dumps(target) + ")")
        if not info or not info.get("found"):
            return (f"'{target}' wala field page par nahi mila. "
                    "Pehle browser_read karke dekho sahi field "
                    "kaunsi hai.")
        if info.get("type") == "password":
            return ("Ruk gaya: ye PASSWORD wala field hai. Main "
                    "isme kabhi kuch nahi likhta - login Ankit "
                    "khud karta hai. Wo screen khud sambhal lo, "
                    "uske baad ka kaam main kar dunga.")
        client.call("Input.insertText", {"text": text},
                    session_id=session)
        label = info.get("label") or target
        shown = text if len(text) <= 100 else text[:100] + "..."
        return f"'{label}' me likh diya: {shown}"

    return _with_browser(work)


def tool_browser_upload_file(target: str, path: str) -> str:
    target = (target or "").strip() or "input[type=file]"
    raw = (path or "").strip().strip('"').strip("'")
    if not raw:
        return "Kaunsi file lagani hai - uska path to do."
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = WORK_DIR / raw
    p = p.resolve()
    if not p.is_file():
        return (f"File mili nahi: {raw} - sirf naam pata ho to "
                "pehle find_file se poore computer me uska path "
                "nikalo, phir wahi poora path yahan do.")

    def work(client, session):
        doc = client.call("DOM.getDocument", session_id=session)
        node = client.call(
            "DOM.querySelector",
            {"nodeId": doc["root"]["nodeId"], "selector": target},
            session_id=session)
        node_id = node.get("nodeId") or 0
        if not node_id:
            return (f"Page par file wala input ('{target}') nahi "
                    "mila. Ho sakta hai pehle koi 'Upload' / 'Add "
                    "video' wala button dabana pade - browser_click "
                    "se wo dabao, phir ye tool dobara chalao.")
        client.call("DOM.setFileInputFiles",
                    {"nodeId": node_id, "files": [str(p)]},
                    session_id=session)
        time.sleep(0.5)
        seen = client.evaluate(
            session,
            "(" + _UPLOAD_CHECK_JS + ")(" + json.dumps(target) + ")")
        size_mb = p.stat().st_size / (1024 * 1024)
        if seen and seen.get("ok"):
            return (f"File lag gayi: {p.name} ({size_mb:.2f} MB) - "
                    f"page ne bhi wahi file pehchani "
                    f"({seen.get('name')}). Ab aage ke steps "
                    "(caption adi) pure karo.")
        return (f"File input par laga di hai: {p.name} "
                f"({size_mb:.2f} MB). Page ne abhi use dikhaya "
                "nahi - browser_read se ek baar page check kar lo.")

    return _with_browser(work)


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
    "browser_open": tool_browser_open,
    "browser_read": tool_browser_read,
    "browser_click": tool_browser_click,
    "browser_type": tool_browser_type,
    "browser_upload_file": tool_browser_upload_file,
    "download_file": tool_download_file,
    "make_video": tool_make_video,
    "watch_video": tool_watch_video,
    "run_program": tool_run_program,
    "find_file": tool_find_file,
    "see_image": tool_see_image,
    "open_file": tool_open_file,
    "extract_zip": tool_extract_zip,
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
  browser setup karo          - agent wala Chrome kholo (alag
                                profile) - usme ek baar tum KHUD
                                login karoge; phir main browser
                                tools se logged-in sites ka kaam
                                karunga (password main kabhi nahi
                                mangta, dekhta ya store karta)
  facebook kholo              - mashhoor site seedha browser me khol
                                do (youtube, instagram, tiktok,
                                whatsapp, google, gmail bhi chalega)
  help                        - this list
  quit                        - stop
For free chatting like Muse, add your free Gemini key in config.env.
Tez dimag: config.env me GROQ_API_KEY bhi ho to pehle Groq ka tez
model jawab deta hai - wo atak jaye to Gemini khud sambhal leta hai."""


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


def _gemini_call(contents: list, model: str = None,
                 system_instruction: bool = True) -> str:
    model = model or GEMINI_MODEL
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={GEMINI_API_KEY}")
    body = {"contents": contents}
    if system_instruction:
        body["system_instruction"] = {
            "parts": [{"text": _system_prompt()}]}
    # system_instruction=False sirf photo ke VIVARAN wali call ke
    # liye hai: wahan agent wala system prompt model ko tool-call
    # JSON ki taraf dhakelta hai, jabki wahan sirf "photo me kya
    # hai" wala saaf vivaran chahiye (v8.5 ka vision->tools bridge).
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
# Groq - dusra, TEZ dimag (v8.2). config.env me GROQ_API_KEY ho to
# pehle Groq jawab deta hai (uske khaas tez chips par chalne wala
# Llama model). API OpenAI-compatible hai: wahi system prompt, wahi
# tool protocol (tolerant parser), wahi tool loop - bas transport
# alag hai. Groq ki koi bhi haar (timeout, busy 429/503, galat key
# 401, ya koi aur error) haar NAHI mani jati: agent chup chaap
# Gemini ladder par gir jata hai aur wahi se jawab lata hai.
# Bina Groq key ke ye hissa bilkul nahi chalta (v8.1 wala vyavhaar).
# --------------------------------------------------------------------------

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# Fail-fast: Groq tez hone ke liye mashhoor hai, isliye sirf 30s ka
# intezaar. Timeout/network par kul 2 koshish (2s ki rukawat), busy
# (429/503) par kul 3 koshish (2s, phir 5s) - phir Gemini ki baari.
_GROQ_TIMEOUT = 30


class _GroqDownError(Exception):
    """Groq se jawab nahi aaya - caller Gemini ladder par girega.

    status me HTTP code rehta hai jab haar kisi HTTP jawab se
    aayi ho (401/403 matlab key ki gadbad) - caller usi se
    faisla karta hai ki user ko key jaanchne ki salah deni hai
    ya nahi. Timeout/network wali haar par status None rehta hai.
    """

    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def _to_openai_messages(contents: list) -> list:
    """Agent ki andar wali history (Gemini-style contents) ko Groq ke
    OpenAI-style messages me badlo: pehle system prompt (yaadon ke
    saath), phir user/assistant ki baariyan (andar 'model' role hai,
    Groq me wahi 'assistant' kahlata hai)."""
    messages = [{"role": "system", "content": _system_prompt()}]
    for item in contents or []:
        role = "assistant" if item.get("role") == "model" else "user"
        text = "".join(p.get("text", "") for p in item.get("parts", []))
        messages.append({"role": role, "content": text})
    return messages


def _groq_call(messages: list) -> str:
    """Groq ko ek baar (retry ke saath) bulao aur jawab ka text do.

    Fail-fast neeti upar wali hai. Busy (429/503) ke alawa koi bhi
    HTTP error (401 galat key samet) turant _GroqDownError banta
    hai - retry bekaar hai, Gemini ki baari jaldi aani chahiye.
    Saari koshishen khatm hon to bhi _GroqDownError hi uthta hai,
    taaki caller hamesha ek hi tareeke se Gemini par gir sake.
    """
    body = {"model": GROQ_MODEL, "messages": messages}
    req = urllib.request.Request(
        _GROQ_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {GROQ_API_KEY}"},
        method="POST",
    )
    last_exc = None
    attempt = 0
    while True:
        try:
            with urllib.request.urlopen(req, timeout=_GROQ_TIMEOUT) as resp:  # noqa: S310
                data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"].get("content")
            return (content or "").strip()
        except urllib.error.HTTPError as exc:
            if exc.code not in _BUSY_CODES:
                log(f"GROQ fail: HTTP {exc.code} (turant Gemini ki baari)")
                raise _GroqDownError(f"HTTP {exc.code}",
                                     status=exc.code) from exc
            last_exc = exc
            max_attempts = 3
            delays = _BUSY_DELAYS
            log(f"GROQ attempt {attempt + 1}/{max_attempts} fail: "
                f"HTTP {exc.code} (server busy / rate limit, retry)")
        except (urllib.error.URLError, socket.timeout, TimeoutError,
                ConnectionError) as exc:
            last_exc = exc
            max_attempts = 2
            delays = _TIMEOUT_DELAYS
            log(f"GROQ attempt {attempt + 1}/{max_attempts} fail: {exc}")
        if attempt + 1 >= max_attempts:
            break
        time.sleep(delays[min(attempt, len(delays) - 1)])
        attempt += 1
    raise _GroqDownError(
        str(last_exc),
        status=(last_exc.code
                if isinstance(last_exc, urllib.error.HTTPError)
                else None))


def _groq_converse(contents: list):
    """Groq ke saath pura tool-loop - _gemini_converse ka aaina.

    (jawab, tool_chala_kya) return hota hai. Tool protocol bilkul
    wahi hai: jawab me JSON mile to _extract_tool_call use pehchan
    kar tool chalata hai, warna jawab plain text hai. Groq ki haar
    par _GroqDownError (ya koi aur exception) upar jata hai.
    """
    contents = list(contents)
    used_tool = False
    for _ in range(5):  # max 5 tool steps per message
        reply = _groq_call(_to_openai_messages(contents))
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


# --------------------------------------------------------------------------
# Tool discipline (v8.1) - 'khud kar lo' wali shikayat ka code ilaaj.
# Hukum me action wala shabd ho (kholo, banao, likho...) aur model ne
# BINA koi tool chalaye sirf text jawab de diya ho, to ek baar sakht
# instruction ke saath dobara pucha jata hai. Kul EK re-ask per
# message - loop kabhi nahi banta.
# --------------------------------------------------------------------------

_ACTION_WORDS = ("kholo", "khol", "open", "banao", "bana", "create",
                 "download", "upload", "post", "likho", "save",
                 "delete", "hatao", "bhejo", "chalao", "play")
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


def _brain_run(contents: list):
    """Dimag chalao: pehle Groq (agar key hai), fail ho to Gemini ladder.

    Safal ho to (jawab, tool_chala_kya); sab fail hon to
    (error_message, None) - error message Gemini wali class-neeti
    se hi banta hai (busy -> busy wala, slow -> slow wala, 404 ->
    plain). Groq se gir kar Gemini se jawab aaye to jawab ke upar
    ek chhota note lagta hai. Groq ki haar key wali ho (HTTP
    401/403) to note me key jaanchne ka ishara bhi jud jata hai -
    baaki haar (timeout/429/5xx/network) par note bilkul waisa
    hi rehta hai. Bina Groq key ke ye seedha Gemini ladder hai -
    bilkul v8.1 wala vyavhaar, koi note nahi.
    """
    groq_failed = False
    groq_key_error = False
    if GROQ_API_KEY:
        try:
            reply, used_tool = _groq_converse(contents)
            log("BRAIN: jawab GROQ se aaya")
            return reply, used_tool
        except Exception as exc:  # har haar par Gemini ki baari
            groq_failed = True
            if getattr(exc, "status", None) in (401, 403):
                # Key wali gadbad (galat ya mis-paste hui key) -
                # user ko note me key jaanchne ka ishara milega.
                groq_key_error = True
            log(f"BRAIN: GROQ fail ({exc}) - Gemini ladder par ja "
                "raha hu")
    reply, used_tool = _ladder_run(contents)
    if used_tool is not None and groq_failed:
        note = ("(tez wale model se jawab nahi aaya, dusre model se "
                "laya hu)")
        if groq_key_error:
            note += (" (Note: lagta hai Groq wali key sahi nahi "
                     "hai — config.env me GROQ_API_KEY wali line "
                     "ek baar jaanch lo, key gsk_ se shuru hoti "
                     "hai.)")
        reply = note + "\n" + reply
    return reply, used_tool


_TOOL_JSON_SHAPE = re.compile(r'"tool"\s*:\s*"[A-Za-z_][A-Za-z0-9_]*"')


def _guard_no_tool_json(reply: str) -> str:
    """Aakhri suraksha: model ka KACCHA tool-call JSON user ko
    kabhi text bankar nahi dikhna chahiye.

    Asal PC par yahi hua tha (v8.4, 2026-11-20): photo wale
    turn par model ne {"tool": "list_skills", ...} bhej diya
    aur wo jawab bankar user ko dikh gaya - user ne pucha
    "ye kay hai". Tool-loop aam taur par tool-call ko chala
    kar alag kar deta hai, lekin koi jawab phir bhi tool-call
    wali shakal me aakhri text bankar reh jaye (parse na ho
    paya ho, aadha kata hua ho, ya prose ke beech ghula ho)
    to use saaf Hinglish line se badal do. Shakal matlab
    jawab me kahin bhi "tool": "naam" wala pattern - aam
    jawab me ye kabhi nahi aata, isliye jahan dikhe wahi
    leak hai.
    """
    if not reply or not _TOOL_JSON_SHAPE.search(reply):
        return reply
    log("GUARD: jawab me kaccha tool-call JSON tha - user ko "
        "saaf jawab diya")
    return ("Kaam karne ki koshish ki, lekin mera jawab gadbad "
            "ho gaya (andar ki takneeki cheez bahar aa gayi). "
            "Ek baar phir se bolo - main dobara koshish karta "
            "hu.")


def brain_ask(message: str) -> str:
    """Dimag se jawab lao - Groq pehle (key ho to), Gemini ladder
    peeche, aur discipline re-ask ke saath.

    Dono dimag fail hon to jawab AAKHRI error ki class se banta hai
    (busy -> busy message, timeout -> slow message, 404 -> plain
    message). Jawab aa jaye lekin hukum action wala ho aur koi tool
    na chala ho (sirf salah mili ho), to ek baar strict re-ask
    hota hai - ye niyam dono dimagon par lagta hai.
    Har bahar jane wala jawab _guard_no_tool_json se guzarta
    hai - kaccha tool-call JSON user ko kabhi nahi dikhta.
    """
    with _history_lock:
        _history.append({"role": "user", "parts": [{"text": message}]})
        del _history[:-20]  # keep the last ~10 exchanges
        contents = list(_history)
    reply, used_tool = _brain_run(contents)
    if used_tool is None:
        return _guard_no_tool_json(reply)  # error message
    if used_tool or not _has_action_intent(message):
        return _guard_no_tool_json(reply)
    # Discipline re-ask: sirf EK baar. Pehle history se wo text-wala
    # model jawab hatao (re-ask uski jagah lega), phir sakht hukum
    # ke saath dimag dobara chalao.
    log("DISCIPLINE: action hukum par koi tool nahi chala - strict "
        "re-ask (ek baar)")
    with _history_lock:
        if _history and _history[-1].get("role") == "model":
            _history.pop()
    strict_contents = contents + [
        {"role": "user", "parts": [{"text": _STRICT_REASK}]}]
    reply2, used2 = _brain_run(strict_contents)
    if used2 is None:
        return _guard_no_tool_json(reply)  # re-ask bhi fail
    return _guard_no_tool_json(reply2)


_VISION_DEFAULT_TEXT = (
    "Maine ek photo bheji hai. Use dhyaan se dekho aur Hinglish me "
    "samjhao ki isme kya dikh raha hai. Koi error, message ya text "
    "dikhe to use padh kar uska matlab bhi batao.")


_VISION_DESCRIBE_PROMPT = (
    "Neeche user ki bheji hui ek photo hai. Photo me jo kuch hai "
    "uska saaf VIVARAN do - screen par dikh raha saara text, "
    "file/folder ke naam, poora path, error message, button, "
    "jo hai jaisa hai waisa likho. Ye vivaran ek dusre AI agent "
    "ko milega jo is par asal me kaam karega, isliye naam, path "
    "aur text bilkul sahi-sahi likho. SIRF vivaran do - koi "
    "JSON, koi tool-call, koi code block mat likho.\n"
    "User ne photo ke saath ye likha hai: {user_text}")


def _vision_describe(message: str, image_b64: str, image_mime: str):
    """Photo ka VIVARAN lao - vision -> tools bridge ka pehla kadam.

    Safal ho to (vivaran, None); haar ho to (None, error_jawab)
    jahan error_jawab v8.4 ke _vision_ask wala hi ladder wala
    jawab hai (busy/slow/key-hint apni class ke hisaab se).

    Do jaan-boojh wale faisle:
    1. Vivaran wali call par agent ka SYSTEM PROMPT NAHI jata
       (system_instruction=False). v8.4 me wahi gadbad thi:
       system prompt tool protocol sikha raha tha, to model ne
       vivaran ki jagah {"tool": ...} wala JSON bhej diya jo
       user ko kaccha dikh gaya.
    2. Vivaran user ko seedha NAHI dikhta - wo brain loop ke
       liye context banta hai (ask_agent dekho), taaki photo ke
       saath aaya hukum asal tools se ho sake.
    """
    mime = (image_mime or "").strip().lower()
    if mime not in _VISION_MIMES:
        mime = "image/jpeg"
    if len(image_b64) > 14_000_000:  # ~10 MB base64 me
        return None, ("Photo bahut badi hai - 10 MB se chhoti "
                      "photo bhejo, main use dekh kar bata dunga.")
    user_text = (message or "").strip() or _VISION_DEFAULT_TEXT
    contents = [{"role": "user", "parts": [
        {"text": _VISION_DESCRIBE_PROMPT.format(user_text=user_text)},
        {"inline_data": {"mime_type": mime, "data": image_b64}},
    ]}]
    last_exc = None
    for model in _ladder_models():
        try:
            reply = _gemini_call(contents, model,
                                 system_instruction=False)
            log(f"VISION: vivaran Gemini[{model}] se aaya")
            return reply, None
        except urllib.error.HTTPError as exc:
            if exc.code in _KEY_ERROR_CODES:
                log(f"VISION key-type error (HTTP {exc.code})")
                return None, _gemini_http_message(exc)
            last_exc = exc
            log(f"VISION: {model} fail (HTTP {exc.code})")
        except Exception as exc:
            last_exc = exc
            log(f"VISION: {model} fail: {exc}")
    return None, _final_error_message(last_exc)


def ask_agent(message: str, image: str = None,
              image_mime: str = None) -> str:
    """Single entry point used by both the chat loop and the HTTP hook.

    image (optional) = chat me bheji photo ka base64 data (bina
    data-URL prefix ke). Photo ho to pehle Gemini vision se
    uska VIVARAN aata hai (_vision_describe), phir wahi vivaran
    context bankar AAM brain loop me jata hai - taaki photo ke
    saath aaya hukum (upload kar do, kholo, dhoondo) asal
    tools se ho sake, sirf vivaran par ruk na jaye. Vision
    fail ho to v8.4 wala hi ladder error jawab milta hai.
    """
    message = (message or "").strip()
    if image:
        log(f"ASK (photo ke saath): {message[:120]}")
        if not GEMINI_API_KEY:
            return ("Photo mil gayi, lekin use dekhne ke liye "
                    "Gemini ki key chahiye - config.env me "
                    "GEMINI_API_KEY daal kar phir photo bhejo, "
                    "main dekh kar bata dunga usme kya hai.")
        description, error_reply = _vision_describe(
            message, str(image), str(image_mime or ""))
        if description is None:
            return error_reply
        photo_ctx = ("[User ne ek photo bheji hai. Photo me ye "
                     f"dikh raha hai: {description}]")
        augmented = (f"{message}\n{photo_ctx}" if message
                     else photo_ctx)
        log("VISION->TOOLS: photo ka vivaran brain loop ko diya")
        if _is_update_command(message):
            return run_tool("agent_update", {})
        site_reply = _site_open_reply(message)
        if site_reply is not None:
            return site_reply
        if _is_browser_setup_command(message):
            return tool_browser_setup()
        return brain_ask(augmented)
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
    if _is_browser_setup_command(message):
        # 'browser setup karo' - agent wala Chrome kholna hai. Ye
        # hukum bhi demo/Gemini dispatch se pehle pakda jata hai,
        # bilkul update aur site commands ki tarah.
        return tool_browser_setup()
    demo_reply = demo_ask(message)
    if demo_reply is not None:
        return demo_reply
    if GEMINI_API_KEY or GROQ_API_KEY:
        return brain_ask(message)
    return ("Abhi main demo mode me hu - bina kisi key ke main sirf "
            "tool wale kaam kar sakta hu. 'help' likho, commands dikha dunga. "
            "Free chat ke liye config.env me apni free Gemini key (ya "
            "tez jawab ke liye Groq key) daal do.")

# --------------------------------------------------------------------------
# Premium chat screen (served at GET /) - same design as the phone app.
# The page also lives in ui.html next to this script for easy editing.
# Self-update sirf agent.py badalta hai, isliye UI ka version marker
# ("myagent-ui-version: N") dono copies me rehta hai: GET / par
# DONO me se NAYI version wali copy serve hoti hai, aur startup par
# ensure_ui_file() disk wali ui.html ko embedded se sync kar deta
# hai jab embedded nayi ho. Matlab update + restart ke baad browser
# me NAYI screen hi dikhegi, purani ui.html use rok nahi sakti.
# --------------------------------------------------------------------------

UI_VERSION = 2

UI_HTML = r'''<!DOCTYPE html>
<!-- myagent-ui-version: 2 -->
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
  /* ---------- Photo attach ---------- */
  #attach {
    flex: 0 0 auto; width: 48px; height: 48px; border-radius: 50%; cursor: pointer; margin: 0 0 1px 1px;
    display: flex; align-items: center; justify-content: center; font-size: 20px; font-family: inherit;
    color: #BFE6FF; background: rgba(90,160,255,.10); border: 1px solid rgba(120,190,255,.4);
  }
  #attach:active { transform: scale(.93); }
  #attach.has {
    color: #fff; border-color: rgba(0,194,255,.75);
    background: linear-gradient(135deg, #12BCFF, #0072CE);
    box-shadow: 0 8px 20px rgba(0,150,255,.5), inset 0 1px 0 rgba(255,255,255,.3);
  }
  #photoBar { flex: 0 0 auto; display: none; padding: 0 4px 9px; }
  #photoBar.open { display: block; }
  .photoChip {
    display: inline-flex; align-items: center; gap: 10px; max-width: 100%;
    padding: 7px 12px 7px 8px; border-radius: 16px;
    background: linear-gradient(165deg, rgba(26,48,90,.92), rgba(11,20,40,.96));
    border: 1px solid rgba(0,194,255,.42); box-shadow: 0 8px 20px rgba(0,0,0,.4);
    font-size: 13px; font-weight: 650; color: #DCEFFF;
  }
  .photoChip img { width: 40px; height: 40px; object-fit: cover; border-radius: 11px; border: 1px solid rgba(140,200,255,.4); }
  .photoChip span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 220px; }
  .photoChip button {
    flex: 0 0 auto; width: 24px; height: 24px; border-radius: 50%; cursor: pointer; font-size: 12px; line-height: 1; font-family: inherit;
    color: #FFD7DB; background: rgba(255,110,120,.22); border: 1px solid rgba(255,130,140,.5);
  }
  .bubble img.msgPhoto {
    display: block; max-width: 250px; width: 100%; border-radius: 13px; margin-bottom: 8px;
    border: 1px solid rgba(140,200,255,.45); box-shadow: 0 6px 16px rgba(0,0,0,.35);
  }
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

<div id="photoBar">
  <span class="photoChip"><img id="photoThumb" alt=""><span id="photoName">photo</span><button id="photoRemove" type="button" aria-label="Photo hatao">✕</button></span>
</div>

<div id="inputbar">
  <button id="attach" type="button" aria-label="Photo bhejo" title="Photo / screenshot bhejo">📎</button>
  <input type="file" id="photoInput" accept="image/*" style="display:none">
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

  function addBubble(role, text, isErr, photoUrl) {
    var row = document.createElement("div");
    row.className = "msgrow " + (role === "user" ? "user" : "agent");
    var b = document.createElement("div");
    b.className = "bubble" + (isErr ? " err" : "");
    if (photoUrl) {
      var img = document.createElement("img");
      img.className = "msgPhoto"; img.src = photoUrl; img.alt = "photo";
      b.appendChild(img);
      var cap = document.createElement("span");
      cap.innerHTML = renderText(text);
      b.appendChild(cap);
    } else {
      b.innerHTML = (role === "user") ? renderText(text) : renderRich(text);
    }
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

  /* ---------- Photo bhejna ----------
     Chuni hui photo pendingPhoto me rehti hai: { dataUrl, image, mime, name }.
     Server ko /ask ke JSON me do fields jate hain:
       image      = base64 data (data-URL wala prefix NAHI)
       image_mime = photo ka mime type (jaise image/png)          */
  var attachBtn = document.getElementById("attach");
  var photoInput = document.getElementById("photoInput");
  var photoBar = document.getElementById("photoBar");
  var photoThumb = document.getElementById("photoThumb");
  var photoName = document.getElementById("photoName");
  var pendingPhoto = null;

  attachBtn.addEventListener("click", function () { photoInput.click(); });
  photoInput.addEventListener("change", function () {
    var f = photoInput.files && photoInput.files[0];
    photoInput.value = "";
    if (!f) return;
    if (f.size > 10 * 1024 * 1024) {
      alert("Ye photo bahut badi hai (10 MB se zyada). Chhoti photo ya screenshot bhejo.");
      return;
    }
    var reader = new FileReader();
    reader.onload = function () {
      var dataUrl = String(reader.result || "");
      var comma = dataUrl.indexOf(",");
      pendingPhoto = {
        dataUrl: dataUrl,
        image: comma >= 0 ? dataUrl.slice(comma + 1) : "",
        mime: f.type || "image/jpeg",
        name: f.name || "photo"
      };
      photoThumb.src = dataUrl;
      photoName.textContent = pendingPhoto.name;
      photoBar.classList.add("open");
      attachBtn.classList.add("has");
      inputEl.focus();
    };
    reader.readAsDataURL(f);
  });
  function clearPhoto() {
    pendingPhoto = null;
    photoBar.classList.remove("open");
    attachBtn.classList.remove("has");
    photoThumb.src = "";
  }
  document.getElementById("photoRemove").addEventListener("click", clearPhoto);

  function sendText(text, displayText) {
    text = (text || "").trim();
    if (busy) return;
    if (!text && !pendingPhoto) return;
    if (!getPin()) { openPinGate(""); return; }
    var hero = document.getElementById("heroWrap");
    if (hero) hero.remove();
    var photo = pendingPhoto;
    addBubble("user", displayText || text, false, photo ? photo.dataUrl : null);
    clearPhoto();
    inputEl.value = ""; autoGrow();
    busy = true; sendBtn.disabled = true;
    showTyping();
    var payload = { message: text, pin: getPin() };
    if (photo) { payload.image = photo.image; payload.image_mime = photo.mime; }
    fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
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


def _ui_version_of(text: str) -> int:
    m = re.search(r"myagent-ui-version:\s*(\d+)", text or "")
    return int(m.group(1)) if m else 0


def ensure_ui_file() -> None:
    """ui.html ko embedded UI se sync rakho (skills bootstrap jaisa).

    Disk par ui.html na ho, ya uska version marker embedded se
    purana ho, to embedded copy disk par likh do. Disk wali copy
    nayi ya barabar ho to use haath mat lagao (haath ke edits
    jeette hain). Kabhi crash nahi karta - fail ho to _ui_page
    waise bhi nayi copy serve kar dega.
    """
    try:
        f = BASE_DIR / "ui.html"
        if f.is_file():
            current = f.read_text(encoding="utf-8", errors="replace")
            if _ui_version_of(current) >= UI_VERSION:
                return
        f.write_text(UI_HTML, encoding="utf-8")
        log(f"UI BOOTSTRAP: ui.html embedded copy se sync ki "
            f"(v{UI_VERSION})")
    except Exception as exc:
        log(f"UI BOOTSTRAP fail (chal raha hu): {exc}")


def _ui_page() -> str:
    """Disk wali ui.html aur embedded copy - dono me se NAYI
    version wali serve karo (self-update ke baad purani disk
    file nayi screen ko rok na sake)."""
    try:
        f = BASE_DIR / "ui.html"
        if f.is_file():
            disk = f.read_text(encoding="utf-8")
            if _ui_version_of(disk) >= _ui_version_of(UI_HTML):
                return disk
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
            if GROQ_API_KEY and GEMINI_API_KEY:
                mode = "groq+gemini"
            elif GROQ_API_KEY:
                mode = "groq"
            elif GEMINI_API_KEY:
                mode = "gemini"
            else:
                mode = "demo"
            self._send_json(200, {"ok": True,
                                  "mode": mode,
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
        # Photo (optional): "image" = base64 data (bina data-URL
        # prefix ke), "image_mime" = uska mime (image/png adi).
        img = payload.get("image")
        reply = ask_agent(str(payload.get("message", "")),
                          image=img if isinstance(img, str) else None,
                          image_mime=payload.get("image_mime"))
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

    ensure_bundled_skills()
    ensure_ui_file()

    if not args.no_server:
        start_http_server()

    if GROQ_API_KEY and GEMINI_API_KEY:
        mode = "Groq (tez) + Gemini (backup)"
    elif GROQ_API_KEY:
        mode = "Groq"
    elif GEMINI_API_KEY:
        mode = "Gemini"
    else:
        mode = "demo (no key)"
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

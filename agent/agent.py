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
v8.14: NVIDIA ADD-ON (user ki khaas haan se, v8.13 'final' ke
baad ka chhota add-on) - config.env me NVIDIA_API_KEY ho to
naya PEHLA dimag NVIDIA Build ke free model (default MiniMax
M3.1 Flash) se jawab deta hai, Groq dusra, NVIDIA ka bhaari
model (default Kimi K3.1 Pro) teesra, phir wahi Gemini ladder.
Bina NVIDIA key ke vyavhaar bilkul v8.13 jaisa hai. Saath me
see_image ko Glimmer (NVIDIA) wala vision backup bhi mila -
Gemini photo dekhne me fail ho to wahi kaam Glimmer se hota
hai. Key sirf config.env me rehti hai, code me kabhi nahi.
v8.15: SCREEN HAATH + GENERAL FRAME (user ki khaas haan se) -
(1) SCREEN HAATH: agent ab kisi bhi Windows software ke andar
kaam kar sakta hai - screen_shot (poori screen ki photo, sirf
stdlib ctypes GDI + zlib PNG), screen_locate (vision ladder -
Gemini, fail par Glimmer - se cheez ke beech ke coordinates),
mouse_move/mouse_click/mouse_scroll/type_text/press_key
(SendInput) aur ek-kadam wala screen_do. Har kaam verified
loop me: screenshot -> ek action -> screenshot -> jaanch.
Config switch SCREEN_HAND (default on) se band ho sakta hai.
type_text ka content log me KABHI nahi jata (sirf lambai).
(2) GENERAL FRAME: prompt ki pehchan ab sabse pehle general
personal agent hai - jo hukum, wahi kaam; MindBendMovies uske
projects me se sirf EK hai, poora frame nahi. (3) CAPTCHA/
login par rukna ab smooth hai: screen usi halat me khuli
rehti hai, progress note hoti hai, user ke 'ho gaya' par kaam
usi step se aage badhta hai - shuru se dobara nahi (browser
haath ke stop-rule ka wording bhi isi se align hai).
v8.16: TEZ JAWAB (user ki shikayat: sawal puchho to agent
der tak "soch raha hai" - haan/na tak jaldi nahi aata) -
(1) FAST PATH: chhota status/haan-na sawal (classifier pakka
ho tabhi) pure tool-loop se pehle ek halki tez call se
nibatta hai - Groq chhote budget par, na ho to MiniMax;
shak ho ya fast call fail ho to chup chaap aam loop.
(2) NVIDIA pehla dimag ab 45s par fail-fast (pehle 120s) aur
busy par 2 koshish (pehle 3) - atka hua free endpoint poori
seedhi ko nahi latkata. (3) Kaam wale hukum par turant
"Samajh gaya - kaam shuru kar raha hu" wali tasalli line aur
har tool kadam se pehle saade shabdon me status (streaming
par). (4) Prompt me nateeja-pehle wala niyam: har kaam wale
jawab ki pehli line me ho gaya / nahi hua. (5) ROKO:
UI me lal "⛔ Roko" button + POST /stop endpoint + sirf-stop
wala sandesh - chalta kaam har kadam se pehle flag check
karke agle kadam par rukta hai, "Ruk gaya" jawab ke saath;
jo call/tool usi pal chal raha hai wo beech me nahi katata
(seema code/prompt me saaf hai). UI v4.
v8.17: PEHLE SAMJHO (user ki shikayat, asal screenshot se:
wo beech me samjha raha tha - "abhi baat kar rha, achhe se
samjho, fhir kaam karna" - aur agent jawab dene ki jagah
phir find_file/list_files chalane laga; sath wale screenshot
me ek hi list_files kadam do baar lagatar chala bhi tha) -
(1) SAMAJH GATE: samjhane/dantne wala sandesh (samjho, suno,
"baat kar rha", "maine bola", "aise nahi" jaise pakke
nishan) aam loop se PEHLE pakda jata hai - ek text-only
dimag call (tool bilkul band) jo apne shabdon me dohra kar
bata hai ki kya samjha, na samajh aaye to EK sawal, aur
andar hukum ghula ho to aakhir me "bolo to shuru karu?"
Saaf hukum/file-naam/URL wale sandesh gate par NAHI rukte.
(2) Prompt me niyam 13 "PEHLE SAMJHO". (3) DUP GUARD:
lagatar ayn wahi tool+args dobara manga jaye to dusri baar
chalaya NAHI jata - dimag ko note milta hai "yehi kadam
abhi-abhi ho chuka hai" aur loop aage badhta hai. UI wahi.
BATTERY SE MILE TEEN FIX AUR (asal-baatcheet wale drishyon
se saabit): (4) SAARRE dimag fail hon to jawab sirf Gemini
wali canned line nahi rehta - pehle ek line me nateeja
(kaun-kaun try hua, kya hua), phir asal wajah. (5) Browser
setup na ho to pehla browser tool hi run rok deta hai -
setup wala saaf sandesh hi jawab hai; aur ek hi browser
tool lagatar 2 baar fail ho to teesri maang nahi chalti.
(6) Sirf NVIDIA key ho to bhi brain chalta hai (dispatch
shart me NVIDIA jud gaya).

A personal agent that runs on Ankit's OWN computer.
- All files and logs stay on this machine.
- Brain = Google Gemini free API (key from a local config file, never in code),
  plus optional Groq free API as the fast brain, plus optional NVIDIA
  Build free API as the first brain when its key is set (same rule:
  keys only in the local config file, never in code).
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
import zlib
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

AGENT_VERSION = "8.17"
UPDATE_URL = "https://mindbendmovies.github.io/mindbendmovies-site/agent/agent.py"
SELF_FILE = Path(__file__).resolve()
BACKUP_FILE = BASE_DIR / "agent_backup.py"

# Har bahari HTTP request ke saath browser jaisi pehchan (v8.7).
# Jad wajah (live probe se pakki): Groq ki API Cloudflare ke
# peeche hai aur Cloudflare Python-urllib ki default pehchan
# (User-Agent) ko KEY JAANCHNE SE PEHLE hi rok deta hai -
# HTTP 403, body "error code: 1010" (ban-by-signature). Dummy
# key ke saath bhi wahi 403 aata tha; browser wali pehchan
# lagate hi request asal API tak pahunchti hai aur galat key
# par asal 401 "Invalid API Key" milta hai. Isliye agent ki
# HAR request ab Chrome (Windows) wali pehchan ke saath jati
# hai - Groq, Gemini, update fetch, web fetch/download sab.
_BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
               "AppleWebKit/537.36 (KHTML, like Gecko) "
               "Chrome/140.0.0.0 Safari/537.36")

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
      NVIDIA_API_KEY   - optional (v8.14): his free NVIDIA Build key
                         (stored ONLY here). Ho to pehle NVIDIA wala
                         dimag jawab deta hai, atak jaye to Groq,
                         phir NVIDIA ka bhaari model, phir Gemini.
      NVIDIA_MODEL     - default: minimaxai/minimax-m3.1-flash
      NVIDIA_MODEL_HEAVY - default: moonshotai/kimi-k3.1-pro
      SCREEN_HAND      - v8.15: screen haath (kisi bhi software me
                         mouse/keyboard) chalu hai ya nahi.
                         Default: on. Band karne ke liye off likho.
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
                "GROQ_MODEL", "NVIDIA_API_KEY", "NVIDIA_MODEL",
                "NVIDIA_MODEL_HEAVY", "SCREEN_HAND", "AGENT_PIN",
                "AGENT_PORT", "AGENT_WORK_DIR"):
        if os.environ.get(key):
            cfg[key] = os.environ[key]
    return cfg


def _heal_key(value: str) -> str:
    """API key ki khud-marammat (v8.6) - startup aur har hot-reload par.

    Asal PC par do galtiyan baar-baar huin: key copy-paste me DO-BAARI
    lag gayi (wahi key chipki hui do baar), aur beech me space/newline
    ghus gaya. Dono par Groq/Gemini sirf 401 dete hain aur asal wajah
    kahin dikhti nahi thi. Isliye:
    - key ke ANDAR ki saari whitespace hata do (asli key me space
      hota hi nahi);
    - value agar bilkul do barabar hisson me banti ho (pehla hissa ==
      dusra hissa) to use ek hissa kar do.
    Quotes wala strip load_config pehle hi kar deta hai.
    """
    if not value:
        return value
    cleaned = re.sub(r"\s+", "", value)
    if cleaned != value:
        log("CONFIG: key ke andar whitespace thi - hata di")
        value = cleaned
    half = len(value) // 2
    if half and len(value) % 2 == 0 and value[:half] == value[half:]:
        log("CONFIG: key do-baari lagi thi — khud ek kar di")
        value = value[:half]
    return value


def _config_on(value, default: bool = True) -> bool:
    """Config ke on/off wale switch ki pehchan (v8.15): khali
    value par default; on/true/1/yes = True; off/false/0/no =
    False; aur kuch samajh na aaye to default hi sach."""
    text = str(value or "").strip().lower()
    if not text:
        return default
    if text in ("on", "true", "1", "yes"):
        return True
    if text in ("off", "false", "0", "no"):
        return False
    return default


def _apply_config(cfg: dict) -> None:
    """Config dict se LIVE settings lagoo karo: dimag ki keys (self-heal
    ke saath), models aur PIN.

    AGENT_PORT aur AGENT_WORK_DIR yahan jaan-boojh kar NAHI badalte -
    wo sirf startup par lagte hain (HTTP server aur work folder pehle
    se bane hote hain; unhe badalne ke liye engine restart hi chahiye).
    """
    global GEMINI_API_KEY, GEMINI_MODEL, GROQ_API_KEY, GROQ_MODEL
    global NVIDIA_API_KEY, NVIDIA_MODEL, NVIDIA_MODEL_HEAVY
    global SCREEN_HAND
    global AGENT_PIN
    GEMINI_API_KEY = _heal_key(cfg.get("GEMINI_API_KEY", "").strip())
    GEMINI_MODEL = cfg.get("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
    GROQ_API_KEY = _heal_key(cfg.get("GROQ_API_KEY", "").strip())
    GROQ_MODEL = (cfg.get("GROQ_MODEL", "").strip()
                  or "llama-3.3-70b-versatile")
    NVIDIA_API_KEY = _heal_key(cfg.get("NVIDIA_API_KEY", "").strip())
    NVIDIA_MODEL = (cfg.get("NVIDIA_MODEL", "").strip()
                    or "minimaxai/minimax-m3.1-flash")
    NVIDIA_MODEL_HEAVY = (cfg.get("NVIDIA_MODEL_HEAVY", "").strip()
                          or "moonshotai/kimi-k3.1-pro")
    SCREEN_HAND = _config_on(cfg.get("SCREEN_HAND", ""), default=True)
    AGENT_PIN = cfg.get("AGENT_PIN", "").strip()


def _config_path():
    """Jo config file asal me istemal hui thi (config.env pehle, .env baad me)."""
    for name in ("config.env", ".env"):
        path = BASE_DIR / name
        if path.is_file():
            return path
    return None


def _config_mtime():
    try:
        return _CONFIG_FILE.stat().st_mtime if _CONFIG_FILE else None
    except OSError:
        return None


CONFIG = load_config()
_CONFIG_FILE = _config_path()
_CONFIG_MTIME = _config_mtime()
_apply_config(CONFIG)


def _maybe_reload_config() -> None:
    """config.env badla ho to BINA restart nayi settings lagoo karo (v8.6).

    Har /ask ki shuruaat me (aur 'dimag test karo' par) bulta hai:
    config file ki mtime purani wali se alag ho to config dobara
    padho aur dimag ki keys/models + PIN live badal do. Isi se user
    ka "maine file theek kar di phir bhi purani key chal rahi hai"
    wala chakkar khatm hota hai. AGENT_PORT / WORK_DIR startup-only
    hain - wo yahan NAHI badalte. Edit gadbad ho (file aadhi saved,
    galat encoding) to purani settings hi chalti rehti hain aur
    request kabhi crash nahi hota.
    """
    global CONFIG, _CONFIG_MTIME
    try:
        if _CONFIG_FILE is None:
            return
        mtime = _config_mtime()
        if mtime is None or mtime == _CONFIG_MTIME:
            return
        cfg = load_config()
        _apply_config(cfg)
        CONFIG = cfg
        _CONFIG_MTIME = mtime
        log("CONFIG dobara padha gaya — nayi settings lagoo "
            "(restart nahi chahiye)")
    except Exception as exc:
        log(f"CONFIG reload fail (purani settings chalti rahengi): {exc}")


try:
    AGENT_PORT = int(CONFIG.get("AGENT_PORT", "8765"))
except ValueError:
    AGENT_PORT = 8765

WORK_DIR = Path(CONFIG.get("AGENT_WORK_DIR", "") or DEFAULT_WORK_DIR).expanduser()
if not WORK_DIR.is_absolute():
    WORK_DIR = (BASE_DIR / WORK_DIR)
WORK_DIR = WORK_DIR.resolve()
WORK_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """You are "My Agent", Ankit Kumar ke PERSONAL agent. Speak in
Hinglish (Roman Hindi + English mix), short and direct, unless
detail is asked for.
Tum ek GENERAL personal agent ho: jo bhi kaam Ankit bole, wahi
tumhara kaam hai - PC ke andar kisi bhi software me kaam, files,
web, video, likhna, planning, ya kuch aur. Hukum hi tumhara
frame hai: har hukum ko USI ki sharton par pura karo. Koi kaam
kisi purane project se juda na ho to use zabardasti us taraf
mat kheecho, aur koi page/site/software tab tak mat kholo jab
tak hukum me uska zikr na ho.
Ankit ke projects me se EK MindBendMovies hai (movie website +
Android app, USA audience ke liye disturbing/thriller movies,
aur ek Facebook Page ke liye videos) - usse juda kaam aaye to
neeche uske khaas sections aur skills kaam ayenge; baaki saare
kaam bilkul aam taur par, bina us context ke, nibta do.
All data stays on HIS OWN computer. Files tum poore computer me
padh/dhoond sakte ho; likhne ka kaam work folder aur apne
folders me hota hai. Never ask for or reveal any API key or PIN.

PERMISSION RULES (Ankit ne khud diye hain, 2026-11-20):
- Ankit ne apne PC ko apne kaam ke liye use karne ki khuli
  permission di hai - PC/tools bina baar-baar puche use karo.
- Login wale kaam (YouTube, Facebook, TikTok, Google adi): login
  ANKIT KHUD apne browser me karega. Tum password KABHI nahi
  mangoge, kabhi store nahi karoge. Kaam logged-in session se
  hoga - login na ho to use khud login karne ko bolo aur ruk jao.
- Paise kharch wale ya DELETE wale kaam se pehle puchna
  zaroori hai. Baaki kaam bina puche kar do.

HAAR NA MANNA (sabse upar ka niyam - kaam ruk jaye to):
- Ek kadam fail hona kaam fail hona NAHI hai. Rukne ki sochne se
  pehle kam se kam 2-3 ALAG raste khud try karo: dusra tool,
  dusra route/page, page dobara padh kar dusra element, haalat
  jaanch karke phir koshish. Ek hi band darwaza baar-baar MAT
  khatkhato - rasta band mile to DUSRA RASTA lo (jaise Business
  Suite me 'Create reel' na mile to seedha Page ke create flow
  par jao).
- SAWAAL SIRF TAB pucho jab kaam sach me SIRF Ankit ke haath me
  ho: password/login, CAPTCHA/2FA, paisa ya delete ki haan, ya
  usi ka faisla (kai file mili hon to ek line me chunna).
- Bina dekhe sawal puchna MANA hai: "kaunsi video?" se pehle
  find_file/browser_read/read_file se khud dekho.
- Sach me rukna pade to jawab me teen cheezein hon: kya-kya
  try kiya, asal rukawat, aur Ankit ke haath wala EK kaam (ho
  to). Khali "nahi hua" kabhi nahi.

SKILLS: skills/ folder me har seekhe hue kaam ki ek markdown
file hai (jaise youtube-upload). Task kisi skill se match kare
to pehle list_skills/read_skill se wo padho, phir usi ke steps
follow karo. Ankit naya kaam sikhaye to create_skill se
skill bana do. Skill files me kabhi password, API key ya PIN
mat likho.

MEMORY: Tumhari long-term memory MEMORY.md hai; uski baatein har
session me neeche "AGENT KI YAADEIN" me milti hain - har jawab me
dhyaan me rakho. Ankit zaroori baat bataye (pasand, faisla,
chal raha kaam, naam, date) to yaad_likho se save kar do. Roz ki
chhoti baatein save mat karo; memory me bhi password/API key/PIN
kabhi mat likho.
SEEKHNA (Ankit ki baaton se): Ankit SUDHAAR de ya niyam sikhaye
("aise nahi", "galat", "hamesha", "kabhi nahi", "yaad rakhna",
"agli baar" jaisi baat) to wo niyam SABSE PEHLE
yaad_likho(text, section="niyam") se save karo, phir kaam karo,
aur jawab me ek line likho: "Seekh liya: <niyam ek line me>".
Seekhe hue niyam har jawab ke saath neeche milte hain - unhe
hamesha mano.
PURANI BAATEIN: Ankit puchhe "kab bola tha / maine kya kaha
tha / yaad hai maine ... bola tha" to jawab SIRF
purani_baat_dhundho ke record se do - andaz kabhi mat lagao.
Record na mile to bolo: "ye baat mujhe apni diary me nahi mili".

KAAM KARNE KA TAREEKA (hamesha yahi follow karo):
1. Hukum samjho; kaam bada ho to mann me chhota plan banao.
2. Kaam asal me tools se karo - sirf baat karke mat chhodo.
3. Kaam ke baad result khud verify karo: file likhi to
   read_file se, page khola to browser_read se dekho. Verify
   kiye bina "ho gaya" KABHI mat bolo.
4. Error aaye to wahi mat ruko: pehle error ka MATLAB samjho (jo
   wajah likhi hai use padho, andaz mat lagao), phir EK doosra
   tareeka KHUD try karo. Wo bhi na bane to asli wajah batao:
   kya atka, kyun, aage kya ho sakta hai.
5. Jo baat aage kaam aayegi (pasand, faisla, chal raha kaam) use
   yaad_likho se save kar do.
6. SEEKHNA: koi kaam NAYE tareeke se bane ya nayi dikkat ka hal
   mile, to jo tareeka kaam aaya use yaad_likho ya create_skill
   se likh lo. Naya kaam kisi purani yaad/skill se milta-julta
   lage to pehle wahi padho, phir shuru karo.
7. TOOL NA HO TO TOOLS GHUMAO MAT: jis kaam ke liye koi tool
   maujud hi nahi hai, uske liye tools ghuma kar kadam barbaad
   MAT karo. PEHLE kadam par saaf batao ki ye kaam tum abhi nahi
   kar sakte, saath me sabse kareebi hal batao - ya wahi hissa
   khud kar do jo tools se ho sakta hai.
8. ADHURA KAAM - 'JAARI RAKHO': jawab kadam-seema se adhura
   rahe to jawab me "Ab tak ye ho gaya" wali suchi aati hai.
   Ankit 'jaari rakho', 'aage badho' ya 'continue' kahe to kaam
   NAYE SIRE se shuru MAT karo - usi suchi se, ho chuke kadam
   DOBARA kiye bina, wahi se aage badho jahan ruke the.
9. KAI CHEEZON WALA KAAM EK SAATH NIBTAO: kaam me kai cheezein
   hon (jaise 3 design) to saari ek ke baad ek LAGATAR bana do -
   beech me fazool kadam mat ghumao. Saari ban jayein to aakhir
   me ek saath dikha/verify kar lo.
10. AADHA HUKUM (file/cheez ka naam na ho): upload/post/kholne
    wala hukum mile aur file na mili ho, to "kaunsi?" puchhne se
    PEHLE find_file se khud dhoondo (hukum ke shabdo se + aam
    media naamo se). Ek pakki file mile to WAHI chuno aur batao
    kaunsi chuni; kai milein to ek line me top naam dekar pucho;
    koi na mile tabhi ek chhota sawal. KHALI "phir se bolo" wala
    jawab KABHI nahi - ya kaam karo, ya ek saaf chhota sawal.
11. NATEEJA PEHLE (jawab ka kram): Har kaam wale jawab ki
    PEHLI line me nateeja likho: ho gaya / nahi hua, aur ek
    line me kya hua. Lambi tafseel uske baad. Haan/na wale
    sawal ka jawab pehle haan ya na me do.
12. ROKO: Ankit beech me "roko" bole ya Roko button dabaye
    to system chalta kaam agle kadam par rok deta hai - iske
    liye tumhe kuch karna nahi hai. Bas ye jhooth kabhi mat
    bolo ki chal raha call ya tool beech me kat sakta hai:
    rukna hamesha AGLE kadam par hota hai.
13. PEHLE SAMJHO: Ankit kuch SAMJHA raha ho, aadhi baat bol
    raha ho, ya pichhle kaam par sudhaar/narazgi bata raha
    ho, to pehle apne shabdon me dohra kar batao ki tumne
    kya samjha - aur kuch saaf na ho to EK chhota sawal
    puchho. Tool tabhi chalao jab hukum saaf ho. Hukum
    AADHA lage (kaunsi file, kahan, kab - kuch gayab ho) to
    bhi andaze se kaam shuru mat karo: pehle samajh pakki
    karo ya ek sawal puchho, phir kaam karo.

WORKER RULE - SABSE SAKHT (ise kabhi mat todo):
- Tum WORKER ho, salah dene wale advisor NAHI. Hukum ka matlab
  hai kaam KARNA, sirf samjhana nahi.
- "khud kar lo", "aap ye steps follow karein", "aapko ye karna
  hoga", "main direct nahi kar sakta lekin..." tab tak SAKHT
  MANA hai jab tak wo kaam kisi tool se ho sakta ho.
- Pehle tool chalao, phir result batao. Bina tool chalaye "kar
  dunga / ho jayega" wale waade bhi mat karo.

BROWSER HAATH (agent wala Chrome - logged-in sites ke liye):
- Tumhare paas ek khaas Chrome hai jo browser tools se chalta
  hai - Ankit ke roz wale Chrome se ALAG; Ankit usme ek baar
  khud login karta hai ('browser setup karo' se khulta hai).
  Tool kahe Chrome taiyaar nahi hai, to Ankit ko bas 'browser
  setup karo' likhne ko bolo.
- Login wali site ka kaam ho (upload, post, comments) to pehle
  matching skill padho, phir browser tools: browser_open,
  browser_read, phir click/type/upload.
- Reel/post upload ke liye Meta Business Suite ke
  content_calendar wala rasta MAT lo - seedha uske Page par jaa
  kar create flow use karo ('Create reel' wahan nahi milta).
- Ankit POOCHE ki browser me kya khula hai ya kis naam/account se
  login hai, to browser_read karke KHUD dekho aur wahi jawab do -
  andaz mat lagao, sawal ko hukum mat samjho.
- Password KABHI mat mango, mat bharo, mat store karo - login
  sirf Ankit ke haath ka kaam hai.
- Page par login check, CAPTCHA, 2FA ya "confirm it's you" screen
  dikhe to TURANT ruk jao aur Ankit ko bolo wo screen khud
  sambhale. Solve ya bypass ki koshish kabhi mat karna. Page ko
  usi halat me khula rakho, jawab me note karo ki kaam kaun se
  step par ruka hai, aur Ankit ko ek saaf line me bulao.
  Ankit "ho gaya" bole to kaam SHURU SE dobara mat karo -
  browser_read se halat verify karke USI step se aage badho
  jahan ruke the.
- Upload/post me saari taiyaari khud karo aur AAKHRI
  Post/Publish/Schedule click BHI KHUD dabao: Ankit ka hukum
  ("upload kar do", "post kar do") HI uski manjuri hai - alag se
  haan ka intezaar mat karo. Click ke baad browser_read se
  verify karke tabhi "ho gaya" bolo. Aakhri click SIRF tab roko
  jab Ankit bole "pehle dikhao" ya "draft banao".
- Har browser kadam ke baad browser_read se page dobara padho;
  andhere me click mat karo.

VIDEO BANANA (poster + awaaz se poori video):
- "Is movie ki video banao" par pehle 'video-banana' skill
  padho, usi ke steps follow karo: poster download_file se job
  folder ke slides/ me lo, titles.txt likho (har slide: MOVIE
  NAAM | hook line), chaaho to speak_to_file se awaaz rakho,
  phir make_video chalao. Baad me video_info se verify karo.

VIDEO DEKH KAR SEEKHNA:
- Ankit kahe "ye video dekh kar seekho" to watch_video chalao.
  Mile steps pehle dikhao aur saaf pucho: "ye skill bana du?" -
  HAAN mile tabhi create_skill chalao.

VIDEO DEKH KAR SOFTWARE INSTALL / CHALANA (poori chain):
- Ankit SOFTWARE ka tutorial video de aur kahe "ye dekh kar
  install kar do / chala do", to: 1. watch_video se steps samjho
  aur dikhao. 2. Aage badhne par create_skill se skill save kar
  do (nayi-skill-seekhna flow). 3. Software hamesha OFFICIAL source
  se lo - download_file ya run_program se; anjaan site se kabhi
  nahi. 4. Seekhe tareeke se chalao, output dekh kar verify karo.
- Install paisa mange ya khatarnak-class command lage to purana
  rule: pehle poochna, mana kabhi nahi - haan mile to aage badho.

FILES (poora computer - koi seema nahi):
- Ankit file/folder ka NAAM bole (jaise "Dragon Princess Hook
  Reels") to pehle find_file se dhoondo. File ko work/ me rakhne
  ko KABHI mat bolo - file jahan hai wahi se kaam karo.
- File CHALA kar dikhane ko kahe (video play, photo/document)
  to open_file chalao - pehle find_file se path nikalo.
- .zip ke andar ki file ka kaam ho to pehle extract_zip se
  kholo, phir andar ki file par kaam karo.
- Likhne ka kaam work/ ya apne folders (poora home) me hoga.
  System jagah (C:\\Windows adi) par tool mana karega.

PHOTO (screenshot / tasveer dekhna):
- Ankit chat me photo bheje to jo dikh raha hai (error, screen,
  text) usi par jawab do, jaise photo saamne khuli ho.
- PC par padi photo dekhni ho to see_image chalao (poora path).
- Photo ke saath HUKUM aaye ("is se video le kar upload kar
  do") to vivaran ke naam/path ko sach maan kar wahi kaam asal
  me karo - sirf vivaran suna kar mat ruk jao.

DESIGN BANANA (logo / banner / poster):
- Design/logo/banner/poster banane ko kahe to design_banao chalao
  - varnan ko saaf prompt me badal kar do (naam, rang, style).
- Ban jaye to open_file se khol kar DIKHAO - sirf path bata kar
  mat ruk jao.
- Teen design mange to design_banao teen baar - alag style/rang
  aur alag filename (jaise story-tv-logo-1) - phir teeno dikhao.

PROGRAM CHALANA (software install karna / chalana):
- Software/program chalane ko kahe to run_program se asal me
  chalao - sirf steps bata kar mat chhodo.
- Jo install PAISA mange ya jo command files DELETE kare, use
  chalane se PEHLE saaf bata kar haan lo. Baaki aam
  install/program bina puche chalao.
- Khatarnak-class command (disk format, system delete, shutdown
  jaisi) par run_program CONFIRM_REQUIRED deta hai - ye MANA
  NAHI, POOCHNA hai. Tab batao command kya karegi aur pucho
  "chala du?". HAAN mile to WAHI command confirm=true ke saath
  dobara chalao - haan hi kaafi hai. Mana karna ya ghuma-phira
  kar dusra rasta dhoondna sakht mana hai.

SCREEN HAATH (kisi bhi software ke andar kaam):
- Kaam kisi aise software ke andar ho jahan na tool hai na
  browser wala rasta (Notepad, Excel, Paint, installer, koi bhi
  desktop program), to pehle 'screen-haath' skill padho, phir
  screen tools se kaam karo: software run_program/open_file se
  kholo, phir screen_shot -> screen_locate -> EK action
  (mouse_click / type_text / press_key / mouse_scroll) ->
  screen_shot se verify. Ek baar me ek hi kadam; andhere me
  click kabhi nahi, coordinates hamesha taaza screenshot se.
- Screen par login, password wala khana, CAPTCHA ya 2FA dikhe
  to WAHI RUK JAO: software ko usi halat me khula rakho, jawab
  me note karo ki kaam kaun se step par ruka hai, aur Ankit ko
  ek saaf line me bulao ("CAPTCHA/login aaya hai, ek baar khud
  sambhal do, main wahi se aage badhunga"). Password KABHI type
  mat karo. Ankit "ho gaya" bole to kaam shuru se dobara mat
  karo - screen_shot se halat verify karke usi step se aage
  badho.
- Paisa kharch ya DELETE wala button screen par dabana ho to
  wahi purana rule: dabane se PEHLE Ankit se pucho. Baaki aam
  clicks bina puche karo.
- Galat click/type ho jaye to screen_shot se halat dekho,
  sudharo (jaise ctrl+z), aur Ankit ko saaf batao.

TOOL PROTOCOL: If you need a tool, reply with ONLY a JSON object like
{"tool": "list_files", "args": {"path": ""}} and nothing else.
FORMAT RULE (bahut zaroori): tool call wala jawab SIRF wahi ek JSON
object hoga - pehle ya baad me EK SHABD bhi nahi, koi prose nahi.
"args" hamesha asli JSON object hoga {"url": "..."} - string ke andar
band JSON kabhi nahi.
Available tools:
- list_files(path) - folder ki list (poora path do)
- read_file(path) - text file padho (poora path)
- find_file(name) - naam se poore computer me dhoondo (aadha naam chalega); naam bole to PEHLE yahi
- open_file(path) - file default app me kholo (video play / photo / document)
- extract_zip(path) - .zip ko paas wale folder me kholo
- see_image(path) - PC par padi photo/screenshot dekho
- design_banao(prompt, filename) - Gemini se design/logo/banner/poster banao (work/ me)
- write_file(path, content) - text file likho (work/ ya apne folders; system jagah nahi)
- create_folder(path) - folder banao (work/ ya apne folders)
- get_time() - is computer ka current date-time
- web_fetch(url) - http/https page ka text lao
- list_skills() - skill files ki list
- read_skill(name) - ek skill padho, e.g. "youtube-upload"
- create_skill(name, content) - nayi skill save karo (sirf skills/ me)
- yaad_likho(text, section) - zaroori baat memory (MEMORY.md) me save karo; sikhaya NIYAM ho to section="niyam" do ("Seekhe hue niyam" me jayega)
- purani_baat_dhundho(query) - diary me tareekh ke saath purani baat dhoondo - "kab bola tha" wale sawalo ka jawab SIRF isse
- open_url(url) - page PC ke default browser me kholo
- video_info(path) - video ka duration/size/resolution (poora path do)
- trim_video(input, start_sec, duration_sec, output) - video kaato (input kahi bhi; output work/)
- join_videos(files, output) - videos kram me jodo (inputs kahi bhi; output work/)
- speak_to_file(text, filename) - awaaz ki audio file work/ me banao
- agent_update() - naya version check karke install karo (restart ke baad lagega)
- browser_open(url) - agent wale Chrome me page kholo (taiyaar na ho to 'browser setup karo' bolo)
- browser_read() - khule page ka title + text padho
- browser_click(target) - button/link dabao (CSS selector ya dikhai dene wala text)
- browser_type(target, text) - field me likho (caption, title adi)
- browser_upload_file(target, path) - page ke file-input par file lagao (pura path; naam hi pata ho to pehle find_file)
- download_file(url, filename) - internet se file download karo (apne folders; 25 MB tak)
- make_video(job_folder) - job folder (slides/ + titles.txt + optional voice.mp3) se vertical video (skill 'video-banana')
- watch_video(source) - YouTube link/video file dekh kar steps samjho (steps pehle Ankit ko dikhane hain; skill haan par hi banegi)
- run_program(command, confirm) - PC par command chalao. Khatarnak-class par CONFIRM_REQUIRED (mana nahi) - pucho, haan par WAHI command confirm=true se dobara chalao.
- screen_shot() - poori screen ki photo lo (work/ me screen.png; screen ka size bhi milta hai)
- screen_locate(target) - screen par cheez (button/text/icon) dhoondo - uske beech ke pixel coordinates milte hain; na mile to saaf 'nahi mila'
- screen_do(instruction) - screen par EK chhota kadam: screenshot se plan karke ek click/type/key - phir screenshot se verify karke batata hai
- mouse_move(x, y) - mouse ko pixel coordinates par le jao
- mouse_click(x, y, button, double) - click (button "left"/"right"; double true ho to double-click)
- mouse_scroll(amount) - scroll (positive = upar, negative = neeche; aam value 3 ya -3)
- type_text(text) - focused jagah par text type karo (password KABHI mat type karo)
- press_key(combo) - key/combo dabao, jaise "enter", "ctrl+s", "alt+tab", "f5"
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
    req = urllib.request.Request(url, headers={"User-Agent": _BROWSER_UA})
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
    'screen-haath.md': b'# Screen Haath (kisi bhi software ke andar kaam)\n\n## Kab use karein\nJab Ankit ka kaam kisi aise software ke andar ho jahan na koi tool hai na browser wala rasta \xe2\x80\x94 jaise Notepad, Excel, Paint, koi purana desktop program, installer ki khidki, ya koi bhi software jo screen par khula hai. Pehle software `run_program` / `open_file` se kholo, phir screen tools se andar kaam karo.\n\n## Kaam ka tareeka \xe2\x80\x94 verified loop (hamesha yahi)\n1. `screen_shot` se screen dekho \xe2\x80\x94 kya khula hai, tum kahan ho.\n2. Jo cheez dabani/likhni hai, `screen_locate` se uske coordinates nikalo (andaze se click kabhi mat karo).\n3. EK hi action karo: `mouse_click` / `type_text` / `press_key` / `mouse_scroll` \xe2\x80\x94 ek baar me ek kadam. Chhota mila-jula kadam ek saath karna ho to `screen_do` bhi hai (wo bhi ek baar me ek hi kadam uthata hai).\n4. Phir `screen_shot` se dobara dekho ki wahi hua jo socha tha. Na hua ho to pehle halat samjho, phir sudharo \xe2\x80\x94 andhere me agla click kabhi nahi.\n\n## Rukne ke niyam (sabse sakht)\n- Screen par login, password wala khana, CAPTCHA ya 2FA dikhe to WAHI RUK JAO. Page/software ko usi halat me khula chhodo, kaam band mat karo \xe2\x80\x94 apne jawab me note karo ki kaam kaun se step par ruka hai, aur Ankit ko ek saaf line me bulao: "CAPTCHA/login aaya hai, ek baar khud sambhal do, main wahi se aage badhunga."\n- Password KABHI type mat karo \xe2\x80\x94 kisi bhi haal me nahi.\n- Ankit "ho gaya" bole to kaam SHURU SE dobara mat karo: pehle `screen_shot` se halat verify karo, phir USI step se aage badho jahan ruke the.\n- Paisa kharch ya delete wala button screen par dikhe to wahi purana rule: dabane se PEHLE Ankit se pucho. Baaki aam clicks bina puche karo.\n\n## Galti ho jaye to\nGalat click/type ho gaya ho to ghabrao mat aur chhupao bhi mat: `screen_shot` lekar dekho ab halat kya hai, galti ko `press_key` ("ctrl+z") ya sahi click se sudharne ki koshish karo, aur Ankit ko saaf batao kya hua tha aur kya sudhara.\n\n## Dhyaan rahe\n- Coordinates hamesha taaza screenshot ke hisaab se lo \xe2\x80\x94 purane coordinates par bharosa mat karo, screen badalti rehti hai.\n- Kaam human pace par karo: har action ke baad chhota sa thaharna thik hai, jaldi-jaldi clicks mat karo.\n- Software band karna ho to pehle kaam save hua hai ya nahi, ye screenshot se pakka karo.\n',
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

# Seekhe hue niyam (v8.13) - MEMORY.md ke andar ek alag hissa
# "## Seekhe hue niyam". Ankit jab agent ko sudhaarta hai
# ("aise nahi", "hamesha", "kabhi nahi", "agli baar") to niyam
# yaad_likho(section="niyam") se ISI hisse me jata hai, aur is
# hisse ka ek chhota digest (LEARNED_DIGEST_MAX tak) har system
# prompt me jata hai - taaki seekhe hue niyam history window se
# bahar jaane par bhi har jawab me maujud rahein.
LEARNED_SECTION = "## Seekhe hue niyam"
LEARNED_DIGEST_MAX = 1500


def _memory_lines() -> list:
    """MEMORY.md ki lines (file na ho to khali list)."""
    try:
        if MEMORY_FILE.is_file():
            return MEMORY_FILE.read_text(
                encoding="utf-8", errors="replace").splitlines()
    except Exception:
        pass
    return []


def load_learned_rules() -> list:
    """MEMORY.md ke 'Seekhe hue niyam' hisse ke niyam (bina date ke).

    Hisse ki pehchan uske header se hoti hai; uske neeche ki
    bullet lines (agli '## ' heading tak) niyam hain. Har bullet
    "- YYYY-MM-DD: <niyam>" wali shakal me save hoti hai - yahan
    date wala hissa hata kar sirf niyam lautaya jata hai.
    """
    rules = []
    in_section = False
    for line in _memory_lines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_section = (stripped == LEARNED_SECTION)
            continue
        if in_section and stripped.startswith("- "):
            text = re.sub(r"^-\s*\d{4}-\d{2}-\d{2}:\s*", "- ",
                          stripped)
            rules.append(text[2:].strip())
    return [r for r in rules if r]


def learned_rules_digest() -> str:
    """Seekhe hue niyamon ka prompt-digest - naye niyam pehle
    jeette hain: jagah kam ho to sabse NAYE niyam rakhe jate
    hain (purane peeche chhoot jate hain), kul LEARNED_DIGEST_MAX
    chars tak."""
    rules = load_learned_rules()
    picked = []
    total = 0
    for rule in reversed(rules):
        line = "- " + rule
        if picked and total + len(line) + 1 > LEARNED_DIGEST_MAX:
            break
        picked.append(line)
        total += len(line) + 1
    picked.reverse()
    return "\n".join(picked)


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


def tool_save_memory(text: str = "", section: str = "") -> str:
    """Ek zaroori baat MEMORY.md me dated bullet ki tarah jodo.

    section="niyam" ho to baat 'Seekhe hue niyam' wale hisse me
    jati hai (v8.13) - wahi hisse se har system prompt ka digest
    banta hai. File me wo hissa hamesha AAKHIR me rakha jata
    hai: aam yaadein usse PEHLE judti hain, taaki aam bullet
    galti se niyam na ban jaye aur niyam hamesha saaf parse hon.
    """
    clean = re.sub(r"\s+", " ", (text or "")).strip()
    if not clean:
        return "Yaad karne ke liye kuch likho to sahi - khali yaad save nahi hoti."
    clean = clean[:MEMORY_ENTRY_MAX]
    line = f"- {datetime.now().strftime('%Y-%m-%d')}: {clean}"
    is_rule = "niyam" in (section or "").lower()
    try:
        if not MEMORY_FILE.is_file():
            MEMORY_FILE.write_text(
                "# My Agent - Yaadein\n"
                "Ankit ke baare me yaad rakhi hui zaroori baatein.\n\n",
                encoding="utf-8")
        content = MEMORY_FILE.read_text(encoding="utf-8",
                                         errors="replace")
        if is_rule:
            if LEARNED_SECTION not in content:
                content = (content.rstrip("\n") + "\n\n"
                           + LEARNED_SECTION + "\n")
            content = content.rstrip("\n") + "\n" + line + "\n"
        elif LEARNED_SECTION in content:
            idx = content.index(LEARNED_SECTION)
            content = (content[:idx].rstrip("\n") + "\n" + line
                       + "\n\n" + content[idx:])
        else:
            content = content.rstrip("\n") + "\n" + line + "\n"
        MEMORY_FILE.write_text(content, encoding="utf-8")
    except Exception as exc:
        return f"Yaad save nahi ho payi: {exc}"
    if is_rule:
        return (f"Seekh liya aur save kar liya (Seekhe hue niyam): "
                f"{clean} Ab ye niyam mujhe hamesha yaad rahega.")
    return (f"Yaad save kar li: {clean} "
            "Ab ye baat mujhe agli baar bhi yaad rahegi.")


# --------------------------------------------------------------------------
# Diary - baaton ka dated record (v8.13, Amendment 1). User ki
# maang: "vah yaad bhi kar pata - kab kay bola hu kay nhi".
# Har user message (PC ke clock ki tareekh+samay ke saath) aur
# turn ke aakhir me agent ne kya kiya/uska jawab ki ek-line
# summary, baatein.jsonl me append hoti hai. Ye file agent
# folder me hi rehti hai, PC se bahar kabhi nahi jati, aur
# MEMORY.md ki tarah runtime par banti hai (zip me nahi hoti).
# In-memory _history sirf live session ke liye hai; diary hi
# lambe samay ka record hai - 'kab bola tha' wale sawalo ka
# jawab purani_baat_dhundho tool isi se deta hai.
# --------------------------------------------------------------------------

DIARY_FILE = BASE_DIR / "baatein.jsonl"
DIARY_MAX_ENTRIES = 2000
DIARY_REDACTED = "[raaz wali baat — save nahi ki]"
_diary_lock = threading.Lock()

_KEY_SHAPE_RE = re.compile(r"\b(?:gsk_[A-Za-z0-9_\-]{8,}|"
                           r"AIza[A-Za-z0-9_\-]{8,})\b")
_LONG_TOKEN_RE = re.compile(r"\b[A-Za-z0-9_\-]{32,}\b")


def _looks_secret(text: str) -> bool:
    """Text me raaz (API key / PIN / password jaisi cheez) lagta
    hai ya nahi. Pehchan: config me lagi asal values (key/PIN
    ayn text me dikh jayein), jaani-pehchani key shakalein
    (gsk_..., AIza...), aur lambe key-jaise token (32+ akshar,
    akshar+ank dono). Diary/memory me raaz kabhi save nahi
    hota - aisi entry redact hokar jati hai."""
    t = text or ""
    for value in (GEMINI_API_KEY, GROQ_API_KEY, AGENT_PIN):
        if value and len(value) >= 6 and value in t:
            return True
    if _KEY_SHAPE_RE.search(t):
        return True
    for m in _LONG_TOKEN_RE.finditer(t):
        tok = m.group(0)
        if any(c.isalpha() for c in tok) and \
                any(c.isdigit() for c in tok):
            return True
    return False


def _diary_safe(text: str) -> str:
    """Diary ke liye saaf text: raaz dikhe to poori entry ki
    jagah sirf ek nishan - asal baat kabhi file me nahi jati."""
    t = re.sub(r"\s+", " ", (text or "")).strip()
    if t and _looks_secret(t):
        return DIARY_REDACTED
    return t


def ensure_diary_file() -> None:
    """Startup par diary file bana do (na ho to). Kabhi crash
    nahi karta - diary na bane to agent bina diary ke chalega."""
    try:
        if not DIARY_FILE.is_file():
            DIARY_FILE.write_text("", encoding="utf-8")
    except Exception as exc:
        log(f"DIARY file nahi ban payi (bina diary chalega): {exc}")


def _diary_append(user_text: str, did_summary: str,
                  when: datetime = None) -> None:
    """Ek diary entry jodo: kab (PC ka clock), user ne kya bola,
    agent ne kya kiya (ek line). Entry ~2000 se zyada ho jayein
    to sabse purani kat jati hain (nayi 2000 rehti hain)."""
    when = when or datetime.now()
    entry = {
        "ts": when.isoformat(timespec="seconds"),
        "user": _diary_safe(user_text),
        "did": _diary_safe(did_summary)[:200],
    }
    try:
        with _diary_lock:
            ensure_diary_file()
            with open(DIARY_FILE, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
            lines = DIARY_FILE.read_text(
                encoding="utf-8", errors="replace").splitlines()
            if len(lines) > DIARY_MAX_ENTRIES + 200:
                DIARY_FILE.write_text(
                    "\n".join(lines[-DIARY_MAX_ENTRIES:]) + "\n",
                    encoding="utf-8")
    except Exception as exc:
        log(f"DIARY entry save nahi ho payi: {exc}")


def _diary_load() -> list:
    """Diary ki saari entries (purani -> nayi kram me). Kharab
    lines chhod di jati hain - diary kabhi crash ki wajah nahi
    banti. 'Restart ke baad bhi record' yahi file hai."""
    entries = []
    try:
        if DIARY_FILE.is_file():
            for raw in DIARY_FILE.read_text(
                    encoding="utf-8", errors="replace").splitlines():
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    item = json.loads(raw)
                except ValueError:
                    continue
                if isinstance(item, dict) and item.get("ts"):
                    entries.append(item)
    except Exception:
        pass
    return entries


def _diary_fmt_date(ts_text: str) -> str:
    """ISO timestamp ko user ke samajh wali tareekh banao:
    '20 Nov 2026, 8:38 PM'. Parse na ho to jaisa hai waisa."""
    try:
        dt = datetime.fromisoformat(str(ts_text))
        return dt.strftime("%d %b %Y, %I:%M %p").lstrip("0")
    except Exception:
        return str(ts_text)


def tool_purani_baat_dhundho(query: str = "") -> str:
    """Diary me purani baat dhoondo (Amendment 1) - 'kab bola
    tha / maine kya kaha tha' wale sawalo ka EKMAATRA srot.
    Keyword match user ke message aur agent-ke-kaam dono par;
    sabse nayi pehle, zyada se zyada 10 entries, tareekh ke
    saath."""
    q = re.sub(r"\s+", " ", (query or "")).strip().lower()
    if not q:
        return "Kya dhoondhu - koi shabd to do jisse purani baat mile."
    terms = [w for w in re.split(r"[^a-z0-9]+", q) if len(w) >= 3]
    if not terms:
        terms = [q]
    hits = []
    for entry in reversed(_diary_load()):
        blob = ((entry.get("user") or "") + " "
                + (entry.get("did") or "")).lower()
        if any(t in blob for t in terms):
            hits.append(entry)
            if len(hits) >= 10:
                break
    if not hits:
        return (f"Diary me '{query}' wali koi baat nahi mili. "
                "Maine apni poori diary (baatein) dekh li hai - "
                "ye baat wahan save nahi hai.")
    lines = [f"'{query}' par diary me {len(hits)} baatein mili "
             "(sabse nayi pehle):"]
    for entry in hits:
        user_text = (entry.get("user") or "")[:160]
        did = (entry.get("did") or "")[:120]
        line = (f"- {_diary_fmt_date(entry.get('ts'))} — tumne "
                f"bola tha: '{user_text}'")
        if did:
            line += f" | agent ne: {did}"
        lines.append(line)
    return "\n".join(lines)


def _diary_recent_reply(n: int = 10) -> str:
    """'purani baatein' demo command ka jawab: aakhri n entries
    tareekh ke saath (bina dimag ke diary ka saboot)."""
    entries = _diary_load()
    if not entries:
        return ("Diary abhi khaali hai - hamari baatein yahan "
                "apne aap tareekh ke saath save hoti rahengi. Kuch "
                "bolo, phir 'purani baatein' likh kar dekh lena.")
    lines = [f"Meri diary ki aakhri {min(n, len(entries))} baatein "
             "(sabse nayi pehle):"]
    for entry in reversed(entries[-n:]):
        user_text = (entry.get("user") or "")[:80]
        lines.append(f"- {_diary_fmt_date(entry.get('ts'))} — "
                     f"{user_text}")
    return "\n".join(lines)


def _learned_rules_reply() -> str:
    """'kya seekha' demo command ka jawab (v8.13): Seekhe hue
    niyam number-daar suchi me - bina dimag ke saboot ki
    seekhna asal me save hua hai."""
    rules = load_learned_rules()
    if not rules:
        return ("Abhi maine tumse koi khaas niyam nahi seekha "
                "hai. Jab tum mujhe sudhaaroge - 'aise nahi, "
                "hamesha aise karo' jaisi baat - to main use "
                "apne 'Seekhe hue niyam' me save kar lunga aur "
                "hamesha manunga.")
    lines = ["Maine tumse ye niyam seekhe hain (aur hamesha "
             "manta hu):"]
    for i, rule in enumerate(rules, 1):
        lines.append(f"{i}. {rule}")
    return "\n".join(lines)


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
    req = urllib.request.Request(url, headers={"User-Agent": _BROWSER_UA})
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


def _gemini_video_call(parts: list, model: str = None) -> str:
    """Video wale parts ke saath ek seedha Gemini call.

    Chat wale _gemini_call se alag: yahan na system prompt jata
    hai na history - sirf video + seekhne wala prompt. Timeout
    lamba (300s) kyunki video samajhne me samay lagta hai. Galti
    par exception upar jata hai, tool use saaf shabdon me badalta
    hai. model na do to config wala model (GEMINI_MODEL) lagta
    hai - tool_watch_video apni ladder se lite bhi bhejta hai.
    """
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model or GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}")
    body = {"contents": [{"role": "user", "parts": parts}]}
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "User-Agent": _BROWSER_UA,
                 "Accept": "application/json"},
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
    # Model ladder (v8.12): pehle primary model; busy/quota-class
    # (503/429) haar par LITE model ek baar. Wajah: asal PC par
    # primary (3.8) ka free quota khatm hone se watch_video seedha
    # 429 par mar jata tha, jabki lite usi samay chal raha tha.
    # Lite se bane to jawab me saaf likha aata hai ki video chhote
    # model ne dekha hai. Dono fail hon to dono ki asal wajahen.
    video_models = [GEMINI_MODEL or _MODEL_LITE]
    if video_models[0] != _MODEL_LITE:
        video_models.append(_MODEL_LITE)
    text = None
    watched_note = ""
    failures = []  # (model, "http"/"error", code, detail)
    for idx, vmodel in enumerate(video_models):
        try:
            text = _gemini_video_call(parts, vmodel)
            if idx > 0:
                watched_note = " (chhote model se dekha hai)"
            break
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", "replace")[:300]
            except Exception:
                pass
            log(f"WATCH_VIDEO fail [{vmodel}]: HTTP {exc.code}")
            failures.append((vmodel, "http", exc.code, detail))
            if exc.code not in _BUSY_CODES:
                break  # busy/quota ke alawa dusra model bekaar hai
        except Exception as exc:
            log(f"WATCH_VIDEO fail [{vmodel}]: {exc}")
            failures.append((vmodel, "error", None, str(exc)))
            break
    if text is None:
        if len(failures) > 1:
            def _wajah(f):
                _m, k, c, d = f
                if k == "http":
                    return f"HTTP {c}" + (f" ({d})" if d else "")
                return d
            return ("Video dekh nahi paya - dono model ruk gaye. "
                    f"Bada model ({failures[0][0]}): "
                    f"{_wajah(failures[0])}. "
                    f"Chhota model ({failures[1][0]}): "
                    f"{_wajah(failures[1])}. "
                    "Thodi der baad phir try karo.")
        _m, fkind, fcode, fdetail = failures[0]
        if fkind == "http":
            return (f"Video dekh nahi paya - Gemini ne HTTP {fcode} "
                    "diya. Video public hai aur format sahi hai, ye "
                    "check karo; thodi der baad phir try karo."
                    + (f" ({fdetail})" if fdetail else ""))
        return (f"Video dekh nahi paya: {fdetail}. Internet check "
                "karke phir try karo.")
    if not text:
        return ("Video bheja to tha, lekin Gemini se koi jawab "
                "nahi aaya - ek baar phir try karo.")
    if len(text) > 12000:
        text = text[:12000] + "\n... (jawab aur lamba tha, kata gaya)"
    return f"{kind} dekh li{watched_note}. Jo samjha, wo ye raha:\n\n{text}"


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
    if not GEMINI_API_KEY and not NVIDIA_API_KEY:
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
    text = ""
    fail_reply = None
    if GEMINI_API_KEY:
        try:
            text = _gemini_video_call(parts)
        except urllib.error.HTTPError as exc:
            log(f"SEE_IMAGE fail: HTTP {exc.code}")
            fail_reply = (f"Photo dekh nahi paya - Gemini ne HTTP "
                          f"{exc.code} diya. Thodi der baad phir "
                          "try karo.")
        except Exception as exc:
            log(f"SEE_IMAGE fail: {exc}")
            fail_reply = (f"Photo dekh nahi paya: {exc}. Internet "
                          "check karke phir try karo.")
        if not text and fail_reply is None:
            fail_reply = ("Photo bheja to tha, lekin Gemini se koi "
                          "jawab nahi aaya - ek baar phir try karo.")
    if not text and NVIDIA_API_KEY:
        # v8.14: Gemini fail/khaali ho (ya uski key hi na ho) to
        # photo Glimmer (NVIDIA) se samjho - wahi prompt, wahi
        # jawab ki shakal.
        try:
            text = _nvidia_vision_call(b64, mime, _SEE_IMAGE_PROMPT)
            if text:
                log(f"SEE_IMAGE ok (NVIDIA Glimmer): {_rel(target)}")
        except Exception as exc:
            log(f"SEE_IMAGE NVIDIA backup fail: {exc}")
    if not text:
        return fail_reply or ("Photo bheja to tha, lekin Gemini se "
                              "koi jawab nahi aaya - ek baar phir "
                              "try karo.")
    if len(text) > 12000:
        text = text[:12000] + "\n... (jawab aur lamba tha, kata gaya)"
    log(f"SEE_IMAGE ok: {_rel(target)}")
    return f"Photo ({target.name}) dekh li. Jo dikha, wo ye raha:\n\n{text}"


# --------------------------------------------------------------------------
# Design banana (v8.10) - Gemini ke IMAGE model se logo/banner/
# poster jaisi tasveer banana. Asal PC par zinda wajah: user ne
# kaha "story tv ke 3 design banao, logo aur banner" aur agent
# ke paas image banane ka koi tool hi nahi tha - kamzor backup
# dimag alag-alag tools ghumata raha aur step-cap par ruk gaya
# (purana wala "ruk gaya, simple karke pucho" jawab). Ab asal
# tool hai - aur v8.11 me cap-system bhi badal gaya hai (neeche
# _StepTracker dekho): seema 20, loop-pehchan, progress suchi.
# API ki shakal Google ke official docs se verify ki hui hai
# (ai.google.dev/gemini-api/docs/image-generation): POST
# v1beta/models/{model}:generateContent, body me
# generationConfig.responseModalities ["TEXT", "IMAGE"], aur
# jawab ke parts me inlineData {mimeType, data(base64)} bankar
# tasveer aati hai. Pehla model: gemini-3.1-flash-image (Nano
# Banana 2 - maujuda Flash Image workhorse); wo model na mile
# (HTTP 404) to dusra khud try hota hai: gemini-2.5-flash-image
# (purana Nano Banana, door-door tak uplabdh). Har bani hui
# tasveer par Google ka SynthID watermark hota hai (docs ki
# baat hai) - ye Google ki taraf se hai, agent ka kiya nahi.
# --------------------------------------------------------------------------

_DESIGN_MODELS = ("gemini-3.1-flash-image", "gemini-2.5-flash-image")
_DESIGN_TIMEOUT = 120  # image banne me samay lagta hai
_DESIGN_MIME_EXT = {"image/png": ".png", "image/jpeg": ".jpg",
                    "image/jpg": ".jpg", "image/webp": ".webp"}


def _gemini_image_call(prompt: str, model: str):
    """Ek image-generation call: (image_bytes, mime, model_text).

    Tasveer na mile to image_bytes None rahega (model_text me
    model ki kahi baat ho sakti hai). HTTP galti par HTTPError
    upar jata hai - tool use saaf shabdon me badalta hai.
    """
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={GEMINI_API_KEY}")
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}}
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "User-Agent": _BROWSER_UA,
                 "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=_DESIGN_TIMEOUT) as resp:  # noqa: S310
        data = json.loads(resp.read().decode("utf-8"))
    text = ""
    for cand in data.get("candidates") or []:
        for part in (cand.get("content") or {}).get("parts") or []:
            if part.get("text"):
                text += part["text"]
            inline = part.get("inlineData") or part.get("inline_data") or {}
            b64 = inline.get("data")
            if b64:
                mime = (inline.get("mimeType") or inline.get("mime_type")
                        or "image/png")
                return base64.b64decode(b64), mime, text.strip()
    return None, None, text.strip()


def _design_filename(filename: str, mime: str) -> str:
    """Design ki file ka saaf naam: sirf aakhri hissa (basename)
    rakho, ajeeb akshar hata do, aur extension hamesha mile hue
    image ke mime se lagao. '../../evil' jaisi chaal se bhi
    file work/ ke bahar nahi ja sakti - naam seedha wahi banta
    hai."""
    raw = (filename or "").strip().strip('"').strip("'")
    raw = raw.replace("\\", "/").rsplit("/", 1)[-1]
    raw = re.sub(r"[^A-Za-z0-9._\- ]+", "_", raw).strip()
    stem = raw.rsplit(".", 1)[0] if "." in raw else raw
    stem = stem.strip(". ") or "design"
    return stem + _DESIGN_MIME_EXT.get(mime, ".png")


def tool_design_banao(prompt: str, filename: str = "") -> str:
    """Gemini ke image model se ek design/tasveer banao.

    prompt = design ka varnan (kya banna hai - naam, rang,
    style). filename = file ka naam (khaali ho to 'design');
    asli extension mile hue image ke mime se lagti hai aur
    file work/ folder me banti hai. Pehla image model na
    mile (404) to dusra model khud try hota hai; quota (429)
    adi par Gemini ki ASLI wajah wapas jati hai - jhooti
    safalta kabhi nahi milti.
    """
    prompt = (prompt or "").strip()
    if not prompt:
        return ("Kaisa design banau - uska varnan to do (jaise "
                "'Story TV ke liye dark-gold logo, beech me "
                "play button').")
    if not GEMINI_API_KEY:
        return ("Design banane ke liye Gemini ki key chahiye, "
                "lekin config.env me GEMINI_API_KEY mili nahi. "
                "Key daal kar phir bolo - main design bana dunga.")
    img = mime = text = None
    last_404 = ""
    for model in _DESIGN_MODELS:
        try:
            img, mime, text = _gemini_image_call(prompt, model)
        except urllib.error.HTTPError as exc:
            detail = _http_error_message(exc)
            log(f"DESIGN fail [{model}]: HTTP {exc.code}"
                + (f" - {detail}" if detail else ""))
            if exc.code == 404:
                last_404 = detail
                continue
            msg = ("Design nahi ban paya - Gemini ne HTTP "
                   f"{exc.code} diya"
                   + (f": {detail}" if detail else ""))
            if exc.code == 429:
                msg += (" Lagta hai free wali hadd (quota) abhi "
                        "khatm hai - thodi der baad phir try karo.")
            return msg + "."
        except Exception as exc:
            log(f"DESIGN fail [{model}]: {exc}")
            return (f"Design nahi ban paya: {exc}. Internet "
                    "check karke phir try karo.")
        break
    if img is None and last_404:
        return ("Design nahi ban paya - Gemini par image wala "
                "model mila hi nahi (HTTP 404"
                + (f": {last_404}" if last_404 else "") + "). "
                "Key sahi hai, ye ek baar jaanch lo; thodi der "
                "baad phir try karo.")
    if not img:
        msg = ("Gemini ne jawab to diya lekin usme koi tasveer "
               "nahi mili.")
        if text:
            msg += f" Model ne kaha: {text[:300]}"
        msg += (" Prompt thoda aur saaf karke phir bolo - kya "
                "banna hai, kis naam/rang/style me.")
        return msg
    try:
        dst = _write_path(_design_filename(filename, mime))
    except ValueError as exc:
        return str(exc)
    dst.parent.mkdir(parents=True, exist_ok=True)
    base = dst
    n = 2
    while dst.exists():
        dst = base.with_name(f"{base.stem}-{n}{base.suffix}")
        n += 1
    dst.write_bytes(img)
    log(f"DESIGN ok: {_rel(dst)} ({len(img)} bytes, {mime})")
    return (f"Design ban gaya: {_rel(dst)} "
            f"({len(img) / 1024:.0f} KB). open_file se khol "
            "kar dekh lo - pasand na aaye to badlaav batao, "
            "naya bana dunga.")


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
            UPDATE_URL, headers={"User-Agent": _BROWSER_UA})
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


# --------------------------------------------------------------------------
# Startup khud-jaanch + khud-update (v8.13) - user ki 18:23
# wali maang ka bacha hua hissa: agent engine start hote hi
# (background thread me, bina roke) do kaam khud karta hai:
# 1. Naya version: UPDATE_URL (wahi URL jo 'update karo'
#    command use karta hai) se published agent.py la kar
#    AGENT_VERSION ki tulna. Naya ho to: download, memory me
#    compile-jaanch, purani file agent_backup.py me, phir
#    swap - aur ek one-time notice flag set hota hai: is
#    session ke PEHLE /ask jawab ke upar ek line judti hai
#    (naya version lag gaya, ek restart par chalega). Koi bhi
#    haar (network/compile/likhna) -> purani file ayn waisi,
#    sirf log, KOI notice nahi, agent aaram se chalta hai.
# 2. Sehat jaanch: dimag-test wale probes EK baar chalte hain
#    aur cache ho jate hain. Pehle jawab par EK chhoti sehat
#    line SIRF tab judti hai jab kuch gadbad ho (dimag down /
#    browser setup nahi) - sab theek ho to khamoshi.
# Manual 'update karo' aur 'dimag test karo' bilkul pehle
# jaise hi chalte hain - ye sirf unka khud-bula hua roop hai.
# --------------------------------------------------------------------------

_pending_notice = ""        # one-time update notice (khali = koi nahi)
_pending_health = ""        # one-time sehat line (khali = sab theek)
_session_prefix_used = False
_startup_thread = None
_startup_lock = threading.Lock()


def _startup_auto_update() -> None:
    """Published agent.py se tulna karke naya version ho to
    khud laga do. Kabhi exception bahar nahi aata: haar par
    purani file surakshit, sirf log."""
    global _pending_notice
    try:
        req = urllib.request.Request(
            UPDATE_URL, headers={"User-Agent": _BROWSER_UA})
        with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310
            source = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        log(f"STARTUP-UPDATE: fetch fail ({exc}) - purana "
            "version hi chalega")
        return
    try:
        remote_version = _parse_version(source)
        if remote_version is None:
            log("STARTUP-UPDATE: remote file me version nahi "
                "mila - kuch nahi badla")
            return
        if _version_tuple(remote_version) <= \
                _version_tuple(AGENT_VERSION):
            log(f"STARTUP-UPDATE: pehle se latest "
                f"(v{AGENT_VERSION})")
            return
        try:
            compile(source, "agent.py", "exec")
        except SyntaxError as exc:
            log(f"STARTUP-UPDATE: nayi file compile fail "
                f"({exc}) - kuch nahi badla")
            return
        shutil.copyfile(SELF_FILE, BACKUP_FILE)
        SELF_FILE.write_text(source, encoding="utf-8")
        _pending_notice = (
            f"Ek khaas baat: naya version v{remote_version} "
            "khud lag gaya hai. Engine ko ek baar band karke "
            "'start' se dobara chalao - tab naya version "
            "chalega.")
        log(f"STARTUP-UPDATE: v{AGENT_VERSION} -> "
            f"v{remote_version} lag gaya (notice pehle jawab "
            "par jayegi)")
    except Exception as exc:
        log(f"STARTUP-UPDATE fail ({exc}) - purana version "
            "surakshit hai")


def _dimag_report() -> dict:
    """Dimag-test ki haalat ek dict me (v8.13): wahi probes jo
    tool_dimag_test chalata hai (_groq_selftest /
    _gemini_selftest / browser line), lekin bina text-lines
    ke - startup sehat line isi se banti hai. States:
    none | pass | fail | badkey (Groq/NVIDIA)."""
    nvidia_state = "none"
    if NVIDIA_API_KEY:
        res = _nvidia_selftest()
        if res.startswith("✅"):
            nvidia_state = "pass"
        elif "Invalid API Key" in res or "HTTP 401" in res \
                or "HTTP 403" in res:
            nvidia_state = "badkey"
        else:
            nvidia_state = "fail"
    groq_state = "none"
    if GROQ_API_KEY:
        res = _groq_selftest()
        if res.startswith("✅"):
            groq_state = "pass"
        elif "Invalid API Key" in res:
            groq_state = "badkey"
        else:
            groq_state = "fail"
    gemini_state = "none"
    lite_state = "none"
    if GEMINI_API_KEY:
        primary = GEMINI_MODEL or _MODEL_LITE
        res = _gemini_selftest(primary)
        gemini_state = "pass" if res.startswith("✅") else "fail"
        if _MODEL_LITE != primary:
            res2 = _gemini_selftest(_MODEL_LITE)
            lite_state = "pass" if res2.startswith("✅") else "fail"
        else:
            lite_state = gemini_state
    browser_line = _browser_state_line()
    return {"nvidia": {"state": nvidia_state},
            "groq": {"state": groq_state},
            "gemini": {"state": gemini_state},
            "gemini_lite": {"state": lite_state},
            "browser_setup_done":
                "setup nahi hua hai" not in browser_line}


def _startup_health_line() -> str:
    """Sehat line banao: kuch gadbad ho tabhi line, warna khali
    string (khamoshi). Gemini primary busy/down lekin lite
    chalta ho to line NAHI - wo uski aam haalat hai, roz wahi
    line dekh kar user use nazarandaz karne lagega."""
    try:
        report = _dimag_report()
    except Exception as exc:
        log(f"STARTUP-HEALTH: report fail ({exc})")
        return ""
    nvidia_state = report.get("nvidia", {}).get("state")
    groq_state = report.get("groq", {}).get("state")
    gemini_state = report.get("gemini", {}).get("state")
    lite_state = report.get("gemini_lite", {}).get("state")
    browser_ok = report.get("browser_setup_done")
    problems = []
    if nvidia_state in ("fail", "badkey"):
        problems.append("naya dimag (NVIDIA) abhi kaam nahi kar "
                        "raha - jawab Groq/Gemini se aayenge")
    if groq_state in ("fail", "badkey"):
        problems.append("tez dimag (Groq) abhi kaam nahi kar "
                        "raha - jawab Gemini se aayenge")
    if gemini_state == "fail" and lite_state == "fail":
        problems.append("Gemini ke dono model abhi jawab nahi "
                        "de rahe")
    if gemini_state == "none" and groq_state == "none" \
            and nvidia_state == "none":
        problems.append("dimag ki koi key config me nahi hai - "
                        "free chat band hai")
    if browser_ok is False:
        problems.append("browser setup abhi nahi hua - "
                        "'browser setup karo' bolna, phir "
                        "logged-in sites ka kaam hoga")
    if not problems:
        return ""
    return "Sehat jaanch: " + "; ".join(problems) + "."


def _startup_checks_run() -> None:
    """Background thread ka kaam: pehle khud-update, phir sehat
    jaanch. Dono ke results one-time flags me rehte hain."""
    global _pending_health
    _startup_auto_update()
    line = _startup_health_line()
    if line:
        _pending_health = line
        log(f"STARTUP-HEALTH: {line}")
    else:
        log("STARTUP-HEALTH: sab theek hai (koi line nahi jayegi)")


def _start_startup_checks() -> None:
    """Engine start par khud-jaanch wala thread chalao -
    non-blocking: /ask iska intezaar sirf pehle jawab par,
    wo bhi zyada se zyada ~2 second (neeche dekho)."""
    global _startup_thread
    with _startup_lock:
        if _startup_thread is not None:
            return
        _startup_thread = threading.Thread(
            target=_startup_checks_run, daemon=True,
            name="startup-checks")
        _startup_thread.start()


def _take_session_prefix() -> str:
    """Session ke PEHLE jawab ke liye one-time prefix: update
    notice (ho to) + sehat line (ho to). Sirf ek baar milta
    hai - uske baad hamesha khali. Startup thread abhi chal
    raha ho to yahan zyada se zyada ~2s ruk kar uska result
    le lo (pehla jawab thoda dheere, baaki bilkul aam)."""
    global _session_prefix_used
    with _startup_lock:
        if _session_prefix_used:
            return ""
        _session_prefix_used = True
        thread = _startup_thread
    if thread is not None and thread.is_alive():
        thread.join(timeout=2.0)
    parts = [p for p in (_pending_notice, _pending_health) if p]
    return "\n".join(parts)


_CMD_QUOTE_CHARS = "'\"`‘’“”"


def _norm_command(text: str) -> str:
    """Intercept hue commands ki pehchan ke liye text ka saaf roop
    (v8.8): lowercase, aas-paas ke quotes (', ", `, ‘’, “”) hata
    kar, beech ke extra spaces sameet kar, aakhir ka punctuation
    (., !, ?) hata kar. User aksar hukum quotes ke saath bhej deta
    hai ('browser setup karo') - bare form aur quoted form ab
    EK jaise fire hote hain. Ye sirf command-matching ke liye hai;
    asal message kahin aur ayn waisa hi jata hai."""
    t = (text or "").strip().lower()
    t = t.strip(_CMD_QUOTE_CHARS).strip()
    t = re.sub(r"\s+", " ", t)
    t = t.rstrip(".!?").strip()
    t = t.strip(_CMD_QUOTE_CHARS).strip()
    return t


_UPDATE_TRIGGERS = ("update", "update karo", "agent update", "update agent")


def _is_update_command(low: str) -> bool:
    """User ke 'update' wale hukum ko pehchano (dono modes ke liye)."""
    low = _norm_command(low)
    return low in _UPDATE_TRIGGERS or low.startswith("update ")


_DIMAG_TEST_TRIGGERS = ("dimag test karo", "dimag test", "test karo dimag")


def _is_dimag_test_command(low: str) -> bool:
    """'dimag test karo' - dono dimagon ki asal jaanch wala hukum (v8.6)."""
    low = _norm_command(low)
    return low in _DIMAG_TEST_TRIGGERS


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
    req = urllib.request.Request(
        "http://%s:%d%s" % (host, port, path),
        headers={"User-Agent": _BROWSER_UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
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
_BROWSER_SETUP_OPENERS = ("setup", "khol", "kholo", "open", "chalu",
                          "start")


def _is_browser_setup_command(low: str) -> bool:
    """'browser setup karo' hukum ki pehchan (dono modes ke liye).

    v8.8: exact hukum ke alawa AAM bol-chaal wale roop bhi chalte
    hain - (browser|chrome) ke saath setup/khol/open/chalu/start
    jaisa shabd ho to setup hi mana jata hai ('chrome setup kar
    do', 'browser khol do'). LEKIN message me kisi site ka naam
    ho (facebook, youtube...) to wo NAVIGATION hai, setup nahi -
    'browser me facebook kholo' setup nahi chalata.
    """
    t = _norm_command(low)
    if t in _BROWSER_SETUP_TRIGGERS:
        return True
    words = re.findall(r"[a-z0-9]+", t)
    if not any(w in ("browser", "chrome") for w in words):
        return False
    if any(w in _SITE_MAP for w in words):
        return False
    if "set up" in t:
        return True
    return any(w in _BROWSER_SETUP_OPENERS for w in words)


def _port_occupied(port: int = BROWSER_DEBUG_PORT) -> bool:
    """Port par koi sun raha hai kya - sirf socket connect ki
    jaanch (CDP jawab de ya na de, usse alag). 'Port par kuch
    hai lekin wo CDP nahi hai' wali haalat pakadne ke liye."""
    try:
        with socket.create_connection(("127.0.0.1", port),
                                      timeout=1.5):
            return True
    except Exception:
        return False


def _cdp_looks_like_ours(version) -> bool:
    """/json/version ke jawab se pehchan: Browser naam me
    Chrome/Chromium/Edge ho to ye ek Chrome-parivaar ka CDP
    endpoint hai. Hamare khaas port (9222) par aisa jawab
    asal me agent wale Chrome ka hi hota hai - aam Chrome
    (default profile) is port par jawab deta hi nahi."""
    browser_name = str((version or {}).get("Browser", ""))
    return any(n in browser_name
               for n in ("Chrome", "Chromium", "Edg"))


def _repair_stale_agent_chrome() -> bool:
    """Setup ki KHUD-MARAMMATT (v8.9): port 9222 par koi aisi
    cheez baithi hai jo CDP jawab nahi de rahi. Agar wo hamara
    hi purana, atka hua agent Chrome hai - uske processes ki
    command line me hamari profile (agent_chrome_profile) ka
    path hoga - to SIRF unhi processes ko band karo aur True
    do, taaki setup aage launch kar sake. Kuch aur ho (ya
    Windows na ho, ya kuch bhi gadbad ho) to False - purana
    port-busy message hi jayega.

    Sirf Windows par, PowerShell se process list (stdlib
    subprocess hi). Apni profile path wale Chrome ke alawa
    KISI process ko haath nahi lagta - user ka aam Chrome
    hamesha surakshit hai.
    """
    if platform.system() != "Windows":
        return False
    profile = str(BROWSER_PROFILE_DIR)
    try:
        ps = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive",
             "-Command",
             "Get-CimInstance Win32_Process "
             "-Filter \"Name='chrome.exe'\" | "
             "Select-Object ProcessId, CommandLine | "
             "ConvertTo-Json -Compress"],
            capture_output=True, text=True, timeout=20)
        out = (ps.stdout or "").strip()
        if not out:
            return False
        data = json.loads(out)
        if isinstance(data, dict):
            data = [data]
        pids = []
        for item in data:
            cmd = str((item or {}).get("CommandLine") or "")
            if profile.lower() in cmd.lower():
                try:
                    pids.append(int(item.get("ProcessId")))
                except (TypeError, ValueError):
                    continue
        if not pids:
            return False
        for pid in pids:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                           capture_output=True, text=True, timeout=10)
        log(f"SETUP self-repair: apne purane Chrome ke "
            f"{len(pids)} process band kiye (PIDs: {pids}) - "
            f"ab launch dobara hoga")
        time.sleep(1.0)
        return True
    except Exception as exc:
        log(f"SETUP self-repair fail (purana message hi "
            f"jayega): {exc}")
        return False


def tool_browser_setup() -> str:
    """Agent wala Chrome kholo - dedicated profile ke saath.

    User us window me EK BAAR khud login karega. Password agent
    kabhi nahi mangta, dekhta ya store karta - login hamesha user
    ke haath me hai, aur ye baat jawab me saaf kahi jati hai.

    v8.8 REUSE: pehle se chalta hua APNA Chrome ab rok nahi hai -
    purani koshish wala Chrome khula reh gaya ho to setup usi se
    jud jata hai (dobara launch nahi karta). Pehchan: profile ki
    DevToolsActivePort marker file aur/ya port 9222 par CDP ka
    jawab. Marker ho lekin port band ho (stale marker) to aam
    launch wala rasta chalta hai.

    v8.9 KHUD-MARAMMATT: port par apna hi ATKA hua Chrome ho
    (CDP jawab band, lekin process hamari profile ke saath
    zinda) to setup use khud band karke fresh launch karta hai
    (_repair_stale_agent_chrome) - user ko Task Manager nahi
    kholna padta.
    """
    marker = BROWSER_PROFILE_DIR / "DevToolsActivePort"
    marker_there = marker.is_file()
    try:
        version = http_json(BROWSER_DEBUG_PORT, "/json/version",
                            timeout=2.0)
    except Exception:
        version = None
    if version is not None:
        if marker_there or _cdp_looks_like_ours(version):
            with _browser_lock:
                client, _sess = _browser_connect()
            if client is not None:
                log("BROWSER SETUP: agent wala Chrome pehle se "
                    "khula tha - usi se jud gaya (reuse)")
                return ("Agent wala Chrome pehle se khula tha — "
                        "usi se jud gaya hu. Us window me login "
                        "karke batao, ya seedha kaam bolo.")
            return ("Agent wala Chrome khula to hai, lekin usse "
                    "jud nahi paya. Us window ko band karke "
                    "'browser setup karo' dobara likho.")
        return ("Port 9222 par pehle se kuch aur chal raha hai, "
                "isliye agent wala Chrome nahi khol paya. Use band "
                "karke 'browser setup karo' dobara likho.")
    if _port_occupied():
        # Port par kuch sun raha hai, lekin CDP ka jawab nahi.
        # v8.9 KHUD-MARAMMATT: wo apna hi purana atka hua Chrome
        # ho to use khud band karke aage badho; kuch aur ho to
        # tab hi purana port-busy message.
        if not _repair_stale_agent_chrome() or _port_occupied():
            return ("Port 9222 par pehle se kuch aur chal raha "
                    "hai, isliye agent wala Chrome nahi khol "
                    "paya. Use band karke 'browser setup karo' "
                    "dobara likho.")
        log("BROWSER SETUP: self-repair ke baad port khaali - "
            "ab fresh launch hoga")
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
    pehchan profile folder ki DevToolsActivePort file hai
    (v8.8: marker na ho to bhi hamare port par Chrome-parivaar
    ka CDP jawab hi pehchan maan liya jata hai).
    """
    global _browser_client, _browser_session
    if _browser_client is not None and _browser_session:
        try:
            _browser_client.evaluate(_browser_session, "1")
            return _browser_client, _browser_session
        except Exception:
            _browser_reset()
    try:
        version = http_json(BROWSER_DEBUG_PORT, "/json/version",
                            timeout=3.0)
    except Exception:
        return None, _browser_setup_needed_msg()
    if not (BROWSER_PROFILE_DIR / "DevToolsActivePort").is_file():
        # v8.8: marker file na ho, lekin hamare khaas port par
        # Chrome-parivaar ka CDP jawab aa raha ho, to wahi agent
        # wala Chrome hai (purani koshish wala chalta hua Chrome
        # aksar yahi haalat me milta hai) - usi ko qabool karo.
        if not _cdp_looks_like_ours(version):
            return None, ("Port 9222 par kuch chal raha hai, lekin wo "
                          "agent wala Chrome nahi lagta - uski profile "
                          "(agent_chrome_profile) yahan nahi mili. Chat "
                          "me likho: 'browser setup karo' - sahi Chrome "
                          "wahi se khulega.")
        log("BROWSER: marker file nahi mili, lekin port 9222 par "
            "Chrome ka CDP jawab mil raha hai - usi ko agent wala "
            "Chrome maan kar jud raha hu")
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


def _browser_is_connected() -> bool:
    """Browser haath is samay sach me judaa hua hai kya (v8.8) -
    cached connection ko halki jaanch (evaluate '1') se parkho;
    kharab nikle to reset karke False. Naya connection KHUD nahi
    banata - ye sirf 'abhi judaa hai ya nahi' batata hai (site
    commands isse tay karte hain ki kholna agent wale Chrome me
    hai ya aam browser me)."""
    with _browser_lock:
        if _browser_client is not None and _browser_session:
            try:
                _browser_client.evaluate(_browser_session, "1")
                return True
            except Exception:
                _browser_reset()
    return False


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
# Screen haath (v8.15) - kisi bhi Windows software ke andar kaam:
# screen dekho (screenshot), cheez dhoondo (vision), mouse
# ghumao/click/scroll karo, type karo, keys dabao. Sirf stdlib
# ctypes (user32/gdi32) - koi pip nahi. Windows-only: dusre OS
# par tools saaf mana karte hain. Har action log hota hai;
# type_text ka CONTENT log me kabhi nahi jata (sirf lambai) -
# run_tool wali aam TOOL line me bhi uske liye khaas redaction
# hai. Kaam hamesha verified loop me hota hai: screenshot ->
# ek action -> screenshot -> jaanch (prompt aur 'screen-haath'
# skill me yahi tareeka likha hai).
# --------------------------------------------------------------------------

_SCREEN_MAX_WIDTH = 1280  # vision ke liye screenshot ki zyada se zyada chaudai
_SCREEN_SHOT_NAME = "screen.png"
_SCREENSHOT_SIZE = None  # (asal chaudai, unchai) - aakhri screenshot ki


def _screen_state() -> str:
    """Screen haath ki haalat: 'ok' | 'off' (config) | 'notwin'."""
    if not SCREEN_HAND:
        return "off"
    if os.name != "nt":
        return "notwin"
    return "ok"


def _screen_guard():
    """Screen tool chal sakta ho to None, warna mana wala jawab."""
    state = _screen_state()
    if state == "ok":
        return None
    if state == "off":
        return ("Screen haath config se band hai (SCREEN_HAND=off). "
                "Chalu karna ho to config.env me SCREEN_HAND=on "
                "likh do - main config khud dobara padh lunga, "
                "restart nahi chahiye.")
    return ("Screen haath sirf Windows par chalta hai - is "
            "computer par wo uplabdh nahi hai.")


def _screen_state_line() -> str:
    """Dimag test ke liye screen haath ki haalat (v8.15) - sirf
    pehchan: na screenshot banta hai, na mouse hilta hai."""
    state = _screen_state()
    if state == "ok":
        return "Screen haath: taiyaar hai ✅"
    if state == "off":
        return "Screen haath: band hai (config SCREEN_HAND=off)"
    return "Screen haath: is OS par uplabdh nahi (sirf Windows)"


# --- shuddha hisse (bina Win32 ke - har OS par test ho sakte hain) ---

def _png_bytes_from_bgra(width: int, height: int, bgra: bytes) -> bytes:
    """BGRA pixels (upar se neeche kram me rows) se PNG bytes
    banao - sirf zlib + struct. Har row: filter byte 0 + RGBA
    bytes. GDI wale alpha ko pakka 255 rakha hai (screen capture
    ka alpha aksar 0 aata hai, usse photo kaali dikhegi)."""
    stride = width * 4
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        row = bgra[y * stride:(y + 1) * stride]
        rgba = bytearray(len(row))
        rgba[0::4] = row[2::4]
        rgba[1::4] = row[1::4]
        rgba[2::4] = row[0::4]
        rgba[3::4] = b"\xff" * width
        raw += rgba

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data)
                              & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + chunk(b"IEND", b""))


def _downscale_bgra(width: int, height: int, bgra: bytes,
                    max_width: int = _SCREEN_MAX_WIDTH):
    """Screenshot ko vision ke liye chhota karo (nearest
    neighbour). Pehle se chhota ho to ayn waisa hi."""
    if width <= max_width or width == 0:
        return width, height, bgra
    new_w = max_width
    new_h = max(1, round(height * max_width / width))
    out = bytearray(new_w * new_h * 4)
    for y in range(new_h):
        sy = (y * height) // new_h
        src_row = sy * width * 4
        dst_row = y * new_w * 4
        for x in range(new_w):
            sx = (x * width) // new_w
            si = src_row + sx * 4
            di = dst_row + x * 4
            out[di:di + 4] = bgra[si:si + 4]
    return new_w, new_h, bytes(out)


def _norm_to_pixel(nx, ny, width: int, height: int):
    """Vision ke 0-1000 wale coordinates ko asal screen pixels
    me badlo (kinare par seema ke andar rakho)."""
    nx = max(0.0, min(1000.0, float(nx)))
    ny = max(0.0, min(1000.0, float(ny)))
    x = int(round(nx / 1000.0 * (width - 1))) if width > 1 else 0
    y = int(round(ny / 1000.0 * (height - 1))) if height > 1 else 0
    return x, y


_VK_NAMED = {
    "enter": 0x0D, "return": 0x0D, "esc": 0x1B, "escape": 0x1B,
    "tab": 0x09, "space": 0x20, "backspace": 0x08, "delete": 0x2E,
    "del": 0x2E, "insert": 0x2D, "home": 0x24, "end": 0x23,
    "pageup": 0x21, "pagedown": 0x22, "up": 0x26, "down": 0x28,
    "left": 0x25, "right": 0x27, "capslock": 0x14,
    "printscreen": 0x2C,
}
for _fnum in range(1, 13):
    _VK_NAMED[f"f{_fnum}"] = 0x70 + _fnum - 1
_VK_MODS = {"ctrl": 0x11, "control": 0x11, "alt": 0x12,
            "shift": 0x10, "win": 0x5B, "windows": 0x5B}


def _parse_key_combo(combo: str):
    """'ctrl+s' / 'alt+tab' / 'enter' ko virtual-key codes ki
    list me badlo (dabane ke kram me). Samajh na aaye to None."""
    parts = [p.strip().lower()
             for p in (combo or "").split("+") if p.strip()]
    if not parts:
        return None
    vks = []
    for part in parts[:-1]:
        vk = _VK_MODS.get(part)
        if vk is None:
            return None
        vks.append(vk)
    last = parts[-1]
    if last in _VK_NAMED:
        vks.append(_VK_NAMED[last])
    elif last in _VK_MODS:
        vks.append(_VK_MODS[last])
    elif len(last) == 1 and last.isalnum():
        vks.append(ord(last.upper()))
    else:
        return None
    return vks


def _as_int(value, default=0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _as_bool(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes")
    return bool(value)


# --- Win32 layer (sirf Windows par bulta hai; tests in
# wrappers ko mock kar dete hain, isliye ctypes ka saara bojh
# inhi chhote functions me band hai) ---

def _win_screen_size():
    """Asal screen size (pixels) - DPI-aware hone ki koshish ke
    saath, taaki coordinates asal pixels se milein."""
    import ctypes
    user32 = ctypes.windll.user32
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            user32.SetProcessDPIAware()
        except Exception:
            pass
    return (int(user32.GetSystemMetrics(0)),
            int(user32.GetSystemMetrics(1)))


def _win_capture_pixels():
    """Poori screen ke pixels: (width, height, BGRA bytes).
    GDI: screen DC -> memory bitmap -> BitBlt -> GetDIBits
    (32-bit, upar-se-neeche kram)."""
    import ctypes
    from ctypes import wintypes

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [("biSize", wintypes.DWORD),
                    ("biWidth", wintypes.LONG),
                    ("biHeight", wintypes.LONG),
                    ("biPlanes", wintypes.WORD),
                    ("biBitCount", wintypes.WORD),
                    ("biCompression", wintypes.DWORD),
                    ("biSizeImage", wintypes.DWORD),
                    ("biXPelsPerMeter", wintypes.LONG),
                    ("biYPelsPerMeter", wintypes.LONG),
                    ("biClrUsed", wintypes.DWORD),
                    ("biClrImportant", wintypes.DWORD)]

    class BITMAPINFO(ctypes.Structure):
        _fields_ = [("bmiHeader", BITMAPINFOHEADER),
                    ("bmiColors", wintypes.DWORD * 1)]

    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    for fn in (user32.GetDC, gdi32.CreateCompatibleDC,
               gdi32.CreateCompatibleBitmap, gdi32.SelectObject):
        fn.restype = ctypes.c_void_p
    width, height = _win_screen_size()
    hdc_screen = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    hbmp = gdi32.CreateCompatibleBitmap(hdc_screen, width, height)
    try:
        gdi32.SelectObject(hdc_mem, hbmp)
        gdi32.BitBlt(hdc_mem, 0, 0, width, height, hdc_screen, 0, 0,
                     0x00CC0020)  # SRCCOPY
        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = width
        bmi.bmiHeader.biHeight = -height  # negative = upar se neeche
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = 0  # BI_RGB
        buf = ctypes.create_string_buffer(width * height * 4)
        got = gdi32.GetDIBits(hdc_mem, hbmp, 0, height, buf,
                              ctypes.byref(bmi), 0)  # DIB_RGB_COLORS
        if not got:
            raise RuntimeError("GetDIBits se pixels nahi mile")
        return width, height, buf.raw
    finally:
        gdi32.DeleteObject(hbmp)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(0, hdc_screen)


_MOUSEEVENTF_MOVE = 0x0001
_MOUSEEVENTF_LEFTDOWN = 0x0002
_MOUSEEVENTF_LEFTUP = 0x0004
_MOUSEEVENTF_RIGHTDOWN = 0x0008
_MOUSEEVENTF_RIGHTUP = 0x0010
_MOUSEEVENTF_WHEEL = 0x0800
_MOUSEEVENTF_ABSOLUTE = 0x8000
_KEYEVENTF_KEYUP = 0x0002
_KEYEVENTF_UNICODE = 0x0004
_WHEEL_DELTA = 120


def _win_input_structs():
    """SendInput ke ctypes structures (lazy - sirf Windows par
    bante hain). INPUT ka size x64 par bilkul sahi (40 bytes)
    rakha hai: type (4) + padding (4) + union (32)."""
    import ctypes
    from ctypes import wintypes

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                    ("mouseData", wintypes.DWORD),
                    ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.c_void_p)]

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", wintypes.WORD),
                    ("wScan", wintypes.WORD),
                    ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.c_void_p)]

    class INPUT_UNION(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]

    class INPUT(ctypes.Structure):
        _anonymous_ = ("u",)
        _fields_ = [("type", wintypes.DWORD), ("u", INPUT_UNION)]

    return INPUT, MOUSEINPUT, KEYBDINPUT


def _win_send_inputs(inputs) -> None:
    import ctypes
    if not inputs:
        return
    arr = (inputs[0].__class__ * len(inputs))(*inputs)
    sent = ctypes.windll.user32.SendInput(
        len(inputs), arr, ctypes.sizeof(arr[0]))
    if sent != len(inputs):
        raise RuntimeError(f"SendInput ne {sent}/{len(inputs)} "
                           "events bheje")


def _win_mouse_move(x: int, y: int) -> None:
    INPUT, MOUSEINPUT, _KB = _win_input_structs()
    width, height = _win_screen_size()
    nx = int(round(65535 * x / max(1, width - 1)))
    ny = int(round(65535 * y / max(1, height - 1)))
    inp = INPUT()
    inp.type = 0  # INPUT_MOUSE
    inp.mi = MOUSEINPUT(nx, ny, 0,
                        _MOUSEEVENTF_MOVE | _MOUSEEVENTF_ABSOLUTE,
                        0, None)
    _win_send_inputs([inp])


def _win_mouse_click(x: int, y: int, button: str = "left",
                     double: bool = False) -> None:
    INPUT, MOUSEINPUT, _KB = _win_input_structs()
    _win_mouse_move(x, y)
    time.sleep(0.05)
    if button == "right":
        down, up = _MOUSEEVENTF_RIGHTDOWN, _MOUSEEVENTF_RIGHTUP
    else:
        down, up = _MOUSEEVENTF_LEFTDOWN, _MOUSEEVENTF_LEFTUP

    def one_click():
        d = INPUT()
        d.type = 0
        d.mi = MOUSEINPUT(0, 0, 0, down, 0, None)
        u = INPUT()
        u.type = 0
        u.mi = MOUSEINPUT(0, 0, 0, up, 0, None)
        _win_send_inputs([d, u])

    one_click()
    if double:
        time.sleep(0.08)
        one_click()


def _win_mouse_scroll(amount: int) -> None:
    """Mouse wheel: amount = notches (positive = upar)."""
    INPUT, MOUSEINPUT, _KB = _win_input_structs()
    inp = INPUT()
    inp.type = 0
    inp.mi = MOUSEINPUT(0, 0, (amount * _WHEEL_DELTA) & 0xFFFFFFFF,
                        _MOUSEEVENTF_WHEEL, 0, None)
    _win_send_inputs([inp])


def _win_type_text(text: str) -> None:
    """Text ko Unicode keyboard events se type karo (focused
    jagah par jata hai). UTF-16 code units par chalta hai,
    taaki Hindi/emoji jaise akshar bhi sahi jayein."""
    INPUT, _MI, KEYBDINPUT = _win_input_structs()
    data = text.encode("utf-16-le")
    units = struct.unpack(f"<{len(data) // 2}H", data)
    events = []
    for unit in units:
        d = INPUT()
        d.type = 1  # INPUT_KEYBOARD
        d.ki = KEYBDINPUT(0, unit, _KEYEVENTF_UNICODE, 0, None)
        u = INPUT()
        u.type = 1
        u.ki = KEYBDINPUT(0, unit,
                          _KEYEVENTF_UNICODE | _KEYEVENTF_KEYUP,
                          0, None)
        events += [d, u]
    for i in range(0, len(events), 200):
        _win_send_inputs(events[i:i + 200])


def _win_press_keys(vks) -> None:
    """VK codes ko kram se dabao: pehle saare neeche (modifiers
    pehle aate hain), phir ulte kram me upar."""
    INPUT, _MI, KEYBDINPUT = _win_input_structs()
    events = []
    for vk in vks:
        e = INPUT()
        e.type = 1
        e.ki = KEYBDINPUT(vk, 0, 0, 0, None)
        events.append(e)
    for vk in reversed(vks):
        e = INPUT()
        e.type = 1
        e.ki = KEYBDINPUT(vk, 0, _KEYEVENTF_KEYUP, 0, None)
        events.append(e)
    _win_send_inputs(events)


# --- screen tools ---

def _take_screenshot():
    """Screenshot lo aur work/ me PNG rakho:
    (path, asal_w, asal_h, vision_w, vision_h). Haar par
    exception - caller saaf jawab me badalta hai."""
    global _SCREENSHOT_SIZE
    width, height, bgra = _win_capture_pixels()
    small_w, small_h, small = _downscale_bgra(width, height, bgra)
    path = WORK_DIR / _SCREEN_SHOT_NAME
    path.write_bytes(_png_bytes_from_bgra(small_w, small_h, small))
    _SCREENSHOT_SIZE = (width, height)
    return path, width, height, small_w, small_h


def tool_screen_shot() -> str:
    """Poori screen ki photo lo (work/screen.png)."""
    guard = _screen_guard()
    if guard:
        return guard
    try:
        path, w, h, sw, sh = _take_screenshot()
    except Exception as exc:
        log(f"SCREEN shot fail: {exc}")
        return f"Screenshot nahi le paya: {exc}"
    log(f"SCREEN shot ok: screen {w}x{h}, vision {sw}x{sh}")
    return (f"Screenshot le liya: {_rel(path)} (screen {w}x{h}). "
            "Uspar koi cheez dhoondni ho to screen_locate chalao; "
            "click ke coordinates hamesha asal screen ke pixels "
            "me hote hain.")


def _vision_ask(b64: str, mime: str, prompt: str) -> str:
    """Screenshot par vision ladder se sawal: pehle Gemini
    vision, fail/khaali par Glimmer (v8.14 wala
    _nvidia_vision_call). Jawab ka text; koi dimag na chale to
    khali string."""
    if GEMINI_API_KEY:
        parts = [{"inline_data": {"mime_type": mime, "data": b64}},
                 {"text": prompt}]
        try:
            text = _gemini_video_call(parts)
            if text:
                return text
        except Exception as exc:
            log(f"SCREEN vision Gemini fail: {exc}")
    if NVIDIA_API_KEY:
        try:
            return _nvidia_vision_call(b64, mime, prompt)
        except Exception as exc:
            log(f"SCREEN vision Glimmer fail: {exc}")
    return ""


_LOCATE_PROMPT = (
    "Is screenshot me ye cheez dhoondo: \"{target}\". Wo saaf "
    "dikh rahi ho to SIRF ek JSON object me jawab do: "
    "{{\"x\": <0-1000>, \"y\": <0-1000>}} - x aur y us cheez ke "
    "BEECH ke bindu hain (0 = bilkul kinara, 1000 = dusra "
    "kinara). Na dikhe to SIRF ye likho: NOT_FOUND. Aur kuch "
    "bhi mat likho.")


def _locate_coords(b64: str, width: int, height: int, target: str):
    """Vision se target ke asal pixel coordinates: (x, y), ya
    None (na mila). Vision hi na chale to RuntimeError."""
    text = _vision_ask(b64, "image/png",
                       _LOCATE_PROMPT.format(target=target))
    if not text:
        raise RuntimeError("vision wale dimag se jawab nahi aaya")
    m = re.search(r'"x"\s*:\s*(\d+(?:\.\d+)?)\D{0,20}?'
                  r'"y"\s*:\s*(\d+(?:\.\d+)?)', text)
    if not m:
        return None
    return _norm_to_pixel(float(m.group(1)), float(m.group(2)),
                          width, height)


def tool_screen_locate(target: str) -> str:
    """Screen par koi cheez (button/text/icon) dhoond kar uske
    beech ke pixel coordinates do."""
    guard = _screen_guard()
    if guard:
        return guard
    target = (target or "").strip()
    if not target:
        return ("Kya dhoondhu - target to batao (button, text ya "
                "icon ka chhota varnan).")
    if not GEMINI_API_KEY and not NVIDIA_API_KEY:
        return ("Screen par cheez dhoondne ke liye vision wali "
                "key chahiye - config me GEMINI_API_KEY aur "
                "NVIDIA_API_KEY dono hi nahi hain.")
    try:
        path, w, h, sw, sh = _take_screenshot()
    except Exception as exc:
        log(f"SCREEN locate: screenshot fail: {exc}")
        return f"Screenshot nahi le paya: {exc}"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    try:
        found = _locate_coords(b64, w, h, target)
    except Exception as exc:
        log(f"SCREEN locate fail: {exc}")
        return (f"'{target}' dhoond nahi paya - {exc}. Thodi der "
                "baad phir try karo.")
    if found is None:
        log(f"SCREEN locate: '{target}' nahi mila")
        return (f"'{target}' screen par nahi mila. Taaza "
                f"screenshot {_rel(path)} me hai - varnan badal "
                "kar phir try karo, ya pehle screen_shot + "
                "see_image se khud dekho ki screen par hai kya.")
    x, y = found
    log(f"SCREEN locate: '{target}' -> ({x}, {y})")
    return (f"'{target}' mila: beech ke coordinates ({x}, {y}) "
            f"(screen {w}x{h}). Click karna ho to "
            f"mouse_click(x={x}, y={y}) chalao - usse pehle "
            "screenshot taaza ho, ye pakka kar lo.")


def tool_mouse_move(x=0, y=0) -> str:
    """Mouse ko pixel coordinates par le jao."""
    guard = _screen_guard()
    if guard:
        return guard
    x, y = _as_int(x), _as_int(y)
    try:
        _win_mouse_move(x, y)
    except Exception as exc:
        log(f"SCREEN mouse_move fail: {exc}")
        return f"Mouse nahi ghuma paya: {exc}"
    log(f"SCREEN mouse_move -> ({x}, {y})")
    time.sleep(0.15)
    return f"Mouse ({x}, {y}) par le gaya."


def tool_mouse_click(x=0, y=0, button: str = "left",
                     double=False) -> str:
    """Pixel coordinates par click (left/right, single/double)."""
    guard = _screen_guard()
    if guard:
        return guard
    x, y = _as_int(x), _as_int(y)
    button = (button or "left").strip().lower()
    if button not in ("left", "right"):
        return "Button sirf 'left' ya 'right' hota hai."
    double = _as_bool(double)
    try:
        _win_mouse_click(x, y, button, double)
    except Exception as exc:
        log(f"SCREEN mouse_click fail: {exc}")
        return f"Click nahi kar paya: {exc}"
    kind = "Double-click" if double else "Click"
    log(f"SCREEN mouse_click {button}"
        f"{' x2' if double else ''} -> ({x}, {y})")
    time.sleep(0.35)
    return (f"{kind} kar diya ({x}, {y}, {button}). Ab "
            "screen_shot se verify kar lo ki wahi hua jo "
            "chahiye tha.")


def tool_mouse_scroll(amount=-3) -> str:
    """Mouse wheel scroll (positive = upar, negative = neeche)."""
    guard = _screen_guard()
    if guard:
        return guard
    amount = max(-50, min(50, _as_int(amount, -3)))
    try:
        _win_mouse_scroll(amount)
    except Exception as exc:
        log(f"SCREEN mouse_scroll fail: {exc}")
        return f"Scroll nahi kar paya: {exc}"
    log(f"SCREEN mouse_scroll {amount}")
    time.sleep(0.25)
    return (f"Scroll kar diya ({amount}). screen_shot se dekho "
            "kahan pahunche.")


def tool_type_text(text: str = "") -> str:
    """Focused jagah par text type karo. DHYAAN: is text ka
    content log me KABHI nahi jata - sirf lambai jati hai
    (password jaisi cheez galti se type ho jaye to bhi log me
    na rahe). Password type karna prompt me sakht mana hai."""
    guard = _screen_guard()
    if guard:
        return guard
    text = text if isinstance(text, str) else str(text or "")
    if not text:
        return "Kya type karu - text to do."
    try:
        _win_type_text(text)
    except Exception as exc:
        log(f"SCREEN type_text fail ({len(text)} akshar): {exc}")
        return f"Type nahi kar paya: {exc}"
    log(f"SCREEN type_text: {len(text)} akshar "
        "(content suraksha ke liye log nahi hota)")
    time.sleep(0.2)
    return (f"{len(text)} akshar type kar diye (focused jagah "
            "par). screen_shot se verify kar lo.")


def tool_press_key(combo: str = "") -> str:
    """Ek key ya combo dabao ('enter', 'ctrl+s', 'alt+tab')."""
    guard = _screen_guard()
    if guard:
        return guard
    vks = _parse_key_combo(combo)
    if vks is None:
        return (f"Ye key/combo samajh nahi aaya: '{combo}'. "
                "Chalte hain jaise: enter, esc, tab, space, "
                "backspace, delete, home, end, up/down/left/right, "
                "f1-f12, aur '+' wale combo: ctrl+s, ctrl+c, "
                "ctrl+v, alt+tab, alt+f4, ctrl+shift+esc.")
    try:
        _win_press_keys(vks)
    except Exception as exc:
        log(f"SCREEN press_key fail: {exc}")
        return f"Key nahi daba paya: {exc}"
    log(f"SCREEN press_key: {combo}")
    time.sleep(0.25)
    return (f"Key daba di: {combo}. screen_shot se asar verify "
            "kar lo.")


_PLAN_PROMPT = (
    "Tum screen par kaam karne wale haath ko EK kadam bata rahe "
    "ho. Kaam: \"{instruction}\". Is screenshot ko dekho aur "
    "SIRF ek JSON object me jawab do, inme se ek shakal me:\n"
    "{{\"action\": \"click\", \"target\": \"<dikhai dene wali "
    "cheez ka varnan>\"}}\n"
    "{{\"action\": \"type\", \"text\": \"<jo type karna hai>\"}}\n"
    "{{\"action\": \"key\", \"combo\": \"<jaise enter ya "
    "ctrl+s>\"}}\n"
    "{{\"action\": \"scroll\", \"amount\": -3}}\n"
    "{{\"action\": \"done\", \"note\": \"<kaam ho gaya - ek "
    "line>\"}}\n"
    "{{\"action\": \"stop\", \"reason\": \"<rukne ki wajah>\"}}\n"
    "Screen par login, password wala khana, CAPTCHA ya 2FA "
    "dikhe to action hamesha \"stop\" rakho aur reason me wahi "
    "likho. Password kabhi type mat karna. Ek baar me sirf EK "
    "kadam - sabse chhota agla kadam chuno.")


def _plan_step(b64: str, instruction: str) -> dict:
    """Vision se agla ek kadam (dict, action ke saath). Jawab
    samajh na aaye to {'action': 'stop', ...}."""
    text = _vision_ask(b64, "image/png",
                       _PLAN_PROMPT.format(instruction=instruction))
    if not text:
        raise RuntimeError("vision wale dimag se jawab nahi aaya")
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try:
            data = json.loads(m.group(0))
            if isinstance(data, dict) and data.get("action"):
                return data
        except Exception:
            pass
    return {"action": "stop",
            "reason": "vision ka jawab samajh nahi aaya"}


def tool_screen_do(instruction: str) -> str:
    """Screen par EK chhota kadam: screenshot -> vision se plan
    -> ek action -> screenshot se jaanch. Poora kaam ek call me
    kabhi nahi hota - har call ek kadam hai, taaki har kadam
    verify ho sake aur galti par wahin ruka ja sake."""
    guard = _screen_guard()
    if guard:
        return guard
    instruction = (instruction or "").strip()
    if not instruction:
        return "Kya karna hai - instruction to do."
    if not GEMINI_API_KEY and not NVIDIA_API_KEY:
        return ("Screen par khud kadam plan karne ke liye vision "
                "wali key chahiye - config me GEMINI_API_KEY aur "
                "NVIDIA_API_KEY dono hi nahi hain.")
    try:
        path, w, h, sw, sh = _take_screenshot()
    except Exception as exc:
        return f"Screenshot nahi le paya: {exc}"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    try:
        plan = _plan_step(b64, instruction)
    except Exception as exc:
        log(f"SCREEN do plan fail: {exc}")
        return f"Kadam plan nahi kar paya - {exc}"
    action = str(plan.get("action", "")).lower()
    log(f"SCREEN do: '{instruction}' -> plan {action}")
    if action == "stop":
        return ("Ruk gaya: "
                + str(plan.get("reason")
                      or "vision ne rukne ko kaha")
                + ". Screen usi halat me khuli hai - wajah door "
                "ho jaye to wahi kadam phir se bolo, main yahin "
                "se aage badhunga.")
    if action == "done":
        return ("Vision ke hisaab se kaam ho gaya hai: "
                + str(plan.get("note") or "")
                + f" Pakka karne ke liye screenshot {_rel(path)} "
                "me hai.")
    if action == "click":
        target = str(plan.get("target") or "").strip()
        if not target:
            return ("Plan me click aaya lekin target nahi - "
                    "kadam nahi uthaya.")
        try:
            found = _locate_coords(b64, w, h, target)
        except Exception as exc:
            return f"Click ka target dhoond nahi paya - {exc}"
        if found is None:
            return (f"Click ka target '{target}' screen par "
                    "nahi mila - kadam nahi uthaya. screen_shot "
                    "se halat dekho.")
        x, y = found
        try:
            _win_mouse_click(x, y, "left", False)
        except Exception as exc:
            return f"Click nahi kar paya: {exc}"
        did = f"'{target}' par click ({x}, {y})"
    elif action == "type":
        text = str(plan.get("text") or "")
        if not text:
            return ("Plan me type aaya lekin text khali hai - "
                    "kadam nahi uthaya.")
        try:
            _win_type_text(text)
        except Exception as exc:
            return f"Type nahi kar paya: {exc}"
        did = f"{len(text)} akshar type kiye"
    elif action == "key":
        combo = str(plan.get("combo") or "")
        vks = _parse_key_combo(combo)
        if vks is None:
            return (f"Plan wali key samajh nahi aayi: '{combo}' "
                    "- kadam nahi uthaya.")
        try:
            _win_press_keys(vks)
        except Exception as exc:
            return f"Key nahi daba paya: {exc}"
        did = f"key dabayi: {combo}"
    elif action == "scroll":
        amount = max(-50, min(50, _as_int(plan.get("amount"), -3)))
        try:
            _win_mouse_scroll(amount)
        except Exception as exc:
            return f"Scroll nahi kar paya: {exc}"
        did = f"scroll kiya ({amount})"
    else:
        return (f"Plan me anjaan action aaya: '{action}' - "
                "kadam nahi uthaya.")
    time.sleep(0.4)
    try:
        path2, _w2, _h2, _sw2, _sh2 = _take_screenshot()
        shot_note = f"Naya screenshot: {_rel(path2)}"
    except Exception:
        shot_note = ("Naya screenshot nahi ban paya - screen_shot "
                     "alag se chalao.")
    log(f"SCREEN do kadam pura: {did}")
    return (f"Ek kadam ho gaya: {did}. {shot_note}. Agla kadam "
            "chahiye to screen_do phir chalao ya khud tools se "
            "aage badho.")


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

# v8.9 SAWAL-GUARD: ye shabd/phrase dikhte hi message ek SAWAL
# ya haalat-jaanch hai, site kholne ka hukum NAHI - chahe usme
# site ka naam aur 'open' dono hi kyun na hon. Asal PC par yahi
# hua tha: "dekho ki kay facebook open hai hai to kis name se
# banao mujhe" (sawal) par matcher do baar "Facebook khol diya"
# bol gaya tha.
_QUESTION_WORDS = {"kya", "kay", "kis", "kaun", "dekho", "dekh"}
_STATE_PHRASES = ("open hai", "khula hai", "khuli hai")


def _looks_like_question(message: str, text: str, words) -> bool:
    """Message site kholne ka hukum hai ya usi site ke baare me
    SAWAL/haalat-jaanch - ye parkho (v8.9). Koi EK bhi nishaani
    mile to sawal mana jata hai aur instant command NAHI chalta
    (baat dimag ke paas jati hai, jo browser_read karke jawab
    dega):

    - aakhir me '?' (normalisation use kaat deta hai, isliye
      asal message par jaanch hoti hai)
    - sawal wale shabd: kya/kay (typo), kis, kaun, dekho/dekh
    - batao/btao/bata wale shabd ('bata' se shuru)
    - 'check karo' ki jodi
    - haalat wale phrase: 'open hai', 'khula hai', 'khuli hai'
      ('open karo' hukum hai, 'open hai' haalat hai)
    """
    raw = (message or "").strip().rstrip(_CMD_QUOTE_CHARS).strip()
    if raw.endswith("?"):
        return True
    wset = set(words)
    if wset & _QUESTION_WORDS:
        return True
    if any(w.startswith("bata") for w in words):
        return True
    if "check" in wset and "karo" in wset:
        return True
    return any(p in text for p in _STATE_PHRASES)


def _site_open_command(message: str):
    """'facebook kholo' / 'open youtube' jaisa hukum ho to site ka
    (label, url) return karo, warna None.

    Pehchan shabdon (tokens) par hoti hai: ek kholne wala shabd
    (kholo/khol/open/chalao...) AUR ek site ka naam - dono hon tabhi.
    Sirf site ka naam (jaise 'facebook par post karo') ismein nahi
    fasna chahiye, wo Gemini ke paas jayega.

    v8.8 VERB-ATTACHMENT: jumle me KAI site naam hon to jeetta wahi
    hai jo kisi open-verb ke SABSE PAAS ho - 'gmail login hai tum
    youtube open karo usme' me hukum youtube ka hai, gmail sirf
    bayaan hai (purana matcher pehla naam utha kar gmail khol deta
    tha - asal PC par yahi galti hui thi).

    v8.9 SAWAL-GUARD: message sawal/haalat-jaanch ho (kya/kay,
    dekho, batao, kis, 'open hai', aakhir me '?'...) to hukum
    bilkul NAHI mana jata - dekho _looks_like_question.
    """
    text = _norm_command(message)
    tokens = [(m.group(0), m.start())
              for m in re.finditer(r"[a-z0-9]+", text)]
    if _looks_like_question(message, text, [w for w, _ in tokens]):
        return None
    verb_pos = [pos for w, pos in tokens if w in _OPEN_WORDS]
    if not verb_pos:
        return None
    sites = [(w, pos) for w, pos in tokens if w in _SITE_MAP]
    if not sites:
        return None
    if len(sites) == 1:
        return _SITE_MAP[sites[0][0]]
    best = min(sites,
               key=lambda sp: min(abs(sp[1] - vp) for vp in verb_pos))
    return _SITE_MAP[best[0]]


def _site_open_reply(message: str):
    """Site hukum chala kar Hinglish jawab do; hukum na ho to None.

    v8.8: browser haath judaa hua ho to site AGENT wale Chrome me
    khulti hai (browser_open) - wahi Chrome jisme user login hai.
    Judaa na ho to purana rasta: aam browser me open_url.

    v8.9: judaa na ho, lekin setup ho chuka ho (profile ki
    marker file maujud) to seedha open_url par girne se pehle
    EK halki connect koshish hoti hai - asal PC par yahi hua
    tha: naya engine process chalu hua, uski session cache
    khaali thi, aur site aam browser me khul gayi jabki agent
    wala Chrome saamne khula khada tha. Marker hi na ho
    (setup kabhi hua hi nahi) to koi koshish nahi - seedha
    purana open_url rasta.
    """
    found = _site_open_command(message)
    if found is None:
        return None
    label, url = found
    if _browser_is_connected():
        result = run_tool("browser_open", {"url": url})
        if result.startswith("Agent wale Chrome me page khul gaya"):
            return f"{label} agent wale Chrome me khol diya hai."
        return result
    if (BROWSER_PROFILE_DIR / "DevToolsActivePort").is_file():
        with _browser_lock:
            client, _sess = _browser_connect()
        if client is not None:
            log("SITE OPEN: agent wale Chrome se khud jud kar "
                "usi me site kholi (v8.9 connect koshish)")
            result = run_tool("browser_open", {"url": url})
            if result.startswith("Agent wale Chrome me page "
                                  "khul gaya"):
                return f"{label} agent wale Chrome me khol diya hai."
            return result
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
    "purani_baat_dhundho": tool_purani_baat_dhundho,
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
    "design_banao": tool_design_banao,
    "open_file": tool_open_file,
    "extract_zip": tool_extract_zip,
    "screen_shot": tool_screen_shot,
    "screen_locate": tool_screen_locate,
    "screen_do": tool_screen_do,
    "mouse_move": tool_mouse_move,
    "mouse_click": tool_mouse_click,
    "mouse_scroll": tool_mouse_scroll,
    "type_text": tool_type_text,
    "press_key": tool_press_key,
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
    log_args = args or {}
    if name == "type_text" and "text" in log_args:
        # v8.15: type_text ka content log me KABHI nahi jata -
        # sirf lambai (jo type hua wo password jaisa hassas bhi
        # ho sakta hai; agent password type karta hi nahi, par
        # galti se aa jaye to bhi log saaf rahe).
        log_args = {**log_args,
                    "text": f"<{len(str(log_args['text']))} akshar>"}
    log(f"TOOL {name} args={json.dumps(log_args, ensure_ascii=False)[:300]} -> {str(result)[:120]}")
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
  kya seekha                  - jo niyam maine tumse seekhe hain
                                (Seekhe hue niyam) number ke saath
  purani baatein              - meri diary ki aakhri 10 baatein
                                tareekh ke saath (kab kya bola tha)
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
    # v8.8: quotes/punctuation saaf wala roop bhi exact-match
    # commands ke liye qabool hai ('time batao' quotes ke saath
    # bhi chalega) - regex wale commands ayn raw text par hi
    # chalte hain (unme file ke naam hote hain).
    nlow = _norm_command(text)

    if low in ("help", "madad", "?") or nlow in ("help", "madad"):
        return HELP_TEXT
    if low in ("time", "what time is it", "samay", "time batao", "date",
               "what is the time") or nlow in (
               "time", "what time is it", "samay", "time batao", "date",
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

    if low in ("skills", "skill", "skills dikhao", "list skills") \
            or nlow in ("skills", "skill", "skills dikhao",
                        "list skills"):
        return run_tool("list_skills", {})

    if low in ("yaadein", "yaadein dikhao", "memories", "memory",
               "meri yaadein") or nlow in (
               "yaadein", "yaadein dikhao", "memories", "memory",
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

    if low in ("kya seekha", "kya seekha hai", "seekhe hue niyam",
               "niyam dikhao", "tumne kya seekha") or nlow in (
               "kya seekha", "kya seekha hai", "seekhe hue niyam",
               "niyam dikhao", "tumne kya seekha"):
        return _learned_rules_reply()

    if low in ("purani baatein", "purani baat", "diary",
               "baatein dikhao", "purani baatein dikhao") or nlow in (
               "purani baatein", "purani baat", "diary",
               "baatein dikhao", "purani baatein dikhao"):
        return _diary_recent_reply()

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
    digest = learned_rules_digest()
    if digest:
        prompt += ("\n\nSEEKHE HUE NIYAM (Ankit ne khud sikhaye hue "
                   "hain - inhe har jawab me hamesha mano, baaki "
                   "saari aadat aur salah se upar):\n" + digest)
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
# v8.12: Groq-fallback wale primary model ke liye fast-fail timeout.
_GEMINI_FAST_TIMEOUT = 15
_TIMEOUT_DELAYS = (2,)
_BUSY_DELAYS = (2, 5)


def _gemini_call(contents: list, model: str = None,
                 system_instruction: bool = True,
                 fast_fail: bool = False) -> str:
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
    # fast_fail (v8.12): Groq ke baad fallback bane primary model ke
    # liye - EK koshish, 15s timeout, koi retry/backoff nahi. Asal PC
    # par primary (3.8) poora din mara raha aur uski retry-chain hi
    # jawab ko minute-bhar latkati thi; ab haar sasti hai aur lite
    # turant mauka pata hai.
    payload = json.dumps(body).encode("utf-8")
    log(f"GEMINI[{model}] prompt ~{len(payload)} chars"
        + (" (fast-fail)" if fast_fail else ""))
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json",
                 "User-Agent": _BROWSER_UA,
                 "Accept": "application/json"},
        method="POST",
    )
    eff_timeout = _GEMINI_FAST_TIMEOUT if fast_fail else _GEMINI_TIMEOUT
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
            with urllib.request.urlopen(req, timeout=eff_timeout) as resp:  # noqa: S310
                data = json.loads(resp.read().decode("utf-8"))
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts).strip()
        except urllib.error.HTTPError as exc:
            if exc.code not in _BUSY_CODES:
                raise
            last_exc = exc
            last_kind = "busy"
            max_attempts = 1 if fast_fail else 3
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
            max_attempts = 1 if fast_fail else 2
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
# v8.12 request diet: record pura rehta hai, lekin dimag ko bheji
# jane wali history sirf aakhri itni baariyon tak seemit hai
# (20 entries = ~10 user/model exchanges) - Groq ki 12k TPM seema
# me lambi history hi sabse bada kharcha thi.
_HISTORY_SEND_MAX = 20


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


# --------------------------------------------------------------------------
# Tool-loop ki seema aur loop-pehchan (v8.11) - kadam-seema 8 se
# badha kar 20. Wajah: seema asal me KAMZOR backup dimag ko
# ghumne se rokne ke liye bani thi, lekin tez dimag (Groq)
# chalne ke baad wahi seema asal bade kaamo ko marne lagi -
# asal PC par "3 design banao" (3 design_banao + 3 open_file
# + jaanch = 8 se zyada kadam) seema par kata, aur purana
# jawab kaam ka bojh wapas user par daal deta tha. Ab teen
# hisse hain:
# 1. SEEMA 20: aam bada kaam aaram se pura hota hai.
# 2. LOOP-PEHCHAN (asli ghumne-rok): ek hi tool-call (naam +
#    args) LAGATAR do baar AYN wahi jawab de, to teesri
#    koshish bekaar hai - run wahi rukta hai, atkane wale
#    kadam ka naam aur ho chuka kaam bata kar. Sirf call ek
#    hona kaafi NAHI hai: jawab alag ho (jaise browser_read
#    par badla hua page) to ye bilkul aam baat hai, loop
#    nahi mana jata.
# 3. SEEMA = PROGRESS, DEAD END NAHI: 20 kadam sach me pure
#    hon to jawab me ho chuke kadmo ki suchi aati hai aur
#    'jaari rakho' bolne par dimag usi suchi se aage badhta
#    hai (jawab history me bhi rehta hai - _record_final_reply).
# --------------------------------------------------------------------------

_MAX_TOOL_STEPS = 20

# Dup guard (v8.17): dimag LAGATAR ayn wahi tool+args dobara
# mange to dusri baar chalaya nahi jata - dimag ko ye note
# tool-result bankar milta hai aur loop aage badhta hai
# (kadam wahi gina jata hai, seema ayn waisi khatam hoti
# hai). Alag args ya beech me dusra kadam aa jaye to aam
# chalana - sirf lagatar-ayn-wahi par rok hai. (Screenshot
# me ek hi list_files do baar lagatar chala tha - asal
# barbaadi yahi thi; _StepTracker wali loop-pehchan iska
# backup hai, ye guard usse pehle rok deta hai.)
_DUP_STEP_NOTE = ("yehi kadam abhi-abhi ho chuka hai — iska "
                  "nateeja upar hai; aage badho ya final "
                  "jawab do")

# Browser asafal-dohrao seema (v8.17, battery drishya f):
# browser setup hi na ho to har browser tool wahi setup
# wala sandesh deta hai - dimag URL badal-badal kar wahi
# asafal kadam dohrata rehta tha aur aakhir me jhootha
# "page par ye dikha" wala jawab bana deta tha. Ab: setup
# wala sandesh milte hi run wahi rukta hai aur wahi sandesh
# user ko jata hai; aur ek hi browser tool lagatar 2 baar
# fail ho to teesri maang chalti hi nahi (note milta hai).
_BROWSER_FAIL_NOTE = ("ye browser wala kadam lagatar fail "
                      "ho raha hai — wahi kaam dohrane se "
                      "wahi nateeja hoga. Pehle wajah dekho "
                      "(browser setup ya login baki ho to "
                      "wahi), warna aage badho ya final "
                      "jawab me wajah batao")

_BROWSER_FAIL_MARKERS = ("nahi ho paya", "ho nahi paya",
                         "uplabdh nahi", "setup karo",
                         "connect nahi", "khul nahi",
                         "band hai", "fail", "error")


def _browser_result_failed(result) -> bool:
    """Browser tool ka jawab asafalta wala hai kya."""
    low = str(result or "").lower()
    return any(m in low for m in _BROWSER_FAIL_MARKERS)


def _tool_signature(tool_call: dict) -> str:
    """Tool call ki pehchan: naam + args ka canonical JSON.

    Args ke shabdon ka kram badalne se pehchan nahi badalti
    (sort_keys), taaki ek hi hukum do shakal me aaye to bhi
    ek hi kadam mana jaye.
    """
    args = tool_call.get("args") or {}
    try:
        canon = json.dumps(args, sort_keys=True, ensure_ascii=False,
                           default=str)
    except (TypeError, ValueError):
        canon = str(args)
    return f"{tool_call.get('tool')}|{canon}"


def _result_snippet(result) -> str:
    """Progress suchi ke liye tool ke jawab ka chhota saaf tukda."""
    text = re.sub(r"\s+", " ", str(result or "")).strip()
    if len(text) > 90:
        text = text[:90].rstrip() + "…"
    return text


def _progress_text(progress: list) -> str:
    """Ho chuke kadmo ki number-daar suchi."""
    lines = []
    for i, (name, snippet) in enumerate(progress, 1):
        lines.append(f"{i}. {name}: {snippet}" if snippet
                     else f"{i}. {name}")
    return "\n".join(lines)


def _tried_line(approaches) -> str:
    """'Try kiye hue raste' wali line (v8.13, Amendment 2) -
    rukne par user ko agent ki koshish DIKHE, sirf haar nahi."""
    if not approaches:
        return ""
    return f"\nTry kiye hue raste: {', '.join(approaches)}"


def _cap_reached_message(progress: list, approaches=None) -> str:
    """Seema (20) par rukne wala jawab - suchi + 'jaari rakho'."""
    return (f"Is kaam ke kadam pure ho gaye ({_MAX_TOOL_STEPS}), "
            "isliye yahan ruk raha hu.\n"
            "Ab tak ye ho gaya:\n"
            f"{_progress_text(progress)}"
            f"{_tried_line(approaches)}\n"
            "Ye kaam abhi adhura hai — 'jaari rakho' bolo to yahi "
            "se aage badhunga.")


def _loop_stuck_message(tool_name: str, progress: list,
                        approaches=None) -> str:
    """Ek hi kadam par atakne wala jawab - kadam ka naam + suchi."""
    msg = (f"Main ek hi kadam par atak gaya hu: {tool_name} "
           "baar-baar wahi jawab de raha hai, isliye ruk raha hu.")
    if progress:
        msg += f"\nJo kaam ho gaya:\n{_progress_text(progress)}"
    msg += _tried_line(approaches)
    return msg


# --------------------------------------------------------------------------
# Koshish-nudge (v8.13, Amendment 2) - "koi kaam ruk jaye to
# usse khoshish kar ke pura karna; mere ulta puchhata hai".
# Dimag ka haar-mannewala jawab (koi tool nahi, "nahi ho paya"
# jaisi baat) tab daboch liya jata hai jab is kaam me abhi 2 se
# kam ALAG raste try hue hon: jawab user ko NAHI jata, uski
# jagah ek andar wala hukum jata hai - "dusra rasta try karo,
# user se kuch mat pucho" - aur loop aage badhta hai. Ek kaam
# par zyada se zyada _MAX_NUDGES (2) nudge; kadam-seema (20)
# aur loop-pehchan isse upar hain, isliye ghumav kabhi nahi
# banta. Rukawat SIRF user ke haath wali ho (login/password/
# CAPTCHA/paisa-delete ki haan) to nudge kabhi nahi - wo jawab
# turant jata hai; suraksha wale ruk kabhi behes nahi karte.
# --------------------------------------------------------------------------

_MAX_NUDGES = 2

# In tools me 'rasta' tool ke saath uska nishana (target/url/
# naam) bhi gina jata hai: ek hi button baar-baar dabana EK
# rasta hai, dusra button dusra rasta.
_TARGET_ARG_KEYS = {
    "browser_click": ("target",),
    "browser_type": ("target",),
    "browser_upload_file": ("target",),
    "browser_open": ("url",),
    "open_url": ("url",),
    "find_file": ("name",),
    "read_file": ("path",),
    "open_file": ("path",),
    "read_skill": ("name",),
    "web_fetch": ("url",),
}


def _approach_key(tool_call: dict) -> str:
    """Ek tool-call ka 'rasta' (approach): tool ka naam + (ho to)
    uska nishana. Nudge ki ginati aur 'Try kiye hue raste' wali
    line dono isi se banti hain."""
    name = tool_call.get("tool") or "?"
    args = tool_call.get("args") or {}
    for key in _TARGET_ARG_KEYS.get(name, ()):
        value = args.get(key)
        if value:
            return f"{name}:{str(value)[:40]}"
    return name


_GIVEUP_MARKERS = (
    "nahi ho paya", "nahi ho payi", "nahi ho sakta",
    "nahi ho sakti", "nahi kar sakta", "nahi kar sakti",
    "nahi mila", "nahi mili", "nahi ho raha", "nahi ho rahi",
    "ho nahi paya", "ruk gaya", "ruk gayi", "sambhav nahi",
    "nahi hoga", "nahi hogi", "nahi kar pa raha",
    "nahi kar pa rahi", "nahi ho pa raha", "nahi ho pa rahi",
)

# Rukawat ki ye kismein SIRF user ke haath me hain - in par
# jawab turant jata hai, nudge kabhi nahi (suraksha pehle).
_BLOCKER_MARKERS = (
    "captcha", "checkpoint", "confirm it's you", "confirm its you",
    "login screen", "login karo", "login karna", "password",
    "2fa", "two-factor", "two factor", "confirm_required",
    "paisa lagega", "paise lagenge", "paisa kharch",
    "delete karne se pehle", "haan chahiye", "manjuri chahiye",
    "permission chahiye", "otp",
)


def _looks_like_giveup(reply: str) -> bool:
    """Aakhri jawab haar-mannewala hai ya nahi (nudge ki shart)."""
    low = (reply or "").lower()
    return any(m in low for m in _GIVEUP_MARKERS)


def _has_user_blocker(reply: str, tracker) -> bool:
    """Rukawat sirf user ke haath wali hai kya - jawab aur is
    run ke tool jawabon dono me nishan dhoondo."""
    blob = (reply or "") + "\n" + "\n".join(tracker.result_snippets)
    low = blob.lower()
    return any(m in low for m in _BLOCKER_MARKERS)


def _nudge_text(approaches) -> str:
    """Andar wala koshish-hukum: user ko NAHI dikhta, dimag ko
    dusra rasta try karne par majboor karta hai."""
    tried = ", ".join(approaches) if approaches else "koi bhi nahi"
    return (
        "INTERNAL INSTRUCTION (ye user ko mat dikhana): Tumne is "
        f"kaam me abhi sirf {len(approaches)} rasta try kiya hai "
        f"({tried}) aur tum haar maan rahe ho - ye galat hai. "
        "User se kuch MAT pucho. Abhi ek DUSRA rasta socho - "
        "dusra tool, dusra route/page, page dobara padh kar dusra "
        "element, ya haalat jaanch karke phir koshish - aur tool "
        "chala kar asal me try karo.")


class _StepTracker:
    """Ek converse run ke kadmo ka hisaab: progress suchi +
    loop-pehchan (lagatar do baar ek hi call, ek hi jawab) +
    try kiye hue ALAG raste (nudge ke liye, v8.13)."""

    def __init__(self):
        self.progress = []        # [(tool ka naam, jawab ka tukda)]
        self.approaches = []      # alag raste, kram me (labels)
        self.result_snippets = []  # blocker-jaanch ke liye tukde
        self._last_sig = None
        self._last_result = None
        self._same = 0            # lagatar ek-jaise (call, jawab)

    def note(self, tool_call: dict, result: str) -> bool:
        """Ek chala hua kadam note karo.

        True mile to LOOP hai: ye call pichhli baar bhi ayn
        wahi thi aur jawab bhi ayn wahi aaya tha - teesri
        koshish bekaar hai, run yahi rok do.
        """
        name = tool_call.get("tool") or "?"
        self.progress.append((name, _result_snippet(result)))
        key = _approach_key(tool_call)
        if key not in self.approaches:
            self.approaches.append(key)
        self.result_snippets.append(str(result or "")[:500])
        sig = _tool_signature(tool_call)
        if sig == self._last_sig and result == self._last_result:
            self._same += 1
        else:
            self._same = 1
        self._last_sig = sig
        self._last_result = result
        return self._same >= 2


def _record_final_reply(text: str):
    """Cap/loop par rukne wala jawab bhi history me model ki
    baari bankar rahe, taaki agle 'jaari rakho' par dimag ko
    apni di hui progress suchi dikhe aur wahi se aage badhe."""
    with _history_lock:
        _history.append({"role": "model", "parts": [{"text": text}]})


# v8.12 request diet: Groq free TPM sirf 12,000 hai - ek 20k wala
# browser_read ya lambi file ka jawab ek hi kadam me poori minute
# ki token-seema kha sakta hai, aur har converse kadam par wahi
# bojh dobara jata hai. Isliye model ko WAPAS jane wali tool-jawab
# copy 4,000 chars par kat-ti hai. Tool ka asal jawab (run_tool ki
# return value, jo user tak jata hai) bilkul nahi badalta.
_MODEL_RESULT_MAX = 4000


def _model_bound_result(result) -> str:
    """Tool jawab ki model-bound copy - _MODEL_RESULT_MAX cap ke saath."""
    text = result if isinstance(result, str) else str(result or "")
    if len(text) <= _MODEL_RESULT_MAX:
        return text
    return (text[:_MODEL_RESULT_MAX] +
            "\n…[jawab lamba tha - model ke liye kata gaya; "
            "pura jawab user ko dikhaya gaya hai]")


# --------------------------------------------------------------------------
# Streaming (v8.13) - mehsoos hone wali raftaar: dimag ka aakhri
# jawab UI me bante-bante dikhta hai, tool kadam chhoti
# 'kaam chal raha hai' lines bankar aate hain. Transport: /ask
# par Server-Sent Events (SSE). Do pakke niyam:
# 1. Stream kahin bhi atke/toote to usi kadam ka jawab AAM
#    (non-stream) call se laya jata hai - jawab kabhi khota
#    nahi, kabhi dohra nahi hota (UI ko hamesha aakhir me pura
#    'final' jawab milta hai, wahi asal hai; beech ke delta
#    sirf preview hain).
# 2. Tool-call JSON kabhi live nahi dikhta: kadam ka text '{'
#    se shuru ho ya usme '"tool"' dikhe to us kadam ke delta
#    rok diye jate hain (_make_step_delta).
# Gemini ki shakal (official docs se verify): POST
# /v1beta/models/<model>:streamGenerateContent?alt=sse -
# har SSE 'data:' frame ek GenerateContentResponse chunk hai,
# text candidates[0].content.parts[].text me tukdo me aata
# hai. Groq OpenAI-compatible hai: body me "stream": true,
# chunks choices[0].delta.content me, aakhir me 'data: [DONE]'.
# --------------------------------------------------------------------------


def _emit_event(on_event, kind: str, text: str) -> None:
    """UI ki taraf ek event bhejo - UI band/gayab ho to bhi
    agent kabhi crash nahi karta."""
    if on_event is None:
        return
    try:
        on_event(kind, text)
    except Exception:
        pass


def _make_step_delta(on_event):
    """Ek converse kadam ke liye delta bhejne wala: text jama
    karta hai aur tool-call jaisi shakal dikhte hi us kadam ke
    delta band kar deta hai (kaccha JSON UI me kabhi nahi)."""
    state = {"buf": "", "live": True}

    def _delta(chunk: str) -> None:
        if not chunk:
            return
        state["buf"] += chunk
        if not state["live"]:
            return
        stripped = state["buf"].lstrip()
        if stripped.startswith("{") or '"tool"' in state["buf"]:
            state["live"] = False
            return
        _emit_event(on_event, "delta", chunk)

    return _delta


# Tool kadam ke status saade shabdon me (v8.16): UI par kaccha
# tool naam ("find_file chal raha hai") ki jagah user ko samajh
# aane wali ek line dikhti hai. Naam map me na ho to purana
# roop hi fallback hai.
_TOOL_STATUS = {
    "list_files": "Files ki list dekh raha hu",
    "read_file": "File padh raha hu",
    "write_file": "File likh raha hu",
    "create_folder": "Folder bana raha hu",
    "get_time": "Time dekh raha hu",
    "web_fetch": "Web page padh raha hu",
    "list_skills": "Skills ki list dekh raha hu",
    "read_skill": "Skill padh raha hu",
    "create_skill": "Nayi skill bana raha hu",
    "yaad_likho": "Ye baat yaad rakh raha hu",
    "purani_baat_dhundho": "Purani baatein dhoondh raha hu",
    "open_url": "Link khol raha hu",
    "video_info": "Video ki jaankari le raha hu",
    "trim_video": "Video kaat raha hu",
    "join_videos": "Video jod raha hu",
    "speak_to_file": "Awaaz bana raha hu",
    "agent_update": "Update kar raha hu",
    "browser_open": "Page khol raha hu",
    "browser_read": "Page padh raha hu",
    "browser_click": "Page par click kar raha hu",
    "browser_type": "Page me likh raha hu",
    "browser_upload_file": "File laga raha hu",
    "download_file": "File download kar raha hu",
    "make_video": "Video bana raha hu",
    "watch_video": "Video dekh raha hu",
    "run_program": "Program chala raha hu",
    "find_file": "File dhoondh raha hu",
    "see_image": "Photo dekh raha hu",
    "design_banao": "Design bana raha hu",
    "open_file": "File khol raha hu",
    "extract_zip": "Zip khol raha hu",
    "screen_shot": "Screen dekh raha hu",
    "screen_locate": "Screen par cheez dhoondh raha hu",
    "screen_do": "Screen par kaam kar raha hu",
    "mouse_move": "Mouse ghuma raha hu",
    "mouse_click": "Click kar raha hu",
    "mouse_scroll": "Scroll kar raha hu",
    "type_text": "Type kar raha hu",
    "press_key": "Key daba raha hu",
}


def _tool_status_text(tool_name: str) -> str:
    """Tool kadam ke liye UI status line (saade shabdon me)."""
    phrase = _TOOL_STATUS.get(tool_name or "")
    if phrase:
        return f"⚙️ {phrase}…"
    return f"⚙️ {tool_name} chal raha hai…"


def _sse_text_lines(resp):
    """Ek khule hue HTTP jawab ko SSE 'data:' payloads me todo.
    Har payload ek string (JSON text ya '[DONE]')."""
    for raw in resp:
        line = raw.decode("utf-8", "replace").strip()
        if line.startswith("data:"):
            yield line[5:].strip()


def _gemini_call_stream(contents: list, model: str = None,
                        on_delta=None, fast_fail: bool = False) -> str:
    """_gemini_call ka streaming roop: EK koshish, koi retry
    nahi (retry wali suraksha caller ke non-stream fallback me
    hai). Haar ki kismein _gemini_call wali hi hain - busy par
    _GeminiBusyError, timeout par _GeminiSlowError, baaki HTTP
    errors ayn waisi - taaki ladder ka vyavhaar na badle."""
    model = model or GEMINI_MODEL
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:streamGenerateContent?alt=sse&key={GEMINI_API_KEY}")
    body = {"contents": contents,
            "system_instruction": {"parts": [{"text": _system_prompt()}]}}
    payload = json.dumps(body).encode("utf-8")
    log(f"GEMINI[{model}] STREAM prompt ~{len(payload)} chars")
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json",
                 "User-Agent": _BROWSER_UA,
                 "Accept": "text/event-stream"},
        method="POST")
    eff_timeout = _GEMINI_FAST_TIMEOUT if fast_fail else _GEMINI_TIMEOUT
    parts_all = []
    try:
        with urllib.request.urlopen(req, timeout=eff_timeout) as resp:  # noqa: S310
            for data in _sse_text_lines(resp):
                if not data or data == "[DONE]":
                    continue
                try:
                    chunk = json.loads(data)
                    parts = chunk["candidates"][0]["content"]["parts"]
                except (ValueError, KeyError, IndexError, TypeError):
                    continue
                for part in parts:
                    text = part.get("text", "")
                    if text:
                        parts_all.append(text)
                        if on_delta is not None:
                            on_delta(text)
    except urllib.error.HTTPError as exc:
        if exc.code in _BUSY_CODES:
            raise _GeminiBusyError(f"HTTP {exc.code}") from exc
        raise
    except (urllib.error.URLError, socket.timeout, TimeoutError,
            ConnectionError) as exc:
        raise _GeminiSlowError(str(exc)) from exc
    return "".join(parts_all).strip()


def _groq_call_stream(messages: list, on_delta=None) -> str:
    """_groq_call ka streaming roop: EK koshish (stream toote to
    caller non-stream _groq_call se pura jawab lata hai, jahan
    poori retry neeti hai). Haar par _GroqDownError hi uthta
    hai - status/detail/rate_scope ke saath, bilkul _groq_call
    ki tarah."""
    body = {"model": GROQ_MODEL, "messages": messages, "stream": True}
    payload = json.dumps(body).encode("utf-8")
    log(f"GROQ STREAM prompt ~{len(payload)} chars")
    req = urllib.request.Request(
        _GROQ_URL, data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {GROQ_API_KEY}",
                 "User-Agent": _BROWSER_UA,
                 "Accept": "text/event-stream"},
        method="POST")
    parts_all = []
    try:
        with urllib.request.urlopen(req, timeout=_GROQ_TIMEOUT) as resp:  # noqa: S310
            for data in _sse_text_lines(resp):
                if not data:
                    continue
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta") or {}
                except (ValueError, KeyError, IndexError, TypeError):
                    continue
                text = delta.get("content")
                if text:
                    parts_all.append(text)
                    if on_delta is not None:
                        on_delta(text)
    except urllib.error.HTTPError as exc:
        detail = _http_error_message(exc)
        rate_scope = (_groq_rate_scope(detail, exc)
                      if exc.code == 429 else "")
        raise _GroqDownError(
            f"HTTP {exc.code}" + (f": {detail}" if detail else ""),
            status=exc.code, detail=detail,
            rate_scope=rate_scope) from exc
    except (urllib.error.URLError, socket.timeout, TimeoutError,
            ConnectionError) as exc:
        raise _GroqDownError(str(exc)) from exc
    return "".join(parts_all).strip()


def _gemini_converse(contents: list, model: str, fast_fail: bool = False,
                     on_event=None):
    """Ek diye hue model ke saath pura tool-loop chalao.

    (jawab, tool_chala_kya) return hota hai; Gemini wali errors
    (slow / HTTP / baaki) caller ko dikhti hain taaki wo fallback
    try kar sake. tool_chala_kya isliye chahiye taaki discipline
    re-ask (sirf salah wale jawab par) sahi faisla le sake.

    Kadam-seema _MAX_TOOL_STEPS (20) hai; har kadam
    _StepTracker me note hota hai - loop pehchane jane par
    run beech me hi imaandaar jawab ke saath rukta hai, aur
    seema pure hone par jawab me progress suchi + 'jaari
    rakho' wala rasta aata hai (v8.11).
    """
    contents = list(contents)
    used_tool = False
    tracker = _StepTracker()
    last_sig = None
    bfail_tool = None
    bfail_streak = 0
    nudges = 0
    for _ in range(_MAX_TOOL_STEPS):
        if _stop_requested():
            stopped = _stopped_message(tracker)
            _record_final_reply(stopped)
            return stopped, used_tool
        if on_event is not None:
            try:
                reply = _gemini_call_stream(
                    contents, model, _make_step_delta(on_event),
                    fast_fail=fast_fail)
            except Exception as exc:
                log(f"STREAM (Gemini {model}) fail: {exc} - aam "
                    "call se jawab la raha hu")
                reply = _gemini_call(contents, model,
                                     fast_fail=fast_fail)
        else:
            reply = _gemini_call(contents, model, fast_fail=fast_fail)
        tool_call = _extract_tool_call(reply)
        if tool_call is None:
            if nudges < _MAX_NUDGES \
                    and len(tracker.approaches) < 2 \
                    and _looks_like_giveup(reply) \
                    and not _has_user_blocker(reply, tracker):
                nudges += 1
                log(f"NUDGE {nudges}: sirf "
                    f"{len(tracker.approaches)} rasta try hua tha - "
                    "haar ki jagah dusra rasta try karne ko kaha")
                contents.append({"role": "model",
                                 "parts": [{"text": reply}]})
                contents.append({"role": "user", "parts": [
                    {"text": _nudge_text(tracker.approaches)}]})
                continue
            with _history_lock:
                _history.append({"role": "model",
                                 "parts": [{"text": reply}]})
            return reply, used_tool
        if _stop_requested():
            stopped = _stopped_message(tracker, tool_call["tool"])
            _record_final_reply(stopped)
            return stopped, used_tool
        sig = _tool_signature(tool_call)
        if last_sig is not None and sig == last_sig:
            # Dup guard (v8.17): lagatar ayn wahi kadam
            # dobara NAHI chalega - note dekar aage badho.
            log(f"DUP GUARD: {tool_call['tool']} ayn wahi "
                "kadam lagatar dobara manga gaya - dobara "
                "chalaya nahi")
            contents.append({"role": "model",
                             "parts": [{"text": reply}]})
            contents.append({"role": "user", "parts": [
                {"text": "Tool result: " + _DUP_STEP_NOTE}]})
            continue
        if tool_call["tool"].startswith("browser_") \
                and bfail_tool == tool_call["tool"] \
                and bfail_streak >= 2:
            # Browser fail seema (v8.17): ek hi browser tool
            # lagatar 2 baar fail - teesri maang nahi chalegi.
            log(f"BROWSER FAIL GUARD: {tool_call['tool']} "
                "lagatar fail ke baad dobara manga gaya - "
                "chalaya nahi")
            contents.append({"role": "model",
                             "parts": [{"text": reply}]})
            contents.append({"role": "user", "parts": [
                {"text": "Tool result: "
                         + _BROWSER_FAIL_NOTE}]})
            continue
        last_sig = sig
        used_tool = True
        _emit_event(on_event, "status",
                    _tool_status_text(tool_call["tool"]))
        result = run_tool(tool_call["tool"], tool_call.get("args") or {})
        if tool_call["tool"].startswith("browser_") \
                and "'browser setup karo'" in result:
            # Browser setup hi nahi hai (v8.17) - ye user ke
            # haath ka kadam hai; URL badal-badal kar loop
            # ghumane ki jagah run yahi roko aur wahi saaf
            # sandesh user ko do.
            log("BROWSER: setup nahi hai - run yahi roka, "
                "user ko saaf sandesh diya")
            _record_final_reply(result)
            return result, True
        if tool_call["tool"].startswith("browser_"):
            if _browser_result_failed(result):
                if bfail_tool == tool_call["tool"]:
                    bfail_streak += 1
                else:
                    bfail_tool = tool_call["tool"]
                    bfail_streak = 1
            else:
                bfail_tool = None
                bfail_streak = 0
        if tracker.note(tool_call, result):
            stuck = _loop_stuck_message(tool_call["tool"],
                                        tracker.progress,
                                        tracker.approaches)
            _record_final_reply(stuck)
            return stuck, used_tool
        contents.append({"role": "model", "parts": [{"text": reply}]})
        contents.append({"role": "user",
                         "parts": [{"text": "Tool result: "
                                            + _model_bound_result(result)}]})
    done = _cap_reached_message(tracker.progress, tracker.approaches)
    _record_final_reply(done)
    return done, used_tool


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
    detail me Groq ke error body ki asal baat rehti hai (jaise
    "Invalid API Key") jab server ne bheji ho (v8.6) - taaki user
    ko sirf "key sahi nahi lagti" nahi, asal wajah dikhe.
    """

    def __init__(self, message, status=None, detail="", rate_scope=""):
        super().__init__(message)
        self.status = status
        self.detail = detail
        # 429 ke liye seema ka dayra: "daily" / "minute" / "" (v8.12) -
        # caller isi se user ko sahi note deta hai (aaj ki seema
        # khatam vs ek-minute wali seema).
        self.rate_scope = rate_scope


def _http_error_parts(exc):
    """HTTPError ke body se (asal message, kaccha snippet) nikalo.

    Body EK hi baar, bounded (~1000 bytes) padha jata hai. Pehle
    Groq/OpenAI shakal {"error": {"message": ...}} try hoti hai;
    wo na mile (jaise Cloudflare ki rok - seedha text "error
    code: 1010") to body ka saaf kiya hua chhota tukda snippet
    banta hai: HTML tags hata kar, whitespace sameet kar, 80
    chars tak (v8.7). Isme kabhi key material ya headers nahi
    hote - sirf server ke bheje body ka hissa hota hai.
    """
    try:
        raw = exc.read(1000)
    except Exception:
        return "", ""
    text = raw.decode("utf-8", errors="ignore")
    try:
        data = json.loads(text)
        msg = (data.get("error") or {}).get("message")
        if isinstance(msg, str) and msg.strip():
            return msg.strip(), ""
    except Exception:
        pass
    snippet = re.sub(r"<[^>]+>", " ", text)
    snippet = re.sub(r"\s+", " ", snippet).strip()
    return "", snippet[:80]


def _http_error_message(exc) -> str:
    """HTTPError ke body se server ki asal baat nikalo (v8.6).

    Groq/OpenAI shakal: {"error": {"message": "..."}}. Body
    bounded (~1000 bytes) padha jata hai, decode/parse ki har
    gadbad par khaali string. Isme kabhi key material nahi hota -
    sirf server ka kaha hua sandesh hota hai.
    """
    return _http_error_parts(exc)[0]


def _groq_rate_scope(detail: str, exc) -> str:
    """Groq 429 ki seema ka dayra: "daily" / "minute" / "" (v8.12).

    Pehle error body ki baat: Groq apne 429 me seema ka naam saaf
    likhta hai ("tokens per day (TPD)" ya "requests per minute
    (RPM)"). Wo na mile to retry-after header: bahut lamba
    intezaar (600s se zyada) = din wali seema, chhota = minute
    wali. Koi ishara na mile to "" - caller purana note rakhega.
    """
    text = (detail or "").lower()
    if any(s in text for s in ("per day", "per-day", "daily",
                               "rpd", "tpd")):
        return "daily"
    if any(s in text for s in ("per minute", "per-minute",
                               "rpm", "tpm")):
        return "minute"
    try:
        secs = float(exc.headers.get("retry-after"))
        return "daily" if secs > 600 else "minute"
    except Exception:
        return ""


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


def _groq_call(messages: list, max_tokens: int = None) -> str:
    """Groq ko ek baar (retry ke saath) bulao aur jawab ka text do.

    Fail-fast neeti upar wali hai. Busy (429/503) ke alawa koi bhi
    HTTP error (401 galat key samet) turant _GroqDownError banta
    hai - retry bekaar hai, Gemini ki baari jaldi aani chahiye.
    Saari koshishen khatm hon to bhi _GroqDownError hi uthta hai,
    taaki caller hamesha ek hi tareeke se Gemini par gir sake.
    max_tokens (v8.16): do to body me jata hai - fast path apne
    chhote sawalon ke liye chhota budget isi se deta hai; na do
    to vyavhaar bilkul purana (koi seema nahi bheji jati).
    """
    body = {"model": GROQ_MODEL, "messages": messages}
    if max_tokens:
        body["max_tokens"] = max_tokens
    payload = json.dumps(body).encode("utf-8")
    log(f"GROQ prompt ~{len(payload)} chars")
    req = urllib.request.Request(
        _GROQ_URL,
        data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {GROQ_API_KEY}",
                 "User-Agent": _BROWSER_UA,
                 "Accept": "application/json"},
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
                detail = _http_error_message(exc)
                log(f"GROQ fail: HTTP {exc.code} (turant Gemini ki "
                    "baari)" + (f" - Groq ne kaha: {detail}"
                                if detail else ""))
                raise _GroqDownError(
                    f"HTTP {exc.code}"
                    + (f": {detail}" if detail else ""),
                    status=exc.code, detail=detail) from exc
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
    detail = ""
    rate_scope = ""
    if isinstance(last_exc, urllib.error.HTTPError):
        detail = _http_error_message(last_exc)
        if last_exc.code == 429:
            rate_scope = _groq_rate_scope(detail, last_exc)
    raise _GroqDownError(
        str(last_exc) + (f": {detail}" if detail else ""),
        status=(last_exc.code
                if isinstance(last_exc, urllib.error.HTTPError)
                else None),
        detail=detail, rate_scope=rate_scope)


def _groq_converse(contents: list, on_event=None):
    """Groq ke saath pura tool-loop - _gemini_converse ka aaina.

    (jawab, tool_chala_kya) return hota hai. Tool protocol bilkul
    wahi hai: jawab me JSON mile to _extract_tool_call use pehchan
    kar tool chalata hai, warna jawab plain text hai. Groq ki haar
    par _GroqDownError (ya koi aur exception) upar jata hai.

    Kadam-seema aur loop-pehchan _gemini_converse wali hi hai
    (_MAX_TOOL_STEPS = 20 + _StepTracker, v8.11).
    """
    contents = list(contents)
    used_tool = False
    tracker = _StepTracker()
    last_sig = None
    bfail_tool = None
    bfail_streak = 0
    nudges = 0
    for _ in range(_MAX_TOOL_STEPS):
        if _stop_requested():
            stopped = _stopped_message(tracker)
            _record_final_reply(stopped)
            return stopped, used_tool
        if on_event is not None:
            try:
                reply = _groq_call_stream(
                    _to_openai_messages(contents),
                    _make_step_delta(on_event))
            except Exception as exc:
                log(f"STREAM (Groq) fail: {exc} - aam call se "
                    "jawab la raha hu")
                reply = _groq_call(_to_openai_messages(contents))
        else:
            reply = _groq_call(_to_openai_messages(contents))
        tool_call = _extract_tool_call(reply)
        if tool_call is None:
            if nudges < _MAX_NUDGES \
                    and len(tracker.approaches) < 2 \
                    and _looks_like_giveup(reply) \
                    and not _has_user_blocker(reply, tracker):
                nudges += 1
                log(f"NUDGE {nudges}: sirf "
                    f"{len(tracker.approaches)} rasta try hua tha - "
                    "haar ki jagah dusra rasta try karne ko kaha")
                contents.append({"role": "model",
                                 "parts": [{"text": reply}]})
                contents.append({"role": "user", "parts": [
                    {"text": _nudge_text(tracker.approaches)}]})
                continue
            with _history_lock:
                _history.append({"role": "model",
                                 "parts": [{"text": reply}]})
            return reply, used_tool
        if _stop_requested():
            stopped = _stopped_message(tracker, tool_call["tool"])
            _record_final_reply(stopped)
            return stopped, used_tool
        sig = _tool_signature(tool_call)
        if last_sig is not None and sig == last_sig:
            # Dup guard (v8.17): lagatar ayn wahi kadam
            # dobara NAHI chalega - note dekar aage badho.
            log(f"DUP GUARD: {tool_call['tool']} ayn wahi "
                "kadam lagatar dobara manga gaya - dobara "
                "chalaya nahi")
            contents.append({"role": "model",
                             "parts": [{"text": reply}]})
            contents.append({"role": "user", "parts": [
                {"text": "Tool result: " + _DUP_STEP_NOTE}]})
            continue
        if tool_call["tool"].startswith("browser_") \
                and bfail_tool == tool_call["tool"] \
                and bfail_streak >= 2:
            # Browser fail seema (v8.17): ek hi browser tool
            # lagatar 2 baar fail - teesri maang nahi chalegi.
            log(f"BROWSER FAIL GUARD: {tool_call['tool']} "
                "lagatar fail ke baad dobara manga gaya - "
                "chalaya nahi")
            contents.append({"role": "model",
                             "parts": [{"text": reply}]})
            contents.append({"role": "user", "parts": [
                {"text": "Tool result: "
                         + _BROWSER_FAIL_NOTE}]})
            continue
        last_sig = sig
        used_tool = True
        _emit_event(on_event, "status",
                    _tool_status_text(tool_call["tool"]))
        result = run_tool(tool_call["tool"], tool_call.get("args") or {})
        if tool_call["tool"].startswith("browser_") \
                and "'browser setup karo'" in result:
            # Browser setup hi nahi hai (v8.17) - ye user ke
            # haath ka kadam hai; URL badal-badal kar loop
            # ghumane ki jagah run yahi roko aur wahi saaf
            # sandesh user ko do.
            log("BROWSER: setup nahi hai - run yahi roka, "
                "user ko saaf sandesh diya")
            _record_final_reply(result)
            return result, True
        if tool_call["tool"].startswith("browser_"):
            if _browser_result_failed(result):
                if bfail_tool == tool_call["tool"]:
                    bfail_streak += 1
                else:
                    bfail_tool = tool_call["tool"]
                    bfail_streak = 1
            else:
                bfail_tool = None
                bfail_streak = 0
        if tracker.note(tool_call, result):
            stuck = _loop_stuck_message(tool_call["tool"],
                                        tracker.progress,
                                        tracker.approaches)
            _record_final_reply(stuck)
            return stuck, used_tool
        contents.append({"role": "model", "parts": [{"text": reply}]})
        contents.append({"role": "user",
                         "parts": [{"text": "Tool result: "
                                            + _model_bound_result(result)}]})
    done = _cap_reached_message(tracker.progress, tracker.approaches)
    _record_final_reply(done)
    return done, used_tool


# --------------------------------------------------------------------------
# NVIDIA Build - naya PEHLA dimag (v8.14 add-on, user ki khaas
# haan se). config.env me NVIDIA_API_KEY ho to pehle NVIDIA ke
# free model jawab dete hain: pehle tez-halka MiniMax M3.1 Flash
# (NVIDIA_MODEL), aur Groq ke baad bhaari Kimi K3.1 Pro
# (NVIDIA_MODEL_HEAVY) - seedhi _brain_run me hai. API
# OpenAI-compatible hai (https://integrate.api.nvidia.com/v1):
# wahi system prompt, wahi tool protocol (jawab ke text me JSON,
# _extract_tool_call hi pehchanta hai - Groq wala ayn tarika),
# wahi tool loop. NVIDIA ki koi bhi haar (timeout, busy 429/503,
# galat key 401, khaali jawab) haar NAHI mani jati: agent chup
# chaap agli seedhi par gir jata hai. Bina NVIDIA key ke ye
# hissa bilkul nahi chalta (v8.13 wala vyavhaar ayn waisa).
# Key SIRF config.env me rehti hai - code/log/jawab me kabhi
# nahi aati.
# --------------------------------------------------------------------------

_NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
_NVIDIA_MODELS_URL = "https://integrate.api.nvidia.com/v1/models"
# Free endpoint bade models par dheera ho sakta hai (Kimi ~50s
# tak dekha gaya). v8.16 se intezaar 45s par seemit hai: pehla
# dimag atka rahe to user ko minute-bhar latkane ki jagah
# jaldi agli seedhi (Groq tez hai) par jana behtar hai.
# Fail-fast neeti Groq wali hi hai: busy (429/503) par kul 2
# koshish, timeout/network par kul 2 koshish, baaki HTTP
# error par turant agli seedhi - koi retry loop nahi.
_NVIDIA_TIMEOUT = 45
# Reasoning wale model pehle reasoning_content me lamba
# sochte hain; chhota budget rakho to asal jawab (content)
# khaali aa jata hai (Glimmer par live dekha gaya). Isliye
# har NVIDIA call me kam se kam 2048 tokens ki jagah.
_NVIDIA_MAX_TOKENS = 2048
# Photo dekhne ka backup model (see_image) - Glimmer photo/
# screenshot samajhne ke liye bana hai.
_NVIDIA_VISION_MODEL = "meta/muse-glimmer-30b"


class _NvidiaDownError(Exception):
    """NVIDIA se jawab nahi aaya - caller agli seedhi par girega.

    status me HTTP code rehta hai jab haar kisi HTTP jawab se
    aayi ho (401/403 matlab key ki gadbad); detail me server ke
    error body ki asal baat (jaise "Invalid API Key") jab bheji
    gayi ho. Bilkul _GroqDownError ka aaina.
    """

    def __init__(self, message, status=None, detail=""):
        super().__init__(message)
        self.status = status
        self.detail = detail


def _nvidia_request(body: dict) -> dict:
    """NVIDIA chat-completions ko ek POST (retry ke saath) aur
    parse hua JSON jawab do. Haar ki har haalat me
    _NvidiaDownError uthta hai - caller ek hi tareeke se agli
    seedhi par gir sakta hai. Key sirf Authorization header me
    jati hai; log me sirf prompt ka size aata hai."""
    payload = json.dumps(body).encode("utf-8")
    log(f"NVIDIA[{body.get('model')}] prompt ~{len(payload)} chars")
    req = urllib.request.Request(
        _NVIDIA_URL,
        data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {NVIDIA_API_KEY}",
                 "User-Agent": _BROWSER_UA,
                 "Accept": "application/json"},
        method="POST",
    )
    last_exc = None
    attempt = 0
    while True:
        try:
            with urllib.request.urlopen(req, timeout=_NVIDIA_TIMEOUT) as resp:  # noqa: S310
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code not in _BUSY_CODES:
                detail = _http_error_message(exc)
                log(f"NVIDIA fail: HTTP {exc.code} (turant agli "
                    "seedhi)" + (f" - NVIDIA ne kaha: {detail}"
                                  if detail else ""))
                raise _NvidiaDownError(
                    f"HTTP {exc.code}"
                    + (f": {detail}" if detail else ""),
                    status=exc.code, detail=detail) from exc
            last_exc = exc
            max_attempts = 2
            delays = _BUSY_DELAYS
            log(f"NVIDIA attempt {attempt + 1}/{max_attempts} fail: "
                f"HTTP {exc.code} (server busy / rate limit, retry)")
        except (urllib.error.URLError, socket.timeout, TimeoutError,
                ConnectionError) as exc:
            last_exc = exc
            max_attempts = 2
            delays = _TIMEOUT_DELAYS
            log(f"NVIDIA attempt {attempt + 1}/{max_attempts} fail: "
                f"{exc}")
        if attempt + 1 >= max_attempts:
            break
        time.sleep(delays[min(attempt, len(delays) - 1)])
        attempt += 1
    detail = ""
    if isinstance(last_exc, urllib.error.HTTPError):
        detail = _http_error_message(last_exc)
    raise _NvidiaDownError(
        str(last_exc) + (f": {detail}" if detail else ""),
        status=(last_exc.code
                if isinstance(last_exc, urllib.error.HTTPError)
                else None),
        detail=detail)


def _nvidia_chat(messages: list, model: str = None,
                 max_tokens: int = None) -> str:
    """NVIDIA ko ek baar bulao aur jawab ka text do (_groq_call
    ka aaina). Jawab ka content khaali mile (reasoning ne pura
    budget kha liya ho) to use haar mano - khaali jawab aage
    bhejne se behtar hai agli seedhi ka asal jawab."""
    body = {"model": model or NVIDIA_MODEL,
            "messages": messages,
            "max_tokens": max_tokens or _NVIDIA_MAX_TOKENS}
    data = _nvidia_request(body)
    try:
        message = data["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as exc:
        raise _NvidiaDownError(
            "NVIDIA ke jawab ki shakal samajh nahi aayi") from exc
    content = (message.get("content") or "").strip()
    if not content:
        log("NVIDIA: content khaali aaya (reasoning ne budget "
            "kha liya hoga) - haar man kar agli seedhi")
        raise _NvidiaDownError("NVIDIA se khaali jawab aaya")
    return content


def _nvidia_call_stream(messages: list, model: str = None,
                        on_delta=None) -> str:
    """_nvidia_chat ka streaming roop: EK koshish (stream toote
    to caller non-stream _nvidia_chat se pura jawab lata hai,
    jahan poori retry neeti hai). Haar par _NvidiaDownError hi
    uthta hai - status/detail ke saath, bilkul _nvidia_request
    ki tarah."""
    body = {"model": model or NVIDIA_MODEL,
            "messages": messages,
            "max_tokens": _NVIDIA_MAX_TOKENS,
            "stream": True}
    payload = json.dumps(body).encode("utf-8")
    log(f"NVIDIA[{body['model']}] STREAM prompt ~{len(payload)} chars")
    req = urllib.request.Request(
        _NVIDIA_URL, data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {NVIDIA_API_KEY}",
                 "User-Agent": _BROWSER_UA,
                 "Accept": "text/event-stream"},
        method="POST")
    parts_all = []
    try:
        with urllib.request.urlopen(req, timeout=_NVIDIA_TIMEOUT) as resp:  # noqa: S310
            for data in _sse_text_lines(resp):
                if not data:
                    continue
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta") or {}
                except (ValueError, KeyError, IndexError, TypeError):
                    continue
                text = delta.get("content")
                if text:
                    parts_all.append(text)
                    if on_delta is not None:
                        on_delta(text)
    except urllib.error.HTTPError as exc:
        detail = _http_error_message(exc)
        raise _NvidiaDownError(
            f"HTTP {exc.code}" + (f": {detail}" if detail else ""),
            status=exc.code, detail=detail) from exc
    except (urllib.error.URLError, socket.timeout, TimeoutError,
            ConnectionError) as exc:
        raise _NvidiaDownError(str(exc)) from exc
    result = "".join(parts_all).strip()
    if not result:
        raise _NvidiaDownError("NVIDIA stream se khaali jawab aaya")
    return result


def _nvidia_converse(contents: list, model: str = None,
                     on_event=None):
    """NVIDIA ke saath pura tool-loop - _groq_converse ka aaina.

    (jawab, tool_chala_kya) return hota hai. Tool protocol bilkul
    wahi hai: jawab me JSON mile to _extract_tool_call use pehchan
    kar tool chalata hai, warna jawab plain text hai. NVIDIA ki
    haar par _NvidiaDownError (ya koi aur exception) upar jata
    hai. model na do to NVIDIA_MODEL (MiniMax) chalta hai;
    bhaari kadam ke liye caller NVIDIA_MODEL_HEAVY (Kimi) deta
    hai.

    Kadam-seema aur loop-pehchan _groq_converse wali hi hai
    (_MAX_TOOL_STEPS = 20 + _StepTracker, v8.11).
    """
    contents = list(contents)
    used_tool = False
    tracker = _StepTracker()
    last_sig = None
    bfail_tool = None
    bfail_streak = 0
    nudges = 0
    for _ in range(_MAX_TOOL_STEPS):
        if _stop_requested():
            stopped = _stopped_message(tracker)
            _record_final_reply(stopped)
            return stopped, used_tool
        if on_event is not None:
            try:
                reply = _nvidia_call_stream(
                    _to_openai_messages(contents), model,
                    _make_step_delta(on_event))
            except Exception as exc:
                log(f"STREAM (NVIDIA) fail: {exc} - aam call se "
                    "jawab la raha hu")
                reply = _nvidia_chat(_to_openai_messages(contents),
                                     model)
        else:
            reply = _nvidia_chat(_to_openai_messages(contents),
                                 model)
        tool_call = _extract_tool_call(reply)
        if tool_call is None:
            if nudges < _MAX_NUDGES \
                    and len(tracker.approaches) < 2 \
                    and _looks_like_giveup(reply) \
                    and not _has_user_blocker(reply, tracker):
                nudges += 1
                log(f"NUDGE {nudges}: sirf "
                    f"{len(tracker.approaches)} rasta try hua tha - "
                    "haar ki jagah dusra rasta try karne ko kaha")
                contents.append({"role": "model",
                                 "parts": [{"text": reply}]})
                contents.append({"role": "user", "parts": [
                    {"text": _nudge_text(tracker.approaches)}]})
                continue
            with _history_lock:
                _history.append({"role": "model",
                                 "parts": [{"text": reply}]})
            return reply, used_tool
        if _stop_requested():
            stopped = _stopped_message(tracker, tool_call["tool"])
            _record_final_reply(stopped)
            return stopped, used_tool
        sig = _tool_signature(tool_call)
        if last_sig is not None and sig == last_sig:
            # Dup guard (v8.17): lagatar ayn wahi kadam
            # dobara NAHI chalega - note dekar aage badho.
            log(f"DUP GUARD: {tool_call['tool']} ayn wahi "
                "kadam lagatar dobara manga gaya - dobara "
                "chalaya nahi")
            contents.append({"role": "model",
                             "parts": [{"text": reply}]})
            contents.append({"role": "user", "parts": [
                {"text": "Tool result: " + _DUP_STEP_NOTE}]})
            continue
        if tool_call["tool"].startswith("browser_") \
                and bfail_tool == tool_call["tool"] \
                and bfail_streak >= 2:
            # Browser fail seema (v8.17): ek hi browser tool
            # lagatar 2 baar fail - teesri maang nahi chalegi.
            log(f"BROWSER FAIL GUARD: {tool_call['tool']} "
                "lagatar fail ke baad dobara manga gaya - "
                "chalaya nahi")
            contents.append({"role": "model",
                             "parts": [{"text": reply}]})
            contents.append({"role": "user", "parts": [
                {"text": "Tool result: "
                         + _BROWSER_FAIL_NOTE}]})
            continue
        last_sig = sig
        used_tool = True
        _emit_event(on_event, "status",
                    _tool_status_text(tool_call["tool"]))
        result = run_tool(tool_call["tool"], tool_call.get("args") or {})
        if tool_call["tool"].startswith("browser_") \
                and "'browser setup karo'" in result:
            # Browser setup hi nahi hai (v8.17) - ye user ke
            # haath ka kadam hai; URL badal-badal kar loop
            # ghumane ki jagah run yahi roko aur wahi saaf
            # sandesh user ko do.
            log("BROWSER: setup nahi hai - run yahi roka, "
                "user ko saaf sandesh diya")
            _record_final_reply(result)
            return result, True
        if tool_call["tool"].startswith("browser_"):
            if _browser_result_failed(result):
                if bfail_tool == tool_call["tool"]:
                    bfail_streak += 1
                else:
                    bfail_tool = tool_call["tool"]
                    bfail_streak = 1
            else:
                bfail_tool = None
                bfail_streak = 0
        if tracker.note(tool_call, result):
            stuck = _loop_stuck_message(tool_call["tool"],
                                        tracker.progress,
                                        tracker.approaches)
            _record_final_reply(stuck)
            return stuck, used_tool
        contents.append({"role": "model", "parts": [{"text": reply}]})
        contents.append({"role": "user",
                         "parts": [{"text": "Tool result: "
                                            + _model_bound_result(result)}]})
    done = _cap_reached_message(tracker.progress, tracker.approaches)
    _record_final_reply(done)
    return done, used_tool


def _nvidia_vision_call(b64: str, mime: str, prompt: str) -> str:
    """Photo/screenshot ko Glimmer se samjho (v8.14) - see_image
    ka backup raasta jab Gemini photo dekhne me fail ho jaye.

    OpenAI wali shakal: image data-URI bankar jati hai. Budget
    jaan-boojh kar bada (2048) - Glimmer pehle reasoning_content
    me sochta hai, chhota budget asal jawab kha jata hai. Haar
    par _NvidiaDownError - caller Gemini wale purane jawab par
    hi rehta hai."""
    messages = [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url",
         "image_url": {"url": f"data:{mime};base64,{b64}"}}]}]
    return _nvidia_chat(messages, model=_NVIDIA_VISION_MODEL,
                        max_tokens=_NVIDIA_MAX_TOKENS)


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


def _ladder_run(contents: list, fast_primary: bool = False,
                on_event=None):
    """Model ladder chalao: pehle primary, fail ho to dusra model.

    Safal ho to (jawab, tool_chala_kya); dono fail hon ya key ki
    galti ho to (error_message, None). Har model apni fail-fast
    retry neeti (timeout/network 2 koshish, busy 3 koshish) se
    chalta hai. Key ki galti (400/401/403) par ladder turant rukti
    hai - dusra model bhi wahi key use karega, koshish bekaar hai.

    fast_primary (v8.12): Groq fail hokar yahan aaye hon to PRIMARY
    model ki koshish sasti rakho (ek koshish, 15s, koi retry nahi) -
    asal PC par mara hua primary apni retry-chain se jawab ko
    minute-bhar latkata tha. Dusra model (lite) apni aam neeti se
    hi chalta hai.
    """
    models = _ladder_models()
    last_exc = None
    extra = {"on_event": on_event} if on_event is not None else {}
    for idx, model in enumerate(models):
        try:
            reply, used_tool = _gemini_converse(
                contents, model,
                fast_fail=(fast_primary and idx == 0), **extra)
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


def _rung_fail_word(status, key_error, rate_scope="") -> str:
    """Ek fail hue dimag ki wajah chhote roop me (v8.17) -
    all-fail wale nateeja note ke liye."""
    if key_error:
        return "key sahi nahi lagi"
    if status is None:
        return "jawab time par nahi aaya (dheera pada)"
    if status == 429 and rate_scope == "daily":
        return "aaj ki free seema khatam thi"
    if status == 429 and rate_scope == "minute":
        return "ek-minute wali seema lagi thi"
    if status in (429, 503):
        return "server busy tha"
    return f"HTTP {status} par fail hua"


def _brain_run(contents: list, on_event=None):
    """Dimag chalao - seedhi (v8.14): pehle NVIDIA MiniMax (agar
    NVIDIA key hai), phir Groq (agar key hai), phir NVIDIA ka
    bhaari model Kimi, aakhir me Gemini ladder.

    Safal ho to (jawab, tool_chala_kya); sab fail hon to
    (error_message, None) - error message Gemini wali class-neeti
    se hi banta hai (busy -> busy wala, slow -> slow wala, 404 ->
    plain). Upar wali seedhi se gir kar neeche se jawab aaye to
    jawab ke upar ek chhota note lagta hai. Kisi dimag ki haar
    key wali ho (HTTP 401/403) to note me usi key ko jaanchne ka
    ishara bhi jud jata hai - baaki haar (timeout/429/5xx/
    network) par note bilkul waisa hi rehta hai. Bina NVIDIA
    key ke vyavhaar bilkul v8.13 wala hai (Groq -> Gemini);
    bina dono keys ke ye seedha Gemini ladder hai - bilkul
    v8.1 wala vyavhaar, koi note nahi.
    """
    nvidia_failed = False
    nvidia_key_error = False
    nvidia_detail = ""
    nvidia_status = None
    heavy_tried = False
    groq_failed = False
    groq_key_error = False
    groq_detail = ""
    groq_status = None
    groq_rate_scope = ""
    extra = {"on_event": on_event} if on_event is not None else {}
    if NVIDIA_API_KEY:
        try:
            reply, used_tool = _nvidia_converse(
                contents, NVIDIA_MODEL, **extra)
            log("BRAIN: jawab NVIDIA (MiniMax) se aaya")
            return reply, used_tool
        except Exception as exc:  # har haar par agli seedhi
            nvidia_failed = True
            nvidia_status = getattr(exc, "status", None)
            if nvidia_status in (401, 403):
                # Key wali gadbad - note me ishara milega, aur
                # bhaari NVIDIA model bhi NAHI try hoga (wahi
                # key hai, wahi 401 aayega - waqt barbaad nahi).
                nvidia_key_error = True
                nvidia_detail = (getattr(exc, "detail", "")
                                 or "")[:120]
            log(f"BRAIN: NVIDIA (MiniMax) fail ({exc}) - agli "
                "seedhi par ja raha hu")
            if nvidia_status is None:
                # HTTP jawab hi nahi aaya - timeout/network par
                # atka tha. v8.16: saade shabdon me darj karo ki
                # pehla dimag dheera pada, isliye seedhi aage
                # badhi (user ki "bas soch raha hai" wali
                # shikayat ka log wala saboot).
                log("BRAIN: NVIDIA dheera pada (jawab time par "
                    "nahi aaya) - agli seedhi par gaya")
    if GROQ_API_KEY:
        try:
            reply, used_tool = _groq_converse(contents, **extra)
            log("BRAIN: jawab GROQ se aaya")
            return reply, used_tool
        except Exception as exc:  # har haar par Gemini ki baari
            groq_failed = True
            groq_status = getattr(exc, "status", None)
            groq_rate_scope = getattr(exc, "rate_scope", "") or ""
            if groq_status in (401, 403):
                # Key wali gadbad (galat ya mis-paste hui key) -
                # user ko note me key jaanchne ka ishara milega.
                groq_key_error = True
                # Groq ke error body ki asal baat (v8.6) - note me
                # jud jayegi, taaki "key sahi nahi lagti" ki jagah
                # pakki wajah dikhe. Key material kabhi nahi hota.
                groq_detail = (getattr(exc, "detail", "") or "")[:120]
            log(f"BRAIN: GROQ fail ({exc}) - Gemini ladder par ja "
                "raha hu")
    if NVIDIA_API_KEY and not nvidia_key_error \
            and NVIDIA_MODEL_HEAVY != NVIDIA_MODEL:
        # Bhaari dimag (Kimi) - MiniMax/Groq dono fail hon tabhi
        # iski baari aati hai. NVIDIA ki key hi kharab ho
        # (401/403) to ye try hi nahi hota (upar wala
        # nvidia_key_error wahi rok hai - wahi key, wahi 401).
        heavy_tried = True
        try:
            reply, used_tool = _nvidia_converse(
                contents, NVIDIA_MODEL_HEAVY, **extra)
            log("BRAIN: jawab NVIDIA (Kimi, bhaari) se aaya")
            if used_tool is not None:
                reply = ("(pehle wale dimagon se jawab nahi aaya, "
                         "bhaari NVIDIA dimag se laya hu)\n"
                         + reply)
            return reply, used_tool
        except Exception as exc:  # har haar par Gemini ki baari
            log(f"BRAIN: NVIDIA (Kimi) fail ({exc}) - Gemini "
                "ladder par ja raha hu")
    reply, used_tool = _ladder_run(
        contents, fast_primary=(groq_failed or nvidia_failed),
        on_event=on_event)
    if used_tool is None and (groq_failed or nvidia_failed):
        # v8.17 (battery drishya e2): SAARRE dimag fail - sirf
        # aakhri (Gemini) wajah wala canned jawab gumrah karta
        # tha; user ko lagta tha sirf Gemini try hua aur baat
        # bina nateeje khatam ho gayi. Nateeja pehle: kaun-kaun
        # try hua aur kya hua, ek line me - asal wajah wala
        # jawab uske neeche ayn waisa rehta hai.
        tried = []
        if nvidia_failed:
            naam = ("NVIDIA (MiniMax + bhaari model)"
                    if heavy_tried else "NVIDIA (MiniMax)")
            tried.append(
                f"{naam}: "
                f"{_rung_fail_word(nvidia_status, nvidia_key_error)}")
        if groq_failed:
            tried.append(
                f"Groq: "
                f"{_rung_fail_word(groq_status, groq_key_error, groq_rate_scope)}")
        reply = ("(Nateeja: jawab nahi ban paya — "
                 + "; ".join(tried)
                 + "; aur Gemini se bhi jawab nahi aaya.)\n"
                 + reply)
    if used_tool is not None and (groq_failed or nvidia_failed):
        if groq_failed:
            note = ("(tez wale model se jawab nahi aaya, dusre "
                    "model se laya hu)")
            if groq_key_error:
                note += (" (Note: lagta hai Groq wali key sahi "
                         "nahi hai — config.env me GROQ_API_KEY "
                         "wali line ek baar jaanch lo, key gsk_ se "
                         "shuru hoti hai.)")
                if groq_detail:
                    note += f" (Groq ne kaha: {groq_detail})"
            if nvidia_key_error:
                # Dono taraf haar hui aur NVIDIA ki key pakki
                # kharab nikli - user ko wo ishara bhi mile.
                note += (" (Note: NVIDIA wali key bhi sahi nahi "
                         "hai — config.env me NVIDIA_API_KEY wali "
                         "line jaanch lo, key nvapi- se shuru "
                         "hoti hai.)")
            if groq_status == 429 and groq_rate_scope == "daily":
                # v8.12: 429 ka dayra saaf batao - din wali seema
                # khatam hai to user ko pata ho ki kal tak tez
                # dimag wapas aayega, koi gadbad nahi hui.
                note += (" (tez dimag ki aaj ki free seema khatam "
                         "ho gayi hai — kal phir tez ho jayega)")
            elif groq_status == 429 and groq_rate_scope == "minute":
                note += (" (tez dimag ki ek-minute wali seema "
                         "lagi hai — thodi der me phir tez ho "
                         "jayega)")
        else:
            # Sirf NVIDIA fail hua tha (Groq ya to hai hi nahi,
            # ya usne jawab de diya hota to hum yahan hote hi
            # nahi - ye Gemini se aaya jawab hai).
            note = ("(NVIDIA wale dimag se jawab nahi aaya, dusre "
                    "model se laya hu)")
            if nvidia_key_error:
                note += (" (Note: lagta hai NVIDIA wali key sahi "
                         "nahi hai — config.env me NVIDIA_API_KEY "
                         "wali line ek baar jaanch lo, key nvapi- "
                         "se shuru hoti hai.)")
                if nvidia_detail:
                    note += f" (NVIDIA ne kaha: {nvidia_detail})"
        reply = note + "\n" + reply
    return reply, used_tool


# --------------------------------------------------------------------------
# Dimag test (v8.6) - 'dimag test karo' par dono dimagon ki ASAL
# jaanch: Groq par halki GET /models call, Gemini par sabse chhoti
# generateContent call. v8.14: NVIDIA par sabse chhoti chat call
# (uske /models par bina sahi key ke bhi 200 aa jata hai, isliye
# GET wali jaanch wahan kaafi nahi). Jawab me har dimag ki pass/fail ke saath
# asal wajah (HTTP code + server ki baat) aati hai - "lagta hai key
# sahi nahi" wala andaz khatm. Test se pehle config hot-reload
# hota hai, isliye taazi save ki hui key hi test hoti hai aur
# restart ki zaroorat nahi padti.
# --------------------------------------------------------------------------

_GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"


def _groq_selftest() -> str:
    """Groq ki key sach me chal rahi hai ya nahi - /models par halki GET."""
    req = urllib.request.Request(
        _GROQ_MODELS_URL,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}",
                 "User-Agent": _BROWSER_UA,
                 "Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
            resp.read(200)
        log("DIMAG TEST: Groq PASS")
        return "✅ chal raha hai"
    except urllib.error.HTTPError as exc:
        detail, snippet = _http_error_parts(exc)
        shown = detail if detail else snippet
        log(f"DIMAG TEST: Groq FAIL HTTP {exc.code}"
            + (f" - {shown}" if shown else ""))
        if detail:
            return f"❌ fail — HTTP {exc.code}: {detail[:120]}"
        if snippet:
            # JSON wali asal baat nahi mili (jaise Cloudflare ki
            # rok) - body ka saaf tukda hi dikhao, taaki rok
            # dikhai de: "HTTP 403 — error code: 1010" (v8.7).
            return f"❌ fail — HTTP {exc.code} — {snippet}"
        return f"❌ fail — HTTP {exc.code}"
    except Exception as exc:
        log(f"DIMAG TEST: Groq FAIL {exc}")
        return f"❌ fail — {exc.__class__.__name__}"


def _nvidia_selftest() -> str:
    """NVIDIA ki key sach me chal rahi hai ya nahi (v8.14).

    GET /models yahan kaafi NAHI hai - wo bina sahi key ke bhi
    khul jata hai (live smoke me dummy key par bhi 200 aaya
    tha), isliye asal jaanch sabse chhoti chat call se hoti
    hai: key, model aur endpoint teeno ek saath pakke ho jate
    hain. Jawab ka content khaali bhi ho (reasoning budget)
    to call ka safal hona hi PASS hai. Key kabhi nahi dikhti."""
    try:
        _nvidia_request({"model": NVIDIA_MODEL,
                         "messages": [{"role": "user",
                                       "content": "ok"}],
                         "max_tokens": 64})
        log("DIMAG TEST: NVIDIA PASS")
        return "✅ chal raha hai"
    except _NvidiaDownError as exc:
        log(f"DIMAG TEST: NVIDIA FAIL {exc}")
        if exc.status:
            return f"❌ fail — {exc}"
        return ("❌ fail — server tak pahuncha hi nahi "
                "(internet/timeout)")
    except Exception as exc:
        log(f"DIMAG TEST: NVIDIA FAIL {exc}")
        return f"❌ fail — {exc.__class__.__name__}"


def _gemini_selftest(model: str) -> str:
    """Ek model par sabse chhoti Gemini call ('ok') - pass/fail + wajah."""
    try:
        _gemini_call([{"role": "user", "parts": [{"text": "ok"}]}],
                     model, system_instruction=False)
        log(f"DIMAG TEST: Gemini[{model}] PASS")
        return "✅ chal raha hai"
    except urllib.error.HTTPError as exc:
        log(f"DIMAG TEST: Gemini[{model}] FAIL HTTP {exc.code}")
        return f"❌ fail — HTTP {exc.code}"
    except Exception as exc:
        log(f"DIMAG TEST: Gemini[{model}] FAIL {exc}")
        return f"❌ fail — {exc.__class__.__name__}"


def _browser_state_line() -> str:
    """Dimag test ke liye browser haath ki haalat (v8.9) - sirf
    pehchan, koi launch/connect ki shuruaat nahi (cached
    connection ki halki jaanch chalegi, bas)."""
    if _browser_is_connected():
        return "Browser: agent Chrome se juda hai ✅"
    if (BROWSER_PROFILE_DIR / "DevToolsActivePort").is_file():
        return ("Browser: agent Chrome khula hai lekin abhi "
                "juda nahi hai")
    return "Browser: setup nahi hua hai (agent Chrome abhi bana hi nahi)"


def _config_state_line() -> str:
    """Dimag test ke liye keys ki maujudgi (v8.9) - SIRF hai ya
    nahi (✓/✗). Key ka koi hissa kabhi nahi dikhta."""
    g = "✓" if GEMINI_API_KEY else "✗"
    q = "✓" if GROQ_API_KEY else "✗"
    n = "✓" if NVIDIA_API_KEY else "✗"
    return (f"Config: Gemini key lagi hai {g}, Groq key lagi "
            f"hai {q}, NVIDIA key lagi hai {n}")


def tool_dimag_test() -> str:
    """'dimag test karo' ka jawab: har dimag ki ek line + aakhri salah.

    Pehle config hot-reload (taaki jo key abhi-abhi save hui hai
    wahi test ho), phir NVIDIA (key ho to), Groq (key ho to),
    phir Gemini ke dono ladder model (primary + lite; dono ek
    hi hon to ek baar).

    v8.9: report me do lines aur - Browser ki haalat aur Config
    me keys ki maujudgi (sirf ✓/✗) - taaki 'dimag theek hai
    lekin browser setup hi nahi hua' wali haalat bhi ek hi
    test me saaf dikh jaye.
    """
    _maybe_reload_config()
    lines = []
    nvidia_state = "none"  # none | pass | fail | badkey
    if NVIDIA_API_KEY:
        res = _nvidia_selftest()
        lines.append(f"NVIDIA (pehla dimag): {res}")
        if res.startswith("✅"):
            nvidia_state = "pass"
        elif "Invalid API Key" in res or "HTTP 401" in res \
                or "HTTP 403" in res:
            nvidia_state = "badkey"
        else:
            nvidia_state = "fail"
    else:
        lines.append("NVIDIA (pehla dimag): key config me hai hi "
                     "nahi — purana Groq/Gemini wala kram chalega")
    groq_state = "none"  # none | pass | fail | badkey
    if GROQ_API_KEY:
        res = _groq_selftest()
        lines.append(f"Groq (tez dimag): {res}")
        if res.startswith("✅"):
            groq_state = "pass"
        elif "Invalid API Key" in res:
            groq_state = "badkey"
        else:
            groq_state = "fail"
    elif NVIDIA_API_KEY:
        lines.append("Groq (tez dimag): key config me hai hi nahi — "
                     "NVIDIA aur Gemini chalenge")
    else:
        lines.append("Groq (tez dimag): key config me hai hi nahi — "
                     "sirf Gemini chalega")
    gemini_state = "none"  # none | pass | fail
    if GEMINI_API_KEY:
        primary = GEMINI_MODEL or _MODEL_LITE
        models = [primary]
        if _MODEL_LITE != primary:
            models.append(_MODEL_LITE)
        any_pass = False
        for model in models:
            res = _gemini_selftest(model)
            lines.append(f"Gemini ({model}): {res}")
            if res.startswith("✅"):
                any_pass = True
        gemini_state = "pass" if any_pass else "fail"
    else:
        lines.append("Gemini: key config me hai hi nahi")
    # v8.9: browser + config ki haalat bhi isi report me.
    browser_line = _browser_state_line()
    lines.append(browser_line)
    lines.append(_screen_state_line())
    lines.append(_config_state_line())
    browser_setup_done = "setup nahi hua hai" not in browser_line
    # Aakhri salah - haalat ke hisaab se ek saaf line.
    if nvidia_state == "badkey":
        lines.append("NVIDIA ki key galat hai: build.nvidia.com "
                     "par apne account se nayi API key banao, COPY "
                     "karke config.env ki NVIDIA_API_KEY wali line "
                     "me waisa hi chipka do (haath se type mat "
                     "karna, key nvapi- se shuru hoti hai). Restart "
                     "ki zaroorat NAHI hai — main config khud "
                     "dobara padh leta hu. Phir 'dimag test karo' "
                     "phir se bolo.")
    elif (nvidia_state == "pass" or groq_state == "pass") \
            and gemini_state == "pass":
        lines.append("Sab theek hai — ab kaam bolo, agent poori "
                     "taqat se chalega.")
    elif groq_state == "badkey":
        lines.append("Groq ki key galat hai: console.groq.com par "
                     "nayi key banao, COPY wale button se copy karke "
                     "config.env ki GROQ_API_KEY wali line me waisa "
                     "hi chipka do (haath se type mat karna). Restart "
                     "ki zaroorat NAHI hai — main config khud dobara "
                     "padh leta hu. Phir 'dimag test karo' phir se bolo.")
    elif nvidia_state == "pass" and gemini_state in ("fail", "none"):
        lines.append("NVIDIA wala pehla dimag chal raha hai — kaam "
                     "chalega. Gemini backup abhi theek nahi hai; "
                     "uski key config.env me ek baar jaanch lo.")
    elif groq_state == "fail" and gemini_state == "pass":
        lines.append("Gemini chal raha hai, isliye kaam to hoga — "
                     "lekin tez wala dimag abhi fail hai. Internet "
                     "check karo aur thodi der baad 'dimag test karo' "
                     "phir bolo.")
    elif nvidia_state == "fail" and gemini_state == "pass":
        lines.append("Gemini chal raha hai — kaam hoga, lekin "
                     "NVIDIA wala pehla dimag abhi fail hai. "
                     "Internet check karo aur thodi der baad "
                     "'dimag test karo' phir bolo.")
    elif groq_state == "pass" and gemini_state in ("fail", "none"):
        lines.append("Tez dimag (Groq) chal raha hai — kaam chalega. "
                     "Gemini backup abhi theek nahi hai; uski key "
                     "config.env me ek baar jaanch lo.")
    elif groq_state == "none" and nvidia_state == "none" \
            and gemini_state == "pass":
        lines.append("Gemini chal raha hai — kaam hoga. Tez jawab "
                     "chahiye to config.env me GROQ_API_KEY bhi daal "
                     "do (free hai, console.groq.com se).")
    elif groq_state == "none" and nvidia_state == "none" \
            and gemini_state == "none":
        lines.append("Dono keys config me nahi hain — pehle "
                     "config.env me GEMINI_API_KEY daalo, phir "
                     "'dimag test karo' bolo.")
    else:
        lines.append("Dono dimag abhi fail hain — internet connection "
                     "check karo, phir 'dimag test karo' phir se bolo.")
    # v8.9: dono dimag pass hon lekin browser setup hi na hua ho
    # to ek line aur - warna 'sab theek' sunkar bhi asal kaam
    # (logged-in sites) atka rehta hai.
    if (groq_state == "pass" or nvidia_state == "pass") \
            and gemini_state == "pass" \
            and not browser_setup_done:
        lines.append("Ek kaam baki hai: 'browser setup karo' "
                     "likho taaki agent wala Chrome taiyaar ho "
                     "jaye — phir logged-in sites (Facebook/"
                     "YouTube upload) ka kaam bhi hoga.")
    return "\n".join(lines)


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
    return _guard_reply_text()


def _guard_reply_text() -> str:
    """Guard ka canned jawab - v8.13 se ye AAKHRI upaay hai
    (pehle khud-recovery aur saade-shabdo wala re-ask hota hai,
    neeche _finalize_reply dekho)."""
    return ("Kaam karne ki koshish ki, lekin mera jawab gadbad "
            "ho gaya (andar ki takneeki cheez bahar aa gayi). "
            "Ek baar phir se bolo - main dobara koshish karta "
            "hu.")


# --------------------------------------------------------------------------
# Guard khud-recovery (v8.13) - asal PC par 2026-11-20 20:38 ko
# user ne do baar "video ko upload kar do" bola aur dono baar
# use canned "phir se bolo" wala jawab mila, kyunki dimag ka
# jawab kacche tool-JSON ki shakal me aaya tha aur guard use
# seedha canned line se badal deta tha. Ab guard pehle KHUD
# sudhaarta hai:
#   1. Jawab ke andar parse hone layak tool-call ho to use
#      ASAL me chalao aur loop aage badhao (kadam-seema ke
#      andar hi - recovery bhi ek aam brain run hai).
#   2. Parse na ho to dimag se EK baar saade shabdon me jawab
#      maango (koi JSON/tool-format nahi wala sakht hukum).
#   3. Tab bhi gadbad ho tabhi canned line - aakhri upaay.
# Ek turn me re-ask zyada se zyada EK baar (recovery aur
# plain re-ask milakar bhi loop nahi banta - har stage ek hi
# baar chalti hai).
# --------------------------------------------------------------------------


def _recover_tool_from_guarded(reply: str, on_event=None):
    """Guard me phanse jawab se tool-call nikaal kar asal me
    chalao. Safal ho to (naya_jawab, tool_chala_kya); embedded
    call na mile ya chalana hi na bane to None."""
    tool_call = _extract_tool_call(reply or "")
    if tool_call is None:
        return None
    log(f"GUARD-RECOVERY: jawab ke andar {tool_call['tool']} "
        "call mili - use asal me chala raha hu")
    with _history_lock:
        # Gadbad jawab history se hatao - recovery uski jagah
        # lega, warna dimag usi kachre ko dekh kar phir bhatkega.
        if _history and _history[-1].get("role") == "model":
            _history.pop()
        contents = list(_history[-_HISTORY_SEND_MAX:])
    note = ("[Tumhara pichhla jawab kacche tool-call JSON ki "
            "shakal me bahar aane wala tha, isliye roka gaya. "
            "Wahi kaam ab asal tool se karo: jo tool chalana tha "
            "use abhi chalao aur kaam pura karke aakhri jawab "
            "saade shabdon me do.]")
    contents = contents + [{"role": "user",
                            "parts": [{"text": note}]}]
    extra = {"on_event": on_event} if on_event is not None else {}
    reply2, used2 = _brain_run(contents, **extra)
    if used2 is None:
        return None
    return reply2, used2


def _plain_reask(contents: list, on_event=None):
    """Dimag se EK baar saade shabdon me jawab maango - koi
    JSON, koi tool-format nahi. Safal ho to saaf jawab (ya
    None jab run hi fail ho jaye)."""
    strict = ("[Ek mahatvapurna nirdesh: tumhara pichhla jawab "
              "takneeki JSON ki shakal me aa gaya tha jo user ko "
              "nahi dikh sakta. Ab user ke hukum ka jawab SIRF "
              "saade shabdon me do - koi JSON nahi, koi tool "
              "call nahi, koi code block nahi. Jo kaam ho chuka "
              "hai use shabdon me batao; jo nahi hua uski saaf "
              "wajah shabdon me do.]")
    run_contents = list(contents) + [
        {"role": "user", "parts": [{"text": strict}]}]
    extra = {"on_event": on_event} if on_event is not None else {}
    reply, used = _brain_run(run_contents, **extra)
    if used is None:
        return None
    return reply


# --------------------------------------------------------------------------
# Aadha-hukum (v8.13) - upload/post wala hukum bina file ke
# naam ke aaye aur dimag bina dekhe "kaunsi?" puchh le, to wo
# jawab roka jata hai: ek andar wala hukum dimag ko pehle
# find_file se KHUD dhoondhne par majboor karta hai. Prompt
# me bhi yahi niyam hai (KAAM point 10); ye mechanism us
# niyam ki peeche wali suraksha hai.
# --------------------------------------------------------------------------

_UPLOADISH_RE = re.compile(
    r"\b(upload|post|share|publish|schedule|daal\s*do|daalo|"
    r"bhej\s*do|bhejo)\b", re.IGNORECASE)
_FILE_MENTION_RE = re.compile(
    r"[\w\-. ]+\.(mp4|mov|mkv|avi|webm|mp3|wav|m4a|jpg|jpeg|"
    r"png|webp|gif|pdf|zip|txt|docx?)\b", re.IGNORECASE)
_QUESTIONY_RE = re.compile(
    r"\?|kaunsi|kaun sa|kaunsa|konsi|konsa|which file|"
    r"kya upload|kya post|kis file", re.IGNORECASE)


def _half_order_hint(message: str, reply: str, used_tool,
                     on_event=None):
    """Aadha-hukum pakdo: bina file wala upload/post hukum +
    bina tool chale sawaal-wala jawab = pehle khud dhoondo.
    Sudhra hua (jawab, tool_chala_kya) mile, warna None
    (matlab: ye pattern nahi hai, jawab jaisa hai waisa jaye)."""
    if used_tool:
        return None
    if not _UPLOADISH_RE.search(message or ""):
        return None
    if _FILE_MENTION_RE.search(message or ""):
        return None
    if not _QUESTIONY_RE.search(reply or ""):
        return None
    log("AADHA-HUKUM: bina file wala hukum aur bina dekhe "
        "sawaal - find_file wala andar-hukum bhej raha hu")
    with _history_lock:
        if _history and _history[-1].get("role") == "model":
            _history.pop()
        contents = list(_history[-_HISTORY_SEND_MAX:])
    note = ("INTERNAL INSTRUCTION (user ko mat dikhana): User "
            "ne upload/post wala hukum diya hai lekin koi file "
            "NAHI batayi, aur tumne bina dekhe sawaal puchh "
            "liya - ye galat hai. Pehle find_file tool se khud "
            "dhoondo: hukum ke shabdo se aur aam media naamo "
            "(video, reel, mp4) se khoj karo. Ek mazboot file "
            "mile to usi par aage ka kaam karo aur jawab me "
            "saaf batao kaunsi file chuni. Kai milein to sirf "
            "ek line me sabse upar ke naam gin kar chunne ko "
            "kaho. Ek bhi na mile to tab ek chhota sawaal pucho.")
    contents = contents + [{"role": "user",
                            "parts": [{"text": note}]}]
    extra = {"on_event": on_event} if on_event is not None else {}
    reply2, used2 = _brain_run(contents, **extra)
    if used2 is None:
        return None
    return reply2, used2


def _finalize_reply(message: str, contents: list, reply: str,
                    used_tool, on_event=None) -> str:
    """Brain ke jawab ko user tak pahunchane se pehle ki saari
    jaanch ek jagah: error passthrough, aadha-hukum sudhaar,
    guard khud-recovery, discipline re-ask - aur sabse aakhir
    me (sab fail ho tab) canned guard line. Har bahar jane
    wala jawab yahin se guzarta hai."""
    extra = {"on_event": on_event} if on_event is not None else {}
    if used_tool is None:
        return _guard_no_tool_json(reply)  # error message
    hinted = _half_order_hint(message, reply, used_tool, **extra)
    if hinted is not None:
        reply, used_tool = hinted
        if used_tool is None:
            return _guard_no_tool_json(reply)
    if _TOOL_JSON_SHAPE.search(reply or ""):
        # Guard trip - pehle khud-recovery: andar chhupa
        # tool-call asal me chalao aur loop aage badhao.
        recovered = _recover_tool_from_guarded(reply, **extra)
        if recovered is not None:
            reply, used_tool = recovered
            if used_tool is None:
                return _guard_no_tool_json(reply)
    if not _TOOL_JSON_SHAPE.search(reply or ""):
        if used_tool or not _has_action_intent(message):
            return reply
        # Discipline re-ask: sirf EK baar. Pehle history se wo
        # text-wala model jawab hatao (re-ask uski jagah lega),
        # phir sakht hukum ke saath dimag dobara chalao.
        log("DISCIPLINE: action hukum par koi tool nahi chala - "
            "strict re-ask (ek baar)")
        with _history_lock:
            if _history and _history[-1].get("role") == "model":
                _history.pop()
        strict_contents = contents + [
            {"role": "user", "parts": [{"text": _STRICT_REASK}]}]
        reply2, used2 = _brain_run(strict_contents, **extra)
        if used2 is None:
            return _guard_no_tool_json(reply)  # re-ask bhi fail
        return _guard_no_tool_json(reply2)
    # Recovery ke baad bhi jawab me kaccha JSON hai - ab EK
    # baar saade shabdon me re-ask, phir hi canned line.
    log("GUARD: recovery ke baad bhi JSON - saade shabdon me "
        "ek re-ask")
    with _history_lock:
        if _history and _history[-1].get("role") == "model":
            _history.pop()
        base = list(_history[-_HISTORY_SEND_MAX:])
    plain = _plain_reask(base, **extra)
    if plain is not None and not _TOOL_JSON_SHAPE.search(plain):
        return plain
    return _guard_reply_text()


# --------------------------------------------------------------------------
# ROKO - STOP mechanism (v8.16). User ki shikayat: beech me
# "roko" bolne par agent rukta NAHI tha - chal raha kaam pehle
# khatm hota tha, "roko" ek naye sandesh ki tarah line me lag
# jata tha. Ab ek thread-safe stop flag hai:
# - Har naye task ki shuruaat me flag saaf hota hai.
# - Brain/tool loop ke HAR kadam se pehle (har brain call se
#   pehle aur har tool chalane se pehle) flag check hota hai;
#   set ho to loop WAHI ruk jata hai - koi aur kadam nahi.
# - Rukne wala jawab aam final jawab ki jagah jata hai: pehli
#   line "Ruk gaya", phir kis kadam par ruka + ab tak ka
#   progress.
# - Trigger do raaste: (a) UI ka lal "⛔ Roko" button ->
#   POST /stop (halka endpoint, chal rahe /ask ko block nahi
#   karta - server threading hai); (b) /ask me SIRF stop wala
#   sandesh jab koi task chal raha ho -> line me nahi lagta,
#   flag set hokar turant jawab aata hai.
# SACH KI SEEMA (isse zyada vaada kabhi nahi): jo brain call
# ya tool USI PAL chal raha hai, wo beech me kata nahi ja
# sakta - rukna uske pure hote hi AGLE kadam par hota hai
# (v8.16 ke 45s wale NVIDIA timeout ke baad zyada se zyada
# utni der). Koi task chal hi na raha ho to "roko" par aam
# dostana jawab milta hai.
# --------------------------------------------------------------------------

_STOP_EVENT = threading.Event()
_TASK_COUNT_LOCK = threading.Lock()
_TASK_COUNT = 0


def _request_stop() -> None:
    """Rukne ka hukum darj karo - chalta loop agle kadam par
    rukega. Chal rahe call/tool ko beech me NAHI katata."""
    _STOP_EVENT.set()
    log("STOP: rukne ka hukum mila - loop agle kadam par rukega")


def _stop_requested() -> bool:
    return _STOP_EVENT.is_set()


def _clear_stop() -> None:
    _STOP_EVENT.clear()


def _task_started() -> None:
    global _TASK_COUNT
    with _TASK_COUNT_LOCK:
        _TASK_COUNT += 1


def _task_finished() -> None:
    global _TASK_COUNT
    with _TASK_COUNT_LOCK:
        _TASK_COUNT = max(0, _TASK_COUNT - 1)


def _tasks_running() -> int:
    with _TASK_COUNT_LOCK:
        return _TASK_COUNT


# Pura sandesh inhi me se ek ho (ya inhi shabdon se bana ho)
# to wo rukne ka hukum hai, naya task NAHI.
_STOP_PHRASES = {"roko", "ruko", "ruk", "ruk jao", "ruk jayo",
                 "band karo", "band kar do", "stop", "stop karo",
                 "bas karo", "bas"}
_STOP_TOKENS = {"roko", "ruko", "ruk", "jao", "jayo", "band",
                "bas", "karo", "kar", "do", "stop"}
_STOP_STRONG = {"roko", "ruko", "ruk", "band", "bas", "stop"}


def _is_stop_message(message: str) -> bool:
    """Pura sandesh SIRF rukne wala hukum hai to True.

    Chhota set, sakht jaanch: sandesh in shabdon ke alawa kuch
    aur rakhe (jaise "video roko mat", "roko aur batao") to ye
    rukne ka hukum NAHI - aam sandesh hai. Galat pehchan se
    asal kaam ruk jaye, ye dheere rukne se bura hai."""
    text = (message or "").strip().lower()
    if not text or len(text) > 30:
        return False
    text = re.sub(r"[!?.,\s]+", " ", text).strip()
    if not text:
        return False
    if text in _STOP_PHRASES:
        return True
    tokens = text.split()
    return (all(t in _STOP_TOKENS for t in tokens)
            and any(t in _STOP_STRONG for t in tokens))


def _stopped_message(tracker, next_tool: str = None) -> str:
    """Rukne par aakhri jawab: pehli line me 'Ruk gaya', phir
    kis kadam par ruka aur ab tak kya ho gaya (progress)."""
    lines = ["Ruk gaya — tumhare rokne par kaam wahi rok "
             "diya hai."]
    if next_tool:
        lines.append(f"Ye kadam shuru hi nahi kiya: "
                     f"{_tool_status_text(next_tool)}")
    progress = list(getattr(tracker, "progress", []) or [])
    if progress:
        lines.append("Ab tak ye ho gaya tha:\n"
                     + _progress_text(progress))
    else:
        lines.append("Ab tak koi kadam pura nahi hua tha.")
    lines.append("Bacha hua kaam nahi kiya hai. Bolo to wahi "
                 "se aage badhu, ya naya kaam do.")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Tez jawab - FAST PATH (v8.16). User ki shikayat: chhota sawal
# ("hua?", "ho gaya kya?") bhi pure tool-loop se guzarta tha;
# pehla dimag (NVIDIA ka dheera free endpoint) atak jaye to
# minute-bhar sirf "soch raha hai" dikhta tha - haan/na tak
# jaldi nahi aata tha. Ab pakka chhota status/haan-na sawal
# seedhi se PEHLE ek halki tez call se nibatta hai: Groq
# (sabse tez dimag) chhote budget par, wo key na ho to
# MiniMax. Classifier jaan-boojh kar sakht hai: zara bhi shak
# ho ki ye hukum ho sakta hai to fast path NAHI khulta, aam
# loop hi chalta hai - galat roka hua hukum dheere jawab se
# kahin bura hai. Fast call fail ho (error, khaali jawab,
# tool-call wali shakal) to bhi chup chaap aam loop - user ko
# kabhi pata nahi chalta ki pehle ye raasta try hua tha.
# --------------------------------------------------------------------------

_FASTPATH_MAX_CHARS = 120
_FASTPATH_MAX_TOKENS = 400

_FASTPATH_INSTRUCTION = (
    "[TEZ JAWAB WALA KADAM: User ka chhota sawal hai. Jawab "
    "ki PEHLI line me sirf nateeja do - haan/na, ya hua/"
    "nahi-hua, jaisa sawal ho waisa. Uske baad zyada se zyada "
    "EK line aur. Koi tool call NAHI, koi lambi tafseel NAHI.]")

# Hukum wale roop - inme se kuch bhi mile to fast path band.
# Bare "upload" jaise shabd yahan NAHI hain: "video upload
# hua?" ek status sawal hai; hukum uske "kar do / karo" wale
# roop se pakda jata hai.
_FASTPATH_ORDER_RE = re.compile(
    r"\b(kar\s*do|kardo|karo|kar\s*de|karde|kholo|khol\s*do|"
    r"banao|bana\s*do|bhejo|bhej\s*do|lagao|laga\s*do|chalao|"
    r"chala\s*do|hatao|hata\s*do|nikalo|likho|likh\s*do|"
    r"dhoondo|dhundo|dikhao|dikha\s*do|roko|rok\s*do|"
    r"band\s*kar|start\s*kar|set\s*kar|add\s*kar|"
    r"upload\s*kar|download\s*kar|delete\s*kar|post\s*kar|"
    r"share\s*kar|publish\s*kar|schedule\s*kar|save\s*kar|"
    r"open\s*kar|create\s*kar|install\s*kar|update\s*kar|"
    r"yaad\s*dila|remind|reminder|alarm)\b", re.IGNORECASE)

# Sirf "?" wale aam sawal ke raaste par bare angrezi hukum
# shabd bhi rok hain (jaise "can you open it?").
_FASTPATH_BARE_VERB_RE = re.compile(
    r"\b(upload|download|delete|open|create|start|play|send|"
    r"make|write|post|share|publish|install|restart|update|"
    r"remove|close|stop|launch|run)\b", re.IGNORECASE)

# Pakke status / haan-na wale pattern.
_FASTPATH_STATUS_RE = re.compile(
    r"(ho\s*gaya|ho\s*gya|hua\s*hai|nahi\s*hua|nahin\s*hua|"
    r"kya\s*hua|hua\s*kya|hua\b|hoga\b|hogi\b|ho\s*raha|"
    r"ho\s*rha|chal\s*raha|chal\s*rha|kar\s*diya|ho\s*paya|"
    r"theek\s*hai|thik\s*hai|sahi\s*hai|kyu\s*nahi|"
    r"kyon\s*nahi|kyun\s*nahi|kab\b|complete|done|ready|"
    r"status|khatam|aa\s*gaya|aa\s*gayi|mil\s*gaya|"
    r"ban\s*gaya)", re.IGNORECASE)

# Waqt ke saath wala schedule roop (jaise "7 baje") - ye
# hukum hota hai, status sawal nahi.
_FASTPATH_TIME_RE = re.compile(
    r"\b\d+\s*(baje|am|pm|min|minute|ghante)\b", re.IGNORECASE)

_FASTPATH_URL_RE = re.compile(
    r"(https?://|www\.)", re.IGNORECASE)


def _is_fastpath_question(message: str) -> bool:
    """Chhota status/haan-na sawal hai to True, warna False.

    Teen jaanch, teeno paas hona zaroori hai:
    1. Chhota (<=120 akshar); koi URL, path, file naam ya
       waqt-wala schedule roop nahi; photo wala andar ka
       sandesh (augmented text) nahi.
    2. Koi hukum wala roop NAHI (kar do, kholo, banao...).
    3. Ya to pakka status pattern mile, ya sawal ho ("?") aur
       koi bare hukum shabd bhi na ho.
    Shak ho to False - aam loop hi sahi raasta hai.
    """
    msg = (message or "").strip()
    if not msg or len(msg) > _FASTPATH_MAX_CHARS:
        return False
    low = msg.lower()
    if "photo bheji hai" in low:
        return False
    if _FASTPATH_URL_RE.search(msg) or _FILE_MENTION_RE.search(msg):
        return False
    if "\\" in msg or re.search(r"[a-zA-Z]:[\\/]", msg):
        return False
    if _FASTPATH_TIME_RE.search(low) \
            or _FASTPATH_ORDER_RE.search(low):
        return False
    if _FASTPATH_STATUS_RE.search(low):
        return True
    if "?" in msg and not _FASTPATH_BARE_VERB_RE.search(low):
        return True
    return False


def _fastpath_answer(contents: list):
    """Fast path ki asal call: Groq pehle (sabse tez, chhota
    budget), wo key na ho to MiniMax usi budget par.

    Safal ho to saaf jawab (string) aur jawab history me bhi
    jud jata hai (baat ka silsila na toote). Koi bhi gadbad -
    error, khaali jawab, tool-call/JSON wali shakal - ho to
    None: caller chup chaap aam loop chalata hai.
    """
    try:
        messages = _to_openai_messages(contents)
    except Exception:
        return None
    if messages and messages[0].get("role") == "system":
        messages[0] = dict(messages[0])
        messages[0]["content"] = (
            messages[0].get("content", "")
            + "\n\n" + _FASTPATH_INSTRUCTION)
    reply = None
    if GROQ_API_KEY:
        try:
            reply = _groq_call(messages,
                               max_tokens=_FASTPATH_MAX_TOKENS)
            log("FASTPATH: jawab Groq se aaya")
        except Exception as exc:
            log(f"FASTPATH: Groq fail ({exc}) - aam loop")
            return None
    elif NVIDIA_API_KEY:
        try:
            reply = _nvidia_chat(messages, NVIDIA_MODEL,
                                 max_tokens=_FASTPATH_MAX_TOKENS)
            log("FASTPATH: jawab NVIDIA (MiniMax) se aaya")
        except Exception as exc:
            log(f"FASTPATH: NVIDIA fail ({exc}) - aam loop")
            return None
    else:
        return None
    reply = (reply or "").strip()
    if not reply or _extract_tool_call(reply) is not None \
            or _TOOL_JSON_SHAPE.search(reply):
        log("FASTPATH: jawab theek shakal me nahi - aam loop")
        return None
    with _history_lock:
        _history.append({"role": "model",
                         "parts": [{"text": reply}]})
    return reply


# --------------------------------------------------------------------------
# Samajh gate (v8.17) - PEHLE SAMJHO. User ki asal shikayat
# (screenshot, 2026-11-21): wo beech me samjha raha tha -
# "abhi maine tume bola ki ye sab khojo jo tum find karne
# chale gye abhi baat kar rha achhe se samjho fhir kaam
# karna" - aur agent ne jawab dene ki jagah phir se
# find_file/list_files chala diye. Wajah: dimag har sandesh
# ko hukum samajh kar tool-loop me ghus jata tha; samjhane
# wala sandesh bhi usi raaste jata tha. Ab aisa sandesh CODE
# se pakda jata hai (sirf prompt se nahi), aam loop se pehle:
# ek TEXT-ONLY dimag call hoti hai jisme tool chalana hi
# band hai (jawab parse hi nahi hota), aur dimag ko hukum
# hai - (a) apne shabdon me dohrao ki kya samjha, (b) kuch
# saaf na ho to EK chhota sawal, (c) koi kaam shuru NAHI
# karna; sandesh me hukum ghula ho to aakhir me ek line me
# go-ahead maango ("bolo to shuru karu?"). Gate hukum wale
# shabdon par bhi jeet-ta hai (dant me "khojo" tha, phir bhi
# gate laga) - lekin saaf hukum (bina samjhane wale nishan
# ke), file-naam ya URL wale sandesh gate par kabhi nahi
# rukte. Text-only call saare dimagon par fail ho to chup
# chaap aam loop - user kabhi bina jawab ke nahi rehta.
# --------------------------------------------------------------------------

_SAMAJH_GATE_INSTRUCTION = (
    "[SAMAJH WALA KADAM: User abhi koi naya hukum NAHI de "
    "raha - wo kuch SAMJHA raha hai, sudhaar bata raha hai, "
    "ya pichhli baat par narazgi dikha raha hai. Is kadam me "
    "tool chalana bilkul band hai aur koi kaam shuru NAHI "
    "karna hai. Sirf ye karo: (1) Apne shabdon me dohra kar "
    "batao ki tumne kya samjha - 2-3 chhoti lines me. "
    "(2) Kuch saaf na ho to aakhir me EK chhota sawal puchho. "
    "(3) Agar user ki baat me koi kaam/hukum ghula hua hai, "
    "to aakhir me ek line me puchho: 'bolo to shuru karu?' - "
    "khud se shuru mat karo. Jawab Hinglish me, shaant aur "
    "saaf.]")

# Samjhane/dantne ke pakke nishan. Sirf wahi shabd/roop jo
# aam hukum me nahi aate: "dhoondo", "kholo", "kar do" jaise
# hukum-shabd yahan jaan-boojh kar NAHI hain - saaf hukum
# gate par nahi rukna chahiye.
_SAMAJH_RE = re.compile(
    r"(samajh|samjho|samjhaya|samjhao|suno|"
    r"baat\s+kar\s+rh|baat\s+kar\s+rah|baat\s+suno|"
    r"abhi\s+bola|maine\s+bola|maine\s+tume\s+bola|"
    r"maine\s+tumhe\s+bola|phir\s+kaam\s+karna|"
    r"pehle\s+samajh|dhyan\s+se|aise\s+nahi|"
    r"nahi\s+bola\s+tha|galat\s+kar)",
    re.IGNORECASE)


def _is_samajh_message(message: str) -> bool:
    """User samjha/dant raha hai (hukum nahi de raha) to True.

    Teen shartein:
    1. Sandesh me samjhane ka pakka nishan mile.
    2. Koi asal file-naam ya URL na ho - wo kaam wala
       sandesh hai, aam raaste jayega (fast path wali hi
       rok yahan bhi).
    3. Photo wala andar ka sandesh nahi (uska caption kaam
       wala hota hai, use tools chahiye).
    Nishan mile to gate hukum wale shabdon par bhi jeet-ta
    hai - dant me "khojo" hone se wo hukum nahi ban jata.
    """
    msg = (message or "").strip()
    if not msg:
        return False
    low = msg.lower()
    if "photo bheji hai" in low:
        return False
    if _FASTPATH_URL_RE.search(msg) or _FILE_MENTION_RE.search(msg):
        return False
    if "\\" in msg or re.search(r"[a-zA-Z]:[\\/]", msg):
        return False
    return bool(_SAMAJH_RE.search(low))


def _samajh_answer(contents: list):
    """Gate ki text-only call: dimag seedhi (NVIDIA MiniMax
    -> Groq -> Gemini) par EK call, system ke aakhir me
    samajh wali hidayat jod kar.

    Tool chalana band hai - is raaste me jawab ka tool-call
    parse hi nahi hota, run_tool kabhi bulaya hi nahi jata;
    bahar jane se pehle jawab _guard_no_tool_json se bhi
    guzarta hai (caller par). Safal ho to saaf jawab aur wo
    history me bhi jud jata hai; saare dimag fail hon to
    None - caller aam loop chalata hai.
    """
    gate_contents = list(contents) + [
        {"role": "user",
         "parts": [{"text": _SAMAJH_GATE_INSTRUCTION}]}]
    reply = None
    if NVIDIA_API_KEY:
        try:
            reply = _nvidia_chat(
                _to_openai_messages(gate_contents), NVIDIA_MODEL,
                max_tokens=_NVIDIA_MAX_TOKENS)
            log("SAMAJH GATE: jawab NVIDIA (MiniMax) se aaya")
        except Exception as exc:
            log(f"SAMAJH GATE: NVIDIA fail ({exc}) - agli seedhi")
            reply = None
    if reply is None and GROQ_API_KEY:
        try:
            reply = _groq_call(_to_openai_messages(gate_contents))
            log("SAMAJH GATE: jawab Groq se aaya")
        except Exception as exc:
            log(f"SAMAJH GATE: Groq fail ({exc}) - agli seedhi")
            reply = None
    if reply is None and GEMINI_API_KEY:
        try:
            reply = _gemini_call(gate_contents,
                                 _ladder_models()[0])
            log("SAMAJH GATE: jawab Gemini se aaya")
        except Exception as exc:
            log(f"SAMAJH GATE: Gemini fail ({exc}) - aam loop")
            reply = None
    reply = (reply or "").strip()
    if not reply:
        return None
    with _history_lock:
        _history.append({"role": "model",
                         "parts": [{"text": reply}]})
    return reply


def brain_ask(message: str, on_event=None) -> str:
    """Dimag se jawab lao - Groq pehle (key ho to), Gemini ladder
    peeche, aur discipline re-ask ke saath.

    Dono dimag fail hon to jawab AAKHRI error ki class se banta hai
    (busy -> busy message, timeout -> slow message, 404 -> plain
    message). Jawab aa jaye lekin hukum action wala ho aur koi tool
    na chala ho (sirf salah mili ho), to ek baar strict re-ask
    hota hai - ye niyam dono dimagon par lagta hai.
    Har bahar jane wala jawab _finalize_reply se guzarta hai:
    aadha-hukum sudhaar, guard khud-recovery (v8.13) aur sabse
    aakhir me canned guard line - kaccha tool-call JSON user ko
    kabhi nahi dikhta.
    on_event (v8.13 streaming): (kind, text) wala callback UI ko
    'status'/'delta' events bhejta hai; None ho to vyavhaar
    bilkul v8.12 jaisa (koi streaming nahi).
    v8.16: pakka chhota status/haan-na sawal pehle fast path
    se nibatta hai (classifier + _fastpath_answer); kaam wale
    hukum par pehle dimag ke jawab se PEHLE ek turant tasalli
    wali status line jati hai; aur rukne par aaya jawab
    finalize ki re-ask mashinari se nahi guzarta (warna roka
    hua kaam 'discipline' ke naam par phir shuru ho jata).
    v8.17: samjhane/dantne wala sandesh sabse pehle SAMAJH
    GATE se nibatta hai (text-only call, tool band) - fast
    path se bhi pehle, kyunki samajh wali baat ka jawab
    pehle aana chahiye, kaam baad me.
    """
    with _history_lock:
        _history.append({"role": "user", "parts": [{"text": message}]})
        # Record intact rehta hai; dimag ko sirf aakhri
        # _HISTORY_SEND_MAX baariyan jati hain (v8.12).
        contents = list(_history[-_HISTORY_SEND_MAX:])
    extra = {"on_event": on_event} if on_event is not None else {}
    if _is_samajh_message(message):
        # Samajh gate (v8.17): samjhane/dantne wala sandesh
        # tool-loop me hi nahi jata - pehle text-only jawab.
        # Gate fail ho (saare dimag) to neeche aam loop hi
        # chalega; user bina jawab ke kabhi nahi rehta.
        log("SAMAJH GATE: pehle jawab, tool nahi")
        gated = _samajh_answer(contents)
        if gated is not None:
            return _guard_no_tool_json(gated)
        log("SAMAJH GATE: text-only call fail - aam loop par gira")
    if _is_fastpath_question(message):
        fast = _fastpath_answer(contents)
        if fast is not None:
            return _guard_no_tool_json(fast)
    if on_event is not None and _has_action_intent(message):
        # Turant tasalli (v8.16): kaam wala hukum aate hi,
        # pehle dimag ke jawab se pehle, ek line - user ko
        # khamosh "soch raha hai" wali haalat nahi milti.
        _emit_event(on_event, "status",
                    "Samajh gaya — kaam shuru kar raha hu…")
    reply, used_tool = _brain_run(contents, **extra)
    if _stop_requested():
        # Rukne par aaya jawab ayn waisa jaye - finalize ki
        # discipline re-ask roke hue kaam ko phir shuru kar
        # degi, isliye sirf guard ki jaanch kaafi hai.
        return _guard_no_tool_json(reply)
    return _finalize_reply(message, contents, reply, used_tool,
                           **extra)


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


def _ask_agent_core(message: str, image: str = None,
                    image_mime: str = None, on_event=None) -> str:
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
    # Config hot-reload (v8.6): config.env badla ho to nayi keys/
    # PIN yahi se lagoo - engine restart ki zaroorat nahi.
    _maybe_reload_config()
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
        if _is_dimag_test_command(message):
            return tool_dimag_test()
        extra = {"on_event": on_event} if on_event is not None else {}
        return brain_ask(augmented, **extra)
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
    if _is_dimag_test_command(message):
        # 'dimag test karo' - dono dimagon ki asal jaanch (v8.6).
        # Brain se pehle pakda jata hai, bilkul update ki tarah -
        # warna test khud usi dimag se hota jo fail ho raha hai.
        return tool_dimag_test()
    demo_reply = demo_ask(message)
    if demo_reply is not None:
        return demo_reply
    if GEMINI_API_KEY or GROQ_API_KEY or NVIDIA_API_KEY:
        extra = {"on_event": on_event} if on_event is not None else {}
        return brain_ask(message, **extra)
    return ("Abhi main demo mode me hu - bina kisi key ke main sirf "
            "tool wale kaam kar sakta hu. 'help' likho, commands dikha dunga. "
            "Free chat ke liye config.env me apni free Gemini key (ya "
            "tez jawab ke liye Groq key, ya NVIDIA key) daal do.")


def ask_agent(message: str, image: str = None,
              image_mime: str = None, on_event=None) -> str:
    """Har /ask ka asal darwaza (v8.13): andar ka kaam
    _ask_agent_core karta hai; ye wrapper do nayi zimmedariyan
    sambhalta hai -
    1. Diary: user ki baat + agent ne kya kiya, tareekh ke
       saath baatein.jsonl me (Amendment 1). Photo wale turn
       par sirf caption save hota hai, photo kabhi nahi.
    2. Session prefix: startup khud-jaanch ka one-time notice/
       sehat line session ke PEHLE jawab ke upar judta hai.
    Diary me jaane wala 'kya kiya' hissa ASAL jawab se banta
    hai (prefix usme nahi jata).
    3. Roko (v8.16): sirf-stop wala sandesh naye task ki
       tarah line me NAHI lagta - koi task chal raha ho to
       stop flag set hokar turant jawab aata hai; na chal
       raha ho to dostana 'koi kaam chal hi nahi raha' wala
       jawab. Baaki har sandesh par naya task shuru hone se
       pehle stop flag saaf hota hai aur task-ginti badhti
       hai (chal rahe task ki pehchan isi ginti se hoti hai).
    """
    if not image and _is_stop_message(message):
        if _tasks_running() > 0:
            _request_stop()
            reply = ("Bol diya — chalta kaam agle kadam par "
                     "ruk jayega.\nJo call ya kadam is pal chal "
                     "raha hai wo beech me nahi katata, isliye "
                     "rukne me kuch second lag sakte hain. "
                     "Rukte hi wahi jawab ayega ki kaam kahan "
                     "ruka aur kya bacha hai.")
        else:
            reply = ("Koi kaam chal hi nahi raha hai, bhai — "
                     "rukne ko kuch hai hi nahi. Bolo, kya "
                     "karna hai?")
        try:
            _diary_append((message or "").strip(),
                          re.sub(r"\s+", " ", reply).strip())
        except Exception:
            pass
        prefix = _take_session_prefix()
        if prefix:
            return prefix + "\n\n" + reply
        return reply
    # Naya task: purana stop hukum is par lagu nahi - flag
    # pehle saaf, aur chalta-hua-task wali ginti me ye darj.
    _clear_stop()
    _task_started()
    try:
        reply = _ask_agent_core(message, image=image,
                                image_mime=image_mime,
                                on_event=on_event)
    finally:
        _task_finished()
    try:
        did = re.sub(r"\s+", " ", (reply or "")).strip()
        _diary_append((message or "").strip(), did)
    except Exception as exc:
        log(f"DIARY wrapper fail (jawab par asar nahi): {exc}")
    prefix = _take_session_prefix()
    if prefix:
        return prefix + "\n\n" + reply
    return reply

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

UI_VERSION = 4

UI_HTML = r'''<!DOCTYPE html>
<!-- myagent-ui-version: 4 -->
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
  .workline { font-size: 12.5px; color: #8FB6DE; padding: 2px 6px 2px 14px; margin: -6px 0 9px; letter-spacing: .2px; animation: in .24s ease-out; }
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
  #stopBtn {
    flex: 0 0 auto; align-self: center; padding: 10px 14px; border-radius: 999px; cursor: pointer;
    font-family: inherit; font-size: 13.5px; font-weight: 800; color: #FFE1E1; white-space: nowrap;
    background: linear-gradient(180deg, rgba(255,72,72,.30), rgba(185,22,22,.34));
    border: 1px solid rgba(255,110,110,.55);
    box-shadow: 0 6px 16px rgba(200,30,30,.35), inset 0 1px 0 rgba(255,255,255,.18);
  }
  #stopBtn:active { transform: scale(.94); }
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
  <button id="stopBtn" type="button" title="Chal raha kaam roko">⛔ Roko</button>
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
    else { payload.stream = true; }
    fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }).then(function (res) {
      if (res.status === 403) {
        hideTyping();
        setPin("");
        addBubble("agent", "PIN galat hai bhai — agent ne mana kar diya. config.env me jo AGENT_PIN rakha tha, wahi PIN dobara daalo.", true);
        openPinGate("PIN galat tha. Dobara try karo — PIN config.env file me AGENT_PIN ke saamne likha hai.");
        return;
      }
      var ctype = res.headers.get("Content-Type") || "";
      if (!photo && res.body && ctype.indexOf("text/event-stream") >= 0) {
        return readAskStream(res);
      }
      return res.text().then(function (bodyText) {
        hideTyping();
        var data = null;
        try { data = JSON.parse(bodyText); } catch (e) {}
        if (res.status !== 200 || !data || typeof data.reply !== "string") {
          addBubble("agent", "Kuch gadbad ho gayi (server se sahi jawab nahi aaya). Agent wali kaali window chal rahi hai ya nahi, ek baar dekh lo, phir dobara bhejo.", true);
          return;
        }
        addBubble("agent", data.reply);
      });
    }).catch(function () {
      hideTyping();
      addBubble("agent", "Agent se jud nahi paya — lagta hai program band hai. Pehle start.bat se agent chalao, phir ye page refresh karke dobara bhejo.", true);
    }).finally(function () {
      busy = false; sendBtn.disabled = false;
    });
  }

  /* Streaming jawab (v8.13): /ask se SSE frames aate hain -
     status (kaam chal raha hai wali chhoti line), delta
     (jawab ke tukde) aur final (PURA asal jawab). Bubble
     delta se bharti hai, lekin final aate hi usi se dobara
     render hoti hai: final hi asal hai, isliye stream beech
     me toote to bhi jawab na khota hai na dohra hota. */
  function readAskStream(res) {
    hideTyping();
    var row = addBubble("agent", "…");
    var bubbleEl = row.querySelector(".bubble");
    var reader = res.body.getReader();
    var decoder = new TextDecoder();
    var buf = "", streamed = "", gotFinal = false;
    function handleFrame(frame) {
      var ev = "message", dataLine = "";
      var lines = frame.split("\n");
      for (var i = 0; i < lines.length; i++) {
        if (lines[i].indexOf("event:") === 0) ev = lines[i].slice(6).replace(/^\s+|\s+$/g, "");
        else if (lines[i].indexOf("data:") === 0) dataLine += lines[i].slice(5).replace(/^\s+/, "");
      }
      if (!dataLine) return;
      var val = dataLine;
      try { val = JSON.parse(dataLine); } catch (e) {}
      if (typeof val !== "string") return;
      if (ev === "status") {
        var w = document.createElement("div");
        w.className = "workline"; w.textContent = val;
        chatEl.insertBefore(w, row); scrollDown();
      } else if (ev === "delta") {
        streamed += val;
        bubbleEl.innerHTML = renderRich(streamed); scrollDown();
      } else if (ev === "final") {
        gotFinal = true;
        bubbleEl.innerHTML = renderRich(val || streamed || "(koi jawab nahi aaya)");
        scrollDown();
      }
    }
    function pump() {
      return reader.read().then(function (part) {
        if (part.done) {
          if (buf.replace(/\s+/g, "")) handleFrame(buf);
          if (!gotFinal && !streamed) bubbleEl.innerHTML = renderRich("(koi jawab nahi aaya)");
          return;
        }
        buf += decoder.decode(part.value, { stream: true });
        var idx;
        while ((idx = buf.indexOf("\n\n")) >= 0) {
          handleFrame(buf.slice(0, idx));
          buf = buf.slice(idx + 2);
        }
        return pump();
      });
    }
    return pump().catch(function () {
      if (!gotFinal && !streamed) {
        bubbleEl.innerHTML = renderRich("Jawab aate-aate ruk gaya — dobara bhej kar dekho.");
      }
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

  /* Roko button (v8.16): chal raha kaam rokne ke liye alag
     halka /stop call - chal rahe /ask ko block nahi karta.
     Jawab ek chhoti workline bankar dikhta hai. */
  document.getElementById("stopBtn").addEventListener("click", function () {
    if (!getPin()) { openPinGate(""); return; }
    function note(txt) {
      var w = document.createElement("div");
      w.className = "workline"; w.textContent = txt;
      chatEl.appendChild(w); scrollDown();
    }
    fetch("/stop", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pin: getPin() })
    }).then(function (res) {
      if (res.status === 200) {
        note("⛔ Rukne ko bol diya — chalta kaam agle kadam par rukega.");
      } else {
        note("⛔ Roko nahi bheja ja saka (PIN galat ya server band hai).");
      }
    }).catch(function () {
      note("⛔ Roko nahi bheja ja saka — agent band lag raha hai.");
    });
  });

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
            if NVIDIA_API_KEY and GROQ_API_KEY and GEMINI_API_KEY:
                mode = "nvidia+groq+gemini"
            elif NVIDIA_API_KEY:
                mode = "nvidia"
            elif GROQ_API_KEY and GEMINI_API_KEY:
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
        if self.path == "/stop":
            # Roko endpoint (v8.16): halka aur turant - sirf
            # stop flag set karta hai. Server threading hai,
            # isliye ye chal rahe /ask ke SAATH parallel chalta
            # hai, use block nahi karta. PIN ki jaanch /ask
            # wali hi hai. Chal raha call/tool beech me nahi
            # katata - loop agle kadam par rukega (sach ki
            # seema yahi hai).
            payload = {}
            try:
                length = int(self.headers.get("Content-Length",
                                              "0"))
                payload = json.loads(
                    self.rfile.read(length) or b"{}")
            except Exception:
                payload = {}
            _maybe_reload_config()
            if AGENT_PIN:
                given = str(payload.get("pin", "") or
                            self.headers.get("X-Agent-PIN", ""))
                if not hmac.compare_digest(given, AGENT_PIN):
                    log("HTTP /stop REJECTED (wrong PIN)")
                    self._send_json(403, {"error": "wrong PIN"})
                    return
            _request_stop()
            self._send_json(200, {"ok": True,
                                  "task_running":
                                      _tasks_running() > 0})
            return
        if self.path != "/ask":
            self._send_json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            self._send_json(400, {"error": "bad JSON"})
            return
        # Config hot-reload (v8.6) PIN jaanch se pehle: config.env
        # me PIN/key badli ho to nayi settings ISI request se lagoo.
        _maybe_reload_config()
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
        img = img if isinstance(img, str) else None
        message = str(payload.get("message", ""))
        # Streaming (v8.13): UI "stream": true bheje aur photo
        # na ho to jawab SSE se bante-bante jata hai. Photo
        # wale turn aur purane client hamesha JSON wale raaste
        # par hi rehte hain (wo rasta ayn waisa hi hai).
        if payload.get("stream") and not img:
            self._ask_stream(message)
            return
        reply = ask_agent(message, image=img,
                          image_mime=payload.get("image_mime"))
        self._send_json(200, {"reply": reply})

    def _sse_send(self, event: str, data: str) -> None:
        """Ek SSE frame bhejo: event ka naam + JSON-encoded
        data (JSON isliye, taaki nayi lines/quotes frame ko
        kabhi na todein)."""
        frame = (f"event: {event}\n"
                 f"data: {json.dumps(data, ensure_ascii=False)}\n\n")
        self.wfile.write(frame.encode("utf-8"))
        self.wfile.flush()

    def _ask_stream(self, message: str) -> None:
        """Streaming wala /ask (v8.13): 'status' events (tool
        kadam), 'delta' events (jawab ke tukde) aur aakhir me
        EK 'final' event jisme PURA asal jawab hota hai - UI
        usi ko asal manta hai, isliye stream beech me toote
        to bhi jawab na khota hai na dohra hota. Content-
        Length nahi bhejte: HTTP/1.0 par body connection band
        hone par khatm hoti hai."""
        self.send_response(200)
        self.send_header("Content-Type",
                         "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        self.close_connection = True

        def _on_event(kind, text):
            try:
                self._sse_send(kind, text)
            except Exception:
                pass  # UI gaya to bhi agent apna kaam karega

        try:
            reply = ask_agent(message, on_event=_on_event)
        except Exception as exc:
            log(f"HTTP /ask stream fail: {exc}")
            reply = ("Kuch gadbad ho gayi - ek baar phir se "
                     "bolo, main dobara koshish karta hu.")
        try:
            self._sse_send("final", reply)
        except Exception:
            pass


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
    ensure_diary_file()
    # Startup khud-jaanch (v8.13): naya version + sehat -
    # background me, engine ko bina roke.
    _start_startup_checks()

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

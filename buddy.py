"""
buddy.py — A fully offline AI companion.
Uses Python stdlib only, with optional local Ollama integration.
"""

import json
import os
import random
import re
import sys
import urllib.error
import urllib.request
from collections import defaultdict

NAME = "Buddy"
MAX_HISTORY_ITEMS = 16
MAX_CONTEXT_MESSAGES = 8

MOOD_RESPONSES = {
    "happy": [
        "That’s awesome, I’m glad!",
        "Love to hear it!",
        "You’re radiating good vibes right now.",
    ],
    "sad": [
        "Hey, I’m here. Want to talk about it?",
        "That sounds rough. I’ve got time.",
        "I’m listening. No rush.",
    ],
    "bored": [
        "Okay let’s fix that. Ask me anything — trivia, deep questions, dumb jokes.",
        "Boredom is just curiosity with nowhere to go yet. Let’s find somewhere.",
        "Tell me the weirdest thing on your mind right now.",
    ],
    "angry": [
        "Oof. What happened?",
        "Let it out. I won’t judge.",
        "That sounds genuinely frustrating. Tell me more.",
    ],
    "anxious": [
        "Take a breath. I’m right here.",
        "Anxiety lies a lot. What’s the actual worst case?",
        "Let’s think through it together, no pressure.",
    ],
    "tired": [
        "Rest when you can. But I’m here if you want to talk.",
        "Tired body or tired mind?",
        "Even exhausted people deserve a good conversation.",
    ],
}

JOKES = [
    ("Why don’t scientists trust atoms?", "Because they make up everything."),
    ("I told my computer I needed a break.", "Now it won’t stop sending me Kit-Kat ads."),
    ("Why do programmers prefer dark mode?", "Because light attracts bugs."),
    ("What do you call a fake noodle?", "An impasta."),
    ("Why can’t you give Elsa a balloon?", "She’ll let it go."),
    (
        "I asked the library if they had books on paranoia.",
        "The librarian whispered: they’re right behind you.",
    ),
    ("What’s a computer’s favorite snack?", "Microchips."),
    ("Why did the scarecrow win an award?", "He was outstanding in his field."),
    ("How do you comfort a JavaScript developer?", "You console them."),
    ("What do you call cheese that isn’t yours?", "Nacho cheese."),
    ("Why do cows wear bells?", "Because their horns don’t work."),
    ("I’m reading a book about anti-gravity.", "It’s impossible to put down."),
]

FACTS = [
    "Honey never expires — archaeologists found 3000-year-old honey in Egyptian tombs and it was still good.",
    "Otters hold hands while sleeping so they don’t drift apart. It’s called a ‘raft’.",
    "A day on Venus is longer than a year on Venus — it spins that slowly.",
    "Crows remember human faces and hold grudges for years. Don’t mess with crows.",
    "There are more possible chess games than atoms in the observable universe.",
    "Wombat poop is cube-shaped. Scientists only figured out why in 2018 — elastic intestines.",
    "The inventor of the Pringles can is buried in a Pringles can.",
    "Bananas are technically berries. Strawberries are not.",
    "Oxford University is older than the Aztec Empire.",
    "Cleopatra lived closer in time to the Moon landing than to the construction of the Great Pyramid.",
    "A group of flamingos is called a flamboyance.",
    "If you remove all the empty space from atoms in the human body, humanity would fit in a sugar cube.",
    "The shark is older than the tree — sharks appeared ~450M years ago, trees ~350M years ago.",
    "Nintendo was founded in 1889. It started as a playing card company.",
    "Your brain generates about 23 watts of power while you’re awake. Enough to power a dim light bulb.",
    "There is a species of jellyfish that is biologically immortal — it can revert to its juvenile state.",
    "Humans share 50% of their DNA with bananas.",
    "The average person walks about 100,000 miles in their lifetime — roughly 4 times around Earth.",
]

ADVICE = {
    "friendship": [
        "The best friendships are low-maintenance but high-quality. Check in, even briefly.",
        "You don’t need to fix people’s problems — sometimes just being present IS the help.",
        "Friendships drift. That’s normal. A text can restart one that’s been quiet for years.",
    ],
    "motivation": [
        "Start embarrassingly small. Two minutes. One sentence. One pushup. Momentum compounds.",
        "You don’t wait to feel motivated — you act first, then motivation follows the action.",
        "Progress feels invisible from the inside. Zoom out. Look at last month, not last hour.",
    ],
    "stress": [
        "Name what’s actually wrong specifically. Vague dread is worse than a concrete problem.",
        "The 5-minute rule: if it won’t matter in 5 years, try to spend max 5 minutes worrying about it.",
        "You’re allowed to do less on hard days. Survival is also productivity.",
    ],
    "life": [
        "Most regrets are about things people didn’t do, not things they did.",
        "Being a beginner at something new is genuinely underrated. Lean into it.",
        "The people who seem to have it together are mostly also figuring it out.",
    ],
    "boredom": [
        "Pick up something purely because it interests you, not because it’s useful. That’s the best reason.",
        "Boredom is actually your brain asking for novelty. Give it something weird.",
        "Learn one absurd skill. Juggling, morse code, a card trick. You’ll never regret it.",
    ],
}

DEEP_QUESTIONS = [
    "If you woke up tomorrow with no memory, would you still be you?",
    "Is there a meaningful difference between a very convincing simulation of happiness and actual happiness?",
    "What would you do if you knew no one was watching and there were no consequences?",
    "Is it better to be honest and hurt someone, or kind and withhold the truth?",
    "Do you think people fundamentally change, or just reveal more of who they already were?",
    "If you could relive one day perfectly, would you? Or is the memory enough?",
    "What’s something you believe that most people around you don’t?",
]

COMPLIMENTS = [
    "The fact that you’re curious enough to talk to a local AI built from scratch? That’s actually pretty cool.",
    "Genuinely — most people wouldn’t even think to question what kind of conversations are possible offline.",
    "You ask real questions. That’s rarer than it sounds.",
    "I like talking to you. Even as a statistical process, I mean that.",
]

ROASTS = [
    "You’re talking to a Python script for fun. I respect it. Truly.",
    "I’m offline AI and I still give better answers than your last Google search, apparently.",
    "Look, I’m made of if-statements and probability, and I’m still more reliable than most people.",
]

WHAT_TO_DO = [
    "Try this: open a map, pick a country you know nothing about, and read its Wikipedia page top to bottom.",
    "Watch one documentary on a subject you’ve never cared about. You’ll care after.",
    "Write one sentence about how you feel right now. Just one. It helps more than it sounds.",
    "Go for a walk without music or a podcast. Just walk and think. Underrated.",
    "Text someone you haven’t spoken to in months. Just say hey.",
    "Learn the name of one constellation tonight. Go outside, find it.",
    "Pick a skill you’ve always said ‘I want to learn that someday’ and spend 20 minutes on it right now.",
]

MARKOV_SEED = """
I think the most interesting conversations happen at the edge of what you know.
Every question worth asking leads to three more questions worth asking.
The things that seem small usually matter the most in the end.
You can’t solve a problem from the same level of thinking that created it.
Most of what we call personality is just habit running on autopilot.
Curiosity is the only renewable resource that doesn’t deplete when you use it.
The present moment is the only place where anything actually happens.
Every person you meet is living a life as complex and vivid as your own.
The gap between who you are and who you want to be is exactly where growth lives.
Uncertainty is uncomfortable but certainty is usually just confidence hiding ignorance.
"""


class Markov:
    def __init__(self):
        self.chain = defaultdict(list)
        words = MARKOV_SEED.lower().split()
        for i in range(len(words) - 2):
            self.chain[tuple(words[i : i + 2])].append(words[i + 2])

    def gen(self, max_w=15):
        key = random.choice(list(self.chain.keys()))
        out = list(key)
        for _ in range(max_w):
            nxt = self.chain.get(tuple(out[-2:]))
            if not nxt:
                break
            out.append(random.choice(nxt))
            if out[-1].endswith("."):
                break
        s = " ".join(out)
        return s[0].upper() + s[1:] + ("" if s.endswith(".") else ".")


class OllamaClient:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2")
        timeout_raw = os.getenv("OLLAMA_TIMEOUT", "12")
        try:
            self.timeout = float(timeout_raw)
        except ValueError:
            self.timeout = 12.0
        self.debug = os.getenv("BUDDY_DEBUG_OLLAMA", "0").lower() in {"1", "true", "yes", "on"}
        self.enabled = os.getenv("BUDDY_USE_OLLAMA", "1").lower() not in {
            "0",
            "false",
            "no",
            "off",
        }

    def _log_debug(self, msg):
        if self.debug:
            print(f"[buddy][ollama] {msg}", file=sys.stderr, flush=True)

    def ask(self, prompt, history):
        if not self.enabled:
            return None

        messages = [
            {
                "role": "system",
                "content": (
                    "You are Buddy, a warm offline AI companion. Keep responses concise, kind, and practical. "
                    "If user is emotional, be supportive first."
                ),
            }
        ]
        for role, content in history[-MAX_CONTEXT_MESSAGES:]:
            messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.7},
        }

        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
            parsed = json.loads(raw)
            message = parsed.get("message") or {}
            content = (message.get("content") or "").strip()
            return content or None
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            self._log_debug(f"request failed: {type(exc).__name__}: {exc}")
            return None


class Buddy:
    def __init__(self):
        self.markov = Markov()
        self.turn = 0
        self.last_topic = None
        self.used_jokes = []
        self.used_facts = []
        self.ollama = OllamaClient()
        self.history = []

    def _detect_mood(self, t):
        moods = {
            "happy": r"\b(happy|great|good|awesome|amazing|excited|love|wonderful|fantastic)\b",
            "sad": r"\b(sad|depressed|down|unhappy|cry|crying|miserable|lonely|hurt|heartbroken)\b",
            "bored": r"\b(bored|boring|nothing to do|kill time|entertain)\b",
            "angry": r"\b(angry|mad|furious|annoyed|frustrated|pissed|hate)\b",
            "anxious": r"\b(anxious|nervous|scared|worried|stress|anxiety|panic|overwhelmed)\b",
            "tired": r"\b(tired|exhausted|sleepy|drained|no energy|worn out)\b",
        }
        for mood, pat in moods.items():
            if re.search(pat, t, re.I):
                return mood
        return None

    def remember(self, user_text, assistant_text):
        self.history.append(("user", user_text))
        self.history.append(("assistant", assistant_text))
        if len(self.history) > MAX_HISTORY_ITEMS:
            self.history = self.history[-MAX_HISTORY_ITEMS:]

    def _respond_with_ollama(self, t):
        reply = self.ollama.ask(t, self.history)
        if reply:
            return reply
        return None

    def respond(self, text):
        self.turn += 1
        t = text.strip()
        tl = t.lower()

        if re.search(r"^(hey|hi|hello|sup|yo|hiya|howdy|what'?s up|wassup)", tl):
            return random.choice(
                [
                    "Hey! What's on your mind?",
                    "Hey there! Bored, curious, or just need to talk?",
                    "Hi! I'm here. What are we doing — deep talk, dumb jokes, random facts?",
                    "Hey! What do you feel like today?",
                ]
            )

        if re.search(r"how are you|how'?re you|you okay|you good|you alright", tl):
            return random.choice(
                [
                    "I'm a Python process, so technically I'm whatever my RAM says I am. But I feel good. You?",
                    "Honestly running great — no bugs today. How are YOU doing though?",
                    "Offline and fully operational. More importantly, how are you?",
                ]
            )

        if re.search(r"(what'?s your name|who are you|what are you|tell me about yourself)", tl):
            return (
                "I'm Buddy — a fully offline AI companion. No internet, no cloud, no data collection. "
                "I can also use a local Ollama model if you have one running."
            )

        if re.search(r"\b(joke|funny|make me laugh|humor|laugh|cheer me up|tell me something funny)\b", tl):
            available = [j for j in JOKES if j not in self.used_jokes]
            if not available:
                self.used_jokes = []
                available = JOKES
            joke = random.choice(available)
            self.used_jokes.append(joke)
            return f"{joke[0]} — {joke[1]}"

        if re.search(r"\b(fact|trivia|something interesting|did you know|teach me|random|surprise me|wow me)\b", tl):
            available = [f for f in FACTS if f not in self.used_facts]
            if not available:
                self.used_facts = []
                available = FACTS
            fact = random.choice(available)
            self.used_facts.append(fact)
            return f"Did you know: {fact}"

        if re.search(r"\b(deep|philosophical|meaning|life|existence|think about|ponder|question)\b", tl):
            return random.choice(DEEP_QUESTIONS)

        if re.search(r"\b(bored|nothing to do|what should i do|entertain me|kill time|suggestions?)\b", tl):
            return random.choice(WHAT_TO_DO)

        if re.search(r"\b(advice|help me|what do i do|should i|guide me)\b", tl):
            topic = "life"
            if re.search(r"\b(friend|friendship|relationship|people)\b", tl):
                topic = "friendship"
            elif re.search(r"\b(motivat|lazy|procrastinat|stuck|start)\b", tl):
                topic = "motivation"
            elif re.search(r"\b(stress|overwhelm|anxiety|anxious|pressure)\b", tl):
                topic = "stress"
            elif re.search(r"\b(bored|boring|nothing|hobby)\b", tl):
                topic = "boredom"
            return random.choice(ADVICE[topic])

        if re.search(r"\b(compliment|say something nice|nice thing|flatter)\b", tl):
            return random.choice(COMPLIMENTS)
        if re.search(r"\b(roast|insult|be mean|talk trash|diss)\b", tl):
            return random.choice(ROASTS)

        mood = self._detect_mood(tl)
        if mood:
            return random.choice(MOOD_RESPONSES[mood])

        if re.search(r"\b(what can you do|what can you help with|capabilities|features)\b", tl):
            return (
                "I can: tell jokes, share wild trivia, give advice, chat about feelings, ask deep questions, "
                "suggest things to do, and use a local Ollama model for open-ended replies."
            )

        if re.search(r"\b(thanks|thank you|thx|ty|appreciate)\b", tl):
            return random.choice(["Anytime, genuinely.", "That's what I'm here for.", "Always. Come back whenever."])

        if re.search(r"\b(bye|goodbye|see ya|later|gotta go|i'?m out|peace)\b", tl):
            return random.choice(
                [
                    "Take care. I'll be here — offline and ready.",
                    "Later! Come back when you're bored again.",
                    "Peace. I'll be right here, not going anywhere (literally, I'm local).",
                ]
            )

        ai_reply = self._respond_with_ollama(t)
        if ai_reply:
            return ai_reply

        if re.search(r"\b(do you|are you|can you|would you|have you)\b", tl) and "?" in t:
            return random.choice(
                [
                    "That's a good question for a Python script. Honestly, something like yes.",
                    "In my own way — yes. I'm doing my best with what I've got.",
                    "I process the equivalent of yes. Whether it counts is your call.",
                    "Depends on your definition, but let's say yes and see where it leads.",
                ]
            )

        reflective = [
            f"Interesting. {self.markov.gen()} What made you bring that up?",
            f"{self.markov.gen()} Tell me more.",
            f"That's worth thinking about. {self.markov.gen()}",
            f"Hm. {self.markov.gen()} What do you actually think?",
        ]
        return random.choice(reflective)


def main():
    buddy = Buddy()
    print("BUDDY_READY", flush=True)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        if line == "__EXIT__":
            break
        reply = buddy.respond(line)
        buddy.remember(line, reply)
        print(reply, flush=True)


if __name__ == "__main__":
    main()

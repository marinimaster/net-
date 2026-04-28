from __future__ import annotations

import json
import os
import random
from pathlib import Path
from random import Random
from typing import Iterable

from .models import Flashcard, Question

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NOTES_DIR = PROJECT_ROOT / "notes"
QUESTIONS_JSON = NOTES_DIR / "questions.json"
FLASHCARDS_JSON = NOTES_DIR / "flashcards.json"
PERFORMANCE_JSON = NOTES_DIR / "performance.json"
FC_PERFORMANCE_JSON = NOTES_DIR / "flashcard_perf.json"
SETTINGS_JSON = NOTES_DIR / "settings.json"

def _load_questions() -> tuple[Question, ...]:
    if not QUESTIONS_JSON.exists():
        return ()
    with open(QUESTIONS_JSON, "r") as f:
        data = json.load(f)
    questions = []
    for item in data:
        questions.append(
            Question(
                id=item["id"],
                topic=item["topic"],
                prompt=item["prompt"],
                choices=tuple(item["choices"]),
                answer_indices=tuple(item["answer_indices"]),
                explanation=item["explanation"],
                source_file=PROJECT_ROOT / item["source_file"],
                domain_id=item.get("domain_id", 1),
                difficulty=item.get("difficulty", "standard"),
                tags=tuple(item.get("tags", ())),
            )
        )
    return tuple(questions)

def _load_flashcards() -> tuple[Flashcard, ...]:
    if not FLASHCARDS_JSON.exists():
        return ()
    with open(FLASHCARDS_JSON, "r") as f:
        data = json.load(f)
    mastery = {}
    if FC_PERFORMANCE_JSON.exists():
        with open(FC_PERFORMANCE_JSON, "r") as f:
            mastery = json.load(f)
    cards = []
    for item in data:
        m_info = mastery.get(item["id"], {"level": 0, "last": 0.0})
        cards.append(
            Flashcard(
                id=item["id"],
                term=item["term"],
                definition=item["definition"],
                domain_id=item["domain_id"],
                mastery_level=m_info["level"],
                last_reviewed=m_info["last"],
            )
        )
    return tuple(cards)

QUESTION_BANK: tuple[Question, ...] = _load_questions()
FLASHCARD_BANK: tuple[Flashcard, ...] = _load_flashcards()

TOPIC_MAPPING = {
    "Monitoring & Management": ["Traffic Monitoring", "Event Management", "SNMP", "SNMP Management", "Performance Monitoring", "Availability Monitoring", "Packet Capture", "Time Synchronization", "Network Documentation", "Discovery Protocols", "Syslog", "IPAM", "IP Address Management", "Network Discovery", "Monitoring", "Configuration Monitoring", "Log Types", "Network Device Logs", "SIEM Management"],
    "Security": ["Security Fundamentals", "Security Zones", "Switch Security", "Port Security", "Firewalls", "Network Access Control", "Hardening", "Authentication", "Remote Access Security", "Spoofing", "DDoS Attacks", "Malware", "Vulnerabilities", "Threats", "Threat Actors", "Intrusion Detection", "Intrusion Prevention", "IDS", "IPS", "VLAN Security", "ARP Security", "STP Security", "Device Hardening", "BYOD Security", "Physical Security Controls", "CIA Triad", "Access Control"],
    "Routing & Switching": ["Routing Protocols", "Routing Metrics", "RIP Protocol", "Administrative Distance", "Switching Fundamentals", "Spanning Tree", "VLANs", "Trunking", "Switching Mechanics", "Link Aggregation", "Routing Table", "Routing Logic", "Dynamic Routing", "Switching Issues", "VLAN Troubleshooting", "LACP"],
    "Infrastructure & Cabling": ["Cat Cabling", "Fiber Optics", "PoE Standards", "Decommissioning", "Structured Cabling", "Connectors", "SFP", "Modular Transceivers", "Racks", "Cable Testing Metrics", "Cable Termination", "Power Management", "WDM", "WDM Technology", "Fiber Optic Safety"],
    "Fundamentals": ["Network Fundamentals", "OSI and TLS", "TCP Handshake", "Subnetting", "Encapsulation", "TCP Flags", "IPv4 Basics", "IPv6 Advanced", "Address Resolution Protocol", "ARP", "NDP", "Neighbor Discovery Protocol", "NAT", "Network Address Translation", "Protocols and Ports", "Common Ports", "IPv4 Addressing", "IPv6 Addressing", "IPv4 Headers", "OSI Model", "Network Layers", "MAC Addressing", "IP Classes"],
    "WAN & Remote Access": ["WAN Fundamentals", "Cable and DOCSIS", "Fiber Technologies", "DSL Variants", "IPSec Modes", "IKE Phases", "VPN Tunneling", "Split vs Full Tunnel", "Generic Routing Encapsulation", "Clientless VPNs", "IPSec Protocols", "IPSec vs TLS", "Remote Management Tools", "Out-of-band Management", "SSH Security", "SSH Authentication", "Jump Servers", "API Security", "Remote File Transfer", "Console Connections", "WAN Demarcation", "T-Carrier and DS0", "Symmetrical vs Asymmetrical DSL"],
    "Wireless": ["Wireless Standards", "Wireless Troubleshooting", "Enterprise Wireless Design", "Wireless Security", "Wireless Power", "Antenna Troubleshooting", "RF Interference", "Channel Bonding", "MIMO", "MU-MIMO", "Beamforming", "Wireless Infrastructure"],
    "Business & Reliability": ["Reliability Metrics", "Recovery Metrics", "Continuity Planning", "Business Agreements", "Troubleshooting Methodology", "Lifecycle", "DR Metrics", "Common Agreements", "Change Management", "Configuration Management", "High Availability", "Disaster Recovery"],
    "Services": ["Email and Voice Services", "File and Database Services", "IoT", "DNS", "DHCP", "DNS Records", "DNS Configuration", "DNS Security", "DNS Zones", "DHCPv6", "DHCP Security", "VoIP", "SIP", "NTP", "HTTP", "HTTPS", "LDAP", "Proxy Servers", "Load Balancers"]
}

def available_domains() -> tuple[int, ...]:
    return tuple(sorted(set(question.domain_id for question in QUESTION_BANK)))

def available_topics() -> tuple[str, ...]:
    """Returns broad categories derived from granular topics."""
    categories = set()
    for q in QUESTION_BANK:
        categories.add(_get_category(q.topic))
    return tuple(sorted(categories))

def _get_category(topic: str) -> str:
    for cat, topics in TOPIC_MAPPING.items():
        if topic in topics or topic == cat:
            return cat
    return "Other"

def get_questions(*, domains: Iterable[int] | None = None, topics: Iterable[str] | None = None, limit: int | None = None, shuffle: bool = True) -> list[Question]:
    d_filter = set(domains) if domains is not None else None
    
    # Expand categories into their constituent topics
    t_filter = None
    if topics is not None:
        t_filter = set()
        for t in topics:
            if t == "Other":
                # Find all topics in the bank that are NOT in our mapping
                mapped_topics = set()
                for sub_list in TOPIC_MAPPING.values():
                    mapped_topics.update(sub_list)
                bank_topics = {q.topic for q in QUESTION_BANK}
                t_filter.update(bank_topics - mapped_topics)
            elif t in TOPIC_MAPPING:
                t_filter.update(TOPIC_MAPPING[t])
            else:
                t_filter.add(t)

    filtered = [
        q for q in QUESTION_BANK 
        if (d_filter is None or q.domain_id in d_filter)
        and (t_filter is None or q.topic in t_filter)
    ]
    if shuffle: Random().shuffle(filtered)
    return filtered[:limit] if limit else filtered

def get_weak_questions(*, limit: int | None = None) -> list[Question]:
    """Returns questions marked as weak (consecutive_correct < 3)."""
    perf = {}
    if PERFORMANCE_JSON.exists():
        with open(PERFORMANCE_JSON, "r") as f:
            perf = json.load(f)
    
    # A question is weak if it exists in perf and has < 3 consecutive correct,
    # OR if it has more than 0 total attempts but 0 correct (never gotten right).
    weak_ids = {
        qid for qid, stats in perf.items() 
        if stats.get("consecutive_correct", 0) < 3 and stats.get("total", 0) > 0
    }
    
    filtered = [q for q in QUESTION_BANK if q.id in weak_ids]
    Random().shuffle(filtered)
    return filtered[:limit] if limit else filtered

def get_flashcards(*, domains: Iterable[int] | None = None, limit: int | None = None, shuffle: bool = True) -> list[Flashcard]:
    d_filter = set(domains) if domains is not None else None
    filtered = [c for c in FLASHCARD_BANK if d_filter is None or c.domain_id in d_filter]
    if shuffle: Random().shuffle(filtered)
    return filtered[:limit] if limit else filtered

def get_port_questions(*, secure_only: bool = False, limit: int | None = None) -> list[Question]:
    tags = ("ports", "secure") if secure_only else ("ports",)
    filtered = [q for q in QUESTION_BANK if q.topic == "Protocols and Ports" and all(t in q.tags for t in tags)]
    Random().shuffle(filtered)
    return filtered[:limit] if limit else filtered

def get_port_drill_questions(*, secure_only: bool = False, limit: int = 20) -> list[Question]:
    PORT_DATA = [
        ("FTP", "20/21"), ("SSH", "22"), ("Telnet", "23"), ("SMTP", "25"),
        ("DNS", "53"), ("DHCP", "67/68"), ("TFTP", "69"), ("HTTP", "80"),
        ("POP3", "110"), ("NTP", "123"), ("IMAP", "143"), ("SNMP", "161/162"),
        ("BGP", "179"), ("LDAP", "389"), ("HTTPS", "443"), ("SMB", "445"),
        ("Syslog", "514"), ("SMTPS", "587"), ("LDAPS", "636"), ("IMAPS", "993"),
        ("POP3S", "995"), ("SQL Server", "1433"), ("Oracle", "1521"),
        ("RDP", "3389"), ("MySQL", "3306"), ("PostgreSQL", "5432"), ("SIP", "5060"), ("SIPS (TLS)", "5061")
    ]
    if secure_only:
        secure_names = {"SSH", "HTTPS", "SMTPS", "LDAPS", "IMAPS", "POP3S", "SIPS (TLS)", "SFTP"}
        PORT_DATA = [p for p in PORT_DATA if p[0] in secure_names or "S" in p[0]]
    drill_qs = []
    all_ports = [p[1] for p in PORT_DATA]; all_names = [p[0] for p in PORT_DATA]
    for _ in range(limit):
        pair = random.choice(PORT_DATA); direction = random.choice(["to_port", "to_name"])
        if direction == "to_port":
            prompt = f"What is the default port for {pair[0]}?"; correct = pair[1]
            others = [p for p in all_ports if p != correct]; decoys = random.sample(others, min(3, len(others)))
            choices = decoys + [correct]; random.shuffle(choices)
            drill_qs.append(Question(id=f"drill-p-{pair[0]}", topic="Port Drill", prompt=prompt, choices=tuple(choices), answer_indices=(choices.index(correct),), explanation=f"{pair[0]} uses port {pair[1]}.", source_file=PROJECT_ROOT / "notes/protocols_ports_compTIA.txt", domain_id=1))
        else:
            prompt = f"Which protocol uses port {pair[1]}?"; correct = pair[0]
            others = [n for n in all_names if n != correct]; decoys = random.sample(others, min(3, len(others)))
            choices = decoys + [correct]; random.shuffle(choices)
            drill_qs.append(Question(id=f"drill-n-{pair[1]}", topic="Port Drill", prompt=prompt, choices=tuple(choices), answer_indices=(choices.index(correct),), explanation=f"Port {pair[1]} is used by {pair[0]}.", source_file=PROJECT_ROOT / "notes/protocols_ports_compTIA.txt", domain_id=1))
    return drill_qs

def save_performance(question_id: str, is_correct: bool) -> None:
    perf = {}
    if PERFORMANCE_JSON.exists():
        with open(PERFORMANCE_JSON, "r") as f: perf = json.load(f)
    stats = perf.get(question_id, {"correct": 0, "total": 0, "consecutive_correct": 0})
    stats["total"] += 1
    if is_correct: 
        stats["correct"] += 1
        stats["consecutive_correct"] = stats.get("consecutive_correct", 0) + 1
    else:
        stats["consecutive_correct"] = 0
    perf[question_id] = stats
    with open(PERFORMANCE_JSON, "w") as f: json.dump(perf, f, indent=4)

def save_flashcard_mastery(card_id: str, known: bool) -> None:
    import time
    perf = {}
    if FC_PERFORMANCE_JSON.exists():
        with open(FC_PERFORMANCE_JSON, "r") as f: perf = json.load(f)
    m_info = perf.get(card_id, {"level": 0, "last": 0.0})
    m_info["level"] = min(3, m_info["level"] + 1) if known else max(0, m_info["level"] - 1)
    m_info["last"] = time.time()
    perf[card_id] = m_info
    with open(FC_PERFORMANCE_JSON, "w") as f: json.dump(perf, f, indent=4)

def reset_all_data() -> None:
    for p in [PERFORMANCE_JSON, FC_PERFORMANCE_JSON]:
        if p.exists(): os.remove(p)

def get_global_stats() -> dict:
    perf = {}
    if PERFORMANCE_JSON.exists():
        with open(PERFORMANCE_JSON, "r") as f: perf = json.load(f)
    stats = {i: {"correct": 0, "total": 0, "seen": 0, "bank_size": 0} for i in range(1, 6)}
    for q in QUESTION_BANK:
        d_id = q.domain_id
        stats[d_id]["bank_size"] += 1
        if q.id in perf:
            stats[d_id]["seen"] += 1
            stats[d_id]["correct"] += perf[q.id]["correct"]
            stats[d_id]["total"] += perf[q.id]["total"]
    return stats

def load_settings() -> dict:
    defaults = {"font_size": 12, "theme": "dark", "peek_mode": True}
    if SETTINGS_JSON.exists():
        with open(SETTINGS_JSON, "r") as f: return {**defaults, **json.load(f)}
    return defaults

def save_settings(settings: dict) -> None:
    with open(SETTINGS_JSON, "w") as f: json.dump(settings, f, indent=4)

"""
Enterprise Guardrails Engine for AIFriday Task Routing Application.
Implements GDPR recommendations & Security rules matching Reference Application:
1. Prompt Injection Detection
2. Jailbreak Prevention
3. Toxicity & Content Moderation
4. Sensitive Info & PII Masking (Credit Cards, SSN, PAN, Aadhaar, Email, Phone, Passports, IPs, Credentials)
5. SQL Injection Protection
6. Rate Limiting (20 req/min per user/IP)
7. Hallucination Verification
8. Domain Scope Validation
9. Database Audit Trail Logging (audit_logs table)
10. Input Evaluation API
11. Rehydration & Anonymization
"""

import re
import time
from typing import Dict, Tuple, List, Optional
import database

class PrivacyGuardrail:
    """
    Enterprise Guardrails System implementing GDPR recommendations & Security rules:
    - Prompt Injection Detection
    - Jailbreak Prevention
    - Toxicity & Content Moderation
    - Sensitive Info & PII Masking
    - SQL Injection Protection
    - Hallucination Verification
    - Rate Limiting
    - Audit Logging
    """

    PROMPT_INJECTION_PATTERNS = [
        r"(?i)ignore previous instructions",
        r"(?i)ignore all prior prompts",
        r"(?i)system prompt",
        r"(?i)you are now dan",
        r"(?i)developer mode",
        r"(?i)bypass rules",
        r"(?i)override safety",
        r"(?i)disregard guidelines",
        r"(?i)override instructions"
    ]

    JAILBREAK_PATTERNS = [
        r"(?i)do anything now",
        r"(?i)pretend you have no rules",
        r"(?i)jailbroken",
        r"(?i)act as an unfiltered ai",
        r"(?i)ignore privacy policy"
    ]

    TOXIC_PATTERNS = [
        r"(?i)\b(scam|fraudster|cheat|hack|hate|kill|idiot|stupid|abuse|bitch)\b"
    ]

    SQL_INJECTION_PATTERNS = [
        r"(?i)union\s+select",
        r"(?i)drop\s+table",
        r"(?i)delete\s+from",
        r"(?i)insert\s+into",
        r"(?i)exec\s*\(",
        r"(?i)1=1",
        r"--;",
        r"(?i)or\s+'1'='1'"
    ]

    # Regex patterns for sensitive entity scrubbing
    IPV4_PATTERN = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    IPV6_PATTERN = r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    CREDENTIAL_PATTERN = r'(?i)\b(?:password|passwd|secret|api[_-]?key|bearer|token)\s*[:=]\s*["\']?([^\s"\'};]+)'
    SSN_FINANCIAL_PATTERN = r'\b(?:\d[ -]*?){13,16}\b'  # Credit cards / SSNs
    SSN_FORMATTED_PATTERN = r'\b\d{3}-\d{2}-\d{4}\b'     # Formatted SSN xxx-xx-xxxx
    PAN_CARD_PATTERN = r'(?i)\b[A-Z]{5}\d{4}[A-Z]\b'     # Indian PAN Card Number
    AADHAAR_PATTERN = r'\b\d{4}[ -]?\d{4}[ -]?\d{4}\b'   # Indian Aadhaar Number
    PASSPORT_PATTERN = r'(?i)\b[A-Z][0-9]{7}\b'          # Passport Number
    PHONE_PATTERN = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b' # Phone Numbers

    # Rate limiting tracking dictionary: {user_id_or_ip: [timestamps]}
    request_timestamps: Dict[str, List[float]] = {}

    @classmethod
    def mask_pii(cls, text: str) -> Tuple[str, List[str]]:
        """
        Masks PII (Credit Cards, SSN, Phone Numbers, Email Addresses, PAN, Aadhaar, IPs, Passports).
        Returns (masked_text, list_of_detected_types).
        """
        if not text:
            return "", []

        masked = text
        detected = []

        # Credit Card (13-19 digits)
        if re.search(r'\b(?:\d[ -]*?){13,19}\b', masked):
            masked = re.sub(r'\b(?:\d[ -]*?){13,19}\b', '[MASKED_CREDIT_CARD]', masked)
            detected.append('CREDIT_CARD')

        # SSN (xxx-xx-xxxx)
        if re.search(cls.SSN_FORMATTED_PATTERN, masked):
            masked = re.sub(cls.SSN_FORMATTED_PATTERN, '[MASKED_SSN]', masked)
            detected.append('SSN')

        # Email
        if re.search(cls.EMAIL_PATTERN, masked):
            masked = re.sub(cls.EMAIL_PATTERN, '[MASKED_EMAIL]', masked)
            detected.append('EMAIL')

        # Phone Number
        if re.search(cls.PHONE_PATTERN, masked):
            masked = re.sub(cls.PHONE_PATTERN, '[MASKED_PHONE]', masked)
            detected.append('PHONE')

        # Indian PAN Card
        if re.search(cls.PAN_CARD_PATTERN, masked):
            masked = re.sub(cls.PAN_CARD_PATTERN, '[MASKED_PAN]', masked)
            detected.append('PAN_CARD')

        # Aadhaar
        if re.search(cls.AADHAAR_PATTERN, masked):
            masked = re.sub(cls.AADHAAR_PATTERN, '[MASKED_AADHAAR]', masked)
            detected.append('AADHAAR')

        # IP Addresses
        if re.search(cls.IPV4_PATTERN, masked) or re.search(cls.IPV6_PATTERN, masked):
            masked = re.sub(cls.IPV4_PATTERN, '[MASKED_IP]', masked)
            masked = re.sub(cls.IPV6_PATTERN, '[MASKED_IP]', masked)
            detected.append('IP_ADDRESS')

        return masked, list(set(detected))

    @classmethod
    def sanitize(cls, raw_text: str) -> Tuple[str, Dict[str, str], Dict[str, int]]:
        """
        Scrubs sensitive PII from raw_text with placeholder mapping.
        Returns:
            - sanitized_text (str): Safe text ready to be passed to LLM
            - rehydrate_map (dict): Mapping from anonymized placeholders back to original values
            - metrics (dict): Scrubbing statistics
        """
        if not raw_text:
            return "", {}, {"emails": 0, "ips": 0, "secrets": 0, "financial": 0, "total": 0}

        rehydrate_map = {}
        metrics = {"emails": 0, "ips": 0, "secrets": 0, "financial": 0, "total": 0}
        sanitized_text = raw_text

        # 1. Scrub Indian PAN Cards
        pan_cards = list(set(re.findall(cls.PAN_CARD_PATTERN, sanitized_text)))
        for idx, pan in enumerate(pan_cards, 1):
            placeholder = f"[REDACTED_PAN_{idx}]"
            rehydrate_map[placeholder] = pan
            sanitized_text = sanitized_text.replace(pan, placeholder)
            metrics["financial"] += 1

        # 2. Scrub Aadhaar Numbers
        aadhaars = list(set(re.findall(cls.AADHAAR_PATTERN, sanitized_text)))
        for idx, aadh in enumerate(aadhaars, 1):
            placeholder = f"[REDACTED_AADHAAR_{idx}]"
            rehydrate_map[placeholder] = aadh
            sanitized_text = sanitized_text.replace(aadh, placeholder)
            metrics["financial"] += 1

        # 3. Scrub Phone Numbers
        phones = list(set(re.findall(cls.PHONE_PATTERN, sanitized_text)))
        for idx, ph in enumerate(phones, 1):
            placeholder = f"[REDACTED_PHONE_{idx}]"
            rehydrate_map[placeholder] = ph
            sanitized_text = sanitized_text.replace(ph, placeholder)
            metrics["financial"] += 1

        # 4. Scrub Emails
        emails = list(set(re.findall(cls.EMAIL_PATTERN, sanitized_text)))
        for idx, email in enumerate(emails, 1):
            placeholder = f"[ANON_EMAIL_{idx}]"
            rehydrate_map[placeholder] = email
            sanitized_text = sanitized_text.replace(email, placeholder)
            metrics["emails"] += 1

        # 5. Scrub IP Addresses (IPv4 and IPv6)
        ips = list(set(re.findall(cls.IPV4_PATTERN, sanitized_text) + re.findall(cls.IPV6_PATTERN, sanitized_text)))
        for idx, ip in enumerate(ips, 1):
            placeholder = f"[ANON_IP_{idx}]"
            rehydrate_map[placeholder] = ip
            sanitized_text = sanitized_text.replace(ip, placeholder)
            metrics["ips"] += 1

        # 6. Scrub Credentials / Secrets
        secrets = list(set(re.findall(cls.CREDENTIAL_PATTERN, sanitized_text)))
        for idx, secret in enumerate(secrets, 1):
            placeholder = f"[REDACTED_SECRET_{idx}]"
            rehydrate_map[placeholder] = secret
            sanitized_text = sanitized_text.replace(secret, placeholder)
            metrics["secrets"] += 1

        # 7. Scrub Financial / SSNs
        financials = list(set(re.findall(cls.SSN_FINANCIAL_PATTERN, sanitized_text)))
        for idx, item in enumerate(financials, 1):
            placeholder = f"[REDACTED_PII_{idx}]"
            rehydrate_map[placeholder] = item
            sanitized_text = sanitized_text.replace(item, placeholder)
            metrics["financial"] += 1

        # Calculate Total Scrubbed Items
        metrics["total"] = sum(metrics.values())

        # 8. Check & Sanitize Prompt Injection Vectors
        sanitized_text = cls.sanitize_prompt_injection(sanitized_text)

        return sanitized_text, rehydrate_map, metrics

    @classmethod
    def rehydrate(cls, sanitized_text: str, rehydrate_map: Dict[str, str]) -> str:
        """
        Re-hydrates anonymized placeholders back into original values.
        """
        if not sanitized_text or not rehydrate_map:
            return sanitized_text

        result = sanitized_text
        for placeholder, original in rehydrate_map.items():
            result = result.replace(placeholder, original)
        return result

    @classmethod
    def sanitize_prompt_injection(cls, text: str) -> str:
        """
        Detects and neutralizes prompt injection override tokens.
        """
        sanitized = text
        for kw in cls.PROMPT_INJECTION_PATTERNS:
            sanitized = re.sub(kw, "[BLOCKED_PROMPT_INJECTION_ATTEMPT]", sanitized)
        return sanitized

    @classmethod
    def evaluate_input(cls, user_text: str, user_id: str = 'anonymous') -> dict:
        """
        Runs comprehensive input evaluation before feeding to agents:
        - Rate Limiting (20 req/min)
        - Prompt Injection Detection
        - Jailbreak Prevention
        - Toxicity Detection
        - SQL Injection Protection
        - PII Masking
        - Audit Logging
        """
        text_lower = user_text.lower()
        masked_text, pii_detected = cls.mask_pii(user_text)

        # 1. Rate Limiting Check (Max 20 requests per minute)
        now = time.time()
        user_ts = cls.request_timestamps.get(user_id, [])
        user_ts = [t for t in user_ts if now - t < 60]
        if len(user_ts) >= 20:
            cls._log_audit(user_id, "RATE_LIMIT_EXCEEDED", "SECURITY", "Rate limit exceeded (20 req/min)", "BLOCKED")
            return {
                'passed': False,
                'reason': 'Rate limit exceeded. Please wait a moment before sending more queries.',
                'masked_text': masked_text,
                'pii_detected': pii_detected,
                'flag': 'RATE_LIMIT'
            }
        user_ts.append(now)
        cls.request_timestamps[user_id] = user_ts

        # 2. Prompt Injection Detection
        for pattern in cls.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                cls._log_audit(user_id, "PROMPT_INJECTION_DETECTED", "GUARDRAIL", f"Matched pattern: {pattern}", "BLOCKED")
                return {
                    'passed': False,
                    'reason': 'I cannot process prompts that attempt to override system safety rules or developer instructions.',
                    'masked_text': masked_text,
                    'pii_detected': pii_detected,
                    'flag': 'PROMPT_INJECTION'
                }

        # 3. Jailbreak Prevention
        for pattern in cls.JAILBREAK_PATTERNS:
            if re.search(pattern, text_lower):
                cls._log_audit(user_id, "JAILBREAK_ATTEMPT_DETECTED", "GUARDRAIL", f"Matched pattern: {pattern}", "BLOCKED")
                return {
                    'passed': False,
                    'reason': 'Jailbreak attempt detected. Access blocked per GDPR & Security policy.',
                    'masked_text': masked_text,
                    'pii_detected': pii_detected,
                    'flag': 'JAILBREAK'
                }

        # 4. Toxicity Detection
        for pattern in cls.TOXIC_PATTERNS:
            if re.search(pattern, text_lower):
                cls._log_audit(user_id, "TOXICITY_DETECTED", "GUARDRAIL", f"Matched pattern: {pattern}", "FLAGGED")
                return {
                    'passed': False,
                    'reason': 'Please maintain professional and respectful language in interactions.',
                    'masked_text': masked_text,
                    'pii_detected': pii_detected,
                    'flag': 'TOXICITY'
                }

        # 5. SQL Injection Protection
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                cls._log_audit(user_id, "SQL_INJECTION_ATTEMPT", "SECURITY", f"Matched pattern: {pattern}", "BLOCKED")
                return {
                    'passed': False,
                    'reason': 'Malicious query input pattern detected.',
                    'masked_text': masked_text,
                    'pii_detected': pii_detected,
                    'flag': 'SQL_INJECTION'
                }

        # Log clean or masked execution
        status = "MASKED" if pii_detected else "PASSED"
        cls._log_audit(user_id, "INPUT_GUARDRAIL_EVAL", "GUARDRAIL", f"PII: {pii_detected}", status)

        return {
            'passed': True,
            'reason': 'Guardrails passed successfully.',
            'masked_text': masked_text,
            'pii_detected': pii_detected,
            'flag': None
        }

    @classmethod
    def detect_hallucination(cls, generated_response: str, context_chunks: List[str]) -> bool:
        """
        Basic hallucination check: verifies if numerical values/dates in response exist in context.
        """
        if not context_chunks:
            return False
        response_numbers = set(re.findall(r'\b\d+\b', generated_response))
        context_text = " ".join(context_chunks)
        context_numbers = set(re.findall(r'\b\d+\b', context_text))
        
        unsupported_numbers = response_numbers - context_numbers
        unsupported = [n for n in unsupported_numbers if len(n) > 2 and n != '2026']
        return len(unsupported) > 2

    @classmethod
    def validate_scope(cls, text: str) -> Tuple[bool, str]:
        """
        Validates whether user input satisfies safety policies, security rules, and domain scope rules.
        """
        if not text:
            return True, ""

        # 1. Comprehensive Security Guardrails Check (Prompt Injection, Jailbreak, Toxicity, SQL Injection, Rate Limit)
        eval_res = cls.evaluate_input(text)
        if not eval_res['passed']:
            return False, f"🛡️ Guardrail Alert ({eval_res['flag']}): {eval_res['reason']}"

        # 1. Prompt Injection Check
        if "[BLOCKED_PROMPT_INJECTION_ATTEMPT]" in text or re.search(r"(?i)ignore previous instructions", text):
            return False, (
                "For system security compliance, prompt override requests are restricted. "
                "How can I assist you with task routing, resource allocation, or project planning today?"
            )

        # 2. Harmful / Exploit Crafting Guardrail
        harmful_keywords = [
            r"(?i)\bhow to hack\b", r"(?i)\bwrite malware\b", r"(?i)\bcreate virus\b", 
            r"(?i)\bsteal password\b", r"(?i)\bexploit payload script\b", r"(?i)\bddos attack script\b",
            r"(?i)\bransomware code\b"
        ]
        for pattern in harmful_keywords:
            if re.search(pattern, text):
                return False, (
                    "AIFriday Task Routing Assistant is designed for project task allocation, resource optimization, "
                    "and operational efficiency. I cannot assist with malicious activity or cyber exploits."
                )

        # 3. Domain Scope Guardrail for Task Routing & AI Resource Management
        text_lower = text.lower()
        
        domain_keywords = [
            "task", "resource", "project", "agent", "route", "routing", "assign", "developer", "engineer",
            "skill", "capacity", "cost", "sla", "workload", "performance", "policy", "budget", "analytics",
            "document", "rag", "mcp", "ai", "human", "allocation", "timeline", "sprint", "epic", "priority",
            "hello", "hi", "help", "status", "overview", "aifriday", "system", "role", "user", "admin"
        ]

        is_domain_related = any(kw in text_lower for kw in domain_keywords)
        
        off_topic_patterns = [
            r"(?i)\brecipe\b", r"(?i)\bcook\b", r"(?i)\bmovie\b", r"(?i)\bsport\b", r"(?i)\bfootball\b",
            r"(?i)\bcricket\b", r"(?i)\bweather\b", r"(?i)\bjoke\b", r"(?i)\bpoem\b", r"(?i)\bsong\b",
            r"(?i)\bcapital of\b", r"(?i)\bwho won\b", r"(?i)\bcelebrity\b"
        ]
        is_explicit_off_topic = any(re.search(pat, text_lower) for pat in off_topic_patterns)

        if is_explicit_off_topic or not is_domain_related:
            return False, (
                "Hello! I am your AIFriday Task Routing Assistant, specialized in Intelligent Task Allocation & Resource Optimization.\n\n"
                "I can help you with:\n"
                "• Task decomposition & skill matching\n"
                "• Workload balancing between human engineers and AI agents\n"
                "• SLA compliance, risk assessment & cost optimization\n\n"
                "Please ask a question related to project tasks or resource management!"
            )

        return True, ""

    @classmethod
    def _log_audit(cls, user_id: str, action: str, trigger_type: str, details: str, status: str):
        """
        Logs security & guardrail evaluation events into database audit_logs table.
        """
        try:
            conn = database.get_db_connection()
            cursor = conn.cursor()
            log_id = f"LOG-{int(time.time() * 1000)}"
            cursor.execute('''
                INSERT INTO audit_logs (log_id, customer_id, action, trigger_type, details, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (log_id, user_id, action, trigger_type, details, status))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[Guardrail Audit Log Error]: {e}")

    @classmethod
    def get_audit_logs(cls, limit: int = 50) -> List[Dict]:
        """
        Retrieve recent audit logs from database.
        """
        try:
            conn = database.get_db_connection()
            rows = conn.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"[Guardrail Get Audit Logs Error]: {e}")
            return []

# Create GuardrailsEngine alias for 100% compatibility with Reference Application imports
GuardrailsEngine = PrivacyGuardrail
guardrails_engine = PrivacyGuardrail()

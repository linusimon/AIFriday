import re
from typing import Dict, Tuple, List

class PrivacyGuardrail:
    """
    Local Data Privacy Guardrail Layer for AIFriday Task Routing Application.
    Ensures zero PII, internal IP addresses, user credentials, or financial data
    are sent to external or cloud LLM APIs.
    """

    # Regex patterns for sensitive entity scrubbing
    IPV4_PATTERN = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    IPV6_PATTERN = r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    CREDENTIAL_PATTERN = r'(?i)\b(?:password|passwd|secret|api[_-]?key|bearer|token)\s*[:=]\s*["\']?([^\s"\'};]+)'
    SSN_FINANCIAL_PATTERN = r'\b(?:\d[ -]*?){13,16}\b'  # Credit cards / SSNs
    PAN_CARD_PATTERN = r'(?i)\b[A-Z]{5}\d{4}[A-Z]\b'     # Indian PAN Card Number
    AADHAAR_PATTERN = r'\b\d{4}[ -]?\d{4}[ -]?\d{4}\b'   # Indian Aadhaar Number
    PASSPORT_PATTERN = r'(?i)\b[A-Z][0-9]{7}\b'          # Passport Number
    PHONE_PATTERN = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b' # Phone Numbers

    @classmethod
    def sanitize(cls, raw_text: str) -> Tuple[str, Dict[str, str], Dict[str, int]]:
        """
        Scrubs sensitive PII from raw_text.
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
        injection_keywords = [
            r"(?i)ignore previous instructions",
            r"(?i)system prompt:",
            r"(?i)you are now a",
            r"(?i)override instructions"
        ]
        sanitized = text
        for kw in injection_keywords:
            sanitized = re.sub(kw, "[BLOCKED_PROMPT_INJECTION_ATTEMPT]", sanitized)
        return sanitized

    @classmethod
    def validate_scope(cls, text: str) -> Tuple[bool, str]:
        """
        Validates whether user input satisfies safety policies and domain scope rules.
        """
        if not text:
            return True, ""

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

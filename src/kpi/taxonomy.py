"""Domain taxonomy for KPI classification."""

DOMAIN_TREE: dict[str, dict] = {
    "marketing": {
        "label": "Marketing",
        "subdomains": ["acquisition", "retention", "brand", "content", "seo", "paid"],
    },
    "product": {
        "label": "Product",
        "subdomains": ["engagement", "activation", "adoption", "nps", "onboarding"],
    },
    "finance": {
        "label": "Finance",
        "subdomains": ["revenue", "cost", "profitability", "cashflow", "unit_economics"],
    },
    "engineering": {
        "label": "Engineering",
        "subdomains": ["reliability", "performance", "velocity", "quality", "dora"],
    },
    "sales": {
        "label": "Sales",
        "subdomains": ["pipeline", "conversion", "retention", "expansion", "activity"],
    },
    "support": {
        "label": "Support",
        "subdomains": ["volume", "quality", "efficiency", "satisfaction"],
    },
    "saas": {
        "label": "SaaS",
        "subdomains": ["growth", "retention", "monetization", "efficiency"],
    },
    "ecommerce": {
        "label": "E-Commerce",
        "subdomains": ["traffic", "conversion", "aov", "fulfillment", "returns"],
    },
    "gaming": {
        "label": "Gaming",
        "subdomains": ["engagement", "monetization", "retention", "virality", "performance"],
    },
}

ALL_DOMAINS = set(DOMAIN_TREE.keys())
ALL_SUBDOMAINS = {sub for d in DOMAIN_TREE.values() for sub in d["subdomains"]}


def get_domain_label(domain: str) -> str:
    return DOMAIN_TREE.get(domain, {}).get("label", domain)


def list_domains() -> list[dict[str, str | list[str]]]:
    return [
        {"key": k, "label": v["label"], "subdomains": v["subdomains"]}
        for k, v in DOMAIN_TREE.items()
    ]

# Phase 2 Implementation Plan: Data-Vendor Opportunity Discovery System

**Version**: 2.0
**Date**: November 18, 2024
**Build Upon**: Phase 1 (7-Agent GenAI Opportunity System)
**New Focus**: Discovering data-vendor business opportunities for 8-digit NAICS segments

---

## 🎯 OBJECTIVES

### Primary Goal
Build a system that analyzes 8-digit NAICS segments to discover opportunities for creating data-vendor businesses by:
1. Identifying core operational data needs of businesses in each segment
2. Mapping existing data vendor landscape (incumbents, pricing, gaps)
3. Assessing data source accessibility and acquisition costs
4. Sizing the market opportunity
5. Evaluating defensibility and competitive moat potential

### Success Criteria
- Analyze each 8-digit NAICS segment independently
- Discover operational data needs through extensive web research
- Identify white-space, disruption, and aggregation opportunities
- Provide actionable scoring based on multiple factors (market size, moat, accessibility, competition)
- Generate comprehensive data-vendor opportunity reports

---

## 🏗️ SYSTEM ARCHITECTURE

### High-Level Design

```
User Input (8-digit NAICS Code + Description)
    ↓
DataVendorAnalyzer.analyze()
    ↓
[LangGraph StateGraph Workflow - PHASE 2]
    ↓
┌─────────────────────────────────────────────────────────────┐
│                   DISCOVERY PHASE                           │
├─────────────────────────────────────────────────────────────┤
│  Data Needs Researcher                                      │
│    → Discover what data businesses need                     │
│    → Search forums, job postings, vendor reviews            │
│    → Identify pain points with current data access          │
│                                                             │
│  Vendor Intelligence Agent                                  │
│    → Map existing data vendor landscape                     │
│    → Extract pricing, features, market share                │
│    → Identify customer complaints and gaps                  │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│                   ANALYSIS PHASE                            │
├─────────────────────────────────────────────────────────────┤
│  Data Source Mapper                                         │
│    → Identify data origins (govt, companies, users)         │
│    → Assess accessibility (public API, scraping, license)   │
│    → Estimate acquisition costs                             │
│                                                             │
│  Data Market Sizer                                          │
│    → Calculate TAM/SAM/SOM for data products                │
│    → Estimate ARPU for data subscriptions                   │
│    → Model unit economics (margins, CAC, LTV)               │
│                                                             │
│  Data Moat Analyzer                                         │
│    → Assess exclusivity potential                           │
│    → Evaluate network effects                               │
│    → Analyze switching costs and barriers                   │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│                   SYNTHESIS PHASE                           │
├─────────────────────────────────────────────────────────────┤
│  Data Product Designer                                      │
│    → Design product format (API, dashboard, reports)        │
│    → Define pricing model (subscription, per-query)         │
│    → Specify integration requirements                       │
│                                                             │
│  Data Opportunity Synthesizer                               │
│    → Rank opportunities by composite score                  │
│    → Generate comprehensive report                          │
│    → Provide go-to-market recommendations                   │
└─────────────────────────────────────────────────────────────┘
    ↓
Data Vendor Opportunity Report (Markdown)
    ↓
DatabaseManager (Results Storage)
AuditDatabase (Complete Operation Tracking)
```

---

## 📋 NEW AGENTS SPECIFICATION

### 1. Data Needs Researcher (`src/data_needs_researcher.py`)

**Purpose**: Discover what data businesses in the segment need to operate effectively

**Key Methods**:
```python
def discover_data_needs(
    naics_8_digit: str,
    segment_description: str
) -> Dict[str, Any]:
    """
    Discover operational data needs through web research

    Returns:
    {
        'data_needs': [
            {
                'data_type': 'Worker compensation insurance rates by state',
                'business_function': 'Risk management / Insurance pricing',
                'importance': 'critical',  # critical, high, medium, low
                'frequency_mentioned': 12,  # times found in research
                'current_pain_points': [
                    'Data is expensive ($5K/year from NCCI)',
                    'Updates are quarterly, need monthly',
                    'Missing data for emerging job classifications'
                ],
                'use_cases': [
                    'Insurance policy pricing',
                    'Risk assessment',
                    'Competitive benchmarking'
                ],
                'decision_impact': 'High - directly affects profitability',
                'sources_found': ['reddit.com/r/insurance', 'insurance-forums.net']
            }
        ],
        'segment_characteristics': {
            'typical_company_size': '10-50 employees',
            'data_sophistication': 'medium',  # low, medium, high
            'budget_for_data': '$1K-10K/year estimated'
        },
        'confidence': 0.75
    }
    """
```

**Search Strategies**:
```python
SEARCH_QUERIES = [
    # Direct data need queries
    'site:reddit.com "{segment}" "what data do you need"',
    'site:reddit.com "{segment}" "where do you get data"',
    'site:reddit.com "{segment}" "data source recommendations"',

    # Job posting analysis (reveals data needs)
    'site:linkedin.com "{segment}" "data analyst" job description',
    'site:indeed.com "{segment}" "data" required skills',

    # Vendor review analysis
    'site:g2.com "{segment}" data vendor reviews',
    'site:capterra.com "{segment}" data software',

    # Industry forum research
    '{segment} industry forum "data challenges"',
    '{segment} "industry report" data requirements',

    # Regulatory/compliance data needs
    '{segment} compliance data requirements',
    '{segment} regulatory reporting data',

    # Operational queries
    '{segment} "operational data" needs',
    '{segment} "business intelligence" requirements',
    '{segment} "what metrics do you track"',

    # Pain point queries
    '{segment} "data is too expensive"',
    '{segment} "can\'t find data for"',
    '{segment} "data quality issues"'
]
```

**LLM Analysis Prompt**:
```
Analyze these web search results about data needs in the {segment} industry.

SEARCH RESULTS:
{search_results}

Extract:
1. Specific data types mentioned (be very specific, not generic)
2. How the data is used (business function, decisions made)
3. Pain points with current data access
4. Frequency of mentions (how often this data type appears)
5. Importance level (critical, high, medium, low)

Return ONLY valid JSON matching this structure:
{
  "data_needs": [
    {
      "data_type": "<specific data type>",
      "business_function": "<how it's used>",
      "importance": "<critical|high|medium|low>",
      "frequency_mentioned": <count>,
      "current_pain_points": ["<specific pain>"],
      "use_cases": ["<specific use case>"],
      "decision_impact": "<description>"
    }
  ]
}

Be SPECIFIC.
Bad: "market data"
Good: "daily commodity spot prices for corn, soybeans, and wheat"

Bad: "customer data"
Good: "retail foot traffic counts by hour and day of week"
```

---

### 2. Vendor Intelligence Agent (`src/vendor_intelligence_agent.py`)

**Purpose**: Map existing data vendor landscape and identify opportunities

**Key Methods**:
```python
def analyze_vendor_landscape(
    data_needs: List[Dict],
    naics_8_digit: str
) -> Dict[str, Any]:
    """
    Map data vendor landscape for each identified data need

    Returns:
    {
        'vendors_by_data_type': {
            'Worker compensation insurance rates': {
                'vendors': [
                    {
                        'name': 'NCCI (National Council on Compensation Insurance)',
                        'pricing': '$5,000-$15,000/year (estimated)',
                        'coverage': 'All US states except monopolistic states',
                        'update_frequency': 'Quarterly',
                        'data_format': 'PDF reports, Excel downloads',
                        'market_position': 'Dominant incumbent',
                        'customer_complaints': [
                            'Too expensive for small agencies',
                            'Data format is not API-friendly',
                            'Quarterly updates too slow'
                        ],
                        'customer_satisfaction': '3.5/5 (from 23 reviews)',
                        'strengths': ['Comprehensive', 'Authoritative', 'Trusted'],
                        'weaknesses': ['Expensive', 'Slow updates', 'Poor UX']
                    }
                ],
                'market_assessment': {
                    'competition_level': 'monopolistic',  # monopolistic, oligopoly, competitive, fragmented
                    'pricing_pressure': 'high',  # high, medium, low
                    'opportunity_type': 'disruption',  # white-space, disruption, aggregation
                    'barriers_to_entry': 'medium',  # high, medium, low
                    'gaps': [
                        'No real-time API access',
                        'Missing emerging job classifications',
                        'No state-level granularity for some categories'
                    ]
                }
            }
        },
        'overall_landscape': {
            'total_vendors_found': 5,
            'dominant_players': ['NCCI', 'ISO'],
            'market_concentration': 'high',  # high, medium, low
            'avg_customer_satisfaction': 3.2,
            'common_complaints': ['Expensive', 'Poor data formats', 'Slow updates']
        }
    }
    """
```

**Search Strategies**:
```python
VENDOR_SEARCH_QUERIES = [
    # Direct vendor discovery
    '"{data_type}" data vendor',
    '"{data_type}" data provider',
    'buy "{data_type}" data',
    'subscribe "{data_type}" API',

    # Pricing research
    '"{vendor_name}" pricing',
    '"{vendor_name}" cost',
    '"{data_type}" data cost',

    # Review research
    'site:g2.com "{vendor_name}"',
    'site:capterra.com "{vendor_name}"',
    'site:trustradius.com "{vendor_name}"',
    'site:reddit.com "{vendor_name}" review',

    # Alternative/competitor research
    '"{vendor_name}" alternative',
    '"{vendor_name}" competitor',
    'best "{data_type}" data providers',

    # Feature/capability research
    '"{vendor_name}" API documentation',
    '"{vendor_name}" data coverage',
    '"{vendor_name}" update frequency'
]
```

---

### 3. Data Source Mapper (`src/data_source_mapper.py`)

**Purpose**: Identify where data originates and assess acquisition feasibility

**Key Methods**:
```python
def map_data_sources(
    data_type: str,
    naics_8_digit: str
) -> Dict[str, Any]:
    """
    Identify data sources and acquisition strategy

    Returns:
    {
        'data_type': 'Worker compensation insurance rates',
        'primary_sources': [
            {
                'source_name': 'State workers compensation boards',
                'source_type': 'government',  # government, corporate, user-generated, sensor, transaction
                'accessibility': 'public',  # public, licensable, proprietary, restricted
                'access_method': 'web_scraping',  # api, web_scraping, manual_collection, partnership, purchase
                'cost_estimate': '$0 (public data)',
                'update_frequency': 'varies by state (monthly to annually)',
                'coverage': '50 states',
                'data_quality': 'authoritative',  # authoritative, reliable, moderate, uncertain
                'legal_restrictions': 'None (public data)',
                'collection_complexity': 'medium'  # low, medium, high
            },
            {
                'source_name': 'Insurance carrier rate filings',
                'source_type': 'corporate',
                'accessibility': 'public',
                'access_method': 'web_scraping',
                'cost_estimate': '$0 (public filings)',
                'update_frequency': 'as filed (varies)',
                'coverage': 'major carriers only',
                'data_quality': 'reliable',
                'legal_restrictions': 'None (public filings)',
                'collection_complexity': 'high (50 different state formats)'
            }
        ],
        'acquisition_strategy': {
            'recommended_approach': 'Build scrapers for state boards + rate filings',
            'estimated_setup_cost': '$25,000 (engineering)',
            'ongoing_cost': '$2,000/month (maintenance + cloud)',
            'time_to_first_data': '3 months',
            'exclusivity_potential': 'low',  # high, medium, low
            'scalability': 'high',  # high, medium, low
            'data_moat': 'Collection infrastructure + normalization algorithms'
        },
        'alternative_sources': [
            {
                'source_name': 'NCCI data licensing',
                'cost_estimate': '$50,000-$100,000/year',
                'pros': ['Comprehensive', 'Already normalized'],
                'cons': ['Expensive', 'Not exclusive', 'Licensing restrictions']
            }
        ]
    }
    """
```

**Search Strategies**:
```python
DATA_SOURCE_QUERIES = [
    # Government sources
    '"{data_type}" government database',
    '"{data_type}" public data',
    '"{data_type}" open data portal',
    '"{data_type}" FOIA',

    # API discovery
    '"{data_type}" API',
    '"{data_type}" REST API documentation',

    # Scraping feasibility
    '"{data_type}" official website',
    'where to find "{data_type}"',

    # Industry sources
    '{industry} association "{data_type}"',
    '{industry} trade group data',

    # Academic/research sources
    '"{data_type}" research dataset',
    '"{data_type}" academic database'
]
```

---

### 4. Data Market Sizer (`src/data_market_sizer.py`)

**Purpose**: Calculate market size and unit economics for data products

**Key Methods**:
```python
def size_data_market(
    naics_8_digit: str,
    segment_description: str,
    data_need: Dict,
    vendor_landscape: Dict,
    research_data: Dict
) -> Dict[str, Any]:
    """
    Size the market for a specific data product

    Returns:
    {
        'data_type': 'Worker compensation insurance rates',
        'market_sizing': {
            'total_establishments': 5234,  # from Census
            'addressable_establishments': 2000,  # those that need this data
            'addressable_criteria': 'Insurance agencies with >5 employees',
            'tam_usd': 10000000,  # total addressable market
            'tam_calculation': '2,000 agencies × $5,000/year current spend',
            'sam_usd': 3000000,  # serviceable available market
            'sam_calculation': '600 agencies we can realistically serve × $5,000',
            'som_y3_usd': 150000,  # serviceable obtainable market year 3
            'som_calculation': '50 customers × $3,000/year (5% penetration)',
            'assumptions': [
                'Current ARPU is $5,000 based on NCCI pricing',
                'We can price at $3,000 (40% discount to incumbent)',
                '30% of market is addressable (agencies >5 employees)',
                '5% market penetration by year 3 is conservative for B2B SaaS'
            ]
        },
        'unit_economics': {
            'arpu_monthly': 250,
            'arpu_annual': 3000,
            'gross_margin': 0.85,  # 85%
            'gross_margin_calculation': {
                'revenue_per_customer': 3000,
                'data_acquisition_cost': 100,  # $2K/mo ÷ 50 customers
                'hosting_cost': 50,
                'support_cost': 300,
                'total_cogs': 450,
                'gross_profit': 2550,
                'margin_pct': 0.85
            },
            'cac_estimate': 1200,  # customer acquisition cost
            'cac_basis': 'Content marketing + inside sales for B2B',
            'ltv_estimate': 9180,  # lifetime value
            'ltv_calculation': '$3,000 ARPU × 36 months retention × 85% margin',
            'ltv_cac_ratio': 7.65,
            'payback_months': 4.7,
            'monthly_churn_rate': 0.028,  # 2.8% monthly = 30% annual
            'assessment': 'Excellent unit economics (LTV/CAC > 3, payback < 12mo)'
        },
        'market_dynamics': {
            'growth_rate': 0.05,  # 5% annually
            'growth_drivers': ['Insurance industry growth', 'Data adoption'],
            'market_maturity': 'mature',  # emerging, growing, mature, declining
            'competitive_intensity': 'medium',
            'pricing_power': 'medium'  # high, medium, low
        }
    }
    """
```

---

### 5. Data Moat Analyzer (`src/data_moat_analyzer.py`)

**Purpose**: Assess defensibility and competitive advantages

**Key Methods**:
```python
def analyze_data_moat(
    data_type: str,
    data_sources: Dict,
    vendor_landscape: Dict,
    market_sizing: Dict
) -> Dict[str, Any]:
    """
    Evaluate moat potential and defensibility

    Returns:
    {
        'data_type': 'Worker compensation insurance rates',
        'moat_factors': {
            'exclusivity': {
                'score': 3,  # 0-10
                'assessment': 'Low - data is publicly available',
                'explanation': 'Anyone can scrape state boards and rate filings',
                'improvement_potential': 'Medium - could get exclusive partnerships with carriers'
            },
            'network_effects': {
                'score': 4,
                'assessment': 'Low-Medium',
                'explanation': 'More customers = more coverage feedback, but not strong',
                'flywheel': 'User corrections improve data quality → attracts more users'
            },
            'data_quality': {
                'score': 7,
                'assessment': 'Medium-High',
                'explanation': 'Normalization and validation algorithms hard to replicate',
                'differentiation': 'Real-time updates, better UX, API access'
            },
            'switching_costs': {
                'score': 6,
                'assessment': 'Medium',
                'explanation': 'After API integration, high friction to switch',
                'lock_in_mechanisms': ['API integrations', 'Workflow dependencies', 'Historical data']
            },
            'scale_advantages': {
                'score': 8,
                'assessment': 'High',
                'explanation': 'Fixed cost to build scrapers, marginal cost near zero',
                'economies': 'Scraping infrastructure amortizes across customers'
            },
            'regulatory_barriers': {
                'score': 2,
                'assessment': 'Low',
                'explanation': 'No licensing requirements for public data',
                'compliance_needs': 'None significant'
            }
        },
        'overall_moat': {
            'composite_score': 5.0,  # average of factors
            'rating': 'Medium',  # Weak, Medium, Strong, Very Strong
            'primary_moat': 'Data quality and infrastructure',
            'secondary_moat': 'Switching costs after integration',
            'moat_sustainability': 'Medium - can be replicated but requires investment',
            'competitive_threats': [
                {
                    'threat': 'Incumbent drops pricing',
                    'probability': 0.30,
                    'mitigation': 'Focus on better UX and real-time updates'
                },
                {
                    'threat': 'Well-funded competitor builds similar infrastructure',
                    'probability': 0.20,
                    'mitigation': 'Move fast, lock in customers with integrations'
                }
            ]
        },
        'strategic_recommendations': [
            'Build best-in-class API and developer experience',
            'Pursue exclusive partnerships with state boards for advanced data',
            'Develop proprietary analytics on top of base data',
            'Create network effects through user feedback loops'
        ]
    }
    """
```

---

### 6. Data Product Designer (`src/data_product_designer.py`)

**Purpose**: Design the actual data product offering

**Key Methods**:
```python
def design_data_product(
    data_type: str,
    data_needs: Dict,
    vendor_landscape: Dict,
    target_customer: Dict
) -> Dict[str, Any]:
    """
    Design data product specifications

    Returns:
    {
        'data_type': 'Worker compensation insurance rates',
        'product_format': {
            'primary_delivery': 'REST API',
            'secondary_delivery': ['Excel downloads', 'CSV exports', 'Web dashboard'],
            'api_specifications': {
                'endpoints': [
                    'GET /rates/{state}/{job_classification}',
                    'GET /rates/history/{state}/{job_classification}',
                    'GET /carriers/{state}'
                ],
                'response_format': 'JSON',
                'rate_limits': '1,000 calls/day (basic), 10,000/day (premium)',
                'authentication': 'API key',
                'documentation': 'OpenAPI 3.0 spec'
            },
            'data_freshness': 'Updated daily (vs. quarterly for incumbent)',
            'historical_data': 'Last 5 years included',
            'coverage': 'All 50 US states'
        },
        'pricing_model': {
            'model_type': 'tiered_subscription',  # subscription, per_query, licensing, freemium
            'tiers': [
                {
                    'name': 'Starter',
                    'price_monthly': 149,
                    'includes': [
                        '1,000 API calls/month',
                        'All 50 states',
                        'Daily updates',
                        'Email support'
                    ],
                    'target': 'Small independent agencies'
                },
                {
                    'name': 'Professional',
                    'price_monthly': 399,
                    'includes': [
                        '10,000 API calls/month',
                        'All 50 states',
                        'Daily updates',
                        'Historical data (5 years)',
                        'Priority support'
                    ],
                    'target': 'Mid-size agencies'
                },
                {
                    'name': 'Enterprise',
                    'price_monthly': 999,
                    'includes': [
                        'Unlimited API calls',
                        'All 50 states',
                        'Real-time updates',
                        'Historical data (10 years)',
                        'Dedicated support',
                        'Custom integrations',
                        'SLA guarantees'
                    ],
                    'target': 'Large agencies and carriers'
                }
            ],
            'pricing_rationale': '50-70% cheaper than incumbent, justified by cost structure'
        },
        'integrations': {
            'priority_integrations': [
                'Applied Epic (agency management system)',
                'Salesforce',
                'HubSpot'
            ],
            'integration_strategy': 'API-first, then native integrations for top 3 AMS platforms'
        },
        'feature_roadmap': {
            'mvp': ['Basic API', 'All states', 'Daily updates'],
            'v2': ['Historical data', 'Web dashboard', 'Excel exports'],
            'v3': ['Predictive analytics', 'Rate change alerts', 'Custom integrations']
        }
    }
    """
```

---

### 7. Data Opportunity Synthesizer (`src/data_opportunity_synthesizer.py`)

**Purpose**: Synthesize all analysis into actionable opportunity report

**Key Methods**:
```python
def synthesize_opportunity(
    all_analysis_data: Dict
) -> str:
    """
    Generate comprehensive data-vendor opportunity report

    Returns: Markdown report with structure:

    # DATA-VENDOR OPPORTUNITY: [Data Type]
    # NAICS: [8-digit code] - [Description]

    ## EXECUTIVE SUMMARY
    - **Opportunity Type**: [White-Space / Disruption / Aggregation]
    - **Market Size**: $[TAM]M TAM / $[SAM]M SAM / $[SOM]M SOM (Y3)
    - **Investment Score**: [0-100] - [TIER_1 / TIER_2 / TIER_3 / PASS]
    - **Primary Moat**: [Description]
    - **Time to Market**: [Estimate]

    ## DATA NEED
    ### What Businesses Need
    - **Data Type**: [Specific data type]
    - **Business Function**: [How it's used]
    - **Decision Impact**: [What depends on this data]
    - **Frequency of Need**: [Daily / Weekly / Monthly]
    - **Importance Level**: [Critical / High / Medium / Low]

    ### Current Pain Points
    1. [Pain point with current access]
    2. [Pain point with current access]

    ## VENDOR LANDSCAPE
    ### Existing Vendors
    [For each vendor]
    - **[Vendor Name]**: $[Price], [Market Position]
      - Strengths: [...]
      - Weaknesses: [...]
      - Customer Satisfaction: [Score]

    ### Market Gaps
    1. [Identified gap]
    2. [Identified gap]

    ### Opportunity Classification
    - **Type**: [White-Space / Disruption / Aggregation]
    - **Rationale**: [Why this classification]

    ## DATA SOURCING STRATEGY
    ### Primary Data Sources
    1. **[Source Name]**: [Access method], $[Cost], [Update frequency]
    2. **[Source Name]**: [Access method], $[Cost], [Update frequency]

    ### Acquisition Plan
    - **Approach**: [Description]
    - **Setup Cost**: $[Amount]
    - **Ongoing Cost**: $[Amount]/month
    - **Time to First Data**: [Timeline]
    - **Exclusivity**: [High / Medium / Low]

    ## MARKET SIZING
    ### Market Metrics
    - **Total Establishments**: [Count]
    - **Addressable Market**: [Count] ([Criteria])
    - **TAM**: $[Amount]M
    - **SAM**: $[Amount]M
    - **SOM (Y3)**: $[Amount]M

    ### Unit Economics
    - **ARPU**: $[Amount]/year
    - **Gross Margin**: [Percent]%
    - **CAC**: $[Amount]
    - **LTV**: $[Amount]
    - **LTV/CAC**: [Ratio]x
    - **Payback**: [Months] months

    ### Assessment
    [Overall unit economics assessment]

    ## COMPETITIVE MOAT
    ### Moat Factors (0-10 scale)
    - **Exclusivity**: [Score] - [Assessment]
    - **Network Effects**: [Score] - [Assessment]
    - **Data Quality**: [Score] - [Assessment]
    - **Switching Costs**: [Score] - [Assessment]
    - **Scale Advantages**: [Score] - [Assessment]

    ### Overall Moat: [Weak / Medium / Strong / Very Strong]
    **Primary Moat**: [Description]

    ## DATA PRODUCT DESIGN
    ### Product Offering
    - **Format**: [API / Dashboard / Reports / etc.]
    - **Update Frequency**: [Real-time / Daily / Weekly]
    - **Coverage**: [Geographic / Temporal scope]

    ### Pricing
    [Tier breakdown]

    ### Key Features
    1. [Feature]
    2. [Feature]

    ## GO-TO-MARKET STRATEGY
    ### Target Customer
    - **ICP**: [Description]
    - **Company Size**: [Range]
    - **Budget**: [Range]

    ### Distribution Channels
    1. [Channel]
    2. [Channel]

    ### Sales Motion
    - **Model**: [Self-serve / Inside sales / Field sales]

    ## INVESTMENT ANALYSIS
    ### Opportunity Score: [0-100]

    **Scoring Breakdown**:
    - Market Size (30%): [Score]/100
    - Moat Strength (25%): [Score]/100
    - Data Accessibility (20%): [Score]/100
    - Competitive Position (15%): [Score]/100
    - Unit Economics (10%): [Score]/100

    ### Classification: [TIER_1 / TIER_2 / TIER_3 / PASS]
    - **TIER_1 (80+)**: Prime opportunity - pursue immediately
    - **TIER_2 (60-79)**: Strong potential - deep dive recommended
    - **TIER_3 (40-59)**: Worth exploring - validate key assumptions
    - **PASS (<40)**: Low priority - revisit later

    ### Key Risks
    1. **[Risk]**: [Probability]%, [Mitigation]
    2. **[Risk]**: [Probability]%, [Mitigation]

    ### Investment Requirements
    - **Initial Capital**: $[Amount]
    - **Time to Revenue**: [Timeline]
    - **Break-even**: [Timeline]

    ## STRATEGIC RECOMMENDATIONS
    1. [Recommendation]
    2. [Recommendation]
    3. [Recommendation]

    ---

    **Analysis Date**: [Date]
    **Confidence Level**: [0.0-1.0]
    **Run ID**: [Audit trail ID]
    """
```

---

## 🔍 SEARCH STRATEGIES (COMPREHENSIVE)

### Data Needs Discovery Queries (20-30 searches)

```python
DATA_NEEDS_SEARCHES = [
    # Phase 1: Direct data need identification (5-7 searches)
    'site:reddit.com "{segment_description}" "what data"',
    'site:reddit.com "{segment_description}" "data source"',
    '"{segment_description}" industry "data requirements"',
    '"{segment_description}" "business intelligence" needs',
    '"{segment_description}" "KPIs" track',

    # Phase 2: Job posting analysis (3-5 searches)
    'site:linkedin.com "{segment_description}" "data analyst" job',
    'site:indeed.com "{segment_description}" data requirements',
    '"{segment_description}" "business analyst" responsibilities data',

    # Phase 3: Regulatory/compliance data (2-3 searches)
    '"{segment_description}" regulatory reporting requirements',
    '"{segment_description}" compliance data needed',

    # Phase 4: Operational data discovery (4-6 searches)
    '"{segment_description}" pricing data sources',
    '"{segment_description}" market data providers',
    '"{segment_description}" "how do you get" data',
    '"{segment_description}" benchmarking data',
    '"{segment_description}" industry metrics',

    # Phase 5: Pain point discovery (4-6 searches)
    'site:reddit.com "{segment_description}" "data is expensive"',
    '"{segment_description}" "can\'t find data"',
    '"{segment_description}" "data quality" problems',
    '"{segment_description}" "need better data"',
    '"{segment_description}" data vendor complaints'
]
```

### Vendor Intelligence Queries (15-20 searches)

```python
VENDOR_INTELLIGENCE_SEARCHES = [
    # Phase 1: Vendor discovery (5-7 searches per data type)
    '"{data_type}" data vendor',
    '"{data_type}" data provider API',
    'buy "{data_type}" subscription',
    '"{data_type}" database provider',
    'best "{data_type}" data source',

    # Phase 2: Pricing research (3-4 searches per vendor)
    '"{vendor_name}" pricing',
    '"{vendor_name}" cost',
    '"{vendor_name}" pricing model',

    # Phase 3: Review/satisfaction research (3-4 searches per vendor)
    'site:g2.com "{vendor_name}"',
    'site:capterra.com "{vendor_name}"',
    'site:reddit.com "{vendor_name}" review',

    # Phase 4: Competitive research (2-3 searches per vendor)
    '"{vendor_name}" vs "{competitor}"',
    '"{vendor_name}" alternative',
    '"{data_type}" vendor comparison'
]
```

### Data Source Discovery Queries (10-15 searches)

```python
DATA_SOURCE_SEARCHES = [
    # Phase 1: Government/public sources (4-5 searches)
    '"{data_type}" government database',
    '"{data_type}" public data API',
    '"{data_type}" open data',

    # Phase 2: Industry sources (3-4 searches)
    '{segment} industry association data',
    '{segment} trade group database',

    # Phase 3: Commercial sources (3-4 searches)
    '"{data_type}" API documentation',
    'where to get "{data_type}"',
    '"{data_type}" data collection'
]
```

**Total Searches Per 8-Digit NAICS**: ~50-65 searches (comprehensive)

---

## 📊 SCORING METHODOLOGY

### Composite Opportunity Score (0-100)

```python
OPPORTUNITY_SCORE = (
    MARKET_SIZE_SCORE * 0.30 +
    MOAT_SCORE * 0.25 +
    DATA_ACCESSIBILITY_SCORE * 0.20 +
    COMPETITIVE_POSITION_SCORE * 0.15 +
    UNIT_ECONOMICS_SCORE * 0.10
)
```

### Component Scoring Details

**1. Market Size Score (0-100, weight 30%)**
```python
def calculate_market_size_score(tam_usd, growth_rate):
    # TAM component (0-70 points)
    if tam_usd >= 100_000_000:
        tam_points = 70
    elif tam_usd >= 50_000_000:
        tam_points = 60
    elif tam_usd >= 10_000_000:
        tam_points = 50
    elif tam_usd >= 5_000_000:
        tam_points = 40
    elif tam_usd >= 1_000_000:
        tam_points = 30
    else:
        tam_points = 20

    # Growth component (0-30 points)
    if growth_rate >= 0.20:
        growth_points = 30
    elif growth_rate >= 0.10:
        growth_points = 25
    elif growth_rate >= 0.05:
        growth_points = 20
    elif growth_rate >= 0.02:
        growth_points = 15
    else:
        growth_points = 10

    return tam_points + growth_points
```

**2. Moat Score (0-100, weight 25%)**
```python
def calculate_moat_score(moat_factors):
    # Average of 6 moat factors (each 0-10)
    avg = (
        moat_factors['exclusivity'] +
        moat_factors['network_effects'] +
        moat_factors['data_quality'] +
        moat_factors['switching_costs'] +
        moat_factors['scale_advantages'] +
        moat_factors['regulatory_barriers']
    ) / 6

    return avg * 10  # Convert to 0-100
```

**3. Data Accessibility Score (0-100, weight 20%)**
```python
def calculate_accessibility_score(data_sources):
    # Based on cost and difficulty to acquire data

    if data_sources['accessibility'] == 'public' and data_sources['cost_estimate'] == '$0':
        base_score = 90
    elif data_sources['accessibility'] == 'public':
        base_score = 80
    elif data_sources['accessibility'] == 'licensable' and data_sources['cost_estimate'] < 10000:
        base_score = 60
    elif data_sources['accessibility'] == 'licensable':
        base_score = 40
    else:  # proprietary or restricted
        base_score = 20

    # Adjust for collection complexity
    if data_sources['collection_complexity'] == 'low':
        complexity_multiplier = 1.0
    elif data_sources['collection_complexity'] == 'medium':
        complexity_multiplier = 0.9
    else:  # high
        complexity_multiplier = 0.7

    return base_score * complexity_multiplier
```

**4. Competitive Position Score (0-100, weight 15%)**
```python
def calculate_competitive_score(vendor_landscape, opportunity_type):
    # Base score by opportunity type
    if opportunity_type == 'white_space':
        base_score = 90  # No competition
    elif opportunity_type == 'disruption':
        # Score based on incumbent weaknesses
        customer_sat = vendor_landscape.get('avg_customer_satisfaction', 3.0)
        if customer_sat < 3.0:
            base_score = 80  # Weak incumbent
        elif customer_sat < 3.5:
            base_score = 70
        else:
            base_score = 50  # Strong incumbent
    else:  # aggregation
        if vendor_landscape.get('competition_level') == 'fragmented':
            base_score = 70
        else:
            base_score = 50

    # Adjust for barriers to entry
    barriers = vendor_landscape.get('barriers_to_entry')
    if barriers == 'low':
        base_score *= 0.9  # Easy for others to enter too
    elif barriers == 'medium':
        base_score *= 1.0
    else:  # high
        base_score *= 1.1  # Hard for others to compete

    return min(base_score, 100)
```

**5. Unit Economics Score (0-100, weight 10%)**
```python
def calculate_unit_economics_score(unit_economics):
    ltv_cac = unit_economics.get('ltv_cac_ratio', 0)
    gross_margin = unit_economics.get('gross_margin', 0)
    payback_months = unit_economics.get('payback_months', 99)

    # LTV/CAC score (0-50 points)
    if ltv_cac >= 5:
        ltv_cac_points = 50
    elif ltv_cac >= 3:
        ltv_cac_points = 40
    elif ltv_cac >= 2:
        ltv_cac_points = 30
    elif ltv_cac >= 1:
        ltv_cac_points = 20
    else:
        ltv_cac_points = 10

    # Gross margin score (0-30 points)
    if gross_margin >= 0.80:
        margin_points = 30
    elif gross_margin >= 0.60:
        margin_points = 25
    elif gross_margin >= 0.40:
        margin_points = 20
    else:
        margin_points = 10

    # Payback score (0-20 points)
    if payback_months <= 6:
        payback_points = 20
    elif payback_months <= 12:
        payback_points = 15
    elif payback_months <= 18:
        payback_points = 10
    else:
        payback_points = 5

    return ltv_cac_points + margin_points + payback_points
```

### Tier Classification

```python
def classify_opportunity(score):
    if score >= 80:
        return "TIER_1"  # Prime opportunity - pursue immediately
    elif score >= 60:
        return "TIER_2"  # Strong potential - deep dive recommended
    elif score >= 40:
        return "TIER_3"  # Worth exploring - validate assumptions
    else:
        return "PASS"    # Low priority - revisit later
```

---

## 🗄️ DATA STRUCTURES & STATE

### Enhanced AnalysisState

```python
class DataVendorAnalysisState(TypedDict):
    # Input
    naics_8_digit: str
    segment_description: str
    phase: str  # "PHASE_2_DATA_VENDOR"
    run_id: str

    # Discovery outputs
    data_needs: Dict[str, Any]
    vendor_landscape: Dict[str, Any]
    data_sources: Dict[str, Any]

    # Analysis outputs
    market_sizing: Dict[str, Any]
    moat_analysis: Dict[str, Any]
    product_design: Dict[str, Any]

    # Final output
    opportunities: List[Dict[str, Any]]  # Ranked list of data-vendor opportunities
    final_report: str

    # Metadata
    error: str
    error_count: int
    completed: bool
```

---

## 🔄 WORKFLOW ORCHESTRATION

### Phase 2 Workflow Graph

```python
def _build_phase2_workflow(self) -> StateGraph:
    """Build Phase 2 data-vendor analysis workflow"""

    workflow = StateGraph(DataVendorAnalysisState)

    # Discovery nodes
    workflow.add_node("data_needs_discovery", self._data_needs_node)
    workflow.add_node("vendor_intelligence", self._vendor_intelligence_node)
    workflow.add_node("data_source_mapping", self._data_source_mapping_node)

    # Analysis nodes
    workflow.add_node("market_sizing", self._market_sizing_node)
    workflow.add_node("moat_analysis", self._moat_analysis_node)
    workflow.add_node("product_design", self._product_design_node)

    # Synthesis node
    workflow.add_node("synthesize", self._synthesize_node)
    workflow.add_node("save_results", self._save_node)

    # Define flow
    workflow.set_entry_point("data_needs_discovery")
    workflow.add_edge("data_needs_discovery", "vendor_intelligence")
    workflow.add_edge("vendor_intelligence", "data_source_mapping")
    workflow.add_edge("data_source_mapping", "market_sizing")
    workflow.add_edge("market_sizing", "moat_analysis")
    workflow.add_edge("moat_analysis", "product_design")
    workflow.add_edge("product_design", "synthesize")
    workflow.add_edge("synthesize", "save_results")
    workflow.add_edge("save_results", END)

    return workflow.compile()
```

---

## 🚀 IMPLEMENTATION PHASES

### Phase 2A: Foundation (Week 1)

**Goal**: Create infrastructure and core agents

**Tasks**:
1. **Create new agent files** (Day 1-2)
   - [ ] `src/data_needs_researcher.py`
   - [ ] `src/vendor_intelligence_agent.py`
   - [ ] `src/data_source_mapper.py`
   - [ ] `src/data_market_sizer.py`
   - [ ] `src/data_moat_analyzer.py`
   - [ ] `src/data_product_designer.py`
   - [ ] `src/data_opportunity_synthesizer.py`

2. **Create Phase 2 analyzer** (Day 3-4)
   - [ ] `src/data_vendor_analyzer.py` - Main orchestrator
   - [ ] Implement `DataVendorAnalysisState` TypedDict
   - [ ] Build workflow graph
   - [ ] Integrate with audit database

3. **Create entry point** (Day 4-5)
   - [ ] `run_data_vendor_analysis.py` - CLI entry point
   - [ ] Handle 8-digit NAICS input file (CSV)
   - [ ] Batch processing support
   - [ ] Progress indicators

4. **Update database schemas** (Day 5)
   - [ ] Add `data_vendor_opportunities` table to DatabaseManager
   - [ ] Add audit tracking for Phase 2 specific operations
   - [ ] Create views for data-vendor reporting

**Deliverables**:
- 7 new agent files with method stubs
- Main orchestrator working (even if agents return mock data)
- Entry point script functional
- Database ready

---

### Phase 2B: Agent Implementation (Week 2-3)

**Goal**: Implement each agent fully with search strategies and LLM prompts

**Tasks**:

1. **Data Needs Researcher** (Days 6-8)
   - [ ] Implement search query generation
   - [ ] Build web search integration
   - [ ] Create LLM prompt for extracting data needs
   - [ ] Add importance/frequency scoring
   - [ ] Test with sample 8-digit NAICS

2. **Vendor Intelligence Agent** (Days 9-11)
   - [ ] Implement vendor discovery searches
   - [ ] Build pricing extraction logic
   - [ ] Create review/satisfaction analysis
   - [ ] Identify gaps and weaknesses
   - [ ] Test vendor landscape mapping

3. **Data Source Mapper** (Days 12-14)
   - [ ] Implement source discovery searches
   - [ ] Build accessibility assessment
   - [ ] Create cost estimation logic
   - [ ] Test source mapping

4. **Data Market Sizer** (Days 15-17)
   - [ ] Implement TAM/SAM/SOM calculations
   - [ ] Build unit economics modeling
   - [ ] Create ARPU estimation
   - [ ] Test market sizing accuracy

5. **Data Moat Analyzer** (Days 18-20)
   - [ ] Implement moat factor scoring
   - [ ] Build composite moat calculation
   - [ ] Create threat assessment
   - [ ] Test moat analysis

6. **Data Product Designer** (Days 21-23)
   - [ ] Implement product format design
   - [ ] Build pricing model generator
   - [ ] Create integration recommendations
   - [ ] Test product design

7. **Data Opportunity Synthesizer** (Days 24-26)
   - [ ] Implement scoring algorithm
   - [ ] Build report generation
   - [ ] Create ranking logic
   - [ ] Test complete synthesis

**Deliverables**:
- All 7 agents fully functional
- Comprehensive test suite
- Sample outputs for 2-3 test cases

---

### Phase 2C: Integration & Testing (Week 4)

**Goal**: End-to-end integration and validation

**Tasks**:

1. **Integration** (Days 27-28)
   - [ ] Connect all agents in workflow
   - [ ] Test complete pipeline
   - [ ] Fix integration issues
   - [ ] Optimize performance

2. **Audit Integration** (Day 29)
   - [ ] Add search query logging
   - [ ] Add LLM call tracking
   - [ ] Add cost tracking
   - [ ] Test audit trail completeness

3. **Testing** (Days 30-31)
   - [ ] Test with 5-10 diverse 8-digit NAICS
   - [ ] Validate output quality
   - [ ] Check cost per analysis
   - [ ] Verify timing/performance

4. **Documentation** (Days 32-33)
   - [ ] Update SYSTEM_DOCUMENTATION.md
   - [ ] Create PHASE_2_USER_GUIDE.md
   - [ ] Document scoring methodology
   - [ ] Create troubleshooting guide

**Deliverables**:
- Fully integrated Phase 2 system
- Complete documentation
- Test results and validation

---

### Phase 2D: Production Deployment (Week 5)

**Goal**: Deploy and optimize for production use

**Tasks**:

1. **Optimization** (Days 34-35)
   - [ ] Optimize search queries
   - [ ] Reduce redundant LLM calls
   - [ ] Improve prompt efficiency
   - [ ] Batch processing optimization

2. **Tooling** (Day 36-37)
   - [ ] Create batch runner for multiple NAICS
   - [ ] Build comparison tool (compare opportunities across segments)
   - [ ] Create export to spreadsheet functionality

3. **Production Testing** (Days 38-39)
   - [ ] Run on user's actual 8-digit NAICS list
   - [ ] Validate results
   - [ ] Adjust based on feedback

4. **Final Polish** (Day 40)
   - [ ] Bug fixes
   - [ ] Performance tuning
   - [ ] Documentation updates

**Deliverables**:
- Production-ready Phase 2 system
- Batch processing tools
- Complete user guide

---

## 📂 FILE STRUCTURE (After Phase 2)

```
industry_taxonomy_oportunity_finder/
├── src/
│   # Phase 1 agents (existing)
│   ├── analyzer.py
│   ├── research_agent.py
│   ├── strategic_agent.py
│   ├── quantitative_agent.py
│   ├── synthesizer_agent.py
│   ├── supervisor_agent.py
│   ├── product_manager_agent.py
│   ├── technical_data_scientist_agent.py
│
│   # Phase 2 agents (new)
│   ├── data_vendor_analyzer.py          # Main Phase 2 orchestrator
│   ├── data_needs_researcher.py         # Data needs discovery
│   ├── vendor_intelligence_agent.py     # Vendor landscape mapping
│   ├── data_source_mapper.py            # Data source identification
│   ├── data_market_sizer.py             # Market sizing for data products
│   ├── data_moat_analyzer.py            # Moat/defensibility analysis
│   ├── data_product_designer.py         # Product design
│   ├── data_opportunity_synthesizer.py  # Report synthesis
│
│   # Shared infrastructure (existing)
│   ├── database.py
│   ├── rag_database.py
│   └── audit_database.py
│
├── run_data_vendor_analysis.py         # Phase 2 entry point (new)
├── batch_data_vendor_analysis.py       # Batch processor (new)
├── compare_opportunities.py             # Comparison tool (new)
│
├── run_analysis.py                      # Phase 1 entry point (existing)
├── batch_analyze.py                     # Phase 1 batch (existing)
├── analyze.py                           # Phase 1 CLI (existing)
├── view_audit.py                        # Audit viewer (existing)
│
├── PHASE_2_IMPLEMENTATION_PLAN.md      # This document
├── PHASE_2_USER_GUIDE.md               # User guide (to be created)
├── SYSTEM_DOCUMENTATION.md             # Updated for Phase 2
├── RECAP.md                            # Updated after Phase 2
│
└── data/
    ├── audit_trail.db                  # Complete audit log
    ├── intelligence.db                 # Phase 1 results
    ├── data_vendor_opportunities.db    # Phase 2 results (new)
    └── chromadb/                       # Vector embeddings
```

---

## 🧪 TESTING STRATEGY

### Test Cases (8-Digit NAICS Samples)

**Test Case 1: Insurance Carriers - Workers Compensation (524126)**
- **Expected**: Strong incumbent (NCCI), high data need, public sources available
- **Opportunity Type**: Disruption
- **Expected Score**: TIER_2 (65-75)

**Test Case 2: Family Restaurants (722511)**
- **Expected**: Multiple data needs (foot traffic, menu pricing, food costs)
- **Opportunity Type**: White-space or Aggregation
- **Expected Score**: TIER_2 or TIER_3

**Test Case 3: Auto Dealers - New Cars (441110)**
- **Expected**: Established vendors (Kelley Blue Book, Edmunds, etc.)
- **Opportunity Type**: Likely PASS (strong incumbents)
- **Expected Score**: TIER_3 or PASS

**Test Case 4: Physicians - General Practice (621111)**
- **Expected**: Multiple data needs (drug interactions, treatment outcomes, insurance coverage)
- **Opportunity Type**: Mixed (some white-space, some disruption)
- **Expected Score**: TIER_2

**Test Case 5: Commercial Banking (522110)**
- **Expected**: Highly regulated, many incumbents
- **Opportunity Type**: Likely PASS (high barriers, strong incumbents)
- **Expected Score**: PASS

### Validation Criteria

For each test case, validate:
- [ ] Data needs discovered are specific and actionable
- [ ] Vendors identified are accurate
- [ ] Pricing estimates are reasonable
- [ ] Market sizing calculations are logical
- [ ] Moat assessment is thoughtful
- [ ] Scoring seems fair and consistent
- [ ] Report is comprehensive and actionable

---

## 💰 COST ESTIMATION (Phase 2 Analysis)

### Per 8-Digit NAICS Analysis

**Phase 2 (Data-Vendor Discovery):**
- Searches: ~50-65 web searches
- LLM Calls: ~15-20 calls
- Tokens: ~250K input + ~40K output
- **Cost**: ~$1.20-1.80 per 8-digit NAICS (using Sherlock-Think-Alpha)
- **Time**: 6-10 minutes per segment

### Batch Analysis (100 segments)

- **Total Cost**: $120-180
- **Total Time**: 10-17 hours (can run overnight)
- **Output**: 100 comprehensive data-vendor opportunity reports

---

## 🎯 SUCCESS METRICS

### Quantitative Metrics

1. **Coverage**: Analyze 100% of provided 8-digit NAICS codes
2. **Discovery Rate**: Find at least 1 data need per segment (>90%)
3. **Vendor Mapping**: Identify vendors for >70% of data needs
4. **Scoring Consistency**: Tier classifications should be actionable
5. **Cost Efficiency**: <$2 per analysis
6. **Processing Time**: <10 minutes per analysis

### Qualitative Metrics

1. **Data Needs Specificity**: Needs should be actionable (not generic)
2. **Vendor Intelligence**: Pricing and gaps should be accurate
3. **Source Feasibility**: Data sourcing strategies should be realistic
4. **Market Sizing**: Calculations should be defensible
5. **Report Quality**: Reports should be comprehensive and actionable

---

## 🚧 RISK MITIGATION

### Technical Risks

**Risk 1: Search Results Quality**
- **Issue**: Web searches may not return enough information
- **Mitigation**:
  - Use 50-65 searches per segment (comprehensive)
  - Multiple query variations
  - Aggregate across sources
  - Confidence scoring to flag weak analyses

**Risk 2: LLM Hallucination**
- **Issue**: LLM may fabricate vendor names or pricing
- **Mitigation**:
  - Require source attribution
  - Flag low-confidence extractions
  - Manual validation on sample (5-10%)
  - Cross-reference vendor names against actual websites

**Risk 3: Vendor Landscape Gaps**
- **Issue**: May miss obscure vendors
- **Mitigation**:
  - Multiple search strategies
  - Industry-specific forums
  - Accept incompleteness (document in confidence score)

### Operational Risks

**Risk 4: Batch Processing Failures**
- **Issue**: Failure mid-batch loses progress
- **Mitigation**:
  - Save after each segment
  - Resume capability
  - Comprehensive audit trail

**Risk 5: Cost Overruns**
- **Issue**: More LLM calls than expected
- **Mitigation**:
  - Pre-calculate estimated cost
  - Budget warnings
  - Cost tracking per segment

---

## 📚 NEXT STEPS

### Immediate Actions (This Session)

1. **Review this plan with user**
   - Confirm approach is correct
   - Adjust priorities if needed
   - Get approval to proceed

2. **Clarify inputs**
   - Get sample 8-digit NAICS list with descriptions
   - Understand any specific focus areas
   - Confirm output format expectations

3. **Begin Phase 2A**
   - Create agent file stubs
   - Set up basic workflow
   - Implement one complete agent (Data Needs Researcher) as proof of concept

### Follow-Up Sessions

1. **Session 2**: Complete Phase 2A (Foundation)
2. **Session 3-4**: Implement agents (Phase 2B)
3. **Session 5**: Integration and testing (Phase 2C)
4. **Session 6**: Production deployment and user testing (Phase 2D)

---

## 📞 QUESTIONS FOR USER

Before proceeding, please clarify:

1. **Input Format**: Will you provide a CSV with columns `[naics_8_digit, description]`? Or another format?

2. **Scope**: How many 8-digit NAICS codes will we analyze? (10? 100? 1000?)

3. **Prioritization**: Should we focus on:
   - White-space opportunities (no vendors exist)?
   - Disruption opportunities (expensive/weak incumbents)?
   - Large markets (TAM > $50M)?
   - Or balanced across all factors?

4. **Timeline**: When do you need results?
   - Urgent (1-2 weeks)?
   - Standard (4-5 weeks)?
   - Flexible?

5. **Validation**: Do you want to review/validate outputs from first 5-10 segments before doing full batch?

---

**Ready to proceed?** Let me know if you'd like to:
- A) Start implementing Phase 2A (create agent stubs and workflow)
- B) Refine the plan further
- C) Test with a single 8-digit NAICS first (proof of concept)


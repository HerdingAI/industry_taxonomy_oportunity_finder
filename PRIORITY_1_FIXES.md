# Priority 1 Bug Fixes

These are critical fixes that must be applied before production use.

---

## Fix #1: Directory Creation (Bug #1)

**File**: `src/database.py` line 21

**Current**:
```python
self.db_dir.mkdir(exist_ok=True)
```

**Fixed**:
```python
self.db_dir.mkdir(parents=True, exist_ok=True)
```

**Reason**: Without `parents=True`, fails if parent directories don't exist (e.g., user specifies "data/professional_services")

---

## Fix #2: Error Counting Mechanism (Bug #3)

**File**: `src/analyzer.py` - Add to AnalysisState

**Add to AnalysisState TypedDict**:
```python
class AnalysisState(TypedDict):
    """State passed between agents"""
    naics_code: str
    industry_name: str

    # Agent outputs
    research_data: Dict[str, Any]
    strategic_data: Dict[str, Any]
    quantitative_data: Dict[str, Any]
    final_report: str

    # Metadata
    error: str
    error_count: int  # NEW: Track number of errors
    completed: bool
```

**Add error checking after each node**:
```python
def _check_errors(self, state: AnalysisState) -> AnalysisState:
    """Check if too many errors have occurred"""
    MAX_ERRORS = 3  # Configurable threshold

    if state.get('error'):
        state['error_count'] = state.get('error_count', 0) + 1

        if state['error_count'] >= MAX_ERRORS:
            print(f"\n❌ Too many errors ({state['error_count']}). Aborting analysis.")
            state['completed'] = False
            # Could add early termination logic here

    return state
```

---

## Fix #3: Empty Search Results (Bug #4)

**File**: `src/research_agent.py` in `_gather_market_data`, `_research_competition`, `_research_tech_and_pain`

**Add check after search**:
```python
search_results = []
for query in queries:
    try:
        results = list(self.ddg.text(query, max_results=3))

        # NEW: Check if results are empty
        if not results:
            print(f"  ⚠️  No results for '{query}'")
            continue

        search_results.extend(results)
    except Exception as e:
        print(f"  ⚠️  Search failed for '{query}': {e}")
        continue

# NEW: Check if we got ANY results
if not search_results:
    print(f"  ⚠️  No search results found. Using LLM knowledge (lower confidence).")
    # Still continue, but mark low confidence
    # LLM will use its training data
```

---

## Fix #4: JSON Parsing Fallback (Bug #5)

**File**: All agents - update `_parse_json()` methods

**Current** (returns empty dict):
```python
return {'confidence': 0.1}
```

**Fixed** (return minimal valid structure):

### research_agent.py:
```python
def _parse_json_response(self, content: str) -> Dict[str, Any]:
    """Extract JSON from LLM response"""
    # ... existing parsing logic ...

    # If all fails, return minimal structure instead of empty dict
    print(f"  ⚠️  Failed to parse JSON, returning minimal structure")
    return {
        'market_size_usd': None,
        'growth_rate': None,
        'establishments': None,
        'employment': None,
        'avg_wage': None,
        'hhi_index': None,
        'top_players': [],
        'pain_points': [],
        'common_tools': [],
        'confidence': 0.1  # Mark as very low confidence
    }
```

### strategic_agent.py:
```python
def _parse_json(self, content: str) -> Dict[str, Any]:
    # ... existing parsing logic ...

    print(f"  ⚠️  Failed to parse JSON")
    return {
        'competitive_rivalry': {'score': 50, 'insight': 'Unable to assess'},
        'new_entrant_threat': {'score': 50, 'insight': 'Unable to assess'},
        'supplier_power': {'score': 50, 'insight': 'Unable to assess'},
        'buyer_power': {'score': 50, 'insight': 'Unable to assess'},
        'substitute_threat': {'score': 50, 'insight': 'Unable to assess'},
        'overall_attractiveness': 50,
        'strategic_verdict': 'Insufficient data for analysis'
    }
```

### quantitative_agent.py:
```python
def _parse_json(self, content: str) -> Dict[str, Any]:
    # ... existing parsing logic ...

    print(f"  ⚠️  Failed to parse JSON")
    return {
        'opportunity_title': 'Analysis Failed',
        'market_sizing': {'tam_usd': None, 'sam_usd': None, 'som_y3_usd': None, 'confidence': 0.1},
        'unit_economics': {'arpu': None, 'gross_margin': None, 'ltv': None, 'cac': None, 'ltv_cac_ratio': None},
        'scoring': {'weighted_score': 0},
        'risk_assessment': {'key_risks': []},
        'strategic_rationale': {},
        'overall_confidence': 0.1
    }
```

---

## Fix #5: Safe Dictionary Access (Bug #10)

**File**: `src/analyzer.py` in `_save_node()`

**Current** (direct access):
```python
market_sizing = opp.get('market_sizing', {})
unit_econ = opp.get('unit_economics', {})
rationale = opp.get('strategic_rationale', {})
risk = opp.get('risk_assessment', {})

opp_id = self.db.save_opportunity({
    'naics_code': state['naics_code'],
    'title': opp.get('opportunity_title'),
    'tam_usd': market_sizing.get('tam_usd'),  # Safe, but could be better
    # ...
})
```

**Fixed** (with defaults):
```python
market_sizing = opp.get('market_sizing', {})
unit_econ = opp.get('unit_economics', {})
rationale = opp.get('strategic_rationale', {})
risk = opp.get('risk_assessment', {})

# Use helper function for safe access
def safe_get(d, key, default=None):
    """Safely get nested dict values"""
    return d.get(key, default) if isinstance(d, dict) else default

opp_id = self.db.save_opportunity({
    'naics_code': state['naics_code'],
    'title': safe_get(opp, 'opportunity_title', 'Unnamed Opportunity'),
    'description': safe_get(opp, 'opportunity_description', ''),
    'opportunity_type': 'ai_automation',
    'opportunity_score': safe_get(opp, 'risk_adjusted_score', 0),
    'confidence': safe_get(opp, 'overall_confidence', 0),
    'risk_adjusted_score': safe_get(opp, 'risk_adjusted_score', 0),
    'tam_usd': safe_get(market_sizing, 'tam_usd'),
    'sam_usd': safe_get(market_sizing, 'sam_usd'),
    'som_y3_usd': safe_get(market_sizing, 'som_y3_usd'),
    'arpu': safe_get(unit_econ, 'arpu'),
    'gross_margin': safe_get(unit_econ, 'gross_margin'),
    'ltv': safe_get(unit_econ, 'ltv'),
    'cac': safe_get(unit_econ, 'cac'),
    'ltv_cac_ratio': safe_get(unit_econ, 'ltv_cac_ratio'),
    'payback_months': safe_get(unit_econ, 'payback_months'),
    'key_moat': safe_get(rationale, 'key_moat', ''),
    'why_now': safe_get(rationale, 'why_now', ''),
    'why_unsolved': safe_get(rationale, 'why_unsolved', ''),
    'competitive_threat': safe_get(rationale, 'competitive_threat', ''),
    'risk_factors': safe_get(risk, 'key_risks', []),
    'expected_value_y5_usd': safe_get(risk, 'expected_value_y5_usd')
})
```

---

## Application Instructions

1. Read BUGS_FOUND.md for full context
2. Apply fixes in order (Fix #1 first, then #2, etc.)
3. Test after each fix if possible
4. Commit fixes with descriptive messages

---

## Testing Checklist

After applying fixes:

- [ ] Test with valid NAICS code (541511)
- [ ] Test with invalid NAICS code (999999)
- [ ] Test with network disabled (simulate search failure)
- [ ] Test batch analysis with 3 codes
- [ ] Verify error counting works (inject 4 errors, should abort)
- [ ] Check all database fields populated correctly
- [ ] Verify reports generated successfully

---

**Status**: Ready to apply once installation completes
**Impact**: Prevents crashes and data loss
**Priority**: CRITICAL

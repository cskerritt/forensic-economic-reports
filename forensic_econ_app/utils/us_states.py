"""
US States data with regional adjustments and automation helpers
"""

# US States and territories with full names and abbreviations
US_STATES = [
    ('AL', 'Alabama'),
    ('AK', 'Alaska'),
    ('AZ', 'Arizona'),
    ('AR', 'Arkansas'),
    ('CA', 'California'),
    ('CO', 'Colorado'),
    ('CT', 'Connecticut'),
    ('DE', 'Delaware'),
    ('FL', 'Florida'),
    ('GA', 'Georgia'),
    ('HI', 'Hawaii'),
    ('ID', 'Idaho'),
    ('IL', 'Illinois'),
    ('IN', 'Indiana'),
    ('IA', 'Iowa'),
    ('KS', 'Kansas'),
    ('KY', 'Kentucky'),
    ('LA', 'Louisiana'),
    ('ME', 'Maine'),
    ('MD', 'Maryland'),
    ('MA', 'Massachusetts'),
    ('MI', 'Michigan'),
    ('MN', 'Minnesota'),
    ('MS', 'Mississippi'),
    ('MO', 'Missouri'),
    ('MT', 'Montana'),
    ('NE', 'Nebraska'),
    ('NV', 'Nevada'),
    ('NH', 'New Hampshire'),
    ('NJ', 'New Jersey'),
    ('NM', 'New Mexico'),
    ('NY', 'New York'),
    ('NC', 'North Carolina'),
    ('ND', 'North Dakota'),
    ('OH', 'Ohio'),
    ('OK', 'Oklahoma'),
    ('OR', 'Oregon'),
    ('PA', 'Pennsylvania'),
    ('RI', 'Rhode Island'),
    ('SC', 'South Carolina'),
    ('SD', 'South Dakota'),
    ('TN', 'Tennessee'),
    ('TX', 'Texas'),
    ('UT', 'Utah'),
    ('VT', 'Vermont'),
    ('VA', 'Virginia'),
    ('WA', 'Washington'),
    ('WV', 'West Virginia'),
    ('WI', 'Wisconsin'),
    ('WY', 'Wyoming'),
    ('DC', 'District of Columbia'),
    ('PR', 'Puerto Rico'),
    ('VI', 'Virgin Islands'),
    ('AS', 'American Samoa'),
    ('GU', 'Guam'),
    ('MP', 'Northern Mariana Islands'),
]

# Regional wage adjustments (approximate multipliers based on cost of living)
REGIONAL_ADJUSTMENTS = {
    'AL': 0.87, 'AK': 1.23, 'AZ': 0.95, 'AR': 0.85, 'CA': 1.25,
    'CO': 1.05, 'CT': 1.15, 'DE': 1.02, 'FL': 0.98, 'GA': 0.92,
    'HI': 1.18, 'ID': 0.90, 'IL': 1.02, 'IN': 0.88, 'IA': 0.86,
    'KS': 0.87, 'KY': 0.86, 'LA': 0.88, 'ME': 0.95, 'MD': 1.12,
    'MA': 1.20, 'MI': 0.90, 'MN': 0.98, 'MS': 0.82, 'MO': 0.88,
    'MT': 0.92, 'NE': 0.88, 'NV': 1.00, 'NH': 1.05, 'NJ': 1.18,
    'NY': 1.15, 'NC': 0.90, 'ND': 0.95, 'OH': 0.88, 'OK': 0.86,
    'OR': 1.05, 'PA': 0.95, 'RI': 1.05, 'SC': 0.85, 'SD': 0.85,
    'TN': 0.88, 'TX': 0.95, 'UT': 0.95, 'VT': 1.00, 'VA': 1.05,
    'WA': 1.15, 'WV': 0.83, 'WI': 0.90, 'WY': 0.95, 'DC': 1.20,
    'PR': 0.65, 'VI': 0.75, 'AS': 0.70, 'GU': 0.75, 'MP': 0.75,
}

# Common default rates by state (for unemployment, growth, etc.)
STATE_ECONOMIC_DEFAULTS = {
    'discount_rates': [3.0, 4.0, 5.0],  # Standard forensic rates
    'default_growth_rate': 0.032,       # 3.2% annual wage growth
    'default_inflation_rate': 0.025,    # 2.5% inflation
}

def get_state_choices():
    """Return state choices formatted for HTML select options"""
    return [(abbr, f"{name} ({abbr})") for abbr, name in US_STATES]

def get_state_adjustment(state_abbr):
    """Get regional wage adjustment for a state"""
    return REGIONAL_ADJUSTMENTS.get(state_abbr.upper(), 1.0)

def get_state_name(state_abbr):
    """Get full state name from abbreviation"""
    for abbr, name in US_STATES:
        if abbr == state_abbr.upper():
            return name
    return state_abbr

def validate_state(state_input):
    """Validate and standardize state input (accepts full name or abbreviation)"""
    state_input = state_input.strip().upper()
    
    # Check if it's a valid abbreviation
    for abbr, name in US_STATES:
        if abbr == state_input:
            return abbr
        if name.upper() == state_input:
            return abbr
    
    return None

def get_default_parameters(state_abbr=None):
    """Get default economic parameters, optionally adjusted for state"""
    defaults = STATE_ECONOMIC_DEFAULTS.copy()
    
    if state_abbr:
        adjustment = get_state_adjustment(state_abbr)
        defaults['regional_adjustment'] = adjustment
        defaults['state_name'] = get_state_name(state_abbr)
    
    return defaults
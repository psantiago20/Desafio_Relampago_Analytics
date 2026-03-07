THEMES = {
    "light": {
        "primary": "#1152d4",
        "fill_color": "rgba(17, 82, 212, 0.1)",
        "background": "#f6f6f8",
        "card": "#ffffff",
        "text_main": "#0f172a",
        "text_muted": "#64748b",
        "border": "rgba(17, 82, 212, 0.1)",
        "accent_green": "#10b981",
        "accent_red": "#ef4444",
        "sidebar_bg": "#ffffff",
    },
    "dark": {
        "primary": "#6366f1",  # Vibrant Indigo
        "fill_color": "rgba(99, 102, 241, 0.15)",
        "background": "#0f172a", # Deep Slate
        "card": "#1e293b",       # Slate-800
        "text_main": "#f8fafc",  # Almost white
        "text_muted": "#cbd5e1", # Brightened from 94a3b8 for better legibility
        "border": "rgba(255, 255, 255, 0.1)",
        "accent_green": "#34d399",
        "accent_red": "#f87171",
        "sidebar_bg": "#0f172a",
    }
}

def get_css(theme_name="light"):
    colors = THEMES[theme_name]
    
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

    :root {{
        --primary: {colors['primary']};
        --background: {colors['background']};
        --card: {colors['card']};
        --text-main: {colors['text_main']};
        --text-muted: {colors['text_muted']};
        --border: {colors['border']};
        --accent-green: {colors['accent_green']};
        --accent-red: {colors['accent_red']};
    }}
    
    /* General Fixes */
    .material-symbols-outlined {{
        font-family: 'Material Symbols Outlined' !important;
        font-weight: normal;
        font-style: normal;
        font-size: 24px;
        line-height: 1;
        letter-spacing: normal;
        text-transform: none;
        display: inline-block;
        white-space: nowrap;
        word-wrap: normal;
        direction: ltr;
        -webkit-font-smoothing: antialiased;
        font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 48;
    }}

    html, body, [class*="css"], .stApp {{
        font-family: 'Inter', sans-serif !important;
        background-color: var(--background) !important;
        color: var(--text-main) !important;
    }}

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: {colors['sidebar_bg']} !important;
        border-right: 1px solid var(--border);
    }}

    /* Target only text/label elements in sidebar */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {{
        color: {colors['text_main']} !important;
    }}

    /* Radio Button Labels */
    div[data-testid="stRadio"] [data-testid="stWidgetLabel"] p {{
        color: {colors['text_main']} !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
    }}
    
    label[data-testid="stWidgetLabel"] p {{
        color: {colors['text_main']} !important;
    }}

    /* ===== MULTISELECT TAG TEXT - ALWAYS WHITE ===== */
    /* These rules come AFTER sidebar rules so they win the cascade */
    section[data-testid="stSidebar"] div[data-baseweb="tag"],
    div[data-baseweb="tag"] {{
        background-color: var(--primary) !important;
        color: white !important;
    }}
    section[data-testid="stSidebar"] div[data-baseweb="tag"] span,
    section[data-testid="stSidebar"] div[data-baseweb="tag"] p,
    div[data-baseweb="tag"] span,
    div[data-baseweb="tag"] p {{
        color: white !important;
    }}
    section[data-testid="stSidebar"] div[data-baseweb="tag"] svg,
    div[data-baseweb="tag"] svg {{
        fill: white !important;
    }}

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 1.5rem !important;
        background-color: transparent !important;
        border-bottom: 2px solid var(--border) !important;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        padding: 10px 4px !important;
        color: var(--text-muted) !important;
        background-color: transparent !important;
        font-weight: 600 !important;
    }}

    .stTabs [aria-selected="true"] {{
        color: var(--primary) !important;
        border-bottom: 2px solid var(--primary) !important;
    }}

    /* Custom KPI Cards - EXACT Match to Reference */
    .kpi-card {{
        background-color: var(--card) !important;
        padding: 1.25rem !important;
        border-radius: 0.75rem !important;
        border: 1px solid var(--border) !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
        margin-bottom: 1rem !important;
        display: flex !important;
        flex-direction: column !important;
        gap: 0.75rem !important;
    }}

    .kpi-header {{
        display: flex !important;
        align-items: center !important;
        gap: 0.75rem !important;
    }}

    .kpi-icon {{
        padding: 0.5rem !important;
        background-color: {colors['fill_color']} !important;
        border-radius: 0.5rem !important;
        color: var(--primary) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}

    .kpi-label {{
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        color: var(--text-muted) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }}

    .kpi-value-container {{
        display: flex !important;
        align-items: baseline !important;
        gap: 0.5rem !important;
    }}

    .kpi-value {{
        font-size: 1.75rem !important;
        font-weight: 800 !important;
        color: var(--text-main) !important;
    }}

    .kpi-delta {{
        font-size: 0.85rem !important;
        font-weight: 700 !important;
    }}

    .delta-up {{ color: var(--accent-green) !important; }}
    .delta-down {{ color: var(--accent-red) !important; }}

    /* Hide Streamlit Header/Footer */
    header[data-testid="stHeader"] {{
        background-color: var(--background) !important;
        border-bottom: 1px solid var(--border);
    }}
    
    footer {{ visibility: hidden; }}
    #MainMenu {{ visibility: hidden; }}

    /* Fix Streamlit Info/Warning/Success boxes colors */
    div[data-testid="stAlert"] {{
        background-color: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 0.5rem !important;
    }}
    div[data-testid="stAlert"] p, 
    div[data-testid="stAlert"] li, 
    div[data-testid="stAlert"] span,
    div[data-testid="stAlert"] div {{ 
        color: var(--text-main) !important; 
    }}

    [data-testid="stMetricLabel"] {{ color: var(--text-muted) !important; }}
    [data-testid="stMetricValue"] {{ color: var(--text-main) !important; }}

    /* Fix selection visibility */
    ::selection {{
        background: var(--primary);
        color: white;
    }}
    </style>
    """

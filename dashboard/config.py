COLORS = {
    "primary": "#1A365D",
    "secondary": "#4A5568",
    "accent": "#3182CE",
    "success": "#38A169",
    "warning": "#DD6B20",
    "background": "#F7FAFC",
    "card": "#FFFFFF",
    "border": "#E2E8F0",
    "text_main": "#1A202C",
    "text_muted": "#718096"
}

CSS_STYLE = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"]  {{
    font-family: 'Inter', sans-serif;
    color: {COLORS['text_main']};
}}

.main {{
    background-color: {COLORS['background']};
}}

h1, h2, h3 {{
    font-family: 'Libre Baskerville', serif !important;
    color: {COLORS['primary']} !important;
    letter-spacing: -0.015em;
}}

h1 {{ font-weight: 700 !important; font-size: 2.2rem !important; margin-bottom: 0.2rem !important; }}
h3 {{ font-weight: 700 !important; font-size: 1.4rem !important; margin-top: 1.5rem !important; border-bottom: 1px solid {COLORS['border']}; padding-bottom: 10px; }}

section[data-testid="stSidebar"] {{
    background-color: {COLORS['card']} !important;
    border-right: 1px solid {COLORS['border']};
}}

hr {{
    border-color: {COLORS['border']};
}}

.stTabs [data-baseweb="tab"] {{
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    letter-spacing: 0.02em;
    padding-top: 15px;
}}
</style>
"""

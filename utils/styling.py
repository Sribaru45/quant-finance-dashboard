BG_COLOR = "#0E1117"
SIDEBAR_COLOR = "#1C1C2E"
ACCENT = "#00D4AA"
DANGER = "#FF6B6B"
TEXT_COLOR = "#FFFFFF"
SUBTEXT_COLOR = "#A0AEC0"

GLOBAL_CSS = """
<style>
    /* Main background */
    .stApp {
        background-color: #0E1117;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1C1C2E;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #1C1C2E;
        border: 1px solid #2D2D44;
        border-radius: 8px;
        padding: 12px 16px;
    }

    [data-testid="stMetricValue"] {
        color: #00D4AA;
        font-size: 1.4rem;
        font-weight: 700;
    }

    [data-testid="stMetricLabel"] {
        color: #A0AEC0;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    [data-testid="stMetricDelta"] svg {
        display: none;
    }

    /* Headers */
    h1, h2, h3 {
        color: #FFFFFF;
        font-family: 'Courier New', monospace;
    }

    /* Info/warning/error boxes */
    .stAlert {
        border-radius: 6px;
    }

    /* Buttons */
    .stButton > button {
        background-color: #00D4AA;
        color: #0E1117;
        border: none;
        font-weight: 600;
        border-radius: 6px;
    }
    .stButton > button:hover {
        background-color: #00b891;
        color: #0E1117;
    }

    /* Selectbox / inputs */
    .stSelectbox label, .stSlider label, .stNumberInput label, .stTextInput label {
        color: #A0AEC0;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    /* Divider */
    hr {
        border-color: #2D2D44;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Sidebar footer */
    .sidebar-footer {
        position: fixed;
        bottom: 1rem;
        left: 0;
        width: 16rem;
        padding: 0.75rem 1rem;
        color: #A0AEC0;
        font-size: 0.75rem;
        border-top: 1px solid #2D2D44;
    }
    .sidebar-footer a {
        color: #00D4AA;
        text-decoration: none;
    }
    .sidebar-footer a:hover {
        text-decoration: underline;
    }

    /* Module header banner */
    .module-header {
        background: linear-gradient(90deg, #1C1C2E 0%, #0E1117 100%);
        border-left: 4px solid #00D4AA;
        padding: 1rem 1.5rem;
        margin-bottom: 1.5rem;
        border-radius: 0 6px 6px 0;
    }
    .module-header h1 {
        margin: 0;
        font-size: 1.6rem;
        color: #FFFFFF;
    }
    .module-header p {
        margin: 0.25rem 0 0 0;
        color: #A0AEC0;
        font-size: 0.9rem;
    }

    /* Landing page module card */
    .module-card {
        background-color: #1C1C2E;
        border: 1px solid #2D2D44;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
        transition: border-color 0.2s;
    }
    .module-card:hover {
        border-color: #00D4AA;
    }
    .module-card h4 {
        color: #00D4AA;
        margin: 0 0 0.25rem 0;
        font-size: 0.95rem;
    }
    .module-card p {
        color: #A0AEC0;
        margin: 0;
        font-size: 0.82rem;
    }

    /* Error card */
    .error-card {
        background-color: #2D1C1C;
        border: 1px solid #FF6B6B;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        color: #FF6B6B;
    }
</style>
"""

PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="#0E1117",
    plot_bgcolor="#0E1117",
    font=dict(color="#FFFFFF", family="Courier New"),
    title_font=dict(color="#FFFFFF", size=16),
    legend=dict(bgcolor="#1C1C2E", bordercolor="#2D2D44", borderwidth=1),
    margin=dict(l=40, r=20, t=50, b=40),
)

def apply_global_css(st):
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

def module_header(st, icon, title, description):
    st.markdown(
        f'<div class="module-header"><h1>{icon} {title}</h1><p>{description}</p></div>',
        unsafe_allow_html=True,
    )

def error_card(st, message, suggestion=""):
    st.markdown(
        f'<div class="error-card"><strong>Error:</strong> {message}'
        + (f'<br><span style="color:#A0AEC0">{suggestion}</span>' if suggestion else "")
        + "</div>",
        unsafe_allow_html=True,
    )

def sidebar_footer(st):
    st.sidebar.markdown(
        '<div class="sidebar-footer">'
        'Built by <strong>Sriram Bharadwaj</strong><br>'
        '<a href="https://github.com/Sribaru45" target="_blank">GitHub</a> &nbsp;|&nbsp; '
        '<a href="https://linkedin.com/in/sriram-bharadwaj" target="_blank">LinkedIn</a>'
        "</div>",
        unsafe_allow_html=True,
    )

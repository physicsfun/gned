import json
from collections import defaultdict
import streamlit as st

st.set_page_config(layout="wide")

st.markdown("""
<style>
/* General spacing */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}

/* Section headings */
h1, h2, h3 {
    letter-spacing: -0.02em;
}

/* Pathway card look */
.pathway-card {
    border: 1px solid rgba(120,120,120,0.25);
    border-radius: 16px;
    padding: 1rem 1rem 0.75rem 1rem;
    background: linear-gradient(180deg, rgba(245,245,250,0.95), rgba(235,238,245,0.95));
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    min-height: 150px;
    margin-bottom: 0.75rem;
}

.pathway-title {
    font-size: 1.05rem;
    font-weight: 700;
    margin-bottom: 0.25rem;
}

.pathway-strength {
    display: inline-block;
    font-size: 0.8rem;
    font-weight: 600;
    padding: 0.2rem 0.55rem;
    border-radius: 999px;
    background: rgba(90, 110, 200, 0.12);
    margin-bottom: 0.6rem;
}

.pathway-description {
    font-size: 0.92rem;
    line-height: 1.35;
    color: #444;
}

/* Recommendation cards */
.rec-card {
    border: 1px solid rgba(120,120,120,0.22);
    border-radius: 18px;
    padding: 1rem 1rem 0.8rem 1rem;
    background: white;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    margin-bottom: 1rem;
}

.rec-code {
    font-size: 1.05rem;
    font-weight: 700;
    margin-bottom: 0.2rem;
}

.rec-meta {
    font-size: 0.88rem;
    color: #666;
    margin-bottom: 0.5rem;
}

.rec-why {
    font-size: 0.9rem;
    font-weight: 600;
    margin-top: 0.5rem;
}

.rec-desc {
    font-size: 0.9rem;
    color: #444;
    line-height: 1.35;
    margin-top: 0.45rem;
}

/* Progress box */
.progress-card {
    border: 1px solid rgba(120,120,120,0.2);
    border-radius: 14px;
    padding: 0.9rem 1rem;
    background: rgba(248,249,252,0.9);
    margin-bottom: 1rem;
}

/* Sidebar header spacing */
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ==========================================================
# LOAD DATA
# ==========================================================

@st.cache_data
def load_courses():
    with open("mru_all_courses_enriched.json", "r", encoding="utf-8") as f:
        return json.load(f)

courses = load_courses()

for c in courses:
    c["label"] = f"{c['code']} — {c['title']}"
    c["level"] = c.get("level_guess", "Unknown")
    c["area"] = c.get("area_guess", "Unknown")
    c["methods"] = c.get("methods", [])
    c["pathways"] = c.get("pathway_affinities", [])
    c["qr_candidate"] = c.get("qr_candidate", False)
    c["communication_candidate"] = c.get("communication_candidate", False)

lookup = {c["label"]: c for c in courses}

# ==========================================================
# PATHWAYS
# ==========================================================

PATHWAYS = {
    "Identity, Culture & Meaning": {
        "methods": ["Interpretation", "Normative Reasoning", "Critical Reflection"],
        "icon": "🧠",
    },
    "Justice, Community & Citizenship": {
        "methods": ["Empirical Social Analysis", "Institutional Analysis"],
        "icon": "⚖️",
    },
    "Data, Evidence & Decision Making": {
        "methods": ["Quantitative Reasoning", "Measurement & Modelling"],
        "icon": "📊",
    },
    "Environment & Sustainability": {
        "methods": ["Hypothesis Testing", "Measurement & Modelling"],
        "icon": "🌿",
    },
    "Communication & Expression": {
        "methods": ["Writing & Rhetoric", "Argumentation"],
        "icon": "✍️",
    },
}

# ==========================================================
# REQUIREMENTS
# ==========================================================

REQUIREMENTS = {
    "Communication": 1,
    "Area I Junior": 1,
    "Area I Senior": 1,
    "Area II Junior": 1,
    "Area II Senior": 1,
    "Quantitative Reasoning": 1,
    "Area III Junior": 1,
    "Area III Senior": 1,
}

AREA_OPTIONS = [
    "Area I — Domains of Meaning & Value",
    "Area II — Human Systems & Institutions",
    "Area III — Formal & Natural Systems",
    "Unknown",
]

LEVEL_OPTIONS = ["Junior", "Senior", "Unknown"]

# ==========================================================
# SESSION STATE
# ==========================================================

if "selected" not in st.session_state:
    st.session_state.selected = []

if "planned" not in st.session_state:
    st.session_state.planned = []

if "chosen_pathway" not in st.session_state:
    st.session_state.chosen_pathway = None

# ==========================================================
# HELPERS
# ==========================================================

def method_profile(selected):
    prof = defaultdict(float)
    for c in selected:
        for m in c["methods"]:
            prof[m] += 1
    return prof

def pathway_scores(profile):
    scores = []
    for name, info in PATHWAYS.items():
        score = sum(profile.get(m, 0) for m in info["methods"])
        scores.append((name, score))
    return sorted(scores, key=lambda x: -x[1])

def requirement_slots(c):
    slots = []
    if c["communication_candidate"]:
        slots.append("Communication")
    if c["qr_candidate"]:
        slots.append("Quantitative Reasoning")
    if c["area"].startswith("Area I"):
        slots.append(f"Area I {c['level']}")
    if c["area"].startswith("Area II"):
        slots.append(f"Area II {c['level']}")
    if c["area"].startswith("Area III"):
        slots.append(f"Area III {c['level']}")
    return slots

def progress(courses):
    filled = {k: 0 for k in REQUIREMENTS}
    for c in courses:
        for slot in requirement_slots(c):
            if slot in filled and filled[slot] < REQUIREMENTS[slot]:
                filled[slot] += 1
    return filled

def recommend(selected, pathway):
    profile = method_profile(selected)
    target = set(PATHWAYS[pathway]["methods"])

    recs = []
    for c in courses:
        if c in selected:
            continue

        score = 0
        overlap = len(set(c["methods"]) & target)
        score += 3 * overlap

        if pathway in c["pathways"]:
            score += 5

        recs.append((score, c))

    return sorted(recs, key=lambda x: -x[0])[:10]

def sort_courses(c):
    return (c["area"], c["level"], c["subject"], c["number"], c["title"])

# ==========================================================
# SIDEBAR
# ==========================================================

st.sidebar.header("Build profile")

with st.sidebar.expander("Advanced course filters", expanded=True):
    selected_area_filters = st.multiselect(
        "Area",
        options=AREA_OPTIONS,
        default=AREA_OPTIONS,
    )

    selected_level_filters = st.multiselect(
        "Level",
        options=LEVEL_OPTIONS,
        default=LEVEL_OPTIONS,
    )

    qr_filter = st.selectbox(
        "Quantitative Reasoning candidate",
        ["All", "QR only", "Non-QR only"],
    )

    comm_filter = st.selectbox(
        "Communication candidate",
        ["All", "Communication only", "Non-communication only"],
    )

search = st.sidebar.text_input("Search courses")

filtered = []
for c in courses:
    if c["area"] not in selected_area_filters:
        continue
    if c["level"] not in selected_level_filters:
        continue

    if qr_filter == "QR only" and not c.get("qr_candidate", False):
        continue
    if qr_filter == "Non-QR only" and c.get("qr_candidate", False):
        continue

    if comm_filter == "Communication only" and not c.get("communication_candidate", False):
        continue
    if comm_filter == "Non-communication only" and c.get("communication_candidate", False):
        continue

    if search.strip():
        blob = f"{c['label']} {c.get('description', '')}".lower()
        if search.lower() not in blob:
            continue

    filtered.append(c)

filtered = sorted(filtered, key=sort_courses)

st.sidebar.caption(f"Showing {len(filtered)} matching courses")

labels = [c["label"] for c in filtered[:300]]

add = st.sidebar.multiselect("Add completed courses", labels)

if st.sidebar.button("Add"):
    for l in add:
        if l not in st.session_state.selected:
            st.session_state.selected.append(l)
    st.rerun()

with st.sidebar.expander("Preview matching courses"):
    for c in filtered[:20]:
        st.write(f"**{c['code']}** — {c['title']}  \n{c['area']} | {c['level']}")

selected_courses = [lookup[l] for l in st.session_state.selected]

if st.sidebar.button("Clear all completed courses"):
    st.session_state.selected = []
    st.session_state.planned = []
    st.rerun()

# ==========================================================
# MAIN UI
# ==========================================================

st.title("Liberal Education Pathway Planner")
st.info("Add completed courses in the sidebar, then explore pathways and build a plan.")

# ----------------------------------------------------------
# 1. PROFILE
# ----------------------------------------------------------

st.header("1. Your profile")

if not selected_courses:
    st.info("Add some completed courses to begin.")
else:
    for c in selected_courses:
        row1, row2 = st.columns([8, 1])
        with row1:
            st.write(f"- **{c['label']}**  \n{c['area']} | {c['level']}")
        with row2:
            if st.button("Remove", key=f"remove_{c['label']}"):
                st.session_state.selected.remove(c["label"])
                if c["label"] in st.session_state.planned:
                    st.session_state.planned.remove(c["label"])
                st.rerun()

# ----------------------------------------------------------
# 2. PATHWAYS
# ----------------------------------------------------------

st.header("2. Your emerging directions")

profile = method_profile(selected_courses)
scores = pathway_scores(profile)

if scores:
    cols = st.columns(len(scores[:5]))

    for i, (name, score) in enumerate(scores[:5]):
        with cols[i]:
            icon = PATHWAYS[name]["icon"]
            label = "Strong" if score > 5 else "Moderate" if score > 2 else "Emerging"

            st.markdown(
                f"""
                <div class="pathway-card">
                    <div class="pathway-title">{icon} {name}</div>
                    <div class="pathway-strength">{label}</div>
                    <div class="pathway-description">
                        Focuses on: {", ".join(PATHWAYS[name]["methods"][:3])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(f"Explore {name}", key=f"pathway_{name}"):
                st.session_state.chosen_pathway = name

if not st.session_state.chosen_pathway and scores:
    st.session_state.chosen_pathway = scores[0][0]

# ----------------------------------------------------------
# 3. RECOMMENDATIONS
# ----------------------------------------------------------

if st.session_state.chosen_pathway:
    pathway = st.session_state.chosen_pathway
    st.header(f"3. Build: {pathway}")

    recs = recommend(selected_courses, pathway)

    for score, c in recs:
        why = []
        if pathway in c["pathways"]:
            why.append("matches this pathway")
        if c["qr_candidate"]:
            why.append("QR candidate")
        if c["communication_candidate"]:
            why.append("Communication candidate")

        desc = c.get("description", "")
        short_desc = desc[:260] + ("..." if len(desc) > 260 else "")

        st.markdown(
            f"""
            <div class="rec-card">
                <div class="rec-code">{c['code']} — {c['title']}</div>
                <div class="rec-meta">{c['area']} | {c['level']} | Score: {score}</div>
                <div><strong>Methods:</strong> {", ".join(c["methods"])}</div>
                <div class="rec-why">Why suggested: {", ".join(why) if why else "general fit"}</div>
                <div class="rec-desc">{short_desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if c["label"] not in st.session_state.planned:
            if st.button("Add to plan", key=f"plan_{c['label']}"):
                st.session_state.planned.append(c["label"])
                st.rerun()
        else:
            st.success("Already in planned build")

# ----------------------------------------------------------
# 4. PLAN + REQUIREMENTS
# ----------------------------------------------------------

st.header("4. Your plan")

planned_courses = [lookup[l] for l in st.session_state.planned]

st.subheader("Progress")
st.markdown('<div class="progress-card">', unsafe_allow_html=True)

prog = progress(selected_courses + planned_courses)

for req, val in prog.items():
    needed = REQUIREMENTS[req]
    mark = "✅" if val >= needed else "⬜"
    st.write(f"{mark} {req}: {val}/{needed}")

st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------
# 5. FACULTY BROWSER
# ----------------------------------------------------------

with st.expander("Faculty/testing browser"):
    st.write(f"Showing {len(filtered)} currently filtered courses.")

    for c in filtered[:100]:
        st.write(
            f"**{c['label']}**  \n"
            f"{c['area']} | {c['level']}  \n"
            f"Methods: {', '.join(c['methods'])}  \n"
            f"Pathways: {', '.join(c['pathways'])}"
        )

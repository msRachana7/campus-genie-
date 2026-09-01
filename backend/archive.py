from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional


router = APIRouter(
    prefix="/api/archive",
    tags=["Time Capsule"]
)


# ============================================================
# PAGE-WIDE STATIC CONTENT
# ============================================================

PAGE_CONFIG = {
    "page_title": "Time Capsule",
    "archive_name": "BMSCE Archives",

    "hero": {
        "eyebrow": "TIME CAPSULE · BMSCE ARCHIVES",
        "title": "Campus has a",
        "highlight": "long memory.",
        "description": (
            "Ask how the culture evolved. Explore old events, alumni paths, "
            "and the ideas that were already in the air three years ago."
        ),
        "button_text": "Explore with Genie",
        "established_year": "1946"
    },

    "browse_section": {
        "eyebrow": "BROWSE THE YEARS",
        "title": "Choose a thread to follow"
    },

    "archive_inspiration": (
        "Public campus-life references from BMSCE Life at BMSCE."
    )
}


# ============================================================
# HARDCODED ARCHIVE CONTENT
# ============================================================

ARCHIVE_DATA = {

    # --------------------------------------------------------
    # 2026
    # --------------------------------------------------------
    "2026": {
        "year": "2026",

        "campus_life": {
            "category": "CAMPUS LIFE",
            "year": "2026",
            "title": "A campus that moves in real time.",
            "description": (
                "Clubs, classrooms and student communities blur into one "
                "shared rhythm — fast, collaborative and always one good "
                "idea away from becoming an event."
            ),
            "button_text": "Open memory"
        },

        "hackathons": {
            "category": "HACKATHONS",
            "year": "2026",
            "title": "From first prototype to final pitch.",
            "description": (
                "Hackathon teams gather around rough sketches, working demos "
                "and late-night problem solving, turning curiosity into "
                "something others can try."
            ),
            "button_text": "Open memory"
        },

        "archive_question": {
            "label": "ASK THE ARCHIVE",
            "question": (
                "What will today's experiments become when the next "
                "generation looks back?"
            ),
            "button_text": "Ask Genie"
        }
    },

    # --------------------------------------------------------
    # 2024
    # --------------------------------------------------------
    "2024": {
        "year": "2024",

        "campus_life": {
            "category": "CAMPUS LIFE",
            "year": "2024",
            "title": "The quad became a meeting point.",
            "description": (
                "Between lectures and club hours, the campus carried a steady "
                "exchange of conversations, collaborations and small moments "
                "of belonging."
            ),
            "button_text": "Open memory"
        },

        "hackathons": {
            "category": "HACKATHONS",
            "year": "2024",
            "title": "Ideas found their teammates.",
            "description": (
                "Student builders moved from a shared problem statement to "
                "practical prototypes, learning that the strongest solutions "
                "rarely happen alone."
            ),
            "button_text": "Open memory"
        },

        "archive_question": {
            "label": "ASK THE ARCHIVE",
            "question": (
                "Which meeting, message or chance encounter quietly changed "
                "someone's path?"
            ),
            "button_text": "Ask Genie"
        }
    },

    # --------------------------------------------------------
    # 2023
    # This is the year displayed in your screenshot
    # --------------------------------------------------------
    "2023": {
        "year": "2023",

        "campus_life": {
            "category": "CAMPUS LIFE",
            "year": "2023",
            "title": "When the quad became a stage.",
            "description": (
                "From club showcases to late-evening rehearsals, "
                "student communities turned ordinary campus spaces "
                "into places to perform, meet and collaborate."
            ),
            "button_text": "Open memory"
        },

        "hackathons": {
            "category": "HACKATHONS",
            "year": "2023",
            "title": "Before the pitch decks.",
            "description": (
                "Teams gathered around ideas, laptops and unfinished "
                "prototypes, testing solutions before they ever became "
                "formal presentations."
            ),
            "button_text": "Open memory"
        },

        "archive_question": {
            "label": "ASK THE ARCHIVE",
            "question": "What did students care about back then?",
            "button_text": "Ask Genie"
        }
    },

    # --------------------------------------------------------
    # 2020
    # --------------------------------------------------------
    "2020": {
        "year": "2020",

        "campus_life": {
            "category": "CAMPUS LIFE",
            "year": "2020",
            "title": "Campus, remembered from a distance.",
            "description": (
                "When routines changed, students kept campus life alive "
                "through messages, shared resources and the familiar hope "
                "of meeting again in person."
            ),
            "button_text": "Open memory"
        },

        "hackathons": {
            "category": "HACKATHONS",
            "year": "2020",
            "title": "Building through uncertainty.",
            "description": (
                "Hackathon energy travelled through screens as teams learned "
                "to test ideas, divide work and keep creating even when "
                "the usual spaces were closed."
            ),
            "button_text": "Open memory"
        },

        "archive_question": {
            "label": "ASK THE ARCHIVE",
            "question": (
                "How did students keep the feeling of campus alive when "
                "they could not gather there?"
            ),
            "button_text": "Ask Genie"
        }
    },

    # --------------------------------------------------------
    # 2016
    # --------------------------------------------------------
    "2016": {
        "year": "2016",

        "campus_life": {
            "category": "CAMPUS LIFE",
            "year": "2016",
            "title": "When the quad became a stage.",
            "description": (
                "Club showcases, rehearsals, conversations between classes "
                "and everyday student traditions gave the campus its warm, "
                "unmistakable rhythm."
            ),
            "button_text": "Open memory"
        },

        "hackathons": {
            "category": "HACKATHONS",
            "year": "2016",
            "title": "Before the pitch decks.",
            "description": (
                "Early teams gathered around practical problems and "
                "ambitious ideas, discovering that a working prototype "
                "often begins with a simple conversation."
            ),
            "button_text": "Open memory"
        },

        "archive_question": {
            "label": "ASK THE ARCHIVE",
            "question": (
                "What did students care about then, and which of those "
                "hopes are still visible today?"
            ),
            "button_text": "Ask Genie"
        }
    }
}


# ============================================================
# SIMPLE HARDCODED "ASK ARCHIVE" REQUEST MODEL
# ============================================================

class ArchiveQuestion(BaseModel):
    question: str
    year: Optional[str] = None


# ============================================================
# HELPER FUNCTION
# ============================================================

def get_year_data(year: str):
    data = ARCHIVE_DATA.get(year)

    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"No archive entry found for {year}"
        )

    return data


# ============================================================
# GET /api/archive
#
# Loads everything needed when Time Capsule page first opens.
# ============================================================

@router.get("")
def get_archive_home():
    years = list(ARCHIVE_DATA.keys())

    return {
        "page": PAGE_CONFIG,
        "default_year": "2023",
        "available_years": years,
        "selected_year": ARCHIVE_DATA["2023"]
    }


# ============================================================
# GET /api/archive/years
#
# Returns year buttons.
# ============================================================

@router.get("/years")
def get_archive_years():
    return {
        "available_years": list(ARCHIVE_DATA.keys()),
        "default_year": "2023"
    }


# ============================================================
# GET /api/archive/all
#
# Returns every hardcoded Time Capsule record.
# ============================================================

@router.get("/all")
def get_all_archive_data():
    return {
        "count": len(ARCHIVE_DATA),
        "archives": ARCHIVE_DATA
    }


# ============================================================
# GET /api/archive/search?q=hackathon
#
# Optional simple search.
# ============================================================

@router.get("/search")
def search_archive(
    q: str = Query(..., min_length=1)
):
    query = q.lower().strip()

    matches = []

    for year, data in ARCHIVE_DATA.items():

        campus = data["campus_life"]
        hackathon = data["hackathons"]
        archive_question = data["archive_question"]

        campus_text = (
            campus["title"] + " " +
            campus["description"]
        ).lower()

        hackathon_text = (
            hackathon["title"] + " " +
            hackathon["description"]
        ).lower()

        question_text = archive_question["question"].lower()

        if query in campus_text:
            matches.append({
                "year": year,
                "type": "campus_life",
                "data": campus
            })

        if query in hackathon_text:
            matches.append({
                "year": year,
                "type": "hackathons",
                "data": hackathon
            })

        if query in question_text:
            matches.append({
                "year": year,
                "type": "archive_question",
                "data": archive_question
            })

    return {
        "query": q,
        "count": len(matches),
        "results": matches
    }


# ============================================================
# POST /api/archive/ask
#
# Fake/hardcoded archive assistant.
# Useful for demoing the "Ask Genie" card.
# ============================================================

@router.post("/ask")
def ask_archive(request: ArchiveQuestion):

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    q = question.lower()

    year = request.year

    if year and year not in ARCHIVE_DATA:
        raise HTTPException(
            status_code=404,
            detail=f"No archive entry found for {year}"
        )

    # --------------------------------------------------------
    # YEAR-SPECIFIC QUESTION
    # --------------------------------------------------------

    if year:
        data = ARCHIVE_DATA[year]

        if "hackathon" in q or "build" in q or "prototype" in q:
            answer = (
                f"In {year}, {data['hackathons']['description']}"
            )

        elif (
            "campus" in q
            or "club" in q
            or "student" in q
            or "culture" in q
        ):
            answer = (
                f"In {year}, {data['campus_life']['description']}"
            )

        else:
            answer = (
                f"The {year} archive remembers this period as: "
                f"'{data['campus_life']['title']}' "
                f"{data['campus_life']['description']}"
            )

        return {
            "question": question,
            "year": year,
            "answer": answer,
            "source": "hardcoded_archive"
        }

    # --------------------------------------------------------
    # GENERAL QUESTIONS
    # --------------------------------------------------------

    if "2023" in q:
        data = ARCHIVE_DATA["2023"]

        answer = (
            data["campus_life"]["description"]
            + " "
            + data["hackathons"]["description"]
        )

    elif "2024" in q:
        data = ARCHIVE_DATA["2024"]

        answer = (
            data["campus_life"]["description"]
            + " "
            + data["hackathons"]["description"]
        )

    elif "2020" in q:
        data = ARCHIVE_DATA["2020"]

        answer = (
            data["campus_life"]["description"]
            + " "
            + data["hackathons"]["description"]
        )

    elif "2016" in q:
        data = ARCHIVE_DATA["2016"]

        answer = (
            data["campus_life"]["description"]
            + " "
            + data["hackathons"]["description"]
        )

    elif "hackathon" in q:
        answer = (
            "Across the archive, hackathons evolved around the same core "
            "pattern: students gathering around practical problems, forming "
            "teams, building prototypes and gradually turning ideas into "
            "something they could demonstrate."
        )

    elif "club" in q or "culture" in q:
        answer = (
            "Campus culture repeatedly grew around clubs, shared spaces, "
            "student conversations, showcases and informal collaboration."
        )

    elif "care" in q:
        answer = (
            "The archive suggests students repeatedly cared about community, "
            "building things together, finding collaborators and creating "
            "spaces where ideas could become projects."
        )

    else:
        answer = (
            "The Time Capsule currently contains memories from "
            + ", ".join(ARCHIVE_DATA.keys())
            + ". Try asking about campus life, clubs, hackathons or a "
              "specific year."
        )

    return {
        "question": question,
        "year": None,
        "answer": answer,
        "source": "hardcoded_archive"
    }


# ============================================================
# GET /api/archive/{year}
#
# IMPORTANT:
# Keep this BELOW /years, /all and /search.
# Otherwise FastAPI could treat words such as "search" as a year.
# ============================================================

@router.get("/{year}")
def get_archive_year(year: str):
    return get_year_data(year)


# ============================================================
# GET /api/archive/{year}/campus-life
# ============================================================

@router.get("/{year}/campus-life")
def get_campus_life(year: str):
    data = get_year_data(year)

    return {
        "year": year,
        "type": "campus_life",
        "content": data["campus_life"]
    }


# ============================================================
# GET /api/archive/{year}/hackathons
# ============================================================

@router.get("/{year}/hackathons")
def get_hackathons(year: str):
    data = get_year_data(year)

    return {
        "year": year,
        "type": "hackathons",
        "content": data["hackathons"]
    }


# ============================================================
# GET /api/archive/{year}/question
# ============================================================

@router.get("/{year}/question")
def get_archive_question(year: str):
    data = get_year_data(year)

    return {
        "year": year,
        "type": "archive_question",
        "content": data["archive_question"]
    }
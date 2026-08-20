import streamlit as st
import pandas as pd
import json
import re
from google import genai
from google.genai import types


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Aesthetic Book Matchmaker",
    page_icon="📚",
    layout="wide"
)


# =========================================================
# SESSION STATE
# =========================================================

if "results" not in st.session_state:
    st.session_state.results = None

if "history" not in st.session_state:
    st.session_state.history = []


# =========================================================
# GEMINI CLIENT
# =========================================================

@st.cache_resource
def get_client():

    return genai.Client(
        api_key=st.secrets["API_KEY"]
    )


client = get_client()


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are an expert literary AI called Aesthetic Book Matchmaker.

Your purpose is to understand books and reading aesthetics.

You can analyze:

1. Text descriptions
2. Images
3. Audio descriptions
4. Book cover photographs
5. Moodboards and aesthetic photographs

IMPORTANT:

If the uploaded image appears to contain a recognizable book cover,
try to identify the book title and author.

If the image is an aesthetic photograph or moodboard rather than
a book cover, do NOT pretend that it is a book cover.
Instead, analyze the visual aesthetic and recommend books.

If audio is provided, understand the user's spoken description.

Never invent a book title or author.

When recommending books, consider:

- atmosphere
- emotional tone
- setting
- themes
- visual aesthetic
- pacing
- season
- weather
- character energy
- writing style
- overall reading experience

The recommendation should NOT be based only on genre.

Return valid JSON only.
"""


# =========================================================
# AI FUNCTION
# =========================================================

def analyze_inputs(
    text,
    image_bytes=None,
    image_type=None,
    audio_bytes=None,
    audio_type=None
):

    prompt = f"""
The user provided this description:

{text}

Analyze all available inputs.

There are two possible situations.

CASE 1:
The image is a BOOK COVER.

Try to identify:
- book title
- author
- whether identification is confident

Then provide:
- identified book
- author
- short description
- aesthetic
- similar books

CASE 2:
The image is NOT a book cover.

Analyze the visual aesthetic.

For the user's requested aesthetic, recommend exactly
3 books.

If audio is provided, use the spoken description as additional
context.

Return exactly this JSON structure:

{{
    "input_type": "book_cover / aesthetic / text_only / mixed",

    "identified_book": {{
        "title": "",
        "author": "",
        "confidence": 0,
        "description": ""
    }},

    "aesthetic_analysis": {{
        "mood": "",
        "atmosphere": "",
        "setting": "",
        "themes": [],
        "visual_style": ""
    }},

    "recommendations": [
        {{
            "title": "",
            "author": "",
            "match_score": 0,
            "reason": "",
            "mood": "",
            "tags": []
        }},
        {{
            "title": "",
            "author": "",
            "match_score": 0,
            "reason": "",
            "mood": "",
            "tags": []
        }},
        {{
            "title": "",
            "author": "",
            "match_score": 0,
            "reason": "",
            "mood": "",
            "tags": []
        }}
    ]
}}
"""

    contents = [prompt]

    # -----------------------------------------------------
    # IMAGE
    # -----------------------------------------------------

    if image_bytes:

        contents.append(
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=image_type
            )
        )

        contents.append(
            """
            Examine this image carefully.

            If it is a book cover, identify the book.

            If it is an aesthetic image, analyze:
            colors, lighting, architecture, objects,
            clothing, environment, weather and atmosphere.
            """
        )

    # -----------------------------------------------------
    # AUDIO
    # -----------------------------------------------------

    if audio_bytes:

        contents.append(
            types.Part.from_bytes(
                data=audio_bytes,
                mime_type=audio_type
            )
        )

        contents.append(
            """
            Listen to the audio and understand the user's
            requested reading mood or book description.
            """
        )

    # -----------------------------------------------------
    # GEMINI
    # -----------------------------------------------------

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.3
        )
    )

    result = response.text

    # Remove markdown code fences

    result = re.sub(
        r"```json",
        "",
        result
    )

    result = re.sub(
        r"```",
        "",
        result
    )

    result = result.strip()

    return json.loads(result)


# =========================================================
# HEADER
# =========================================================

st.title("📚 Aesthetic Book Matchmaker")

st.markdown(
    """
### Find a book based on your **vibe**, not just your genre.

Describe your mood, upload an aesthetic photograph,
upload a book cover, or tell us your vibe through voice.
"""
)

st.divider()


# =========================================================
# INPUT SECTION
# =========================================================

st.header("✨ Tell Us What You're Looking For")


# ---------------------------------------------------------
# TEXT
# ---------------------------------------------------------

text = st.text_area(
    "✍️ Describe your book vibe",
    placeholder=(
        "Example: Dark academia in the rain, "
        "old libraries, candlelight, mystery, "
        "loneliness and intellectual conversations..."
    ),
    height=130
)


# =========================================================
# IMAGE + AUDIO
# =========================================================

image_col, audio_col = st.columns(2)


# ---------------------------------------------------------
# IMAGE
# ---------------------------------------------------------

with image_col:

    st.subheader("📸 Photo")

    image_option = st.radio(
        "Choose image input",
        [
            "Upload Image",
            "Take Photo"
        ],
        horizontal=True
    )

    uploaded_image = None

    if image_option == "Upload Image":

        uploaded_image = st.file_uploader(
            "Upload a book cover or aesthetic image",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp"
            ]
        )

    else:

        uploaded_image = st.camera_input(
            "Take a photo"
        )


# ---------------------------------------------------------
# AUDIO
# ---------------------------------------------------------

with audio_col:

    st.subheader("🎤 Voice")

    audio_option = st.radio(
        "Choose audio input",
        [
            "Upload Audio",
            "Record Voice"
        ],
        horizontal=True
    )

    uploaded_audio = None

    if audio_option == "Upload Audio":

        uploaded_audio = st.file_uploader(
            "Upload your book description",
            type=[
                "wav",
                "mp3",
                "m4a",
                "ogg"
            ]
        )

    else:

        uploaded_audio = st.audio_input(
            "Record your book vibe"
        )


# =========================================================
# PREVIEW
# =========================================================

if uploaded_image:

    st.success("📸 Image ready.")

    st.image(
        uploaded_image,
        width=300
    )


if uploaded_audio:

    st.success("🎤 Audio ready.")

    st.audio(
        uploaded_audio
    )


# =========================================================
# SUBMISSION
# =========================================================

st.divider()

submit = st.button(
    "🔮 FIND MY BOOK",
    type="primary",
    use_container_width=True
)


# =========================================================
# SUBMIT ACTION
# =========================================================

if submit:

    if (
        not text.strip()
        and uploaded_image is None
        and uploaded_audio is None
    ):

        st.warning(
            "Please provide at least one input: "
            "text, photo, or audio."
        )

    else:

        try:

            with st.spinner(
                "🤖 Gemini is analyzing your reading vibe..."
            ):

                # -----------------------------------------
                # IMAGE DATA
                # -----------------------------------------

                image_bytes = None
                image_type = None

                if uploaded_image:

                    image_bytes = (
                        uploaded_image.getvalue()
                    )

                    image_type = getattr(
                        uploaded_image,
                        "type",
                        "image/jpeg"
                    )

                # -----------------------------------------
                # AUDIO DATA
                # -----------------------------------------

                audio_bytes = None
                audio_type = None

                if uploaded_audio:

                    audio_bytes = (
                        uploaded_audio.getvalue()
                    )

                    audio_type = getattr(
                        uploaded_audio,
                        "type",
                        "audio/wav"
                    )

                # -----------------------------------------
                # GEMINI
                # -----------------------------------------

                result = analyze_inputs(
                    text=text,
                    image_bytes=image_bytes,
                    image_type=image_type,
                    audio_bytes=audio_bytes,
                    audio_type=audio_type
                )

                st.session_state.results = result

                # History

                st.session_state.history.append(
                    {
                        "Input": text[:50],
                        "Type": result.get(
                            "input_type",
                            "Unknown"
                        ),
                        "Books": 3
                    }
                )

            st.success(
                "✨ Analysis complete!"
            )

        except Exception as e:

            st.error(
                f"Something went wrong: {e}"
            )


# =========================================================
# RESULTS
# =========================================================

if st.session_state.results:

    result = st.session_state.results

    st.divider()

    st.header("🔮 AI Analysis")


    # =====================================================
    # INPUT TYPE
    # =====================================================

    st.info(
        f"Detected input type: "
        f"**{result.get('input_type', 'Unknown')}**"
    )


    # =====================================================
    # IDENTIFIED BOOK
    # =====================================================

    identified = result.get(
        "identified_book",
        {}
    )

    if identified.get("title"):

        st.header("📖 Book Found")

        book_col1, book_col2 = st.columns(
            [1, 3]
        )

        with book_col1:

            st.metric(
                "AI Confidence",
                f"{identified.get('confidence', 0)}%"
            )

        with book_col2:

            st.subheader(
                identified.get(
                    "title",
                    "Unknown Book"
                )
            )

            st.write(
                f"**Author:** "
                f"{identified.get('author', 'Unknown')}"
            )

            st.write(
                identified.get(
                    "description",
                    ""
                )
            )


    # =====================================================
    # AESTHETIC ANALYSIS
    # =====================================================

    analysis = result.get(
        "aesthetic_analysis",
        {}
    )

    st.header("🎨 Aesthetic Analysis")

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "🌙 Mood",
            analysis.get(
                "mood",
                "Unknown"
            )
        )

    with c2:

        st.metric(
            "🏛️ Atmosphere",
            analysis.get(
                "atmosphere",
                "Unknown"
            )
        )

    with c3:

        st.metric(
            "📍 Setting",
            analysis.get(
                "setting",
                "Unknown"
            )
        )


    with st.expander(
        "View detailed aesthetic analysis",
        expanded=True
    ):

        st.write(
            "**Visual Style:**",
            analysis.get(
                "visual_style",
                "Not available"
            )
        )

        themes = analysis.get(
            "themes",
            []
        )

        if themes:

            st.write(
                "**Themes:** "
                + ", ".join(themes)
            )


    # =====================================================
    # RECOMMENDATIONS
    # =====================================================

    st.header("📚 Your Book Matches")

    recommendations = result.get(
        "recommendations",
        []
    )

    for number, book in enumerate(
        recommendations,
        start=1
    ):

        col1, col2 = st.columns(
            [1, 4]
        )

        with col1:

            st.metric(
                "Match",
                f"{book.get('match_score', 0)}%"
            )

        with col2:

            st.subheader(
                f"{number}. {book.get('title', 'Unknown')}"
            )

            st.write(
                f"**by {book.get('author', 'Unknown')}**"
            )

            st.write(
                book.get(
                    "reason",
                    ""
                )
            )

            st.write(
                f"🌙 **Mood:** "
                f"{book.get('mood', 'Unknown')}"
            )

            tags = book.get(
                "tags",
                []
            )

            if tags:

                st.write(
                    " ".join(
                        f"`#{tag}`"
                        for tag in tags
                    )
                )

        st.divider()


    # =====================================================
    # DATAFRAME
    # =====================================================

    if recommendations:

        df = pd.DataFrame(
            recommendations
        )

        st.header("📊 Recommendation Dashboard")

        k1, k2, k3 = st.columns(3)

        k1.metric(
            "Books Recommended",
            len(df),
            delta="+3"
        )

        k2.metric(
            "Best Match",
            f"{df['match_score'].max()}%"
        )

        k3.metric(
            "Average Match",
            f"{int(df['match_score'].mean())}%"
        )

        st.subheader(
            "📈 Match Score Comparison"
        )

        chart_df = df[
            ["title", "match_score"]
        ].copy()

        chart_df = chart_df.set_index(
            "title"
        )

        st.bar_chart(
            chart_df
        )

        st.subheader(
            "✏️ Edit Recommendations"
        )

        edited_df = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic"
        )

        csv = edited_df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇️ Download Recommendations",
            csv,
            "aesthetic_book_recommendations.csv",
            "text/csv"
        )


# =========================================================
# HISTORY
# =========================================================

if st.session_state.history:

    st.divider()

    with st.expander(
        "📜 Search History"
    ):

        history_df = pd.DataFrame(
            st.session_state.history
        )

        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "📚 Aesthetic Book Matchmaker | "
    "Powered by Streamlit + Gemini AI"
)
import nltk
import requests
from bs4 import BeautifulSoup
import re
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words
from sumy.summarizers.lsa import LsaSummarizer
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import streamlit as st

# Download NLTK punkt tokenizer
nltk.download('punkt')

# ---------------------------
# Inject CSS for styling
st.markdown("""
    <style>
    body {
        background-color: #f7f7f9;
    }
    .title-container {
        text-align: center;
        padding: 30px;
        margin-bottom: 20px;
        background: linear-gradient(135deg, #4CAF50, #2e7d32);
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    .title-text {
        font-size: 50px;
        font-weight: bold;
        background: -webkit-linear-gradient(#ffffff, #d4ffd1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .subtitle-text {
        font-size: 18px;
        color: white;
        font-style: italic;
        margin-top: -10px;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        padding: 10px 25px;
        font-size: 18px;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #45a049;
        transform: scale(1.05);
    }
    </style>
""", unsafe_allow_html=True)

# Attractive Title
st.markdown("""
<div class="title-container">
    <div class="title-text">📄 SumSnap AI</div>
    <div class="subtitle-text">Smart Web Scraping & Summarization</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------
def clean_text(text):
    cleaned_text = re.sub(r'\d', '', text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    cleaned_text = re.sub(r'\([^)]*\)', '', cleaned_text)
    cleaned_text = re.sub(r'[^\w\s]', '', cleaned_text)
    return cleaned_text.strip()

def summarize_text(text):
    cleaned_text = clean_text(text)
    parser = PlaintextParser.from_string(cleaned_text, Tokenizer('english'))
    stemmer = Stemmer('english')
    summarizer = LsaSummarizer(stemmer)
    summarizer.stop_words = get_stop_words('english')
    summary = summarizer(parser.document, 2)
    return ' '.join([str(sentence) for sentence in summary])

def get_sections_with_summaries(soup):
    sections = {}
    headings_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    all_elements = soup.find_all(headings_tags + ['p'])

    current_heading = "Introduction"
    current_text = ""

    for el in all_elements:
        if el.name in headings_tags:
            if current_text.strip():
                sections[current_heading] = summarize_text(current_text)
            current_heading = re.sub(r'\([^)]*\)', '', el.get_text()).strip()
            current_text = ""
        elif el.name == 'p':
            current_text += " " + el.get_text()

    if current_text.strip():
        sections[current_heading] = summarize_text(current_text)

    return sections

def generate_pdf(section_headings_and_summaries):
    filename = "output.pdf"
    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    story = []

    for heading, summary in section_headings_and_summaries.items():
        story.append(Paragraph(f"<b>{heading}</b>", styles["Heading2"]))
        story.append(Paragraph(summary, styles["Normal"]))
        story.append(Spacer(1, 12))

    doc.build(story)
    return filename

# ---------------------------
url = st.text_input("🔗 Enter a URL to scrape:")

if url:
    try:
        with st.spinner("🔍 Fetching and summarizing content... Please wait..."):
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            section_headings_and_summaries = get_sections_with_summaries(soup)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📖 Read"):
                st.subheader("Summarized Content")
                for heading, summary in section_headings_and_summaries.items():
                    with st.expander(f"📌 {heading}"):
                        st.write(summary)

        with col2:
            if st.button("💾 Download PDF"):
                pdf_file = generate_pdf(section_headings_and_summaries)
                with open(pdf_file, "rb") as f:
                    st.download_button(
                        label="⬇ Click to Download PDF",
                        data=f,
                        file_name="summary.pdf",
                        mime="application/pdf"
                    )

    except Exception as e:
        st.error(f"❌ Error: {e}")

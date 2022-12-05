import base64

import pandas as pd
import streamlit as st

from edspdf import Config, load
from edspdf.visualization import merge_boxes, show_annotations

CONFIG = """\
[pipeline]
    components = ["extractor", "classifier", "aggregator"]
    components_config = ${components}

[components]

[components.extractor]
@factory = "pdfminer-extractor"
extract_style = true

[components.classifier]
@factory = "mask-classifier"
x0 = 0.25
x1 = 0.95
y0 = 0.3
y1 = 0.9
threshold = 0.1

[components.aggregator]
@factory = "styled-aggregator"
"""


st.set_page_config(
    page_title="EDS-PDF Demo",
    page_icon="📄",
)

st.title("EDS-PDF")

st.warning(
    "You should **not** put sensitive data in the example, as this application "
    "**is not secure**."
)

st.sidebar.header("About")
st.sidebar.markdown(
    "EDS-PDF is a contributive effort maintained by AP-HP's Data Science team. "
    "Have a look at the "
    "[documentation](https://aphp.github.io/edspdf/) for more information."
)


st.header("Extract a PDF")

st.subheader("Configuration")
config = st.text_area(label="Change the config", value=CONFIG, height=200)


model_load_state = st.info("Loading model...")

reader = load(Config.from_str(config))

model_load_state.empty()

st.subheader("Input")
upload = st.file_uploader("PDF to analyse", accept_multiple_files=False)

if upload:

    pdf = upload.getvalue()

    base64_pdf = base64.b64encode(pdf).decode("utf-8")

    text, styles = reader(pdf)

    body = text.get("body")
    body_styles = styles.get("body")

    pdf_display = f"""\
    <iframe
        src="data:application/pdf;base64,{base64_pdf}"
        width="700"
        height="1000"
        type="application/pdf">
    </iframe>"""

    st.subheader("Output")

    with st.expander("Visualisation"):

        doc = reader.components.extractor(pdf)  # noqa
        doc = reader.components.classifier(doc)  # noqa
        merged = merge_boxes(sorted(doc.lines, key=lambda b: (b.y0, b.x0)))

        texts, styles = reader.components.aggregator(doc)  # noqa
        body = texts.get("body", "")
        styles = texts.get("styles", "")

        imgs = show_annotations(pdf=pdf, annotations=merged)

        page = st.selectbox("Pages", options=[i + 1 for i in range(len(imgs))]) - 1

        st.image(imgs[page])

    # with st.expander("PDF"):
    #     st.markdown(pdf_display, unsafe_allow_html=True)

    with st.expander("Text"):
        if body is None:
            st.warning(
                "No text detected... Are you sure this is a text-based PDF?\n\n"
                "There is no support for OCR within EDS-PDF (for now?)."
            )
        else:
            st.markdown("```\n" + body + "\n```")

    with st.expander("Styles"):
        if body_styles is None:
            st.warning(
                "No text detected... Are you sure this is a text-based PDF?\n\n"
                "There is no support for OCR within EDS-PDF (for now?)."
            )
        else:
            st.dataframe(pd.DataFrame.from_records(body_styles))

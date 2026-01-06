import streamlit as st
import requests
import pandas as pd
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import av

st.set_page_config(page_title="Food Nutrition Scanner", layout="centered")
st.title("Food Nutrition Scanner")

barcode = st.session_state.get("barcode", None)

class DummyScanner(VideoProcessorBase):
    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        # Camera only — barcode decoding happens client-side or manually
        return frame

webrtc_streamer(
    key="scanner",
    video_processor_factory=DummyScanner,
    media_stream_constraints={"video": True, "audio": False},
)

barcode_manual = st.text_input("Enter barcode if scan is not available")

if barcode_manual:
    st.session_state["barcode"] = barcode_manual.strip()

if "barcode" in st.session_state:
    barcode = st.session_state["barcode"]
    st.success(f"Using barcode: {barcode}")

if barcode and st.button("Fetch Product Info"):

    url = (
        f"https://world.openfoodfacts.net/api/v2/product/{barcode}"
        "?fields=product_name,nutriscore_data,nutriments,nutrition_grades"
    )

    r = requests.get(url, timeout=10)
    data = r.json()

    if data.get("status") != 1:
        st.error("Product not found")
    else:
        product = data["product"]

        st.header(product.get("product_name", "Unknown Product"))
        st.subheader(f"Nutrition Grade: {product.get('nutrition_grades', 'N/A').upper()}")

        nutriments = product.get("nutriments", {})
        rows = []
        for k, v in nutriments.items():
            if k.endswith("_100g"):
                base = k.replace("_100g", "")
                rows.append([
                    base.replace("_", " ").replace("-", " ").title(),
                    round(v, 2),
                    nutriments.get(f"{base}_unit", "")
                ])

        df = pd.DataFrame(rows, columns=["Nutrient", "Per 100g", "Unit"])
        st.subheader("Nutrition Facts")
        st.dataframe(df, use_container_width=True)

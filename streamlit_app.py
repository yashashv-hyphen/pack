"""
Pack Maker — web edition. Upload a ZIP of product images, download packs of 2, 3, and 4.
"""

import io
import zipfile
from pathlib import Path

import streamlit as st
from PIL import Image

from pack_maker_core import process_image

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".gif"}

st.set_page_config(page_title="Pack Maker", page_icon="📦")
st.title("📦 Pack Maker")
st.caption("Upload a ZIP of product images, get packs of 2, 3, and 4.")

uploaded = st.file_uploader("Upload ZIP file", type="zip")

if uploaded is not None:
    with zipfile.ZipFile(uploaded) as zf:
        entries = [
            n for n in zf.namelist()
            if Path(n).suffix.lower() in IMAGE_EXTS
            and not Path(n).name.startswith(".")
        ]

        if not entries:
            st.warning("No image files found in that ZIP.")
        else:
            st.write(f"Found **{len(entries)}** image(s). Generating packs of 2, 3, 4…")
            progress = st.progress(0)
            status = st.empty()

            out_buf = io.BytesIO()
            saved = []
            # PNGs are already compressed — re-deflating them in the zip just
            # burns CPU for no size benefit, so store them uncompressed.
            with zipfile.ZipFile(out_buf, "w", zipfile.ZIP_STORED) as out_zf:
                for idx, name in enumerate(entries, 1):
                    stem = Path(name).stem
                    status.text(f"[{idx}/{len(entries)}]  {Path(name).name}")
                    try:
                        img = Image.open(io.BytesIO(zf.read(name)))
                        for fname, result in process_image(img, stem):
                            buf = io.BytesIO()
                            result.save(buf, format="PNG", compress_level=4)
                            out_zf.writestr(fname, buf.getvalue())
                            saved.append(fname)
                    except Exception as e:
                        st.error(f"{Path(name).name}: {e}")
                    progress.progress(idx / len(entries))

            status.text(f"Done — {len(saved)} files generated")
            st.success(f"Generated {len(saved)} pack images.")
            st.download_button(
                "⬇️ Download all packs (.zip)",
                data=out_buf.getvalue(),
                file_name="packs.zip",
                mime="application/zip",
            )

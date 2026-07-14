"""
Pack Maker — web edition. Upload a ZIP of product images, download packs of 2, 3, and 4.
"""

import hashlib
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


def generate_packs(zip_bytes: bytes) -> tuple[bytes, int]:
    """Process every image in the uploaded ZIP and return (output_zip_bytes, count)."""
    out_buf = io.BytesIO()
    saved = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        entries = [
            n for n in zf.namelist()
            if Path(n).suffix.lower() in IMAGE_EXTS
            and not Path(n).name.startswith(".")
        ]
        if not entries:
            return b"", 0

        progress = st.progress(0)
        status = st.empty()

        # JPEGs are already compressed — re-deflating them in the zip just
        # burns CPU for no size benefit, so store them uncompressed.
        with zipfile.ZipFile(out_buf, "w", zipfile.ZIP_STORED) as out_zf:
            for idx, name in enumerate(entries, 1):
                stem = Path(name).stem
                status.text(f"[{idx}/{len(entries)}]  {Path(name).name}")
                try:
                    img = Image.open(io.BytesIO(zf.read(name)))
                    for fname, result in process_image(img, stem):
                        # Packs are already flattened onto a solid background
                        # (no transparency), so JPEG gives a much smaller file
                        # than PNG with no visible quality loss at this quality.
                        buf = io.BytesIO()
                        result.save(buf, format="JPEG", quality=92, optimize=True)
                        jpg_name = fname.rsplit(".", 1)[0] + ".jpg"
                        out_zf.writestr(jpg_name, buf.getvalue())
                        saved.append(jpg_name)
                except Exception as e:
                    st.error(f"{Path(name).name}: {e}")
                progress.progress(idx / len(entries))

        status.text(f"Done — {len(saved)} files generated")

    return out_buf.getvalue(), len(saved)


if uploaded is not None:
    zip_bytes = uploaded.getvalue()
    file_key = hashlib.sha256(zip_bytes).hexdigest()

    # Only (re)generate when a genuinely new/different ZIP is uploaded — otherwise
    # reuse the cached result so clicking "Download" (which reruns the script)
    # doesn't reprocess every image from scratch.
    if st.session_state.get("pack_maker_key") != file_key:
        result_zip, count = generate_packs(zip_bytes)
        st.session_state["pack_maker_key"] = file_key
        st.session_state["pack_maker_result"] = result_zip
        st.session_state["pack_maker_count"] = count

    result_zip = st.session_state["pack_maker_result"]
    count = st.session_state["pack_maker_count"]

    if count == 0:
        st.warning("No image files found in that ZIP.")
    else:
        st.success(f"Generated {count} pack images.")
        st.download_button(
            "⬇️ Download all packs (.zip)",
            data=result_zip,
            file_name="packs.zip",
            mime="application/zip",
        )

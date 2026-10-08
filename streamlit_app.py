import time
import streamlit as st

from meesho_sorter import process_pdfs

st.set_page_config(
    page_title="Meesho Label Sorter",
    page_icon="📦",
    layout="wide",
)

st.title("📦 Meesho Label Sorter")
st.caption("14 Meesho accounts ke label PDFs ko ek saath upload karein — tool original pages ko sirf arrange + merge karega.")

with st.expander("Sorting rule", expanded=False):
    st.markdown(
        """
- **Product family:** SKU ke end ke numeric digits sirf grouping ke liye ignore hote hain. Original SKU label par unchanged rehta hai.  
  Example: `RED_white_Flowar_01`, `RED_white_Flowar16`, `RED_white_Flowar_32` → same family.
- **Text suffix stays separate:** `RED_white_Flowar_A` alag family rahega.
- **Family order:** alphabetical.
- **Size order:** XS → S → M → L → XL → XXL → XXXL/3XL → 4XL → 5XL → 6XL → 7XL → 8XL.
- Same product + size ke labels sab accounts se **continuous** rahenge.
- Jo label read na ho, wo final PDF ke **end** me jayega; error section se pehle **1 blank page** aayega.
- Barcode, QR, address, invoice, SKU text, page design ko edit nahi kiya jata.
        """
    )

uploads = st.file_uploader(
    "Saare Meesho label PDFs yahan upload karein",
    type=["pdf"],
    accept_multiple_files=True,
    help="14 files ek saath upload kar sakte hain. Tool aur bhi PDFs handle kar sakta hai.",
)

if uploads:
    total_mb = sum(f.size for f in uploads) / (1024 * 1024)
    st.info(f"{len(uploads)} PDF selected • {total_mb:.1f} MB")

    if st.button("⚡ SORT + MERGE", type="primary", use_container_width=True):
        start = time.time()
        progress = st.progress(10, text="PDFs load ho rahe hain...")

        try:
            named_bytes = [(f.name, f.getvalue()) for f in uploads]
            progress.progress(30, text="SKU aur Size read ho rahe hain...")
            result = process_pdfs(named_bytes)
            progress.progress(90, text="Final sorted PDF ready ki ja rahi hai...")
            elapsed = time.time() - start
            progress.progress(100, text="Done")
        except Exception as exc:
            progress.empty()
            st.error(f"Processing failed: {exc}")
            st.stop()

        st.session_state["last_result"] = result
        st.session_state["elapsed"] = elapsed
        st.session_state["file_count"] = len(uploads)

if "last_result" in st.session_state:
    result = st.session_state["last_result"]
    elapsed = st.session_state.get("elapsed", 0)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("PDF Files", st.session_state.get("file_count", "-"))
    c2.metric("Input Labels", result["input_labels"])
    c3.metric("Product Families", result["product_families"])
    c4.metric("Unreadable", len(result["unreadable_df"]))
    c5.metric("Time", f"{elapsed:.1f}s")

    if len(result["unreadable_df"]) == 0:
        st.success(
            f"✅ All {result['input_labels']} labels read successfully. "
            f"Final PDF has {result['output_pages']} pages."
        )
    else:
        st.warning(
            f"⚠️ {len(result['unreadable_df'])} label(s) read nahi hue. "
            "Final PDF me normal labels ke baad 1 blank separator page hai, "
            "aur uske baad unreadable labels original form me hain."
        )

    st.download_button(
        "⬇️ DOWNLOAD FINAL SORTED PDF",
        data=result["sorted_pdf"],
        file_name="Meesho_Final_Sorted_Labels.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )

    with st.expander("Product + Size quantity summary"):
        st.dataframe(result["summary_df"], use_container_width=True, hide_index=True, height=420)

    if len(result["unreadable_df"]):
        with st.expander("Unreadable/Error labels details"):
            st.dataframe(
                result["unreadable_df"][["source_file", "page_number", "sku", "size", "parse_note"]],
                use_container_width=True,
                hide_index=True,
            )

    with st.expander("Sorted label index"):
        st.dataframe(
            result["order_df"][["family", "size", "sku", "order_no", "source_file", "page_number", "parse_status"]],
            use_container_width=True,
            hide_index=True,
            height=500,
        )

st.divider()
st.caption("Privacy note: Streamlit Cloud par upload ki hui order PDFs server par processing ke liye bheji jati hain. Customer-address PDFs ke liye app ko private rakhna recommended hai.")

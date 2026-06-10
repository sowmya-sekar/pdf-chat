import streamlit as st
import requests

API_URL = "https://pdf-chat-production-a069.up.railway.app"

st.set_page_config(page_title="PDF Chat", page_icon="📄")
st.title("📄 PDF Chat")
st.caption("Upload a PDF and ask questions!")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_uploaded" not in st.session_state:
    st.session_state.pdf_uploaded = False
if "summary" not in st.session_state:
    st.session_state.summary = ""

with st.sidebar:
    st.header("Upload PDF")
    uploaded_file = st.file_uploader("Choose a PDF", type="pdf")
    if uploaded_file:
        if st.button("Upload & Process"):
            with st.spinner("Uploading... Processing runs in background (wait 2-3 mins before asking questions)"):
             res = requests.post(
            f"{API_URL}/upload",
            files={"file": (uploaded_file.name, uploaded_file, "application/pdf")},
            timeout=30
        )
        if res.status_code == 200:
            st.success("✅ PDF uploading! Wait 2-3 mins then ask questions.")
            st.session_state.pdf_uploaded = True
            st.session_state.messages = []
            st.session_state.summary = ""
        else:
            st.error(f"Failed: {res.status_code} — {res.text}")

    if st.session_state.pdf_uploaded:
        st.divider()
        if st.button("📝 Get Notes & Key Points"):
            with st.spinner("Generating notes..."):
                res = requests.post(f"{API_URL}/summarize", timeout=60)
                if res.status_code == 200:
                    st.session_state.summary = res.json()["summary"]
                else:
                    st.error(f"Error: {res.text}")

if st.session_state.summary:
    with st.expander("📝 Notes & Key Points", expanded=True):
        st.markdown(st.session_state.summary)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Ask a question about your PDF..."):
    if not st.session_state.pdf_uploaded:
        st.warning("Please upload a PDF first!")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                res = requests.post(
                    f"{API_URL}/query",
                    json={"question": prompt},
                    timeout=60
                )
                if res.status_code == 200:
                    answer = res.json()["answer"]
                    st.write(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error(f"Error: {res.text}")
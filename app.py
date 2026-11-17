import streamlit as st
import subprocess
import tempfile
import shutil
from pathlib import Path

st.set_page_config(
    page_title="YouTube → Shorts",
    page_icon="🎬",
    layout="centered"
)

st.markdown("""
    <h1 style='text-align: center;'>🎬 YouTube → Shorts</h1>
    <p style='text-align: center; color: gray;'>Long video থেকে সহজে YouTube Shorts বানাও</p>
""", unsafe_allow_html=True)

@st.cache_resource
def install_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except:
        with st.spinner("প্রয়োজনীয় টুল ইনস্টল হচ্ছে (শুধু প্রথমবার)..."):
            subprocess.run(["apt-get", "update", "-qq"], check=False)
            subprocess.run(["apt-get", "install", "-y", "-qq", "ffmpeg"], check=False)
        return True

install_ffmpeg()

url = st.text_input("YouTube URL পেস্ট করো", placeholder="https://youtu.be/...")

col1, col2 = st.columns(2)
with col1:
    start = st.number_input("শুরুর সময় (সেকেন্ডে)", min_value=0, value=30, step=1)
with col2:
    length = st.number_input("কত সেকেন্ড চাও", min_value=10, max_value=60, value=40, step=1)

blur = st.checkbox("Blurred Background ব্যবহার করবো", value=True)

if st.button("🚀 Shorts বানাও", use_container_width=True):
    if not url or ("youtube.com" not in url and "youtu.be" not in url):
        st.error("সঠিক YouTube URL দাও!")
    else:
        with st.spinner("ভিডিও ডাউনলোড হচ্ছে + Shorts তৈরি হচ্ছে... অনুগ্রহ করে অপেক্ষা করো (১-২ মিনিট লাগতে পারে)"):
            work = Path(tempfile.mkdtemp())
            video = work / "video.mp4"
            out = work / "short.mp4"

            try:
                # Very flexible format selection
                cmd = [
                    "yt-dlp",
                    "--no-playlist",
                    "--no-warnings",
                    "-f", "bv*+ba/b",
                    "--merge-output-format", "mp4",
                    "-o", str(video),
                    "--force-overwrites",
                    url
                ]
                
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

                if not video.exists() or video.stat().st_size < 10000:
                    st.error("ডাউনলোড ব্যর্থ হয়েছে।")
                    with st.expander("এরর দেখো (ডেভেলপারের জন্য)"):
                        st.code(r.stderr[-1500:] if r.stderr else r.stdout[-1500:] if r.stdout else "No error output")
                    st.info("টিপস: অন্য একটি পাবলিক YouTube ভিডিও দিয়ে চেষ্টা করো।")
                else:
                    if blur:
                        vf = (
                            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                            "crop=1080:1920,boxblur=15:5[bg];"
                            "[0:v]scale=1080:-2:force_original_aspect_ratio=decrease[fg];"
                            "[bg][fg]overlay=(W-w)/2:(H-h)/2"
                        )
                    else:
                        vf = "crop=ih*9/16:ih,scale=1080:1920"

                    r2 = subprocess.run([
                        "ffmpeg", "-y",
                        "-ss", str(start),
                        "-i", str(video),
                        "-t", str(length),
                        "-vf", vf,
                        "-c:v", "libx264",
                        "-preset", "ultrafast",
                        "-crf", "26",
                        "-c:a", "aac",
                        "-b:a", "128k",
                        "-movflags", "+faststart",
                        str(out)
                    ], capture_output=True, text=True, timeout=120)

                    if out.exists() and out.stat().st_size > 5000:
                        st.success("✅ Shorts সফলভাবে তৈরি হয়েছে!")
                        st.video(str(out))

                        with open(out, "rb") as f:
                            st.download_button(
                                label="⬇️ Shorts ডাউনলোড করো",
                                data=f,
                                file_name="youtube_short.mp4",
                                mime="video/mp4",
                                use_container_width=True
                            )
                    else:
                        st.error("Shorts তৈরি ব্যর্থ হয়েছে।")
                        with st.expander("এরর দেখো"):
                            st.code(r2.stderr[-1000:] if r2.stderr else "No error")

            except subprocess.TimeoutExpired:
                st.error("সময় শেষ হয়ে গেছে। ছোট ভিডিও দিয়ে চেষ্টা করো।")
            except Exception as e:
                st.error(f"কিছু একটা ভুল হয়েছে: {str(e)}")
            finally:
                shutil.rmtree(work, ignore_errors=True)

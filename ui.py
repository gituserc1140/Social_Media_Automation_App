"""Streamlit screens and session-only workflow state."""

import os
from datetime import datetime, time, timedelta, timezone

import streamlit as st

import buffer_client
import cohere_service
import media_service
import openai_service
import pixel_art
import viggle_service


def render_app() -> None:
    st.title("Pixel Post Studio")
    st.caption("Make pixel art, bring it to life, and prepare it for Buffer.")

    st.sidebar.caption(
        "OpenAI, Cohere, and Buffer keys are read from the server .env file. "
        "The Viggle key stays in this session."
    )
    st.sidebar.subheader("API keys")
    st.sidebar.caption(
        "Image generation, animation, and publishing may incur charges."
    )
    st.sidebar.markdown(
        "[OpenAI](https://platform.openai.com/api-keys) · "
        "[Cohere](https://dashboard.cohere.com/api-keys) · "
        "[Viggle](https://portal.viggle.ai/keys) · "
        "[Buffer](https://publish.buffer.com/settings/api)"
    )
    api_keys = {
        "openai": os.getenv("OPENAI_API_KEY", "").strip(),
        "cohere": os.getenv("COHERE_API_KEY", "").strip(),
        "viggle": st.sidebar.text_input(
            "Viggle API key",
            type="password",
            key="viggle_api_key",
            help="Used for image-referenced Viggle video generation.",
        ),
        "buffer": os.getenv("BUFFER_API_KEY", "").strip(),
    }
    if st.sidebar.button("Test OpenAI key"):
        if not api_keys["openai"]:
            st.sidebar.warning("Set OPENAI_API_KEY in the server .env file.")
        else:
            try:
                openai_service.validate_api_key(api_keys["openai"])
                st.sidebar.success("OpenAI key is valid.")
            except Exception as exc:
                _show_error("OpenAI key check failed", exc, api_keys)
    if st.sidebar.button("Test Cohere key"):
        if not api_keys["cohere"]:
            st.sidebar.warning("Set COHERE_API_KEY in the server .env file.")
        else:
            try:
                cohere_service.validate_api_key(api_keys["cohere"])
                st.sidebar.success("Cohere key is valid.")
            except Exception as exc:
                _show_error("Cohere key check failed", exc, api_keys)
    if st.sidebar.button("Test Viggle key"):
        if not api_keys["viggle"]:
            st.sidebar.warning("Enter your Viggle API key above.")
        else:
            try:
                balance = viggle_service.get_credit_balance(api_keys["viggle"])
                st.sidebar.success(f"Viggle key is valid. Credit balance: {balance:g}")
            except Exception as exc:
                _show_error("Viggle key check failed", exc, api_keys)
    if st.sidebar.button("Test Buffer key"):
        if not api_keys["buffer"]:
            st.sidebar.warning("Set BUFFER_API_KEY in the server .env file.")
        else:
            try:
                organizations = buffer_client.get_organizations(api_keys["buffer"])
                st.sidebar.success(
                    f"Buffer key is valid. Found {len(organizations)} organization(s)."
                )
            except Exception as exc:
                _show_error("Buffer key check failed", exc, api_keys)
    st.session_state.setdefault("pixel_art_image", None)
    st.session_state.setdefault("animation_bytes", None)
    st.session_state.setdefault("animation_type", None)
    st.session_state.setdefault("converted_animation_bytes", None)
    st.session_state.setdefault("music_bytes", None)
    st.session_state.setdefault("music_extension", None)
    st.session_state.setdefault("caption_text", "")
    st.session_state.setdefault("buffer_organizations", [])
    st.session_state.setdefault("buffer_channels", [])

    create_tab, animate_tab, soundtrack_tab, publish_tab = st.tabs(
        [
            "1 · Create pixel art",
            "2 · Animate",
            "3 · Soundtrack (optional)",
            "4 · Caption & publish",
        ]
    )

    with create_tab:
        prompt = st.text_input(
            "Describe your pixel-art scene",
            placeholder="A tiny astronaut tending a garden on the moon",
            key="image_prompt",
        )
        left, right = st.columns(2)
        with left:
            if st.button("Generate with OpenAI", type="primary", width="stretch"):
                if not prompt.strip():
                    st.error("Enter a description for your pixel art.")
                elif not api_keys["openai"]:
                    st.error("Set OPENAI_API_KEY in the server .env file.")
                else:
                    with st.spinner("Creating pixel art with OpenAI…"):
                        try:
                            _save_pixel_art(
                                openai_service.generate_pixel_art(
                                    prompt.strip(),
                                    api_keys["openai"],
                                )
                            )
                            st.success("Pixel art created.")
                        except Exception as exc:
                            _show_error("Image generation failed", exc, api_keys)
        with right:
            uploaded_image = st.file_uploader(
                "Or convert an image you own",
                type=["png", "jpg", "jpeg", "webp"],
                key="source_image_upload",
            )
            if st.button("Convert upload to pixel art", width="stretch"):
                if uploaded_image is None:
                    st.error("Choose an image to convert.")
                else:
                    try:
                        _save_pixel_art(
                            pixel_art.convert_to_pixel_art(uploaded_image.getvalue())
                        )
                        st.success("Uploaded image converted to pixel art.")
                    except Exception as exc:
                        st.error(f"Image conversion failed: {exc}")

        if st.session_state.pixel_art_image:
            st.subheader("Image preview")
            st.image(st.session_state.pixel_art_image, width="stretch")
            st.download_button(
                "Download pixel art",
                data=st.session_state.pixel_art_image,
                file_name="pixel-art.png",
                mime="image/png",
            )

    with animate_tab:
        image_bytes = st.session_state.pixel_art_image
        uploaded_animation = st.file_uploader(
            "Upload an existing MP4 animation",
            type=["mp4"],
            key="animation_upload",
        )
        if uploaded_animation is not None:
            uploaded_bytes = uploaded_animation.getvalue()
            if (
                st.session_state.get("uploaded_animation_name") != uploaded_animation.name
                or st.session_state.get("uploaded_animation_source") != uploaded_bytes
            ):
                st.session_state.animation_bytes = uploaded_bytes
                st.session_state.animation_type = "mp4"
                st.session_state.converted_animation_bytes = None
                st.session_state.uploaded_animation_name = uploaded_animation.name
                st.session_state.uploaded_animation_source = uploaded_bytes
                st.success("Animation uploaded and ready to use.")
        if image_bytes:
            st.image(image_bytes, caption="Image to animate", width=320)
            st.caption("Animation provider: Viggle")
            animation_prompt = st.text_input(
                "Describe the motion",
                value="A gentle idle animation; preserve the original pixel-art style.",
                key="animation_prompt",
            )
            st.caption(
                "Viggle returns video with native audio. Generation is billed by "
                "duration; check your Viggle balance before submitting."
            )
            viggle_quality = st.selectbox(
                "Viggle quality",
                ["low", "high"],
                help="Low is faster to iterate; both quality levels use the same rate per resolution.",
            )
            viggle_duration = st.slider(
                "Video duration (seconds)",
                min_value=3,
                max_value=15,
                value=5,
                help="Viggle generation is billed by duration.",
            )
            if st.button("Create animation", type="primary"):
                if not api_keys["viggle"]:
                    st.error("Enter your Viggle API key in the sidebar.")
                elif not animation_prompt.strip():
                    st.error("Describe how the artwork should move.")
                else:
                    with st.spinner(
                        "Animating with Viggle. This can take several minutes…"
                    ):
                        try:
                            video_bytes = viggle_service.animate_image(
                                image_bytes,
                                animation_prompt.strip(),
                                api_keys["viggle"],
                                quality=viggle_quality,
                                duration_seconds=viggle_duration,
                            )
                            if st.session_state.music_bytes:
                                video_bytes = media_service.add_background_music(
                                    video_bytes,
                                    st.session_state.music_bytes,
                                    st.session_state.music_extension,
                                )
                            st.session_state.animation_bytes = video_bytes
                            st.session_state.animation_type = "mp4"
                            st.session_state.converted_animation_bytes = None
                        except Exception as exc:
                            _show_error("Animation failed", exc, api_keys)
        else:
            st.info(
                "Create pixel art to generate an animation, or upload an existing "
                "MP4 animation above."
            )

        _render_animation_preview()
        if (
            st.session_state.animation_type == "mp4"
            and st.session_state.animation_bytes
        ):
            st.caption(
                "Convert to TikTok portrait (1080 × 1920). The full video stays visible "
                "over a solid background sampled from the video; zoom adjusts its size."
            )
            video_zoom = st.slider(
                "Video zoom",
                min_value=0.5,
                max_value=2.0,
                value=1.0,
                step=0.1,
                help=(
                    "Zoom out to show more of the whole video, or zoom in to crop "
                    "closer. A matching solid color fills the 9:16 frame."
                ),
            )
            if st.button("Convert video to 1080 × 1920"):
                with st.spinner("Converting video to 1080 × 1920…"):
                    try:
                        st.session_state.converted_animation_bytes = (
                            media_service.convert_to_tiktok_format(
                                st.session_state.animation_bytes,
                                zoom=video_zoom,
                            )
                        )
                        st.rerun()
                    except Exception as exc:
                        _show_error("TikTok video conversion failed", exc, api_keys)

    with soundtrack_tab:
        st.caption("Optional: skip the soundtrack and continue to Caption & publish.")
        st.write("Upload an audio track to preview it or add it to your video.")
        uploaded_music = st.file_uploader(
            "Upload an audio track",
            type=["mp3", "wav", "m4a", "ogg"],
            key="music_upload",
        )
        if uploaded_music is not None:
            extension = uploaded_music.name.rsplit(".", maxsplit=1)[-1].lower()
            uploaded_bytes = uploaded_music.getvalue()
            if (
                st.session_state.get("uploaded_music_name") != uploaded_music.name
                or st.session_state.get("uploaded_music_source") != uploaded_bytes
            ):
                st.session_state.music_bytes = uploaded_bytes
                st.session_state.music_extension = extension
                st.session_state.uploaded_music_name = uploaded_music.name
                st.session_state.uploaded_music_source = uploaded_bytes
        if st.session_state.music_bytes:
            st.audio(st.session_state.music_bytes)
            st.download_button(
                "Download soundtrack",
                data=st.session_state.music_bytes,
                file_name=f"pixel-art-soundtrack.{st.session_state.music_extension}",
                mime=_audio_mime(st.session_state.music_extension),
            )
            if (
                st.session_state.animation_type == "mp4"
                and st.session_state.animation_bytes
                and st.button("Add soundtrack to current video")
            ):
                with st.spinner("Adding soundtrack to video…"):
                    try:
                        if st.session_state.converted_animation_bytes:
                            st.session_state.converted_animation_bytes = (
                                media_service.add_background_music(
                                    st.session_state.converted_animation_bytes,
                                    st.session_state.music_bytes,
                                    st.session_state.music_extension,
                                )
                            )
                        else:
                            st.session_state.animation_bytes = (
                                media_service.add_background_music(
                                    st.session_state.animation_bytes,
                                    st.session_state.music_bytes,
                                    st.session_state.music_extension,
                                )
                            )
                        st.success("Soundtrack added to the video.")
                    except Exception as exc:
                        _show_error("Could not add soundtrack", exc, api_keys)
            elif st.session_state.animation_type == "gif":
                st.caption("The demo animation is a GIF. Add a soundtrack after creating an MP4 in live mode.")

    with publish_tab:
        _render_publish(api_keys, prompt)


def _render_animation_preview() -> None:
    animation = st.session_state.animation_bytes
    if not animation:
        return
    if st.session_state.animation_type == "mp4":
        converted_animation = st.session_state.converted_animation_bytes
        st.video(converted_animation or animation)
        if converted_animation:
            st.download_button(
                "Download converted TikTok video (1080 × 1920)",
                data=converted_animation,
                file_name="tiktok-video-1080x1920.mp4",
                mime="video/mp4",
                key="download_converted_tiktok_video",
            )
            st.download_button(
                "Download original animation",
                data=animation,
                file_name="pixel-art-animation-original.mp4",
                mime="video/mp4",
                key="download_original_animation",
            )
            return
        file_name, mime_type = "pixel-art-animation.mp4", "video/mp4"
    else:
        st.image(animation, caption="Looping demo animation", width=420)
        file_name, mime_type = "pixel-art-animation.gif", "image/gif"
    st.download_button(
        "Download animation",
        data=animation,
        file_name=file_name,
        mime=mime_type,
    )


def _render_publish(api_keys: dict[str, str], prompt: str) -> None:
    if not st.session_state.pixel_art_image and not st.session_state.animation_bytes:
        st.info("Create pixel art or upload an animation before preparing a post.")
        return

    st.subheader("Caption")
    if st.button("Generate caption and hashtags"):
        if not api_keys["cohere"]:
            st.error("Set COHERE_API_KEY in the server .env file.")
        else:
            with st.spinner("Writing a caption with Cohere…"):
                try:
                    st.session_state.caption_text = cohere_service.generate_caption(
                        prompt.strip() or "A pixel-art creation",
                        api_keys["cohere"],
                    )
                except Exception as exc:
                    _show_error("Cohere caption generation failed", exc, api_keys)

    caption = st.text_area("Post text", key="caption_text", height=120)
    if st.session_state.animation_bytes:
        media_kind = "video" if st.session_state.animation_type == "mp4" else "image"
        st.caption(f"Your {media_kind} is ready to preview and download above.")
    else:
        media_kind = "image"

    st.subheader("Publish with Buffer")
    buffer_key = api_keys["buffer"]
    if not buffer_key:
        st.warning("Set BUFFER_API_KEY in the server .env file to connect your accounts.")
        return
    if st.button("Load Buffer organizations"):
        with st.spinner("Loading Buffer organizations…"):
            try:
                st.session_state.buffer_organizations = buffer_client.get_organizations(buffer_key)
                st.session_state.buffer_channels = []
            except Exception as exc:
                _show_error("Could not load Buffer organizations", exc, api_keys)

    organizations = st.session_state.buffer_organizations
    if not organizations:
        return
    organization_by_label = {
        f"{item['name']} ({item['id']})": item["id"] for item in organizations
    }
    organization_label = st.selectbox("Buffer organization", list(organization_by_label))
    if st.button("Load channels for organization"):
        with st.spinner("Loading social accounts…"):
            try:
                st.session_state.buffer_channels = buffer_client.get_channels(
                    organization_by_label[organization_label],
                    buffer_key,
                )
            except Exception as exc:
                _show_error("Could not load Buffer channels", exc, api_keys)

    channels = st.session_state.buffer_channels
    if not channels:
        return
    channel_by_label = {
        f"{channel['name']} · {channel['service']}": channel["id"]
        for channel in channels
    }
    channel_label = st.selectbox("Social account", list(channel_by_label))
    schedule_mode = st.radio(
        "When should Buffer publish?",
        ["Add to next queue slot", "Schedule for a specific time"],
    )

    due_at = None
    if schedule_mode == "Schedule for a specific time":
        default_datetime = datetime.now(timezone.utc) + timedelta(hours=1)
        post_date = st.date_input("Date (UTC)", value=default_datetime.date())
        post_time = st.time_input(
            "Time (UTC)",
            value=default_datetime.time().replace(second=0, microsecond=0),
        )
        due_at = datetime.combine(post_date, post_time, tzinfo=timezone.utc)
        if due_at <= datetime.now(timezone.utc):
            st.warning("Choose a future date and time.")

    media_source = st.radio(
        "Post media",
        ["Use a public media URL", "Text only"],
        index=0,
        horizontal=True,
        key="buffer_media_source",
    )
    if st.session_state.converted_animation_bytes or st.session_state.animation_bytes:
        st.info(
            "Buffer cannot upload files directly from this app. Download your animation, "
            "host it at a public HTTPS URL (for example, an S3 object URL), then paste "
            "that direct media-file URL below."
        )
    media_url = ""
    social_page_url = False
    if media_source == "Use a public media URL":
        media_url = st.text_input(
            "Direct public image/video file URL",
            help=(
                "Use a direct HTTPS URL to an image or MP4 file hosted on public storage, "
                "such as an Amazon S3 object URL. The object must be accessible to Buffer "
                "without signing in."
            ),
        )
        storage_links = st.columns(2)
        with storage_links[0]:
            st.link_button("Open Amazon S3", "https://aws.amazon.com/s3/")
        with storage_links[1]:
            st.link_button("Open Cloudinary", "https://console.cloudinary.com/")
        st.caption(
            "Upload your downloaded media to S3 or Cloudinary, then paste its direct "
            "HTTPS media URL above. The file must be publicly accessible to Buffer; "
            "presigned URLs may expire before a scheduled post is published."
        )
        social_page_url = bool(media_url.strip()) and buffer_client.is_social_media_page_url(
            media_url.strip()
        )
        if social_page_url:
            st.warning(
                "This looks like a social-media profile or post page, not a direct video file. "
                "Use a public URL that serves the actual .mp4/.png/.jpg file."
            )
    if "tiktok" in channel_label.lower() and media_source == "Text only":
        st.warning("TikTok requires an image or video. Choose generated media or provide a public media URL.")
    post_button_label = (
        "Add post to queue"
        if schedule_mode == "Add to next queue slot"
        else "Schedule post"
    )
    if st.button(post_button_label, type="primary"):
        if not caption.strip():
            st.error("Write or generate a caption first.")
        elif schedule_mode != "Add to next queue slot" and (
            due_at is None or due_at <= datetime.now(timezone.utc)
        ):
            st.error("Choose a future date and time.")
        elif media_url and not media_url.lower().startswith("https://"):
            st.error("Enter a public HTTPS media URL.")
        elif social_page_url:
            st.error(
                "Buffer cannot read media from a social profile/share page. "
                "Paste a direct public media-file URL instead."
            )
        elif "tiktok" in channel_label.lower() and media_source == "Text only":
            st.error(
                "TikTok posts require an image or video. Provide a public media-file URL."
            )
        else:
            due_at_text = (
                due_at.isoformat(timespec="seconds").replace("+00:00", "Z")
                if due_at
                else None
            )
            with st.spinner("Sending post to Buffer…"):
                try:
                    if media_source == "Text only":
                        media_url = ""
                    post = buffer_client.create_post(
                        channel_id=channel_by_label[channel_label],
                        text=caption.strip(),
                        api_key=buffer_key,
                        mode=(
                            "addToQueue"
                            if schedule_mode == "Add to next queue slot"
                            else "customScheduled"
                        ),
                        due_at=due_at_text,
                        media_url=media_url.strip() or None,
                        media_kind=(
                            media_kind if media_url.strip() else None
                        ),
                    )
                    st.success(
                        f"Post queued successfully (Buffer post ID: {post['id']})."
                    )
                except Exception as exc:
                    _show_error("Could not send post to Buffer", exc, api_keys)


def _audio_mime(extension: str) -> str:
    return {
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "m4a": "audio/mp4",
        "ogg": "audio/ogg",
    }.get(extension, "application/octet-stream")


def _save_pixel_art(image_bytes: bytes) -> None:
    st.session_state.pixel_art_image = image_bytes
    st.session_state.animation_bytes = None
    st.session_state.animation_type = None
    st.session_state.converted_animation_bytes = None


def _show_error(message: str, error: Exception, api_keys: dict[str, str]) -> None:
    details = str(error)
    for api_key in api_keys.values():
        if api_key:
            details = details.replace(api_key, "[redacted]")
    st.error(f"{message}: {details}")
    if isinstance(error, viggle_service.ViggleAPIError):
        if error.status_code == 401 or error.code in {
            "UNAUTHENTICATED",
            "INVALID_CREDENTIAL",
        }:
            st.info(
                "Viggle rejected this credential. Create a Viggle V1 project API key in "
                "the Viggle developer dashboard, then replace the value in the sidebar. "
                "A Viggle website, Discord, or other product login token is not an API key."
            )
            st.markdown(
                "[Create or manage Viggle API keys](https://portal.viggle.ai/keys) · "
                "[Viggle API authentication guide](https://docs.viggle.ai/v1/authentication)"
            )
        elif error.status_code == 402 or error.code == "INSUFFICIENT_CREDITS":
            st.info("The Viggle API key was accepted, but its account needs more API credits.")
            st.markdown("[View Viggle dashboard and credits](https://portal.viggle.ai/dashboard)")

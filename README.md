# Pixel Post Studio

A small Streamlit app for creating pixel art, turning it into an animation,
adding a soundtrack, and preparing social posts with Buffer.

## Run locally

Python 3.10 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On Windows, activate the environment with `.venv\Scripts\activate`.

## Use live services

The app opens in **Live mode**. Enter provider keys in the sidebar as needed:

- **OpenAI** — image generation (`gpt-image-1`) and captions (`gpt-4o-mini`).
  Use **Test OpenAI key** for a non-billable credentials check.
- **Google Gemini** — animation with **Gemini Omni Flash** (default, image-
  conditioned video through the Interactions API) or **Veo 3.1** (long-running
  image-to-video generation). Use **Test Google Gemini key** for a
  non-billable credentials check.
- **fal.ai** — image-to-video animation (`fal-ai/wan-i2v`). The key is tested
  when animation is requested; the validation call itself would incur model
  usage.
- **Viggle** — image-referenced video generation. Get a key from the
  [Viggle dashboard](https://portal.viggle.ai/keys), enter it in the sidebar,
  and use **Check Viggle credits** to verify it and view the available balance.
  Choose low/high quality and a 3–15 second duration in the Animate tab; Viggle
  generation is billed by duration and returns video with native audio. Use a
  Viggle V1 project API key (not a regular Viggle or Discord login token).
- **Cloudinary** — automatic hosting for generated image/video assets attached
  to Buffer posts. Enter your Cloudinary cloud name, API key, and API secret in
  the sidebar. Choose **Generated animation video (upload to Cloudinary)** (or
  generated pixel art) in the post media selector; the app uploads the asset
  and passes its public delivery URL to Buffer.
- **Hugging Face** — soundtrack generation (`facebook/musicgen-small`). Use
  **Test Hugging Face token** for a non-billable credentials check.
- **Buffer** — click **Load Buffer organizations** to verify access and select
  a connected account. Add a post to the next queue slot or schedule it for a
  specific UTC time.

Provider keys may be entered independently; for example, OpenAI is not needed
to convert an uploaded image, and Buffer is not needed to create or download
art. Generation and publishing calls may incur provider charges. To explore
without live API calls, turn on **Demo mode** in the sidebar; demo publishing
is simulated and never sends a post.

Keys are password inputs held in the active Streamlit session only. The app does
not write them to files, environment variables, or Streamlit secrets. fal.ai
generation runs in a short-lived child process so a key is not added to the
shared Streamlit server process environment. As with any web app, the server
must receive a key to use it; only enter credentials on a trusted HTTPS
deployment. This app does not include user sign-in, per-user quotas, or
server-side session isolation for a public multi-tenant launch. Add those
controls before exposing a deployment to untrusted users.

Buffer does not accept local media uploads directly. Generated media can be
uploaded to Cloudinary by the app, or you can provide another host's direct,
publicly accessible HTTPS file URL. A TikTok profile/post URL (or another
social share page) is not the video file, so Buffer cannot fetch it. Cloudinary
assets are public and remain in your Cloudinary account; delete them there when
no longer needed. Posts can also be queued without media on platforms that
allow text-only posts. TikTok requires an image or video.

Provider usage may incur charges and is subject to each provider's account
access, model availability, and rate limits.

### Google video quota errors

Gemini Omni and Veo have separate model/project quotas. If Google returns HTTP
429, the app now shows Google's error message and any available quota metric.
Check the limits and usage for the Google AI Studio project that owns the API
key, confirm that the selected video model is available to that project, and
wait for a rate limit to reset or request/enable the appropriate quota. Repeated
retries do not bypass a provider quota.

## Project layout

- `app.py` — Streamlit entry point.
- `ui.py` — workflow, settings, preview, download, and publishing screens.
- `pixel_art.py` — image conversion and offline demo assets.
- `openai_service.py` — OpenAI image generation and captioning.
- `animation_service.py` — fal.ai image-to-video generation.
- `google_video_service.py` — Gemini Omni Flash and Veo 3.1 animation.
- `viggle_service.py` — Viggle image-to-video generation and credit checks.
- `cloudinary_service.py` — signed media uploads for Buffer attachments.
- `music_service.py` — Hugging Face soundtrack generation.
- `media_service.py` — local audio/video muxing.
- `buffer_client.py` — Buffer organization, channel, and post operations.

Run tests with:

```bash
python -m pytest
```

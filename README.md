# Pixel Post Studio

A small Streamlit app for creating pixel art, turning it into an animation (or
uploading an existing MP4), adding a soundtrack, and preparing social posts with
Buffer. The Animate tab can also convert an MP4 to TikTok's 1080 × 1920 portrait
format with adjustable zoom, a solid video-matched background, and a separate
download.

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

- **OpenAI** — pixel-art image generation (`gpt-image-1`). Use **Test OpenAI key**
  for a non-billable credentials check.
- **Cohere** — caption and hashtag generation. Create an API key in the
  [Cohere dashboard](https://dashboard.cohere.com/api-keys) and enter it in the
  sidebar. Cohere's trial/free usage and model access depend on its current
  account limits and terms; check your Cohere dashboard for details.
- **Viggle** — image-referenced video generation. Get a key from the
  [Viggle dashboard](https://portal.viggle.ai/keys), enter it in the sidebar,
  and use **Check Viggle credits** to verify it and view the available balance.
  Choose low/high quality and a 3–15 second duration in the Animate tab; Viggle
  generation is billed by duration and returns video with native audio. Use a
  Viggle V1 project API key (not a regular Viggle or Discord login token).
- **Buffer** — click **Load Buffer organizations** to verify access and select
  a connected account. Add a post to the next queue slot or schedule it for a
  specific UTC time.

Provider keys may be entered independently; for example, OpenAI is only needed
for image generation, Cohere is only needed for live caption generation, and
Buffer is not needed to create or download art. Upload your own audio track in
the optional soundtrack tab. Generation and publishing calls may incur provider
charges.

Keys are password inputs held in the active Streamlit session only. The app does
not write them to files, environment variables, or Streamlit secrets. As with
any web app, the server must receive a key to use it; only enter credentials on
a trusted HTTPS deployment. This app does not include user sign-in, per-user quotas, or
server-side session isolation for a public multi-tenant launch. Add those
controls before exposing a deployment to untrusted users.

Buffer does not accept local media uploads directly. To attach generated media,
download it from the app and host it at a direct, publicly accessible HTTPS file
URL, such as an Amazon S3 object URL or Cloudinary delivery URL. The public media
URL section has **Open Amazon S3** and **Open Cloudinary** buttons. Upload your
downloaded video to one of those services, then paste its direct HTTPS media URL
above (not a storage dashboard or share-page URL). The file must be publicly
accessible to Buffer; presigned URLs may expire before a scheduled post is
published. A TikTok profile/post URL (or another social share page) is not the
video file, so Buffer cannot fetch it. Posts can also be queued without media on
platforms that allow text-only posts. TikTok requires an image or video.

Provider usage may incur charges and is subject to each provider's account
access, model availability, and rate limits.

## Project layout

- `app.py` — Streamlit entry point.
- `ui.py` — workflow, settings, preview, download, and publishing screens.
- `pixel_art.py` — image conversion and offline demo assets.
- `openai_service.py` — OpenAI image generation.
- `cohere_service.py` — Cohere caption and hashtag generation.
- `viggle_service.py` — Viggle image-to-video generation and credit checks.
- `media_service.py` — local audio/video muxing.
- `buffer_client.py` — Buffer organization, channel, and post operations.

Run tests with:

```bash
python -m pytest
```

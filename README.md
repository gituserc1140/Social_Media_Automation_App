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

## Configure live services

OpenAI, Cohere, and Buffer credentials are loaded on the server from a `.env`
file in the project root. Fill in the provided `.env` template before starting
the app:

```dotenv
OPENAI_API_KEY=your-openai-api-key
COHERE_API_KEY=your-cohere-api-key
BUFFER_API_KEY=your-buffer-api-key
```

The `.env` file is excluded from Git. For deployed environments, set these as
server environment variables instead; environment variables take precedence
over values in `.env`. These three keys are not entered into the Streamlit UI.

The Viggle key remains a password input in the sidebar, so it can be rotated
from the UI without changing the server configuration. Configure provider
credentials as needed:

- **OpenAI** — pixel-art image generation (`gpt-image-1`). Use **Test OpenAI key**
  for a non-billable credentials check. Configure `OPENAI_API_KEY` on the server.
- **Cohere** — caption and hashtag generation. Create an API key in the
  [Cohere dashboard](https://dashboard.cohere.com/api-keys) and enter it in the
  `.env` file as `COHERE_API_KEY`. Cohere's trial/free usage and model access
  depend on its current account limits and terms; check your Cohere dashboard
  for details. **Test Cohere key** checks credentials using the models endpoint
  without generating a caption.
- **Viggle** — image-referenced video generation. Get a key from the
  [Viggle dashboard](https://portal.viggle.ai/keys), enter it in the sidebar,
  and use **Test Viggle key** to verify it and view the available balance.
  Choose low/high quality and a 3–15 second duration in the Animate tab; Viggle
  generation is billed by duration and returns video with native audio. Use a
  Viggle V1 project API key (not a regular Viggle or Discord login token).
- **Buffer** — click **Load Buffer organizations** to verify access and select
  a connected account. Configure `BUFFER_API_KEY` on the server. Add a post to
  the next queue slot or schedule it for a specific UTC time. **Test Buffer
  key** checks access by listing the organizations available to the account.

Provider credentials may be configured independently; for example, OpenAI is
only needed for image generation, Cohere is only needed for live caption
generation, and Buffer is not needed to create or download art. Upload your own
audio track in the optional soundtrack tab. Generation and publishing calls may
incur provider charges.

The OpenAI, Cohere, and Buffer keys are server-side configuration. The Viggle
key is held in the active Streamlit session only and is not saved to disk.
This app does not include user sign-in, per-user quotas, or server-side session
isolation for a public multi-tenant launch. Add those controls before exposing
a deployment to untrusted users.

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
- `.env.example` — server-side OpenAI, Cohere, and Buffer key template.
- `.env` — local credentials file; ignored by Git.

Run tests with:

```bash
python -m pytest
```

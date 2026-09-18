# Local livestream

OBS captures the external Samsung LS27D300G display at 1920×1080, 30 fps.
The user arranged the webcam at upper left and ChatGPT at right; reserve the
lower-left area for the windowed SC2 client. API launch uses `-displayMode 0`.
Simultaneous game/API/capture operation is verified: OBS preview shows the running
campaign on the left and the conversation on the right.
Use `--window-size 960 540` for the reserved area. The first launch ignored
`--window-position 1728 550`; place the window through the UI after startup. These are the same
window flags used by [PySC2](https://github.com/google-deepmind/pysc2/blob/master/pysc2/lib/sc_process.py).

X broadcast: https://x.com/i/broadcasts/1oJMvNMOYpOxQ

The broadcast is public; everyone can chat. OBS uses Apple's hardware H.264
encoder, 6000 kbps video and 128 kbps AAC audio. The existing X source is
configured in OBS; its stream key belongs only in OBS's local settings.
Never commit it or display the destination settings on the captured monitor.

Controls in OBS:

- Microphone: click the speaker icon under **Mic/Aux** in Audio Mixer.
- Webcam: click the eye next to **Video Capture Device** in Sources.
- End transmission: **Stop Streaming**. End the broadcast in X Live Studio too.
- **macOS Screen Capture** audio is muted to avoid broadcasting unrelated
  desktop audio. **macOS Audio Capture** uses Application Audio Capture → SC2;
  its meter was active during API-driven gameplay.

The user enabled webcam and microphone after their initial muted setup.
At initial live verification OBS reported zero dropped frames. A later check at
45 minutes showed 96 dropped frames (0.1%), about 6130 kbps and 30 fps. At that
check the user had muted Mic/Aux and hidden the webcam; these controls were left
unchanged.

References: [X Live Producer](https://help.x.com/en/using-x/how-to-use-live-producer),
[OBS macOS Screen Capture](https://obsproject.com/kb/macos-screen-capture-source).

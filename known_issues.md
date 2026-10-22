# Known issues

## Temporary Bluetooth audio stalls

### Status and functional impact

With the EDIFIER MP230 connected through Bluetooth A2DP, audio can occasionally
pause for approximately 1–6 seconds during repeated button presses. The physical
button events still reach PiZoo, but the call into the Pygame/SDL audio mixer can
block while the Bluetooth stream is stalled. Button callbacks waiting behind that
call are processed quickly when audio resumes, so one or more sounds may be late,
replaced by a newer press, or effectively missed.

This is currently considered non-critical:

- The Raspberry Pi does not reboot or lose power.
- The PiZoo service does not crash or restart.
- The Bluetooth speaker remains connected according to BlueZ.
- Audio resumes without intervention after the short pause.

This issue is separate from the earlier analog-speaker problem. That speaker was
connected to the Pi's audio jack but powered by the same battery pack over USB.
Giving the speaker an independent power supply eliminated the original permanent
loss of audio, indicating that problem was caused by the speaker's power source.

### Reproduction and observations

The issue was reproduced by connecting the EDIFIER MP230, starting PiZoo, and
pressing different animal buttons repeatedly (roughly one press every 0.7–1
second) for 30–45 seconds.

The diagnostic logs showed several mixer calls taking much longer than normal:

- About 12.0 seconds while using the original 22.05 kHz mono mixer format.
- About 1.8 and 4.7 seconds after changing Bluetooth playback to 48 kHz stereo.
- About 6.25 seconds during an experimental direct-BlueALSA test.

During the 4.7-second example, several additional button callbacks accumulated
and all continued immediately after the blocked mixer call returned. This
confirmed that GPIO input was still working during the silent period.

Checks made during the stalls found:

- The PiZoo PID was unchanged and systemd reported zero automatic restarts.
- Raspberry Pi uptime and boot identity were unchanged.
- `bluetoothctl` continued to report the speaker as connected.
- BlueALSA and the kernel logged no corresponding disconnect or transport error.
- `vcgencmd get_throttled` returned `0x0`, with no current or historical
  undervoltage/throttling flag.
- Wi-Fi was using 5 GHz with a strong signal, making 2.4 GHz Wi-Fi/Bluetooth
  coexistence interference less likely.

A deliberate Bluetooth disconnect was also tested. The connection monitor
detected the route change and systemd restarted only the game process, producing
the startup sound. The naturally occurring short stalls did not show this restart
pattern and are therefore not Bluetooth disconnects or Raspberry Pi reboots.

### Hypotheses and changes tested

1. **Button bounce or callback storms.** Historical logs contained bursts of
   callbacks. A 150 ms GPIO debounce interval was added. This removed the callback
   storms but did not eliminate Bluetooth audio stalls.

2. **Concurrent global mixer operations.** The old code stopped the entire mixer
   before each sound and allowed multiple GPIO threads to access it. PiZoo now
   serializes mixer access and uses one dedicated channel, where a new sound
   replaces the previous sound. This improved behavior but did not remove the
   temporary stalls.

3. **Live sample-rate/channel conversion.** The original 22.05 kHz mono mixer did
   not match the 48 kHz stereo A2DP/SBC transport. Bluetooth playback was changed
   to native 48 kHz stereo. The first stress test reduced the worst observed pause
   from about 12 seconds to 4.7 seconds, but a later test still produced a
   6.25-second pause.

4. **ALSA `plug` conversion and buffering.** A temporary direct BlueALSA PCM was
   defined in `~/.asoundrc` to bypass the standard `bluealsa` plug wrapper. The
   stress test still produced a 6.25-second block, so the experiment was reverted
   and the temporary ALSA configuration was removed.

5. **Bluetooth disconnection.** Automatic connection monitoring and analog
   fallback were added and verified with an intentional disconnect. Real stalls
   occur while the device remains connected, so reconnection logic cannot prevent
   them.

### Current assessment

The remaining behavior is most consistent with temporary back-pressure or lock
contention in the Pygame/SDL, ALSA, BlueALSA, and A2DP playback path used with this
speaker. It is not currently evidence of faulty GPIO input, Raspberry Pi power
loss, or a PiZoo process crash.

The current mitigations—GPIO debounce, serialized dedicated-channel playback,
native A2DP format, connection monitoring, and analog fallback—should remain in
place. If the delay becomes unacceptable, possible future experiments include a
separate restartable audio worker, a different Linux Bluetooth audio backend such
as PipeWire, or a lower SBC bitrate. Those alternatives have not yet been tested.

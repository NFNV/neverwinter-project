# Postmortem: UDP status false offline (Jan 2026)

## Summary
The status endpoint reported the NWN server as offline even while the container was running.
This was a false negative for availability.
It affected the public status view and operator confidence.
The server itself remained healthy throughout.

## Impact
- Status UI showed "offline" while players could still connect.
- Operators spent time double-checking logs and connectivity.
- Trust in the status indicator decreased.

## Root cause
- Backend relied on UDP query packets (GameSpy-style) as truth.
- The server did not reliably respond to those packets.
- Packet captures (tcpdump) confirmed no UDP responses in cases where the server was up.
- The health signal was tied to a protocol that is not guaranteed by NWN:EE.

## Fix
- Switched to container-truth for online/offline.
- Status backend queries Docker Engine over the unix socket.
- `/status` now reflects `nwn-ee-pw` container state.
- UDP query logic is no longer used as the online signal.

## Prevention
- Treat UDP query protocols as best-effort diagnostics, not truth.
- Prefer deterministic signals (container state) for availability.
- Consider tri-state semantics (online, offline, unknown) for future multi-signal checks.
- Document the semantics of `/status` so UI behavior is predictable.

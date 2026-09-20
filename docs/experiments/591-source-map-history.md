# Lab 591: preserve history across verified adapter filenames

Previous-attempt matching now optionally accepts adapters whose current local
output hashes match their sidecars and whose source_sha256 values match. Existing
same-filename behavior remains. Cross-filename matches require valid provenance;
missing sidecars, different source identities or modified output maps do not match.
Every summary includes adapter_map and warns that adapter builds may differ.
Restart evidence is checked against the historical attempt's own filename.

Eleven episode tests passed. Real read-only lookup for dialogue-lab586 returns the
latest dialogue attempt50–4083 followed by context-lab376 attempts46–21849 and
47–16530. No map scripts or hidden state are read into summaries. No new outcome
credit, model call, or mission launch. This repairs history continuity; improved
policy choices remain unproven.

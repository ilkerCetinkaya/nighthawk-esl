# Faz 1 — MCP el sıkışma kanıtı (Claude Code oturumu, 2026-11-09)

Orijinal PCB/şematik değiştirilmedi. Yönlendirme yapılmadı, Gerber üretilmedi.

## 1. Bağlantı durumu (Claude Code `session_connectors_status`, ham çıktı)

```
{"name":"freerouting-local","kind":"project","transport":"stdio","status":"connected","tool_count":31}
{"name":"kicad-pro","kind":"project","transport":"stdio","status":"failed","error":"MCP server \"kicad-pro\" connection timed out after 30000ms"}
```

## 2. freerouting-local — DOĞRULANDI (Claude Code'un kendi araç çağrılarıyla)

- Araç sayısı: 31 (autoroute_board, create_session, enqueue_job, upload_job_input_from_local_file, start_job, get_job_details, get_job_drc_summary, download_job_output_to_local_file, …).
- `get_system_status` yanıtı (ham):
```
{"status":200,"contentType":"application/json","body":{"status":"OK","cpu_load":40.60,"ram_used":44,"ram_available":47,"storage_available":11088,"session_count":0}}
```
- `get_system_environment` yanıtı: FreeRouting 2.5.0 (2026-10-05), Java 25.0.4.1 Eclipse Adoptium, Mac OS X aarch64, pipeline_type MCP, actor_type AGENT.
- Komut satırı argümanları (sunucudan): `--api_server.enabled=true --api_server.authentication.enabled=false --mcp_server.enabled=true --mcp_server.authentication.enabled=false --mcp_server.stdio=true --gui.enabled=false` (yalnız localhost, yerel mod).

## 3. kicad-pro — DOĞRULANMADI

Claude Code hatası (verbatim): `MCP server "kicad-pro" connection timed out after 30000ms`.

Kök neden araştırması [ÖLÇÜM] (aynı komut/env ile elle `initialize` gönderilerek):

| Yapılandırma | `initialize` yanıt süresi |
|---|---|
| `KICAD_MCP_JAVA_EXECUTABLE` + `KICAD_MCP_FREEROUTING_JAR` ikisi de tanımlı | >120 sn (yanıt yok) |
| ikisi de kaldırılmış | 33.9 sn (ilk soğuk başlangıç) |
| yalnız `KICAD_MCP_JAVA_EXECUTABLE` | 0.7 sn |
| düzeltilmiş `.mcp.json` (jar env'i kaldırıldı), 3 deneme | 0.5 / 0.5 / 0.5 sn |

Sonuç: `KICAD_MCP_FREEROUTING_JAR` ortam değişkeni kicad-mcp-pro başlangıcını fiilen kilitliyor (nedeni kaynak kodda ayrıca incelenecek); `.mcp.json` düzeltildi (jar yolu artık araç çağrısında `freerouting_jar_path` ile verilecek). Düzeltme sonrası sunucu yerelde 0.5 sn'de yanıt veriyor, **ancak Claude Code bağlantısı bu oturumda yeniden kurulmadı**. Proje sunucuları kullanıcı tarafından yeniden bağlanmalı (`/mcp` → kicad-pro → Reconnect).

## 4. Bekleyen adımlar (kicad-pro bağlanınca)

3. kicad-pro araçlarını Claude Code'dan listele.
5. `run_drc` — kopya: `sandbox/handshake/NIGHTHAWK_REVB_copy.kicad_pcb` (sha256 orijinalle aynı).
6. Sonuçları bu dosyaya ekle. Faz 2'ye ancak iki sunucu da bağımsız doğrulanınca geçilecek.

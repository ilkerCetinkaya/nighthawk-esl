# AI routing — yeniden başlatma sonrası devam planı

Durum (2026-11-09): `.mcp.json` (proje kökü) iki sunucu içeriyor: `freerouting-local` (sarmalayıcı), `kicad-pro`. Claude Code içinde el sıkışma HENÜZ doğrulanmadı.

## Düzeltilen sorun (Faz 1.3)
FreeRouting 2.5.0 MCP'si `tools/list`'te `outputSchema` bildiriyor ama `tools/call` yanıtında `structuredContent` döndürmüyor. MCP SDK istemcileri bu durumda hata veriyor ("has an output schema but did not return structured content"); stdout'taki boş satırlar zararsızdı. `fr_mcp_stdio_wrapper.py` boş satırları süzüyor ve `outputSchema`'yı kaldırıyor; resmi Python SDK ile el sıkışma + `get_system_status` doğrulandı (`sdk_handshake_test.py`). Claude Code'un kendi istemcisi ile doğrulama: yeniden başlatma sonrası.

## Yeniden başlatma sonrası ilk kontroller (Faz 1.4–1.5)
1. Claude Code'da MCP onayını kabul et; `/mcp` ile iki sunucunun "connected" olduğunu gör.
2. Claude kendi araç listesinden `freerouting-local` (31 araç) ve `kicad-pro` (builder, ~234) araçlarını listelemeli.
3. Aynı oturumda: `get_system_status` (freerouting) + `pcb_get_nets` / `run_drc` (kicad-pro) çağrıları.
4. Kanıtı `results/handshake_evidence.md` içine yaz.

## Sonraki fazlar (kopyalar üzerinde, tam kart YOK, Gerber YOK)
- Faz 2: DSN'de katman/net sınıfı/kısıt/keepout korunumu; `route_apply_ses` zaman aşımı; `-drc` kullanma; kural bağımsız doğrulama (kicad-cli DRC + özel `.kicad_dru`).
- Faz 3: L2 (In1) saf GND; L3 yalnız onaylı sinyal; RF keepout ihlali yok; ihlal yoksa kapı, varsa bağlanamayan net listesi + neden sınıflandırması. Katman kısıtı otomatik gevşetilmez.
- Faz 4: pcbnew ile programatik RF yönlendirme (`rf_route_b.py` genişletilir); JLCPCB stackup + 50 Ω geometri doğrulaması (tam geometri; yalnız genişlik yetmez).
- Faz 5: üç alt küme (A dijital, B güç/kontrol, C karışık + GND kısıtı); tamamlanma, bağlanmamış liste, via, uzunluk, süre, L2/L3 ihlali, DRC öncesi/sonrası, DSN↔SES↔PCB farkı.

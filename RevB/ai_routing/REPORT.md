# NIGHTHAWK REV B — AI destekli routing altyapısı: doğrulama raporu

Etiketler: [ÖLÇÜM] bu oturumda çalıştırıldı, [KAYNAK] kaynak koddan/dokümandan okundu, [VARSAYIM] test edilmedi.
Orijinal `RevB/pcb/NIGHTHAWK_REVB.kicad_pcb` değiştirilmedi (bayt bayt aynı, sha256 doğrulandı). Şematik, footprint, Gerber: dokunulmadı.

## 1. Kurulu yazılım

| Bileşen | Sürüm | Not |
|---|---|---|
| KiCad | 10.0.6 | `kicad-cli pcb export` içinde Specctra/DSN yok [ÖLÇÜM] |
| kicad-mcp-pro (oaslananka) | 4.9.0, MIT, 7 Kas 2026 | `ai_routing/.venv`, `requirements.lock.txt` ile sabit |
| FreeRouting | 2.5.0 (resmi jar, sha256 resmi indirmeyle eşleşti) | MCP sunucusu jar'ın içinde |
| Java | Temurin 25 (`GPace copy/build/tools/jre25`) | sistem java'sı 1.8, jar'ı çalıştıramaz |
| Python | 3.13.7 (venv), KiCad kendi Python'u | |

Kaynak denetimi (kicad-mcp-pro) [KAYNAK]: telemetri varsayılan kapalı; ağ kodu yalnız bileşen arama, bulut bağlayıcı ve eval adaptörlerinde; `KICAD_MCP_WORKSPACE_ROOT` ile dosya erişimi kısıtlanıyor; mod kademeleri readonly/write/manufacturing/experimental. FreeRouting MCP yerel modda 127.0.0.1'e bağlanıyor, kimlik doğrulama kapalı (yalnız localhost; ağa açılmamalı). Kart verisi hiçbir dış servise gönderilmedi.

## 2. MCP yapılandırması ve bağlantı durumu

- Önerilen yapılandırma: `ai_routing/mcp.config.proposed.json` (iki sunucu). **Henüz Claude Code'a eklenmedi**: MCP sunucuları kod çalıştırır, onayınızla `.mcp.json`'a eklenmeli; eklendikten sonra oturumun yeniden başlaması gerekir.
- Bu oturumda araçlar Claude Code'a bağlı olmadığından, aynı protokolü konuşan istemcilerle test ettim (`mcp_client.py`, `fr_client.py`).
- FreeRouting MCP: 31 araç, bağlandı [ÖLÇÜM].
- kicad-mcp-pro: `builder` profili 234, `full` 332 araç [ÖLÇÜM].

## 3. Gerçek araç yetenekleri

**FreeRouting MCP (yerel)**: oturum/iş oluşturma, DSN yükleme (`upload_job_input_from_local_file`), ayar güncelleme, başlatma, durum izleme, log, DRC özeti, SES indirme, tek adımlı `autoroute_board`. Hepsi çalıştı [ÖLÇÜM].

**kicad-mcp-pro**: 
- Okuma/denetim: net, footprint, via, stackup, empedans tahmini, DRC/ERC, kural yönetimi (`drc_rule_*`, `route_set_net_class_rules`).
- Yazma (`pcb_add_track`, `pcb_add_via`, `pcb_add_zone`, `pcb_move_footprint`, `route_single_track`…): **çalışan bir KiCad (IPC API) gerektiriyor**. `builder`/`full` profillerinde listede görünmüyor; araç kaydı bitmeden çağrılamıyor.
- Başsız yönlendirme: `route_export_dsn`, `route_autoroute_freerouting`, `route_apply_ses`.

**Canlı IPC doğrulaması** [ÖLÇÜM]: izole yapılandırma (`ai_routing/kicad_cfg`, API sunucusu açık) ile pcbnew başlatıldı; `kipy` ile KiCad 10.0.6'ya bağlanıldı, 241 footprint/125 iz/111 via/7 bölge okundu, bir iz oluşturulup geri alındı. Yani yazma yolu mümkün, ama bir KiCad süreci arka planda çalışmalı. Sizin kendi KiCad ayarlarınız değiştirilmedi.

## 4. Test sonuçları

Test kartı: orijinalin kopyası, 16 kritik olmayan net (FLASH_*, BB_EN/FB/MODE, BQ_*, CC1/CC2, ARM_WDG, LOOPS_OK, RESET_BTN), diğer net bağlantıları pad'lerden silindi (yalnızca bu 16 net yönlendirilebilir; 20 bağlantı). Taban DRC alt kümesi: `results/subset_drc_before.json`.

| | A: FreeRouting MCP (çok adımlı) | B: kicad-mcp-pro'nun FreeRouting çalıştırıcısı |
|---|---|---|
| Tamamlanma | 20/20 bağlantı (0 bağlanmamış) | 20/20 |
| Via | 17 | 17 |
| Toplam iz uzunluğu | 126.1 mm | 126.0 mm |
| FreeRouting süresi | 2.9 sn (tek adımlı: 4.3 sn) | ~30–120 sn (CLI, makine yüklüyken) |
| Tabana göre yeni DRC | +40 clearance, +17 hole_clearance | +42 clearance, +17 hole_clearance |
| Net sınıfı/kısıt koruma | **hayır** | **hayır** |

Her iki yol aynı motoru kullandığı için sonuçlar neredeyse aynı; fark yalnızca orkestrasyon. Yeni ihlallerin dökümü [ÖLÇÜM]: 29 iz **In1.Cu (GND düzlemi) üzerine çizilmiş** (zone clearance), 17 via hole_clearance, ~12 U8 (IPC) pad aralığı (0.135–0.16 mm, özel `.kicad_dru` kuralları DSN'e taşınmıyor).

## 5. Sınırlamalar ve çözülmemiş sorunlar

1. **Referans düzlemi korunmuyor.** FreeRouting In1'e sinyal çiziyor. In1'i engelleyerek (keepout, `wire_keepout`, `type power`) denedim: via'lar da engellendiğinde veya düzlem sinyal dışı bırakıldığında tamamlanma ciddi düştü (216–231 bağlanmamış, tam kartta) [ÖLÇÜM]. Tam kartta In1'i saf GND tutmak yerleşimi gevşetmeyi (kart/yerleşim kararı) gerektirebilir.
2. **kicad-mcp-pro `route_export_dsn`**: KiCad 10.0.6 CLI'sında başsız DSN yok. Araç `ok:true` döndürüp dosya yazmıyor (yalnız önceden hazırlanmış DSN'i kopyalıyor) [ÖLÇÜM]. Çözüm: pcbnew Python API'siyle `ExportSpecctraDSN` (`dsn_tools.py`, çalışıyor).
3. **kicad-mcp-pro FreeRouting komutu 2.5.0 ile uyumsuz**: `-drc` bayrağı eklenince FreeRouting yalnız DRC yapıp SES üretmiyor [ÖLÇÜM]. Ayrıca `java` yolu PATH'ten alınıyor (Java 8). Çözüm: `-drc` olmadan ve `KICAD_MCP_JAVA_EXECUTABLE` ile Java 25.
4. **`route_apply_ses`**: 100 sn'de dönmedi, nedeni belirlenemedi [ÖLÇÜM: zaman aşımı]. Yedek: `pcbnew.ImportSpecctraSES` (çalışıyor, `dsn_tools.py`).
5. **kicad-mcp-pro araç kaydı yavaş**: bu makinede `experimental`/`agent_full` kipinde ilk çağrıda 30 sn bütçesini aşıyor, bazen 9 dakikada bitmiyor (`ToolRegistrationTimeoutError`). Makine yüklüyken (başka uygulamalar CPU'da) daha kötü. `pcb_get_stackup`/`pcb_get_impedance_for_trace` bu yüzden **test edilemedi**.
6. **FreeRouting MCP şema hatası**: `autoroute_board` şeması `body.filePath` diyor, sunucu `body.file_path` bekliyor [ÖLÇÜM]. Çok adımlı araçlarda `path.jobId` / `body` sarmalayıcıları gerekiyor.
7. **FreeRouting MCP stdout'ta boş satırlar yazıyor**: resmi Python MCP SDK istemcisi (mcp 2.3.0) bu yüzden çağrıları askıda bırakıyor, ham JSON-RPC çalışıyor. Claude Code'un kendi istemcisiyle davranış **test edilemedi** [VARSAYIM].
8. Yönlendirme sınıfları (2.4 GHz, 868 MHz, NFC…) için `route_set_net_class_rules` yalnız `.kicad_dru` yazıyor; FreeRouting'in DSN'inde genişlik/boşluk sınıfı olarak taşınmıyor. Empedans, referans düzlemi sürekliliği ve geri dönüş akımı otomatik yönlendiricide **modellenmiyor**; geometrik DRC'ye uyması RF doğruluğu anlamına gelmez.

## 6. Önerilen tam kart mimarisi

1. **RF yolları: elle/betikle, kilitli** (şu anki `rf_route_b.py` yaklaşımı). Genişlik JLCPCB stackup hesabından (0.359 mm L1/L2), via çitleri ve RF kalkanı sınırı elle; autorouter'a girmez.
2. **Sınıflara ayırma**: DSN'e göndermeden önce RF/NFC/ESP32-anten/CC1352R besleme net'lerinin kilitli izleri sabit engel olarak kalır; diğer net'ler `exclude_nets`/net sınıfı ile sınıf sınıf (güç → dijital) yönlendirilir.
3. **Düzlem koruması**: In1 GND zone'u ve keepout'lar DSN'e girer; yönlendirme sonrası betik In1'deki tüm sinyal izlerini tespit eder (denetim kapısı). Tam kart için yerleşim gevşetmesi (kullanıcı kararı) gerekebilir.
4. **Zincir**: pcbnew `ExportSpecctraDSN` → FreeRouting MCP (yerel, çok adımlı iş) → `ImportSpecctraSES` → zone doldurma → `kicad-cli` DRC.
5. **Doğrulama kapıları**: DRC/ERC, bağlanmamış öğeler, In1 sinyal izi sayısı = 0, RF genişlik/empedans denetimi, keepout doğrulaması (`verify_r2.py`), netlist karşılaştırma.
6. **Canlı düzenleme gerekirse**: izole yapılandırmalı pcbnew + kicad-mcp-pro IPC araçları; kayıt gecikmesi giderilene (veya Claude Code'da test edilene) kadar betikle yönlendirme birincil kalsın.

## 7. Yeniden üretme

```
cd NIGHTHAWK_ESL/RevB/ai_routing
python3 -m venv .venv && .venv/bin/pip install -r requirements.lock.txt
KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
$KPY make_subset.py
$KPY dsn_tools.py export sandbox/testA/subset.kicad_pcb sandbox/testA/output/routing/subset.dsn
.venv/bin/python run_tests.py a route
$KPY dsn_tools.py import sandbox/testA/subset.kicad_pcb sandbox/testA/output/routing/subset_fr_mcp.ses sandbox/testA/out.kicad_pcb
$KPY measure.py sandbox/subset.kicad_pcb sandbox/testA/out.kicad_pcb
```

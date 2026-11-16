# NIGHTHAWK REV B — JLCPCB üretim dosyaları (YÖNLENDİRMESİ BİTMEMİŞ KART)

**UYARI: Bu set kullanıcının talebiyle, kartın bu haliyle çıkarıldı. Kart yönlendirilmemiş: DRC'ye göre 409 bağlanmamış bağlantı var (yalnızca RF yolları ve GND via'ları çizili). Bu kart ÇALIŞMAZ; sipariş edilirse işlevsel olmayan bir PCB gelir.** Hiçbir şey üretilmedi, ölçülmedi. Anten/RF performansı, uyumluluk veya üretime hazırlık iddiası yoktur.

Kaynak kart: `RevB/pcb/NIGHTHAWK_REVB.kicad_pcb` (kopyası `../work/`; orijinal değişmedi). Üreten betik: `RevB/manufacturing/make_fab_b.py`.

## Dosyalar
| Dosya | İçerik |
|---|---|
| `NIGHTHAWK_REVB_JLCPCB_gerbers.zip` | JLCPCB'ye yüklenecek Gerber + Excellon sürgü dosyaları (11 katman dosyası + drill + drill map) |
| `Gerber/`, `Drill/` | zip'in açık hali (Protel uzantıları, mask üzerinden silk çıkarılmış, origin: kart sol-alt = 0,0) |
| `BOM_JLCPCB.csv` | Comment, Designator, Footprint, LCSC Part Number: 181 parça, 72 satır, yalnızca tasarımda LCSC kodu olan ve DNP olmayanlar |
| `CPL_JLCPCB.csv` | Designator, Mid X, Mid Y, Layer, Rotation: BOM ile birebir aynı 181 parça (93 alt, 88 üst) |
| `CPL_rotation_audit.csv` | her parça için KiCad açısı ve uygulanan düzeltme |
| `NOT_ASSEMBLED_BY_JLCPCB.csv` | BOM/CPL dışı kalan 60 satır ve nedeni |

## Kart ayarları (JLCPCB sipariş formu)
4 katman · 80 × 50 mm (Gerber 80.1 × 50.1) · 1.6 mm · JLC04161H-7628 · siyah maske · HASL, kurşunlu (Gerber işinde `HAL SnPb`) · empedans kontrolü **seçme** (50 Ω genişlik doğrulanmış geometri değil).

## CPL açıları: nasıl hesaplandı, nelere güvenilmemeli
- Üst yüz: KiCad açısı. Alt yüz: `(180 − açı) mod 360` (kicad-jlcpcb-tools'un kullandığı biçim).
- Üzerine paket bazlı JLCPCB düzeltmesi eklendi: **topluluk veritabanı** (JLCKicadTools `cpl_rotations_db.csv`, 59 kural, kopyası `../jlc_cpl_rotation_db_JLCKicadTools.csv`). Bu JLCPCB'nin resmi tablosu **değildir**.
- Kural eşleşen: SOT-23 / SOT-23-5 / SOT-23-6 (−90), SOIC-8 (270), TSSOP-24 (270), VQFN-16 (270), JST PH (180).
- **Kural eşleşmeyen ve yönü kutuplu/önemli parçalar — JLCPCB'nin CPL önizlemesinde (DFM) mutlaka elle kontrol edin:** U1 ESP32-C3-WROOM-02, U7 CC1352R (VQFN-48), U9 TRF7970A (VQFN-32), TPS63802 (VSON-10), LED'ler, kristaller (Y1–Y3), diyotlar/ESD, IR LED ve fotodiyot (yan bakışlı, özel footprint), tact butonlar, pin header'lar.
- **J1 (USB-C):** footprint orijini kart kenarında (üretici çizimine göre), gövde merkezinde değil; kabuk arka kenarı varsayım. CPL konumu/açısı bu parça için doğrulanmadı. JLCPCB'de elle hizalayın veya elle lehimleyin.

## BOM'da olmayanlar (LCSC kodu uydurulmadı)
- **U8 Johanson IPC 0900PC15A0036**, **U12**, **J5**, **SH1 (Würth kalkan çerçevesi + kapak)**: tasarımda LCSC kodu yok; JLCPCB montaj dışı (elle/consign).
- **ANT1, ANT3**: PCB üzerindeki anten/bobin bakırı (parça değil). **TP\***: test noktası pad'leri.
- **DNP (tasarım gereği takılmayan):** RF eşleşme ve U.FL parçaları (R25, R27, R30, R31, C30–C33, C36–C38, C64, C84, L3, L4, J3, J4, J8, ANT2 868 MHz çip anten).

## Doğrulananlar
BOM ve CPL aynı 181 referansı içeriyor · tüm LCSC kodları `C` + rakam biçiminde, tasarım dosyasından alındı · CPL koordinatları kartın içinde (x 2.6–76.0, y 0–47.8 mm). DRC: bakır hatası yok (yalnız silkscreen uyarıları) ama 409 bağlanmamış bağlantı.

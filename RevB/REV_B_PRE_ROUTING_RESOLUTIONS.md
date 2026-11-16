# NIGHTHAWK REV B — Pre-routing mandatory items (durum)

Etiketler: [DS]=datasheet/çizim, [CALC]=hesap, [ASM]=varsayım, [MEAS]=ölçüm (yok).

| # | Madde | Sonuç | Kaynak |
|---|---|---|---|
| 1 | CC1352R giriş gücü | No-loss bazı: +10.5 / +4.9 / −9.5 dBm (S21 −10/−15.6/−30). 1.3 dB farkı = IPC tipik insertion loss'un eski tabloda belirtilmeden düşülmesi. Marjinler −5.5/+0.1/+14.5 dB. Zorunlu S21 testi + zaman dilimleme (ESP_RF_QUIET / CC_RF_BUSY) | [CALC], rf_coex_calc.py |
| 2 | USB-C ayak izi | HRO TYPE-C-31-M-12 üretici önerilen yerleşim çiziminden: pad sırası kart kenarından 6.86 mm, 4×0.60 + 8×0.30 pad, NPTH Ø0.6 @±2.89/5.79, kabuk slotları ±4.325. Origin = kart kenarı. Kabuk ön hattı (kenardan 0.83 mm) çizimden değil | [DS] + [ASM] kabuk ucu |
| 3 | Pil konnektörü | PHR-2 fişi 5.8×4.5×6.35 mm; kablo çentiği 6.6×4.2 mm (x 36.7–43.3), keepout 36–44×0–4.5, J2 y=9.8 | [DS] JST PHR-2 (LCSC kopyası) |
| 4 | ESP32 anten boşluğu | Hava kesimi y=15.0 (belgelenmiş 15 mm) | [DS] Espressif |
| 5 | Würth kalkan | Çerçeve 36103205S dış 20.4 / iç 20.0 / h 3.0–3.2 ±0.1, kapak 36003200S dış 20.9 / h; çerçeve datasheet durumu "Expired" (tedarik riski, alternatif şart); toplam yükseklik 3.0–3.2 + kapak ≈ çerçeve+kapak, mekanik denetimde doğrulanacak | [DS] |
| 6 | Johanson IPC | Üretici pad/maske şeklinden ölçüldü (görselden, ±0.03 mm): pad 0.86×0.34 @0.5 mm, uç pedleri 0.43×0.66 / 0.43×0.91. Ölçülmüş görsel; boyutlu çizim yok. U8 pedleri arası boşluk 0.135–0.16 mm → özel DRC kuralı 0.12 mm (JLCPCB min 0.09 mm) | [DS görsel] + [ASM] |

Sapmalar (üretici referansından): hole-to-copper kuralı 0.25→0.20 mm (USB-C üretici yerleşimi 0.20 veriyor); U8 pedleri arası min boşluk 0.12 mm.

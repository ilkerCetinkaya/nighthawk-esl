# Manufacturing notes (JLCPCB)

- Layers 4, thickness 1.6 mm, stackup JLC04161H-7628 (JLCPCB impedance page read 2026-11-07), copper 1 oz outer / 0.5 oz inner as per that stackup, surface finish ENIG recommended (declared in the board file).
- Solder mask: request black with white silkscreen; availability and price at JLCPCB were not checked.
- 50 ohm width: 0.36 mm on L1 over L2 (Hammerstad-Jensen estimate with Er 4.4, h 0.2104 mm, t 0.035 mm gives about 51 ohm bare, expected near 50 ohm with solder mask). **Not field-solved.** Confirm with the JLCPCB impedance calculator and order with impedance control if RF performance matters.
- Min via 0.6/0.3 mm, track/space 0.2/0.15 mm, DRC clean at those rules. Edge-launch SMA parts overhang the edge by design.
- Files: Manufacturing/Gerber, Manufacturing/Drill, NIGHTHAWK_JLCPCB_gerbers.zip, BOM/JLCPCB_BOM.csv, CPL/JLCPCB_CPL.csv.
- CPL: coordinates exported from the final PCB relative to the board origin; no JLCPCB rotation offsets applied. **Check every polarised part (U1, U2, U3 to U12, D2 to D5, J1, J4, J5, J7, SW1, SW2) in the JLCPCB assembly viewer.**
- Parts with low stock at the time of checking: J7 microSD (707), J2/J3 SMA (204).
- ESP32-C3-WROOM-02 antenna keepout is a rule area on all layers; the board has no copper under the antenna.
- Assembly drawings: Manufacturing/Assembly/Assembly_Top.pdf and Assembly_Bottom.pdf; 3D renders: Render_Top.png, Render_Bottom.png.

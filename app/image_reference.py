"""Reviewed AT89C51 display subsystem transcribed from the supplied schematics."""
from app.design import Design

LCD_PROMPTS = (
    "AT89C51 with an 8-bit LM016L LCD",
    "Create an AT89C51 PDIP-40 schematic with a 5 V supply and a 14-pin LM016L LCD in 8-bit write-only mode. Connect P1.0 through P1.7 to LCD D0 through D7 in order. Connect P2.1 to LCD RS and P2.2 to LCD E. Ground LCD RW. Tie EA high to use internal program memory. Add a 12 MHz crystal between XTAL1 and XTAL2 with a 33 pF capacitor from each crystal pin to ground. Add a 10 uF capacitor from 5 V to the active-high reset node and a 10 kohm resistor from reset to ground. Use a 10 kohm potentiometer between 5 V and ground and connect its wiper to LCD contrast. Keep the LCD data lines in order and show power, reset, and oscillator as separate groups.",
)


def at89c51_lcd():
    components = [
        ('U1', 'at89c51_pdip40', 'AT89C51', 680, 295),
        ('LCD1', 'lm016l', 'LM016L / 8-bit', 1280, 247),
        ('X2', 'crystal', '12 MHz', 210, 210),
        ('C1', 'capacitor_polarized', '10 uF', 210, 800),
        ('C2', 'capacitor', '33 pF', 210, 410),
        ('C3', 'capacitor', '33 pF', 210, 600),
        ('R1', 'resistor', '10 kohm', 210, 1000),
        ('RV1', 'potentiometer', '10 kohm', 1280, 750),
        ('V1', 'dc_source', '5 V', 710, 125),
    ]
    nets = {
        **{f'D{i}': [f'U1.{i+1}', f'LCD1.{i+7}'] for i in range(8)},
        'RS': ['U1.22', 'LCD1.4'],
        'EN': ['U1.23', 'LCD1.6'],
        'VCC': ['V1.+', 'U1.40', 'U1.31', 'LCD1.2', 'C1.+', 'RV1.1'],
        'GND': ['V1.-', 'U1.20', 'LCD1.1', 'LCD1.5', 'C2.2', 'C3.2', 'R1.2', 'RV1.2'],
        'CONTRAST': ['RV1.W', 'LCD1.3'],
        'RST': ['U1.9', 'C1.-', 'R1.1'],
        'XTAL1': ['U1.19', 'X2.1', 'C2.1'],
        'XTAL2': ['U1.18', 'X2.2', 'C3.1'],
    }
    return Design(
        title='AT89C51 and 8-bit LM016L display',
        components=[dict(ref=ref,part=part,value=value,position=dict(x=x,y=y))
                    for ref,part,value,x,y in components],
        nets=[dict(name=name,pins=pins) for name,pins in nets.items()],
        notes=[
            'Reviewed display subsystem. RS and EN use the first 8051/LCD image. The full fan diagram uses different application-specific assignments.',
            'The crystal frequency and adjustable contrast are design choices. Check crystal load, supply decoupling, reset timing and LCD contrast against the hardware before building.',
            'Firmware must initialize the display in 8-bit write-only mode. This draft has not been simulated.',
        ],
    )

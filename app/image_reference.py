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


ADC_PROMPT = (
    "Create an AT89C51 temperature sensing circuit with an LM35 and ADC0804LCN. "
    "Use a common 5 V supply. Connect LM35 VOUT to ADC VIN+, and ground VIN-, AGND, DGND and CS. "
    "Connect ADC DB0 through DB7 to AT89C51 P2.0 through P2.7 in order. "
    "Connect ADC RD to P3.7, WR to P3.6, and INTR to P3.2. "
    "Put a 10 kohm resistor between CLK R and CLK IN and a 150 pF capacitor from CLK IN to ground. "
    "Keep the existing AT89C51 12 MHz crystal, two 33 pF load capacitors, and active-high RC reset. "
    "Leave VREF/2 open for the supply-derived reference and keep clock and analog lines grouped."
)


def at89c51_adc():
    """Image-derived sensor bus with an explicitly chosen handshake pin map."""
    base = at89c51_lcd()
    components = [c for c in base.components if c.ref not in {'LCD1','RV1'}]
    components.extend([
        dict(ref='U2',part='adc0804lcn',value='ADC0804LCN',position={'x':1350,'y':295}),
        dict(ref='U3',part='lm35',value='LM35',position={'x':1980,'y':295}),
        dict(ref='R2',part='resistor',value='10 kohm',position={'x':1980,'y':550}),
        dict(ref='C4',part='capacitor',value='150 pF',position={'x':1980,'y':800}),
    ])
    keep = {'RST','XTAL1','XTAL2','VCC','GND'}
    nets = {n.name:[p for p in n.pins if not p.startswith(('LCD1.','RV1.'))]
            for n in base.nets if n.name in keep}
    nets['VCC'].extend(['U2.20','U3.VS'])
    nets['GND'].extend(['U2.1','U2.7','U2.8','U2.10','U3.GND','C4.2'])
    nets.update({f'DB{i}':[f'U2.{18-i}',f'U1.{21+i}'] for i in range(8)})
    nets.update({
        'ADC_RD':['U1.17','U2.2'], 'ADC_WR':['U1.16','U2.3'],
        'ADC_INTR':['U2.5','U1.12'], 'TEMP_ANALOG':['U3.VOUT','U2.6'],
        'ADC_CLK_IN':['U2.4','R2.1','C4.1'], 'ADC_CLK_R':['U2.19','R2.2'],
    })
    return Design(title='AT89C51 temperature acquisition with ADC0804',
                  components=components,nets=[dict(name=n,pins=p) for n,p in nets.items()],
                  notes=[
                      'Sensor, parallel data bus and RC oscillator are adapted from the temperature-controller image. RD, WR and INTR assignments are explicit choices for this reference.',
                      'VREF/2 is left open to use the ADC internal divider. Verify conversion span and calibration. Add local supply bypassing and validate grounding with the actual hardware.',
                      'Firmware must sequence WR, monitor INTR and read Port 2 with RD. Motor control, display and simulated readings are outside this subsystem.',
                  ])

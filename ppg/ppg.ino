#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"
#include <U8g2lib.h>

// OLED: Page buffer version for low RAM boards
U8G2_SSD1306_128X64_NONAME_1_HW_I2C display(U8G2_R0, U8X8_PIN_NONE);

MAX30105 particleSensor;

const byte RATE_SIZE = 4;
byte rates[RATE_SIZE];
byte rateSpot = 0;
long lastBeat = 0;

float beatsPerMinute;
int beatAvg;

void setup() {
  Serial.begin(115200);
  while (!Serial);
  Serial.println("Setup begin");

  display.begin();
  display.setFont(u8g2_font_ncenB14_tr);

  display.firstPage();
  do {
    display.drawStr(0, 24, "Starting...");
  } while (display.nextPage());

  delay(1000);

  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) {
    Serial.println("Sensor fail");
    display.firstPage();
    do {
      display.drawStr(0, 24, "Sensor Error!");
    } while (display.nextPage());
    while (1);
  }

  Serial.println("Sensor OK");
  particleSensor.setup();
  particleSensor.setPulseAmplitudeRed(0x3F);
  particleSensor.setPulseAmplitudeGreen(0);

  display.firstPage();
  do {
    display.drawStr(0, 24, "Place finger");
  } while (display.nextPage());
}

void loop() {
  long irValue = particleSensor.getIR();

  if (checkForBeat(irValue)) {
    long delta = millis() - lastBeat;
    lastBeat = millis();

    beatsPerMinute = 60 / (delta / 1000.0);

    if (beatsPerMinute < 255 && beatsPerMinute > 20) {
      rates[rateSpot++] = (byte)beatsPerMinute;
      rateSpot %= RATE_SIZE;

      beatAvg = 0;
      for (byte x = 0; x < RATE_SIZE; x++)
        beatAvg += rates[x];
      beatAvg /= RATE_SIZE;

      // Show BPM
      char bpmText[16];
      sprintf(bpmText, "BPM: %d", beatAvg);

      display.firstPage();
      do {
        display.drawStr(0, 24, bpmText);
      } while (display.nextPage());
    }
  }

  // Debug output
  Serial.print("IR=");
  Serial.print(irValue);
  Serial.print(" BPM=");
  Serial.print(beatsPerMinute);
  Serial.print(" Avg BPM=");
  Serial.print(beatAvg);
  if (irValue < 50000)
    Serial.print(" (No finger)");
  Serial.println();
}

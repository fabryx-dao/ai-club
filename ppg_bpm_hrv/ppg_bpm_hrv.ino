#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"
#include <U8g2lib.h>

// OLED: Page-buffered for low RAM boards
U8G2_SSD1306_128X64_NONAME_1_HW_I2C display(U8G2_R0, U8X8_PIN_NONE);

// MAX30102 setup
MAX30105 particleSensor;

const byte RATE_SIZE = 4;
byte rates[RATE_SIZE];
byte rateSpot = 0;
long lastBeat = 0;

float beatsPerMinute;
int beatAvg;

// For HRV (SDNN)
unsigned long ibiValues[RATE_SIZE];  // inter-beat intervals in ms

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
    long now = millis();
    long delta = now - lastBeat;
    lastBeat = now;

    beatsPerMinute = 60 / (delta / 1000.0);

    if (beatsPerMinute < 255 && beatsPerMinute > 20) {
      rates[rateSpot] = (byte)beatsPerMinute;
      ibiValues[rateSpot] = delta; // store IBI
      rateSpot = (rateSpot + 1) % RATE_SIZE;

      // Average BPM
      beatAvg = 0;
      for (byte x = 0; x < RATE_SIZE; x++)
        beatAvg += rates[x];
      beatAvg /= RATE_SIZE;

      // HRV (SDNN)
      float mean = 0;
      for (byte i = 0; i < RATE_SIZE; i++) mean += ibiValues[i];
      mean /= RATE_SIZE;

      float variance = 0;
      for (byte i = 0; i < RATE_SIZE; i++)
        variance += (ibiValues[i] - mean) * (ibiValues[i] - mean);
      variance /= RATE_SIZE;
      int hrv = sqrt(variance); // HRV in ms

      // Display both
      char bpmText[16];
      sprintf(bpmText, "BPM: %d", beatAvg);

      char hrvText[16];
      sprintf(hrvText, "HRV: %dms", hrv);

      display.firstPage();
      do {
        display.drawStr(0, 24, bpmText);
        display.drawStr(0, 48, hrvText);
      } while (display.nextPage());

      // Serial debug
      Serial.print("BPM=");
      Serial.print(beatAvg);
      Serial.print(" HRV=");
      Serial.print(hrv);
      Serial.print(" IR=");
      Serial.println(irValue);
    }
  }
}

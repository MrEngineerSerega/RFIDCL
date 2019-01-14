#include <Arduino.h>
#include <SPI.h>
#include <MFRC522.h>

#define RST_PIN		9		//
#define SS_PIN		10		//

MFRC522 mfrc522(SS_PIN, RST_PIN);	// Create MFRC522 instance

void setup() {
    Serial.begin(9600);		// Initialize serial communications with the PC
    while (!Serial);		// Do nothing if no serial port is opened (added for Arduinos based on ATMEGA32U4)
    SPI.begin();			// Init SPI bus
    mfrc522.PCD_Init();		// Init MFRC522
    Serial.println(F("Scan PICC to see UID, type, and data blocks..."));
}

void loop() {
    // Look for new cards
    if ( ! mfrc522.PICC_IsNewCardPresent()) {
        return;
    }

    // Select one of the cards
    if ( ! mfrc522.PICC_ReadCardSerial()) {
        return;
    }

    // mfrc522.PICC_UIDToSerial(&(mfrc522.uid));
    mfrc522.PICC_DumpToSerial(&(mfrc522.uid));
}

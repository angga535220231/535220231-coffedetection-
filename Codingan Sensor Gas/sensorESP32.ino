#include <WiFi.h>
#include <WebServer.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// ===== WIFI =====
const char* ssid = "A";
const char* password = "ayam1212";

WebServer server(80);

// ===== LCD =====
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ===== SENSOR =====
const int mq2Pin   = 34;
const int mq135Pin = 35;
const int mq3Pin   = 32;

// ===== CONTROL SYSTEM =====
bool systemActive = true;

// =====================================================
// FUNCTION KUALITAS GAS
// =====================================================
String kualitasGas(int nilai) {

  if (nilai < 800) {
    return "SANGAT BAIK";
  }
  else if (nilai < 1500) {
    return "BAIK";
  }
  else if (nilai < 2500) {
    return "SEDANG";
  }
  else if (nilai < 3500) {
    return "BURUK";
  }
  else {
    return "SNGT BURUK";
  }
}

// =====================================================
// HTML WEBSITE
// =====================================================
String HTMLpage() {

  int val_mq2   = analogRead(mq2Pin);
  int val_mq135 = analogRead(mq135Pin);
  int val_mq3   = analogRead(mq3Pin);

  String html = "<!DOCTYPE html><html>";
  html += "<head>";
  html += "<meta name='viewport' content='width=device-width, initial-scale=1'>";
  html += "<meta http-equiv='refresh' content='2'>";
  html += "<title>ESP32 GAS MONITOR</title>";

  html += "<style>";
  html += "body{font-family:Arial;text-align:center;background:#f2f2f2;}";
  html += ".card{background:white;padding:20px;margin:15px;border-radius:15px;box-shadow:0 0 10px rgba(0,0,0,0.2);}";
  html += "button{padding:15px 30px;font-size:18px;border:none;border-radius:10px;}";
  html += ".on{background:green;color:white;}";
  html += ".off{background:red;color:white;}";
  html += "</style>";

  html += "</head><body>";

  html += "<h2>ESP32 GAS MONITOR</h2>";

  html += "<div class='card'>";
  html += "<h3>Status System : ";
  html += (systemActive ? "ON" : "OFF");
  html += "</h3>";
  html += "</div>";

  html += "<div class='card'>";
  html += "<h3>MQ2</h3>";
  html += "<p>Nilai : " + String(val_mq2) + "</p>";
  html += "<p>Kualitas : " + kualitasGas(val_mq2) + "</p>";
  html += "</div>";

  html += "<div class='card'>";
  html += "<h3>MQ135</h3>";
  html += "<p>Nilai : " + String(val_mq135) + "</p>";
  html += "<p>Kualitas : " + kualitasGas(val_mq135) + "</p>";
  html += "</div>";

  html += "<div class='card'>";
  html += "<h3>MQ3</h3>";
  html += "<p>Nilai : " + String(val_mq3) + "</p>";
  html += "<p>Kualitas : " + kualitasGas(val_mq3) + "</p>";
  html += "</div>";

  html += "<a href='/on'>";
  html += "<button class='on'>ON</button>";
  html += "</a>";

  html += "<br><br>";

  html += "<a href='/off'>";
  html += "<button class='off'>OFF</button>";
  html += "</a>";

  html += "</body></html>";

  return html;
}

// =====================================================
// HANDLER WEB
// =====================================================
void handleRoot() {
  server.send(200, "text/html", HTMLpage());
}

void handleOn() {

  systemActive = true;

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("SYSTEM ON");

  server.send(200, "text/html", HTMLpage());
}

void handleOff() {

  systemActive = false;

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("SYSTEM OFF");

  server.send(200, "text/html", HTMLpage());
}

// =====================================================
// SETUP
// =====================================================
void setup() {

  Serial.begin(115200);

  // I2C LCD
  Wire.begin(21, 22);

  // LCD
  lcd.init();
  lcd.backlight();

  lcd.setCursor(0, 0);
  lcd.print("Connecting WiFi");

  // WIFI
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi Connected");
  Serial.println(WiFi.localIP());

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("WiFi Connected");

  lcd.setCursor(0, 1);
  lcd.print(WiFi.localIP());

  delay(3000);

  // ROUTING
  server.on("/", handleRoot);
  server.on("/on", handleOn);
  server.on("/off", handleOff);

  // START SERVER
  server.begin();

  Serial.println("Web Server Started");
}

// =====================================================
// LOOP
// =====================================================
void loop() {

  server.handleClient();

  // Jika system OFF
  if (!systemActive) {
    delay(500);
    return;
  }

  // BACA SENSOR
  int val_mq2   = analogRead(mq2Pin);
  int val_mq135 = analogRead(mq135Pin);
  int val_mq3   = analogRead(mq3Pin);

  // SERIAL MONITOR
  Serial.print("MQ2: ");
  Serial.print(val_mq2);

  Serial.print(" | MQ135: ");
  Serial.print(val_mq135);

  Serial.print(" | MQ3: ");
  Serial.println(val_mq3);

  // =====================================================
  // MQ2
  // =====================================================
  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print("MQ2:");
  lcd.print(val_mq2);

  lcd.setCursor(0, 1);
  lcd.print(kualitasGas(val_mq2));

  delay(1500);

  // =====================================================
  // MQ135
  // =====================================================
  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print("MQ135:");
  lcd.print(val_mq135);

  lcd.setCursor(0, 1);
  lcd.print(kualitasGas(val_mq135));

  delay(1500);

  // =====================================================
  // MQ3
  // =====================================================
  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print("MQ3:");
  lcd.print(val_mq3);

  lcd.setCursor(0, 1);
  lcd.print(kualitasGas(val_mq3));

  delay(1500);
}
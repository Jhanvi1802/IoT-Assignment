#include <WiFi.h>
#include <PubSubClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>

#define TEMP_PIN 4
#define MOIST_PIN 34
#define CO2_PIN 35

const char* ssid = "Wokwi-GUEST";
const char* password = "";

const char* mqttServer = "broker.emqx.io";
const int   mqttPort   = 1883;
const char* dataTopic = "sensor1/data";
const char* alertTopic = "sensor1/alert";

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
OneWire oneWire(TEMP_PIN);
DallasTemperature tempSensor(&oneWire);

unsigned long lastPublish = 0;
unsigned long lastStore = 0;

struct SensorData {
  unsigned long timeStamp;
  float temp;
  float moisture;
  float co2;
};

SensorData dataLog[96];
int logPtr = 0;

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  WiFi.begin(ssid, password);
  unsigned long startTime = millis();

  while (WiFi.status() != WL_CONNECTED && millis() - startTime < 8000) {
    delay(200);
  }
}

void connectMQTT() {
  if (mqttClient.connected()) return;

  mqttClient.setServer(mqttServer, mqttPort);
  unsigned long startTime = millis();

  while (!mqttClient.connected() && millis() - startTime < 5000) {
    mqttClient.connect("esp32_node");
    delay(300);
  }
}

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  connectWiFi();
  connectMQTT();
  tempSensor.begin();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWiFi();
  if (!mqttClient.connected()) connectMQTT();
  mqttClient.loop();

  unsigned long now = millis();

  if (now - lastPublish >= 2000) {
    lastPublish = now;

    tempSensor.requestTemperatures();
    float temperature = tempSensor.getTempCByIndex(0);
    float moisture = map(analogRead(MOIST_PIN), 0, 4095, 0, 100);
    float co2 = map(analogRead(CO2_PIN), 0, 4095, 0, 1000);

    char payload[150];
    snprintf(payload, sizeof(payload),
             "{\"temp\":%.1f,\"moisture\":%.1f,\"co2\":%.1f}",
             temperature, moisture, co2);

    mqttClient.publish(dataTopic, payload);
    Serial.println(payload);

    bool sendAlert = false;
    char alertMsg[150];

    if (temperature < 5 || temperature > 120) {
      snprintf(alertMsg, sizeof(alertMsg),
               "{\"alert\":\"temperature_out_of_range\",\"value\":%.1f}", temperature);
      sendAlert = true;
    }
    else if (moisture < 10 || moisture > 70) {
      snprintf(alertMsg, sizeof(alertMsg),
               "{\"alert\":\"moisture_out_of_range\",\"value\":%.1f}", moisture);
      sendAlert = true;
    }
    else if (co2 < 200 || co2 > 800) {
      snprintf(alertMsg, sizeof(alertMsg),
               "{\"alert\":\"co2_out_of_range\",\"value\":%.1f}", co2);
      sendAlert = true;
    }

    if (sendAlert) {
      mqttClient.publish(alertTopic, alertMsg);
      Serial.println(alertMsg);
    }
  }

  if (now - lastStore >= 900000) {   // 15 minutes
    lastStore = now;

    tempSensor.requestTemperatures();
    float temperature = tempSensor.getTempCByIndex(0);
    float moisture = map(analogRead(MOIST_PIN), 0, 4095, 0, 100);
    float co2 = map(analogRead(CO2_PIN), 0, 4095, 0, 1000);

    if (logPtr >= 96) logPtr = 0;

    dataLog[logPtr].timeStamp = millis();
    dataLog[logPtr].temp = temperature;
    dataLog[logPtr].moisture = moisture;
    dataLog[logPtr].co2 = co2;

    logPtr++;
  }
}

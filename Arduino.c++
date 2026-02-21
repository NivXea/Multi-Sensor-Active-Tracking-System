#define TRIG 9
#define ECHO 10

float readDistanceCM()
{
  digitalWrite(TRIG, LOW);
  delayMicroseconds(5);

  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);

  long duration = pulseIn(ECHO, HIGH, 30000);
  return duration * 0.0343 / 2;
}

void setup()
{
  Serial.begin(9600);
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
}

void loop()
{
  float d = readDistanceCM();

  if(d > 0 && d < 30)
    Serial.println("ALERT");
  else
    Serial.println("SAFE");

  delay(100);
}

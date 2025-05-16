#define PLANT_ADC_PIN 26
#define RLD_ADC_PIN   27

// === DSP parameters ===
const float alpha = 0.01;    // Baseline tracking
const float decay = 0.9995;
const float env_alpha = 0.1;
const float mean_alpha = 0.01;
const float var_alpha = 0.01;
const float mu = 0.03;

const unsigned int SAMPLE_RATE = 200;
const unsigned long SAMPLE_INTERVAL = 1000000UL / SAMPLE_RATE;

unsigned long lastMicros = 0;
unsigned long global_time = 0;

// === LMS DSP state ===
float plant_baseline = 0.0;
float rld_baseline = 0.0;

float lms_filtered = 0.0;
float lms_w = 0.0;
float prev_lms = 0.0;
float max_amp_lms = 0.1;

float env_lms = 0.0, mean_lms = 0.0, var_lms = 0.0;

void setup() {
  Serial.begin(115200);
  //while (!Serial);
  analogReadResolution(10); // 10-bit ADC
}

void loop() {
  if (micros() - lastMicros < SAMPLE_INTERVAL) return;

  unsigned long now = micros();
  float dt = (now - lastMicros) / 1000000.0;
  lastMicros = now;

  // === Read ADC ===
  float plant_v = (analogRead(PLANT_ADC_PIN) / 1023.0) * 3.3;
  float rld_v   = (analogRead(RLD_ADC_PIN)   / 1023.0) * 3.3;

  // === Adaptive DC removal ===
  plant_baseline += alpha * (plant_v - plant_baseline);
  rld_baseline   += alpha * (rld_v   - rld_baseline);

  float plant_centered = plant_v - plant_baseline;
  float rld_centered   = rld_v   - rld_baseline;

  // === LMS Adaptive Filter ===
  float estimate = lms_w * rld_centered;
  float error = plant_centered - estimate;
  lms_w += mu * error * rld_centered;

  lms_filtered += 0.1 * (error - lms_filtered);
  max_amp_lms = max(max_amp_lms * decay, abs(lms_filtered));

  float norm_lms = lms_filtered / max_amp_lms;
  float rate_lms = (norm_lms - prev_lms) / dt;
  prev_lms = norm_lms;

  env_lms += env_alpha * (abs(norm_lms) - env_lms);
  mean_lms += mean_alpha * (norm_lms - mean_lms);
  float diff_lms = norm_lms - mean_lms;
  var_lms += var_alpha * (diff_lms * diff_lms - var_lms);
  float energy_lms = norm_lms * norm_lms;

  // === Serial output ===
  global_time = millis();

  Serial.print(global_time); Serial.print(" ");
  Serial.print(norm_lms, 5);     Serial.print(" ");
  Serial.print(rate_lms, 5);     Serial.print(" ");
  Serial.print(env_lms, 5);      Serial.print(" ");
  Serial.print(mean_lms, 5);     Serial.print(" ");
  Serial.print(var_lms, 5);      Serial.print(" ");
  Serial.println(energy_lms, 5);
}

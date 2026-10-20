#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/ledc.h"
#include "driver/gpio.h"
#include "esp_timer.h"
#include "esp_err.h"

// Motor 1 Pins
#define M1_RPWM_GPIO      22
#define M1_LPWM_GPIO      23
#define M1_RPWM_CHANNEL   LEDC_CHANNEL_0
#define M1_LPWM_CHANNEL   LEDC_CHANNEL_1

// Motor 2 Pins (Safe general purpose IOs)
#define M2_RPWM_GPIO      18
#define M2_LPWM_GPIO      19
#define M2_RPWM_CHANNEL   LEDC_CHANNEL_2
#define M2_LPWM_CHANNEL   LEDC_CHANNEL_3

// LEDC Peripheral Configurations
#define LEDC_TIMER        LEDC_TIMER_0
#define LEDC_MODE         LEDC_LOW_SPEED_MODE
#define LEDC_DUTY_RES     LEDC_TIMER_8_BIT   // 0 to 255
#define LEDC_FREQUENCY    5000

// #define trigpin 17
// #define echopin 16
#define ir_pin 4

// Helper function to safely update a single channel's duty cycle
static void set_channel_duty(ledc_channel_t channel, uint32_t duty) {
    ledc_set_duty(LEDC_MODE, channel, duty);
    ledc_update_duty(LEDC_MODE, channel);
}

// Drive Motor 1 safely
static void set_motor1(int speed) {
    if (speed >= 0) {
        set_channel_duty(M1_LPWM_CHANNEL, 0); 
        set_channel_duty(M1_RPWM_CHANNEL, speed);
    } else {
        set_channel_duty(M1_RPWM_CHANNEL, 0); 
        set_channel_duty(M1_LPWM_CHANNEL, -speed);
    }
}

static void set_motor2(int speed) {
    if (speed >= 0) {
        set_channel_duty(M2_LPWM_CHANNEL, 0); 
        set_channel_duty(M2_RPWM_CHANNEL, speed);
    } else {
        set_channel_duty(M2_RPWM_CHANNEL, 0); 
        set_channel_duty(M2_LPWM_CHANNEL, -speed);
    }
}

static void stop_all_motors(void) {
    set_channel_duty(M1_RPWM_CHANNEL, 0);
    set_channel_duty(M1_LPWM_CHANNEL, 0);
    set_channel_duty(M2_RPWM_CHANNEL, 0);
    set_channel_duty(M2_LPWM_CHANNEL, 0);
}
static void get_distance(){
    // set_gpio_pin 
}

// Initialize Motors and Hardware Timers
static void hardware_init(void) {
    // 1. Configure LEDC Timer
    ledc_timer_config_t ledc_timer = {
        .speed_mode       = LEDC_MODE,
        .timer_num        = LEDC_TIMER,
        .duty_resolution  = LEDC_DUTY_RES,
        .freq_hz          = LEDC_FREQUENCY,
        .clk_cfg          = LEDC_AUTO_CLK
    };
    ESP_ERROR_CHECK(ledc_timer_config(&ledc_timer));

    // 2. Configure LEDC Channels (Fixed array brackets)
    ledc_channel_config_t ledc_channels[4] = {
        {.channel = M1_RPWM_CHANNEL, .gpio_num = M1_RPWM_GPIO, .speed_mode = LEDC_MODE, .timer_sel = LEDC_TIMER, .duty = 0, .hpoint = 0},
        {.channel = M1_LPWM_CHANNEL, .gpio_num = M1_LPWM_GPIO, .speed_mode = LEDC_MODE, .timer_sel = LEDC_TIMER, .duty = 0, .hpoint = 0},
        {.channel = M2_RPWM_CHANNEL, .gpio_num = M2_RPWM_GPIO, .speed_mode = LEDC_MODE, .timer_sel = LEDC_TIMER, .duty = 0, .hpoint = 0},
        {.channel = M2_LPWM_CHANNEL, .gpio_num = M2_LPWM_GPIO, .speed_mode = LEDC_MODE, .timer_sel = LEDC_TIMER, .duty = 0, .hpoint = 0}
    };
    for (int i = 0; i < 4; i++) {
        ESP_ERROR_CHECK(ledc_channel_config(&ledc_channels[i]));
    }
}

void app_main(void) {
    hardware_init();
    printf("Hardware Initialized. Starting Motor Test Loop...\n");
    
    while (1) {
        printf("Ramping motors up...\n");
        for (int i = 0; i <= 200; i++) {
            set_motor1(i);
          set_motor2(i);
            vTaskDelay(pdMS_TO_TICKS(10)); 
        }
for (int i = 200; i >= 0; i--) {
    set_motor1(-i); 
    set_motor2(-i);
    vTaskDelay(pdMS_TO_TICKS(10)); 
}

        printf("Running at full speed...\n");
        vTaskDelay(pdMS_TO_TICKS(3000)); 
        
        printf("Stopping motors...\n");
        stop_all_motors();               
        vTaskDelay(pdMS_TO_TICKS(2000));
    }
}

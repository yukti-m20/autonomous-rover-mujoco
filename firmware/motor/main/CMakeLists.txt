idf_component_register(SRCS "mcpwm_bdc_control_example_main.c"
                       INCLUDE_DIRS "."
                       REQUIRES esp_driver_ledc esp_driver_gpio esp_timer driver)

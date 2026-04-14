# PI Benchmark Sweep

| Task | Mode | Model | Hidden Outcome | Family | Stage | Time (s) | First Submit (s) | Hidden Evals | Builds | Self-Tests | Probe | Tokens |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| filter_tank_sequence | oneshot_blind | gpt-5.4 | PASS | pass | integration | 295.1 | 217.5 | 1 | 0 | 0 | no | 164269 |
| filter_tank_sequence | oneshot_blind | gpt-5.4-mini | HOST_TEST_FAILED | host_tests | host unit tests | 336.4 | 328.1 | 1 | 0 | 0 | no | 375775 |
| filter_tank_sequence | oneshot_blind | qwen35-27b-q4km | INTEGRATION_FAILED | integration | integration | 165.1 | 84.9 | 1 | 0 | 0 | no | 172691 |
| filter_tank_sequence | oneshot_blind | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 122.8 | 119.2 | 1 | 0 | 0 | no | 169931 |
| filter_tank_sequence | oneshot_blind | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 45.0 | 37.3 | 1 | 0 | 0 | no | 201901 |
| filter_tank_sequence | oneshot_blind | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 28.7 | 24.1 | 1 | 0 | 0 | no | 171343 |
| filter_tank_sequence | oneshot_blind | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 53.5 | - | 0 | 0 | 0 | no | 1585683 |
| filter_tank_sequence | realistic_self_verify | gpt-5.4 | PASS | pass | integration | 485.2 | 433.4 | 1 | 1 | 8 | yes | 618585 |
| filter_tank_sequence | realistic_self_verify | gpt-5.4-mini | HOST_TEST_FAILED | host_tests | host unit tests | 688.9 | 680.9 | 1 | 1 | 4 | yes | 982241 |
| filter_tank_sequence | realistic_self_verify | qwen35-27b-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 3600.0 | 1459.4 | 1 | 2 | 20 | yes | 4583059 |
| filter_tank_sequence | realistic_self_verify | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 1194.8 | 1170.7 | 1 | 6 | 44 | yes | 8235289 |
| filter_tank_sequence | realistic_self_verify | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 857.3 | 549.5 | 3 | 8 | 11 | yes | 4713204 |
| filter_tank_sequence | realistic_self_verify | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 416.0 | 392.6 | 2 | 4 | 7 | no | 3428566 |
| filter_tank_sequence | realistic_self_verify | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 353.1 | - | 0 | 15 | 1 | yes | 5139502 |
| filter_tank_sequence | ci_red_green | gpt-5.4 | PASS | pass | integration | 1236.1 | 406.0 | 5 | 5 | 10 | yes | 2263677 |
| filter_tank_sequence | ci_red_green | gpt-5.4-mini | HOST_TEST_FAILED | host_tests | host unit tests | 1861.5 | 425.9 | 6 | 2 | 16 | yes | 3755986 |
| filter_tank_sequence | ci_red_green | qwen35-27b-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 3600.0 | 2478.2 | 4 | 8 | 22 | yes | 8184885 |
| filter_tank_sequence | ci_red_green | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 1277.5 | 956.0 | 7 | 6 | 18 | yes | 4185241 |
| filter_tank_sequence | ci_red_green | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 570.8 | 252.8 | 9 | 11 | 1 | yes | 4351238 |
| filter_tank_sequence | ci_red_green | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 1980.3 | 334.4 | 113 | 7 | 21 | yes | 22097052 |
| filter_tank_sequence | ci_red_green | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3427.5 | - | 0 | 210 | 0 | authored | 37254780 |
| filter_tank_sequence | oracle_full | gpt-5.4 | PASS | pass | integration | 705.7 | 291.4 | 3 | 3 | 5 | yes | 1198137 |
| filter_tank_sequence | oracle_full | gpt-5.4-mini | INTEGRATION_FAILED | integration | integration | 1718.3 | 533.1 | 5 | 3 | 10 | yes | 4354171 |
| filter_tank_sequence | oracle_full | qwen35-27b-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 3445.6 | 1389.2 | 16 | 4 | 12 | yes | 5067564 |
| filter_tank_sequence | oracle_full | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 2203.3 | 987.8 | 19 | 5 | 15 | yes | 5446329 |
| filter_tank_sequence | oracle_full | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 2373.4 | 2175.2 | 10 | 8 | 15 | yes | 9956535 |
| filter_tank_sequence | oracle_full | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 430.8 | 117.2 | 6 | 1 | 1 | authored | 2339803 |
| filter_tank_sequence | oracle_full | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.0 | - | 0 | 0 | 0 | no | 66815457 |
| mixing_tank_fill_heat | oneshot_blind | gpt-5.4 | PASS | pass | integration | 206.1 | 133.8 | 1 | 0 | 0 | no | 141234 |
| mixing_tank_fill_heat | oneshot_blind | gpt-5.4-mini | HOST_TEST_FAILED | host_tests | host unit tests | 184.3 | 175.0 | 1 | 0 | 0 | no | 280293 |
| mixing_tank_fill_heat | oneshot_blind | qwen35-27b-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 133.3 | 120.8 | 1 | 0 | 0 | no | 197176 |
| mixing_tank_fill_heat | oneshot_blind | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 29.9 | 24.7 | 1 | 0 | 0 | no | 158051 |
| mixing_tank_fill_heat | oneshot_blind | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 100.2 | 86.2 | 1 | 0 | 0 | no | 514811 |
| mixing_tank_fill_heat | oneshot_blind | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 20.9 | 17.9 | 1 | 0 | 0 | no | 66321 |
| mixing_tank_fill_heat | oneshot_blind | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 55.5 | 50.6 | 0 | 0 | 0 | no | 1221984 |
| mixing_tank_fill_heat | realistic_self_verify | gpt-5.4 | PASS | pass | integration | 393.5 | 344.4 | 1 | 1 | 1 | yes | 253398 |
| mixing_tank_fill_heat | realistic_self_verify | gpt-5.4-mini | INTEGRATION_FAILED | integration | integration | 410.0 | 257.4 | 2 | 2 | 3 | yes | 641651 |
| mixing_tank_fill_heat | realistic_self_verify | qwen35-27b-q4km | PASS | pass | integration | 2453.7 | 2022.0 | 2 | 7 | 31 | yes | 5919091 |
| mixing_tank_fill_heat | realistic_self_verify | qwen35-35b-a3b-ud-q4km | INTEGRATION_FAILED | integration | integration | 790.8 | 657.0 | 2 | 5 | 25 | yes | 3695025 |
| mixing_tank_fill_heat | realistic_self_verify | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 2220.3 | 1690.2 | 77 | 7 | 44 | yes | 17273061 |
| mixing_tank_fill_heat | realistic_self_verify | qwen35-4b-ud-q4kxl | INTEGRATION_FAILED | integration | integration | 1091.7 | 840.7 | 3 | 0 | 40 | authored | 9595995 |
| mixing_tank_fill_heat | realistic_self_verify | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 1578.9 | - | 0 | 3 | 3 | no | 71209021 |
| mixing_tank_fill_heat | ci_red_green | gpt-5.4 | PASS | pass | integration | 282.1 | 234.9 | 1 | 1 | 1 | yes | 195107 |
| mixing_tank_fill_heat | ci_red_green | gpt-5.4-mini | PASS | pass | integration | 330.4 | 279.8 | 1 | 1 | 1 | yes | 365896 |
| mixing_tank_fill_heat | ci_red_green | qwen35-27b-q4km | INTEGRATION_FAILED | integration | integration | 3303.7 | 1094.2 | 13 | 11 | 15 | yes | 4831199 |
| mixing_tank_fill_heat | ci_red_green | qwen35-35b-a3b-ud-q4km | INTEGRATION_FAILED | integration | integration | 2840.1 | 718.6 | 13 | 8 | 20 | yes | 9726428 |
| mixing_tank_fill_heat | ci_red_green | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 1032.5 | 862.0 | 4 | 6 | 36 | yes | 7702383 |
| mixing_tank_fill_heat | ci_red_green | qwen35-4b-ud-q4kxl | PASS | pass | integration | 463.0 | 375.4 | 2 | 5 | 3 | no | 3993579 |
| mixing_tank_fill_heat | ci_red_green | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.0 | - | 0 | 2 | 8 | authored | 192103069 |
| mixing_tank_fill_heat | oracle_full | gpt-5.4 | PASS | pass | integration | 383.4 | 338.1 | 1 | 1 | 2 | yes | 426597 |
| mixing_tank_fill_heat | oracle_full | gpt-5.4-mini | PASS | pass | integration | 320.3 | 271.1 | 1 | 1 | 1 | yes | 358274 |
| mixing_tank_fill_heat | oracle_full | qwen35-27b-q4km | PASS | pass | integration | 1336.3 | 1254.5 | 1 | 3 | 9 | yes | 1801795 |
| mixing_tank_fill_heat | oracle_full | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 997.6 | 287.4 | 6 | 8 | 15 | authored | 5950032 |
| mixing_tank_fill_heat | oracle_full | qwen35-9b-ud-q4kxl | INTEGRATION_FAILED | integration | integration | 2375.3 | 1940.2 | 7 | 4 | 22 | yes | 9689398 |
| mixing_tank_fill_heat | oracle_full | qwen35-4b-ud-q4kxl | INTEGRATION_FAILED | integration | integration | 1586.9 | 696.8 | 21 | 6 | 11 | yes | 10200038 |
| mixing_tank_fill_heat | oracle_full | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 523.9 | - | 0 | 2 | 1 | no | 21834556 |
| pressure_vessel_interlock | oneshot_blind | gpt-5.4 | PASS | pass | integration | 162.8 | 99.0 | 1 | 0 | 0 | no | 83745 |
| pressure_vessel_interlock | oneshot_blind | gpt-5.4-mini | PASS | pass | integration | 181.0 | 118.6 | 1 | 0 | 0 | no | 164794 |
| pressure_vessel_interlock | oneshot_blind | qwen35-27b-q4km | PASS | pass | integration | 127.7 | 59.3 | 1 | 0 | 0 | no | 171194 |
| pressure_vessel_interlock | oneshot_blind | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 18.7 | 14.6 | 1 | 0 | 0 | no | 89719 |
| pressure_vessel_interlock | oneshot_blind | qwen35-9b-ud-q4kxl | PASS | pass | integration | 244.7 | 181.5 | 1 | 0 | 0 | no | 778790 |
| pressure_vessel_interlock | oneshot_blind | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 20.0 | 17.6 | 1 | 0 | 0 | no | 121230 |
| pressure_vessel_interlock | oneshot_blind | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.0 | - | 0 | 0 | 0 | no | 116911969 |
| pressure_vessel_interlock | realistic_self_verify | gpt-5.4 | PASS | pass | integration | 387.8 | 347.8 | 1 | 1 | 1 | yes | 308355 |
| pressure_vessel_interlock | realistic_self_verify | gpt-5.4-mini | PASS | pass | integration | 366.2 | 326.0 | 1 | 2 | 2 | yes | 663120 |
| pressure_vessel_interlock | realistic_self_verify | qwen35-27b-q4km | PASS | pass | integration | 1419.7 | 1370.9 | 1 | 4 | 5 | yes | 3134546 |
| pressure_vessel_interlock | realistic_self_verify | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 1874.5 | 1867.6 | 1 | 3 | 16 | yes | 3782462 |
| pressure_vessel_interlock | realistic_self_verify | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 2279.1 | 1054.8 | 2 | 11 | 13 | yes | 9073873 |
| pressure_vessel_interlock | realistic_self_verify | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 365.6 | 329.7 | 2 | 5 | 8 | authored | 2738875 |
| pressure_vessel_interlock | realistic_self_verify | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.0 | - | 0 | 0 | 0 | no | 119947182 |
| pressure_vessel_interlock | ci_red_green | gpt-5.4 | PASS | pass | integration | 305.7 | 265.3 | 1 | 1 | 1 | yes | 345105 |
| pressure_vessel_interlock | ci_red_green | gpt-5.4-mini | PASS | pass | integration | 446.4 | 407.5 | 1 | 1 | 3 | yes | 1222655 |
| pressure_vessel_interlock | ci_red_green | qwen35-27b-q4km | PASS | pass | integration | 2748.4 | 521.3 | 3 | 2 | 19 | yes | 3515603 |
| pressure_vessel_interlock | ci_red_green | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 2694.5 | 2656.1 | 1 | 3 | 46 | yes | 5822306 |
| pressure_vessel_interlock | ci_red_green | qwen35-9b-ud-q4kxl | PASS | pass | integration | 2026.8 | 1950.2 | 2 | 9 | 17 | yes | 10671257 |
| pressure_vessel_interlock | ci_red_green | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 3600.0 | 883.5 | 14 | 6 | 291 | authored | 8910300 |
| pressure_vessel_interlock | ci_red_green | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.0 | - | 0 | 0 | 0 | authored | 165130946 |
| pressure_vessel_interlock | oracle_full | gpt-5.4 | PASS | pass | integration | 283.8 | 233.8 | 1 | 1 | 1 | yes | 254150 |
| pressure_vessel_interlock | oracle_full | gpt-5.4-mini | PASS | pass | integration | 492.3 | 448.6 | 1 | 2 | 4 | yes | 872724 |
| pressure_vessel_interlock | oracle_full | qwen35-27b-q4km | PASS | pass | integration | 2191.5 | 1357.6 | 4 | 5 | 11 | yes | 4495757 |
| pressure_vessel_interlock | oracle_full | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 657.3 | 616.1 | 1 | 2 | 5 | authored | 1159791 |
| pressure_vessel_interlock | oracle_full | qwen35-9b-ud-q4kxl | PASS | pass | integration | 2895.3 | 1544.0 | 9 | 0 | 0 | authored | 7226916 |
| pressure_vessel_interlock | oracle_full | qwen35-4b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.0 | - | 0 | 1 | 0 | authored | 79505551 |
| pressure_vessel_interlock | oracle_full | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.0 | - | 0 | 12 | 8 | authored | 117268970 |
| tank_fill_drain | oneshot_blind | gpt-5.4 | PASS | pass | integration | 133.0 | 77.2 | 1 | 0 | 0 | no | 49579 |
| tank_fill_drain | oneshot_blind | gpt-5.4-mini | PASS | pass | integration | 157.8 | 99.1 | 1 | 0 | 0 | no | 73281 |
| tank_fill_drain | oneshot_blind | qwen35-27b-q4km | PASS | pass | integration | 102.0 | 44.1 | 1 | 0 | 0 | no | 95838 |
| tank_fill_drain | oneshot_blind | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 65.2 | 12.0 | 1 | 0 | 0 | no | 83216 |
| tank_fill_drain | oneshot_blind | qwen35-9b-ud-q4kxl | PASS | pass | integration | 77.9 | 21.2 | 1 | 0 | 0 | no | 134837 |
| tank_fill_drain | oneshot_blind | qwen35-4b-ud-q4kxl | INTEGRATION_FAILED | integration | integration | 72.3 | 15.7 | 1 | 0 | 0 | no | 133117 |
| tank_fill_drain | oneshot_blind | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 34.6 | - | 0 | 0 | 0 | no | 657056 |
| tank_fill_drain | realistic_self_verify | gpt-5.4 | PASS | pass | integration | 283.4 | 240.8 | 1 | 1 | 2 | yes | 363908 |
| tank_fill_drain | realistic_self_verify | gpt-5.4-mini | PASS | pass | integration | 586.8 | 438.6 | 2 | 2 | 11 | yes | 1638454 |
| tank_fill_drain | realistic_self_verify | qwen35-27b-q4km | PASS | pass | integration | 1672.5 | 1183.5 | 3 | 3 | 8 | yes | 2497527 |
| tank_fill_drain | realistic_self_verify | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 1141.2 | 1108.2 | 1 | 3 | 28 | yes | 4795748 |
| tank_fill_drain | realistic_self_verify | qwen35-9b-ud-q4kxl | PASS | pass | integration | 444.0 | 410.1 | 1 | 3 | 3 | yes | 1310596 |
| tank_fill_drain | realistic_self_verify | qwen35-4b-ud-q4kxl | PASS | pass | integration | 1415.2 | 1382.7 | 1 | 3 | 67 | yes | 3627070 |
| tank_fill_drain | realistic_self_verify | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.0 | - | 0 | 1 | 7 | authored | 128325804 |
| tank_fill_drain | ci_red_green | gpt-5.4 | PASS | pass | integration | 451.6 | 410.6 | 1 | 1 | 3 | yes | 429903 |
| tank_fill_drain | ci_red_green | gpt-5.4-mini | PASS | pass | integration | 290.9 | 258.3 | 1 | 1 | 3 | yes | 463888 |
| tank_fill_drain | ci_red_green | qwen35-27b-q4km | PASS | pass | integration | 1118.5 | 1078.3 | 1 | 3 | 7 | yes | 1487341 |
| tank_fill_drain | ci_red_green | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 723.5 | 691.9 | 1 | 2 | 7 | yes | 1754081 |
| tank_fill_drain | ci_red_green | qwen35-9b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.0 | - | 0 | 1 | 2 | yes | 326777 |
| tank_fill_drain | ci_red_green | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 1884.5 | 296.5 | 128 | 8 | 24 | authored | 39024659 |
| tank_fill_drain | ci_red_green | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.0 | - | 0 | 4 | 25 | yes | 128789476 |
| tank_fill_drain | oracle_full | gpt-5.4 | PASS | pass | integration | 380.3 | 332.9 | 1 | 1 | 5 | yes | 314100 |
| tank_fill_drain | oracle_full | gpt-5.4-mini | PASS | pass | integration | 407.7 | 376.3 | 1 | 1 | 8 | yes | 767268 |
| tank_fill_drain | oracle_full | qwen35-27b-q4km | PASS | pass | integration | 446.5 | 404.2 | 1 | 1 | 2 | yes | 737170 |
| tank_fill_drain | oracle_full | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 652.2 | 619.7 | 1 | 2 | 4 | yes | 1670916 |
| tank_fill_drain | oracle_full | qwen35-9b-ud-q4kxl | PASS | pass | integration | 421.0 | 263.2 | 4 | 1 | 3 | yes | 1821664 |
| tank_fill_drain | oracle_full | qwen35-4b-ud-q4kxl | PASS | pass | integration | 1067.6 | 662.1 | 9 | 0 | 4 | yes | 10326065 |
| tank_fill_drain | oracle_full | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 899.4 | - | 0 | 0 | 6 | authored | 17841974 |
| thermal_chamber_hysteresis | oneshot_blind | gpt-5.4 | PASS | pass | integration | 207.8 | 135.9 | 1 | 0 | 0 | no | 77823 |
| thermal_chamber_hysteresis | oneshot_blind | gpt-5.4-mini | PASS | pass | integration | 192.2 | 128.0 | 1 | 0 | 0 | no | 108037 |
| thermal_chamber_hysteresis | oneshot_blind | qwen35-27b-q4km | PASS | pass | integration | 122.4 | 52.6 | 1 | 0 | 0 | no | 168204 |
| thermal_chamber_hysteresis | oneshot_blind | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 22.8 | 18.6 | 1 | 0 | 0 | no | 100686 |
| thermal_chamber_hysteresis | oneshot_blind | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 31.7 | 22.6 | 1 | 0 | 0 | no | 209260 |
| thermal_chamber_hysteresis | oneshot_blind | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 27.2 | 24.9 | 1 | 0 | 0 | no | 127028 |
| thermal_chamber_hysteresis | oneshot_blind | qwen35-2b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 34.9 | 30.1 | 1 | 0 | 0 | no | 542203 |
| thermal_chamber_hysteresis | realistic_self_verify | gpt-5.4 | PASS | pass | integration | 433.6 | 389.0 | 1 | 1 | 3 | yes | 359957 |
| thermal_chamber_hysteresis | realistic_self_verify | gpt-5.4-mini | PASS | pass | integration | 749.9 | 697.8 | 1 | 2 | 7 | yes | 1131727 |
| thermal_chamber_hysteresis | realistic_self_verify | qwen35-27b-q4km | PASS | pass | integration | 1328.4 | 1270.9 | 1 | 2 | 6 | yes | 1388683 |
| thermal_chamber_hysteresis | realistic_self_verify | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 684.3 | 676.9 | 1 | 2 | 18 | yes | 1784900 |
| thermal_chamber_hysteresis | realistic_self_verify | qwen35-9b-ud-q4kxl | INTEGRATION_FAILED | integration | integration | 1319.0 | 1278.3 | 1 | 3 | 13 | yes | 2514013 |
| thermal_chamber_hysteresis | realistic_self_verify | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 119.4 | 115.2 | 1 | 1 | 3 | yes | 465215 |
| thermal_chamber_hysteresis | realistic_self_verify | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.0 | - | 0 | 281 | 0 | no | 45559684 |
| thermal_chamber_hysteresis | ci_red_green | gpt-5.4 | PASS | pass | integration | 376.5 | 332.9 | 1 | 1 | 2 | yes | 307659 |
| thermal_chamber_hysteresis | ci_red_green | gpt-5.4-mini | PASS | pass | integration | 349.7 | 310.1 | 1 | 1 | 2 | yes | 425590 |
| thermal_chamber_hysteresis | ci_red_green | qwen35-27b-q4km | PASS | pass | integration | 850.9 | 808.2 | 1 | 1 | 4 | yes | 837447 |
| thermal_chamber_hysteresis | ci_red_green | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 812.6 | 775.4 | 1 | 3 | 6 | yes | 1005262 |
| thermal_chamber_hysteresis | ci_red_green | qwen35-9b-ud-q4kxl | PASS | pass | integration | 995.9 | 922.0 | 2 | 4 | 7 | no | 2348231 |
| thermal_chamber_hysteresis | ci_red_green | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 1192.1 | 788.0 | 6 | 5 | 31 | yes | 6725107 |
| thermal_chamber_hysteresis | ci_red_green | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 594.9 | - | 0 | 0 | 9 | authored | 2589694 |
| thermal_chamber_hysteresis | oracle_full | gpt-5.4 | PASS | pass | integration | 296.8 | 255.9 | 1 | 1 | 1 | yes | 216612 |
| thermal_chamber_hysteresis | oracle_full | gpt-5.4-mini | INTEGRATION_FAILED | integration | integration | 794.9 | 346.0 | 2 | 1 | 9 | yes | 1804688 |
| thermal_chamber_hysteresis | oracle_full | qwen35-27b-q4km | PASS | pass | integration | 1807.7 | 1750.6 | 1 | 4 | 10 | yes | 4616601 |
| thermal_chamber_hysteresis | oracle_full | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 1492.5 | 1431.5 | 2 | 4 | 10 | yes | 3166206 |
| thermal_chamber_hysteresis | oracle_full | qwen35-9b-ud-q4kxl | PASS | pass | integration | 528.8 | 375.6 | 4 | 6 | 2 | yes | 1694589 |
| thermal_chamber_hysteresis | oracle_full | qwen35-4b-ud-q4kxl | PASS | pass | integration | 632.4 | 478.5 | 4 | 4 | 4 | no | 10610619 |
| thermal_chamber_hysteresis | oracle_full | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 2236.6 | - | 0 | 0 | 0 | no | 2193045 |
| filter_tank_sequence | oneshot_blind | gpt-5.4 | INTEGRATION_FAILED | integration | integration | 318.8 | 246.0 | 1 | 0 | 0 | no | 188639 |
| filter_tank_sequence | oneshot_blind | gpt-5.4-mini | HOST_TEST_FAILED | host_tests | host unit tests | 192.9 | 188.6 | 1 | 0 | 0 | no | 185794 |
| filter_tank_sequence | oneshot_blind | qwen35-27b-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 117.8 | 106.8 | 1 | 0 | 0 | no | 216621 |
| filter_tank_sequence | oneshot_blind | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 25.7 | 21.2 | 1 | 0 | 0 | no | 78470 |
| filter_tank_sequence | oneshot_blind | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 86.2 | 74.9 | 1 | 0 | 0 | no | 267580 |
| filter_tank_sequence | oneshot_blind | qwen35-4b-ud-q4kxl | None | unknown | - | 43.3 | 26.8 | 2 | 0 | 0 | no | 181744 |
| filter_tank_sequence | oneshot_blind | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 632.6 | - | 0 | 0 | 0 | no | 1287415 |
| filter_tank_sequence | realistic_self_verify | gpt-5.4 | INTEGRATION_FAILED | integration | integration | 507.0 | 455.8 | 1 | 2 | 3 | yes | 583765 |
| filter_tank_sequence | realistic_self_verify | gpt-5.4-mini | HOST_TEST_FAILED | host_tests | host unit tests | 607.1 | 585.7 | 1 | 1 | 3 | yes | 1033679 |
| filter_tank_sequence | realistic_self_verify | qwen35-27b-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 1975.6 | 1948.2 | 1 | 3 | 9 | yes | 3429667 |
| filter_tank_sequence | realistic_self_verify | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 1868.9 | 1608.3 | 2 | 10 | 15 | yes | 8666863 |
| filter_tank_sequence | realistic_self_verify | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 3600.0 | 2746.0 | 1 | 26 | 25 | yes | 13590626 |
| filter_tank_sequence | realistic_self_verify | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 1704.3 | 589.7 | 171 | 8 | 19 | authored | 17910342 |
| filter_tank_sequence | realistic_self_verify | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 446.4 | - | 0 | 4 | 47 | authored | 5460934 |
| filter_tank_sequence | ci_red_green | gpt-5.4 | PASS | pass | integration | 476.5 | 413.3 | 1 | 1 | 6 | yes | 722297 |
| filter_tank_sequence | ci_red_green | gpt-5.4-mini | PASS | pass | integration | 1306.6 | 604.1 | 3 | 4 | 13 | yes | 3242211 |
| filter_tank_sequence | ci_red_green | qwen35-27b-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 3600.0 | 1594.7 | 9 | 11 | 27 | yes | 8873321 |
| filter_tank_sequence | ci_red_green | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 1587.1 | 1505.4 | 4 | 8 | 6 | yes | 5706619 |
| filter_tank_sequence | ci_red_green | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 3600.0 | 1115.8 | 270 | 265 | 14 | yes | 29513729 |
| filter_tank_sequence | ci_red_green | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 3600.0 | 1972.9 | 3 | 6 | 36 | yes | 48532817 |
| filter_tank_sequence | ci_red_green | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.0 | - | 0 | 0 | 0 | no | 32614057 |
| filter_tank_sequence | oracle_full | gpt-5.4 | NO_SUBMISSION | no_submission | - | 745.3 | - | 0 | 0 | 0 | no | 0 |
| filter_tank_sequence | oracle_full | gpt-5.4-mini | INTEGRATION_FAILED | integration | integration | 1405.7 | 735.9 | 5 | 6 | 10 | authored | 3542241 |
| filter_tank_sequence | oracle_full | qwen35-27b-q4km | PASS | pass | integration | 2613.1 | 1926.7 | 7 | 3 | 11 | yes | 9649391 |
| filter_tank_sequence | oracle_full | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 3600.0 | 770.5 | 667 | 22 | 15 | yes | 57300078 |
| filter_tank_sequence | oracle_full | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 1131.2 | 915.0 | 10 | 7 | 15 | authored | 13833540 |
| filter_tank_sequence | oracle_full | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 1329.1 | 1190.0 | 4 | 15 | 0 | authored | 11495932 |
| filter_tank_sequence | oracle_full | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 1068.7 | - | 0 | 9 | 0 | no | 7814215 |
| mixing_tank_fill_heat | oneshot_blind | gpt-5.4 | PASS | pass | integration | 417.3 | 348.2 | 1 | 0 | 0 | no | 268120 |
| mixing_tank_fill_heat | oneshot_blind | gpt-5.4-mini | INTEGRATION_FAILED | integration | integration | 329.5 | 258.6 | 1 | 0 | 0 | no | 381101 |
| mixing_tank_fill_heat | oneshot_blind | qwen35-27b-q4km | QEMU_SMOKE_FAILED | host_tests | host unit tests | 161.3 | 78.8 | 1 | 0 | 0 | no | 176015 |
| mixing_tank_fill_heat | oneshot_blind | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 20.1 | 16.0 | 1 | 0 | 0 | no | 83355 |
| mixing_tank_fill_heat | oneshot_blind | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 37.2 | 30.4 | 1 | 0 | 0 | no | 150073 |
| mixing_tank_fill_heat | oneshot_blind | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 21.3 | 18.6 | 1 | 0 | 0 | no | 171955 |
| mixing_tank_fill_heat | oneshot_blind | qwen35-2b-ud-q4kxl | None | unknown | - | 36.7 | 27.7 | 2 | 0 | 0 | no | 687082 |
| mixing_tank_fill_heat | realistic_self_verify | gpt-5.4 | PASS | pass | integration | 363.0 | 312.2 | 1 | 1 | 2 | yes | 428753 |
| mixing_tank_fill_heat | realistic_self_verify | gpt-5.4-mini | INTEGRATION_FAILED | integration | integration | 598.4 | 542.4 | 1 | 1 | 5 | yes | 1087032 |
| mixing_tank_fill_heat | realistic_self_verify | qwen35-27b-q4km | QEMU_SMOKE_FAILED | host_tests | host unit tests | 2417.2 | 2136.7 | 3 | 3 | 15 | yes | 3755822 |
| mixing_tank_fill_heat | realistic_self_verify | qwen35-35b-a3b-ud-q4km | INTEGRATION_FAILED | integration | integration | 1863.2 | 864.3 | 2 | 3 | 8 | authored | 4247057 |
| mixing_tank_fill_heat | realistic_self_verify | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 2893.0 | 2884.0 | 1 | 3 | 213 | yes | 7647118 |
| mixing_tank_fill_heat | realistic_self_verify | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 376.8 | 370.4 | 1 | 3 | 6 | yes | 3748754 |
| mixing_tank_fill_heat | realistic_self_verify | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.0 | - | 0 | 0 | 0 | no | 144382986 |
| mixing_tank_fill_heat | ci_red_green | gpt-5.4 | PASS | pass | integration | 699.0 | 652.3 | 1 | 1 | 3 | yes | 522016 |
| mixing_tank_fill_heat | ci_red_green | gpt-5.4-mini | PASS | pass | integration | 884.7 | 822.2 | 1 | 1 | 5 | yes | 1514345 |
| mixing_tank_fill_heat | ci_red_green | qwen35-27b-q4km | QEMU_SMOKE_FAILED | host_tests | host unit tests | 2699.0 | 1303.0 | 11 | 8 | 27 | yes | 5512980 |
| mixing_tank_fill_heat | ci_red_green | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 2683.3 | 1902.9 | 8 | 7 | 17 | authored | 7101525 |
| mixing_tank_fill_heat | ci_red_green | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 1455.1 | 1180.7 | 9 | 8 | 32 | yes | 10948053 |
| mixing_tank_fill_heat | ci_red_green | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 597.4 | 528.8 | 5 | 13 | 1 | yes | 11157892 |
| mixing_tank_fill_heat | ci_red_green | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 656.1 | - | 0 | 0 | 0 | no | 24535050 |
| mixing_tank_fill_heat | oracle_full | gpt-5.4 | PASS | pass | integration | 401.7 | 351.5 | 1 | 1 | 2 | yes | 340414 |
| mixing_tank_fill_heat | oracle_full | gpt-5.4-mini | PASS | pass | integration | 511.7 | 462.0 | 1 | 1 | 4 | yes | 969270 |
| mixing_tank_fill_heat | oracle_full | qwen35-27b-q4km | INTEGRATION_FAILED | integration | integration | 2768.2 | 1702.8 | 5 | 4 | 16 | yes | 13428027 |
| mixing_tank_fill_heat | oracle_full | qwen35-35b-a3b-ud-q4km | INTEGRATION_FAILED | integration | integration | 2191.9 | 1184.7 | 6 | 6 | 14 | yes | 7066592 |
| mixing_tank_fill_heat | oracle_full | qwen35-9b-ud-q4kxl | PASS | pass | integration | 836.2 | 787.1 | 1 | 3 | 0 | no | 5258150 |
| mixing_tank_fill_heat | oracle_full | qwen35-4b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 858.6 | - | 0 | 0 | 0 | no | 16168267 |
| mixing_tank_fill_heat | oracle_full | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.0 | - | 0 | 655 | 0 | no | 99171798 |
| pressure_vessel_interlock | oneshot_blind | gpt-5.4 | PASS | pass | integration | 162.8 | 100.4 | 1 | 0 | 0 | no | 96874 |
| pressure_vessel_interlock | oneshot_blind | gpt-5.4-mini | PASS | pass | integration | 161.1 | 101.6 | 1 | 0 | 0 | no | 130230 |
| pressure_vessel_interlock | oneshot_blind | qwen35-27b-q4km | PASS | pass | integration | 126.0 | 62.0 | 1 | 0 | 0 | no | 139280 |
| pressure_vessel_interlock | oneshot_blind | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 16.7 | 14.0 | 1 | 0 | 0 | no | 99832 |
| pressure_vessel_interlock | oneshot_blind | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 45.3 | 37.5 | 1 | 0 | 0 | no | 212385 |
| pressure_vessel_interlock | oneshot_blind | qwen35-4b-ud-q4kxl | INTEGRATION_FAILED | integration | integration | 77.1 | 16.3 | 1 | 0 | 0 | no | 134279 |
| pressure_vessel_interlock | oneshot_blind | qwen35-2b-ud-q4kxl | None | unknown | - | 76.2 | 51.5 | 3 | 0 | 0 | no | 1000140 |
| pressure_vessel_interlock | realistic_self_verify | gpt-5.4 | PASS | pass | integration | 337.5 | 294.8 | 1 | 1 | 2 | yes | 337927 |
| pressure_vessel_interlock | realistic_self_verify | gpt-5.4-mini | PASS | pass | integration | 623.2 | 583.2 | 1 | 1 | 5 | yes | 1311059 |
| pressure_vessel_interlock | realistic_self_verify | qwen35-27b-q4km | PASS | pass | integration | 2800.6 | 2750.0 | 1 | 2 | 16 | yes | 3866422 |
| pressure_vessel_interlock | realistic_self_verify | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 1580.3 | 1543.7 | 1 | 4 | 12 | yes | 4502116 |
| pressure_vessel_interlock | realistic_self_verify | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 3429.1 | 2840.0 | 2 | 8 | 26 | yes | 10863874 |
| pressure_vessel_interlock | realistic_self_verify | qwen35-4b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 943.3 | - | 0 | 2 | 29 | authored | 3299040 |
| pressure_vessel_interlock | realistic_self_verify | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 136.6 | - | 0 | 0 | 0 | no | 1973826 |
| pressure_vessel_interlock | ci_red_green | gpt-5.4 | PASS | pass | integration | 262.5 | 224.8 | 1 | 1 | 1 | yes | 207452 |
| pressure_vessel_interlock | ci_red_green | gpt-5.4-mini | PASS | pass | integration | 243.2 | 205.0 | 1 | 1 | 1 | yes | 264677 |
| pressure_vessel_interlock | ci_red_green | qwen35-27b-q4km | PASS | pass | integration | 1622.0 | 1577.7 | 1 | 1 | 13 | yes | 2920805 |
| pressure_vessel_interlock | ci_red_green | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 1747.7 | 523.7 | 23 | 13 | 15 | yes | 5363508 |
| pressure_vessel_interlock | ci_red_green | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 2797.6 | 778.9 | 345 | 7 | 7 | authored | 36210689 |
| pressure_vessel_interlock | ci_red_green | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 3318.8 | 3046.7 | 30 | 17 | 259 | authored | 17788921 |
| pressure_vessel_interlock | ci_red_green | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 1574.6 | - | 0 | 85 | 0 | no | 51210356 |
| pressure_vessel_interlock | oracle_full | gpt-5.4 | PASS | pass | integration | 269.7 | 233.3 | 1 | 1 | 2 | yes | 323797 |
| pressure_vessel_interlock | oracle_full | gpt-5.4-mini | PASS | pass | integration | 611.8 | 572.5 | 1 | 2 | 5 | yes | 1626647 |
| pressure_vessel_interlock | oracle_full | qwen35-27b-q4km | PASS | pass | integration | 1426.1 | 1368.7 | 1 | 2 | 13 | yes | 2868864 |
| pressure_vessel_interlock | oracle_full | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 1394.9 | 1353.5 | 1 | 3 | 12 | yes | 3437564 |
| pressure_vessel_interlock | oracle_full | qwen35-9b-ud-q4kxl | PASS | pass | integration | 3456.1 | 3362.3 | 2 | 5 | 57 | yes | 7920232 |
| pressure_vessel_interlock | oracle_full | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 3600.0 | 1787.4 | 3 | 10 | 2 | authored | 68620026 |
| pressure_vessel_interlock | oracle_full | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.0 | - | 0 | 39 | 0 | no | 183220787 |
| tank_fill_drain | oneshot_blind | gpt-5.4 | PASS | pass | integration | 121.4 | 68.7 | 1 | 0 | 0 | no | 61177 |
| tank_fill_drain | oneshot_blind | gpt-5.4-mini | PASS | pass | integration | 226.9 | 172.3 | 1 | 0 | 0 | no | 150555 |
| tank_fill_drain | oneshot_blind | qwen35-27b-q4km | INTEGRATION_FAILED | integration | integration | 104.2 | 44.0 | 1 | 0 | 0 | no | 104295 |
| tank_fill_drain | oneshot_blind | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 61.2 | 10.6 | 1 | 0 | 0 | no | 78951 |
| tank_fill_drain | oneshot_blind | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 29.0 | 19.4 | 1 | 0 | 0 | no | 151503 |
| tank_fill_drain | oneshot_blind | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 28.2 | 24.5 | 1 | 0 | 0 | no | 147651 |
| tank_fill_drain | oneshot_blind | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 349.4 | - | 0 | 0 | 0 | no | 13494578 |
| tank_fill_drain | realistic_self_verify | gpt-5.4 | PASS | pass | integration | 378.6 | 340.7 | 1 | 1 | 6 | yes | 660143 |
| tank_fill_drain | realistic_self_verify | gpt-5.4-mini | PASS | pass | integration | 488.8 | 450.8 | 1 | 2 | 1 | yes | 483884 |
| tank_fill_drain | realistic_self_verify | qwen35-27b-q4km | PASS | pass | integration | 3600.0 | 1019.6 | 4 | 4 | 13 | yes | 58922157 |
| tank_fill_drain | realistic_self_verify | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 2009.9 | 318.5 | 2 | 3 | 20 | authored | 3479397 |
| tank_fill_drain | realistic_self_verify | qwen35-9b-ud-q4kxl | PASS | pass | integration | 1080.4 | 878.4 | 2 | 7 | 8 | yes | 5197731 |
| tank_fill_drain | realistic_self_verify | qwen35-4b-ud-q4kxl | PASS | pass | integration | 755.3 | 367.4 | 2 | 3 | 5 | yes | 6840482 |
| tank_fill_drain | realistic_self_verify | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 394.5 | - | 0 | 11 | 0 | authored | 4700947 |
| tank_fill_drain | ci_red_green | gpt-5.4 | PASS | pass | integration | 224.3 | 194.1 | 1 | 1 | 1 | yes | 168583 |
| tank_fill_drain | ci_red_green | gpt-5.4-mini | PASS | pass | integration | 351.7 | 320.0 | 1 | 2 | 5 | yes | 586862 |
| tank_fill_drain | ci_red_green | qwen35-27b-q4km | PASS | pass | integration | 1366.0 | 1325.9 | 1 | 7 | 7 | yes | 2137615 |
| tank_fill_drain | ci_red_green | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 250.1 | 219.8 | 1 | 1 | 2 | yes | 505077 |
| tank_fill_drain | ci_red_green | qwen35-9b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.0 | - | 0 | 1 | 2 | yes | 2987294 |
| tank_fill_drain | ci_red_green | qwen35-4b-ud-q4kxl | INTEGRATION_FAILED | integration | integration | 1720.0 | 1594.7 | 1 | 3 | 37 | yes | 8730474 |
| tank_fill_drain | ci_red_green | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 181.8 | - | 0 | 0 | 0 | authored | 4323781 |
| tank_fill_drain | oracle_full | gpt-5.4 | PASS | pass | integration | 406.0 | 374.2 | 1 | 1 | 7 | yes | 395887 |
| tank_fill_drain | oracle_full | gpt-5.4-mini | PASS | pass | integration | 240.9 | 201.7 | 1 | 1 | 1 | yes | 369688 |
| tank_fill_drain | oracle_full | qwen35-27b-q4km | PASS | pass | integration | 1050.1 | 1005.1 | 1 | 1 | 10 | yes | 1330047 |
| tank_fill_drain | oracle_full | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 385.3 | 352.7 | 1 | 1 | 11 | yes | 1191274 |
| tank_fill_drain | oracle_full | qwen35-9b-ud-q4kxl | INTEGRATION_FAILED | infra | integration | 1932.9 | 1313.3 | 6 | 4 | 14 | yes | 6835595 |
| tank_fill_drain | oracle_full | qwen35-4b-ud-q4kxl | INTEGRATION_FAILED | integration | integration | 548.6 | 134.6 | 7 | 1 | 4 | yes | 2152913 |
| tank_fill_drain | oracle_full | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 347.0 | - | 0 | 3 | 4 | authored | 2123272 |
| thermal_chamber_hysteresis | oneshot_blind | gpt-5.4 | PASS | pass | integration | 178.3 | 114.0 | 1 | 0 | 0 | no | 127594 |
| thermal_chamber_hysteresis | oneshot_blind | gpt-5.4-mini | PASS | pass | integration | 148.2 | 75.1 | 1 | 0 | 0 | no | 114294 |
| thermal_chamber_hysteresis | oneshot_blind | qwen35-27b-q4km | PASS | pass | integration | 122.1 | 56.3 | 1 | 0 | 0 | no | 101275 |
| thermal_chamber_hysteresis | oneshot_blind | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 85.9 | 26.9 | 1 | 0 | 0 | no | 135310 |
| thermal_chamber_hysteresis | oneshot_blind | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 36.9 | 27.2 | 1 | 0 | 0 | no | 284627 |
| thermal_chamber_hysteresis | oneshot_blind | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 30.5 | 29.3 | 1 | 0 | 0 | no | 160488 |
| thermal_chamber_hysteresis | oneshot_blind | qwen35-2b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 18.2 | 16.1 | 1 | 0 | 0 | no | 237787 |
| thermal_chamber_hysteresis | realistic_self_verify | gpt-5.4 | PASS | pass | integration | 503.3 | 460.8 | 1 | 1 | 5 | yes | 649727 |
| thermal_chamber_hysteresis | realistic_self_verify | gpt-5.4-mini | PASS | pass | integration | 365.1 | 323.7 | 1 | 1 | 4 | yes | 950659 |
| thermal_chamber_hysteresis | realistic_self_verify | qwen35-27b-q4km | PASS | pass | integration | 1143.6 | 1079.8 | 1 | 3 | 5 | yes | 1164902 |
| thermal_chamber_hysteresis | realistic_self_verify | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 761.5 | 753.9 | 1 | 1 | 12 | yes | 5560818 |
| thermal_chamber_hysteresis | realistic_self_verify | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 2424.7 | 2304.8 | 1 | 3 | 26 | yes | 7863222 |
| thermal_chamber_hysteresis | realistic_self_verify | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 1445.4 | 1143.0 | 3 | 1 | 93 | yes | 4012283 |
| thermal_chamber_hysteresis | realistic_self_verify | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.1 | - | 0 | 0 | 0 | no | 117810657 |
| thermal_chamber_hysteresis | ci_red_green | gpt-5.4 | PASS | pass | integration | 395.2 | 339.5 | 1 | 1 | 5 | yes | 554791 |
| thermal_chamber_hysteresis | ci_red_green | gpt-5.4-mini | PASS | pass | integration | 519.5 | 478.7 | 1 | 2 | 4 | yes | 627396 |
| thermal_chamber_hysteresis | ci_red_green | qwen35-27b-q4km | PASS | pass | integration | 1275.1 | 1227.6 | 1 | 1 | 8 | yes | 1735169 |
| thermal_chamber_hysteresis | ci_red_green | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 510.5 | 133.3 | 5 | 6 | 11 | yes | 1652106 |
| thermal_chamber_hysteresis | ci_red_green | qwen35-9b-ud-q4kxl | PASS | pass | integration | 1940.5 | 1899.9 | 1 | 6 | 54 | yes | 3625265 |
| thermal_chamber_hysteresis | ci_red_green | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 671.1 | 355.2 | 2 | 5 | 11 | yes | 4619756 |
| thermal_chamber_hysteresis | ci_red_green | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 619.6 | - | 0 | 0 | 8 | no | 28356336 |
| thermal_chamber_hysteresis | oracle_full | gpt-5.4 | PASS | pass | integration | 385.3 | 346.4 | 1 | 1 | 3 | yes | 486228 |
| thermal_chamber_hysteresis | oracle_full | gpt-5.4-mini | PASS | pass | integration | 423.8 | 386.2 | 1 | 1 | 5 | yes | 588032 |
| thermal_chamber_hysteresis | oracle_full | qwen35-27b-q4km | PASS | pass | integration | 1344.0 | 759.0 | 2 | 1 | 8 | yes | 2612251 |
| thermal_chamber_hysteresis | oracle_full | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 1095.3 | 1051.3 | 1 | 2 | 11 | yes | 1641562 |
| thermal_chamber_hysteresis | oracle_full | qwen35-9b-ud-q4kxl | PASS | pass | integration | 1426.5 | 1286.0 | 3 | 9 | 5 | yes | 3818210 |
| thermal_chamber_hysteresis | oracle_full | qwen35-4b-ud-q4kxl | INTEGRATION_FAILED | integration | integration | 1685.9 | 98.2 | 29 | 7 | 1 | no | 8606966 |
| thermal_chamber_hysteresis | oracle_full | qwen35-2b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 329.0 | 239.2 | 1 | 13 | 4 | authored | 3260560 |
| filter_tank_sequence | oneshot_blind | gpt-5.4 | INTEGRATION_FAILED | integration | integration | 259.0 | 187.2 | 1 | 0 | 0 | no | 189843 |
| filter_tank_sequence | oneshot_blind | gpt-5.4-mini | PASS | pass | integration | 267.2 | 194.3 | 1 | 0 | 0 | no | 232347 |
| filter_tank_sequence | oneshot_blind | qwen35-27b-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 152.1 | 133.1 | 1 | 0 | 0 | no | 186264 |
| filter_tank_sequence | oneshot_blind | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 53.3 | 49.4 | 1 | 0 | 0 | no | 115299 |
| filter_tank_sequence | oneshot_blind | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 48.5 | 39.4 | 1 | 0 | 0 | no | 237923 |
| filter_tank_sequence | oneshot_blind | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 32.7 | 29.5 | 1 | 0 | 0 | no | 97589 |
| filter_tank_sequence | oneshot_blind | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.1 | - | 0 | 0 | 0 | no | 148358422 |
| filter_tank_sequence | realistic_self_verify | gpt-5.4 | PASS | pass | integration | 299.9 | 249.5 | 1 | 1 | 1 | yes | 254572 |
| filter_tank_sequence | realistic_self_verify | gpt-5.4-mini | HOST_TEST_FAILED | host_tests | host unit tests | 529.5 | 522.7 | 1 | 1 | 4 | yes | 1666288 |
| filter_tank_sequence | realistic_self_verify | qwen35-27b-q4km | INTEGRATION_FAILED | integration | integration | 2446.0 | 2377.2 | 1 | 3 | 12 | yes | 4682744 |
| filter_tank_sequence | realistic_self_verify | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 2315.9 | 1174.4 | 3 | 15 | 22 | yes | 8448676 |
| filter_tank_sequence | realistic_self_verify | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 1885.4 | 1507.6 | 3 | 3 | 1 | yes | 3341320 |
| filter_tank_sequence | realistic_self_verify | qwen35-4b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 947.0 | - | 0 | 0 | 5 | no | 7625346 |
| filter_tank_sequence | realistic_self_verify | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.1 | - | 0 | 7 | 0 | no | 199455931 |
| filter_tank_sequence | ci_red_green | gpt-5.4 | PASS | pass | integration | 400.1 | 347.9 | 1 | 1 | 5 | yes | 664255 |
| filter_tank_sequence | ci_red_green | gpt-5.4-mini | HOST_TEST_FAILED | host_tests | host unit tests | 1271.8 | 329.1 | 8 | 10 | 13 | yes | 3118089 |
| filter_tank_sequence | ci_red_green | qwen35-27b-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 3600.1 | 825.5 | 103 | 42 | 35 | yes | 22162138 |
| filter_tank_sequence | ci_red_green | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 1185.2 | 1134.5 | 2 | 2 | 14 | yes | 5019792 |
| filter_tank_sequence | ci_red_green | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 1797.6 | 895.2 | 6 | 7 | 13 | yes | 10744996 |
| filter_tank_sequence | ci_red_green | qwen35-4b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 1492.9 | - | 0 | 22 | 1 | no | 10439837 |
| filter_tank_sequence | ci_red_green | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 2956.7 | - | 0 | 0 | 0 | no | 5002922 |
| filter_tank_sequence | oracle_full | gpt-5.4 | PASS | pass | integration | 414.5 | 366.1 | 1 | 1 | 5 | yes | 675519 |
| filter_tank_sequence | oracle_full | gpt-5.4-mini | HOST_TEST_FAILED | host_tests | host unit tests | 1076.5 | 343.9 | 8 | 7 | 13 | yes | 3969445 |
| filter_tank_sequence | oracle_full | qwen35-27b-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 2262.4 | 816.6 | 16 | 5 | 3 | yes | 3708719 |
| filter_tank_sequence | oracle_full | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 1683.7 | 1468.2 | 7 | 14 | 11 | yes | 6914328 |
| filter_tank_sequence | oracle_full | qwen35-9b-ud-q4kxl | INTEGRATION_FAILED | integration | integration | 1943.4 | 1064.6 | 12 | 9 | 9 | yes | 6083979 |
| filter_tank_sequence | oracle_full | qwen35-4b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.1 | - | 0 | 1 | 5 | authored | 634361 |
| filter_tank_sequence | oracle_full | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 1574.9 | - | 0 | 0 | 0 | authored | 81187009 |
| mixing_tank_fill_heat | oneshot_blind | gpt-5.4 | PASS | pass | integration | 155.7 | 87.8 | 1 | 0 | 0 | no | 112778 |
| mixing_tank_fill_heat | oneshot_blind | gpt-5.4-mini | PASS | pass | integration | 189.2 | 121.1 | 1 | 0 | 0 | no | 157098 |
| mixing_tank_fill_heat | oneshot_blind | qwen35-27b-q4km | PASS | pass | integration | 133.3 | 59.9 | 1 | 0 | 0 | no | 94234 |
| mixing_tank_fill_heat | oneshot_blind | qwen35-35b-a3b-ud-q4km | INTEGRATION_FAILED | integration | integration | 84.7 | 17.5 | 1 | 0 | 0 | no | 95701 |
| mixing_tank_fill_heat | oneshot_blind | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 66.8 | 60.0 | 1 | 0 | 0 | no | 226644 |
| mixing_tank_fill_heat | oneshot_blind | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 18.6 | 15.8 | 1 | 0 | 0 | no | 121198 |
| mixing_tank_fill_heat | oneshot_blind | qwen35-2b-ud-q4kxl | None | unknown | - | 140.5 | 27.5 | 2 | 0 | 0 | no | 821351 |
| mixing_tank_fill_heat | realistic_self_verify | gpt-5.4 | PASS | pass | integration | 352.9 | 304.8 | 1 | 1 | 2 | yes | 396353 |
| mixing_tank_fill_heat | realistic_self_verify | gpt-5.4-mini | INTEGRATION_FAILED | integration | integration | 502.2 | 453.5 | 1 | 1 | 4 | yes | 1233169 |
| mixing_tank_fill_heat | realistic_self_verify | qwen35-27b-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 440.4 | 301.7 | 1 | 1 | 2 | yes | 334864 |
| mixing_tank_fill_heat | realistic_self_verify | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 1409.3 | 1390.9 | 2 | 3 | 7 | authored | 3101828 |
| mixing_tank_fill_heat | realistic_self_verify | qwen35-9b-ud-q4kxl | INTEGRATION_FAILED | integration | integration | 1437.8 | 1369.6 | 1 | 5 | 6 | yes | 3479365 |
| mixing_tank_fill_heat | realistic_self_verify | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 1023.2 | 875.9 | 1 | 4 | 4 | yes | 5883232 |
| mixing_tank_fill_heat | realistic_self_verify | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 1809.6 | - | 0 | 0 | 11 | authored | 81524480 |
| mixing_tank_fill_heat | ci_red_green | gpt-5.4 | PASS | pass | integration | 347.5 | 301.3 | 1 | 1 | 3 | yes | 431495 |
| mixing_tank_fill_heat | ci_red_green | gpt-5.4-mini | PASS | pass | integration | 938.6 | 888.6 | 1 | 3 | 8 | yes | 1737462 |
| mixing_tank_fill_heat | ci_red_green | qwen35-27b-q4km | INTEGRATION_FAILED | integration | integration | 3600.1 | 2666.0 | 7 | 11 | 31 | yes | 7773358 |
| mixing_tank_fill_heat | ci_red_green | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 1194.9 | 1149.5 | 1 | 2 | 10 | yes | 3174083 |
| mixing_tank_fill_heat | ci_red_green | qwen35-9b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 770.0 | - | 0 | 3 | 1 | yes | 9743188 |
| mixing_tank_fill_heat | ci_red_green | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 715.8 | 386.2 | 18 | 4 | 17 | no | 8952362 |
| mixing_tank_fill_heat | ci_red_green | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 74.9 | - | 0 | 0 | 0 | authored | 1297799 |
| mixing_tank_fill_heat | oracle_full | gpt-5.4 | PASS | pass | integration | 263.4 | 218.0 | 1 | 1 | 1 | yes | 207866 |
| mixing_tank_fill_heat | oracle_full | gpt-5.4-mini | PASS | pass | integration | 578.9 | 533.9 | 1 | 2 | 5 | yes | 1854472 |
| mixing_tank_fill_heat | oracle_full | qwen35-27b-q4km | PASS | pass | integration | 2231.4 | 753.8 | 5 | 4 | 9 | yes | 2504235 |
| mixing_tank_fill_heat | oracle_full | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 1294.7 | 1247.5 | 1 | 1 | 12 | yes | 2346109 |
| mixing_tank_fill_heat | oracle_full | qwen35-9b-ud-q4kxl | PASS | pass | integration | 1836.3 | 1363.7 | 11 | 12 | 83 | yes | 5158060 |
| mixing_tank_fill_heat | oracle_full | qwen35-4b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.1 | - | 0 | 3 | 17 | authored | 127936222 |
| mixing_tank_fill_heat | oracle_full | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.1 | - | 0 | 3 | 0 | no | 130944097 |
| pressure_vessel_interlock | oneshot_blind | gpt-5.4 | PASS | pass | integration | 169.7 | 104.9 | 1 | 0 | 0 | no | 166109 |
| pressure_vessel_interlock | oneshot_blind | gpt-5.4-mini | HOST_TEST_FAILED | host_tests | host unit tests | 140.9 | 135.6 | 1 | 0 | 0 | no | 234968 |
| pressure_vessel_interlock | oneshot_blind | qwen35-27b-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 74.1 | 70.9 | 1 | 0 | 0 | no | 162966 |
| pressure_vessel_interlock | oneshot_blind | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 40.2 | 35.9 | 1 | 0 | 0 | no | 230787 |
| pressure_vessel_interlock | oneshot_blind | qwen35-9b-ud-q4kxl | None | unknown | - | 101.5 | 63.1 | 2 | 0 | 0 | no | 421509 |
| pressure_vessel_interlock | oneshot_blind | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 49.3 | 43.6 | 1 | 0 | 0 | no | 253120 |
| pressure_vessel_interlock | oneshot_blind | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 949.0 | - | 0 | 0 | 0 | no | 26980983 |
| pressure_vessel_interlock | realistic_self_verify | gpt-5.4 | PASS | pass | integration | 354.2 | 315.8 | 1 | 2 | 1 | yes | 481497 |
| pressure_vessel_interlock | realistic_self_verify | gpt-5.4-mini | PASS | pass | integration | 356.8 | 320.0 | 1 | 3 | 7 | yes | 868045 |
| pressure_vessel_interlock | realistic_self_verify | qwen35-27b-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 2260.2 | 2137.0 | 1 | 4 | 19 | yes | 4974788 |
| pressure_vessel_interlock | realistic_self_verify | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 683.4 | 677.0 | 1 | 6 | 4 | authored | 3087734 |
| pressure_vessel_interlock | realistic_self_verify | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 2796.6 | 2772.2 | 1 | 4 | 176 | authored | 6688245 |
| pressure_vessel_interlock | realistic_self_verify | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 1638.6 | 1606.9 | 3 | 1 | 29 | yes | 8900376 |
| pressure_vessel_interlock | realistic_self_verify | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 1474.5 | - | 0 | 0 | 1 | no | 67716990 |
| pressure_vessel_interlock | ci_red_green | gpt-5.4 | PASS | pass | integration | 444.8 | 408.6 | 1 | 3 | 6 | yes | 656753 |
| pressure_vessel_interlock | ci_red_green | gpt-5.4-mini | PASS | pass | integration | 687.5 | 650.8 | 1 | 3 | 7 | authored | 1672405 |
| pressure_vessel_interlock | ci_red_green | qwen35-27b-q4km | PASS | pass | integration | 2457.8 | 1999.0 | 6 | 5 | 14 | yes | 4695778 |
| pressure_vessel_interlock | ci_red_green | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 1103.8 | 352.9 | 130 | 13 | 19 | yes | 19220668 |
| pressure_vessel_interlock | ci_red_green | qwen35-9b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.1 | - | 0 | 4 | 209 | authored | 13067011 |
| pressure_vessel_interlock | ci_red_green | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 470.4 | 203.6 | 12 | 18 | 3 | yes | 5579494 |
| pressure_vessel_interlock | ci_red_green | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 1317.6 | - | 0 | 190 | 1 | authored | 21884521 |
| pressure_vessel_interlock | oracle_full | gpt-5.4 | PASS | pass | integration | 514.7 | 476.0 | 1 | 2 | 7 | yes | 938080 |
| pressure_vessel_interlock | oracle_full | gpt-5.4-mini | PASS | pass | integration | 380.3 | 238.0 | 3 | 5 | 6 | yes | 1425428 |
| pressure_vessel_interlock | oracle_full | qwen35-27b-q4km | PASS | pass | integration | 1923.3 | 1709.3 | 2 | 7 | 16 | yes | 4799463 |
| pressure_vessel_interlock | oracle_full | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 1462.9 | 1255.8 | 7 | 14 | 19 | yes | 12026276 |
| pressure_vessel_interlock | oracle_full | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 1217.0 | 971.9 | 13 | 16 | 33 | authored | 8812673 |
| pressure_vessel_interlock | oracle_full | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 1246.0 | 978.6 | 24 | 9 | 52 | yes | 11126119 |
| pressure_vessel_interlock | oracle_full | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 575.4 | - | 0 | 0 | 109 | yes | 5984315 |
| tank_fill_drain | oneshot_blind | gpt-5.4 | PASS | pass | integration | 123.0 | 70.3 | 1 | 0 | 0 | no | 83222 |
| tank_fill_drain | oneshot_blind | gpt-5.4-mini | PASS | pass | integration | 115.8 | 61.0 | 1 | 0 | 0 | no | 107023 |
| tank_fill_drain | oneshot_blind | qwen35-27b-q4km | PASS | pass | integration | 105.0 | 45.8 | 1 | 0 | 0 | no | 104561 |
| tank_fill_drain | oneshot_blind | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 78.6 | 28.0 | 1 | 0 | 0 | no | 97650 |
| tank_fill_drain | oneshot_blind | qwen35-9b-ud-q4kxl | INTEGRATION_FAILED | integration | integration | 77.6 | 19.8 | 1 | 0 | 0 | no | 130852 |
| tank_fill_drain | oneshot_blind | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 12.6 | 10.7 | 1 | 0 | 0 | no | 83954 |
| tank_fill_drain | oneshot_blind | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 11.4 | - | 0 | 0 | 0 | no | 97678 |
| tank_fill_drain | realistic_self_verify | gpt-5.4 | PASS | pass | integration | 178.3 | 143.5 | 1 | 1 | 1 | yes | 183259 |
| tank_fill_drain | realistic_self_verify | gpt-5.4-mini | PASS | pass | integration | 610.0 | 576.4 | 1 | 2 | 2 | yes | 919681 |
| tank_fill_drain | realistic_self_verify | qwen35-27b-q4km | PASS | pass | integration | 1578.1 | 1523.4 | 1 | 1 | 10 | yes | 2324978 |
| tank_fill_drain | realistic_self_verify | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 597.6 | 565.4 | 1 | 2 | 5 | yes | 1100177 |
| tank_fill_drain | realistic_self_verify | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 1013.4 | 889.2 | 1 | 2 | 7 | yes | 1686411 |
| tank_fill_drain | realistic_self_verify | qwen35-4b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.1 | - | 0 | 3 | 250 | yes | 11908277 |
| tank_fill_drain | realistic_self_verify | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.1 | - | 0 | 111 | 0 | no | 109308309 |
| tank_fill_drain | ci_red_green | gpt-5.4 | PASS | pass | integration | 271.0 | 239.4 | 1 | 1 | 2 | yes | 314876 |
| tank_fill_drain | ci_red_green | gpt-5.4-mini | PASS | pass | integration | 322.4 | 290.1 | 1 | 1 | 9 | yes | 528856 |
| tank_fill_drain | ci_red_green | qwen35-27b-q4km | PASS | pass | integration | 835.3 | 793.9 | 1 | 2 | 7 | yes | 1608937 |
| tank_fill_drain | ci_red_green | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 363.0 | 332.1 | 1 | 2 | 3 | yes | 920983 |
| tank_fill_drain | ci_red_green | qwen35-9b-ud-q4kxl | INTEGRATION_FAILED | integration | integration | 659.1 | 319.4 | 8 | 5 | 2 | yes | 2865257 |
| tank_fill_drain | ci_red_green | qwen35-4b-ud-q4kxl | INTEGRATION_FAILED | integration | integration | 3264.7 | 2584.6 | 11 | 2 | 59 | yes | 13193215 |
| tank_fill_drain | ci_red_green | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.1 | - | 0 | 0 | 0 | authored | 94535453 |
| tank_fill_drain | oracle_full | gpt-5.4 | PASS | pass | integration | 467.1 | 436.4 | 1 | 1 | 5 | yes | 662472 |
| tank_fill_drain | oracle_full | gpt-5.4-mini | PASS | pass | integration | 324.1 | 294.2 | 1 | 1 | 8 | yes | 386045 |
| tank_fill_drain | oracle_full | qwen35-27b-q4km | PASS | pass | integration | 495.7 | 400.2 | 3 | 3 | 2 | yes | 846284 |
| tank_fill_drain | oracle_full | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 970.8 | 373.3 | 2 | 2 | 7 | yes | 1075076 |
| tank_fill_drain | oracle_full | qwen35-9b-ud-q4kxl | INTEGRATION_FAILED | integration | integration | 2699.9 | 762.5 | 48 | 10 | 18 | yes | 12430635 |
| tank_fill_drain | oracle_full | qwen35-4b-ud-q4kxl | INTEGRATION_FAILED | integration | integration | 3600.1 | 140.1 | 103 | 1 | 3 | authored | 11755027 |
| tank_fill_drain | oracle_full | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.1 | - | 0 | 398 | 0 | no | 61870141 |
| thermal_chamber_hysteresis | oneshot_blind | gpt-5.4 | PASS | pass | integration | 123.0 | 60.0 | 1 | 0 | 0 | no | 69358 |
| thermal_chamber_hysteresis | oneshot_blind | gpt-5.4-mini | PASS | pass | integration | 124.4 | 63.8 | 1 | 0 | 0 | no | 101441 |
| thermal_chamber_hysteresis | oneshot_blind | qwen35-27b-q4km | PASS | pass | integration | 114.8 | 48.6 | 1 | 0 | 0 | no | 165345 |
| thermal_chamber_hysteresis | oneshot_blind | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 16.1 | 13.5 | 1 | 0 | 0 | no | 75911 |
| thermal_chamber_hysteresis | oneshot_blind | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 48.7 | 43.0 | 1 | 0 | 0 | no | 182560 |
| thermal_chamber_hysteresis | oneshot_blind | qwen35-4b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 18.9 | 16.9 | 1 | 0 | 0 | no | 93847 |
| thermal_chamber_hysteresis | oneshot_blind | qwen35-2b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 44.0 | 33.7 | 1 | 0 | 0 | no | 1188986 |
| thermal_chamber_hysteresis | realistic_self_verify | gpt-5.4 | PASS | pass | integration | 299.3 | 259.8 | 1 | 1 | 1 | yes | 363661 |
| thermal_chamber_hysteresis | realistic_self_verify | gpt-5.4-mini | INTEGRATION_FAILED | integration | integration | 433.9 | 394.3 | 1 | 1 | 4 | yes | 853054 |
| thermal_chamber_hysteresis | realistic_self_verify | qwen35-27b-q4km | PASS | pass | integration | 2470.1 | 2419.6 | 1 | 1 | 12 | yes | 2497343 |
| thermal_chamber_hysteresis | realistic_self_verify | qwen35-35b-a3b-ud-q4km | HOST_TEST_FAILED | host_tests | host unit tests | 647.5 | 642.1 | 1 | 2 | 6 | yes | 1490655 |
| thermal_chamber_hysteresis | realistic_self_verify | qwen35-9b-ud-q4kxl | HOST_TEST_FAILED | host_tests | host unit tests | 2446.5 | 1768.1 | 2 | 11 | 5 | yes | 6120453 |
| thermal_chamber_hysteresis | realistic_self_verify | qwen35-4b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.1 | - | 0 | 10 | 1 | authored | 2135397 |
| thermal_chamber_hysteresis | realistic_self_verify | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3612.1 | - | 0 | 0 | 0 | authored | 1075817 |
| thermal_chamber_hysteresis | ci_red_green | gpt-5.4 | PASS | pass | integration | 313.6 | 275.6 | 1 | 2 | 2 | yes | 413492 |
| thermal_chamber_hysteresis | ci_red_green | gpt-5.4-mini | INTEGRATION_FAILED | integration | integration | 1674.4 | 423.7 | 8 | 2 | 9 | yes | 4019196 |
| thermal_chamber_hysteresis | ci_red_green | qwen35-27b-q4km | PASS | pass | integration | 1695.7 | 1648.2 | 1 | 5 | 10 | yes | 2469564 |
| thermal_chamber_hysteresis | ci_red_green | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 777.2 | 738.4 | 1 | 2 | 8 | yes | 1163104 |
| thermal_chamber_hysteresis | ci_red_green | qwen35-9b-ud-q4kxl | INTEGRATION_FAILED | integration | integration | 2666.5 | 1506.0 | 4 | 5 | 19 | authored | 6707249 |
| thermal_chamber_hysteresis | ci_red_green | qwen35-4b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.1 | - | 0 | 7 | 96 | authored | 6621246 |
| thermal_chamber_hysteresis | ci_red_green | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 536.1 | - | 0 | 0 | 0 | no | 24196086 |
| thermal_chamber_hysteresis | oracle_full | gpt-5.4 | PASS | pass | integration | 433.8 | 395.5 | 1 | 1 | 3 | yes | 550844 |
| thermal_chamber_hysteresis | oracle_full | gpt-5.4-mini | PASS | pass | integration | 608.8 | 479.3 | 2 | 1 | 8 | yes | 1459288 |
| thermal_chamber_hysteresis | oracle_full | qwen35-27b-q4km | PASS | pass | integration | 1231.7 | 1174.1 | 1 | 1 | 6 | yes | 2067603 |
| thermal_chamber_hysteresis | oracle_full | qwen35-35b-a3b-ud-q4km | PASS | pass | integration | 784.1 | 742.1 | 1 | 3 | 6 | yes | 1031976 |
| thermal_chamber_hysteresis | oracle_full | qwen35-9b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 3600.1 | 3592.7 | 0 | 5 | 7 | yes | 7580708 |
| thermal_chamber_hysteresis | oracle_full | qwen35-4b-ud-q4kxl | INTEGRATION_FAILED | integration | integration | 1173.7 | 364.1 | 20 | 10 | 17 | yes | 11011786 |
| thermal_chamber_hysteresis | oracle_full | qwen35-2b-ud-q4kxl | NO_SUBMISSION | no_submission | - | 955.4 | - | 0 | 1 | 37 | no | 8491113 |

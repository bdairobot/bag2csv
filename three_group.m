function three_group()
    clc;clear;close all;
    filename = 'husky-IJRR-map-fusion-day-carpark-_2018-10-30-22-25-18_statistics.csv';
    extract_topic_statistics(filename,[6.2, 7.5],'rgb');
    filename = 'husky-IJRR-map-fusion-day-forest-_2018-10-30-23-57-21_statistics.csv';
    extract_topic_statistics(filename,[6, 7.477],'rgb');
    filename = 'husky-IJRR-map-fusion-night-forest-_2018-10-31-12-10-02_statistics.csv';
    extract_topic_statistics(filename,[6.1, 7.39],'thermal');
end